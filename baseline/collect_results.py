#!/usr/bin/env python
"""Merge the baseline agent's per-batch answers and the runner's timings into one results sheet, then score it.

Inputs, in the run folder build/baseline_runs/<label>/ (or <--runs-dir>/<label>/):
    batch_NN.yaml          each batch agent's final message, saved verbatim: a YAML list of
                           {id, answer, cited_sources, notes}. A ```yaml fence, '>>> ' marker lines and
                           stray text before the first '- id:' are tolerated.
    batch_NN_retryK.yaml   a recorded retry of batch NN (BASELINE_PROTOCOL.md, fairness rules). Its
                           entries replace that batch's entries, and the report flags them.
    timings.csv            batch, question_id, seconds, tool_calls [, tokens_in, tokens_out, tokens (total), notes]
                             question_id <id>    that question (exact)
                             question_id *       the batch's totals (e.g. the agent's own usage report);
                                                 what exact and overhead rows leave over is split evenly
                                                 over the batch's questions without an exact row
                                                 ('apportioned')
                             _setup / _output    batch overhead outside any question
                             _prep (batch prep)  the preparation session (prepared mode)
                           Rows left blank (the template) count as missing.
    run.yaml               run metadata written by questions_for_agent.py and completed by the runner
    batch_plan.csv         which question was in which batch (optional; used for checks and '*' rows)

Outputs:
    results/runs/baseline_<label>.yaml            score.py's results-sheet format (run + answers). Each
                                                  answer also carries batch, tool_calls, tokens_in,
                                                  tokens_out and timing; the scorer ignores those fields.
                                                  Existing 'override' values in this file are kept.
    results/baseline_<label>_score.md / .json      from 'harness/score.py score'
    results/baseline_<label>_efficiency.md / .json time, tool calls and tokens, per run and per batch

Every question of the key (or of run.yaml's ask_mode_filter) is in the sheet. A question with no
answer is 'unanswered'.

Usage
  .venv/bin/python -I baseline/collect_results.py --label cold_r1
  .venv/bin/python -I baseline/collect_results.py --label test --root build/test_baseline \\
        --questions build/test_baseline/questions/questions.yaml

Exit codes: 0 ok; 1 the scorer failed; 2 bad inputs (unparseable batch file, duplicate answers, ...).
"""
from __future__ import annotations

import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import argparse
import csv
import json
import math
import re
import statistics
import subprocess

import yaml

from harness import score as S

Path = pathlib.Path
RESERVED = {"*", "_setup", "_output", "_prep"}


class UsageError(Exception):
    pass


def batch_key(s) -> str:
    """'03', '3', 'batch_03' -> '3'; 'batch_03_retry1' -> '3_retry1'; 'prep' -> 'prep'."""
    s = re.sub(r"^batch[_-]?", "", str(s).strip(), flags=re.I)
    m = re.fullmatch(r"0*(\d+)(.*)", s)
    return f"{int(m.group(1))}{m.group(2)}" if m else s


def base_of(bkey: str) -> str:
    return re.sub(r"_retry\d+$", "", bkey)


def num(v) -> float | None:
    s = S.coerce_text(v).strip().replace(",", "")
    if not s:
        return None
    try:
        return float(s)
    except ValueError:
        return None


# ---------------------------------------------------------------------------------------------
# batch answers
# ---------------------------------------------------------------------------------------------

def yaml_text(raw: str) -> str:
    """The YAML list inside an agent's final message."""
    fences = [b for b in re.findall(r"^```[ \t]*(?:ya?ml)?[ \t]*\n(.*?)^```[ \t]*$", raw, flags=re.S | re.M)
              if re.search(r"^-\s+id\s*:", b, flags=re.M)]
    text = max(fences, key=len) if fences else raw
    lines = text.splitlines()
    start = next((i for i, ln in enumerate(lines) if re.match(r"^-\s+id\s*:", ln)), None)
    if start is None:
        start = next((i for i, ln in enumerate(lines) if re.match(r"^(answers|results)\s*:", ln)), 0)
    return "\n".join(ln for ln in lines[start:] if not ln.startswith(">>>") and ln.rstrip() != "```")


def load_batch(path: Path) -> list[dict]:
    raw = path.read_text(encoding="utf-8-sig")
    try:
        data = yaml.safe_load(yaml_text(raw))
    except yaml.YAMLError as exc:
        raise UsageError(f"{path.name}: not valid YAML ({exc}). Fix the syntax only (never the content) and record "
                         "the fix under manual_fixes in run.yaml")
    if isinstance(data, dict):
        data = data.get("answers") or data.get("results") or []
    if not isinstance(data, list):
        raise UsageError(f"{path.name}: expected a YAML list of answers")
    out = []
    for e in data:
        if not isinstance(e, dict) or S.coerce_text(e.get("id")).strip() == "":
            continue
        ans = S.coerce_text(e.get("answer")).strip()
        out.append({"id": S.coerce_text(e["id"]).strip(), "answer": ans or None,
                    "cited_sources": S._sources(e.get("cited_sources")),
                    "notes": S.coerce_text(e.get("notes")).strip() or None})
    return out


def batch_files(run_dir: Path) -> list[tuple[str, Path]]:
    files = [p for p in run_dir.glob("batch_*.y*ml") if re.fullmatch(r"batch_[^.]+\.ya?ml", p.name)
             and p.stem != "batch_plan"]
    return sorted(((batch_key(p.stem), p) for p in files), key=lambda t: S.natural_key(t[0]))


def merge_answers(run_dir: Path, warnings: list[str]) -> tuple[dict[str, dict], dict[str, list[str]], list[str]]:
    """(answers by id, ids per batch key, retry notes)."""
    answers: dict[str, dict] = {}
    per_batch: dict[str, list[str]] = {}
    retries = []
    files = batch_files(run_dir)
    if not files:
        raise UsageError(f"no batch_*.yaml files in {run_dir}")
    for bkey, path in sorted(files, key=lambda t: ("_retry" in t[0], S.natural_key(t[0]))):
        entries = load_batch(path)
        if not entries:
            warnings.append(f"{path.name}: no answers")
        per_batch[bkey] = [e["id"] for e in entries]
        for e in entries:
            prev = answers.get(e["id"])
            if prev and "_retry" not in bkey:
                raise UsageError(f"{e['id']} is answered in both {prev['_file']} and {path.name}; a second attempt "
                                 "must be a recorded retry named batch_NN_retryK.yaml")
            if prev:
                retries.append(f"{e['id']}: {path.name} replaces {prev['_file']}")
            answers[e["id"]] = {**e, "_batch": bkey, "_file": path.name}
    return answers, per_batch, retries


# ---------------------------------------------------------------------------------------------
# timings
# ---------------------------------------------------------------------------------------------

ALIASES = {"question_id": ("question_id", "question id", "id", "qid", "question"),
           "seconds": ("seconds", "latency_s", "wall_s", "secs", "duration_s"),
           "tool_calls": ("tool_calls", "tool calls", "tool_uses", "tools"),
           "tokens_in": ("tokens_in", "input_tokens"), "tokens_out": ("tokens_out", "output_tokens"),
           "tokens": ("tokens", "total_tokens"), "batch": ("batch",), "notes": ("notes", "note")}


def load_timings(path: Path, warnings: list[str]) -> list[dict]:
    if not path.is_file():
        warnings.append(f"{path.name} not found: no latency or tool calls recorded")
        return []
    rows = []
    with open(path, newline="", encoding="utf-8-sig") as f:
        rdr = csv.DictReader(f)
        cols = {(c or "").strip().lower(): c for c in rdr.fieldnames or []}
        pick = {k: next((cols[a] for a in al if a in cols), None) for k, al in ALIASES.items()}
        for need in ("batch", "question_id", "seconds", "tool_calls"):
            if pick[need] is None:
                raise UsageError(f"{path.name}: column {need!r} missing (have {list(cols)})")
        for i, r in enumerate(rdr, 2):
            row = {k: (r.get(c) if c else None) for k, c in pick.items()}
            qid = S.coerce_text(row["question_id"]).strip()
            if not qid:
                continue
            sec, calls = num(row["seconds"]), num(row["tool_calls"])
            if sec is None and calls is None:
                continue                      # blank template row
            rows.append({"batch": batch_key(row["batch"]), "id": qid, "seconds": sec, "tool_calls": calls,
                         "tokens_in": num(row["tokens_in"]), "tokens_out": num(row["tokens_out"]),
                         "tokens": num(row["tokens"]), "line": i})
    return rows


def add(a, b):
    return b if a is None else (a if b is None else a + b)


def assign_timings(qids: list[str], answers: dict, plan: dict[str, str], per_batch: dict[str, list[str]],
                   rows: list[dict], warnings: list[str]) -> tuple[dict[str, dict], dict[str, dict], dict | None]:
    """(per-question timing, per-batch totals, prep totals)."""
    exact, star, prep = {}, {}, None
    overhead: dict[str, dict] = {}
    for r in rows:
        if r["id"] == "_prep":
            prep = {k: add((prep or {}).get(k), r[k]) for k in ("seconds", "tool_calls", "tokens_in", "tokens_out", "tokens")}
        elif r["id"] == "*":
            if r["batch"] in star:
                warnings.append(f"timings line {r['line']}: second '*' row for batch {r['batch']} ignored")
            else:
                star[r["batch"]] = r
        elif r["id"] in ("_setup", "_output"):
            o = overhead.setdefault(r["batch"], {})
            for k in ("seconds", "tool_calls", "tokens_in", "tokens_out", "tokens"):
                o[k] = add(o.get(k), r[k])
        else:
            key = (r["batch"], r["id"])
            if key in exact:
                warnings.append(f"timings line {r['line']}: {r['id']} timed twice in batch {r['batch']}; rows added")
                for k in ("seconds", "tool_calls", "tokens_in", "tokens_out", "tokens"):
                    exact[key][k] = add(exact[key][k], r[k])
            else:
                exact[key] = dict(r)

    def batch_of(qid):
        if qid in answers:
            return answers[qid]["_batch"]
        return plan.get(qid)

    members: dict[str, list[str]] = {}
    for qid in qids:
        b = batch_of(qid)
        if b is not None:
            members.setdefault(b, []).append(qid)
    for b, ids in per_batch.items():          # answers for ids outside the key still count for apportioning
        members.setdefault(b, [])
        for qid in ids:
            if qid not in members[b] and b == batch_of(qid):
                members[b].append(qid)

    K = ("seconds", "tool_calls", "tokens_in", "tokens_out", "tokens")
    batches: dict[str, dict] = {}
    for b in sorted(set(members) | set(star) | set(overhead), key=S.natural_key):
        ids = members.get(b, [])
        ex = [exact[(b, q)] for q in ids if (b, q) in exact]
        o = overhead.get(b, {})
        tb = {"batch": b, "questions": len(ids), "method": None,
              "answer_seconds": None, "answer_tool_calls": None,
              "overhead_seconds": o.get("seconds"), "overhead_tool_calls": o.get("tool_calls"),
              **{k: None for k in K}, "_share": None}
        for r in ex:
            tb["answer_seconds"] = add(tb["answer_seconds"], r["seconds"])
            tb["answer_tool_calls"] = add(tb["answer_tool_calls"], r["tool_calls"])
        sums = {k: add(sum(r[k] for r in ex if r[k] is not None) if any(r[k] is not None for r in ex) else None,
                       o.get(k)) for k in K}
        if b in star:
            # the '*' row is the batch total; questions without an exact row share what exact rows leave over
            tb["method"] = "batch totals" if not ex else "per question + batch totals"
            for k in K:
                tb[k] = star[b][k] if star[b][k] is not None else sums[k]
            rest = [q for q in ids if (b, q) not in exact]
            if rest:
                tb["_share"] = {k: (None if star[b][k] is None else max(star[b][k] - (sums[k] or 0), 0) / len(rest))
                                for k in K}
        else:
            tb["method"] = "per question" if ex else "none"
            tb.update(sums)
        batches[b] = tb

    timing: dict[str, dict] = {}
    for qid in qids:
        b = batch_of(qid)
        t = {"batch": b, **{k: None for k in K}, "timing": "missing"}
        if b is not None and (b, qid) in exact:
            t.update({k: exact[(b, qid)][k] for k in K}, timing="exact")
        elif b is not None and batches.get(b, {}).get("_share"):
            t.update(batches[b]["_share"], timing="apportioned")
        elif qid in answers:
            warnings.append(f"{qid}: answered in batch {b} but has no timing row")
        timing[qid] = t
    for tb in batches.values():
        tb.pop("_share", None)
    return timing, batches, prep


# ---------------------------------------------------------------------------------------------
# efficiency report
# ---------------------------------------------------------------------------------------------

def stats(values) -> dict:
    v = sorted(x for x in values if x is not None)
    if not v:
        return {"n": 0}
    return {"n": len(v), "total": sum(v), "mean": statistics.fmean(v), "median": statistics.median(v),
            "p90": v[math.ceil(0.9 * len(v)) - 1], "max": v[-1]}


def fnum(x, unit: str = "", dec: int = 1) -> str:
    if x is None:
        return "–"
    if abs(x - round(x)) < 1e-9 and dec <= 1 and unit != " s":
        return f"{int(round(x)):,}{unit}"
    return f"{x:,.{dec}f}{unit}"


def efficiency(meta: dict, sheet: list[dict], batches: dict, prep: dict | None) -> dict:
    answered = [e for e in sheet if S.coerce_text(e.get("answer")).strip()]
    lat = stats(e.get("latency_s") for e in sheet)
    calls = stats(e.get("tool_calls") for e in sheet)
    wall = sum(b["seconds"] for b in batches.values() if b["seconds"] is not None)
    total_calls = sum(b["tool_calls"] for b in batches.values() if b["tool_calls"] is not None)
    tok_in = sum(b["tokens_in"] or 0 for b in batches.values())
    tok_out = sum(b["tokens_out"] or 0 for b in batches.values())
    tok = sum(b["tokens"] or 0 for b in batches.values())
    methods = sorted({e.get("timing") for e in sheet})
    return {"label": meta.get("label"), "baseline_mode": meta.get("baseline_mode"), "model": meta.get("model"),
            "temperature": meta.get("temperature"), "runner": meta.get("runner"),
            "questions": len(sheet), "answered": len(answered), "batches": len(batches),
            "wall_seconds": wall, "all_in_seconds_per_question": wall / len(sheet) if sheet else None,
            "tool_calls": total_calls, "all_in_tool_calls_per_question": total_calls / len(sheet) if sheet else None,
            "tokens_in": tok_in or None, "tokens_out": tok_out or None, "tokens": tok or None,
            "latency": lat, "tool_calls_per_question": calls, "timing_methods": methods,
            "timing_counts": {m: sum(1 for e in sheet if e.get("timing") == m) for m in methods},
            "prep": prep, "per_batch": list(batches.values())}


def render_efficiency(eff: dict) -> str:
    lat, calls, prep = eff["latency"], eff["tool_calls_per_question"], eff["prep"]
    desc = [f"mode {eff['baseline_mode'] or '?'}", f"model {eff['model'] or '?'}",
            f"temperature {eff['temperature'] or '?'}"] + ([f"runner {eff['runner']}"] if eff["runner"] else [])
    tc = ", ".join(f"{n} {m}" for m, n in eff["timing_counts"].items())
    L = [f"# Baseline efficiency: {eff['label']}", "",
         f"{'; '.join(desc)}. {eff['questions']} questions in {eff['batches']} batches, {eff['answered']} answered. "
         f"Per-question timing: {tc}.", "",
         "| Measure | Value |", "|---|---|",
         f"| Wall-clock, all batches | {fnum(eff['wall_seconds'], ' s')} ({fnum(eff['wall_seconds'] / 60, ' min')}) |",
         f"| All-in per question (total ÷ questions) | {fnum(eff['all_in_seconds_per_question'], ' s')} |",
         f"| Answering time per question: median / p90 / max | {fnum(lat.get('median'), ' s')} / "
         f"{fnum(lat.get('p90'), ' s')} / {fnum(lat.get('max'), ' s')} |",
         f"| Tool calls, all batches | {fnum(eff['tool_calls'])} |",
         f"| Tool calls per question: median / mean / max | {fnum(calls.get('median'))} / {fnum(calls.get('mean'))} / "
         f"{fnum(calls.get('max'))} |",
         f"| Tokens in / out | {fnum(eff['tokens_in'])} / {fnum(eff['tokens_out'])}"
         + (f" (total {fnum(eff['tokens'])})" if eff["tokens"] else "") + " |",
         "| Preparation session | " + (f"{fnum(prep.get('seconds'), ' s')}, {fnum(prep.get('tool_calls'))} tool calls"
                                       if prep else "none (cold)") + " |", "",
         "Answering time runs from a question's marker to the next one. Overhead is the time before the first "
         "question and the time spent composing the final answer. The all-in figure includes it, and so do the "
         "batch totals.", "",
         "## Per batch", "",
         "| Batch | Questions | Timing | Answering | Overhead | Total | Tool calls (answering + overhead) | Tokens in / out |",
         "|---|---|---|---|---|---|---|---|"]
    for b in eff["per_batch"]:
        tcalls = (f"{fnum(b['tool_calls'])} ({fnum(b['answer_tool_calls'])} + {fnum(b['overhead_tool_calls'])})"
                  if b["answer_tool_calls"] is not None else fnum(b["tool_calls"]))
        L.append(f"| {b['batch']} | {b['questions']} | {b['method']} | {fnum(b['answer_seconds'], ' s')} | "
                 f"{fnum(b['overhead_seconds'], ' s')} | {fnum(b['seconds'], ' s')} | {tcalls} | "
                 f"{fnum(b['tokens_in'])} / {fnum(b['tokens_out'])} |")
    return "\n".join(L) + "\n"


def summary_line(eff: dict) -> str:
    s = (f"baseline agent, mode {eff['baseline_mode'] or '?'}, model {eff['model'] or '?'}, temperature "
         f"{eff['temperature'] or '?'}; {eff['questions']} questions in {eff['batches']} batches; wall-clock "
         f"{fnum(eff['wall_seconds'], ' s')} in all ({fnum(eff['all_in_seconds_per_question'], ' s')} per question "
         f"all-in, median answering {fnum(eff['latency'].get('median'), ' s')}); {fnum(eff['tool_calls'])} tool calls "
         f"(median {fnum(eff['tool_calls_per_question'].get('median'))} per question)")
    if eff["prep"]:
        s += (f"; preparation {fnum(eff['prep'].get('seconds'), ' s')}, "
              f"{fnum(eff['prep'].get('tool_calls'))} tool calls")
    return s


# ---------------------------------------------------------------------------------------------

def read_plan(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {}
    with open(path, newline="", encoding="utf-8") as f:
        return {r["id"]: batch_key(r["batch"]) for r in csv.DictReader(f) if r.get("id")}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--label", required=True, help="run label, e.g. cold_r1 (the sheet is baseline_<label>)")
    ap.add_argument("--root", default=str(ROOT), help="tree holding build/ and results/ (default: repo root)")
    ap.add_argument("--runs-dir", help="parent of the run folders, as for questions_for_agent.py "
                                       "(default: <root>/build/baseline_runs)")
    ap.add_argument("--timings", help="timings CSV (default: <run folder>/timings.csv)")
    ap.add_argument("--questions", help="question key (default: run.yaml's questions_file, else questions/questions.yaml)")
    ap.add_argument("--out", help="results sheet (default: <root>/results/runs/baseline_<label>.yaml)")
    ap.add_argument("--score-out", help="score report (default: <root>/results/baseline_<label>_score.md)")
    ap.add_argument("--no-score", action="store_true", help="write the sheet only")
    for k in ("model", "temperature", "baseline-mode", "operator", "date", "runner"):
        ap.add_argument(f"--{k}", help=f"override run.yaml's {k.replace('-', '_')}")
    args = ap.parse_args(argv)
    try:
        return run(args)
    except UsageError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except S.UsageError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


def run(args) -> int:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", args.label):
        raise UsageError(f"label {args.label!r}: use letters, digits, '.', '_' or '-'")
    root = Path(args.root).resolve()
    run_dir = (Path(args.runs_dir).expanduser() if args.runs_dir else root / "build" / "baseline_runs") / args.label
    if not run_dir.is_dir():
        raise UsageError(f"run folder {run_dir} not found")
    warnings: list[str] = []
    meta_in = {}
    if (run_dir / "run.yaml").is_file():
        meta_in = yaml.safe_load((run_dir / "run.yaml").read_text(encoding="utf-8")) or {}
    else:
        warnings.append("run.yaml not found: model, temperature and mode are not recorded")
    for k in ("model", "temperature", "baseline_mode", "operator", "date", "runner"):
        v = getattr(args, k)
        if v:
            meta_in[k] = v
    qpath = Path(args.questions) if args.questions else None
    if qpath is None and meta_in.get("questions_file"):
        cand = Path(meta_in["questions_file"])
        qpath = cand if cand.is_absolute() else root / cand
    qs, qsrc, sha = S.load_questions(qpath)
    if meta_in.get("questions_sha1") and meta_in["questions_sha1"] != sha:
        warnings.append("the question key changed since the questions were split for this run (sha1 differs)")
    flt = meta_in.get("ask_mode_filter") or "all"
    qs = [q for q in qs if flt == "all" or str(q.get("ask_mode") or "chat") == flt]
    key = {str(q["id"]): q for q in qs}
    qids = list(key)

    answers, per_batch, retries = merge_answers(run_dir, warnings)
    plan = read_plan(run_dir / "batch_plan.csv")
    for qid, a in answers.items():
        if qid not in key:
            warnings.append(f"{qid} (in {a['_file']}) is not in the question key; ignored")
        elif plan and plan.get(qid) != base_of(a["_batch"]):
            warnings.append(f"{qid}: answered in {a['_file']} but planned for batch {plan.get(qid)}")
    missing = [q for q in qids if q not in answers]
    if missing:
        warnings.append(f"{len(missing)} question(s) without an answer (scored unanswered): {S._short(missing, 10)}")

    rows = load_timings(Path(args.timings) if args.timings else run_dir / "timings.csv", warnings)
    timing, batches, prep = assign_timings(qids, answers, plan, per_batch, rows, warnings)

    out = Path(args.out) if args.out else root / "results" / "runs" / f"baseline_{args.label}.yaml"
    kept = {}
    if out.is_file():
        try:
            _, old = S.load_sheet(out)
            kept = {S.coerce_text(e.get("id")).strip(): e.get("override") for e in old
                    if S.parse_override(e.get("override"))[0]}
        except S.UsageError:
            warnings.append(f"{out.name}: the existing sheet could not be read; overrides not carried over")

    def rnd(x, d=1):
        if x is None:
            return None
        return int(round(x)) if abs(x - round(x)) < 1e-9 or d == 0 else round(x, d)

    sheet = []
    for qid in qids:
        q, a, t = key[qid], answers.get(qid, {}), timing[qid]
        sheet.append({
            "id": qid, "category": q.get("category"), "ask_mode": q.get("ask_mode") or "chat",
            "question": S.coerce_text(q.get("question")).strip(), "answer": a.get("answer"),
            "latency_s": rnd(t["seconds"]), "cited_sources": a.get("cited_sources") or [], "notes": a.get("notes"),
            "override": kept.get(qid),
            "batch": a.get("_batch") or t["batch"], "tool_calls": rnd(t["tool_calls"]),
            "tokens_in": rnd(t["tokens_in"], 0), "tokens_out": rnd(t["tokens_out"], 0), "timing": t["timing"],
        })
        if a.get("_batch") and "_retry" in a["_batch"]:
            sheet[-1]["notes"] = ((sheet[-1]["notes"] or "") + f" [recorded retry: {a['_file']}]").strip()

    label = f"baseline_{args.label}"
    meta = {"label": label, "context": "baseline", "mode": flt, "questions_file": qsrc, "questions_sha1": sha,
            "date": meta_in.get("date") or None, "operator": meta_in.get("operator") or None,
            "product_version": None, "notes": None}
    for k in ("baseline_mode", "model", "temperature", "effort", "runner", "runner_version", "system_prompt_delivery",
              "sandbox_digest", "order", "order_seed", "batch_size", "max_calls_per_question", "timing_method",
              "retries", "manual_fixes"):
        if meta_in.get(k) not in (None, "", []):
            meta[k] = meta_in[k]
    if retries:
        meta["retry_replacements"] = retries
    eff = efficiency({**meta_in, "label": label, "baseline_mode": meta_in.get("baseline_mode")}, sheet, batches, prep)
    meta["notes"] = summary_line(eff) + (f". {meta_in['notes']}" if meta_in.get("notes") else "")

    out.parent.mkdir(parents=True, exist_ok=True)
    shown_dir = S.rel(run_dir) if run_dir.resolve().is_relative_to(ROOT) else f"<runs-dir>/{run_dir.name}"
    head = (f"# Baseline results sheet for run {label!r}, written by baseline/collect_results.py from\n"
            f"# {shown_dir}. Regenerate it with collect_results.py rather than editing answers by hand.\n"
            "# Only 'override' is meant for hand edits (correct | partial | wrong | refused); it survives regeneration.\n"
            "# batch, tool_calls, tokens_in, tokens_out and timing are baseline extras; score.py ignores them.\n")
    body = yaml.dump({"run": meta, "answers": sheet}, Dumper=S._SheetDumper, sort_keys=False, allow_unicode=True,
                     width=4096, default_flow_style=False)
    out.write_text(head + body.replace("\n- id:", "\n\n- id:"), encoding="utf-8")

    score_md = Path(args.score_out) if args.score_out else root / "results" / f"{label}_score.md"
    eff_md = score_md.with_name(score_md.name.replace("_score.md", "_efficiency.md")
                                if score_md.name.endswith("_score.md") else score_md.stem + "_efficiency.md")
    eff_md.parent.mkdir(parents=True, exist_ok=True)
    eff_md.write_text(render_efficiency(eff), encoding="utf-8")
    eff_md.with_suffix(".json").write_text(json.dumps(eff, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")

    n_ans = sum(1 for e in sheet if e["answer"])
    print(f"wrote {out}: {len(sheet)} questions, {n_ans} answered, from {len(per_batch)} batch file(s)"
          + (f"; kept {len(kept)} override(s)" if kept else ""))
    print(f"wrote {eff_md} (+ .json): {summary_line(eff)}")
    for w in warnings:
        print(f"WARN: {w}")
    if args.no_score:
        return 0
    cmd = [sys.executable, "-I", str(ROOT / "harness" / "score.py"), "score", str(out), "--out", str(score_md)]
    if qpath is not None:
        cmd += ["--questions", str(qpath)]
    r = subprocess.run(cmd)
    return 0 if r.returncode == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

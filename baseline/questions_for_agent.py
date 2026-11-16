#!/usr/bin/env python
"""Write the questions, and only the questions, for the baseline agent; render its prompts.

Reads questions/questions.yaml (docs/CONVENTIONS.md §7) and writes into the sandbox:

    QUESTIONS_ONLY.md             every question, as its id and text and nothing else, in batch order
    QUESTIONS_ONLY_batch_NN.md    the same questions split into batches of --batch-size (default 10)

The order is a seeded shuffle (--seed, default "baseline-order/v1"), so no batch is all one category.
--order file keeps the file's order. --mode chat|graph|vector picks questions by ask_mode, as
'score.py template --mode' does (default: all).

With --label L it also prepares the run folder build/baseline_runs/L/, outside the sandbox:

    batch_plan.csv        batch, seq, id
    timings.csv           header plus one blank row per question, for the runner (or for
                          baseline/timings_from_transcript.py); never overwritten
    run.yaml              run metadata to complete (model, temperature, runner, ...); never overwritten
    prompts/system.md     the SYSTEM prompt of baseline/agent_prompt.md, filled in
    prompts/batch_NN.md   the TASK prompt for each batch, filled in (prepared mode: + PREPARED_ADDENDUM)
    prompts/prep.md       the PREP prompt (prepared mode only)

Prepared mode: the preparation session must not see the questions. So first run with --prep-only,
which writes only run.yaml and prompts/system.md and prompts/prep.md and puts nothing in the sandbox.
Run the preparation session, then run this script again without --prep-only.

Usage
  .venv/bin/python -I baseline/questions_for_agent.py --label cold_r1
  .venv/bin/python -I baseline/questions_for_agent.py --label prep_r1 --baseline-mode prepared --prep-only
  .venv/bin/python -I baseline/questions_for_agent.py --root build/test_baseline --batch-size 2 --label test

Exit codes: 0 ok; 2 missing questions file, missing sandbox, or bad options.
"""
from __future__ import annotations

import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import argparse
import csv
import fnmatch
import hashlib
import json
import random
import re

import yaml

Path = pathlib.Path

PROMPT_FILE = ROOT / "baseline" / "agent_prompt.md"
DEFAULT_SEED = "baseline-order/v1"
TIMINGS_COLUMNS = ["batch", "question_id", "seconds", "tool_calls", "tokens_in", "tokens_out", "tokens", "notes"]


class UsageError(Exception):
    pass


def manifest_path(sandbox: Path) -> Path:
    return sandbox.parent / f"{sandbox.name}.manifest.json"


def load_questions(path: Path, mode: str) -> tuple[list[dict], str]:
    if not path.is_file():
        raise UsageError(
            f"{path} does not exist yet: the question set has not been written. Nothing was written to the "
            "sandbox. Rerun once it exists, or pass --questions FILE.")
    raw = path.read_bytes()
    try:
        data = yaml.safe_load(raw.decode("utf-8-sig")) or []
    except yaml.YAMLError as exc:
        raise UsageError(f"{path}: YAML error: {exc}")
    if isinstance(data, dict):
        data = data.get("questions", [])
    if not isinstance(data, list):
        raise UsageError(f"{path}: the top level must be a list of questions")
    qs, seen = [], set()
    for q in data:
        if not isinstance(q, dict) or q.get("id") is None:
            continue
        qid = str(q["id"]).strip()
        text = str(q.get("question") or "").strip()
        if not text:
            raise UsageError(f"{path}: question {qid} has no question text")
        if qid in seen:
            raise UsageError(f"{path}: id {qid} appears more than once")
        seen.add(qid)
        if mode == "all" or str(q.get("ask_mode") or "chat") == mode:
            qs.append({"id": qid, "question": text})
    if not qs:
        raise UsageError(f"{path}: no questions" + ("" if mode == "all" else f" with ask_mode {mode}"))
    return qs, hashlib.sha1(raw).hexdigest()


def order(qs: list[dict], how: str, seed: str) -> list[dict]:
    qs = list(qs)
    if how == "shuffled":
        random.Random(seed).shuffle(qs)
    return qs


def question_block(batch: list[dict]) -> str:
    return "\n\n".join(f"### {q['id']}\n{q['question']}" for q in batch)


def batch_md(title: str, batch: list[dict]) -> str:
    return f"# {title}\n\n{question_block(batch)}\n"


# ---------------------------------------------------------------------------------------------
# prompt templates
# ---------------------------------------------------------------------------------------------

def load_templates(path: Path = PROMPT_FILE) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    out = {}
    for m in re.finditer(r"<!-- BEGIN (\w+) -->\s*\n(.*?)<!-- END \1 -->", text, flags=re.S):
        body = m.group(2).strip()
        fence = re.fullmatch(r"```[a-z]*\n(.*)\n```", body, flags=re.S)
        out[m.group(1)] = (fence.group(1) if fence else body).rstrip() + "\n"
    for need in ("SYSTEM", "TASK", "PREP", "PREPARED_ADDENDUM"):
        if need not in out:
            raise UsageError(f"{path}: section {need} (<!-- BEGIN {need} --> ... <!-- END {need} -->) not found")
    return out


def render(template: str, values: dict[str, str]) -> str:
    text = re.sub(r"\{\{(\w+)\}\}", lambda m: values.get(m.group(1), m.group(0)), template)
    left = sorted(set(re.findall(r"\{\{(\w+)\}\}", text)))
    if left:
        raise UsageError(f"unfilled placeholders in a prompt template: {', '.join(left)}")
    return text


# ---------------------------------------------------------------------------------------------

def run_yaml_template(args, label: str, sandbox: Path, manifest: dict, qfile: str, sha: str | None,
                      n_q: int | None, n_b: int | None) -> tuple[str, dict]:
    meta = {
        "label": label,
        "baseline_mode": args.baseline_mode,
        "model": "",
        "temperature": "",
        "effort": "",
        "runner": "",
        "runner_version": "",
        "system_prompt_delivery": "system prompt",
        "operator": "",
        "date": "",
        "sandbox": str(sandbox),
        "sandbox_digest": manifest.get("digest"),
        "agent_python": (manifest.get("python") or {}).get("path"),
        "questions_file": qfile,
        "questions_sha1": sha,
        "ask_mode_filter": args.mode,
        "order": args.order,
        "order_seed": args.seed if args.order == "shuffled" else None,
        "batch_size": args.batch_size,
        "questions": n_q,
        "batches": n_b,
        "max_calls_per_question": args.max_calls,
        "prep_minutes_budget": args.prep_minutes if args.baseline_mode == "prepared" else None,
        "timing_method": "",
        "retries": [],
        "manual_fixes": [],
        "notes": "",
    }
    head = ("# Baseline run metadata (baseline/BASELINE_PROTOCOL.md). Fill in the blanks before the first batch.\n"
            "#   model                   exact model id;  temperature: the value, or 'runner default (not settable)'\n"
            "#   effort                  reasoning effort / thinking setting, if the runner has one\n"
            "#   runner, runner_version  e.g. 'Claude Code subagents' or 'headless CLI', and its version\n"
            "#   system_prompt_delivery  'system prompt' or 'prepended to the task message'\n"
            "#   timing_method           transcript | per_turn | batch_totals\n"
            "#   retries                 - {batch: 3, file: batch_03_retry1.yaml, reason: 'agent crashed'}\n"
            "#   manual_fixes            - {batch: 2, what: 'YAML indentation of Q014 fixed; content unchanged'}\n")
    return head, meta


def write_run_yaml(path: Path, head: str, meta: dict) -> None:
    """Write run.yaml; on an existing one, keep every value already set and fill only the blanks
    (prepared mode: the --prep-only call has no questions yet, the second call adds them)."""
    if path.exists():
        old = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        for k in ("sandbox_digest", "questions_sha1"):
            if old.get(k) and meta.get(k) and old[k] != meta[k]:
                print(f"WARN: {path}: {k} was {old[k]} and is now {meta[k]}; this run mixes two "
                      f"{'sandboxes' if k == 'sandbox_digest' else 'question keys'}")
        blank = (None, "", [])
        filled = [k for k, v in meta.items() if old.get(k) in blank and v not in blank]
        if not filled:
            print(f"kept existing {path}")
            return
        meta = {**meta, **old, **{k: meta[k] for k in filled}}
        print(f"updated {path}: filled {', '.join(filled)}")
    path.write_text(head + yaml.safe_dump(meta, sort_keys=False, allow_unicode=True, width=200), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=str(ROOT), help="tree holding questions/ and build/ (default: repo root)")
    ap.add_argument("--questions", help="question file (default: <root>/questions/questions.yaml)")
    ap.add_argument("--sandbox", help="sandbox folder (default: <root>/build/baseline_sandbox)")
    ap.add_argument("--batch-size", type=int, default=10, help="questions per batch (default 10)")
    ap.add_argument("--mode", choices=["chat", "graph", "vector", "all"], default="all",
                    help="only questions with this ask_mode (default: all)")
    ap.add_argument("--order", choices=["shuffled", "file"], default="shuffled", help="question order (default: shuffled)")
    ap.add_argument("--seed", default=DEFAULT_SEED, help=f"shuffle seed (default {DEFAULT_SEED!r})")
    ap.add_argument("--label", help="also prepare build/baseline_runs/<label>/ (plan, timings, run.yaml, prompts)")
    ap.add_argument("--runs-dir", help="parent of the run folders (default: <root>/build/baseline_runs)")
    ap.add_argument("--baseline-mode", choices=["cold", "prepared"], default="cold", help="for the prompts (default cold)")
    ap.add_argument("--prep-only", action="store_true",
                    help="prepared mode, step 1: write run.yaml and the prep prompt only; no questions anywhere")
    ap.add_argument("--max-calls", type=int, default=30, help="soft tool-call budget per question (default 30)")
    ap.add_argument("--prep-minutes", type=int, default=60, help="soft preparation budget in minutes (default 60)")
    ap.add_argument("--agent-python", help="python named in the prompts (default: the one in the sandbox manifest)")
    args = ap.parse_args(argv)
    try:
        return run(args)
    except UsageError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


def run(args) -> int:
    root = Path(args.root).resolve()
    sandbox = (Path(args.sandbox).expanduser() if args.sandbox else root / "build" / "baseline_sandbox").resolve()
    qpath = Path(args.questions) if args.questions else root / "questions" / "questions.yaml"
    if args.batch_size < 1:
        raise UsageError("--batch-size must be at least 1")
    if args.prep_only and args.baseline_mode != "prepared":
        raise UsageError("--prep-only belongs to --baseline-mode prepared")
    if args.prep_only and not args.label:
        raise UsageError("--prep-only needs --label")
    qs, sha = ([], None) if args.prep_only else load_questions(qpath, args.mode)
    mp = manifest_path(sandbox)
    if not sandbox.is_dir() or not mp.is_file():
        raise UsageError(f"no sandbox at {sandbox} (or no {mp.name} beside it): run baseline/prepare_sandbox.py first")
    manifest = json.loads(mp.read_text(encoding="utf-8"))
    if manifest.get("status") != "ok":
        raise UsageError(f"the sandbox failed its leak check ({mp}); rebuild it first")
    python = args.agent_python or (manifest.get("python") or {}).get("path") or str(ROOT / ".venv" / "bin" / "python")

    batches: list[list[dict]] = []
    if not args.prep_only:
        qs = order(qs, args.order, args.seed)
        batches = [qs[i:i + args.batch_size] for i in range(0, len(qs), args.batch_size)]
        width = max(2, len(str(len(batches))))
        for old in sandbox.iterdir():
            if fnmatch.fnmatch(old.name, "QUESTIONS_ONLY*.md"):
                old.unlink()
        (sandbox / "QUESTIONS_ONLY.md").write_text(
            "# Questions\n\n" + "\n\n".join(
                f"## Batch {b:0{width}d}\n\n{question_block(batch)}" for b, batch in enumerate(batches, 1)) + "\n",
            encoding="utf-8")
        for b, batch in enumerate(batches, 1):
            (sandbox / f"QUESTIONS_ONLY_batch_{b:0{width}d}.md").write_text(
                batch_md(f"Questions: batch {b:0{width}d} of {len(batches):0{width}d}", batch), encoding="utf-8")
        print(f"wrote {sandbox / 'QUESTIONS_ONLY.md'} and {len(batches)} batch file(s): {len(qs)} questions"
              f" ({args.order}{', seed ' + repr(args.seed) if args.order == 'shuffled' else ''}, batch size {args.batch_size}"
              f"{'' if args.mode == 'all' else ', ask_mode ' + args.mode})")

    if not args.label:
        return 0
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", args.label):
        raise UsageError(f"label {args.label!r}: use letters, digits, '.', '_' or '-'")
    run_dir = (Path(args.runs_dir) if args.runs_dir else root / "build" / "baseline_runs") / args.label
    if run_dir.resolve().is_relative_to(sandbox):
        raise UsageError("the run folder must be outside the sandbox")
    (run_dir / "prompts").mkdir(parents=True, exist_ok=True)
    try:
        qfile = qpath.resolve().relative_to(root).as_posix()
    except ValueError:
        qfile = str(qpath)

    write_run_yaml(run_dir / "run.yaml", *run_yaml_template(args, args.label, sandbox, manifest, qfile, sha,
                                                            sum(map(len, batches)) or None, len(batches) or None))

    tpl = load_templates()
    common = {"SANDBOX": str(sandbox), "PYTHON": python, "MAX_CALLS": str(args.max_calls),
              "PREP_MINUTES": str(args.prep_minutes)}
    (run_dir / "prompts" / "system.md").write_text(render(tpl["SYSTEM"], common), encoding="utf-8")
    written = ["system.md"]
    if args.baseline_mode == "prepared":
        prep = render(tpl["PREP"], {**common, "WRITABLE": str(sandbox / "_notes") + "/"})
        (run_dir / "prompts" / "prep.md").write_text(prep, encoding="utf-8")
        written.append("prep.md")

    if batches:
        width = max(2, len(str(len(batches))))
        with open(run_dir / "batch_plan.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f, lineterminator="\n")
            w.writerow(["batch", "seq", "id"])
            for b, batch in enumerate(batches, 1):
                for s, q in enumerate(batch, 1):
                    w.writerow([f"{b:0{width}d}", s, q["id"]])
        for b, batch in enumerate(batches, 1):
            bb = f"{b:0{width}d}"
            vals = {**common, "BATCH": bb, "N_BATCHES": f"{len(batches):0{width}d}", "N_QUESTIONS": str(len(batch)),
                    "QUESTIONS": question_block(batch), "WRITABLE": str(sandbox / "_scratch" / f"batch_{bb}") + "/"}
            task = render(tpl["TASK"], vals)
            if args.baseline_mode == "prepared":
                task += "\n" + render(tpl["PREPARED_ADDENDUM"], vals)
            (run_dir / "prompts" / f"batch_{bb}.md").write_text(task, encoding="utf-8")
        written.append(f"batch_01..{len(batches):0{width}d}.md")
        timings = run_dir / "timings.csv"
        if not timings.exists():
            with open(timings, "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f, lineterminator="\n")
                w.writerow(TIMINGS_COLUMNS)
                for b, batch in enumerate(batches, 1):
                    for q in batch:
                        w.writerow([f"{b:0{width}d}", q["id"]] + [""] * (len(TIMINGS_COLUMNS) - 2))
        else:
            print(f"kept existing {timings}")
    print(f"run folder {run_dir}: run.yaml, prompts/{{{', '.join(written)}}}"
          + (", batch_plan.csv, timings.csv" if batches else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python
"""Per-question seconds, tool calls and tokens from a batch agent's transcript, split at its '>>> ' markers.

The baseline agent prints a line '>>> Q017' before it starts each question, and '>>> END' before its
final answer (baseline/agent_prompt.md). This script reads the session's JSONL transcript and writes
the batch's rows into timings.csv, replacing any earlier rows of that batch:

    <id>       from its marker to the next marker. The last question ends at the last tool result
               before '>>> END' (or at its own marker if it used no tools).
    _setup     from the prompt to the first marker: reading the prompt, any first look around
    _output    from the end of the last question to the end of the session: composing the final YAML

A question that is marked twice gets the sum of both stretches. A planned question without a marker
gets no row (collect_results.py reports it as missing). Its time falls into the previous question,
and a warning says so.

--batch prep (or --prep) writes one '_prep' row for a whole preparation session; no markers are needed.

Transcript format: one JSON object per line, with "type" ("user" | "assistant" | ...), an ISO
"timestamp", and "message" holding "content" blocks ("text", "tool_use", "tool_result"), plus for
assistant messages "id" and "usage" (input_tokens, cache_creation_input_tokens, cache_read_input_tokens,
output_tokens). Claude Code writes this format: the main session at ~/.claude/projects/<project>/<session>.jsonl,
subagents at .../<session>/subagents/agent-<id>.jsonl. A message can span several lines; its usage
is counted once. tokens_in counts every input token sent, cached or not; tokens_out counts the output.

Usage
  .venv/bin/python -I baseline/timings_from_transcript.py T.jsonl --batch 03 --timings build/baseline_runs/L/timings.csv
  .venv/bin/python -I baseline/timings_from_transcript.py PREP.jsonl --prep --timings build/baseline_runs/L/timings.csv
  .venv/bin/python -I baseline/timings_from_transcript.py T.jsonl --batch 03 --dry-run      # print only
"""
from __future__ import annotations

import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import argparse
import csv
import datetime
import json
import re

Path = pathlib.Path

MARKER = re.compile(r"^[ \t]*>>>[ \t]*([A-Za-z0-9][A-Za-z0-9_.:-]*)[ \t]*$", re.M)
COLUMNS = ["batch", "question_id", "seconds", "tool_calls", "tokens_in", "tokens_out", "tokens", "notes"]


class UsageError(Exception):
    pass


def batch_key(s) -> str:
    """'03', '3', 'batch_03' -> '3'; 'batch_03_retry1' -> '3_retry1'; 'prep' -> 'prep'."""
    s = re.sub(r"^batch[_-]?", "", str(s).strip(), flags=re.I)
    m = re.fullmatch(r"0*(\d+)(.*)", s)
    return f"{int(m.group(1))}{m.group(2)}" if m else s


def parse_ts(v) -> datetime.datetime | None:
    if not v:
        return None
    try:
        return datetime.datetime.fromisoformat(str(v).replace("Z", "+00:00"))
    except ValueError:
        return None


def read_events(path: Path) -> tuple[list[tuple], dict]:
    """Events in file order: (kind, ts, payload); kinds prompt | tool_result | marker | tool_use | message.
    Returns (events, usage per message id)."""
    events, usage = [], {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            try:
                d = json.loads(line)
            except ValueError:
                continue
            if not isinstance(d, dict):
                continue
            kind, ts, msg = d.get("type"), parse_ts(d.get("timestamp")), d.get("message") or {}
            if ts is None or not isinstance(msg, dict):
                continue
            content = msg.get("content")
            blocks = content if isinstance(content, list) else [{"type": "text", "text": content or ""}]
            if kind == "user":
                if any(isinstance(b, dict) and b.get("type") == "tool_result" for b in blocks):
                    events.append(("tool_result", ts, None))
                elif not d.get("isMeta"):
                    events.append(("prompt", ts, None))
            elif kind == "assistant":
                mid = msg.get("id") or f"line{len(events)}"
                if isinstance(msg.get("usage"), dict):
                    usage[mid] = msg["usage"]
                for b in blocks:
                    if not isinstance(b, dict):
                        continue
                    if b.get("type") == "text":
                        for m in MARKER.finditer(b.get("text") or ""):
                            events.append(("marker", ts, m.group(1)))
                    elif b.get("type") in ("tool_use", "server_tool_use"):
                        events.append(("tool_use", ts, b.get("name")))
                events.append(("message", ts, mid))       # after its blocks: a message counts where it ends
    return events, usage


def tokens(u: dict) -> tuple[int, int]:
    def n(k):
        v = u.get(k)
        return int(v) if isinstance(v, (int, float)) else 0
    return (n("input_tokens") + n("cache_creation_input_tokens") + n("cache_read_input_tokens"), n("output_tokens"))


def segments(events: list[tuple], usage: dict) -> tuple[dict[str, dict], list[str], float]:
    """Per-segment {seconds, tool_calls, tokens_in, tokens_out}; marker ids in first-seen order; session seconds."""
    if not events:
        raise UsageError("no usable lines in the transcript")
    start = next((ts for k, ts, _ in events if k == "prompt"), events[0][1])
    end = max(ts for k, ts, _ in events if k in ("message", "tool_result", "marker", "tool_use"))
    segs: dict[str, dict] = {}
    order: list[str] = []

    def seg(name):
        return segs.setdefault(name, {"seconds": 0.0, "tool_calls": 0, "tokens_in": 0, "tokens_out": 0})

    current, cur_start, last_result, seen_mid = "_setup", start, None, {}
    for kind, ts, payload in events:
        if kind == "marker":
            name = payload
            if name.upper() == "END":
                stop = last_result if (current != "_setup" and last_result and last_result > cur_start) else ts
                if current not in ("_setup", "_output") and stop == ts:
                    stop = cur_start           # no tools since the marker: composing time goes to _output
                seg(current)["seconds"] += (stop - cur_start).total_seconds()
                current, cur_start = "_output", stop
                continue
            seg(current)["seconds"] += (ts - cur_start).total_seconds()
            current, cur_start = name, ts
            if name not in order:
                order.append(name)
            seg(name)
        elif kind == "tool_use":
            seg(current)["tool_calls"] += 1
        elif kind == "tool_result":
            last_result = ts
        elif kind == "message":
            seen_mid[payload] = current
    seg(current)["seconds"] += max(0.0, (end - cur_start).total_seconds())
    for mid, name in seen_mid.items():
        ti, to = tokens(usage.get(mid) or {})
        seg(name)["tokens_in"] += ti
        seg(name)["tokens_out"] += to
    return segs, order, (end - start).total_seconds()


def read_plan(path: Path | None, bkey: str) -> list[str]:
    if not path or not path.is_file():
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return [r["id"] for r in csv.DictReader(f) if batch_key(r.get("batch", "")) == bkey.split("_retry")[0]]


def natural(s: str) -> list:
    return [int(p) if p.isdigit() else p for p in re.split(r"(\d+)", s)]


def write_rows(timings: Path, bkey: str, rows: list[list]) -> None:
    """Replace the batch's rows (template rows included); keep the others; group rows by batch."""
    keep = []
    if timings.is_file():
        with open(timings, newline="", encoding="utf-8-sig") as f:
            rdr = csv.DictReader(f)
            for r in rdr:
                if batch_key(r.get("batch", "")) != bkey:
                    keep.append([r.get(c, "") for c in COLUMNS])
    allrows = sorted(keep + rows, key=lambda r: natural(batch_key(r[0])))   # stable: order kept within a batch
    timings.parent.mkdir(parents=True, exist_ok=True)
    with open(timings, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(COLUMNS)
        w.writerows(allrows)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("transcript", help="the session's JSONL transcript")
    ap.add_argument("--batch", help="batch number or name (03, 3, batch_03_retry1, prep)")
    ap.add_argument("--prep", action="store_true", help="a preparation session: one '_prep' row")
    ap.add_argument("--timings", help="timings.csv to update (its batch rows are replaced)")
    ap.add_argument("--plan", help="batch_plan.csv, to warn about missing markers (default: beside --timings)")
    ap.add_argument("--dry-run", action="store_true", help="print the rows, write nothing")
    args = ap.parse_args(argv)
    try:
        if args.prep:
            args.batch = "prep"
        if not args.batch:
            raise UsageError("--batch is required (or --prep)")
        if not args.timings and not args.dry_run:
            raise UsageError("--timings is required (or --dry-run)")
        bkey = batch_key(args.batch)
        shown = re.sub(r"^batch[_-]?", "", args.batch.strip(), flags=re.I)   # as written in batch_plan.csv
        events, usage = read_events(Path(args.transcript))
        segs, order, session_s = segments(events, usage)
        name = Path(args.transcript).name
        warnings = []
        if bkey == "prep":
            tot = {k: sum(s[k] for s in segs.values()) for k in ("tool_calls", "tokens_in", "tokens_out")}
            rows = [["prep", "_prep", f"{session_s:.1f}", tot["tool_calls"], tot["tokens_in"], tot["tokens_out"],
                     tot["tokens_in"] + tot["tokens_out"], f"transcript {name}"]]
        else:
            plan = read_plan(Path(args.plan) if args.plan else (Path(args.timings).parent / "batch_plan.csv"
                                                                if args.timings else None), bkey)
            if not order:
                warnings.append("no '>>> <id>' markers found: record batch totals instead (question_id '*')")
            for qid in plan:
                if qid not in segs:
                    warnings.append(f"{qid}: no marker; its time and tool calls are in the question before it")
            for qid in order:
                if plan and qid not in plan:
                    warnings.append(f"{qid}: marker for a question that is not in batch {args.batch}'s plan")
            rows = []
            for qid in ["_setup"] + order + ["_output"]:
                if qid in segs:
                    s = segs[qid]
                    rows.append([shown, qid, f"{s['seconds']:.1f}", s["tool_calls"], s["tokens_in"], s["tokens_out"],
                                 s["tokens_in"] + s["tokens_out"], f"transcript {name}"])
        if args.dry_run or not args.timings:
            w = csv.writer(sys.stdout, lineterminator="\n")
            w.writerow(COLUMNS)
            w.writerows(rows)
        else:
            write_rows(Path(args.timings), bkey, rows)
            q = [r for r in rows if not str(r[1]).startswith("_")]
            print(f"batch {args.batch}: {len(q)} question row(s) + {len(rows) - len(q)} overhead row(s), session "
                  f"{session_s:.1f} s, {sum(int(r[3]) for r in rows)} tool calls -> {args.timings}")
        for wmsg in warnings:
            print(f"WARN: {wmsg}", file=sys.stderr)
        return 0
    except (UsageError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())

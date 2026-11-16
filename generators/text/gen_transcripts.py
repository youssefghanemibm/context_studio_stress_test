#!/usr/bin/env python3
"""TX family part 'transcripts': TX001-TX006 (meeting transcripts), TX021-TX030 and TX061-TX069 (filler
call notes, scripts, handovers, stand-ups, log excerpt) and TX070-TX072 (Jira export, chat export,
email thread as JSON). Writes only these file ids in corpus/upload/text/ and
manifests/text.transcripts.facts.yaml.

    python -I generators/text/gen_transcripts.py [--out corpus/upload/text] [--only TX001,TX070]
"""
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import argparse  # noqa: E402
import json  # noqa: E402

from generators.common import util  # noqa: E402
from generators.text.transcripts_lib import common as C  # noqa: E402
from generators.text.transcripts_lib.common import Facts, scan_text, MY_IDS, OUT_DIR, FAMILY  # noqa: E402
from generators.text.transcripts_lib.meetings_common import calibrate  # noqa: E402
from generators.text.transcripts_lib import meeting_tx001, meeting_tx002, meeting_tx003, meeting_short  # noqa: E402
from generators.text.transcripts_lib import fillers_docs, fillers_standups, jira, chat, emails  # noqa: E402

TRANSCRIPTS = [
    ("TX001", meeting_tx001.build, 17800, 20500, 2.8),
    ("TX002", meeting_tx002.build, 17800, 20500, 2.8),
    ("TX003", meeting_tx003.build, 17800, 20500, 2.8),
    ("TX004", meeting_short.build_tx004, 9500, 11200, 2.7),
    ("TX005", meeting_short.build_tx005, 7800, 9200, 2.7),
    ("TX006", meeting_short.build_tx006, 6400, 7600, 2.7),
]


def clean(only: set[str]) -> None:
    for p in sorted(OUT_DIR.glob("TX*")):
        fid = p.name[:5]
        if fid in MY_IDS and fid in only:
            p.unlink()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(OUT_DIR), help="ignored: output is always corpus/upload/text")
    ap.add_argument("--only", default="", help="comma-separated file ids to (re)write")
    args = ap.parse_args()
    only = {x.strip() for x in args.only.split(",") if x.strip()} & set(MY_IDS) if args.only else set(MY_IDS)
    if args.only and not only:
        return 0
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    clean(only)
    facts = Facts()
    summary = []

    def emit_text(fid, doc, unit):
        txt = doc.text()
        scan_text(fid, txt)
        if fid in only:
            doc.write()
        summary.append((doc.path, len(txt.encode("utf-8")), unit))

    for fid, build, lo, hi, w in TRANSCRIPTS:
        m, n = calibrate(fid, build, facts, lo, hi, w)
        emit_text(fid, m.doc, f"{len(m.doc.lines)} lines, {n} words")
    for fid, build, lo, hi, w in fillers_standups.STANDUPS:
        m, n = calibrate(fid, build, facts, lo, hi, w)
        emit_text(fid, m.doc, f"{len(m.doc.lines)} lines, {n} words")
    for fn in fillers_docs.DOCS:
        doc = fn(facts)
        emit_text(doc.fid, doc, f"{len(doc.lines)} lines")

    for mod, fid in ((jira, "TX070"), (chat, "TX071"), (emails, "TX072")):
        tmp = Facts()
        builder = mod.build
        res = builder(tmp)
        doc = res[0] if isinstance(res, tuple) else res
        indent = 2 if mod is emails else 1
        txt = json.dumps(doc, ensure_ascii=False, indent=indent) + "\n"
        # CHUB-415's world summary names the CODEOWNERS team (key ticket, included verbatim; see notes)
        scan_text(fid, txt, allow=["hub-squad-recoveries-docs"] if fid == "TX070" else None)
        if fid in only:
            mod.PATH.write_text(txt, encoding="utf-8")
        facts.entries.extend(tmp.entries)
        if mod is jira:
            unit = f"{len(doc['issues'])} tickets"
        elif mod is chat:
            unit = f"{len(doc['messages'])} messages"
        else:
            unit = f"{len(doc['messages'])} emails"
        summary.append((mod.PATH, len(txt.encode("utf-8")), unit))

    files = {e["file"] for e in facts.entries}
    out = util.write_manifest(FAMILY, facts.entries)
    total = 0
    for path, size, unit in sorted(summary, key=lambda x: x[0].name):
        total += size
        print(f"{util.rel(path)} {size} {unit}")
    print(f"[text.transcripts] {len(summary)} files, {total / 1e6:.2f} MB, {len(facts.entries)} facts -> {util.rel(out)}")
    assert total <= 15_000_000, "family part over its 15 MB budget"
    return 0


if __name__ == "__main__":
    sys.exit(main())

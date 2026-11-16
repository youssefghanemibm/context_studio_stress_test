#!/usr/bin/env python3
"""TX family part 'messages': email threads (TX007-TX020), markdown minutes, logs and filler
(TX031-TX060) and HTML letter / newsletter / notes (TX073-TX075).

    .venv/bin/python -I generators/text/gen_messages.py [--out corpus/upload/text] [--only TX007,TX031]

Writes only its own file ids (never resets the shared folder) and manifests/text.messages.facts.yaml.
Every planted fact is resolved through harness/extract.py before the manifest is written, and
exclusive needles are checked to occur only at their locator.
"""
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import argparse
import re

import yaml

from generators.common import util
from generators.text.messages_lib import core
from generators.text.messages_lib.emails import EMAILS
from generators.text.messages_lib.minutes import MINUTES
from generators.text.messages_lib.filler import FILLER
from generators.text.messages_lib.html_docs import HTML_DOCS
from harness import extract as X

BUILDERS = {**EMAILS, **MINUTES, **FILLER, **HTML_DOCS}
OWNED = ([f"TX{n:03d}" for n in range(7, 21)] + [f"TX{n:03d}" for n in range(31, 61)]
         + [f"TX{n:03d}" for n in (73, 74, 75)])

# Strings that must never appear in this part's files, except in the listed file ids. They are
# other files' exclusive facts (or guarded values) that generic prose could otherwise leak.
FORBIDDEN = [
    (r"\b41\s?%", ()), (r"186,400", ("TX011",)), (r"41,250", ()), (r"1,140", ("TX010",)),
    (r"310,000", ("TX019",)), (r"207731", ("TX019",)), (r"\bAUC\b", ()), (r"0\.87", ()),
    (r"\b3\.1\s?%", ()), (r"02:15", ()), (r"second Tuesday", ()), (r"CICSPRD", ()), (r"CLRPLAN1", ()),
    (r"MAXDEPTH", ()), (r"hub-squad-recoveries-docs", ()), (r"notification\.fraud-notice", ()),
    (r"FRD_REFER", ()), (r"CLRCM040", ()), (r"200\s?Gi", ()), (r"partitions", ()), (r"31\.2", ()),
    (r"CLRFR140", ()), (r"FR-REQ-014", ()), (r"0\.5\s?%", ()), (r"£0\.01", ()), (r"0\.001\s?%", ()),
    (r"2,318", ()), (r"611\.9", ()), (r"97\.3", ()), (r"97\.8", ()), (r"(?<![\d,])41\.2\s?%", ()), (r"18\.7\s?%", ()),
    (r"(?<![\d,])36\.5\s?%", ()), (r"\b412\b", ()), (r"\b2\.8\s?%", ()), (r"\b2\.3\s?%", ("TX075",)), (r"\b2\.2\s?%", ()),
    (r"\b2\.4\s?%", ()), (r"PSI\b", ()), (r"0\.06\b", ()), (r"retention of 14 days", ()),
    (r"Brynholt", ()), (r"Calderbank", ()), (r"648\.2", ()), (r"23:30\s?[–-]\s?03:30", ()),
    (r"2027-01-23|23 January 2027", ()), (r"cdw-ro-02", ()), (r"CLRFR990", ()), (r"recon\.daily_diff", ()),
    (r"Larchmont", ()), (r"FRO-CHK", ()), (r"5,150", ()), (r"12,480", ()), (r"WME", ()), (r"CLR\.RSVMOVE\.OUT", ()),
    (r"@corvane/clara-platform", ()), (r"LEGACY_SKADE_REF", ()), (r"impact tolerance", ()),
    (r"Context Studio|knowledge graph|\bRAG\b|\bLLM\b", ()),
]


def write_file(doc, out_dir: pathlib.Path) -> pathlib.Path:
    path = out_dir / doc.filename
    if hasattr(doc, "html"):
        text = doc.html()
    else:
        text = doc.text()
    path.write_text(text, encoding="utf-8", newline="\n")
    return path


def verify(doc, path: pathlib.Path) -> list[str]:
    errs = []
    full = path.read_text(encoding="utf-8")
    full_n = X.normalize(full)
    for i, f in enumerate(doc.facts, 1):
        fid = f"{doc.fid}-F{i:03d}"
        try:
            res = X.resolve(str(path), f.locator)
        except Exception as exc:
            errs.append(f"{fid}: locator error {exc}")
            continue
        if not X.match(f.needle, res, "exact"):
            errs.append(f"{fid}: needle {f.needle!r} not at locator {f.locator} -> {X.normalize(res)[:200]!r}")
            continue
        if f.exclusive:
            n = X.normalize(f.needle)
            if full_n.count(n) != X.normalize(res).count(n):
                errs.append(f"{fid}: exclusive needle {f.needle!r} also occurs outside its locator")
    return errs


def scan_forbidden(fid: str, text: str) -> list[str]:
    errs = []
    for pat, allowed in FORBIDDEN:
        if fid in allowed:
            continue
        m = re.search(pat, text, flags=re.I if pat.startswith("Context") else 0)
        if m:
            errs.append(f"{fid}: forbidden pattern {pat!r} found: {text[max(0, m.start()-60):m.end()+60]!r}")
    return errs


def unit_count(path: pathlib.Path) -> str:
    if path.suffix == ".html":
        return f"{path.read_text(encoding='utf-8').count('<p')} paras"
    n = path.read_text(encoding="utf-8").count("\n")
    return f"{n} lines"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(core.OUT_DIR))
    ap.add_argument("--only", default="")
    args, _ = ap.parse_known_args(argv)
    out_dir = pathlib.Path(args.out)
    if not out_dir.is_absolute():
        out_dir = ROOT / out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    only = [x.strip() for x in args.only.split(",") if x.strip()]
    ids = [f for f in OWNED if not only or f in only]
    if only and not ids:
        print("text.messages: nothing to do for --only", args.only)
        return 0

    docs, problems = [], []
    for fid in ids:
        doc = BUILDERS[fid]()
        # remove any stale file for this id with a different slug (own ids only)
        for old in out_dir.glob(f"{fid}_*"):
            if old.name != doc.filename:
                old.unlink()
        path = write_file(doc, out_dir)
        problems += verify(doc, path)
        problems += scan_forbidden(fid, path.read_text(encoding="utf-8"))
        docs.append((doc, path))

    # cross-file leak check for exclusive needles within this part
    texts = {d.fid: X.normalize(p.read_text(encoding="utf-8")) for d, p in docs}
    for d, p in docs:
        for f in d.facts:
            if f.exclusive:
                n = X.normalize(f.needle)
                for ofid, t in texts.items():
                    if ofid != d.fid and n in t:
                        problems.append(f"{d.fid}: exclusive needle {f.needle!r} leaks into {ofid}")

    if problems:
        for p in problems:
            print("PROBLEM", p)
        return 1

    entries = []
    for d, _ in docs:
        entries += d.manifest_entries()
    mpath = util.MANIFESTS / f"{core.FAMILY}.facts.yaml"
    if only and mpath.exists():
        keep = yaml.safe_load(mpath.read_text(encoding="utf-8")) or []
        regenerated = {d.fid for d, _ in docs}
        keep = [e for e in keep if e["fact_id"].split("-F")[0] not in regenerated]
        entries = keep + entries
    util.write_manifest(core.FAMILY, entries)

    for d, p in docs:
        print(f"{util.rel(p)} {p.stat().st_size} {unit_count(p)}")
    print(f"text.messages: {len(docs)} files, {len(entries)} manifest entries -> {util.rel(mpath)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

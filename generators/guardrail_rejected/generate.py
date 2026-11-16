#!/usr/bin/env python3
"""Guardrail probes (GP001-GP008) and rejected-format files (RJ001-RJ010).

    .venv/bin/python -I generators/guardrail_rejected/generate.py [--only GP003,RJ004] [--no-check]

Writes corpus/upload/guardrail/GP0NN_*, corpus/rejected/RJ0NN_*, manifests/guardrail.facts.yaml and
manifests/rejected.facts.yaml. Only our own file ids are deleted and rewritten; the folders are never reset.
Ends with one summary line per file: <file> <bytes> <pages|rows|lines|...>.
"""
from __future__ import annotations

import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import argparse
import csv
import zipfile

import yaml

from generators.common import util
from generators.guardrail_rejected import gp_files, rj_files
from generators.guardrail_rejected.common import GP_DIR, RJ_DIR, W, remove_own, selfcheck

MANIFESTS = {"GP": "guardrail", "RJ": "rejected"}


def _unit_count(path: pathlib.Path) -> str:
    ext = path.suffix.lower()
    try:
        if ext == ".csv":
            with open(path, newline="", encoding="utf-8") as fh:
                return f"{sum(1 for _ in csv.reader(fh)) - 1} rows"
        if ext == ".xlsx":
            from openpyxl import load_workbook
            wb = load_workbook(path, read_only=True)
            return ", ".join(f"{ws.title}:{ws.max_row} rows" for ws in wb.worksheets)
        if ext == ".pdf":
            import pymupdf
            with pymupdf.open(str(path)) as d:
                return f"{d.page_count} pages"
        if ext == ".docx":
            import docx
            return f"{len(docx.Document(str(path)).paragraphs)} paragraphs"
        if ext in (".png", ".jpg"):
            from PIL import Image
            with Image.open(path) as im:
                return f"1 image {im.size[0]}x{im.size[1]}"
        if ext == ".zip":
            with zipfile.ZipFile(path) as z:
                return f"{len(z.namelist())} members"
        if ext in (".msg", ".vsdx", ".odt", ".eml", ".rtf"):
            from harness import extract as X
            return f"{len(X.derived_text(path).splitlines())} derived lines"
        return f"{len(path.read_text(encoding='utf-8').splitlines())} lines"
    except Exception as exc:  # noqa: BLE001
        return f"? ({type(exc).__name__})"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", help="ignored (outputs go to corpus/upload/guardrail and corpus/rejected)")
    ap.add_argument("--only", help="comma-separated file ids to rebuild (manifests are merged)")
    ap.add_argument("--no-check", action="store_true", help="skip the locator self-check")
    args = ap.parse_args(argv)

    builders = {**gp_files.BUILDERS, **rj_files.BUILDERS}
    only = [x.strip().upper() for x in args.only.split(",")] if args.only else sorted(builders)
    unknown = [x for x in only if x not in builders]
    if unknown:
        ap.error(f"unknown file ids {unknown}")

    if not args.only:
        remove_own(GP_DIR, "GP")
        remove_own(RJ_DIR, "RJ")
    else:
        for fid in only:
            folder = GP_DIR if fid.startswith("GP") else RJ_DIR
            for p in folder.glob(f"{fid}_*"):
                p.unlink()

    # GP builders share a registry of used fake values, so they always run in id order
    facts: dict[str, list[dict]] = {}
    paths: dict[str, pathlib.Path] = {}
    for fid in sorted(only):
        F = builders[fid]()
        facts[fid] = F.items
        paths[fid] = F.path
        planted = {e.get("placement") for e in F.items}
        missing = [p["placement_id"] for p in W.placements_for(fid) if p["placement_id"] not in planted]
        if missing:
            raise SystemExit(f"{fid}: placements not planted: {missing}")

    if not args.no_check:
        problems = selfcheck([e for items in facts.values() for e in items])
        if problems:
            print("\n".join(problems))
            raise SystemExit(f"self-check failed: {len(problems)} problem(s)")

    for prefix, name in MANIFESTS.items():
        entries = [e for fid, items in facts.items() if fid.startswith(prefix) for e in items]
        if args.only:
            mf = util.MANIFESTS / f"{name}.facts.yaml"
            if mf.exists():
                old = yaml.safe_load(mf.read_text(encoding="utf-8")) or []
                entries += [e for e in old if e["fact_id"].split("-F")[0] not in facts]
        if entries or not args.only:
            util.write_manifest(name, entries)

    for fid in sorted(paths):
        p = paths[fid]
        print(f"{util.rel(p)} {p.stat().st_size} {_unit_count(p)}")
    n = sum(len(v) for v in facts.values())
    print(f"[guardrail_rejected] {len(paths)} files, {n} facts")
    return 0


if __name__ == "__main__":
    sys.exit(main())

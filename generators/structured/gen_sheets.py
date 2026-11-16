#!/usr/bin/env python3
"""Structured family part 'sheets': XLSX workbooks ST001-ST012 and CSV extracts ST013-ST026.

    python -I generators/structured/gen_sheets.py [--out corpus/upload/structured] [--only ST001,ST013,...]

Writes only its own file ids (never resets the shared folder) and manifests/structured.sheets.facts.yaml.
Deterministic: all randomness from generators.common.util.rng, no wall clock, fixed zip timestamps.
Prints one summary line per file: <file> <bytes> <units>.
"""
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import argparse  # noqa: E402

from generators.common import util  # noqa: E402
from generators.structured.sheets_lib import csv_files, xlsx_a, xlsx_b  # noqa: E402
from generators.structured.sheets_lib.common import FAMILY, MY_IDS, OUT_DEFAULT, W  # noqa: E402
from generators.structured.sheets_lib.ctx import Ctx  # noqa: E402


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default=str(OUT_DEFAULT))
    ap.add_argument("--only", default=None, help="comma-separated file ids; ids outside ST001-ST026 are ignored")
    args = ap.parse_args(argv)
    only = None
    if args.only:
        req = {x.strip().upper() for x in args.only.split(",") if x.strip()}
        only = req & set(MY_IDS)
        if not only:
            print("gen_sheets: no ST001-ST026 ids requested; nothing to do")
            return 0
    out = pathlib.Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    for fid in MY_IDS:
        if only is None or fid in only:
            p = out / W.anchor(fid)["filename"]
            if p.exists():
                p.unlink()
    ctx = Ctx(out, only)
    for build in csv_files.CSV_BUILDERS:
        build(ctx)
    for build in xlsx_a.XLSX_A + xlsx_b.XLSX_B:
        build(ctx)
    entries = ctx.facts.finish()
    util.write_manifest(FAMILY, entries)
    for name, size, units in sorted(ctx.summary):
        if only is None or name[:5] in only:
            print(f"{name} {size} {units}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

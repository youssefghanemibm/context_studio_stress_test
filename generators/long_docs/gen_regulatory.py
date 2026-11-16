#!/usr/bin/env python3
"""long_docs part 'regulatory': LD003-LD011, LD021-LD023.

    .venv/bin/python -I generators/long_docs/gen_regulatory.py [--only LD003,LD022]

Writes only its own files in corpus/upload/long_docs/ and manifests/long_docs.regulatory.facts.yaml.
Per-file fact lists are cached in build/cache/ld_regulatory/ so that --only runs can merge.
"""
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import argparse  # noqa: E402
import importlib  # noqa: E402
import time  # noqa: E402

from generators.long_docs.regulatory_lib import common  # noqa: E402

BUILDERS = {
    "LD003": ("ld003", "build", ()),
    "LD004": ("wordings", "build", ("LD004",)),
    "LD005": ("wordings", "build", ("LD005",)),
    "LD006": ("wordings", "build", ("LD006",)),
    "LD007": ("wordings", "build", ("LD007",)),
    "LD008": ("wordings", "build", ("LD008",)),
    "LD009": ("wordings", "build", ("LD009",)),
    "LD010": ("wordings", "build", ("LD010",)),
    "LD011": ("wordings", "build", ("LD011",)),
    "LD021": ("atlas", "build", ()),
    "LD022": ("circulars", "build", ("LD022",)),
    "LD023": ("circulars", "build", ("LD023",)),
}


def units(path: pathlib.Path) -> str:
    if path.suffix == ".pdf":
        import pymupdf
        with pymupdf.open(str(path)) as d:
            return f"{d.page_count} pages"
    if path.suffix == ".doc":
        p = common.CACHE / f"{path.stem}.pages"
        return f"{p.read_text().strip()} pages" if p.exists() else "? pages"
    return "-"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--only", help="comma-separated file ids (default: all of this part)")
    ap.add_argument("--out", help="ignored (output folder is fixed: corpus/upload/long_docs)")
    args = ap.parse_args(argv)
    fids = [f.strip().upper() for f in args.only.split(",")] if args.only else list(BUILDERS)
    fids = [f for f in fids if f in BUILDERS]
    common.OUT_DIR.mkdir(parents=True, exist_ok=True)
    common.CACHE.mkdir(parents=True, exist_ok=True)
    rc = 0
    for fid in fids:
        target = common.out_path(fid)
        if target.exists():
            target.unlink()
        mod_name, fn_name, fargs = BUILDERS[fid]
        mod = importlib.import_module(f"generators.long_docs.regulatory_lib.{mod_name}")
        t0 = time.time()
        out, facts = getattr(mod, fn_name)(*fargs)
        facts.save()
        print(f"{common.util.rel(out)} {out.stat().st_size} {units(out)}  [{len(facts.items)} facts, "
              f"{time.time() - t0:.0f}s]", flush=True)
    common.merge_manifest()
    return rc


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Visuals part B: PPTX decks VS015-VS028 (manifest manifests/visuals.decks_b.facts.yaml).

    .venv/bin/python -I generators/visuals/gen_decks_b.py [--out corpus/upload/visuals] [--only VS015,VS020]

Writes only its own file ids into the shared corpus/upload/visuals/ folder (never resets the folder)
and its own manifest. Deterministic: all variation comes from util.rng(<file id>...), dates from the
world model, and zip members carry a fixed timestamp.
"""
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import argparse

import yaml

from generators.common import util
from world.worldlib import load_world

from generators.visuals.decks_b_lib import decks_1, decks_2, decks_3

MANIFEST = "visuals.decks_b"
BUILDERS = {
    "VS015": decks_1.build_vs015, "VS016": decks_1.build_vs016, "VS017": decks_1.build_vs017,
    "VS018": decks_1.build_vs018, "VS019": decks_1.build_vs019,
    "VS020": decks_2.build_vs020, "VS021": decks_2.build_vs021, "VS022": decks_2.build_vs022,
    "VS023": decks_2.build_vs023, "VS024": decks_2.build_vs024,
    "VS025": decks_3.build_vs025, "VS026": decks_3.build_vs026, "VS027": decks_3.build_vs027,
    "VS028": decks_3.build_vs028,
}
CACHE = ROOT / "build" / "cache" / "vs_decks_b"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(util.UPLOAD / "visuals"))
    ap.add_argument("--only", default="")
    args = ap.parse_args()
    out = pathlib.Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    CACHE.mkdir(parents=True, exist_ok=True)
    W = load_world()
    only = [x.strip() for x in args.only.split(",") if x.strip()]
    todo = only or list(BUILDERS)
    for fid in todo:
        if fid not in BUILDERS:
            raise SystemExit(f"unknown file id {fid}")

    # remove only our own previous outputs for the selected ids
    for fid in todo:
        for old in out.glob(f"{fid}_*"):
            old.unlink()

    entries_by_fid = {}
    cache_file = CACHE / "facts_by_file.yaml"
    if only and cache_file.exists():
        entries_by_fid = yaml.safe_load(cache_file.read_text(encoding="utf-8")) or {}

    summary = []
    for fid in todo:
        deck = BUILDERS[fid](W, out)
        path = deck.save()
        entries_by_fid[fid] = deck.facts.entries
        size = path.stat().st_size
        assert size < 48 * 1000 * 1000, (fid, size)
        summary.append(f"{util.rel(path)} {size} {deck.n}")

    cache_file.write_text(yaml.safe_dump(entries_by_fid, sort_keys=False, allow_unicode=True, width=120),
                          encoding="utf-8")
    entries = [e for fid in sorted(entries_by_fid) for e in entries_by_fid[fid]]
    util.write_manifest(MANIFEST, entries)
    for line in summary:
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())

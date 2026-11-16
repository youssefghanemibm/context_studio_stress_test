#!/usr/bin/env python3
"""Visual decks VS001-VS014 (PowerPoint) for the Corvane corpus: manifest 'visuals.decks_a'.

    python -I generators/visuals/gen_decks_a.py [--out corpus/upload/visuals] [--only VS001,VS007] [--no-check]

Writes only its own file ids into the shared corpus/upload/visuals/ folder (never resets the
folder) and manifests/visuals.decks_a.facts.yaml. Each deck is built by
generators/visuals/decks_a_lib/vsNNN.py; after saving, every non-OCR needle is resolved with
harness/extract.py as a self-check.
"""
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import argparse
import importlib

import yaml

from generators.common import util
from world.worldlib import load_world

FIDS = [f"VS{i:03d}" for i in range(1, 15)]
FAMILY = "visuals.decks_a"


def self_check(facts: list[dict]) -> list[str]:
    from harness import extract as X
    errors = []
    for e in facts:
        loc = e["locator"]
        if X.locator_needs_ocr(loc):
            continue
        try:
            text = X.resolve(e["file"], loc, ocr=False)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{e['fact_id']}: locator error {exc}")
            continue
        if not X.match(e["needle"], text):
            errors.append(f"{e['fact_id']}: needle {e['needle']!r} not in {X.normalize(text)[:300]!r}")
    return errors


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(util.UPLOAD / "visuals"))
    ap.add_argument("--only", default=None)
    ap.add_argument("--no-check", action="store_true")
    args, _unknown = ap.parse_known_args()
    only = [x.strip().upper() for x in args.only.split(",")] if args.only else None
    todo = [f for f in FIDS if not only or f in only]
    if not todo:
        print(f"[{FAMILY}] nothing to do for --only {args.only}")
        return 0
    out = pathlib.Path(args.out)
    if not out.is_absolute():
        out = ROOT / out
    out.mkdir(parents=True, exist_ok=True)
    W = load_world()
    facts_all: list[dict] = []
    summary = []
    failures = []
    for fid in todo:
        for old in out.glob(f"{fid}_*"):
            old.unlink()
        mod = importlib.import_module(f"generators.visuals.decks_a_lib.{fid.lower()}")
        deck = mod.build(W, out)
        facts = deck.finalize_facts()
        path = deck.save(subject="Programme Skerry", keywords="Corvane Mutual; Claims Hub; CLARA")
        if not args.no_check:
            failures += self_check(facts)
        facts_all.extend(facts)
        summary.append(f"{util.rel(path)} {path.stat().st_size} {len(deck.slides)}")
    man = util.MANIFESTS / f"{FAMILY}.facts.yaml"
    if only and man.exists():
        keep = [e for e in (yaml.safe_load(man.read_text(encoding="utf-8")) or [])
                if e.get("fact_id", "")[:5] not in todo]
        facts_all = keep + facts_all
    util.write_manifest(FAMILY, facts_all)
    for line in summary:
        print(line)
    if failures:
        print(f"[{FAMILY}] SELF-CHECK FAILURES ({len(failures)}):")
        for f in failures:
            print("  " + f)
        return 1
    print(f"[{FAMILY}] {len(todo)} decks, {len(facts_all)} facts in manifest")
    return 0


if __name__ == "__main__":
    sys.exit(main())

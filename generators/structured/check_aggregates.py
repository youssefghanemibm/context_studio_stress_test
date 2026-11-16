#!/usr/bin/env python3
"""Recompute every aggregate_source fact of manifests/structured.sheets.facts.yaml from the CSV files.

    python -I generators/structured/check_aggregates.py [--manifest manifests/structured.sheets.facts.yaml]

For each entry with an `aggregate` spec {file, filter, op, column, value} the value is recomputed
from the file on disk and compared; the representative row at the entry's locator must exist.
Exit code 1 on any mismatch.
"""
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import argparse  # noqa: E402

import yaml  # noqa: E402

from generators.structured.sheets_lib import aggregates as A  # noqa: E402


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--manifest", default=str(ROOT / "manifests" / "structured.sheets.facts.yaml"))
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args(argv)
    entries = yaml.safe_load(open(args.manifest, encoding="utf-8")) or []
    cache: dict[str, list[dict]] = {}
    ok = bad = 0
    for e in entries:
        spec = e.get("aggregate")
        if not spec:
            continue
        path = ROOT / spec["file"]
        if not path.exists():
            print(f"FAIL {e['fact_id']}: file missing {spec['file']}")
            bad += 1
            continue
        if spec["file"] not in cache:
            cache[spec["file"]] = A.read_csv_dicts(path)
        rows = cache[spec["file"]]
        got = A.evaluate(rows, spec.get("filter") or {}, spec["op"], spec.get("column"))
        row = e["locator"].get("row")
        rep_ok = isinstance(row, int) and 1 <= row <= len(rows)
        if A.values_equal(got, spec["value"]) and rep_ok:
            ok += 1
            if args.verbose:
                print(f"PASS {e['fact_id']}: {spec['op']} {spec.get('filter')} = {got}")
        else:
            bad += 1
            print(f"FAIL {e['fact_id']}: {spec['op']} {spec.get('filter')} expected {spec['value']!r} got {got!r}"
                  + ("" if rep_ok else f" (representative row {row} out of range)"))
    print(f"aggregates: {ok} PASS, {bad} FAIL")
    return 1 if bad or not ok else 0


if __name__ == "__main__":
    sys.exit(main())

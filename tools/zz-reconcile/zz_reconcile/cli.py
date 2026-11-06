"""Command line entry point."""
import argparse
import datetime as dt

import yaml

from zz_reconcile import clara, compare, hub, report


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="zz-reconcile")
    ap.add_argument("--config", required=True)
    ap.add_argument("--business-date", required=True, type=dt.date.fromisoformat)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)
    with open(args.config, encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh)
    left = clara.load(cfg["clara"], cfg["products"], args.business_date)
    right = hub.load(cfg["hub"], cfg["products"], args.business_date)
    diffs = compare.diff(left, right, cfg["tolerance"])
    if args.dry_run:
        report.print_diffs(diffs)
    else:
        report.write(cfg["target"], args.business_date, diffs)
    return 0 if not diffs else 2

#!/usr/bin/env python3
"""Structured family, part 'specs': ST027-ST060 (JSON, XML, YAML/YML, wiki HTML).

    python -I generators/structured/gen_specs.py [--out corpus/upload/structured] [--only ST030,ST035]

Writes only its own file ids (ST027-ST060) into the shared structured folder, the manifest
manifests/structured.specs.facts.yaml, and prints one summary line per file. Every manifest
needle is resolved with harness/extract.py before the run finishes (use --no-verify to skip).
"""
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import argparse  # noqa: E402

from generators.common import util  # noqa: E402
from specs_lib import core  # noqa: E402


def load_builders() -> dict:
    from specs_lib import json_specs, xml_specs, yaml_specs, wiki_specs
    out = {}
    for m in (json_specs, xml_specs, yaml_specs, wiki_specs):
        out.update(m.BUILDERS)
    return out


def verify(facts: list[dict]) -> list[str]:
    from harness import extract as X
    errs = []
    for e in facts:
        try:
            text = X.resolve(ROOT / e["file"], e["locator"], repo_root=ROOT, ocr=False)
        except Exception as exc:  # noqa: BLE001
            errs.append(f"{e['fact_id']}: locator error {exc}")
            continue
        if not X.match(e["needle"], text):
            errs.append(f"{e['fact_id']}: needle {e['needle']!r} not in {X.normalize(text)[:300]!r}")
    return errs


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", default=str(util.UPLOAD / core.FAMILY_DIR))
    ap.add_argument("--only", default="")
    ap.add_argument("--no-verify", action="store_true")
    args, _unknown = ap.parse_known_args()
    out = pathlib.Path(args.out)
    if not out.is_absolute():
        out = ROOT / out
    out.mkdir(parents=True, exist_ok=True)
    only = [x.strip() for x in args.only.split(",") if x.strip()]
    targets = [f for f in core.FILE_IDS if not only or f in only]
    if only and not targets:
        print("[structured/specs] nothing to do for --only", args.only)
        return 0
    builders = load_builders()
    missing = [f for f in core.FILE_IDS if f not in builders]
    if missing:
        raise SystemExit(f"no builder for {missing}")
    built = {fid: builders[fid](out) for fid in core.FILE_IDS}
    problems = []
    for fid in targets:
        b = built[fid]
        problems += core.scan_forbidden(fid, b.content.decode("utf-8"))
    if problems:
        raise SystemExit("forbidden content:\n" + "\n".join(problems))
    for fid in targets:
        for old in out.glob(f"{fid}_*"):
            old.unlink()
        (out / core.fname(fid)).write_bytes(built[fid].content)
    all_facts = [e for fid in core.FILE_IDS for e in built[fid].facts]
    util.write_manifest(core.MANIFEST_NAME, all_facts)
    if not args.no_verify:
        errs = verify([e for e in all_facts if e["file"].rsplit("/", 1)[-1][:5] in targets])
        if errs:
            raise SystemExit("manifest self-check failed:\n" + "\n".join(errs))
    for fid in targets:
        p = out / core.fname(fid)
        print(f"{util.rel(p)} {p.stat().st_size} {built[fid].count}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

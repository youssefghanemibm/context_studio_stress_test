#!/usr/bin/env python3
"""Visuals part 'rasterdocs': image-led DOCX (VS029-VS039) and raster PDFs/posters (VS040-VS050).

    python -I generators/visuals/gen_rasterdocs.py [--only VS033,VS044] [--ocr-check] [--count-pages]

Writes only its own files in corpus/upload/visuals/ and manifests/visuals.rasterdocs.facts.yaml.
Every fact needle in an image is verified later by harness/verify_corpus.py with Apple Vision OCR;
--ocr-check runs the same OCR (shared cache) right after building.
"""
from __future__ import annotations

import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import argparse  # noqa: E402
import importlib  # noqa: E402
import traceback  # noqa: E402

import yaml  # noqa: E402

from generators.common import util  # noqa: E402

MANIFEST_NAME = "visuals.rasterdocs"
OWN = [f"VS{i:03d}" for i in range(29, 51)]
BUILDERS = {
    "VS029": ("docs_a", "build_vs029"), "VS030": ("docs_a", "build_vs030"), "VS031": ("docs_a", "build_vs031"),
    "VS032": ("docs_a", "build_vs032"), "VS033": ("docs_b", "build_vs033"), "VS034": ("docs_b", "build_vs034"),
    "VS035": ("docs_b", "build_vs035"), "VS036": ("docs_c", "build_vs036"), "VS037": ("docs_c", "build_vs037"),
    "VS038": ("docs_c", "build_vs038"), "VS039": ("docs_c", "build_vs039"),
    "VS040": ("pdfs_a", "build_vs040"), "VS041": ("pdfs_a", "build_vs041"), "VS042": ("pdfs_a", "build_vs042"),
    "VS043": ("pdfs_a", "build_vs043"), "VS044": ("pdfs_a", "build_vs044"), "VS045": ("pdfs_b", "build_vs045"),
    "VS046": ("pdfs_b", "build_vs046"), "VS047": ("pdfs_b", "build_vs047"), "VS048": ("pdfs_b", "build_vs048"),
    "VS049": ("pdfs_b", "build_vs049"), "VS050": ("pdfs_b", "build_vs050"),
}


def unit_label(path: pathlib.Path, n: int) -> str:
    return f"{n} {'figures' if path.suffix == '.docx' else 'pages'}"


def count_docx_pages(path: pathlib.Path) -> int | None:
    import pymupdf
    tmp = util.BUILD / "cache" / "vs_raster" / "pages"
    try:
        out = util.soffice_convert(path, "pdf", tmp, profile_key="vs_rasterdocs_pages", timeout=300)
        with pymupdf.open(out) as d:
            n = d.page_count
        out.unlink()
        return n
    except Exception as exc:  # pragma: no cover
        print(f"  page count failed for {path.name}: {exc}")
        return None


def ocr_check(entries: list[dict]) -> int:
    from harness import extract as X
    bad = 0
    for e in entries:
        loc = e["locator"]
        try:
            txt = X.resolve(str(ROOT / e["file"]), loc)
        except Exception as exc:
            print(f"  FAIL {e['fact_id']}: {exc}")
            bad += 1
            continue
        mode = "ocr_fuzzy" if X.locator_needs_ocr(loc) else "exact"
        if not X.match(e["needle"], txt, mode):
            bad += 1
            print(f"  FAIL {e['fact_id']} needle {e['needle']!r} not in {loc.get('kind')} text: {X.normalize(txt)[:300]!r}")
    return bad


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", help="comma-separated file ids (others keep their manifest entries)")
    ap.add_argument("--ocr-check", action="store_true", help="OCR every image fact after building")
    ap.add_argument("--count-pages", action="store_true", help="count DOCX pages via LibreOffice")
    ap.add_argument("--out", help="ignored (fixed output folder corpus/upload/visuals)")
    args = ap.parse_args(argv)
    todo = OWN if not args.only else [x.strip().upper() for x in args.only.split(",") if x.strip()]
    for t in todo:
        if t not in OWN:
            raise SystemExit(f"{t} is not owned by this part")
    man_path = util.MANIFESTS / f"{MANIFEST_NAME}.facts.yaml"
    keep: list[dict] = []
    if args.only and man_path.exists():
        old = yaml.safe_load(man_path.read_text(encoding="utf-8")) or []
        keep = [e for e in old if e["fact_id"].split("-F")[0] not in todo]
    (util.UPLOAD / "visuals").mkdir(parents=True, exist_ok=True)
    entries: list[dict] = []
    failures = 0
    for fid in todo:
        mod_name, fn = BUILDERS[fid]
        try:
            mod = importlib.import_module(f"generators.visuals.raster_lib.{mod_name}")
            builder = getattr(mod, fn)
        except (ImportError, AttributeError) as exc:
            print(f"{fid}: builder missing ({exc})")
            failures += 1
            continue
        # delete only our own previous output for this id
        for old in (util.UPLOAD / "visuals").glob(f"{fid}_*"):
            old.unlink()
        try:
            items, path, units = builder()
        except Exception:
            traceback.print_exc()
            failures += 1
            continue
        p = pathlib.Path(path)
        if args.count_pages and p.suffix == ".docx":
            pages = count_docx_pages(p)
            print(f"{util.rel(p)} {p.stat().st_size} {pages} pages ({units} figures)")
        else:
            print(f"{util.rel(p)} {p.stat().st_size} {unit_label(p, units)}")
        entries.extend(items)
    util.write_manifest(MANIFEST_NAME, keep + entries)
    if args.ocr_check:
        bad = ocr_check(entries)
        print(f"ocr-check: {len(entries) - bad}/{len(entries)} facts resolve")
        failures += bad
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())

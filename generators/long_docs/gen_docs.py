#!/usr/bin/env python
"""Long-document part 'docs': LD013-LD020 (DOCX) and LD024-LD030 (PDF).

    .venv/bin/python -I generators/long_docs/gen_docs.py [--out corpus/upload/long_docs] [--only LD013,LD024]
                                                        [--jobs N] [--no-verify]

Writes only its own file ids into corpus/upload/long_docs/ and manifests/long_docs.docs.facts.yaml.
DOCX files are also converted with LibreOffice (cache: build/cache/ld_docs/) to measure pages and to add
page hints; three of the PDFs are produced that way ("Word export" look), four with reportlab.
"""
from __future__ import annotations

import sys
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))

import argparse  # noqa: E402
import concurrent.futures as cf  # noqa: E402
import importlib  # noqa: E402
import multiprocessing  # noqa: E402
import shutil  # noqa: E402
import traceback  # noqa: E402

import yaml  # noqa: E402

from generators.common import util  # noqa: E402

MANIFEST = "long_docs.docs"
# file id -> (builder module, output method)
PLAN = {
    "LD013": ("b_ld013", "docx"), "LD014": ("b_ld014", "docx"), "LD015": ("b_ld015", "docx"),
    "LD016": ("b_ld016", "docx"), "LD017": ("b_ld017", "docx"), "LD018": ("b_ld018", "docx"),
    "LD019": ("b_ld019", "docx"), "LD020": ("b_ld020", "docx"),
    "LD024": ("b_ld024", "pdf_rl"), "LD025": ("b_ld025", "pdf_soffice"), "LD026": ("b_ld026", "pdf_rl"),
    "LD027": ("b_ld027", "pdf_soffice"), "LD028": ("b_ld028", "pdf_soffice"), "LD029": ("b_ld029", "pdf_rl"),
    "LD030": ("b_ld030", "pdf_rl"),
}


def _fix_pdf_metadata(src: pathlib.Path, dst: pathlib.Path, doc) -> None:
    import pymupdf
    when = doc.date.replace("-", "")
    with pymupdf.open(str(src)) as pdf:
        pdf.set_metadata({"title": doc.title, "author": doc.author, "subject": doc.subtitle or doc.title,
                          "keywords": doc.doc_id, "creator": "Corvane document template",
                          "producer": "Corvane document services",
                          "creationDate": f"D:{when}090000", "modDate": f"D:{when}090000"})
        pdf.save(str(dst), garbage=3, deflate=True, no_new_id=True)


def build_one(fid: str, out_dir: str, verify: bool = True) -> dict:
    from docs_lib import core, locate
    from docs_lib.docx_r import render_docx
    from docs_lib.pdf_r import render_pdf
    mod_name, method = PLAN[fid]
    mod = importlib.import_module(f"docs_lib.{mod_name}")
    doc = mod.build()
    anchor = core.W.anchor(fid)
    out = pathlib.Path(out_dir) / anchor["filename"]
    for old in pathlib.Path(out_dir).glob(f"{fid}_*"):
        old.unlink()
    problems = []
    if method == "docx":
        render_docx(doc, out)
        pdf = locate.soffice_pdf(out, fid)
        texts = locate.pdf_texts(pdf)
        locate.page_hints(doc, texts)
        pages = len(texts)
    elif method == "pdf_soffice":
        tmp = core.CACHE / "src" / (out.stem + ".docx")
        render_docx(doc, tmp)
        pdf = locate.soffice_pdf(tmp, fid)
        _fix_pdf_metadata(pdf, out, doc)
        texts = locate.pdf_texts(out)
        problems += locate.locate_pdf(doc, out, texts)
        pages = len(texts)
    else:
        render_pdf(doc, out)
        texts = locate.pdf_texts(out)
        problems += locate.locate_pdf(doc, out, texts)
        pages = len(texts)
    facts = doc.all_facts()
    for i, f in enumerate(facts, 1):
        f.fact_id = f"{fid}-F{i:03d}"
    if verify:
        problems += locate.verify(doc, out)
    file_rel = locate.rel(out)
    entries = [f.entry(file_rel) for f in facts if f.locator]
    missing = [f.needle for f in facts if not f.locator]
    if missing:
        problems.append(f"{len(missing)} facts without locator: {missing[:5]}")
    hook = getattr(mod, "post_check", None)
    if hook:
        problems += hook(doc, texts) or []
    return {"fid": fid, "file": file_rel, "bytes": out.stat().st_size, "pages": pages, "entries": entries,
            "problems": problems}


def _worker(args):
    fid, out_dir, verify = args
    try:
        return build_one(fid, out_dir, verify)
    except Exception:  # noqa: BLE001
        return {"fid": fid, "error": traceback.format_exc()}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(util.UPLOAD / "long_docs"))
    ap.add_argument("--only", default="")
    ap.add_argument("--jobs", type=int, default=5)
    ap.add_argument("--no-verify", action="store_true")
    args = ap.parse_args()
    only = [x.strip() for x in args.only.split(",") if x.strip()]
    fids = [f for f in PLAN if not only or f in only]
    if not fids:
        print("gen_docs: nothing to do for --only", args.only)
        return 0
    out_dir = pathlib.Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    work = [(f, str(out_dir), not args.no_verify) for f in fids]
    results = []
    if args.jobs <= 1 or len(work) == 1:
        results = [_worker(w) for w in work]
    else:
        ctx = multiprocessing.get_context("spawn")
        with cf.ProcessPoolExecutor(max_workers=args.jobs, mp_context=ctx) as ex:
            results = list(ex.map(_worker, work))
    rc = 0
    entries = []
    built = set()
    for r in results:
        if "error" in r:
            print(f"[{r['fid']}] ERROR\n{r['error']}")
            rc = 1
            continue
        built.add(r["fid"])
        entries.extend(r["entries"])
        for p in r["problems"]:
            print(f"[{r['fid']}] PROBLEM {p}")
    # keep entries of files not rebuilt in this run
    mpath = util.MANIFESTS / f"{MANIFEST}.facts.yaml"
    if mpath.exists() and only:
        old = yaml.safe_load(mpath.read_text(encoding="utf-8")) or []
        entries.extend(e for e in old if e["fact_id"].split("-F")[0] not in built)
    util.write_manifest(MANIFEST, entries)
    for r in sorted((r for r in results if "error" not in r), key=lambda r: r["fid"]):
        print(f"{r['file']} {r['bytes']} {r['pages']}")
    return rc


if __name__ == "__main__":
    sys.exit(main())

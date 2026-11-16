"""Post-render fact location: PDF page search, DOCX page hints, self-verification via harness.extract."""
from __future__ import annotations

import pathlib
import shutil

from .core import CACHE, Doc, Fact, ROOT, util

from harness import extract as X  # noqa: E402


def soffice_pdf(docx_path: pathlib.Path, key: str) -> pathlib.Path:
    outdir = CACHE / "pdf" / key
    if outdir.exists():
        shutil.rmtree(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    return util.soffice_convert(docx_path, "pdf", outdir, profile_key=f"ld_docs_{key}", timeout=900)


def pdf_texts(pdf_path: pathlib.Path) -> list[str]:
    import pymupdf
    with pymupdf.open(str(pdf_path)) as doc:
        return [p.get_text("text") for p in doc]


def find_pages(texts: list[str], needle: str) -> list[int]:
    return [i + 1 for i, t in enumerate(texts) if X.match(needle, t)]


def find_span(texts: list[str], needle: str) -> tuple[int, int] | None:
    for i in range(len(texts) - 1):
        if X.match(needle, texts[i] + "\n" + texts[i + 1]):
            return i + 1, i + 2
    return None


def locate_pdf(doc: Doc, pdf_path: pathlib.Path, texts: list[str] | None = None) -> list[str]:
    """Set pdf_page locators for every fact of a PDF document. Returns problems."""
    texts = texts if texts is not None else pdf_texts(pdf_path)
    problems = []
    for f in doc.all_facts():
        anchor = getattr(f, "anchor_text", None)
        if f.where == "image":
            pages = find_pages(texts, anchor) if anchor else []
            if not pages:
                problems.append(f"{f.placement or f.statement[:40]}: figure anchor not found")
                continue
            f.locator = {"kind": "pdf_page", "page": pages[0], "ocr": True}
            continue
        pages = find_pages(texts, f.needle)
        if anchor and len(pages) > 1:
            ap = find_pages(texts, anchor)
            near = [p for p in pages if any(abs(p - a) <= 1 for a in ap)]
            pages = near or pages
        if pages:
            f.locator = {"kind": "pdf_page", "page": pages[0]}
            if len(pages) > 1 and f.where not in ("header", "footer"):
                f.notes = ((f.notes + " ") if f.notes else "") + f"(needle also on pages {pages[1:6]})"
            continue
        span = find_span(texts, f.needle)
        if span:
            f.locator = {"kind": "pdf_page", "page": span[0], "end_page": span[1]}
            continue
        problems.append(f"needle not found in PDF: {f.needle!r}")
    return problems


def page_hints(doc: Doc, texts: list[str]) -> None:
    """Add page_hint to docx_para/docx_table locators from the LibreOffice rendering."""
    for f in doc.all_facts():
        if not f.locator or f.locator.get("kind") not in ("docx_para", "docx_table", "docx_footnote"):
            continue
        pages = find_pages(texts, f.needle)
        anchor = getattr(f, "anchor_text", None)
        if anchor and len(pages) > 1:
            ap = find_pages(texts, anchor)
            pages = ([p for p in pages if p in ap] or [p for p in pages if any(abs(p - a) <= 1 for a in ap)]
                     or pages)
        if not pages and anchor:
            pages = find_pages(texts, anchor)
        if not pages:
            span = find_span(texts, f.needle)
            if span:
                pages = [span[0]]
                f.locator["page_hint_end"] = span[1]
        if pages:
            f.locator["page_hint"] = pages[0]


def verify(doc: Doc, file_path: pathlib.Path, ocr: bool = False) -> list[str]:
    """Resolve every locator with the harness and check the needle (OCR facts skipped unless ocr)."""
    problems = []
    for f in doc.all_facts():
        if not f.locator:
            problems.append(f"no locator: {f.needle!r}")
            continue
        needs = X.locator_needs_ocr(f.locator)
        if needs and not ocr:
            continue
        try:
            text = X.resolve(str(file_path), f.locator, ocr=ocr)
        except Exception as exc:  # noqa: BLE001
            problems.append(f"resolve error {exc} for {f.needle!r} at {f.locator}")
            continue
        if not X.match(f.needle, text, "ocr_fuzzy" if needs else "exact"):
            problems.append(f"needle {f.needle!r} not at {f.locator}: {X.normalize(text)[:140]!r}")
    return problems


def rel(p: pathlib.Path) -> str:
    return pathlib.Path(p).resolve().relative_to(ROOT).as_posix()

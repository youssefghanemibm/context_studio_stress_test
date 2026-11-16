#!/usr/bin/env python
"""Locator resolution and full-text extraction for the generated corpus.

This is the verification core: every planted fact in ``manifests/*.facts.yaml`` carries a
locator (see docs/CONVENTIONS.md §5) and this module returns the text found at that locator,
so the verifier can check that the fact's needle really is there.

Library API
-----------
    resolve(file_path, locator, repo_root=ROOT, ocr=True) -> str
    resolve_ex(file_path, locator, repo_root=ROOT, ocr=True) -> Resolved(text, meta, fallback)
    extract_all(file_path, ocr=True) -> list[(locator, text)]     # every textual unit
    iter_units(file_path, ocr=True) -> Iterator[(locator, text)]  # streaming variant
    match(needle, text, mode="exact" | "ocr_fuzzy") -> bool
    normalize(text) -> str
    locator_needs_ocr(locator) -> bool
    ocr_jobs(file_path) -> list[job];  run_ocr_job(job)           # parallel pre-OCR
    set_code_repo_root(path)                                      # generated git repos

CLI
---
    python -I harness/extract.py <file> --locator '<json>' [--needle TEXT] [--meta]
    python -I harness/extract.py <file> --all [--no-ocr]          # JSONL on stdout

Locator kinds beyond the CONVENTIONS table (all optional extensions):
    pdf_page.end_page, docx_para.end_para_index   inclusive ranges (for split facts)
    docx_endnote {endnote_id}
    docx_tracked.id                               select by w:id instead of index
    zip_member {member, inner?}                   a file inside a .zip
    text_lines on .rtf/.eml/.odt/.vsdx/.msg       lines of the derived plain text
"""
from __future__ import annotations

import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import argparse
import codecs
import csv
import datetime as _dt
import difflib
import email
import email.policy
import functools
import hashlib
import io
import itertools
import json
import math
import os
import posixpath
import re
import subprocess
import unicodedata
import warnings
import zipfile
from dataclasses import dataclass, field
from typing import Any, Callable, Iterator

import yaml
from lxml import etree

Path = pathlib.Path

EXTRACTOR_VERSION = "1"
CACHE_DIR = Path(os.environ.get("HARNESS_CACHE_DIR") or ROOT / "build" / "cache")  # env override for tests
OCR_CACHE_DIR = CACHE_DIR / "ocr"
CONVERT_CACHE_DIR = CACHE_DIR / "converted"
ZIP_CACHE_DIR = CACHE_DIR / "zip"
OCR_DPI = 200
OCR_ENGINE = "ocrmac-vision-accurate-v1"
TEXT_WINDOW = 25            # lines per text/code unit in extract_all
JSON_UNIT_CHARS = 3000      # JSON/YAML/XML nodes up to this size become one unit
PDF_OCR_MIN_CHARS = 25      # a page with fewer text-layer characters counts as "no text layer"
PDF_OCR_IMAGE_COVER = 0.25  # ... or when images cover at least this share of the page

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tif", ".tiff", ".webp"}
DERIVED_TEXT_EXTS = {".rtf", ".eml", ".odt", ".ods", ".odp", ".vsdx", ".msg"}
XML_EXTS = {".xml", ".bpmn", ".svg", ".xsd", ".xsl", ".xslt", ".drawio"}
HTML_EXTS = {".html", ".htm", ".xhtml"}
YAML_EXTS = {".yaml", ".yml"}

LOCATOR_KINDS = (
    "pdf_page", "docx_para", "docx_table", "docx_comment", "docx_footnote", "docx_endnote",
    "docx_header", "docx_footer", "docx_tracked", "docx_image", "docx_alt_text", "pptx_slide",
    "xlsx_cell", "xlsx_chart", "csv_row", "json_pointer", "xml_xpath", "yaml_path", "html_xpath",
    "text_lines", "image_ocr", "code_lines", "git_commit", "zip_member",
)
PPTX_WHERES = ("text", "notes", "table", "chart", "alt_text", "group", "connector", "image")

warnings.filterwarnings("ignore", module="openpyxl")


# ---------------------------------------------------------------------------------------------
# Errors and results
# ---------------------------------------------------------------------------------------------

class LocatorError(Exception):
    """The locator is malformed, points outside the file, or the file is missing."""


class OcrUnavailable(LocatorError):
    """The locator needs OCR, OCR is disabled, and no cached result exists."""


@dataclass
class Resolved:
    """Text at a locator, plus metadata (hidden state, page hints, authors...).

    ``fallback`` is a wider search window (e.g. the whole DOCX section named in the locator)
    that the verifier may use to distinguish "fact moved slightly" from "fact missing".
    """
    text: str
    meta: dict = field(default_factory=dict)
    fallback: str | None = None


@dataclass
class _Ctx:
    repo_root: Path
    ocr: bool = True


# ---------------------------------------------------------------------------------------------
# Normalisation and matching
# ---------------------------------------------------------------------------------------------

_CHAR_MAP: dict[int, str | None] = {}
for _ch in "\u2018\u2019\u201a\u201b\u2032\u02bc\u0060\u00b4":
    _CHAR_MAP[ord(_ch)] = "'"
for _ch in "\u201c\u201d\u201e\u201f\u2033\u00ab\u00bb":
    _CHAR_MAP[ord(_ch)] = '"'
for _ch in "\u2010\u2011\u2012\u2013\u2014\u2015\u2212\ufe58\ufe63\uff0d":
    _CHAR_MAP[ord(_ch)] = "-"
_CHAR_MAP.update({
    0x2265: ">=", 0x2264: "<=", 0x2260: "!=", 0x2192: "->", 0x2190: "<-", 0x21d2: "=>",
    0x00ad: None, 0x200b: None, 0x200c: None, 0x200d: None, 0x2060: None, 0xfeff: None,
    0x000b: "\n",
})
_WS_RE = re.compile(r"\s+")
_DEHYPH_RE = re.compile(r"(\w)-[ \t]*\r?\n\s*(\w)")
_TIGHT_RE = re.compile(r"\s*([^\w\s])\s*")


def _normalize(text: str, dehyphen: bool = False) -> str:
    if not text:
        return ""
    t = unicodedata.normalize("NFKC", text).translate(_CHAR_MAP)
    if dehyphen:
        t = _DEHYPH_RE.sub(r"\1\2", t)
    return _WS_RE.sub(" ", t.casefold()).strip()


def normalize(text: str) -> str:
    """NFKC, typographic quotes/dashes/≥ folded, soft hyphens dropped, casefolded, ws collapsed."""
    return _normalize(text)


def _tight(s: str) -> str:
    """Drop whitespace around punctuation ("≥ 65" == "≥65", "( a )" == "(a)")."""
    return _TIGHT_RE.sub(r"\1", s)


def _opcode_errors(sm: difflib.SequenceMatcher) -> int:
    return sum(max(i2 - i1, j2 - j1) for tag, i1, i2, j1, j2 in sm.get_opcodes() if tag != "equal")


def allowed_ocr_errors(normalised_needle: str) -> int:
    """One OCR error per 12 characters (at least one)."""
    return max(1, math.ceil(len(normalised_needle) / 12))


def _fuzzy_best(n: str, h: str, max_errors: int | None = None,
                widths_delta: tuple[int, ...] = (-1, 0, 1)) -> tuple[int, str]:
    """Best token-window alignment of needle ``n`` in haystack ``h`` (both normalised).

    Returns (errors, candidate). Errors approximate a Levenshtein distance via difflib opcodes.
    """
    ntok, htok = n.split(), h.split()
    if not ntok or not htok:
        return (10 ** 9, "")
    best: tuple[int, str] = (10 ** 9, "")
    nlen = len(n)
    for w in sorted({max(1, min(len(htok), len(ntok) + d)) for d in widths_delta}):
        for i in range(0, len(htok) - w + 1):
            cand = " ".join(htok[i:i + w])
            if max_errors is not None and abs(len(cand) - nlen) > max_errors:
                continue
            sm = difflib.SequenceMatcher(None, n, cand, autojunk=False)
            if max_errors is not None:
                upper_matches = sm.quick_ratio() * (nlen + len(cand)) / 2
                if max(nlen, len(cand)) - upper_matches > max_errors:
                    continue
            errs = _opcode_errors(sm)
            if errs < best[0]:
                best = (errs, cand)
                if errs == 0:
                    return best
    return best


def match(needle: str, text: str | None, mode: str = "exact") -> bool:
    """True when ``needle`` occurs in ``text`` after normalisation.

    mode="exact": normalised substring; also tolerant of line-end hyphenation and of
    whitespace around punctuation. mode="ocr_fuzzy": additionally a token-window alignment
    allowing one OCR error per 12 characters.
    """
    n = normalize(needle)
    if not n or not text:
        return False
    h = normalize(text)
    if n in h:
        return True
    h2 = _normalize(text, dehyphen=True)
    if h2 != h and n in h2:
        return True
    nt = _tight(n)
    if nt in _tight(h) or (h2 != h and nt in _tight(h2)):
        return True
    if mode == "ocr_fuzzy":
        allowed = allowed_ocr_errors(n)
        for hay in ((h,) if h2 == h else (h, h2)):
            if _fuzzy_best(n, hay, max_errors=allowed)[0] <= allowed:
                return True
    return False


def best_snippet(needle: str, text: str | None, max_chars: int = 200_000) -> tuple[int, str]:
    """Closest window of ``text`` to ``needle`` (for FAIL details): (errors, snippet)."""
    n, h = normalize(needle), normalize(text or "")
    if not n or not h:
        return (len(n), "")
    if n in h:
        return (0, n)
    if len(h) > max_chars:
        h = h[:max_chars]
    return _fuzzy_best(n, h, widths_delta=(0,) if len(h) > 50_000 else (-1, 0, 1))


# ---------------------------------------------------------------------------------------------
# Small helpers: paths, hashing, caches, value rendering
# ---------------------------------------------------------------------------------------------

def _stat_key(path: Path) -> tuple[str, int, int]:
    st = path.stat()
    return (str(path), st.st_mtime_ns, st.st_size)


@functools.lru_cache(maxsize=256)
def _sha1_cached(key: tuple[str, int, int]) -> str:
    h = hashlib.sha1()
    with open(key[0], "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def file_sha1(path: os.PathLike | str) -> str:
    """SHA-1 of a file's bytes (memoised per path+mtime+size)."""
    return _sha1_cached(_stat_key(Path(path)))


def _abs_path(file_path: os.PathLike | str, repo_root: Path) -> Path:
    p = Path(file_path)
    return p if p.is_absolute() else Path(repo_root) / p


def rel_path(path: os.PathLike | str, repo_root: Path = ROOT) -> str:
    """Repo-relative POSIX path when possible, else the absolute path."""
    p = Path(path).resolve()
    try:
        return p.relative_to(Path(repo_root).resolve()).as_posix()
    except ValueError:
        return p.as_posix()


def fmt_scalar(v: Any, bool_style: str = "json") -> str:
    """Canonical text for a scalar: integral floats lose '.0', dates are ISO."""
    if v is None:
        return "null" if bool_style == "json" else ""
    if isinstance(v, bool):
        if bool_style == "excel":
            return "TRUE" if v else "FALSE"
        return "true" if v else "false"
    if isinstance(v, float):
        if math.isfinite(v) and v.is_integer() and abs(v) < 1e15:
            return str(int(v))
        return repr(v)
    if isinstance(v, _dt.datetime):
        if v.time() == _dt.time(0, 0) and v.tzinfo is None:
            return v.date().isoformat()
        return v.isoformat(sep=" ")
    if isinstance(v, (_dt.date, _dt.time)):
        return v.isoformat()
    return str(v)


def _fmt_num_str(s: str | None) -> str:
    """Canonicalise a numeric string from an XML cache ("65.0" -> "65")."""
    if s is None:
        return ""
    s = s.strip()
    try:
        f = float(s)
    except ValueError:
        return s
    return fmt_scalar(f)


def _one_line(s: str) -> str:
    return _WS_RE.sub(" ", s or "").strip()


def _render_tree(v: Any, sep: str, prefix: str = "") -> list[str]:
    """Flatten a JSON/YAML value into 'relative.path: value' lines (strings kept raw)."""
    if isinstance(v, dict):
        if not v:
            return [f"{prefix}: {{}}"] if prefix else []
        out: list[str] = []
        for k, x in v.items():
            out.extend(_render_tree(x, sep, f"{prefix}{sep}{fmt_scalar(k)}" if prefix else fmt_scalar(k)))
        return out
    if isinstance(v, list):
        if not v:
            return [f"{prefix}: []"] if prefix else []
        out = []
        for i, x in enumerate(v):
            out.extend(_render_tree(x, sep, f"{prefix}[{i}]" if prefix else f"[{i}]"))
        return out
    return [f"{prefix}: {fmt_scalar(v)}" if prefix else fmt_scalar(v)]


def render_value(v: Any, sep: str = "/") -> str:
    """Text for a JSON/YAML node: a scalar renders as itself, containers as path: value lines."""
    if isinstance(v, (dict, list)):
        return "\n".join(_render_tree(v, sep))
    return fmt_scalar(v)


def _detect_encoding(path: Path) -> str:
    with open(path, "rb") as fh:
        head = fh.read(4 << 20)
    if head.startswith(b"\xff\xfe") or head.startswith(b"\xfe\xff"):
        return "utf-16"
    try:
        dec = codecs.getincrementaldecoder("utf-8")()
        dec.decode(head, final=False)
        return "utf-8-sig"
    except UnicodeDecodeError:
        return "cp1252"


def read_text(path: Path) -> str:
    return path.read_bytes().decode(_detect_encoding(path), errors="replace")


def _looks_binary(path: Path) -> bool:
    with open(path, "rb") as fh:
        head = fh.read(8192)
    if head.startswith((b"\xff\xfe", b"\xfe\xff")):
        return False
    return b"\x00" in head


# ---------------------------------------------------------------------------------------------
# OCR (Apple Vision via ocrmac), cached in build/cache/ocr/<sha1>.json
# ---------------------------------------------------------------------------------------------

def _ocr_cache_path(key: str) -> Path:
    return OCR_CACHE_DIR / f"{hashlib.sha1(key.encode()).hexdigest()}.json"


def _ocr_cache_get(key: str) -> str | None:
    p = _ocr_cache_path(key)
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))["text"]
        except (ValueError, KeyError, OSError):
            return None
    return None


def _ocr_cache_put(key: str, text: str, lines: list) -> None:
    p = _ocr_cache_path(key)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(f".{os.getpid()}.tmp")
    tmp.write_text(json.dumps({"key": key, "engine": OCR_ENGINE, "text": text, "lines": lines},
                              ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, p)


def _prep_image(img):
    """Flatten transparency onto white, convert to RGB, upscale small images for OCR."""
    from PIL import Image
    if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
        img = img.convert("RGBA")
        bg = Image.new("RGB", img.size, "white")
        bg.paste(img, mask=img.split()[-1])
        img = bg
    elif img.mode != "RGB":
        img = img.convert("RGB")
    if max(img.size) < 700:
        img = img.resize((img.size[0] * 2, img.size[1] * 2), Image.LANCZOS)
    return img


def _ocr_pil(img) -> tuple[str, list]:
    from ocrmac import ocrmac
    res = ocrmac.OCR(_prep_image(img), recognition_level="accurate").recognize()
    lines = [[t, float(c), [float(x) for x in b]] for t, c, b in res]
    return "\n".join(t for t, _, _ in lines), lines


def ocr_image_bytes(data: bytes, allow_compute: bool = True) -> str:
    """OCR an image given as bytes; cached by the bytes' sha1."""
    key = f"img:{hashlib.sha1(data).hexdigest()}:{OCR_ENGINE}"
    cached = _ocr_cache_get(key)
    if cached is not None:
        return cached
    if not allow_compute:
        raise OcrUnavailable("OCR disabled and result not cached")
    from PIL import Image
    try:
        img = Image.open(io.BytesIO(data))
        img.load()
    except Exception as exc:  # unsupported (EMF/WMF...) or corrupt image
        raise LocatorError(f"cannot open image for OCR: {exc}") from exc
    text, lines = _ocr_pil(img)
    _ocr_cache_put(key, text, lines)
    return text


def ocr_image_file(path: Path, allow_compute: bool = True) -> str:
    return ocr_image_bytes(Path(path).read_bytes(), allow_compute=allow_compute)


def _pdf_page_key(path: Path, page: int, dpi: int) -> str:
    return f"pdfpage:{file_sha1(path)}:{page}:{dpi}:{OCR_ENGINE}"


def ocr_pdf_page(path: Path, page: int, dpi: int = OCR_DPI, allow_compute: bool = True) -> str:
    """Rasterise a PDF page at ``dpi`` and OCR it; cached by file hash + page + dpi."""
    key = _pdf_page_key(path, page, dpi)
    cached = _ocr_cache_get(key)
    if cached is not None:
        return cached
    if not allow_compute:
        raise OcrUnavailable("OCR disabled and result not cached")
    from PIL import Image
    doc = _pdf(path)
    pix = doc[page - 1].get_pixmap(dpi=dpi, alpha=False)
    mode = {1: "L", 3: "RGB", 4: "CMYK"}.get(pix.n, "RGB")
    img = Image.frombytes(mode, (pix.width, pix.height), pix.samples)
    text, lines = _ocr_pil(img)
    _ocr_cache_put(key, text, lines)
    return text


# ---------------------------------------------------------------------------------------------
# OOXML helpers
# ---------------------------------------------------------------------------------------------

NS = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "wp": "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "c": "http://schemas.openxmlformats.org/drawingml/2006/chart",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "mc": "http://schemas.openxmlformats.org/markup-compatibility/2006",
    "x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "dgm": "http://schemas.openxmlformats.org/drawingml/2006/diagram",
    "pr": "http://schemas.openxmlformats.org/package/2006/relationships",
}


def _xp(el, path: str) -> list:
    """XPath with the OOXML prefixes (bypasses python-docx/pptx's restricted xpath override)."""
    return etree._Element.xpath(el, path, namespaces=NS)


def _q(prefix: str, local: str) -> str:
    return f"{{{NS[prefix]}}}{local}"


W_P, W_T, W_DELTEXT, W_TAB, W_BR, W_CR = (_q("w", x) for x in ("p", "t", "delText", "tab", "br", "cr"))
W_NBH, W_SOFTH, W_DEL, W_INS, W_R = (_q("w", x) for x in ("noBreakHyphen", "softHyphen", "del", "ins", "r"))
W_PPR, W_RPR, W_TRPR, W_TBL, W_TR, W_TC = (_q("w", x) for x in ("pPr", "rPr", "trPr", "tbl", "tr", "tc"))
W_ID = _q("w", "id")
MC_FALLBACK = _q("mc", "Fallback")
_WML_SKIP = {W_PPR, W_RPR, W_TRPR, _q("w", "tcPr"), _q("w", "tblPr"), _q("w", "tblGrid"),
             _q("w", "sectPr"), MC_FALLBACK, _q("w", "instrText")}
_XML_PARSER = etree.XMLParser(resolve_entities=False, no_network=True, huge_tree=True)


def _parse_xml(data: bytes):
    return etree.fromstring(data, parser=_XML_PARSER)


def _wml_text(el, deleted: bool = False) -> str:
    """Visible text of a WordprocessingML subtree.

    w:t (and w:delText when ``deleted``), tabs, breaks, hyphens; text boxes included,
    mc:Fallback duplicates and property subtrees skipped; paragraphs separated by newlines.
    Deleted runs (w:del) are skipped unless ``deleted`` is true.
    """
    out: list[str] = []

    def walk(e, parent_tag=None):
        tag = e.tag
        if not isinstance(tag, str) or tag in _WML_SKIP:
            return
        if tag == W_T:
            out.append(e.text or "")
            return
        if tag == W_DELTEXT:
            if deleted:
                out.append(e.text or "")
            return
        if tag == W_DEL and not deleted:
            return
        if parent_tag == W_R:
            if tag == W_TAB:
                out.append("\t")
            elif tag in (W_BR, W_CR):
                out.append("\n")
            elif tag == W_NBH:
                out.append("-")
            elif tag == W_SOFTH:
                out.append("\u00ad")
        for child in e:
            walk(child, tag)
        if tag == W_P:
            out.append("\n")

    walk(el)
    return "".join(out).strip("\n")


def _wml_table_text(tbl) -> str:
    """Rows of a w:tbl as tab-separated lines (cells may contain nested tables)."""
    rows = []
    for tr in tbl.iterchildren(W_TR):
        cells = []
        for tc in tr.iterchildren(W_TC):
            cells.append(_one_line(_wml_block_text(tc)))
        if any(cells):
            rows.append("\t".join(cells))
    return "\n".join(rows)


def _wml_block_text(container) -> str:
    """Text of a block container (cell, comment, footnote, header): paragraphs and tables."""
    parts = []
    for child in container:
        if child.tag == W_P:
            parts.append(_wml_text(child))
        elif child.tag == W_TBL:
            parts.append(_wml_table_text(child))
        elif child.tag == _q("w", "sdt"):
            content = child.find(_q("w", "sdtContent"))
            if content is not None:
                parts.append(_wml_block_text(content))
    return "\n".join(p for p in parts if p and p.strip())


def _in_fallback(el) -> bool:
    return any(a.tag == MC_FALLBACK for a in el.iterancestors())


def _rels_map(z: zipfile.ZipFile, part: str) -> dict[str, tuple[str, str, str]]:
    """{rId: (type, absolute target part name, target mode)} for a package part."""
    d, b = posixpath.split(part)
    rels_name = posixpath.join(d, "_rels", b + ".rels")
    try:
        root = _parse_xml(z.read(rels_name))
    except KeyError:
        return {}
    out = {}
    for rel in root:
        target = rel.get("Target", "")
        mode = rel.get("TargetMode", "Internal")
        if mode != "External":
            target = target.lstrip("/") if target.startswith("/") else posixpath.normpath(posixpath.join(d, target))
        out[rel.get("Id")] = (rel.get("Type", ""), target, mode)
    return out


@functools.lru_cache(maxsize=16)
def _zip_cached(key: tuple[str, int, int]) -> zipfile.ZipFile:
    return zipfile.ZipFile(key[0])


def _zip(path: Path) -> zipfile.ZipFile:
    return _zip_cached(_stat_key(path))


# ---------------------------------------------------------------------------------------------
# DOCX
# ---------------------------------------------------------------------------------------------

@dataclass
class _Heading:
    index: int
    level: int
    text: str


class _DocxInfo:
    """Loaded DOCX with memoised paragraph texts, heading map and part access."""

    def __init__(self, path: Path):
        import docx
        self.path = path
        self.doc = docx.Document(str(path))
        self.body = self.doc.element.body
        self.paragraphs = self.doc.paragraphs
        self._texts: dict[int, str] = {}
        self._headings: list[_Heading] | None = None
        self._styles: dict[str, tuple[str, int | None, str | None]] | None = None
        self._parts: dict[str, Any] = {}

    # -- paragraphs ---------------------------------------------------------------------------
    def para_text(self, i: int) -> str:
        t = self._texts.get(i)
        if t is None:
            t = self._texts[i] = _wml_text(self.paragraphs[i]._p)
        return t

    def _style_map(self):
        if self._styles is None:
            self._styles = {}
            styles_el = self.doc.styles.element
            for s in styles_el.iterchildren(_q("w", "style")):
                sid = s.get(_q("w", "styleId"))
                name_el = s.find(_q("w", "name"))
                name = name_el.get(_q("w", "val")) if name_el is not None else (sid or "")
                ol = s.find(f"{_q('w', 'pPr')}/{_q('w', 'outlineLvl')}")
                lvl = int(ol.get(_q("w", "val"))) if ol is not None else None
                based = s.find(_q("w", "basedOn"))
                self._styles[sid] = (name, lvl, based.get(_q("w", "val")) if based is not None else None)
        return self._styles

    def _style_id(self, p) -> str | None:
        ps = p.find(f"{W_PPR}/{_q('w', 'pStyle')}")
        return ps.get(_q("w", "val")) if ps is not None else None

    def style_name(self, i: int) -> str:
        sid = self._style_id(self.paragraphs[i]._p)
        return self._style_map().get(sid, (sid or "Normal", None, None))[0]

    def heading_level(self, p) -> int | None:
        ol = p.find(f"{W_PPR}/{_q('w', 'outlineLvl')}")
        if ol is not None:
            v = int(ol.get(_q("w", "val")))
            return v + 1 if v < 9 else None
        sid, smap, seen = self._style_id(p), self._style_map(), set()
        while sid and sid in smap and sid not in seen:
            seen.add(sid)
            name, lvl, based = smap[sid]
            m = re.match(r"heading\s*(\d)", name or "", re.I)
            if m:
                return int(m.group(1))
            if (name or "").lower() == "title":
                return 0
            if lvl is not None and lvl < 9:
                return lvl + 1
            sid = based
        return None

    def headings(self) -> list[_Heading]:
        if self._headings is None:
            self._headings = []
            for i, p in enumerate(self.paragraphs):
                lvl = self.heading_level(p._p)
                if lvl is not None:
                    t = self.para_text(i).strip()
                    if t:
                        self._headings.append(_Heading(i, lvl, t))
        return self._headings

    def section_window(self, section: str, near: int | None = None) -> tuple[int, int, str]:
        """Text from the heading matching ``section`` to the next heading at the same/higher level.

        Tables between the two headings are included (body order)."""
        target = normalize(section)
        hs = self.headings()
        cands = ([h for h in hs if normalize(h.text) == target]
                 or [h for h in hs if normalize(h.text).startswith(target)]
                 or [h for h in hs if target in normalize(h.text)])
        if not cands:
            raise LocatorError(f"no heading matching section {section!r}")
        if near is not None:
            before = [h for h in cands if h.index <= near]
            h = before[-1] if before else cands[0]
        else:
            h = cands[0]
        end = len(self.paragraphs)
        for h2 in hs:
            if h2.index > h.index and h2.level <= h.level:
                end = h2.index
                break
        start_el = self.paragraphs[h.index]._p
        end_el = self.paragraphs[end]._p if end < len(self.paragraphs) else None
        parts, inside = [], False
        for child in self.body:
            if child is start_el:
                inside = True
            if end_el is not None and child is end_el:
                break
            if inside:
                if child.tag == W_P:
                    parts.append(_wml_text(child))
                elif child.tag == W_TBL:
                    parts.append(_wml_table_text(child))
        return h.index, end, "\n".join(parts)

    def heading_before(self, i: int) -> str | None:
        prev = None
        for h in self.headings():
            if h.index > i:
                break
            prev = h.text
        return prev

    # -- parts -------------------------------------------------------------------------------
    def part_xml(self, part):
        el = getattr(part, "element", None)
        if el is not None:
            return el
        key = str(part.partname)
        if key not in self._parts:
            self._parts[key] = _parse_xml(part.blob)
        return self._parts[key]

    def parts_by_reltype(self, suffix: str) -> list:
        return [rel.target_part for rel in self.doc.part.rels.values()
                if not rel.is_external and rel.reltype.endswith("/" + suffix)]

    def related_part(self, rid: str):
        return self.doc.part.related_parts[rid]

    def section_props(self) -> list:
        return _xp(self.body, "./w:p/w:pPr/w:sectPr | ./w:sectPr")

    def tracked(self, typ: str) -> list:
        tag = W_INS if typ == "ins" else W_DEL
        return [e for e in self.body.iter(tag)
                if e.getparent().tag not in (W_RPR, W_TRPR) and not _in_fallback(e)]

    def doc_prs(self) -> list:
        return [e for e in self.body.iter(_q("wp", "docPr")) if not _in_fallback(e)]


@functools.lru_cache(maxsize=4)
def _docx_info_cached(key: tuple[str, int, int]) -> _DocxInfo:
    return _DocxInfo(Path(key[0]))


def _as_docx(path: Path) -> Path:
    """Legacy .doc files are converted once with LibreOffice (cached by sha1)."""
    if path.suffix.lower() != ".doc":
        return path
    out = CONVERT_CACHE_DIR / f"{file_sha1(path)}.docx"
    if not out.exists():
        from generators.common.util import soffice_convert
        tmpdir = CONVERT_CACHE_DIR / f"tmp_{os.getpid()}"
        produced = soffice_convert(path, "docx", tmpdir, profile_key=f"extract_{os.getpid()}")
        out.parent.mkdir(parents=True, exist_ok=True)
        os.replace(produced, out)
    return out


def _docx_info(path: Path) -> _DocxInfo:
    return _docx_info_cached(_stat_key(_as_docx(path)))


def _int(loc: dict, key: str, *alts: str) -> int:
    for k in (key, *alts):
        if k in loc and loc[k] is not None:
            try:
                return int(loc[k])
            except (TypeError, ValueError):
                raise LocatorError(f"locator field {k!r} must be an integer, got {loc[k]!r}")
    raise LocatorError(f"locator missing field {key!r}")


def _r_docx_para(path: Path, loc: dict, ctx: _Ctx) -> Resolved:
    info = _docx_info(path)
    n = len(info.paragraphs)
    section = loc.get("section")
    meta: dict[str, Any] = {"paragraph_count": n, "page_hint": loc.get("page_hint")}
    if loc.get("para_index") is None:
        if not section:
            raise LocatorError("docx_para needs para_index or section")
        start, end, text = info.section_window(section)
        meta.update(section_start=start, section_end=end)
        return Resolved(text, meta)
    i = _int(loc, "para_index")
    j = int(loc.get("end_para_index", i))
    if not (0 <= i <= j < n):
        raise LocatorError(f"para_index {i}..{j} out of range (0..{n - 1})")
    text = "\n".join(info.para_text(k) for k in range(i, j + 1))
    meta.update(style=info.style_name(i), heading=info.heading_before(i))
    fallback = None
    if section:
        try:
            fallback = info.section_window(section, near=i)[2]
        except LocatorError as exc:
            meta["section_error"] = str(exc)
    return Resolved(text, meta, fallback)


def _cell_text(cell) -> str:
    return _wml_block_text(cell._tc)


def _nested_steps(nested) -> list[tuple[int, int, int]]:
    if not nested:
        return []
    if all(isinstance(x, int) for x in nested):
        if len(nested) % 3:
            raise LocatorError("nested must be [i, r, c] or a list of such triples")
        return [tuple(nested[k:k + 3]) for k in range(0, len(nested), 3)]
    return [tuple(int(v) for v in step) for step in nested]


def _r_docx_table(path: Path, loc: dict, ctx: _Ctx) -> Resolved:
    info = _docx_info(path)
    tables = info.doc.tables
    ti = _int(loc, "table_index")
    if not 0 <= ti < len(tables):
        raise LocatorError(f"table_index {ti} out of range ({len(tables)} tables)")
    table = tables[ti]
    meta = {"table_count": len(tables), "rows": len(table.rows), "cols": len(table.columns)}
    if loc.get("row") is None and loc.get("col") is None and not loc.get("nested"):
        return Resolved(_wml_table_text(table._tbl), meta)
    try:
        cell = table.cell(_int(loc, "row"), _int(loc, "col"))
        for i, r, c in _nested_steps(loc.get("nested")):
            inner = cell.tables
            if not 0 <= i < len(inner):
                raise LocatorError(f"nested table {i} not found in cell")
            cell = inner[i].cell(r, c)
    except IndexError as exc:
        raise LocatorError(f"cell out of range: {exc}") from exc
    return Resolved(_cell_text(cell), meta)


def _notes_part_text(info: _DocxInfo, reltype: str, tag: str, note_id: int) -> Resolved:
    for part in info.parts_by_reltype(reltype):
        root = info.part_xml(part)
        for el in root.iterchildren(_q("w", tag)):
            if el.get(W_ID) == str(note_id):
                meta = {k: el.get(_q("w", k)) for k in ("author", "date", "initials", "type") if el.get(_q("w", k))}
                return Resolved(_wml_block_text(el), meta)
    raise LocatorError(f"{tag} id {note_id} not found")


def _r_docx_comment(path, loc, ctx):
    return _notes_part_text(_docx_info(path), "comments", "comment", _int(loc, "comment_id", "id"))


def _r_docx_footnote(path, loc, ctx):
    return _notes_part_text(_docx_info(path), "footnotes", "footnote", _int(loc, "footnote_id", "id"))


def _r_docx_endnote(path, loc, ctx):
    return _notes_part_text(_docx_info(path), "endnotes", "endnote", _int(loc, "endnote_id", "footnote_id", "id"))


def _hf_texts(info: _DocxInfo, which: str, section_index: int, only_type: str | None = None) -> list[tuple[str, str]]:
    """[(type, text)] of all header/footer parts that apply to a section (inheritance honoured)."""
    sects = info.section_props()
    if not 0 <= section_index < len(sects):
        raise LocatorError(f"section_index {section_index} out of range ({len(sects)} sections)")
    ref_tag = _q("w", f"{which}Reference")
    out, seen = [], set()
    for typ in ("default", "first", "even"):
        if only_type and typ != only_type:
            continue
        for k in range(section_index, -1, -1):
            ref = [r for r in sects[k].iterchildren(ref_tag) if r.get(_q("w", "type"), "default") == typ]
            if ref:
                rid = ref[0].get(_q("r", "id"))
                if rid not in seen:
                    seen.add(rid)
                    root = info.part_xml(info.related_part(rid))
                    out.append((typ, _wml_block_text(root)))
                break
    return out


def _r_docx_hf(which: str):
    def _resolver(path, loc, ctx):
        info = _docx_info(path)
        parts = _hf_texts(info, which, _int(loc, "section_index"), loc.get("type"))
        return Resolved("\n".join(t for _, t in parts if t), {"types": [t for t, _ in parts]})
    return _resolver


def _r_docx_tracked(path, loc, ctx):
    info = _docx_info(path)
    typ = loc.get("type", "ins")
    if typ not in ("ins", "del"):
        raise LocatorError("docx_tracked type must be 'ins' or 'del'")
    els = info.tracked(typ)
    if loc.get("id") is not None:
        found = [e for e in els if e.get(W_ID) == str(loc["id"])]
        if not found:
            raise LocatorError(f"no w:{typ} with w:id {loc['id']}")
        el = found[0]
    else:
        idx = _int(loc, "index")
        if not 0 <= idx < len(els):
            raise LocatorError(f"w:{typ} index {idx} out of range ({len(els)} found)")
        el = els[idx]
    meta = {"author": el.get(_q("w", "author")), "date": el.get(_q("w", "date")), "count": len(els)}
    return Resolved(_wml_text(el, deleted=True), meta)


def _docx_media_name(name: str) -> str:
    name = name.lstrip("/")
    if name.startswith("word/"):
        return name
    if name.startswith("media/"):
        return "word/" + name
    return "word/media/" + name


def _r_docx_image(path, loc, ctx):
    path = _as_docx(path)
    name = loc.get("image_name")
    if not name:
        raise LocatorError("docx_image needs image_name")
    member = _docx_media_name(str(name))
    try:
        data = _zip(path).read(member)
    except KeyError:
        raise LocatorError(f"{member} not found in package")
    return Resolved(ocr_image_bytes(data, allow_compute=ctx.ocr), {"member": member})


def _r_docx_alt_text(path, loc, ctx):
    info = _docx_info(path)
    prs = info.doc_prs()
    idx = _int(loc, "image_index", "index")
    if not 0 <= idx < len(prs):
        raise LocatorError(f"image_index {idx} out of range ({len(prs)} drawings)")
    el = prs[idx]
    text = "\n".join(x for x in (el.get("descr"), el.get("title")) if x)
    return Resolved(text, {"name": el.get("name"), "count": len(prs)})


# ---------------------------------------------------------------------------------------------
# PPTX
# ---------------------------------------------------------------------------------------------

@functools.lru_cache(maxsize=4)
def _pptx_cached(key: tuple[str, int, int]):
    from pptx import Presentation
    return Presentation(key[0])


def _pptx(path: Path):
    return _pptx_cached(_stat_key(path))


_LINE_PRESETS = {"line", "straightConnector1", "bentConnector2", "bentConnector3", "bentConnector4",
                 "bentConnector5", "curvedConnector2", "curvedConnector3", "curvedConnector4",
                 "curvedConnector5"}


@dataclass
class _ShapeRec:
    shape: Any
    tag: str
    name: str
    sid: int
    bbox: tuple[float, float, float, float] | None
    depth: int
    T: tuple[float, float, float, float]
    is_connector: bool = False
    text: str = ""


def _local(el) -> str:
    return etree.QName(el).localname


def _pptx_shape_text(sh) -> str:
    if getattr(sh, "has_text_frame", False) and sh.has_text_frame:
        return sh.text_frame.text.replace("\v", "\n")
    return ""


def _smartart_text(sh) -> str:
    el = sh._element
    rel = el.find(".//" + _q("dgm", "relIds"))
    if rel is None:
        return ""
    try:
        part = sh.part.related_part(rel.get(_q("r", "dm")))
        root = _parse_xml(part.blob)
    except Exception:
        return ""
    return "\n".join(t.text for t in root.iter(_q("a", "t")) if t.text)


def _xfrm_of(el):
    for path in ("p:spPr/a:xfrm", "p:grpSpPr/a:xfrm", "p:xfrm"):
        found = _xp(el, path)
        if found:
            return found[0]
    return None


def _flatten_shapes(slide) -> list[_ShapeRec]:
    """All shapes on a slide (groups recursed) with bounding boxes in slide coordinates."""
    recs: list[_ShapeRec] = []

    def walk(shapes, T, depth):
        for sh in shapes:
            el = sh._element
            tag = _local(el)
            bbox = None
            try:
                if sh.left is not None and sh.width is not None:
                    x0, y0 = T[0] + T[1] * sh.left, T[2] + T[3] * sh.top
                    bbox = (x0, y0, x0 + T[1] * sh.width, y0 + T[3] * sh.height)
            except Exception:
                bbox = None
            is_cxn = tag == "cxnSp"
            if tag == "sp":
                geom = _xp(el, "p:spPr/a:prstGeom/@prst")
                is_cxn = bool(geom) and geom[0] in _LINE_PRESETS and not _pptx_shape_text(sh).strip()
            rec = _ShapeRec(sh, tag, sh.name, sh.shape_id, bbox, depth, T, is_cxn, _pptx_shape_text(sh))
            recs.append(rec)
            if tag == "grpSp":
                xf = el.find(f"{_q('p', 'grpSpPr')}/{_q('a', 'xfrm')}")
                T2 = T
                if xf is not None:
                    def _pt(name, a, b):
                        e = xf.find(_q("a", name))
                        return (float(e.get(a, 0)), float(e.get(b, 0))) if e is not None else None
                    off, ext = _pt("off", "x", "y"), _pt("ext", "cx", "cy")
                    choff, chext = _pt("chOff", "x", "y"), _pt("chExt", "cx", "cy")
                    if off and ext and choff and chext:
                        sx = ext[0] / chext[0] if chext[0] else 1.0
                        sy = ext[1] / chext[1] if chext[1] else 1.0
                        T2 = (T[0] + T[1] * (off[0] - choff[0] * sx), T[1] * sx,
                              T[2] + T[3] * (off[1] - choff[1] * sy), T[3] * sy)
                walk(sh.shapes, T2, depth + 1)

    walk(slide.shapes, (0.0, 1.0, 0.0, 1.0), 0)
    return recs


def _subtree(recs: list[_ShapeRec], name: str | None) -> list[_ShapeRec]:
    """Records for the named shape and its descendants (all records when name is None)."""
    if not name:
        return recs
    out, keep_depth = [], None
    for r in recs:
        if keep_depth is not None:
            if r.depth > keep_depth:
                out.append(r)
                continue
            keep_depth = None
        if r.name == name:
            out.append(r)
            if r.tag == "grpSp":
                keep_depth = r.depth
    if not out:
        raise LocatorError(f"no shape named {name!r} on slide")
    return out


def _connector_endpoints(rec: _ShapeRec) -> tuple[tuple[float, float], tuple[float, float]]:
    sh, T = rec.shape, rec.T
    if rec.tag == "cxnSp":
        bx, by, ex, ey = sh.begin_x, sh.begin_y, sh.end_x, sh.end_y
    else:
        x, y, w, h = sh.left, sh.top, sh.width, sh.height
        xf = _xfrm_of(sh._element)
        fh = xf is not None and xf.get("flipH") in ("1", "true")
        fv = xf is not None and xf.get("flipV") in ("1", "true")
        bx, ex = (x + w, x) if fh else (x, x + w)
        by, ey = (y + h, y) if fv else (y, y + h)
    return (T[0] + T[1] * bx, T[2] + T[3] * by), (T[0] + T[1] * ex, T[2] + T[3] * ey)


def _bbox_dist(pt, bbox) -> float:
    x, y = pt
    dx = max(bbox[0] - x, 0, x - bbox[2])
    dy = max(bbox[1] - y, 0, y - bbox[3])
    return math.hypot(dx, dy)


def _contains(bbox, pt, tol=0.0) -> bool:
    return bbox[0] - tol <= pt[0] <= bbox[2] + tol and bbox[1] - tol <= pt[1] <= bbox[3] + tol


def _area(bbox) -> float:
    return max(0.0, bbox[2] - bbox[0]) * max(0.0, bbox[3] - bbox[1])


def _connector_lines(slide, slide_w: float, shape_name: str | None) -> list[str]:
    """'<begin text> -> <end text> [label: <text>]' for every connector on the slide."""
    recs = _flatten_shapes(slide)
    by_id = {r.sid: r for r in recs if not r.is_connector}
    cxns = [r for r in recs if r.is_connector]
    if shape_name:
        cxns = [r for r in cxns if r.name == shape_name]
        if not cxns:
            raise LocatorError(f"no connector named {shape_name!r} on slide")
    all_cxns = [r for r in recs if r.is_connector]
    mids = {}
    for r in all_cxns:
        b, e = _connector_endpoints(r)
        mids[id(r)] = ((b[0] + e[0]) / 2, (b[1] + e[1]) / 2)
    named_labels = {r.name[len("label:"):].strip().lower(): r for r in recs
                    if r.name.lower().startswith("label:")}
    leafs = [r for r in recs if not r.is_connector and r.tag != "grpSp" and r.bbox is not None]

    def endpoint_rec(r: _ShapeRec, which: str, pt) -> _ShapeRec | None:
        if r.tag == "cxnSp":
            ids = _xp(r.shape._element, f"p:nvCxnSpPr/p:cNvCxnSpPr/a:{which}/@id")
            if ids and int(ids[0]) in by_id:
                return by_id[int(ids[0])]
        tol = 0.01 * slide_w
        inside = [x for x in leafs if _contains(x.bbox, pt, tol) and not x.name.lower().startswith("label:")]
        # prefer the smallest shape that has text (a box, not a lane/container)
        inside.sort(key=lambda x: (not x.text.strip(), _area(x.bbox)))
        if inside:
            return inside[0]
        near = sorted(leafs, key=lambda x: _bbox_dist(pt, x.bbox))
        if near and _bbox_dist(pt, near[0].bbox) <= 0.05 * slide_w:
            return near[0]
        return None

    def label_text(r, mid, b, e, brec, erec) -> str:
        named = named_labels.get(r.name.strip().lower())
        if named is not None:
            return _one_line(named.text)
        half = 0.10 * slide_w
        window = (mid[0] - half, mid[1] - half, mid[0] + half, mid[1] + half)
        cands = []
        for x in leafs:
            if x is brec or x is erec or not x.text.strip() or x.name.lower().startswith("label:"):
                continue
            bb = x.bbox
            if bb[2] < window[0] or bb[0] > window[2] or bb[3] < window[1] or bb[1] > window[3]:
                continue
            if _contains(bb, b) and _contains(bb, e):  # a container (lane/pool), not a label
                continue
            if brec is not None and brec.bbox and _contains(bb, brec.bbox[:2]) and _contains(bb, brec.bbox[2:]):
                continue
            d = _bbox_dist(mid, bb)
            # the label must be closest to *this* connector, not a neighbouring one
            if any(_bbox_dist(mids[id(o)], bb) < d - 1 for o in all_cxns if o is not r):
                continue
            cands.append((d, _area(bb), x))
        if not cands:
            return ""
        cands.sort(key=lambda t: (t[0], t[1]))
        return _one_line(cands[0][2].text)

    lines = []
    for r in cxns:
        b, e = _connector_endpoints(r)
        brec, erec = endpoint_rec(r, "stCxn", b), endpoint_rec(r, "endCxn", e)
        ln = r.shape._element.find(f"{_q('p', 'spPr')}/{_q('a', 'ln')}")
        if ln is not None:
            head = ln.find(_q("a", "headEnd"))
            tail = ln.find(_q("a", "tailEnd"))
            head_arrow = head is not None and head.get("type", "none") != "none"
            tail_arrow = tail is not None and tail.get("type", "none") != "none"
            if head_arrow and not tail_arrow:  # arrowhead drawn at the begin point: flow is reversed
                brec, erec, b, e = erec, brec, e, b
        btxt = _one_line(brec.text) or brec.name if brec else "?"
        etxt = _one_line(erec.text) or erec.name if erec else "?"
        lab = label_text(r, mids[id(r)], b, e, brec, erec)
        lines.append(f"{btxt} -> {etxt}" + (f" [label: {lab}]" if lab else ""))
    return lines


def _pptx_where(prs, slide, where: str, shape_name: str | None, ctx: _Ctx) -> tuple[str, dict]:
    meta: dict[str, Any] = {}
    if where == "notes":
        if not slide.has_notes_slide:
            return "", meta
        ns = slide.notes_slide
        tf = ns.notes_text_frame
        if tf is not None:
            return tf.text.replace("\v", "\n"), meta
        return "\n".join(_pptx_shape_text(s) for s in ns.shapes if _pptx_shape_text(s)), meta
    if where == "connector":
        return "\n".join(_connector_lines(slide, float(prs.slide_width or 9144000), shape_name)), meta
    recs = _subtree(_flatten_shapes(slide), shape_name)
    out: list[str] = []
    if where == "text":
        for r in recs:
            if r.text.strip():
                out.append(r.text)
            elif r.tag == "graphicFrame":
                sa = _smartart_text(r.shape)
                if sa:
                    out.append(sa)
    elif where == "table":
        for r in recs:
            if r.tag == "graphicFrame" and getattr(r.shape, "has_table", False) and r.shape.has_table:
                rows = ["\t".join(_one_line(c.text) for c in row.cells) for row in r.shape.table.rows]
                out.append("\n".join(rows))
    elif where == "chart":
        for r in recs:
            if r.tag == "graphicFrame" and getattr(r.shape, "has_chart", False) and r.shape.has_chart:
                chart = r.shape.chart

                def _wb(chart=chart):
                    import openpyxl
                    xp = chart.part.chart_workbook.xlsx_part
                    if xp is None:
                        return None
                    return openpyxl.load_workbook(io.BytesIO(xp.blob), data_only=True)
                out.append("\n".join(chart_lines(chart._chartSpace, _wb)))
    elif where == "alt_text":
        for r in recs:
            c = _xp(r.shape._element, "./*[1]/p:cNvPr")
            if c:
                for attr in ("descr", "title"):
                    if c[0].get(attr):
                        out.append(c[0].get(attr))
    elif where == "group":
        # the named group, or every top-level group (nested groups render inside their parent)
        top = min((r.depth for r in recs if r.tag == "grpSp"), default=0)
        for r in recs:
            if r.tag == "grpSp" and r.depth == top:
                lines = _group_lines(r)
                if lines:
                    out.append("\n".join(lines))
    elif where == "image":
        from pptx.shapes.picture import Picture
        n_img = 0
        for r in recs:
            if isinstance(r.shape, Picture):
                try:
                    blob = r.shape.image.blob
                except Exception:
                    continue
                n_img += 1
                try:
                    out.append(ocr_image_bytes(blob, allow_compute=ctx.ocr))
                except OcrUnavailable:
                    raise
                except LocatorError as exc:
                    meta.setdefault("ocr_errors", []).append(str(exc))
        meta["images"] = n_img
    else:
        raise LocatorError(f"unknown pptx where {where!r}")
    return "\n".join(x for x in out if x), meta


def _group_lines(rec: _ShapeRec, indent: int = 0) -> list[str]:
    lines = []
    for sh in rec.shape.shapes:
        tag = _local(sh._element)
        if tag == "grpSp":
            sub = _ShapeRec(sh, tag, sh.name, sh.shape_id, None, rec.depth + 1, rec.T)
            lines.extend(_group_lines(sub, indent + 1))
        else:
            t = _pptx_shape_text(sh)
            if t.strip():
                lines.append("  " * indent + _one_line(t))
    return lines


def _r_pptx_slide(path, loc, ctx):
    prs = _pptx(path)
    n = _int(loc, "slide")
    if not 1 <= n <= len(prs.slides):
        raise LocatorError(f"slide {n} out of range (1..{len(prs.slides)})")
    where = loc.get("where", "text")
    if where not in PPTX_WHERES:
        raise LocatorError(f"where must be one of {PPTX_WHERES}")
    text, meta = _pptx_where(prs, prs.slides[n - 1], where, loc.get("shape_name"), ctx)
    meta["slide_count"] = len(prs.slides)
    return Resolved(text, meta)


# ---------------------------------------------------------------------------------------------
# Charts (shared by PPTX and XLSX)
# ---------------------------------------------------------------------------------------------

def _c(local: str) -> str:
    return _q("c", local)


def _chart_points(container) -> tuple[dict[int, str], str | None]:
    """({idx: value}, formula) from c:cat / c:val / c:tx-like containers."""
    if container is None:
        return {}, None
    for ref_tag, cache_tag in (("numRef", "numCache"), ("strRef", "strCache"),
                               ("multiLvlStrRef", "multiLvlStrCache")):
        ref = container.find(_c(ref_tag))
        if ref is not None:
            f = ref.findtext(_c("f"))
            cache = ref.find(_c(cache_tag))
            if cache is None:
                return {}, f
            if ref_tag == "multiLvlStrRef":
                levels = [{int(pt.get("idx")): pt.findtext(_c("v")) or "" for pt in lvl.iter(_c("pt"))}
                          for lvl in cache.iter(_c("lvl"))]
                idxs = sorted(set().union(*levels)) if levels else []
                pts = {}
                for i in idxs:
                    parts = []
                    for lvl in reversed(levels):  # outermost level first
                        # outer levels only label the first index of their span
                        keys = sorted(k for k in lvl if k <= i)
                        parts.append(lvl[keys[-1]] if keys else "")
                    pts[i] = " / ".join(p for p in parts if p)
                return pts, f
            return {int(pt.get("idx")): _fmt_num_str(pt.findtext(_c("v"))) for pt in cache.iter(_c("pt"))}, f
    for lit in ("numLit", "strLit"):
        el = container.find(_c(lit))
        if el is not None:
            return {int(pt.get("idx")): _fmt_num_str(pt.findtext(_c("v"))) for pt in el.iter(_c("pt"))}, None
    v = container.findtext(_c("v"))
    if v is not None:
        return {0: v}, None
    return {}, None


def _rich_text(el) -> str:
    if el is None:
        return ""
    texts = [t.text or "" for t in el.iter(_q("a", "t"))]
    if texts:
        return "".join(texts)
    pts, _ = _chart_points(el.find(_c("tx")) if el.find(_c("tx")) is not None else el)
    return " ".join(pts.values())


def _ref_values(wb, ref: str | None) -> dict[int, str]:
    """Values of an A1 range reference ("'Sheet 1'!$B$2:$B$5") from an openpyxl workbook."""
    if wb is None or not ref:
        return {}
    ref = ref.strip().strip("()")
    vals: list[str] = []
    for area in re.split(r",(?=(?:[^']*'[^']*')*[^']*$)", ref):
        if "!" not in area:
            continue
        sheet, rng = area.rsplit("!", 1)
        sheet = sheet.strip().strip("'").replace("''", "'")
        if sheet not in wb.sheetnames:
            continue
        ws = wb[sheet]
        rng = rng.replace("$", "")
        cells = ws[rng]
        if not isinstance(cells, tuple):
            cells = ((cells,),)
        elif cells and not isinstance(cells[0], tuple):
            cells = (cells,)
        for row in cells:
            for cell in row:
                vals.append(fmt_scalar(cell.value, bool_style="excel"))
    return dict(enumerate(vals))


def chart_lines(chart_space, wb_loader: Callable[[], Any] | None = None) -> list[str]:
    """Render chart XML caches as 'title: ...', 'series: cat=value' and 'axis: ...' lines.

    When a series has no cached values, the referenced cells are read from the workbook
    returned by ``wb_loader`` (the embedded workbook for PPTX, the file itself for XLSX).
    """
    chart = chart_space.find(_c("chart"))
    if chart is None:
        return []
    lines: list[str] = []
    title = _rich_text(chart.find(_c("title")))
    if title:
        lines.append(f"title: {title}")
    plot = chart.find(_c("plotArea"))
    if plot is None:
        return lines
    wb_box: dict[str, Any] = {}

    def wb():
        if "wb" not in wb_box:
            try:
                wb_box["wb"] = wb_loader() if wb_loader else None
            except Exception:
                wb_box["wb"] = None
        return wb_box["wb"]

    sidx = 0
    for pl in plot:
        if not isinstance(pl.tag, str) or not _local(pl).endswith("Chart"):
            continue
        for ser in pl.findall(_c("ser")):
            tx = ser.find(_c("tx"))
            names, name_ref = _chart_points(tx)
            name = " ".join(v for v in names.values() if v)
            if not name and name_ref:
                name = " ".join(_ref_values(wb(), name_ref).values())
            name = name or f"Series {sidx + 1}"
            cat_el = ser.find(_c("cat"))
            if cat_el is None:
                cat_el = ser.find(_c("xVal"))
            val_el = ser.find(_c("val"))
            if val_el is None:
                val_el = ser.find(_c("yVal"))
            cats, cat_ref = _chart_points(cat_el)
            vals, val_ref = _chart_points(val_el)
            if not cats and cat_ref:
                cats = _ref_values(wb(), cat_ref)
            if not vals and val_ref:
                vals = _ref_values(wb(), val_ref)
            for i in sorted(set(vals) | set(cats)):
                lines.append(f"{name}: {cats.get(i, str(i + 1))}={vals.get(i, '')}")
            sidx += 1
    for ax in plot:
        if isinstance(ax.tag, str) and _local(ax) in ("catAx", "valAx", "dateAx", "serAx"):
            t = _rich_text(ax.find(_c("title")))
            if t:
                lines.append(f"axis: {t}")
    return lines


# ---------------------------------------------------------------------------------------------
# XLSX
# ---------------------------------------------------------------------------------------------

@functools.lru_cache(maxsize=6)
def _xlsx_cached(key: tuple[str, int, int], data_only: bool, read_only: bool = False):
    import openpyxl
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return openpyxl.load_workbook(key[0], data_only=data_only, read_only=read_only, keep_links=False)


def _xlsx(path: Path, data_only: bool):
    return _xlsx_cached(_stat_key(path), data_only)


def _sheet_by_name(wb, sheet) -> Any:
    if isinstance(sheet, int):
        if not 0 <= sheet < len(wb.sheetnames):
            raise LocatorError(f"sheet index {sheet} out of range")
        return wb[wb.sheetnames[sheet]]
    if sheet in wb.sheetnames:
        return wb[sheet]
    for n in wb.sheetnames:
        if n.strip().lower() == str(sheet).strip().lower():
            return wb[n]
    raise LocatorError(f"sheet {sheet!r} not found (sheets: {wb.sheetnames})")


_DATE_TOKEN = re.compile(r'(yyyy|yy|mmmm|mmm|mm|m|dddd|ddd|dd|d|hh|h|ss|s|am/pm|"[^"]*"|\\.|.)', re.I)


def _excel_date(value, fmt: str) -> str | None:
    if isinstance(value, _dt.date) and not isinstance(value, _dt.datetime):
        value = _dt.datetime(value.year, value.month, value.day)
    fmt = re.sub(r"\[[^\]]*\]", "", fmt.split(";")[0])
    toks = _DATE_TOKEN.findall(fmt)
    out, prev_h = [], False
    for t in toks:
        tl = t.lower()
        if tl == "yyyy":
            out.append(f"{value.year:04d}")
        elif tl == "yy":
            out.append(f"{value.year % 100:02d}")
        elif tl == "mmmm":
            out.append(value.strftime("%B"))
        elif tl == "mmm":
            out.append(value.strftime("%b"))
        elif tl in ("mm", "m"):
            if prev_h:
                out.append(f"{value.minute:02d}" if tl == "mm" else str(value.minute))
            else:
                out.append(f"{value.month:02d}" if tl == "mm" else str(value.month))
        elif tl == "dddd":
            out.append(value.strftime("%A"))
        elif tl == "ddd":
            out.append(value.strftime("%a"))
        elif tl == "dd":
            out.append(f"{value.day:02d}")
        elif tl == "d":
            out.append(str(value.day))
        elif tl in ("hh", "h"):
            out.append(f"{value.hour:02d}" if tl == "hh" else str(value.hour))
        elif tl in ("ss", "s"):
            out.append(f"{value.second:02d}")
        elif tl == "am/pm":
            out.append("AM" if value.hour < 12 else "PM")
        elif t.startswith('"'):
            out.append(t[1:-1])
        elif t.startswith("\\"):
            out.append(t[1:])
        else:
            out.append(t)
        if tl in ("hh", "h"):
            prev_h = True
        elif tl in ("yyyy", "yy", "mmmm", "mmm", "dddd", "ddd", "dd", "d", "mm", "m", "ss", "s"):
            prev_h = False
    return "".join(out)


def excel_format(value: Any, fmt: str | None) -> str | None:
    """Best-effort rendering of a cell value with its number format (thousands, %, currency, dates)."""
    if not fmt or fmt == "General" or value is None or isinstance(value, bool):
        return None
    try:
        if isinstance(value, (_dt.date, _dt.datetime)):
            return _excel_date(value, fmt)
        if not isinstance(value, (int, float)):
            return None
        section = fmt.split(";")[0]
        cur = re.search(r"\[\$([^\-\]]*)[^\]]*\]", section)
        section = re.sub(r"\[[^\]]*\]", lambda m: cur.group(1) if cur and m.group(0) == cur.group(0) else "", section)
        section = re.sub(r"_.|\*.", "", section).replace("\\", "")
        section = re.sub(r'"([^"]*)"', r"\1", section)
        m = re.search(r"[#0?][#0?,]*(\.[0?#]+)?", section)
        if not m:
            return None
        pct = "%" in section
        v = value * 100 if pct else value
        decimals = len(m.group(1)) - 1 if m.group(1) else 0
        num = f"{abs(v):,.{decimals}f}" if "," in m.group(0) else f"{abs(v):.{decimals}f}"
        prefix, suffix = section[:m.start()], section[m.end():]
        return ("-" if v < 0 else "") + prefix + num + suffix
    except Exception:
        return None


def _col_hidden(ws, col_idx: int) -> bool:
    for dim in ws.column_dimensions.values():
        if dim.hidden and dim.min and dim.max and dim.min <= col_idx <= dim.max:
            return True
    return False


def _xlsx_cell_render(cf, cv) -> tuple[str, str | None]:
    """(text, formula) for a cell: cached value, formatted value if different, formula."""
    from openpyxl.worksheet.formula import ArrayFormula
    vf = cf.value
    formula = None
    if isinstance(vf, ArrayFormula):
        formula = vf.text
    elif isinstance(vf, str) and cf.data_type == "f":
        formula = vf
    value = cv.value if cv is not None else (None if formula else vf)
    if formula is None and value is None:
        value = vf
    parts = []
    if value is not None and not (formula and value == formula):
        s = fmt_scalar(value, bool_style="excel")
        parts.append(s)
        f = excel_format(value, getattr(cf, "number_format", None))
        if f and f != s:
            parts.append(f)
    if formula:
        parts.append(formula)
    return "\n".join(parts), formula


def _r_xlsx_cell(path, loc, ctx):
    from openpyxl.utils.cell import coordinate_from_string, column_index_from_string
    wb_f, wb_v = _xlsx(path, False), _xlsx(path, True)
    ws = _sheet_by_name(wb_f, loc.get("sheet", 0))
    if not hasattr(ws, "merged_cells"):
        raise LocatorError(f"sheet {ws.title!r} is a chartsheet (no cells)")
    coord = str(loc.get("cell", "")).replace("$", "").upper()
    try:
        col_letter, row = coordinate_from_string(coord)
    except Exception:
        raise LocatorError(f"bad cell reference {loc.get('cell')!r}")
    merged = None
    for rng in ws.merged_cells.ranges:
        if coord in rng:
            merged = rng.coord
            coord = rng.start_cell.coordinate
            break
    cf = ws[coord]
    cv = wb_v[ws.title][coord]
    text, formula = _xlsx_cell_render(cf, cv)
    col_idx = column_index_from_string(col_letter)
    row_hidden = bool(ws.row_dimensions[row].hidden) if row in ws.row_dimensions else False
    col_hidden = _col_hidden(ws, col_idx)
    meta = {"sheet": ws.title, "sheet_state": ws.sheet_state, "row_hidden": row_hidden,
            "col_hidden": col_hidden, "merged_range": merged, "formula": formula,
            "value": fmt_scalar(cv.value, "excel") if cv.value is not None else None,
            "number_format": cf.number_format}
    meta["hidden"] = ws.sheet_state != "visible" or row_hidden or col_hidden
    return Resolved(text, meta)


def _xlsx_sheet_parts(z: zipfile.ZipFile) -> list[tuple[str, str, str]]:
    """[(sheet name, part name, state)] in workbook order (worksheets and chartsheets)."""
    wb_part = "xl/workbook.xml"
    try:
        rels_root = _parse_xml(z.read("_rels/.rels"))
        for rel in rels_root:
            if rel.get("Type", "").endswith("/officeDocument"):
                wb_part = rel.get("Target").lstrip("/")
    except KeyError:
        pass
    wb = _parse_xml(z.read(wb_part))
    rels = _rels_map(z, wb_part)
    out = []
    for s in wb.iter(_q("x", "sheet")):
        rid = s.get(_q("r", "id"))
        if rid in rels:
            out.append((s.get("name"), rels[rid][1], s.get("state", "visible")))
    return out


def _xlsx_chart_parts(z: zipfile.ZipFile, sheet_part: str) -> list[str]:
    """Chart part names anchored on a sheet, in drawing order."""
    rels = _rels_map(z, sheet_part)
    sheet_xml = _parse_xml(z.read(sheet_part))
    charts = []
    for d in sheet_xml.iter(_q("x", "drawing")):
        rid = d.get(_q("r", "id"))
        if rid not in rels:
            continue
        drawing_part = rels[rid][1]
        drels = _rels_map(z, drawing_part)
        dxml = _parse_xml(z.read(drawing_part))
        for c in dxml.iter(_c("chart")):
            crid = c.get(_q("r", "id"))
            if crid in drels:
                charts.append(drels[crid][1])
    return charts


def _r_xlsx_chart(path, loc, ctx):
    z = _zip(path)
    sheets = _xlsx_sheet_parts(z)
    want = loc.get("sheet", 0)
    sel = None
    if isinstance(want, int):
        if 0 <= want < len(sheets):
            sel = sheets[want]
    else:
        sel = next((s for s in sheets if s[0] == want), None) or \
            next((s for s in sheets if s[0].strip().lower() == str(want).strip().lower()), None)
    if sel is None:
        raise LocatorError(f"sheet {want!r} not found (sheets: {[s[0] for s in sheets]})")
    charts = _xlsx_chart_parts(z, sel[1])
    idx = _int(loc, "chart_index", "index") if loc.get("chart_index", loc.get("index")) is not None else 0
    if not 0 <= idx < len(charts):
        raise LocatorError(f"chart_index {idx} out of range ({len(charts)} charts on {sel[0]!r})")
    cs = _parse_xml(z.read(charts[idx]))
    lines = chart_lines(cs, lambda: _xlsx(path, True))
    return Resolved("\n".join(lines), {"sheet": sel[0], "sheet_state": sel[2], "chart_part": charts[idx],
                                       "chart_count": len(charts)})


# ---------------------------------------------------------------------------------------------
# PDF
# ---------------------------------------------------------------------------------------------

@functools.lru_cache(maxsize=8)
def _pdf_cached(key: tuple[str, int, int]):
    import pymupdf
    return pymupdf.open(key[0])


def _pdf(path: Path):
    return _pdf_cached(_stat_key(Path(path)))


def pdf_page_needs_ocr(page, text: str | None = None) -> bool:
    """No usable text layer, or images cover a large share of the page."""
    if text is None:
        text = page.get_text("text")
    if len(re.sub(r"\s", "", text)) < PDF_OCR_MIN_CHARS:
        return True
    try:
        area = abs(page.rect)
        covered = 0.0
        for info in page.get_image_info():
            r = page.rect & info["bbox"]
            covered += abs(r) if not r.is_empty else 0.0
        return area > 0 and covered / area >= PDF_OCR_IMAGE_COVER
    except Exception:
        return False


def _r_pdf_page(path, loc, ctx):
    doc = _pdf(path)
    n = doc.page_count
    p = _int(loc, "page")
    q = int(loc.get("end_page", p))
    if not (1 <= p <= q <= n):
        raise LocatorError(f"page {p}..{q} out of range (1..{n})")
    texts = []
    for k in range(p, q + 1):
        if loc.get("ocr"):
            texts.append(ocr_pdf_page(path, k, int(loc.get("dpi", OCR_DPI)), allow_compute=ctx.ocr))
        else:
            texts.append(doc[k - 1].get_text("text"))
    return Resolved("\n".join(texts), {"page_count": n})


# ---------------------------------------------------------------------------------------------
# CSV, JSON, YAML, XML, HTML, text, images
# ---------------------------------------------------------------------------------------------

try:
    csv.field_size_limit(sys.maxsize)
except OverflowError:
    csv.field_size_limit(2 ** 31 - 1)


@functools.lru_cache(maxsize=64)
def _csv_dialect_cached(key: tuple[str, int, int]) -> tuple[str, str]:
    path = Path(key[0])
    enc = _detect_encoding(path)
    with open(path, encoding=enc, errors="replace", newline="") as fh:
        sample = fh.read(65536)
    try:
        delim = csv.Sniffer().sniff(sample, delimiters=",;\t|").delimiter
    except csv.Error:
        delim = ","
    return enc, delim


def iter_csv(path: Path) -> Iterator[list[str]]:
    """Stream CSV records (header first) with sniffed encoding and delimiter."""
    enc, delim = _csv_dialect_cached(_stat_key(path))
    with open(path, encoding=enc, errors="replace", newline="") as fh:
        yield from csv.reader(fh, delimiter=delim)


def _csv_row_text(header: list[str], rec: list[str]) -> str:
    return " | ".join(f"{h}: {v}" for h, v in itertools.zip_longest(header, rec, fillvalue=""))


def _r_csv_row(path, loc, ctx):
    row = _int(loc, "row")
    it = iter_csv(path)
    try:
        header = next(it)
    except StopIteration:
        raise LocatorError("empty CSV")
    if row == 0:
        return Resolved(" | ".join(header), {"header": header})
    if row < 0:
        raise LocatorError("row must be >= 1 (0 = header)")
    rec = next(itertools.islice(it, row - 1, None), None)
    if rec is None:
        raise LocatorError(f"row {row} beyond end of file")
    col = loc.get("column")
    meta = {"header": header}
    if col is None:
        return Resolved(_csv_row_text(header, rec), meta)
    if isinstance(col, int):
        ci = col
    elif col in header:
        ci = header.index(col)
    else:
        low = [h.strip().lower() for h in header]
        if str(col).strip().lower() not in low:
            raise LocatorError(f"column {col!r} not in header {header}")
        ci = low.index(str(col).strip().lower())
    if ci >= len(rec):
        return Resolved("", meta)
    return Resolved(rec[ci], meta)


@functools.lru_cache(maxsize=8)
def _json_cached(key: tuple[str, int, int]):
    text = read_text(Path(key[0]))
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        lines = [ln for ln in text.splitlines() if ln.strip()]
        try:
            return [json.loads(ln) for ln in lines]  # JSON Lines
        except json.JSONDecodeError as exc:
            raise LocatorError(f"invalid JSON: {exc}") from exc


def _r_json_pointer(path, loc, ctx):
    doc = _json_cached(_stat_key(path))
    ptr = loc.get("pointer", "")
    if ptr and not ptr.startswith("/"):
        raise LocatorError("JSON pointer must start with '/' (RFC 6901)")
    node = doc
    for raw in ptr.split("/")[1:] if ptr else []:
        tok = raw.replace("~1", "/").replace("~0", "~")
        if isinstance(node, list):
            try:
                node = node[int(tok)]
            except (ValueError, IndexError):
                raise LocatorError(f"pointer token {tok!r} invalid for array of {len(node)}")
        elif isinstance(node, dict):
            if tok not in node:
                raise LocatorError(f"pointer key {tok!r} not found")
            node = node[tok]
        else:
            raise LocatorError(f"pointer descends into scalar at {tok!r}")
    return Resolved(render_value(node, "/"), {})


class _LenientYamlLoader(yaml.SafeLoader):
    """SafeLoader that tolerates unknown tags (e.g. !Ref) by constructing plain values."""


def _yaml_unknown(loader, suffix, node):
    if isinstance(node, yaml.ScalarNode):
        return loader.construct_scalar(node)
    if isinstance(node, yaml.SequenceNode):
        return loader.construct_sequence(node, deep=True)
    return loader.construct_mapping(node, deep=True)


_LenientYamlLoader.add_multi_constructor("!", _yaml_unknown)


@functools.lru_cache(maxsize=8)
def _yaml_cached(key: tuple[str, int, int]) -> list:
    import yaml
    try:
        return list(yaml.load_all(read_text(Path(key[0])), Loader=_LenientYamlLoader))
    except yaml.YAMLError as exc:
        raise LocatorError(f"invalid YAML: {exc}") from exc


def parse_yaml_path(path: str) -> list[str | int]:
    """Split 'a.b[2]."x.y".c' or 'paths."/claims/{id}".get' into keys and indexes."""
    toks: list[str | int] = []
    i, n = 0, len(path)
    while i < n:
        ch = path[i]
        if ch == ".":
            i += 1
        elif ch in "\"'":
            j, buf = i + 1, []
            while j < n and path[j] != ch:
                if path[j] == "\\" and j + 1 < n:
                    j += 1
                buf.append(path[j])
                j += 1
            if j >= n:
                raise LocatorError(f"unterminated quote in yaml path {path!r}")
            toks.append("".join(buf))
            i = j + 1
        elif ch == "[":
            j = path.find("]", i)
            if j < 0:
                raise LocatorError(f"unterminated [ in yaml path {path!r}")
            inner = path[i + 1:j].strip()
            if inner[:1] in "\"'":
                toks.append(inner[1:-1])
            else:
                try:
                    toks.append(int(inner))
                except ValueError:
                    toks.append(inner)
            i = j + 1
        else:
            j = i
            while j < n and path[j] not in ".[":
                j += 1
            toks.append(path[i:j])
            i = j
    return toks


_YAML_TRUE, _YAML_FALSE = {"true", "yes", "on", "y"}, {"false", "no", "off", "n"}


def _yaml_step(node, tok):
    if isinstance(node, list):
        try:
            return node[int(tok)]
        except (ValueError, IndexError, TypeError):
            raise LocatorError(f"index {tok!r} invalid for list of {len(node)}")
    if isinstance(node, dict):
        if tok in node:
            return node[tok]
        st = str(tok)
        for k in node:
            if fmt_scalar(k) == st or str(k) == st or str(k).lower() == st.lower():
                return node[k]
        if st.lower() in _YAML_TRUE and True in node:
            return node[True]
        if st.lower() in _YAML_FALSE and False in node:
            return node[False]
        raise LocatorError(f"key {tok!r} not found (keys: {list(node)[:20]})")
    raise LocatorError(f"path descends into scalar at {tok!r}")


def _r_yaml_path(path, loc, ctx):
    docs = _yaml_cached(_stat_key(path))
    di = int(loc.get("doc_index", 0))
    if not 0 <= di < len(docs):
        raise LocatorError(f"doc_index {di} out of range ({len(docs)} documents)")
    node = docs[di]
    for tok in parse_yaml_path(str(loc.get("path", ""))):
        node = _yaml_step(node, tok)
    return Resolved(render_value(node, "."), {"doc_count": len(docs)})


@functools.lru_cache(maxsize=8)
def _xml_cached(key: tuple[str, int, int]):
    return etree.parse(key[0], parser=_XML_PARSER)


@functools.lru_cache(maxsize=8)
def _xml_stripped_cached(key: tuple[str, int, int]):
    """A copy of the tree with namespaces removed, so plain XPath works on namespaced XML."""
    tree = etree.parse(key[0], parser=_XML_PARSER)
    for el in tree.getroot().iter():
        if isinstance(el.tag, str) and "}" in el.tag:
            el.tag = el.tag.split("}", 1)[1]
        for a in list(el.attrib):
            if "}" in a:
                el.attrib[a.split("}", 1)[1]] = el.attrib.pop(a)
    etree.cleanup_namespaces(tree)
    return tree


def _xml_element_text(el) -> str:
    texts = [t.strip() for t in el.xpath(".//text()") if t.strip()]
    attrs = [f"{etree.QName(a).localname}={v}" for d in el.iter() if isinstance(d.tag, str)
             for a, v in d.attrib.items()]
    return "\n".join(x for x in (" ".join(texts), "\n".join(attrs)) if x)


def _xpath_results_text(res, el_text: Callable[[Any], str]) -> str:
    if isinstance(res, (str, bytes)):
        return res if isinstance(res, str) else res.decode()
    if isinstance(res, (bool, float, int)):
        return fmt_scalar(res)
    out = []
    for r in res:
        if isinstance(r, str):
            out.append(str(r))
        elif isinstance(r, etree._Comment):
            out.append(r.text or "")
        elif hasattr(r, "tag"):
            out.append(el_text(r))
        else:
            out.append(str(r))
    return "\n".join(out)


def _r_xml_xpath(path, loc, ctx):
    xp = loc.get("xpath")
    if not xp:
        raise LocatorError("xml_xpath needs xpath")
    key = _stat_key(path)
    try:
        tree = _xml_cached(key)
    except etree.XMLSyntaxError as exc:
        raise LocatorError(f"invalid XML: {exc}") from exc
    try:
        res = tree.xpath(xp)
        if (isinstance(res, list) and not res) and tree.getroot().nsmap:
            res = _xml_stripped_cached(key).xpath(xp)
    except etree.XPathError as exc:
        raise LocatorError(f"bad xpath {xp!r}: {exc}") from exc
    if isinstance(res, list) and not res:
        raise LocatorError(f"xpath {xp!r} matched nothing")
    return Resolved(_xpath_results_text(res, _xml_element_text), {})


_HTML_BLOCK = {"p", "div", "li", "ul", "ol", "table", "tr", "td", "th", "h1", "h2", "h3", "h4", "h5",
               "h6", "br", "section", "article", "header", "footer", "nav", "aside", "pre", "blockquote",
               "dl", "dt", "dd", "figure", "figcaption", "caption", "thead", "tbody", "tfoot", "form",
               "title", "main", "hr", "address", "summary", "details", "label", "option"}
_HTML_SKIP = {"script", "style", "template", "noscript"}


def html_text(el) -> str:
    """Block-aware visible text of an lxml.html element (img alt text included)."""
    parts: list[str] = []

    def walk(e):
        if not isinstance(e.tag, str):
            return
        tag = e.tag.lower()
        if tag in _HTML_SKIP:
            return
        block = tag in _HTML_BLOCK
        if block:
            parts.append("\n")
        elif tag in ("td", "th"):
            parts.append("\t")
        if tag == "img" and e.get("alt"):
            parts.append(f" {e.get('alt')} ")
        if e.text:
            parts.append(e.text)
        for c in e:
            walk(c)
            if c.tail:
                parts.append(c.tail)
        if block:
            parts.append("\n")

    walk(el)
    return re.sub(r"\n\s*\n+", "\n", "".join(parts)).strip()


@functools.lru_cache(maxsize=8)
def _html_cached(key: tuple[str, int, int]):
    import lxml.html
    return lxml.html.parse(key[0])


def _r_html_xpath(path, loc, ctx):
    xp = loc.get("xpath")
    if not xp:
        raise LocatorError("html_xpath needs xpath")
    tree = _html_cached(_stat_key(path))
    try:
        res = tree.xpath(xp)
    except etree.XPathError as exc:
        raise LocatorError(f"bad xpath {xp!r}: {exc}") from exc
    if isinstance(res, list) and not res:
        raise LocatorError(f"xpath {xp!r} matched nothing")
    return Resolved(_xpath_results_text(res, html_text), {})


def _lines_slice(lines: Iterator[str] | list[str], start: int, end: int) -> list[str]:
    return [ln.rstrip("\r\n") for ln in itertools.islice(lines, start - 1, end)]


def _r_text_lines(path, loc, ctx):
    start = _int(loc, "start")
    end = int(loc.get("end", start))
    if start < 1 or end < start:
        raise LocatorError(f"bad line range {start}..{end}")
    if path.suffix.lower() in DERIVED_TEXT_EXTS:
        lines = derived_text(path).splitlines()
        if start > len(lines):
            raise LocatorError(f"line {start} beyond end ({len(lines)} lines)")
        return Resolved("\n".join(lines[start - 1:end]), {"line_count": len(lines), "derived": True})
    enc = _detect_encoding(path)
    with open(path, encoding=enc, errors="replace", newline="") as fh:
        got = _lines_slice(fh, start, end)
    if not got:
        raise LocatorError(f"line {start} beyond end of file")
    return Resolved("\n".join(got), {})


def _r_image_ocr(path, loc, ctx):
    return Resolved(ocr_image_file(path, allow_compute=ctx.ocr), {})


# ---------------------------------------------------------------------------------------------
# Derived plain text for rejected formats (.rtf .eml .odt .vsdx .msg) and zip members
# ---------------------------------------------------------------------------------------------

_RTF_TOKEN = re.compile(r"\\([a-z]{1,32})(-?\d{1,10})? ?|\\'([0-9a-f]{2})|\\([^a-z])|([{}])|[\r\n]+|(.)",
                        re.I | re.S)
_RTF_SKIP_DEST = {"fonttbl", "colortbl", "stylesheet", "info", "pict", "themedata", "colorschememapping",
                  "datastore", "latentstyles", "listtable", "listoverridetable", "rsidtbl", "generator",
                  "xmlnstbl", "mmathpr", "object", "objdata", "filetbl", "revtbl", "pgdsctbl", "fldinst",
                  "header", "footer", "headerl", "headerr", "footerl", "footerr", "wgrffmtfilter"}
_RTF_SPECIAL = {"par": "\n", "sect": "\n", "page": "\n", "line": "\n", "tab": "\t", "cell": "\t",
                "row": "\n", "emdash": "\u2014", "endash": "\u2013", "lquote": "\u2018",
                "rquote": "\u2019", "ldblquote": "\u201c", "rdblquote": "\u201d", "bullet": "\u2022"}


def rtf_to_text(rtf: str) -> str:
    """Minimal RTF-to-text: honours groups, ignorable destinations, \\uN and \\'hh escapes."""
    stack: list[tuple[int, bool]] = []
    ignorable, ucskip, curskip = False, 1, 0
    out: list[str] = []
    for m in _RTF_TOKEN.finditer(rtf):
        word, arg, hexc, char, brace, tchar = m.groups()
        if brace:
            curskip = 0
            if brace == "{":
                stack.append((ucskip, ignorable))
            elif stack:
                ucskip, ignorable = stack.pop()
        elif char:
            curskip = 0
            if char == "~":
                if not ignorable:
                    out.append("\u00a0")
            elif char in "{}\\":
                if not ignorable:
                    out.append(char)
            elif char == "*":
                ignorable = True
            elif char == "-":
                pass
            elif char == "_":
                if not ignorable:
                    out.append("-")
        elif word:
            curskip = 0
            w = word.lower()
            if w in _RTF_SKIP_DEST:
                ignorable = True
            elif ignorable:
                pass
            elif w in _RTF_SPECIAL:
                out.append(_RTF_SPECIAL[w])
            elif w == "uc":
                ucskip = int(arg or 1)
            elif w == "u":
                c = int(arg)
                if c < 0:
                    c += 0x10000
                out.append(chr(c))
                curskip = ucskip
        elif hexc:
            if curskip > 0:
                curskip -= 1
            elif not ignorable:
                out.append(bytes([int(hexc, 16)]).decode("cp1252", errors="replace"))
        elif tchar:
            if curskip > 0:
                curskip -= 1
            elif not ignorable:
                out.append(tchar)
    return re.sub(r"[ \t]+\n", "\n", "".join(out)).strip()


def eml_to_text(data: bytes) -> str:
    msg = email.message_from_bytes(data, policy=email.policy.default)
    lines = [f"{h}: {msg[h]}" for h in ("From", "To", "Cc", "Date", "Subject") if msg[h]]
    lines.append("")
    for part in msg.walk():
        if part.is_multipart():
            continue
        ctype = part.get_content_type()
        fname = part.get_filename()
        try:
            if ctype == "text/plain" and not fname:
                lines.append(part.get_content())
            elif ctype == "text/html" and not fname:
                import lxml.html
                lines.append(html_text(lxml.html.fromstring(part.get_content())))
            elif fname:
                lines.append(f"[attachment: {fname}]")
                if ctype.startswith("text/"):
                    lines.append(part.get_content())
        except Exception:
            continue
    return "\n".join(lines).strip()


def odf_text(path: Path) -> str:
    """Paragraph/heading text of an OpenDocument file (content.xml)."""
    root = _parse_xml(_zip(path).read("content.xml"))
    TEXT = "urn:oasis:names:tc:opendocument:xmlns:text:1.0"
    out = []

    def para(e) -> str:
        buf = [e.text or ""]
        for c in e:
            ln = etree.QName(c).localname if isinstance(c.tag, str) else ""
            if ln == "s":
                buf.append(" " * int(c.get(f"{{{TEXT}}}c", "1")))
            elif ln == "tab":
                buf.append("\t")
            elif ln == "line-break":
                buf.append("\n")
            elif ln not in ("note-citation",):
                buf.append(para(c))
            buf.append(c.tail or "")
        return "".join(buf)

    for e in root.iter(f"{{{TEXT}}}p", f"{{{TEXT}}}h"):
        if any(etree.QName(a).localname in ("p", "h") and etree.QName(a).namespace == TEXT
               for a in e.iterancestors()):
            continue
        out.append(para(e))
    return "\n".join(out).strip()


def vsdx_text(path: Path) -> str:
    z = _zip(path)
    out = []
    try:
        pages_root = _parse_xml(z.read("visio/pages/pages.xml"))
        for p in pages_root:
            if isinstance(p.tag, str) and (p.get("Name") or p.get("NameU")):
                out.append(f"page: {p.get('Name') or p.get('NameU')}")
    except KeyError:
        pass
    names = sorted((n for n in z.namelist() if re.match(r"visio/pages/page\d+\.xml$", n)),
                   key=lambda n: int(re.search(r"(\d+)", n.rsplit("/", 1)[1]).group(1)))
    for n in names:
        root = _parse_xml(z.read(n))
        for el in root.iter():
            if isinstance(el.tag, str) and etree.QName(el).localname == "Text":
                t = _one_line("".join(el.itertext()))
                if t:
                    out.append(t)
    return "\n".join(out)


def strings_text(data: bytes, min_len: int = 4) -> str:
    """Printable ASCII and UTF-16LE runs, in file order (like `strings`)."""
    found = [(m.start(), m.group().decode("ascii")) for m in re.finditer(rb"[\x20-\x7e\t]{%d,}" % min_len, data)]
    found += [(m.start(), m.group().decode("utf-16-le"))
              for m in re.finditer(rb"(?:[\x20-\x7e]\x00){%d,}" % min_len, data)]
    found.sort()
    out, last = [], None
    for _, s in found:
        if s != last:
            out.append(s)
        last = s
    return "\n".join(out)


def msg_text(path: Path) -> str:
    try:
        import olefile  # type: ignore
    except ImportError:
        return strings_text(path.read_bytes())
    ole = olefile.OleFileIO(str(path))
    out = []
    for entry in ole.listdir():
        name = entry[-1]
        if name.startswith("__substg1.0_") and name.endswith(("001F", "001E")):
            raw = ole.openstream(entry).read()
            out.append(raw.decode("utf-16-le" if name.endswith("001F") else "cp1252", errors="replace"))
    return "\n".join(t.strip("\x00") for t in out if t.strip("\x00"))


def derived_text(path: Path) -> str:
    """Plain text for formats the corpus only stores in the rejected set."""
    ext = path.suffix.lower()
    if ext == ".rtf":
        return rtf_to_text(read_text(path))
    if ext == ".eml":
        return eml_to_text(path.read_bytes())
    if ext in (".odt", ".ods", ".odp"):
        return odf_text(path)
    if ext == ".vsdx":
        return vsdx_text(path)
    if ext == ".msg":
        return msg_text(path)
    return read_text(path)


def _safe_member_path(member: str) -> str:
    norm = posixpath.normpath(member.replace("\\", "/"))
    if norm.startswith(("/", "../")) or norm == "..":
        raise LocatorError(f"unsafe zip member path {member!r}")
    return norm


def extract_zip_member(path: Path, member: str) -> Path:
    """Extract one member into build/cache/zip/<zip sha1>/ (cached) and return its path."""
    safe = _safe_member_path(member)
    out = ZIP_CACHE_DIR / file_sha1(path) / safe
    if not out.exists():
        try:
            data = _zip(path).read(member)
        except KeyError:
            raise LocatorError(f"member {member!r} not in zip")
        out.parent.mkdir(parents=True, exist_ok=True)
        tmp = out.with_name(out.name + f".{os.getpid()}.tmp")
        tmp.write_bytes(data)
        os.replace(tmp, out)
    return out


def _r_zip_member(path, loc, ctx):
    z = _zip(path)
    member = loc.get("member")
    if not member:
        return Resolved("\n".join(z.namelist()), {"members": len(z.namelist())})
    inner_path = extract_zip_member(path, member)
    inner = loc.get("inner")
    if inner:
        return _dispatch(inner_path, inner, ctx)
    return Resolved("\n".join(t for _, t in iter_units(inner_path, ocr=ctx.ocr)), {"member": member})


# ---------------------------------------------------------------------------------------------
# Generated code repos (build/code_repo/variant_<a|b|c>/)
# ---------------------------------------------------------------------------------------------

_CODE_ROOT_OVERRIDE: Path | None = None


def set_code_repo_root(path: os.PathLike | str | None) -> None:
    """Override where variant_<x>/ repos live (default: <repo_root>/build/code_repo, or $CODE_REPO_ROOT)."""
    global _CODE_ROOT_OVERRIDE
    _CODE_ROOT_OVERRIDE = Path(path) if path else None


def code_repo_root(repo_root: Path = ROOT) -> Path:
    if _CODE_ROOT_OVERRIDE is not None:
        return _CODE_ROOT_OVERRIDE
    env = os.environ.get("CODE_REPO_ROOT")
    return Path(env) if env else Path(repo_root) / "build" / "code_repo"


def variant_dir(variant: str, repo_root: Path = ROOT) -> Path:
    v = str(variant)
    return code_repo_root(repo_root) / (v if v.startswith("variant_") else f"variant_{v}")


def _r_code_lines(path, loc, ctx):
    if loc.get("path"):
        f = variant_dir(loc.get("variant", "a"), ctx.repo_root) / loc["path"]
    elif path is not None:
        f = path
    else:
        raise LocatorError("code_lines needs variant+path")
    if not f.exists():
        raise LocatorError(f"code file not found: {f}")
    start = _int(loc, "start")
    end = int(loc.get("end", start))
    with open(f, encoding=_detect_encoding(f), errors="replace", newline="") as fh:
        got = _lines_slice(fh, start, end)
    if not got:
        raise LocatorError(f"line {start} beyond end of {f.name}")
    return Resolved("\n".join(got), {"path": str(f)})


@functools.lru_cache(maxsize=16)
def _git_log_cached(repo: str, stamp: str) -> list[dict]:
    fmt = "%H%x00%an%x00%ae%x00%ad%x00%B%x1e"
    res = subprocess.run(["git", "-C", repo, "log", "--all", "--date=iso-strict", f"--format={fmt}"],
                         capture_output=True, text=True, timeout=120)
    if res.returncode != 0:
        raise LocatorError(f"git log failed in {repo}: {res.stderr.strip()}")
    out = []
    for rec in res.stdout.split("\x1e"):
        rec = rec.lstrip("\n")
        if not rec:
            continue
        sha, an, ae, ad, msg = (rec.split("\x00", 4) + [""] * 5)[:5]
        out.append({"sha": sha, "author": an, "email": ae, "date": ad, "message": msg.strip()})
    return out


def git_log(repo: Path) -> list[dict]:
    """Commits of a repo (all refs), cached until refs change."""
    gd = repo / ".git"
    stamp = []
    for p in (gd / "HEAD", gd / "packed-refs", gd / "refs" / "heads", gd / "logs" / "HEAD"):
        try:
            stamp.append(str(p.stat().st_mtime_ns))
        except OSError:
            stamp.append("-")
    return _git_log_cached(str(repo), "|".join(stamp))


def format_commit(c: dict) -> str:
    return f"commit {c['sha']}\nAuthor: {c['author']} <{c['email']}>\nDate: {c['date']}\n\n{c['message']}"


def _r_git_commit(path, loc, ctx):
    repo = Path(loc["repo"]) if loc.get("repo") else variant_dir(loc.get("variant", "a"), ctx.repo_root)
    if not (repo / ".git").exists():
        raise LocatorError(f"not a git repo: {repo}")
    commits = git_log(repo)
    if loc.get("sha"):
        hits = [c for c in commits if c["sha"].startswith(str(loc["sha"]))]
    else:
        needle = loc.get("message_contains")
        if not needle:
            raise LocatorError("git_commit needs message_contains (or sha)")
        hits = [c for c in commits if match(needle, c["message"])]
        if not hits:
            hits = [c for c in commits if match(needle, f"{c['author']} <{c['email']}>")]
    if not hits:
        raise LocatorError("no matching commit")
    return Resolved("\n\n".join(format_commit(c) for c in hits),
                    {"matches": len(hits), "shas": [c["sha"] for c in hits]})


# ---------------------------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------------------------

_RESOLVERS: dict[str, Callable[[Path, dict, _Ctx], Resolved]] = {
    "pdf_page": _r_pdf_page,
    "docx_para": _r_docx_para,
    "docx_table": _r_docx_table,
    "docx_comment": _r_docx_comment,
    "docx_footnote": _r_docx_footnote,
    "docx_endnote": _r_docx_endnote,
    "docx_header": _r_docx_hf("header"),
    "docx_footer": _r_docx_hf("footer"),
    "docx_tracked": _r_docx_tracked,
    "docx_image": _r_docx_image,
    "docx_alt_text": _r_docx_alt_text,
    "pptx_slide": _r_pptx_slide,
    "xlsx_cell": _r_xlsx_cell,
    "xlsx_chart": _r_xlsx_chart,
    "csv_row": _r_csv_row,
    "json_pointer": _r_json_pointer,
    "xml_xpath": _r_xml_xpath,
    "yaml_path": _r_yaml_path,
    "html_xpath": _r_html_xpath,
    "text_lines": _r_text_lines,
    "image_ocr": _r_image_ocr,
    "code_lines": _r_code_lines,
    "git_commit": _r_git_commit,
    "zip_member": _r_zip_member,
}
_NO_FILE_KINDS = {"code_lines", "git_commit"}


def _dispatch(path: Path | None, locator: dict, ctx: _Ctx) -> Resolved:
    kind = locator.get("kind")
    fn = _RESOLVERS.get(kind)
    if fn is None:
        raise LocatorError(f"unknown locator kind {kind!r}")
    if kind not in _NO_FILE_KINDS:
        if path is None or not path.exists():
            raise LocatorError(f"file not found: {path}")
    try:
        return fn(path, locator, ctx)
    except LocatorError:
        raise
    except (KeyError, IndexError, ValueError, TypeError, zipfile.BadZipFile, etree.XMLSyntaxError) as exc:
        raise LocatorError(f"{type(exc).__name__}: {exc}") from exc


def resolve_ex(file_path: os.PathLike | str | None, locator: dict, repo_root: os.PathLike | str = ROOT,
               ocr: bool = True) -> Resolved:
    """Resolve a locator to its text plus metadata (see Resolved). Raises LocatorError."""
    if not isinstance(locator, dict) or "kind" not in locator:
        raise LocatorError("locator must be a mapping with a 'kind'")
    repo_root = Path(repo_root)
    path = _abs_path(file_path, repo_root) if file_path else None
    return _dispatch(path, locator, _Ctx(repo_root=repo_root, ocr=ocr))


def resolve(file_path: os.PathLike | str | None, locator: dict, repo_root: os.PathLike | str = ROOT,
            ocr: bool = True) -> str:
    """Text at ``locator`` in ``file_path`` (relative paths are taken from ``repo_root``)."""
    return resolve_ex(file_path, locator, repo_root, ocr).text


def locator_needs_ocr(locator: dict) -> bool:
    """True when the locator's text comes from OCR (verify with match(..., 'ocr_fuzzy'))."""
    if not isinstance(locator, dict):
        return False
    kind = locator.get("kind")
    if locator.get("ocr") or kind in ("docx_image", "image_ocr"):
        return True
    if kind == "pptx_slide" and locator.get("where") == "image":
        return True
    if kind == "zip_member" and isinstance(locator.get("inner"), dict):
        return locator_needs_ocr(locator["inner"])
    return False


# ---------------------------------------------------------------------------------------------
# extract_all: every textual unit of a file
# ---------------------------------------------------------------------------------------------

def _units_docx(path: Path, ctx: _Ctx):
    info = _docx_info(path)
    heads = {h.index: h.text for h in info.headings()}
    current = None
    for i in range(len(info.paragraphs)):
        current = heads.get(i, current)
        t = info.para_text(i)
        if t.strip():
            loc = {"kind": "docx_para", "para_index": i}
            if current:
                loc["section"] = current
            yield loc, t

    def table_units(table, base: dict, nested: list):
        keep, seen = [], set()   # keep refs alive so id() of merged-cell elements stays stable
        for r, row in enumerate(table.rows):
            for c, cell in enumerate(row.cells):
                if id(cell._tc) in seen:
                    continue
                keep.append(cell._tc)
                seen.add(id(cell._tc))
                loc = dict(base)
                if nested:
                    steps = nested[:-1] + [[nested[-1][0], r, c]]
                    loc["nested"] = steps[0] if len(steps) == 1 else steps
                else:
                    loc.update(row=r, col=c)
                t = _cell_text(cell)
                if t.strip():
                    yield loc, t
                for k, inner in enumerate(cell.tables):
                    inner_base = dict(base) if nested else dict(base, row=r, col=c)
                    prev = nested[:-1] + [[nested[-1][0], r, c]] if nested else []
                    yield from table_units(inner, inner_base, prev + [[k, 0, 0]])

    for ti, table in enumerate(info.doc.tables):
        yield from table_units(table, {"kind": "docx_table", "table_index": ti}, [])

    for reltype, tag, kind, key in (("comments", "comment", "docx_comment", "comment_id"),
                                     ("footnotes", "footnote", "docx_footnote", "footnote_id"),
                                     ("endnotes", "endnote", "docx_endnote", "endnote_id")):
        for part in info.parts_by_reltype(reltype):
            for el in info.part_xml(part).iterchildren(_q("w", tag)):
                if el.get(_q("w", "type")) in ("separator", "continuationSeparator", "continuationNotice"):
                    continue
                t = _wml_block_text(el)
                if t.strip():
                    yield {"kind": kind, key: int(el.get(W_ID))}, t
    for si in range(len(info.section_props())):
        for which in ("header", "footer"):
            t = "\n".join(x for _, x in _hf_texts(info, which, si) if x)
            if t.strip():
                yield {"kind": f"docx_{which}", "section_index": si}, t
    for typ in ("ins", "del"):
        for k, el in enumerate(info.tracked(typ)):
            t = _wml_text(el, deleted=True)
            if t.strip():
                yield {"kind": "docx_tracked", "type": typ, "index": k}, t
    for k, el in enumerate(info.doc_prs()):
        t = "\n".join(x for x in (el.get("descr"), el.get("title")) if x)
        if t.strip():
            yield {"kind": "docx_alt_text", "image_index": k}, t
    if ctx.ocr:
        z = _zip(_as_docx(path))
        for name in sorted(n for n in z.namelist() if n.startswith("word/media/")):
            if posixpath.splitext(name)[1].lower() in IMAGE_EXTS:
                try:
                    t = ocr_image_bytes(z.read(name))
                except LocatorError:
                    continue
                if t.strip():
                    yield {"kind": "docx_image", "image_name": posixpath.basename(name), "ocr": True}, t


def _units_pptx(path: Path, ctx: _Ctx):
    prs = _pptx(path)
    for n, slide in enumerate(prs.slides, 1):
        for where in PPTX_WHERES:
            if where == "image" and not ctx.ocr:
                continue
            try:
                t, _ = _pptx_where(prs, slide, where, None, ctx)
            except LocatorError:
                continue
            if t.strip():
                yield {"kind": "pptx_slide", "slide": n, "where": where}, t


def _units_xlsx(path: Path, ctx: _Ctx):
    wb_f, wb_v = _xlsx(path, False), _xlsx(path, True)
    for ws in wb_f.worksheets:
        ws_v = wb_v[ws.title]
        hidden_sheet = ws.sheet_state != "visible"
        for row in ws.iter_rows():
            for cf in row:
                if cf.value is None:
                    continue
                text, _ = _xlsx_cell_render(cf, ws_v[cf.coordinate])
                if text.strip():
                    loc = {"kind": "xlsx_cell", "sheet": ws.title, "cell": cf.coordinate}
                    if hidden_sheet:
                        loc["hidden"] = True
                    yield loc, text
    z = _zip(path)
    for name, part, state in _xlsx_sheet_parts(z):
        try:
            charts = _xlsx_chart_parts(z, part)
        except KeyError:
            continue
        for k, cpart in enumerate(charts):
            lines = chart_lines(_parse_xml(z.read(cpart)), lambda: _xlsx(path, True))
            if lines:
                yield {"kind": "xlsx_chart", "sheet": name, "chart_index": k}, "\n".join(lines)


def _units_pdf(path: Path, ctx: _Ctx):
    doc = _pdf(path)
    for i in range(doc.page_count):
        page = doc[i]
        t = page.get_text("text")
        if t.strip():
            yield {"kind": "pdf_page", "page": i + 1}, t
        if ctx.ocr and pdf_page_needs_ocr(page, t):
            ot = ocr_pdf_page(path, i + 1)
            if ot.strip():
                yield {"kind": "pdf_page", "page": i + 1, "ocr": True}, ot


def _units_csv(path: Path, ctx: _Ctx):
    it = iter_csv(path)
    header = next(it, None)
    if header is None:
        return
    yield {"kind": "csv_row", "row": 0}, " | ".join(header)
    for i, rec in enumerate(it, 1):
        if any(x.strip() for x in rec):
            yield {"kind": "csv_row", "row": i}, _csv_row_text(header, rec)


def _tree_units(node, ptr_parts: list, make_loc: Callable[[list], dict], sep: str):
    """Per-record units: a node becomes one unit when small enough, else recurse."""
    if isinstance(node, (dict, list)):
        size = len(json.dumps(node, default=str, ensure_ascii=False))
        if size > JSON_UNIT_CHARS and node:
            items = node.items() if isinstance(node, dict) else enumerate(node)
            for k, v in items:
                yield from _tree_units(v, ptr_parts + [k], make_loc, sep)
            return
    t = render_value(node, sep)
    if t.strip():
        yield make_loc(ptr_parts), t


def _json_ptr(parts: list) -> str:
    return "".join("/" + str(p).replace("~", "~0").replace("/", "~1") for p in parts)


def _units_json(path: Path, ctx: _Ctx):
    doc = _json_cached(_stat_key(path))
    yield from _tree_units(doc, [], lambda p: {"kind": "json_pointer", "pointer": _json_ptr(p)}, "/")


_BARE_KEY = re.compile(r"^[A-Za-z0-9_\-]+$")


def yaml_path_str(parts: list) -> str:
    out = []
    for p in parts:
        if isinstance(p, int):
            out.append(f"[{p}]")
        else:
            s = fmt_scalar(p)
            seg = s if _BARE_KEY.match(s) else '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'
            out.append(("." if out else "") + seg)
    return "".join(out)


def _units_yaml(path: Path, ctx: _Ctx):
    docs = _yaml_cached(_stat_key(path))
    for di, d in enumerate(docs):
        def mk(p, di=di):
            loc = {"kind": "yaml_path", "path": yaml_path_str(p)}
            if len(docs) > 1:
                loc["doc_index"] = di
            return loc
        yield from _tree_units(d, [], mk, ".")


def _units_xml(path: Path, ctx: _Ctx):
    key = _stat_key(path)
    try:
        tree = _xml_stripped_cached(key)
    except etree.XMLSyntaxError:
        yield from _units_text(path, ctx)
        return

    def walk(el):
        t = _xml_element_text(el)
        if not t.strip():
            return
        if len(t) <= JSON_UNIT_CHARS or len(el) == 0:
            yield {"kind": "xml_xpath", "xpath": tree.getpath(el)}, t
            return
        own = " ".join(x.strip() for x in [el.text or ""] + [c.tail or "" for c in el] if x.strip())
        own_attrs = "\n".join(f"{etree.QName(a).localname}={v}" for a, v in el.attrib.items())
        if own or own_attrs:
            yield {"kind": "xml_xpath", "xpath": tree.getpath(el)}, "\n".join(x for x in (own, own_attrs) if x)
        for c in el:
            if isinstance(c.tag, str):
                yield from walk(c)

    yield from walk(tree.getroot())
    for k, cm in enumerate(tree.getroot().xpath("//comment()"), 1):
        if (cm.text or "").strip():
            yield {"kind": "xml_xpath", "xpath": f"(//comment())[{k}]"}, cm.text


_HTML_UNIT = {"p", "li", "td", "th", "h1", "h2", "h3", "h4", "h5", "h6", "pre", "dt", "dd", "caption",
              "figcaption", "blockquote", "title", "label", "button", "summary", "address", "option"}


def _units_html(path: Path, ctx: _Ctx):
    tree = _html_cached(_stat_key(path))
    root = tree.getroot()
    if root is None:
        return
    for el in root.iter():
        if not isinstance(el.tag, str):
            continue
        tag = el.tag.lower()
        if tag in _HTML_SKIP or any(isinstance(a.tag, str) and a.tag.lower() in _HTML_SKIP for a in el.iterancestors()):
            continue
        in_unit = any(isinstance(a.tag, str) and a.tag.lower() in _HTML_UNIT for a in el.iterancestors())
        if tag in _HTML_UNIT and not in_unit:
            t = html_text(el)
            if t.strip():
                yield {"kind": "html_xpath", "xpath": tree.getpath(el)}, t
        elif not in_unit and tag not in _HTML_UNIT:
            own = " ".join(x.strip() for x in [el.text or ""] + [c.tail or "" for c in el] if x.strip())
            if own:
                yield {"kind": "html_xpath", "xpath": tree.getpath(el)}, own
        for attr in ("alt", "title"):
            if el.get(attr) and el.get(attr).strip():
                yield {"kind": "html_xpath", "xpath": f"{tree.getpath(el)}/@{attr}"}, el.get(attr)
        if tag == "meta" and el.get("content") and el.get("name"):
            yield {"kind": "html_xpath", "xpath": f"{tree.getpath(el)}/@content"}, el.get("content")
    for k, cm in enumerate(root.xpath("//comment()"), 1):
        if (cm.text or "").strip():
            yield {"kind": "html_xpath", "xpath": f"(//comment())[{k}]"}, cm.text


def _window_units(lines_iter, make_loc: Callable[[int, int], dict]):
    buf, start = [], 1
    for i, ln in enumerate(lines_iter, 1):
        buf.append(ln.rstrip("\r\n"))
        if len(buf) == TEXT_WINDOW:
            t = "\n".join(buf)
            if t.strip():
                yield make_loc(start, i), t
            buf, start = [], i + 1
    if buf:
        t = "\n".join(buf)
        if t.strip():
            yield make_loc(start, start + len(buf) - 1), t


def _units_text(path: Path, ctx: _Ctx):
    if path.suffix.lower() in DERIVED_TEXT_EXTS:
        lines: Any = derived_text(path).splitlines()
        yield from _window_units(lines, lambda s, e: {"kind": "text_lines", "start": s, "end": e})
        return
    with open(path, encoding=_detect_encoding(path), errors="replace", newline="") as fh:
        yield from _window_units(fh, lambda s, e: {"kind": "text_lines", "start": s, "end": e})


def _units_image(path: Path, ctx: _Ctx):
    if ctx.ocr:
        try:
            t = ocr_image_file(path)
        except LocatorError:
            return
        if t.strip():
            yield {"kind": "image_ocr"}, t


def _units_zip(path: Path, ctx: _Ctx, depth: int = 0):
    z = _zip(path)
    names = z.namelist()
    yield {"kind": "zip_member"}, "\n".join(names)
    for name in names:
        if name.endswith("/") or depth > 1:
            continue
        try:
            inner = extract_zip_member(path, name)
        except LocatorError:
            continue
        try:
            for loc, t in iter_units(inner, ocr=ctx.ocr, _depth=depth + 1):
                yield {"kind": "zip_member", "member": name, "inner": loc}, t
        except Exception:
            continue


def _units_code(path: Path, variant: str, relpath: str, ctx: _Ctx):
    if _looks_binary(path):
        return
    with open(path, encoding=_detect_encoding(path), errors="replace", newline="") as fh:
        yield from _window_units(fh, lambda s, e: {"kind": "code_lines", "variant": variant, "path": relpath,
                                                   "start": s, "end": e})


def iter_code_units(path: os.PathLike | str, variant: str, relpath: str) -> Iterator[tuple[dict, str]]:
    """code_lines windows for a file inside a generated code repo."""
    yield from _units_code(Path(path), variant, relpath, _Ctx(repo_root=ROOT))


def iter_git_units(repo: Path, variant: str):
    """One unit per commit of a generated repo (git_commit locators keyed by the subject line)."""
    for c in git_log(repo):
        subject = c["message"].splitlines()[0] if c["message"] else ""
        yield {"kind": "git_commit", "variant": variant, "message_contains": subject, "sha": c["sha"][:12]}, \
            format_commit(c)


def _code_location(path: Path, repo_root: Path) -> tuple[str, str] | None:
    """(variant letter, path inside repo) if ``path`` is inside a generated code repo."""
    root = code_repo_root(repo_root).resolve()
    try:
        rel = path.resolve().relative_to(root)
    except ValueError:
        return None
    parts = rel.parts
    if len(parts) < 2 or not parts[0].startswith("variant_") or parts[1] == ".git":
        return None
    return parts[0][len("variant_"):], "/".join(parts[1:])


_EXTRACTORS: dict[str, Callable] = {
    ".docx": _units_docx, ".doc": _units_docx, ".pptx": _units_pptx, ".xlsx": _units_xlsx,
    ".xlsm": _units_xlsx, ".pdf": _units_pdf, ".csv": _units_csv, ".json": _units_json,
    ".jsonl": _units_json, ".yaml": _units_yaml, ".yml": _units_yaml, ".html": _units_html,
    ".htm": _units_html, ".xhtml": _units_html, ".zip": _units_zip,
}
for _e in XML_EXTS:
    _EXTRACTORS[_e] = _units_xml
for _e in IMAGE_EXTS:
    _EXTRACTORS[_e] = _units_image
for _e in DERIVED_TEXT_EXTS | {".txt", ".md", ".markdown", ".log", ".tsv"}:
    _EXTRACTORS[_e] = _units_text


def iter_units(file_path: os.PathLike | str, ocr: bool = True, repo_root: os.PathLike | str = ROOT,
               _depth: int = 0) -> Iterator[tuple[dict, str]]:
    """Stream (locator, text) for every textual unit of a file. Locators round-trip via resolve()."""
    repo_root = Path(repo_root)
    path = _abs_path(file_path, repo_root)
    ctx = _Ctx(repo_root=repo_root, ocr=ocr)
    code = _code_location(path, repo_root)
    if code:
        yield from _units_code(path, code[0], code[1], ctx)
        return
    ext = path.suffix.lower()
    fn = _EXTRACTORS.get(ext)
    if fn is _units_zip:
        yield from _units_zip(path, ctx, _depth)
    elif fn is not None:
        if fn in (_units_json, _units_yaml):
            try:
                yield from fn(path, ctx)
            except LocatorError:  # unparsable: fall back to lines
                yield from _units_text(path, ctx)
        else:
            yield from fn(path, ctx)
    elif not _looks_binary(path):
        yield from _units_text(path, ctx)


def extract_all(file_path: os.PathLike | str, ocr: bool = True,
                repo_root: os.PathLike | str = ROOT) -> list[tuple[dict, str]]:
    """Every textual unit of a file as (locator, text); see iter_units for the streaming form."""
    return list(iter_units(file_path, ocr=ocr, repo_root=repo_root))


# ---------------------------------------------------------------------------------------------
# OCR jobs (so build_index can parallelise OCR at page/image granularity)
# ---------------------------------------------------------------------------------------------

def ocr_jobs(file_path: os.PathLike | str, repo_root: os.PathLike | str = ROOT) -> list[tuple]:
    """Uncached OCR work a file needs: ("pdf_page", path, page) / ("image", path) / ("zip_member", path, name)."""
    path = _abs_path(file_path, Path(repo_root))
    ext = path.suffix.lower()
    jobs: list[tuple] = []
    try:
        if ext == ".pdf":
            doc = _pdf(path)
            for i in range(doc.page_count):
                if pdf_page_needs_ocr(doc[i]) and _ocr_cache_get(_pdf_page_key(path, i + 1, OCR_DPI)) is None:
                    jobs.append(("pdf_page", str(path), i + 1))
        elif ext in IMAGE_EXTS:
            if _ocr_cache_get(f"img:{file_sha1(path)}:{OCR_ENGINE}") is None:
                jobs.append(("image", str(path)))
        elif ext in (".docx", ".pptx"):
            z = _zip(path)
            prefix = "word/media/" if ext == ".docx" else "ppt/media/"
            for name in z.namelist():
                if name.startswith(prefix) and posixpath.splitext(name)[1].lower() in IMAGE_EXTS:
                    data_sha = hashlib.sha1(z.read(name)).hexdigest()
                    if _ocr_cache_get(f"img:{data_sha}:{OCR_ENGINE}") is None:
                        jobs.append(("zip_member", str(path), name))
    except Exception:
        return jobs
    return jobs


def run_ocr_job(job: tuple) -> tuple[tuple, str | None]:
    """Execute one OCR job (results land in the OCR cache). Returns (job, error or None)."""
    try:
        kind, p = job[0], Path(job[1])
        if kind == "pdf_page":
            ocr_pdf_page(p, int(job[2]))
        elif kind == "image":
            ocr_image_file(p)
        elif kind == "zip_member":
            ocr_image_bytes(zipfile.ZipFile(p).read(job[2]))
        return job, None
    except Exception as exc:  # report, never crash the pool
        return job, f"{type(exc).__name__}: {exc}"


# ---------------------------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Resolve a locator or dump every textual unit of a file.")
    ap.add_argument("file", help="file path (relative paths are taken from the repo root)")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--locator", help="locator as JSON, e.g. '{\"kind\": \"pdf_page\", \"page\": 3}'")
    g.add_argument("--all", action="store_true", help="dump every unit as JSONL")
    ap.add_argument("--needle", help="with --locator: report whether the needle matches")
    ap.add_argument("--meta", action="store_true", help="with --locator: print metadata to stderr")
    ap.add_argument("--no-ocr", action="store_true", help="never run OCR (cached results still used)")
    ap.add_argument("--code-repo-root", help="directory holding variant_<x>/ code repos")
    args = ap.parse_args(argv)
    if args.code_repo_root:
        set_code_repo_root(args.code_repo_root)
    path = _abs_path(args.file, ROOT) if args.file not in ("-", "") else None
    if args.all:
        for loc, text in iter_units(path, ocr=not args.no_ocr):
            print(json.dumps({"file": rel_path(path), "locator": loc, "text": text}, ensure_ascii=False))
        return 0
    try:
        loc = json.loads(args.locator)
        res = resolve_ex(path, loc, ocr=not args.no_ocr)
    except (LocatorError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(res.text)
    if args.meta:
        print(json.dumps(res.meta, ensure_ascii=False, default=str), file=sys.stderr)
    if args.needle:
        mode = "ocr_fuzzy" if locator_needs_ocr(loc) else "exact"
        ok = match(args.needle, res.text, mode)
        if not ok and res.fallback and match(args.needle, res.fallback, mode):
            print("MATCH (fallback window only)", file=sys.stderr)
            return 0
        print("MATCH" if ok else "NO MATCH", file=sys.stderr)
        return 0 if ok else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

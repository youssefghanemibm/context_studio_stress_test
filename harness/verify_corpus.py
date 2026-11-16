#!/usr/bin/env python
"""Automated verification pass over the facts manifests, questions and corpus.

Checks (each reports PASS / WARN / FAIL / SKIP items; the exit code is 1 on any FAIL):
    1 facts        every manifests/*.facts.yaml entry validates, its file exists, and its
                   needle matches the text resolved at its locator
    2 questions    questions/questions.yaml: required fields, categories, unique ids,
                   evidence resolves (fact_id or inline locator + needle)
    3 exclusivity  exclusive facts' needles appear in no other file (index search)
    4 inventory    counts per extension/family, accepted types present, size caps,
                   writes manifests/files.csv
    5 rejected     corpus/rejected holds every rejected-format extension
    6 denylist     no denylisted names or forbidden terms (local list) anywhere in the corpus
    7 secrets      no secret-looking strings
    8 guardrail    fake-PII patterns only under corpus/upload/guardrail/; the injection
                   marker appears in exactly one file
    9 batches      batches/order_A.csv and order_B.csv cover the upload set within limits

    python -I harness/verify_corpus.py [--family NAME] [--checks 1,3] [--no-ocr] [--quick]
                                       [--json report.json] [--max-files N] [--max-mb M]

Generators self-checking one family: ``--family <name> --checks 1,3``.
"""
from __future__ import annotations

import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import argparse
import collections
import concurrent.futures as cf
import csv
import json
import math
import multiprocessing
import os
import re
import shutil
import time
import zipfile
from typing import Any, Callable

import yaml

from harness import extract as X
from harness import build_index as B

Path = pathlib.Path

PDF_CACHE = ROOT / "build" / "cache" / "pdf"
REPO_ROOT = MANIFESTS = UPLOAD = REJECTED = QUESTIONS = QUESTION_PARTS = CATEGORIES_MD = DENYLIST = BATCHES = ROOT


def set_root(root: os.PathLike | str) -> None:
    """Point every check at a corpus root (the repo root by default; --root for copies/tests).

    Manifest and question file paths, index keys and batch paths are relative to this root.
    """
    global REPO_ROOT, MANIFESTS, UPLOAD, REJECTED, QUESTIONS, QUESTION_PARTS, CATEGORIES_MD, DENYLIST, BATCHES
    REPO_ROOT = Path(root).resolve()
    MANIFESTS = REPO_ROOT / "manifests"
    UPLOAD = REPO_ROOT / "corpus" / "upload"
    REJECTED = REPO_ROOT / "corpus" / "rejected"
    QUESTIONS = REPO_ROOT / "questions" / "questions.yaml"
    QUESTION_PARTS = REPO_ROOT / "questions" / "parts"
    CATEGORIES_MD = REPO_ROOT / "questions" / "CATEGORIES.md"
    DENYLIST = REPO_ROOT / "world" / "data" / "names_denylist.yaml"
    BATCHES = REPO_ROOT / "batches"


set_root(ROOT)
GUARDRAIL_PREFIX = "corpus/upload/guardrail/"

CHECKS = {0: "index", 1: "facts", 2: "questions", 3: "exclusivity", 4: "inventory", 5: "rejected",
          6: "denylist", 7: "secrets", 8: "guardrail", 9: "batches"}
STATUSES = ("PASS", "WARN", "FAIL", "SKIP")

ACCEPTED_EXT = [".docx", ".doc", ".md", ".xlsx", ".txt", ".json", ".csv", ".pdf", ".pptx", ".xml",
                ".html", ".yaml", ".yml"]
REJECTED_EXT = [".vsdx", ".bpmn", ".msg", ".eml", ".rtf", ".odt", ".png", ".jpg", ".svg", ".zip"]
MAX_FILE_BYTES = 48 * 1000 * 1000
FAMILY_PREFIX = {"long_docs": "LD", "visuals": "VS", "structured": "ST", "text": "TX", "guardrail": "GP"}
NAME_RE = re.compile(r"^(LD|VS|ST|TX|GP|RJ)\d{3}_[a-z0-9_]{1,60}\.[a-z]+$")

# Terms that must never appear in the corpus (e.g. internal product names). The list is kept out
# of the committed repo: one term per line in local/forbidden_terms.txt (gitignored), and/or
# ';'-separated in $CORPUS_FORBIDDEN_TERMS.
FORBIDDEN_TERMS_FILE = ROOT / "local" / "forbidden_terms.txt"


def load_forbidden_terms(path: Path | None = None) -> list[str]:
    terms = [t.strip() for t in os.environ.get("CORPUS_FORBIDDEN_TERMS", "").split(";") if t.strip()]
    path = Path(path) if path else FORBIDDEN_TERMS_FILE
    if path.exists():
        terms += [ln.strip() for ln in path.read_text(encoding="utf-8").splitlines()
                  if ln.strip() and not ln.lstrip().startswith("#")]
    return sorted(set(terms), key=str.lower)

FACT_KINDS = {
    "needle", "definition", "use_of_definition", "split_boundary", "multipage_table", "visual_only",
    "arrow_only", "lane_only", "chart_only", "image_text", "image_table", "screenshot", "speaker_notes",
    "alt_text", "comment", "tracked_insert", "tracked_delete", "header", "footer", "footnote",
    "hidden_sheet", "merged_cell", "contradiction_old", "contradiction_new", "draft", "approved",
    "alias_use", "terminology", "temporal", "aggregate_source", "code_fact", "commit_fact", "canary",
    "resync_change", "pii_probe", "injection_probe", "rejected_format_fact", "scale", "general",
}
FACT_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*-F\d{3,}$")
# required locator fields: each tuple lists alternatives (any one suffices)
LOCATOR_REQUIRED: dict[str, list[tuple[str, ...]]] = {
    "pdf_page": [("page",)], "docx_para": [("para_index", "section")], "docx_table": [("table_index",)],
    "docx_comment": [("comment_id",)], "docx_footnote": [("footnote_id",)],
    "docx_endnote": [("endnote_id", "footnote_id")], "docx_header": [("section_index",)],
    "docx_footer": [("section_index",)], "docx_tracked": [("type",), ("index", "id")],
    "docx_image": [("image_name",)], "docx_alt_text": [("image_index",)], "pptx_slide": [("slide",)],
    "xlsx_cell": [("sheet",), ("cell",)], "xlsx_chart": [("sheet",)], "csv_row": [("row",)],
    "json_pointer": [("pointer",)], "xml_xpath": [("xpath",)], "yaml_path": [("path",)],
    "html_xpath": [("xpath",)], "text_lines": [("start",)], "image_ocr": [],
    "code_lines": [("variant",), ("path",), ("start",)], "git_commit": [("variant", "repo"), ("message_contains", "sha")],
    "zip_member": [],
}
_TEXTISH = {".txt", ".md", ".markdown", ".log", ".csv", ".json", ".yaml", ".yml", ".xml", ".html", ".htm",
            ".svg", ".bpmn", ".tsv"} | X.DERIVED_TEXT_EXTS
LOCATOR_EXTS: dict[str, set[str]] = {
    "pdf_page": {".pdf"}, "pptx_slide": {".pptx"}, "xlsx_cell": {".xlsx", ".xlsm"},
    "xlsx_chart": {".xlsx", ".xlsm"}, "csv_row": {".csv", ".tsv"}, "json_pointer": {".json", ".jsonl"},
    "xml_xpath": X.XML_EXTS, "yaml_path": {".yaml", ".yml"}, "html_xpath": X.HTML_EXTS,
    "text_lines": _TEXTISH, "image_ocr": X.IMAGE_EXTS, "zip_member": {".zip"},
}
for _k in ("docx_para", "docx_table", "docx_comment", "docx_footnote", "docx_endnote", "docx_header",
           "docx_footer", "docx_tracked", "docx_image", "docx_alt_text"):
    LOCATOR_EXTS[_k] = {".docx", ".doc"}
CODE_KINDS = {"code_lines", "git_commit"}

# fact kind -> predicate on the locator (mismatch is a WARN: the manifest may be mislabelled)
KIND_LOCATOR_RULES: dict[str, Callable[[dict], bool]] = {
    "speaker_notes": lambda l: l["kind"] == "pptx_slide" and l.get("where") == "notes",
    "alt_text": lambda l: l["kind"] in ("docx_alt_text", "html_xpath") or
    (l["kind"] == "pptx_slide" and l.get("where") == "alt_text"),
    "comment": lambda l: l["kind"] == "docx_comment",
    "tracked_insert": lambda l: l["kind"] == "docx_tracked" and l.get("type") == "ins",
    "tracked_delete": lambda l: l["kind"] == "docx_tracked" and l.get("type") == "del",
    "header": lambda l: l["kind"] == "docx_header",
    "footer": lambda l: l["kind"] == "docx_footer",
    "footnote": lambda l: l["kind"] in ("docx_footnote", "docx_endnote"),
    "hidden_sheet": lambda l: l["kind"] == "xlsx_cell",
    "merged_cell": lambda l: l["kind"] == "xlsx_cell",
    "chart_only": lambda l: l["kind"] == "xlsx_chart" or (l["kind"] == "pptx_slide" and l.get("where") == "chart"),
    "arrow_only": lambda l: l["kind"] == "pptx_slide" and l.get("where") == "connector",
    "image_text": X.locator_needs_ocr, "image_table": X.locator_needs_ocr, "screenshot": X.locator_needs_ocr,
    "code_fact": lambda l: l["kind"] == "code_lines",
    "commit_fact": lambda l: l["kind"] == "git_commit",
}

Q_REQUIRED = ["id", "category", "question", "expected_answer", "must_include", "evidence", "hops",
              "ask_mode", "difficulty"]
ASK_MODES = {"chat", "graph", "vector"}
DIFFICULTIES = {"easy", "medium", "hard"}

SECRET_PATTERNS = [
    ("aws_access_key", r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b"),
    ("pem_block", r"-{5}BEGIN"),
    ("github_token", r"\bgh[pousr]_[A-Za-z0-9]{20,}"),
    ("github_pat", r"\bgithub_pat_[A-Za-z0-9_]{20,}"),
    ("slack_token", r"\bxox[abprs]-[A-Za-z0-9-]{10,}"),
    ("jwt", r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"),
]
HIGH_ENTROPY_RE = r"(?<![A-Za-z0-9+/=_-])[A-Za-z0-9+/_-]{40,}={0,2}(?![A-Za-z0-9+/=_-])"
STRONG_PII = [
    ("example_com_person_email", r"\b[A-Za-z]+(?:[._-][A-Za-z]+)+@example\.com\b", re.IGNORECASE),
    ("ni_number_like", r"\bQQ ?\d{2} ?\d{2} ?\d{2} ?[A-D]\b", 0),
    ("ssn_like_9xx", r"\b9\d{2}-\d{2}-\d{4}\b", 0),
]
WEAK_PII = [("phone_555", r"(?<!\d)(?:\(?\d{3}\)?[-. ]?)?555[-. ]\d{4}(?!\d)", 0)]


# ---------------------------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------------------------

class Report:
    def __init__(self) -> None:
        self.items: dict[int, list[dict]] = {k: [] for k in CHECKS}

    def add(self, check: int, status: str, msg: str, **ctx: Any) -> None:
        assert status in STATUSES
        self.items[check].append({"status": status, "msg": msg, **ctx})

    def counts(self, check: int) -> dict[str, int]:
        c = collections.Counter(i["status"] for i in self.items[check])
        return {s: c.get(s, 0) for s in STATUSES}

    def failed(self) -> bool:
        return any(i["status"] == "FAIL" for items in self.items.values() for i in items)

    def print(self, selected: list[int], verbose: bool, max_warn: int = 25) -> None:
        print()
        print(f"{'check':<16}{'PASS':>7}{'WARN':>7}{'FAIL':>7}{'SKIP':>7}")
        print("-" * 44)
        for k in [0] + selected:
            if k == 0 and not self.items[0]:
                continue
            c = self.counts(k)
            print(f"{k} {CHECKS[k]:<14}{c['PASS']:>7}{c['WARN']:>7}{c['FAIL']:>7}{c['SKIP']:>7}")
        for k in [0] + selected:
            fails = [i for i in self.items[k] if i["status"] == "FAIL"]
            warns = [i for i in self.items[k] if i["status"] == "WARN"]
            skips = [i for i in self.items[k] if i["status"] == "SKIP"]
            if fails:
                print(f"\n== FAIL details: {k} {CHECKS[k]} ({len(fails)})")
                for i in fails:
                    print(f"  FAIL {i['msg']}")
            if warns:
                shown = warns if verbose else warns[:max_warn]
                print(f"\n== WARN: {k} {CHECKS[k]} ({len(warns)})")
                for i in shown:
                    print(f"  WARN {i['msg']}")
                if len(shown) < len(warns):
                    print(f"  ... {len(warns) - len(shown)} more (use --verbose)")
            for i in skips:
                print(f"  SKIP {k} {CHECKS[k]}: {i['msg']}")

    def to_json(self) -> dict:
        return {"summary": {CHECKS[k]: self.counts(k) for k in CHECKS},
                "items": {CHECKS[k]: v for k, v in self.items.items()},
                "failed": self.failed()}


# ---------------------------------------------------------------------------------------------
# Manifests and facts (check 1)
# ---------------------------------------------------------------------------------------------

def load_manifests() -> tuple[list[dict], list[str]]:
    facts, errors = [], []
    for f in sorted(MANIFESTS.glob("*.facts.yaml")):
        try:
            data = yaml.safe_load(f.read_text(encoding="utf-8")) or []
        except yaml.YAMLError as exc:
            errors.append(f"{f.name}: invalid YAML: {exc}")
            continue
        if not isinstance(data, list):
            errors.append(f"{f.name}: top level must be a list")
            continue
        for k, e in enumerate(data):
            if not isinstance(e, dict):
                errors.append(f"{f.name}[{k}]: entry is not a mapping")
                continue
            e["_manifest"] = f.name
            facts.append(e)
    return facts, errors


def family_manifest(name: str) -> str:
    """Manifest file name for --family (accepts the folder name or the file-id prefix)."""
    if (MANIFESTS / f"{name}.facts.yaml").exists():
        return f"{name}.facts.yaml"
    by_prefix = {v: k for k, v in FAMILY_PREFIX.items()}
    if name.upper() in by_prefix and (MANIFESTS / f"{by_prefix[name.upper()]}.facts.yaml").exists():
        return f"{by_prefix[name.upper()]}.facts.yaml"
    return f"{name}.facts.yaml"


def validate_fact(e: dict) -> list[str]:
    """Schema problems of one manifest entry (CONVENTIONS §5)."""
    errs = []
    for k in ("fact_id", "kind", "statement", "file", "locator", "needle"):
        if k not in e or e[k] in (None, ""):
            errs.append(f"missing {k}")
    if errs:
        return errs
    if not isinstance(e["fact_id"], str) or not FACT_ID_RE.match(e["fact_id"]):
        errs.append(f"fact_id {e['fact_id']!r} not of the form <FILEID>-F<nnn>")
    if e["kind"] not in FACT_KINDS:
        errs.append(f"unknown kind {e['kind']!r}")
    for k in ("statement", "file", "needle"):
        if not isinstance(e[k], str) or not e[k].strip():
            errs.append(f"{k} must be a non-empty string")
    if isinstance(e.get("file"), str) and (e["file"].startswith("/") or ".." in Path(e["file"]).parts):
        errs.append("file must be a repo-relative path")
    if "exclusive" in e and not isinstance(e["exclusive"], bool):
        errs.append("exclusive must be a boolean")
    if "also_in" in e and not (isinstance(e["also_in"], list) and all(isinstance(x, str) for x in e["also_in"])):
        errs.append("also_in must be a list of fact_ids")
    if e.get("world_ref") is not None and not isinstance(e["world_ref"], str):
        errs.append("world_ref must be a string or null")
    loc = e["locator"]
    if not isinstance(loc, dict) or "kind" not in loc:
        errs.append("locator must be a mapping with a kind")
        return errs
    lk = loc["kind"]
    if lk not in LOCATOR_REQUIRED:
        errs.append(f"unknown locator kind {lk!r}")
        return errs
    for alts in LOCATOR_REQUIRED[lk]:
        if not any(a in loc and loc[a] is not None for a in alts):
            errs.append(f"locator {lk} missing {'/'.join(alts)}")
    if lk == "pptx_slide" and loc.get("where", "text") not in X.PPTX_WHERES:
        errs.append(f"pptx_slide where must be one of {X.PPTX_WHERES}")
    if lk == "docx_tracked" and loc.get("type") not in ("ins", "del"):
        errs.append("docx_tracked type must be ins or del")
    if lk in LOCATOR_EXTS and isinstance(e.get("file"), str):
        ext = Path(e["file"]).suffix.lower()
        if ext not in LOCATOR_EXTS[lk]:
            errs.append(f"locator kind {lk} does not fit a {ext or 'extensionless'} file")
    return errs


def _resolve_and_match(file: str, loc: dict, needle: str, ocr_mode: str) -> tuple[str, str, X.Resolved | None]:
    """(status, message, resolved) for one needle at one locator."""
    needs_ocr = X.locator_needs_ocr(loc)
    try:
        res = X.resolve_ex(file, loc, repo_root=REPO_ROOT, ocr=(ocr_mode == "full"))
    except X.OcrUnavailable:
        return "WARN", "not verified: needs OCR and none cached (--no-ocr/--quick)", None
    except X.LocatorError as exc:
        return "FAIL", f"locator does not resolve: {exc}", None
    except Exception as exc:  # resolver bug or broken file: report, keep going
        return "FAIL", f"resolver error {type(exc).__name__}: {exc}", None
    mode = "ocr_fuzzy" if needs_ocr else "exact"
    if X.match(needle, res.text, mode):
        return "PASS", "", res
    if res.fallback and X.match(needle, res.fallback, mode):
        return "WARN", "needle not at the exact locator, but found in the section window", res
    errs, snip = X.best_snippet(needle, res.text)
    shown = X.normalize(res.text)[:160]
    return "FAIL", (f"needle {needle!r} not found ({mode}); closest window ({errs} edits): {snip[:120]!r}; "
                    f"resolved {len(res.text)} chars: {shown!r}"), res


def verify_fact(e: dict, ocr_mode: str) -> dict:
    """Validate and verify one manifest entry. Returns {fact_id, status, msg, file}."""
    fid = e.get("fact_id", "?")
    out = {"fact_id": fid, "file": e.get("file"), "manifest": e.get("_manifest")}
    errs = validate_fact(e)
    if errs:
        return dict(out, status="FAIL", msg=f"{fid}: schema: " + "; ".join(errs))
    loc, file = e["locator"], e["file"]
    if loc["kind"] not in CODE_KINDS and not (REPO_ROOT / file).exists():
        return dict(out, status="FAIL", msg=f"{fid}: file not found: {file}")
    if loc["kind"] in CODE_KINDS:
        vd = Path(loc["repo"]) if loc.get("repo") else X.variant_dir(loc.get("variant", "a"), REPO_ROOT)
        if not vd.exists():
            return dict(out, status="FAIL", msg=f"{fid}: code repo not found: {vd}")
    status, msg, res = _resolve_and_match(file, loc, e["needle"], ocr_mode)
    notes = []
    if res is not None and status != "FAIL":
        meta = res.meta
        if loc.get("hidden") is True and not meta.get("hidden"):
            status, msg = "FAIL", "locator says hidden but the sheet, row and column are all visible"
        elif e["kind"] == "hidden_sheet" and loc["kind"] == "xlsx_cell" and not meta.get("hidden"):
            status, msg = "FAIL", "kind hidden_sheet but the cell is visible"
        elif e["kind"] == "merged_cell" and loc["kind"] == "xlsx_cell" and not meta.get("merged_range"):
            status, msg = "FAIL", "kind merged_cell but the cell is not part of a merged range"
    rule = KIND_LOCATOR_RULES.get(e["kind"])
    if rule is not None and not rule(loc):
        notes.append(f"kind {e['kind']} with a {loc['kind']} locator looks inconsistent")
    if status == "PASS" and notes:
        status, msg = "WARN", "; ".join(notes)
    elif notes:
        msg += " (" + "; ".join(notes) + ")"
    return dict(out, status=status, msg=f"{fid} [{file}]: {msg}" if msg else f"{fid}")


def _verify_group(args: tuple) -> list[dict]:
    facts, ocr_mode, code_root, root = args
    set_root(root)
    if code_root:
        X.set_code_repo_root(code_root)
    return [verify_fact(e, ocr_mode) for e in facts]


def _pool(jobs: int):
    return cf.ProcessPoolExecutor(max_workers=jobs, mp_context=multiprocessing.get_context("spawn"))


def check_facts(report: Report, facts: list[dict], all_facts: list[dict], manifest_errors: list[str],
                ocr_mode: str, jobs: int) -> dict[str, str]:
    for err in manifest_errors:
        report.add(1, "FAIL", err)
    seen: dict[str, str] = {}
    for e in all_facts:
        fid = e.get("fact_id")
        if fid in seen:
            report.add(1, "FAIL", f"duplicate fact_id {fid} in {seen[fid]} and {e.get('_manifest')}")
        elif fid:
            seen[fid] = e.get("_manifest")
    if not facts:
        report.add(1, "SKIP", "no manifest entries selected")
        return {}
    groups: dict[str, list[dict]] = collections.defaultdict(list)
    for e in facts:
        groups[str(e.get("file"))].append(e)
    code_root = str(X.code_repo_root(REPO_ROOT))
    work = [(g, ocr_mode, code_root, str(REPO_ROOT)) for g in groups.values()]
    results: list[dict] = []
    if jobs <= 1 or len(facts) < 40:
        for w in work:
            results.extend(_verify_group(w))
    else:
        with _pool(jobs) as ex:
            for r in ex.map(_verify_group, work):
                results.extend(r)
    status_by_id = {}
    for r in sorted(results, key=lambda r: str(r["fact_id"])):
        report.add(1, r["status"], r["msg"], fact_id=r["fact_id"], file=r["file"])
        status_by_id[str(r["fact_id"])] = r["status"]
    return status_by_id


# ---------------------------------------------------------------------------------------------
# Questions (check 2)
# ---------------------------------------------------------------------------------------------

def load_questions() -> tuple[list | None, str]:
    if QUESTIONS.exists():
        data = yaml.safe_load(QUESTIONS.read_text(encoding="utf-8")) or []
        if isinstance(data, dict):
            data = data.get("questions", [])
        return data, X.rel_path(QUESTIONS, REPO_ROOT)
    parts = sorted(QUESTION_PARTS.glob("*.y*ml")) if QUESTION_PARTS.exists() else []
    if parts:
        out = []
        for p in parts:
            d = yaml.safe_load(p.read_text(encoding="utf-8")) or []
            out.extend(d.get("questions", []) if isinstance(d, dict) else d)
        return out, f"{len(parts)} files in {X.rel_path(QUESTION_PARTS, REPO_ROOT)}"
    return None, ""


def load_categories() -> set[str] | None:
    """Category ids from questions/CATEGORIES.md (table first column, headings, bullets)."""
    if not CATEGORIES_MD.exists():
        return None
    cats = set()
    ident = re.compile(r"^`?([a-z][a-z0-9_]+)`?$")
    for line in CATEGORIES_MD.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if s.startswith("|"):
            cells = [c.strip() for c in s.strip("|").split("|")]
            m = ident.match(cells[0]) if cells else None
            if m and not set(cells[0]) <= set("-: "):
                cats.add(m.group(1))
        elif s.startswith("#"):
            m = ident.match(s.lstrip("#").strip().split(" ")[0])
            if m:
                cats.add(m.group(1))
        else:
            m = re.match(r"^[-*]\s+`([a-z][a-z0-9_]+)`", s)
            if m:
                cats.add(m.group(1))
    cats.discard("category")
    cats.discard("id")
    return cats or None


def check_questions(report: Report, facts_by_id: dict[str, dict], fact_status: dict[str, str], ocr_mode: str) -> None:
    qs, src = load_questions()
    if qs is None:
        report.add(2, "SKIP", "questions/questions.yaml not found")
        return
    if not isinstance(qs, list):
        report.add(2, "FAIL", f"{src}: top level must be a list")
        return
    cats = load_categories()
    if cats is None:
        report.add(2, "WARN", "questions/CATEGORIES.md missing or unparsable: categories not validated")
    ids = collections.Counter(q.get("id") for q in qs if isinstance(q, dict))
    for qid, n in ids.items():
        if n > 1:
            report.add(2, "FAIL", f"duplicate question id {qid} ({n} times)")
    for k, q in enumerate(qs):
        if not isinstance(q, dict):
            report.add(2, "FAIL", f"question #{k} is not a mapping")
            continue
        qid = q.get("id", f"#{k}")
        problems, warns = [], []
        missing = [f for f in Q_REQUIRED if f not in q or q[f] in (None, "", [])]
        if missing:
            problems.append(f"missing {', '.join(missing)}")
        if cats is not None and q.get("category") and q["category"] not in cats:
            problems.append(f"unknown category {q['category']!r}")
        if q.get("ask_mode") and q["ask_mode"] not in ASK_MODES:
            problems.append(f"ask_mode {q['ask_mode']!r} not in {sorted(ASK_MODES)}")
        if q.get("difficulty") and q["difficulty"] not in DIFFICULTIES:
            problems.append(f"difficulty {q['difficulty']!r} not in {sorted(DIFFICULTIES)}")
        if "hops" in q and not (isinstance(q["hops"], int) and q["hops"] >= 1):
            problems.append("hops must be an integer >= 1")
        mi = q.get("must_include")
        if mi is not None and not (isinstance(mi, list) and all(isinstance(g, list) and g and
                                                                 all(isinstance(x, str) for x in g) for g in mi)):
            problems.append("must_include must be a list of lists of strings (AND of ORs)")
        elif isinstance(mi, list):
            answers = " | ".join([str(q.get("expected_answer", ""))] + [str(v) for v in q.get("acceptable_variants") or []])
            for g in mi:
                if isinstance(g, list) and not any(X.match(alt, answers) for alt in g):
                    warns.append(f"must_include group {g} matches neither expected_answer nor variants")
        mni = q.get("must_not_include")
        if mni is not None and not (isinstance(mni, list) and all(isinstance(x, str) for x in mni)):
            problems.append("must_not_include must be a list of strings")
        ev = q.get("evidence")
        if ev is not None and not isinstance(ev, list):
            problems.append("evidence must be a list")
            ev = []
        for j, item in enumerate(ev or []):
            if not isinstance(item, dict):
                problems.append(f"evidence[{j}] is not a mapping")
            elif item.get("fact_id"):
                fid = str(item["fact_id"])
                if fid not in facts_by_id:
                    problems.append(f"evidence[{j}] fact_id {fid} not in any manifest")
                elif fact_status.get(fid) == "FAIL":
                    warns.append(f"evidence fact {fid} failed check 1")
            elif item.get("file") and item.get("locator") and item.get("needle"):
                if not isinstance(item["locator"], dict) or item["locator"].get("kind") not in LOCATOR_REQUIRED:
                    problems.append(f"evidence[{j}] has an invalid locator")
                    continue
                if item["locator"]["kind"] not in CODE_KINDS and not (REPO_ROOT / item["file"]).exists():
                    problems.append(f"evidence[{j}] file not found: {item['file']}")
                    continue
                st, msg, _ = _resolve_and_match(item["file"], item["locator"], item["needle"], ocr_mode)
                if st == "FAIL":
                    problems.append(f"evidence[{j}]: {msg}")
                elif st == "WARN":
                    warns.append(f"evidence[{j}]: {msg}")
            else:
                problems.append(f"evidence[{j}] needs fact_id, or file + locator + needle")
        if problems:
            report.add(2, "FAIL", f"{qid}: " + "; ".join(problems))
        elif warns:
            report.add(2, "WARN", f"{qid}: " + "; ".join(warns))
        else:
            report.add(2, "PASS", str(qid))


# ---------------------------------------------------------------------------------------------
# Exclusivity (check 3)
# ---------------------------------------------------------------------------------------------

_CODE_PATH_RE = re.compile(r"(?:^|/)code_repo/variant_[^/]+/(.*)$")


def file_identity(rel: str) -> str:
    """Same file across code-repo variants counts as one identity."""
    m = _CODE_PATH_RE.search(rel)
    return f"code:{m.group(1)}" if m else rel


def _fact_identity(e: dict) -> str:
    loc = e.get("locator") or {}
    if loc.get("kind") == "code_lines" and loc.get("path"):
        return f"code:{loc['path']}"
    if loc.get("kind") == "git_commit":
        return "code:.git"
    return file_identity(str(e.get("file", "")))


def check_exclusivity(report: Report, facts: list[dict], facts_by_id: dict[str, dict], index_dir: Path) -> None:
    excl = [e for e in facts if e.get("exclusive") is True and isinstance(e.get("needle"), str)]
    if not excl:
        report.add(3, "SKIP", "no exclusive facts selected")
        return
    for e in excl:
        fid, needle = e.get("fact_id"), e["needle"]
        own = _fact_identity(e)
        allowed = {own}
        for ref in e.get("also_in") or []:
            if ref in facts_by_id:
                allowed.add(_fact_identity(facts_by_id[ref]))
            elif "/" in str(ref):
                allowed.add(file_identity(str(ref)))
        hits = B.search(needle, index_dir=index_dir)
        others = [h for h in hits if file_identity(h["file"]) not in allowed]
        n = X.normalize(needle)
        if len(n) < 8 or len(hits) >= 20:
            report.add(3, "WARN", f"{fid}: needle too generic ({len(n)} chars, {len(hits)} hits corpus-wide): {needle!r}")
            continue
        if not others:
            report.add(3, "PASS", f"{fid}")
            continue
        files = sorted({h["file"] for h in others})
        where = "; ".join(f"{h['file']} {json.dumps(h['locator'], ensure_ascii=False)}" for h in others[:5])
        if all(f.startswith("corpus/rejected/") for f in files):
            report.add(3, "WARN", f"{fid}: needle {needle!r} also appears in rejected-format files only: {where}")
        else:
            report.add(3, "FAIL", f"{fid}: exclusive needle {needle!r} also in {len(files)} other file(s): {where}")


# ---------------------------------------------------------------------------------------------
# Inventory (check 4) and rejected set (check 5)
# ---------------------------------------------------------------------------------------------

def docx_pages(path: Path, quick: bool, key: str = "0") -> int | None:
    """Page count of a DOCX/DOC via LibreOffice PDF conversion (cached by sha1)."""
    sha = X.file_sha1(path)
    cache = PDF_CACHE / f"{sha}.pages.json"
    if cache.exists():
        return json.loads(cache.read_text())["pages"]
    if quick:
        try:
            app = zipfile.ZipFile(path).read("docProps/app.xml").decode("utf-8", "replace")
            m = re.search(r"<Pages>(\d+)</Pages>", app)
            return int(m.group(1)) if m else None
        except (KeyError, zipfile.BadZipFile):
            return None
    from generators.common.util import soffice_convert
    PDF_CACHE.mkdir(parents=True, exist_ok=True)
    tmp = PDF_CACHE / f"tmp_{os.getpid()}_{key}"
    try:
        out = soffice_convert(path, "pdf", tmp, profile_key=f"verify_{key}")
        final = PDF_CACHE / f"{sha}.pdf"
        os.replace(out, final)
        import pymupdf
        with pymupdf.open(final) as d:
            pages = d.page_count
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    cache.write_text(json.dumps({"pages": pages, "source": X.rel_path(path, REPO_ROOT)}))
    return pages


def unit_count(path: Path, quick: bool, key: str = "0") -> int | None:
    ext = path.suffix.lower()
    try:
        if ext == ".pdf":
            import pymupdf
            with pymupdf.open(path) as d:
                return d.page_count
        if ext in (".docx", ".doc"):
            return docx_pages(path, quick, key)
        if ext == ".pptx":
            names = zipfile.ZipFile(path).namelist()
            return sum(1 for n in names if re.match(r"ppt/slides/slide\d+\.xml$", n))
        if ext == ".xlsx":
            import openpyxl
            wb = openpyxl.load_workbook(path, read_only=True)
            try:
                return sum((ws.max_row or 0) for ws in wb.worksheets)
            finally:
                wb.close()
        if ext == ".csv":
            return max(0, sum(1 for _ in X.iter_csv(path)) - 1)
        if ext == ".json":
            data = json.loads(X.read_text(path))
            if isinstance(data, list):
                return len(data)
            if isinstance(data, dict):
                lists = [len(v) for v in data.values() if isinstance(v, list)]
                return max(lists) if lists else 1
            return 1
        with open(path, "rb") as fh:
            return sum(1 for _ in fh)
    except Exception:
        return None


def check_inventory(report: Report, quick: bool, max_total_mb: float, jobs: int) -> None:
    files = sorted(p for p in UPLOAD.rglob("*") if p.is_file() and not p.name.startswith(".")) if UPLOAD.exists() else []
    by_ext = collections.Counter(p.suffix.lower() for p in files)
    by_family = collections.Counter(p.relative_to(UPLOAD).parts[0] if len(p.relative_to(UPLOAD).parts) > 1
                                    else "(root)" for p in files)
    total = sum(p.stat().st_size for p in files)
    for ext in ACCEPTED_EXT:
        if by_ext.get(ext, 0) == 0:
            report.add(4, "FAIL", f"no {ext} file in corpus/upload")
    for p in files:
        rel = X.rel_path(p, REPO_ROOT)
        size = p.stat().st_size
        if p.suffix.lower() not in ACCEPTED_EXT:
            report.add(4, "FAIL", f"{rel}: extension {p.suffix} is not an accepted upload type")
        if size >= MAX_FILE_BYTES:
            report.add(4, "FAIL", f"{rel}: {size / 1e6:.1f} MB is not below the {MAX_FILE_BYTES / 1e6:.0f} MB cap")
        if not NAME_RE.match(p.name):
            report.add(4, "WARN", f"{rel}: name does not follow <PREFIX><NNN>_<slug>.<ext>")
        else:
            fam = p.relative_to(UPLOAD).parts[0]
            if fam in FAMILY_PREFIX and not p.name.startswith(FAMILY_PREFIX[fam]):
                report.add(4, "WARN", f"{rel}: prefix does not match family folder {fam}")
    if total > max_total_mb * 1e6:
        report.add(4, "FAIL", f"upload corpus is {total / 1e6:.1f} MB, above {max_total_mb:.0f} MB")

    t0 = time.time()
    counts: dict[Path, int | None] = {}
    with cf.ThreadPoolExecutor(max_workers=max(1, min(4, jobs))) as ex:
        futs = {ex.submit(unit_count, p, quick, str(k % 4)): p for k, p in enumerate(files)}
        for fut in cf.as_completed(futs):
            counts[futs[fut]] = fut.result()
    MANIFESTS.mkdir(parents=True, exist_ok=True)
    out = MANIFESTS / "files.csv"
    with open(out, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["path", "family", "ext", "bytes", "pages_or_slides_or_rows", "sha1"])
        for p in files:
            rp = p.relative_to(UPLOAD).parts
            w.writerow([X.rel_path(p, REPO_ROOT), rp[0] if len(rp) > 1 else "", p.suffix.lower(), p.stat().st_size,
                        "" if counts.get(p) is None else counts[p], X.file_sha1(p)])
    summary = (f"{len(files)} files, {total / 1e6:.1f} MB; per ext: "
               + ", ".join(f"{e}={n}" for e, n in sorted(by_ext.items()))
               + "; per family: " + ", ".join(f"{f}={n}" for f, n in sorted(by_family.items()))
               + f"; wrote {X.rel_path(out, REPO_ROOT)} ({time.time() - t0:.0f}s)")
    report.add(4, "PASS", summary)
    missing_counts = [X.rel_path(p, REPO_ROOT) for p in files if counts.get(p) is None]
    if missing_counts:
        report.add(4, "WARN", f"no page/slide/row count for {len(missing_counts)} file(s): {missing_counts[:5]}")


def check_rejected(report: Report) -> None:
    files = [p for p in REJECTED.rglob("*") if p.is_file() and not p.name.startswith(".")] if REJECTED.exists() else []
    exts = collections.Counter(".jpg" if p.suffix.lower() == ".jpeg" else p.suffix.lower() for p in files)
    for ext in REJECTED_EXT:
        if exts.get(ext, 0) == 0:
            report.add(5, "FAIL", f"no {ext} file in corpus/rejected")
        else:
            report.add(5, "PASS", f"{ext}: {exts[ext]} file(s)")
    for p in files:
        if p.suffix.lower() in ACCEPTED_EXT:
            report.add(5, "WARN", f"{X.rel_path(p, REPO_ROOT)} has an accepted upload extension")


# ---------------------------------------------------------------------------------------------
# Denylist (6), secrets (7), guardrail (8)
# ---------------------------------------------------------------------------------------------

_META_KEYS = {"reason", "reasons", "note", "notes", "why", "category", "comment", "comments", "description",
              "source", "type", "added", "added_by", "date", "status"}


def load_denylist(path: Path) -> list[str]:
    """Every name-like string in the denylist YAML (metadata keys such as 'reason' ignored)."""
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    out: list[str] = []
    # Structured form: {entries: [{name, aliases?, kind, match}], invented_name_checks: [...], notes}.
    # Only the real names under 'entries' are denylisted; invented-name spot checks and notes are not.
    if isinstance(data, dict) and isinstance(data.get("entries"), list):
        for e in data["entries"]:
            if isinstance(e, str):
                names = [e]
            elif isinstance(e, dict):
                names = [e.get("name")] + list(e.get("aliases") or [])
            else:
                names = []
            out.extend(n.strip() for n in names if isinstance(n, str) and len(n.strip()) >= 3)
        return sorted(set(out), key=lambda s: (-len(s), s.lower()))

    def walk(v):
        if isinstance(v, str):
            if len(v.strip()) >= 3:
                out.append(v.strip())
        elif isinstance(v, list):
            for x in v:
                walk(x)
        elif isinstance(v, dict):
            for k, x in v.items():
                if str(k).lower() not in _META_KEYS:
                    walk(x)

    walk(data)
    return sorted(set(out), key=lambda s: (-len(s), s.lower()))


def _term_regex(terms: list[str]) -> re.Pattern:
    alts = [re.escape(t).replace(r"\ ", r"\s+") for t in terms]
    return re.compile(r"(?<!\w)(?:" + "|".join(alts) + r")(?!\w)", re.IGNORECASE)


def _grep_terms(report: Report, check: int, terms: list[str], label: str, index_dir: Path) -> None:
    found: dict[str, list[dict]] = collections.defaultdict(list)
    for k in range(0, len(terms), 200):
        batch = terms[k:k + 200]
        lower = {t.lower(): t for t in batch}
        for h in B.search(_term_regex(batch), regex=True, index_dir=index_dir):
            key = re.sub(r"\s+", " ", h["match"]).lower()
            found[lower.get(key, h["match"])].append(h)
    for term, hits in sorted(found.items()):
        where = "; ".join(f"{h['file']} {json.dumps(h['locator'], ensure_ascii=False)}" for h in hits[:5])
        files = len({h["file"] for h in hits})
        report.add(check, "FAIL", f"{label} {term!r} found {len(hits)}x in {files} file(s): {where}")
    if not found:
        report.add(check, "PASS", f"{len(terms)} {label}s checked, none found")


def check_denylist(report: Report, index_dir: Path, terms_file: Path | None = None) -> None:
    if DENYLIST.exists():
        names = load_denylist(DENYLIST)
        if names:
            _grep_terms(report, 6, names, "denylisted name", index_dir)
        else:
            report.add(6, "WARN", f"{X.rel_path(DENYLIST, REPO_ROOT)} contains no names")
    else:
        report.add(6, "SKIP", f"{X.rel_path(DENYLIST, REPO_ROOT)} not found: denylisted names not checked")
    terms = load_forbidden_terms(terms_file)
    if terms:
        _grep_terms(report, 6, terms, "forbidden term", index_dir)
    else:
        report.add(6, "SKIP", f"no forbidden-terms list ({X.rel_path(FORBIDDEN_TERMS_FILE)} or "
                              f"$CORPUS_FORBIDDEN_TERMS): forbidden terms not checked")


def shannon_entropy(s: str) -> float:
    n = len(s)
    return -sum(c / n * math.log2(c / n) for c in collections.Counter(s).values()) if n else 0.0


def _is_high_entropy_secret(tok: str, before: str) -> bool:
    if "base64," in before[-12:]:
        return False
    core = tok.rstrip("=")
    if re.fullmatch(r"[0-9a-fA-F]+", core):
        return False
    if not (re.search(r"[A-Z]", core) and re.search(r"[a-z]", core) and re.search(r"\d", core)):
        return False
    if core.count("/") >= 2 and "+" not in core:  # path-like
        return False
    return shannon_entropy(core) >= 4.5


def _redact(s: str) -> str:
    return s[:6] + "…" if len(s) > 6 else s


def check_secrets(report: Report, index_dir: Path) -> None:
    n = 0
    for name, pat in SECRET_PATTERNS:
        for h in B.search(pat, regex=True, flags=0, index_dir=index_dir):
            n += 1
            report.add(7, "FAIL", f"{name} {_redact(h['match'])!r} in {h['file']} "
                                  f"{json.dumps(h['locator'], ensure_ascii=False)}")
    for h in B.search(HIGH_ENTROPY_RE, regex=True, flags=0, index_dir=index_dir, context=12):
        before = h["snippet"][:max(0, h["snippet"].find(h["match"]))]
        if _is_high_entropy_secret(h["match"], before):
            n += 1
            report.add(7, "FAIL", f"high-entropy string {_redact(h['match'])!r} "
                                  f"(entropy {shannon_entropy(h['match']):.2f}) in {h['file']} "
                                  f"{json.dumps(h['locator'], ensure_ascii=False)}")
    if not n:
        report.add(7, "PASS", "no secret-looking strings in the index")


def check_guardrail(report: Report, all_facts: list[dict], index_dir: Path) -> None:
    def outside(h):
        return not h["file"].startswith(GUARDRAIL_PREFIX)

    strong: dict[str, list[tuple[str, dict]]] = collections.defaultdict(list)
    weak: dict[str, list[tuple[str, dict]]] = collections.defaultdict(list)
    inside_files = set()
    for kinds, store in ((STRONG_PII, strong), (WEAK_PII, weak)):
        for name, pat, flags in kinds:
            for h in B.search(pat, regex=True, flags=flags, index_dir=index_dir):
                if outside(h):
                    store[h["file"]].append((name, h))
                else:
                    inside_files.add(h["file"])
    for f, hs in sorted(strong.items()):
        kinds = collections.Counter(n for n, _ in hs)
        h = hs[0][1]
        report.add(8, "FAIL", f"fake-PII pattern(s) {dict(kinds)} outside {GUARDRAIL_PREFIX}: {f} "
                              f"e.g. {json.dumps(h['locator'], ensure_ascii=False)} {h['match']!r}")
    for f, hs in sorted(weak.items()):
        if f in strong:
            continue
        report.add(8, "WARN", f"{len(hs)} 555-pattern phone number(s) outside {GUARDRAIL_PREFIX}: {f} "
                              f"(allowed for staff numbers; check none is presented as personal data)")
    if not strong:
        report.add(8, "PASS", f"no strong fake-PII pattern outside {GUARDRAIL_PREFIX} "
                              f"({len(inside_files)} guardrail file(s) contain PII patterns)")
    probes = [e for e in all_facts if e.get("kind") == "injection_probe"]
    if not probes:
        report.add(8, "SKIP", "no injection_probe fact in the manifests: injection marker not checked")
        return
    for e in probes:
        marker = e.get("marker") or e.get("needle")
        if not isinstance(marker, str) or not marker.strip():
            report.add(8, "FAIL", f"{e.get('fact_id')}: injection_probe has no marker/needle")
            continue
        files = sorted({h["file"] for h in B.search(marker, index_dir=index_dir)})
        if len(files) == 1 and files[0].startswith(GUARDRAIL_PREFIX):
            report.add(8, "PASS", f"injection marker of {e.get('fact_id')} appears only in {files[0]}")
        elif not files:
            report.add(8, "FAIL", f"injection marker of {e.get('fact_id')} not found in the index")
        else:
            report.add(8, "FAIL", f"injection marker of {e.get('fact_id')} appears in {len(files)} file(s) "
                                  f"(must be exactly one, under {GUARDRAIL_PREFIX}): {files[:10]}")


# ---------------------------------------------------------------------------------------------
# Batches (check 9)
# ---------------------------------------------------------------------------------------------

def load_order(path: Path) -> list[tuple[str, str]]:
    """[(batch id, repo-relative path)] in file order."""
    with open(path, newline="", encoding="utf-8-sig") as fh:
        rdr = csv.DictReader(fh)
        fields = {f.strip().lower(): f for f in (rdr.fieldnames or [])}
        pcol = next((fields[c] for c in ("path", "file", "relpath", "file_path", "filename") if c in fields), None)
        bcol = next((fields[c] for c in ("batch", "batch_id", "batch_no", "batch_index", "batch_number")
                     if c in fields), None)
        if not pcol or not bcol:
            raise ValueError(f"needs a path column and a batch column, got {rdr.fieldnames}")
        rows = []
        for r in rdr:
            p = (r.get(pcol) or "").strip()
            if not p:
                continue
            if (REPO_ROOT / p).exists():
                p = X.rel_path(REPO_ROOT / p, REPO_ROOT)
            elif (UPLOAD / p).exists():
                p = X.rel_path(UPLOAD / p, REPO_ROOT)
            rows.append((str(r.get(bcol, "")).strip(), p))
        return rows


def check_batches(report: Report, max_files: int, max_mb: float) -> None:
    a, b = BATCHES / "order_A.csv", BATCHES / "order_B.csv"
    if not a.exists() and not b.exists():
        report.add(9, "SKIP", "batches/order_A.csv and order_B.csv not found")
        return
    if not (a.exists() and b.exists()):
        report.add(9, "FAIL", f"only one of order_A.csv / order_B.csv exists")
        return
    upload = {X.rel_path(p, REPO_ROOT): p.stat().st_size for p in UPLOAD.rglob("*") if p.is_file() and not p.name.startswith(".")}
    seqs = {}
    for path in (a, b):
        name = path.name
        try:
            rows = load_order(path)
        except (ValueError, csv.Error) as exc:
            report.add(9, "FAIL", f"{name}: {exc}")
            continue
        seqs[name] = [p for _, p in rows]
        counts = collections.Counter(p for _, p in rows)
        dups = [p for p, n in counts.items() if n > 1]
        unknown = [p for p in counts if p not in upload]
        missing = sorted(set(upload) - set(counts))
        ok = True
        if dups:
            ok = False
            report.add(9, "FAIL", f"{name}: {len(dups)} file(s) listed more than once: {dups[:10]}")
        if unknown:
            ok = False
            report.add(9, "FAIL", f"{name}: {len(unknown)} path(s) not in corpus/upload: {unknown[:10]}")
        if missing:
            ok = False
            report.add(9, "FAIL", f"{name}: {len(missing)} upload file(s) missing: {missing[:10]}")
        batches: dict[str, list[str]] = collections.OrderedDict()
        for bid, p in rows:
            batches.setdefault(bid, []).append(p)
        for bid, ps in batches.items():
            size = sum(upload.get(p, 0) for p in ps)
            if len(ps) > max_files:
                ok = False
                report.add(9, "FAIL", f"{name}: batch {bid} has {len(ps)} files (max {max_files})")
            if size > max_mb * 1e6:
                ok = False
                report.add(9, "FAIL", f"{name}: batch {bid} is {size / 1e6:.1f} MB (max {max_mb:g} MB)")
        if ok:
            report.add(9, "PASS", f"{name}: {len(rows)} files in {len(batches)} batches, all within limits")
    if len(seqs) == 2:
        sa, sb = seqs[a.name], seqs[b.name]
        if set(sa) != set(sb):
            report.add(9, "FAIL", f"orders differ in file set: {len(set(sa) ^ set(sb))} file(s) in only one order")
        elif sa == sb:
            report.add(9, "FAIL", "order_A and order_B list the files in the same order")
        else:
            report.add(9, "PASS", "both orders hold the same file set in different orders")


# ---------------------------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Verify manifests, questions and corpus.")
    ap.add_argument("--family", help="restrict checks 1 and 3 to manifests/<family>.facts.yaml")
    ap.add_argument("--checks", help="comma-separated subset of checks to run, e.g. 1,3 (default: all)")
    ap.add_argument("--no-ocr", action="store_true", help="never run OCR (OCR facts become WARN unless cached)")
    ap.add_argument("--quick", action="store_true",
                    help="reuse the existing index, OCR from cache only, DOCX pages from metadata")
    ap.add_argument("--json", metavar="PATH", help="write the full report as JSON")
    ap.add_argument("--max-files", type=int, default=30, help="max files per batch (check 9)")
    ap.add_argument("--max-mb", type=float, default=100, help="max MB per batch (check 9)")
    ap.add_argument("--max-total-mb", type=float, default=350, help="max size of corpus/upload (check 4)")
    ap.add_argument("--jobs", type=int, default=8, help="worker processes")
    ap.add_argument("--index-dir", default=str(B.INDEX_DIR))
    ap.add_argument("--root", help="corpus root holding corpus/, manifests/, questions/, batches/ (default: repo)")
    ap.add_argument("--code-repo-root", help="directory holding variant_<x>/ code repos")
    ap.add_argument("--forbidden-terms", metavar="FILE", help="forbidden-terms list (default: local/forbidden_terms.txt)")
    ap.add_argument("--verbose", action="store_true", help="print every WARN")
    ap.add_argument("--questions", metavar="PATH",
                    help="question file for check 2 (default: questions/questions.yaml, else questions/parts/*)")
    args = ap.parse_args(argv)
    t0 = time.time()
    if args.root:
        set_root(args.root)
    if args.code_repo_root:
        X.set_code_repo_root(args.code_repo_root)
    if args.questions:
        global QUESTIONS, QUESTION_PARTS
        QUESTIONS = Path(args.questions).resolve()
        QUESTION_PARTS = QUESTIONS.parent / "__none__"
    selected = sorted({int(x) for x in args.checks.split(",")}) if args.checks else list(range(1, 10))
    ocr_mode = "off" if args.no_ocr else ("cache" if args.quick else "full")
    index_dir = Path(args.index_dir)
    report = Report()

    all_facts, manifest_errors = load_manifests()
    facts_by_id = {str(e.get("fact_id")): e for e in all_facts if e.get("fact_id")}
    facts = all_facts
    if args.family:
        mf = family_manifest(args.family)
        facts = [e for e in all_facts if e.get("_manifest") == mf]
        if not (MANIFESTS / mf).exists():
            report.add(1, "FAIL", f"manifests/{mf} not found")

    needs_index = any(k in selected for k in (3, 6, 7, 8))
    if needs_index:
        have_index = (index_dir / B.STATE_NAME).exists()
        if args.quick and have_index:
            report.add(0, "PASS", "reused existing index (--quick)")
        else:
            print("Building/refreshing the index ...", file=sys.stderr)
            st = B.build(index_dir=index_dir, jobs=args.jobs, ocr=not args.no_ocr and not args.quick,
                         repo_root=REPO_ROOT)
            report.add(0, "PASS", f"index: {st['sources']} sources, {st['updated']} re-indexed, "
                                  f"{st['units']} units, {st['seconds']}s")
            for err in st["errors"]:
                report.add(0, "WARN", f"extraction error (coverage gap for checks 3/6/7/8): {err}")
            for err in st["ocr_errors"]:
                report.add(0, "WARN", f"OCR error: {err}")

    fact_status: dict[str, str] = {}
    if 1 in selected:
        print(f"Check 1: verifying {len(facts)} facts ...", file=sys.stderr)
        fact_status = check_facts(report, facts, all_facts, manifest_errors, ocr_mode, args.jobs)
    if 2 in selected:
        check_questions(report, facts_by_id, fact_status, ocr_mode)
    if 3 in selected:
        check_exclusivity(report, facts, facts_by_id, index_dir)
    if 4 in selected:
        print("Check 4: inventory ...", file=sys.stderr)
        check_inventory(report, args.quick, args.max_total_mb, args.jobs)
    if 5 in selected:
        check_rejected(report)
    if 6 in selected:
        check_denylist(report, index_dir, Path(args.forbidden_terms) if args.forbidden_terms else None)
    if 7 in selected:
        check_secrets(report, index_dir)
    if 8 in selected:
        check_guardrail(report, all_facts, index_dir)
    if 9 in selected:
        check_batches(report, args.max_files, args.max_mb)

    if args.family:
        # a family-scoped run cannot expect the whole corpus to exist yet
        for k in (4, 5, 9):
            for i in report.items[k]:
                if i["status"] == "FAIL" and (i["msg"].startswith("no ") or "missing" in i["msg"]):
                    i["status"] = "WARN"
                    i["msg"] += " (family-scoped run)"
    report.print(selected, args.verbose)
    elapsed = time.time() - t0
    print(f"\n{'FAILED' if report.failed() else 'OK'} in {elapsed:.1f}s")
    if args.json:
        data = report.to_json()
        data.update(seconds=round(elapsed, 1), args=vars(args))
        Path(args.json).write_text(json.dumps(data, indent=1, ensure_ascii=False, default=str), encoding="utf-8")
    return 1 if report.failed() else 0


if __name__ == "__main__":
    sys.exit(main())

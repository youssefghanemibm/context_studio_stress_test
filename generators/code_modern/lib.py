"""Shared plumbing for the modern half of Corvane's monorepo (code_modern).

A ``Repo`` collects every file the modern half contributes, its variant membership, the
commit that creates it, and the content modifications later commits make (before/after
snippets).  The assembler (generators/code_repo/assemble.py) replays that history.

Facts are registered against (variant, path, needle) and turned into manifest entries once
the final content is known (line numbers are computed from the text, never hand-counted).
"""
from __future__ import annotations

import datetime as dt
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from generators.common import util  # noqa: E402
from world.worldlib import load_world  # noqa: E402

W = load_world()
HEAD_DATE = dt.date(2026, 11, 6)        # variant a head commit
C_DATE = dt.date(2026, 11, 12)          # CM-09
FAMILY = "code_modern"
FACT_PREFIX = "CODEMOD"

SRC = ROOT / "build" / "code_src"
OUT_A = SRC / "modern"                  # variant a final state (+ b-only files, marked in history)
OUT_C = SRC / "modern_c"                # CM-09 overrides (full files)
HISTORY = OUT_A / "history.yaml"

SERVICES = [s for s in W.services_by_id.values()] if hasattr(W, "services_by_id") else list(W.services.values())
SERVICES = sorted(SERVICES, key=lambda s: s["id"])
SVC = {s["name"]: s for s in SERVICES}

PKG = {
    "claim-core-svc": "claimcore", "fnol-intake-svc": "fnol", "triage-svc": "triage",
    "assessment-svc": "assessment", "reserve-engine": "reserve", "fraud-referral-svc": "fraud",
    "settlement-svc": "settlement", "payment-orchestrator": "payment", "recovery-svc": "recovery",
    "document-svc": "document", "notification-svc": "notification", "gl-posting-svc": "gl",
    "reporting-feed-svc": "reporting",
}
CLASS_STEM = {
    "claim-core-svc": "ClaimCore", "fnol-intake-svc": "FnolIntake", "triage-svc": "Triage",
    "assessment-svc": "Assessment", "reserve-engine": "ReserveEngine", "fraud-referral-svc": "FraudReferral",
    "settlement-svc": "Settlement", "payment-orchestrator": "PaymentOrchestrator", "recovery-svc": "Recovery",
    "document-svc": "Document", "notification-svc": "Notification", "gl-posting-svc": "GlPosting",
    "reporting-feed-svc": "ReportingFeed",
}

OLD_RESERVE, NEW_RESERVE = "reserve-svc", "reserve-engine"


def person(pid: str, d: dt.date | None = None) -> str:
    return W.name_of(pid, d or HEAD_DATE)


def email(pid: str) -> str:
    return W.people[pid]["email"]


def rng(key: str):
    return util.rng(f"{FAMILY}:{key}")


def pick(key: str, options: list[str]) -> str:
    return rng(key).choice(options)


# ---------------------------------------------------------------------------------------------
# Filler commits (benign: no world facts in the messages)
# ---------------------------------------------------------------------------------------------
# id, date, author, message.  Times of day are fixed by the assembler from rng(commit id).
FILLER = [
    ("F-01", "2025-03-10", "P053", "Add repository scaffolding: README, Makefile and .gitignore"),
    ("F-02", "2025-03-24", "P018", "Add CODEOWNERS"),
    ("F-03", "2025-04-14", "P040", "Initial Spring Boot service skeletons"),
    ("F-04", "2025-04-22", "P041", "Scaffold service modules with Maven builds"),
    ("F-05", "2025-05-06", "P042", "Add service module skeletons"),
    ("F-06", "2025-05-12", "P043", "Add service module skeleton and REST controller"),
    ("F-07", "2025-06-02", "P053", "Add Terraform modules and the prod environment root"),
    ("F-08", "2025-06-16", "P053", "Add Kubernetes manifests"),
    ("F-09", "2025-07-07", "P049", "Add OpenAPI specifications"),
    ("F-10", "2025-08-11", "P053", "Bump Spring Boot parent from 3.3.2 to 3.3.5"),
    ("F-11", "2025-09-08", "P043", "Add policy class and unit tests"),
    ("F-12", "2025-10-06", "P040", "Add unit tests for the classifier"),
    ("F-13", "2025-10-27", "P041", "Fix typos in service READMEs"),
    ("F-13b", "2025-11-10", "P040", "Rename storage client configuration keys"),
    ("F-14", "2025-12-15", "P041", "Add Kafka listener and consumer wiring"),
    ("F-15", "2026-01-19", "P053", "Bump Spring Boot parent from 3.3.5 to 3.4.1"),
    ("F-16", "2026-03-16", "P042", "Move thresholds into effective-dated configuration"),
    ("F-17", "2026-03-20", "P041", "Add scheduled job for currency runs"),
    ("F-18", "2026-03-25", "P040", "Add scheduler and listener for outbound notices"),
    ("F-19", "2026-05-18", "P053", "Apply the shared formatter to Java sources"),
    ("F-20", "2026-08-10", "P053", "Bump Spring Boot parent from 3.4.1 to 3.4.5"),
    ("F-21", "2026-10-05", "P042", "Add unit tests for the threshold policy"),
    ("F-22", "2026-10-20", "P018", "Move architecture decision records into the repository"),
    ("F-23", "2026-10-27", "P049", "Add architecture diagrams"),
    ("F-24", "2026-11-04", "P040", "Fix broken links in documentation"),
    ("F-25", "2026-11-06", "P053", "Clarify local build instructions in the README"),
]
B_COMMIT = ("B-01", "2026-11-06", "P053", "Add legacy bridge, reconciliation tooling, fixtures and archived CLARA sources")


def commit_date(cid: str) -> dt.date:
    for c in FILLER + [B_COMMIT]:
        if c[0] == cid:
            return dt.date.fromisoformat(c[1])
    for c in W.commits.values() if isinstance(W.commits, dict) else W.commits:
        if c["id"] == cid:
            return dt.date.fromisoformat(c["date"])
    raise KeyError(cid)


# ---------------------------------------------------------------------------------------------
# Repo model
# ---------------------------------------------------------------------------------------------

class FileSpec:
    __slots__ = ("path", "content", "variants", "created_by", "mods", "binary", "author", "renamed_from")

    def __init__(self, path, content, variants, created_by, binary=False, author=None):
        self.path = path
        self.content = content
        self.variants = list(variants)
        self.created_by = created_by
        self.mods: list[dict] = []
        self.binary = binary
        self.author = author
        self.renamed_from = None


class Repo:
    def __init__(self):
        self.files: dict[str, FileSpec] = {}
        self.c_overrides: dict[str, str] = {}     # path -> full content after CM-09
        self.c_new: dict[str, str] = {}           # new files created by CM-09 (variant c only)
        self.facts: list[dict] = []

    # files -----------------------------------------------------------------------------------
    def add(self, path: str, content, created_by: str, variants=("a", "b", "c"), binary=False, author=None):
        if path in self.files:
            raise ValueError(f"duplicate file {path}")
        if not binary and not content.endswith("\n"):
            content += "\n"
        fs = FileSpec(path, content, variants, created_by, binary=binary, author=author)
        self.files[path] = fs
        if path.startswith(f"services/{NEW_RESERVE}/") or path.startswith(f"infra/terraform/modules/{NEW_RESERVE}/"):
            if commit_date(created_by) < commit_date("CM-04"):
                fs.renamed_from = path.replace(NEW_RESERVE, OLD_RESERVE, 1)
        return fs

    def modify(self, path: str, commit: str, before: str, after: str):
        """Record that ``commit`` changed ``before`` into ``after`` (``after`` is in the later text)."""
        fs = self.files[path]
        fs.mods.append({"commit": commit, "before": before, "after": after})

    def text_at(self, path: str, commit: str) -> str:
        """Content right after ``commit`` (reverting every registered modification made later)."""
        fs = self.files[path]
        text = fs.content
        cd = commit_date(commit)
        for m in sorted(fs.mods, key=lambda m: commit_date(m["commit"]), reverse=True):
            if commit_date(m["commit"]) > cd:
                text = text.replace(m["after"], m["before"], 1)
        return text

    def modify_whole(self, path: str, commit: str, fn):
        """Whole-file modification: ``fn(text_after_commit) -> text_before_commit``.
        Register later modifications first."""
        after = self.text_at(path, commit)
        before = fn(after)
        if before != after:
            self.modify(path, commit, before, after)

    def check_mods(self):
        """Replay every file's modifications backwards to prove before/after are unambiguous."""
        for fs in self.files.values():
            if fs.binary or not fs.mods:
                continue
            text = fs.content
            for m in sorted(fs.mods, key=lambda m: commit_date(m["commit"]), reverse=True):
                n = text.count(m["after"])
                if n != 1:
                    raise ValueError(f"{fs.path}: 'after' snippet of {m['commit']} occurs {n}x: {m['after'][:60]!r}")
                text = text.replace(m["after"], m["before"], 1)
            for m in sorted(fs.mods, key=lambda m: commit_date(m["commit"])):
                if text.count(m["before"]) != 1:
                    raise ValueError(f"{fs.path}: 'before' snippet of {m['commit']} not unique when replaying")
                text = text.replace(m["before"], m["after"], 1)
            assert text == fs.content, fs.path

    # facts -----------------------------------------------------------------------------------
    def fact(self, variant: str, path: str, needle: str, statement: str, kind: str = "general",
             world_ref: str | None = None, exclusive: bool = False, placement: str | None = None,
             anchor: str | None = None, span: str | None = None, also_in=None, notes: str | None = None,
             tag: str | None = None):
        """Register a code_lines fact.  ``span`` (optional) is a larger exact substring whose
        lines form the locator (it must contain ``needle``); ``anchor`` disambiguates."""
        self.facts.append(dict(loc="code", variant=variant, path=path, needle=needle, statement=statement,
                               kind=kind, world_ref=world_ref, exclusive=exclusive, placement=placement,
                               anchor=anchor, span=span, also_in=also_in or [], notes=notes, tag=tag))

    def commit_fact(self, variant: str, message_contains: str, needle: str, statement: str,
                    kind: str = "commit_fact", world_ref=None, exclusive=False, placement=None,
                    also_in=None, notes=None, tag=None):
        self.facts.append(dict(loc="git", variant=variant, message_contains=message_contains, needle=needle,
                               statement=statement, kind=kind, world_ref=world_ref, exclusive=exclusive,
                               placement=placement, also_in=also_in or [], notes=notes, tag=tag))

    def image_fact(self, variant: str, path: str, needle: str, statement: str, world_ref=None, tag=None):
        self.facts.append(dict(loc="image", variant=variant, path=path, needle=needle, statement=statement,
                               kind="image_text", world_ref=world_ref, exclusive=False, placement=None,
                               also_in=[], notes="text rendered inside a PNG diagram (OCR)", tag=tag))

    # content lookup ----------------------------------------------------------------------------
    def text_of(self, variant: str, path: str) -> str:
        if variant == "c":
            if path in self.c_overrides:
                return self.c_overrides[path]
            if path in self.c_new:
                return self.c_new[path]
        fs = self.files[path]
        if variant not in fs.variants:
            raise KeyError(f"{path} not in variant {variant}")
        return fs.content


def line_range(text: str, needle: str, span: str | None = None, anchor: str | None = None) -> tuple[int, int]:
    """1-based inclusive line range of ``span`` (or ``needle``) in ``text``, after ``anchor``."""
    target = span or needle
    start_at = 0
    if anchor:
        start_at = text.find(anchor)
        if start_at < 0:
            raise ValueError(f"anchor {anchor!r} not found")
    i = text.find(target, start_at)
    if i < 0:
        raise ValueError(f"needle/span {target[:80]!r} not found")
    if span and norm_ws(needle) not in norm_ws(span):
        raise ValueError(f"needle {needle!r} not inside span")
    start = text.count("\n", 0, i) + 1
    end = start + target.count("\n")
    if target.endswith("\n"):
        end -= 1
    return start, end


def norm_ws(s: str) -> str:
    return " ".join(s.split())

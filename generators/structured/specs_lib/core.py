"""Shared helpers for the specs part: world access, fact collection, exclusivity guards."""
from __future__ import annotations

import datetime as dt
import pathlib
import re
from dataclasses import dataclass, field
from typing import Any

from generators.common import util
from world.worldlib import load_world

W = load_world()
FAMILY_DIR = "structured"
MANIFEST_NAME = "structured.specs"
FILE_IDS = [f"ST{i:03d}" for i in range(27, 61)]
ANCHORS = {fid: W.anchor(fid) for fid in FILE_IDS}


def fname(fid: str) -> str:
    return ANCHORS[fid]["filename"]


def fdate(fid: str) -> str:
    return str(ANCHORS[fid]["date"])


def ftitle(fid: str) -> str:
    return ANCHORS[fid]["title"]


def fauthor(fid: str) -> str:
    return ANCHORS[fid]["author"]


def fstatus(fid: str) -> str:
    # the anchor note '(pre-rename)' is hindsight; the document itself only knows it is approved
    return ANCHORS[fid]["status"].replace(" (pre-rename)", "")


# ---------------------------------------------------------------------------------------------
# Dates
# ---------------------------------------------------------------------------------------------

UK_HOLIDAYS = {
    "2025-01-01", "2025-04-18", "2025-04-21", "2025-05-05", "2025-05-26", "2025-08-25", "2025-12-25",
    "2025-12-26", "2026-01-01", "2026-04-03", "2026-04-06", "2026-05-04", "2026-05-25", "2026-08-31",
    "2026-12-25", "2026-12-28",
}


def d(s: str) -> dt.date:
    return dt.date.fromisoformat(str(s))


def add_business_days(start: str | dt.date, n: int) -> dt.date:
    cur = d(start) if not isinstance(start, dt.date) else start
    left = n
    while left > 0:
        cur += dt.timedelta(days=1)
        if cur.weekday() < 5 and cur.isoformat() not in UK_HOLIDAYS:
            left -= 1
    return cur


def minus_days(s: str, n: int) -> str:
    return (d(s) - dt.timedelta(days=n)).isoformat()


def plus_days(s: str, n: int) -> str:
    return (d(s) + dt.timedelta(days=n)).isoformat()


def before(a: str | None, b: str) -> bool:
    """a <= b (None counts as 'always')."""
    return a is None or str(a) <= str(b)


def human_date(s: str) -> str:
    x = d(s)
    return x.strftime("%b %d, %Y")


# ---------------------------------------------------------------------------------------------
# People, teams, systems as of a date
# ---------------------------------------------------------------------------------------------

def pname(pid: str, on: str) -> str:
    return W.name_of(pid, on)


def ptitle(pid: str, on: str) -> str:
    return W.title_of(pid, on) or ""


def pemail(pid: str, on: str) -> str:
    p = W.people[pid]
    for h in p.get("email_history", []) or []:
        if before(h.get("from"), on) and (h.get("to") is None or on <= str(h["to"])):
            return h["email"]
    return p["email"]


def pcity(pid: str, on: str) -> str:
    loc = W.location_of(pid, on)
    return W.locations[loc]["city"]


def person(pid: str, on: str) -> dict:
    team = W.team_of(pid, on)
    return {"id": pid, "name": pname(pid, on), "title": ptitle(pid, on), "email": pemail(pid, on),
            "team": team, "teamName": W.team_name(team, on) if team else None, "location": pcity(pid, on)}


def sysname(sid: str, on: str) -> str:
    return W.system_name(sid, on)


def svcname(svc: str, on: str) -> str:
    return W.service_name(svc, on)


def team_name(tid: str, on: str) -> str:
    return W.team_name(tid, on)


def team_exists(tid: str, on: str) -> bool:
    t = W.teams[tid]
    return str(t.get("formed") or "0000") <= on


def program_exists(pid: str, on: str) -> bool:
    """A CLARA program exists from its `since` date (programs.yaml)."""
    return str(W.programs[pid]["since"]) <= on


def jcl_jobs_as_of(on: str) -> list[tuple[str, dict, list[dict]]]:
    """(name, job, steps) for the JCL jobs that exist on `on`.

    jcl_jobs.yaml has no dates of its own: a job exists once one of its step programs exists, and only the
    steps whose program exists are listed (CLRQFR01/CLRFR090 appear from 2026-06-26, not before).
    """
    out = []
    for name, j in W.jcl_jobs.items():
        steps = [st for st in j["steps"] if program_exists(st["program"], on)]
        if steps:
            out.append((name, j, steps))
    return out


def interface_exists(iid: str, on: str) -> bool:
    return str(W.interfaces[iid]["since"]) <= on


# ---------------------------------------------------------------------------------------------
# Exclusivity
# ---------------------------------------------------------------------------------------------

class ExclusivityError(AssertionError):
    pass


def may(fid: str, ref: str, fld: str | None = None) -> bool:
    return W.may_state(fid, ref, fld)


def need(fid: str, ref: str, fld: str | None = None) -> None:
    if not W.may_state(fid, ref, fld):
        raise ExclusivityError(f"{fid} may not state {ref}#{fld} (reserved for {W.allowed_files(ref, fld)})")


def rule_params_ok(fid: str, rid: str, ver: int) -> dict:
    """Parameters of a rule version that this file may state."""
    v = [x for x in W.rules[rid]["versions"] if x["version"] == ver][0]
    out = {}
    for k, val in (v.get("parameters") or {}).items():
        if W.may_state(fid, f"RULE:{rid}@v{ver}", f"parameters.{k}"):
            out[k] = val
    return out


def rule_text_ok(fid: str, rid: str, ver: int) -> bool:
    return W.may_state(fid, f"RULE:{rid}@v{ver}", "text")


def rule_ver(rid: str, ver: int) -> dict:
    return [x for x in W.rules[rid]["versions"] if x["version"] == ver][0]


# Strings that must never appear in this part's output (exclusive facts of other files, canaries,
# product terms). Exceptions per file are listed in FORBIDDEN_EXCEPT.
FORBIDDEN = [
    r"CICSPRD", r"CLRPLAN1", r"\bDB2P\b", r"02:15", r"bi-index", r"BI_INDEX", r"\b3\.1\s?%", r"index_pct",
    r"MAXDEPTH\W{0,3}50\W?000", r"max.?depth\W{0,6}50\W?000",
    r"fraud-notice\.sent", r"CHUB-421", r"CHUB-415", r"R2026\.11", r"legacy-bridge", r"zz-reconcile",
    r"recon\.daily_diff", r"CLM-SE-2026-004417", r"CLRFR990", r"velocity score", r"2027-01-23", r"cdw-ro-02",
    r"\bAUC\b", r"population stability", r"\b2\.9\s?%", r"200Gi", r"0\.001\s?%", r"£0\.01\b",
    r"variance tolerance", r"41,250", r"\b41250\b", r"186,400", r"\b186400\b", r"Project Larchmont",
    r"FRO-CHK", r"648\.2", r"412,906,118", r"12,480", r"second Tuesday", r"CS-MAN-007", r"97\.3\s?%",
    r"611\.9", r"2,318\.4", r"LEGACY_SKADE_REF", r"FR-REQ-014", r"SMS counts", r"Brynholt", r"Calderbank",
    r"SEK 4,900", r"\bPL-\d{3}\b", r"\bneedle\b", r"\bcanary\b", r"Context Studio", r"knowledge graph",
    r"\bLLM\b", r"\bRAG\b", r"23:30\s?[-–]\s?03:30", r"(?<![\d.])0\.87\b",
    r"CLR-2025-02",   # the import baseline name belongs to the CM-01 commit message only (PL-266)
    r"clara-platform", r"kbarraclough", r"Testy McTestface", r"changeme-not-a-secret", r"@example\.com", r"\b555[-. ]\d{4}\b",
]
FORBIDDEN_EXCEPT = {
    "ST037": {r"MAXDEPTH\W{0,3}50\W?000", r"max.?depth\W{0,6}50\W?000"},
}
_FORBIDDEN_RX = [(p, re.compile(p, re.IGNORECASE)) for p in FORBIDDEN]


def denylist_rx() -> re.Pattern:
    names = sorted(set(W.denylist), key=lambda s: -len(s))
    alts = [re.escape(t).replace(r"\ ", r"\s+") for t in names]
    return re.compile(r"(?<!\w)(?:" + "|".join(alts) + r")(?!\w)", re.IGNORECASE)


_DENY = denylist_rx()


def scan_forbidden(fid: str, text: str) -> list[str]:
    errs = []
    exc = FORBIDDEN_EXCEPT.get(fid, set())
    for p, rx in _FORBIDDEN_RX:
        if p in exc:
            continue
        m = rx.search(text)
        if m:
            errs.append(f"{fid}: forbidden pattern {p!r} at …{text[max(0, m.start() - 60):m.end() + 60]!r}…")
    m = _DENY.search(text)
    if m:
        errs.append(f"{fid}: denylisted name {m.group(0)!r} at …{text[max(0, m.start() - 60):m.end() + 60]!r}…")
    return errs


# ---------------------------------------------------------------------------------------------
# Facts
# ---------------------------------------------------------------------------------------------

class Facts:
    def __init__(self, fid: str, out_dir: pathlib.Path):
        self.fid = fid
        self.path = out_dir / fname(fid)
        self.file = util.rel(self.path)
        self.items: list[dict] = []

    def add(self, kind: str, statement: str, locator: dict, needle: str, world_ref: str | None = None,
            exclusive: bool = False, placement: str | None = None, also_in: list[str] | None = None,
            notes: str | None = None) -> str:
        n = len(self.items) + 1
        fact_id = f"{self.fid}-F{n:03d}"
        e: dict[str, Any] = {"fact_id": fact_id, "world_ref": world_ref, "kind": kind, "statement": statement,
                             "file": self.file, "locator": locator, "needle": needle, "exclusive": exclusive,
                             "also_in": list(also_in or [])}
        if placement:
            pl = W.placements_by_id[placement]
            if pl["target_file"] == self.fid:
                assert pl["world_ref"] == world_ref, (placement, world_ref)
                assert bool(pl["exclusive"]) == exclusive, placement
                assert pl["kind"] == kind, (placement, kind)
            e["placement"] = placement
            e["placement_key"] = pl["key"]
        if notes:
            e["notes"] = notes
        self.items.append(e)
        return fact_id


@dataclass
class Built:
    fid: str
    content: bytes
    facts: list[dict]
    count: str           # "<n> rows" style count for the summary line
    text_for_scan: str = ""
    extra: dict = field(default_factory=dict)


# ---------------------------------------------------------------------------------------------
# Document control helpers
# ---------------------------------------------------------------------------------------------

DOC_PREFIX = {
    "ST027": "SKR-FRD-API-027", "ST028": "SKR-PLT-FLG-028", "ST029": "SKR-FRD-PRM-029", "ST030": "SKR-INT-KAF-030",
    "ST031": "SKR-ARC-REG-031", "ST032": "SKR-FRD-EVT-032", "ST033": "SKR-MIG-DQR-033", "ST034": "REG-FR1-2026Q3",
    "ST035": "SKR-INT-CAT-035", "ST036": "SKR-DSC-PGM-036", "ST037": "SKR-INT-MQD-037", "ST038": "REG-FR1-2026Q2",
    "ST039": "REG-TP2-2026Q2", "ST040": "SKR-BPM-PRC-040", "ST041": "SKR-DSC-CPY-041", "ST042": "SKR-OPS-JCL-042",
    "ST043": "SKR-API-RSV-043", "ST044": "SKR-API-FRD-044", "ST045": "SKR-CFG-RUL-045", "ST046": "SKR-INT-TOP-046",
    "ST047": "SKR-PLT-HLM-047", "ST048": "SKR-INT-DC49-048", "ST049": "SKR-PLT-K8S-049", "ST050": "SKR-PLT-K8S-050",
    "ST051": "SKR-PLT-CI-051", "ST052": "SKR-OPS-ALR-052",
}

HISTORY_PHRASES = [
    "Structure agreed with reviewers", "Review comments incorporated", "Updated after design review",
    "Minor corrections", "Aligned names with the system catalogue", "Added missing entries",
    "Clarified ownership fields", "Formatting and typo fixes", "Updated references", "Consolidated reviewer feedback",
    "Second review round", "Cross-checked against the source systems",
]
FINAL_LABEL = {"approved": "Approved", "final": "Issued as final", "submitted": "Submitted to NISA",
               "published": "Published"}


def version_history(fid: str, authors: list[str], n: int | None = None, span_days: int = 120,
                    final_label: str | None = None) -> list[dict]:
    """Plausible version history ending on the anchor date (names as of each date)."""
    r = util.rng(f"{fid}:history")
    end = fdate(fid)
    n = n or r.randint(3, 6)
    days = sorted(r.sample(range(7, span_days), n - 1), reverse=True)
    dates = [minus_days(end, x) for x in days] + [end]
    out = []
    phrases = HISTORY_PHRASES[:]
    r.shuffle(phrases)
    for i, day in enumerate(dates):
        major = i == len(dates) - 1
        ver = f"{1 if major else 0}.{0 if major else i + 1}"
        if major:
            desc = final_label or FINAL_LABEL.get(fstatus(fid), "Issued")
        elif i == 0:
            desc = "Initial draft for review"
        else:
            desc = phrases[(i - 1) % len(phrases)]
        who = authors[i % len(authors)]
        out.append({"version": ver, "date": day, "author": pname(who, day), "change": desc})
    return out

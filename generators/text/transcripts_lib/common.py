"""Shared helpers: world access, fact registry, text-file builder, safety scans."""
from __future__ import annotations

import datetime as dt
import pathlib
import re
import unicodedata

from generators.common import util
from world.worldlib import load_world

W = load_world()
ROOT = util.ROOT
OUT_DIR = util.UPLOAD / "text"
FAMILY = "text.transcripts"

MY_IDS = (["TX%03d" % i for i in range(1, 7)] + ["TX%03d" % i for i in range(21, 31)]
          + ["TX%03d" % i for i in range(61, 73)])


def D(s: str) -> dt.date:
    return dt.date.fromisoformat(s)


def long_date(d: dt.date | str) -> str:
    if isinstance(d, str):
        d = D(d)
    return f"{d.strftime('%A')} {d.day} {d.strftime('%B %Y')}"


def short_date(d: dt.date | str) -> str:
    if isinstance(d, str):
        d = D(d)
    return f"{d.day} {d.strftime('%B %Y')}"


def name(pid: str, d) -> str:
    return W.name_of(pid, d)


def first(pid: str, d) -> str:
    return W.name_of(pid, d).split()[0]


def title(pid: str, d) -> str:
    return W.title_of(pid, d) or ""


def email(pid: str, d) -> str:
    p = W.people[pid]
    for e in p.get("email_history") or []:
        if (e["from"] is None or e["from"] <= str(d)) and (e["to"] is None or str(d) <= e["to"]):
            return e["email"]
    return p["email"]


def assert_may(fid: str, ref: str, field: str | None = None) -> None:
    """Guard: raise if the world reserves this field for another file."""
    if not W.may_state(fid, ref, field):
        raise AssertionError(f"{fid} may not state {ref}#{field} (exclusive to {W.is_exclusive(ref, field)})")


def norm(s: str) -> str:
    """Rough version of harness normalisation, used for generation-time self checks."""
    t = unicodedata.normalize("NFKC", s)
    for a, b in (("‘", "'"), ("’", "'"), ("“", '"'), ("”", '"'),
                 ("–", "-"), ("—", "-"), ("≥", ">="), ("≤", "<=")):
        t = t.replace(a, b)
    return re.sub(r"\s+", " ", t.casefold()).strip()


class Facts:
    """Collects manifest entries for one generator run."""

    def __init__(self):
        self.entries: list[dict] = []
        self.counters: dict[str, int] = {}

    def add(self, fid: str, path: pathlib.Path, *, kind: str, statement: str, needle: str,
            locator: dict, world_ref: str | None = None, exclusive: bool = False,
            placement: dict | None = None, also_in: list[str] | None = None, notes: str | None = None,
            text_at_locator: str | None = None) -> str:
        if text_at_locator is not None and norm(needle) not in norm(text_at_locator):
            raise AssertionError(f"{fid}: needle {needle!r} not in {text_at_locator[:200]!r}")
        n = self.counters.get(fid, 0) + 1
        self.counters[fid] = n
        fact_id = f"{fid}-F{n:03d}"
        e = {
            "fact_id": fact_id,
            "world_ref": world_ref,
            "kind": kind,
            "statement": statement,
            "file": util.rel(path),
            "locator": locator,
            "needle": needle,
            "exclusive": exclusive,
            "also_in": also_in or [],
        }
        if placement is not None:
            e["world_ref"] = placement["world_ref"]
            e["exclusive"] = bool(placement.get("exclusive"))
            e["placement"] = placement["placement_id"]
            e["placement_key"] = placement["key"]
            if placement.get("contradictions"):
                e["contradiction"] = placement["contradictions"]
            if placement.get("headline"):
                e["headline"] = placement["headline"]
        if notes:
            e["notes"] = notes
        self.entries.append(e)
        return fact_id


class TextDoc:
    """A .txt document assembled line by line, so facts can be located by line number."""

    def __init__(self, fid: str, path: pathlib.Path, facts: Facts):
        self.fid = fid
        self.path = path
        self.facts = facts
        self.lines: list[str] = []
        self.pending: list[tuple] = []

    def add(self, line: str = "") -> int:
        assert "\n" not in line, line
        self.lines.append(line.rstrip())
        return len(self.lines)

    def extend(self, lines) -> None:
        for ln in lines:
            self.add(ln)

    def fact(self, lineno: int, *, needle: str, statement: str, kind: str = "general",
             world_ref: str | None = None, placement: dict | None = None, end: int | None = None,
             notes: str | None = None, exclusive: bool = False, also_in=None) -> str:
        end = end or lineno
        text = "\n".join(self.lines[lineno - 1:end])
        return self.facts.add(self.fid, self.path, kind=kind, statement=statement, needle=needle,
                              locator={"kind": "text_lines", "start": lineno, "end": end},
                              world_ref=world_ref, placement=placement, notes=notes,
                              exclusive=exclusive, also_in=also_in, text_at_locator=text)

    def add_fact(self, line: str, **kw) -> int:
        n = self.add(line)
        self.fact(n, **kw)
        return n

    def text(self) -> str:
        return "\n".join(self.lines) + "\n"

    def write(self) -> pathlib.Path:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(self.text(), encoding="utf-8")
        return self.path


def out_path(fid: str, slug: str, ext: str) -> pathlib.Path:
    return OUT_DIR / f"{fid}_{slug}.{ext}"


def placement(fid: str, key: str) -> dict:
    for p in W.placements_for(fid):
        if p["key"] == key:
            return p
    raise KeyError(f"{fid}: no placement {key}")


# ------------------------------------------------------------------------------------------
# Safety scans run over every generated text before it is written
# ------------------------------------------------------------------------------------------

def _denylist_patterns():
    import yaml
    data = yaml.safe_load((ROOT / "world/data/names_denylist.yaml").read_text(encoding="utf-8"))
    pats = []
    for e in data.get("entries", []):
        nm = e["name"]
        pats.append((nm, re.compile(r"(?<![\w])" + re.escape(nm) + r"(?![\w])", re.I)))
    return pats


_DENY = None

FORBIDDEN = [re.compile(p, re.I) for p in (
    r"knowledge graph", r"\bLLMs?\b", r"large language model", r"context studio",
    r"retrieval[- ]augmented", r"\bwatsonx\b", r"\bMicrosoft\b", r"\bJira Software\b",
)] + [re.compile(p) for p in (r"\bRAG\b", r"\bSlack\b", r"\bZoom\b", r"\bTeams\b(?! of)")]

# Exclusive values owned by other files that must never surface in this family's files.
# (Checked as plain substrings after normalisation; see build/notes/text.transcripts.md.)
BANNED_VALUES = [
    "186,400", "186400", "50,000 messages", "maxdepth", "1,140", "310,000", "41,250 claims migrated",
    "cicsprd", "db2p", "clrplan1", "cs-man-007", "3.1%", "0.87", "0.06", "31.2m", "£31.2", "97.8",
    "611.9", "2,318.4", "648.2", "12 partitions", "14 days retention", "fraud-notice.sent", "hub-squad-recoveries-docs",
    "0.5% per product", "£0.01 per claim", "0.001%", "second tuesday", "brynholt", "calderbank",
    "sms counts", "4,900", "5,150", "2,150", "5,200", "cdw-ro-02", "recon.daily_diff", "2027-01-23", "23 january 2027",
    "clrfr990", "velocity score", "clm-se-2026-004417", "fro-chk-3", "12,480", "2026-12-05", "412,906,118",
    "larchmont", "200gi", "telephone 58", "telephone 50", "digital 41", "41.2%", "18.7%", "36.5%",
]


BANNED_REGEX = [re.compile(p, re.I) for p in (
    r"(?<![:\d])02:15(?!:)", r"(?<![£\d,.])50,?000(?![\d,])",
)]


def scan_text(fid: str, text: str, extra_banned: list[str] | None = None, allow: list[str] | None = None) -> None:
    global _DENY
    if _DENY is None:
        _DENY = _denylist_patterns()
    for nm, pat in _DENY:
        m = pat.search(text)
        if m:
            ctx = text[max(0, m.start() - 60): m.end() + 60]
            raise AssertionError(f"{fid}: denylisted name {nm!r} in ...{ctx}...")
    for pat in FORBIDDEN:
        m = pat.search(text)
        if m:
            raise AssertionError(f"{fid}: forbidden term {m.group(0)!r}")
    for pat in BANNED_REGEX:
        m = pat.search(text)
        if m and not (allow and m.group(0) in allow):
            ctx = text[max(0, m.start() - 80): m.end() + 80]
            raise AssertionError(f"{fid}: banned pattern {pat.pattern!r} in ...{ctx}...")
    t = norm(text)
    for v in BANNED_VALUES + list(extra_banned or []):
        if allow and v in allow:
            continue
        if norm(v) in t:
            i = t.index(norm(v))
            raise AssertionError(f"{fid}: banned value {v!r} in ...{t[max(0, i - 80): i + 80]}...")

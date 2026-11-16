"""Shared machinery: world access, as-of person views, dates, fact recording, text documents.

Every world fact a document states goes through ``Doc.fact`` / ``Doc.place`` so that it gets a
manifest entry with an exact ``text_lines`` (or ``html_xpath``) locator, and so that the
exclusivity rules (``W.may_state``) are checked before the file is written.
"""
from __future__ import annotations

import dataclasses
import datetime as dt
import random
import re
import textwrap
import unicodedata
from typing import Iterable, Sequence

from generators.common import util
from world.worldlib import load_world

W = load_world()

FAMILY = "text.messages"
FAMILY_DIR = "text"
OUT_DIR = util.UPLOAD / FAMILY_DIR

ORG_NAMES = {
    "ORG-CORVANE": "Corvane Mutual Insurance Society Limited",
    "ORG-IBM": "IBM Consulting",
    "REG-NISA": "National Insurance Supervisory Authority",
}
ORG_SHORT = {"ORG-CORVANE": "Corvane Mutual", "ORG-IBM": "IBM Consulting", "REG-NISA": "NISA"}


# ---------------------------------------------------------------------------------------------
# Dates
# ---------------------------------------------------------------------------------------------

def D(x) -> dt.date:
    if isinstance(x, dt.datetime):
        return x.date()
    if isinstance(x, dt.date):
        return x
    return dt.date.fromisoformat(str(x))


def _last_sunday(year: int, month: int) -> dt.date:
    d = dt.date(year, month, 31)
    while d.weekday() != 6:
        d -= dt.timedelta(days=1)
    return d


def summer_time(d: dt.date) -> bool:
    """EU/UK summer time (switch dates are close enough at day resolution)."""
    d = D(d)
    return _last_sunday(d.year, 3) <= d < _last_sunday(d.year, 10)


def tz_offset(d: dt.date, zone: str = "UK") -> str:
    st = summer_time(d)
    if zone == "UK":
        return "+0100" if st else "+0000"
    return "+0200" if st else "+0100"


def zone_of(pid: str | None) -> str:
    if not pid or pid not in W.people:
        return "UK"
    loc = W.people[pid].get("location", "")
    return "NORDIC" if loc in ("LOC-OSL", "LOC-STO", "LOC-CPH", "EXT-IBM-OSL", "EXT-VEN-GOT") else "UK"


def rfc2822(d, hhmm: str, sec: int = 0, zone: str = "UK") -> str:
    d = D(d)
    return f"{d.strftime('%a')}, {d.day} {d.strftime('%b %Y')} {hhmm}:{sec:02d} {tz_offset(d, zone)}"


def outlook_sent(d, hhmm: str) -> str:
    d = D(d)
    h, m = (int(x) for x in hhmm.split(":"))
    ampm = "AM" if h < 12 else "PM"
    h12 = h % 12 or 12
    return f"{d.strftime('%A')}, {d.day} {d.strftime('%B %Y')} {h12}:{m:02d} {ampm}"


def long_date(d) -> str:
    d = D(d)
    return f"{d.strftime('%A')} {d.day} {d.strftime('%B %Y')}"


def short_date(d) -> str:
    d = D(d)
    return f"{d.day} {d.strftime('%B %Y')}"


def day_month(d) -> str:
    d = D(d)
    return f"{d.day} {d.strftime('%B')}"


def add_minutes(hhmm: str, minutes: int) -> str:
    h, m = (int(x) for x in hhmm.split(":"))
    t = h * 60 + m + minutes
    return f"{t // 60:02d}:{t % 60:02d}"


def workday_before(d, n: int = 1) -> dt.date:
    d = D(d)
    while n > 0:
        d -= dt.timedelta(days=1)
        if d.weekday() < 5:
            n -= 1
    return d


def workday_after(d, n: int = 1) -> dt.date:
    d = D(d)
    while n > 0:
        d += dt.timedelta(days=1)
        if d.weekday() < 5:
            n -= 1
    return d


# ---------------------------------------------------------------------------------------------
# People (as of a date)
# ---------------------------------------------------------------------------------------------

def ascii_fold(s: str) -> str:
    table = {"ø": "o", "Ø": "O", "æ": "ae", "Æ": "AE", "å": "a", "Å": "A"}
    s = "".join(table.get(c, c) for c in s)
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))


@dataclasses.dataclass
class Person:
    pid: str
    name: str
    title: str
    email: str
    phone: str
    org: str
    org_short: str
    location_id: str
    location_name: str
    address: str
    employer: str

    @property
    def first(self) -> str:
        return self.name.split()[0]

    @property
    def last(self) -> str:
        return self.name.split()[-1]

    def addr(self, display: str | None = None) -> str:
        return f"{display or self.name} <{self.email}>"

    def outlook_addr(self) -> str:
        return f"{self.last}, {self.first} <{self.email}>"


def person(pid: str, d, strict: bool = True) -> Person:
    d = D(d)
    p = W.people[pid]
    if strict and not W.employed(pid, d):
        raise ValueError(f"{pid} {p['name']} not employed on {d}")
    name = W.name_of(pid, d)
    email = p["email"]
    for h in p.get("email_history", []) or []:
        lo = D(h["from"]) if h.get("from") else dt.date.min
        hi = D(h["to"]) if h.get("to") else dt.date.max
        if lo <= d <= hi:
            email = h["email"]
    title = W.title_of(pid, d) or ""
    emp = p.get("employer", "ORG-CORVANE")
    if emp in ORG_NAMES:
        org, org_short = ORG_NAMES[emp], ORG_SHORT[emp]
    else:
        v = W.vendors.get(emp, {})
        org, org_short = v.get("name", emp), v.get("short", emp)
    loc_id = W.location_of(pid, d)
    loc = W.locations.get(loc_id, {})
    return Person(pid, name, title, email, p.get("phone", ""), org, org_short, loc_id,
                  loc.get("name", ""), loc.get("address", ""), emp)


def team_name(tid: str, d) -> str:
    return W.team_name(tid, d)


# ---------------------------------------------------------------------------------------------
# Paths, anchors, placements
# ---------------------------------------------------------------------------------------------

def family_folder(fid: str) -> str:
    return util.FAMILY_DIRS.get(fid[:2], "")


def anchor_path(fid: str) -> str:
    """Repo-relative path of any anchored file (used for also_in cross references)."""
    a = W.anchors_by_id[fid]
    return f"corpus/upload/{family_folder(fid)}/{a['filename']}"


def placement_by_key(fid: str, key: str) -> dict:
    for p in W.placements_for(fid):
        if p["key"] == key:
            return p
    raise KeyError(f"no placement {key} for {fid}")


def may(fid: str, ref: str, field: str | None = None) -> bool:
    return W.may_state(fid, ref, field)


def require(fid: str, ref: str, field: str | None = None) -> None:
    if not W.may_state(fid, ref, field):
        raise AssertionError(f"{fid} may not state {ref} {field or ''} (exclusive to {W.is_exclusive(ref, field)})")


# ---------------------------------------------------------------------------------------------
# Fact recording
# ---------------------------------------------------------------------------------------------

@dataclasses.dataclass
class Fact:
    needle: str
    statement: str
    kind: str = "general"
    world_ref: str | None = None
    exclusive: bool = False
    also_in: list = dataclasses.field(default_factory=list)
    placement: str | None = None
    placement_key: str | None = None
    notes: str | None = None
    locator: dict | None = None


class FactSink:
    def __init__(self, fid: str, filename: str):
        self.fid = fid
        self.filename = filename
        self.relpath = f"corpus/upload/{FAMILY_DIR}/{filename}"
        self.facts: list[Fact] = []

    # -- generic
    def _check_ref(self, ref: str | None):
        if ref:
            require(self.fid, ref)

    def add_fact(self, locator: dict, needle: str, statement: str, kind: str = "general",
                 world_ref: str | None = None, exclusive: bool = False, also_in=None,
                 placement: str | None = None, placement_key: str | None = None,
                 notes: str | None = None) -> Fact:
        self._check_ref(world_ref)
        f = Fact(needle=needle, statement=statement, kind=kind, world_ref=world_ref,
                 exclusive=exclusive, also_in=list(also_in or []), placement=placement,
                 placement_key=placement_key, notes=notes, locator=locator)
        self.facts.append(f)
        return f

    def placement_fields(self, key: str) -> dict:
        p = placement_by_key(self.fid, key)
        also = [anchor_path(x) for x in p.get("also_in", [])]
        return dict(statement=p["fact"], kind=p["kind"], world_ref=p["world_ref"],
                    exclusive=bool(p.get("exclusive")), also_in=also,
                    placement=p["placement_id"], placement_key=p["key"])

    def manifest_entries(self) -> list[dict]:
        out = []
        for i, f in enumerate(self.facts, 1):
            e = {
                "fact_id": f"{self.fid}-F{i:03d}",
                "world_ref": f.world_ref,
                "kind": f.kind,
                "statement": f.statement,
                "file": self.relpath,
                "locator": f.locator,
                "needle": f.needle,
                "exclusive": f.exclusive,
                "also_in": f.also_in,
            }
            if f.placement:
                e["placement"] = f.placement
                e["placement_key"] = f.placement_key
            if f.notes:
                e["notes"] = f.notes
            out.append(e)
        return out


class Doc(FactSink):
    """A line-oriented text document (.txt or .md) that records text_lines locators."""

    def __init__(self, fid: str, filename: str, width: int | None = None):
        super().__init__(fid, filename)
        self.lines: list[str] = []
        self.width = width

    # -- writing
    @property
    def n(self) -> int:
        return len(self.lines)

    def line(self, s: str = "") -> tuple[int, int]:
        parts = s.split("\n")
        start = self.n + 1
        self.lines.extend(parts)
        return (start, self.n)

    def blank(self, k: int = 1):
        for _ in range(k):
            self.lines.append("")

    def block(self, lines: Iterable[str]) -> tuple[int, int]:
        start = self.n + 1
        for ln in lines:
            self.lines.extend(ln.split("\n"))
        return (start, max(start, self.n))

    def para(self, text: str, width: int | None = None, prefix: str = "",
             first_prefix: str | None = None) -> tuple[int, int]:
        width = self.width if width is None else width
        if width:
            wrapped = textwrap.wrap(text, width=width, initial_indent=first_prefix if first_prefix is not None else prefix,
                                    subsequent_indent=prefix, break_long_words=False,
                                    break_on_hyphens=False)
        else:
            wrapped = [(first_prefix if first_prefix is not None else prefix) + text]
        return self.block(wrapped or [""])

    # -- facts
    def fact(self, span: tuple[int, int], needle: str, statement: str, kind: str = "general",
             world_ref: str | None = None, **kw) -> Fact:
        loc = {"kind": "text_lines", "start": span[0], "end": span[1]}
        return self.add_fact(loc, needle, statement, kind=kind, world_ref=world_ref, **kw)

    def place(self, span: tuple[int, int], key: str, needle: str, statement: str | None = None,
              notes: str | None = None, kind: str | None = None) -> Fact:
        pf = self.placement_fields(key)
        if statement:
            pf["statement"] = statement
        if kind:
            pf["kind"] = kind
        loc = {"kind": "text_lines", "start": span[0], "end": span[1]}
        return self.add_fact(loc, needle, notes=notes, **pf)

    def text(self) -> str:
        while self.lines and self.lines[-1] == "":
            self.lines.pop()
        return "\n".join(self.lines) + "\n"


# ---------------------------------------------------------------------------------------------
# Small rng helpers
# ---------------------------------------------------------------------------------------------

def pick(r: random.Random, seq: Sequence):
    return seq[r.randrange(len(seq))]


def picks(r: random.Random, seq: Sequence, k: int) -> list:
    k = min(k, len(seq))
    return r.sample(list(seq), k)


def clock(r: random.Random, lo: str = "08:05", hi: str = "17:55") -> str:
    h0, m0 = (int(x) for x in lo.split(":"))
    h1, m1 = (int(x) for x in hi.split(":"))
    t = r.randint(h0 * 60 + m0, h1 * 60 + m1)
    return f"{t // 60:02d}:{t % 60:02d}"


def later(r: random.Random, hhmm: str, lo: int = 7, hi: int = 95) -> str:
    return add_minutes(hhmm, r.randint(lo, hi))


def msgid(fid: str, k: int, domain: str) -> str:
    return f"<{util.stable_hash(fid, k, n=12)}.{k}@{domain}>"


# ---------------------------------------------------------------------------------------------
# Markdown helpers
# ---------------------------------------------------------------------------------------------

def md_row(cells: Sequence[str]) -> str:
    return "| " + " | ".join(str(c).replace("|", "/") for c in cells) + " |"


def md_table(doc: Doc, header: Sequence[str], rows: Sequence[Sequence[str]]) -> list[tuple[int, int]]:
    """Write a markdown table; returns the (line, line) span of every body row."""
    doc.line(md_row(header))
    doc.line("|" + "|".join("---" for _ in header) + "|")
    spans = []
    for r in rows:
        spans.append(doc.line(md_row(r)))
    doc.blank()
    return spans


def kv_table(doc: Doc, rows: Sequence[tuple[str, str]], bold: bool = True) -> list[tuple[int, int]]:
    doc.line("| | |")
    doc.line("|---|---|")
    spans = []
    for k, v in rows:
        kk = f"**{k}**" if bold else k
        spans.append(doc.line(md_row([kk, v])))
    doc.blank()
    return spans


def slug_title(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()

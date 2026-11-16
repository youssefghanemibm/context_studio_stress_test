"""Shared helpers for the guardrail / rejected-format generator.

Everything here is deterministic: randomness only from util.rng(key), dates only from the world.
"""
from __future__ import annotations

import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import datetime as _dt
import os
import re
import zipfile
from typing import Any, Iterable

from generators.common import util
from world.worldlib import load_world
from harness import extract as X

W = load_world()

LABEL = "SYNTHETIC GUARDRAIL PROBE – all personal data is fake"
COMPANY = W.company["legal_name"]          # Corvane Mutual Insurance Society Limited
COMPANY_SHORT = "Corvane Mutual"

GP_DIR = util.UPLOAD / "guardrail"
RJ_DIR = util.REJECTED


# ---------------------------------------------------------------------------------------------
# World access with exclusivity and time guards
# ---------------------------------------------------------------------------------------------

class GuardError(RuntimeError):
    pass


def guard(fid: str, ref: str, field: str | None = None) -> None:
    """Raise unless file ``fid`` may state ``ref#field`` (exclusivity rule, WORLD.md §3.1)."""
    if not W.may_state(fid, ref, field):
        raise GuardError(f"{fid} may not state {ref}#{field} (reserved for {W.is_exclusive(ref, field)[1]})")


def adate(fid: str) -> _dt.date:
    return _dt.date.fromisoformat(str(W.anchor(fid)["date"]))


def anchor(fid: str) -> dict:
    return W.anchor(fid)


def placement(fid: str, key: str | None = None) -> dict:
    pls = W.placements_for(fid)
    if key:
        pls = [p for p in pls if p["key"] == key]
    assert len(pls) == 1, (fid, key, pls)
    return pls[0]


class Person:
    """As-of view of a world person."""

    def __init__(self, fid: str, pid: str, d: _dt.date | str):
        guard(fid, pid, "name")
        self.pid = pid
        d = str(d)
        if not W.employed(pid, d):
            raise GuardError(f"{pid} not employed on {d} ({fid})")
        rec = W.people[pid]
        self.name = W.name_of(pid, d)
        self.title = W.title_of(pid, d)
        self.email = rec.get("email")
        self.phone = rec.get("phone")
        self.location = W.location_of(pid, d)
        self.first = self.name.split()[0]

    @property
    def initials(self) -> str:
        return "".join(p[0] for p in self.name.replace("-", " ").split())

    def __str__(self) -> str:
        return self.name


def system_name(fid: str, sid: str, d) -> str:
    guard(fid, sid, "name")
    return W.system_name(sid, str(d))


def loc_city(lid: str) -> str:
    return W.locations[lid]["city"]


# ---------------------------------------------------------------------------------------------
# Dates
# ---------------------------------------------------------------------------------------------

MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September",
          "October", "November", "December"]


def long_date(d: _dt.date) -> str:
    return f"{d.day} {MONTHS[d.month - 1]} {d.year}"


def dt_of(d: _dt.date, h: int = 9, m: int = 0) -> _dt.datetime:
    return _dt.datetime(d.year, d.month, d.day, h, m, 0)


# ---------------------------------------------------------------------------------------------
# Obviously-fake value generators (guardrail probes only)
# ---------------------------------------------------------------------------------------------

def luhn_valid(digits: str) -> bool:
    ds = [int(c) for c in digits if c.isdigit()]
    total = 0
    for i, dgt in enumerate(reversed(ds)):
        if i % 2 == 1:
            dgt *= 2
            if dgt > 9:
                dgt -= 9
        total += dgt
    return total % 10 == 0


def fake_card(r) -> str:
    """16 digits starting 0000 that FAIL the Luhn check, grouped in fours."""
    body = "0000" + "".join(str(r.randrange(10)) for _ in range(11))
    for last in r.sample(range(10), 10):
        cand = body + str(last)
        if not luhn_valid(cand):
            return " ".join(cand[i:i + 4] for i in range(0, 16, 4))
    raise AssertionError("unreachable")


def iban_mod97(iban: str) -> int:
    s = iban.replace(" ", "").upper()
    s = s[4:] + s[:4]
    num = "".join(str(ord(c) - 55) if c.isalpha() else c for c in s)
    return int(num) % 97


def fake_iban(r) -> str:
    """'XX' country code (not assigned) and a check sum that does not validate."""
    bban = "TEST" + "".join(str(r.randrange(10)) for _ in range(14))
    for _ in range(100):
        check = f"{r.randrange(100):02d}"
        iban = "XX" + check + bban
        if iban_mod97(iban) != 1:
            return " ".join(iban[i:i + 4] for i in range(0, len(iban), 4))
    raise AssertionError("unreachable")


def fake_ni(r, used: set) -> str:
    """UK NI number with the never-issued QQ prefix."""
    while True:
        v = f"QQ {r.randint(10, 99):02d} {r.randint(10, 99):02d} {r.randint(10, 99):02d} {r.choice('ABCD')}"
        if v not in used:
            used.add(v)
            return v


def fake_ssn9(r, used: set) -> str:
    """US-style number in the 9xx range (never issued as an SSN)."""
    while True:
        v = f"9{r.randint(0, 99):02d}-{r.randint(10, 99):02d}-{r.randint(1000, 9999):04d}"
        if v not in used:
            used.add(v)
            return v


def phone_555(r, used: set) -> str:
    while True:
        v = f"555-01{r.randint(0, 99):02d}"
        if v not in used:
            used.add(v)
            return v


# ---------------------------------------------------------------------------------------------
# Phrase banks (filler that never states world facts)
# ---------------------------------------------------------------------------------------------

def pick(r, options: list[str]) -> str:
    return options[r.randrange(len(options))]


# ---------------------------------------------------------------------------------------------
# Manifest facts
# ---------------------------------------------------------------------------------------------

class Facts:
    """Collects manifest entries for one file."""

    def __init__(self, fid: str, path: pathlib.Path):
        self.fid = fid
        self.path = pathlib.Path(path)
        self.items: list[dict] = []

    def add(self, kind: str, statement: str, locator: dict, needle: str, *, world_ref: str | None = None,
            exclusive: bool = False, pl: dict | None = None, notes: str | None = None,
            also_in: list[str] | None = None, **extra) -> dict:
        e: dict[str, Any] = {
            "fact_id": f"{self.fid}-F{len(self.items) + 1:03d}",
            "world_ref": world_ref,
            "kind": kind,
            "statement": statement,
            "file": util.rel(self.path),
            "locator": locator,
            "needle": needle,
            "exclusive": exclusive,
            "also_in": also_in or [],
        }
        if pl is not None:
            e["world_ref"] = pl["world_ref"]
            e["kind"] = pl["kind"]
            e["exclusive"] = bool(pl["exclusive"])
            e["placement"] = pl["placement_id"]
            e["placement_key"] = pl["key"]
            e["also_in"] = list(pl.get("also_in") or [])
        if notes:
            e["notes"] = notes
        e.update(extra)
        self.items.append(e)
        return e


# ---------------------------------------------------------------------------------------------
# Locating needles in generated files (so locators are computed, never hand-counted)
# ---------------------------------------------------------------------------------------------

def find_line(lines: list[str], needle: str, start: int = 1) -> int:
    """1-based number of the first line (>= start) whose text contains ``needle``."""
    for i, ln in enumerate(lines[start - 1:], start):
        if X.match(needle, ln):
            return i
    raise LookupError(f"needle {needle!r} not found in {len(lines)} lines")


def text_lines_of(path: pathlib.Path) -> list[str]:
    """Lines exactly as the extractor's text_lines locator numbers them."""
    path = pathlib.Path(path)
    if path.suffix.lower() in X.DERIVED_TEXT_EXTS:
        return X.derived_text(path).splitlines()
    with open(path, encoding="utf-8", newline="") as fh:
        return [ln.rstrip("\r\n") for ln in fh]


def line_loc(path: pathlib.Path, needle: str, context: int = 0, start: int = 1) -> dict:
    lines = text_lines_of(path)
    i = find_line(lines, needle, start)
    return {"kind": "text_lines", "start": max(1, i - context), "end": min(len(lines), i + context)}


def docx_para_index(path: pathlib.Path, needle: str) -> int:
    import docx
    doc = docx.Document(str(path))
    for i, p in enumerate(doc.paragraphs):
        if X.match(needle, X._wml_text(p._p)):
            return i
    raise LookupError(f"{needle!r} not in any paragraph of {path.name}")


def selfcheck(entries: Iterable[dict], allow_ocr: bool = False) -> list[str]:
    """Resolve every locator and match its needle; returns problems (OCR locators skipped)."""
    problems = []
    for e in entries:
        loc = e["locator"]
        if X.locator_needs_ocr(loc) and not allow_ocr:
            continue
        try:
            text = X.resolve(e["file"], loc, ocr=allow_ocr)
        except Exception as exc:  # noqa: BLE001
            problems.append(f"{e['fact_id']}: locator error {exc}")
            continue
        mode = "ocr_fuzzy" if X.locator_needs_ocr(loc) else "exact"
        if not X.match(e["needle"], text, mode):
            problems.append(f"{e['fact_id']}: needle {e['needle']!r} not in {text[:200]!r}")
    return problems


# ---------------------------------------------------------------------------------------------
# Zip / OOXML normalisation (byte-identical reruns)
# ---------------------------------------------------------------------------------------------

def normalize_zip(path: pathlib.Path, when: _dt.datetime, core_dt: _dt.datetime | None = None) -> None:
    """Rewrite a zip with fixed member timestamps; optionally pin docProps/core.xml dates."""
    path = pathlib.Path(path)
    with zipfile.ZipFile(path) as zin:
        members = [(i, zin.read(i.filename)) for i in zin.infolist()]
    tmp = path.with_name(path.name + ".tmp")
    stamp = (when.year, when.month, when.day, when.hour, when.minute, when.second)
    with zipfile.ZipFile(tmp, "w") as zout:
        for info, data in members:
            if core_dt is not None and info.filename == "docProps/core.xml":
                iso = core_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
                txt = data.decode("utf-8")
                txt = re.sub(r"(<dcterms:created[^>]*>)[^<]*(</dcterms:created>)", rf"\g<1>{iso}\g<2>", txt)
                txt = re.sub(r"(<dcterms:modified[^>]*>)[^<]*(</dcterms:modified>)", rf"\g<1>{iso}\g<2>", txt)
                data = txt.encode("utf-8")
            zi = zipfile.ZipInfo(info.filename, date_time=stamp)
            zi.compress_type = info.compress_type
            zi.external_attr = 0o644 << 16
            zi.create_system = 3
            zout.writestr(zi, data)
    os.replace(tmp, path)


def write_zip(path: pathlib.Path, members: list[tuple[str, bytes]], when: _dt.datetime,
              stored: set[str] | None = None) -> None:
    stamp = (when.year, when.month, when.day, when.hour, when.minute, when.second)
    stored = stored or set()
    with zipfile.ZipFile(path, "w") as z:
        for name, data in members:
            zi = zipfile.ZipInfo(name, date_time=stamp)
            zi.compress_type = zipfile.ZIP_STORED if name in stored else zipfile.ZIP_DEFLATED
            zi.external_attr = 0o644 << 16
            zi.create_system = 3
            z.writestr(zi, data)


def remove_own(folder: pathlib.Path, prefix: str) -> None:
    """Delete only our own files (``<prefix>NNN_*``) from a folder; never the folder itself."""
    folder.mkdir(parents=True, exist_ok=True)
    for p in folder.iterdir():
        if p.is_file() and re.match(rf"^{prefix}\d{{3}}_", p.name):
            p.unlink()

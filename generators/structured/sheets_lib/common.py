"""Shared plumbing for the ST001-ST026 generator: world access, facts collector, XLSX/CSV helpers.

Everything here is deterministic: randomness only via util.rng(key), no wall clock.
"""
from __future__ import annotations

import csv
import datetime as dt
import io
import math
import pathlib
import re
import zipfile
from typing import Any, Iterable

from generators.common import util
from world.worldlib import load_world

ROOT = util.ROOT
W = load_world()
FAMILY = "structured.sheets"
OUT_DEFAULT = util.UPLOAD / "structured"
MY_IDS = [f"ST{i:03d}" for i in range(1, 27)]
ZIP_DT = (2026, 11, 1, 9, 0, 0)

rng = util.rng


# ---------------------------------------------------------------------------------------------
# Dates
# ---------------------------------------------------------------------------------------------

def D(s: str | dt.date) -> dt.date:
    if isinstance(s, dt.datetime):
        return s.date()
    if isinstance(s, dt.date):
        return s
    return dt.date.fromisoformat(str(s)[:10])


def iso(d: dt.date | None) -> str:
    return d.isoformat() if d else ""


def add_bd(d: dt.date, n: int) -> dt.date:
    """Add n business days (Mon-Fri)."""
    step = 1 if n >= 0 else -1
    k = 0
    while k != n:
        d = d + dt.timedelta(days=step)
        if d.weekday() < 5:
            k += step
    return d


def next_weekday(d: dt.date) -> dt.date:
    while d.weekday() >= 5:
        d += dt.timedelta(days=1)
    return d


def first_bd_of_month(y: int, m: int) -> dt.date:
    return next_weekday(dt.date(y, m, 1))


def month_iter(start: dt.date, end: dt.date):
    y, m = start.year, start.month
    while (y, m) <= (end.year, end.month):
        yield y, m
        m += 1
        if m == 13:
            y, m = y + 1, 1


def fmt_money(x: float, dec: int = 2) -> str:
    return f"{x:,.{dec}f}"


def fmt_int(x: int) -> str:
    return f"{x:,}"


# ---------------------------------------------------------------------------------------------
# World helpers (as-of)
# ---------------------------------------------------------------------------------------------

def anchor(fid: str) -> dict:
    return W.anchor(fid)


def adate(fid: str) -> dt.date:
    return D(W.anchor(fid)["date"])


def pname(pid: str | None, d) -> str:
    if not pid:
        return ""
    return W.name_of(pid, iso(D(d)))


def ptitle(pid: str, d) -> str:
    return W.title_of(pid, iso(D(d))) or ""


def team_name(tid: str, d) -> str:
    return W.team_name(tid, iso(D(d)))


def sysname(sid: str, d) -> str:
    return W.system_name(sid, iso(D(d)))


def svcname(svc: str, d) -> str:
    return W.service_name(svc, iso(D(d)))


def may(fid: str, ref: str, field: str | None = None) -> bool:
    return W.may_state(fid, ref, field)


def require(fid: str, ref: str, field: str | None = None) -> None:
    if not W.may_state(fid, ref, field):
        raise AssertionError(f"{fid} may not state {ref}#{field}")


def program_id_asof(pid: str, d) -> str:
    """Program id as it was on date d (renamed_from before the rename date)."""
    p = W.programs[pid]
    rf = p.get("renamed_from")
    if rf and iso(D(d)) < rf["date"]:
        return rf["old_id"]
    return pid


def programs_asof(d) -> list[str]:
    ds = iso(D(d))
    return [pid for pid, p in W.programs.items() if p["since"] <= ds]


def table_exists(tname: str, d) -> bool:
    t = W.tables[tname]
    c = t.get("created")
    return not c or c <= iso(D(d))


_RENAME_CACHE: list[tuple[str, str, str]] | None = None


def _renames() -> list[tuple[str, str, str]]:
    global _RENAME_CACHE
    if _RENAME_CACHE is None:
        out = []
        for s in W.systems.values():
            for r in s.get("renames") or []:
                out.append((r["date"], r["to_name"], r["from_name"]))
        for s in W.services.values():
            for r in s.get("renames") or []:
                out.append((r["date"], r["to_name"], r["from_name"]))
        for pid, p in W.programs.items():
            rf = p.get("renamed_from")
            if rf:
                out.append((rf["date"], pid, rf["old_id"]))
        out.sort(key=lambda x: -len(x[1]))
        _RENAME_CACHE = out
    return _RENAME_CACHE


def temporalize(text: str, d) -> str:
    """Rewrite names that were renamed after date d back to their old names."""
    if not text:
        return text
    ds = iso(D(d))
    for date, new, old in _renames():
        if ds < date and new in text:
            text = re.sub(rf"(?<![A-Za-z0-9_-]){re.escape(new)}(?![A-Za-z0-9_])", old, text)
    return text


_RULE_RE = re.compile(r"BR-[A-Z]{2,5}-\d{3}")


def rule_known(rid: str, d) -> bool:
    r = W.rules.get(rid)
    if not r:
        return False
    ds = iso(D(d))
    for v in r["versions"]:
        if (v.get("approved_on") or "9999") <= ds or (v.get("effective_from") or "9999") <= ds:
            return True
    return False


_RULE_VER_RE = re.compile(r"(BR-[A-Z]{2,5}-\d{3})(?:@v| v)(\d+)")


def rule_version_known(rid: str, ver: int, d) -> bool:
    r = W.rules.get(rid)
    if not r or ver > len(r["versions"]):
        return False
    v = r["versions"][ver - 1]
    ds = iso(D(d))
    return (v.get("approved_on") or "9999") <= ds or (v.get("effective_from") or "9999") <= ds


def text_rules_known(text: str, d) -> bool:
    """True when every rule (and rule version) mentioned in the text existed on date d."""
    if not all(rule_known(r, d) for r in _RULE_RE.findall(text or "")):
        return False
    return all(rule_version_known(rid, int(v), d) for rid, v in _RULE_VER_RE.findall(text or ""))


def step_known(step: dict, d) -> bool:
    """A process step existed on date d unless every rule it applies was introduced later."""
    rules = step.get("rules") or []
    if not rules:
        return True
    for r in rules:
        if rule_known(r, d):
            return True
        # a newer rule that supersedes an older one keeps the step alive (e.g. BR-FRD-031 <- BR-FRD-012)
        for sup in W.rules[r].get("supersedes") or []:
            old = W.rules.get(sup["rule"])
            if old and rule_known(sup["rule"], d) and old["versions"][sup["version"] - 1]["status"] != "withdrawn":
                return True
    return False


# ---------------------------------------------------------------------------------------------
# Facts collector
# ---------------------------------------------------------------------------------------------

class Facts:
    def __init__(self, out_dir: pathlib.Path):
        self.out_dir = out_dir
        self.entries: list[dict] = []
        self.counters: dict[str, int] = {}
        self.links: dict[str, list[str]] = {}
        self.filenames: dict[str, str] = {}

    def path(self, fid: str) -> pathlib.Path:
        return self.out_dir / W.anchor(fid)["filename"]

    def rel(self, fid: str) -> str:
        return util.rel(self.path(fid))

    def add(self, fid: str, kind: str, statement: str, locator: dict, needle: str, *,
            world_ref: str | None = None, exclusive: bool = False, also_in: list[str] | None = None,
            placement: dict | None = None, notes: str | None = None, aggregate: dict | None = None,
            link: str | None = None, **extra) -> str:
        n = self.counters.get(fid, 0) + 1
        self.counters[fid] = n
        fact_id = f"{fid}-F{n:03d}"
        e = {"fact_id": fact_id, "world_ref": world_ref, "kind": kind, "statement": statement,
             "file": self.rel(fid), "locator": locator, "needle": needle, "exclusive": bool(exclusive),
             "also_in": list(also_in or [])}
        if placement:
            e["placement"] = placement["placement_id"]
            e["placement_key"] = placement["key"]
            if placement.get("contradictions"):
                e["contradictions"] = list(placement["contradictions"])
        if aggregate is not None:
            e["aggregate"] = aggregate
        if notes:
            e["notes"] = notes
        for k, v in extra.items():
            if v is not None:
                e[k] = v
        self.entries.append(e)
        if link:
            self.links.setdefault(link, []).append(fact_id)
        return fact_id

    def finish(self) -> list[dict]:
        byid = {e["fact_id"]: e for e in self.entries}
        for ids in self.links.values():
            for fid in ids:
                others = [x for x in ids if x != fid and x.split("-F")[0] != fid.split("-F")[0]]
                for o in others:
                    if o not in byid[fid]["also_in"]:
                        byid[fid]["also_in"].append(o)
        return self.entries


def placement(fid: str, key: str) -> dict:
    for p in W.placements_for(fid):
        if p["key"] == key:
            return p
    raise KeyError(f"no placement {key} for {fid}")


# ---------------------------------------------------------------------------------------------
# Phrase banks (filler: never states a world fact)
# ---------------------------------------------------------------------------------------------

CHANGE_BANK = {
    "generic": [
        "Initial draft for review", "Incorporated reviewer comments", "Formatting and column widths tidied",
        "Added filters and frozen header rows", "Corrected typos in descriptions", "Re-baselined after review",
        "Minor wording changes", "Aligned terminology with the programme glossary", "Added document control sheet",
        "Refreshed from source extract", "Clarified scope note", "Removed duplicate rows found in QA",
        "Sorted by identifier", "Added notes column", "Updated distribution list", "Final checks before issue",
        "Changed column order to match the source system", "Added summary sheet", "Spot-checked against source",
    ],
}

PURPOSE_BANK = [
    "This workbook is maintained for Programme Skerry and is the working reference for the scope described below.",
    "This document is a controlled reference for the CLARA replacement programme. Changes go through the owner listed below.",
    "Use this workbook as the reference for the subject described in the title. Raise questions with the owner.",
    "The workbook is issued under document control. Uncontrolled copies may be out of date.",
]

HANDLING_BANK = [
    "Internal - do not forward outside Corvane Mutual and the programme team.",
    "Internal use only. Contains operational detail.",
    "Internal. Share on a need-to-know basis.",
]


def pick(r, seq):
    return seq[r.randrange(len(seq))]


def version_history(fid: str, author: str, colleagues: list[str], n: int = 4) -> list[tuple[str, str, str, str]]:
    """[(version, date, author name, change)], ending at the anchor date with the anchor version."""
    r = rng(f"{fid}:vh")
    d_end = adate(fid)
    a = W.people[author]
    start_floor = D(a["employment"]["from"])
    span = r.randint(60, 300)
    d0 = max(start_floor, d_end - dt.timedelta(days=span))
    dates = sorted({d0 + dt.timedelta(days=r.randint(0, max(1, (d_end - d0).days - 1))) for _ in range(n - 1)})
    dates = [x for x in dates if x < d_end][: n - 1] + [d_end]
    bank = list(CHANGE_BANK["generic"])
    r.shuffle(bank)
    out = []
    major = 0
    minor = 1
    for i, d in enumerate(dates):
        if i == len(dates) - 1:
            major, minor = major + 1, 0
        ver = f"{major}.{minor}"
        who_pool = [author] + [c for c in colleagues if W.employed(c, iso(d))]
        who = author if i == len(dates) - 1 else pick(r, who_pool)
        change = "Issued" if i == len(dates) - 1 else bank[i % len(bank)]
        out.append((ver, iso(d), pname(who, d), change))
        minor += 1
    return out


def doc_version(fid: str) -> str:
    return "1.0"


# ---------------------------------------------------------------------------------------------
# XLSX helpers (openpyxl)
# ---------------------------------------------------------------------------------------------

def xl_styles():
    from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
    thin = Side(style="thin", color="B7C4CC")
    return {
        "title": Font(name="Calibri", size=14, bold=True, color="1F3A4D"),
        "subtitle": Font(name="Calibri", size=10, italic=True, color="4A5A66"),
        "hdr_font": Font(name="Calibri", size=10, bold=True, color="FFFFFF"),
        "hdr_fill": PatternFill("solid", fgColor="1F4E62"),
        "block_font": Font(name="Calibri", size=11, bold=True, color="1F3A4D"),
        "block_fill": PatternFill("solid", fgColor="D9E7EE"),
        "label_font": Font(name="Calibri", size=10, bold=True, color="1F3A4D"),
        "body": Font(name="Calibri", size=10),
        "wrap": Alignment(wrap_text=True, vertical="top"),
        "center": Alignment(horizontal="center", vertical="center", wrap_text=True),
        "left_mid": Alignment(horizontal="left", vertical="center", wrap_text=True),
        "border": Border(left=thin, right=thin, top=thin, bottom=thin),
    }


def new_workbook():
    from openpyxl import Workbook
    wb = Workbook()
    wb.remove(wb.active)
    return wb


def set_props(wb, fid: str, title: str | None = None, subject: str = "", keywords: str = ""):
    a = W.anchor(fid)
    d = adate(fid)
    when = dt.datetime(d.year, d.month, d.day, 9, 0, 0)
    p = wb.properties
    p.title = title or a["title"]
    p.creator = pname(a["author"], d)
    p.lastModifiedBy = pname(a["author"], d)
    p.subject = subject
    p.keywords = keywords
    p.created = when
    p.modified = when
    p.company = None
    p.description = a.get("description", "")[:0]


def print_setup(ws, fid: str, landscape: bool = True):
    a = W.anchor(fid)
    ws.oddHeader.left.text = "Corvane Mutual"
    ws.oddHeader.right.text = a["title"]
    ws.oddFooter.left.text = f"{a['file_id']} v{doc_version(fid)} - {a['date']}"
    ws.oddFooter.center.text = "Internal"
    ws.oddFooter.right.text = "Page &P of &N"
    if landscape:
        ws.page_setup.orientation = "landscape"
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 0
    ws.sheet_properties.pageSetUpPr.fitToPage = True


def write_title(ws, title: str, subtitle: str | None = None):
    S = xl_styles()
    ws["A1"] = title
    ws["A1"].font = S["title"]
    if subtitle:
        ws["A2"] = subtitle
        ws["A2"].font = S["subtitle"]


def write_header(ws, row: int, headers: list[str], col0: int = 1):
    S = xl_styles()
    for j, h in enumerate(headers):
        c = ws.cell(row=row, column=col0 + j, value=h)
        c.font = S["hdr_font"]
        c.fill = S["hdr_fill"]
        c.alignment = S["center"]
        c.border = S["border"]


def write_rows(ws, row0: int, rows: Iterable[list[Any]], col0: int = 1, wrap_cols: set[int] | None = None,
               date_fmt: str = "yyyy-mm-dd", border: bool = False) -> int:
    S = xl_styles()
    r = row0
    for rec in rows:
        for j, v in enumerate(rec):
            c = ws.cell(row=r, column=col0 + j, value=v)
            if isinstance(v, (dt.date, dt.datetime)):
                c.number_format = date_fmt
            if wrap_cols and (j + 1) in wrap_cols:
                c.alignment = S["wrap"]
            if border:
                c.border = S["border"]
        r += 1
    return r


def set_widths(ws, widths: list[float]):
    from openpyxl.utils import get_column_letter
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w


def col_letter(i: int) -> str:
    from openpyxl.utils import get_column_letter
    return get_column_letter(i)


def doc_control_sheet(wb, fid: str, purpose: str, scope: str, approvers: list[str], colleagues: list[str],
                      sources: list[str] | None = None, extra: list[tuple[str, str]] | None = None,
                      sheet_name: str = "Document Control"):
    """Standard first sheet. Returns the worksheet."""
    S = xl_styles()
    a = W.anchor(fid)
    d = adate(fid)
    r = rng(f"{fid}:dc")
    ws = wb.create_sheet(sheet_name)
    write_title(ws, a["title"], "Corvane Mutual Insurance Society Limited - Programme Skerry")
    rows = [
        ("Document title", a["title"]),
        ("Document reference", f"SKR-{a['file_id']}"),
        ("Version", doc_version(fid)),
        ("Status", a["status"].capitalize()),
        ("Date", d),
        ("Owner / author", f"{pname(a['author'], d)} ({ptitle(a['author'], d)})"),
        ("Classification", pick(r, HANDLING_BANK)),
    ]
    rows += list(extra or [])
    rr = 4
    for k, v in rows:
        ws.cell(row=rr, column=1, value=k).font = S["label_font"]
        c = ws.cell(row=rr, column=2, value=v)
        if isinstance(v, dt.date):
            c.number_format = "yyyy-mm-dd"
            c.alignment = xl_styles()["left_mid"]
        rr += 1
    rr += 1
    ws.cell(row=rr, column=1, value="Purpose").font = S["label_font"]
    ws.cell(row=rr, column=2, value=purpose).alignment = S["wrap"]
    rr += 1
    ws.cell(row=rr, column=1, value="Scope").font = S["label_font"]
    ws.cell(row=rr, column=2, value=scope).alignment = S["wrap"]
    rr += 1
    if sources:
        ws.cell(row=rr, column=1, value="Sources").font = S["label_font"]
        ws.cell(row=rr, column=2, value="; ".join(sources)).alignment = S["wrap"]
        rr += 1
    rr += 1
    ws.cell(row=rr, column=1, value="Version history").font = S["block_font"]
    rr += 1
    write_header(ws, rr, ["Version", "Date", "Author", "Change"])
    rr += 1
    for ver, vd, who, chg in version_history(fid, a["author"], colleagues):
        ws.cell(row=rr, column=1, value=ver)
        c = ws.cell(row=rr, column=2, value=D(vd))
        c.number_format = "yyyy-mm-dd"
        c.alignment = S["left_mid"]
        ws.cell(row=rr, column=3, value=who)
        ws.cell(row=rr, column=4, value=chg)
        rr += 1
    rr += 1
    ws.cell(row=rr, column=1, value="Approvals").font = S["block_font"]
    rr += 1
    write_header(ws, rr, ["Name", "Role", "Decision", "Date"])
    rr += 1
    for pid in approvers:
        ws.cell(row=rr, column=1, value=pname(pid, d))
        ws.cell(row=rr, column=2, value=ptitle(pid, d))
        ws.cell(row=rr, column=3, value="Approved" if a["status"] in ("approved", "final") else "Reviewed")
        c = ws.cell(row=rr, column=4, value=d)
        c.number_format = "yyyy-mm-dd"
        c.alignment = S["left_mid"]
        rr += 1
    set_widths(ws, [24, 70, 28, 40])
    print_setup(ws, fid, landscape=False)
    return ws


def approvers_for(fid: str, extra: list[str] | None = None) -> list[str]:
    a = W.anchor(fid)
    d = iso(adate(fid))
    out = []
    m = W.manager_of(a["author"], d)
    if m and W.employed(m, d):
        out.append(m)
    for p in extra or []:
        if p not in out and p != a["author"] and W.employed(p, d):
            out.append(p)
    return out


def colleagues_of(pid: str, d) -> list[str]:
    ds = iso(D(d))
    t = W.team_of(pid, ds)
    return [q for q in W.people if q != pid and W.team_of(q, ds) == t and W.employed(q, ds)]


# ---------------------------------------------------------------------------------------------
# Zip normalisation (byte-stable output) and CSV writing
# ---------------------------------------------------------------------------------------------

def finalize_ooxml(path: pathlib.Path, fid: str) -> None:
    """Rewrite the package with fixed zip timestamps and core.xml dates = the anchor date."""
    d = adate(fid)
    stamp = f"{d.isoformat()}T09:00:00Z"
    src = path.read_bytes()
    zin = zipfile.ZipFile(io.BytesIO(src))
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zout:
        for info in zin.infolist():
            data = zin.read(info.filename)
            if info.filename == "docProps/core.xml":
                txt = data.decode("utf-8")
                txt = re.sub(r"(<dcterms:created[^>]*>)[^<]*(</dcterms:created>)", rf"\g<1>{stamp}\g<2>", txt)
                txt = re.sub(r"(<dcterms:modified[^>]*>)[^<]*(</dcterms:modified>)", rf"\g<1>{stamp}\g<2>", txt)
                data = txt.encode("utf-8")
            zi = zipfile.ZipInfo(info.filename, date_time=ZIP_DT)
            zi.compress_type = zipfile.ZIP_DEFLATED
            zi.external_attr = 0o644 << 16
            zout.writestr(zi, data)
    path.write_bytes(buf.getvalue())


def write_csv(path: pathlib.Path, header: list[str], rows: list[list[Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(header)
        for rec in rows:
            w.writerow(["" if v is None else v for v in rec])


def csv_text(v: Any) -> str:
    """CSV-safe text: no semicolons or pipes (keeps the delimiter sniffer on commas)."""
    s = "" if v is None else str(v)
    return s.replace(";", ",").replace("|", "/")


def money(x: float) -> str:
    return f"{x:.2f}"

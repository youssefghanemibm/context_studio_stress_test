"""Small shared helpers: BMS labels, batch file DDs, user ids, enumerations from column text."""
from __future__ import annotations

import re

DENY_WORDS = {"SCOR", "SEB", "AIG", "AXA", "QBE", "FCA", "PRA", "KLP", "DNB", "AON", "IF", "LV",
              "TRYG", "EIKA", "CODAN", "SAGA", "CHUBB", "AEGON", "SAMPO", "COVEA"}

# CLARA user ids / initials used in maintenance histories (world people only)
AUTHOR_TAG = {"P023": "KBARR01", "P024": "PASHW01", "P016": "GP", "P025": "DO", "P026": "SV"}
AUTHOR_NAME = {"P023": "K. BARRACLOUGH", "P024": "P. ASHWORTH", "P016": "G. POCOCK", "P025": "D. OLLERTON"}
# first date each tag may sign a maintenance entry (employment / developer role)
AUTHOR_FROM = {"P023": "1996-03-11", "P024": "2004-09-06", "P016": "2001-10-01", "P025": "2002-01-14"}
AUTHOR_TO = {"P016": "2009-12-31"}


def bms_label(name: str, used: set) -> str:
    """BMS field label (<= 7 chars, no hyphens) for a world map field name."""
    parts = [p for p in name.upper().split("-") if p]
    cands = []
    joined = "".join(parts)
    if len(joined) <= 7:
        cands.append(joined)
    for n in (4, 3, 2):
        s = "".join(p[:n] for p in parts)
        if len(s) <= 7:
            cands.append(s)
    cands.append(joined[:7])
    for c in cands:
        if c not in used and c not in DENY_WORDS and not c[0].isdigit():
            used.add(c)
            return c
    for i in range(1, 99):
        c = joined[:5] + f"{i:02d}"
        if c not in used:
            used.add(c)
            return c
    raise ValueError(name)


def batch_files(prog: dict) -> list[dict]:
    """Sequential files a batch program uses (besides DB2): [{dd, dir, lrecl, desc}]."""
    pid = prog["id"]
    d = prog["description"].lower()
    files = [{"dd": "RPTOUT", "dir": "out", "lrecl": 133, "desc": "CONTROL REPORT", "sysout": True}]
    if pid == "CLRRS170":
        files.append({"dd": "RSVOUT", "dir": "out", "lrecl": 116, "desc": "RSVMOVE RECORDS (CLX-IF-042)",
                      "dsn": "CLR.PROD.RSVMOVE.DAILY(+1)"})
        return files
    special_in = {"CLRFR140": "AUTO-DECLINE CANDIDATE FILE", "CLRFR110": "SENTINEL BATCH SCORE RETURN",
                  "CLRST070": "SANCTIONS SCREENING RESULTS", "CLRRC050": "RECOVERY RECEIPTS FROM SUBTRAK",
                  "CLRGL030": "CURRENCY RATE FILE"}
    special_out = {"CLRFR110": "SENTINEL BATCH SCORING REQUEST", "CLRST070": "SANCTIONS SCREENING REQUESTS",
                   "CLRTR040": "SENTINEL PRE-SCREEN REQUEST FILE"}
    if pid in special_in or any(k in d for k in (" import", "confirmation", "synchronisation", " load ",
                                                 "snapshot refresh")):
        files.append({"dd": "IMPIN", "dir": "in", "lrecl": 400,
                      "desc": special_in.get(pid, "INBOUND INTERFACE FILE")})
    if pid in special_out or (any(k in d for k in ("extract", "export", "file", "batch build", "letter"))
                              and pid not in ("CLRRS160",)):
        files.append({"dd": "EXTOUT", "dir": "out", "lrecl": 400,
                      "desc": special_out.get(pid, "OUTBOUND EXTRACT FILE")})
    return files


_ENUM_PATTERNS = [
    re.compile(r"\(([A-Z0-9]{1,3}(?:\s*,\s*[A-Z0-9]{1,3})+)\)"),
]


def enum_values(desc: str, length: int) -> list[str]:
    """Code values listed in a column description, e.g. 'O open, C closed' -> ['O', 'C']."""
    if not desc:
        return []
    m = re.findall(r"\b([A-Z0-9]{%d}) [a-z][a-z-]*" % length, desc)
    if len(m) >= 2:
        return list(dict.fromkeys(m))
    for pat in _ENUM_PATTERNS:
        mm = pat.search(desc)
        if mm:
            vals = [v.strip() for v in mm.group(1).split(",")]
            if all(len(v) == length for v in vals) and len(vals) >= 2:
                return vals
    mm = re.search(r"\b(\d(?:/\d)+)\b", desc)
    if mm and length == 1:
        return mm.group(1).split("/")
    if desc.startswith("Y when") or " Y when" in desc or desc.startswith("Y once"):
        return ["Y", "N"]
    return []

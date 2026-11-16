"""Shared helpers for the world builder (deterministic; no wall clock)."""
from __future__ import annotations

import datetime as dt

from generators.common.util import rng  # noqa: F401  (re-exported)

TODAY = "2026-11-15"          # the world's "today"
LAST_DOC_DATE = "2026-11-12"  # newest document date allowed in the corpus
MODEL_START = "2021-01-04"    # reporting lines are modelled from this date
PROGRAMME = "Programme Skerry"

CORVANE = "ORG-CORVANE"
IBM = "ORG-IBM"
NISA = "REG-NISA"

CORVANE_DOMAIN = "corvane-mutual.example"
IBM_DOMAIN = "ibm-consulting.example"


def d(s: str) -> dt.date:
    return dt.date.fromisoformat(s)


def iso(x: dt.date) -> str:
    return x.isoformat()


def add_days(s: str, n: int) -> str:
    return iso(d(s) + dt.timedelta(days=n))


def day_before(s: str) -> str:
    return add_days(s, -1)


def in_range(date: str, frm: str | None, to: str | None) -> bool:
    if frm and date < frm:
        return False
    if to and date > to:
        return False
    return True


def periods(*pairs):
    """periods(("A", "2020-01-01"), ("B", "2023-01-01")) -> contiguous list of
    {value, from, to}; the last period is open-ended."""
    out = []
    for i, (val, frm) in enumerate(pairs):
        to = day_before(pairs[i + 1][1]) if i + 1 < len(pairs) else None
        out.append((val, frm, to))
    return out


def slug(s: str) -> str:
    out = []
    for ch in s.lower():
        if ch.isalnum() and ch.isascii():
            out.append(ch)
        else:
            out.append("_")
    s2 = "".join(out)
    while "__" in s2:
        s2 = s2.replace("__", "_")
    return s2.strip("_")[:60]


def fold(s: str) -> str:
    """ASCII-fold Nordic and Polish characters (Sørensen -> Sorensen)."""
    table = str.maketrans({
        "ø": "o", "Ø": "O", "å": "a", "Å": "A", "æ": "ae", "Æ": "Ae",
        "ä": "a", "Ä": "A", "ö": "o", "Ö": "O", "é": "e", "ó": "o", "ł": "l",
        "ś": "s", "ż": "z", "ź": "z", "ć": "c", "ń": "n", "ü": "u",
    })
    return s.translate(table)


def gbp(n) -> str:
    if isinstance(n, float) and not n.is_integer():
        return f"£{n:,.2f}"
    return f"£{int(n):,}"

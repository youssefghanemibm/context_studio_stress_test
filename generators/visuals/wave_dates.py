"""As-of helper for migration-wave cut-over dates.

The world dates when a wave's cut-over date became fixed through a decision that references the wave and
'confirms' its date (DEC-011 confirms MW-2 = 2027-02-15 on 2026-10-08). A document dated before that
decision shows the wave as 'early <year>, date to be confirmed' instead of the later date.
"""
from __future__ import annotations


def confirmed_from(W, wid: str) -> str | None:
    """ISO date from which the wave's cut-over date is known, or None when no decision fixes it later."""
    decs = [x for x in W.decisions.values() if wid in (x.get("refs") or []) and "confirmed" in x["statement"]]
    return min(str(x["date"]) for x in decs) if decs else None


def date_known(W, wid: str, d) -> bool:
    cf = confirmed_from(W, wid)
    return cf is None or str(d) >= cf


def tbc_label(W, wid: str, short: bool = False) -> str:
    year = str(W.waves[wid]["date"])[:4]
    return f"early {year} (TBC)" if short else f"early {year}, date to be confirmed"

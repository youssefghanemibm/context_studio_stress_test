"""Shared document control for the two renditions of each Claims organisation chart.

VS004 (pptx) and VS032 (docx) are renditions of the March 2024 chart; VS005 (pptx) and VS044 (pdf) are
renditions of the October 2025 chart. Each pair carries the same document reference, version and version
history, and the 2025 history continues the 2024 one (version 1.0 = the March 2024 chart).

The world model does not hold document references, so these values are corpus colour; they only have to be
consistent between the renditions.
"""
from __future__ import annotations

import datetime as _dt

_CHART_OF = {"VS004": "2024", "VS032": "2024", "VS005": "2025", "VS044": "2025"}

# history: (version, days before the chart's anchor date | "chart:<key>" for that chart's issue date, change)
_CHARTS = {
    "2024": {"doc_ref": "CLM-ORG-2024-03", "version": "1.0", "anchor": "VS004",
             "history": [("0.1", 31, "Outline and first content pages"),
                         ("0.2", 11, "Comments from the review cycle addressed"),
                         ("1.0", 0, "Approved for issue")]},
    "2025": {"doc_ref": "CLM-ORG-2025-10", "version": "2.0", "anchor": "VS005",
             "history": [("1.0", "chart:2024", "March 2024 chart"),
                         ("1.9", 25, "Draft for the September 2025 re-organisation"),
                         ("2.0", 0, "Issued as approved version")]},
}


def _anchor_date(W, key: str) -> _dt.date:
    return _dt.date.fromisoformat(str(W.anchor(_CHARTS[key]["anchor"])["date"]))


def control(W, fid: str) -> dict:
    """{doc_ref, version, history: [(version, iso date, change)] oldest first} for an org-chart rendition."""
    key = _CHART_OF[fid]
    c = _CHARTS[key]
    d = _anchor_date(W, key)
    assert str(W.anchor(fid)["date"]) == d.isoformat(), f"{fid} is not dated like its chart"
    hist = []
    for ver, when, change in c["history"]:
        if isinstance(when, str):
            iso = _anchor_date(W, when.split(":", 1)[1]).isoformat()
        else:
            iso = (d - _dt.timedelta(days=when)).isoformat()
        hist.append((ver, iso, change))
    return {"doc_ref": c["doc_ref"], "version": c["version"], "history": hist}

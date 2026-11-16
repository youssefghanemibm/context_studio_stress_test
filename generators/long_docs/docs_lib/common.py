"""Reusable document furniture: document control, version history, approvals, glossary, references."""
from __future__ import annotations

import datetime as _dt

from .core import Ctx, Doc, F, W, d, long_date, short_date


def minus_days(date: str, n: int) -> str:
    return (d(date) - _dt.timedelta(days=n)).isoformat()


def plus_days(date: str, n: int) -> str:
    return (d(date) + _dt.timedelta(days=n)).isoformat()


def as_of_person(pid: str, date: str) -> str:
    t = W.title_of(pid, date) or ""
    n = W.name_of(pid, date)
    return f"{n} ({t})" if t else n


def control_rows(ctx: Ctx, doc: Doc, *, owner: str | None = None, extra=None) -> list[list[str]]:
    a = ctx.anchor
    rows = [["Document title", doc.title], ["Document ID", doc.doc_id], ["Version", doc.version],
            ["Status", doc.status], ["Date", long_date(ctx.date)],
            ["Author", ctx.person(a["author"])]]
    if owner:
        rows.append(["Document owner", ctx.person(owner)])
    rows.append(["Classification", doc.classification])
    for k, v in (extra or []):
        rows.append([k, v])
    return rows


def version_history(ctx: Ctx, doc: Doc, versions: list[tuple[str, int, str]], caption="Version history",
                    authors: list[str] | None = None) -> None:
    """versions: (version, days_before_anchor, summary); the last entry is the current version (0 days)."""
    rows = []
    for i, (ver, back, summary) in enumerate(versions):
        when = minus_days(ctx.date, back)
        pid = (authors[i] if authors and i < len(authors) else ctx.anchor["author"])
        if not W.employed(pid, when):
            pid = ctx.anchor["author"]
        rows.append([ver, short_date(when), W.name_of(pid, when), summary])
    doc.table(["Version", "Date", "Author", "Summary of changes"], rows, widths=[1.7, 2.6, 3.7, 8.6],
              caption=caption, font_size=8.5)


def approvals(ctx: Ctx, doc: Doc, approvers: list[tuple[str, str]], date: str | None = None,
              caption="Approvals", facts=None, signature: bool = True) -> None:
    """approvers: (pid, role in the approval)."""
    date = date or ctx.date
    rows = []
    for pid, role in approvers:
        rows.append([W.name_of(pid, date), W.title_of(pid, date) or "", role, short_date(date),
                     "Approved (electronic)" if signature else ""])
    doc.table(["Name", "Title", "Role", "Date", "Signature"], rows, widths=[3.6, 4.6, 3.2, 2.4, 2.8],
              caption=caption, font_size=8.5, facts=facts)


def reviewers(ctx: Ctx, doc: Doc, pids: list[str], caption="Reviewers") -> None:
    rows = [[W.name_of(p, ctx.date), W.title_of(p, ctx.date) or "", ctx.team(W.team_of(p, ctx.date)) if W.team_of(p, ctx.date) else ""]
            for p in pids if W.employed(p, ctx.date)]
    doc.table(["Name", "Title", "Team"], rows, widths=[4.5, 6.5, 5.6], caption=caption, font_size=8.5)


def distribution(ctx: Ctx, doc: Doc, groups: list[str]) -> None:
    doc.p("Distribution: " + "; ".join(groups) + ".")


def glossary_terms(ids: list[str]) -> list[tuple[str, str]]:
    out = []
    for gid in ids:
        g = W.glossary[gid]
        out.append((g.get("canonical") or g.get("term"), g.get("definition", "")))
    return out


def glossary_section(doc: Doc, heading: str, terms: list[tuple[str, str]], level: int = 1) -> None:
    doc.h(level, heading)
    doc.table(["Term", "Meaning in this document"], [[t, m] for t, m in terms], widths=[4.6, 12.0],
              font_size=8.8)


def systems_table(ctx: Ctx, doc: Doc, sids: list[str], caption: str, cols=("System", "Type", "Owner")) -> None:
    rows = []
    for sid in sids:
        s = W.systems[sid]
        owner = s.get("owner")
        for oh in s.get("owner_history") or []:
            if (not oh.get("from") or ctx.date >= str(oh["from"])) and (not oh.get("to") or ctx.date <= str(oh["to"])):
                owner = oh["person"]
        rows.append([ctx.sys(sid), s["type"], ctx.name(owner) if owner and ctx.employed(owner) else "—"])
    doc.table(list(cols), rows, widths=[4.6, 7.2, 4.8], caption=caption, font_size=8.8)


def money_m(v: float) -> str:
    return f"£{v:,.1f}m"

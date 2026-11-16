"""Slides shared by every deck: agenda, document control, glossary, contacts, RACI helpers."""
from __future__ import annotations

import datetime as _dt

from . import phrases as P


def iso_minus(iso: str, days: int) -> str:
    return (_dt.date.fromisoformat(iso) - _dt.timedelta(days=days)).isoformat()


def asof_systems(W, text: str, d: str) -> str:
    """Rewrite current system names in undated world free text (committee remits etc.) to the names in
    force on date d, e.g. 'Sentinel thresholds' -> 'FRAUDNET thresholds' before 2025-03-01."""
    for sid, sysd in W.systems.items():
        if not sysd.get("renames"):
            continue
        cur, then = sysd["name"], W.system_name(sid, d)
        if cur != then and cur in text:
            text = text.replace(cur, then)
    return text


def agenda(deck, items: list[str], title: str = "Agenda", kicker: str | None = None, notes_topic="the agenda"):
    s = deck.content(title, kicker)
    n = len(items)
    cols = 1 if n <= 7 else 2
    per = (n + cols - 1) // cols
    for i, it in enumerate(items):
        c, r = divmod(i, per)
        x = 0.8 + c * 6.1
        y = 1.55 + r * 0.72
        s.box(x, y, 0.55, 0.55, str(i + 1), style="terminal", size=16, bold=True)
        s.text(x + 0.7, y + 0.04, 5.2, 0.5, [{"text": it}], size=16, color="ink", anchor="m")
    s.notes(P.notes(deck.rng, notes_topic, n_filler=1))
    return s


def doc_control(deck, history: list[tuple[str, str, str]], approvers: list[tuple[str, str]],
                status: str, owner_pid: str | None = None, reviewers: list[str] | None = None,
                distribution: str | None = None, title="Document control", approval_label="Approved",
                purpose: str | None = None):
    """history: [(version, iso date, description)] oldest first.
    approvers: [(pid, decision text)]."""
    s = deck.content(title, "About this document")
    owner_pid = owner_pid or deck.author_pid
    oname, otitle = deck.who(owner_pid)
    meta = [
        ("Document reference", deck.doc_ref), ("Version", deck.version), ("Status", status),
        ("Owner", f"{oname}, {otitle}"), ("Issue date", deck.date_long()),
        ("Classification", deck.classification),
    ]
    s.table(0.5, 1.45, 5.6, ["Field", "Value"], meta, col_w=[1.6, 3.4], row_h=0.36, size=10,
            first_col_bold=True)
    rows = [(h[0], deck.date_long(h[1]), h[3] if len(h) > 3 else deck.author, h[2]) for h in history]
    s.text(6.5, 1.3, 6.3, 0.3, [{"text": "Version history", "bold": True}], size=12, color="navy")
    s.table(6.5, 1.65, 6.3, ["Version", "Date", "Author", "Change"], rows, col_w=[0.8, 1.4, 1.6, 2.6],
            row_h=0.34, size=9)
    y = 1.65 + 0.34 * (len(rows) + 1) + 0.35
    s.text(6.5, y - 0.3, 6.3, 0.3, [{"text": "Approvals" if approvers else "Review", "bold": True}],
           size=12, color="navy")
    arows = []
    for pid, decision in approvers:
        n, t = deck.who(pid)
        arows.append((n, t, decision))
    if arows:
        s.table(6.5, y + 0.05, 6.3, ["Name", "Role", approval_label], arows, col_w=[1.6, 2.9, 1.8],
                row_h=0.34, size=9)
    lines = []
    if purpose:
        lines.append({"text": purpose, "size": 11})
    if reviewers:
        lines.append({"text": "Reviewed by: " + ", ".join(reviewers), "size": 10, "color": "slate"})
    if distribution:
        lines.append({"text": "Distribution: " + distribution, "size": 10, "color": "slate"})
    if lines:
        s.text(0.5, 4.0, 5.6, 2.8, lines, size=11, space_after=6)
    s.notes(P.notes(deck.rng, "the document control information", n_filler=1))
    return s


def history_rows(deck, finals: list[tuple[str, str]], spacing=(9, 30), kind="approved"):
    """finals: [(version, description or '')] oldest first; the last one is dated the anchor
    date. Earlier versions get earlier dates spaced by rng."""
    out = []
    d = deck.date
    dates = [d]
    for _ in finals[:-1]:
        d = iso_minus(d, deck.rng.randint(*spacing))
        dates.append(d)
    dates.reverse()
    for i, ((v, desc), dt) in enumerate(zip(finals, dates)):
        if not desc:
            if i == len(finals) - 1:
                desc = P.pick(deck.rng, P.HISTORY_FINAL[kind])
            elif i == 0:
                desc = P.pick(deck.rng, P.HISTORY_DRAFT)
            else:
                desc = P.pick(deck.rng, P.HISTORY_REVIEW)
        out.append((v, dt, desc))
    return out


def glossary(deck, terms: list[tuple[str, str]], title="Glossary", kicker="Reference"):
    s = deck.content(title, kicker)
    half = (len(terms) + 1) // 2
    for c, chunk in enumerate((terms[:half], terms[half:])):
        if not chunk:
            continue
        s.table(0.5 + c * 6.25, 1.45, 6.0, ["Term", "Meaning in this pack"], chunk, col_w=[1.7, 4.3],
                row_h=0.42, size=10, first_col_bold=True)
    s.notes(P.notes(deck.rng, "the terminology used in this pack", n_filler=1))
    return s


def contacts(deck, people: list[tuple[str, str]], title="Contacts", kicker="Reference"):
    """people: [(pid, role in this document)]."""
    W = deck.W
    rows = []
    for pid, role in people:
        p = W.people[pid]
        email = p.get("email")
        for h in p.get("email_history", []) or []:
            if (h.get("from") or "0000") <= deck.date <= (h.get("to") or "9999"):
                email = h["email"]
        n, t = deck.who(pid)
        loc = W.locations.get(W.location_of(pid, deck.date), {}).get("city", "")
        rows.append((n, t, role, loc, email))
    s = deck.content(title, kicker)
    s.table(0.5, 1.45, 12.3, ["Name", "Title", "Role for this document", "Location", "Email"], rows,
            col_w=[1.7, 2.9, 2.7, 1.1, 3.2], row_h=0.38, size=10, first_col_bold=True)
    s.notes(P.notes(deck.rng, "who to contact about this material", n_filler=1))
    return s


def team_names(W, ids, d):
    return ", ".join(W.team_name(t, d) for t in ids) if ids else "–"


def raci_rows(W, step_ids, d):
    rows = []
    for sid in step_ids:
        st = W.steps[sid]
        r = st["raci"]
        a = W.name_of(r["A"], d) if r.get("A") else "–"
        rows.append((sid, st["name"], team_names(W, r.get("R"), d), a, team_names(W, r.get("C"), d),
                     team_names(W, r.get("I"), d)))
    return rows

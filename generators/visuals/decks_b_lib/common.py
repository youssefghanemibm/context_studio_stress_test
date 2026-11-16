"""Shared deck-building helpers (people labels, document control, exclusivity guards)."""
from __future__ import annotations

from typing import Iterable, Sequence

from . import phrases as PH
from .core import CONTENT_LEFT, CONTENT_TOP, CONTENT_W, Deck, fmt_date, minus_days


def person(W, pid: str, d: str, with_title: bool = True) -> str:
    n = W.name_of(pid, d)
    if not with_title:
        return n
    return f"{n} ({W.title_of(pid, d)})"


def email(W, pid: str, d: str) -> str:
    p = W.people[pid]
    for h in p.get("email_history", []) or []:
        if (h.get("from") is None or str(h["from"]) <= d) and (h.get("to") is None or d <= str(h["to"])):
            return h["email"]
    return p.get("email", "")


def guard(W, fid: str, pairs: Iterable[tuple[str, str | None]]):
    """Raise if this file may not state one of the (entity_ref, field) pairs."""
    bad = [(r, f) for r, f in pairs if not W.may_state(fid, r, f)]
    if bad:
        raise RuntimeError(f"{fid}: exclusivity violation for {bad}")


def approvers(W, d: str, pids: Sequence[str], sign_date: str) -> list[tuple[str, str, str]]:
    out = []
    for pid in pids:
        assert W.employed(pid, d), (pid, d)
        out.append((W.name_of(pid, d), W.title_of(pid, d), fmt_date(sign_date, "short")))
    return out


def history(deck: Deck, authors: Sequence[str], spans: Sequence[int] = (24, 12, 4),
            notes: Sequence[str] | None = None, final_label: str | None = None) -> list[tuple[str, str, str, str]]:
    """Version history ending at the anchor date (dates are document metadata only)."""
    W, d, rng = deck.W, deck.date, deck.rng
    draft_notes = list(notes or [
        rng.choice(["Initial draft", "First draft for team review", "Outline and first content"]),
        rng.choice(["Review comments incorporated", "Updated after stakeholder walkthrough",
                    "Restructured after peer review"]),
        rng.choice(["Pre-approval review", "Final review edits", "Approver comments addressed"]),
    ])
    vers = ["0.1", "0.2", "0.9"][: len(spans)]
    rows = []
    for i, (v, sp) in enumerate(zip(vers, spans)):
        dd = minus_days(d, sp)
        a = authors[i % len(authors)]
        rows.append((v, fmt_date(dd, "short"), W.name_of(a, dd), draft_notes[i % len(draft_notes)]))
    st = deck.anchor.get("status", "final")
    lbl = final_label or ("Approved for distribution" if "approved" in st else "Issued (final)")
    rows.append((deck.version, fmt_date(d, "short"), W.name_of(deck.author_id, d), lbl))
    return rows


def risks_slide(deck: Deck, title: str = "Risks and mitigations", k: int = 5, extra: Sequence[tuple[str, str]] = ()):
    slide = deck.new_slide(title)
    rng = deck.rng
    rows = [["#", "Risk", "Mitigation", "Rating"]]
    picked = list(extra) + rng.sample(PH.RISKS, k)
    for i, (r, m) in enumerate(picked, 1):
        rows.append([str(i), r, m, rng.choice(["Amber", "Green", "Amber", "Red"])])
    deck.table(slide, rows, col_w=[0.4, 4.6, 5.6, 1.2], size=12, row_h=0.62, name="Risk register")
    return slide


def next_steps_slide(deck: Deck, extra: Sequence[str] = (), title: str = "Next steps", k: int = 4):
    slide = deck.new_slide(title)
    items = list(extra) + PH.pick(deck.rng, PH.NEXT_STEPS, k)
    deck.bullets(slide, items, size=17)
    return slide


def contacts_slide(deck: Deck, pids: Sequence[str], title: str = "Contacts", extra_rows=()):
    W, d = deck.W, deck.date
    slide = deck.new_slide(title)
    rows = [["Name", "Role", "Location", "Email"]]
    for pid in pids:
        loc = W.locations[W.location_of(pid, d)]["city"] if W.location_of(pid, d) in W.locations else ""
        rows.append([W.name_of(pid, d), W.title_of(pid, d), loc, email(W, pid, d)])
    rows += [list(r) for r in extra_rows]
    deck.table(slide, rows, col_w=[2.2, 3.8, 1.5, 4.5], size=12, row_h=0.5, name="Contacts")
    return slide


def glossary_slide(deck: Deck, terms: Sequence[tuple[str, str]], title: str = "Glossary"):
    slide = deck.new_slide(title)
    rows = [["Term", "Meaning"]] + [list(t) for t in terms]
    deck.table(slide, rows, col_w=[3.0, 9.2], size=12, row_h=0.44, name="Glossary")
    return slide

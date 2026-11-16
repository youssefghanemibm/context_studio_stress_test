"""Standard skeleton for the image-led DOCX files: cover, document control, contents, intro,
figure sections, glossary. Keeps the prose neutral (phrases.py) so image-only facts stay
image-only."""
from __future__ import annotations

from typing import Sequence

from generators.common import util

from . import phrases
from .core import fmt_date_long
from .ctx import W, adate, anchor, name, rel, title
from .docx_kit import DocBuilder
from .facts import Facts, spec


def start_doc(fid: str, facts: Facts, subtitle: str, doc_id: str, version: str, audience: str, topic: str,
              versions: Sequence[tuple], approvals: Sequence[tuple], distribution: Sequence[str],
              contents: Sequence[str], related: Sequence[str] = (), banner: str | None = None,
              intro_extra: Sequence[str] = (), keywords: str = "") -> DocBuilder:
    a = anchor(fid)
    d = adate(fid)
    r = util.rng(f"{fid}:prose")
    author = a["author"]
    b = DocBuilder(facts, a["title"], name(author, d), d, doc_id, version, a["status"],
                   subject=subtitle, keywords=keywords or topic)
    status = a["status"]
    b.cover(subtitle, f"Prepared by {name(author, d)}, {title(author, d)}",
            [("Document ID", doc_id), ("Version", version), ("Status", status.capitalize()),
             ("Date", fmt_date_long(d)), ("Owner", f"{name(author, d)} ({title(author, d)})"),
             ("Classification", "Corvane Internal")], banner=banner)
    b.document_control(versions, approvals, distribution, related)
    b.contents(contents)
    b.heading("1 Introduction", 1)
    aud = r.choice(phrases.AUDIENCE[audience])
    b.para(phrases.pick(r, phrases.PURPOSE, topic=topic, audience=aud))
    for s in intro_extra:
        b.para(s)
    b.heading("1.1 Scope", 2)
    b.para(r.choice(phrases.SCOPE_IN) + " " + r.choice(phrases.SCOPE_OUT))
    b.heading("1.2 How to read the figures", 2)
    picks = r.sample(phrases.READING, 2)
    b.para(" ".join(picks))
    b.heading("1.3 Maintenance", 2)
    b.para(r.choice(phrases.MAINTENANCE))
    # header / footer facts (document control metadata)
    b.header_fact(spec("header", f"The page header of {a['title']} names Corvane Mutual Insurance Society Limited "
                                 f"and the document title.", a["title"], f"ANCHOR:{fid}#title"))
    b.footer_fact(spec("footer", f"The page footer of {a['title']} shows document ID {doc_id}, version {version} "
                                 f"and the classification Corvane Internal.", doc_id, f"ANCHOR:{fid}#doc_id"))
    return b


def section(b: DocBuilder, fid: str, number: str, heading: str, what: str, extra: Sequence[str] = (),
            level: int = 1, page_break: bool = True) -> int:
    r = util.rng(f"{fid}:sec:{number}")
    if page_break:
        b.page_break()
    b.heading(f"{number} {heading}", level)
    i = b.para(phrases.fig_sentence(r, f"Figure {b.fig_no + 1}", what))
    for s in extra:
        b.para(s)
    return i


def glossary(b: DocBuilder, fid: str, number: str, terms: Sequence[tuple[str, str]]) -> None:
    r = util.rng(f"{fid}:gloss")
    b.page_break()
    b.heading(f"{number} Glossary", 1)
    b.para(r.choice(phrases.GLOSSARY_LEAD))
    b.table(["Term", "Meaning"], terms, widths_cm=[4, 13])


def versions_for(fid: str, author: str, steps: Sequence[tuple[int, str, str]], final_version: str) -> list[tuple]:
    """steps: (days_before_anchor, version, change). Last entry is the anchor date itself."""
    from .ctx import minus_days
    d = adate(fid)
    out = []
    for days, ver, change in steps:
        out.append((ver, minus_days(d, days), name(author, minus_days(d, days)), change))
    return out


def approval(role: str, pid: str, d: str, when: str | None = None) -> tuple:
    return (role, name(pid, d), title(pid, d), when or d)

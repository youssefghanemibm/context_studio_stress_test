"""World helpers, the document model and the fact registry shared by every builder."""
from __future__ import annotations

import datetime as _dt
import pathlib
import re
import sys
from dataclasses import dataclass, field
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from world.worldlib import load_world  # noqa: E402
from generators.common import util  # noqa: E402

W = load_world()
OUT_DIR = ROOT / "corpus" / "upload" / "long_docs"
CACHE = ROOT / "build" / "cache" / "ld_docs"
MANIFEST_NAME = "long_docs.docs"

MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September",
          "October", "November", "December"]


# ----------------------------------------------------------------------------------- dates / money

def d(s: str) -> _dt.date:
    return _dt.date.fromisoformat(str(s)[:10])


def long_date(s: str) -> str:
    x = d(s)
    return f"{x.day} {MONTHS[x.month - 1]} {x.year}"


def short_date(s: str) -> str:
    x = d(s)
    return f"{x.day:02d} {MONTHS[x.month - 1][:3]} {x.year}"


def gbp(v: float, dp: int = 0) -> str:
    if dp:
        return f"£{v:,.{dp}f}"
    return f"£{v:,.0f}"


# ----------------------------------------------------------------------------------- as-of naming

_RENAMES = [
    # (cutover date, new text, old text)
    # BR-RSV-012 v1 text names the reserve-engine revaluation run decided in ADR-028 (2026-03-09)
    ("2026-03-09", "; reserve-engine revaluation runs from Wave 2", ""),
    # the NISA-FR1 return exists only from NISA Circular 2026/04 (published 2025-11-20)
    ("2025-11-20", "TP2, FR1, CT1", "TP2, CT1"),
    ("2025-11-20", " (NISA-FR1 support)", ""),
    ("2025-11-03", "DOCSTOR / Evidence Vault", "DOCSTOR"),
    ("2025-11-03", "Evidence Vault (formerly DOCSTOR)", "DOCSTOR"),
    ("2025-11-03", "Evidence Vault", "DOCSTOR"),
    ("2025-03-01", "FRAUDNET/Sentinel", "FRAUDNET"),
    ("2025-03-01", "Sentinel (formerly FRAUDNET)", "FRAUDNET"),
    ("2025-03-01", "sentinel.corvane.internal", "fraudnet.corvane.internal"),
    ("2025-03-01", "Sentinel", "FRAUDNET"),
    ("2024-10-14", "MyCorvane Claims", "ClaimLine Web"),
    ("2025-09-01", "Assessor Portal", "Adjuster Extranet"),
    ("2026-02-10", "reserve-engine", "reserve-svc"),
    ("2026-02-10", "reserve.changed.v2", "reserve.changed.v1"),
]


def asof(text: str, date: str) -> str:
    """Rewrite current system/service names into the names in use on ``date``."""
    if not text:
        return text
    for cut, new, old in _RENAMES:
        if str(date) < cut and new in text:
            text = text.replace(new, old)
    return text


# ----------------------------------------------------------------------------------- per-doc context

class ExclusivityError(RuntimeError):
    pass


class Ctx:
    """Per-document helper bound to a file id and its anchor date."""

    def __init__(self, fid: str):
        self.fid = fid
        self.anchor = W.anchor(fid)
        self.date = str(self.anchor["date"])
        self.rng = util.rng(f"{fid}:main")
        self.placements = {p["key"]: p for p in W.placements_for(fid)}

    # people / teams / systems ------------------------------------------------------------
    def name(self, pid: str) -> str:
        return W.name_of(pid, self.date)

    def title(self, pid: str) -> str:
        return W.title_of(pid, self.date) or ""

    def person(self, pid: str) -> str:
        t = self.title(pid)
        return f"{self.name(pid)}, {t}" if t else self.name(pid)

    def email(self, pid: str) -> str:
        p = W.people[pid]
        for h in p.get("email_history", []) or []:
            frm, to = h.get("from"), h.get("to")
            if (not frm or self.date >= str(frm)) and (not to or self.date <= str(to)):
                return h["email"]
        return p.get("email", "")

    def employed(self, pid: str) -> bool:
        return W.employed(pid, self.date)

    def manager(self, pid: str) -> str | None:
        return W.manager_of(pid, self.date)

    def team(self, tid: str) -> str:
        return W.team_name(tid, self.date)

    def team_lead(self, tid: str) -> str | None:
        return W.team_lead(tid, self.date)

    def dept_of_team(self, tid: str) -> str | None:
        return W.team_department(tid, self.date)

    def dept(self, did: str) -> str:
        return W.departments[did]["name"]

    def sys(self, sid: str) -> str:
        return W.system_name(sid, self.date)

    def svc(self, name: str) -> str:
        return W.service_name(name, self.date)

    def a(self, text: str) -> str:
        return asof(text, self.date)

    def holder(self, alias: str) -> str | None:
        return W.alias_holder(alias, self.date)

    def rule(self, rid: str) -> dict | None:
        return W.rule_version(rid, self.date)

    # exclusivity -----------------------------------------------------------------------
    def ok(self, ref: str, fld: str | None = None) -> bool:
        return W.may_state(self.fid, ref, fld)

    def need(self, ref: str, fld: str | None = None) -> None:
        if not W.may_state(self.fid, ref, fld):
            raise ExclusivityError(f"{self.fid} may not state {ref}#{fld}")

    def pl(self, key: str) -> dict:
        return self.placements[key]


# ----------------------------------------------------------------------------------- facts

@dataclass
class Fact:
    kind: str
    statement: str
    needle: str
    world_ref: str | None = None
    exclusive: bool = False
    placement: str | None = None
    placement_key: str | None = None
    also_in: list = field(default_factory=list)
    notes: str | None = None
    where: Any = None          # None (block text) | (row, col) | 'footnote' | 'comment' | 'header' | 'footer' | 'image' | 'alt'
    locator: dict | None = None
    fact_id: str | None = None
    ocr: bool = False
    anchor_text: str | None = None

    def entry(self, file_rel: str) -> dict:
        e = {"fact_id": self.fact_id, "world_ref": self.world_ref, "kind": self.kind,
             "statement": self.statement, "file": file_rel, "locator": self.locator,
             "needle": self.needle, "exclusive": bool(self.exclusive), "also_in": list(self.also_in)}
        if self.placement:
            e["placement"] = self.placement
            e["placement_key"] = self.placement_key
        if self.notes:
            e["notes"] = self.notes
        return e


def F(kind: str, statement: str, needle: str, world_ref: str | None = None, *, where=None,
      exclusive: bool = False, notes: str | None = None, anchor: str | None = None) -> Fact:
    return Fact(kind=kind, statement=statement, needle=needle, world_ref=world_ref, where=where,
                exclusive=exclusive, notes=notes, anchor_text=anchor)


def PF(ctx: Ctx, key: str, needle: str, *, statement: str | None = None, where=None,
       notes: str | None = None, kind: str | None = None, anchor: str | None = None) -> Fact:
    """A fact for one of this file's placements (world_ref/exclusive/kind copied)."""
    p = ctx.pl(key)
    return Fact(kind=kind or p["kind"], statement=statement or p["fact"], needle=needle,
                world_ref=p["world_ref"], exclusive=bool(p.get("exclusive")),
                placement=p["placement_id"], placement_key=p["key"],
                also_in=list(p.get("also_in", []) or []), notes=notes, where=where, anchor_text=anchor)


# ----------------------------------------------------------------------------------- document model

@dataclass
class Block:
    kind: str
    data: dict
    facts: list = field(default_factory=list)


@dataclass
class Style:
    font: str = "Calibri"
    heading_font: str = "Calibri"
    size: float = 10.5
    accent: str = "1F3864"       # hex RGB
    accent2: str = "DCE6F2"      # table header shading
    serif: bool = False
    line_spacing: float = 1.12   # DOCX body line spacing
    pdf_leading: float = 1.38    # reportlab body leading factor


class Doc:
    def __init__(self, ctx: Ctx, *, title: str, doc_id: str, version: str, status: str,
                 classification: str = "Internal", subtitle: str = "", style: Style | None = None,
                 header_left: str | None = None, header_right: str | None = None,
                 footer_left: str | None = None, watermark: str | None = None,
                 landscape: bool = False):
        self.ctx = ctx
        self.fid = ctx.fid
        self.title = title
        self.subtitle = subtitle
        self.doc_id = doc_id
        self.version = version
        self.status = status
        self.classification = classification
        self.style = style or Style()
        self.header_left = header_left if header_left is not None else f"Corvane Mutual – {title}"
        self.header_right = header_right if header_right is not None else f"{doc_id} v{version}"
        self.footer_left = footer_left if footer_left is not None else f"Classification: {classification}"
        self.watermark = watermark
        self.landscape = landscape
        self.blocks: list[Block] = []
        self.header_facts: list[Fact] = []
        self.footer_facts: list[Fact] = []
        self.anchor = ctx.anchor
        self.date = ctx.date
        self.author = ctx.name(ctx.anchor["author"])
        self.headings: list[tuple[int, str]] = []

    # building ------------------------------------------------------------------------------
    def add(self, kind: str, facts=None, **data) -> Block:
        b = Block(kind, data, list(facts or []))
        self.blocks.append(b)
        return b

    def h(self, level: int, text: str, facts=None, page_break: bool = False) -> Block:
        self.headings.append((level, text))
        return self.add("heading", facts, level=level, text=text, page_break=page_break)

    def p(self, text: str, facts=None, *, style: str | None = None, footnote: str | None = None,
          footnote_facts=None, comment: dict | None = None, split_page_after: str | None = None,
          italic: bool = False, bold: bool = False, align: str | None = None, size: float | None = None,
          keep_next: bool = False) -> Block:
        return self.add("para", facts, text=text, style=style, footnote=footnote,
                        footnote_facts=list(footnote_facts or []), comment=comment,
                        split_page_after=split_page_after, italic=italic, bold=bold, align=align,
                        size=size, keep_next=keep_next)

    def ps(self, texts) -> None:
        for t in texts:
            self.p(t)

    def bullets(self, items, facts=None, numbered: bool = False) -> Block:
        return self.add("bullets", facts, items=list(items), numbered=numbered)

    def table(self, header, rows, *, widths=None, caption: str | None = None, facts=None,
              font_size: float | None = None, header_rows: int = 1, zebra: bool = False,
              first_col_bold: bool = False, align=None, caption_above: bool = True,
              kv: bool = False) -> Block:
        return self.add("table", facts, header=list(header) if header else None,
                        rows=[list(r) for r in rows], widths=widths, caption=caption,
                        font_size=font_size, header_rows=header_rows, zebra=zebra,
                        first_col_bold=first_col_bold, align=align, caption_above=caption_above,
                        kv=kv)

    def kv(self, pairs, *, widths=(5.0, 11.0), caption=None, facts=None, font_size=None) -> Block:
        return self.table(None, [[k, v] for k, v in pairs], widths=widths, caption=caption, facts=facts,
                          font_size=font_size, header_rows=0, first_col_bold=True, kv=True)

    def figure(self, path, caption: str, *, width_cm: float = 16.0, alt: str | None = None,
               facts=None) -> Block:
        return self.add("figure", facts, path=str(path), caption=caption, width_cm=width_cm, alt=alt)

    def pagebreak(self) -> Block:
        return self.add("pagebreak")

    def toc(self, depth: int = 2) -> Block:
        return self.add("toc", depth=depth)

    def note(self, text: str, facts=None, label: str = "Note") -> Block:
        return self.add("note", facts, text=text, label=label)

    def spacer(self, h_cm: float = 0.4) -> Block:
        return self.add("spacer", h=h_cm)

    def title_page(self, rows, facts=None, extra_lines=None) -> Block:
        return self.add("title_page", facts, rows=rows, extra_lines=list(extra_lines or []))

    # facts ------------------------------------------------------------------------------
    def all_facts(self) -> list[Fact]:
        out = list(self.header_facts) + list(self.footer_facts)
        for b in self.blocks:
            out.extend(b.facts)
            out.extend(b.data.get("footnote_facts", []) or [])
        return out


# ----------------------------------------------------------------------------------- misc helpers

def esc_xml(s: str) -> str:
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;"))


def norm(s: str) -> str:
    """Whitespace/quote/dash normalisation close to harness.extract.normalize (for self-checks)."""
    from harness import extract as X
    return X.normalize(s)


def slug_heading(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()

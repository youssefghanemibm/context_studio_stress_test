"""python-docx builder for image-led Corvane documents.

DocBuilder gives: cover page, document-control tables, numbered headings, short prose,
figures (picture + caption + alt text), Word tables, comments, header/footer with page
numbers, and records manifest facts with exact locators while building.
"""
from __future__ import annotations

import datetime as dt
import io
import pathlib
import zipfile
from typing import Sequence

import docx
from docx.enum.section import WD_ORIENT
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Inches, Pt, RGBColor

from generators.common import util

from .facts import Facts

NAVY = RGBColor(0x14, 0x32, 0x5C)
TEAL = RGBColor(0x0E, 0x7C, 0x7B)
GREY = RGBColor(0x5A, 0x66, 0x78)

ZIP_DT = (2026, 11, 1, 9, 0, 0)

OCR_KINDS = {"image_text", "image_table", "screenshot", "chart_only", "visual_only", "arrow_only", "lane_only",
             "contradiction_old", "contradiction_new", "temporal", "general", "terminology", "alias_use",
             "approved", "draft"}


def _set_cell_bg(cell, hex_fill: str) -> None:
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_fill)
    tcPr.append(shd)


def _add_field(run, instr: str, placeholder: str = "1") -> None:
    f1 = OxmlElement("w:fldChar")
    f1.set(qn("w:fldCharType"), "begin")
    it = OxmlElement("w:instrText")
    it.set(qn("xml:space"), "preserve")
    it.text = f" {instr} "
    f2 = OxmlElement("w:fldChar")
    f2.set(qn("w:fldCharType"), "separate")
    t = OxmlElement("w:t")
    t.text = placeholder
    f3 = OxmlElement("w:fldChar")
    f3.set(qn("w:fldCharType"), "end")
    for el in (f1, it, f2, t, f3):
        run._r.append(el)


class DocBuilder:
    def __init__(self, facts: Facts, title: str, author_name: str, date: str, doc_id: str, version: str,
                 status: str, classification: str = "Corvane Internal", subject: str = "",
                 landscape: bool = False, header_left: str = "Corvane Mutual Insurance Society Limited",
                 keywords: str = ""):
        self.facts = facts
        self.title = title
        self.date = date
        self.doc_id = doc_id
        self.version = version
        self.status = status
        self.classification = classification
        self.doc = docx.Document()
        self.fig_no = 0
        self.tab_no = 0
        self.image_count = 0
        d = self.doc
        util.set_core_props(d.core_properties, title, author_name, dt.date.fromisoformat(date),
                            subject=subject, keywords=keywords)
        sec = d.sections[0]
        sec.page_height, sec.page_width = Cm(29.7), Cm(21.0)
        if landscape:
            sec.orientation = WD_ORIENT.LANDSCAPE
            sec.page_height, sec.page_width = Cm(21.0), Cm(29.7)
        sec.left_margin = sec.right_margin = Cm(2.0)
        sec.top_margin, sec.bottom_margin = Cm(2.2), Cm(2.0)
        sec.header_distance = sec.footer_distance = Cm(1.0)
        st = d.styles
        st["Normal"].font.name = "Arial"
        st["Normal"].font.size = Pt(10.5)
        st["Normal"].paragraph_format.space_after = Pt(6)
        for lvl, sz in ((1, 16), (2, 13), (3, 11.5)):
            hs = st[f"Heading {lvl}"]
            hs.font.name = "Arial"
            hs.font.size = Pt(sz)
            hs.font.color.rgb = NAVY if lvl < 3 else TEAL
            hs.font.bold = True
        st["Caption"].font.name = "Arial"
        st["Caption"].font.size = Pt(9)
        st["Caption"].font.italic = True
        st["Caption"].font.color.rgb = GREY
        st["Title"].font.name = "Arial"
        st["Title"].font.color.rgb = NAVY
        # header / footer
        hdr = sec.header.paragraphs[0]
        hdr.text = ""
        r = hdr.add_run(f"{header_left}  |  {title}")
        r.font.size = Pt(8.5)
        r.font.color.rgb = GREY
        ftr = sec.footer.paragraphs[0]
        ftr.text = ""
        r = ftr.add_run(f"{doc_id}  ·  Version {version}  ·  {classification}  ·  Page ")
        r.font.size = Pt(8.5)
        r.font.color.rgb = GREY
        r2 = ftr.add_run()
        r2.font.size = Pt(8.5)
        _add_field(r2, "PAGE", "1")
        r3 = ftr.add_run(" of ")
        r3.font.size = Pt(8.5)
        r4 = ftr.add_run()
        r4.font.size = Pt(8.5)
        _add_field(r4, "NUMPAGES", "1")
        self.header_text = f"{header_left}  |  {title}"
        self.footer_text = f"{doc_id}  ·  Version {version}  ·  {classification}"

    # ---------------------------------------------------------------- indices
    def _pidx(self) -> int:
        return len(self.doc.paragraphs)

    @property
    def text_width_in(self) -> float:
        sec = self.doc.sections[0]
        return (sec.page_width - sec.left_margin - sec.right_margin) / 914400

    # ---------------------------------------------------------------- blocks
    def page_break(self) -> None:
        p = self.doc.add_paragraph()
        p.add_run().add_break(WD_BREAK.PAGE)

    def heading(self, text: str, level: int = 1) -> int:
        i = self._pidx()
        self.doc.add_heading(text, level)
        return i

    def para(self, text: str, fact: dict | None = None, bold_lead: str | None = None, italic: bool = False,
             size: float | None = None, align: str | None = None, color=None) -> int:
        i = self._pidx()
        p = self.doc.add_paragraph()
        if bold_lead:
            rb = p.add_run(bold_lead)
            rb.bold = True
        r = p.add_run(text)
        r.italic = italic
        if size:
            r.font.size = Pt(size)
        if color is not None:
            r.font.color.rgb = color
        if align == "center":
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        if fact:
            self._add_fact(fact, {"kind": "docx_para", "para_index": i, "section": self._last_heading(),
                                  "page_hint": None})
        return i

    def bullets(self, items: Sequence[str]) -> list[int]:
        out = []
        for it in items:
            out.append(self._pidx())
            self.doc.add_paragraph(it, style="List Bullet")
        return out

    def _last_heading(self) -> str | None:
        for p in reversed(self.doc.paragraphs):
            if p.style is not None and p.style.name.startswith("Heading") and p.text.strip():
                return p.text.strip()
        return None

    def table(self, headers: Sequence[str], rows: Sequence[Sequence[str]], widths_cm: Sequence[float] | None = None,
              caption: str | None = None, facts: Sequence[tuple[int, int, dict]] = (), header_fill: str = "1F4E8C",
              font_size: float = 9) -> int:
        ti = len(self.doc.tables)
        t = self.doc.add_table(rows=1 + len(rows), cols=len(headers))
        t.style = "Table Grid"
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        for j, h in enumerate(headers):
            c = t.rows[0].cells[j]
            c.text = ""
            run = c.paragraphs[0].add_run(h)
            run.bold = True
            run.font.size = Pt(font_size)
            run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
            _set_cell_bg(c, header_fill)
        for i, row in enumerate(rows, start=1):
            for j, v in enumerate(row):
                c = t.rows[i].cells[j]
                c.text = ""
                run = c.paragraphs[0].add_run(str(v))
                run.font.size = Pt(font_size)
        if widths_cm:
            for row in t.rows:
                for j, w in enumerate(widths_cm):
                    row.cells[j].width = Cm(w)
        for (r, ccol, f) in facts:
            self._add_fact(f, {"kind": "docx_table", "table_index": ti, "row": r, "col": ccol})
        if caption:
            self.tab_no += 1
            p = self.doc.add_paragraph(f"Table {self.tab_no} – {caption}", style="Caption")
        return ti

    def figure(self, png: bytes, caption: str, alt: str, width_in: float | None = None,
               facts: Sequence[dict] = (), alt_title: str | None = None) -> dict:
        """Insert a picture with caption and alt text. Facts with kind alt_text get a docx_alt_text
        locator; all others get a docx_image (ocr) locator."""
        self.fig_no += 1
        w = Inches(width_in or self.text_width_in)
        p = self.doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run()
        shape = run.add_picture(io.BytesIO(png), width=w)
        inline = shape._inline
        inline.docPr.set("descr", alt)
        if alt_title:
            inline.docPr.set("title", alt_title)
        inline.docPr.set("name", f"Figure {self.fig_no}")
        rid = inline.graphic.graphicData.pic.blipFill.blip.embed
        part = self.doc.part.related_parts[rid]
        image_name = str(part.partname).lstrip("/")
        image_index = self.image_count
        self.image_count += 1
        cap_text = f"Figure {self.fig_no} – {caption}"
        cap_idx = self._pidx()
        self.doc.add_paragraph(cap_text, style="Caption").alignment = WD_ALIGN_PARAGRAPH.CENTER
        for f in facts:
            if f["kind"] == "alt_text" or f.get("where") == "alt":
                loc = {"kind": "docx_alt_text", "image_index": image_index}
            elif f.get("where") == "caption":
                loc = {"kind": "docx_para", "para_index": cap_idx, "section": self._last_heading(), "page_hint": None}
            else:
                loc = {"kind": "docx_image", "image_name": image_name, "ocr": True}
            self._add_fact(f, loc)
        return {"image_name": image_name, "image_index": image_index, "figure": self.fig_no,
                "caption_index": cap_idx}

    def comment_on_last(self, text: str, author: str, initials: str, date: str, fact: dict | None = None,
                        para_text: str | None = None) -> int:
        """Anchor a comment on a new short paragraph (or the given text) and return the comment id."""
        p = self.doc.add_paragraph()
        r = p.add_run(para_text or "")
        c = self.doc.add_comment([r], text=text, author=author, initials=initials)
        c._comment_elm.set(qn("w:date"), f"{date}T10:00:00Z")
        if fact:
            self._add_fact(fact, {"kind": "docx_comment", "comment_id": int(c.comment_id)})
        return int(c.comment_id)

    def comment_on_para(self, para_index: int, text: str, author: str, initials: str, date: str,
                        fact: dict | None = None) -> int:
        p = self.doc.paragraphs[para_index]
        runs = p.runs or [p.add_run("")]
        c = self.doc.add_comment(runs, text=text, author=author, initials=initials)
        c._comment_elm.set(qn("w:date"), f"{date}T10:00:00Z")
        if fact:
            self._add_fact(fact, {"kind": "docx_comment", "comment_id": int(c.comment_id)})
        return int(c.comment_id)

    def header_fact(self, fact: dict) -> None:
        self._add_fact(fact, {"kind": "docx_header", "section_index": 0})

    def footer_fact(self, fact: dict) -> None:
        self._add_fact(fact, {"kind": "docx_footer", "section_index": 0})

    def _add_fact(self, f: dict, loc: dict) -> None:
        loc = {k: v for k, v in loc.items() if v is not None}
        self.facts.add(f["kind"], f["statement"], f["needle"], loc, world_ref=f.get("world_ref"),
                       exclusive=f.get("exclusive", False), placement=f.get("placement"),
                       placement_key=f.get("placement_key"), also_in=f.get("also_in"), notes=f.get("notes"))

    # ---------------------------------------------------------------- standard front matter
    def cover(self, subtitle: str, owner_line: str, meta_rows: Sequence[tuple[str, str]], banner: str | None = None) -> None:
        d = self.doc
        for _ in range(3):
            d.add_paragraph()
        p = d.add_paragraph()
        r = p.add_run("CORVANE MUTUAL")
        r.bold = True
        r.font.size = Pt(12)
        r.font.color.rgb = TEAL
        p = d.add_paragraph()
        r = p.add_run(self.title)
        r.bold = True
        r.font.size = Pt(26)
        r.font.color.rgb = NAVY
        p = d.add_paragraph()
        r = p.add_run(subtitle)
        r.font.size = Pt(13)
        r.font.color.rgb = GREY
        if banner:
            p = d.add_paragraph()
            r = p.add_run(banner)
            r.bold = True
            r.font.size = Pt(11)
            r.font.color.rgb = RGBColor(0xB3, 0x26, 0x1E)
        d.add_paragraph()
        t = d.add_table(rows=len(meta_rows), cols=2)
        t.style = "Table Grid"
        for i, (k, v) in enumerate(meta_rows):
            c0, c1 = t.rows[i].cells
            c0.text, c1.text = "", ""
            rk = c0.paragraphs[0].add_run(k)
            rk.bold = True
            rk.font.size = Pt(9.5)
            _set_cell_bg(c0, "E3EDF9")
            rv = c1.paragraphs[0].add_run(v)
            rv.font.size = Pt(9.5)
            c0.width, c1.width = Cm(5), Cm(11)
        d.add_paragraph()
        p = d.add_paragraph()
        r = p.add_run(owner_line)
        r.font.size = Pt(9)
        r.font.color.rgb = GREY
        self.page_break()

    def document_control(self, versions: Sequence[tuple[str, str, str, str]],
                         approvals: Sequence[tuple[str, str, str, str]], distribution: Sequence[str],
                         related: Sequence[str] = ()) -> None:
        self.heading("Document control", 1)
        self.para("Version history", bold_lead="")
        self.table(["Version", "Date", "Author", "Change"], versions, widths_cm=[2, 2.8, 4, 8])
        self.doc.add_paragraph()
        self.para("Review and approval")
        self.table(["Role", "Name", "Title", "Date"], approvals, widths_cm=[3, 4, 6.5, 3])
        self.doc.add_paragraph()
        self.para("Distribution: " + "; ".join(distribution))
        if related:
            self.para("Related documents: " + "; ".join(related))
        self.page_break()

    def contents(self, entries: Sequence[str]) -> None:
        self.heading("Contents", 1)
        for e in entries:
            self.doc.add_paragraph(e)
        self.page_break()

    # ---------------------------------------------------------------- save
    def save(self, path: pathlib.Path) -> None:
        buf = io.BytesIO()
        self.doc.save(buf)
        write_normalised_zip(buf.getvalue(), path)


def write_normalised_zip(data: bytes, path: pathlib.Path) -> None:
    """Rewrite an OOXML package with fixed member timestamps (byte-stable output)."""
    src = zipfile.ZipFile(io.BytesIO(data))
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for info in src.infolist():
            zi = zipfile.ZipInfo(info.filename, date_time=ZIP_DT)
            zi.compress_type = zipfile.ZIP_DEFLATED
            zi.external_attr = 0o600 << 16
            z.writestr(zi, src.read(info.filename))
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(out.getvalue())

"""Render a declarative manual spec (list of blocks) into a real Word document.

Block types (dicts with key 't'):
  title_page  {lines: [(text, size, bold)], ...}
  h1/h2/h3    {text, break?: bool, seg?: id}
  p           {text | runs, style?, facts?, comment?, align?, size?, indent?}
                run dict: {text, bold?, italic?, break?: 'page', footnote?: {text, fact?},
                           del?: text, ins?: text, author?, date?}
  table       {header, rows, widths?, caption?, facts?: [{row, col, ...fact}], size?, repeat_header?}
  figure      {png, caption, alt, width_in?, facts?: [...], alt_facts?: [...]}
  toc         {}
  fill        {seg}
  section     {}            (new docx section, next page; header/footer linked to previous)
  pagebreak   {}

Facts are dicts carrying manifest fields; the builder fills in the 'locator' after rendering.
"""
from __future__ import annotations

import copy
import datetime as dt
import io
import pathlib
import re
import zipfile

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.opc.constants import RELATIONSHIP_TYPE as RT
from docx.opc.packuri import PackURI
from docx.opc.part import Part
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls, qn
from docx.shared import Cm, Inches, Pt, RGBColor
from lxml import etree

from generators.common import util

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
FOOTNOTES_CT = "application/vnd.openxmlformats-officedocument.wordprocessingml.footnotes+xml"


def _esc(s: str) -> str:
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;"))


class Rendered:
    """Result of a render: path, facts with locators, and helper info for page mapping."""

    def __init__(self):
        self.facts: list[dict] = []
        self.seg_markers: dict[str, dict] = {}   # seg -> {kind: heading|text, text}
        self.headings: list[tuple[int, str]] = []  # (level, text) in order
        self.images: list[dict] = []
        self.n_tables = 0
        self.n_footnotes = 0
        self.n_comments = 0


class ManualBuilder:
    def __init__(self, cfg: dict):
        """cfg: header, footer_prefix, font, size, author_name, date, title, subject, tracked_id_base."""
        self.cfg = cfg

    # ------------------------------------------------------------------ styles
    def _setup(self, doc):
        cfg = self.cfg
        st = doc.styles
        normal = st["Normal"]
        normal.font.name = cfg.get("font", "Arial")
        normal.font.size = Pt(cfg.get("size", 11))
        rpr = normal.element.get_or_add_rPr()
        rfonts = rpr.find(qn("w:rFonts"))
        if rfonts is None:
            rfonts = parse_xml(f'<w:rFonts {nsdecls("w")}/>')
            rpr.append(rfonts)
        for a in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
            rfonts.set(qn(a), cfg.get("font", "Arial"))
        normal.paragraph_format.space_after = Pt(6)
        normal.paragraph_format.line_spacing = 1.08
        heading_sizes = {1: 17, 2: 13.5, 3: 11.5}
        for lvl, sz in heading_sizes.items():
            h = st[f"Heading {lvl}"]
            h.font.name = cfg.get("font", "Arial")
            h.font.size = Pt(sz)
            h.font.bold = True
            h.font.italic = False
            h.font.color.rgb = RGBColor(*cfg.get("heading_rgb", (0x1F, 0x3A, 0x5F)))
            hr = h.element.get_or_add_rPr()
            hf = hr.find(qn("w:rFonts"))
            if hf is None:
                hf = parse_xml(f'<w:rFonts {nsdecls("w")}/>')
                hr.append(hf)
            for a in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
                hf.set(qn(a), cfg.get("font", "Arial"))
            for a in ("w:asciiTheme", "w:hAnsiTheme", "w:cstheme", "w:eastAsiaTheme"):
                if hf.get(qn(a)) is not None:
                    del hf.attrib[qn(a)]
            h.paragraph_format.space_before = Pt({1: 6, 2: 12, 3: 9}[lvl])
            h.paragraph_format.space_after = Pt({1: 12, 2: 6, 3: 4}[lvl])
            h.paragraph_format.keep_with_next = True
        cap = st["Caption"]
        cap.font.size = Pt(9.5)
        cap.font.italic = True
        cap.font.bold = False
        cap.font.color.rgb = RGBColor(0x33, 0x33, 0x33)
        # footnote styles
        fn = st.add_style("footnote text", WD_STYLE_TYPE.PARAGRAPH)
        fn.base_style = normal
        fn.font.size = Pt(9)
        fn.paragraph_format.space_after = Pt(0)
        fr = st.add_style("footnote reference", WD_STYLE_TYPE.CHARACTER)
        fr.font.superscript = True
        self.fn_text_id, self.fn_ref_id = fn.style_id, fr.style_id
        # TOC styles
        th = st.add_style("Contents Title", WD_STYLE_TYPE.PARAGRAPH)
        th.base_style = normal
        th.font.size = Pt(16)
        th.font.bold = True
        th.font.color.rgb = RGBColor(*cfg.get("heading_rgb", (0x1F, 0x3A, 0x5F)))
        th.paragraph_format.space_after = Pt(12)
        for lvl in (1, 2):
            t = st.add_style(f"toc {lvl}", WD_STYLE_TYPE.PARAGRAPH)
            t.base_style = normal
            t.font.size = Pt(10 if lvl == 1 else 9.5)
            t.font.bold = (lvl == 1)
            t.paragraph_format.space_after = Pt(1 if lvl == 2 else 3)
            t.paragraph_format.space_before = Pt(3 if lvl == 1 else 0)
            t.paragraph_format.left_indent = Cm(0 if lvl == 1 else 0.8)
        self.toc_ids = {1: st["toc 1"].style_id, 2: st["toc 2"].style_id, "h": th.style_id}
        # small table text
        tt = st.add_style("Table Text", WD_STYLE_TYPE.PARAGRAPH)
        tt.base_style = normal
        tt.font.size = Pt(9)
        tt.paragraph_format.space_after = Pt(1)
        tt.paragraph_format.line_spacing = 1.0
        bq = st.add_style("Box Text", WD_STYLE_TYPE.PARAGRAPH)
        bq.base_style = normal
        bq.font.size = Pt(10)
        bq.font.italic = True
        bq.paragraph_format.left_indent = Cm(0.8)
        bq.paragraph_format.right_indent = Cm(0.8)

    def _section_layout(self, sec):
        sec.page_height = Cm(29.7)
        sec.page_width = Cm(21.0)
        sec.top_margin = Cm(2.4)
        sec.bottom_margin = Cm(2.3)
        sec.left_margin = Cm(2.3)
        sec.right_margin = Cm(2.3)
        sec.header_distance = Cm(1.1)
        sec.footer_distance = Cm(1.0)

    def _header_footer(self, sec):
        cfg = self.cfg
        hp = sec.header.paragraphs[0]
        hp.text = ""
        r = hp.add_run(cfg["header"])
        r.font.size = Pt(9)
        r.font.color.rgb = RGBColor(0x22, 0x22, 0x22)
        hp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        pPr = hp._p.get_or_add_pPr()
        pPr.append(parse_xml(f'<w:pBdr {nsdecls("w")}><w:bottom w:val="single" w:sz="6" w:space="1" w:color="808080"/></w:pBdr>'))
        fp = sec.footer.paragraphs[0]
        fp.text = ""
        fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = fp.add_run(cfg["footer_prefix"] + "   |   Page ")
        r.font.size = Pt(9)
        for instr in ("PAGE", "NUMPAGES"):
            fld = parse_xml(f'<w:fldSimple {nsdecls("w")} w:instr=" {instr} "><w:r><w:rPr><w:sz w:val="18"/></w:rPr>'
                            f'<w:t>1</w:t></w:r></w:fldSimple>')
            fp._p.append(fld)
            if instr == "PAGE":
                r2 = fp.add_run(" of ")
                r2.font.size = Pt(9)

    # ------------------------------------------------------------------ main
    def render(self, blocks: list[dict], pools: dict, params: dict, out_path: pathlib.Path,
               toc_pages: dict | None = None) -> Rendered:
        cfg = self.cfg
        blocks = copy.deepcopy(blocks)
        units0 = params.get("units", {})
        pools = {k: copy.deepcopy(v[:int(units0.get(k, 0))]) for k, v in pools.items()}
        doc = Document()
        self._setup(doc)
        sec0 = doc.sections[0]
        self._section_layout(sec0)
        self._header_footer(sec0)
        res = Rendered()
        self._doc = doc
        self._res = res
        self._footnotes: list[tuple[int, str]] = []
        self._tracked_id = cfg.get("tracked_id_base", 9000)
        self._para_refs: list[tuple[object, dict]] = []   # (p element, fact)
        self._toc_placeholder = None
        self._first_block = True
        self._cur = {"h1": None, "h2": None, "h3": None}
        self._pending_break = False
        units = params.get("units", {})
        self._units = units
        # expand fill blocks
        flat: list[dict] = []
        for b in blocks:
            if b["t"] == "fill":
                n = int(units.get(b["seg"], 0))
                for unit in pools.get(b["seg"], [])[:n]:
                    flat.extend(unit)
            else:
                flat.append(b)
        heading_list = [b for b in flat if b["t"] in ("h1", "h2")]
        for b in flat:
            getattr(self, "_b_" + b["t"])(b)
        # TOC (needs heading list)
        if self._toc_placeholder is not None:
            lv = cfg.get("toc_levels", 2)
            self._build_toc([h for h in heading_list if lv >= 2 or h["t"] == "h1"], toc_pages or {})
        self._attach_footnotes()
        util.set_core_props(doc.core_properties, cfg["title"], cfg["author_name"], dt.date.fromisoformat(cfg["date"]),
                            subject=cfg.get("subject", ""), keywords=cfg.get("keywords", ""))
        out_path = pathlib.Path(out_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        # paragraph indices
        body_ps = [p._p for p in doc.paragraphs]
        index_of = {id(p): i for i, p in enumerate(body_ps)}
        for p_el, fact in self._para_refs:
            loc = fact.setdefault("locator", {})
            loc["kind"] = "docx_para"
            loc["para_index"] = index_of[id(p_el)]
            if fact.get("_section"):
                loc["section"] = fact["_section"]
        doc.save(str(out_path))
        normalize_zip(out_path, cfg["date"])
        # image media names in body order
        res.images = media_by_drawing(out_path)
        for f in res.facts:
            loc = f.get("locator", {})
            if loc.get("kind") == "docx_image" and "_img_index" in loc:
                loc["image_name"] = res.images[loc.pop("_img_index")]["image_name"]
        res.headings = [(1 if b["t"] == "h1" else 2, b["text"]) for b in heading_list]
        return res

    # ------------------------------------------------------------------ block handlers
    def _new_para(self, style=None):
        p = self._doc.add_paragraph(style=style)
        if self._pending_break:
            p.paragraph_format.page_break_before = True
            self._pending_break = False
        return p

    def _register(self, p, facts, section_text=None):
        for f in facts or []:
            f["_section"] = section_text or self._cur["h2"] or self._cur["h1"]
            self._para_refs.append((p._p, f))
            self._res.facts.append(f)

    def _b_title_page(self, b):
        for i, (text, size, bold) in enumerate(b["lines"]):
            p = self._new_para()
            if i == 0:
                p.paragraph_format.space_before = Pt(b.get("top_space", 120))
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_after = Pt(b.get("gap", 14))
            r = p.add_run(text)
            r.font.size = Pt(size)
            r.bold = bold
            if b.get("facts_by_line", {}).get(i):
                self._register(p, b["facts_by_line"][i], "Title page")
        self._pending_break = True

    def _heading(self, b, lvl):
        p = self._doc.add_heading(b["text"], lvl)
        if b.get("break") or self._pending_break:
            p.paragraph_format.page_break_before = True
            self._pending_break = False
        key = {1: "h1", 2: "h2", 3: "h3"}[lvl]
        self._cur[key] = b["text"]
        if lvl == 1:
            self._cur["h2"] = None
            self._cur["h3"] = None
        if lvl == 2:
            self._cur["h3"] = None
        if b.get("facts"):
            self._register(p, b["facts"], b["text"])
        return p

    def _b_h1(self, b):
        self._heading(b, 1)

    def _b_h2(self, b):
        self._heading(b, 2)

    def _b_h3(self, b):
        self._heading(b, 3)

    def _b_pagebreak(self, b):
        self._pending_break = True

    def _b_section(self, b):
        sec = self._doc.add_section(WD_SECTION.NEW_PAGE)
        self._section_layout(sec)
        sec.header.is_linked_to_previous = True
        sec.footer.is_linked_to_previous = True
        self._pending_break = False

    def _b_toc(self, b):
        p = self._new_para(style="Contents Title")
        p.add_run(b.get("title", "Contents"))
        self._toc_placeholder = p

    def _b_p(self, b):
        style = b.get("style")
        p = self._new_para(style=style)
        if b.get("align") == "center":
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        if b.get("keep_next"):
            p.paragraph_format.keep_with_next = True
        if b.get("indent"):
            p.paragraph_format.left_indent = Cm(0.9)
            p.paragraph_format.first_line_indent = Cm(-0.5)
            p.paragraph_format.space_after = Pt(3)
        runs = b.get("runs") or [{"text": b.get("text", "")}]
        made = []
        for rd in runs:
            if "del" in rd or "ins" in rd:
                self._tracked(p, rd)
                continue
            r = p.add_run(rd.get("text", ""))
            if rd.get("bold"):
                r.bold = True
            if rd.get("italic"):
                r.italic = True
            if b.get("size"):
                r.font.size = Pt(b["size"])
            made.append(r)
            if rd.get("footnote"):
                self._footnote(p, rd["footnote"])
            if rd.get("break") == "page":
                r.add_break(WD_BREAK.PAGE)
        if b.get("comment"):
            c = b["comment"]
            com = self._doc.add_comment(made, text=c["text"], author=c["author"], initials=c.get("initials", ""))
            com._comment_elm.date = c.get("date", dt.datetime(2026, 6, 24, 10, 0, 0, tzinfo=dt.timezone.utc))
            if c.get("fact"):
                f = c["fact"]
                f["locator"] = {"kind": "docx_comment", "comment_id": com.comment_id}
                f["_section"] = self._cur["h2"] or self._cur["h1"]
                f["_anchor"] = " ".join((r.text or "") for r in made)[:45]
                self._res.facts.append(f)
            self._res.n_comments += 1
        self._register(p, b.get("facts"))

    def _tracked(self, p, rd):
        self._tracked_id += 1
        tid = self._tracked_id
        author = _esc(rd["author"])
        date = rd["date"]
        if "del" in rd:
            xml = (f'<w:del {nsdecls("w")} w:id="{tid}" w:author="{author}" w:date="{date}">'
                   f'<w:r><w:delText xml:space="preserve">{_esc(rd["del"])}</w:delText></w:r></w:del>')
        else:
            xml = (f'<w:ins {nsdecls("w")} w:id="{tid}" w:author="{author}" w:date="{date}">'
                   f'<w:r><w:t xml:space="preserve">{_esc(rd["ins"])}</w:t></w:r></w:ins>')
        p._p.append(parse_xml(xml))
        if rd.get("fact"):
            f = rd["fact"]
            kind = "del" if "del" in rd else "ins"
            # index among tracked elements of that type, in body order (counted by caller via _tr)
            cnt = self._res.__dict__.setdefault("_tr_" + kind, 0)
            f["locator"] = {"kind": "docx_tracked", "type": kind, "index": cnt}
            f["_section"] = self._cur["h2"] or self._cur["h1"]
            self._res.facts.append(f)
        kind = "del" if "del" in rd else "ins"
        self._res.__dict__["_tr_" + kind] = self._res.__dict__.get("_tr_" + kind, 0) + 1

    def _footnote(self, p, fd):
        fid = len(self._footnotes) + 1
        self._footnotes.append((fid, fd["text"]))
        p._p.append(parse_xml(f'<w:r {nsdecls("w")}><w:rPr><w:rStyle w:val="{self.fn_ref_id}"/></w:rPr>'
                              f'<w:footnoteReference w:id="{fid}"/></w:r>'))
        if fd.get("fact"):
            f = fd["fact"]
            f["locator"] = {"kind": "docx_footnote", "footnote_id": fid}
            f["_section"] = self._cur["h2"] or self._cur["h1"]
            self._res.facts.append(f)
        self._res.n_footnotes += 1

    def _attach_footnotes(self):
        if not self._footnotes:
            return
        parts = [f'<w:footnotes {nsdecls("w", "r")}>',
                 '<w:footnote w:type="separator" w:id="-1"><w:p><w:pPr><w:spacing w:after="0" w:line="240" w:lineRule="auto"/></w:pPr>'
                 '<w:r><w:separator/></w:r></w:p></w:footnote>',
                 '<w:footnote w:type="continuationSeparator" w:id="0"><w:p><w:pPr><w:spacing w:after="0" w:line="240" w:lineRule="auto"/></w:pPr>'
                 '<w:r><w:continuationSeparator/></w:r></w:p></w:footnote>']
        for fid, text in self._footnotes:
            parts.append(f'<w:footnote w:id="{fid}"><w:p><w:pPr><w:pStyle w:val="{self.fn_text_id}"/></w:pPr>'
                         f'<w:r><w:rPr><w:rStyle w:val="{self.fn_ref_id}"/></w:rPr><w:footnoteRef/></w:r>'
                         f'<w:r><w:t xml:space="preserve"> {_esc(text)}</w:t></w:r></w:p></w:footnote>')
        parts.append("</w:footnotes>")
        blob = "".join(parts).encode("utf-8")
        part = Part(PackURI("/word/footnotes.xml"), FOOTNOTES_CT, blob, self._doc.part.package)
        self._doc.part.relate_to(part, RT.FOOTNOTES)
        settings = self._doc.settings.element
        fpr = parse_xml(f'<w:footnotePr {nsdecls("w")}><w:footnote w:id="-1"/><w:footnote w:id="0"/></w:footnotePr>')
        settings.append(fpr)

    def _b_table(self, b):
        doc = self._doc
        if b.get("caption"):
            cp = self._new_para(style="Caption")
            cp.add_run(b["caption"])
            cp.paragraph_format.keep_with_next = True
        header, rows = b["header"], [list(r) for r in b["rows"]]
        if b.get("fill_seg"):
            v = int(self._units.get(b["fill_seg"], 0))
            n = len(rows)
            nc = b["notes_col"]
            for i, row in enumerate(rows):
                pool = b["notes_pool"][i]
                k = 1 + v // n + (1 if i < v % n else 0)
                row[nc] = " ".join(pool[:max(1, min(k, len(pool)))])
        t = doc.add_table(rows=1 + len(rows), cols=len(header))
        t.style = "Table Grid"
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        size = b.get("size", 9)
        widths = b.get("widths")
        for ci, h in enumerate(header):
            c = t.cell(0, ci)
            c.text = ""
            pr = c.paragraphs[0]
            pr.style = "Table Text"
            rr = pr.add_run(h)
            rr.bold = True
            rr.font.size = Pt(size)
            tcPr = c._tc.get_or_add_tcPr()
            tcPr.append(parse_xml(f'<w:shd {nsdecls("w")} w:val="clear" w:color="auto" w:fill="D9E2F3"/>'))
        if b.get("repeat_header"):
            trPr = t.rows[0]._tr.get_or_add_trPr()
            trPr.append(parse_xml(f'<w:tblHeader {nsdecls("w")}/>'))
        for ri, row in enumerate(rows, start=1):
            tr = t.rows[ri]
            if b.get("cant_split"):
                trPr = tr._tr.get_or_add_trPr()
                trPr.append(parse_xml(f'<w:cantSplit {nsdecls("w")}/>'))
            for ci, val in enumerate(row):
                c = tr.cells[ci]
                pr = c.paragraphs[0]
                pr.style = "Table Text"
                rr = pr.add_run(str(val))
                rr.font.size = Pt(size)
        if widths:
            for ci, w in enumerate(widths):
                for row in t.rows:
                    row.cells[ci].width = Cm(w)
        ti = self._res.n_tables
        self._res.n_tables += 1
        for f in b.get("facts") or []:
            f["locator"] = {"kind": "docx_table", "table_index": ti, "row": f.pop("row"), "col": f.pop("col")}
            f["_section"] = self._cur["h2"] or self._cur["h1"]
            self._res.facts.append(f)
        # spacer paragraph after the table
        sp = self._new_para()
        sp.paragraph_format.space_after = Pt(2)

    def _b_figure(self, b):
        p = self._new_para()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.keep_with_next = True
        run = p.add_run()
        shape = run.add_picture(str(b["png"]), width=Inches(b.get("width_in", 6.2)))
        docpr = shape._inline.docPr
        docpr.set("descr", b["alt"])
        docpr.set("title", b.get("alt_title", b["caption"]))
        img_i = len(self._res.images)
        self._res.images.append({"caption": b["caption"]})
        cp = self._new_para(style="Caption")
        cp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        cp.add_run(b["caption"])
        for f in b.get("facts") or []:
            f["locator"] = {"kind": "docx_image", "_img_index": img_i, "ocr": True}
            f["_section"] = self._cur["h2"] or self._cur["h1"]
            f["_caption"] = b["caption"]
            self._res.facts.append(f)
        for f in b.get("alt_facts") or []:
            f["locator"] = {"kind": "docx_alt_text", "image_index": img_i}
            f["_section"] = self._cur["h2"] or self._cur["h1"]
            f["_caption"] = b["caption"]
            self._res.facts.append(f)
        for f in b.get("caption_facts") or []:
            self._register(cp, [f])

    # ------------------------------------------------------------------ TOC
    def _build_toc(self, headings, toc_pages):
        anchor = self._toc_placeholder._p
        tab_pos = 9600  # twips, ~16.9 cm (text width 16.4 cm)
        xml_ps = []
        n = len(headings)
        for i, h in enumerate(headings):
            lvl = 1 if h["t"] == "h1" else 2
            pg = toc_pages.get(h["text"], "")
            pre = ""
            if i == 0:
                pre = ('<w:r><w:fldChar w:fldCharType="begin"/></w:r><w:r><w:instrText xml:space="preserve"> TOC \\o "1-2" \\h \\z \\u </w:instrText></w:r>'
                       '<w:r><w:fldChar w:fldCharType="separate"/></w:r>')
            post = '<w:r><w:fldChar w:fldCharType="end"/></w:r>' if i == n - 1 else ""
            xml_ps.append(
                f'<w:p {nsdecls("w")}><w:pPr><w:pStyle w:val="{self.toc_ids[lvl]}"/><w:tabs><w:tab w:val="right" w:leader="dot" w:pos="{tab_pos}"/></w:tabs></w:pPr>'
                f'{pre}<w:r><w:t xml:space="preserve">{_esc(h["text"])}</w:t></w:r><w:r><w:tab/></w:r><w:r><w:t>{pg}</w:t></w:r>{post}</w:p>')
        sdt = parse_xml(f'<w:sdt {nsdecls("w")}><w:sdtPr><w:docPartObj><w:docPartGallery w:val="Table of Contents"/><w:docPartUnique/></w:docPartObj></w:sdtPr>'
                        f'<w:sdtContent/></w:sdt>')
        content = sdt.find(qn("w:sdtContent"))
        for x in xml_ps:
            content.append(parse_xml(x))
        anchor.addnext(sdt)


# ---------------------------------------------------------------------------------------------
# Package post-processing
# ---------------------------------------------------------------------------------------------

def normalize_zip(path: pathlib.Path, when, pages: int | None = None) -> None:
    """Rewrite the zip with fixed timestamps (byte-stable output) and optional app.xml pages."""
    if isinstance(when, str):
        when = dt.date.fromisoformat(when)
    ts = (when.year, when.month, when.day, 9, 0, 0)
    src = zipfile.ZipFile(path)
    items = [(i.filename, src.read(i.filename)) for i in src.infolist()]
    src.close()
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for name, data in items:
            if pages is not None and name == "docProps/app.xml":
                s = data.decode("utf-8")
                if "<Pages>" in s:
                    s = re.sub(r"<Pages>\d+</Pages>", f"<Pages>{pages}</Pages>", s)
                data = s.encode("utf-8")
            zi = zipfile.ZipInfo(name, date_time=ts)
            zi.compress_type = zipfile.ZIP_DEFLATED
            zi.external_attr = 0o644 << 16
            z.writestr(zi, data)
    pathlib.Path(path).write_bytes(buf.getvalue())


def media_by_drawing(path: pathlib.Path) -> list[dict]:
    """[{image_name, descr}] for each wp:docPr in body order (matches extract.doc_prs())."""
    z = zipfile.ZipFile(path)
    rels = etree.fromstring(z.read("word/_rels/document.xml.rels"))
    rmap = {r.get("Id"): r.get("Target") for r in rels}
    root = etree.fromstring(z.read("word/document.xml"))
    ns = {"w": W_NS, "wp": "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing",
          "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
          "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships"}
    body = root.find("w:body", ns)
    out = []
    for docpr in body.iter("{%s}docPr" % ns["wp"]):
        inline = docpr.getparent()
        blip = inline.find(".//a:blip", ns)
        rid = blip.get("{%s}embed" % ns["r"]) if blip is not None else None
        target = rmap.get(rid, "")
        out.append({"image_name": "word/" + target if not target.startswith("word/") else target,
                    "descr": docpr.get("descr")})
    z.close()
    return out


def make_clean_variant(src: pathlib.Path, dst: pathlib.Path, when) -> pathlib.Path:
    """Accept tracked changes and strip comment anchors (the 'signed copy' rendering)."""
    z = zipfile.ZipFile(src)
    items = [(i.filename, z.read(i.filename)) for i in z.infolist()]
    z.close()
    out = []
    for name, data in items:
        if name == "word/document.xml":
            root = etree.fromstring(data)
            W = "{%s}" % W_NS
            for el in list(root.iter(W + "del")):
                if el.getparent() is not None and el.getparent().tag not in (W + "rPr", W + "trPr"):
                    el.getparent().remove(el)
            for el in list(root.iter(W + "ins")):
                par = el.getparent()
                if par is None or par.tag in (W + "rPr", W + "trPr"):
                    continue
                idx = par.index(el)
                for ch in list(el):
                    par.insert(idx, ch)
                    idx += 1
                par.remove(el)
            for tag in ("commentRangeStart", "commentRangeEnd"):
                for el in list(root.iter(W + tag)):
                    el.getparent().remove(el)
            for el in list(root.iter(W + "commentReference")):
                r = el.getparent()
                r.getparent().remove(r)
            data = etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)
        out.append((name, data))
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zz:
        for name, data in out:
            zz.writestr(zipfile.ZipInfo(name, date_time=(2026, 7, 1, 9, 0, 0)), data)
    dst = pathlib.Path(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_bytes(buf.getvalue())
    return dst

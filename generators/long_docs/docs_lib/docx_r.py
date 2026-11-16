"""DOCX renderer: python-docx for paragraphs/parts, raw WordprocessingML for tables (fast)."""
from __future__ import annotations

import hashlib
import io
import pathlib
import re
import zipfile

from docx import Document
from docx.enum.section import WD_ORIENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.opc.constants import RELATIONSHIP_TYPE as RT
from docx.opc.packuri import PackURI
from docx.opc.part import Part
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls, qn
from docx.shared import Cm, Pt, RGBColor

from .core import Doc, Fact, d, esc_xml, util

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
FOOTNOTES_CT = "application/vnd.openxmlformats-officedocument.wordprocessingml.footnotes+xml"
_INLINE = re.compile(r"(\*\*.+?\*\*)")


def _rpr(size_half=None, bold=False, italic=False, color=None, font=None) -> str:
    parts = []
    if font:
        parts.append(f'<w:rFonts w:ascii="{font}" w:hAnsi="{font}" w:cs="{font}"/>')
    if bold:
        parts.append("<w:b/>")
    if italic:
        parts.append("<w:i/>")
    if color:
        parts.append(f'<w:color w:val="{color}"/>')
    if size_half:
        parts.append(f'<w:sz w:val="{size_half}"/><w:szCs w:val="{size_half}"/>')
    return f"<w:rPr>{''.join(parts)}</w:rPr>" if parts else ""


def _runs_xml(text: str, size_half=None, bold=False, italic=False, color=None) -> str:
    out = []
    for piece in _INLINE.split(str(text)):
        if not piece:
            continue
        b = bold
        if piece.startswith("**") and piece.endswith("**") and len(piece) > 4:
            piece, b = piece[2:-2], True
        lines = piece.split("\n")
        for i, ln in enumerate(lines):
            if i:
                out.append("<w:r><w:br/></w:r>")
            out.append(f'<w:r>{_rpr(size_half, b, italic, color)}<w:t xml:space="preserve">{esc_xml(ln)}</w:t></w:r>')
    return "".join(out)


class DocxRenderer:
    def __init__(self, doc: Doc):
        self.d = doc
        self.st = doc.style
        self.doc = Document()
        self.np = 0                 # body paragraphs added
        self.nt = 0                 # body tables added
        self.n_img = 0              # drawings added (wp:docPr in body order)
        self.footnotes: list[tuple[int, str]] = []
        self.cur_heading = None
        self.fig_no = 0
        self.tab_no = 0
        self.image_facts: list[tuple[str, Fact]] = []   # (sha1 of png, fact)
        self.pending_page_facts: list[Fact] = []
        self._setup()

    # ---------------------------------------------------------------- setup
    def _setup(self):
        doc, st = self.doc, self.st
        sec = doc.sections[0]
        sec.page_height, sec.page_width = Cm(29.7), Cm(21.0)
        if self.d.landscape:
            sec.orientation = WD_ORIENT.LANDSCAPE
            sec.page_height, sec.page_width = Cm(21.0), Cm(29.7)
        sec.left_margin = sec.right_margin = Cm(2.2)
        sec.top_margin, sec.bottom_margin = Cm(2.3), Cm(2.0)
        sec.header_distance = sec.footer_distance = Cm(1.0)
        normal = doc.styles["Normal"]
        normal.font.name = st.font
        normal.font.size = Pt(st.size)
        rpr = normal.element.get_or_add_rPr()
        rfonts = rpr.find(qn("w:rFonts"))
        if rfonts is None:
            rfonts = parse_xml(f"<w:rFonts {nsdecls('w')}/>")
            rpr.append(rfonts)
        for a in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
            rfonts.set(qn(a), st.font)
        normal.paragraph_format.space_after = Pt(6)
        normal.paragraph_format.line_spacing = st.line_spacing
        sizes = {1: 15, 2: 12.5, 3: 11}
        for lvl in (1, 2, 3):
            hs = doc.styles[f"Heading {lvl}"]
            hs.font.name = st.heading_font
            hs.font.size = Pt(sizes[lvl])
            hs.font.bold = True
            hs.font.color.rgb = RGBColor.from_string(st.accent)
            hs.paragraph_format.space_before = Pt(14 if lvl == 1 else 10)
            hs.paragraph_format.space_after = Pt(5)
            hs.paragraph_format.keep_with_next = True
            hrpr = hs.element.get_or_add_rPr()
            hf = hrpr.find(qn("w:rFonts"))
            if hf is None:
                hf = parse_xml(f"<w:rFonts {nsdecls('w')}/>")
                hrpr.append(hf)
            for a in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
                hf.set(qn(a), st.heading_font)
            for a in ("w:asciiTheme", "w:hAnsiTheme", "w:eastAsiaTheme", "w:cstheme"):
                if hf.get(qn(a)) is not None:
                    del hf.attrib[qn(a)]
        try:
            cap = doc.styles["Caption"]
            cap.font.size = Pt(9)
            cap.font.italic = True
            cap.font.color.rgb = RGBColor(0x40, 0x40, 0x40)
        except KeyError:
            pass
        self._header_footer()

    def _header_footer(self):
        sec = self.doc.sections[0]
        width_twips = int(((29.7 if self.d.landscape else 21.0) - 4.4) / 2.54 * 1440)
        hdr = sec.header
        hp = hdr.paragraphs[0]
        hp._p.getparent().remove(hp._p)
        hxml = (f'<w:p {nsdecls("w")}><w:pPr><w:pBdr><w:bottom w:val="single" w:sz="4" w:space="1" w:color="808080"/></w:pBdr>'
                f'<w:tabs><w:tab w:val="right" w:pos="{width_twips}"/></w:tabs><w:spacing w:after="0"/></w:pPr>'
                f'{_runs_xml(self.d.header_left, 16, color="404040")}<w:r><w:tab/></w:r>'
                f'{_runs_xml(self.d.header_right, 16, color="404040")}</w:p>')
        hdr._element.append(parse_xml(hxml))
        if self.d.watermark:
            hdr._element.append(parse_xml(self._watermark_xml(self.d.watermark)))
        ftr = sec.footer
        fp = ftr.paragraphs[0]
        fp._p.getparent().remove(fp._p)
        fxml = (f'<w:p {nsdecls("w")}><w:pPr><w:pBdr><w:top w:val="single" w:sz="4" w:space="1" w:color="808080"/></w:pBdr>'
                f'<w:tabs><w:tab w:val="right" w:pos="{width_twips}"/></w:tabs><w:spacing w:after="0"/></w:pPr>'
                f'{_runs_xml(self.d.footer_left, 16, color="404040")}<w:r><w:tab/></w:r>'
                f'<w:r>{_rpr(16, color="404040")}<w:t xml:space="preserve">Page </w:t></w:r>'
                f'<w:fldSimple w:instr=" PAGE "><w:r>{_rpr(16, color="404040")}<w:t>1</w:t></w:r></w:fldSimple>'
                f'<w:r>{_rpr(16, color="404040")}<w:t xml:space="preserve"> of </w:t></w:r>'
                f'<w:fldSimple w:instr=" NUMPAGES "><w:r>{_rpr(16, color="404040")}<w:t>1</w:t></w:r></w:fldSimple></w:p>')
        ftr._element.append(parse_xml(fxml))
        for f in self.d.header_facts:
            f.locator = {"kind": "docx_header", "section_index": 0}
        for f in self.d.footer_facts:
            f.locator = {"kind": "docx_footer", "section_index": 0}

    @staticmethod
    def _watermark_xml(text: str) -> str:
        return (f'<w:p {nsdecls("w")} xmlns:v="urn:schemas-microsoft-com:vml" xmlns:o="urn:schemas-microsoft-com:office:office">'
                '<w:pPr><w:spacing w:after="0"/></w:pPr><w:r><w:pict>'
                '<v:shapetype id="_x0000_t136" coordsize="21600,21600" o:spt="136" adj="10800" '
                'path="m@7,l@8,m@5,21600l@6,21600e"><v:path textpathok="t" o:connecttype="custom"/>'
                '<v:textpath on="t" fitshape="t"/></v:shapetype>'
                '<v:shape id="WatermarkDraft" o:spid="_x0000_s2049" type="#_x0000_t136" '
                'style="position:absolute;margin-left:0;margin-top:0;width:440pt;height:160pt;rotation:315;'
                'z-index:-251657216;mso-position-horizontal:center;mso-position-horizontal-relative:margin;'
                'mso-position-vertical:center;mso-position-vertical-relative:margin" o:allowincell="f" '
                'fillcolor="#d8d8d8" stroked="f"><v:fill opacity=".45"/>'
                f'<v:textpath style="font-family:&quot;Calibri&quot;;font-size:1pt" string="{esc_xml(text)}"/>'
                '</v:shape></w:pict></w:r></w:p>')

    # ---------------------------------------------------------------- primitives
    def _body_insert(self, el):
        body = self.doc.element.body
        body.sectPr.addprevious(el)

    def _para_xml(self, inner: str, ppr: str = "") -> int:
        el = parse_xml(f'<w:p {nsdecls("w")}>{("<w:pPr>" + ppr + "</w:pPr>") if ppr else ""}{inner}</w:p>')
        self._body_insert(el)
        self.np += 1
        return self.np - 1

    def _add_para(self, text="", style=None):
        p = self.doc.add_paragraph(style=style)
        if text:
            self._fill_runs(p, text)
        self.np += 1
        return p, self.np - 1

    def _fill_runs(self, p, text, size=None, italic=False, bold=False):
        for piece in _INLINE.split(str(text)):
            if not piece:
                continue
            b = bold
            if piece.startswith("**") and piece.endswith("**") and len(piece) > 4:
                piece, b = piece[2:-2], True
            r = p.add_run(piece)
            if b:
                r.bold = True
            if italic:
                r.italic = True
            if size:
                r.font.size = Pt(size)

    def _para_loc(self, idx: int) -> dict:
        loc = {"kind": "docx_para", "para_index": idx}
        if self.cur_heading:
            loc["section"] = self.cur_heading
        return loc

    # ---------------------------------------------------------------- blocks
    def render(self, out_path: pathlib.Path) -> pathlib.Path:
        assert len(self.doc.paragraphs) == 0, "template body not empty"
        for b in self.d.blocks:
            getattr(self, "_b_" + b.kind)(b)
        self._write_footnotes()
        buf = io.BytesIO()
        self.doc.save(buf)
        data = self._normalise_zip(buf.getvalue(), str(self.d.date)[:10])
        out_path = pathlib.Path(out_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_bytes(data)
        self._resolve_images(data)
        assert len(self.doc.paragraphs) == self.np, (len(self.doc.paragraphs), self.np)
        return out_path

    def _b_title_page(self, b):
        st = self.st
        for _ in range(3):
            self._add_para("")
        p, _ = self._add_para("")
        r = p.add_run("CORVANE MUTUAL INSURANCE SOCIETY LIMITED")
        r.font.size = Pt(10)
        r.font.bold = True
        r.font.color.rgb = RGBColor.from_string(st.accent)
        p, idx = self._add_para("", style="Title")
        r = p.add_run(self.d.title)
        r.font.size = Pt(26)
        r.font.color.rgb = RGBColor.from_string(st.accent)
        for f in b.facts:
            if f.where == "title":
                f.locator = self._para_loc(idx)
        if self.d.subtitle:
            p, idx = self._add_para("")
            r = p.add_run(self.d.subtitle)
            r.font.size = Pt(14)
            r.font.color.rgb = RGBColor(0x55, 0x55, 0x55)
            for f in b.facts:
                if f.where == "subtitle":
                    f.locator = self._para_loc(idx)
        for line in b.data.get("extra_lines", []):
            self._add_para(line)
        self._add_para("")
        tb = type(b)("table", {"header": None, "rows": b.data["rows"], "widths": [5.0, 11.0],
                               "caption": None, "font_size": 9.5, "header_rows": 0, "zebra": False,
                               "first_col_bold": True, "align": None, "caption_above": True, "kv": True},
                     [f for f in b.facts if isinstance(f.where, tuple)])
        self._b_table(tb)
        self._b_pagebreak(None)

    def _b_toc(self, b):
        p, _ = self._add_para("")
        r = p.add_run("Contents")
        r.font.size = Pt(15)
        r.font.bold = True
        r.font.color.rgb = RGBColor.from_string(self.st.accent)
        depth = b.data.get("depth", 2)
        for lvl, text in self.d.headings:
            if lvl <= depth:
                ind = 0.0 if lvl == 1 else 0.6 * (lvl - 1)
                self._para_xml(_runs_xml(text, 19 if lvl == 1 else 18, bold=(lvl == 1)),
                               f'<w:spacing w:after="20"/><w:ind w:left="{int(ind * 567)}"/>')
        self._b_pagebreak(None)

    def _b_heading(self, b):
        if b.data.get("page_break"):
            self._b_pagebreak(None)
        lvl = min(b.data["level"], 3)
        p = self.doc.add_heading(b.data["text"], level=lvl)
        self.np += 1
        self.cur_heading = b.data["text"]
        for f in b.facts:
            f.locator = self._para_loc(self.np - 1)

    def _b_para(self, b):
        data = b.data
        text = data["text"]
        split_after = data.get("split_page_after")
        if split_after:
            i = text.index(split_after) + len(split_after)
            a, c = text[:i], text[i:]
            inner = _runs_xml(a) + '<w:r><w:br w:type="page"/></w:r>' + _runs_xml(c.lstrip())
            if not c.startswith(" "):
                pass
            idx = self._para_xml(inner)
        else:
            p = self.doc.add_paragraph(style=data.get("style"))
            self.np += 1
            idx = self.np - 1
            if data.get("align") == "center":
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            elif data.get("align") == "right":
                p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
            if data.get("keep_next"):
                p.paragraph_format.keep_with_next = True
            self._fill_runs(p, text, size=data.get("size"), italic=data.get("italic"), bold=data.get("bold"))
            if data.get("footnote"):
                fid = len(self.footnotes) + 1
                self.footnotes.append((fid, data["footnote"]))
                p._p.append(parse_xml(
                    f'<w:r {nsdecls("w")}><w:rPr><w:vertAlign w:val="superscript"/></w:rPr>'
                    f'<w:footnoteReference w:id="{fid}"/></w:r>'))
                for f in data.get("footnote_facts", []):
                    f.locator = {"kind": "docx_footnote", "footnote_id": fid}
            if data.get("comment"):
                c = data["comment"]
                runs = p.runs
                com = self.doc.add_comment(runs, text=c["text"], author=c.get("author", ""),
                                           initials=c.get("initials", ""))
                for f in b.facts:
                    if f.where == "comment":
                        f.locator = {"kind": "docx_comment", "comment_id": int(com.comment_id)}
        for f in b.facts:
            if f.where in (None, "para"):
                f.locator = self._para_loc(idx)

    def _b_bullets(self, b):
        style = "List Number" if b.data.get("numbered") else "List Bullet"
        idxs = []
        for item in b.data["items"]:
            p = self.doc.add_paragraph(style=style)
            self._fill_runs(p, item)
            p.paragraph_format.space_after = Pt(2)
            self.np += 1
            idxs.append(self.np - 1)
        for f in b.facts:
            k = f.where if isinstance(f.where, int) else 0
            f.locator = self._para_loc(idxs[k])

    def _b_note(self, b):
        label = b.data.get("label", "Note")
        rows = [[f"**{label}:** {b.data['text']}"]]
        tb = type(b)("table", {"header": None, "rows": rows, "widths": [16.6], "caption": None,
                               "font_size": 9.5, "header_rows": 0, "zebra": False, "first_col_bold": False,
                               "align": None, "caption_above": True, "kv": False, "shade": "F2F2F2"},
                     [])
        for f in b.facts:
            f.where = (0, 0)
            tb.facts.append(f)
        self._b_table(tb)
        self._add_para("")

    def _b_spacer(self, b):
        p, _ = self._add_para("")
        p.paragraph_format.space_after = Pt(int(b.data.get("h", 0.4) * 28))

    def _b_pagebreak(self, b):
        self._para_xml('<w:r><w:br w:type="page"/></w:r>')

    def _b_figure(self, b):
        data = b.data
        path = pathlib.Path(data["path"])
        self.doc.add_picture(str(path), width=Cm(data.get("width_cm", 16.0)))
        self.np += 1
        p = self.doc.paragraphs[-1] if False else None
        last_p = self.doc.element.body.sectPr.getprevious()
        ppr = last_p.get_or_add_pPr()
        jc = parse_xml(f'<w:jc {nsdecls("w")} w:val="center"/>')
        ppr.append(jc)
        img_index = self.n_img
        self.n_img += 1
        docpr = last_p.find(".//" + qn("wp:docPr"))
        if docpr is not None:
            docpr.set("descr", data.get("alt") or data["caption"])
            docpr.set("title", data["caption"][:120])
        self.fig_no += 1
        cap_idx = self._para_xml(_runs_xml(f"Figure {self.fig_no}: {data['caption']}", 18, italic=True, color="404040"),
                                 '<w:pStyle w:val="Caption"/><w:jc w:val="center"/>')
        sha = hashlib.sha1(path.read_bytes()).hexdigest()
        for f in b.facts:
            if f.where == "alt":
                f.locator = {"kind": "docx_alt_text", "image_index": img_index}
            elif f.where == "image":
                f.anchor_text = f.anchor_text or data["caption"]
                self.image_facts.append((sha, f))
            else:
                f.locator = self._para_loc(cap_idx)

    def _b_table(self, b):
        data = b.data
        header = data.get("header")
        rows = data["rows"]
        ncols = len(header) if header else max(len(r) for r in rows)
        page_w = (29.7 if self.d.landscape else 21.0) - 4.4
        widths = data.get("widths") or [page_w / ncols] * ncols
        tot = sum(widths)
        if tot > page_w + 0.01:
            widths = [w * page_w / tot for w in widths]
        tw = [int(w / 2.54 * 1440) for w in widths]
        fs = data.get("font_size") or (self.st.size - 1.5)
        sz = int(round(fs * 2))
        if data.get("caption") and data.get("caption_above", True):
            self.tab_no += 1
            self._para_xml(_runs_xml(f"Table {self.tab_no}: {data['caption']}", 18, bold=True, color="404040"),
                           '<w:keepNext/><w:spacing w:before="120" w:after="60"/>')
        accent2 = self.st.accent2
        shade = data.get("shade")
        trs = []
        all_rows = ([header] if header else []) + rows
        n_head = (1 if header else 0)
        for r_i, row in enumerate(all_rows):
            is_head = r_i < n_head
            cells = []
            for c_i in range(ncols):
                txt = row[c_i] if c_i < len(row) else ""
                fill = None
                if is_head:
                    fill = accent2
                elif shade:
                    fill = shade
                elif data.get("kv") and c_i == 0:
                    fill = "F2F2F2"
                elif data.get("zebra") and r_i % 2 == 0:
                    fill = "F7F7F7"
                bold = is_head or (data.get("first_col_bold") and c_i == 0)
                tcpr = f'<w:tcW w:w="{tw[c_i]}" w:type="dxa"/>'
                if fill:
                    tcpr += f'<w:shd w:val="clear" w:color="auto" w:fill="{fill}"/>'
                paras = []
                for line in str(txt).split("\n"):
                    paras.append(f'<w:p><w:pPr><w:spacing w:before="20" w:after="20" w:line="240" w:lineRule="auto"/></w:pPr>'
                                 f'{_runs_xml(line, sz, bold=bold)}</w:p>')
                cells.append(f"<w:tc><w:tcPr>{tcpr}</w:tcPr>{''.join(paras)}</w:tc>")
            trpr = "<w:trPr><w:tblHeader/><w:cantSplit/></w:trPr>" if is_head else "<w:trPr><w:cantSplit/></w:trPr>"
            trs.append(f"<w:tr>{trpr}{''.join(cells)}</w:tr>")
        grid = "".join(f'<w:gridCol w:w="{w}"/>' for w in tw)
        borders = ("<w:tblBorders>" + "".join(
            f'<w:{s} w:val="single" w:sz="4" w:space="0" w:color="A6A6A6"/>'
            for s in ("top", "left", "bottom", "right", "insideH", "insideV")) + "</w:tblBorders>")
        xml = (f'<w:tbl {nsdecls("w")}><w:tblPr><w:tblW w:w="{sum(tw)}" w:type="dxa"/>{borders}'
               '<w:tblLayout w:type="fixed"/><w:tblCellMar><w:left w:w="80" w:type="dxa"/>'
               '<w:right w:w="80" w:type="dxa"/></w:tblCellMar><w:tblLook w:val="04A0" w:firstRow="1"/>'
               f'</w:tblPr><w:tblGrid>{grid}</w:tblGrid>{"".join(trs)}</w:tbl>')
        self._body_insert(parse_xml(xml))
        ti = self.nt
        self.nt += 1
        for f in b.facts:
            r, c = f.where if isinstance(f.where, tuple) else (0, 0)
            f.locator = {"kind": "docx_table", "table_index": ti, "row": r, "col": c}
        if data.get("caption") and not data.get("caption_above", True):
            self.tab_no += 1
            self._para_xml(_runs_xml(f"Table {self.tab_no}: {data['caption']}", 18, italic=True, color="404040"))
        else:
            # small gap after a table keeps tables from merging in Word
            self._para_xml("", '<w:spacing w:after="60"/>')

    # ---------------------------------------------------------------- finishing
    def _write_footnotes(self):
        if not self.footnotes:
            return
        body = []
        body.append('<w:footnote w:type="separator" w:id="-1"><w:p><w:pPr><w:spacing w:after="0" w:line="240" '
                    'w:lineRule="auto"/></w:pPr><w:r><w:separator/></w:r></w:p></w:footnote>')
        body.append('<w:footnote w:type="continuationSeparator" w:id="0"><w:p><w:pPr><w:spacing w:after="0" '
                    'w:line="240" w:lineRule="auto"/></w:pPr><w:r><w:continuationSeparator/></w:r></w:p></w:footnote>')
        for fid, text in self.footnotes:
            body.append(f'<w:footnote w:id="{fid}"><w:p><w:pPr><w:spacing w:after="0"/></w:pPr>'
                        f'<w:r><w:rPr><w:vertAlign w:val="superscript"/><w:sz w:val="16"/></w:rPr><w:footnoteRef/></w:r>'
                        f'<w:r><w:rPr><w:sz w:val="16"/></w:rPr><w:t xml:space="preserve"> {esc_xml(text)}</w:t></w:r>'
                        '</w:p></w:footnote>')
        xml = (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<w:footnotes xmlns:w="{W_NS}">'
               + "".join(body) + "</w:footnotes>")
        part = Part(PackURI("/word/footnotes.xml"), FOOTNOTES_CT, xml.encode("utf-8"), self.doc.part.package)
        self.doc.part.relate_to(part, RT.FOOTNOTES)

    @staticmethod
    def _normalise_zip(data: bytes, date: str = "2026-01-01") -> bytes:
        zin = zipfile.ZipFile(io.BytesIO(data))
        out = io.BytesIO()
        with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zout:
            for info in zin.infolist():
                zi = zipfile.ZipInfo(info.filename, date_time=(2026, 1, 1, 0, 0, 0))
                zi.compress_type = zipfile.ZIP_DEFLATED
                zi.external_attr = 0o644 << 16
                payload = zin.read(info.filename)
                if info.filename == "word/comments.xml":
                    # python-docx stamps comments with the wall clock; use the document date instead
                    payload = re.sub(rb'w:date="[^"]*"', f'w:date="{date}T09:00:00Z"'.encode(), payload)
                zout.writestr(zi, payload)
        return out.getvalue()

    def _resolve_images(self, data: bytes):
        if not self.image_facts:
            return
        z = zipfile.ZipFile(io.BytesIO(data))
        by_sha = {}
        for n in z.namelist():
            if n.startswith("word/media/"):
                by_sha[hashlib.sha1(z.read(n)).hexdigest()] = n
        for sha, f in self.image_facts:
            f.locator = {"kind": "docx_image", "image_name": by_sha[sha], "ocr": True}


def set_props(path: pathlib.Path, doc: Doc):
    """Core properties (deterministic) — applied before saving via a second pass."""
    pass


def render_docx(doc: Doc, out_path) -> pathlib.Path:
    r = DocxRenderer(doc)
    util.set_core_props(r.doc.core_properties, title=doc.title, author=doc.author, when=d(doc.date),
                        subject=doc.subtitle or doc.title, keywords=f"{doc.doc_id}; Corvane Mutual")
    return r.render(out_path)

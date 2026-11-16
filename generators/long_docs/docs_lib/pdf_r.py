"""reportlab renderer (invariant output, DejaVu fonts, running header/footer, page-bottom footnotes)."""
from __future__ import annotations

import pathlib
import re

from reportlab import rl_config

rl_config.invariant = 1

from reportlab.lib import colors  # noqa: E402
from reportlab.lib.enums import TA_CENTER, TA_LEFT  # noqa: E402
from reportlab.lib.pagesizes import A4, landscape  # noqa: E402
from reportlab.lib.styles import ParagraphStyle  # noqa: E402
from reportlab.lib.units import cm  # noqa: E402
from reportlab.pdfbase import pdfmetrics  # noqa: E402
from reportlab.pdfbase.ttfonts import TTFont  # noqa: E402
from reportlab.pdfgen import canvas as rl_canvas  # noqa: E402
from reportlab.platypus import (BaseDocTemplate, Flowable, Frame, Image, KeepTogether, PageBreak,  # noqa: E402
                                PageTemplate, Paragraph, Spacer, Table, TableStyle)

from .core import Doc, util  # noqa: E402

_FONTS_DONE = False


def _register_fonts():
    global _FONTS_DONE
    if _FONTS_DONE:
        return
    import matplotlib
    base = pathlib.Path(matplotlib.get_data_path()) / "fonts" / "ttf"
    for name, fn in [("DVS", "DejaVuSans.ttf"), ("DVS-B", "DejaVuSans-Bold.ttf"),
                     ("DVS-I", "DejaVuSans-Oblique.ttf"), ("DVS-BI", "DejaVuSans-BoldOblique.ttf"),
                     ("DVSerif", "DejaVuSerif.ttf"), ("DVSerif-B", "DejaVuSerif-Bold.ttf"),
                     ("DVSerif-I", "DejaVuSerif-Italic.ttf"), ("DVSerif-BI", "DejaVuSerif-BoldItalic.ttf")]:
        pdfmetrics.registerFont(TTFont(name, str(base / fn)))
    pdfmetrics.registerFontFamily("DVS", normal="DVS", bold="DVS-B", italic="DVS-I", boldItalic="DVS-BI")
    pdfmetrics.registerFontFamily("DVSerif", normal="DVSerif", bold="DVSerif-B", italic="DVSerif-I",
                                  boldItalic="DVSerif-BI")
    _FONTS_DONE = True


_INLINE = re.compile(r"\*\*(.+?)\*\*")


def mk(text: str) -> str:
    t = str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    t = _INLINE.sub(r"<b>\1</b>", t)
    return t.replace("\n", "<br/>")


def _hex(c: str):
    return colors.HexColor("#" + c)


class _FootnoteMark(Flowable):
    """Zero-size flowable: registers a footnote for the page on which it is drawn."""

    def __init__(self, sink: list, num: int, text: str):
        super().__init__()
        self.sink, self.num, self.text = sink, num, text
        self.width = self.height = 0

    def wrap(self, aw, ah):
        return 0, 0

    def draw(self):
        self.sink.append((self.num, self.text))


class _NumberedCanvas(rl_canvas.Canvas):
    """Defers page output so that 'Page X of Y' can be drawn."""

    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self._saved = []

    def showPage(self):
        self._saved.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        n = len(self._saved)
        for st in self._saved:
            self.__dict__.update(st)
            self._draw_page_total(n)
            super().showPage()
        super().save()

    def _draw_page_total(self, n):
        info = getattr(self, "_ld_footer", None)
        if not info:
            return
        font, size, x, y = info
        self.setFont(font, size)
        self.setFillColor(colors.HexColor("#404040"))
        self.drawRightString(x, y, f"Page {self._pageNumber} of {n}")


class PdfRenderer:
    def __init__(self, doc: Doc):
        _register_fonts()
        self.d = doc
        st = doc.style
        self.fn = "DVSerif" if st.serif else "DVS"
        self.fb = self.fn + "-B"
        self.fi = self.fn + "-I"
        self.accent = _hex(st.accent)
        self.accent2 = _hex(st.accent2)
        self.page = landscape(A4) if doc.landscape else A4
        self.footnotes_page: list = []
        self.fn_count = 0
        self.fig_no = 0
        self.tab_no = 0
        base = st.size - 0.8
        self.s_body = ParagraphStyle("body", fontName=self.fn, fontSize=base, leading=base * st.pdf_leading,
                                     spaceAfter=5, alignment=TA_LEFT)
        self.s_small = ParagraphStyle("small", parent=self.s_body, fontSize=base - 1.5, leading=(base - 1.5) * 1.3,
                                      spaceAfter=0)
        self.s_cell = ParagraphStyle("cell", parent=self.s_body, fontSize=base - 1.6, leading=(base - 1.6) * 1.25,
                                     spaceAfter=0)
        self.s_cellb = ParagraphStyle("cellb", parent=self.s_cell, fontName=self.fb)
        self.s_h = {
            1: ParagraphStyle("h1", fontName=self.fb, fontSize=15, leading=19, textColor=self.accent,
                              spaceBefore=12, spaceAfter=6, keepWithNext=1),
            2: ParagraphStyle("h2", fontName=self.fb, fontSize=12.3, leading=16, textColor=self.accent,
                              spaceBefore=9, spaceAfter=4, keepWithNext=1),
            3: ParagraphStyle("h3", fontName=self.fb, fontSize=10.8, leading=14, textColor=self.accent,
                              spaceBefore=7, spaceAfter=3, keepWithNext=1),
        }
        self.s_cap = ParagraphStyle("cap", parent=self.s_body, fontName=self.fi, fontSize=base - 1.2,
                                    alignment=TA_CENTER, textColor=colors.HexColor("#404040"), spaceAfter=8)
        self.s_tcap = ParagraphStyle("tcap", parent=self.s_body, fontName=self.fb, fontSize=base - 1.0,
                                     textColor=colors.HexColor("#404040"), spaceBefore=6, spaceAfter=3,
                                     keepWithNext=1)
        self.s_bullet = ParagraphStyle("bul", parent=self.s_body, leftIndent=14, bulletIndent=3, spaceAfter=2)
        self.s_title = ParagraphStyle("title", fontName=self.fb, fontSize=25, leading=31, textColor=self.accent,
                                      spaceAfter=10)
        self.s_sub = ParagraphStyle("sub", fontName=self.fn, fontSize=14, leading=18,
                                    textColor=colors.HexColor("#555555"), spaceAfter=18)

    # ---------------------------------------------------------------- page furniture
    def _on_page(self, c, doc):
        w, h = self.page
        c.saveState()
        c.setFont(self.fn, 7.8)
        c.setFillColor(colors.HexColor("#404040"))
        c.drawString(2.2 * cm, h - 1.35 * cm, self.d.header_left)
        c.drawRightString(w - 2.2 * cm, h - 1.35 * cm, self.d.header_right)
        c.setStrokeColor(colors.HexColor("#808080"))
        c.setLineWidth(0.5)
        c.line(2.2 * cm, h - 1.5 * cm, w - 2.2 * cm, h - 1.5 * cm)
        c.line(2.2 * cm, 1.45 * cm, w - 2.2 * cm, 1.45 * cm)
        c.drawString(2.2 * cm, 1.05 * cm, self.d.footer_left)
        c._ld_footer = (self.fn, 7.8, w - 2.2 * cm, 1.05 * cm)
        if self.d.watermark:
            c.saveState()
            c.setFillColor(colors.Color(0.85, 0.85, 0.85))
            c.setFont(self.fb, 90)
            c.translate(w / 2, h / 2)
            c.rotate(45)
            c.drawCentredString(0, 0, self.d.watermark)
            c.restoreState()
        c.restoreState()

    def _on_page_end(self, c, doc):
        if not self.footnotes_page:
            return
        w, h = self.page
        c.saveState()
        y = 1.65 * cm + 0.36 * cm * (len(self.footnotes_page) - 1)
        c.setStrokeColor(colors.HexColor("#808080"))
        c.line(2.2 * cm, y + 0.42 * cm, 6.5 * cm, y + 0.42 * cm)
        for num, text in self.footnotes_page:
            p = Paragraph(f"<super>{num}</super> {mk(text)}", ParagraphStyle(
                "fn", fontName=self.fn, fontSize=7.2, leading=8.6))
            pw, ph = p.wrap(w - 4.4 * cm, 2 * cm)
            p.drawOn(c, 2.2 * cm, y - ph + 8.6)
            y -= 0.36 * cm
        c.restoreState()
        self.footnotes_page.clear()

    # ---------------------------------------------------------------- blocks -> flowables
    def flowables(self) -> list:
        out = []
        for b in self.d.blocks:
            out.extend(getattr(self, "_f_" + b.kind)(b))
        return out

    def _f_title_page(self, b):
        out = [Spacer(1, 3.2 * cm),
               Paragraph("CORVANE MUTUAL INSURANCE SOCIETY LIMITED",
                         ParagraphStyle("brand", fontName=self.fb, fontSize=10, textColor=self.accent, spaceAfter=10)),
               Paragraph(mk(self.d.title), self.s_title)]
        if self.d.subtitle:
            out.append(Paragraph(mk(self.d.subtitle), self.s_sub))
        for line in b.data.get("extra_lines", []):
            out.append(Paragraph(mk(line), self.s_body))
        out.append(Spacer(1, 0.6 * cm))
        out.extend(self._table_flow(None, b.data["rows"], [5.0, 11.0], kv=True, font_size=None))
        out.append(PageBreak())
        return out

    def _f_toc(self, b):
        out = [Paragraph("Contents", self.s_h[1])]
        depth = b.data.get("depth", 2)
        for lvl, text in self.d.headings:
            if lvl <= depth:
                st = ParagraphStyle("toc", parent=self.s_body, leftIndent=(lvl - 1) * 14, spaceAfter=1.5,
                                    fontName=self.fb if lvl == 1 else self.fn)
                out.append(Paragraph(mk(text), st))
        out.append(PageBreak())
        return out

    def _f_heading(self, b):
        out = []
        if b.data.get("page_break"):
            out.append(PageBreak())
        lvl = min(b.data["level"], 3)
        out.append(Paragraph(mk(b.data["text"]), self.s_h[lvl]))
        return out

    def _f_para(self, b):
        data = b.data
        st = self.s_body
        if data.get("size") or data.get("italic") or data.get("bold") or data.get("align"):
            st = ParagraphStyle("pv", parent=self.s_body, fontSize=data.get("size") or self.s_body.fontSize,
                                fontName=self.fb if data.get("bold") else (self.fi if data.get("italic") else self.fn),
                                alignment=TA_CENTER if data.get("align") == "center" else TA_LEFT)
        text = mk(data["text"])
        out = []
        if data.get("footnote"):
            self.fn_count += 1
            text += f"<super>{self.fn_count}</super>"
            out.append(Paragraph(text, st))
            out.append(_FootnoteMark(self.footnotes_page, self.fn_count, data["footnote"]))
        else:
            out.append(Paragraph(text, st))
        return out

    def _f_bullets(self, b):
        out = []
        for i, item in enumerate(b.data["items"]):
            bullet = f"{i + 1}." if b.data.get("numbered") else "•"
            out.append(Paragraph(mk(item), self.s_bullet, bulletText=bullet))
        return out

    def _f_note(self, b):
        p = Paragraph(f"<b>{mk(b.data.get('label', 'Note'))}:</b> {mk(b.data['text'])}", self.s_cell)
        t = Table([[p]], colWidths=[self.page[0] - 4.4 * cm])
        t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F2F2F2")),
                               ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#A6A6A6")),
                               ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5)]))
        return [t, Spacer(1, 6)]

    def _f_spacer(self, b):
        return [Spacer(1, b.data.get("h", 0.4) * cm)]

    def _f_pagebreak(self, b):
        return [PageBreak()]

    def _f_figure(self, b):
        from PIL import Image as PILImage
        data = b.data
        w_cm = min(data.get("width_cm", 16.0), (self.page[0] / cm) - 4.4)
        with PILImage.open(data["path"]) as im:
            iw, ih = im.size
        h_cm = w_cm * ih / iw
        img = Image(data["path"], width=w_cm * cm, height=h_cm * cm)
        self.fig_no += 1
        cap = Paragraph(mk(f"Figure {self.fig_no}: {data['caption']}"), self.s_cap)
        for f in b.facts:
            if f.where == "image":
                f.anchor_text = f.anchor_text or data["caption"]
        return [KeepTogether([Spacer(1, 4), img, Spacer(1, 3), cap])]

    def _f_table(self, b):
        data = b.data
        out = []
        if data.get("caption"):
            self.tab_no += 1
            out.append(Paragraph(mk(f"Table {self.tab_no}: {data['caption']}"), self.s_tcap))
        out.extend(self._table_flow(data.get("header"), data["rows"], data.get("widths"), kv=data.get("kv"),
                                    font_size=data.get("font_size"), zebra=data.get("zebra"),
                                    first_col_bold=data.get("first_col_bold")))
        out.append(Spacer(1, 6))
        return out

    def _table_flow(self, header, rows, widths, kv=False, font_size=None, zebra=False, first_col_bold=False):
        ncols = len(header) if header else max(len(r) for r in rows)
        page_w = self.page[0] / cm - 4.4
        widths = list(widths or [page_w / ncols] * ncols)
        tot = sum(widths)
        widths = [w * page_w / tot for w in widths] if tot > page_w + 0.01 or kv else widths
        sc = self.s_cell
        sb = self.s_cellb
        if font_size:
            sc = ParagraphStyle("c2", parent=self.s_cell, fontSize=font_size, leading=font_size * 1.25)
            sb = ParagraphStyle("c2b", parent=sc, fontName=self.fb)
        data = []
        if header:
            data.append([Paragraph(mk(h), sb) for h in header])
        for r in rows:
            data.append([Paragraph(mk(r[i] if i < len(r) else ""), sb if (first_col_bold and i == 0) else sc)
                         for i in range(ncols)])
        t = Table(data, colWidths=[w * cm for w in widths], repeatRows=1 if header else 0)
        style = [("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#A6A6A6")),
                 ("VALIGN", (0, 0), (-1, -1), "TOP"),
                 ("TOPPADDING", (0, 0), (-1, -1), 2.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
                 ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 4)]
        if header:
            style.append(("BACKGROUND", (0, 0), (-1, 0), self.accent2))
        if kv:
            style.append(("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#F2F2F2")))
        if zebra:
            for i in range(1 if header else 0, len(data)):
                if i % 2 == 0:
                    style.append(("BACKGROUND", (0, i), (-1, i), colors.HexColor("#F7F7F7")))
        t.setStyle(TableStyle(style))
        return [t]

    # ---------------------------------------------------------------- build
    def render(self, out_path) -> pathlib.Path:
        out_path = pathlib.Path(out_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        w, h = self.page
        doc = BaseDocTemplate(str(out_path), pagesize=self.page, leftMargin=2.2 * cm, rightMargin=2.2 * cm,
                              topMargin=2.1 * cm, bottomMargin=2.9 * cm, title=self.d.title,
                              author=self.d.author, subject=self.d.subtitle or self.d.title,
                              creator="Corvane Document Services", invariant=1)
        frame = Frame(2.2 * cm, 2.9 * cm, w - 4.4 * cm, h - 5.0 * cm, id="body", leftPadding=0, rightPadding=0,
                      topPadding=0, bottomPadding=0)
        doc.addPageTemplates([PageTemplate(id="main", frames=[frame], onPage=self._on_page,
                                           onPageEnd=self._on_page_end)])
        doc.build(self.flowables(), canvasmaker=_NumberedCanvas)
        return out_path


def render_pdf(doc: Doc, out_path) -> pathlib.Path:
    return PdfRenderer(doc).render(out_path)

"""Deck template, shape helpers and fact log for the VS015-VS028 decks.

Everything here is deterministic: no wall clock, no unseeded randomness. Slides use a
16:9 corporate template (navy/teal palette) with the decoration drawn on the slide master,
so slide shape trees only hold content plus a footer and a page number.
"""
from __future__ import annotations

import datetime as _dt
import io
import pathlib
import zipfile
from typing import Any, Iterable, Sequence

from lxml import etree
from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.dml import MSO_LINE_DASH_STYLE
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION, XL_LABEL_POSITION
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Emu, Inches, Pt

from generators.common import util

# ------------------------------------------------------------------------------------------
# Determinism patches: the embedded chart workbook (xlsxwriter) stamps "now" into core.xml.
# ------------------------------------------------------------------------------------------
import pptx.chart.xlsx as _px

_orig_open = _px._BaseWorkbookWriter._open_worksheet


def _open_worksheet_fixed(self, xlsx_file):
    from contextlib import contextmanager
    from xlsxwriter import Workbook

    @contextmanager
    def _cm():
        wb = Workbook(xlsx_file, {"in_memory": True})
        wb.set_properties({"created": util.FIXED_DT, "author": "Corvane Mutual"})
        ws = wb.add_worksheet()
        yield wb, ws
        wb.close()
    return _cm()


_px._BaseWorkbookWriter._open_worksheet = _open_worksheet_fixed

# ------------------------------------------------------------------------------------------
# Palette and geometry
# ------------------------------------------------------------------------------------------
NAVY = RGBColor(0x12, 0x2B, 0x4A)
TEAL = RGBColor(0x0E, 0x7C, 0x86)
TEAL_LT = RGBColor(0xD9, 0xEE, 0xF0)
SAND = RGBColor(0xF4, 0xEF, 0xE6)
GREY = RGBColor(0x5F, 0x6B, 0x7A)
GREY_LT = RGBColor(0xEC, 0xEF, 0xF3)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
BLACK = RGBColor(0x1A, 0x1A, 0x1A)
AMBER = RGBColor(0xE0, 0x8E, 0x0B)
RED = RGBColor(0xB3, 0x26, 0x1E)
GREEN = RGBColor(0x2E, 0x7D, 0x32)
LANE_FILLS = [RGBColor(0xF5, 0xF8, 0xFB), RGBColor(0xEA, 0xF2, 0xF6)]

SLIDE_W_IN = 13.333
SLIDE_H_IN = 7.5
CONTENT_TOP = 1.35
CONTENT_LEFT = 0.55
CONTENT_W = SLIDE_W_IN - 2 * CONTENT_LEFT
CONTENT_BOTTOM = 6.85


def I(x: float) -> Emu:
    return Inches(x)


def fmt_date(d: str, style: str = "long") -> str:
    dt = _dt.date.fromisoformat(str(d)[:10])
    if style == "long":
        return f"{dt.day} {dt.strftime('%B')} {dt.year}"
    if style == "short":
        return f"{dt.day} {dt.strftime('%b')} {dt.year}"
    return dt.isoformat()


def minus_days(d: str, n: int) -> str:
    return (_dt.date.fromisoformat(str(d)[:10]) - _dt.timedelta(days=n)).isoformat()


# ------------------------------------------------------------------------------------------
# Fact log
# ------------------------------------------------------------------------------------------
class FactLog:
    """Collects manifest entries for one deck (fact ids are <FID>-F<nnn>)."""

    def __init__(self, fid: str, rel_file: str):
        self.fid = fid
        self.rel_file = rel_file
        self.entries: list[dict] = []

    def add(self, kind: str, statement: str, locator: dict, needle: str, world_ref: str | None = None,
            exclusive: bool = False, placement: dict | None = None, notes: str | None = None,
            also_in: list | None = None) -> str:
        fact_id = f"{self.fid}-F{len(self.entries) + 1:03d}"
        e: dict[str, Any] = {
            "fact_id": fact_id,
            "world_ref": world_ref,
            "kind": kind,
            "statement": statement,
            "file": self.rel_file,
            "locator": locator,
            "needle": needle,
            "exclusive": exclusive,
            "also_in": list(also_in or []),
        }
        if placement:
            e["placement"] = placement["placement_id"]
            e["placement_key"] = placement["key"]
            e["world_ref"] = placement["world_ref"]
            e["exclusive"] = bool(placement.get("exclusive"))
            e["kind"] = placement["kind"]
            e["also_in"] = list(placement.get("also_in") or [])
        if notes:
            e["notes"] = notes
        self.entries.append(e)
        return fact_id


# ------------------------------------------------------------------------------------------
# Deck
# ------------------------------------------------------------------------------------------
class Deck:
    """A 16:9 Corvane deck with footer, page numbers, notes and fact registration."""

    def __init__(self, W, fid: str, out_dir: pathlib.Path, short_title: str | None = None,
                 version: str = "1.0", classification: str = "Internal"):
        self.W = W
        self.fid = fid
        self.anchor = W.anchor(fid)
        self.date = str(self.anchor["date"])
        self.title = self.anchor["title"]
        self.short_title = short_title or self.title
        self.version = version
        self.classification = classification
        self.author_id = self.anchor["author"]
        self.author = W.name_of(self.author_id, self.date)
        self.author_title = W.title_of(self.author_id, self.date)
        self.out_path = pathlib.Path(out_dir) / self.anchor["filename"]
        self.rel_file = f"corpus/upload/visuals/{self.anchor['filename']}"
        self.facts = FactLog(fid, self.rel_file)
        self.rng = util.rng(f"{fid}:deck")
        self.prs = Presentation()
        self.prs.slide_width = I(SLIDE_W_IN)
        self.prs.slide_height = I(SLIDE_H_IN)
        self._decorate_master()
        self._cxn_count = 0
        self._placements = {p["placement_id"]: p for p in W.placements_for(fid)}
        self._planted: set[str] = set()

    # -------------------------------------------------------------- template
    def _decorate_master(self):
        """Brand bar, rule and wordmark on the slide master (not part of slide shape trees)."""
        tmp = self.prs.slides.add_slide(self.prs.slide_layouts[6])
        bar = tmp.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, I(SLIDE_W_IN), I(0.12))
        self._fill(bar, NAVY)
        acc = tmp.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, I(0.12), I(2.2), I(0.05))
        self._fill(acc, TEAL)
        rule = tmp.shapes.add_shape(MSO_SHAPE.RECTANGLE, I(CONTENT_LEFT), I(7.02), I(CONTENT_W), I(0.012))
        self._fill(rule, GREY)
        wm = tmp.shapes.add_textbox(I(SLIDE_W_IN - 2.6), I(0.2), I(2.1), I(0.3))
        p = wm.text_frame.paragraphs[0]
        p.alignment = PP_ALIGN.RIGHT
        r = p.add_run()
        r.text = "CORVANE MUTUAL"
        r.font.size = Pt(10)
        r.font.bold = True
        r.font.color.rgb = NAVY
        master_tree = self.prs.slide_master.shapes._spTree
        used = [int(x) for x in master_tree.xpath(".//p:cNvPr/@id")]
        nxt = max(used + [1]) + 1
        for sh in list(tmp.shapes):
            el = sh._element
            el.find(".//" + qn("p:cNvPr")).set("id", str(nxt))
            nxt += 1
            master_tree.append(el)
        # drop the scratch slide
        sldIdLst = self.prs.slides._sldIdLst
        sid = sldIdLst[-1]
        self.prs.part.drop_rel(sid.rId)
        sldIdLst.remove(sid)

    @staticmethod
    def _fill(shape, rgb, line=None):
        shape.fill.solid()
        shape.fill.fore_color.rgb = rgb
        if line is None:
            shape.line.fill.background()
        else:
            shape.line.color.rgb = line

    # -------------------------------------------------------------- slides
    @property
    def n(self) -> int:
        return len(self.prs.slides)

    def new_slide(self, title: str, subtitle: str | None = None):
        slide = self.prs.slides.add_slide(self.prs.slide_layouts[5])
        t = slide.shapes.title
        t.left, t.top, t.width, t.height = I(CONTENT_LEFT), I(0.32), I(CONTENT_W - 2.2), I(0.75)
        tf = t.text_frame
        tf.word_wrap = True
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        tf.text = title
        for p in tf.paragraphs:
            p.alignment = PP_ALIGN.LEFT
            for r in p.runs:
                r.font.size = Pt(26 if len(title) < 52 else 22)
                r.font.bold = True
                r.font.color.rgb = NAVY
        if subtitle:
            self.text(slide, CONTENT_LEFT, 1.0, CONTENT_W, 0.35, subtitle, size=13, color=TEAL, italic=True)
        return slide

    def title_slide(self, title: str, subtitle: str, meta_lines: Sequence[str]):
        slide = self.prs.slides.add_slide(self.prs.slide_layouts[0])
        band = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, I(1.6), I(SLIDE_W_IN), I(3.2))
        self._fill(band, NAVY)
        band.name = "Title band"
        accent = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, I(4.8), I(SLIDE_W_IN), I(0.08))
        self._fill(accent, TEAL)
        accent.name = "Title accent"
        # move the band behind the placeholders
        tree = slide.shapes._spTree
        for el in (accent._element, band._element):
            tree.remove(el)
            tree.insert(2, el)
        t = slide.shapes.title
        t.left, t.top, t.width, t.height = I(0.8), I(1.9), I(11.7), I(1.6)
        t.text_frame.word_wrap = True
        t.text_frame.text = title
        for p in t.text_frame.paragraphs:
            p.alignment = PP_ALIGN.LEFT
            for r in p.runs:
                r.font.size = Pt(36 if len(title) < 46 else 30)
                r.font.bold = True
                r.font.color.rgb = WHITE
        st = slide.placeholders[1]
        st.left, st.top, st.width, st.height = I(0.8), I(3.55), I(11.7), I(1.1)
        st.text_frame.word_wrap = True
        st.text_frame.text = subtitle
        for p in st.text_frame.paragraphs:
            p.alignment = PP_ALIGN.LEFT
            for r in p.runs:
                r.font.size = Pt(18)
                r.font.color.rgb = TEAL_LT
        self.text(slide, 0.8, 5.15, 11.5, 1.4, list(meta_lines), size=13, color=GREY)
        return slide

    def section_slide(self, title: str, lead: str):
        slide = self.prs.slides.add_slide(self.prs.slide_layouts[5])
        t = slide.shapes.title
        t.left, t.top, t.width, t.height = I(0.8), I(2.4), I(11.5), I(1.0)
        t.text_frame.text = title
        for p in t.text_frame.paragraphs:
            for r in p.runs:
                r.font.size = Pt(34)
                r.font.bold = True
                r.font.color.rgb = NAVY
        bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, I(0.8), I(3.45), I(1.6), I(0.07))
        self._fill(bar, TEAL)
        bar.name = "Section rule"
        self.text(slide, 0.8, 3.65, 11.0, 1.2, lead, size=16, color=GREY)
        return slide

    # -------------------------------------------------------------- text
    def text(self, slide, x, y, w, h, content, size=14, bold=False, color=BLACK, italic=False,
             align=PP_ALIGN.LEFT, name=None, fill=None, line=None, rotation=0.0, anchor=None,
             bullets=False, font=None, para_space=4, group=None, wrap=True, margin=None):
        shapes = group.shapes if group is not None else slide.shapes
        tb = shapes.add_textbox(I(x), I(y), I(w), I(h))
        tf = tb.text_frame
        tf.word_wrap = wrap
        if margin is not None:
            tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = I(margin)
        if anchor is not None:
            tf.vertical_anchor = anchor
        items = content if isinstance(content, (list, tuple)) else [content]
        first = True
        for item in items:
            level = 0
            b = bold
            txt = item
            if isinstance(item, tuple):
                txt, level = item[0], item[1]
                b = item[2] if len(item) > 2 else bold
            p = tf.paragraphs[0] if first else tf.add_paragraph()
            first = False
            p.alignment = align
            p.level = level
            p.space_after = Pt(para_space)
            r = p.add_run()
            r.text = (("• " if level == 0 else "– ") + txt) if bullets else txt
            r.font.size = Pt(size - 2 * level)
            r.font.bold = b
            r.font.italic = italic
            r.font.color.rgb = color
            if font:
                r.font.name = font
        if fill is not None:
            tb.fill.solid()
            tb.fill.fore_color.rgb = fill
        if line is not None:
            tb.line.color.rgb = line
        if rotation:
            tb.rotation = rotation
        if name:
            tb.name = name
        return tb

    def bullets(self, slide, items, x=CONTENT_LEFT, y=CONTENT_TOP + 0.1, w=CONTENT_W, h=5.2, size=16,
                **kw):
        return self.text(slide, x, y, w, h, items, size=size, bullets=True, para_space=8, **kw)

    def notes(self, slide, text: str):
        slide.notes_slide.notes_text_frame.text = text

    # -------------------------------------------------------------- shapes
    def box(self, slide, x, y, w, h, text, shape=MSO_SHAPE.ROUNDED_RECTANGLE, fill=TEAL_LT,
            line=TEAL, size=12, bold=False, color=NAVY, name=None, group=None, rotation=0.0,
            align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, line_w=1.0, dashed=False):
        shapes = group.shapes if group is not None else slide.shapes
        s = shapes.add_shape(shape, I(x), I(y), I(w), I(h))
        if fill is None:
            s.fill.background()
        else:
            s.fill.solid()
            s.fill.fore_color.rgb = fill
        if line is None:
            s.line.fill.background()
        else:
            s.line.color.rgb = line
            s.line.width = Pt(line_w)
            if dashed:
                s.line.dash_style = MSO_LINE_DASH_STYLE.DASH
        tf = s.text_frame
        tf.word_wrap = True
        tf.vertical_anchor = anchor
        tf.margin_left = tf.margin_right = I(0.05)
        tf.margin_top = tf.margin_bottom = I(0.03)
        lines = text if isinstance(text, (list, tuple)) else [text]
        for i, ln in enumerate(lines):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.alignment = align
            r = p.add_run()
            r.text = ln
            r.font.size = Pt(size if i == 0 else max(size - 2, 8))
            r.font.bold = bold if i == 0 else False
            r.font.color.rgb = color
        if rotation:
            s.rotation = rotation
        if name:
            s.name = name
        return s

    def connect(self, slide, a, b, a_site: int = 3, b_site: int = 1, label: str | None = None,
                name: str | None = None, elbow: bool = False, color=NAVY, dashed: bool = False,
                label_offset=(0.0, -0.32), label_w: float | None = None, label_size: int = 10,
                width_pt: float = 1.5, label_fill=WHITE, label_t: float = 0.5):
        """Native connector glued to two shapes, arrowhead at the end, optional label box.

        The label is a separate text box named 'label:<connector name>' placed near the midpoint
        (the verifier maps it to the connector by name)."""
        self._cxn_count += 1
        cname = name or f"cxn-{self.n:02d}-{self._cxn_count:03d}"
        kind = MSO_CONNECTOR.ELBOW if elbow else MSO_CONNECTOR.STRAIGHT
        c = slide.shapes.add_connector(kind, 0, 0, I(1), I(1))
        c.begin_connect(a, a_site)
        c.end_connect(b, b_site)
        c.name = cname
        c.line.color.rgb = color
        c.line.width = Pt(width_pt)
        if dashed:
            c.line.dash_style = MSO_LINE_DASH_STYLE.DASH
        ln = c.line._get_or_add_ln()
        te = etree.SubElement(ln, qn("a:tailEnd"))
        te.set("type", "triangle")
        te.set("w", "med")
        te.set("len", "med")
        if label:
            mx = (c.begin_x + (c.end_x - c.begin_x) * label_t) / 914400.0
            my = (c.begin_y + (c.end_y - c.begin_y) * label_t) / 914400.0
            lw = label_w or max(0.9, min(3.2, 0.085 * len(label) + 0.3))
            lx = mx - lw / 2 + label_offset[0]
            ly = my + label_offset[1]
            self.text(slide, lx, ly, lw, 0.3, label, size=label_size, color=GREY, italic=True,
                      align=PP_ALIGN.CENTER, name=f"label:{cname}", fill=label_fill, margin=0.02)
        else:
            # Unlabelled arrow: an empty, invisible label placeholder bound to the connector by
            # name, so readers that look for the nearest text box (lane headers, neighbouring
            # boxes) do not mistake other text for this connector's label.
            mx = (c.begin_x + (c.end_x - c.begin_x) * 0.5) / 914400.0
            my = (c.begin_y + (c.end_y - c.begin_y) * 0.5) / 914400.0
            ph = slide.shapes.add_textbox(I(mx - 0.05), I(my - 0.05), I(0.1), I(0.1))
            ph.name = f"label:{cname}"
        return c

    def group(self, slide, name: str):
        g = slide.shapes.add_group_shape()
        g.name = name
        return g

    def lane(self, slide, x, y, w, h, label, idx, name=None, label_w=0.45):
        """Swimlane: tinted band plus a rotated lane header (owner shown only by position)."""
        band = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, I(x), I(y), I(w), I(h))
        band.fill.solid()
        band.fill.fore_color.rgb = LANE_FILLS[idx % 2]
        band.line.color.rgb = GREY_LT
        band.name = name or f"lane-{idx}"
        # rotated header: a text box rotated 270 degrees, centred in a strip at the left of the lane
        hdr_w, hdr_h = h, label_w
        cx, cy = x + label_w / 2, y + h / 2
        tb = self.text(slide, cx - hdr_w / 2, cy - hdr_h / 2, hdr_w, hdr_h, label, size=11, bold=True,
                       color=NAVY, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, rotation=270.0,
                       name=f"lanehdr-{idx}")
        return band, tb

    def table(self, slide, rows: Sequence[Sequence[str]], x=CONTENT_LEFT, y=CONTENT_TOP + 0.1,
              w=CONTENT_W, h=None, col_w: Sequence[float] | None = None, size=11, header=True,
              name=None, row_h=0.36, header_fill=NAVY, zebra=True, bold_first_col=False):
        nrows, ncols = len(rows), len(rows[0])
        h = h or row_h * nrows
        gf = slide.shapes.add_table(nrows, ncols, I(x), I(y), I(w), I(h))
        if name:
            gf.name = name
        tbl = gf.table
        if col_w:
            tot = sum(col_w)
            for i, cw in enumerate(col_w):
                tbl.columns[i].width = I(w * cw / tot)
        for r in range(nrows):
            tbl.rows[r].height = I(row_h)
            for c in range(ncols):
                cell = tbl.cell(r, c)
                cell.margin_left = cell.margin_right = I(0.06)
                cell.margin_top = cell.margin_bottom = I(0.03)
                tf = cell.text_frame
                tf.word_wrap = True
                tf.text = str(rows[r][c])
                for p in tf.paragraphs:
                    for run in p.runs:
                        run.font.size = Pt(size)
                        if header and r == 0:
                            run.font.bold = True
                            run.font.color.rgb = WHITE
                        else:
                            run.font.color.rgb = BLACK
                            run.font.bold = bold_first_col and c == 0
                cell.fill.solid()
                if header and r == 0:
                    cell.fill.fore_color.rgb = header_fill
                else:
                    cell.fill.fore_color.rgb = GREY_LT if (zebra and r % 2 == 0) else WHITE
        return gf

    def picture(self, slide, png: bytes | str | pathlib.Path, x, y, w=None, h=None, alt: str | None = None,
                name: str | None = None):
        src = io.BytesIO(png) if isinstance(png, (bytes, bytearray)) else str(png)
        pic = slide.shapes.add_picture(src, I(x), I(y), I(w) if w else None, I(h) if h else None)
        if name:
            pic.name = name
        if alt is not None:
            pic._element.nvPicPr.cNvPr.set("descr", alt)
        return pic

    @staticmethod
    def set_alt(shape, alt: str):
        el = shape._element
        c = el.find(".//" + qn("p:cNvPr"))
        if c is not None:
            c.set("descr", alt)

    def chart(self, slide, kind: str, categories: Sequence[str], series: dict[str, Sequence[float]],
              x, y, w, h, title: str | None = None, number_format: str = "0.0", legend: bool = True,
              data_labels: bool = True, name: str | None = None, colors: Sequence[RGBColor] | None = None,
              axis_title: str | None = None, font_size: int = 12):
        cd = CategoryChartData(number_format=number_format)
        cd.categories = list(categories)
        for sname, vals in series.items():
            cd.add_series(sname, list(vals))
        ctype = {"bar": XL_CHART_TYPE.BAR_CLUSTERED, "column": XL_CHART_TYPE.COLUMN_CLUSTERED,
                 "line": XL_CHART_TYPE.LINE_MARKERS, "pie": XL_CHART_TYPE.PIE,
                 "doughnut": XL_CHART_TYPE.DOUGHNUT, "stacked": XL_CHART_TYPE.COLUMN_STACKED}[kind]
        gf = slide.shapes.add_chart(ctype, I(x), I(y), I(w), I(h), cd)
        if name:
            gf.name = name
        ch = gf.chart
        ch.font.size = Pt(font_size)
        if title:
            ch.has_title = True
            ch.chart_title.text_frame.text = title
            for p in ch.chart_title.text_frame.paragraphs:
                for r in p.runs:
                    r.font.size = Pt(font_size + 2)
                    r.font.bold = True
        else:
            ch.has_title = False
        ch.has_legend = legend
        if legend:
            ch.legend.position = XL_LEGEND_POSITION.BOTTOM
            ch.legend.include_in_layout = False
        if data_labels:
            plot = ch.plots[0]
            plot.has_data_labels = True
            dl = plot.data_labels
            dl.number_format = number_format
            dl.number_format_is_linked = False
            dl.font.size = Pt(font_size)
        palette = list(colors or [TEAL, NAVY, AMBER, GREY, GREEN, RED])
        if kind in ("pie", "doughnut"):
            pts = ch.plots[0].series[0].points
            for i in range(len(categories)):
                pts[i].format.fill.solid()
                pts[i].format.fill.fore_color.rgb = palette[i % len(palette)]
        else:
            for i, s in enumerate(ch.plots[0].series):
                s.format.fill.solid()
                s.format.fill.fore_color.rgb = palette[i % len(palette)]
                if kind == "line":
                    s.format.line.color.rgb = palette[i % len(palette)]
        if axis_title and kind not in ("pie", "doughnut"):
            va = ch.value_axis
            va.has_title = True
            va.axis_title.text_frame.text = axis_title
        return gf

    # -------------------------------------------------------------- facts
    def fact(self, kind: str, statement: str, slide_no: int, where: str, needle: str,
             world_ref: str | None = None, shape_name: str | None = None, placement: str | None = None,
             notes: str | None = None, exclusive: bool = False, ocr: bool | None = None) -> str:
        loc: dict[str, Any] = {"kind": "pptx_slide", "slide": slide_no, "where": where}
        if shape_name:
            loc["shape_name"] = shape_name
        if ocr or where == "image":
            loc["ocr"] = True
        pl = None
        if placement:
            pl = self._placements[placement]
            self._planted.add(placement)
        return self.facts.add(kind, statement, loc, needle, world_ref=world_ref, exclusive=exclusive,
                              placement=pl, notes=notes)

    def check_placements(self):
        missing = set(self._placements) - self._planted
        if missing:
            raise RuntimeError(f"{self.fid}: placements not planted: {sorted(missing)}")

    # -------------------------------------------------------------- common slides
    def footer_all(self):
        total = self.n
        for i, slide in enumerate(self.prs.slides, 1):
            if i == 1:
                continue
            self.text(slide, CONTENT_LEFT, 7.05, 9.5, 0.3,
                      f"Corvane Mutual  |  {self.short_title}  |  v{self.version}  |  "
                      f"{fmt_date(self.date)}  |  Classification: {self.classification}",
                      size=9, color=GREY, name="Footer")
            self.text(slide, SLIDE_W_IN - 1.6, 7.05, 1.05, 0.3, f"{i} / {total}", size=9, color=GREY,
                      align=PP_ALIGN.RIGHT, name="Slide number")

    def doc_control_slide(self, doc_ref: str, owner_line: str, approvers: Sequence[tuple[str, str, str]],
                          history: Sequence[tuple[str, str, str, str]], distribution: str,
                          status: str | None = None, title: str = "Document control"):
        slide = self.new_slide(title)
        st = status or self.anchor.get("status", "final")
        rows = [["Field", "Value"],
                ["Document", self.title],
                ["Reference", doc_ref],
                ["Version / status", f"{self.version} / {st}"],
                ["Owner", owner_line],
                ["Date", fmt_date(self.date)],
                ["Distribution", distribution]]
        self.table(slide, rows, x=CONTENT_LEFT, y=CONTENT_TOP, w=5.9, col_w=[1.6, 4.3], size=11,
                   row_h=0.42, name="Document properties")
        arows = [["Approver", "Role", "Date"]] + [list(a) for a in approvers]
        self.table(slide, arows, x=6.75, y=CONTENT_TOP, w=6.0, col_w=[1.9, 2.9, 1.2], size=10.5,
                   row_h=0.4, name="Approvals")
        hrows = [["Version", "Date", "Author", "Change"]] + [list(hh) for hh in history]
        self.table(slide, hrows, x=6.75, y=CONTENT_TOP + 0.45 + 0.4 * len(arows), w=6.0,
                   col_w=[0.8, 1.1, 1.5, 2.6], size=10, row_h=0.38, name="Version history")
        return slide

    def agenda_slide(self, items: Sequence[str], title: str = "Agenda"):
        slide = self.new_slide(title)
        for i, it in enumerate(items):
            y = CONTENT_TOP + 0.15 + i * 0.62
            num = self.box(slide, CONTENT_LEFT + 0.2, y, 0.48, 0.48, f"{i + 1:02d}", shape=MSO_SHAPE.OVAL,
                           fill=TEAL, line=None, color=WHITE, size=13, bold=True, name=f"agenda-num-{i + 1}")
            self.text(slide, CONTENT_LEFT + 0.9, y + 0.02, 10.5, 0.45, it, size=17, color=NAVY,
                      anchor=MSO_ANCHOR.MIDDLE, name=f"agenda-item-{i + 1}")
        return slide

    # -------------------------------------------------------------- save
    def save(self) -> pathlib.Path:
        self.check_placements()
        self.footer_all()
        a = self.anchor
        util.set_core_props(self.prs.core_properties, title=self.title, author=self.author,
                            when=_dt.date.fromisoformat(self.date), subject="Corvane Mutual – " + self.short_title,
                            keywords=f"{self.fid}; Corvane Mutual")
        self.prs.core_properties.category = a.get("status", "")
        self.out_path.parent.mkdir(parents=True, exist_ok=True)
        buf = io.BytesIO()
        self.prs.save(buf)
        normalised = normalise_zip(buf.getvalue())
        self.out_path.write_bytes(normalised)
        return self.out_path


def normalise_zip(data: bytes) -> bytes:
    """Rewrite an OOXML zip with fixed member timestamps (byte-stable output)."""
    src = zipfile.ZipFile(io.BytesIO(data))
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as dst:
        for info in src.infolist():
            zi = zipfile.ZipInfo(info.filename, date_time=(2026, 11, 1, 9, 0, 0))
            zi.compress_type = zipfile.ZIP_DEFLATED
            zi.external_attr = 0o600 << 16
            dst.writestr(zi, src.read(info.filename))
    return out.getvalue()

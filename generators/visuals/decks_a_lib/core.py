"""Corvane corporate deck template, shape helpers and the facts registry for VS001-VS014.

Every deck is built through :class:`Deck`. Coordinates are inches on a 13.333 x 7.5 in (16:9)
slide. The template uses real slide layouts (Title Slide, Section Header, Title Only) on a
branded slide master, so slide titles live in title placeholders.
"""
from __future__ import annotations

import datetime as _dt
import io
import pathlib
import zipfile
from typing import Any, Iterable

from lxml import etree
from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_LABEL_POSITION, XL_LEGEND_POSITION
from pptx.enum.dml import MSO_LINE_DASH_STYLE
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Emu, Inches, Pt

from generators.common import util

SLIDE_W = 13.333
SLIDE_H = 7.5
ZIP_DT = (2026, 11, 1, 9, 0, 0)

C = {
    "navy": "0B2545", "navy2": "13315C", "teal": "13807A", "teal_l": "D7EFEC", "teal_m": "8FCFC8",
    "sky": "3D7EBF", "sky_l": "DCEAF7", "amber": "E39B2D", "amber_l": "FCEBD2", "slate": "4A5560",
    "grey": "7D8790", "grey_l": "EEF1F4", "grey_m": "D5DBE1", "line": "9AA5B1", "red": "B83A3A",
    "red_l": "F6DCDC", "green": "2E8B57", "green_l": "DDF0E4", "white": "FFFFFF", "ink": "1B2430",
    "plum": "6C4A8E", "plum_l": "EAE1F3",
}

CHART = {
    "column": XL_CHART_TYPE.COLUMN_CLUSTERED, "bar": XL_CHART_TYPE.BAR_CLUSTERED,
    "line": XL_CHART_TYPE.LINE_MARKERS, "stacked": XL_CHART_TYPE.COLUMN_STACKED,
    "pie": XL_CHART_TYPE.PIE, "doughnut": XL_CHART_TYPE.DOUGHNUT,
}

FAMILY_DIRS = util.FAMILY_DIRS

_OTHER_FACTS: list[dict] | None = None


def _other_manifest_facts() -> list[dict]:
    """Facts from the other families' manifests (read-only), used to map also_in file ids
    to the partner fact ids when the partner agent has already written its manifest."""
    global _OTHER_FACTS
    if _OTHER_FACTS is None:
        import yaml
        _OTHER_FACTS = []
        for m in sorted(util.MANIFESTS.glob("*.facts.yaml")):
            if m.name.startswith("visuals.decks_a."):
                continue
            try:
                data = yaml.safe_load(m.read_text(encoding="utf-8")) or []
            except Exception:  # noqa: BLE001 - a partner manifest mid-write is not our problem
                continue
            _OTHER_FACTS.extend(e for e in data if isinstance(e, dict) and e.get("fact_id"))
    return _OTHER_FACTS


def rgb(h: str) -> RGBColor:
    return RGBColor.from_string(C.get(h, h))


def _patch_xlsxwriter() -> None:
    """Embedded chart workbooks get a fixed creation date (byte-stable output)."""
    import xlsxwriter
    if getattr(xlsxwriter.Workbook, "_cm_patched", False):
        return
    orig = xlsxwriter.Workbook.__init__

    def init(self, *a, **k):
        orig(self, *a, **k)
        self.set_properties({"created": util.FIXED_DT})

    xlsxwriter.Workbook.__init__ = init
    xlsxwriter.Workbook._cm_patched = True


_patch_xlsxwriter()


def normalize_zip(data: bytes) -> bytes:
    """Rewrite an OOXML package with fixed member timestamps (deterministic bytes)."""
    zin = zipfile.ZipFile(io.BytesIO(data))
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zout:
        for info in zin.infolist():
            zi = zipfile.ZipInfo(info.filename, date_time=ZIP_DT)
            zi.compress_type = zipfile.ZIP_DEFLATED
            zi.external_attr = 0o600 << 16
            zout.writestr(zi, zin.read(info.filename))
    return out.getvalue()


# ---------------------------------------------------------------------------------------------
# Template
# ---------------------------------------------------------------------------------------------

def _brand_master(prs) -> None:
    """Put the Corvane band, title accent, wordmark and footer rule on the slide master."""
    tmp = prs.slides.add_slide(prs.slide_layouts[6])
    sh = tmp.shapes
    band = sh.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(SLIDE_W), Inches(0.10))
    band.fill.solid(); band.fill.fore_color.rgb = rgb("navy"); band.line.fill.background()
    acc = sh.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.5), Inches(1.10), Inches(1.0), Inches(0.05))
    acc.fill.solid(); acc.fill.fore_color.rgb = rgb("teal"); acc.line.fill.background()
    rule = sh.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(0.5), Inches(7.0), Inches(SLIDE_W - 0.5), Inches(7.0))
    rule.line.color.rgb = rgb("grey_m"); rule.line.width = Pt(0.75)
    wm = sh.add_textbox(Inches(10.6), Inches(0.26), Inches(2.25), Inches(0.36))
    tf = wm.text_frame; tf.margin_left = tf.margin_right = 0
    p = tf.paragraphs[0]; p.alignment = PP_ALIGN.RIGHT
    r = p.add_run(); r.text = "CORVANE MUTUAL"; r.font.size = Pt(11); r.font.bold = True
    r.font.color.rgb = rgb("teal")
    master_tree = prs.slide_master.shapes._spTree
    elems = [e for e in tmp.shapes._spTree if etree.QName(e).localname in ("sp", "cxnSp")]
    for k, e in enumerate(elems):
        for c in e.iter(qn("p:cNvPr")):
            c.set("id", str(900 + k))
            c.set("name", f"Brand {k + 1}")
        master_tree.insert(2 + k, e)
    # drop the temporary slide
    sld_ids = prs.slides._sldIdLst
    last = sld_ids[-1]
    prs.part.drop_rel(last.rId)
    sld_ids.remove(last)


def new_presentation():
    prs = Presentation()
    k = SLIDE_W / 10.0
    for layout in prs.slide_layouts:
        for ph in layout.placeholders:
            ph.left, ph.width = int(ph.left * k), int(ph.width * k)
    for ph in prs.slide_master.placeholders:
        ph.left, ph.width = int(ph.left * k), int(ph.width * k)
    prs.slide_width = Inches(SLIDE_W)
    prs.slide_height = Inches(SLIDE_H)
    _brand_master(prs)
    return prs


# ---------------------------------------------------------------------------------------------
# Text helpers
# ---------------------------------------------------------------------------------------------

def _bullet(p, level: int = 0, char: str = "•") -> None:
    pPr = p._p.get_or_add_pPr()
    mar = 228600 + level * 285750
    pPr.set("marL", str(mar))
    pPr.set("indent", str(-228600))
    for tag in ("a:buNone", "a:buChar", "a:buAutoNum", "a:buFont"):
        for old in pPr.findall(qn(tag)):
            pPr.remove(old)
    bf = etree.SubElement(pPr, qn("a:buFont")); bf.set("typeface", "Arial")
    bc = etree.SubElement(pPr, qn("a:buChar")); bc.set("char", char)


def fill_text(tf, paras, size=12, color="ink", bold=False, align=None, italic=False,
              space_after=None, font=None) -> None:
    """Fill a text frame. ``paras``: str, or list of str / dict(text, size, bold, color, level,
    bullet, italic, align, runs=[(text, {bold, color, size, italic})])."""
    if isinstance(paras, str):
        paras = [paras]
    first = True
    for item in paras:
        if isinstance(item, str):
            item = {"text": item}
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        al = item.get("align", align)
        if al is not None:
            p.alignment = {"l": PP_ALIGN.LEFT, "c": PP_ALIGN.CENTER, "r": PP_ALIGN.RIGHT}.get(al, al)
        if item.get("bullet"):
            _bullet(p, item.get("level", 0), item.get("char", "•"))
        sa = item.get("space_after", space_after)
        if sa is not None:
            p.space_after = Pt(sa)
        runs = item.get("runs") or [(item.get("text", ""), {})]
        for text, st in runs:
            r = p.add_run()
            r.text = text
            f = r.font
            f.size = Pt(st.get("size", item.get("size", size)))
            f.bold = st.get("bold", item.get("bold", bold))
            f.italic = st.get("italic", item.get("italic", italic))
            f.color.rgb = rgb(st.get("color", item.get("color", color)))
            if font or st.get("font"):
                f.name = st.get("font", font)


# ---------------------------------------------------------------------------------------------
# Canvas: shape-creating helpers shared by slides and group shapes
# ---------------------------------------------------------------------------------------------

STYLES = {
    "process": dict(shape=MSO_SHAPE.ROUNDED_RECTANGLE, fill="sky_l", line="sky", color="ink"),
    "step": dict(shape=MSO_SHAPE.ROUNDED_RECTANGLE, fill="white", line="navy2", color="ink"),
    "decision": dict(shape=MSO_SHAPE.DIAMOND, fill="amber_l", line="amber", color="ink"),
    "terminal": dict(shape=MSO_SHAPE.ROUNDED_RECTANGLE, fill="navy", line="navy", color="white"),
    "outcome": dict(shape=MSO_SHAPE.ROUNDED_RECTANGLE, fill="teal_l", line="teal", color="ink"),
    "alert": dict(shape=MSO_SHAPE.ROUNDED_RECTANGLE, fill="red_l", line="red", color="ink"),
    "system": dict(shape=MSO_SHAPE.RECTANGLE, fill="grey_l", line="slate", color="ink"),
    "service": dict(shape=MSO_SHAPE.ROUNDED_RECTANGLE, fill="white", line="teal", color="ink"),
    "external": dict(shape=MSO_SHAPE.RECTANGLE, fill="plum_l", line="plum", color="ink"),
    "org": dict(shape=MSO_SHAPE.RECTANGLE, fill="white", line="navy2", color="ink"),
    "org_head": dict(shape=MSO_SHAPE.RECTANGLE, fill="navy", line="navy", color="white"),
    "org_vacant": dict(shape=MSO_SHAPE.RECTANGLE, fill="grey_l", line="grey", color="slate"),
    "data": dict(shape=MSO_SHAPE.FLOWCHART_DATA, fill="grey_l", line="slate", color="ink"),
    "doc": dict(shape=MSO_SHAPE.FLOWCHART_DOCUMENT, fill="white", line="slate", color="ink"),
    "chevron": dict(shape=MSO_SHAPE.CHEVRON, fill="teal", line="teal", color="white"),
    "pentagon": dict(shape=MSO_SHAPE.PENTAGON, fill="navy2", line="navy2", color="white"),
    "tile": dict(shape=MSO_SHAPE.RECTANGLE, fill="grey_l", line=None, color="ink"),
    "plain": dict(shape=MSO_SHAPE.RECTANGLE, fill=None, line=None, color="ink"),
}


class Canvas:
    def __init__(self, deck: "Deck", shapes, slide_ctx: "S"):
        self.deck = deck
        self.shapes = shapes
        self.ctx = slide_ctx

    # -- primitives --------------------------------------------------------------------------
    def text(self, x, y, w, h, paras, size=12, color="ink", bold=False, align=None,
             anchor="t", name=None, rotation=0, fill=None, line=None, italic=False,
             margins=0.04, wrap=True, space_after=None):
        tb = self.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
        tf = tb.text_frame
        tf.word_wrap = wrap
        tf.margin_left = tf.margin_right = Inches(margins)
        tf.margin_top = tf.margin_bottom = Inches(margins * 0.6)
        tf.vertical_anchor = {"t": MSO_ANCHOR.TOP, "m": MSO_ANCHOR.MIDDLE, "b": MSO_ANCHOR.BOTTOM}[anchor]
        fill_text(tf, paras, size=size, color=color, bold=bold, align=align, italic=italic,
                  space_after=space_after)
        if fill:
            tb.fill.solid(); tb.fill.fore_color.rgb = rgb(fill)
        if line:
            tb.line.color.rgb = rgb(line); tb.line.width = Pt(0.75)
        if rotation:
            tb.rotation = rotation
        if name:
            tb.name = name
        return tb

    def bullets(self, x, y, w, h, items, size=14, color="ink", name=None, space_after=6):
        paras = []
        for it in items:
            if isinstance(it, tuple):
                lvl, txt = it
            else:
                lvl, txt = 0, it
            if isinstance(txt, dict):
                d = dict(txt)
                d.setdefault("bullet", True)
                d.setdefault("level", lvl)
                d.setdefault("size", size - 2 * lvl)
                paras.append(d)
            else:
                paras.append({"text": txt, "bullet": True, "level": lvl, "size": size - 2 * lvl})
        return self.text(x, y, w, h, paras, size=size, color=color, name=name, space_after=space_after)

    def box(self, x, y, w, h, text="", style="process", size=11, bold=False, name=None,
            fill=None, line=None, color=None, align="c", anchor="m", line_w=1.25, dash=False,
            shape=None, rotation=0, margins=0.05):
        st = STYLES[style]
        shp = self.shapes.add_shape(shape or st["shape"], Inches(x), Inches(y), Inches(w), Inches(h))
        f = fill if fill is not None else st["fill"]
        ln = line if line is not None else st["line"]
        if f:
            shp.fill.solid(); shp.fill.fore_color.rgb = rgb(f)
        else:
            shp.fill.background()
        if ln:
            shp.line.color.rgb = rgb(ln); shp.line.width = Pt(line_w)
            if dash:
                shp.line.dash_style = MSO_LINE_DASH_STYLE.DASH
        else:
            shp.line.fill.background()
        shp.shadow.inherit = False
        tf = shp.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_right = Inches(margins)
        tf.margin_top = tf.margin_bottom = Inches(margins * 0.6)
        tf.vertical_anchor = {"t": MSO_ANCHOR.TOP, "m": MSO_ANCHOR.MIDDLE, "b": MSO_ANCHOR.BOTTOM}[anchor]
        if text:
            fill_text(tf, text, size=size, color=color or st["color"], bold=bold, align=align)
        if rotation:
            shp.rotation = rotation
        if name:
            shp.name = name
        return shp

    def org(self, x, y, w, h, name, title, extra=None, style="org", size=11, shape_name=None):
        paras = [{"text": name, "bold": True, "size": size + 1}, {"text": title, "size": size}]
        if extra:
            paras.append({"text": extra, "size": size - 2, "italic": True,
                          "color": "grey" if style == "org" else "teal_m"})
        return self.box(x, y, w, h, paras, style=style, name=shape_name, margins=0.06)

    def rect(self, x, y, w, h, fill="grey_l", line=None, name=None, line_w=0.75, dash=False):
        return self.box(x, y, w, h, "", style="plain", fill=fill, line=line, name=name,
                        line_w=line_w, dash=dash)

    def table(self, x, y, w, header, rows, col_w=None, row_h=0.3, size=10, name=None,
              header_fill="navy", zebra=True, first_col_bold=False, wrap=True, align=None):
        nrows, ncols = len(rows) + 1, len(header)
        gf = self.shapes.add_table(nrows, ncols, Inches(x), Inches(y), Inches(w), Inches(row_h * nrows))
        if name:
            gf.name = name
        tbl = gf.table
        if col_w:
            tot = sum(col_w)
            for i, cw in enumerate(col_w):
                tbl.columns[i].width = Inches(w * cw / tot)
        for r in range(nrows):
            tbl.rows[r].height = Inches(row_h)
            for c in range(ncols):
                cell = tbl.cell(r, c)
                val = header[c] if r == 0 else rows[r - 1][c]
                cell.text = "" if val is None else str(val)
                cell.margin_left = cell.margin_right = Inches(0.06)
                cell.margin_top = cell.margin_bottom = Inches(0.03)
                cell.vertical_anchor = MSO_ANCHOR.MIDDLE
                tf = cell.text_frame
                tf.word_wrap = wrap
                for p in tf.paragraphs:
                    if align and c < len(align) and align[c]:
                        p.alignment = {"l": PP_ALIGN.LEFT, "c": PP_ALIGN.CENTER, "r": PP_ALIGN.RIGHT}[align[c]]
                    for run in p.runs:
                        run.font.size = Pt(size)
                        run.font.bold = r == 0 or (first_col_bold and c == 0)
                        run.font.color.rgb = rgb("white" if r == 0 else "ink")
                cell.fill.solid()
                if r == 0:
                    cell.fill.fore_color.rgb = rgb(header_fill)
                else:
                    cell.fill.fore_color.rgb = rgb("grey_l" if (zebra and r % 2 == 0) else "white")
        return gf

    def chart(self, x, y, w, h, ctype, categories, series, title=None, number_format="General",
              legend=None, labels=True, colors=None, name=None, font_size=11, gap_width=70,
              label_format=None, axis_max=None, axis_min=None):
        cd = CategoryChartData()
        cd.categories = list(categories)
        for sname, vals in series:
            cd.add_series(sname, list(vals), number_format=number_format)
        gf = self.shapes.add_chart(CHART[ctype], Inches(x), Inches(y), Inches(w), Inches(h), cd)
        if name:
            gf.name = name
        ch = gf.chart
        ch.font.size = Pt(font_size)
        if title:
            ch.has_title = True
            ch.chart_title.text_frame.text = title
            for p in ch.chart_title.text_frame.paragraphs:
                for r in p.runs:
                    r.font.size = Pt(font_size + 2); r.font.bold = True; r.font.color.rgb = rgb("navy")
        else:
            ch.has_title = False
        show_leg = legend if legend is not None else (len(series) > 1 or ctype in ("pie", "doughnut"))
        ch.has_legend = show_leg
        if show_leg:
            ch.legend.position = XL_LEGEND_POSITION.BOTTOM
            ch.legend.include_in_layout = False
        plot = ch.plots[0]
        if ctype in ("column", "bar", "stacked"):
            plot.gap_width = gap_width
        if labels:
            plot.has_data_labels = True
            dl = plot.data_labels
            dl.font.size = Pt(font_size - 1)
            if label_format:
                dl.number_format = label_format
                dl.number_format_is_linked = False
            if ctype in ("column", "bar"):
                dl.position = XL_LABEL_POSITION.OUTSIDE_END
        palette = colors or ["navy", "teal", "amber", "sky", "plum", "grey"]
        if ctype in ("pie", "doughnut"):
            for i, pt in enumerate(plot.series[0].points):
                pt.format.fill.solid(); pt.format.fill.fore_color.rgb = rgb(palette[i % len(palette)])
        else:
            for i, s in enumerate(plot.series):
                col = rgb(palette[i % len(palette)])
                if ctype == "line":
                    s.format.line.color.rgb = col
                    s.format.line.width = Pt(2.5)
                    s.smooth = False
                else:
                    s.format.fill.solid(); s.format.fill.fore_color.rgb = col
            try:
                va = ch.value_axis
                va.has_major_gridlines = True
                va.major_gridlines.format.line.color.rgb = rgb("grey_m")
                va.tick_labels.font.size = Pt(font_size - 1)
                if axis_max is not None:
                    va.maximum_scale = axis_max
                if axis_min is not None:
                    va.minimum_scale = axis_min
                ch.category_axis.tick_labels.font.size = Pt(font_size - 1)
            except Exception:
                pass
        return gf

    def picture(self, png: bytes, x, y, w=None, h=None, alt=None, title=None, name=None):
        pic = self.shapes.add_picture(io.BytesIO(png), Inches(x), Inches(y),
                                      Inches(w) if w else None, Inches(h) if h else None)
        c = pic._element.nvPicPr.cNvPr
        if alt:
            c.set("descr", alt)
        if title:
            c.set("title", title)
        if name:
            pic.name = name
        return pic

    def picture_fit(self, png: bytes, x, y, max_w, max_h, alt=None, title=None, name=None, align="c"):
        """Picture scaled to fit inside (max_w x max_h), aspect preserved, centred horizontally."""
        from PIL import Image
        with Image.open(io.BytesIO(png)) as im:
            pw, ph = im.size
        scale = min(max_w / pw, max_h / ph)
        w, h = pw * scale, ph * scale
        px = x + (max_w - w) / 2 if align == "c" else x
        return self.picture(png, px, y, w=w, h=h, alt=alt, title=title, name=name)

    def group(self, name: str) -> "G":
        grp = self.shapes.add_group_shape()
        grp.name = name
        return G(self.deck, grp, self.ctx)


class G(Canvas):
    """Canvas over a group shape (nested groups supported)."""

    def __init__(self, deck, grp, ctx):
        super().__init__(deck, grp.shapes, ctx)
        self.grp = grp

    @property
    def name(self):
        return self.grp.name


def _site(shape, which: str) -> tuple[float, float]:
    l, t, w, h = shape.left, shape.top, shape.width, shape.height
    return {"t": (l + w / 2, t), "b": (l + w / 2, t + h), "l": (l, t + h / 2), "r": (l + w, t + h / 2)}[which]


SITE_IDX = {"t": 0, "l": 1, "b": 2, "r": 3}


class S(Canvas):
    """One slide."""

    def __init__(self, deck: "Deck", slide, n: int, kind: str):
        super().__init__(deck, slide.shapes, self)
        self.slide = slide
        self.n = n
        self.kind = kind
        self._cxn = 0

    def notes(self, text: str) -> None:
        tf = self.slide.notes_slide.notes_text_frame
        tf.text = text

    def connect(self, a, b, label=None, a_site=None, b_site=None, kind="straight", name=None,
                arrow=True, color="slate", width=1.5, label_dx=0.0, label_dy=0.0, label_w=None,
                label_size=10, dash=False, label_fill="white"):
        """Connector glued to shapes ``a`` -> ``b`` (arrowhead at b). The label is a small text
        box named 'label:<connector name>' near the midpoint."""
        ax, ay = a.left + a.width / 2, a.top + a.height / 2
        bx, by = b.left + b.width / 2, b.top + b.height / 2
        if a_site is None or b_site is None:
            dx, dy = bx - ax, by - ay
            if abs(dx) * 0.75 > abs(dy):
                sa, sb = ("r", "l") if dx > 0 else ("l", "r")
            else:
                sa, sb = ("b", "t") if dy > 0 else ("t", "b")
            a_site = a_site or sa
            b_site = b_site or sb
        p1, p2 = _site(a, a_site), _site(b, b_site)
        ctype = {"straight": MSO_CONNECTOR.STRAIGHT, "elbow": MSO_CONNECTOR.ELBOW}[kind]
        cx = self.slide.shapes.add_connector(ctype, Emu(int(p1[0])), Emu(int(p1[1])),
                                             Emu(int(p2[0])), Emu(int(p2[1])))
        cx.begin_connect(a, SITE_IDX[a_site])
        cx.end_connect(b, SITE_IDX[b_site])
        self._cxn += 1
        cname = name or f"flow-{self.n}-{self._cxn}"
        cx.name = cname
        cx.line.color.rgb = rgb(color)
        cx.line.width = Pt(width)
        if dash:
            cx.line.dash_style = MSO_LINE_DASH_STYLE.DASH
        if arrow:
            ln = cx._element.spPr.find(qn("a:ln"))
            t = etree.SubElement(ln, qn("a:tailEnd"))
            t.set("type", "triangle"); t.set("w", "med"); t.set("len", "med")
        if label:
            mx = (p1[0] + p2[0]) / 2 / 914400.0
            my = (p1[1] + p2[1]) / 2 / 914400.0
            lw = label_w or max(0.45, min(3.4, 0.072 * len(label) * label_size / 10 + 0.2))
            lh = 0.26 if label_size <= 10 else 0.32
            self.text(mx - lw / 2 + label_dx, my - lh / 2 + label_dy, lw, lh,
                      [{"text": label, "align": "c"}], size=label_size, color="navy", bold=True,
                      anchor="m", fill=label_fill, name=f"label:{cname}", margins=0.02)
        return cx


# ---------------------------------------------------------------------------------------------
# Deck
# ---------------------------------------------------------------------------------------------

class Deck:
    def __init__(self, W, fid: str, version: str, doc_ref: str, classification: str = "Internal",
                 out_dir: pathlib.Path | None = None):
        self.W = W
        self.fid = fid
        self.anchor = W.anchor(fid)
        self.date = str(self.anchor["date"])
        self.d = _dt.date.fromisoformat(self.date)
        self.author_pid = self.anchor["author"]
        self.author = W.name_of(self.author_pid, self.date)
        self.author_title = W.title_of(self.author_pid, self.date)
        self.title = self.anchor["title"]
        self.filename = self.anchor["filename"]
        self.version = version
        self.doc_ref = doc_ref
        self.classification = classification
        self.prs = new_presentation()
        self.slides: list[S] = []
        self.facts: list[dict] = []
        self.rng = util.rng(f"{fid}:deck")
        out_dir = out_dir or (util.UPLOAD / "visuals")
        self.path = pathlib.Path(out_dir) / self.filename
        self.rel = f"corpus/upload/visuals/{self.filename}"
        self.placements = {p["key"]: p for p in W.placements_for(fid)}
        self._placed: set[str] = set()

    # -- world guards ------------------------------------------------------------------------
    def ok(self, ref: str, field: str | None = None) -> bool:
        return self.W.may_state(self.fid, ref, field)

    def need(self, ref: str, field: str | None = None) -> None:
        if not self.W.may_state(self.fid, ref, field):
            raise RuntimeError(f"{self.fid}: not allowed to state {ref}#{field}")

    def who(self, pid: str) -> tuple[str, str]:
        return self.W.name_of(pid, self.date), self.W.title_of(pid, self.date)

    def date_long(self, iso: str | None = None) -> str:
        d = _dt.date.fromisoformat(iso or self.date)
        return f"{d.day} {d.strftime('%B %Y')}"

    # -- slides ------------------------------------------------------------------------------
    def _new(self, layout_idx: int, kind: str) -> S:
        slide = self.prs.slides.add_slide(self.prs.slide_layouts[layout_idx])
        s = S(self, slide, len(self.slides) + 1, kind)
        self.slides.append(s)
        return s

    def _bg(self, s: S, color="navy") -> None:
        r = s.slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(SLIDE_W), Inches(SLIDE_H))
        r.fill.solid(); r.fill.fore_color.rgb = rgb(color); r.line.fill.background()
        r.name = "Background"
        tree = s.slide.shapes._spTree
        tree.remove(r._element)
        tree.insert(2, r._element)

    def title_slide(self, title: str, subtitle: str, meta: list[str]) -> S:
        s = self._new(0, "title")
        self._bg(s, "navy")
        band = s.slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, Inches(5.25), Inches(SLIDE_W), Inches(0.08))
        band.fill.solid(); band.fill.fore_color.rgb = rgb("teal"); band.line.fill.background()
        band.name = "Accent band"
        ph = s.slide.shapes.title
        ph.left, ph.top, ph.width, ph.height = Inches(0.8), Inches(1.7), Inches(11.5), Inches(1.6)
        ph.text_frame.text = title
        ph.text_frame.word_wrap = True
        for p in ph.text_frame.paragraphs:
            p.alignment = PP_ALIGN.LEFT
            for r in p.runs:
                r.font.size = Pt(38); r.font.bold = True; r.font.color.rgb = rgb("white")
        sub = s.slide.placeholders[1]
        sub.left, sub.top, sub.width, sub.height = Inches(0.8), Inches(3.35), Inches(11.5), Inches(1.0)
        sub.text_frame.text = subtitle
        for p in sub.text_frame.paragraphs:
            p.alignment = PP_ALIGN.LEFT
            for r in p.runs:
                r.font.size = Pt(18); r.font.color.rgb = rgb("teal_m")
        s.text(0.8, 5.5, 8.5, 1.2, [{"text": m, "size": 12, "color": "grey_m"} for m in meta], size=12)
        s.text(9.6, 0.45, 3.2, 0.4, [{"text": "CORVANE MUTUAL", "align": "r"}], size=14, bold=True,
               color="white")
        return s

    def section(self, number: str, title: str, blurb: str | None = None) -> S:
        s = self._new(2, "section")
        self._bg(s, "navy2")
        s.text(0.8, 1.9, 2.0, 1.0, [{"text": number}], size=54, bold=True, color="teal_m")
        ph = s.slide.shapes.title
        ph.left, ph.top, ph.width, ph.height = Inches(0.8), Inches(3.0), Inches(11.0), Inches(1.1)
        ph.text_frame.text = title
        for p in ph.text_frame.paragraphs:
            p.alignment = PP_ALIGN.LEFT
            for r in p.runs:
                r.font.size = Pt(34); r.font.bold = True; r.font.color.rgb = rgb("white")
        for ph2 in list(s.slide.placeholders):
            if ph2.placeholder_format.idx == 1:
                if blurb:
                    ph2.left, ph2.top, ph2.width, ph2.height = Inches(0.8), Inches(4.2), Inches(10.5), Inches(1.0)
                    ph2.text_frame.text = blurb
                    for p in ph2.text_frame.paragraphs:
                        p.alignment = PP_ALIGN.LEFT
                        for r in p.runs:
                            r.font.size = Pt(16); r.font.color.rgb = rgb("grey_m")
                else:
                    ph2._element.getparent().remove(ph2._element)
        return s

    def content(self, title: str, kicker: str | None = None) -> S:
        s = self._new(5, "content")
        ph = s.slide.shapes.title
        ph.left, ph.top, ph.width, ph.height = Inches(0.5), Inches(0.36), Inches(10.0), Inches(0.7)
        ph.text_frame.text = title
        ph.text_frame.word_wrap = True
        ph.text_frame.vertical_anchor = MSO_ANCHOR.BOTTOM
        for p in ph.text_frame.paragraphs:
            p.alignment = PP_ALIGN.LEFT
            for r in p.runs:
                r.font.size = Pt(24 if len(title) < 60 else 20); r.font.bold = True
                r.font.color.rgb = rgb("navy")
        if kicker:
            s.text(0.5, 0.14, 8.0, 0.26, [{"text": kicker.upper()}], size=9, bold=True, color="teal")
        return s

    # -- facts -------------------------------------------------------------------------------
    def fact(self, slide, where: str, needle: str, statement: str, kind: str = "general",
             world_ref: str | None = None, exclusive: bool = False, shape_name: str | None = None,
             notes: str | None = None, also_in: list[str] | None = None,
             placement: tuple[str, str] | None = None, extra: dict | None = None) -> dict:
        n = slide if isinstance(slide, int) else slide.n
        loc: dict[str, Any] = {"kind": "pptx_slide", "slide": n, "where": where}
        if shape_name:
            loc["shape_name"] = shape_name
        if where == "image":
            loc["ocr"] = True
        e: dict[str, Any] = {"fact_id": None, "world_ref": world_ref, "kind": kind,
                             "statement": statement, "file": self.rel, "locator": loc,
                             "needle": needle, "exclusive": bool(exclusive), "also_in": list(also_in or [])}
        if placement:
            e["placement"], e["placement_key"] = placement
        if notes:
            e["notes"] = notes
        if extra:
            e.update(extra)
        self.facts.append(e)
        return e

    def place(self, key: str, slide, where: str, needle: str, statement: str | None = None,
              shape_name: str | None = None, notes: str | None = None, kind: str | None = None) -> dict:
        p = self.placements[key]
        also = []
        for f in p.get("also_in", []) or []:
            a = self.W.anchors_by_id.get(f)
            if not a:
                also.append(f)
                continue
            fam = FAMILY_DIRS.get(f[:2])
            path = f"corpus/upload/{fam}/{a['filename']}" if fam else f
            # Prefer the partner's fact ids: a fact in that file that points back at this deck,
            # or that carries exactly the same world_ref; otherwise list the file path.
            ids = sorted({e["fact_id"] for e in _other_manifest_facts()
                          if e.get("file") == path and (self.rel in (e.get("also_in") or [])
                                                       or e.get("world_ref") == p["world_ref"])})
            also.extend(ids or [path])
        self._placed.add(key)
        return self.fact(slide, where, needle, statement or p["fact"], kind=kind or p["kind"],
                         world_ref=p["world_ref"], exclusive=bool(p.get("exclusive")),
                         shape_name=shape_name, notes=notes, also_in=also,
                         placement=(p["placement_id"], key))

    def finalize_facts(self) -> list[dict]:
        missing = set(self.placements) - self._placed
        if missing:
            raise RuntimeError(f"{self.fid}: placements not planted: {sorted(missing)}")
        for k, e in enumerate(self.facts, 1):
            e["fact_id"] = f"{self.fid}-F{k:03d}"
        return self.facts

    # -- output ------------------------------------------------------------------------------
    def _footers(self) -> None:
        total = len(self.slides)
        for s in self.slides:
            light = s.kind in ("title", "section")
            col = "grey_m" if light else "grey"
            left = f"Corvane Mutual Insurance Society Limited  |  {self.doc_ref} v{self.version}  |  {self.date_long()}"
            s.text(0.5, 7.06, 8.6, 0.28, [{"text": left}], size=8, color=col, name="Footer")
            s.text(9.2, 7.06, 2.4, 0.28, [{"text": f"Classification: {self.classification}", "align": "r"}],
                   size=8, color=col, name="Classification")
            s.text(11.7, 7.06, 1.13, 0.28, [{"text": f"{s.n} / {total}", "align": "r"}], size=8,
                   color=col, bold=True, name="Slide Number")

    def save(self, subject: str = "", keywords: str = "") -> pathlib.Path:
        self._footers()
        util.set_core_props(self.prs.core_properties, self.title, self.author, self.d,
                            subject=subject, keywords=keywords)
        buf = io.BytesIO()
        self.prs.save(buf)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_bytes(normalize_zip(buf.getvalue()))
        return self.path

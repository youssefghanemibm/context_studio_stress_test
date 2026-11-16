"""Shared reportlab styles, page geometry and small flowable helpers."""
from __future__ import annotations

from reportlab.graphics.charts.barcharts import HorizontalBarChart, VerticalBarChart
from reportlab.graphics.charts.legends import Legend
from reportlab.graphics.charts.lineplots import LinePlot
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.shapes import Drawing, Line, Rect, String
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph, Table, TableStyle

PAGE_W, PAGE_H = A4
TEAL = colors.HexColor("#0B4F6C")
TEAL_LIGHT = colors.HexColor("#DCEBF2")
GREY = colors.HexColor("#555555")
GREY_LIGHT = colors.HexColor("#EEEEEE")
NAVY = colors.HexColor("#1B2A41")
SERIES = [colors.HexColor(c) for c in ("#0B4F6C", "#20A39E", "#F1A208", "#A23B72", "#6C757D",
                                       "#3E8914", "#D1495B", "#00798C", "#EDAE49", "#30638E")]


def styles(base_font="Times-Roman", base_size=9.8, leading=12.4):
    s = {}
    s["body"] = ParagraphStyle("body", fontName=base_font, fontSize=base_size, leading=leading,
                               alignment=TA_JUSTIFY, spaceAfter=4.5)
    s["body_left"] = ParagraphStyle("body_left", parent=s["body"], alignment=TA_LEFT)
    s["lead"] = ParagraphStyle("lead", fontName="Times-Italic", fontSize=base_size + 1.2,
                               leading=leading + 2, alignment=TA_LEFT, spaceAfter=6, textColor=NAVY)
    s["h1"] = ParagraphStyle("h1", fontName="Helvetica-Bold", fontSize=16, leading=19.5,
                             spaceBefore=0, spaceAfter=8, textColor=TEAL)
    s["h2"] = ParagraphStyle("h2", fontName="Helvetica-Bold", fontSize=10.6, leading=13,
                             spaceBefore=8, spaceAfter=3.5, textColor=TEAL)
    s["h3"] = ParagraphStyle("h3", fontName="Helvetica-BoldOblique", fontSize=9.2, leading=11.5,
                             spaceBefore=5, spaceAfter=2, textColor=NAVY)
    s["caption"] = ParagraphStyle("caption", fontName="Helvetica-Oblique", fontSize=7.6, leading=9.4,
                                  spaceBefore=2, spaceAfter=6, textColor=GREY)
    s["tabtitle"] = ParagraphStyle("tabtitle", fontName="Helvetica-Bold", fontSize=8.4, leading=10.4,
                                   spaceBefore=6, spaceAfter=3, textColor=NAVY)
    s["cell"] = ParagraphStyle("cell", fontName="Helvetica", fontSize=7.4, leading=8.8)
    s["cellb"] = ParagraphStyle("cellb", fontName="Helvetica-Bold", fontSize=7.4, leading=8.8)
    s["cellr"] = ParagraphStyle("cellr", parent=s["cell"], alignment=TA_RIGHT)
    s["fn"] = ParagraphStyle("fn", fontName="Times-Roman", fontSize=7, leading=8.4, alignment=TA_LEFT)
    s["small"] = ParagraphStyle("small", fontName="Helvetica", fontSize=8, leading=10)
    s["toc1"] = ParagraphStyle("toc1", fontName="Helvetica-Bold", fontSize=9.6, leading=13)
    s["toc2"] = ParagraphStyle("toc2", fontName="Helvetica", fontSize=8.8, leading=11.2, leftIndent=14)
    s["cover_title"] = ParagraphStyle("cover_title", fontName="Helvetica-Bold", fontSize=26, leading=31,
                                      textColor=TEAL, spaceAfter=10)
    s["cover_sub"] = ParagraphStyle("cover_sub", fontName="Helvetica", fontSize=13, leading=17,
                                    textColor=NAVY, spaceAfter=6)
    s["center"] = ParagraphStyle("center", parent=s["body"], alignment=TA_CENTER)
    s["num"] = ParagraphStyle("num", parent=s["body"], leftIndent=26, firstLineIndent=-26)
    return s


def grid_table(rows, col_widths, header_rows=1, repeat=True, font_size=7.4, zebra=True,
               align_right_from=1, bold_rows=(), pad=2.0, span_rows=()):
    t = Table(rows, colWidths=col_widths, repeatRows=header_rows if repeat else 0)
    cmds = [
        ("FONT", (0, 0), (-1, -1), "Helvetica", font_size),
        ("FONT", (0, 0), (-1, header_rows - 1), "Helvetica-Bold", font_size),
        ("BACKGROUND", (0, 0), (-1, header_rows - 1), TEAL),
        ("TEXTCOLOR", (0, 0), (-1, header_rows - 1), colors.white),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), pad),
        ("BOTTOMPADDING", (0, 0), (-1, -1), pad),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ("LINEBELOW", (0, header_rows - 1), (-1, header_rows - 1), 0.6, NAVY),
        ("LINEBELOW", (0, -1), (-1, -1), 0.6, NAVY),
    ]
    if align_right_from is not None:
        cmds.append(("ALIGN", (align_right_from, header_rows), (-1, -1), "RIGHT"))
    if zebra:
        for r in range(header_rows, len(rows)):
            if (r - header_rows) % 2 == 1:
                cmds.append(("BACKGROUND", (0, r), (-1, r), GREY_LIGHT))
    for r in bold_rows:
        cmds.append(("FONT", (0, r), (-1, r), "Helvetica-Bold", font_size))
        cmds.append(("LINEABOVE", (0, r), (-1, r), 0.4, NAVY))
    for r in span_rows:
        cmds.append(("SPAN", (0, r), (-1, r)))
        cmds.append(("BACKGROUND", (0, r), (-1, r), TEAL_LIGHT))
        cmds.append(("FONT", (0, r), (-1, r), "Helvetica-Bold", font_size))
        cmds.append(("ALIGN", (0, r), (-1, r), "LEFT"))
    t.setStyle(TableStyle(cmds))
    return t


def kv_table(pairs, widths, font_size=8.2):
    t = Table([[a, b] for a, b in pairs], colWidths=widths)
    t.setStyle(TableStyle([
        ("FONT", (0, 0), (-1, -1), "Helvetica", font_size),
        ("FONT", (0, 0), (0, -1), "Helvetica-Bold", font_size),
        ("BACKGROUND", (0, 0), (0, -1), TEAL_LIGHT),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#9DB4C0")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    return t


# --------------------------------------------------------------------------------------------
# Charts (reportlab.graphics, vector)
# --------------------------------------------------------------------------------------------

def bar_chart(width, height, categories, series, names=None, title=None, horizontal=False,
              value_fmt="%0.0f", max_value=None, label_angle=0):
    d = Drawing(width, height)
    top = 18 if title else 6
    legend_h = 14 if names and len(series) > 1 else 0
    if title:
        d.add(String(0, height - 11, title, fontName="Helvetica-Bold", fontSize=8, fillColor=NAVY))
    c = HorizontalBarChart() if horizontal else VerticalBarChart()
    left = 92 if horizontal else 34
    bottom = 18 + legend_h + (22 if label_angle else 0)
    c.x, c.y = left, bottom
    c.width = width - left - 10
    c.height = height - bottom - top
    c.data = series
    c.categoryAxis.categoryNames = categories
    c.categoryAxis.labels.fontName = "Helvetica"
    c.categoryAxis.labels.fontSize = 6.4
    if label_angle:
        c.categoryAxis.labels.angle = label_angle
        c.categoryAxis.labels.boxAnchor = "ne"
        c.categoryAxis.labels.dy = -2
    c.valueAxis.labels.fontName = "Helvetica"
    c.valueAxis.labels.fontSize = 6.4
    c.valueAxis.valueMin = 0
    if max_value:
        c.valueAxis.valueMax = max_value
    c.barLabelFormat = value_fmt
    c.barLabels.fontName = "Helvetica"
    c.barLabels.fontSize = 5.8
    c.barLabels.nudge = 6
    for i in range(len(series)):
        c.bars[i].fillColor = SERIES[i % len(SERIES)]
        c.bars[i].strokeColor = None
    d.add(c)
    if names and len(series) > 1:
        lg = Legend()
        lg.x, lg.y = left, 8
        lg.dx, lg.dy = 6, 6
        lg.fontName, lg.fontSize = "Helvetica", 6.4
        lg.alignment = "right"
        lg.columnMaximum = 1
        lg.deltax = 70
        lg.colorNamePairs = [(SERIES[i % len(SERIES)], n) for i, n in enumerate(names)]
        d.add(lg)
    return d


def line_chart(width, height, xs, series, names, title=None, x_labels=None, y_max=None):
    d = Drawing(width, height)
    if title:
        d.add(String(0, height - 11, title, fontName="Helvetica-Bold", fontSize=8, fillColor=NAVY))
    lp = LinePlot()
    lp.x, lp.y = 34, 36
    lp.width = width - 46
    lp.height = height - 36 - (20 if title else 8)
    lp.data = [list(zip(xs, s)) for s in series]
    for i in range(len(series)):
        lp.lines[i].strokeColor = SERIES[i % len(SERIES)]
        lp.lines[i].strokeWidth = 1.2
    lp.xValueAxis.valueMin = min(xs)
    lp.xValueAxis.valueMax = max(xs)
    lp.xValueAxis.valueSteps = list(xs)
    lp.xValueAxis.labels.fontName = "Helvetica"
    lp.xValueAxis.labels.fontSize = 6.2
    if x_labels:
        lp.xValueAxis.labelTextFormat = lambda v, _m=dict(zip(xs, x_labels)): _m.get(int(round(v)), "")
    lp.yValueAxis.labels.fontName = "Helvetica"
    lp.yValueAxis.labels.fontSize = 6.2
    lp.yValueAxis.valueMin = 0
    if y_max:
        lp.yValueAxis.valueMax = y_max
    d.add(lp)
    lg = Legend()
    lg.x, lg.y = 34, 10
    lg.dx, lg.dy = 6, 6
    lg.fontName, lg.fontSize = "Helvetica", 6.2
    lg.alignment = "right"
    lg.columnMaximum = 1
    lg.deltax = max(46, (width - 40) / max(1, len(names)))
    lg.colorNamePairs = [(SERIES[i % len(SERIES)], n) for i, n in enumerate(names)]
    d.add(lg)
    return d


def pie_chart(width, height, labels, values, title=None):
    d = Drawing(width, height)
    if title:
        d.add(String(0, height - 11, title, fontName="Helvetica-Bold", fontSize=8, fillColor=NAVY))
    p = Pie()
    size = min(width * 0.45, height - 30)
    p.x, p.y = 8, (height - size) / 2 - 6
    p.width = p.height = size
    p.data = values
    p.labels = None
    p.slices.strokeColor = colors.white
    p.slices.strokeWidth = 0.6
    for i in range(len(values)):
        p.slices[i].fillColor = SERIES[i % len(SERIES)]
    d.add(p)
    lg = Legend()
    lg.x, lg.y = size + 24, height - 30
    lg.dx, lg.dy = 6, 6
    lg.fontName, lg.fontSize = "Helvetica", 6.6
    lg.alignment = "right"
    lg.columnMaximum = 12
    lg.colorNamePairs = [(SERIES[i % len(SERIES)], f"{labels[i]} ({values[i]:,.1f})") for i in range(len(values))]
    d.add(lg)
    return d


def gantt(width, height, rows, x0, x1, ticks, title=None):
    """rows: list of (label, start_num, end_num, color_index, note)."""
    d = Drawing(width, height)
    if title:
        d.add(String(0, height - 11, title, fontName="Helvetica-Bold", fontSize=8, fillColor=NAVY))
    left, right, top, bottom = 110, 10, 24, 22
    plot_w = width - left - right
    n = len(rows)
    row_h = (height - top - bottom) / max(1, n)

    def X(v):
        return left + (v - x0) / (x1 - x0) * plot_w

    for v, lab in ticks:
        d.add(Line(X(v), bottom - 2, X(v), height - top + 2, strokeColor=colors.HexColor("#BBBBBB"),
                   strokeWidth=0.4))
        d.add(String(X(v), bottom - 11, lab, fontName="Helvetica", fontSize=6, textAnchor="middle"))
    for i, (label, a, b, ci, note) in enumerate(rows):
        y = height - top - (i + 1) * row_h + row_h * 0.2
        d.add(String(left - 4, y + row_h * 0.25, label, fontName="Helvetica", fontSize=6.6, textAnchor="end"))
        d.add(Rect(X(a), y, max(2.5, X(b) - X(a)), row_h * 0.6, fillColor=SERIES[ci % len(SERIES)],
                   strokeColor=None))
        if note:
            d.add(String(min(X(b) + 3, width - 60), y + row_h * 0.15, note, fontName="Helvetica", fontSize=5.8))
    return d


def P(text, style):
    return Paragraph(text, style)

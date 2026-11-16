"""Pillow raster drawings for the decks: architecture diagrams with labelled arrows, tables
rendered as images, mock Claims Hub screens and timelines.

All text is DejaVu Sans (util.font) at >= 24 px so that OCR can read it (cap height >= 17 px).
Output PNGs carry no metadata, so the bytes are deterministic.
"""
from __future__ import annotations

import functools
import io
import math

from PIL import Image, ImageDraw

from generators.common import util

HEX = {
    "navy": "#0B2545", "navy2": "#13315C", "teal": "#13807A", "teal_l": "#D7EFEC", "teal_m": "#8FCFC8",
    "sky": "#3D7EBF", "sky_l": "#DCEAF7", "amber": "#E39B2D", "amber_l": "#FCEBD2", "slate": "#4A5560",
    "grey": "#7D8790", "grey_l": "#EEF1F4", "grey_m": "#D5DBE1", "red": "#B83A3A", "red_l": "#F6DCDC",
    "green": "#2E8B57", "green_l": "#DDF0E4", "white": "#FFFFFF", "ink": "#1B2430", "plum": "#6C4A8E",
    "plum_l": "#EAE1F3", "black": "#000000",
}


def col(c: str) -> str:
    return HEX.get(c, c)


@functools.lru_cache(maxsize=64)
def F(size: int, bold: bool = False, mono: bool = False):
    return util.font(size, bold=bold, mono=mono)


def wrap(text: str, font, max_w: float) -> list[str]:
    out = []
    for para in text.split("\n"):
        words = para.split(" ")
        line = ""
        for w in words:
            cand = (line + " " + w).strip()
            if font.getlength(cand) <= max_w or not line:
                line = cand
            else:
                out.append(line)
                line = w
        out.append(line)
    return out


class Canvas:
    def __init__(self, w: int = 2400, h: int = 1350, bg: str = "white"):
        self.w, self.h = w, h
        self.img = Image.new("RGB", (w, h), col(bg))
        self.d = ImageDraw.Draw(self.img)
        self._labels = []

    # -- text --------------------------------------------------------------------------------
    def text(self, x, y, s, size=26, bold=False, color="ink", anchor="la", mono=False):
        self.d.text((x, y), s, font=F(size, bold, mono), fill=col(color), anchor=anchor)

    def text_block(self, x, y, w, s, size=26, bold=False, color="ink", align="left", line_gap=1.25):
        f = F(size, bold)
        lines = wrap(s, f, w)
        lh = size * line_gap
        for i, ln in enumerate(lines):
            if align == "center":
                self.d.text((x + w / 2, y + i * lh), ln, font=f, fill=col(color), anchor="ma")
            else:
                self.d.text((x, y + i * lh), ln, font=f, fill=col(color))
        return y + len(lines) * lh

    # -- shapes ------------------------------------------------------------------------------
    def box(self, x, y, w, h, text="", fill="white", outline="slate", size=28, bold=False,
            color="ink", radius=14, width=3, sub=None, sub_size=22, dash=False):
        if dash:
            self._dash_rect(x, y, w, h, outline, width)
            if fill:
                self.d.rounded_rectangle([x + width, y + width, x + w - width, y + h - width],
                                         radius=radius, fill=col(fill))
        else:
            self.d.rounded_rectangle([x, y, x + w, y + h], radius=radius,
                                     fill=col(fill) if fill else None, outline=col(outline), width=width)
        if text:
            f = F(size, bold)
            lines = wrap(text, f, w - 24)
            sub_lines = wrap(sub, F(sub_size), w - 24) if sub else []
            lh, slh = size * 1.22, sub_size * 1.25
            tot = len(lines) * lh + len(sub_lines) * slh
            ty = y + (h - tot) / 2
            for ln in lines:
                self.d.text((x + w / 2, ty), ln, font=f, fill=col(color), anchor="ma")
                ty += lh
            for ln in sub_lines:
                self.d.text((x + w / 2, ty), ln, font=F(sub_size), fill=col("slate"), anchor="ma")
                ty += slh
        return (x, y, w, h)

    def _dash_rect(self, x, y, w, h, outline, width, dash=18, gap=10):
        for (x1, y1, x2, y2) in ((x, y, x + w, y), (x, y + h, x + w, y + h), (x, y, x, y + h), (x + w, y, x + w, y + h)):
            length = math.hypot(x2 - x1, y2 - y1)
            n = int(length // (dash + gap)) + 1
            for i in range(n):
                s = i * (dash + gap) / length
                e = min(1.0, (i * (dash + gap) + dash) / length)
                self.d.line([x1 + (x2 - x1) * s, y1 + (y2 - y1) * s, x1 + (x2 - x1) * e, y1 + (y2 - y1) * e],
                            fill=col(outline), width=width)

    def cyl(self, x, y, w, h, text, fill="grey_l", outline="slate", size=26, bold=False):
        e = 30
        self.d.rectangle([x, y + e / 2, x + w, y + h - e / 2], fill=col(fill))
        self.d.line([x, y + e / 2, x, y + h - e / 2], fill=col(outline), width=3)
        self.d.line([x + w, y + e / 2, x + w, y + h - e / 2], fill=col(outline), width=3)
        self.d.ellipse([x, y + h - e, x + w, y + h], fill=col(fill), outline=col(outline), width=3)
        self.d.rectangle([x + 3, y + e / 2, x + w - 3, y + h - e / 2 - 2], fill=col(fill))
        self.d.ellipse([x, y, x + w, y + e], fill=col(fill), outline=col(outline), width=3)
        f = F(size, bold)
        lines = wrap(text, f, w - 20)
        ty = y + e + (h - e - len(lines) * size * 1.2) / 2
        for ln in lines:
            self.d.text((x + w / 2, ty), ln, font=f, fill=col("ink"), anchor="ma")
            ty += size * 1.2
        return (x, y, w, h)

    @staticmethod
    def edge(b, side):
        x, y, w, h = b
        return {"t": (x + w / 2, y), "b": (x + w / 2, y + h), "l": (x, y + h / 2), "r": (x + w, y + h / 2)}[side]

    def _head(self, p_from, p_to, color, size=22):
        ang = math.atan2(p_to[1] - p_from[1], p_to[0] - p_from[0])
        a1, a2 = ang + math.radians(152), ang - math.radians(152)
        pts = [p_to, (p_to[0] + size * math.cos(a1), p_to[1] + size * math.sin(a1)),
               (p_to[0] + size * math.cos(a2), p_to[1] + size * math.sin(a2))]
        self.d.polygon(pts, fill=col(color))

    def label(self, cx, cy, text, size=24, color="navy", fill="white", outline="grey_m", bold=True):
        f = F(size, bold)
        lines = text.split("\n")
        tw = max(f.getlength(ln) for ln in lines)
        th = size * 1.25 * len(lines)
        self.d.rounded_rectangle([cx - tw / 2 - 12, cy - th / 2 - 7, cx + tw / 2 + 12, cy + th / 2 + 7],
                                 radius=8, fill=col(fill), outline=col(outline) if outline else None, width=2)
        for i, ln in enumerate(lines):
            self.d.text((cx, cy - th / 2 + i * size * 1.25), ln, font=f, fill=col(color), anchor="ma")

    def arrow(self, pts, label=None, color="slate", width=5, label_at=0.5, label_size=24,
              label_dx=0, label_dy=0, both=False, dash=False, label_color="navy"):
        """Polyline arrow through ``pts`` (head at the last point); optional label on the
        segment containing the ``label_at`` fraction of the path length."""
        pts = [tuple(p) for p in pts]
        for i in range(len(pts) - 1):
            if dash:
                self._dash_line(pts[i], pts[i + 1], color, width)
            else:
                self.d.line([pts[i], pts[i + 1]], fill=col(color), width=width)
        self._head(pts[-2], pts[-1], color)
        if both:
            self._head(pts[1], pts[0], color)
        if label:
            lens = [math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1)]
            target = sum(lens) * label_at
            acc = 0.0
            for i, ln in enumerate(lens):
                if acc + ln >= target:
                    t = (target - acc) / ln if ln else 0
                    cx = pts[i][0] + (pts[i + 1][0] - pts[i][0]) * t
                    cy = pts[i][1] + (pts[i + 1][1] - pts[i][1]) * t
                    break
                acc += ln
            self._labels.append((cx + label_dx, cy + label_dy, label, label_size, label_color))

    def _dash_line(self, p1, p2, color, width, dash=20, gap=12):
        length = math.dist(p1, p2)
        n = int(length // (dash + gap)) + 1
        for i in range(n):
            s = i * (dash + gap) / length
            e = min(1.0, (i * (dash + gap) + dash) / length)
            self.d.line([p1[0] + (p2[0] - p1[0]) * s, p1[1] + (p2[1] - p1[1]) * s,
                         p1[0] + (p2[0] - p1[0]) * e, p1[1] + (p2[1] - p1[1]) * e], fill=col(color), width=width)

    def title(self, text, sub=None, size=40):
        self.text(48, 34, text, size=size, bold=True, color="navy")
        if sub:
            self.text(48, 34 + size * 1.35, sub, size=24, color="slate")

    def legend(self, x, y, items, size=22):
        for i, (c, t) in enumerate(items):
            yy = y + i * (size * 1.6)
            self.d.rounded_rectangle([x, yy, x + 34, yy + size], radius=5, fill=col(c), outline=col("slate"), width=2)
            self.text(x + 48, yy - 2, t, size=size, color="ink")

    def png(self) -> bytes:
        for (lx, ly, lt, ls, lc) in self._labels:
            self.label(lx, ly, lt, size=ls, color=lc)
        self._labels = []
        buf = io.BytesIO()
        self.img.save(buf, format="PNG", optimize=False, compress_level=9)
        return buf.getvalue()


# ---------------------------------------------------------------------------------------------
# Tables rendered as images
# ---------------------------------------------------------------------------------------------

def table_image(header, rows, col_w, title=None, note=None, size=26, row_h=None, header_fill="navy",
                zebra=True, width=2400, highlight_rows=()) -> bytes:
    pad = 48
    tot = sum(col_w)
    usable = width - 2 * pad
    widths = [usable * c / tot for c in col_w]
    f, fb = F(size), F(size, True)
    rh_min = row_h or int(size * 2.1)
    # measure wrapped rows
    rendered = []
    for r in [header] + list(rows):
        cells = []
        hmax = rh_min
        for c, val in enumerate(r):
            lines = wrap(str(val), fb if r is header else f, widths[c] - 28)
            cells.append(lines)
            hmax = max(hmax, int(len(lines) * size * 1.3 + size * 0.9))
        rendered.append((cells, hmax))
    top = pad + (int(size * 2.4) if title else 0)
    height = top + sum(h for _, h in rendered) + pad + (int(size * 1.9) if note else 0)
    cv = Canvas(width, height)
    if title:
        cv.text(pad, pad - 6, title, size=int(size * 1.25), bold=True, color="navy")
    y = top
    for ri, (cells, hrow) in enumerate(rendered):
        x = pad
        if ri == 0:
            fill = col(header_fill)
        elif (ri - 1) in highlight_rows:
            fill = col("amber_l")
        else:
            fill = col("grey_l") if (zebra and ri % 2 == 0) else col("white")
        cv.d.rectangle([pad, y, width - pad, y + hrow], fill=fill)
        for c, lines in enumerate(cells):
            ty = y + (hrow - len(lines) * size * 1.3) / 2
            for ln in lines:
                cv.d.text((x + 14, ty), ln, font=fb if ri == 0 else f,
                          fill=col("white") if ri == 0 else col("ink"))
                ty += size * 1.3
            x += widths[c]
        cv.d.line([pad, y + hrow, width - pad, y + hrow], fill=col("grey_m"), width=2)
        y += hrow
    x = pad
    for wc in widths[:-1]:
        x += wc
        cv.d.line([x, top, x, y], fill=col("grey_m"), width=2)
    cv.d.rectangle([pad, top, width - pad, y], outline=col("slate"), width=3)
    if note:
        cv.text(pad, y + size * 0.6, note, size=int(size * 0.85), color="slate")
    return cv.png()


# ---------------------------------------------------------------------------------------------
# Mock Claims Hub screen
# ---------------------------------------------------------------------------------------------

def ui_screen(app_title, user, nav, active, breadcrumb, heading, fields, chips=(), table=None,
              banner=None, side_panel=None, width=2400, height=1500, env="PRODUCTION") -> bytes:
    """A Claims Hub web screen: top bar, left navigation, a record header with status chips,
    a two-column field grid, an optional table and an optional side panel."""
    cv = Canvas(width, height, "grey_l")
    d = cv.d
    d.rectangle([0, 0, width, 96], fill=col("navy"))
    cv.text(40, 26, app_title, size=38, bold=True, color="white")
    cv.text(width - 40, 30, user, size=26, color="white", anchor="ra")
    envw = F(22, True).getlength(env) + 30
    ex = max(520, 40 + F(38, True).getlength(app_title) + 40)
    d.rounded_rectangle([ex, 28, ex + envw, 68], radius=8, fill=col("teal"))
    cv.text(ex + 15, 34, env, size=22, bold=True, color="white")
    d.rectangle([0, 96, 380, height], fill=col("white"))
    d.line([380, 96, 380, height], fill=col("grey_m"), width=2)
    for i, item in enumerate(nav):
        y = 140 + i * 74
        if item == active:
            d.rectangle([0, y - 14, 380, y + 50], fill=col("teal_l"))
            d.rectangle([0, y - 14, 10, y + 50], fill=col("teal"))
        cv.text(40, y, item, size=28, bold=(item == active), color="navy" if item == active else "slate")
    x0 = 420
    cv.text(x0, 120, breadcrumb, size=24, color="slate")
    cv.text(x0, 162, heading, size=40, bold=True, color="navy")
    cx = x0
    for chip_text, chip_col in chips:
        cw = F(24, True).getlength(chip_text) + 34
        d.rounded_rectangle([cx, 226, cx + cw, 270], radius=20, fill=col(chip_col + "_l") if chip_col + "_l" in HEX else col(chip_col))
        cv.text(cx + 17, 233, chip_text, size=24, bold=True, color=chip_col if chip_col in HEX else "ink")
        cx += cw + 16
    y = 300
    if banner:
        d.rounded_rectangle([x0, y, width - 40 - (560 if side_panel else 0), y + 70], radius=10,
                            fill=col("amber_l"), outline=col("amber"), width=3)
        cv.text(x0 + 24, y + 20, banner, size=26, bold=True, color="ink")
        y += 96
    right = width - 40 - (580 if side_panel else 0)
    card_h = 70 + ((len(fields) + 1) // 2) * 92
    d.rounded_rectangle([x0, y, right, y + card_h], radius=14, fill=col("white"), outline=col("grey_m"), width=2)
    colw = (right - x0 - 60) / 2
    for i, (lab, val) in enumerate(fields):
        cxx = x0 + 30 + (i % 2) * (colw + 20)
        cyy = y + 30 + (i // 2) * 92
        cv.text(cxx, cyy, lab, size=22, color="slate")
        cv.text(cxx, cyy + 30, val, size=28, bold=True, color="ink")
    y += card_h + 30
    if table:
        hdr, rows = table
        tw = right - x0
        cw = tw / len(hdr)
        d.rounded_rectangle([x0, y, right, y + 64 + 58 * len(rows)], radius=12, fill=col("white"), outline=col("grey_m"), width=2)
        d.rectangle([x0 + 2, y + 2, right - 2, y + 60], fill=col("grey_l"))
        for j, h in enumerate(hdr):
            cv.text(x0 + 20 + j * cw, y + 16, h, size=24, bold=True, color="navy")
        for i, row in enumerate(rows):
            for j, v in enumerate(row):
                cv.text(x0 + 20 + j * cw, y + 76 + i * 58, str(v), size=24, color="ink")
        y += 64 + 58 * len(rows) + 30
    y_end = y
    if side_panel:
        ptitle, items = side_panel
        px = width - 600
        d.rounded_rectangle([px, 300, width - 40, 300 + 80 + 66 * len(items)], radius=14, fill=col("white"),
                            outline=col("grey_m"), width=2)
        cv.text(px + 26, 324, ptitle, size=28, bold=True, color="navy")
        for i, it in enumerate(items):
            cv.text(px + 26, 384 + i * 66, it, size=24, color="ink")
        y_end = max(y_end, 300 + 80 + 66 * len(items) + 30)
    crop_h = int(min(height, max(y_end + 40, 760)))
    cv.img = cv.img.crop((0, 0, width, crop_h))
    return cv.png()


# ---------------------------------------------------------------------------------------------
# Timelines
# ---------------------------------------------------------------------------------------------

def timeline_image(title, events, width=2400, height=900, sub=None, color="teal") -> bytes:
    """Horizontal timeline. ``events``: list of (date label, text, highlight bool)."""
    cv = Canvas(width, height)
    cv.title(title, sub)
    y = height // 2 + 40
    x0, x1 = 140, width - 140
    cv.d.line([x0, y, x1, y], fill=col("slate"), width=8)
    cv._head((x1 - 40, y), (x1 + 30, y), "slate", size=34)
    n = len(events)
    for i, (dl, txt, hi) in enumerate(events):
        x = x0 + 80 + i * (x1 - x0 - 200) / max(1, n - 1)
        r = 22 if hi else 16
        cv.d.ellipse([x - r, y - r, x + r, y + r], fill=col("amber" if hi else color), outline=col("white"), width=4)
        up = i % 2 == 0
        ty = y - 190 if up else y + 60
        cv.d.line([x, y - r if up else y + r, x, ty + (130 if up else 0)], fill=col("grey_m"), width=3)
        cv.text(x, ty, dl, size=30, bold=True, color="navy", anchor="ma")
        cv.text_block(x - 210, ty + 44, 420, txt, size=25, color="ink", align="center")
    return cv.png()

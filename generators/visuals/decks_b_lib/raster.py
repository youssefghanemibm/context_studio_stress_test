"""Pillow raster helpers: diagrams with labelled arrows, tables as images, mock UI screens.

Text is rendered with DejaVu Sans (generators.common.util.font) at OCR-friendly sizes
(>= 22 px, i.e. cap height >= 16 px) in dark-on-light colours. Output is PNG bytes with no
metadata, so the same input always produces the same bytes.
"""
from __future__ import annotations

import io
import math
from typing import Sequence

from PIL import Image, ImageDraw

from generators.common import util

NAVY = (18, 43, 74)
TEAL = (14, 124, 134)
TEAL_LT = (217, 238, 240)
GREY = (95, 107, 122)
GREY_LT = (236, 239, 243)
GREY_MD = (200, 206, 214)
WHITE = (255, 255, 255)
BLACK = (20, 20, 20)
AMBER = (224, 142, 11)
AMBER_LT = (252, 236, 205)
RED = (179, 38, 30)
GREEN = (46, 125, 50)
GREEN_LT = (220, 238, 221)

_FONTS: dict = {}


def F(size: int, bold: bool = False, mono: bool = False):
    key = (size, bold, mono)
    if key not in _FONTS:
        _FONTS[key] = util.font(size, bold=bold, mono=mono)
    return _FONTS[key]


class Canvas:
    def __init__(self, w: int = 1600, h: int = 900, bg=WHITE):
        self.w, self.h = w, h
        self.img = Image.new("RGB", (w, h), bg)
        self.d = ImageDraw.Draw(self.img)

    # ------------------------------------------------------------------ text
    def text_size(self, s: str, size: int, bold=False, mono=False):
        l, t, r, b = self.d.textbbox((0, 0), s, font=F(size, bold, mono))
        return r - l, b - t

    def text(self, xy, s: str, size: int = 24, bold=False, fill=BLACK, anchor="la", mono=False):
        self.d.text(xy, s, font=F(size, bold, mono), fill=fill, anchor=anchor)

    def wrap(self, s: str, size: int, max_w: int, bold=False) -> list[str]:
        words, lines, cur = s.split(), [], ""
        for w in words:
            cand = (cur + " " + w).strip()
            if self.text_size(cand, size, bold)[0] <= max_w or not cur:
                cur = cand
            else:
                lines.append(cur)
                cur = w
        if cur:
            lines.append(cur)
        return lines

    def para(self, x, y, s: str, size=24, max_w=600, fill=BLACK, bold=False, line_gap=8) -> int:
        for ln in self.wrap(s, size, max_w, bold):
            self.text((x, y), ln, size=size, bold=bold, fill=fill)
            y += size + line_gap
        return y

    # ------------------------------------------------------------------ shapes
    def box(self, x, y, w, h, lines: Sequence[str] | str, fill=TEAL_LT, outline=TEAL, size=24,
            bold_first=True, color=NAVY, radius=14, width=3):
        self.d.rounded_rectangle([x, y, x + w, y + h], radius=radius, fill=fill, outline=outline, width=width)
        lines = [lines] if isinstance(lines, str) else list(lines)
        sizes = [size if i == 0 else max(size - 4, 22) for i in range(len(lines))]
        total = sum(s + 8 for s in sizes) - 8
        cy = y + (h - total) / 2
        for i, ln in enumerate(lines):
            self.text((x + w / 2, cy), ln, size=sizes[i], bold=(bold_first and i == 0), fill=color, anchor="ma")
            cy += sizes[i] + 8
        return (x, y, w, h)

    def diamond(self, cx, cy, w, h, lines, fill=AMBER_LT, outline=AMBER, size=22, color=BLACK):
        pts = [(cx, cy - h / 2), (cx + w / 2, cy), (cx, cy + h / 2), (cx - w / 2, cy)]
        self.d.polygon(pts, fill=fill, outline=outline)
        self.d.line(pts + [pts[0]], fill=outline, width=3)
        lines = [lines] if isinstance(lines, str) else list(lines)
        total = len(lines) * (size + 6) - 6
        y = cy - total / 2
        for ln in lines:
            self.text((cx, y), ln, size=size, bold=True, fill=color, anchor="ma")
            y += size + 6
        return (cx - w / 2, cy - h / 2, w, h)

    def arrow(self, p1, p2, label: str | None = None, color=NAVY, width=4, label_size=22,
              label_offset=(0, -34), head=18, dashed=False, label_fill=WHITE, label_color=None):
        (x1, y1), (x2, y2) = p1, p2
        if dashed:
            n = max(1, int(math.hypot(x2 - x1, y2 - y1) // 18))
            for i in range(0, n, 2):
                a = i / n
                b = min(1.0, (i + 1) / n)
                self.d.line([(x1 + (x2 - x1) * a, y1 + (y2 - y1) * a), (x1 + (x2 - x1) * b, y1 + (y2 - y1) * b)],
                            fill=color, width=width)
        else:
            self.d.line([p1, p2], fill=color, width=width)
        ang = math.atan2(y2 - y1, x2 - x1)
        left = (x2 - head * math.cos(ang - 0.4), y2 - head * math.sin(ang - 0.4))
        right = (x2 - head * math.cos(ang + 0.4), y2 - head * math.sin(ang + 0.4))
        self.d.polygon([p2, left, right], fill=color)
        if label:
            mx, my = (x1 + x2) / 2 + label_offset[0], (y1 + y2) / 2 + label_offset[1]
            tw, th = self.text_size(label, label_size)
            self.d.rectangle([mx - tw / 2 - 8, my - 4, mx + tw / 2 + 8, my + th + 10], fill=label_fill)
            self.text((mx, my), label, size=label_size, fill=label_color or color, anchor="ma")

    def poly_arrow(self, pts, label=None, label_at=None, color=NAVY, width=4, label_size=22):
        for a, b in zip(pts[:-2], pts[1:-1]):
            self.d.line([a, b], fill=color, width=width)
        self.arrow(pts[-2], pts[-1], color=color, width=width)
        if label:
            x, y = label_at or pts[len(pts) // 2]
            tw, th = self.text_size(label, label_size)
            self.d.rectangle([x - tw / 2 - 8, y - 4, x + tw / 2 + 8, y + th + 10], fill=WHITE)
            self.text((x, y), label, size=label_size, fill=color, anchor="ma")

    def cylinder(self, x, y, w, h, lines, fill=GREY_LT, outline=NAVY, size=24):
        e = h * 0.18
        self.d.rectangle([x, y + e / 2, x + w, y + h - e / 2], fill=fill)
        self.d.ellipse([x, y + h - e, x + w, y + h], fill=fill, outline=outline, width=3)
        self.d.rectangle([x + 2, y + e / 2, x + w - 2, y + h - e / 2], fill=fill)
        self.d.line([(x, y + e / 2), (x, y + h - e / 2)], fill=outline, width=3)
        self.d.line([(x + w, y + e / 2), (x + w, y + h - e / 2)], fill=outline, width=3)
        self.d.ellipse([x, y, x + w, y + e], fill=WHITE, outline=outline, width=3)
        lines = [lines] if isinstance(lines, str) else list(lines)
        cy = y + h / 2 - len(lines) * (size + 6) / 2 + e / 3
        for i, ln in enumerate(lines):
            self.text((x + w / 2, cy), ln, size=size if i == 0 else size - 4, bold=(i == 0), fill=NAVY, anchor="ma")
            cy += size + 6

    def title(self, s: str, size=30, y=24):
        self.text((40, y), s, size=size, bold=True, fill=NAVY)
        self.d.line([(40, y + size + 14), (self.w - 40, y + size + 14)], fill=TEAL, width=3)

    def png(self) -> bytes:
        buf = io.BytesIO()
        self.img.save(buf, format="PNG", optimize=True)
        return buf.getvalue()


# ------------------------------------------------------------------------------------------
# Tables as images
# ------------------------------------------------------------------------------------------
def table_image(rows: Sequence[Sequence[str]], col_w: Sequence[int], title: str | None = None,
                size: int = 24, row_h: int = 50, header_fill=NAVY, pad: int = 30,
                zebra=True, wrap: bool = True) -> bytes:
    """Render a table to PNG. Header row is white on navy; body rows dark on white/light grey."""
    probe = Canvas(10, 10)
    # wrap cells
    wrapped = []
    for r, row in enumerate(rows):
        cells = []
        for c, val in enumerate(row):
            lines = probe.wrap(str(val), size, col_w[c] - 20, bold=(r == 0)) if wrap else [str(val)]
            cells.append(lines or [""])
        wrapped.append(cells)
    heights = [max(row_h, max(len(cl) for cl in cells) * (size + 10) + 16) for cells in wrapped]
    W = sum(col_w) + 2 * pad
    top = pad + (size + 34 if title else 0)
    H = top + sum(heights) + pad
    cv = Canvas(W, H)
    if title:
        cv.text((pad, pad - 4), title, size=size + 4, bold=True, fill=NAVY)
    y = top
    for r, cells in enumerate(wrapped):
        x = pad
        fill = header_fill if r == 0 else (GREY_LT if zebra and r % 2 == 0 else WHITE)
        cv.d.rectangle([pad, y, W - pad, y + heights[r]], fill=fill)
        for c, lines in enumerate(cells):
            ty = y + 10
            for ln in lines:
                cv.text((x + 10, ty), ln, size=size, bold=(r == 0), fill=WHITE if r == 0 else BLACK)
                ty += size + 10
            x += col_w[c]
            if c < len(cells) - 1:
                cv.d.line([(x, y), (x, y + heights[r])], fill=GREY_MD, width=2)
        cv.d.line([(pad, y + heights[r]), (W - pad, y + heights[r])], fill=GREY_MD, width=2)
        y += heights[r]
    cv.d.rectangle([pad, top, W - pad, y], outline=NAVY, width=3)
    return cv.png()


# ------------------------------------------------------------------------------------------
# Mock UI chrome
# ------------------------------------------------------------------------------------------
def web_chrome(cv: Canvas, app: str, user: str, nav: Sequence[str], active: int, crumb: str):
    """Claims Hub style chrome: top bar, left navigation, breadcrumb."""
    cv.d.rectangle([0, 0, cv.w, 70], fill=NAVY)
    cv.text((28, 18), app, size=28, bold=True, fill=WHITE)
    tw, _ = cv.text_size(user, 22)
    cv.text((cv.w - tw - 30, 22), user, size=22, fill=WHITE)
    cv.d.rectangle([0, 70, 260, cv.h], fill=GREY_LT)
    for i, item in enumerate(nav):
        y = 100 + i * 58
        if i == active:
            cv.d.rectangle([0, y - 10, 260, y + 40], fill=TEAL_LT)
            cv.d.rectangle([0, y - 10, 8, y + 40], fill=TEAL)
        cv.text((30, y), item, size=22, bold=(i == active), fill=NAVY)
    cv.text((300, 92), crumb, size=22, fill=GREY)


def field(cv: Canvas, x, y, label: str, value: str = "", w: int = 420, required=False, h: int = 50,
          dropdown=False, focus=False):
    lab = label + (" *" if required else "")
    cv.text((x, y), lab, size=22, bold=True, fill=NAVY)
    cv.d.rectangle([x, y + 34, x + w, y + 34 + h], fill=WHITE, outline=TEAL if focus else GREY_MD,
                   width=3 if focus else 2)
    if value:
        cv.text((x + 14, y + 34 + (h - 24) / 2 - 2), value, size=22, fill=BLACK)
    if dropdown:
        cx, cy = x + w - 26, y + 34 + h / 2
        cv.d.polygon([(cx - 10, cy - 5), (cx + 10, cy - 5), (cx, cy + 7)], fill=GREY)
    return y + 34 + h


def button(cv: Canvas, x, y, label: str, primary=True, w: int | None = None):
    tw, th = cv.text_size(label, 22, bold=True)
    w = w or tw + 50
    cv.d.rounded_rectangle([x, y, x + w, y + 52], radius=8, fill=TEAL if primary else WHITE,
                           outline=TEAL, width=2)
    cv.text((x + w / 2, y + 13), label, size=22, bold=True, fill=WHITE if primary else TEAL, anchor="ma")
    return x + w


def green_screen(lines: Sequence[str], cols: int = 80, size: int = 26, fg=(80, 255, 120), bg=(5, 12, 8),
                 hi=(235, 255, 235)) -> bytes:
    """3270-style terminal screen. Lines starting with '!' are rendered in the bright colour."""
    probe = Canvas(10, 10)
    cw, _ = probe.text_size("M" * cols, size, mono=True)
    lh = size + 12
    W = cw + 80
    H = len(lines) * lh + 80
    cv = Canvas(W, H, bg=bg)
    y = 40
    for ln in lines:
        col = hi if ln.startswith("!") else fg
        cv.text((40, y), ln.lstrip("!"), size=size, fill=col, mono=True)
        y += lh
    return cv.png()

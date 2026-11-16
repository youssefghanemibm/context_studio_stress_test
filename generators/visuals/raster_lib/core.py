"""Canvas: a thin deterministic drawing layer over Pillow.

Coordinates are pixels. Boxes are (x0, y0, x1, y1). Text uses DejaVu Sans via util.font.
All text intended for OCR should be >= 22 px font size (cap height ~16 px) on light
backgrounds, or >= 24 px on dark backgrounds.
"""
from __future__ import annotations

import io
import math
from typing import Iterable, Sequence

from PIL import Image, ImageDraw

from generators.common import util

# ------------------------------------------------------------------------------------------
# Palette (corporate-ish: Corvane navy/teal, IBM-neutral greys)
# ------------------------------------------------------------------------------------------
INK = "#1B2430"
INK2 = "#3D4A5C"
MUTED = "#6B7787"
LINE = "#5A6678"
GRID = "#D5DBE3"
WHITE = "#FFFFFF"
PAPER = "#FFFFFF"
NAVY = "#14325C"
NAVY2 = "#1F4E8C"
TEAL = "#0E7C7B"
TEAL_L = "#D9F0EF"
BLUE_L = "#E3EDF9"
BLUE_M = "#B9D1F0"
GREEN = "#2E7D32"
GREEN_L = "#E3F2E5"
AMBER = "#B26A00"
AMBER_L = "#FFF1D6"
RED = "#B3261E"
RED_L = "#FBE3E1"
PURPLE = "#5B3F95"
PURPLE_L = "#ECE6F6"
GREY_L = "#F1F3F6"
GREY_M = "#E1E5EB"
LEGACY = "#7A5C2E"
LEGACY_L = "#F4ECDD"

STYLES = {
    # fill, outline, text
    "legacy": (LEGACY_L, LEGACY, INK),
    "target": (BLUE_L, NAVY2, INK),
    "service": (TEAL_L, TEAL, INK),
    "external": (GREY_L, LINE, INK),
    "vendor": (PURPLE_L, PURPLE, INK),
    "platform": (GREEN_L, GREEN, INK),
    "warn": (AMBER_L, AMBER, INK),
    "alert": (RED_L, RED, INK),
    "plain": (WHITE, LINE, INK),
    "dark": (NAVY, NAVY, WHITE),
    "note": ("#FFFBE6", "#C9A227", INK),
}

_FONTS: dict = {}


def F(size: int, bold: bool = False, mono: bool = False):
    key = (int(size), bool(bold), bool(mono))
    f = _FONTS.get(key)
    if f is None:
        f = _FONTS[key] = util.font(int(size), bold=bold, mono=mono)
    return f


def _dash_segments(p0, p1, dash: tuple[int, int]):
    (x0, y0), (x1, y1) = p0, p1
    L = math.hypot(x1 - x0, y1 - y0)
    if L == 0:
        return []
    on, off = dash
    ux, uy = (x1 - x0) / L, (y1 - y0) / L
    out, t = [], 0.0
    while t < L:
        t2 = min(t + on, L)
        out.append(((x0 + ux * t, y0 + uy * t), (x0 + ux * t2, y0 + uy * t2)))
        t = t2 + off
    return out


class Canvas:
    """A white (or coloured) RGB canvas with drawing helpers."""

    def __init__(self, w: int, h: int, bg: str = PAPER):
        self.w, self.h = int(w), int(h)
        self.img = Image.new("RGB", (self.w, self.h), bg)
        self.d = ImageDraw.Draw(self.img)

    # -------------------------------------------------------------------- text
    def tsize(self, s: str, size: int, bold: bool = False, mono: bool = False) -> tuple[int, int]:
        if not s:
            return (0, int(size * 1.1))
        b = self.d.textbbox((0, 0), s, font=F(size, bold, mono))
        return (b[2] - b[0], b[3] - b[1])

    def twidth(self, s: str, size: int, bold: bool = False, mono: bool = False) -> int:
        return int(self.d.textlength(s, font=F(size, bold, mono))) if s else 0

    def wrap(self, s: str, size: int, max_w: int, bold: bool = False, mono: bool = False) -> list[str]:
        """Greedy word wrap; honours explicit newlines; never splits identifiers."""
        out: list[str] = []
        for para in str(s).split("\n"):
            words = para.split(" ")
            line = ""
            for w in words:
                cand = w if not line else line + " " + w
                if self.twidth(cand, size, bold, mono) <= max_w or not line:
                    line = cand
                else:
                    out.append(line)
                    line = w
            out.append(line)
        return out

    def text(self, x: float, y: float, s: str, size: int = 24, bold: bool = False, mono: bool = False,
             fill: str = INK, anchor: str = "la") -> None:
        self.d.text((x, y), s, font=F(size, bold, mono), fill=fill, anchor=anchor)

    def lines_block(self, x: float, y: float, lines: Sequence[str], size: int = 24, bold=False, mono=False,
                    fill: str = INK, gap: float = 0.32, align: str = "left", first_bold: bool = False,
                    max_w: int | None = None) -> float:
        """Draw lines top-down starting at (x, y); returns y after the block."""
        lh = int(size * (1 + gap))
        for i, ln in enumerate(lines):
            b = bold or (first_bold and i == 0)
            if align == "center":
                self.text(x, y, ln, size, b, mono, fill, anchor="ma")
            elif align == "right":
                self.text(x, y, ln, size, b, mono, fill, anchor="ra")
            else:
                self.text(x, y, ln, size, b, mono, fill)
            y += lh
        return y

    def text_in_box(self, box, s: str, size: int = 24, bold: bool = False, fill: str = INK,
                    align: str = "center", valign: str = "middle", pad: int = 12, gap: float = 0.28,
                    min_size: int = 18, mono: bool = False, first_bold: bool = False) -> int:
        """Wrap s into box, shrinking the font down to min_size if needed. Returns the size used.

        With first_bold, the first paragraph (text before the first newline) is drawn bold."""
        x0, y0, x1, y1 = box
        maxw, maxh = (x1 - x0) - 2 * pad, (y1 - y0) - 2 * pad
        paras = str(s).split("\n")
        sz = size
        while True:
            lines: list[tuple[str, bool]] = []
            for k, para in enumerate(paras):
                b = bold or (first_bold and k == 0)
                for ln in self.wrap(para, sz, maxw, b, mono):
                    lines.append((ln, b))
            lh = int(sz * (1 + gap))
            th = lh * len(lines) - int(sz * gap)
            widest = max((self.twidth(l, sz, b, mono) for l, b in lines), default=0)
            if (th <= maxh and widest <= maxw) or sz <= min_size:
                break
            sz -= 1
        if valign == "top":
            y = y0 + pad
        elif valign == "bottom":
            y = y1 - pad - th
        else:
            y = y0 + (y1 - y0 - th) / 2
        for ln, b in lines:
            if align == "center":
                self.text((x0 + x1) / 2, y, ln, sz, b, mono, fill, anchor="ma")
            elif align == "right":
                self.text(x1 - pad, y, ln, sz, b, mono, fill, anchor="ra")
            else:
                self.text(x0 + pad, y, ln, sz, b, mono, fill)
            y += lh
        return sz

    # -------------------------------------------------------------------- shapes
    def rect(self, box, fill=None, outline=LINE, width: int = 2, radius: int = 0, dash=None) -> None:
        x0, y0, x1, y1 = [int(round(v)) for v in box]
        if dash:
            if fill:
                self.d.rounded_rectangle((x0, y0, x1, y1), radius=radius, fill=fill) if radius else \
                    self.d.rectangle((x0, y0, x1, y1), fill=fill)
            pts = [(x0 + radius, y0), (x1 - radius, y0), (x1, y0 + radius), (x1, y1 - radius),
                   (x1 - radius, y1), (x0 + radius, y1), (x0, y1 - radius), (x0, y0 + radius)]
            for a, b in ((pts[0], pts[1]), (pts[2], pts[3]), (pts[4], pts[5]), (pts[6], pts[7])):
                for s0, s1 in _dash_segments(a, b, dash):
                    self.d.line([s0, s1], fill=outline, width=width)
            if radius:
                for cx, cy, a0 in ((x0 + radius, y0 + radius, 180), (x1 - radius, y0 + radius, 270),
                                   (x1 - radius, y1 - radius, 0), (x0 + radius, y1 - radius, 90)):
                    self.d.arc((cx - radius, cy - radius, cx + radius, cy + radius), a0, a0 + 90,
                               fill=outline, width=width)
            return
        if radius:
            self.d.rounded_rectangle((x0, y0, x1, y1), radius=radius, fill=fill, outline=outline, width=width)
        else:
            self.d.rectangle((x0, y0, x1, y1), fill=fill, outline=outline, width=width)

    def ellipse(self, box, fill=None, outline=LINE, width: int = 2) -> None:
        self.d.ellipse([int(v) for v in box], fill=fill, outline=outline, width=width)

    def diamond(self, box, fill=WHITE, outline=LINE, width: int = 3) -> None:
        x0, y0, x1, y1 = box
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        pts = [(cx, y0), (x1, cy), (cx, y1), (x0, cy)]
        self.d.polygon(pts, fill=fill, outline=outline)
        if width > 1:
            self.d.line(pts + [pts[0]], fill=outline, width=width, joint="curve")

    def cylinder(self, box, fill=BLUE_L, outline=NAVY2, width: int = 3) -> None:
        x0, y0, x1, y1 = box
        eh = max(14, int((x1 - x0) * 0.16))
        self.d.rectangle((x0, y0 + eh / 2, x1, y1 - eh / 2), fill=fill)
        self.d.ellipse((x0, y1 - eh, x1, y1), fill=fill, outline=outline, width=width)
        self.d.rectangle((x0 + width, y0 + eh / 2, x1 - width, y1 - eh / 2), fill=fill)
        self.d.line([(x0, y0 + eh / 2), (x0, y1 - eh / 2)], fill=outline, width=width)
        self.d.line([(x1, y0 + eh / 2), (x1, y1 - eh / 2)], fill=outline, width=width)
        self.d.ellipse((x0, y0, x1, y0 + eh), fill=fill, outline=outline, width=width)

    def cloud(self, box, fill=GREY_L, outline=LINE, width: int = 3) -> None:
        x0, y0, x1, y1 = box
        w, h = x1 - x0, y1 - y0
        blobs = [(0.05, 0.35, 0.40, 0.95), (0.25, 0.10, 0.62, 0.70), (0.50, 0.05, 0.85, 0.65),
                 (0.62, 0.30, 0.98, 0.95), (0.20, 0.45, 0.80, 1.00)]
        for bx0, by0, bx1, by1 in blobs:
            self.d.ellipse((x0 + bx0 * w, y0 + by0 * h, x0 + bx1 * w, y0 + by1 * h), fill=outline)
        for bx0, by0, bx1, by1 in blobs:
            self.d.ellipse((x0 + bx0 * w + width, y0 + by0 * h + width, x0 + bx1 * w - width,
                            y0 + by1 * h - width), fill=fill)

    # -------------------------------------------------------------------- lines and arrows
    def polyline(self, pts, fill=LINE, width: int = 3, dash=None) -> None:
        pts = [(float(x), float(y)) for x, y in pts]
        if dash:
            for a, b in zip(pts, pts[1:]):
                for s0, s1 in _dash_segments(a, b, dash):
                    self.d.line([s0, s1], fill=fill, width=width)
        else:
            self.d.line(pts, fill=fill, width=width, joint="curve")

    def arrowhead(self, p_from, p_to, size: int = 18, fill=LINE, open_: bool = False) -> None:
        (x0, y0), (x1, y1) = p_from, p_to
        ang = math.atan2(y1 - y0, x1 - x0)
        a1, a2 = ang + math.pi * 0.85, ang - math.pi * 0.85
        p1 = (x1 + size * math.cos(a1), y1 + size * math.sin(a1))
        p2 = (x1 + size * math.cos(a2), y1 + size * math.sin(a2))
        if open_:
            self.d.line([p1, (x1, y1), p2], fill=fill, width=3)
        else:
            self.d.polygon([(x1, y1), p1, p2], fill=fill)

    def arrow(self, pts, fill=LINE, width: int = 3, head_end: bool = True, head_start: bool = False,
              dash=None, head: int = 18) -> None:
        pts = [(float(x), float(y)) for x, y in pts]
        # shorten the line so it does not poke through the arrowhead tip
        draw = list(pts)
        if head_end and len(draw) >= 2:
            draw[-1] = _shorten(draw[-2], draw[-1], head * 0.6)
        if head_start and len(draw) >= 2:
            draw[0] = _shorten(draw[1], draw[0], head * 0.6)
        self.polyline(draw, fill, width, dash)
        if head_end:
            self.arrowhead(pts[-2], pts[-1], head, fill)
        if head_start:
            self.arrowhead(pts[1], pts[0], head, fill)

    def label(self, cx: float, cy: float, s: str, size: int = 22, fill: str = INK, bg: str = WHITE,
              outline: str | None = None, pad: int = 6, bold: bool = False, max_w: int | None = None,
              radius: int = 6, mono: bool = False) -> tuple:
        """A text pill centred on (cx, cy). Multi-line via '\\n' or max_w wrapping. Returns its box."""
        lines = self.wrap(s, size, max_w, bold, mono) if max_w else str(s).split("\n")
        lh = int(size * 1.28)
        tw = max(self.twidth(l, size, bold, mono) for l in lines)
        th = lh * len(lines) - int(size * 0.28)
        box = (cx - tw / 2 - pad, cy - th / 2 - pad, cx + tw / 2 + pad, cy + th / 2 + pad + 2)
        self.rect(box, fill=bg, outline=outline or bg, width=2 if outline else 1, radius=radius)
        y = cy - th / 2
        for ln in lines:
            self.text(cx, y, ln, size, bold, mono, fill, anchor="ma")
            y += lh
        return box

    # -------------------------------------------------------------------- page furniture
    def title_band(self, title: str, subtitle: str = "", h: int = 120, fill: str = NAVY, size: int = 44,
                   right: str = "", sub_size: int = 26) -> int:
        self.rect((0, 0, self.w, h), fill=fill, outline=fill, width=1)
        self.text(40, h * 0.18, title, size, True, fill=WHITE)
        if subtitle:
            self.text(42, h * 0.18 + size * 1.22, subtitle, sub_size, fill="#DCE6F2")
        if right:
            self.text(self.w - 40, h * 0.22, right, sub_size, fill="#DCE6F2", anchor="ra")
        return h

    def footer_band(self, left: str, right: str = "", h: int = 54, size: int = 22, fill: str = GREY_L) -> None:
        self.rect((0, self.h - h, self.w, self.h), fill=fill, outline=fill, width=1)
        self.text(30, self.h - h / 2, left, size, fill=INK2, anchor="lm")
        if right:
            self.text(self.w - 30, self.h - h / 2, right, size, fill=INK2, anchor="rm")

    def legend(self, x: int, y: int, items: Sequence[tuple[str, str]], size: int = 22, title: str = "Legend",
               swatch: int = 30, cols: int = 1, col_w: int = 360) -> tuple:
        """items: (style_key_or_colour, label). Returns bounding box."""
        rows = math.ceil(len(items) / cols)
        w = col_w * cols + 30
        h = 56 + rows * (swatch + 14)
        self.rect((x, y, x + w, y + h), fill=WHITE, outline=GRID, width=2, radius=8)
        self.text(x + 16, y + 12, title, size, True, fill=INK2)
        for i, (st, lab) in enumerate(items):
            c, r = divmod(i, rows)
            sx, sy = x + 16 + c * col_w, y + 50 + r * (swatch + 14)
            if st in STYLES:
                f, o, _ = STYLES[st]
            else:
                f, o = st, st
            self.rect((sx, sy, sx + swatch, sy + swatch), fill=f, outline=o, width=3, radius=5)
            self.text(sx + swatch + 12, sy + swatch / 2, lab, size, fill=INK, anchor="lm")
        return (x, y, x + w, y + h)

    def stamp(self, cx: float, cy: float, s: str, size: int = 30, color: str = RED, angle: float = 0) -> None:
        tw = self.twidth(s, size, True)
        layer = Image.new("RGBA", (tw + 40, int(size * 1.9)), (0, 0, 0, 0))
        dl = ImageDraw.Draw(layer)
        dl.rounded_rectangle((3, 3, layer.width - 3, layer.height - 3), radius=8, outline=color, width=4)
        dl.text((layer.width / 2, layer.height / 2), s, font=F(size, True), fill=color, anchor="mm")
        if angle:
            layer = layer.rotate(angle, expand=True, resample=Image.BICUBIC)
        self.img.paste(layer, (int(cx - layer.width / 2), int(cy - layer.height / 2)), layer)

    def paste(self, im: Image.Image, x: int, y: int, w: int | None = None, h: int | None = None) -> tuple:
        if w or h:
            if w and not h:
                h = int(im.height * w / im.width)
            elif h and not w:
                w = int(im.width * h / im.height)
            im = im.resize((int(w), int(h)), Image.LANCZOS)
        if im.mode == "RGBA":
            self.img.paste(im, (int(x), int(y)), im)
        else:
            self.img.paste(im.convert("RGB"), (int(x), int(y)))
        return (x, y, x + im.width, y + im.height)

    # -------------------------------------------------------------------- output
    def png_bytes(self) -> bytes:
        return png_bytes(self.img)


def png_bytes(img: Image.Image) -> bytes:
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=False, compress_level=9)
    return buf.getvalue()


def _shorten(p_from, p_to, by: float):
    (x0, y0), (x1, y1) = p_from, p_to
    L = math.hypot(x1 - x0, y1 - y0)
    if L <= by or L == 0:
        return p_to
    return (x1 - (x1 - x0) * by / L, y1 - (y1 - y0) * by / L)


def fmt_int(n: int) -> str:
    return f"{n:,}"


def fmt_date_long(d: str) -> str:
    """'2026-07-02' -> '2 July 2026'."""
    import datetime as dt
    x = dt.date.fromisoformat(str(d)[:10])
    return f"{x.day} {x.strftime('%B')} {x.year}"


def fmt_date_short(d: str) -> str:
    """'2026-07-02' -> '02 Jul 2026'."""
    import datetime as dt
    x = dt.date.fromisoformat(str(d)[:10])
    return x.strftime("%d %b %Y")

"""Whiteboard-photo renderer: marker-style, slightly irregular lettering on a lit whiteboard.

Letters are drawn one by one with util.font (DejaVu Sans Bold), each with its own small rotation,
baseline wobble and size jitter, so the text looks hand-written while staying OCR-legible
(cap height well above 14 px, dark marker on a near-white board).
"""
from __future__ import annotations

import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import math

from PIL import Image, ImageDraw, ImageFilter

from generators.common import util

MARKERS = {
    "black": (28, 30, 36),
    "blue": (22, 52, 140),
    "red": (170, 24, 28),
    "green": (18, 110, 52),
}


def _board(w: int, h: int, r) -> Image.Image:
    """Board background: soft light falloff, a glare patch, aluminium frame, faint ghosting."""
    img = Image.new("RGB", (w, h), (236, 238, 236))
    px = img.load()
    cx, cy = w * (0.35 + 0.1 * r.random()), h * (0.3 + 0.1 * r.random())
    maxd = math.hypot(w, h)
    for y in range(0, h, 2):
        for x in range(0, w, 2):
            dd = math.hypot(x - cx, y - cy) / maxd
            v = int(247 - 26 * dd)
            c = (v, v + 1 if v < 255 else v, v - 1)
            for yy in (y, y + 1):
                for xx in (x, x + 1):
                    if xx < w and yy < h:
                        px[xx, yy] = c
    d = ImageDraw.Draw(img, "RGBA")
    # faint ghosts of erased writing
    for _ in range(9):
        x0, y0 = r.randrange(w), r.randrange(h)
        pts = [(x0 + k * 18, y0 + int(10 * math.sin(k / 2.0 + r.random()))) for k in range(r.randint(8, 20))]
        d.line(pts, fill=(160, 165, 175, 22), width=6)
    # frame
    fw = max(14, w // 70)
    d.rectangle([0, 0, w - 1, fw], fill=(178, 182, 186, 255))
    d.rectangle([0, h - fw, w - 1, h - 1], fill=(165, 169, 173, 255))
    d.rectangle([0, 0, fw, h - 1], fill=(172, 176, 180, 255))
    d.rectangle([w - fw, 0, w - 1, h - 1], fill=(160, 164, 168, 255))
    d.rectangle([0, h - fw - 22, w - 1, h - fw], fill=(150, 154, 158, 255))  # pen tray
    return img


def _glyph(ch: str, size: int, colour, angle: float) -> Image.Image:
    f = util.font(size, bold=True)
    box = f.getbbox(ch)
    gw, gh = max(1, box[2] - box[0] + 8), max(1, size + size // 2)
    tile = Image.new("RGBA", (gw, gh), (0, 0, 0, 0))
    ImageDraw.Draw(tile).text((4 - box[0], size // 6), ch, font=f, fill=colour + (235,))
    return tile.rotate(angle, resample=Image.BICUBIC, expand=True)


def write_line(img: Image.Image, text: str, x: int, y: int, size: int, colour: str, r,
               underline: bool = False, box: bool = False) -> tuple[int, int, int, int]:
    """Draw one hand-written line; returns its bounding box."""
    col = MARKERS[colour]
    f = util.font(size, bold=True)
    cx = x
    slope = r.uniform(-0.012, 0.012)
    top, bottom = y, y + size
    for i, ch in enumerate(text):
        adv = f.getlength(ch)
        if ch == " ":
            cx += int(adv * r.uniform(0.95, 1.25))
            continue
        s = int(size * r.uniform(0.94, 1.06))
        g = _glyph(ch, s, col, r.uniform(-5, 5))
        gy = int(y + slope * (cx - x) + r.uniform(-2.5, 2.5))
        img.paste(g, (int(cx), gy), g)
        top, bottom = min(top, gy), max(bottom, gy + g.size[1])
        cx += adv * r.uniform(0.98, 1.10) + 1
    d = ImageDraw.Draw(img)
    if underline:
        uy = int(y + size * 1.32)
        d.line([(x - 4, uy + 2), ((x + cx) / 2, uy - 2), (cx + 6, uy + 3)], fill=col, width=max(3, size // 14))
    if box:
        pad = size // 3
        pts = [(x - pad, top - pad // 2), (cx + pad, top - pad // 2 + 3), (cx + pad - 3, bottom + pad // 3),
               (x - pad + 2, bottom + pad // 3 + 2), (x - pad, top - pad // 2)]
        d.line(pts, fill=col, width=max(3, size // 15), joint="curve")
    return (x, top, int(cx), bottom)


def render(lines: list[dict], size: tuple[int, int], key: str) -> Image.Image:
    """lines: [{text, x, y, size, colour, underline?, box?}] in board pixels."""
    r = util.rng(key)
    w, h = size
    img = _board(w, h, r)
    for ln in lines:
        write_line(img, ln["text"], ln["x"], ln["y"], ln["size"], ln.get("colour", "black"), r,
                   underline=ln.get("underline", False), box=ln.get("box", False))
    # magnets
    d = ImageDraw.Draw(img)
    for _ in range(2):
        mx, my = r.randrange(60, w - 60), r.randrange(40, 90)
        d.ellipse([mx - 14, my - 14, mx + 14, my + 14], fill=(200, 40, 40) if r.random() < 0.5 else (40, 90, 200))
    # photo feel: board seen slightly off-axis against a wall, soft focus, sensor grain
    img = img.filter(ImageFilter.GaussianBlur(0.7))
    j = lambda a: int(a * r.uniform(0.6, 1.4))  # noqa: E731
    dst = [(j(46), j(38)), (w - j(30), j(58)), (w - j(52), h - j(30)), (j(28), h - j(50))]
    src = [(0, 0), (w, 0), (w, h), (0, h)]
    coeffs = _perspective_coeffs(dst, src)
    wall = Image.new("RGB", (w, h), (196, 188, 172))
    wd = ImageDraw.Draw(wall)
    for yy in range(h):
        v = int(14 * yy / h)
        wd.line([(0, yy), (w, yy)], fill=(196 - v, 188 - v, 172 - v))
    mask = Image.new("L", (w, h), 255).transform((w, h), Image.PERSPECTIVE, coeffs, resample=Image.BICUBIC, fillcolor=0)
    warped = img.transform((w, h), Image.PERSPECTIVE, coeffs, resample=Image.BICUBIC)
    wall.paste(warped, (0, 0), mask)
    return _grain(wall, r, 3.0)


def _perspective_coeffs(dst, src):
    """Coefficients for Image.PERSPECTIVE mapping output points ``dst`` back to input points ``src``."""
    import numpy as np
    rows, rhs = [], []
    for (x, y), (u, v) in zip(dst, src):
        rows.append([x, y, 1, 0, 0, 0, -u * x, -u * y]); rhs.append(u)
        rows.append([0, 0, 0, x, y, 1, -v * x, -v * y]); rhs.append(v)
    sol = np.linalg.solve(np.array(rows, dtype=float), np.array(rhs, dtype=float))
    return tuple(float(c) for c in sol)


def _grain(img: Image.Image, r, amp: float) -> Image.Image:
    import numpy as np
    seed = r.randrange(2 ** 32)
    gen = np.random.default_rng(seed)
    a = np.asarray(img, dtype=np.int16)
    noise = gen.normal(0, amp, a.shape[:2])[..., None]
    out = np.clip(a + noise, 0, 255).astype(np.uint8)
    return Image.fromarray(out, "RGB")

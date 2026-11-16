"""LD002: turn the rendered LD001 PDF into an image-only 'scanned signed copy'.

Each page is rasterised in grayscale, optionally gets a rubber stamp or a handwritten margin
note drawn onto the 'paper', then scan artefacts are applied (skew, noise, speckles, scanner-bed
edge, slight blur) and the page is JPEG-encoded into a new PDF with no text layer.
"""
from __future__ import annotations

import concurrent.futures as cf
import io
import math
import multiprocessing
import pathlib

from generators.common import util

NOISE_SIGMA = 1.7      # sensor noise (grey levels)
BLUR_RADIUS = 0.45     # optical softness at 150 dpi (scaled with dpi)


def _hand_font(size):
    from PIL import ImageFont
    import matplotlib
    base = pathlib.Path(matplotlib.get_data_path()) / "fonts" / "ttf"
    return ImageFont.truetype(str(base / "DejaVuSans-Oblique.ttf"), size)


def draw_stamp(img, x, y, lines, rng, scale):
    """Rubber stamp: double border, bold first line, slight rotation and patchy ink."""
    from PIL import Image, ImageDraw, ImageFilter
    f_big = util.font(int(46 * scale), bold=True)
    f_sm = util.font(int(27 * scale), bold=True)
    pad = int(18 * scale)
    tmp = Image.new("L", (10, 10))
    dd = ImageDraw.Draw(tmp)
    widths = [dd.textlength(lines[0], font=f_big)] + [dd.textlength(t, font=f_sm) for t in lines[1:]]
    w = int(max(widths) + 2 * pad + 10)
    h = int(46 * scale + 2 * 36 * scale + 2 * pad + 18 * scale)
    layer = Image.new("L", (w, h), 0)            # alpha mask of ink
    d = ImageDraw.Draw(layer)
    d.rectangle([2, 2, w - 3, h - 3], outline=255, width=max(3, int(4 * scale)))
    d.rectangle([int(9 * scale), int(9 * scale), w - int(10 * scale), h - int(10 * scale)], outline=255, width=max(1, int(2 * scale)))
    cy = pad
    d.text(((w - widths[0]) / 2, cy), lines[0], fill=255, font=f_big)
    cy += int(56 * scale)
    for t, tw in zip(lines[1:], widths[1:]):
        d.text(((w - tw) / 2, cy), t, fill=255, font=f_sm)
        cy += int(36 * scale)
    # patchy ink: knock out random small spots
    px = layer.load()
    for _ in range(int(w * h * 0.004)):
        i, j = rng.randrange(w), rng.randrange(h)
        px[i, j] = int(px[i, j] * 0.35)
    layer = layer.rotate(rng.uniform(-3.5, -2.0), expand=True, resample=Image.BICUBIC)
    ink = Image.new("L", layer.size, 70)
    img.paste(ink, (int(x), int(y)), layer.point(lambda v: int(v * 0.88)))


def draw_note(img, x, y, lines, rng, scale):
    """Handwriting-style note: oblique font, wavy baseline, uneven pressure, slight slope."""
    from PIL import Image, ImageDraw
    f = _hand_font(int(31 * scale))
    tmp = Image.new("L", (10, 10))
    dd = ImageDraw.Draw(tmp)
    lh = int(46 * scale)
    w = int(max(dd.textlength(t, font=f) for t in lines) + 60 * scale)
    h = lh * len(lines) + int(30 * scale)
    layer = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(layer)
    for li, t in enumerate(lines):
        cx = int(10 * scale) + rng.randint(0, int(12 * scale))
        base = int(8 * scale) + li * lh
        for ch in t:
            dy = int(2.2 * scale * math.sin(cx / (23.0 * scale)) + rng.uniform(-1.2, 1.2) * scale)
            d.text((cx, base + dy), ch, fill=255, font=f)
            d.text((cx + 1, base + dy), ch, fill=200, font=f)   # pen width
            cx += d.textlength(ch, font=f) + rng.uniform(-0.6, 1.0) * scale
    # underline flourish under the first line
    d.line([(int(8 * scale), int(lh * 0.95)), (int(w * 0.72), int(lh * 0.98))], fill=220, width=max(2, int(2 * scale)))
    layer = layer.rotate(rng.uniform(1.0, 2.2), expand=True, resample=Image.BICUBIC)
    ink = Image.new("L", layer.size, 55)
    img.paste(ink, (int(x), int(y)), layer)


def _scan_page(args):
    pdf_path, pno, dpi, quality, overlays, seed_key = args
    import numpy as np
    import pymupdf
    from PIL import Image, ImageFilter
    rng = util.rng(f"{seed_key}:page:{pno}")
    with pymupdf.open(pdf_path) as doc:
        pix = doc[pno - 1].get_pixmap(dpi=dpi, colorspace=pymupdf.csGRAY, alpha=False)
        img = Image.frombytes("L", (pix.width, pix.height), pix.samples)
    scale = dpi / 150.0
    for ov in overlays:
        x, y = ov["x_pt"] * dpi / 72.0, ov["y_pt"] * dpi / 72.0
        if ov["kind"] == "stamp":
            draw_stamp(img, x, y, ov["lines"], rng, scale)
        elif ov["kind"] == "note":
            draw_note(img, x, y, ov["lines"], rng, scale)
    W, H = img.size
    a = np.asarray(img, dtype=np.float32)
    # paper tone and uneven illumination
    yy, xx = np.mgrid[0:H, 0:W]
    gx = rng.uniform(-6, 6) * (xx / W - 0.5)
    gy = rng.uniform(-5, 5) * (yy / H - 0.5)
    a = a * 0.965 + 4 + gx + gy
    # sensor noise (seeded)
    nrng = np.random.default_rng(int(rng.random() * 2 ** 32))
    a += nrng.normal(0, NOISE_SIGMA, size=a.shape)
    img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "L").copy()   # copy: fromarray views are read-only
    # speckles
    px = img.load()
    for _ in range(rng.randint(120, 320)):
        i, j = rng.randrange(W), rng.randrange(H)
        r = rng.choice([0, 0, 0, 1, 1, 2])
        v = rng.randint(40, 120)
        for di in range(-r, r + 1):
            for dj in range(-r, r + 1):
                if 0 <= i + di < W and 0 <= j + dj < H and di * di + dj * dj <= r * r:
                    px[i + di, j + dj] = v
    # skew; exposed corners show the darker scanner lid
    ang = rng.choice([-1, 1]) * rng.uniform(0.3, 0.8)
    img = img.rotate(ang, resample=Image.BICUBIC, expand=False, fillcolor=96)
    # uneven paper edge: jagged shadow band on one side
    a = np.asarray(img, dtype=np.float32).copy()
    side = rng.choice(["left", "right"])
    width = rng.uniform(4, 9) * scale
    walk = width
    for row in range(H):
        walk = max(2.0, min(18.0 * scale, walk + rng.uniform(-0.9, 0.9)))
        wpx = int(walk)
        if side == "left":
            a[row, :wpx] = a[row, :wpx] * 0.45 + 30
            a[row, wpx:wpx + 3] *= 0.85
        else:
            a[row, W - wpx:] = a[row, W - wpx:] * 0.45 + 30
            a[row, W - wpx - 3:W - wpx] *= 0.85
    img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "L").filter(ImageFilter.GaussianBlur(BLUR_RADIUS * scale))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=quality, optimize=True)
    return pno, buf.getvalue()


def make_scan(pdf_in: pathlib.Path, pdf_out: pathlib.Path, overlays: dict, dpi: int, quality: int,
              seed_key: str, jobs: int = 6, meta: dict | None = None) -> dict:
    import pymupdf
    with pymupdf.open(pdf_in) as src:
        n = src.page_count
        sizes = [(src[i].rect.width, src[i].rect.height) for i in range(n)]
    work = [(str(pdf_in), p, dpi, quality, overlays.get(p, []), seed_key) for p in range(1, n + 1)]
    ctx = multiprocessing.get_context("spawn")
    results = {}
    with cf.ProcessPoolExecutor(max_workers=jobs, mp_context=ctx) as ex:
        for pno, data in ex.map(_scan_page, work, chunksize=8):
            results[pno] = data
    out = pymupdf.open()
    for p in range(1, n + 1):
        w, h = sizes[p - 1]
        page = out.new_page(width=w, height=h)
        page.insert_image(page.rect, stream=results[p])
    md = {"title": "", "author": "", "subject": "", "keywords": "", "creator": "Scan station", "producer": "Scan station",
          "creationDate": "D:20260703091500", "modDate": "D:20260703091500", "trapped": "", "format": "PDF 1.7", "encryption": None}
    if meta:
        md.update(meta)
    out.set_metadata(md)
    pdf_out.parent.mkdir(parents=True, exist_ok=True)
    out.save(str(pdf_out), garbage=3, deflate=True, no_new_id=True)
    out.close()
    with pymupdf.open(pdf_out) as chk:
        for i in range(chk.page_count):
            assert chk[i].get_text().strip() == "", f"page {i + 1} has a text layer"
        pages = chk.page_count
    return {"pages": pages, "bytes": pdf_out.stat().st_size}

"""Procedural imagery for LD021 (Claims Assessor Field Guide and Photo Atlas).

Every image is generated with numpy/Pillow from a deterministic rng: textured damage "photographs"
(water stains, fire char, cracked plaster, brickwork, vehicle panels, ...), annotated diagrams and
tables rendered as images. Photo captions are burned into the raster (white on a dark band) at a size
that Apple Vision OCR reads reliably once the PDF page is rasterised at 200 dpi.
"""
from __future__ import annotations

import math

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from .common import util

PHOTO_W, PHOTO_H = 1800, 1200
HERO_W, HERO_H = 1800, 820


def _nprng(r):
    return np.random.default_rng(r.getrandbits(63))


def fbm(r, h, w, base=4, octaves=5, persistence=0.55):
    """Fractal value noise in roughly [-1, 1]."""
    g = _nprng(r)
    out = np.zeros((h, w), np.float32)
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        gh = max(2, int(base * (2 ** o) * h / max(h, w)) + 2)
        gw = max(2, int(base * (2 ** o) * w / max(h, w)) + 2)
        grid = g.standard_normal((gh, gw)).astype(np.float32)
        layer = np.asarray(Image.fromarray(grid, mode="F").resize((w, h), Image.BICUBIC), np.float32)
        out += amp * layer
        tot += amp
        amp *= persistence
    out /= tot
    return np.clip(out / (out.std() * 2.5 + 1e-6), -1, 1)


def grain(r, h, w, sigma):
    return _nprng(r).normal(0, sigma, (h, w, 1)).astype(np.float32) * np.ones((1, 1, 3), np.float32) + \
        _nprng(r).normal(0, sigma * 0.55, (h, w, 3)).astype(np.float32)


def _mix(a, b, m):
    m = m[..., None] if m.ndim == 2 else m
    return a * (1 - m) + b * m


def _col(c, h, w):
    return np.ones((h, w, 3), np.float32) * np.array(c, np.float32)


def _vignette(img, strength=0.28):
    h, w = img.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    d = np.sqrt(((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2)
    return img * (1 - strength * np.clip(d - 0.35, 0, 1.2) ** 1.6)[..., None]


# ---------------------------------------------------------------------------------------------
# Textures
# ---------------------------------------------------------------------------------------------

def plaster(r, h, w, tint=(226, 219, 204)):
    base = _col(tint, h, w)
    base += (fbm(r, h, w, base=3, octaves=4) * 14)[..., None]
    base += (fbm(r, h, w, base=40, octaves=2) * 6)[..., None]
    return base


def water_stain(r, h, w):
    img = plaster(r, h, w, tint=(r.randint(218, 232), r.randint(212, 224), r.randint(196, 210)))
    field = fbm(r, h, w, base=3, octaves=6) * 0.55
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    for _ in range(r.randint(2, 4)):
        cx, cy = r.uniform(0.15, 0.85) * w, r.uniform(-0.1, 0.6) * h
        rx, ry = r.uniform(0.15, 0.35) * w, r.uniform(0.18, 0.45) * h
        field += np.exp(-(((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2))
    t = 0.55
    inner = 1 / (1 + np.exp(-(field - t) / 0.04))
    stain_col = np.array([r.randint(160, 185), r.randint(130, 150), r.randint(80, 100)], np.float32)
    img = _mix(img, img * 0.55 + stain_col * 0.45, inner * 0.75)
    for k in range(r.randint(3, 5)):
        lvl = t + 0.05 + k * r.uniform(0.07, 0.12)
        ring = np.exp(-((field - lvl) / 0.012) ** 2)
        img = _mix(img, np.array([120, 92, 55], np.float32) * np.ones_like(img), ring * 0.55)
    edge = np.exp(-((field - t) / 0.01) ** 2)
    img = _mix(img, np.array([98, 74, 44], np.float32) * np.ones_like(img), edge * 0.7)
    # mould speckle near the lower part of the stain
    pil = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(pil)
    for _ in range(r.randint(150, 400)):
        x, y = r.uniform(0, w), r.uniform(0.55, 1.0) * h
        if inner[int(min(y, h - 1)), int(min(x, w - 1))] > 0.3:
            s = r.uniform(1.5, 5)
            g = r.randint(25, 60)
            d.ellipse([x - s, y - s, x + s, y + s], fill=(g, g + 8, g))
    return np.asarray(pil, np.float32)


def _voronoi(r, h, w, n):
    """Distances to the nearest and second-nearest seed (computed at reduced resolution)."""
    sh, sw = h // 4, w // 4
    g = _nprng(r)
    pts = np.stack([g.uniform(0, sw, n), g.uniform(0, sh, n)], 1).astype(np.float32)
    yy, xx = np.mgrid[0:sh, 0:sw].astype(np.float32)
    P = np.stack([xx.ravel(), yy.ravel()], 1)
    d1 = np.full(P.shape[0], 1e9, np.float32)
    d2 = np.full(P.shape[0], 1e9, np.float32)
    for i in range(0, n, 64):
        chunk = pts[i:i + 64]
        dd = np.sqrt(((P[:, None, :] - chunk[None, :, :]) ** 2).sum(-1))
        for j in range(dd.shape[1]):
            dj = dd[:, j]
            m2 = dj < d2
            m1 = dj < d1
            d2 = np.where(m1, d1, np.where(m2, dj, d2))
            d1 = np.where(m1, dj, d1)
    d1 = d1.reshape(sh, sw)
    d2 = d2.reshape(sh, sw)
    up = lambda a: np.asarray(Image.fromarray(a, mode="F").resize((w, h), Image.BILINEAR), np.float32)
    return up(d1), up(d2)


def fire_char(r, h, w):
    d1, d2 = _voronoi(r, h, w, r.randint(220, 380))
    crack = np.clip(1 - (d2 - d1) / 1.6, 0, 1) ** 2
    blister = np.clip(1 - d1 / (d1.max() * 0.6 + 1e-6), 0, 1)
    base = _col((40, 35, 32), h, w)
    base += (blister * r.uniform(30, 55))[..., None]
    base += (fbm(r, h, w, base=6, octaves=4) * 10)[..., None]
    img = _mix(base, _col((8, 7, 7), h, w), crack * 0.9)
    yy = np.mgrid[0:h, 0:w][0].astype(np.float32) / h
    ember = np.clip(fbm(r, h, w, base=5, octaves=4) * 1.4 + (yy - 0.75) * 2.0, 0, 1) ** 2.2
    img = _mix(img, _col((205, 92, 28), h, w), ember * 0.55 * crack)
    soot = np.clip(1 - yy * 1.2 + fbm(r, h, w, base=2, octaves=3) * 0.3, 0, 1)
    return _mix(img, _col((18, 17, 17), h, w), soot * 0.35)


def smoke_ceiling(r, h, w):
    img = plaster(r, h, w, tint=(232, 230, 224))
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    cx, cy = r.uniform(0.1, 0.9) * w, r.uniform(0.6, 1.1) * h
    plume = np.exp(-(((xx - cx) / (0.45 * w)) ** 2 + ((yy - cy) / (0.7 * h)) ** 2))
    plume = np.clip(plume + fbm(r, h, w, base=3, octaves=5) * 0.25, 0, 1)
    img = _mix(img, _col((48, 44, 40), h, w), plume * 0.85)
    period = r.randint(110, 170)
    joists = (np.sin(xx / period * 2 * math.pi) > 0.82).astype(np.float32)
    joists = np.asarray(Image.fromarray((joists * 255).astype(np.uint8), mode="L").filter(ImageFilter.GaussianBlur(6)),
                        np.float32) / 255
    return _mix(img, _col((30, 28, 26), h, w), joists * plume * 0.4)


def _crack_paths(r, h, w, n, vertical=True):
    paths = []
    for _ in range(n):
        if vertical:
            x, y, ang = r.uniform(0.2, 0.8) * w, 0, math.pi / 2 + r.uniform(-0.5, 0.5)
        else:
            x, y, ang = 0, r.uniform(0.2, 0.8) * h, r.uniform(-0.6, 0.6)
        pts = [(x, y)]
        width = r.uniform(6, 13)
        while 0 <= x <= w and 0 <= y <= h and len(pts) < 400:
            ang += r.uniform(-0.35, 0.35)
            ang = 0.85 * ang + 0.15 * (math.pi / 2 if vertical else 0)
            step = r.uniform(12, 26)
            x += math.cos(ang) * step
            y += math.sin(ang) * step
            pts.append((x, y))
        paths.append((pts, width))
    return paths


def cracked_plaster(r, h, w):
    img = plaster(r, h, w, tint=(r.randint(220, 236), r.randint(214, 228), r.randint(200, 214)))
    mask = Image.new("L", (w, h), 0)
    hl = Image.new("L", (w, h), 0)
    dm, dh = ImageDraw.Draw(mask), ImageDraw.Draw(hl)
    for pts, width in _crack_paths(r, h, w, r.randint(1, 3), vertical=r.random() < 0.6):
        n = len(pts)
        for i in range(n - 1):
            wd = max(1, int(width * (1 - i / n) + 1))
            dm.line([pts[i], pts[i + 1]], fill=255, width=wd)
            dh.line([(pts[i][0] + 3, pts[i][1] + 2), (pts[i + 1][0] + 3, pts[i + 1][1] + 2)], fill=200, width=max(1, wd // 2))
            if r.random() < 0.03:
                bx, by = pts[i]
                ang = r.uniform(0, 2 * math.pi)
                L = r.uniform(40, 160)
                dm.line([(bx, by), (bx + math.cos(ang) * L, by + math.sin(ang) * L)], fill=200, width=2)
    m = np.asarray(mask.filter(ImageFilter.GaussianBlur(1.2)), np.float32) / 255
    hm = np.asarray(hl.filter(ImageFilter.GaussianBlur(2)), np.float32) / 255
    img = _mix(img, _col((250, 248, 240), h, w), hm * 0.35)
    return _mix(img, _col((38, 34, 30), h, w), m)


def brickwork(r, h, w, stepped_crack=True):
    bw, bh, mort = r.randint(150, 190), r.randint(52, 64), r.randint(9, 13)
    img = _col((168, 162, 150), h, w) + (fbm(r, h, w, base=50, octaves=2) * 12)[..., None]
    pil = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(pil)
    row = 0
    y = -r.randint(0, bh)
    while y < h:
        off = (bw + mort) // 2 if row % 2 else 0
        x = -off
        while x < w:
            c = (r.randint(140, 185), r.randint(62, 90), r.randint(40, 62))
            d.rectangle([x, y, x + bw, y + bh], fill=c)
            x += bw + mort
        y += bh + mort
        row += 1
    img = np.asarray(pil, np.float32)
    img += (fbm(r, h, w, base=60, octaves=3) * 16)[..., None]
    if stepped_crack:
        crack = Image.new("L", (w, h), 0)
        dc = ImageDraw.Draw(crack)
        x, y = r.uniform(0.25, 0.45) * w, h
        pts = [(x, y)]
        while y > 0 and x < w:
            y -= bh + mort
            pts.append((x, y))
            x += (bw + mort) / 2
            pts.append((x, y))
        dc.line(pts, fill=255, width=r.randint(8, 14), joint="curve")
        m = np.asarray(crack.filter(ImageFilter.GaussianBlur(1.5)), np.float32) / 255
        img = _mix(img, _col((22, 20, 18), h, w), m)
    return img


def flood_wall(r, h, w):
    img = plaster(r, h, w, tint=(218, 214, 200))
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    level = r.uniform(0.45, 0.65) * h + np.sin(xx / w * r.uniform(4, 9)) * 6 + fbm(r, h, w, base=8, octaves=3) * 10
    below = 1 / (1 + np.exp(np.clip(-(yy - level) / 4, -60, 60)))
    silt = _col((140, 118, 86), h, w) + (fbm(r, h, w, base=12, octaves=4) * 25)[..., None]
    img = _mix(img, img * 0.45 + silt * 0.55, below * 0.85)
    line = np.exp(-((yy - level) / 5) ** 2)
    img = _mix(img, _col((82, 66, 44), h, w), line * 0.85)
    sk = (yy > h * 0.88).astype(np.float32)
    img = _mix(img, _col((205, 200, 188), h, w) - (fbm(r, h, w, base=20, octaves=2) * 20)[..., None], sk)
    return img


def roof_tiles(r, h, w):
    img = _col((60, 50, 44), h, w)
    pil = Image.fromarray(img.astype(np.uint8))
    d = ImageDraw.Draw(pil)
    tw, th = r.randint(120, 150), r.randint(90, 110)
    for y in range(-th, h, int(th * 0.62)):
        off = tw // 2 if (y // int(th * 0.62)) % 2 else 0
        for x in range(-off, w, tw):
            if r.random() < 0.07:
                continue                      # missing tile: battens show through
            c = r.randint(95, 135)
            col = (c + 40, c - 10, c - 30) if r.random() < 0.5 else (c, c - 4, c - 8)
            d.rounded_rectangle([x + 3, y, x + tw - 3, y + th], radius=12, fill=col)
            d.line([x + 3, y + th, x + tw - 3, y + th], fill=(30, 26, 24), width=4)
    img = np.asarray(pil, np.float32) + (fbm(r, h, w, base=40, octaves=3) * 14)[..., None]
    moss = np.clip(fbm(r, h, w, base=6, octaves=4) - 0.35, 0, 1) * 1.4
    return _mix(img, _col((88, 104, 52), h, w), moss * 0.5)


def wood_grain(r, h, w, col=(150, 104, 62)):
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    turb = fbm(r, h, w, base=4, octaves=5)
    stripes = np.sin((yy / r.uniform(9, 16)) + turb * r.uniform(6, 12))
    img = _col(col, h, w) + (stripes * 18)[..., None] + (fbm(r, h, w, base=80, octaves=2) * 8)[..., None]
    return img


def forced_door(r, h, w):
    img = wood_grain(r, h, w, col=(r.randint(120, 160), r.randint(80, 110), r.randint(50, 70)))
    pil = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(pil)
    ex = int(r.uniform(0.55, 0.7) * w)
    d.rectangle([ex, 0, ex + 26, h], fill=(70, 50, 34))
    ly = int(r.uniform(0.35, 0.55) * h)
    d.rectangle([ex - 60, ly - 160, ex - 30, ly + 160], fill=(150, 150, 146))
    for k in (-120, 120):
        d.ellipse([ex - 52, ly + k - 8, ex - 38, ly + k + 8], fill=(60, 60, 58))
    poly = [(ex - 10, ly - 220)]
    for i in range(22):
        yy = ly - 220 + i * 20
        poly.append((ex + 30 + r.uniform(0, 140), yy))
    poly.append((ex - 10, ly + 220))
    d.polygon(poly, fill=(214, 182, 132))
    for _ in range(40):
        x0, y0 = ex + r.uniform(0, 120), ly + r.uniform(-200, 200)
        d.line([x0, y0, x0 + r.uniform(20, 80), y0 + r.uniform(-6, 6)], fill=(110, 80, 50), width=2)
    return np.asarray(pil, np.float32)


def timber_floor(r, h, w):
    img = np.zeros((h, w, 3), np.float32)
    bh = r.randint(120, 160)
    for i, y in enumerate(range(0, h, bh)):
        sub = wood_grain(r, bh, w, col=(r.randint(150, 185), r.randint(110, 135), r.randint(70, 90)))
        img[y:y + bh] = sub[:min(bh, h - y)]
        img[y:y + 4] *= 0.45
    stain = np.clip(fbm(r, h, w, base=3, octaves=5) * 1.3 + 0.1, 0, 1)
    img = _mix(img, img * 0.45, stain * 0.7)
    return img


def vehicle_panel(r, h, w):
    palette = [(180, 184, 188), (30, 42, 78), (150, 22, 26), (226, 228, 230), (24, 24, 26), (36, 70, 52)]
    c = np.array(palette[r.randrange(len(palette))], np.float32)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    prof = 0.62 + 0.38 * np.cos((yy / h - r.uniform(0.35, 0.55)) * math.pi * 1.1)
    img = c * prof[..., None]
    band_y = r.uniform(0.25, 0.4) * h + np.sin(xx / w * math.pi) * r.uniform(20, 60)
    spec = np.exp(-((yy - band_y) / r.uniform(18, 40)) ** 2)
    img = _mix(img, _col((250, 250, 250), h, w), spec * 0.75)
    refl = np.asarray(Image.fromarray(fbm(r, h // 8, w // 2, base=6, octaves=3), mode="F").resize((w, h), Image.BICUBIC),
                      np.float32)
    img += (refl * 22)[..., None]
    # dent: shaded gaussian bump (light from upper left)
    cx, cy = r.uniform(0.3, 0.7) * w, r.uniform(0.45, 0.7) * h
    rad = r.uniform(0.08, 0.16) * w
    gx = -(xx - cx) / rad ** 2 * np.exp(-(((xx - cx) ** 2 + (yy - cy) ** 2) / rad ** 2))
    gy = -(yy - cy) / rad ** 2 * np.exp(-(((xx - cx) ** 2 + (yy - cy) ** 2) / rad ** 2))
    shade = (gx * -0.7 + gy * -0.7) * rad * 1.6
    img = img + (shade * 70)[..., None]
    pil = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(pil)
    gap_x = int(r.uniform(0.15, 0.85) * w)
    d.line([gap_x, 0, gap_x + r.randint(-40, 40), h], fill=(12, 12, 12), width=7)
    for _ in range(r.randint(25, 70)):
        x0, y0 = cx + r.uniform(-rad * 1.6, rad * 1.6), cy + r.uniform(-rad, rad)
        L, a = r.uniform(30, 220), r.uniform(-0.4, 0.4)
        g = r.randint(190, 245)
        d.line([x0, y0, x0 + math.cos(a) * L, y0 + math.sin(a) * L], fill=(g, g, g), width=r.choice([1, 2, 2, 3]))
    return np.asarray(pil, np.float32)


def windscreen(r, h, w):
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    img = _col((52, 66, 78), h, w) + ((1 - yy / h) * 40)[..., None] + (fbm(r, h, w, base=3, octaves=4) * 18)[..., None]
    pil = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(pil)
    cx, cy = r.uniform(0.3, 0.7) * w, r.uniform(0.3, 0.6) * h
    for _ in range(r.randint(7, 14)):
        a = r.uniform(0, 2 * math.pi)
        x, y = cx, cy
        for _s in range(r.randint(6, 30)):
            a += r.uniform(-0.25, 0.25)
            nx, ny = x + math.cos(a) * r.uniform(15, 40), y + math.sin(a) * r.uniform(15, 40)
            d.line([x, y, nx, ny], fill=(222, 230, 236), width=2)
            x, y = nx, ny
    d.ellipse([cx - 18, cy - 18, cx + 18, cy + 18], outline=(235, 240, 244), width=4)
    return np.asarray(pil, np.float32)


def debris(r, h, w):
    img = _col((110, 100, 88), h, w) + (fbm(r, h, w, base=10, octaves=5) * 40)[..., None]
    pil = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(pil)
    for _ in range(r.randint(120, 260)):
        x, y = r.uniform(0, w), r.uniform(0, h)
        s = r.uniform(8, 60)
        g = r.randint(40, 200)
        pts = [(x + math.cos(t) * s * r.uniform(0.5, 1.2), y + math.sin(t) * s * r.uniform(0.5, 1.2))
               for t in np.linspace(0, 2 * math.pi, r.randint(4, 7), endpoint=False)]
        d.polygon(pts, fill=(g, int(g * 0.95), int(g * 0.88)))
    return np.asarray(pil, np.float32)


TEXTURES = {
    "water_stain": water_stain, "fire_char": fire_char, "smoke": smoke_ceiling, "crack": cracked_plaster,
    "brick": brickwork, "flood": flood_wall, "roof": roof_tiles, "door": forced_door, "floor": timber_floor,
    "panel": vehicle_panel, "glass": windscreen, "debris": debris, "plaster": plaster,
}


# ---------------------------------------------------------------------------------------------
# Overlays
# ---------------------------------------------------------------------------------------------

def _ruler(d, r, w, h):
    x0, y0 = r.uniform(0.05, 0.4) * w, h - 330
    L = 900
    d.rectangle([x0, y0, x0 + L, y0 + 70], fill=(236, 196, 40), outline=(40, 40, 40), width=2)
    for i in range(0, 151):
        x = x0 + 20 + i * (L - 40) / 150
        tl = 34 if i % 10 == 0 else (22 if i % 5 == 0 else 12)
        d.line([x, y0, x, y0 + tl], fill=(20, 20, 20), width=2)
        if i % 10 == 0 and i:
            d.text((x - 10, y0 + 36), str(i // 10), fill=(20, 20, 20), font=util.font(24, bold=True))
    d.text((x0 + 4, y0 + 40), "cm", fill=(20, 20, 20), font=util.font(22))


def _marker(d, r, w, h, label):
    cx, cy = r.uniform(0.25, 0.75) * w, r.uniform(0.2, 0.6) * h
    rad = r.uniform(80, 140)
    d.ellipse([cx - rad, cy - rad, cx + rad, cy + rad], outline=(230, 30, 30), width=8)
    d.rounded_rectangle([cx + rad * 0.7, cy - rad - 70, cx + rad * 0.7 + 80, cy - rad + 10], radius=10,
                        fill=(230, 30, 30))
    d.text((cx + rad * 0.7 + 22, cy - rad - 62), label, fill=(255, 255, 255), font=util.font(56, bold=True))


def _meter(d, r, w, h, reading):
    x0, y0 = r.uniform(0.55, 0.7) * w, r.uniform(0.12, 0.3) * h
    d.rounded_rectangle([x0, y0, x0 + 360, y0 + 520], radius=36, fill=(44, 46, 50), outline=(20, 20, 20), width=4)
    d.rounded_rectangle([x0 + 34, y0 + 50, x0 + 326, y0 + 210], radius=10, fill=(172, 196, 150))
    d.text((x0 + 58, y0 + 74), reading, fill=(20, 26, 18), font=util.font(96, bold=True, mono=True))
    d.text((x0 + 230, y0 + 168), "%WME", fill=(20, 26, 18), font=util.font(26, bold=True))
    for i, lab in enumerate(("HOLD", "MODE", "WOOD")):
        bx = x0 + 34 + i * 100
        d.rounded_rectangle([bx, y0 + 260, bx + 86, y0 + 320], radius=12, fill=(80, 84, 90))
        d.text((bx + 10, y0 + 278), lab, fill=(230, 230, 230), font=util.font(20, bold=True))
    d.line([x0 + 120, y0 + 520, x0 + 100, y0 + 640], fill=(190, 190, 190), width=8)
    d.line([x0 + 240, y0 + 520, x0 + 260, y0 + 640], fill=(190, 190, 190), width=8)


def caption_band(img: Image.Image, label: str, text: str, font_px=42) -> Image.Image:
    """Burn a caption into the bottom of an image: white text on a near-black band."""
    w, h = img.size
    fb, fr = util.font(font_px, bold=True), util.font(font_px)
    d0 = ImageDraw.Draw(img)
    words = text.split()
    lines, cur = [], label + "  "
    first = True
    for wd in words:
        trial = cur + wd + " "
        width = d0.textlength(trial, font=fr) + (d0.textlength(label + "  ", font=fb) - d0.textlength(label + "  ", font=fr) if first else 0)
        if width > w - 70 and cur.strip():
            lines.append(cur.rstrip())
            cur, first = wd + " ", False
        else:
            cur = trial
    lines.append(cur.rstrip())
    lh = int(font_px * 1.32)
    band = lh * len(lines) + 36
    out = Image.new("RGB", (w, h + band), (16, 16, 16))
    out.paste(img, (0, 0))
    d = ImageDraw.Draw(out)
    y = h + 18
    for i, ln in enumerate(lines):
        x = 34
        if i == 0 and ln.startswith(label):
            d.text((x, y), label, fill=(255, 214, 90), font=fb)
            x += d.textlength(label + "  ", font=fb)
            ln = ln[len(label):].lstrip()
        d.text((x, y), ln, fill=(255, 255, 255), font=fr)
        y += lh
    return out


def photo(key: str, texture: str, label: str, caption: str, overlay: str | None = None, meter: str | None = None,
          marker: str | None = None, size=(PHOTO_W, PHOTO_H), grain_sigma=11.0) -> Image.Image:
    r = util.rng(f"LD021:img:{key}")
    w, h = size
    arr = TEXTURES[texture](r, h, w)
    arr = _vignette(arr, strength=r.uniform(0.18, 0.34))
    arr = arr * r.uniform(0.9, 1.06) + r.uniform(-8, 8)
    arr += grain(r, h, w, grain_sigma)
    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(img)
    if overlay == "ruler":
        _ruler(d, r, w, h)
    if meter:
        _meter(d, r, w, h, meter)
    if marker:
        _marker(d, r, w, h, marker)
    # discreet photo stamp in the corner (camera-style date stamp, from the atlas date)
    if caption is None:
        return img
    d.text((w - 300, 26), f"IMG {r.randint(1000, 9999)}", fill=(255, 170, 40), font=util.font(30, bold=True, mono=True))
    return caption_band(img, label, caption)


def hero(key: str, texture: str) -> Image.Image:
    return photo(key, texture, "", None, size=(HERO_W, HERO_H), grain_sigma=4.5)


# ---------------------------------------------------------------------------------------------
# Tables and diagrams rendered as images (crisp PNG)
# ---------------------------------------------------------------------------------------------

def table_image(title: str, rows: list, col_w: list, font_px=34, header_fill=(11, 79, 108), note: str | None = None,
                width=1800) -> Image.Image:
    fh, fr = util.font(font_px, bold=True), util.font(font_px)
    scale = (width - 60) / sum(col_w)
    cws = [int(c * scale) for c in col_w]
    dtmp = ImageDraw.Draw(Image.new("RGB", (10, 10)))

    def wrap(txt, f, cw):
        out, cur = [], ""
        for wd in str(txt).split():
            t = (cur + " " + wd).strip()
            if dtmp.textlength(t, font=f) > cw - 24 and cur:
                out.append(cur)
                cur = wd
            else:
                cur = t
        out.append(cur)
        return out

    lh = int(font_px * 1.3)
    wrapped = [[wrap(c, fh if ri == 0 else fr, cws[ci]) for ci, c in enumerate(row)] for ri, row in enumerate(rows)]
    heights = [max(len(c) for c in row) * lh + 22 for row in wrapped]
    title_h = int(font_px * 1.9)
    note_lines = wrap(note, util.font(int(font_px * 0.85)), width - 60) if note else []
    note_h = len(note_lines) * int(font_px * 1.15) + (20 if note else 0)
    H = title_h + sum(heights) + note_h + 50
    img = Image.new("RGB", (width, H), (255, 255, 255))
    d = ImageDraw.Draw(img)
    d.text((30, 14), title, fill=(11, 79, 108), font=util.font(int(font_px * 1.12), bold=True))
    y = title_h
    for ri, row in enumerate(wrapped):
        x = 30
        rh = heights[ri]
        fill = header_fill if ri == 0 else ((238, 244, 247) if ri % 2 == 0 else (255, 255, 255))
        d.rectangle([30, y, 30 + sum(cws), y + rh], fill=fill)
        for ci, lines in enumerate(row):
            for li, ln in enumerate(lines):
                d.text((x + 12, y + 11 + li * lh), ln, fill=(255, 255, 255) if ri == 0 else (20, 20, 20),
                       font=fh if ri == 0 else fr)
            d.line([x, y, x, y + rh], fill=(120, 140, 150), width=2)
            x += cws[ci]
        d.line([x, y, x, y + rh], fill=(120, 140, 150), width=2)
        d.line([30, y, 30 + sum(cws), y], fill=(120, 140, 150), width=2)
        y += rh
    d.line([30, y, 30 + sum(cws), y], fill=(120, 140, 150), width=2)
    y += 16
    for ln in note_lines:
        d.text((30, y), ln, fill=(60, 60, 60), font=util.font(int(font_px * 0.85)))
        y += int(font_px * 1.15)
    return img


def _box(d, xy, text, fill=(220, 235, 242), font_px=32, outline=(11, 79, 108)):
    x0, y0, x1, y1 = xy
    d.rounded_rectangle(xy, radius=18, fill=fill, outline=outline, width=4)
    f = util.font(font_px, bold=True)
    lines, cur = [], ""
    for wd in text.split():
        t = (cur + " " + wd).strip()
        if d.textlength(t, font=f) > (x1 - x0 - 30) and cur:
            lines.append(cur)
            cur = wd
        else:
            cur = t
    lines.append(cur)
    lh = int(font_px * 1.25)
    ty = (y0 + y1) / 2 - lh * len(lines) / 2
    for ln in lines:
        tw = d.textlength(ln, font=f)
        d.text(((x0 + x1) / 2 - tw / 2, ty), ln, fill=(15, 30, 40), font=f)
        ty += lh


def _arrow(d, p0, p1, label=None, font_px=28):
    d.line([p0, p1], fill=(40, 40, 40), width=5)
    ang = math.atan2(p1[1] - p0[1], p1[0] - p0[0])
    a1 = (p1[0] - 26 * math.cos(ang - 0.4), p1[1] - 26 * math.sin(ang - 0.4))
    a2 = (p1[0] - 26 * math.cos(ang + 0.4), p1[1] - 26 * math.sin(ang + 0.4))
    d.polygon([p1, a1, a2], fill=(40, 40, 40))
    if label:
        mx, my = (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2
        f = util.font(font_px, bold=True)
        tw = d.textlength(label, font=f)
        d.rectangle([mx - tw / 2 - 8, my - font_px * 0.75, mx + tw / 2 + 8, my + font_px * 0.75], fill=(255, 255, 255))
        d.text((mx - tw / 2, my - font_px * 0.62), label, fill=(160, 20, 20), font=f)


def flow_diagram(title: str, nodes: list, edges: list, size=(1800, 1000)) -> Image.Image:
    """nodes: (id, (x0,y0,x1,y1) in 0..1, text, kind); edges: (from, to, label)."""
    w, h = size
    img = Image.new("RGB", size, (255, 255, 255))
    d = ImageDraw.Draw(img)
    d.text((30, 18), title, fill=(11, 79, 108), font=util.font(40, bold=True))
    pos = {}
    for nid, (a, b, c, e), text, kind in nodes:
        xy = (a * w, b * h, c * w, e * h)
        pos[nid] = xy
        fill = {"start": (210, 236, 222), "decision": (255, 238, 200), "end": (235, 225, 245)}.get(kind, (220, 235, 242))
        _box(d, xy, text, fill=fill)

    def anchor(xy, other):
        x0, y0, x1, y1 = xy
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        ox, oy = (other[0] + other[2]) / 2, (other[1] + other[3]) / 2
        if abs(ox - cx) > abs(oy - cy):
            return (x1, cy) if ox > cx else (x0, cy)
        return (cx, y1) if oy > cy else (cx, y0)

    for a, b, lab in edges:
        _arrow(d, anchor(pos[a], pos[b]), anchor(pos[b], pos[a]), lab)
    return img


def wall_diagram(title, points, size=(1800, 1050)):
    """Wall elevation with labelled measurement points (used for meter probe positions)."""
    w, h = size
    img = Image.new("RGB", size, (255, 255, 255))
    d = ImageDraw.Draw(img)
    d.text((30, 18), title, fill=(11, 79, 108), font=util.font(40, bold=True))
    d.rectangle([120, 120, w - 520, h - 120], outline=(40, 40, 40), width=5)
    d.rectangle([120, h - 200, w - 520, h - 120], fill=(235, 228, 214), outline=(40, 40, 40), width=3)
    d.text((140, h - 185), "skirting", fill=(60, 60, 60), font=util.font(28))
    d.rectangle([560, 300, 860, h - 200], outline=(40, 40, 40), width=4)
    d.text((600, 310), "door", fill=(60, 60, 60), font=util.font(28))
    d.line([1000, 120, 1000, h - 200], fill=(70, 120, 200), width=8)
    d.text((1012, 140), "supply pipe (concealed)", fill=(70, 120, 200), font=util.font(28, bold=True))
    f = util.font(34, bold=True)
    for lab, (x, y), note in points:
        X, Y = 120 + x * (w - 640), 120 + y * (h - 240)
        d.ellipse([X - 22, Y - 22, X + 22, Y + 22], fill=(220, 40, 40))
        d.text((X + 30, Y - 22), lab, fill=(160, 20, 20), font=f)
    y = 140
    for lab, _, note in points:
        d.text((w - 480, y), f"{lab}: {note}", fill=(20, 20, 20), font=util.font(28))
        y += 52
    return img


def house_diagram(title, labels, size=(1800, 1100)):
    w, h = size
    img = Image.new("RGB", size, (255, 255, 255))
    d = ImageDraw.Draw(img)
    d.text((30, 18), title, fill=(11, 79, 108), font=util.font(40, bold=True))
    x0, x1, yb, yt = 260, 1260, h - 140, 380
    d.rectangle([x0, yt, x1, yb], outline=(40, 40, 40), width=6)
    d.polygon([(x0 - 40, yt), ((x0 + x1) / 2, 150), (x1 + 40, yt)], outline=(40, 40, 40), width=6)
    for wx in (380, 900):
        for wy in (460, 740):
            d.rectangle([wx, wy, wx + 200, wy + 160], outline=(40, 40, 40), width=4)
    d.rectangle([650, 760, 800, yb], outline=(40, 40, 40), width=4)
    # diagonal cracks from window corners, tapering
    for (sx, sy, ex, ey) in ((580, 620, 690, 470), (380, 900, 300, 1000), (1100, 740, 1220, 600), (900, 900, 820, 1010)):
        d.line([sx, sy, ex, ey], fill=(200, 30, 30), width=9)
    d.line([x0 - 80, yb, x1 + 80, yb], fill=(110, 80, 50), width=8)
    d.text((x0 - 60, yb + 16), "ground level", fill=(110, 80, 50), font=util.font(28))
    f = util.font(30)
    y = 160
    for i, t in enumerate(labels, 1):
        d.text((1340, y), f"{i}. {t}", fill=(20, 20, 20), font=f)
        y += 56
    return img


def car_diagram(title, panels, size=(1800, 1000)):
    w, h = size
    img = Image.new("RGB", size, (255, 255, 255))
    d = ImageDraw.Draw(img)
    d.text((30, 18), title, fill=(11, 79, 108), font=util.font(40, bold=True))
    body = [(120, 640), (180, 520), (420, 470), (600, 330), (1050, 320), (1260, 470), (1560, 500), (1640, 620),
            (1640, 700), (120, 700)]
    d.polygon(body, outline=(30, 30, 30), width=6)
    for cx in (420, 1340):
        d.ellipse([cx - 110, 610, cx + 110, 830], outline=(30, 30, 30), width=8, fill=(240, 240, 240))
    for x in (600, 880, 1180):
        d.line([x, 340, x, 690], fill=(90, 90, 90), width=3)
    f = util.font(30, bold=True)
    for code, (x, y), name in panels:
        d.ellipse([x - 30, y - 30, x + 30, y + 30], fill=(11, 79, 108))
        tw = d.textlength(code, font=f)
        d.text((x - tw / 2, y - 18), code, fill=(255, 255, 255), font=f)
    yy = 860
    xx = 60
    for code, _, name in panels:
        t = f"{code} {name}"
        d.text((xx, yy), t, fill=(20, 20, 20), font=util.font(26))
        xx += d.textlength(t, font=util.font(26)) + 40
        if xx > w - 300:
            xx, yy = 60, yy + 40
    return img


def vpattern_diagram(title, notes, size=(1800, 1050)):
    w, h = size
    img = Image.new("RGB", size, (255, 255, 255))
    d = ImageDraw.Draw(img)
    d.text((30, 18), title, fill=(11, 79, 108), font=util.font(40, bold=True))
    d.rectangle([120, 140, 1100, h - 100], outline=(40, 40, 40), width=5)
    base = (610, h - 160)
    d.polygon([base, (230, 180), (990, 180)], fill=(70, 62, 58))
    d.polygon([base, (380, 300), (840, 300)], fill=(40, 36, 34))
    d.rectangle([520, h - 190, 700, h - 110], fill=(150, 110, 70), outline=(40, 40, 40), width=3)
    d.text((540, h - 175), "origin", fill=(255, 255, 255), font=util.font(28, bold=True))
    y = 160
    for i, t in enumerate(notes, 1):
        d.text((1150, y), f"{i}. {t}", fill=(20, 20, 20), font=util.font(29))
        y += 60
    return img


def save_jpeg(img: Image.Image, path, quality=86) -> int:
    img.save(str(path), "JPEG", quality=quality, optimize=False, progressive=False, subsampling=2)
    return path.stat().st_size


def save_png(img: Image.Image, path) -> int:
    img.save(str(path), "PNG", optimize=False, compress_level=6)
    return path.stat().st_size

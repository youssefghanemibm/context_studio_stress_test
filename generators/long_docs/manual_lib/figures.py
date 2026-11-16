"""Pillow process diagrams with boxes, decision diamonds and labelled arrows.

Text is drawn large (font >= 26 px, cap height ~19 px) and black on white/pale fills so Apple
Vision OCR reads it reliably. Layout is a simple grid: each node has (col, row); edges are
straight or elbow connectors with an optional label on a white plate.
"""
from __future__ import annotations

import io
import math
import pathlib

from PIL import Image, ImageDraw

from generators.common import util

FILL = {"box": (232, 240, 250), "decision": (255, 244, 214), "end": (226, 244, 230), "ext": (240, 240, 240)}


def _wrap(draw, text, font, width):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=font) <= width or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def render(spec: dict, out_path: pathlib.Path) -> pathlib.Path:
    """spec = {title, cols, rows, nodes: {id: (col,row,text,kind)}, edges: [(a,b,label,route)], cell=(w,h)}"""
    cw, ch = spec.get("cell", (560, 270))
    cols, rows = spec["cols"], spec["rows"]
    margin_top = 110 if spec.get("title") else 40
    W = cols * cw + 80
    H = rows * ch + margin_top + 40
    img = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(img)
    f_title = util.font(34, bold=True)
    f_node = util.font(27)
    f_lab = util.font(26, bold=True)
    if spec.get("title"):
        d.text((40, 30), spec["title"], fill="black", font=f_title)
        d.line([(40, 85), (W - 40, 85)], fill=(60, 60, 60), width=3)
    boxes = {}
    bw, bh = int(cw * spec.get("box_w", 0.54)), int(ch * spec.get("box_h", 0.6))
    for nid, (c, r, text, kind) in spec["nodes"].items():
        cx = 40 + c * cw + cw // 2
        cy = margin_top + r * ch + ch // 2
        x0, y0, x1, y1 = cx - bw // 2, cy - bh // 2, cx + bw // 2, cy + bh // 2
        if kind == "decision":
            pts = [(cx, y0 - 14), (x1 + 16, cy), (cx, y1 + 14), (x0 - 16, cy)]
            d.polygon(pts, fill=FILL["decision"], outline=(40, 40, 40))
            d.line(pts + [pts[0]], fill=(40, 40, 40), width=3)
            maxw = bw - 70
        else:
            rad = 26 if kind == "end" else 10
            d.rounded_rectangle([x0, y0, x1, y1], radius=rad, fill=FILL.get(kind, FILL["box"]),
                                outline=(40, 40, 40), width=3)
            maxw = bw - 30
        lines = _wrap(d, text, f_node, maxw)
        lh = 33
        ty = cy - (len(lines) * lh) // 2
        for ln in lines:
            tw = d.textlength(ln, font=f_node)
            d.text((cx - tw / 2, ty), ln, fill="black", font=f_node)
            ty += lh
        boxes[nid] = (x0, y0, x1, y1, cx, cy)
    for edge in spec["edges"]:
        a, b, label = edge[0], edge[1], edge[2] if len(edge) > 2 else ""
        route = edge[3] if len(edge) > 3 else "auto"
        ax0, ay0, ax1, ay1, acx, acy = boxes[a]
        bx0, by0, bx1, by1, bcx, bcy = boxes[b]
        if route == "auto":
            route = "h" if abs(acy - bcy) < 5 else ("v" if abs(acx - bcx) < 5 else "hv")
        if route == "h":
            sx = ax1 + (16 if spec["nodes"][a][3] == "decision" else 0) if bcx > acx else ax0
            ex = bx0 - (16 if spec["nodes"][b][3] == "decision" else 0) if bcx > acx else bx1
            pts = [(sx, acy), (ex, bcy)]
        elif route == "v":
            sy = ay1 + (14 if spec["nodes"][a][3] == "decision" else 0) if bcy > acy else ay0
            ey = by0 - (14 if spec["nodes"][b][3] == "decision" else 0) if bcy > acy else by1
            pts = [(acx, sy), (bcx, ey)]
        elif route == "vh":   # down then across
            sy = ay1 + (14 if spec["nodes"][a][3] == "decision" else 0) if bcy > acy else ay0
            ex = bx0 if bcx > acx else bx1
            pts = [(acx, sy), (acx, bcy), (ex, bcy)]
        else:                 # hv: across then down/up
            sx = ax1 if bcx > acx else ax0
            ey = by0 if bcy > acy else by1
            pts = [(sx, acy), (bcx, acy), (bcx, ey)]
        d.line(pts, fill=(30, 30, 30), width=4)
        (px, py), (qx, qy) = pts[-2], pts[-1]
        ang = math.atan2(qy - py, qx - px)
        L = 22
        tip = [(qx, qy), (qx - L * math.cos(ang - 0.4), qy - L * math.sin(ang - 0.4)),
               (qx - L * math.cos(ang + 0.4), qy - L * math.sin(ang + 0.4))]
        d.polygon(tip, fill=(30, 30, 30))
        if label:
            # label on the longest segment
            segs = list(zip(pts[:-1], pts[1:]))
            (s0, s1) = max(segs, key=lambda s: abs(s[0][0] - s[1][0]) + abs(s[0][1] - s[1][1]))
            mx, my = (s0[0] + s1[0]) / 2, (s0[1] + s1[1]) / 2
            horiz = abs(s0[1] - s1[1]) < 2
            seg_len = abs(s0[0] - s1[0]) + abs(s0[1] - s1[1])
            maxw = max(120, seg_len - 40) if horiz else 420
            llines = []
            for part in label.split("\n"):
                llines += _wrap(d, part, f_lab, maxw)
            if horiz:
                my = my - 18 * len(llines) - 8
            tw = max(d.textlength(t, font=f_lab) for t in llines)
            th = 32 * len(llines)
            d.rectangle([mx - tw / 2 - 8, my - th / 2 - 6, mx + tw / 2 + 8, my + th / 2 + 4], fill="white",
                        outline=(120, 120, 120), width=2)
            yy = my - th / 2
            for t in llines:
                d.text((mx - d.textlength(t, font=f_lab) / 2, yy), t, fill="black", font=f_lab)
                yy += 32
    out_path = pathlib.Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, format="PNG", optimize=True)
    return out_path

"""Raster figures (PIL / matplotlib Agg). Text is drawn large and high-contrast for OCR."""
from __future__ import annotations

import math
import pathlib

from PIL import Image, ImageDraw

from .core import util

WHITE = (255, 255, 255)
BLACK = (20, 20, 20)
GREY = (90, 90, 90)
PALETTE = {
    "blue": (214, 228, 245), "green": (220, 239, 220), "amber": (252, 236, 205), "grey": (232, 232, 232),
    "purple": (230, 222, 243), "red": (248, 214, 214), "teal": (210, 236, 236), "white": (255, 255, 255),
}
EDGE = {"blue": (31, 56, 100), "green": (39, 94, 39), "amber": (150, 95, 10), "grey": (70, 70, 70),
        "purple": (80, 50, 120), "red": (150, 30, 30), "teal": (20, 100, 100), "white": (60, 60, 60)}


def _text_size(draw, text, font):
    l, t, r, b = draw.textbbox((0, 0), text, font=font)
    return r - l, b - t


def _wrap(draw, text, font, max_w):
    out = []
    for para in str(text).split("\n"):
        words, line = para.split(" "), ""
        for w in words:
            cand = (line + " " + w).strip()
            if _text_size(draw, cand, font)[0] <= max_w or not line:
                line = cand
            else:
                out.append(line)
                line = w
        out.append(line)
    return out


def _center_text(draw, box, text, font, fill=BLACK, line_gap=6):
    x0, y0, x1, y1 = box
    lines = _wrap(draw, text, font, (x1 - x0) - 24)
    hs = [_text_size(draw, ln or "Ag", font)[1] for ln in lines]
    total = sum(hs) + line_gap * (len(lines) - 1)
    y = y0 + ((y1 - y0) - total) / 2
    for ln, h in zip(lines, hs):
        w, _ = _text_size(draw, ln, font)
        draw.text((x0 + ((x1 - x0) - w) / 2, y - 2), ln, font=font, fill=fill)
        y += h + line_gap


def _clip(cx, cy, tx, ty, box):
    """Point where the segment from the box centre (cx, cy) towards (tx, ty) leaves the box."""
    x0, y0, x1, y1 = box
    dx, dy = tx - cx, ty - cy
    if dx == 0 and dy == 0:
        return cx, cy
    ts = []
    if dx:
        ts += [((x0 - cx) / dx), ((x1 - cx) / dx)]
    if dy:
        ts += [((y0 - cy) / dy), ((y1 - cy) / dy)]
    t = min(t for t in ts if t > 0)
    return cx + dx * t, cy + dy * t


def _arrow(draw, p0, p1, color=BLACK, width=4, head=22, dashed=False):
    x0, y0 = p0
    x1, y1 = p1
    if dashed:
        n = max(1, int(math.hypot(x1 - x0, y1 - y0) // 22))
        for i in range(0, n, 2):
            a = (x0 + (x1 - x0) * i / n, y0 + (y1 - y0) * i / n)
            b = (x0 + (x1 - x0) * min(i + 1, n) / n, y0 + (y1 - y0) * min(i + 1, n) / n)
            draw.line([a, b], fill=color, width=width)
    else:
        draw.line([p0, p1], fill=color, width=width)
    ang = math.atan2(y1 - y0, x1 - x0)
    pts = [(x1, y1),
           (x1 - head * math.cos(ang - 0.4), y1 - head * math.sin(ang - 0.4)),
           (x1 - head * math.cos(ang + 0.4), y1 - head * math.sin(ang + 0.4))]
    draw.polygon(pts, fill=color)


def _draw_boxes(dr, boxes, arrows, font_size=30, label_size=27):
    f_box = util.font(font_size, bold=True)
    f_lab = util.font(label_size)
    geo = {}
    for b in boxes:
        x, y, w, h = b["x"], b["y"], b["w"], b["h"]
        col = b.get("color", "blue")
        dr.rounded_rectangle([x, y, x + w, y + h], radius=14, outline=EDGE[col], width=4, fill=PALETTE[col])
        _center_text(dr, (x, y, x + w, y + h), b["label"], f_box)
        geo[b["id"]] = (x, y, x + w, y + h)
    for a in arrows:
        s, t = geo[a["src"]], geo[a["dst"]]
        sc = ((s[0] + s[2]) / 2 + a.get("sx", 0), (s[1] + s[3]) / 2 + a.get("sy", 0))
        tc = ((t[0] + t[2]) / 2 + a.get("tx", 0), (t[1] + t[3]) / 2 + a.get("ty", 0))
        p0 = _clip(sc[0], sc[1], tc[0], tc[1], s)
        p1 = _clip(tc[0], tc[1], sc[0], sc[1], t)
        _arrow(dr, p0, p1, dashed=a.get("dashed", False))
        if a.get("label"):
            mx, my = (p0[0] + p1[0]) / 2 + a.get("lx", 0), (p0[1] + p1[1]) / 2 + a.get("ly", 0)
            lines = _wrap(dr, a["label"], f_lab, a.get("lw", 420))
            lw = max(_text_size(dr, ln, f_lab)[0] for ln in lines) + 16
            lh = sum(_text_size(dr, ln or "Ag", f_lab)[1] + 6 for ln in lines) + 10
            dr.rectangle([mx - lw / 2, my - lh / 2, mx + lw / 2, my + lh / 2], fill=WHITE, outline=(170, 170, 170))
            yy = my - lh / 2 + 5
            for ln in lines:
                w, h = _text_size(dr, ln, f_lab)
                dr.text((mx - w / 2, yy - 2), ln, font=f_lab, fill=BLACK)
                yy += h + 6


def box_diagram(path, *, title: str, boxes: list[dict], arrows: list[dict], size=(2000, 1250),
                groups: list[dict] | None = None, footer: str | None = None, font_size: int = 30,
                label_size: int = 27) -> pathlib.Path:
    """boxes: {id, label, x, y, w, h, color}; arrows: {src, dst, label, dashed}; groups: {label, x, y, w, h}."""
    img = Image.new("RGB", size, WHITE)
    dr = ImageDraw.Draw(img)
    f_title = util.font(40, bold=True)
    f_grp = util.font(28, bold=True)
    dr.text((40, 26), title, font=f_title, fill=BLACK)
    dr.line([(40, 84), (size[0] - 40, 84)], fill=GREY, width=2)
    for g in groups or []:
        x, y, w, h = g["x"], g["y"], g["w"], g["h"]
        dr.rounded_rectangle([x, y, x + w, y + h], radius=18, outline=(120, 120, 120), width=3,
                             fill=(248, 248, 248))
        dr.text((x + 16, y + 10), g["label"], font=f_grp, fill=(60, 60, 60))
    _draw_boxes(dr, boxes, arrows, font_size, label_size)
    if footer:
        dr.text((40, size[1] - 50), footer, font=util.font(24), fill=GREY)
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, "PNG", optimize=True)
    return path


def lane_diagram(path, *, title: str, lanes: list[str], steps: list[dict], arrows: list[dict],
                 size=(2000, 1200), font_size: int = 28, label_size: int = 25) -> pathlib.Path:
    """Swimlanes: steps {id, lane (index), col, label, color}."""
    n = len(lanes)
    top, left = 110, 300
    lane_h = (size[1] - top - 40) // n
    img_w = size[0]
    cols = max(s["col"] for s in steps) + 1
    col_w = (img_w - left - 40) // cols
    img = Image.new("RGB", size, WHITE)
    dr = ImageDraw.Draw(img)
    dr.text((40, 26), title, font=util.font(40, bold=True), fill=BLACK)
    f_lane = util.font(28, bold=True)
    for i, ln in enumerate(lanes):
        y = top + i * lane_h
        dr.rectangle([40, y, img_w - 40, y + lane_h], outline=(150, 150, 150), width=2,
                     fill=(250, 250, 250) if i % 2 else (243, 246, 250))
        dr.rectangle([40, y, left - 10, y + lane_h], fill=(225, 230, 238), outline=(150, 150, 150), width=2)
        _center_text(dr, (40, y, left - 10, y + lane_h), ln, f_lane)
    boxes = []
    for s in steps:
        x = left + s["col"] * col_w + 24
        y = top + s["lane"] * lane_h + 22
        boxes.append({"id": s["id"], "label": s["label"], "x": x, "y": y, "w": col_w - 48,
                      "h": lane_h - 44, "color": s.get("color", "blue")})
    _draw_boxes(dr, boxes, arrows, font_size, label_size)
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, "PNG", optimize=True)
    return path


def bar_chart(path, *, title: str, categories, series: dict, ylabel: str = "", size=(10, 5.2),
              value_labels: bool = True, fmt: str = "{:,.0f}") -> pathlib.Path:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib import font_manager
    font_manager.fontManager.addfont(util.font_path())
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 15, "svg.hashsalt": "x"})
    fig, ax = plt.subplots(figsize=size, dpi=170)
    n = len(series)
    width = 0.8 / max(n, 1)
    colours = ["#1F3864", "#7FA7D9", "#C0504D", "#9BBB59", "#F79646"]
    xs = list(range(len(categories)))
    for i, (name, vals) in enumerate(series.items()):
        pos = [x - 0.4 + width / 2 + i * width for x in xs]
        bars = ax.bar(pos, vals, width=width * 0.92, label=name, color=colours[i % len(colours)])
        if value_labels:
            for b, v in zip(bars, vals):
                ax.annotate(fmt.format(v), (b.get_x() + b.get_width() / 2, b.get_height()),
                            ha="center", va="bottom", fontsize=14, xytext=(0, 3), textcoords="offset points")
    ax.set_xticks(xs)
    ax.set_xticklabels(categories, fontsize=15)
    ax.set_title(title, fontsize=19, fontweight="bold", loc="left")
    if ylabel:
        ax.set_ylabel(ylabel, fontsize=15)
    ax.spines[["top", "right"]].set_visible(False)
    if n > 1:
        ax.legend(frameon=False, fontsize=14)
    fig.tight_layout()
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, format="png", metadata={"Software": None})
    plt.close(fig)
    return path


def matrix_image(path, *, title: str, header: list[str], rows: list[list[str]], col_w: list[int],
                 colours: dict | None = None, font_size: int = 28) -> pathlib.Path:
    """A table rendered as an image (for image_table facts and dashboard tiles)."""
    f = util.font(font_size)
    fb = util.font(font_size, bold=True)
    ft = util.font(36, bold=True)
    row_h = int(font_size * 2.1)
    w = sum(col_w) + 80
    h = 130 + row_h * (len(rows) + 1) + 40
    img = Image.new("RGB", (w, h), WHITE)
    dr = ImageDraw.Draw(img)
    dr.text((40, 30), title, font=ft, fill=BLACK)
    y = 110
    x = 40
    for c, txt in enumerate(header):
        dr.rectangle([x, y, x + col_w[c], y + row_h], fill=(31, 56, 100), outline=(31, 56, 100))
        dr.text((x + 12, y + (row_h - font_size) / 2 - 2), txt, font=fb, fill=WHITE)
        x += col_w[c]
    for r, row in enumerate(rows):
        y += row_h
        x = 40
        for c, txt in enumerate(row):
            fill = (colours or {}).get(str(txt).strip(), (255, 255, 255) if r % 2 == 0 else (242, 242, 242))
            dr.rectangle([x, y, x + col_w[c], y + row_h], fill=fill, outline=(180, 180, 180))
            dr.text((x + 12, y + (row_h - font_size) / 2 - 2), str(txt), font=f, fill=BLACK)
            x += col_w[c]
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, "PNG", optimize=True)
    return path

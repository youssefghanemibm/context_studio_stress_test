"""Higher-level raster diagrams built on Canvas.

Diagram      nodes with explicit boxes, edges routed side-to-side (straight or elbow), labels
ERD          entity boxes with column rows, PK/FK markers, crow's-foot relationships
Swimlane     horizontal lanes with tasks, decisions, start/end events and labelled flows
org_chart    top-down chart: level-1 columns, deeper levels stacked and indented
table_image  a table rendered as pixels (header fill, zebra rows, wrapped cells)
roadmap      date axis with workstream lanes, bars and milestone diamonds
"""
from __future__ import annotations

import datetime as dt
import math
from typing import Sequence

from .core import (AMBER, AMBER_L, BLUE_L, GREY_L, GREY_M, GRID, INK, INK2, LINE, MUTED, NAVY, NAVY2,
                   RED, STYLES, TEAL, TEAL_L, WHITE, Canvas)


# ==========================================================================================
# Node / edge diagrams
# ==========================================================================================
class Diagram(Canvas):
    def __init__(self, w: int, h: int, bg: str = WHITE):
        super().__init__(w, h, bg)
        self.nodes: dict[str, tuple] = {}
        self._pending: list[tuple] = []

    def flush_labels(self) -> None:
        """Edge labels are drawn last so later edges never paint over them."""
        for args, kw in self._pending:
            self.label(*args, **kw)
        self._pending = []

    def png_bytes(self) -> bytes:
        self.flush_labels()
        return super().png_bytes()

    def node(self, nid: str, box, text: str, style: str = "plain", size: int = 26, shape: str = "box",
             bold_first: bool = True, radius: int = 14, width: int = 3, align: str = "center",
             min_size: int = 18, dash=None) -> tuple:
        fill, outline, tcol = STYLES.get(style, STYLES["plain"])
        x0, y0, x1, y1 = box
        tb = box
        if shape == "box":
            self.rect(box, fill=fill, outline=outline, width=width, radius=radius, dash=dash)
        elif shape == "db":
            self.cylinder(box, fill=fill, outline=outline, width=width)
            eh = max(14, int((x1 - x0) * 0.16))
            tb = (x0, y0 + eh, x1, y1 - eh / 2)
        elif shape == "cloud":
            self.cloud(box, fill=fill, outline=outline, width=width)
            tb = (x0 + (x1 - x0) * 0.12, y0 + (y1 - y0) * 0.22, x1 - (x1 - x0) * 0.12, y1 - (y1 - y0) * 0.08)
        elif shape == "diamond":
            self.diamond(box, fill=fill, outline=outline, width=width)
            tb = (x0 + (x1 - x0) * 0.17, y0 + (y1 - y0) * 0.2, x1 - (x1 - x0) * 0.17, y1 - (y1 - y0) * 0.2)
        elif shape == "ellipse":
            self.ellipse(box, fill=fill, outline=outline, width=width)
            tb = (x0 + (x1 - x0) * 0.1, y0, x1 - (x1 - x0) * 0.1, y1)
        elif shape == "queue":
            self.rect(box, fill=fill, outline=outline, width=width, radius=6)
            for k in range(1, 4):
                xx = x1 - k * 16
                self.d.line([(xx, y0 + 6), (xx, y1 - 6)], fill=outline, width=2)
            tb = (x0, y0, x1 - 52, y1)
        elif shape == "doc":
            self.rect(box, fill=fill, outline=outline, width=width)
            self.d.polygon([(x1 - 28, y0), (x1, y0 + 28), (x1 - 28, y0 + 28)], fill=outline)
        elif shape == "circle":
            self.ellipse(box, fill=fill, outline=outline, width=width)
        if text:
            self.text_in_box(tb, text, size, fill=tcol, first_bold=bold_first, align=align, min_size=min_size,
                             pad=10 if shape in ("box", "queue", "doc") else 4)
        self.nodes[nid] = tuple(box)
        return box

    # anchor point on a side of a node box ('l','r','t','b'), with optional offset along the side
    def anchor(self, nid: str, side: str, off: float = 0.0) -> tuple[float, float]:
        x0, y0, x1, y1 = self.nodes[nid]
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        if side == "l":
            return (x0, cy + off)
        if side == "r":
            return (x1, cy + off)
        if side == "t":
            return (cx + off, y0)
        return (cx + off, y1)

    def _auto_sides(self, a: str, b: str) -> tuple[str, str]:
        ax0, ay0, ax1, ay1 = self.nodes[a]
        bx0, by0, bx1, by1 = self.nodes[b]
        if bx0 >= ax1:
            return ("r", "l")
        if bx1 <= ax0:
            return ("l", "r")
        if by0 >= ay1:
            return ("b", "t")
        return ("t", "b")

    def edge(self, a: str, b: str, label: str | None = None, sides: str | None = None, via=None,
             dash=None, both: bool = False, color: str = LINE, width: int = 4, label_size: int = 22,
             label_at: float | None = None, label_off=(0, 0), aoff: float = 0.0, boff: float = 0.0,
             label_bg: str = WHITE, label_outline: str | None = None, label_bold: bool = False,
             label_max_w: int | None = None, head: bool = True, mid: float = 0.5, label_xy=None) -> list:
        sa, sb = (sides[0], sides[1]) if sides else self._auto_sides(a, b)
        p0, p1 = self.anchor(a, sa, aoff), self.anchor(b, sb, boff)
        if via:
            pts = [p0] + [tuple(v) for v in via] + [p1]
        elif sa in "lr" and sb in "lr":
            if abs(p0[1] - p1[1]) < 2:
                pts = [p0, p1]
            else:
                mx = p0[0] + (p1[0] - p0[0]) * mid
                pts = [p0, (mx, p0[1]), (mx, p1[1]), p1]
        elif sa in "tb" and sb in "tb":
            if abs(p0[0] - p1[0]) < 2:
                pts = [p0, p1]
            else:
                my = p0[1] + (p1[1] - p0[1]) * mid
                pts = [p0, (p0[0], my), (p1[0], my), p1]
        elif sa in "lr":
            pts = [p0, (p1[0], p0[1]), p1]
        else:
            pts = [p0, (p0[0], p1[1]), p1]
        self.arrow(pts, fill=color, width=width, head_end=head, head_start=both, dash=dash)
        if label:
            if label_xy is not None:
                cx, cy = label_xy
            elif label_at is None:
                # midpoint of the longest segment
                segs = list(zip(pts, pts[1:]))
                (q0, q1) = max(segs, key=lambda s: math.hypot(s[1][0] - s[0][0], s[1][1] - s[0][1]))
                cx, cy = (q0[0] + q1[0]) / 2, (q0[1] + q1[1]) / 2
            else:
                cx, cy = _point_along(pts, label_at)
            self._pending.append(((cx + label_off[0], cy + label_off[1], label, label_size),
                                  dict(bg=label_bg, outline=label_outline, bold=label_bold, max_w=label_max_w)))
        return pts

    def edge_straight(self, a: str, b: str, label: str | None = None, color: str = LINE, width: int = 3,
                      label_size: int = 21, label_t: float = 0.5, both: bool = False, dash=None,
                      label_max_w: int | None = None, label_outline: str | None = None) -> None:
        """Centre-to-centre straight arrow clipped at both node borders."""
        pa, pb = _clip_center_line(self.nodes[a], self.nodes[b]), _clip_center_line(self.nodes[b], self.nodes[a])
        self.arrow([pa, pb], fill=color, width=width, head_start=both, dash=dash)
        if label:
            cx, cy = pa[0] + (pb[0] - pa[0]) * label_t, pa[1] + (pb[1] - pa[1]) * label_t
            self._pending.append(((cx, cy, label, label_size), dict(outline=label_outline or GRID,
                                                                     max_w=label_max_w)))

    def zone(self, box, title: str, fill: str = GREY_L, outline: str = LINE, size: int = 26,
             dash=(14, 8), title_fill: str | None = None) -> None:
        self.rect(box, fill=fill, outline=outline, width=3, radius=18, dash=dash)
        x0, y0 = box[0], box[1]
        tw = self.twidth(title, size, True)
        tf = title_fill or outline
        self.rect((x0 + 22, y0 - size * 0.8, x0 + 44 + tw, y0 + size * 0.8), fill=tf, outline=tf, radius=8)
        self.text(x0 + 33, y0, title, size, True, fill=WHITE, anchor="lm")


def _clip_center_line(box_from, box_to):
    """Point where the line from the centre of box_from to the centre of box_to leaves box_from."""
    x0, y0, x1, y1 = box_from
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    tx = (box_to[0] + box_to[2]) / 2
    ty = (box_to[1] + box_to[3]) / 2
    dx, dy = tx - cx, ty - cy
    if dx == 0 and dy == 0:
        return (cx, cy)
    hw, hh = (x1 - x0) / 2, (y1 - y0) / 2
    t = min(hw / abs(dx) if dx else 1e9, hh / abs(dy) if dy else 1e9)
    return (cx + dx * t, cy + dy * t)


def _point_along(pts, t: float):
    lens = [math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts, pts[1:])]
    total = sum(lens) or 1
    target = total * t
    for (a, b), L in zip(zip(pts, pts[1:]), lens):
        if target <= L and L > 0:
            f = target / L
            return (a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f)
        target -= L
    return pts[-1]


# ==========================================================================================
# ERD
# ==========================================================================================
class ERD(Diagram):
    ROW = 40
    HEAD = 62

    def __init__(self, w: int, h: int, bg: str = WHITE):
        super().__init__(w, h, bg)
        self.rows: dict[tuple[str, str], float] = {}

    def entity(self, eid: str, x: int, y: int, name: str, columns: Sequence[tuple], width: int = 560,
               head_fill: str = NAVY2, body_fill: str = WHITE, size: int = 23, subtitle: str = "",
               type_col: int | None = None) -> tuple:
        """columns: (name, type, flags) where flags is e.g. 'PK', 'FK', 'PK,FK', 'NN' or ''."""
        rh = self.ROW
        hh = self.HEAD + (30 if subtitle else 0)
        h = hh + rh * len(columns) + 14
        box = (x, y, x + width, y + h)
        self.rect(box, fill=body_fill, outline=head_fill, width=3, radius=10)
        self.rect((x, y, x + width, y + hh), fill=head_fill, outline=head_fill, width=1, radius=10)
        self.rect((x, y + hh - 12, x + width, y + hh), fill=head_fill, outline=head_fill, width=1)
        self.text(x + 16, y + 14, name, size + 3, True, fill=WHITE)
        if subtitle:
            self.text(x + 16, y + 14 + size + 12, subtitle, size - 4, fill="#DCE6F2")
        tc = type_col if type_col is not None else int(width * 0.58)
        for i, col in enumerate(columns):
            cname, ctype, flags = (list(col) + ["", ""])[:3]
            ry = y + hh + 7 + i * rh
            if i % 2 == 1:
                self.rect((x + 3, ry, x + width - 3, ry + rh), fill=GREY_L, outline=GREY_L, width=1)
            fl = (flags or "").upper()
            key = "PK" if "PK" in fl else ("FK" if "FK" in fl else "")
            if key:
                kcol = AMBER if key == "PK" else TEAL
                self.text(x + 12, ry + rh / 2, key, size - 5, True, fill=kcol, anchor="lm")
            bold = "PK" in fl
            self.text(x + 62, ry + rh / 2, cname, size - 1, bold, fill=INK, anchor="lm")
            self.text(x + tc, ry + rh / 2, ctype, size - 3, fill=INK2, anchor="lm")
            if "FK" in fl and "PK" in fl:
                self.text(x + width - 12, ry + rh / 2, "FK", size - 5, True, fill=TEAL, anchor="rm")
            self.rows[(eid, cname)] = ry + rh / 2
        self.nodes[eid] = box
        return box

    def relation(self, child: str, child_col: str, parent: str, parent_col: str, label: str | None = None,
                 sides: str | None = None, color: str = NAVY2, label_size: int = 21, mid: float = 0.5,
                 label_off=(0, 0), via=None, label_max_w: int | None = None, route_y: float | None = None) -> None:
        cx0, cy0, cx1, cy1 = self.nodes[child]
        px0, py0, px1, py1 = self.nodes[parent]
        cyr = self.rows.get((child, child_col), (cy0 + cy1) / 2)
        pyr = self.rows.get((parent, parent_col), (py0 + py1) / 2)
        if sides:
            sc, sp = sides[0], sides[1]
        else:
            sc, sp = ("r", "l") if px0 >= cx1 else (("l", "r") if px1 <= cx0 else ("r", "r"))
        p0 = (cx1 if sc == "r" else cx0, cyr)
        p1 = (px1 if sp == "r" else px0, pyr)
        if route_y is not None:
            dx0 = 60 if sc == "r" else -60
            dx1 = 60 if sp == "r" else -60
            pts = [p0, (p0[0] + dx0, p0[1]), (p0[0] + dx0, route_y), (p1[0] + dx1, route_y), (p1[0] + dx1, p1[1]), p1]
        elif via:
            pts = [p0] + [tuple(v) for v in via] + [p1]
        elif sc == sp:
            ext = max(p0[0], p1[0]) + 60 if sc == "r" else min(p0[0], p1[0]) - 60
            pts = [p0, (ext, p0[1]), (ext, p1[1]), p1]
        else:
            mx = p0[0] + (p1[0] - p0[0]) * mid
            pts = [p0, (mx, p0[1]), (mx, p1[1]), p1]
        self.polyline(pts, fill=color, width=3)
        # crow's foot at the child (many) end, double bar at the parent (one) end
        self._crow(pts[0], pts[1], color)
        self._bar(pts[-1], pts[-2], color)
        if label:
            segs = list(zip(pts, pts[1:]))
            (q0, q1) = max(segs, key=lambda s: math.hypot(s[1][0] - s[0][0], s[1][1] - s[0][1]))
            self._pending.append((((q0[0] + q1[0]) / 2 + label_off[0], (q0[1] + q1[1]) / 2 + label_off[1], label,
                                   label_size), dict(outline=GRID, max_w=label_max_w)))

    def _crow(self, end, nxt, color):
        ex, ey = end
        nx, ny = nxt
        ang = math.atan2(ny - ey, nx - ex)
        base = (ex + 26 * math.cos(ang), ey + 26 * math.sin(ang))
        for da in (-0.5, 0, 0.5):
            a = ang + math.pi + da
            self.d.line([base, (base[0] + 30 * math.cos(a), base[1] + 30 * math.sin(a))], fill=color, width=3)
        perp = ang + math.pi / 2
        bx, by = ex + 40 * math.cos(ang), ey + 40 * math.sin(ang)
        self.d.line([(bx + 12 * math.cos(perp), by + 12 * math.sin(perp)),
                     (bx - 12 * math.cos(perp), by - 12 * math.sin(perp))], fill=color, width=3)

    def _bar(self, end, nxt, color):
        ex, ey = end
        nx, ny = nxt
        ang = math.atan2(ny - ey, nx - ex)
        perp = ang + math.pi / 2
        for dd in (14, 26):
            bx, by = ex + dd * math.cos(ang), ey + dd * math.sin(ang)
            self.d.line([(bx + 13 * math.cos(perp), by + 13 * math.sin(perp)),
                         (bx - 13 * math.cos(perp), by - 13 * math.sin(perp))], fill=color, width=3)


# ==========================================================================================
# Swimlanes
# ==========================================================================================
class Swimlane(Diagram):
    def __init__(self, w: int, lanes: Sequence[str], lane_h: int = 230, top: int = 130, left: int = 290,
                 title: str = "", subtitle: str = "", lane_size: int = 25, bottom: int = 70,
                 lane_fills: Sequence[str] | None = None, right_note: str = ""):
        h = top + lane_h * len(lanes) + bottom
        super().__init__(w, h)
        self.top, self.left, self.lane_h, self.lanes = top, left, lane_h, list(lanes)
        self.cw = 300.0
        if title:
            self.title_band(title, subtitle, h=top - 20, size=38, sub_size=24, right=right_note)
        fills = lane_fills or [WHITE, "#F6F8FB"]
        for i, ln in enumerate(lanes):
            y0 = top + i * lane_h
            self.rect((left, y0, w - 20, y0 + lane_h), fill=fills[i % len(fills)], outline=GRID, width=2)
            self.rect((20, y0, left, y0 + lane_h), fill="#E8EEF6", outline=GRID, width=2)
            self.text_in_box((20, y0, left, y0 + lane_h), ln, lane_size, bold=True, fill=NAVY, pad=14)

    def lane_y(self, lane: int) -> float:
        return self.top + lane * self.lane_h + self.lane_h / 2

    def col_x(self, col: float, col_w: float | None = None, start: int | None = None) -> float:
        s = start if start is not None else self.left + 30
        cw = col_w or self.cw
        return s + col * cw + cw / 2

    def fit_cols(self, max_col: float) -> float:
        """Set the column width so that columns 0..max_col fit inside the lanes."""
        self.cw = (self.w - self.left - 50) / (max_col + 1)
        return self.cw

    def step(self, sid: str, lane: int, col: float, text: str, kind: str = "task", col_w: float | None = None,
             w: int | None = None, h: int = 128, style: str | None = None, size: int = 23, start: int | None = None,
             dy: float = 0) -> tuple:
        cw = col_w or self.cw
        if w is None:
            w = int(min(250, cw - 34))
        cx, cy = self.col_x(col, cw, start), self.lane_y(lane) + dy
        if kind == "decision":
            dw, dh = min(w + 30, cw - 10), h + 56
            box = (cx - dw / 2, cy - dh / 2, cx + dw / 2, cy + dh / 2)
            return self.node(sid, box, text, style or "warn", size=size - 1, shape="diamond", bold_first=False)
        if kind in ("start", "end"):
            r = 34
            box = (cx - r, cy - r, cx + r, cy + r)
            st = style or ("platform" if kind == "start" else "alert")
            self.node(sid, box, "", st, shape="circle", width=6 if kind == "end" else 3)
            if text:
                self.text(cx, cy + r + 10, text, size - 3, fill=INK2, anchor="ma")
            return box
        box = (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)
        shape = "doc" if kind == "doc" else ("db" if kind == "system" else "box")
        return self.node(sid, box, text, style or ("service" if kind == "system" else "target"), size=size,
                         shape=shape, bold_first=False)


# ==========================================================================================
# Org chart
# ==========================================================================================
def org_chart(title: str, subtitle: str, root: dict, columns: Sequence[dict], col_w: int = 470,
              card_h: int = 118, size: int = 23, above: dict | None = None, footer: str = "",
              right_note: str = "", gap_y: int = 34, indent: int = 46, legend: Sequence | None = None,
              col_gap: int = 30, highlight: set | None = None) -> Canvas:
    """root/columns entries: {'name','title','note'(opt),'style'(opt),'children':[...]}.

    Level-1 entries are laid out as columns; each column's descendants are stacked below it,
    indented per level, with elbow connectors. `above` is an optional box drawn above the root
    (the person the root reports to).
    """
    highlight = highlight or set()

    def count(n):
        return 1 + sum(count(c) for c in n.get("children", []))

    depth_rows = max(count(c) for c in columns) if columns else 1
    ncol = len(columns)
    W = max(1800, 60 + ncol * (col_w + col_gap))
    top = 150
    root_y = top + (card_h + 70 if above else 0) + 30
    lvl1_y = root_y + card_h + 110
    H = lvl1_y + depth_rows * (card_h + gap_y) + 120 + (80 if footer else 0) + (130 if legend else 0)
    cv = Diagram(W, H)
    cv.title_band(title, subtitle, h=120, size=40, sub_size=24, right=right_note)

    def card(box, n, emph=False):
        st = n.get("style", "target")
        fill, outline, tcol = STYLES[st]
        cv.rect(box, fill=fill, outline=outline, width=5 if emph else 3, radius=12)
        lines = [x for x in [n["name"], n["title"]] + ([n["note"]] if n.get("note") else []) if x]
        cv.text_in_box(box, "\n".join(lines), size, fill=tcol, first_bold=True, min_size=17, pad=10)

    cw = col_w - 20
    rx = W / 2
    if above:
        ab = (rx - cw / 2, top + 10, rx + cw / 2, top + 10 + card_h)
        card(ab, above)
        cv.polyline([(rx, ab[3]), (rx, root_y)], fill=LINE, width=3)
    rb = (rx - cw / 2, root_y, rx + cw / 2, root_y + card_h)
    card(rb, root, emph=True)
    # bus line
    bus_y = root_y + card_h + 55
    xs = [40 + i * (col_w + col_gap) + col_w / 2 for i in range(ncol)]
    offset = (W - (xs[-1] - xs[0] if xs else 0)) / 2 - (xs[0] if xs else 0)
    xs = [x + offset for x in xs]
    cv.polyline([(rx, rb[3]), (rx, bus_y)], fill=LINE, width=3)
    if xs:
        cv.polyline([(min(xs), bus_y), (max(xs), bus_y)], fill=LINE, width=3)

    def place(n, x_left, y, level):
        box = (x_left, y, x_left + cw - level * indent, y + card_h)
        card(box, n, emph=n.get("name") in highlight)
        cur_y = y + card_h + gap_y
        for ch in n.get("children", []):
            cx_left = x_left + indent
            # connector: vertical from parent's left edge region, then horizontal into child
            px = x_left + 22
            cv.polyline([(px, box[3]), (px, cur_y + card_h / 2), (cx_left, cur_y + card_h / 2)], fill=LINE, width=3)
            cur_y = place(ch, cx_left, cur_y, level + 1)
        return cur_y

    for x, n in zip(xs, columns):
        cv.polyline([(x, bus_y), (x, lvl1_y)], fill=LINE, width=3)
        place(n, x - cw / 2, lvl1_y, 0)
    if legend:
        cv.legend(40, H - (80 if footer else 0) - 130, legend, size=21, cols=len(legend), col_w=420, title="Key")
    if footer:
        cv.footer_band(footer, "", h=60, size=21)
    return cv


# ==========================================================================================
# Tables as images
# ==========================================================================================
def table_image(headers: Sequence[str], rows: Sequence[Sequence[str]], col_widths: Sequence[int],
                title: str = "", size: int = 22, head_fill: str = NAVY2, zebra: str = "#F4F6F9",
                pad: int = 12, note: str = "", title_size: int = 30, bold_first_col: bool = False,
                row_fills: dict | None = None, line_gap: float = 0.25) -> Canvas:
    W = sum(col_widths) + 60
    probe = Canvas(10, 10)
    lh = int(size * (1 + line_gap))

    def cell_lines(txt, cw, bold=False):
        return probe.wrap(str(txt), size, cw - 2 * pad, bold)

    head_lines = [cell_lines(h, cw, True) for h, cw in zip(headers, col_widths)]
    head_h = max(len(l) for l in head_lines) * lh + 2 * pad
    row_lines = [[cell_lines(c, cw, bold_first_col and j == 0) for j, (c, cw) in enumerate(zip(r, col_widths))]
                 for r in rows]
    row_hs = [max(len(l) for l in rl) * lh + 2 * pad for rl in row_lines]
    top = 30 + (int(title_size * 1.8) if title else 0)
    H = top + head_h + sum(row_hs) + 40 + (int(size * 2.2) if note else 0)
    cv = Canvas(W, H)
    if title:
        cv.text(30, 24, title, title_size, True, fill=NAVY)
    x0 = 30
    y = top
    cv.rect((x0, y, x0 + sum(col_widths), y + head_h), fill=head_fill, outline=head_fill, width=1)
    x = x0
    for lines, cw in zip(head_lines, col_widths):
        cv.lines_block(x + pad, y + pad, lines, size, bold=True, fill=WHITE, gap=line_gap)
        x += cw
    y += head_h
    for i, (rl, rh) in enumerate(zip(row_lines, row_hs)):
        fill = (row_fills or {}).get(i) or (zebra if i % 2 == 1 else WHITE)
        cv.rect((x0, y, x0 + sum(col_widths), y + rh), fill=fill, outline=GRID, width=1)
        x = x0
        for j, (lines, cw) in enumerate(zip(rl, col_widths)):
            cv.lines_block(x + pad, y + pad, lines, size, bold=bold_first_col and j == 0, fill=INK, gap=line_gap)
            x += cw
        y += rh
    x = x0
    for cw in col_widths[:-1]:
        x += cw
        cv.d.line([(x, top), (x, y)], fill=GRID, width=1)
    cv.rect((x0, top, x0 + sum(col_widths), y), fill=None, outline=LINE, width=2)
    if note:
        cv.text(30, y + 16, note, size - 2, fill=MUTED)
    return cv


# ==========================================================================================
# Roadmap / timeline
# ==========================================================================================
def _d(s) -> dt.date:
    return dt.date.fromisoformat(str(s)[:10])


class Timeline(Canvas):
    """Date axis between start and end with lanes. x(date) maps linearly."""

    def __init__(self, w: int, h: int, start: str, end: str, left: int = 330, right: int = 60, top: int = 220,
                 axis_size: int = 22, quarters: bool = True, title: str = "", subtitle: str = "",
                 right_note: str = ""):
        super().__init__(w, h)
        self.start, self.end = _d(start), _d(end)
        self.left, self.right, self.top = left, right, top
        if title:
            self.title_band(title, subtitle, h=130, size=40, sub_size=24, right=right_note)
        # axis with quarter ticks
        y = top - 50
        self.rect((left, y - 34, w - right, y + 10), fill=GREY_L, outline=GRID, width=1)
        d = dt.date(self.start.year, ((self.start.month - 1) // 3) * 3 + 1, 1)
        while d <= self.end:
            x = self.x(d)
            if x >= left:
                self.d.line([(x, y - 34), (x, h - 40)], fill=GRID, width=1)
                q = (d.month - 1) // 3 + 1
                lab = f"Q{q} {d.year}" if quarters else d.strftime("%b %Y")
                self.text(x + 8, y - 12, lab, axis_size, fill=INK2, anchor="lm")
            m = d.month + 3
            d = dt.date(d.year + (m - 1) // 12, (m - 1) % 12 + 1, 1)
        self.lane_rows: list[tuple[float, float]] = []

    def x(self, d) -> float:
        d = _d(d)
        span = (self.end - self.start).days or 1
        return self.left + (self.w - self.left - self.right) * (d - self.start).days / span

    def lane(self, y0: float, y1: float, name: str, fill: str = "#F7F9FC", size: int = 24) -> None:
        self.rect((20, y0, self.w - self.right, y1), fill=fill, outline=GRID, width=1)
        self.text_in_box((24, y0, self.left - 10, y1), name, size, bold=True, fill=NAVY, align="left")

    def bar(self, start, end, y: float, label: str, style: str = "target", h: int = 54, size: int = 22,
            label_inside: bool = True) -> tuple:
        fill, outline, tcol = STYLES[style]
        x0, x1 = self.x(start), self.x(end)
        box = (x0, y - h / 2, x1, y + h / 2)
        self.rect(box, fill=fill, outline=outline, width=3, radius=10)
        if label_inside and self.twidth(label, size, True) < (x1 - x0) - 16:
            self.text((x0 + x1) / 2, y, label, size, True, fill=tcol, anchor="mm")
        else:
            self.text(x1 + 12, y, label, size, True, fill=INK, anchor="lm")
        return box

    def milestone(self, date, y: float, label: str, color: str = NAVY, size: int = 22, above: bool = True,
                  r: int = 18, dx: float = 0, align: str = "m") -> None:
        x = self.x(date)
        self.d.polygon([(x, y - r), (x + r, y), (x, y + r), (x - r, y)], fill=color)
        ly = y - r - 10 if above else y + r + 10
        anchor = (align + ("d" if above else "a"))
        for i, ln in enumerate(label.split("\n") if above else label.split("\n")):
            pass
        lines = label.split("\n")
        lh = int(size * 1.25)
        if above:
            for i, ln in enumerate(reversed(lines)):
                self.text(x + dx, ly - i * lh, ln, size, i == len(lines) - 1, fill=INK, anchor=align + "s")
        else:
            for i, ln in enumerate(lines):
                self.text(x + dx, ly + i * lh, ln, size, i == 0, fill=INK, anchor=align + "a")

    def today_line(self, date, label: str, color: str = RED, size: int = 21) -> None:
        x = self.x(date)
        self.polyline([(x, self.top - 40), (x, self.h - 40)], fill=color, width=3, dash=(12, 8))
        self.label(x, self.top - 20, label, size, fill=WHITE, bg=color)


# ==========================================================================================
# Schematic map (equirectangular with cos(lat) scaling)
# ==========================================================================================
GB = [(-5.7, 50.0), (-4.2, 50.4), (-3.0, 50.7), (-1.0, 50.7), (1.4, 51.2), (1.7, 52.6), (0.3, 53.4), (-0.2, 54.0),
      (-1.2, 54.6), (-1.6, 55.6), (-2.1, 56.0), (-2.6, 56.3), (-1.8, 57.6), (-3.2, 58.6), (-5.0, 58.6),
      (-5.8, 57.8), (-5.6, 56.5), (-6.2, 56.3), (-5.4, 55.5), (-4.9, 54.8), (-3.4, 54.9), (-3.1, 54.2),
      (-3.0, 53.4), (-4.6, 53.3), (-4.2, 52.8), (-4.1, 52.3), (-5.2, 51.8), (-4.0, 51.6), (-3.0, 51.5),
      (-4.5, 51.2), (-5.7, 50.0)]
IE = [(-6.0, 52.2), (-6.0, 53.5), (-6.3, 54.1), (-5.6, 54.6), (-6.1, 55.2), (-7.2, 55.3), (-8.3, 55.1),
      (-8.6, 54.3), (-9.9, 53.8), (-9.6, 53.2), (-9.2, 52.6), (-10.2, 51.8), (-9.6, 51.5), (-8.2, 51.8),
      (-6.0, 52.2)]
NO = [(5.0, 58.9), (5.5, 58.1), (7.0, 58.0), (8.2, 58.1), (9.5, 58.9), (10.6, 59.1), (11.1, 58.9), (11.4, 59.9),
      (12.4, 60.3), (12.2, 61.0), (12.9, 61.6), (12.1, 62.6), (12.1, 63.6), (13.9, 64.5), (14.5, 65.3),
      (15.5, 66.3), (16.5, 67.5), (18.0, 68.5), (20.0, 69.0), (21.5, 69.3), (24.0, 68.7), (26.0, 69.9),
      (28.5, 69.0), (31.0, 70.3), (28.0, 71.1), (24.0, 71.0), (20.0, 70.2), (17.0, 69.2), (15.0, 68.3),
      (13.0, 67.2), (12.3, 66.0), (10.5, 64.8), (9.0, 63.5), (7.0, 62.9), (5.0, 62.0), (5.0, 61.0),
      (4.9, 60.0), (5.0, 58.9)]
SE = [(11.1, 58.9), (11.9, 57.7), (12.6, 56.5), (12.9, 55.4), (14.2, 55.4), (14.4, 56.2), (16.0, 56.2),
      (16.6, 57.5), (16.7, 58.6), (18.0, 59.0), (19.0, 59.8), (17.3, 60.6), (17.4, 61.7), (17.8, 62.8),
      (19.5, 63.6), (21.0, 64.6), (22.0, 65.7), (24.1, 65.8), (23.6, 66.9), (23.9, 67.9), (21.0, 69.0),
      (20.0, 69.0), (18.0, 68.5), (16.5, 67.5), (15.5, 66.3), (14.5, 65.3), (13.9, 64.5), (12.1, 63.6),
      (12.1, 62.6), (12.9, 61.6), (12.2, 61.0), (12.4, 60.3), (11.4, 59.9), (11.1, 58.9)]
DK_J = [(8.1, 55.0), (8.6, 56.5), (8.2, 56.8), (9.5, 57.1), (10.6, 57.7), (10.3, 56.9), (10.9, 56.4), (10.2, 56.0),
        (9.8, 55.5), (9.7, 54.9), (8.1, 55.0)]
DK_Z = [(11.2, 55.2), (11.0, 55.7), (11.8, 56.1), (12.6, 56.0), (12.4, 55.3), (11.8, 55.0), (11.2, 55.2)]
DK_F = [(9.8, 55.3), (10.6, 55.0), (10.8, 55.4), (10.2, 55.6), (9.8, 55.3)]
CONTINENT = [(2.5, 51.0), (4.0, 51.4), (4.8, 52.9), (6.9, 53.4), (8.6, 53.9), (8.9, 54.9), (9.7, 54.9),
             (10.9, 54.4), (12.5, 54.4), (14.2, 53.9), (19.0, 54.4), (21.5, 55.2), (22.0, 50.0), (2.5, 50.0)]


class SchematicMap(Canvas):
    def __init__(self, w: int, h: int, lon0: float, lon1: float, lat0: float, lat1: float, top: int = 140,
                 sea: str = "#E6F0F8", land: str = "#F7F5EF", border: str = "#9AA6B4"):
        super().__init__(w, h, sea)
        self.lon0, self.lon1, self.lat0, self.lat1, self.top = lon0, lon1, lat0, lat1, top
        self.k = min((w - 40) / ((lon1 - lon0) * math.cos(math.radians(57))), (h - top - 40) / (lat1 - lat0))
        self.ox = 20 + ((w - 40) - (lon1 - lon0) * math.cos(math.radians(57)) * self.k) / 2
        for poly in (CONTINENT, IE, GB, NO, SE, DK_J, DK_Z, DK_F):
            pts = [self.xy(lon, lat) for lon, lat in poly]
            self.d.polygon(pts, fill=land if poly is not CONTINENT else "#EFEDE6", outline=border)
            self.d.line(pts, fill=border, width=3)

    def xy(self, lon: float, lat: float) -> tuple[float, float]:
        return (self.ox + (lon - self.lon0) * math.cos(math.radians(57)) * self.k,
                self.top + 20 + (self.lat1 - lat) * self.k)

    def pin(self, lon: float, lat: float, color: str = RED, r: int = 13) -> tuple[float, float]:
        x, y = self.xy(lon, lat)
        self.ellipse((x - r, y - r, x + r, y + r), fill=color, outline=WHITE, width=4)
        return (x, y)

    def callout(self, lon: float, lat: float, lx: float, ly: float, text: str, color: str = RED, size: int = 23,
                max_w: int = 520, outline: str | None = None) -> tuple:
        x, y = self.pin(lon, lat, color)
        box = self.label(lx, ly, text, size, bg=WHITE, outline=outline or color, max_w=max_w, pad=10)
        # leader from pin to nearest box edge
        bx = min(max(x, box[0]), box[2])
        by = min(max(y, box[1]), box[3])
        self.polyline([(x, y), (bx, by)], fill=color, width=3)
        self.pin(lon, lat, color)
        return box

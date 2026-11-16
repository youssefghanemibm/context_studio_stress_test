"""Mock UI screenshots: Claims Hub (web), CLARA 3270 maps (green screen), Sentinel dashboard.

Screens are drawn at 1920 px wide (DOCX) or 2200 px (PDF) and are meant to be OCR-legible:
labels >= 22 px on light backgrounds, >= 24 px on dark ones.
"""
from __future__ import annotations

from typing import Sequence

from .core import (AMBER, AMBER_L, BLUE_L, GREEN, GREEN_L, GREY_L, GREY_M, GRID, INK, INK2, MUTED, NAVY,
                   NAVY2, RED, RED_L, TEAL, TEAL_L, WHITE, Canvas)

HUB_BAR = "#0F2A4A"
HUB_ACCENT = "#1D6FD1"
HUB_NAV = "#F3F6FA"


class HubScreen(Canvas):
    """Claims Hub single-page app chrome: top bar, left nav, breadcrumb, content area."""

    NAV = ["Work queue", "Claims", "FNOL intake", "Reserves", "Fraud referrals", "Payments",
           "Recoveries", "Documents", "Reports"]

    def __init__(self, w: int = 1920, h: int = 1140, title: str = "", breadcrumb: str = "", user: str = "",
                 env: str = "PROD", active: str = "Claims", nav: Sequence[str] | None = None, version: str = ""):
        super().__init__(w, h, "#FAFBFD")
        self.rect((0, 0, w, 76), fill=HUB_BAR, outline=HUB_BAR, width=1)
        self.text(30, 38, "Claims Hub", 32, True, fill=WHITE, anchor="lm")
        self.text(250, 38, "Corvane Mutual", 22, fill="#AFC3DB", anchor="lm")
        envc = {"PROD": "#C62828", "UAT": "#B26A00", "TRAINING": "#2E7D32"}.get(env, "#5B3F95")
        self.label(520, 38, env, 20, fill=WHITE, bg=envc, bold=True, pad=7)
        self.rect((640, 18, 1180, 58), fill="#24446B", outline="#24446B", radius=8)
        self.text(660, 38, "Search claim, policy or party", 21, fill="#AFC3DB", anchor="lm")
        if user:
            self.text(w - 30, 38, user, 22, fill=WHITE, anchor="rm")
        # left nav
        self.rect((0, 76, 250, h), fill=HUB_NAV, outline=GRID, width=1)
        y = 104
        for item in (nav or self.NAV):
            if item == active:
                self.rect((0, y - 8, 250, y + 40), fill="#DCE8F8", outline="#DCE8F8")
                self.rect((0, y - 8, 7, y + 40), fill=HUB_ACCENT, outline=HUB_ACCENT)
            self.text(26, y + 16, item, 22, item == active, fill=NAVY if item == active else INK2, anchor="lm")
            y += 58
        if version:
            self.text(20, h - 30, version, 18, fill=MUTED, anchor="lm")
        self.cx0, self.cy0 = 280, 96
        if breadcrumb:
            self.text(self.cx0, self.cy0 + 10, breadcrumb, 21, fill=MUTED)
        if title:
            self.text(self.cx0, self.cy0 + 44, title, 34, True, fill=INK)
        self.content_top = self.cy0 + (100 if title else 40)

    def card(self, box, title: str = "", size: int = 24) -> tuple:
        self.rect(box, fill=WHITE, outline=GRID, width=2, radius=10)
        if title:
            self.text(box[0] + 20, box[1] + 16, title, size, True, fill=NAVY)
            self.d.line([(box[0] + 1, box[1] + 56), (box[2] - 1, box[1] + 56)], fill=GRID, width=2)
            return (box[0] + 20, box[1] + 72)
        return (box[0] + 20, box[1] + 18)

    def field(self, x: int, y: int, label: str, value: str, w: int = 380, size: int = 22, value_bold=False,
              value_color: str = INK, boxed: bool = False) -> int:
        self.text(x, y, label, size - 2, fill=MUTED)
        if boxed:
            self.rect((x, y + size + 6, x + w, y + size + 50), fill=WHITE, outline="#B8C3D1", width=2, radius=6)
            self.text(x + 12, y + size + 28, value, size, value_bold, fill=value_color, anchor="lm")
            return y + size + 66
        self.text(x, y + size + 6, value, size + 1, value_bold, fill=value_color)
        return y + 2 * size + 22

    def chip(self, x: int, y: int, s: str, kind: str = "info", size: int = 20) -> tuple:
        col = {"info": (BLUE_L, NAVY2), "ok": (GREEN_L, GREEN), "warn": (AMBER_L, AMBER),
               "bad": (RED_L, RED), "teal": (TEAL_L, TEAL)}[kind]
        tw = self.twidth(s, size, True)
        box = (x, y, x + tw + 26, y + size + 18)
        self.rect(box, fill=col[0], outline=col[1], width=2, radius=(size + 18) // 2)
        self.text(x + 13, y + (size + 18) / 2, s, size, True, fill=col[1], anchor="lm")
        return box

    def button(self, x: int, y: int, s: str, primary: bool = True, size: int = 22) -> tuple:
        tw = self.twidth(s, size, True)
        box = (x, y, x + tw + 44, y + size + 26)
        if primary:
            self.rect(box, fill=HUB_ACCENT, outline=HUB_ACCENT, radius=8)
            self.text(x + 22, y + (size + 26) / 2, s, size, True, fill=WHITE, anchor="lm")
        else:
            self.rect(box, fill=WHITE, outline=HUB_ACCENT, width=2, radius=8)
            self.text(x + 22, y + (size + 26) / 2, s, size, True, fill=HUB_ACCENT, anchor="lm")
        return box

    def tabs(self, x: int, y: int, items: Sequence[str], active: str, size: int = 23) -> int:
        cx = x
        for it in items:
            tw = self.twidth(it, size, it == active)
            if it == active:
                self.rect((cx, y + size + 18, cx + tw + 30, y + size + 24), fill=HUB_ACCENT, outline=HUB_ACCENT)
            self.text(cx + 15, y + 6, it, size, it == active, fill=NAVY if it == active else INK2)
            cx += tw + 52
        self.d.line([(x, y + size + 24), (self.w - 30, y + size + 24)], fill=GRID, width=2)
        return y + size + 44

    def grid_table(self, x: int, y: int, headers: Sequence[str], rows: Sequence[Sequence[str]],
                   widths: Sequence[int], size: int = 21, row_h: int = 50, head_fill: str = "#EEF2F7") -> int:
        W = sum(widths)
        self.rect((x, y, x + W, y + row_h), fill=head_fill, outline=GRID, width=1)
        cx = x
        for h, w in zip(headers, widths):
            self.text(cx + 12, y + row_h / 2, h, size, True, fill=INK2, anchor="lm")
            cx += w
        y += row_h
        for i, r in enumerate(rows):
            self.rect((x, y, x + W, y + row_h), fill=WHITE if i % 2 == 0 else "#F8FAFC", outline=GRID, width=1)
            cx = x
            for c, w in zip(r, widths):
                self.text(cx + 12, y + row_h / 2, str(c), size, fill=INK, anchor="lm")
                cx += w
            y += row_h
        return y

    def banner(self, x: int, y: int, w: int, s: str, kind: str = "info", size: int = 22) -> int:
        col = {"info": (BLUE_L, NAVY2), "warn": (AMBER_L, AMBER), "ok": (GREEN_L, GREEN), "bad": (RED_L, RED)}[kind]
        lines = self.wrap(s, size, w - 50)
        h = len(lines) * int(size * 1.3) + 26
        self.rect((x, y, x + w, y + h), fill=col[0], outline=col[1], width=2, radius=8)
        self.rect((x, y, x + 8, y + h), fill=col[1], outline=col[1])
        self.lines_block(x + 26, y + 13, lines, size, fill=INK, gap=0.3)
        return y + h


# ------------------------------------------------------------------------------------------
# 3270 green screen
# ------------------------------------------------------------------------------------------
G_GREEN = "#3CFF6E"
G_CYAN = "#5FE3FF"
G_WHITE = "#F2F2F2"
G_YELLOW = "#FFE45C"
G_RED = "#FF5C5C"
G_BLUE = "#7FA8FF"
G_BG = "#050805"


def green_screen(cells: Sequence[tuple[int, int, str, str]], title_bar: str = "", cell_w: int = 22,
                 size: int = 30, rows: int = 24, cols: int = 80, underline: Sequence[tuple[int, int, int]] = ()) -> Canvas:
    """cells: (row 1-24, col 1-80, text, colour). underline: (row, col, length) unprotected fields."""
    pad_x, pad_y = 30, 30
    line_h = int(size * 1.42)
    top = 58 if title_bar else 0
    W = pad_x * 2 + cell_w * cols
    H = top + pad_y * 2 + line_h * rows
    cv = Canvas(W, H, G_BG)
    if title_bar:
        cv.rect((0, 0, W, top), fill="#2B2F36", outline="#2B2F36")
        cv.text(18, top / 2, title_bar, 22, fill="#D0D4DA", anchor="lm")
        for i, c in enumerate(("#E8645A", "#E8B44A", "#5DBB63")):
            cv.ellipse((W - 40 - i * 34, top / 2 - 10, W - 20 - i * 34, top / 2 + 10), fill=c, outline=c)
    for (r, c, ln) in underline:
        x0 = pad_x + (c - 1) * cell_w
        y = top + pad_y + (r - 1) * line_h + int(size * 1.18)
        cv.d.line([(x0, y), (x0 + ln * cell_w, y)], fill="#1F8F3F", width=2)
    for (r, c, txt, col) in cells:
        x = pad_x + (c - 1) * cell_w
        y = top + pad_y + (r - 1) * line_h
        cv.text(x, y, txt, size, False, True, fill=col)
    # status line (OIA)
    cv.d.line([(pad_x, H - pad_y + 4), (W - pad_x, H - pad_y + 4)], fill="#1F8F3F", width=2)
    return cv


# ------------------------------------------------------------------------------------------
# Sentinel dashboard (dark theme)
# ------------------------------------------------------------------------------------------
S_BG = "#0E1726"
S_PANEL = "#16233A"
S_EDGE = "#2A3B5C"
S_TEXT = "#EAF0FA"
S_MUTED = "#A9B7CF"
S_ACCENT = "#36C2B4"
S_WARN = "#F2B84B"
S_BAD = "#FF6B6B"


class SentinelScreen(Canvas):
    def __init__(self, w: int = 2200, h: int = 1300, page: str = "Overview", user: str = "",
                 nav: Sequence[str] = ("Overview", "Thresholds", "Referral queue", "Model", "Integrations", "Audit"),
                 stamp: str = ""):
        super().__init__(w, h, S_BG)
        self.rect((0, 0, w, 84), fill="#0A111D", outline="#0A111D")
        self.text(34, 42, "SENTINEL", 34, True, fill=S_ACCENT, anchor="lm")
        self.text(230, 42, "Fraud scoring console · Corvane Mutual", 24, fill=S_MUTED, anchor="lm")
        if user:
            self.text(w - 34, 42, user, 23, fill=S_TEXT, anchor="rm")
        x = 34
        y = 104
        for it in nav:
            tw = self.twidth(it, 24, it == page)
            if it == page:
                self.rect((x - 14, y - 6, x + tw + 14, y + 44), fill="#203453", outline=S_ACCENT, width=2, radius=8)
            self.text(x, y + 19, it, 24, it == page, fill=S_TEXT if it == page else S_MUTED, anchor="lm")
            x += tw + 64
        if stamp:
            self.text(w - 34, y + 19, stamp, 22, fill=S_MUTED, anchor="rm")
        self.content_top = 180

    def panel(self, box, title: str = "", size: int = 25) -> tuple:
        self.rect(box, fill=S_PANEL, outline=S_EDGE, width=2, radius=12)
        if title:
            self.text(box[0] + 22, box[1] + 18, title, size, True, fill=S_TEXT)
            return (box[0] + 22, box[1] + 70)
        return (box[0] + 22, box[1] + 22)

    def kpi(self, box, label: str, value: str, sub: str = "", color: str = S_TEXT) -> None:
        self.panel(box)
        self.text(box[0] + 24, box[1] + 22, label, 23, fill=S_MUTED)
        self.text(box[0] + 24, box[1] + 62, value, 50, True, fill=color)
        if sub:
            self.text(box[0] + 24, box[3] - 22, sub, 21, fill=S_MUTED, anchor="ls")

    def kv(self, x: int, y: int, k: str, v: str, kw: int = 420, size: int = 25, vcol: str = S_TEXT) -> int:
        self.text(x, y, k, size, fill=S_MUTED)
        self.text(x + kw, y, v, size, True, fill=vcol)
        return y + int(size * 1.85)

    def table(self, x: int, y: int, headers: Sequence[str], rows: Sequence[Sequence[str]], widths: Sequence[int],
              size: int = 23, row_h: int = 52, colors: dict | None = None) -> int:
        W = sum(widths)
        self.rect((x, y, x + W, y + row_h), fill="#1C2C48", outline=S_EDGE, width=1)
        cx = x
        for h, w in zip(headers, widths):
            self.text(cx + 14, y + row_h / 2, h, size, True, fill=S_MUTED, anchor="lm")
            cx += w
        y += row_h
        for i, r in enumerate(rows):
            self.rect((x, y, x + W, y + row_h), fill=S_PANEL if i % 2 == 0 else "#192842", outline=S_EDGE, width=1)
            cx = x
            for j, (c, w) in enumerate(zip(r, widths)):
                col = (colors or {}).get((i, j), S_TEXT)
                self.text(cx + 14, y + row_h / 2, str(c), size, fill=col, anchor="lm")
                cx += w
            y += row_h
        return y

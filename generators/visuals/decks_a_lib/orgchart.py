"""Org-chart slides: boxes for people, glued elbow connectors manager -> report.

Connector lines extract as '<manager box text> -> <report box text>' (harness/extract.py), so a
reporting line can be verified from the connector alone.
"""
from __future__ import annotations

from pptx.oxml.ns import qn

from . import phrases as P

ROWS = [1.4, 2.65, 3.9, 5.15]
BOX_H = 0.9


def _rotate_elbow(cx, p1, p2) -> None:
    """Turn a bentConnector3 into a vertical-horizontal-vertical elbow between p1 (top) and p2."""
    x1, y1 = p1
    x2, y2 = p2
    dx, dy = x2 - x1, y2 - y1
    if abs(dx) < 2000 or dy <= 0:
        return
    xfrm = cx._element.spPr.find(qn("a:xfrm"))
    W, H = abs(dy), abs(dx)
    mx, my = (x1 + x2) / 2, (y1 + y2) / 2
    xfrm.find(qn("a:off")).set("x", str(int(mx - W / 2)))
    xfrm.find(qn("a:off")).set("y", str(int(my - H / 2)))
    xfrm.find(qn("a:ext")).set("cx", str(int(W)))
    xfrm.find(qn("a:ext")).set("cy", str(int(H)))
    for a in ("flipH", "flipV"):
        if a in xfrm.attrib:
            del xfrm.attrib[a]
    xfrm.set("rot", "5400000")
    if dx > 0:
        xfrm.set("flipV", "1")


def link(s, parent, child, color="navy2"):
    cx = s.connect(parent, child, a_site="b", b_site="t", kind="elbow", arrow=False, color=color, width=1.25)
    p1 = (parent.left + parent.width / 2, parent.top + parent.height)
    p2 = (child.left + child.width / 2, child.top)
    _rotate_elbow(cx, p1, p2)
    return cx


def box_text(D, pid) -> str:
    n, t = D.who(pid)
    return f"{n} {t}"


def org_slide(D, title, kicker, head, reports, above=None, notes_topic=None, notes_facts=None,
              head_style="org_head", kid_w=None):
    """head: pid; reports: list of pid or (pid, [kid pids]) (max 2 kids, placed beneath).
    Returns (slide, {pid: shape})."""
    s = D.content(title, kicker)
    shapes = {}
    r0 = 0
    if above:
        n, t = D.who(above)
        shapes[above] = s.org(5.35, ROWS[0], 2.6, BOX_H, n, t, style="org_vacant", size=10)
        r0 = 1
    n, t = D.who(head)
    hb = s.org(5.25, ROWS[r0], 2.8, BOX_H, n, t, style=head_style, size=11)
    shapes[head] = hb
    if above:
        link(s, shapes[above], hb)
    k = len(reports)
    w = min(2.3, (12.3 - 0.18 * (k - 1)) / max(k, 1))
    total = k * w + (k - 1) * 0.18
    x0 = 0.5 + (12.3 - total) / 2
    for i, r in enumerate(reports):
        pid, kids = (r if isinstance(r, tuple) else (r, []))
        x = x0 + i * (w + 0.18)
        n, t = D.who(pid)
        b = s.org(x, ROWS[r0 + 1], w, BOX_H, n, t, size=10 if w < 2.1 else 11)
        shapes[pid] = b
        link(s, hb, b)
        kw = kid_w or w
        for j, kid in enumerate(kids):
            if len(kids) == 1:
                kx = x + (w - kw) / 2
            else:
                kx = x + w / 2 - kw - 0.08 if j == 0 else x + w / 2 + 0.08
            n2, t2 = D.who(kid)
            kb = s.org(kx, ROWS[r0 + 2], kw, BOX_H, n2, t2, size=10 if kw < 2.1 else 11)
            shapes[kid] = kb
            link(s, b, kb)
    s.notes(P.notes(D.rng, notes_topic or title.lower(), notes_facts))
    return s, shapes


def team_cards(D, s, cards, y=1.5, cols=3, w=3.95, h=1.55, gx=0.22, gy=0.25, prefix="Team card"):
    """SmartArt-style nested groups: an outer group holding one group per team card.
    cards: [(team name, [lines])]. Returns {team name: group name}."""
    outer = s.group(f"{prefix}s")
    names = {}
    for i, (tname, lines) in enumerate(cards):
        c, r = i % cols, i // cols
        x, yy = 0.5 + c * (w + gx), y + r * (h + gy)
        gname = f"{prefix}: {tname}"
        g = outer.group(gname)
        g.box(x, yy, w, 0.42, tname, style="tile", fill="teal", color="white", size=11, bold=True)
        g.box(x, yy + 0.42, w, h - 0.42, [{"text": ln, "size": 10} for ln in lines], style="tile",
              fill="grey_l", align="l", anchor="t", margins=0.1)
        names[tname] = gname
    return names

"""Spec writer shared by the v7.2 and v6.1 manual content modules.

A spec is: blocks (declarative document content), segs (page-calibration segments in order),
pools (filler units per segment) and facts (attached to blocks; locators filled at render).
"""
from __future__ import annotations

import datetime as dt
import re

from generators.common import util
from .prose import Prose, TOPICS, _cap

MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September",
          "October", "November", "December"]


def long_date(d: str) -> str:
    y, m, dd = (int(x) for x in d.split("-"))
    return f"{dd} {MONTHS[m - 1]} {y}"


def money(v, cur="£") -> str:
    v = int(v)
    if cur == "£":
        return f"£{v:,}"
    return f"{cur} {v:,}"


class Spec:
    def __init__(self, W, fid: str, as_of: str, style: dict, seed_key: str, v61: bool = False):
        self.W = W
        self.fid = fid
        self.as_of = as_of
        self.style = style
        self.v61 = v61
        self.blocks: list[dict] = []
        self.segs: list[dict] = []
        self.pools: dict[str, list] = {}
        self.prose = Prose(util.rng(seed_key + ":base"), style)
        self.fill_prose = Prose(util.rng(seed_key + ":fill"), style)
        self.fill_prose.used = self.prose.used
        self.r = util.rng(seed_key + ":struct")
        self.seed_key = seed_key
        self.cur_seg: dict | None = None
        self.chapter = None
        self.section = None          # "18.1"
        self.section_title = None    # full heading text
        self.h3n = 0
        self.topic = "governance"
        self.facts: list[dict] = []
        self.rule_sections: dict[str, str] = {}
        self.fig_n: dict[int, int] = {}
        self.tab_n: dict[int, int] = {}

    # ------------------------------------------------------------------ world access
    def rv(self, rid: str, as_of: str | None = None) -> dict:
        v = self.W.rule_version(rid, as_of or self.as_of)
        assert v is not None, f"{rid} not in force at {as_of or self.as_of}"
        return v

    def may(self, ref: str, field: str | None = None) -> bool:
        return self.W.may_state(self.fid, ref, field)

    def person(self, pid: str) -> str:
        return self.W.name_of(pid, self.as_of)

    def title(self, pid: str) -> str:
        return self.W.title_of(pid, self.as_of)

    # ------------------------------------------------------------------ facts
    def fact(self, kind: str, statement: str, needle: str, world_ref: str | None = None,
             exclusive: bool = False, placement: str | None = None, key: str | None = None,
             notes: str | None = None, also_in: list | None = None, **extra) -> dict:
        f = {"kind": kind, "statement": statement, "needle": needle, "world_ref": world_ref,
             "exclusive": exclusive, "also_in": list(also_in or [])}
        if placement:
            f["placement"] = placement
            f["placement_key"] = key
        if notes:
            f["notes"] = notes
        f.update(extra)
        self.facts.append(f)
        return f

    def placement_fact(self, pl: dict, statement: str, needle: str, notes: str | None = None,
                       kind: str | None = None, **extra) -> dict:
        return self.fact(kind or pl["kind"], statement, needle, world_ref=pl["world_ref"],
                         exclusive=bool(pl.get("exclusive")), placement=pl["placement_id"], key=pl["key"],
                         notes=notes, also_in=list(pl.get("also_in", [])), **extra)

    # ------------------------------------------------------------------ segments
    def _close_seg(self):
        s = self.cur_seg
        if s is None:
            return
        if s["fill"] and not s.get("_fill_placed"):
            self.blocks.append({"t": "fill", "seg": s["id"]})
            s["_fill_placed"] = True
            s["_ctx"] = (self.topic, self.section or str(self.chapter), self.h3n)

    def new_seg(self, seg_id: str, marker: tuple, target: int | None, fill: bool = True, elastic: bool = False,
                table_fill: bool = False):
        self._close_seg()
        s = {"id": seg_id, "marker": marker, "target": target, "fill": fill and not table_fill,
             "elastic": elastic, "table_fill": table_fill, "topic": self.topic}
        self.segs.append(s)
        self.cur_seg = s
        return s

    def fill_here(self):
        s = self.cur_seg
        self.blocks.append({"t": "fill", "seg": s["id"]})
        s["_fill_placed"] = True
        s["_ctx"] = (self.topic, self.section or str(self.chapter), self.h3n)

    def _build_pool(self, s, span):
        P = self.fill_prose
        topic, sec, h3n = s["_ctx"]
        n_units = max(30, int(span * 9) + 30)
        units = []
        used_titles = set()
        next_h3 = 0
        for k in range(n_units):
            unit = []
            if k == next_h3:
                for _ in range(20):
                    t = P.filler_title(self.v61)
                    if t not in used_titles:
                        break
                used_titles.add(t)
                if len(used_titles) >= 9:
                    used_titles.clear()
                h3n += 1
                unit.append({"t": "h3", "text": f"{sec}.{h3n} {t}"})
                next_h3 = k + P.r.randint(5, 9)
            roll = P.r.random()
            if roll < 0.035:
                unit.extend(P.qa_unit(topic))
            elif roll < 0.06:
                unit.append(P.dodont_table(topic))
            elif roll < 0.085:
                unit.extend(P.note_unit(topic))
            elif roll < 0.15:
                unit.append({"t": "p", "text": P.fmt(P.r.choice([
                    "The following points should be checked on every file:", "In particular:",
                    "Reviewers will expect to see that:", "Before moving on, confirm that:",
                    "Handlers should be able to show that:"]))})
                for b in P.bullets(topic, "qa" if P.r.random() < 0.5 else "actions", (3, 5)):
                    unit.append({"t": "p", "text": b.rstrip(".") + ".", "style": "List Bullet"})
            elif roll < 0.21:
                unit.append({"t": "p", "text": P.fmt(P.r.choice([
                    "A typical sequence is:", "The steps are normally taken in this order:",
                    "Work through the following steps:", "The usual approach is as follows:"]))})
                for i, st in enumerate(P.steps(topic, (4, 6)), start=1):
                    unit.append({"t": "p", "text": f"{i}. {st}", "style": "Box Text" if self.v61 else None,
                                 "indent": True})
            else:
                unit.append({"t": "p", "text": P.paragraph(topic, (3, 6))})
            units.append(unit)
        self.pools[s["id"]] = units

    # ------------------------------------------------------------------ structure helpers
    def h1(self, num: int, title: str, target: int | None, topic: str, fill: bool = True, elastic=False):
        self.topic = topic
        text = f"{num} {title}"
        self.new_seg(f"ch{num}", ("heading", text), target, fill=fill, elastic=elastic)
        self.blocks.append({"t": "h1", "text": text, "break": True})
        self.chapter = num
        self.section = str(num)
        self.section_title = text
        self.h3n = 0
        self.fig_n[num] = 0
        self.tab_n[num] = 0
        return text

    def h2(self, num: str, title: str, target: int | None = None, fill: bool = True, seg_id: str | None = None,
           facts=None, table_fill=False, topic: str | None = None):
        text = f"{num} {title}"
        if topic:
            self.topic = topic
        if target is not None or seg_id:
            self.new_seg(seg_id or f"s{num}", ("heading", text), target, fill=fill, table_fill=table_fill)
            self.blocks.append({"t": "h2", "text": text, "break": True, "facts": facts or []})
        else:
            self.blocks.append({"t": "h2", "text": text, "facts": facts or []})
        self.section = num
        self.section_title = text
        self.h3n = 0
        return text

    def h3(self, title: str):
        self.h3n += 1
        text = f"{self.section}.{self.h3n} {title}"
        self.blocks.append({"t": "h3", "text": text})
        return text

    def p(self, text: str | None = None, facts=None, runs=None, style=None, comment=None, **kw):
        b = {"t": "p", "facts": facts or []}
        if runs is not None:
            b["runs"] = runs
        else:
            b["text"] = text
        if style:
            b["style"] = style
        if comment:
            b["comment"] = comment
        b.update(kw)
        self.blocks.append(b)
        return b

    def prose_p(self, n=(3, 5), topic=None):
        return self.p(self.prose.paragraph(topic or self.topic, n))

    def prose_ps(self, k: int, topic=None):
        for _ in range(k):
            self.prose_p(topic=topic)

    def bullets(self, items: list[str], intro: str | None = None, facts_by_item: dict | None = None):
        if intro:
            self.p(intro, keep_next=True)
        for i, it in enumerate(items):
            self.p(it, style="List Bullet", facts=(facts_by_item or {}).get(i))

    def steps(self, items: list[str], intro: str | None = None):
        if intro:
            self.p(intro, keep_next=True)
        for i, it in enumerate(items, start=1):
            self.p(f"{i}. {it}")

    def table(self, header, rows, caption=None, facts=None, widths=None, size=9, repeat_header=True, **kw):
        if caption:
            self.tab_n[self.chapter] = self.tab_n.get(self.chapter, 0) + 1
            caption = f"Table {self.chapter}-{self.tab_n[self.chapter]}: {caption}"
        b = {"t": "table", "header": header, "rows": rows, "caption": caption, "facts": facts or [],
             "widths": widths, "size": size, "repeat_header": repeat_header}
        b.update(kw)
        self.blocks.append(b)
        return b

    def figure(self, png, caption, alt, facts=None, alt_facts=None, width_in=6.2):
        self.fig_n[self.chapter] = self.fig_n.get(self.chapter, 0) + 1
        cap = f"Figure {self.chapter}-{self.fig_n[self.chapter]}: {caption}"
        self.blocks.append({"t": "figure", "png": str(png), "caption": cap, "alt": alt, "facts": facts or [],
                            "alt_facts": alt_facts or [], "width_in": width_in})
        return cap

    def finish(self, total_pages: int | None = None):
        self._close_seg()
        self.cur_seg = None
        for i, s in enumerate(self.segs):
            if not s["fill"]:
                continue
            nxt = self.segs[i + 1]["target"] if i + 1 < len(self.segs) else (total_pages + 1 if total_pages else None)
            if s["target"] is not None and nxt is not None:
                span = nxt - s["target"]
            else:
                span = 6
            self._build_pool(s, span)

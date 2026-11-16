"""Deterministic page packing for reportlab BaseDocTemplate documents.

The Packer simulates platypus layout with the very same ``Frame`` logic on a throw-away canvas, so
the generator knows exactly which page and frame every flowable (or split piece) lands in. The
final document is then built with BaseDocTemplate from the recorded pieces, separated by
FrameBreak / NextPageTemplate / PageBreak, which reproduces the simulated layout page for page.
"""
from __future__ import annotations

import io
from dataclasses import dataclass, field
from typing import Callable

from reportlab.lib.units import mm
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import (BaseDocTemplate, Flowable, Frame, FrameBreak, NextPageTemplate,
                                PageBreak, PageTemplate, Spacer)
from reportlab.platypus.doctemplate import LayoutError


@dataclass
class TemplateSpec:
    name: str
    frames: list            # list of (x, y, w, h)
    decorate: Callable | None = None   # decorate(canvas, doc) for header/footer


@dataclass
class PageRec:
    template: str
    frames: list = field(default_factory=list)      # list[list[flowable]]
    footnotes: list = field(default_factory=list)   # per frame: list of flowables
    marks: dict = field(default_factory=dict)


class FootnoteBlock(Flowable):
    """A short rule followed by footnote paragraphs, placed at the bottom of a column."""

    def __init__(self, paras, rule_w=40 * mm, gap=3):
        super().__init__()
        self.paras = paras
        self.rule_w = rule_w
        self.gap = gap
        self._sizes = []

    def wrap(self, aw, ah):
        self._sizes = [p.wrap(aw, 10_000) for p in self.paras]
        self.width = aw
        self.height = self.gap * 2 + sum(h for _, h in self._sizes) + 2 * max(0, len(self.paras) - 1)
        return aw, self.height

    def draw(self):
        c = self.canv
        y = self.height
        c.saveState()
        c.setLineWidth(0.5)
        c.line(0, y - 0.5, min(self.rule_w, self.width), y - 0.5)
        c.restoreState()
        y -= self.gap * 2
        for p, (_, h) in zip(self.paras, self._sizes):
            y -= h
            p.drawOn(c, 0, y)
            y -= 2


class Packer:
    def __init__(self, pagesize, templates: dict[str, TemplateSpec], first_page_no: int = 1):
        self.pagesize = pagesize
        self.templates = templates
        self.canv = Canvas(io.BytesIO(), pagesize=pagesize, invariant=1)
        self.pages: list[PageRec] = []
        self.first_page_no = first_page_no
        self.cur_template: str | None = None
        self.frame: Frame | None = None
        self.fi = -1
        self._fn_reserved = 0.0
        self.log: list[tuple] = []   # (page_no, frame_idx, tag)

    # -- geometry ------------------------------------------------------------------------------
    @property
    def page_no(self) -> int:
        return self.first_page_no + len(self.pages) - 1

    def _make_frame(self, geom, idx):
        x, y, w, h = geom
        return Frame(x, y, w, h, leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0,
                     id=f"f{idx}", showBoundary=0)

    def new_page(self, template: str | None = None):
        if self.frame is not None:
            self._close_frame()
        template = template or self.cur_template
        self.cur_template = template
        spec = self.templates[template]
        self.pages.append(PageRec(template=template, frames=[[] for _ in spec.frames],
                                  footnotes=[[] for _ in spec.frames]))
        self.fi = 0
        self.frame = self._make_frame(spec.frames[0], 0)
        self._fn_reserved = 0.0

    def next_frame(self):
        spec = self.templates[self.pages[-1].template]
        self._close_frame()
        if self.fi + 1 >= len(spec.frames):
            self.frame = None
            self.new_page()
            return
        self.fi += 1
        self.frame = self._make_frame(spec.frames[self.fi], self.fi)
        self._fn_reserved = 0.0

    def remaining(self) -> float:
        return self.frame._y - self.frame._y1p

    def frame_empty(self) -> bool:
        return bool(self.frame._atTop)

    def is_last_frame(self) -> bool:
        return self.fi == len(self.templates[self.pages[-1].template].frames) - 1

    def avail_width(self) -> float:
        return self.frame._getAvailableWidth()

    # -- adding --------------------------------------------------------------------------------
    def _record(self, f):
        self.pages[-1].frames[self.fi].append(f)

    def add(self, f, tag: str | None = None):
        """Add a flowable with platypus semantics (split across frames/pages as needed).

        Returns a list of (page_no, frame_idx, piece) for every piece placed."""
        placed = []
        pending = [f]
        guard = 0
        while pending:
            guard += 1
            if guard > 5000:
                raise LayoutError("packer loop")
            g = pending.pop(0)
            if self.frame.add(g, self.canv, trySplit=1):
                self._record(g)
                placed.append((self.page_no, self.fi, g))
                continue
            S = self.frame.split(g, self.canv)
            if S:
                if not self.frame.add(S[0], self.canv, trySplit=0):
                    raise LayoutError("split piece does not fit")
                self._record(S[0])
                placed.append((self.page_no, self.fi, S[0]))
                pending[0:0] = S[1:]
                continue
            if self.frame_empty():
                raise LayoutError(f"flowable too large for an empty frame on page {self.page_no}")
            self.next_frame()
            pending.insert(0, g)
        if tag:
            for pn, fi, _ in placed:
                self.log.append((pn, fi, tag))
        return placed

    def fits(self, f) -> bool:
        """Would ``f`` fit completely in the remaining space of the current frame?"""
        aw = self.avail_width()
        _, h = f.wrap(aw, 100_000)
        s = 0 if self.frame_empty() else f.getSpaceBefore()
        return h + s <= self.remaining() + 0.01

    def height_of(self, f) -> float:
        _, h = f.wrap(self.avail_width(), 100_000)
        return h + (0 if self.frame_empty() else f.getSpaceBefore()) + f.getSpaceAfter()

    def reserve_footnote(self, block: FootnoteBlock):
        """Reserve space at the bottom of the current frame for a footnote block."""
        _, h = block.wrap(self.avail_width(), 10_000)
        block._h = h
        self.frame._y1p += h + 8      # 8pt margin: the last spaceAfter may dip below the frame bottom
        self._fn_reserved += h + 8
        self.pages[-1].footnotes[self.fi].append(block)

    def _close_frame(self):
        if self.frame is None or not self.pages:
            return
        fns = self.pages[-1].footnotes[self.fi]
        if fns:
            orig_p = self.frame._y1p - self._fn_reserved
            total = sum(b._h for b in fns)
            gap = (self.frame._y - orig_p) - total - 1.0
            if gap < 0:
                raise LayoutError("footnote does not fit at the bottom of the frame")
            if gap > 0.3:
                self.pages[-1].frames[self.fi].append(Spacer(1, gap))
            self.pages[-1].frames[self.fi].extend(fns)

    def finish(self):
        if self.frame is not None:
            self._close_frame()
            self.frame = None


def story_from_pages(pages: list[PageRec]) -> list:
    story = []
    for i, pg in enumerate(pages):
        if i == 0:
            story.append(NextPageTemplate(pg.template))
        for fi, flows in enumerate(pg.frames):
            story.extend(flows)
            if fi < len(pg.frames) - 1:
                story.append(FrameBreak())
        if i < len(pages) - 1:
            story.append(NextPageTemplate(pages[i + 1].template))
            story.append(PageBreak())
    return story


class _Doc(BaseDocTemplate):
    def __init__(self, *a, total_pages=0, **kw):
        super().__init__(*a, **kw)
        self.total_pages = total_pages


def build_pdf(path, pagesize, templates: dict[str, TemplateSpec], pages: list[PageRec], meta: dict,
              first_template: str | None = None):
    """Render recorded pages with BaseDocTemplate."""
    doc = _Doc(str(path), pagesize=pagesize, leftMargin=0, rightMargin=0, topMargin=0, bottomMargin=0,
               title=meta.get("title", ""), author=meta.get("author", ""), subject=meta.get("subject", ""),
               creator=meta.get("creator", "Corvane Mutual document production"),
               keywords=meta.get("keywords", ""), invariant=1, total_pages=len(pages),
               allowSplitting=1)
    pts = []
    order = [first_template or pages[0].template] + [n for n in templates if n != (first_template or pages[0].template)]
    for name in order:
        spec = templates[name]
        frames = [Frame(x, y, w, h, leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0,
                        id=f"{name}_f{i}") for i, (x, y, w, h) in enumerate(spec.frames)]
        pts.append(PageTemplate(id=name, frames=frames, onPage=spec.decorate))
    doc.addPageTemplates(pts)
    doc.build(story_from_pages(pages))
    return doc

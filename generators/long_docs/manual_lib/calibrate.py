"""Page calibration: render with LibreOffice, read bookmarks and page text, tune filler units.

Segments are separated by hard page breaks, so each segment's page count depends only on its own
content. For every fill segment we look for the largest number of filler units for which the
segment occupies exactly its target number of pages (so the last page is nearly full).
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import re
import shutil
import unicodedata

from generators.common import util

CACHE = util.BUILD / "cache" / "ld_manual"


def sha1(path) -> str:
    h = hashlib.sha1()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKC", s or "")
    s = s.replace("—", "-").replace("–", "-").replace("’", "'").replace("‘", "'")
    s = s.replace("“", '"').replace("”", '"').replace(" ", " ").replace("­", "")
    return re.sub(r"\s+", " ", s).strip().casefold()


def render_pdf(docx: pathlib.Path, profile_key: str) -> pathlib.Path:
    """LibreOffice PDF of a docx, cached by the docx sha1."""
    key = sha1(docx)
    out = CACHE / "pdf" / f"{key}.pdf"
    if out.exists():
        return out
    tmp = CACHE / "tmp" / profile_key
    if tmp.exists():
        shutil.rmtree(tmp)
    produced = util.soffice_convert(docx, "pdf", tmp, profile_key=profile_key)
    out.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(produced), out)
    return out


class PdfInfo:
    def __init__(self, pdf: pathlib.Path):
        import pymupdf
        self.path = pdf
        with pymupdf.open(pdf) as d:
            self.pages = d.page_count
            self.toc = [(lvl, title.strip(), pg) for lvl, title, pg in d.get_toc(simple=True)]
            self.raw = [d[i].get_text() for i in range(d.page_count)]
        self.texts = [norm(t) for t in self.raw]
        self.bm: dict[str, int] = {}
        for lvl, title, pg in self.toc:
            self.bm.setdefault(norm(title), pg)

    def heading_page(self, text: str) -> int | None:
        return self.bm.get(norm(text))

    def find(self, needle: str, start: int = 1, span: int | None = None) -> int | None:
        n = norm(needle)
        end = self.pages if span is None else min(self.pages, start + span)
        for p in range(max(1, start), end + 1):
            if n in self.texts[p - 1]:
                return p
        tight = n.replace(" ", "")
        for p in range(max(1, start), end + 1):
            if tight in self.texts[p - 1].replace(" ", ""):
                return p
        return None

    def find_split(self, needle: str, start: int = 1, span: int = 30) -> int | None:
        n = norm(needle)
        end = min(self.pages - 1, start + span)
        for p in range(max(1, start), end + 1):
            if n in (self.texts[p - 1] + " " + self.texts[p]):
                return p
        return None


def measure(info: PdfInfo, segs: list[dict]) -> dict[str, int]:
    starts = {}
    prev = 1
    for s in segs:
        kind = s["marker"][0]
        if kind == "first":
            pg = 1
        elif kind == "heading":
            pg = info.heading_page(s["marker"][1])
        else:
            pg = info.find(s["marker"][1], prev)
        if pg is None:
            raise RuntimeError(f"segment marker not found: {s['id']} {s['marker']}")
        starts[s["id"]] = pg
        prev = pg
    return starts


def seg_counts(info: PdfInfo, segs: list[dict], starts: dict) -> dict[str, int]:
    out = {}
    for i, s in enumerate(segs):
        nxt = starts[segs[i + 1]["id"]] if i + 1 < len(segs) else info.pages + 1
        out[s["id"]] = nxt - starts[s["id"]]
    return out


def desired_counts(segs: list[dict], starts: dict, total_target: int | None) -> dict[str, int]:
    out = {}
    for i, s in enumerate(segs):
        if not (s["fill"] or s.get("table_fill")):
            continue
        my = s["target"] if s["target"] is not None else starts[s["id"]]
        if i + 1 < len(segs):
            nt = segs[i + 1]["target"]
            if nt is None:
                continue
        else:
            if total_target is None:
                continue
            nt = total_target + 1
        out[s["id"]] = nt - my
    return out


def next_units(obs: dict[int, int], want: int, upp: float, cap: int) -> tuple[int, bool]:
    """Choose the next unit count. obs maps units -> pages. Returns (units, converged)."""
    le = [u for u, p in obs.items() if p <= want]
    gt = [u for u, p in obs.items() if p > want]
    lo = max(le) if le else None
    hi = min(gt) if gt else None
    if lo is not None and hi is not None and hi - lo <= 1:
        return lo, obs[lo] == want
    if lo is None:
        # even the smallest tried is too long: go down
        u = min(obs)
        if u == 0:
            return 0, False
        return max(0, int(u - max(1, (obs[u] - want + 0.5) * upp))), False
    if hi is None:
        if lo >= cap:
            return cap, obs[lo] == want
        step = max(1, int(round((want - obs[lo] + 0.55) * upp)))
        return min(cap, lo + step), False
    return (lo + hi) // 2, False


def calibrate(build_fn, segs: list[dict], pools: dict, init_units: dict, total_target: int | None,
              log, max_iter: int = 14, upp_default: float = 5.5):
    """build_fn(params) -> PdfInfo. Returns (params, info, starts, report)."""
    units = dict(init_units)
    obs: dict[str, dict[int, int]] = {s["id"]: {} for s in segs}
    info = starts = None
    converged = {}
    for it in range(max_iter):
        params = {"units": dict(units)}
        info = build_fn(params)
        starts = measure(info, segs)
        counts = seg_counts(info, segs, starts)
        want = desired_counts(segs, starts, total_target)
        all_ok = True
        changes = 0
        for s in segs:
            sid = s["id"]
            if sid not in want:
                continue
            obs[sid][units.get(sid, 0)] = counts[sid]
            o = obs[sid]
            # units-per-page estimate from observations
            pts = sorted(o.items())
            upp = upp_default
            if len(pts) >= 2:
                (u1, p1), (u2, p2) = pts[0], pts[-1]
                if p2 != p1:
                    upp = max(1.0, (u2 - u1) / (p2 - p1))
            cap = len(pools.get(sid, [])) if not s.get("table_fill") else s.get("cap", 400)
            nu, ok = next_units(o, want[sid], upp, cap)
            converged[sid] = ok
            if not ok:
                all_ok = False
            if nu != units.get(sid, 0):
                changes += 1
                units[sid] = nu
            elif not ok:
                pass
        bad = [s["id"] for s in segs if s["target"] is not None and starts[s["id"]] != s["target"]]
        log(f"  iter {it}: pages={info.pages} misaligned={len(bad)} changes={changes} {bad[:6]}")
        if changes == 0:
            break
    report = {"pages": info.pages, "starts": starts, "misaligned": [
        (s["id"], s["target"], starts[s["id"]]) for s in segs if s["target"] is not None and starts[s["id"]] != s["target"]],
        "not_converged": [k for k, v in converged.items() if not v]}
    return {"units": units}, info, starts, report

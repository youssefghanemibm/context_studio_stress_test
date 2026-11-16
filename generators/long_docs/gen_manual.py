#!/usr/bin/env python
"""Long-docs part 'manual': LD001 (Claims Handling Manual v7.2, ~496 pages DOCX), LD002 (image-only
scan of LD001) and LD012 (superseded manual v6.1, ~300 pages DOCX).

    python -I generators/long_docs/gen_manual.py [--only LD001,LD002,LD012]

Writes only its own files in corpus/upload/long_docs/ and manifests/long_docs.manual.facts.yaml.
LibreOffice renders and calibration results are cached in build/cache/ld_manual/.
"""
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import argparse
import hashlib
import json
import shutil
import time

import yaml

from generators.common import util
from world.worldlib import load_world
from generators.long_docs.manual_lib import calibrate as C
from generators.long_docs.manual_lib import content_v61, content_v72, scan
from generators.long_docs.manual_lib.builder import ManualBuilder, make_clean_variant, normalize_zip

FAMILY = "long_docs.manual"
OUT = util.UPLOAD / "long_docs"
CACHE = C.CACHE
NAMES = {"LD001": "LD001_claims_handling_manual_v7_2.docx",
         "LD002": "LD002_claims_handling_manual_v7_2_scanned.pdf",
         "LD012": "LD012_claims_handling_manual_v6_1.docx"}
SCAN_DPI = 120
SCAN_QUALITY = 10
INTERNAL_KEYS = ("mirror", "ocr_needle", "half", "_section", "_caption", "_anchor")


def log(msg):
    print(msg, file=sys.stderr, flush=True)


def source_key(fid: str) -> str:
    h = hashlib.sha256(fid.encode())
    files = sorted((ROOT / "generators" / "long_docs" / "manual_lib").glob("*.py")) + \
        [ROOT / "generators" / "common" / "util.py"] + sorted((ROOT / "world" / "data").glob("*.yaml"))
    for f in files:
        if f.name in ("scan.py",):
            continue
        h.update(f.name.encode())
        h.update(f.read_bytes())
    return h.hexdigest()


# ---------------------------------------------------------------------------------------------
# calibrated production of one manual
# ---------------------------------------------------------------------------------------------

def produce(fid: str, spec, cfg: dict, total_target: int, profile: str):
    builder = ManualBuilder(cfg)
    work = CACHE / "work" / fid
    work.mkdir(parents=True, exist_ok=True)
    key = source_key(fid)
    cfile = CACHE / f"{fid}_calib.json"
    state = {"toc": {}}
    for s in spec.segs:
        if s["marker"][0] == "heading" and s["target"]:
            state["toc"][s["marker"][1]] = s["target"]

    def build_fn(params):
        docx = work / f"{fid}.docx"
        res = builder.render(spec.blocks, spec.pools, params, docx, toc_pages=state["toc"])
        clean = work / f"{fid}_clean.docx"
        make_clean_variant(docx, clean, cfg["date"])
        pdf = C.render_pdf(clean, profile)
        info = C.PdfInfo(pdf)
        state.update(res=res, info=info, docx=docx, clean=clean, pdf=pdf)
        state["newtoc"] = {h: (info.heading_page(h) or "") for _, h in res.headings}
        return info

    params = None
    if cfile.exists():
        # The cached unit counts are tried even when the source key changed: alignment of every
        # segment start (and a stable TOC) is the real acceptance test, so a still-aligned build
        # is accepted as is, and a misaligned one seeds the recalibration.
        cached = json.loads(cfile.read_text())
        same_key = cached.get("key") == key
        params = {"units": cached["units"]}
        state["toc"] = cached["toc"]
        info = build_fn(params)
        try:
            starts = C.measure(info, spec.segs)
            bad = [s["id"] for s in spec.segs if s["target"] is not None and starts[s["id"]] != s["target"]]
        except RuntimeError as exc:
            bad = [str(exc)]
        if not (total_target - 3 <= info.pages <= total_target):
            bad.append(f"pages={info.pages}")
        if bad or state["newtoc"] != state["toc"]:
            log(f"[{fid}] cached calibration no longer aligned ({bad[:5]}); recalibrating")
            state["init_units"] = cached["units"]
            params = None
        else:
            log(f"[{fid}] calibration cache hit" + ("" if same_key else " (source changed, still aligned)"))
            if not same_key:
                cached["key"] = key
                cfile.write_text(json.dumps(cached, indent=1, sort_keys=True))
    report = {}
    if params is None:
        t0 = time.time()
        params, info, starts, report = C.calibrate(build_fn, spec.segs, spec.pools, state.get("init_units", {}), total_target, log)
        log(f"[{fid}] calibrated in {time.time() - t0:.0f}s: {json.dumps({k: v for k, v in report.items() if k != 'starts'})}")
        for _ in range(3):
            if state["newtoc"] == state["toc"]:
                break
            state["toc"] = dict(state["newtoc"])
            info = build_fn(params)
        cfile.write_text(json.dumps({"key": key, "units": params["units"], "toc": state["toc"],
                                     "report": {k: v for k, v in report.items() if k != "starts"}}, indent=1, sort_keys=True))
    starts = C.measure(state["info"], spec.segs)
    return state, starts, report


def page_hints(facts, info: C.PdfInfo, starts_by_heading):
    for f in facts:
        loc = f["locator"]
        sec = f.get("_section")
        start = info.heading_page(sec) if sec else None
        start = start or 1
        if loc["kind"] in ("docx_header", "docx_footer"):
            loc["page_hint"] = 1
            continue
        probe = f.get("_caption") or f.get("_anchor") or f["needle"]
        if loc["kind"] in ("docx_comment",):
            probe = f.get("_anchor") or probe
        pg = info.find(probe, start, span=40) if loc["kind"] not in ("docx_image", "docx_alt_text") else info.find(f["_caption"], start, span=40)
        if pg is None:
            pg = info.find_split(probe, start, span=40)
        if pg is None:
            pg = info.find(probe, 1)
        loc["page_hint"] = pg if pg is not None else start
        if pg is None:
            log(f"  WARN no page found for {f.get('statement', '')[:70]!r} needle={f['needle']!r}")


def finalize_entries(fid, facts, rel_path, prefix=None):
    out = []
    for i, f in enumerate(facts, start=1):
        e = {"fact_id": f"{fid}-F{i:03d}"}
        for k in ("world_ref", "kind", "statement"):
            e[k] = f.get(k)
        e["file"] = rel_path
        loc = {k: v for k, v in f["locator"].items() if not k.startswith("_")}
        e["locator"] = loc
        e["needle"] = f["needle"]
        e["exclusive"] = bool(f.get("exclusive"))
        e["also_in"] = list(f.get("also_in") or [])
        if f.get("placement"):
            e["placement"] = f["placement"]
            e["placement_key"] = f["placement_key"]
        if f.get("notes"):
            e["notes"] = f["notes"]
        f["_fact_id"] = e["fact_id"]
        out.append(e)
    return out


def check_text(path: pathlib.Path, forbidden: list[str], label: str):
    from harness import extract as X
    bad = []
    for loc, text in X.iter_units(str(path), ocr=False):
        for tok in forbidden:
            if tok.lower() in (text or "").lower():
                bad.append((tok, loc, (text or "")[:120]))
    if bad:
        for b in bad[:20]:
            log(f"  [{label}] forbidden token {b[0]!r} at {b[1]}: {b[2]!r}")
        raise SystemExit(f"{label}: {len(bad)} forbidden-token hits")


# ---------------------------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(OUT))
    ap.add_argument("--only", default="")
    args, _ = ap.parse_known_args()
    only = {x.strip() for x in args.only.split(",") if x.strip()} or set(NAMES)
    mine = only & set(NAMES)
    if not mine:
        return 0
    if "LD002" in mine:
        mine.add("LD001")          # the scan needs LD001's render
    out_dir = pathlib.Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    W = load_world()
    fig_dir = CACHE / "fig"
    entries: dict[str, list] = {}
    summary = []

    # ---------------------------------------------------------------- LD001
    if "LD001" in mine:
        a = W.anchor("LD001")
        spec = content_v72.build(W, fig_dir)
        cfg = {"header": content_v72.HEADER, "footer_prefix": content_v72.FOOTER, "title": a["title"],
               "author_name": W.name_of(a["author"], a["date"]), "date": a["date"],
               "subject": "Claims handling procedures", "keywords": "claims; manual; procedures", "tracked_id_base": 9000}
        state, starts, rep = produce("LD001", spec, cfg, 496, "ld_manual_ld001")
        info = state["info"]
        res = state["res"]
        dst = out_dir / NAMES["LD001"]
        if dst.exists():
            dst.unlink()
        shutil.copyfile(state["docx"], dst)
        normalize_zip(dst, a["date"], pages=info.pages)
        rel = util.rel(dst)
        facts = list(res.facts)
        pls = {p["placement_id"]: p for p in W.placements_for("LD001")}
        hdr = {"kind": "header", "statement": "Every page header of manual v7.2 reads 'Claims Handling Manual v7.2 — Approved 30 June 2026 — Owner: Claims Director'.",
               "needle": "Claims Handling Manual v7.2 — Approved 30 June 2026 — Owner: Claims Director",
               "world_ref": pls["PL-009"]["world_ref"], "exclusive": False, "also_in": ["LD002"], "placement": "PL-009",
               "placement_key": pls["PL-009"]["key"], "locator": {"kind": "docx_header", "section_index": 0}, "mirror": True,
               "ocr_needle": "Claims Handling Manual v7.2", "notes": "Header defined in section 0; section 1 (appendices) links to it."}
        ftr = {"kind": "footer", "statement": "Every page footer of manual v7.2 shows document ID CS-MAN-007 rev 7.2 and 'Classification: Internal'.",
               "needle": "CS-MAN-007 rev 7.2", "world_ref": pls["PL-010"]["world_ref"], "exclusive": True, "also_in": ["LD002"],
               "placement": "PL-010", "placement_key": pls["PL-010"]["key"], "locator": {"kind": "docx_footer", "section_index": 0},
               "mirror": True, "notes": "Exclusive: the document ID appears only in the footer (never in the body)."}
        hdr2 = dict(hdr, locator={"kind": "docx_header", "section_index": 1}, placement=None, mirror=False,
                    statement="The appendices section (section 1) inherits the same header text.", kind="header", also_in=[])
        ftr2 = {"kind": "footer", "statement": "The footer carries 'Classification: Internal' and a Page N of M field.",
                "needle": "Classification: Internal", "world_ref": "ANCHOR:LD001", "exclusive": False, "also_in": [],
                "locator": {"kind": "docx_footer", "section_index": 1}}
        facts = [hdr, ftr, hdr2, ftr2] + facts
        page_hints(facts, info, starts)
        # sanity: needles appear in the clean PDF only where they should (exclusive body checks)
        body_all = " ".join(info.texts)
        assert "3.1% per annum" not in body_all, "PL-011 rate leaked into the LD001 body"
        e1 = finalize_entries("LD001", facts, rel)
        entries["LD001"] = (facts, e1)
        # multipage table check (PL-007)
        cap_pg = info.find("Table 7-1: Default indemnity reserves", 80)
        eow = [f for f in facts if f.get("placement") == "PL-007"][0]
        last_row_pg = info.find("COMUK", eow["locator"]["page_hint"])
        log(f"[LD001] Table 7-1 starts p.{cap_pg}; EOW row p.{eow['locator']['page_hint']}; table ends ~p.{info.find('Replacing the default reserve', 88)}")
        # page count of the actual LD001 docx (tracked changes visible)
        pdf_real = C.render_pdf(dst, "ld_manual_ld001_real")
        real = C.PdfInfo(pdf_real)
        diffs = [h for _, h in res.headings if real.heading_page(h) != info.heading_page(h)]
        log(f"[LD001] pages: clean render {info.pages}, as-delivered render {real.pages}; heading page diffs: {len(diffs)} {diffs[:3]}")
        summary.append((dst, info.pages))
        state_ld001 = state

    # ---------------------------------------------------------------- LD002
    if "LD002" in mine:
        a2 = W.anchor("LD002")
        info = state_ld001["info"]
        facts1 = entries["LD001"][0]
        import pymupdf
        with pymupdf.open(state_ld001["pdf"]) as doc:
            p1 = doc[0]
            blocks = [b for b in p1.get_text("blocks") if b[1] > 70 and b[3] < p1.rect.height - 60]
            top_text = min(b[1] for b in blocks)
            stamp_xy = (p1.rect.width - 290, max(78, top_text - 140))
            note_pg = [f for f in facts1 if f.get("placement") == "PL-002"][0]["locator"]["page_hint"]
            pn = doc[note_pg - 1]
            bl = [b for b in pn.get_text("blocks") if b[1] > 70 and b[3] < pn.rect.height - 70]
            low = max(b[3] for b in bl)
            note_xy = (90, low + 40)
            assert note_xy[1] + 110 < pn.rect.height - 70, "no room for the margin note"
        stamp_lines = ["RECEIVED", "Claims Standards Office", "03 JUL 2026"]
        note_lines = ["T3 review 14d from 01/07 —", "agreed RC 09/06 — LK"]
        overlays = {1: [{"kind": "stamp", "x_pt": stamp_xy[0], "y_pt": stamp_xy[1], "lines": stamp_lines}],
                    note_pg: [{"kind": "note", "x_pt": note_xy[0], "y_pt": note_xy[1], "lines": note_lines}]}
        dst2 = out_dir / NAMES["LD002"]
        skey = hashlib.sha256((C.sha1(state_ld001["pdf"]) + (ROOT / "generators/long_docs/manual_lib/scan.py").read_text()
                               + json.dumps(overlays, sort_keys=True) + f"{SCAN_DPI}:{SCAN_QUALITY}").encode()).hexdigest()[:20]
        cached = CACHE / "scan" / f"{skey}.pdf"
        if not cached.exists():
            t0 = time.time()
            r = scan.make_scan(state_ld001["pdf"], cached, overlays, SCAN_DPI, SCAN_QUALITY, "LD002",
                               meta={"title": "Claims Handling Manual v7.2 (scanned signed copy)"})
            log(f"[LD002] scanned {r['pages']} pages, {r['bytes'] / 1e6:.1f} MB in {time.time() - t0:.0f}s")
        if dst2.exists():
            dst2.unlink()
        shutil.copyfile(cached, dst2)
        rel2 = util.rel(dst2)
        f2 = []
        pls2 = {p["placement_id"]: p for p in W.placements_for("LD002")}
        f2.append({"kind": "image_text", "statement": "The scanned copy carries a 'RECEIVED — Claims Standards Office — 03 JUL 2026' stamp on page 1.",
                   "needle": "Claims Standards Office", "world_ref": pls2["PL-022"]["world_ref"], "exclusive": True, "also_in": [],
                   "placement": "PL-022", "placement_key": pls2["PL-022"]["key"], "locator": {"kind": "pdf_page", "page": 1, "ocr": True},
                   "notes": "Rubber-stamp image drawn into the page-1 scan only; full stamp text: RECEIVED / Claims Standards Office / 03 JUL 2026."})
        f2.append({"kind": "image_text", "statement": "Page-1 received stamp date: 03 JUL 2026.", "needle": "03 JUL 2026",
                   "world_ref": "ANCHOR:LD002#received_stamp", "exclusive": False, "also_in": [],
                   "locator": {"kind": "pdf_page", "page": 1, "ocr": True}})
        f2.append({"kind": "image_text", "statement": f"Handwritten margin note on page {note_pg}: 'T3 review 14d from 01/07 — agreed RC 09/06 — LK'.",
                   "needle": "T3 review 14d from 01/07", "world_ref": pls2["PL-023"]["world_ref"], "exclusive": False, "also_in": [],
                   "placement": "PL-023", "placement_key": pls2["PL-023"]["key"], "locator": {"kind": "pdf_page", "page": note_pg, "ocr": True},
                   "notes": "Handwriting-style note in the blank area below §19.4 (only in the scan). Second line: 'agreed RC 09/06 — LK'."})
        f2.append({"kind": "image_text", "statement": "Second line of the handwritten note: 'agreed RC 09/06 — LK' (the Reserving Committee of 9 June 2026, DEC-008).",
                   "needle": "agreed RC 09/06", "world_ref": "DECISION:DEC-008", "exclusive": False, "also_in": [],
                   "locator": {"kind": "pdf_page", "page": note_pg, "ocr": True}})
        remap = {"header": "image_text", "footer": "image_text", "footnote": "image_text", "comment": "image_text",
                 "tracked_insert": "image_text", "tracked_delete": "image_text", "alt_text": "image_text"}
        for f in facts1:
            if not f.get("mirror"):
                continue
            pg = 2 if f["locator"]["kind"] in ("docx_header", "docx_footer") else f["locator"]["page_hint"]
            g = {"kind": remap.get(f["kind"], f["kind"]),
                 "statement": f"Scanned copy (p.{pg}): {f['statement']}",
                 "needle": f.get("ocr_needle") or f["needle"], "world_ref": f.get("world_ref"),
                 "exclusive": bool(f.get("exclusive")), "also_in": [], "locator": {"kind": "pdf_page", "page": pg, "ocr": True},
                 "_mirror_of": f}
            if f.get("placement"):
                g["placement"] = f["placement"]
                g["placement_key"] = f["placement_key"]
            note = f"OCR mirror of {f['kind']} fact in LD001."
            if f.get("notes"):
                note += " " + f["notes"]
            g["notes"] = note
            f2.append(g)
        e2 = finalize_entries("LD002", f2, rel2)
        # cross-link also_in
        for g, e in zip(f2, e2):
            src = g.get("_mirror_of")
            if src is not None:
                e["also_in"] = [src["_fact_id"]]
        e1 = entries["LD001"][1]
        by_id1 = {e["fact_id"]: e for e in e1}
        for g, e in zip(f2, e2):
            src = g.get("_mirror_of")
            if src is not None:
                ee = by_id1[src["_fact_id"]]
                ee["also_in"] = [x for x in ee["also_in"] if x != "LD002"] + [e["fact_id"]]
        for ee in e1:
            ee["also_in"] = [x if x != "LD002" else rel2 for x in ee["also_in"]]
        entries["LD002"] = (f2, e2)
        import pymupdf
        with pymupdf.open(dst2) as dd:
            summary.append((dst2, dd.page_count))

    # ---------------------------------------------------------------- LD012
    if "LD012" in mine:
        a = W.anchor("LD012")
        spec = content_v61.build(W, fig_dir)
        cfg = {"header": content_v61.HEADER, "footer_prefix": content_v61.FOOTER, "title": a["title"],
               "author_name": W.name_of(a["author"], a["date"]), "date": a["date"], "subject": "Claims handling standards",
               "keywords": "claims; manual; standards", "tracked_id_base": 7000, "toc_levels": 1, "font": "Times New Roman",
               "size": 11.5, "heading_rgb": (0x22, 0x22, 0x22)}
        state, starts, rep = produce("LD012", spec, cfg, content_v61.TOTAL, "ld_manual_ld012")
        info = state["info"]
        res = state["res"]
        dst = out_dir / NAMES["LD012"]
        if dst.exists():
            dst.unlink()
        shutil.copyfile(state["docx"], dst)
        normalize_zip(dst, a["date"], pages=info.pages)
        check_text(dst, content_v61.ANACHRONISMS, "LD012")
        rel = util.rel(dst)
        pls = {p["placement_id"]: p for p in W.placements_for("LD012")}
        hdr = {"kind": "alias_use", "statement": "Manual v6.1 header: 'Approved 15 May 2023 — Owner: Ingrid Sørensen, Claims Director'.",
               "needle": "Approved 15 May 2023 — Owner: Ingrid Sørensen, Claims Director", "world_ref": pls["PL-039"]["world_ref"],
               "exclusive": False, "also_in": [], "placement": "PL-039", "placement_key": pls["PL-039"]["key"],
               "locator": {"kind": "docx_header", "section_index": 0},
               "notes": "Uses the Claims Director's pre-2025-08-23 name (Ingrid Sørensen, now Ingrid Ashby)."}
        ftr = {"kind": "footer", "statement": "Manual v6.1 footer shows document ID CS-MAN-006 rev 6.1.", "needle": "CS-MAN-006 rev 6.1",
               "world_ref": "ANCHOR:LD012#doc_id", "exclusive": False, "also_in": [], "locator": {"kind": "docx_footer", "section_index": 0}}
        facts = [hdr, ftr] + list(res.facts)
        page_hints(facts, info, starts)
        entries["LD012"] = (facts, finalize_entries("LD012", facts, rel))
        summary.append((dst, info.pages))

    # ---------------------------------------------------------------- manifest
    man_path = util.MANIFESTS / f"{FAMILY}.facts.yaml"
    keep = []
    if man_path.exists():
        old = yaml.safe_load(man_path.read_text(encoding="utf-8")) or []
        regenerated = set(entries)
        keep = [e for e in old if e["fact_id"].split("-F")[0] not in regenerated]
    all_entries = keep + [e for fid in sorted(entries) for e in entries[fid][1]]
    util.write_manifest(FAMILY, all_entries)
    for path, units in summary:
        print(f"{util.rel(path)} {path.stat().st_size} {units}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

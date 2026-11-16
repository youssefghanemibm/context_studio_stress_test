#!/usr/bin/env python
"""Tests for harness/extract.py (and a smoke test of harness/build_index.py).

Builds tiny synthetic fixtures in build/test_fixtures/ at test time, then asserts that
resolve() returns the expected text for every locator kind, that every unit produced by
extract_all() round-trips through resolve(), and that match() normalises as documented.

    python -I harness/tests/test_extract.py          # plain asserts, no pytest needed
"""
from __future__ import annotations

import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import datetime as dt
import json
import os
import shutil
import subprocess
import time
import traceback
import zipfile

from harness import extract as X

FIX = ROOT / "build" / "test_fixtures"
TIMINGS: list[tuple[str, float]] = []


# ---------------------------------------------------------------------------------------------
# Fixture builders
# ---------------------------------------------------------------------------------------------

def text_image(path: pathlib.Path, lines: list[str], size=(1400, 500), font_size=44) -> pathlib.Path:
    from PIL import Image, ImageDraw
    from generators.common import util
    img = Image.new("RGB", size, "white")
    d = ImageDraw.Draw(img)
    f = util.font(font_size)
    for i, t in enumerate(lines):
        d.text((40, 40 + i * int(font_size * 1.6)), t, fill="black", font=f)
    img.save(path)
    return path


FOOTNOTES_XML = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<w:footnotes xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
    '<w:footnote w:type="separator" w:id="-1"><w:p><w:r><w:separator/></w:r></w:p></w:footnote>'
    '<w:footnote w:type="continuationSeparator" w:id="0"><w:p><w:r><w:continuationSeparator/></w:r></w:p></w:footnote>'
    '<w:footnote w:id="1"><w:p><w:r><w:t>Source: NISA circular 2026/04, paragraph 12.</w:t></w:r></w:p></w:footnote>'
    '</w:footnotes>')


def add_footnotes_part(path: pathlib.Path) -> None:
    """python-docx has no footnote API: add word/footnotes.xml, its rel and content type."""
    with zipfile.ZipFile(path) as z:
        items = {n: z.read(n) for n in z.namelist()}
    ct = items["[Content_Types].xml"].decode()
    ct = ct.replace("</Types>", '<Override PartName="/word/footnotes.xml" ContentType="application/'
                    'vnd.openxmlformats-officedocument.wordprocessingml.footnotes+xml"/></Types>')
    rels = items["word/_rels/document.xml.rels"].decode()
    rels = rels.replace("</Relationships>", '<Relationship Id="rIdFn1" Type="http://schemas.openxmlformats.org/'
                        'officeDocument/2006/relationships/footnotes" Target="footnotes.xml"/></Relationships>')
    items["[Content_Types].xml"] = ct.encode()
    items["word/_rels/document.xml.rels"] = rels.encode()
    items["word/footnotes.xml"] = FOOTNOTES_XML.encode()
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        for n, data in items.items():
            z.writestr(n, data)


def make_docx(path: pathlib.Path) -> dict:
    import docx
    from docx.shared import Inches
    from docx.oxml import parse_xml
    from docx.oxml.ns import nsdecls
    img = text_image(FIX / "docx_img.png", ["INVOICE TOTAL 4821 GBP", "Approved by Claims Ops"])
    doc = docx.Document()
    doc.sections[0].header.paragraphs[0].text = "Corvane header section one"
    doc.sections[0].footer.paragraphs[0].text = "Footer: internal use only"
    doc.add_heading("1 Introduction", level=1)                                     # 0
    doc.add_paragraph("The reserve review cadence is described below.")            # 1
    doc.add_heading("2 Referral rules", level=1)                                   # 2
    p = doc.add_paragraph("Fraud referral threshold is a Sentinel score of 65 or more.")  # 3
    comment = doc.add_comment(p.runs[0], text="Check with the SIU lead before publishing", author="Reviewer")
    p2 = doc.add_paragraph("Footnoted sentence about NISA reporting.")             # 4
    p2.add_run()._r.append(parse_xml('<w:footnoteReference %s w:id="1"/>' % nsdecls("w")))
    p3 = doc.add_paragraph("Tier-3 claims are reviewed every ")                    # 5
    p3._p.append(parse_xml(f'<w:del {nsdecls("w")} w:id="901" w:author="Editor" w:date="2026-03-01T00:00:00Z">'
                           '<w:r><w:delText>30 days</w:delText></w:r></w:del>'))
    p3._p.append(parse_xml(f'<w:ins {nsdecls("w")} w:id="902" w:author="Editor" w:date="2026-03-01T00:00:00Z">'
                           '<w:r><w:t>14 days</w:t></w:r></w:ins>'))
    doc.add_picture(str(img), width=Inches(5))                                     # 6
    doc.inline_shapes[0]._inline.docPr.set("descr", "Bar chart of reserve movements")
    t = doc.add_table(rows=2, cols=2)
    t.cell(0, 0).text, t.cell(0, 1).text, t.cell(1, 0).text = "Outer A", "Outer B", "Outer C"
    nt = t.cell(1, 1).add_table(rows=2, cols=2)
    nt.cell(1, 0).text = "Nested value 4417"
    sec = doc.add_section()
    sec.header.is_linked_to_previous = False
    sec.header.paragraphs[0].text = "Appendix header"
    doc.add_paragraph("Appendix text.")
    doc.save(path)
    add_footnotes_part(path)
    return {"comment_id": comment.comment_id}


def make_pptx(path: pathlib.Path) -> None:
    from pptx import Presentation
    from pptx.chart.data import CategoryChartData
    from pptx.enum.chart import XL_CHART_TYPE
    from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
    from pptx.util import Inches
    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
    s1 = prs.slides.add_slide(prs.slide_layouts[6])
    a = s1.shapes.add_shape(MSO_SHAPE.DIAMOND, Inches(1), Inches(2), Inches(3), Inches(1.5))
    a.text = "Decision: Fraud score ≥ 65?"
    b = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(8), Inches(2), Inches(3), Inches(1.5))
    b.text, b.name = "Refer to SIU", "box_siu"
    c = s1.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, 0, 0, 0, 0)
    c.begin_connect(a, 3)
    c.end_connect(b, 1)
    c.name = "cxn_yes"
    lbl = s1.shapes.add_textbox(Inches(5.5), Inches(2.3), Inches(1), Inches(0.5))
    lbl.text = "Yes"
    d = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(1), Inches(5), Inches(3), Inches(1.2))
    d.text = "Continue standard handling"
    c2 = s1.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, 0, 0, 0, 0)
    c2.begin_connect(a, 2)
    c2.end_connect(d, 0)
    c2.name = "cxn_no"
    l2 = s1.shapes.add_textbox(Inches(4.5), Inches(4), Inches(1), Inches(0.5))
    l2.text, l2.name = "No", "label:cxn_no"
    s1.notes_slide.notes_text_frame.text = "Speaker note: escalate within 2 working days"
    grp = s1.shapes.add_group_shape()
    grp.name = "systems_group"
    grp.shapes.add_textbox(Inches(9), Inches(5), Inches(3), Inches(0.5)).text = "Group member: Claims Hub"
    grp.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(9), Inches(5.6), Inches(3), Inches(0.5)).text = \
        "Group member: CLARA"

    s2 = prs.slides.add_slide(prs.slide_layouts[6])
    img = text_image(FIX / "pptx_img.png", ["RESERVE SCREEN", "Case reserve 18,250"])
    pic = s2.shapes.add_picture(str(img), Inches(0.5), Inches(0.5), width=Inches(6))
    pic._element.nvPicPr.cNvPr.set("descr", "Screenshot of the reserve screen")
    cd = CategoryChartData()
    cd.categories = ["Q1", "Q2", "Q3"]
    cd.add_series("Open claims", (120, 135.5, 98))
    gf = s2.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, Inches(7), Inches(0.5), Inches(5.5), Inches(4), cd)
    gf.chart.has_title = True
    gf.chart.chart_title.text_frame.text = "Open claims by quarter"
    tbl = s2.shapes.add_table(2, 2, Inches(7), Inches(5), Inches(5), Inches(1)).table
    tbl.cell(0, 0).text, tbl.cell(0, 1).text = "Cell A", "Cell B"
    tbl.cell(1, 0).text, tbl.cell(1, 1).text = "Tier-3", "14 days"

    # slide 3: a connector inside a moved group (child -> slide transform), and an unconnected
    # connector whose arrowhead sits at its begin point (direction reversed)
    from pptx.oxml import parse_xml
    from pptx.oxml.ns import nsdecls, qn
    s3 = prs.slides.add_slide(prs.slide_layouts[6])
    g = s3.shapes.add_group_shape()
    p1 = g.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(1), Inches(1), Inches(2), Inches(1))
    p1.text = "Intake"
    p2 = g.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(6), Inches(1), Inches(2), Inches(1))
    p2.text = "Triage"
    gc = g.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, 0, 0, 0, 0)
    gc.begin_connect(p1, 3)
    gc.end_connect(p2, 1)
    g._element.grpSpPr.find(qn("a:xfrm")).find(qn("a:off")).set("y", str(Inches(4)))   # move group down 3in
    s3.shapes.add_textbox(Inches(4), Inches(4.6), Inches(1), Inches(0.4)).text = "Hand-off"
    ap = s3.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(1), Inches(6), Inches(2), Inches(1))
    ap.text = "Approve"
    pay = s3.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(6), Inches(6), Inches(2), Inches(1))
    pay.text = "Pay"
    loose = s3.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(3), Inches(6.5), Inches(6), Inches(6.5))
    ln = loose._element.spPr.get_or_add_ln()
    ln.append(parse_xml(f'<a:headEnd {nsdecls("a")} type="triangle"/>'))
    prs.save(path)


def make_xlsx(path: pathlib.Path) -> None:
    import openpyxl
    from openpyxl.chart import BarChart, Reference
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Summary"
    ws.append(["Quarter", "Claims"])
    for q, v in (("Q1", 120), ("Q2", 135), ("Q3", 98)):
        ws.append([q, v])
    ws["B5"] = "=SUM(B2:B4)"
    ws.merge_cells("A7:C7")
    ws["A7"] = "Merged heading: reserve summary"
    ws["D2"] = 0.125
    ws["D2"].number_format = "0.0%"
    ws["E2"] = 1250000
    ws["E2"].number_format = '"£"#,##0'
    ws["F2"] = dt.date(2026, 10, 1)
    ws["F2"].number_format = "dd/mm/yyyy"
    hidden = wb.create_sheet("Secret")
    hidden["B2"] = "hidden value 777"
    hidden.sheet_state = "hidden"
    chart = BarChart()
    chart.title = "Claims per quarter"
    chart.add_data(Reference(ws, min_col=2, min_row=1, max_row=4), titles_from_data=True)
    chart.set_categories(Reference(ws, min_col=1, min_row=2, max_row=4))
    ws.add_chart(chart, "H2")
    wb.save(path)


def make_pdf_two_column(path: pathlib.Path) -> None:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import BaseDocTemplate, Frame, FrameBreak, PageBreak, PageTemplate, Paragraph
    st = getSampleStyleSheet()["BodyText"]
    w, h = A4
    m, gap = 50, 20
    colw = (w - 2 * m - gap) / 2
    doc = BaseDocTemplate(str(path), pagesize=A4, invariant=1)
    doc.addPageTemplates([PageTemplate(id="two", frames=[Frame(m, m, colw, h - 2 * m, id="c1"),
                                                          Frame(m + colw + gap, m, colw, h - 2 * m, id="c2")])])
    story = [Paragraph("Left column: claims are triaged on receipt by the intake team.", st),
             FrameBreak(),
             Paragraph("Right column: the reserve uplift is 12.5 percent for Tier-3 claims.", st),
             PageBreak(),
             Paragraph("Second page fact: the NISA filing is due on 2026-12-31.", st)]
    doc.build(story)


def make_pdf_image_only(path: pathlib.Path) -> None:
    import pymupdf
    png = text_image(FIX / "scan_page.png", ["SCANNED MEMO", "Image only fact: claim 7781 escalated",
                                             "to the Major Loss Unit on 2026-09-14."],
                     size=(1654, 2339), font_size=48)
    doc = pymupdf.open()
    page = doc.new_page(width=595, height=842)
    page.insert_image(page.rect, filename=str(png))
    doc.save(str(path))


def make_small_files() -> None:
    (FIX / "claims.csv").write_text("claim_id,status,amount\nCLM-1,open,100\nCLM-2,closed,250\n", encoding="utf-8")
    (FIX / "tickets.json").write_text(json.dumps({
        "tickets": [{"id": "T-1", "summary": "Login fails"},
                    {"id": "T-2", "summary": "Reserve screen freezes", "tags": ["ui", "reserve"]}],
        "a/b": {"c~d": 5}}, indent=1), encoding="utf-8")
    (FIX / "rules.xml").write_text(
        '<?xml version="1.0"?><rules xmlns="urn:corvane:rules"><rule id="R1"><threshold>50</threshold></rule>'
        '<rule id="R2"><name>Fraud referral</name><threshold>65</threshold></rule></rules>', encoding="utf-8")
    (FIX / "api.yaml").write_text(
        'openapi: 3.0.0\npaths:\n  /claims/{id}:\n    get:\n      summary: Fetch a claim by id\n'
        '      responses:\n        "200":\n          description: OK\n---\nkind: ConfigMap\n'
        'data:\n  fraud.threshold: "65"\nitems:\n  - name: first\n  - name: second\n', encoding="utf-8")
    (FIX / "runbook.html").write_text(
        '<html><head><title>Ops runbook</title></head><body><h1>Runbook</h1>'
        '<p class="fact">Restart the <b>claims-hub</b> pod before 06:00.</p>'
        '<img src="x.png" alt="Diagram of failover"/><table><tr><td>A1</td><td>B1</td></tr></table>'
        '<div>Loose div text about batch windows</div></body></html>', encoding="utf-8")
    (FIX / "notes.txt").write_text("\n".join(f"line {i}: filler" if i not in (3, 4) else
                                             ("line 3: the cut-over weekend" if i == 3 else "line 4: is 2027-03-06")
                                             for i in range(1, 31)) + "\n", encoding="utf-8")
    text_image(FIX / "whiteboard.png", ["WHITEBOARD", "Cut-over go/no-go at 18:00"])
    (FIX / "memo.rtf").write_text(r"{\rtf1\ansi{\fonttbl{\f0 Arial;}}\f0 Hello {\b bold} world\par "
                                  r"Threshold " + "\\" + r"u8805?65 applies\par}", encoding="ascii")
    (FIX / "mail.eml").write_text("From: a@corvane-mutual.example\nTo: b@corvane-mutual.example\n"
                                  "Subject: Reserve update\nContent-Type: text/plain; charset=utf-8\n\n"
                                  "The reserve review moves to 14 days.\n", encoding="utf-8")
    with zipfile.ZipFile(FIX / "bundle.zip", "w") as z:
        z.writestr("inner/readme.txt", "Zipped fact: archive retention is 7 years.\n")


def git(repo: pathlib.Path, *args: str, env: dict | None = None) -> None:
    e = dict(os.environ, **(env or {}))
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, env=e)


def make_code_repo(root: pathlib.Path) -> None:
    repo = root / "variant_a"
    if repo.exists():
        shutil.rmtree(repo)
    (repo / "src").mkdir(parents=True)
    git(repo, "init", "-q", "-b", "main")
    cfg = ["-c", "commit.gpgsign=false"]
    (repo / "src" / "rules.py").write_text("# rules\nFRAUD_THRESHOLD = 50\n", encoding="utf-8")
    git(repo, "add", ".")
    git(repo, *cfg, "commit", "-q", "-m", "Initial import of claims rules",
        env={"GIT_AUTHOR_NAME": "Ana Example", "GIT_AUTHOR_EMAIL": "ana@ibm-consulting.example",
             "GIT_COMMITTER_NAME": "Ana Example", "GIT_COMMITTER_EMAIL": "ana@ibm-consulting.example",
             "GIT_AUTHOR_DATE": "2026-01-05T10:00:00+00:00", "GIT_COMMITTER_DATE": "2026-01-05T10:00:00+00:00"})
    (repo / "src" / "rules.py").write_text("# rules\nFRAUD_THRESHOLD = 65\n", encoding="utf-8")
    git(repo, "add", ".")
    git(repo, *cfg, "commit", "-q", "-m", "Raise fraud threshold to 65\n\nPer referral rule review.",
        env={"GIT_AUTHOR_NAME": "Ben Example", "GIT_AUTHOR_EMAIL": "ben@ibm-consulting.example",
             "GIT_COMMITTER_NAME": "Ben Example", "GIT_COMMITTER_EMAIL": "ben@ibm-consulting.example",
             "GIT_AUTHOR_DATE": "2026-02-10T09:30:00+00:00", "GIT_COMMITTER_DATE": "2026-02-10T09:30:00+00:00"})


def build_fixtures() -> dict:
    if FIX.exists():
        shutil.rmtree(FIX)
    FIX.mkdir(parents=True)
    info = make_docx(FIX / "sample.docx")
    make_pptx(FIX / "deck.pptx")
    make_xlsx(FIX / "book.xlsx")
    make_pdf_two_column(FIX / "two_col.pdf")
    make_pdf_image_only(FIX / "scan.pdf")
    make_small_files()
    make_code_repo(FIX / "code_repo")
    return info


# ---------------------------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------------------------

def R(file: str, loc: dict, **kw) -> str:
    t0 = time.perf_counter()
    text = X.resolve(FIX / file if file else None, loc, **kw)
    TIMINGS.append((f"resolve {loc['kind']}" + (f"/{loc['where']}" if "where" in loc else "")
                    + (" (ocr)" if X.locator_needs_ocr(loc) else ""), time.perf_counter() - t0))
    return text


def RX(file: str, loc: dict) -> X.Resolved:
    return X.resolve_ex(FIX / file, loc)


def has(text: str, needle: str, fuzzy: bool = False) -> None:
    mode = "ocr_fuzzy" if fuzzy else "exact"
    assert X.match(needle, text, mode), f"needle {needle!r} not in resolved text {text!r}"


def raises(fn, exc=X.LocatorError) -> None:
    try:
        fn()
    except exc:
        return
    raise AssertionError(f"expected {exc.__name__}")


# ---------------------------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------------------------

def test_match():
    assert X.match("score of 65 or more", "a Score  of\n65 or more b")
    assert X.match("“quoted” — dash", '"quoted" - dash')
    assert X.match("score ≥ 65", "score >=65")
    assert X.match("referral", "refer­ral")
    assert X.match("referral", "refer-\nral")
    assert X.match("ﬁle", "file")                                  # NFKC ligature
    assert X.match("Tier‑3", "tier-3")                             # non-breaking hyphen
    assert not X.match("score of 66", "score of 65")
    assert not X.match("", "anything")
    assert not X.match("Sentinel score of 65", "Sentlnel score of 65")
    assert X.match("Sentinel score of 65", "the Sentlnel score of 65 applies", "ocr_fuzzy")
    assert X.match("Sentinel score of 65", "the Sentlnel scoreof 65 applies", "ocr_fuzzy")
    assert not X.match("Sentinel score of 65", "the Sentlnel sc0re 0f 65 applies", "ocr_fuzzy")  # 3 errors > 2
    assert not X.match("Major Loss Unit", "completely different words here", "ocr_fuzzy")


def test_docx(info):
    f = "sample.docx"
    has(R(f, {"kind": "docx_para", "para_index": 3}), "Sentinel score of 65 or more")
    res = RX(f, {"kind": "docx_para", "para_index": 1, "section": "2 Referral rules", "page_hint": 1})
    assert not X.match("score of 65", res.text) and X.match("score of 65", res.fallback), "section fallback"
    assert res.meta["page_hint"] == 1
    has(R(f, {"kind": "docx_para", "section": "Referral rules"}), "score of 65")
    p5 = R(f, {"kind": "docx_para", "para_index": 5})
    has(p5, "reviewed every 14 days")
    assert "30 days" not in p5, "deleted text must not appear in the paragraph"
    has(R(f, {"kind": "docx_para", "para_index": 3, "end_para_index": 4}), "65 or more. Footnoted")
    has(R(f, {"kind": "docx_table", "table_index": 0, "row": 0, "col": 1}), "Outer B")
    has(R(f, {"kind": "docx_table", "table_index": 0, "row": 1, "col": 1, "nested": [0, 1, 0]}), "Nested value 4417")
    has(R(f, {"kind": "docx_table", "table_index": 0}), "Outer C")
    has(R(f, {"kind": "docx_comment", "comment_id": info["comment_id"]}), "Check with the SIU lead")
    has(R(f, {"kind": "docx_footnote", "footnote_id": 1}), "NISA circular 2026/04")
    has(R(f, {"kind": "docx_header", "section_index": 0}), "Corvane header section one")
    has(R(f, {"kind": "docx_header", "section_index": 1}), "Appendix header")
    has(R(f, {"kind": "docx_footer", "section_index": 1}), "internal use only")  # inherited from section 0
    has(R(f, {"kind": "docx_tracked", "type": "ins", "index": 0}), "14 days")
    has(R(f, {"kind": "docx_tracked", "type": "del", "index": 0}), "30 days")
    has(R(f, {"kind": "docx_tracked", "type": "del", "id": 901}), "30 days")
    assert RX(f, {"kind": "docx_tracked", "type": "ins", "index": 0}).meta["author"] == "Editor"
    has(R(f, {"kind": "docx_alt_text", "image_index": 0}), "Bar chart of reserve movements")
    has(R(f, {"kind": "docx_image", "image_name": "image1.png", "ocr": True}), "INVOICE TOTAL 4821 GBP", fuzzy=True)
    raises(lambda: R(f, {"kind": "docx_para", "para_index": 9999}))
    raises(lambda: R(f, {"kind": "docx_comment", "comment_id": 77}))


def test_pptx():
    f = "deck.pptx"
    t = R(f, {"kind": "pptx_slide", "slide": 1, "where": "text"})
    for n in ("Decision: Fraud score ≥ 65?", "Refer to SIU", "Group member: CLARA"):
        has(t, n)
    assert R(f, {"kind": "pptx_slide", "slide": 1, "where": "text", "shape_name": "box_siu"}).strip() == "Refer to SIU"
    cx = R(f, {"kind": "pptx_slide", "slide": 1, "where": "connector"})
    has(cx, "Decision: Fraud score ≥ 65? -> Refer to SIU [label: Yes]")
    has(cx, "Decision: Fraud score >= 65? -> Continue standard handling [label: No]")
    one = R(f, {"kind": "pptx_slide", "slide": 1, "where": "connector", "shape_name": "cxn_no"})
    assert "Refer to SIU" not in one and "[label: No]" in one
    has(R(f, {"kind": "pptx_slide", "slide": 1, "where": "notes"}), "escalate within 2 working days")
    g = R(f, {"kind": "pptx_slide", "slide": 1, "where": "group"})
    has(g, "Group member: Claims Hub")
    has(g, "Group member: CLARA")
    has(R(f, {"kind": "pptx_slide", "slide": 1, "where": "group", "shape_name": "systems_group"}), "Claims Hub")
    ch = R(f, {"kind": "pptx_slide", "slide": 2, "where": "chart"})
    has(ch, "title: Open claims by quarter")
    has(ch, "Open claims: Q2=135.5")
    has(ch, "Open claims: Q1=120")
    has(R(f, {"kind": "pptx_slide", "slide": 2, "where": "alt_text"}), "Screenshot of the reserve screen")
    has(R(f, {"kind": "pptx_slide", "slide": 2, "where": "table"}), "Tier-3\t14 days")
    has(R(f, {"kind": "pptx_slide", "slide": 2, "where": "image"}), "Case reserve 18,250", fuzzy=True)
    c3 = R(f, {"kind": "pptx_slide", "slide": 3, "where": "connector"}).splitlines()
    assert c3 == ["Intake -> Triage [label: Hand-off]", "Pay -> Approve"], c3
    raises(lambda: R(f, {"kind": "pptx_slide", "slide": 4}))
    raises(lambda: R(f, {"kind": "pptx_slide", "slide": 1, "where": "text", "shape_name": "nope"}))


def test_xlsx():
    f = "book.xlsx"
    assert R(f, {"kind": "xlsx_cell", "sheet": "Summary", "cell": "B3"}) == "135"
    has(R(f, {"kind": "xlsx_cell", "sheet": "Summary", "cell": "B5"}), "=SUM(B2:B4)")
    r = RX(f, {"kind": "xlsx_cell", "sheet": "Summary", "cell": "B7"})
    has(r.text, "Merged heading: reserve summary")
    assert r.meta["merged_range"] == "A7:C7"
    r = RX(f, {"kind": "xlsx_cell", "sheet": "Secret", "cell": "B2", "hidden": True})
    has(r.text, "hidden value 777")
    assert r.meta["sheet_state"] == "hidden" and r.meta["hidden"] is True
    has(R(f, {"kind": "xlsx_cell", "sheet": "Summary", "cell": "D2"}), "12.5%")
    has(R(f, {"kind": "xlsx_cell", "sheet": "Summary", "cell": "E2"}), "£1,250,000")
    d = R(f, {"kind": "xlsx_cell", "sheet": "Summary", "cell": "F2"})
    has(d, "2026-10-01")
    has(d, "01/10/2026")
    ch = R(f, {"kind": "xlsx_chart", "sheet": "Summary", "chart_index": 0})
    has(ch, "title: Claims per quarter")
    has(ch, "Claims: Q2=135")       # openpyxl writes no cache: values come from the workbook
    raises(lambda: R(f, {"kind": "xlsx_chart", "sheet": "Summary", "chart_index": 1}))
    raises(lambda: R(f, {"kind": "xlsx_cell", "sheet": "Nope", "cell": "A1"}))


def test_pdf():
    t = R("two_col.pdf", {"kind": "pdf_page", "page": 1})
    has(t, "reserve uplift is 12.5 percent for Tier-3 claims")
    has(t, "triaged on receipt by the intake team")
    assert t.index("Left column") < t.index("Right column"), "column order"
    has(R("two_col.pdf", {"kind": "pdf_page", "page": 2}), "NISA filing is due on 2026-12-31")
    has(R("two_col.pdf", {"kind": "pdf_page", "page": 1, "end_page": 2}), "2026-12-31")
    assert R("scan.pdf", {"kind": "pdf_page", "page": 1}).strip() == ""
    has(R("scan.pdf", {"kind": "pdf_page", "page": 1, "ocr": True}), "claim 7781 escalated to the Major Loss Unit",
        fuzzy=True)
    raises(lambda: R("two_col.pdf", {"kind": "pdf_page", "page": 3}))


def test_structured():
    assert R("claims.csv", {"kind": "csv_row", "row": 2, "column": "amount"}) == "250"
    assert R("claims.csv", {"kind": "csv_row", "row": 2, "column": "Status"}) == "closed"
    has(R("claims.csv", {"kind": "csv_row", "row": 1}), "claim_id: CLM-1 | status: open")
    raises(lambda: R("claims.csv", {"kind": "csv_row", "row": 3, "column": "amount"}))
    assert R("tickets.json", {"kind": "json_pointer", "pointer": "/tickets/1/summary"}) == "Reserve screen freezes"
    assert R("tickets.json", {"kind": "json_pointer", "pointer": "/a~1b/c~0d"}) == "5"
    has(R("tickets.json", {"kind": "json_pointer", "pointer": "/tickets/1"}), "summary: Reserve screen freezes")
    assert R("rules.xml", {"kind": "xml_xpath", "xpath": "//rule[@id='R2']/threshold"}) == "65"
    assert R("rules.xml", {"kind": "xml_xpath",
                           "xpath": "//*[local-name()='rule'][@id='R2']/*[local-name()='name']"}) == "Fraud referral"
    assert R("rules.xml", {"kind": "xml_xpath", "xpath": "//rule[2]/@id"}) == "R2"
    y = "api.yaml"
    assert R(y, {"kind": "yaml_path", "path": 'paths."/claims/{id}".get.summary'}) == "Fetch a claim by id"
    assert R(y, {"kind": "yaml_path", "path": "paths./claims/{id}.get.summary"}) == "Fetch a claim by id"
    assert R(y, {"kind": "yaml_path", "path": 'paths."/claims/{id}".get.responses.200.description'}) == "OK"
    assert R(y, {"kind": "yaml_path", "path": 'data."fraud.threshold"', "doc_index": 1}) == "65"
    assert R(y, {"kind": "yaml_path", "path": "items[1].name", "doc_index": 1}) == "second"
    raises(lambda: R(y, {"kind": "yaml_path", "path": "paths.nope"}))
    assert R("runbook.html", {"kind": "html_xpath", "xpath": "//p[@class='fact']"}) == \
        "Restart the claims-hub pod before 06:00."
    assert R("runbook.html", {"kind": "html_xpath", "xpath": "//img/@alt"}) == "Diagram of failover"
    assert R("notes.txt", {"kind": "text_lines", "start": 3, "end": 4}) == \
        "line 3: the cut-over weekend\nline 4: is 2027-03-06"
    has(R("whiteboard.png", {"kind": "image_ocr"}), "Cut-over go/no-go at 18:00", fuzzy=True)
    has(R("memo.rtf", {"kind": "text_lines", "start": 1, "end": 2}), "Hello bold world Threshold ≥65")
    has(R("mail.eml", {"kind": "text_lines", "start": 1, "end": 10}), "moves to 14 days")
    has(R("bundle.zip", {"kind": "zip_member", "member": "inner/readme.txt",
                         "inner": {"kind": "text_lines", "start": 1}}), "retention is 7 years")


def test_code_repo():
    X.set_code_repo_root(FIX / "code_repo")
    try:
        assert R("", {"kind": "code_lines", "variant": "a", "path": "src/rules.py", "start": 2, "end": 2}) == \
            "FRAUD_THRESHOLD = 65"
        c = R("", {"kind": "git_commit", "variant": "a", "message_contains": "fraud threshold"})
        has(c, "Ben Example")
        has(c, "2026-02-10")
        has(c, "Per referral rule review")
        assert "Ana Example" not in c
        has(R("", {"kind": "git_commit", "variant": "a", "message_contains": "Ana Example"}), "Initial import")
        raises(lambda: R("", {"kind": "git_commit", "variant": "a", "message_contains": "no such commit"}))
        units = list(X.iter_git_units(FIX / "code_repo" / "variant_a", "a"))
        assert len(units) == 2
        cu = X.extract_all(FIX / "code_repo" / "variant_a" / "src" / "rules.py")
        assert cu and cu[0][0]["kind"] == "code_lines" and cu[0][0]["path"] == "src/rules.py"
    finally:
        X.set_code_repo_root(None)


ROUND_TRIP = ["sample.docx", "deck.pptx", "book.xlsx", "two_col.pdf", "scan.pdf", "claims.csv", "tickets.json",
              "rules.xml", "api.yaml", "runbook.html", "notes.txt", "whiteboard.png", "memo.rtf", "mail.eml",
              "bundle.zip"]


def test_extract_all_round_trip():
    """Every unit extract_all() yields must be found again by resolve() at its locator."""
    kinds = set()
    for name in ROUND_TRIP:
        t0 = time.perf_counter()
        units = X.extract_all(FIX / name)
        TIMINGS.append((f"extract_all {name} ({len(units)} units)", time.perf_counter() - t0))
        assert units, f"no units from {name}"
        for loc, text in units:
            kinds.add(loc["kind"] + (f"/{loc['where']}" if "where" in loc else ""))
            got = X.resolve(FIX / name, loc)
            assert X.normalize(text) in X.normalize(got), f"{name} {loc}: unit text not at locator"
    must = {"docx_para", "docx_table", "docx_comment", "docx_footnote", "docx_header", "docx_footer",
            "docx_tracked", "docx_alt_text", "docx_image", "pptx_slide/text", "pptx_slide/notes",
            "pptx_slide/table", "pptx_slide/chart", "pptx_slide/alt_text", "pptx_slide/group",
            "pptx_slide/connector", "pptx_slide/image", "xlsx_cell", "xlsx_chart", "pdf_page", "csv_row",
            "json_pointer", "xml_xpath", "yaml_path", "html_xpath", "text_lines", "image_ocr", "zip_member"}
    assert must <= kinds, f"extract_all missed kinds: {must - kinds}"
    hidden = [loc for loc, _ in X.extract_all(FIX / "book.xlsx") if loc.get("sheet") == "Secret"]
    assert hidden and hidden[0].get("hidden") is True
    ocr_pages = [loc for loc, _ in X.extract_all(FIX / "scan.pdf") if loc.get("ocr")]
    assert ocr_pages == [{"kind": "pdf_page", "page": 1, "ocr": True}]
    no_ocr = X.extract_all(FIX / "sample.docx", ocr=False)
    assert not any(loc["kind"] == "docx_image" for loc, _ in no_ocr)


def test_ocr_disabled():
    X.OCR_CACHE_DIR = FIX / "ocr_cache_empty"
    try:
        raises(lambda: X.resolve(FIX / "scan.pdf", {"kind": "pdf_page", "page": 1, "ocr": True}, ocr=False),
               X.OcrUnavailable)
    finally:
        X.OCR_CACHE_DIR = FIX / "ocr_cache"


def test_cli():
    py = sys.executable
    res = subprocess.run([py, "-I", str(ROOT / "harness" / "extract.py"), str(FIX / "claims.csv"),
                          "--locator", '{"kind": "csv_row", "row": 1, "column": "status"}', "--needle", "open"],
                         capture_output=True, text=True, timeout=120)
    assert res.returncode == 0 and res.stdout.strip() == "open", res.stderr
    res = subprocess.run([py, "-I", str(ROOT / "harness" / "extract.py"), str(FIX / "claims.csv"), "--all"],
                         capture_output=True, text=True, timeout=120)
    lines = [json.loads(x) for x in res.stdout.splitlines()]
    assert len(lines) == 3 and lines[2]["locator"] == {"kind": "csv_row", "row": 2}


def test_build_index_and_search():
    from harness import build_index as B
    X.set_code_repo_root(FIX / "code_repo")
    try:
        idx = FIX / "index"
        srcs = B.discover_sources(roots=[FIX], include_code=True)
        srcs = [s for s in srcs if "/index/" not in s.rel and "ocr_cache" not in s.rel
                and "/code_repo/" not in s.rel or s.kind in ("code", "git_log")]
        t0 = time.perf_counter()
        st = B.build(sources=srcs, index_dir=idx, jobs=2, verbose=False)
        TIMINGS.append((f"build_index fixtures ({st['sources']} sources, jobs=2)", time.perf_counter() - t0))
        assert not st["errors"], st["errors"]
        st2 = B.build(sources=srcs, index_dir=idx, jobs=2, verbose=False)
        assert st2["updated"] == 0 and st2["skipped"] == st["sources"], st2
        hits = B.search("Refer to SIU", index_dir=idx)
        assert any(h["file"].endswith("deck.pptx") for h in hits), hits
        hits = B.search(r"FRAUD_THRESHOLD\s*=\s*\d+", regex=True, flags=0, index_dir=idx)
        assert any(h["locator"]["kind"] == "code_lines" for h in hits), hits
        hits = B.search("Raise fraud threshold", index_dir=idx)
        assert any(h["locator"]["kind"] == "git_commit" for h in hits), hits
        hits = B.search("score of 65 or more. footnoted", index_dir=idx)  # spans two paragraphs
        assert hits, "cross-unit search"
        hits = B.search("CLM-2", index_dir=idx, files=["*.csv"])
        assert hits and all(h["file"].endswith(".csv") for h in hits), hits
    finally:
        X.set_code_repo_root(None)


def build_verify_root() -> pathlib.Path:
    """A miniature corpus with deliberate defects, for an end-to-end run of verify_corpus."""
    import yaml
    V = FIX / "vroot"
    up, rj = V / "corpus" / "upload", V / "corpus" / "rejected"
    copies = {"long_docs/LD001_sample.docx": "sample.docx", "long_docs/LD002_two_col.pdf": "two_col.pdf",
              "visuals/VS001_deck.pptx": "deck.pptx", "structured/ST001_book.xlsx": "book.xlsx",
              "structured/ST002_claims.csv": "claims.csv", "structured/ST003_tickets.json": "tickets.json",
              "structured/ST004_rules.xml": "rules.xml", "structured/ST005_api.yaml": "api.yaml",
              "text/TX001_runbook.html": "runbook.html"}
    for dst, src in copies.items():
        (up / dst).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(FIX / src, up / dst)
    fake_key = "".join(["AK", "IA"]) + "Z" * 16                    # assembled so no literal sits in source
    (up / "text" / "TX002_notes.txt").write_text(
        "Desk phone 555-0142 for the intake team.\nKnown issue: Reserve screen freezes on save.\n", encoding="utf-8")
    (up / "text" / "TX003_readme.md").write_text(
        f"# Readme\nPartner: Acme Insurance.\nBuilt on the Zebra Platform.\nconfig key = {fake_key}\n",
        encoding="utf-8")
    (up / "text" / "TX004_leak.txt").write_text("Customer ref 999-12-3456 found in log.\n", encoding="utf-8")
    (up / "guardrail").mkdir(parents=True, exist_ok=True)
    (up / "guardrail" / "GP001_probe.txt").write_text(
        "Probe file.\nContact jane.doe@example.com, NI QQ 12 34 56 C.\nPROBE-MARKER-ZX81\n", encoding="utf-8")
    rj.mkdir(parents=True, exist_ok=True)
    for src, dst in (("memo.rtf", "RJ001_memo.rtf"), ("mail.eml", "RJ002_mail.eml"),
                     ("bundle.zip", "RJ003_bundle.zip"), ("whiteboard.png", "RJ004_whiteboard.png")):
        shutil.copy(FIX / src, rj / dst)

    def fact(fid, kind, file, loc, needle, exclusive=False, **kw):
        return dict(fact_id=fid, world_ref=None, kind=kind, statement=f"statement for {fid}",
                    file=f"corpus/upload/{file}", locator=loc, needle=needle, exclusive=exclusive, also_in=[], **kw)
    facts = [
        fact("LD001-F001", "needle", "long_docs/LD001_sample.docx", {"kind": "docx_para", "para_index": 3},
             "score of 65 or more", True),
        fact("LD001-F002", "tracked_delete", "long_docs/LD001_sample.docx",
             {"kind": "docx_tracked", "type": "del", "index": 0}, "30 days"),
        fact("VS001-F001", "arrow_only", "visuals/VS001_deck.pptx", {"kind": "pptx_slide", "slide": 1,
             "where": "connector"}, "Refer to SIU [label: Yes]", True),
        fact("ST001-F001", "hidden_sheet", "structured/ST001_book.xlsx",
             {"kind": "xlsx_cell", "sheet": "Secret", "cell": "B2", "hidden": True}, "hidden value 777"),
        fact("ST001-F002", "needle", "structured/ST001_book.xlsx",
             {"kind": "xlsx_cell", "sheet": "Summary", "cell": "B3", "hidden": True}, "135"),
        fact("ST002-F001", "needle", "structured/ST002_claims.csv", {"kind": "csv_row", "row": 2, "column": "amount"},
             "250"),
        fact("ST003-F001", "needle", "structured/ST003_tickets.json",
             {"kind": "json_pointer", "pointer": "/tickets/1/summary"}, "Reserve screen freezes", True),
        fact("ST005-F001", "needle", "structured/ST005_api.yaml",
             {"kind": "yaml_path", "path": 'data."fraud.threshold"', "doc_index": 1}, "65", True),
        fact("TX001-F001", "needle", "text/TX001_runbook.html", {"kind": "html_xpath", "xpath": "//p[@class='fact']"},
             "Restart the claims-hub pod"),
        fact("LD002-F001", "needle", "long_docs/LD002_two_col.pdf", {"kind": "pdf_page", "page": 1},
             "reserve uplift is 13 percent"),
        fact("GP001-F001", "injection_probe", "guardrail/GP001_probe.txt", {"kind": "text_lines", "start": 3},
             "PROBE-MARKER-ZX81", True),
        fact("TX009-F001", "needle", "text/TX009_missing.txt", {"kind": "text_lines", "start": 1}, "anything"),
    ]
    bad = fact("TX002-F009", "needle", "text/TX002_notes.txt", {"kind": "text_lines", "start": 1}, "Desk phone")
    del bad["statement"]
    facts.append(bad)
    (V / "manifests").mkdir(parents=True, exist_ok=True)
    (V / "manifests" / "test.facts.yaml").write_text(yaml.safe_dump(facts, sort_keys=False), encoding="utf-8")
    (V / "questions").mkdir(parents=True, exist_ok=True)
    (V / "questions" / "CATEGORIES.md").write_text(
        "| category | meaning |\n|---|---|\n| `needle_long_range` | far-apart facts |\n", encoding="utf-8")
    qs = [dict(id="Q001", category="needle_long_range", dimensions=["long_doc"], question="Referral threshold?",
               expected_answer="A Sentinel score of 65 or more.", acceptable_variants=[], must_include=[["65"]],
               must_not_include=["50"], evidence=[{"fact_id": "LD001-F001"}], hops=1, ask_mode="chat",
               difficulty="easy", world_refs=[], trap=""),
          dict(id="Q002", category="bogus", question="Uplift?", expected_answer="12.5 percent",
               must_include=[["12.5"]], evidence=[{"file": "corpus/upload/long_docs/LD002_two_col.pdf",
                                                    "locator": {"kind": "pdf_page", "page": 1},
                                                    "needle": "uplift is 99 percent"}],
               ask_mode="chat", difficulty="easy")]
    (V / "questions" / "questions.yaml").write_text(yaml.safe_dump(qs, sort_keys=False), encoding="utf-8")
    (V / "world" / "data").mkdir(parents=True, exist_ok=True)
    (V / "world" / "data" / "names_denylist.yaml").write_text(
        yaml.safe_dump({"insurers": [{"name": "Acme Insurance", "reason": "sounds real"}]}), encoding="utf-8")
    files = sorted(p.relative_to(V).as_posix() for p in up.rglob("*") if p.is_file())
    (V / "batches").mkdir(parents=True, exist_ok=True)
    for name, seq in (("order_A.csv", files), ("order_B.csv", list(reversed(files)))):
        with open(V / "batches" / name, "w", encoding="utf-8") as fh:
            fh.write("batch,path\n" + "".join(f"{1 + k // 8},{p}\n" for k, p in enumerate(seq)))
    return V


def test_verify_end_to_end():
    from harness import verify_corpus as VC
    V = build_verify_root()
    rep = FIX / "verify_report.json"
    t0 = time.perf_counter()
    terms = FIX / "forbidden_terms.txt"
    terms.write_text("# test list\nZebra Platform\n", encoding="utf-8")
    code = VC.main(["--root", str(V), "--index-dir", str(V / "build" / "index"), "--jobs", "2",
                    "--json", str(rep), "--forbidden-terms", str(terms)])
    TIMINGS.append(("verify_corpus end-to-end on mini corpus", time.perf_counter() - t0))
    VC.set_root(ROOT)
    assert code == 1, "defects were planted, so the run must fail"
    data = json.loads(rep.read_text())
    items = data["items"]
    fact_status = {i["fact_id"]: i["status"] for i in items["facts"] if "fact_id" in i}
    expect = {"LD001-F001": "PASS", "LD001-F002": "PASS", "VS001-F001": "PASS", "ST001-F001": "PASS",
              "ST001-F002": "FAIL", "ST002-F001": "PASS", "ST003-F001": "PASS", "ST005-F001": "PASS",
              "TX001-F001": "PASS", "LD002-F001": "FAIL", "GP001-F001": "PASS", "TX009-F001": "FAIL",
              "TX002-F009": "FAIL"}
    assert fact_status == expect, {k: (fact_status.get(k), v) for k, v in expect.items() if fact_status.get(k) != v}

    def st(check, prefix):
        return [i["status"] for i in items[check] if i["msg"].startswith(prefix)]
    assert st("exclusivity", "ST003-F001") == ["FAIL"], items["exclusivity"]
    assert st("exclusivity", "ST005-F001") == ["WARN"]
    assert st("exclusivity", "LD001-F001") == ["PASS"] and st("exclusivity", "VS001-F001") == ["PASS"]
    assert st("questions", "Q001") == ["PASS"] and st("questions", "Q002") == ["FAIL"], items["questions"]
    q2 = next(i["msg"] for i in items["questions"] if i["msg"].startswith("Q002"))
    assert "unknown category" in q2 and "hops" in q2 and "not found" in q2, q2
    inv_fail = {i["msg"] for i in items["inventory"] if i["status"] == "FAIL"}
    assert inv_fail == {"no .doc file in corpus/upload", "no .yml file in corpus/upload"}, inv_fail
    assert sum(i["status"] == "FAIL" for i in items["rejected"]) == 6
    assert any(i["status"] == "FAIL" and "Acme Insurance" in i["msg"] for i in items["denylist"])
    assert any(i["status"] == "FAIL" and "forbidden term 'Zebra Platform'" in i["msg"] for i in items["denylist"])
    sec = [i for i in items["secrets"] if i["status"] == "FAIL"]
    assert len(sec) == 1 and "aws_access_key" in sec[0]["msg"] and "TX003" in sec[0]["msg"], sec
    g = items["guardrail"]
    assert any(i["status"] == "FAIL" and "TX004_leak" in i["msg"] for i in g), g
    assert any(i["status"] == "WARN" and "TX002_notes" in i["msg"] for i in g), g
    assert any(i["status"] == "PASS" and "injection marker" in i["msg"] for i in g), g
    assert not any("GP001" in i["msg"] and i["status"] == "FAIL" for i in g)
    assert [i["status"] for i in items["batches"]] == ["PASS", "PASS", "PASS"], items["batches"]
    rows = list(csv_rows(V / "manifests" / "files.csv"))
    assert len(rows) == 13 and all(r["sha1"] for r in rows)
    docx_row = next(r for r in rows if r["path"].endswith(".docx"))
    assert docx_row["pages_or_slides_or_rows"] not in ("", "0"), docx_row   # LibreOffice page count
    code = VC.main(["--root", str(V), "--index-dir", str(V / "build" / "index"), "--checks", "9",
                    "--max-files", "3"])
    VC.set_root(ROOT)
    assert code == 1
    code = VC.main(["--root", str(V), "--index-dir", str(V / "build" / "index"), "--family", "test",
                    "--checks", "1", "--quick"])
    VC.set_root(ROOT)
    assert code == 1   # family run still fails on its own bad facts


def csv_rows(path):
    import csv
    with open(path, newline="", encoding="utf-8") as fh:
        yield from csv.DictReader(fh)


def main() -> int:
    t0 = time.perf_counter()
    info = build_fixtures()
    TIMINGS.append(("build fixtures", time.perf_counter() - t0))
    X.OCR_CACHE_DIR = FIX / "ocr_cache"   # isolated, cold OCR cache for honest timings
    tests = [("match", test_match, ()), ("docx", test_docx, (info,)), ("pptx", test_pptx, ()),
             ("xlsx", test_xlsx, ()), ("pdf", test_pdf, ()), ("structured", test_structured, ()),
             ("code_repo", test_code_repo, ()), ("extract_all_round_trip", test_extract_all_round_trip, ()),
             ("ocr_disabled", test_ocr_disabled, ()), ("cli", test_cli, ()),
             ("build_index_and_search", test_build_index_and_search, ()),
             ("verify_end_to_end", test_verify_end_to_end, ())]
    failed = 0
    for name, fn, args in tests:
        t1 = time.perf_counter()
        try:
            fn(*args)
            print(f"PASS {name} ({time.perf_counter() - t1:.2f}s)")
        except Exception:
            failed += 1
            print(f"FAIL {name}")
            traceback.print_exc()
    print("\nTimings:")
    agg: dict[str, list[float]] = {}
    for k, v in TIMINGS:
        agg.setdefault(k, []).append(v)
    for k, vs in agg.items():
        print(f"  {k:<60} n={len(vs):<3} total={sum(vs) * 1000:8.1f} ms  max={max(vs) * 1000:7.1f} ms")
    print(f"\n{len(tests) - failed}/{len(tests)} test groups passed in {time.perf_counter() - t0:.1f}s")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

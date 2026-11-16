"""LD022 (NISA Circular 2026/04) and LD023 (NISA Circular 2024/07): formal regulator circulars (reportlab)."""
from __future__ import annotations

import datetime as dt

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (BaseDocTemplate, CondPageBreak, Frame, KeepTogether, NextPageTemplate,
                                PageBreak, PageTemplate, Paragraph, Spacer, Table, TableStyle)

from . import circulars_text as CT
from .common import W, Facts, anchor, guard, long_date, out_path, person

PAGE_W, PAGE_H = A4
NISA_GREEN = colors.HexColor("#1F4E3D")
NISA_LIGHT = colors.HexColor("#E3EDE8")
INK = colors.HexColor("#1A1A1A")
GREY = colors.HexColor("#5A5A5A")

ML, MR, MT, MB = 26 * mm, 24 * mm, 30 * mm, 26 * mm

SPEC = {
    "LD022": {"circ": "CIRC-2026-04", "pages": (16, 20)},
    "LD023": {"circ": "CIRC-2024-07", "pages": (9, 12)},
}


def _styles():
    s = {}
    s["body"] = ParagraphStyle("body", fontName="Times-Roman", fontSize=11, leading=15.8, spaceAfter=7.5,
                               textColor=INK)
    s["par"] = ParagraphStyle("par", parent=s["body"], leftIndent=46, bulletIndent=0, bulletFontName="Times-Bold",
                              bulletFontSize=11)
    s["sub"] = ParagraphStyle("sub", parent=s["par"], leftIndent=58, bulletIndent=12, bulletFontName="Times-Roman")
    s["ul"] = ParagraphStyle("ul", parent=s["body"], leftIndent=64, bulletIndent=50, spaceAfter=4)
    s["h1"] = ParagraphStyle("h1", fontName="Helvetica-Bold", fontSize=13.5, leading=17, spaceBefore=14,
                             spaceAfter=8, textColor=NISA_GREEN)
    s["h2"] = ParagraphStyle("h2", fontName="Helvetica-Bold", fontSize=10.5, leading=13.5, spaceBefore=8,
                             spaceAfter=5, textColor=INK)
    s["cell"] = ParagraphStyle("cell", fontName="Helvetica", fontSize=8.8, leading=11)
    s["cellb"] = ParagraphStyle("cellb", fontName="Helvetica-Bold", fontSize=8.8, leading=11, textColor=colors.white)
    s["tabtitle"] = ParagraphStyle("tabtitle", fontName="Helvetica-Bold", fontSize=9.2, leading=12, spaceBefore=4,
                                   spaceAfter=4, textColor=NISA_GREEN)
    s["quote"] = ParagraphStyle("quote", fontName="Times-Italic", fontSize=10.5, leading=14.5, leftIndent=30,
                                rightIndent=20, spaceAfter=6, textColor=INK)
    s["cover_org"] = ParagraphStyle("cover_org", fontName="Helvetica-Bold", fontSize=12, leading=15,
                                    textColor=NISA_GREEN, spaceAfter=40)
    s["cover_ref"] = ParagraphStyle("cover_ref", fontName="Helvetica", fontSize=16, leading=20, textColor=GREY,
                                    spaceAfter=6)
    s["cover_title"] = ParagraphStyle("cover_title", fontName="Helvetica-Bold", fontSize=26, leading=31,
                                      textColor=INK, spaceAfter=26)
    s["cover_sum"] = ParagraphStyle("cover_sum", fontName="Times-Roman", fontSize=11.5, leading=16, spaceAfter=8)
    s["toc"] = ParagraphStyle("toc", fontName="Helvetica", fontSize=10.5, leading=17)
    s["sign"] = ParagraphStyle("sign", parent=s["body"], spaceAfter=2)
    return s


def _table(rows, widths, S, title=None):
    data = []
    for ri, row in enumerate(rows):
        st = S["cellb"] if ri == 0 else S["cell"]
        data.append([Paragraph(str(c), st) for c in row])
    t = Table(data, colWidths=[w * mm for w in widths], repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NISA_GREEN),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#9DB5AA")),
        ("TOPPADDING", (0, 0), (-1, -1), 3.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ] + [("BACKGROUND", (0, r), (-1, r), NISA_LIGHT) for r in range(2, len(rows), 2)]))
    out = []
    if title:
        out.append(Paragraph(title, S["tabtitle"]))
    out.append(t)
    out.append(Spacer(1, 8))
    return out


def _flow(blocks, S):
    story = []
    for b in blocks:
        k = b[0]
        if k == "h1":
            if b[1].startswith("Annex") and not (story and isinstance(story[-1], PageBreak)):
                story.append(PageBreak())
            else:
                story.append(CondPageBreak(60 * mm))
            story.append(Paragraph(b[1], S["h1"]))
        elif k == "h2":
            story.append(CondPageBreak(30 * mm))
            story.append(Paragraph(b[1], S["h2"]))
        elif k == "par":
            num, tag, text = b[1], b[2], b[3]
            style = S["sub"] if num.count(".") >= 2 else S["par"]
            label = f"{num} {tag}" if style is S["par"] else f"{num}"
            txt = text if tag != "R" else f"<b>{text}</b>"
            if style is S["sub"]:
                txt = f"<font name='Helvetica-Oblique' size='8.5' color='#5A5A5A'>{tag}</font>&nbsp;&nbsp;{text}"
            story.append(Paragraph(txt, style, bulletText=label))
        elif k == "p":
            story.append(Paragraph(b[1], S["body"]))
        elif k == "ul":
            for it in b[1]:
                story.append(Paragraph(it, S["ul"], bulletText="•"))
        elif k == "table":
            story.extend(_table(b[2], b[3], S, b[1]))
        elif k == "quote":
            story.append(Spacer(1, 4))
            for line in b[1]:
                story.append(Paragraph(line, S["quote"]))
        elif k == "pb":
            story.append(PageBreak())
    return story


class _Doc(BaseDocTemplate):
    pass


def _render(path, an, circ, content, author, S, total_pages):
    ref = circ["ref"]
    short = ref.replace("NISA ", "")

    def cover(canv, doc):
        canv.saveState()
        canv.setFillColor(NISA_GREEN)
        canv.rect(0, PAGE_H - 22 * mm, PAGE_W, 22 * mm, stroke=0, fill=1)
        canv.rect(0, 0, 9 * mm, PAGE_H, stroke=0, fill=1)
        canv.setFillColor(colors.white)
        canv.setFont("Helvetica-Bold", 10)
        canv.drawString(ML, PAGE_H - 13 * mm, "NISA")
        canv.setFont("Helvetica", 8.5)
        canv.drawRightString(PAGE_W - MR, PAGE_H - 13 * mm, "nisa.example")
        canv.setFillColor(GREY)
        canv.setFont("Helvetica", 7.5)
        canv.drawString(ML, 14 * mm, f"{ref}  |  Published {long_date(circ['published'])}")
        canv.restoreState()

    def body(canv, doc):
        canv.saveState()
        canv.setFont("Helvetica", 8)
        canv.setFillColor(NISA_GREEN)
        canv.drawString(ML, PAGE_H - 16 * mm, "National Insurance Supervisory Authority")
        canv.drawRightString(PAGE_W - MR, PAGE_H - 16 * mm, short)
        canv.setStrokeColor(NISA_GREEN)
        canv.setLineWidth(0.6)
        canv.line(ML, PAGE_H - 18.5 * mm, PAGE_W - MR, PAGE_H - 18.5 * mm)
        canv.setFillColor(GREY)
        canv.setFont("Helvetica", 7.5)
        canv.drawString(ML, 14 * mm, f"{ref} – {circ['title']}")
        canv.drawRightString(PAGE_W - MR, 14 * mm, f"Page {doc.page} of {total_pages}")
        canv.restoreState()

    doc = _Doc(str(path), pagesize=A4, leftMargin=ML, rightMargin=MR, topMargin=MT, bottomMargin=MB,
               title=f"{ref} – {circ['title']}", author=author["name"], subject=circ["title"],
               creator="NISA publishing", keywords=f"{ref}; circular", invariant=1)
    fr = Frame(ML, MB, PAGE_W - ML - MR, PAGE_H - MT - MB, id="body", leftPadding=0, rightPadding=0,
               topPadding=0, bottomPadding=0)
    doc.addPageTemplates([PageTemplate(id="cover", frames=[fr], onPage=cover),
                          PageTemplate(id="body", frames=[fr], onPage=body)])
    story = [Spacer(1, 18 * mm), Paragraph("NATIONAL INSURANCE SUPERVISORY AUTHORITY", S["cover_org"]),
             Paragraph(f"Circular {short.split(' ')[-1]}", S["cover_ref"]),
             Paragraph(circ["title"], S["cover_title"])]
    meta = [("Reference", ref), ("Published", long_date(circ["published"])),
            ("Effective", long_date(circ["effective"])),
            ("Addressed to", "All insurers supervised by the Authority that handle general insurance claims, "
                             "including UK-headquartered insurers in respect of their Nordic branches"),
            ("Status", "Paragraphs marked R are requirements and apply from the effective date. Paragraphs marked G "
                       "are guidance."),
            ("Contact", f"{author['name']}, {author['title']} ({author['email']})")]
    mt = Table([[Paragraph(f"<b>{a}</b>", S["cell"]), Paragraph(b, S["cell"])] for a, b in meta],
               colWidths=[32 * mm, PAGE_W - ML - MR - 32 * mm])
    mt.setStyle(TableStyle([("LINEBELOW", (0, 0), (-1, -1), 0.4, colors.HexColor("#9DB5AA")),
                            ("VALIGN", (0, 0), (-1, -1), "TOP"), ("TOPPADDING", (0, 0), (-1, -1), 5),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 5)]))
    story += [mt, Spacer(1, 12 * mm), Paragraph("<b>Summary</b>", S["h2"]), Paragraph(content["summary"], S["cover_sum"]),
              NextPageTemplate("body"), PageBreak()]
    # contents
    story.append(Paragraph("Contents", S["h1"]))
    for b in content["blocks"]:
        if b[0] == "h1":
            story.append(Paragraph(b[1], S["toc"]))
    story.append(PageBreak())
    story += _flow(content["blocks"], S)
    story += [Spacer(1, 14), KeepTogether([
        Paragraph(f"Issued on {long_date(circ['published'])} by the National Insurance Supervisory Authority.", S["sign"]),
        Spacer(1, 10), Paragraph(f"<b>{author['name']}</b>", S["sign"]), Paragraph(author["title"], S["sign"])])]
    doc.build(story)
    return doc.page


def build(fid):
    sp = SPEC[fid]
    an = anchor(fid)
    circ = W.circulars[sp["circ"]]
    guard(fid, f"CIRCULAR:{sp['circ']}", "requirements")
    guard(fid, f"CIRCULAR:{sp['circ']}", "effective")
    # Clarifications (CIRC-2026-04, 2026-01-14) post-date the circular and are exclusive to VS014: never stated.
    when = an["date"]
    assert str(circ["published"]) == str(when)
    name, title = person(an["author"], when)
    author = {"name": name, "title": title, "email": W.people[an["author"]]["email"]}
    req = {r["para"]: r["text"] for r in circ["requirements"]}
    if fid == "LD022":
        fr1 = W.reports["NISA-FR1"]
        guard(fid, "REPORT:NISA-FR1", "first_due")
        first_due = dt.date.fromisoformat(str(fr1["first_due"]))
        sched = [("Quarter", "Reporting period", "Return due")]
        qs = [("Q2 2026", "1 April – 30 June 2026", dt.date(2026, 7, 30)),
              ("Q3 2026", "1 July – 30 September 2026", dt.date(2026, 10, 30)),
              ("Q4 2026", "1 October – 31 December 2026", dt.date(2027, 1, 30)),
              ("Q1 2027", "1 January – 31 March 2027", dt.date(2027, 4, 30))]
        assert qs[0][2] == first_due
        for q, per, due in qs:
            sched.append((q, per, long_date(due)))
        related = []
        for cid, why in (("CIRC-2024-07", "The acknowledgement of a first notice of loss is separate from the notice "
                                          "under paragraph 3.2"),
                         ("CIRC-2025-02", "Payment disruption tolerances continue to apply to claims paid after a "
                                          "referral is concluded"),
                         ("CIRC-2025-11", "Retention and minimisation of claim records, including referral records")):
            c = W.circulars[cid]
            guard(fid, f"CIRCULAR:{cid}", "effective")
            if str(c["published"]) > str(when):
                continue
            related.append((c["ref"].replace("NISA ", ""), c["title"], long_date(c["effective"]), why))
        content = CT.circ_2026_04(req, author, {"first_due_long": long_date(first_due), "schedule_rows": sched},
                                  related)
    else:
        content = CT.circ_2024_07(req, author)
    S = _styles()
    out = out_path(fid)
    out.parent.mkdir(parents=True, exist_ok=True)
    n = _render(out, an, circ, content, author, S, total_pages=0)
    n = _render(out, an, circ, content, author, S, total_pages=n)
    lo, hi = sp["pages"]
    if not lo <= n <= hi:
        raise RuntimeError(f"{fid}: {n} pages, expected {lo}-{hi}")
    facts = _facts(fid, out, circ, req, author)
    return out, facts


def _page_texts(path):
    import pymupdf
    with pymupdf.open(str(path)) as d:
        return [p.get_text("text") for p in d]


def _find(X, texts, needle, after=1):
    for i in range(after - 1, len(texts)):
        if X.match(needle, texts[i]):
            return i + 1
    raise RuntimeError(f"needle not found: {needle!r}")


def _facts(fid, out, circ, req, author):
    from harness import extract as X
    texts = _page_texts(out)
    facts = Facts(fid)
    cref = f"CIRCULAR:{circ['id']}"
    body_start = 3   # pages 1-2 are the cover and the contents

    def add(kind, statement, needle, world_ref, pl=None, after=body_start, notes=None, **kw):
        page = _find(X, texts, needle, after=after)
        loc = {"kind": "pdf_page", "page": page}
        if pl:
            return facts.placement(pl, needle, loc, statement=statement, notes=notes, **kw)
        return facts.add(kind, statement, needle, loc, world_ref=world_ref, notes=notes, **kw)

    from .common import placements
    pls = placements(fid)
    if fid == "LD022":
        add(None, "NISA Circular 2026/04 §3.3: score-based referral cut-offs must be calibrated and documented; on a "
                  "0-100 scale the cut-off must not exceed 65.", "on a 0–100 scale the cut-off must not exceed 65",
            None, pl=pls["ld22_cutoff"], notes="requirement paragraph 3.3 (marked R) in Section 3")
        add(None, "NISA Circular 2026/04 §3.2: written notice to the customer within 10 business days of referral; may "
                  "be deferred for up to 60 days where a tipping-off risk is certified.",
            "within 10 business days of referral that the claim is subject to additional checks", None,
            pl=pls["ld22_notice"], notes="requirement paragraph 3.2; the 60-day deferral is in the same sentence")
        add("needle", "NISA Circular 2026/04 §3.2: the customer notice may be deferred for up to 60 days where a "
                      "tipping-off risk is certified.", "may be deferred for up to 60 days where a tipping-off risk is "
            "certified", f"{cref}#requirements.3.2", placement_key="ld22_notice")
        add(None, "NISA Circular 2026/04 §3.4: submit the quarterly NISA-FR1 fraud referral return within 30 days after "
                  "each quarter end.", "Submit the quarterly NISA-FR1 fraud referral return within 30 days after each "
            "quarter end", None, pl=pls["ld22_fr1"], notes="requirement paragraph 3.4")
        add("needle", "NISA Circular 2026/04 §3.1: no claim may be declined, reduced or repudiated on the basis of an "
                      "automated score alone; a documented human review is required.",
            "No claim may be declined, reduced or repudiated on the basis of an automated score alone",
            f"{cref}#requirements.3.1")
        add("needle", "NISA Circular 2026/04 §3.5: retain referral records for 7 years.", "Retain referral records for 7 "
            "years", f"{cref}#requirements.3.5")
        add("temporal", "NISA Circular 2026/04 is effective from 1 April 2026.", "Effective 1 April 2026",
            f"{cref}#effective", after=1, notes="cover page metadata table")
        add("general", "NISA Circular 2026/04 was published on 20 November 2025.", "Published 20 November 2025",
            f"{cref}#published", after=1)
        add("general", f"The contact for NISA Circular 2026/04 is {author['name']}, {author['title']}.",
            f"{author['name']}, {author['title']}", "PERSON:P056", after=1)
        add("temporal", "The first NISA-FR1 return covers the quarter ending 30 June 2026 and is due on 30 July 2026.",
            "The first return covers the quarter ending 30 June 2026 and is due on 30 July 2026",
            "REPORT:NISA-FR1#first_due")
        add("general", "NISA Circular 2026/04: a score scale other than 0-100 must be mapped to the ceiling in §3.3.",
            "uses a scale other than 0–100, the firm should document how its cut-off corresponds to the ceiling",
            f"{cref}#requirements.3.3", notes="guidance 3.3.2")
        add("general", "NISA Circular 2026/04: the §3.2 notice is separate from the FNOL acknowledgement required by "
                       "Circular 2024/07.", "is separate from the acknowledgement of a first notice of loss required by "
            "NISA Circular 2024/07", "CIRCULAR:CIRC-2024-07", notes="guidance 3.2.4: cross-reference between circulars")
        add("general", "NISA-FR1 return for Q3 2026 (1 July - 30 September 2026) is due "
            "on 30 October 2026.", "Q3 2026 1 July – 30 September 2026 30 October 2026", "REPORT:NISA-FR1#due",
            notes="Table 1 in Section 6 (reporting periods and due dates)")
        add("general", "NISA Circular 2026/04 cross-refers to NISA Circular 2025/11, Claims Data Retention and "
                       "Minimisation.", "NISA Circular 2025/11 (Claims Data Retention and Minimisation)",
            "CIRCULAR:CIRC-2025-11#title", notes="paragraph 1.5; also listed in Annex G")
        add("general", "Annex G of Circular 2026/04 lists Circular 2025/02, Operational Resilience for Claims Payment, "
                       "effective 1 July 2025.", "Operational Resilience for Claims Payment",
            "CIRCULAR:CIRC-2025-02#effective", notes="Annex G related publications table")
    else:
        add("needle", "NISA Circular 2024/07 §2.1: acknowledge every first notice of loss within 2 business days.",
            "Acknowledge every first notice of loss within 2 business days.", f"{cref}#requirements.2.1",
            notes="requirement paragraph 2.1 (marked R); contrast the 2012 Motor UK wording's 5 working days (C11)")
        add("needle", "NISA Circular 2024/07 §2.4: submit the annual NISA-CT1 claims timeliness return by 31 March "
                      "each year.", "Submit the annual NISA-CT1 claims timeliness return by 31 March each year",
            f"{cref}#requirements.2.4")
        add("temporal", "NISA Circular 2024/07 is effective from 1 October 2024.", "Effective 1 October 2024",
            f"{cref}#effective", after=1, notes="cover page metadata table")
        add("general", "NISA Circular 2024/07 was published on 28 June 2024.", "Published 28 June 2024",
            f"{cref}#published", after=1)
        add("general", f"The contact for NISA Circular 2024/07 is {author['name']}, {author['title']}.",
            f"{author['name']}, {author['title']}", "PERSON:P055", after=1)
        add("general", "NISA Circular 2024/07: the acknowledgement requirement applies whatever the policy wording says.",
            "The requirement in paragraph 2.1 applies whatever the policy wording says", f"{cref}#requirements.2.1",
            notes="guidance 3.4; relevant to the older wordings that promise longer acknowledgement periods")
    return facts

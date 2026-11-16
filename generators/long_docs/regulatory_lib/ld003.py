"""LD003: NISA Annual Claims & Reserving Filing 2025 (150-page multi-column PDF)."""
from __future__ import annotations

import math

from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import CondPageBreak, KeepTogether, Paragraph, Spacer, Table, TableStyle

from . import ld003_text as T
from .common import (W, Deck, Facts, guard, long_date, may, out_path, person, placements, rule_text,
                     seeded)
from .pdfkit import FootnoteBlock, Packer, PageRec, TemplateSpec, build_pdf
from .rlstyle import (GREY, NAVY, PAGE_H, PAGE_W, TEAL, TEAL_LIGHT, bar_chart, gantt, grid_table,
                      kv_table, line_chart, pie_chart, styles)

FID = "LD003"
DATE = "2026-03-31"
FY = "2025"
TOTAL_PAGES = 150
HEADER_TEXT = "Corvane Mutual Insurance Society Limited — NISA-FRN 40417"

ML = 50
MR = 50
TOP = PAGE_H - 62
BOT = 52
FW = PAGE_W - ML - MR
FH = TOP - BOT
GUT2 = 16
GUT3 = 12
CW2 = (FW - GUT2) / 2
CW3 = (FW - 2 * GUT3) / 3
SECT_H = 150

S = styles()


def _decorate(canv, doc):
    canv.saveState()
    canv.setFont("Helvetica", 7.4)
    canv.setFillColor(NAVY)
    canv.drawString(ML, PAGE_H - 36, HEADER_TEXT)
    canv.drawRightString(PAGE_W - MR, PAGE_H - 36, "Annual Claims & Reserving Filing 2025")
    canv.setStrokeColor(TEAL)
    canv.setLineWidth(0.6)
    canv.line(ML, PAGE_H - 41, PAGE_W - MR, PAGE_H - 41)
    canv.line(ML, 38, PAGE_W - MR, 38)
    canv.setFont("Helvetica", 6.8)
    canv.setFillColor(GREY)
    canv.drawString(ML, 28, "NISA-AFR | Financial year 2025 | Filed 31 March 2026")
    canv.drawCentredString(PAGE_W / 2, 28, "Restricted — Supervisory")
    canv.drawRightString(PAGE_W - MR, 28, f"Page {doc.page} of {TOTAL_PAGES}")
    canv.restoreState()


def _decorate_cover(canv, doc):
    canv.saveState()
    canv.setFillColor(TEAL)
    canv.rect(0, PAGE_H - 250, PAGE_W, 250, stroke=0, fill=1)
    canv.setFillColor(colors.HexColor("#20A39E"))
    canv.rect(0, PAGE_H - 258, PAGE_W, 8, stroke=0, fill=1)
    canv.setFont("Helvetica", 7.4)
    canv.setFillColor(colors.white)
    canv.drawString(ML, PAGE_H - 36, HEADER_TEXT)
    canv.drawRightString(PAGE_W - MR, PAGE_H - 36, "Annual Claims & Reserving Filing 2025")
    canv.setFont("Helvetica-Bold", 30)
    canv.drawString(ML, PAGE_H - 130, "Annual Claims &")
    canv.drawString(ML, PAGE_H - 166, "Reserving Filing 2025")
    canv.setFont("Helvetica", 12)
    canv.drawString(ML, PAGE_H - 200, "Financial year ended 31 December 2025")
    canv.drawString(ML, PAGE_H - 218, "Submitted to the National Insurance Supervisory Authority")
    canv.setFillColor(GREY)
    canv.setFont("Helvetica", 6.8)
    canv.drawCentredString(PAGE_W / 2, 28, "Restricted — Supervisory")
    canv.drawRightString(PAGE_W - MR, 28, f"Page {doc.page} of {TOTAL_PAGES}")
    canv.restoreState()


TEMPLATES = {
    "cover": TemplateSpec("cover", [(ML, BOT, FW, PAGE_H - 290 - BOT)], _decorate_cover),
    "full": TemplateSpec("full", [(ML, BOT, FW, FH)], _decorate),
    "two": TemplateSpec("two", [(ML, BOT, CW2, FH), (ML + CW2 + GUT2, BOT, CW2, FH)], _decorate),
    "three": TemplateSpec("three", [(ML, BOT, CW3, FH), (ML + CW3 + GUT3, BOT, CW3, FH),
                                    (ML + 2 * (CW3 + GUT3), BOT, CW3, FH)], _decorate),
    "sect": TemplateSpec("sect", [(ML, TOP - SECT_H, FW, SECT_H), (ML, BOT, CW2, FH - SECT_H - 10),
                                  (ML + CW2 + GUT2, BOT, CW2, FH - SECT_H - 10)], _decorate),
    "sect3": TemplateSpec("sect3", [(ML, TOP - SECT_H, FW, SECT_H), (ML, BOT, CW3, FH - SECT_H - 10),
                                    (ML + CW3 + GUT3, BOT, CW3, FH - SECT_H - 10),
                                    (ML + 2 * (CW3 + GUT3), BOT, CW3, FH - SECT_H - 10)], _decorate),
}
AFTER_SECT = {"sect": "two", "sect3": "three"}


# ---------------------------------------------------------------------------------------------
# Data (deterministic; world totals where the world defines them)
# ---------------------------------------------------------------------------------------------

def _split_int(total, weights):
    raw = [total * w / sum(weights) for w in weights]
    out = [int(math.floor(x)) for x in raw]
    rem = total - sum(out)
    order = sorted(range(len(raw)), key=lambda i: -(raw[i] - out[i]))
    for i in order[:rem]:
        out[i] += 1
    return out


def _split_tenths(total, weights):
    t = int(round(total * 10))
    return [v / 10 for v in _split_int(t, weights)]


class Data:
    def __init__(self):
        r = seeded("LD003:data")
        self.r = r
        fin = W.get("ORG:company")["financials"]["fy2025"] if W.get("ORG:company") else None
        self.fin = fin
        profile = {}
        import yaml
        from .common import ROOT
        prof = yaml.safe_load((ROOT / "world/data/claims_profile.yaml").read_text())
        self.profile = prof
        self.products = list(W.get(f"PRODUCT:{p}") for p in prof["products"])
        self.prod_ids = list(prof["products"].keys())
        shares = list(prof["products"].values())
        self.notified = dict(zip(self.prod_ids, _split_int(fin["claims_notified"], shares)))
        # monthly pattern
        motor_w = [1.04, 0.97, 1.0, 0.95, 0.98, 0.97, 1.0, 1.02, 0.99, 1.01, 1.03, 1.08]
        home_w = [1.22, 1.15, 1.02, 0.86, 0.82, 0.8, 0.84, 0.86, 0.9, 1.0, 1.16, 1.37]
        self.monthly = {}
        for pid in self.prod_ids:
            line = W.get(f"PRODUCT:{pid}")["line"]
            base = home_w if line in ("Home", "Commercial Property") else motor_w
            wts = [b * (1 + r.uniform(-0.035, 0.035)) for b in base]
            self.monthly[pid] = _split_int(self.notified[pid], wts)
        # peril split
        ctw = prof["claim_type_weights"]
        self.peril = {}
        for pid in self.prod_ids:
            prod = W.get(f"PRODUCT:{pid}")
            weights = ctw[prod["line"]]
            cts = [c for c in prod["claim_types"] if c in weights]
            self.peril[pid] = dict(zip(cts, _split_int(self.notified[pid], [weights[c] for c in cts])))
        # technical provisions (case + IBNR) by reserving class
        self.classes = ["Motor Private UK", "Home Buildings & Contents UK", "Commercial Property UK",
                        "SME Liability UK", "Nordic Motor (NO/SE/DK)", "Nordic Home (NO/SE/DK)"]
        tp = fin["claims_outstanding_technical_provisions_gbp_m"]
        ibnr = fin["ibnr_gbp_m"]
        case = round(tp - ibnr, 1)
        self.tp, self.ibnr, self.case = tp, ibnr, case
        self.case_by = _split_tenths(case, [31.4, 16.6, 14.2, 21.3, 9.9, 6.6])
        self.ibnr_by = _split_tenths(ibnr, [29.6, 12.8, 11.9, 32.2, 7.7, 5.8])
        # accident year splits per class
        self.ays = list(range(2014, 2026))
        tail = {"Motor Private UK": 0.62, "Home Buildings & Contents UK": 0.48, "Commercial Property UK": 0.66,
                "SME Liability UK": 0.84, "Nordic Motor (NO/SE/DK)": 0.6, "Nordic Home (NO/SE/DK)": 0.45}
        self.ay_case, self.ay_ibnr = {}, {}
        for i, c in enumerate(self.classes):
            k = tail[c]
            w_case = [k ** (2025 - y) * (1 + r.uniform(-0.08, 0.08)) for y in self.ays]
            w_ibnr = [(k * 0.82) ** (2025 - y) * (1 + r.uniform(-0.08, 0.08)) for y in self.ays]
            self.ay_case[c] = _split_tenths(self.case_by[i], w_case)
            self.ay_ibnr[c] = _split_tenths(self.ibnr_by[i], w_ibnr)
        # triangles (paid cumulative, GBP m)
        patterns = {
            "Motor Private UK": [0.52, 0.78, 0.89, 0.94, 0.968, 0.982, 0.99, 0.995, 0.998, 1.0],
            "Home Buildings & Contents UK": [0.66, 0.9, 0.96, 0.985, 0.994, 0.998, 1.0, 1.0, 1.0, 1.0],
            "Commercial Property UK": [0.41, 0.72, 0.86, 0.93, 0.965, 0.983, 0.992, 0.997, 0.999, 1.0],
            "SME Liability UK": [0.16, 0.37, 0.55, 0.69, 0.8, 0.88, 0.93, 0.965, 0.985, 1.0],
            "Nordic Motor (NO/SE/DK)": [0.55, 0.8, 0.9, 0.95, 0.972, 0.985, 0.992, 0.996, 0.999, 1.0],
            "Nordic Home (NO/SE/DK)": [0.7, 0.92, 0.97, 0.988, 0.995, 0.998, 1.0, 1.0, 1.0, 1.0],
        }
        base_ult = {"Motor Private UK": 405.0, "Home Buildings & Contents UK": 236.0,
                    "Commercial Property UK": 118.0, "SME Liability UK": 72.0,
                    "Nordic Motor (NO/SE/DK)": 151.0, "Nordic Home (NO/SE/DK)": 96.0}
        self.tri_years = list(range(2016, 2026))
        self.tri = {}
        for c in self.classes:
            rows = []
            for y in self.tri_years:
                ult = base_ult[c] * (1.035 ** (y - 2016)) * (1 + r.uniform(-0.06, 0.06))
                devs = []
                for dv in range(1, 11):
                    if y + dv - 1 > 2025:
                        devs.append(None)
                    else:
                        noise = 1 + r.uniform(-0.012, 0.012) if dv < 10 else 1
                        devs.append(round(ult * patterns[c][dv - 1] * noise, 1))
                for k in range(1, len(devs)):  # cumulative must not fall
                    if devs[k] is not None and devs[k - 1] is not None and devs[k] < devs[k - 1]:
                        devs[k] = devs[k - 1]
                rows.append(devs)
            self.tri[c] = rows
        # complaints (invented operational counts)
        self.complaint_cats = ["Delay in handling", "Claim outcome / decline", "Settlement amount",
                               "Communication", "Repair quality", "Assessor conduct", "Excess deduction",
                               "Hire vehicle", "Alternative accommodation", "Fraud investigation",
                               "Payment error", "Data protection", "Vulnerability handling", "Other"]
        self.complaints = {}
        for cat in self.complaint_cats:
            base = r.randint(40, 420)
            self.complaints[cat] = [max(3, int(base / 12 * r.uniform(0.7, 1.3))) for _ in range(12)]
        # reserve movement counts by quarter and reason code
        self.rsn_codes = [("NEW", "Initial reserve"), ("INF", "New information"), ("ASR", "Assessor report"),
                          ("LIT", "Litigation"), ("INX", "Indexation"), ("REO", "Reopened claim"),
                          ("SET", "Final settlement"), ("PRT", "Partial payment"), ("REC", "Recovery netting"),
                          ("FXR", "Currency revaluation"), ("COR", "Correction"), ("TRF", "Transfer between types")]


# ---------------------------------------------------------------------------------------------
# Builder helpers
# ---------------------------------------------------------------------------------------------

class Ctx:
    def __init__(self):
        self.deck = Deck("LD003:text")
        self.facts = Facts(FID)
        self.data = Data()
        self.headings = []      # (level, text, page)
        self.tables = []        # (label, page)
        self.figures = []
        self.marks = {}


def heading(pk, ctx, text, level=2, min_after=46):
    st = {1: S["h1"], 2: S["h2"], 3: S["h3"]}[level]
    p = Paragraph(text, st)
    if not pk.frame_empty() and pk.remaining() < pk.height_of(p) + min_after:
        pk.next_frame()
    placed = pk.add(p)
    pg = placed[0][0]
    if level <= 2:
        ctx.headings.append((level, text, pg))
    return pg


def para(pk, text, style="body"):
    return pk.add(Paragraph(text, S[style]))


def filler(pk, ctx, topic, n=1, extra=()):
    for _ in range(n):
        pk.add(Paragraph(T.paragraph(ctx.deck, topic, 3, 6, extra), S["body"]))


def fill_to(pk, ctx, end_page, topic, extra=(), subheads=True):
    """Fill with topic prose until the last frame of ``end_page`` is (nearly) full."""
    deck = ctx.deck
    heads = list(T.SUBHEADS.get(topic, []))
    since_head = 0
    while True:
        if pk.page_no > end_page:
            raise RuntimeError(f"LD003 segment overflow past page {end_page}")
        last = pk.page_no == end_page and pk.is_last_frame()
        if last and pk.remaining() < 2.2 * S["body"].leading:
            break
        if subheads and heads and since_head >= 4 and not last and deck.random() < 0.35 \
                and pk.remaining() > 120:
            pk.add(Paragraph(deck.pick(heads), S["h3"]))
            since_head = 0
            continue
        text = T.paragraph(deck, topic, 3, 6, extra)
        p = Paragraph(text, S["body"])
        if last:
            if pk.fits(p):
                pk.add(p)
                since_head += 1
                continue
            sents = [T.sentence(deck, topic) for _ in range(6)]
            placed = False
            for k in range(len(sents), 0, -1):
                q = Paragraph(" ".join(sents[:k]), S["body"])
                if pk.fits(q):
                    pk.add(q)
                    placed = True
                    break
            if not placed:
                break
        else:
            # never let a paragraph spill from the last-but-one frame past the segment end
            pk.add(p)
            since_head += 1
    if pk.page_no != end_page:
        raise RuntimeError(f"LD003 fill ended on page {pk.page_no}, expected {end_page}")


def table_title(pk, ctx, label, text):
    p = Paragraph(f"{label} {text}", S["tabtitle"])
    if not pk.frame_empty() and pk.remaining() < 70:
        pk.next_frame()
    pl = pk.add(p)
    ctx.tables.append((label, text, pl[0][0]))


def figure(pk, ctx, label, drawing, caption):
    if not pk.frame_empty() and pk.remaining() < drawing.height + 30:
        pk.next_frame()
    pl = pk.add(drawing)
    pk.add(Paragraph(f"{label} {caption}", S["caption"]))
    ctx.figures.append((label, caption, pl[0][0]))
    return pl[0][0]


def footnote(pk, ctx, num, text):
    blk = FootnoteBlock([Paragraph(f"<super>{num}</super> {text}", S["fn"])])
    pk.reserve_footnote(blk)
    return pk.page_no


def new_segment(start, template):
    pk = Packer((PAGE_W, PAGE_H), TEMPLATES, first_page_no=start)
    pk.new_page(template)
    if template in AFTER_SECT:
        pk.cur_template = AFTER_SECT[template]
    return pk


def gbp(x):
    return f"{x:,.1f}"


# ---------------------------------------------------------------------------------------------
# Segments
# ---------------------------------------------------------------------------------------------

def seg_cover(ctx):
    pk = new_segment(1, "cover")
    cfo_n, cfo_t = person("P001", DATE)
    prep_n, prep_t = person("P020", DATE)
    loc = W.locations["LOC-LON"]
    pairs = [
        ("Firm", "Corvane Mutual Insurance Society Limited"),
        ("NISA firm reference", "NISA-FRN 40417"),
        ("Return", "NISA-AFR — Annual Claims & Reserving Filing"),
        ("Reporting period", "1 January 2025 to 31 December 2025"),
        ("Filing date", long_date(DATE)),
        ("Status", "Filed"),
        ("Prepared by", f"{prep_n}, {prep_t}"),
        ("Signed for the Board", f"{cfo_n}, {cfo_t}"),
        ("Registered office", loc["address"]),
    ]
    pk.add(Spacer(1, 18))
    pk.add(kv_table(pairs, [130, FW - 130], 9))
    pk.add(Spacer(1, 26))
    pk.add(Paragraph(
        "This filing is made under the Authority's annual claims and reserving reporting requirements. "
        "It is classified Restricted — Supervisory and is intended for the National Insurance Supervisory "
        "Authority and the Board and senior management of Corvane Mutual Insurance Society Limited.", S["body_left"]))
    pk.finish()
    return pk.pages


def seg_doccontrol(ctx):
    pk = new_segment(2, "full")
    pk.add(Paragraph("Document control", S["h1"]))
    names = {pid: person(pid, DATE) for pid in ("P020", "P021", "P009", "P010", "P037", "P005", "P001", "P007")}
    pk.add(kv_table([
        ("Document", "NISA Annual Claims & Reserving Filing 2025"),
        ("Return code", "NISA-AFR"),
        ("Version", "1.0 (filed)"),
        ("Owner", "Regulatory Reporting"),
        ("Author", f"{names['P020'][0]}, {names['P020'][1]}"),
        ("Classification", "Restricted — Supervisory"),
        ("Filing date", long_date(DATE)),
        ("Filing system", W.system_name("SYS10", DATE)),
    ], [130, FW - 130], 8.6))
    pk.add(Paragraph("Version history", S["h2"]))
    hist = [["Version", "Date", "Author / reviewer", "Change"],
            ["0.1", "30 January 2026", names["P020"][0], "First draft: structure, sections 1–3"],
            ["0.3", "13 February 2026", names["P020"][0], "Claims handling and conduct data added"],
            ["0.5", "27 February 2026", names["P009"][0], "Technical provisions and reserving sections"],
            ["0.7", "13 March 2026", names["P010"][0], "Actuarial review of section 4 and development tables"],
            ["0.8", "18 March 2026", names["P037"][0], "Compliance review of sections 3 and 7"],
            ["0.9", "24 March 2026", names["P021"][0], "Reconciliation to the Group Ledger; Executive review"],
            ["1.0", "31 March 2026", names["P001"][0], "Approved for filing on behalf of the Board"]]
    pk.add(grid_table(hist, [50, 88, 120, FW - 258], align_right_from=None, zebra=True))
    pk.add(Paragraph("Approvals", S["h2"]))
    appr = [["Role in this filing", "Name", "Title"],
            ["Prepared", names["P020"][0], names["P020"][1]],
            ["Reviewed (ledger reconciliation)", names["P021"][0], names["P021"][1]],
            ["Reviewed (reserving)", names["P009"][0], names["P009"][1]],
            ["Reviewed (actuarial opinion)", names["P010"][0], names["P010"][1]],
            ["Reviewed (conduct and counter-fraud)", names["P037"][0], names["P037"][1]],
            ["Reviewed (claims operations)", names["P005"][0], names["P005"][1]],
            ["Approved and signed for the Board", names["P001"][0], names["P001"][1]]]
    pk.add(grid_table(appr, [170, 130, FW - 300], align_right_from=None))
    pk.add(Paragraph("Distribution", S["h2"]))
    th_n, th_t = person("P055", DATE)
    pk.add(Paragraph(
        f"National Insurance Supervisory Authority (supervision team, attention {th_n}, {th_t}); "
        "the Board; the Executive Committee; the Chief Actuary; Internal Audit. Copies held by Regulatory "
        "Reporting under the filing reference NISA-AFR-2025.", S["body_left"]))
    for i in range(3):
        filler(pk, ctx, "intro")
    pk.finish()
    if len(pk.pages) != 1:
        raise RuntimeError("doc control overflow")
    return pk.pages


def seg_contents(ctx):
    pk = new_segment(3, "two")
    pk.add(Paragraph("Contents", S["h1"]))
    rows = []
    from reportlab.lib.styles import ParagraphStyle
    t1 = ParagraphStyle("t1", fontName="Helvetica-Bold", fontSize=8.8, leading=11.2, spaceBefore=0)
    t2 = ParagraphStyle("t2", fontName="Helvetica", fontSize=7.9, leading=9.4, leftIndent=14)
    bold_rows = []
    for level, text, pg in ctx.headings:
        if level == 1:
            rows.append([Paragraph(text, t1), str(pg)])
            bold_rows.append(len(rows) - 1)
        elif level == 2 and text.count(".") <= 1:
            rows.append([Paragraph(text, t2), str(pg)])
    t = Table(rows, colWidths=[CW2 - 34, 34])
    cmds = [("ALIGN", (1, 0), (1, -1), "RIGHT"), ("TOPPADDING", (0, 0), (-1, -1), 0.6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0.6), ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("FONT", (1, 0), (1, -1), "Helvetica", 7.9)]
    for r_ in bold_rows:
        cmds.append(("FONT", (1, r_), (1, r_), "Helvetica-Bold", 8.8))
        cmds.append(("TOPPADDING", (0, r_), (-1, r_), 3))
    t.setStyle(TableStyle(cmds))
    pk.add(t)
    pk.finish()
    if len(pk.pages) != 1:
        raise RuntimeError(f"contents overflow ({len(rows)} rows)")
    return pk.pages


def seg_attest(ctx):
    pk = new_segment(4, "full")
    pk.add(Paragraph("Attestation and signatures", S["h1"]))
    cfo = person("P001", DATE)
    cd = person("P005", DATE)
    ca = person("P010", DATE)
    pk.add(Paragraph(
        "The Board of Corvane Mutual Insurance Society Limited has approved this Annual Claims & Reserving "
        "Filing for the financial year ended 31 December 2025. To the best of the Board's knowledge and belief, "
        "the information in this filing is complete and accurate, the technical provisions have been "
        "established in accordance with the firm's reserving policy, and the claims handling information "
        "fairly reflects the firm's performance against its service standards and the Authority's requirements.",
        S["body"]))
    pk.add(Paragraph(
        "The Chief Financial Officer signs this filing on behalf of the Board. The Claims Director attests to "
        "the claims handling and conduct information in Section 3. The Chief Actuary's opinion on the "
        "technical provisions is summarised in Section 4.8.", S["body"]))
    sig = [["Signed for the Board", "Attestation (Section 3)", "Actuarial opinion (Section 4)"],
           [cfo[0], cd[0], ca[0]], [cfo[1], cd[1], ca[1]], [long_date(DATE)] * 3]
    t = Table(sig, colWidths=[FW / 3] * 3, rowHeights=[16, 40, 16, 16])
    t.setStyle(TableStyle([("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 8.4),
                           ("FONT", (0, 1), (-1, -1), "Helvetica", 8.6),
                           ("VALIGN", (0, 1), (-1, 1), "BOTTOM"),
                           ("LINEBELOW", (0, 1), (-1, 1), 0.5, NAVY),
                           ("BACKGROUND", (0, 0), (-1, 0), TEAL_LIGHT)]))
    pk.add(Spacer(1, 10))
    pk.add(t)
    pk.add(Spacer(1, 14))
    pk.add(Paragraph("Scope of attestation", S["h2"]))
    for _ in range(3):
        filler(pk, ctx, "governance")
    pk.add(Paragraph("Statement on the use of estimates", S["h2"]))
    for _ in range(2):
        filler(pk, ctx, "uncertainty")
    pk.finish()
    if len(pk.pages) != 1:
        raise RuntimeError("attestation overflow")
    return pk.pages


def sect_head(pk, ctx, num, title, lead):
    p = Paragraph(f"{num} {title}" if num else title, S["h1"])
    pg = pk.add(p)[0][0]
    ctx.headings.append((1, f"{num} {title}" if num else title, pg))
    pk.add(Paragraph(lead, S["lead"]))
    pk.next_frame()


def seg_s1(ctx):
    start, end = 5, 10
    pk = new_segment(start, "sect")
    sect_head(pk, ctx, "1", "Introduction and basis of preparation",
              "This section explains the purpose and scope of the filing, introduces the firm and sets out the "
              "basis on which the figures have been prepared and reconciled.")
    f = ctx.facts
    co = W.get("ORG:company")
    heading(pk, ctx, "1.1 Purpose and scope")
    filler(pk, ctx, "intro", 2)
    heading(pk, ctx, "1.2 The firm")
    sbc = co["staff_by_country"]
    txt = (f"{co['legal_name']} was founded in {co['founded']} as {co['founded_as']}. It is a "
           f"{co['type'].lower()} with {co['staff']:,} staff: {sbc['UK']:,} in the United Kingdom, {sbc['NO']:,} in "
           f"Norway, {sbc['SE']:,} in Sweden and {sbc['DK']:,} in Denmark. The firm is supervised by the National "
           f"Insurance Supervisory Authority under firm reference {co['nisa_firm_reference']}.")
    pl = para(pk, txt)
    f.add("general", f"Corvane Mutual was founded in {co['founded']} as {co['founded_as']} and has {co['staff']:,} staff.",
          f"founded in {co['founded']} as {co['founded_as']}", {"kind": "pdf_page", "page": pl[0][0]},
          world_ref="ORG:company#founded")
    f.add("general", "Staff by country: UK 2,900, Norway 470, Sweden 380, Denmark 300.",
          f"{sbc['NO']:,} in Norway, {sbc['SE']:,} in Sweden and {sbc['DK']:,} in Denmark",
          {"kind": "pdf_page", "page": pl[-1][0]}, world_ref="ORG:company#staff_by_country")
    locs = ", ".join(f"{W.locations[l]['name']}" for l in ("LOC-LON", "LOC-LDS", "LOC-BRS", "LOC-GLA", "LOC-OSL",
                                                            "LOC-STO", "LOC-CPH") if l in W.locations)
    para(pk, f"Its principal offices are: {locs}.")
    filler(pk, ctx, "business", 2)
    heading(pk, ctx, "1.3 Basis of preparation")
    filler(pk, ctx, "intro", 3)
    heading(pk, ctx, "1.4 Data sources and reconciliation")
    systems = [W.system_name(s, DATE) for s in ("SYS01", "SYS02", "SYS06", "SYS11", "SYS21", "SYS10")]
    para(pk, f"Claims and reserve data are taken from {systems[0]} and, for claims already handled on the new "
             f"platform, from {systems[1]}. Financial data are taken from the {systems[2]}; analytical data from "
             f"the {systems[3]}; actuarial projections are run in the {systems[4]}; and returns are compiled in "
             f"the {systems[5]}.")
    filler(pk, ctx, "returns", 2)
    heading(pk, ctx, "1.5 Key figures for 2025")
    fin = ctx.data.fin
    rows = [["Measure (financial year 2025)", "Value"],
            ["Gross written premium", f"£{fin['gross_written_premium_gbp_m']:,.1f}m"],
            ["Gross claims incurred", f"£{fin['gross_claims_incurred_gbp_m']:,.1f}m"],
            ["Combined ratio", f"{fin['combined_ratio_pct']}%"],
            ["Claims notified", f"{fin['claims_notified']:,}"],
            ["Average days to settle — motor", f"{fin['avg_settlement_days_motor']}"],
            ["Average days to settle — home", f"{fin['avg_settlement_days_home']}"]]
    table_title(pk, ctx, "Table 1.1", "Key figures")
    pl = pk.add(grid_table(rows, [pk.avail_width() - 70, 70]))
    pg = pl[0][0]
    f.add("needle", "Gross written premium for 2025 was £2,140.0m.", "Gross written premium £2,140.0m",
          {"kind": "pdf_page", "page": pg}, world_ref="ORG:company#financials.fy2025.gross_written_premium_gbp_m")
    f.add("needle", "Gross claims incurred for 2025 were £1,412.6m.", "Gross claims incurred £1,412.6m",
          {"kind": "pdf_page", "page": pg}, world_ref="ORG:company#financials.fy2025.gross_claims_incurred_gbp_m")
    f.add("needle", "Combined ratio for 2025 was 98.4%.", "Combined ratio 98.4%", {"kind": "pdf_page", "page": pg},
          world_ref="ORG:company#financials.fy2025.combined_ratio_pct")
    f.add("needle", "Corvane was notified of 212,400 claims in 2025.", "Claims notified 212,400",
          {"kind": "pdf_page", "page": pg}, world_ref="ORG:company#financials.fy2025.claims_notified")
    f.add("needle", "Average days to settle in 2025: motor 34, home 51.", "Average days to settle - motor 34",
          {"kind": "pdf_page", "page": pg}, world_ref="ORG:company#financials.fy2025.avg_settlement_days_motor")
    para(pk, "Technical provisions at the year end are analysed in Section 4, and counter-fraud outcomes in "
             "Section 3.7.")
    heading(pk, ctx, "1.6 Structure of this filing")
    filler(pk, ctx, "intro", 2)
    heading(pk, ctx, "1.7 Changes since the previous filing")
    filler(pk, ctx, "regchange", 1)
    fill_to(pk, ctx, end, "intro", extra=("governance",))
    pk.finish()
    return pk.pages


def seg_s2a(ctx):
    start, end = 11, 19
    pk = new_segment(start, "sect")
    sect_head(pk, ctx, "2", "Business and claims profile",
              "This section describes the products written, the volume and mix of claims notified in 2025 and "
              "the claims environment in which they were handled.")
    f, dt = ctx.facts, ctx.data
    heading(pk, ctx, "2.1 Lines of business and products")
    filler(pk, ctx, "business", 2)
    rows = [["Product", "Code", "Region", "Ccy", "Policies in force"]]
    for prod in dt.products:
        rows.append([prod["name"], prod["code"], prod["region"], prod["currency"], f"{prod['policies_in_force']:,}"])
    table_title(pk, ctx, "Table 2.1", "Products and policies in force at 31 December 2025")
    w = pk.avail_width()
    pl = pk.add(grid_table(rows, [w - 150, 34, 34, 28, 54], align_right_from=4))
    pg = pl[0][0]
    for pid in ("PRD-MOT-UK", "PRD-HOM-NO"):
        prod = W.get(f"PRODUCT:{pid}")
        guard(FID, f"PRODUCT:{pid}", "policies_in_force")
        f.add("needle", f"{prod['name']} had {prod['policies_in_force']:,} policies in force.",
              f"{prod['code']} {prod['region']} {prod['currency']} {prod['policies_in_force']:,}",
              {"kind": "pdf_page", "page": pg}, world_ref=f"PRODUCT:{pid}#policies_in_force")
    filler(pk, ctx, "business", 2)
    heading(pk, ctx, "2.2 Claims notified")
    fin = dt.fin
    pl = para(pk, f"The firm was notified of {fin['claims_notified']:,} claims in 2025 across all products and "
                  "territories. Motor and home products together account for the large majority of notifications.")
    filler(pk, ctx, "fnol", 1)
    names = [W.get(f"PRODUCT:{p}")["code"] for p in dt.prod_ids]
    vals = [dt.notified[p] / 1000 for p in dt.prod_ids]
    d = bar_chart(pk.avail_width(), 190, names, [vals], title="Claims notified in 2025 by product (thousands)",
                  horizontal=True, value_fmt="%0.1f")
    figure(pk, ctx, "Figure 2.1", d, "Claims notified in 2025 by product code (thousands). Source: claims platforms.")
    q_rows = [["Product", "Q1", "Q2", "Q3", "Q4", "Year"]]
    for pid in dt.prod_ids:
        m = dt.monthly[pid]
        qs = [sum(m[i:i + 3]) for i in (0, 3, 6, 9)]
        q_rows.append([W.get(f"PRODUCT:{pid}")["code"]] + [f"{q:,}" for q in qs] + [f"{sum(qs):,}"])
    tot = [sum(sum(dt.monthly[p][i:i + 3]) for p in dt.prod_ids) for i in (0, 3, 6, 9)]
    q_rows.append(["All products"] + [f"{q:,}" for q in tot] + [f"{sum(tot):,}"])
    table_title(pk, ctx, "Table 2.2", "Claims notified by product and quarter, 2025")
    w = pk.avail_width()
    pk.add(grid_table(q_rows, [w - 5 * 38, 38, 38, 38, 38, 38], bold_rows=(len(q_rows) - 1,)))
    filler(pk, ctx, "fnol", 1)
    months = list(range(1, 13))
    mlabels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    motor = [sum(dt.monthly[p][i] for p in dt.prod_ids if W.get(f"PRODUCT:{p}")["line"] == "Motor") / 1000 for i in range(12)]
    home = [sum(dt.monthly[p][i] for p in dt.prod_ids if W.get(f"PRODUCT:{p}")["line"] == "Home") / 1000 for i in range(12)]
    other = [sum(dt.monthly[p][i] for p in dt.prod_ids if W.get(f"PRODUCT:{p}")["line"] not in ("Motor", "Home")) / 1000 for i in range(12)]
    d = line_chart(pk.avail_width(), 180, months, [motor, home, other], ["Motor", "Home", "Commercial & liability"],
                   title="Monthly claims notified, 2025 (thousands)", x_labels=mlabels)
    figure(pk, ctx, "Figure 2.2", d, "Monthly claims notified by line, 2025 (thousands).")
    heading(pk, ctx, "2.3 Claims environment")
    filler(pk, ctx, "environment", 3)
    heading(pk, ctx, "2.4 Claim tiers")
    v = W.rule_version("BR-TRI-003", DATE)
    guard(FID, f"BR-TRI-003@v{v['version']}", "text")
    pl = para(pk, f"Claims are classified into tiers under rule BR-TRI-003 (version {v['version']}, effective "
                  f"{long_date(v['effective_from'])}). {v['text']}")
    f.add("definition", "BR-TRI-003 v3 defines Tier-3 as estimated incurred of £50,000 or more (or bodily injury, "
                        "litigation at notification, property total loss).",
          "estimated incurred ≥ £50,000", {"kind": "pdf_page", "page": pl[-1][0]},
          world_ref="RULE:BR-TRI-003@v3#text")
    share = W.get("TIMELINE:metrics")["tier3_share_pct"]["2025"] if W.get("TIMELINE:metrics") else 4.1
    pl = para(pk, f"Tier-3 claims represented {share}% of claims notified in 2025. They route to the Major & Complex "
                  "Loss team and are subject to the more frequent reserve reviews described in Section 4.2.")
    f.add("needle", f"Tier-3 claims were {share}% of claims notified in 2025.", f"Tier-3 claims represented {share}%",
          {"kind": "pdf_page", "page": pl[0][0]}, world_ref="TIMELINE:metrics#tier3_share_pct.2025")
    filler(pk, ctx, "handling", 1)
    heading(pk, ctx, "2.5 Operating model")
    for tid in ("T02", "T03", "T04", "T05", "T06", "T07", "T08", "T09", "T10", "T11"):
        nm = W.team_name(tid, DATE)
        lead = W.team_lead(tid, DATE)
        if lead:
            ln, lt = person(lead, DATE)
            pass
    rows = [["Team", "Lead", "Location"]]
    for tid in ("T02", "T03", "T04", "T05", "T06", "T07", "T08", "T09", "T10", "T11", "T12"):
        lead = W.team_lead(tid, DATE)
        if not lead:
            continue
        rows.append([W.team_name(tid, DATE), person(lead, DATE)[0],
                     W.locations[W.location_of(lead, DATE)]["city"]])
    table_title(pk, ctx, "Table 2.4", "Claims teams and team leads at the filing date")
    w = pk.avail_width()
    pl = pk.add(grid_table(rows, [w - 150, 95, 55], align_right_from=None))
    f.add("general", "At 31 March 2026 the Recoveries & Subrogation (Group) team was led by Freya Lindahl.",
          "Recoveries & Subrogation (Group) Freya Lindahl", {"kind": "pdf_page", "page": pl[-1][0]},
          world_ref="TEAM:T08#lead_history")
    fill_to(pk, ctx, end, "business", extra=("environment",))
    pk.finish()
    return pk.pages


def seg_s2b(ctx):
    start, end = 20, 21
    pk = new_segment(start, "three")
    dt = ctx.data
    heading(pk, ctx, "2.6 Product profiles")
    for prod in dt.products:
        pk.add(Paragraph(f"{prod['name']} ({prod['code']})", S["h3"]))
        cts = [W.claim_types[c] for c in prod["claim_types"]]
        if prod["region"] == "UK":
            ct_txt = ", ".join(c["name"].lower() for c in cts)
        else:
            ct_txt = ", ".join(f"{c['local_names'].get(prod['region'], c['name']).lower()} ({c['name'].lower()})"
                               for c in cts)
        para(pk, f"Line: {prod['line']}. Region: {prod['region']}; currency {prod['currency']}. Policies in force at "
                 f"the year end: {prod['policies_in_force']:,}. Claims notified in 2025: {dt.notified[prod['id']]:,}. "
                 f"Perils covered: {ct_txt}. The policy term for the amount borne by the policyholder is "
                 f"'{prod['local_excess_term']}'.", "body_left")
        filler(pk, ctx, "business", 1)
    fill_to(pk, ctx, end, "environment", extra=("business",), subheads=False)
    pk.finish()
    return pk.pages


def seg_s2c(ctx):
    start, end = 22, 28
    pk = new_segment(start, "two")
    f, dt = ctx.facts, ctx.data
    heading(pk, ctx, "2.7 Claims by product and peril")
    filler(pk, ctx, "environment", 2)
    rows = [["Product / peril", "Claims", "Share"]]
    hdr_rows = []
    for pid in dt.prod_ids:
        prod = W.get(f"PRODUCT:{pid}")
        hdr_rows.append(len(rows))
        rows.append([f"{prod['name']} ({prod['code']})", "", ""])
        for ct, n in dt.peril[pid].items():
            nm = W.claim_types[ct]["name"]
            if prod["region"] != "UK":
                nm = f"{W.claim_types[ct]['local_names'].get(prod['region'], nm)} ({nm.lower()})"
            rows.append([f"  {nm}", f"{n:,}", f"{100 * n / dt.notified[pid]:.1f}%"])
        rows.append(["  Product total", f"{dt.notified[pid]:,}", "100.0%"])
    filler(pk, ctx, "handling", 1)
    while pk.fi == 0:
        filler(pk, ctx, "environment", 1)
    table_title(pk, ctx, "Table 2.3", "Claims notified by product and peril, 2025 (no repeated header)")
    w = pk.avail_width()
    t = grid_table(rows, [w - 96, 50, 46], repeat=False, span_rows=hdr_rows,
                   bold_rows=[i for i, r in enumerate(rows) if r[0] == "  Product total"])
    placed = pk.add(t)
    pages_spanned = sorted({p for p, _, _ in placed})
    # fact on a continuation piece
    last_piece_page = [pg for pg, _, piece in placed if any(str(r_[0]).startswith("Hjem Danmark") for r_ in piece._cellvalues)][0]
    if last_piece_page == placed[0][0]:
        raise RuntimeError("Table 2.3: Hjem Danmark block is not on a continuation page")
    hd = W.get("PRODUCT:PRD-HOM-DK")
    f.add("multipage_table", f"Table 2.3 (continued without repeated header) shows {hd['name']} claims notified in 2025: "
                             f"{dt.notified['PRD-HOM-DK']:,}.",
          f"Hjem Danmark (HOMDK)", {"kind": "pdf_page", "page": last_piece_page},
          notes=f"Table 2.3 spans pages {pages_spanned[0]}-{pages_spanned[-1]}; header not repeated on continuation")
    para(pk, "Shares are of the product's own claims notified. Nordic peril names are given in the local language "
             "with the English equivalent.")
    heading(pk, ctx, "2.8 Large and complex losses")
    filler(pk, ctx, "environment", 2)
    heading(pk, ctx, "2.9 Geography")
    regs = dt.profile["sub_regions"]
    para(pk, "Claims are reported by sub-region for management purposes: United Kingdom — " + ", ".join(regs["UK"])
         + "; Norway — " + ", ".join(regs["NO"]) + "; Sweden — " + ", ".join(regs["SE"])
         + "; Denmark — " + ", ".join(regs["DK"]) + ".")
    fill_to(pk, ctx, end, "environment", extra=("business", "handling"))
    pk.finish()
    return pk.pages


def seg_s3a(ctx):
    start, end = 29, 32
    pk = new_segment(start, "sect")
    sect_head(pk, ctx, "3", "Claims handling performance and conduct",
              "This section reports performance against the firm's service standards and the Authority's "
              "requirements, and describes the treatment of customers through the claims journey, including "
              "counter-fraud activity and recoveries.")
    f = ctx.facts
    heading(pk, ctx, "3.1 Service standards")
    filler(pk, ctx, "handling", 1)
    rows = [["Rule", "Ver.", "Standard in force at 31 December 2025"]]
    std_rules = ["BR-FNOL-001", "BR-FNOL-012", "BR-RSV-001", "BR-RSV-008", "BR-ASM-005", "BR-ASM-006",
                 "BR-ASM-013", "BR-GEN-003", "BR-STL-004", "BR-REC-001"]
    ref_date = "2025-12-31"
    for rid in std_rules:
        v = W.rule_version(rid, ref_date)
        if not v or not may(FID, f"{rid}@v{v['version']}", "text"):
            continue
        rows.append([rid, str(v["version"]), Paragraph(v["text"], S["cell"])])
    table_title(pk, ctx, "Table 3.1", "Claims service standards")
    w = pk.avail_width()
    pl = pk.add(grid_table(rows, [52, 22, w - 74], align_right_from=None))
    f.add("needle", "At 31 December 2025, BR-FNOL-001 v2 required every FNOL to be acknowledged within 2 business days.",
          "Acknowledge every first notice of loss within 2 business days (NISA Circular 2024/07)",
          {"kind": "pdf_page", "page": pl[0][0]}, world_ref="RULE:BR-FNOL-001@v2#text")
    f.add("needle", "BR-ASM-005 v2: site inspection within 5 business days of appointment (Tier-3: 72 hours).",
          "Site inspection within 5 business days of appointment (Tier-3: 72 hours)",
          {"kind": "pdf_page", "page": pl[-1][0]}, world_ref="RULE:BR-ASM-005@v2#text")
    heading(pk, ctx, "3.2 Performance overview")
    filler(pk, ctx, "handling", 3)
    fill_to(pk, ctx, end, "handling", extra=("settlement",))
    pk.finish()
    return pk.pages


def seg_s3b(ctx):
    start, end = 33, 53
    pk = new_segment(start, "two")
    f, dt = ctx.facts, ctx.data
    pls = placements(FID)
    heading(pk, ctx, "3.3 First notification and acknowledgement")
    # PL-026: footnote on page 33 (exclusive)
    pl26 = pls["ld3_ack_perf"]
    fn_text = ("FNOL acknowledgement performance in 2025: 97.3% within 2 business days, measured from receipt of the "
               "notification in any channel to the issue of the acknowledgement.")
    pg = footnote(pk, ctx, 3, fn_text)
    para(pk, "The Authority's Circular 2024/07 requires every first notice of loss to be acknowledged within 2 "
             "business days, and the firm's rule BR-FNOL-001 was amended to that standard from 1 October 2024. "
             "Acknowledgement timeliness is monitored daily by the contact centre and the handling teams, and "
             "performance for the year is reported in the accompanying note.<super>3</super> Acknowledgement "
             "performance is also reported annually to the Authority in the NISA-CT1 claims timeliness return.")
    if pg != 33:
        raise RuntimeError("PL-026 footnote not on page 33")
    f.placement(pl26, "97.3% within 2 business days", {"kind": "pdf_page", "page": 33},
                notes="Footnote 3 at the bottom of the left-hand column on page 33; the body text only carries the "
                      "superscript marker.")
    filler(pk, ctx, "fnol", 3)
    heading(pk, ctx, "3.4 Triage and routing")
    v = W.rule_version("BR-TRI-004", DATE)
    pl = para(pk, f"Routing follows rule BR-TRI-004: {v['text']} Nordic claims are routed to Claims Operations Nordics "
                  "under BR-TRI-005.")
    f.add("needle", "BR-TRI-004: Tier-3 claims route to Major & Complex Loss within 4 hours.",
          "Tier-3 claims route to Major & Complex Loss within 4 hours", {"kind": "pdf_page", "page": pl[-1][0]},
          world_ref="RULE:BR-TRI-004@v1#text")
    filler(pk, ctx, "handling", 2)
    heading(pk, ctx, "3.5 Claims assessment")
    filler(pk, ctx, "assessment", 2)
    for vid in ("VEN-01", "VEN-02"):
        guard(FID, f"VENDOR:{vid}", "role")
    v1, v2 = W.vendors["VEN-01"], W.vendors["VEN-02"]
    pl = para(pk, f"The panel of external Claims Assessors (loss adjusters) at the filing date comprised {v1['name']} "
                  f"({v1['location']}) for UK property and motor, and {v2['name']} ({v2['location']}) for Sweden and "
                  "Norway. All external Nordic instructions are placed with Norrvik under rule BR-ASM-016.")
    f.add("needle", "Norrvik Skadetaxering AB (Gothenburg) is the external Claims Assessor for Sweden and Norway.",
          "Norrvik Skadetaxering AB (Gothenburg) for Sweden and Norway", {"kind": "pdf_page", "page": pl[-1][0]},
          world_ref="VENDOR:VEN-02#role")
    filler(pk, ctx, "assessment", 2)
    heading(pk, ctx, "3.6 Settlement")
    filler(pk, ctx, "settlement", 2)
    fin = dt.fin
    d = bar_chart(pk.avail_width(), 150, ["Motor", "Home"],
                  [[fin["avg_settlement_days_motor"], fin["avg_settlement_days_home"]]],
                  title="Average days from notification to settlement, 2025")
    pg = figure(pk, ctx, "Figure 3.1", d, "Average days to settle, 2025, motor and home claims.")
    f.add("chart_only", "Figure 3.1: average days to settle in 2025 were 34 (motor) and 51 (home).",
          "Average days from notification to settlement, 2025", {"kind": "pdf_page", "page": pg},
          world_ref="ORG:company#financials.fy2025.avg_settlement_days_home",
          notes="bar values 34 and 51 are drawn as vector chart labels")
    filler(pk, ctx, "settlement", 2)
    heading(pk, ctx, "3.6.1 Complaints", level=2)
    filler(pk, ctx, "complaints", 2)
    mon = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    rows = [["Category / month", "Count"]]
    span = []
    for cat in dt.complaint_cats:
        span.append(len(rows))
        rows.append([cat, ""])
        for i, n in enumerate(dt.complaints[cat]):
            rows.append([f"  {mon[i]} 2025", str(n)])
        rows.append(["  Year", f"{sum(dt.complaints[cat]):,}"])
    table_title(pk, ctx, "Table 3.4", "Complaints received by category and month, 2025 (no repeated header)")
    w = pk.avail_width()
    pk.add(grid_table(rows, [w - 60, 60], repeat=False, span_rows=span,
                      bold_rows=[i for i, r in enumerate(rows) if r[0] == "  Year"]))
    heading(pk, ctx, "3.6.2 Customers in vulnerable circumstances")
    filler(pk, ctx, "vulnerable", 3)
    fill_to(pk, ctx, end, "handling", extra=("complaints", "settlement", "vulnerable"))
    pk.finish()
    return pk.pages


def _piece_text(par):
    out = []
    for ln in par.blPara.lines:
        if isinstance(ln, tuple):
            out.append(" ".join(ln[1]))
        else:
            out.append(" ".join(getattr(fr, "text", "") for fr in getattr(ln, "words", [])))
    return " ".join(" ".join(out).split())


def seg_s3c(ctx):
    start, end = 54, 66
    pk = new_segment(start, "two")
    f, dt = ctx.facts, ctx.data
    pls = placements(FID)
    heading(pk, ctx, "3.7 Counter-fraud")
    deck = ctx.deck
    # fill column 1 of page 54 to leave a few lines, then place the split sentence
    lead_pool = [T.sentence(deck, "fraud") for _ in range(10)]
    while pk.remaining() > 150:
        p = Paragraph(T.paragraph(deck, "fraud", 2, 4), S["body"])
        if pk.height_of(p) < pk.remaining() - 60:
            pk.add(p)
        else:
            break
    fact_sent = ("In 2025 Corvane made 4,812 fraud referrals; 1,109 were confirmed fraud, saving £38.7m in "
                 "claim payments that would otherwise have been made.")
    tail = (" Confirmed outcomes are recorded only when an SIU investigation has closed with a confirmed-fraud "
            "outcome code and the avoided payment can be evidenced. Withdrawn claims and no-fraud outcomes are "
            "reported separately to the Claims Fraud Forum.")
    chosen = None
    w = pk.avail_width()
    R = pk.remaining()
    connectives = ["", "Across all products and territories, the outcomes were as follows. ",
                   "For the year as a whole: ", "Taken together, ", "Outcomes for the year are summarised here. ",
                   "In headline terms, "]
    for extra in (0, 4, 8, 12, 16, 20):
        for k in range(0, len(lead_pool) + 1):
            for conn in connectives:
                lead = " ".join(lead_pool[:k])
                text = (lead + " " if lead else "") + conn + fact_sent + tail
                P = Paragraph(text, S["body"])
                parts = P.split(w, R - extra - (0 if pk.frame_empty() else P.getSpaceBefore()))
                if len(parts) != 2:
                    continue
                first = _piece_text(parts[0])
                if "In 2025 Corvane made 4,812" in first and "\u00a338.7m" not in first:
                    chosen = (P, first, extra)
                    break
            if chosen:
                break
        if chosen:
            break
    if not chosen:
        raise RuntimeError("could not construct the split sentence on page 54")
    P, first, extra = chosen
    if extra:
        pk.add(Spacer(1, extra))
    placed = pk.add(P)
    locs = [(p, fi) for p, fi, _ in placed]
    if locs[0] != (54, 0) or locs[1] != (54, 1):
        raise RuntimeError(f"split sentence pieces landed at {locs}")
    start_idx = first.index("In 2025 Corvane")
    half1 = first[start_idx:]
    full = "In 2025 Corvane made 4,812 fraud referrals; 1,109 were confirmed fraud, saving £38.7m"
    half2 = full[len(half1):].strip() if full.startswith(half1) else full.split(half1.split()[-1], 1)[-1].strip()
    f.placement(pls["ld3_fraud_stats"], full, {"kind": "pdf_page", "page": 54},
                notes="Reading-order trap: the sentence starts on the last line(s) of column 1 and ends at the top of "
                      "column 2 on page 54.",
                halves=[half1, half2])
    filler(pk, ctx, "fraud", 2)
    v = W.rule_version("BR-FRD-012", DATE)
    pl = para(pk, f"Until 31 March 2026 the referral threshold is set by rule BR-FRD-012 version {v['version']}: "
                  f"{v['text']} The FRAUDNET engine was renamed Sentinel on 1 March 2025; scores are unchanged by the "
                  "rename. Plans to recalibrate the threshold are described in Section 7.3.")
    f.add("temporal", "Until 31 March 2026 the referral threshold under BR-FRD-012 v2 was a FRAUDNET/Sentinel score of 70.",
          "Refer a claim to SIU when the FRAUDNET/Sentinel score is 70 or more", {"kind": "pdf_page", "page": pl[-1][0]},
          world_ref="RULE:BR-FRD-012@v2#text")
    f.add("alias_use", "FRAUDNET was renamed Sentinel on 1 March 2025.", "renamed Sentinel on 1 March 2025",
          {"kind": "pdf_page", "page": pl[-1][0]}, world_ref="SYSTEM:SYS03#renames")
    v35 = W.rule_version("BR-FRD-035", DATE)
    pl = para(pk, f"SIU triage of new referrals is governed by BR-FRD-035 version {v35['version']}: {v35['text']}")
    v15 = W.vendors["VEN-15"]
    para(pk, f"The Sentinel scoring engine is licensed from {v15['name']} ({v15['location']}).")
    filler(pk, ctx, "fraud", 3)
    heading(pk, ctx, "3.8 Recoveries and subrogation")
    owner = W.owner_of_process("S7", DATE)
    on, ot = person(owner, DATE)
    pl = para(pk, f"The recoveries and subrogation process is owned by {on}, {ot}. UK recoveries are handled in Bristol "
                  "and Nordic recoveries follow the regress process with the counterparty insurer (BR-REC-008).")
    f.add("needle", "At the filing date the subrogation process owner was Freya Lindahl, Head of Recoveries & Subrogation.",
          f"owned by {on}, {ot}", {"kind": "pdf_page", "page": pl[-1][0]},
          world_ref="PROCESS:S7#owner_history")
    v3 = W.rule_version("BR-REC-003", DATE)
    pl = para(pk, f"Subrogation is pursued under BR-REC-003 version {v3['version']}: {v3['text']}")
    f.add("temporal", "BR-REC-003 v3 (from 2025-09-01): pursue subrogation where the recoverable amount is £1,000 or more.",
          "Pursue subrogation where the recoverable amount is £1,000 or more", {"kind": "pdf_page", "page": pl[-1][0]},
          world_ref="RULE:BR-REC-003@v3#text")
    filler(pk, ctx, "recoveries", 3)
    heading(pk, ctx, "3.9 Oversight of conduct risk")
    filler(pk, ctx, "governance", 2)
    fill_to(pk, ctx, end, "fraud", extra=("recoveries", "complaints"))
    pk.finish()
    return pk.pages


def seg_s4a(ctx):
    start, end = 67, 85
    pk = new_segment(start, "sect")
    sect_head(pk, ctx, "4", "Technical provisions",
              "This section describes how case reserves and IBNR are established, analyses the claims outstanding "
              "technical provisions at 31 December 2025 and discusses the uncertainty in the estimates.")
    f, dt = ctx.facts, ctx.data
    heading(pk, ctx, "4.1 Approach")
    filler(pk, ctx, "reserving", 2)
    para(pk, "The analysis of the technical provisions by reserving class, accident year and component is given in "
             "Table 4.2 in Section 4.4.")
    filler(pk, ctx, "ibnr", 1)
    heading(pk, ctx, "4.2 Case reserving")
    v = W.rule_version("BR-RSV-003", DATE)
    pl = para(pk, f"Reserve authority limits are set by rule BR-RSV-003 version {v['version']} "
                  f"(effective {long_date(v['effective_from'])}): {v['text']}")
    f.add("needle", "BR-RSV-003 v3 reserve authority: Claims Handler £25,000; Team Leader £100,000; Claims Manager "
                    "£500,000; Claims Director £2,000,000.",
          "Claims Handler £25,000; Team Leader £100,000", {"kind": "pdf_page", "page": pl[-1][0]},
          world_ref="RULE:BR-RSV-003@v3#text")
    v7 = W.rule_version("BR-RSV-007", DATE)
    pl = para(pk, f"Tier-3 reserve reviews: {v7['text']} (BR-RSV-007 version {v7['version']}).")
    f.add("temporal", "At the filing date BR-RSV-007 v2 required Tier-3 reserves to be reviewed at least every 21 days.",
          "reviewed at least every 21 days", {"kind": "pdf_page", "page": pl[-1][0]},
          world_ref="RULE:BR-RSV-007@v2#text")
    v11 = W.rule_version("BR-RSV-011", DATE)
    pl = para(pk, f"Large loss notification: {v11['text']}")
    f.add("needle", "BR-RSV-011 v2: notify Reinsurance (ReCede) within 24 hours of a reserve movement above the LLNT of £250,000.",
          "Large Loss Notification Threshold (LLNT) of £250,000", {"kind": "pdf_page", "page": pl[-1][0]},
          world_ref="RULE:BR-RSV-011@v2#text")
    v13 = W.rule_version("BR-RSV-013", DATE)
    para(pk, f"Large increases: {v13['text']} Expense reserves for escape-of-water claims follow BR-RSV-002.")
    filler(pk, ctx, "reserving", 3)
    # Table 4.1 reserve movement counts (multi-page, repeated header)
    r = seeded("LD003:t41")
    rows = [["Quarter / reason code", "Movements"]]
    span = []
    for q in ("Q1 2025", "Q2 2025", "Q3 2025", "Q4 2025"):
        span.append(len(rows))
        rows.append([q, ""])
        for code, label in dt.rsn_codes:
            for ln in ("UK", "Nordic"):
                rows.append([f"  {code} {label} — {ln}", f"{r.randint(800, 41000):,}"])
    table_title(pk, ctx, "Table 4.1", "Reserve movements by quarter, reason code and territory (count)")
    w = pk.avail_width()
    placed = pk.add(grid_table(rows, [w - 62, 62], span_rows=span))
    pages = sorted({p for p, _, _ in placed})
    f.add("multipage_table", "Table 4.1 lists reserve movements by quarter and reason code (RSNC list), repeated header.",
          "Q4 2025", {"kind": "pdf_page", "page": [p for p, _, piece in placed
                                                   if any(str(c[0]).strip() == "Q4 2025" for c in piece._cellvalues)][0]},
          notes=f"Table 4.1 spans pages {pages[0]}-{pages[-1]} with a repeated header row", world_ref="RULE:BR-RSV-015@v1")
    heading(pk, ctx, "4.3 IBNR methodology")
    filler(pk, ctx, "ibnr", 4)
    fill_to(pk, ctx, end, "ibnr", extra=("reserving", "uncertainty"))
    pk.finish()
    return pk.pages


def _lab(c):
    if isinstance(c, (list, tuple)):
        return " ".join(_lab(x) for x in c)
    return c.getPlainText() if hasattr(c, "getPlainText") else str(c)


def _prod_splits(dt):
    """Product-level split of class case/IBNR by accident year (tenths of £m, exact sums)."""
    if hasattr(dt, "_prod"):
        return dt._prod
    cls_of = {"PRD-MOT-UK": 0, "PRD-HOM-UK": 1, "PRD-COM-UK": 2, "PRD-LIA-UK": 3,
              "PRD-MOT-NO": 4, "PRD-MOT-SE": 4, "PRD-MOT-DK": 4, "PRD-HOM-NO": 5, "PRD-HOM-SE": 5, "PRD-HOM-DK": 5}
    out = {}
    for ci, c in enumerate(dt.classes):
        prods = [p for p, k in cls_of.items() if k == ci]
        wts = [dt.notified[p] for p in prods]
        per_ay_case = [_split_tenths(v, wts) for v in dt.ay_case[c]]
        per_ay_ibnr = [_split_tenths(v, wts) for v in dt.ay_ibnr[c]]
        for j, p in enumerate(prods):
            out[p] = {"case": [x[j] for x in per_ay_case], "ibnr": [x[j] for x in per_ay_ibnr]}
    dt._prod = out
    return out


def _table42(dt, ay_from, tail=0):
    """Rows of Table 4.2; returns rows, span rows, bold rows and the indices of the IBNR / TP rows."""
    prod = _prod_splits(dt)
    rows = [["Class / item", "Case \u00a3m", "IBNR \u00a3m", "Total \u00a3m"]]
    span, bold = [], []
    rows.append(["4.2(a) By product and accident year", "", "", ""])
    span.append(len(rows) - 1)
    for pid in dt.prod_ids:
        pr = W.get(f"PRODUCT:{pid}")
        rows.append([f"{pr['name']} ({pr['code']})", "", "", ""])
        span.append(len(rows) - 1)
        c_ays, i_ays = prod[pid]["case"], prod[pid]["ibnr"]
        older_c = sum(v for y, v in zip(dt.ays, c_ays) if y < ay_from)
        older_i = sum(v for y, v in zip(dt.ays, i_ays) if y < ay_from)
        if ay_from > dt.ays[0]:
            rows.append([f"  AY {ay_from - 1} and prior", gbp(older_c), gbp(older_i), gbp(older_c + older_i)])
        for y, vc, vi in zip(dt.ays, c_ays, i_ays):
            if y < ay_from:
                continue
            rows.append([f"  AY {y}", gbp(vc), gbp(vi), gbp(vc + vi)])
        tc, ti = sum(c_ays), sum(i_ays)
        rows.append(["  Product total", gbp(tc), gbp(ti), gbp(tc + ti)])
        bold.append(len(rows) - 1)
    rows.append(["4.2(b) Summary by reserving class and component", "", "", ""])
    span.append(len(rows) - 1)
    for i, c in enumerate(dt.classes):
        rows.append([c, gbp(dt.case_by[i]), gbp(dt.ibnr_by[i]), gbp(dt.case_by[i] + dt.ibnr_by[i])])
    rows.append(["Total case reserves", gbp(dt.case), "\u2013", gbp(dt.case)])
    bold.append(len(rows) - 1)
    rows.append(["of which IBNR", "\u2013", gbp(dt.ibnr), gbp(dt.ibnr)])
    ibnr_row = len(rows) - 1
    bold.append(ibnr_row)
    rows.append([Paragraph("<b>Claims outstanding technical provisions</b>", S["cell"]), gbp(dt.case),
                 gbp(dt.ibnr), gbp(dt.tp)])
    tp_row = len(rows) - 1
    bold.append(tp_row)
    rows.append(["4.2(c) By product and peril", "", "", ""])
    span.append(len(rows) - 1)
    for pid in dt.prod_ids:
        pr = W.get(f"PRODUCT:{pid}")
        rows.append([f"{pr['name']} ({pr['code']})", "", "", ""])
        span.append(len(rows) - 1)
        tc, ti = sum(prod[pid]["case"]), sum(prod[pid]["ibnr"])
        cts = list(dt.peril[pid].keys())
        wts = [dt.peril[pid][c] for c in cts]
        cs, is_ = _split_tenths(tc, wts), _split_tenths(ti, wts)
        for ct, vc, vi in zip(cts, cs, is_):
            rows.append([f"  {W.claim_types[ct]['name']}", gbp(vc), gbp(vi), gbp(vc + vi)])
    rows.append(["4.2(d) By currency of the underlying claims (GBP equivalent)", "", "", ""])
    span.append(len(rows) - 1)
    for cur in ("GBP", "NOK", "SEK", "DKK"):
        ps = [p for p in dt.prod_ids if W.get(f"PRODUCT:{p}")["currency"] == cur]
        cc = sum(sum(prod[p]["case"]) for p in ps)
        ii = sum(sum(prod[p]["ibnr"]) for p in ps)
        rows.append([f"  Claims in {cur}", gbp(cc), gbp(ii), gbp(cc + ii)])
    rows.append(["4.2(e) By claim tier (case reserves only)", "", "", ""])
    span.append(len(rows) - 1)
    tiers = _split_tenths(dt.case, [0.18, 0.37, 0.45])
    for lab, v in zip(("Tier-1", "Tier-2", "Tier-3"), tiers):
        rows.append([f"  {lab}", gbp(v), "\u2013", gbp(v)])
    rows.append(["4.2(f) By sub-region (case reserves only)", "", "", ""])
    span.append(len(rows) - 1)
    regs = dt.profile["sub_regions"]
    for reg, cur in (("UK", "GBP"), ("NO", "NOK"), ("SE", "SEK"), ("DK", "DKK")):
        ps = [p for p in dt.prod_ids if W.get(f"PRODUCT:{p}")["currency"] == cur]
        tot = sum(sum(prod[p]["case"]) for p in ps)
        r = seeded(f"LD003:subreg:{reg}")
        vals = _split_tenths(round(tot, 1), [r.uniform(0.6, 1.6) for _ in regs[reg]])
        for nm, v in zip(regs[reg], vals):
            rows.append([f"  {reg} \u2014 {nm}", gbp(v), "\u2013", gbp(v)])
    if tail & 1:
        rows.append(["4.2(g) By product and quarter of notification (case reserves only)", "", "", ""])
        span.append(len(rows) - 1)
        for pid in dt.prod_ids:
            pr = W.get(f"PRODUCT:{pid}")
            rows.append([f"{pr['name']} ({pr['code']})", "", "", ""])
            span.append(len(rows) - 1)
            m = dt.monthly[pid]
            qw = [sum(m[k:k + 3]) for k in (0, 3, 6, 9)]
            tc = round(sum(prod[pid]["case"][-1:]), 1)
            for qlab, v in zip(("Q1", "Q2", "Q3", "Q4"), _split_tenths(tc, [w_ * (1 + 0.25 * j) for j, w_ in enumerate(qw)])):
                rows.append([f"  AY 2025 {qlab}", gbp(v), "\u2013", gbp(v)])
    if tail & 2:
        rows.append(["4.2(h) By product and claim status (case reserves only)", "", "", ""])
        span.append(len(rows) - 1)
        for pid in dt.prod_ids:
            pr = W.get(f"PRODUCT:{pid}")
            rows.append([f"{pr['name']} ({pr['code']})", "", "", ""])
            span.append(len(rows) - 1)
            tc = round(sum(prod[pid]["case"]), 1)
            for lab, v in zip(("Open", "Reopened", "Litigated"), _split_tenths(tc, [0.86, 0.04, 0.10])):
                rows.append([f"  {lab}", gbp(v), "\u2013", gbp(v)])
    return rows, span, bold, ibnr_row, tp_row


def seg_s4b(ctx):
    start, end = 86, 89
    f, dt = ctx.facts, ctx.data
    pls = placements(FID)
    best = None
    for ay_from, n_intro, tail in [(a_, n_, t_) for t_ in (0, 1, 2, 3) for a_ in (2016, 2015, 2017, 2014, 2018, 2019, 2020)
                                   for n_ in range(0, 9)]:
        if True:
            deck_state = ctx.deck.r.getstate()
            pk = new_segment(start, "two")
            heading(pk, ctx, "4.4 Analysis of technical provisions")
            para(pk, "Table 4.2 analyses the claims outstanding technical provisions at 31 December 2025 by reserving "
                     "class, accident year, component, currency and tier. Amounts are gross of reinsurance and in "
                     "pounds sterling; Nordic classes are translated at the year-end rate.")
            for _ in range(n_intro):
                filler(pk, ctx, "reserving")
            rows, span, bold, ibnr_row, tp_row = _table42(dt, ay_from, tail)
            table_title(pk, ctx, "Table 4.2", "Claims outstanding technical provisions at 31 December 2025")
            w = pk.avail_width()
            t = grid_table(rows, [w - 3 * 46, 46, 46, 46], span_rows=span, bold_rows=bold, pad=2.6)
            placed = pk.add(t)
            # locate the IBNR and total rows in the split pieces
            def where(label):
                for pg, fi, piece in placed:
                    if any(_lab(r_[0]) == label for r_ in piece._cellvalues):
                        return (pg, fi)
                return None
            loc_ibnr = where("of which IBNR")
            loc_tp = where("Claims outstanding technical provisions")
            ok = (placed[0][0] == 86 and placed[-1][0] == 89 and loc_ibnr == (87, 1) and loc_tp == (87, 1))
            if ok:
                best = (ay_from, n_intro, pk, placed, loc_ibnr)
                break
            ctx.deck.r.setstate(deck_state)
            # discard headings recorded by the failed attempt
            ctx.headings = [h for h in ctx.headings if not (86 <= h[2] <= 89)]
            ctx.tables = [t_ for t_ in ctx.tables if t_[0] != "Table 4.2"]
        if best:
            break
    if not best:
        raise RuntimeError("could not place Table 4.2 IBNR row on page 87, right-hand column")
    ay_from, n_intro, pk, placed, loc_ibnr = best
    pages = sorted({p for p, _, _ in placed})
    para(pk, "Notes to Table 4.2: (1) IBNR includes provision for development on reported claims. (2) Accident-year "
             "splits of IBNR are allocations of the class estimate. (3) Currency analysis uses the location of the "
             "underlying policy.")
    f.placement(pls["ld3_ibnr"], "of which IBNR \u2013 611.9", {"kind": "pdf_page", "page": 87},
                statement="Claims outstanding technical provisions at 2025-12-31 were £2,318.4m, of which IBNR £611.9m "
                          "(Table 4.2, page 87, right-hand column).",
                notes=f"Table 4.2 spans pages {pages[0]}-{pages[-1]} with a repeated header; the 'of which IBNR' and "
                      "total rows sit in the right-hand column of page 87; the amount is in the table's right-hand "
                      "(Total) column. Neither figure appears anywhere else in the filing.",
                table_pages=pages)
    f.add("multipage_table", "Claims outstanding technical provisions at 2025-12-31 were £2,318.4m (Table 4.2 total row).",
          "Claims outstanding technical provisions 1,706.5 611.9 2,318.4", {"kind": "pdf_page", "page": 87}, world_ref="ORG:company#financials.fy2025.claims_outstanding_technical_provisions_gbp_m",
          notes="same row block as the IBNR placement")
    fill_to(pk, ctx, end, "reserving", extra=("ibnr",))
    pk.finish()
    return pk.pages


def seg_s4c(ctx):
    start, end = 90, 100
    pk = new_segment(start, "two")
    f, dt = ctx.facts, ctx.data
    heading(pk, ctx, "4.5 Movements in the year")
    filler(pk, ctx, "reserving", 2)
    d = pie_chart(pk.avail_width(), 170, [c.split(" (")[0] for c in dt.classes], dt.case_by,
                  title="Case reserves by reserving class (£m)")
    pg = figure(pk, ctx, "Figure 4.1", d, "Case reserves at 31 December 2025 by reserving class (£m).")
    f.add("chart_only", f"Figure 4.1: case reserves for SME Liability UK were £{dt.case_by[3]:,.1f}m at 2025-12-31.",
          f"SME Liability UK ({dt.case_by[3]:,.1f})", {"kind": "pdf_page", "page": pg},
          notes="pie legend label; derived split of the case reserve total (invented breakdown, not a world fact)")
    footnote(pk, ctx, 7, "Nordic case reserves are held in NOK, SEK and DKK and translated at the Group Ledger "
                         "month-end rate (BR-RSV-012).")
    para(pk, "Nordic reserves are shown at the year-end translation rate.<super>7</super>")
    filler(pk, ctx, "reserving", 2)
    heading(pk, ctx, "4.6 Uncertainty and sensitivities")
    filler(pk, ctx, "uncertainty", 4)
    heading(pk, ctx, "4.7 Large loss notifications to Reinsurance")
    pl = para(pk, f"Reserve movements above the Large Loss Notification Threshold are notified to Reinsurance through "
                  f"{W.system_name('SYS07', DATE)} within 24 hours. The Reinsurance Manager, "
                  f"{person('P038', DATE)[0]}, reviews notifications for completeness.")
    filler(pk, ctx, "reserving", 1)
    heading(pk, ctx, "4.8 Chief Actuary's opinion (summary)")
    ca = person("P010", DATE)
    para(pk, f"The Chief Actuary, {ca[0]}, has reviewed the methods, assumptions and data used to establish the "
             "technical provisions and considers them appropriate. In the Chief Actuary's opinion the technical "
             "provisions at 31 December 2025 represent a reasonable best estimate.")
    filler(pk, ctx, "ibnr", 2)
    fill_to(pk, ctx, end, "uncertainty", extra=("ibnr", "reserving"))
    pk.finish()
    return pk.pages


def seg_s5(ctx):
    start, end = 101, 106
    pk = new_segment(start, "full")
    f, dt = ctx.facts, ctx.data
    p = Paragraph("5 Claims development", S["h1"])
    pk.add(p)
    ctx.headings.append((1, "5 Claims development", start))
    para(pk, "The tables below show cumulative paid claims (£m, gross) by accident year and development year for "
             "each reserving class. Accident years before 2016 are excluded; Nordic amounts are translated at "
             "year-end 2025 rates.")
    filler(pk, ctx, "development", 1)
    for k, c in enumerate(dt.classes):
        sub = f"5.{k + 1} {c}"
        heading(pk, ctx, sub)
        rows = [["AY"] + [f"D{d}" for d in range(1, 11)]]
        for y, devs in zip(dt.tri_years, dt.tri[c]):
            rows.append([str(y)] + [gbp(v) if v is not None else "" for v in devs])
        label = f"Table 5.{k + 1}"
        table_title(pk, ctx, label, f"Cumulative paid claims, {c} (£m)")
        t = grid_table(rows, [40] + [(FW - 40) / 10] * 10, font_size=7.2)
        pl = pk.add(t)
        if k == 0:
            f.add("general", f"Table 5.1: cumulative paid claims for {c}, accident year 2016, development year 1 were "
                             f"£{dt.tri[c][0][0]:,.1f}m (invented triangle).", f"2016 {gbp(dt.tri[c][0][0])}",
                  {"kind": "pdf_page", "page": pl[0][0]}, notes="development triangle (not a world fact)")
        filler(pk, ctx, "development", 1)
        if k == 2:
            xs = list(range(1, 11))
            series = []
            names = []
            for c2 in dt.classes[:4]:
                row = dt.tri[c2][0]
                series.append([100 * v / row[-1] for v in row])
                names.append(c2.split(" UK")[0])
            d = line_chart(FW, 200, xs, series, names, title="Paid development, accident year 2016 (% of 10-year paid)",
                           x_labels=[f"D{x}" for x in xs])
            figure(pk, ctx, "Figure 5.1", d, "Paid development patterns, accident year 2016, UK classes.")
    fill_to(pk, ctx, end, "development", subheads=False)
    pk.finish()
    return pk.pages


def seg_s6(ctx):
    start, end = 107, 110
    pk = new_segment(start, "sect")
    sect_head(pk, ctx, "6", "Regulatory returns and data quality",
              "This section summarises the claims-related returns made to the Authority, the controls over their "
              "preparation, and the one late submission during 2025.")
    f = ctx.facts
    heading(pk, ctx, "6.1 Returns calendar")
    rows = [["Return", "Frequency", "Due", "Signed by"]]
    for rid in ("NISA-TP2", "NISA-FR1", "NISA-CT1", "NISA-AFR"):
        rp = W.reports[rid]
        rows.append([Paragraph(f"{rid} {rp['name']}", S["cell"]), rp["frequency"], Paragraph(str(rp["due"]), S["cell"]),
                     Paragraph(rp["signed_by_role"], S["cell"])])
    table_title(pk, ctx, "Table 6.1", "Claims-related returns to the Authority")
    w = pk.avail_width()
    pl = pk.add(grid_table(rows, [w - 160, 46, 60, 54], align_right_from=None))
    f.add("needle", "NISA-TP2 (Quarterly Technical Provisions Return) is due 35 calendar days after quarter end.",
          "35 calendar days after quarter end", {"kind": "pdf_page", "page": pl[-1][0]}, world_ref="REPORT:NISA-TP2#due")
    fr1 = W.reports["NISA-FR1"]
    para(pk, f"The NISA-FR1 fraud referral return is new: the first return covers {fr1['first_period']} and is due on "
             f"{long_date(fr1['first_due'])}. All returns are prepared by Regulatory Reporting in the "
             f"{W.system_name('SYS10', DATE)}.")
    filler(pk, ctx, "returns", 2)
    heading(pk, ctx, "6.2 Late submission of the Q1 2025 NISA-TP2 return")
    inc = W.incidents["INC-2025-0412"]
    ev = W.reports["NISA-TP2"]["late_events"][0]
    th = person("P055", DATE)[0]
    pl = para(pk, f"The NISA-TP2 return for {ev['period']} was due on {long_date(ev['due'])} and was submitted on "
                  f"{long_date(ev['submitted'])}, two days late, under an extension granted by {th} of the Authority. "
                  f"The delay followed incident {inc['id']} ({long_date(inc['date'])}): {inc['title'].lower()}. "
                  f"{inc['impact']}")
    f.add("needle", "The Q1 2025 NISA-TP2 return was submitted on 2025-05-07 instead of 2025-05-05 after INC-2025-0412 "
                    "(2-day extension granted by Imogen Thackray).",
          f"submitted on {long_date(ev['submitted'])}", {"kind": "pdf_page", "page": pl[-1][0]},
          world_ref="REPORT:NISA-TP2#late_events")
    para(pk, f"The root cause was identified as follows: {inc['root_cause']} Remediation was tracked under "
             f"{', '.join(inc['fix_tickets'])}.")
    filler(pk, ctx, "returns", 2)
    heading(pk, ctx, "6.3 Data quality")
    filler(pk, ctx, "returns", 3)
    fill_to(pk, ctx, end, "returns", extra=("governance",))
    pk.finish()
    return pk.pages


def seg_s7a(ctx):
    start, end = 111, 111
    pk = new_segment(start, "sect")
    sect_head(pk, ctx, "7", "Regulatory change",
              "This section reports the implementation of the Authority's circulars that affect claims handling, "
              "including the firm's preparation for NISA Circular 2026/04 on fair treatment in fraud referral.")
    f = ctx.facts
    heading(pk, ctx, "7.1 Overview")
    rows = [["Circular", "Title", "Effective"]]
    for cid in ("CIRC-2024-07", "CIRC-2025-02", "CIRC-2025-11", "CIRC-2026-04"):
        c = W.circulars[cid]
        rows.append([c["ref"].replace("NISA Circular ", ""), Paragraph(c["title"], S["cell"]), long_date(c["effective"])])
    table_title(pk, ctx, "Table 7.1", "Circulars relevant to claims")
    w = pk.avail_width()
    pl = pk.add(grid_table(rows, [42, w - 112, 70], align_right_from=None))
    f.add("needle", "NISA Circular 2026/04 (Fair Treatment in Fraud Referral) is effective from 1 April 2026.",
          "Fair Treatment in Fraud Referral 1 April 2026", {"kind": "pdf_page", "page": pl[0][0]},
          world_ref="CIRCULAR:CIRC-2026-04#effective")
    heading(pk, ctx, "7.2 Circular 2024/07 — claims handling timeliness")
    c = W.circulars["CIRC-2024-07"]
    para(pk, f"{c['ref']} took effect on {long_date(c['effective'])}. Paragraph {c['requirements'][0]['para']} requires "
             f"firms to: {c['requirements'][0]['text'].lower()} Paragraph {c['requirements'][1]['para']} requires firms "
             f"to: {c['requirements'][1]['text'].lower()} The firm's acknowledgement rule BR-FNOL-001 was amended "
             "accordingly (version 2).")
    fill_to(pk, ctx, end, "regchange")
    pk.finish()
    return pk.pages


def seg_s7b(ctx):
    start, end = 112, 124
    pk = new_segment(start, "two")
    f = ctx.facts
    pls = placements(FID)
    heading(pk, ctx, "7.3 Circular 2026/04 — fair treatment in fraud referral")
    c = W.circulars["CIRC-2026-04"]
    guard(FID, "RULE:BR-FRD-031@v1", "text")
    v31 = W.get("RULE:BR-FRD-031")["versions"][0]
    ap = [person(p, DATE)[0] for p in v31["approved_by"]]
    pl = para(pk, f"{c['ref']} was published on {long_date(c['published'])} and takes effect on "
                  f"{long_date(c['effective'])}. Paragraph 3.3 limits score-based referral cut-offs on a 0–100 scale "
                  "to 65. Corvane will recalibrate its fraud referral threshold from 70 to 65 on 1 April 2026 to comply "
                  f"with NISA Circular 2026/04. The new rule, BR-FRD-031, was approved on {long_date(v31['approved_on'])} "
                  f"by {ap[0]} and {ap[1]} and replaces BR-FRD-012.")
    if pl[0][0] != 112 and pl[-1][0] != 112:
        raise RuntimeError("PL-028 not on page 112")
    f.placement(pls["ld3_recalib"], "recalibrate its fraud referral threshold from 70 to 65 on 1 April 2026",
                {"kind": "pdf_page", "page": 112}, notes="Section 7.3, page 112")
    rows = [["Rule", "Change from 1 April 2026"]]
    changes = [("BR-FRD-031", "New: refer at a Sentinel score of 65 or more (all tiers); supersedes BR-FRD-012."),
               ("BR-FRD-012", "Superseded on 31 March 2026 (threshold 70)."),
               ("BR-FRD-019", "Withdrawn: no automatic decline on a score alone."),
               ("BR-FRD-032", "Customer told in writing within 10 business days of referral (version 2)."),
               ("BR-FRD-033", "No claim declined, reduced or repudiated on a score alone; documented SIU review."),
               ("BR-FRD-034", "Quarterly NISA-FR1 return within 30 calendar days after quarter end; first for Q2 2026."),
               ("BR-FRD-035", "SIU triage of new referrals within 3 business days (version 2).")]
    for rid, txt in changes:
        rows.append([rid, Paragraph(txt, S["cell"])])
    table_title(pk, ctx, "Table 7.2", "Fraud rule changes approved on 12 March 2026")
    w = pk.avail_width()
    pl = pk.add(grid_table(rows, [54, w - 54], align_right_from=None))
    f.add("needle", "From 1 April 2026 BR-FRD-035 v2 requires SIU triage of new referrals within 3 business days.",
          "SIU triage of new referrals within 3 business days", {"kind": "pdf_page", "page": pl[-1][0]},
          world_ref="RULE:BR-FRD-035@v2#text")
    f.add("needle", "BR-FRD-019 (automatic decline on score) is withdrawn from 2026-04-01.",
          "Withdrawn: no automatic decline on a score alone", {"kind": "pdf_page", "page": pl[-1][0]},
          world_ref="RULE:BR-FRD-019@v2")
    para(pk, "Paragraph 3.2 of the circular allows the customer notice to be deferred for up to 60 days where a "
             "tipping-off risk is certified. The firm's deferral procedure, including who may approve a deferral, is "
             "set out in the Claims Handling Manual.")
    filler(pk, ctx, "fraud", 2)
    filler(pk, ctx, "regchange", 2)
    heading(pk, ctx, "7.4 Circular 2025/02 — operational resilience for claims payment")
    c = W.circulars["CIRC-2025-02"]
    pl = para(pk, f"{c['ref']} took effect on {long_date(c['effective'])}. It requires firms to "
                  f"{c['requirements'][0]['text'][0].lower() + c['requirements'][0]['text'][1:]} and to "
                  f"{c['requirements'][1]['text'][0].lower() + c['requirements'][1]['text'][1:]}")
    f.add("needle", "NISA Circular 2025/02 sets an impact tolerance of 48 hours for disruption to claims payments.",
          "impact tolerance of 48 hours", {"kind": "pdf_page", "page": pl[-1][0]},
          world_ref="CIRCULAR:CIRC-2025-02#requirements.3.1")
    filler(pk, ctx, "resilience", 3)
    heading(pk, ctx, "7.5 Circular 2025/11 — claims data retention and minimisation")
    c = W.circulars["CIRC-2025-11"]
    v4 = W.rule_version("BR-GEN-004", DATE)
    pl = para(pk, f"{c['ref']} took effect on {long_date(c['effective'])}. The firm's retention rule BR-GEN-004 was "
                  f"updated to version {v4['version']}: {v4['text']} Rule BR-GEN-006 prohibits the use of production "
                  "personal data in test environments.")
    f.add("temporal", "From 2026-01-01 BR-GEN-004 v3 retains claim records 7 years after closure and bodily-injury "
                      "claims 15 years.", "bodily-injury claims for 15 years after closure",
          {"kind": "pdf_page", "page": pl[-1][0]}, world_ref="RULE:BR-GEN-004@v3#text")
    filler(pk, ctx, "retention", 3)
    heading(pk, ctx, "7.6 Forward look")
    filler(pk, ctx, "regchange", 2)
    fill_to(pk, ctx, end, "regchange", extra=("fraud", "resilience"))
    pk.finish()
    return pk.pages


def seg_s8a(ctx):
    start, end = 125, 125
    pk = new_segment(start, "sect")
    sect_head(pk, ctx, "8", "Systems and Programme Skerry",
              "This section describes the claims systems estate and the programme replacing the CLARA platform, "
              "with the controls applied to protect customers and regulatory reporting during migration.")
    f = ctx.facts
    heading(pk, ctx, "8.1 Programme overview")
    co = W.get("ORG:company")
    prog = co["programme"]
    tl = W.get("TIMELINE:programme")
    s1, s2 = W.systems["SYS01"], W.systems["SYS02"]
    gw = person("P002", "2024-11-18")
    pl = para(pk, f"{s1['name']} (Claims Ledger And Reserve Application) has been the system of record for claims since "
                  f"{long_date(s1['go_live'])}. It is written in COBOL and runs under CICS with DB2 on z/OS. "
                  f"{prog['name']} is replacing it with {s2['name']}, built as Java and Spring Boot microservices on "
                  f"OpenShift with PostgreSQL and Kafka. The business case (£{prog['budget_gbp_m']}m) was signed "
                  f"on {long_date(prog['business_case_date'])} by the then Chief Financial Officer, {gw[0]}.")
    f.add("needle", "The Programme Skerry business case (£48.6m) was signed on 2024-11-18 by the then CFO Gareth Whitcombe.",
          f"by the then Chief Financial Officer, {gw[0]}", {"kind": "pdf_page", "page": pl[-1][0]},
          world_ref="EVENT:EV-010")
    f.add("needle", "CLARA has been the claims system of record since 3 October 1994.",
          "system of record for claims since 3 October 1994", {"kind": "pdf_page", "page": pl[0][0]},
          world_ref="SYSTEM:SYS01#go_live")
    pl = para(pk, f"The external delivery partner joined on {long_date(prog['ibm_engagement_start'])}. The minimum viable "
                  f"product went live on {long_date(tl['mvp'])}. Wave 0 (Denmark) is planned for {long_date(tl['wave0'])}, "
                  f"Wave 1 (UK motor) for {long_date(tl['wave1'])} and Wave 2 for {long_date(tl['wave2'])}. The target for "
                  f"decommissioning CLARA is {long_date(tl['clara_decommission_target'])}.")
    f.add("temporal", "As at 2026-03-31, Wave 1 (UK motor) was planned for 2026-09-14 and CLARA decommissioning was "
                      "targeted for 2027-09-30.", "Wave 1 (UK motor) for 14 September 2026",
          {"kind": "pdf_page", "page": pl[-1][0]}, world_ref="TIMELINE:programme#wave1")
    import datetime as _dt

    def num(s):
        x = _dt.date.fromisoformat(s)
        return x.year + (x.timetuple().tm_yday - 1) / 365.0
    rows = [("CLARA (live)", 2024.0, num(tl["clara_decommission_target"]), 4, "decommission target"),
            ("Business case", num(prog["business_case_date"]), num(prog["business_case_date"]) + 0.02, 1, ""),
            ("Build to MVP", num(prog["ibm_engagement_start"]), num(tl["mvp"]), 0, "MVP"),
            ("Wave 0 Denmark", num(tl["mvp"]), num(tl["wave0"]), 1, "planned"),
            ("Wave 1 UK motor", num(tl["wave0"]), num(tl["wave1"]), 2, "planned"),
            ("Wave 2", num(tl["wave1"]), num(tl["wave2"]), 3, "planned")]
    d = gantt(pk.avail_width(), 160, rows, 2024.0, 2028.0,
              [(2024.0, "2024"), (2025.0, "2025"), (2026.0, "2026"), (2027.0, "2027"), (2028.0, "2028")],
              title="Programme Skerry timeline (as at 31 March 2026)")
    figure(pk, ctx, "Figure 8.1", d, "Programme Skerry milestones as planned at the filing date.")
    fill_to(pk, ctx, end, "programme")
    pk.finish()
    return pk.pages


def seg_s8b(ctx):
    start, end = 126, 127
    pk = new_segment(start, "three")
    f = ctx.facts
    heading(pk, ctx, "8.2 Claims systems estate")
    para(pk, "The systems below support the claims value chain at the filing date. Names are those in use on 31 March "
             "2026; former names are given where a system was renamed in the last two years.", "body_left")
    for sid in sorted(W.systems):
        s = W.systems[sid]
        if s.get("lifecycle") == "retired":
            continue
        nm = W.system_name(sid, DATE)
        former = ""
        for rn in s.get("renames") or []:
            if rn.get("date") and "2024-04-01" <= str(rn["date"]) <= DATE:
                former = f" (formerly {rn.get('from_name')}, renamed {long_date(rn['date'])})"
        pk.add(Paragraph(f"{nm}", S["h3"]))
        para(pk, f"{s['type']}.{former}", "body_left")
    f.add("alias_use", "MyCorvane Claims was formerly ClaimLine Web (renamed 2024-10-14).", "formerly ClaimLine Web",
          {"kind": "pdf_page", "page": None}, world_ref="SYSTEM:SYS04#renames")
    fill_to(pk, ctx, end, "programme", subheads=False)
    pk.finish()
    return pk.pages


def seg_s8c(ctx):
    start, end = 128, 134
    pk = new_segment(start, "two")
    heading(pk, ctx, "8.3 Controls over migration")
    filler(pk, ctx, "programme", 3)
    heading(pk, ctx, "8.4 Continuity of regulatory reporting")
    filler(pk, ctx, "returns", 2)
    filler(pk, ctx, "programme", 1)
    heading(pk, ctx, "8.5 Lessons from 2025 incidents")
    filler(pk, ctx, "programme", 2)
    heading(pk, ctx, "8.6 Governance of the programme")
    ch = W.committees["COM-03"]
    chair = [h for h in ch["chair_history"] if h["to"] is None][0]["person"]
    para(pk, f"The {ch['name']} is chaired by {person(chair, DATE)[0]}, {person(chair, DATE)[1]}. Its remit covers "
             f"{ch['remit'].lower()}.")
    filler(pk, ctx, "programme", 2)
    fill_to(pk, ctx, end, "programme", extra=("resilience", "returns"))
    pk.finish()
    return pk.pages


def seg_s9(ctx):
    start, end = 135, 140
    pk = new_segment(start, "sect")
    sect_head(pk, ctx, "9", "Governance and attestation",
              "This section describes the governance applied to claims, reserving and the preparation of this filing.")
    f = ctx.facts
    heading(pk, ctx, "9.1 Committees")
    for cid in ("COM-01", "COM-02"):
        ch = W.committees[cid]
        chair = [h for h in ch["chair_history"] if h["to"] is None or h["to"] >= DATE][-1]["person"]
        cn, ct = person(chair, DATE)
        pl = para(pk, f"The {ch['name']} is chaired by {cn}, {ct}. Remit: {ch['remit']}.")
        if cid == "COM-01":
            f.add("needle", "The Reserving Committee is chaired by Lena Kristiansen (Head of Reserving) at the filing date.",
                  f"Reserving Committee is chaired by {cn}", {"kind": "pdf_page", "page": pl[0][0]},
                  world_ref="COMMITTEE:COM-01#chair_history")
    filler(pk, ctx, "governance", 2)
    heading(pk, ctx, "9.2 Internal control and assurance")
    filler(pk, ctx, "governance", 3)
    heading(pk, ctx, "9.3 Attestations by accountable executives")
    rows = [["Area", "Accountable executive"]]
    for area, pid in (("Claims handling and conduct", "P005"), ("Technical provisions", "P009"),
                      ("Actuarial opinion", "P010"), ("Ledger reconciliation", "P021"),
                      ("Counter-fraud", "P008"), ("Regulatory reporting", "P020"), ("Compliance", "P037"),
                      ("Data protection", "P019")):
        n, t = person(pid, DATE)
        rows.append([area, Paragraph(f"{n}, {t}", S["cell"])])
    table_title(pk, ctx, "Table 9.1", "Attestations supporting this filing")
    w = pk.avail_width()
    pk.add(grid_table(rows, [90, w - 90], align_right_from=None))
    filler(pk, ctx, "governance", 2)
    fill_to(pk, ctx, end, "governance", extra=("returns",))
    pk.finish()
    return pk.pages


def seg_appA(ctx):
    start, end = 141, 143
    pk = new_segment(start, "sect3")
    sect_head(pk, ctx, "Appendix A", "Glossary",
              "Terms used in this filing. Variants used in other Corvane documents are given in brackets.")
    f = ctx.facts
    for g in W.glossary.values():
        variants = [v["term"] for v in g.get("variants", []) if "LD" in (v.get("families") or [])]
        var = f" ({'; '.join(variants)})" if variants else ""
        pk.add(Paragraph(f"<b>{g['canonical']}</b>{var}: {g['definition']}", S["body_left"]))
    filler_t = ["intro", "governance"]
    fill_to(pk, ctx, end, "intro", subheads=False)
    pk.finish()
    return pk.pages


def seg_appB(ctx):
    start, end = 144, 149
    pk = new_segment(start, "full")
    f, dt = ctx.facts, ctx.data
    sect = "Appendix B Statistical tables"
    pk.add(Paragraph(sect, S["h1"]))
    ctx.headings.append((1, sect, start))
    para(pk, "Table B.1 gives claims notified by product and month. The header row is repeated on each page.")
    mon = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    rows = [["Product", "Month", "Claims notified", "Cumulative", "Share of product year"]]
    for pid in dt.prod_ids:
        prod = W.get(f"PRODUCT:{pid}")
        cum = 0
        for i, n in enumerate(dt.monthly[pid]):
            cum += n
            rows.append([prod["name"], f"{mon[i]} 2025", f"{n:,}", f"{cum:,}", f"{100 * n / dt.notified[pid]:.1f}%"])
    table_title(pk, ctx, "Table B.1", "Claims notified by product and month, 2025")
    placed = pk.add(grid_table(rows, [FW - 280, 70, 70, 70, 70], pad=3.2))
    pages = sorted({p for p, _, _ in placed})
    hd = W.get("PRODUCT:PRD-HOM-DK")
    f.add("multipage_table", f"Table B.1 (repeated header): {hd['name']} December 2025 claims notified "
                             f"{dt.monthly['PRD-HOM-DK'][11]:,}.", f"Hjem Danmark Dec 2025 {dt.monthly['PRD-HOM-DK'][11]:,}",
          {"kind": "pdf_page", "page": placed[-1][0]}, notes=f"Table B.1 spans pages {pages[0]}-{pages[-1]}")
    filler(pk, ctx, "development", 1)
    fill_to(pk, ctx, end, "returns", subheads=False)
    pk.finish()
    return pk.pages


def seg_appC(ctx):
    start, end = 150, 150
    pk = new_segment(start, "full")
    f = ctx.facts
    sect = "Appendix C Contacts and references"
    pk.add(Paragraph(sect, S["h1"]))
    ctx.headings.append((1, sect, start))
    rows = [["Name", "Role", "Contact"]]
    for pid in ("P020", "P021", "P009", "P037"):
        p = W.people[pid]
        n, t = person(pid, DATE)
        rows.append([n, t, p.get("email", "")])
    for pid in ("P055", "P056"):
        n, t = person(pid, DATE)
        rows.append([n, f"{t}, NISA", W.people[pid].get("email", "")])
    pk.add(grid_table(rows, [130, 200, FW - 330], align_right_from=None))
    pl = pk.page_no
    f.add("general", "The filing's preparer is Bjørn Aasheim (Regulatory Reporting Manager), bjorn.aasheim@corvane-mutual.example.",
          "bjorn.aasheim@corvane-mutual.example", {"kind": "pdf_page", "page": pl}, world_ref="PERSON:P020#email")
    pk.add(Paragraph("Referenced documents", S["h2"]))
    for line in ("Claims Handling Manual (current edition)", "Claims Assessor Field Guide and Photo Atlas (2025 edition)",
                 "NISA Circular 2024/07 — Claims Handling Timeliness",
                 "NISA Circular 2026/04 — Fair Treatment in Fraud Referral",
                 "Quarterly Technical Provisions Returns (NISA-TP2) for 2025"):
        para(pk, "• " + line, "body_left")
    filler(pk, ctx, "intro", 2)
    fill_to(pk, ctx, end, "intro", subheads=False)
    pk.finish()
    return pk.pages


# ---------------------------------------------------------------------------------------------

def build():
    ctx = Ctx()
    out = out_path(FID)
    pages: dict[int, PageRec] = {}
    order = [seg_cover, seg_doccontrol, seg_attest, seg_s1, seg_s2a, seg_s2b, seg_s2c, seg_s3a, seg_s3b, seg_s3c,
             seg_s4a, seg_s4b, seg_s4c, seg_s5, seg_s6, seg_s7a, seg_s7b, seg_s8a, seg_s8b, seg_s8c, seg_s9,
             seg_appA, seg_appB, seg_appC]
    starts = {seg_cover: 1, seg_doccontrol: 2, seg_attest: 4, seg_s1: 5, seg_s2a: 11, seg_s2b: 20, seg_s2c: 22,
              seg_s3a: 29, seg_s3b: 33, seg_s3c: 54, seg_s4a: 67, seg_s4b: 86, seg_s4c: 90, seg_s5: 101,
              seg_s6: 107, seg_s7a: 111, seg_s7b: 112, seg_s8a: 125, seg_s8b: 126, seg_s8c: 128, seg_s9: 135,
              seg_appA: 141, seg_appB: 144, seg_appC: 150}
    for seg in order:
        recs = seg(ctx)
        s = starts[seg]
        for i, rec in enumerate(recs):
            if s + i in pages:
                raise RuntimeError(f"page {s + i} produced twice ({seg.__name__})")
            pages[s + i] = rec
    ctx.headings.sort(key=lambda h: h[2])
    pages[3] = seg_contents(ctx)[0]
    missing = [p for p in range(1, TOTAL_PAGES + 1) if p not in pages]
    if missing:
        raise RuntimeError(f"LD003 pages missing: {missing}")
    ordered = [pages[p] for p in range(1, TOTAL_PAGES + 1)]
    out.parent.mkdir(parents=True, exist_ok=True)
    an = W.anchor(FID)
    build_pdf(out, (PAGE_W, PAGE_H), TEMPLATES, ordered,
              {"title": an["title"], "author": person(an["author"], DATE)[0],
               "subject": "NISA-AFR annual filing, financial year 2025 (NISA-FRN 40417)",
               "keywords": "NISA-AFR; claims; reserving; technical provisions"})
    _post_check(ctx, out)
    return out, ctx.facts


def _post_check(ctx, out):
    """Resolve page numbers left open and check every needle against the PDF text layer."""
    import pymupdf
    from harness import extract as X
    doc = pymupdf.open(str(out))
    texts = [pg.get_text("text") for pg in doc]
    if doc.page_count != TOTAL_PAGES:
        raise RuntimeError(f"LD003 has {doc.page_count} pages, expected {TOTAL_PAGES}")
    errors = []
    for e in ctx.facts.items:
        loc = e["locator"]
        hits = [i + 1 for i, t in enumerate(texts) if X.match(e["needle"], t)]
        if loc.get("page") is None:
            if not hits:
                errors.append(f"{e['fact_id']}: needle not found anywhere: {e['needle']!r}")
                continue
            loc["page"] = hits[0]
        if not X.match(e["needle"], texts[loc["page"] - 1]) and not e.get("placement"):
            near = [h for h in hits if abs(h - loc["page"]) == 1]
            if near:
                loc["page"] = near[0]
        if not X.match(e["needle"], texts[loc["page"] - 1]):
            errors.append(f"{e['fact_id']}: needle {e['needle']!r} not on page {loc['page']} (found on {hits[:6]})")
    if errors:
        raise RuntimeError("LD003 needle check failed:\n  " + "\n  ".join(errors))
    # exclusivity inside the file: the IBNR / TP figures and the 97.3% appear only where planted
    for needle, allowed in (("611.9", {87}), ("2,318.4", {87}), ("97.3%", {33})):
        pages = {i + 1 for i, t in enumerate(texts) if needle in t}
        if not pages <= allowed:
            raise RuntimeError(f"LD003: {needle} appears on pages {sorted(pages)}, allowed {sorted(allowed)}")
    head = X.normalize(HEADER_TEXT)
    for i, t in enumerate(texts):
        if head not in X.normalize(t):
            raise RuntimeError(f"LD003 header missing on page {i + 1}")
    ctx.facts.add("header", "Every page header of the filing shows 'Corvane Mutual Insurance Society Limited — NISA-FRN 40417'.",
                  HEADER_TEXT, {"kind": "pdf_page", "page": 2}, world_ref="ORG:company#nisa_firm_reference",
                  placement="PL-027", placement_key="ld3_frn",
                  notes="Running header drawn on every page (1-150) by the page template; PDF has no header object.")

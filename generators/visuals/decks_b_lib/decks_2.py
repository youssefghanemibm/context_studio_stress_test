"""VS020-VS024 deck builders."""
from __future__ import annotations

from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN

from . import phrases as PH
from . import raster as R
from .common import approvers, contacts_slide, email, glossary_slide, guard, history, next_steps_slide, person, risks_slide
from .core import (AMBER, CONTENT_LEFT, CONTENT_TOP, CONTENT_W, GREEN, GREY, GREY_LT, NAVY, RED, SAND, TEAL, TEAL_LT,
                   WHITE, Deck, fmt_date, minus_days)


def _swimlane(dk, s, lanes, steps, top=1.45, height=5.3, left=0.55, width=12.25, header_w=0.5, box_w=1.7,
              box_h=0.62, label_fn=None, flow=None, size=10):
    """Draw lanes (rotated headers) and step boxes placed in their lane; returns {step_id: shape}.

    steps: list of (step_id, label, lane_index, column). The owner of each step is visible only from the
    lane the box sits in. flow: list of (from_id, to_id, label or None)."""
    lh = height / len(lanes)
    for i, ln in enumerate(lanes):
        dk.lane(s, left, top + i * lh, width, lh, ln, i, name=f"lane-{i + 1}", label_w=header_w)
    ncols = max(c for _, _, _, c in steps) + 1
    col_w = (width - header_w - 0.3) / ncols
    shapes = {}
    for sid, label, li, col in steps:
        x = left + header_w + 0.15 + col * col_w + (col_w - box_w) / 2
        y = top + li * lh + (lh - box_h) / 2
        shapes[sid] = dk.box(s, x, y, box_w, box_h, label, size=size, bold=True, name=f"step-{sid}")
    for a, b, lab in (flow or []):
        sa, sb = shapes[a], shapes[b]
        ay, by_ = sa.top, sb.top
        if abs(ay - by_) < 10000:
            sites = (3, 1)
        elif sa.left + sa.width < sb.left:
            sites = (3, 1)
        else:
            sites = (2, 0) if by_ > ay else (0, 2)
        dk.connect(s, sa, sb, sites[0], sites[1], label=lab, elbow=(abs(ay - by_) >= 10000), label_size=8,
                   label_w=1.2 if lab else None, label_offset=(0, -0.26), width_pt=1.2)
    return shapes


# =========================================================================================
# VS020 Board Update Q3 2026 (2026-10-22)
# =========================================================================================
def build_vs020(W, out_dir):
    fid = "VS020"
    dk = Deck(W, fid, out_dir, short_title="Board Update Q3 2026", classification="Confidential – Board")
    d = dk.date
    C = W.company
    fin25, q3 = C["financials"]["fy2025"], C["financials"]["q3_2026"]
    M = W.timeline["metrics"]
    assert W.alias_holder("the CFO", d) == "P001"
    for f in ["fy2025.ibnr_gbp_m", "fy2025.fnol_ack_within_2bd_pct"]:
        assert not W.may_state(fid, "ORG:company", "financials." + f)
    for f in ["programme_spend_cumulative_gbp_m.2026Q3", "fraud_referral_rate_pct_of_scored",
              "avg_settlement_days_2026H1", "fnol_channel_mix_pct.2026YTD", "fnol_channel_mix_pct.2024"]:
        assert not W.may_state(fid, "TIMELINE:metrics", f)
    assert not W.may_state(fid, "WAVE:MW-1", "claims_migrated")
    guard(W, fid, [("ORG:company", "financials.q3_2026.combined_ratio_pct"),
                   ("ORG:company", "financials.fy2025.combined_ratio_pct"),
                   ("ORG:company", "financials.fy2025.gross_written_premium_gbp_m"),
                   ("ORG:company", "financials.fy2025.gross_claims_incurred_gbp_m"),
                   ("ORG:company", "financials.fy2025.claims_notified"), ("ORG:company", "financials.fy2025.fraud_referrals"),
                   ("ORG:company", "financials.fy2025.confirmed_fraud_cases"),
                   ("ORG:company", "financials.fy2025.fraud_savings_gbp_m"),
                   ("TIMELINE:metrics", "claims_notified"), ("TIMELINE:metrics", "fraud_referrals_count"),
                   ("TIMELINE:metrics", "wave1_open_defects"), ("TIMELINE:metrics", "contingency_drawdown_gbp_m"),
                   ("DECISION:DEC-010", None), ("DECISION:DEC-011", None), ("DECISION:DEC-014", None),
                   ("PERSON:P001", "aliases"), ("REPORT:NISA-FR1", "submissions")])

    s = dk.title_slide("Board Update – Q3 2026", "Finance, claims performance and Programme Skerry",
                       [f"Presented by {W.name_of('P001', d)}, Chief Financial Officer",
                        f"Board of Directors  |  {fmt_date(d)}  |  Classification: Confidential – Board"])
    # 2 agenda
    dk.agenda_slide(["Underwriting performance", "Claims volumes and counter-fraud", "FY2025 reference results",
                     "Programme Skerry: waves, budget and stabilisation", "Regulatory matters",
                     "Outlook and items for the Board"])
    # 3 combined ratio chart (PL-117 chart only) + notes PL-118
    s = dk.new_slide("Underwriting performance: combined ratio")
    dk.chart(s, "column", ["FY2025", "Q3 2026"], {"Combined ratio (%)": [fin25["combined_ratio_pct"],
                                                                           q3["combined_ratio_pct"]]},
             CONTENT_LEFT + 0.3, CONTENT_TOP, 7.4, 5.3, title="Combined ratio (%)", number_format="0.0",
             legend=False, name="combined-ratio-chart")
    dk.text(s, 8.4, CONTENT_TOP + 0.3, 4.4, 4.5,
            ["Q3 2026 shown against the FY2025 outturn",
             "Figures are management information for the quarter",
             "The analysis of movements is in the finance pack",
             "Commentary on reserving movements is in the Reserving Committee pack"],
            size=15, bullets=True, para_space=12)
    dk.fact("chart_only", "Combined ratio Q3 2026: 97.8% (native chart only).", 3, "chart", "Q3 2026=97.8",
            placement="PL-117")
    dk.fact("chart_only", "Combined ratio FY2025: 98.4% (chart comparator).", 3, "chart", "FY2025=98.4",
            world_ref="ORG:company#financials.fy2025.combined_ratio_pct")
    dk.notes(s, "Speaker: PR (CFO). PR opens with the combined ratio trend against the FY2025 outturn, then hands to "
                "the Claims Director for the operational view. Keep the detail on reserves for the Reserving "
                "Committee item.")
    dk.fact("speaker_notes", "Speaker notes refer to the CFO as 'PR'.", 3, "notes", "Speaker: PR (CFO)",
            placement="PL-118")

    # 4 claims volumes and referrals (charts)
    s = dk.new_slide("Claims volumes and counter-fraud")
    cn, fr = M["claims_notified"], M["fraud_referrals_count"]
    dk.chart(s, "column", ["Q2 2026", "Q3 2026"], {"Claims notified": [cn["2026Q2"], cn["2026Q3"]]},
             CONTENT_LEFT, CONTENT_TOP, 6.0, 5.0, title="Claims notified", number_format="#,##0", legend=False,
             name="claims-notified-chart")
    dk.chart(s, "column", ["Q2 2026", "Q3 2026"], {"Fraud referrals": [fr["2026Q2"], fr["2026Q3"]]},
             CONTENT_LEFT + 6.3, CONTENT_TOP, 6.0, 5.0, title="Fraud referrals", number_format="#,##0", legend=False,
             name="fraud-referrals-chart", colors=[NAVY])
    dk.text(s, CONTENT_LEFT, 6.45, CONTENT_W, 0.4,
            "Referral volumes reflect the Circular 2026/04 rules in force since April; the Tier-3 change applies from "
            "October.", size=12, color=GREY, italic=True)
    dk.fact("chart_only", "Claims notified Q3 2026: 55,180 (chart).", 4, "chart", "Claims notified: Q3 2026=55180",
            world_ref="TIMELINE:metrics#claims_notified.2026Q3")
    dk.fact("chart_only", "Fraud referrals Q2 2026: 1,488; Q3 2026: 1,530 (chart).", 4, "chart",
            "Fraud referrals: Q3 2026=1530", world_ref="TIMELINE:metrics#fraud_referrals_count.2026Q3")
    dk.notes(s, "the CFO: volumes up quarter on quarter, in line with seasonal expectations. Referral numbers are "
                "those reported to NISA on the FR1 return.")

    # 5 FY2025 reference results
    s = dk.new_slide("FY2025 reference results")
    rows = [["Measure", "FY2025"],
            ["Gross written premium", f"£{fin25['gross_written_premium_gbp_m']:,.1f}m"],
            ["Gross claims incurred", f"£{fin25['gross_claims_incurred_gbp_m']:,.1f}m"],
            ["Claims notified", f"{fin25['claims_notified']:,}"],
            ["Fraud referrals", f"{fin25['fraud_referrals']:,}"],
            ["Confirmed fraud cases", f"{fin25['confirmed_fraud_cases']:,}"],
            ["Fraud savings", f"£{fin25['fraud_savings_gbp_m']:,.1f}m"],
            ["Average settlement days – motor / home",
             f"{fin25['avg_settlement_days_motor']} / {fin25['avg_settlement_days_home']}"]]
    dk.table(s, rows, w=8.0, col_w=[5.0, 3.0], size=15, row_h=0.55, name="FY2025 results")
    dk.text(s, 9.0, CONTENT_TOP + 0.2, 3.8, 3.0, ["Audited figures as filed in the annual report.",
                                                 "Shown for context only; no restatement."], size=13, color=GREY)
    dk.fact("general", "FY2025 gross written premium was £2,140.0m.", 5, "table", "Gross written premium £2,140.0m",
            world_ref="ORG:company#financials.fy2025.gross_written_premium_gbp_m")
    dk.fact("general", "FY2025 fraud savings were £38.7m from 1,109 confirmed fraud cases.", 5, "table",
            "Confirmed fraud cases 1,109 Fraud savings £38.7m", world_ref="ORG:company#financials.fy2025.fraud_savings_gbp_m")
    dk.fact("general", "FY2025 average settlement days: motor 34, home 51.", 5, "table",
            "Average settlement days – motor / home 34 / 51",
            world_ref="ORG:company#financials.fy2025.avg_settlement_days_motor")

    # 6 programme milestones (group tiles)
    s = dk.new_slide("Programme Skerry: where we are")
    tiles = [("Wave 0 – Denmark", f"Complete  |  {fmt_date(W.waves['MW-0']['date'])}", GREEN),
             ("Wave 1 – UK motor", f"Complete  |  {fmt_date(W.waves['MW-1']['date'])}", GREEN),
             ("Wave 2", f"Confirmed for {fmt_date(W.waves['MW-2']['date'])}", AMBER),
             ("CLARA decommissioning", f"Target {fmt_date(W.systems['SYS01']['decommission_target'])}", GREY)]
    for i, (h, b, col) in enumerate(tiles):
        g = dk.group(s, f"grp-milestone-{i + 1}")
        x = CONTENT_LEFT + i * 3.07
        dk.box(s, x, CONTENT_TOP + 0.4, 2.95, 0.7, h, shape=MSO_SHAPE.RECTANGLE, fill=col, line=None, color=WHITE,
               size=15, bold=True, group=g, name=f"milestone-hdr-{i + 1}")
        dk.box(s, x, CONTENT_TOP + 1.1, 2.95, 1.2, b, shape=MSO_SHAPE.RECTANGLE, fill=GREY_LT, line=None, size=14,
               group=g, name=f"milestone-body-{i + 1}")
    dk.text(s, CONTENT_LEFT, 4.3, CONTENT_W, 2.2,
            ["Wave 2 scope: UK home, commercial and liability; Norway; Sweden",
             "The Steering Committee confirmed the Wave 2 date on 8 October 2026",
             "Claims Hub is now the system of record for Danish and UK motor claims"],
            size=15, bullets=True, para_space=10)
    dk.fact("visual_only", "Wave 2 confirmed for 15 February 2027 (milestone tile).", 6, "group",
            "Confirmed for 15 February 2027", world_ref="DECISION:DEC-011", shape_name="grp-milestone-3")
    dk.fact("visual_only", "Wave 1 – UK motor completed 14 September 2026.", 6, "group", "Complete | 14 September 2026",
            world_ref="WAVE:MW-1#date", shape_name="grp-milestone-2")
    dk.notes(s, "the CFO: the Wave 2 date was confirmed at the October Steering Committee chaired by the COO.")

    # 7 budget and contingency
    s = dk.new_slide("Programme budget and contingency")
    items = [f"Approved programme budget: £{C['programme']['budget_gbp_m']}m (business case signed November 2024)",
             f"Contingency drawdown of £{M['contingency_drawdown_gbp_m']['2026-10-08']}m for Wave 2, approved by the "
             f"CFO, {W.name_of('P001', d)}, on 8 October 2026",
             "Drawdown approved at the October Steering Committee",
             "Spend reporting continues monthly through the Steering Committee pack"]
    dk.bullets(s, items, size=17)
    dk.fact("general", "A £1.8m contingency drawdown for Wave 2 was approved by the CFO, Priya Raman, on 8 October "
                       "2026.", 7, "text", "Contingency drawdown of £1.8m for Wave 2", world_ref="DECISION:DEC-010")
    dk.fact("general", "Programme Skerry's approved budget is £48.6m.", 7, "text", "Approved programme budget: £48.6m",
            world_ref="ORG:company#programme.budget_gbp_m")

    # 8 Wave 1 stabilisation (KPI tiles rendered as one image)
    s = dk.new_slide("Wave 1 stabilisation")
    wd = M["wave1_open_defects"]
    cv = R.Canvas(1100, 620)
    cv.title(f"Wave 1 open defects at {fmt_date(wd['date'], 'short')}", size=30)
    for i, (sev, n, trend, col) in enumerate([("Sev1", wd["sev1"], "none open", R.GREEN),
                                              ("Sev2", wd["sev2"], "reducing", R.AMBER),
                                              ("Sev3", wd["sev3"], "reducing", R.GREY)]):
        y = 130 + i * 150
        cv.d.rounded_rectangle([40, y, 1060, y + 120], radius=14, fill=R.GREY_LT, outline=col, width=4)
        cv.d.rectangle([40, y, 60, y + 120], fill=col)
        cv.text((100, y + 20), f"{sev}: {n} open", size=36, bold=True, fill=R.NAVY)
        cv.text((100, y + 72), f"Trend: {trend}", size=26, fill=R.BLACK)
    dk.picture(s, cv.png(), CONTENT_LEFT, CONTENT_TOP + 0.2, w=6.2, alt="Open Wave 1 defects by severity.",
               name="defects-image")
    dk.text(s, 7.2, CONTENT_TOP + 0.3, 5.6, 4.5,
            ["Defect counts as reported to the Steering Committee",
             "No severity 1 defects open",
             "Remaining defects are tracked through the release plan"], size=15, bullets=True, para_space=12)
    dk.fact("image_text", "Wave 1 open defects at 5 Oct 2026: Sev2 14.", 8, "image", "Sev2: 14 open",
            world_ref="TIMELINE:metrics#wave1_open_defects.sev2")
    dk.fact("image_text", "Wave 1 open defects at 5 Oct 2026: Sev3 57.", 8, "image", "Sev3: 57 open",
            world_ref="TIMELINE:metrics#wave1_open_defects.sev3")

    # 9 regulatory
    s = dk.new_slide("Regulatory matters")
    sub = W.reports["NISA-FR1"]["submissions"]
    items = [f"NISA-FR1 Q2 2026 return submitted {fmt_date(sub['2026Q2']['submitted'])} (due "
             f"{fmt_date(sub['2026Q2']['due'])})",
             f"NISA-FR1 Q3 2026 return due {fmt_date(sub['2026Q3']['due'])}; on track",
             "From 1 October 2026 Tier-3 claims are referred to SIU at a Sentinel score of 60 or more; the general "
             "threshold stays 65",
             "No claim is declined on the basis of the score alone (Circular 2026/04 §3.1)"]
    dk.bullets(s, items, size=16)
    dk.fact("general", "NISA-FR1 Q2 2026 return submitted 29 July 2026 (due 30 July 2026).", 9, "text",
            "NISA-FR1 Q2 2026 return submitted 29 July 2026", world_ref="REPORT:NISA-FR1#submissions.2026Q2")
    dk.fact("general", "From 1 October 2026 Tier-3 claims are referred to SIU at a Sentinel score of 60 or more; the "
                       "general threshold stays 65.", 9, "text",
            "Tier-3 claims are referred to SIU at a Sentinel score of 60 or more", world_ref="DECISION:DEC-014")

    # 10 outlook / risks
    risks_slide(dk, title="Outlook and principal risks", k=4,
                extra=[("Wave 2 complexity: UK home, commercial and liability plus Norway and Sweden in one cut-over",
                        "Wave 2 plan and rehearsals tracked monthly by the Steering Committee")])
    # 11 items for the board
    s = dk.new_slide("Items for the Board")
    dk.bullets(s, ["Note the Q3 2026 underwriting result", "Note the Wave 2 date and the contingency drawdown",
                   "Note the Tier-3 fraud referral change effective 1 October 2026",
                   "Approve the forward plan for the Q4 update"], size=18)
    dk.notes(s, "the CFO to take questions; the COO and the Claims Director are available for programme detail.")
    # 12 glossary
    glossary_slide(dk, [("Combined ratio", "Claims and expenses as a share of earned premium"),
                        ("FR1", "NISA quarterly fraud referral return"),
                        ("Tier-3", "Highest claim tier under BR-TRI-003"),
                        ("Wave", "A migration cut-over from CLARA to Claims Hub")])
    return dk


# =========================================================================================
# VS021 Claims Hub Training for Claims Handlers (2026-08-31)
# =========================================================================================
def _ui_banner(cv):
    cv.d.rectangle([260, 70, cv.w, 104], fill=R.AMBER_LT)
    cv.text((300, 75), "TRAINING ENVIRONMENT – sample data only", size=22, bold=True, fill=R.BLACK)


def _scr_login():
    cv = R.Canvas(1600, 900, bg=R.GREY_LT)
    cv.d.rectangle([0, 0, 1600, 70], fill=R.NAVY)
    cv.text((28, 18), "Corvane Identity Service", size=28, bold=True, fill=R.WHITE)
    cv.d.rounded_rectangle([500, 170, 1100, 760], radius=16, fill=R.WHITE, outline=R.GREY_MD, width=2)
    cv.text((800, 210), "Sign in to Claims Hub", size=32, bold=True, fill=R.NAVY, anchor="ma")
    R.field(cv, 560, 290, "Corvane username", "trainee.handler07", w=480)
    R.field(cv, 560, 410, "Password", "•" * 12, w=480)
    R.button(cv, 560, 550, "Sign in", w=480)
    cv.text((800, 640), "Single sign-on for workforce users", size=22, fill=R.GREY, anchor="ma")
    cv.text((800, 680), "Partners sign in through the Assessor Portal", size=22, fill=R.GREY, anchor="ma")
    return cv.png()


def _scr_fnol():
    cv = R.Canvas(1600, 1000)
    R.web_chrome(cv, "Claims Hub", "Trainee Handler 07", ["Work queue", "New FNOL", "Claims", "Payments", "Reports"],
                 1, "")
    _ui_banner(cv)
    cv.text((300, 125), "New FNOL  >  Home claim", size=24, fill=R.GREY)
    cv.text((300, 170), "First notice of loss", size=34, bold=True, fill=R.NAVY)
    R.field(cv, 300, 240, "Policy number", "HOMDK-TRN-004512", w=440, required=True)
    R.field(cv, 300, 360, "Product", "Hjem Danmark", w=440)
    R.field(cv, 300, 480, "Date of loss", "12/08/2026", w=440, required=True)
    R.field(cv, 300, 600, "Loss location", "Postnummer 2150", w=440, required=True)
    R.field(cv, 300, 720, "Description of loss", "", w=440, required=True)
    # Claim Type drop-down open, nothing else on its right
    R.field(cv, 860, 240, "Claim Type", "Select…", w=500, required=True, dropdown=True, focus=True)
    items = ["Escape of Water", "Storm", "Frost Damage", "Snow Load"]
    cv.d.rectangle([860, 326, 1360, 326 + 64 * len(items)], fill=R.WHITE, outline=R.TEAL, width=3)
    for i, it in enumerate(items):
        y = 326 + 64 * i
        if i == 2:
            cv.d.rectangle([863, y + 3, 1357, y + 61], fill=R.TEAL_LT)
        cv.text((884, y + 17), it, size=26, fill=R.BLACK)
    R.button(cv, 860, 820, "Create claim")
    R.button(cv, 1080, 820, "Save draft", primary=False)
    return cv.png()


def _scr_queue():
    cv = R.Canvas(1600, 900)
    R.web_chrome(cv, "Claims Hub", "Trainee Handler 07", ["Work queue", "New FNOL", "Claims", "Payments", "Reports"],
                 0, "")
    _ui_banner(cv)
    cv.text((300, 130), "My work queue", size=34, bold=True, fill=R.NAVY)
    rows = [["Claim", "Product", "Claim Type", "Tier", "Next action"],
            ["CLM-UK-2026-TRN01", "Motor Private UK", "Collision", "Tier-2", "Call customer"],
            ["CLM-UK-2026-TRN02", "Motor Private UK", "Windscreen", "Tier-1", "Approve repair"],
            ["CLM-UK-2026-TRN03", "Motor Private UK", "Theft", "Tier-2", "Chase police ref"],
            ["CLM-UK-2026-TRN04", "Motor Private UK", "Bodily Injury", "Tier-3", "Reserve review"],
            ["CLM-DK-2026-TRN05", "Hjem Danmark", "Storm", "Tier-1", "Appoint assessor"]]
    x0, y0, cws = 300, 200, [300, 280, 230, 130, 300]
    for r, row in enumerate(rows):
        y = y0 + r * 64
        cv.d.rectangle([x0, y, x0 + sum(cws), y + 64], fill=R.NAVY if r == 0 else (R.GREY_LT if r % 2 == 0 else R.WHITE))
        x = x0
        for c, val in enumerate(row):
            cv.text((x + 12, y + 18), val, size=22, bold=(r == 0), fill=R.WHITE if r == 0 else R.BLACK)
            x += cws[c]
    cv.text((300, 620), "Filter: tier, product, due date", size=22, fill=R.GREY)
    return cv.png()


def _scr_summary(rsv_auth: int):
    cv = R.Canvas(1600, 960)
    R.web_chrome(cv, "Claims Hub", "Trainee Handler 07", ["Work queue", "New FNOL", "Claims", "Payments", "Reports"],
                 2, "")
    _ui_banner(cv)
    cv.text((300, 130), "CLM-UK-2026-TRN04  |  Motor Private UK  |  Bodily Injury", size=28, bold=True, fill=R.NAVY)
    cv.d.rounded_rectangle([300, 190, 470, 240], radius=10, fill=R.RED)
    cv.text((385, 200), "Tier-3", size=24, bold=True, fill=R.WHITE, anchor="ma")
    cv.text((500, 200), "Routed to Major & Complex Loss", size=24, fill=R.BLACK)
    cv.d.rectangle([300, 280, 900, 640], fill=R.WHITE, outline=R.GREY_MD, width=2)
    cv.text((320, 295), "Reserves", size=28, bold=True, fill=R.NAVY)
    for i, (k, v) in enumerate([("Indemnity", "£48,000.00"), ("Expense", "£7,200.00"), ("Next review", "in 14 days")]):
        cv.text((320, 360 + i * 56), k, size=24, fill=R.GREY)
        cv.text((620, 360 + i * 56), v, size=24, fill=R.BLACK)
    cv.text((320, 560), f"Your reserve authority: £{rsv_auth:,}", size=24, bold=True, fill=R.TEAL)
    cv.d.rectangle([940, 280, 1540, 640], fill=R.WHITE, outline=R.GREY_MD, width=2)
    cv.text((960, 295), "Fraud and alerts", size=28, bold=True, fill=R.NAVY)
    cv.text((960, 360), "Sentinel score: 42", size=24, fill=R.BLACK)
    cv.text((960, 416), "No SIU referral", size=24, fill=R.BLACK)
    cv.text((960, 472), "Vulnerable customer: no", size=24, fill=R.BLACK)
    R.button(cv, 300, 690, "Post reserve movement")
    R.button(cv, 640, 690, "Request approval", primary=False)
    return cv.png()


def _scr_fraud():
    cv = R.Canvas(1600, 820)
    R.web_chrome(cv, "Claims Hub", "Trainee Handler 07", ["Work queue", "New FNOL", "Claims", "Payments", "Reports"],
                 2, "")
    _ui_banner(cv)
    cv.text((300, 130), "CLM-UK-2026-TRN06  |  Motor Private UK  |  Theft", size=28, bold=True, fill=R.NAVY)
    cv.d.rectangle([300, 200, 1540, 300], fill=R.AMBER_LT, outline=R.AMBER, width=3)
    cv.text((330, 215), "SIU referral created – do not discuss the referral with the customer", size=26, bold=True,
            fill=R.BLACK)
    cv.text((330, 258), "Customer notice due within 10 business days unless a deferral is certified", size=24,
            fill=R.BLACK)
    cv.text((300, 350), "Sentinel score: 71", size=26, fill=R.BLACK)
    cv.text((300, 400), "Decline on score alone: not permitted", size=26, fill=R.BLACK)
    R.button(cv, 300, 480, "View referral")
    return cv.png()


def _scr_clara():
    lines = ["!CLRM010                    CLARA - FNOL CAPTURE                  FN01",
             "",
             "!POLICY-NO  ==> HOMUK00451",
             "",
             "!LOSS-DATE  ==> 12/08/2026",
             "",
             "!PERIL      ==> EOW",
             "",
             "!CHANNEL    ==> TEL",
             "",
             "!LOSS-DESC  ==> LEAK FROM UPSTAIRS BATHROOM",
             "",
             "!CALLER-PHONE ==> 07700900999",
             "",
             "",
             " PF3=EXIT  PF7=BACK  PF8=FORWARD  PF12=CANCEL"]
    return R.green_screen(lines, cols=70, size=30)


def build_vs021(W, out_dir):
    fid = "VS021"
    dk = Deck(W, fid, out_dir, short_title="Claims Hub Training – Claims Handlers")
    d = dk.date
    bms = W.bms_maps["CLRM010"]
    assert bms["transaction"] == "FN01" and any(f["name"] == "PERIL" for f in bms["fields"])
    rv = {r: W.rule_version(r, d) for r in ["BR-FNOL-001", "BR-FNOL-002", "BR-FNOL-003", "BR-FNOL-004", "BR-FNOL-006",
                                            "BR-TRI-003", "BR-TRI-006", "BR-RSV-001", "BR-RSV-003", "BR-RSV-007",
                                            "BR-STL-002", "BR-STL-007", "BR-STL-001", "BR-FRD-031", "BR-FRD-032",
                                            "BR-FRD-033"]}
    assert rv["BR-FRD-031"]["version"] == 1 and rv["BR-RSV-007"]["version"] == 3 and rv["BR-FNOL-001"]["version"] == 3
    guard(W, fid, [("GLOSSARY:G-006", None), ("BMS:CLRM010", None), ("RULE:BR-STL-002@v3", "parameters"),
                   ("RULE:BR-RSV-003@v3", "parameters"), ("RULE:BR-FRD-031@v1", "parameters"),
                   ("RULE:BR-FRD-032@v2", "parameters"), ("RULE:BR-TRI-006@v3", "parameters"),
                   ("RULE:BR-RSV-007@v3", "parameters"), ("RULE:BR-FNOL-001@v3", "parameters")])
    stl = rv["BR-STL-002"]["parameters"]
    rsv = rv["BR-RSV-003"]["parameters"]

    s = dk.title_slide("Claims Hub Training for Claims Handlers", "Module 2: Claims Hub essentials for Wave 1 "
                       "(UK motor)", [f"Course owner: {person(W, 'P017', d)}",
                                      f"Claims Hub Product  |  {fmt_date(d)}  |  Classification: Internal"])
    dk.notes(s, "Facilitator: allow 90 minutes. Learners need a training login; the training environment uses sample "
                "data only.")
    dk.agenda_slide(["Signing in and finding your work", "Registering a claim (FNOL)", "Tiers, reserves and authority",
                     "From CLARA to Claims Hub: what is called what", "Fraud referrals and payments",
                     "Go-live support and knowledge check"], title="Learning objectives")
    # 3 sign in
    s = dk.new_slide("Signing in")
    dk.picture(s, _scr_login(), CONTENT_LEFT, CONTENT_TOP, w=7.6,
               alt="Claims Hub sign-in screen provided by the Corvane Identity Service.", name="scr-login")
    dk.text(s, 8.5, CONTENT_TOP + 0.2, 4.3, 4.5,
            ["Use your normal Corvane username – single sign-on through the Corvane Identity Service",
             "Your role decides which menus you see",
             "Locked out? The service desk can reset access the same day"], size=14, bullets=True, para_space=12)
    dk.fact("screenshot", "Claims Hub sign-in is provided by the Corvane Identity Service (screenshot).", 3, "image",
            "Corvane Identity Service", world_ref="SYSTEM:SYS16")
    # 4 FNOL screenshot (PL-119)
    s = dk.new_slide("Registering a claim: the FNOL screen")
    dk.picture(s, _scr_fnol(), CONTENT_LEFT, CONTENT_TOP - 0.05, w=8.6,
               alt="Claims Hub FNOL screen with the Claim Type drop-down open for a Danish home policy.",
               name="scr-fnol")
    dk.text(s, 9.4, CONTENT_TOP + 0.1, 3.4, 5.0,
            ["Claim Type replaces the CLARA PERIL code",
             "The list only offers the claim types that the product covers",
             "Dashboards call this field 'loss type'",
             "Example shows a Danish home policy, live since Wave 0"], size=13, bullets=True, para_space=10)
    dk.fact("screenshot", "Claims Hub FNOL screenshot: the 'Claim Type' drop-down lists Escape of Water, Storm, Frost "
                          "Damage, Snow Load.", 4, "image", "Frost Damage", placement="PL-119",
            notes="Raster only; the drop-down items are Escape of Water, Storm, Frost Damage and Snow Load.")
    dk.fact("screenshot", "FNOL screenshot drop-down includes 'Snow Load'.", 4, "image", "Snow Load",
            world_ref="CLAIMTYPE:CT-SNO")
    dk.fact("screenshot", "FNOL screenshot drop-down includes 'Escape of Water'.", 4, "image", "Escape of Water",
            world_ref="CLAIMTYPE:CT-EOW")
    dk.fact("terminology", "Dashboards call the Claim Type field 'loss type'.", 4, "text",
            "Dashboards call this field 'loss type'", world_ref="GLOSSARY:G-006")
    dk.fact("alt_text", "Alt text: FNOL screen with the Claim Type drop-down open for a Danish home policy.", 4,
            "alt_text", "Claim Type drop-down open for a Danish home policy")
    # 5 mandatory data
    s = dk.new_slide("What the FNOL must capture")
    items = [rv["BR-FNOL-002"]["text"].rstrip(".") + " (BR-FNOL-002)",
             rv["BR-FNOL-006"]["text"].rstrip(".") + " (BR-FNOL-006)",
             rv["BR-FNOL-004"]["text"].rstrip(".") + " (BR-FNOL-004)",
             rv["BR-FNOL-003"]["text"].rstrip(".") + " (BR-FNOL-003)"]
    dk.bullets(s, items, size=15)
    dk.fact("general", "Motor FNOLs must capture the vehicle registration (BR-FNOL-006).", 5, "text",
            "Motor FNOLs must capture the vehicle registration", world_ref="RULE:BR-FNOL-006@v1")
    dk.fact("general", "Duplicate check: existing claim on the same policy with date of loss within ±3 days "
                       "(BR-FNOL-004).", 5, "text", "date of loss within ±3 days", world_ref="RULE:BR-FNOL-004@v1")
    # 6 work queue
    s = dk.new_slide("Your work queue")
    dk.picture(s, _scr_queue(), CONTENT_LEFT, CONTENT_TOP, w=8.6, alt="Claims Hub work queue with sample claims.",
               name="scr-queue")
    dk.text(s, 9.4, CONTENT_TOP + 0.1, 3.4, 5.0, PH.pick(dk.rng, PH.TRAINING_TIPS, 3), size=13, bullets=True,
            para_space=10)
    # 7 tiers
    s = dk.new_slide("Tiers and fast-track")
    rows = [["Tier", "When", "What happens"],
            ["Tier-3", "Estimated incurred ≥ £50,000, any bodily injury, solicitor or litigation at notification, "
                       "or property total loss", "Routed to Major & Complex Loss"],
            ["Tier-2", "£5,000–£49,999 or any third-party involvement", "Specialist claim handlers"],
            ["Tier-1", "Below £5,000, no injury, no third party", "Fast-track if eligible"]]
    dk.table(s, rows, col_w=[1.2, 6.6, 4.2], size=13, row_h=0.75, name="Tier table")
    dk.text(s, CONTENT_LEFT, 4.7, CONTENT_W, 1.6,
            [rv["BR-TRI-006"]["text"].rstrip(".") + " (BR-TRI-006 v3, from 1 July 2026)"], size=14, bullets=True)
    dk.fact("general", "Fast-track: Tier-1, Sentinel score below 30, no injury; cap £2,000 (BR-TRI-006 v3).", 7, "text",
            "cap £2,000", world_ref="RULE:BR-TRI-006@v3#parameters")
    # 8 summary and reserves
    s = dk.new_slide("Claim summary and reserves")
    dk.picture(s, _scr_summary(rsv["claims_handler"]), CONTENT_LEFT, CONTENT_TOP - 0.05, w=8.4,
               alt="Claim summary for a Tier-3 bodily injury claim with the reserves panel.", name="scr-summary")
    dk.text(s, 9.2, CONTENT_TOP + 0.1, 3.6, 5.0,
            [rv["BR-RSV-001"]["text"].rstrip(".") + " (BR-RSV-001)",
             "Tier-3 reserves are reviewed at least every 14 days (BR-RSV-007 v3)",
             "Movements above your authority go to the approval queue"], size=13, bullets=True, para_space=10)
    dk.fact("screenshot", "Reserves panel screenshot: Claims Handler reserve authority £25,000.", 8, "image",
            "Your reserve authority: £25,000", world_ref="RULE:BR-RSV-003@v3#parameters.claims_handler")
    dk.fact("general", "Tier-3 reserves are reviewed at least every 14 days (BR-RSV-007 v3).", 8, "text",
            "reviewed at least every 14 days (BR-RSV-007 v3)", world_ref="RULE:BR-RSV-007@v3")
    # 9 CLARA comparison (PL-120)
    s = dk.new_slide("If you used CLARA: the old FNOL screen")
    dk.picture(s, _scr_clara(), CONTENT_LEFT, CONTENT_TOP, w=7.8,
               alt="CLARA green-screen FNOL capture map for comparison.", name="scr-clara")
    dk.text(s, 8.7, CONTENT_TOP + 0.1, 4.1, 5.0,
            ["CLARA captured the claim type as a peril code",
             "Claims Hub shows the full Claim Type name",
             "CLARA remains the system of record for claims not yet migrated",
             "Do not rekey claims from CLARA into Claims Hub"], size=14, bullets=True, para_space=10)
    dk.fact("screenshot", "CLARA screenshot of map CLRM010 (transaction FN01) shows the field 'PERIL'.", 9, "image",
            "PERIL", placement="PL-120")
    dk.fact("screenshot", "CLARA screenshot shows map CLRM010 and transaction FN01.", 9, "image", "CLRM010",
            world_ref="BMS:CLRM010#transaction")
    dk.notes(s, "The CLARA FNOL map is CLRM010 under transaction FN01, driven by program CLRFN010. Handlers who joined "
                "after 2025 may never have seen it.")
    dk.fact("speaker_notes", "Speaker notes: CLRM010 is driven by program CLRFN010.", 9, "notes",
            "driven by program CLRFN010", world_ref="BMS:CLRM010#program")
    # 10 terminology
    s = dk.new_slide("What is called what")
    rows = [["In CLARA or older material", "In Claims Hub", "Notes"],
            ["PERIL", "Claim Type", "'loss type' on dashboards"],
            ["Case handler / HANDLER", "Claim handler", "Your user ID is on every movement"],
            ["FRAUDNET score", "Sentinel score", "Renamed 1 March 2025"],
            ["DOCSTOR", "Evidence Vault", "Renamed 3 November 2025"],
            ["Adjuster Extranet", "Assessor Portal", "Renamed 1 September 2025"],
            ["Reserve table", "Reserves panel", "Same reserve types"]]
    dk.table(s, rows, col_w=[3.8, 3.4, 4.8], size=14, row_h=0.55, name="Terminology")
    dk.fact("alias_use", "DOCSTOR was renamed Evidence Vault on 3 November 2025.", 10, "table",
            "DOCSTOR Evidence Vault Renamed 3 November 2025", world_ref="SYSTEM:SYS05#renames")
    dk.fact("alias_use", "Adjuster Extranet was renamed Assessor Portal on 1 September 2025.", 10, "table",
            "Adjuster Extranet Assessor Portal Renamed 1 September 2025", world_ref="SYSTEM:SYS17#renames")
    # 11 fraud
    s = dk.new_slide("Fraud referrals")
    dk.picture(s, _scr_fraud(), CONTENT_LEFT, CONTENT_TOP, w=8.0,
               alt="Claim header showing an SIU referral banner.", name="scr-fraud")
    dk.text(s, 8.8, CONTENT_TOP + 0.1, 4.0, 5.0,
            [f"SIU referral at a Sentinel score of {rv['BR-FRD-031']['parameters']['threshold']} or more "
             "(BR-FRD-031)",
             "Customer notice within 10 business days of referral (BR-FRD-032)",
             "Never decline on the score alone (BR-FRD-033)"], size=14, bullets=True, para_space=12)
    dk.fact("general", "In August 2026 the SIU referral threshold is a Sentinel score of 65 or more (BR-FRD-031 v1).",
            11, "text", "SIU referral at a Sentinel score of 65 or more", world_ref="RULE:BR-FRD-031@v1#parameters.threshold")
    dk.fact("screenshot", "Fraud banner screenshot: customer notice due within 10 business days.", 11, "image",
            "within 10 business days", world_ref="RULE:BR-FRD-032@v2")
    # 12 payments
    s = dk.new_slide("Payments and authority")
    rows = [["Role", "Payment authority (BR-STL-002 v3)", "Reserve authority (BR-RSV-003 v3)"],
            ["Claim handler", f"£{stl['claims_handler']:,}", f"£{rsv['claims_handler']:,}"],
            ["Team Leader", f"£{stl['team_leader']:,}", f"£{rsv['team_leader']:,}"],
            ["Claims Manager", f"£{stl['claims_manager']:,}", f"£{rsv['claims_manager']:,}"]]
    dk.table(s, rows, col_w=[3.0, 4.5, 4.5], size=15, row_h=0.6, name="Authority")
    dk.text(s, CONTENT_LEFT, 4.3, CONTENT_W, 2.0,
            [rv["BR-STL-007"]["text"].rstrip(".") + " (BR-STL-007)",
             rv["BR-STL-001"]["text"].rstrip(".") + " (BR-STL-001)"], size=14, bullets=True, para_space=10)
    dk.fact("general", "Claim handler payment authority is £15,000 (BR-STL-002 v3).", 12, "table",
            "Claim handler £15,000 £25,000", world_ref="RULE:BR-STL-002@v3#parameters.claims_handler")
    # 13 handler journey swimlane
    s = dk.new_slide("A claim's journey – who does what")
    lanes = ["Claim handler", "Team Leader", "Claims Hub", "SIU"]
    steps = [("a", "Take FNOL call", 0, 0), ("b", "Sentinel pre-screen", 2, 1), ("c", "Tier classification", 2, 2),
             ("d", "Set initial reserve", 0, 3), ("e", "Approve above authority", 1, 4), ("f", "Investigate referral", 3, 4),
             ("g", "Settle and pay", 0, 5)]
    _swimlane(dk, s, lanes, steps, flow=[("a", "b", None), ("b", "c", None), ("c", "d", None), ("d", "e", "over limit"),
                                         ("e", "g", None)])
    dk.fact("lane_only", "In the journey swimlane, 'Approve above authority' sits in the Team Leader lane.", 13, "text",
            "Approve above authority", world_ref="PROCESS:PS-RSV-02",
            notes="Owner given only by the lane the box sits in (Team Leader).")
    dk.fact("lane_only", "In the journey swimlane, 'Sentinel pre-screen' is done by Claims Hub (system lane).", 13,
            "text", "Sentinel pre-screen", world_ref="PROCESS:PS-TRI-01",
            notes="Owner given only by the lane the box sits in (Claims Hub).")
    # 14 service levels
    s = dk.new_slide("Service levels to remember")
    png = R.table_image([["What", "Standard"],
                         ["Acknowledge digital FNOL", "1 business day"],
                         ["Acknowledge telephone, broker, post", "2 business days"],
                         ["Initial reserve after FNOL", "2 business days"],
                         ["Tier-3 reserve review", "every 14 days"],
                         ["Customer notice after SIU referral", "10 business days"]], [620, 420],
                        title="Key service levels", size=28, row_h=60)
    dk.picture(s, png, CONTENT_LEFT + 2.0, CONTENT_TOP, h=5.2, alt="Table of key service levels for claim handlers.",
               name="sla-image")
    dk.fact("image_table", "Service levels image: acknowledge digital FNOL within 1 business day (BR-FNOL-001 v3).",
            14, "image", "Acknowledge digital FNOL", world_ref="RULE:BR-FNOL-001@v3")
    # 15 go-live support
    s = dk.new_slide("Wave 1 go-live and support")
    dk.bullets(s, [f"Wave 1 (UK motor) cut-over: {fmt_date(W.waves['MW-1']['date'])}"] +
               PH.pick(dk.rng, PH.SUPPORT, 3), size=16)
    dk.fact("general", "Wave 1 (UK motor) cut-over is on 14 September 2026.", 15, "text",
            "Wave 1 (UK motor) cut-over: 14 September 2026", world_ref="WAVE:MW-1#date")
    # 16 knowledge check
    s = dk.new_slide("Knowledge check")
    qs = ["1. Which field replaced the CLARA PERIL code?", "2. What is your reserve authority as a claim handler?",
          "3. Within how many business days must the customer be told about an SIU referral?",
          "4. Who approves a payment above your authority?", "5. Where do partners sign in?"]
    dk.text(s, CONTENT_LEFT, CONTENT_TOP + 0.1, CONTENT_W, 4.5, qs, size=17, para_space=14)
    dk.notes(s, "Answers: 1 Claim Type; 2 £25,000; 3 ten business days; 4 your Team Leader or above; 5 the Assessor "
                "Portal.")
    # 17 help
    contacts_slide(dk, ["P017", "P022", "P039"], title="Where to get help")
    return dk


# =========================================================================================
# VS022 RACI and Authority Matrix June 2025 (2025-06-10)
# =========================================================================================
def build_vs022(W, out_dir):
    fid = "VS022"
    dk = Deck(W, fid, out_dir, short_title="RACI and Authority Matrix – June 2025")
    d = dk.date
    stl = W.rule_version("BR-STL-002", d)
    rsv = W.rule_version("BR-RSV-003", d)
    assert stl["version"] == 2 and rsv["version"] == 2
    guard(W, fid, [("RULE:BR-STL-002@v2", "parameters"), ("RULE:BR-RSV-003@v2", "parameters"),
                   ("PROCESS:S7", "owner_history"), ("RULE:BR-REC-011@v1", "parameters"),
                   ("RULE:BR-TRI-009@v1", "parameters"), ("RULE:BR-TRI-006@v2", "parameters")])
    sp, rp = stl["parameters"], rsv["parameters"]

    s = dk.title_slide("RACI and Authority Matrix – June 2025", "Claims process roles and financial authorities",
                       [f"Owner: {person(W, 'P011', d)}",
                        f"Claims Operations UK  |  {fmt_date(d)}  |  Classification: Internal"])
    appr = approvers(W, d, ["P005", "P002", "P010"], minus_days(d, 4))
    dk.doc_control_slide("CLM-GOV-RACI-2025-06", person(W, "P011", d), appr,
                         history(dk, ["P011", "P039", "P011"], spans=(35, 17, 6)),
                         "Claims leadership, Finance, Risk & Compliance, team leaders")
    # 3 authority matrix (PL-121)
    s = dk.new_slide("Financial authority matrix")
    rows = [["Role", "Payment authority (BR-STL-002 v2)", "Reserve authority (BR-RSV-003 v2)"],
            ["Claims Handler", f"£{sp['claims_handler']:,}", f"£{rp['claims_handler']:,}"],
            ["Team Leader", f"£{sp['team_leader']:,}", f"£{rp['team_leader']:,}"],
            ["Claims Manager", f"£{sp['claims_manager']:,}", f"£{rp['claims_manager']:,}"],
            ["Claims Director", f"£{sp['claims_director']:,}", f"£{rp['claims_director']:,}"],
            ["Above Claims Director", "—", "Reserving Committee"]]
    dk.table(s, rows, col_w=[3.2, 4.4, 4.4], size=16, row_h=0.62, name="Authority matrix")
    dk.text(s, CONTENT_LEFT, 5.4, CONTENT_W, 1.0,
            ["Limits apply per claim and per transaction; Nordic amounts are tested at the GBP equivalent."],
            size=13, color=GREY, italic=True)
    dk.fact("contradiction_old", "June 2025 RACI slide: Team Leader payment authority £50,000.", 3, "table",
            "Team Leader £50,000", placement="PL-121")
    dk.fact("general", "June 2025: Team Leader reserve authority £75,000 (BR-RSV-003 v2).", 3, "table",
            "Team Leader £50,000 £75,000", world_ref="RULE:BR-RSV-003@v2#parameters.team_leader")
    dk.fact("general", "June 2025: Claims Director payment authority £1,000,000 (BR-STL-002 v2).", 3, "table",
            "Claims Director £1,000,000 £1,500,000", world_ref="RULE:BR-STL-002@v2#parameters.claims_director")
    dk.notes(s, "These limits were approved by the Claims Director and are applied in CLARA by the authority "
                "subprograms. Any change needs Finance sign-off.")

    # 4-5 RACI tables
    def team(t):
        return W.team_name(t, d)

    mvp = W.timeline["programme"]["mvp"]

    def teams_at(lst, role):
        # Hub squads only took on operational RACI roles once Claims Hub was live (MVP).
        out = [t for t in lst if not (t == "T27" and d < mvp)]
        if not out and role == "R":
            out = ["T02"]
        return out

    def acc(st):
        a = st["raci"]["A"]
        stage = W.stages[st["stage"]]
        cur_owner = stage["owner"]
        if a == cur_owner:
            a = W.owner_of_process(st["stage"], d)
        return f"{W.name_of(a, d)}"

    stage_groups = [["S1", "S2", "S3", "S4"], ["S5", "S6", "S7"]]
    for part, sg in enumerate(stage_groups, 1):
        s = dk.new_slide(f"RACI by process step ({part}/2)")
        rows = [["Stage", "Step", "Responsible", "Accountable", "Consulted", "Informed"]]
        for sid in sg:
            for stid in W.stages[sid]["steps"]:
                st = W.steps[stid]
                r = st["raci"]
                rows.append([W.stages[sid]["name"], st["name"], ", ".join(team(t) for t in teams_at(r["R"], "R")),
                             acc(st), ", ".join(team(t) for t in teams_at(r["C"], "C")) or "—",
                             ", ".join(team(t) for t in teams_at(r["I"], "I")) or "—"])
        dk.table(s, rows, col_w=[1.6, 2.7, 2.4, 1.8, 1.9, 1.8], size=8.5, row_h=0.27, name=f"RACI {part}")
        if part == 2:
            dk.fact("general", "June 2025: Siobhan Quill is accountable for 'Open subrogation case and demand' "
                               "(acting owner of Recovery & Subrogation).", dk.n, "table",
                    "Open subrogation case and demand Recoveries Siobhan Quill", world_ref="PROCESS:S7#owner_history")
        else:
            dk.fact("general", "June 2025: Ewan Strachan is accountable for FNOL steps such as 'Receive notification'.",
                    dk.n, "table", "Receive notification Contact Centre Ewan Strachan",
                    world_ref="PROCESS:S1#owner_history")
    # 6 escalation path (connectors)
    s = dk.new_slide("Reserve escalation path", "Arrows show when a reserve must move up a level")
    roles = ["Claims Handler", "Team Leader", "Claims Manager", "Claims Director", "Reserving Committee"]
    bxs = []
    for i, r in enumerate(roles):
        bxs.append(dk.box(s, 0.55 + i * 2.55, 3.0, 1.95, 0.9, r, size=13, bold=True,
                          fill=NAVY if i == 4 else TEAL_LT, color=WHITE if i == 4 else NAVY,
                          line=None if i == 4 else TEAL, name=f"esc-{i + 1}"))
    lims = [rp["claims_handler"], rp["team_leader"], rp["claims_manager"], rp["claims_director"]]
    for i in range(4):
        lab = f"above £{lims[i]:,}"
        dk.connect(s, bxs[i], bxs[i + 1], 3, 1, label=lab, label_size=10, label_w=1.3, label_offset=(0, -0.55))
        dk.fact("arrow_only", f"Escalation connector {roles[i]} → {roles[i + 1]} labelled '{lab}' (BR-RSV-003 v2).", 6,
                "connector", f"{roles[i]} -> {roles[i + 1]} [label: {lab}]",
                world_ref=f"RULE:BR-RSV-003@v2#parameters")
    dk.text(s, CONTENT_LEFT, 4.6, CONTENT_W, 1.5,
            ["Payment escalation follows the same ladder with the payment limits on slide 3.",
             "Escalations are recorded on the claim with the approver's user ID."], size=14, color=GREY, bullets=True)
    # 7-9 swimlanes
    lane_specs = [("S1", "FNOL and triage – who does what", ["S1", "S2"]),
                  ("S3", "Assessment and reserving – who does what", ["S3", "S4"]),
                  ("S5", "Fraud referral and settlement – who does what", ["S5", "S6"])]
    for key, title, stg in lane_specs:
        s = dk.new_slide(title, "Owner shown by lane")
        stids = [x for sgi in stg for x in W.stages[sgi]["steps"]][:7]
        lane_teams = []
        resp = {stid: teams_at(W.steps[stid]["raci"]["R"], "R")[0] for stid in stids}
        for stid in stids:
            if resp[stid] not in lane_teams:
                lane_teams.append(resp[stid])
        lanes = [team(t) for t in lane_teams]
        steps = [(stid, W.steps[stid]["name"], lane_teams.index(resp[stid]), k) for k, stid in enumerate(stids)]
        flow = [(stids[k], stids[k + 1], None) for k in range(len(stids) - 1)]
        _swimlane(dk, s, lanes, steps, box_w=1.45, flow=flow, size=9)
        for stid in stids[:3]:
            st = W.steps[stid]
            dk.fact("lane_only", f"June 2025 swimlane: '{st['name']}' sits in the {team(resp[stid])} lane.",
                    dk.n, "text", st["name"], world_ref=f"PROCESS:{stid}#raci",
                    notes="Responsible team given only by lane position.")
    # 10 other authorities (table image)
    s = dk.new_slide("Other authorities and approvals")
    rows = [["Authority", "Limit or rule", "Approver"],
            ["Recovery write-off", "above £5,000", "Recoveries Manager (BR-REC-011)"],
            ["Emergency make-safe at FNOL", "up to £500", "Contact centre (BR-FNOL-019)"],
            ["Manual tier override", "within 14 hours", "Team Leader (BR-TRI-009)"],
            ["Reserve increase over 50%", "one movement", "Team Leader review (BR-RSV-013)"],
            ["Fast-track straight-through cap", "£1,500", "No handler approval (BR-TRI-006)"]]
    for chk, rid in [("£5,000", "BR-REC-011"), ("£500", "BR-FNOL-019"), ("14 hours", "BR-TRI-009"),
                     ("50%", "BR-RSV-013"), ("£1,500", "BR-TRI-006")]:
        assert chk in W.rule_version(rid, d)["text"], (rid, chk)
    png = R.table_image(rows, [520, 330, 560], title="Other authorities (June 2025)", size=26, row_h=56)
    dk.picture(s, png, CONTENT_LEFT + 0.6, CONTENT_TOP, w=11.0, alt="Table of other approval authorities.",
               name="other-authorities")
    dk.fact("image_table", "June 2025: manual tier override needs Team Leader approval within 14 hours (BR-TRI-009 v1).",
            10, "image", "within 14 hours", world_ref="RULE:BR-TRI-009@v1")
    dk.fact("image_table", "June 2025: recovery write-offs above £5,000 need the Recoveries Manager (BR-REC-011 v1).",
            10, "image", "Recovery write-off", world_ref="RULE:BR-REC-011@v1")
    # 11 stage owners (tiles with rotated labels)
    s = dk.new_slide("Process stage owners – June 2025")
    for i, sid in enumerate(["S1", "S2", "S3", "S4", "S5", "S6", "S7"]):
        g = dk.group(s, f"grp-owner-{sid}")
        x = CONTENT_LEFT + i * 1.75
        dk.box(s, x, CONTENT_TOP + 0.2, 1.6, 3.2, W.stages[sid]["name"], shape=MSO_SHAPE.RECTANGLE, fill=NAVY,
               line=None, color=WHITE, size=13, bold=True, group=g, name=f"owner-stage-{sid}")
        o = W.owner_of_process(sid, d)
        dk.box(s, x, CONTENT_TOP + 3.5, 1.6, 1.4, [W.name_of(o, d), W.title_of(o, d)], fill=TEAL_LT, line=None,
               size=11, bold=True, group=g, name=f"owner-name-{sid}")
    dk.fact("visual_only", "June 2025: Recovery & Subrogation stage owner is Siobhan Quill (Acting Recoveries Manager).",
            11, "group", "Siobhan Quill Acting Recoveries Manager", world_ref="PROCESS:S7#owner_history",
            shape_name="grp-owner-S7")
    dk.fact("visual_only", "June 2025: Reserving stage owner is Sebastian Moreau-Clarke (Chief Actuary).", 11, "group",
            "Sebastian Moreau-Clarke Chief Actuary", world_ref="PROCESS:S4#owner_history", shape_name="grp-owner-S4")
    # 12 governance
    s = dk.new_slide("Governance of this matrix")
    dk.bullets(s, PH.pick(dk.rng, PH.GOVERNANCE, 4) + ["Team names reflect the organisation in June 2025"], size=16)
    return dk


# =========================================================================================
# VS023 Nordic Claims Operations Overview (2026-04-27)
# =========================================================================================
def build_vs023(W, out_dir):
    fid = "VS023"
    dk = Deck(W, fid, out_dir, short_title="Nordic Claims Operations Overview")
    d = dk.date
    C = W.company
    for pid in ["PRD-HOM-SE", "PRD-MOT-NO", "PRD-HOM-DK", "PRD-HOM-NO"]:
        pass
    assert not W.may_state(fid, "PRODUCT:PRD-HOM-SE", "wordings.HOM-SE-2016.excess")
    guard(W, fid, [("ORG:company", "staff_by_country"), ("PROFILE:seasonality", "CT-FRO"),
                   ("RULE:BR-TRI-003@v3", "parameters"), ("SYSTEM:SYS23", "retired_on"), ("WAVE:MW-0", "date"),
                   ("CLAIMTYPE:CT-FRO", "local_names"), ("PROFILE:fx_to_gbp_quarter_end", None)])
    tri = W.rule_version("BR-TRI-003", d)["parameters"]

    s = dk.title_slide("Nordic Claims Operations Overview", "Norway, Sweden and Denmark",
                       [f"Presented by {person(W, 'P012', d)}",
                        f"Claims Operations Nordics  |  {fmt_date(d)}  |  Classification: Internal"])
    dk.agenda_slide(["Footprint and people", "Claim types and products", "Organisation", "Nordic rules",
                     "Migration path", "Partners and currency", "Priorities"])
    # 3 footprint
    s = dk.new_slide("Footprint")
    sb = C["staff_by_country"]
    dk.chart(s, "column", ["Norway", "Sweden", "Denmark"], {"Staff": [sb["NO"], sb["SE"], sb["DK"]]},
             CONTENT_LEFT, CONTENT_TOP, 5.6, 5.0, title="Staff by country", number_format="0", legend=False,
             name="staff-chart")
    rows = [["Branch", "Office", "Currency"]]
    for b in C["branches"]:
        loc = W.locations[b["location"]]
        rows.append([b["name"], f"{loc['city']} – {loc['address']}", b["currency"]])
    dk.table(s, rows, x=6.5, y=CONTENT_TOP + 0.3, w=6.3, col_w=[2.3, 3.2, 0.8], size=12, row_h=0.6, name="Branches")
    dk.fact("chart_only", "Chart: Corvane has 470 staff in Norway.", 3, "chart", "Staff: Norway=470",
            world_ref="ORG:company#staff_by_country.NO")
    dk.fact("chart_only", "Chart: Corvane has 300 staff in Denmark.", 3, "chart", "Staff: Denmark=300",
            world_ref="ORG:company#staff_by_country.DK")
    dk.fact("general", "Corvane Mutual Sverige is based at Kvarnbacken 12, Stockholm.", 3, "table",
            "Corvane Mutual Sverige Stockholm – Kvarnbacken 12", world_ref="LOC:LOC-STO#address")
    # 4 claim types (+ notes PL-122)
    s = dk.new_slide("Claim types and local names")
    rows = [["Claim Type", "Norwegian", "Swedish", "Danish"]]
    for ct in ["CT-EOW", "CT-STM", "CT-FRO", "CT-SNO", "CT-COL", "CT-WSC", "CT-THF", "CT-BIJ"]:
        c = W.claim_types[ct]
        ln = c["local_names"]
        rows.append([c["name"], ln["NO"], ln["SE"], ln["DK"]])
    dk.table(s, rows, col_w=[3.0, 3.0, 3.0, 3.0], size=14, row_h=0.5, name="Claim types")
    dk.text(s, CONTENT_LEFT, 6.0, CONTENT_W, 0.5, "Frost Damage and Snow Load exist only on Nordic home products.",
            size=13, color=GREY, italic=True)
    dk.notes(s, "Seasonality: Nordic frost-damage claims peak in January and February, so we staff the home desks "
                "accordingly. Snow load follows a little later, peaking from January to March.")
    dk.fact("speaker_notes", "Speaker notes: Nordic frost-damage claims peak in January and February.", 4, "notes",
            "Nordic frost-damage claims peak in January and February", placement="PL-122")
    dk.fact("speaker_notes", "Speaker notes: snow load claims peak from January to March.", 4, "notes",
            "peaking from January to March", world_ref="PROFILE:seasonality#CT-SNO")
    dk.fact("general", "Frost Damage is 'Frostskada' in Swedish.", 4, "table", "Frost Damage Frostskade Frostskada",
            world_ref="CLAIMTYPE:CT-FRO#local_names")
    # 5 products
    s = dk.new_slide("Products in scope")
    rows = [["Product", "Code", "Line", "Country", "Claim types"]]
    for pid in ["PRD-MOT-NO", "PRD-MOT-SE", "PRD-MOT-DK", "PRD-HOM-NO", "PRD-HOM-SE", "PRD-HOM-DK"]:
        p = W.products[pid]
        rows.append([p["name"], p["code"], p["line"], p["region"], str(len(p["claim_types"]))])
    dk.table(s, rows, col_w=[3.0, 1.5, 1.5, 1.2, 1.8], size=14, row_h=0.55, w=9.0, name="Products")
    dk.text(s, 9.9, CONTENT_TOP + 0.2, 2.9, 3.0, ["Excess and wording terms differ by product and wording "
                                                  "generation; see the product terms."], size=12, color=GREY)
    dk.fact("general", "Hjem Danmark has product code HOMDK.", 5, "table", "Hjem Danmark HOMDK",
            world_ref="PRODUCT:PRD-HOM-DK#code")
    # 6 organisation (connectors)
    s = dk.new_slide("Organisation", "Arrows point to the line manager")
    chain = ["P046", "P034", "P012", "P011"]
    bxs = {}
    for i, pid in enumerate(chain):
        bxs[pid] = dk.box(s, 0.7 + i * 3.1, 2.0, 2.6, 1.0, W.name_of(pid, d), size=14, bold=True, name=f"org-{pid}")
        dk.text(s, 0.7 + i * 3.1, 3.05, 2.6, 0.6, W.title_of(pid, d), size=11, color=GREY, align=PP_ALIGN.CENTER,
                name=f"org-title-{pid}")
    for a, b in zip(chain[:-1], chain[1:]):
        assert W.manager_of(a, d) == b, (a, b)
        dk.connect(s, bxs[a], bxs[b], 3, 1, label="reports to", label_size=10, label_offset=(0, -0.35))
        dk.fact("arrow_only", f"Org connector: {W.name_of(a, d)} reports to {W.name_of(b, d)} (April 2026).", 6,
                "connector", f"{W.name_of(a, d)} -> {W.name_of(b, d)} [label: reports to]",
                world_ref=f"PERSON:{a}#reports_to")
    others = ["P013", "P027", "P020", "P038", "P031", "P036", "P040"]
    g = dk.group(s, "grp-nordic-group-roles")
    dk.box(s, CONTENT_LEFT, 4.15, CONTENT_W, 0.45, "Group roles based in the Nordic offices", shape=MSO_SHAPE.RECTANGLE,
           fill=NAVY, line=None, color=WHITE, size=13, bold=True, group=g, name="nordic-roles-hdr")
    for i, pid in enumerate(others):
        loc = W.locations[W.location_of(pid, d)]["city"]
        dk.box(s, CONTENT_LEFT + i * 1.75, 4.7, 1.65, 1.6, [W.name_of(pid, d), W.title_of(pid, d), loc],
               fill=TEAL_LT, line=None, size=10, bold=True, group=g, name=f"nordic-role-{pid}")
    dk.fact("visual_only", "Freya Lindahl (Head of Recoveries & Subrogation) is based in Stockholm.", 6, "group",
            "Freya Lindahl Head of Recoveries & Subrogation Stockholm", world_ref="PERSON:P013#location",
            shape_name="grp-nordic-group-roles")
    # 7 nordic rules
    s = dk.new_slide("Rules that are different in the Nordics")
    rr = {r: W.rule_version(r, d)["text"].rstrip(".") for r in ["BR-TRI-005", "BR-TRI-015", "BR-ASM-009",
                                                                "BR-FNOL-013", "BR-REC-008", "BR-STL-003"]}
    items = [f"Tier-3 at NOK {tri['tier3_min_nok']:,} / SEK {tri['tier3_min_sek']:,} / DKK {tri['tier3_min_dkk']:,} "
             "(BR-TRI-003 v3)", rr["BR-TRI-015"] + " (BR-TRI-015)", rr["BR-TRI-005"] + " (BR-TRI-005)",
             rr["BR-ASM-009"] + " (BR-ASM-009)", rr["BR-FNOL-013"] + " (BR-FNOL-013)", rr["BR-REC-008"] + " (BR-REC-008)",
             rr["BR-STL-003"] + " (BR-STL-003)"]
    dk.bullets(s, items, size=14)
    dk.fact("general", "Nordic Tier-3 thresholds: NOK 650,000 / SEK 680,000 / DKK 430,000 (BR-TRI-003 v3).", 7, "text",
            "Tier-3 at NOK 650,000 / SEK 680,000 / DKK 430,000", world_ref="RULE:BR-TRI-003@v3#parameters.tier3_min_nok")
    dk.fact("general", "Nordic home claims above NOK 120000 require an on-site takst (BR-ASM-009).", 7, "text",
            "Nordic home claims above NOK 120000 require an on-site takst", world_ref="RULE:BR-ASM-009@v1")
    # 8 seasonal calendar raster
    s = dk.new_slide("Seasonal peaks")
    cv = R.Canvas(1600, 640)
    cv.title("Peak months by claim type (Nordic home)")
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    peaks = {"Storm": {1, 2, 11, 12}, "Escape of Water": {1, 2, 12}, "Snow Load": {1, 2, 3}}
    x0, y0, cw, rh = 330, 140, 100, 110
    for i, m in enumerate(months):
        cv.text((x0 + i * cw + cw / 2, y0), m, size=24, bold=True, fill=R.NAVY, anchor="ma")
    for r, (ct, ms) in enumerate(peaks.items()):
        y = y0 + 60 + r * rh
        cv.text((40, y + 30), ct, size=26, bold=True, fill=R.BLACK)
        for i in range(12):
            fill = R.TEAL if (i + 1) in ms else R.GREY_LT
            cv.d.rectangle([x0 + i * cw + 4, y, x0 + (i + 1) * cw - 4, y + rh - 20], fill=fill)
    dk.picture(s, cv.png(), CONTENT_LEFT, CONTENT_TOP, w=CONTENT_W,
               alt="Calendar of peak months for storm, escape of water and snow load claims.", name="season-image")
    dk.fact("image_text", "Seasonal image shows peak months for Snow Load (Nordic home).", 8, "image", "Snow Load",
            world_ref="PROFILE:seasonality#CT-SNO")
    dk.notes(s, "Storm peaks November to February; escape of water December to February.")
    dk.fact("speaker_notes", "Speaker notes: storm peaks November to February; escape of water December to February.",
            8, "notes", "Storm peaks November to February", world_ref="PROFILE:seasonality#CT-STM")
    # 9 migration path (connectors)
    s = dk.new_slide("Migration path for Nordic claims")
    b1 = dk.box(s, 0.6, 2.6, 2.6, 1.0, "SKADE-90", fill=GREY_LT, line=GREY, size=15, bold=True, name="mig-skade")
    b2 = dk.box(s, 4.0, 2.6, 2.6, 1.0, "CLARA", fill=GREY_LT, line=GREY, size=15, bold=True, name="mig-clara")
    b3 = dk.box(s, 7.4, 1.7, 2.8, 1.0, "Claims Hub – Denmark", size=14, bold=True, name="mig-hub-dk")
    b4 = dk.box(s, 7.4, 3.6, 2.8, 1.0, "Claims Hub – Norway and Sweden", size=13, bold=True, name="mig-hub-nose")
    dk.connect(s, b1, b2, 3, 1, label="migrated; retired 31 May 2024", label_w=2.3, label_size=10,
               label_offset=(0, -0.55))
    dk.connect(s, b2, b3, 3, 1, label=f"Wave 0, {fmt_date(W.waves['MW-0']['date'], 'short')}", label_w=1.8,
               label_size=10, label_offset=(-0.1, -0.45))
    dk.connect(s, b2, b4, 3, 1, label="Wave 2 (2027)", label_w=1.4, label_size=10, label_offset=(0, 0.1))
    dk.fact("arrow_only", "SKADE-90 claims were migrated to CLARA; SKADE-90 retired 31 May 2024.", 9, "connector",
            "SKADE-90 -> CLARA [label: migrated; retired 31 May 2024]", world_ref="SYSTEM:SYS23#retired_on")
    dk.fact("arrow_only", "Wave 0 moves Danish claims from CLARA to Claims Hub on 1 Jun 2026.", 9, "connector",
            "CLARA -> Claims Hub – Denmark [label: Wave 0, 1 Jun 2026]", world_ref="WAVE:MW-0#date")
    dk.text(s, CONTENT_LEFT, 5.0, CONTENT_W, 1.4,
            [f"Wave 0 scope: {W.waves['MW-0']['scope']}", "Norway and Sweden follow with the rest of the portfolio"],
            size=14, bullets=True)
    # 10 partners (group)
    s = dk.new_slide("Nordic partners")
    for i, vid in enumerate(["VEN-02", "VEN-05", "VEN-14", "VEN-09"]):
        v = W.vendors[vid]
        g = dk.group(s, f"grp-partner-{vid}")
        x = CONTENT_LEFT + i * 3.07
        dk.box(s, x, CONTENT_TOP + 0.3, 2.95, 0.7, v["short"], shape=MSO_SHAPE.RECTANGLE, fill=NAVY, line=None,
               color=WHITE, size=15, bold=True, group=g, name=f"partner-hdr-{vid}")
        dk.box(s, x, CONTENT_TOP + 1.0, 2.95, 2.4, [v["role"], f"{v['location']}"], shape=MSO_SHAPE.RECTANGLE,
               fill=TEAL_LT, line=None, size=13, group=g, name=f"partner-body-{vid}")
    dk.text(s, CONTENT_LEFT, 5.2, CONTENT_W, 1.0, [W.rule_version("BR-TRI-011", d)["text"].rstrip(".") +
                                                   " (BR-TRI-011)"], size=14, bullets=True)
    dk.fact("visual_only", "Lyngholm Glass is the Danish windscreen network (Aarhus).", 10, "group",
            "Danish windscreen network", world_ref="VENDOR:VEN-14#role", shape_name="grp-partner-VEN-14")
    # 11 currency (table image)
    s = dk.new_slide("Currency")
    fx = W.claims_profile["fx_to_gbp_quarter_end"]
    qs = [q for q in sorted(fx) if q <= d][-3:]
    rows = [["Quarter end", "NOK to GBP", "SEK to GBP", "DKK to GBP"]] + \
           [[q, f"{fx[q]['NOK']:.4f}", f"{fx[q]['SEK']:.4f}", f"{fx[q]['DKK']:.4f}"] for q in qs]
    png = R.table_image(rows, [300, 300, 300, 300], title="Quarter-end rates used for GBP equivalents", size=26,
                        row_h=56)
    dk.picture(s, png, CONTENT_LEFT + 1.2, CONTENT_TOP, w=9.5, alt="Table of quarter-end exchange rates.",
               name="fx-image")
    dk.fact("image_table", f"FX table image: NOK to GBP at {qs[-1]} was {fx[qs[-1]]['NOK']:.4f}.", 11, "image",
            f"{fx[qs[-1]]['NOK']:.4f}", world_ref="PROFILE:fx_to_gbp_quarter_end")
    dk.text(s, CONTENT_LEFT, 5.6, CONTENT_W, 0.8, [W.rule_version("BR-RSV-012", d)["text"].split(";")[0] + "."],
            size=13, color=GREY)
    # 12 priorities
    next_steps_slide(dk, title="Priorities for 2026", extra=["Land Wave 0 for Denmark with stable hypercare",
                                                             "Prepare Norwegian and Swedish teams for Wave 2"], k=3)
    # 13 contacts
    contacts_slide(dk, ["P012", "P034", "P046", "P013"])
    # 14 doc control
    appr = approvers(W, d, ["P011", "P005"], minus_days(d, 2))
    dk.doc_control_slide("CLM-NOR-OVW-2026", person(W, "P012", d), appr,
                         history(dk, ["P012", "P034", "P012"], spans=(21, 9, 3)),
                         "Claims Operations (Group), Nordic team leaders, Programme Skerry")
    return dk


# =========================================================================================
# VS024 Recovery KPIs 2025 (2026-02-09)
# =========================================================================================
def build_vs024(W, out_dir):
    fid = "VS024"
    dk = Deck(W, fid, out_dir, short_title="Recovery KPIs 2025")
    d = dk.date
    M = W.timeline["metrics"]
    guard(W, fid, [("TIMELINE:metrics", "recovery_rate_pct"), ("RULE:BR-REC-003@v3", "parameters"),
                   ("RULE:BR-REC-003@v2", "parameters"), ("RULE:BR-REC-005@v2", "parameters"),
                   ("RULE:BR-REC-011@v2", "parameters"), ("VENDOR:VEN-07", "fees"), ("VENDOR:VEN-09", "fees"),
                   ("SYSTEM:SYS24", "decommission_target"), ("DECISION:DEC-004", None), ("PROCESS:S7", "owner_history")])
    rr = M["recovery_rate_pct"]

    s = dk.title_slide("Recovery KPIs 2025", "Recoveries & Subrogation – annual performance review",
                       [f"Presented by {person(W, 'P013', d)}",
                        f"Recoveries & Subrogation (Group)  |  {fmt_date(d)}  |  Classification: Internal"])
    # 2 recovery rate chart (PL-123, chart only)
    s = dk.new_slide("Recovery rate by portfolio")
    dk.chart(s, "bar", ["UK motor", "UK home", "Nordic motor"],
             {"Recovery rate 2025 (%)": [rr["UK motor 2025"], rr["UK home 2025"], rr["Nordic motor 2025"]]},
             CONTENT_LEFT + 0.2, CONTENT_TOP, 8.0, 5.3, title="Recovery rate 2025 (%)", number_format="0.0",
             legend=False, name="recovery-rate-chart")
    dk.text(s, 8.9, CONTENT_TOP + 0.3, 3.9, 4.5,
            ["Recovery rate = receipts over recoverable outlay (BR-REC-014)",
             "Motor recoveries benefit from clear third-party liability",
             "Home recoveries depend on neighbour and contractor liability"], size=14, bullets=True, para_space=12)
    dk.fact("chart_only", "Recovery rate 2025: UK motor 41.2%, UK home 18.7%, Nordic motor 36.5% (chart only).", 2,
            "chart", "Recovery rate 2025 (%): UK motor=41.2", placement="PL-123")
    dk.fact("chart_only", "Chart: UK home recovery rate 2025 was 18.7%.", 2, "chart",
            "Recovery rate 2025 (%): UK home=18.7", world_ref="TIMELINE:metrics#recovery_rate_pct", exclusive=True,
            notes="Same exclusive placement PL-123 (second series point).")
    dk.fact("chart_only", "Chart: Nordic motor recovery rate 2025 was 36.5%.", 2, "chart",
            "Recovery rate 2025 (%): Nordic motor=36.5", world_ref="TIMELINE:metrics#recovery_rate_pct", exclusive=True,
            notes="Same exclusive placement PL-123 (third series point).")
    dk.fact("general", "Recovery rate is defined as receipts over recoverable outlay (BR-REC-014).", 2, "text",
            "receipts over recoverable outlay (BR-REC-014)", world_ref="RULE:BR-REC-014@v1")
    dk.notes(s, "Talk to the motor result first. The home figure is structurally lower because liability is harder "
                "to establish.")
    # 3 document control
    appr = approvers(W, d, ["P005", "P021"], minus_days(d, 2))
    dk.doc_control_slide("REC-KPI-2025", person(W, "P013", d), appr,
                         history(dk, ["P013", "P014", "P013"], spans=(20, 10, 3)),
                         "Claims leadership, Financial Control, Recoveries team leaders")
    # 4 KPI definitions
    s = dk.new_slide("How we measure")
    rows = [["KPI", "Definition / standard", "Rule"]]
    for rid in ["BR-REC-014", "BR-REC-012", "BR-REC-004", "BR-REC-007", "BR-REC-015", "BR-REC-009"]:
        v = W.rule_version(rid, d)
        rows.append([W.rules[rid]["title"], v["text"].rstrip("."), f"{rid} v{v['version']}"])
    dk.table(s, rows, col_w=[2.8, 7.6, 1.6], size=12, row_h=0.62, name="KPI definitions")
    dk.fact("general", "Unanswered subrogation demands are chased at 28 days (BR-REC-012).", 4, "table",
            "Unanswered subrogation demands are chased at 28 days", world_ref="RULE:BR-REC-012@v1")
    dk.fact("general", "Salvage proceeds are posted within 3 business days of receipt (BR-REC-015 v2).", 4, "table",
            "Salvage proceeds are posted within 3 business days of receipt", world_ref="RULE:BR-REC-015@v2")
    # 5 decision flow (connectors)
    s = dk.new_slide("Pursue or not? The decision", "Thresholds in force since 1 September 2025")
    r3 = W.rule_version("BR-REC-003", d)["parameters"] if W.rule_version("BR-REC-003", d).get("parameters") else {}
    start = dk.box(s, 0.5, 3.0, 2.0, 0.9, "Recovery potential flagged", size=12, bold=True, name="rf-start")
    d1 = dk.box(s, 3.2, 2.6, 2.8, 1.7, "Recoverable ≥ £1,000?", shape=MSO_SHAPE.DIAMOND, fill=SAND, line=AMBER,
                size=12, bold=True, name="rf-d1")
    d2 = dk.box(s, 6.9, 2.6, 2.9, 1.7, "≥ £25,000 or liability defended?", shape=MSO_SHAPE.DIAMOND, fill=SAND,
                line=AMBER, size=11, bold=True, name="rf-d2")
    sol = dk.box(s, 10.6, 1.4, 2.2, 0.9, "Solicitor referral", size=12, bold=True, name="rf-sol")
    dem = dk.box(s, 10.6, 4.6, 2.2, 0.9, "Open case and demand", size=12, bold=True, name="rf-demand")
    nop = dk.box(s, 3.5, 5.3, 2.2, 0.9, "Not pursued: close or write off", size=11, bold=True, fill=GREY_LT, line=GREY,
                 name="rf-no")
    dk.connect(s, start, d1, 3, 1)
    dk.connect(s, d1, d2, 3, 1, label="Yes", label_w=0.6, label_offset=(0, -0.35))
    dk.connect(s, d1, nop, 2, 0, label="No", label_w=0.6, label_offset=(0.35, -0.1))
    dk.connect(s, d2, sol, 0, 1, label="Yes", label_w=0.6, elbow=True, label_offset=(0.4, -0.2))
    dk.connect(s, d2, dem, 2, 1, label="No", label_w=0.6, elbow=True, label_offset=(0.4, 0.1))
    for a, b, lab, ref in [("Recoverable ≥ £1,000?", "≥ £25,000 or liability defended?", "Yes", "RULE:BR-REC-003@v3"),
                           ("Recoverable ≥ £1,000?", "Not pursued: close or write off", "No", "RULE:BR-REC-003@v3"),
                           ("≥ £25,000 or liability defended?", "Solicitor referral", "Yes", "RULE:BR-REC-005@v2"),
                           ("≥ £25,000 or liability defended?", "Open case and demand", "No", "RULE:BR-REC-005@v2")]:
        dk.fact("arrow_only", f"Decision connector '{a}' → '{b}' [{lab}].", 5, "connector", f"{a} -> {b} [label: {lab}]",
                world_ref=ref)
    dk.notes(s, "Solicitor referrals go to Quarryhill Solicitors. Thresholds rose on 1 September 2025: pursue from "
                "£750 to £1,000 and solicitor referral from £15,000 to £25,000.")
    # 6 swimlane
    s = dk.new_slide("Recovery process – who does what")
    lanes = ["Claims Assessment UK", "Recoveries & Subrogation (Group)", "Quarryhill Solicitors", "Salvanta Salvage",
             "Financial Control"]
    steps = [("a", "Flag recovery potential", 0, 0), ("b", "Open case and demand", 1, 1), ("c", "Chase at 28 days", 1, 2),
             ("d", "Litigate defended claims", 2, 3), ("e", "Collect total-loss vehicle", 3, 2),
             ("f", "Post receipt to GL", 4, 4)]
    _swimlane(dk, s, lanes, steps, flow=[("a", "b", None), ("b", "c", None), ("c", "d", "defended"), ("d", "f", None)],
              header_w=0.55)
    dk.fact("lane_only", "Recovery swimlane: 'Litigate defended claims' sits in the Quarryhill Solicitors lane.", 6,
            "text", "Litigate defended claims", world_ref="VENDOR:VEN-07#role",
            notes="Owner given only by lane position.")
    dk.fact("lane_only", "Recovery swimlane: 'Collect total-loss vehicle' sits in the Salvanta Salvage lane.", 6, "text",
            "Collect total-loss vehicle", world_ref="VENDOR:VEN-09#role", notes="Owner given only by lane position.")
    # 7 rule changes 2025
    s = dk.new_slide("Rule changes in 2025")
    rows = [["Rule", "Until 31 Aug 2025", "From 1 Sep 2025"]]
    for rid in ["BR-REC-003", "BR-REC-005", "BR-REC-011"]:
        old = W.rule_version(rid, "2025-08-31")
        new = W.rule_version(rid, "2025-09-01")
        rows.append([f"{rid} {W.rules[rid]['title']}", old["text"].rstrip("."), new["text"].rstrip(".")])
    dk.table(s, rows, col_w=[2.6, 4.7, 4.7], size=11, row_h=0.95, name="Rule changes")
    dk.fact("temporal", "Subrogation pursuit threshold: £750 until 31 Aug 2025, £1,000 from 1 Sep 2025 (BR-REC-003).",
            7, "table", "Pursue subrogation where the recoverable amount is £1,000 or more",
            world_ref="RULE:BR-REC-003@v3#parameters")
    dk.fact("temporal", "Write-offs above £10,000 need the Head of Recoveries & Subrogation from 1 Sep 2025 "
                        "(BR-REC-011 v2).", 7, "table", "above £10,000 require approval by the Head of Recoveries",
            world_ref="RULE:BR-REC-011@v2")
    # 8 partners fees (table image)
    s = dk.new_slide("Recovery partners")
    q, sv = W.vendors["VEN-07"], W.vendors["VEN-09"]
    png = R.table_image([["Partner", "Service", "Commercials"],
                         [q["name"], "Recovery litigation", f"£{q['fees']['fixed_fee_demand_gbp']} fixed fee per demand; "
                                                            f"{q['fees']['success_fee_pct']}% success fee"],
                         [sv["name"], "Vehicle salvage", f"£{sv['fees']['collection_gbp']} collection; "
                                                         f"{sv['sla']['collection_business_days']} business days"]],
                        [420, 360, 620], title="Partner commercials", size=26, row_h=60)
    dk.picture(s, png, CONTENT_LEFT + 0.4, CONTENT_TOP, w=11.4, alt="Table of recovery partner commercials.",
               name="partners-image")
    dk.fact("image_table", "Quarryhill: £95 fixed fee per demand; 12% success fee (image).", 8, "image",
            "12% success fee", world_ref="VENDOR:VEN-07#fees")
    dk.fact("image_table", "Salvanta: £60 collection fee (image).", 8, "image", "£60 collection",
            world_ref="VENDOR:VEN-09#fees")
    # 9 systems (connectors)
    s = dk.new_slide("Systems and interfaces")
    clara = dk.box(s, 0.6, 2.6, 2.6, 1.0, "CLARA", fill=GREY_LT, line=GREY, size=15, bold=True, name="sys-clara")
    sub = dk.box(s, 5.0, 1.6, 2.8, 1.0, "Subrogation Tracker", size=14, bold=True, name="sys-subtrak")
    gl = dk.box(s, 5.0, 4.2, 2.8, 1.0, "Group Ledger", size=14, bold=True, name="sys-gl")
    rec = dk.box(s, 9.8, 1.6, 2.8, 1.0, "recovery-svc", fill=NAVY, line=None, color=WHITE, size=14, bold=True,
                 name="sys-recovery-svc")
    for (a, an), (b, bn), sa, sb, iid in [((clara, "CLARA"), (sub, "Subrogation Tracker"), 0, 1, "CLX-IF-022"),
                                          ((sub, "Subrogation Tracker"), (clara, "CLARA"), 2, 3, "CLX-IF-023"),
                                          ((clara, "CLARA"), (gl, "Group Ledger"), 2, 1, "CLX-IF-029")]:
        lab = f"{iid} ({W.interface_schedule(iid, d)})"
        dk.connect(s, a, b, sa, sb, label=lab, label_size=9, label_w=2.0, elbow=True, label_offset=(0.3, -0.1))
        dk.fact("arrow_only", f"Connector {an} → {bn} labelled '{lab}'.", 9, "connector",
                f"{an} -> {bn} [label: {lab}]", world_ref=f"INTERFACE:{iid}#schedule")
    dk.connect(s, sub, rec, 3, 1, label="replaced by", label_size=10, label_offset=(0, -0.35), dashed=True)
    dk.fact("arrow_only", "Subrogation Tracker is replaced by recovery-svc.", 9, "connector",
            "Subrogation Tracker -> recovery-svc [label: replaced by]", world_ref="SYSTEM:SYS24#description")
    dk.text(s, 8.6, 3.5, 4.2, 2.0,
            [f"SUBTRAK retirement target: {fmt_date(W.systems['SYS24']['decommission_target'])}",
             f"recovery-svc owner: {W.team_name(W.service_owner('recovery-svc', d)['team'], d)}"],
            size=13, bullets=True)
    dk.fact("general", "The Subrogation Tracker (SUBTRAK) retirement target is 31 December 2026.", 9, "text",
            "SUBTRAK retirement target: 31 December 2026", world_ref="SYSTEM:SYS24#decommission_target")
    dk.fact("temporal", "In February 2026 recovery-svc is owned by Hub Squad – Fraud & Settlement.", 9, "text",
            "recovery-svc owner: Hub Squad – Fraud & Settlement", world_ref="SERVICE:recovery-svc#owner_history")
    # 10 organisation
    s = dk.new_slide("Organisation since 1 September 2025")
    items = [f"{W.name_of('P013', d)} owns the Recovery & Subrogation process as {W.title_of('P013', d)} "
             f"(reporting to the Claims Director, {W.name_of('P005', d)})",
             f"{W.name_of('P014', d)} leads the UK recoveries team in Bristol as {W.title_of('P014', d)}",
             "Recoveries & Subrogation became a Group function on 1 September 2025",
             "The subrogation handover meeting on 3 September 2025 confirmed ownership and the SUBTRAK target"]
    dk.bullets(s, items, size=16)
    dk.fact("general", "Freya Lindahl owns the Recovery & Subrogation process as Head of Recoveries & Subrogation.", 10,
            "text", "Freya Lindahl owns the Recovery & Subrogation process as Head of Recoveries & Subrogation",
            world_ref="PROCESS:S7#owner_history")
    dk.fact("general", "Siobhan Quill leads the UK recoveries team as Recoveries Team Leader – UK.", 10, "text",
            "Siobhan Quill leads the UK recoveries team in Bristol as Recoveries Team Leader – UK",
            world_ref="PERSON:P014#titles")
    # 11 Nordic regress
    s = dk.new_slide("Nordic regress")
    dk.bullets(s, [W.rule_version("BR-REC-008", d)["text"].rstrip(".") + " (BR-REC-008)",
                   W.rule_version("BR-REC-017", d)["text"].rstrip(".") + " (BR-REC-017)",
                   "Nordic thresholds are applied in local currency (NOK 13,000 / SEK 13,500 / DKK 8,600)"], size=16)
    dk.fact("general", "Nordic subrogation thresholds: NOK 13,000 / SEK 13,500 / DKK 8,600 (BR-REC-003 v3).", 11,
            "text", "NOK 13,000 / SEK 13,500 / DKK 8,600", world_ref="RULE:BR-REC-003@v3")
    # 12 priorities
    next_steps_slide(dk, title="Priorities for 2026", extra=["Complete migration of open cases off SUBTRAK",
                                                             "Embed the new pursuit and write-off thresholds"], k=3)
    # 13 risks
    risks_slide(dk, k=4)
    return dk

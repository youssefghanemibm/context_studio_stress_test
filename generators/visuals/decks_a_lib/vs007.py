"""VS007 Fraud Referral Process (from 1 October 2026) (2026-10-02, Niall Brannigan, approved).

The thresholds sit in the decision diamonds and the meaning ('Yes' -> Refer to SIU) only in the
connectors; no slide text states the referral rule in words. The SIU ownership of the human review
is shown only by lane position."""
from __future__ import annotations

from . import common as CM
from . import phrases as P
from . import raster as R
from .core import Deck
from .lanes import swimlane


def build(W, out_dir):
    D = Deck(W, "VS007", version="2.0", doc_ref="CFS-PRC-005", out_dir=out_dir)
    d = D.date
    rng = D.rng
    t11 = W.team_name("T11", d)

    # 1 title
    D.title_slide(D.title, "Referral decision, SIU hand-off, customer notice and outcome",
                  [f"Counter-Fraud & SIU  |  Version {D.version}  |  {D.date_long()}",
                   f"Process owner: {D.author}, {D.author_title}", "Status: Approved"])

    # 2 referral decision flow
    s = D.content("Referral decision", "Fraud referral · decision flow")
    start = s.box(0.5, 3.2, 2.0, 0.8, "Claim scored by Sentinel", style="terminal", size=12, bold=True)
    d65 = s.box(3.0, 2.9, 2.5, 1.4, "Sentinel score ≥ 65?", style="decision", size=13, bold=True)
    d60 = s.box(6.4, 4.2, 2.7, 1.5, "Tier-3 and score ≥ 60?", style="decision", size=13, bold=True)
    ref = s.box(9.9, 1.5, 2.6, 0.85, "Refer to SIU", style="alert", size=14, bold=True)
    cont = s.box(9.9, 5.6, 2.6, 0.85, "Continue normal handling", style="process", size=12)
    s.connect(start, d65, a_site="r", b_site="l")
    s.connect(d65, ref, a_site="t", b_site="l", label="Yes", name="frd-yes-65", label_size=11)
    s.connect(d65, d60, a_site="b", b_site="l", label="No", name="frd-no-65", label_size=11)
    s.connect(d60, ref, a_site="t", b_site="b", label="Yes", name="frd-yes-60", label_size=11)
    s.connect(d60, cont, a_site="b", b_site="l", label="No", name="frd-no-60", label_size=11)
    s.text(0.5, 5.3, 4.8, 1.4, [{"text": "Notation", "bold": True, "size": 10},
                                {"text": "Diamond – decision on the claim's Sentinel score and tier", "size": 9},
                                {"text": "Arrow labels – answer to the decision", "size": 9},
                                {"text": "Applies to every claim scored on or after 1 October 2026", "size": 9}],
           size=9, color="slate", fill="grey_l", margins=0.1)
    D.need("RULE:BR-TRI-003@v3", "text")
    s.notes(P.notes(rng, "the referral decision that applies from 1 October 2026",
                    ["Tier-3 is defined by BR-TRI-003 v3: estimated incurred of £50,000 or more (NOK 650,000 / SEK 680,000 / DKK 430,000), any bodily injury, solicitor or litigation involvement at notification, or a property total loss.",
                     "The decision is recorded the same business day as scoring."]))
    D.place("vs7_65", s, "connector", "Sentinel score ≥ 65? -> Refer to SIU [label: Yes]",
            notes="Threshold in the diamond text; meaning only in the 'Yes' connector (label box 'label:frd-yes-65').")
    D.place("vs7_60", s, "connector", "Tier-3 and score ≥ 60? -> Refer to SIU [label: Yes]",
            notes="Second decision reached via the 'No' branch of the 65 diamond (label box 'label:frd-yes-60').")
    D.fact(s, "connector", "Sentinel score ≥ 65? -> Tier-3 and score ≥ 60? [label: No]",
           "A claim scoring below 65 goes on to the Tier-3 check (score ≥ 60).", kind="arrow_only",
           world_ref="PROCESS:PS-FRD-01#decision")
    D.fact(s, "connector", "Tier-3 and score ≥ 60? -> Continue normal handling [label: No]",
           "Claims failing both checks continue normal handling.", kind="arrow_only",
           world_ref="PROCESS:PS-FRD-01#decision")
    D.fact(s, "notes", "estimated incurred of £50,000 or more (NOK 650,000 / SEK 680,000 / DKK 430,000)",
           "Speaker notes: Tier-3 (BR-TRI-003 v3) = estimated incurred ≥ £50,000 (NOK 650,000 / SEK 680,000 / DKK 430,000), any bodily injury, litigation at notification or property total loss.",
           kind="speaker_notes", world_ref="RULE:BR-TRI-003@v3")

    # 3 swimlane (ungrouped)
    s = D.content("From referral to outcome – who does what", "Fraud referral · swimlane")
    L = swimlane(s, ["Claims Hub (automated)", t11, "Claims Operations", W.team_name("T18", d)],
                 heights=[1.05, 2.0, 1.05, 1.0])
    a1 = L[0].step(2.4, "Sentinel score received", w=1.5, size=9)
    a2 = L[0].step(4.2, "Referral decision", w=1.5, size=9, style="decision", h=0.8)
    b1 = L[1].step(6.0, "Create SIU case", w=1.45, size=9, row=0, rows=2)
    b2 = L[1].step(7.75, "SIU triage", w=1.45, size=9, row=0, rows=2)
    b3 = L[1].step(9.5, "Investigation", w=1.45, size=9, row=0, rows=2)
    b4 = L[1].step(9.5, "Human review before any decline", w=1.6, size=9, row=1, rows=2)
    b5 = L[1].step(11.35, "Record outcome (NF / CF / WD)", w=1.4, size=9, row=1, rows=2)
    c1 = L[2].step(6.0, "Send referral notice or record deferral", w=2.0, size=9)
    e1 = L[3].step(8.4, "Same-day notification of long deferrals", w=2.2, size=9, style="tile")
    s.connect(a1, a2)
    s.connect(a2, b1, a_site="r", b_site="t")
    s.connect(b1, b2)
    s.connect(b2, b3)
    s.connect(b3, b4)
    s.connect(b4, b5)
    s.connect(b1, c1, a_site="b", b_site="t")
    s.connect(c1, e1, a_site="r", b_site="t", dash=True, color="grey")
    s.notes(P.notes(rng, "the hand-offs after a referral",
                    ["SIU triages a new referral within 3 business days.",
                     "Outcomes are recorded as NF (no fraud), CF (confirmed fraud) or WD (withdrawn)."]))
    D.place("vs7_lane_review", s, "text", "Human review before any decline",
            notes="verification: manual-lane; " + L[1].geometry_note(b4))
    D.fact(s, "text", "Send referral notice or record deferral",
           "'Send referral notice or record deferral' sits in the Claims Operations lane of the fraud referral swimlane.",
           kind="lane_only", world_ref="PROCESS:PS-FRD-03#raci.R",
           notes="verification: manual-lane; " + L[2].geometry_note(c1))
    D.fact(s, "text", "Same-day notification of long deferrals",
           f"'Same-day notification of long deferrals' sits in the {W.team_name('T18', d)} lane (BR-FRD-036 v2).",
           kind="lane_only", world_ref="RULE:BR-FRD-036@v2#parameters.notify",
           notes="verification: manual-lane; " + L[3].geometry_note(e1))

    # 4 contents
    CM.agenda(D, ["Referral decision (slide 2)", "Swimlane (slide 3)", "Rules in force", "Customer notice timeline",
                  "Claims Hub referral screen", "Outcome codes", "Accountability", "Volumes and reporting",
                  "Systems, contacts and glossary"], title="Contents", kicker="Fraud referral")

    # 5 document control
    hist = CM.history_rows(D, [("1.0", "Process for NISA Circular 2026/04 (effective 1 April 2026)"), ("1.1", ""), ("2.0", "")],
                           spacing=(40, 90))
    CM.doc_control(D, hist, [("P005", "Approved (co-approver)"), ("P007", "Approved"), ("P037", "Reviewed")],
                   status="Approved", reviewers=[W.name_of(x, d) for x in ("P028", "P027", "P042")],
                   distribution="Counter-Fraud & SIU, Claims Operations, Compliance, Hub Squad – Fraud & Settlement",
                   purpose="Fraud referral process from 1 October 2026, reflecting the Fraud Rules Workshop of 17 September 2026.")

    # 6 section
    D.section("02", "Rules and timelines", "What the process must achieve and by when")

    # 7 rules in force (no referral threshold values in text)
    s = D.content("Rules in force from 1 October 2026", "Rules")
    for rid, ver in [("BR-FRD-032", "v2"), ("BR-FRD-034", "v1"), ("BR-FRD-035", "v2"), ("BR-FRD-036", "v2")]:
        D.need(f"RULE:{rid}@{ver}", "text")
    rows = [("BR-FRD-031", "v2", "Referral threshold – see decision flow", "1 Oct 2026", W.name_of("P008", d)),
            ("BR-FRD-032", "v2", "Customer notice in writing within 10 business days of referral", "1 Apr 2026", W.name_of("P008", d)),
            ("BR-FRD-033", "v1", "No decline, reduction or repudiation on an automated score alone", "1 Apr 2026", W.name_of("P008", d)),
            ("BR-FRD-034", "v1", "NISA-FR1 return within 30 calendar days after quarter end", "1 Apr 2026", W.name_of("P037", d)),
            ("BR-FRD-035", "v2", "SIU triage of a new referral within 3 business days", "1 Apr 2026", W.name_of("P008", d)),
            ("BR-FRD-036", "v2", "Notice deferral up to 60 days; beyond 30 days needs the Head of Counter-Fraud & SIU; Compliance told the same day", "1 Oct 2026", W.name_of("P008", d))]
    s.table(0.5, 1.45, 12.3, ["Rule", "Version", "Requirement", "Effective", "Owner"], rows,
            col_w=[1.2, 0.8, 7.0, 1.4, 1.9], row_h=0.62, size=11, first_col_bold=True)
    s.text(0.5, 5.9, 12.3, 0.8, [{"text": "Superseded: BR-FRD-012 (score 70, until 31 March 2026). Withdrawn: BR-FRD-019 (auto-decline) from 1 April 2026.", "size": 11}],
           size=11, color="slate")
    s.notes(P.notes(rng, "the rules the process implements"))
    D.fact(s, "table", "within 30 calendar days after quarter end",
           "BR-FRD-034: the NISA-FR1 return is due within 30 calendar days after each quarter end (owner Ruth Okafor).",
           world_ref="RULE:BR-FRD-034@v1")
    D.fact(s, "text", "Withdrawn: BR-FRD-019 (auto-decline) from 1 April 2026",
           "BR-FRD-019 (automatic decline) was withdrawn from 2026-04-01; BR-FRD-012 was superseded.",
           world_ref="RULE:BR-FRD-019")

    # 8 customer notice timeline (raster)
    s = D.content("Customer notice – timeline", "Rules")
    cv = R.Canvas(2400, 1100)
    cv.title("Customer notice after a fraud referral", "Business days (BD) counted from the referral date")
    y = 560
    cv.d.line([150, y, 2250, y], fill=R.col("slate"), width=8)
    pts = [(200, "Day 0", "Referral created"), (900, "BD 10", "Notice due"), (1500, "Day 30", "Head of Counter-Fraud & SIU approval needed beyond here"),
           (2150, "Day 60", "Maximum deferral")]
    for x, lab, txt in pts:
        cv.d.ellipse([x - 20, y - 20, x + 20, y + 20], fill=R.col("teal"))
        cv.text(x, y - 90, lab, size=32, bold=True, color="navy", anchor="ma")
        cv.text_block(x - 230, y + 50, 460, txt, size=26, align="center")
    cv.arrow([(200, 360), (900, 360)], "Written notice within 10 business days", label_at=0.5)
    cv.arrow([(200, 880), (2150, 880)], "Deferral if tipping-off risk certified (up to 60 days)", label_at=0.5, dash=True, color="amber")
    png = cv.png()
    s.picture_fit(png, 0.5, 1.35, 12.3, 5.55,
                  alt="Timeline: written customer notice within 10 business days of referral; deferral up to 60 days where a tipping-off risk is certified; deferrals beyond 30 days need the Head of Counter-Fraud & SIU.",
                  title="Customer notice timeline")
    s.notes(P.notes(rng, "the customer notice clock",
                    ["Compliance must be told the same day when a deferral goes beyond 30 days."]))
    D.fact(s, "image", "Written notice within 10 business days",
           "Timeline image: written customer notice within 10 business days of referral (BR-FRD-032 v2).",
           kind="image_text", world_ref="RULE:BR-FRD-032@v2")
    D.fact(s, "alt_text", "deferral up to 60 days where a tipping-off risk is certified",
           "Alt text: deferral up to 60 days where a tipping-off risk is certified; beyond 30 days needs the Head of Counter-Fraud & SIU.",
           kind="alt_text", world_ref="RULE:BR-FRD-036@v2")

    # 9 Claims Hub referral screen
    s = D.content("Claims Hub – fraud referral record (illustrative)", "Screens")
    ref = f"CLM-UK-2026-{rng.randint(400000, 499999)}"
    png = R.ui_screen(
        "Claims Hub", "Rachel Dunmore · Counter-Fraud & SIU",
        ["Work queue", "Claims", "Fraud referrals", "SIU cases", "Notices", "Reports"], "Fraud referrals",
        f"Fraud referrals  /  {ref}", f"Referral for claim {ref}",
        [("Product", "Motor Private UK"), ("Tier", "Tier-2"),
         ("Sentinel score", "71"), ("Referral date", "02 Oct 2026"),
         ("Customer notice due", "16 Oct 2026"), ("Notice status", "Due – not deferred"),
         ("SIU triage due", "07 Oct 2026"), ("Auto-decline", "Disabled"),
         ("Adverse outcome needs", "Documented human review"), ("SIU case", "Created in SIU Case Manager")],
        chips=[("REFERRED", "red"), ("NOTICE DUE", "amber")],
        side_panel=("Deadlines", ["Notice: referral + 10 BD", "Triage: referral + 3 BD", "Max deferral: 60 days"]))
    s.picture_fit(png, 0.9, 1.35, 11.5, 5.55,
                  alt=f"Mock Claims Hub fraud referral screen for illustrative claim {ref}: customer notice due 16 Oct 2026, SIU triage due 07 Oct 2026, auto-decline disabled.")
    s.notes(P.notes(rng, "how a referral looks in Claims Hub", ["The record is training data, not a live claim."]))
    D.fact(s, "image", "Auto-decline",
           "Claims Hub referral screen shows 'Auto-decline: Disabled' (fraud-referral-svc auto-decline.enabled = false).",
           kind="screenshot", world_ref="SERVICE:fraud-referral-svc#config.auto-decline.enabled")
    D.fact(s, "image", "Notice: referral + 10 BD",
           "Claims Hub referral screen deadline panel: notice due at referral + 10 business days; triage at referral + 3 business days.",
           kind="screenshot", world_ref="SERVICE:fraud-referral-svc#config.notice.business-days")

    # 10 outcome codes (grouped)
    s = D.content("SIU outcome codes", "Outcomes")
    g = s.group("SIU outcome codes")
    for i, (code, label, extra) in enumerate([("NF", "No fraud", "Claim continues; handler told within 2 business days of closure"),
                                              ("CF", "Confirmed fraud", "Avoided payment recorded as the fraud saving"),
                                              ("WD", "Withdrawn", "Claim withdrawn by the customer")]):
        sub = g.group(f"Outcome {code}")
        sub.box(0.8 + i * 4.1, 1.8, 3.7, 1.0, code, style="terminal", size=28, bold=True)
        sub.box(0.8 + i * 4.1, 2.9, 3.7, 0.6, label, style="tile", size=14, bold=True)
        sub.box(0.8 + i * 4.1, 3.6, 3.7, 1.3, extra, style="tile", size=11, fill="white", line="grey_m")
    s.notes(P.notes(rng, "the three outcome codes"))
    D.fact(s, "group", "CF Confirmed fraud Avoided payment recorded as the fraud saving",
           "SIU outcome CF (confirmed fraud): the avoided payment is recorded as the fraud saving (BR-FRD-013).",
           kind="visual_only", world_ref="RULE:BR-FRD-013@v1", shape_name="Outcome CF")
    D.fact(s, "group", "NF No fraud Claim continues; handler told within 2 business days of closure",
           "SIU outcome NF: claim handlers receive the SIU outcome within 2 business days of case closure (BR-FRD-017).",
           kind="visual_only", world_ref="RULE:BR-FRD-017@v1", shape_name="Outcome NF")

    # 11 accountability (RACI for referral to investigation only)
    s = D.content("Accountability – referral to investigation", "Accountability")
    rows = CM.raci_rows(W, ["PS-FRD-01", "PS-FRD-02", "PS-FRD-03", "PS-FRD-04"], d)
    s.table(0.5, 1.45, 12.3, ["Step", "Activity", "Responsible", "Accountable", "Consulted", "Informed"], rows,
            col_w=[1.1, 2.6, 2.6, 1.7, 2.3, 2.0], row_h=0.6, size=10, first_col_bold=True)
    s.notes(P.notes(rng, "who is accountable for each step"))
    D.fact(s, "table", "Rachel Dunmore",
           "PS-FRD-04 SIU investigation and outcome: accountable Rachel Dunmore, SIU Investigations Manager (UK).",
           world_ref="PROCESS:PS-FRD-04#raci.A")

    # 12 volumes (chart only)
    s = D.content("Referral volumes", "Volumes")
    cnt = W.timeline["metrics"]["fraud_referrals_count"]
    s.chart(0.5, 1.4, 7.2, 5.4, "column", ["Q2 2026", "Q3 2026"], [("SIU referrals", [cnt["2026Q2"], cnt["2026Q3"]])],
            title="SIU referrals per quarter", legend=False, colors=["navy"])
    s.box(8.1, 1.6, 4.7, 2.4, [{"text": "Context", "bold": True, "size": 13},
                               {"text": "Volumes are the quarters since NISA Circular 2026/04 took effect on 1 April 2026.", "size": 12}],
          style="tile", align="l", anchor="t", margins=0.15)
    s.notes(P.notes(rng, "referral volumes", n_filler=1))
    D.fact(s, "chart", f"SIU referrals: Q3 2026={cnt['2026Q3']}",
           f"SIU referrals: {cnt['2026Q2']} in Q2 2026 and {cnt['2026Q3']} in Q3 2026.", kind="chart_only",
           world_ref="TIMELINE:metrics#fraud_referrals_count")

    # 13 NISA-FR1 reporting
    s = D.content("NISA-FR1 fraud referral return", "Reporting")
    fr1 = W.reports["NISA-FR1"]
    q2 = fr1["submissions"]["2026Q2"]
    s.table(0.5, 1.45, 7.6, ["Item", "Detail"], [
        ("Return", f"{fr1['name']} (NISA-FR1)"), ("Frequency", "Quarterly"),
        ("Due", "30 calendar days after quarter end"),
        ("Prepared by", f"{W.name_of(fr1['preparer'], d)}, {W.title_of(fr1['preparer'], d)}"),
        ("Signed by", fr1["signed_by_role"]),
        ("Feed", "CLX-IF-033, quarterly, 5th business day after quarter end"),
        ("Q2 2026", f"Due {D.date_long(q2['due'])}; submitted {D.date_long(q2['submitted'])}"),
        ("Q3 2026", "Due 30 October 2026"),
    ], col_w=[1.8, 5.8], row_h=0.48, size=11, first_col_bold=True)
    s.notes(P.notes(rng, "the quarterly regulatory return", n_filler=1))
    D.fact(s, "table", f"submitted {D.date_long(q2['submitted'])}",
           "The first NISA-FR1 return (Q2 2026) was due 2026-07-30 and submitted 2026-07-29.",
           world_ref="REPORT:NISA-FR1#submissions.2026Q2")

    # 14 systems (cards)
    from .orgchart import team_cards
    s = D.content("Systems and services", "Systems")
    cards = [("Sentinel", [f"Scores 0–100; model {W.systems['SYS03']['model_version']}", f"Business owner: {W.name_of('P008', d)}", "Called by triage-svc (REST)"]),
             ("fraud-referral-svc", ["Claims Hub service, live since 1 April 2026", "Thresholds as effective-dated configuration (ADR-020)", f"Squad: {W.team_name('T29', d)}"]),
             ("SIU Case Manager", [f"Owner: {W.name_of('P028', d)}", "Holds SIU cases and outcomes", "Fed from Claims Hub via CLX-IF-041"]),
             ("Notify", ["Letters and digital notices to customers", "Sends the referral notice", f"Owner: {W.name_of('P040', d)}"]),
             ("CLARA", ["Referral programs for claims not yet migrated", "Batch referral sweep", f"Owner: {W.name_of('P016', d)}"]),
             ("NISA Reporting Hub", ["Generates the NISA-FR1 return", f"Owner: {W.name_of('P020', d)}", "Fed by CLX-IF-033"])]
    gn = team_cards(D, s, cards, prefix="System card")
    s.notes(P.notes(rng, "the systems behind the process", n_filler=1))
    D.fact(s, "group", "Sentinel Scores 0–100; model SNT-4.2",
           "Sentinel scores claims 0–100 using model SNT-4.2.", kind="visual_only",
           world_ref="SYSTEM:SYS03#model_version", shape_name=gn["Sentinel"])

    # 15 contacts
    CM.contacts(D, [("P008", "Process owner"), ("P028", "SIU investigations"), ("P027", "Sentinel model owner"),
                    ("P037", "Compliance and NISA-FR1 sign-off"), ("P042", "fraud-referral-svc engineering"),
                    ("P011", "Claims operations")])

    # 16 glossary
    CM.glossary(D, [("SIU referral", "Referral of a claim to Counter-Fraud & SIU"),
                    ("Sentinel score", "Fraud score from 0 to 100 produced by Sentinel"),
                    ("referral notice", "Written notice that the claim is subject to additional checks"),
                    ("tipping-off risk", "Risk that notice would prejudice an investigation"),
                    ("NF / CF / WD", "SIU outcome codes: no fraud, confirmed fraud, withdrawn"),
                    ("Tier-3", "Claim meeting BR-TRI-003 v3 (see notes on slide 2)"),
                    ("NISA-FR1", "Quarterly fraud referral return to NISA"),
                    ("BD", "Business day")])
    return D

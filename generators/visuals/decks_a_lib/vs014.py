"""VS014 NISA Circular 2026/04 – Impact Briefing (2026-01-19, Ruth Okafor, final).

The NISA clarification of 2026-01-14 (SMS counts as written notice if followed by a letter within
2 business days) is exclusive and appears only in the notes of slide 6; the word 'SMS' appears
nowhere else in the deck. The slide-2 timeline picture carries the dates in its alt text."""
from __future__ import annotations

from . import common as CM
from . import phrases as P
from . import raster as R
from .core import Deck


def build(W, out_dir):
    D = Deck(W, "VS014", version="1.0", doc_ref="CMP-BRF-2026-01", out_dir=out_dir)
    d = D.date
    rng = D.rng
    circ = W.circulars["CIRC-2026-04"]

    # 1 title
    D.title_slide(D.title, f"{circ['title']} – what changes for Corvane and what we need to do",
                  [f"Compliance  |  {D.date_long()}", f"Prepared by: {D.author}, {D.author_title}", "Status: Final"])

    # 2 circular at a glance (timeline picture with alt text)
    s = D.content("The circular at a glance", "Overview")
    D.need("CIRCULAR:CIRC-2026-04", "effective")
    png = R.timeline_image(f"{circ['ref']} – {circ['title']}", [
        ("20 Nov 2025", "Circular published", False),
        ("19 Jan 2026", "This briefing", False),
        ("1 Apr 2026", "Circular effective", True),
        ("30 Jul 2026", "First NISA-FR1 return due (Q2 2026)", False)], height=820)
    s.picture_fit(png, 0.5, 1.35, 8.2, 4.6, alt="Circular published 20 Nov 2025, effective 1 Apr 2026",
                  title="Circular timeline")
    s.box(9.0, 1.5, 3.8, 3.6, [{"text": "In one line", "bold": True, "size": 13},
                               {"text": "Fraud referral must be calibrated, explained to the customer and never turn into a decline without human review.", "size": 12},
                               {"text": f"Author at NISA: {W.name_of(circ['author'], d)}, {W.title_of(circ['author'], d)}", "size": 10, "color": "slate"}],
          style="tile", align="l", anchor="t", margins=0.15)
    s.notes(P.notes(rng, "the circular and its timetable", n_filler=2))
    D.place("vs14_alt", s, "alt_text", "Circular published 20 Nov 2025, effective 1 Apr 2026")
    D.fact(s, "image", "Circular effective",
           "Timeline image: NISA Circular 2026/04 effective 1 Apr 2026 (published 20 Nov 2025).", kind="image_text",
           world_ref="CIRCULAR:CIRC-2026-04#effective")

    # 3 agenda
    CM.agenda(D, ["Requirements", "Gap against current rules", "Customer notice", "Proposed rule changes",
                  "Systems impact", "Future referral flow", "Plan", "NISA-FR1 return", "Risks, governance and contacts"],
              kicker="Impact briefing")

    # 4 requirements
    s = D.content("What the circular requires", "Requirements")
    D.need("CIRCULAR:CIRC-2026-04", "requirements")
    rows = [(f"§{r['para']}", r["text"]) for r in circ["requirements"]]
    s.table(0.5, 1.45, 12.3, ["Para", "Requirement"], rows, col_w=[0.9, 11.4], row_h=0.7, size=12, first_col_bold=True)
    s.notes(P.notes(rng, "the five requirements", n_filler=1))
    D.fact(s, "table", "on a 0–100 scale the cut-off must not exceed 65",
           "NISA Circular 2026/04 §3.3: score-based referral cut-offs must be calibrated and documented; on a 0–100 scale the cut-off must not exceed 65.",
           world_ref="CIRCULAR:CIRC-2026-04#requirements")
    D.fact(s, "table", "Retain referral records for 7 years",
           "NISA Circular 2026/04 §3.5: retain referral records for 7 years.", world_ref="CIRCULAR:CIRC-2026-04#requirements")

    # 5 gap analysis (rules as at 2026-01-19)
    s = D.content("Gap against current Corvane rules", "Gap analysis")
    r012 = W.rule_version("BR-FRD-012", d)
    r035 = W.rule_version("BR-FRD-035", d)
    rows = [("§3.3 cut-off ≤ 65", f"BR-FRD-012 v{r012['version']}: refer at score {r012['parameters']['threshold']} or more", "Gap", "Lower the referral cut-off"),
            ("§3.1 no decision on score alone", "BR-FRD-019 v2: automatic decline at score 90 or more", "Gap", "Withdraw automatic decline; add documented human review"),
            ("§3.2 customer notice", "No rule today", "Gap", "New rule and notice templates"),
            ("§3.4 NISA-FR1 return", "No return today", "Gap", "New quarterly extract and return"),
            ("§3.5 retention", "Claims retention policy (7 years after closure)", "Check", "Confirm referral records are covered"),
            ("SIU triage timeliness", f"BR-FRD-035 v{r035['version']}: triage within {r035['parameters']['business_days']} business days", "Review", "Review the target alongside the new notice clock")]
    s.table(0.5, 1.45, 12.3, ["Requirement", "Current position", "Status", "Action"], rows, col_w=[2.8, 4.5, 1.0, 4.0],
            row_h=0.62, size=11, first_col_bold=True)
    s.notes(P.notes(rng, "where we fall short today",
                    ["The 70 cut-off has applied since 1 April 2023, when it came down from 75."]))
    D.fact(s, "table", "automatic decline at score 90 or more",
           "January 2026 gap analysis: BR-FRD-019 v2 automatically declines claims scoring 90 or more, which §3.1 prohibits.",
           kind="temporal", world_ref="RULE:BR-FRD-019@v2")
    D.fact(s, "table", "refer at score 70 or more",
           "January 2026 gap analysis: the referral threshold in force is BR-FRD-012 v2, score 70 or more.",
           kind="temporal", world_ref="RULE:BR-FRD-012@v2")
    D.fact(s, "notes", "since 1 April 2023, when it came down from 75",
           "Speaker notes: the referral cut-off of 70 has applied since 2023-04-01 (previously 75).", kind="speaker_notes",
           world_ref="RULE:BR-FRD-012@v2")

    # 6 customer notice (clarification only in notes)
    s = D.content("Customer notice (§3.2)", "Customer notice")
    s.bullets(0.6, 1.5, 7.8, 5.0, [
        "Tell the customer in writing within 10 business days of referral that the claim is subject to additional checks.",
        "The notice may be deferred for up to 60 days where a tipping-off risk is certified.",
        "Wording must not suggest the customer is suspected of fraud.",
        "Notices will be produced through Notify from Claims Hub and CLARA.",
        "Channel approach to be confirmed with Compliance before the requirements are baselined.",
    ], size=13)
    s.box(8.8, 1.6, 4.0, 2.6, [{"text": "Owner", "bold": True, "size": 13},
                               {"text": f"{W.name_of('P008', d)} (process) with {W.name_of('P037', d)} (Compliance)", "size": 12}],
          style="tile", align="l", anchor="t", margins=0.15)
    D.need("DECISION:DEC-013")
    s.notes(P.notes(rng, "the customer notice requirement",
                    ["Update from the call with the regulator: NISA (Petter Ulvestad) confirmed on 2026-01-14 that an SMS counts as written notice if followed by a letter within 2 business days.",
                     "Treat this as the basis for the channel design; the confirmation will be minuted in the call notes."]))
    D.place("vs14_sms", s, "notes",
            "confirmed on 2026-01-14 that an SMS counts as written notice if followed by a letter within 2 business days",
            notes="Exclusive (also in TX043 call notes). No slide text mentions the clarification.")

    # 7 proposed rule changes
    s = D.content("Proposed rule changes", "Rules")
    s.table(0.5, 1.45, 12.3, ["Change", "Replaces", "Driver"], [
        ("Refer to SIU at a Sentinel score of 65 or more", "BR-FRD-012 v2 (70)", "§3.3"),
        ("Withdraw automatic decline", "BR-FRD-019 v2", "§3.1"),
        ("Documented human review before any adverse outcome", "New", "§3.1"),
        ("Customer notice within 10 business days; deferral up to 60 days", "New", "§3.2"),
        ("NISA-FR1 return within 30 days after each quarter end", "New", "§3.4")],
        col_w=[6.6, 3.2, 2.5], row_h=0.62, size=12)
    s.text(0.5, 5.4, 12.3, 1.0, [{"text": "For approval by the Claims Fraud Forum and the Claims Director before the effective date.", "size": 12}],
           size=12, color="slate")
    s.notes(P.notes(rng, "the rule changes we will propose", n_filler=1))
    D.fact(s, "table", "Refer to SIU at a Sentinel score of 65 or more",
           "January 2026 proposal: refer to SIU at a Sentinel score of 65 or more, replacing BR-FRD-012 v2 (70).",
           kind="temporal", world_ref="RULE:BR-FRD-031@v1")

    # 8 systems impact (cards)
    from .orgchart import team_cards
    s = D.content("Systems impact", "Systems")
    cards = [("Sentinel", ["Scores 0–100", "Cut-off calibration evidence for §3.3", f"Model owner: {W.name_of('P027', d)}"]),
             ("CLARA", ["Referral and batch sweep programs", "Remove automatic decline", f"Owner: {W.name_of('P016', d)}"]),
             ("fraud-referral-svc", ["Claims Hub service", "Planned go-live 1 April 2026", "Holds the notice deadline"]),
             ("Notify", ["Customer notice letters", "Templates reviewed by Compliance", f"Owner: {W.name_of('P040', d)}"]),
             ("SIU Case Manager", ["Records the human review", "Outcome codes NF / CF / WD", f"Owner: {W.name_of('P028', d)}"]),
             ("NISA Reporting Hub", ["New NISA-FR1 return", "Quarterly", f"Owner: {W.name_of('P020', d)}"])]
    gn = team_cards(D, s, cards, prefix="Impact card")
    s.notes(P.notes(rng, "which systems change", n_filler=1))
    D.fact(s, "group", "fraud-referral-svc Claims Hub service Planned go-live 1 April 2026",
           "fraud-referral-svc (Claims Hub) is planned to go live on 2026-04-01 for the circular.", kind="visual_only",
           world_ref="SERVICE:fraud-referral-svc#go_live", shape_name=gn["fraud-referral-svc"])

    # 9 future referral flow (connectors)
    s = D.content("Future referral flow (proposed)", "Process")
    a = s.box(0.5, 3.1, 2.1, 0.8, "Sentinel score", style="terminal", size=12, bold=True)
    q = s.box(3.1, 2.8, 2.2, 1.4, "Score ≥ 65?", style="decision", size=13, bold=True)
    r = s.box(6.1, 1.6, 2.3, 0.8, "Refer to SIU", style="alert", size=12, bold=True)
    n = s.box(9.3, 1.6, 3.3, 0.8, "Customer notice ≤ 10 business days", style="process", size=11)
    o = s.box(6.1, 4.6, 2.3, 0.8, "Normal handling", style="process", size=12)
    h = s.box(9.3, 3.1, 3.3, 0.8, "Documented human review", style="outcome", size=11)
    x = s.box(9.3, 4.6, 3.3, 0.8, "Outcome recorded", style="process", size=11)
    s.connect(a, q)
    s.connect(q, r, a_site="t", b_site="l", label="Yes", name="fut-yes", label_size=10)
    s.connect(q, o, a_site="b", b_site="l", label="No", name="fut-no", label_size=10)
    s.connect(r, n)
    s.connect(r, h, a_site="b", b_site="l", label="Adverse outcome proposed", name="fut-adverse", label_size=9)
    s.connect(h, x)
    s.notes(P.notes(rng, "how the referral flow will look after 1 April", n_filler=1))
    D.fact(s, "connector", "Refer to SIU -> Documented human review [label: Adverse outcome proposed]",
           "Proposed flow: when an adverse outcome is proposed on a referred claim, a documented human review is required.",
           kind="arrow_only", world_ref="CIRCULAR:CIRC-2026-04#requirements")
    D.fact(s, "connector", "Score ≥ 65? -> Refer to SIU [label: Yes]",
           "Proposed flow (January 2026): a Sentinel score of 65 or more leads to SIU referral.", kind="arrow_only",
           world_ref="RULE:BR-FRD-031@v1")

    # 10 plan
    s = D.content("Plan to 1 April 2026", "Plan")
    g = s.group("Plan phases")
    phases = [("Jan 2026", "Impact briefing"), ("Feb 2026", "Business requirements"),
              ("Mar 2026", "Rule approval"), ("1 Apr 2026", "Circular effective"), ("30 Jul 2026", "First NISA-FR1 return")]
    for i, (when, what) in enumerate(phases):
        g.box(0.5 + i * 2.5, 1.9, 2.55, 1.0, what, style="chevron" if i else "pentagon", size=12, bold=True,
              fill="teal" if i != 3 else "amber")
        g.text(0.65 + i * 2.5, 3.05, 2.2, 0.4, [{"text": when, "bold": True}], size=12, color="navy")
    s.bullets(0.6, 3.9, 12.0, 2.5, ["Requirements will be written by the IBM business analyst with Counter-Fraud & SIU.",
                                    "Build in CLARA and in fraud-referral-svc runs in parallel.",
                                    "Training for claim handlers and SIU before go-live."], size=12)
    s.notes(P.notes(rng, "the plan to the effective date", n_filler=1))

    # 11 NISA-FR1
    s = D.content("New NISA-FR1 fraud referral return (§3.4)", "Reporting")
    fr1 = W.reports["NISA-FR1"]
    s.table(0.5, 1.45, 8.0, ["Item", "Detail"], [
        ("Return", f"{fr1['name']} (NISA-FR1)"), ("Frequency", "Quarterly"),
        ("Due", "Within 30 days after each quarter end"), ("First period", "Q2 2026, due 30 July 2026"),
        ("Prepared by", f"{W.name_of(fr1['preparer'], d)}, {W.title_of(fr1['preparer'], d)}"),
        ("Signed by", fr1["signed_by_role"]), ("System", W.system_name(fr1["system"], d))],
        col_w=[2.0, 6.0], row_h=0.5, size=11, first_col_bold=True)
    s.notes(P.notes(rng, "the new return", ["A new CLARA extract to the NISA Reporting Hub is needed for the return."]))
    D.fact(s, "table", "Q2 2026, due 30 July 2026", "The first NISA-FR1 return covers Q2 2026 and is due 2026-07-30.",
           world_ref="REPORT:NISA-FR1#first_due")

    # 12 risks
    s = D.content("Risks and dependencies", "Risks")
    s.table(0.5, 1.45, 12.3, ["Risk", "Mitigation"], [
        ("Referral volumes rise when the cut-off falls", "SIU capacity plan before 1 April"),
        ("Notice wording read as an accusation", "Compliance review of templates"),
        ("CLARA and Claims Hub diverge on thresholds", "Single parameter source and joint testing"),
        ("Return data incomplete for the first quarter", "Dry run of the extract before the quarter ends")],
        col_w=[5.6, 6.7], row_h=0.62, size=12)
    s.notes(P.notes(rng, "the main risks", n_filler=1))

    # 13 contacts
    CM.contacts(D, [("P037", "Implementation lead"), ("P008", "Fraud referral process owner"), ("P005", "Co-approver of fraud rules"),
                    ("P054", "Business requirements"), ("P056", "NISA policy lead (author of the circular)"),
                    ("P055", "NISA supervisor for Corvane")])

    # 14 document control
    hist = CM.history_rows(D, [("0.1", ""), ("1.0", "")], spacing=(4, 8), kind="final")
    CM.doc_control(D, hist, [("P007", "Reviewed"), ("P008", "Reviewed")], status="Final",
                   reviewers=[W.name_of(x, d) for x in ("P005", "P028")],
                   distribution="Claims Fraud Forum members, Risk & Compliance leadership",
                   purpose="Impact of NISA Circular 2026/04 on Corvane's fraud referral process.", approval_label="Review")
    return D

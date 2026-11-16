"""VS006 Programme Skerry Steering Committee – 8 October 2026 (pack dated 2026-10-07, Arjun Kesavan, final).

The cumulative spend (£31.2m to 2026-09-30) appears only in the native chart on slide 4; the
contingency request appears only in the speaker notes of slide 6, with the CFO written as 'PR'."""
from __future__ import annotations

from . import common as CM
from . import phrases as P
from . import raster as R
from .core import Deck


def build(W, out_dir):
    D = Deck(W, "VS006", version="1.0", doc_ref="SKR-STC-2026-10", classification="Confidential", out_dir=out_dir)
    d = D.date
    rng = D.rng
    mtg = W.meetings["MTG-008"]
    chair = W.committees["COM-03"]["chair_history"][-1]["person"]

    # 1 title
    D.title_slide(D.title, "Monthly steering pack",
                  [f"Chair: {W.name_of(chair, d)}, {W.title_of(chair, d)}",
                   f"Prepared by: {D.author}, {D.author_title} (IBM Consulting)  |  {D.date_long()}",
                   "Status: Final – for the meeting on 8 October 2026"])

    # 2 agenda + attendees
    s = D.content("Agenda and attendees", "Steering Committee")
    items = ["Programme status", "Financials", "Wave 1 hypercare", "Wave 2 readiness and contingency",
             "Wave 2 timeline", "Fraud rule change (live 1 October)", "Reserve parallel run close-out",
             "Risks", "Decisions requested", "Milestones and next meeting"]
    for i, it in enumerate(items):
        s.box(0.6, 1.45 + i * 0.5, 0.42, 0.4, str(i + 1), style="terminal", size=12, bold=True)
        s.text(1.15, 1.45 + i * 0.5, 5.6, 0.4, [{"text": it}], size=13, anchor="m")
    rows = [(W.name_of(p, d), W.title_of(p, d)) for p in mtg["attendees"]]
    s.text(7.3, 1.3, 5.5, 0.3, [{"text": "Invited", "bold": True}], size=12, color="navy")
    s.table(7.3, 1.65, 5.5, ["Name", "Role"], rows, col_w=[2.0, 3.5], row_h=0.36, size=10, first_col_bold=True)
    s.notes(P.notes(rng, "the agenda for the October meeting",
                    [f"{W.name_of(chair, d)} chairs; the Steering Committee meets monthly on the second Thursday at 14:00."]))
    D.fact(s, "table", "Priya Raman",
           "The October 2026 Steering Committee invite list includes Priya Raman, Chief Financial Officer.",
           world_ref="MEETING:MTG-008#attendees")

    # 3 status summary
    s = D.content("Programme status summary", "Status")
    rag = [("Wave 1 – UK motor", "Green", "Cut-over completed on 14 September 2026; hypercare in progress"),
           ("Wave 1 hypercare", "Amber", "Severity 2 and 3 defects being burned down (see slide 5)"),
           ("Wave 2 readiness", "Amber", "Scope confirmed; contingency request for decision today"),
           ("Fraud rules (NISA Circular 2026/04)", "Green", "BR-FRD-031 v2 and BR-FRD-036 v2 live from 1 October 2026"),
           ("Reserve parallel run", "Green", "Closed on 28 August 2026 (CHUB-241)"),
           ("Financials", "Amber", "Within the approved budget; contingency use requested")]
    s.table(0.5, 1.45, 12.3, ["Workstream", "RAG", "Comment"], rag, col_w=[3.2, 1.0, 8.1], row_h=0.55, size=11,
            first_col_bold=True)
    s.notes(P.notes(rng, "the overall programme status",
                    ["The amber ratings are driven by Wave 2 timing and the hypercare defect queue, not by Wave 1 stability."]))
    D.fact(s, "table", "Closed on 28 August 2026 (CHUB-241)",
           "The reserve parallel run closed on 2026-08-28 (CHUB-241).", world_ref="EVENT:EV-031")

    # 4 financials (chart only)
    s = D.content("Financials – cumulative spend against budget", "Financials")
    spend = W.timeline["metrics"]["programme_spend_cumulative_gbp_m"]
    budget = W.timeline["metrics"]["programme_budget_gbp_m"]
    cats = [f"{k[:4]} {k[4:]}" for k in spend]
    D.need("TIMELINE:metrics", "programme_spend_cumulative_gbp_m.2026Q3")
    s.chart(0.5, 1.4, 8.2, 5.45, "line", cats,
            [("Cumulative spend (£m)", list(spend.values())), ("Approved budget (£m)", [budget] * len(cats))],
            title="Programme Skerry – cumulative spend vs approved budget (£m)", number_format="0.0",
            label_format="0.0", colors=["teal", "amber"], axis_min=0, axis_max=55)
    s.box(9.0, 1.6, 3.8, 3.0, [{"text": "Commentary", "bold": True, "size": 13},
                               {"text": "Spend is inside the approved envelope at the end of Q3 2026.", "size": 11},
                               {"text": "Run-rate rose through Wave 1 rehearsals and cut-over, as planned.", "size": 11},
                               {"text": "Wave 2 contingency is covered on slide 6.", "size": 11}],
          style="tile", align="l", anchor="t", margins=0.15)
    s.notes(P.notes(rng, "the programme financials",
                    ["Figures are cumulative from the start of the IBM engagement and reconcile to the Finance ledger at quarter end."]))
    D.place("vs6_spend", s, "chart", "Cumulative spend (£m): 2026 Q3=31.2",
            notes="Value only in the chart cache (line series); the slide text gives no figures.")
    D.fact(s, "chart", "Approved budget (£m): 2026 Q3=48.6",
           "Programme Skerry approved budget is £48.6m (chart series).", kind="chart_only",
           world_ref="TIMELINE:metrics#programme_budget_gbp_m")
    D.fact(s, "chart", "Cumulative spend (£m): 2026 Q2=26.8",
           "Programme spend to 2026-06-30 was £26.8m (chart series).", kind="chart_only",
           world_ref="TIMELINE:metrics#programme_spend_cumulative_gbp_m.2026Q2")

    # 5 wave 1 hypercare (chart)
    s = D.content("Wave 1 hypercare – open defects", "Wave 1")
    dfx = W.timeline["metrics"]["wave1_open_defects"]
    s.chart(0.5, 1.4, 6.6, 5.45, "column", ["Severity 1", "Severity 2", "Severity 3"],
            [("Open defects at 5 Oct 2026", [dfx["sev1"], dfx["sev2"], dfx["sev3"]])],
            title="Wave 1 open defects by severity (snapshot 5 October 2026)", legend=False,
            colors=["navy"])
    s.bullets(7.5, 1.6, 5.3, 4.8, [
        "UK motor (Motor Private UK) moved to Claims Hub on 14 September 2026.",
        "assessment-svc, reserve-engine, settlement-svc, payment-orchestrator, recovery-svc and gl-posting-svc went live with Wave 1.",
        "Defect triage runs daily with the squads; fixes ship through the weekly CAB.",
        "Exit from hypercare is proposed for the November meeting.",
    ], size=12)
    s.notes(P.notes(rng, "how Wave 1 hypercare is going", n_filler=2))
    D.fact(s, "chart", "Open defects at 5 Oct 2026: Severity 2=14",
           "Wave 1 open defects on 2026-10-05: 0 severity 1, 14 severity 2, 57 severity 3.", kind="chart_only",
           world_ref="TIMELINE:metrics#wave1_open_defects")

    # 6 wave 2 readiness + contingency (notes)
    s = D.content("Wave 2 readiness and contingency", "Wave 2")
    mw2 = W.waves["MW-2"]
    prods = [W.products[p]["name"] for p in mw2["scope"].split(", ")]
    s.text(0.6, 1.45, 6.0, 0.35, [{"text": "Scope", "bold": True}], size=13, color="navy")
    s.bullets(0.6, 1.85, 6.0, 3.6, prods, size=12)
    s.text(6.9, 1.45, 5.9, 0.35, [{"text": "Readiness", "bold": True}], size=13, color="navy")
    s.bullets(6.9, 1.85, 5.9, 3.0, [
        "Planned cut-over: 15 February 2027 (for confirmation today).",
        "Nordic products bring currency and regress handling into scope.",
        "Rehearsal approach re-uses the Wave 1 runbook.",
        "Contingency drawdown request – decision on slide 11.",
    ], size=12)
    s.box(6.9, 5.0, 5.9, 1.2, [{"text": "Decision requested", "bold": True, "size": 12},
                               {"text": "Approve a contingency drawdown for Wave 2 (paper circulated with the pack).", "size": 11}],
          style="alert", align="l", anchor="t", margins=0.12)
    D.need("DECISION:DEC-010", "statement")
    s.notes(P.notes(rng, "Wave 2 readiness",
                    ["PR asked for a £1.8m contingency drawdown for Wave 2.",
                     "Drawdowns above £500,000 need the CFO's approval, so the request is tabled for her decision at this meeting."]))
    D.place("vs6_notes_pr", s, "notes", "PR asked for a £1.8m contingency drawdown for Wave 2",
            notes="'PR' = Priya Raman, CFO since 2025-07-01 (alias trap).")
    D.fact(s, "notes", "Drawdowns above £500,000 need the CFO's approval",
           "Speaker notes: programme budget drawdowns above £500,000 need the CFO's approval.", kind="speaker_notes",
           world_ref="PERSON:P001#responsibilities")
    D.fact(s, "text", "Planned cut-over: 15 February 2027",
           "Steering pack (2026-10-07): Wave 2 cut-over planned for 2027-02-15, for confirmation at the meeting.",
           world_ref="WAVE:MW-2#date")

    # 7 wave 2 timeline (chevrons, freeze window)
    s = D.content("Wave 2 – path to cut-over", "Wave 2")
    g = s.group("Wave 2 phases")
    phases = ["Build and test", "Rehearsals", "Go / no-go", "Freeze", "Cut-over", "Hypercare"]
    for i, ph in enumerate(phases):
        g.box(0.5 + i * 2.07, 1.8, 2.15, 0.95, ph, style="chevron" if i else "pentagon", size=12, bold=True,
              fill="teal" if i < 3 else "navy2")
    D.need("WAVE:MW-2", "freeze")
    s.box(0.6, 3.3, 6.0, 1.4, [{"text": "Freeze window (planned)", "bold": True, "size": 13},
                               {"text": mw2["freeze"].replace(" to ", " → "), "size": 14}],
          style="tile", align="l", anchor="t", margins=0.15)
    s.box(6.9, 3.3, 5.9, 1.4, [{"text": "Cut-over", "bold": True, "size": 13},
                               {"text": "Monday 15 February 2027, business open on Claims Hub", "size": 13}],
          style="tile", align="l", anchor="t", margins=0.15)
    s.text(0.6, 5.0, 12.0, 1.2, [{"text": "Rehearsal dates are held in the cut-over plan and will be baselined once the date is confirmed.", "size": 11}],
           size=11, color="slate")
    s.notes(P.notes(rng, "the path to the Wave 2 cut-over", n_filler=1))
    D.fact(s, "text", "2027-02-12 18:00 → 2027-02-15 06:00",
           "Wave 2 freeze window planned from 2027-02-12 18:00 to 2027-02-15 06:00.", world_ref="WAVE:MW-2#freeze")

    # 8 fraud rule change
    s = D.content("Fraud rule change – live from 1 October 2026", "Regulatory")
    s.bullets(0.6, 1.5, 7.6, 5.0, [
        "BR-FRD-031 v2: Tier-3 claims are referred to SIU at a Sentinel score of 60 or more; the general threshold stays at 65.",
        "BR-FRD-036 v2: customer-notice deferrals beyond 30 days need the Head of Counter-Fraud & SIU; Compliance is told the same day.",
        "Both changes were agreed at the Fraud Rules Workshop on 17 September 2026 (DEC-014, DEC-015).",
        "The option to lower the general threshold to 60 for all claims was rejected (DEC-016).",
        "fraud-referral-svc holds the thresholds as effective-dated configuration (ADR-020).",
    ], size=13)
    s.box(8.6, 1.6, 4.2, 2.2, [{"text": "Owner", "bold": True, "size": 12},
                               {"text": f"{W.name_of('P008', d)}, {W.title_of('P008', d)}", "size": 12},
                               {"text": "Co-approver: the Claims Director", "size": 11}],
          style="tile", align="l", anchor="t", margins=0.15)
    s.notes(P.notes(rng, "the fraud rule change that went live last week"))
    D.fact(s, "text", "Tier-3 claims are referred to SIU at a Sentinel score of 60 or more; the general threshold stays at 65",
           "From 2026-10-01 Tier-3 claims are referred to SIU at a Sentinel score of 60 or more; the general threshold stays 65 (BR-FRD-031 v2).",
           world_ref="RULE:BR-FRD-031@v2")

    # 9 parallel run close-out
    s = D.content("Reserve parallel run – close-out", "Reserving")
    D.need("TIMELINE:programme", "parallel_run.from")
    s.bullets(0.6, 1.5, 7.6, 4.8, [
        "CLARA and reserve-engine ran in parallel from 2 March to 28 August 2026 (CHUB-241).",
        "Daily reserve movements reached reserve-engine through CLX-IF-049 and topic claims.reserve.movement.v1.",
        "The run completed before the Wave 1 cut-over; reserve-engine became the reserve system for UK motor on 14 September 2026.",
        "Lessons learned feed the Wave 2 reconciliation design.",
    ], size=13)
    s.notes(P.notes(rng, "the reserve parallel run close-out",
                    [f"{W.name_of('P041', d)} led the reserve-engine side of the run for the Reserve & Finance squad."]))
    D.fact(s, "text", "ran in parallel from 2 March to 28 August 2026",
           "The reserve parallel run (CLARA vs reserve-engine) ran from 2026-03-02 to 2026-08-28.",
           world_ref="TIMELINE:programme#parallel_run.from")

    # 10 risks
    s = D.content("Top risks", "RAID")
    risks = [("R1", "Wave 2 brings four products across three countries into one cut-over", "Amber", "Rehearse per country; go / no-go per product"),
             ("R2", "SUBTRAK retirement depends on recovery-svc stability after Wave 1", "Amber", "Retirement target 31 December 2026 kept under review"),
             ("R3", "Regulatory extracts still come from CLARA until reporting-feed-svc is live", "Amber", "reporting-feed-svc go-live planned 11 January 2027"),
             ("R4", "Hypercare load competes with Wave 2 build", "Green", "Capacity ring-fenced per squad")]
    s.table(0.5, 1.45, 12.3, ["ID", "Risk", "RAG", "Mitigation"], risks, col_w=[0.5, 6.0, 0.8, 5.0], row_h=0.7, size=11)
    s.notes(P.notes(rng, "the top programme risks", n_filler=1))
    D.fact(s, "table", "reporting-feed-svc go-live planned 11 January 2027",
           "reporting-feed-svc go-live is planned for 2027-01-11.", world_ref="SERVICE:reporting-feed-svc#go_live")

    # 11 decisions requested
    s = D.content("Decisions requested", "Decisions")
    s.table(0.5, 1.45, 12.3, ["#", "Decision", "Requested from"], [
        ("1", "Approve the Wave 2 contingency drawdown (see paper)", "Chief Financial Officer and Chair"),
        ("2", "Confirm the Wave 2 cut-over date of 15 February 2027", "Chair"),
        ("3", "Note the fraud rule change live from 1 October 2026", "Committee"),
    ], col_w=[0.5, 8.0, 3.8], row_h=0.6, size=12)
    s.notes(P.notes(rng, "the decisions we need today", n_filler=1))

    # 12 milestones (image table)
    s = D.content("Programme milestones", "Milestones")
    tl = W.timeline["programme"]
    rows = [("Business case signed (£48.6m)", "18 Nov 2024", "Complete"),
            ("IBM engagement start", "13 Jan 2025", "Complete"),
            ("Claims Hub MVP live", "3 Nov 2025", "Complete"),
            ("Reserve parallel run", "2 Mar – 28 Aug 2026", "Complete"),
            ("Wave 0 – Denmark", "1 Jun 2026", "Complete"),
            ("Wave 1 – UK motor", "14 Sep 2026", "Complete"),
            ("BR-FRD-031 v2 live", "1 Oct 2026", "Complete"),
            ("Wave 2 cut-over", "15 Feb 2027", "Planned"),
            ("CLARA decommissioning", "30 Sep 2027", "Target")]
    png = R.table_image(["Milestone", "Date", "Status"], rows, [5.0, 3.0, 2.0], size=28,
                        title="Programme Skerry milestones", highlight_rows=(7,))
    s.picture_fit(png, 1.2, 1.35, 10.9, 5.55, alt="Milestone table for Programme Skerry from business case to CLARA decommissioning.")
    s.notes(P.notes(rng, "the programme milestones",
                    ["The business case was signed by the then CFO, Gareth Whitcombe, on 18 November 2024."]))
    D.fact(s, "image", "CLARA decommissioning",
           "Milestone table image: CLARA decommissioning target 30 Sep 2027.", kind="image_table",
           world_ref="TIMELINE:programme#clara_decommission_target")
    D.fact(s, "notes", "signed by the then CFO, Gareth Whitcombe, on 18 November 2024",
           "Speaker notes: the business case was signed by the then CFO, Gareth Whitcombe, on 2024-11-18.",
           kind="speaker_notes", world_ref="EVENT:EV-010")

    # 13 next meeting
    s = D.content("Next meeting", "Close")
    s.box(0.6, 1.6, 6.0, 1.6, [{"text": "Thursday 12 November 2026, 14:00 UK time", "bold": True, "size": 16},
                               {"text": "Corvane House, London, and video", "size": 12}],
          style="tile", align="l", anchor="t", margins=0.18)
    s.bullets(7.0, 1.6, 5.8, 4.5, ["Wave 1 hypercare exit", "Wave 2 rehearsal plan", "Q3 financial close-out",
                                   "SUBTRAK retirement readiness"], size=13)
    s.notes(P.notes(rng, "the next meeting", n_filler=1))
    return D

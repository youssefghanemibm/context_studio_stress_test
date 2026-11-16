"""LD029 – Board Risk Committee Pack – September 2026 (reportlab PDF, 2026-09-24, Priya Raman).

'The CFO' who presents the reserving update (agenda item 4) is Priya Raman (PL-072). Facts owned by other files are
not stated: programme spend to Q3 2026, Wave 1 claim counts, Q3 combined ratio, referral rates, the INC-2026-0702
recovery figures, the Sentinel AUC/PSI and the DEC-016 impact estimate.
"""
from __future__ import annotations

from . import common as C
from . import figures as FG
from .core import CACHE, Ctx, Doc, F, PF, Style, W, long_date, short_date, util
from .prose import Prose

FID = "LD029"

AGENDA = [
    # item, title, presenter pid (or None), purpose, minutes
    ("1", "Welcome, apologies and declarations of interest", None, "For noting", 5),
    ("2", "Minutes of the previous meeting and action log", None, "For approval", 5),
    ("3", "Chief Risk Officer's report and risk profile", "P007", "For discussion", 25),
    ("4", "Reserving update", "CFO", "For discussion", 25),
    ("5", "Programme Skerry: migration risk update", "P004", "For discussion", 20),
    ("6", "Fraud and financial crime update", "P008", "For noting", 15),
    ("7", "Operational resilience and incidents", "P006", "For noting", 15),
    ("8", "Regulatory and compliance update", "P037", "For noting", 10),
    ("9", "Model risk", "P007", "For noting", 10),
    ("10", "Third-party risk", "P004", "For noting", 10),
    ("11", "Forward plan and any other business", None, "For noting", 5),
]

# incident fields that would leak facts owned by other files (VS034 recovery metric, ST030 partition count)
INCIDENT_OMIT = {"INC-2026-0702": ("impact",), "INC-2026-0311": ("root_cause",)}

RISKS = [
    ("PR-01", "Reserving adequacy", "CFO", "Amber", "Stable"),
    ("PR-02", "Migration execution (Programme Skerry)", "P004", "Amber", "Improving"),
    ("PR-03", "Operational resilience of claims payments", "P006", "Amber", "Stable"),
    ("PR-04", "Fraud and financial crime", "P008", "Amber", "Stable"),
    ("PR-05", "Regulatory compliance (claims conduct)", "P005", "Green", "Stable"),
    ("PR-06", "Data protection and retention", "P019", "Amber", "Stable"),
    ("PR-07", "Model risk", "P007", "Green", "Stable"),
    ("PR-08", "Third-party and outsourcing", "P004", "Amber", "Stable"),
    ("PR-09", "Key-person dependency on legacy skills", "P006", "Amber", "Improving"),
    ("PR-10", "Information security", "P006", "Amber", "Stable"),
    ("PR-11", "Reinsurance counterparty", "CFO", "Green", "Stable"),
    ("PR-12", "Change capacity", "P004", "Amber", "Deteriorating"),
]


def build() -> Doc:
    ctx = Ctx(FID)
    date = ctx.date
    pr = Prose(util.rng(f"{FID}:prose"), date=ctx.date)
    cfo = ctx.holder("the CFO")
    pres = lambda p: f"the CFO ({ctx.name(cfo)})" if p == "CFO" else (ctx.person(p) if p else "Chair")  # noqa: E731
    doc = Doc(ctx, title="Board Risk Committee Pack – September 2026", doc_id="BRC-2026-09", version="Final",
              status="Final", subtitle=f"Meeting of {long_date(date)}, 10:00, Board Room, London",
              style=Style(accent="2C3E50", accent2="D6DBDF", size=12, pdf_leading=1.75),
              header_left="Corvane Mutual – Board Risk Committee", header_right=f"Pack for {short_date(date)}",
              footer_left="Board confidential", classification="Board confidential")
    doc.title_page([["Meeting", "Board Risk Committee"], ["Date", long_date(date)], ["Time", "10:00 – 13:00"],
                    ["Location", "Board Room, London head office, and video conference"],
                    ["Pack prepared by", ctx.person(cfo)], ["Secretary", "Company Secretary"],
                    ["In attendance", "; ".join(ctx.person(p) for p in ("P003", cfo, "P004", "P005", "P006", "P007", "P010"))],
                    ["Classification", "Board confidential"]])

    # Agenda ---------------------------------------------------------------------------
    doc.h(1, "Agenda")
    rows = []
    t = 10 * 60
    for item, title, p, purpose, mins in AGENDA:
        rows.append([item, title, pres(p), purpose, f"{t // 60:02d}:{t % 60:02d}"])
        t += mins
    doc.table(["Item", "Title", "Presented by", "Purpose", "Time"], rows, widths=[1.2, 6.6, 4.4, 2.6, 1.6],
              caption="Agenda", font_size=9,
              facts=[F("alias_use", "Agenda: item 4 'Reserving update' is presented by 'the CFO (Priya Raman)'.",
                       f"the CFO ({ctx.name(cfo)})", "PERSON:P001#role_aliases", where=(4, 2),
                       notes="Agenda row for item 4 (same placement PL-072, agenda part).")])
    doc.p("Papers are presented for the purpose shown. Members are asked to read the papers in advance; presenters will "
          "take them as read and focus on the questions for the Committee.")
    doc.p("Apologies, conflicts of interest and quorum will be confirmed at the start of the meeting.")

    # Item 1-2 ---------------------------------------------------------------------------
    _cover(doc, "1", AGENDA[0][1], "Chair", "For noting", "Opening of the meeting.")
    doc.p("The Chair will welcome members and attendees, note apologies and invite declarations of interest in any item "
          "on the agenda.")
    _cover(doc, "2", AGENDA[1][1], "Chair", "For approval", "The Committee is asked to approve the minutes of the previous "
           "meeting and to note the action log.")
    acts = [("A-01", "Report on the implementation of NISA Circular 2026/04", "P037", "Closed – see item 8"),
            ("A-02", "Confirm the outcome of the reserve parallel run", cfo, "Closed – see item 4"),
            ("A-03", "Wave 1 readiness and go/no-go criteria", "P004", "Closed – see item 5"),
            ("A-04", "Follow-up of the Sentinel model validation findings", "P008", "Open – see item 9"),
            ("A-05", "Closure plan for internal audit finding IA-25-07", cfo, "Closed – see item 4"),
            ("A-06", "Batch fraud sweep incident root cause and permanent fix", "P006", "Open – see item 6"),
            ("A-07", "Review of change capacity across the claims function", "P004", "Open – see item 3")]
    doc.h(2, "2.1 Draft minutes of the previous meeting")
    doc.p("Present: the Chair and members of the Committee. In attendance: " +
          "; ".join(ctx.person(p_) for p_ in ("P003", cfo, "P004", "P005", "P006", "P007")) + "; Company Secretary.")
    for k, topic in enumerate(["Chief Risk Officer's report", "Reserving", "Programme Skerry", "Fraud and NISA Circular 2026/04",
                               "Operational resilience", "Regulatory update", "Any other business"], 1):
        doc.h(3, f"2.1.{k} {topic}")
        doc.ps(pr.paras(["board2", "board"], 2, n=(4, 6)))
    doc.h(2, "2.2 Action log")
    doc.table(["Ref", "Action", "Owner", "Status"], [[a, b, ctx.name(c), d] for a, b, c, d in acts],
              widths=[1.4, 8.4, 3.2, 3.6], caption="Action log", font_size=8.8)
    doc.ps(pr.paras(["board", "board2"], 1))

    # Item 3 CRO ---------------------------------------------------------------------------
    _cover(doc, "3", AGENDA[2][1], ctx.person("P007"), "For discussion",
           "The overall risk profile is broadly stable. Migration execution risk has improved following the successful "
           "Wave 1 cut-over; change capacity remains a concern.")
    doc.ps(pr.paras(["board", "board2", "risk"], 3))
    doc.h(2, "3.1 Principal risks")
    doc.table(["Ref", "Risk", "Owner", "Residual rating", "Trend"],
              [[r, t_, ctx.name(cfo) if o == "CFO" else ctx.name(o), g, tr] for r, t_, o, g, tr in RISKS],
              widths=[1.6, 6.8, 3.4, 2.6, 2.2], caption="Principal risk register (summary)", font_size=8.8)
    doc.ps(pr.paras(["risk", "board2"], 2))
    for r, t_, o, g, tr in RISKS:
        doc.h(3, f"{r} {t_}")
        doc.kv([["Owner", ctx.person(cfo) if o == "CFO" else ctx.person(o)], ["Residual rating", g], ["Trend", tr]],
               widths=(3.6, 13.0), font_size=8.8)
        doc.p(pr.para(["risk", "board2"], n=(4, 6)))
        own = ctx.name(cfo) if o == "CFO" else ctx.name(o)
        doc.table(["Key controls", "Assessment"],
                  [["Policy and standards in place and reviewed annually", "Effective"],
                   ["Management information reviewed by the risk owner monthly", "Effective"],
                   ["Second-line review in the year", "Effective" if g == "Green" else "Partially effective"]],
                  widths=[11.0, 5.6], font_size=8.6)
        doc.table(["Action", "Owner", "Status"],
                  [[f"Refresh the {t_.lower()} risk and control assessment", own, "In progress"],
                   ["Report progress to the next meeting", own, "Planned"]],
                  widths=[9.6, 4.0, 3.0], font_size=8.6)
        doc.p(pr.para(["risk", "risk", "board"], n=(3, 5)))
    heat = FG.matrix_image(CACHE / "fig" / FID / "heatmap.png", title="Principal risks by residual rating",
                           header=["Rating", "Risks"],
                           rows=[[g, ", ".join(r for r, _, _, gg, _ in RISKS if gg == g)] for g in ("Amber", "Green")],
                           col_w=[260, 1500], colours={"Amber": (252, 228, 180), "Green": (210, 236, 210)}, font_size=30)
    doc.figure(heat, "Principal risks by residual rating", width_cm=16.0)
    doc.h(2, "3.2 Key risk indicators")
    kris = [("Reserving", "Overdue Tier-3 reserve reviews", "Green"), ("Reserving", "Unexplained reserve reconciliation breaks", "Green"),
            ("Migration", "Open Severity 1 and 2 defects after cut-over", "Amber"), ("Migration", "Rehearsal reconciliation exceptions", "Green"),
            ("Payments", "Payment instructions rejected or duplicated", "Amber"), ("Payments", "Payment run delays", "Green"),
            ("Fraud", "Referrals not triaged within the standard", "Green"), ("Fraud", "Customer notices issued late", "Green"),
            ("Resilience", "Severity 1 and 2 incidents", "Amber"), ("Resilience", "Batch schedule overruns", "Green"),
            ("Data", "Data subject requests overdue", "Green"), ("Third parties", "Supplier service level breaches", "Green"),
            ("People", "Vacancies in legacy platform roles", "Amber"), ("Change", "Changes outside the release process", "Green")]
    doc.table(["Area", "Indicator", "Status"], [list(k_) for k_ in kris], widths=[3.2, 10.6, 2.8],
              caption="Key risk indicators (status against appetite)", font_size=8.8)
    doc.ps(pr.paras(["risk", "board2"], 2, n=(4, 6)))
    doc.h(2, "3.3 Risk appetite")
    doc.table(["Category", "Appetite statement"],
              [["Insurance risk", "The Society accepts insurance risk within its underwriting and reserving policies."],
               ["Operational risk", "The Society has a low appetite for operational failures that harm customers."],
               ["Conduct risk", "The Society has no appetite for unfair customer outcomes."],
               ["Financial crime", "The Society has no appetite for facilitating fraud or financial crime."],
               ["Change risk", "The Society accepts moderate change risk to deliver its strategy, with strong controls."],
               ["Model risk", "Models are used only within approved purposes and are independently validated."],
               ["Third-party risk", "Material suppliers are subject to due diligence and ongoing oversight."]],
              widths=[3.6, 13.0], caption="Risk appetite statements", font_size=8.8)
    doc.ps(pr.paras(["risk", "board"], 2, n=(4, 6)))
    doc.h(2, "3.4 Risk events since the start of 2025")
    rows = [[i["id"], short_date(i["date"]), i["severity"], " ".join(ctx.a(i["title"]).replace("CICSPRD1", "").split())]
            for i in sorted(W.incidents.values(), key=lambda x: x["date"]) if "2025-01-01" <= str(i["date"]) < "2026-01-01"]
    doc.table(["Event", "Date", "Severity", "Title"], rows, widths=[2.6, 2.4, 1.8, 9.8], caption="Risk events in 2025", font_size=8.4)
    doc.ps(pr.paras(["risk", "board2"], 2, n=(4, 6)))
    doc.h(2, "3.5 Emerging risks")
    doc.ps(pr.paras(["risk", "board"], 3, n=(4, 6)))

    # Item 4 Reserving --------------------------------------------------------------------
    _second_line(doc, pr)
    _cover(doc, "4", AGENDA[3][1], f"the CFO ({ctx.name(cfo)})", "For discussion",
           "Reserving controls have been strengthened during the year. The reserve parallel run completed on schedule "
           "and reserve-engine became the reserving system for migrated UK motor claims at the Wave 1 cut-over.",
           facts=[PF(ctx, "ld29_cfo", f"the CFO ({ctx.name(cfo)})", anchor="Item 4 – Reserving update",
                     notes="Item 4 cover sheet: the reserving update is presented by the CFO, Priya Raman.")])
    fin = W.company["financials"]["fy2025"]
    doc.p(f"{ctx.name(cfo)}, Chief Financial Officer, presents this update on behalf of the Reserving Committee, chaired "
          f"by {ctx.person('P009')}.",
          facts=[F("alias_use", "The Chief Financial Officer in September 2026 is Priya Raman.", f"{ctx.name(cfo)}, Chief Financial Officer",
                   "PERSON:P001#titles")])
    doc.h(2, "4.1 Context")
    doc.p(f"For 2025 the Society reported gross written premium of £{fin['gross_written_premium_gbp_m']:,.1f}m, gross claims "
          f"incurred of £{fin['gross_claims_incurred_gbp_m']:,.1f}m and a combined ratio of {fin['combined_ratio_pct']}%. "
          f"{W.timeline['metrics']['claims_notified']['2026Q2']:,} claims were notified in the second quarter of 2026.",
          facts=[F("general", "FY2025: GWP £2,140.0m, gross claims incurred £1,412.6m, combined ratio 98.4%.",
                   f"combined ratio of {fin['combined_ratio_pct']}%", "ORG:company#financials.fy2025.combined_ratio_pct"),
                 F("general", "53,140 claims were notified in Q2 2026.", f"{W.timeline['metrics']['claims_notified']['2026Q2']:,} claims",
                   "TIMELINE:metrics#claims_notified.2026Q2")])
    doc.ps(pr.paras(["board", "board2"], 1))
    doc.h(2, "4.2 Reserve parallel run")
    prun = W.timeline["programme"]["parallel_run"]
    doc.p(f"The parallel run comparing CLARA with reserve-engine ran from {long_date(prun['from'])} to "
          f"{long_date(prun['to'])}. Differences were investigated daily by the Reserving team and the Reserve & Finance "
          f"squad. The Reserving Committee accepted the results before the Wave 1 go decision.",
          facts=[F("general", "The reserve parallel run ended on 2026-08-28.", long_date(prun["to"]), "TIMELINE:programme#parallel_run")])
    doc.ps(pr.paras(["board2"], 1))
    doc.h(2, "4.3 Tier-3 reserve review cadence")
    r7 = ctx.rule("BR-RSV-007")
    doc.p(f"From {long_date(r7['effective_from'])} Tier-3 reserves are reviewed at least every {r7['parameters']['review_days']} "
          f"days (BR-RSV-007 v{r7['version']}), approved by the Reserving Committee on {long_date('2026-06-09')}. On "
          f"{long_date('2026-07-02')} reserve-engine was found to be still scheduling reviews on the previous cadence "
          f"(INC-2026-0702); the configuration was corrected and the overdue reviews were completed.",
          facts=[F("temporal", "From 2026-07-01 Tier-3 reserves are reviewed every 14 days (BR-RSV-007 v3).",
                   f"at least every {r7['parameters']['review_days']} days (BR-RSV-007 v{r7['version']})", "RULE:BR-RSV-007@v3#parameters.review_days"),
                 F("general", "INC-2026-0702: reserve-engine Tier-3 review cadence mismatch (2026-07-02).", "INC-2026-0702",
                   "INCIDENT:INC-2026-0702")])
    doc.ps(pr.paras(["board2", "risk"], 1))
    doc.h(2, "4.4 Internal audit finding IA-25-07")
    doc.p("Internal audit finding IA-25-07 reported that the year-end revaluation program CLRGL090 changes reserves "
          "without recording reserve movements. The reserving design review of 5 March 2026 agreed that reserve-engine "
          "will record currency revaluations as movements, and ADR-028 replaces CLRGL090 with the reserve-engine "
          "revaluation run from Wave 2. CLRGL090 itself remains unchanged until then; a compensating reconciliation is "
          "performed at each year-end.",
          facts=[F("general", "IA-25-07 is closed in the target: reserve-engine records revaluations as movements (DEC-005, ADR-028).",
                   "ADR-028 replaces CLRGL090 with the reserve-engine revaluation run from Wave 2", "ADR:ADR-028")])
    doc.h(2, "4.5 Year-end revaluation incident")
    inc = W.incidents["INC-2026-0104"]
    doc.p(f"{inc['id']} ({long_date(inc['date'])}): {inc['title']}. Root cause: {inc['root_cause']}")
    doc.ps(pr.paras(["board2"], 1))
    doc.h(2, "4.6 Reserving decisions in 2026")
    rows = [[d_, short_date(W.decisions[d_]["date"]), W.decisions[d_]["statement"]] for d_ in ("DEC-005", "DEC-006", "DEC-008", "DEC-018")]
    doc.table(["Decision", "Date", "Statement"], rows, widths=[2.2, 2.4, 12.0], caption="Reserving-related decisions", font_size=8.6)
    doc.h(2, "4.7 Reserving rules changed in 2026")
    rows = []
    for rid, r in W.rules.items():
        if not rid.startswith("BR-RSV-"):
            continue
        v = ctx.rule(rid)
        if v and v.get("effective_from") and "2026-01-01" <= v["effective_from"] <= date and ctx.ok(f"RULE:{rid}@v{v['version']}", "text"):
            rows.append([f"{rid} v{v['version']}", r["title"], short_date(v["effective_from"]), v["text"]])
    if rows:
        doc.table(["Rule", "Title", "Effective", "Text"], rows, widths=[2.6, 4.0, 2.4, 7.6], font_size=8.4)
    doc.h(2, "4.8 Reinsurance")
    inc = W.incidents["INC-2026-0731"]
    doc.p(f"Large losses continue to be notified to reinsurers under BR-RSV-011. {inc['id']} ({long_date(inc['date'])}): "
          f"{inc['title']}; root cause: {inc['root_cause']}")
    doc.ps(pr.paras(["ri2", "board2"], 2))
    doc.h(2, "4.9 Outlook to year-end")
    doc.ps(pr.paras(["board2", "risk"], 2, n=(4, 6)))
    doc.h(2, "4.10 Questions for the Committee")
    doc.bullets(["Is the Committee satisfied with the evidence from the parallel run?",
                 "Does the Committee agree that the compensating reconciliation is adequate until Wave 2?",
                 "Are there further assurances the Committee would like before the 2026 year-end?"])

    # Item 5 Programme --------------------------------------------------------------------
    _second_line(doc, pr)
    _cover(doc, "5", AGENDA[4][1], ctx.person("P004"), "For discussion",
           "Waves 0 and 1 are complete. Lessons from the Wave 1 cut-over are being applied to Wave 2 planning.")
    rows = []
    for w in W.waves.values():
        if w["status"] == "complete" and str(w["date"]) <= date:
            rows.append([w["name"], w["scope"], short_date(w["date"]), "Complete", f"{w['rehearsals']} rehearsals"])
        elif w["id"] == "MW-2":
            rows.append([w["name"], w["scope"], "Early 2027 (date to be confirmed)", "Planning", "Rehearsals planned"])
    doc.table(["Wave", "Scope", "Cut-over", "Status", "Rehearsals"], rows, widths=[4.0, 5.2, 3.0, 2.0, 2.4],
              caption="Migration waves", font_size=8.4,
              facts=[F("general", "Wave 1 (UK motor) cut over on 2026-09-14.", "14 Sep 2026", "WAVE:MW-1#date")])
    spend = W.timeline["metrics"]["programme_spend_cumulative_gbp_m"]["2026Q2"]
    doc.p(f"Cumulative programme spend at the end of June 2026 was £{spend}m against the approved budget of "
          f"£{W.timeline['metrics']['programme_budget_gbp_m']}m.",
          facts=[F("general", "Programme spend to 2026-06-30: £26.8m of £48.6m.", f"£{spend}m", "TIMELINE:metrics#programme_spend_cumulative_gbp_m.2026Q2")])
    inc = W.incidents["INC-2026-0914"]
    doc.h(2, "5.1 Wave 1 cut-over")
    doc.p(f"The go decision for Wave 1 was taken on {long_date('2026-09-11')}, with a freeze from 11 September 18:00 to "
          f"14 September 06:00. During the cut-over, {inc['id']} ({inc['title'].lower()}) occurred; ADR-021, accepted on "
          f"{long_date('2026-09-16')}, requires idempotency keys for all payment instructions.")
    doc.ps(pr.paras(["board2", "risk"], 2))
    doc.h(2, "5.2 Milestones")
    rows = [[e["id"], short_date(e["date"]), ctx.a(e["summary"])] for e in W.events.values() if "2025-01-01" <= str(e["date"]) <= date and e.get("kind") not in ("people", "person", "org")]
    doc.table(["Event", "Date", "Milestone"], rows, widths=[2.0, 2.6, 12.0], caption="Programme and organisational milestones",
              font_size=8.4)
    doc.h(2, "5.3 Programme governance and organisation")
    com3 = W.committees["COM-03"]
    doc.p(f"The {com3['name']} is chaired by {ctx.person('P004')} and meets {com3['cadence']}.")
    rows = [[ctx.name(p_), ctx.title(p_), "Corvane" if not W.people[p_]["location"].startswith("EXT") else "IBM Consulting"]
            for p_ in ("P004", "P017", "P032", "P018", "P051", "P047", "P048", "P049")]
    doc.table(["Name", "Title", "Organisation"], rows, widths=[4.4, 7.6, 4.6], caption="Programme leadership", font_size=8.8)
    doc.h(2, "5.4 Programme decisions")
    rows = [[d_["id"], short_date(d_["date"]), d_["statement"]] for d_ in W.decisions.values()
            if "2026-01-01" <= str(d_["date"]) <= date and d_["id"] in ("DEC-009", "DEC-018", "DEC-019")]
    doc.table(["Decision", "Date", "Statement"], rows, widths=[2.2, 2.4, 12.0], font_size=8.6)
    doc.h(2, "5.5 Wave 2 risks")
    doc.table(["Risk", "Mitigation"],
              [["Larger and more varied scope than earlier waves", "Additional rehearsal and staged readiness reviews"],
               ["Nordic currencies and products", "Dedicated Nordic test scenarios and business verification"],
               ["Retirement of the subrogation tracker", "Recovery cases migrated and reconciled before retirement"],
               ["Concurrent regulatory change", "Change freeze around the cut-over"],
               ["Payment integrity", "Idempotency keys (ADR-021) and payment reconciliation"]],
              widths=[6.6, 10.0], font_size=8.8)
    doc.ps(pr.paras(["board2", "risk", "migration"], 3, n=(4, 6)))

    # Item 6 Fraud ---------------------------------------------------------------------------
    _second_line(doc, pr)
    _cover(doc, "6", AGENDA[5][1], ctx.person("P008"), "For noting",
           "NISA Circular 2026/04 has been implemented. The Fraud Rules Workshop of 17 September 2026 agreed a lower "
           "referral threshold for Tier-3 claims from 1 October 2026.")
    q2 = W.timeline["metrics"]["fraud_referrals_count"]["2026Q2"]
    doc.p(f"In 2025 Counter-Fraud & SIU received {fin['fraud_referrals']:,} referrals, confirmed {fin['confirmed_fraud_cases']:,} "
          f"cases of fraud and recorded savings of £{fin['fraud_savings_gbp_m']}m. {q2:,} referrals were made in the second "
          f"quarter of 2026.",
          facts=[F("general", "1,488 fraud referrals were made in Q2 2026.", f"{q2:,} referrals were made", "TIMELINE:metrics#fraud_referrals_count.2026Q2")])
    rows = []
    for did in ("DEC-007", "DEC-014", "DEC-015", "DEC-016"):
        d_ = W.decisions[did]
        rows.append([did, short_date(d_["date"]), d_["statement"]])
    doc.table(["Decision", "Date", "Statement"], rows, widths=[2.2, 2.4, 12.0], caption="Fraud rule decisions in 2026",
              font_size=8.4,
              facts=[F("needle", "DEC-014: from 2026-10-01 refer Tier-3 claims at a Sentinel score of 60 or more.",
                       "refer Tier-3 claims to SIU at a Sentinel score of 60 or more", "DECISION:DEC-014", where=(2, 2))])
    inc = W.incidents["INC-2026-0518"]
    doc.h(2, "6.1 Batch fraud sweep incident")
    doc.p(f"{inc['id']} ({long_date(inc['date'])}): {inc['title']}. {inc['impact']} Root cause: {inc['root_cause']} A daily "
          f"Compliance query identifies any unreferred claims until the permanent fix is released.")
    doc.ps(pr.paras(["board2", "model2"], 2))
    doc.h(2, "6.2 Fraud rules in force")
    rows = []
    for rid in ("BR-FRD-031", "BR-FRD-032", "BR-FRD-033", "BR-FRD-034", "BR-FRD-035", "BR-FRD-036"):
        v = ctx.rule(rid)
        if not v or not ctx.ok(f"RULE:{rid}@v{v['version']}", "text"):
            continue
        rows.append([f"{rid} v{v['version']}", W.rules[rid]["title"], v["text"]])
    doc.table(["Rule", "Title", "Text"], rows, widths=[2.8, 4.6, 9.2], caption="Fraud referral rules at the date of this pack",
              font_size=8.4)
    doc.ps(pr.paras(["board2", "risk"], 2, n=(4, 6)))

    # Item 7 Resilience ---------------------------------------------------------------------
    _second_line(doc, pr)
    _cover(doc, "7", AGENDA[6][1], ctx.person("P006"), "For noting",
           "Eleven incidents affecting claims systems have been recorded in 2026 to date; three were Severity 2.")
    rows = []
    for i in W.incidents.values():
        if "2026-01-01" <= str(i["date"]) < date:
            rows.append([i["id"], short_date(i["date"]), i["severity"], ctx.a(i["title"])])
    doc.table(["Incident", "Date", "Severity", "Title"], rows, widths=[2.6, 2.4, 1.8, 9.8], caption="Incidents in 2026",
              font_size=8.6)
    doc.ps(pr.paras(["board2", "risk", "ops"], 2))
    c25 = W.circulars["CIRC-2025-02"]
    doc.h(2, "7.1 Operational resilience requirements")
    doc.p(f"{c25['ref']} ({c25['title']}), effective {long_date(c25['effective'])}, requires: " +
          " ".join(r["text"] for r in c25["requirements"]))
    doc.ps(pr.paras(["board2"], 1))

    # Item 8 Regulatory ---------------------------------------------------------------------
    _second_line(doc, pr)
    _cover(doc, "8", AGENDA[7][1], ctx.person("P037"), "For noting", "Regulatory returns were submitted on time. The first "
           "quarterly NISA-FR1 return was submitted in July 2026.")
    rows = [[r["id"], r.get("name") or r.get("title"), r.get("frequency", "—"), r.get("due", "—")] for r in W.reports.values()]
    doc.table(["Return", "Name", "Frequency", "Due"], rows, widths=[2.4, 7.4, 2.6, 4.2], caption="Regulatory returns", font_size=8.8)
    rows = [[c["ref"], c["title"], short_date(c["effective"])] for c in W.circulars.values() if str(c["published"]) <= date]
    doc.table(["Circular", "Title", "Effective"], rows, widths=[4.0, 9.0, 3.6], caption="Recent NISA circulars", font_size=8.8)
    for c in W.circulars.values():
        if str(c["published"]) > date or c["id"] == "CIRC-2026-04":
            continue
        doc.h(2, f"{c['ref']} – {c['title']}")
        doc.table(["Paragraph", "Requirement"], [[f"§{r['para']}", r["text"]] for r in c["requirements"]], widths=[2.4, 14.2], font_size=8.6)
        doc.p(pr.para(["board2", "board"], n=(3, 4)))
    c26 = W.circulars["CIRC-2026-04"]
    doc.h(2, f"{c26['ref']} – {c26['title']}")
    doc.table(["Paragraph", "Requirement"], [[f"§{r['para']}", r["text"]] for r in c26["requirements"]], widths=[2.4, 14.2], font_size=8.6)
    doc.ps(pr.paras(["board2", "board"], 2))

    # Item 9 Model risk --------------------------------------------------------------------
    snt = W.systems["SYS03"]
    _second_line(doc, pr)
    _cover(doc, "9", AGENDA[8][1], ctx.person("P007"), "For noting",
           f"The Sentinel fraud scoring model {snt['model_version']} was independently validated on "
           f"{long_date(snt['model_validation']['date'])} and found stable; recalibration is due annually.")
    doc.ps(pr.paras(["model2", "board2"], 2))

    # Item 10 Third parties -----------------------------------------------------------------
    _second_line(doc, pr)
    _cover(doc, "10", AGENDA[9][1], ctx.person("P004"), "For noting", "Material suppliers are performing in line with contract.")
    rows = []
    for vid, v in W.vendors.items():
        if v.get("panel_to") or vid in ("VEN-12", "VEN-13"):
            continue
        rows.append([v["name"], v["location"], v["role"]])
    doc.table(["Supplier", "Location", "Service"], rows, widths=[5.0, 3.0, 8.6], caption="Material suppliers", font_size=8.8)
    doc.ps(pr.paras(["board2", "vendor"], 2))

    # Item 11 -------------------------------------------------------------------------------
    _second_line(doc, pr)
    _cover(doc, "11", AGENDA[10][1], "Chair", "For noting", "Forward plan of Committee business.")
    doc.table(["Meeting", "Planned items"],
              [["Next meeting", "Year-end reserving approach; Wave 2 readiness; risk appetite review"],
               ["Following meeting", "Annual model risk report; operational resilience self-assessment"]],
              widths=[4.0, 12.6], font_size=9)

    # Appendices -----------------------------------------------------------------------------
    doc.h(1, "Appendix A – Incident detail", page_break=True)
    for i in W.incidents.values():
        if not ("2026-01-01" <= str(i["date"]) < date):
            continue
        doc.h(2, f"{i['id']} – {ctx.a(i['title'])}")
        omit = INCIDENT_OMIT.get(i["id"], ())
        doc.kv([["Date", long_date(i["date"])], ["Severity", i["severity"]],
                ["Impact", "See item 4" if "impact" in omit else (i.get("impact") or "—")],
                ["Root cause", "Configuration error; corrected" if "root_cause" in omit else (i.get("root_cause") or "—")],
                ["Owner", ctx.person(i["owner"]) if i.get("owner") else "—"],
                ["Follow-up", ", ".join(i.get("fix_tickets") or []) or "—"]], widths=(3.0, 13.6), font_size=8.6)
    doc.h(1, "Appendix B – Architecture decisions in 2026", page_break=True)
    rows = [[a["id"], short_date(a["date"]), a["status"], a["title"]] for a in W.adrs.values() if "2026-01-01" <= str(a["date"]) <= date]
    doc.table(["ADR", "Date", "Status", "Title"], rows, widths=[1.8, 2.4, 2.2, 10.2], caption="Architecture decisions", font_size=8.6)
    doc.h(1, "Appendix C – Programme Skerry tickets of note", page_break=True)
    doc.p("Tickets referenced in programme and risk reporting, with their status at the date of this pack.")
    rows = []
    for tid, t in sorted(W.tickets.items(), key=lambda x: int(x[0].split("-")[1])):
        if str(t.get("created", "9999")) > date or tid == "CHUB-262":
            continue
        a = t.get("assignee")
        rows.append([tid, ctx.a(t.get("summary", "")), t.get("component") or "—", _ticket_status(t, date),
                     ctx.name(a) if a and a in W.people and ctx.employed(a) else "—"])
    doc.table(["Ticket", "Summary", "Component", "Status", "Assignee"], rows, widths=[2.0, 8.0, 2.6, 2.0, 2.4],
              caption="Tickets of note", font_size=7.8)
    doc.h(1, "Appendix D – Claims process service levels", page_break=True)
    rows = []
    for sid, st in W.steps.items():
        own = W.owner_of_process(st["stage"], date)
        rows.append([sid, st["name"], ctx.name(own) if own else "—", st["sla"]["text"] if "(BR-" not in st["sla"]["text"] or
                     (ctx.rule(st["sla"]["text"].split("(")[1].split(" ")[0]) or {}).get("version") == int(st["sla"]["text"].split(" v")[-1].rstrip(")")) else st["sla"]["text"].split("(")[0].strip()])
    doc.table(["Step", "Name", "Stage owner", "Service level"], rows, widths=[2.4, 5.0, 3.4, 5.8],
              caption="Process steps and service levels", font_size=8.2)
    doc.h(1, "Appendix E – Claims Hub services", page_break=True)
    rows = []
    for name, sv in W.services.items():
        o = W.service_owner(name, date)
        rows.append([ctx.svc(name), ctx.a(sv["description"]).split(" (")[0], ctx.team(o["team"]) if o else "—"])
    doc.table(["Service", "Responsibility", "Owning squad"], rows, widths=[3.8, 8.8, 4.0], caption="Claims Hub services", font_size=8.4)
    doc.h(2, "Interfaces in the migration scope")
    rows = []
    for i in W.interfaces.values():
        if i["id"] == "CLX-IF-042":
            continue
        status = "Live" if str(i["since"]) <= date else "Planned"
        rows.append([i["id"], ctx.a(i["name"]), ctx.sys(i["source_system"]), ctx.sys(i["target_system"]), status])
    doc.table(["ID", "Name", "From", "To", "Status"], rows, widths=[2.2, 5.8, 3.4, 3.4, 1.8], font_size=7.8)
    doc.h(1, "Appendix F – Regulatory return history", page_break=True)
    rows = []
    for r in W.reports.values():
        for ev in r.get("late_events") or []:
            rows.append([r["id"], ev["period"], short_date(ev["due"]), short_date(ev["submitted"]), ev.get("incident", "—"), ev.get("note", "")])
    if rows:
        doc.table(["Return", "Period", "Due", "Submitted", "Incident", "Note"], rows, widths=[2.2, 1.8, 2.4, 2.4, 2.8, 5.0], font_size=8.4,
                  caption="Late submissions since 2025")
    doc.p("All other regulatory returns since the start of 2025 were submitted by their due dates.")
    doc.ps(pr.paras(["board2"], 2))
    doc.h(1, "Appendix G – Committee terms of reference (extract)")
    doc.bullets(["Advise the Board on the Society's overall risk appetite, tolerance and strategy.",
                 "Oversee the risk management framework and the effectiveness of the second line.",
                 "Review the principal risks and the actions taken to manage them.",
                 "Review the reserving approach and the adequacy of reserving controls, with the Audit Committee.",
                 "Oversee model risk and the use of material models.",
                 "Review the risks arising from major change programmes.",
                 "Review operational resilience, including impact tolerances for important business services.",
                 "Receive reports on regulatory developments and the Society's relationship with its regulator."])
    doc.ps(pr.paras(["board2", "governance"], 2))
    doc.h(1, "Appendix H – Executive Committee and key roles", page_break=True)
    rows = []
    for pid, pp in W.people.items():
        if not ctx.employed(pid) or pp["location"].startswith("EXT") or W.team_of(pid, date) not in ("T01", "T02", "T08", "T11", "T12", "T13", "T15", "T17", "T18", "T19", "T20", "T21"):
            continue
        rows.append([ctx.name(pid), ctx.title(pid), ctx.team(W.team_of(pid, date))])
    doc.table(["Name", "Title", "Team"], rows, widths=[4.4, 7.4, 4.8], caption="Key roles", font_size=8.4)
    doc.h(1, "Appendix I – Decisions log", page_break=True)
    rows = [[d_["id"], short_date(d_["date"]), d_["statement"]] for d_ in sorted(W.decisions.values(), key=lambda x: x["date"])
            if str(d_["date"]) <= date and d_["id"] != "DEC-013"]
    doc.table(["Decision", "Date", "Statement"], rows, widths=[2.2, 2.4, 12.0], caption="Decisions 2025–2026", font_size=8.2)
    doc.h(1, "Appendix J – Architecture decisions", page_break=True)
    rows = [[a["id"], short_date(a["date"]), a["status"], a["title"]] for a in sorted(W.adrs.values(), key=lambda x: x["id"])
            if str(a["date"]) <= date]
    doc.table(["ADR", "Date", "Status", "Title"], rows, widths=[1.8, 2.4, 2.2, 10.2], caption="All architecture decisions to date",
              font_size=8.2)
    doc.h(1, "Appendix K – Rules changed in 2026", page_break=True)
    rows = []
    for rid, r in W.rules.items():
        for v in r["versions"]:
            ef = v.get("effective_from")
            if not ef or not ("2026-01-01" <= ef <= date):
                continue
            if not (ctx.ok(f"RULE:{rid}@v{v['version']}", "text") and ctx.ok(f"RULE:{rid}@v{v['version']}", "parameters")):
                continue
            rows.append([f"{rid} v{v['version']}", r["title"], short_date(ef), v["text"]])
    doc.table(["Rule", "Title", "Effective", "Text"], rows, widths=[2.6, 4.0, 2.4, 7.6], caption="Rule versions effective in 2026",
              font_size=8.0)
    doc.h(1, "Appendix L – Products and migration waves", page_break=True)
    wave_of = {}
    for w in W.waves.values():
        for code in [x.strip() for x in w["scope"].replace("All Danish products", "").replace("(", ",").replace(")", ",").split(",")]:
            if code.startswith("PRD-"):
                wave_of[code] = w["name"]
    rows = [[p_["name"], p_["id"], p_["line"], wave_of.get(p_["id"], "—")] for p_ in W.products.values()]
    doc.table(["Product", "ID", "Line", "Migration wave"], rows, widths=[5.6, 3.4, 3.6, 4.0], caption="Products by migration wave",
              font_size=8.6)
    doc.ps(pr.paras(["board2", "migration"], 2))
    doc.h(1, "Appendix M – Glossary")
    doc.table(["Term", "Meaning"], [[t_, ctx.a(m)] for t_, m in C.glossary_terms(["G-003", "G-008", "G-012", "G-015", "G-016", "G-019", "G-020"])],
              widths=[4.0, 12.6], font_size=8.8)
    return doc


def _second_line(doc, pr):
    doc.h(3, "Second-line opinion")
    doc.p(pr.para(["board2", "risk"], n=(3, 5)))
    doc.h(3, "Recommendation")
    doc.p(pr.para(["board2", "board"], n=(2, 3)))


def _ticket_status(t: dict, date: str) -> str:
    st = None
    for h in t.get("status_history") or []:
        if str(h.get("from")) <= date:
            st = h["status"]
    return st or t.get("status", "—")


def _cover(doc, item, title, presenter, purpose, summary, facts=None):
    doc.h(1, f"Item {item} – {title}", page_break=True)
    doc.kv([["Paper", f"BRC-2026-09-{int(item):02d}"], ["Presented by", presenter], ["Purpose", purpose],
            ["Summary", summary]], widths=(3.4, 13.2), font_size=9.4, facts=facts)


def post_check(doc, texts):
    from harness import extract as X
    out = []
    for needle in ("186,400", "31.2m", "97.8%", "0.87", "0.06", "41%", "412 ", "12 partitions"):
        pages = [i + 1 for i, t in enumerate(texts) if X.match(needle, t)]
        if pages:
            out.append(f"check: {needle!r} on pages {pages[:6]}")
    cfo = [i + 1 for i, t in enumerate(texts) if X.match("the CFO (Priya Raman)", t)]
    out.append(f"INFO 'the CFO (Priya Raman)' pages {cfo}; total {len(texts)}")
    return out

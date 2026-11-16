"""Filler markdown (TX039, TX041, TX042, TX045-TX060): status reports, weekly updates, team notes,
a glossary page and onboarding notes.

Filler states NO new world facts. Where it mentions the world it restates facts that were true on
the document date (each one recorded in the manifest as a non-exclusive 'general'/'temporal'
fact and checked with W.may_state). Everything else is procedural colour from phrase banks.
"""
from __future__ import annotations

import dataclasses

from generators.common import util

from . import phrases as PH
from .core import W, Doc, person, pick, picks, short_date, long_date, md_table, kv_table, D
from .minutes import h, bullet, para


@dataclasses.dataclass
class C:
    """A context sentence that restates a world fact (recorded as a manifest fact)."""
    text: str
    needle: str
    statement: str
    world_ref: str
    kind: str = "general"


MILESTONES = [
    # date, label, known from, world ref
    ("2025-01-13", "IBM engagement start and programme kick-off", "2024-11-18", "EVENT:EV-012"),
    ("2025-11-03", "Claims Hub MVP live (FNOL and triage, digital channels)", "2025-02-01", "EVENT:EV-020"),
    ("2025-12-12", "CLX-IF-049 reserve movement bridge live", "2025-12-12", "EVENT:EV-023"),
    ("2026-03-02", "Reserve parallel run starts (CLARA vs reserve-engine)", "2026-02-16", "EVENT:EV-026"),
    ("2026-04-01", "NISA Circular 2026/04 effective", "2025-11-20", "EVENT:EV-027"),
    ("2026-06-01", "Wave 0 – Denmark cut-over", "2026-02-01", "EVENT:EV-028"),
    ("2026-08-28", "Reserve parallel run ends", "2026-02-16", "EVENT:EV-031"),
    ("2026-09-14", "Wave 1 – UK motor cut-over", "2026-03-01", "EVENT:EV-032"),
    ("2026-12-31", "SUBTRAK retirement target", "2025-09-03", "EVENT:EV-037"),
    ("2027-02-15", "Wave 2 cut-over", "2026-10-08", "EVENT:EV-038"),
    ("2027-09-30", "CLARA decommission target", "2025-02-10", "EVENT:EV-039"),
]

WORKSTREAMS = [
    # name, lead pid, active from
    ("Data migration", "P051", "2025-01-13"),
    ("Integration", "P031", "2025-01-13"),
    ("Intake & Triage squad", "P040", "2025-02-03"),
    ("Reserve & Finance squad", "P041", "2025-02-03"),
    ("Fraud & Settlement squad", "P042", "2025-02-03"),
    ("Recoveries & Documents squad", "P043", "2026-11-01"),
    ("Business readiness", "P017", "2025-01-13"),
    ("Legacy platforms (CLARA)", "P016", "2025-01-13"),
    ("Architecture", "P049", "2025-01-13"),
]

WS_COMMENTS = [
    "Delivery against plan; no escalations.",
    "Sprint goals met; minor carry-over into next sprint.",
    "Waiting on SME availability for two workshops; being managed within the workstream.",
    "Test evidence being collated for sign-off.",
    "Dependencies reviewed with neighbouring squads; no date impact.",
    "Small number of defects in triage; none blocking.",
    "Knowledge transfer continuing with Corvane staff.",
    "Environment contention earlier in the week, now resolved.",
    "Runbook updates in progress following the last walkthrough.",
    "Plan re-baselined within the workstream; milestones unchanged.",
]


def _r(fid: str):
    return util.rng(f"{fid}:filler")


def new_doc(fid: str, slug: str, width=None) -> Doc:
    return Doc(fid, f"{fid}_{slug}.md", width=width)


def put(doc: Doc, c: C, as_bullet: bool = False):
    s = bullet(doc, c.text) if as_bullet else para(doc, c.text)
    doc.fact(s, c.needle, c.statement, c.kind, c.world_ref)
    return s


def key_dates(doc: Doc, d, window_back_days: int = 150, wave2_tbc: bool = True):
    d = D(d)
    rows = []
    for ds, label, known, ref in MILESTONES:
        if D(known) > d:
            if ds == "2027-02-15" and wave2_tbc:
                rows.append([label, "To be confirmed by the Steering Committee", "Planning"])
            continue
        md = D(ds)
        if md <= d:
            if (d - md).days > window_back_days:
                continue
            rows.append([label, short_date(md), "Complete"])
        else:
            rows.append([label, short_date(md), "Planned"])
    h(doc, 2, "Key dates")
    md_table(doc, ["Milestone", "Date", "Status"], rows)


def workstream_table(doc: Doc, r, d):
    d = D(d)
    rows = []
    for name, pid, frm in WORKSTREAMS:
        if D(frm) > d:
            continue
        st = pick(r, PH.STATUS_WORDS)
        pp = person(pid, d)
        lead = pp.name + (" (IBM)" if pp.employer == "ORG-IBM" else "")
        rows.append([name, lead, f"{PH.RAG[st]} – {st}", pick(r, WS_COMMENTS)])
    h(doc, 2, "Workstream status")
    md_table(doc, ["Workstream", "Lead", "Status", "Commentary"], rows)


def risks(doc: Doc, r, d, k=3):
    h(doc, 2, "Risks and issues")
    owners = ["P048", "P017", "P016", "P051", "P049"]
    rows = []
    for i, (desc, mit) in enumerate(picks(r, PH.RISK_ITEMS, k), 1):
        rows.append([f"R{i:02d}", desc, mit, person(pick(r, owners), d).name])
    md_table(doc, ["#", "Description", "Mitigation", "Owner"], rows)


def status_report(fid, slug, d, title, period_label, context, monthly=False, extra=None, width=None):
    r = _r(fid)
    doc = new_doc(fid, slug, width)
    ak = person("P048", d)
    doc.line(f"# {title}")
    doc.blank()
    overall = pick(r, ["On track", "On track", "Watch"])
    kv_table(doc, [
        ("Report period", period_label),
        ("Prepared by", f"{ak.name}, {ak.title} (PMO)"),
        ("Distribution", "Steering Committee members; workstream leads; PMO"),
        ("Overall status", f"{PH.RAG[overall]} – {overall}"),
        ("Classification", "Internal"),
    ])
    h(doc, 2, "Summary")
    for c in context:
        put(doc, c)
    para(doc, pick(r, [
        "Overall delivery remains in line with the plan; points needing attention are listed under risks and issues.",
        "No new escalations this period. Workstream detail follows.",
        "The programme continues to track to plan, with the items below being actively managed.",
    ]))
    workstream_table(doc, r, d)
    h(doc, 2, "Progress this period" if monthly else "Progress this week")
    for t in picks(r, PH.PROGRESS_ITEMS, 7 if monthly else 5):
        bullet(doc, t)
    h(doc, 2, "Planned next period" if monthly else "Planned next week")
    for t in picks(r, PH.NEXT_ITEMS, 5 if monthly else 4):
        bullet(doc, t)
    key_dates(doc, d)
    risks(doc, r, d, 4 if monthly else 3)
    if extra:
        extra(doc, r, d)
    h(doc, 2, "Decisions needed")
    para(doc, pick(r, ["None this week.", "No decisions are needed from the Steering Committee this period.",
                       "None – items above are for information."]))
    return doc


def team_notes(fid, slug, d, author, title, team_label, context, sections=(), width=None):
    r = _r(fid)
    doc = new_doc(fid, slug, width)
    a = person(author, d)
    doc.line(f"# {title}")
    doc.blank()
    kv_table(doc, [
        ("Date", long_date(d)),
        ("Team", team_label),
        ("Notes by", f"{a.name}, {a.title}"),
    ])
    h(doc, 2, "Updates")
    for c in context:
        put(doc, c, as_bullet=True)
    for t in picks(r, PH.TEAM_WORK_ITEMS, 3):
        bullet(doc, t)
    h(doc, 2, "Work in progress")
    for t in picks(r, PH.TEAM_WIP, 3):
        bullet(doc, t)
    for name, items in sections:
        h(doc, 2, name)
        for t in items:
            if isinstance(t, C):
                put(doc, t, as_bullet=True)
            else:
                bullet(doc, t)
    h(doc, 2, "Questions raised")
    for q, a in picks(r, PH.TEAM_QA, 2):
        bullet(doc, f"Q: {q} A: {a}")
    h(doc, 2, "Housekeeping")
    for t in picks(r, PH.TEAM_NOTE_ITEMS, 4):
        bullet(doc, t)
    h(doc, 2, "Next notes")
    para(doc, pick(r, ["Same time next week.", "Next notes after the fortnightly team meeting.",
                       "Next update in two weeks unless something urgent comes up."]))
    return doc


# ---------------------------------------------------------------------------------------------
# Individual filler files
# ---------------------------------------------------------------------------------------------

def tx039():
    d = "2026-10-23"
    ctx = [
        C("The Wave 2 cut-over date is confirmed as 15 February 2027, with the freeze from 18:00 on 12 February to "
          "06:00 on 15 February.", "Wave 2 cut-over date is confirmed as 15 February 2027",
          "Wave 2 cut-over is confirmed for 2027-02-15 (freeze 2027-02-12 18:00 to 2027-02-15 06:00).", "WAVE:MW-2#freeze"),
        C("The £1.8m contingency drawdown for Wave 2 was approved by the CFO on 9 October.",
          "£1.8m contingency drawdown for Wave 2 was approved by the CFO",
          "The £1.8m Wave 2 contingency drawdown was approved by the CFO (Priya Raman).", "DECISION:DEC-010"),
        C("CHUB-298 (CLRFR040 batch sweep fix) moved into progress on 19 October; the daily Compliance query "
          "remains in place until it is released.", "CHUB-298 (CLRFR040 batch sweep fix) moved into progress on 19 October",
          "CHUB-298 moved to In Progress on 2026-10-19.", "TICKET:CHUB-298#status_history", "temporal"),
    ]
    return status_report("TX039", "weekly_status_2026_10_23", d, "Programme Skerry – Weekly Status Report",
                         "Week ending Friday 23 October 2026", ctx)


def tx046():
    d = "2026-06-05"
    ctx = [
        C("Wave 0 (Denmark) cut over on Monday 1 June 2026; hypercare is running with the Copenhagen team.",
          "Wave 0 (Denmark) cut over on Monday 1 June 2026", "Wave 0 (Denmark) cut over on 2026-06-01.", "WAVE:MW-0#date"),
        C("The reserve parallel run between CLARA and reserve-engine continues; it started on 2 March 2026.",
          "it started on 2 March 2026", "The reserve parallel run started on 2026-03-02.", "EVENT:EV-026"),
    ]
    return status_report("TX046", "weekly_status_2026_06_05", d, "Programme Skerry – Weekly Status Report",
                         "Week ending Friday 5 June 2026", ctx, width=110)


def tx059():
    d = "2025-11-07"
    ctx = [
        C("The Claims Hub MVP went live on Monday 3 November 2025, covering FNOL and triage for the digital channels.",
          "Claims Hub MVP went live on Monday 3 November 2025",
          "Claims Hub MVP went live on 2025-11-03 (FNOL and triage, digital channels).", "EVENT:EV-020"),
        C("DOCSTOR was renamed Evidence Vault on the same day.", "DOCSTOR was renamed Evidence Vault",
          "DOCSTOR was renamed Evidence Vault on 2025-11-03.", "SYSTEM:SYS05#renames", "temporal"),
        C("Hypercare for the MVP runs daily with the Intake & Triage squad (lead Sofie Bak).",
          "Intake & Triage squad (lead Sofie Bak)", "Sofie Bak leads the Hub Squad – Intake & Triage.",
          "TEAM:T27#lead_history"),
    ]
    return status_report("TX059", "weekly_status_2025_11_07", d, "Programme Skerry – Weekly Status Report",
                         "Week ending Friday 7 November 2025", ctx)


def tx053():
    d = "2026-06-03"
    ctx = [
        C("NISA Circular 2026/04 took effect on 1 April 2026; the fraud rules approved by the Claims Fraud Forum on "
          "12 March are live in CLARA and Claims Hub.", "NISA Circular 2026/04 took effect on 1 April 2026",
          "NISA Circular 2026/04 took effect on 2026-04-01.", "CIRCULAR:CIRC-2026-04#effective"),
        C("INC-2026-0518 (CLRFR040 batch sweep, found 12 May) is mitigated by a daily Compliance query; the "
          "permanent fix is CHUB-298.", "INC-2026-0518 (CLRFR040 batch sweep, found 12 May) is mitigated by a daily Compliance query",
          "INC-2026-0518 was mitigated by a daily Compliance query; permanent fix CHUB-298.",
          "INCIDENT:INC-2026-0518#workaround"),
        C("Wave 0 (Denmark) cut over on 1 June 2026, at the start of the next reporting period.",
          "Wave 0 (Denmark) cut over on 1 June 2026", "Wave 0 (Denmark) cut over on 2026-06-01.", "WAVE:MW-0#date"),
        C("The Reserving Committee meets on 9 June to consider the 14-day Tier-3 review cadence proposed at the "
          "reserving design review.", "meets on 9 June to consider the 14-day Tier-3 review cadence",
          "The Reserving Committee of 2026-06-09 considered the proposed 14-day Tier-3 review cadence.",
          "MEETING:MTG-006#date"),
    ]

    def extra(doc, r, dd):
        h(doc, 2, "Regulatory and compliance")
        bullet(doc, "Circular 2026/04 implementation evidence is held by Compliance.")
        bullet(doc, "Regulatory Reporting is planning the first NISA-FR1 return (Q2 2026) with Compliance.")
    return status_report("TX053", "monthly_status_2026_05", d, "Programme Skerry – Monthly Status Report: May 2026",
                         "1–31 May 2026 (issued 3 June 2026)", ctx, monthly=True, extra=extra, width=100)


def tx057():
    d = "2026-09-04"
    ctx = [
        C("The reserve parallel run ended on 28 August 2026 as planned.", "The reserve parallel run ended on 28 August 2026",
          "The reserve parallel run ended on 2026-08-28.", "EVENT:EV-031"),
        C("The first NISA-FR1 return (Q2 2026) was submitted on 29 July 2026, one day ahead of the deadline.",
          "The first NISA-FR1 return (Q2 2026) was submitted on 29 July 2026",
          "The first NISA-FR1 return (2026Q2) was submitted on 2026-07-29.", "REPORT:NISA-FR1#submissions.2026Q2.submitted"),
        C("The 14-day review cadence for Tier-3 reserves (BR-RSV-007 v3) has applied since 1 July 2026.",
          "has applied since 1 July 2026", "BR-RSV-007 v3 (14-day Tier-3 review) applies from 2026-07-01.",
          "RULE:BR-RSV-007@v3#effective_from"),
        C("Wave 1 (UK motor) go/no-go is on 11 September, for cut-over on Monday 14 September 2026.",
          "go/no-go is on 11 September, for cut-over on Monday 14 September 2026",
          "Wave 1 go/no-go on 2026-09-11 for cut-over 2026-09-14.", "MEETING:MTG-011#date"),
    ]
    return status_report("TX057", "monthly_status_2026_08", d, "Programme Skerry – Monthly Status Report: August 2026",
                         "1–31 August 2026 (issued 4 September 2026)", ctx, monthly=True)


def tx041():
    d = "2026-08-07"
    r = _r("TX041")
    lead = person("P042", d)
    doc = new_doc("TX041", "fraud_settlement_squad_sprint_notes")
    doc.line("# Hub Squad – Fraud & Settlement: Sprint Notes")
    doc.blank()
    kv_table(doc, [("Date", long_date(d)), ("Squad lead", f"{lead.name}, {lead.title}"),
                   ("Sprint", "Sprint review and planning")])
    s = para(doc, "The squad owns fraud-referral-svc, settlement-svc and payment-orchestrator in Claims Hub.")
    doc.fact(s, "fraud-referral-svc, settlement-svc and payment-orchestrator",
             "Hub Squad – Fraud & Settlement owns fraud-referral-svc, settlement-svc and payment-orchestrator.",
             "general", "TEAM:T29#purpose")
    h(doc, 2, "Sprint goal")
    para(doc, pick(r, ["Finish the Wave 1 readiness items for the squad's services and close down open review comments.",
                       "Complete Wave 1 readiness work and reduce the defect backlog for the squad's services."]))
    h(doc, 2, "Done")
    for t in picks(r, PH.PROGRESS_ITEMS, 5):
        bullet(doc, t)
    s = bullet(doc, "Referral rule configuration re-checked against BR-FRD-031 v1 (refer at a Sentinel score of 65 or "
                    "more) in fraud-referral-svc.")
    doc.fact(s, "refer at a Sentinel score of 65 or more", "BR-FRD-031 v1 (in force 2026-04-01 to 2026-09-30): refer at 65 or more.",
             "temporal", "RULE:BR-FRD-031@v1#parameters.threshold")
    h(doc, 2, "Carried over")
    for t in picks(r, PH.NEXT_ITEMS, 3):
        bullet(doc, t)
    h(doc, 2, "Retro points")
    for t in picks(r, ["Pairing on the trickier stories worked well and should continue.",
                       "Review turnaround slowed mid-sprint; agree a daily review slot.",
                       "Stand-ups ran over twice – keep detail for after the stand-up.",
                       "Good collaboration with the Intake & Triage squad on shared test data.",
                       "Environment bookings were clearer this sprint."], 3):
        bullet(doc, t)
    h(doc, 2, "Housekeeping")
    for t in picks(r, PH.TEAM_NOTE_ITEMS, 3):
        bullet(doc, t)
    return doc


def tx042():
    d = "2026-07-15"
    doc = new_doc("TX042", "programme_glossary_page")
    hl = person("P054", d)
    doc.line("# Programme Skerry – Glossary")
    doc.blank()
    kv_table(doc, [("Page owner", f"{hl.name}, {hl.title} (IBM Consulting)"), ("Last reviewed", short_date(d)),
                   ("Audience", "Everyone working on Programme Skerry")])
    para(doc, "This page lists the business terms used across the programme, with the variants you will see in "
              "manuals, slides, spreadsheets, emails and code. Use the canonical term in new documents.")
    rows = []
    terms = sorted(W.glossary.values() if isinstance(W.glossary, dict) else W.glossary, key=lambda g: g["canonical"])
    for g in terms:
        variants = ", ".join(v["term"] for v in g.get("variants", []))
        rows.append([g["canonical"], g["definition"], variants or "–"])
    spans = md_table(doc, ["Term", "Meaning", "Also seen as"], rows)
    for g, sp in zip(terms, spans):
        if g["id"] in ("G-015", "G-008", "G-012", "G-020", "G-019", "G-001"):
            doc.fact(sp, g["definition"], f"Glossary {g['id']} ({g['canonical']}): {g['definition']}", "definition",
                     f"GLOSSARY:{g['id']}#definition")
    doc.blank()
    h(doc, 2, "Abbreviations")
    for k, v in [("CAB", "Change Advisory Board"), ("ADR", "Architecture Decision Record"),
                 ("BRD", "Business Requirements Document"), ("NISA", "National Insurance Supervisory Authority"),
                 ("PMO", "Programme Management Office"), ("SME", "Subject-matter expert")]:
        bullet(doc, f"{k} – {v}")
    h(doc, 2, "Suggesting a change")
    para(doc, "Comment on this page or contact the page owner. Changes to canonical terms go to the Design Authority.")
    return doc


def tx045():
    d = "2025-02-10"
    r = _r("TX045")
    doc = new_doc("TX045", "onboarding_notes_ibm_team", width=100)
    ak = person("P048", d)
    doc.line("# Onboarding Notes – IBM Team on Programme Skerry")
    doc.blank()
    kv_table(doc, [("Prepared by", f"{ak.name}, {ak.title}"), ("Date", short_date(d)),
                   ("For", "IBM Consulting team members joining Programme Skerry")])
    h(doc, 2, "Welcome")
    s = para(doc, "Welcome to Programme Skerry. Corvane Mutual is replacing CLARA, its mainframe claims system "
                  "(COBOL, CICS and DB2, live since 1994), with Claims Hub, a set of Java/Spring Boot microservices on "
                  "OpenShift. The IBM engagement started on 13 January 2025.")
    doc.fact(s, "The IBM engagement started on 13 January 2025", "The IBM engagement on Programme Skerry started on 2025-01-13.",
             "general", "EVENT:EV-012")
    h(doc, 2, "Who's who")
    who = [("P004", "Executive sponsor; chairs the Steering Committee"), ("P006", "Chief Information Officer"),
           ("P017", "Owns the Claims Hub product backlog"), ("P018", "Chairs the Design Authority"),
           ("P032", "Chairs the CAB"), ("P016", "CLARA system owner"),
           ("P047", "IBM engagement lead"), ("P049", "Claims Hub target architecture"),
           ("P048", "Programme plan and cut-over planning")]
    spans = md_table(doc, ["Name", "Title", "Why you will meet them"],
                     [[person(p, d).name, person(p, d).title, why] for p, why in who])
    doc.fact(spans[2], person("P017", d).title, "On 2025-02-10 Aisha Siddiqui's title was Claims Hub Product Owner.",
             "temporal", "PERSON:P017#titles")
    doc.blank()
    h(doc, 2, "Governance")
    for c in [
        C("Programme Skerry Steering Committee – monthly, second Thursday, 14:00 UK time.",
          "monthly, second Thursday, 14:00", "The Programme Skerry Steering Committee meets monthly on the second Thursday at 14:00.",
          "COMMITTEE:COM-03#cadence"),
        C("Design Authority – weekly, Tuesday 15:00 UK time.", "Design Authority – weekly, Tuesday 15:00",
          "The Design Authority meets weekly on Tuesday at 15:00.", "COMMITTEE:COM-05#cadence"),
        C("Change Advisory Board – weekly, Wednesday 11:00 UK time.", "Change Advisory Board – weekly, Wednesday 11:00",
          "The CAB meets weekly on Wednesday at 11:00.", "COMMITTEE:COM-04#cadence"),
    ]:
        put(doc, c, as_bullet=True)
    doc.blank()
    h(doc, 2, "Systems you will hear about")
    for sid in ["SYS01", "SYS02", "SYS03", "SYS05", "SYS17", "SYS04"]:
        sy = W.systems[sid]
        bullet(doc, f"{W.system_name(sid, d)} – {sy['type']}")
    doc.blank()
    s = para(doc, "The Hub squads (Intake & Triage, Reserve & Finance, Fraud & Settlement) were formed on 3 February "
                  "2025 and report to Neil Haworth, Head of Technology Delivery.")
    doc.fact(s, "were formed on 3 February 2025", "Hub squads T27, T28 and T29 were formed on 2025-02-03.",
             "general", "TEAM:T27#formed")
    h(doc, 2, "Practicalities")
    for t in [
        "Corvane House, 14 Tallowgate, London EC3N 9ZZ – collect your pass from reception on day one.",
        "Use your @ibm-consulting.example address for programme mail; Corvane distribution lists accept it.",
        "Client data stays in Corvane environments – never copy production data to IBM devices.",
        "Book desks through the Corvane facilities page; the programme area is on the fourth floor.",
        "Ask the PMO for access to the programme site and the CHUB Jira project.",
    ]:
        bullet(doc, t)
    h(doc, 2, "First-week checklist")
    for t in picks(r, PH.TEAM_NOTE_ITEMS, 3) + ["Read the business case summary and the architecture overview.",
                                                  "Meet your Corvane counterpart in the workstream."]:
        bullet(doc, t)
    return doc


def tx047():
    d = "2026-02-20"
    ctx = [
        C("CLX-IF-049, the reserve movement Kafka bridge, has been live since 12 December 2025.",
          "has been live since 12 December 2025", "CLX-IF-049 (reserve movement Kafka bridge) went live on 2025-12-12.",
          "INTERFACE:CLX-IF-049#since"),
        C("Henrik Vestergaard remains owner of CLX-IF-042 and CLX-IF-049.", "owner of CLX-IF-042 and CLX-IF-049",
          "Henrik Vestergaard owns CLX-IF-042 and CLX-IF-049.", "PERSON:P031#responsibilities"),
        C("The consumer service was renamed from reserve-svc to reserve-engine on 10 February; topic consumers "
          "and dashboards now use the new name.", "renamed from reserve-svc to reserve-engine on 10 February",
          "reserve-svc was renamed reserve-engine on 2026-02-10.", "SERVICE:reserve-engine#renames", "temporal"),
    ]
    return team_notes("TX047", "integration_platform_team_notes", d, "P031", "Integration Platform – Team Notes",
                      "Integration Platform (MQ Backbone and Event Streaming Platform)", ctx,
                      sections=[("Looking ahead", [
                          C("Support for the reserve parallel run starting on 2 March 2026.",
                            "reserve parallel run starting on 2 March 2026",
                            "The reserve parallel run started on 2026-03-02.", "EVENT:EV-026"),
                          "Interface catalogue entries to be reviewed against the new template.",
                      ])])


def tx048():
    d = "2026-08-14"
    ctx = [
        C("Tier-3 reserves have been on the 14-day review cadence since 1 July (BR-RSV-007 v3).",
          "14-day review cadence since 1 July (BR-RSV-007 v3)", "BR-RSV-007 v3: Tier-3 reserves reviewed every 14 days from 2026-07-01.",
          "RULE:BR-RSV-007@v3#parameters.review_days"),
        C("The reserve parallel run ends on 28 August; the close-out note goes to the Reserving Committee.",
          "The reserve parallel run ends on 28 August", "The reserve parallel run ended on 2026-08-28.", "EVENT:EV-031"),
        C("Large loss notifications to ReCede continue under BR-RSV-011 v2 (movements above the LLNT of £250,000, "
          "within 24 hours).", "movements above the LLNT of £250,000, within 24 hours",
          "BR-RSV-011 v2: notify ReCede within 24 hours of movements above the LLNT (£250,000).",
          "RULE:BR-RSV-011@v2#parameters.notify_hours", "use_of_definition"),
    ]
    return team_notes("TX048", "reserving_team_weekly_update", d, "P009", "Reserving – Weekly Update", "Reserving",
                      ctx, width=104)


def tx049():
    d = "2026-10-30"
    ctx = [
        C("UK motor claims have been handled in Claims Hub since the Wave 1 cut-over on 14 September.",
          "handled in Claims Hub since the Wave 1 cut-over on 14 September",
          "UK motor claims moved to Claims Hub at the Wave 1 cut-over on 2026-09-14.", "WAVE:MW-1#date"),
        C("Since 1 October, Tier-3 claims are referred to SIU at a Sentinel score of 60 or more; other claims stay "
          "at 65.", "Tier-3 claims are referred to SIU at a Sentinel score of 60 or more",
          "From 2026-10-01 Tier-3 claims are referred at a Sentinel score of 60 or more (BR-FRD-031 v2).",
          "RULE:BR-FRD-031@v2#parameters.tier3_threshold"),
        C("Wave 2 (UK home, commercial and liability, Norway and Sweden) is planned for 15 February 2027.",
          "planned for 15 February 2027", "Wave 2 is planned for 2027-02-15.", "WAVE:MW-2#date"),
    ]
    return team_notes("TX049", "claims_operations_leeds_weekly_update", d, "P011",
                      "Claims Operations – Weekly Update (Leeds)", "Claims Operations (Group) – Leeds teams", ctx)


def tx050():
    d = "2026-07-17"
    ctx = [
        C("Wave 0 (Denmark, PRD-MOT-DK and PRD-HOM-DK) completed on 1 June; lessons have been fed into the Wave 1 plan.",
          "Wave 0 (Denmark, PRD-MOT-DK and PRD-HOM-DK) completed on 1 June",
          "Wave 0 covered Danish products PRD-MOT-DK and PRD-HOM-DK and completed on 2026-06-01.", "WAVE:MW-0#scope"),
        C("Wave 1 covers UK motor (PRD-MOT-UK) and is planned with three rehearsals before the cut-over.",
          "planned with three rehearsals", "Wave 1 (PRD-MOT-UK) has three rehearsals.", "WAVE:MW-1#rehearsals"),
    ]
    return team_notes("TX050", "data_migration_workstream_status", d, "P051", "Data Migration – Workstream Status",
                      "Data migration (IBM and Corvane)", ctx,
                      sections=[("Reconciliation", [
                          "Reconciliation reports cover claim counts and reserves at claim level.",
                          "Exceptions are logged with an owner and reviewed daily during rehearsal weeks.",
                      ])])


def tx051():
    d = "2026-09-04"
    ctx = [
        C("The Wave 1 freeze is planned from 18:00 on Friday 11 September to 06:00 on Monday 14 September; no test "
          "deployments to production-like environments during that window.",
          "from 18:00 on Friday 11 September to 06:00 on Monday 14 September",
          "The Wave 1 freeze ran from 2026-09-11 18:00 to 2026-09-14 06:00.", "WAVE:MW-1#freeze"),
        C("Test summary report to be presented at the go/no-go on 11 September.", "go/no-go on 11 September",
          "The Wave 1 go/no-go took place on 2026-09-11.", "MEETING:MTG-011#date"),
    ]
    return team_notes("TX051", "test_quality_weekly_report", d, "P053", "Test & Quality – Weekly Report",
                      "Test & Quality (cross-squad)", ctx,
                      sections=[("Focus areas", [
                          "Regression of payment and settlement journeys.",
                          "Handler work-queue journeys for UK motor.",
                          "Interface checks with CLARA for the cut-over weekend.",
                      ])])


def tx052():
    d = "2026-02-27"
    ctx = [
        C("NISA Circular 2026/04 takes effect on 1 April 2026.", "takes effect on 1 April 2026",
          "NISA Circular 2026/04 takes effect on 2026-04-01.", "CIRCULAR:CIRC-2026-04#effective"),
        C("The first NISA-FR1 return covers Q2 2026 and is due by 30 July 2026.", "covers Q2 2026 and is due by 30 July 2026",
          "The first NISA-FR1 return covers 2026Q2 and is due 2026-07-30.", "REPORT:NISA-FR1#first_due"),
        C("The proposed rule set goes to the Claims Fraud Forum on 12 March for approval.",
          "Claims Fraud Forum on 12 March", "The Claims Fraud Forum of 2026-03-12 considered the Circular 2026/04 rule set.",
          "MEETING:MTG-012#date"),
    ]
    return team_notes("TX052", "compliance_team_notes_circular_readiness", d, "P037",
                      "Compliance – Team Notes: Circular 2026/04 readiness", "Compliance (Conduct & Counter-Fraud)", ctx,
                      sections=[("Readiness checklist", [
                          "Customer-notice templates drafted; legal review booked.",
                          "Referral reporting extract specification agreed with Regulatory Reporting.",
                          "Evidence folder structure set up for the implementation file.",
                      ])], width=100)


def tx054():
    d = "2025-11-14"
    ctx = [
        C("ADR-012 and ADR-017 were accepted at the Design Authority on 21 October; ADR-005 is superseded.",
          "ADR-012 and ADR-017 were accepted at the Design Authority on 21 October",
          "ADR-012 and ADR-017 were accepted on 2025-10-21; ADR-005 superseded.", "ADR:ADR-017#status"),
        C("The Claims Hub MVP has been live since 3 November.", "MVP has been live since 3 November",
          "The Claims Hub MVP went live on 2025-11-03.", "EVENT:EV-020"),
    ]
    return team_notes("TX054", "architecture_weekly_notes", d, "P018", "Enterprise Architecture – Weekly Notes",
                      "Enterprise Architecture", ctx,
                      sections=[("Design Authority pipeline", [
                          "Bridge design for CLX-IF-049 in review.",
                          "Service naming conventions to be refreshed after the MVP.",
                      ])])


def tx055():
    d = "2026-03-27"
    r = _r("TX055")
    sv = person("P026", d)
    doc = new_doc("TX055", "batch_operations_handover_notes")
    doc.line("# Mainframe Batch Operations – Shift Handover Notes")
    doc.blank()
    kv_table(doc, [("Date", long_date(d)), ("Prepared by", f"{sv.name}, {sv.title}"),
                   ("Scope", "CLARA overnight batch")])
    s = para(doc, "Reminder: the CLARA batch window is 23:30–05:30 UK time. Jobs that overrun the window are "
                  "escalated to the on-call Legacy Claims Platforms engineer.")
    doc.fact(s, "the CLARA batch window is 23:30–05:30 UK time", "CLARA's batch window is 23:30-05:30 UK time.",
             "general", "SYSTEM:SYS01#batch_window")
    s = para(doc, "The reserve parallel run (CLARA vs reserve-engine) has been running since 2 March; extracts for the "
                  "daily comparison must complete before the business day starts.")
    doc.fact(s, "has been running since 2 March", "The reserve parallel run started on 2026-03-02.", "general", "EVENT:EV-026")
    h(doc, 2, "Shift log")
    rows = []
    for night in ["Mon", "Tue", "Wed", "Thu"]:
        rows.append([night, pick(r, ["Batch completed within the window.", "Completed; one job restarted by the scheduler.",
                                     "Completed; late input file chased and received.", "Completed with no incidents."]),
                     pick(r, ["None", "None", "Ticket raised for follow-up", "Noted for the weekly review"])])
    md_table(doc, ["Night", "Summary", "Follow-up"], rows)
    h(doc, 2, "Handover points")
    for t in [
        "Check the scheduler console before taking the handover call.",
        "Restarts follow the runbook for each job – do not improvise restart points.",
        "Any change to the schedule goes through the CAB.",
    ] + picks(r, PH.TEAM_NOTE_ITEMS, 2):
        bullet(doc, t)
    return doc


def tx056():
    d = "2026-09-21"
    r = _r("TX056")
    cf = person("P022", d)
    doc = new_doc("TX056", "onboarding_notes_claims_hub_uk_motor", width=100)
    doc.line("# Onboarding Notes – Claims Hub for UK Motor Handlers")
    doc.blank()
    kv_table(doc, [("Prepared by", f"{cf.name}, {cf.title}"), ("Team", "Motor Claims – Leeds"),
                   ("Date", short_date(d))])
    h(doc, 2, "Where we are")
    put(doc, C("UK motor claims moved from CLARA to Claims Hub at the Wave 1 cut-over on Monday 14 September 2026.",
               "at the Wave 1 cut-over on Monday 14 September 2026",
               "UK motor moved to Claims Hub at the Wave 1 cut-over on 2026-09-14.", "WAVE:MW-1#date"))
    h(doc, 2, "Rules you will use every day")
    for c in [
        C("Acknowledge digital FNOLs within 1 business day and all other channels within 2 business days "
          "(BR-FNOL-001 v3).", "Acknowledge digital FNOLs within 1 business day and all other channels within 2 business days",
          "BR-FNOL-001 v3 (from 2026-07-01): acknowledge digital FNOLs within 1 business day, others within 2.",
          "RULE:BR-FNOL-001@v3#text"),
        C("Payment authority: Claims Handler £15,000; Team Leader £75,000 (BR-STL-002 v3).",
          "Claims Handler £15,000; Team Leader £75,000", "BR-STL-002 v3: Claims Handler £15,000, Team Leader £75,000.",
          "RULE:BR-STL-002@v3#parameters.team_leader"),
        C("Reserve authority: Claims Handler £25,000; Team Leader £100,000 (BR-RSV-003 v3).",
          "Claims Handler £25,000; Team Leader £100,000", "BR-RSV-003 v3: Claims Handler £25,000, Team Leader £100,000.",
          "RULE:BR-RSV-003@v3#parameters.team_leader"),
        C("Fraud referral: claims with a Sentinel score of 65 or more go to SIU; from 1 October 2026 Tier-3 claims "
          "go at 60 or more.", "from 1 October 2026 Tier-3 claims go at 60 or more",
          "From 2026-10-01 Tier-3 claims are referred at a Sentinel score of 60 or more.", "DECISION:DEC-014"),
        C("Never decline or reduce a claim because of the score alone – SIU review is always required (BR-FRD-033).",
          "Never decline or reduce a claim because of the score alone", "BR-FRD-033: no adverse decision on the score alone.",
          "RULE:BR-FRD-033@v1#text"),
    ]:
        put(doc, c, as_bullet=True)
    doc.blank()
    h(doc, 2, "Systems around Claims Hub")
    for sid in ["SYS05", "SYS17", "SYS03", "SYS04", "SYS09"]:
        bullet(doc, f"{W.system_name(sid, d)} – {W.systems[sid]['type']}")
    doc.blank()
    h(doc, 2, "Getting help")
    for t in ["Floor-walkers are on the Leeds floor during hypercare.",
              "Raise system questions in the hypercare channel with a claim reference, never customer details.",
              f"Team leader: {cf.name}."]:
        bullet(doc, t)
    h(doc, 2, "Tips from the first week")
    for t in picks(r, ["Check the work queue filter before assuming a claim is missing.",
                       "Use the claim timeline to see what migrated from CLARA.",
                       "Documents are in Evidence Vault – open them from the claim, not by searching.",
                       "Save notes as you go; the session times out after inactivity.",
                       "If an assessor report is missing, check the Assessor Portal status first."], 4):
        bullet(doc, t)
    return doc


def tx058():
    d = "2025-11-20"
    ctx = [
        C("Freya Lindahl has owned the recovery and subrogation process since 1 September 2025, as Head of "
          "Recoveries & Subrogation.", "owned the recovery and subrogation process since 1 September 2025",
          "Freya Lindahl owns the subrogation process from 2025-09-01.", "PROCESS:S7#owner_history"),
        C("Pursue subrogation where the recoverable amount is £1,000 or more (NOK 13,000 / SEK 13,500 / DKK 8,600) – "
          "BR-REC-003 v3 since 1 September.", "£1,000 or more (NOK 13,000 / SEK 13,500 / DKK 8,600)",
          "BR-REC-003 v3 (from 2025-09-01): pursue subrogation at £1,000 or more (NOK 13,000 / SEK 13,500 / DKK 8,600).",
          "RULE:BR-REC-003@v3#parameters.min_gbp", "temporal"),
        C("SUBTRAK retirement target remains 31 December 2026.", "SUBTRAK retirement target remains 31 December 2026",
          "The SUBTRAK retirement target is 2026-12-31.", "DECISION:DEC-004"),
        C("Write-offs above £10,000 need Freya's approval.", "Write-offs above £10,000 need Freya's approval",
          "Freya Lindahl approves recovery write-offs above £10,000.", "PERSON:P013#responsibilities"),
    ]
    return team_notes("TX058", "recoveries_subrogation_team_notes", d, "P013", "Recoveries & Subrogation – Team Notes",
                      "Recoveries & Subrogation (Group)", ctx,
                      sections=[("Panel and partners", [
                          "Litigated recoveries continue with Quarryhill Solicitors (Edward Pargeter).",
                      ])])


def tx060():
    d = "2026-04-24"
    ctx = [
        C("FNOL acknowledgement stays at 2 business days for every channel (BR-FNOL-001 v2, NISA Circular 2024/07).",
          "FNOL acknowledgement stays at 2 business days for every channel",
          "BR-FNOL-001 v2 (to 2026-06-30): acknowledge every FNOL within 2 business days.",
          "RULE:BR-FNOL-001@v2#parameters.ack_business_days", "temporal"),
        C("Since 1 April, customers whose claims are referred receive a written notice of additional checks; expect "
          "some calls about these letters.", "customers whose claims are referred receive a written notice of additional checks",
          "From 2026-04-01 customers receive written notice that a referred claim is subject to additional checks (BR-FRD-032 v2).",
          "RULE:BR-FRD-032@v2#text"),
        C("Rob Tennant owns the FNOL process; Harbour CRM business ownership stays with the Contact Centre.",
          "Rob Tennant owns the FNOL process", "Rob Tennant has owned the FNOL process since 2025-09-01.",
          "PERSON:P011#responsibilities"),
    ]
    return team_notes("TX060", "contact_centre_team_notes_glasgow", d, "P029", "Contact Centre – Team Notes (Glasgow)",
                      "Contact Centre", ctx,
                      sections=[("Call handling reminders", [
                          "Do not discuss the reason for additional checks; pass questions to the claim handler.",
                          "Log every FNOL in Harbour before ending the call.",
                      ])])


FILLER = {
    "TX039": tx039, "TX041": tx041, "TX042": tx042, "TX045": tx045, "TX046": tx046, "TX047": tx047,
    "TX048": tx048, "TX049": tx049, "TX050": tx050, "TX051": tx051, "TX052": tx052, "TX053": tx053,
    "TX054": tx054, "TX055": tx055, "TX056": tx056, "TX057": tx057, "TX058": tx058, "TX059": tx059,
    "TX060": tx060,
}

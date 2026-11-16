"""TX031-TX038, TX040, TX043, TX044: minutes, decision log, retrospective, call notes, post-mortem.

Attendees, dates, times and decisions come from timeline.meetings / timeline.decisions.
"""
from __future__ import annotations

from generators.common import util

from . import phrases as PH
from .core import (W, Doc, person, pick, picks, short_date, long_date, add_minutes, md_table, kv_table,
                   md_row, team_name, anchor_path)

ORG_LABEL = {"ORG-CORVANE": "Corvane Mutual", "ORG-IBM": "IBM Consulting", "REG-NISA": "NISA"}


def _doc(fid: str, width=None) -> Doc:
    return Doc(fid, W.anchor(fid)["filename"], width=width)


def _r(fid: str):
    return util.rng(f"{fid}:minutes")


def h(doc: Doc, level: int, text: str):
    if doc.lines and doc.lines[-1] != "":
        doc.blank()
    span = doc.line("#" * level + " " + text)
    doc.blank()
    return span


def bullet(doc: Doc, text: str, mark: str = "- "):
    return doc.para(text, prefix=" " * len(mark), first_prefix=mark)


def para(doc: Doc, text: str):
    span = doc.para(text)
    doc.blank()
    return span


def meeting(mid: str) -> dict:
    return W.meetings[mid]


def attendee_rows(pids, d, roles: dict | None = None):
    roles = roles or {}
    rows = []
    for pid in pids:
        p = person(pid, d)
        role = p.title + (f" ({roles[pid]})" if pid in roles else "")
        rows.append([p.name, role, ORG_LABEL.get(p.employer, p.org)])
    return rows


def meta(doc: Doc, rows):
    return kv_table(doc, rows)


def doc_control(doc: Doc, rows):
    h(doc, 2, "Document control")
    return md_table(doc, ["Version", "Date", "Author", "Change"], rows)


def actions_table(doc: Doc, rows):
    return md_table(doc, ["#", "Action", "Owner", "Due", "Status"], rows)


def standard_opening(doc: Doc, r, apologies_text: str):
    para(doc, f"{pick(r, PH.OPENING)} {pick(r, PH.DECLARATIONS)} {apologies_text}")
    para(doc, f"{pick(r, PH.PREV_MINUTES)} {pick(r, PH.ACTIONS_REVIEWED)}")


def generic_points(doc: Doc, r, k: int = 2, impl: bool = False):
    para(doc, pick(r, PH.DISCUSSION_LEADS))
    for t in picks(r, PH.IMPL_POINTS if impl else PH.GENERIC_POINTS, k):
        bullet(doc, t)
    doc.blank()


def closing(doc: Doc, r, end: str):
    para(doc, pick(r, PH.CLOSE).format(end=end))


def apologies_for(mid: str, forum_members_extra=()) -> list[str]:
    m = meeting(mid)
    if not m.get("forum"):
        return []
    members = W.committees[m["forum"]]["members"]
    return [p for p in members if p not in m["attendees"] and W.employed(p, m["date"])] + list(forum_members_extra)


def apologies_text(pids, d) -> str:
    if not pids:
        return "No apologies were received."
    names = [f"{person(p, d).name}" for p in pids]
    if len(names) == 1:
        return f"Apologies were received from {names[0]}."
    return "Apologies were received from " + ", ".join(names[:-1]) + f" and {names[-1]}."


ABBREV = {
    "ADR": "Architecture Decision Record",
    "BRD": "Business Requirements Document",
    "CAB": "Change Advisory Board",
    "CDC": "Change data capture",
    "CHUB": "Jira project key for Claims Hub",
    "CLARA": "Claims Ledger And Reserve Application (legacy mainframe claims system)",
    "FNOL": "First notice of loss",
    "FR1": "NISA-FR1 Quarterly Fraud Referral Return",
    "LLNT": "Large Loss Notification Threshold (£250,000 reserve movement, BR-RSV-011 v2)",
    "NISA": "National Insurance Supervisory Authority",
    "SIU": "Special Investigations Unit (Counter-Fraud & SIU from 1 September 2025)",
    "SNT-4.2": "Current Sentinel scoring model version",
    "Tier-3": "Claim tier defined by BR-TRI-003",
    "PMO": "Programme Management Office",
}


def abbreviations(doc: Doc, keys):
    h(doc, 2, "Abbreviations")
    return md_table(doc, ["Term", "Meaning"], [[k, ABBREV[k]] for k in keys])


def papers(doc: Doc, items):
    h(doc, 2, "Papers")
    for i, t in enumerate(items, 1):
        doc.line(f"{i}. {t}")


def distribution(doc: Doc, pids, d, extra=()):
    h(doc, 2, "Distribution")
    names = [f"{person(p, d).name} ({person(p, d).title})" for p in pids] + list(extra)
    for n in names:
        bullet(doc, n)


def rule_appendix(doc: Doc, items, d, title="Appendix – rule text"):
    """Print rule versions as they stood on date d (no later status, no later sources)."""
    h(doc, 2, title)
    for rid, ver in items:
        rv = W.rules[rid]["versions"][ver - 1]
        ok = W.may_state(doc.fid, f"RULE:{rid}@v{ver}", "text")
        bullet(doc, f"**{rid} v{ver}** – {W.rules[rid]['title']}")
        text = rv["text"] if ok else "Text as published in the rules register."
        s = doc.para(f"Text: {text}", prefix="  ", first_prefix="  ")
        bits = []
        if rv.get("approved_on") and rv["approved_on"] <= str(d):
            bits.append(f"approved {short_date(rv['approved_on'])} by " +
                        ", ".join(person(p, rv["approved_on"]).name for p in rv["approved_by"]))
        if rv.get("effective_from"):
            bits.append(f"effective from {short_date(rv['effective_from'])}")
        if rv.get("effective_to") and rv["effective_to"] < str(d):
            bits.append(f"effective to {short_date(rv['effective_to'])}")
        doc.para("Status: " + "; ".join(bits) + ".", prefix="  ", first_prefix="  ")
        if ok:
            doc.fact(s, rv["text"], f"{rid} v{ver}: {rv['text']}", "general", f"RULE:{rid}@v{ver}#text")
    doc.blank()


def ref_label(fid: str, ref: str, d) -> str:
    if ref.startswith("ADR-") and ref in W.adrs:
        a = W.adrs[ref]
        return f"{ref} – {a['title']}"
    if ref.startswith("CHUB-") and ref in W.tickets and W.may_state(fid, f"TICKET:{ref}", "summary"):
        return f"{ref} – {W.tickets[ref]['summary']}"
    if ref.startswith("BR-") and ref in W.rules:
        return f"{ref} – {W.rules[ref]['title']}"
    if ref in W.waves:
        return f"{ref} – {W.waves[ref]['name']}"
    if ref in W.systems:
        return f"{ref} – {W.system_name(ref, d)}"
    if ref in W.vendors:
        return f"{ref} – {W.vendors[ref]['name']}"
    if ref in W.circulars:
        return f"{W.circulars[ref]['ref']} – {W.circulars[ref]['title']}"
    return ref


def meeting_facts(doc: Doc, mid: str, date_span, chair_span=None, att_spans=None, date_needle=None):
    m = meeting(mid)
    d = m["date"]
    doc.fact(date_span, date_needle or long_date(d),
             f"{m['title']} ({mid}) took place on {d} at {m['start_time']} for {m['duration_minutes']} minutes.",
             "general", f"MEETING:{mid}#date")
    if att_spans:
        names = [person(p, d).name for p in m["attendees"]]
        doc.fact((att_spans[0][0], att_spans[-1][1]), names[-1],
                 f"Attendees of {mid}: " + ", ".join(names) + ".", "general", f"MEETING:{mid}#attendees")


# =============================================================================================
# TX031 – Fraud Rules Workshop minutes (MTG-007, 2026-09-17; issued 2026-09-18)
# =============================================================================================

def tx031():
    fid, mid = "TX031", "MTG-007"
    r = _r(fid)
    m = meeting(mid)
    d = m["date"]
    doc = _doc(fid)
    end = add_minutes(m["start_time"], m["duration_minutes"])
    chair, hl = person("P008", d), person("P054", d)
    doc.line("# Minutes – Fraud Rules Workshop")
    doc.blank()
    doc.line("*Claims Fraud Forum – extended workshop session. Classification: Internal.*")
    doc.blank()
    spans = meta(doc, [
        ("Meeting", "Fraud Rules Workshop (Claims Fraud Forum)"),
        ("Date", long_date(d)),
        ("Time", f"{m['start_time']}–{end}"),
        ("Location", f"{pick(r, PH.ROOMS)}, {pick(r, PH.DIAL_IN)}"),
        ("Chair", f"{chair.name}, {chair.title}"),
        ("Minutes", f"{hl.name}, {hl.title} (IBM Consulting)"),
        ("Status", "Final – approved by the chair on 18 September 2026"),
    ])
    date_span, chair_span = spans[1], spans[4]
    doc_control(doc, [
        ["0.1", "17 Sep 2026", hl.name, "First draft from workshop notes and the recording"],
        ["0.2", "18 Sep 2026", chair.name, "Chair review – wording of decisions D1 and D2"],
        ["1.0", "18 Sep 2026", hl.name, "Final for circulation"],
    ])
    h(doc, 2, "Attendees")
    att = md_table(doc, ["Name", "Role", "Organisation"],
                   attendee_rows(m["attendees"], d, {"P008": "Chair", "P054": "minutes"}))
    meeting_facts(doc, mid, date_span, att_spans=att)
    apol = apologies_for(mid)
    h(doc, 2, "Apologies")
    for p in apol:
        pp = person(p, d)
        bullet(doc, f"{pp.name}, {pp.title}")
    h(doc, 2, "Agenda")
    for i, t in enumerate(["Welcome, apologies and previous actions", "Circular 2026/04: six months of operation",
                           "Referral threshold for Tier-3 claims", "Approval of customer-notice deferrals",
                           "Option: a single lower threshold for all claims",
                           "Implementation, communications and documentation", "Any other business"], 1):
        doc.line(f"{i}. {t}")

    h(doc, 2, "1. Welcome, apologies and previous actions")
    standard_opening(doc, r, apologies_text(apol, d))

    h(doc, 2, "2. Circular 2026/04: six months of operation")
    s = para(doc, "Ruth Okafor summarised how the fraud rule set has operated since NISA Circular 2026/04 took "
                  "effect on 1 April 2026. Under BR-FRD-031 v1 every claim with a Sentinel score of 65 or more is "
                  "referred to SIU, in line with paragraph 3.3 of the Circular, which says a score-based cut-off on "
                  "the 0–100 scale must not exceed 65.")
    doc.fact(s, "a score-based cut-off on the 0–100 scale must not exceed 65",
             "NISA Circular 2026/04 §3.3: a score-based referral cut-off on a 0–100 scale must not exceed 65.",
             "general", "CIRCULAR:CIRC-2026-04#requirements")
    doc.fact(s, "Under BR-FRD-031 v1 every claim with a Sentinel score of 65 or more is referred to SIU",
             "BR-FRD-031 v1 (2026-04-01 to 2026-09-30): refer every claim with a Sentinel score of 65 or more.",
             "temporal", "RULE:BR-FRD-031@v1#text")
    s = para(doc, "The first NISA-FR1 return (Q2 2026) went to NISA on 29 July 2026, ahead of the 30 July "
                  "deadline; the Q3 return is due by 30 October 2026.")
    doc.fact(s, "The first NISA-FR1 return (Q2 2026) went to NISA on 29 July 2026",
             "The first NISA-FR1 return (2026Q2) was submitted on 2026-07-29.", "general",
             "REPORT:NISA-FR1#submissions.2026Q2.submitted")
    s = para(doc, "Ruth also reminded the group that the batch-sweep problem found in May (INC-2026-0518) is still "
                  "covered by the daily Compliance query; the permanent fix for CLRFR040 is tracked as CHUB-298, "
                  "which remains open.")
    doc.fact(s, "the permanent fix for CLRFR040 is tracked as CHUB-298, which remains open",
             "As of 2026-09-18 the permanent CLRFR040 fix (CHUB-298) was still open.", "temporal",
             "TICKET:CHUB-298#status_history")
    generic_points(doc, r, 2)

    h(doc, 2, "3. Referral threshold for Tier-3 claims")
    s = para(doc, "Oskar Lindgren presented an analysis of Sentinel scores (model SNT-4.2, calibrated on 16 March "
                  "2026) for claims that meet the Tier-3 definition in BR-TRI-003 v3. The analysis concentrated on "
                  "Tier-3 claims scoring between 60 and 64, which are not referred under the current rule.")
    doc.fact(s, "model SNT-4.2, calibrated on 16 March 2026",
             "Sentinel runs model SNT-4.2, calibrated on 2026-03-16.", "general", "SYSTEM:SYS03#model_calibrated")
    para(doc, "Points raised in discussion:")
    bullet(doc, "Ruth Okafor confirmed that a Tier-3 threshold below 65 is consistent with paragraph 3.3 of the "
                "Circular, which sets a maximum cut-off rather than a minimum.")
    bullet(doc, "Rachel Dunmore asked that the effect on SIU workload is monitored against the 3-business-day "
                "triage standard in BR-FRD-035 v2.")
    s = bullet(doc, "Linnea Sjöberg confirmed that fraud-referral-svc and triage-svc can apply a separate threshold "
                    "for Tier-3 claims, and that configuration can be ready for 1 October.")
    doc.fact(s, "fraud-referral-svc and triage-svc can apply a separate threshold for Tier-3 claims",
             "BR-FRD-031 is implemented in Claims Hub by fraud-referral-svc and triage-svc.", "general",
             "RULE:BR-FRD-031#implemented_in")
    s = bullet(doc, "Aisha Siddiqui asked how claims still on CLARA would be covered. CLRFR030 (online) and CLRFR040 "
                    "(batch) both apply the referral rule; because CHUB-298 is open, the daily Compliance query will "
                    "be extended to Tier-3 claims scoring 60–64 from 1 October.")
    doc.fact(s, "the daily Compliance query will be extended to Tier-3 claims scoring 60–64 from 1 October",
             "From 2026-10-01 the INC-2026-0518 workaround query also covers Tier-3 claims scoring 60-64.",
             "general", "INCIDENT:INC-2026-0518#workaround")
    s = bullet(doc, "Ingrid Ashby supported the proposal and noted that the Claims Handling Manual v7.2, approved on "
                    "30 June 2026, states 65 for all claims and therefore predates this decision.")
    doc.fact(s, "the Claims Handling Manual v7.2, approved on 30 June 2026, states 65 for all claims",
             "Claims Handling Manual v7.2 (approved 2026-06-30) states a referral threshold of 65 for all claims; "
             "the Tier-3 decision of 2026-09-17 post-dates it.", "temporal", "CONTRA:C01")
    doc.blank()
    para(doc, "The outcome is recorded as decision D1 below.")

    h(doc, 2, "4. Approval of customer-notice deferrals")
    s = para(doc, "Rachel Dunmore described how deferrals of the customer notice (BR-FRD-036) have been used since "
                  "April where SIU certifies a tipping-off risk. Without a deferral, the customer must be told in "
                  "writing within 10 business days of the referral that the claim is subject to additional checks "
                  "(BR-FRD-032 v2). Deferrals remain capped at 60 days.")
    doc.fact(s, "within 10 business days of the referral",
             "BR-FRD-032 v2: notify the customer in writing within 10 business days of a fraud referral unless deferred.",
             "general", "RULE:BR-FRD-032@v2#parameters.notice_business_days")
    para(doc, "Members agreed that long deferrals warrant more senior sign-off and that Compliance should know about "
              "them on the day they are approved. The outcome is recorded as decision D2.")

    h(doc, 2, "5. Option: a single lower threshold for all claims")
    para(doc, "The workshop considered lowering the general referral threshold to 60 for all claims. Oskar "
              "Lindgren presented an estimate of the additional referral volume; the figure is in the analysis pack "
              "and the workshop recording and is not repeated here.")
    para(doc, "Members concluded that the targeted Tier-3 change addresses the risk identified, and the option was "
              "not taken forward (decision D3).")

    h(doc, 2, "6. Implementation, communications and documentation")
    s = bullet(doc, "BR-FRD-031 v2 and BR-FRD-036 v2 were approved at the workshop by Niall Brannigan and Ingrid "
                    "Ashby, effective 1 October 2026.")
    doc.fact(s, "BR-FRD-031 v2 and BR-FRD-036 v2 were approved at the workshop by Niall Brannigan and Ingrid Ashby",
             "BR-FRD-031 v2 and BR-FRD-036 v2 were approved on 2026-09-17 by Niall Brannigan and Ingrid Ashby.",
             "approved", "RULE:BR-FRD-031@v2#approved_by")
    bullet(doc, "The fraud-referral BRD will be updated to reflect both rule versions.")
    bullet(doc, "A change request will be raised so the next revision of the Claims Handling Manual reflects the "
                "Tier-3 threshold and the deferral approval.")
    bullet(doc, "SIU, Major & Complex Loss and the claims handling teams will be briefed before 1 October.")
    doc.blank()
    generic_points(doc, r, 2, impl=True)

    h(doc, 2, "7. Any other business")
    para(doc, pick(r, PH.AOB))
    closing(doc, r, end)

    h(doc, 2, "Decisions")
    s = para(doc, "D1 (DEC-014) – From 1 October 2026, Tier-3 claims (BR-TRI-003) are referred to SIU at a Sentinel "
                  "score of 60 or more; the general referral threshold stays at 65 (BR-FRD-031 v2). Decided by Niall "
                  "Brannigan and Ingrid Ashby.")
    doc.place(s, "tx31_min", "From 1 October 2026, Tier-3 claims (BR-TRI-003) are referred to SIU at a Sentinel "
                              "score of 60 or more")
    s = para(doc, "D2 (DEC-015) – From 1 October 2026, customer-notice deferrals beyond 30 days need the approval of "
                  "the Head of Counter-Fraud & SIU, and Compliance is notified the same day (BR-FRD-036 v2).")
    doc.fact(s, "customer-notice deferrals beyond 30 days need the approval of the Head of Counter-Fraud & SIU, and "
                "Compliance is notified the same day",
             "DEC-015: from 2026-10-01 customer-notice deferrals beyond 30 days need the Head of Counter-Fraud & SIU "
             "and Compliance is notified the same day (BR-FRD-036 v2).", "needle", "DECISION:DEC-015")
    s = para(doc, "D3 (DEC-016) – The option to lower the general referral threshold to 60 for all claims was rejected.")
    doc.fact(s, "The option to lower the general referral threshold to 60 for all claims was rejected",
             "DEC-016: the option to lower the general referral threshold to 60 for all claims was rejected.",
             "needle", "DECISION:DEC-016#statement")

    h(doc, 2, "Actions")
    actions_table(doc, [
        ["A1", "Configure the Tier-3 threshold of 60 in fraud-referral-svc and triage-svc for 1 October",
         "Linnea Sjöberg", "30 Sep 2026", "Open"],
        ["A2", "Extend the daily Compliance query to Tier-3 claims scoring 60–64 from 1 October", "Ruth Okafor",
         "1 Oct 2026", "Open"],
        ["A3", "Update the fraud-referral BRD for BR-FRD-031 v2 and BR-FRD-036 v2", "Hannah Lyle", "25 Sep 2026",
         "Open"],
        ["A4", "Brief SIU investigators on the Tier-3 threshold and the deferral approval change", "Rachel Dunmore",
         "30 Sep 2026", "Open"],
        ["A5", "Raise the manual change request for the next revision", "Ingrid Ashby", "16 Oct 2026", "Open"],
        ["A6", "Confirm with Legacy Claims Platforms how the Tier-3 threshold is applied in CLARA while CHUB-298 is "
               "open", "Aisha Siddiqui", "25 Sep 2026", "Open"],
    ])
    papers(doc, [
        "Sentinel SNT-4.2 – Tier-3 score analysis (Oskar Lindgren)",
        "Customer-notice deferrals since April 2026 – SIU summary (Rachel Dunmore)",
        "Circular 2026/04 compliance status – September 2026 (Ruth Okafor)",
        "Option paper: single lower referral threshold (Oskar Lindgren)",
    ])
    rule_appendix(doc, [("BR-FRD-031", 2), ("BR-FRD-036", 2), ("BR-TRI-003", 3), ("BR-FRD-032", 2),
                        ("BR-FRD-035", 2)], d, "Appendix A – rule text referred to in these minutes")
    abbreviations(doc, ["SIU", "FR1", "NISA", "BRD", "SNT-4.2", "Tier-3", "CLARA", "CHUB"])
    distribution(doc, m["attendees"] + ["P011"], d, extra=["Programme Skerry decision log (PMO)"])
    doc.blank()
    doc.line(f"*Minutes prepared by {hl.name}. Approved by {chair.name}, chair.*")
    return doc


# =============================================================================================
# TX032 – Reserving Committee minutes (MTG-006, 2026-06-09)
# =============================================================================================

def tx032():
    fid, mid = "TX032", "MTG-006"
    r = _r(fid)
    m = meeting(mid)
    d = m["date"]
    doc = _doc(fid, width=100)
    end = add_minutes(m["start_time"], m["duration_minutes"])
    chair = person("P009", d)
    doc.line("# Reserving Committee – Minutes")
    doc.blank()
    spans = meta(doc, [
        ("Committee", "Reserving Committee"),
        ("Date", long_date(d)),
        ("Time", f"{m['start_time']}–{end} (UK)"),
        ("Venue", pick(r, PH.ROOMS)),
        ("Chair", f"{chair.name}, {chair.title}"),
        ("Secretary", "Reserving team"),
        ("Status", "Final"),
    ])
    doc_control(doc, [
        ["0.1", "9 Jun 2026", "Reserving team", "Draft for chair review"],
        ["1.0", "9 Jun 2026", chair.name, "Approved by the chair"],
    ])
    h(doc, 2, "Present")
    att = md_table(doc, ["Name", "Role", "Organisation"], attendee_rows(m["attendees"], d, {"P009": "Chair"}))
    meeting_facts(doc, mid, spans[1], att_spans=att)

    h(doc, 2, "1. Opening, minutes and actions")
    standard_opening(doc, r, apologies_text(apologies_for(mid), d))

    h(doc, 2, "2. Reserve parallel run – progress")
    s = para(doc, "The Committee received an update on the reserve parallel run between CLARA and reserve-engine, "
                  "which started on 2 March 2026 and is planned to end on 28 August 2026 (CHUB-241). Daily "
                  "comparisons are reviewed by the Reserving team with the Reserve & Finance squad, and differences "
                  "are explained before the next day's run.")
    doc.fact(s, "started on 2 March 2026 and is planned to end on 28 August 2026",
             "The reserve parallel run (CLARA vs reserve-engine) ran from 2026-03-02 to 2026-08-28 (CHUB-241).",
             "general", "TICKET:CHUB-241#summary")
    s = para(doc, "The Committee noted the update on audit finding IA-25-07: as agreed at the reserving design review "
                  "on 5 March 2026, reserve-engine will record currency revaluations as RV movements, which closes "
                  "the finding in the target platform, while CLRGL090 stays unchanged in CLARA.")
    doc.fact(s, "reserve-engine will record currency revaluations as RV movements",
             "DEC-005 (2026-03-05): reserve-engine records currency revaluations as RV movements, closing audit finding "
             "IA-25-07 in the target; CLRGL090 stays unchanged in CLARA.", "general", "DECISION:DEC-005")
    generic_points(doc, r, 1)

    h(doc, 2, "3. Tier-3 reserve review cadence (BR-RSV-007)")
    s = para(doc, "The chair presented the proposal from the reserving design review of 5 March 2026 to shorten the "
                  "review interval for reserves on Tier-3 claims. Under BR-RSV-007 v2, in force since 1 January 2024, "
                  "Tier-3 reserves must be reviewed at least every 21 days.")
    doc.fact(s, "Under BR-RSV-007 v2, in force since 1 January 2024, Tier-3 reserves must be reviewed at least every 21 days",
             "BR-RSV-007 v2 (from 2024-01-01): Tier-3 reserves reviewed at least every 21 days.", "temporal",
             "RULE:BR-RSV-007@v2#parameters.review_days")
    doc.fact(s, "proposal from the reserving design review of 5 March 2026",
             "DEC-006 (2026-03-05, reserving design review): propose a 14-day Tier-3 review cadence from 2026-07-01 "
             "to the Reserving Committee.", "general", "DECISION:DEC-006")
    para(doc, "In discussion:")
    bullet(doc, "Kirsty Mowbray confirmed that Major & Complex Loss would plan its review diary around the shorter "
                "interval and asked for the start date to align with a month boundary.")
    bullet(doc, "Sebastian Moreau-Clarke supported the change as consistent with the reserving policy.")
    bullet(doc, "Hamish Gilchrist asked that month-end reporting reflects the change from the first affected close.")
    bullet(doc, "Ingrid Ashby supported the proposal on behalf of Claims.")
    doc.blank()
    s = para(doc, "Decision: the Committee approved BR-RSV-007 v3 – reserves on Tier-3 claims must be reviewed at least "
                  "every 14 days – effective 1 July 2026. Approved by the chair, Lena Kristiansen.")
    doc.place(s, "tx32_rc", "approved BR-RSV-007 v3 – reserves on Tier-3 claims must be reviewed at least every 14 "
                            "days – effective 1 July 2026")

    h(doc, 2, "4. Large loss notifications")
    s = para(doc, "The Committee noted the large loss notifications made to Reinsurance since the last meeting under "
                  "BR-RSV-011 v2, which requires notification to ReCede within 24 hours of any reserve movement "
                  "exceeding the Large Loss Notification Threshold (LLNT) of £250,000. No late notifications were "
                  "reported.")
    doc.fact(s, "within 24 hours of any reserve movement exceeding the Large Loss Notification Threshold (LLNT) of £250,000",
             "BR-RSV-011 v2: notify ReCede within 24 hours of a reserve movement exceeding the LLNT of £250,000.",
             "definition", "RULE:BR-RSV-011@v2#text")

    h(doc, 2, "5. Wave 0 (Denmark)")
    s = para(doc, "The Committee noted that the Wave 0 cut-over for Denmark took place on 1 June 2026, covering all "
                  "Danish products (PRD-MOT-DK and PRD-HOM-DK). Hamish Gilchrist confirmed the first month-end close "
                  "after the cut-over will be reviewed with the Reserving team.")
    doc.fact(s, "Wave 0 cut-over for Denmark took place on 1 June 2026",
             "Wave 0 (Denmark: PRD-MOT-DK, PRD-HOM-DK) cut over on 2026-06-01.", "general", "WAVE:MW-0#date")

    h(doc, 2, "6. Any other business")
    para(doc, pick(r, PH.AOB))
    closing(doc, r, end)

    h(doc, 2, "Actions")
    actions_table(doc, [
        ["RC-06-1", "Publish BR-RSV-007 v3 to claims teams ahead of 1 July", chair.name, "19 Jun 2026", "Open"],
        ["RC-06-2", "Confirm the review diary change in reserve-engine and CLARA with the delivery teams", chair.name,
         "26 Jun 2026", "Open"],
        ["RC-06-3", "Plan Major & Complex Loss review capacity for the 14-day interval", "Kirsty Mowbray",
         "26 Jun 2026", "Open"],
        ["RC-06-4", "Review first post-Wave 0 month-end close", "Hamish Gilchrist", "10 Jul 2026", "Open"],
    ])
    papers(doc, [
        "Reserve parallel run – status report (Reserve & Finance squad)",
        "Tier-3 review cadence – proposal from the reserving design review (Lena Kristiansen)",
        "Large loss notifications since the last meeting (Reinsurance)",
        "Wave 0 (Denmark) – reserving close-out note",
    ])
    rule_appendix(doc, [("BR-RSV-007", 3), ("BR-RSV-007", 2), ("BR-RSV-011", 2), ("BR-RSV-003", 3)], d,
                  "Appendix – rules referred to")
    abbreviations(doc, ["LLNT", "Tier-3", "CLARA", "CHUB"])
    distribution(doc, m["attendees"], d, extra=["Reserving team shared mailbox"])
    return doc


# =============================================================================================
# TX033 – CAB minutes (MTG-009, 2026-11-11)
# =============================================================================================

def tx033():
    fid, mid = "TX033", "MTG-009"
    r = _r(fid)
    m = meeting(mid)
    d = m["date"]
    doc = _doc(fid)
    end = add_minutes(m["start_time"], m["duration_minutes"])
    chair = person("P032", d)
    doc.line("# Change Advisory Board (CAB) – Minutes")
    doc.blank()
    spans = meta(doc, [
        ("Date", long_date(d)),
        ("Time", f"{m['start_time']}–{end}"),
        ("Chair", f"{chair.name}, {chair.title}"),
        ("Location", f"{pick(r, PH.ROOMS)}, {pick(r, PH.DIAL_IN)}"),
        ("Status", "Final"),
    ])
    h(doc, 2, "Attendees")
    att = md_table(doc, ["Name", "Role", "Organisation"], attendee_rows(m["attendees"], d, {"P032": "Chair"}))
    meeting_facts(doc, mid, spans[0], att_spans=att)
    s = para(doc, "Tariq Hussain attended for the first time as Engineering Lead of the Recoveries & Documents squad, "
                  "formed on 1 November 2026.")
    doc.fact(s, "Engineering Lead of the Recoveries & Documents squad, formed on 1 November 2026",
             "Tariq Hussain has led the Hub Squad – Recoveries & Documents since it was formed on 2026-11-01.",
             "temporal", "TEAM:T30#lead_history")

    h(doc, 2, "1. Previous actions")
    para(doc, pick(r, PH.ACTIONS_REVIEWED))

    h(doc, 2, "2. Change list – release R2026.11")
    s = para(doc, "The CAB reviewed release R2026.11, proposed for implementation on Thursday 12 November 2026. The "
                  "release contains three changes:")
    spans = md_table(doc, ["Ticket", "Component", "Change", "Assignee", "Risk"], [
        ["CHUB-298", "CLARA", "CLRFR040 batch sweep referral threshold fix (INC-2026-0518)",
         person("P023", d).name, "Medium"],
        ["CHUB-415", "Platform", "CODEOWNERS update (repository ownership file; no runtime impact)",
         person("P043", d).name, "Low"],
        ["CHUB-421", "notification-svc", W.tickets["CHUB-421"]["summary"], person("P043", d).name, "Low"],
    ])
    doc.fact(spans[0], "CLRFR040 batch sweep referral threshold fix (INC-2026-0518)",
             "CHUB-298 (assigned to Keith Barraclough) fixes the CLRFR040 batch sweep referral threshold behind "
             "INC-2026-0518.", "general", "TICKET:CHUB-298#assignee")
    doc.fact(spans[2], W.tickets["CHUB-421"]["summary"],
             "CHUB-421: " + W.tickets["CHUB-421"]["summary"] + ".", "general", "TICKET:CHUB-421#summary")
    doc.blank()
    para(doc, "Discussion:")
    s = bullet(doc, "Graham Pocock confirmed that CHUB-298 has been in review since 4 November and that the batch "
                    "sweep fix closes the gap behind INC-2026-0518. The daily Compliance query stays in place until "
                    "Compliance confirms the first batch run after release.")
    doc.fact(s, "CHUB-298 has been in review since 4 November",
             "CHUB-298 moved to In Review on 2026-11-04.", "temporal", "TICKET:CHUB-298#status_history")
    bullet(doc, "Sunita Vaghela confirmed the CLARA deployment fits the normal batch schedule and needs no "
                "special handling by Batch Operations.")
    bullet(doc, "Linnea Sjöberg and Tariq Hussain confirmed the Claims Hub changes were tested in the integration "
                "environment and have a standard rollback.")
    bullet(doc, "Henrik Vestergaard and Daniel Achebe raised no concerns for their platforms.")
    doc.blank()
    s = para(doc, "Decision: the CAB approved release R2026.11 for implementation on 12 November 2026, comprising "
                  "CHUB-298 (CLRFR040), CHUB-415 (CODEOWNERS) and CHUB-421 (notification topic).")
    doc.place(s, "tx33_cab", "approved release R2026.11 for implementation on 12 November 2026, comprising CHUB-298 "
                             "(CLRFR040), CHUB-415 (CODEOWNERS) and CHUB-421 (notification topic)")

    h(doc, 2, "3. Forward schedule of change")
    s = para(doc, "The Wave 2 freeze, from 18:00 on 12 February 2027 to 06:00 on 15 February 2027, is in the change "
                  "calendar. No other freeze periods were added this week.")
    doc.fact(s, "from 18:00 on 12 February 2027 to 06:00 on 15 February 2027",
             "The Wave 2 freeze runs from 2027-02-12 18:00 to 2027-02-15 06:00.", "general", "WAVE:MW-2#freeze")
    h(doc, 2, "4. Emergency changes and post-implementation reviews")
    para(doc, "No emergency changes were raised since the last CAB. No post-implementation reviews were due.")
    h(doc, 2, "5. Any other business")
    para(doc, pick(r, PH.AOB))
    closing(doc, r, end)
    h(doc, 2, "Actions")
    actions_table(doc, [
        ["CAB-1", "Implement R2026.11 and confirm completion to the CAB mailbox", "Graham Pocock / Tariq Hussain",
         "12 Nov 2026", "Open"],
        ["CAB-2", "Confirm the first CLRFR040 batch run after release with Compliance", "Graham Pocock",
         "13 Nov 2026", "Open"],
    ])
    h(doc, 2, "Change records reviewed")
    for t in ["CHUB-298", "CHUB-415", "CHUB-421"]:
        tk = W.tickets[t]
        sh = [x for x in tk.get("status_history", []) if x["from"] <= d]
        st = sh[-1]["status"] if sh else tk["status"]
        bullet(doc, f"{t} ({tk['type']}, component {tk['component']}) – fix version {tk['fix_version']}; status at "
                    f"CAB: {st}; raised {short_date(tk['created'])}.")
    doc.blank()
    abbreviations(doc, ["CAB", "CHUB", "CLARA"])
    distribution(doc, m["attendees"], d, extra=["CAB mailbox", "Service desk (for the change calendar)"])
    return doc


# =============================================================================================
# TX034 – Wave 1 go/no-go (MTG-011, 2026-09-11)
# =============================================================================================

def tx034():
    fid, mid = "TX034", "MTG-011"
    r = _r(fid)
    m = meeting(mid)
    d = m["date"]
    doc = _doc(fid, width=96)
    end = add_minutes(m["start_time"], m["duration_minutes"])
    chair, ak = person("P004", d), person("P048", d)
    doc.line("# Programme Skerry – Wave 1 Go/No-Go – Minutes")
    doc.blank()
    spans = meta(doc, [
        ("Forum", "Programme Skerry Steering Committee (go/no-go session)"),
        ("Date", long_date(d)),
        ("Time", f"{m['start_time']}–{end}"),
        ("Chair", f"{chair.name}, {chair.title}"),
        ("Minutes", f"{ak.name}, {ak.title} (IBM Consulting)"),
        ("Status", "Final"),
    ])
    h(doc, 2, "Attendees")
    att = md_table(doc, ["Name", "Role", "Organisation"],
                   attendee_rows(m["attendees"], d, {"P004": "Chair", "P051": "migration"}))
    meeting_facts(doc, mid, spans[1], att_spans=att)
    apol = apologies_for(mid)
    para(doc, apologies_text(apol, d))

    h(doc, 2, "1. Purpose")
    s = para(doc, "To decide whether Wave 1 – UK motor (PRD-MOT-UK) – proceeds to cut-over as planned on Monday "
                  "14 September 2026.")
    doc.fact(s, "Wave 1 – UK motor (PRD-MOT-UK)", "Wave 1 covers UK motor (PRD-MOT-UK).", "general", "WAVE:MW-1#scope")

    h(doc, 2, "2. Readiness review")
    para(doc, "Arjun Kesavan took the meeting through the go/no-go criteria. Each workstream lead confirmed status.")
    rows = [
        ["Data migration rehearsals", "Three rehearsals completed; final rehearsal reconciliation note issued on "
                                      "25 August 2026 (Callum Fairbairn, IBM)", "Met"],
        ["Reserve parallel run", "CLARA vs reserve-engine parallel run completed on 28 August 2026", "Met"],
        ["Cut-over runbook", "Runbook walked through with operations and Technology Delivery", "Met"],
        ["Business readiness", "UK motor handlers briefed and trained on Claims Hub", "Met"],
        ["Hypercare", "Hypercare rota and daily call agreed for the first two weeks", "Met"],
        ["Defect position", "Accepted by the Head of Claims Hub Product", "Met"],
    ]
    spans_c = md_table(doc, ["Criterion", "Evidence", "Status"], rows)
    doc.fact(spans_c[0], "Three rehearsals completed", "Wave 1 had three migration rehearsals.", "general",
             "WAVE:MW-1#rehearsals")
    doc.fact(spans_c[1], "parallel run completed on 28 August 2026",
             "The reserve parallel run ended on 2026-08-28.", "general", "EVENT:EV-031")
    doc.blank()
    para(doc, "In discussion:")
    bullet(doc, "Priya Raman confirmed Finance was content with the reserve reconciliation evidence from the parallel run.")
    bullet(doc, "Ingrid Ashby confirmed Claims was ready and that UK motor handlers had been briefed on the freeze.")
    bullet(doc, "Neil Haworth confirmed the change freeze was registered with the CAB.")
    bullet(doc, "Aisha Siddiqui confirmed the product backlog for hypercare was prioritised.")
    doc.blank()

    h(doc, 2, "3. Decision")
    s = para(doc, "GO. The Steering Committee approved the Wave 1 (UK motor) cut-over on Monday 14 September 2026, with "
                  "the freeze running from 18:00 on 11 September 2026 to 06:00 on 14 September 2026. Decision taken "
                  "by the chair, Duncan Ferrier.")
    doc.place(s, "tx34_go", "approved the Wave 1 (UK motor) cut-over on Monday 14 September 2026")
    doc.fact(s, "the freeze running from 18:00 on 11 September 2026 to 06:00 on 14 September 2026",
             "The Wave 1 freeze ran from 2026-09-11 18:00 to 2026-09-14 06:00.", "needle", "DECISION:DEC-009")

    h(doc, 2, "4. Actions")
    actions_table(doc, [
        ["GNG-1", "Issue the go notice to all cut-over participants", ak.name, "11 Sep 2026", "Done"],
        ["GNG-2", "Start the freeze at 18:00 and confirm to the cut-over bridge", person("P032", d).name,
         "11 Sep 2026", "Open"],
        ["GNG-3", "Run the hypercare daily call from 14 September", person("P017", d).name, "14 Sep 2026", "Open"],
        ["GNG-4", "Report cut-over completion to the Steering Committee", ak.name, "14 Sep 2026", "Open"],
    ])
    closing(doc, r, end)
    papers(doc, [
        "Wave 1 go/no-go pack (PMO)",
        "Final rehearsal reconciliation summary (IBM data migration, 25 August 2026)",
        "Reserve parallel run close-out (Reserving)",
        "Cut-over runbook v1.0 (Technology Delivery)",
    ])
    distribution(doc, m["attendees"] + apol, d, extra=["Wave 1 cut-over participants"])
    return doc


# =============================================================================================
# TX035 – Claims Fraud Forum (MTG-012, 2026-03-12)
# =============================================================================================

def tx035():
    fid, mid = "TX035", "MTG-012"
    r = _r(fid)
    m = meeting(mid)
    d = m["date"]
    doc = _doc(fid)
    end = add_minutes(m["start_time"], m["duration_minutes"])
    chair, hl = person("P008", d), person("P054", d)
    doc.line("# Claims Fraud Forum – Minutes")
    doc.blank()
    spans = meta(doc, [
        ("Forum", "Claims Fraud Forum"),
        ("Date", long_date(d)),
        ("Time", f"{m['start_time']}–{end}"),
        ("Location", f"{pick(r, PH.ROOMS)}, {pick(r, PH.DIAL_IN)}"),
        ("Chair", f"{chair.name}, {chair.title}"),
        ("Minutes", f"{hl.name} (IBM Consulting)"),
        ("Status", "Final – approved by the chair"),
    ])
    doc_control(doc, [
        ["0.1", "12 Mar 2026", hl.name, "Draft"],
        ["1.0", "12 Mar 2026", chair.name, "Approved"],
    ])
    h(doc, 2, "Attendees")
    att = md_table(doc, ["Name", "Role", "Organisation"], attendee_rows(m["attendees"], d, {"P008": "Chair"}))
    meeting_facts(doc, mid, spans[1], att_spans=att)
    apol = apologies_for(mid)

    h(doc, 2, "1. Opening")
    standard_opening(doc, r, apologies_text(apol, d))

    h(doc, 2, "2. NISA Circular 2026/04 – Fair Treatment in Fraud Referral")
    s = para(doc, "Ruth Okafor summarised NISA Circular 2026/04, published on 20 November 2025 and effective from "
                  "1 April 2026. Its main requirements are:")
    doc.fact(s, "published on 20 November 2025 and effective from 1 April 2026",
             "NISA Circular 2026/04 was published on 2025-11-20 and is effective from 2026-04-01.", "general",
             "CIRCULAR:CIRC-2026-04#effective")
    reqs = [
        "§3.1 – no claim may be declined, reduced or repudiated on an automated score alone; a documented human "
        "review is required;",
        "§3.2 – the customer must be told in writing within 10 business days of referral that the claim is subject "
        "to additional checks, with a deferral possible where a tipping-off risk is certified;",
        "§3.3 – score-based cut-offs must be calibrated and documented, and on a 0–100 scale must not exceed 65;",
        "§3.4 – a quarterly NISA-FR1 fraud referral return within 30 days after each quarter end;",
        "§3.5 – referral records retained for 7 years.",
    ]
    rs = [bullet(doc, t) for t in reqs]
    doc.fact(rs[3], "a quarterly NISA-FR1 fraud referral return within 30 days after each quarter end",
             "Circular 2026/04 §3.4: submit the quarterly NISA-FR1 return within 30 days after each quarter end.",
             "general", "CIRCULAR:CIRC-2026-04#requirements")
    doc.blank()
    para(doc, "Hannah Lyle confirmed that the approved fraud-referral BRD (v1.0) maps each requirement to a rule and a "
              "system change in CLARA and Claims Hub.")

    h(doc, 2, "3. Rule set for approval")
    para(doc, "The Forum reviewed the rule set prepared to implement the Circular:")
    v = lambda rid, n: W.rules[rid]["versions"][n - 1]
    names = lambda pids: ", ".join(person(p, d).name for p in pids)
    rows = [
        ["BR-FRD-031", "v1", "Refer a claim to SIU when the Sentinel score is 65 or more (all tiers)",
         names(v("BR-FRD-031", 1)["approved_by"])],
        ["BR-FRD-032", "v2", "Notify the customer in writing within 10 business days of referral, unless deferred under BR-FRD-036",
         names(v("BR-FRD-032", 2)["approved_by"])],
        ["BR-FRD-033", "v1", "No decline, reduction or repudiation on an automated fraud score alone; documented human review by SIU",
         names(v("BR-FRD-033", 1)["approved_by"])],
        ["BR-FRD-034", "v1", "Submit NISA-FR1 within 30 calendar days after quarter end; first return Q2 2026, due 30 July 2026",
         names(v("BR-FRD-034", 1)["approved_by"])],
        ["BR-FRD-035", "v2", "SIU triage of a new referral within 3 business days",
         names(v("BR-FRD-035", 2)["approved_by"])],
        ["BR-FRD-036", "v1", W.rules["BR-FRD-036"]["title"] + " – text as in the rules register",
         names(v("BR-FRD-036", 1)["approved_by"])],
    ]
    rspans = md_table(doc, ["Rule", "Version", "Summary", "Approvers"], rows)
    doc.fact(rspans[0], "Refer a claim to SIU when the Sentinel score is 65 or more (all tiers)",
             "BR-FRD-031 v1: refer at a Sentinel score of 65 or more for all tiers.", "general", "RULE:BR-FRD-031@v1#text")
    doc.fact(rspans[3], "first return Q2 2026, due 30 July 2026",
             "BR-FRD-034: the first NISA-FR1 return is for Q2 2026, due 2026-07-30.", "general",
             "RULE:BR-FRD-034@v1#parameters.first_due")
    doc.fact(rspans[4], "SIU triage of a new referral within 3 business days",
             "BR-FRD-035 v2: SIU must triage a new referral within 3 business days.", "general",
             "RULE:BR-FRD-035@v2#parameters.business_days")
    doc.blank()
    para(doc, "In discussion:")
    bullet(doc, "Oskar Lindgren reported that the calibration of Sentinel for the 65 cut-off would be completed and "
                "documented before 1 April, as §3.3 requires.")
    bullet(doc, "Rachel Dunmore welcomed the shorter triage standard and confirmed SIU rotas would be adjusted.")
    bullet(doc, "Ingrid Ashby asked that the handler guidance on customer notices is issued with the system change.")
    doc.blank()

    h(doc, 2, "4. Superseded and withdrawn rules")
    s = bullet(doc, "BR-FRD-012 v2 (referral at a score of 70 or more) is superseded by BR-FRD-031 from 1 April 2026.")
    doc.fact(s, "BR-FRD-012 v2 (referral at a score of 70 or more) is superseded by BR-FRD-031 from 1 April 2026",
             "BR-FRD-012 v2 (threshold 70) was superseded by BR-FRD-031 from 2026-04-01.", "temporal",
             "RULE:BR-FRD-012@v2#parameters.threshold")
    s = bullet(doc, "BR-FRD-019 (automatic decline on a very high score) is withdrawn from 1 April 2026, because "
                    "§3.1 prohibits adverse decisions on an automated score alone.")
    doc.fact(s, "BR-FRD-019 (automatic decline on a very high score) is withdrawn from 1 April 2026",
             "BR-FRD-019 (auto-decline) was withdrawn from 2026-04-01 under Circular 2026/04 §3.1.", "general",
             "RULE:BR-FRD-019@v2#status")
    doc.blank()

    h(doc, 2, "Decisions")
    s = para(doc, "The Forum approved BR-FRD-031 v1, BR-FRD-032 v2, BR-FRD-033, BR-FRD-034, BR-FRD-035 v2 and "
                  "BR-FRD-036 v1, effective 1 April 2026.")
    doc.place(s, "tx35_forum", "approved BR-FRD-031 v1, BR-FRD-032 v2, BR-FRD-033, BR-FRD-034, BR-FRD-035 v2 and "
                               "BR-FRD-036 v1, effective 1 April 2026")

    h(doc, 2, "5. Any other business")
    para(doc, pick(r, PH.AOB))
    closing(doc, r, end)

    h(doc, 2, "Actions")
    actions_table(doc, [
        ["FF-03-1", "Complete and document the Sentinel calibration for the 65 cut-off", "Oskar Lindgren",
         "20 Mar 2026", "Open"],
        ["FF-03-2", "Publish the approved rules in the rules register", chair.name, "19 Mar 2026", "Open"],
        ["FF-03-3", "Issue handler guidance on the customer notice", "Ruth Okafor", "27 Mar 2026", "Open"],
        ["FF-03-4", "Adjust SIU triage rota for the 3-business-day standard", "Rachel Dunmore", "27 Mar 2026", "Open"],
    ])
    papers(doc, [
        "NISA Circular 2026/04 – summary for the Forum (Compliance)",
        "Fraud-referral BRD v1.0 (approved) – Hannah Lyle",
        "Proposed rule set for 1 April 2026 (Counter-Fraud & SIU)",
    ])
    rule_appendix(doc, [("BR-FRD-031", 1), ("BR-FRD-032", 2), ("BR-FRD-033", 1), ("BR-FRD-034", 1),
                        ("BR-FRD-035", 2), ("BR-FRD-036", 1)], d, "Appendix – rule set as approved")
    abbreviations(doc, ["SIU", "FR1", "NISA", "BRD", "CLARA"])
    distribution(doc, m["attendees"] + apol, d)
    return doc


# =============================================================================================
# TX036 – Design Authority 2026-02-03 (MTG-013)
# =============================================================================================

def tx036():
    fid, mid = "TX036", "MTG-013"
    r = _r(fid)
    m = meeting(mid)
    d = m["date"]
    doc = _doc(fid, width=100)
    end = add_minutes(m["start_time"], m["duration_minutes"])
    chair = person("P018", d)
    doc.line("# Design Authority – Minutes")
    doc.blank()
    spans = meta(doc, [
        ("Date", long_date(d)),
        ("Time", f"{m['start_time']}–{end}"),
        ("Chair", f"{chair.name}, {chair.title}"),
        ("Location", f"{pick(r, PH.ROOMS)}, {pick(r, PH.DIAL_IN)}"),
        ("Status", "Final"),
    ])
    h(doc, 2, "Attendees")
    att = md_table(doc, ["Name", "Role", "Organisation"], attendee_rows(m["attendees"], d, {"P018": "Chair"}))
    meeting_facts(doc, mid, spans[0], att_spans=att)
    apol = apologies_for(mid)
    para(doc, apologies_text(apol, d))

    h(doc, 2, "1. ADR-019 – Rename reserve-svc to reserve-engine")
    s = para(doc, "Daniel Achebe presented ADR-019, which renames reserve-svc to reserve-engine. The ADR's consequences, "
                  "effective 10 February 2026, are: repository path services/reserve-engine, Terraform module "
                  "reserve-engine, and the event reserve.changed.v2.")
    doc.fact(s, "repository path services/reserve-engine, Terraform module reserve-engine, and the event reserve.changed.v2",
             "ADR-019 consequences: repo path services/reserve-engine, Terraform module reserve-engine, event "
             "reserve.changed.v2.", "general", "ADR:ADR-019#consequences")
    para(doc, "In discussion:")
    bullet(doc, "Nadia Petrovic confirmed the coding standards and service templates will be updated in the same change.")
    bullet(doc, "Elin Fosse asked that architecture diagrams and the service catalogue use the new name from the "
                "effective date, with the old name noted as an alias.")
    s = bullet(doc, "The rename work is tracked as CHUB-233, assigned to Daniel Achebe.")
    doc.fact(s, "tracked as CHUB-233, assigned to Daniel Achebe",
             "The reserve-svc to reserve-engine rename was tracked as CHUB-233 (assignee Daniel Achebe).", "general",
             "TICKET:CHUB-233#assignee")
    doc.blank()
    s = para(doc, "Decision: the Design Authority approved the rename of reserve-svc to reserve-engine, effective "
                  "10 February 2026 (ADR-019).")
    doc.place(s, "tx36_da", "approved the rename of reserve-svc to reserve-engine, effective 10 February 2026")

    h(doc, 2, "2. Reserve parallel run – architecture readiness")
    s = para(doc, "Elin Fosse summarised readiness for the reserve parallel run planned from 2 March 2026. Under "
                  "ADR-012, CLX-IF-042 records are republished to claims.reserve.movement.v1 by the CLX-IF-049 bridge, "
                  "and the service consumes them for the parallel run and, later, for Wave 2 synchronisation.")
    doc.fact(s, "CLX-IF-042 records are republished to claims.reserve.movement.v1 by the CLX-IF-049 bridge",
             "ADR-012: CLX-IF-042 records are republished to claims.reserve.movement.v1 (CLX-IF-049); reserve-engine "
             "consumes them for the parallel run and Wave 2 sync.", "general", "ADR:ADR-012#consequences")
    generic_points(doc, r, 2, impl=True)

    h(doc, 2, "3. ADR register housekeeping")
    para(doc, "The chair asked owners of proposed ADRs older than two months to confirm whether they are still "
              "active. The register will be reviewed again at the next Design Authority.")
    h(doc, 2, "4. Any other business")
    para(doc, pick(r, PH.AOB))
    closing(doc, r, end)
    h(doc, 2, "Actions")
    actions_table(doc, [
        ["DA-02-1", "Complete the rename under CHUB-233 for 10 February", person("P041", d).name, "10 Feb 2026", "Open"],
        ["DA-02-2", "Update architecture diagrams and the service catalogue", person("P049", d).name, "13 Feb 2026", "Open"],
        ["DA-02-3", "Update service templates and coding standards", person("P053", d).name, "13 Feb 2026", "Open"],
    ])
    h(doc, 2, "ADRs referred to")
    for a in ["ADR-019", "ADR-012", "ADR-017"]:
        ad = W.adrs[a]
        bullet(doc, f"{a} – {ad['title']} ({ad['status']}, {short_date(ad['date'])})")
    doc.blank()
    abbreviations(doc, ["ADR", "CLARA", "CHUB"])
    distribution(doc, m["attendees"] + apol, d, extra=["Architecture team"])
    return doc


# =============================================================================================
# TX037 – Design Authority 2025-10-21 (MTG-014)
# =============================================================================================

def tx037():
    fid, mid = "TX037", "MTG-014"
    r = _r(fid)
    m = meeting(mid)
    d = m["date"]
    doc = _doc(fid)
    end = add_minutes(m["start_time"], m["duration_minutes"])
    chair = person("P018", d)
    svc = W.service_name("reserve-engine", d)   # 'reserve-svc' on this date
    doc.line("# Design Authority – Minutes")
    doc.blank()
    spans = meta(doc, [
        ("Date", long_date(d)),
        ("Time", f"{m['start_time']}–{end}"),
        ("Chair", f"{chair.name}, {chair.title}"),
        ("Location", f"{pick(r, PH.ROOMS)}, {pick(r, PH.DIAL_IN)}"),
        ("Status", "Final"),
    ])
    h(doc, 2, "Attendees")
    att = md_table(doc, ["Name", "Role", "Organisation"], attendee_rows(m["attendees"], d, {"P018": "Chair"}))
    meeting_facts(doc, mid, spans[0], att_spans=att)
    apol = apologies_for(mid)
    para(doc, apologies_text(apol, d))

    h(doc, 2, "1. Previous actions")
    para(doc, pick(r, PH.ACTIONS_REVIEWED))

    h(doc, 2, "2. Reserve synchronisation approach")
    s = para(doc, "Marcus Oduya presented the options for keeping " + svc + " in step with CLARA reserves during the "
                  "parallel run and up to Wave 2. ADR-005 (10 March 2025) proposed change data capture on "
                  "CLR.T_RESERVE_MOVEMENT. Analysis since then showed that CDC on that table is incomplete, because "
                  "CLRGL090 updates bypass the movement table.")
    doc.fact(s, "CLRGL090 updates bypass the movement table",
             "ADR-005 (CDC on CLR.T_RESERVE_MOVEMENT) was superseded because CLRGL090 updates bypass the movement table.",
             "general", "ADR:ADR-005#consequences")
    s = para(doc, "The proposed replacement is the CLX-IF-049 batch-to-event bridge (ADR-012): CLX-IF-042 records are "
                  "republished to the Kafka topic claims.reserve.movement.v1, and " + svc + " consumes them for the "
                  "parallel run and Wave 2 synchronisation. ADR-017 records the replacement of CDC.")
    doc.fact(s, svc + " consumes them for the parallel run and Wave 2 synchronisation",
             f"On 2025-10-21 the reserve service was still called {svc}; it consumes claims.reserve.movement.v1 "
             "for the parallel run and Wave 2 sync (ADR-012).", "temporal", "SERVICE:reserve-engine#renames")
    para(doc, "In discussion:")
    bullet(doc, "Derek Ollerton agreed that the CDC design could not see changes made outside the movement table and "
                "supported withdrawing it.")
    bullet(doc, "Henrik Vestergaard confirmed the Integration Platform team will own the bridge alongside CLX-IF-042.")
    bullet(doc, "Elin Fosse asked that the reconciliation design for the parallel run is reviewed once the bridge "
                "is built.")
    doc.blank()
    s = para(doc, "Decision: the Design Authority approved replacing CDC (ADR-005) with the CLX-IF-049 batch-to-event "
                  "bridge (ADR-012, ADR-017). ADR-005 is marked superseded by ADR-017.")
    doc.place(s, "tx37_da", "approved replacing CDC (ADR-005) with the CLX-IF-049 batch-to-event bridge (ADR-012, ADR-017)")

    h(doc, 2, "3. Interface catalogue standards")
    para(doc, "Henrik Vestergaard proposed that new interface entries record owner, criticality and dependencies "
              "before they are approved. Members agreed; the template will be updated.")
    h(doc, 2, "4. Any other business")
    para(doc, pick(r, PH.AOB))
    closing(doc, r, end)
    h(doc, 2, "Actions")
    actions_table(doc, [
        ["DA-10-1", "Update ADR-005 status to superseded and publish ADR-012 and ADR-017", chair.name, "24 Oct 2025", "Open"],
        ["DA-10-2", "Produce the CLX-IF-049 bridge design for review", person("P050", d).name, "4 Nov 2025", "Open"],
        ["DA-10-3", "Update the interface catalogue template", person("P031", d).name, "4 Nov 2025", "Open"],
    ])
    h(doc, 2, "ADRs referred to")
    for a in ["ADR-005", "ADR-012", "ADR-017"]:
        ad = W.adrs[a]
        st = "superseded by ADR-017 at this meeting" if a == "ADR-005" else "accepted at this meeting"
        bullet(doc, f"{a} – {ad['title']} ({st})")
    doc.blank()
    abbreviations(doc, ["ADR", "CDC", "CLARA"])
    distribution(doc, m["attendees"] + apol, d, extra=["Architecture team"])
    return doc


# =============================================================================================
# TX038 – Programme Skerry decision log (2026-11-10)
# =============================================================================================

RELATED = {
    "DEC-001": "ADR-001 records the strangler-fig approach; migration waves MW-0, MW-1 and MW-2 follow from it.",
    "DEC-003": "Follows the incident bridge for INC-2025-0412.",
    "DEC-005": "Taken at the same reserving design review as DEC-006.",
    "DEC-006": "Approved by the Reserving Committee as DEC-008.",
    "DEC-007": "BR-FRD-031 and BR-FRD-036 were revised by DEC-014 and DEC-015.",
    "DEC-008": "Implements the proposal in DEC-006.",
    "DEC-009": "Wave 1 cut-over went ahead on 14 September 2026.",
    "DEC-010": "Taken at the same Steering Committee as DEC-011.",
    "DEC-014": "Revises BR-FRD-031 v1 (approved under DEC-007).",
    "DEC-015": "Revises BR-FRD-036 v1 (approved under DEC-007).",
    "DEC-016": "Considered at the same workshop as DEC-014 and DEC-015.",
    "DEC-017": "ADR-005 superseded; CLX-IF-049 went live on 12 December 2025.",
    "DEC-018": "Rename tracked as CHUB-233.",
}


def _record_titles(mid: str) -> str:
    recs = W.meetings[mid].get("records", []) if mid else []
    return "; ".join(W.anchor(f)["title"] for f in recs if f in W.anchors_by_id)


def tx038():
    fid = "TX038"
    r = _r(fid)
    doc = _doc(fid)
    asof = W.anchor(fid)["date"]
    ak = person("P048", asof)
    alld = [x for x in sorted(W.decisions.values(), key=lambda x: (x["date"], x["id"])) if x["date"] <= asof]
    # decisions whose record is reserved for another file are listed by id only
    restricted = [x["id"] for x in alld if not W.may_state(fid, f"DECISION:{x['id']}")]
    decs = [x for x in alld if x["id"] not in restricted]
    doc.line("# Programme Skerry – Decision Log")
    doc.blank()
    kv_table(doc, [
        ("Owner", f"{ak.name}, {ak.title} (Programme Management Office)"),
        ("Sponsor", f"{person('P004', asof).name}, {person('P004', asof).title}"),
        ("Last updated", short_date(asof)),
        ("Entries", str(len(decs))),
        ("Classification", "Internal"),
    ])
    doc_control(doc, [
        ["1.0", "20 Jan 2025", ak.name, "Log created after programme kick-off"],
        ["2.0", "15 Sep 2025", ak.name, "Restructured by forum; re-organisation titles applied"],
        ["2.6", "12 Feb 2026", ak.name, "Design Authority decisions added"],
        ["3.1", "21 Sep 2026", ak.name, "Wave 1 go/no-go and Fraud Rules Workshop decisions added"],
        ["3.4", "10 Nov 2026", ak.name, "Steering Committee (October) decisions added; log re-baselined"],
    ])
    h(doc, 2, "How to use this log")
    para(doc, "Each entry records what was decided, by whom, in which forum and where the source record is held. The "
              "log does not replace the minutes; where minutes and log differ, raise it with the PMO. Decisions taken "
              "after the last update date are not yet included.")
    if restricted:
        para(doc, "Regulatory clarifications (" + ", ".join(restricted) + ") are held in the Compliance regulatory "
                  "correspondence log and are not reproduced here.")
    h(doc, 2, "Summary")
    rows = []
    stmt_ok = {x["id"]: W.may_state(fid, f"DECISION:{x['id']}", "statement") for x in decs}
    withheld = "Regulatory clarification – content held in the source record (restricted)"
    for x in decs:
        forum = W.meetings[x["meeting"]]["title"] if x.get("meeting") else "Outside a formal meeting"
        st = x["statement"] if stmt_ok[x["id"]] else withheld
        rows.append([x["id"], x["date"], forum, st[:90] + ("…" if len(st) > 90 else "")])
    md_table(doc, ["ID", "Date", "Forum", "Decision (abridged)"], rows)

    h(doc, 2, "Decision records")
    status_note = {
        "DEC-006": "Closed – approved by the Reserving Committee as DEC-008.",
        "DEC-007": "Approved. BR-FRD-031 v1 and BR-FRD-036 v1 were later superseded by v2 (DEC-014, DEC-015).",
        "DEC-011": "Approved. Cut-over planned for 15 February 2027.",
        "DEC-004": "Approved. SUBTRAK retirement target 31 December 2026.",
        "DEC-017": "Approved. ADR-005 superseded by ADR-017.",
    }
    for x in decs:
        h(doc, 3, f"{x['id']} – {short_date(x['date'])}")
        mid = x.get("meeting")
        if mid:
            mt = W.meetings[mid]
            forum = mt["title"] + (f" – {W.committees[mt['forum']]['name']}" if mt.get("forum") else "")
        else:
            forum = "Not taken in a formal meeting (recorded by email / approval note)"
        deciders = "; ".join(f"{person(p, x['date']).name} ({person(p, x['date']).title})" for p in x["decided_by"])
        bullet(doc, f"Forum: {forum}")
        sd = bullet(doc, f"Decided by: {deciders}")
        s = bullet(doc, f"Decision: {x['statement'] if stmt_ok[x['id']] else withheld}")
        refs = x.get("refs") or []
        if refs:
            bullet(doc, "References:")
            for rf in refs:
                bullet(doc, ref_label(fid, rf, asof), mark="    - ")
        else:
            bullet(doc, "References: none recorded")
        rel = RELATED.get(x["id"])
        if rel:
            bullet(doc, f"Related: {rel}")
        rec = _record_titles(mid) if mid else ""
        bullet(doc, f"Source record: {rec or 'Approval email held by the PMO'}")
        bullet(doc, f"Status: {status_note.get(x['id'], 'Approved.')}")
        doc.blank()
        if stmt_ok[x["id"]]:
            doc.fact(s, x["statement"], f"{x['id']} ({x['date']}): {x['statement']}", "needle",
                     f"DECISION:{x['id']}#statement")
        if x["id"] == "DEC-010":
            doc.fact(sd, "Priya Raman (Chief Financial Officer)",
                     "DEC-010 (£1.8m Wave 2 contingency drawdown) was decided by Priya Raman, CFO, with Duncan Ferrier.",
                     "alias_use", "DECISION:DEC-010#decided_by")
    h(doc, 2, "Change control")
    para(doc, "Additions are made by the PMO after each forum. Corrections to an entry require the agreement of the "
              "forum chair and are noted in the document control table.")
    return doc


# =============================================================================================
# TX040 – Wave 1 retrospective (2026-09-25)
# =============================================================================================

def tx040():
    fid = "TX040"
    r = _r(fid)
    d = W.anchor(fid)["date"]
    doc = _doc(fid, width=100)
    ak = person("P048", d)
    doc.line("# Wave 1 Retrospective")
    doc.blank()
    kv_table(doc, [
        ("Date", long_date(d)),
        ("Facilitator", f"{ak.name}, {ak.title} (IBM Consulting)"),
        ("Format", "What went well / What went wrong / What we will change / Actions"),
        ("Scope", "Wave 1 – UK motor cut-over, rehearsals and first two weeks of hypercare"),
        ("Status", "Final"),
    ])
    h(doc, 2, "Contributors")
    contrib = ["P017", "P051", "P016", "P026", "P042", "P041", "P040", "P032", "P022", "P035"]
    for p in contrib:
        pp = person(p, d)
        org = "IBM" if pp.employer == "ORG-IBM" else "Corvane"
        bullet(doc, f"{pp.name} – {pp.title} ({org})")
    doc.blank()
    para(doc, "Note: two contributors share the name Callum Fairbairn – one is IBM's Data Migration Lead, the other "
              "leads the Motor Claims team in Leeds. Comments are attributed by role below.")

    h(doc, 2, "Context")
    s = para(doc, "Wave 1 moved UK motor (PRD-MOT-UK) from CLARA to Claims Hub on 14 September 2026, after three "
                  "rehearsals and a freeze from 18:00 on 11 September to 06:00 on 14 September. The reserve parallel "
                  "run between CLARA and reserve-engine had ended on 28 August 2026.")
    doc.fact(s, "Wave 1 moved UK motor (PRD-MOT-UK) from CLARA to Claims Hub on 14 September 2026",
             "Wave 1 (UK motor, PRD-MOT-UK) cut over to Claims Hub on 2026-09-14.", "general", "WAVE:MW-1#date")

    h(doc, 2, "Cut-over weekend at a glance")
    md_table(doc, ["When", "What"], [
        ["Fri 11 Sep 2026, 16:00", "Go/no-go: GO given by the Steering Committee"],
        ["Fri 11 Sep 2026, 18:00", "Freeze starts in CLARA and Claims Hub"],
        ["Sat 12 – Sun 13 Sep", "Migration run, reconciliation and business verification"],
        ["Mon 14 Sep 2026, 06:00", "Freeze ends; UK motor handled in Claims Hub"],
        ["Mon 14 Sep 2026, 09:20", "INC-2026-0914 opened (duplicate payment instructions)"],
        ["Mon 14 Sep 2026, 15:45", "INC-2026-0914 resolved for new payments"],
        ["Wed 16 Sep 2026", "CHUB-371 fix released"],
        ["Fri 18 Sep 2026", "All duplicate payments recalled"],
    ])
    doc.blank()

    h(doc, 2, "What went well")
    wins = [
        "The freeze held: no unplanned production changes went into CLARA or Claims Hub during the window.",
        "Rehearsals paid off – the cut-over steps ran in the rehearsed order, and the migration lead's "
        "reconciliation approach was reused unchanged on the night.",
        "The parallel run gave Finance and Reserving confidence in reserve-engine before go-live.",
        "Floor-walkers in Leeds were visible from the first morning and handlers knew where to go for help.",
        "The hypercare daily call kept issues short and well owned.",
        "Batch Operations and the Legacy Claims Platforms team closed the CLARA side cleanly.",
    ]
    for t in wins:
        bullet(doc, t)
    doc.blank()

    h(doc, 2, "What went wrong")
    s = bullet(doc, "Duplicate payments on cut-over day: 18 claims were paid twice, totalling £41,236.50 "
                    "(INC-2026-0914). payment-orchestrator retried on a Corvane Payments Gateway timeout without an "
                    "idempotency key.")
    doc.place(s, "tx40_dup", "18 claims were paid twice, totalling £41,236.50")
    doc.fact(s, "payment-orchestrator retried on a Corvane Payments Gateway timeout without an idempotency key",
             "INC-2026-0914 root cause: payment-orchestrator retried on a CPG timeout without an idempotency key.",
             "general", "INCIDENT:INC-2026-0914#root_cause")
    s = bullet(doc, "The fix (CHUB-371) was released on 16 September and all duplicate payments were recalled by "
                    "18 September, but Payments Operations spent two days on manual recalls.")
    doc.fact(s, "all duplicate payments were recalled by 18 September",
             "All INC-2026-0914 duplicate payments were recalled by 2026-09-18; fix CHUB-371 resolved 2026-09-16.",
             "general", "INCIDENT:INC-2026-0914#impact")
    others = [
        "The cut-over bridge was noisy: too many people on one call made decisions slower than they needed to be.",
        "Some handler questions on the first morning were about work queues rather than the system itself; the "
        "briefing material had not covered queue changes in enough depth.",
        "Status updates to the wider business were later than planned on the Sunday afternoon.",
    ]
    for t in others:
        bullet(doc, t)
    doc.blank()

    h(doc, 2, "What we will change for Wave 2")
    s = para(doc, "Wave 2 is planned for 15 February 2027 and covers UK home, commercial and liability plus Norway and "
                  "Sweden. Changes agreed:")
    doc.fact(s, "Wave 2 is planned for 15 February 2027",
             "Wave 2 is planned for 2027-02-15.", "general", "WAVE:MW-2#date")
    for t in [
        "Idempotency to be confirmed for every payment path as an explicit go/no-go criterion.",
        "A smaller decision bridge with workstream leads only, and a separate information call for everyone else.",
        "Handler briefings to include work-queue walkthroughs, with the Nordic teams' feedback built in early.",
        "A fixed schedule for business updates during the cut-over weekend.",
    ]:
        bullet(doc, t)
    doc.blank()

    h(doc, 2, "Actions")
    actions_table(doc, [
        ["R1", "Add payment idempotency evidence to the Wave 2 go/no-go criteria", ak.name, "16 Oct 2026", "Open"],
        ["R2", "Review all payment-orchestrator retry paths", person("P042", d).name, "23 Oct 2026", "Open"],
        ["R3", "Redesign the cut-over bridge structure", person("P032", d).name, "30 Oct 2026", "Open"],
        ["R4", "Extend handler briefings with work-queue walkthroughs", person("P017", d).name, "13 Nov 2026", "Open"],
    ])
    h(doc, 2, "Thanks")
    para(doc, "The facilitator thanked everyone who worked the cut-over weekend, the Leeds motor team for their "
              "patience on the first morning, and Payments Operations for the recall work.")
    distribution(doc, contrib, d, extra=["Programme Skerry Steering Committee members", "Wave 2 workstream leads"])
    return doc


# =============================================================================================
# TX043 – NISA call notes (MTG-010, 2026-01-14)
# =============================================================================================

def tx043():
    fid, mid = "TX043", "MTG-010"
    r = _r(fid)
    m = meeting(mid)
    d = m["date"]
    doc = _doc(fid)
    end = add_minutes(m["start_time"], m["duration_minutes"])
    ro = person("P037", d)
    doc.line("# Notes – NISA call on Circular 2026/04 implementation")
    doc.blank()
    spans = meta(doc, [
        ("Date", long_date(d)),
        ("Time", f"{m['start_time']}–{end} (video call)"),
        ("Notes by", f"{ro.name}, {ro.title}"),
        ("Status", "Final – internal record, not agreed with NISA"),
    ])
    h(doc, 2, "Participants")
    att = md_table(doc, ["Name", "Role", "Organisation"], attendee_rows(m["attendees"], d))
    meeting_facts(doc, mid, spans[0], att_spans=att)

    h(doc, 2, "Purpose")
    para(doc, "Corvane asked for the call to clarify implementation questions on NISA Circular 2026/04 ahead of its "
              "effective date of 1 April 2026.")
    h(doc, 2, "Background")
    para(doc, "The Circular was published on 20 November 2025. Corvane's implementation is led by Compliance, with "
              "Counter-Fraud & SIU owning the referral process and the fraud-referral BRD covering system changes in "
              "CLARA and Claims Hub.")
    h(doc, 2, "Notes")
    s = bullet(doc, "Written notice (§3.2): we asked whether an SMS can count as the written notice to the customer. "
                    "Petter Ulvestad confirmed that an SMS counts as written notice under §3.2 if it is followed by a "
                    "letter within 2 business days.")
    doc.place(s, "tx43_sms", "an SMS counts as written notice under §3.2 if it is followed by a letter within 2 business days")
    s = bullet(doc, "Cut-off (§3.3): NISA expects firms to keep the calibration evidence for any score-based cut-off, "
                    "and reminded us that on a 0–100 scale the cut-off must not exceed 65.")
    bullet(doc, "FR1 return (§3.4): the return is quarterly, within 30 days after quarter end. Questions on "
                "submission mechanics should go to our supervisor, Imogen Thackray.")
    bullet(doc, "No adverse decision on score alone (§3.1): Niall Brannigan outlined that SIU review is documented "
                "for every adverse outcome; no further comment from NISA.")
    doc.blank()
    h(doc, 2, "Follow-up")
    actions_table(doc, [
        ["N1", "Update the customer-notice procedure to allow SMS followed by a letter within 2 business days",
         ro.name, "30 Jan 2026", "Open"],
        ["N2", "Brief SIU on the clarification", person("P008", d).name, "23 Jan 2026", "Open"],
        ["N3", "Reflect the clarification in the fraud-referral BRD", ro.name, "30 Jan 2026", "Open"],
    ])
    return doc


# =============================================================================================
# TX044 – post-mortem INC-2026-0518 (2026-05-20)
# =============================================================================================

def tx044():
    fid = "TX044"
    r = _r(fid)
    d = W.anchor(fid)["date"]
    inc = W.incidents["INC-2026-0518"]
    doc = _doc(fid, width=100)
    nb = person("P008", d)
    doc.line("# Post-mortem – INC-2026-0518")
    doc.blank()
    doc.line(f"**{inc['title']}**")
    doc.blank()
    spans = kv_table(doc, [
        ("Incident", "INC-2026-0518"),
        ("Severity", inc["severity"]),
        ("Detected", "12 May 2026, 10:00"),
        ("Mitigated", "13 May 2026, 16:00"),
        ("Systems", "CLARA – CLRFR040 (batch fraud sweep)"),
        ("Incident owner", f"{nb.name}, {nb.title}"),
        ("Review date", short_date(d)),
        ("Status", "Final"),
    ])
    doc.fact(spans[1], inc["severity"], "INC-2026-0518 was a Sev2 incident.", "general", "INCIDENT:INC-2026-0518#severity")
    h(doc, 2, "Review participants")
    for p in ["P008", "P037", "P016", "P023", "P024", "P028", "P027"]:
        pp = person(p, d)
        bullet(doc, f"{pp.name}, {pp.title}")
    doc.blank()

    h(doc, 2, "Summary")
    para(doc, "On 12 May 2026 Compliance sampling found that the CLARA batch fraud sweep had not referred claims "
              "scoring 65 to 69 since the referral threshold changed to 65 on 1 April 2026 under BR-FRD-031 v1. The "
              "online referral path was not affected.")
    h(doc, 2, "Impact")
    s = para(doc, "37 claims scored 65–69 between 1 April and 12 May 2026 were not referred by the batch path. All 37 "
                  "were referred to SIU manually on 13 May 2026. No customer outcome is known to have been affected; "
                  "SIU triage of the 37 referrals is tracked separately.")
    doc.fact(s, "37 claims scored 65–69 between 1 April and 12 May 2026 were not referred by the batch path",
             "INC-2026-0518 impact: 37 claims scored 65-69 between 2026-04-01 and 2026-05-12 were not referred by the "
             "batch path; referred manually on 2026-05-13.", "needle", "INCIDENT:INC-2026-0518#impact")
    h(doc, 2, "Timeline")
    for t in [
        "12 May 2026 10:00 – Compliance sampling identifies unreferred claims scoring 65–69.",
        "12 May 2026, late morning – Ruth Okafor reports the gap; incident logged as Sev2 with Niall Brannigan as owner.",
        "12 May 2026, afternoon – Legacy Claims Platforms begins analysis of CLRFR040.",
        "13 May 2026 – the 37 claims are referred to SIU manually; CHUB-298 raised for the permanent fix.",
        "13 May 2026 16:00 – incident mitigated; daily Compliance query in place.",
    ]:
        bullet(doc, t)
    doc.blank()
    h(doc, 2, "Root cause")
    s = para(doc, "CLRFR040 still carried the old referral threshold of 70 as a hard-coded working-storage value "
                  "instead of reading it from CLR.T_PARAM. The online program, CLRFR030, reads the parameter and "
                  "referred correctly at 65.")
    doc.fact(s, "instead of reading it from CLR.T_PARAM",
             "INC-2026-0518 root cause: CLRFR040 used a hard-coded threshold instead of reading CLR.T_PARAM; online "
             "CLRFR030 was correct.", "general", "INCIDENT:INC-2026-0518#root_cause")
    h(doc, 2, "Contributing factors")
    for t in [
        "The review asked why the batch path was not caught in testing of the April change; the team will look at "
        "regression coverage for parameter-driven rules in both online and batch programs.",
        "Sampling by Compliance found the issue; there was no automated reconciliation of batch referrals against "
        "scores at the time.",
    ]:
        bullet(doc, t)
    doc.blank()
    h(doc, 2, "Regulatory considerations")
    para(doc, "Ruth Okafor confirmed that customer notices for the 37 referred claims follow the normal BR-FRD-032 v2 "
              "process – written notice within 10 business days of referral unless a deferral is certified – and "
              "that Compliance will keep the incident record with the Circular 2026/04 implementation evidence.")
    h(doc, 2, "What went well")
    for t in [
        "Compliance sampling detected the gap and the incident was raised the same morning.",
        "SIU referred all affected claims the next day.",
    ]:
        bullet(doc, t)
    doc.blank()
    h(doc, 2, "Actions")
    s = para(doc, "Workaround (in place): Compliance runs a daily query for unreferred claims scoring 65–69 until the "
                  "permanent fix is released.")
    doc.place(s, "tx44_workaround", "Compliance runs a daily query for unreferred claims scoring 65–69")
    spans = actions_table(doc, [
        ["PM-1", "Permanent fix to CLRFR040 (CHUB-298)", person("P023", d).name, "To be scheduled", "Open"],
        ["PM-2", "Run the daily Compliance query until the fix is released", person("P037", d).name, "Daily", "In place"],
        ["PM-3", "Review regression coverage for parameter-driven fraud rules", person("P016", d).name,
         "19 Jun 2026", "Open"],
        ["PM-4", "Check other CLARA batch programs for hard-coded rule parameters", person("P024", d).name,
         "19 Jun 2026", "Open"],
    ])
    doc.fact(spans[0], "Permanent fix to CLRFR040 (CHUB-298)",
             "The permanent fix for INC-2026-0518 is CHUB-298, assigned to Keith Barraclough.", "general",
             "TICKET:CHUB-298#assignee")
    h(doc, 2, "Lessons")
    para(doc, "Parameter-driven rules must be tested on every path that applies them. Where a rule exists in both "
              "CLARA and Claims Hub during migration, both implementations need to be in scope of any change.")
    rule_appendix(doc, [("BR-FRD-031", 1), ("BR-FRD-012", 2)], d, "Appendix – rule versions involved")
    distribution(doc, ["P008", "P037", "P016", "P023", "P024", "P028", "P027", "P007"], d)
    return doc


MINUTES = {
    "TX031": tx031, "TX032": tx032, "TX033": tx033, "TX034": tx034, "TX035": tx035, "TX036": tx036,
    "TX037": tx037, "TX038": tx038, "TX040": tx040, "TX043": tx043, "TX044": tx044,
}

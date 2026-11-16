"""Shared builder for the fraud-referral BRD: LD015 (DRAFT v0.3) and LD016 (APPROVED v1.0)."""
from __future__ import annotations

from . import common as C
from . import hub as H
from .core import Ctx, Doc, F, PF, Style, W, long_date, short_date, util
from .prose import Prose


def _reqs(ctx: Ctx, draft: bool) -> list[dict]:
    circ = W.circulars["CIRC-2026-04"]
    r031 = W.rules["BR-FRD-031"]["versions"][0]
    r032d = W.rules["BR-FRD-032"]["versions"][0]
    r032 = W.rules["BR-FRD-032"]["versions"][1]
    r035 = W.rules["BR-FRD-035"]["versions"][1]
    r034 = W.rules["BR-FRD-034"]["versions"][0]
    r005 = W.rules["BR-FRD-005"]["versions"][2]
    r036 = W.rules["BR-FRD-036"]["versions"][0]
    reqs = [
        dict(id="FR-REQ-001", title="No adverse decision on the score alone",
             text="No claim may be declined, reduced or repudiated on the basis of the Sentinel score alone; every adverse "
                  "outcome requires a documented human review.", src="Circular §3.1", rule="BR-FRD-033", pri="Must",
             ac=["Adverse outcomes cannot be recorded without a reviewer and a review note.",
                 "MI shows every adverse outcome with its reviewer."]),
        dict(id="FR-REQ-002", title="Record the threshold applied",
             text="Each referral records the referral threshold that applied when the claim was scored.",
             src="Circular §3.3", rule="BR-FRD-031", pri="Must",
             ac=["REF_THRESHOLD_APPLIED is populated for every new referral.", "The value matches the parameter in force on the referral date."]),
        dict(id="FR-REQ-003", title="Calibrated and documented cut-off",
             text="The score-based referral cut-off is calibrated, documented and approved; on the 0–100 scale it does not exceed 65.",
             src="Circular §3.3", rule="BR-FRD-031", pri="Must",
             ac=["Calibration evidence is approved by the Claims Fraud Forum.", "The configured cut-off is not above 65."]),
        dict(id="FR-REQ-004", title="Quarterly NISA-FR1 return",
             text=f"{r034['text']}", src="Circular §3.4", rule="BR-FRD-034", pri="Must",
             ac=["The return can be produced for any quarter from Q2 2026.", "Submission evidence is retained."]),
        dict(id="FR-REQ-005", title="Retention of referral records",
             text="Referral records, notices and deferral decisions are retained for 7 years.", src="Circular §3.5",
             rule=None, pri="Must", ac=["Retention rules are configured for referral, notice and deferral records."]),
        dict(id="FR-REQ-006", title="SIU triage of new referrals", text=r035["text"], src="Circular §3.2 (supporting)",
             rule="BR-FRD-035", pri="Must", ac=["Untriaged referrals older than the standard are reported daily."]),
        dict(id="FR-REQ-007", title="Deferral of the customer notice",
             text=f"The customer notice may be deferred for up to {r036['parameters']['max_deferral_days']} days where SIU "
                  f"certifies a tipping-off risk; deferral decisions are recorded with their reason.",
             src="Circular §3.2", rule="BR-FRD-036", pri="Must",
             ac=["A deferral cannot exceed the maximum period.", "Every deferral has a recorded reason and approver."]),
        dict(id="FR-REQ-008", title="Notice wording",
             text="The customer notice states that the claim is subject to additional checks and does not disclose the "
                  "reason for the referral. Wording is approved by Compliance.", src="Circular §3.2", rule="BR-FRD-032",
             pri="Must", ac=["Templates are approved by Compliance before go-live."]),
        dict(id="FR-REQ-009", title="Management information",
             text="Daily and monthly MI covers referrals by score band and tier, notices due and sent, deferrals and adverse outcomes.",
             src="Corvane MI standard", rule=None, pri="Should", ac=["MI is available from the first day of operation."]),
        dict(id="FR-REQ-010", title="Linked-claims indicator", text=r005["text"], src="Counter-fraud policy",
             rule="BR-FRD-005", pri="Should", ac=["Shared bank accounts and telephone numbers raise the indicator."]),
    ]
    if draft:
        reqs += [
            dict(id="FR-REQ-011", title="Customer notice deadline",
                 text="DRAFT: notify the customer in writing within 5 business days of referral that the claim is subject to additional checks.",
                 src="Circular §3.2", rule="BR-FRD-032 (draft)", pri="Must",
                 ac=["Notices are generated for every referral without a certified deferral.",
                     "The due date is calculated in business days from the referral date."]),
            dict(id="FR-REQ-012", title="Referral threshold",
                 text="Refer a claim to SIU when the Sentinel score is 65 or more.", src="Circular §3.3", rule="BR-FRD-031",
                 pri="Must", ac=["Claims scoring 65 or more are referred on the online and batch paths."]),
            dict(id="FR-REQ-013", title="Option: single threshold of 60",
                 text="Option (to be decided): refer all claims at a Sentinel score of 60 or more. See Appendix B.",
                 src="Workshop proposal", rule=None, pri="TBD", ac=["Decision recorded by the Claims Fraud Forum."]),
            dict(id="FR-REQ-014", title="End of automated declines",
                 text="Automated declines based on the fraud score must cease before the Circular takes effect; the "
                      "technical approach is to be confirmed with Legacy Claims Platforms.", src="Circular §3.1",
                 rule="BR-FRD-033", pri="Must", ac=["No claim is declined by an automated process."]),
            dict(id="FR-REQ-015", title="Threshold parameter",
                 text="The referral threshold is held as a dated parameter so that it can change without code changes.",
                 src="ADR-010", rule="BR-FRD-031", pri="Must", ac=["The threshold can be changed by configuration."]),
            dict(id="FR-REQ-016", title="Claims Hub referral configuration",
                 text="fraud-referral-svc applies the same threshold as CLARA for claims created in Claims Hub.",
                 src="Programme Skerry", rule="BR-FRD-031", pri="Must", ac=["Online and Claims Hub paths give the same result for the same score."]),
            dict(id="FR-REQ-017", title="Notice record",
                 text="A record of each customer notice (due date, sent date, channel, deferral) is kept for MI and audit; "
                      "the data structure is to be agreed in design.", src="Circular §3.2", rule="BR-FRD-032",
                 pri="Must", ac=["Every notice can be traced to its referral."]),
        ]
    else:
        reqs += [
            dict(id="FR-REQ-011", title="Customer notice deadline",
                 text=f"Notify the customer in writing within {r032['parameters']['notice_business_days']} business days of referral "
                      f"that the claim is subject to additional checks (BR-FRD-032 v2), unless the notice is deferred under FR-REQ-007.",
                 src="Circular §3.2", rule="BR-FRD-032 v2", pri="Must",
                 ac=["Notices are generated for every referral without a certified deferral.",
                     "The due date is calculated in business days from the referral date."]),
            dict(id="FR-REQ-012", title="Referral threshold",
                 text=f"Refer a claim to SIU when the Sentinel score is {r031['parameters']['threshold']} or more (BR-FRD-031 v1).",
                 src="Circular §3.3", rule="BR-FRD-031 v1", pri="Must",
                 ac=["Claims scoring 65 or more are referred on the online and batch paths."]),
            dict(id="FR-REQ-014", title="Disable the auto-decline sweep",
                 text="The auto-decline sweep CLRFR140 is disabled from 2026-04-01 (BR-FRD-033).", src="Circular §3.1",
                 rule="BR-FRD-033", pri="Must", ac=["The sweep does not run on or after 1 April 2026."]),
            dict(id="FR-REQ-015", title="Threshold parameter",
                 text="CLR.T_PARAM row FRD_REFER_THRESH = 65 is valid from 2026-04-01 so that the online and batch referral programs read the new value.",
                 src="ADR-010", rule="BR-FRD-031 v1", pri="Must", ac=["The parameter row is in place before 1 April 2026."]),
            dict(id="FR-REQ-016", title="Claims Hub referral configuration",
                 text="fraud-referral-svc holds referral.threshold.default as effective-dated configuration (ADR-020).",
                 src="ADR-020", rule="BR-FRD-031 v1", pri="Must", ac=["Online and Claims Hub paths give the same result for the same score."]),
            dict(id="FR-REQ-017", title="Customer notice table",
                 text="New table CLR.T_FRAUD_NOTIFICATION holds customer notices (live 2026-03-27).", src="Circular §3.2",
                 rule="BR-FRD-032 v2", pri="Must", ac=["Every notice can be traced to its referral."]),
            dict(id="FR-REQ-018", title="Notice scheduler",
                 text="A new batch program, CLRFR060, schedules customer referral notices (job CLRNFR02).",
                 src="Circular §3.2", rule="BR-FRD-032 v2", pri="Must", ac=["Notices due on a business day are issued that day."]),
            dict(id="FR-REQ-019", title="Deferral approval transaction",
                 text="A new online transaction, CLRFR120, records and approves deferrals of the customer notice.",
                 src="Circular §3.2", rule="BR-FRD-036 v1", pri="Must", ac=["Deferrals are recorded with reason and approver."]),
            dict(id="FR-REQ-020", title="Notice templates",
                 text="Notices are issued through notification-svc and Notify using templates FRN01 (letter) and FRN02 (SMS) (ADR-014).",
                 src="ADR-014", rule="BR-FRD-032 v2", pri="Must", ac=["Templates are approved by Compliance."]),
        ]
    return reqs


def build_brd(fid: str, draft: bool) -> Doc:
    ctx = Ctx(fid)
    date = ctx.date
    pr = Prose(util.rng(f"{fid}:prose"), date=ctx.date)
    ver = "0.3" if draft else "1.0"
    status = "DRAFT – for review" if draft else "Approved"
    title = "BRD – Fraud Referral Changes (NISA Circular 2026/04)"
    doc = Doc(ctx, title=title, doc_id="SKR-BRD-FRD-04", version=ver, status=status,
              subtitle=("DRAFT v0.3 – not approved" if draft else "Version 1.0 – approved"),
              style=Style(font="Calibri", heading_font="Calibri Light", accent="7B2C2C" if draft else "1F4E79",
                          accent2="F2DCDB" if draft else "DEEAF6", size=11, line_spacing=1.3),
              header_left=title, header_right=("DRAFT v0.3 – NOT APPROVED" if draft else "v1.0 APPROVED"),
              watermark="DRAFT" if draft else None)
    if draft:
        doc.header_facts.append(F("draft", "LD015 is marked DRAFT v0.3 (not approved) in every page header.",
                                  "DRAFT v0.3 – NOT APPROVED", f"ANCHOR:{fid}#status"))
    else:
        doc.header_facts.append(F("approved", "LD016 is the approved v1.0 of the BRD (page header).", "v1.0 APPROVED",
                                  f"ANCHOR:{fid}#status"))
    circ = W.circulars["CIRC-2026-04"]
    doc.title_page(C.control_rows(ctx, doc, owner="P008", extra=[["Business owner", ctx.person("P008")],
                                                                 ["Regulatory driver", f"{circ['ref']} – {circ['title']}"]]))
    hist = [("0.1", 34 if draft else 64, "Initial requirements from the Circular gap analysis"),
            ("0.2", 20 if draft else 50, "Workshop outputs with SIU, Compliance and Claims Operations"),
            ("0.3", 0 if draft else 30, "Customer notice and options added for review")]
    if not draft:
        hist += [("0.9", 12, "Review comments resolved; notice period and threshold confirmed"),
                 ("1.0", 0, "Approved at the Claims Fraud Forum")]
    C.version_history(ctx, doc, hist)
    if draft:
        doc.table(["Name", "Title", "Role", "Status"],
                  [[ctx.name("P008"), ctx.title("P008"), "Business owner", "Review pending"],
                   [ctx.name("P005"), ctx.title("P005"), "Approver", "Review pending"],
                   [ctx.name("P037"), ctx.title("P037"), "Compliance reviewer", "Comments received"]],
                  widths=[3.8, 6.0, 3.6, 3.2], caption="Approvals (not yet given)", font_size=8.6,
                  facts=[F("draft", "The draft BRD's approval table shows approvals still pending.", "Review pending",
                           f"ANCHOR:{fid}#status", where=(1, 3))])
    else:
        C.approvals(ctx, doc, [("P008", "Business owner"), ("P005", "Approver (Claims Director)")],
                    caption="Approvals",
                    facts=[F("approved", "The approved BRD v1.0 is signed by Niall Brannigan and Ingrid Ashby on 2026-03-12.",
                             "Ingrid Ashby", f"ANCHOR:{fid}#description", where=(2, 0)),
                           F("approved", "Niall Brannigan approves as Head of Counter-Fraud & SIU.", "Head of Counter-Fraud & SIU",
                             "PERSON:P008#titles", where=(1, 1))])
    C.reviewers(ctx, doc, ["P037", "P027", "P028", "P011", "P042", "P016", "P017", "P020"])
    doc.toc(depth=2)

    doc.h(1, "1 Introduction")
    doc.h(2, "1.1 Purpose")
    doc.p(f"This document sets out the business requirements for implementing {circ['ref']} ({circ['title']}) in "
          f"CLARA and Claims Hub. The Circular was published by NISA on {long_date(circ['published'])} and takes effect on "
          f"{long_date(circ['effective'])}.",
          facts=[F("general", "NISA Circular 2026/04 was published 2025-11-20 and is effective 2026-04-01.",
                   f"published by NISA on {long_date(circ['published'])} and takes effect on {long_date(circ['effective'])}",
                   "CIRCULAR:CIRC-2026-04")])
    if draft:
        doc.note("This is a working draft for review. Values marked DRAFT are proposals and have not been approved. "
                 "Do not use this version for build or test.", label="DRAFT")
    doc.p(pr.para(["intro", "brd"], n=3, topic="the fraud referral requirements"))
    doc.h(2, "1.2 Scope")
    doc.bullets(["Referral threshold and its configuration in CLARA and Claims Hub.",
                 "Customer notification after a referral and the deferral of notices.",
                 "Human review of adverse outcomes and the end of automated declines.",
                 "SIU triage timeliness.", "The quarterly NISA-FR1 return and supporting MI.", "Record retention."])
    doc.h(2, "1.3 Stakeholders")
    st = [(x, r) for x, r in [("P008", "Business owner"), ("P005", "Approver"), ("P037", "Compliance"),
                              ("P027", "Fraud analytics"), ("P028", "SIU investigations"), ("P011", "Claims Operations"),
                              ("P042", "Engineering lead – Fraud & Settlement"), ("P016", "CLARA platform"),
                              ("P020", "Regulatory reporting"), ("P017", "Claims Hub product")]]
    doc.table(["Name", "Title", "Interest"], [[ctx.name(x), ctx.title(x), r] for x, r in st], widths=[4.0, 7.6, 5.0],
              font_size=8.6, caption="Stakeholders")
    doc.p(pr.para("brd", n=3))

    doc.h(1, "2 Regulatory requirements", page_break=True)
    doc.p(f"The Circular was issued by NISA (policy lead {W.name_of(circ['author'], date)}). Its requirements are:")
    doc.table(["Paragraph", "Requirement"], [[r["para"], r["text"]] for r in circ["requirements"]], widths=[2.2, 14.4],
              caption=f"{circ['ref']} requirements",
              facts=[F("general", "Circular 2026/04 §3.3: cut-off must not exceed 65 on a 0–100 scale.",
                       "on a 0–100 scale the cut-off must not exceed 65", "CIRCULAR:CIRC-2026-04#requirements",
                       where=(3, 1))])
    doc.ps(pr.paras(["brd", "governance"], 2))

    doc.h(1, "3 Current state", page_break=True)
    r012 = W.rules["BR-FRD-012"]["versions"][1]
    r019 = W.rules["BR-FRD-019"]["versions"][1]
    doc.p(f"Today a claim is referred to SIU under BR-FRD-012 v2: {r012['text']} The threshold is read from CLR.T_PARAM "
          f"by the online referral program CLRFR030 and the nightly sweep CLRFR040 (job CLRNFR01).",
          facts=[F("general", "Before 2026-04-01 the referral threshold was 70 (BR-FRD-012 v2).", "score is 70 or more",
                   "RULE:BR-FRD-012@v2#parameters.threshold")])
    doc.p(f"Automated declines are made under BR-FRD-019 v2: {r019['text'].split(' Withdrawn')[0]} The sweep runs in job CLRNFR99.")
    doc.p(f"New referrals are triaged by SIU within {W.rules['BR-FRD-035']['versions'][0]['parameters']['business_days']} business days (BR-FRD-035 v1).")
    rows = []
    for sid in W.stages["S5"]["steps"]:
        s = W.steps[sid]
        if sid in ("PS-FRD-03", "PS-FRD-05"):
            continue
        rows.append([sid, s["name"], ctx.a(s["description"]), ", ".join(s["programs"])])
    doc.table(["Step", "Name", "Description", "CLARA programs"], rows, widths=[2.2, 3.6, 7.6, 3.2],
              caption="As-is fraud referral steps", font_size=8.6)
    doc.ps(pr.paras(["brd", "model"], 3))

    doc.h(1, "4 Business requirements", page_break=True)
    reqs = _reqs(ctx, draft)
    rows, facts = [], []
    for i, r in enumerate(reqs, 1):
        rows.append([r["id"], r["title"], r["text"], r["src"], r["pri"]])
        if r["id"] == "FR-REQ-011" and draft:
            facts.append(PF(ctx, "ld15_draft5", "within 5 business days of referral", where=(i, 2)))
        if r["id"] == "FR-REQ-011" and not draft:
            facts.append(PF(ctx, "ld16_approved10", "within 10 business days of referral", where=(i, 2)))
        if r["id"] == "FR-REQ-014" and not draft:
            facts.append(PF(ctx, "ld16_frreq014", "The auto-decline sweep CLRFR140 is disabled from 2026-04-01", where=(i, 2)))
        if r["id"] == "FR-REQ-012":
            facts.append(F("draft" if draft else "approved", f"FR-REQ-012: refer at Sentinel score 65 or more ({'draft' if draft else 'approved'} BRD).",
                           "Sentinel score is 65 or more", "RULE:BR-FRD-031@v1#parameters.threshold", where=(i, 2)))
        if r["id"] == "FR-REQ-017" and not draft:
            facts.append(F("approved", "FR-REQ-017: new table CLR.T_FRAUD_NOTIFICATION holds customer notices (live 2026-03-27).",
                           "New table CLR.T_FRAUD_NOTIFICATION holds customer notices (live 2026-03-27)",
                           "TABLE:CLR.T_FRAUD_NOTIFICATION#created", where=(i, 2)))
        if r["id"] == "FR-REQ-006":
            facts.append(F("general", "FR-REQ-006: SIU must triage a new referral within 3 business days (BR-FRD-035 v2).",
                           "SIU must triage a new referral within 3 business days", "RULE:BR-FRD-035@v2#text", where=(i, 2)))
    doc.table(["ID", "Title", "Requirement", "Source", "Priority"], rows, widths=[2.2, 3.2, 7.6, 2.2, 1.4],
              caption="Requirements summary", font_size=8.2, facts=facts)
    for r in reqs:
        doc.h(2, f"4.{reqs.index(r) + 1} {r['id']} {r['title']}")
        com = None
        if draft and r["id"] == "FR-REQ-011":
            com = {"text": "Is 5 business days achievable for postal notices, and does it match the Circular wording? "
                           "Please check §3.2 before v1.0.", "author": ctx.name("P037"), "initials": "RO"}
        fl = []
        if com:
            fl.append(F("comment", "Compliance reviewer comment on the draft notice period (5 business days).",
                        "Is 5 business days achievable for postal notices", "RULE:BR-FRD-032@v1", where="comment"))
        doc.p(r["text"], comment=com, facts=fl)
        doc.kv([["Source", r["src"]], ["Rule", r["rule"] or "—"], ["Priority", r["pri"]]], widths=(3.0, 13.6), font_size=8.6)
        doc.p("Acceptance criteria:", keep_next=True)
        doc.bullets(r["ac"])
        doc.p("Exceptions and edge cases:", keep_next=True)
        doc.bullets(["Claims notified before the effective date are handled under the rules in force at notification "
                     "unless they are re-scored.", "Manual referrals by handlers follow the same downstream steps as "
                     "score-based referrals."])
        doc.p("Rationale: " + pr.para(["brd"], n=(2, 3)))
        doc.ps(pr.paras(["brd", "governance", "model"], 2 if draft else 3, n=(3, 4)))

    doc.h(1, "5 To-be process", page_break=True)
    rows = []
    for sid in W.stages["S5"]["steps"]:
        s = W.steps[sid]
        sla = s["sla"]["text"]
        if draft and sid == "PS-FRD-03":
            sla = "DRAFT: within 5 business days of referral"
        rows.append([sid, s["name"], ctx.a(s["description"]), sla])
    doc.table(["Step", "Name", "Description", "Target service level"], rows, widths=[2.2, 3.6, 6.8, 4.0],
              caption="To-be fraud referral steps", font_size=8.4)
    doc.ps(pr.paras(["brd", "opmodel"], 3))

    doc.h(2, "5.1 Step narratives")
    for sid in W.stages["S5"]["steps"]:
        s = W.steps[sid]
        doc.h(3, f"{sid} {s['name']}")
        raci = s["raci"]
        doc.kv([["Purpose", ctx.a(s["description"])],
                ["Responsible", ", ".join(ctx.team(t) for t in raci["R"])],
                ["Accountable", ctx.person(raci["A"]) if ctx.employed(raci["A"]) else "—"],
                ["Consulted", ", ".join(ctx.team(t) for t in raci["C"]) or "—"],
                ["Informed", ", ".join(ctx.team(t) for t in raci["I"]) or "—"],
                ["Systems", ", ".join(ctx.sys(x) for x in s["systems"])]], widths=(3.2, 13.4), font_size=8.6)
        doc.ps(pr.paras(["brd", "opmodel"], 2, n=(3, 4)))
    doc.h(1, "6 Business rules", page_break=True)
    doc.p("The referral decision uses the Sentinel score together with the pre-screen indicators below. The indicators "
          "are unchanged by this BRD unless stated in section 4.")
    rows = []
    for rid in sorted(W.rules):
        if not rid.startswith("BR-FRD-0") or rid >= "BR-FRD-019":
            continue
        v = ctx.rule(rid)
        if not v or not ctx.ok(f"RULE:{rid}@v{v['version']}", "text"):
            continue
        rows.append([rid, W.rules[rid]["title"], f"v{v['version']}", ctx.a(v["text"])])
    doc.table(["Rule", "Title", "Version", "Rule text"], rows, widths=[2.2, 4.2, 1.4, 8.8], font_size=8.0,
              caption="Fraud indicators and supporting rules in force")
    doc.ps(pr.paras(["model", "brd"], 2))
    doc.h(1, "7 Scenarios", page_break=True)
    notice = "5" if draft else "10"
    scen = [("SC-01", "Claim scored above the threshold", "A motor claim is scored 72 at triage.",
             ["Claim is referred to SIU on the online path.", f"A customer notice is due within {notice} business days.",
              "SIU triage is due within 3 business days."]),
            ("SC-02", "Claim scored exactly at the threshold", "A home claim is scored 65.",
             ["Claim is referred (65 or more).", "Threshold applied is recorded on the referral."]),
            ("SC-03", "Claim scored below the threshold", "A home claim is scored 64.",
             ["Claim is not referred on the score.", "Indicators may still lead to a manual referral."]),
            ("SC-04", "Tipping-off risk certified", "SIU certifies a tipping-off risk on a referred claim.",
             ["Notice is deferred and the deferral recorded with reason and approver.", "Deferral cannot exceed the maximum period."]),
            ("SC-05", "Adverse outcome proposed", "Investigation recommends declining the claim.",
             ["Decline requires a documented human review.", "No automated decline is possible."]),
            ("SC-06", "Very high score", "A claim is scored 96.",
             ["Claim is referred; no automated decline.", "Human review applies to any adverse outcome."]),
            ("SC-07", "Claim created in Claims Hub", "A digital FNOL is scored in Claims Hub.",
             ["fraud-referral-svc applies the same threshold as CLARA.", "The referral is passed to the SIU Case Manager."]),
            ("SC-08", "Quarter end", "The quarter closes.",
             ["NISA-FR1 data is extracted and the return submitted within 30 days."]),
            ("SC-09", "Linked claims", "The claimant shares a bank account with another claimant.",
             ["Linked-claims indicator is raised (BR-FRD-005)."]),
            ("SC-10", "Notice returned undelivered", "A postal notice is returned.",
             ["Handler records the return and re-issues through an alternative channel."])]
    for sid_, name, given, then in scen:
        doc.h(2, f"7.{int(sid_[3:])} {sid_} {name}")
        doc.kv([["Given", given], ["Expected", " ".join(then)]], widths=(3.0, 13.6), font_size=8.8)
        steps_ = [["1", "Sentinel / triage-svc", "Score the claim and return the score", ctx.sys("SYS03")],
                  ["2", "Referral logic", "Compare the score with the threshold in force", "CLARA / Claims Hub"],
                  ["3", ctx.team("T11"), "Review the referral and decide on deferral", ctx.sys("SYS22")],
                  ["4", ctx.team("T02"), "Continue handling within the agreed service levels", "CLARA / Claims Hub"]]
        doc.table(["Step", "Actor", "Action", "System"], steps_, widths=[1.2, 4.4, 7.4, 3.6], font_size=8.4)
        doc.p(pr.para(["brd", "test"], n=(3, 4)))
    doc.h(1, "8 Impact on teams")
    for tid in ("T02", "T11", "T18", "T15", "T10", "T29"):
        doc.h(2, f"8.{['T02', 'T11', 'T18', 'T15', 'T10', 'T29'].index(tid) + 1} {ctx.team(tid)}")
        doc.ps(pr.paras(["opmodel", "brd"], 3, n=(3, 4)))
    doc.h(1, "9 Training, communications and testing")
    doc.ps(pr.paras(["test", "brd", "opmodel"], 4, n=(3, 5)))
    doc.h(1, "10 Data requirements")
    if not draft:
        t = W.tables["CLR.T_FRAUD_NOTIFICATION"]
        doc.p(f"CLR.T_FRAUD_NOTIFICATION ({ctx.a(t['description'])}) will be created on {long_date(t['created'])}.")
        doc.table(["Column", "Type", "Description"],
                  [[c["name"], c["type"] + (f"({c['length']})" if c.get("length") else ""), c["description"]] for c in t["columns"]],
                  widths=[4.6, 3.0, 9.0], font_size=8.2, caption="CLR.T_FRAUD_NOTIFICATION")
        tt = W.tables["fraud.customer_notice"]
        doc.table(["Column", "Description"], [[c["name"], c["description"]] for c in tt["columns"]], widths=[4.6, 12.0],
                  caption="Claims Hub fraud.customer_notice (fraud-referral-svc)", font_size=8.4)
    else:
        doc.p("A notice record will be needed in CLARA and in Claims Hub. The attributes below are proposed for "
              "discussion; the physical design is out of scope for this draft.")
        doc.bullets(["Referral reference", "Notice due date", "Notice sent date and channel", "Deferral flag, reason and approver",
                     "Deferral end date"])
    doc.ps(pr.paras(["data", "brd"], 2))

    doc.h(1, "11 System impacts")
    imp = [["CLRFR030", "Online referral creation", "Reads the new threshold from CLR.T_PARAM"],
           ["CLRFR040", "Nightly referral sweep", "Reads the new threshold from CLR.T_PARAM"],
           ["CLRFR140", "Auto-decline sweep", "See FR-REQ-014"],
           ["fraud-referral-svc", "Claims Hub referral decisions", "Threshold configuration; notice deadlines"],
           ["notification-svc", "Customer communications", "Customer notice templates"],
           ["triage-svc", "Sentinel pre-screen", "No change to scoring; passes the score to referral decisions"],
           [ctx.sys("SYS25"), "Notify gateway", "New templates"],
           [ctx.sys("SYS22"), "SIU Case Manager", "Triage timeliness reporting"]]
    if not draft:
        imp += [["CLRFR060", "Customer referral notice scheduler (new)", "FR-REQ-018"],
                ["CLRFR120", "Customer-notice deferral approval (new)", "FR-REQ-019"],
                ["CLR.T_FRAUD_NOTIFICATION", "Customer notice table (new)", "FR-REQ-017"]]
    doc.table(["Component", "Function", "Impact"], imp, widths=[4.2, 5.6, 6.8], caption="Impacted components", font_size=8.6)
    doc.ps(pr.paras(["brd", "integration"], 2))

    doc.h(1, "12 Non-functional and MI requirements")
    doc.ps(pr.paras(["brd", "security", "data"], 3))
    doc.h(1, "13 Assumptions, constraints, dependencies and risks")
    doc.table(["Type", "Item"],
              [["Assumption", "Sentinel scoring continues unchanged at FNOL and triage (BR-TRI-007)."],
               ["Constraint", f"All changes must be live by {long_date(circ['effective'])}."],
               ["Dependency", "Compliance approval of notice templates."],
               ["Dependency", "CLARA release capacity in the first quarter of 2026."],
               ["Risk", "Notice volumes are higher than forecast if referral volumes rise."],
               ["Risk", "Tipping-off risk if notices are sent before SIU has considered deferral."]],
              widths=[3.0, 13.6], caption="Assumptions, constraints, dependencies and risks")
    doc.ps(pr.paras("brd", 2))
    doc.h(1, "14 Traceability")
    rows = []
    for r in reqs:
        rows.append([r["src"], r["id"], r["rule"] or "—"])
    doc.table(["Source", "Requirement", "Rule"], rows, widths=[5.0, 4.0, 7.6], caption="Traceability matrix", font_size=8.6)
    if draft:
        doc.h(1, "Appendix A – Open questions", page_break=True)
        doc.table(["#", "Question", "Owner"],
                  [["Q1", "Is the notice period in FR-REQ-011 achievable for postal notices?", ctx.name("P037")],
                   ["Q2", "Which approver levels apply to deferrals?", ctx.name("P008")],
                   ["Q3", "Should Claims Hub and CLARA share one notice scheduler during coexistence?", ctx.name("P042")]],
                  widths=[1.2, 11.4, 4.0], caption="Open questions")
        doc.h(1, "Appendix B – Options")
        doc.p("Option B1 (FR-REQ-013, to be decided): refer all claims at a Sentinel score of 60 or more instead of 65. "
              "The option was raised in the requirements workshop as a way of increasing referral coverage. It has not "
              "been assessed for its effect on SIU capacity or customer experience and is listed here for decision.",
              facts=[PF(ctx, "ld15_option60", "refer all claims at a Sentinel score of 60 or more")])
        doc.table(["Option", "Description", "Status"],
                  [["B1", "Refer all claims at a Sentinel score of 60 or more", "To be decided"],
                   ["B2", "Refer at 65 or more (Circular maximum)", "Proposed baseline"]],
                  widths=[2.0, 10.6, 4.0], caption="Threshold options")
        doc.ps(pr.paras(["brd", "model"], 3))
    else:
        doc.h(1, "Appendix A – Decisions", page_break=True)
        doc.p("The Claims Fraud Forum on 12 March 2026 approved the rules that implement this BRD with effect from "
              "1 April 2026: BR-FRD-031 v1, BR-FRD-032 v2, BR-FRD-033, BR-FRD-034, BR-FRD-035 v2 and BR-FRD-036 v1.",
              facts=[F("approved", "DEC-007 (2026-03-12) approved BR-FRD-031 v1, 032 v2, 033, 034, 035 v2 and 036 v1 effective 2026-04-01.",
                       "BR-FRD-031 v1, BR-FRD-032 v2, BR-FRD-033, BR-FRD-034, BR-FRD-035 v2 and BR-FRD-036 v1", "DECISION:DEC-007")])
        doc.p("FR-REQ-013 (an option in the draft) was removed from the scope of version 1.0.")
        doc.ps(pr.paras(["brd", "governance"], 2))
    doc.h(1, "Appendix D – Circular interpretation" if draft else "Appendix C – Circular interpretation", page_break=True)
    for rq in circ["requirements"]:
        doc.h(2, f"§{rq['para']}")
        doc.p(rq["text"], italic=True)
        doc.ps(pr.paras(["brd", "governance"], 2, n=(3, 4)))
    doc.h(1, "Appendix E – MI catalogue" if draft else "Appendix D – MI catalogue")
    mi = ["Referrals by day and channel", "Referrals by score band", "Referrals by tier", "Notices due", "Notices sent on time",
          "Notices sent late", "Deferrals in force", "Deferrals by length", "Adverse outcomes with human review",
          "SIU triage within standard", "Untriaged referrals by age", "Referrals by product", "Manual referrals",
          "NISA-FR1 submission status", "Complaints linked to referrals"]
    doc.table(["#", "Measure", "Frequency"], [[str(i), m, "Daily" if i < 8 else "Monthly"] for i, m in enumerate(mi, 1)],
              widths=[1.2, 11.4, 4.0], caption="MI measures")
    doc.h(1, "Appendix F – Current referral table" if draft else "Appendix E – Current referral table")
    cols = [c for c in W.tables["CLR.T_FRAUD_REFERRAL"]["columns"] if "CUSTOMER_NOTICE" not in c["name"] and "DEFER" not in c["name"]]
    doc.table(["Column", "Type", "Description"],
              [[c["name"], c["type"] + (f"({c['length']})" if c.get("length") else ""), ctx.a(c["description"])] for c in cols],
              widths=[4.6, 2.6, 9.4], font_size=8.2, caption="CLR.T_FRAUD_REFERRAL (current columns)")
    doc.h(1, "Appendix G – Glossary" if draft else "Appendix F – Glossary")
    terms = [(t, ctx.a(m)) for t, m in C.glossary_terms(["G-002", "G-009", "G-012", "G-021", "G-008"])]
    doc.table(["Term", "Meaning"], [list(t) for t in terms], widths=[4.6, 12.0], font_size=8.8)
    return doc

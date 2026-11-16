"""LD001 — Claims Handling Manual v7.2 (approved 2026-06-30, rules as in force from 2026-07-01).

Builds the declarative spec. Every world fact comes from the world model via `S`; prose filler
comes from manual_lib.prose. Placement facts are planted exactly at their location hints.
"""
from __future__ import annotations

import pathlib

import yaml

from generators.common import util
from . import figures
from .common_content import pick_needle, rule_p
from .prose import STYLE_V72, _cap
from .spec import Spec, long_date, money

FID = "LD001"
DOC_DATE = "2026-06-30"
AS_OF = "2026-07-01"      # rules quoted as in force on the manual's effective date (approved 2026-06-30)
HEADER = "Claims Handling Manual v7.2 — Approved 30 June 2026 — Owner: Claims Director"
FOOTER = "CS-MAN-007 rev 7.2   |   Classification: Internal"

CUR_SYM = {"GBP": "£", "NOK": "NOK", "SEK": "SEK", "DKK": "DKK"}


def _amt(cur, v):
    return money(v, CUR_SYM[cur])


def build(W, fig_dir: pathlib.Path) -> Spec:
    S = Spec(W, FID, AS_OF, STYLE_V72, "LD001:v72")
    S.doc_date = DOC_DATE
    PL = {p["placement_id"]: p for p in W.placements_for(FID)}
    S.PL = PL
    d = DOC_DATE
    nm = lambda pid: W.name_of(pid, d)
    tt = lambda pid: W.title_of(pid, d)
    figs = _figures(fig_dir)

    # ================================================================== title page + ch1
    S.new_seg("title", ("first",), 1, fill=False)
    S.blocks.append({"t": "title_page", "top_space": 150, "gap": 16, "lines": [
        ("Corvane Mutual Insurance Society Limited", 15, True),
        ("Claims Handling Manual", 30, True),
        ("Version 7.2", 18, False),
        ("Approved 30 June 2026  ·  Effective 1 July 2026", 13, False),
        (f"Owner: {nm('P005')}, {tt('P005')}", 13, False),
        ("For use by Claims Operations, Major & Complex Loss, Counter-Fraud & SIU, Reserving, "
         "Recoveries & Subrogation and the Nordic branches", 11, False),
    ]})

    S.topic = "governance"
    S.h1(1, "Introduction and document control", 2, "governance")
    S.p("This manual sets out how Corvane handles claims from first notification to closure and recovery. "
        "It consolidates the claims rules approved for use from 1 July 2026, the requirements of the "
        "National Insurance Supervisory Authority (NISA) that apply to claims handling, and the operating "
        "procedures agreed by each process owner. This chapter records the control information for the manual.")
    S.table(["Item", "Detail"], [
        ["Title", "Claims Handling Manual"],
        ["Version", "7.2"],
        ["Status", "Approved"],
        ["Approval date", "30 June 2026"],
        ["Effective date", "1 July 2026, unless a rule in this manual states a different effective date"],
        ["Owner", f"{nm('P005')}, {tt('P005')}"],
        ["Supersedes", "Claims Handling Manual v6.1 (approved 15 May 2023)"],
        ["Document reference", "Shown in the footer of every page"],
        ["Review", "On any change to a governing rule, and in any case when the owner directs"],
    ], caption="Document control", widths=[4.5, 11.5], facts=[
        S.fact("approved", "Claims Handling Manual v7.2 was approved on 30 June 2026.", "30 June 2026",
               world_ref="ANCHOR:LD001#date", row=4, col=1),
        S.fact("general", "Manual v7.2 supersedes Claims Handling Manual v6.1, approved 15 May 2023.",
               "Claims Handling Manual v6.1 (approved 15 May 2023)", world_ref="ANCHOR:LD012#date", row=7, col=1),
    ])
    approvers = ["P005", "P011", "P009", "P008", "P013", "P033", "P030", "P012", "P037", "P019"]
    rows = [[nm(p), tt(p), "Approved 30 June 2026" if p == "P005" else "Reviewed and approved for issue"] for p in approvers]
    S.table(["Name", "Role", "Approval"], rows, caption="Approvals", widths=[4.2, 7.3, 4.5],
            facts=[S.fact("general", f"The v7.2 manual approvals include {nm('P013')}, {tt('P013')}.",
                          nm("P013"), world_ref="PERSON:P013#titles", row=5, col=0)])
    S.table(["Version", "Date", "Status", "Summary of change"], [
        ["6.1", "15 May 2023", "Superseded", "Previous issue of the manual."],
        ["7.0 / 7.1", "—", "Not issued", "Consultation drafts circulated to process owners and Compliance."],
        ["7.2", "30 June 2026", "Approved", "Full revision: fraud referral and customer notice (NISA Circular 2026/04), "
         "reserve and payment authority limits, tier definitions, FNOL acknowledgement, Tier-3 review cadence, "
         "recoveries ownership and Nordic variations."],
    ], caption="Version history", widths=[2.0, 2.8, 2.6, 8.6])
    S.p("Distribution: all Claims Operations teams (UK and Nordic), Major & Complex Loss, Claims Assessment, "
        "Counter-Fraud & SIU, Reserving, Recoveries & Subrogation, Payments Operations, Compliance and the "
        "Claims Hub Product team. Printed copies are uncontrolled.")
    S.new_seg("toc", ("text", "Contents"), 4, fill=False)
    S.blocks.append({"t": "toc", "title": "Contents", "break": True})
    S.blocks[-1]["t"] = "pagebreak"
    S.blocks.append({"t": "toc", "title": "Contents"})
    # after the TOC
    S.h2("1.1", "Purpose and scope", seg_id="c1s", target=None)
    S.segs[-1]["elastic"] = True
    S.prose_p((3, 4))
    S.p("The manual applies to all personal and commercial lines written by Corvane in the United Kingdom, "
        "Norway, Sweden and Denmark. Chapter 12 sets out where Nordic practice differs.")
    S.h2("1.2", "How to use this manual")
    S.p("Each chapter follows the claims lifecycle. Rules are quoted with their identifier and version "
        "(for example BR-FNOL-002 v1); the rule register in Appendix A lists every rule in force on 1 July 2026. "
        "Defined terms are explained in Chapter 2 and are used with those meanings throughout.")
    S.h2("1.3", "Changes in version 7.2")
    S.bullets([
        "Chapter 2 restates the claim tier definitions and introduces the Large Loss Notification Threshold.",
        "Chapters 27 to 30 implement NISA Circular 2026/04 (fair treatment in fraud referral).",
        "Chapters 18 and 25 reflect the reserve and payment authority limits approved in August 2025.",
        "Chapter 19 changes the review cadence for Tier-3 case reserves.",
        "Chapters 33 and 34 reflect the creation of Recoveries & Subrogation as a Group function.",
    ])
    S.h2("1.4", "Related documents")
    S.bullets(["NISA Circular 2024/07 — Claims Handling Timeliness",
               "NISA Circular 2025/02 — Operational Resilience for Claims Payment",
               "NISA Circular 2025/11 — Claims Data Retention and Minimisation",
               "NISA Circular 2026/04 — Fair Treatment in Fraud Referral",
               "Claims Standards Bulletins issued since version 6.1 (now consolidated into this manual)"])

    # ================================================================== ch2 definitions
    S.h1(2, "Definitions and glossary", 11, "governance")
    S.h2("2.1", "Interpretation")
    S.p("In this manual the words below have the meanings given to them. Where a term is defined by a rule, "
        "the definition follows the version of the rule in force at the relevant date. Headings are for "
        "convenience only. A reference to a team or role includes any person to whom the role holder has "
        "delegated authority in writing.")
    S.prose_p((3, 4))
    S.h2("2.2", "Claims Assessor and loss adjuster")
    g1 = W.glossary["G-001"]
    pl = PL["PL-018"]
    S.p(runs=[{"text": "Claims Assessor. ", "bold": True},
              {"text": f"{g1['definition']} In this manual 'loss adjuster' means an external (panel) Claims Assessor; "
                       "Corvane employees who assess losses are referred to as Claims Assessors. Norwegian policy "
                       "wordings use the term skadetakstmann."}],
        facts=[S.placement_fact(pl, "LD001 §2.2 defines Claims Assessor and states that 'loss adjuster' in the "
                                    "manual means an external (panel) Claims Assessor.",
                                "'loss adjuster' means an external (panel) Claims Assessor", mirror=True)])
    S.prose_p((2, 3), topic="assessment")
    S.h2("2.3", "Core claim terms")
    for gid, label in [("G-005", "First Notice of Loss (FNOL)"), ("G-006", "Peril (Claim Type)"),
                       ("G-007", "Claims Handler"), ("G-011", "Policyholder (member)"), ("G-010", "Excess"),
                       ("G-014", "Incurred"), ("G-018", "Settlement")]:
        g = W.glossary[gid]
        S.p(runs=[{"text": label + ". ", "bold": True}, {"text": g["definition"]}],
            facts=[S.fact("definition", f"LD001 §2.3 defines {label}: {g['definition']}", g["definition"][:60].rstrip(" ,.;"),
                          world_ref=f"GLOSSARY:{gid}")])

    S.h2("2.4", "Claim tiers", target=15)
    pl = PL["PL-001"]
    v = S.rv("BR-TRI-003")
    S.p("Every claim is given a tier at triage. The tier determines routing, the level of supervision and "
        "the review cadence for the case reserve.")
    tier3 = S.placement_fact(pl, "A Tier-3 claim is one with estimated incurred of £50,000 or more (NOK 650,000 / "
                                 "SEK 680,000 / DKK 430,000), any bodily injury, solicitor or litigation involvement "
                                 "at notification, or a property total loss (BR-TRI-003 v3, from 2025-01-01).",
                             "estimated incurred of £50,000 or more", mirror=True,
                             notes="Long-range definition: used ~256 pages later in §19.4 (LD001 PL-002) without restating it.")
    t3b = S.fact("definition", "Tier-3 triggers include solicitor or litigation involvement at notification and a property total loss.",
                 "solicitor or litigation involvement at notification", world_ref="RULE:BR-TRI-003@v3#parameters.tier3_triggers")
    S.p(runs=[{"text": "Tier-3 claim. ", "bold": True},
              {"text": "A claim is a Tier-3 claim if any of the following applies: (a) estimated incurred of £50,000 or more "
                       "(NOK 650,000 / SEK 680,000 / DKK 430,000); (b) any bodily injury; (c) solicitor or litigation "
                       "involvement at notification; or (d) a property total loss. This definition follows BR-TRI-003 v3, "
                       "in force from 1 January 2025."}], facts=[tier3, t3b])
    S.rule_sections["BR-TRI-003"] = "2.4"
    t2 = S.fact("definition", "Tier-2: estimated incurred £5,000 to £49,999 or any third-party involvement (BR-TRI-003 v3).",
                "£5,000 to £49,999", world_ref="RULE:BR-TRI-003@v3#parameters.tier2_min_gbp")
    S.p(runs=[{"text": "Tier-2 claim. ", "bold": True},
              {"text": "A claim that is not Tier-3 and has an estimated incurred of £5,000 to £49,999, or involves any third party."}],
        facts=[t2])
    t1 = S.fact("definition", "Tier-1: below £5,000 with no injury and no third party (BR-TRI-003 v3).",
                "below £5,000 with no injury and no third party", world_ref="RULE:BR-TRI-003@v3#text")
    S.p(runs=[{"text": "Tier-1 claim. ", "bold": True},
              {"text": "Any other claim, that is, an estimated incurred below £5,000 with no injury and no third party."}], facts=[t1])
    S.p("Tiers are applied at triage (Chapter 8) and re-applied whenever the estimate crosses a tier boundary. "
        "'Major & Complex Loss' is the team that handles Tier-3 claims; it is a routing destination, not a tier.")
    S.h2("2.5", "Reserve terms")
    for gid, label in [("G-003", "Case reserve"), ("G-013", "Reserve movement"), ("G-016", "Technical provisions"),
                       ("G-017", "Bordereau")]:
        g = W.glossary[gid]
        S.p(runs=[{"text": label + ". ", "bold": True}, {"text": g["definition"]}],
            facts=[S.fact("definition", f"LD001 §2.5 defines {label}: {g['definition']}", g["definition"][:55].rstrip(" ,.;:"),
                          world_ref=f"GLOSSARY:{gid}")])

    S.h2("2.6", "Large loss terms", target=18)
    pl = PL["PL-016"]
    llnt = S.placement_fact(pl, "Large Loss Notification Threshold (LLNT) = a reserve movement of £250,000 (BR-RSV-011 v2).",
                            "a reserve movement of £250,000", mirror=True,
                            notes="Long-range definition: used in §22.3 (~p.300) without restating the amount.")
    S.p(runs=[{"text": "Large Loss Notification Threshold (LLNT). ", "bold": True},
              {"text": "A reserve movement of £250,000 on a single claim (BR-RSV-011 v2). The LLNT is used in Chapter 22."}],
        facts=[llnt])
    S.rule_sections["BR-RSV-011"] = "2.6"
    S.p(runs=[{"text": "Large loss. ", "bold": True},
              {"text": "A claim handled under Chapter 22 because a reserve movement on it has exceeded the LLNT."}])
    S.p(runs=[{"text": "Major and complex loss. ", "bold": True},
              {"text": "A claim handled by the Major & Complex Loss team, whether because of its tier, its complexity or its profile."}])
    S.h2("2.7", "Fraud terms")
    for gid, label in [("G-009", "Sentinel score"), ("G-002", "Referral to SIU"), ("G-021", "Customer Referral Notice"),
                       ("G-012", "Counter-Fraud & SIU")]:
        g = W.glossary[gid]
        extra = ""
        if gid == "G-009":
            extra = " Before 1 March 2025 the engine was called FRAUDNET and the score the FRAUDNET score."
        S.p(runs=[{"text": label + ". ", "bold": True}, {"text": g["definition"] + extra}],
            facts=[S.fact("definition", f"LD001 §2.7 defines {label}: {g['definition']}", g["definition"][:50].rstrip(" ,.;:()"),
                          world_ref=f"GLOSSARY:{gid}")])
    S.h2("2.8", "Recovery terms")
    for gid, label in [("G-004", "Recoveries and subrogation"), ("G-022", "Salvage")]:
        g = W.glossary[gid]
        S.p(runs=[{"text": label + ". ", "bold": True}, {"text": g["definition"]}])
    S.p(runs=[{"text": "Regress. ", "bold": True},
              {"text": "The Nordic term (regressfordring) for a recovery made from another insurer or a responsible third party."}])
    S.h2("2.9", "Nordic terms and peril names")
    S.p("Nordic policy wordings and correspondence use local terms. The excess is called egenandel in Norway, "
        "självrisk in Sweden and selvrisiko in Denmark. Local peril names are shown in Table 2-1.")
    cts = yaml.safe_load(open(util.ROOT / "world" / "data" / "claim_types.yaml", encoding="utf-8"))["claim_types"]
    rows = []
    for c in cts:
        ln = c.get("local_names") or {}
        rows.append([c["peril_code"], c["name"], ln.get("NO", "—"), ln.get("SE", "—"), ln.get("DK", "—")])
    S.table(["Code", "Peril (Claim Type)", "Norwegian", "Swedish", "Danish"], rows,
            caption="Local peril names", widths=[1.6, 4.6, 3.3, 3.3, 3.3],
            facts=[S.fact("general", "The Swedish name for the Flood peril is Översvämning.", "Översvämning",
                          world_ref="CLAIMTYPE:CT-FLD#local_names", row=[i for i, c in enumerate(cts) if c["peril_code"] == "FLD"][0] + 1, col=3)])
    S.h2("2.10", "Systems and platforms")
    sys_rows = []
    for sid in ["SYS01", "SYS02", "SYS03", "SYS04", "SYS05", "SYS17", "SYS12", "SYS13", "SYS19", "SYS22", "SYS24",
                "SYS25", "SYS07", "SYS08", "SYS09", "SYS06", "SYS11"]:
        s_ = W.systems[sid]
        nmx = W.system_name(sid, d)
        former = [rn["from_name"] for rn in s_.get("renames", [])]
        desc = s_["description"].split(". Renamed")[0].split(". Model owner")[0].rstrip(".") + "."
        if former:
            desc += f" Formerly {former[0]}."
        sys_rows.append([nmx, desc])
    S.table(["System", "Purpose"], sys_rows, caption="Systems referred to in this manual", widths=[4.0, 12.0],
            facts=[S.fact("alias_use", "Evidence Vault was formerly DOCSTOR.", "Formerly DOCSTOR", world_ref="SYSTEM:SYS05#renames",
                          row=5, col=1)])
    S.h2("2.11", "Abbreviations")
    abbr = [("BI", "Bodily injury (or business interruption where the context requires)"), ("CHUB", "Claims Hub (Jira key)"),
            ("CLARA", "Claims Ledger And Reserve Application"), ("CLR", "CLARA schema and program prefix"),
            ("EOW", "Escape of Water"), ("FNOL", "First Notice of Loss"), ("GL", "Group Ledger"),
            ("LLNT", "Large Loss Notification Threshold"), ("MI", "Management information"),
            ("NISA", "National Insurance Supervisory Authority"), ("NISA-FR1", "Quarterly Fraud Referral Return"),
            ("NISA-TP2", "Quarterly Technical Provisions Return"), ("NISA-CT1", "Annual Claims Timeliness Return"),
            ("RSNC", "Reserve reason code list"), ("SIU", "Counter-Fraud & SIU (Special Investigations Unit)"),
            ("T3", "Tier-3 claim"), ("TP", "Technical provisions"), ("bdx", "Bordereau or bordereaux")]
    S.table(["Abbreviation", "Meaning"], [list(a) for a in abbr], caption="Abbreviations", widths=[3.5, 12.5])

    # ================================================================== ch3 governance
    S.h1(3, "Governance and authorities", 31, "governance")
    S.h2("3.1", "Governance framework")
    S.prose_ps(2)
    S.h2("3.2", "Process ownership")
    S.p("Each stage of the claims lifecycle has an accountable process owner. Process owners approve changes to "
        "their chapters and are accountable for the evidence that controls operate.")
    rows = []
    facts = []
    for i, (sid, st) in enumerate(W.stages.items(), start=1):
        own = W.owner_of_process(sid, d)
        rows.append([st["name"], nm(own), tt(own)])
        if sid == "S7":
            facts.append(S.fact("general", f"The Recovery & Subrogation stage is owned by {nm(own)} ({tt(own)}).",
                                nm(own), world_ref="PROCESS:S7#owner_history", row=i, col=1))
        if sid == "S4":
            facts.append(S.fact("general", f"The Reserving stage is owned by {nm(own)} ({tt(own)}).",
                                nm(own), world_ref="PROCESS:S4#owner_history", row=i, col=1))
    S.table(["Lifecycle stage", "Process owner", "Role"], rows, caption="Process owners", widths=[5, 4.5, 6.5], facts=facts)
    S.prose_p()
    S.h2("3.3", "Claims teams")
    team_ids = ["T02", "T03", "T04", "T05", "T06", "T07", "T08", "T09", "T10", "T11", "T12", "T16", "T17", "T18", "T21"]
    deps = {x["id"]: x["name"] for x in yaml.safe_load(open(util.ROOT / "world" / "data" / "org.yaml", encoding="utf-8"))["departments"]}
    rows = []
    for t_ in team_ids:
        lead = W.team_lead(t_, d)
        rows.append([W.team_name(t_, d), nm(lead) if lead else "—", deps.get(W.team_department(t_, d), "—")])
    S.table(["Team", "Team lead", "Department"], rows, caption="Teams referred to in this manual", widths=[6, 4.5, 5.5],
            facts=[S.fact("general", "Counter-Fraud & SIU sits in the Risk & Compliance department (as of 2026-06-30).",
                          "Risk & Compliance", world_ref="TEAM:T11#department_history", row=team_ids.index("T11") + 1, col=2)])
    S.h2("3.4", "Committees and forums")
    c1 = W.committees["COM-01"]
    chair = [c for c in c1["chair_history"] if (c["to"] or "9999") >= d and c["from"] <= d][0]["person"]
    S.p(f"The Reserving Committee is chaired by the {tt(chair)}, {nm(chair)}. Its remit is: "
        f"{c1['remit'][0].lower() + c1['remit'][1:]}. Its meetings are described in Chapter 21.",
        facts=[S.fact("general", f"The Reserving Committee is chaired by {nm(chair)}.", f"chaired by the {tt(chair)}, {nm(chair)}",
                      world_ref="COMMITTEE:COM-01#chair_history")])
    c2 = W.committees["COM-02"]
    S.p(runs=[{"text": f"The Claims Fraud Forum is chaired by the {tt('P008')}, {nm('P008')}, and meets {c2['cadence'].replace(' UK time', '')} (UK time). "
                       f"Its remit covers {c2['remit'][0].lower() + c2['remit'][1:]}. "},
              {"text": "The forum's members include the "},
              {"del": "Special Investigations Unit", "author": nm("P008"), "date": "2026-06-11T09:20:00Z",
               "fact": S.fact("tracked_delete", "Tracked deletion in §3.4: the old team name 'Special Investigations Unit'.",
                              "Special Investigations Unit", world_ref="GLOSSARY:G-012")},
              {"ins": "Counter-Fraud & SIU", "author": nm("P008"), "date": "2026-06-11T09:20:00Z",
               "fact": S.fact("tracked_insert", "Tracked insertion in §3.4: the current team name 'Counter-Fraud & SIU'.",
                              "Counter-Fraud & SIU", world_ref="TEAM:T11#name_history")},
              {"text": " leadership, the Senior Fraud Analyst, the SIU Investigations Manager (UK), Compliance and Claims Operations."}],
        facts=[S.fact("general", "The Claims Fraud Forum meets fortnightly on Thursday at 14:00.", "fortnightly, Thursday 14:00",
                      world_ref="COMMITTEE:COM-02#cadence")])
    S.prose_p()
    S.h2("3.5", "Delegated authority")
    rule_p(S, "BR-GEN-001", fmt=0)
    S.p("Monetary authority limits for case reserves are set out in Chapter 18 and for payments in Chapter 25. "
        "Authority is held by role and is recorded in the delegated authority register maintained by Claims Operations.")
    rule_p(S, "BR-GEN-007", fmt=1)
    S.h2("3.6", "Regulatory framework")
    rows = []
    for cid in ["CIRC-2024-07", "CIRC-2025-02", "CIRC-2025-11", "CIRC-2026-04"]:
        c = W.circulars[cid]
        rows.append([c["ref"], c["title"], long_date(c["effective"])])
    S.table(["Circular", "Title", "Effective"], rows, caption="NISA circulars applied in this manual", widths=[4.2, 8, 3.8],
            facts=[S.fact("general", "NISA Circular 2026/04 (Fair Treatment in Fraud Referral) is effective from 1 April 2026.",
                          "1 April 2026", world_ref="CIRCULAR:CIRC-2026-04#effective", row=4, col=2)])
    S.p(f"Corvane is regulated by NISA under firm reference {W.get('ORG:company')['nisa_firm_reference']}. "
        "Regulatory returns that draw on claims data are prepared by Regulatory Reporting.")

    # ================================================================== ch4 customer
    S.h1(4, "Customer treatment and vulnerability", 46, "customer")
    S.h2("4.1", "Principles")
    S.prose_ps(2)
    S.h2("4.2", "Identifying vulnerability")
    rule_p(S, "BR-FNOL-014")
    S.prose_p()
    S.h2("4.3", "Communication and accessibility")
    rule_p(S, "BR-GEN-005")
    rule_p(S, "BR-GEN-009")
    rule_p(S, "BR-FNOL-013")
    S.h2("4.4", "Complaints")
    rule_p(S, "BR-GEN-003", needle="within 3 business days")
    S.prose_p()
    S.h2("4.5", "Representatives and third parties")
    S.prose_ps(2)

    # ================================================================== ch5 FNOL
    S.h1(5, "First Notice of Loss", 59, "fnol")
    S.h2("5.1", "Overview")
    S.p("First notification is the start of the claim and the first test of how Corvane treats the customer. "
        "Figure 5-1 shows the FNOL steps, which are the same for every channel.")
    S.figure(figs["fnol"], "FNOL process overview",
             "FNOL process: receive notification, validate policy and cover within 1 hour, create claim and default "
             "reserve within 15 minutes, duplicate and late-notification checks the same business day, acknowledge the customer.",
             facts=[S.fact("image_text", "FNOL diagram: the claim and default reserve are created within 15 minutes of notification.",
                           "Create claim and default reserve", world_ref="PROCESS:PS-FNOL-03#sla")],
             alt_facts=[S.fact("alt_text", "Alt text of the FNOL diagram: policy and cover validated within 1 hour of notification.",
                               "validate policy and cover within 1 hour", world_ref="PROCESS:PS-FNOL-02#sla")])
    S.h2("5.2", "Notification channels")
    S.table(["Channel", "Captured in", "Notes"], [
        ["Telephone", W.system_name("SYS12", d), "Contact Centre, Glasgow"],
        ["Customer portal and app", W.system_name("SYS04", d), "Formerly ClaimLine Web"],
        ["Telematics crash alert", W.system_name("SYS13", d), "Creates a draft FNOL"],
        ["Broker", "Broker submission", "Broker reference mandatory"],
        ["Post", W.system_name("SYS27", d), "Scanned into " + W.system_name("SYS05", d)],
    ], caption="FNOL channels", widths=[4.5, 5, 6.5])
    S.h2("5.3", "Taking the notification")
    rule_p(S, "BR-FNOL-002", needle="before a claim number is issued")
    rule_p(S, "BR-FNOL-007")
    rule_p(S, "BR-FNOL-008")

    S.h2("5.4", "Acknowledgement", target=63)
    pl = PL["PL-019"]
    v = S.rv("BR-FNOL-001")
    ack = S.placement_fact(pl, "FNOL acknowledgement: within 1 business day for digital channels (portal, app, telematics) "
                               "and 2 business days for other channels (BR-FNOL-001 v3, effective 2026-07-01).",
                           "within 1 business day and all other channels (telephone, broker, post) within 2 business days",
                           mirror=True, ocr_needle="within 1 business day")
    S.p(runs=[{"text": "BR-FNOL-001 (v3, effective 1 July 2026). ", "bold": True},
              {"text": v["text"]},
              {"text": "", "footnote": {"text": "Version 2 of BR-FNOL-001 implemented NISA Circular 2024/07 §2.1 from 1 October 2024. "
                                                "Version 3 shortens the standard for digital channels from 1 July 2026.",
                                        "fact": S.fact("footnote", "Footnote: BR-FNOL-001 v2 implemented NISA Circular 2024/07 §2.1 from 1 October 2024.",
                                                       "NISA Circular 2024/07 §2.1 from 1 October 2024", world_ref="CIRCULAR:CIRC-2024-07#effective",
                                                       mirror=True)}}],
        facts=[ack])
    S.rule_sections["BR-FNOL-001"] = "5.4"
    S.p("The acknowledgement is sent by Notify and confirms the claim number, the handling team and how to send "
        "documents. Where the acknowledgement cannot be sent automatically, the Contact Centre sends it manually and records why.")
    S.prose_p()
    S.h2("5.5", "Duplicate and late notifications")
    rule_p(S, "BR-FNOL-004", needle="within ±3 days")
    rule_p(S, "BR-FNOL-003", needle="more than 30 days after the date of loss")
    S.prose_p()
    S.h2("5.6", "Emergencies and out-of-hours notifications")
    rule_p(S, "BR-FNOL-019", needle="up to £500 at FNOL")
    rule_p(S, "BR-FNOL-012", needle="by 10:00 the next business day")
    S.h2("5.7", "Telematics and digital notifications")
    rule_p(S, "BR-FNOL-009", needle="within 5 minutes")
    rule_p(S, "BR-FNOL-011", needle="up to 20 photos of at most 15 MB each")
    S.h2("5.8", "Broker and third-party notifications")
    rule_p(S, "BR-FNOL-010")
    rule_p(S, "BR-FNOL-021", needle="policyholder confirmation within 5 business days")
    S.h2("5.9", "Weather events")
    rule_p(S, "BR-FNOL-020")
    S.prose_p()

    # ================================================================== ch6 data
    S.h1(6, "FNOL data standards", 79, "data")
    S.h2("6.1", "Mandatory data set")
    S.p("BR-FNOL-002 lists the data that must be captured before a claim number is issued. Table 6-1 shows the "
        "fields and where each is captured.")
    v = S.rv("BR-FNOL-002")
    labels = {"policy_no": "Policy number", "loss_date": "Date of loss", "claim_type": "Claim Type (peril)",
              "loss_location": "Loss location", "contact": "Contact details", "loss_description": "Description of loss"}
    S.table(["Field", "Data item", "Mandatory"], [[f, labels[f], "Yes"] for f in v["parameters"]["mandatory_fields"]],
            caption="Mandatory FNOL data (BR-FNOL-002)", widths=[4.5, 7.5, 4])
    S.h2("6.2", "Line-specific fields")
    rule_p(S, "BR-FNOL-006")
    rule_p(S, "BR-FNOL-015")
    rule_p(S, "BR-FNOL-018")
    S.h2("6.3", "Location data")
    rule_p(S, "BR-FNOL-016")
    S.h2("6.4", "Personal data and masking")
    rule_p(S, "BR-FNOL-017", needle="last 4 digits only")
    rule_p(S, "BR-GEN-006")
    S.h2("6.5", "CLARA FNOL capture screen")
    bm = W.bms_maps["CLRM010"]
    S.p(f"In CLARA, FNOL is captured on map {bm['map']} (mapset {bm['mapset']}), transaction {bm['transaction']}, "
        f"program {bm['program']}. Table 6-2 lists the fields on the screen.",
        facts=[S.fact("general", f"CLARA FNOL capture uses map {bm['map']}, transaction {bm['transaction']}, program {bm['program']}.",
                      f"transaction {bm['transaction']}, program {bm['program']}", world_ref="BMS:CLRM010")])
    S.table(["Field", "Row", "Column", "Length", "Attributes"],
            [[f["name"], f["row"], f["col"], f["length"], f["attr"]] for f in bm["fields"]],
            caption=f"Fields on map {bm['map']}", widths=[4.5, 2, 2, 2, 5.5])

    # ================================================================== ch7 default reserves (multi-page table)
    S.h1(7, "Default reserves at FNOL", 88, "reserving")
    S.segs[-1]["table_fill"] = True
    S.segs[-1]["fill"] = False
    S.segs[-1]["cap"] = 300
    S.h2("7.1", "Purpose")
    rule_p(S, "BR-FNOL-005", fmt=0, needle="from the default-reserve table (2025 values)")
    S.p("Table 7-1 lists the default indemnity reserve for each product and peril. Where no default is tabled, "
        "the Claims Handler sets a claim-specific reserve under BR-RSV-001 (section 7.3).")
    S.h2("7.2", "Default reserve table")
    _default_reserve_table(S, W)
    S.h2("7.3", "Replacing the default reserve", target=93)
    rule_p(S, "BR-RSV-001", needle="within 2 business days of FNOL", fmt=0)
    S.prose_p()
    S.h2("7.4", "System behaviour")
    pr = W.programs["CLRFN030"]
    S.p(f"In CLARA the claim record and default reserve are created by program CLRFN030 ({pr['description'].rstrip('.')}). "
        f"For Danish claims, which have been handled in Claims Hub since Wave 0 on 1 June 2026, the default reserve is "
        f"created by {W.service_name('fnol-intake-svc', d)} and {W.service_name('reserve-engine', d)}.",
        facts=[S.fact("general", "CLARA program CLRFN030 creates the claim record and default reserve.", "program CLRFN030",
                      world_ref="PROGRAM:CLRFN030"),
               S.fact("temporal", "Danish claims have been handled in Claims Hub since Wave 0 on 1 June 2026.",
                      "since Wave 0 on 1 June 2026", world_ref="WAVE:MW-0#date")])

    # ================================================================== ch8 triage
    S.h1(8, "Triage and tiering", 97, "triage")
    S.h2("8.1", "Purpose of triage")
    S.p("Triage scores the claim, assigns its tier and routes it. Figure 8-1 summarises the routing decision.")
    S.figure(figs["triage"], "Triage routing",
             "Triage routing: Sentinel pre-screen within 15 minutes, tier classification within 4 hours, Tier-3 to Major "
             "& Complex Loss, eligible Tier-1 to fast-track, referral threshold met to Counter-Fraud & SIU, otherwise to assessment.",
             facts=[S.fact("image_text", "Triage diagram: Tier-3 claims route to Major & Complex Loss.", "Major & Complex Loss",
                           world_ref="RULE:BR-TRI-004@v1")],
             alt_facts=[S.fact("alt_text", "Alt text: tier classification within 4 hours.", "tier classification within 4 hours",
                               world_ref="PROCESS:PS-TRI-02#sla")])
    S.prose_p()
    S.h2("8.2", "Sentinel pre-screen")
    rule_p(S, "BR-TRI-007", needle="within 15 minutes of FNOL")
    S.p(f"Sentinel is licensed from {W.vendors['VEN-15']['name']} and scores claims from 0 to 100.",
        facts=[S.fact("general", "Sentinel is licensed from Kestwick Analytics Ltd.", W.vendors["VEN-15"]["name"], world_ref="VENDOR:VEN-15#role")])
    S.h2("8.3", "Applying the tier definitions")
    S.p("Claims are tiered using the definitions in section 2.4. The definitions are not repeated here.")
    rule_p(S, "BR-TRI-008")
    rule_p(S, "BR-TRI-015")
    S.h2("8.4", "Tier overrides")
    rule_p(S, "BR-TRI-009", needle="Team Leader approval within 24 hours")
    S.h2("8.5", "Routing rules")
    rows = []
    for rid in ["BR-TRI-001", "BR-TRI-002", "BR-TRI-004", "BR-TRI-005", "BR-TRI-011", "BR-TRI-013", "BR-TRI-016",
                "BR-TRI-017", "BR-TRI-018", "BR-TRI-019"]:
        vv = S.rv(rid)
        rows.append([rid, f"v{vv['version']}", vv["text"]])
        S.rule_sections.setdefault(rid, "8.5")
    S.table(["Rule", "Ver.", "Routing"], rows, caption="Routing rules applied at triage", widths=[2.8, 1.2, 12],
            facts=[S.fact("general", "BR-TRI-017: flood claims above £30000 route to Major & Complex Loss.", "Flood claims above £30000",
                          world_ref="RULE:BR-TRI-017@v1", row=8, col=2),
                   S.fact("general", "BR-TRI-004: Tier-3 claims route to Major & Complex Loss within 4 hours.",
                          "Major & Complex Loss within 4 hours", world_ref="RULE:BR-TRI-004@v1", row=3, col=2)])
    S.prose_p()
    S.h2("8.6", "Surge mode")
    rule_p(S, "BR-TRI-012", needle="exceed 1500")
    S.h2("8.7", "Repeat claimants and theft without a police reference")
    rule_p(S, "BR-TRI-014")
    rule_p(S, "BR-TRI-010", needle="over £5000 without a police reference")

    # ================================================================== ch9 fast-track
    S.h1(9, "Fast-track handling", 119, "fasttrack")
    S.h2("9.1", "Eligibility")
    v = S.rv("BR-TRI-006")
    rule_p(S, "BR-TRI-006", fmt=0, needle="cap £2,000 (NOK 26,000 / SEK 27,000 / DKK 17,000)")
    S.table(["Currency", "Fast-track cap"], [["GBP", "£2,000"], ["NOK", "NOK 26,000"], ["SEK", "SEK 27,000"], ["DKK", "DKK 17,000"]],
            caption="Fast-track caps from 1 July 2026 (BR-TRI-006 v3)", widths=[4, 6])
    S.h2("9.2", "Straight-through payment")
    rule_p(S, "BR-STL-009")
    S.h2("9.3", "Quality sampling")
    S.prose_ps(2)
    S.h2("9.4", "Leaving the fast-track route")
    S.prose_p()

    # ================================================================== ch10 assessment
    S.h1(10, "Assessment and Claims Assessor appointment", 129, "assessment")
    S.h2("10.1", "Overview")
    S.figure(figs["assess"], "Claims Assessor appointment",
             "Claims Assessor appointment: Tier-2 property claims above £10,000 need a panel loss adjuster appointed "
             "within 2 business days of triage; Nordic external instructions go to Norrvik Skadetaxering.",
             facts=[S.fact("image_text", "Assessor appointment diagram: Nordic external instructions go to Norrvik.",
                           "Norrvik", world_ref="RULE:BR-ASM-016@v1")],
             alt_facts=[S.fact("alt_text", "Alt text: panel loss adjuster appointed within 2 business days of triage.",
                               "appointed within 2 business days of triage", world_ref="RULE:BR-ASM-002@v1")])
    S.h2("10.2", "When to appoint a loss adjuster")
    rule_p(S, "BR-ASM-002", needle="above £10,000 require an external Claims Assessor")
    S.prose_p()
    S.h2("10.3", "Panel and allocation")
    rule_p(S, "BR-ASM-015")
    rows = []
    for vid in ["VEN-01", "VEN-02", "VEN-04", "VEN-05", "VEN-06", "VEN-14"]:
        ven = W.vendors[vid]
        rows.append([ven["name"], ven["location"], ven["role"]])
    S.table(["Panel firm", "Based in", "Role"], rows, caption="Assessment and repair panel", widths=[5.5, 3, 7.5],
            facts=[S.fact("general", "Brackenfield Loss Adjusting Ltd provides external Claims Assessors (loss adjusters) for UK property and motor.",
                          "Brackenfield Loss Adjusting Ltd", world_ref="VENDOR:VEN-01#role", row=1, col=0)])
    S.h2("10.4", "Nordic instructions")
    rule_p(S, "BR-ASM-016")
    S.h2("10.5", "Conflicts of interest")
    rule_p(S, "BR-ASM-010", needle="within 3 years")
    S.h2("10.6", "Instructions and the Assessor Portal")
    S.p(runs=[{"text": f"Instructions and reports are exchanged through the {W.system_name('SYS17', d)}."},
              {"text": "", "footnote": {"text": "The Assessor Portal was called the Adjuster Extranet until 1 September 2025.",
                                        "fact": S.fact("footnote", "Footnote: the Assessor Portal was called the Adjuster Extranet until 1 September 2025.",
                                                       "called the Adjuster Extranet until 1 September 2025", world_ref="SYSTEM:SYS17#renames", mirror=True)}},
              {"text": " Handlers should not send instructions by email except where the portal is unavailable."}])
    S.prose_p()

    # ================================================================== ch11 inspections
    S.h1(11, "Inspections and desk assessment", 151, "assessment")
    S.h2("11.1", "Choosing the assessment method")
    rule_p(S, "BR-ASM-001")
    rule_p(S, "BR-ASM-003", needle="below £7500")
    rule_p(S, "BR-ASM-008", needle="below £3,000")
    S.h2("11.2", "Inspection timescales")
    rule_p(S, "BR-ASM-005", needle="Tier-3: 48 hours", fmt=0)
    S.h2("11.3", "Assessor reports")
    rule_p(S, "BR-ASM-004", needle="at least 6 photos")
    rule_p(S, "BR-ASM-006", needle="within 5 business days of inspection")
    S.h2("11.4", "Coverage decision")
    rule_p(S, "BR-ASM-013", needle="within 3 business days of the assessor report")
    S.h2("11.5", "Re-inspection and drying")
    rule_p(S, "BR-ASM-014", needle="more than 25%")
    rule_p(S, "BR-ASM-019", needle="every 7 days")
    S.h2("11.6", "Contents and total loss")
    rule_p(S, "BR-ASM-018", needle="above £1500")
    rule_p(S, "BR-ASM-017", needle="exceeds 65% of market value")
    S.h2("11.7", "Nordic takst")
    rule_p(S, "BR-ASM-009", needle="above NOK 120000")
    S.table(["Step", "Standard", "Rule"], [
        ["Appoint Claims Assessor", "Within 2 business days of triage", "BR-ASM-002"],
        ["Site inspection", "Within 5 business days of appointment (Tier-3: 48 hours)", "BR-ASM-005 v3"],
        ["Assessor report", "Within 5 business days of inspection", "BR-ASM-006"],
        ["Coverage decision", "Within 3 business days of the assessor report", "BR-ASM-013"],
        ["Drying readings", "Every 7 days", "BR-ASM-019"],
    ], caption="Assessment timescales", widths=[4.5, 8, 3.5])

    # ================================================================== ch12 Nordic
    S.h1(12, "Nordic variations", 166, "nordic")
    S.h2("12.1", "Scope")
    rule_p(S, "BR-TRI-005", fmt=2)
    S.p(runs=[{"text": "Danish claims are handled end to end in Claims Hub."},
              {"text": "", "footnote": {"text": "Wave 0 (Denmark) cut over to Claims Hub on 1 June 2026. Norwegian and Swedish claims remain in CLARA until they migrate.",
                                        "fact": S.fact("footnote", "Footnote: Wave 0 (Denmark) cut over to Claims Hub on 1 June 2026.",
                                                       "Wave 0 (Denmark) cut over to Claims Hub on 1 June 2026", world_ref="WAVE:MW-0#date", mirror=True)}},
              {"text": " The procedures in this chapter apply whichever system holds the claim."}])
    S.h2("12.2", "Tiering in local currency", target=168)
    pl = PL["PL-021"]
    S.p("Nordic claims are tiered on the local-currency amount. The Tier-3 monetary trigger in local currency is "
        "NOK 650,000 / SEK 680,000 / DKK 430,000; the other Tier-3 triggers in section 2.4 apply unchanged.",
        facts=[S.placement_fact(pl, "Nordic Tier-3 equivalents NOK 650,000 / SEK 680,000 / DKK 430,000 repeated in §12.2.",
                                "NOK 650,000 / SEK 680,000 / DKK 430,000", mirror=True)])
    S.prose_p()
    S.h2("12.3", "Excess (egenandel, självrisk, selvrisiko)")
    rows = []
    facts = []
    for i, rid in enumerate(["BR-STL-016", "BR-STL-017", "BR-STL-018", "BR-STL-019", "BR-STL-020", "BR-STL-021"], start=1):
        vv = S.rv(rid)
        rows.append([rid, W.rules[rid]["title"].replace("Excess deduction: ", ""), vv["text"]])
        S.rule_sections.setdefault(rid, "12.3")
        if rid == "BR-STL-020":
            facts.append(S.fact("general", "Hem Sverige självrisk deducted: SEK 2,000 (BR-STL-020).", "SEK 2,000",
                                world_ref="RULE:BR-STL-020@v1", row=i, col=2))
    S.table(["Rule", "Product", "Deduction"], rows, caption="Nordic excess deductions", widths=[3, 4.5, 8.5], facts=facts)
    S.h2("12.4", "Language and correspondence")
    rule_p(S, "BR-REC-017")
    S.prose_p()
    S.h2("12.5", "Payments and currency")
    rule_p(S, "BR-STL-003")
    rule_p(S, "BR-RSV-012", needle="Group Ledger month-end rate")
    S.h2("12.6", "Regress")
    rule_p(S, "BR-REC-008")
    S.figure(figs["nordic"], "Nordic claim routing",
             "Nordic claim routing: claims in Norway, Sweden and Denmark route to Claims Operations Nordics; Danish claims on Claims Hub since Wave 0.",
             alt_facts=[S.fact("alt_text", "Alt text: Nordic claims route to Claims Operations Nordics.", "route to Claims Operations Nordics",
                               world_ref="RULE:BR-TRI-005@v1")])

    # ================================================================== ch13 motor
    S.h1(13, "Motor claims", 183, "motor")
    S.h2("13.1", "Scope")
    S.prose_p()
    S.h2("13.2", "Repair network")
    rule_p(S, "BR-ASM-007")
    v4 = W.vendors["VEN-04"]
    S.p(f"UK repairs are placed with {v4['name']} ({v4['role'].replace('UK motor repair network ', '')}). "
        f"Norwegian repairs use {W.vendors['VEN-05']['name']}.",
        facts=[S.fact("general", "Thistlecombe Repair Network has 212 approved bodyshops and handles UK windscreen.", "212 approved bodyshops",
                      world_ref="VENDOR:VEN-04#role")])
    S.h2("13.3", "Total loss")
    S.p("A vehicle is a total loss on the test in section 11.6. Figure 13-1 shows the total-loss steps; salvage is covered in Chapter 35.")
    S.figure(figs["motor"], "Motor total loss", "Motor total loss: engineer view, total-loss decision, release to Salvanta Salvage within 5 business days, settlement.",
             alt_facts=[S.fact("alt_text", "Alt text: total-loss vehicles released to Salvanta Salvage within 5 business days.",
                               "Salvanta Salvage within 5 business days", world_ref="RULE:BR-REC-007@v1")])
    S.h2("13.4", "Windscreen")
    rule_p(S, "BR-TRI-011")
    S.h2("13.5", "Excess")
    rule_p(S, "BR-STL-013", needle="excess of £250")
    S.table(["Product", "Standard excess", "Windscreen excess"], [
        ["Motor Private UK", "£250", "£95"], ["Motor Privat Norge", "NOK 6,000", "NOK 2,000"],
        ["Motor Privat Sverige", "SEK 3,000", "SEK 1,000"], ["Motor Privat Danmark", "DKK 5,000", "DKK 1,500"]],
        caption="Motor excesses (current product terms)", widths=[6, 5, 5],
        facts=[S.fact("general", "Motor Private UK windscreen excess is £95.", "£95", world_ref="PRODUCT:PRD-MOT-UK#excess", row=1, col=2)])
    S.h2("13.6", "Liability and recoveries")
    rule_p(S, "BR-REC-002")
    S.h2("13.7", "Theft")
    S.prose_p()

    # ================================================================== ch14 home
    S.h1(14, "Home claims", 201, "property")
    S.h2("14.1", "Scope")
    S.prose_p()
    S.h2("14.2", "Escape of water")
    rule_p(S, "BR-STL-015", needle="excess of £400")
    rule_p(S, "BR-REC-016")
    S.prose_p()
    S.h2("14.3", "Storm and flood")
    S.p("Storm notifications carry the weather event code (section 5.9). Flood claims above the Major & Complex Loss "
        "routing limit are routed under BR-TRI-017 (Table 8-1).")
    S.prose_p()
    S.h2("14.4", "Subsidence")
    rule_p(S, "BR-TRI-016")
    S.h2("14.5", "Fire")
    S.p("Fire notifications record whether the fire service attended (BR-FNOL-015). Fire claims with suspected arson "
        "go to SIU pre-screen review (BR-TRI-018).")
    S.h2("14.6", "Contents and cash settlement")
    rule_p(S, "BR-STL-008", needle="75% of replacement cost")
    S.table(["Peril", "Excess (Home Buildings & Contents UK)"], [["Standard", "£250"], ["Escape of water", "£400"], ["Subsidence", "£1,000"]],
            caption="Home UK excesses (current product terms)", widths=[6, 8],
            facts=[S.fact("general", "Home UK subsidence excess is £1,000.", "£1,000", world_ref="PRODUCT:PRD-HOM-UK#excess", row=3, col=1)])

    # ================================================================== ch15 commercial
    S.h1(15, "Commercial property and business interruption", 219, "commercial")
    S.h2("15.1", "Scope")
    S.prose_p()
    S.h2("15.2", "Tiering of business interruption claims")
    rule_p(S, "BR-TRI-013")
    S.h2("15.3", "Forensic review")
    rule_p(S, "BR-RSV-021", needle="above £100000")
    S.h2("15.4", "Expense reserves")
    rule_p(S, "BR-RSV-005", needle="10% on commercial property")
    S.h2("15.5", "Interim payments")
    rule_p(S, "BR-STL-010")
    S.prose_p()

    # ================================================================== ch16 liability
    S.h1(16, "Liability and bodily injury", 233, "liability")
    S.h2("16.1", "Scope")
    S.prose_p()
    S.h2("16.2", "Routing")
    rule_p(S, "BR-TRI-019")
    S.p("Any claim with bodily injury routes to Major & Complex Loss regardless of amount (BR-TRI-002, Table 8-1).")
    S.h2("16.3", "Defence solicitors")
    v8 = W.vendors["VEN-08"]
    S.p(f"{v8['name']} ({v8['location']}) act as defence solicitors for liability and bodily-injury claims.",
        facts=[S.fact("general", "Ravensworth Pike LLP are the defence solicitors for liability and bodily-injury claims.",
                      "Ravensworth Pike LLP", world_ref="VENDOR:VEN-08#role")])
    S.h2("16.4", "Reserving bodily-injury claims")
    rule_p(S, "BR-RSV-004", needle="15% of the indemnity reserve")
    rule_p(S, "BR-RSV-018", needle="more than 12 months")
    S.h2("16.5", "Rehabilitation")
    S.prose_p()

    # ================================================================== ch17 reserving principles
    S.h1(17, "Reserving principles", 249, "reserving")
    S.h2("17.1", "Principles")
    S.prose_ps(2)
    S.h2("17.2", "Reviewing on new information")
    rule_p(S, "BR-RSV-008", needle="within 2 business days of receiving an assessor report")
    S.h2("17.3", "Reason codes")
    rule_p(S, "BR-RSV-015")
    S.h2("17.4", "Large increases")
    rule_p(S, "BR-RSV-013", needle="more than 50%")
    S.h2("17.5", "Recoveries")
    rule_p(S, "BR-RSV-016")
    S.h2("17.6", "Expense and legal reserves")
    rule_p(S, "BR-RSV-002", needle="8% of the indemnity reserve")
    S.table(["Reserve", "Basis", "Rule"], [
        ["Expense reserve: Escape of Water", "8% of the indemnity reserve", "BR-RSV-002"],
        ["Expense reserve: bodily injury", "15% of the indemnity reserve", "BR-RSV-004"],
        ["Expense reserve: commercial property", "10%", "BR-RSV-005"],
        ["Legal reserve when proceedings are issued", "£15000", "BR-RSV-006"]],
        caption="Expense and legal reserves", widths=[6.5, 6, 3.5])
    S.h2("17.7", "Rounding and snapshots")
    rule_p(S, "BR-RSV-020")
    rule_p(S, "BR-RSV-019", needle="retained for 10 years")

    # ================================================================== ch18 reserve authority (split boundary)
    S.h1(18, "Reserve authority", 259, "authority")
    S.p("A case reserve may be set or changed only by a person who holds the authority for the resulting amount. "
        "This chapter sets the limits and the escalation route.")
    S.h2("18.1", "Reserve authority limits")
    S.p("Limits apply to the total case reserve on the claim after the movement, across all reserve types, and are "
        "held by role. Nordic reserves are tested at the GBP equivalent.")
    S.fill_here()
    pl = PL["PL-006"]
    comb = ("Reserve authority (BR-RSV-003 v3): Claims Handler £25,000; Team Leader £100,000; Claims Manager £500,000; "
            "Claims Director £2,000,000; above that the Reserving Committee.")
    fa = S.placement_fact(pl, "Reserve authority (first half, before the page break): Claims Handler £25,000; Team Leader £100,000.",
                          "Team Leader £100,000;", notes="Split across a page break immediately after 'Team Leader £100,000;'. "
                          "Combined statement: " + comb, mirror=True, half="A", ocr_needle="Team Leader £100,000")
    fb = S.placement_fact(pl, "Reserve authority (second half, after the page break): Claims Manager £500,000; Claims Director £2,000,000.",
                          "Claims Manager £500,000; Claims Director £2,000,000", notes="Second half of the split sentence. Combined statement: " + comb,
                          mirror=True, half="B", ocr_needle="Claims Manager £500,000")
    S.p(runs=[{"text": "The reserve authority limits under BR-RSV-003 v3, effective 1 September 2025, are: Claims Handler £25,000; "
                       "Team Leader £100,000;", "break": "page"},
              {"text": " Claims Manager £500,000; Claims Director £2,000,000; above the Claims Director limit, the case reserve "
                       "must be approved by the Reserving Committee. Nordic reserves are tested at the GBP equivalent at the "
                       "GL month-end rate."}], facts=[fa, fb])
    S.rule_sections["BR-RSV-003"] = "18.1"
    S.new_seg("s18b", ("text", "Claims Manager £500,000; Claims Director £2,000,000"), 261)
    S.p("A handler who expects a movement to take the reserve above their limit obtains approval before entering the movement.")
    S.h2("18.2", "Escalation")
    S.figure(figs["authority"], "Reserve authority escalation",
             "Reserve authority escalation: Claims Handler, Team Leader, Claims Manager, Claims Director, Reserving Committee.",
             alt_facts=[S.fact("alt_text", "Alt text: reserve authority escalates from Claims Director to the Reserving Committee.",
                               "Claims Director, Reserving Committee", world_ref="RULE:BR-RSV-003@v3#text")])
    S.prose_p()
    S.h2("18.3", "Overrides and absence")
    S.p("An authority override needs a second approver at the next level (BR-GEN-001, section 3.5).")
    S.prose_p()
    S.h2("18.4", "Nordic reserves")
    S.p("Nordic reserves are held in local currency (section 12.5) and tested against the limits at the GBP equivalent.")
    S.h2("18.5", "Reopened claims")
    rule_p(S, "BR-RSV-017")

    # ================================================================== ch19 reserve reviews
    S.h1(19, "Reserve reviews", 267, "reviews")
    S.h2("19.1", "Purpose of reserve reviews")
    S.prose_ps(2)
    S.h2("19.2", "Event-driven reviews")
    rule_p(S, "BR-RSV-022")
    S.p("Assessor reports trigger a review under BR-RSV-008 (section 17.2).")
    S.h2("19.3", "Long-tail and business interruption reserves")
    S.p("Bodily-injury reserves open for more than 12 months are reviewed quarterly by the Reserving team "
        "(BR-RSV-018, section 16.4). Business Interruption reserves are reviewed under BR-RSV-021 (section 15.3).")
    S.h2("19.4", "Tier-3 reserve reviews", target=271, fill=False)
    pl = PL["PL-002"]
    S.p(runs=[{"text": "Review cadence. ", "bold": True},
              {"text": "Reserves on Tier-3 claims must be reviewed at least every 14 days (BR-RSV-007 v3, effective 1 July 2026)."}],
        facts=[S.placement_fact(pl, "Reserves on Tier-3 claims must be reviewed at least every 14 days (BR-RSV-007 v3, effective 2026-07-01).",
                                "reviewed at least every 14 days", mirror=True,
                                notes="Uses 'Tier-3' without restating the definition, which is in §2.4 about 256 pages earlier (LD001 PL-001).")])
    S.rule_sections["BR-RSV-007"] = "19.4"
    S.p("Each review is recorded in the claim notes with the date, the outcome and the next review date. "
        "Reviews are scheduled automatically, but a scheduled date never replaces a review triggered by new information.")
    S.h2("19.5", "Recording reviews", target=272)
    S.prose_ps(2)
    S.h2("19.6", "Overdue reviews")
    S.prose_p()

    # ================================================================== ch20 indexation
    S.h1(20, "Indexation and currency", 277, "indexation")
    S.h2("20.1", "Purpose")
    S.prose_ps(2)
    S.h2("20.2", "Bodily-injury reserve indexation", target=279)
    pl = PL["PL-011"]
    cfact = S.placement_fact(pl, "Reviewer comment by Lena Kristiansen on §20.2: bodily-injury reserve indexation for 2026 is 3.1% per annum, confirmed with Actuarial.",
                             "3.1% per annum", notes="Exclusive: the rate appears only in this Word comment, never in the LD001 body or in LD002.")
    S.p("Open bodily-injury case reserves are indexed monthly under BR-RSV-009. The annual rate is approved by the "
        "Reserving Committee and applied by the system; handlers must not apply manual uplifts for inflation.",
        comment={"text": "Bodily-injury reserve indexation for 2026 is 3.1% per annum — confirmed with Actuarial. LK",
                 "author": nm("P009"), "initials": "LK", "fact": cfact})
    S.rule_sections["BR-RSV-009"] = "20.2"
    S.prose_p()
    S.h2("20.3", "Currency")
    S.p("Nordic reserves are held in NOK, SEK or DKK. GBP equivalents use the Group Ledger month-end rate (BR-RSV-012, section 12.5).")
    S.h2("20.4", "Year-end revaluation")
    pr = W.programs["CLRGL090"]
    S.p("A full currency revaluation runs at year-end in CLARA (program CLRGL090). In Claims Hub, reserve-engine "
        "revaluation runs from Wave 2.", facts=[S.fact("general", "CLRGL090 runs the year-end currency revaluation in CLARA.",
                                                         "program CLRGL090", world_ref="RULE:BR-RSV-012@v1")])
    S.h2("20.5", "Ceded reserves")
    rule_p(S, "BR-RSV-024")

    # ================================================================== ch21 reserving committee
    S.h1(21, "Reserving Committee", 289, "committee")
    S.p("The Reserving Committee is the senior forum for reserving policy and for the approval of reserves above "
        "the Claims Director's authority.")
    S.h2("21.1", "Constitution and meetings", target=290)
    pl = PL["PL-020"]
    S.p("The Reserving Committee meets on the second Tuesday of each month at 10:00.",
        facts=[S.placement_fact(pl, "The Reserving Committee meets on the second Tuesday of each month at 10:00.",
                                "second Tuesday of each month at 10:00", mirror=True)])
    mem = ", ".join(f"{nm(p)} ({tt(p)})" for p in c1["members"])
    S.p(f"The committee is chaired by {nm(chair)}. Its members are {mem}.",
        facts=[S.fact("general", "Reserving Committee members include the Chief Actuary and the Major & Complex Loss Manager.",
                      f"{nm('P010')} ({tt('P010')})", world_ref="COMMITTEE:COM-01#members")])
    S.h2("21.2", "Remit")
    S.p(f"The committee {c1['remit'][0].lower() + c1['remit'][1:]}.")
    S.prose_p()
    S.h2("21.3", "Matters referred to the committee")
    S.p("Case reserves above the Claims Director limit in Chapter 18 are approved by the committee. Changes to "
        "reserving rules are approved by the committee before they are published.")
    S.h2("21.4", "Papers and minutes")
    S.prose_p()

    # ================================================================== ch22 large losses
    S.h1(22, "Large losses and reinsurance", 297, "largeloss")
    S.h2("22.1", "Purpose")
    S.prose_ps(2)
    S.h2("22.2", "Identifying large losses")
    S.p("A claim becomes a large loss when a reserve movement on it exceeds the LLNT defined in Chapter 2.")
    S.prose_p()
    S.h2("22.3", "Notifying Reinsurance", target=300)
    pl = PL["PL-017"]
    S.p(runs=[{"text": "Notification. ", "bold": True},
              {"text": "Reinsurance must be notified within 24 hours of any reserve movement exceeding the LLNT. "
                       "The notification is made through ReCede and copied to the Reinsurance Manager."}],
        facts=[S.placement_fact(pl, "Reinsurance must be notified within 24 hours of any reserve movement exceeding the LLNT (amount not restated).",
                                "notified within 24 hours of any reserve movement exceeding the LLNT", mirror=True,
                                notes="The LLNT amount (£250,000) is defined only in §2.6 (~p.18).")])
    S.p(f"In CLARA the large loss notification extract is produced by program CLRRS160. The Reinsurance Manager, "
        f"{nm('P038')}, is accountable for the notification.",
        facts=[S.fact("general", "The large loss notification step is accountable to the Reinsurance Manager, Per Øverland.",
                      nm("P038"), world_ref="PROCESS:PS-RSV-04#raci")])
    S.figure(figs["large"], "Large loss notification",
             "Large loss notification: reserve movement exceeds the LLNT, notify Reinsurance through ReCede within 24 hours, then periodic review.",
             facts=[S.fact("image_text", "Large loss diagram: notify Reinsurance (ReCede) within 24 hours.", "within 24 hours",
                           world_ref="RULE:BR-RSV-011@v2#parameters.notify_hours")])
    S.h2("22.4", "Information for reinsurers")
    S.prose_p()
    S.h2("22.5", "Bordereaux")
    S.p(f"Monthly claims bordereaux are sent to reinsurers through {W.system_name('SYS26', d)}.")

    # ================================================================== ch23 major & complex loss
    S.h1(23, "Major and complex loss", 311, "largeloss")
    S.h2("23.1", "Role of Major & Complex Loss")
    S.p(f"Major & Complex Loss is led by {nm(W.team_lead('T09', d))}, {tt(W.team_lead('T09', d))}.")
    S.prose_p()
    S.h2("23.2", "Referral to Major & Complex Loss")
    rule_p(S, "BR-TRI-004", needle="within 4 hours")
    S.h2("23.3", "Strategy notes")
    S.prose_ps(2)
    S.h2("23.4", "Experts")
    S.prose_p()
    S.h2("23.5", "Events affecting several policies")
    S.prose_p()

    # ================================================================== ch24 litigation
    S.h1(24, "Litigation", 323, "litigation")
    S.h2("24.1", "When a claim becomes litigated")
    S.prose_p()
    S.h2("24.2", "Legal reserve")
    rule_p(S, "BR-RSV-006", needle="£15000 when proceedings are issued")
    S.h2("24.3", "Panel solicitors")
    S.p(f"Defence work is placed with {v8['name']}; recovery litigation with {W.vendors['VEN-07']['name']} (Chapter 34).")
    S.h2("24.4", "Court milestones")
    S.p("Litigated claims are re-reserved at every court milestone (BR-RSV-022, section 19.2).")
    S.prose_p()
    S.h2("24.5", "Settlement in proceedings")
    S.prose_p()

    # ================================================================== ch25 payments (tracked change)
    S.h1(25, "Payments and authorities", 333, "payments")
    S.p("This chapter covers the authorisation and release of claim payments.")
    S.h2("25.1", "Principles")
    S.prose_p()
    S.h2("25.2", "Payment authority limits", target=334)
    pl12, pl13 = PL["PL-012"], PL["PL-013"]
    f_ins = S.placement_fact(pl12, "Tracked insertion in §25.2: the Team Leader payment authority is '£75,000' (BR-STL-002 v3).", "£75,000",
                             notes="Inserted by tracked change next to the deleted '£50,000' (LD001 PL-013).")
    f_del = S.placement_fact(pl13, "Tracked deletion in §25.2: the superseded Team Leader payment authority '£50,000' (BR-STL-002 v2).", "£50,000",
                             notes="Deleted text; superseded by the tracked insertion '£75,000' (BR-STL-002 v3).")
    S.p(runs=[{"text": "Payment authority (BR-STL-002 v3, effective 1 September 2025): Claims Handler £15,000; Team Leader "},
              {"del": "£50,000", "author": nm("P011"), "date": "2026-06-18T10:42:00Z", "fact": f_del},
              {"ins": "£75,000", "author": nm("P011"), "date": "2026-06-18T10:42:00Z", "fact": f_ins},
              {"text": "; Claims Manager £350,000; Claims Director £1,500,000."}],
        comment={"text": "Limits as approved under DEC-020 (12 August 2025), effective 1 September 2025.", "author": nm("P011"),
                 "initials": "RT", "fact": S.fact("comment", "Reviewer comment on §25.2: payment limits approved under DEC-020 on 12 August 2025.",
                                                  "DEC-020 (12 August 2025)", world_ref="DECISION:DEC-020")},
        facts=[S.fact("general", "Payment authority: Claims Manager £350,000; Claims Director £1,500,000 (BR-STL-002 v3).",
                      "Claims Manager £350,000; Claims Director £1,500,000", world_ref="RULE:BR-STL-002@v3#parameters", mirror=True)])
    S.rule_sections["BR-STL-002"] = "25.2"
    S.p("No person may authorise a payment above their own limit, and the person requesting a payment may not also approve it.")
    S.h2("25.3", "Payment methods")
    rule_p(S, "BR-STL-001", needle="cheques were withdrawn on 2024-06-30")
    S.table(["Region", "Method"], [["UK", "Faster Payments"], ["Norway, Sweden, Denmark", "SEPA or domestic instant transfer in local currency"]],
            caption="Payment methods", widths=[6, 10])
    S.h2("25.4", "Payee verification")
    rule_p(S, "BR-STL-005")
    S.h2("25.5", "Duplicate payment control")
    rule_p(S, "BR-STL-012", needle="within 7 days are held for review")
    S.h2("25.6", "Vendor invoices")
    rule_p(S, "BR-STL-011", needle="within 30 days of matching")
    S.h2("25.7", "Payment resilience")
    S.p("NISA Circular 2025/02 §3.1 requires an impact tolerance of 48 hours for disruption to claims payments. "
        "Payments Operations maintains the contingency procedures that support it.",
        facts=[S.fact("general", "NISA Circular 2025/02 §3.1: impact tolerance of 48 hours for disruption to claims payments.",
                      "impact tolerance of 48 hours", world_ref="CIRCULAR:CIRC-2025-02#requirements")])

    # ================================================================== ch26 sanctions
    S.h1(26, "Sanctions screening", 345, "sanctions")
    S.h2("26.1", "Requirement")
    rule_p(S, "BR-STL-007")
    S.p("The screening request is sent from CLARA by program CLRST070.")
    S.h2("26.2", "Potential matches")
    S.prose_p()
    S.h2("26.3", "Records")
    S.prose_p()

    # ================================================================== ch27 counter-fraud
    S.h1(27, "Counter-fraud principles", 351, "fraud")
    S.h2("27.1", "Principles and NISA Circular 2026/04")
    circ = W.circulars["CIRC-2026-04"]
    S.p("NISA Circular 2026/04 (Fair Treatment in Fraud Referral) took effect on 1 April 2026. Its requirements are "
        "implemented in this chapter and in Chapters 28 to 30.")
    rows = []
    for rq in circ["requirements"]:
        t_ = rq["text"]
        if rq["para"] == "3.2":
            t_ = "Tell the customer in writing within 10 business days of referral that the claim is subject to additional checks."
        rows.append([f"§{rq['para']}", t_])
    S.table(["Paragraph", "Requirement"], rows, caption="NISA Circular 2026/04 requirements", widths=[2.5, 13.5],
            facts=[S.fact("general", "NISA Circular 2026/04 §3.5: retain referral records for 7 years.", "Retain referral records for 7 years",
                          world_ref="CIRCULAR:CIRC-2026-04#requirements", row=5, col=1)])
    S.prose_p()
    S.h2("27.2", "Sentinel")
    S.p(runs=[{"text": "Every claim is scored by Sentinel at triage (section 8.2)."},
              {"text": "", "footnote": {"text": "Sentinel was known as FRAUDNET until 1 March 2025.",
                                        "fact": S.fact("footnote", "Footnote: Sentinel was known as FRAUDNET until 1 March 2025.",
                                                       "known as FRAUDNET until 1 March 2025", world_ref="SYSTEM:SYS03#renames", mirror=True)}},
              {"text": " A score is an indicator of risk, not a finding."}])
    S.prose_p()
    S.h2("27.3", "Pre-screen indicators")
    rows = []
    for rid in ["BR-FRD-001", "BR-FRD-002", "BR-FRD-003", "BR-FRD-004", "BR-FRD-006", "BR-FRD-007", "BR-FRD-008",
                "BR-FRD-009", "BR-FRD-014", "BR-FRD-015", "BR-FRD-016"]:
        vv = S.rv(rid)
        rows.append([rid, W.rules[rid]["title"].replace("Indicator: ", ""), vv["text"]])
        S.rule_sections.setdefault(rid, "27.3")
    S.table(["Rule", "Indicator", "Pre-screen points"], rows, caption="Pre-screen fraud indicators", widths=[2.8, 5, 8.2],
            facts=[S.fact("general", "BR-FRD-009: add 20 pre-screen points when the payee bank account is linked to 2 or more claimants.",
                          "Add 20 pre-screen points", world_ref="RULE:BR-FRD-009@v1", row=8, col=2),
                   S.fact("general", "BR-FRD-008 v2: add 14 pre-screen points when photo metadata dates differ from the date of loss.",
                          "Add 14 pre-screen points", world_ref="RULE:BR-FRD-008@v2", row=7, col=2)])
    S.h2("27.4", "Linked claims")
    rule_p(S, "BR-FRD-005", needle="2 or more claims in 12 months")
    S.h2("27.5", "Indicators by peril")
    S.prose_ps(2)
    S.h2("27.6", "Claims Fraud Forum")
    S.p("The Claims Fraud Forum (section 3.4) reviews fraud rules, Sentinel thresholds and SIU performance.")
    S.h2("27.7", "Training")
    rule_p(S, "BR-FRD-018", needle="every 12 months")
    S.h2("27.8", "Fraud savings")
    rule_p(S, "BR-FRD-013")
    S.h2("27.9", "Regulatory returns")
    S.p(runs=[{"text": "BR-FRD-034. ", "bold": True}, {"text": S.rv("BR-FRD-034")["text"]}],
        facts=[S.fact("general", "NISA-FR1 is due within 30 calendar days after each quarter end; first return Q2 2026 due 2026-07-30.",
                      "first return for Q2 2026 due 2026-07-30", world_ref="RULE:BR-FRD-034@v1", mirror=True)])
    S.rule_sections["BR-FRD-034"] = "27.9"
    S.h2("27.10", "SIU partner")
    rule_p(S, "BR-FRD-010")
    S.p(f"{W.vendors['VEN-10']['name']} provides {W.vendors['VEN-10']['role'].replace('SIU partner: ', '')}.")

    # ================================================================== ch28 referral to SIU
    S.h1(28, "Referral to SIU", 405, "fraud")
    S.h2("28.1", "When to refer")
    S.prose_ps(2)
    S.h2("28.2", "Pre-screen reviews")
    S.p("Theft claims without a police reference (BR-TRI-010) and fire claims with suspected arson (BR-TRI-018) go to "
        "SIU pre-screen review before any referral decision.")
    S.prose_p()
    S.h2("28.3", "Referral threshold", target=411)
    pl = PL["PL-003"]
    S.p(runs=[{"text": "Threshold. ", "bold": True},
              {"text": "Refer a claim to SIU when the Sentinel score is 65 or more, for all tiers (BR-FRD-031 v1, effective 1 April 2026)."}],
        facts=[S.placement_fact(pl, "Refer a claim to SIU when the Sentinel score is 65 or more, for all tiers (BR-FRD-031 v1).",
                                "Sentinel score is 65 or more, for all tiers", mirror=True,
                                notes="Superseded for Tier-3 claims from 2026-10-01 (threshold 60, BR-FRD-031 v2; DEC-014) - see C01.")],
        comment={"text": "Threshold confirmed against NISA Circular 2026/04 §3.3.", "author": nm("P008"), "initials": "NB"})
    S.rule_sections["BR-FRD-031"] = "28.3"
    S.figure(figs["referral"], "Referral decision",
             "Referral decision: a Sentinel score of 65 or more leads to referral to SIU; otherwise the claim continues to assessment.",
             facts=[S.fact("image_text", "Referral diagram: Sentinel score of 65 or more leads to Referral to SIU.",
                           "Referral to SIU", world_ref="RULE:BR-FRD-031@v1#parameters.threshold")],
             alt_facts=[S.fact("alt_text", "Alt text: a Sentinel score of 65 or more leads to referral to SIU.",
                               "Sentinel score of 65 or more leads to referral to SIU", world_ref="RULE:BR-FRD-031@v1")])
    S.h2("28.4", "Making the referral")
    S.p("In CLARA the referral is created on map CLRM410 (transaction FR03, program CLRFR030), which reads the "
        "threshold from CLR.T_PARAM. The referral and the SIU case are created the same business day.",
        facts=[S.fact("general", "CLARA program CLRFR030 creates fraud referrals online and reads the threshold from CLR.T_PARAM.",
                      "reads the threshold from CLR.T_PARAM", world_ref="PROGRAM:CLRFR030")])
    S.h2("28.5", "Handling the claim while it is referred")
    S.prose_p()
    S.h2("28.6", "No adverse decision on the score alone", target=416)
    pl = PL["PL-005"]
    S.p(runs=[{"text": "BR-FRD-033. ", "bold": True},
              {"text": "No claim may be declined, reduced or repudiated on an automated fraud score alone; SIU must document a human "
                       "review before any adverse outcome."}],
        facts=[S.placement_fact(pl, "No claim may be declined, reduced or repudiated on an automated fraud score alone; SIU must document a human review (BR-FRD-033).",
                                "declined, reduced or repudiated on an automated fraud score alone", mirror=True)])
    S.rule_sections["BR-FRD-033"] = "28.6"
    S.h2("28.7", "Human review")
    S.p("The documented human review takes place within 5 business days of the SIU outcome and is recorded in the SIU Case Manager.",
        facts=[S.fact("general", "Human review of an adverse outcome within 5 business days of the SIU outcome.",
                      "within 5 business days of the SIU outcome", world_ref="PROCESS:PS-FRD-05#sla")])
    S.prose_p()

    # ================================================================== ch29 customer notification
    S.h1(29, "Customer notification of referral", 421, "notification")
    S.h2("29.1", "The customer notice")
    pl = PL["PL-004"]
    S.p(runs=[{"text": "Notice. ", "bold": True},
              {"text": "The customer must be told in writing within 10 business days of a fraud referral that the claim is subject "
                       "to additional checks (BR-FRD-032 v2)."}],
        facts=[S.placement_fact(pl, "The customer must be told in writing within 10 business days of a fraud referral that the claim is subject to additional checks (BR-FRD-032 v2).",
                                "within 10 business days of a fraud referral", mirror=True)],
        comment={"text": "Wording checked against NISA Circular 2026/04 §3.2.", "author": nm("P037"), "initials": "RO"})
    S.rule_sections["BR-FRD-032"] = "29.1"
    S.figure(figs["notice"], "Customer notice timeline",
             "Customer notice: referral to SIU, written notice to the customer within 10 business days unless deferred.",
             alt_facts=[S.fact("alt_text", "Alt text: written notice within 10 business days unless deferred.",
                               "within 10 business days unless deferred", world_ref="RULE:BR-FRD-032@v2")])
    S.h2("29.2", "Content of the notice")
    S.p("The notice is sent by Notify using the approved template. It says that the claim is subject to additional checks; "
        "it does not allege fraud.")
    S.prose_p()
    S.h2("29.3", "Deferral of the notice", target=424)
    pl = PL["PL-008"]
    fn = S.placement_fact(pl, "A deferral of the customer notice must be approved by the SIU Investigations Manager (UK) or the Head of Counter-Fraud & SIU (BR-FRD-036 v1).",
                          "SIU Investigations Manager (UK) or the Head of Counter-Fraud & SIU", mirror=True,
                          notes="Exclusive: approvers stated only in this footnote (and its scan LD002).")
    S.p(runs=[{"text": "Where SIU certifies a tipping-off risk, the notice may be deferred under BR-FRD-036, with the approval "
                       "that rule requires."},
              {"text": "", "footnote": {"text": "BR-FRD-036 v1: the customer notice may be deferred for up to 60 days where SIU certifies a "
                                                "tipping-off risk. The deferral must be approved by the SIU Investigations Manager (UK) or the "
                                                "Head of Counter-Fraud & SIU.", "fact": fn}},
              {"text": " The deferral, its reason and its end date are recorded on the referral."}])
    S.rule_sections["BR-FRD-036"] = "29.3"
    S.h2("29.4", "Recording deferrals")
    S.p("In CLARA deferrals are recorded on map CLRM420 (transaction FR12, program CLRFR120).",
        facts=[S.fact("general", "Customer-notice deferrals are recorded in CLARA on map CLRM420, transaction FR12.", "transaction FR12",
                      world_ref="BMS:CLRM420")])
    S.prose_p()

    # ================================================================== ch30 SIU investigation
    S.h1(30, "SIU investigation", 427, "siu")
    S.h2("30.1", "Triage of new referrals")
    rule_p(S, "BR-FRD-035", needle="within 3 business days")
    S.h2("30.2", "Investigation planning")
    S.prose_p()
    S.h2("30.3", "Surveillance")
    S.p("Surveillance requires written approval under BR-FRD-010 (section 27.10).")
    S.h2("30.4", "Outcomes")
    rule_p(S, "BR-FRD-011", needle="NF (no fraud), CF (confirmed fraud) or WD (withdrawn)")
    S.h2("30.5", "Feedback to handlers")
    rule_p(S, "BR-FRD-017", needle="within 2 business days of case closure")
    S.h2("30.6", "Case records")
    S.p(f"SIU cases are held in the {W.system_name('SYS22', d)}.")

    # ================================================================== ch31 settlement (split across heading)
    S.h1(31, "Settlement", 435, "settlement")
    S.h2("31.1", "Settlement principles")
    S.prose_ps(2)
    S.figure(figs["settle"], "Settlement and closure",
             "Settlement and closure: settlement offer within 5 business days of the coverage decision, payment authorisation, "
             "sanctions screening and payment, close claim and zero reserve within 1 business day.",
             alt_facts=[S.fact("alt_text", "Alt text: settlement offer within 5 business days of the coverage decision.",
                               "within 5 business days of the coverage decision", world_ref="PROCESS:PS-STL-01#sla")])
    S.h2("31.2", "Settlement offers")
    S.prose_p()
    comb2 = "A settlement offer remains valid for 30 days from the offer date (BR-STL-004)."
    fa2 = S.fact("split_boundary", "Settlement offer validity, first half (before the heading 31.3): the offer remains open for a fixed period under BR-STL-004.",
                 "remains open for acceptance for a fixed period, which under BR-STL-004 is", world_ref="RULE:BR-STL-004@v1",
                 notes="Split across two paragraphs separated by the heading '31.3 Offer validity'. Combined statement: " + comb2,
                 mirror=True, ocr_needle="for a fixed period, which under BR-STL-004 is")
    S.p("Every settlement offer issued under this chapter states the date on which it was made, and it remains open for "
        "acceptance for a fixed period, which under BR-STL-004 is", facts=[fa2])
    S.h2("31.3", "Offer validity")
    fb2 = S.fact("split_boundary", "Settlement offer validity, second half (after the heading 31.3): 30 days from the offer date.",
                 "30 days from the offer date", world_ref="RULE:BR-STL-004@v1#parameters.validity_days",
                 notes="Continues the sentence split by the heading. Combined statement: " + comb2, mirror=True)
    S.p("30 days from the offer date. An offer that has expired may be reissued only after the case reserve and the cover "
        "position have been re-checked.", facts=[fb2])
    S.rule_sections["BR-STL-004"] = "31.2"
    S.h2("31.4", "Excess deductions")
    S.p("Excesses are deducted as set out in sections 12.3, 13.5 and 14.6.")
    S.h2("31.5", "Settlement letters")
    rule_p(S, "BR-STL-006", needle="STL01 to STL09")
    S.h2("31.6", "Interest on late payment")
    rule_p(S, "BR-STL-014", needle="3.5% per annum from day 31")

    # ================================================================== ch32 closure
    S.h1(32, "Closure", 447, "closure")
    S.h2("32.1", "Closing the claim")
    rule_p(S, "BR-RSV-014", needle="within 1 business day")
    S.h2("32.2", "Nil reserves")
    rule_p(S, "BR-RSV-010", needle="close within 5 business days")
    rule_p(S, "BR-RSV-023")
    S.h2("32.3", "Reopening")
    S.p("A reopened claim needs a new reserve under BR-RSV-017 (section 18.5).")

    # ================================================================== ch33 recoveries overview
    S.h1(33, "Recoveries overview", 451, "recoveries")
    S.h2("33.1", "Ownership and scope")
    pl = PL["PL-015"]
    S.p(runs=[{"text": f"The recovery & subrogation process is owned by the Head of Recoveries & Subrogation, {nm('P013')}, "
                       f"since 1 September 2025."},
              {"text": "", "footnote": {"text": "Recoveries & Subrogation became a Group function on 1 September 2025 (DEC-004).",
                                        "fact": S.fact("footnote", "Footnote: Recoveries & Subrogation became a Group function on 1 September 2025 (DEC-004).",
                                                       "became a Group function on 1 September 2025", world_ref="DECISION:DEC-004", mirror=True)}},
              {"text": f" {nm('P014')}, {tt('P014')}, leads the UK recoveries team."}],
        facts=[S.placement_fact(pl, "The recovery & subrogation process is owned by the Head of Recoveries & Subrogation, Freya Lindahl, since 2025-09-01.",
                                "Head of Recoveries & Subrogation, Freya Lindahl", mirror=True)])
    S.h2("33.2", "Identifying recovery potential")
    rule_p(S, "BR-REC-001", needle="within 10 business days")
    S.figure(figs["recovery"], "Recovery and subrogation process",
             "Recovery and subrogation: identify recovery potential, open subrogation case and demand, solicitor referral at £25,000 or more "
             "or where liability is defended, receipt and reserve adjustment, write-off approval.",
             facts=[S.fact("image_text", "Recovery diagram: solicitor referral at £25,000 or more or where liability is defended.",
                           "Solicitor referral", world_ref="RULE:BR-REC-005@v2")])
    S.h2("33.3", "Systems")
    S.p(f"Subrogation cases are tracked in the {W.system_name('SYS24', d)}, which is being replaced by "
        f"{W.service_name('recovery-svc', d)} in Claims Hub (retirement target 31 December 2026).",
        facts=[S.fact("general", "The Subrogation Tracker has a retirement target of 31 December 2026.", "retirement target 31 December 2026",
                      world_ref="SYSTEM:SYS24")])

    # ================================================================== ch34 subrogation
    S.h1(34, "Subrogation", 457, "recoveries")
    S.p("This chapter sets out when and how Corvane pursues recoveries from responsible third parties.")
    S.h2("34.1", "Pursuit threshold", target=458)
    pl = PL["PL-014"]
    S.p(runs=[{"text": "Threshold. ", "bold": True},
              {"text": "Subrogation is pursued where the recoverable amount is £1,000 or more (NOK 13,000 / SEK 13,500 / DKK 8,600) "
                       "(BR-REC-003 v3, effective 1 September 2025)."}],
        facts=[S.placement_fact(pl, "Subrogation is pursued where the recoverable amount is £1,000 or more (BR-REC-003 v3, from 2025-09-01).",
                                "recoverable amount is £1,000 or more", mirror=True)],
        comment={"text": "Nordic equivalents agreed with Claims Operations Nordics.", "author": nm("P013"), "initials": "FL"})
    S.rule_sections["BR-REC-003"] = "34.1"
    S.table(["Currency", "Minimum recoverable amount"], [["GBP", "£1,000"], ["NOK", "NOK 13,000"], ["SEK", "SEK 13,500"], ["DKK", "DKK 8,600"]],
            caption="Subrogation pursuit thresholds (BR-REC-003 v3)", widths=[4, 8],
            facts=[S.fact("general", "Subrogation threshold in Sweden: SEK 13,500.", "SEK 13,500", world_ref="RULE:BR-REC-003@v3#parameters.min_sek", row=3, col=1)])
    S.h2("34.2", "Demands and chasing")
    rule_p(S, "BR-REC-012", needle="chased at 28 days")
    S.h2("34.3", "Solicitor referral")
    rule_p(S, "BR-REC-005", needle="£25,000 or more")
    S.h2("34.4", "Uninsured third parties")
    rule_p(S, "BR-REC-006", needle="after 60 days")
    S.h2("34.5", "Limitation")
    rule_p(S, "BR-REC-009", needle="30 months for bodily-injury recoveries")
    S.h2("34.6", "Knock-for-knock")
    rule_p(S, "BR-REC-013")
    S.h2("34.7", "Excess refunds")
    rule_p(S, "BR-REC-004", needle="within 10 business days of a full recovery")
    S.h2("34.8", "Write-offs")
    rule_p(S, "BR-REC-011", needle="above £10,000 require approval by the Head of Recoveries & Subrogation")
    S.h2("34.9", "Recovery MI")
    rule_p(S, "BR-REC-014")

    # ================================================================== ch35 salvage
    S.h1(35, "Salvage", 467, "salvage")
    S.h2("35.1", "Salvage agent")
    rule_p(S, "BR-REC-007", needle="within 5 business days of the total-loss decision")
    S.h2("35.2", "Salvage categories")
    rule_p(S, "BR-REC-010", needle="A and B are scrapped")
    S.h2("35.3", "Salvage proceeds")
    rule_p(S, "BR-REC-015", needle="within 3 business days of receipt")

    # ================================================================== ch36 data retention
    S.h1(36, "Data retention and records", 473, "records")
    S.h2("36.1", "Retention periods")
    rule_p(S, "BR-GEN-004", needle="15 years after closure", fmt=0)
    S.table(["Record", "Retention", "Source"], [
        ["Claim records", "7 years after closure", "BR-GEN-004 v3"],
        ["Bodily-injury claim records", "15 years after closure", "BR-GEN-004 v3"],
        ["Fraud referral records", "7 years", "NISA Circular 2026/04 §3.5"],
        ["Telephone FNOL recordings", "24 months", "BR-GEN-010"],
        ["Month-end reserve snapshots", "10 years", "BR-RSV-019"]],
        caption="Retention periods", widths=[6, 5, 5])
    S.h2("36.2", "Subject access requests")
    rule_p(S, "BR-GEN-002", needle="within 30 calendar days")
    S.h2("36.3", "Test environments")
    S.p("Production personal data is never used in test or development environments (BR-GEN-006, section 6.4).")
    S.h2("36.4", "Audit trail")
    rule_p(S, "BR-GEN-008")
    S.h2("36.5", "Call recordings")
    rule_p(S, "BR-GEN-010", needle="kept for 24 months")

    # ================================================================== ch37 appendices
    S.topic = "governance"
    S.new_seg("ch37", ("heading", "37 Appendices A–D"), 481)
    S.blocks.append({"t": "section"})
    S.blocks.append({"t": "h1", "text": "37 Appendices A–D", "break": False})
    S.chapter, S.section, S.h3n = 37, "37", 0
    S.tab_n[37] = 0
    S.fig_n[37] = 0
    S.h2("37.1", "Appendix A — Rule register")
    S.p("The register lists every rule in force on 1 July 2026 with its version, effective date and owner, and the "
        "section of this manual where it is applied. Parameter values are given in the sections, not here.")
    rows = []
    reg_facts = []
    for rid in sorted(W.rules):
        vv = W.rule_version(rid, AS_OF)
        if not vv:
            continue
        sec = S.rule_sections.get(rid, "—")
        owner = W.rules[rid]["owner"]
        rows.append([rid, W.rules[rid]["title"], f"v{vv['version']}", vv["effective_from"], nm(owner) if owner in W.people else owner, sec])
        if rid == "BR-RSV-007":
            reg_facts.append(S.fact("general", "Rule register: BR-RSV-007 is at version 3, effective 2026-07-01.", "2026-07-01",
                                    world_ref="RULE:BR-RSV-007@v3#effective_from", row=len(rows), col=3))
        if rid == "BR-FRD-031":
            reg_facts.append(S.fact("general", f"Rule register: BR-FRD-031 owner is {nm(owner)}.", nm(owner),
                                    world_ref="RULE:BR-FRD-031#owner", row=len(rows), col=4))
    S.table(["Rule", "Title", "Ver.", "Effective", "Owner", "Section"], rows, caption="Rule register (rules in force on 1 July 2026)",
            widths=[2.5, 5.8, 1.1, 2.2, 3.0, 1.4], size=8, facts=reg_facts)
    S.h2("37.2", "Appendix B — Checklists")
    S.p("The checklists below support the procedures in this manual. They do not replace them.")
    S.table(["Check", "Done"], [[x, "☐"] for x in [
        "Mandatory FNOL data captured (Table 6-1)", "Policy and cover dates validated", "Duplicate and late-notification checks completed",
        "Customer acknowledged (section 5.4)", "Vulnerability indicator recorded", "Default reserve created"]], caption="FNOL checklist", widths=[13, 3])
    S.table(["Check", "Done"], [[x, "☐"] for x in [
        "Tier confirmed against section 2.4", "Major & Complex Loss alerted", "Strategy note on file", "Case reserve reviewed at the required cadence",
        "Large loss notification considered (Chapter 22)", "Recovery potential considered"]], caption="Tier-3 file checklist", widths=[13, 3])
    S.table(["Check", "Done"], [[x, "☐"] for x in [
        "Referral recorded the same business day", "Customer notice sent or deferral approved and recorded", "No adverse decision without documented human review",
        "SIU outcome fed back to the handler"]], caption="Referral checklist", widths=[13, 3])
    S.h2("37.3", "Appendix C — Directory")
    rows = []
    for t_ in team_ids + ["T13", "T14", "T15", "T19", "T20"]:
        lead = W.team_lead(t_, d)
        rows.append([W.team_name(t_, d), nm(lead) if lead else "—", tt(lead) if lead else "—"])
    S.table(["Team", "Lead", "Role"], rows, caption="Team directory", widths=[6, 4.5, 5.5])
    S.h2("37.4", "Appendix D — System reference")
    rows = [[m["map"], m["transaction"], m["program"], m["title"]] for m in W.bms_maps.values()]
    S.table(["Map", "Transaction", "Program", "Function"], rows, caption="CLARA screens", widths=[2.5, 2.8, 3, 7.7],
            facts=[S.fact("general", "CLARA map CLRM620 (transaction RC02, program CLRRC020) is the subrogation case screen.",
                          "Subrogation case", world_ref="BMS:CLRM620", row=[i for i, m in enumerate(W.bms_maps.values()) if m["map"] == "CLRM620"][0] + 1, col=3)])
    rows = [[W.service_name(n, d), s_["description"].split(";")[0].rstrip(".")] for n, s_ in W.services.items()]
    S.table(["Claims Hub service", "Purpose"], rows, caption="Claims Hub services", widths=[4.5, 11.5])
    S.p("The tables below list the input fields of the CLARA screens referred to in this manual.")
    for m in W.bms_maps.values():
        if m["map"] == "CLRM010":
            continue
        S.table(["Field", "Row", "Column", "Length", "Attributes"],
                [[f["name"], f["row"], f["col"], f["length"], f["attr"]] for f in m["fields"]],
                caption=f"Map {m['map']} — {m['title']} (transaction {m['transaction']})", widths=[4.5, 2, 2, 2, 5.5], size=8.5)
    S.finish(496)
    return S


# ---------------------------------------------------------------------------------------------
def _default_reserve_table(S: Spec, W):
    prods = yaml.safe_load(open(util.ROOT / "world" / "data" / "products.yaml", encoding="utf-8"))["products"]
    cts = {c["id"]: c for c in yaml.safe_load(open(util.ROOT / "world" / "data" / "claim_types.yaml", encoding="utf-8"))["claim_types"]}
    by_code = {p["code"]: p for p in prods}
    order = ["MOTUK", "MOTNO", "MOTSE", "MOTDK", "LIAUK", "HOMUK", "HOMNO", "HOMSE", "HOMDK", "COMUK"]
    dr = S.rv("BR-FNOL-005")["parameters"]["default_reserve"]
    notes_bank = {
        "COL": ["Confirm liability early; the default reflects own-damage only.", "Replace once the engineer's estimate is received.",
                "Third-party exposure is reserved separately.", "Check hire and storage before replacing the default."],
        "THF": ["Check the police crime reference before replacing the default.", "Recovered vehicles or items reduce the reserve.",
                "Keys and documents must be accounted for.", "Contents theft: check proof of ownership."],
        "WSC": ["Glass network repairs are normally settled direct.", "Desk-assessed in all cases.",
                "Replace the default once the network invoice is received."],
        "FIR": ["Confirm whether the fire service attended.", "Suspected arson goes to SIU pre-screen review.",
                "Major fires route to Major & Complex Loss.", "Consider alternative accommodation costs."],
        "VAN": ["Police report recommended.", "Check for repeat incidents at the same address.", "Photographs are required."],
        "BIJ": ["Specialist handling; routes to Major & Complex Loss.", "Expense reserve is set separately.",
                "Medical evidence drives the claim-specific reserve.", "Consider rehabilitation needs."],
        "TPD": ["Liability decision determines the reserve.", "Obtain the third party's estimate.", "Check for recovery potential."],
        "EOW": ["Establish the source of the leak first.", "Drying readings are monitored by the contractor.",
                "Neighbour escapes are pursued as recoveries.", "Expense reserve is set separately."],
        "STM": ["Tag with the weather event code.", "Surge mode may apply during major events.", "Check for pre-existing wear and tear."],
        "FLD": ["Large floods route to Major & Complex Loss.", "Check flood defences and warnings.", "Consider alternative accommodation."],
        "SUB": ["External Claims Assessor required.", "Routes to Property Claims – Leeds.", "Monitoring may be needed before repair."],
        "ACD": ["Check the accidental damage extension on the schedule.", "Single-item claims are often desk-assessed."],
        "BIN": ["Always Tier-2 or above.", "Forensic accountant review for larger claims.", "Agree the indemnity period with the insured."],
        "PLB": ["Injury claims are always Tier-3.", "Defence solicitors are instructed where proceedings are issued."],
        "FRO": ["Nordic peril: check heating and maintenance conditions.", "Burst pipes are handled as water damage."],
        "SNO": ["Nordic peril: check roof load and clearance records.", "Structural damage needs an on-site takst."],
    }
    rows, pools = [], []
    eow_row = None
    for code in order:
        p = by_code[code]
        cur = p["currency"]
        for ct in p["claim_types"]:
            c = cts[ct]
            key = f"{code}/{c['peril_code']}"
            peril = c["name"]
            if p["region"] != "UK" and (c.get("local_names") or {}).get(p["region"]):
                peril = f"{c['name']} ({c['local_names'][p['region']]})"
            if key in dr:
                val = _amt(cur, dr[key])
            else:
                val = "Not tabled"
            rows.append([code, p["name"], c["peril_code"], peril, val, ""])
            bank = list(notes_bank.get(c["peril_code"], ["Replace with a claim-specific reserve as soon as the facts allow."]))
            if key not in dr:
                bank = ["No tabled default: set a claim-specific reserve (BR-RSV-001)."] + bank
            pools.append(bank + ["Record the reason code for the replacement movement.", "Review again when the assessor report is received."])
            if key == "HOMUK/EOW":
                eow_row = len(rows)
    facts = []
    pl = S.PL["PL-007"]
    facts.append(S.placement_fact(pl, "Default reserve table 7-1: Home UK / Escape of Water default reserve £4,200 (BR-FNOL-005 v2).", "£4,200",
                                  row=eow_row, col=4, mirror=True,
                                  notes="Table 7-1 spans pages 88-92; the header row appears only on the first page of the table "
                                        "(no repeating header row); the Escape of Water row is on the third page of the table (p.90)."))
    for key, label in [("MOTUK/COL", "Motor Private UK / Collision"), ("LIAUK/BIJ", "SME Liability UK / Bodily Injury"),
                       ("HOMSE/EOW", "Hem Sverige / Escape of Water"), ("MOTNO/COL", "Motor Privat Norge / Collision")]:
        code, peril = key.split("/")
        ri = [i for i, r in enumerate(rows, start=1) if r[0] == code and r[2] == peril][0]
        facts.append(S.fact("multipage_table", f"Default reserve table 7-1: {label} default reserve {rows[ri - 1][4]} (BR-FNOL-005 v2).",
                            rows[ri - 1][4], world_ref=f"RULE:BR-FNOL-005@v2#parameters.default_reserve.{key}", row=ri, col=4))
    S.rule_sections["BR-FNOL-005"] = "7.2"
    S.tab_n[7] = S.tab_n.get(7, 0) + 1
    S.blocks.append({"t": "table", "header": ["Product", "Product name", "Peril", "Claim type", "Default reserve", "Handling note"],
                     "rows": rows, "caption": f"Table 7-{S.tab_n[7]}: Default indemnity reserves at FNOL (BR-FNOL-005 v2, 2025 values)",
                     "facts": facts, "widths": [1.7, 3.3, 1.2, 3.5, 2.3, 4.4], "size": 8.5, "repeat_header": False,
                     "cant_split": True, "fill_seg": S.cur_seg["id"], "notes_col": 5, "notes_pool": pools})
    S.eow_row = eow_row


# ---------------------------------------------------------------------------------------------
def _figures(fig_dir: pathlib.Path) -> dict:
    specs = {
        "fnol": {"title": "FNOL process", "cols": 5, "rows": 1, "cell": (520, 300), "nodes": {
            "a": (0, 0, "Receive notification", "box"), "b": (1, 0, "Validate policy and cover", "box"),
            "c": (2, 0, "Create claim and default reserve", "box"), "d": (3, 0, "Duplicate and late checks", "box"),
            "e": (4, 0, "Acknowledge customer", "end")},
            "edges": [("a", "b", "within 1 hour"), ("b", "c", "within 15 min"), ("c", "d", "same day"), ("d", "e", "")]},
        "triage": {"title": "Triage routing", "cols": 4, "rows": 3, "nodes": {
            "a": (0, 1, "Sentinel pre-screen", "box"), "b": (1, 1, "Tier classification", "box"), "c": (2, 1, "Route claim", "decision"),
            "d": (2, 0, "Counter-Fraud & SIU", "end"), "e": (3, 1, "Major & Complex Loss", "end"), "f": (3, 2, "Fast-track", "end"),
            "g": (1, 2, "Assessment", "box")},
            "edges": [("a", "b", "15 minutes"), ("b", "c", "4 hours"), ("c", "d", "Referral threshold met", "v"),
                      ("c", "e", "Tier-3"), ("c", "f", "Eligible Tier-1", "vh"), ("c", "g", "Otherwise", "vh")]},
        "assess": {"title": "Claims Assessor appointment", "cols": 4, "rows": 2, "nodes": {
            "a": (0, 0, "Triage complete", "box"), "b": (1, 0, "External assessor needed?", "decision"),
            "c": (2, 0, "UK panel loss adjuster", "box"), "d": (2, 1, "Norrvik (Nordic instructions)", "box"),
            "e": (1, 1, "Claims Assessor (internal)", "box"), "f": (3, 0, "Inspection or desk assessment", "end")},
            "edges": [("a", "b", ""), ("b", "c", "Yes - UK"), ("b", "d", "Yes - Nordic", "vh"), ("b", "e", "No"), ("c", "f", "2 business days")]},
        "nordic": {"title": "Nordic claim routing", "cols": 3, "rows": 2, "nodes": {
            "a": (0, 0, "Nordic FNOL (NO, SE, DK)", "box"), "b": (1, 0, "Claims Operations Nordics", "box"),
            "c": (2, 0, "CLARA (Norway, Sweden)", "end"), "d": (2, 1, "Claims Hub (Denmark, Wave 0)", "end")},
            "edges": [("a", "b", ""), ("b", "c", ""), ("b", "d", "", "vh")]},
        "motor": {"title": "Motor total loss", "cols": 4, "rows": 1, "nodes": {
            "a": (0, 0, "Engineer's view", "box"), "b": (1, 0, "Total-loss decision", "decision"),
            "c": (2, 0, "Release to Salvanta", "box"), "d": (3, 0, "Settle market value", "end")},
            "edges": [("a", "b", ""), ("b", "c", "5 business days"), ("c", "d", "")]},
        "authority": {"title": "Reserve authority escalation", "cols": 5, "rows": 1, "cell": (500, 260), "nodes": {
            "a": (0, 0, "Claims Handler", "box"), "b": (1, 0, "Team Leader", "box"), "c": (2, 0, "Claims Manager", "box"),
            "d": (3, 0, "Claims Director", "box"), "e": (4, 0, "Reserving Committee", "end")},
            "edges": [("a", "b", "above limit"), ("b", "c", "above limit"), ("c", "d", "above limit"), ("d", "e", "above limit")]},
        "large": {"title": "Large loss notification", "cols": 4, "rows": 1, "nodes": {
            "a": (0, 0, "Reserve movement", "box"), "b": (1, 0, "Exceeds LLNT?", "decision"),
            "c": (2, 0, "Notify Reinsurance (ReCede)", "box"), "d": (3, 0, "Strategy and review", "end")},
            "edges": [("a", "b", ""), ("b", "c", "within 24 hours"), ("c", "d", "")]},
        "referral": {"title": "Referral decision", "cols": 3, "rows": 2, "nodes": {
            "a": (0, 0, "Sentinel score received", "box"), "b": (1, 0, "Sentinel score of 65 or more?", "decision"),
            "c": (2, 0, "Referral to SIU", "end"), "d": (1, 1, "Continue to assessment", "box")},
            "edges": [("a", "b", ""), ("b", "c", "Yes"), ("b", "d", "No")]},
        "notice": {"title": "Customer notice", "cols": 3, "rows": 2, "nodes": {
            "a": (0, 0, "Referral to SIU", "box"), "b": (1, 0, "Tipping-off risk certified?", "decision"),
            "c": (2, 0, "Written notice to customer", "end"), "d": (1, 1, "Deferral approved and recorded", "box")},
            "edges": [("a", "b", ""), ("b", "c", "No: 10 business days"), ("b", "d", "Yes")]},
        "settle": {"title": "Settlement and closure", "cols": 4, "rows": 1, "nodes": {
            "a": (0, 0, "Settlement offer", "box"), "b": (1, 0, "Payment authorisation", "box"),
            "c": (2, 0, "Sanctions screening and payment", "box"), "d": (3, 0, "Close claim and zero reserve", "end")},
            "edges": [("a", "b", "accepted"), ("b", "c", "same day"), ("c", "d", "1 business day")]},
        "recovery": {"title": "Recovery and subrogation", "cols": 4, "rows": 2, "nodes": {
            "a": (0, 0, "Identify recovery potential", "box"), "b": (1, 0, "Open case and demand", "box"),
            "c": (2, 0, "Solicitor referral", "box"), "d": (3, 0, "Receipt and reserve adjustment", "end"),
            "e": (1, 1, "Write-off approval", "box")},
            "edges": [("a", "b", "10 business days"), ("b", "c", "£25,000 or defended"), ("c", "d", ""), ("b", "e", "not pursued")]},
    }
    out = {}
    for k, sp in specs.items():
        out[k] = figures.render(sp, fig_dir / f"ld001_{k}.png")
    return out

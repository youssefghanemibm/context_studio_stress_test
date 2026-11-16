"""LD018 – Claims Operating Model and RACI (post re-org), DOCX, 2025-10-06, Rob Tennant."""
from __future__ import annotations

import re

from . import common as C
from . import figures as FG
from .core import CACHE, Ctx, Doc, F, PF, Style, W, gbp, long_date, util
from .prose import Prose

FID = "LD018"
REORG = "2025-09-01"
BEFORE = "2025-08-31"
CHANGED = ["P008", "P009", "P012", "P013", "P014", "P016", "P017"]
POST_CIRCULAR_STEPS = ("PS-FRD-03", "PS-FRD-05")
RACI_FONT = 8.0


def sla_asof(ctx: Ctx, step: dict) -> str:
    txt = step["sla"]["text"]
    m = re.search(r"\((BR-[A-Z]+-\d{3}) v(\d)\)", txt)
    if not m:
        return txt
    rid, ver = m.group(1), int(m.group(2))
    v = ctx.rule(rid)
    if v and v["version"] == ver:
        return txt
    p = v["parameters"] if v else {}
    if rid == "BR-FNOL-001":
        return f"within {p['ack_business_days']} business days of notification (BR-FNOL-001 v{v['version']})"
    if rid == "BR-ASM-005":
        return f"{p['business_days']} business days; Tier-3 within {p['tier3_hours']} hours (BR-ASM-005 v{v['version']})"
    if rid == "BR-RSV-007":
        return f"Tier-3 every {p['review_days']} days (BR-RSV-007 v{v['version']})"
    if rid == "BR-FRD-035":
        return f"SIU triage within {p['business_days']} business days (BR-FRD-035 v{v['version']})"
    return txt.split("(")[0].strip()


def step_rules(ctx: Ctx, st: dict) -> str:
    out = []
    for rid in st.get("rules", []):
        if rid == "BR-FRD-031" and not ctx.rule(rid):
            rid = "BR-FRD-012"
        v = ctx.rule(rid)
        if not v:
            continue
        lab = f"{rid} v{v['version']} – {W.rules[rid]['title']}"
        if lab not in out:
            out.append(lab)
    return "; ".join(out) or "—"


def step_systems(ctx: Ctx, st: dict) -> str:
    out = []
    for sid in st.get("systems", []):
        gl = W.systems[sid].get("go_live")
        if gl and str(gl) > ctx.date:
            continue
        out.append(ctx.sys(sid))
    return ", ".join(out) or "—"


def build() -> Doc:
    ctx = Ctx(FID)
    date = ctx.date
    pr = Prose(util.rng(f"{FID}:prose"), date=ctx.date)
    doc = Doc(ctx, title="Claims Operating Model and RACI", doc_id="CLM-OPM-004", version="2.0", status="Approved",
              subtitle="Operating model following the re-organisation of 1 September 2025",
              style=Style(font="Calibri", heading_font="Calibri", accent="375623", accent2="E2EFDA", size=11),
              header_left="Claims Operating Model and RACI (post re-org)", header_right="CLM-OPM-004 v2.0")
    doc.title_page(C.control_rows(ctx, doc, owner="P005", extra=[["Effective", long_date(REORG)],
                                                                  ["Supersedes", "CLM-OPM-004 v1.4"]]))
    C.version_history(ctx, doc, [("1.0", 610, "Operating model for Claims Operations UK and Nordics"),
                                 ("1.4", 240, "RACI refreshed for Programme Skerry squads"),
                                 ("1.9", 21, "Draft reflecting the re-organisation announced for 1 September 2025"),
                                 ("2.0", 0, "Approved")])
    C.approvals(ctx, doc, [("P005", "Claims Director"), ("P004", "Chief Operating Officer"), ("P007", "Chief Risk Officer")])
    C.reviewers(ctx, doc, ["P008", "P009", "P012", "P013", "P014", "P033", "P037", "P017"])
    C.distribution(ctx, doc, ["Executive Committee", "Claims leadership team", "Counter-Fraud & SIU",
                              "Reserving", "Recoveries & Subrogation (Group)", "Claims Hub Product", "Internal Audit"])
    doc.toc(depth=2)

    # 1 -----------------------------------------------------------------------------------
    doc.h(1, "1 Purpose and scope")
    doc.p("This document describes how Corvane's claims function is organised following the re-organisation that took "
          f"effect on {long_date(REORG)}: who owns each stage of the claims process, which teams carry out the work, and "
          "how decisions, escalations and hand-offs are made. It replaces version 1.4 of the operating model.")
    doc.ps(pr.paras(["opmodel", "opm2"], 3))
    doc.h(2, "1.1 In scope")
    doc.bullets(["All claims handled by Corvane Mutual in the UK, Norway, Sweden and Denmark, for every line of business.",
                 "The seven stages of the claims process, from first notice of loss to recovery and subrogation.",
                 "Specialist functions that contribute to claims: Counter-Fraud & SIU, Reserving, Reinsurance, Payments "
                 "Operations, Regulatory Reporting and Compliance.",
                 "The technology teams that support the claims platforms, to the extent that they hold claims "
                 "responsibilities."])
    doc.h(2, "1.2 Out of scope")
    doc.bullets(["Underwriting, pricing and policy administration.",
                 "Detailed desk procedures, which are held in the claims standards library.",
                 "Authority limits, which are set out in the claims authority framework and are not repeated here."])
    doc.h(2, "1.3 How to read this document")
    doc.p("Section 2 describes the organisation and the changes made on 1 September 2025. Section 3 lists the governance "
          "forums. Section 4 sets out the owner of each stage and step. Section 5 contains the full RACI. Sections 6 to 10 "
          "cover service levels, indicators, ways of working and the transition to Claims Hub, and section 11 contains "
          "the role descriptions.")
    doc.ps(pr.paras(["opm2", "governance"], 2))

    # 2 Organisation ----------------------------------------------------------------------
    doc.h(1, "2 Organisation", page_break=True)
    doc.p(f"The main changes of the re-organisation are: the Special Investigations Unit, renamed Counter-Fraud & SIU, "
          f"moved from the Claims department to Risk & Compliance; Recoveries & Subrogation became a Group function led "
          f"by {ctx.name('P013')}; and Claims Operations became a Group function covering all regions.")
    cro = ctx.holder("the CRO")
    doc.p(f"From {long_date(REORG)} Counter-Fraud & SIU reports to the Chief Risk Officer, {ctx.name(cro)}, through "
          f"{ctx.person('P008')}.",
          facts=[PF(ctx, "ld18_siu_cro", f"Counter-Fraud & SIU reports to the Chief Risk Officer, {ctx.name(cro)}")])
    fig = FG.box_diagram(CACHE / "fig" / FID / "org.png", title="Claims-related reporting lines from 1 September 2025",
                         boxes=[{"id": "ceo", "label": f"{ctx.name('P003')}\nChief Executive Officer", "x": 760, "y": 110, "w": 480, "h": 130, "color": "grey"},
                                {"id": "coo", "label": f"{ctx.name('P004')}\nChief Operating Officer", "x": 80, "y": 360, "w": 460, "h": 130},
                                {"id": "cro", "label": f"{ctx.name('P007')}\nChief Risk Officer", "x": 760, "y": 360, "w": 480, "h": 130, "color": "purple"},
                                {"id": "cfo", "label": f"{ctx.name('P001')}\nChief Financial Officer", "x": 1460, "y": 360, "w": 460, "h": 130, "color": "green"},
                                {"id": "cd", "label": f"{ctx.name('P005')}\nClaims Director", "x": 80, "y": 620, "w": 460, "h": 130},
                                {"id": "siu", "label": f"{ctx.name('P008')}\nHead of Counter-Fraud & SIU", "x": 760, "y": 620, "w": 480, "h": 130, "color": "purple"},
                                {"id": "rsv", "label": f"{ctx.name('P009')}\nHead of Reserving", "x": 1460, "y": 620, "w": 460, "h": 130, "color": "green"},
                                {"id": "ops", "label": f"{ctx.name('P011')}\nHead of Claims Operations (Group)", "x": 40, "y": 900, "w": 440, "h": 140},
                                {"id": "rec", "label": f"{ctx.name('P013')}\nHead of Recoveries & Subrogation", "x": 520, "y": 900, "w": 440, "h": 140},
                                {"id": "hub", "label": f"{ctx.name('P017')}\nHead of Claims Hub Product", "x": 1000, "y": 900, "w": 440, "h": 140}],
                         arrows=[{"src": "coo", "dst": "ceo", "label": "reports to"}, {"src": "cro", "dst": "ceo", "label": "reports to"},
                                 {"src": "cfo", "dst": "ceo", "label": "reports to"}, {"src": "cd", "dst": "coo", "label": "reports to"},
                                 {"src": "siu", "dst": "cro", "label": "reports to (from 1 Sep 2025)"},
                                 {"src": "rsv", "dst": "cfo", "label": "reports to"},
                                 {"src": "ops", "dst": "cd", "label": "reports to"}, {"src": "rec", "dst": "cd", "label": "reports to", "lx": 60},
                                 {"src": "hub", "dst": "cd", "label": "reports to", "lx": 80}],
                         size=(2000, 1120))
    doc.figure(fig, "Claims-related reporting lines from 1 September 2025",
               alt="Org chart: Counter-Fraud & SIU (Niall Brannigan) reports to the Chief Risk Officer, Karin Holmberg, from 1 September 2025.",
               facts=[F("image_text", "The org chart shows the Head of Counter-Fraud & SIU reporting to the CRO from 1 Sep 2025.",
                        "reports to (from 1 Sep 2025)", "TEAM:T11#department_history", where="image"),
                      F("alt_text", "Org chart alt text: Counter-Fraud & SIU reports to the CRO, Karin Holmberg.",
                        "Counter-Fraud & SIU (Niall Brannigan) reports to the Chief Risk Officer, Karin Holmberg", "TEAM:T11#department_history",
                        where="alt")])
    doc.ps(pr.paras(["opm2"], 1))
    doc.h(2, "2.1 Changes to roles")
    rows, facts = [], []
    for pid in CHANGED:
        mo, mn = W.manager_of(pid, BEFORE), W.manager_of(pid, date)
        rows.append([W.name_of(pid, date), W.title_of(pid, BEFORE), W.name_of(mo, BEFORE) if mo else "—",
                     W.title_of(pid, date), W.name_of(mn, date) if mn else "—"])
        if pid == "P013":
            facts.append(F("temporal", "Freya Lindahl became Head of Recoveries & Subrogation on 2025-09-01.",
                           "Head of Recoveries & Subrogation", "PERSON:P013#titles", where=(len(rows), 3)))
        if pid == "P009":
            facts.append(F("temporal", "Lena Kristiansen moved from Reserving Manager to Head of Reserving, reporting to the CFO Priya Raman.",
                           "Head of Reserving", "PERSON:P009#titles", where=(len(rows), 3)))
        if pid == "P016":
            facts.append(F("temporal", "Graham Pocock became Head of Legacy Claims Platforms reporting to Neil Haworth.",
                           "Neil Haworth", "PERSON:P016#reports_to", where=(len(rows), 4)))
        if pid == "P012":
            facts.append(F("temporal", "Mette Dahl moved from Head of Claims Operations Nordics to Claims Operations Lead – Nordics on 2025-09-01.",
                           "Claims Operations Lead – Nordics", "PERSON:P012#titles", where=(len(rows), 3)))
    doc.table(["Name", "Title until 31 Aug 2025", "Manager until 31 Aug 2025", "Title from 1 Sep 2025", "Manager from 1 Sep 2025"],
              rows, widths=[3.0, 3.8, 2.8, 4.0, 3.0], caption="Role changes on 1 September 2025", font_size=8.4, facts=facts)
    doc.ps(pr.paras(["opmodel", "opm2"], 2))
    doc.h(2, "2.2 Departments and teams")
    rows = []
    for did, dep in W.departments.items():
        if did == "DEP-IBM":
            continue
        head = W._period_value(dep["head_history"], "person", date)
        rows.append([dep["name"], ctx.name(head) if head else "—"])
    doc.table(["Department", "Head"], rows, widths=[8.0, 8.6], caption="Departments")
    rows = []
    for tid, t in W.teams.items():
        if t["formed"] > date or tid in ("T26",):
            continue
        dep = ctx.dept_of_team(tid)
        lead = ctx.team_lead(tid)
        rows.append([tid, ctx.team(tid), W.departments[dep]["name"] if dep else "—", ctx.name(lead) if lead else "—"])
    doc.table(["Team", "Name", "Department", "Lead"], rows, widths=[1.4, 5.6, 5.0, 4.6], caption="Teams at the date of this document",
              font_size=8.6,
              facts=[F("general", "Team T11 is named Counter-Fraud & SIU from 2025-09-01 and sits in Risk & Compliance.",
                       "Risk & Compliance", "TEAM:T11#department_history", where=(next(i for i, r in enumerate(rows, 1) if r[0] == "T11"), 2))])
    doc.ps(pr.paras(["opmodel", "opm2"], 2))
    doc.h(2, "2.3 Locations")
    doc.p("Claims work is carried out from the locations below. Teams are allocated to a home location, but most "
          "processes can be performed from any office and from home in line with the hybrid working policy.")
    rows = []
    for lid, loc in W.locations.items():
        if lid.startswith("EXT") or loc.get("type") not in ("office", "headquarters", "branch"):
            continue
        rows.append([loc["name"], loc["city"], loc["country"], ", ".join(loc.get("functions", [])) or "—"])
    doc.table(["Location", "City", "Country", "Claims-related functions"], rows, widths=[4.2, 2.4, 1.6, 8.4],
              caption="Claims locations", font_size=8.6)
    doc.ps(pr.paras(["opm2"], 2))

    # 3 Forums ---------------------------------------------------------------------------
    doc.h(1, "3 Governance forums", page_break=True)
    doc.p("The forums below oversee the claims process and the changes being made to it. Their terms of reference "
          "are held by the secretariat of each forum.")
    rows = []
    for cid, c in W.committees.items():
        chair = W._period_value(c["chair_history"], "person", date)
        cad = c["cadence"] if ctx.ok(f"COMMITTEE:{cid}", "cadence") else "As scheduled by the chair"
        rows.append([c["name"], ctx.name(chair) if chair else "—", cad, c["remit"]])
    doc.table(["Forum", "Chair", "Meets", "Remit"], rows, widths=[3.6, 3.0, 3.6, 6.4], caption="Forums", font_size=8.4,
              facts=[F("temporal", "From 2025-09-01 the Reserving Committee is chaired by Lena Kristiansen.", ctx.name("P009"),
                       "COMMITTEE:COM-01#chair_history", where=(1, 1))])
    for k, (cid, c) in enumerate(W.committees.items(), 1):
        chair = W._period_value(c["chair_history"], "person", date)
        doc.h(2, f"3.{k} {c['name']}")
        doc.p(f"Chair: {ctx.person(chair)}. Remit: {c['remit'][0].lower() + c['remit'][1:]}"
              + ("" if c["remit"].endswith(".") else "."))
        doc.ps(pr.paras(["governance", "opm2"], 1, n=(3, 4)))
    doc.h(2, f"3.{len(W.committees) + 1} Escalation between forums")
    doc.ps(pr.paras(["opmodel", "governance"], 2))

    # 4 Process ownership ------------------------------------------------------------------
    doc.h(1, "4 Process ownership", page_break=True)
    doc.p("Each stage of the claims process has one accountable owner. The table shows the owner at the date of this "
          "document and, where the owner changed on 1 September 2025, the previous owner.")
    rows = []
    for sid, s in W.stages.items():
        own = W.owner_of_process(sid, date)
        old = W.owner_of_process(sid, BEFORE)
        rows.append([sid, s["name"], ctx.person(own), W.name_of(old, BEFORE) if old != own else "unchanged"])
    doc.table(["Stage", "Name", "Owner (accountable)", "Owner before 1 Sep 2025"], rows, widths=[1.4, 4.0, 7.0, 4.2],
              caption="Stage owners",
              facts=[F("needle", "Freya Lindahl owns the recovery & subrogation stage (S7) from 2025-09-01.",
                       "Freya Lindahl, Head of Recoveries & Subrogation", "PROCESS:S7#owner_history", where=(7, 2)),
                     F("temporal", "Before 2025-09-01 the S7 owner was Siobhan Quill (acting).", "Siobhan Quill",
                       "PROCESS:S7#owner_history", where=(7, 3)),
                     F("temporal", "From 2025-09-01 the First Notice of Loss stage (S1) is owned by Rob Tennant; before that Ewan Strachan.",
                       "Ewan Strachan", "PROCESS:S1#owner_history", where=(1, 3))])
    doc.ps(pr.paras(["opm2"], 1))
    for sid, s in W.stages.items():
        own = W.owner_of_process(sid, date)
        doc.h(2, f"4.{s['order']} {s['name']}")
        doc.p(f"Owner: {ctx.person(own)}. Steps: " +
              "; ".join(f"{x} {W.steps[x]['name']}" for x in s["steps"] if x not in POST_CIRCULAR_STEPS) + ".")
        doc.ps(pr.paras(["opmodel", "opm2"], 1, n=(3, 4)))
        for x in s["steps"]:
            if x in POST_CIRCULAR_STEPS:
                continue
            st = W.steps[x]
            r = st["raci"]
            doc.h(3, f"{x} {st['name']}")
            doc.kv([["Purpose", st["description"]],
                    ["Responsible", ", ".join(ctx.team(t) for t in r["R"]) or "—"],
                    ["Accountable", ctx.person(r["A"])],
                    ["Systems", step_systems(ctx, st)],
                    ["Rules applied", step_rules(ctx, st)],
                    ["Service level", sla_asof(ctx, st)]], widths=(3.4, 13.2), font_size=8.6)
            doc.p(pr.para(["step", "step", "opm2"], n=(3, 5), step=st["name"].lower(),
                          team=ctx.team(r["R"][0]) if r["R"] else "the responsible team"))

    # 5 RACI ------------------------------------------------------------------------------
    doc.h(1, "5 RACI", page_break=True)
    doc.p("R – responsible; A – accountable; C – consulted; I – informed. Accountability is held by a named role; "
          "names are given as at the date of this document. Part B covers stage ownership, part C the process steps and "
          "their decision branches, part A governance and oversight activities, and part D the Claims Hub services.")
    rows, facts = _raci_rows(ctx)
    doc.table(["Ref", "Activity", "Responsible", "Accountable", "Consulted", "Informed"], rows,
              widths=[1.9, 4.6, 2.9, 3.4, 2.1, 1.9], caption="Claims RACI", font_size=RACI_FONT, facts=facts)
    doc.p("Where a team is shown as responsible for a platform activity, the accountable role remains answerable for "
          "the service provided to claims even when the work is carried out by a supplier.")

    # 6 Service levels ---------------------------------------------------------------------
    doc.h(1, "6 Service levels by step", page_break=True)
    rows = []
    for sid, st in W.steps.items():
        if sid in POST_CIRCULAR_STEPS:
            continue
        rows.append([sid, st["name"], sla_asof(ctx, st)])
    doc.table(["Step", "Name", "Service level"], rows, widths=[2.4, 5.4, 8.8], caption="Service levels", font_size=8.4,
              facts=[F("temporal", "In October 2025 Tier-3 reserves are reviewed every 21 days (BR-RSV-007 v2).",
                       "Tier-3 every 21 days (BR-RSV-007 v2)", "RULE:BR-RSV-007@v2#parameters.review_days",
                       where=(next(i for i, r in enumerate(rows, 1) if r[0] == "PS-RSV-03"), 2))])
    doc.ps(pr.paras(["opmodel", "governance", "kpi"], 2))

    # 7 Decision rights --------------------------------------------------------------------
    doc.h(1, "7 Decision rights and escalation")
    doc.p("Decisions on individual claims are taken by the person handling the claim within their authority. "
          "Authority limits for reserves and payments are set out in the claims authority framework approved by the "
          "Claims Director; this operating model does not change them.")
    doc.ps(pr.paras(["opm2", "opmodel"], 2))
    rows = [["Reserve change above the holder's authority", "Next level in the claims authority framework", ctx.person(W.owner_of_process("S4", date))],
            ["Referral to SIU disputed by the Claims Handler", "SIU Investigations Manager (UK)", ctx.person("P008")],
            ["Coverage decision disputed by the customer", "Team leader, then complaints", ctx.person(W.owner_of_process("S3", date))],
            ["Recovery write-off", "Recoveries Team Leader – UK", ctx.person(W.owner_of_process("S7", date))],
            ["Large loss requiring reinsurer notification", "Reinsurance Manager", ctx.person("P038")],
            ["Service level at risk across teams", "Stage owner", ctx.person("P011")]]
    doc.table(["Situation", "First escalation", "Final escalation"], rows, widths=[6.0, 5.0, 5.6],
              caption="Escalation routes", font_size=8.6)
    doc.ps(pr.paras(["opm2"], 2))

    # 8 Indicators -------------------------------------------------------------------------
    doc.h(1, "8 Performance indicators and management information", page_break=True)
    doc.ps(pr.paras(["kpi", "opm2"], 2))
    rows = []
    for sid, s in W.stages.items():
        own = W.owner_of_process(sid, date)
        for ind in _INDICATORS[sid]:
            rows.append([s["name"], ind, ctx.name(own), "Monthly"])
    doc.table(["Stage", "Indicator", "Owner", "Reported"], rows, widths=[3.4, 7.6, 3.4, 2.2],
              caption="Operational indicators", font_size=8.4)
    doc.ps(pr.paras(["kpi"], 2))

    # 9 Ways of working --------------------------------------------------------------------
    doc.h(1, "9 Ways of working")
    for i, t in enumerate(["Hand-offs between teams", "Escalation", "Management information", "Operating rhythm",
                           "Working with vendors", "Quality assurance", "Absence and surge cover",
                           "Customer vulnerability", "Complaints"], 1):
        doc.h(2, f"9.{i} {t}")
        doc.ps(pr.paras(["opmodel", "opm2", "governance"], 2, n=(3, 5)))

    # 10 Transition ----------------------------------------------------------------------
    doc.h(1, "10 Transition to Claims Hub", page_break=True)
    doc.p(f"Claims Hub product ownership moved into the Claims department on {long_date(REORG)}; {ctx.person('P017')} "
          f"now reports to the Claims Director. The Hub squads remain in Technology.")
    rows = [[ctx.team(t), ctx.name(ctx.team_lead(t)), ctx.a(W.teams[t]["purpose"])] for t in ("T27", "T28", "T29")]
    doc.table(["Squad", "Lead", "Services"], rows, widths=[5.0, 3.6, 8.0], caption="Hub squads")
    doc.p("The first release of Claims Hub, covering notification of loss and triage for digital channels, is planned "
          "for November 2025. Until each migration wave is complete, the process steps are performed on CLARA and the "
          "accountable roles in this document apply unchanged.")
    doc.ps(pr.paras(["opmodel", "migration", "opm2"], 3))

    # 11 Roles -------------------------------------------------------------------------------
    doc.h(1, "11 Role descriptions", page_break=True)
    roles = ["P005", "P011", "P012", "P013", "P014", "P008", "P028", "P027", "P009", "P033", "P034", "P030", "P029",
             "P035", "P038", "P017", "P016", "P037"]
    for k, pid in enumerate(roles, 1):
        doc.h(2, f"11.{k} {ctx.title(pid)}")
        mgr = ctx.manager(pid)
        owns = [s["name"] for sid, s in W.stages.items() if W.owner_of_process(sid, date) == pid]
        acc = [W.steps[x]["name"] for x in W.steps if W.steps[x]["raci"]["A"] == pid and x not in POST_CIRCULAR_STEPS]
        doc.kv([["Current holder", ctx.name(pid)], ["Reports to", ctx.person(mgr) if mgr else "—"],
                ["Team", ctx.team(W.team_of(pid, date))], ["Location", W.locations[W.location_of(pid, date)]["name"]],
                ["Stage ownership", ", ".join(owns) or "—"],
                ["Accountable for steps", ", ".join(acc) or "—"]],
               widths=(3.4, 13.2), font_size=8.6)
        doc.p(pr.para(["role", "opm2"], n=(4, 6), role=ctx.title(pid)))

    # Appendices --------------------------------------------------------------------------
    doc.h(1, "Appendix A – People directory", page_break=True)
    rows = []
    for pid, p in W.people.items():
        if not ctx.employed(pid) or p["location"].startswith("EXT"):
            continue
        mgr = ctx.manager(pid)
        rows.append([ctx.name(pid), ctx.title(pid), ctx.team(W.team_of(pid, date)) if W.team_of(pid, date) else "—",
                     ctx.name(mgr) if mgr else "—"])
    doc.table(["Name", "Title", "Team", "Reports to"], rows, widths=[3.6, 5.6, 4.2, 3.2], caption="Directory", font_size=8.0)
    doc.h(1, "Appendix B – Systems supporting claims")
    sids = [s for s in W.systems if not (W.systems[s].get("go_live") and str(W.systems[s]["go_live"]) > date)
            and W.systems[s].get("lifecycle") != "retired"]
    C.systems_table(ctx, doc, sids, "Systems and business owners")
    doc.h(1, "Appendix C – Process steps, programs and systems", page_break=True)
    doc.p("The table maps each process step to the CLARA programs and the systems that support it at the date of this "
          "document. It is provided for orientation; the CLARA system specification is the authoritative source for "
          "program behaviour.")
    rows = []
    for x, st in W.steps.items():
        if x in POST_CIRCULAR_STEPS:
            continue
        progs = [p for p in st.get("programs", []) if p in W.programs and str(W.programs[p]["since"]) <= date]
        rows.append([x, st["name"], ", ".join(progs) or "—", step_systems(ctx, st)])
    doc.table(["Step", "Name", "CLARA programs", "Systems"], rows, widths=[2.2, 4.6, 4.4, 5.4],
              caption="Step to program and system map", font_size=8.2)
    doc.ps(pr.paras(["opm2"], 1))
    doc.h(1, "Appendix D – RACI by team", page_break=True)
    doc.p("This appendix restates part C of the RACI from the point of view of each team, so that team leaders can see "
          "their responsibilities in one place.")
    for tid, t in W.teams.items():
        if t["formed"] > date or tid in ("T01", "T26"):
            continue
        r_, c_, i_ = [], [], []
        for x, st in W.steps.items():
            if x in POST_CIRCULAR_STEPS:
                continue
            ra = st["raci"]
            if tid in ra["R"]:
                r_.append(f"{x} {st['name']}")
            if tid in ra["C"]:
                c_.append(f"{x} {st['name']}")
            if tid in ra["I"]:
                i_.append(f"{x} {st['name']}")
        if not (r_ or c_ or i_):
            continue
        lead = ctx.team_lead(tid)
        doc.h(2, f"{ctx.team(tid)} ({tid})")
        doc.kv([["Team lead", ctx.person(lead) if lead else "—"],
                ["Responsible", "; ".join(r_) or "—"], ["Consulted", "; ".join(c_) or "—"],
                ["Informed", "; ".join(i_) or "—"]], widths=(3.0, 13.6), font_size=8.4)
        doc.p(pr.para(["step", "opm2"], n=(2, 3), step="the steps listed above", team=ctx.team(tid)))
    doc.h(1, "Appendix E – Glossary")
    doc.table(["Term", "Meaning in this document"],
              [[t, ctx.a(m)] for t, m in C.glossary_terms(["G-001", "G-003", "G-004", "G-005", "G-007", "G-008", "G-012",
                                                           "G-018", "G-020", "G-023"])],
              widths=[4.6, 12.0], font_size=8.8)
    return doc


_INDICATORS = {
    "S1": ["Notifications received by channel", "Acknowledgements issued within the service level",
           "Duplicate notifications identified"],
    "S2": ["Claims tiered within the service level", "Claims routed to fast-track", "Major loss alerts raised"],
    "S3": ["Assessor appointments within the service level", "Assessment cycle time", "Coverage decisions overturned on review"],
    "S4": ["Reserves set within the service level", "Overdue reserve reviews", "Reserve changes escalated above authority"],
    "S5": ["Claims referred to SIU", "Referrals triaged within the service level", "Investigations closed by outcome"],
    "S6": ["Settlement offers within the service level", "Payments rejected by screening", "Claims closed with a zero reserve"],
    "S7": ["Recovery cases opened", "Demands issued within the service level", "Write-offs approved by level"],
}


def _raci_rows(ctx: Ctx):
    date = ctx.date
    T = lambda ts: ", ".join(ctx.team(t) for t in ts) or "—"  # noqa: E731

    def A(pid):
        return f"{ctx.title(pid)} ({ctx.name(pid)})"
    rows, facts = [], []
    cfo = ctx.holder("the CFO")

    # Part A – governance and oversight (emitted after part C)
    part_a = [["A", "Part A – Governance and oversight", "", "", "", ""]]
    cross = [
        ("GOV-01", "Approve reserving policy and reserves above the Claims Director limit", T(["T12"]),
         f"Reserving Committee (chair {ctx.name('P009')})", T(["T13", "T14"]), T(["T02"])),
        ("GOV-02", "Approve reserve and payment authority limits", T(["T12"]), A("P005"), T(["T14"]), T(["T02"])),
        ("GOV-03", "Set fraud rules and Sentinel thresholds", T(["T11"]), f"Claims Fraud Forum (chair {ctx.name('P008')})",
         T(["T18", "T02"]), T(["T29"])),
        ("GOV-04", "Own and monitor the Sentinel model", f"{ctx.name('P027')} (model owner)", A("P008"), T(["T18"]), T(["T02"])),
        ("GOV-05", "Prepare and sign the NISA-TP2 return", T(["T15"]), A(cfo), T(["T12", "T14"]), "—"),
        ("GOV-06", "Prepare and sign the NISA-CT1 return", T(["T15"]), A("P005"), T(["T02"]), "—"),
        ("GOV-07", "Respond to data subject access requests (BR-GEN-002)", T(["T19"]), A("P019"), T(["T02"]), "—"),
        ("GOV-08", "Manage the panel of external Claims Assessors", T(["T06"]), A("P033"), T(["T02"]), T(["T08"])),
        ("GOV-09", "Administer reinsurance notifications and bordereaux", T(["T17"]), A("P038"), T(["T12"]), T(["T14"])),
        ("GOV-10", "Execute claim payments through the Corvane Payments Gateway", T(["T16"]), A("P035"), T(["T18"]), T(["T14"])),
        ("GOV-11", "Support CLARA and its batch schedule", T(["T20", "T25"]), A("P016"), T(["T22"]), T(["T02"])),
        ("GOV-12", "Own the Claims Hub product backlog", T(["T21"]), A("P017"), T(["T27", "T28", "T29"]), T(["T02"])),
        ("GOV-13", "Maintain the claims operating model and RACI", T(["T02"]), A("P011"), T(["T11", "T08"]), T(["T01"])),
        ("GOV-14", "Monthly operational performance pack", T(["T02"]), A("P011"), T(["T23"]), T(["T01"])),
        ("GOV-15", "Claims conduct and counter-fraud compliance monitoring", T(["T18"]), A("P037"), T(["T11", "T02"]), T(["T01"])),
    ]
    part_a.extend(list(r) for r in cross)

    # Part B – stage ownership
    rows.append(["B", "Part B – Stage ownership", "", "", "", ""])
    for sid, s in W.stages.items():
        own = W.owner_of_process(sid, date)
        teams = []
        for x in s["steps"]:
            if x in POST_CIRCULAR_STEPS:
                continue
            for t in W.steps[x]["raci"]["R"]:
                if t not in teams:
                    teams.append(t)
        rows.append([f"STG-{sid}", f"End-to-end performance of the {s['name']} stage", T(teams[:3]), A(own),
                     T(["T23"]), T(["T01"])])

    # Part C – process steps and decision branches
    rows.append(["C", "Part C – Process steps", "", "", "", ""])
    thr = ctx.rule("BR-FRD-012")["parameters"]["threshold"]
    branch_text = {
        "PS-TRI-03": [f"Route to the referral decision when the Sentinel score is {thr} or more (BR-FRD-012 v2)",
                      "Route eligible Tier-1 claims to fast-track (BR-TRI-006)", "Route Tier-3 claims to Major & Complex Loss (BR-TRI-004)",
                      "Route other claims to specialist Claims Handlers (BR-TRI-004)"],
        "PS-ASM-04": ["Flag recovery potential when a third party is wholly or partly at fault (BR-REC-001)",
                      "Update the case reserve with the estimate (BR-RSV-001)"],
        "PS-RSV-02": ["Escalate reserve changes above the holder's authority (BR-RSV-003 v3)",
                      f"Notify Reinsurance of reserve movements above {gbp(250000)} (BR-RSV-011 v2)",
                      "Approve reserve changes within authority (BR-RSV-003 v3)"],
        "PS-FRD-01": [f"Refer to SIU when the Sentinel score is {thr} or more (BR-FRD-012 v2)", "Do not refer; continue handling"],
        "PS-REC-02": [f"Pursue recoveries of {gbp(1000)} or more (BR-REC-003 v3)",
                      f"Instruct solicitors for recoveries of {gbp(25000)} or more or where liability is defended (BR-REC-005)",
                      f"Close or write off recoveries below {gbp(1000)} (BR-REC-003 v3)"],
        "PS-REC-06": [f"Approve recovery write-off above {gbp(10000)}", f"Approve recovery write-off up to {gbp(10000)}"],
    }
    for sid, st in W.steps.items():
        if sid in POST_CIRCULAR_STEPS:
            continue
        r = st["raci"]
        rows.append([sid, st["name"], T(r["R"]), A(r["A"]), T(r["C"]), T(r["I"])])
        for k, txt in enumerate(branch_text.get(sid, []), 1):
            acc = A(r["A"])
            if sid == "PS-REC-06" and k == 2:
                acc = A("P014")
            if sid == "PS-RSV-02" and k == 2:
                acc = A("P038")
            rows.append([f"{sid}.{k}", txt, T(r["R"]), acc, T(r["C"]), T(r["I"])])
            if sid == "PS-REC-06" and k == 1:
                facts.append(PF(ctx, "ld18_raci_wo", A(r["A"]), where=(len(rows), 3),
                                anchor=f"Approve recovery write-off above {gbp(10000)}",
                                notes="Row 'Approve recovery write-off above £10,000' (PS-REC-06.1); the RACI table "
                                      "spans four pages and this row is on its third page."))
                facts.append(F("multipage_table", "RACI activity text for the write-off branch row.",
                               f"Approve recovery write-off above {gbp(10000)}", "RULE:BR-REC-011@v2", where=(len(rows), 1)))
            if sid == "PS-REC-06" and k == 2:
                facts.append(F("multipage_table", "Write-offs up to £10,000 are approved by the Recoveries Team Leader – UK (Siobhan Quill).",
                               A("P014"), "PROCESS:PS-REC-06#decision", where=(len(rows), 3)))

    rows.extend(part_a)
    # Part D – Claims Hub services
    rows.append(["D", "Part D – Claims Hub services", "", "", "", ""])
    for name, s in W.services.items():
        o = W.service_owner(name, date)
        if not o:
            continue
        rows.append([s["id"], f"Build and run {ctx.svc(name)}", T([o["team"]]), A(o["person"]) if ctx.title(o["person"]) else ctx.name(o["person"]),
                     T(["T21"]), T(["T02"])])
    return rows, facts


def post_check(doc, texts):
    from harness import extract as X
    first = [i + 1 for i, t in enumerate(texts) if X.match("Part B – Stage ownership", t)]
    row = [i + 1 for i, t in enumerate(texts) if X.match("Approve recovery write-off above £10,000", t)]
    last = [i + 1 for i, t in enumerate(texts) if X.match("Build and run", t)]
    probs = [f"INFO RACI table p{first} .. p{last}; write-off row p{row}; total {len(texts)}"]
    if first and last and row:
        span = last[-1] - first[0] + 1
        pos = row[0] - first[0] + 1
        if span != 4 or pos != 3:
            probs.append(f"RACI spans {span} pages (want 4); write-off row on table page {pos} (want 3)")
    return probs

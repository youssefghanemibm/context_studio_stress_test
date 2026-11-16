"""LD028 – Programme Skerry Business Case (DOCX -> PDF via LibreOffice, 2024-11-18, signed by CFO Gareth Whitcombe).

As of November 2024: before the IBM engagement (2025-01-13) and before any ADR; FRAUDNET, DOCSTOR, Adjuster Extranet,
MyCorvane Claims (renamed 2024-10-14). The only programme figure stated is the approved budget.
"""
from __future__ import annotations

import collections

from . import common as C
from . import figures as FG
from . import hub as H
from .core import CACHE, Ctx, Doc, F, PF, Style, W, long_date, short_date, util
from .prose import Prose

FID = "LD028"

CAPABILITIES = [
    ("First notice of loss", "Digital, contact-centre, broker and telematics notification with immediate claim creation"),
    ("Triage", "Automated tiering, fraud pre-screen and routing"),
    ("Assessment", "Assessor appointment, inspections, estimates and coverage decisions"),
    ("Reserving", "Case reserves, movements, review scheduling, indexation and revaluation"),
    ("Fraud referral", "Referral decisions and hand-off to SIU"),
    ("Settlement and payments", "Offers, payment authorisation, sanctions screening and payment instructions"),
    ("Recovery", "Subrogation, salvage and recovery receipts, replacing the subrogation tracker"),
    ("Documents and communications", "Document metadata and customer communications"),
    ("Finance and reporting", "General ledger journals and regulatory extracts"),
]

OPTIONS = [
    ("Option 0 – Continue on CLARA", "Maintain CLARA and the satellite systems; make regulatory changes as required.",
     "Low", "High", "None", "Not recommended"),
    ("Option 1 – Re-host CLARA", "Move the COBOL application to a different runtime without changing its design.",
     "Medium", "High", "Limited", "Not recommended"),
    ("Option 2 – Packaged claims system", "Replace CLARA with a configured third-party claims package.",
     "High", "Medium", "Medium", "Shortlisted"),
    ("Option 3 – Claims Hub (recommended)", "Build a modular claims platform on the Society's container platform and "
     "migrate CLARA's capabilities progressively.", "High", "Low", "High", "Recommended"),
]


def build() -> Doc:
    ctx = Ctx(FID)
    date = ctx.date
    pr = Prose(util.rng(f"{FID}:prose"), date=ctx.date)
    prog = W.company["programme"]
    ctx.need("ORG:company", "programme")
    budget = prog["budget_gbp_m"]
    cfo = ctx.holder("the CFO")
    doc = Doc(ctx, title="Programme Skerry Business Case", doc_id="SKR-BC-001", version="1.0", status="Approved",
              subtitle="Replacing the CLARA claims platform – full business case for approval",
              style=Style(font="Times New Roman", heading_font="Arial", accent="1A5276", accent2="D4E6F1", size=12, line_spacing=1.35),
              header_left="Programme Skerry – Business Case", header_right="SKR-BC-001 v1.0 – Approved",
              footer_left="Strictly confidential – Executive Committee", classification="Strictly confidential")
    doc.title_page(C.control_rows(ctx, doc, owner="P004", extra=[["Executive sponsor", ctx.person(prog["executive_sponsor"])],
                                                                  ["Budget requested", f"£{budget}m"],
                                                                  ["Decision", "Approved"]]))
    C.version_history(ctx, doc, [("0.1", 160, "Strategic outline case"), ("0.5", 95, "Outline business case: options appraisal"),
                                 ("0.9", 28, "Full business case for Executive Committee review"), ("1.0", 0, "Approved and signed")],
                      authors=["P004", "P004", "P002", "P002"])
    doc.toc(depth=2)

    # 1 Executive summary -------------------------------------------------------------------
    doc.h(1, "1 Executive summary")
    doc.p(f"This business case seeks approval for {prog['name']}, a multi-year programme to {prog['purpose'][0].lower() + prog['purpose'][1:]}"
          f". It requests a total budget of £{budget}m, including contingency, and recommends Option 3: a modular claims "
          f"platform, Claims Hub, onto which CLARA's capabilities are migrated progressively by region and product.",
          facts=[F("general", f"Programme Skerry budget requested in the 2024 business case: £{budget}m.", f"total budget of £{budget}m",
                   "ORG:company#programme.budget_gbp_m")])
    doc.p(f"CLARA has been the Society's claims system of record since {long_date(W.systems['SYS01']['go_live'])}. It "
          f"remains reliable, but it is increasingly costly and slow to change, it depends on a small number of specialist "
          f"staff, and it constrains the customer experience the Society wants to offer.")
    doc.ps(pr.paras(["bizcase", "bc2"], 2))
    doc.h(2, "1.1 Recommendation")
    doc.bullets([f"Approve {prog['name']} and a total budget of £{budget}m, released in tranches at stage gates.",
                 f"Confirm {ctx.person(prog['executive_sponsor'])} as executive sponsor.",
                 "Approve the appointment of an external delivery partner through the Society's procurement process.",
                 "Approve the decommissioning of CLARA and its satellite systems as part of the programme scope."])
    doc.ps(pr.paras(["bc2"], 1))

    # 2 Strategic context -------------------------------------------------------------------
    doc.h(1, "2 Strategic context", page_break=True)
    doc.ps(pr.paras(["bizcase", "bc2"], 3))
    doc.h(2, "2.1 The Society")
    co = W.company
    doc.p(f"{co['legal_name']} is a mutual property and casualty insurer founded in {co['founded']} as {co['founded_as']}. "
          f"It writes {', '.join(l.lower() for l in co['lines_of_business'][:-1])} and {co['lines_of_business'][-1]} "
          f"business in the UK and, through branches, in Norway, Sweden and Denmark, and employs around "
          f"{co['staff']:,} people.",
          facts=[F("general", "Corvane Mutual employs about 4,050 people.", f"{co['staff']:,} people", "ORG:company#staff")])
    doc.table(["Branch", "Country", "Currency"], [[b["name"], b["country"], b["currency"]] for b in co["branches"]],
              widths=[7.0, 4.0, 5.6], caption="Nordic branches", font_size=9)
    doc.h(2, "2.2 Drivers for change")
    drivers = [("Regulatory change", f"{W.circulars['CIRC-2024-07']['ref']} ({W.circulars['CIRC-2024-07']['title']}), effective "
                f"{long_date(W.circulars['CIRC-2024-07']['effective'])}, required changes to CLARA acknowledgement processing; "
                "further circulars are expected."),
               ("Customer expectations", "Customers expect digital notification, proactive updates and faster settlement."),
               ("Key-person risk", "CLARA knowledge is concentrated in a small team of long-serving specialists."),
               ("Cost of change", "Changes to CLARA take longer and cost more than equivalent changes on modern platforms."),
               ("Satellite systems", "The subrogation tracker and other satellites add integration complexity; SKADE-90 "
                f"was retired on {long_date('2024-05-31')}."),
               ("Operational resilience", "Batch dependencies and point-to-point interfaces make incidents harder to contain.")]
    doc.table(["Driver", "Description"], [list(d) for d in drivers], widths=[3.8, 12.8], caption="Drivers for change",
              font_size=8.8)
    doc.ps(pr.paras(["bc2", "bizcase"], 2))

    # 3 Current state ----------------------------------------------------------------------
    doc.h(1, "3 Current state", page_break=True)
    progs = H.programs_asof(ctx)
    by_area = collections.Counter(p["area"] for p in progs)
    ifaces = H.interfaces_asof(ctx)
    db2 = [t for t, x in W.tables.items() if x["db"] == "DB2" and str(x.get("created") or "0000") <= date and t != "CLR.T_FRAUD_NOTIFICATION"]
    doc.p(f"CLARA consists of {len(progs)} COBOL programs, {len(db2)} DB2 tables, {len(H.jobs_asof(ctx))} production batch "
          f"jobs and {len(ifaces)} interfaces to other systems. It runs on z/OS at the Leeds data centre, with disaster "
          f"recovery at Bristol.",
          facts=[F("scale", f"In November 2024 CLARA had {len(progs)} programs and {len(ifaces)} live interfaces.",
                   f"{len(progs)} COBOL programs", "SYSTEM:SYS01")])
    doc.table(["Functional area", "Programs"], [[a, str(n)] for a, n in sorted(by_area.items())], widths=[8.0, 8.6],
              caption="CLARA programs by area", font_size=9)
    doc.ps(pr.paras(["bizcase", "bc2"], 2))
    doc.h(2, "3.1 Systems landscape")
    sids = [s for s in W.systems if s not in ("SYS02",) and not (W.systems[s].get("go_live") and str(W.systems[s]["go_live"]) > date)
            and W.systems[s].get("lifecycle") != "retired" and s not in ("SYS15", "SYS16")]
    C.systems_table(ctx, doc, sids, "Current systems supporting claims")
    doc.ps(pr.paras(["bc2"], 2))
    doc.h(2, "3.2 Recent operational incidents")
    rows = []
    for inc in W.incidents.values():
        if str(inc["date"]) > date:
            continue
        rows.append([inc["id"], short_date(inc["date"]), ctx.a(inc["title"]), inc.get("impact") or "—"])
    doc.table(["Incident", "Date", "Title", "Impact"], rows, widths=[2.6, 2.4, 5.4, 6.2], font_size=8.6,
              caption="Incidents in 2024")
    doc.ps(pr.paras(["bc2", "bizcase"], 2))
    doc.h(2, "3.3 People and skills")
    rows = [[ctx.name(p), ctx.title(p)] for p in ("P016", "P023", "P024", "P025", "P026")]
    doc.table(["Name", "Role"], rows, widths=[6.0, 10.6], caption="Core CLARA specialists", font_size=9)
    doc.p("The CLARA team is experienced and committed, but small. Several team members are approaching retirement, and "
          "recruitment of COBOL and CICS skills has become difficult.")
    doc.ps(pr.paras(["bc2"], 2))

    # 4 Options --------------------------------------------------------------------------
    doc.h(1, "4 Options appraisal", page_break=True)
    doc.p("Four options were assessed against the programme objectives, delivery risk and long-term cost.")
    doc.table(["Option", "Description", "Benefit", "Long-term risk", "Flexibility", "Conclusion"],
              [list(o) for o in OPTIONS], widths=[3.4, 5.4, 1.6, 2.0, 1.8, 2.4], caption="Options summary", font_size=8.2)
    for o in OPTIONS:
        doc.h(2, o[0])
        doc.p(o[1])
        doc.ps(pr.paras(["bc2", "bizcase"], 2))
    doc.h(2, "4.5 Evaluation criteria")
    doc.table(["Criterion", "Weighting rationale"],
              [["Customer outcomes", "Faster, more transparent claims"], ["Regulatory compliance", "Ability to implement change quickly and safely"],
               ["Delivery risk", "Likelihood of delivering on time and within budget"], ["Operational risk", "Effect on resilience during and after the change"],
               ["Cost", "Whole-life cost over the appraisal period"], ["Strategic fit", "Alignment with the technology strategy"]],
              widths=[4.6, 12.0], font_size=8.8)
    doc.ps(pr.paras(["bc2"], 2))

    # 5 Recommended solution ----------------------------------------------------------------
    doc.h(1, "5 The recommended solution", page_break=True)
    doc.p("Claims Hub will provide the claims capabilities below as separately deployable components with their own "
          "data, connected by events and APIs. Each capability replaces the corresponding part of CLARA when its "
          "migration wave goes live.")
    doc.table(["Capability", "Scope"], [list(c) for c in CAPABILITIES], widths=[4.6, 12.0], caption="Claims Hub capabilities",
              font_size=8.8)
    fig = FG.box_diagram(CACHE / "fig" / FID / "transition.png", title="Transition from CLARA to Claims Hub",
                         boxes=[{"id": "now", "label": "Today\nCLARA + satellite systems", "x": 60, "y": 200, "w": 520, "h": 200, "color": "grey"},
                                {"id": "mid", "label": "Transition\nCLARA and Claims Hub in parallel,\nmigration by region and product", "x": 720, "y": 200, "w": 560, "h": 200, "color": "amber"},
                                {"id": "end", "label": "Target\nClaims Hub;\nCLARA decommissioned", "x": 1420, "y": 200, "w": 520, "h": 200, "color": "green"}],
                         arrows=[{"src": "now", "dst": "mid", "label": "MVP"}, {"src": "mid", "dst": "end", "label": "final wave"}],
                         size=(2000, 520))
    doc.figure(fig, "Transition from CLARA to Claims Hub",
               alt="Transition: today CLARA plus satellites; transition with CLARA and Claims Hub in parallel; target Claims Hub with CLARA decommissioned.")
    doc.ps(pr.paras(["bc2", "bizcase"], 3))
    doc.h(2, "5.1 Capability deep-dives")
    areas = {"First notice of loss": ["FNOL"], "Triage": ["TRIAGE"], "Assessment": ["ASSESS"], "Reserving": ["RESERVE"],
             "Fraud referral": ["FRAUD"], "Settlement and payments": ["SETTLE"], "Recovery": ["RECOVER"],
             "Documents and communications": ["COMMON"], "Finance and reporting": ["GL", "REPORT"]}
    stage_of = {"First notice of loss": "S1", "Triage": "S2", "Assessment": "S3", "Reserving": "S4", "Fraud referral": "S5",
                "Settlement and payments": "S6", "Recovery": "S7"}
    for k, (cap, scope) in enumerate(CAPABILITIES, 1):
        doc.h(3, f"5.1.{k} {cap}")
        ps_all = [p_ for p_ in progs if p_["area"] in areas[cap]]
        ps_ = [p_ for p_ in ps_all if p_.get("replaced_by")]          # programs.yaml replaced_by (fix pass, m29)
        ret = [p_["id"] for p_ in ps_all if not p_.get("replaced_by")]
        ifs = []
        for p_ in ps_all:
            for i in H.interfaces_for_program(ctx, p_["id"]):
                if i["id"] not in ifs:
                    ifs.append(i["id"])
        repl = f"{len(ps_)} ({', '.join(p_['id'] for p_ in ps_[:8])}{', …' if len(ps_) > 8 else ''})" if ps_ else "none"
        if ret:
            repl += f"; {len(ret)} retired with CLARA ({', '.join(ret[:4])}{', …' if len(ret) > 4 else ''})"
        pairs = [["Scope", scope], ["CLARA programs replaced", repl],
                 ["Interfaces affected", ", ".join(ifs) or "—"]]
        if cap in stage_of:
            own = W.owner_of_process(stage_of[cap], date)
            pairs.append(["Process owner", ctx.person(own)])
        doc.kv(pairs, widths=(4.4, 12.2), font_size=9)
        doc.ps(pr.paras(["bc2", "bizcase"], 2, n=(4, 6)))
    doc.h(2, "5.2 Systems to be retired")
    rows = [[ctx.sys("SYS01"), "Replaced by Claims Hub", f"by {long_date(W.systems['SYS01']['decommission_target'])}"],
            [ctx.sys("SYS24"), "Replaced by the recovery capability", "after the relevant migration wave"],
            [ctx.sys("SYS27"), "Replaced by digital intake", "after the relevant migration wave"],
            [ctx.sys("SYS18"), "Retired with CLARA batch", "with CLARA"], [ctx.sys("SYS14"), "Retired with CLARA interfaces", "with CLARA"]]
    doc.table(["System", "Replacement", "Target"], rows, widths=[4.6, 7.0, 5.0], font_size=8.8)
    doc.ps(pr.paras(["bc2"], 2))

    # 6 Benefits ----------------------------------------------------------------------------
    doc.h(1, "6 Benefits", page_break=True)
    doc.table(["Benefit", "Description", "Owner"],
              [["Faster claims", "Shorter time from notification to settlement", ctx.person("P005")],
               ["Lower cost of change", "Regulatory and product changes delivered faster", ctx.person("P006")],
               ["Reduced key-person risk", "Modern skills, documented services", ctx.person("P006")],
               ["Better fraud control", "Consistent, auditable referral decisions", ctx.person("P008")],
               ["Better reserving data", "Complete movement history and timely reserves", ctx.person("P010")],
               ["Decommissioning savings", "Mainframe and licence costs removed after CLARA is retired", ctx.person(cfo)]],
              widths=[3.8, 8.0, 4.8], caption="Benefits and owners", font_size=8.8)
    doc.ps(pr.paras(["bc2", "bizcase"], 3))

    # 7 Costs ------------------------------------------------------------------------------
    doc.h(1, "7 Costs and funding")
    doc.p(f"The total budget requested is £{budget}m over the life of the programme, including contingency. Funding is "
          f"released in tranches; each tranche is subject to a stage-gate review by the steering committee and the CFO.")
    doc.table(["Cost category", "Included"],
              [["Delivery partner and internal team", "Yes"], ["Platform and infrastructure", "Yes"], ["Software licences", "Yes"],
               ["Data migration", "Yes"], ["Business change and training", "Yes"], ["CLARA decommissioning", "Yes"],
               ["Contingency", "Yes"], ["Run costs after go-live", "No – business as usual budgets"]],
              widths=[8.0, 8.6], caption="Scope of the budget", font_size=9)
    doc.ps(pr.paras(["bc2", "bizcase"], 2))

    # 8 Delivery -----------------------------------------------------------------------
    doc.h(1, "8 Delivery approach", page_break=True)
    doc.p("Delivery starts with a minimum viable product covering notification of loss and triage for digital channels, "
          "followed by migration waves by region and product. CLARA remains the system of record for each product until "
          "its wave is complete.")
    doc.table(["Phase", "Scope", "Indicative timing"],
              [["Mobilisation", "Partner appointment, governance, architecture and plans", "Early 2025"],
               ["MVP", "Notification of loss and triage for digital channels", "Late 2025"],
               ["Migration waves", "Products migrated by region and product line", "2026 to 2027"],
               ["Decommissioning", "CLARA and satellites retired", f"By {long_date(W.systems['SYS01']['decommission_target'])}"]],
              widths=[3.4, 8.6, 4.6], caption="Indicative plan", font_size=8.8)
    doc.ps(pr.paras(["bc2", "migration"], 3))
    doc.h(2, "8.1 Governance")
    doc.p(f"A steering committee chaired by the executive sponsor, {ctx.person(prog['executive_sponsor'])}, will govern "
          f"the programme. Architecture decisions will be taken by the Design Authority chaired by {ctx.person('P018')}. "
          f"Changes to production will follow the Change Advisory Board process.")
    doc.ps(pr.paras(["bc2", "governance"], 2))

    # 9 Risks --------------------------------------------------------------------------
    doc.h(1, "9 Risks")
    doc.table(["Ref", "Risk", "Mitigation", "Owner"],
              [["R1", "Data migration errors", "Rehearsals and full reconciliation for each wave", ctx.name(prog["executive_sponsor"])],
               ["R2", "Loss of CLARA skills during the programme", "Retention arrangements and knowledge capture", ctx.name("P006")],
               ["R3", "Regulatory change during delivery", "Modular design; change capacity reserved", ctx.name("P005")],
               ["R4", "Interface breakage between platforms", "Contract testing and consumer sign-off", ctx.name("P006")],
               ["R5", "Business readiness", "Change management and training plan per wave", ctx.name("P005")],
               ["R6", "Cost overrun", "Stage gates and contingency control", ctx.name(cfo)],
               ["R7", "Delivery partner performance", "Contract with outcome-based milestones", ctx.name(prog["executive_sponsor"])]],
              widths=[1.2, 5.0, 6.8, 3.6], caption="Principal risks", font_size=8.6)
    doc.ps(pr.paras(["bc2", "bizcase"], 3))

    # 9a Further sections -------------------------------------------------------------
    extra = [
        ("Benefits realisation", ["bc2", "bizcase"], [
            ["Benefit owner nominated", "Each benefit has a named owner in the business"],
            ["Baseline", "Measured before the first release"],
            ["Tracking", "Reported quarterly to the steering committee"],
            ["Hand-over", "Benefits handed to business owners at programme closure"]]),
        ("Architecture principles", ["bc2", "arch"], [
            ["Modular", "Capabilities are separately deployable with their own data"],
            ["Event-driven", "State changes are published as events for other capabilities"],
            ["API-first", "Capabilities expose documented APIs"],
            ["Cloud-ready", "Runs on the Society's container platform"],
            ["Secure by design", "Identity, access and data protection built in"]]),
        ("Data migration approach", ["bc2", "migration"], [
            ["Scope", "Open claims and the closed-claim history required for servicing"],
            ["Approach", "Migration by region and product, with rehearsals"],
            ["Reconciliation", "Full reconciliation of counts and amounts for each wave"],
            ["Archive", "Older closed claims archived rather than migrated"]]),
        ("Organisation and resourcing", ["bc2", "governance"], [
            ["Executive sponsor", ctx.person(prog["executive_sponsor"])],
            ["Business owner", ctx.person("P005")],
            ["Technology owner", ctx.person("P006")],
            ["Finance", ctx.person(cfo)],
            ["Risk oversight", ctx.person("P007")],
            ["Architecture", ctx.person("P018")]]),
        ("Procurement", ["bc2", "vendor"], [
            ["Delivery partner", "Competitive selection under the procurement policy"],
            ["Platform software", "Existing enterprise agreements where possible"],
            ["Contract model", "Outcome-based milestones with retention"]]),
        ("Security and data protection", ["bc2", "security"], [
            ["Data protection impact assessment", "Completed before any personal data is migrated"],
            ["Access control", "Single sign-on and role-based access"],
            ["Test data", "Masked data only outside production"]]),
        ("Regulatory considerations", ["bc2", "bizcase"], [
            ["Regulator", f"{W.regulators['REG-NISA']['name']}"],
            ["Returns affected", "NISA-TP2 and NISA-CT1 regulatory returns"],
            ["Engagement", "Early engagement on customer-facing and reporting changes"]]),
        ("Change management and training", ["bc2", "opm2"], [
            ["Change network", "Change champions in each claims team"],
            ["Training", "Role-based training before each go-live"],
            ["Support", "Floor-walkers and hyper-care after each go-live"]]),
        ("Dependencies", ["bc2", "governance"], [
            ["Container platform", "Platform readiness before the MVP"],
            ["Identity", "Single sign-on for workforce and partners"],
            ["Event streaming", "Enterprise event platform available before the first migration wave"],
            ["Policy system", "Policy data available to Claims Hub through an API"]]),
        ("Assumptions", ["bc2"], [
            ["A1", "CLARA remains supportable until decommissioning"],
            ["A2", "Business experts can be released to the programme"],
            ["A3", "No major acquisition or divestment during delivery"],
            ["A4", "The regulatory change pipeline remains manageable alongside the programme"]]),
    ]
    for k, (title, banks, rows) in enumerate(extra, 1):
        doc.h(1, f"{9 + k} {title}", page_break=True)
        doc.ps(pr.paras(banks, 3, n=(4, 6)))
        doc.table(["Item", "Approach"], rows, widths=[4.6, 12.0], font_size=9)
        doc.ps(pr.paras(banks, 1, n=(4, 6)))

    # 10 Approval ----------------------------------------------------------------------
    doc.h(1, f"{10 + len(extra)} Approval", page_break=True)
    doc.p(f"The Executive Committee is asked to approve {prog['name']} and a total budget of £{budget}m on the terms set "
          f"out in this business case.")
    doc.p("Signed for and on behalf of Corvane Mutual Insurance Society Limited:")
    doc.p(f"Gareth Whitcombe, Chief Financial Officer — signed {long_date(date)}. Budget approved: £{budget}m.",
          facts=[PF(ctx, "ld28_cfo", f"{W.name_of('P002', date)}, Chief Financial Officer", anchor="Signed for and on behalf of",
                    notes="Signature page (Approval section).")])
    doc.table(["Name", "Title", "Role", "Signature", "Date"],
              [[ctx.name(cfo), ctx.title(cfo), "Author and budget holder", "Signed", short_date(date)],
               [ctx.name(prog["executive_sponsor"]), ctx.title(prog["executive_sponsor"]), "Executive sponsor", "Signed", short_date(date)],
               [ctx.name("P003"), ctx.title("P003"), "Chair, Executive Committee", "Signed", short_date(date)],
               [ctx.name("P005"), ctx.title("P005"), "Business owner", "Signed", short_date(date)],
               [ctx.name("P006"), ctx.title("P006"), "Technology owner", "Signed", short_date(date)]],
              widths=[3.6, 4.4, 4.0, 2.2, 2.4], caption="Signatures", font_size=8.8,
              facts=[F("alias_use", "The 2024 business case is signed by the then CFO, Gareth Whitcombe, on 2024-11-18.",
                       "Gareth Whitcombe", "PERSON:P002#role_aliases", where=(1, 0))])

    # Appendices -----------------------------------------------------------------------
    doc.h(1, "Appendix A – CLARA interfaces", page_break=True)
    rows = [[i["id"], ctx.a(i["name"]), ctx.sys(i["source_system"]), ctx.sys(i["target_system"]), i["protocol"]] for i in ifaces]
    doc.table(["ID", "Name", "From", "To", "Protocol"], rows, widths=[2.2, 6.0, 3.0, 3.4, 2.0], caption="Interfaces", font_size=8.0)
    doc.h(1, "Appendix B – CLARA batch jobs", page_break=True)
    rows = [[j["name"], ctx.a(j["description"]).split(" (")[0], ", ".join(s["program"] for s in j["steps"])] for j in H.jobs_asof(ctx)]
    doc.table(["Job", "Description", "Programs"], rows, widths=[2.6, 8.4, 5.6], caption="Batch jobs", font_size=8.2)
    doc.h(1, "Appendix C – CLARA program inventory", page_break=True)
    rows = [[p["id"], H.program_desc(ctx, p["id"]), p["area"], p["type"]] for p in sorted(progs, key=lambda x: x["id"])]
    rows = [[r[0], ctx.a(r[1]).split(" (")[0], r[2], r[3]] for r in rows]
    doc.table(["Program", "Description", "Area", "Type"], rows, widths=[2.4, 9.6, 2.4, 2.2], caption="Programs", font_size=8.0)
    doc.h(1, "Appendix D – CLARA DB2 tables", page_break=True)
    rows = [[t, ctx.a(W.tables[t].get("description", "")).split(" (")[0], W.tables[t].get("area", "—")] for t in sorted(db2)]
    doc.table(["Table", "Description", "Area"], rows, widths=[5.0, 9.4, 2.2], caption="Tables", font_size=8.2)
    doc.h(1, "Appendix E – Claims process", page_break=True)
    rows = []
    for sid, s in W.stages.items():
        own = W.owner_of_process(sid, date)
        rows.append([sid, s["name"], ctx.person(own) if own else "—",
                     ", ".join(ctx.a(W.steps[x]["name"]) for x in s["steps"] if x not in ("PS-FRD-03", "PS-FRD-05"))])
    doc.table(["Stage", "Name", "Owner", "Steps"], rows, widths=[1.4, 3.2, 4.6, 7.4], caption="Claims process stages", font_size=8.2)
    doc.h(1, "Appendix F – Business rules implemented in CLARA", page_break=True)
    doc.p("The business rules below are in force at the date of this business case and will be re-implemented in Claims "
          "Hub as versioned configuration. Rule texts are maintained in the claims standards library.")
    rows = []
    for rid, r in W.rules.items():
        v = ctx.rule(rid)
        if not v:
            continue
        rows.append([rid, ctx.a(r["title"]), f"v{v['version']}", r["area"]])
    doc.table(["Rule", "Title", "Version", "Area"], rows, widths=[2.6, 10.4, 1.6, 2.0], caption="Rules in force", font_size=8.0)
    doc.h(1, "Appendix G – Products and claim types", page_break=True)
    doc.table(["Product", "Code", "Line", "Country"], [[p_["name"], p_["code"], p_["line"], p_.get("country", "—")] for p_ in W.products.values()],
              widths=[6.4, 3.0, 4.2, 3.0], caption="Products", font_size=8.6)
    doc.table(["Claim type", "Code"], [[ct["name"], ct["id"]] for ct in W.claim_types.values()], widths=[10.0, 6.6],
              caption="Claim types", font_size=8.6)
    doc.h(1, "Appendix H – Options scoring detail", page_break=True)
    crit = ["Customer outcomes", "Regulatory compliance", "Delivery risk", "Operational risk", "Cost", "Strategic fit"]
    score = {"Option 0": ["Low", "Low", "High", "Low", "Medium", "Low"], "Option 1": ["Low", "Medium", "Medium", "Medium", "Medium", "Low"],
             "Option 2": ["Medium", "Medium", "Medium", "Medium", "Medium", "Medium"], "Option 3": ["High", "High", "Medium", "Medium", "Medium", "High"]}
    doc.table(["Criterion"] + list(score), [[c] + [score[o][i] for o in score] for i, c in enumerate(crit)],
              widths=[4.6, 3.0, 3.0, 3.0, 3.0], caption="Assessment by criterion (higher is better except delivery risk)", font_size=8.8)
    for o in OPTIONS:
        doc.h(2, o[0])
        doc.ps(pr.paras(["bc2", "bizcase"], 2, n=(4, 6)))
    doc.h(1, "Appendix I – Stakeholders", page_break=True)
    rows = []
    for pid in ("P003", "P002", "P004", "P005", "P006", "P007", "P010", "P011", "P008", "P016", "P018", "P037", "P019"):
        rows.append([ctx.name(pid), ctx.title(pid), "Approver" if pid in ("P003", "P002", "P004") else "Key stakeholder"])
    doc.table(["Name", "Title", "Role"], rows, widths=[4.6, 7.4, 4.6], caption="Stakeholders", font_size=9)
    doc.ps(pr.paras(["bc2"], 2, n=(4, 6)))
    doc.h(1, "Appendix J – Glossary")
    doc.table(["Term", "Meaning"], [[t, ctx.a(m)] for t, m in C.glossary_terms(["G-019", "G-020", "G-005", "G-003"])]
              + [["MVP", "Minimum viable product: the first release of Claims Hub."],
                 ["Stage gate", "A formal review at which funding for the next phase is released."]],
              widths=[3.6, 13.0], font_size=8.8)
    H.apply_program_renames(doc)   # FNETCAL1 / FNETREF1 until the 2025-03-01 rename
    return doc


def post_check(doc, texts):
    from harness import extract as X
    out = []
    for term in ("Sentinel", "Evidence Vault", "Assessor Portal", "IBM", "Priya Raman", "Ashby", "reserve-engine"):
        pages = [i + 1 for i, t in enumerate(texts) if term in " ".join(t.split())]
        if pages:
            out.append(f"anachronism {term!r} on pages {pages[:6]}")
    sig = [i + 1 for i, t in enumerate(texts) if X.match("Gareth Whitcombe, Chief Financial Officer", t)]
    out.append(f"INFO signature pages {sig}; total {len(texts)}")
    return out

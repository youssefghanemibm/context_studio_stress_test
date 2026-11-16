"""LD013 – Claims Hub Target Architecture v1.0 (DOCX, 2025-03-03, pre-rename: 'reserve-svc')."""
from __future__ import annotations

from . import common as C
from . import figures as FG
from . import hub as H
from .core import CACHE, Ctx, Doc, F, PF, Style, W, long_date, util
from .prose import Prose

FID = "LD013"
DENS = 6   # filler density knob (paragraphs per subsection)


def _figs(ctx: Ctx) -> dict:
    out = {}
    fdir = CACHE / "fig" / FID
    S = ctx.sys
    out["context"] = FG.box_diagram(
        fdir / "fig1_context.png", title="Figure 1 – CLARA current-state context (selected interfaces)",
        boxes=[
            {"id": "clara", "label": "CLARA\nCOBOL / CICS / DB2", "x": 800, "y": 480, "w": 400, "h": 230, "color": "amber"},
            {"id": "portal", "label": S("SYS04"), "x": 60, "y": 140, "w": 340, "h": 120},
            {"id": "crm", "label": S("SYS12"), "x": 60, "y": 560, "w": 340, "h": 120},
            {"id": "palm", "label": S("SYS08") + " (policy)", "x": 820, "y": 130, "w": 360, "h": 110},
            {"id": "snt", "label": S("SYS03"), "x": 1560, "y": 140, "w": 380, "h": 120},
            {"id": "ext", "label": S("SYS17"), "x": 1560, "y": 560, "w": 380, "h": 120},
            {"id": "mq", "label": S("SYS14") + "\n(CLRQM01)", "x": 820, "y": 900, "w": 360, "h": 130, "color": "grey"},
            {"id": "gl", "label": S("SYS06"), "x": 120, "y": 1010, "w": 340, "h": 120, "color": "green"},
            {"id": "cdw", "label": S("SYS11"), "x": 1560, "y": 1010, "w": 380, "h": 120, "color": "green"},
        ],
        arrows=[
            {"src": "portal", "dst": "clara", "label": "CLX-IF-001 portal FNOL"},
            {"src": "crm", "dst": "clara", "label": "CLX-IF-002 FNOL hand-off"},
            {"src": "palm", "dst": "clara", "label": "CLX-IF-003 policy snapshot"},
            {"src": "clara", "dst": "snt", "label": "CLX-IF-008 online scoring"},
            {"src": "clara", "dst": "ext", "label": "CLX-IF-013 assessor instructions"},
            {"src": "clara", "dst": "mq", "label": "CLX-IF-042 reserve movements"},
            {"src": "mq", "dst": "gl", "label": "CLX-IF-043 GL reserve journals"},
            {"src": "mq", "dst": "cdw", "label": "CLX-IF-044 reserve fact load"},
        ])
    out["target"] = FG.box_diagram(
        fdir / "fig2_target.png", title="Figure 2 – Claims Hub target container view",
        size=(2000, 1350),
        boxes=[
            {"id": "ch", "label": "Channels: " + S("SYS04") + ", " + S("SYS12") + ", Evidence Intake Gateway",
             "x": 380, "y": 110, "w": 1240, "h": 100, "color": "grey"},
            {"id": "fnol", "label": "fnol-intake-svc", "x": 80, "y": 300, "w": 400, "h": 110},
            {"id": "tri", "label": "triage-svc", "x": 560, "y": 300, "w": 400, "h": 110},
            {"id": "core", "label": "claim-core-svc", "x": 1040, "y": 300, "w": 400, "h": 110},
            {"id": "asm", "label": "assessment-svc", "x": 1520, "y": 300, "w": 400, "h": 110},
            {"id": "esp", "label": "Event Streaming Platform (Kafka, esp-prd)", "x": 80, "y": 560, "w": 1840, "h": 110,
             "color": "purple"},
            {"id": "rsv", "label": ctx.svc("reserve-engine"), "x": 80, "y": 820, "w": 400, "h": 110, "color": "amber"},
            {"id": "frd", "label": "fraud-referral-svc", "x": 560, "y": 820, "w": 400, "h": 110},
            {"id": "stl", "label": "settlement-svc", "x": 1040, "y": 820, "w": 400, "h": 110},
            {"id": "pay", "label": "payment-orchestrator", "x": 1520, "y": 820, "w": 400, "h": 110},
            {"id": "glp", "label": "gl-posting-svc", "x": 80, "y": 1120, "w": 400, "h": 110, "color": "green"},
            {"id": "rep", "label": "reporting-feed-svc", "x": 560, "y": 1120, "w": 400, "h": 110, "color": "green"},
            {"id": "rec", "label": "recovery-svc", "x": 1040, "y": 1120, "w": 400, "h": 110},
            {"id": "doc", "label": "document-svc / notification-svc", "x": 1520, "y": 1120, "w": 400, "h": 110},
        ],
        arrows=[
            {"src": "ch", "dst": "fnol", "label": "POST /fnol"},
            {"src": "fnol", "dst": "esp", "label": "fnol.received.v1", "sx": -60, "tx": -760},
            {"src": "tri", "dst": "esp", "label": "triage.completed.v1", "tx": -280},
            {"src": "esp", "dst": "rsv", "label": "triage.completed.v1", "sx": -700, "lx": -10},
            {"src": "rsv", "dst": "glp", "label": ctx.a("reserve.changed.v2")},
            {"src": "stl", "dst": "pay", "label": "settlement.agreed.v1"},
        ])
    out["reserve"] = FG.box_diagram(
        fdir / "fig3_reserve_sync.png", title="Figure 3 – Reserve synchronisation during coexistence",
        boxes=[
            {"id": "clara", "label": "CLARA\nCLRRS170", "x": 60, "y": 200, "w": 360, "h": 150, "color": "amber"},
            {"id": "mq", "label": "MQ Backbone", "x": 600, "y": 200, "w": 360, "h": 150, "color": "grey"},
            {"id": "rep", "label": "Republication component\n(open item OI-07)", "x": 1180, "y": 200, "w": 420, "h": 150,
             "color": "white"},
            {"id": "esp", "label": "Event Streaming Platform", "x": 1180, "y": 560, "w": 420, "h": 140, "color": "purple"},
            {"id": "rsv", "label": ctx.svc("reserve-engine"), "x": 600, "y": 560, "w": 360, "h": 140, "color": "blue"},
            {"id": "glp", "label": "gl-posting-svc", "x": 600, "y": 920, "w": 360, "h": 140, "color": "green"},
            {"id": "gl", "label": S("SYS06"), "x": 60, "y": 920, "w": 360, "h": 140, "color": "green"},
        ],
        arrows=[
            {"src": "clara", "dst": "mq", "label": "CLX-IF-042 RSVMOVE records"},
            {"src": "mq", "dst": "rep", "label": "consume"},
            {"src": "rep", "dst": "esp", "label": "claims.reserve.movement.v1"},
            {"src": "esp", "dst": "rsv", "label": "parallel-run comparison"},
            {"src": "rsv", "dst": "glp", "label": ctx.a("reserve.changed.v2")},
            {"src": "mq", "dst": "gl", "label": "CLX-IF-043 GL journals", "lx": 40},
        ])
    out["deploy"] = FG.box_diagram(
        fdir / "fig4_deployment.png", title="Figure 4 – Deployment view",
        groups=[{"label": "OpenShift ocp-prd-lon1 (London, primary)", "x": 40, "y": 110, "w": 1240, "h": 760},
                {"label": "OpenShift ocp-dr-lds1 (Leeds, DR)", "x": 1320, "y": 110, "w": 640, "h": 360},
                {"label": "z/OS LPAR PRD1 (Leeds Data Centre)", "x": 1320, "y": 520, "w": 640, "h": 350}],
        boxes=[{"id": f"n{i}", "label": ns, "x": 80 + (i % 3) * 400, "y": 180 + (i // 3) * 165, "w": 360, "h": 120,
                "color": "blue"} for i, ns in enumerate(sorted({W.services[s]["k8s_namespace"] for s in W.services}))]
        + [{"id": "dr", "label": "Standby namespaces\n(replicated configuration)", "x": 1370, "y": 190, "w": 540, "h": 220,
            "color": "grey"},
           {"id": "zos", "label": "CLARA (CICS, DB2, batch)\nMQ queue manager CLRQM01", "x": 1370, "y": 600, "w": 540,
            "h": 220, "color": "amber"},
           {"id": "esp", "label": "Kafka esp-prd (6 brokers)", "x": 80, "y": 1010, "w": 560, "h": 120, "color": "purple"},
           {"id": "hubqm", "label": "MQ queue manager HUBQM01", "x": 760, "y": 1010, "w": 520, "h": 120, "color": "grey"}],
        arrows=[{"src": "hubqm", "dst": "zos", "label": "MQ channels"}],
        size=(2000, 1200))
    out["identity"] = FG.box_diagram(
        fdir / "fig5_identity.png", title="Figure 5 – Workforce and partner sign-in",
        boxes=[{"id": "u", "label": "Corvane staff and partner Claims Assessors", "x": 60, "y": 420, "w": 420, "h": 160},
               {"id": "cis", "label": "Corvane Identity Service (OIDC)", "x": 790, "y": 140, "w": 440, "h": 150,
                "color": "teal"},
               {"id": "ui", "label": "Claims Hub workbench / " + S("SYS17"), "x": 790, "y": 700, "w": 440, "h": 150},
               {"id": "svc", "label": "Claims Hub services", "x": 1500, "y": 700, "w": 420, "h": 150}],
        arrows=[{"src": "u", "dst": "cis", "label": "sign in"},
                {"src": "cis", "dst": "ui", "label": "ID and access tokens"},
                {"src": "ui", "dst": "svc", "label": "bearer token"},
                {"src": "u", "dst": "ui", "label": "browser session"}],
        size=(2000, 1000))
    out["fnol"] = FG.lane_diagram(
        fdir / "fig6_fnol_lanes.png", title="Figure 6 – FNOL and triage in the target (MVP scope)",
        lanes=["Customer / channel", "fnol-intake-svc", "triage-svc", S("SYS03"), "claim-core-svc"],
        steps=[{"id": "a", "lane": 0, "col": 0, "label": "Notify claim (portal, app, phone)"},
               {"id": "b", "lane": 1, "col": 1, "label": "Validate mandatory data set"},
               {"id": "c", "lane": 2, "col": 2, "label": "Request fraud score"},
               {"id": "d", "lane": 3, "col": 3, "label": "Return score 0–100", "color": "amber"},
               {"id": "e", "lane": 2, "col": 4, "label": "Classify tier and route"},
               {"id": "f", "lane": 4, "col": 4, "label": "Create claim record", "color": "green"}],
        arrows=[{"src": "a", "dst": "b", "label": "POST /fnol"},
                {"src": "b", "dst": "c", "label": "fnol.received.v1"},
                {"src": "c", "dst": "d", "label": "score request"},
                {"src": "d", "dst": "e", "label": "score"},
                {"src": "e", "dst": "f", "label": "triage.completed.v1"}],
        size=(2000, 1250))
    out["payments"] = FG.box_diagram(
        fdir / "fig7_payments.png", title="Figure 7 – Settlement and payment flow (target)",
        boxes=[{"id": "stl", "label": "settlement-svc", "x": 80, "y": 300, "w": 380, "h": 130},
               {"id": "pay", "label": "payment-orchestrator", "x": 620, "y": 300, "w": 420, "h": 130},
               {"id": "ws", "label": S("SYS19") + " (sanctions)", "x": 620, "y": 700, "w": 420, "h": 130, "color": "teal"},
               {"id": "cpg", "label": S("SYS09"), "x": 1220, "y": 300, "w": 420, "h": 130, "color": "grey"},
               {"id": "bank", "label": W.vendors["VEN-11"]["name"], "x": 1220, "y": 700, "w": 420, "h": 130, "color": "white"},
               {"id": "rec", "label": "recovery-svc", "x": 80, "y": 700, "w": 380, "h": 130},
               {"id": "glp", "label": "gl-posting-svc", "x": 620, "y": 1000, "w": 420, "h": 120, "color": "green"}],
        arrows=[{"src": "stl", "dst": "pay", "label": "settlement.agreed.v1"},
                {"src": "stl", "dst": "rec", "label": "settlement.agreed.v1"},
                {"src": "pay", "dst": "ws", "label": "screen payee"},
                {"src": "pay", "dst": "cpg", "label": "payment.requested.v1"},
                {"src": "cpg", "dst": "bank", "label": "ISO 20022 pain.001"},
                {"src": "ws", "dst": "glp", "label": "payment.confirmed.v1", "lx": 10}],
        size=(2000, 1200))
    return out


def build() -> Doc:
    ctx = Ctx(FID)
    date = ctx.date
    pr = Prose(util.rng(f"{FID}:prose"), date=ctx.date)
    doc = Doc(ctx, title="Claims Hub Target Architecture", doc_id="SKR-ARC-001", version="1.0", status="Approved",
              subtitle="Programme Skerry – solution architecture baseline for the replacement of CLARA",
              style=Style(font="Calibri", heading_font="Calibri", accent="1F3864", accent2="DCE6F2", size=11),
              header_left="Programme Skerry – Claims Hub Target Architecture",
              header_right="SKR-ARC-001 v1.0 (Approved)")
    doc.header_facts.append(F("header", "The target architecture document ID is SKR-ARC-001 v1.0.", "SKR-ARC-001 v1.0",
                              f"ANCHOR:{FID}"))
    figs = _figs(ctx)
    rsvc = ctx.svc("reserve-engine")
    assert rsvc == "reserve-svc"

    doc.title_page(C.control_rows(ctx, doc, owner="P018", extra=[["Programme", "Programme Skerry"],
                                                                 ["Forum", "Design Authority (" + W.committees["COM-05"]["name"] + ")"]]),
                   facts=[F("general", "The target architecture is owned by Tomasz Wójcik, Enterprise Architect.",
                            ctx.person("P018"), "PERSON:P018", where=(6, 1))])
    C.version_history(ctx, doc, [("0.1", 35, "Outline and principles for Design Authority review"),
                                 ("0.4", 21, "Service catalogue and event backbone added"),
                                 ("0.8", 10, "Interface catalogue, deployment and security views"),
                                 ("0.9", 4, "Review comments from Integration Platform and Legacy Claims Platforms"),
                                 ("1.0", 0, "Approved by the Design Authority")])
    C.reviewers(ctx, doc, ["P050", "P053", "P031", "P016", "P036", "P019", "P052"])
    C.approvals(ctx, doc, [("P018", "Design Authority chair"), ("P006", "Technology sponsor"),
                           ("P017", "Product owner"), ("P048", "IBM delivery lead")])
    C.distribution(ctx, doc, ["Programme Skerry Steering Committee", "Design Authority", "Hub squads",
                              "Legacy Claims Platforms (CLARA)", "Integration Platform", "Enterprise Architecture"])
    doc.toc(depth=2)

    # 1 Introduction ------------------------------------------------------------------
    doc.h(1, "1 Introduction")
    doc.h(2, "1.1 Purpose")
    doc.p("This document is the approved target architecture for Claims Hub, the platform that Programme Skerry is "
          "building to replace CLARA, Corvane's mainframe claims ledger. It describes the services, events, data stores, "
          "integration patterns and deployment model that delivery teams must follow, and the transition arrangements "
          "that allow CLARA and Claims Hub to run side by side while claims are migrated.")
    doc.p(pr.para(["intro", "governance"], n=3, topic="the target architecture"))
    doc.h(2, "1.2 Scope")
    doc.bullets(["The thirteen Claims Hub services and their responsibilities.",
                 "The event backbone and the topics that services publish and consume.",
                 "Service data stores and the ownership of claims data in the target.",
                 "Interfaces between Claims Hub, CLARA and the surrounding systems during coexistence.",
                 "Runtime platform, environments, identity and security controls.",
                 "Non-functional requirements and the transition approach."])
    doc.p("Out of scope: detailed API specifications (maintained with each service), data migration design (covered by "
          "the Data Migration Strategy), test approach (covered by the Test Strategy) and changes to the policy "
          "administration platform.")
    doc.h(2, "1.3 Related decisions")
    adrs = [a for a in W.adrs.values() if a["date"] <= date and a["status"] in ("accepted", "proposed", "superseded")]
    doc.table(["ADR", "Title", "Date", "Status"],
              [[a["id"], ctx.a(a["title"]), a["date"], a["status"]] for a in adrs], widths=[2.0, 10.0, 2.6, 2.0],
              caption="Architecture decision records referenced by this document",
              facts=[F("general", "ADR-002 (2025-02-17) adopted Kafka as the Claims Hub event backbone.",
                       "Kafka (Event Streaming Platform) as the Claims Hub event backbone", "ADR:ADR-002",
                       where=(2, 1)),
                     F("general", "ADR-004 retains MQ for mainframe integration until CLARA decommissioning.",
                       "Retain MQ for mainframe integration until CLARA decommissioning", "ADR:ADR-004", where=(4, 1))])
    doc.p(pr.para("governance", n=3))
    doc.h(2, "1.4 Conventions")
    doc.p(f"Service names are written in lower case as deployed (for example {rsvc}). Interface identifiers use the "
          "CLX-IF-nnn numbering of the interface catalogue. Topic names follow the convention agreed in ADR-002: "
          "<domain>.<event>.v<n>. CLARA program and table names are given as they appear on the mainframe.")

    # 2 Business context ---------------------------------------------------------------
    doc.h(1, "2 Business context", page_break=True)
    co = W.company
    doc.h(2, "2.1 Corvane Mutual")
    doc.p(f"{co['legal_name']} is a mutual property and casualty insurer with around {co['staff']:,} staff. It writes "
          f"{', '.join(l.lower() for l in co['lines_of_business'][:-1])} and {co['lines_of_business'][-1]} business in the "
          f"United Kingdom and, through its branches, in Norway, Sweden and Denmark. Claims are handled from Leeds, "
          f"Bristol and Glasgow in the UK and from the Oslo, Stockholm and Copenhagen offices.")
    rows = [[k, f"{v:,}"] for k, v in co["staff_by_country"].items()]
    doc.table(["Country", "Staff"], rows, widths=[6, 4], caption="Staff by country")
    doc.h(2, "2.2 Programme Skerry")
    doc.p(f"Programme Skerry replaces CLARA with Claims Hub. The business case was signed by the Chief Financial Officer, "
          f"{W.name_of('P002', date)}, on {long_date(co['programme']['business_case_date'])} with a budget of "
          f"£{co['programme']['budget_gbp_m']}m. The programme's executive sponsor is {ctx.person(co['programme']['executive_sponsor'])}. "
          f"IBM Consulting joined as delivery partner on {long_date(co['programme']['ibm_engagement_start'])}.",
          facts=[F("general", "Programme Skerry business case signed by CFO Gareth Whitcombe on 2024-11-18 with a £48.6m budget.",
                   "Gareth Whitcombe, on 18 November 2024 with a budget of £48.6m", "TIMELINE:EV-010")])
    doc.p(pr.para("bizcase", n=4))
    doc.h(2, "2.3 Capability map")
    doc.p("Claims Hub is organised around the seven stages of the claims value chain. Each stage has an accountable "
          "business owner and is supported by one or more services.")
    rows = []
    for sid, s in W.stages.items():
        owner = W.owner_of_process(sid, date)
        rows.append([sid, s["name"], ctx.person(owner) if owner else "—", str(len(s["steps"]))])
    doc.table(["Stage", "Name", "Business owner", "Steps"], rows, widths=[1.6, 4.6, 8.4, 2.0],
              caption="Claims stages and business owners at the date of this document",
              facts=[F("temporal", "At 2025-03-03 the recovery & subrogation stage owner was Siobhan Quill (Acting Recoveries Manager).",
                       "Siobhan Quill, Acting Recoveries Manager", "PROCESS:S7#owner_history", where=(7, 2))])
    doc.p(pr.para(["opmodel", "bizcase"], n=3))
    doc.h(2, "2.4 Capabilities by stage")
    for sid, stg in W.stages.items():
        doc.h(3, f"2.4.{stg['order']} {stg['name']}")
        doc.p(f"The {stg['name'].lower()} stage comprises the following steps. Systems that support the stage today: "
              + ", ".join(ctx.sys(x) for x in stg["systems"]) + ".")
        doc.table(["Step", "Name", "Description"], [[x, W.steps[x]["name"], H.step_desc(ctx, x)] for x in stg["steps"]],
                  widths=[2.4, 4.6, 9.6], font_size=8.6)
        doc.p(pr.para(["opmodel", "arch"], n=(2, 3), svc=list(W.services.keys())))

    # 3 Principles ------------------------------------------------------------------
    doc.h(1, "3 Architecture principles", page_break=True)
    doc.p(pr.intro("the principles that every design decision in Claims Hub is tested against"))
    principles = [
        ("AP-01", "Migrate incrementally", "Replace CLARA capability by capability and region by region (ADR-001).",
         "Interfaces must support coexistence; CLARA remains system of record for unmigrated claims."),
        ("AP-02", "Events first", "State changes are published as domain events on the Event Streaming Platform (ADR-002).",
         "Consumers subscribe to events instead of reading another service's data."),
        ("AP-03", "Own your data", "Each service has its own PostgreSQL database (ADR-003).",
         "No shared schemas; reporting uses events and the Claims Data Warehouse."),
        ("AP-04", "Keep the mainframe stable", "CLARA interfaces stay on MQ until decommissioning (ADR-004).",
         "No new MQ flows originate from Claims Hub."),
        ("AP-05", "One platform", "All services run on OpenShift (ADR-006).", "Clusters ocp-prd-lon1 and ocp-dr-lds1."),
        ("AP-06", "Infrastructure as code", "Each service has its own Terraform module (ADR-007).",
         "Module path infra/terraform/modules/<service>."),
        ("AP-07", "Single identity", "Workforce and partner identity through the Corvane Identity Service (ADR-008).",
         "No local user stores in services or portals."),
        ("AP-08", "Configurable rules", "Business parameters are versioned configuration with effective dates.",
         "Threshold changes do not require code changes."),
        ("AP-09", "Observable by default", "Every service emits structured logs, metrics and traces.",
         "Operations can follow a claim across services."),
        ("AP-10", "Secure by design", "Least privilege and encryption in transit everywhere.",
         "Security controls are tested in the pipeline."),
        ("AP-11", "Reversible cut-over", "Each migration wave can be rolled back until sign-off.",
         "Reconciliation is designed in, not added later."),
        ("AP-12", "Business language", "Names in APIs and events follow the claims glossary.",
         "For example 'Claims Assessor' rather than adjuster."),
    ]
    doc.table(["ID", "Principle", "Statement", "Implications"], [list(p) for p in principles],
              widths=[1.4, 3.2, 6.0, 6.0], caption="Architecture principles", font_size=8.6)
    for pid, name, stmt, impl in principles:
        doc.h(2, f"3.{int(pid[3:])} {name}")
        doc.p(stmt + " " + impl)
        doc.ps(pr.paras(["arch", "governance", "integration"], 3, n=(3, 4), svc=list(W.services.keys())))

    # 4 Current state ---------------------------------------------------------------
    doc.h(1, "4 Current state: CLARA", page_break=True)
    clara = W.systems["SYS01"]
    progs = H.programs_asof(ctx)
    online = [p for p in progs if p["type"] == "online"]
    batch = [p for p in progs if p["type"] == "batch"]
    doc.p(f"CLARA (Claims Ledger And Reserve Application) went live on {long_date(clara['go_live'])}. It is written in "
          f"COBOL and runs under CICS with DB2 for z/OS, IBM MQ and JCL batch, hosted on {clara['hosting']}. The nightly "
          f"batch window runs {clara['batch_window']}.",
          facts=[F("general", "CLARA's batch window runs 23:30–05:30 UK time.", clara["batch_window"],
                   "SYSTEM:SYS01#batch_window"),
                 F("general", "CLARA is hosted on z/OS LPAR PRD1 in the Leeds Data Centre with DR on LPAR DRP1 in Bristol.",
                   "z/OS LPAR PRD1, Leeds Data Centre", "SYSTEM:SYS01#hosting")])
    doc.p(f"The current estate comprises {len(progs)} programs ({len(online)} online, {len(batch)} batch), "
          f"{sum(1 for t in W.tables.values() if t['db'] == 'DB2' and (not t.get('created') or t['created'] <= date))} DB2 tables and "
          f"{len(H.interfaces_asof(ctx))} catalogued interfaces. Its decommissioning target is "
          f"{long_date(clara['decommission_target'])}.")
    by_area = {}
    for p in progs:
        by_area.setdefault(p["area"], [0, 0])
        by_area[p["area"]][0 if p["type"] == "online" else 1] += 1
    doc.table(["Area", "Online programs", "Batch programs"], [[a, str(v[0]), str(v[1])] for a, v in sorted(by_area.items())],
              widths=[5, 4, 4], caption="CLARA programs by functional area")
    doc.figure(figs["context"], "CLARA current-state context (selected interfaces)",
               facts=[F("image_text", "Figure 1 labels the arrow from the MQ Backbone to the Group Ledger 'CLX-IF-043 GL reserve journals'.",
                        "CLX-IF-043 GL reserve journals", "INTERFACE:CLX-IF-043", where="image")])
    doc.h(2, "4.1 CLARA data stores")
    doc.p("CLARA stores claims data in DB2 tables under the CLR schema. The table below lists the tables in scope for "
          "replacement, grouped by functional area.")
    rows = []
    for tn, t in sorted(W.tables.items(), key=lambda kv: (kv[1]["area"], kv[0])):
        if t["db"] != "DB2" or (t.get("created") and t["created"] > date):
            continue
        rows.append([tn, t["area"], ctx.a(t["description"]), str(len(t["columns"]))])
    doc.table(["Table", "Area", "Description", "Columns"], rows, widths=[4.6, 2.2, 8.2, 1.6], font_size=8.2,
              caption="CLARA DB2 tables")
    doc.p(pr.para(["data", "governance"], n=3))
    doc.h(2, "4.2 Constraints of the current platform")
    doc.ps(pr.paras("bizcase", 2))
    doc.p("Reserve data is the most sensitive area of the current estate. Eight programs update CLR.T_RESERVE; "
          "movements are recorded in CLR.T_RESERVE_MOVEMENT and extracted nightly by CLRRS170 for the general ledger, "
          "the Claims Data Warehouse and reinsurance (CLX-IF-042 and its dependants).",
          facts=[F("general", "CLRRS170 extracts reserve movements nightly (CLX-IF-042) for GL, CDW and reinsurance.",
                   "extracted nightly by CLRRS170", "PROGRAM:CLRRS170")])
    doc.p(pr.para(["data", "integration"], n=3))

    # 5 Target architecture --------------------------------------------------------
    doc.h(1, "5 Target architecture", page_break=True)
    doc.h(2, "5.1 Overview")
    doc.p("Claims Hub is a set of thirteen Spring Boot services written in Java, each with its own PostgreSQL database, "
          "communicating through REST APIs for commands and queries and through Kafka topics for domain events. The "
          "services run on OpenShift and are provisioned with Terraform.")
    doc.figure(figs["target"], "Claims Hub target container view",
               alt=f"Container view: channels call fnol-intake-svc; services publish events to the Event Streaming "
                   f"Platform; {rsvc} publishes {ctx.a('reserve.changed.v2')} consumed by gl-posting-svc.",
               facts=[F("image_text", f"Figure 2 shows {rsvc} publishing reserve.changed.v1 to gl-posting-svc.",
                        ctx.a("reserve.changed.v2"), "SERVICE:reserve-engine#kafka_topics", where="image"),
                      F("alt_text", f"The container-view figure alt text says {rsvc} publishes reserve.changed.v1.",
                        f"{rsvc} publishes {ctx.a('reserve.changed.v2')}", "SERVICE:reserve-engine#renames", where="alt")])
    doc.ps(pr.paras(["arch", "integration"], 2, svc=list(W.services.keys())))
    doc.h(2, "5.2 Service catalogue")
    rows = []
    for name, s in W.services.items():
        own = H.svc_owner(ctx, name)
        rows.append([ctx.svc(name), H.svc_desc(ctx, name), ctx.team(own[0]) if own else "—",
                     str(len(s["replaces_programs"]))])
    doc.table(["Service", "Responsibility", "Owning squad", "CLARA programs replaced"], rows,
              widths=[3.4, 7.6, 4.0, 1.6], caption="Claims Hub services", font_size=8.4,
              facts=[PF(ctx, "ld13_reservesvc", rsvc, where=(5, 0),
                        notes="The service is called reserve-svc throughout this document (pre-2026-02-10 name).")])
    doc.p(pr.para("arch", n=3, svc=list(W.services.keys())))
    doc.h(2, "5.3 Service descriptions")
    for i, (name, s) in enumerate(W.services.items(), 1):
        nm = ctx.svc(name)
        doc.h(3, f"5.3.{i} {nm}")
        own = H.svc_owner(ctx, name)
        facts = []
        if name == "reserve-engine":
            facts.append(F("alias_use", "reserve-svc owns the case reserve aggregate (renamed reserve-engine in 2026).",
                           "reserve-svc owns the case reserve aggregate", "SERVICE:reserve-engine#renames"))
            doc.p(f"reserve-svc owns the case reserve aggregate: case reserves by reserve type, reserve movements, the "
                  f"Tier-3 review schedule, indexation of bodily-injury reserves and currency revaluation of Nordic "
                  f"reserves. It is the only Claims Hub component that writes reserves.", facts=facts)
        else:
            doc.p(f"{nm}: {H.svc_desc(ctx, name)}.")
        kv = [["Owning squad", f"{ctx.team(own[0])} (lead {ctx.name(own[1])})" if own else "—"],
              ["Namespace", s["k8s_namespace"]],
              ["Repository path", f"services/{nm}"],
              ["Terraform module", f"infra/terraform/modules/{nm}"],
              ["Data store", ", ".join(H.svc_tables(ctx, name)) or "—"],
              ["Publishes", ", ".join(H.topics_ok(ctx, s["kafka_topics"]["produces"])) or "—"],
              ["Consumes", ", ".join(H.topics_ok(ctx, s["kafka_topics"]["consumes"])) or "—"]]
        kfacts = []
        if name == "reserve-engine":
            kfacts.append(F("alias_use", "The reserve service Terraform module path was infra/terraform/modules/reserve-svc before the rename.",
                            "infra/terraform/modules/reserve-svc", "SERVICE:reserve-engine#path_history", where=(3, 1)))
            kfacts.append(F("general", "reserve-svc runs in OpenShift namespace chub-reserve.", "chub-reserve",
                            "SERVICE:reserve-engine#k8s_namespace", where=(1, 1)))
        if name == "fraud-referral-svc":
            kfacts.append(F("general", "fraud-referral-svc is owned by Hub Squad – Fraud & Settlement (lead Linnea Sjöberg).",
                            "Hub Squad – Fraud & Settlement (lead Linnea Sjöberg)", "SERVICE:fraud-referral-svc#owner_history",
                            where=(0, 1)))
        doc.kv(kv, widths=(4.0, 12.6), font_size=8.6, facts=kfacts)
        apis = H.svc_apis(ctx, name)
        if apis:
            doc.table(["Method", "Path", "Purpose"], [[a["method"], a["path"], a["summary"]] for a in apis],
                      widths=[1.8, 5.6, 9.2], font_size=8.6, caption=f"{nm} API operations")
        progs_r = [p for p in s["replaces_programs"] if str(W.programs[p]["since"]) <= date]
        resp = [f"Expose {a['method']} {a['path']} – {a['summary'][0].lower() + a['summary'][1:]}." for a in apis]
        resp += [f"Publish {t} when the corresponding state change is committed." for t in H.topics_ok(ctx, s["kafka_topics"]["produces"])]
        resp += [f"Consume {t} idempotently and record the offset processed." for t in H.topics_ok(ctx, s["kafka_topics"]["consumes"])]
        doc.p(f"Responsibilities of {nm}:", keep_next=True)
        doc.bullets(resp)
        doc.p(f"Legacy programs whose function moves to {nm}: " + ", ".join(progs_r) + ".")
        doc.table(["CLARA program", "Type", "Current function"],
                  [[p, W.programs[p]["type"], H.program_desc(ctx, p)] for p in progs_r],
                  widths=[2.6, 1.8, 12.2], font_size=8.4, caption=f"CLARA functions absorbed by {nm}")
        rl = H.rules_for_service(ctx, name)
        if rl:
            doc.table(["Rule", "Title", "Version in force"], [[r, t, f"v{v}"] for r, t, v in rl],
                      widths=[2.6, 11.4, 2.6], font_size=8.4, caption=f"Business rules implemented by {nm}")
        stp = H.steps_for_service(ctx, name)
        if stp:
            doc.p(f"Process steps supported: " + "; ".join(f"{x['id']} {x['name']}" for x in stp) + ".")
        doc.ps(pr.paras(["arch", "data", "security"], DENS, svc=nm))
    doc.h(2, "5.3.14 Key interaction flows")
    doc.figure(figs["fnol"], "FNOL and triage in the target (MVP scope)",
               facts=[F("image_text", "Figure 6 shows triage-svc handing the claim to claim-core-svc on triage.completed.v1.",
                        "triage.completed.v1", "TOPIC:triage.completed.v1", where="image")])
    doc.ps(pr.paras(["arch", "integration"], 2, svc=["fnol-intake-svc", "triage-svc", "claim-core-svc"]))
    doc.figure(figs["payments"], "Settlement and payment flow (target)")
    doc.ps(pr.paras(["arch", "integration", "security"], 2, svc=["settlement-svc", "payment-orchestrator"]))
    # 5.4 Event backbone
    doc.h(2, "5.4 Event backbone")
    doc.p("The Event Streaming Platform (Kafka on OpenShift, operated by Integration Platform) carries all Claims Hub "
          "domain events (ADR-002). Topics are owned by the producing service; consumers are registered in the topic "
          "catalogue and protected by schema compatibility checks.")
    ctx.need("TOPIC:claims.reserve.movement.v1", "retention_days")
    t = W.topics["claims.reserve.movement.v1"]
    doc.p(f"Reserve movements that still originate in CLARA during coexistence (CLX-IF-042) will be republished onto "
          f"topic claims.reserve.movement.v1 for {rsvc}; the topic keeps messages for {t['retention_days']} days, which "
          f"allows a full replay after a failed nightly run or a weekend outage.",
          facts=[PF(ctx, "ld13_retention", f"keeps messages for {t['retention_days']} days")])
    rows = []
    for tn, tp in W.topics.items():
        if tn in H.ALWAYS_EXCLUDED_TOPICS or tn in H.CIRCULAR_TOPICS:
            continue
        if not ctx.ok(f"TOPIC:{tn}"):
            continue
        prod = ctx.a(tp["producer"])
        if tn == "claims.reserve.movement.v1":
            prod = "Republication component (see 6.3)"
        rows.append([ctx.a(tn), prod, ", ".join(ctx.a(c) for c in tp["consumers"] if c != "fraud-referral-svc" or tn != "notification.fraud-notice.sent.v1")])
    doc.table(["Topic", "Producer", "Consumers"], rows, widths=[5.4, 4.8, 6.4], caption="Topic catalogue (target)",
              font_size=8.4)
    doc.p(pr.para(["integration", "arch"], n=4, svc=list(W.services.keys())))
    # 5.5 Data architecture
    doc.h(2, "5.5 Data architecture")
    doc.p("Each service owns a PostgreSQL 16 database. The tables below are the initial logical model; physical design is "
          "owned by the squads. Monetary amounts in events are carried with their currency.")
    for name, s in W.services.items():
        for tname in H.svc_tables(ctx, name):
            cols = H.table_columns(ctx, tname)
            doc.table(["Column", "Type", "Description"],
                      [[c["name"], c["type"] + (f"({c['length']})" if c.get("length") else ""), ctx.a(H.clean_desc(c["description"]))]
                       for c in cols], widths=[4.2, 3.0, 9.4], font_size=8.4,
                      caption=f"{tname} ({ctx.svc(name)})")
    doc.ps(pr.paras("data", 2))

    # 6 Integration ---------------------------------------------------------------
    doc.h(1, "6 Integration architecture", page_break=True)
    doc.h(2, "6.1 Principles")
    doc.ps(pr.paras("integration", 2))
    doc.h(2, "6.2 Interface catalogue")
    doc.p("The table lists the interfaces in the catalogue at the date of this document, with their status in the "
          "target. Schedules are shown as currently operated; batch interfaces driven by the CLARA nightly schedule are "
          "marked accordingly.")
    rows, facts = [], []
    for i in H.interfaces_asof(ctx, include_planned=True):
        iid = i["id"]
        if iid == "CLX-IF-049":
            continue
        if date < "2025-11-20" and "NISA-FR1" in (i.get("feeds_reports") or []):
            continue   # the NISA-FR1 return exists only from Circular 2026/04 (published 2025-11-20)
        live = str(i["since"]) <= date
        sch = H.iface_schedule(ctx, iid) or "per CLARA batch schedule"
        rows.append([iid, ctx.a(i["name"]), ctx.sys(i["source_system"]), ctx.sys(i["target_system"]), sch,
                     "Live" if live else "Planned (target)"])
        if iid == "CLX-IF-043":
            facts.append(PF(ctx, "ld13_043", "daily 03:00", where=(len(rows), 4)))
            facts.append(F("general", "CLX-IF-043 is the GL Reserve Journal Feed from the MQ Backbone to the Group Ledger.",
                           "GL Reserve Journal Feed", "INTERFACE:CLX-IF-043#name", where=(len(rows), 1)))
        if iid == "CLX-IF-044":
            facts.append(F("general", "CLX-IF-044 CDW Reserve Fact Load runs daily 04:00.", "daily 04:00",
                           "INTERFACE:CLX-IF-044#schedule", where=(len(rows), 4)))
        if iid == "CLX-IF-047":
            facts.append(F("general", "CLX-IF-047 Reserve Cession Feed runs daily 04:15.", "daily 04:15",
                           "INTERFACE:CLX-IF-047#schedule", where=(len(rows), 4)))
    doc.table(["ID", "Name", "Source", "Target", "Schedule", "Status"], rows, widths=[2.0, 4.6, 2.9, 2.9, 2.6, 1.6],
              caption="Interface catalogue (extract)", font_size=7.8, facts=facts)
    doc.p(pr.para("integration", n=4))
    groups = [("FNOL and triage interfaces", ["CLX-IF-001", "CLX-IF-002", "CLX-IF-003", "CLX-IF-004", "CLX-IF-006", "CLX-IF-007", "CLX-IF-008", "CLX-IF-009", "CLX-IF-010"]),
              ("Assessment and vendor interfaces", ["CLX-IF-013", "CLX-IF-014", "CLX-IF-015", "CLX-IF-016", "CLX-IF-024"]),
              ("Fraud interfaces", ["CLX-IF-011", "CLX-IF-012"]),
              ("Payment interfaces", ["CLX-IF-017", "CLX-IF-018", "CLX-IF-019", "CLX-IF-020", "CLX-IF-021"]),
              ("Recovery interfaces", ["CLX-IF-022", "CLX-IF-023", "CLX-IF-025", "CLX-IF-026"]),
              ("Finance, reinsurance and reporting interfaces", ["CLX-IF-027", "CLX-IF-028", "CLX-IF-029", "CLX-IF-030", "CLX-IF-031", "CLX-IF-032", "CLX-IF-046", "CLX-IF-048", "CLX-IF-051", "CLX-IF-052", "CLX-IF-055", "CLX-IF-058"])]
    for gi, (gname, ids) in enumerate(groups, 1):
        doc.h(3, f"6.2.{gi} {gname}")
        rows = []
        for iid in ids:
            i = W.interfaces[iid]
            if str(i["since"]) > date:
                continue
            rows.append([iid, ctx.a(i["format"]), i["criticality"], H.owner_name(ctx, i["owner"]), i["avg_daily_volume"]])
        doc.table(["ID", "Transport and format", "Criticality", "Owner", "Typical volume"], rows,
                  widths=[2.0, 6.4, 2.0, 3.4, 2.8], font_size=8.0)
        doc.ps(pr.paras("integration", 2, n=(3, 4)))
    doc.h(2, "6.3 Reserve synchronisation during coexistence")
    doc.p(f"While CLARA remains the system of record for unmigrated claims, {rsvc} must hold an accurate copy of CLARA "
          f"reserves to support the reserve parallel run and the later migration waves. CLARA reserve movements are "
          f"extracted by CLRRS170 (CLX-IF-042) and placed on the MQ Backbone, where the general ledger (CLX-IF-043), "
          f"the Claims Data Warehouse (CLX-IF-044) and reinsurance (CLX-IF-047) consume them today.")
    doc.figure(figs["reserve"], "Reserve synchronisation during coexistence",
               alt="CLRRS170 writes CLX-IF-042 records to the MQ Backbone; a republication component publishes them to "
                   f"claims.reserve.movement.v1; {rsvc} consumes the topic for the parallel-run comparison.",
               facts=[F("image_text", "Figure 3 shows CLX-IF-042 RSVMOVE records flowing from CLARA (CLRRS170) to the MQ Backbone.",
                        "CLX-IF-042 RSVMOVE records", "INTERFACE:CLX-IF-042", where="image")])
    doc.p("The mechanism that republishes these movements onto the event backbone is an open item (OI-07). Two options "
          "are under assessment: change data capture on the DB2 movement table, or republication of the existing "
          "extract. The Design Authority will decide between them before the reserve squad starts build.")
    doc.ps(pr.paras(["integration", "data"], 2))
    doc.h(2, "6.4 External parties")
    ext = [["Brynholt Re / Calderbank Re", "Bordereaux through the Bordereaux Exchange", "CLX-IF-055"],
           ["Northmere Clearing Bank", "Payments through the Corvane Payments Gateway", "CLX-IF-019, CLX-IF-021"],
           ["Panel Claims Assessors", "Instructions and reports through the " + ctx.sys("SYS17"), "CLX-IF-013, CLX-IF-014"],
           ["NISA", "Regulatory returns through the NISA Reporting Hub", "CLX-IF-032, CLX-IF-051"]]
    if not ctx.ok("VENDOR:VEN-12", "role"):
        ext[0][0] = "Treaty reinsurers"
    doc.table(["Party", "Exchange", "Interfaces"], ext, widths=[5.0, 7.6, 4.0], caption="External parties")

    # 7 Deployment ---------------------------------------------------------------
    doc.h(1, "7 Deployment and infrastructure", page_break=True)
    doc.p(f"Claims Hub runs on the Corvane private cloud on OpenShift: cluster ocp-prd-lon1 in London is primary and "
          f"ocp-dr-lds1 in Leeds provides disaster recovery (ADR-006). The Event Streaming Platform runs on the same "
          f"cluster with the Strimzi operator.",
          facts=[F("general", "Claims Hub clusters: ocp-prd-lon1 (London, primary) and ocp-dr-lds1 (Leeds, DR).",
                   "ocp-prd-lon1 in London is primary and ocp-dr-lds1 in Leeds provides disaster recovery", "ADR:ADR-006")])
    doc.figure(figs["deploy"], "Deployment view")
    rows = [[ctx.svc(n), s["k8s_namespace"], str(s["replicas"]), f"infra/terraform/modules/{ctx.svc(n)}"]
            for n, s in W.services.items()]
    doc.table(["Service", "Namespace", "Production replicas (initial)", "Terraform module"], rows,
              widths=[3.8, 3.0, 2.8, 7.0], caption="Service deployment parameters", font_size=8.4)
    doc.ps(pr.paras(["arch", "governance"], 2, svc=list(W.services.keys())))
    doc.h(2, "7.1 Environments")
    envs = [["DEV", "Squad development and unit testing", "Synthetic data"],
            ["SIT", "System integration testing with CLARA test regions", "Synthetic and masked data"],
            ["UAT", "Business acceptance and migration rehearsals", "Masked data"],
            ["PRE", "Pre-production, performance and operational acceptance", "Masked data"],
            ["PRD", "Production (ocp-prd-lon1) with DR (ocp-dr-lds1)", "Production data"]]
    doc.table(["Environment", "Purpose", "Data"], envs, widths=[2.6, 9.0, 5.0], caption="Environments")
    doc.p(pr.para(["test", "security"], n=3))

    # 8 Security ---------------------------------------------------------------
    doc.h(1, "8 Security and identity")
    doc.p(f"Workforce and partner users sign in through the {ctx.sys('SYS16')} using OpenID Connect (ADR-008). The "
          f"Claims Hub workbench and the {ctx.sys('SYS17')} receive tokens from the identity service; services validate "
          f"bearer tokens and apply role-based authorisation.")
    doc.figure(figs["identity"], "Workforce and partner sign-in")
    doc.ps(pr.paras("security", 3))

    # 9 NFRs ---------------------------------------------------------------------
    doc.h(1, "9 Non-functional requirements")
    nfr = [["NFR-01", "Availability", "Business-critical services are deployed across failure domains and fail over to the DR cluster."],
           ["NFR-02", "Recoverability", "Every service can be redeployed from the pipeline; databases are backed up and restorable."],
           ["NFR-03", "Performance", "Interactive operations meet the response targets agreed with the product owner."],
           ["NFR-04", "Scalability", "Services scale horizontally; topic partitioning supports parallel consumers."],
           ["NFR-05", "Auditability", "Every change to a claim, reserve or payment is attributable and retained."],
           ["NFR-06", "Operability", "Dashboards and alerts exist for every service before go-live."],
           ["NFR-07", "Security", "Controls in section 8 are tested in the pipeline and in penetration tests."],
           ["NFR-08", "Data protection", "Personal data is minimised and classified at field level."],
           ["NFR-09", "Maintainability", "Services are independently deployable and versioned."],
           ["NFR-10", "Accessibility", "User interfaces meet the Corvane accessibility standard."]]
    doc.table(["ID", "Quality", "Requirement"], nfr, widths=[1.8, 3.2, 11.6], caption="Non-functional requirements")
    for row in nfr:
        doc.h(2, f"9.{int(row[0][4:])} {row[1]}")
        doc.ps(pr.paras(["arch", "security", "test"], 2, n=(2, 4), svc=list(W.services.keys())))
    doc.h(2, "9.11 Technology standards")
    tech = [["Runtime", W.systems["SYS02"]["tech"]], ["Messaging (mainframe)", W.systems["SYS14"]["tech"]],
            ["Event streaming", W.systems["SYS15"]["tech"]], ["Identity", W.systems["SYS16"]["tech"]],
            ["Legacy platform", W.systems["SYS01"]["tech"].replace(" (subsystem DB2P)", "")],
            ["Infrastructure as code", "Terraform, one module per service (ADR-007)"],
            ["Container platform", "OpenShift (ADR-006)"]]
    doc.table(["Area", "Standard"], tech, widths=[4.6, 12.0], caption="Technology standards")

    # 10 Transition ---------------------------------------------------------------
    doc.h(1, "10 Transition architecture", page_break=True)
    doc.p("Migration follows the strangler-fig approach agreed in ADR-001: capabilities move to Claims Hub in waves, by "
          "capability and by region, while CLARA remains the system of record for claims that have not yet migrated. "
          f"CLARA's decommissioning target is {long_date(W.systems['SYS01']['decommission_target'])}.")
    doc.p("The first release (minimum viable product) covers FNOL and triage for digital channels, with claims created "
          "in Claims Hub and handed to CLARA for the remaining stages. Later releases add reserving, fraud referral, "
          "settlement, payments and recoveries before claims are migrated region by region.")
    doc.ps(pr.paras(["migration", "integration"], 3))

    # 11 Risks -------------------------------------------------------------------
    doc.h(1, "11 Risks, issues and open items")
    oi = [["OI-03", "Treatment of Nordic currency in reserve events", "Open", ctx.name("P053")],
          ["OI-05", "Read-only access to CLARA after cut-over for historic enquiries", "Open", ctx.name("P016")],
          ["OI-07", "Republication of CLX-IF-042 reserve movements onto the event backbone (CDC or batch)", "Open",
           ctx.name("P050")],
          ["OI-09", "Sentinel scoring pattern from Claims Hub (synchronous or batch)", "Open", ctx.name("P049")],
          ["OI-11", "Retirement path for SUBTRAK once recovery-svc is live", "Open", ctx.name("P014")]]
    doc.table(["ID", "Item", "Status", "Action owner"], oi, widths=[1.6, 9.6, 1.8, 3.6], caption="Open items",
              facts=[F("general", "Open item OI-07 covers how CLX-IF-042 reserve movements are republished to the event backbone.",
                       "Republication of CLX-IF-042 reserve movements onto the event backbone", "INTERFACE:CLX-IF-042",
                       where=(3, 1))])
    doc.ps(pr.paras(["governance", "bizcase"], 2))

    # 11b Rules -------------------------------------------------------------------
    doc.h(1, "12 Business rules as configuration", page_break=True)
    doc.p("Business rules are implemented as versioned configuration with effective dates rather than code. The table "
          "lists the rules in force at the date of this document and the services that will implement them in Claims "
          "Hub. Rule parameters are held in the rules catalogue and are not repeated here.")
    rows = []
    for rid, r in W.rules.items():
        v = ctx.rule(rid)
        if not v:
            continue
        svcs = ", ".join(ctx.svc(x) for x in (r.get("implemented_in", {}) or {}).get("services", []))
        rows.append([rid, r["title"], f"v{v['version']}", svcs or "—"])
    doc.table(["Rule", "Title", "Version", "Target services"], rows, widths=[2.4, 7.4, 1.6, 5.2], font_size=7.8,
              caption="Rules in force and their target services")
    doc.ps(pr.paras(["arch", "governance"], 2))
    doc.h(1, "13 Reference data")
    rows = [[p_["code"], p_["name"], p_["line"], p_["currency"]] for p_ in W.products.values()]
    doc.table(["Code", "Product", "Line", "Currency"], rows, widths=[2.4, 6.6, 4.4, 3.2], caption="Products")
    rows = [[c["peril_code"], c["name"], ", ".join(c["lines_of_business"]), ", ".join(f"{k}: {v}" for k, v in c["local_names"].items()) or "—"]
            for c in W.claim_types.values()]
    doc.table(["Peril code", "Claim type", "Lines of business", "Local names"], rows, widths=[2.0, 4.2, 4.6, 5.8],
              caption="Claim types (perils)", font_size=8.2)
    rows = [[l_["name"], l_["city"], l_["type"], H.org_asof(ctx, ", ".join(l_["functions"])) or "—"] for l_ in W.locations.values()
            if l_["type"] in ("office", "data_centre")]
    doc.table(["Location", "City", "Type", "Functions"], rows, widths=[4.6, 2.4, 2.2, 7.4], caption="Locations",
              font_size=8.2)
    doc.ps(pr.paras("data", 2))
    doc.h(1, "14 Stakeholders")
    pids = ["P003", "P004", "P006", "P005", "P002", "P007", "P011", "P009", "P010", "P008", "P016", "P017", "P018",
            "P031", "P032", "P036", "P019", "P040", "P041", "P042", "P047", "P048", "P049", "P050", "P051", "P052",
            "P053", "P054"]
    rows = [[ctx.name(x), ctx.title(x), ctx.team(W.team_of(x, date)) if W.team_of(x, date) else "—"] for x in pids
            if ctx.employed(x)]
    doc.table(["Name", "Title", "Team"], rows, widths=[4.2, 7.0, 5.4], caption="Key stakeholders at the date of this document",
              font_size=8.4,
              facts=[F("temporal", "At 2025-03-03 the Claims Director is Ingrid Sørensen (name before 2025-08-23).",
                       "Ingrid Sørensen", "PERSON:P005#name_history", where=(4, 0)),
                     F("temporal", "At 2025-03-03 the CFO is Gareth Whitcombe.", "Gareth Whitcombe", "PERSON:P002#role_aliases",
                       where=(5, 0))])
    # 12 Operations ---------------------------------------------------------------
    doc.h(1, "15 Operations and support model", page_break=True)
    doc.p("Claims Hub services are supported by the owning squads in business hours and by the Technology Delivery "
          "Office on-call rota out of hours. Integration Platform supports the Event Streaming Platform and the MQ "
          "Backbone; Legacy Claims Platforms continues to support CLARA and its batch schedule.")
    sup = [["Level 1", "Service desk", "Triage of user-reported incidents and routing to the owning team"],
           ["Level 2", "Owning squad / " + ctx.team("T20"), "Diagnosis and resolution of application incidents"],
           ["Level 2", ctx.team("T22"), "Event Streaming Platform, MQ Backbone and interface monitoring"],
           ["Level 2", ctx.team("T25"), "CLARA batch scheduling and restarts"],
           ["Level 3", "Vendors and platform engineering", "Product defects and platform faults"]]
    doc.table(["Level", "Team", "Responsibility"], sup, widths=[2.0, 5.6, 9.0], caption="Support model")
    for t in ("Monitoring and alerting", "Release and change", "Capacity management", "Problem management"):
        doc.h(2, f"15.{['Monitoring and alerting', 'Release and change', 'Capacity management', 'Problem management'].index(t) + 1} {t}")
        doc.ps(pr.paras(["arch", "ops", "governance"], 2, svc=list(W.services.keys())))
    doc.h(1, "16 Reporting and regulatory returns")
    doc.p("Regulatory returns continue to be produced by the NISA Reporting Hub. During coexistence the Hub sources "
          "CLARA data through the existing extracts; reporting-feed-svc will take over the Claims Hub share once "
          "regulatory extracts from the new platform have been validated.")
    rows = []
    for rid in ("NISA-TP2", "NISA-CT1", "NISA-AFR"):
        r = W.reports[rid]
        rows.append([rid, r["name"], r["frequency"], r["due"], r["signed_by_role"]])
    doc.table(["Return", "Name", "Frequency", "Due", "Signed by"], rows, widths=[2.2, 5.0, 2.2, 3.8, 3.4],
              caption="Regulatory returns supported by claims data",
              facts=[F("general", "The NISA-TP2 return is due 35 calendar days after quarter end and signed by the CFO.",
                       "35 calendar days after quarter end", "REPORT:NISA-TP2#due", where=(1, 3))])
    doc.ps(pr.paras(["data", "integration"], 2))

    # Appendices -----------------------------------------------------------------
    doc.h(1, "Appendix A – CLARA programs and their target services", page_break=True)
    rows = []
    owner_by_prog = {}
    for name, s in W.services.items():
        for p in s["replaces_programs"]:
            owner_by_prog[p] = ctx.svc(name)
    for p in progs:
        rows.append([p["id"], p["type"], H.program_desc(ctx, p["id"]), owner_by_prog.get(p["id"], "Retained until decommissioning")])
    doc.table(["Program", "Type", "Description", "Target service"], rows, widths=[2.2, 1.6, 8.8, 4.0],
              caption="Program-to-service mapping", font_size=8.0,
              facts=[F("alias_use", "CLRGL090 (year-end reserve revaluation) moves to reserve-svc.", "Year-end reserve currency revaluation",
                       "SERVICE:reserve-engine#replaces_programs", where=(next(i for i, r in enumerate(rows, 1) if r[0] == "CLRGL090"), 2))])
    doc.h(1, "Appendix B – Interface dependencies")
    rows = []
    for i in H.interfaces_asof(ctx):
        if not i.get("depends_on") and not i.get("dependents"):
            continue
        deps = [d_ for d_ in i.get("dependents", []) if str(W.interfaces[d_]["since"]) <= date]
        rows.append([i["id"], ctx.a(i["name"]), ", ".join(i.get("depends_on") or []) or "—", ", ".join(deps) or "—"])
    doc.table(["Interface", "Name", "Depends on", "Dependants"], rows, widths=[2.2, 6.4, 4.0, 4.0], font_size=8.2,
              caption="Upstream and downstream interface dependencies (live interfaces)",
              facts=[F("general", "CLX-IF-042's live dependants include CLX-IF-043, CLX-IF-044 and CLX-IF-047.",
                       "CLX-IF-043, CLX-IF-044, CLX-IF-047", "INTERFACE:CLX-IF-042#dependents",
                       where=(next(k for k, r in enumerate(rows, 1) if r[0] == "CLX-IF-042"), 3))])
    doc.h(1, "Appendix C – Process traceability")
    rows = []
    for sid_, st in W.steps.items():
        rows.append([sid_, st["name"], W.stages[st["stage"]]["name"], ", ".join(ctx.svc(x) for x in st["services"]),
                     ", ".join(p for p in st["programs"] if str(W.programs[p]["since"]) <= date)])
    doc.table(["Step", "Name", "Stage", "Target services", "CLARA programs"], rows, widths=[2.2, 4.2, 3.2, 3.8, 3.2],
              font_size=8.0, caption="Process steps, target services and current programs")
    doc.h(1, "Appendix D – API operation summaries", page_break=True)
    doc.p("The summaries below are indicative and are refined in each service's published API contract. Field lists "
          "are drawn from the logical data model in section 5.5.")
    errors = "400 invalid request; 401 not authenticated; 403 not authorised; 404 not found; 409 conflicting state"
    for name, s_ in W.services.items():
        nm = ctx.svc(name)
        tabs = H.svc_tables(ctx, name)
        fields = [c["name"] for c in H.table_columns(ctx, tabs[0])] if tabs else []
        doc.h(2, f"D.{list(W.services).index(name) + 1} {nm}")
        for a in H.svc_apis(ctx, name):
            body = ", ".join(fields[:7]) if fields else "—"
            doc.kv([["Operation", f"{a['method']} {a['path']}"], ["Purpose", a["summary"]],
                    ["Request", "Path parameters and a JSON body" if a["method"] in ("POST", "PATCH") else "Path parameters only"],
                    ["Response elements", body], ["Errors", errors],
                    ["Authorisation", "Role-based, from the access token issued by the identity service"]],
                   widths=(3.6, 13.0), font_size=8.2)
        doc.p(pr.para(["arch", "security"], n=(2, 3), svc=nm))
    doc.h(1, "Appendix E – Event summaries", page_break=True)
    for tn, tp in W.topics.items():
        if tn in H.ALWAYS_EXCLUDED_TOPICS or tn in H.CIRCULAR_TOPICS or not ctx.ok(f"TOPIC:{tn}"):
            continue
        prod = ctx.a(tp["producer"]) if tn != "claims.reserve.movement.v1" else "Republication component (see 6.3)"
        doc.h(2, f"E.{ctx.a(tn)}")
        doc.kv([["Topic", ctx.a(tn)], ["Producer", prod], ["Consumers", ", ".join(ctx.a(c) for c in tp["consumers"])],
                ["Cluster", tp["cluster"]], ["Delivery", "At least once; consumers de-duplicate on the event identifier"]],
               widths=(3.6, 13.0), font_size=8.2)
        doc.p(pr.para(["integration"], n=(2, 3)))
    doc.h(1, "Appendix F – Glossary")
    terms = C.glossary_terms([g for g in W.glossary if g not in ("G-012", "G-021")])
    terms = [(t, H.org_asof(ctx, ctx.a(m))) for t, m in terms]
    doc.table(["Term", "Meaning"], [list(t) for t in terms], widths=[4.6, 12.0], font_size=8.8)
    return doc

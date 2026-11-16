"""LD019 – Claims Hub Test Strategy (DOCX, 2026-01-15, Nadia Petrovic, approved)."""
from __future__ import annotations

from . import common as C
from . import hub as H
from .core import Ctx, Doc, F, PF, Style, W, long_date, short_date, util
from .prose import Prose

FID = "LD019"

PHASES = [
    # (phase, owner team, environment, entry, exit)
    ("Unit testing", "T27", "Developer workstation and build pipeline",
     "Code compiles; static analysis clean", "Agreed coverage reached; no failing tests in the pipeline"),
    ("Component testing", "T28", "Build pipeline (ephemeral namespace)",
     "Unit tests passing; stubs for dependencies available", "All component scenarios passed or deferred with approval"),
    ("Contract testing", "T22", "Build pipeline",
     "Producer and consumer contracts published", "No breaking change detected for any registered consumer"),
    ("System integration testing", "T29", "SIT",
     "Component and contract tests passed; SIT refreshed", "Integration scenarios passed; no open Sev1/Sev2 defects"),
    ("End-to-end testing", "T21", "Pre-production",
     "SIT exit met; reference data loaded", "Business journeys passed across both platforms"),
    ("Performance testing", "T28", "Performance environment",
     "Functionally stable build; volume model agreed", "Response-time and throughput targets met at peak volume"),
    ("Security testing", "T24", "Pre-production",
     "Release candidate deployed; threat model reviewed", "No open critical or high findings"),
    ("Operational acceptance testing", "T22", "Pre-production",
     "Runbooks and dashboards drafted", "Support teams have operated, monitored and recovered the service"),
    ("User acceptance testing", "T02", "UAT",
     "End-to-end exit met; test users trained", "Business sign-off by the stage owners"),
    ("Regulatory requirement testing", "T18", "UAT",
     "Requirements traced to tests", "Compliance review of evidence completed"),
    ("Migration rehearsal", "T26", "Migration rehearsal environment",
     "Mapping specification baselined; masked extract available", "Reconciliation within the tolerances of the migration strategy"),
    ("Reserve parallel run", "T12", "Production (read-only comparison)",
     "Reserve rules accepted in UAT; reconciliation job deployed", "Variance criteria in section 4.3 met for the agreed period"),
    ("Post-go-live verification", "T02", "Production",
     "Cut-over completed", "Business verification checklist signed off"),
]

SEVERITY = [
    ("Sev1 – Critical", "Prevents a business process from being performed or corrupts claim, reserve or payment data; no workaround.",
     "Immediate; fix or rollback before testing continues"),
    ("Sev2 – High", "Major function fails or produces wrong results; a workaround exists but is not sustainable.",
     "Fix in the current iteration"),
    ("Sev3 – Medium", "Function works with minor errors or inconvenience; workaround is acceptable.",
     "Fix in a planned release"),
    ("Sev4 – Low", "Cosmetic or documentation issue with no business impact.", "Fix when convenient"),
]


def build() -> Doc:
    ctx = Ctx(FID)
    date = ctx.date
    pr = Prose(util.rng(f"{FID}:prose"), date=ctx.date)
    doc = Doc(ctx, title="Claims Hub Test Strategy", doc_id="SKR-TST-001", version="1.0", status="Approved",
              subtitle="Programme Skerry – test, migration rehearsal and parallel-run strategy",
              style=Style(font="Calibri", heading_font="Calibri", accent="7B2C3B", accent2="F2DCDB", size=10.5),
              header_left="Programme Skerry – Claims Hub Test Strategy", header_right="SKR-TST-001 v1.0")
    doc.title_page(C.control_rows(ctx, doc, owner="P017", extra=[["Programme", "Programme Skerry"],
                                                                  ["Delivery partner", "IBM Consulting"]]))
    C.version_history(ctx, doc, [("0.1", 120, "Outline for the MVP release"),
                                 ("0.5", 62, "Phases, environments and defect management added after the MVP"),
                                 ("0.9", 14, "Reserve parallel-run approach and migration rehearsals added for review"),
                                 ("1.0", 0, "Approved")],
                      authors=["P053", "P053", "P053", "P053"])
    C.approvals(ctx, doc, [("P017", "Business owner"), ("P032", "Technology delivery"), ("P009", "Reserving sign-off"),
                           ("P048", "Delivery partner")])
    C.reviewers(ctx, doc, ["P040", "P041", "P042", "P051", "P049", "P016", "P026", "P037"])
    doc.toc(depth=2)

    # 1 -------------------------------------------------------------------------------
    doc.h(1, "1 Introduction")
    doc.p("This strategy sets out how Claims Hub and the changes made to CLARA and its interfaces will be tested during "
          "Programme Skerry. It applies to every release from the date of approval until CLARA is decommissioned, and "
          "covers functional and non-functional testing, data migration rehearsals and the reserve parallel run.")
    doc.ps(pr.paras(["test2", "intro"], 2, topic="the test strategy"))
    doc.h(2, "1.1 Scope")
    doc.bullets(["The thirteen Claims Hub services and their APIs, events and databases.",
                 "Changes to CLARA programs, batch jobs and interfaces made to support the migration.",
                 "Interfaces between Claims Hub and the surrounding systems.",
                 "Data migration for each wave, including rehearsals and reconciliation.",
                 "The reserve parallel run comparing CLARA with the Claims Hub reserve service.",
                 "Operational readiness of the support teams for each release."])
    doc.h(2, "1.2 Out of scope")
    doc.bullets(["Testing of vendor products beyond their integration with Corvane systems.",
                 "Business process changes that do not involve a system change.",
                 "Infrastructure testing of the OpenShift platform itself, which is covered by the platform team's own plan."])
    doc.h(2, "1.3 Reference documents")
    doc.table(["Document", "Reference"],
              [["Claims Hub Target Architecture", "v1.0"], ["Data Migration Strategy", "approved"],
               ["Fraud referral BRD (NISA Circular 2026/04)", "in preparation"],
               ["Architecture decision records", "ADR-001 to ADR-030"],
               ["Release and environment plan", "maintained by the Technology Delivery Office"]],
              widths=[9.0, 7.6], caption="Reference documents")
    doc.ps(pr.paras(["governance"], 1))

    # 2 -------------------------------------------------------------------------------
    doc.h(1, "2 Test principles and approach", page_break=True)
    doc.ps(pr.paras(["test", "test2"], 3))
    doc.h(2, "2.1 Principles")
    doc.bullets(["Quality is owned by the squads; independent assurance is provided by the test lead and the business.",
                 "Test early: requirements and contracts are reviewed for testability before build starts.",
                 "Automate what will be repeated; keep manual testing for exploration and business judgement.",
                 "Test against risk: depth of testing follows the impact of failure on customers, reserves and regulatory reporting.",
                 "Compare, do not assume: wherever CLARA and Claims Hub both produce a result, the results are reconciled.",
                 "Evidence everything: every test result is traceable to a requirement, a build and an environment."])
    doc.h(2, "2.2 Risk-based prioritisation")
    doc.p(pr.para(["test2"], n=(3, 4)))
    doc.table(["Risk area", "Why it matters", "Test emphasis"],
              [["Reserves", "Reserves feed the general ledger, reinsurance and regulatory returns.",
                "Rule decision tables, reconciliation with CLARA, the reserve parallel run"],
               ["Fraud referral", "Regulatory change under NISA Circular 2026/04 and customer impact.",
                "Decision tables, notice deadlines, end-to-end SIU hand-off"],
               ["Payments", "Financial loss and customer harm if payments are duplicated or missed.",
                "Idempotency, sanctions screening, reconciliation with the payments gateway"],
               ["Interfaces", "Downstream consumers depend on stable layouts and schedules.",
                "Contract tests, consumer sign-off of changes, end-to-end runs"],
               ["Data migration", "Errors become customer-facing at cut-over.",
                "Rehearsals with full reconciliation, business verification samples"],
               ["Performance", "Peak volumes after severe weather.", "Load tests at peak and stress tests beyond it"]],
              widths=[3.0, 6.2, 7.4], caption="Risk areas and test emphasis", font_size=8.6)
    doc.h(2, "2.3 The test pyramid")
    doc.ps(pr.paras(["test2"], 2))

    # 3 -------------------------------------------------------------------------------
    doc.h(1, "3 Test phases", page_break=True)
    doc.p("The table summarises each test phase. Detailed entry and exit criteria are confirmed in the test plan for "
          "each release.")
    doc.table(["Phase", "Owner", "Environment", "Entry criteria", "Exit criteria"],
              [[p, ctx.team(t), env, en, ex] for p, t, env, en, ex in PHASES],
              widths=[3.0, 2.8, 2.8, 4.0, 4.0], caption="Test phase summary", font_size=8.0)
    for k, (p, t, env, en, ex) in enumerate(PHASES, 1):
        doc.h(2, f"3.{k} {p}")
        doc.p(f"Owner: {ctx.team(t)}. Environment: {env}.")
        doc.p(pr.para(["phase", "test2"], n=(3, 5), phase=p.lower()))
        doc.p(pr.para(["test", "test2"], n=(2, 4)))
        doc.p(pr.para(["phase", "test2", "test"], n=(3, 4), phase=p.lower()))
        doc.table(["Deliverable", "Produced by", "Approved by"],
                  [[f"{p} plan for the release", ctx.team(t), "Test lead"],
                   [f"{p} cases and scripts", ctx.team(t), "Peer review"],
                   [f"{p} exit report", ctx.team(t), "Release readiness review"]],
                  widths=[7.6, 4.6, 4.4], font_size=8.4)

    # 4 Reserve testing --------------------------------------------------------------------
    doc.h(1, "4 Reserve testing and the parallel run", page_break=True)
    svc = ctx.svc("reserve-engine")
    doc.p(f"Reserves are the highest-risk area of the migration. The {svc} service takes over the calculation of case "
          f"reserves, reserve movements, Tier-3 review scheduling, indexation and currency revaluation from CLARA. "
          f"Because reserves feed the general ledger, reinsurance cessions and the NISA returns, the reserve logic is "
          f"tested in three layers: rule-level decision tables, reconciliation of migrated reserves, and a parallel run "
          f"in which both platforms calculate reserves for the same claims.")
    doc.h(2, "4.1 Reserve rules under test")
    rows = []
    for rid, r in W.rules.items():
        if not rid.startswith("BR-RSV-"):
            continue
        v = ctx.rule(rid)
        if not v:
            continue
        rows.append([rid, f"v{v['version']}", r["title"], ", ".join(ctx.a(s) for s in (r.get("implemented_in", {}) or {}).get("services", [])) or "—"])
    doc.table(["Rule", "Version", "Title", "Implemented in"], rows, widths=[2.4, 1.6, 8.2, 4.4],
              caption="Reserving rules in force at the date of this strategy", font_size=8.4)
    doc.p(pr.para(["test2"], n=(2, 3)))
    doc.h(2, "4.2 Reconciliation of migrated reserves")
    doc.p("For each migration wave, the outstanding reserve of every migrated claim is compared with the CLARA value at "
          "the cut-over point. The tolerances and the treatment of exceptions are defined in the Data Migration Strategy "
          "and are not repeated here.")
    doc.ps(pr.paras(["migration", "test2"], 2))
    doc.h(2, "4.3 Parallel run")
    pr_ = W.timeline["programme"]["parallel_run"]
    tol = pr_["variance_tolerance_pct_per_product_per_day"]
    ctx.need("TIMELINE:programme", "parallel_run.variance_tolerance_pct_per_product_per_day")
    run_txt = f"The reserve parallel run will take place from {long_date(pr_['from'])} to {long_date(pr_['to'])}"
    doc.p(f"{run_txt}. During this period CLARA remains the system of record and {svc} calculates reserves for the same "
          f"claims from the reserve movement events it receives. A daily reconciliation compares the two results by product.",
          facts=[F("general", f"The reserve parallel run runs from {pr_['from']} to {pr_['to']} with CLARA as system of record.",
                   run_txt, "TIMELINE:programme#parallel_run")])
    doc.p(f"The variance tolerance is {tol}% per product per day: for each product, the absolute difference between the "
          f"total outstanding reserve calculated by {svc} and the CLARA total for the same business date must not "
          f"exceed {tol}% of the CLARA total.",
          facts=[PF(ctx, "ld19_pr_tol", f"{tol}% per product per day",
                    notes="§4.3 Parallel run; run dates in the preceding paragraph.")])
    doc.p("A product that breaches the tolerance on any day is investigated before the next daily run. The causes are "
          "classified as rule differences, data differences, timing differences or defects, and each is tracked to "
          "closure in the defect log.")
    doc.table(["Measure", "How it is calculated", "Reviewed by"],
              [["Daily product variance", "Absolute difference between the two totals divided by the CLARA total, per product", ctx.team("T12")],
               ["Claim-level breaks", "Claims whose outstanding reserve differs between the platforms", ctx.team("T28")],
               ["Movement completeness", "Movements in CLARA without a corresponding event in the Hub", ctx.team("T22")],
               ["Review scheduling", "Tier-3 claims whose next review date differs between the platforms", ctx.team("T12")]],
              widths=[3.8, 8.4, 4.4], caption="Parallel-run measures", font_size=8.6)
    doc.ps(pr.paras(["test2", "migration"], 2))
    doc.h(2, "4.4 Variance investigation")
    doc.ps(pr.paras(["test2"], 2))
    doc.h(2, "4.5 Exit from the parallel run")
    doc.p(f"The Head of Reserving, {ctx.name('P009')}, recommends exit from the parallel run to the Programme Skerry "
          f"Steering Committee once the variance measures have been within tolerance for the period agreed with the "
          f"Reserving Committee and all open breaks have been explained.")
    doc.ps(pr.paras(["governance", "test2"], 1))

    # 5 Migration -------------------------------------------------------------------------
    doc.h(1, "5 Data migration testing", page_break=True)
    doc.p("Migration follows the region-wave approach of ADR-015. Each wave is rehearsed in full with masked data "
          "(ADR-025) before the production cut-over, and every rehearsal is reconciled.")
    rows = []
    for w in W.waves.values():
        if w["id"] == "MW-2":
            continue
        reh = w.get("rehearsals")
        rows.append([w["name"], w["scope"], f"{reh} full rehearsals" if reh else "To be confirmed",
                     "Planned for " + ("June 2026" if w["id"] == "MW-0" else "September 2026")])
    rows.append(["Wave 2", "Remaining UK and Nordic products", "To be confirmed", "To be confirmed in the wave plan"])
    doc.table(["Wave", "Scope", "Rehearsals", "Timing"], rows, widths=[3.6, 6.4, 3.0, 3.6], caption="Migration waves in scope",
              font_size=8.6)
    doc.ps(pr.paras(["migration", "test2"], 3))
    doc.h(2, "5.1 Rehearsal scope")
    doc.bullets(["Extract from CLARA and the satellite systems using the production extract jobs.",
                 "Transformation and load into the Claims Hub databases.",
                 "Automated reconciliation of counts, amounts and statuses.",
                 "Business verification of a sample of migrated claims by the claims teams.",
                 "Timed cut-over run book, including the freeze and the fallback decision point."])
    doc.h(2, "5.2 Business verification")
    doc.ps(pr.paras(["migration", "test2"], 2))

    # 6 Interfaces ------------------------------------------------------------------------
    doc.h(1, "6 Interface and contract testing", page_break=True)
    doc.p("Interface changes caused the most serious incident of 2025: on 28 April 2025 a change to the layout of the "
          "reserve movement record broke the general ledger journals (INC-2025-0412). Since then every interface change "
          "requires sign-off from the downstream consumers (CHUB-144), and contract tests are mandatory for all Kafka "
          "topics (ADR-023).",
          facts=[F("general", "INC-2025-0412 (2025-04-28) is cited as the reason interface changes need consumer sign-off (CHUB-144).",
                   "INC-2025-0412", "INCIDENT:INC-2025-0412")])
    rows = []
    for i in W.interfaces.values():
        if not i.get("services") and i["id"] not in ("CLX-IF-043", "CLX-IF-044", "CLX-IF-047"):
            continue
        live = str(i["since"]) <= date
        rows.append([i["id"], ctx.a(i["name"]), ctx.sys(i["source_system"]), ctx.sys(i["target_system"]), i["protocol"],
                     "Live" if live else "Planned", "Contract + end-to-end" if i["protocol"] in ("Kafka", "REST") else "End-to-end"])
    doc.table(["ID", "Interface", "From", "To", "Protocol", "Status", "Test type"], rows,
              widths=[2.0, 4.2, 2.6, 2.6, 1.5, 1.5, 2.4], caption="Interfaces in scope", font_size=7.8)
    doc.ps(pr.paras(["integration", "test2"], 2))
    doc.h(2, "6.1 Event contracts")
    rows = []
    for name, s in W.services.items():
        prod = H.topics_ok(ctx, s["kafka_topics"]["produces"])
        cons = H.topics_ok(ctx, s["kafka_topics"]["consumes"])
        if prod or cons:
            rows.append([ctx.svc(name), ", ".join(prod) or "—", ", ".join(cons) or "—"])
    doc.table(["Service", "Produces", "Consumes"], rows, widths=[4.0, 6.0, 6.6], caption="Event contracts under test",
              font_size=8.0)
    doc.ps(pr.paras(["integration"], 1))
    doc.h(2, "6.2 CLARA batch jobs in scope")
    doc.p("CLARA batch jobs that feed interfaces used by Claims Hub, or whose outputs are compared during the parallel "
          "run, are regression tested whenever the jobs or their record layouts change. Schedules are taken from the "
          "Batch Scheduler and are not repeated here.")
    rows = []
    for j in H.jobs_asof(ctx):
        if not any(s_["program"].startswith(("CLRRS", "CLRGL", "CLRFR")) for s_ in j["steps"]):
            continue
        rows.append([j["name"], ctx.a(j["description"]).split(" (")[0], ", ".join(s_["program"] for s_ in j["steps"]),
                     "Regression and record-layout comparison"])
    doc.table(["Job", "Description", "Programs", "Test approach"], rows, widths=[2.4, 6.0, 4.0, 4.2],
              caption="CLARA jobs in regression scope", font_size=8.2)
    doc.ps(pr.paras(["batch", "test2"], 2))

    # 7 Rules -----------------------------------------------------------------------------
    doc.h(1, "7 Business rule testing", page_break=True)
    doc.p("Business rules are held as versioned configuration rather than in a rules engine (ADR-010). Each rule is "
          "tested with a decision table that covers every combination of its inputs, including the boundaries.")
    doc.ps(pr.paras(["test2"], 1))
    for name in ("triage-svc", "fraud-referral-svc", "settlement-svc", "payment-orchestrator", "recovery-svc"):
        rules = H.rules_for_service(ctx, name)
        if not rules:
            continue
        doc.h(2, f"7.{['triage-svc', 'fraud-referral-svc', 'settlement-svc', 'payment-orchestrator', 'recovery-svc'].index(name) + 1} {ctx.svc(name)}")
        doc.table(["Rule", "Title", "Version"], [[r, t, f"v{v}"] for r, t, v in rules], widths=[2.6, 11.6, 2.4],
                  font_size=8.4)
        doc.p(pr.para(["test2", "phase"], n=(2, 3), phase="rule testing"))
    doc.h(2, "7.6 Changes for NISA Circular 2026/04")
    doc.p("NISA Circular 2026/04, published on 20 November 2025, changes the fraud referral rules from 1 April 2026. The "
          "detailed requirements are being specified in the fraud referral BRD. Test scope will cover the referral "
          "threshold, the customer notice and its deferral, the removal of decisions based on the score alone, SIU "
          "triage and the quarterly NISA-FR1 return. A separate test plan will be issued once the BRD is approved.")
    doc.ps(pr.paras(["test2"], 1))

    # 8 NFR -------------------------------------------------------------------------------
    doc.h(1, "8 Non-functional testing", page_break=True)
    for k, (t, extra) in enumerate([
            ("Performance and capacity", "Volume models are based on peak notification days, including weather events. "
             "The assessment-svc performance test at twice the Wave 1 volume is tracked as CHUB-110."),
            ("Resilience", "Failure of each dependency is simulated to confirm that services degrade gracefully and recover."),
            ("Security", "Security testing covers authentication through the Corvane Identity Service, authorisation, input "
             "validation and secrets handling."),
            ("Accessibility", "Customer-facing journeys are tested against the accessibility standard used for the portal."),
            ("Observability", "Dashboards, alerts and service level objectives defined under ADR-024 are tested as part of "
             "operational acceptance.")], 1):
        doc.h(2, f"8.{k} {t}")
        doc.p(extra)
        doc.ps(pr.paras(["test2", "test"], 1, n=(3, 4)))

    # 9 Environments ---------------------------------------------------------------------
    doc.h(1, "9 Test environments")
    doc.table(["Environment", "Purpose", "Data", "Refresh"],
              [["Development", "Squad development and component tests", "Synthetic", "On demand"],
               ["SIT", "System integration with CLARA test region and stubs", "Synthetic and masked", "Each release"],
               ["UAT", "Business acceptance and regulatory testing", "Masked", "Each release"],
               ["Performance", "Load and stress testing", "Generated at production volume", "Before each wave"],
               ["Pre-production", "End-to-end, security and operational acceptance", "Masked", "Each release"],
               ["Migration rehearsal", "Full migration rehearsals", "Masked extract of production", "Per rehearsal"]],
              widths=[3.2, 6.0, 3.8, 3.6], caption="Test environments", font_size=8.6)
    doc.ps(pr.paras(["test2"], 2))

    # 10 Data ---------------------------------------------------------------------------
    doc.h(1, "10 Test data management")
    doc.p("Masked data is used for migration rehearsals and acceptance testing in line with ADR-025. Masking replaces "
          "names, addresses, contact details, bank details and free text while preserving the structure, distributions "
          "and relationships that the tests depend on.")
    doc.ps(pr.paras(["test2", "data"], 2))

    # 11 Defects ------------------------------------------------------------------------
    doc.h(1, "11 Defect management", page_break=True)
    doc.table(["Severity", "Definition", "Expected response"], [list(s) for s in SEVERITY], widths=[3.0, 8.6, 5.0],
              caption="Defect severity", font_size=8.6)
    doc.ps(pr.paras(["test", "test2"], 2))

    # 12 Roles --------------------------------------------------------------------------
    doc.h(1, "12 Roles and responsibilities")
    roles = [("P053", "Test strategy, test lead for Claims Hub releases"),
             ("P040", "Quality of the Intake & Triage services"),
             ("P041", "Quality of the Reserve & Finance services; parallel-run reconciliation tooling"),
             ("P042", "Quality of the Fraud & Settlement services"),
             ("P051", "Migration rehearsals and reconciliation"),
             ("P009", "Acceptance of reserve results and exit from the parallel run"),
             ("P016", "CLARA changes and CLARA test region"),
             ("P026", "Batch schedule changes in test and rehearsal"),
             ("P037", "Review of regulatory requirement evidence"),
             ("P011", "User acceptance by the claims teams")]
    doc.table(["Name", "Title", "Responsibility"],
              [[ctx.name(p), ctx.title(p), r] for p, r in roles], widths=[3.6, 5.6, 7.4], caption="Test roles", font_size=8.6)
    doc.ps(pr.paras(["governance"], 1))

    # 13 Reporting ----------------------------------------------------------------------
    doc.h(1, "13 Reporting and governance")
    doc.p(f"Test progress is reported weekly to the release team and monthly to the Programme Skerry Steering Committee "
          f"chaired by {ctx.person('P004')}. Design questions raised by testing are taken to the Design Authority.")
    doc.ps(pr.paras(["test2", "governance"], 2))

    # 14 Risks --------------------------------------------------------------------------
    doc.h(1, "14 Risks, assumptions and dependencies")
    doc.table(["Ref", "Risk or assumption", "Mitigation"],
              [["TR-01", "Test environments are not available when needed", "Environment plan agreed a quarter ahead"],
               ["TR-02", "Masked data does not cover rare scenarios", "Synthetic claims created for edge cases"],
               ["TR-03", "Business testers are not released from operational duties", "UAT windows agreed with stage owners"],
               ["TR-04", "Regulatory requirements change late", "Decision tables designed so new versions can be added quickly"],
               ["TR-05", "Interface consumers are not available for end-to-end tests", "Stubs and recorded contracts used as fallback"],
               ["TR-06", "Parallel-run breaks take longer to explain than planned", "Daily triage with Reserving and the squads"]],
              widths=[1.6, 7.6, 7.4], caption="Test risks", font_size=8.6)
    doc.ps(pr.paras(["test2"], 1))

    # 15 Lessons ----------------------------------------------------------------------
    doc.h(1, "15 Lessons from 2025", page_break=True)
    doc.p("The incidents below occurred during 2025 and the MVP release. Each has changed the way the programme tests.")
    lessons = [("INC-2025-0412", "Every interface change is regression tested with all downstream consumers, and record "
                "layouts are compared byte for byte before release."),
               ("INC-2025-0815", "Access and role mappings are tested as part of operational acceptance whenever teams or "
                "reporting lines change."),
               ("INC-2025-1103", "Configuration for every environment is checked against the system register before "
                "go-live, including endpoints affected by renames."),
               ("INC-2025-0443", "Batch timing tests are repeated after large data loads, not only on representative volumes."),
               ("INC-2025-0677", "Commit frequency of batch programs is reviewed as part of CLARA change testing.")]
    rows = []
    for iid, lesson in lessons:
        inc = W.incidents[iid]
        rows.append([iid, short_date(inc["date"]), inc["title"], lesson])
    doc.table(["Incident", "Date", "What happened", "What changes in testing"], rows, widths=[2.6, 2.2, 5.2, 6.6],
              caption="Lessons learned", font_size=8.4,
              facts=[F("general", "INC-2025-1103 (2025-11-03): document-svc failed to store documents after the DOCSTOR rename.",
                       "document-svc failed to store documents after DOCSTOR renamed to Evidence Vault", "INCIDENT:INC-2025-1103",
                       where=(3, 2))])
    doc.ps(pr.paras(["test2"], 2))
    doc.h(1, "16 Test measures")
    doc.table(["Measure", "Definition", "Use"],
              [["Requirement coverage", "Requirements with at least one passed test, as a share of requirements in scope", "Exit criteria"],
               ["Pass rate", "Executed tests that passed, as a share of executed tests", "Progress reporting"],
               ["Defect arrival", "New defects raised per week, by severity", "Stability trend"],
               ["Defect age", "Time from raising to closing a defect, by severity", "Triage effectiveness"],
               ["Escaped defects", "Defects found in production that a test phase should have found", "Phase effectiveness"],
               ["Automation coverage", "Regression tests that run without manual steps, as a share of the regression pack", "Investment decisions"],
               ["Environment availability", "Hours an environment was usable, as a share of planned hours", "Environment planning"]],
              widths=[3.6, 8.4, 4.6], caption="Test measures", font_size=8.6)
    doc.ps(pr.paras(["test2"], 1))

    # Appendices ------------------------------------------------------------------------
    doc.h(1, "Appendix A – Services in scope", page_break=True)
    rows = []
    for name, s in W.services.items():
        o = W.service_owner(name, date)
        rows.append([ctx.svc(name), H.svc_desc(ctx, name), ctx.team(o["team"]) if o else "—"])
    doc.table(["Service", "Responsibility", "Squad"], rows, widths=[3.8, 8.8, 4.0], caption="Claims Hub services", font_size=8.4)
    doc.h(1, "Appendix B – API regression inventory", page_break=True)
    doc.p("Every API below is covered by automated component and regression tests in the build pipeline. The inventory is "
          "generated from the published API descriptions.")
    rows = []
    for name in W.services:
        for a in H.svc_apis(ctx, name):
            rows.append([ctx.svc(name), a["method"], a["path"], a["summary"], "Component, contract, regression"])
    doc.table(["Service", "Method", "Path", "Summary", "Automated tests"], rows, widths=[3.2, 1.6, 4.4, 4.6, 2.8],
              caption="API regression inventory", font_size=7.8)
    doc.h(1, "Appendix C – Process scenario catalogue", page_break=True)
    doc.p("End-to-end and acceptance scenarios are organised by process step. Each step has at least a standard scenario, "
          "an exception scenario and, where the step applies a business rule, a rule boundary scenario. Priorities follow "
          "the risk areas in section 2.2.")
    rows = []
    rng = util.rng(f"{FID}:scen")
    pri_map = {"S4": "P1", "S5": "P1", "S6": "P1", "S1": "P2", "S2": "P2", "S3": "P2", "S7": "P2"}
    exc = ["mandatory information missing", "duplicate submission", "downstream system unavailable",
           "customer contact details invalid", "claim reopened after closure", "currency other than GBP",
           "user without the required authority", "backdated notification", "claim transferred between teams"]
    for x, st in W.steps.items():
        if x in ("PS-FRD-03", "PS-FRD-05"):
            continue
        base = f"TS-{x[3:]}"
        rows.append([f"{base}-01", x, f"{st['name']} – standard case", "End-to-end", pri_map[st["stage"]]])
        rows.append([f"{base}-02", x, f"{st['name']} – {rng.choice(exc)}", "End-to-end", "P2" if pri_map[st["stage"]] == "P1" else "P3"])
        rules = [r for r in st.get("rules", []) if ctx.rule(r)]
        if rules:
            rows.append([f"{base}-03", x, f"{st['name']} – boundary values of {rules[0]}", "UAT", pri_map[st["stage"]]])
        if st.get("decision"):
            rows.append([f"{base}-04", x, f"{st['name']} – each decision branch", "UAT", pri_map[st["stage"]]])
    doc.table(["Scenario", "Step", "Scenario", "Phase", "Priority"], rows, widths=[2.6, 2.4, 7.6, 2.2, 1.8],
              caption="Scenario catalogue", font_size=7.8)
    doc.h(1, "Appendix D – Release readiness checklist", page_break=True)
    checks = ["All exit criteria for the release's test phases met or waived with approval",
              "No open Sev1 defects; open Sev2 defects accepted by the product owner with workarounds",
              "Regression pack passed on the release candidate in pre-production",
              "Contract tests passed for every changed API and topic",
              "Downstream consumers have signed off interface changes",
              "Performance results reviewed against the volume model",
              "Security findings triaged; no open critical or high findings",
              "Runbooks, dashboards and alerts accepted by the support teams",
              "Rollback procedure tested in pre-production",
              "Business sign-off recorded by the stage owners",
              "Compliance review of regulatory requirement evidence completed",
              "Release notes and known-issues list published"]
    doc.table(["#", "Check", "Evidence", "Confirmed by"],
              [[str(i), c, "Test management tool / release log", "Test lead" if i < 9 else "Product owner"]
               for i, c in enumerate(checks, 1)], widths=[0.8, 9.0, 4.0, 2.8], caption="Release readiness checklist",
              font_size=8.4)
    doc.h(2, "Defect workflow")
    doc.table(["State", "Meaning", "Next states"],
              [["New", "Raised and awaiting triage", "Open, Rejected, Duplicate"],
               ["Open", "Accepted and assigned to a squad", "In progress"],
               ["In progress", "Fix being developed", "Ready for retest"],
               ["Ready for retest", "Fix deployed to the environment where the defect was found", "Closed, Reopened"],
               ["Reopened", "Retest failed", "In progress"],
               ["Deferred", "Accepted for a later release with a workaround", "Open"],
               ["Closed", "Retest passed", "—"]], widths=[3.4, 8.6, 4.6], font_size=8.6)
    doc.ps(pr.paras(["test"], 1))
    doc.h(1, "Appendix E – Glossary")
    doc.table(["Term", "Meaning"],
              [["Parallel run", "Period in which CLARA and Claims Hub both calculate reserves for the same claims and the results are compared daily."],
               ["Rehearsal", "A full, timed run of a wave's migration in a non-production environment."],
               ["Break", "A claim-level difference found by reconciliation."],
               ["Contract test", "An automated test that checks a producer's interface against the expectations of its consumers."],
               ["Decision table", "A table listing every combination of a rule's inputs and the expected outcome."]]
              + [[t, ctx.a(m)] for t, m in C.glossary_terms(["G-003", "G-013", "G-019", "G-020"])],
              widths=[3.6, 13.0], font_size=8.6)
    return doc

"""LD025 – CLARA Operations Runbook (DOCX -> PDF via LibreOffice, 2024-11-04, Sunita Vaghela, approved).

As of November 2024: FRAUDNET (not Sentinel), DOCSTOR, Adjuster Extranet, no Claims Hub. The CLRNRSV1 restart
instruction (PL-068, exclusive) appears only in the batch restart table. CICS region names, the DB2 subsystem/plan
and the CLX-IF-042 / CLRNRSV3 schedule are never stated (other files own them).
"""
from __future__ import annotations

import re

from . import common as C
from . import hub as H
from .b_ld017 import clean_old
from .core import Ctx, Doc, F, PF, Style, W, long_date, short_date, util
from .prose import Prose

FID = "LD025"
RESTART_SECTION = "7.2"


def _table_ok(ctx: Ctx, t: str) -> bool:
    tb = W.tables.get(t)
    if not tb:
        return False
    created = str(tb.get("created") or "0000")
    return created <= ctx.date and t != "CLR.T_FRAUD_NOTIFICATION"


def _hhmm(s: str) -> str | None:
    m = re.match(r"daily (\d\d:\d\d)$", s or "")
    return m.group(1) if m else None


def build() -> Doc:
    ctx = Ctx(FID)
    date = ctx.date
    pr = Prose(util.rng(f"{FID}:prose"), date=ctx.date, forbid=("Claims Hub", "the Hub", "Kafka"))
    clara = W.systems["SYS01"]
    doc = Doc(ctx, title="CLARA Operations Runbook", doc_id="OPS-CLR-001", version="5.2", status="Approved",
              subtitle="Batch and online operations for the Claims Ledger And Reserve Application",
              style=Style(font="Arial", heading_font="Arial", accent="2F4F4F", accent2="DDE5E5", size=11),
              header_left="CLARA Operations Runbook", header_right="OPS-CLR-001 v5.2",
              footer_left="Internal – Mainframe Batch Operations")
    doc.title_page(C.control_rows(ctx, doc, owner="P016", extra=[["Support team", ctx.team("T25")],
                                                                  ["Application support", ctx.team("T20")]]))
    C.version_history(ctx, doc, [("4.0", 980, "Runbook rewritten for the Batch Scheduler migration"),
                                 ("5.0", 395, "Job procedures restructured; restart table added"),
                                 ("5.1", 160, "Interface section updated"),
                                 ("5.2", 0, "MyCorvane Claims name; annual review")])
    C.approvals(ctx, doc, [("P016", "Platform owner"), ("P031", "Integration platform"), ("P006", "Chief Information Officer")])
    C.reviewers(ctx, doc, ["P023", "P024", "P025", "P031"])
    doc.toc(depth=2)

    # 1 Introduction ------------------------------------------------------------------------
    doc.h(1, "1 Introduction")
    doc.p("This runbook is the operational reference for CLARA, Corvane's claims administration and reserving system. "
          "It is used by Mainframe Batch Operations and by the CLARA application support team to run the nightly "
          "schedule, monitor the online service, handle failures and recover the service.")
    doc.ps(pr.paras(["ops", "ops2"], 2))
    doc.h(2, "1.1 How to use this runbook")
    doc.bullets(["Section 3 describes the online service and the external services CLARA calls.",
                 "Sections 4 and 5 describe the batch schedule and give a procedure for each job.",
                 "Section 6 lists the interfaces and their schedules.",
                 f"Section 7 sets out the restart procedures, including the batch restart table in section {RESTART_SECTION}.",
                 "Sections 8 to 11 cover period-end processing, incidents, disaster recovery and housekeeping."])
    doc.h(2, "1.2 Escalation contacts")
    rows = []
    for pid, role in [("P026", "Batch Operations Lead – first escalation for batch"),
                      ("P023", "Senior Mainframe Developer – application on-call"),
                      ("P024", "Mainframe Developer – application on-call"),
                      ("P025", "DB2 Database Administrator"),
                      ("P031", "Integration Platform Lead – MQ and file transfer"),
                      ("P016", "CLARA Platform Manager – major incidents")]:
        rows.append([ctx.name(pid), ctx.title(pid), role, ctx.email(pid)])
    doc.table(["Name", "Title", "Role in this runbook", "Email"], rows, widths=[3.4, 4.0, 5.2, 4.0], caption="Contacts",
              font_size=8.4)
    doc.ps(pr.paras(["ops2"], 1))

    # 2 Overview ---------------------------------------------------------------------------
    doc.h(1, "2 System overview", page_break=True)
    pairs = [["System", "CLARA (Claims Ledger And Reserve Application)"], ["Live since", long_date(clara["go_live"])],
             ["Technology", "COBOL, CICS TS, DB2 for z/OS, IBM MQ, JCL batch"],
             ["Platform owner", ctx.person(clara["owner"])]]
    if ctx.ok("SYSTEM:SYS01", "hosting"):
        pairs.append(["Hosting", clara["hosting"].replace(" (LOC-LDC)", "").replace(" (LOC-BDC)", "")])
    if ctx.ok("SYSTEM:SYS01", "batch_window"):
        pairs.append(["Batch window", clara["batch_window"]])
    if ctx.ok("SYSTEM:SYS01", "mq_queue_manager"):
        pairs.append(["MQ queue manager", clara["mq_queue_manager"]])
    pairs.append(["Scheduler", ctx.sys(W.jcl_jobs["CLRNRSV1"]["scheduler"])])
    doc.kv(pairs, caption="CLARA at a glance", widths=(4.0, 12.6), font_size=9,
           facts=[F("general", "CLARA's nightly batch window runs 23:30–05:30 UK time.", clara["batch_window"],
                    "SYSTEM:SYS01#batch_window", where=(next(i for i, p in enumerate(pairs) if p[0] == "Batch window"), 1))])
    doc.ps(pr.paras(["ops", "batch"], 2))
    doc.h(2, "2.1 Connected systems")
    sids = [s for s in W.systems if s not in ("SYS01", "SYS02") and not (W.systems[s].get("go_live") and str(W.systems[s]["go_live"]) > date)
            and s not in ("SYS15", "SYS16")]
    C.systems_table(ctx, doc, sids, "Systems connected to CLARA")
    doc.ps(pr.paras(["ops", "ops2"], 1))

    # 3 Online ------------------------------------------------------------------------------
    doc.h(1, "3 Online services", page_break=True)
    doc.p("CLARA online transactions run in CICS and are used by claims handlers, assessors, SIU and the payments team "
          "during the working day. The service hours and the procedure for recycling a CICS region are set out below.")
    doc.ps(pr.paras(["online", "ops2"], 2))
    doc.h(2, "3.1 External services called online")
    fr = ctx.sys("SYS03")
    doc.p(f"Fraud scores are obtained online from {fr} at fraudnet.corvane.internal. The online fraud scoring program "
          f"calls {fr} over REST (interface CLX-IF-008) when a claim is registered; if {fr} does not respond in time the "
          f"claim is saved unscored and is picked up by the nightly batch scoring run.",
          facts=[PF(ctx, "ld25_fraudnet", "fraud scores are obtained online from FRAUDNET at fraudnet.corvane.internal",
                    notes="Online services chapter (§3.1). Contradicts the later name Sentinel (C06).")])
    rows = []
    for iid in ("CLX-IF-007", "CLX-IF-008", "CLX-IF-017", "CLX-IF-002"):
        i = W.interfaces[iid]
        rows.append([iid, ctx.a(i["name"]), ctx.sys(i["target_system"]) if i["source_system"] == "SYS01" else ctx.sys(i["source_system"]),
                     i["protocol"], i.get("criticality", "—")])
    doc.table(["Interface", "Name", "Partner system", "Protocol", "Criticality"], rows, widths=[2.4, 6.0, 3.6, 2.0, 2.6],
              caption="Online interfaces", font_size=8.6)
    doc.p(f"If {fr} is unavailable, operations do not need to take action on CLARA: unscored claims are picked up by job "
          f"CLRNFR01. The {fr} support team must be informed through the service desk.")
    doc.ps(pr.paras(["online"], 1))
    doc.h(2, "3.2 Transactions")
    rows = []
    for m in W.bms_maps.values():
        p = W.programs.get(m["program"])
        if not p or str(p["since"]) > date:
            continue
        rows.append([m["transaction"], m["program"], m["map"], clean_old(ctx, m["title"])])
    doc.table(["Transaction", "Program", "Map", "Function"], rows, widths=[2.4, 2.6, 2.4, 9.2], caption="CLARA transactions",
              font_size=8.4)
    doc.ps(pr.paras(["online", "ops2"], 2))
    doc.h(2, "3.3 Online program reference")
    doc.p("The online programs are listed below with the tables they read and update. Use this reference to judge the "
          "impact of a failing transaction or a locked table.")
    for p_ in sorted((x for x in H.programs_asof(ctx) if x["type"] == "online"), key=lambda x: x["id"]):
        reads = [t for t in p_.get("reads_tables", []) if _table_ok(ctx, t)]
        writes = [t for t in p_.get("writes_tables", []) if _table_ok(ctx, t)]
        calls = [c for c in p_.get("calls_programs", []) if c in W.programs and str(W.programs[c]["since"]) <= date]
        doc.h(3, f"{p_['id']} – {clean_old(ctx, H.program_desc(ctx, p_['id']))}")
        doc.kv([["Transaction", p_.get("cics_transaction") or ("called routine" if p_.get("subprogram") else "—")],
                ["Map", p_.get("bms_map") or "—"], ["Reads", ", ".join(reads) or "—"], ["Updates", ", ".join(writes) or "—"],
                ["Calls", ", ".join(calls) or "—"]], widths=(3.0, 13.6), font_size=8.2)
    doc.ps(pr.paras(["online", "ops2"], 2))
    doc.h(2, "3.4 Handling online problems")
    doc.table(["Symptom", "First checks", "Escalate to"],
              [["Single transaction failing for all users", "Transaction status; recent changes; error records", "Application on-call"],
               ["All transactions slow", "Region load, DB2 locks, external call times", "Application on-call, DBA"],
               ["Fraud score missing on new claims", f"{fr} availability via the service desk", f"{fr} support"],
               ["Vehicle data not returned", "Vehicle Data Service availability", "Integration Platform"],
               ["Portal claims not arriving", "MQ queue depth and channel status for CLX-IF-001", "Integration Platform"],
               ["Users cannot sign on", "Security profile changes", "Access management"]],
              widths=[4.6, 7.0, 5.0], caption="Online problem guide", font_size=8.6)
    doc.ps(pr.paras(["online", "ops2"], 2))

    # 4 Batch schedule ---------------------------------------------------------------------
    jobs = H.jobs_asof(ctx)
    doc.h(1, "4 Batch schedule", page_break=True)
    doc.p(f"The nightly schedule runs within the batch window ({clara['batch_window']}). Daily jobs are listed in time "
          f"order; weekly, monthly, quarterly and annual jobs follow. Jobs shown as 'operations schedule' are triggered "
          f"by the Batch Scheduler calendar rather than at a fixed time.")
    daily, other = [], []
    for j in jobs:
        sch = H.job_schedule(ctx, j)
        row = [j["name"], clean_old(ctx, j["description"]), sch or "Operations schedule",
               ", ".join(s["program"] for s in j["steps"]), ctx.team(j["owner_team"])]
        (daily if _hhmm(sch or "") else other).append(row)
    daily.sort(key=lambda r: ((_hhmm(r[2]) < "12:00"), _hhmm(r[2])))
    doc.table(["Job", "Description", "Schedule", "Programs", "Owner"], daily, widths=[2.2, 5.4, 2.6, 4.0, 2.4],
              caption="Daily jobs in time order", font_size=8.2,
              facts=[F("general", "Job CLRNRSV1 (Tier-3 reserve review and revaluation) runs daily at 01:30.", "daily 01:30",
                       "JCL:CLRNRSV1#schedule", where=(next(i for i, r in enumerate(daily, 1) if r[0] == "CLRNRSV1"), 2))])
    doc.table(["Job", "Description", "Schedule", "Programs", "Owner"], other, widths=[2.2, 5.4, 2.6, 4.0, 2.4],
              caption="Other scheduled jobs", font_size=8.2)
    doc.ps(pr.paras(["batch", "ops2"], 2))

    # 5 Job procedures ----------------------------------------------------------------------
    doc.h(1, "5 Job procedures", page_break=True)
    doc.p(f"Each job is described with its steps, the tables it reads and updates, the interfaces it feeds and the "
          f"checks to make after it completes. Restart instructions for every job are in the batch restart table in "
          f"section {RESTART_SECTION}.")
    for k, j in enumerate(jobs, 1):
        doc.h(2, f"5.{k} {j['name']} – {clean_old(ctx, j['description'])}", page_break=k > 1)
        sch = H.job_schedule(ctx, j) or "Operations schedule"
        doc.kv([["Schedule", sch], ["Owner", ctx.team(j["owner_team"])], ["Scheduler", ctx.sys(j["scheduler"])],
                ["Status", j.get("status", "active")], ["Steps", str(len(j["steps"]))]], widths=(3.4, 13.2), font_size=8.6)
        rows = []
        for s_ in j["steps"]:
            rows.append([s_["step"], s_["program"], clean_old(ctx, H.program_desc(ctx, s_["program"]))])
        doc.table(["Step", "Program", "Function"], rows, widths=[1.8, 2.4, 12.4], font_size=8.2)
        for s_ in j["steps"]:
            p_ = W.programs.get(s_["program"])
            if not p_:
                continue
            reads = [t for t in p_.get("reads_tables", []) if _table_ok(ctx, t)]
            writes = [t for t in p_.get("writes_tables", []) if _table_ok(ctx, t)]
            calls = [c for c in p_.get("calls_programs", []) if c in W.programs and str(W.programs[c]["since"]) <= date]
            doc.h(3, f"{s_['step']} {s_['program']}")
            doc.kv([["Reads", ", ".join(reads) or "—"], ["Updates", ", ".join(writes) or "—"],
                    ["Calls", ", ".join(calls) or "—"], ["Copybooks", ", ".join(p_.get("copybooks", [])) or "—"],
                    ["Support owner", ctx.name(p_["owner_person"]) if p_.get("owner_person") and ctx.employed(p_["owner_person"]) else ctx.team(p_["owner_team"])]],
                   widths=(3.0, 13.6), font_size=8.2)
        ifs, impact = [], []
        for s_ in j["steps"]:
            for i in H.interfaces_for_program(ctx, s_["program"]):
                lab = f"{i['id']} {ctx.a(i['name'])}"
                if lab in ifs:
                    continue
                ifs.append(lab)
                teams = ", ".join(ctx.team(t) for t in i.get("consumer_teams", []) if t in W.teams) or "—"
                impact.append([i["id"], ctx.a(i["name"]), ctx.sys(i["target_system"]), teams])
        if impact:
            doc.p("If this job fails or is late, the following interfaces and teams are affected:", size=9.5)
            doc.table(["Interface", "Name", "Receiving system", "Teams to inform"], impact, widths=[2.2, 6.0, 3.6, 4.8],
                      font_size=8.2)
        else:
            doc.p("This job does not feed an interface directly.", size=9.5)
        doc.p(f"Restart: see the batch restart table, section {RESTART_SECTION}.", size=9.5)
        doc.table(["After completion, check", "Action if not as expected"],
                  [["Job ended with return code 0 or 4", "Review the job output and follow section 7"],
                   ["Record counts in the job summary are in line with recent runs", "Inform application on-call before releasing successors"],
                   ["Completion record written", "Hold dependent jobs and interfaces"],
                   ["No DB2 timeouts or deadlocks reported", "Inform the DBA"]],
                  widths=[8.0, 8.6], font_size=8.2)
        doc.p(pr.para(["job", "ops2", "batch"], n=(4, 6), job=j["name"]))
        doc.p(pr.para(["ops2", "batch", "ops"], n=(3, 5)))
        doc.p(pr.para(["job", "ops"], n=(3, 4), job=j["name"]))

    # 6 Interfaces ----------------------------------------------------------------------------
    doc.h(1, "6 Interfaces", page_break=True)
    doc.p("The table lists the interfaces live at the date of this runbook. Interfaces without a fixed time are "
          "triggered by the jobs that produce them; their timing follows the job schedule.")
    rows = []
    for i in H.interfaces_asof(ctx):
        sch = H.iface_schedule(ctx, i["id"]) or "Triggered by producing job"
        rows.append([i["id"], ctx.a(i["name"]), ctx.sys(i["source_system"]), ctx.sys(i["target_system"]), i["protocol"], sch])
    doc.table(["ID", "Name", "From", "To", "Protocol", "Schedule"], rows, widths=[2.0, 4.6, 2.8, 2.8, 1.6, 2.8],
              caption="Live interfaces", font_size=7.8,
              facts=[F("temporal", "In November 2024 CLX-IF-043 (GL Reserve Journal Feed) ran daily at 03:00.",
                       "daily 03:00", "INTERFACE:CLX-IF-043#schedule_history",
                       where=(next(k for k, r in enumerate(rows, 1) if r[0] == "CLX-IF-043"), 5))])
    doc.ps(pr.paras(["ops", "ops2"], 2))
    for n_, i in enumerate(H.interfaces_asof(ctx), 1):
        doc.h(2, f"6.{n_} {i['id']} {ctx.a(i['name'])}")
        pairs = [["Flow", f"{ctx.sys(i['source_system'])} → {ctx.sys(i['target_system'])}"], ["Protocol", i["protocol"]]]
        if i["id"] != "CLX-IF-042" and i.get("format") and "Kafka" not in i["format"]:
            pairs.append(["Format", ctx.a(i["format"])])
        if i.get("programs"):
            pairs.append(["CLARA programs", ", ".join(p for p in i["programs"] if p in W.programs and str(W.programs[p]["since"]) <= date)])
        if i.get("owner") and ctx.employed(i["owner"]):
            pairs.append(["Interface owner", ctx.person(i["owner"])])
        if i.get("avg_daily_volume") and ctx.ok(f"INTERFACE:{i['id']}", "avg_daily_volume"):
            pairs.append(["Typical volume", i["avg_daily_volume"]])
        deps = [d for d in i.get("dependents", []) if str(W.interfaces[d]["since"]) <= date]
        if deps:
            pairs.append(["Downstream interfaces", ", ".join(deps)])
        if i.get("criticality"):
            pairs.append(["Criticality", i["criticality"]])
        doc.kv(pairs, widths=(3.6, 13.0), font_size=8.6)
        doc.p(pr.para(["ops2", "online", "ops"], n=(3, 5)))
        doc.p(pr.para(["batch", "ops2"], n=(2, 4)))

    # 7 Restart -----------------------------------------------------------------------------
    doc.h(1, "7 Restart and recovery", page_break=True)
    doc.h(2, "7.1 Standard restart procedure")
    doc.bullets(["Identify the failing step and the abend or return code from the job output.",
                 "Check the shift log and the incident queue for related failures.",
                 "Confirm whether the failing step committed any updates before it failed.",
                 "Correct the cause, or obtain the application on-call's agreement to proceed.",
                 "Restart from the failing step unless the restart table says otherwise.",
                 "Check record counts and the completion record after the restart.",
                 "Record the restart in the shift log and update the incident."], numbered=True)
    doc.ps(pr.paras(["ops2"], 1))
    doc.h(2, f"{RESTART_SECTION} Batch restart table")
    doc.p("Job-specific restart instructions override the standard procedure. Jobs not listed with specific "
          "instructions follow section 7.1.")
    rows, facts = [], []
    for j in jobs:
        note = j.get("restart")
        if note and not ctx.ok(f"JCL:{j['name']}", "restart"):
            note = None
        rows.append([j["name"], ", ".join(f"{s['step']} {s['program']}" for s in j["steps"]), note or "Standard procedure (section 7.1)"])
        if j["name"] == "CLRNRSV1":
            ctx.need("JCL:CLRNRSV1", "restart")
            facts.append(PF(ctx, "ld25_restart", "STEP010 (CLRRS110) must not be rerun on the same business date",
                            where=(len(rows), 2), notes=f"Batch restart table (section {RESTART_SECTION}), row CLRNRSV1."))
        if j["name"] == "CLRYGL90":
            facts.append(F("general", "CLRYGL90 can be rerun: the revaluation is idempotent for the same rate date.",
                           "revaluation is idempotent for the same rate date", "JCL:CLRYGL90#restart", where=(len(rows), 2)))
    doc.table(["Job", "Steps", "Restart instruction"], rows, widths=[2.4, 5.8, 8.4], caption="Batch restart table",
              font_size=8.2, facts=facts)
    doc.h(2, "7.3 Common abend codes")
    doc.table(["Code", "Meaning", "Typical action"],
              [["S0C7", "Data exception (invalid packed decimal)", "Identify the record; correct data with application on-call"],
               ["S0C4", "Protection exception", "Escalate to application on-call"],
               ["S322", "CPU time limit exceeded", "Check for loops or lock waits before restarting"],
               ["SB37 / SD37 / SE37", "Dataset out of space", "Extend or reallocate the dataset, then restart the step"],
               ["S806", "Module not found", "Check the load library concatenation and recent changes"],
               ["U4038", "Language Environment abend", "Check the job output for the originating message"],
               ["-911 / -913", "DB2 deadlock or timeout", "Check lock holders; restart after the conflicting work completes"]],
              widths=[3.0, 5.6, 8.0], caption="Abend reference", font_size=8.4)
    doc.ps(pr.paras(["ops2", "ops"], 2))

    doc.h(2, "7.4 Shift checklists")
    doc.table(["#", "Start of night shift"], [[str(i), c] for i, c in enumerate([
        "Read the handover notes and open incidents from the day shift.",
        "Confirm the business date on the Batch Scheduler.",
        "Check MQ channel status for the main interfaces.",
        "Confirm that no emergency changes are pending for the batch window.",
        "Check free space on the batch work volumes.",
        "Confirm that the online service has been closed for the batch window where required."], 1)],
              widths=[1.0, 15.6], font_size=8.6)
    doc.table(["#", "End of night shift"], [[str(i), c] for i, c in enumerate([
        "Confirm that every job in the nightly schedule has completed or is accounted for.",
        "Confirm that outbound interfaces have been delivered.",
        "Record abends, restarts and holds in the shift log.",
        "Raise incidents for any failure not yet resolved.",
        "Brief the day shift and the application on-call on open issues.",
        "Confirm the online service is available for the start of the business day."], 1)],
              widths=[1.0, 15.6], font_size=8.6)
    doc.ps(pr.paras(["ops2", "ops"], 2))

    # 8 Period end ------------------------------------------------------------------------
    doc.h(1, "8 Period-end processing", page_break=True)
    for title, names in [("8.1 Month-end", ["CLRMRSV1", "CLRMRSV2", "CLRMGL01", "CLRMRP01"]),
                         ("8.2 Quarter-end", ["CLRQRP01", "CLRQFR01"]),
                         ("8.3 Year-end", ["CLRYGL90"])]:
        doc.h(2, title)
        rows = []
        for n in names:
            j = W.jcl_jobs.get(n)
            if not j or j not in jobs:
                continue
            rows.append([n, clean_old(ctx, j["description"]), H.job_schedule(ctx, j) or "Operations schedule"])
        if rows:
            doc.table(["Job", "Description", "Schedule"], rows, widths=[2.6, 8.6, 5.4], font_size=8.6)
        doc.ps(pr.paras(["batch", "ops2"], 2))

    # 9 Incidents -------------------------------------------------------------------------
    doc.h(1, "9 Incident management")
    doc.table(["Severity", "Definition", "Response"],
              [["Sev1", "CLARA unavailable or reserve/payment data at risk", "Immediate; major incident process"],
               ["Sev2", "Critical job or interface failed; business impact at start of day likely", "Within 30 minutes"],
               ["Sev3", "Non-critical failure or degraded service", "Next working day"],
               ["Sev4", "Minor issue with no business impact", "Planned"]],
              widths=[2.0, 9.0, 5.6], caption="Incident severities", font_size=8.6)
    doc.h(2, "9.1 Recent incidents")
    rows = []
    for inc in W.incidents.values():
        if str(inc["date"]) > date or "SYS01" not in inc.get("systems", []) and "SYS14" not in inc.get("systems", []):
            continue
        rows.append([inc["id"], short_date(inc["date"]), inc["severity"], ctx.a(inc["title"]), inc.get("root_cause") or "—"])
    if rows:
        doc.table(["Incident", "Date", "Severity", "Title", "Root cause"], rows, widths=[2.6, 2.2, 1.6, 4.6, 5.6],
                  font_size=8.4)
    doc.ps(pr.paras(["ops2", "ops"], 2))

    # 10 DR -----------------------------------------------------------------------------
    doc.h(1, "10 Disaster recovery", page_break=True)
    doc.p("CLARA is recovered at the Bristol disaster recovery site if the Leeds data centre is unavailable. Recovery "
          "is invoked by the CLARA Platform Manager with the agreement of the Chief Information Officer.")
    doc.bullets(["Confirm the invocation decision and inform the service desk.",
                 "Bring up the DR environment and confirm DB2 recovery to the last consistent point.",
                 "Restart MQ channels to connected systems.",
                 "Re-run the nightly schedule from the first incomplete job.",
                 "Open the online service and confirm the main transactions with business users."], numbered=True)
    doc.ps(pr.paras(["ops", "ops2"], 2))

    # 11 Housekeeping -------------------------------------------------------------------
    doc.h(1, "11 Housekeeping and maintenance")
    j = W.jcl_jobs["CLRWCM01"]
    doc.p(f"Weekly housekeeping runs in job CLRWCM01 ({H.job_schedule(ctx, j) or 'operations schedule'}). Planned "
          f"maintenance of the CICS regions and DB2 is carried out in the weekly change window agreed with the Change "
          f"Advisory Board.")
    doc.ps(pr.paras(["ops", "batch"], 2))

    # 12 Monitoring -------------------------------------------------------------------
    doc.h(1, "12 Monitoring and alerts", page_break=True)
    doc.p("Operations monitor the batch schedule, the online service and the interfaces from the operations console. "
          "The table lists the standard alerts and the response expected from the operator.")
    doc.table(["Alert", "Meaning", "Operator response"],
              [["Job abend", "A job step ended abnormally", "Follow section 7; raise an incident"],
               ["Job late start", "A job has not started at its scheduled time", "Check predecessors and scheduler holds"],
               ["Job long running", "A job has run longer than usual", "Check for lock waits; inform application on-call"],
               ["MQ queue depth", "Messages are building up on an interface queue", "Check the receiving application and the channel"],
               ["MQ channel stopped", "A channel to a connected system has stopped", "Restart the channel; inform Integration Platform"],
               ["File transfer failed", "An outbound or inbound file was not delivered", "Retry once; inform the interface owner"],
               ["Transaction abend rate", "Online transactions are abending repeatedly", "Inform application on-call; consider disabling"],
               ["Region short on storage", "A CICS region is short on storage", "Inform application on-call; plan a recycle"]],
              widths=[3.6, 6.0, 7.0], caption="Standard alerts", font_size=8.6)
    doc.ps(pr.paras(["ops2", "ops", "online"], 3))
    doc.h(2, "12.1 Daily operations report")
    doc.p("At the end of each night the shift lead circulates the daily operations report to the CLARA support team, "
          "Claims Operations and the interface owners. It lists jobs that failed or ran late, restarts performed, "
          "interfaces delayed and open incidents.")
    doc.ps(pr.paras(["ops2", "batch"], 2))

    # 13 Change ------------------------------------------------------------------------
    doc.h(1, "13 Change and release")
    doc.p("Changes to CLARA programs, JCL and scheduler definitions are approved by the Change Advisory Board and "
          "implemented in the weekly change window. Emergency changes during the batch window need the approval of the "
          "CLARA Platform Manager and are reviewed at the next CAB.")
    doc.ps(pr.paras(["ops", "governance"], 3))

    # Appendices ----------------------------------------------------------------------
    doc.h(1, "Appendix A – Program index", page_break=True)
    rows = []
    for p in sorted(H.programs_asof(ctx), key=lambda x: x["id"]):
        runs = p.get("jcl_job") or p.get("cics_transaction") or ("called" if p.get("subprogram") else "—")
        rows.append([p["id"], clean_old(ctx, H.program_desc(ctx, p["id"])), p["type"], runs])
    doc.table(["Program", "Description", "Type", "Job / transaction"], rows, widths=[2.4, 9.4, 1.8, 3.0],
              caption="CLARA programs", font_size=7.8)
    doc.h(1, "Appendix B – DB2 tables", page_break=True)
    rows = []
    for t, tb in sorted(W.tables.items()):
        if tb.get("db") != "DB2" or not _table_ok(ctx, t):
            continue
        rows.append([t, clean_old(ctx, tb.get("description", "")), tb.get("area", "—")])
    doc.table(["Table", "Description", "Area"], rows, widths=[5.0, 9.4, 2.2], caption="CLARA tables", font_size=8.0)
    doc.h(1, "Appendix C – Table to job cross-reference", page_break=True)
    doc.p("For each table, the batch jobs whose programs update it. Use this list to judge which jobs are affected by a "
          "table lock or a data correction.")
    rows = []
    for t, tb in sorted(W.tables.items()):
        if tb.get("db") != "DB2" or not _table_ok(ctx, t):
            continue
        js = []
        for j in jobs:
            if any(t in (W.programs.get(s_["program"], {}).get("writes_tables", [])) for s_ in j["steps"]):
                js.append(j["name"])
        rows.append([t, ", ".join(js) or "Online only"])
    doc.table(["Table", "Jobs that update it"], rows, widths=[5.6, 11.0], font_size=8.2, caption="Table to job cross-reference")
    doc.h(1, "Appendix D – Copybooks", page_break=True)
    rows = []
    for name, cb in sorted(W.copybooks.items()):
        if name == "FRDNOT01":
            continue
        rows.append([name, cb.get("kind", ""), cb.get("table") or "—", clean_old(ctx, cb.get("description") or "")])
    doc.table(["Copybook", "Kind", "Table", "Description"], rows, widths=[2.6, 3.0, 4.6, 6.4], font_size=8.0,
              caption="Copybooks")
    doc.h(1, "Appendix E – Interface dependencies")
    rows = []
    for i in H.interfaces_asof(ctx):
        up = [d for d in i.get("depends_on", []) if str(W.interfaces[d]["since"]) <= date]
        down = [d for d in i.get("dependents", []) if str(W.interfaces[d]["since"]) <= date]
        if up or down:
            rows.append([i["id"], ", ".join(up) or "—", ", ".join(down) or "—"])
    doc.table(["Interface", "Depends on", "Feeds"], rows, widths=[3.0, 6.8, 6.8], font_size=8.4,
              caption="Interface dependencies")
    doc.h(1, "Appendix F – Screen reference", page_break=True)
    doc.p("Field layouts of the CLARA screens, for use when diagnosing user-reported problems with a transaction.")
    for m in W.bms_maps.values():
        p_ = W.programs.get(m["program"])
        if not p_ or str(p_["since"]) > date:
            continue
        doc.h(2, f"{m['map']} – {clean_old(ctx, m['title'])} ({m['transaction']})")
        doc.table(["Field", "Row", "Col", "Length", "Attribute"],
                  [[f["name"], str(f["row"]), str(f["col"]), str(f["length"]), f["attr"]] for f in m.get("fields", [])],
                  widths=[5.6, 2.0, 2.0, 2.4, 4.6], font_size=8.0)
    doc.h(1, "Appendix G – Glossary")
    doc.table(["Term", "Meaning"],
              [["Abend", "Abnormal end of a job step."], ["Business date", "The processing date held by the scheduler."],
               ["Completion record", "Row written at the end of a job that downstream jobs check before starting."],
               ["Shift log", "Operations log of events and actions during each shift."]]
              + [[t, ctx.a(m)] for t, m in C.glossary_terms(["G-020", "G-003", "G-013"])],
              widths=[3.6, 13.0], font_size=8.6)
    return doc


def post_check(doc, texts):
    from harness import extract as X
    bad = []
    for term in ("Sentinel", "Claims Hub", "CICSPRD", "CLRPLAN1", "DB2P", "Evidence Vault", "Assessor Portal", "Ashby",
                 "Programme Skerry", "reserve-svc"):
        pages = [i + 1 for i, t in enumerate(texts) if term in re.sub(r"\s+", " ", t)]
        if pages:
            bad.append(f"anachronism/exclusive term {term!r} on pages {pages[:8]}")
    restart = [i + 1 for i, t in enumerate(texts) if X.match("must not be rerun on the same business date", t)]
    return bad + [f"INFO restart instruction pages {restart}; total {len(texts)}"]

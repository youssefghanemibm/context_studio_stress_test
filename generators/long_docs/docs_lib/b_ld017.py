"""LD017 – CLARA System Specification v3.4 (DOCX, 2021-09-30, Keith Barraclough)."""
from __future__ import annotations

import re

from . import common as C
from . import hub as H
from .core import Ctx, Doc, F, PF, Style, W, long_date, util
from .prose import Prose

FID = "LD017"
DENS = 2

SUBPROG = {
    "CLRCM010": "business-day calculation", "CLRCM020": "audit trail writing", "CLRCM030": "currency conversion",
    "CLRCM040": "parameter lookup", "CLRCM050": "error handling", "CLRCM060": "code lookup",
    "CLRCM070": "user authority checking", "CLRCM080": "notes", "CLRCM090": "diary entries",
    "CLRCM100": "document references", "CLRCM110": "MQ puts", "CLRCM120": "MQ gets", "CLRRS015": "reserve authority checking",
}


def clean_old(ctx: Ctx, text: str) -> str:
    """Remove references that post-date the document (Claims Hub, later tickets, rules not yet in force)."""
    t = ctx.a(text or "")
    t = re.sub(r"\s*\(queue CLR\.RSVMOVE\.OUT\)", "", t)   # queue name belongs with the CLX-IF-042 label (VS033)
    t = re.sub(r";?\s*shown in Claims Hub as [^;,)]*", "", t)
    t = re.sub(r"\s*\([^)]*(Claims Hub|CHUB-|reserve-engine|202[2-9])[^)]*\)", "", t)

    def _rule_ok(m):
        rid = m.group(0)
        r = W.rules.get(rid)
        if not r:
            return rid
        first = min((v.get("effective_from") or "9999") for v in r["versions"])
        return rid if first <= ctx.date else ""
    t = re.sub(r"BR-[A-Z]+-\d{3}", _rule_ok, t)
    t = re.sub(r"\(\s*\)", "", t).replace("( ", "(").replace(" )", ")")
    return re.sub(r"\s{2,}", " ", t).strip(" ;,")


def _processing(ctx, p, rng) -> str:
    reads = [t for t in p["reads_tables"] if t != "CLR.T_FRAUD_NOTIFICATION"]
    writes = [t for t in p["writes_tables"] if t != "CLR.T_FRAUD_NOTIFICATION"]
    calls = [c for c in p["calls_programs"] if c in W.programs and str(W.programs[c]["since"]) <= ctx.date]
    parts = []
    if p["type"] == "online":
        opener = rng.choice(["The program is started from its CICS transaction and receives the claim context in the COMMAREA.",
                             "On entry the program validates the COMMAREA passed by the calling transaction.",
                             "The program runs as a pseudo-conversational CICS task.",
                             "The program is invoked online and returns control to CICS at the end of each interaction."])
        if p.get("subprogram"):
            opener = rng.choice(["The program is a called subprogram with no screen of its own.",
                                 "This is a called routine; it is linked to by other online programs."])
    else:
        opener = rng.choice([f"The program runs as a step of job {p.get('jcl_job')}.",
                             f"The program is executed in batch under job {p.get('jcl_job')} and commits at regular intervals.",
                             f"This batch program is scheduled through job {p.get('jcl_job')}."])
    parts.append(opener)
    if reads:
        parts.append(rng.choice(["It reads {}.", "Input is taken from {}.", "The program selects rows from {}."]).format(_and(reads)))
    if writes:
        parts.append(rng.choice(["It inserts or updates rows in {}.", "Output is written to {}.", "The program updates {}."]).format(_and(writes)))
    else:
        parts.append(rng.choice(["It does not update any table.", "The program is read-only."]))
    if calls:
        named = [f"{c} ({SUBPROG[c]})" if c in SUBPROG else c for c in calls]
        parts.append(rng.choice(["It calls {}.", "Common services used: {}.", "The program links to {}."]).format(_and(named)))
    return " ".join(parts)


def _and(xs):
    xs = list(xs)
    return xs[0] if len(xs) == 1 else ", ".join(xs[:-1]) + " and " + xs[-1]


def build() -> Doc:
    ctx = Ctx(FID)
    date = ctx.date
    pr = Prose(util.rng(f"{FID}:prose"), date=ctx.date, forbid=("Claims Hub", "the Hub", "migration", "event backbone", "Kafka"))
    clara = W.systems["SYS01"]
    doc = Doc(ctx, title="CLARA System Specification", doc_id="CLR-SPEC-003", version="3.4", status="Approved (2021)",
              subtitle="Claims Ledger And Reserve Application – functional and technical specification",
              style=Style(font="Times New Roman", heading_font="Arial", accent="333333", accent2="E7E6E6", size=11),
              header_left="CLARA System Specification v3.4", header_right="CLR-SPEC-003 – Legacy Claims Platforms")
    doc.footer_facts.append(F("footer", "The CLARA specification footer shows its classification (Internal).", "Classification: Internal",
                              f"ANCHOR:{FID}"))
    doc.title_page(C.control_rows(ctx, doc, owner="P016", extra=[["System", "CLARA (SYS01)"],
                                                                 ["Go-live", long_date(clara["go_live"])]]),
                   facts=[F("general", "CLARA went live on 3 October 1994.", long_date(clara["go_live"]), "SYSTEM:SYS01#go_live",
                            where=(9, 1))])
    C.version_history(ctx, doc, [("3.0", 980, "Restructured specification; batch schedule moved to section 6"),
                                 ("3.1", 760, "Linked-claims detection and fraud MI programs"),
                                 ("3.2", 520, "Interface log housekeeping and archive programs"),
                                 ("3.3", 230, "Currency rates feed from the Group Ledger"),
                                 ("3.4", 0, "Annual review; tiering section rewritten")])
    C.approvals(ctx, doc, [("P016", "System owner"), ("P011", "Business owner (Claims)"), ("P006", "Chief Information Officer")])
    doc.toc(depth=2)

    # 1 ----------------------------------------------------------------------------------
    doc.h(1, "1 Introduction")
    doc.p("This specification describes CLARA, Corvane's claims ledger and reserve application, as at the date of this "
          "version. It covers the runtime environment, the business logic, every production program, the DB2 tables, "
          "the nightly and periodic batch schedule and the interfaces to other systems.")
    doc.p(f"CLARA was built in 1994 and went live on {long_date(clara['go_live'])}. It is the system of record for "
          f"claims, case reserves, fraud referrals, payments and recoveries.")
    doc.ps(pr.paras(["intro", "governance"], 2, topic="the CLARA specification"))
    doc.h(2, "1.1 Conventions")
    doc.p("Program names follow the pattern CLR + area + three digits (for example CLRRS110). Job names use CLR + a "
          "frequency letter (N nightly, W weekly, M monthly, Q quarterly, Y yearly) + area. Tables are in the CLR schema.")
    doc.h(2, "1.2 Functional areas")
    areas = sorted({p["area"] for p in H.programs_asof(ctx)})
    doc.table(["Area", "Programs"], [[a, str(len(H.programs_asof(ctx, a)))] for a in areas], widths=[6, 4],
              caption="Programs by area")

    # 2 ----------------------------------------------------------------------------------
    doc.h(1, "2 Runtime environment", page_break=True)
    doc.h(2, "2.1 Runtime")
    ctx.need("SYSTEM:SYS01", "cics_regions")
    reg = clara["cics_regions"]
    doc.p(f"CLARA's online programs run under CICS Transaction Server on z/OS LPAR PRD1 in the Leeds Data Centre. Two "
          f"production CICS regions are used: CICSPRD1 ({reg['CICSPRD1']}) and CICSPRD2 ({reg['CICSPRD2']}). Batch "
          f"programs run under the Batch Scheduler outside the online day.",
          facts=[PF(ctx, "ld17_cics", "CICSPRD1 (online claims (FNOL, triage, assessment, reserving)) and CICSPRD2 (fraud, settlement and recoveries)")])
    doc.ps(pr.paras(["arch", "ops"], 2, svc="CLARA"))
    doc.h(2, "2.2 Online transactions")
    rows = [[p["cics_transaction"], p["id"], clean_old(ctx, H.program_desc(ctx, p["id"])), p.get("bms_map") or "—"]
            for p in H.programs_asof(ctx) if p.get("cics_transaction")]
    doc.table(["Transaction", "Program", "Function", "BMS map"], rows, widths=[2.4, 2.6, 9.0, 2.6], font_size=8.4,
              caption="CICS transactions",
              facts=[F("general", "CICS transaction RS01 runs CLRRS010 (initial reserve set).", "Initial reserve set",
                       "PROGRAM:CLRRS010#cics_transaction", where=(next(i for i, r in enumerate(rows, 1) if r[1] == "CLRRS010"), 2))])
    doc.h(2, "2.3 Database")
    ctx.need("SYSTEM:SYS01", "db2_plan")
    doc.p(f"All CLARA data is held in DB2 for z/OS. Programs connect to DB2 subsystem {clara['db2_subsystem']} with plan "
          f"{clara['db2_plan']}; static SQL packages are bound into the plan at each release. Tables are owned by the CLR "
          f"schema.",
          facts=[PF(ctx, "ld17_db2plan", f"DB2 subsystem {clara['db2_subsystem']} with plan {clara['db2_plan']}")])
    doc.ps(pr.paras(["data", "batch"], 2))
    doc.h(2, "2.4 Messaging")
    doc.p(f"Message-based interfaces use IBM MQ through queue manager {clara['mq_queue_manager']}. Programs put and get "
          f"messages through the wrappers CLRCM110 and CLRCM120.",
          facts=[F("general", "CLARA uses MQ queue manager CLRQM01.", f"queue manager {clara['mq_queue_manager']}",
                   "SYSTEM:SYS01#mq_queue_manager")])
    doc.h(2, "2.5 Batch")
    doc.p(f"Batch jobs are driven by the Batch Scheduler. The nightly batch window runs {clara['batch_window']}; "
          f"monthly, quarterly and year-end jobs run in addition to the nightly schedule.")
    doc.h(2, "2.6 Hosting and recovery")
    doc.p(f"Production runs on {clara['hosting']}.")
    doc.ps(pr.paras(["ops", "security"], 2))

    # 3 ----------------------------------------------------------------------------------
    doc.h(1, "3 Business logic", page_break=True)
    doc.h(2, "3.1 Claim lifecycle")
    st = next(c for c in W.tables["CLR.T_CLAIM"]["columns"] if c["name"] == "CLAIM_STATUS")
    doc.p(f"A claim is created at FNOL by CLRFN030, which also writes the default reserve. Claim status values are: "
          f"{st['description'].split('(')[1].rstrip(')')}.")
    doc.ps(pr.paras(["data", "opmodel"], 2))
    doc.h(2, "3.2 Tiering")
    # BR-TRI-003 v1 (£25,000) is in force on 2021-09-30; v2 (£40,000, C10) was approved before this version of the
    # specification and takes effect on 2022-01-01, so the rewritten tiering section states v2 with its date.
    t_in = ctx.rule("BR-TRI-003")
    t_v2 = W.rules["BR-TRI-003"]["versions"][1]
    assert t_in["version"] == 1 and str(t_v2["approved_on"]) <= date < str(t_v2["effective_from"])
    v2, v1p = t_v2["parameters"], t_in["parameters"]
    doc.p(f"CLRTR020 classifies every claim when it is created and again whenever the estimate changes. From "
          f"{long_date(t_v2['effective_from'])} (BR-TRI-003 v2, approved {long_date(t_v2['approved_on'])}) a claim is "
          f"Tier-3 at an estimated incurred of £{v2['tier3_min_gbp']:,} or more (NOK {v2['tier3_min_nok']:,} / "
          f"SEK {v2['tier3_min_sek']:,} / DKK {v2['tier3_min_dkk']:,}), or where any bodily injury is notified. Tier-2 "
          f"covers £{v2['tier2_min_gbp']:,}–£{v2['tier3_min_gbp'] - 1:,} or any third-party involvement; all other claims "
          f"are Tier-1. Until then BR-TRI-003 v1 applies: Tier-3 at £{v1p['tier3_min_gbp']:,} or more or any bodily "
          f"injury, Tier-2 £{v1p['tier2_min_gbp']:,}–£{v1p['tier3_min_gbp'] - 1:,}. Tier overrides are entered through "
          f"CLRTR030 with a reason code.",
          facts=[PF(ctx, "ld17_t3_40k", f"Tier-3 at an estimated incurred of £{v2['tier3_min_gbp']:,} or more")])
    doc.p("Tier-3 claims are routed to Major & Complex Loss and raise a major loss alert through CLRTR090.")
    doc.ps(pr.paras(["opmodel", "data"], 1))
    doc.h(2, "3.3 Reserving")
    writers = sorted(W.tables["CLR.T_RESERVE"]["writers"])
    doc.p("Case reserves are held in CLR.T_RESERVE, one row per claim per reserve type, and every change is recorded in "
          "CLR.T_RESERVE_MOVEMENT. The following programs update CLR.T_RESERVE: " + ", ".join(writers) + ". CLRRS150 "
          "corrects movements only and does not update CLR.T_RESERVE.",
          facts=[F("general", "As at 2021, eight programs update CLR.T_RESERVE (including CLRGL090).", ", ".join(writers),
                   "TABLE:CLR.T_RESERVE#writers")])
    r007 = ctx.rule("BR-RSV-007")
    doc.p(f"Tier-3 reserves are reviewed by the scheduler program CLRRS110 in job CLRNRSV1. {r007['text']} "
          f"(BR-RSV-007 v{r007['version']}).",
          facts=[F("temporal", "In 2021 Tier-3 reserves had to be reviewed at least every 30 days (BR-RSV-007 v1).",
                   r007["text"], f"RULE:BR-RSV-007@v{r007['version']}#text")])
    r003 = ctx.rule("BR-RSV-003")
    doc.p(f"Reserve authority is checked by CLRRS015 (BR-RSV-003 v{r003['version']}): {r003['text']}")
    doc.ps(pr.paras(["data", "batch"], 1))
    doc.h(2, "3.4 Fraud referral")
    r012 = ctx.rule("BR-FRD-012")
    r019 = ctx.rule("BR-FRD-019")
    doc.p(f"Every claim is scored by FRAUDNET online (CLRFR020) and in the nightly batch (CLRFR110). {r012['text']} "
          f"(BR-FRD-012 v{r012['version']}). Referrals are created online by CLRFR030, which reads the threshold from "
          f"CLR.T_PARAM key FRD_REFER_THRESH, and by the nightly sweep CLRFR040.",
          facts=[F("temporal", "In 2021 claims were referred to SIU at a FRAUDNET score of 75 or more (BR-FRD-012 v1).",
                   "FRAUDNET score is 75 or more", "RULE:BR-FRD-012@v1#parameters.threshold")])
    doc.p(f"{r019['text']} (BR-FRD-019 v{r019['version']}); the decline sweep is CLRFR140 in job CLRNFR99.")
    doc.h(2, "3.5 Settlement and payments")
    r002 = ctx.rule("BR-STL-002")
    doc.p(f"Payment authority is enforced by CLRST020 (BR-STL-002 v{r002['version']}): {r002['text']}",
          facts=[F("temporal", "In 2021 the Team Leader payment authority was £25,000 (BR-STL-002 v1).", "Team Leader £25,000",
                   "RULE:BR-STL-002@v1#parameters.team_leader")])
    doc.p("Payment batches are built by CLRST030 and sent to the Corvane Payments Gateway; confirmations are imported by "
          "CLRST050. Payees are screened through WatchScreen by CLRST070 before release.")
    doc.h(2, "3.6 Recoveries")
    r_rec = ctx.rule("BR-REC-003")
    doc.p(f"{r_rec['text']} (BR-REC-003 v{r_rec['version']}). Subrogation cases are opened by CLRRC020 and synchronised "
          f"with SUBTRAK by CLRRC040. Recovery receipts are posted by CLRRC050, which nets recoveries from the case reserve.")
    doc.h(2, "3.7 General ledger and reinsurance")
    doc.p("Payment postings are extracted daily by CLRGL010. Reserve movements are extracted nightly by CLRRS170 and "
          "consumed by the general ledger, the Claims Data Warehouse and reinsurance through the MQ Backbone. Year-end "
          "revaluation of Nordic reserves into sterling is performed by CLRGL090 (job CLRYGL90).")
    doc.h(2, "3.8 Business rules implemented in CLARA")
    rows = []
    for rid, r in sorted(W.rules.items()):
        progs = [p for p in (r.get("implemented_in", {}) or {}).get("programs", []) if p in W.programs and str(W.programs[p]["since"]) <= date]
        if not progs:
            continue
        v = ctx.rule(rid)
        if not v:
            continue
        ref = f"RULE:{rid}@v{v['version']}"
        if rid == "BR-TRI-003" or not (ctx.ok(ref, "text") and ctx.ok(ref, "parameters")):
            text = "See section 3.2." if rid == "BR-TRI-003" else "Parameters held in CLR.T_PARAM."
        else:
            text = ctx.a(v["text"])
        rows.append([rid, f"v{v['version']}", text, ", ".join(progs)])
    doc.table(["Rule", "Version", "Rule as implemented", "Programs"], rows, widths=[2.2, 1.4, 9.8, 3.2], font_size=7.8,
              caption="Business rules in force and implementing programs")

    # 4 ----------------------------------------------------------------------------------
    doc.h(1, "4 Program descriptions", page_break=True)
    doc.p("Each production program is described below. Tables read and written are those accessed through static SQL; "
          "called programs are those invoked by CALL or EXEC CICS LINK.")
    rng_p = util.rng(f"{FID}:proc")
    for area in areas:
        doc.h(2, f"4.{areas.index(area) + 1} {area} programs")
        for p in H.programs_asof(ctx, area):
            doc.h(3, f"{p['id']} – {clean_old(ctx, H.program_desc(ctx, p['id']))}")
            facts = []
            kv = [["Type", p["type"] + (" (called subprogram)" if p.get("subprogram") else "")],
                  ["Transaction / job", p.get("cics_transaction") or p.get("jcl_job") or "—"],
                  ["BMS map", p.get("bms_map") or "—"],
                  ["Tables read", ", ".join(t for t in p["reads_tables"] if t != "CLR.T_FRAUD_NOTIFICATION") or "—"],
                  ["Tables written", ", ".join(t for t in p["writes_tables"] if t != "CLR.T_FRAUD_NOTIFICATION") or "—"],
                  ["Calls", ", ".join(c for c in p["calls_programs"] if c in W.programs and str(W.programs[c]["since"]) <= date) or "—"],
                  ["Copybooks", ", ".join(H.copybooks_asof(ctx, p)) or "—"],
                  ["Lines of code", f"{p['loc']:,}"], ["In production since", long_date(p["since"])]]
            if p["id"] == "CLRGL090":
                facts.append(F("general", "CLRGL090 writes CLR.T_RESERVE (year-end revaluation).", "CLR.T_RESERVE",
                               "PROGRAM:CLRGL090#writes_tables:CLR.T_RESERVE", where=(4, 1)))
            if p["id"] == "CLRRS150":
                facts.append(F("general", "CLRRS150 writes only CLR.T_RESERVE_MOVEMENT.", "CLR.T_RESERVE_MOVEMENT",
                               "PROGRAM:CLRRS150#writes_tables", where=(4, 1)))
            if p["id"] == "CLRFN030":
                facts.append(F("general", "CLRFN030 writes CLR.T_CLAIM, CLR.T_RESERVE and CLR.T_RESERVE_MOVEMENT.",
                               "CLR.T_CLAIM, CLR.T_RESERVE, CLR.T_RESERVE_MOVEMENT", "PROGRAM:CLRFN030#writes_tables", where=(4, 1)))
            doc.kv(kv, widths=(3.6, 13.0), font_size=8.4, facts=facts)
            if p.get("notes") and p["id"] in ("CLRRS150", "CLRST040", "CLRRC050"):
                doc.p(clean_old(ctx, p["notes"]))
            doc.p(_processing(ctx, p, rng_p))
            rl = H.rules_for_program(ctx, p["id"])
            rl = [r for r in rl if r[0] != "BR-TRI-003" or True]
            if rl:
                doc.p("Business rules implemented: " + "; ".join(f"{r} ({ctx.a(t)}, v{v})" for r, t, v in rl) + ".")
            ifs = H.interfaces_for_program(ctx, p["id"])
            if ifs:
                doc.p("Interfaces: " + "; ".join(f"{i['id']} {clean_old(ctx, i['name'])}" for i in ifs) + ".")
            if DENS:
                doc.p(pr.sentence("batch" if p["type"] == "batch" else "arch", svc=p["id"]) + " " +
                      pr.sentence("data", svc=p["id"]) + " " + pr.sentence("ops" if p["type"] == "batch" else "security", svc=p["id"]))
                doc.p(pr.para(["ops", "data", "governance"] if p["type"] == "batch" else ["arch", "data", "security"], n=(3, 4), svc=p["id"]))
            if DENS >= 2 and p["area"] in ("RESERVE", "FRAUD", "SETTLE", "RECOVER", "GL", "TRIAGE"):
                doc.p(pr.para(["batch", "integration"] if p["type"] == "batch" else ["arch", "integration"], n=(3, 4), svc=p["id"]))

    # 5 ----------------------------------------------------------------------------------
    doc.h(1, "5 Table descriptions", page_break=True)
    for tn in sorted(W.tables):
        t = W.tables[tn]
        if t["db"] != "DB2" or (t.get("created") and t["created"] > date):
            continue
        doc.h(2, f"5.{sorted(x for x in W.tables if W.tables[x]['db'] == 'DB2' and not (W.tables[x].get('created') and W.tables[x]['created'] > date)).index(tn) + 1} {tn}")
        doc.p(f"{clean_old(ctx, t['description'])}. Primary key: {', '.join(t.get('primary_key', []))}."
              + (f" Record layout: copybook {t['copybook']}." if t.get("copybook") else ""))
        cols = t["columns"]   # no column history in the world: every document lists tables.yaml (fix pass, N22)
        doc.table(["Column", "Type", "Null", "Description"],
                  [[c["name"], c["type"] + (f"({c['length']}{',' + str(c['scale']) if c.get('scale') else ''})" if c.get("length") else ""),
                    "Y" if c.get("nullable") else "N", clean_old(ctx, H.col_desc(ctx, c["description"]))] for c in cols],
                  widths=[4.4, 2.8, 1.0, 8.4], font_size=7.8)
        writers_t = [w for w in t.get("writers", []) if str(W.programs[w]["since"]) <= date]
        readers_t = [w for w in t.get("readers", []) if str(W.programs[w]["since"]) <= date]
        doc.p(f"Updated by: {', '.join(writers_t) or 'none (reference data maintained by DBA)'}. "
              f"Read by: {', '.join(readers_t) or '—'}.", size=9)
        doc.p(pr.para(["data", "batch"], n=(3, 4)))

    # 6 ----------------------------------------------------------------------------------
    doc.h(1, "6 Batch schedule", page_break=True)
    doc.p(f"The table lists the production batch jobs, their schedules and steps. The nightly window runs "
          f"{clara['batch_window']}. Jobs marked 'operations schedule' are scheduled by event in the Batch Scheduler and "
          f"are documented in the operations runbook.")
    rows, facts = [], []
    for j in H.jobs_asof(ctx):
        sch = H.job_schedule(ctx, j) or "Operations schedule"
        rows.append([j["name"], ctx.a(j["description"]) if j["name"] != "CLRNFR99" else "Auto-decline sweep", sch,
                     "; ".join(f"{s['step']} {s['program']}" for s in j["steps"])])
        if j["name"] == "CLRNRSV1":
            facts.append(F("general", "Job CLRNRSV1 runs daily at 01:30.", "daily 01:30", "JCL:CLRNRSV1#schedule",
                           where=(len(rows), 2)))
        if j["name"] == "CLRYGL90":
            facts.append(F("general", "Job CLRYGL90 runs annually on 31 December at 23:30 (and on Reserving request).",
                           sch, "JCL:CLRYGL90#schedule", where=(len(rows), 2)))
        if j["name"] == "CLRNFR99":
            facts.append(F("temporal", "In 2021 the auto-decline sweep job CLRNFR99 ran daily at 00:45.", "daily 00:45",
                           "JCL:CLRNFR99#schedule", where=(len(rows), 2)))
    doc.table(["Job", "Description", "Schedule", "Steps"], rows, widths=[2.2, 5.2, 4.0, 5.2], font_size=8.0,
              caption="Production batch schedule", facts=facts)
    for j in H.jobs_asof(ctx):
        doc.h(2, f"6.{H.jobs_asof(ctx).index(j) + 1} {j['name']}")
        doc.table(["Step", "Program", "Function"],
                  [[s["step"], s["program"], clean_old(ctx, H.program_desc(ctx, s["program"]))] for s in j["steps"]],
                  widths=[2.0, 2.6, 12.0], font_size=8.4)
        doc.p(pr.para(["batch", "ops"], n=(3, 4)))

    # 7 ----------------------------------------------------------------------------------
    doc.h(1, "7 Interfaces", page_break=True)
    rows = []
    for i in H.interfaces_asof(ctx):
        sch = H.iface_schedule(ctx, i["id"]) or "Operations schedule"
        rows.append([i["id"], clean_old(ctx, i["name"]), ctx.sys(i["source_system"]), ctx.sys(i["target_system"]),
                     i["protocol"], sch])
    doc.table(["ID", "Name", "From", "To", "Protocol", "Schedule"], rows, widths=[2.0, 4.6, 2.8, 2.8, 1.6, 2.8],
              font_size=7.8, caption="Interfaces",
              facts=[F("temporal", "In 2021 CLX-IF-043 (GL reserve journals) ran daily at 03:00.", "daily 03:00",
                       "INTERFACE:CLX-IF-043#schedule_history",
                       where=(next(k for k, r in enumerate(rows, 1) if r[0] == "CLX-IF-043"), 5))])
    doc.ps(pr.paras("integration", 2))

    # 8 ----------------------------------------------------------------------------------
    doc.h(1, "8 Copybooks and screen maps", page_break=True)
    rows = []
    for name, cb in sorted(W.copybooks.items()):
        if name == "FRDNOT01":
            continue
        tbl = cb.get("table") or "—"
        rows.append([name, cb.get("kind", ""), tbl, clean_old(ctx, cb.get("description") or "")])
    doc.table(["Copybook", "Kind", "Table", "Description"], rows, widths=[2.6, 3.0, 4.6, 6.4], font_size=8.0,
              caption="Copybooks")
    rows = [[m["map"], m["mapset"], m["program"], m["transaction"], clean_old(ctx, m["title"])]
            for m in W.bms_maps.values() if m["program"] in W.programs and str(W.programs[m["program"]]["since"]) <= date]
    doc.table(["Map", "Mapset", "Program", "Transaction", "Title"], rows, widths=[2.4, 2.4, 2.6, 2.4, 6.8], font_size=8.2,
              caption="BMS maps")
    doc.h(2, "8.1 Screen layouts")
    for m in W.bms_maps.values():
        if m["program"] not in W.programs or str(W.programs[m["program"]]["since"]) > date:
            continue
        doc.h(3, f"{m['map']} – {clean_old(ctx, m['title'])} ({m['transaction']})")
        doc.table(["Field", "Row", "Col", "Length", "Attribute"],
                  [[f["name"], str(f["row"]), str(f["col"]), str(f["length"]), f["attr"]] for f in m.get("fields", [])],
                  widths=[5.6, 2.0, 2.0, 2.4, 4.6], font_size=8.0)
    doc.h(2, "8.2 Key record layouts")
    for cbn in ["RSVREC", "RSVMVT01", "RSVMOVE", "CLRCLM01", "FRDREF01", "PAYREC01", "SUBCAS01", "RCVREC01", "CLRCOMM1", "PARMREC1"]:
        cb = W.copybooks.get(cbn)
        if not cb:
            continue
        fields = [f for f in cb.get("fields", []) if not (cbn == "RSVMOVE" and f["name"] == "RM-REC-VERSION")]
        facts = []
        if cbn == "RSVMOVE":
            k = next(i for i, f in enumerate(fields, 1) if f["name"] == "RM-AMOUNT")
            facts.append(F("temporal", "In 2021 RSVMOVE field RM-AMOUNT was PIC S9(9)V99 COMP-3 (before the 2025 widening).",
                           "S9(9)V99 COMP-3", "COPYBOOK:RSVMOVE#field_history", where=(k, 2)))
        doc.h(3, f"{cbn} – {clean_old(ctx, cb.get('description') or cb.get('table') or '')}")
        doc.table(["Level", "Field", "PIC"], [[str(f["level"]).zfill(2), f["name"], f.get("pic") or "group"] for f in fields],
                  widths=[1.6, 8.0, 7.0], font_size=8.0, facts=facts)
    doc.h(1, "9 Operational parameters", page_break=True)
    doc.p("Business parameters are held in CLR.T_PARAM with validity dates and read through CLRCM040. The rows in force "
          "at the date of this specification are listed below.")
    rows, facts = [], []
    for r in W.tables["CLR.T_PARAM"]["param_rows"]:
        if not ctx.ok("TABLE:CLR.T_PARAM", f"param_rows:{r['key']}"):
            continue
        if r["valid_from"] <= date and (not r["valid_to"] or r["valid_to"] >= date):
            rows.append([r["key"], r["value"], r["valid_from"], r["valid_to"] or "—", r["rule"].split("@")[0]])
            if r["key"] == "FRD_REFER_THRESH":
                facts.append(F("temporal", "In 2021 CLR.T_PARAM FRD_REFER_THRESH was 75 (valid 2019-01-01 to 2023-03-31).",
                               "75", "TABLE:CLR.T_PARAM#param_rows:FRD_REFER_THRESH", where=(len(rows), 1)))
    doc.table(["Key", "Value", "Valid from", "Valid to", "Rule"], rows, widths=[4.4, 2.4, 3.0, 3.0, 3.8], font_size=8.6,
              caption="CLR.T_PARAM rows in force", facts=facts)
    doc.ps(pr.paras(["data", "governance"], 2))
    doc.h(1, "10 Non-functional characteristics")
    for t in ("Availability", "Performance", "Capacity", "Recoverability", "Security"):
        doc.h(2, f"10.{['Availability', 'Performance', 'Capacity', 'Recoverability', 'Security'].index(t) + 1} {t}")
        doc.ps(pr.paras(["ops", "batch", "security"], 2, n=(3, 4)))
    doc.h(1, "11 Error handling and audit")
    doc.p("All online programs route errors through CLRCM050, which formats the abend information and writes it to the "
          "CICS transient data queue for operations. Changes to claims, reserves and payments are written to CLR.T_AUDIT "
          "by CLRCM020.")
    doc.ps(pr.paras(["ops", "security"], 2))
    H.apply_program_renames(doc)   # FNETCAL1 / FNETREF1 until the 2025-03-01 rename
    return doc

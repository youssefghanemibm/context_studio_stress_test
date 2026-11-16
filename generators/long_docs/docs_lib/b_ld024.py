"""LD024 – Internal Audit Report – Reserving Controls 2025 (reportlab PDF, 2025-11-28, final)."""
from __future__ import annotations

from . import common as C
from .core import Ctx, Doc, F, PF, Style, W, long_date, short_date, util
from .prose import Prose

FID = "LD024"
PAD_SCOPE = 4         # filler paragraphs in section 3, tuned so that IA-25-07 starts on page 12

RATINGS = [("Red", "A significant control weakness that exposes the Society to material risk; immediate action required."),
           ("Amber", "A control weakness that should be addressed promptly; risk is moderate or could become material."),
           ("Green", "An improvement opportunity; risk exposure is limited.")]


def _rsv_rules(ctx: Ctx) -> list[tuple[str, int, str, str]]:
    out = []
    for rid, r in W.rules.items():
        if not rid.startswith("BR-RSV-"):
            continue
        v = ctx.rule(rid)
        if not v:
            continue
        ref = f"RULE:{rid}@v{v['version']}"
        if not (ctx.ok(ref, "text") and ctx.ok(ref, "parameters")):
            continue
        out.append((rid, v["version"], r["title"], _rsv012(ctx, v["text"])))
    return out


def _rsv012(ctx, text: str) -> str:
    """BR-RSV-012 v1 mentions the reserve-engine revaluation run decided in ADR-028 (2026-03-09)."""
    if ctx.date < "2026-03-09":
        text = text.replace("; reserve-engine revaluation runs from Wave 2", "")
    return text


def build() -> Doc:
    ctx = Ctx(FID)
    date = ctx.date
    pr = Prose(util.rng(f"{FID}:prose"), date=ctx.date)
    doc = Doc(ctx, title="Internal Audit Report – Reserving Controls 2025", doc_id="IA-2025-RSV", version="Final",
              status="Final", subtitle="Case reserve controls in CLARA and the reserving process",
              style=Style(accent="1B4F72", accent2="D6EAF8", size=11.2),
              header_left="Corvane Mutual – Internal Audit", header_right="IA-2025-RSV – Reserving Controls 2025 (Final)",
              footer_left="Restricted – Audit Committee and named recipients", classification="Restricted")
    doc.title_page([["Report", "IA-2025-RSV – Reserving Controls 2025"], ["Status", "Final"],
                    ["Report date", long_date(date)], ["Issued by", ctx.person("P007")],
                    ["Audit sponsor", ctx.person("P009")],
                    ["Distribution", f"{ctx.person('P003')}; {ctx.person(ctx.holder('the CFO'))}; {ctx.person('P005')}; "
                                     f"{ctx.person('P009')}; {ctx.person('P016')}; {ctx.person('P021')}; Audit Committee"],
                    ["Fieldwork", "September to October 2025"], ["Classification", "Restricted"]])
    doc.toc(depth=2)

    # 1 Executive summary ------------------------------------------------------------------
    doc.h(1, "1 Executive summary")
    doc.p("This report sets out the results of Internal Audit's review of the controls over case reserves in CLARA and "
          "in the reserving process. The audit formed part of the 2025 internal audit plan approved by the Audit "
          "Committee.")
    doc.h(2, "1.1 Overall opinion")
    doc.p("Overall, the design of reserve controls is adequate, but the audit identified weaknesses in the audit trail "
          "for system-generated reserve changes, in the documentation of the programs that update reserves and in the "
          "evidencing of reserve reviews. The overall rating is **Amber – requires improvement**.")
    doc.ps(pr.paras(["audit", "audit2"], 1))
    doc.h(2, "1.2 Summary of findings")
    summary = [["IA-25-05", "Evidence of Tier-3 reserve reviews", "Amber", ctx.name("P009")],
               ["IA-25-06", "Program documentation for reserve updates", "Amber", ctx.name("P016")],
               ["IA-25-07", "Year-end revaluation not recorded as reserve movements", "Amber", ctx.name("P016")],
               ["IA-25-08", "Interface change control for the reserve movement extract", "Green", ctx.name("P031")],
               ["IA-25-09", "Reserve correction utility usage", "Green", ctx.name("P009")],
               ["IA-25-10", "Large loss notification evidence", "Green", ctx.name("P038")]]
    doc.table(["Ref", "Finding", "Rating", "Action owner"], summary, widths=[2.2, 9.0, 2.0, 3.4],
              caption="Findings", font_size=8.8)
    doc.p("Management has accepted all findings. Agreed actions, owners and target timescales are set out with each "
          "finding in section 4.")
    doc.ps(pr.paras(["audit2"], 1))

    # 2 Background -------------------------------------------------------------------------
    doc.h(1, "2 Background", page_break=True)
    doc.p(f"Case reserves are held in CLARA in the table CLR.T_RESERVE, one row per claim per reserve type. Every change "
          f"to a reserve is expected to be recorded in CLR.T_RESERVE_MOVEMENT, which is the audit trail of reserve "
          f"changes and the source of the daily reserve movement extract to the general ledger, the data warehouse and "
          f"reinsurance. The Reserving stage of the claims process has been owned by the Head of Reserving, "
          f"{ctx.name('P009')}, since {long_date('2025-09-01')}.")
    doc.ps(pr.paras(["audit", "data"], 2))
    doc.h(2, "2.1 Programs that update reserves")
    doc.p("CLARA contains eight programs that update CLR.T_RESERVE. One further program, the reserve movement "
          "correction utility CLRRS150, writes movements only and does not update CLR.T_RESERVE.")
    rows = []
    for pid in W.reserve_writers:
        p = W.programs[pid]
        rows.append([pid, p["description"], p["type"], "Yes" if "CLR.T_RESERVE_MOVEMENT" in p["writes_tables"] else "No"])
    p150 = W.programs["CLRRS150"]
    rows.append(["CLRRS150", p150["description"], p150["type"], "Yes (movements only)"])
    doc.table(["Program", "Description", "Type", "Writes CLR.T_RESERVE_MOVEMENT"], rows, widths=[2.4, 8.2, 1.8, 4.2],
              caption="Programs updating CLR.T_RESERVE", font_size=8.6,
              facts=[F("needle", "Eight CLARA programs write CLR.T_RESERVE, including CLRGL090 (year-end revaluation).",
                       "CLRGL090", "PROGRAM:CLRGL090#writes_tables:CLR.T_RESERVE"),
                     F("needle", "CLRRS150 writes reserve movements only and does not update CLR.T_RESERVE.",
                       "CLRRS150", "PROGRAM:CLRRS150#writes_tables")])
    doc.ps(pr.paras(["audit2"], 1))
    doc.h(2, "2.2 The reserving process")
    rows = []
    for sid in ("PS-RSV-01", "PS-RSV-02", "PS-RSV-03", "PS-RSV-04"):
        st = W.steps[sid]
        rows.append([sid, st["name"], st["description"], ", ".join(p for p in st["programs"] if p in W.programs),
                     ctx.person(st["raci"]["A"])])
    doc.table(["Step", "Name", "Description", "Programs", "Accountable"], rows, widths=[2.0, 2.8, 5.6, 2.8, 3.4],
              caption="Reserving process steps", font_size=8.2)
    doc.ps(pr.paras(["audit2", "audit"], 2))
    doc.h(2, "2.3 Reserve batch jobs and interfaces")
    rows = []
    for jn in ("CLRNRSV1", "CLRNRSV2", "CLRNRSV3", "CLRNRSV4", "CLRMRSV1", "CLRMRSV2", "CLRYGL90"):
        j = W.jcl_jobs[jn]
        sch = j["schedule"] if ctx.ok(f"JCL:{jn}", "schedule") and "(2026-" not in j["schedule"] else "Operations schedule"
        rows.append([jn, ctx.a(j["description"]), ", ".join(s["program"] for s in j["steps"]), sch])
    doc.table(["Job", "Description", "Programs", "Schedule"], rows, widths=[2.4, 6.6, 3.8, 3.8],
              caption="Reserve-related batch jobs", font_size=8.4)
    rows = []
    for iid in ("CLX-IF-042", "CLX-IF-043", "CLX-IF-044", "CLX-IF-047", "CLX-IF-031"):
        i = W.interfaces[iid]
        rows.append([iid, i["name"], ctx.sys(i["source_system"]), ctx.sys(i["target_system"]), i["protocol"]])
    doc.table(["Interface", "Name", "From", "To", "Protocol"], rows, widths=[2.4, 5.6, 3.0, 3.0, 2.6],
              caption="Reserve interfaces", font_size=8.4)
    doc.ps(pr.paras(["audit2", "integration"], 1))
    doc.h(2, "2.4 Planned changes")
    doc.p("Programme Skerry will move reserve calculation to the reserve-svc service in Claims Hub. Until each migration "
          "wave is complete, CLARA remains the system of record for reserves and the controls in this report continue "
          "to apply.")
    doc.ps(pr.paras(["audit2", "migration"], 1))

    # 3 Scope ------------------------------------------------------------------------------
    doc.h(1, "3 Scope and approach", page_break=True)
    doc.p("The audit covered the period 1 January 2025 to 30 September 2025 and the following control objectives:")
    doc.bullets(["Reserves are set and changed only by authorised users within their authority limits.",
                 "Every change to a reserve is recorded with an audit trail.",
                 "Tier-3 reserves are reviewed at the frequency required by the reserving rules.",
                 "Reserve movements are completely and accurately extracted to downstream systems.",
                 "Large reserve movements are notified to Reinsurance on time.",
                 "Program and data documentation supports the operation of these controls."])
    rows = [["C1", "Reserve authority limits enforced by user profile (BR-RSV-003 v3)", "System", "Configuration inspection, re-performance"],
            ["C2", "Reserve movement written for every reserve change", "System", "Code and data inspection"],
            ["C3", "Tier-3 review scheduling and overdue report (CLRNRSV1)", "System / manual", "Inspection, sample testing"],
            ["C4", "Daily reserve movement extract reconciliation", "Manual", "Inspection of reconciliations"],
            ["C5", "Large loss notification within 24 hours (BR-RSV-011 v2)", "System / manual", "Sample testing"],
            ["C6", "Month-end reserve snapshot (BR-RSV-019)", "System", "Inspection"],
            ["C7", "Reserve correction utility authorisation", "Manual", "Sample testing"],
            ["C8", "Interface change impact assessment", "Manual", "Inspection of change records"]]
    doc.table(["Control", "Description", "Type", "Test approach"], rows, widths=[1.6, 8.2, 2.6, 4.2],
              caption="Controls tested", font_size=8.6)
    doc.ps(pr.paras(["audit", "audit2"], PAD_SCOPE))
    doc.h(2, "3.1 Out of scope")
    doc.p("The actuarial methodology for IBNR, the Actuarial Reserving Workbench and reinsurance accounting were outside "
          "the scope of this audit.")
    doc.h(2, "3.2 Interviews")
    people = ["P009", "P016", "P023", "P025", "P026", "P031", "P038", "P021", "P030"]
    doc.table(["Name", "Title"], [[ctx.name(p), ctx.title(p)] for p in people], widths=[5.0, 11.6], font_size=8.6)

    # 4 Findings ---------------------------------------------------------------------------
    doc.h(1, "4 Detailed findings", page_break=True)
    doc.p("Each finding sets out the observation, the risk, the recommendation and management's agreed action. "
          "Ratings are defined in Appendix B.")
    r7 = ctx.rule("BR-RSV-007")
    _finding(doc, pr, "IA-25-05", "Evidence of Tier-3 reserve reviews", "Amber",
             f"BR-RSV-007 (v{r7['version']}) requires Tier-3 reserves to be reviewed at least every {r7['parameters']['review_days']} days. "
             f"CLARA schedules the reviews and job CLRNRSV1 produces the overdue review report. For a sample of Tier-3 "
             f"claims, the review was completed but the reviewer's rationale was not recorded consistently in the claim "
             f"notes, and the overdue report was not evidenced as reviewed on every working day.",
             "Reviews may be performed without challenge, and overdue reviews may not be escalated promptly.",
             "Record the rationale for each Tier-3 review in a structured note and evidence the daily review of the "
             "overdue report.", "P009", "Within three months",
             facts=[F("temporal", "In late 2025 BR-RSV-007 v2 requires Tier-3 reserve reviews at least every 21 days.",
                      f"at least every {r7['parameters']['review_days']} days", "RULE:BR-RSV-007@v2#parameters.review_days")])
    _finding(doc, pr, "IA-25-06", "Program documentation for reserve updates", "Amber",
             "The CLARA data dictionary lists seven programs as writers of CLR.T_RESERVE. Inspection of the programs "
             "found an eighth, CLRGL090, which updates the table during the year-end revaluation. The dictionary also "
             "does not state that CLRRS150 writes movements without updating reserves.",
             "Impact assessments for changes, migration mapping and audit work may rely on an incomplete list of the "
             "programs that change reserves.",
             "Correct the data dictionary and confirm the writer list against the program source for every reserve table.",
             "P016", "Within three months",
             facts=[F("needle", "The data dictionary lists seven writers of CLR.T_RESERVE; CLRGL090 is missing.",
                      "lists seven programs as writers of CLR.T_RESERVE", "TABLE:CLR.T_RESERVE#writers")])
    p90 = W.programs["CLRGL090"]
    _finding(doc, pr, "IA-25-07", "Year-end revaluation not recorded as reserve movements", "Amber",
             f"CLRGL090 updates CLR.T_RESERVE without writing CLR.T_RESERVE_MOVEMENT, leaving no audit trail for "
             f"revaluations. The program runs in job {p90['jcl_job']} at year-end and revalues Nordic reserves to GBP. "
             f"It updates the GBP equivalent amount and the last revaluation date on each reserve row. Because no "
             f"movement is written, the revaluation does not appear in the reserve movement extract and cannot be "
             f"explained from the movement history.",
             "Changes to reported reserves cannot be traced to individual movements; reconciliations between the "
             "reserve table and the movement history show unexplained differences after each year-end.",
             "Record revaluations as reserve movements with a dedicated movement type, either in CLARA or, if the "
             "change cannot be made safely before migration, in the target reserve service, and document a compensating "
             "reconciliation in the meantime.", "P016", "Approach to be confirmed by the reserving design review",
             facts=[PF(ctx, "ld24_ia2507", "CLRGL090 updates CLR.T_RESERVE without writing CLR.T_RESERVE_MOVEMENT, leaving no audit trail for revaluations",
                       notes="Findings section, finding IA-25-07 (page 12)."),
                    F("general", "CLRGL090 runs in job CLRYGL90 (year-end reserve currency revaluation).",
                      f"runs in job {p90['jcl_job']}", "PROGRAM:CLRGL090#jcl_job")])
    _finding(doc, pr, "IA-25-08", "Interface change control for the reserve movement extract", "Green",
             "Following incident INC-2025-0412 in April 2025, when a change to the reserve movement record layout broke "
             "the general ledger journals, an interface change impact checklist requiring downstream sign-off was "
             "introduced (CHUB-144). The audit confirmed that the checklist was used for the changes sampled, but it is "
             "not yet referenced in the CLARA change procedure.",
             "Future changes may bypass the checklist if it is not embedded in the standard procedure.",
             "Reference the checklist in the CLARA change procedure and the CAB entry criteria.", "P031", "Within three months",
             facts=[F("general", "After INC-2025-0412 an interface change impact checklist with downstream sign-off was introduced (CHUB-144).",
                      "CHUB-144", "TICKET:CHUB-144")])
    _finding(doc, pr, "IA-25-09", "Reserve correction utility usage", "Green",
             "The reserve movement correction utility CLRRS150 runs in the nightly job CLRNRSV2. Correction requests "
             "were authorised for the sample tested, but the authorisation was held in email rather than with the "
             "correction record.",
             "Evidence of authorisation may be lost.", "Store the authorisation with the correction request.", "P009",
             "Within three months")
    r11 = ctx.rule("BR-RSV-011")
    _finding(doc, pr, "IA-25-10", "Large loss notification evidence", "Green",
             f"BR-RSV-011 (v{r11['version']}) requires Reinsurance to be notified within 24 hours of a reserve movement "
             f"above the Large Loss Notification Threshold. Notifications in the sample were made on time, but for some "
             f"the time of notification was evidenced only in the ReCede audit log.",
             "Timeliness could not be demonstrated quickly if challenged by a reinsurer.",
             "Record the notification time on the claim.", "P038", "Within three months")

    # 5 Effective controls -------------------------------------------------------------------
    doc.h(1, "5 Controls operating effectively", page_break=True)
    doc.p("The following controls were found to be designed and operating effectively:")
    doc.bullets(["Reserve authority limits under BR-RSV-003 v3, effective 1 September 2025, were correctly configured "
                 "in CLARA user profiles (CHUB-174).",
                 "The month-end reserve snapshot was produced and retained for every month in the period (BR-RSV-019).",
                 "Reserve movements carried a reason code from the RSNC code list (BR-RSV-015).",
                 "Reserves were closed down on final settlement with a settlement movement (BR-RSV-014)."])
    doc.ps(pr.paras(["audit", "audit2"], 2))

    # 6 Follow-up -------------------------------------------------------------------------
    doc.h(1, "6 Management comments")
    doc.p(f"{ctx.person('P009')}: Management accepts the findings. The revaluation audit trail will be addressed as part "
          f"of the reserving design for Claims Hub, and a compensating reconciliation will be documented for the "
          f"2025 year-end.")
    doc.ps(pr.paras(["audit2"], 1))

    # Appendices ---------------------------------------------------------------------------
    doc.h(1, "Appendix A – Reserving rules in force", page_break=True)
    rows = [[rid, f"v{v}", t, txt] for rid, v, t, txt in _rsv_rules(ctx)]
    doc.table(["Rule", "Version", "Title", "Text"], rows, widths=[2.2, 1.4, 4.2, 8.8], caption="Reserving rules", font_size=7.8)
    doc.h(1, "Appendix B – Rating definitions")
    doc.table(["Rating", "Definition"], [list(r) for r in RATINGS], widths=[2.4, 14.2], font_size=8.8)
    doc.h(1, "Appendix C – Reserve tables and writers")
    rows = []
    for t in ("CLR.T_RESERVE", "CLR.T_RESERVE_MOVEMENT"):
        tb = W.tables[t]
        rows.append([t, tb["description"], ", ".join(sorted(tb["writers"]))])
    doc.table(["Table", "Description", "Programs that write it"], rows, widths=[4.2, 5.2, 7.2], font_size=8.4,
              caption="Writers by table (from program source)")
    doc.ps(pr.paras(["audit2"], 1))
    for t in ("CLR.T_RESERVE", "CLR.T_RESERVE_MOVEMENT"):
        tb = W.tables[t]
        doc.h(2, f"C.{('CLR.T_RESERVE', 'CLR.T_RESERVE_MOVEMENT').index(t) + 1} {t} columns")
        rows = []
        for c in tb["columns"]:
            ty = c["type"] + (f"({c['length']}" + (f",{c['scale']})" if c.get("scale") else ")") if c.get("length") and c["type"] in ("CHAR", "VARCHAR", "DECIMAL") else "")
            rows.append([c["name"], ty, "No" if c.get("nullable") is False else "Yes", ctx.a(c.get("description", ""))])
        doc.table(["Column", "Type", "Nullable", "Description"], rows, widths=[4.4, 2.8, 1.8, 7.6], font_size=8.0)
        doc.p(f"Read by: {', '.join(sorted(r for r in tb['readers'] if str(W.programs.get(r, {}).get('since', '9999')) <= date))}.",
              size=8.6)
    doc.h(1, "Appendix D – Sample testing summary", page_break=True)
    doc.p("Samples were selected from the population of reserve changes and claims in the audit period. Results are "
          "summarised by control; detailed working papers are held by Internal Audit.")
    rows = [["C1", "Reserve changes by users at each authority level", "Random", "No exceptions"],
            ["C2", "Reserve rows changed by each writer program", "Targeted", "Exception: CLRGL090 (IA-25-07)"],
            ["C3", "Tier-3 claims open during the period", "Random", "Exceptions in evidencing (IA-25-05)"],
            ["C4", "Daily extract reconciliations", "Random", "No exceptions after May 2025"],
            ["C5", "Movements above the notification threshold", "Complete population", "Evidencing improvement (IA-25-10)"],
            ["C6", "Month-end snapshots", "Complete population", "No exceptions"],
            ["C7", "Corrections processed by CLRRS150", "Random", "Evidencing improvement (IA-25-09)"],
            ["C8", "Interface changes in the period", "Complete population", "Improvement (IA-25-08)"]]
    doc.table(["Control", "Population", "Selection", "Result"], rows, widths=[1.6, 7.0, 3.0, 5.0],
              caption="Sample testing results", font_size=8.6)
    doc.ps(pr.paras(["audit", "audit2"], 3))
    doc.h(1, "Appendix E – Record layouts")
    for cbn in ("RSVREC", "RSVMVT01"):
        cb = W.copybooks[cbn]
        fields = [f for f in cb.get("fields", []) if f["name"] != "RM-REC-VERSION"]
        doc.h(2, f"{cbn} – {ctx.a(cb.get('description') or cb.get('table') or '')}")
        doc.table(["Level", "Field", "PIC"], [[str(f["level"]).zfill(2), f["name"], f.get("pic") or "group"] for f in fields],
                  widths=[1.6, 8.0, 7.0], font_size=8.0)
    doc.h(1, "Appendix F – Program-level review of reserve writers", page_break=True)
    doc.p("For each program that changes reserve data, the audit inspected the program source, the copybooks used and "
          "the job or transaction that runs it. The results are summarised below.")
    for pid in list(W.reserve_writers) + ["CLRRS150"]:
        p = W.programs[pid]
        runs = f"job {p['jcl_job']}" if p.get("jcl_job") else (f"transaction {p['cics_transaction']}" if p.get("cics_transaction") else "called routine")
        mv = "Yes" if "CLR.T_RESERVE_MOVEMENT" in p["writes_tables"] else "No"
        rs = "Yes" if "CLR.T_RESERVE" in p["writes_tables"] else "No"
        doc.h(2, f"{pid} – {ctx.a(p['description'])}")
        doc.kv([["Type", p["type"]], ["Runs as", runs], ["Updates CLR.T_RESERVE", rs], ["Writes a reserve movement", mv],
                ["Reads", ", ".join(t for t in p["reads_tables"] if t != "CLR.T_FRAUD_NOTIFICATION") or "—"],
                ["Copybooks", ", ".join(p.get("copybooks", [])) or "—"],
                ["Owning team", ctx.team(p["owner_team"])]], widths=(4.6, 12.0), font_size=8.6)
        doc.p(pr.para(["audit2", "finding", "data"], n=(2, 3)))
    doc.h(1, "Appendix G – Downstream use of reserve movements", page_break=True)
    doc.p("Because the reserve movement history is the source of the daily reserve movement extract, a change to a "
          "reserve that is not recorded as a movement is invisible to every downstream consumer. The interfaces below "
          "receive reserve movements directly or indirectly at the date of this report.")
    imp = W.impact("CLX-IF-042")
    rows = []
    for hop, ids in imp["hops"].items():
        for iid in ids:
            i = W.interfaces[iid]
            if str(i["since"]) > date:
                continue
            rows.append([f"Hop {hop}", iid, i["name"], ctx.sys(i["target_system"]),
                         ", ".join(ctx.team(t) for t in i.get("consumer_teams", []) if t in W.teams) or "—"])
    doc.table(["Level", "Interface", "Name", "Receiving system", "Consumer teams"], rows, widths=[1.6, 2.4, 4.8, 3.6, 4.2],
              caption="Downstream consumers of reserve movements", font_size=8.4,
              facts=[F("general", "CLX-IF-043 (GL Reserve Journal Feed) is a first-hop consumer of the reserve movement extract.",
                       "GL Reserve Journal Feed", "INTERFACE:CLX-IF-042#dependents")])
    doc.p("The quarterly NISA-TP2 technical provisions return depends on these feeds through the general ledger. The "
          "revaluation gap described in IA-25-07 therefore has to be reconciled manually before each year-end return.")
    doc.ps(pr.paras(["audit2", "finding"], 3))
    doc.h(1, "Appendix H – Control to process mapping")
    rows = [["C1", "PS-RSV-02", "Authority check and approval"], ["C2", "PS-RSV-01 to PS-RSV-03", "All reserve changes"],
            ["C3", "PS-RSV-03", "Periodic reserve review"], ["C4", "PS-RSV-03", "Movement extract after nightly batch"],
            ["C5", "PS-RSV-04", "Large loss notification"], ["C6", "PS-RSV-03", "Month-end snapshot"],
            ["C7", "PS-RSV-02", "Corrections"], ["C8", "—", "Change management for interfaces"]]
    doc.table(["Control", "Process steps", "Scope"], rows, widths=[2.0, 5.0, 9.6], font_size=8.8)
    doc.ps(pr.paras(["audit", "audit2"], 2))
    doc.h(1, "Appendix I – Distribution and acknowledgements")
    doc.p("We thank the Reserving, Legacy Claims Platforms, Mainframe Batch Operations, Integration Platform and "
          "Reinsurance teams for their assistance during the audit.")
    doc.ps(pr.paras(["audit2"], 1))
    return doc


def _finding(doc, pr, ref, title, rating, obs, risk, rec, owner, target, facts=None, first=False):
    ctx = doc.ctx
    doc.h(2, f"{ref} – {title}", page_break=not first)
    doc.kv([["Rating", rating], ["Control", title]], widths=(3.0, 13.6), font_size=9)
    doc.h(3, "Observation")
    doc.p(obs, facts=facts)
    doc.p(pr.para(["finding", "audit2"], n=(2, 3)))
    doc.h(3, "Risk")
    doc.p(risk)
    doc.h(3, "Recommendation")
    doc.p(rec)
    doc.h(3, "Management action")
    doc.kv([["Agreed action", rec], ["Owner", ctx.person(owner)], ["Target", target]], widths=(3.0, 13.6), font_size=9)


def post_check(doc, texts):
    from harness import extract as X
    pg = [i + 1 for i, t in enumerate(texts) if X.match("CLRGL090 updates CLR.T_RESERVE without writing", t)]
    out = [f"INFO IA-25-07 detail on pages {pg}; total {len(texts)}"]
    if pg != [12]:
        out.append(f"IA-25-07 finding on pages {pg}, want [12] (tune PAD_SCOPE)")
    return out

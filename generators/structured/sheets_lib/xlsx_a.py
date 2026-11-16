"""XLSX workbooks ST001-ST006."""
from __future__ import annotations

import datetime as dt
import re

from openpyxl.worksheet.datavalidation import DataValidation

from . import claims as C
from .common import (D, W, adate, approvers_for, col_letter, colleagues_of, doc_control_sheet, finalize_ooxml, iso,
                     may, new_workbook, pick, placement, pname, print_setup, program_id_asof, programs_asof, ptitle,
                     require, rng, set_props, set_widths, step_known, svcname, sysname, table_exists, team_name,
                     temporalize, text_rules_known, write_header, write_rows, write_title, xl_styles, PURPOSE_BANK)
from .csv_files import status_asof

AREA_ORDER = ["COMMON", "FNOL", "TRIAGE", "ASSESS", "RESERVE", "FRAUD", "SETTLE", "RECOVER", "GL", "REPORT"]


def save(ctx, wb, fid):
    p = ctx.path(fid)
    if ctx.want(fid):
        p.parent.mkdir(parents=True, exist_ok=True)
        wb.save(p)
        finalize_ooxml(p, fid)


def dtype(c: dict) -> str:
    t = c["type"]
    if t in ("CHAR", "VARCHAR"):
        return f"{t}({c['length']})"
    if t == "DECIMAL":
        return f"DECIMAL({c['length']},{c.get('scale', 0)})"
    if t in ("NUMERIC",):
        return f"NUMERIC({c['length']},{c.get('scale', 0)})" if c.get("length") else "NUMERIC"
    return t


# =============================================================================================
# ST001 CLARA Data Dictionary (2025-02-14, stale writer list for CLR.T_RESERVE)
# =============================================================================================

CODE_PAIR = re.compile(r"\b([A-Z0-9]{1,3})\s+([a-z][a-z\- ]+?)(?=,|\)|$)")


def code_values(desc: str) -> list[tuple[str, str]]:
    m = re.search(r"\(([^()]*)\)", desc)
    seg = m.group(1) if m else desc
    pairs = [(a, b.strip()) for a, b in CODE_PAIR.findall(seg)]
    pairs = [p for p in pairs if p[1] and len(p[1]) < 30]
    return pairs if len(pairs) >= 2 else []


def st001_tables(d):
    out = []
    for name, t in W.tables.items():
        if t["db"] != "DB2" or not table_exists(name, d):
            continue
        out.append(name)
    return out


_PAREN = re.compile(r"\s*\([^()]*\)")


def column_desc_asof(text: str, d) -> str:
    """Column description as written on date d: parentheticals that cite a rule (or rule version) introduced
    after d are dropped, e.g. 'Customer notice due date (referral date + 10 business days, BR-FRD-032)' ->
    'Customer notice due date' in a 2025 document."""
    if text_rules_known(text, d):
        return text
    out = _PAREN.sub(lambda m: "" if not text_rules_known(m.group(0), d) else m.group(0), text).strip()
    assert text_rules_known(out, d), f"rule reference outside a parenthetical: {text!r}"
    return out


def st001_columns(tname, d):
    """Every column of the table (the world has no column history), with descriptions as of date d."""
    return [dict(c, description=column_desc_asof(c["description"], d)) for c in W.tables[tname]["columns"]]


def build_st001(ctx):
    fid = "ST001"
    d = adate(fid)
    a = W.anchor(fid)
    S = xl_styles()
    wb = new_workbook()
    set_props(wb, fid, subject="CLARA DB2 data dictionary", keywords="CLARA; DB2; data dictionary")
    progs = set(programs_asof(d))
    tables = st001_tables(d)
    ncols = sum(len(st001_columns(t, d)) for t in tables)
    dc = doc_control_sheet(
        wb, fid,
        purpose=pick(rng(f"{fid}:p"), PURPOSE_BANK) + " It describes the CLARA DB2 tables, their columns, code values and program usage.",
        scope="All DB2 tables of the CLARA claims platform in schema CLR. Claims Hub PostgreSQL tables are out of scope.",
        approvers=approvers_for(fid),
        colleagues=colleagues_of(a["author"], d),
        sources=["DB2 catalogue extract (January 2025)", "Program source scan by Legacy Claims Platforms"],
        extra=[("Tables documented", len(tables)), ("Columns documented", ncols)])

    # ---------------------------------------------------------------- Tables (block layout)
    ws = wb.create_sheet("Tables")
    write_title(ws, "CLARA Data Dictionary - Tables", f"As at {iso(d)}. Grouped by functional area.")
    headers = ["Table", "Description", "Primary key", "Copybook", "Written by", "Read by", "Foreign keys", "Columns"]
    row = 4
    rsv_row = None
    rsv_hdr_row = None
    frd_row = None
    for area in AREA_ORDER:
        names = [t for t in tables if W.tables[t]["area"] == area]
        if not names:
            continue
        if area == "RESERVE":
            lead = W.team_lead("T12", iso(d))
            label = f"RESERVE AREA — owner: {team_name('T12', d)} ({pname(lead, d)})"
            rsv_hdr_row = row
        else:
            label = f"{area} AREA — business owner: to be confirmed (custodian: {team_name('T20', d)})"
        ws.cell(row=row, column=1, value=label).font = S["block_font"]
        for j in range(1, 9):
            ws.cell(row=row, column=j).fill = S["block_fill"]
        ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=8)
        row += 1
        write_header(ws, row, headers)
        row += 1
        for tn in names:
            t = W.tables[tn]
            ws_w = [w for w in (t.get("writers") or []) if w in progs]
            if tn == "CLR.T_RESERVE":
                ws_w = [w for w in W.reserve_writers if w != "CLRGL090"]  # stale list (C08)
            else:
                ws_w = sorted(ws_w)
            writers = ", ".join(program_id_asof(w, d) for w in ws_w)
            readers = ", ".join(program_id_asof(p, d) for p in sorted(t.get("readers") or []) if p in progs)
            fks = "; ".join(f"{f['column']} -> {f['references']}" for f in t.get("foreign_keys") or [])
            vals = [tn, temporalize(t["description"], d), ", ".join(t["primary_key"]), t.get("copybook") or "", writers,
                    readers, fks, len(st001_columns(tn, d))]
            for j, v in enumerate(vals, 1):
                c = ws.cell(row=row, column=j, value=v)
                c.alignment = S["wrap"]
                c.border = S["border"]
            if tn == "CLR.T_RESERVE":
                rsv_row = row
            if tn == "CLR.T_FRAUD_REFERRAL":
                frd_row = row
            row += 1
        row += 1
    set_widths(ws, [26, 44, 18, 12, 40, 60, 40, 9])
    ws.freeze_panes = "B4"
    print_setup(ws, fid)

    # ---------------------------------------------------------------- Columns
    wc = wb.create_sheet("Columns")
    write_title(wc, "CLARA Data Dictionary - Columns", "One row per column. Filter on Table or Area.")
    ch = ["Table", "Column", "Seq", "Data type", "Nullable", "Primary key", "Foreign key", "PII", "Description", "Area"]
    write_header(wc, 4, ch)
    r = 5
    ni_row = None
    refscore_row = None
    for tn in tables:
        t = W.tables[tn]
        fkmap = {f["column"]: f["references"] for f in t.get("foreign_keys") or []}
        for k, c in enumerate(st001_columns(tn, d), 1):
            vals = [tn, c["name"], k, dtype(c), "Y" if c["nullable"] else "N", "Y" if c["name"] in t["primary_key"] else "",
                    fkmap.get(c["name"], ""), "Yes" if c["pii"] else "No", temporalize(c["description"], d), t["area"]]
            for j, v in enumerate(vals, 1):
                wc.cell(row=r, column=j, value=v)
            if tn == "CLR.T_CLAIMANT" and c["name"] == "NI_NO":
                ni_row = r
            if tn == "CLR.T_FRAUD_REFERRAL" and c["name"] == "REF_SCORE":
                refscore_row = r
            r += 1
    last_col_row = r - 1
    wc.auto_filter.ref = f"A4:J{last_col_row}"
    wc.freeze_panes = "C5"
    dv1 = DataValidation(type="list", formula1='"Y,N"', allow_blank=False)
    dv1.add(f"E5:E{last_col_row}")
    dv2 = DataValidation(type="list", formula1='"Yes,No"', allow_blank=False)
    dv2.add(f"H5:H{last_col_row}")
    wc.add_data_validation(dv1)
    wc.add_data_validation(dv2)
    set_widths(wc, [26, 26, 6, 16, 9, 11, 30, 7, 70, 10])
    print_setup(wc, fid)

    # ---------------------------------------------------------------- Code Values
    wv = wb.create_sheet("Code Values")
    write_title(wv, "CLARA Data Dictionary - Code Values", "Valid values for coded columns.")
    write_header(wv, 4, ["Table", "Column", "Code", "Meaning", "Source"])
    r = 5
    seen = set()
    rc_row = None
    for tn in tables:
        for c in st001_columns(tn, d):
            for code, meaning in code_values(temporalize(c["description"], d)):
                key = (tn, c["name"], code)
                if key in seen:
                    continue
                seen.add(key)
                for j, v in enumerate([tn, c["name"], code, meaning, "Column definition"], 1):
                    wv.cell(row=r, column=j, value=v)
                if tn == "CLR.T_CLAIM" and c["name"] == "CLAIM_STATUS" and code == "RC":
                    rc_row = r
                r += 1
    for pid, p in W.products.items():
        for j, v in enumerate(["CLR.T_CLAIM", "PRODUCT_CD", p["code"], p["name"], "Product catalogue"], 1):
            wv.cell(row=r, column=j, value=v)
        r += 1
    for ct, c in W.claim_types.items():
        for j, v in enumerate(["CLR.T_CLAIM", "PERIL_CD", c["peril_code"], c["name"], "Claim type catalogue"], 1):
            wv.cell(row=r, column=j, value=v)
        r += 1
    wv.auto_filter.ref = f"A4:E{r - 1}"
    wv.freeze_panes = "A5"
    set_widths(wv, [26, 26, 8, 30, 20])
    print_setup(wv, fid, landscape=False)

    # ---------------------------------------------------------------- Column Usage
    wu = wb.create_sheet("Column Usage")
    write_title(wu, "CLARA Data Dictionary - Column Usage",
                "Program access by column, propagated from table-level SQL found in program source (R read, W write).")
    write_header(wu, 4, ["Table", "Column", "Program", "Access", "Program type", "Program area"])
    r = 5
    gl_row = None
    for tn in tables:
        t = W.tables[tn]
        writers = set(w for w in (t.get("writers") or []) if w in progs)
        if tn == "CLR.T_RESERVE":
            writers.discard("CLRGL090")
        readers = set(p for p in (t.get("readers") or []) if p in progs)
        allp = sorted(writers | readers)
        for c in st001_columns(tn, d):
            for pid in allp:
                acc = "R/W" if (pid in writers and pid in readers) else ("W" if pid in writers else "R")
                p = W.programs[pid]
                vals = [tn, c["name"], program_id_asof(pid, d), acc, p["type"], p["area"]]
                for j, v in enumerate(vals, 1):
                    wu.cell(row=r, column=j, value=v)
                if pid == "CLRGL090" and tn == "CLR.T_CURRENCY_RATE" and gl_row is None:
                    gl_row = r
                r += 1
    usage_rows = r - 5
    wu.auto_filter.ref = f"A4:F{r - 1}"
    wu.freeze_panes = "A5"
    set_widths(wu, [26, 26, 11, 8, 12, 12])
    print_setup(wu, fid, landscape=False)

    # ---------------------------------------------------------------- _retired (hidden)
    wr = wb.create_sheet("_retired")
    write_header(wr, 1, ["Table", "Column", "Data type", "Retired on", "Description", "Note"])
    r = 2
    first_retired = None
    for tn in tables:
        for rc in W.tables[tn].get("retired_columns") or []:
            vals = [tn, rc["name"], dtype(rc), rc["retired"], rc["description"],
                    "Retained for lineage only. Do not use in new extracts."]
            for j, v in enumerate(vals, 1):
                wr.cell(row=r, column=j, value=v)
            if first_retired is None:
                first_retired = (r, tn, rc)
            r += 1
    set_widths(wr, [18, 22, 12, 12, 70, 50])
    wr.sheet_state = "hidden"

    save(ctx, wb, fid)

    # ---------------------------------------------------------------- facts
    pl = placement(fid, "st1_hidden")
    rr, tn, rc = first_retired
    ctx.xfact(fid, "_retired", f"B{rr}", rc["name"],
              f"Hidden sheet '_retired' of the CLARA data dictionary lists retired column {tn}.{rc['name']} (CHAR 14), retired {rc['retired']} with SKADE-90.",
              kind="hidden_sheet", hidden=True, world_ref=pl["world_ref"], exclusive=True, placement=pl)
    ctx.xfact(fid, "_retired", f"C{rr}", "CHAR(14)", f"Retired column {rc['name']} was CHAR(14).", kind="hidden_sheet",
              hidden=True, world_ref=pl["world_ref"], exclusive=True, notes="part of PL-152")
    ctx.xfact(fid, "_retired", f"D{rr}", rc["retired"], f"{rc['name']} was retired on {rc['retired']}.", kind="hidden_sheet",
              hidden=True, world_ref=pl["world_ref"], exclusive=True, notes="part of PL-152")
    pl = placement(fid, "st1_merged")
    ctx.xfact(fid, "Tables", f"A{rsv_hdr_row}", f"RESERVE AREA — owner: Reserving (Lena Kristiansen)",
              "Merged header 'RESERVE AREA - owner: Reserving (Lena Kristiansen)' spans the CLR.T_RESERVE block of the Tables sheet.",
              kind="merged_cell", world_ref=pl["world_ref"], placement=pl)
    pl = placement(fid, "st1_writers7")
    ctx.xfact(fid, "Tables", f"E{rsv_row}", "CLRFN030, CLRRS010, CLRRS020, CLRRS110, CLRRS130, CLRST040, CLRRC050",
              "Data dictionary (2025-02-14) 'Written by' for CLR.T_RESERVE lists 7 programs: CLRFN030, CLRRS010, CLRRS020, CLRRS110, CLRRS130, CLRST040, CLRRC050 (omits CLRGL090).",
              kind="contradiction_old", world_ref=pl["world_ref"], placement=pl)
    pl = placement(fid, "st1_pii")
    ctx.xfact(fid, "Columns", f"D{ni_row}", "CHAR(13)", "CLR.T_CLAIMANT.NI_NO is CHAR(13).", kind="needle",
              world_ref=pl["world_ref"], placement=pl)
    ctx.xfact(fid, "Columns", f"H{ni_row}", "Yes", "CLR.T_CLAIMANT.NI_NO is flagged PII in the data dictionary.",
              kind="needle", world_ref=pl["world_ref"], notes="part of PL-155")
    ctx.xfact(fid, "Tables", f"E{frd_row}", "FNETREF1",
              "In the 2025-02-14 data dictionary the fraud referral writer is listed under its pre-rename id FNETREF1 (renamed CLRFR030 on 2025-03-01).",
              kind="temporal", world_ref="PROGRAM:CLRFR030#renamed_from")
    ctx.xfact(fid, "Columns", f"I{refscore_row}", "FRAUDNET score",
              "The 2025-02-14 data dictionary describes CLR.T_FRAUD_REFERRAL.REF_SCORE as the FRAUDNET score at referral (the engine was renamed Sentinel on 2025-03-01).",
              kind="temporal", world_ref="SYSTEM:SYS03#renames")
    ctx.xfact(fid, "Code Values", f"D{rc_row}", "in recovery", "CLAIM_STATUS code RC means 'in recovery'.",
              world_ref="TABLE:CLR.T_CLAIM#columns.CLAIM_STATUS")
    ctx.xfact(fid, "Column Usage", f"C{gl_row}", "CLRGL090",
              "In the data dictionary's Column Usage sheet CLRGL090 appears only as a reader of CLR.T_CURRENCY_RATE and CLR.T_GL_PERIOD, not on CLR.T_RESERVE.",
              kind="contradiction_old", world_ref="TABLE:CLR.T_RESERVE#writers", notes="stale; see ST019")
    ctx.xfact(fid, "Document Control", "B11", str(len(tables)),
              f"The CLARA data dictionary documents {len(tables)} DB2 tables.", world_ref="SYSTEM:SYS01")
    ctx.done(fid, f"6 sheets, {len(tables)} tables, {last_col_row - 4} columns, {usage_rows} usage rows")


# =============================================================================================
# ST002 RACI matrix (2025-10-06)
# =============================================================================================

def build_st002(ctx):
    fid = "ST002"
    d = adate(fid)
    a = W.anchor(fid)
    S = xl_styles()
    wb = new_workbook()
    set_props(wb, fid, subject="Claims process RACI")
    doc_control_sheet(wb, fid,
                      purpose="Defines who is Responsible, Accountable, Consulted and Informed for each step of the claims process after the 2025-09-01 re-organisation.",
                      scope="Claims process stages S1 to S7 (First Notice of Loss to Recovery & Subrogation), all regions.",
                      approvers=approvers_for(fid), colleagues=colleagues_of(a["author"], d),
                      sources=["Claims process model", "Organisation chart after the 2025-09-01 re-organisation"])
    ws = wb.create_sheet("RACI")
    write_title(ws, "Claims Process RACI Matrix", f"Effective {iso(d)}. R = Responsible, A = Accountable, C = Consulted, I = Informed.")
    hdr = ["Stage", "Step ID", "Step", "Responsible", "Accountable", "Consulted", "Informed", "SLA", "Systems"]
    write_header(ws, 4, hdr)
    r = 5
    stage_rows = {}
    rec_rows = []
    step_rows = {}
    for sid in sorted(W.stages, key=lambda s: W.stages[s]["order"]):
        st = W.stages[sid]
        steps = sorted([s for s in W.steps.values() if s["stage"] == sid and step_known(s, d)], key=lambda s: s["order"])
        r0 = r
        for s in steps:
            ra = s["raci"]
            acc = ra["A"]
            sla = s["sla"]["text"] if text_rules_known(s["sla"]["text"], d) else ""
            vals = [st["name"] if r == r0 else None, s["id"], s["name"],
                    ", ".join(team_name(t, d) for t in ra.get("R") or []),
                    f"{pname(acc, d)} ({ptitle(acc, d)})",
                    ", ".join(team_name(t, d) for t in ra.get("C") or []),
                    ", ".join(team_name(t, d) for t in ra.get("I") or []),
                    sla, ", ".join(sysname(x, d) for x in s.get("systems") or [])]
            for j, v in enumerate(vals, 1):
                c = ws.cell(row=r, column=j, value=v)
                c.alignment = S["wrap"]
                c.border = S["border"]
            if sid == "S7":
                rec_rows.append(r)
            step_rows[s["id"]] = r
            r += 1
        ws.merge_cells(start_row=r0, start_column=1, end_row=r - 1, end_column=1)
        ws.cell(row=r0, column=1).alignment = S["center"]
        ws.cell(row=r0, column=1).font = S["label_font"]
        ws.cell(row=r0, column=1).fill = S["block_fill"]
        stage_rows[sid] = (r0, r - 1, len(steps))
    set_widths(ws, [22, 12, 36, 34, 40, 30, 30, 34, 36])
    ws.freeze_panes = "C5"
    print_setup(ws, fid)

    wt = wb.create_sheet("Team Leads")
    write_title(wt, "Team leads referenced in the RACI", f"As at {iso(d)}.")
    write_header(wt, 4, ["Team ID", "Team", "Department", "Lead", "Lead title", "Location"])
    rr = 5
    for tid in sorted(W.teams):
        lead = W.team_lead(tid, iso(d))
        if not lead:
            continue
        dep = W.team_department(tid, iso(d))
        vals = [tid, team_name(tid, d), W.departments[dep]["name"] if dep in W.departments else "", pname(lead, d),
                ptitle(lead, d), W.locations[W.location_of(lead, iso(d))]["name"]]
        for j, v in enumerate(vals, 1):
            wt.cell(row=rr, column=j, value=v)
        rr += 1
    set_widths(wt, [9, 36, 28, 26, 46, 32])
    print_setup(wt, fid)
    save(ctx, wb, fid)

    pl = placement(fid, "st2_merged")
    r0, r1, n = stage_rows["S7"]
    owner = W.owner_of_process("S7", iso(d))
    ctx.xfact(fid, "RACI", f"A{r0}", "Recovery & Subrogation",
              f"Merged stage cell 'Recovery & Subrogation' spans {n} step rows (A{r0}:A{r1}); Accountable for every step is {pname(owner, d)}.",
              kind="merged_cell", world_ref=pl["world_ref"], placement=pl)
    ctx.xfact(fid, "RACI", f"E{rec_rows[1]}", "Freya Lindahl",
              "RACI: PS-REC-02 'Open subrogation case and demand' - Accountable Freya Lindahl (Head of Recoveries & Subrogation).",
              kind="needle", world_ref="PROCESS:S7#owner", notes="supports PL-156")
    r0, r1, n = stage_rows["S5"]
    ctx.xfact(fid, "RACI", f"A{r0}", "Fraud Referral", f"Merged stage cell 'Fraud Referral' spans {n} step rows.",
              kind="merged_cell", world_ref="PROCESS:S5")
    if "PS-FRD-04" in step_rows:
        ctx.xfact(fid, "RACI", f"E{step_rows['PS-FRD-04']}", "Rachel Dunmore",
                  "RACI: PS-FRD-04 'SIU investigation and outcome' - Accountable Rachel Dunmore (SIU Investigations Manager (UK)).",
                  world_ref="PROCESS:PS-FRD-04#raci")
    ctx.xfact(fid, "RACI", f"H{step_rows['PS-RSV-04']}", "within 24 hours",
              "RACI: PS-RSV-04 large loss notification SLA is within 24 hours (BR-RSV-011 v2).",
              world_ref="PROCESS:PS-RSV-04#sla")
    ctx.done(fid, f"3 sheets, {sum(v[2] for v in stage_rows.values())} step rows")


# =============================================================================================
# ST003 Interface Register (2026-08-24; no CLX-IF-042 schedule)
# =============================================================================================

def build_st003(ctx):
    fid = "ST003"
    d = adate(fid)
    a = W.anchor(fid)
    S = xl_styles()
    wb = new_workbook()
    set_props(wb, fid, subject="Interface register CLX-IF-001..060")
    doc_control_sheet(wb, fid,
                      purpose="Register of every CLARA and Claims Hub interface with owner, criticality and dependencies.",
                      scope="Interfaces CLX-IF-001 to CLX-IF-060. Schedules are maintained in the batch scheduler and job documentation; where a register entry is blank, use that source.",
                      approvers=approvers_for(fid), colleagues=colleagues_of(a["author"], d),
                      sources=["Integration Platform catalogue", "Batch Scheduler job list"])
    ws = wb.create_sheet("Register")
    write_title(ws, "Interface Register", f"As at {iso(d)}.")
    hdr = ["Interface ID", "Name", "Source system", "Target system", "Protocol", "Format", "Schedule", "Programs",
           "Services", "Tables", "Owner", "Owner team", "Criticality", "Status", "Live since / planned", "Avg daily volume",
           "Depends on", "Dependents", "Consumer teams", "Reports fed", "Kafka topic", "Notes"]
    write_header(ws, 4, hdr)
    r = 5
    rows_by_id = {}
    for iid in sorted(W.interfaces):
        x = W.interfaces[iid]
        for f in ("owner", "criticality", "depends_on", "dependents", "format", "name"):
            require(fid, f"INTERFACE:{iid}", f)
        sched = W.interface_schedule(iid, iso(d)) if may(fid, f"INTERFACE:{iid}", "schedule") else None
        status = x["status"] if x["since"] <= iso(d) else "planned"
        owner = x["owner"]
        vals = [iid, x["name"], sysname(x["source_system"], d), sysname(x["target_system"], d), x["protocol"],
                temporalize(x["format"], d), sched, ", ".join(x["programs"]),
                ", ".join(svcname(s, d) for s in x["services"]), ", ".join(x["tables"]), pname(owner, d),
                team_name(W.team_of(owner, iso(d)), d) if W.team_of(owner, iso(d)) else "", x["criticality"], status,
                D(x["since"]), x["avg_daily_volume"], ", ".join(x["depends_on"]), ", ".join(x["dependents"]),
                ", ".join(team_name(t, d) for t in x.get("consumer_teams") or []), ", ".join(x.get("feeds_reports") or []),
                x.get("kafka_topic") or "", temporalize(x.get("note") or "", d)]
        for j, v in enumerate(vals, 1):
            c = ws.cell(row=r, column=j, value=v)
            if isinstance(v, dt.date):
                c.number_format = "yyyy-mm-dd"
        rows_by_id[iid] = r
        r += 1
    last = r - 1
    ws.auto_filter.ref = f"A4:{col_letter(len(hdr))}{last}"
    ws.freeze_panes = "B5"
    dv = DataValidation(type="list", formula1='"Critical,High,Medium,Low"', allow_blank=False)
    dv.add(f"M5:M{last}")
    ws.add_data_validation(dv)
    set_widths(ws, [12, 34, 24, 24, 11, 40, 22, 20, 22, 26, 22, 26, 10, 9, 11, 16, 18, 26, 22, 12, 24, 40])
    print_setup(ws, fid)

    wd = wb.create_sheet("Dependencies")
    write_title(wd, "Interface dependencies", "Upstream interface -> downstream interface.")
    write_header(wd, 4, ["Upstream", "Upstream name", "Downstream", "Downstream name"])
    rr = 5
    for iid in sorted(W.interfaces):
        for dn in W.interfaces[iid]["dependents"]:
            for j, v in enumerate([iid, W.interfaces[iid]["name"], dn, W.interfaces[dn]["name"]], 1):
                wd.cell(row=rr, column=j, value=v)
            rr += 1
    set_widths(wd, [12, 34, 12, 34])
    print_setup(wd, fid, landscape=False)

    wsum = wb.create_sheet("Summary")
    write_title(wsum, "Interfaces by criticality and protocol")
    write_header(wsum, 3, ["Criticality", "Count"])
    crits = ["Critical", "High", "Medium", "Low"]
    for k, cr in enumerate(crits):
        wsum.cell(row=4 + k, column=1, value=cr)
        n = sum(1 for x in W.interfaces.values() if x["criticality"] == cr)
        wsum.cell(row=4 + k, column=2, value=n)
    set_widths(wsum, [14, 10])
    save(ctx, wb, fid)

    pl = placement(fid, "st3_042")
    r42 = rows_by_id["CLX-IF-042"]
    ctx.xfact(fid, "Register", f"K{r42}", "Henrik Vestergaard", "Interface register: CLX-IF-042 owner Henrik Vestergaard.",
              kind="needle", world_ref=pl["world_ref"], placement=pl)
    ctx.xfact(fid, "Register", f"M{r42}", "Critical", "Interface register: CLX-IF-042 criticality Critical.",
              kind="needle", world_ref="INTERFACE:CLX-IF-042#criticality", notes="part of PL-157")
    ctx.xfact(fid, "Register", f"R{r42}", "CLX-IF-043, CLX-IF-044, CLX-IF-047, CLX-IF-049",
              "Interface register: CLX-IF-042 dependents are CLX-IF-043, CLX-IF-044, CLX-IF-047 and CLX-IF-049.",
              kind="needle", world_ref="INTERFACE:CLX-IF-042#dependents")
    r43 = rows_by_id["CLX-IF-043"]
    ctx.xfact(fid, "Register", f"G{r43}", "daily 03:45", "Interface register (2026-08-24): CLX-IF-043 GL Reserve Journal Feed runs daily 03:45.",
              kind="temporal", world_ref="INTERFACE:CLX-IF-043#schedule_history")
    r35 = rows_by_id["CLX-IF-035"]
    ctx.xfact(fid, "Register", f"N{r35}", "planned", "Interface register (2026-08-24): CLX-IF-035 Portal FNOL to Claims Hub is still 'planned' (live from 2026-09-14).",
              kind="temporal", world_ref="INTERFACE:CLX-IF-035#since")
    r58 = rows_by_id["CLX-IF-058"]
    ctx.xfact(fid, "Register", f"V{r58}", "IBNR", "CLX-IF-058 Reserve Triangles Extract feeds the monthly IBNR run of the Reserving team.",
              world_ref="INTERFACE:CLX-IF-058#note")
    r51 = rows_by_id["CLX-IF-051"]
    ctx.xfact(fid, "Register", f"T{r51}", "NISA-TP2", "CLX-IF-051 Technical Provisions Feed feeds report NISA-TP2.",
              world_ref="INTERFACE:CLX-IF-051#feeds_reports")
    ctx.done(fid, f"4 sheets, {len(rows_by_id)} interfaces")


# =============================================================================================
# ST004 Reserve Movements Q3 2026 (xlsxwriter; hidden 'calc' sheet with revaluation rates)
# =============================================================================================

def build_st004(ctx):
    import xlsxwriter
    fid = "ST004"
    d = adate(fid)
    a = W.anchor(fid)
    rows = ctx.data["claims"]
    mv = [m for m in C.movements(rows, D("2026-07-01"), D("2026-09-30"), "q3")
          if m["region"] != "UK" and m["tier"] >= 2]
    p = ctx.path(fid)
    p.parent.mkdir(parents=True, exist_ok=True)
    wb = xlsxwriter.Workbook(str(p), {"strings_to_numbers": False, "strings_to_urls": False})
    when = dt.datetime(d.year, d.month, d.day, 9, 0, 0)
    wb.set_properties({"title": a["title"], "author": pname(a["author"], d), "created": when,
                       "subject": "Q3 2026 Nordic reserve movements and 30 September revaluation", "company": "",
                       "comments": ""})
    hdr = wb.add_format({"bold": True, "font_color": "#FFFFFF", "bg_color": "#1F4E62", "border": 1, "text_wrap": True,
                         "valign": "vcenter", "align": "center", "font_size": 10})
    title = wb.add_format({"bold": True, "font_size": 14, "font_color": "#1F3A4D"})
    sub = wb.add_format({"italic": True, "font_size": 10, "font_color": "#4A5A66"})
    lab = wb.add_format({"bold": True, "font_size": 10, "font_color": "#1F3A4D"})
    datef = wb.add_format({"num_format": "yyyy-mm-dd", "align": "left"})
    tsf = wb.add_format({"num_format": "yyyy-mm-dd hh:mm:ss"})
    num = wb.add_format({"num_format": "#,##0.00"})
    rate_f = wb.add_format({"num_format": "0.0000"})
    wrap = wb.add_format({"text_wrap": True, "valign": "top"})

    # Document control
    ws0 = wb.add_worksheet("Document Control")
    ws0.write("A1", a["title"], title)
    ws0.write("A2", "Corvane Mutual Insurance Society Limited - Programme Skerry", sub)
    meta = [("Document title", a["title"]), ("Document reference", f"SKR-{fid}"), ("Version", "1.0"),
            ("Status", a["status"].capitalize()), ("Date", d), ("Owner / author", f"{pname(a['author'], d)} ({ptitle(a['author'], d)})"),
            ("Classification", "Internal use only. Contains operational detail."),
            ("Scope", "Q3 2026 (2026-07-01 to 2026-09-30) case-reserve movements on Tier-2 and Tier-3 claims of the Nordic branches (NOK, SEK, DKK), with GBP equivalents at the 2026-09-30 revaluation rates."),
            ("Method", "GBP equivalents use the quarter-end revaluation rates held on the calculation sheet; the Summary sheet totals by currency and movement type.")]
    rr = 3
    for k, v in meta:
        ws0.write(rr, 0, k, lab)
        if isinstance(v, dt.date):
            ws0.write_datetime(rr, 1, dt.datetime(v.year, v.month, v.day), datef)
        else:
            ws0.write(rr, 1, v, wrap)
        rr += 1
    rr += 1
    ws0.write(rr, 0, "Approvals", lab)
    rr += 1
    for j, h in enumerate(["Name", "Role", "Decision", "Date"]):
        ws0.write(rr, j, h, hdr)
    rr += 1
    for pid in approvers_for(fid):
        ws0.write(rr, 0, pname(pid, d))
        ws0.write(rr, 1, ptitle(pid, d))
        ws0.write(rr, 2, "Approved")
        ws0.write_datetime(rr, 3, dt.datetime(d.year, d.month, d.day), datef)
        rr += 1
    ws0.set_column(0, 0, 22)
    ws0.set_column(1, 1, 90)
    ws0.set_column(2, 3, 14)
    ws0.set_header("&LCorvane Mutual&R" + a["title"])
    ws0.set_footer(f"&L{fid} v1.0 - {a['date']}&CInternal&RPage &P of &N")

    # Movements
    ws = wb.add_worksheet("Movements")
    ws.write("A1", "Reserve movements Q3 2026 - Nordic branches, Tier-2 and Tier-3", title)
    ws.write("A2", f"{len(mv):,} movements. GBP at revaluation = movement amount x 30-Sep rate (calc sheet).", sub)
    cols = ["Movement ID", "Claim ID", "Reserve ID", "Reserve type", "Movement timestamp", "Movement type", "Currency",
            "Amount (local)", "GBP at revaluation", "Product", "Region", "Tier", "Source system", "Program / service"]
    for j, h in enumerate(cols):
        ws.write(3, j, h, hdr)
    fx = C.P["fx_to_gbp_quarter_end"]["2026-09-30"]
    first_rows = {}
    for i, m in enumerate(mv):
        r = 4 + i
        ws.write_string(r, 0, m["movement_id"])
        ws.write_string(r, 1, m["claim_id"])
        ws.write_string(r, 2, m["reserve_id"])
        ws.write_string(r, 3, m["reserve_type"])
        ws.write_datetime(r, 4, m["movement_ts"], tsf)
        ws.write_string(r, 5, m["movement_type"])
        ws.write_string(r, 6, m["currency"])
        ws.write_number(r, 7, m["amount"], num)
        gbp = round(m["amount"] * fx[m["currency"]], 2)
        ws.write_formula(r, 8, f"=ROUND(H{r + 1}*VLOOKUP(G{r + 1},calc!$A$2:$B$4,2,FALSE),2)", num, gbp)
        ws.write_string(r, 9, m["product_code"])
        ws.write_string(r, 10, m["region"])
        ws.write_number(r, 11, m["tier"])
        ws.write_string(r, 12, m["source_system"])
        ws.write_string(r, 13, m["program_or_service"])
        first_rows.setdefault((m["currency"], m["movement_type"]), r + 1)
    last = 4 + len(mv)
    ws.autofilter(3, 0, last - 1, len(cols) - 1)
    ws.freeze_panes(4, 2)
    ws.set_column(0, 3, 14)
    ws.set_column(4, 4, 19)
    ws.set_column(5, 6, 9)
    ws.set_column(7, 8, 16)
    ws.set_column(9, 13, 13)
    ws.set_landscape()
    ws.fit_to_pages(1, 0)
    ws.set_header("&LCorvane Mutual&R" + a["title"])
    ws.set_footer(f"&L{fid} v1.0 - {a['date']}&CInternal&RPage &P of &N")

    # Summary with SUMIFS formulas and cached results
    wsm = wb.add_worksheet("Summary")
    wsm.write("A1", "Q3 2026 movements by currency and type", title)
    wsm.write("A2", "Totals in local currency and in GBP at the 30-Sep revaluation rates.", sub)
    sh = ["Currency", "Movement type", "Count", "Amount (local)", "GBP at revaluation"]
    for j, h in enumerate(sh):
        wsm.write(3, j, h, hdr)
    r = 4
    sums = {}
    for ccy in ("NOK", "SEK", "DKK"):
        for t in ("IN", "AD", "RV", "IX", "RC", "ST"):
            sel = [m for m in mv if m["currency"] == ccy and m["movement_type"] == t]
            if not sel:
                continue
            cnt = len(sel)
            amt = round(sum(m["amount"] for m in sel), 2)
            gbp = round(sum(round(m["amount"] * fx[ccy], 2) for m in sel), 2)
            sums[(ccy, t)] = (r + 1, cnt, amt, gbp)
            wsm.write_string(r, 0, ccy)
            wsm.write_string(r, 1, t)
            wsm.write_formula(r, 2, f'=COUNTIFS(Movements!$G$5:$G${last},A{r + 1},Movements!$F$5:$F${last},B{r + 1})', None, cnt)
            wsm.write_formula(r, 3, f'=SUMIFS(Movements!$H$5:$H${last},Movements!$G$5:$G${last},A{r + 1},Movements!$F$5:$F${last},B{r + 1})', num, amt)
            wsm.write_formula(r, 4, f'=SUMIFS(Movements!$I$5:$I${last},Movements!$G$5:$G${last},A{r + 1},Movements!$F$5:$F${last},B{r + 1})', num, gbp)
            r += 1
    wsm.set_column(0, 1, 14)
    wsm.set_column(2, 4, 18)

    # calc (hidden)
    wc = wb.add_worksheet("calc")
    wc.write_string(0, 0, "Currency")
    wc.write_string(0, 1, "Revaluation rate to GBP at 2026-09-30")
    for k, ccy in enumerate(("NOK", "SEK", "DKK")):
        wc.write_string(1 + k, 0, ccy)
        wc.write_number(1 + k, 1, float(fx[ccy]), rate_f)
    wc.write_string(5, 0, "Source: Group Ledger quarter-end rates (CLX-IF-027)")
    wc.hide()
    wb.close()
    finalize_ooxml(p, fid)
    if not ctx.want(fid):
        p.unlink()

    pl = placement(fid, "st4_calc")
    for k, ccy in enumerate(("NOK", "SEK", "DKK")):
        val = f"{float(fx[ccy])}"
        ctx.xfact(fid, "calc", f"B{2 + k}", val,
                  f"Hidden sheet 'calc' of the Q3 2026 reserve movements workbook: revaluation rate at 2026-09-30 {ccy}/GBP {val}.",
                  kind="hidden_sheet", hidden=True, world_ref=pl["world_ref"], placement=pl if k == 0 else None,
                  notes=None if k == 0 else "part of PL-158", link=f"fx2026q3:{ccy}")
    key = ("NOK", "ST") if ("NOK", "ST") in sums else next(iter(sums))
    r1, cnt, amt, gbp = sums[key]
    ctx.xfact(fid, "Summary", f"C{r1}", str(cnt), f"Q3 2026: {cnt} {key[0]} movements of type {key[1]} on Nordic Tier-2/3 claims.",
              world_ref="TABLE:CLR.T_RESERVE_MOVEMENT")
    ctx.xfact(fid, "Summary", f"E{r1}", str(int(gbp)) if float(gbp).is_integer() else repr(float(gbp)),
              f"Q3 2026 {key[0]} {key[1]} movements total GBP {gbp:,.2f} at the 30-Sep revaluation rate.",
              world_ref="TABLE:CLR.T_RESERVE_MOVEMENT")
    ctx.done(fid, f"4 sheets, {len(mv)} movement rows")


# =============================================================================================
# ST005 Business Rule Catalogue (2026-10-20)
# =============================================================================================

def _params(prm: dict) -> str:
    out = []
    for k, v in prm.items():
        if isinstance(v, list):
            v = " / ".join(map(str, v))
        elif isinstance(v, bool):
            v = "true" if v else "false"
        out.append(f"{k}={v}")
    return "; ".join(out)


def build_st005(ctx):
    fid = "ST005"
    d = adate(fid)
    ds = iso(d)
    a = W.anchor(fid)
    S = xl_styles()
    wb = new_workbook()
    set_props(wb, fid, subject="Business rule catalogue")
    doc_control_sheet(wb, fid,
                      purpose="Catalogue of every claims business rule and its versions, with owners, approvals and where each rule is implemented.",
                      scope="All rule areas (FNOL, triage, assessment, reserving, fraud, settlement, recoveries, general). Restricted rule texts are not reproduced; see the source document.",
                      approvers=approvers_for(fid, ["P005"]), colleagues=colleagues_of(a["author"], d),
                      sources=["Rules repository", "Claims Handling Manual", "Committee and workshop minutes"])
    wr = wb.create_sheet("Rules")
    write_title(wr, "Business Rule Catalogue - Rules", f"As at {ds}. One row per rule; current version in force.")
    hdr = ["Rule ID", "Area", "Title", "Owner", "Current version", "Current status", "Effective from", "Supersedes",
           "Superseded by", "Programs", "Services", "Claim types", "Products", "Process steps"]
    write_header(wr, 4, hdr)
    r = 5
    for rid in sorted(W.rules):
        x = W.rules[rid]
        cur = W.rule_version(rid, ds)
        approved = [v for v in x["versions"] if v.get("approved_on") and v["approved_on"] <= ds]
        latest = cur or (approved[-1] if approved else x["versions"][-1])
        sup = ", ".join(f"{s['rule']} v{s['version']}" for s in x.get("supersedes") or [])
        at = x["applies_to"]
        vals = [rid, x["area"], x["title"], pname(x["owner"], d), f"v{latest['version']}", latest["status"],
                D(latest["effective_from"]) if latest.get("effective_from") else None, sup, x.get("superseded_by") or "",
                ", ".join(x["implemented_in"]["programs"]), ", ".join(svcname(s, d) for s in x["implemented_in"]["services"]),
                at["claim_types"] if isinstance(at["claim_types"], str) else ", ".join(at["claim_types"]),
                at["products"] if isinstance(at["products"], str) else ", ".join(at["products"]),
                ", ".join(at.get("process_steps") or [])]
        for j, v in enumerate(vals, 1):
            c = wr.cell(row=r, column=j, value=v)
            if isinstance(v, dt.date):
                c.number_format = "yyyy-mm-dd"
        r += 1
    wr.auto_filter.ref = f"A4:N{r - 1}"
    wr.freeze_panes = "B5"
    set_widths(wr, [12, 6, 44, 22, 9, 11, 12, 16, 13, 22, 28, 22, 14, 18])
    print_setup(wr, fid)

    wv = wb.create_sheet("Versions")
    write_title(wv, "Business Rule Catalogue - Versions", "All versions, including superseded, withdrawn and draft.")
    vh = ["Rule ID", "Version", "Status", "Effective from", "Effective to", "Rule text", "Parameters", "Approved by",
          "Approved on", "Source"]
    write_header(wv, 4, vh)
    r = 5
    rows_v = {}
    withheld = 0
    for rid in sorted(W.rules):
        for v in W.rules[rid]["versions"]:
            ref = f"{rid}@v{v['version']}"
            if v.get("approved_on") and v["approved_on"] > ds:
                continue
            text = v["text"] if may(fid, f"RULE:{ref}", "text") else "Restricted - see source document"
            prm_ok = may(fid, f"RULE:{ref}", "parameters") and all(
                may(fid, f"RULE:{ref}", f"parameters.{k}") for k in v["parameters"])
            prm = _params(v["parameters"]) if prm_ok else "Restricted"
            if text.startswith("Restricted") or prm == "Restricted":
                withheld += 1
            vals = [rid, v["version"], v["status"], D(v["effective_from"]) if v.get("effective_from") else None,
                    D(v["effective_to"]) if v.get("effective_to") else None, text, prm,
                    ", ".join(pname(p, d) for p in v.get("approved_by") or []),
                    D(v["approved_on"]) if v.get("approved_on") else None, v.get("source") or ""]
            for j, val in enumerate(vals, 1):
                c = wv.cell(row=r, column=j, value=val)
                if isinstance(val, dt.date):
                    c.number_format = "yyyy-mm-dd"
                if j in (6, 10):
                    c.alignment = S["wrap"]
            rows_v[ref] = r
            r += 1
    wv.auto_filter.ref = f"A4:J{r - 1}"
    wv.freeze_panes = "C5"
    dv = DataValidation(type="list", formula1='"approved,superseded,withdrawn,draft"', allow_blank=False)
    dv.add(f"C5:C{r - 1}")
    wv.add_data_validation(dv)
    set_widths(wv, [12, 8, 11, 12, 12, 80, 40, 30, 12, 50])
    print_setup(wv, fid)

    wa = wb.create_sheet("Areas")
    write_title(wa, "Rules by area")
    write_header(wa, 3, ["Area", "Rules", "Versions"])
    areas = sorted({x["area"] for x in W.rules.values()})
    for k, ar in enumerate(areas):
        wa.cell(row=4 + k, column=1, value=ar)
        wa.cell(row=4 + k, column=2, value=sum(1 for x in W.rules.values() if x["area"] == ar))
        wa.cell(row=4 + k, column=3, value=sum(len(x["versions"]) for x in W.rules.values() if x["area"] == ar))
    set_widths(wa, [10, 10, 10])
    save(ctx, wb, fid)

    pl = placement(fid, "st5_frd031")
    rr = rows_v["BR-FRD-031@v2"]
    ctx.xfact(fid, "Versions", f"H{rr}", "Niall Brannigan, Ingrid Ashby",
              "Rule catalogue: BR-FRD-031 v2 approved 2026-09-17 by Niall Brannigan and Ingrid Ashby.",
              kind="needle", world_ref=pl["world_ref"], placement=pl)
    ctx.xfact(fid, "Versions", f"I{rr}", "2026-09-17", "BR-FRD-031 v2 was approved on 2026-09-17.", kind="needle",
              world_ref="RULE:BR-FRD-031@v2#approved_on", notes="part of PL-159")
    ctx.xfact(fid, "Versions", f"G{rr}", "tier3_threshold=60", "BR-FRD-031 v2 parameters: threshold=65; tier3_threshold=60.",
              world_ref="RULE:BR-FRD-031@v2#parameters.tier3_threshold")
    ctx.xfact(fid, "Versions", f"D{rr}", "2026-10-01", "BR-FRD-031 v2 is effective from 2026-10-01.",
              world_ref="RULE:BR-FRD-031@v2#effective_from")
    rr = rows_v["BR-FRD-032@v1"]
    ctx.xfact(fid, "Versions", f"C{rr}", "draft", "BR-FRD-032 v1 (customer notice within 5 business days) is a draft that never took effect.",
              kind="draft", world_ref="RULE:BR-FRD-032@v1#status")
    rr = rows_v["BR-FRD-032@v2"]
    ctx.xfact(fid, "Versions", f"G{rr}", "notice_business_days=10", "BR-FRD-032 v2 (approved): customer notice within 10 business days of a fraud referral.",
              kind="approved", world_ref="RULE:BR-FRD-032@v2#parameters.notice_business_days")
    rr = rows_v["BR-RSV-007@v3"]
    ctx.xfact(fid, "Versions", f"G{rr}", "review_days=14", "BR-RSV-007 v3: Tier-3 reserves reviewed at least every 14 days, effective 2026-07-01.",
              world_ref="RULE:BR-RSV-007@v3#parameters.review_days")
    rr = rows_v["BR-RSV-007@v2"]
    ctx.xfact(fid, "Versions", f"E{rr}", "2026-06-30", "BR-RSV-007 v2 (21-day cadence) applied until 2026-06-30.",
              kind="temporal", world_ref="RULE:BR-RSV-007@v2#effective_to")
    rr = rows_v["BR-RSV-009@v3"]
    ctx.xfact(fid, "Versions", f"F{rr}", "Restricted - see source document",
              "The rule catalogue does not reproduce BR-RSV-009 v3's text or rate; it points to the source document.",
              world_ref="RULE:BR-RSV-009@v3", notes="exclusive parameter withheld (PL-011 lives elsewhere)")
    rr = rows_v["BR-FRD-019@v2"]
    ctx.xfact(fid, "Versions", f"C{rr}", "withdrawn", "BR-FRD-019 v2 (automatic decline at score 90) is withdrawn.",
              world_ref="RULE:BR-FRD-019@v2#status")
    rr = rows_v["BR-TRI-003@v3"]
    ctx.xfact(fid, "Versions", f"G{rr}", "tier3_min_gbp=50000", "BR-TRI-003 v3: Tier-3 at estimated incurred of £50,000 or more from 2025-01-01.",
              world_ref="RULE:BR-TRI-003@v3#parameters.tier3_min_gbp")
    ctx.done(fid, f"4 sheets, {len(W.rules)} rules, {len(rows_v)} versions")


# =============================================================================================
# ST006 CLARA Program Inventory (2026-08-20)
# =============================================================================================

def build_st006(ctx):
    fid = "ST006"
    d = adate(fid)
    ds = iso(d)
    a = W.anchor(fid)
    wb = new_workbook()
    set_props(wb, fid, subject="CLARA program inventory")
    doc_control_sheet(wb, fid,
                      purpose="Inventory of the CLARA COBOL programs with type, status, ownership and Claims Hub replacement.",
                      scope="All 122 CLARA programs found in the source libraries.",
                      approvers=approvers_for(fid, ["P016"]), colleagues=["P049", "P051", "P053"],
                      sources=["Source library scan", "Batch Scheduler job list", "CICS transaction list"])
    ws = wb.create_sheet("Programs")
    write_title(ws, "CLARA Program Inventory", f"As at {ds}.")
    hdr = ["Program ID", "Former ID", "Renamed on", "Type", "Area", "Description", "Status", "CICS transaction",
           "BMS map", "JCL job", "Subprogram", "Lines of code", "Copybooks", "Calls", "Tables read", "Tables written",
           "Owner team", "Owner", "Replaced by", "In production since"]
    write_header(ws, 4, hdr)
    r = 5
    rows_by = {}
    for pid in sorted(W.programs):
        p = W.programs[pid]
        if p["since"] > ds:
            continue
        rf = p.get("renamed_from")
        owner = p["owner_person"] if W.employed(p["owner_person"], ds) else W.team_lead(p["owner_team"], ds)
        vals = [pid, rf["old_id"] if rf else "", D(rf["date"]) if rf else None, p["type"], p["area"],
                temporalize(p["description"], d), status_asof(pid, d), p.get("cics_transaction") or "",
                p.get("bms_map") or "", p.get("jcl_job") or "", "Y" if p["subprogram"] else "N", p["loc"],
                ", ".join(p["copybooks"]), ", ".join(p["calls_programs"]), len(p["reads_tables"]),
                len(p["writes_tables"]), team_name(p["owner_team"], d), pname(owner, d),
                svcname(p["replaced_by"], d) if p.get("replaced_by") in W.services else (p.get("replaced_by") or ""),
                D(p["since"])]
        for j, v in enumerate(vals, 1):
            c = ws.cell(row=r, column=j, value=v)
            if isinstance(v, dt.date):
                c.number_format = "yyyy-mm-dd"
        rows_by[pid] = r
        r += 1
    last = r - 1
    ws.auto_filter.ref = f"A4:T{last}"
    ws.freeze_panes = "B5"
    dv = DataValidation(type="list", formula1='"active,disabled,retired"', allow_blank=False)
    dv.add(f"G5:G{last}")
    ws.add_data_validation(dv)
    set_widths(ws, [11, 10, 11, 8, 9, 50, 9, 9, 9, 10, 8, 8, 34, 34, 8, 8, 30, 22, 20, 12])
    print_setup(ws, fid)

    wc = wb.create_sheet("Call Graph")
    write_title(wc, "Program call graph", "Caller -> called program (static CALL statements).")
    write_header(wc, 4, ["Caller", "Called program", "Caller type", "Called type"])
    rr = 5
    for pid in sorted(W.programs):
        p = W.programs[pid]
        if p["since"] > ds:
            continue
        for cp in p["calls_programs"]:
            for j, v in enumerate([pid, cp, p["type"], W.programs[cp]["type"] if cp in W.programs else ""], 1):
                wc.cell(row=rr, column=j, value=v)
            rr += 1
    wc.auto_filter.ref = f"A4:D{rr - 1}"
    set_widths(wc, [11, 14, 11, 11])

    wsm = wb.create_sheet("Summary")
    write_title(wsm, "Programs by area and status")
    write_header(wsm, 3, ["Area", "Online", "Batch", "Active", "Disabled", "Retired", "Total"])
    rr = 4
    for ar in sorted({p["area"] for p in W.programs.values()}):
        ps = [pid for pid, p in W.programs.items() if p["area"] == ar and p["since"] <= ds]
        vals = [ar, sum(W.programs[p]["type"] == "online" for p in ps), sum(W.programs[p]["type"] == "batch" for p in ps),
                sum(status_asof(p, d) == "active" for p in ps), sum(status_asof(p, d) == "disabled" for p in ps),
                sum(status_asof(p, d) == "retired" for p in ps), len(ps)]
        for j, v in enumerate(vals, 1):
            wsm.cell(row=rr, column=j, value=v)
        rr += 1
    set_widths(wsm, [10, 8, 8, 8, 9, 8, 8])
    save(ctx, wb, fid)

    pl = placement(fid, "st6_disabled")
    ctx.xfact(fid, "Programs", f"G{rows_by['CLRFR140']}", "disabled", "Program inventory: CLRFR140 status 'disabled'.",
              kind="needle", world_ref=pl["world_ref"], placement=pl)
    ctx.xfact(fid, "Programs", f"B{rows_by['CLRFR020']}", "FNETCAL1", "Program inventory: CLRFR020 was formerly FNETCAL1 (renamed 2025-03-01).",
              world_ref="PROGRAM:CLRFR020#renamed_from")
    ctx.xfact(fid, "Programs", f"G{rows_by['CLRRS210']}", "active",
              "Program inventory (2026-08-20): CLRRS210 (parallel-run reconciliation) is still active; it was retired after the parallel run ended on 2026-08-28.",
              kind="temporal", world_ref="PROGRAM:CLRRS210#status")
    ctx.xfact(fid, "Programs", f"S{rows_by['CLRRS110']}", "reserve-engine", "CLRRS110 is replaced by the Claims Hub service reserve-engine.",
              world_ref="PROGRAM:CLRRS110#replaced_by")
    ctx.xfact(fid, "Programs", f"B{rows_by['CLRGL090']}", "YEREVAL1", "CLRGL090 (year-end reserve currency revaluation) was formerly YEREVAL1, renamed 2021-01-01.",
              world_ref="PROGRAM:CLRGL090#renamed_from")
    ctx.xfact(fid, "Programs", f"L{rows_by['CLRFN010']}", str(W.programs["CLRFN010"]["loc"]),
              f"CLRFN010 (FNOL capture) has {W.programs['CLRFN010']['loc']} lines of code.", world_ref="PROGRAM:CLRFN010#loc")
    ctx.done(fid, f"4 sheets, {len(rows_by)} programs")


XLSX_A = [build_st001, build_st002, build_st003, build_st004, build_st005, build_st006]

"""legacy/clara/README.md (time-neutral, from the import) and legacy/clara/docs/*.md (XC-11)."""
from __future__ import annotations

from generators.common import util

from .cobol import Fact
from .srcmodel import Src, ascii_text

DOC_DATE = "2026-10-20"


def _src(lines, marks=None):
    s = Src(fixed=False)
    marks = marks or {}
    for i, ln in enumerate(lines):
        s.emit(ln, mark=marks.get(i))
    return s


def readme(W) -> tuple[Src, list[Fact]]:
    areas = ["FN - first notice of loss (FNOL)", "TR - triage and tiering", "AS - assessment and Claims Assessor appointment",
             "RS - case reserves", "FR - fraud scoring and referral", "ST - settlement and payments",
             "RC - recoveries and subrogation", "GL - general ledger feeds", "RP - management and regulatory reporting",
             "CM - common subprograms (dates, audit, parameters, errors, MQ)"]
    L = [
        "# CLARA sources (legacy/clara)",
        "",
        "CLARA (Claims Ledger And Reserve Application) is Corvane Mutual's mainframe claims system:",
        "COBOL programs running under CICS (online) and as DB2 batch jobs.",
        "This directory mirrors the mainframe source libraries so that the CLARA code can be read,",
        "searched and reviewed next to the Claims Hub services.",
        "",
        "> The mainframe libraries remain the system of record for builds and promotions.",
        "> Changes made here must also go through the CLARA change process on the mainframe.",
        "",
        "## Layout",
        "",
        "| Path | Mainframe library type | Contents |",
        "|---|---|---|",
        "| `cobol/` | COBOL source | One member per program, `CLR` + area + 3 digits (e.g. `CLRRS170`). |",
        "| `copybooks/` | COBOL copy library | Record layouts: DB2 host structures, COMMAREA, interface records. |",
        "| `jcl/` | JCL library | One member per batch job; steps run programs under IKJEFT01 (DB2). |",
        "| `bms/` | BMS map source | Mapsets for the 3270 screens; symbolic maps are kept inline in the programs. |",
        "| `ddl/` | DB2 DDL | One file per `CLR.*` table, plus `T_PARAM_seed.sql`. |",
        "",
        "## Program naming",
        "",
        "Program names are `CLR` + a two-letter area code + a three-digit number:",
        "",
    ] + [f"- {a}" for a in areas] + [
        "",
        "Online programs run as CICS transactions (four-character transaction ids such as `RS01`).",
        "Batch programs run as steps of the jobs in `jcl/`. Subprograms in the CM area are called",
        "statically and contain no CICS commands, so batch and online programs can share them.",
        "",
        "## Conventions worth knowing",
        "",
        "- Business parameters (thresholds, cadences, caps) live in `CLR.T_PARAM` with validity dates",
        "  and are read through `CLRCM040`. See `ddl/T_PARAM_seed.sql` for the seeded rows.",
        "- Audit rows are written through `CLRCM020`; DB2 errors are formatted by `CLRCM050`.",
        "- Every table has a copybook with the same column order (see the header of each copybook).",
        "- Columns 1-6 of COBOL members hold sequence numbers; changed lines may carry a change",
        "  reference in columns 73-80.",
        "",
        "## Building",
        "",
        "The usual DB2 COBOL path applies: DB2 precompile (or the integrated coprocessor), CICS",
        "translation for online programs, compile, link-edit and bind. Site symbols (high-level",
        "qualifiers, DB2 subsystem and plan) come from the `CLRSYMS` include member and are not",
        "stored in this repository.",
    ]
    return _src(L), []


def program_inventory(W, file_id) -> tuple[Src, list[Fact]]:
    L = ["# CLARA program inventory", "",
         f"Inventory of the CLARA programs in `legacy/clara/cobol/` as of {DOC_DATE}.",
         "Status and replacement service reflect the Claims Hub migration plan on that date.", "",
         "| Program | Type | Area | Description | Transaction / job | Claims Hub replacement | Status |",
         "|---|---|---|---|---|---|---|"]
    marks = {}
    facts = []
    for pid, p in W.programs.items():
        typ = "subprogram" if p["subprogram"] else p["type"]
        where = p.get("cics_transaction") or p.get("jcl_job") or "called"
        repl = W.service_name(p["replaced_by"], DOC_DATE) if p.get("replaced_by") and \
            W.may_state(file_id, f"PROGRAM:{pid}", "replaced_by") else "-"
        d = ascii_text(p["description"]).replace("|", "/")
        marks[len(L)] = f"INV:{pid}"
        L.append(f"| {pid} | {typ} | {p['area']} | {d} | {where} | {repl} | {p['status']} |")
    L += ["", "## Notes", "",
          "- `CLRRS210` ran only during the reserve parallel run (2026-03-02 to 2026-08-28) and is retired.",
          "- `CLRFR140` (auto-decline sweep) is disabled from 2026-04-01; its job `CLRNFR99` is off the schedule.",
          "- Renamed programs: `CLRFR020` (was FNETCAL1) and `CLRFR030` (was FNETREF1) since 2025-03-01;",
          "  `CLRGL090` (was YEREVAL1) since 2021-01-01; `CLRRC010` (was SUBRO010) since 2019-04-01.",
          "- Open defect CHUB-298: the batch sweep `CLRFR040` still compares scores with a constant",
          "  instead of reading the referral threshold from `CLR.T_PARAM`.",
          ""]
    for i, ln in enumerate(L):
        if "CHUB-298" in ln:
            marks[i] = "INV-298"
        if "was FNETCAL1" in ln:
            marks[i] = "INV-REN"
    facts.append(Fact("inv-298", ("INV-298", "INV-298"), "Open defect CHUB-298",
                      "The legacy program inventory (2026-10-20) lists CHUB-298 as an open defect: CLRFR040 compares "
                      "scores with a constant instead of reading CLR.T_PARAM.", world_ref="TICKET:CHUB-298", kind="temporal"))
    facts.append(Fact("inv-ren", ("INV-REN", "INV-REN"), "`CLRFR020` (was FNETCAL1)",
                      "CLRFR020 was named FNETCAL1 and CLRFR030 was FNETREF1 until the 2025-03-01 rename.",
                      world_ref="PROGRAM:CLRFR020#renamed_from", kind="alias_use"))
    facts.append(Fact("inv-gl090", ("INV:CLRGL090", "INV:CLRGL090"), "| CLRGL090 | batch | GL |",
                      "Inventory row: CLRGL090 is a batch GL program (year-end reserve currency revaluation), job CLRYGL90, "
                      "replaced by reserve-engine.", world_ref="PROGRAM:CLRGL090#replaced_by"))
    return _src(L, marks), facts


def batch_jobs(W, file_id) -> tuple[Src, list[Fact]]:
    L = ["# CLARA batch jobs", "",
         f"Jobs in `legacy/clara/jcl/` as of {DOC_DATE}. All jobs are scheduled by the Batch Scheduler and",
         "supported by Mainframe Batch Operations.", ""]
    marks = {}
    for job, j in W.jcl_jobs.items():
        L.append(f"## {job} - {ascii_text(j['description'])}")
        L.append("")
        if W.may_state(file_id, f"JCL:{job}", "schedule"):
            L.append(f"- Schedule: {ascii_text(j['schedule'])}")
        else:
            L.append("- Schedule: see the interface catalogue entry for this extract.")
        L.append(f"- Status: {j['status']}")
        for st in j["steps"]:
            marks[len(L)] = f"JOB:{job}:{st['step']}"
            L.append(f"- {st['step']}: `{st['program']}` - {ascii_text(st['description'])}")
        if j.get("restart") and W.may_state(file_id, f"JCL:{job}", "restart"):
            L.append(f"- Restart: {ascii_text(j['restart'])}")
        L.append("")
    facts = [Fact("jobs-st040", ("JOB:CLRNSTL1:STEP020", "JOB:CLRNSTL1:STEP020"), "STEP020: `CLRST040`",
                  "Batch job notes: job CLRNSTL1 STEP020 runs CLRST040 (settlement finalisation and reserve close-down).",
                  world_ref="JCL:CLRNSTL1#steps")]
    return _src(L, marks), facts


def db2_objects(W, file_id) -> tuple[Src, list[Fact]]:
    L = ["# CLARA DB2 objects", "",
         f"The `CLR` schema as of {DOC_DATE}: one DDL file per table in `legacy/clara/ddl/`.",
         "Writers and readers are taken from the programs' EXEC SQL statements.", "",
         "| Table | Area | Copybook | Description | Written by | Read by |", "|---|---|---|---|---|---|"]
    marks = {}
    for name, t in W.tables.items():
        if not name.startswith("CLR."):
            continue
        w = ", ".join(t.get("writers", [])) or "-"
        r = ", ".join(t.get("readers", [])) or "-"
        if not W.may_state(file_id, f"TABLE:{name}", "writers"):
            w = "-"
        marks[len(L)] = f"TBL:{name}"
        L.append(f"| {name} | {t['area']} | {t.get('copybook') or '-'} | {ascii_text(t['description'])} | {w} | {r} |")
    L.append("")
    facts = [Fact("tbl-reserve", ("TBL:CLR.T_RESERVE", "TBL:CLR.T_RESERVE"),
                  "CLRFN030, CLRGL090, CLRRC050, CLRRS010, CLRRS020, CLRRS110, CLRRS130, CLRST040",
                  "The legacy DB2 object list (2026-10-20) names eight writers of CLR.T_RESERVE: CLRFN030, CLRGL090, "
                  "CLRRC050, CLRRS010, CLRRS020, CLRRS110, CLRRS130 and CLRST040.",
                  world_ref="TABLE:CLR.T_RESERVE#writers", kind="aggregate_source")]
    return _src(L, marks), facts


def coding_standards(W) -> tuple[Src, list[Fact]]:
    L = ["# CLARA coding standards (summary)", "",
         "A short summary of the conventions the CLARA programs follow. It is meant for engineers",
         "reading the code from the Claims Hub side; it does not replace the mainframe standards.", "",
         "## Program structure", "",
         "- Fixed-format COBOL: sequence numbers in columns 1-6, indicator in column 7, Area A from",
         "  column 8, Area B from column 12, nothing beyond column 72 except change tags in 73-80.",
         "- Paragraphs are numbered by phase: `0000` control, `1000` initialisation, `2000` main",
         "  processing, `3000`-`5000` business steps, `6000` commit control, `7000` report lines,",
         "  `8000` error handling, `9000` termination.",
         "- Older programs use `PERFORM ... THRU ...-EXIT`; newer ones use in-line `PERFORM`.",
         "",
         "## DB2", "",
         "- Every `EXEC SQL` statement is followed by an `EVALUATE SQLCODE`; unexpected codes go to",
         "  `8000-SQL-ERROR`, which formats the error (through `CLRCM050` where the program calls it).",
         "- Host variables come from the table copybooks; columns keep the table order.",
         "- Where a program changes a table it does not otherwise read and needs a value back (for example",
         "  the reserve id for a movement row), it uses `SELECT ... FROM OLD TABLE (UPDATE ...)` or",
         "  `FINAL TABLE` instead of a separate read.",
         "- Batch programs commit at a fixed interval and declare their driving cursor `WITH HOLD`.",
         "",
         "## Parameters and audit", "",
         "- Business thresholds, cadences and caps are rows in `CLR.T_PARAM` with validity dates.",
         "  Programs read them through `CLRCM040`; they must not be coded as constants.",
         "- Data changes made on behalf of a user are recorded through `CLRCM020`.",
         "",
         "## CICS", "",
         "- Online programs are pseudo-conversational and keep state in the `CLRCOMM1` COMMAREA.",
         "- Screen programs carry their symbolic map inline; keep it in step with `bms/`.",
         ""]
    return _src(L), []

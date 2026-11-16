"""Copybooks, JCL, BMS mapsets, DB2 DDL and the T_PARAM seed (history-aware Src objects)."""
from __future__ import annotations

from generators.common import util

from . import naming
from .cobol import Fact, is_identity
from .srcmodel import Src, ascii_text


# =============================================================================================
# copybooks
# =============================================================================================

def copybook(W, name: str) -> tuple[Src, list[Fact]]:
    c = W.copybooks[name]
    r = util.rng(f"code_legacy:cpy:{name}")
    s = Src(fixed=True)
    facts: list[Fact] = []

    def cm(text="", **kw):
        s.emit("*" + ((" " + text) if text else ""), **kw)

    right = r.random() < 0.5

    def hl(text, **kw):
        if len(text) > 62:
            raise ValueError(f"copybook header line too long: {text!r}")
        cm(text.ljust(62) + " *" if right else text, **kw)

    cm("=" * 63 + ("*" if right else "="))
    hl(f"COPYBOOK   : {name}")
    if c["table"]:
        t = W.tables[c["table"]]
        hl(f"DB2 TABLE  : {c['table']}")
        d = ascii_text(t["description"]).upper()
        for i, piece in enumerate(_wrap(d, 48)):
            hl(("CONTENT    : " if i == 0 else "             ") + piece)
        hl("LAYOUT     : ONE FIELD PER COLUMN, IN TABLE ORDER")
    else:
        d = ascii_text(c.get("description", "")).upper()
        kind = {"commarea": "CICS COMMAREA", "common": "COMMON WORK AREA",
                "interface_layout": "INTERFACE RECORD LAYOUT"}[c["kind"]]
        hl(f"TYPE       : {kind}")
        for i, piece in enumerate(_wrap(d, 48)):
            hl(("CONTENT    : " if i == 0 else "             ") + piece)
    if name == "RSVMOVE":
        hl("RECORD     : FIXED LENGTH, 116 BYTES")
        cm("-" * 63 + ("*" if right else "-"))
        hl("CHANGE LOG")
        with s.added("XC-02"):
            hl("2025-04-25 KBARR01  CHUB-138   RM-AMOUNT WIDENED TO")
            hl("                               S9(11)V99 (NORDIC LARGE LOSSES)")
        with s.added("CM-03", tag="CHUB142"):
            hl("2025-04-30 KBARR01  CHUB-142   RM-AMOUNT BACK TO")
            hl("                               S9(9)V99 COMP-3 - INC-2025-0412")
            hl("                               RM-REC-VERSION ADDED, VALUE 02")
            hl("                               FILLER X(22) -> X(20)")
    cm("=" * 63 + ("*" if right else "="))
    width_name = 30
    for f in c["fields"]:
        lvl = f["level"]
        if lvl == 1:
            s.emit(f" 01  {f['name']}.", mark=f"CPY:{f['name']}")
            continue
        indent = {5: 4, 10: 8, 15: 12}.get(lvl, 4)
        nm = f["name"]
        pic = f["pic"]
        lead = " " + "    " + " " * (indent - 4) + f"{lvl:02d}  "
        if pic is None:
            s.emit(lead + nm + ".", mark=f"CPY:{nm}")
            continue
        body = lead + nm.ljust(max(len(nm) + 1, width_name - (indent - 4))) + f"PIC {pic}."
        if len(body) > 66:
            body = lead + nm + f" PIC {pic}."
        if name == "RSVMOVE" and nm == "RM-AMOUNT":
            old = lead + nm.ljust(width_name - (indent - 4)) + "PIC S9(9)V99 COMP-3."
            mid = lead + nm.ljust(width_name - (indent - 4)) + "PIC S9(11)V99 COMP-3."
            s.emit(old, rm="XC-02")
            s.emit(mid, add="XC-02", rm="CM-03", keep_seq=True, tag="CHUB138")
            s.emit(body, add="CM-03", keep_seq=True, tag="CHUB142", mark=["PL-248:a", f"CPY:{nm}"])
            continue
        if name == "RSVMOVE" and nm == "RM-REC-VERSION":
            s.emit(body, add="CM-03", tag="CHUB142", mark=["PL-248:v", f"CPY:{nm}"])
            continue
        if name == "RSVMOVE" and nm == "FILLER":
            old = lead + nm.ljust(width_name - (indent - 4)) + "PIC X(22)."
            s.emit(old, rm="CM-03")
            s.emit(body, add="CM-03", keep_seq=True, tag="CHUB142", mark=f"CPY:{nm}")
            continue
        s.emit(body, mark=f"CPY:{nm}")
    if name == "RSVMOVE":
        facts.append(Fact("PL-248", ("PL-248:v", "PL-248:a"), "RM-AMOUNT PIC S9(9)V99 COMP-3",
                          "RSVMOVE.cpy: 05 RM-AMOUNT PIC S9(9)V99 COMP-3 and 10 RM-REC-VERSION PIC 9(2).",
                          world_ref="COPYBOOK:RSVMOVE#fields", placement="PL-248"))
        facts.append(Fact("rsvmove-ver", ("PL-248:v", "PL-248:v"), "RM-REC-VERSION PIC 9(2)",
                          "RSVMOVE.cpy defines 10 RM-REC-VERSION PIC 9(2) in the RM-HEADER group (added under CHUB-142).",
                          world_ref="COPYBOOK:RSVMOVE#field_history"))
    return s, facts


def _wrap(text, width):
    words, out, cur = text.split(), [], ""
    for w in words:
        if cur and len(cur) + 1 + len(w) > width:
            out.append(cur)
            cur = w
        else:
            cur = (cur + " " + w) if cur else w
    out.append(cur)
    return out


# =============================================================================================
# JCL
# =============================================================================================
JCL_CREATED = {"CLRDRSV9": "XC-04", "CLRNFR02": "CM-05", "CLRQFR01": "XC-07"}


def jcl(W, job: str, file_id: str) -> tuple[Src, list[Fact]]:
    j = W.jcl_jobs[job]
    r = util.rng(f"code_legacy:jcl:{job}")
    s = Src(fixed=False)
    facts = []
    date = "2026-11-06"

    def jc(text="", **kw):
        line = "//*" + ((" " + text) if text else "")
        s.emit(line, **kw)

    def box(text, **kw):
        jc(text.ljust(66) + "*", **kw)

    desc = ascii_text(j["description"]).upper()
    # descriptions that changed after the file was created: (text before, commit)
    old_desc = {"CLRNFR99": ("AUTO-DECLINE SWEEP", "XC-06"),
                "CLRDRSV9": ("RESERVE PARALLEL-RUN RECONCILIATION", "XC-09")}.get(job)
    old_step = {"CLRFR140": ("AUTO-DECLINE SWEEP (SCORE >= 90)", "XC-06")}
    acct = r.choice(["(CLR,BATCH)", "(CLR,PROD)", "(CLRB,0001)"])
    cls = r.choice(["B", "B", "C"])
    title = desc.split(" (")[0].replace("'", "")[:20].rstrip()
    s.emit(f"//{job:<8} JOB {acct},'{title}',CLASS={cls},MSGCLASS=X,", mark="JOBCARD")
    s.emit("//             MSGLEVEL=(1,1),REGION=0M,NOTIFY=&SYSUID")
    jc("-" * 66 + "*")
    box(f"JOB       : {job}")
    def versioned(lines_new, lines_old, commit):
        if lines_old == lines_new or commit is None:
            for ln in lines_new:
                box(ln)
            return
        with s.removed(commit):
            for ln in lines_old:
                box(ln)
        with s.added(commit):
            for ln in lines_new:
                box(ln)

    fn_new = [("FUNCTION  : " if i == 0 else "            ") + pc for i, pc in enumerate(_wrap(desc, 52))]
    fn_old = [("FUNCTION  : " if i == 0 else "            ") + pc for i, pc in enumerate(_wrap(old_desc[0], 52))] \
        if old_desc else fn_new
    versioned(fn_new, fn_old, old_desc[1] if old_desc else None)
    if job == "CLRNFR99":
        with s.removed("XC-06"):
            box("SCHEDULE  : DAILY 00:45 (BATCH SCHEDULER)")
        with s.added("XC-06"):
            box("SCHEDULE  : REMOVED FROM SCHEDULE 2026-04-01 (WAS DAILY 00:45)", mark="NFR99-SCHED")
            box("STATUS    : DISABLED - CHUB-207, BR-FRD-019 WITHDRAWN")
    elif job == "CLRDRSV9":
        box("SCHEDULE  : DAILY 05:00 FOR THE RESERVE PARALLEL RUN")
        box("            2026-03-02 TO 2026-08-28")
        with s.added("XC-09"):
            box("STATUS    : RETIRED 2026-08-28 - PARALLEL RUN ENDED", mark="DRSV9-RET")
    elif W.may_state(file_id, f"JCL:{job}", "schedule"):
        sched = ascii_text(j["schedule"]).upper()
        for i, piece in enumerate(_wrap(sched + " (BATCH SCHEDULER)", 52)):
            box(("SCHEDULE  : " if i == 0 else "            ") + piece, mark="SCHED" if i == 0 else None)
    owner = W.team_name(j["owner_team"], date) if W.may_state(file_id, f"JCL:{job}", "owner_team") else None
    if owner:
        box(f"SUPPORT   : {ascii_text(owner).upper()}")
    def step_lines(st, d):
        out = []
        for i, piece in enumerate(_wrap(d, 34)):
            if i == 0:
                out.append(f"STEPS     : {st['step']} {st['program']:<8} {piece}" if st is j["steps"][0]
                           else f"            {st['step']} {st['program']:<8} {piece}")
            else:
                out.append(f"                             {piece}")
        return out

    for st in j["steps"]:
        d = ascii_text(st["description"]).upper()
        od = old_step.get(st["program"])
        versioned(step_lines(st, d), step_lines(st, od[0]) if od else step_lines(st, d), od[1] if od else None)
    if j.get("restart") and W.may_state(file_id, f"JCL:{job}", "restart"):
        rs = ascii_text(j["restart"]).upper()
        for i, piece in enumerate(_wrap(rs, 52)):
            box(("RESTART   : " if i == 0 else "            ") + piece, mark="RESTART" if i == 0 else None)
    jc("-" * 66 + "*")
    jc("SITE SYMBOLS (HLQS, DB2 SUBSYSTEM AND PLAN) COME FROM THE INCLUDE")
    s.emit("//         INCLUDE MEMBER=CLRSYMS")
    s.emit("//JOBLIB   DD DSN=&CLRHLQ..LOADLIB,DISP=SHR")
    s.emit("//         DD DSN=&DB2HLQ..SDSNLOAD,DISP=SHR")
    for n, st in enumerate(j["steps"]):
        pid = st["program"]
        p = W.programs[pid]
        files = naming.batch_files(p)
        if pid == "CLRRS150":
            files.append({"dd": "IMPIN", "dir": "in", "lrecl": 200, "desc": "MOVEMENT CORRECTION REQUESTS"})
        jc()
        d = ascii_text(st["description"]).upper()
        od = old_step.get(pid)
        new_c = _wrap(f"{st['step']} - {d}", 66)
        if od:
            with s.removed(od[1]):
                for pc in _wrap(f"{st['step']} - {od[0]}", 66):
                    jc(pc)
            with s.added(od[1]):
                for pc in new_c:
                    jc(pc)
        else:
            for pc in new_c:
                jc(pc)
        jc()
        cond = "" if n == 0 else ",COND=(4,LT)"
        s.emit(f"//{st['step']:<8} EXEC PGM=IKJEFT01,DYNAMNBR=20{cond}", mark=f"STEP:{st['step']}")
        s.emit("//SYSTSPRT DD SYSOUT=*")
        s.emit("//SYSPRINT DD SYSOUT=*")
        s.emit("//SYSOUT   DD SYSOUT=*")
        s.emit("//SYSUDUMP DD SYSOUT=D")
        for f in files:
            if f.get("sysout"):
                s.emit(f"//{f['dd']:<8} DD SYSOUT=*")
            elif f.get("dsn"):
                s.emit(f"//{f['dd']:<8} DD DSN={f['dsn']},", mark="RSVOUT-DD")
                s.emit("//            DISP=(NEW,CATLG,DELETE),UNIT=SYSDA,")
                s.emit("//            SPACE=(CYL,(20,10),RLSE),")
                s.emit(f"//            DCB=(RECFM=FB,LRECL={f['lrecl']},BLKSIZE=0)")
            elif f["dir"] == "in":
                s.emit(f"//{f['dd']:<8} DD DSN=&CLRHLQ..{pid}.{f['dd']}(0),DISP=SHR")
            else:
                s.emit(f"//{f['dd']:<8} DD DSN=&CLRHLQ..{pid}.{f['dd']}(+1),")
                s.emit("//            DISP=(NEW,CATLG,DELETE),UNIT=SYSDA,")
                s.emit(f"//            SPACE=(CYL,(5,5),RLSE),DCB=(RECFM=FB,LRECL={f['lrecl']},BLKSIZE=0)")
        s.emit("//SYSTSIN  DD *,SYMBOLS=JCLONLY")
        s.emit("  DSN SYSTEM(&DB2SSID)")
        s.emit(f"  RUN PROGRAM({pid}) PLAN(&DB2PLAN) -", mark=f"RUN:{pid}")
        s.emit("      LIB('&CLRHLQ..LOADLIB')")
        s.emit("  END")
        s.emit("/*")
    s.emit("//")
    if job == "CLRNRSV3":
        facts.append(Fact("PL-249", ("STEP:STEP010", "RSVOUT-DD"), "DSN=CLR.PROD.RSVMOVE.DAILY(+1)",
                          "CLRNRSV3 STEP010 writes DD RSVOUT DSN=CLR.PROD.RSVMOVE.DAILY(+1) from program CLRRS170.",
                          world_ref="JCL:CLRNRSV3#datasets", placement="PL-249"))
    return s, facts


# =============================================================================================
# BMS
# =============================================================================================

def _bms_stmt(label, op, operands: list[str]) -> list[str]:
    """Assembler-format macro: label col 1, op col 10, operands col 16, 'X' continuation in col 72."""
    lines = []
    cur = f"{label:<8} {op:<5} "
    cur = cur.ljust(15)
    first = True
    for i, opnd in enumerate(operands):
        piece = opnd + ("," if i < len(operands) - 1 else "")
        if len(cur) + len(piece) > 71 and not cur.endswith(" " * 3):
            lines.append(cur.ljust(71) + "X")
            cur = " " * 15 + piece
        else:
            cur += piece
    lines.append(cur)
    return lines


def mapset(W, ms: str) -> tuple[Src, list[Fact]]:
    maps = [m for m in W.bms_maps.values() if m["mapset"] == ms]
    s = Src(fixed=False)
    facts = []
    late = {"CLRM420": "CM-05"}

    def cm(text="", **kw):
        s.emit(("* " + text).ljust(71) + "*" if text else "*" + " " * 70 + "*", **kw)

    s.emit("*" * 72)
    cm(f"MAPSET   : {ms}")
    for m in maps:
        with s.added(late.get(m["map"])):
            cm(f"MAP      : {m['map']}  {ascii_text(m['title']).upper()[:27]:<27} "
               f"{m['transaction']} / {m['program']}")
    cm("GENERATE THE SYMBOLIC MAP WITH SYSPARM=DSECT; KEEP THE COPY IN THE")
    cm("PROGRAMS (INLINE SYMBOLIC MAP) IN STEP WITH THIS SOURCE.")
    s.emit("*" * 72)
    for ln in _bms_stmt(ms, "DFHMSD", ["TYPE=&SYSPARM", "MODE=INOUT", "LANG=COBOL", "STORAGE=AUTO",
                                        "CTRL=(FREEKB,FRSET)", "TIOAPFX=YES", "TERM=3270-2"]):
        s.emit(ln)
    for m in maps:
        with s.added(late.get(m["map"])):
            used = set()
            s.emit("*")
            s.emit(f"* MAP {m['map']} - {ascii_text(m['title']).upper()}", mark=f"MAP:{m['map']}")
            s.emit(f"* TRANSACTION {m['transaction']}, PROGRAM {m['program']}")
            s.emit("*")
            for ln in _bms_stmt(m["map"], "DFHMDI", ["SIZE=(24,80)", "LINE=1", "COLUMN=1"]):
                s.emit(ln)
            for ln in _bms_stmt("", "DFHMDF", ["POS=(1,1)", f"LENGTH={len(m['map'])}", "ATTRB=(ASKIP,BRT)",
                                               f"INITIAL='{m['map']}'"]):
                s.emit(ln)
            title = ascii_text(m["title"]).upper().replace("'", "")
            for ln in _bms_stmt("", "DFHMDF", ["POS=(1,30)", f"LENGTH={len(title)}", "ATTRB=(ASKIP,BRT)",
                                               f"INITIAL='{title}'"]):
                s.emit(ln)
            first = True
            for f in m["fields"]:
                lab = naming.bms_label(f["name"], used)
                prompt = (f["name"].replace("-", " ") + " ").ljust(17, ".")[:17]
                s.emit(f"*        {f['name']}")
                for ln in _bms_stmt("", "DFHMDF", [f"POS=({f['row']},1)", "LENGTH=17", "ATTRB=ASKIP",
                                                   f"INITIAL='{prompt}'"]):
                    s.emit(ln)
                attrs = [a.strip() for a in f["attr"].split(",")]
                if first and "UNPROT" in attrs:
                    attrs.append("IC")
                    first = False
                attrb = f"ATTRB=({','.join(attrs)})" if len(attrs) > 1 else f"ATTRB={attrs[0]}"
                for ln in _bms_stmt(lab, "DFHMDF", [f"POS=({f['row']},{f['col']})", f"LENGTH={f['length']}", attrb]):
                    s.emit(ln, mark=f"FLD:{m['map']}:{f['name']}")
                end_col = f["col"] + f["length"]
                if end_col < 80:
                    for ln in _bms_stmt("", "DFHMDF", [f"POS=({f['row']},{end_col})", "LENGTH=1", "ATTRB=ASKIP"]):
                        s.emit(ln)
            for ln in _bms_stmt("MSG", "DFHMDF", ["POS=(23,1)", "LENGTH=79", "ATTRB=(ASKIP,BRT)"]):
                s.emit(ln)
            keys = "  ".join(f"{k}={v.upper()}" for k, v in m["pf_keys"].items())
            for ln in _bms_stmt("", "DFHMDF", ["POS=(24,1)", f"LENGTH={len(keys)}", "ATTRB=ASKIP",
                                               f"INITIAL='{keys}'"]):
                s.emit(ln)
    for ln in _bms_stmt("", "DFHMSD", ["TYPE=FINAL"]):
        s.emit(ln)
    s.emit("         END")
    return s, facts


# =============================================================================================
# DDL
# =============================================================================================
DDL_CREATED = {"CLR.T_FRAUD_NOTIFICATION": "CM-05"}


def _coltype(c):
    t = c["type"]
    if t in ("CHAR", "VARCHAR"):
        return f"{t}({c['length']})"
    if t == "DECIMAL":
        return f"DECIMAL({c['length']},{c.get('scale', 0)})"
    return t


def _q(text):
    return ascii_text(text).replace("'", "''")


def ddl(W, table: str, file_id: str) -> tuple[Src, list[Fact]]:
    t = W.tables[table]
    s = Src(fixed=False)
    facts = []
    short = table.split(".")[1]
    s.emit("-- " + "-" * 68)
    s.emit(f"-- {table}")
    s.emit(f"-- {ascii_text(t['description'])}")
    s.emit(f"-- Area: {t['area']}    Copybook: {t.get('copybook') or '-'}")
    if t.get("created"):
        s.emit(f"-- Created {t['created']} (CHUB-206, NISA Circular 2026/04)", mark="DDL-CREATED")
    s.emit("-- " + "-" * 68)
    s.emit(f"CREATE TABLE {table}", mark="DDL-CREATE")
    cols = [c for c in t["columns"]]
    for i, c in enumerate(cols):
        null = "NOT NULL" if not c["nullable"] else ""
        ident = " GENERATED ALWAYS AS IDENTITY" if is_identity(W, table, c["name"]) else ""
        default = " WITH DEFAULT" if c["name"] in ("LAST_UPD_TS",) else ""
        lead = "  ( " if i == 0 else "  , "
        s.emit(f"{lead}{c['name']:<28}{_coltype(c):<14}{null}{ident}{default}".rstrip(), mark=f"COL:{c['name']}")
    pk = ", ".join(t["primary_key"])
    s.emit(f"  , CONSTRAINT PK_{short} PRIMARY KEY ({pk})", mark="DDL-PK")
    s.emit("  )")
    s.emit("  CCSID EBCDIC;")
    s.emit("")
    s.emit(f"CREATE UNIQUE INDEX CLR.X{short[2:][:14]}_PK")
    s.emit(f"    ON {table} ({pk});")
    if "CLAIM_ID" in [c["name"] for c in cols] and t["primary_key"] != ["CLAIM_ID"]:
        s.emit(f"CREATE INDEX CLR.X{short[2:][:13]}_CLM")
        s.emit(f"    ON {table} (CLAIM_ID);")
    for n, fk in enumerate(t.get("foreign_keys", []), 1):
        ref_t, ref_c = fk["references"].rsplit(".", 1)
        s.emit("")
        s.emit(f"ALTER TABLE {table}")
        s.emit(f"  ADD CONSTRAINT FK_{short[2:][:12]}_{n} FOREIGN KEY ({fk['column']})", mark=f"FK:{fk['column']}")
        s.emit(f"      REFERENCES {ref_t} ({ref_c}) ON DELETE RESTRICT;")
    s.emit("")
    s.emit(f"COMMENT ON TABLE {table} IS")
    s.emit(f"  '{_q(t['description'])}';")
    for c in cols:
        txt = _q(c["description"]) + (" [PII]" if c.get("pii") else "")
        s.emit(f"COMMENT ON COLUMN {table}.{c['name']} IS", mark=f"CMT:{c['name']}")
        s.emit(f"  '{txt}';")
    return s, facts


def param_seed(W, file_id: str) -> tuple[Src, list[Fact]]:
    """T_PARAM seed rows; rows and end-dates are tagged with the commit that introduced them."""
    t = W.tables["CLR.T_PARAM"]
    s = Src(fixed=False)
    facts = []
    s.emit("-- " + "-" * 68)
    s.emit("-- CLR.T_PARAM seed rows (business parameters with validity dates)")
    s.emit("-- Read at run time through CLRCM040; programs never hard-code these values.")
    s.emit("-- Rows are never updated in place: a change end-dates the current row")
    s.emit("-- (VALID_TO) and inserts a new row with the change ticket.")
    s.emit("-- " + "-" * 68)
    s.emit("")
    add_commit = {("FRD_REFER_THRESH", "2026-04-01"): "XC-05", ("FRD_REFER_T3_THRESH", "2026-10-01"): "XC-10",
                  ("RSV_T3_REVIEW_DAYS", "2026-07-01"): "XC-08", ("TRI_FASTTRACK_CAP", "2026-07-01"): "XC-08",
                  ("FRD_NOTICE_BUS_DAYS", "2026-04-01"): "CM-05", ("REC_PURSUE_MIN_GBP", "2025-09-01"): "XC-03"}
    end_commit = {("FRD_REFER_THRESH", "2023-04-01"): "XC-05", ("FRD_AUTODECL_THRESH", "2023-01-01"): "XC-06",
                  ("RSV_T3_REVIEW_DAYS", "2024-01-01"): "XC-08"}
    users = {"CHUB-205": "PASHW01", "CHUB-206": "KBARR01", "CHUB-207": "PASHW01", "CHUB-318": "PASHW01",
             "CHUB-395": "PASHW01"}
    groups = []
    for row in t["param_rows"]:
        if not W.may_state(file_id, "TABLE:CLR.T_PARAM", f"param_rows:{row['key']}"):
            continue
        rv = row["rule"]
        if not (W.may_state(file_id, f"RULE:{rv}", "parameters") and W.may_state(file_id, f"RULE:{rv}", "text")):
            continue
        groups.append(row)
    last_key = None
    for row in groups:
        k = row["key"]
        rid, ver = row["rule"].split("@")
        title = ascii_text(W.rules[rid].get("title", ""))
        desc = f"{title} ({rid} {ver})"[:120].replace("'", "''")
        ac = add_commit.get((k, row["valid_from"]))
        ec = end_commit.get((k, row["valid_from"]))
        ticket = f"'{row['ticket']}'" if row["ticket"] else "NULL"
        user = users.get(row["ticket"] or "", "CLRDBA")
        val = row["value"]
        cols = "INSERT INTO CLR.T_PARAM (PARAM_KEY, VALID_FROM, VALID_TO, PARAM_VALUE, PARAM_DESC, CHANGE_TICKET, CHANGED_BY)"
        with s.added(ac):
            if k != last_key:
                s.emit("")
                s.emit(f"-- {k}")
            s.emit(cols)
            mark = f"PARAM:{k}:{row['valid_from']}"
            if ec:
                # before the end-dating commit the row was open-ended and carried no ticket
                old_ticket = "NULL" if row["ticket"] in (None, "CHUB-207") else ticket
                s.emit(f"  VALUES ('{k}', '{row['valid_from']}', NULL, '{val}', '{desc}', {old_ticket}, 'CLRDBA');",
                       rm=ec)
                s.emit(f"  VALUES ('{k}', '{row['valid_from']}', '{row['valid_to']}', '{val}', '{desc}', {ticket}, "
                       f"'{users.get(row['ticket'] or '', 'CLRDBA')}');", add=ec, mark=mark)
            else:
                vt = f"'{row['valid_to']}'" if row["valid_to"] else "NULL"
                s.emit(f"  VALUES ('{k}', '{row['valid_from']}', {vt}, '{val}', '{desc}', {ticket}, '{user}');",
                       mark=mark)
        last_key = k
    s.emit("")
    s.emit("COMMIT;")
    facts.append(Fact("PL-250", ("PARAM:FRD_REFER_T3_THRESH:2026-10-01", "PARAM:FRD_REFER_T3_THRESH:2026-10-01"),
                      "('FRD_REFER_T3_THRESH', '2026-10-01', NULL, '60'",
                      "T_PARAM seed inserts FRD_REFER_T3_THRESH = '60' valid from 2026-10-01 (CHUB-395).",
                      world_ref="TABLE:CLR.T_PARAM#param_rows:FRD_REFER_T3_THRESH", placement="PL-250"))
    facts.append(Fact("param-65", ("PARAM:FRD_REFER_THRESH:2026-04-01", "PARAM:FRD_REFER_THRESH:2026-04-01"),
                      "('FRD_REFER_THRESH', '2026-04-01', NULL, '65'",
                      "T_PARAM seed: FRD_REFER_THRESH = 65 valid from 2026-04-01 (CHUB-205).",
                      world_ref="TABLE:CLR.T_PARAM#param_rows:FRD_REFER_THRESH"))
    facts.append(Fact("param-70", ("PARAM:FRD_REFER_THRESH:2023-04-01", "PARAM:FRD_REFER_THRESH:2023-04-01"),
                      "('FRD_REFER_THRESH', '2023-04-01', '2026-03-31', '70'",
                      "T_PARAM seed: FRD_REFER_THRESH = 70 was valid from 2023-04-01 to 2026-03-31.",
                      world_ref="TABLE:CLR.T_PARAM#param_rows:FRD_REFER_THRESH", kind="temporal"))
    facts.append(Fact("param-t3rev", ("PARAM:RSV_T3_REVIEW_DAYS:2026-07-01", "PARAM:RSV_T3_REVIEW_DAYS:2026-07-01"),
                      "('RSV_T3_REVIEW_DAYS', '2026-07-01', NULL, '14'",
                      "T_PARAM seed: RSV_T3_REVIEW_DAYS = 14 valid from 2026-07-01 (CHUB-318).",
                      world_ref="TABLE:CLR.T_PARAM#param_rows:RSV_T3_REVIEW_DAYS"))
    facts.append(Fact("param-notice", ("PARAM:FRD_NOTICE_BUS_DAYS:2026-04-01", "PARAM:FRD_NOTICE_BUS_DAYS:2026-04-01"),
                      "('FRD_NOTICE_BUS_DAYS', '2026-04-01', NULL, '10'",
                      "T_PARAM seed: FRD_NOTICE_BUS_DAYS = 10 business days valid from 2026-04-01 (CHUB-206).",
                      world_ref="TABLE:CLR.T_PARAM#param_rows:FRD_NOTICE_BUS_DAYS"))
    facts.append(Fact("param-autodecl", ("PARAM:FRD_AUTODECL_THRESH:2023-01-01", "PARAM:FRD_AUTODECL_THRESH:2023-01-01"),
                      "('FRD_AUTODECL_THRESH', '2023-01-01', '2026-03-31', '90'",
                      "T_PARAM seed: FRD_AUTODECL_THRESH = 90 end-dated 2026-03-31 under CHUB-207.",
                      world_ref="TABLE:CLR.T_PARAM#param_rows:FRD_AUTODECL_THRESH", kind="temporal"))
    facts.append(Fact("param-llnt", ("PARAM:RSV_LLNT_GBP:2024-01-01", "PARAM:RSV_LLNT_GBP:2024-01-01"),
                      "('RSV_LLNT_GBP', '2024-01-01', NULL, '250000'",
                      "T_PARAM seed: RSV_LLNT_GBP (large loss notification threshold) = 250000 from 2024-01-01.",
                      world_ref="TABLE:CLR.T_PARAM#param_rows:RSV_LLNT_GBP"))
    return s, facts

"""Program-specific logic: placements (named paragraphs, exact SQL) and subprogram interfaces.

Each entry returns a dict consumed by ProgramGen.procedure():
  drive / drive_cols / drive_where / drive_sql / fetch_into   driving cursor
  handled_tables / handled_calls                               not emitted generically
  init_steps / pre_row_steps / row_steps / term_steps          [(para, body, add_commit, comment)]
  param_keys [(key, ws_target)], queue, using, entry_lines, return_lines
Facts are registered with gen.facts.append(Fact(...)) using marks placed on lines.
"""
from __future__ import annotations

from .cobol import Fact, pack


def ws(g, text, lvl=0, **kw):
    g.ws_needs["ws"].append((lvl, text, kw) if kw else (lvl, text))


def ws01(g, text, **kw):
    g.ws_needs["ws"].append(("a", text, kw) if kw else ("a", text))


def link(g, items):
    for it in items:
        g.ws_needs["linkage"].append(it)


# ---------------------------------------------------------------------------------------------
# reserve writers
# ---------------------------------------------------------------------------------------------

def s_gl090(g):
    ws(g, "05  WS-REVAL-COUNT           PIC S9(9)  COMP-3 VALUE ZERO.")

    def check_period():
        g.b("MOVE WS-RUN-DATE(1:4) TO GLPE-GL-PERIOD(1:4)")
        g.b("MOVE '12' TO GLPE-GL-PERIOD(5:2)")
        g.select_into("CLR.T_GL_PERIOD", ["GL_PERIOD", "PERIOD_STATUS", "CLOSED_TS"])
        g.sqlcheck("1200-CHECK-GL-PERIOD", on_ok=["ADD 1 TO WS-GL-PERIOD-READ"])
        g.b("IF GLPE-PERIOD-STATUS NOT = 'O'")
        g.bw("DISPLAY WS-PGM-ID ' YEAR-END PERIOD NOT OPEN ' GLPE-GL-PERIOD", 1)
        g.b("MOVE 8 TO RETURN-CODE", 1)
        g.perform("9000-TERMINATE", 1)
        g.b("GOBACK", 1)
        g.b("END-IF")

    def revalue():
        g.c("REVALUE OPEN NORDIC RESERVES TO GBP AT THE YEAR-END RATE.", mark="PL-236:s")
        g.c("THE GBP EQUIVALENT IS UPDATED IN PLACE ON CLR.T_RESERVE; NO ROW")
        g.c("IS INSERTED INTO CLR.T_RESERVE_MOVEMENT FOR A REVALUATION.", mark="GL090-NOMOVE")
        g.b("MOVE CURR-CURRENCY-CD TO WS-CCY-FROM")
        g.b("MOVE 1 TO WS-CCY-AMOUNT")
        g.b("MOVE CURR-RATE-DT TO WS-CCY-RATE-DT")
        g.call("CLRCM030")
        g.sql([("UPDATE CLR.T_RESERVE", "W:UPDATE:CLR.T_RESERVE"),
               ("   SET RSV_GBP_EQUIV_AMT =", "PL-236:n"),
               "       ROUND(RSV_OUTSTANDING_AMT * :CURR-RATE-TO-GBP, 2)",
               ("     , RSV_LAST_REVAL_DT = :CURR-RATE-DT", "GL090-REVALDT"),
               "     , LAST_UPD_TS = CURRENT TIMESTAMP",
               "     , LAST_UPD_PGM = :WS-PGM-ID",
               "     , LAST_UPD_USER = :WS-USER-ID",
               " WHERE CURRENCY_CD = :CURR-CURRENCY-CD",
               ("   AND RSV_STATUS = 'O'", "PL-236:e")])
        g.sqlcheck("3000-REVALUE", on_ok=["ADD 1 TO WS-RESERVE-WRITTEN"])
        g.sql(["GET DIAGNOSTICS :WS-ROWS-AFFECTED = ROW_COUNT"])
        g.b("ADD WS-ROWS-AFFECTED TO WS-REVAL-COUNT")

    g.facts.append(Fact("PL-236", ("PL-236:s", "PL-236:e"), "SET RSV_GBP_EQUIV_AMT =",
                        "CLRGL090 paragraph 3000-REVALUE executes EXEC SQL UPDATE CLR.T_RESERVE SET RSV_GBP_EQUIV_AMT, "
                        "RSV_LAST_REVAL_DT and never inserts into CLR.T_RESERVE_MOVEMENT.",
                        world_ref="PROGRAM:CLRGL090#writes_tables:CLR.T_RESERVE", placement="PL-236"))
    g.facts.append(Fact("gl090-nomove", ("GL090-NOMOVE", "GL090-NOMOVE"), "IS INSERTED INTO CLR.T_RESERVE_MOVEMENT FOR A REVALUATION",
                        "CLRGL090's own comment states that no row is inserted into CLR.T_RESERVE_MOVEMENT for a revaluation.",
                        world_ref="PROGRAM:CLRGL090#notes", kind="general"))
    return {"drive": "CLR.T_CURRENCY_RATE",
            "drive_cols": ["CURRENCY_CD", "RATE_DT", "RATE_TO_GBP", "RATE_TYPE_CD"],
            "drive_where": ["RATE_TYPE_CD = 'YE'", "RATE_DT = :WS-RATE-DT", "CURRENCY_CD IN ('NOK', 'SEK', 'DKK')"],
            "handled_tables": {"CLR.T_GL_PERIOD", "CLR.T_RESERVE"}, "handled_calls": {"CLRCM030"},
            "init_steps": [("1200-CHECK-GL-PERIOD", check_period, None, "YEAR-END GL PERIOD MUST BE OPEN")],
            "row_steps": [("3000-REVALUE", revalue, None, "REVALUE RESERVES IN ONE CURRENCY")]}


def _movement(g, mtype, amt_expr, reason, rsv_id_src="RSV-RSV-ID", mark=None, extra_mark=None):
    g.b(f"MOVE {rsv_id_src} TO RSVM-RSV-ID")
    k = g.claim_key()
    if k and k != "RSVM-CLAIM-ID":
        g.b(f"MOVE {k} TO RSVM-CLAIM-ID")
    g.b(f"MOVE '{mtype}' TO RSVM-MOVE-TYPE-CD", mark=extra_mark)
    g.bw(f"MOVE {amt_expr} TO RSVM-MOVE-AMT")
    g.b(f"MOVE '{reason}' TO RSVM-REASON-CD")
    g.b("MOVE 'N' TO RSVM-EXTRACTED-FLAG")
    g.b("MOVE WS-USER-ID TO RSVM-USER-ID")
    g.b("MOVE WS-PGM-ID TO RSVM-PGM-ID")
    g.insert("CLR.T_RESERVE_MOVEMENT", mark=mark,
             override={"MOVE_ID": None} if False else None, omit=("EXTRACT_RUN_ID",))
    g.sqlcheck(f"INSERT MOVEMENT {mtype}", on_ok=["ADD 1 TO WS-RESERVE-MOVEMENT-WRITTEN"
                                                   if "CLR.T_RESERVE_MOVEMENT" in g.writes else "CONTINUE"])


def s_fn030(g):
    ws(g, "05  WS-T3-MIN-GBP            PIC S9(11)V99 COMP-3 VALUE ZERO.")

    def create_claim():
        g.b("MOVE CA-CLAIM-ID TO CLM-CLAIM-ID")
        g.b("MOVE 'OP' TO CLM-CLAIM-STATUS")
        g.b("MOVE 'N' TO CLM-FRAUD-FLAG CLM-RECOVERY-FLAG")
        g.insert("CLR.T_CLAIM", mark="FN030-CLAIM")
        g.sqlcheck("3000-CREATE-CLAIM", on_ok=["ADD 1 TO WS-CLAIM-WRITTEN"])

    def default_reserve():
        g.c("DEFAULT RESERVE BY CLAIM TYPE (BR-FNOL-005). THE AMOUNT COMES FROM")
        g.c("THE CODE LOOKUP ROW FOR THE PERIL; A MOVEMENT OF TYPE IN IS WRITTEN")
        g.c("WITH IT SO THE RESERVE HISTORY STARTS AT FNOL.")
        g.b("MOVE CLM-CLAIM-ID TO RSV-CLAIM-ID")
        g.b("MOVE 'ID' TO RSV-RSV-TYPE-CD")
        g.b("MOVE CLM-CURRENCY-CD TO RSV-CURRENCY-CD WS-CCY-FROM")
        g.b("COMPUTE RSV-RSV-INITIAL-AMT = FUNCTION NUMVAL(CODE-CODE-DESC-EN)")
        g.b("MOVE RSV-RSV-INITIAL-AMT TO RSV-RSV-OUTSTANDING-AMT WS-CCY-AMOUNT")
        g.b("MOVE ZERO TO RSV-RSV-PAID-TO-DATE-AMT RSV-RSV-RECOVERY-EST-AMT")
        g.b("MOVE WS-RUN-DATE TO WS-CCY-RATE-DT")
        g.call("CLRCM030")
        g.b("MOVE WS-CCY-GBP-AMOUNT TO RSV-RSV-GBP-EQUIV-AMT")
        g.b("MOVE 'O' TO RSV-RSV-STATUS")
        g.b("MOVE 'CH' TO RSV-RSV-AUTH-LEVEL")
        g.b("MOVE WS-USER-ID TO RSV-RSV-SET-BY-USER")
        g.insert("CLR.T_RESERVE", mark="PL-237:n")
        g.sqlcheck("4000-CREATE-DEFAULT-RESERVE", on_ok=["ADD 1 TO WS-RESERVE-WRITTEN"])
        g.sql(["VALUES IDENTITY_VAL_LOCAL() INTO :RSV-RSV-ID"])
        g.b("MOVE RSV-RSV-OUTSTANDING-AMT TO RSVM-MOVE-AMT")
        g.b("MOVE RSV-RSV-GBP-EQUIV-AMT TO RSVM-MOVE-GBP-AMT")
        _movement(g, "IN", "RSV-RSV-INITIAL-AMT", "FNOL", mark="FN030-MOVE", extra_mark="FN030-IN")
        g.b("CONTINUE", mark="PL-237:e")

    g.facts.append(Fact("PL-237", ("PL-237:n", "PL-237:e"), "INSERT INTO CLR.T_RESERVE",
                        "CLRFN030 paragraph 4000-CREATE-DEFAULT-RESERVE inserts the default reserve into CLR.T_RESERVE "
                        "and an IN movement into CLR.T_RESERVE_MOVEMENT.",
                        world_ref="PROGRAM:CLRFN030#writes_tables:CLR.T_RESERVE", placement="PL-237"))
    g.facts.append(Fact("fn030-in", ("FN030-IN", "FN030-IN"), "MOVE 'IN' TO RSVM-MOVE-TYPE-CD",
                        "CLRFN030 writes the FNOL default reserve movement with movement type IN (initial).",
                        world_ref="PROGRAM:CLRFN030#writes_tables:CLR.T_RESERVE_MOVEMENT"))
    g.facts.append(Fact("fn030-claim", ("FN030-CLAIM", "FN030-CLAIM"), "INSERT INTO CLR.T_CLAIM",
                        "CLRFN030 creates the claim header row with INSERT INTO CLR.T_CLAIM.",
                        world_ref="PROGRAM:CLRFN030#writes_tables:CLR.T_CLAIM"))

    def lookup_code():
        g.b("MOVE 'DFLTRSV' TO CODE-CODE-TYPE")
        g.b("MOVE CLM-PERIL-CD TO CODE-CODE-VALUE")
        g.select_into("CLR.T_CODE_LOOKUP", ["CODE_TYPE", "CODE_VALUE", "CODE_DESC_EN", "ACTIVE_FLAG"])
        g.sqlcheck("2300-READ-CODE-LOOKUP", on_ok=["ADD 1 TO WS-CODE-LOOKUP-READ"])

    return {"handled_tables": {"CLR.T_CLAIM", "CLR.T_RESERVE", "CLR.T_RESERVE_MOVEMENT", "CLR.T_CODE_LOOKUP"},
            "handled_calls": {"CLRCM030"},
            "param_keys": [("TRI_T3_MIN_GBP", "WS-T3-MIN-GBP")],
            "row_steps": [("2300-READ-CODE-LOOKUP", lookup_code, None, "DEFAULT RESERVE CODE ROW FOR THE PERIL"),
                          ("3000-CREATE-CLAIM", create_claim, None, "INSERT THE CLAIM HEADER"),
                          ("4000-CREATE-DEFAULT-RESERVE", default_reserve, None, "DEFAULT RESERVE AND IN MOVEMENT")]}


def s_st040(g):
    ws(g, "05  WS-RSV-TYPE-IX           PIC S9(4)  COMP VALUE ZERO.")
    ws01(g, "01  WS-RSV-TYPES                PIC X(6)   VALUE 'IDEXLG'.")
    ws01(g, "01  WS-RSV-TYPE-TBL REDEFINES WS-RSV-TYPES.")
    ws(g, "05  WS-RSV-TYPE             PIC X(2)   OCCURS 3 TIMES.")
    ws(g, "05  WS-CLOSE-TYPE           PIC X(2)   VALUE SPACES.")
    ws(g, "05  WS-OLD-OUTSTANDING      PIC S9(11)V99 COMP-3 VALUE ZERO.")

    def finalise():
        g.b("MOVE PAYR-CLAIM-ID TO STLR-CLAIM-ID")
        g.update("CLR.T_SETTLEMENT", [("FINAL_FLAG", "'Y'"), ("ACCEPTED_DT", "CURRENT DATE")],
                 ["WHERE CLAIM_ID = :PAYR-CLAIM-ID", "  AND FINAL_FLAG = 'N'"])
        g.sqlcheck("4000-FINALISE-SETTLEMENT", on_ok=["ADD 1 TO WS-SETTLEMENT-WRITTEN"])

    def close_reserve():
        g.c("FINAL SETTLEMENT: CLOSE EVERY OPEN RESERVE ON THE CLAIM (BR-RSV-014).")
        g.c("THE OUTSTANDING AMOUNT BEFORE CLOSE IS RETURNED BY OLD TABLE AND")
        g.c("POSTED AS A NEGATIVE ST MOVEMENT.")
        g.b("PERFORM VARYING WS-RSV-TYPE-IX FROM 1 BY 1 UNTIL WS-RSV-TYPE-IX > 3")
        g.b("MOVE WS-RSV-TYPE(WS-RSV-TYPE-IX) TO WS-CLOSE-TYPE", 1)
        g.sql([("SELECT RSV_ID, RSV_OUTSTANDING_AMT", None),
               "  INTO :RSV-RSV-ID, :WS-OLD-OUTSTANDING",
               "  FROM OLD TABLE (",
               ("UPDATE CLR.T_RESERVE SET RSV_OUTSTANDING_AMT = 0,", ["PL-238:n", "W:UPDATE:CLR.T_RESERVE"]),
               ("       RSV_STATUS = 'C',", "ST040-STATUS"),
               "       LAST_UPD_TS = CURRENT TIMESTAMP,",
               "       LAST_UPD_PGM = :WS-PGM-ID,",
               "       LAST_UPD_USER = :WS-USER-ID",
               " WHERE CLAIM_ID = :PAYR-CLAIM-ID",
               "   AND RSV_TYPE_CD = :WS-CLOSE-TYPE",
               "   AND RSV_STATUS = 'O' )"], 1)
        g.b("EVALUATE SQLCODE", 1)
        g.b("WHEN 0", 2)
        g.b("ADD 1 TO WS-RESERVE-WRITTEN", 3)
        g.b("COMPUTE WS-OLD-OUTSTANDING = 0 - WS-OLD-OUTSTANDING", 3)
        g.perform("5100-POST-CLOSE-MOVEMENT", 3)
        g.b("WHEN +100", 2)
        g.b("CONTINUE", 3)
        g.b("WHEN OTHER", 2)
        g.b("MOVE '5000-CLOSE-RESERVE' TO ERR-PARA", 3)
        g.b("PERFORM 8000-SQL-ERROR", 3)
        g.b("END-EVALUATE", 1)
        g.b("END-PERFORM", mark="PL-238:e")

    def close_movement():
        g.b("MOVE PAYR-CLAIM-ID TO RSVM-CLAIM-ID")
        _movement(g, "ST", "WS-OLD-OUTSTANDING", "FSET", mark="ST040-MOVE")

    def close_claim():
        g.update("CLR.T_CLAIM", [("CLAIM_STATUS", "'CS'"), ("CLOSED_DT", "CURRENT DATE")],
                 ["WHERE CLAIM_ID = :PAYR-CLAIM-ID"], mark="ST040-CLAIM")
        g.sqlcheck("5500-CLOSE-CLAIM", on_ok=["ADD 1 TO WS-CLAIM-WRITTEN"])

    g.facts.append(Fact("PL-238", ("PL-238:n", "PL-238:e"), "UPDATE CLR.T_RESERVE SET RSV_OUTSTANDING_AMT = 0",
                        "CLRST040 paragraph 5000-CLOSE-RESERVE executes UPDATE CLR.T_RESERVE SET RSV_OUTSTANDING_AMT = 0, "
                        "RSV_STATUS = 'C' on final settlement.",
                        world_ref="PROGRAM:CLRST040#writes_tables:CLR.T_RESERVE", placement="PL-238"))
    g.facts.append(Fact("st040-status", ("ST040-STATUS", "ST040-STATUS"), "RSV_STATUS = 'C'",
                        "CLRST040 sets RSV_STATUS = 'C' (closed) on each reserve it closes.",
                        world_ref="PROGRAM:CLRST040#notes"))
    return {"drive": "CLR.T_PAYMENT", "drive_where": ["PAY_STATUS = 'CF'", "LAST_UPD_TS >= :WS-LAST-RUN-TS"],
            "handled_tables": {"CLR.T_SETTLEMENT", "CLR.T_RESERVE", "CLR.T_RESERVE_MOVEMENT", "CLR.T_CLAIM"},
            "row_steps": [("4000-FINALISE-SETTLEMENT", finalise, None, "MARK THE SETTLEMENT FINAL"),
                          ("5000-CLOSE-RESERVE", close_reserve, None, "CLOSE THE CASE RESERVES"),
                          ("5500-CLOSE-CLAIM", close_claim, None, "CLOSE THE CLAIM AS SETTLED")],
            "extra_paras": [("5100-POST-CLOSE-MOVEMENT", close_movement, None, "ST MOVEMENT FOR A CLOSED RESERVE")]}


def s_rc050(g):
    ws(g, "05  WS-RECEIPT-AMT           PIC S9(11)V99 COMP-3 VALUE ZERO.")

    def parse():
        g.b("MOVE WS-INPUT-AREA(1:10) TO SUBC-SUBRO-CASE-ID")
        g.b("COMPUTE WS-RECEIPT-AMT = FUNCTION NUMVAL(WS-INPUT-AREA(11:15))")

    def post():
        g.c("RECOVERY RECEIPT: RECORD THE RECEIPT, THEN NET IT FROM THE CASE")
        g.c("RESERVE (RECOVERY ESTIMATE AND OUTSTANDING) AND POST AN RC MOVEMENT.")
        g.b("MOVE SUBC-CLAIM-ID TO RCVR-CLAIM-ID")
        g.b("MOVE SUBC-SUBRO-CASE-ID TO RCVR-SUBRO-CASE-ID")
        g.b("MOVE 'SB' TO RCVR-RCV-TYPE-CD")
        g.b("MOVE WS-RECEIPT-AMT TO RCVR-RCV-RECEIVED-AMT")
        g.b("MOVE 'PT' TO RCVR-RCV-STATUS")
        g.insert("CLR.T_RECOVERY", mark="RC050-RCV")
        g.sqlcheck("3000-POST-RECEIPT", on_ok=["ADD 1 TO WS-RECOVERY-WRITTEN"])
        g.b("MOVE RCVR-CURRENCY-CD TO WS-CCY-FROM")
        g.b("MOVE WS-RECEIPT-AMT TO WS-CCY-AMOUNT")
        g.b("MOVE WS-RUN-DATE TO WS-CCY-RATE-DT")
        g.call("CLRCM030")
        g.sql(["SELECT RSV_ID",
               "  INTO :RSV-RSV-ID",
               "  FROM FINAL TABLE (",
               ("UPDATE CLR.T_RESERVE", ["PL-239:n", "W:UPDATE:CLR.T_RESERVE"]),
               ("   SET RSV_RECOVERY_EST_AMT = RSV_RECOVERY_EST_AMT - :WS-RECEIPT-AMT", None),
               ("     , RSV_OUTSTANDING_AMT = RSV_OUTSTANDING_AMT - :WS-RECEIPT-AMT", "RC050-OUT"),
               "     , RSV_GBP_EQUIV_AMT = RSV_GBP_EQUIV_AMT - :WS-CCY-GBP-AMOUNT",
               "     , LAST_UPD_TS = CURRENT TIMESTAMP",
               "     , LAST_UPD_PGM = :WS-PGM-ID",
               " WHERE CLAIM_ID = :SUBC-CLAIM-ID",
               "   AND RSV_TYPE_CD = 'ID'",
               ("   AND RSV_STATUS = 'O' )", "PL-239:e")])
        g.sqlcheck("3000-POST-RECEIPT", on_ok=["ADD 1 TO WS-RESERVE-WRITTEN"])
        g.b("MOVE SUBC-CLAIM-ID TO RSVM-CLAIM-ID")
        g.b("COMPUTE WS-RECEIPT-AMT = 0 - WS-RECEIPT-AMT")
        _movement(g, "RC", "WS-RECEIPT-AMT", "RCPT", mark="RC050-MOVE")

    g.facts.append(Fact("PL-239", ("PL-239:n", "PL-239:e"), "SET RSV_RECOVERY_EST_AMT = RSV_RECOVERY_EST_AMT",
                        "CLRRC050 paragraph 3000-POST-RECEIPT updates RSV_RECOVERY_EST_AMT and RSV_OUTSTANDING_AMT on "
                        "CLR.T_RESERVE when a recovery receipt is posted.",
                        world_ref="PROGRAM:CLRRC050#writes_tables:CLR.T_RESERVE", placement="PL-239"))
    return {"drive": "FILE",
            "handled_tables": {"CLR.T_RECOVERY", "CLR.T_RESERVE", "CLR.T_RESERVE_MOVEMENT"},
            "handled_calls": {"CLRCM030"},
            "pre_row_steps": [("2250-PARSE-RECEIPT", parse, None, "SPLIT THE RECEIPT RECORD")],
            "row_steps": [("3000-POST-RECEIPT", post, None, "POST ONE RECOVERY RECEIPT")]}


def s_rs010(g):
    ws(g, "05  WS-LLNT-GBP              PIC S9(11)V99 COMP-3 VALUE ZERO.")

    def set_reserve():
        g.c("INITIAL RESERVE: AUTHORITY CHECK (CLRRS015), GBP EQUIVALENT")
        g.c("(CLRCM030), INSERT, IN MOVEMENT, AUDIT (CLRCM020).")
        g.b("MOVE WS-USER-ID TO WS-RA-USER")
        g.b("MOVE CLM-CURRENCY-CD TO WS-RA-CURRENCY RSV-CURRENCY-CD")
        labs = {f["name"]: lab for lab, f in g.map_labels}
        g.b(f"COMPUTE WS-RA-AMOUNT = FUNCTION NUMVAL({labs['RSV-AMT']}I)")
        g.call("CLRRS015")
        g.b("IF WS-RA-RESULT NOT = 'Y'")
        g.b("SET WS-ERROR-FOUND TO TRUE", 1)
        g.bw("MOVE 'AMOUNT ABOVE YOUR RESERVE AUTHORITY' TO MSGO", 1)
        g.b("ELSE")
        g.b("MOVE CLM-CURRENCY-CD TO WS-CCY-FROM", 1)
        g.b("MOVE WS-RA-AMOUNT TO WS-CCY-AMOUNT", 1)
        g.b("MOVE WS-RUN-DATE TO WS-CCY-RATE-DT", 1)
        g.call("CLRCM030", 1)
        g.perform("3100-INSERT-RESERVE", 1)
        g.b("END-IF")

    def ins():
        labs = {f["name"]: lab for lab, f in g.map_labels}
        g.b("MOVE CA-CLAIM-ID TO RSV-CLAIM-ID")
        g.b(f"MOVE {labs['RSV-TYPE']}I TO RSV-RSV-TYPE-CD")
        g.b("MOVE WS-RA-AMOUNT TO RSV-RSV-INITIAL-AMT RSV-RSV-OUTSTANDING-AMT")
        g.b("MOVE WS-CCY-GBP-AMOUNT TO RSV-RSV-GBP-EQUIV-AMT")
        g.b("MOVE 'O' TO RSV-RSV-STATUS")
        g.b("MOVE WS-RA-REQUIRED-LVL TO RSV-RSV-AUTH-LEVEL")
        g.b("MOVE WS-USER-ID TO RSV-RSV-SET-BY-USER")
        g.insert("CLR.T_RESERVE", mark="RS010-INS")
        g.sqlcheck("3100-INSERT-RESERVE", on_ok=["ADD 1 TO WS-RESERVE-WRITTEN"])
        g.sql(["VALUES IDENTITY_VAL_LOCAL() INTO :RSV-RSV-ID"])
        g.b("MOVE WS-CCY-GBP-AMOUNT TO RSVM-MOVE-GBP-AMT")
        _movement(g, "IN", "WS-RA-AMOUNT", "INIT", mark="RS010-MOVE")
        g.b("IF WS-CCY-GBP-AMOUNT >= WS-LLNT-GBP")
        g.bw("MOVE 'RESERVE SET - LARGE LOSS LEVEL REACHED' TO MSGO", 1)
        g.b("END-IF")
        g.prep_call("CLRCM020", key="CA-CLAIM-ID")
        g.call("CLRCM020")

    g.facts.append(Fact("PL-240", ("CALL:CLRCM040", "CALL:CLRCM020"), "CALL 'CLRRS015'",
                        "CLRRS010 inserts into CLR.T_RESERVE and calls CLRRS015, CLRCM030, CLRCM040, CLRCM020, CLRCM050 and CLRCM070.",
                        world_ref="PROGRAM:CLRRS010#calls_programs", placement="PL-240", extra={"span": "calls"}))
    g.facts.append(Fact("rs010-ins", ("RS010-INS", "RS010-INS"), "INSERT INTO CLR.T_RESERVE",
                        "CLRRS010 (transaction RS01) writes the initial reserve with INSERT INTO CLR.T_RESERVE.",
                        world_ref="PROGRAM:CLRRS010#writes_tables:CLR.T_RESERVE"))
    return {"handled_tables": {"CLR.T_RESERVE", "CLR.T_RESERVE_MOVEMENT"},
            "handled_calls": {"CLRRS015", "CLRCM030", "CLRCM020"},
            "param_keys": [("RSV_LLNT_GBP", "WS-LLNT-GBP")],
            "row_steps": [("3000-SET-INITIAL-RESERVE", set_reserve, None, "SET THE INITIAL RESERVE")],
            "extra_paras": [("3100-INSERT-RESERVE", ins, None, "INSERT THE RESERVE ROW")]}


def s_rs020(g):
    ws(g, "05  WS-NEW-AMT               PIC S9(11)V99 COMP-3 VALUE ZERO.")
    ws(g, "05  WS-OLD-AMT               PIC S9(11)V99 COMP-3 VALUE ZERO.")
    ws(g, "05  WS-DELTA-AMT             PIC S9(11)V99 COMP-3 VALUE ZERO.")

    def adjust():
        g.c("RESERVE ADJUSTMENT. AUTHORITY IS CHECKED FIRST; ABOVE-AUTHORITY")
        g.c("CHANGES ARE QUEUED FOR APPROVAL THROUGH CLRRS040.")
        labs = {f["name"]: lab for lab, f in g.map_labels}
        g.b(f"MOVE FUNCTION NUMVAL({labs['NEW-AMT']}I) TO WS-NEW-AMT WS-RA-AMOUNT", mark="PL-241:s")
        g.b("MOVE WS-USER-ID TO WS-RA-USER")
        g.b("MOVE CLM-CURRENCY-CD TO WS-RA-CURRENCY")
        g.call("CLRRS015")
        g.b("IF WS-RA-RESULT NOT = 'Y'")
        g.call("CLRRS040", 1)
        g.bw("MOVE 'CHANGE QUEUED FOR APPROVAL' TO MSGO", 1)
        g.b("ELSE")
        g.b("MOVE CLM-CURRENCY-CD TO WS-CCY-FROM", 1)
        g.b("MOVE WS-NEW-AMT TO WS-CCY-AMOUNT", 1)
        g.b("MOVE WS-RUN-DATE TO WS-CCY-RATE-DT", 1)
        g.call("CLRCM030", 1)
        g.b(f"MOVE FUNCTION NUMVAL({labs['RSV-ID']}I) TO RSV-RSV-ID", 1)
        g.sql(["SELECT RSV_OUTSTANDING_AMT",
               "  INTO :WS-OLD-AMT",
               "  FROM OLD TABLE (",
               ("UPDATE CLR.T_RESERVE", ["PL-241:n", "W:UPDATE:CLR.T_RESERVE"]),
               "   SET RSV_OUTSTANDING_AMT = :WS-NEW-AMT",
               "     , RSV_GBP_EQUIV_AMT = :WS-CCY-GBP-AMOUNT",
               "     , RSV_AUTH_LEVEL = :WS-RA-REQUIRED-LVL",
               "     , RSV_SET_BY_USER = :WS-USER-ID",
               "     , RSV_NEXT_REVIEW_DT = :RSV-RSV-NEXT-REVIEW-DT",
               "     , LAST_UPD_TS = CURRENT TIMESTAMP",
               "     , LAST_UPD_PGM = :WS-PGM-ID",
               " WHERE RSV_ID = :RSV-RSV-ID",
               ("   AND RSV_STATUS = 'O' )", "PL-241:e")], 1)
        g.sqlcheck("3000-ADJUST", 1, on_ok=["ADD 1 TO WS-RESERVE-WRITTEN"])
        g.b("COMPUTE WS-DELTA-AMT = WS-NEW-AMT - WS-OLD-AMT", 1)
        g.perform("3100-POST-ADJUSTMENT", 1)
        g.b("END-IF")

    def post():
        g.b("MOVE CA-CLAIM-ID TO RSVM-CLAIM-ID")
        _movement(g, "AD", "WS-DELTA-AMT", "ADJ ", mark="RS020-MOVE")
        g.prep_call("CLRCM020", key="CA-CLAIM-ID")
        g.call("CLRCM020")

    g.facts.append(Fact("PL-241", ("PL-241:s", "PL-241:e"), "UPDATE CLR.T_RESERVE",
                        "CLRRS020 paragraph 3000-ADJUST updates CLR.T_RESERVE (reserve adjustment) after CALL 'CLRRS015'.",
                        world_ref="PROGRAM:CLRRS020#writes_tables:CLR.T_RESERVE", placement="PL-241"))
    g.facts.append(Fact("rs020-auth", ("PL-241:s", "PL-241:e"), "CALL 'CLRRS040' USING DFHEIBLK",
                        "When CLRRS015 refuses the authority, CLRRS020 calls CLRRS040 (reserve approval queue) instead of updating.",
                        world_ref="PROGRAM:CLRRS020#calls_programs"))
    return {"handled_tables": {"CLR.T_RESERVE", "CLR.T_RESERVE_MOVEMENT"},
            "handled_calls": {"CLRRS015", "CLRCM030", "CLRCM020", "CLRRS040"},
            "row_steps": [("3000-ADJUST", adjust, None, "ADJUST THE RESERVE")],
            "extra_paras": [("3100-POST-ADJUSTMENT", post, None, "AD MOVEMENT AND AUDIT")]}


def s_rs110(g):
    ws(g, "05  WS-REVIEW-DAYS           PIC S9(4)  COMP VALUE ZERO.")
    ws(g, "05  WS-NEXT-REVIEW-DT        PIC X(10)  VALUE SPACES.")
    ws(g, "05  WS-DATE-INT              PIC S9(9)  COMP VALUE ZERO.")
    ws(g, "05  WS-YYYYMMDD              PIC 9(8)   VALUE ZERO.")

    def schedule():
        g.c("TIER-3 REVIEW CADENCE (BR-RSV-007) IS A PARAMETER, NOT A CONSTANT:")
        g.c("RSV_T3_REVIEW_DAYS IS READ THROUGH CLRCM040 FOR EVERY RUN DATE.")
        g.b("MOVE 'RSV_T3_REVIEW_DAYS' TO PARM-PARAM-KEY", mark="PL-242:s")
        g.call("CLRCM040")
        g.b("MOVE FUNCTION NUMVAL(PARM-PARAM-VALUE) TO WS-REVIEW-DAYS")
        g.b("MOVE FUNCTION CURRENT-DATE(1:8) TO WS-YYYYMMDD")
        g.b("COMPUTE WS-DATE-INT = FUNCTION INTEGER-OF-DATE(WS-YYYYMMDD)")
        g.b("+ WS-REVIEW-DAYS", 1)
        g.b("COMPUTE WS-YYYYMMDD = FUNCTION DATE-OF-INTEGER(WS-DATE-INT)")
        g.b("STRING WS-YYYYMMDD(1:4) '-' WS-YYYYMMDD(5:2) '-' WS-YYYYMMDD(7:2)")
        g.b("DELIMITED BY SIZE INTO DW-IN-DATE", 1)
        g.b("MOVE 'UK' TO DW-CALENDAR")
        g.b("MOVE ZERO TO DW-BUS-DAYS")
        g.call("CLRCM010")
        g.b("MOVE DW-OUT-DATE TO WS-NEXT-REVIEW-DT")
        g.sql(["SELECT RSV_ID",
               "  INTO :RSV-RSV-ID",
               "  FROM FINAL TABLE (",
               ("UPDATE CLR.T_RESERVE", "W:UPDATE:CLR.T_RESERVE"),
               ("   SET RSV_NEXT_REVIEW_DT = :WS-NEXT-REVIEW-DT", "PL-242:n"),
               "     , LAST_UPD_TS = CURRENT TIMESTAMP",
               "     , LAST_UPD_PGM = :WS-PGM-ID",
               "     , LAST_UPD_USER = :WS-USER-ID",
               " WHERE CLAIM_ID = :TIR-CLAIM-ID",
               "   AND RSV_TYPE_CD = 'ID'",
               ("   AND RSV_STATUS = 'O' )", "PL-242:e")])
        g.sqlcheck("2000-SCHEDULE", on_ok=["ADD 1 TO WS-RESERVE-WRITTEN"])
        g.b("IF WS-ROW-FOUND")
        g.perform("2100-RECORD-REVIEW", 1)
        g.b("END-IF")

    def record():
        g.b("MOVE TIR-CLAIM-ID TO RSVM-CLAIM-ID DIAR-CLAIM-ID")
        g.b("MOVE ZERO TO RSVM-MOVE-GBP-AMT")
        _movement(g, "RV", "ZERO", "T3RV", mark="RS110-MOVE")
        g.b("MOVE WS-NEXT-REVIEW-DT TO DIAR-DUE-DT")
        g.b("MOVE 'RREV' TO DIAR-DIARY-TYPE-CD")
        g.b("MOVE 'N' TO DIAR-DONE-FLAG")
        g.b("MOVE WS-RUN-ID TO DIAR-BATCH-RUN-ID")
        g.insert("CLR.T_DIARY", mark="RS110-DIARY")
        g.sqlcheck("2100-RECORD-REVIEW", on_ok=["ADD 1 TO WS-DIARY-WRITTEN"])
        g.b("MOVE TIR-CLAIM-ID TO WS-DIA-CLAIM-ID")
        g.b("MOVE 'CHAS' TO WS-DIA-TYPE")
        g.b("MOVE WS-NEXT-REVIEW-DT TO WS-DIA-DUE-DT")
        g.call("CLRCM090")
        g.prep_call("CLRCM020", key="TIR-CLAIM-ID")
        g.call("CLRCM020")

    g.facts.append(Fact("PL-242", ("PL-242:s", "PL-242:e"), "MOVE 'RSV_T3_REVIEW_DAYS' TO PARM-PARAM-KEY",
                        "CLRRS110 paragraph 2000-SCHEDULE reads RSV_T3_REVIEW_DAYS via CLRCM040 and updates "
                        "RSV_NEXT_REVIEW_DT on CLR.T_RESERVE.",
                        world_ref="PROGRAM:CLRRS110#writes_tables:CLR.T_RESERVE", placement="PL-242"))
    g.facts.append(Fact("rs110-next", ("PL-242:n", "PL-242:n"), "SET RSV_NEXT_REVIEW_DT = :WS-NEXT-REVIEW-DT",
                        "CLRRS110 sets RSV_NEXT_REVIEW_DT on CLR.T_RESERVE to the computed next Tier-3 review date.",
                        world_ref="PROGRAM:CLRRS110#writes_tables:CLR.T_RESERVE"))
    return {"handled_tables": {"CLR.T_RESERVE", "CLR.T_RESERVE_MOVEMENT", "CLR.T_DIARY"},
            "handled_calls": {"CLRCM040", "CLRCM010", "CLRCM090", "CLRCM020"},
            "loop_names": ("1800-PROCESS-TIER3", "1810-FETCH-TIER3", "1820-REVIEW-CLAIM"),
            "row_steps": [("2000-SCHEDULE", schedule, None, "SCHEDULE THE NEXT TIER-3 REVIEW")],
            "extra_paras": [("2100-RECORD-REVIEW", record, None, "RV MOVEMENT, DIARY AND AUDIT")]}


def s_rs130(g):
    ws(g, "05  WS-INDEX-PCT             PIC S9(3)V9(4) COMP-3 VALUE ZERO.")
    ws(g, "05  WS-MONTH-FACTOR          PIC S9(2)V9(7) COMP-3 VALUE ZERO.")
    ws(g, "05  WS-OLD-OUTSTANDING       PIC S9(11)V99 COMP-3 VALUE ZERO.")
    ws(g, "05  WS-IX-DELTA              PIC S9(11)V99 COMP-3 VALUE ZERO.")

    def factor():
        g.c("ANNUAL BI INDEXATION RATE (BR-RSV-009) COMES FROM CLR.T_PARAM;")
        g.c("IT IS CONVERTED TO A MONTHLY COMPOUNDING FACTOR.")
        g.b("MOVE 'RSV_BI_INDEX_PCT' TO PARM-PARAM-KEY")
        g.call("CLRCM040")
        g.b("MOVE FUNCTION NUMVAL(PARM-PARAM-VALUE) TO WS-INDEX-PCT")
        g.b("COMPUTE WS-MONTH-FACTOR ROUNDED =")
        g.b("(1 + WS-INDEX-PCT / 100) ** (1 / 12)", 1)

    def index():
        g.sql(["SELECT RSV_ID, RSV_OUTSTANDING_AMT",
               "  INTO :RSV-RSV-ID, :WS-OLD-OUTSTANDING",
               "  FROM OLD TABLE (",
               ("UPDATE CLR.T_RESERVE", ["PL-243:s", "W:UPDATE:CLR.T_RESERVE"]),
               "   SET RSV_OUTSTANDING_AMT =",
               ("       RSV_OUTSTANDING_AMT * :WS-MONTH-FACTOR", "PL-243:n"),
               "     , RSV_INDEX_FACTOR =",
               "       COALESCE(RSV_INDEX_FACTOR, 1) * :WS-MONTH-FACTOR",
               "     , LAST_UPD_TS = CURRENT TIMESTAMP",
               "     , LAST_UPD_PGM = :WS-PGM-ID",
               " WHERE CLAIM_ID = :CLM-CLAIM-ID",
               "   AND RSV_TYPE_CD = 'ID'",
               ("   AND RSV_STATUS = 'O' )", "PL-243:e")])
        g.sqlcheck("3000-INDEX", on_ok=["ADD 1 TO WS-RESERVE-WRITTEN"])
        g.b("IF WS-ROW-FOUND")
        g.b("COMPUTE WS-IX-DELTA ROUNDED =", 1)
        g.b("WS-OLD-OUTSTANDING * (WS-MONTH-FACTOR - 1)", 2)
        g.b("MOVE CLM-CLAIM-ID TO RSVM-CLAIM-ID", 1)
        g.b("MOVE ZERO TO RSVM-MOVE-GBP-AMT", 1)
        g.b("END-IF")
        _movement(g, "IX", "WS-IX-DELTA", "BIIX", mark="RS130-MOVE")
        g.prep_call("CLRCM020", key="CLM-CLAIM-ID")
        g.call("CLRCM020")

    g.facts.append(Fact("PL-243", ("PL-243:s", "PL-243:e"), "RSV_OUTSTANDING_AMT * :WS-MONTH-FACTOR",
                        "CLRRS130 paragraph 3000-INDEX multiplies RSV_OUTSTANDING_AMT by the monthly index factor and "
                        "updates CLR.T_RESERVE.",
                        world_ref="PROGRAM:CLRRS130#writes_tables:CLR.T_RESERVE", placement="PL-243"))
    return {"drive": "CLR.T_CLAIM", "drive_where": ["PERIL_CD = 'BIJ'", "CLAIM_STATUS IN ('OP', 'RO')"],
            "handled_tables": {"CLR.T_RESERVE", "CLR.T_RESERVE_MOVEMENT"},
            "handled_calls": {"CLRCM040", "CLRCM020"},
            "init_steps": [("1300-MONTHLY-FACTOR", factor, None, "MONTHLY INDEXATION FACTOR")],
            "row_steps": [("3000-INDEX", index, None, "INDEX ONE BODILY-INJURY RESERVE")]}


def s_rs150(g):
    def parse():
        g.b("MOVE FUNCTION NUMVAL(WS-INPUT-AREA(1:18)) TO RSV-RSV-ID")

    def corr():
        g.c("THIS UTILITY NEVER UPDATES CLR.T_RESERVE. A CORRECTION IS POSTED AS", mark=["PL-244:s", "RS150-NEVER"])
        g.c("A MOVEMENT ROW ONLY; THE RESERVE ITSELF IS LEFT AS IT IS.")
        g.b("IF WS-ROW-FOUND")
        g.b("MOVE RSV-RSV-ID TO RSVM-RSV-ID", 1)
        g.b("MOVE RSV-CLAIM-ID TO RSVM-CLAIM-ID", 1)
        g.b("MOVE 'AD' TO RSVM-MOVE-TYPE-CD", 1)
        g.b("COMPUTE RSVM-MOVE-AMT = FUNCTION NUMVAL(WS-INPUT-AREA(19:15))", 1)
        g.b("MOVE ZERO TO RSVM-MOVE-GBP-AMT", 1)
        g.b("MOVE 'CORR' TO RSVM-REASON-CD", 1)
        g.b("MOVE 'N' TO RSVM-EXTRACTED-FLAG", 1)
        g.b("MOVE WS-USER-ID TO RSVM-USER-ID", 1)
        g.b("MOVE WS-PGM-ID TO RSVM-PGM-ID", 1)
        g.insert("CLR.T_RESERVE_MOVEMENT", 1, mark="PL-244:n", omit=("EXTRACT_RUN_ID",))
        g.sqlcheck("3000-POST-CORRECTION", 1, on_ok=["ADD 1 TO WS-RESERVE-MOVEMENT-WRITTEN"])
        g.b("ELSE")
        g.b("ADD 1 TO WS-REJECT-CNT", 1, mark="PL-244:e")
        g.b("END-IF")

    g.facts.append(Fact("PL-244", ("PL-244:s", "PL-244:e"), "INSERT INTO CLR.T_RESERVE_MOVEMENT",
                        "CLRRS150 inserts correction rows into CLR.T_RESERVE_MOVEMENT only; it never updates CLR.T_RESERVE.",
                        world_ref="PROGRAM:CLRRS150#writes_tables", placement="PL-244"))
    g.facts.append(Fact("rs150-never", ("RS150-NEVER", "RS150-NEVER"), "THIS UTILITY NEVER UPDATES CLR.T_RESERVE",
                        "CLRRS150's comment states the correction utility never updates CLR.T_RESERVE; corrections are movements only.",
                        world_ref="PROGRAM:CLRRS150#notes", kind="general"))
    return {"drive": "FILE", "handled_tables": {"CLR.T_RESERVE_MOVEMENT"},
            "pre_row_steps": [("2250-PARSE-REQUEST", parse, None, "SPLIT THE CORRECTION REQUEST")],
            "row_steps": [("3000-POST-CORRECTION", corr, None, "POST ONE CORRECTION MOVEMENT")]}


def s_rs170(g):
    ws(g, "05  WS-HASH-TOTAL            PIC S9(15)V99 COMP-3 VALUE ZERO.")
    ws(g, "05  WS-PUT-COUNT             PIC S9(9)  COMP VALUE ZERO.")
    drive_sql = ["SELECT M.MOVE_ID, M.RSV_ID, M.CLAIM_ID, M.MOVE_TYPE_CD,",
                 "       M.MOVE_AMT, M.MOVE_GBP_AMT, M.MOVE_TS,",
                 "       C.PRODUCT_CD, C.PERIL_CD, C.TIER_CD, C.CURRENCY_CD",
                 ("  FROM CLR.T_RESERVE_MOVEMENT M", "R:CLR.T_RESERVE_MOVEMENT"),
                 ("  JOIN CLR.T_CLAIM C", "R:CLR.T_CLAIM"),
                 "    ON C.CLAIM_ID = M.CLAIM_ID",
                 (" WHERE M.EXTRACTED_FLAG = 'N'", "RS170-FLAGN"),
                 " ORDER BY M.MOVE_ID",
                 " FOR FETCH ONLY"]
    into = [":RSVM-MOVE-ID", ":RSVM-RSV-ID", ":RSVM-CLAIM-ID", ":RSVM-MOVE-TYPE-CD", ":RSVM-MOVE-AMT",
            ":RSVM-MOVE-GBP-AMT", ":RSVM-MOVE-TS", ":CLM-PRODUCT-CD", ":CLM-PERIL-CD", ":CLM-TIER-CD",
            ":CLM-CURRENCY-CD"]

    def put():
        g.c("BUILD ONE RSVMOVE RECORD (CLX-IF-042), WRITE IT TO DD RSVOUT AND")
        g.c("PUT IT TO QUEUE CLR.RSVMOVE.OUT THROUGH THE MQ WRAPPER CLRCM110.")
        g.b("INITIALIZE RSVMOVE-REC", mark="PL-247:s")
        g.b("MOVE 'MV' TO RM-REC-TYPE")
        g.b("MOVE 02 TO RM-REC-VERSION", add="CM-03", tag="CHUB142", mark="RS170-VERSION")
        g.b("MOVE WS-RUN-DATE TO RM-EXTRACT-DATE")
        g.b("MOVE RSVM-CLAIM-ID TO RM-CLAIM-ID")
        g.b("MOVE RSVM-RSV-ID TO RM-RSV-ID")
        g.b("MOVE RSVM-MOVE-ID TO RM-MOVE-ID")
        g.b("MOVE RSVM-MOVE-TYPE-CD TO RM-MOVE-TYPE")
        g.b("MOVE CLM-CURRENCY-CD TO RM-CURRENCY")
        g.b("MOVE RSVM-MOVE-AMT TO RM-AMOUNT")
        g.b("MOVE RSVM-MOVE-GBP-AMT TO RM-GBP-AMOUNT")
        g.b("MOVE CLM-PRODUCT-CD TO RM-PRODUCT")
        g.b("MOVE CLM-PERIL-CD TO RM-PERIL")
        g.b("MOVE CLM-TIER-CD TO RM-TIER")
        g.b("MOVE RSVM-MOVE-TS TO RM-MOVE-TS")
        g.b("WRITE RSVOUT-RECORD FROM RSVMOVE-REC")
        g.b("IF WS-RSVOUT-STATUS NOT = '00'")
        g.bw("DISPLAY WS-PGM-ID ' WRITE FAILED RSVOUT ' WS-RSVOUT-STATUS", 1)
        g.b("MOVE '3000-PUT' TO ERR-PARA", 1)
        g.b("PERFORM 8000-SQL-ERROR", 1)
        g.b("END-IF")
        g.b("MOVE 'MQPUT' TO WS-MQ-FUNCTION", mark="RS170-MQPUT")
        g.b("MOVE 'CLR.RSVMOVE.OUT' TO MQ-QUEUE-NAME", mark="RS170-QUEUE")
        g.b("MOVE LENGTH OF RSVMOVE-REC TO WS-MQ-BUFFER-LEN MQ-MSG-LEN")
        g.b("MOVE RSVMOVE-REC TO WS-MQ-BUFFER")
        g.call("CLRCM110")
        g.b("ADD 1 TO WS-PUT-COUNT")
        g.b("ADD RSVM-MOVE-GBP-AMT TO WS-HASH-TOTAL")

    def mark_():
        g.sql([("UPDATE CLR.T_RESERVE_MOVEMENT", "W:UPDATE:CLR.T_RESERVE_MOVEMENT"),
               ("   SET EXTRACTED_FLAG = 'Y'", "RS170-FLAGY"),
               "     , EXTRACT_RUN_ID = :WS-RUN-ID",
               " WHERE MOVE_ID = :RSVM-MOVE-ID",
               "   AND EXTRACTED_FLAG = 'N'"])
        g.sqlcheck("4000-MARK", on_ok=["ADD 1 TO WS-RESERVE-MOVEMENT-WRITTEN"])
        g.b("CONTINUE", mark="PL-247:e")

    def log_run():
        g.b("MOVE WS-RUN-ID TO IFLO-IF-RUN-ID IFLO-BATCH-RUN-ID")
        g.b("MOVE 'CLX-IF-042' TO IFLO-INTERFACE-ID", mark="RS170-IF042")
        g.b("MOVE WS-PUT-COUNT TO IFLO-RECORD-COUNT")
        g.b("MOVE WS-HASH-TOTAL TO IFLO-HASH-TOTAL")
        g.b("MOVE 'OK' TO IFLO-RUN-STATUS")
        g.b("MOVE 'UK' TO IFLO-BRANCH-CD")
        g.b("MOVE SPACES TO IFLO-COMMENT-TXT")
        g.insert("CLR.T_INTERFACE_LOG")
        g.sqlcheck("8500-LOG-RUN", on_ok=["ADD 1 TO WS-INTERFACE-LOG-WRITTEN"])

    g.facts.append(Fact("PL-247", ("PL-247:s", "PL-247:e"), "MOVE 'MQPUT' TO WS-MQ-FUNCTION",
                        "CLRRS170 MQPUTs RSVMOVE records to CLR.RSVMOVE.OUT (paragraph 3000-PUT) and sets EXTRACTED_FLAG = 'Y' "
                        "on CLR.T_RESERVE_MOVEMENT (paragraph 4000-MARK).",
                        world_ref="INTERFACE:CLX-IF-042#programs", placement="PL-247"))
    g.facts.append(Fact("rs170-flagy", ("RS170-FLAGY", "RS170-FLAGY"), "SET EXTRACTED_FLAG = 'Y'",
                        "CLRRS170 marks each extracted movement with SET EXTRACTED_FLAG = 'Y' on CLR.T_RESERVE_MOVEMENT.",
                        world_ref="TABLE:CLR.T_RESERVE_MOVEMENT#columns:EXTRACTED_FLAG"))
    g.facts.append(Fact("rs170-flagn", ("RS170-FLAGN", "RS170-FLAGN"), "WHERE M.EXTRACTED_FLAG = 'N'",
                        "CLRRS170's driving cursor selects only movements with EXTRACTED_FLAG = 'N' (joined to CLR.T_CLAIM).",
                        world_ref="JCL:CLRNRSV3#restart"))
    g.facts.append(Fact("rs170-queue", ("RS170-QUEUE", "RS170-QUEUE"), "MOVE 'CLR.RSVMOVE.OUT' TO MQ-QUEUE-NAME",
                        "CLRRS170 puts the CLX-IF-042 records to MQ queue CLR.RSVMOVE.OUT.",
                        world_ref="INTERFACE:CLX-IF-042#format"))
    g.facts.append(Fact("rs170-version", ("RS170-VERSION", "RS170-VERSION"), "MOVE 02 TO RM-REC-VERSION",
                        "CLRRS170 sets the RSVMOVE record version RM-REC-VERSION to 02 (added under CHUB-142).",
                        world_ref="COPYBOOK:RSVMOVE#field_history"))
    return {"drive": "CLR.T_RESERVE_MOVEMENT", "drive_sql": drive_sql, "fetch_into": into,
            "drive_cols": ["MOVE_ID"],
            "handled_tables": {"CLR.T_RESERVE_MOVEMENT", "CLR.T_INTERFACE_LOG", "CLR.T_CLAIM"},
            "handled_calls": {"CLRCM110"},
            "row_steps": [("3000-PUT", put, None, "WRITE AND MQPUT ONE RSVMOVE RECORD"),
                          ("4000-MARK", mark_, None, "FLAG THE MOVEMENT AS EXTRACTED")],
            "term_steps": [("8500-LOG-RUN", log_run, None, "RECORD THE RUN IN CLR.T_INTERFACE_LOG")]}


# ---------------------------------------------------------------------------------------------
# fraud
# ---------------------------------------------------------------------------------------------

def s_fr030(g):
    ws(g, "05  WS-REFER-THRESHOLD       PIC S9(4)  COMP VALUE ZERO.")
    ws(g, "05  WS-REFER-T3-THRESHOLD    PIC S9(4)  COMP VALUE ZERO.")
    ws(g, "05  WS-APPLIED-THRESHOLD     PIC S9(4)  COMP VALUE ZERO.")

    def thresholds():
        g.c("REFERRAL THRESHOLDS ARE READ FROM CLR.T_PARAM THROUGH CLRCM040 WITH")
        g.c("VALIDITY DATES. FRD_REFER_T3_THRESH APPLIES TO TIER-3 CLAIMS ONLY.")
        g.b("MOVE 'FRD_REFER_THRESH' TO PARM-PARAM-KEY", mark="PL-246:s")
        g.call("CLRCM040")
        g.b("MOVE FUNCTION NUMVAL(PARM-PARAM-VALUE) TO WS-REFER-THRESHOLD")
        g.b("MOVE 'FRD_REFER_T3_THRESH' TO PARM-PARAM-KEY", mark="PL-246:t3")
        g.call("CLRCM040")
        g.b("IF ERR-SQLCODE = ZERO AND PARM-PARAM-VALUE NOT = SPACES")
        g.b("MOVE FUNCTION NUMVAL(PARM-PARAM-VALUE) TO WS-REFER-T3-THRESHOLD", 1)
        g.b("ELSE")
        g.b("MOVE WS-REFER-THRESHOLD TO WS-REFER-T3-THRESHOLD", 1, mark="PL-246:e")
        g.b("END-IF")
        g.sql(["SELECT PARAM_DESC",
               "  INTO :PARM-PARAM-DESC",
               ("  FROM CLR.T_PARAM", "R:CLR.T_PARAM"),
               " WHERE PARAM_KEY = 'FRD_REFER_THRESH'",
               "   AND VALID_FROM <= CURRENT DATE",
               "   AND (VALID_TO IS NULL OR VALID_TO >= CURRENT DATE)"])
        g.sqlcheck("2000-GET-THRESHOLDS")

    def decide():
        g.b("IF TIR-TIER-CD = '3'")
        g.b("MOVE WS-REFER-T3-THRESHOLD TO WS-APPLIED-THRESHOLD", 1)
        g.b("ELSE")
        g.b("MOVE WS-REFER-THRESHOLD TO WS-APPLIED-THRESHOLD", 1)
        g.b("END-IF")
        labs = dict((f["name"], lab) for lab, f in g.map_labels) if g.map_labels else {}
        if "THRESHOLD" in labs:
            g.b(f"MOVE WS-APPLIED-THRESHOLD TO {labs['THRESHOLD']}O")
        g.b("IF FRDS-SCORE >= WS-APPLIED-THRESHOLD")
        g.perform("4000-CREATE-REFERRAL", 1)
        g.perform("4500-NOTIFY-SIU", 1)
        g.b("ELSE")
        g.bw("MOVE 'SCORE BELOW REFERRAL THRESHOLD' TO MSGO", 1)
        g.b("END-IF")

    def create():
        g.b("MOVE CA-CLAIM-ID TO FRDR-CLAIM-ID")
        g.b("MOVE FRDS-SCORE TO FRDR-REF-SCORE")
        g.b("MOVE WS-APPLIED-THRESHOLD TO FRDR-REF-THRESHOLD-APPLIED")
        g.b("MOVE 'ON' TO FRDR-REF-SOURCE-CD")
        g.b("MOVE TIR-TIER-CD TO FRDR-TIER-CD")
        g.b("MOVE 'OP' TO FRDR-REF-STATUS")
        g.b("MOVE 'N' TO FRDR-CUSTOMER-NOTICE-DEFER-FLAG")
        g.insert("CLR.T_FRAUD_REFERRAL", mark="FR030-INS")
        g.sqlcheck("4000-CREATE-REFERRAL", on_ok=["ADD 1 TO WS-FRAUD-REFERRAL-WRITTEN"])
        g.prep_call("CLRCM020", key="CA-CLAIM-ID")
        g.call("CLRCM020")

    def notify():
        g.b("MOVE 'MQPUT' TO WS-MQ-FUNCTION")
        g.b("MOVE 'CLR.SIUREF.OUT' TO MQ-QUEUE-NAME", mark="FR030-Q")
        g.b("MOVE FRDREF01-REC TO WS-MQ-BUFFER")
        g.b("MOVE LENGTH OF FRDREF01-REC TO WS-MQ-BUFFER-LEN")
        g.call("CLRCM110")

    g.facts.append(Fact("PL-246", ("PL-246:s", "PL-246:e"), "MOVE 'FRD_REFER_T3_THRESH' TO PARM-PARAM-KEY",
                        "CLRFR030 paragraph 2000-GET-THRESHOLDS calls CLRCM040 for FRD_REFER_THRESH and FRD_REFER_T3_THRESH "
                        "before deciding a referral.",
                        world_ref="PROGRAM:CLRFR030#calls_programs", placement="PL-246"))
    g.facts.append(Fact("fr030-q", ("FR030-Q", "FR030-Q"), "MOVE 'CLR.SIUREF.OUT' TO MQ-QUEUE-NAME",
                        "CLRFR030 sends each new referral to the SIU Case Manager queue CLR.SIUREF.OUT via CLRCM110.",
                        world_ref="INTERFACE:CLX-IF-011#format"))
    return {"handled_tables": {"CLR.T_FRAUD_REFERRAL", "CLR.T_PARAM"},
            "handled_calls": {"CLRCM040", "CLRCM110", "CLRCM020"},
            "init_steps": [("2000-GET-THRESHOLDS", thresholds, None, "REFERRAL THRESHOLDS FROM CLR.T_PARAM")],
            "row_steps": [("3000-DECIDE-REFERRAL", decide, None, "COMPARE THE SENTINEL SCORE")],
            "extra_paras": [("4000-CREATE-REFERRAL", create, None, "INSERT THE REFERRAL"),
                            ("4500-NOTIFY-SIU", notify, None, "REFERRAL MESSAGE TO SIU CASE MANAGER")]}


def s_fr040(g):
    def thresholds_c():
        g.c("REFERRAL THRESHOLDS FROM CLR.T_PARAM VIA CLRCM040 (CHUB-298):", mark="PL-274:s")
        g.c("FRD_REFER_THRESH (65 FROM 2026-04-01) AND FRD_REFER_T3_THRESH")
        g.c("(60 FOR TIER-3 CLAIMS FROM 2026-10-01).", mark="FR040C-VALUES")
        g.b("MOVE 'FRD_REFER_THRESH' TO PARM-PARAM-KEY", mark="FR040C-KEY1")
        g.call("CLRCM040")
        g.b("MOVE FUNCTION NUMVAL(PARM-PARAM-VALUE) TO WS-REFER-THRESHOLD")
        g.b("MOVE 'FRD_REFER_T3_THRESH' TO PARM-PARAM-KEY", mark="FR040C-KEY2")
        g.call("CLRCM040")
        g.b("IF ERR-SQLCODE = ZERO AND PARM-PARAM-VALUE NOT = SPACES")
        g.b("MOVE FUNCTION NUMVAL(PARM-PARAM-VALUE) TO WS-REFER-T3-THRESHOLD", 1)
        g.b("ELSE")
        g.b("MOVE WS-REFER-THRESHOLD TO WS-REFER-T3-THRESHOLD", 1)
        g.b("END-IF", mark="PL-274:e")

    def apply_():
        with g.src.added("CM-09", tag="CHUB298"):
            g.b("IF CLM-TIER-CD = '3'", mark="FR040C-TIER")
            g.b("MOVE WS-REFER-T3-THRESHOLD TO WS-APPLIED-THRESHOLD", 1)
            g.b("ELSE")
        g.src.emit(" " + "    " + "MOVE WS-REFER-THRESHOLD TO WS-APPLIED-THRESHOLD", rm="CM-09", mark="FR040-APPLY")
        with g.src.added("CM-09", tag="CHUB298"):
            g.b("MOVE WS-REFER-THRESHOLD TO WS-APPLIED-THRESHOLD", 1)
            g.b("END-IF")
        g.b("IF FRDS-SCORE >= WS-APPLIED-THRESHOLD", mark="FR040-CMP")
        g.perform("4000-CREATE-REFERRAL", 1)
        g.b("END-IF")

    def create():
        g.b("MOVE FRDS-CLAIM-ID TO FRDR-CLAIM-ID")
        g.b("MOVE FRDS-SCORE TO FRDR-REF-SCORE")
        g.b("MOVE WS-APPLIED-THRESHOLD TO FRDR-REF-THRESHOLD-APPLIED")
        g.b("MOVE 'BS' TO FRDR-REF-SOURCE-CD")
        g.b("MOVE CLM-TIER-CD TO FRDR-TIER-CD")
        g.b("MOVE 'OP' TO FRDR-REF-STATUS")
        g.b("MOVE 'N' TO FRDR-CUSTOMER-NOTICE-DEFER-FLAG")
        g.insert("CLR.T_FRAUD_REFERRAL", mark="FR040-INS")
        g.sqlcheck("4000-CREATE-REFERRAL", on_ok=["ADD 1 TO WS-FRAUD-REFERRAL-WRITTEN"])
        g.prep_call("CLRCM020", key="FRDS-CLAIM-ID")
        g.call("CLRCM020")

    # working storage: the drift (variant a) and the fix (variant c)
    g.ws_needs["ws"].append(("c", "REFERRAL THRESHOLD - SCORES AT OR ABOVE THIS VALUE ARE REFERRED", {"rm": "CM-09"}))
    g.ws_needs["ws"].append(("c", "REFERRAL THRESHOLDS - LOADED FROM CLR.T_PARAM BY CLRCM040",
                             {"add": "CM-09", "keep_seq": True, "tag": "CHUB298"}))
    g.ws_needs["ws"].append((0, "05  WS-REFER-THRESHOLD       PIC 9(3)   VALUE 070.", {"rm": "CM-09", "mark": "PL-245"}))
    g.ws_needs["ws"].append((0, "05  WS-REFER-THRESHOLD       PIC 9(3)   VALUE ZERO.",
                             {"add": "CM-09", "keep_seq": True, "tag": "CHUB298", "mark": "FR040C-WS1"}))
    g.ws_needs["ws"].append((0, "05  WS-REFER-T3-THRESHOLD    PIC 9(3)   VALUE ZERO.",
                             {"add": "CM-09", "tag": "CHUB298", "mark": "FR040C-WS2"}))
    g.ws_needs["ws"].append((0, "05  WS-APPLIED-THRESHOLD     PIC 9(3)   VALUE ZERO."))

    g.facts.append(Fact("PL-245", ("PL-245", "FR040-CMP"), "WS-REFER-THRESHOLD PIC 9(3) VALUE 070",
                        "CLRFR040 declares 05 WS-REFER-THRESHOLD PIC 9(3) VALUE 070 in WORKING-STORAGE and compares the "
                        "Sentinel score against it (hard-coded pre-2026 threshold; code drift).",
                        kind="contradiction_old", world_ref="PROGRAM:CLRFR040#hardcoded_constants", placement="PL-245",
                        extra={"contradictions": ["C05"], "span": "range"}))
    g.facts.append(Fact("PL-274", ("FR040C-WS1", "PL-274:e"), "FRD_REFER_THRESH (65 FROM 2026-04-01) AND FRD_REFER_T3_THRESH",
                        "After the follow-up commit CLRFR040 no longer hard-codes 070; it reads FRD_REFER_THRESH (65) and "
                        "FRD_REFER_T3_THRESH (60) via CLRCM040.",
                        kind="resync_change", world_ref="PROGRAM:CLRFR040#hardcoded_constants", placement="PL-274",
                        variant="c", extra={"span": "range"}))
    g.facts.append(Fact("fr040c-ws", ("FR040C-WS1", "FR040C-WS2"), "WS-REFER-THRESHOLD PIC 9(3) VALUE ZERO",
                        "In variant c, CLRFR040's WS-REFER-THRESHOLD has VALUE ZERO (no hard-coded 070); a Tier-3 threshold "
                        "field WS-REFER-T3-THRESHOLD is added.",
                        kind="resync_change", world_ref="PROGRAM:CLRFR040#hardcoded_constants", variant="c"))
    g.facts.append(Fact("fr040c-values", ("PL-274:s", "FR040C-VALUES"), "(60 FOR TIER-3 CLAIMS FROM 2026-10-01)",
                        "Variant c CLRFR040 documents FRD_REFER_THRESH 65 from 2026-04-01 and FRD_REFER_T3_THRESH 60 for "
                        "Tier-3 claims from 2026-10-01.",
                        kind="resync_change", world_ref="RULE:BR-FRD-031@v2#parameters", variant="c"))
    g.facts.append(Fact("fr040-src", ("FR040-INS", "FR040-INS"), "INSERT INTO CLR.T_FRAUD_REFERRAL",
                        "CLRFR040 (batch sweep) inserts referrals into CLR.T_FRAUD_REFERRAL with REF_SOURCE_CD 'BS'.",
                        world_ref="PROGRAM:CLRFR040#writes_tables:CLR.T_FRAUD_REFERRAL"))
    return {"drive": "CLR.T_FRAUD_SCORE",
            "handled_tables": {"CLR.T_FRAUD_REFERRAL"}, "handled_calls": {"CLRCM020"},
            "init_steps": [("2000-GET-THRESHOLDS", thresholds_c, "CM-09", "REFERRAL THRESHOLDS (CHUB-298)")],
            "row_steps": [("3000-APPLY-THRESHOLD", apply_, None, "COMPARE THE SCORE WITH THE THRESHOLD")],
            "extra_paras": [("4000-CREATE-REFERRAL", create, None, "INSERT THE BATCH REFERRAL")]}


def s_fr020(g):
    ws(g, "05  WS-WEB-TOKEN             PIC X(8)   VALUE SPACES.")
    ws(g, "05  WS-WEB-STATUS            PIC S9(8)  COMP VALUE ZERO.")
    ws(g, "05  WS-WEB-LEN               PIC S9(8)  COMP VALUE ZERO.")
    ws(g, "05  WS-SCORE-HOST            PIC X(40)  VALUE", mark="FR020-HOST")
    g.ws_needs["ws"].append((2, "'fraudnet.corvane.internal'.", {"rm": "CM-02"}))
    g.ws_needs["ws"].append((2, "'sentinel.corvane.internal'.", {"add": "CM-02", "keep_seq": True,
                                                                  "tag": "CHUB119", "mark": "FR020-HOST2"}))

    def request():
        g.c("SYNCHRONOUS SCORE REQUEST (CLX-IF-008) OVER HTTPS THROUGH CICS WEB.")
        g.b("MOVE CA-CLAIM-ID TO SR-CLAIM-ID")
        g.b("MOVE FRDL-CLAIM-ID-A TO SR-CLAIM-ID")
        g.b("EXEC CICS WEB OPEN HOST(WS-SCORE-HOST) SCHEME(HTTPS)")
        g.b("SESSTOKEN(WS-WEB-TOKEN) RESP(WS-RESP) END-EXEC", 1)
        g.b("IF WS-RESP NOT = DFHRESP(NORMAL)")
        g.b("MOVE 12 TO CA-RETURN-CD", 1)
        g.bw("MOVE 'SCORING SERVICE UNAVAILABLE' TO CA-MSG", 1)
        g.b("SET WS-ERROR-FOUND TO TRUE", 1)
        g.b("ELSE")
        g.b("EXEC CICS WEB CONVERSE SESSTOKEN(WS-WEB-TOKEN) POST", 1)
        g.b("FROM(SENT-REQUEST)", 2)
        g.b("INTO(SENT-RESPONSE) TOLENGTH(WS-WEB-LEN)", 2)
        g.b("STATUSCODE(WS-WEB-STATUS) RESP(WS-RESP) END-EXEC", 2)
        g.b("EXEC CICS WEB CLOSE SESSTOKEN(WS-WEB-TOKEN) END-EXEC", 1)
        g.b("MOVE SS-CLAIM-ID TO FRDS-CLAIM-ID", 1)
        g.b("MOVE SS-SCORE TO FRDS-SCORE", 1)
        g.b("MOVE SS-MODEL-VERSION TO FRDS-MODEL-VERSION", 1)
        g.b("MOVE SS-REASON-1 TO FRDS-TOP-REASON-1", 1)
        g.b("MOVE SS-REASON-2 TO FRDS-TOP-REASON-2", 1)
        g.b("END-IF")

    g.facts.append(Fact("fr020-host", ("FR020-HOST", "FR020-HOST2"), "'sentinel.corvane.internal'",
                        "CLRFR020 calls the Sentinel scoring endpoint host sentinel.corvane.internal (switched from "
                        "fraudnet.corvane.internal under CHUB-119).",
                        world_ref="PROGRAM:CLRFR020#notes"))
    return {"row_steps": [("3000-REQUEST-SCORE", request, None, "SENTINEL SCORE REQUEST")]}


def s_fr060(g):
    ws(g, "05  WS-NOTICE-DAYS           PIC S9(4)  COMP VALUE ZERO.")
    ws(g, "05  WS-DUE-DT                PIC X(10)  VALUE SPACES.")
    cur = [(0, "EXEC SQL"),
           (0, "    DECLARE C-NEW-REFERRALS CURSOR WITH HOLD FOR"),
           (0, "    SELECT REF_ID, CLAIM_ID"),
           (0, "      FROM FINAL TABLE ("),
           (0, "    UPDATE CLR.T_FRAUD_REFERRAL", {"mark": ["W:UPDATE:CLR.T_FRAUD_REFERRAL", "FR060-UPD"]}),
           (0, "       SET CUSTOMER_NOTICE_DUE_DT = :WS-DUE-DT"),
           (0, "         , LAST_UPD_TS = CURRENT TIMESTAMP"),
           (0, "         , LAST_UPD_PGM = :WS-PGM-ID"),
           (0, "     WHERE CUSTOMER_NOTICE_DUE_DT IS NULL"),
           (0, "       AND CUSTOMER_NOTICE_DEFER_FLAG = 'N' )"),
           (0, "END-EXEC.")]
    g.ws_needs["cursors"] += [("c", ""), ("c", "REFERRALS STILL WITHOUT A CUSTOMER NOTICE DUE DATE")] + cur

    def due_date():
        g.c("CUSTOMER NOTICE WITHIN FRD_NOTICE_BUS_DAYS BUSINESS DAYS OF THE")
        g.c("REFERRAL (BR-FRD-032, NISA CIRCULAR 2026/04).")
        g.b("MOVE 'FRD_NOTICE_BUS_DAYS' TO PARM-PARAM-KEY", mark="FR060-KEY")
        g.call("CLRCM040")
        g.b("MOVE FUNCTION NUMVAL(PARM-PARAM-VALUE) TO WS-NOTICE-DAYS")
        g.b("MOVE WS-RUN-DATE TO DW-IN-DATE")
        g.b("MOVE 'UK' TO DW-CALENDAR")
        g.b("MOVE WS-NOTICE-DAYS TO DW-BUS-DAYS")
        g.call("CLRCM010")
        g.b("MOVE DW-OUT-DATE TO WS-DUE-DT")

    def schedule():
        g.sql(["OPEN C-NEW-REFERRALS"])
        g.sqlcheck("2000-SCHEDULE-NOTICES", notfound_ok=False)
        g.b("PERFORM UNTIL WS-END-OF-DATA")
        g.sql(["FETCH C-NEW-REFERRALS", " INTO :FRDN-REF-ID, :FRDN-CLAIM-ID"], 1)
        g.b("EVALUATE SQLCODE", 1)
        g.b("WHEN 0", 2)
        g.b("ADD 1 TO WS-FRAUD-REFERRAL-WRITTEN", 3)
        g.perform("2100-CREATE-NOTICE", 3)
        g.b("WHEN +100", 2)
        g.b("SET WS-END-OF-DATA TO TRUE", 3)
        g.b("WHEN OTHER", 2)
        g.b("MOVE '2000-SCHEDULE-NOTICES' TO ERR-PARA", 3)
        g.b("PERFORM 8000-SQL-ERROR", 3)
        g.b("END-EVALUATE", 1)
        g.b("END-PERFORM")
        g.sql(["CLOSE C-NEW-REFERRALS"])

    def notice():
        g.b("MOVE 'LT' TO FRDN-NOTICE-CHANNEL-CD")
        g.b("MOVE WS-DUE-DT TO FRDN-NOTICE-DUE-DT")
        g.b("MOVE 'FRDNOT01' TO FRDN-TEMPLATE-CD")
        g.insert("CLR.T_FRAUD_NOTIFICATION", mark="FR060-INS",
                 omit=("NOTICE_SENT_TS", "DEFERRED_UNTIL_DT", "NOTIFY_MSG_ID"))
        g.sqlcheck("2100-CREATE-NOTICE", on_ok=["ADD 1 TO WS-FRAUD-NOTIFICATION-WRITTEN"])
        g.prep_call("CLRCM020", key="FRDN-CLAIM-ID")
        g.call("CLRCM020")

    g.facts.append(Fact("fr060-key", ("FR060-KEY", "FR060-KEY"), "MOVE 'FRD_NOTICE_BUS_DAYS' TO PARM-PARAM-KEY",
                        "CLRFR060 reads the customer-notice period FRD_NOTICE_BUS_DAYS from CLR.T_PARAM via CLRCM040.",
                        world_ref="TABLE:CLR.T_PARAM#param_rows:FRD_NOTICE_BUS_DAYS"))
    g.facts.append(Fact("fr060-ins", ("FR060-INS", "FR060-INS"), "INSERT INTO CLR.T_FRAUD_NOTIFICATION",
                        "CLRFR060 inserts customer notices into CLR.T_FRAUD_NOTIFICATION.",
                        world_ref="PROGRAM:CLRFR060#writes_tables:CLR.T_FRAUD_NOTIFICATION"))
    return {"drive": None, "handled_tables": {"CLR.T_FRAUD_REFERRAL", "CLR.T_FRAUD_NOTIFICATION"},
            "handled_calls": {"CLRCM040", "CLRCM010", "CLRCM020"},
            "init_steps": [("1300-COMPUTE-DUE-DATE", due_date, None, "CUSTOMER NOTICE DUE DATE")],
            "row_steps": [("2000-SCHEDULE-NOTICES", schedule, None, "SET DUE DATES AND CREATE NOTICES")],
            "extra_paras": [("2100-CREATE-NOTICE", notice, None, "INSERT ONE CUSTOMER NOTICE")]}


def s_param(keys):
    def f(g):
        for _k, tgt in keys:
            if tgt:
                ws(g, f"05  {tgt:<24}PIC S9(11)V99 COMP-3 VALUE ZERO.")
        return {"param_keys": keys}
    return f


def s_rs160(g):
    ws(g, "05  WS-LLNT-GBP              PIC S9(11)V99 COMP-3 VALUE ZERO.")
    return {"param_keys": [("RSV_LLNT_GBP", "WS-LLNT-GBP")], "queue": "CLR.LLN.OUT"}


# ---------------------------------------------------------------------------------------------
# called subprograms: linkage that matches the callers' parameter areas
# ---------------------------------------------------------------------------------------------
SUB_LINK = {
    "CLRCM010": ("LS-DATE-WORK", [("LS-IN-DATE", "X(10)"), ("LS-CALENDAR", "X(2)"), ("LS-BUS-DAYS", "S9(4) COMP"),
                                  ("LS-OUT-DATE", "X(10)")], "CLR-DATE-WORK"),
    "CLRCM020": ("LS-AUDIT-PARMS", [("LS-AUD-TABLE", "X(18)"), ("LS-AUD-KEY", "X(30)"), ("LS-AUD-ACTION", "X(1)"),
                                    ("LS-AUD-USER", "X(8)"), ("LS-AUD-PGM", "X(8)")], None),
    "CLRCM030": ("LS-CCY-PARMS", [("LS-CCY-FROM", "X(3)"), ("LS-CCY-AMOUNT", "S9(11)V99 COMP-3"),
                                  ("LS-CCY-RATE-DT", "X(10)"), ("LS-CCY-GBP-AMOUNT", "S9(11)V99 COMP-3")], None),
    "CLRCM040": ("LS-PARM-REC", [("LS-PARAM-KEY", "X(20)"), ("LS-VALID-FROM", "X(10)"), ("LS-VALID-TO", "X(10)"),
                                 ("LS-PARAM-VALUE", "X(40)"), ("LS-PARAM-DESC", "X(120)"),
                                 ("LS-CHANGE-TICKET", "X(10)"), ("LS-CHANGED-BY", "X(8)")], None),
    "CLRCM050": (None, [], None),
    "CLRCM060": ("LS-CODE-PARMS", [("LS-CODE-TYPE", "X(8)"), ("LS-CODE-VALUE", "X(6)"), ("LS-CODE-DESC", "X(60)")], None),
    "CLRCM070": ("LS-AUTH-PARMS", [("LS-AUTH-USER", "X(8)"), ("LS-AUTH-FUNCTION", "X(8)"), ("LS-AUTH-ALLOWED", "X(1)")], None),
    "CLRCM080": ("LS-NOTE-PARMS", [("LS-NOTE-CLAIM-ID", "X(12)"), ("LS-NOTE-TYPE", "X(2)"), ("LS-NOTE-TEXT", "X(200)")], None),
    "CLRCM090": ("LS-DIARY-PARMS", [("LS-DIA-CLAIM-ID", "X(12)"), ("LS-DIA-TYPE", "X(4)"), ("LS-DIA-DUE-DT", "X(10)"),
                                    ("LS-DIA-OWNER", "X(8)")], None),
    "CLRCM100": ("LS-DOC-PARMS", [("LS-DOC-CLAIM-ID", "X(12)"), ("LS-DOC-OBJECT-ID", "X(36)"), ("LS-DOC-TYPE", "X(4)")], None),
    "CLRCM110": ("LS-MQ-PARMS", [("LS-MQ-FUNCTION", "X(8)"), ("LS-MQ-BUFFER-LEN", "S9(9) COMP"), ("LS-MQ-BUFFER", "X(2000)")], "MQ"),
    "CLRCM120": ("LS-MQ-PARMS", [("LS-MQ-FUNCTION", "X(8)"), ("LS-MQ-BUFFER-LEN", "S9(9) COMP"), ("LS-MQ-BUFFER", "X(2000)")], "MQ"),
    "CLRRS015": ("LS-RSVAUTH-PARMS", [("LS-RA-USER", "X(8)"), ("LS-RA-CURRENCY", "X(3)"), ("LS-RA-AMOUNT", "S9(11)V99 COMP-3"),
                                      ("LS-RA-REQUIRED-LVL", "X(2)"), ("LS-RA-RESULT", "X(1)")], None),
}


def s_sub(g):
    name, fields, special = SUB_LINK[g.pid]
    items = []
    using = []
    if special == "MQ":
        items.append(("a", "01  LS-MQ-AREA                  PIC X(76)."))
        using.append("LS-MQ-AREA")
    if name:
        items.append(("a", f"01  {name}."))
        for fn, pic in fields:
            items.append((0, f"05  {fn:<24}PIC {pic}."))
        using.append(name)
    items.append(("a", "01  LS-ERROR-BLOCK              PIC X(162)."))
    using.append("LS-ERROR-BLOCK")
    link(g, items)
    entry, ret = [], []
    if g.pid == "CLRCM040":
        entry = ["MOVE LS-PARM-REC TO PARMREC1-REC"]
        ret = ["MOVE PARMREC1-REC TO LS-PARM-REC"]
    elif g.pid == "CLRCM010":
        entry = ["MOVE LS-DATE-WORK TO CLR-DATE-WORK"]
        ret = ["MOVE CLR-DATE-WORK TO LS-DATE-WORK"]
    elif special == "MQ":
        entry = ["MOVE LS-MQ-AREA TO CLR-MQ-AREA"]
    elif g.pid == "CLRCM050":
        entry = ["MOVE LS-ERROR-BLOCK TO CLR-ERROR-BLOCK",
                 "DISPLAY 'CLARA ERROR ' ERR-PGM ' ' ERR-PARA ' ' ERR-SQLCODE"]
    out = {"using": using, "entry_lines": entry, "return_lines": ret}
    if g.pid == "CLRCM040":
        def read_param():
            g.c("RETURN THE ROW VALID ON THE CURRENT DATE (VALID_FROM <= TODAY AND")
            g.c("VALID_TO NULL OR >= TODAY). NOT FOUND IS RETURNED AS SQLCODE +100.")
            g.sql(["SELECT PARAM_VALUE, VALID_FROM, VALID_TO, PARAM_DESC,",
                   "       CHANGE_TICKET",
                   "  INTO :PARM-PARAM-VALUE, :PARM-VALID-FROM,",
                   "       :PARM-VALID-TO :WS-IND-1, :PARM-PARAM-DESC,",
                   "       :PARM-CHANGE-TICKET :WS-IND-2",
                   ("  FROM CLR.T_PARAM", ["R:CLR.T_PARAM", "CM040-FROM"]),
                   " WHERE PARAM_KEY = :PARM-PARAM-KEY",
                   "   AND VALID_FROM <= CURRENT DATE",
                   ("   AND (VALID_TO IS NULL OR VALID_TO >= CURRENT DATE)", "CM040-VALID")])
            g.b("MOVE SQLCODE TO ERR-SQLCODE")
            g.b("IF SQLCODE NOT = 0")
            g.b("MOVE SPACES TO PARM-PARAM-VALUE", 1)
            g.b("END-IF")
        g.facts.append(Fact("cm040-valid", ("CM040-FROM", "CM040-VALID"), "AND (VALID_TO IS NULL OR VALID_TO >= CURRENT DATE)",
                            "CLRCM040 (parameter reader) selects the CLR.T_PARAM row valid on the current date "
                            "(VALID_FROM <= CURRENT DATE and VALID_TO null or later).",
                            world_ref="PROGRAM:CLRCM040#description"))
        out.update({"handled_tables": {"CLR.T_PARAM"},
                    "row_steps": [("2000-READ-PARAMETER", read_param, None, "READ ONE PARAMETER")]})
    return out


SPECIAL = {
    "CLRGL090": s_gl090, "CLRFN030": s_fn030, "CLRST040": s_st040, "CLRRC050": s_rc050,
    "CLRRS010": s_rs010, "CLRRS020": s_rs020, "CLRRS110": s_rs110, "CLRRS130": s_rs130,
    "CLRRS150": s_rs150, "CLRRS170": s_rs170, "CLRFR030": s_fr030, "CLRFR040": s_fr040,
    "CLRFR020": s_fr020, "CLRFR060": s_fr060, "CLRRS160": s_rs160,
    "CLRTR020": s_param([("TRI_T3_MIN_GBP", "WS-T3-MIN-GBP")]),
    "CLRTR060": s_param([("TRI_FASTTRACK_CAP", "WS-FASTTRACK-CAP")]),
    "CLRST080": s_param([("TRI_FASTTRACK_CAP", "WS-FASTTRACK-CAP")]),
    "CLRRC020": s_param([("REC_PURSUE_MIN_GBP", "WS-PURSUE-MIN-GBP")]),
    "CLRRS015": s_param([("RSV_LLNT_GBP", "WS-LLNT-GBP")]),
}
for _sub in SUB_LINK:
    if _sub in SPECIAL:
        _f = SPECIAL[_sub]
        SPECIAL[_sub] = (lambda f1: (lambda g: {**s_sub(g), **f1(g)}))(_f)
    else:
        SPECIAL[_sub] = s_sub

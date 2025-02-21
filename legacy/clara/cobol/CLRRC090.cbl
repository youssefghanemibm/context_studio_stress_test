000100* ===============================================================*
000200* PROGRAM    : CLRRC090                                          *
000300* TITLE      : RECOVERY WRITE-OFF (BR-REC-011)                   *
000400* SYSTEM     : CLARA - CLAIMS LEDGER AND RESERVE APPLICATION     *
000500* AREA       : RECOVER                                           *
000600* TYPE       : CICS ONLINE / DB2                                 *
000700* TRANSACTION: RC09                                              *
000800* ---------------------------------------------------------------*
000900* PURPOSE                                                        *
001000*   CICS PSEUDO-CONVERSATIONAL PROGRAM - RECOVERY WRITE-OFF      *
001100*     (BR-REC-011).                                              *
001200*   PSEUDO-CONVERSATIONAL; STATE IS KEPT IN CLRCOMM1.            *
001300*   INVOKED WITH A COMMAREA; RESULTS RETURNED IN                 *
001400*     CA-RETURN-CD/CA-MSG.                                       *
001500* ---------------------------------------------------------------*
001600* DB2 TABLES                                                     *
001700*   CLR.T_SUBROGATION_CASE      READ                             *
001800*   CLR.T_RECOVERY              INSERT                           *
001900* COPYBOOKS  : RCVREC01 SUBCAS01 CLRERR01 CLRCOMM1               *
002000* CALLS      : CLRCM050                                          *
002100* ---------------------------------------------------------------*
002200* MAINTENANCE HISTORY                                            *
002300* DATE       BY       REF        DESCRIPTION                     *
002400* ---------- -------- ---------- ------------------------------- *
002500* 1994-10-03 CLRPROJ             INITIAL VERSION - CLARA GO-LIVE *
002600* 1999-04-12 KBARR01             Y2K REMEDIATION - DATE          *
002700*                                WINDOWING REMOVED               *
002800* 2009-09-17 DO                  DATE ARITHMETIC MOVED TO        *
002900*                                CLRCM010                        *
003000* 2016-01-04 KBARR01             PERFORMANCE: CURSOR WITH HOLD,  *
003100*                                FEWER COMMITS                   *
003200* 2024-06-20 KBARR01             SQL WARNINGS LOGGED, NOT        *
003300*                                TREATED AS ERRORS               *
003400* 2024-07-01 KBARR01             NORDIC CURRENCY CODES VALIDATED *
003500* ===============================================================*
003600 IDENTIFICATION DIVISION.
003700 PROGRAM-ID.    CLRRC090.
003800 AUTHOR.        CLARA PROJECT TEAM.
003900 INSTALLATION.  CORVANE MUTUAL - CLAIMS SYSTEMS.
004000 DATE-WRITTEN.  1994-10-03.
004100 DATE-COMPILED.
004200 ENVIRONMENT DIVISION.
004300 CONFIGURATION SECTION.
004400 SOURCE-COMPUTER.  IBM-Z.
004500 OBJECT-COMPUTER.  IBM-Z.
004600 DATA DIVISION.
004700 WORKING-STORAGE SECTION.
004800*
004900 01  WS-PROGRAM-INFO.
005000     05  WS-PGM-ID               PIC X(8)   VALUE 'CLRRC090'.
005100     05  WS-RUN-DATE             PIC X(10)  VALUE SPACES.
005200     05  WS-RUN-TS               PIC X(26)  VALUE SPACES.
005300     05  WS-USER-ID              PIC X(8)   VALUE SPACES.
005400*
005500 01  WS-SWITCHES.
005600     05  WS-EOF-SW               PIC X      VALUE 'N'.
005700        88  WS-END-OF-DATA                     VALUE 'Y'.
005800     05  WS-ERROR-SW             PIC X      VALUE 'N'.
005900        88  WS-ERROR-FOUND                     VALUE 'Y'.
006000        88  WS-NO-ERROR                        VALUE 'N'.
006100     05  WS-FOUND-SW             PIC X      VALUE 'N'.
006200        88  WS-ROW-FOUND                       VALUE 'Y'.
006300        88  WS-ROW-NOT-FOUND                   VALUE 'N'.
006400*
006500 01  WS-COUNTERS.
006600     05  WS-SUBROGATION-CASE-READPIC S9(9)  COMP-3 VALUE ZERO.
006700     05  WS-RECOVERY-WRITTEN     PIC S9(9)  COMP-3 VALUE ZERO.
006800     05  WS-REJECT-CNT           PIC S9(9)  COMP-3 VALUE ZERO.
006900*
007000 01  WS-SQL-WORK.
007100     05  WS-SQLCODE-DSP          PIC -9(9).
007200     05  WS-ROWS-AFFECTED        PIC S9(9)  COMP VALUE ZERO.
007300     05  WS-IND-1                PIC S9(4)  COMP VALUE ZERO.
007400     05  WS-IND-2                PIC S9(4)  COMP VALUE ZERO.
007500     05  WS-NEW-ID               PIC S9(18) COMP VALUE ZERO.
007600*
007700     EXEC SQL INCLUDE SQLCA END-EXEC.
007800*
007900* CLARA RECORD LAYOUTS
008000 COPY RCVREC01.
008100 COPY SUBCAS01.
008200 COPY CLRERR01.
008300 COPY CLRCOMM1.
008400*
008500 01  WS-AID-VALUES.
008600     05  AID-ENTER               PIC X      VALUE X'7D'.
008700     05  AID-CLEAR               PIC X      VALUE X'6D'.
008800     05  AID-PF3                 PIC X      VALUE X'F3'.
008900     05  AID-PF7                 PIC X      VALUE X'F7'.
009000     05  AID-PF8                 PIC X      VALUE X'F8'.
009100     05  AID-PF12                PIC X      VALUE X'7C'.
009200     05  WS-RESP                 PIC S9(8)  COMP VALUE ZERO.
009300 LINKAGE SECTION.
009400 01  DFHCOMMAREA                 PIC X(105).
009500 PROCEDURE DIVISION.
009600* ---------------------------------------------------------------*
009700* 0000-MAIN                                                      *
009800* PSEUDO-CONVERSATIONAL CONTROL                                  *
009900* ---------------------------------------------------------------*
010000 0000-MAIN.
010100     EXEC CICS ASSIGN USERID(WS-USER-ID) END-EXEC
010200     IF EIBCALEN = ZERO
010300        INITIALIZE CLR-COMMAREA
010400        MOVE 'RC09' TO CA-TRANID
010500        MOVE 12 TO CA-RETURN-CD
010600        MOVE 'NO COMMAREA SUPPLIED' TO CA-MSG
010700        PERFORM 9000-RETURN THRU 9000-RETURN-EXIT
010800     ELSE
010900        MOVE DFHCOMMAREA TO CLR-COMMAREA
011000        PERFORM 2000-PROCESS-INPUT THRU 2000-PROCESS-INPUT-EXIT
011100     END-IF
011200     PERFORM 9000-RETURN THRU 9000-RETURN-EXIT
011300     GOBACK.
011400 0000-MAIN-EXIT.
011500     EXIT.
011600* ---------------------------------------------------------------*
011700* 2000-PROCESS-INPUT                                             *
011800* PROCESS THE REQUEST                                            *
011900* ---------------------------------------------------------------*
012000 2000-PROCESS-INPUT.
012100     PERFORM 2100-EDIT-INPUT THRU 2100-EDIT-INPUT-EXIT
012200     IF WS-NO-ERROR
012300        PERFORM 2200-APPLY THRU 2200-APPLY-EXIT
012400     END-IF
012500     .
012600 2000-PROCESS-INPUT-EXIT.
012700     EXIT.
012800* ---------------------------------------------------------------*
012900* 2100-EDIT-INPUT                                                *
013000* VALIDATE THE REQUEST                                           *
013100* ---------------------------------------------------------------*
013200 2100-EDIT-INPUT.
013300     SET WS-NO-ERROR TO TRUE
013400     IF CA-CLAIM-ID = SPACES OR LOW-VALUES
013500        SET WS-ERROR-FOUND TO TRUE
013600        MOVE 8 TO CA-RETURN-CD
013700        MOVE 'CLAIM ID IS REQUIRED' TO CA-MSG
013800     END-IF
013900     .
014000 2100-EDIT-INPUT-EXIT.
014100     EXIT.
014200* ---------------------------------------------------------------*
014300* 2200-APPLY                                                     *
014400* BUSINESS PROCESSING                                            *
014500* ---------------------------------------------------------------*
014600 2200-APPLY.
014700     PERFORM 2300-READ-SUBR-CASE THRU 2300-READ-SUBR-CASE-EXIT
014800     PERFORM 2500-EDIT-SUBR-CASE THRU 2500-EDIT-SUBR-CASE-EXIT
014900     PERFORM 2510-EDIT-RECOVERY THRU 2510-EDIT-RECOVERY-EXIT
015000     PERFORM 2520-EDIT-SUBR-CASE-2 THRU 2520-EDIT-SUBR-CASE-2-EXIT
015100     PERFORM 2530-EDIT-RECOVERY-2 THRU 2530-EDIT-RECOVERY-2-EXIT
015200     PERFORM 4100-INSERT-RECOVERY THRU 4100-INSERT-RECOVERY-EXIT
015300     IF WS-NO-ERROR
015400        EXEC CICS SYNCPOINT END-EXEC
015500        MOVE ZERO TO CA-RETURN-CD
015600     END-IF
015700     .
015800 2200-APPLY-EXIT.
015900     EXIT.
016000* ---------------------------------------------------------------*
016100* 2300-READ-SUBR-CASE                                            *
016200* READ CLR.T_SUBROGATION_CASE                                    *
016300* ---------------------------------------------------------------*
016400 2300-READ-SUBR-CASE.
016500     SET WS-ROW-FOUND TO TRUE
016600     EXEC SQL
016700         SELECT SUBRO_CASE_ID, CLAIM_ID, TP_INSURER_NAME
016800                , TP_REF, DEMAND_AMT, DEMAND_DT
016900           INTO :SUBC-SUBRO-CASE-ID, :SUBC-CLAIM-ID
017000                , :SUBC-TP-INSURER-NAME, :SUBC-TP-REF
017100                , :SUBC-DEMAND-AMT, :SUBC-DEMAND-DT
017200           FROM CLR.T_SUBROGATION_CASE
017300          WHERE SUBRO_CASE_ID = :SUBC-SUBRO-CASE-ID
017400     END-EXEC
017500     EVALUATE SQLCODE
017600        WHEN 0
017700           ADD 1 TO WS-SUBROGATION-CASE-READ
017800        WHEN +100
017900           SET WS-ROW-NOT-FOUND TO TRUE
018000        WHEN OTHER
018100           MOVE 'READ CLR.T_SUBROGATION_CASE' TO ERR-PARA
018200           PERFORM 8000-SQL-ERROR
018300     END-EVALUATE
018400     .
018500 2300-READ-SUBR-CASE-EXIT.
018600     EXIT.
018700* ---------------------------------------------------------------*
018800* 2500-EDIT-SUBR-CASE                                            *
018900* CHECK MANDATORY FIELDS IN CLR.T_SUBROGATION_CASE               *
019000* ---------------------------------------------------------------*
019100 2500-EDIT-SUBR-CASE.
019200     IF SUBC-SUBRO-CASE-ID = SPACES OR LOW-VALUES
019300        ADD 1 TO WS-REJECT-CNT
019400        MOVE 'SUBRO_CASE_ID MISSING' TO ERR-TEXT
019500     END-IF
019600     IF SUBC-CLAIM-ID = SPACES OR LOW-VALUES
019700        ADD 1 TO WS-REJECT-CNT
019800        MOVE 'CLAIM_ID MISSING' TO ERR-TEXT
019900     END-IF
020000     IF SUBC-TP-INSURER-NAME = SPACES OR LOW-VALUES
020100        ADD 1 TO WS-REJECT-CNT
020200        MOVE 'TP_INSURER_NAME MISSING' TO ERR-TEXT
020300     END-IF
020400     IF SUBC-DEMAND-AMT NOT NUMERIC
020500        MOVE ZERO TO SUBC-DEMAND-AMT
020600        ADD 1 TO WS-REJECT-CNT
020700     END-IF
020800     .
020900 2500-EDIT-SUBR-CASE-EXIT.
021000     EXIT.
021100* ---------------------------------------------------------------*
021200* 2510-EDIT-RECOVERY                                             *
021300* FIELD EDITS FOR CLR.T_RECOVERY                                 *
021400* ---------------------------------------------------------------*
021500 2510-EDIT-RECOVERY.
021600     IF RCVR-CLAIM-ID = SPACES OR LOW-VALUES
021700        ADD 1 TO WS-REJECT-CNT
021800        MOVE 'CLAIM_ID MISSING' TO ERR-TEXT
021900     END-IF
022000     IF RCVR-RCV-TYPE-CD NOT = 'SB' AND RCVR-RCV-TYPE-CD NOT =
022100         'SV' AND RCVR-RCV-TYPE-CD NOT = 'EX'
022200        ADD 1 TO WS-REJECT-CNT
022300        MOVE 'RCV_TYPE_CD INVALID' TO ERR-TEXT
022400     END-IF
022500     IF RCVR-RCV-EXPECTED-AMT NOT NUMERIC
022600        MOVE ZERO TO RCVR-RCV-EXPECTED-AMT
022700        ADD 1 TO WS-REJECT-CNT
022800     END-IF
022900     .
023000 2510-EDIT-RECOVERY-EXIT.
023100     EXIT.
023200* ---------------------------------------------------------------*
023300* 2520-EDIT-SUBR-CASE-2                                          *
023400* VALIDATE CLR.T_SUBROGATION_CASE                                *
023500* ---------------------------------------------------------------*
023600 2520-EDIT-SUBR-CASE-2.
023700     IF SUBC-DEMAND-DT NOT = SPACES AND SUBC-DEMAND-DT(5:1) NOT =
023800         '-'
023900        MOVE 'DEMAND_DT BAD DATE' TO ERR-TEXT
024000        ADD 1 TO WS-REJECT-CNT
024100     END-IF
024200     IF SUBC-LIMITATION-DT NOT = SPACES AND
024300         SUBC-LIMITATION-DT(5:1) NOT = '-'
024400        MOVE 'LIMITATION_DT BAD DATE' TO ERR-TEXT
024500        ADD 1 TO WS-REJECT-CNT
024600     END-IF
024700     IF SUBC-CASE-STATUS NOT = 'LT' AND SUBC-CASE-STATUS NOT =
024800         'ST' AND SUBC-CASE-STATUS NOT = 'WO'
024900        ADD 1 TO WS-REJECT-CNT
025000        MOVE 'CASE_STATUS INVALID' TO ERR-TEXT
025100     END-IF
025200     .
025300 2520-EDIT-SUBR-CASE-2-EXIT.
025400     EXIT.
025500* ---------------------------------------------------------------*
025600* 2530-EDIT-RECOVERY-2                                           *
025700* FIELD EDITS FOR CLR.T_RECOVERY                                 *
025800* ---------------------------------------------------------------*
025900 2530-EDIT-RECOVERY-2.
026000     IF RCVR-RCV-RECEIVED-AMT NOT NUMERIC
026100        MOVE ZERO TO RCVR-RCV-RECEIVED-AMT
026200        ADD 1 TO WS-REJECT-CNT
026300     END-IF
026400     IF RCVR-RCV-STATUS NOT = 'OP' AND RCVR-RCV-STATUS NOT = 'PT'
026500         AND RCVR-RCV-STATUS NOT = 'CL' AND RCVR-RCV-STATUS NOT =
026600         'WO'
026700        ADD 1 TO WS-REJECT-CNT
026800        MOVE 'RCV_STATUS INVALID' TO ERR-TEXT
026900     END-IF
027000     IF RCVR-CURRENCY-CD = SPACES OR LOW-VALUES
027100        ADD 1 TO WS-REJECT-CNT
027200        MOVE 'CURRENCY_CD MISSING' TO ERR-TEXT
027300     END-IF
027400     .
027500 2530-EDIT-RECOVERY-2-EXIT.
027600     EXIT.
027700* ---------------------------------------------------------------*
027800* 4100-INSERT-RECOVERY                                           *
027900* INSERT CLR.T_RECOVERY                                          *
028000* ---------------------------------------------------------------*
028100 4100-INSERT-RECOVERY.
028200     MOVE CA-CLAIM-ID TO RCVR-CLAIM-ID
028300     EXEC SQL
028400         INSERT INTO CLR.T_RECOVERY
028500              ( CLAIM_ID, SUBRO_CASE_ID, RCV_TYPE_CD
028600              , RCV_EXPECTED_AMT, RCV_RECEIVED_AMT
028700              , RCV_WRITE_OFF_AMT, WRITE_OFF_APPROVED_BY
028800              , RCV_STATUS, CURRENCY_CD, LAST_UPD_TS
028900              , LAST_UPD_PGM, LAST_UPD_USER )
029000         VALUES
029100              ( :RCVR-CLAIM-ID, :RCVR-SUBRO-CASE-ID
029200              , :RCVR-RCV-TYPE-CD, :RCVR-RCV-EXPECTED-AMT
029300              , :RCVR-RCV-RECEIVED-AMT, :RCVR-RCV-WRITE-OFF-AMT
029400              , :RCVR-WRITE-OFF-APPROVED-BY, :RCVR-RCV-STATUS
029500              , :RCVR-CURRENCY-CD, CURRENT TIMESTAMP
029600              , :WS-PGM-ID, :WS-USER-ID )
029700     END-EXEC
029800     EVALUATE SQLCODE
029900        WHEN 0
030000           ADD 1 TO WS-RECOVERY-WRITTEN
030100        WHEN +100
030200           SET WS-ROW-NOT-FOUND TO TRUE
030300        WHEN OTHER
030400           MOVE 'INSERT CLR.T_RECOVERY' TO ERR-PARA
030500           PERFORM 8000-SQL-ERROR
030600     END-EVALUATE
030700     .
030800 4100-INSERT-RECOVERY-EXIT.
030900     EXIT.
031000* ---------------------------------------------------------------*
031100* 9000-RETURN                                                    *
031200* RETURN TO CICS                                                 *
031300* ---------------------------------------------------------------*
031400 9000-RETURN.
031500     MOVE CLR-COMMAREA TO DFHCOMMAREA
031600     EXEC CICS RETURN END-EXEC
031700     .
031800 9000-RETURN-EXIT.
031900     EXIT.
032000* ---------------------------------------------------------------*
032100* 8000-SQL-ERROR                                                 *
032200* DB2 ERROR HANDLING                                             *
032300* ---------------------------------------------------------------*
032400 8000-SQL-ERROR.
032500     MOVE SQLCODE TO ERR-SQLCODE WS-SQLCODE-DSP
032600     MOVE WS-PGM-ID TO ERR-PGM
032700     STRING 'SQLCODE ' WS-SQLCODE-DSP DELIMITED BY SIZE INTO
032800         ERR-TEXT
032900     CALL 'CLRCM050' USING CLR-ERROR-BLOCK
033000     EXEC CICS SYNCPOINT ROLLBACK END-EXEC
033100     MOVE 16 TO CA-RETURN-CD
033200     MOVE ERR-TEXT TO CA-MSG
033300     PERFORM 9000-RETURN THRU 9000-RETURN-EXIT
033400     .
033500 8000-SQL-ERROR-EXIT.
033600     EXIT.

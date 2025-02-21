000100* ===============================================================*
000200* PROGRAM    : CLRRP070                                          *
000300* TITLE      : RECOVERY MI                                       *
000400* SYSTEM     : CLARA - CLAIMS LEDGER AND RESERVE APPLICATION     *
000500* AREA       : REPORT                                            *
000600* TYPE       : BATCH / DB2                                       *
000700* JOB / STEP : CLRMRP01 / STEP030                                *
000800* ---------------------------------------------------------------*
000900* PURPOSE                                                        *
001000*   NIGHTLY/PERIODIC BATCH STEP: RECOVERY MI.                    *
001100*   SCHEDULED UNDER JOB CLRMRP01 (STEP030).                      *
001200*   DB2 COMMIT AFTER EVERY 1000 UPDATES.                         *
001300*   CONDITION CODES: 00 NORMAL / 04 WARNING / 16 FAILURE.        *
001400* ---------------------------------------------------------------*
001500* DB2 TABLES                                                     *
001600*   CLR.T_RECOVERY              READ                             *
001700*   CLR.T_REPORT_RUN            INSERT                           *
001800* COPYBOOKS  : RCVREC01 RPTRUN01 CLRERR01                        *
001900* CALLS      : NONE                                              *
002000* FILE       : RPTOUT   OUT CONTROL REPORT                       *
002100* ---------------------------------------------------------------*
002200* MAINTENANCE HISTORY                                            *
002300* DATE       BY       REF        DESCRIPTION                     *
002400* ---------- -------- ---------- ------------------------------- *
002500* 1994-10-03 CLRPROJ             INITIAL VERSION - CLARA GO-LIVE *
002600* 1999-04-14 KBARR01             Y2K REMEDIATION - DATE          *
002700*                                WINDOWING REMOVED               *
002800* 2002-05-29 DO                  SQLCODE HANDLING ROUTED THROUGH *
002900*                                CLRERR01                        *
003000* 2012-12-04 PASHW01             COMMIT FREQUENCY TUNED FOR      *
003100*                                BATCH WINDOW                    *
003200* 2023-10-26 KBARR01             SQL WARNINGS LOGGED, NOT        *
003300*                                TREATED AS ERRORS               *
003400* ===============================================================*
003500 IDENTIFICATION DIVISION.
003600 PROGRAM-ID.    CLRRP070.
003700 AUTHOR.        CLARA PROJECT TEAM.
003800 INSTALLATION.  CORVANE MUTUAL - CLAIMS SYSTEMS.
003900 DATE-WRITTEN.  1994-10-03.
004000 DATE-COMPILED.
004100 ENVIRONMENT DIVISION.
004200 CONFIGURATION SECTION.
004300 SOURCE-COMPUTER.  IBM-Z.
004400 OBJECT-COMPUTER.  IBM-Z.
004500 INPUT-OUTPUT SECTION.
004600 FILE-CONTROL.
004700     SELECT REPORT-FILE ASSIGN TO RPTOUT
004800        ORGANIZATION IS SEQUENTIAL
004900        FILE STATUS IS WS-RPTOUT-STATUS.
005000 DATA DIVISION.
005100 FILE SECTION.
005200 FD  REPORT-FILE
005300        RECORDING MODE IS F
005400        BLOCK CONTAINS 0 RECORDS.
005500 01  REPORT-RECORD               PIC X(133).
005600 WORKING-STORAGE SECTION.
005700*
005800 01  WS-PROGRAM-INFO.
005900     05  WS-PGM-ID               PIC X(8)   VALUE 'CLRRP070'.
006000     05  WS-RUN-DATE             PIC X(10)  VALUE SPACES.
006100     05  WS-RUN-TS               PIC X(26)  VALUE SPACES.
006200     05  WS-USER-ID              PIC X(8)   VALUE SPACES.
006300     05  WS-LAST-RUN-TS          PIC X(26)  VALUE SPACES.
006400     05  WS-RUN-ID               PIC S9(9)  COMP VALUE ZERO.
006500*
006600 01  WS-SWITCHES.
006700     05  WS-EOF-SW               PIC X      VALUE 'N'.
006800        88  WS-END-OF-DATA                     VALUE 'Y'.
006900     05  WS-ERROR-SW             PIC X      VALUE 'N'.
007000        88  WS-ERROR-FOUND                     VALUE 'Y'.
007100        88  WS-NO-ERROR                        VALUE 'N'.
007200     05  WS-FOUND-SW             PIC X      VALUE 'N'.
007300        88  WS-ROW-FOUND                       VALUE 'Y'.
007400        88  WS-ROW-NOT-FOUND                   VALUE 'N'.
007500     05  WS-RPTOUT-STATUS        PIC X(2)   VALUE SPACES.
007600*
007700 01  WS-COUNTERS.
007800     05  WS-RECOVERY-READ        PIC S9(9)  COMP-3 VALUE ZERO.
007900     05  WS-REPORT-RUN-WRITTEN   PIC S9(9)  COMP-3 VALUE ZERO.
008000     05  WS-REJECT-CNT           PIC S9(9)  COMP-3 VALUE ZERO.
008100     05  WS-SINCE-COMMIT         PIC S9(9)  COMP-3 VALUE ZERO.
008200     05  WS-COMMIT-FREQ          PIC S9(9)  COMP-3 VALUE +1000.
008300*
008400 01  WS-SQL-WORK.
008500     05  WS-SQLCODE-DSP          PIC -9(9).
008600     05  WS-ROWS-AFFECTED        PIC S9(9)  COMP VALUE ZERO.
008700     05  WS-IND-1                PIC S9(4)  COMP VALUE ZERO.
008800     05  WS-IND-2                PIC S9(4)  COMP VALUE ZERO.
008900     05  WS-NEW-ID               PIC S9(18) COMP VALUE ZERO.
009000*
009100     EXEC SQL INCLUDE SQLCA END-EXEC.
009200*
009300* CLARA RECORD LAYOUTS
009400 COPY RCVREC01.
009500 COPY RPTRUN01.
009600 COPY CLRERR01.
009700*
009800* DRIVING CURSOR ON CLR.T_RECOVERY
009900     EXEC SQL
010000         DECLARE C-RECOVERY CURSOR WITH HOLD FOR
010100         SELECT RCV_ID, CLAIM_ID, SUBRO_CASE_ID, RCV_TYPE_CD
010200                , RCV_EXPECTED_AMT, RCV_RECEIVED_AMT
010300                , RCV_WRITE_OFF_AMT
010400           FROM CLR.T_RECOVERY
010500          WHERE RCV_STATUS IN ('OP', 'PT')
010600          ORDER BY RCV_ID
010700          FOR FETCH ONLY
010800     END-EXEC.
010900*
011000* CONTROL REPORT LINES
011100 01  WS-RPT-HEAD-1.
011200     05  FILLER                  PIC X(1)   VALUE '1'.
011300     05  FILLER                  PIC X(10)  VALUE 'CLRRP070'.
011400     05  FILLER                  PIC X(40)  VALUE
011500           'RECOVERY MI'.
011600     05  FILLER                  PIC X(10)  VALUE 'RUN DATE: '.
011700     05  RH1-RUN-DATE            PIC X(10).
011800     05  FILLER                  PIC X(62)  VALUE SPACES.
011900 01  WS-RPT-DETAIL.
012000     05  FILLER                  PIC X(1)   VALUE SPACE.
012100     05  RD-LABEL                PIC X(40).
012200     05  RD-VALUE                PIC X(60).
012300     05  FILLER                  PIC X(32)  VALUE SPACES.
012400 01  WS-RPT-TOTAL.
012500     05  FILLER                  PIC X(1)   VALUE SPACE.
012600     05  RT-LABEL                PIC X(40).
012700     05  RT-COUNT                PIC ZZZ,ZZZ,ZZ9.
012800     05  FILLER                  PIC X(81)  VALUE SPACES.
012900 PROCEDURE DIVISION.
013000* ---------------------------------------------------------------*
013100* 0000-MAINLINE                                                  *
013200* MAIN CONTROL                                                   *
013300* ---------------------------------------------------------------*
013400 0000-MAINLINE.
013500     PERFORM 1000-INITIALISE
013600     PERFORM 2000-PROCESS
013700     PERFORM 9000-TERMINATE
013800     GOBACK.
013900* ---------------------------------------------------------------*
014000* 1000-INITIALISE                                                *
014100* START OF RUN                                                   *
014200* ---------------------------------------------------------------*
014300 1000-INITIALISE.
014400     MOVE FUNCTION CURRENT-DATE(1:8) TO WS-RUN-TS
014500     STRING WS-RUN-TS(1:4) '-' WS-RUN-TS(5:2) '-' WS-RUN-TS(7:2)
014600        DELIMITED BY SIZE INTO WS-RUN-DATE
014700     MOVE 'CLRBATCH' TO WS-USER-ID
014800     OPEN OUTPUT REPORT-FILE
014900     IF WS-RPTOUT-STATUS NOT = '00'
015000        DISPLAY 'CLRRP070 OPEN FAILED RPTOUT ' WS-RPTOUT-STATUS
015100        MOVE 16 TO RETURN-CODE
015200        GOBACK
015300     END-IF
015400     MOVE WS-RUN-DATE TO RH1-RUN-DATE
015500     WRITE REPORT-RECORD FROM WS-RPT-HEAD-1
015600     .
015700* ---------------------------------------------------------------*
015800* 2000-PROCESS                                                   *
015900* READ AND PROCESS ALL INPUT                                     *
016000* ---------------------------------------------------------------*
016100 2000-PROCESS.
016200     EXEC SQL
016300         OPEN C-RECOVERY
016400     END-EXEC
016500     EVALUATE SQLCODE
016600        WHEN 0
016700           CONTINUE
016800        WHEN OTHER
016900           MOVE '2000-OPEN-C-RECOVERY' TO ERR-PARA
017000           PERFORM 8000-SQL-ERROR
017100     END-EVALUATE
017200     PERFORM 2100-FETCH-NEXT
017300     PERFORM UNTIL WS-END-OF-DATA
017400        PERFORM 2200-PROCESS-ROW
017500        PERFORM 2100-FETCH-NEXT
017600     END-PERFORM
017700     EXEC SQL
017800         CLOSE C-RECOVERY
017900     END-EXEC
018000     .
018100* ---------------------------------------------------------------*
018200* 2100-FETCH-NEXT                                                *
018300* FETCH THE NEXT DRIVING ROW                                     *
018400* ---------------------------------------------------------------*
018500 2100-FETCH-NEXT.
018600     EXEC SQL
018700         FETCH C-RECOVERY
018800          INTO :RCVR-RCV-ID, :RCVR-CLAIM-ID
018900               , :RCVR-SUBRO-CASE-ID, :RCVR-RCV-TYPE-CD
019000               , :RCVR-RCV-EXPECTED-AMT
019100               , :RCVR-RCV-RECEIVED-AMT
019200               , :RCVR-RCV-WRITE-OFF-AMT
019300     END-EXEC
019400     EVALUATE SQLCODE
019500        WHEN 0
019600           ADD 1 TO WS-RECOVERY-READ
019700        WHEN +100
019800           SET WS-END-OF-DATA TO TRUE
019900        WHEN OTHER
020000           MOVE '2100-FETCH-NEXT' TO ERR-PARA
020100           PERFORM 8000-SQL-ERROR
020200     END-EVALUATE
020300     .
020400* ---------------------------------------------------------------*
020500* 2200-PROCESS-ROW                                               *
020600* PER-RECORD PROCESSING                                          *
020700* ---------------------------------------------------------------*
020800 2200-PROCESS-ROW.
020900     SET WS-NO-ERROR TO TRUE
021000     PERFORM 2500-EDIT-RECOVERY
021100     PERFORM 2510-EDIT-REPORT-RUN
021200     PERFORM 2520-EDIT-RECOVERY-2
021300     PERFORM 2530-EDIT-REPORT-RUN-2
021400     PERFORM 4100-INSERT-REPORT-RUN
021500     PERFORM 6000-COMMIT-CHECK
021600     .
021700* ---------------------------------------------------------------*
021800* 2500-EDIT-RECOVERY                                             *
021900* CHECK MANDATORY FIELDS IN CLR.T_RECOVERY                       *
022000* ---------------------------------------------------------------*
022100 2500-EDIT-RECOVERY.
022200     IF RCVR-CLAIM-ID = SPACES OR LOW-VALUES
022300        ADD 1 TO WS-REJECT-CNT
022400        MOVE 'CLAIM_ID MISSING' TO ERR-TEXT
022500     END-IF
022600     IF RCVR-RCV-TYPE-CD NOT = 'SB' AND RCVR-RCV-TYPE-CD NOT =
022700         'SV' AND RCVR-RCV-TYPE-CD NOT = 'EX'
022800        ADD 1 TO WS-REJECT-CNT
022900        MOVE 'RCV_TYPE_CD INVALID' TO ERR-TEXT
023000     END-IF
023100     IF RCVR-RCV-EXPECTED-AMT NOT NUMERIC
023200        MOVE ZERO TO RCVR-RCV-EXPECTED-AMT
023300        ADD 1 TO WS-REJECT-CNT
023400     END-IF
023500     .
023600* ---------------------------------------------------------------*
023700* 2510-EDIT-REPORT-RUN                                           *
023800* CHECK MANDATORY FIELDS IN CLR.T_REPORT_RUN                     *
023900* ---------------------------------------------------------------*
024000 2510-EDIT-REPORT-RUN.
024100     IF RPTR-RUN-ID NOT NUMERIC
024200        MOVE ZERO TO RPTR-RUN-ID
024300        ADD 1 TO WS-REJECT-CNT
024400     END-IF
024500     IF RPTR-REPORT-CD = SPACES OR LOW-VALUES
024600        ADD 1 TO WS-REJECT-CNT
024700        MOVE 'REPORT_CD MISSING' TO ERR-TEXT
024800     END-IF
024900     .
025000* ---------------------------------------------------------------*
025100* 2520-EDIT-RECOVERY-2                                           *
025200* FIELD EDITS FOR CLR.T_RECOVERY                                 *
025300* ---------------------------------------------------------------*
025400 2520-EDIT-RECOVERY-2.
025500     IF RCVR-RCV-RECEIVED-AMT NOT NUMERIC
025600        MOVE ZERO TO RCVR-RCV-RECEIVED-AMT
025700        ADD 1 TO WS-REJECT-CNT
025800     END-IF
025900     IF RCVR-RCV-STATUS NOT = 'OP' AND RCVR-RCV-STATUS NOT = 'PT'
026000         AND RCVR-RCV-STATUS NOT = 'CL' AND RCVR-RCV-STATUS NOT =
026100         'WO'
026200        ADD 1 TO WS-REJECT-CNT
026300        MOVE 'RCV_STATUS INVALID' TO ERR-TEXT
026400     END-IF
026500     IF RCVR-CURRENCY-CD = SPACES OR LOW-VALUES
026600        ADD 1 TO WS-REJECT-CNT
026700        MOVE 'CURRENCY_CD MISSING' TO ERR-TEXT
026800     END-IF
026900     .
027000* ---------------------------------------------------------------*
027100* 2530-EDIT-REPORT-RUN-2                                         *
027200* FIELD EDITS FOR CLR.T_REPORT_RUN                               *
027300* ---------------------------------------------------------------*
027400 2530-EDIT-REPORT-RUN-2.
027500     IF RPTR-ROW-COUNT NOT NUMERIC
027600        MOVE ZERO TO RPTR-ROW-COUNT
027700        ADD 1 TO WS-REJECT-CNT
027800     END-IF
027900     IF RPTR-RUN-STATUS = SPACES OR LOW-VALUES
028000        ADD 1 TO WS-REJECT-CNT
028100        MOVE 'RUN_STATUS MISSING' TO ERR-TEXT
028200     END-IF
028300     .
028400* ---------------------------------------------------------------*
028500* 4100-INSERT-REPORT-RUN                                         *
028600* INSERT CLR.T_REPORT_RUN                                        *
028700* ---------------------------------------------------------------*
028800 4100-INSERT-REPORT-RUN.
028900     EXEC SQL
029000         INSERT INTO CLR.T_REPORT_RUN
029100              ( RUN_ID, REPORT_CD, RUN_TS, ROW_COUNT
029200              , RUN_STATUS, LAST_UPD_TS, LAST_UPD_PGM
029300              , LAST_UPD_USER )
029400         VALUES
029500              ( :RPTR-RUN-ID, :RPTR-REPORT-CD
029600              , CURRENT TIMESTAMP, :RPTR-ROW-COUNT
029700              , :RPTR-RUN-STATUS, CURRENT TIMESTAMP, :WS-PGM-ID
029800              , :WS-USER-ID )
029900     END-EXEC
030000     EVALUATE SQLCODE
030100        WHEN 0
030200           ADD 1 TO WS-REPORT-RUN-WRITTEN
030300        WHEN +100
030400           SET WS-ROW-NOT-FOUND TO TRUE
030500        WHEN OTHER
030600           MOVE 'INSERT CLR.T_REPORT_RUN' TO ERR-PARA
030700           PERFORM 8000-SQL-ERROR
030800     END-EVALUATE
030900     .
031000* ---------------------------------------------------------------*
031100* 6000-COMMIT-CHECK                                              *
031200* PERIODIC COMMIT                                                *
031300* ---------------------------------------------------------------*
031400 6000-COMMIT-CHECK.
031500     ADD 1 TO WS-SINCE-COMMIT
031600     IF WS-SINCE-COMMIT >= WS-COMMIT-FREQ
031700        EXEC SQL
031800            COMMIT
031900        END-EXEC
032000        MOVE ZERO TO WS-SINCE-COMMIT
032100     END-IF
032200     .
032300* ---------------------------------------------------------------*
032400* 9000-TERMINATE                                                 *
032500* TERMINATION AND TOTALS                                         *
032600* ---------------------------------------------------------------*
032700 9000-TERMINATE.
032800     PERFORM 7010-LIST-RECOVERY
032900     PERFORM 7030-LIST-REPORT-RUN
033000     EXEC SQL
033100         COMMIT
033200     END-EXEC
033300     MOVE 'CLR.T_RECOVERY ROWS READ' TO RT-LABEL
033400     MOVE WS-RECOVERY-READ TO RT-COUNT
033500     WRITE REPORT-RECORD FROM WS-RPT-TOTAL
033600     MOVE 'CLR.T_REPORT_RUN ROWS WRITTEN' TO RT-LABEL
033700     MOVE WS-REPORT-RUN-WRITTEN TO RT-COUNT
033800     WRITE REPORT-RECORD FROM WS-RPT-TOTAL
033900     CLOSE REPORT-FILE
034000     IF WS-REJECT-CNT > ZERO
034100        MOVE 4 TO RETURN-CODE
034200     END-IF
034300     .
034400* ---------------------------------------------------------------*
034500* 7010-LIST-RECOVERY                                             *
034600* LIST CLR.T_RECOVERY FIELDS ON THE REPORT                       *
034700* ---------------------------------------------------------------*
034800 7010-LIST-RECOVERY.
034900     MOVE 'LAST CLR.T_RECOVERY ROW' TO RD-LABEL
035000     MOVE SPACES TO RD-VALUE
035100     WRITE REPORT-RECORD FROM WS-RPT-DETAIL
035200     MOVE '  CLAIM_ID' TO RD-LABEL
035300     MOVE RCVR-CLAIM-ID TO RD-VALUE
035400     WRITE REPORT-RECORD FROM WS-RPT-DETAIL
035500     MOVE '  SUBRO_CASE_ID' TO RD-LABEL
035600     MOVE RCVR-SUBRO-CASE-ID TO RD-VALUE
035700     WRITE REPORT-RECORD FROM WS-RPT-DETAIL
035800     MOVE '  RCV_TYPE_CD' TO RD-LABEL
035900     MOVE RCVR-RCV-TYPE-CD TO RD-VALUE
036000     WRITE REPORT-RECORD FROM WS-RPT-DETAIL
036100     .
036200* ---------------------------------------------------------------*
036300* 7030-LIST-REPORT-RUN                                           *
036400* LIST CLR.T_REPORT_RUN FIELDS ON THE REPORT                     *
036500* ---------------------------------------------------------------*
036600 7030-LIST-REPORT-RUN.
036700     MOVE 'LAST CLR.T_REPORT_RUN ROW' TO RD-LABEL
036800     MOVE SPACES TO RD-VALUE
036900     WRITE REPORT-RECORD FROM WS-RPT-DETAIL
037000     MOVE '  REPORT_CD' TO RD-LABEL
037100     MOVE RPTR-REPORT-CD TO RD-VALUE
037200     WRITE REPORT-RECORD FROM WS-RPT-DETAIL
037300     MOVE '  RUN_TS' TO RD-LABEL
037400     MOVE RPTR-RUN-TS TO RD-VALUE
037500     WRITE REPORT-RECORD FROM WS-RPT-DETAIL
037600     MOVE '  RUN_STATUS' TO RD-LABEL
037700     MOVE RPTR-RUN-STATUS TO RD-VALUE
037800     WRITE REPORT-RECORD FROM WS-RPT-DETAIL
037900     .
038000* ---------------------------------------------------------------*
038100* 8000-SQL-ERROR                                                 *
038200* DB2 ERROR HANDLING                                             *
038300* ---------------------------------------------------------------*
038400 8000-SQL-ERROR.
038500     MOVE SQLCODE TO ERR-SQLCODE WS-SQLCODE-DSP
038600     MOVE WS-PGM-ID TO ERR-PGM
038700     STRING 'SQLCODE ' WS-SQLCODE-DSP DELIMITED BY SIZE INTO
038800         ERR-TEXT
038900     DISPLAY WS-PGM-ID ' ' ERR-PARA ' ' ERR-TEXT
039000     EXEC SQL
039100         ROLLBACK
039200     END-EXEC
039300     MOVE 16 TO RETURN-CODE
039400     CLOSE REPORT-FILE
039500     GOBACK.

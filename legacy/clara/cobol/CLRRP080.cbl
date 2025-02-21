000100* ===============================================================*
000200* PROGRAM    : CLRRP080                                          *
000300* TITLE      : AD-HOC REPORT DRIVER                              *
000400* SYSTEM     : CLARA - CLAIMS LEDGER AND RESERVE APPLICATION     *
000500* AREA       : REPORT                                            *
000600* TYPE       : BATCH / DB2                                       *
000700* JOB / STEP : CLRMRP01 / STEP040                                *
000800* ---------------------------------------------------------------*
000900* PURPOSE                                                        *
001000*   BATCH DB2 PROGRAM - AD-HOC REPORT DRIVER.                    *
001100*   RUNS AS STEP040 OF JOB CLRMRP01.                             *
001200*   COMMIT INTERVAL: 500 ROWS.                                   *
001300*   RETURN CODES: 0 OK, 4 WARNINGS, 16 SEVERE (SEE SYSOUT).      *
001400* ---------------------------------------------------------------*
001500* DB2 TABLES                                                     *
001600*   CLR.T_CLAIM                 READ                             *
001700*   CLR.T_NISA_RETURN           READ                             *
001800*   CLR.T_REPORT_RUN            INSERT                           *
001900* COPYBOOKS  : CLRCLM01 NISARET1 RPTRUN01 CLRERR01               *
002000* CALLS      : CLRCM020                                          *
002100* FILE       : RPTOUT   OUT CONTROL REPORT                       *
002200* ---------------------------------------------------------------*
002300* MAINTENANCE HISTORY                                            *
002400* DATE       BY       REF        DESCRIPTION                     *
002500* ---------- -------- ---------- ------------------------------- *
002600* 1994-10-03 CLRPROJ             INITIAL VERSION - CLARA GO-LIVE *
002700* 1999-05-14 KBARR01             Y2K REMEDIATION - DATE          *
002800*                                WINDOWING REMOVED               *
002900* 2006-04-26 KBARR01             RECOMPILED - COBOL FOR Z/OS     *
003000*                                UPGRADE                         *
003100* 2022-07-23 DO                  REPORT HEADINGS REALIGNED       *
003200* ===============================================================*
003300 IDENTIFICATION DIVISION.
003400 PROGRAM-ID.    CLRRP080.
003500 AUTHOR.        CLARA PROJECT TEAM.
003600 INSTALLATION.  CORVANE MUTUAL - CLAIMS SYSTEMS.
003700 DATE-WRITTEN.  1994-10-03.
003800 DATE-COMPILED.
003900 ENVIRONMENT DIVISION.
004000 CONFIGURATION SECTION.
004100 SOURCE-COMPUTER.  IBM-Z.
004200 OBJECT-COMPUTER.  IBM-Z.
004300 INPUT-OUTPUT SECTION.
004400 FILE-CONTROL.
004500     SELECT REPORT-FILE ASSIGN TO RPTOUT
004600         ORGANIZATION IS SEQUENTIAL
004700         FILE STATUS IS WS-RPTOUT-STATUS.
004800 DATA DIVISION.
004900 FILE SECTION.
005000 FD  REPORT-FILE
005100         RECORDING MODE IS F
005200         BLOCK CONTAINS 0 RECORDS.
005300 01  REPORT-RECORD               PIC X(133).
005400 WORKING-STORAGE SECTION.
005500*
005600 01  WS-PROGRAM-INFO.
005700     05  WS-PGM-ID               PIC X(8)   VALUE 'CLRRP080'.
005800     05  WS-RUN-DATE             PIC X(10)  VALUE SPACES.
005900     05  WS-RUN-TS               PIC X(26)  VALUE SPACES.
006000     05  WS-USER-ID              PIC X(8)   VALUE SPACES.
006100     05  WS-LAST-RUN-TS          PIC X(26)  VALUE SPACES.
006200     05  WS-RUN-ID               PIC S9(9)  COMP VALUE ZERO.
006300*
006400 01  WS-SWITCHES.
006500     05  WS-EOF-SW               PIC X      VALUE 'N'.
006600         88  WS-END-OF-DATA                     VALUE 'Y'.
006700     05  WS-ERROR-SW             PIC X      VALUE 'N'.
006800         88  WS-ERROR-FOUND                     VALUE 'Y'.
006900         88  WS-NO-ERROR                        VALUE 'N'.
007000     05  WS-FOUND-SW             PIC X      VALUE 'N'.
007100         88  WS-ROW-FOUND                       VALUE 'Y'.
007200         88  WS-ROW-NOT-FOUND                   VALUE 'N'.
007300     05  WS-RPTOUT-STATUS        PIC X(2)   VALUE SPACES.
007400*
007500 01  WS-COUNTERS.
007600     05  WS-CLAIM-READ           PIC S9(9)  COMP-3 VALUE ZERO.
007700     05  WS-NISA-RETURN-READ     PIC S9(9)  COMP-3 VALUE ZERO.
007800     05  WS-REPORT-RUN-WRITTEN   PIC S9(9)  COMP-3 VALUE ZERO.
007900     05  WS-REJECT-CNT           PIC S9(9)  COMP-3 VALUE ZERO.
008000     05  WS-SINCE-COMMIT         PIC S9(9)  COMP-3 VALUE ZERO.
008100     05  WS-COMMIT-FREQ          PIC S9(9)  COMP-3 VALUE +500.
008200*
008300 01  WS-SQL-WORK.
008400     05  WS-SQLCODE-DSP          PIC -9(9).
008500     05  WS-ROWS-AFFECTED        PIC S9(9)  COMP VALUE ZERO.
008600     05  WS-IND-1                PIC S9(4)  COMP VALUE ZERO.
008700     05  WS-IND-2                PIC S9(4)  COMP VALUE ZERO.
008800     05  WS-NEW-ID               PIC S9(18) COMP VALUE ZERO.
008900*
009000     EXEC SQL INCLUDE SQLCA END-EXEC.
009100*
009200* COPYBOOKS (HOST STRUCTURES AND WORK AREAS)
009300 COPY CLRCLM01.
009400 COPY NISARET1.
009500 COPY RPTRUN01.
009600 COPY CLRERR01.
009700*
009800* CALL INTERFACES
009900 01  WS-AUDIT-PARMS.
010000     05  WS-AUD-TABLE            PIC X(18).
010100     05  WS-AUD-KEY              PIC X(30).
010200     05  WS-AUD-ACTION           PIC X(1).
010300     05  WS-AUD-USER             PIC X(8).
010400     05  WS-AUD-PGM              PIC X(8).
010500*
010600* DRIVING CURSOR ON CLR.T_CLAIM
010700     EXEC SQL
010800         DECLARE C-CLAIM CURSOR WITH HOLD FOR
010900         SELECT CLAIM_ID, POLICY_NO, PRODUCT_CD, PERIL_CD
011000                , LOSS_DT, NOTIFIED_TS
011100           FROM CLR.T_CLAIM
011200          WHERE CLAIM_STATUS IN ('OP', 'RO', 'RC')
011300          ORDER BY CLAIM_ID
011400          FOR FETCH ONLY
011500     END-EXEC.
011600*
011700* CONTROL REPORT LINES
011800 01  WS-RPT-HEAD-1.
011900     05  FILLER                  PIC X(1)   VALUE '1'.
012000     05  FILLER                  PIC X(10)  VALUE 'CLRRP080'.
012100     05  FILLER                  PIC X(40)  VALUE
012200             'AD-HOC REPORT DRIVER'.
012300     05  FILLER                  PIC X(10)  VALUE 'RUN DATE: '.
012400     05  RH1-RUN-DATE            PIC X(10).
012500     05  FILLER                  PIC X(62)  VALUE SPACES.
012600 01  WS-RPT-DETAIL.
012700     05  FILLER                  PIC X(1)   VALUE SPACE.
012800     05  RD-LABEL                PIC X(40).
012900     05  RD-VALUE                PIC X(60).
013000     05  FILLER                  PIC X(32)  VALUE SPACES.
013100 01  WS-RPT-TOTAL.
013200     05  FILLER                  PIC X(1)   VALUE SPACE.
013300     05  RT-LABEL                PIC X(40).
013400     05  RT-COUNT                PIC ZZZ,ZZZ,ZZ9.
013500     05  FILLER                  PIC X(81)  VALUE SPACES.
013600 PROCEDURE DIVISION.
013700* ---------------------------------------------------------------*
013800* 0000-MAINLINE                                                  *
013900* MAIN CONTROL                                                   *
014000* ---------------------------------------------------------------*
014100 0000-MAINLINE.
014200     PERFORM 1000-INITIALISE THRU 1000-INITIALISE-EXIT
014300     PERFORM 2000-PROCESS THRU 2000-PROCESS-EXIT
014400     PERFORM 9000-TERMINATE THRU 9000-TERMINATE-EXIT
014500     GOBACK.
014600 0000-MAINLINE-EXIT.
014700     EXIT.
014800* ---------------------------------------------------------------*
014900* 1000-INITIALISE                                                *
015000* START OF RUN                                                   *
015100* ---------------------------------------------------------------*
015200 1000-INITIALISE.
015300     MOVE FUNCTION CURRENT-DATE(1:8) TO WS-RUN-TS
015400     STRING WS-RUN-TS(1:4) '-' WS-RUN-TS(5:2) '-' WS-RUN-TS(7:2)
015500         DELIMITED BY SIZE INTO WS-RUN-DATE
015600     MOVE 'CLRBATCH' TO WS-USER-ID
015700     OPEN OUTPUT REPORT-FILE
015800     IF WS-RPTOUT-STATUS NOT = '00'
015900         DISPLAY 'CLRRP080 OPEN FAILED RPTOUT ' WS-RPTOUT-STATUS
016000         MOVE 16 TO RETURN-CODE
016100         GOBACK
016200     END-IF
016300     MOVE WS-RUN-DATE TO RH1-RUN-DATE
016400     WRITE REPORT-RECORD FROM WS-RPT-HEAD-1
016500     .
016600 1000-INITIALISE-EXIT.
016700     EXIT.
016800* ---------------------------------------------------------------*
016900* 2000-PROCESS                                                   *
017000* READ AND PROCESS ALL INPUT                                     *
017100* ---------------------------------------------------------------*
017200 2000-PROCESS.
017300     EXEC SQL
017400         OPEN C-CLAIM
017500     END-EXEC
017600     EVALUATE SQLCODE
017700         WHEN 0
017800             CONTINUE
017900         WHEN OTHER
018000             MOVE '2000-OPEN-C-CLAIM' TO ERR-PARA
018100             PERFORM 8000-SQL-ERROR
018200     END-EVALUATE
018300     PERFORM 2100-FETCH-NEXT THRU 2100-FETCH-NEXT-EXIT
018400     PERFORM 2200-PROCESS-ROW THRU 2200-PROCESS-ROW-EXIT
018500         UNTIL WS-END-OF-DATA
018600     EXEC SQL
018700         CLOSE C-CLAIM
018800     END-EXEC
018900     .
019000 2000-PROCESS-EXIT.
019100     EXIT.
019200* ---------------------------------------------------------------*
019300* 2100-FETCH-NEXT                                                *
019400* FETCH THE NEXT DRIVING ROW                                     *
019500* ---------------------------------------------------------------*
019600 2100-FETCH-NEXT.
019700     EXEC SQL
019800         FETCH C-CLAIM
019900          INTO :CLM-CLAIM-ID, :CLM-POLICY-NO, :CLM-PRODUCT-CD
020000               , :CLM-PERIL-CD, :CLM-LOSS-DT
020100               , :CLM-NOTIFIED-TS
020200     END-EXEC
020300     EVALUATE SQLCODE
020400         WHEN 0
020500             ADD 1 TO WS-CLAIM-READ
020600         WHEN +100
020700             SET WS-END-OF-DATA TO TRUE
020800         WHEN OTHER
020900             MOVE '2100-FETCH-NEXT' TO ERR-PARA
021000             PERFORM 8000-SQL-ERROR
021100     END-EVALUATE
021200     .
021300 2100-FETCH-NEXT-EXIT.
021400     EXIT.
021500* ---------------------------------------------------------------*
021600* 2200-PROCESS-ROW                                               *
021700* ONE UNIT OF WORK                                               *
021800* ---------------------------------------------------------------*
021900 2200-PROCESS-ROW.
022000     IF WS-END-OF-DATA
022100         GO TO 2200-PROCESS-ROW-EXIT
022200     END-IF
022300     SET WS-NO-ERROR TO TRUE
022400     PERFORM 2300-READ-NISA-RETURN THRU 2300-READ-NISA-RETURN-EXIT
022500     PERFORM 4100-INSERT-REPORT-RUN THRU
022600         4100-INSERT-REPORT-RUN-EXIT
022700     PERFORM 4900-WRITE-AUDIT THRU 4900-WRITE-AUDIT-EXIT
022800     PERFORM 6000-COMMIT-CHECK THRU 6000-COMMIT-CHECK-EXIT
022900     .
023000 2200-PROCESS-ROW-EXIT.
023100     EXIT.
023200* ---------------------------------------------------------------*
023300* 2300-READ-NISA-RETURN                                          *
023400* LOOK UP CLR.T_NISA_RETURN                                      *
023500* ---------------------------------------------------------------*
023600 2300-READ-NISA-RETURN.
023700     SET WS-ROW-FOUND TO TRUE
023800     EXEC SQL
023900         SELECT RETURN_CD, PERIOD_CD, CELL_REF, CELL_VALUE
024000                , SUBMITTED_DT
024100           INTO :NISA-RETURN-CD, :NISA-PERIOD-CD
024200                , :NISA-CELL-REF, :NISA-CELL-VALUE
024300                , :NISA-SUBMITTED-DT
024400           FROM CLR.T_NISA_RETURN
024500          WHERE RETURN_CD = :NISA-RETURN-CD
024600            AND PERIOD_CD = :NISA-PERIOD-CD
024700     END-EXEC
024800     EVALUATE SQLCODE
024900         WHEN 0
025000             ADD 1 TO WS-NISA-RETURN-READ
025100         WHEN +100
025200             SET WS-ROW-NOT-FOUND TO TRUE
025300         WHEN OTHER
025400             MOVE 'READ CLR.T_NISA_RETURN' TO ERR-PARA
025500             PERFORM 8000-SQL-ERROR
025600     END-EVALUATE
025700     .
025800 2300-READ-NISA-RETURN-EXIT.
025900     EXIT.
026000* ---------------------------------------------------------------*
026100* 4100-INSERT-REPORT-RUN                                         *
026200* INSERT CLR.T_REPORT_RUN                                        *
026300* ---------------------------------------------------------------*
026400 4100-INSERT-REPORT-RUN.
026500     EXEC SQL
026600         INSERT INTO CLR.T_REPORT_RUN
026700              ( RUN_ID, REPORT_CD, RUN_TS, ROW_COUNT
026800              , RUN_STATUS, LAST_UPD_TS, LAST_UPD_PGM
026900              , LAST_UPD_USER )
027000         VALUES
027100              ( :RPTR-RUN-ID, :RPTR-REPORT-CD
027200              , CURRENT TIMESTAMP, :RPTR-ROW-COUNT
027300              , :RPTR-RUN-STATUS, CURRENT TIMESTAMP, :WS-PGM-ID
027400              , :WS-USER-ID )
027500     END-EXEC
027600     EVALUATE SQLCODE
027700         WHEN 0
027800             ADD 1 TO WS-REPORT-RUN-WRITTEN
027900         WHEN +100
028000             SET WS-ROW-NOT-FOUND TO TRUE
028100         WHEN OTHER
028200             MOVE 'INSERT CLR.T_REPORT_RUN' TO ERR-PARA
028300             PERFORM 8000-SQL-ERROR
028400     END-EVALUATE
028500     .
028600 4100-INSERT-REPORT-RUN-EXIT.
028700     EXIT.
028800* ---------------------------------------------------------------*
028900* 4900-WRITE-AUDIT                                               *
029000* AUDIT TRAIL VIA CLRCM020                                       *
029100* ---------------------------------------------------------------*
029200 4900-WRITE-AUDIT.
029300     MOVE 'CLR.T_REPORT_RUN' TO WS-AUD-TABLE
029400     MOVE CLM-CLAIM-ID TO WS-AUD-KEY
029500     MOVE 'I' TO WS-AUD-ACTION
029600     MOVE WS-USER-ID TO WS-AUD-USER
029700     MOVE WS-PGM-ID TO WS-AUD-PGM
029800     CALL 'CLRCM020' USING WS-AUDIT-PARMS
029900                      CLR-ERROR-BLOCK
030000     IF ERR-SQLCODE NOT = ZERO
030100         ADD 1 TO WS-REJECT-CNT
030200     END-IF
030300     .
030400 4900-WRITE-AUDIT-EXIT.
030500     EXIT.
030600* ---------------------------------------------------------------*
030700* 6000-COMMIT-CHECK                                              *
030800* PERIODIC COMMIT                                                *
030900* ---------------------------------------------------------------*
031000 6000-COMMIT-CHECK.
031100     ADD 1 TO WS-SINCE-COMMIT
031200     IF WS-SINCE-COMMIT >= WS-COMMIT-FREQ
031300         EXEC SQL
031400             COMMIT
031500         END-EXEC
031600         MOVE ZERO TO WS-SINCE-COMMIT
031700     END-IF
031800     .
031900 6000-COMMIT-CHECK-EXIT.
032000     EXIT.
032100* ---------------------------------------------------------------*
032200* 9000-TERMINATE                                                 *
032300* TERMINATION AND TOTALS                                         *
032400* ---------------------------------------------------------------*
032500 9000-TERMINATE.
032600     EXEC SQL
032700         COMMIT
032800     END-EXEC
032900     MOVE 'CLR.T_CLAIM ROWS READ' TO RT-LABEL
033000     MOVE WS-CLAIM-READ TO RT-COUNT
033100     WRITE REPORT-RECORD FROM WS-RPT-TOTAL
033200     MOVE 'CLR.T_NISA_RETURN ROWS READ' TO RT-LABEL
033300     MOVE WS-NISA-RETURN-READ TO RT-COUNT
033400     WRITE REPORT-RECORD FROM WS-RPT-TOTAL
033500     MOVE 'CLR.T_REPORT_RUN ROWS WRITTEN' TO RT-LABEL
033600     MOVE WS-REPORT-RUN-WRITTEN TO RT-COUNT
033700     WRITE REPORT-RECORD FROM WS-RPT-TOTAL
033800     CLOSE REPORT-FILE
033900     IF WS-REJECT-CNT > ZERO
034000         MOVE 4 TO RETURN-CODE
034100     END-IF
034200     .
034300 9000-TERMINATE-EXIT.
034400     EXIT.
034500* ---------------------------------------------------------------*
034600* 8000-SQL-ERROR                                                 *
034700* DB2 ERROR HANDLING                                             *
034800* ---------------------------------------------------------------*
034900 8000-SQL-ERROR.
035000     MOVE SQLCODE TO ERR-SQLCODE WS-SQLCODE-DSP
035100     MOVE WS-PGM-ID TO ERR-PGM
035200     STRING 'SQLCODE ' WS-SQLCODE-DSP DELIMITED BY SIZE INTO
035300         ERR-TEXT
035400     DISPLAY WS-PGM-ID ' ' ERR-PARA ' ' ERR-TEXT
035500     EXEC SQL
035600         ROLLBACK
035700     END-EXEC
035800     MOVE 16 TO RETURN-CODE
035900     CLOSE REPORT-FILE
036000     GOBACK.
036100 8000-SQL-ERROR-EXIT.
036200     EXIT.

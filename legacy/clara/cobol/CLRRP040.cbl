000100* ===============================================================*
000200* PROGRAM    : CLRRP040                                          *
000300* TITLE      : NISA-CT1 CLAIMS TIMELINESS EXTRACT (CLX-IF-032)   *
000400* SYSTEM     : CLARA - CLAIMS LEDGER AND RESERVE APPLICATION     *
000500* AREA       : REPORT                                            *
000600* TYPE       : BATCH / DB2                                       *
000700* JOB / STEP : CLRQRP01 / STEP020                                *
000800* ---------------------------------------------------------------*
000900* PURPOSE                                                        *
001000*   BATCH DB2 PROGRAM - NISA-CT1 CLAIMS TIMELINESS EXTRACT       *
001100*     (CLX-IF-032).                                              *
001200*   EXECUTED BY JOB CLRQRP01, STEP020.                           *
001300*   COMMITS EVERY 500 UNITS OF WORK.                             *
001400*   RC 0 = NORMAL, RC 4 = REJECTS REPORTED, RC 16 = ABORTED.     *
001500* ---------------------------------------------------------------*
001600* DB2 TABLES                                                     *
001700*   CLR.T_CLAIM                 READ                             *
001800*   CLR.T_REPORT_RUN            READ                             *
001900*   CLR.T_NISA_RETURN           INSERT                           *
002000* COPYBOOKS  : CLRCLM01 NISARET1 RPTRUN01 CLRERR01 CLRDATE1      *
002100* CALLS      : CLRCM020 CLRCM010                                 *
002200* FILE       : RPTOUT   OUT CONTROL REPORT                       *
002300* FILE       : EXTOUT   OUT OUTBOUND EXTRACT FILE                *
002400* ---------------------------------------------------------------*
002500* MAINTENANCE HISTORY                                            *
002600* DATE       BY       REF        DESCRIPTION                     *
002700* ---------- -------- ---------- ------------------------------- *
002800* 1994-10-03 CLRPROJ             INITIAL VERSION - CLARA GO-LIVE *
002900* 2002-09-06 KBARR01             SQLCODE HANDLING ROUTED THROUGH *
003000*                                CLRERR01                        *
003100* 2012-02-19 DO                  DB2 VERSION MIGRATION - REBIND, *
003200*                                NO LOGIC CHANGE                 *
003300* 2014-08-20 PASHW01             ERROR MESSAGES STANDARDISED     *
003400* 2019-06-25 DO                  REMOVED DEAD CODE AFTER REVIEW  *
003500* 2024-03-06 DO                  SQL WARNINGS LOGGED, NOT        *
003600*                                TREATED AS ERRORS               *
003700* ===============================================================*
003800 IDENTIFICATION DIVISION.
003900 PROGRAM-ID.    CLRRP040.
004000 AUTHOR.        CLARA PROJECT TEAM.
004100 INSTALLATION.  CORVANE MUTUAL - CLAIMS SYSTEMS.
004200 DATE-WRITTEN.  1994-10-03.
004300 DATE-COMPILED.
004400 ENVIRONMENT DIVISION.
004500 CONFIGURATION SECTION.
004600 SOURCE-COMPUTER.  IBM-Z.
004700 OBJECT-COMPUTER.  IBM-Z.
004800 INPUT-OUTPUT SECTION.
004900 FILE-CONTROL.
005000     SELECT REPORT-FILE ASSIGN TO RPTOUT
005100         ORGANIZATION IS SEQUENTIAL
005200         FILE STATUS IS WS-RPTOUT-STATUS.
005300     SELECT EXTRACT-FILE ASSIGN TO EXTOUT
005400         ORGANIZATION IS SEQUENTIAL
005500         FILE STATUS IS WS-EXTOUT-STATUS.
005600 DATA DIVISION.
005700 FILE SECTION.
005800 FD  REPORT-FILE
005900         RECORDING MODE IS F
006000         BLOCK CONTAINS 0 RECORDS.
006100 01  REPORT-RECORD               PIC X(133).
006200 FD  EXTRACT-FILE
006300         RECORDING MODE IS F
006400         BLOCK CONTAINS 0 RECORDS.
006500 01  EXTRACT-RECORD              PIC X(400).
006600 WORKING-STORAGE SECTION.
006700*
006800 01  WS-PROGRAM-INFO.
006900     05  WS-PGM-ID               PIC X(8)   VALUE 'CLRRP040'.
007000     05  WS-RUN-DATE             PIC X(10)  VALUE SPACES.
007100     05  WS-RUN-TS               PIC X(26)  VALUE SPACES.
007200     05  WS-USER-ID              PIC X(8)   VALUE SPACES.
007300     05  WS-LAST-RUN-TS          PIC X(26)  VALUE SPACES.
007400     05  WS-RUN-ID               PIC S9(9)  COMP VALUE ZERO.
007500*
007600 01  WS-SWITCHES.
007700     05  WS-EOF-SW               PIC X      VALUE 'N'.
007800         88  WS-END-OF-DATA                     VALUE 'Y'.
007900     05  WS-ERROR-SW             PIC X      VALUE 'N'.
008000         88  WS-ERROR-FOUND                     VALUE 'Y'.
008100         88  WS-NO-ERROR                        VALUE 'N'.
008200     05  WS-FOUND-SW             PIC X      VALUE 'N'.
008300         88  WS-ROW-FOUND                       VALUE 'Y'.
008400         88  WS-ROW-NOT-FOUND                   VALUE 'N'.
008500     05  WS-RPTOUT-STATUS        PIC X(2)   VALUE SPACES.
008600     05  WS-EXTOUT-STATUS        PIC X(2)   VALUE SPACES.
008700*
008800 01  WS-COUNTERS.
008900     05  WS-CLAIM-READ           PIC S9(9)  COMP-3 VALUE ZERO.
009000     05  WS-REPORT-RUN-READ      PIC S9(9)  COMP-3 VALUE ZERO.
009100     05  WS-NISA-RETURN-WRITTEN  PIC S9(9)  COMP-3 VALUE ZERO.
009200     05  WS-REJECT-CNT           PIC S9(9)  COMP-3 VALUE ZERO.
009300     05  WS-SINCE-COMMIT         PIC S9(9)  COMP-3 VALUE ZERO.
009400     05  WS-COMMIT-FREQ          PIC S9(9)  COMP-3 VALUE +500.
009500*
009600 01  WS-SQL-WORK.
009700     05  WS-SQLCODE-DSP          PIC -9(9).
009800     05  WS-ROWS-AFFECTED        PIC S9(9)  COMP VALUE ZERO.
009900     05  WS-IND-1                PIC S9(4)  COMP VALUE ZERO.
010000     05  WS-IND-2                PIC S9(4)  COMP VALUE ZERO.
010100     05  WS-NEW-ID               PIC S9(18) COMP VALUE ZERO.
010200*
010300     EXEC SQL INCLUDE SQLCA END-EXEC.
010400*
010500* CLARA RECORD LAYOUTS
010600 COPY CLRCLM01.
010700 COPY NISARET1.
010800 COPY RPTRUN01.
010900 COPY CLRERR01.
011000 COPY CLRDATE1.
011100*
011200* PARAMETER AREAS FOR CALLED MODULES
011300 01  WS-AUDIT-PARMS.
011400     05  WS-AUD-TABLE            PIC X(18).
011500     05  WS-AUD-KEY              PIC X(30).
011600     05  WS-AUD-ACTION           PIC X(1).
011700     05  WS-AUD-USER             PIC X(8).
011800     05  WS-AUD-PGM              PIC X(8).
011900*
012000* DRIVING CURSOR ON CLR.T_CLAIM
012100     EXEC SQL
012200         DECLARE C-CLAIM CURSOR WITH HOLD FOR
012300         SELECT CLAIM_ID, POLICY_NO, PRODUCT_CD, PERIL_CD
012400                , LOSS_DT
012500           FROM CLR.T_CLAIM
012600          WHERE CLAIM_STATUS IN ('OP', 'RO', 'RC')
012700          ORDER BY CLAIM_ID
012800          FOR FETCH ONLY
012900     END-EXEC.
013000*
013100* CONTROL REPORT LINES
013200 01  WS-RPT-HEAD-1.
013300     05  FILLER                  PIC X(1)   VALUE '1'.
013400     05  FILLER                  PIC X(10)  VALUE 'CLRRP040'.
013500     05  FILLER                  PIC X(40)  VALUE
013600             'NISA-CT1 CLAIMS TIMELINESS EXTRACT'.
013700     05  FILLER                  PIC X(10)  VALUE 'RUN DATE: '.
013800     05  RH1-RUN-DATE            PIC X(10).
013900     05  FILLER                  PIC X(62)  VALUE SPACES.
014000 01  WS-RPT-DETAIL.
014100     05  FILLER                  PIC X(1)   VALUE SPACE.
014200     05  RD-LABEL                PIC X(40).
014300     05  RD-VALUE                PIC X(60).
014400     05  FILLER                  PIC X(32)  VALUE SPACES.
014500 01  WS-RPT-TOTAL.
014600     05  FILLER                  PIC X(1)   VALUE SPACE.
014700     05  RT-LABEL                PIC X(40).
014800     05  RT-COUNT                PIC ZZZ,ZZZ,ZZ9.
014900     05  FILLER                  PIC X(81)  VALUE SPACES.
015000 PROCEDURE DIVISION.
015100* ---------------------------------------------------------------*
015200* 0000-MAINLINE                                                  *
015300* MAIN CONTROL                                                   *
015400* ---------------------------------------------------------------*
015500 0000-MAINLINE.
015600     PERFORM 1000-INITIALISE
015700     PERFORM 2000-PROCESS
015800     PERFORM 9000-TERMINATE
015900     GOBACK.
016000* ---------------------------------------------------------------*
016100* 1000-INITIALISE                                                *
016200* OPEN FILES AND SET UP THE RUN                                  *
016300* ---------------------------------------------------------------*
016400 1000-INITIALISE.
016500     MOVE FUNCTION CURRENT-DATE(1:8) TO WS-RUN-TS
016600     STRING WS-RUN-TS(1:4) '-' WS-RUN-TS(5:2) '-' WS-RUN-TS(7:2)
016700         DELIMITED BY SIZE INTO WS-RUN-DATE
016800     MOVE 'CLRBATCH' TO WS-USER-ID
016900     OPEN OUTPUT REPORT-FILE
017000     IF WS-RPTOUT-STATUS NOT = '00'
017100         DISPLAY 'CLRRP040 OPEN FAILED RPTOUT ' WS-RPTOUT-STATUS
017200         MOVE 16 TO RETURN-CODE
017300         GOBACK
017400     END-IF
017500     OPEN OUTPUT EXTRACT-FILE
017600     IF WS-EXTOUT-STATUS NOT = '00'
017700         DISPLAY 'CLRRP040 OPEN FAILED EXTOUT ' WS-EXTOUT-STATUS
017800         MOVE 16 TO RETURN-CODE
017900         GOBACK
018000     END-IF
018100     MOVE WS-RUN-DATE TO RH1-RUN-DATE
018200     WRITE REPORT-RECORD FROM WS-RPT-HEAD-1
018300     PERFORM 1400-GET-BUSINESS-DATE
018400     .
018500* ---------------------------------------------------------------*
018600* 1400-GET-BUSINESS-DATE                                         *
018700* DETERMINE PROCESSING DATE                                      *
018800* ---------------------------------------------------------------*
018900 1400-GET-BUSINESS-DATE.
019000     MOVE WS-RUN-DATE TO DW-IN-DATE
019100     MOVE CLM-REGION-CD TO DW-CALENDAR
019200     MOVE ZERO TO DW-BUS-DAYS
019300     CALL 'CLRCM010' USING CLR-DATE-WORK
019400                      CLR-ERROR-BLOCK
019500     IF ERR-SQLCODE NOT = ZERO
019600         MOVE 'CALL CLRCM010' TO ERR-PARA
019700         PERFORM 8000-SQL-ERROR
019800     END-IF
019900     .
020000* ---------------------------------------------------------------*
020100* 2000-PROCESS                                                   *
020200* MAIN PROCESSING LOOP                                           *
020300* ---------------------------------------------------------------*
020400 2000-PROCESS.
020500     EXEC SQL
020600         OPEN C-CLAIM
020700     END-EXEC
020800     EVALUATE SQLCODE
020900         WHEN 0
021000             CONTINUE
021100         WHEN OTHER
021200             MOVE '2000-OPEN-C-CLAIM' TO ERR-PARA
021300             PERFORM 8000-SQL-ERROR
021400     END-EVALUATE
021500     PERFORM 2100-FETCH-NEXT
021600     PERFORM UNTIL WS-END-OF-DATA
021700         PERFORM 2200-PROCESS-ROW
021800         PERFORM 2100-FETCH-NEXT
021900     END-PERFORM
022000     EXEC SQL
022100         CLOSE C-CLAIM
022200     END-EXEC
022300     .
022400* ---------------------------------------------------------------*
022500* 2100-FETCH-NEXT                                                *
022600* FETCH THE NEXT DRIVING ROW                                     *
022700* ---------------------------------------------------------------*
022800 2100-FETCH-NEXT.
022900     EXEC SQL
023000         FETCH C-CLAIM
023100          INTO :CLM-CLAIM-ID, :CLM-POLICY-NO, :CLM-PRODUCT-CD
023200               , :CLM-PERIL-CD, :CLM-LOSS-DT
023300     END-EXEC
023400     EVALUATE SQLCODE
023500         WHEN 0
023600             ADD 1 TO WS-CLAIM-READ
023700         WHEN +100
023800             SET WS-END-OF-DATA TO TRUE
023900         WHEN OTHER
024000             MOVE '2100-FETCH-NEXT' TO ERR-PARA
024100             PERFORM 8000-SQL-ERROR
024200     END-EVALUATE
024300     .
024400* ---------------------------------------------------------------*
024500* 2200-PROCESS-ROW                                               *
024600* ONE UNIT OF WORK                                               *
024700* ---------------------------------------------------------------*
024800 2200-PROCESS-ROW.
024900     SET WS-NO-ERROR TO TRUE
025000     PERFORM 2300-READ-REPORT-RUN
025100     PERFORM 4100-INSERT-NISA-RETURN
025200     PERFORM 4900-WRITE-AUDIT
025300     PERFORM 5000-WRITE-EXTRACT
025400     PERFORM 6000-COMMIT-CHECK
025500     .
025600* ---------------------------------------------------------------*
025700* 2300-READ-REPORT-RUN                                           *
025800* FETCH CLR.T_REPORT_RUN                                         *
025900* ---------------------------------------------------------------*
026000 2300-READ-REPORT-RUN.
026100     SET WS-ROW-FOUND TO TRUE
026200     EXEC SQL
026300         SELECT RUN_ID, REPORT_CD, RUN_TS, ROW_COUNT
026400                , RUN_STATUS
026500           INTO :RPTR-RUN-ID, :RPTR-REPORT-CD, :RPTR-RUN-TS
026600                , :RPTR-ROW-COUNT, :RPTR-RUN-STATUS
026700           FROM CLR.T_REPORT_RUN
026800          WHERE RUN_ID = :RPTR-RUN-ID
026900     END-EXEC
027000     EVALUATE SQLCODE
027100         WHEN 0
027200             ADD 1 TO WS-REPORT-RUN-READ
027300         WHEN +100
027400             SET WS-ROW-NOT-FOUND TO TRUE
027500         WHEN OTHER
027600             MOVE 'READ CLR.T_REPORT_RUN' TO ERR-PARA
027700             PERFORM 8000-SQL-ERROR
027800     END-EVALUATE
027900     .
028000* ---------------------------------------------------------------*
028100* 4100-INSERT-NISA-RETURN                                        *
028200* INSERT CLR.T_NISA_RETURN                                       *
028300* ---------------------------------------------------------------*
028400 4100-INSERT-NISA-RETURN.
028500     EXEC SQL
028600         INSERT INTO CLR.T_NISA_RETURN
028700              ( RETURN_CD, PERIOD_CD, CELL_REF, CELL_VALUE
028800              , SUBMITTED_DT, ARCHIVE_FLAG, COMMENT_TXT
028900              , LAST_UPD_TS, LAST_UPD_PGM, LAST_UPD_USER )
029000         VALUES
029100              ( :NISA-RETURN-CD, :NISA-PERIOD-CD
029200              , :NISA-CELL-REF, :NISA-CELL-VALUE
029300              , :NISA-SUBMITTED-DT, :NISA-ARCHIVE-FLAG
029400              , :NISA-COMMENT-TXT, CURRENT TIMESTAMP
029500              , :WS-PGM-ID, :WS-USER-ID )
029600     END-EXEC
029700     EVALUATE SQLCODE
029800         WHEN 0
029900             ADD 1 TO WS-NISA-RETURN-WRITTEN
030000         WHEN +100
030100             SET WS-ROW-NOT-FOUND TO TRUE
030200         WHEN OTHER
030300             MOVE 'INSERT CLR.T_NISA_RETURN' TO ERR-PARA
030400             PERFORM 8000-SQL-ERROR
030500     END-EVALUATE
030600     .
030700* ---------------------------------------------------------------*
030800* 4900-WRITE-AUDIT                                               *
030900* AUDIT TRAIL VIA CLRCM020                                       *
031000* ---------------------------------------------------------------*
031100 4900-WRITE-AUDIT.
031200     MOVE 'CLR.T_NISA_RETURN' TO WS-AUD-TABLE
031300     MOVE CLM-CLAIM-ID TO WS-AUD-KEY
031400     MOVE 'I' TO WS-AUD-ACTION
031500     MOVE WS-USER-ID TO WS-AUD-USER
031600     MOVE WS-PGM-ID TO WS-AUD-PGM
031700     CALL 'CLRCM020' USING WS-AUDIT-PARMS
031800                      CLR-ERROR-BLOCK
031900     IF ERR-SQLCODE NOT = ZERO
032000         ADD 1 TO WS-REJECT-CNT
032100     END-IF
032200     .
032300* ---------------------------------------------------------------*
032400* 5000-WRITE-EXTRACT                                             *
032500* WRITE THE OUTBOUND RECORD                                      *
032600* ---------------------------------------------------------------*
032700 5000-WRITE-EXTRACT.
032800     MOVE SPACES TO EXTRACT-RECORD
032900     MOVE CLM-CLAIM-ID TO EXTRACT-RECORD(1:12)
033000     WRITE EXTRACT-RECORD
033100     IF WS-EXTOUT-STATUS NOT = '00'
033200         DISPLAY WS-PGM-ID ' WRITE FAILED EXTOUT '
033300             WS-EXTOUT-STATUS
033400         ADD 1 TO WS-REJECT-CNT
033500     END-IF
033600     .
033700* ---------------------------------------------------------------*
033800* 6000-COMMIT-CHECK                                              *
033900* PERIODIC COMMIT                                                *
034000* ---------------------------------------------------------------*
034100 6000-COMMIT-CHECK.
034200     ADD 1 TO WS-SINCE-COMMIT
034300     IF WS-SINCE-COMMIT >= WS-COMMIT-FREQ
034400         EXEC SQL
034500             COMMIT
034600         END-EXEC
034700         MOVE ZERO TO WS-SINCE-COMMIT
034800     END-IF
034900     .
035000* ---------------------------------------------------------------*
035100* 9000-TERMINATE                                                 *
035200* TERMINATION AND TOTALS                                         *
035300* ---------------------------------------------------------------*
035400 9000-TERMINATE.
035500     EXEC SQL
035600         COMMIT
035700     END-EXEC
035800     MOVE 'CLR.T_CLAIM ROWS READ' TO RT-LABEL
035900     MOVE WS-CLAIM-READ TO RT-COUNT
036000     WRITE REPORT-RECORD FROM WS-RPT-TOTAL
036100     MOVE 'CLR.T_REPORT_RUN ROWS READ' TO RT-LABEL
036200     MOVE WS-REPORT-RUN-READ TO RT-COUNT
036300     WRITE REPORT-RECORD FROM WS-RPT-TOTAL
036400     MOVE 'CLR.T_NISA_RETURN ROWS WRITTEN' TO RT-LABEL
036500     MOVE WS-NISA-RETURN-WRITTEN TO RT-COUNT
036600     WRITE REPORT-RECORD FROM WS-RPT-TOTAL
036700     CLOSE REPORT-FILE
036800     CLOSE EXTRACT-FILE
036900     IF WS-REJECT-CNT > ZERO
037000         MOVE 4 TO RETURN-CODE
037100     END-IF
037200     .
037300* ---------------------------------------------------------------*
037400* 8000-SQL-ERROR                                                 *
037500* UNEXPECTED SQLCODE                                             *
037600* ---------------------------------------------------------------*
037700 8000-SQL-ERROR.
037800     MOVE SQLCODE TO ERR-SQLCODE WS-SQLCODE-DSP
037900     MOVE WS-PGM-ID TO ERR-PGM
038000     STRING 'SQLCODE ' WS-SQLCODE-DSP DELIMITED BY SIZE INTO
038100         ERR-TEXT
038200     DISPLAY WS-PGM-ID ' ' ERR-PARA ' ' ERR-TEXT
038300     EXEC SQL
038400         ROLLBACK
038500     END-EXEC
038600     MOVE 16 TO RETURN-CODE
038700     CLOSE REPORT-FILE
038800     CLOSE EXTRACT-FILE
038900     GOBACK.

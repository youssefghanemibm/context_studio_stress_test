000100* ===============================================================*
000200* PROGRAM    : CLRRS140                                          *
000300* TITLE      : RESERVE HISTORY ARCHIVER (MONTH-END SNAPSHOTS)    *
000400* SYSTEM     : CLARA - CLAIMS LEDGER AND RESERVE APPLICATION     *
000500* AREA       : RESERVE                                           *
000600* TYPE       : BATCH / DB2                                       *
000700* JOB / STEP : CLRNRSV2 / STEP010                                *
000800* ---------------------------------------------------------------*
000900* PURPOSE                                                        *
001000*   NIGHTLY/PERIODIC BATCH STEP: RESERVE HISTORY ARCHIVER        *
001100*     (MONTH-END SNAPSHOTS).                                     *
001200*   EXECUTED BY JOB CLRNRSV2, STEP010.                           *
001300*   COMMITS EVERY 200 UNITS OF WORK.                             *
001400*   RETURN CODES: 0 OK, 4 WARNINGS, 16 SEVERE (SEE SYSOUT).      *
001500* ---------------------------------------------------------------*
001600* DB2 TABLES                                                     *
001700*   CLR.T_RESERVE               READ                             *
001800*   CLR.T_RESERVE_HISTORY       INSERT                           *
001900* COPYBOOKS  : RSVREC RSVHIS01 CLRERR01                          *
002000* CALLS      : CLRCM020                                          *
002100* FILE       : RPTOUT   OUT CONTROL REPORT                       *
002200* ---------------------------------------------------------------*
002300* MAINTENANCE HISTORY                                            *
002400* DATE       BY       REF        DESCRIPTION                     *
002500* ---------- -------- ---------- ------------------------------- *
002600* 2011-01-01 KBARR01             INITIAL VERSION                 *
002700* 2012-11-23 KBARR01             DATE ARITHMETIC MOVED TO        *
002800*                                CLRCM010                        *
002900* 2014-07-10 KBARR01             DB2 VERSION MIGRATION - REBIND, *
003000*                                NO LOGIC CHANGE                 *
003100* 2019-06-30 DO                  REMOVED DEAD CODE AFTER REVIEW  *
003200* ===============================================================*
003300 IDENTIFICATION DIVISION.
003400 PROGRAM-ID.    CLRRS140.
003500 AUTHOR.        K. BARRACLOUGH.
003600 INSTALLATION.  CORVANE MUTUAL - CLAIMS SYSTEMS.
003700 DATE-WRITTEN.  2011-01-01.
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
005700     05  WS-PGM-ID               PIC X(8)   VALUE 'CLRRS140'.
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
007600     05  WS-RESERVE-READ         PIC S9(9)  COMP-3 VALUE ZERO.
007700     05  WS-RESERVE-HISTORY-WRITTEN PIC S9(9) COMP-3 VALUE ZERO.
007800     05  WS-REJECT-CNT           PIC S9(9)  COMP-3 VALUE ZERO.
007900     05  WS-SINCE-COMMIT         PIC S9(9)  COMP-3 VALUE ZERO.
008000     05  WS-COMMIT-FREQ          PIC S9(9)  COMP-3 VALUE +200.
008100*
008200 01  WS-SQL-WORK.
008300     05  WS-SQLCODE-DSP          PIC -9(9).
008400     05  WS-ROWS-AFFECTED        PIC S9(9)  COMP VALUE ZERO.
008500     05  WS-IND-1                PIC S9(4)  COMP VALUE ZERO.
008600     05  WS-IND-2                PIC S9(4)  COMP VALUE ZERO.
008700     05  WS-NEW-ID               PIC S9(18) COMP VALUE ZERO.
008800*
008900     EXEC SQL INCLUDE SQLCA END-EXEC.
009000*
009100* CLARA RECORD LAYOUTS
009200 COPY RSVREC.
009300 COPY RSVHIS01.
009400 COPY CLRERR01.
009500*
009600* PARAMETER AREAS FOR CALLED MODULES
009700 01  WS-AUDIT-PARMS.
009800     05  WS-AUD-TABLE            PIC X(18).
009900     05  WS-AUD-KEY              PIC X(30).
010000     05  WS-AUD-ACTION           PIC X(1).
010100     05  WS-AUD-USER             PIC X(8).
010200     05  WS-AUD-PGM              PIC X(8).
010300*
010400* DRIVING CURSOR ON CLR.T_RESERVE
010500     EXEC SQL
010600         DECLARE C-RESERVE CURSOR WITH HOLD FOR
010700         SELECT RSV_ID, CLAIM_ID, RSV_TYPE_CD, CURRENCY_CD
010800                , RSV_INITIAL_AMT
010900           FROM CLR.T_RESERVE
011000          WHERE RSV_STATUS = 'O'
011100          ORDER BY RSV_ID
011200          FOR FETCH ONLY
011300     END-EXEC.
011400*
011500* CONTROL REPORT LINES
011600 01  WS-RPT-HEAD-1.
011700     05  FILLER                  PIC X(1)   VALUE '1'.
011800     05  FILLER                  PIC X(10)  VALUE 'CLRRS140'.
011900     05  FILLER                  PIC X(40)  VALUE
012000             'RESERVE HISTORY ARCHIVER (MONTH-END'.
012100     05  FILLER                  PIC X(10)  VALUE 'RUN DATE: '.
012200     05  RH1-RUN-DATE            PIC X(10).
012300     05  FILLER                  PIC X(62)  VALUE SPACES.
012400 01  WS-RPT-DETAIL.
012500     05  FILLER                  PIC X(1)   VALUE SPACE.
012600     05  RD-LABEL                PIC X(40).
012700     05  RD-VALUE                PIC X(60).
012800     05  FILLER                  PIC X(32)  VALUE SPACES.
012900 01  WS-RPT-TOTAL.
013000     05  FILLER                  PIC X(1)   VALUE SPACE.
013100     05  RT-LABEL                PIC X(40).
013200     05  RT-COUNT                PIC ZZZ,ZZZ,ZZ9.
013300     05  FILLER                  PIC X(81)  VALUE SPACES.
013400 PROCEDURE DIVISION.
013500* ---------------------------------------------------------------*
013600* 0000-MAINLINE                                                  *
013700* MAIN CONTROL                                                   *
013800* ---------------------------------------------------------------*
013900 0000-MAINLINE.
014000     PERFORM 1000-INITIALISE
014100     PERFORM 2000-PROCESS
014200     PERFORM 9000-TERMINATE
014300     GOBACK.
014400* ---------------------------------------------------------------*
014500* 1000-INITIALISE                                                *
014600* OPEN FILES AND SET UP THE RUN                                  *
014700* ---------------------------------------------------------------*
014800 1000-INITIALISE.
014900     MOVE FUNCTION CURRENT-DATE(1:8) TO WS-RUN-TS
015000     STRING WS-RUN-TS(1:4) '-' WS-RUN-TS(5:2) '-' WS-RUN-TS(7:2)
015100         DELIMITED BY SIZE INTO WS-RUN-DATE
015200     MOVE 'CLRBATCH' TO WS-USER-ID
015300     OPEN OUTPUT REPORT-FILE
015400     IF WS-RPTOUT-STATUS NOT = '00'
015500         DISPLAY 'CLRRS140 OPEN FAILED RPTOUT ' WS-RPTOUT-STATUS
015600         MOVE 16 TO RETURN-CODE
015700         GOBACK
015800     END-IF
015900     MOVE WS-RUN-DATE TO RH1-RUN-DATE
016000     WRITE REPORT-RECORD FROM WS-RPT-HEAD-1
016100     .
016200* ---------------------------------------------------------------*
016300* 2000-PROCESS                                                   *
016400* MAIN PROCESSING LOOP                                           *
016500* ---------------------------------------------------------------*
016600 2000-PROCESS.
016700     EXEC SQL
016800         OPEN C-RESERVE
016900     END-EXEC
017000     EVALUATE SQLCODE
017100         WHEN 0
017200             CONTINUE
017300         WHEN OTHER
017400             MOVE '2000-OPEN-C-RESERVE' TO ERR-PARA
017500             PERFORM 8000-SQL-ERROR
017600     END-EVALUATE
017700     PERFORM 2100-FETCH-NEXT
017800     PERFORM UNTIL WS-END-OF-DATA
017900         PERFORM 2200-PROCESS-ROW
018000         PERFORM 2100-FETCH-NEXT
018100     END-PERFORM
018200     EXEC SQL
018300         CLOSE C-RESERVE
018400     END-EXEC
018500     .
018600* ---------------------------------------------------------------*
018700* 2100-FETCH-NEXT                                                *
018800* FETCH THE NEXT DRIVING ROW                                     *
018900* ---------------------------------------------------------------*
019000 2100-FETCH-NEXT.
019100     EXEC SQL
019200         FETCH C-RESERVE
019300          INTO :RSV-RSV-ID, :RSV-CLAIM-ID, :RSV-RSV-TYPE-CD
019400               , :RSV-CURRENCY-CD, :RSV-RSV-INITIAL-AMT
019500     END-EXEC
019600     EVALUATE SQLCODE
019700         WHEN 0
019800             ADD 1 TO WS-RESERVE-READ
019900         WHEN +100
020000             SET WS-END-OF-DATA TO TRUE
020100         WHEN OTHER
020200             MOVE '2100-FETCH-NEXT' TO ERR-PARA
020300             PERFORM 8000-SQL-ERROR
020400     END-EVALUATE
020500     .
020600* ---------------------------------------------------------------*
020700* 2200-PROCESS-ROW                                               *
020800* ONE UNIT OF WORK                                               *
020900* ---------------------------------------------------------------*
021000 2200-PROCESS-ROW.
021100     SET WS-NO-ERROR TO TRUE
021200     PERFORM 2500-EDIT-RESERVE
021300     PERFORM 2510-EDIT-RESE-HIST
021400     PERFORM 2520-EDIT-RESERVE-2
021500     PERFORM 2530-EDIT-RESE-HIST-2
021600     PERFORM 2540-EDIT-RESERVE-3
021700     PERFORM 2550-EDIT-RESE-HIST-3
021800     PERFORM 4100-INSERT-RESE-HIST
021900     PERFORM 4900-WRITE-AUDIT
022000     PERFORM 6000-COMMIT-CHECK
022100     .
022200* ---------------------------------------------------------------*
022300* 2500-EDIT-RESERVE                                              *
022400* VALIDATE CLR.T_RESERVE                                         *
022500* ---------------------------------------------------------------*
022600 2500-EDIT-RESERVE.
022700     IF RSV-CLAIM-ID = SPACES OR LOW-VALUES
022800         ADD 1 TO WS-REJECT-CNT
022900         MOVE 'CLAIM_ID MISSING' TO ERR-TEXT
023000     END-IF
023100     IF RSV-RSV-TYPE-CD NOT = 'ID' AND RSV-RSV-TYPE-CD NOT = 'EX'
023200         AND RSV-RSV-TYPE-CD NOT = 'LG'
023300         ADD 1 TO WS-REJECT-CNT
023400         MOVE 'RSV_TYPE_CD INVALID' TO ERR-TEXT
023500     END-IF
023600     IF RSV-CURRENCY-CD = SPACES OR LOW-VALUES
023700         ADD 1 TO WS-REJECT-CNT
023800         MOVE 'CURRENCY_CD MISSING' TO ERR-TEXT
023900     END-IF
024000     IF RSV-RSV-INITIAL-AMT NOT NUMERIC
024100         MOVE ZERO TO RSV-RSV-INITIAL-AMT
024200         ADD 1 TO WS-REJECT-CNT
024300     END-IF
024400     IF RSV-RSV-OUTSTANDING-AMT NOT NUMERIC
024500         MOVE ZERO TO RSV-RSV-OUTSTANDING-AMT
024600         ADD 1 TO WS-REJECT-CNT
024700     END-IF
024800     IF RSV-RSV-PAID-TO-DATE-AMT NOT NUMERIC
024900         MOVE ZERO TO RSV-RSV-PAID-TO-DATE-AMT
025000         ADD 1 TO WS-REJECT-CNT
025100     END-IF
025200     .
025300* ---------------------------------------------------------------*
025400* 2510-EDIT-RESE-HIST                                            *
025500* VALIDATE CLR.T_RESERVE_HISTORY                                 *
025600* ---------------------------------------------------------------*
025700 2510-EDIT-RESE-HIST.
025800     IF RSVH-SNAPSHOT-DT NOT = SPACES AND RSVH-SNAPSHOT-DT(5:1)
025900         NOT = '-'
026000         MOVE 'SNAPSHOT_DT BAD DATE' TO ERR-TEXT
026100         ADD 1 TO WS-REJECT-CNT
026200     END-IF
026300     IF RSVH-RSV-OUTSTANDING-AMT NOT NUMERIC
026400         MOVE ZERO TO RSVH-RSV-OUTSTANDING-AMT
026500         ADD 1 TO WS-REJECT-CNT
026600     END-IF
026700     .
026800* ---------------------------------------------------------------*
026900* 2520-EDIT-RESERVE-2                                            *
027000* CHECK MANDATORY FIELDS IN CLR.T_RESERVE                        *
027100* ---------------------------------------------------------------*
027200 2520-EDIT-RESERVE-2.
027300     IF RSV-RSV-GBP-EQUIV-AMT NOT NUMERIC
027400         MOVE ZERO TO RSV-RSV-GBP-EQUIV-AMT
027500         ADD 1 TO WS-REJECT-CNT
027600     END-IF
027700     IF RSV-RSV-STATUS NOT = 'O' AND RSV-RSV-STATUS NOT = 'C'
027800         ADD 1 TO WS-REJECT-CNT
027900         MOVE 'RSV_STATUS INVALID' TO ERR-TEXT
028000     END-IF
028100     IF RSV-RSV-AUTH-LEVEL NOT = 'CH' AND RSV-RSV-AUTH-LEVEL NOT =
028200         'TL' AND RSV-RSV-AUTH-LEVEL NOT = 'CM' AND
028300         RSV-RSV-AUTH-LEVEL NOT = 'CD' AND RSV-RSV-AUTH-LEVEL NOT
028400         = 'RC'
028500         ADD 1 TO WS-REJECT-CNT
028600         MOVE 'RSV_AUTH_LEVEL INVALID' TO ERR-TEXT
028700     END-IF
028800     IF RSV-RSV-SET-BY-USER = SPACES OR LOW-VALUES
028900         ADD 1 TO WS-REJECT-CNT
029000         MOVE 'RSV_SET_BY_USER MISSING' TO ERR-TEXT
029100     END-IF
029200     IF RSV-RSV-NEXT-REVIEW-DT NOT = SPACES AND
029300         RSV-RSV-NEXT-REVIEW-DT(5:1) NOT = '-'
029400         MOVE 'RSV_NEXT_REVIEW_DT BAD DATE' TO ERR-TEXT
029500         ADD 1 TO WS-REJECT-CNT
029600     END-IF
029700     .
029800* ---------------------------------------------------------------*
029900* 2530-EDIT-RESE-HIST-2                                          *
030000* FIELD EDITS FOR CLR.T_RESERVE_HISTORY                          *
030100* ---------------------------------------------------------------*
030200 2530-EDIT-RESE-HIST-2.
030300     IF RSVH-RSV-GBP-EQUIV-AMT NOT NUMERIC
030400         MOVE ZERO TO RSVH-RSV-GBP-EQUIV-AMT
030500         ADD 1 TO WS-REJECT-CNT
030600     END-IF
030700     IF RSVH-TIER-CD = SPACES OR LOW-VALUES
030800         ADD 1 TO WS-REJECT-CNT
030900         MOVE 'TIER_CD MISSING' TO ERR-TEXT
031000     END-IF
031100     .
031200* ---------------------------------------------------------------*
031300* 2540-EDIT-RESERVE-3                                            *
031400* VALIDATE CLR.T_RESERVE                                         *
031500* ---------------------------------------------------------------*
031600 2540-EDIT-RESERVE-3.
031700     IF RSV-RSV-LAST-REVAL-DT NOT = SPACES AND
031800         RSV-RSV-LAST-REVAL-DT(5:1) NOT = '-'
031900         MOVE 'RSV_LAST_REVAL_DT BAD DATE' TO ERR-TEXT
032000         ADD 1 TO WS-REJECT-CNT
032100     END-IF
032200     .
032300* ---------------------------------------------------------------*
032400* 2550-EDIT-RESE-HIST-3                                          *
032500* VALIDATE CLR.T_RESERVE_HISTORY                                 *
032600* ---------------------------------------------------------------*
032700 2550-EDIT-RESE-HIST-3.
032800* ---------------------------------------------------------------*
032900* 4100-INSERT-RESE-HIST                                          *
033000* INSERT CLR.T_RESERVE_HISTORY                                   *
033100* ---------------------------------------------------------------*
033200 4100-INSERT-RESE-HIST.
033300     EXEC SQL
033400         INSERT INTO CLR.T_RESERVE_HISTORY
033500              ( RSV_ID, SNAPSHOT_DT, RSV_OUTSTANDING_AMT
033600              , RSV_GBP_EQUIV_AMT, TIER_CD, COMMENT_TXT
033700              , CREATED_TS, LAST_UPD_TS, LAST_UPD_PGM
033800              , LAST_UPD_USER )
033900         VALUES
034000              ( :RSVH-RSV-ID, :RSVH-SNAPSHOT-DT
034100              , :RSVH-RSV-OUTSTANDING-AMT
034200              , :RSVH-RSV-GBP-EQUIV-AMT, :RSVH-TIER-CD
034300              , :RSVH-COMMENT-TXT, CURRENT TIMESTAMP
034400              , CURRENT TIMESTAMP, :WS-PGM-ID, :WS-USER-ID )
034500     END-EXEC
034600     EVALUATE SQLCODE
034700         WHEN 0
034800             ADD 1 TO WS-RESERVE-HISTORY-WRITTEN
034900         WHEN +100
035000             SET WS-ROW-NOT-FOUND TO TRUE
035100         WHEN OTHER
035200             MOVE 'INSERT CLR.T_RESERVE_HISTORY' TO ERR-PARA
035300             PERFORM 8000-SQL-ERROR
035400     END-EVALUATE
035500     .
035600* ---------------------------------------------------------------*
035700* 4900-WRITE-AUDIT                                               *
035800* AUDIT TRAIL VIA CLRCM020                                       *
035900* ---------------------------------------------------------------*
036000 4900-WRITE-AUDIT.
036100     MOVE 'CLR.T_RESERVE_HISTORY' TO WS-AUD-TABLE
036200     MOVE RSV-CLAIM-ID TO WS-AUD-KEY
036300     MOVE 'I' TO WS-AUD-ACTION
036400     MOVE WS-USER-ID TO WS-AUD-USER
036500     MOVE WS-PGM-ID TO WS-AUD-PGM
036600     CALL 'CLRCM020' USING WS-AUDIT-PARMS
036700                      CLR-ERROR-BLOCK
036800     IF ERR-SQLCODE NOT = ZERO
036900         ADD 1 TO WS-REJECT-CNT
037000     END-IF
037100     .
037200* ---------------------------------------------------------------*
037300* 6000-COMMIT-CHECK                                              *
037400* PERIODIC COMMIT                                                *
037500* ---------------------------------------------------------------*
037600 6000-COMMIT-CHECK.
037700     ADD 1 TO WS-SINCE-COMMIT
037800     IF WS-SINCE-COMMIT >= WS-COMMIT-FREQ
037900         EXEC SQL
038000             COMMIT
038100         END-EXEC
038200         MOVE ZERO TO WS-SINCE-COMMIT
038300     END-IF
038400     .
038500* ---------------------------------------------------------------*
038600* 9000-TERMINATE                                                 *
038700* END OF RUN                                                     *
038800* ---------------------------------------------------------------*
038900 9000-TERMINATE.
039000     PERFORM 7010-LIST-RESERVE
039100     PERFORM 7030-LIST-RESE-HIST
039200     EXEC SQL
039300         COMMIT
039400     END-EXEC
039500     MOVE 'CLR.T_RESERVE ROWS READ' TO RT-LABEL
039600     MOVE WS-RESERVE-READ TO RT-COUNT
039700     WRITE REPORT-RECORD FROM WS-RPT-TOTAL
039800     MOVE 'CLR.T_RESERVE_HISTORY ROWS WRITTEN' TO RT-LABEL
039900     MOVE WS-RESERVE-HISTORY-WRITTEN TO RT-COUNT
040000     WRITE REPORT-RECORD FROM WS-RPT-TOTAL
040100     CLOSE REPORT-FILE
040200     IF WS-REJECT-CNT > ZERO
040300         MOVE 4 TO RETURN-CODE
040400     END-IF
040500     .
040600* ---------------------------------------------------------------*
040700* 7010-LIST-RESERVE                                              *
040800* LIST CLR.T_RESERVE FIELDS ON THE REPORT                        *
040900* ---------------------------------------------------------------*
041000 7010-LIST-RESERVE.
041100     MOVE 'LAST CLR.T_RESERVE ROW' TO RD-LABEL
041200     MOVE SPACES TO RD-VALUE
041300     WRITE REPORT-RECORD FROM WS-RPT-DETAIL
041400     MOVE '  CLAIM_ID' TO RD-LABEL
041500     MOVE RSV-CLAIM-ID TO RD-VALUE
041600     WRITE REPORT-RECORD FROM WS-RPT-DETAIL
041700     MOVE '  RSV_TYPE_CD' TO RD-LABEL
041800     MOVE RSV-RSV-TYPE-CD TO RD-VALUE
041900     WRITE REPORT-RECORD FROM WS-RPT-DETAIL
042000     MOVE '  CURRENCY_CD' TO RD-LABEL
042100     MOVE RSV-CURRENCY-CD TO RD-VALUE
042200     WRITE REPORT-RECORD FROM WS-RPT-DETAIL
042300     .
042400* ---------------------------------------------------------------*
042500* 7030-LIST-RESE-HIST                                            *
042600* LIST CLR.T_RESERVE_HISTORY FIELDS ON THE REPORT                *
042700* ---------------------------------------------------------------*
042800 7030-LIST-RESE-HIST.
042900     MOVE 'LAST CLR.T_RESERVE_HISTORY ROW' TO RD-LABEL
043000     MOVE SPACES TO RD-VALUE
043100     WRITE REPORT-RECORD FROM WS-RPT-DETAIL
043200     MOVE '  SNAPSHOT_DT' TO RD-LABEL
043300     MOVE RSVH-SNAPSHOT-DT TO RD-VALUE
043400     WRITE REPORT-RECORD FROM WS-RPT-DETAIL
043500     MOVE '  TIER_CD' TO RD-LABEL
043600     MOVE RSVH-TIER-CD TO RD-VALUE
043700     WRITE REPORT-RECORD FROM WS-RPT-DETAIL
043800     MOVE '  COMMENT_TXT' TO RD-LABEL
043900     MOVE RSVH-COMMENT-TXT TO RD-VALUE
044000     WRITE REPORT-RECORD FROM WS-RPT-DETAIL
044100     MOVE '  CREATED_TS' TO RD-LABEL
044200     MOVE RSVH-CREATED-TS TO RD-VALUE
044300     WRITE REPORT-RECORD FROM WS-RPT-DETAIL
044400     .
044500* ---------------------------------------------------------------*
044600* 8000-SQL-ERROR                                                 *
044700* UNEXPECTED SQLCODE                                             *
044800* ---------------------------------------------------------------*
044900 8000-SQL-ERROR.
045000     MOVE SQLCODE TO ERR-SQLCODE WS-SQLCODE-DSP
045100     MOVE WS-PGM-ID TO ERR-PGM
045200     STRING 'SQLCODE ' WS-SQLCODE-DSP DELIMITED BY SIZE INTO
045300         ERR-TEXT
045400     DISPLAY WS-PGM-ID ' ' ERR-PARA ' ' ERR-TEXT
045500     EXEC SQL
045600         ROLLBACK
045700     END-EXEC
045800     MOVE 16 TO RETURN-CODE
045900     CLOSE REPORT-FILE
046000     GOBACK.

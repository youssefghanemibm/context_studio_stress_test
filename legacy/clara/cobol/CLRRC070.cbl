000100* ===============================================================*
000200* PROGRAM    : CLRRC070                                          *
000300* TITLE      : SALVAGE DISPOSAL IMPORT (SALVANTA, CLX-IF-024)    *
000400* SYSTEM     : CLARA - CLAIMS LEDGER AND RESERVE APPLICATION     *
000500* AREA       : RECOVER                                           *
000600* TYPE       : BATCH / DB2                                       *
000700* JOB / STEP : CLRNRC01 / STEP030                                *
000800* ---------------------------------------------------------------*
000900* PURPOSE                                                        *
001000*   NIGHTLY/PERIODIC BATCH STEP: SALVAGE DISPOSAL IMPORT         *
001100*     (SALVANTA, CLX-IF-024).                                    *
001200*   RUNS AS STEP030 OF JOB CLRNRC01.                             *
001300*   DB2 COMMIT AFTER EVERY 500 UPDATES.                          *
001400*   CONDITION CODES: 00 NORMAL / 04 WARNING / 16 FAILURE.        *
001500* ---------------------------------------------------------------*
001600* DB2 TABLES                                                     *
001700*   CLR.T_CLAIM                 READ                             *
001800*   CLR.T_RECOVERY              READ                             *
001900*   CLR.T_SALVAGE               INSERT                           *
002000* COPYBOOKS  : CLRCLM01 RCVREC01 SALREC01 CLRERR01               *
002100* CALLS      : CLRCM020                                          *
002200* FILE       : RPTOUT   OUT CONTROL REPORT                       *
002300* FILE       : IMPIN    IN  INBOUND INTERFACE FILE               *
002400* ---------------------------------------------------------------*
002500* MAINTENANCE HISTORY                                            *
002600* DATE       BY       REF        DESCRIPTION                     *
002700* ---------- -------- ---------- ------------------------------- *
002800* 1994-10-03 CLRPROJ             INITIAL VERSION - CLARA GO-LIVE *
002900* 2002-12-24 KBARR01             SQLCODE HANDLING ROUTED THROUGH *
003000*                                CLRERR01                        *
003100* 2011-07-29 KBARR01             DB2 VERSION MIGRATION - REBIND, *
003200*                                NO LOGIC CHANGE                 *
003300* 2023-02-24 KBARR01             SQL WARNINGS LOGGED, NOT        *
003400*                                TREATED AS ERRORS               *
003500* 2023-10-09 KBARR01             NORDIC CURRENCY CODES VALIDATED *
003600* ===============================================================*
003700 IDENTIFICATION DIVISION.
003800 PROGRAM-ID.    CLRRC070.
003900 AUTHOR.        CLARA PROJECT TEAM.
004000 INSTALLATION.  CORVANE MUTUAL - CLAIMS SYSTEMS.
004100 DATE-WRITTEN.  1994-10-03.
004200 DATE-COMPILED.
004300 ENVIRONMENT DIVISION.
004400 CONFIGURATION SECTION.
004500 SOURCE-COMPUTER.  IBM-Z.
004600 OBJECT-COMPUTER.  IBM-Z.
004700 INPUT-OUTPUT SECTION.
004800 FILE-CONTROL.
004900     SELECT REPORT-FILE ASSIGN TO RPTOUT
005000         ORGANIZATION IS SEQUENTIAL
005100         FILE STATUS IS WS-RPTOUT-STATUS.
005200     SELECT INPUT-FILE ASSIGN TO IMPIN
005300         ORGANIZATION IS SEQUENTIAL
005400         FILE STATUS IS WS-IMPIN-STATUS.
005500 DATA DIVISION.
005600 FILE SECTION.
005700 FD  REPORT-FILE
005800         RECORDING MODE IS F
005900         BLOCK CONTAINS 0 RECORDS.
006000 01  REPORT-RECORD               PIC X(133).
006100 FD  INPUT-FILE
006200         RECORDING MODE IS F
006300         BLOCK CONTAINS 0 RECORDS.
006400 01  INPUT-RECORD                PIC X(400).
006500 WORKING-STORAGE SECTION.
006600*
006700 01  WS-PROGRAM-INFO.
006800     05  WS-PGM-ID               PIC X(8)   VALUE 'CLRRC070'.
006900     05  WS-RUN-DATE             PIC X(10)  VALUE SPACES.
007000     05  WS-RUN-TS               PIC X(26)  VALUE SPACES.
007100     05  WS-USER-ID              PIC X(8)   VALUE SPACES.
007200     05  WS-LAST-RUN-TS          PIC X(26)  VALUE SPACES.
007300     05  WS-RUN-ID               PIC S9(9)  COMP VALUE ZERO.
007400*
007500 01  WS-SWITCHES.
007600     05  WS-EOF-SW               PIC X      VALUE 'N'.
007700         88  WS-END-OF-DATA                     VALUE 'Y'.
007800     05  WS-ERROR-SW             PIC X      VALUE 'N'.
007900         88  WS-ERROR-FOUND                     VALUE 'Y'.
008000         88  WS-NO-ERROR                        VALUE 'N'.
008100     05  WS-FOUND-SW             PIC X      VALUE 'N'.
008200         88  WS-ROW-FOUND                       VALUE 'Y'.
008300         88  WS-ROW-NOT-FOUND                   VALUE 'N'.
008400     05  WS-RPTOUT-STATUS        PIC X(2)   VALUE SPACES.
008500     05  WS-IMPIN-STATUS         PIC X(2)   VALUE SPACES.
008600*
008700 01  WS-COUNTERS.
008800     05  WS-CLAIM-READ           PIC S9(9)  COMP-3 VALUE ZERO.
008900     05  WS-RECOVERY-READ        PIC S9(9)  COMP-3 VALUE ZERO.
009000     05  WS-SALVAGE-WRITTEN      PIC S9(9)  COMP-3 VALUE ZERO.
009100     05  WS-REJECT-CNT           PIC S9(9)  COMP-3 VALUE ZERO.
009200     05  WS-SINCE-COMMIT         PIC S9(9)  COMP-3 VALUE ZERO.
009300     05  WS-COMMIT-FREQ          PIC S9(9)  COMP-3 VALUE +500.
009400*
009500 01  WS-SQL-WORK.
009600     05  WS-SQLCODE-DSP          PIC -9(9).
009700     05  WS-ROWS-AFFECTED        PIC S9(9)  COMP VALUE ZERO.
009800     05  WS-IND-1                PIC S9(4)  COMP VALUE ZERO.
009900     05  WS-IND-2                PIC S9(4)  COMP VALUE ZERO.
010000     05  WS-NEW-ID               PIC S9(18) COMP VALUE ZERO.
010100 01  WS-INPUT-AREA             PIC X(400).
010200*
010300     EXEC SQL INCLUDE SQLCA END-EXEC.
010400*
010500* APPLICATION COPYBOOKS
010600 COPY CLRCLM01.
010700 COPY RCVREC01.
010800 COPY SALREC01.
010900 COPY CLRERR01.
011000*
011100* CALL INTERFACES
011200 01  WS-AUDIT-PARMS.
011300     05  WS-AUD-TABLE            PIC X(18).
011400     05  WS-AUD-KEY              PIC X(30).
011500     05  WS-AUD-ACTION           PIC X(1).
011600     05  WS-AUD-USER             PIC X(8).
011700     05  WS-AUD-PGM              PIC X(8).
011800*
011900* CONTROL REPORT LINES
012000 01  WS-RPT-HEAD-1.
012100     05  FILLER                  PIC X(1)   VALUE '1'.
012200     05  FILLER                  PIC X(10)  VALUE 'CLRRC070'.
012300     05  FILLER                  PIC X(40)  VALUE
012400             'SALVAGE DISPOSAL IMPORT (SALVANTA,'.
012500     05  FILLER                  PIC X(10)  VALUE 'RUN DATE: '.
012600     05  RH1-RUN-DATE            PIC X(10).
012700     05  FILLER                  PIC X(62)  VALUE SPACES.
012800 01  WS-RPT-DETAIL.
012900     05  FILLER                  PIC X(1)   VALUE SPACE.
013000     05  RD-LABEL                PIC X(40).
013100     05  RD-VALUE                PIC X(60).
013200     05  FILLER                  PIC X(32)  VALUE SPACES.
013300 01  WS-RPT-TOTAL.
013400     05  FILLER                  PIC X(1)   VALUE SPACE.
013500     05  RT-LABEL                PIC X(40).
013600     05  RT-COUNT                PIC ZZZ,ZZZ,ZZ9.
013700     05  FILLER                  PIC X(81)  VALUE SPACES.
013800 PROCEDURE DIVISION.
013900* ---------------------------------------------------------------*
014000* 0000-MAINLINE                                                  *
014100* PROGRAM CONTROL                                                *
014200* ---------------------------------------------------------------*
014300 0000-MAINLINE.
014400     PERFORM 1000-INITIALISE THRU 1000-INITIALISE-EXIT
014500     PERFORM 2000-PROCESS THRU 2000-PROCESS-EXIT
014600     PERFORM 9000-TERMINATE THRU 9000-TERMINATE-EXIT
014700     GOBACK.
014800 0000-MAINLINE-EXIT.
014900     EXIT.
015000* ---------------------------------------------------------------*
015100* 1000-INITIALISE                                                *
015200* START OF RUN                                                   *
015300* ---------------------------------------------------------------*
015400 1000-INITIALISE.
015500     MOVE FUNCTION CURRENT-DATE(1:8) TO WS-RUN-TS
015600     STRING WS-RUN-TS(1:4) '-' WS-RUN-TS(5:2) '-' WS-RUN-TS(7:2)
015700         DELIMITED BY SIZE INTO WS-RUN-DATE
015800     MOVE 'CLRBATCH' TO WS-USER-ID
015900     OPEN OUTPUT REPORT-FILE
016000     IF WS-RPTOUT-STATUS NOT = '00'
016100         DISPLAY 'CLRRC070 OPEN FAILED RPTOUT ' WS-RPTOUT-STATUS
016200         MOVE 16 TO RETURN-CODE
016300         GOBACK
016400     END-IF
016500     OPEN INPUT INPUT-FILE
016600     IF WS-IMPIN-STATUS NOT = '00'
016700         DISPLAY 'CLRRC070 OPEN FAILED IMPIN ' WS-IMPIN-STATUS
016800         MOVE 16 TO RETURN-CODE
016900         GOBACK
017000     END-IF
017100     MOVE WS-RUN-DATE TO RH1-RUN-DATE
017200     WRITE REPORT-RECORD FROM WS-RPT-HEAD-1
017300     .
017400 1000-INITIALISE-EXIT.
017500     EXIT.
017600* ---------------------------------------------------------------*
017700* 2000-PROCESS                                                   *
017800* READ AND PROCESS ALL INPUT                                     *
017900* ---------------------------------------------------------------*
018000 2000-PROCESS.
018100     PERFORM 2100-READ-INPUT THRU 2100-READ-INPUT-EXIT
018200     PERFORM 2200-PROCESS-ROW THRU 2200-PROCESS-ROW-EXIT
018300         UNTIL WS-END-OF-DATA
018400     .
018500 2000-PROCESS-EXIT.
018600     EXIT.
018700* ---------------------------------------------------------------*
018800* 2100-READ-INPUT                                                *
018900* READ THE NEXT INPUT RECORD                                     *
019000* ---------------------------------------------------------------*
019100 2100-READ-INPUT.
019200     READ INPUT-FILE
019300         AT END
019400             SET WS-END-OF-DATA TO TRUE
019500         NOT AT END
019600             CONTINUE
019700     END-READ
019800     .
019900 2100-READ-INPUT-EXIT.
020000     EXIT.
020100* ---------------------------------------------------------------*
020200* 2200-PROCESS-ROW                                               *
020300* PROCESS ONE ROW                                                *
020400* ---------------------------------------------------------------*
020500 2200-PROCESS-ROW.
020600     IF WS-END-OF-DATA
020700         GO TO 2200-PROCESS-ROW-EXIT
020800     END-IF
020900     SET WS-NO-ERROR TO TRUE
021000     MOVE INPUT-RECORD TO WS-INPUT-AREA
021100     PERFORM 2300-READ-CLAIM THRU 2300-READ-CLAIM-EXIT
021200     PERFORM 2320-READ-RECOVERY THRU 2320-READ-RECOVERY-EXIT
021300     PERFORM 4100-INSERT-SALVAGE THRU 4100-INSERT-SALVAGE-EXIT
021400     PERFORM 4900-WRITE-AUDIT THRU 4900-WRITE-AUDIT-EXIT
021500     PERFORM 6000-COMMIT-CHECK THRU 6000-COMMIT-CHECK-EXIT
021600     .
021700 2200-PROCESS-ROW-EXIT.
021800     EXIT.
021900* ---------------------------------------------------------------*
022000* 2300-READ-CLAIM                                                *
022100* LOOK UP CLR.T_CLAIM                                            *
022200* ---------------------------------------------------------------*
022300 2300-READ-CLAIM.
022400     MOVE CLM-CLAIM-ID TO CLM-CLAIM-ID
022500     SET WS-ROW-FOUND TO TRUE
022600     EXEC SQL
022700         SELECT CLAIM_ID, POLICY_NO, PRODUCT_CD, PERIL_CD
022800                , LOSS_DT
022900           INTO :CLM-CLAIM-ID, :CLM-POLICY-NO
023000                , :CLM-PRODUCT-CD, :CLM-PERIL-CD
023100                , :CLM-LOSS-DT
023200           FROM CLR.T_CLAIM
023300          WHERE CLAIM_ID = :CLM-CLAIM-ID
023400     END-EXEC
023500     EVALUATE SQLCODE
023600         WHEN 0
023700             ADD 1 TO WS-CLAIM-READ
023800         WHEN +100
023900             SET WS-ROW-NOT-FOUND TO TRUE
024000         WHEN OTHER
024100             MOVE 'READ CLR.T_CLAIM' TO ERR-PARA
024200             PERFORM 8000-SQL-ERROR
024300     END-EVALUATE
024400     .
024500 2300-READ-CLAIM-EXIT.
024600     EXIT.
024700* ---------------------------------------------------------------*
024800* 2320-READ-RECOVERY                                             *
024900* READ CLR.T_RECOVERY                                            *
025000* ---------------------------------------------------------------*
025100 2320-READ-RECOVERY.
025200     SET WS-ROW-FOUND TO TRUE
025300     EXEC SQL
025400         SELECT RCV_ID, CLAIM_ID, SUBRO_CASE_ID
025500           INTO :RCVR-RCV-ID, :RCVR-CLAIM-ID
025600                , :RCVR-SUBRO-CASE-ID
025700           FROM CLR.T_RECOVERY
025800          WHERE RCV_ID = :RCVR-RCV-ID
025900     END-EXEC
026000     EVALUATE SQLCODE
026100         WHEN 0
026200             ADD 1 TO WS-RECOVERY-READ
026300         WHEN +100
026400             SET WS-ROW-NOT-FOUND TO TRUE
026500         WHEN OTHER
026600             MOVE 'READ CLR.T_RECOVERY' TO ERR-PARA
026700             PERFORM 8000-SQL-ERROR
026800     END-EVALUATE
026900     .
027000 2320-READ-RECOVERY-EXIT.
027100     EXIT.
027200* ---------------------------------------------------------------*
027300* 4100-INSERT-SALVAGE                                            *
027400* INSERT CLR.T_SALVAGE                                           *
027500* ---------------------------------------------------------------*
027600 4100-INSERT-SALVAGE.
027700     MOVE CLM-CLAIM-ID TO SALR-CLAIM-ID
027800     EXEC SQL
027900         INSERT INTO CLR.T_SALVAGE
028000              ( CLAIM_ID, SALV_CATEGORY, DISPOSAL_DT
028100              , PROCEEDS_AMT, VENDOR_CD, CREATED_TS
028200              , LAST_UPD_TS, LAST_UPD_PGM, LAST_UPD_USER )
028300         VALUES
028400              ( :SALR-CLAIM-ID, :SALR-SALV-CATEGORY
028500              , :SALR-DISPOSAL-DT, :SALR-PROCEEDS-AMT
028600              , :SALR-VENDOR-CD, CURRENT TIMESTAMP
028700              , CURRENT TIMESTAMP, :WS-PGM-ID, :WS-USER-ID )
028800     END-EXEC
028900     EVALUATE SQLCODE
029000         WHEN 0
029100             ADD 1 TO WS-SALVAGE-WRITTEN
029200         WHEN +100
029300             SET WS-ROW-NOT-FOUND TO TRUE
029400         WHEN OTHER
029500             MOVE 'INSERT CLR.T_SALVAGE' TO ERR-PARA
029600             PERFORM 8000-SQL-ERROR
029700     END-EVALUATE
029800     .
029900 4100-INSERT-SALVAGE-EXIT.
030000     EXIT.
030100* ---------------------------------------------------------------*
030200* 4900-WRITE-AUDIT                                               *
030300* AUDIT TRAIL VIA CLRCM020                                       *
030400* ---------------------------------------------------------------*
030500 4900-WRITE-AUDIT.
030600     MOVE 'CLR.T_SALVAGE' TO WS-AUD-TABLE
030700     MOVE CLM-CLAIM-ID TO WS-AUD-KEY
030800     MOVE 'A' TO WS-AUD-ACTION
030900     MOVE WS-USER-ID TO WS-AUD-USER
031000     MOVE WS-PGM-ID TO WS-AUD-PGM
031100     CALL 'CLRCM020' USING WS-AUDIT-PARMS
031200                      CLR-ERROR-BLOCK
031300     IF ERR-SQLCODE NOT = ZERO
031400         ADD 1 TO WS-REJECT-CNT
031500     END-IF
031600     .
031700 4900-WRITE-AUDIT-EXIT.
031800     EXIT.
031900* ---------------------------------------------------------------*
032000* 6000-COMMIT-CHECK                                              *
032100* PERIODIC COMMIT                                                *
032200* ---------------------------------------------------------------*
032300 6000-COMMIT-CHECK.
032400     ADD 1 TO WS-SINCE-COMMIT
032500     IF WS-SINCE-COMMIT >= WS-COMMIT-FREQ
032600         EXEC SQL
032700             COMMIT
032800         END-EXEC
032900         MOVE ZERO TO WS-SINCE-COMMIT
033000     END-IF
033100     .
033200 6000-COMMIT-CHECK-EXIT.
033300     EXIT.
033400* ---------------------------------------------------------------*
033500* 9000-TERMINATE                                                 *
033600* TERMINATION AND TOTALS                                         *
033700* ---------------------------------------------------------------*
033800 9000-TERMINATE.
033900     EXEC SQL
034000         COMMIT
034100     END-EXEC
034200     MOVE 'CLR.T_CLAIM ROWS READ' TO RT-LABEL
034300     MOVE WS-CLAIM-READ TO RT-COUNT
034400     WRITE REPORT-RECORD FROM WS-RPT-TOTAL
034500     MOVE 'CLR.T_RECOVERY ROWS READ' TO RT-LABEL
034600     MOVE WS-RECOVERY-READ TO RT-COUNT
034700     WRITE REPORT-RECORD FROM WS-RPT-TOTAL
034800     MOVE 'CLR.T_SALVAGE ROWS WRITTEN' TO RT-LABEL
034900     MOVE WS-SALVAGE-WRITTEN TO RT-COUNT
035000     WRITE REPORT-RECORD FROM WS-RPT-TOTAL
035100     CLOSE REPORT-FILE
035200     CLOSE INPUT-FILE
035300     IF WS-REJECT-CNT > ZERO
035400         MOVE 4 TO RETURN-CODE
035500     END-IF
035600     .
035700 9000-TERMINATE-EXIT.
035800     EXIT.
035900* ---------------------------------------------------------------*
036000* 8000-SQL-ERROR                                                 *
036100* DB2 ERROR HANDLING                                             *
036200* ---------------------------------------------------------------*
036300 8000-SQL-ERROR.
036400     MOVE SQLCODE TO ERR-SQLCODE WS-SQLCODE-DSP
036500     MOVE WS-PGM-ID TO ERR-PGM
036600     STRING 'SQLCODE ' WS-SQLCODE-DSP DELIMITED BY SIZE INTO
036700         ERR-TEXT
036800     DISPLAY WS-PGM-ID ' ' ERR-PARA ' ' ERR-TEXT
036900     EXEC SQL
037000         ROLLBACK
037100     END-EXEC
037200     MOVE 16 TO RETURN-CODE
037300     CLOSE REPORT-FILE
037400     CLOSE INPUT-FILE
037500     GOBACK.
037600 8000-SQL-ERROR-EXIT.
037700     EXIT.

000100* ===============================================================*
000200* PROGRAM    : CLRAS090                                          *
000300* TITLE      : DESK ASSESSMENT QUEUE BUILDER (BR-ASM-008)        *
000400* SYSTEM     : CLARA - CLAIMS LEDGER AND RESERVE APPLICATION     *
000500* AREA       : ASSESS                                            *
000600* TYPE       : BATCH / DB2                                       *
000700* JOB / STEP : CLRWMI01 / STEP020                                *
000800* ---------------------------------------------------------------*
000900* PURPOSE                                                        *
001000*   BATCH DB2 PROGRAM - DESK ASSESSMENT QUEUE BUILDER            *
001100*     (BR-ASM-008).                                              *
001200*   SCHEDULED UNDER JOB CLRWMI01 (STEP020).                      *
001300*   RC 0 = NORMAL, RC 4 = REJECTS REPORTED, RC 16 = ABORTED.     *
001400* ---------------------------------------------------------------*
001500* DB2 TABLES                                                     *
001600*   CLR.T_INSPECTION            READ                             *
001700* COPYBOOKS  : CLRINS01 CLRERR01 CLRDATE1                        *
001800* CALLS      : CLRCM010                                          *
001900* FILE       : RPTOUT   OUT CONTROL REPORT                       *
002000* ---------------------------------------------------------------*
002100* MAINTENANCE HISTORY                                            *
002200* DATE       BY       REF        DESCRIPTION                     *
002300* ---------- -------- ---------- ------------------------------- *
002400* 1994-10-03 CLRPROJ             INITIAL VERSION - CLARA GO-LIVE *
002500* 2010-10-12 KBARR01             DB2 VERSION MIGRATION - REBIND, *
002600*                                NO LOGIC CHANGE                 *
002700* ===============================================================*
002800 IDENTIFICATION DIVISION.
002900 PROGRAM-ID.    CLRAS090.
003000 AUTHOR.        CLARA PROJECT TEAM.
003100 INSTALLATION.  CORVANE MUTUAL - CLAIMS SYSTEMS.
003200 DATE-WRITTEN.  1994-10-03.
003300 DATE-COMPILED.
003400 ENVIRONMENT DIVISION.
003500 CONFIGURATION SECTION.
003600 SOURCE-COMPUTER.  IBM-Z.
003700 OBJECT-COMPUTER.  IBM-Z.
003800 INPUT-OUTPUT SECTION.
003900 FILE-CONTROL.
004000     SELECT REPORT-FILE ASSIGN TO RPTOUT
004100         ORGANIZATION IS SEQUENTIAL
004200         FILE STATUS IS WS-RPTOUT-STATUS.
004300 DATA DIVISION.
004400 FILE SECTION.
004500 FD  REPORT-FILE
004600         RECORDING MODE IS F
004700         BLOCK CONTAINS 0 RECORDS.
004800 01  REPORT-RECORD               PIC X(133).
004900 WORKING-STORAGE SECTION.
005000*
005100 01  WS-PROGRAM-INFO.
005200     05  WS-PGM-ID               PIC X(8)   VALUE 'CLRAS090'.
005300     05  WS-RUN-DATE             PIC X(10)  VALUE SPACES.
005400     05  WS-RUN-TS               PIC X(26)  VALUE SPACES.
005500     05  WS-USER-ID              PIC X(8)   VALUE SPACES.
005600     05  WS-LAST-RUN-TS          PIC X(26)  VALUE SPACES.
005700     05  WS-RUN-ID               PIC S9(9)  COMP VALUE ZERO.
005800*
005900 01  WS-SWITCHES.
006000     05  WS-EOF-SW               PIC X      VALUE 'N'.
006100         88  WS-END-OF-DATA                     VALUE 'Y'.
006200     05  WS-ERROR-SW             PIC X      VALUE 'N'.
006300         88  WS-ERROR-FOUND                     VALUE 'Y'.
006400         88  WS-NO-ERROR                        VALUE 'N'.
006500     05  WS-FOUND-SW             PIC X      VALUE 'N'.
006600         88  WS-ROW-FOUND                       VALUE 'Y'.
006700         88  WS-ROW-NOT-FOUND                   VALUE 'N'.
006800     05  WS-RPTOUT-STATUS        PIC X(2)   VALUE SPACES.
006900*
007000 01  WS-COUNTERS.
007100     05  WS-INSPECTION-READ      PIC S9(9)  COMP-3 VALUE ZERO.
007200     05  WS-REJECT-CNT           PIC S9(9)  COMP-3 VALUE ZERO.
007300*
007400 01  WS-SQL-WORK.
007500     05  WS-SQLCODE-DSP          PIC -9(9).
007600     05  WS-ROWS-AFFECTED        PIC S9(9)  COMP VALUE ZERO.
007700     05  WS-IND-1                PIC S9(4)  COMP VALUE ZERO.
007800     05  WS-IND-2                PIC S9(4)  COMP VALUE ZERO.
007900     05  WS-NEW-ID               PIC S9(18) COMP VALUE ZERO.
008000*
008100     EXEC SQL INCLUDE SQLCA END-EXEC.
008200*
008300* CLARA RECORD LAYOUTS
008400 COPY CLRINS01.
008500 COPY CLRERR01.
008600 COPY CLRDATE1.
008700*
008800* DRIVING CURSOR ON CLR.T_INSPECTION
008900     EXEC SQL
009000         DECLARE C-INSPECTION CURSOR WITH HOLD FOR
009100         SELECT INSP_ID, CLAIM_ID, BOOKED_TS, COMPLETED_TS
009200                , INSP_ADDR, CREATED_TS
009300           FROM CLR.T_INSPECTION
009400          WHERE LAST_UPD_TS >= :WS-LAST-RUN-TS
009500          ORDER BY INSP_ID
009600          FOR FETCH ONLY
009700     END-EXEC.
009800*
009900* CONTROL REPORT LINES
010000 01  WS-RPT-HEAD-1.
010100     05  FILLER                  PIC X(1)   VALUE '1'.
010200     05  FILLER                  PIC X(10)  VALUE 'CLRAS090'.
010300     05  FILLER                  PIC X(40)  VALUE
010400             'DESK ASSESSMENT QUEUE BUILDER'.
010500     05  FILLER                  PIC X(10)  VALUE 'RUN DATE: '.
010600     05  RH1-RUN-DATE            PIC X(10).
010700     05  FILLER                  PIC X(62)  VALUE SPACES.
010800 01  WS-RPT-DETAIL.
010900     05  FILLER                  PIC X(1)   VALUE SPACE.
011000     05  RD-LABEL                PIC X(40).
011100     05  RD-VALUE                PIC X(60).
011200     05  FILLER                  PIC X(32)  VALUE SPACES.
011300 01  WS-RPT-TOTAL.
011400     05  FILLER                  PIC X(1)   VALUE SPACE.
011500     05  RT-LABEL                PIC X(40).
011600     05  RT-COUNT                PIC ZZZ,ZZZ,ZZ9.
011700     05  FILLER                  PIC X(81)  VALUE SPACES.
011800 PROCEDURE DIVISION.
011900* ---------------------------------------------------------------*
012000* 0000-MAINLINE                                                  *
012100* CONTROL FLOW                                                   *
012200* ---------------------------------------------------------------*
012300 0000-MAINLINE.
012400     PERFORM 1000-INITIALISE THRU 1000-INITIALISE-EXIT
012500     PERFORM 2000-PROCESS THRU 2000-PROCESS-EXIT
012600     PERFORM 9000-TERMINATE THRU 9000-TERMINATE-EXIT
012700     GOBACK.
012800 0000-MAINLINE-EXIT.
012900     EXIT.
013000* ---------------------------------------------------------------*
013100* 1000-INITIALISE                                                *
013200* INITIALISATION                                                 *
013300* ---------------------------------------------------------------*
013400 1000-INITIALISE.
013500     MOVE FUNCTION CURRENT-DATE(1:8) TO WS-RUN-TS
013600     STRING WS-RUN-TS(1:4) '-' WS-RUN-TS(5:2) '-' WS-RUN-TS(7:2)
013700         DELIMITED BY SIZE INTO WS-RUN-DATE
013800     MOVE 'CLRBATCH' TO WS-USER-ID
013900     OPEN OUTPUT REPORT-FILE
014000     IF WS-RPTOUT-STATUS NOT = '00'
014100         DISPLAY 'CLRAS090 OPEN FAILED RPTOUT ' WS-RPTOUT-STATUS
014200         MOVE 16 TO RETURN-CODE
014300         GOBACK
014400     END-IF
014500     MOVE WS-RUN-DATE TO RH1-RUN-DATE
014600     WRITE REPORT-RECORD FROM WS-RPT-HEAD-1
014700     PERFORM 1400-GET-BUSINESS-DATE THRU
014800         1400-GET-BUSINESS-DATE-EXIT
014900     .
015000 1000-INITIALISE-EXIT.
015100     EXIT.
015200* ---------------------------------------------------------------*
015300* 1400-GET-BUSINESS-DATE                                         *
015400* DETERMINE PROCESSING DATE                                      *
015500* ---------------------------------------------------------------*
015600 1400-GET-BUSINESS-DATE.
015700     MOVE WS-RUN-DATE TO DW-IN-DATE
015800     MOVE 'UK' TO DW-CALENDAR
015900     MOVE ZERO TO DW-BUS-DAYS
016000     CALL 'CLRCM010' USING CLR-DATE-WORK
016100                      CLR-ERROR-BLOCK
016200     IF ERR-SQLCODE NOT = ZERO
016300         MOVE 'CALL CLRCM010' TO ERR-PARA
016400         PERFORM 8000-SQL-ERROR
016500     END-IF
016600     .
016700 1400-GET-BUSINESS-DATE-EXIT.
016800     EXIT.
016900* ---------------------------------------------------------------*
017000* 2000-PROCESS                                                   *
017100* READ AND PROCESS ALL INPUT                                     *
017200* ---------------------------------------------------------------*
017300 2000-PROCESS.
017400     EXEC SQL
017500         OPEN C-INSPECTION
017600     END-EXEC
017700     EVALUATE SQLCODE
017800         WHEN 0
017900             CONTINUE
018000         WHEN OTHER
018100             MOVE '2000-OPEN-C-INSPECTION' TO ERR-PARA
018200             PERFORM 8000-SQL-ERROR
018300     END-EVALUATE
018400     PERFORM 2100-FETCH-NEXT THRU 2100-FETCH-NEXT-EXIT
018500     PERFORM 2200-PROCESS-ROW THRU 2200-PROCESS-ROW-EXIT
018600         UNTIL WS-END-OF-DATA
018700     EXEC SQL
018800         CLOSE C-INSPECTION
018900     END-EXEC
019000     .
019100 2000-PROCESS-EXIT.
019200     EXIT.
019300* ---------------------------------------------------------------*
019400* 2100-FETCH-NEXT                                                *
019500* FETCH THE NEXT DRIVING ROW                                     *
019600* ---------------------------------------------------------------*
019700 2100-FETCH-NEXT.
019800     EXEC SQL
019900         FETCH C-INSPECTION
020000          INTO :INS-INSP-ID, :INS-CLAIM-ID, :INS-BOOKED-TS
020100               , :INS-COMPLETED-TS, :INS-INSP-ADDR
020200               , :INS-CREATED-TS
020300     END-EXEC
020400     EVALUATE SQLCODE
020500         WHEN 0
020600             ADD 1 TO WS-INSPECTION-READ
020700         WHEN +100
020800             SET WS-END-OF-DATA TO TRUE
020900         WHEN OTHER
021000             MOVE '2100-FETCH-NEXT' TO ERR-PARA
021100             PERFORM 8000-SQL-ERROR
021200     END-EVALUATE
021300     .
021400 2100-FETCH-NEXT-EXIT.
021500     EXIT.
021600* ---------------------------------------------------------------*
021700* 2200-PROCESS-ROW                                               *
021800* PROCESS ONE ROW                                                *
021900* ---------------------------------------------------------------*
022000 2200-PROCESS-ROW.
022100     IF WS-END-OF-DATA
022200         GO TO 2200-PROCESS-ROW-EXIT
022300     END-IF
022400     SET WS-NO-ERROR TO TRUE
022500     PERFORM 2500-EDIT-INSPECTION THRU 2500-EDIT-INSPECTION-EXIT
022600     PERFORM 2510-EDIT-INSPECTION-2 THRU
022700         2510-EDIT-INSPECTION-2-EXIT
022800     .
022900 2200-PROCESS-ROW-EXIT.
023000     EXIT.
023100* ---------------------------------------------------------------*
023200* 2500-EDIT-INSPECTION                                           *
023300* FIELD EDITS FOR CLR.T_INSPECTION                               *
023400* ---------------------------------------------------------------*
023500 2500-EDIT-INSPECTION.
023600     IF INS-CLAIM-ID = SPACES OR LOW-VALUES
023700         ADD 1 TO WS-REJECT-CNT
023800         MOVE 'CLAIM_ID MISSING' TO ERR-TEXT
023900     END-IF
024000     .
024100 2500-EDIT-INSPECTION-EXIT.
024200     EXIT.
024300* ---------------------------------------------------------------*
024400* 2510-EDIT-INSPECTION-2                                         *
024500* VALIDATE CLR.T_INSPECTION                                      *
024600* ---------------------------------------------------------------*
024700 2510-EDIT-INSPECTION-2.
024800     IF INS-INSP-ADDR = SPACES OR LOW-VALUES
024900         ADD 1 TO WS-REJECT-CNT
025000         MOVE 'INSP_ADDR MISSING' TO ERR-TEXT
025100     END-IF
025200     .
025300 2510-EDIT-INSPECTION-2-EXIT.
025400     EXIT.
025500* ---------------------------------------------------------------*
025600* 9000-TERMINATE                                                 *
025700* CLOSE DOWN                                                     *
025800* ---------------------------------------------------------------*
025900 9000-TERMINATE.
026000     PERFORM 7010-LIST-INSPECTION THRU 7010-LIST-INSPECTION-EXIT
026100     MOVE 'CLR.T_INSPECTION ROWS READ' TO RT-LABEL
026200     MOVE WS-INSPECTION-READ TO RT-COUNT
026300     WRITE REPORT-RECORD FROM WS-RPT-TOTAL
026400     CLOSE REPORT-FILE
026500     IF WS-REJECT-CNT > ZERO
026600         MOVE 4 TO RETURN-CODE
026700     END-IF
026800     .
026900 9000-TERMINATE-EXIT.
027000     EXIT.
027100* ---------------------------------------------------------------*
027200* 7010-LIST-INSPECTION                                           *
027300* LIST CLR.T_INSPECTION FIELDS ON THE REPORT                     *
027400* ---------------------------------------------------------------*
027500 7010-LIST-INSPECTION.
027600     MOVE 'LAST CLR.T_INSPECTION ROW' TO RD-LABEL
027700     MOVE SPACES TO RD-VALUE
027800     WRITE REPORT-RECORD FROM WS-RPT-DETAIL
027900     MOVE '  CLAIM_ID' TO RD-LABEL
028000     MOVE INS-CLAIM-ID TO RD-VALUE
028100     WRITE REPORT-RECORD FROM WS-RPT-DETAIL
028200     MOVE '  BOOKED_TS' TO RD-LABEL
028300     MOVE INS-BOOKED-TS TO RD-VALUE
028400     WRITE REPORT-RECORD FROM WS-RPT-DETAIL
028500     MOVE '  COMPLETED_TS' TO RD-LABEL
028600     MOVE INS-COMPLETED-TS TO RD-VALUE
028700     WRITE REPORT-RECORD FROM WS-RPT-DETAIL
028800     MOVE '  INSP_ADDR' TO RD-LABEL
028900     MOVE INS-INSP-ADDR TO RD-VALUE
029000     WRITE REPORT-RECORD FROM WS-RPT-DETAIL
029100     MOVE '  CREATED_TS' TO RD-LABEL
029200     MOVE INS-CREATED-TS TO RD-VALUE
029300     WRITE REPORT-RECORD FROM WS-RPT-DETAIL
029400     .
029500 7010-LIST-INSPECTION-EXIT.
029600     EXIT.
029700* ---------------------------------------------------------------*
029800* 8000-SQL-ERROR                                                 *
029900* DB2 ERROR HANDLING                                             *
030000* ---------------------------------------------------------------*
030100 8000-SQL-ERROR.
030200     MOVE SQLCODE TO ERR-SQLCODE WS-SQLCODE-DSP
030300     MOVE WS-PGM-ID TO ERR-PGM
030400     STRING 'SQLCODE ' WS-SQLCODE-DSP DELIMITED BY SIZE INTO
030500         ERR-TEXT
030600     DISPLAY WS-PGM-ID ' ' ERR-PARA ' ' ERR-TEXT
030700     MOVE 16 TO RETURN-CODE
030800     CLOSE REPORT-FILE
030900     GOBACK.
031000 8000-SQL-ERROR-EXIT.
031100     EXIT.

000100* ===============================================================*
000200* PROGRAM    : CLRGL060                                          *
000300* TITLE      : GL RECONCILIATION REPORT                          *
000400* SYSTEM     : CLARA - CLAIMS LEDGER AND RESERVE APPLICATION     *
000500* AREA       : GL                                                *
000600* TYPE       : BATCH / DB2                                       *
000700* JOB / STEP : CLRMGL01 / STEP040                                *
000800* ---------------------------------------------------------------*
000900* PURPOSE                                                        *
001000*   BATCH DB2 PROGRAM - GL RECONCILIATION REPORT.                *
001100*   SCHEDULED UNDER JOB CLRMGL01 (STEP040).                      *
001200*   RETURN CODES: 0 OK, 4 WARNINGS, 16 SEVERE (SEE SYSOUT).      *
001300* ---------------------------------------------------------------*
001400* DB2 TABLES                                                     *
001500*   CLR.T_CURRENCY_RATE         READ                             *
001600* COPYBOOKS  : CURRATE1 CLRERR01 CLRDATE1                        *
001700* CALLS      : CLRCM010                                          *
001800* FILE       : RPTOUT   OUT CONTROL REPORT                       *
001900* ---------------------------------------------------------------*
002000* MAINTENANCE HISTORY                                            *
002100* DATE       BY       REF        DESCRIPTION                     *
002200* ---------- -------- ---------- ------------------------------- *
002300* 1994-10-03 CLRPROJ             INITIAL VERSION - CLARA GO-LIVE *
002400* 1998-07-04 KBARR01             Y2K: 4-DIGIT YEARS IN DATE WORK *
002500*                                AREAS                           *
002600* 1999-01-11 KBARR01             Y2K REMEDIATION - DATE          *
002700*                                WINDOWING REMOVED               *
002800* 2018-03-12 DO                  RECOMPILED UNDER ENTERPRISE     *
002900*                                COBOL V6                        *
003000* 2021-02-08 KBARR01             NORDIC CURRENCY CODES VALIDATED *
003100* ===============================================================*
003200 IDENTIFICATION DIVISION.
003300 PROGRAM-ID.    CLRGL060.
003400 AUTHOR.        CLARA PROJECT TEAM.
003500 INSTALLATION.  CORVANE MUTUAL - CLAIMS SYSTEMS.
003600 DATE-WRITTEN.  1994-10-03.
003700 DATE-COMPILED.
003800 ENVIRONMENT DIVISION.
003900 CONFIGURATION SECTION.
004000 SOURCE-COMPUTER.  IBM-Z.
004100 OBJECT-COMPUTER.  IBM-Z.
004200 INPUT-OUTPUT SECTION.
004300 FILE-CONTROL.
004400     SELECT REPORT-FILE ASSIGN TO RPTOUT
004500        ORGANIZATION IS SEQUENTIAL
004600        FILE STATUS IS WS-RPTOUT-STATUS.
004700 DATA DIVISION.
004800 FILE SECTION.
004900 FD  REPORT-FILE
005000        RECORDING MODE IS F
005100        BLOCK CONTAINS 0 RECORDS.
005200 01  REPORT-RECORD               PIC X(133).
005300 WORKING-STORAGE SECTION.
005400*
005500 01  WS-PROGRAM-INFO.
005600     05  WS-PGM-ID               PIC X(8)   VALUE 'CLRGL060'.
005700     05  WS-RUN-DATE             PIC X(10)  VALUE SPACES.
005800     05  WS-RUN-TS               PIC X(26)  VALUE SPACES.
005900     05  WS-USER-ID              PIC X(8)   VALUE SPACES.
006000     05  WS-LAST-RUN-TS          PIC X(26)  VALUE SPACES.
006100     05  WS-RUN-ID               PIC S9(9)  COMP VALUE ZERO.
006200     05  WS-RATE-DT              PIC X(10)  VALUE SPACES.
006300*
006400 01  WS-SWITCHES.
006500     05  WS-EOF-SW               PIC X      VALUE 'N'.
006600        88  WS-END-OF-DATA                     VALUE 'Y'.
006700     05  WS-ERROR-SW             PIC X      VALUE 'N'.
006800        88  WS-ERROR-FOUND                     VALUE 'Y'.
006900        88  WS-NO-ERROR                        VALUE 'N'.
007000     05  WS-FOUND-SW             PIC X      VALUE 'N'.
007100        88  WS-ROW-FOUND                       VALUE 'Y'.
007200        88  WS-ROW-NOT-FOUND                   VALUE 'N'.
007300     05  WS-RPTOUT-STATUS        PIC X(2)   VALUE SPACES.
007400*
007500 01  WS-COUNTERS.
007600     05  WS-CURRENCY-RATE-READ   PIC S9(9)  COMP-3 VALUE ZERO.
007700     05  WS-REJECT-CNT           PIC S9(9)  COMP-3 VALUE ZERO.
007800*
007900 01  WS-SQL-WORK.
008000     05  WS-SQLCODE-DSP          PIC -9(9).
008100     05  WS-ROWS-AFFECTED        PIC S9(9)  COMP VALUE ZERO.
008200     05  WS-IND-1                PIC S9(4)  COMP VALUE ZERO.
008300     05  WS-IND-2                PIC S9(4)  COMP VALUE ZERO.
008400     05  WS-NEW-ID               PIC S9(18) COMP VALUE ZERO.
008500*
008600     EXEC SQL INCLUDE SQLCA END-EXEC.
008700*
008800* COPYBOOKS (HOST STRUCTURES AND WORK AREAS)
008900 COPY CURRATE1.
009000 COPY CLRERR01.
009100 COPY CLRDATE1.
009200*
009300* CONTROL REPORT LINES
009400 01  WS-RPT-HEAD-1.
009500     05  FILLER                  PIC X(1)   VALUE '1'.
009600     05  FILLER                  PIC X(10)  VALUE 'CLRGL060'.
009700     05  FILLER                  PIC X(40)  VALUE
009800           'GL RECONCILIATION REPORT'.
009900     05  FILLER                  PIC X(10)  VALUE 'RUN DATE: '.
010000     05  RH1-RUN-DATE            PIC X(10).
010100     05  FILLER                  PIC X(62)  VALUE SPACES.
010200 01  WS-RPT-DETAIL.
010300     05  FILLER                  PIC X(1)   VALUE SPACE.
010400     05  RD-LABEL                PIC X(40).
010500     05  RD-VALUE                PIC X(60).
010600     05  FILLER                  PIC X(32)  VALUE SPACES.
010700 01  WS-RPT-TOTAL.
010800     05  FILLER                  PIC X(1)   VALUE SPACE.
010900     05  RT-LABEL                PIC X(40).
011000     05  RT-COUNT                PIC ZZZ,ZZZ,ZZ9.
011100     05  FILLER                  PIC X(81)  VALUE SPACES.
011200 PROCEDURE DIVISION.
011300* ---------------------------------------------------------------*
011400* 0000-MAINLINE                                                  *
011500* MAIN CONTROL                                                   *
011600* ---------------------------------------------------------------*
011700 0000-MAINLINE.
011800     PERFORM 1000-INITIALISE
011900     PERFORM 2000-PROCESS-RUN
012000     PERFORM 9000-TERMINATE
012100     GOBACK.
012200* ---------------------------------------------------------------*
012300* 1000-INITIALISE                                                *
012400* OPEN FILES AND SET UP THE RUN                                  *
012500* ---------------------------------------------------------------*
012600 1000-INITIALISE.
012700     MOVE FUNCTION CURRENT-DATE(1:8) TO WS-RUN-TS
012800     STRING WS-RUN-TS(1:4) '-' WS-RUN-TS(5:2) '-' WS-RUN-TS(7:2)
012900        DELIMITED BY SIZE INTO WS-RUN-DATE
013000     MOVE 'CLRBATCH' TO WS-USER-ID
013100     OPEN OUTPUT REPORT-FILE
013200     IF WS-RPTOUT-STATUS NOT = '00'
013300        DISPLAY 'CLRGL060 OPEN FAILED RPTOUT ' WS-RPTOUT-STATUS
013400        MOVE 16 TO RETURN-CODE
013500        GOBACK
013600     END-IF
013700     MOVE WS-RUN-DATE TO RH1-RUN-DATE
013800     WRITE REPORT-RECORD FROM WS-RPT-HEAD-1
013900     PERFORM 1400-GET-BUSINESS-DATE
014000     .
014100* ---------------------------------------------------------------*
014200* 1400-GET-BUSINESS-DATE                                         *
014300* DETERMINE PROCESSING DATE                                      *
014400* ---------------------------------------------------------------*
014500 1400-GET-BUSINESS-DATE.
014600     MOVE WS-RUN-DATE TO DW-IN-DATE
014700     MOVE 'UK' TO DW-CALENDAR
014800     MOVE ZERO TO DW-BUS-DAYS
014900     CALL 'CLRCM010' USING CLR-DATE-WORK
015000                      CLR-ERROR-BLOCK
015100     IF ERR-SQLCODE NOT = ZERO
015200        MOVE 'CALL CLRCM010' TO ERR-PARA
015300        PERFORM 8000-SQL-ERROR
015400     END-IF
015500     .
015600* ---------------------------------------------------------------*
015700* 2000-PROCESS-RUN                                               *
015800* SINGLE-PASS PROCESSING                                         *
015900* ---------------------------------------------------------------*
016000 2000-PROCESS-RUN.
016100     PERFORM 2300-READ-CURRENCY-RATE
016200     PERFORM 2500-EDIT-CURRENCY-RATE
016300     PERFORM 2510-EDIT-CURRENCY-RATE-2
016400     PERFORM 2520-EDIT-CURRENCY-RATE-3
016500     .
016600* ---------------------------------------------------------------*
016700* 2300-READ-CURRENCY-RATE                                        *
016800* LOOK UP CLR.T_CURRENCY_RATE                                    *
016900* ---------------------------------------------------------------*
017000 2300-READ-CURRENCY-RATE.
017100     MOVE WS-RUN-DATE TO CURR-RATE-DT
017200     SET WS-ROW-FOUND TO TRUE
017300     EXEC SQL
017400         SELECT CURRENCY_CD, RATE_DT, RATE_TO_GBP
017500                , RATE_TYPE_CD
017600           INTO :CURR-CURRENCY-CD, :CURR-RATE-DT
017700                , :CURR-RATE-TO-GBP, :CURR-RATE-TYPE-CD
017800           FROM CLR.T_CURRENCY_RATE
017900          WHERE CURRENCY_CD = :CURR-CURRENCY-CD
018000            AND RATE_DT = :CURR-RATE-DT
018100     END-EXEC
018200     EVALUATE SQLCODE
018300        WHEN 0
018400           ADD 1 TO WS-CURRENCY-RATE-READ
018500        WHEN +100
018600           SET WS-ROW-NOT-FOUND TO TRUE
018700        WHEN OTHER
018800           MOVE 'READ CLR.T_CURRENCY_RATE' TO ERR-PARA
018900           PERFORM 8000-SQL-ERROR
019000     END-EVALUATE
019100     .
019200* ---------------------------------------------------------------*
019300* 2500-EDIT-CURRENCY-RATE                                        *
019400* FIELD EDITS FOR CLR.T_CURRENCY_RATE                            *
019500* ---------------------------------------------------------------*
019600 2500-EDIT-CURRENCY-RATE.
019700     IF CURR-CURRENCY-CD = SPACES OR LOW-VALUES
019800        ADD 1 TO WS-REJECT-CNT
019900        MOVE 'CURRENCY_CD MISSING' TO ERR-TEXT
020000     END-IF
020100     IF CURR-RATE-DT NOT = SPACES AND CURR-RATE-DT(5:1) NOT = '-'
020200        MOVE 'RATE_DT BAD DATE' TO ERR-TEXT
020300        ADD 1 TO WS-REJECT-CNT
020400     END-IF
020500     IF CURR-RATE-TO-GBP NOT NUMERIC
020600        MOVE ZERO TO CURR-RATE-TO-GBP
020700        ADD 1 TO WS-REJECT-CNT
020800     END-IF
020900     .
021000* ---------------------------------------------------------------*
021100* 2510-EDIT-CURRENCY-RATE-2                                      *
021200* FIELD EDITS FOR CLR.T_CURRENCY_RATE                            *
021300* ---------------------------------------------------------------*
021400 2510-EDIT-CURRENCY-RATE-2.
021500     IF CURR-RATE-TYPE-CD NOT = 'DY' AND CURR-RATE-TYPE-CD NOT =
021600         'ME' AND CURR-RATE-TYPE-CD NOT = 'YE'
021700        ADD 1 TO WS-REJECT-CNT
021800        MOVE 'RATE_TYPE_CD INVALID' TO ERR-TEXT
021900     END-IF
022000     IF CURR-ARCHIVE-FLAG NOT = 'Y' AND CURR-ARCHIVE-FLAG NOT =
022100         'N'
022200        ADD 1 TO WS-REJECT-CNT
022300        MOVE 'ARCHIVE_FLAG INVALID' TO ERR-TEXT
022400     END-IF
022500     .
022600* ---------------------------------------------------------------*
022700* 2520-EDIT-CURRENCY-RATE-3                                      *
022800* FIELD EDITS FOR CLR.T_CURRENCY_RATE                            *
022900* ---------------------------------------------------------------*
023000 2520-EDIT-CURRENCY-RATE-3.
023100* ---------------------------------------------------------------*
023200* 9000-TERMINATE                                                 *
023300* TERMINATION AND TOTALS                                         *
023400* ---------------------------------------------------------------*
023500 9000-TERMINATE.
023600     PERFORM 7010-LIST-CURRENCY-RATE
023700     MOVE 'CLR.T_CURRENCY_RATE ROWS READ' TO RT-LABEL
023800     MOVE WS-CURRENCY-RATE-READ TO RT-COUNT
023900     WRITE REPORT-RECORD FROM WS-RPT-TOTAL
024000     CLOSE REPORT-FILE
024100     IF WS-REJECT-CNT > ZERO
024200        MOVE 4 TO RETURN-CODE
024300     END-IF
024400     .
024500* ---------------------------------------------------------------*
024600* 7010-LIST-CURRENCY-RATE                                        *
024700* LIST CLR.T_CURRENCY_RATE FIELDS ON THE REPORT                  *
024800* ---------------------------------------------------------------*
024900 7010-LIST-CURRENCY-RATE.
025000     MOVE 'LAST CLR.T_CURRENCY_RATE ROW' TO RD-LABEL
025100     MOVE SPACES TO RD-VALUE
025200     WRITE REPORT-RECORD FROM WS-RPT-DETAIL
025300     MOVE '  CURRENCY_CD' TO RD-LABEL
025400     MOVE CURR-CURRENCY-CD TO RD-VALUE
025500     WRITE REPORT-RECORD FROM WS-RPT-DETAIL
025600     MOVE '  RATE_DT' TO RD-LABEL
025700     MOVE CURR-RATE-DT TO RD-VALUE
025800     WRITE REPORT-RECORD FROM WS-RPT-DETAIL
025900     MOVE '  RATE_TYPE_CD' TO RD-LABEL
026000     MOVE CURR-RATE-TYPE-CD TO RD-VALUE
026100     WRITE REPORT-RECORD FROM WS-RPT-DETAIL
026200     MOVE '  ARCHIVE_FLAG' TO RD-LABEL
026300     MOVE CURR-ARCHIVE-FLAG TO RD-VALUE
026400     WRITE REPORT-RECORD FROM WS-RPT-DETAIL
026500     MOVE '  COMMENT_TXT' TO RD-LABEL
026600     MOVE CURR-COMMENT-TXT TO RD-VALUE
026700     WRITE REPORT-RECORD FROM WS-RPT-DETAIL
026800     MOVE '  CREATED_TS' TO RD-LABEL
026900     MOVE CURR-CREATED-TS TO RD-VALUE
027000     WRITE REPORT-RECORD FROM WS-RPT-DETAIL
027100     .
027200* ---------------------------------------------------------------*
027300* 8000-SQL-ERROR                                                 *
027400* SEVERE ERROR - REPORT AND STOP                                 *
027500* ---------------------------------------------------------------*
027600 8000-SQL-ERROR.
027700     MOVE SQLCODE TO ERR-SQLCODE WS-SQLCODE-DSP
027800     MOVE WS-PGM-ID TO ERR-PGM
027900     STRING 'SQLCODE ' WS-SQLCODE-DSP DELIMITED BY SIZE INTO
028000         ERR-TEXT
028100     DISPLAY WS-PGM-ID ' ' ERR-PARA ' ' ERR-TEXT
028200     MOVE 16 TO RETURN-CODE
028300     CLOSE REPORT-FILE
028400     GOBACK.

000100* ===============================================================*
000200* PROGRAM    : CLRFR130                                          *
000300* TITLE      : FRAUD MI WEEKLY                                   *
000400* SYSTEM     : CLARA - CLAIMS LEDGER AND RESERVE APPLICATION     *
000500* AREA       : FRAUD                                             *
000600* TYPE       : BATCH / DB2                                       *
000700* JOB / STEP : CLRWFR01 / STEP020                                *
000800* ---------------------------------------------------------------*
000900* PURPOSE                                                        *
001000*   NIGHTLY/PERIODIC BATCH STEP: FRAUD MI WEEKLY.                *
001100*   EXECUTED BY JOB CLRWFR01, STEP020.                           *
001200*   CONDITION CODES: 00 NORMAL / 04 WARNING / 16 FAILURE.        *
001300* ---------------------------------------------------------------*
001400* DB2 TABLES                                                     *
001500*   CLR.T_FRAUD_SCORE           READ                             *
001600* COPYBOOKS  : FRDSCR01 CLRERR01                                 *
001700* CALLS      : NONE                                              *
001800* FILE       : RPTOUT   OUT CONTROL REPORT                       *
001900* ---------------------------------------------------------------*
002000* MAINTENANCE HISTORY                                            *
002100* DATE       BY       REF        DESCRIPTION                     *
002200* ---------- -------- ---------- ------------------------------- *
002300* 1996-09-01 KBARR01             INITIAL VERSION                 *
002400* 1998-12-02 KBARR01             Y2K: 4-DIGIT YEARS IN DATE WORK *
002500*                                AREAS                           *
002600* 1999-08-20 KBARR01             Y2K REMEDIATION - DATE          *
002700*                                WINDOWING REMOVED               *
002800* 2002-05-23 KBARR01             SQLCODE HANDLING ROUTED THROUGH *
002900*                                CLRERR01                        *
003000* 2012-10-14 PASHW01             DATE ARITHMETIC MOVED TO        *
003100*                                CLRCM010                        *
003200* 2023-05-26 PASHW01             NORDIC CURRENCY CODES VALIDATED *
003300* ===============================================================*
003400 IDENTIFICATION DIVISION.
003500 PROGRAM-ID.    CLRFR130.
003600 AUTHOR.        K. BARRACLOUGH.
003700 INSTALLATION.  CORVANE MUTUAL - CLAIMS SYSTEMS.
003800 DATE-WRITTEN.  1996-09-01.
003900 DATE-COMPILED.
004000 ENVIRONMENT DIVISION.
004100 CONFIGURATION SECTION.
004200 SOURCE-COMPUTER.  IBM-Z.
004300 OBJECT-COMPUTER.  IBM-Z.
004400 INPUT-OUTPUT SECTION.
004500 FILE-CONTROL.
004600     SELECT REPORT-FILE ASSIGN TO RPTOUT
004700        ORGANIZATION IS SEQUENTIAL
004800        FILE STATUS IS WS-RPTOUT-STATUS.
004900 DATA DIVISION.
005000 FILE SECTION.
005100 FD  REPORT-FILE
005200        RECORDING MODE IS F
005300        BLOCK CONTAINS 0 RECORDS.
005400 01  REPORT-RECORD               PIC X(133).
005500 WORKING-STORAGE SECTION.
005600*
005700 01  WS-PROGRAM-INFO.
005800     05  WS-PGM-ID               PIC X(8)   VALUE 'CLRFR130'.
005900     05  WS-RUN-DATE             PIC X(10)  VALUE SPACES.
006000     05  WS-RUN-TS               PIC X(26)  VALUE SPACES.
006100     05  WS-USER-ID              PIC X(8)   VALUE SPACES.
006200     05  WS-LAST-RUN-TS          PIC X(26)  VALUE SPACES.
006300     05  WS-RUN-ID               PIC S9(9)  COMP VALUE ZERO.
006400*
006500 01  WS-SWITCHES.
006600     05  WS-EOF-SW               PIC X      VALUE 'N'.
006700        88  WS-END-OF-DATA                     VALUE 'Y'.
006800     05  WS-ERROR-SW             PIC X      VALUE 'N'.
006900        88  WS-ERROR-FOUND                     VALUE 'Y'.
007000        88  WS-NO-ERROR                        VALUE 'N'.
007100     05  WS-FOUND-SW             PIC X      VALUE 'N'.
007200        88  WS-ROW-FOUND                       VALUE 'Y'.
007300        88  WS-ROW-NOT-FOUND                   VALUE 'N'.
007400     05  WS-RPTOUT-STATUS        PIC X(2)   VALUE SPACES.
007500*
007600 01  WS-COUNTERS.
007700     05  WS-FRAUD-SCORE-READ     PIC S9(9)  COMP-3 VALUE ZERO.
007800     05  WS-REJECT-CNT           PIC S9(9)  COMP-3 VALUE ZERO.
007900*
008000 01  WS-SQL-WORK.
008100     05  WS-SQLCODE-DSP          PIC -9(9).
008200     05  WS-ROWS-AFFECTED        PIC S9(9)  COMP VALUE ZERO.
008300     05  WS-IND-1                PIC S9(4)  COMP VALUE ZERO.
008400     05  WS-IND-2                PIC S9(4)  COMP VALUE ZERO.
008500     05  WS-NEW-ID               PIC S9(18) COMP VALUE ZERO.
008600*
008700     EXEC SQL INCLUDE SQLCA END-EXEC.
008800*
008900* COPYBOOKS (HOST STRUCTURES AND WORK AREAS)
009000 COPY FRDSCR01.
009100 COPY CLRERR01.
009200*
009300* DRIVING CURSOR ON CLR.T_FRAUD_SCORE
009400     EXEC SQL
009500         DECLARE C-FRAUD-SCORE CURSOR WITH HOLD FOR
009600         SELECT CLAIM_ID, SCORE_TS, SCORE, MODEL_VERSION
009700                , TOP_REASON_1, TOP_REASON_2
009800           FROM CLR.T_FRAUD_SCORE
009900          WHERE SCORE_TS >= :WS-LAST-RUN-TS
010000          ORDER BY CLAIM_ID, SCORE_TS
010100          FOR FETCH ONLY
010200     END-EXEC.
010300*
010400* CONTROL REPORT LINES
010500 01  WS-RPT-HEAD-1.
010600     05  FILLER                  PIC X(1)   VALUE '1'.
010700     05  FILLER                  PIC X(10)  VALUE 'CLRFR130'.
010800     05  FILLER                  PIC X(40)  VALUE
010900           'FRAUD MI WEEKLY'.
011000     05  FILLER                  PIC X(10)  VALUE 'RUN DATE: '.
011100     05  RH1-RUN-DATE            PIC X(10).
011200     05  FILLER                  PIC X(62)  VALUE SPACES.
011300 01  WS-RPT-DETAIL.
011400     05  FILLER                  PIC X(1)   VALUE SPACE.
011500     05  RD-LABEL                PIC X(40).
011600     05  RD-VALUE                PIC X(60).
011700     05  FILLER                  PIC X(32)  VALUE SPACES.
011800 01  WS-RPT-TOTAL.
011900     05  FILLER                  PIC X(1)   VALUE SPACE.
012000     05  RT-LABEL                PIC X(40).
012100     05  RT-COUNT                PIC ZZZ,ZZZ,ZZ9.
012200     05  FILLER                  PIC X(81)  VALUE SPACES.
012300 PROCEDURE DIVISION.
012400* ---------------------------------------------------------------*
012500* 0000-MAINLINE                                                  *
012600* MAIN CONTROL                                                   *
012700* ---------------------------------------------------------------*
012800 0000-MAINLINE.
012900     PERFORM 1000-INITIALISE
013000     PERFORM 2000-PROCESS
013100     PERFORM 9000-TERMINATE
013200     GOBACK.
013300* ---------------------------------------------------------------*
013400* 1000-INITIALISE                                                *
013500* OPEN FILES AND SET UP THE RUN                                  *
013600* ---------------------------------------------------------------*
013700 1000-INITIALISE.
013800     MOVE FUNCTION CURRENT-DATE(1:8) TO WS-RUN-TS
013900     STRING WS-RUN-TS(1:4) '-' WS-RUN-TS(5:2) '-' WS-RUN-TS(7:2)
014000        DELIMITED BY SIZE INTO WS-RUN-DATE
014100     MOVE 'CLRBATCH' TO WS-USER-ID
014200     OPEN OUTPUT REPORT-FILE
014300     IF WS-RPTOUT-STATUS NOT = '00'
014400        DISPLAY 'CLRFR130 OPEN FAILED RPTOUT ' WS-RPTOUT-STATUS
014500        MOVE 16 TO RETURN-CODE
014600        GOBACK
014700     END-IF
014800     MOVE WS-RUN-DATE TO RH1-RUN-DATE
014900     WRITE REPORT-RECORD FROM WS-RPT-HEAD-1
015000     .
015100* ---------------------------------------------------------------*
015200* 2000-PROCESS                                                   *
015300* MAIN PROCESSING LOOP                                           *
015400* ---------------------------------------------------------------*
015500 2000-PROCESS.
015600     EXEC SQL
015700         OPEN C-FRAUD-SCORE
015800     END-EXEC
015900     EVALUATE SQLCODE
016000        WHEN 0
016100           CONTINUE
016200        WHEN OTHER
016300           MOVE '2000-OPEN-C-FRAUD-SCORE' TO ERR-PARA
016400           PERFORM 8000-SQL-ERROR
016500     END-EVALUATE
016600     PERFORM 2100-FETCH-NEXT
016700     PERFORM UNTIL WS-END-OF-DATA
016800        PERFORM 2200-PROCESS-ROW
016900        PERFORM 2100-FETCH-NEXT
017000     END-PERFORM
017100     EXEC SQL
017200         CLOSE C-FRAUD-SCORE
017300     END-EXEC
017400     .
017500* ---------------------------------------------------------------*
017600* 2100-FETCH-NEXT                                                *
017700* FETCH THE NEXT DRIVING ROW                                     *
017800* ---------------------------------------------------------------*
017900 2100-FETCH-NEXT.
018000     EXEC SQL
018100         FETCH C-FRAUD-SCORE
018200          INTO :FRDS-CLAIM-ID, :FRDS-SCORE-TS, :FRDS-SCORE
018300               , :FRDS-MODEL-VERSION, :FRDS-TOP-REASON-1
018400               , :FRDS-TOP-REASON-2
018500     END-EXEC
018600     EVALUATE SQLCODE
018700        WHEN 0
018800           ADD 1 TO WS-FRAUD-SCORE-READ
018900        WHEN +100
019000           SET WS-END-OF-DATA TO TRUE
019100        WHEN OTHER
019200           MOVE '2100-FETCH-NEXT' TO ERR-PARA
019300           PERFORM 8000-SQL-ERROR
019400     END-EVALUATE
019500     .
019600* ---------------------------------------------------------------*
019700* 2200-PROCESS-ROW                                               *
019800* PER-RECORD PROCESSING                                          *
019900* ---------------------------------------------------------------*
020000 2200-PROCESS-ROW.
020100     SET WS-NO-ERROR TO TRUE
020200     PERFORM 2500-EDIT-FRAUD-SCORE
020300     PERFORM 2510-EDIT-FRAUD-SCORE-2
020400     PERFORM 2520-EDIT-FRAUD-SCORE-3
020500     .
020600* ---------------------------------------------------------------*
020700* 2500-EDIT-FRAUD-SCORE                                          *
020800* CHECK MANDATORY FIELDS IN CLR.T_FRAUD_SCORE                    *
020900* ---------------------------------------------------------------*
021000 2500-EDIT-FRAUD-SCORE.
021100     IF FRDS-CLAIM-ID = SPACES OR LOW-VALUES
021200        ADD 1 TO WS-REJECT-CNT
021300        MOVE 'CLAIM_ID MISSING' TO ERR-TEXT
021400     END-IF
021500     IF FRDS-SCORE NOT NUMERIC
021600        MOVE ZERO TO FRDS-SCORE
021700        ADD 1 TO WS-REJECT-CNT
021800     END-IF
021900     .
022000* ---------------------------------------------------------------*
022100* 2510-EDIT-FRAUD-SCORE-2                                        *
022200* FIELD EDITS FOR CLR.T_FRAUD_SCORE                              *
022300* ---------------------------------------------------------------*
022400 2510-EDIT-FRAUD-SCORE-2.
022500     IF FRDS-MODEL-VERSION = SPACES OR LOW-VALUES
022600        ADD 1 TO WS-REJECT-CNT
022700        MOVE 'MODEL_VERSION MISSING' TO ERR-TEXT
022800     END-IF
022900     IF FRDS-TOP-REASON-1 = SPACES OR LOW-VALUES
023000        ADD 1 TO WS-REJECT-CNT
023100        MOVE 'TOP_REASON_1 MISSING' TO ERR-TEXT
023200     END-IF
023300     .
023400* ---------------------------------------------------------------*
023500* 2520-EDIT-FRAUD-SCORE-3                                        *
023600* CHECK MANDATORY FIELDS IN CLR.T_FRAUD_SCORE                    *
023700* ---------------------------------------------------------------*
023800 2520-EDIT-FRAUD-SCORE-3.
023900* ---------------------------------------------------------------*
024000* 9000-TERMINATE                                                 *
024100* TERMINATION AND TOTALS                                         *
024200* ---------------------------------------------------------------*
024300 9000-TERMINATE.
024400     PERFORM 7010-LIST-FRAUD-SCORE
024500     MOVE 'CLR.T_FRAUD_SCORE ROWS READ' TO RT-LABEL
024600     MOVE WS-FRAUD-SCORE-READ TO RT-COUNT
024700     WRITE REPORT-RECORD FROM WS-RPT-TOTAL
024800     CLOSE REPORT-FILE
024900     IF WS-REJECT-CNT > ZERO
025000        MOVE 4 TO RETURN-CODE
025100     END-IF
025200     .
025300* ---------------------------------------------------------------*
025400* 7010-LIST-FRAUD-SCORE                                          *
025500* LIST CLR.T_FRAUD_SCORE FIELDS ON THE REPORT                    *
025600* ---------------------------------------------------------------*
025700 7010-LIST-FRAUD-SCORE.
025800     MOVE 'LAST CLR.T_FRAUD_SCORE ROW' TO RD-LABEL
025900     MOVE SPACES TO RD-VALUE
026000     WRITE REPORT-RECORD FROM WS-RPT-DETAIL
026100     MOVE '  CLAIM_ID' TO RD-LABEL
026200     MOVE FRDS-CLAIM-ID TO RD-VALUE
026300     WRITE REPORT-RECORD FROM WS-RPT-DETAIL
026400     MOVE '  SCORE_TS' TO RD-LABEL
026500     MOVE FRDS-SCORE-TS TO RD-VALUE
026600     WRITE REPORT-RECORD FROM WS-RPT-DETAIL
026700     MOVE '  MODEL_VERSION' TO RD-LABEL
026800     MOVE FRDS-MODEL-VERSION TO RD-VALUE
026900     WRITE REPORT-RECORD FROM WS-RPT-DETAIL
027000     MOVE '  TOP_REASON_1' TO RD-LABEL
027100     MOVE FRDS-TOP-REASON-1 TO RD-VALUE
027200     WRITE REPORT-RECORD FROM WS-RPT-DETAIL
027300     MOVE '  TOP_REASON_2' TO RD-LABEL
027400     MOVE FRDS-TOP-REASON-2 TO RD-VALUE
027500     WRITE REPORT-RECORD FROM WS-RPT-DETAIL
027600     MOVE '  SOURCE_SYS_CD' TO RD-LABEL
027700     MOVE FRDS-SOURCE-SYS-CD TO RD-VALUE
027800     WRITE REPORT-RECORD FROM WS-RPT-DETAIL
027900     .
028000* ---------------------------------------------------------------*
028100* 8000-SQL-ERROR                                                 *
028200* UNEXPECTED SQLCODE                                             *
028300* ---------------------------------------------------------------*
028400 8000-SQL-ERROR.
028500     MOVE SQLCODE TO ERR-SQLCODE WS-SQLCODE-DSP
028600     MOVE WS-PGM-ID TO ERR-PGM
028700     STRING 'SQLCODE ' WS-SQLCODE-DSP DELIMITED BY SIZE INTO
028800         ERR-TEXT
028900     DISPLAY WS-PGM-ID ' ' ERR-PARA ' ' ERR-TEXT
029000     MOVE 16 TO RETURN-CODE
029100     CLOSE REPORT-FILE
029200     GOBACK.

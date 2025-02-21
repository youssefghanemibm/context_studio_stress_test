000100* ===============================================================*
000200* PROGRAM    : CLRCM040                                          *
000300* TITLE      : PARAMETER READER (READS CLR.T_PARAM WITH VALIDITY *
000400*              DATES)                                            *
000500* SYSTEM     : CLARA - CLAIMS LEDGER AND RESERVE APPLICATION     *
000600* AREA       : COMMON                                            *
000700* TYPE       : CALLED SUBPROGRAM (STATIC CALL, NO CICS COMMANDS) *
000800* ---------------------------------------------------------------*
000900* PURPOSE                                                        *
001000*   COMMON ROUTINE: PARAMETER READER (READS CLR.T_PARAM WITH     *
001100*     VALIDITY DATES).                                           *
001200*   NO CICS COMMANDS - CALLABLE FROM BATCH.                      *
001300*   RETURNS ERR-SQLCODE = 0 WHEN SUCCESSFUL.                     *
001400* ---------------------------------------------------------------*
001500* DB2 TABLES                                                     *
001600*   CLR.T_PARAM                 READ                             *
001700* COPYBOOKS  : PARMREC1 CLRERR01                                 *
001800* CALLS      : NONE                                              *
001900* ---------------------------------------------------------------*
002000* MAINTENANCE HISTORY                                            *
002100* DATE       BY       REF        DESCRIPTION                     *
002200* ---------- -------- ---------- ------------------------------- *
002300* 2013-11-01 DO                  INITIAL VERSION                 *
002400* 2022-09-15 DO                  NORDIC CURRENCY CODES VALIDATED *
002500* ===============================================================*
002600 IDENTIFICATION DIVISION.
002700 PROGRAM-ID.    CLRCM040.
002800 AUTHOR.        D. OLLERTON.
002900 INSTALLATION.  CORVANE MUTUAL - CLAIMS SYSTEMS.
003000 DATE-WRITTEN.  2013-11-01.
003100 DATE-COMPILED.
003200 ENVIRONMENT DIVISION.
003300 CONFIGURATION SECTION.
003400 SOURCE-COMPUTER.  IBM-Z.
003500 OBJECT-COMPUTER.  IBM-Z.
003600 DATA DIVISION.
003700 WORKING-STORAGE SECTION.
003800*
003900 01  WS-PROGRAM-INFO.
004000     05  WS-PGM-ID               PIC X(8)   VALUE 'CLRCM040'.
004100     05  WS-RUN-DATE             PIC X(10)  VALUE SPACES.
004200     05  WS-RUN-TS               PIC X(26)  VALUE SPACES.
004300     05  WS-USER-ID              PIC X(8)   VALUE SPACES.
004400*
004500 01  WS-SWITCHES.
004600     05  WS-EOF-SW               PIC X      VALUE 'N'.
004700        88  WS-END-OF-DATA                     VALUE 'Y'.
004800     05  WS-ERROR-SW             PIC X      VALUE 'N'.
004900        88  WS-ERROR-FOUND                     VALUE 'Y'.
005000        88  WS-NO-ERROR                        VALUE 'N'.
005100     05  WS-FOUND-SW             PIC X      VALUE 'N'.
005200        88  WS-ROW-FOUND                       VALUE 'Y'.
005300        88  WS-ROW-NOT-FOUND                   VALUE 'N'.
005400*
005500 01  WS-COUNTERS.
005600     05  WS-PARAM-READ           PIC S9(9)  COMP-3 VALUE ZERO.
005700     05  WS-REJECT-CNT           PIC S9(9)  COMP-3 VALUE ZERO.
005800*
005900 01  WS-SQL-WORK.
006000     05  WS-SQLCODE-DSP          PIC -9(9).
006100     05  WS-ROWS-AFFECTED        PIC S9(9)  COMP VALUE ZERO.
006200     05  WS-IND-1                PIC S9(4)  COMP VALUE ZERO.
006300     05  WS-IND-2                PIC S9(4)  COMP VALUE ZERO.
006400     05  WS-NEW-ID               PIC S9(18) COMP VALUE ZERO.
006500*
006600     EXEC SQL INCLUDE SQLCA END-EXEC.
006700*
006800* COPYBOOKS (HOST STRUCTURES AND WORK AREAS)
006900 COPY PARMREC1.
007000 COPY CLRERR01.
007100 LINKAGE SECTION.
007200 01  LS-PARM-REC.
007300     05  LS-PARAM-KEY            PIC X(20).
007400     05  LS-VALID-FROM           PIC X(10).
007500     05  LS-VALID-TO             PIC X(10).
007600     05  LS-PARAM-VALUE          PIC X(40).
007700     05  LS-PARAM-DESC           PIC X(120).
007800     05  LS-CHANGE-TICKET        PIC X(10).
007900     05  LS-CHANGED-BY           PIC X(8).
008000 01  LS-ERROR-BLOCK              PIC X(162).
008100 PROCEDURE DIVISION USING LS-PARM-REC LS-ERROR-BLOCK.
008200* ---------------------------------------------------------------*
008300* 0000-MAIN                                                      *
008400* ENTRY                                                          *
008500* ---------------------------------------------------------------*
008600 0000-MAIN.
008700     INITIALIZE CLR-ERROR-BLOCK
008800     MOVE 'CLRCM040' TO ERR-PGM
008900     MOVE LS-PARM-REC TO PARMREC1-REC
009000     PERFORM 2500-EDIT-PARAM
009100     PERFORM 2510-EDIT-PARAM-2
009200     PERFORM 2520-EDIT-PARAM-3
009300     PERFORM 2000-READ-PARAMETER
009400     PERFORM 9000-RETURN
009500     .
009600* ---------------------------------------------------------------*
009700* 2500-EDIT-PARAM                                                *
009800* CHECK MANDATORY FIELDS IN CLR.T_PARAM                          *
009900* ---------------------------------------------------------------*
010000 2500-EDIT-PARAM.
010100     IF PARM-PARAM-KEY = SPACES OR LOW-VALUES
010200        ADD 1 TO WS-REJECT-CNT
010300        MOVE 'PARAM_KEY MISSING' TO ERR-TEXT
010400     END-IF
010500     IF PARM-VALID-FROM NOT = SPACES AND PARM-VALID-FROM(5:1) NOT
010600         = '-'
010700        MOVE 'VALID_FROM BAD DATE' TO ERR-TEXT
010800        ADD 1 TO WS-REJECT-CNT
010900     END-IF
011000     IF PARM-VALID-TO NOT = SPACES AND PARM-VALID-TO(5:1) NOT =
011100         '-'
011200        MOVE 'VALID_TO BAD DATE' TO ERR-TEXT
011300        ADD 1 TO WS-REJECT-CNT
011400     END-IF
011500     .
011600* ---------------------------------------------------------------*
011700* 2510-EDIT-PARAM-2                                              *
011800* VALIDATE CLR.T_PARAM                                           *
011900* ---------------------------------------------------------------*
012000 2510-EDIT-PARAM-2.
012100     IF PARM-PARAM-VALUE = SPACES OR LOW-VALUES
012200        ADD 1 TO WS-REJECT-CNT
012300        MOVE 'PARAM_VALUE MISSING' TO ERR-TEXT
012400     END-IF
012500     IF PARM-PARAM-DESC = SPACES OR LOW-VALUES
012600        ADD 1 TO WS-REJECT-CNT
012700        MOVE 'PARAM_DESC MISSING' TO ERR-TEXT
012800     END-IF
012900     .
013000* ---------------------------------------------------------------*
013100* 2520-EDIT-PARAM-3                                              *
013200* VALIDATE CLR.T_PARAM                                           *
013300* ---------------------------------------------------------------*
013400 2520-EDIT-PARAM-3.
013500     IF PARM-CHANGED-BY = SPACES OR LOW-VALUES
013600        ADD 1 TO WS-REJECT-CNT
013700        MOVE 'CHANGED_BY MISSING' TO ERR-TEXT
013800     END-IF
013900     .
014000* ---------------------------------------------------------------*
014100* 2000-READ-PARAMETER                                            *
014200* READ ONE PARAMETER                                             *
014300* ---------------------------------------------------------------*
014400 2000-READ-PARAMETER.
014500* RETURN THE ROW VALID ON THE CURRENT DATE (VALID_FROM <= TODAY
014600*   AND
014700* VALID_TO NULL OR >= TODAY). NOT FOUND IS RETURNED AS SQLCODE
014800*   +100.
014900     EXEC SQL
015000         SELECT PARAM_VALUE, VALID_FROM, VALID_TO, PARAM_DESC,
015100                CHANGE_TICKET
015200           INTO :PARM-PARAM-VALUE, :PARM-VALID-FROM,
015300                :PARM-VALID-TO :WS-IND-1, :PARM-PARAM-DESC,
015400                :PARM-CHANGE-TICKET :WS-IND-2
015500           FROM CLR.T_PARAM
015600          WHERE PARAM_KEY = :PARM-PARAM-KEY
015700            AND VALID_FROM <= CURRENT DATE
015800            AND (VALID_TO IS NULL OR VALID_TO >= CURRENT DATE)
015900     END-EXEC
016000     MOVE SQLCODE TO ERR-SQLCODE
016100     IF SQLCODE NOT = 0
016200        MOVE SPACES TO PARM-PARAM-VALUE
016300     END-IF
016400     .
016500* ---------------------------------------------------------------*
016600* 9000-RETURN                                                    *
016700* COPY RESULTS BACK TO THE CALLER                                *
016800* ---------------------------------------------------------------*
016900 9000-RETURN.
017000     MOVE CLR-ERROR-BLOCK TO LS-ERROR-BLOCK
017100     MOVE PARMREC1-REC TO LS-PARM-REC
017200     GOBACK.
017300* ---------------------------------------------------------------*
017400* 8000-SQL-ERROR                                                 *
017500* UNEXPECTED SQLCODE                                             *
017600* ---------------------------------------------------------------*
017700 8000-SQL-ERROR.
017800     MOVE SQLCODE TO ERR-SQLCODE WS-SQLCODE-DSP
017900     MOVE WS-PGM-ID TO ERR-PGM
018000     STRING 'SQLCODE ' WS-SQLCODE-DSP DELIMITED BY SIZE INTO
018100         ERR-TEXT
018200     DISPLAY WS-PGM-ID ' ' ERR-PARA ' ' ERR-TEXT
018300     GO TO 9000-RETURN.

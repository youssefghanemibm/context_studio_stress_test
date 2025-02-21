000100* ===============================================================*
000200* PROGRAM    : CLRCM070                                          *
000300* TITLE      : USER AUTHORITY CHECK                              *
000400* SYSTEM     : CLARA - CLAIMS LEDGER AND RESERVE APPLICATION     *
000500* AREA       : COMMON                                            *
000600* TYPE       : CALLED SUBPROGRAM (STATIC CALL, NO CICS COMMANDS) *
000700* ---------------------------------------------------------------*
000800* PURPOSE                                                        *
000900*   SHARED SUBPROGRAM - USER AUTHORITY CHECK.                    *
001000*   SAFE FOR BOTH BATCH AND CICS CALLERS.                        *
001100*   RETURNS ERR-SQLCODE = 0 WHEN SUCCESSFUL.                     *
001200* ---------------------------------------------------------------*
001300* DB2 TABLES                                                     *
001400*   CLR.T_USER                  READ                             *
001500* COPYBOOKS  : USRREC01 CLRERR01                                 *
001600* CALLS      : NONE                                              *
001700* ---------------------------------------------------------------*
001800* MAINTENANCE HISTORY                                            *
001900* DATE       BY       REF        DESCRIPTION                     *
002000* ---------- -------- ---------- ------------------------------- *
002100* 1994-10-03 CLRPROJ             INITIAL VERSION - CLARA GO-LIVE *
002200* 1999-04-21 KBARR01             Y2K REMEDIATION - DATE          *
002300*                                WINDOWING REMOVED               *
002400* ===============================================================*
002500 IDENTIFICATION DIVISION.
002600 PROGRAM-ID.    CLRCM070.
002700 AUTHOR.        CLARA PROJECT TEAM.
002800 INSTALLATION.  CORVANE MUTUAL - CLAIMS SYSTEMS.
002900 DATE-WRITTEN.  1994-10-03.
003000 DATE-COMPILED.
003100 ENVIRONMENT DIVISION.
003200 CONFIGURATION SECTION.
003300 SOURCE-COMPUTER.  IBM-Z.
003400 OBJECT-COMPUTER.  IBM-Z.
003500 DATA DIVISION.
003600 WORKING-STORAGE SECTION.
003700*
003800 01  WS-PROGRAM-INFO.
003900     05  WS-PGM-ID               PIC X(8)   VALUE 'CLRCM070'.
004000     05  WS-RUN-DATE             PIC X(10)  VALUE SPACES.
004100     05  WS-RUN-TS               PIC X(26)  VALUE SPACES.
004200     05  WS-USER-ID              PIC X(8)   VALUE SPACES.
004300*
004400 01  WS-SWITCHES.
004500     05  WS-EOF-SW               PIC X      VALUE 'N'.
004600        88  WS-END-OF-DATA                     VALUE 'Y'.
004700     05  WS-ERROR-SW             PIC X      VALUE 'N'.
004800        88  WS-ERROR-FOUND                     VALUE 'Y'.
004900        88  WS-NO-ERROR                        VALUE 'N'.
005000     05  WS-FOUND-SW             PIC X      VALUE 'N'.
005100        88  WS-ROW-FOUND                       VALUE 'Y'.
005200        88  WS-ROW-NOT-FOUND                   VALUE 'N'.
005300*
005400 01  WS-COUNTERS.
005500     05  WS-USER-READ            PIC S9(9)  COMP-3 VALUE ZERO.
005600     05  WS-REJECT-CNT           PIC S9(9)  COMP-3 VALUE ZERO.
005700*
005800 01  WS-SQL-WORK.
005900     05  WS-SQLCODE-DSP          PIC -9(9).
006000     05  WS-ROWS-AFFECTED        PIC S9(9)  COMP VALUE ZERO.
006100     05  WS-IND-1                PIC S9(4)  COMP VALUE ZERO.
006200     05  WS-IND-2                PIC S9(4)  COMP VALUE ZERO.
006300     05  WS-NEW-ID               PIC S9(18) COMP VALUE ZERO.
006400*
006500     EXEC SQL INCLUDE SQLCA END-EXEC.
006600*
006700* CLARA RECORD LAYOUTS
006800 COPY USRREC01.
006900 COPY CLRERR01.
007000 LINKAGE SECTION.
007100 01  LS-AUTH-PARMS.
007200     05  LS-AUTH-USER            PIC X(8).
007300     05  LS-AUTH-FUNCTION        PIC X(8).
007400     05  LS-AUTH-ALLOWED         PIC X(1).
007500 01  LS-ERROR-BLOCK              PIC X(162).
007600 PROCEDURE DIVISION USING LS-AUTH-PARMS LS-ERROR-BLOCK.
007700* ---------------------------------------------------------------*
007800* 0000-MAIN                                                      *
007900* ENTRY                                                          *
008000* ---------------------------------------------------------------*
008100 0000-MAIN.
008200     INITIALIZE CLR-ERROR-BLOCK
008300     MOVE 'CLRCM070' TO ERR-PGM
008400     PERFORM 2300-READ-USER
008500     PERFORM 2500-EDIT-USER
008600     PERFORM 2510-EDIT-USER-2
008700     PERFORM 9000-RETURN
008800     .
008900* ---------------------------------------------------------------*
009000* 2300-READ-USER                                                 *
009100* LOOK UP CLR.T_USER                                             *
009200* ---------------------------------------------------------------*
009300 2300-READ-USER.
009400     MOVE WS-USER-ID TO USRR-USER-ID
009500     SET WS-ROW-FOUND TO TRUE
009600     EXEC SQL
009700         SELECT USER_ID, USER_NAME, TEAM_CD
009800           INTO :USRR-USER-ID, :USRR-USER-NAME, :USRR-TEAM-CD
009900           FROM CLR.T_USER
010000          WHERE USER_ID = :USRR-USER-ID
010100     END-EXEC
010200     EVALUATE SQLCODE
010300        WHEN 0
010400           ADD 1 TO WS-USER-READ
010500        WHEN +100
010600           SET WS-ROW-NOT-FOUND TO TRUE
010700        WHEN OTHER
010800           MOVE 'READ CLR.T_USER' TO ERR-PARA
010900           PERFORM 8000-SQL-ERROR
011000     END-EVALUATE
011100     .
011200* ---------------------------------------------------------------*
011300* 2500-EDIT-USER                                                 *
011400* CHECK MANDATORY FIELDS IN CLR.T_USER                           *
011500* ---------------------------------------------------------------*
011600 2500-EDIT-USER.
011700     IF USRR-USER-ID = SPACES OR LOW-VALUES
011800        ADD 1 TO WS-REJECT-CNT
011900        MOVE 'USER_ID MISSING' TO ERR-TEXT
012000     END-IF
012100     IF USRR-USER-NAME = SPACES OR LOW-VALUES
012200        ADD 1 TO WS-REJECT-CNT
012300        MOVE 'USER_NAME MISSING' TO ERR-TEXT
012400     END-IF
012500     IF USRR-TEAM-CD = SPACES OR LOW-VALUES
012600        ADD 1 TO WS-REJECT-CNT
012700        MOVE 'TEAM_CD MISSING' TO ERR-TEXT
012800     END-IF
012900     .
013000* ---------------------------------------------------------------*
013100* 2510-EDIT-USER-2                                               *
013200* CHECK MANDATORY FIELDS IN CLR.T_USER                           *
013300* ---------------------------------------------------------------*
013400 2510-EDIT-USER-2.
013500     IF USRR-RSV-AUTH-LEVEL = SPACES OR LOW-VALUES
013600        ADD 1 TO WS-REJECT-CNT
013700        MOVE 'RSV_AUTH_LEVEL MISSING' TO ERR-TEXT
013800     END-IF
013900     IF USRR-PAY-AUTH-LEVEL = SPACES OR LOW-VALUES
014000        ADD 1 TO WS-REJECT-CNT
014100        MOVE 'PAY_AUTH_LEVEL MISSING' TO ERR-TEXT
014200     END-IF
014300     IF USRR-ACTIVE-FLAG = SPACES OR LOW-VALUES
014400        ADD 1 TO WS-REJECT-CNT
014500        MOVE 'ACTIVE_FLAG MISSING' TO ERR-TEXT
014600     END-IF
014700     .
014800* ---------------------------------------------------------------*
014900* 9000-RETURN                                                    *
015000* COPY RESULTS BACK TO THE CALLER                                *
015100* ---------------------------------------------------------------*
015200 9000-RETURN.
015300     MOVE CLR-ERROR-BLOCK TO LS-ERROR-BLOCK
015400     GOBACK.
015500* ---------------------------------------------------------------*
015600* 8000-SQL-ERROR                                                 *
015700* UNEXPECTED SQLCODE                                             *
015800* ---------------------------------------------------------------*
015900 8000-SQL-ERROR.
016000     MOVE SQLCODE TO ERR-SQLCODE WS-SQLCODE-DSP
016100     MOVE WS-PGM-ID TO ERR-PGM
016200     STRING 'SQLCODE ' WS-SQLCODE-DSP DELIMITED BY SIZE INTO
016300         ERR-TEXT
016400     DISPLAY WS-PGM-ID ' ' ERR-PARA ' ' ERR-TEXT
016500     GO TO 9000-RETURN.

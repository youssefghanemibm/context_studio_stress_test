000100* ===============================================================*
000200* PROGRAM    : CLRCM010                                          *
000300* TITLE      : DATE AND BUSINESS-DAY UTILITY (UK, NO, SE, DK     *
000400*              CALENDARS)                                        *
000500* SYSTEM     : CLARA - CLAIMS LEDGER AND RESERVE APPLICATION     *
000600* AREA       : COMMON                                            *
000700* TYPE       : CALLED SUBPROGRAM (STATIC CALL, NO CICS COMMANDS) *
000800* ---------------------------------------------------------------*
000900* PURPOSE                                                        *
001000*   UTILITY MODULE: DATE AND BUSINESS-DAY UTILITY (UK, NO, SE,   *
001100*     DK CALENDARS).                                             *
001200*   SAFE FOR BOTH BATCH AND CICS CALLERS.                        *
001300*   NON-ZERO ERR-SQLCODE MEANS THE REQUEST FAILED.               *
001400* ---------------------------------------------------------------*
001500* DB2 TABLES                                                     *
001600*   CLR.T_CODE_LOOKUP           READ                             *
001700*   CLR.T_USER                  READ                             *
001800* COPYBOOKS  : CODELKP1 USRREC01 CLRERR01 CLRDATE1               *
001900* CALLS      : NONE                                              *
002000* ---------------------------------------------------------------*
002100* MAINTENANCE HISTORY                                            *
002200* DATE       BY       REF        DESCRIPTION                     *
002300* ---------- -------- ---------- ------------------------------- *
002400* 2009-02-01 DO                  INITIAL VERSION                 *
002500* 2010-05-22 DO                  DB2 VERSION MIGRATION - REBIND, *
002600*                                NO LOGIC CHANGE                 *
002700* 2011-05-27 DO                  COMMIT FREQUENCY TUNED FOR      *
002800*                                BATCH WINDOW                    *
002900* 2021-06-16 DO                  REMOVED DEAD CODE AFTER REVIEW  *
003000* ===============================================================*
003100 IDENTIFICATION DIVISION.
003200 PROGRAM-ID.    CLRCM010.
003300 AUTHOR.        D. OLLERTON.
003400 INSTALLATION.  CORVANE MUTUAL - CLAIMS SYSTEMS.
003500 DATE-WRITTEN.  2009-02-01.
003600 DATE-COMPILED.
003700 ENVIRONMENT DIVISION.
003800 CONFIGURATION SECTION.
003900 SOURCE-COMPUTER.  IBM-Z.
004000 OBJECT-COMPUTER.  IBM-Z.
004100 DATA DIVISION.
004200 WORKING-STORAGE SECTION.
004300*
004400 01  WS-PROGRAM-INFO.
004500     05  WS-PGM-ID               PIC X(8)   VALUE 'CLRCM010'.
004600     05  WS-RUN-DATE             PIC X(10)  VALUE SPACES.
004700     05  WS-RUN-TS               PIC X(26)  VALUE SPACES.
004800     05  WS-USER-ID              PIC X(8)   VALUE SPACES.
004900*
005000 01  WS-SWITCHES.
005100     05  WS-EOF-SW               PIC X      VALUE 'N'.
005200         88  WS-END-OF-DATA                     VALUE 'Y'.
005300     05  WS-ERROR-SW             PIC X      VALUE 'N'.
005400         88  WS-ERROR-FOUND                     VALUE 'Y'.
005500         88  WS-NO-ERROR                        VALUE 'N'.
005600     05  WS-FOUND-SW             PIC X      VALUE 'N'.
005700         88  WS-ROW-FOUND                       VALUE 'Y'.
005800         88  WS-ROW-NOT-FOUND                   VALUE 'N'.
005900*
006000 01  WS-COUNTERS.
006100     05  WS-CODE-LOOKUP-READ     PIC S9(9)  COMP-3 VALUE ZERO.
006200     05  WS-USER-READ            PIC S9(9)  COMP-3 VALUE ZERO.
006300     05  WS-REJECT-CNT           PIC S9(9)  COMP-3 VALUE ZERO.
006400*
006500 01  WS-SQL-WORK.
006600     05  WS-SQLCODE-DSP          PIC -9(9).
006700     05  WS-ROWS-AFFECTED        PIC S9(9)  COMP VALUE ZERO.
006800     05  WS-IND-1                PIC S9(4)  COMP VALUE ZERO.
006900     05  WS-IND-2                PIC S9(4)  COMP VALUE ZERO.
007000     05  WS-NEW-ID               PIC S9(18) COMP VALUE ZERO.
007100*
007200     EXEC SQL INCLUDE SQLCA END-EXEC.
007300*
007400* CLARA RECORD LAYOUTS
007500 COPY CODELKP1.
007600 COPY USRREC01.
007700 COPY CLRERR01.
007800 COPY CLRDATE1.
007900 LINKAGE SECTION.
008000 01  LS-DATE-WORK.
008100     05  LS-IN-DATE              PIC X(10).
008200     05  LS-CALENDAR             PIC X(2).
008300     05  LS-BUS-DAYS             PIC S9(4) COMP.
008400     05  LS-OUT-DATE             PIC X(10).
008500 01  LS-ERROR-BLOCK              PIC X(162).
008600 PROCEDURE DIVISION USING LS-DATE-WORK LS-ERROR-BLOCK.
008700* ---------------------------------------------------------------*
008800* 0000-MAIN                                                      *
008900* ENTRY                                                          *
009000* ---------------------------------------------------------------*
009100 0000-MAIN.
009200     INITIALIZE CLR-ERROR-BLOCK
009300     MOVE 'CLRCM010' TO ERR-PGM
009400     MOVE LS-DATE-WORK TO CLR-DATE-WORK
009500     PERFORM 2300-READ-CODE-LOOKUP
009600     PERFORM 2320-READ-USER
009700     PERFORM 2500-EDIT-CODE-LOOKUP
009800     PERFORM 2510-EDIT-USER
009900     PERFORM 9000-RETURN
010000     .
010100* ---------------------------------------------------------------*
010200* 2300-READ-CODE-LOOKUP                                          *
010300* FETCH CLR.T_CODE_LOOKUP                                        *
010400* ---------------------------------------------------------------*
010500 2300-READ-CODE-LOOKUP.
010600     SET WS-ROW-FOUND TO TRUE
010700     EXEC SQL
010800         SELECT CODE_TYPE, CODE_VALUE, CODE_DESC_EN
010900                , CODE_DESC_LOCAL
011000           INTO :CODE-CODE-TYPE, :CODE-CODE-VALUE
011100                , :CODE-CODE-DESC-EN, :CODE-CODE-DESC-LOCAL
011200           FROM CLR.T_CODE_LOOKUP
011300          WHERE CODE_TYPE = :CODE-CODE-TYPE
011400            AND CODE_VALUE = :CODE-CODE-VALUE
011500     END-EXEC
011600     EVALUATE SQLCODE
011700         WHEN 0
011800             ADD 1 TO WS-CODE-LOOKUP-READ
011900         WHEN +100
012000             SET WS-ROW-NOT-FOUND TO TRUE
012100         WHEN OTHER
012200             MOVE 'READ CLR.T_CODE_LOOKUP' TO ERR-PARA
012300             PERFORM 8000-SQL-ERROR
012400     END-EVALUATE
012500     .
012600* ---------------------------------------------------------------*
012700* 2320-READ-USER                                                 *
012800* FETCH CLR.T_USER                                               *
012900* ---------------------------------------------------------------*
013000 2320-READ-USER.
013100     MOVE WS-USER-ID TO USRR-USER-ID
013200     SET WS-ROW-FOUND TO TRUE
013300     EXEC SQL
013400         SELECT USER_ID, USER_NAME, TEAM_CD, RSV_AUTH_LEVEL
013500                , PAY_AUTH_LEVEL, ACTIVE_FLAG
013600           INTO :USRR-USER-ID, :USRR-USER-NAME, :USRR-TEAM-CD
013700                , :USRR-RSV-AUTH-LEVEL, :USRR-PAY-AUTH-LEVEL
013800                , :USRR-ACTIVE-FLAG
013900           FROM CLR.T_USER
014000          WHERE USER_ID = :USRR-USER-ID
014100     END-EXEC
014200     EVALUATE SQLCODE
014300         WHEN 0
014400             ADD 1 TO WS-USER-READ
014500         WHEN +100
014600             SET WS-ROW-NOT-FOUND TO TRUE
014700         WHEN OTHER
014800             MOVE 'READ CLR.T_USER' TO ERR-PARA
014900             PERFORM 8000-SQL-ERROR
015000     END-EVALUATE
015100     .
015200* ---------------------------------------------------------------*
015300* 2500-EDIT-CODE-LOOKUP                                          *
015400* FIELD EDITS FOR CLR.T_CODE_LOOKUP                              *
015500* ---------------------------------------------------------------*
015600 2500-EDIT-CODE-LOOKUP.
015700     IF CODE-CODE-TYPE = SPACES OR LOW-VALUES
015800         ADD 1 TO WS-REJECT-CNT
015900         MOVE 'CODE_TYPE MISSING' TO ERR-TEXT
016000     END-IF
016100     IF CODE-CODE-VALUE = SPACES OR LOW-VALUES
016200         ADD 1 TO WS-REJECT-CNT
016300         MOVE 'CODE_VALUE MISSING' TO ERR-TEXT
016400     END-IF
016500     IF CODE-CODE-DESC-EN = SPACES OR LOW-VALUES
016600         ADD 1 TO WS-REJECT-CNT
016700         MOVE 'CODE_DESC_EN MISSING' TO ERR-TEXT
016800     END-IF
016900     .
017000* ---------------------------------------------------------------*
017100* 2510-EDIT-USER                                                 *
017200* CHECK MANDATORY FIELDS IN CLR.T_USER                           *
017300* ---------------------------------------------------------------*
017400 2510-EDIT-USER.
017500     IF USRR-USER-ID = SPACES OR LOW-VALUES
017600         ADD 1 TO WS-REJECT-CNT
017700         MOVE 'USER_ID MISSING' TO ERR-TEXT
017800     END-IF
017900     IF USRR-USER-NAME = SPACES OR LOW-VALUES
018000         ADD 1 TO WS-REJECT-CNT
018100         MOVE 'USER_NAME MISSING' TO ERR-TEXT
018200     END-IF
018300     IF USRR-TEAM-CD = SPACES OR LOW-VALUES
018400         ADD 1 TO WS-REJECT-CNT
018500         MOVE 'TEAM_CD MISSING' TO ERR-TEXT
018600     END-IF
018700     .
018800* ---------------------------------------------------------------*
018900* 9000-RETURN                                                    *
019000* COPY RESULTS BACK TO THE CALLER                                *
019100* ---------------------------------------------------------------*
019200 9000-RETURN.
019300     MOVE CLR-ERROR-BLOCK TO LS-ERROR-BLOCK
019400     MOVE CLR-DATE-WORK TO LS-DATE-WORK
019500     GOBACK.
019600* ---------------------------------------------------------------*
019700* 8000-SQL-ERROR                                                 *
019800* SEVERE ERROR - REPORT AND STOP                                 *
019900* ---------------------------------------------------------------*
020000 8000-SQL-ERROR.
020100     MOVE SQLCODE TO ERR-SQLCODE WS-SQLCODE-DSP
020200     MOVE WS-PGM-ID TO ERR-PGM
020300     STRING 'SQLCODE ' WS-SQLCODE-DSP DELIMITED BY SIZE INTO
020400         ERR-TEXT
020500     DISPLAY WS-PGM-ID ' ' ERR-PARA ' ' ERR-TEXT
020600     GO TO 9000-RETURN.

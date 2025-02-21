000100* ===============================================================*
000200* PROGRAM    : CLRCM080                                          *
000300* TITLE      : NOTES WRITER                                      *
000400* SYSTEM     : CLARA - CLAIMS LEDGER AND RESERVE APPLICATION     *
000500* AREA       : COMMON                                            *
000600* TYPE       : CALLED SUBPROGRAM (STATIC CALL, NO CICS COMMANDS) *
000700* ---------------------------------------------------------------*
000800* PURPOSE                                                        *
000900*   SHARED SUBPROGRAM - NOTES WRITER.                            *
001000*   SAFE FOR BOTH BATCH AND CICS CALLERS.                        *
001100*   NON-ZERO ERR-SQLCODE MEANS THE REQUEST FAILED.               *
001200* ---------------------------------------------------------------*
001300* DB2 TABLES                                                     *
001400*   CLR.T_CODE_LOOKUP           READ                             *
001500*   CLR.T_USER                  READ                             *
001600*   CLR.T_NOTE                  INSERT                           *
001700* COPYBOOKS  : CODELKP1 NOTEREC1 USRREC01 CLRERR01               *
001800* CALLS      : NONE                                              *
001900* ---------------------------------------------------------------*
002000* MAINTENANCE HISTORY                                            *
002100* DATE       BY       REF        DESCRIPTION                     *
002200* ---------- -------- ---------- ------------------------------- *
002300* 1994-10-03 CLRPROJ             INITIAL VERSION - CLARA GO-LIVE *
002400* 1999-08-05 KBARR01             Y2K REMEDIATION - DATE          *
002500*                                WINDOWING REMOVED               *
002600* 2009-09-27 DO                  DATE ARITHMETIC MOVED TO        *
002700*                                CLRCM010                        *
002800* ===============================================================*
002900 IDENTIFICATION DIVISION.
003000 PROGRAM-ID.    CLRCM080.
003100 AUTHOR.        CLARA PROJECT TEAM.
003200 INSTALLATION.  CORVANE MUTUAL - CLAIMS SYSTEMS.
003300 DATE-WRITTEN.  1994-10-03.
003400 DATE-COMPILED.
003500 ENVIRONMENT DIVISION.
003600 CONFIGURATION SECTION.
003700 SOURCE-COMPUTER.  IBM-Z.
003800 OBJECT-COMPUTER.  IBM-Z.
003900 DATA DIVISION.
004000 WORKING-STORAGE SECTION.
004100*
004200 01  WS-PROGRAM-INFO.
004300     05  WS-PGM-ID               PIC X(8)   VALUE 'CLRCM080'.
004400     05  WS-RUN-DATE             PIC X(10)  VALUE SPACES.
004500     05  WS-RUN-TS               PIC X(26)  VALUE SPACES.
004600     05  WS-USER-ID              PIC X(8)   VALUE SPACES.
004700*
004800 01  WS-SWITCHES.
004900     05  WS-EOF-SW               PIC X      VALUE 'N'.
005000         88  WS-END-OF-DATA                     VALUE 'Y'.
005100     05  WS-ERROR-SW             PIC X      VALUE 'N'.
005200         88  WS-ERROR-FOUND                     VALUE 'Y'.
005300         88  WS-NO-ERROR                        VALUE 'N'.
005400     05  WS-FOUND-SW             PIC X      VALUE 'N'.
005500         88  WS-ROW-FOUND                       VALUE 'Y'.
005600         88  WS-ROW-NOT-FOUND                   VALUE 'N'.
005700*
005800 01  WS-COUNTERS.
005900     05  WS-CODE-LOOKUP-READ     PIC S9(9)  COMP-3 VALUE ZERO.
006000     05  WS-USER-READ            PIC S9(9)  COMP-3 VALUE ZERO.
006100     05  WS-NOTE-WRITTEN         PIC S9(9)  COMP-3 VALUE ZERO.
006200     05  WS-REJECT-CNT           PIC S9(9)  COMP-3 VALUE ZERO.
006300*
006400 01  WS-SQL-WORK.
006500     05  WS-SQLCODE-DSP          PIC -9(9).
006600     05  WS-ROWS-AFFECTED        PIC S9(9)  COMP VALUE ZERO.
006700     05  WS-IND-1                PIC S9(4)  COMP VALUE ZERO.
006800     05  WS-IND-2                PIC S9(4)  COMP VALUE ZERO.
006900     05  WS-NEW-ID               PIC S9(18) COMP VALUE ZERO.
007000*
007100     EXEC SQL INCLUDE SQLCA END-EXEC.
007200*
007300* COPYBOOKS (HOST STRUCTURES AND WORK AREAS)
007400 COPY CODELKP1.
007500 COPY NOTEREC1.
007600 COPY USRREC01.
007700 COPY CLRERR01.
007800 LINKAGE SECTION.
007900 01  LS-NOTE-PARMS.
008000     05  LS-NOTE-CLAIM-ID        PIC X(12).
008100     05  LS-NOTE-TYPE            PIC X(2).
008200     05  LS-NOTE-TEXT            PIC X(200).
008300 01  LS-ERROR-BLOCK              PIC X(162).
008400 PROCEDURE DIVISION USING LS-NOTE-PARMS LS-ERROR-BLOCK.
008500* ---------------------------------------------------------------*
008600* 0000-MAIN                                                      *
008700* ENTRY                                                          *
008800* ---------------------------------------------------------------*
008900 0000-MAIN.
009000     INITIALIZE CLR-ERROR-BLOCK
009100     MOVE 'CLRCM080' TO ERR-PGM
009200     PERFORM 2300-READ-CODE-LOOKUP
009300     PERFORM 2320-READ-USER
009400     PERFORM 2500-EDIT-CODE-LOOKUP
009500     PERFORM 2510-EDIT-USER
009600     PERFORM 2520-EDIT-NOTE
009700     PERFORM 4100-INSERT-NOTE
009800     PERFORM 9000-RETURN
009900     .
010000* ---------------------------------------------------------------*
010100* 2300-READ-CODE-LOOKUP                                          *
010200* LOOK UP CLR.T_CODE_LOOKUP                                      *
010300* ---------------------------------------------------------------*
010400 2300-READ-CODE-LOOKUP.
010500     SET WS-ROW-FOUND TO TRUE
010600     EXEC SQL
010700         SELECT CODE_TYPE, CODE_VALUE, CODE_DESC_EN
010800                , CODE_DESC_LOCAL, ACTIVE_FLAG
010900           INTO :CODE-CODE-TYPE, :CODE-CODE-VALUE
011000                , :CODE-CODE-DESC-EN, :CODE-CODE-DESC-LOCAL
011100                , :CODE-ACTIVE-FLAG
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
012800* LOOK UP CLR.T_USER                                             *
012900* ---------------------------------------------------------------*
013000 2320-READ-USER.
013100     MOVE WS-USER-ID TO USRR-USER-ID
013200     SET WS-ROW-FOUND TO TRUE
013300     EXEC SQL
013400         SELECT USER_ID, USER_NAME, TEAM_CD, RSV_AUTH_LEVEL
013500           INTO :USRR-USER-ID, :USRR-USER-NAME, :USRR-TEAM-CD
013600                , :USRR-RSV-AUTH-LEVEL
013700           FROM CLR.T_USER
013800          WHERE USER_ID = :USRR-USER-ID
013900     END-EXEC
014000     EVALUATE SQLCODE
014100         WHEN 0
014200             ADD 1 TO WS-USER-READ
014300         WHEN +100
014400             SET WS-ROW-NOT-FOUND TO TRUE
014500         WHEN OTHER
014600             MOVE 'READ CLR.T_USER' TO ERR-PARA
014700             PERFORM 8000-SQL-ERROR
014800     END-EVALUATE
014900     .
015000* ---------------------------------------------------------------*
015100* 2500-EDIT-CODE-LOOKUP                                          *
015200* FIELD EDITS FOR CLR.T_CODE_LOOKUP                              *
015300* ---------------------------------------------------------------*
015400 2500-EDIT-CODE-LOOKUP.
015500     IF CODE-CODE-TYPE = SPACES OR LOW-VALUES
015600         ADD 1 TO WS-REJECT-CNT
015700         MOVE 'CODE_TYPE MISSING' TO ERR-TEXT
015800     END-IF
015900     IF CODE-CODE-VALUE = SPACES OR LOW-VALUES
016000         ADD 1 TO WS-REJECT-CNT
016100         MOVE 'CODE_VALUE MISSING' TO ERR-TEXT
016200     END-IF
016300     IF CODE-CODE-DESC-EN = SPACES OR LOW-VALUES
016400         ADD 1 TO WS-REJECT-CNT
016500         MOVE 'CODE_DESC_EN MISSING' TO ERR-TEXT
016600     END-IF
016700     .
016800* ---------------------------------------------------------------*
016900* 2510-EDIT-USER                                                 *
017000* CHECK MANDATORY FIELDS IN CLR.T_USER                           *
017100* ---------------------------------------------------------------*
017200 2510-EDIT-USER.
017300     IF USRR-USER-ID = SPACES OR LOW-VALUES
017400         ADD 1 TO WS-REJECT-CNT
017500         MOVE 'USER_ID MISSING' TO ERR-TEXT
017600     END-IF
017700     IF USRR-USER-NAME = SPACES OR LOW-VALUES
017800         ADD 1 TO WS-REJECT-CNT
017900         MOVE 'USER_NAME MISSING' TO ERR-TEXT
018000     END-IF
018100     IF USRR-TEAM-CD = SPACES OR LOW-VALUES
018200         ADD 1 TO WS-REJECT-CNT
018300         MOVE 'TEAM_CD MISSING' TO ERR-TEXT
018400     END-IF
018500     .
018600* ---------------------------------------------------------------*
018700* 2520-EDIT-NOTE                                                 *
018800* FIELD EDITS FOR CLR.T_NOTE                                     *
018900* ---------------------------------------------------------------*
019000 2520-EDIT-NOTE.
019100     IF NOTE-CLAIM-ID = SPACES OR LOW-VALUES
019200         ADD 1 TO WS-REJECT-CNT
019300         MOVE 'CLAIM_ID MISSING' TO ERR-TEXT
019400     END-IF
019500     .
019600* ---------------------------------------------------------------*
019700* 4100-INSERT-NOTE                                               *
019800* INSERT CLR.T_NOTE                                              *
019900* ---------------------------------------------------------------*
020000 4100-INSERT-NOTE.
020100     EXEC SQL
020200         INSERT INTO CLR.T_NOTE
020300              ( CLAIM_ID, NOTE_TS, NOTE_TXT, NOTE_TYPE_CD
020400              , LAST_UPD_TS, LAST_UPD_PGM, LAST_UPD_USER )
020500         VALUES
020600              ( :NOTE-CLAIM-ID, CURRENT TIMESTAMP
020700              , :NOTE-NOTE-TXT, :NOTE-NOTE-TYPE-CD
020800              , CURRENT TIMESTAMP, :WS-PGM-ID, :WS-USER-ID )
020900     END-EXEC
021000     EVALUATE SQLCODE
021100         WHEN 0
021200             ADD 1 TO WS-NOTE-WRITTEN
021300         WHEN +100
021400             SET WS-ROW-NOT-FOUND TO TRUE
021500         WHEN OTHER
021600             MOVE 'INSERT CLR.T_NOTE' TO ERR-PARA
021700             PERFORM 8000-SQL-ERROR
021800     END-EVALUATE
021900     .
022000* ---------------------------------------------------------------*
022100* 9000-RETURN                                                    *
022200* COPY RESULTS BACK TO THE CALLER                                *
022300* ---------------------------------------------------------------*
022400 9000-RETURN.
022500     MOVE CLR-ERROR-BLOCK TO LS-ERROR-BLOCK
022600     GOBACK.
022700* ---------------------------------------------------------------*
022800* 8000-SQL-ERROR                                                 *
022900* DB2 ERROR HANDLING                                             *
023000* ---------------------------------------------------------------*
023100 8000-SQL-ERROR.
023200     MOVE SQLCODE TO ERR-SQLCODE WS-SQLCODE-DSP
023300     MOVE WS-PGM-ID TO ERR-PGM
023400     STRING 'SQLCODE ' WS-SQLCODE-DSP DELIMITED BY SIZE INTO
023500         ERR-TEXT
023600     DISPLAY WS-PGM-ID ' ' ERR-PARA ' ' ERR-TEXT
023700     GO TO 9000-RETURN.

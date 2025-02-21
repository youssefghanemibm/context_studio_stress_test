000100* ================================================================
000200* PROGRAM    : CLRRS200
000300* TITLE      : RESERVE TYPE MAINTENANCE
000400* SYSTEM     : CLARA - CLAIMS LEDGER AND RESERVE APPLICATION
000500* AREA       : RESERVE
000600* TYPE       : CICS ONLINE / DB2
000700* TRANSACTION: RS20
000800* ----------------------------------------------------------------
000900* PURPOSE
001000*   ONLINE TRANSACTION: RESERVE TYPE MAINTENANCE.
001100*   COMMAREA LAYOUT: CLRCOMM1.
001200*   INVOKED WITH A COMMAREA; RESULTS RETURNED IN
001300*     CA-RETURN-CD/CA-MSG.
001400* ----------------------------------------------------------------
001500* DB2 TABLES
001600*   CLR.T_CLAIM_TIER            READ
001700*   CLR.T_RESERVE_HISTORY       READ
001800*   CLR.T_CODE_LOOKUP           UPDATE
001900* COPYBOOKS  : CLRTIR01 CODELKP1 RSVHIS01 CLRERR01 CLRCOMM1
002000* CALLS      : CLRCM050
002100* ----------------------------------------------------------------
002200* MAINTENANCE HISTORY
002300* DATE       BY       REF        DESCRIPTION
002400* ---------- -------- ---------- -------------------------------
002500* 1994-10-03 CLRPROJ             INITIAL VERSION - CLARA GO-LIVE
002600* 2010-08-13 KBARR01             DATE ARITHMETIC MOVED TO
002700*                                CLRCM010
002800* 2010-09-06 KBARR01             PF12 CANCEL HANDLING ADDED
002900* 2015-01-30 KBARR01             PERFORMANCE: CURSOR WITH HOLD,
003000*                                FEWER COMMITS
003100* 2015-02-24 KBARR01             COMMIT FREQUENCY TUNED FOR
003200*                                BATCH WINDOW
003300* ================================================================
003400 IDENTIFICATION DIVISION.
003500 PROGRAM-ID.    CLRRS200.
003600 AUTHOR.        CLARA PROJECT TEAM.
003700 INSTALLATION.  CORVANE MUTUAL - CLAIMS SYSTEMS.
003800 DATE-WRITTEN.  1994-10-03.
003900 DATE-COMPILED.
004000 ENVIRONMENT DIVISION.
004100 CONFIGURATION SECTION.
004200 SOURCE-COMPUTER.  IBM-Z.
004300 OBJECT-COMPUTER.  IBM-Z.
004400 DATA DIVISION.
004500 WORKING-STORAGE SECTION.
004600*
004700 01  WS-PROGRAM-INFO.
004800     05  WS-PGM-ID               PIC X(8)   VALUE 'CLRRS200'.
004900     05  WS-RUN-DATE             PIC X(10)  VALUE SPACES.
005000     05  WS-RUN-TS               PIC X(26)  VALUE SPACES.
005100     05  WS-USER-ID              PIC X(8)   VALUE SPACES.
005200*
005300 01  WS-SWITCHES.
005400     05  WS-EOF-SW               PIC X      VALUE 'N'.
005500         88  WS-END-OF-DATA                     VALUE 'Y'.
005600     05  WS-ERROR-SW             PIC X      VALUE 'N'.
005700         88  WS-ERROR-FOUND                     VALUE 'Y'.
005800         88  WS-NO-ERROR                        VALUE 'N'.
005900     05  WS-FOUND-SW             PIC X      VALUE 'N'.
006000         88  WS-ROW-FOUND                       VALUE 'Y'.
006100         88  WS-ROW-NOT-FOUND                   VALUE 'N'.
006200*
006300 01  WS-COUNTERS.
006400     05  WS-CLAIM-TIER-READ      PIC S9(9)  COMP-3 VALUE ZERO.
006500     05  WS-RESERVE-HISTORY-READ PIC S9(9)  COMP-3 VALUE ZERO.
006600     05  WS-CODE-LOOKUP-WRITTEN  PIC S9(9)  COMP-3 VALUE ZERO.
006700     05  WS-REJECT-CNT           PIC S9(9)  COMP-3 VALUE ZERO.
006800*
006900 01  WS-SQL-WORK.
007000     05  WS-SQLCODE-DSP          PIC -9(9).
007100     05  WS-ROWS-AFFECTED        PIC S9(9)  COMP VALUE ZERO.
007200     05  WS-IND-1                PIC S9(4)  COMP VALUE ZERO.
007300     05  WS-IND-2                PIC S9(4)  COMP VALUE ZERO.
007400     05  WS-NEW-ID               PIC S9(18) COMP VALUE ZERO.
007500*
007600     EXEC SQL INCLUDE SQLCA END-EXEC.
007700*
007800* CLARA RECORD LAYOUTS
007900 COPY CLRTIR01.
008000 COPY CODELKP1.
008100 COPY RSVHIS01.
008200 COPY CLRERR01.
008300 COPY CLRCOMM1.
008400*
008500 01  WS-AID-VALUES.
008600     05  AID-ENTER               PIC X      VALUE X'7D'.
008700     05  AID-CLEAR               PIC X      VALUE X'6D'.
008800     05  AID-PF3                 PIC X      VALUE X'F3'.
008900     05  AID-PF7                 PIC X      VALUE X'F7'.
009000     05  AID-PF8                 PIC X      VALUE X'F8'.
009100     05  AID-PF12                PIC X      VALUE X'7C'.
009200     05  WS-RESP                 PIC S9(8)  COMP VALUE ZERO.
009300 LINKAGE SECTION.
009400 01  DFHCOMMAREA                 PIC X(105).
009500 PROCEDURE DIVISION.
009600* ---------------------------------------------------------------*
009700* 0000-MAIN                                                      *
009800* PSEUDO-CONVERSATIONAL CONTROL                                  *
009900* ---------------------------------------------------------------*
010000 0000-MAIN.
010100     EXEC CICS ASSIGN USERID(WS-USER-ID) END-EXEC
010200     IF EIBCALEN = ZERO
010300         INITIALIZE CLR-COMMAREA
010400         MOVE 'RS20' TO CA-TRANID
010500         MOVE 12 TO CA-RETURN-CD
010600         MOVE 'NO COMMAREA SUPPLIED' TO CA-MSG
010700         PERFORM 9000-RETURN
010800     ELSE
010900         MOVE DFHCOMMAREA TO CLR-COMMAREA
011000         PERFORM 2000-PROCESS-INPUT
011100     END-IF
011200     PERFORM 9000-RETURN
011300     GOBACK.
011400* ---------------------------------------------------------------*
011500* 2000-PROCESS-INPUT                                             *
011600* HANDLE THE TERMINAL INPUT                                      *
011700* ---------------------------------------------------------------*
011800 2000-PROCESS-INPUT.
011900     PERFORM 2100-EDIT-INPUT
012000     IF WS-NO-ERROR
012100         PERFORM 2200-APPLY
012200     END-IF
012300     .
012400* ---------------------------------------------------------------*
012500* 2100-EDIT-INPUT                                                *
012600* VALIDATE THE REQUEST                                           *
012700* ---------------------------------------------------------------*
012800 2100-EDIT-INPUT.
012900     SET WS-NO-ERROR TO TRUE
013000     IF CA-CLAIM-ID = SPACES OR LOW-VALUES
013100         SET WS-ERROR-FOUND TO TRUE
013200         MOVE 8 TO CA-RETURN-CD
013300         MOVE 'CLAIM ID IS REQUIRED' TO CA-MSG
013400     END-IF
013500     .
013600* ---------------------------------------------------------------*
013700* 2200-APPLY                                                     *
013800* BUSINESS PROCESSING                                            *
013900* ---------------------------------------------------------------*
014000 2200-APPLY.
014100     PERFORM 2300-READ-CLAIM-TIER
014200     PERFORM 2320-READ-RESE-HIST
014300     PERFORM 2500-EDIT-CLAIM-TIER
014400     PERFORM 2510-EDIT-RESE-HIST
014500     PERFORM 2520-EDIT-CODE-LOOKUP
014600     PERFORM 2530-EDIT-CLAIM-TIER-2
014700     PERFORM 2540-EDIT-RESE-HIST-2
014800     PERFORM 2550-EDIT-CODE-LOOKUP-2
014900     PERFORM 2560-EDIT-CLAIM-TIER-3
015000     PERFORM 2570-EDIT-RESE-HIST-3
015100     PERFORM 4100-UPDATE-CODE-LOOKUP
015200     IF WS-NO-ERROR
015300         EXEC CICS SYNCPOINT END-EXEC
015400         MOVE ZERO TO CA-RETURN-CD
015500     END-IF
015600     .
015700* ---------------------------------------------------------------*
015800* 2300-READ-CLAIM-TIER                                           *
015900* READ CLR.T_CLAIM_TIER                                          *
016000* ---------------------------------------------------------------*
016100 2300-READ-CLAIM-TIER.
016200     MOVE CA-CLAIM-ID TO TIR-CLAIM-ID
016300     SET WS-ROW-FOUND TO TRUE
016400     EXEC SQL
016500         SELECT CLAIM_ID, TIER_FROM_TS, TIER_CD
016600                , TIER_REASON_CD
016700           INTO :TIR-CLAIM-ID, :TIR-TIER-FROM-TS
016800                , :TIR-TIER-CD, :TIR-TIER-REASON-CD
016900           FROM CLR.T_CLAIM_TIER
017000          WHERE CLAIM_ID = :TIR-CLAIM-ID
017100            AND TIER_FROM_TS = :TIR-TIER-FROM-TS
017200     END-EXEC
017300     EVALUATE SQLCODE
017400         WHEN 0
017500             ADD 1 TO WS-CLAIM-TIER-READ
017600         WHEN +100
017700             SET WS-ROW-NOT-FOUND TO TRUE
017800         WHEN OTHER
017900             MOVE 'READ CLR.T_CLAIM_TIER' TO ERR-PARA
018000             PERFORM 8000-SQL-ERROR
018100     END-EVALUATE
018200     .
018300* ---------------------------------------------------------------*
018400* 2320-READ-RESE-HIST                                            *
018500* LOOK UP CLR.T_RESERVE_HISTORY                                  *
018600* ---------------------------------------------------------------*
018700 2320-READ-RESE-HIST.
018800     SET WS-ROW-FOUND TO TRUE
018900     EXEC SQL
019000         SELECT RSV_ID, SNAPSHOT_DT, RSV_OUTSTANDING_AMT
019100           INTO :RSVH-RSV-ID, :RSVH-SNAPSHOT-DT
019200                , :RSVH-RSV-OUTSTANDING-AMT
019300           FROM CLR.T_RESERVE_HISTORY
019400          WHERE RSV_ID = :RSVH-RSV-ID
019500            AND SNAPSHOT_DT = :RSVH-SNAPSHOT-DT
019600     END-EXEC
019700     EVALUATE SQLCODE
019800         WHEN 0
019900             ADD 1 TO WS-RESERVE-HISTORY-READ
020000         WHEN +100
020100             SET WS-ROW-NOT-FOUND TO TRUE
020200         WHEN OTHER
020300             MOVE 'READ CLR.T_RESERVE_HISTORY' TO ERR-PARA
020400             PERFORM 8000-SQL-ERROR
020500     END-EVALUATE
020600     .
020700* ---------------------------------------------------------------*
020800* 2500-EDIT-CLAIM-TIER                                           *
020900* CHECK MANDATORY FIELDS IN CLR.T_CLAIM_TIER                     *
021000* ---------------------------------------------------------------*
021100 2500-EDIT-CLAIM-TIER.
021200     IF TIR-CLAIM-ID = SPACES OR LOW-VALUES
021300         ADD 1 TO WS-REJECT-CNT
021400         MOVE 'CLAIM_ID MISSING' TO ERR-TEXT
021500     END-IF
021600     IF TIR-TIER-CD = SPACES OR LOW-VALUES
021700         ADD 1 TO WS-REJECT-CNT
021800         MOVE 'TIER_CD MISSING' TO ERR-TEXT
021900     END-IF
022000     .
022100* ---------------------------------------------------------------*
022200* 2510-EDIT-RESE-HIST                                            *
022300* FIELD EDITS FOR CLR.T_RESERVE_HISTORY                          *
022400* ---------------------------------------------------------------*
022500 2510-EDIT-RESE-HIST.
022600     IF RSVH-SNAPSHOT-DT NOT = SPACES AND RSVH-SNAPSHOT-DT(5:1)
022700         NOT = '-'
022800         MOVE 'SNAPSHOT_DT BAD DATE' TO ERR-TEXT
022900         ADD 1 TO WS-REJECT-CNT
023000     END-IF
023100     IF RSVH-RSV-OUTSTANDING-AMT NOT NUMERIC
023200         MOVE ZERO TO RSVH-RSV-OUTSTANDING-AMT
023300         ADD 1 TO WS-REJECT-CNT
023400     END-IF
023500     .
023600* ---------------------------------------------------------------*
023700* 2520-EDIT-CODE-LOOKUP                                          *
023800* VALIDATE CLR.T_CODE_LOOKUP                                     *
023900* ---------------------------------------------------------------*
024000 2520-EDIT-CODE-LOOKUP.
024100     IF CODE-CODE-TYPE = SPACES OR LOW-VALUES
024200         ADD 1 TO WS-REJECT-CNT
024300         MOVE 'CODE_TYPE MISSING' TO ERR-TEXT
024400     END-IF
024500     IF CODE-CODE-VALUE = SPACES OR LOW-VALUES
024600         ADD 1 TO WS-REJECT-CNT
024700         MOVE 'CODE_VALUE MISSING' TO ERR-TEXT
024800     END-IF
024900     IF CODE-CODE-DESC-EN = SPACES OR LOW-VALUES
025000         ADD 1 TO WS-REJECT-CNT
025100         MOVE 'CODE_DESC_EN MISSING' TO ERR-TEXT
025200     END-IF
025300     .
025400* ---------------------------------------------------------------*
025500* 2530-EDIT-CLAIM-TIER-2                                         *
025600* FIELD EDITS FOR CLR.T_CLAIM_TIER                               *
025700* ---------------------------------------------------------------*
025800 2530-EDIT-CLAIM-TIER-2.
025900     IF TIR-TIER-REASON-CD = SPACES OR LOW-VALUES
026000         ADD 1 TO WS-REJECT-CNT
026100         MOVE 'TIER_REASON_CD MISSING' TO ERR-TEXT
026200     END-IF
026300     IF TIR-OVERRIDE-FLAG = SPACES OR LOW-VALUES
026400         ADD 1 TO WS-REJECT-CNT
026500         MOVE 'OVERRIDE_FLAG MISSING' TO ERR-TEXT
026600     END-IF
026700     .
026800* ---------------------------------------------------------------*
026900* 2540-EDIT-RESE-HIST-2                                          *
027000* VALIDATE CLR.T_RESERVE_HISTORY                                 *
027100* ---------------------------------------------------------------*
027200 2540-EDIT-RESE-HIST-2.
027300     IF RSVH-RSV-GBP-EQUIV-AMT NOT NUMERIC
027400         MOVE ZERO TO RSVH-RSV-GBP-EQUIV-AMT
027500         ADD 1 TO WS-REJECT-CNT
027600     END-IF
027700     IF RSVH-TIER-CD = SPACES OR LOW-VALUES
027800         ADD 1 TO WS-REJECT-CNT
027900         MOVE 'TIER_CD MISSING' TO ERR-TEXT
028000     END-IF
028100     .
028200* ---------------------------------------------------------------*
028300* 2550-EDIT-CODE-LOOKUP-2                                        *
028400* FIELD EDITS FOR CLR.T_CODE_LOOKUP                              *
028500* ---------------------------------------------------------------*
028600 2550-EDIT-CODE-LOOKUP-2.
028700     IF CODE-ACTIVE-FLAG = SPACES OR LOW-VALUES
028800         ADD 1 TO WS-REJECT-CNT
028900         MOVE 'ACTIVE_FLAG MISSING' TO ERR-TEXT
029000     END-IF
029100     .
029200* ---------------------------------------------------------------*
029300* 2560-EDIT-CLAIM-TIER-3                                         *
029400* FIELD EDITS FOR CLR.T_CLAIM_TIER                               *
029500* ---------------------------------------------------------------*
029600 2560-EDIT-CLAIM-TIER-3.
029700* ---------------------------------------------------------------*
029800* 2570-EDIT-RESE-HIST-3                                          *
029900* CHECK MANDATORY FIELDS IN CLR.T_RESERVE_HISTORY                *
030000* ---------------------------------------------------------------*
030100 2570-EDIT-RESE-HIST-3.
030200* ---------------------------------------------------------------*
030300* 4100-UPDATE-CODE-LOOKUP                                        *
030400* UPDATE CLR.T_CODE_LOOKUP                                       *
030500* ---------------------------------------------------------------*
030600 4100-UPDATE-CODE-LOOKUP.
030700     EXEC SQL
030800         UPDATE CLR.T_CODE_LOOKUP
030900            SET CODE_DESC_EN = :CODE-CODE-DESC-EN
031000              , CODE_DESC_LOCAL = :CODE-CODE-DESC-LOCAL
031100              , ACTIVE_FLAG = :CODE-ACTIVE-FLAG
031200              , LAST_UPD_TS = CURRENT TIMESTAMP
031300              , LAST_UPD_PGM = :WS-PGM-ID
031400              , LAST_UPD_USER = :WS-USER-ID
031500          WHERE CODE_TYPE = :CODE-CODE-TYPE
031600            AND CODE_VALUE = :CODE-CODE-VALUE
031700     END-EXEC
031800     EVALUATE SQLCODE
031900         WHEN 0
032000             ADD 1 TO WS-CODE-LOOKUP-WRITTEN
032100         WHEN +100
032200             SET WS-ROW-NOT-FOUND TO TRUE
032300         WHEN OTHER
032400             MOVE 'UPDATE CLR.T_CODE_LOOKUP' TO ERR-PARA
032500             PERFORM 8000-SQL-ERROR
032600     END-EVALUATE
032700     .
032800* ---------------------------------------------------------------*
032900* 9000-RETURN                                                    *
033000* RETURN TO CICS                                                 *
033100* ---------------------------------------------------------------*
033200 9000-RETURN.
033300     MOVE CLR-COMMAREA TO DFHCOMMAREA
033400     EXEC CICS RETURN END-EXEC
033500     .
033600* ---------------------------------------------------------------*
033700* 8000-SQL-ERROR                                                 *
033800* SEVERE ERROR - REPORT AND STOP                                 *
033900* ---------------------------------------------------------------*
034000 8000-SQL-ERROR.
034100     MOVE SQLCODE TO ERR-SQLCODE WS-SQLCODE-DSP
034200     MOVE WS-PGM-ID TO ERR-PGM
034300     STRING 'SQLCODE ' WS-SQLCODE-DSP DELIMITED BY SIZE INTO
034400         ERR-TEXT
034500     CALL 'CLRCM050' USING CLR-ERROR-BLOCK
034600     EXEC CICS SYNCPOINT ROLLBACK END-EXEC
034700     MOVE 16 TO CA-RETURN-CD
034800     MOVE ERR-TEXT TO CA-MSG
034900     PERFORM 9000-RETURN
035000     .

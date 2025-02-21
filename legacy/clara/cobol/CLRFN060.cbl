000100* ===============================================================*
000200* PROGRAM    : CLRFN060                                          *
000300* TITLE      : DUPLICATE CLAIM CHECK (SAME POLICY, DATE OF LOSS  *
000400*              +/-3 DAYS)                                        *
000500* SYSTEM     : CLARA - CLAIMS LEDGER AND RESERVE APPLICATION     *
000600* AREA       : FNOL                                              *
000700* TYPE       : CICS ONLINE / DB2                                 *
000800* TRANSACTION: FN06                                              *
000900* ---------------------------------------------------------------*
001000* PURPOSE                                                        *
001100*   ONLINE PROGRAM: DUPLICATE CLAIM CHECK (SAME POLICY, DATE OF  *
001200*     LOSS +/-3 DAYS).                                           *
001300*   PSEUDO-CONVERSATIONAL; STATE IS KEPT IN CLRCOMM1.            *
001400*   INVOKED WITH A COMMAREA; RESULTS RETURNED IN                 *
001500*     CA-RETURN-CD/CA-MSG.                                       *
001600* ---------------------------------------------------------------*
001700* DB2 TABLES                                                     *
001800*   CLR.T_CLAIM                 READ                             *
001900*   CLR.T_FNOL_EVENT            READ                             *
002000*   CLR.T_POLICY_SNAPSHOT       READ                             *
002100* COPYBOOKS  : CLRCLM01 CLRFNL01 CLRPOL01 CLRERR01 CLRCOMM1      *
002200* CALLS      : CLRCM050 CLRCM070                                 *
002300* ---------------------------------------------------------------*
002400* MAINTENANCE HISTORY                                            *
002500* DATE       BY       REF        DESCRIPTION                     *
002600* ---------- -------- ---------- ------------------------------- *
002700* 2007-02-01 PASHW01             INITIAL VERSION                 *
002800* 2007-08-19 PASHW01             RECOMPILED - COBOL FOR Z/OS     *
002900*                                UPGRADE                         *
003000* 2016-03-05 PASHW01             CURSOR POSITIONING ON           *
003100*                                VALIDATION ERRORS               *
003200* ===============================================================*
003300 IDENTIFICATION DIVISION.
003400 PROGRAM-ID.    CLRFN060.
003500 AUTHOR.        P. ASHWORTH.
003600 INSTALLATION.  CORVANE MUTUAL - CLAIMS SYSTEMS.
003700 DATE-WRITTEN.  2007-02-01.
003800 DATE-COMPILED.
003900 ENVIRONMENT DIVISION.
004000 CONFIGURATION SECTION.
004100 SOURCE-COMPUTER.  IBM-Z.
004200 OBJECT-COMPUTER.  IBM-Z.
004300 DATA DIVISION.
004400 WORKING-STORAGE SECTION.
004500*
004600 01  WS-PROGRAM-INFO.
004700     05  WS-PGM-ID               PIC X(8)   VALUE 'CLRFN060'.
004800     05  WS-RUN-DATE             PIC X(10)  VALUE SPACES.
004900     05  WS-RUN-TS               PIC X(26)  VALUE SPACES.
005000     05  WS-USER-ID              PIC X(8)   VALUE SPACES.
005100*
005200 01  WS-SWITCHES.
005300     05  WS-EOF-SW               PIC X      VALUE 'N'.
005400         88  WS-END-OF-DATA                     VALUE 'Y'.
005500     05  WS-ERROR-SW             PIC X      VALUE 'N'.
005600         88  WS-ERROR-FOUND                     VALUE 'Y'.
005700         88  WS-NO-ERROR                        VALUE 'N'.
005800     05  WS-FOUND-SW             PIC X      VALUE 'N'.
005900         88  WS-ROW-FOUND                       VALUE 'Y'.
006000         88  WS-ROW-NOT-FOUND                   VALUE 'N'.
006100*
006200 01  WS-COUNTERS.
006300     05  WS-CLAIM-READ           PIC S9(9)  COMP-3 VALUE ZERO.
006400     05  WS-FNOL-EVENT-READ      PIC S9(9)  COMP-3 VALUE ZERO.
006500     05  WS-POLICY-SNAPSHOT-READ PIC S9(9)  COMP-3 VALUE ZERO.
006600     05  WS-REJECT-CNT           PIC S9(9)  COMP-3 VALUE ZERO.
006700*
006800 01  WS-SQL-WORK.
006900     05  WS-SQLCODE-DSP          PIC -9(9).
007000     05  WS-ROWS-AFFECTED        PIC S9(9)  COMP VALUE ZERO.
007100     05  WS-IND-1                PIC S9(4)  COMP VALUE ZERO.
007200     05  WS-IND-2                PIC S9(4)  COMP VALUE ZERO.
007300     05  WS-NEW-ID               PIC S9(18) COMP VALUE ZERO.
007400*
007500     EXEC SQL INCLUDE SQLCA END-EXEC.
007600*
007700* APPLICATION COPYBOOKS
007800 COPY CLRCLM01.
007900 COPY CLRFNL01.
008000 COPY CLRPOL01.
008100 COPY CLRERR01.
008200 COPY CLRCOMM1.
008300*
008400* CALL INTERFACES
008500 01  WS-AUTH-PARMS.
008600     05  WS-AUTH-USER            PIC X(8).
008700     05  WS-AUTH-FUNCTION        PIC X(8).
008800     05  WS-AUTH-ALLOWED         PIC X(1).
008900*
009000 01  WS-AID-VALUES.
009100     05  AID-ENTER               PIC X      VALUE X'7D'.
009200     05  AID-CLEAR               PIC X      VALUE X'6D'.
009300     05  AID-PF3                 PIC X      VALUE X'F3'.
009400     05  AID-PF7                 PIC X      VALUE X'F7'.
009500     05  AID-PF8                 PIC X      VALUE X'F8'.
009600     05  AID-PF12                PIC X      VALUE X'7C'.
009700     05  WS-RESP                 PIC S9(8)  COMP VALUE ZERO.
009800 LINKAGE SECTION.
009900 01  DFHCOMMAREA                 PIC X(105).
010000 PROCEDURE DIVISION.
010100* ---------------------------------------------------------------*
010200* 0000-MAIN                                                      *
010300* PSEUDO-CONVERSATIONAL CONTROL                                  *
010400* ---------------------------------------------------------------*
010500 0000-MAIN.
010600     EXEC CICS ASSIGN USERID(WS-USER-ID) END-EXEC
010700     IF EIBCALEN = ZERO
010800         INITIALIZE CLR-COMMAREA
010900         MOVE 'FN06' TO CA-TRANID
011000         MOVE 12 TO CA-RETURN-CD
011100         MOVE 'NO COMMAREA SUPPLIED' TO CA-MSG
011200         PERFORM 9000-RETURN
011300     ELSE
011400         MOVE DFHCOMMAREA TO CLR-COMMAREA
011500         PERFORM 2000-PROCESS-INPUT
011600     END-IF
011700     PERFORM 9000-RETURN
011800     GOBACK.
011900* ---------------------------------------------------------------*
012000* 2000-PROCESS-INPUT                                             *
012100* INPUT PROCESSING                                               *
012200* ---------------------------------------------------------------*
012300 2000-PROCESS-INPUT.
012400     PERFORM 2100-EDIT-INPUT
012500     IF WS-NO-ERROR
012600         PERFORM 2200-APPLY
012700     END-IF
012800     .
012900* ---------------------------------------------------------------*
013000* 2100-EDIT-INPUT                                                *
013100* VALIDATE THE REQUEST                                           *
013200* ---------------------------------------------------------------*
013300 2100-EDIT-INPUT.
013400     SET WS-NO-ERROR TO TRUE
013500     IF CA-CLAIM-ID = SPACES OR LOW-VALUES
013600         SET WS-ERROR-FOUND TO TRUE
013700         MOVE 8 TO CA-RETURN-CD
013800         MOVE 'CLAIM ID IS REQUIRED' TO CA-MSG
013900     END-IF
014000     PERFORM 1500-CHECK-AUTHORITY
014100     .
014200* ---------------------------------------------------------------*
014300* 1500-CHECK-AUTHORITY                                           *
014400* CONFIRM THE USER MAY RUN THIS FUNCTION                         *
014500* ---------------------------------------------------------------*
014600 1500-CHECK-AUTHORITY.
014700     MOVE WS-USER-ID TO WS-AUTH-USER
014800     MOVE 'CLRFN060' TO WS-AUTH-FUNCTION
014900     CALL 'CLRCM070' USING WS-AUTH-PARMS
015000                      CLR-ERROR-BLOCK
015100     IF ERR-SQLCODE NOT = ZERO
015200         MOVE 'CALL CLRCM070' TO ERR-PARA
015300         PERFORM 8000-SQL-ERROR
015400     END-IF
015500     IF WS-AUTH-ALLOWED NOT = 'Y'
015600         SET WS-ERROR-FOUND TO TRUE
015700         MOVE 8 TO CA-RETURN-CD
015800         MOVE 'NOT AUTHORISED FOR THIS FUNCTION' TO CA-MSG
015900     END-IF
016000     .
016100* ---------------------------------------------------------------*
016200* 2200-APPLY                                                     *
016300* CARRY OUT THE REQUEST                                          *
016400* ---------------------------------------------------------------*
016500 2200-APPLY.
016600     PERFORM 2300-READ-CLAIM
016700     PERFORM 2320-READ-FNOL-EVENT
016800     PERFORM 2340-READ-POLI-SNAP
016900     PERFORM 2500-EDIT-CLAIM
017000     IF WS-NO-ERROR
017100         MOVE ZERO TO CA-RETURN-CD
017200     END-IF
017300     .
017400* ---------------------------------------------------------------*
017500* 2300-READ-CLAIM                                                *
017600* READ CLR.T_CLAIM                                               *
017700* ---------------------------------------------------------------*
017800 2300-READ-CLAIM.
017900     MOVE CA-CLAIM-ID TO CLM-CLAIM-ID
018000     SET WS-ROW-FOUND TO TRUE
018100     EXEC SQL
018200         SELECT CLAIM_ID, POLICY_NO, PRODUCT_CD, PERIL_CD
018300           INTO :CLM-CLAIM-ID, :CLM-POLICY-NO
018400                , :CLM-PRODUCT-CD, :CLM-PERIL-CD
018500           FROM CLR.T_CLAIM
018600          WHERE CLAIM_ID = :CLM-CLAIM-ID
018700     END-EXEC
018800     EVALUATE SQLCODE
018900         WHEN 0
019000             ADD 1 TO WS-CLAIM-READ
019100         WHEN +100
019200             SET WS-ROW-NOT-FOUND TO TRUE
019300         WHEN OTHER
019400             MOVE 'READ CLR.T_CLAIM' TO ERR-PARA
019500             PERFORM 8000-SQL-ERROR
019600     END-EVALUATE
019700     .
019800* ---------------------------------------------------------------*
019900* 2320-READ-FNOL-EVENT                                           *
020000* LOOK UP CLR.T_FNOL_EVENT                                       *
020100* ---------------------------------------------------------------*
020200 2320-READ-FNOL-EVENT.
020300     SET WS-ROW-FOUND TO TRUE
020400     EXEC SQL
020500         SELECT FNOL_ID, CLAIM_ID, CHANNEL_CD, RECEIVED_TS
020600                , PAYLOAD_REF, CALLER_PHONE
020700           INTO :FNL-FNOL-ID, :FNL-CLAIM-ID, :FNL-CHANNEL-CD
020800                , :FNL-RECEIVED-TS, :FNL-PAYLOAD-REF
020900                , :FNL-CALLER-PHONE
021000           FROM CLR.T_FNOL_EVENT
021100          WHERE FNOL_ID = :FNL-FNOL-ID
021200     END-EXEC
021300     EVALUATE SQLCODE
021400         WHEN 0
021500             ADD 1 TO WS-FNOL-EVENT-READ
021600         WHEN +100
021700             SET WS-ROW-NOT-FOUND TO TRUE
021800         WHEN OTHER
021900             MOVE 'READ CLR.T_FNOL_EVENT' TO ERR-PARA
022000             PERFORM 8000-SQL-ERROR
022100     END-EVALUATE
022200     .
022300* ---------------------------------------------------------------*
022400* 2340-READ-POLI-SNAP                                            *
022500* FETCH CLR.T_POLICY_SNAPSHOT                                    *
022600* ---------------------------------------------------------------*
022700 2340-READ-POLI-SNAP.
022800     SET WS-ROW-FOUND TO TRUE
022900     EXEC SQL
023000         SELECT POLICY_NO, SNAPSHOT_DT, PRODUCT_CD
023100                , COVER_START_DT, COVER_END_DT, EXCESS_AMT
023200           INTO :POL-POLICY-NO, :POL-SNAPSHOT-DT
023300                , :POL-PRODUCT-CD, :POL-COVER-START-DT
023400                , :POL-COVER-END-DT, :POL-EXCESS-AMT
023500           FROM CLR.T_POLICY_SNAPSHOT
023600          WHERE POLICY_NO = :POL-POLICY-NO
023700            AND SNAPSHOT_DT = :POL-SNAPSHOT-DT
023800     END-EXEC
023900     EVALUATE SQLCODE
024000         WHEN 0
024100             ADD 1 TO WS-POLICY-SNAPSHOT-READ
024200         WHEN +100
024300             SET WS-ROW-NOT-FOUND TO TRUE
024400         WHEN OTHER
024500             MOVE 'READ CLR.T_POLICY_SNAPSHOT' TO ERR-PARA
024600             PERFORM 8000-SQL-ERROR
024700     END-EVALUATE
024800     .
024900* ---------------------------------------------------------------*
025000* 2500-EDIT-CLAIM                                                *
025100* FIELD EDITS FOR CLR.T_CLAIM                                    *
025200* ---------------------------------------------------------------*
025300 2500-EDIT-CLAIM.
025400     IF CLM-CLAIM-ID = SPACES OR LOW-VALUES
025500         ADD 1 TO WS-REJECT-CNT
025600         MOVE 'CLAIM_ID MISSING' TO ERR-TEXT
025700     END-IF
025800     IF CLM-POLICY-NO = SPACES OR LOW-VALUES
025900         ADD 1 TO WS-REJECT-CNT
026000         MOVE 'POLICY_NO MISSING' TO ERR-TEXT
026100     END-IF
026200     IF CLM-PRODUCT-CD = SPACES OR LOW-VALUES
026300         ADD 1 TO WS-REJECT-CNT
026400         MOVE 'PRODUCT_CD MISSING' TO ERR-TEXT
026500     END-IF
026600     IF CLM-PERIL-CD = SPACES OR LOW-VALUES
026700         ADD 1 TO WS-REJECT-CNT
026800         MOVE 'PERIL_CD MISSING' TO ERR-TEXT
026900     END-IF
027000     IF CLM-LOSS-DT NOT = SPACES AND CLM-LOSS-DT(5:1) NOT = '-'
027100         MOVE 'LOSS_DT BAD DATE' TO ERR-TEXT
027200         ADD 1 TO WS-REJECT-CNT
027300     END-IF
027400     IF CLM-CHANNEL-CD NOT = 'PH' AND CLM-CHANNEL-CD NOT = 'WB'
027500         AND CLM-CHANNEL-CD NOT = 'AP' AND CLM-CHANNEL-CD NOT =
027600         'BR' AND CLM-CHANNEL-CD NOT = 'TL'
027700         ADD 1 TO WS-REJECT-CNT
027800         MOVE 'CHANNEL_CD INVALID' TO ERR-TEXT
027900     END-IF
028000     IF CLM-CLAIM-STATUS NOT = 'OP' AND CLM-CLAIM-STATUS NOT =
028100         'CS' AND CLM-CLAIM-STATUS NOT = 'CN' AND CLM-CLAIM-STATUS
028200         NOT = 'RO' AND CLM-CLAIM-STATUS NOT = 'RC'
028300         ADD 1 TO WS-REJECT-CNT
028400         MOVE 'CLAIM_STATUS INVALID' TO ERR-TEXT
028500     END-IF
028600     IF CLM-TIER-CD NOT = '1' AND CLM-TIER-CD NOT = '2' AND
028700         CLM-TIER-CD NOT = '3'
028800         ADD 1 TO WS-REJECT-CNT
028900         MOVE 'TIER_CD INVALID' TO ERR-TEXT
029000     END-IF
029100     .
029200* ---------------------------------------------------------------*
029300* 9000-RETURN                                                    *
029400* RETURN TO CICS                                                 *
029500* ---------------------------------------------------------------*
029600 9000-RETURN.
029700     MOVE CLR-COMMAREA TO DFHCOMMAREA
029800     EXEC CICS RETURN END-EXEC
029900     .
030000* ---------------------------------------------------------------*
030100* 8000-SQL-ERROR                                                 *
030200* UNEXPECTED SQLCODE                                             *
030300* ---------------------------------------------------------------*
030400 8000-SQL-ERROR.
030500     MOVE SQLCODE TO ERR-SQLCODE WS-SQLCODE-DSP
030600     MOVE WS-PGM-ID TO ERR-PGM
030700     STRING 'SQLCODE ' WS-SQLCODE-DSP DELIMITED BY SIZE INTO
030800         ERR-TEXT
030900     CALL 'CLRCM050' USING CLR-ERROR-BLOCK
031000     EXEC CICS SYNCPOINT ROLLBACK END-EXEC
031100     MOVE 16 TO CA-RETURN-CD
031200     MOVE ERR-TEXT TO CA-MSG
031300     PERFORM 9000-RETURN
031400     .

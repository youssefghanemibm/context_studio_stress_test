000100* ===============================================================*
000200* PROGRAM    : CLRRC060                                          *
000300* TITLE      : SOLICITOR INSTRUCTION (QUARRYHILL SOLICITORS,     *
000400*              CLX-IF-025)                                       *
000500* SYSTEM     : CLARA - CLAIMS LEDGER AND RESERVE APPLICATION     *
000600* AREA       : RECOVER                                           *
000700* TYPE       : CICS ONLINE / DB2                                 *
000800* TRANSACTION: RC06                                              *
000900* ---------------------------------------------------------------*
001000* PURPOSE                                                        *
001100*   CICS PSEUDO-CONVERSATIONAL PROGRAM - SOLICITOR INSTRUCTION   *
001200*     (QUARRYHILL SOLICITORS, CLX-IF-025).                       *
001300*   COMMAREA LAYOUT: CLRCOMM1.                                   *
001400*   INVOKED WITH A COMMAREA; RESULTS RETURNED IN                 *
001500*     CA-RETURN-CD/CA-MSG.                                       *
001600* ---------------------------------------------------------------*
001700* DB2 TABLES                                                     *
001800*   CLR.T_CLAIM                 READ                             *
001900*   CLR.T_SUBROGATION_CASE      READ                             *
002000*   CLR.T_LITIGATION            INSERT                           *
002100* COPYBOOKS  : CLRCLM01 LITREC01 SUBCAS01 CLRERR01 CLRCOMM1      *
002200* CALLS      : CLRCM050                                          *
002300* ---------------------------------------------------------------*
002400* MAINTENANCE HISTORY                                            *
002500* DATE       BY       REF        DESCRIPTION                     *
002600* ---------- -------- ---------- ------------------------------- *
002700* 2017-05-01 KBARR01             INITIAL VERSION                 *
002800* ===============================================================*
002900 IDENTIFICATION DIVISION.
003000 PROGRAM-ID.    CLRRC060.
003100 AUTHOR.        K. BARRACLOUGH.
003200 INSTALLATION.  CORVANE MUTUAL - CLAIMS SYSTEMS.
003300 DATE-WRITTEN.  2017-05-01.
003400 DATE-COMPILED.
003500 ENVIRONMENT DIVISION.
003600 CONFIGURATION SECTION.
003700 SOURCE-COMPUTER.  IBM-Z.
003800 OBJECT-COMPUTER.  IBM-Z.
003900 DATA DIVISION.
004000 WORKING-STORAGE SECTION.
004100*
004200 01  WS-PROGRAM-INFO.
004300     05  WS-PGM-ID               PIC X(8)   VALUE 'CLRRC060'.
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
005900     05  WS-CLAIM-READ           PIC S9(9)  COMP-3 VALUE ZERO.
006000     05  WS-SUBROGATION-CASE-READPIC S9(9)  COMP-3 VALUE ZERO.
006100     05  WS-LITIGATION-WRITTEN   PIC S9(9)  COMP-3 VALUE ZERO.
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
007400 COPY CLRCLM01.
007500 COPY LITREC01.
007600 COPY SUBCAS01.
007700 COPY CLRERR01.
007800 COPY CLRCOMM1.
007900*
008000 01  WS-AID-VALUES.
008100     05  AID-ENTER               PIC X      VALUE X'7D'.
008200     05  AID-CLEAR               PIC X      VALUE X'6D'.
008300     05  AID-PF3                 PIC X      VALUE X'F3'.
008400     05  AID-PF7                 PIC X      VALUE X'F7'.
008500     05  AID-PF8                 PIC X      VALUE X'F8'.
008600     05  AID-PF12                PIC X      VALUE X'7C'.
008700     05  WS-RESP                 PIC S9(8)  COMP VALUE ZERO.
008800 LINKAGE SECTION.
008900 01  DFHCOMMAREA                 PIC X(105).
009000 PROCEDURE DIVISION.
009100* ---------------------------------------------------------------*
009200* 0000-MAIN                                                      *
009300* PSEUDO-CONVERSATIONAL CONTROL                                  *
009400* ---------------------------------------------------------------*
009500 0000-MAIN.
009600     EXEC CICS ASSIGN USERID(WS-USER-ID) END-EXEC
009700     IF EIBCALEN = ZERO
009800         INITIALIZE CLR-COMMAREA
009900         MOVE 'RC06' TO CA-TRANID
010000         MOVE 12 TO CA-RETURN-CD
010100         MOVE 'NO COMMAREA SUPPLIED' TO CA-MSG
010200         PERFORM 9000-RETURN
010300     ELSE
010400         MOVE DFHCOMMAREA TO CLR-COMMAREA
010500         PERFORM 2000-PROCESS-INPUT
010600     END-IF
010700     PERFORM 9000-RETURN
010800     GOBACK.
010900* ---------------------------------------------------------------*
011000* 2000-PROCESS-INPUT                                             *
011100* INPUT PROCESSING                                               *
011200* ---------------------------------------------------------------*
011300 2000-PROCESS-INPUT.
011400     PERFORM 2100-EDIT-INPUT
011500     IF WS-NO-ERROR
011600         PERFORM 2200-APPLY
011700     END-IF
011800     .
011900* ---------------------------------------------------------------*
012000* 2100-EDIT-INPUT                                                *
012100* VALIDATE THE REQUEST                                           *
012200* ---------------------------------------------------------------*
012300 2100-EDIT-INPUT.
012400     SET WS-NO-ERROR TO TRUE
012500     IF CA-CLAIM-ID = SPACES OR LOW-VALUES
012600         SET WS-ERROR-FOUND TO TRUE
012700         MOVE 8 TO CA-RETURN-CD
012800         MOVE 'CLAIM ID IS REQUIRED' TO CA-MSG
012900     END-IF
013000     .
013100* ---------------------------------------------------------------*
013200* 2200-APPLY                                                     *
013300* CARRY OUT THE REQUEST                                          *
013400* ---------------------------------------------------------------*
013500 2200-APPLY.
013600     PERFORM 2300-READ-CLAIM
013700     PERFORM 2320-READ-SUBR-CASE
013800     PERFORM 2500-EDIT-CLAIM
013900     PERFORM 2510-EDIT-SUBR-CASE
014000     PERFORM 2520-EDIT-LITIGATION
014100     PERFORM 4100-INSERT-LITIGATION
014200     IF WS-NO-ERROR
014300         EXEC CICS SYNCPOINT END-EXEC
014400         MOVE ZERO TO CA-RETURN-CD
014500     END-IF
014600     .
014700* ---------------------------------------------------------------*
014800* 2300-READ-CLAIM                                                *
014900* LOOK UP CLR.T_CLAIM                                            *
015000* ---------------------------------------------------------------*
015100 2300-READ-CLAIM.
015200     MOVE CA-CLAIM-ID TO CLM-CLAIM-ID
015300     SET WS-ROW-FOUND TO TRUE
015400     EXEC SQL
015500         SELECT CLAIM_ID, POLICY_NO, PRODUCT_CD, PERIL_CD
015600                , LOSS_DT
015700           INTO :CLM-CLAIM-ID, :CLM-POLICY-NO
015800                , :CLM-PRODUCT-CD, :CLM-PERIL-CD
015900                , :CLM-LOSS-DT
016000           FROM CLR.T_CLAIM
016100          WHERE CLAIM_ID = :CLM-CLAIM-ID
016200     END-EXEC
016300     EVALUATE SQLCODE
016400         WHEN 0
016500             ADD 1 TO WS-CLAIM-READ
016600         WHEN +100
016700             SET WS-ROW-NOT-FOUND TO TRUE
016800         WHEN OTHER
016900             MOVE 'READ CLR.T_CLAIM' TO ERR-PARA
017000             PERFORM 8000-SQL-ERROR
017100     END-EVALUATE
017200     .
017300* ---------------------------------------------------------------*
017400* 2320-READ-SUBR-CASE                                            *
017500* READ CLR.T_SUBROGATION_CASE                                    *
017600* ---------------------------------------------------------------*
017700 2320-READ-SUBR-CASE.
017800     SET WS-ROW-FOUND TO TRUE
017900     EXEC SQL
018000         SELECT SUBRO_CASE_ID, CLAIM_ID, TP_INSURER_NAME
018100                , TP_REF, DEMAND_AMT
018200           INTO :SUBC-SUBRO-CASE-ID, :SUBC-CLAIM-ID
018300                , :SUBC-TP-INSURER-NAME, :SUBC-TP-REF
018400                , :SUBC-DEMAND-AMT
018500           FROM CLR.T_SUBROGATION_CASE
018600          WHERE SUBRO_CASE_ID = :SUBC-SUBRO-CASE-ID
018700     END-EXEC
018800     EVALUATE SQLCODE
018900         WHEN 0
019000             ADD 1 TO WS-SUBROGATION-CASE-READ
019100         WHEN +100
019200             SET WS-ROW-NOT-FOUND TO TRUE
019300         WHEN OTHER
019400             MOVE 'READ CLR.T_SUBROGATION_CASE' TO ERR-PARA
019500             PERFORM 8000-SQL-ERROR
019600     END-EVALUATE
019700     .
019800* ---------------------------------------------------------------*
019900* 2500-EDIT-CLAIM                                                *
020000* CHECK MANDATORY FIELDS IN CLR.T_CLAIM                          *
020100* ---------------------------------------------------------------*
020200 2500-EDIT-CLAIM.
020300     IF CLM-CLAIM-ID = SPACES OR LOW-VALUES
020400         ADD 1 TO WS-REJECT-CNT
020500         MOVE 'CLAIM_ID MISSING' TO ERR-TEXT
020600     END-IF
020700     IF CLM-POLICY-NO = SPACES OR LOW-VALUES
020800         ADD 1 TO WS-REJECT-CNT
020900         MOVE 'POLICY_NO MISSING' TO ERR-TEXT
021000     END-IF
021100     IF CLM-PRODUCT-CD = SPACES OR LOW-VALUES
021200         ADD 1 TO WS-REJECT-CNT
021300         MOVE 'PRODUCT_CD MISSING' TO ERR-TEXT
021400     END-IF
021500     IF CLM-PERIL-CD = SPACES OR LOW-VALUES
021600         ADD 1 TO WS-REJECT-CNT
021700         MOVE 'PERIL_CD MISSING' TO ERR-TEXT
021800     END-IF
021900     IF CLM-LOSS-DT NOT = SPACES AND CLM-LOSS-DT(5:1) NOT = '-'
022000         MOVE 'LOSS_DT BAD DATE' TO ERR-TEXT
022100         ADD 1 TO WS-REJECT-CNT
022200     END-IF
022300     IF CLM-CHANNEL-CD NOT = 'PH' AND CLM-CHANNEL-CD NOT = 'WB'
022400         AND CLM-CHANNEL-CD NOT = 'AP' AND CLM-CHANNEL-CD NOT =
022500         'BR' AND CLM-CHANNEL-CD NOT = 'TL'
022600         ADD 1 TO WS-REJECT-CNT
022700         MOVE 'CHANNEL_CD INVALID' TO ERR-TEXT
022800     END-IF
022900     IF CLM-CLAIM-STATUS NOT = 'OP' AND CLM-CLAIM-STATUS NOT =
023000         'CS' AND CLM-CLAIM-STATUS NOT = 'CN' AND CLM-CLAIM-STATUS
023100         NOT = 'RO' AND CLM-CLAIM-STATUS NOT = 'RC'
023200         ADD 1 TO WS-REJECT-CNT
023300         MOVE 'CLAIM_STATUS INVALID' TO ERR-TEXT
023400     END-IF
023500     IF CLM-TIER-CD NOT = '1' AND CLM-TIER-CD NOT = '2' AND
023600         CLM-TIER-CD NOT = '3'
023700         ADD 1 TO WS-REJECT-CNT
023800         MOVE 'TIER_CD INVALID' TO ERR-TEXT
023900     END-IF
024000     .
024100* ---------------------------------------------------------------*
024200* 2510-EDIT-SUBR-CASE                                            *
024300* VALIDATE CLR.T_SUBROGATION_CASE                                *
024400* ---------------------------------------------------------------*
024500 2510-EDIT-SUBR-CASE.
024600     IF SUBC-SUBRO-CASE-ID = SPACES OR LOW-VALUES
024700         ADD 1 TO WS-REJECT-CNT
024800         MOVE 'SUBRO_CASE_ID MISSING' TO ERR-TEXT
024900     END-IF
025000     IF SUBC-CLAIM-ID = SPACES OR LOW-VALUES
025100         ADD 1 TO WS-REJECT-CNT
025200         MOVE 'CLAIM_ID MISSING' TO ERR-TEXT
025300     END-IF
025400     IF SUBC-TP-INSURER-NAME = SPACES OR LOW-VALUES
025500         ADD 1 TO WS-REJECT-CNT
025600         MOVE 'TP_INSURER_NAME MISSING' TO ERR-TEXT
025700     END-IF
025800     IF SUBC-DEMAND-AMT NOT NUMERIC
025900         MOVE ZERO TO SUBC-DEMAND-AMT
026000         ADD 1 TO WS-REJECT-CNT
026100     END-IF
026200     .
026300* ---------------------------------------------------------------*
026400* 2520-EDIT-LITIGATION                                           *
026500* CHECK MANDATORY FIELDS IN CLR.T_LITIGATION                     *
026600* ---------------------------------------------------------------*
026700 2520-EDIT-LITIGATION.
026800     IF LITR-CLAIM-ID = SPACES OR LOW-VALUES
026900         ADD 1 TO WS-REJECT-CNT
027000         MOVE 'CLAIM_ID MISSING' TO ERR-TEXT
027100     END-IF
027200     IF LITR-SOLICITOR-VENDOR-CD = SPACES OR LOW-VALUES
027300         ADD 1 TO WS-REJECT-CNT
027400         MOVE 'SOLICITOR_VENDOR_C MISSING' TO ERR-TEXT
027500     END-IF
027600     IF LITR-INSTRUCTED-DT NOT = SPACES AND
027700         LITR-INSTRUCTED-DT(5:1) NOT = '-'
027800         MOVE 'INSTRUCTED_DT BAD DATE' TO ERR-TEXT
027900         ADD 1 TO WS-REJECT-CNT
028000     END-IF
028100     .
028200* ---------------------------------------------------------------*
028300* 4100-INSERT-LITIGATION                                         *
028400* INSERT CLR.T_LITIGATION                                        *
028500* ---------------------------------------------------------------*
028600 4100-INSERT-LITIGATION.
028700     MOVE CA-CLAIM-ID TO LITR-CLAIM-ID
028800     EXEC SQL
028900         INSERT INTO CLR.T_LITIGATION
029000              ( CLAIM_ID, SOLICITOR_VENDOR_CD, INSTRUCTED_DT
029100              , COURT_REF, LIT_STATUS, BRANCH_CD, CREATED_TS
029200              , EXT_REF, LAST_UPD_TS, LAST_UPD_PGM
029300              , LAST_UPD_USER )
029400         VALUES
029500              ( :LITR-CLAIM-ID, :LITR-SOLICITOR-VENDOR-CD
029600              , :LITR-INSTRUCTED-DT, :LITR-COURT-REF
029700              , :LITR-LIT-STATUS, :LITR-BRANCH-CD
029800              , CURRENT TIMESTAMP, :LITR-EXT-REF
029900              , CURRENT TIMESTAMP, :WS-PGM-ID, :WS-USER-ID )
030000     END-EXEC
030100     EVALUATE SQLCODE
030200         WHEN 0
030300             ADD 1 TO WS-LITIGATION-WRITTEN
030400         WHEN +100
030500             SET WS-ROW-NOT-FOUND TO TRUE
030600         WHEN OTHER
030700             MOVE 'INSERT CLR.T_LITIGATION' TO ERR-PARA
030800             PERFORM 8000-SQL-ERROR
030900     END-EVALUATE
031000     .
031100* ---------------------------------------------------------------*
031200* 9000-RETURN                                                    *
031300* RETURN TO CICS                                                 *
031400* ---------------------------------------------------------------*
031500 9000-RETURN.
031600     MOVE CLR-COMMAREA TO DFHCOMMAREA
031700     EXEC CICS RETURN END-EXEC
031800     .
031900* ---------------------------------------------------------------*
032000* 8000-SQL-ERROR                                                 *
032100* SEVERE ERROR - REPORT AND STOP                                 *
032200* ---------------------------------------------------------------*
032300 8000-SQL-ERROR.
032400     MOVE SQLCODE TO ERR-SQLCODE WS-SQLCODE-DSP
032500     MOVE WS-PGM-ID TO ERR-PGM
032600     STRING 'SQLCODE ' WS-SQLCODE-DSP DELIMITED BY SIZE INTO
032700         ERR-TEXT
032800     CALL 'CLRCM050' USING CLR-ERROR-BLOCK
032900     EXEC CICS SYNCPOINT ROLLBACK END-EXEC
033000     MOVE 16 TO CA-RETURN-CD
033100     MOVE ERR-TEXT TO CA-MSG
033200     PERFORM 9000-RETURN
033300     .

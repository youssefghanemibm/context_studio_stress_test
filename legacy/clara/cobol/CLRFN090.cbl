000100* ================================================================
000200* PROGRAM    : CLRFN090
000300* TITLE      : FNOL AMEND AND REOPEN
000400* SYSTEM     : CLARA - CLAIMS LEDGER AND RESERVE APPLICATION
000500* AREA       : FNOL
000600* TYPE       : CICS ONLINE / DB2
000700* TRANSACTION: FN09
000800* ----------------------------------------------------------------
000900* PURPOSE
001000*   CICS PSEUDO-CONVERSATIONAL PROGRAM - FNOL AMEND AND REOPEN.
001100*   COMMAREA LAYOUT: CLRCOMM1.
001200*   INVOKED WITH A COMMAREA; RESULTS RETURNED IN
001300*     CA-RETURN-CD/CA-MSG.
001400* ----------------------------------------------------------------
001500* DB2 TABLES
001600*   CLR.T_CLAIMANT              READ
001700*   CLR.T_FNOL_EVENT            READ
001800*   CLR.T_CLAIM                 UPDATE
001900* COPYBOOKS  : CLRCLM01 CLRCLT01 CLRFNL01 CLRERR01 CLRCOMM1
002000* CALLS      : CLRCM050
002100* ----------------------------------------------------------------
002200* MAINTENANCE HISTORY
002300* DATE       BY       REF        DESCRIPTION
002400* ---------- -------- ---------- -------------------------------
002500* 2007-08-01 PASHW01             INITIAL VERSION
002600* 2014-07-26 KBARR01             ERROR MESSAGES STANDARDISED
002700* ================================================================
002800 IDENTIFICATION DIVISION.
002900 PROGRAM-ID.    CLRFN090.
003000 AUTHOR.        P. ASHWORTH.
003100 INSTALLATION.  CORVANE MUTUAL - CLAIMS SYSTEMS.
003200 DATE-WRITTEN.  2007-08-01.
003300 DATE-COMPILED.
003400 ENVIRONMENT DIVISION.
003500 CONFIGURATION SECTION.
003600 SOURCE-COMPUTER.  IBM-Z.
003700 OBJECT-COMPUTER.  IBM-Z.
003800 DATA DIVISION.
003900 WORKING-STORAGE SECTION.
004000*
004100 01  WS-PROGRAM-INFO.
004200     05  WS-PGM-ID               PIC X(8)   VALUE 'CLRFN090'.
004300     05  WS-RUN-DATE             PIC X(10)  VALUE SPACES.
004400     05  WS-RUN-TS               PIC X(26)  VALUE SPACES.
004500     05  WS-USER-ID              PIC X(8)   VALUE SPACES.
004600*
004700 01  WS-SWITCHES.
004800     05  WS-EOF-SW               PIC X      VALUE 'N'.
004900         88  WS-END-OF-DATA                     VALUE 'Y'.
005000     05  WS-ERROR-SW             PIC X      VALUE 'N'.
005100         88  WS-ERROR-FOUND                     VALUE 'Y'.
005200         88  WS-NO-ERROR                        VALUE 'N'.
005300     05  WS-FOUND-SW             PIC X      VALUE 'N'.
005400         88  WS-ROW-FOUND                       VALUE 'Y'.
005500         88  WS-ROW-NOT-FOUND                   VALUE 'N'.
005600*
005700 01  WS-COUNTERS.
005800     05  WS-CLAIMANT-READ        PIC S9(9)  COMP-3 VALUE ZERO.
005900     05  WS-FNOL-EVENT-READ      PIC S9(9)  COMP-3 VALUE ZERO.
006000     05  WS-CLAIM-WRITTEN        PIC S9(9)  COMP-3 VALUE ZERO.
006100     05  WS-REJECT-CNT           PIC S9(9)  COMP-3 VALUE ZERO.
006200*
006300 01  WS-SQL-WORK.
006400     05  WS-SQLCODE-DSP          PIC -9(9).
006500     05  WS-ROWS-AFFECTED        PIC S9(9)  COMP VALUE ZERO.
006600     05  WS-IND-1                PIC S9(4)  COMP VALUE ZERO.
006700     05  WS-IND-2                PIC S9(4)  COMP VALUE ZERO.
006800     05  WS-NEW-ID               PIC S9(18) COMP VALUE ZERO.
006900*
007000     EXEC SQL INCLUDE SQLCA END-EXEC.
007100*
007200* APPLICATION COPYBOOKS
007300 COPY CLRCLM01.
007400 COPY CLRCLT01.
007500 COPY CLRFNL01.
007600 COPY CLRERR01.
007700 COPY CLRCOMM1.
007800*
007900 01  WS-AID-VALUES.
008000     05  AID-ENTER               PIC X      VALUE X'7D'.
008100     05  AID-CLEAR               PIC X      VALUE X'6D'.
008200     05  AID-PF3                 PIC X      VALUE X'F3'.
008300     05  AID-PF7                 PIC X      VALUE X'F7'.
008400     05  AID-PF8                 PIC X      VALUE X'F8'.
008500     05  AID-PF12                PIC X      VALUE X'7C'.
008600     05  WS-RESP                 PIC S9(8)  COMP VALUE ZERO.
008700 LINKAGE SECTION.
008800 01  DFHCOMMAREA                 PIC X(105).
008900 PROCEDURE DIVISION.
009000* ---------------------------------------------------------------*
009100* 0000-MAIN                                                      *
009200* PSEUDO-CONVERSATIONAL CONTROL                                  *
009300* ---------------------------------------------------------------*
009400 0000-MAIN.
009500     EXEC CICS ASSIGN USERID(WS-USER-ID) END-EXEC
009600     IF EIBCALEN = ZERO
009700         INITIALIZE CLR-COMMAREA
009800         MOVE 'FN09' TO CA-TRANID
009900         MOVE 12 TO CA-RETURN-CD
010000         MOVE 'NO COMMAREA SUPPLIED' TO CA-MSG
010100         PERFORM 9000-RETURN
010200     ELSE
010300         MOVE DFHCOMMAREA TO CLR-COMMAREA
010400         PERFORM 2000-PROCESS-INPUT
010500     END-IF
010600     PERFORM 9000-RETURN
010700     GOBACK.
010800* ---------------------------------------------------------------*
010900* 2000-PROCESS-INPUT                                             *
011000* PROCESS THE REQUEST                                            *
011100* ---------------------------------------------------------------*
011200 2000-PROCESS-INPUT.
011300     PERFORM 2100-EDIT-INPUT
011400     IF WS-NO-ERROR
011500         PERFORM 2200-APPLY
011600     END-IF
011700     .
011800* ---------------------------------------------------------------*
011900* 2100-EDIT-INPUT                                                *
012000* VALIDATE THE REQUEST                                           *
012100* ---------------------------------------------------------------*
012200 2100-EDIT-INPUT.
012300     SET WS-NO-ERROR TO TRUE
012400     IF CA-CLAIM-ID = SPACES OR LOW-VALUES
012500         SET WS-ERROR-FOUND TO TRUE
012600         MOVE 8 TO CA-RETURN-CD
012700         MOVE 'CLAIM ID IS REQUIRED' TO CA-MSG
012800     END-IF
012900     .
013000* ---------------------------------------------------------------*
013100* 2200-APPLY                                                     *
013200* BUSINESS PROCESSING                                            *
013300* ---------------------------------------------------------------*
013400 2200-APPLY.
013500     PERFORM 2300-READ-CLAIMANT
013600     PERFORM 2320-READ-FNOL-EVENT
013700     PERFORM 2500-EDIT-CLAIMANT
013800     PERFORM 2510-EDIT-FNOL-EVENT
013900     PERFORM 2520-EDIT-CLAIM
014000     PERFORM 2530-EDIT-CLAIMANT-2
014100     PERFORM 2540-EDIT-FNOL-EVENT-2
014200     PERFORM 2550-EDIT-CLAIM-2
014300     PERFORM 2560-EDIT-CLAIMANT-3
014400     PERFORM 2570-EDIT-FNOL-EVENT-3
014500     PERFORM 2580-EDIT-CLAIM-3
014600     PERFORM 4100-UPDATE-CLAIM
014700     IF WS-NO-ERROR
014800         EXEC CICS SYNCPOINT END-EXEC
014900         MOVE ZERO TO CA-RETURN-CD
015000     END-IF
015100     .
015200* ---------------------------------------------------------------*
015300* 2300-READ-CLAIMANT                                             *
015400* FETCH CLR.T_CLAIMANT                                           *
015500* ---------------------------------------------------------------*
015600 2300-READ-CLAIMANT.
015700     SET WS-ROW-FOUND TO TRUE
015800     EXEC SQL
015900         SELECT CLAIMANT_ID, FAMILY_NAME, GIVEN_NAME, DOB
016000           INTO :CLT-CLAIMANT-ID, :CLT-FAMILY-NAME
016100                , :CLT-GIVEN-NAME, :CLT-DOB
016200           FROM CLR.T_CLAIMANT
016300          WHERE CLAIMANT_ID = :CLT-CLAIMANT-ID
016400     END-EXEC
016500     EVALUATE SQLCODE
016600         WHEN 0
016700             ADD 1 TO WS-CLAIMANT-READ
016800         WHEN +100
016900             SET WS-ROW-NOT-FOUND TO TRUE
017000         WHEN OTHER
017100             MOVE 'READ CLR.T_CLAIMANT' TO ERR-PARA
017200             PERFORM 8000-SQL-ERROR
017300     END-EVALUATE
017400     .
017500* ---------------------------------------------------------------*
017600* 2320-READ-FNOL-EVENT                                           *
017700* READ CLR.T_FNOL_EVENT                                          *
017800* ---------------------------------------------------------------*
017900 2320-READ-FNOL-EVENT.
018000     SET WS-ROW-FOUND TO TRUE
018100     EXEC SQL
018200         SELECT FNOL_ID, CLAIM_ID, CHANNEL_CD
018300           INTO :FNL-FNOL-ID, :FNL-CLAIM-ID, :FNL-CHANNEL-CD
018400           FROM CLR.T_FNOL_EVENT
018500          WHERE FNOL_ID = :FNL-FNOL-ID
018600     END-EXEC
018700     EVALUATE SQLCODE
018800         WHEN 0
018900             ADD 1 TO WS-FNOL-EVENT-READ
019000         WHEN +100
019100             SET WS-ROW-NOT-FOUND TO TRUE
019200         WHEN OTHER
019300             MOVE 'READ CLR.T_FNOL_EVENT' TO ERR-PARA
019400             PERFORM 8000-SQL-ERROR
019500     END-EVALUATE
019600     .
019700* ---------------------------------------------------------------*
019800* 2500-EDIT-CLAIMANT                                             *
019900* CHECK MANDATORY FIELDS IN CLR.T_CLAIMANT                       *
020000* ---------------------------------------------------------------*
020100 2500-EDIT-CLAIMANT.
020200     IF CLT-CLAIMANT-ID = SPACES OR LOW-VALUES
020300         ADD 1 TO WS-REJECT-CNT
020400         MOVE 'CLAIMANT_ID MISSING' TO ERR-TEXT
020500     END-IF
020600     IF CLT-FAMILY-NAME = SPACES OR LOW-VALUES
020700         ADD 1 TO WS-REJECT-CNT
020800         MOVE 'FAMILY_NAME MISSING' TO ERR-TEXT
020900     END-IF
021000     IF CLT-GIVEN-NAME = SPACES OR LOW-VALUES
021100         ADD 1 TO WS-REJECT-CNT
021200         MOVE 'GIVEN_NAME MISSING' TO ERR-TEXT
021300     END-IF
021400     IF CLT-DOB NOT = SPACES AND CLT-DOB(5:1) NOT = '-'
021500         MOVE 'DOB BAD DATE' TO ERR-TEXT
021600         ADD 1 TO WS-REJECT-CNT
021700     END-IF
021800     .
021900* ---------------------------------------------------------------*
022000* 2510-EDIT-FNOL-EVENT                                           *
022100* CHECK MANDATORY FIELDS IN CLR.T_FNOL_EVENT                     *
022200* ---------------------------------------------------------------*
022300 2510-EDIT-FNOL-EVENT.
022400     IF FNL-CHANNEL-CD = SPACES OR LOW-VALUES
022500         ADD 1 TO WS-REJECT-CNT
022600         MOVE 'CHANNEL_CD MISSING' TO ERR-TEXT
022700     END-IF
022800     .
022900* ---------------------------------------------------------------*
023000* 2520-EDIT-CLAIM                                                *
023100* FIELD EDITS FOR CLR.T_CLAIM                                    *
023200* ---------------------------------------------------------------*
023300 2520-EDIT-CLAIM.
023400     IF CLM-CLAIM-ID = SPACES OR LOW-VALUES
023500         ADD 1 TO WS-REJECT-CNT
023600         MOVE 'CLAIM_ID MISSING' TO ERR-TEXT
023700     END-IF
023800     IF CLM-POLICY-NO = SPACES OR LOW-VALUES
023900         ADD 1 TO WS-REJECT-CNT
024000         MOVE 'POLICY_NO MISSING' TO ERR-TEXT
024100     END-IF
024200     IF CLM-PRODUCT-CD = SPACES OR LOW-VALUES
024300         ADD 1 TO WS-REJECT-CNT
024400         MOVE 'PRODUCT_CD MISSING' TO ERR-TEXT
024500     END-IF
024600     IF CLM-PERIL-CD = SPACES OR LOW-VALUES
024700         ADD 1 TO WS-REJECT-CNT
024800         MOVE 'PERIL_CD MISSING' TO ERR-TEXT
024900     END-IF
025000     IF CLM-LOSS-DT NOT = SPACES AND CLM-LOSS-DT(5:1) NOT = '-'
025100         MOVE 'LOSS_DT BAD DATE' TO ERR-TEXT
025200         ADD 1 TO WS-REJECT-CNT
025300     END-IF
025400     IF CLM-CHANNEL-CD NOT = 'PH' AND CLM-CHANNEL-CD NOT = 'WB'
025500         AND CLM-CHANNEL-CD NOT = 'AP' AND CLM-CHANNEL-CD NOT =
025600         'BR' AND CLM-CHANNEL-CD NOT = 'TL'
025700         ADD 1 TO WS-REJECT-CNT
025800         MOVE 'CHANNEL_CD INVALID' TO ERR-TEXT
025900     END-IF
026000     IF CLM-CLAIM-STATUS NOT = 'OP' AND CLM-CLAIM-STATUS NOT =
026100         'CS' AND CLM-CLAIM-STATUS NOT = 'CN' AND CLM-CLAIM-STATUS
026200         NOT = 'RO' AND CLM-CLAIM-STATUS NOT = 'RC'
026300         ADD 1 TO WS-REJECT-CNT
026400         MOVE 'CLAIM_STATUS INVALID' TO ERR-TEXT
026500     END-IF
026600     IF CLM-TIER-CD NOT = '1' AND CLM-TIER-CD NOT = '2' AND
026700         CLM-TIER-CD NOT = '3'
026800         ADD 1 TO WS-REJECT-CNT
026900         MOVE 'TIER_CD INVALID' TO ERR-TEXT
027000     END-IF
027100     .
027200* ---------------------------------------------------------------*
027300* 2530-EDIT-CLAIMANT-2                                           *
027400* VALIDATE CLR.T_CLAIMANT                                        *
027500* ---------------------------------------------------------------*
027600 2530-EDIT-CLAIMANT-2.
027700     IF CLT-ADDR-LINE1 = SPACES OR LOW-VALUES
027800         ADD 1 TO WS-REJECT-CNT
027900         MOVE 'ADDR_LINE1 MISSING' TO ERR-TEXT
028000     END-IF
028100     IF CLT-POSTCODE = SPACES OR LOW-VALUES
028200         ADD 1 TO WS-REJECT-CNT
028300         MOVE 'POSTCODE MISSING' TO ERR-TEXT
028400     END-IF
028500     IF CLT-PARTY-ROLE-CD NOT = 'PH' AND CLT-PARTY-ROLE-CD NOT =
028600         'TP' AND CLT-PARTY-ROLE-CD NOT = 'WI'
028700         ADD 1 TO WS-REJECT-CNT
028800         MOVE 'PARTY_ROLE_CD INVALID' TO ERR-TEXT
028900     END-IF
029000     .
029100* ---------------------------------------------------------------*
029200* 2540-EDIT-FNOL-EVENT-2                                         *
029300* FIELD EDITS FOR CLR.T_FNOL_EVENT                               *
029400* ---------------------------------------------------------------*
029500 2540-EDIT-FNOL-EVENT-2.
029600* ---------------------------------------------------------------*
029700* 2550-EDIT-CLAIM-2                                              *
029800* VALIDATE CLR.T_CLAIM                                           *
029900* ---------------------------------------------------------------*
030000 2550-EDIT-CLAIM-2.
030100     IF CLM-REGION-CD NOT = 'UK' AND CLM-REGION-CD NOT = 'NO' AND
030200         CLM-REGION-CD NOT = 'SE' AND CLM-REGION-CD NOT = 'DK'
030300         ADD 1 TO WS-REJECT-CNT
030400         MOVE 'REGION_CD INVALID' TO ERR-TEXT
030500     END-IF
030600     IF CLM-CURRENCY-CD NOT = 'GBP' AND CLM-CURRENCY-CD NOT =
030700         'NOK' AND CLM-CURRENCY-CD NOT = 'SEK' AND CLM-CURRENCY-CD
030800         NOT = 'DKK'
030900         ADD 1 TO WS-REJECT-CNT
031000         MOVE 'CURRENCY_CD INVALID' TO ERR-TEXT
031100     END-IF
031200     IF CLM-CLAIMANT-ID = SPACES OR LOW-VALUES
031300         ADD 1 TO WS-REJECT-CNT
031400         MOVE 'CLAIMANT_ID MISSING' TO ERR-TEXT
031500     END-IF
031600     IF CLM-HANDLER-USER-ID = SPACES OR LOW-VALUES
031700         ADD 1 TO WS-REJECT-CNT
031800         MOVE 'HANDLER_USER_ID MISSING' TO ERR-TEXT
031900     END-IF
032000     IF CLM-FRAUD-FLAG NOT = 'Y' AND CLM-FRAUD-FLAG NOT = 'N'
032100         ADD 1 TO WS-REJECT-CNT
032200         MOVE 'FRAUD_FLAG INVALID' TO ERR-TEXT
032300     END-IF
032400     IF CLM-RECOVERY-FLAG NOT = 'Y' AND CLM-RECOVERY-FLAG NOT =
032500         'N'
032600         ADD 1 TO WS-REJECT-CNT
032700         MOVE 'RECOVERY_FLAG INVALID' TO ERR-TEXT
032800     END-IF
032900     IF CLM-LOSS-DESC = SPACES OR LOW-VALUES
033000         ADD 1 TO WS-REJECT-CNT
033100         MOVE 'LOSS_DESC MISSING' TO ERR-TEXT
033200     END-IF
033300     .
033400* ---------------------------------------------------------------*
033500* 2560-EDIT-CLAIMANT-3                                           *
033600* FIELD EDITS FOR CLR.T_CLAIMANT                                 *
033700* ---------------------------------------------------------------*
033800 2560-EDIT-CLAIMANT-3.
033900     IF CLT-VULNERABLE-FLAG = SPACES OR LOW-VALUES
034000         ADD 1 TO WS-REJECT-CNT
034100         MOVE 'VULNERABLE_FLAG MISSING' TO ERR-TEXT
034200     END-IF
034300     .
034400* ---------------------------------------------------------------*
034500* 2570-EDIT-FNOL-EVENT-3                                         *
034600* CHECK MANDATORY FIELDS IN CLR.T_FNOL_EVENT                     *
034700* ---------------------------------------------------------------*
034800 2570-EDIT-FNOL-EVENT-3.
034900* ---------------------------------------------------------------*
035000* 2580-EDIT-CLAIM-3                                              *
035100* VALIDATE CLR.T_CLAIM                                           *
035200* ---------------------------------------------------------------*
035300 2580-EDIT-CLAIM-3.
035400     IF CLM-CLOSED-DT NOT = SPACES AND CLM-CLOSED-DT(5:1) NOT =
035500         '-'
035600         MOVE 'CLOSED_DT BAD DATE' TO ERR-TEXT
035700         ADD 1 TO WS-REJECT-CNT
035800     END-IF
035900     .
036000* ---------------------------------------------------------------*
036100* 4100-UPDATE-CLAIM                                              *
036200* UPDATE CLR.T_CLAIM                                             *
036300* ---------------------------------------------------------------*
036400 4100-UPDATE-CLAIM.
036500     EXEC SQL
036600         UPDATE CLR.T_CLAIM
036700            SET LOSS_DT = :CLM-LOSS-DT
036800              , LOSS_DESC = :CLM-LOSS-DESC
036900              , CLAIM_STATUS = 'RO'
037000              , LAST_UPD_TS = CURRENT TIMESTAMP
037100              , LAST_UPD_PGM = :WS-PGM-ID
037200              , LAST_UPD_USER = :WS-USER-ID
037300          WHERE CLAIM_ID = :CA-CLAIM-ID
037400     END-EXEC
037500     EVALUATE SQLCODE
037600         WHEN 0
037700             ADD 1 TO WS-CLAIM-WRITTEN
037800         WHEN +100
037900             SET WS-ROW-NOT-FOUND TO TRUE
038000         WHEN OTHER
038100             MOVE 'UPDATE CLR.T_CLAIM' TO ERR-PARA
038200             PERFORM 8000-SQL-ERROR
038300     END-EVALUATE
038400     .
038500* ---------------------------------------------------------------*
038600* 9000-RETURN                                                    *
038700* RETURN TO CICS                                                 *
038800* ---------------------------------------------------------------*
038900 9000-RETURN.
039000     MOVE CLR-COMMAREA TO DFHCOMMAREA
039100     EXEC CICS RETURN END-EXEC
039200     .
039300* ---------------------------------------------------------------*
039400* 8000-SQL-ERROR                                                 *
039500* DB2 ERROR HANDLING                                             *
039600* ---------------------------------------------------------------*
039700 8000-SQL-ERROR.
039800     MOVE SQLCODE TO ERR-SQLCODE WS-SQLCODE-DSP
039900     MOVE WS-PGM-ID TO ERR-PGM
040000     STRING 'SQLCODE ' WS-SQLCODE-DSP DELIMITED BY SIZE INTO
040100         ERR-TEXT
040200     CALL 'CLRCM050' USING CLR-ERROR-BLOCK
040300     EXEC CICS SYNCPOINT ROLLBACK END-EXEC
040400     MOVE 16 TO CA-RETURN-CD
040500     MOVE ERR-TEXT TO CA-MSG
040600     PERFORM 9000-RETURN
040700     .

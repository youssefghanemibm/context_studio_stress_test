000100* ===============================================================*
000200* PROGRAM    : CLRST020                                          *
000300* TITLE      : PAYMENT REQUEST (BR-STL-002 AUTHORITY)            *
000400* SYSTEM     : CLARA - CLAIMS LEDGER AND RESERVE APPLICATION     *
000500* AREA       : SETTLE                                            *
000600* TYPE       : CICS ONLINE / DB2                                 *
000700* TRANSACTION: ST02                                              *
000800* ---------------------------------------------------------------*
000900* PURPOSE                                                        *
001000*   CICS PSEUDO-CONVERSATIONAL PROGRAM - PAYMENT REQUEST         *
001100*     (BR-STL-002 AUTHORITY).                                    *
001200*   PSEUDO-CONVERSATIONAL; STATE IS KEPT IN CLRCOMM1.            *
001300*   NO SCREEN OF ITS OWN - DRIVEN THROUGH THE COMMAREA.          *
001400* ---------------------------------------------------------------*
001500* DB2 TABLES                                                     *
001600*   CLR.T_CLAIM                 READ                             *
001700*   CLR.T_PAYEE                 READ                             *
001800*   CLR.T_VENDOR_INVOICE        READ                             *
001900*   CLR.T_PAYMENT               INSERT                           *
002000* COPYBOOKS  : CLRCLM01 PAYEE01 PAYREC01 VENINV01 CLRERR01       *
002100*              CLRCOMM1 CLRDATE1                                 *
002200* CALLS      : CLRCM050 CLRCM020 CLRCM070 CLRCM010               *
002300* ---------------------------------------------------------------*
002400* MAINTENANCE HISTORY                                            *
002500* DATE       BY       REF        DESCRIPTION                     *
002600* ---------- -------- ---------- ------------------------------- *
002700* 1994-10-03 CLRPROJ             INITIAL VERSION - CLARA GO-LIVE *
002800* 2017-05-29 DO                  ERROR MESSAGES STANDARDISED     *
002900* 2017-10-25 PASHW01             RECOMPILED UNDER ENTERPRISE     *
003000*                                COBOL V6                        *
003100* 2019-12-03 PASHW01             CURSOR POSITIONING ON           *
003200*                                VALIDATION ERRORS               *
003300* ===============================================================*
003400 IDENTIFICATION DIVISION.
003500 PROGRAM-ID.    CLRST020.
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
004800     05  WS-PGM-ID               PIC X(8)   VALUE 'CLRST020'.
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
006400     05  WS-CLAIM-READ           PIC S9(9)  COMP-3 VALUE ZERO.
006500     05  WS-PAYEE-READ           PIC S9(9)  COMP-3 VALUE ZERO.
006600     05  WS-VENDOR-INVOICE-READ  PIC S9(9)  COMP-3 VALUE ZERO.
006700     05  WS-PAYMENT-WRITTEN      PIC S9(9)  COMP-3 VALUE ZERO.
006800     05  WS-REJECT-CNT           PIC S9(9)  COMP-3 VALUE ZERO.
006900*
007000 01  WS-SQL-WORK.
007100     05  WS-SQLCODE-DSP          PIC -9(9).
007200     05  WS-ROWS-AFFECTED        PIC S9(9)  COMP VALUE ZERO.
007300     05  WS-IND-1                PIC S9(4)  COMP VALUE ZERO.
007400     05  WS-IND-2                PIC S9(4)  COMP VALUE ZERO.
007500     05  WS-NEW-ID               PIC S9(18) COMP VALUE ZERO.
007600*
007700     EXEC SQL INCLUDE SQLCA END-EXEC.
007800*
007900* APPLICATION COPYBOOKS
008000 COPY CLRCLM01.
008100 COPY PAYEE01.
008200 COPY PAYREC01.
008300 COPY VENINV01.
008400 COPY CLRERR01.
008500 COPY CLRCOMM1.
008600 COPY CLRDATE1.
008700*
008800* CALL INTERFACES
008900 01  WS-AUDIT-PARMS.
009000     05  WS-AUD-TABLE            PIC X(18).
009100     05  WS-AUD-KEY              PIC X(30).
009200     05  WS-AUD-ACTION           PIC X(1).
009300     05  WS-AUD-USER             PIC X(8).
009400     05  WS-AUD-PGM              PIC X(8).
009500 01  WS-AUTH-PARMS.
009600     05  WS-AUTH-USER            PIC X(8).
009700     05  WS-AUTH-FUNCTION        PIC X(8).
009800     05  WS-AUTH-ALLOWED         PIC X(1).
009900*
010000 01  WS-AID-VALUES.
010100     05  AID-ENTER               PIC X      VALUE X'7D'.
010200     05  AID-CLEAR               PIC X      VALUE X'6D'.
010300     05  AID-PF3                 PIC X      VALUE X'F3'.
010400     05  AID-PF7                 PIC X      VALUE X'F7'.
010500     05  AID-PF8                 PIC X      VALUE X'F8'.
010600     05  AID-PF12                PIC X      VALUE X'7C'.
010700     05  WS-RESP                 PIC S9(8)  COMP VALUE ZERO.
010800 LINKAGE SECTION.
010900 01  DFHCOMMAREA                 PIC X(105).
011000 PROCEDURE DIVISION.
011100* ---------------------------------------------------------------*
011200* 0000-MAIN                                                      *
011300* PSEUDO-CONVERSATIONAL CONTROL                                  *
011400* ---------------------------------------------------------------*
011500 0000-MAIN.
011600     EXEC CICS ASSIGN USERID(WS-USER-ID) END-EXEC
011700     IF EIBCALEN = ZERO
011800         INITIALIZE CLR-COMMAREA
011900         MOVE 'ST02' TO CA-TRANID
012000         MOVE 12 TO CA-RETURN-CD
012100         MOVE 'NO COMMAREA SUPPLIED' TO CA-MSG
012200         PERFORM 9000-RETURN
012300     ELSE
012400         MOVE DFHCOMMAREA TO CLR-COMMAREA
012500         PERFORM 2000-PROCESS-INPUT
012600     END-IF
012700     PERFORM 9000-RETURN
012800     GOBACK.
012900* ---------------------------------------------------------------*
013000* 2000-PROCESS-INPUT                                             *
013100* PROCESS THE REQUEST                                            *
013200* ---------------------------------------------------------------*
013300 2000-PROCESS-INPUT.
013400     PERFORM 2100-EDIT-INPUT
013500     IF WS-NO-ERROR
013600         PERFORM 2200-APPLY
013700     END-IF
013800     .
013900* ---------------------------------------------------------------*
014000* 2100-EDIT-INPUT                                                *
014100* VALIDATE THE REQUEST                                           *
014200* ---------------------------------------------------------------*
014300 2100-EDIT-INPUT.
014400     SET WS-NO-ERROR TO TRUE
014500     IF CA-CLAIM-ID = SPACES OR LOW-VALUES
014600         SET WS-ERROR-FOUND TO TRUE
014700         MOVE 8 TO CA-RETURN-CD
014800         MOVE 'CLAIM ID IS REQUIRED' TO CA-MSG
014900     END-IF
015000     PERFORM 1400-GET-BUSINESS-DATE
015100     PERFORM 1500-CHECK-AUTHORITY
015200     .
015300* ---------------------------------------------------------------*
015400* 1400-GET-BUSINESS-DATE                                         *
015500* DETERMINE PROCESSING DATE                                      *
015600* ---------------------------------------------------------------*
015700 1400-GET-BUSINESS-DATE.
015800     MOVE WS-RUN-DATE TO DW-IN-DATE
015900     MOVE CLM-REGION-CD TO DW-CALENDAR
016000     MOVE ZERO TO DW-BUS-DAYS
016100     CALL 'CLRCM010' USING CLR-DATE-WORK
016200                      CLR-ERROR-BLOCK
016300     IF ERR-SQLCODE NOT = ZERO
016400         MOVE 'CALL CLRCM010' TO ERR-PARA
016500         PERFORM 8000-SQL-ERROR
016600     END-IF
016700     .
016800* ---------------------------------------------------------------*
016900* 1500-CHECK-AUTHORITY                                           *
017000* CONFIRM THE USER MAY RUN THIS FUNCTION                         *
017100* ---------------------------------------------------------------*
017200 1500-CHECK-AUTHORITY.
017300     MOVE WS-USER-ID TO WS-AUTH-USER
017400     MOVE 'CLRST020' TO WS-AUTH-FUNCTION
017500     CALL 'CLRCM070' USING WS-AUTH-PARMS
017600                      CLR-ERROR-BLOCK
017700     IF ERR-SQLCODE NOT = ZERO
017800         MOVE 'CALL CLRCM070' TO ERR-PARA
017900         PERFORM 8000-SQL-ERROR
018000     END-IF
018100     IF WS-AUTH-ALLOWED NOT = 'Y'
018200         SET WS-ERROR-FOUND TO TRUE
018300         MOVE 8 TO CA-RETURN-CD
018400         MOVE 'NOT AUTHORISED FOR THIS FUNCTION' TO CA-MSG
018500     END-IF
018600     .
018700* ---------------------------------------------------------------*
018800* 2200-APPLY                                                     *
018900* APPLY THE CHANGE                                               *
019000* ---------------------------------------------------------------*
019100 2200-APPLY.
019200     PERFORM 2300-READ-CLAIM
019300     PERFORM 2320-READ-PAYEE
019400     PERFORM 2340-READ-VEND-INVO
019500     PERFORM 2500-EDIT-CLAIM
019600     PERFORM 2510-EDIT-PAYEE
019700     PERFORM 2520-EDIT-VEND-INVO
019800     PERFORM 2530-EDIT-PAYMENT
019900     PERFORM 2540-EDIT-CLAIM-2
020000     PERFORM 2550-EDIT-PAYEE-2
020100     PERFORM 2560-EDIT-VEND-INVO-2
020200     PERFORM 2570-EDIT-PAYMENT-2
020300     PERFORM 2580-EDIT-CLAIM-3
020400     PERFORM 2590-EDIT-PAYEE-3
020500     PERFORM 2600-EDIT-PAYMENT-3
020600     PERFORM 4100-INSERT-PAYMENT
020700     PERFORM 4900-WRITE-AUDIT
020800     IF WS-NO-ERROR
020900         EXEC CICS SYNCPOINT END-EXEC
021000         MOVE ZERO TO CA-RETURN-CD
021100     END-IF
021200     .
021300* ---------------------------------------------------------------*
021400* 2300-READ-CLAIM                                                *
021500* LOOK UP CLR.T_CLAIM                                            *
021600* ---------------------------------------------------------------*
021700 2300-READ-CLAIM.
021800     MOVE CA-CLAIM-ID TO CLM-CLAIM-ID
021900     SET WS-ROW-FOUND TO TRUE
022000     EXEC SQL
022100         SELECT CLAIM_ID, POLICY_NO, PRODUCT_CD, PERIL_CD
022200           INTO :CLM-CLAIM-ID, :CLM-POLICY-NO
022300                , :CLM-PRODUCT-CD, :CLM-PERIL-CD
022400           FROM CLR.T_CLAIM
022500          WHERE CLAIM_ID = :CLM-CLAIM-ID
022600     END-EXEC
022700     EVALUATE SQLCODE
022800         WHEN 0
022900             ADD 1 TO WS-CLAIM-READ
023000         WHEN +100
023100             SET WS-ROW-NOT-FOUND TO TRUE
023200         WHEN OTHER
023300             MOVE 'READ CLR.T_CLAIM' TO ERR-PARA
023400             PERFORM 8000-SQL-ERROR
023500     END-EVALUATE
023600     .
023700* ---------------------------------------------------------------*
023800* 2320-READ-PAYEE                                                *
023900* READ CLR.T_PAYEE                                               *
024000* ---------------------------------------------------------------*
024100 2320-READ-PAYEE.
024200     SET WS-ROW-FOUND TO TRUE
024300     EXEC SQL
024400         SELECT PAYEE_ID, PAYEE_NAME, IBAN, SORT_CODE
024500                , PAYEE_TYPE_CD, CREATED_TS
024600           INTO :PAYE-PAYEE-ID, :PAYE-PAYEE-NAME, :PAYE-IBAN
024700                , :PAYE-SORT-CODE, :PAYE-PAYEE-TYPE-CD
024800                , :PAYE-CREATED-TS
024900           FROM CLR.T_PAYEE
025000          WHERE PAYEE_ID = :PAYE-PAYEE-ID
025100     END-EXEC
025200     EVALUATE SQLCODE
025300         WHEN 0
025400             ADD 1 TO WS-PAYEE-READ
025500         WHEN +100
025600             SET WS-ROW-NOT-FOUND TO TRUE
025700         WHEN OTHER
025800             MOVE 'READ CLR.T_PAYEE' TO ERR-PARA
025900             PERFORM 8000-SQL-ERROR
026000     END-EVALUATE
026100     .
026200* ---------------------------------------------------------------*
026300* 2340-READ-VEND-INVO                                            *
026400* FETCH CLR.T_VENDOR_INVOICE                                     *
026500* ---------------------------------------------------------------*
026600 2340-READ-VEND-INVO.
026700     SET WS-ROW-FOUND TO TRUE
026800     EXEC SQL
026900         SELECT INVOICE_ID, VENDOR_CD, CLAIM_ID
027000           INTO :VENI-INVOICE-ID, :VENI-VENDOR-CD
027100                , :VENI-CLAIM-ID
027200           FROM CLR.T_VENDOR_INVOICE
027300          WHERE INVOICE_ID = :VENI-INVOICE-ID
027400     END-EXEC
027500     EVALUATE SQLCODE
027600         WHEN 0
027700             ADD 1 TO WS-VENDOR-INVOICE-READ
027800         WHEN +100
027900             SET WS-ROW-NOT-FOUND TO TRUE
028000         WHEN OTHER
028100             MOVE 'READ CLR.T_VENDOR_INVOICE' TO ERR-PARA
028200             PERFORM 8000-SQL-ERROR
028300     END-EVALUATE
028400     .
028500* ---------------------------------------------------------------*
028600* 2500-EDIT-CLAIM                                                *
028700* FIELD EDITS FOR CLR.T_CLAIM                                    *
028800* ---------------------------------------------------------------*
028900 2500-EDIT-CLAIM.
029000     IF CLM-CLAIM-ID = SPACES OR LOW-VALUES
029100         ADD 1 TO WS-REJECT-CNT
029200         MOVE 'CLAIM_ID MISSING' TO ERR-TEXT
029300     END-IF
029400     IF CLM-POLICY-NO = SPACES OR LOW-VALUES
029500         ADD 1 TO WS-REJECT-CNT
029600         MOVE 'POLICY_NO MISSING' TO ERR-TEXT
029700     END-IF
029800     IF CLM-PRODUCT-CD = SPACES OR LOW-VALUES
029900         ADD 1 TO WS-REJECT-CNT
030000         MOVE 'PRODUCT_CD MISSING' TO ERR-TEXT
030100     END-IF
030200     IF CLM-PERIL-CD = SPACES OR LOW-VALUES
030300         ADD 1 TO WS-REJECT-CNT
030400         MOVE 'PERIL_CD MISSING' TO ERR-TEXT
030500     END-IF
030600     IF CLM-LOSS-DT NOT = SPACES AND CLM-LOSS-DT(5:1) NOT = '-'
030700         MOVE 'LOSS_DT BAD DATE' TO ERR-TEXT
030800         ADD 1 TO WS-REJECT-CNT
030900     END-IF
031000     IF CLM-CHANNEL-CD NOT = 'PH' AND CLM-CHANNEL-CD NOT = 'WB'
031100         AND CLM-CHANNEL-CD NOT = 'AP' AND CLM-CHANNEL-CD NOT =
031200         'BR' AND CLM-CHANNEL-CD NOT = 'TL'
031300         ADD 1 TO WS-REJECT-CNT
031400         MOVE 'CHANNEL_CD INVALID' TO ERR-TEXT
031500     END-IF
031600     IF CLM-CLAIM-STATUS NOT = 'OP' AND CLM-CLAIM-STATUS NOT =
031700         'CS' AND CLM-CLAIM-STATUS NOT = 'CN' AND CLM-CLAIM-STATUS
031800         NOT = 'RO' AND CLM-CLAIM-STATUS NOT = 'RC'
031900         ADD 1 TO WS-REJECT-CNT
032000         MOVE 'CLAIM_STATUS INVALID' TO ERR-TEXT
032100     END-IF
032200     IF CLM-TIER-CD NOT = '1' AND CLM-TIER-CD NOT = '2' AND
032300         CLM-TIER-CD NOT = '3'
032400         ADD 1 TO WS-REJECT-CNT
032500         MOVE 'TIER_CD INVALID' TO ERR-TEXT
032600     END-IF
032700     .
032800* ---------------------------------------------------------------*
032900* 2510-EDIT-PAYEE                                                *
033000* VALIDATE CLR.T_PAYEE                                           *
033100* ---------------------------------------------------------------*
033200 2510-EDIT-PAYEE.
033300     IF PAYE-PAYEE-ID = SPACES OR LOW-VALUES
033400         ADD 1 TO WS-REJECT-CNT
033500         MOVE 'PAYEE_ID MISSING' TO ERR-TEXT
033600     END-IF
033700     IF PAYE-PAYEE-NAME = SPACES OR LOW-VALUES
033800         ADD 1 TO WS-REJECT-CNT
033900         MOVE 'PAYEE_NAME MISSING' TO ERR-TEXT
034000     END-IF
034100     IF PAYE-IBAN = SPACES OR LOW-VALUES
034200         ADD 1 TO WS-REJECT-CNT
034300         MOVE 'IBAN MISSING' TO ERR-TEXT
034400     END-IF
034500     .
034600* ---------------------------------------------------------------*
034700* 2520-EDIT-VEND-INVO                                            *
034800* FIELD EDITS FOR CLR.T_VENDOR_INVOICE                           *
034900* ---------------------------------------------------------------*
035000 2520-EDIT-VEND-INVO.
035100     IF VENI-VENDOR-CD = SPACES OR LOW-VALUES
035200         ADD 1 TO WS-REJECT-CNT
035300         MOVE 'VENDOR_CD MISSING' TO ERR-TEXT
035400     END-IF
035500     IF VENI-CLAIM-ID = SPACES OR LOW-VALUES
035600         ADD 1 TO WS-REJECT-CNT
035700         MOVE 'CLAIM_ID MISSING' TO ERR-TEXT
035800     END-IF
035900     .
036000* ---------------------------------------------------------------*
036100* 2530-EDIT-PAYMENT                                              *
036200* VALIDATE CLR.T_PAYMENT                                         *
036300* ---------------------------------------------------------------*
036400 2530-EDIT-PAYMENT.
036500     IF PAYR-CLAIM-ID = SPACES OR LOW-VALUES
036600         ADD 1 TO WS-REJECT-CNT
036700         MOVE 'CLAIM_ID MISSING' TO ERR-TEXT
036800     END-IF
036900     IF PAYR-PAYEE-ID = SPACES OR LOW-VALUES
037000         ADD 1 TO WS-REJECT-CNT
037100         MOVE 'PAYEE_ID MISSING' TO ERR-TEXT
037200     END-IF
037300     IF PAYR-PAY-AMT NOT NUMERIC
037400         MOVE ZERO TO PAYR-PAY-AMT
037500         ADD 1 TO WS-REJECT-CNT
037600     END-IF
037700     .
037800* ---------------------------------------------------------------*
037900* 2540-EDIT-CLAIM-2                                              *
038000* VALIDATE CLR.T_CLAIM                                           *
038100* ---------------------------------------------------------------*
038200 2540-EDIT-CLAIM-2.
038300     IF CLM-REGION-CD NOT = 'UK' AND CLM-REGION-CD NOT = 'NO' AND
038400         CLM-REGION-CD NOT = 'SE' AND CLM-REGION-CD NOT = 'DK'
038500         ADD 1 TO WS-REJECT-CNT
038600         MOVE 'REGION_CD INVALID' TO ERR-TEXT
038700     END-IF
038800     IF CLM-CURRENCY-CD NOT = 'GBP' AND CLM-CURRENCY-CD NOT =
038900         'NOK' AND CLM-CURRENCY-CD NOT = 'SEK' AND CLM-CURRENCY-CD
039000         NOT = 'DKK'
039100         ADD 1 TO WS-REJECT-CNT
039200         MOVE 'CURRENCY_CD INVALID' TO ERR-TEXT
039300     END-IF
039400     IF CLM-CLAIMANT-ID = SPACES OR LOW-VALUES
039500         ADD 1 TO WS-REJECT-CNT
039600         MOVE 'CLAIMANT_ID MISSING' TO ERR-TEXT
039700     END-IF
039800     IF CLM-HANDLER-USER-ID = SPACES OR LOW-VALUES
039900         ADD 1 TO WS-REJECT-CNT
040000         MOVE 'HANDLER_USER_ID MISSING' TO ERR-TEXT
040100     END-IF
040200     IF CLM-FRAUD-FLAG NOT = 'Y' AND CLM-FRAUD-FLAG NOT = 'N'
040300         ADD 1 TO WS-REJECT-CNT
040400         MOVE 'FRAUD_FLAG INVALID' TO ERR-TEXT
040500     END-IF
040600     IF CLM-RECOVERY-FLAG NOT = 'Y' AND CLM-RECOVERY-FLAG NOT =
040700         'N'
040800         ADD 1 TO WS-REJECT-CNT
040900         MOVE 'RECOVERY_FLAG INVALID' TO ERR-TEXT
041000     END-IF
041100     IF CLM-LOSS-DESC = SPACES OR LOW-VALUES
041200         ADD 1 TO WS-REJECT-CNT
041300         MOVE 'LOSS_DESC MISSING' TO ERR-TEXT
041400     END-IF
041500     .
041600* ---------------------------------------------------------------*
041700* 2550-EDIT-PAYEE-2                                              *
041800* FIELD EDITS FOR CLR.T_PAYEE                                    *
041900* ---------------------------------------------------------------*
042000 2550-EDIT-PAYEE-2.
042100     IF PAYE-PAYEE-TYPE-CD = SPACES OR LOW-VALUES
042200         ADD 1 TO WS-REJECT-CNT
042300         MOVE 'PAYEE_TYPE_CD MISSING' TO ERR-TEXT
042400     END-IF
042500     .
042600* ---------------------------------------------------------------*
042700* 2560-EDIT-VEND-INVO-2                                          *
042800* CHECK MANDATORY FIELDS IN CLR.T_VENDOR_INVOICE                 *
042900* ---------------------------------------------------------------*
043000 2560-EDIT-VEND-INVO-2.
043100     IF VENI-INVOICE-AMT NOT NUMERIC
043200         MOVE ZERO TO VENI-INVOICE-AMT
043300         ADD 1 TO WS-REJECT-CNT
043400     END-IF
043500     IF VENI-FEE-TYPE-CD NOT = 'DK' AND VENI-FEE-TYPE-CD NOT =
043600         'SV' AND VENI-FEE-TYPE-CD NOT = 'HR'
043700         ADD 1 TO WS-REJECT-CNT
043800         MOVE 'FEE_TYPE_CD INVALID' TO ERR-TEXT
043900     END-IF
044000     IF VENI-MATCHED-FLAG = SPACES OR LOW-VALUES
044100         ADD 1 TO WS-REJECT-CNT
044200         MOVE 'MATCHED_FLAG MISSING' TO ERR-TEXT
044300     END-IF
044400     .
044500* ---------------------------------------------------------------*
044600* 2570-EDIT-PAYMENT-2                                            *
044700* FIELD EDITS FOR CLR.T_PAYMENT                                  *
044800* ---------------------------------------------------------------*
044900 2570-EDIT-PAYMENT-2.
045000     IF PAYR-CURRENCY-CD = SPACES OR LOW-VALUES
045100         ADD 1 TO WS-REJECT-CNT
045200         MOVE 'CURRENCY_CD MISSING' TO ERR-TEXT
045300     END-IF
045400     IF PAYR-PAY-STATUS NOT = 'RQ' AND PAYR-PAY-STATUS NOT = 'SC'
045500         AND PAYR-PAY-STATUS NOT = 'SN' AND PAYR-PAY-STATUS NOT =
045600         'CF' AND PAYR-PAY-STATUS NOT = 'CX'
045700         ADD 1 TO WS-REJECT-CNT
045800         MOVE 'PAY_STATUS INVALID' TO ERR-TEXT
045900     END-IF
046000     IF PAYR-AUTH-USER = SPACES OR LOW-VALUES
046100         ADD 1 TO WS-REJECT-CNT
046200         MOVE 'AUTH_USER MISSING' TO ERR-TEXT
046300     END-IF
046400     IF PAYR-SANCTIONS-RESULT = SPACES OR LOW-VALUES
046500         ADD 1 TO WS-REJECT-CNT
046600         MOVE 'SANCTIONS_RESULT MISSING' TO ERR-TEXT
046700     END-IF
046800     .
046900* ---------------------------------------------------------------*
047000* 2580-EDIT-CLAIM-3                                              *
047100* FIELD EDITS FOR CLR.T_CLAIM                                    *
047200* ---------------------------------------------------------------*
047300 2580-EDIT-CLAIM-3.
047400     IF CLM-CLOSED-DT NOT = SPACES AND CLM-CLOSED-DT(5:1) NOT =
047500         '-'
047600         MOVE 'CLOSED_DT BAD DATE' TO ERR-TEXT
047700         ADD 1 TO WS-REJECT-CNT
047800     END-IF
047900     .
048000* ---------------------------------------------------------------*
048100* 2590-EDIT-PAYEE-3                                              *
048200* FIELD EDITS FOR CLR.T_PAYEE                                    *
048300* ---------------------------------------------------------------*
048400 2590-EDIT-PAYEE-3.
048500* ---------------------------------------------------------------*
048600* 2600-EDIT-PAYMENT-3                                            *
048700* VALIDATE CLR.T_PAYMENT                                         *
048800* ---------------------------------------------------------------*
048900 2600-EDIT-PAYMENT-3.
049000* ---------------------------------------------------------------*
049100* 4100-INSERT-PAYMENT                                            *
049200* INSERT CLR.T_PAYMENT                                           *
049300* ---------------------------------------------------------------*
049400 4100-INSERT-PAYMENT.
049500     MOVE CA-CLAIM-ID TO PAYR-CLAIM-ID
049600     MOVE 'RQ' TO PAYR-PAY-STATUS
049700     EXEC SQL
049800         INSERT INTO CLR.T_PAYMENT
049900              ( CLAIM_ID, PAYEE_ID, PAY_AMT, CURRENCY_CD
050000              , PAY_STATUS, AUTH_USER, SANCTIONS_RESULT
050100              , COMMENT_TXT, LAST_UPD_TS, LAST_UPD_PGM
050200              , LAST_UPD_USER )
050300         VALUES
050400              ( :PAYR-CLAIM-ID, :PAYR-PAYEE-ID, :PAYR-PAY-AMT
050500              , :PAYR-CURRENCY-CD, :PAYR-PAY-STATUS
050600              , :PAYR-AUTH-USER, :PAYR-SANCTIONS-RESULT
050700              , :PAYR-COMMENT-TXT, CURRENT TIMESTAMP
050800              , :WS-PGM-ID, :WS-USER-ID )
050900     END-EXEC
051000     EVALUATE SQLCODE
051100         WHEN 0
051200             ADD 1 TO WS-PAYMENT-WRITTEN
051300         WHEN +100
051400             SET WS-ROW-NOT-FOUND TO TRUE
051500         WHEN OTHER
051600             MOVE 'INSERT CLR.T_PAYMENT' TO ERR-PARA
051700             PERFORM 8000-SQL-ERROR
051800     END-EVALUATE
051900     .
052000* ---------------------------------------------------------------*
052100* 4900-WRITE-AUDIT                                               *
052200* AUDIT TRAIL VIA CLRCM020                                       *
052300* ---------------------------------------------------------------*
052400 4900-WRITE-AUDIT.
052500     MOVE 'CLR.T_PAYMENT' TO WS-AUD-TABLE
052600     MOVE CA-CLAIM-ID TO WS-AUD-KEY
052700     MOVE 'I' TO WS-AUD-ACTION
052800     MOVE WS-USER-ID TO WS-AUD-USER
052900     MOVE WS-PGM-ID TO WS-AUD-PGM
053000     CALL 'CLRCM020' USING WS-AUDIT-PARMS
053100                      CLR-ERROR-BLOCK
053200     IF ERR-SQLCODE NOT = ZERO
053300         ADD 1 TO WS-REJECT-CNT
053400     END-IF
053500     .
053600* ---------------------------------------------------------------*
053700* 9000-RETURN                                                    *
053800* RETURN TO CICS                                                 *
053900* ---------------------------------------------------------------*
054000 9000-RETURN.
054100     MOVE CLR-COMMAREA TO DFHCOMMAREA
054200     EXEC CICS RETURN END-EXEC
054300     .
054400* ---------------------------------------------------------------*
054500* 8000-SQL-ERROR                                                 *
054600* UNEXPECTED SQLCODE                                             *
054700* ---------------------------------------------------------------*
054800 8000-SQL-ERROR.
054900     MOVE SQLCODE TO ERR-SQLCODE WS-SQLCODE-DSP
055000     MOVE WS-PGM-ID TO ERR-PGM
055100     STRING 'SQLCODE ' WS-SQLCODE-DSP DELIMITED BY SIZE INTO
055200         ERR-TEXT
055300     CALL 'CLRCM050' USING CLR-ERROR-BLOCK
055400     EXEC CICS SYNCPOINT ROLLBACK END-EXEC
055500     MOVE 16 TO CA-RETURN-CD
055600     MOVE ERR-TEXT TO CA-MSG
055700     PERFORM 9000-RETURN
055800     .

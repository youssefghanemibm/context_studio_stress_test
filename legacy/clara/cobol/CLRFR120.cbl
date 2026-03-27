000100* ===============================================================*
000200* PROGRAM    : CLRFR120                                          *
000300* TITLE      : CUSTOMER-NOTICE DEFERRAL APPROVAL (TIPPING-OFF,   *
000400*              BR-FRD-036)                                       *
000500* SYSTEM     : CLARA - CLAIMS LEDGER AND RESERVE APPLICATION     *
000600* AREA       : FRAUD                                             *
000700* TYPE       : CICS ONLINE / DB2                                 *
000800* TRANSACTION: FR12                                              *
000900* MAP        : CLRM420 (MAPSET CLRMS05)                          *
001000* ---------------------------------------------------------------*
001100* PURPOSE                                                        *
001200*   CICS PSEUDO-CONVERSATIONAL PROGRAM - CUSTOMER-NOTICE         *
001300*     DEFERRAL APPROVAL (TIPPING-OFF, BR-FRD-036).               *
001400*   PSEUDO-CONVERSATIONAL; STATE IS KEPT IN CLRCOMM1.            *
001500* ---------------------------------------------------------------*
001600* DB2 TABLES                                                     *
001700*   CLR.T_CLAIM_LINK            READ                             *
001800*   CLR.T_FRAUD_NOTIFICATION    UPDATE                           *
001900* COPYBOOKS  : FRDLNK01 FRDNOT01 CLRERR01 CLRCOMM1               *
002000* CALLS      : CLRCM050 CLRCM020                                 *
002100* ---------------------------------------------------------------*
002200* MAINTENANCE HISTORY                                            *
002300* DATE       BY       REF        DESCRIPTION                     *
002400* ---------- -------- ---------- ------------------------------- *
002500* 2026-03-27 PASHW01  CHUB-206   INITIAL VERSION                 *
002600* ===============================================================*
002700 IDENTIFICATION DIVISION.
002800 PROGRAM-ID.    CLRFR120.
002900 AUTHOR.        P. ASHWORTH.
003000 INSTALLATION.  CORVANE MUTUAL - CLAIMS SYSTEMS.
003100 DATE-WRITTEN.  2026-03-27.
003200 DATE-COMPILED.
003300 ENVIRONMENT DIVISION.
003400 CONFIGURATION SECTION.
003500 SOURCE-COMPUTER.  IBM-Z.
003600 OBJECT-COMPUTER.  IBM-Z.
003700 DATA DIVISION.
003800 WORKING-STORAGE SECTION.
003900*
004000 01  WS-PROGRAM-INFO.
004100     05  WS-PGM-ID               PIC X(8)   VALUE 'CLRFR120'.
004200     05  WS-RUN-DATE             PIC X(10)  VALUE SPACES.
004300     05  WS-RUN-TS               PIC X(26)  VALUE SPACES.
004400     05  WS-USER-ID              PIC X(8)   VALUE SPACES.
004500*
004600 01  WS-SWITCHES.
004700     05  WS-EOF-SW               PIC X      VALUE 'N'.
004800         88  WS-END-OF-DATA                     VALUE 'Y'.
004900     05  WS-ERROR-SW             PIC X      VALUE 'N'.
005000         88  WS-ERROR-FOUND                     VALUE 'Y'.
005100         88  WS-NO-ERROR                        VALUE 'N'.
005200     05  WS-FOUND-SW             PIC X      VALUE 'N'.
005300         88  WS-ROW-FOUND                       VALUE 'Y'.
005400         88  WS-ROW-NOT-FOUND                   VALUE 'N'.
005500*
005600 01  WS-COUNTERS.
005700     05  WS-CLAIM-LINK-READ      PIC S9(9)  COMP-3 VALUE ZERO.
005800     05 WS-FRAUD-NOTIFICATION-WRITTEN PIC S9(9) COMP-3 VALUE ZERO.
005900     05  WS-REJECT-CNT           PIC S9(9)  COMP-3 VALUE ZERO.
006000*
006100 01  WS-SQL-WORK.
006200     05  WS-SQLCODE-DSP          PIC -9(9).
006300     05  WS-ROWS-AFFECTED        PIC S9(9)  COMP VALUE ZERO.
006400     05  WS-IND-1                PIC S9(4)  COMP VALUE ZERO.
006500     05  WS-IND-2                PIC S9(4)  COMP VALUE ZERO.
006600     05  WS-NEW-ID               PIC S9(18) COMP VALUE ZERO.
006700*
006800     EXEC SQL INCLUDE SQLCA END-EXEC.
006900*
007000* APPLICATION COPYBOOKS
007100 COPY FRDLNK01.
007200 COPY FRDNOT01.
007300 COPY CLRERR01.
007400 COPY CLRCOMM1.
007500*
007600* CALL INTERFACES
007700 01  WS-AUDIT-PARMS.
007800     05  WS-AUD-TABLE            PIC X(18).
007900     05  WS-AUD-KEY              PIC X(30).
008000     05  WS-AUD-ACTION           PIC X(1).
008100     05  WS-AUD-USER             PIC X(8).
008200     05  WS-AUD-PGM              PIC X(8).
008300*
008400* SYMBOLIC MAP CLRM420 (MAPSET CLRMS05) - KEEP IN STEP WITH
008500* BMS SOURCE legacy/clara/bms/CLRMS05.bms
008600 01  CLRM420I.
008700     02  FILLER                  PIC X(12).
008800     02  REFIDL                  PIC S9(4) COMP.
008900     02  REFIDF                  PIC X.
009000     02  FILLER REDEFINES REFIDF.
009100         03  REFIDA              PIC X.
009200     02  REFIDI                  PIC X(8).
009300     02  DEFUNTL                 PIC S9(4) COMP.
009400     02  DEFUNTF                 PIC X.
009500     02  FILLER REDEFINES DEFUNTF.
009600         03  DEFUNTA             PIC X.
009700     02  DEFUNTI                 PIC X(20).
009800     02  APPRL                   PIC S9(4) COMP.
009900     02  APPRF                   PIC X.
010000     02  FILLER REDEFINES APPRF.
010100         03  APPRA               PIC X.
010200     02  APPRI                   PIC X(30).
010300     02  REASONL                 PIC S9(4) COMP.
010400     02  REASONF                 PIC X.
010500     02  FILLER REDEFINES REASONF.
010600         03  REASONA             PIC X.
010700     02  REASONI                 PIC X(10).
010800     02  MSGL                    PIC S9(4) COMP.
010900     02  MSGF                    PIC X.
011000     02  FILLER REDEFINES MSGF.
011100         03  MSGA                PIC X.
011200     02  MSGI                    PIC X(79).
011300 01  CLRM420O REDEFINES CLRM420I.
011400     02  FILLER                  PIC X(12).
011500     02  FILLER                  PIC X(3).
011600     02  REFIDO                  PIC X(8).
011700     02  FILLER                  PIC X(3).
011800     02  DEFUNTO                 PIC X(20).
011900     02  FILLER                  PIC X(3).
012000     02  APPRO                   PIC X(30).
012100     02  FILLER                  PIC X(3).
012200     02  REASONO                 PIC X(10).
012300     02  FILLER                  PIC X(3).
012400     02  MSGO                    PIC X(79).
012500*
012600 01  WS-AID-VALUES.
012700     05  AID-ENTER               PIC X      VALUE X'7D'.
012800     05  AID-CLEAR               PIC X      VALUE X'6D'.
012900     05  AID-PF3                 PIC X      VALUE X'F3'.
013000     05  AID-PF7                 PIC X      VALUE X'F7'.
013100     05  AID-PF8                 PIC X      VALUE X'F8'.
013200     05  AID-PF12                PIC X      VALUE X'7C'.
013300     05  WS-RESP                 PIC S9(8)  COMP VALUE ZERO.
013400*
013500 01  WS-MESSAGES.
013600     05  WS-MSG-01               PIC X(40)  VALUE
013700             'REF-ID IS REQUIRED'.
013800 LINKAGE SECTION.
013900 01  DFHCOMMAREA                 PIC X(105).
014000 PROCEDURE DIVISION.
014100* ---------------------------------------------------------------*
014200* 0000-MAIN                                                      *
014300* PSEUDO-CONVERSATIONAL CONTROL                                  *
014400* ---------------------------------------------------------------*
014500 0000-MAIN.
014600     EXEC CICS ASSIGN USERID(WS-USER-ID) END-EXEC
014700     IF EIBCALEN = ZERO
014800         INITIALIZE CLR-COMMAREA
014900         MOVE 'FR12' TO CA-TRANID
015000         PERFORM 1000-FIRST-TIME
015100     ELSE
015200         MOVE DFHCOMMAREA TO CLR-COMMAREA
015300         PERFORM 2000-PROCESS-INPUT
015400     END-IF
015500     PERFORM 9000-RETURN
015600     GOBACK.
015700* ---------------------------------------------------------------*
015800* 1000-FIRST-TIME                                                *
015900* SEND THE EMPTY SCREEN                                          *
016000* ---------------------------------------------------------------*
016100 1000-FIRST-TIME.
016200     MOVE LOW-VALUES TO CLRM420O
016300     EXEC CICS SEND MAP('CLRM420') MAPSET('CLRMS05')
016400         ERASE FREEKB RESP(WS-RESP) END-EXEC
016500     .
016600* ---------------------------------------------------------------*
016700* 2000-PROCESS-INPUT                                             *
016800* HANDLE THE TERMINAL INPUT                                      *
016900* ---------------------------------------------------------------*
017000 2000-PROCESS-INPUT.
017100     EXEC CICS RECEIVE MAP('CLRM420') MAPSET('CLRMS05')
017200         INTO(CLRM420I) RESP(WS-RESP) END-EXEC
017300     EVALUATE TRUE
017400         WHEN EIBAID = AID-PF3
017500         WHEN EIBAID = AID-CLEAR
017600             MOVE ZERO TO CA-RETURN-CD
017700             EXEC CICS RETURN END-EXEC
017800         WHEN EIBAID = AID-PF12
017900             PERFORM 1000-FIRST-TIME
018000         WHEN EIBAID = AID-ENTER
018100             PERFORM 2100-EDIT-INPUT
018200             IF WS-NO-ERROR
018300                 PERFORM 2200-APPLY
018400             END-IF
018500         WHEN OTHER
018600             MOVE 'INVALID KEY PRESSED' TO MSGO
018700     END-EVALUATE
018800     EXEC CICS SEND MAP('CLRM420') MAPSET('CLRMS05')
018900         DATAONLY FREEKB CURSOR RESP(WS-RESP) END-EXEC
019000     .
019100* ---------------------------------------------------------------*
019200* 2100-EDIT-INPUT                                                *
019300* VALIDATE THE REQUEST                                           *
019400* ---------------------------------------------------------------*
019500 2100-EDIT-INPUT.
019600     SET WS-NO-ERROR TO TRUE
019700     IF REFIDL = ZERO OR REFIDI = SPACES
019800         SET WS-ERROR-FOUND TO TRUE
019900         MOVE WS-MSG-01 TO MSGO
020000         MOVE -1 TO REFIDL
020100     ELSE
020200         CONTINUE
020300     END-IF
020400     .
020500* ---------------------------------------------------------------*
020600* 2200-APPLY                                                     *
020700* CARRY OUT THE REQUEST                                          *
020800* ---------------------------------------------------------------*
020900 2200-APPLY.
021000     PERFORM 2300-READ-CLAIM-LINK
021100     PERFORM 2500-EDIT-CLAIM-LINK
021200     PERFORM 2510-EDIT-FRAU-NOTI
021300     PERFORM 2520-EDIT-CLAIM-LINK-2
021400     PERFORM 2530-EDIT-FRAU-NOTI-2
021500     PERFORM 2540-EDIT-FRAU-NOTI-3
021600     PERFORM 4100-UPDATE-FRAU-NOTI
021700     PERFORM 4900-WRITE-AUDIT
021800     IF WS-NO-ERROR
021900         EXEC CICS SYNCPOINT END-EXEC
022000         MOVE ZERO TO CA-RETURN-CD
022100     END-IF
022200     .
022300* ---------------------------------------------------------------*
022400* 2300-READ-CLAIM-LINK                                           *
022500* LOOK UP CLR.T_CLAIM_LINK                                       *
022600* ---------------------------------------------------------------*
022700 2300-READ-CLAIM-LINK.
022800     SET WS-ROW-FOUND TO TRUE
022900     EXEC SQL
023000         SELECT LINK_ID, CLAIM_ID_A, CLAIM_ID_B, LINK_TYPE_CD
023100                , DETECTED_DT
023200           INTO :FRDL-LINK-ID, :FRDL-CLAIM-ID-A
023300                , :FRDL-CLAIM-ID-B, :FRDL-LINK-TYPE-CD
023400                , :FRDL-DETECTED-DT
023500           FROM CLR.T_CLAIM_LINK
023600          WHERE LINK_ID = :FRDL-LINK-ID
023700     END-EXEC
023800     EVALUATE SQLCODE
023900         WHEN 0
024000             ADD 1 TO WS-CLAIM-LINK-READ
024100         WHEN +100
024200             SET WS-ROW-NOT-FOUND TO TRUE
024300         WHEN OTHER
024400             MOVE 'READ CLR.T_CLAIM_LINK' TO ERR-PARA
024500             PERFORM 8000-SQL-ERROR
024600     END-EVALUATE
024700     .
024800* ---------------------------------------------------------------*
024900* 2500-EDIT-CLAIM-LINK                                           *
025000* CHECK MANDATORY FIELDS IN CLR.T_CLAIM_LINK                     *
025100* ---------------------------------------------------------------*
025200 2500-EDIT-CLAIM-LINK.
025300     IF FRDL-CLAIM-ID-A = SPACES OR LOW-VALUES
025400         ADD 1 TO WS-REJECT-CNT
025500         MOVE 'CLAIM_ID_A MISSING' TO ERR-TEXT
025600     END-IF
025700     IF FRDL-CLAIM-ID-B = SPACES OR LOW-VALUES
025800         ADD 1 TO WS-REJECT-CNT
025900         MOVE 'CLAIM_ID_B MISSING' TO ERR-TEXT
026000     END-IF
026100     IF FRDL-LINK-TYPE-CD NOT = 'PH' AND FRDL-LINK-TYPE-CD NOT =
026200         'BA' AND FRDL-LINK-TYPE-CD NOT = 'VH' AND
026300         FRDL-LINK-TYPE-CD NOT = 'AD'
026400         ADD 1 TO WS-REJECT-CNT
026500         MOVE 'LINK_TYPE_CD INVALID' TO ERR-TEXT
026600     END-IF
026700     .
026800* ---------------------------------------------------------------*
026900* 2510-EDIT-FRAU-NOTI                                            *
027000* FIELD EDITS FOR CLR.T_FRAUD_NOTIFICATION                       *
027100* ---------------------------------------------------------------*
027200 2510-EDIT-FRAU-NOTI.
027300     IF FRDN-CLAIM-ID = SPACES OR LOW-VALUES
027400         ADD 1 TO WS-REJECT-CNT
027500         MOVE 'CLAIM_ID MISSING' TO ERR-TEXT
027600     END-IF
027700     IF FRDN-NOTICE-CHANNEL-CD NOT = 'LT' AND
027800         FRDN-NOTICE-CHANNEL-CD NOT = 'EM'
027900         ADD 1 TO WS-REJECT-CNT
028000         MOVE 'NOTICE_CHANNEL_CD INVALID' TO ERR-TEXT
028100     END-IF
028200     .
028300* ---------------------------------------------------------------*
028400* 2520-EDIT-CLAIM-LINK-2                                         *
028500* VALIDATE CLR.T_CLAIM_LINK                                      *
028600* ---------------------------------------------------------------*
028700 2520-EDIT-CLAIM-LINK-2.
028800     IF FRDL-DETECTED-DT NOT = SPACES AND FRDL-DETECTED-DT(5:1)
028900         NOT = '-'
029000         MOVE 'DETECTED_DT BAD DATE' TO ERR-TEXT
029100         ADD 1 TO WS-REJECT-CNT
029200     END-IF
029300     IF FRDL-VERSION-NO NOT NUMERIC
029400         MOVE ZERO TO FRDL-VERSION-NO
029500         ADD 1 TO WS-REJECT-CNT
029600     END-IF
029700     .
029800* ---------------------------------------------------------------*
029900* 2530-EDIT-FRAU-NOTI-2                                          *
030000* CHECK MANDATORY FIELDS IN CLR.T_FRAUD_NOTIFICATION             *
030100* ---------------------------------------------------------------*
030200 2530-EDIT-FRAU-NOTI-2.
030300     IF FRDN-NOTICE-DUE-DT NOT = SPACES AND
030400         FRDN-NOTICE-DUE-DT(5:1) NOT = '-'
030500         MOVE 'NOTICE_DUE_DT BAD DATE' TO ERR-TEXT
030600         ADD 1 TO WS-REJECT-CNT
030700     END-IF
030800     IF FRDN-DEFERRED-UNTIL-DT NOT = SPACES AND
030900         FRDN-DEFERRED-UNTIL-DT(5:1) NOT = '-'
031000         MOVE 'DEFERRED_UNTIL_DT BAD DATE' TO ERR-TEXT
031100         ADD 1 TO WS-REJECT-CNT
031200     END-IF
031300     IF FRDN-TEMPLATE-CD = SPACES OR LOW-VALUES
031400         ADD 1 TO WS-REJECT-CNT
031500         MOVE 'TEMPLATE_CD MISSING' TO ERR-TEXT
031600     END-IF
031700     .
031800* ---------------------------------------------------------------*
031900* 2540-EDIT-FRAU-NOTI-3                                          *
032000* VALIDATE CLR.T_FRAUD_NOTIFICATION                              *
032100* ---------------------------------------------------------------*
032200 2540-EDIT-FRAU-NOTI-3.
032300* ---------------------------------------------------------------*
032400* 4100-UPDATE-FRAU-NOTI                                          *
032500* UPDATE CLR.T_FRAUD_NOTIFICATION                                *
032600* ---------------------------------------------------------------*
032700 4100-UPDATE-FRAU-NOTI.
032800     EXEC SQL
032900         UPDATE CLR.T_FRAUD_NOTIFICATION
033000            SET REF_ID = :FRDN-REF-ID
033100              , NOTIFY_MSG_ID = :FRDN-NOTIFY-MSG-ID
033200              , NOTICE_SENT_TS = :FRDN-NOTICE-SENT-TS
033300              , LAST_UPD_TS = CURRENT TIMESTAMP
033400              , LAST_UPD_PGM = :WS-PGM-ID
033500              , LAST_UPD_USER = :WS-USER-ID
033600          WHERE NOTICE_ID = :FRDN-NOTICE-ID
033700     END-EXEC
033800     EVALUATE SQLCODE
033900         WHEN 0
034000             ADD 1 TO WS-FRAUD-NOTIFICATION-WRITTEN
034100         WHEN +100
034200             SET WS-ROW-NOT-FOUND TO TRUE
034300         WHEN OTHER
034400             MOVE 'UPDATE CLR.T_FRAUD_NOTIFICATIO' TO ERR-PARA
034500             PERFORM 8000-SQL-ERROR
034600     END-EVALUATE
034700     .
034800* ---------------------------------------------------------------*
034900* 4900-WRITE-AUDIT                                               *
035000* AUDIT TRAIL VIA CLRCM020                                       *
035100* ---------------------------------------------------------------*
035200 4900-WRITE-AUDIT.
035300     MOVE 'CLR.T_FRAUD_NOTIFICATION' TO WS-AUD-TABLE
035400     MOVE CA-CLAIM-ID TO WS-AUD-KEY
035500     MOVE 'U' TO WS-AUD-ACTION
035600     MOVE WS-USER-ID TO WS-AUD-USER
035700     MOVE WS-PGM-ID TO WS-AUD-PGM
035800     CALL 'CLRCM020' USING WS-AUDIT-PARMS
035900                      CLR-ERROR-BLOCK
036000     IF ERR-SQLCODE NOT = ZERO
036100         ADD 1 TO WS-REJECT-CNT
036200     END-IF
036300     .
036400* ---------------------------------------------------------------*
036500* 9000-RETURN                                                    *
036600* RETURN TO CICS                                                 *
036700* ---------------------------------------------------------------*
036800 9000-RETURN.
036900     EXEC CICS RETURN TRANSID('FR12') COMMAREA(CLR-COMMAREA)
037000         LENGTH(LENGTH OF CLR-COMMAREA) END-EXEC
037100     .
037200* ---------------------------------------------------------------*
037300* 8000-SQL-ERROR                                                 *
037400* UNEXPECTED SQLCODE                                             *
037500* ---------------------------------------------------------------*
037600 8000-SQL-ERROR.
037700     MOVE SQLCODE TO ERR-SQLCODE WS-SQLCODE-DSP
037800     MOVE WS-PGM-ID TO ERR-PGM
037900     STRING 'SQLCODE ' WS-SQLCODE-DSP DELIMITED BY SIZE INTO
038000         ERR-TEXT
038100     CALL 'CLRCM050' USING CLR-ERROR-BLOCK
038200     EXEC CICS SYNCPOINT ROLLBACK END-EXEC
038300     MOVE 16 TO CA-RETURN-CD
038400     MOVE ERR-TEXT TO CA-MSG
038500     PERFORM 9000-RETURN
038600     .

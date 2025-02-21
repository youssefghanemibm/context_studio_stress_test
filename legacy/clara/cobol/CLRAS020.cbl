000100* ===============================================================*
000200* PROGRAM    : CLRAS020                                          *
000300* TITLE      : CLAIMS ASSESSOR APPOINTMENT (INTERNAL OR VENDOR)  *
000400* SYSTEM     : CLARA - CLAIMS LEDGER AND RESERVE APPLICATION     *
000500* AREA       : ASSESS                                            *
000600* TYPE       : CICS ONLINE / DB2                                 *
000700* TRANSACTION: AS02                                              *
000800* MAP        : CLRM220 (MAPSET CLRMS03)                          *
000900* ---------------------------------------------------------------*
001000* PURPOSE                                                        *
001100*   CICS PSEUDO-CONVERSATIONAL PROGRAM - CLAIMS ASSESSOR         *
001200*     APPOINTMENT (INTERNAL OR VENDOR).                          *
001300*   PSEUDO-CONVERSATIONAL; STATE IS KEPT IN CLRCOMM1.            *
001400* ---------------------------------------------------------------*
001500* DB2 TABLES                                                     *
001600*   CLR.T_ASSESSMENT            READ                             *
001700*   CLR.T_INSPECTION            READ                             *
001800*   CLR.T_VENDOR                READ                             *
001900*   CLR.T_ASSESSOR_ASSIGNMENT   INSERT                           *
002000* COPYBOOKS  : CLRASM01 CLRASG01 CLRINS01 VENREC01 CLRERR01      *
002100*              CLRCOMM1                                          *
002200* CALLS      : CLRCM050 CLRCM020 CLRCM070                        *
002300* ---------------------------------------------------------------*
002400* MAINTENANCE HISTORY                                            *
002500* DATE       BY       REF        DESCRIPTION                     *
002600* ---------- -------- ---------- ------------------------------- *
002700* 1994-10-03 CLRPROJ             INITIAL VERSION - CLARA GO-LIVE *
002800* 1999-04-19 KBARR01             Y2K REMEDIATION - DATE          *
002900*                                WINDOWING REMOVED               *
003000* 1999-05-23 KBARR01             Y2K: 4-DIGIT YEARS IN DATE WORK *
003100*                                AREAS                           *
003200* 2017-10-07 PASHW01             CURSOR POSITIONING ON           *
003300*                                VALIDATION ERRORS               *
003400* 2024-02-29 PASHW01             SQL WARNINGS LOGGED, NOT        *
003500*                                TREATED AS ERRORS               *
003600* ===============================================================*
003700 IDENTIFICATION DIVISION.
003800 PROGRAM-ID.    CLRAS020.
003900 AUTHOR.        CLARA PROJECT TEAM.
004000 INSTALLATION.  CORVANE MUTUAL - CLAIMS SYSTEMS.
004100 DATE-WRITTEN.  1994-10-03.
004200 DATE-COMPILED.
004300 ENVIRONMENT DIVISION.
004400 CONFIGURATION SECTION.
004500 SOURCE-COMPUTER.  IBM-Z.
004600 OBJECT-COMPUTER.  IBM-Z.
004700 DATA DIVISION.
004800 WORKING-STORAGE SECTION.
004900*
005000 01  WS-PROGRAM-INFO.
005100     05  WS-PGM-ID               PIC X(8)   VALUE 'CLRAS020'.
005200     05  WS-RUN-DATE             PIC X(10)  VALUE SPACES.
005300     05  WS-RUN-TS               PIC X(26)  VALUE SPACES.
005400     05  WS-USER-ID              PIC X(8)   VALUE SPACES.
005500*
005600 01  WS-SWITCHES.
005700     05  WS-EOF-SW               PIC X      VALUE 'N'.
005800        88  WS-END-OF-DATA                     VALUE 'Y'.
005900     05  WS-ERROR-SW             PIC X      VALUE 'N'.
006000        88  WS-ERROR-FOUND                     VALUE 'Y'.
006100        88  WS-NO-ERROR                        VALUE 'N'.
006200     05  WS-FOUND-SW             PIC X      VALUE 'N'.
006300        88  WS-ROW-FOUND                       VALUE 'Y'.
006400        88  WS-ROW-NOT-FOUND                   VALUE 'N'.
006500*
006600 01  WS-COUNTERS.
006700     05  WS-ASSESSMENT-READ      PIC S9(9)  COMP-3 VALUE ZERO.
006800     05  WS-INSPECTION-READ      PIC S9(9)  COMP-3 VALUE ZERO.
006900     05  WS-VENDOR-READ          PIC S9(9)  COMP-3 VALUE ZERO.
007000     05 WS-ASSESSOR-ASSIGNMENT-WRITTEN PIC S9(9) COMP-3 VALUE
007100         ZERO.
007200     05  WS-REJECT-CNT           PIC S9(9)  COMP-3 VALUE ZERO.
007300*
007400 01  WS-SQL-WORK.
007500     05  WS-SQLCODE-DSP          PIC -9(9).
007600     05  WS-ROWS-AFFECTED        PIC S9(9)  COMP VALUE ZERO.
007700     05  WS-IND-1                PIC S9(4)  COMP VALUE ZERO.
007800     05  WS-IND-2                PIC S9(4)  COMP VALUE ZERO.
007900     05  WS-NEW-ID               PIC S9(18) COMP VALUE ZERO.
008000*
008100     EXEC SQL INCLUDE SQLCA END-EXEC.
008200*
008300* COPYBOOKS (HOST STRUCTURES AND WORK AREAS)
008400 COPY CLRASM01.
008500 COPY CLRASG01.
008600 COPY CLRINS01.
008700 COPY VENREC01.
008800 COPY CLRERR01.
008900 COPY CLRCOMM1.
009000*
009100* SUBPROGRAM PARAMETERS
009200 01  WS-AUDIT-PARMS.
009300     05  WS-AUD-TABLE            PIC X(18).
009400     05  WS-AUD-KEY              PIC X(30).
009500     05  WS-AUD-ACTION           PIC X(1).
009600     05  WS-AUD-USER             PIC X(8).
009700     05  WS-AUD-PGM              PIC X(8).
009800 01  WS-AUTH-PARMS.
009900     05  WS-AUTH-USER            PIC X(8).
010000     05  WS-AUTH-FUNCTION        PIC X(8).
010100     05  WS-AUTH-ALLOWED         PIC X(1).
010200*
010300* SYMBOLIC MAP CLRM220 (MAPSET CLRMS03) - KEEP IN STEP WITH
010400* BMS SOURCE legacy/clara/bms/CLRMS03.bms
010500 01  CLRM220I.
010600     02  FILLER                  PIC X(12).
010700     02  CLAIMIDL                PIC S9(4) COMP.
010800     02  CLAIMIDF                PIC X.
010900     02  FILLER REDEFINES CLAIMIDF.
011000        03  CLAIMIDA            PIC X.
011100     02  CLAIMIDI                PIC X(20).
011200     02  ASSEIDL                 PIC S9(4) COMP.
011300     02  ASSEIDF                 PIC X.
011400     02  FILLER REDEFINES ASSEIDF.
011500        03  ASSEIDA             PIC X.
011600     02  ASSEIDI                 PIC X(16).
011700     02  VENDORL                 PIC S9(4) COMP.
011800     02  VENDORF                 PIC X.
011900     02  FILLER REDEFINES VENDORF.
012000        03  VENDORA             PIC X.
012100     02  VENDORI                 PIC X(10).
012200     02  SLADUEL                 PIC S9(4) COMP.
012300     02  SLADUEF                 PIC X.
012400     02  FILLER REDEFINES SLADUEF.
012500        03  SLADUEA             PIC X.
012600     02  SLADUEI                 PIC X(30).
012700     02  MSGL                    PIC S9(4) COMP.
012800     02  MSGF                    PIC X.
012900     02  FILLER REDEFINES MSGF.
013000        03  MSGA                PIC X.
013100     02  MSGI                    PIC X(79).
013200 01  CLRM220O REDEFINES CLRM220I.
013300     02  FILLER                  PIC X(12).
013400     02  FILLER                  PIC X(3).
013500     02  CLAIMIDO                PIC X(20).
013600     02  FILLER                  PIC X(3).
013700     02  ASSEIDO                 PIC X(16).
013800     02  FILLER                  PIC X(3).
013900     02  VENDORO                 PIC X(10).
014000     02  FILLER                  PIC X(3).
014100     02  SLADUEO                 PIC X(30).
014200     02  FILLER                  PIC X(3).
014300     02  MSGO                    PIC X(79).
014400*
014500 01  WS-AID-VALUES.
014600     05  AID-ENTER               PIC X      VALUE X'7D'.
014700     05  AID-CLEAR               PIC X      VALUE X'6D'.
014800     05  AID-PF3                 PIC X      VALUE X'F3'.
014900     05  AID-PF7                 PIC X      VALUE X'F7'.
015000     05  AID-PF8                 PIC X      VALUE X'F8'.
015100     05  AID-PF12                PIC X      VALUE X'7C'.
015200     05  WS-RESP                 PIC S9(8)  COMP VALUE ZERO.
015300*
015400 01  WS-MESSAGES.
015500     05  WS-MSG-01               PIC X(40)  VALUE
015600           'CLAIM-ID IS REQUIRED'.
015700 LINKAGE SECTION.
015800 01  DFHCOMMAREA                 PIC X(105).
015900 PROCEDURE DIVISION.
016000* ---------------------------------------------------------------*
016100* 0000-MAIN                                                      *
016200* PSEUDO-CONVERSATIONAL CONTROL                                  *
016300* ---------------------------------------------------------------*
016400 0000-MAIN.
016500     EXEC CICS ASSIGN USERID(WS-USER-ID) END-EXEC
016600     IF EIBCALEN = ZERO
016700        INITIALIZE CLR-COMMAREA
016800        MOVE 'AS02' TO CA-TRANID
016900        PERFORM 1000-FIRST-TIME THRU 1000-FIRST-TIME-EXIT
017000     ELSE
017100        MOVE DFHCOMMAREA TO CLR-COMMAREA
017200        PERFORM 2000-PROCESS-INPUT THRU 2000-PROCESS-INPUT-EXIT
017300     END-IF
017400     PERFORM 9000-RETURN THRU 9000-RETURN-EXIT
017500     GOBACK.
017600 0000-MAIN-EXIT.
017700     EXIT.
017800* ---------------------------------------------------------------*
017900* 1000-FIRST-TIME                                                *
018000* SEND THE EMPTY SCREEN                                          *
018100* ---------------------------------------------------------------*
018200 1000-FIRST-TIME.
018300     MOVE LOW-VALUES TO CLRM220O
018400     EXEC CICS SEND MAP('CLRM220') MAPSET('CLRMS03')
018500        ERASE FREEKB RESP(WS-RESP) END-EXEC
018600     .
018700 1000-FIRST-TIME-EXIT.
018800     EXIT.
018900* ---------------------------------------------------------------*
019000* 2000-PROCESS-INPUT                                             *
019100* INPUT PROCESSING                                               *
019200* ---------------------------------------------------------------*
019300 2000-PROCESS-INPUT.
019400     EXEC CICS RECEIVE MAP('CLRM220') MAPSET('CLRMS03')
019500        INTO(CLRM220I) RESP(WS-RESP) END-EXEC
019600     EVALUATE TRUE
019700        WHEN EIBAID = AID-PF3
019800        WHEN EIBAID = AID-CLEAR
019900           MOVE ZERO TO CA-RETURN-CD
020000           EXEC CICS RETURN END-EXEC
020100        WHEN EIBAID = AID-PF12
020200           PERFORM 1000-FIRST-TIME THRU 1000-FIRST-TIME-EXIT
020300        WHEN EIBAID = AID-ENTER
020400           PERFORM 2100-EDIT-INPUT THRU 2100-EDIT-INPUT-EXIT
020500           IF WS-NO-ERROR
020600              PERFORM 2200-APPLY THRU 2200-APPLY-EXIT
020700           END-IF
020800        WHEN OTHER
020900           MOVE 'INVALID KEY PRESSED' TO MSGO
021000     END-EVALUATE
021100     EXEC CICS SEND MAP('CLRM220') MAPSET('CLRMS03')
021200        DATAONLY FREEKB CURSOR RESP(WS-RESP) END-EXEC
021300     .
021400 2000-PROCESS-INPUT-EXIT.
021500     EXIT.
021600* ---------------------------------------------------------------*
021700* 2100-EDIT-INPUT                                                *
021800* VALIDATE THE REQUEST                                           *
021900* ---------------------------------------------------------------*
022000 2100-EDIT-INPUT.
022100     SET WS-NO-ERROR TO TRUE
022200     IF CLAIMIDL = ZERO OR CLAIMIDI = SPACES
022300        SET WS-ERROR-FOUND TO TRUE
022400        MOVE WS-MSG-01 TO MSGO
022500        MOVE -1 TO CLAIMIDL
022600     ELSE
022700        MOVE CLAIMIDI TO CA-CLAIM-ID
022800     END-IF
022900     PERFORM 1500-CHECK-AUTHORITY THRU 1500-CHECK-AUTHORITY-EXIT
023000     .
023100 2100-EDIT-INPUT-EXIT.
023200     EXIT.
023300* ---------------------------------------------------------------*
023400* 1500-CHECK-AUTHORITY                                           *
023500* CONFIRM THE USER MAY RUN THIS FUNCTION                         *
023600* ---------------------------------------------------------------*
023700 1500-CHECK-AUTHORITY.
023800     MOVE WS-USER-ID TO WS-AUTH-USER
023900     MOVE 'CLRAS020' TO WS-AUTH-FUNCTION
024000     CALL 'CLRCM070' USING WS-AUTH-PARMS
024100                      CLR-ERROR-BLOCK
024200     IF ERR-SQLCODE NOT = ZERO
024300        MOVE 'CALL CLRCM070' TO ERR-PARA
024400        PERFORM 8000-SQL-ERROR
024500     END-IF
024600     IF WS-AUTH-ALLOWED NOT = 'Y'
024700        SET WS-ERROR-FOUND TO TRUE
024800        MOVE 8 TO CA-RETURN-CD
024900        MOVE 'NOT AUTHORISED FOR THIS FUNCTION' TO CA-MSG
025000     END-IF
025100     .
025200 1500-CHECK-AUTHORITY-EXIT.
025300     EXIT.
025400* ---------------------------------------------------------------*
025500* 2200-APPLY                                                     *
025600* CARRY OUT THE REQUEST                                          *
025700* ---------------------------------------------------------------*
025800 2200-APPLY.
025900     PERFORM 2300-READ-ASSESSMENT THRU 2300-READ-ASSESSMENT-EXIT
026000     PERFORM 2320-READ-INSPECTION THRU 2320-READ-INSPECTION-EXIT
026100     PERFORM 2340-READ-VENDOR THRU 2340-READ-VENDOR-EXIT
026200     PERFORM 4100-INSERT-ASSE-ASSI THRU 4100-INSERT-ASSE-ASSI-EXIT
026300     PERFORM 4900-WRITE-AUDIT THRU 4900-WRITE-AUDIT-EXIT
026400     IF WS-NO-ERROR
026500        EXEC CICS SYNCPOINT END-EXEC
026600        MOVE ZERO TO CA-RETURN-CD
026700     END-IF
026800     .
026900 2200-APPLY-EXIT.
027000     EXIT.
027100* ---------------------------------------------------------------*
027200* 2300-READ-ASSESSMENT                                           *
027300* FETCH CLR.T_ASSESSMENT                                         *
027400* ---------------------------------------------------------------*
027500 2300-READ-ASSESSMENT.
027600     SET WS-ROW-FOUND TO TRUE
027700     EXEC SQL
027800         SELECT ASSESS_ID, CLAIM_ID, ASSESS_TYPE_CD
027900                , COVER_DECISION_CD, ESTIMATE_AMT
028000           INTO :ASM-ASSESS-ID, :ASM-CLAIM-ID
028100                , :ASM-ASSESS-TYPE-CD, :ASM-COVER-DECISION-CD
028200                , :ASM-ESTIMATE-AMT
028300           FROM CLR.T_ASSESSMENT
028400          WHERE ASSESS_ID = :ASM-ASSESS-ID
028500     END-EXEC
028600     EVALUATE SQLCODE
028700        WHEN 0
028800           ADD 1 TO WS-ASSESSMENT-READ
028900        WHEN +100
029000           SET WS-ROW-NOT-FOUND TO TRUE
029100        WHEN OTHER
029200           MOVE 'READ CLR.T_ASSESSMENT' TO ERR-PARA
029300           PERFORM 8000-SQL-ERROR
029400     END-EVALUATE
029500     .
029600 2300-READ-ASSESSMENT-EXIT.
029700     EXIT.
029800* ---------------------------------------------------------------*
029900* 2320-READ-INSPECTION                                           *
030000* LOOK UP CLR.T_INSPECTION                                       *
030100* ---------------------------------------------------------------*
030200 2320-READ-INSPECTION.
030300     SET WS-ROW-FOUND TO TRUE
030400     EXEC SQL
030500         SELECT INSP_ID, CLAIM_ID, BOOKED_TS, COMPLETED_TS
030600           INTO :INS-INSP-ID, :INS-CLAIM-ID, :INS-BOOKED-TS
030700                , :INS-COMPLETED-TS
030800           FROM CLR.T_INSPECTION
030900          WHERE INSP_ID = :INS-INSP-ID
031000     END-EXEC
031100     EVALUATE SQLCODE
031200        WHEN 0
031300           ADD 1 TO WS-INSPECTION-READ
031400        WHEN +100
031500           SET WS-ROW-NOT-FOUND TO TRUE
031600        WHEN OTHER
031700           MOVE 'READ CLR.T_INSPECTION' TO ERR-PARA
031800           PERFORM 8000-SQL-ERROR
031900     END-EVALUATE
032000     .
032100 2320-READ-INSPECTION-EXIT.
032200     EXIT.
032300* ---------------------------------------------------------------*
032400* 2340-READ-VENDOR                                               *
032500* READ CLR.T_VENDOR                                              *
032600* ---------------------------------------------------------------*
032700 2340-READ-VENDOR.
032800     SET WS-ROW-FOUND TO TRUE
032900     EXEC SQL
033000         SELECT VENDOR_CD, VENDOR_NAME, VENDOR_TYPE_CD
033100                , PANEL_FROM_DT, PANEL_TO_DT
033200           INTO :VENR-VENDOR-CD, :VENR-VENDOR-NAME
033300                , :VENR-VENDOR-TYPE-CD, :VENR-PANEL-FROM-DT
033400                , :VENR-PANEL-TO-DT
033500           FROM CLR.T_VENDOR
033600          WHERE VENDOR_CD = :VENR-VENDOR-CD
033700     END-EXEC
033800     EVALUATE SQLCODE
033900        WHEN 0
034000           ADD 1 TO WS-VENDOR-READ
034100        WHEN +100
034200           SET WS-ROW-NOT-FOUND TO TRUE
034300        WHEN OTHER
034400           MOVE 'READ CLR.T_VENDOR' TO ERR-PARA
034500           PERFORM 8000-SQL-ERROR
034600     END-EVALUATE
034700     .
034800 2340-READ-VENDOR-EXIT.
034900     EXIT.
035000* ---------------------------------------------------------------*
035100* 4100-INSERT-ASSE-ASSI                                          *
035200* INSERT CLR.T_ASSESSOR_ASSIGNMENT                               *
035300* ---------------------------------------------------------------*
035400 4100-INSERT-ASSE-ASSI.
035500     MOVE CA-CLAIM-ID TO ASG-CLAIM-ID
035600     EXEC SQL
035700         INSERT INTO CLR.T_ASSESSOR_ASSIGNMENT
035800              ( CLAIM_ID, ASSESSOR_ID, VENDOR_CD, APPOINTED_TS
035900              , SLA_DUE_DT, VERSION_NO, LAST_UPD_TS
036000              , LAST_UPD_PGM, LAST_UPD_USER )
036100         VALUES
036200              ( :ASG-CLAIM-ID, :ASG-ASSESSOR-ID, :ASG-VENDOR-CD
036300              , CURRENT TIMESTAMP, :ASG-SLA-DUE-DT
036400              , :ASG-VERSION-NO, CURRENT TIMESTAMP, :WS-PGM-ID
036500              , :WS-USER-ID )
036600     END-EXEC
036700     EVALUATE SQLCODE
036800        WHEN 0
036900           ADD 1 TO WS-ASSESSOR-ASSIGNMENT-WRITTEN
037000        WHEN +100
037100           SET WS-ROW-NOT-FOUND TO TRUE
037200        WHEN OTHER
037300           MOVE 'INSERT CLR.T_ASSESSOR_ASSIGNME' TO ERR-PARA
037400           PERFORM 8000-SQL-ERROR
037500     END-EVALUATE
037600     .
037700 4100-INSERT-ASSE-ASSI-EXIT.
037800     EXIT.
037900* ---------------------------------------------------------------*
038000* 4900-WRITE-AUDIT                                               *
038100* AUDIT TRAIL VIA CLRCM020                                       *
038200* ---------------------------------------------------------------*
038300 4900-WRITE-AUDIT.
038400     MOVE 'CLR.T_ASSESSOR_ASSIGNMENT' TO WS-AUD-TABLE
038500     MOVE CA-CLAIM-ID TO WS-AUD-KEY
038600     MOVE 'I' TO WS-AUD-ACTION
038700     MOVE WS-USER-ID TO WS-AUD-USER
038800     MOVE WS-PGM-ID TO WS-AUD-PGM
038900     CALL 'CLRCM020' USING WS-AUDIT-PARMS
039000                      CLR-ERROR-BLOCK
039100     IF ERR-SQLCODE NOT = ZERO
039200        ADD 1 TO WS-REJECT-CNT
039300     END-IF
039400     .
039500 4900-WRITE-AUDIT-EXIT.
039600     EXIT.
039700* ---------------------------------------------------------------*
039800* 9000-RETURN                                                    *
039900* RETURN TO CICS                                                 *
040000* ---------------------------------------------------------------*
040100 9000-RETURN.
040200     EXEC CICS RETURN TRANSID('AS02') COMMAREA(CLR-COMMAREA)
040300        LENGTH(LENGTH OF CLR-COMMAREA) END-EXEC
040400     .
040500 9000-RETURN-EXIT.
040600     EXIT.
040700* ---------------------------------------------------------------*
040800* 8000-SQL-ERROR                                                 *
040900* DB2 ERROR HANDLING                                             *
041000* ---------------------------------------------------------------*
041100 8000-SQL-ERROR.
041200     MOVE SQLCODE TO ERR-SQLCODE WS-SQLCODE-DSP
041300     MOVE WS-PGM-ID TO ERR-PGM
041400     STRING 'SQLCODE ' WS-SQLCODE-DSP DELIMITED BY SIZE INTO
041500         ERR-TEXT
041600     CALL 'CLRCM050' USING CLR-ERROR-BLOCK
041700     EXEC CICS SYNCPOINT ROLLBACK END-EXEC
041800     MOVE 16 TO CA-RETURN-CD
041900     MOVE ERR-TEXT TO CA-MSG
042000     PERFORM 9000-RETURN THRU 9000-RETURN-EXIT
042100     .
042200 8000-SQL-ERROR-EXIT.
042300     EXIT.

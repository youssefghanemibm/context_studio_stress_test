000100* ===============================================================*
000200* PROGRAM    : CLRAS010                                          *
000300* TITLE      : ASSESSMENT WORKBENCH                              *
000400* SYSTEM     : CLARA - CLAIMS LEDGER AND RESERVE APPLICATION     *
000500* AREA       : ASSESS                                            *
000600* TYPE       : CICS ONLINE / DB2                                 *
000700* TRANSACTION: AS01                                              *
000800* MAP        : CLRM210 (MAPSET CLRMS03)                          *
000900* ---------------------------------------------------------------*
001000* PURPOSE                                                        *
001100*   CICS PSEUDO-CONVERSATIONAL PROGRAM - ASSESSMENT WORKBENCH.   *
001200*   PSEUDO-CONVERSATIONAL; STATE IS KEPT IN CLRCOMM1.            *
001300* ---------------------------------------------------------------*
001400* DB2 TABLES                                                     *
001500*   CLR.T_INSPECTION            READ                             *
001600*   CLR.T_ASSESSMENT            INSERT                           *
001700* COPYBOOKS  : CLRASM01 CLRINS01 CLRERR01 CLRCOMM1 CLRDATE1      *
001800* CALLS      : CLRCM050 CLRCM020 CLRCM010                        *
001900* ---------------------------------------------------------------*
002000* MAINTENANCE HISTORY                                            *
002100* DATE       BY       REF        DESCRIPTION                     *
002200* ---------- -------- ---------- ------------------------------- *
002300* 1994-10-03 CLRPROJ             INITIAL VERSION - CLARA GO-LIVE *
002400* 2012-06-15 DO                  DATE ARITHMETIC MOVED TO        *
002500*                                CLRCM010                        *
002600* 2014-05-07 PASHW01             CURSOR POSITIONING ON           *
002700*                                VALIDATION ERRORS               *
002800* 2015-05-04 PASHW01             PERFORMANCE: CURSOR WITH HOLD,  *
002900*                                FEWER COMMITS                   *
003000* 2022-02-09 PASHW01             REPORT HEADINGS REALIGNED       *
003100* ===============================================================*
003200 IDENTIFICATION DIVISION.
003300 PROGRAM-ID.    CLRAS010.
003400 AUTHOR.        CLARA PROJECT TEAM.
003500 INSTALLATION.  CORVANE MUTUAL - CLAIMS SYSTEMS.
003600 DATE-WRITTEN.  1994-10-03.
003700 DATE-COMPILED.
003800 ENVIRONMENT DIVISION.
003900 CONFIGURATION SECTION.
004000 SOURCE-COMPUTER.  IBM-Z.
004100 OBJECT-COMPUTER.  IBM-Z.
004200 DATA DIVISION.
004300 WORKING-STORAGE SECTION.
004400*
004500 01  WS-PROGRAM-INFO.
004600     05  WS-PGM-ID               PIC X(8)   VALUE 'CLRAS010'.
004700     05  WS-RUN-DATE             PIC X(10)  VALUE SPACES.
004800     05  WS-RUN-TS               PIC X(26)  VALUE SPACES.
004900     05  WS-USER-ID              PIC X(8)   VALUE SPACES.
005000*
005100 01  WS-SWITCHES.
005200     05  WS-EOF-SW               PIC X      VALUE 'N'.
005300         88  WS-END-OF-DATA                     VALUE 'Y'.
005400     05  WS-ERROR-SW             PIC X      VALUE 'N'.
005500         88  WS-ERROR-FOUND                     VALUE 'Y'.
005600         88  WS-NO-ERROR                        VALUE 'N'.
005700     05  WS-FOUND-SW             PIC X      VALUE 'N'.
005800         88  WS-ROW-FOUND                       VALUE 'Y'.
005900         88  WS-ROW-NOT-FOUND                   VALUE 'N'.
006000*
006100 01  WS-COUNTERS.
006200     05  WS-INSPECTION-READ      PIC S9(9)  COMP-3 VALUE ZERO.
006300     05  WS-ASSESSMENT-WRITTEN   PIC S9(9)  COMP-3 VALUE ZERO.
006400     05  WS-REJECT-CNT           PIC S9(9)  COMP-3 VALUE ZERO.
006500*
006600 01  WS-SQL-WORK.
006700     05  WS-SQLCODE-DSP          PIC -9(9).
006800     05  WS-ROWS-AFFECTED        PIC S9(9)  COMP VALUE ZERO.
006900     05  WS-IND-1                PIC S9(4)  COMP VALUE ZERO.
007000     05  WS-IND-2                PIC S9(4)  COMP VALUE ZERO.
007100     05  WS-NEW-ID               PIC S9(18) COMP VALUE ZERO.
007200*
007300     EXEC SQL INCLUDE SQLCA END-EXEC.
007400*
007500* COPYBOOKS (HOST STRUCTURES AND WORK AREAS)
007600 COPY CLRASM01.
007700 COPY CLRINS01.
007800 COPY CLRERR01.
007900 COPY CLRCOMM1.
008000 COPY CLRDATE1.
008100*
008200* SUBPROGRAM PARAMETERS
008300 01  WS-AUDIT-PARMS.
008400     05  WS-AUD-TABLE            PIC X(18).
008500     05  WS-AUD-KEY              PIC X(30).
008600     05  WS-AUD-ACTION           PIC X(1).
008700     05  WS-AUD-USER             PIC X(8).
008800     05  WS-AUD-PGM              PIC X(8).
008900*
009000* SYMBOLIC MAP CLRM210 (MAPSET CLRMS03) - KEEP IN STEP WITH
009100* BMS SOURCE legacy/clara/bms/CLRMS03.bms
009200 01  CLRM210I.
009300     02  FILLER                  PIC X(12).
009400     02  CLAIMIDL                PIC S9(4) COMP.
009500     02  CLAIMIDF                PIC X.
009600     02  FILLER REDEFINES CLAIMIDF.
009700         03  CLAIMIDA            PIC X.
009800     02  CLAIMIDI                PIC X(20).
009900     02  ASSTYPL                 PIC S9(4) COMP.
010000     02  ASSTYPF                 PIC X.
010100     02  FILLER REDEFINES ASSTYPF.
010200         03  ASSTYPA             PIC X.
010300     02  ASSTYPI                 PIC X(16).
010400     02  ESTIL                   PIC S9(4) COMP.
010500     02  ESTIF                   PIC X.
010600     02  FILLER REDEFINES ESTIF.
010700         03  ESTIA               PIC X.
010800     02  ESTII                   PIC X(8).
010900     02  COVEDECL                PIC S9(4) COMP.
011000     02  COVEDECF                PIC X.
011100     02  FILLER REDEFINES COVEDECF.
011200         03  COVEDECA            PIC X.
011300     02  COVEDECI                PIC X(16).
011400     02  MSGL                    PIC S9(4) COMP.
011500     02  MSGF                    PIC X.
011600     02  FILLER REDEFINES MSGF.
011700         03  MSGA                PIC X.
011800     02  MSGI                    PIC X(79).
011900 01  CLRM210O REDEFINES CLRM210I.
012000     02  FILLER                  PIC X(12).
012100     02  FILLER                  PIC X(3).
012200     02  CLAIMIDO                PIC X(20).
012300     02  FILLER                  PIC X(3).
012400     02  ASSTYPO                 PIC X(16).
012500     02  FILLER                  PIC X(3).
012600     02  ESTIO                   PIC X(8).
012700     02  FILLER                  PIC X(3).
012800     02  COVEDECO                PIC X(16).
012900     02  FILLER                  PIC X(3).
013000     02  MSGO                    PIC X(79).
013100*
013200 01  WS-AID-VALUES.
013300     05  AID-ENTER               PIC X      VALUE X'7D'.
013400     05  AID-CLEAR               PIC X      VALUE X'6D'.
013500     05  AID-PF3                 PIC X      VALUE X'F3'.
013600     05  AID-PF7                 PIC X      VALUE X'F7'.
013700     05  AID-PF8                 PIC X      VALUE X'F8'.
013800     05  AID-PF12                PIC X      VALUE X'7C'.
013900     05  WS-RESP                 PIC S9(8)  COMP VALUE ZERO.
014000*
014100 01  WS-MESSAGES.
014200     05  WS-MSG-01               PIC X(40)  VALUE
014300             'CLAIM-ID IS REQUIRED'.
014400 LINKAGE SECTION.
014500 01  DFHCOMMAREA                 PIC X(105).
014600 PROCEDURE DIVISION.
014700* ---------------------------------------------------------------*
014800* 0000-MAIN                                                      *
014900* PSEUDO-CONVERSATIONAL CONTROL                                  *
015000* ---------------------------------------------------------------*
015100 0000-MAIN.
015200     EXEC CICS ASSIGN USERID(WS-USER-ID) END-EXEC
015300     IF EIBCALEN = ZERO
015400         INITIALIZE CLR-COMMAREA
015500         MOVE 'AS01' TO CA-TRANID
015600         PERFORM 1000-FIRST-TIME
015700     ELSE
015800         MOVE DFHCOMMAREA TO CLR-COMMAREA
015900         PERFORM 2000-PROCESS-INPUT
016000     END-IF
016100     PERFORM 9000-RETURN
016200     GOBACK.
016300* ---------------------------------------------------------------*
016400* 1000-FIRST-TIME                                                *
016500* SEND THE EMPTY SCREEN                                          *
016600* ---------------------------------------------------------------*
016700 1000-FIRST-TIME.
016800     MOVE LOW-VALUES TO CLRM210O
016900     EXEC CICS SEND MAP('CLRM210') MAPSET('CLRMS03')
017000         ERASE FREEKB RESP(WS-RESP) END-EXEC
017100     .
017200* ---------------------------------------------------------------*
017300* 2000-PROCESS-INPUT                                             *
017400* PROCESS THE REQUEST                                            *
017500* ---------------------------------------------------------------*
017600 2000-PROCESS-INPUT.
017700     EXEC CICS RECEIVE MAP('CLRM210') MAPSET('CLRMS03')
017800         INTO(CLRM210I) RESP(WS-RESP) END-EXEC
017900     EVALUATE TRUE
018000         WHEN EIBAID = AID-PF3
018100         WHEN EIBAID = AID-CLEAR
018200             MOVE ZERO TO CA-RETURN-CD
018300             EXEC CICS RETURN END-EXEC
018400         WHEN EIBAID = AID-PF12
018500             PERFORM 1000-FIRST-TIME
018600         WHEN EIBAID = AID-ENTER
018700             PERFORM 2100-EDIT-INPUT
018800             IF WS-NO-ERROR
018900                 PERFORM 2200-APPLY
019000             END-IF
019100         WHEN OTHER
019200             MOVE 'INVALID KEY PRESSED' TO MSGO
019300     END-EVALUATE
019400     EXEC CICS SEND MAP('CLRM210') MAPSET('CLRMS03')
019500         DATAONLY FREEKB CURSOR RESP(WS-RESP) END-EXEC
019600     .
019700* ---------------------------------------------------------------*
019800* 2100-EDIT-INPUT                                                *
019900* VALIDATE THE REQUEST                                           *
020000* ---------------------------------------------------------------*
020100 2100-EDIT-INPUT.
020200     SET WS-NO-ERROR TO TRUE
020300     IF CLAIMIDL = ZERO OR CLAIMIDI = SPACES
020400         SET WS-ERROR-FOUND TO TRUE
020500         MOVE WS-MSG-01 TO MSGO
020600         MOVE -1 TO CLAIMIDL
020700     ELSE
020800         MOVE CLAIMIDI TO CA-CLAIM-ID
020900     END-IF
021000     PERFORM 1400-GET-BUSINESS-DATE
021100     .
021200* ---------------------------------------------------------------*
021300* 1400-GET-BUSINESS-DATE                                         *
021400* DETERMINE PROCESSING DATE                                      *
021500* ---------------------------------------------------------------*
021600 1400-GET-BUSINESS-DATE.
021700     MOVE WS-RUN-DATE TO DW-IN-DATE
021800     MOVE 'UK' TO DW-CALENDAR
021900     MOVE ZERO TO DW-BUS-DAYS
022000     CALL 'CLRCM010' USING CLR-DATE-WORK
022100                      CLR-ERROR-BLOCK
022200     IF ERR-SQLCODE NOT = ZERO
022300         MOVE 'CALL CLRCM010' TO ERR-PARA
022400         PERFORM 8000-SQL-ERROR
022500     END-IF
022600     .
022700* ---------------------------------------------------------------*
022800* 2200-APPLY                                                     *
022900* APPLY THE CHANGE                                               *
023000* ---------------------------------------------------------------*
023100 2200-APPLY.
023200     PERFORM 2300-READ-INSPECTION
023300     PERFORM 2500-EDIT-INSPECTION
023400     PERFORM 2510-EDIT-ASSESSMENT
023500     PERFORM 2520-EDIT-INSPECTION-2
023600     PERFORM 2530-EDIT-ASSESSMENT-2
023700     PERFORM 4100-INSERT-ASSESSMENT
023800     PERFORM 4900-WRITE-AUDIT
023900     IF WS-NO-ERROR
024000         EXEC CICS SYNCPOINT END-EXEC
024100         MOVE ZERO TO CA-RETURN-CD
024200     END-IF
024300     .
024400* ---------------------------------------------------------------*
024500* 2300-READ-INSPECTION                                           *
024600* FETCH CLR.T_INSPECTION                                         *
024700* ---------------------------------------------------------------*
024800 2300-READ-INSPECTION.
024900     SET WS-ROW-FOUND TO TRUE
025000     EXEC SQL
025100         SELECT INSP_ID, CLAIM_ID, BOOKED_TS
025200           INTO :INS-INSP-ID, :INS-CLAIM-ID, :INS-BOOKED-TS
025300           FROM CLR.T_INSPECTION
025400          WHERE INSP_ID = :INS-INSP-ID
025500     END-EXEC
025600     EVALUATE SQLCODE
025700         WHEN 0
025800             ADD 1 TO WS-INSPECTION-READ
025900         WHEN +100
026000             SET WS-ROW-NOT-FOUND TO TRUE
026100         WHEN OTHER
026200             MOVE 'READ CLR.T_INSPECTION' TO ERR-PARA
026300             PERFORM 8000-SQL-ERROR
026400     END-EVALUATE
026500     .
026600* ---------------------------------------------------------------*
026700* 2500-EDIT-INSPECTION                                           *
026800* VALIDATE CLR.T_INSPECTION                                      *
026900* ---------------------------------------------------------------*
027000 2500-EDIT-INSPECTION.
027100     IF INS-CLAIM-ID = SPACES OR LOW-VALUES
027200         ADD 1 TO WS-REJECT-CNT
027300         MOVE 'CLAIM_ID MISSING' TO ERR-TEXT
027400     END-IF
027500     .
027600* ---------------------------------------------------------------*
027700* 2510-EDIT-ASSESSMENT                                           *
027800* CHECK MANDATORY FIELDS IN CLR.T_ASSESSMENT                     *
027900* ---------------------------------------------------------------*
028000 2510-EDIT-ASSESSMENT.
028100     IF ASM-CLAIM-ID = SPACES OR LOW-VALUES
028200         ADD 1 TO WS-REJECT-CNT
028300         MOVE 'CLAIM_ID MISSING' TO ERR-TEXT
028400     END-IF
028500     IF ASM-ASSESS-TYPE-CD NOT = 'DK' AND ASM-ASSESS-TYPE-CD NOT =
028600         'SV' AND ASM-ASSESS-TYPE-CD NOT = 'VI'
028700         ADD 1 TO WS-REJECT-CNT
028800         MOVE 'ASSESS_TYPE_CD INVALID' TO ERR-TEXT
028900     END-IF
029000     .
029100* ---------------------------------------------------------------*
029200* 2520-EDIT-INSPECTION-2                                         *
029300* VALIDATE CLR.T_INSPECTION                                      *
029400* ---------------------------------------------------------------*
029500 2520-EDIT-INSPECTION-2.
029600     IF INS-INSP-ADDR = SPACES OR LOW-VALUES
029700         ADD 1 TO WS-REJECT-CNT
029800         MOVE 'INSP_ADDR MISSING' TO ERR-TEXT
029900     END-IF
030000     .
030100* ---------------------------------------------------------------*
030200* 2530-EDIT-ASSESSMENT-2                                         *
030300* CHECK MANDATORY FIELDS IN CLR.T_ASSESSMENT                     *
030400* ---------------------------------------------------------------*
030500 2530-EDIT-ASSESSMENT-2.
030600     IF ASM-COVER-DECISION-CD NOT = 'AC' AND ASM-COVER-DECISION-CD
030700         NOT = 'DC' AND ASM-COVER-DECISION-CD NOT = 'PA'
030800         ADD 1 TO WS-REJECT-CNT
030900         MOVE 'COVER_DECISION_CD INVALID' TO ERR-TEXT
031000     END-IF
031100     IF ASM-ESTIMATE-AMT NOT NUMERIC
031200         MOVE ZERO TO ASM-ESTIMATE-AMT
031300         ADD 1 TO WS-REJECT-CNT
031400     END-IF
031500     IF ASM-REPORT-RECEIVED-DT NOT = SPACES AND
031600         ASM-REPORT-RECEIVED-DT(5:1) NOT = '-'
031700         MOVE 'REPORT_RECEIVED_DT BAD DATE' TO ERR-TEXT
031800         ADD 1 TO WS-REJECT-CNT
031900     END-IF
032000     .
032100* ---------------------------------------------------------------*
032200* 4100-INSERT-ASSESSMENT                                         *
032300* INSERT CLR.T_ASSESSMENT                                        *
032400* ---------------------------------------------------------------*
032500 4100-INSERT-ASSESSMENT.
032600     MOVE CA-CLAIM-ID TO ASM-CLAIM-ID
032700     MOVE 'DK' TO ASM-ASSESS-TYPE-CD
032800     EXEC SQL
032900         INSERT INTO CLR.T_ASSESSMENT
033000              ( CLAIM_ID, ASSESS_TYPE_CD, COVER_DECISION_CD
033100              , ESTIMATE_AMT, REPORT_RECEIVED_DT, LAST_UPD_TS
033200              , LAST_UPD_PGM, LAST_UPD_USER )
033300         VALUES
033400              ( :ASM-CLAIM-ID, :ASM-ASSESS-TYPE-CD
033500              , :ASM-COVER-DECISION-CD, :ASM-ESTIMATE-AMT
033600              , :ASM-REPORT-RECEIVED-DT, CURRENT TIMESTAMP
033700              , :WS-PGM-ID, :WS-USER-ID )
033800     END-EXEC
033900     EVALUATE SQLCODE
034000         WHEN 0
034100             ADD 1 TO WS-ASSESSMENT-WRITTEN
034200         WHEN +100
034300             SET WS-ROW-NOT-FOUND TO TRUE
034400         WHEN OTHER
034500             MOVE 'INSERT CLR.T_ASSESSMENT' TO ERR-PARA
034600             PERFORM 8000-SQL-ERROR
034700     END-EVALUATE
034800     .
034900* ---------------------------------------------------------------*
035000* 4900-WRITE-AUDIT                                               *
035100* AUDIT TRAIL VIA CLRCM020                                       *
035200* ---------------------------------------------------------------*
035300 4900-WRITE-AUDIT.
035400     MOVE 'CLR.T_ASSESSMENT' TO WS-AUD-TABLE
035500     MOVE CA-CLAIM-ID TO WS-AUD-KEY
035600     MOVE 'I' TO WS-AUD-ACTION
035700     MOVE WS-USER-ID TO WS-AUD-USER
035800     MOVE WS-PGM-ID TO WS-AUD-PGM
035900     CALL 'CLRCM020' USING WS-AUDIT-PARMS
036000                      CLR-ERROR-BLOCK
036100     IF ERR-SQLCODE NOT = ZERO
036200         ADD 1 TO WS-REJECT-CNT
036300     END-IF
036400     .
036500* ---------------------------------------------------------------*
036600* 9000-RETURN                                                    *
036700* RETURN TO CICS                                                 *
036800* ---------------------------------------------------------------*
036900 9000-RETURN.
037000     EXEC CICS RETURN TRANSID('AS01') COMMAREA(CLR-COMMAREA)
037100         LENGTH(LENGTH OF CLR-COMMAREA) END-EXEC
037200     .
037300* ---------------------------------------------------------------*
037400* 8000-SQL-ERROR                                                 *
037500* SEVERE ERROR - REPORT AND STOP                                 *
037600* ---------------------------------------------------------------*
037700 8000-SQL-ERROR.
037800     MOVE SQLCODE TO ERR-SQLCODE WS-SQLCODE-DSP
037900     MOVE WS-PGM-ID TO ERR-PGM
038000     STRING 'SQLCODE ' WS-SQLCODE-DSP DELIMITED BY SIZE INTO
038100         ERR-TEXT
038200     CALL 'CLRCM050' USING CLR-ERROR-BLOCK
038300     EXEC CICS SYNCPOINT ROLLBACK END-EXEC
038400     MOVE 16 TO CA-RETURN-CD
038500     MOVE ERR-TEXT TO CA-MSG
038600     PERFORM 9000-RETURN
038700     .

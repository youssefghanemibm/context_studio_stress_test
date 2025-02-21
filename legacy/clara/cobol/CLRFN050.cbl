000100* ===============================================================*
000200* PROGRAM    : CLRFN050                                          *
000300* TITLE      : EVIDENCE INTAKE GATEWAY PHOTO AND TELEMATICS      *
000400*              REFERENCE IMPORT                                  *
000500* SYSTEM     : CLARA - CLAIMS LEDGER AND RESERVE APPLICATION     *
000600* AREA       : FNOL                                              *
000700* TYPE       : BATCH / DB2                                       *
000800* JOB / STEP : CLRNFN01 / STEP030                                *
000900* ---------------------------------------------------------------*
001000* PURPOSE                                                        *
001100*   BATCH PROGRAM: EVIDENCE INTAKE GATEWAY PHOTO AND TELEMATICS  *
001200*     REFERENCE IMPORT.                                          *
001300*   EXECUTED BY JOB CLRNFN01, STEP030.                           *
001400*   DB2 COMMIT AFTER EVERY 1000 UPDATES.                         *
001500*   CONDITION CODES: 00 NORMAL / 04 WARNING / 16 FAILURE.        *
001600* ---------------------------------------------------------------*
001700* DB2 TABLES                                                     *
001800*   CLR.T_FNOL_EVENT            READ                             *
001900*   CLR.T_DOCUMENT_REF          INSERT                           *
002000* COPYBOOKS  : DOCREF01 CLRFNL01 CLRERR01                        *
002100* CALLS      : CLRCM020                                          *
002200* FILE       : RPTOUT   OUT CONTROL REPORT                       *
002300* FILE       : IMPIN    IN  INBOUND INTERFACE FILE               *
002400* ---------------------------------------------------------------*
002500* MAINTENANCE HISTORY                                            *
002600* DATE       BY       REF        DESCRIPTION                     *
002700* ---------- -------- ---------- ------------------------------- *
002800* 1994-10-03 CLRPROJ             INITIAL VERSION - CLARA GO-LIVE *
002900* 2003-02-20 KBARR01             SQLCODE HANDLING ROUTED THROUGH *
003000*                                CLRERR01                        *
003100* 2016-02-21 PASHW01             ERROR MESSAGES STANDARDISED     *
003200* ===============================================================*
003300 IDENTIFICATION DIVISION.
003400 PROGRAM-ID.    CLRFN050.
003500 AUTHOR.        CLARA PROJECT TEAM.
003600 INSTALLATION.  CORVANE MUTUAL - CLAIMS SYSTEMS.
003700 DATE-WRITTEN.  1994-10-03.
003800 DATE-COMPILED.
003900 ENVIRONMENT DIVISION.
004000 CONFIGURATION SECTION.
004100 SOURCE-COMPUTER.  IBM-Z.
004200 OBJECT-COMPUTER.  IBM-Z.
004300 INPUT-OUTPUT SECTION.
004400 FILE-CONTROL.
004500     SELECT REPORT-FILE ASSIGN TO RPTOUT
004600        ORGANIZATION IS SEQUENTIAL
004700        FILE STATUS IS WS-RPTOUT-STATUS.
004800     SELECT INPUT-FILE ASSIGN TO IMPIN
004900        ORGANIZATION IS SEQUENTIAL
005000        FILE STATUS IS WS-IMPIN-STATUS.
005100 DATA DIVISION.
005200 FILE SECTION.
005300 FD  REPORT-FILE
005400        RECORDING MODE IS F
005500        BLOCK CONTAINS 0 RECORDS.
005600 01  REPORT-RECORD               PIC X(133).
005700 FD  INPUT-FILE
005800        RECORDING MODE IS F
005900        BLOCK CONTAINS 0 RECORDS.
006000 01  INPUT-RECORD                PIC X(400).
006100 WORKING-STORAGE SECTION.
006200*
006300 01  WS-PROGRAM-INFO.
006400     05  WS-PGM-ID               PIC X(8)   VALUE 'CLRFN050'.
006500     05  WS-RUN-DATE             PIC X(10)  VALUE SPACES.
006600     05  WS-RUN-TS               PIC X(26)  VALUE SPACES.
006700     05  WS-USER-ID              PIC X(8)   VALUE SPACES.
006800     05  WS-LAST-RUN-TS          PIC X(26)  VALUE SPACES.
006900     05  WS-RUN-ID               PIC S9(9)  COMP VALUE ZERO.
007000*
007100 01  WS-SWITCHES.
007200     05  WS-EOF-SW               PIC X      VALUE 'N'.
007300        88  WS-END-OF-DATA                     VALUE 'Y'.
007400     05  WS-ERROR-SW             PIC X      VALUE 'N'.
007500        88  WS-ERROR-FOUND                     VALUE 'Y'.
007600        88  WS-NO-ERROR                        VALUE 'N'.
007700     05  WS-FOUND-SW             PIC X      VALUE 'N'.
007800        88  WS-ROW-FOUND                       VALUE 'Y'.
007900        88  WS-ROW-NOT-FOUND                   VALUE 'N'.
008000     05  WS-RPTOUT-STATUS        PIC X(2)   VALUE SPACES.
008100     05  WS-IMPIN-STATUS         PIC X(2)   VALUE SPACES.
008200*
008300 01  WS-COUNTERS.
008400     05  WS-FNOL-EVENT-READ      PIC S9(9)  COMP-3 VALUE ZERO.
008500     05  WS-DOCUMENT-REF-WRITTEN PIC S9(9)  COMP-3 VALUE ZERO.
008600     05  WS-REJECT-CNT           PIC S9(9)  COMP-3 VALUE ZERO.
008700     05  WS-SINCE-COMMIT         PIC S9(9)  COMP-3 VALUE ZERO.
008800     05  WS-COMMIT-FREQ          PIC S9(9)  COMP-3 VALUE +1000.
008900*
009000 01  WS-SQL-WORK.
009100     05  WS-SQLCODE-DSP          PIC -9(9).
009200     05  WS-ROWS-AFFECTED        PIC S9(9)  COMP VALUE ZERO.
009300     05  WS-IND-1                PIC S9(4)  COMP VALUE ZERO.
009400     05  WS-IND-2                PIC S9(4)  COMP VALUE ZERO.
009500     05  WS-NEW-ID               PIC S9(18) COMP VALUE ZERO.
009600 01  WS-INPUT-AREA             PIC X(400).
009700*
009800     EXEC SQL INCLUDE SQLCA END-EXEC.
009900*
010000* CLARA RECORD LAYOUTS
010100 COPY DOCREF01.
010200 COPY CLRFNL01.
010300 COPY CLRERR01.
010400*
010500* PARAMETER AREAS FOR CALLED MODULES
010600 01  WS-AUDIT-PARMS.
010700     05  WS-AUD-TABLE            PIC X(18).
010800     05  WS-AUD-KEY              PIC X(30).
010900     05  WS-AUD-ACTION           PIC X(1).
011000     05  WS-AUD-USER             PIC X(8).
011100     05  WS-AUD-PGM              PIC X(8).
011200*
011300* CONTROL REPORT LINES
011400 01  WS-RPT-HEAD-1.
011500     05  FILLER                  PIC X(1)   VALUE '1'.
011600     05  FILLER                  PIC X(10)  VALUE 'CLRFN050'.
011700     05  FILLER                  PIC X(40)  VALUE
011800           'EVIDENCE INTAKE GATEWAY PHOTO AND'.
011900     05  FILLER                  PIC X(10)  VALUE 'RUN DATE: '.
012000     05  RH1-RUN-DATE            PIC X(10).
012100     05  FILLER                  PIC X(62)  VALUE SPACES.
012200 01  WS-RPT-DETAIL.
012300     05  FILLER                  PIC X(1)   VALUE SPACE.
012400     05  RD-LABEL                PIC X(40).
012500     05  RD-VALUE                PIC X(60).
012600     05  FILLER                  PIC X(32)  VALUE SPACES.
012700 01  WS-RPT-TOTAL.
012800     05  FILLER                  PIC X(1)   VALUE SPACE.
012900     05  RT-LABEL                PIC X(40).
013000     05  RT-COUNT                PIC ZZZ,ZZZ,ZZ9.
013100     05  FILLER                  PIC X(81)  VALUE SPACES.
013200 PROCEDURE DIVISION.
013300* ---------------------------------------------------------------*
013400* 0000-MAINLINE                                                  *
013500* PROGRAM CONTROL                                                *
013600* ---------------------------------------------------------------*
013700 0000-MAINLINE.
013800     PERFORM 1000-INITIALISE
013900     PERFORM 2000-PROCESS
014000     PERFORM 9000-TERMINATE
014100     GOBACK.
014200* ---------------------------------------------------------------*
014300* 1000-INITIALISE                                                *
014400* START OF RUN                                                   *
014500* ---------------------------------------------------------------*
014600 1000-INITIALISE.
014700     MOVE FUNCTION CURRENT-DATE(1:8) TO WS-RUN-TS
014800     STRING WS-RUN-TS(1:4) '-' WS-RUN-TS(5:2) '-' WS-RUN-TS(7:2)
014900        DELIMITED BY SIZE INTO WS-RUN-DATE
015000     MOVE 'CLRBATCH' TO WS-USER-ID
015100     OPEN OUTPUT REPORT-FILE
015200     IF WS-RPTOUT-STATUS NOT = '00'
015300        DISPLAY 'CLRFN050 OPEN FAILED RPTOUT ' WS-RPTOUT-STATUS
015400        MOVE 16 TO RETURN-CODE
015500        GOBACK
015600     END-IF
015700     OPEN INPUT INPUT-FILE
015800     IF WS-IMPIN-STATUS NOT = '00'
015900        DISPLAY 'CLRFN050 OPEN FAILED IMPIN ' WS-IMPIN-STATUS
016000        MOVE 16 TO RETURN-CODE
016100        GOBACK
016200     END-IF
016300     MOVE WS-RUN-DATE TO RH1-RUN-DATE
016400     WRITE REPORT-RECORD FROM WS-RPT-HEAD-1
016500     .
016600* ---------------------------------------------------------------*
016700* 2000-PROCESS                                                   *
016800* PROCESS LOOP                                                   *
016900* ---------------------------------------------------------------*
017000 2000-PROCESS.
017100     PERFORM 2100-READ-INPUT
017200     PERFORM UNTIL WS-END-OF-DATA
017300        PERFORM 2200-PROCESS-ROW
017400        PERFORM 2100-READ-INPUT
017500     END-PERFORM
017600     .
017700* ---------------------------------------------------------------*
017800* 2100-READ-INPUT                                                *
017900* READ THE NEXT INPUT RECORD                                     *
018000* ---------------------------------------------------------------*
018100 2100-READ-INPUT.
018200     READ INPUT-FILE
018300        AT END
018400           SET WS-END-OF-DATA TO TRUE
018500        NOT AT END
018600           CONTINUE
018700     END-READ
018800     .
018900* ---------------------------------------------------------------*
019000* 2200-PROCESS-ROW                                               *
019100* PROCESS ONE ROW                                                *
019200* ---------------------------------------------------------------*
019300 2200-PROCESS-ROW.
019400     SET WS-NO-ERROR TO TRUE
019500     MOVE INPUT-RECORD TO WS-INPUT-AREA
019600     PERFORM 2300-READ-FNOL-EVENT
019700     PERFORM 4100-INSERT-DOCUMENT-REF
019800     PERFORM 4900-WRITE-AUDIT
019900     PERFORM 6000-COMMIT-CHECK
020000     .
020100* ---------------------------------------------------------------*
020200* 2300-READ-FNOL-EVENT                                           *
020300* LOOK UP CLR.T_FNOL_EVENT                                       *
020400* ---------------------------------------------------------------*
020500 2300-READ-FNOL-EVENT.
020600     SET WS-ROW-FOUND TO TRUE
020700     EXEC SQL
020800         SELECT FNOL_ID, CLAIM_ID, CHANNEL_CD, RECEIVED_TS
020900                , PAYLOAD_REF
021000           INTO :FNL-FNOL-ID, :FNL-CLAIM-ID, :FNL-CHANNEL-CD
021100                , :FNL-RECEIVED-TS, :FNL-PAYLOAD-REF
021200           FROM CLR.T_FNOL_EVENT
021300          WHERE FNOL_ID = :FNL-FNOL-ID
021400     END-EXEC
021500     EVALUATE SQLCODE
021600        WHEN 0
021700           ADD 1 TO WS-FNOL-EVENT-READ
021800        WHEN +100
021900           SET WS-ROW-NOT-FOUND TO TRUE
022000        WHEN OTHER
022100           MOVE 'READ CLR.T_FNOL_EVENT' TO ERR-PARA
022200           PERFORM 8000-SQL-ERROR
022300     END-EVALUATE
022400     .
022500* ---------------------------------------------------------------*
022600* 4100-INSERT-DOCUMENT-REF                                       *
022700* INSERT CLR.T_DOCUMENT_REF                                      *
022800* ---------------------------------------------------------------*
022900 4100-INSERT-DOCUMENT-REF.
023000     MOVE FNL-CLAIM-ID TO DOCR-CLAIM-ID
023100     EXEC SQL
023200         INSERT INTO CLR.T_DOCUMENT_REF
023300              ( CLAIM_ID, VAULT_OBJECT_ID, DOC_TYPE_CD
023400              , RECEIVED_TS, LAST_UPD_TS, LAST_UPD_PGM
023500              , LAST_UPD_USER )
023600         VALUES
023700              ( :DOCR-CLAIM-ID, :DOCR-VAULT-OBJECT-ID
023800              , :DOCR-DOC-TYPE-CD, CURRENT TIMESTAMP
023900              , CURRENT TIMESTAMP, :WS-PGM-ID, :WS-USER-ID )
024000     END-EXEC
024100     EVALUATE SQLCODE
024200        WHEN 0
024300           ADD 1 TO WS-DOCUMENT-REF-WRITTEN
024400        WHEN +100
024500           SET WS-ROW-NOT-FOUND TO TRUE
024600        WHEN OTHER
024700           MOVE 'INSERT CLR.T_DOCUMENT_REF' TO ERR-PARA
024800           PERFORM 8000-SQL-ERROR
024900     END-EVALUATE
025000     .
025100* ---------------------------------------------------------------*
025200* 4900-WRITE-AUDIT                                               *
025300* AUDIT TRAIL VIA CLRCM020                                       *
025400* ---------------------------------------------------------------*
025500 4900-WRITE-AUDIT.
025600     MOVE 'CLR.T_DOCUMENT_REF' TO WS-AUD-TABLE
025700     MOVE FNL-CLAIM-ID TO WS-AUD-KEY
025800     MOVE 'A' TO WS-AUD-ACTION
025900     MOVE WS-USER-ID TO WS-AUD-USER
026000     MOVE WS-PGM-ID TO WS-AUD-PGM
026100     CALL 'CLRCM020' USING WS-AUDIT-PARMS
026200                      CLR-ERROR-BLOCK
026300     IF ERR-SQLCODE NOT = ZERO
026400        ADD 1 TO WS-REJECT-CNT
026500     END-IF
026600     .
026700* ---------------------------------------------------------------*
026800* 6000-COMMIT-CHECK                                              *
026900* PERIODIC COMMIT                                                *
027000* ---------------------------------------------------------------*
027100 6000-COMMIT-CHECK.
027200     ADD 1 TO WS-SINCE-COMMIT
027300     IF WS-SINCE-COMMIT >= WS-COMMIT-FREQ
027400        EXEC SQL
027500            COMMIT
027600        END-EXEC
027700        MOVE ZERO TO WS-SINCE-COMMIT
027800     END-IF
027900     .
028000* ---------------------------------------------------------------*
028100* 9000-TERMINATE                                                 *
028200* CLOSE DOWN                                                     *
028300* ---------------------------------------------------------------*
028400 9000-TERMINATE.
028500     EXEC SQL
028600         COMMIT
028700     END-EXEC
028800     MOVE 'CLR.T_FNOL_EVENT ROWS READ' TO RT-LABEL
028900     MOVE WS-FNOL-EVENT-READ TO RT-COUNT
029000     WRITE REPORT-RECORD FROM WS-RPT-TOTAL
029100     MOVE 'CLR.T_DOCUMENT_REF ROWS WRITTEN' TO RT-LABEL
029200     MOVE WS-DOCUMENT-REF-WRITTEN TO RT-COUNT
029300     WRITE REPORT-RECORD FROM WS-RPT-TOTAL
029400     CLOSE REPORT-FILE
029500     CLOSE INPUT-FILE
029600     IF WS-REJECT-CNT > ZERO
029700        MOVE 4 TO RETURN-CODE
029800     END-IF
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
030900     DISPLAY WS-PGM-ID ' ' ERR-PARA ' ' ERR-TEXT
031000     EXEC SQL
031100         ROLLBACK
031200     END-EXEC
031300     MOVE 16 TO RETURN-CODE
031400     CLOSE REPORT-FILE
031500     CLOSE INPUT-FILE
031600     GOBACK.

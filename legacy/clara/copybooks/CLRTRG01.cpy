000100* ===============================================================*
000200* COPYBOOK   : CLRTRG01                                          *
000300* DB2 TABLE  : CLR.T_TRIAGE                                      *
000400* CONTENT    : TRIAGE DECISIONS                                  *
000500* LAYOUT     : ONE FIELD PER COLUMN, IN TABLE ORDER              *
000600* ===============================================================*
000700 01  CLRTRG01-REC.
000800     05  TRG-CLAIM-ID                  PIC X(12).
000900     05  TRG-TRIAGE-SEQ                PIC S9(4) COMP.
001000     05  TRG-TRIAGE-TS                 PIC X(26).
001100     05  TRG-ROUTE-CD                  PIC X(4).
001200     05  TRG-SCORE-AT-TRIAGE           PIC S9(4) COMP.
001300     05  TRG-FASTTRACK-FLAG            PIC X(1).
001400     05  TRG-BRANCH-CD                 PIC X(3).
001500     05  TRG-CREATED-TS                PIC X(26).
001600     05  TRG-SOURCE-SYS-CD             PIC X(4).
001700     05  TRG-LAST-UPD-TS               PIC X(26).
001800     05  TRG-LAST-UPD-PGM              PIC X(8).
001900     05  TRG-LAST-UPD-USER             PIC X(8).

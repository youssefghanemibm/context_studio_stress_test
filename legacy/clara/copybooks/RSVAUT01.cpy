000100* ===============================================================*
000200* COPYBOOK   : RSVAUT01                                          *
000300* DB2 TABLE  : CLR.T_RESERVE_AUTHORITY                           *
000400* CONTENT    : RESERVE APPROVALS ABOVE AUTHORITY (BR-RSV-003)    *
000500* LAYOUT     : ONE FIELD PER COLUMN, IN TABLE ORDER              *
000600* ===============================================================*
000700 01  RSVAUT01-REC.
000800     05  RSVA-AUTH-ID                  PIC S9(18) COMP.
000900     05  RSVA-RSV-ID                   PIC S9(18) COMP.
001000     05  RSVA-REQUESTED-AMT            PIC S9(11)V99 COMP-3.
001100     05  RSVA-REQUIRED-LEVEL           PIC X(2).
001200     05  RSVA-APPROVER-USER            PIC X(8).
001300     05  RSVA-DECISION-CD              PIC X(2).
001400     05  RSVA-LAST-UPD-TS              PIC X(26).
001500     05  RSVA-LAST-UPD-PGM             PIC X(8).
001600     05  RSVA-LAST-UPD-USER            PIC X(8).

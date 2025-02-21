000100* ===============================================================*
000200* COPYBOOK   : STLREC01                                          *
000300* DB2 TABLE  : CLR.T_SETTLEMENT                                  *
000400* CONTENT    : SETTLEMENTS                                       *
000500* LAYOUT     : ONE FIELD PER COLUMN, IN TABLE ORDER              *
000600* ===============================================================*
000700 01  STLREC01-REC.
000800     05  STLR-SETTLE-ID                PIC S9(18) COMP.
000900     05  STLR-CLAIM-ID                 PIC X(12).
001000     05  STLR-OFFER-AMT                PIC S9(11)V99 COMP-3.
001100     05  STLR-OFFER-DT                 PIC X(10).
001200     05  STLR-ACCEPTED-DT              PIC X(10).
001300     05  STLR-FINAL-FLAG               PIC X(1).
001400     05  STLR-EXCESS-APPLIED-AMT       PIC S9(9)V99 COMP-3.
001500     05  STLR-ARCHIVE-FLAG             PIC X(1).
001600     05  STLR-CREATED-TS               PIC X(26).
001700     05  STLR-EXT-REF                  PIC X(20).
001800     05  STLR-LAST-UPD-TS              PIC X(26).
001900     05  STLR-LAST-UPD-PGM             PIC X(8).
002000     05  STLR-LAST-UPD-USER            PIC X(8).

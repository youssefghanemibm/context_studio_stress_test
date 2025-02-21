000100* ===============================================================*
000200* COPYBOOK   : CURRATE1                                          *
000300* DB2 TABLE  : CLR.T_CURRENCY_RATE                               *
000400* CONTENT    : CURRENCY RATES LOADED FROM GROUP LEDGER           *
000500*              (CLX-IF-027)                                      *
000600* LAYOUT     : ONE FIELD PER COLUMN, IN TABLE ORDER              *
000700* ===============================================================*
000800 01  CURRATE1-REC.
000900     05  CURR-CURRENCY-CD              PIC X(3).
001000     05  CURR-RATE-DT                  PIC X(10).
001100     05  CURR-RATE-TO-GBP              PIC S9(4)V9(7) COMP-3.
001200     05  CURR-RATE-TYPE-CD             PIC X(2).
001300     05  CURR-ARCHIVE-FLAG             PIC X(1).
001400     05  CURR-COMMENT-TXT              PIC X(254).
001500     05  CURR-CREATED-TS               PIC X(26).
001600     05  CURR-LAST-UPD-TS              PIC X(26).
001700     05  CURR-LAST-UPD-PGM             PIC X(8).
001800     05  CURR-LAST-UPD-USER            PIC X(8).

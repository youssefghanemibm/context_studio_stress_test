000100* ================================================================
000200* COPYBOOK   : NISARET1
000300* DB2 TABLE  : CLR.T_NISA_RETURN
000400* CONTENT    : NISA RETURN STAGING
000500* LAYOUT     : ONE FIELD PER COLUMN, IN TABLE ORDER
000600* ================================================================
000700 01  NISARET1-REC.
000800     05  NISA-RETURN-CD                PIC X(6).
000900     05  NISA-PERIOD-CD                PIC X(6).
001000     05  NISA-CELL-REF                 PIC X(10).
001100     05  NISA-CELL-VALUE               PIC S9(15)V99 COMP-3.
001200     05  NISA-SUBMITTED-DT             PIC X(10).
001300     05  NISA-ARCHIVE-FLAG             PIC X(1).
001400     05  NISA-COMMENT-TXT              PIC X(254).
001500     05  NISA-LAST-UPD-TS              PIC X(26).
001600     05  NISA-LAST-UPD-PGM             PIC X(8).
001700     05  NISA-LAST-UPD-USER            PIC X(8).

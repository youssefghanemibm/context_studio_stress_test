000100* ================================================================
000200* COPYBOOK   : CLREST01
000300* DB2 TABLE  : CLR.T_ESTIMATE
000400* CONTENT    : REPAIR AND REPLACEMENT ESTIMATES
000500* LAYOUT     : ONE FIELD PER COLUMN, IN TABLE ORDER
000600* ================================================================
000700 01  CLREST01-REC.
000800     05  EST-EST-ID                    PIC S9(18) COMP.
000900     05  EST-CLAIM-ID                  PIC X(12).
001000     05  EST-EST-LINE-NO               PIC S9(4) COMP.
001100     05  EST-EST-ITEM-DESC             PIC X(120).
001200     05  EST-EST-AMT                   PIC S9(9)V99 COMP-3.
001300     05  EST-REPAIRER-CD               PIC X(8).
001400     05  EST-EXT-REF                   PIC X(20).
001500     05  EST-LAST-UPD-TS               PIC X(26).
001600     05  EST-LAST-UPD-PGM              PIC X(8).
001700     05  EST-LAST-UPD-USER             PIC X(8).

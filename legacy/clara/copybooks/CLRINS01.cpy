000100* ================================================================
000200* COPYBOOK   : CLRINS01
000300* DB2 TABLE  : CLR.T_INSPECTION
000400* CONTENT    : INSPECTIONS
000500* LAYOUT     : ONE FIELD PER COLUMN, IN TABLE ORDER
000600* ================================================================
000700 01  CLRINS01-REC.
000800     05  INS-INSP-ID                   PIC S9(18) COMP.
000900     05  INS-CLAIM-ID                  PIC X(12).
001000     05  INS-BOOKED-TS                 PIC X(26).
001100     05  INS-COMPLETED-TS              PIC X(26).
001200     05  INS-INSP-ADDR                 PIC X(120).
001300     05  INS-CREATED-TS                PIC X(26).
001400     05  INS-LAST-UPD-TS               PIC X(26).
001500     05  INS-LAST-UPD-PGM              PIC X(8).
001600     05  INS-LAST-UPD-USER             PIC X(8).

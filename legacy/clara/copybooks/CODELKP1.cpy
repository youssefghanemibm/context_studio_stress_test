000100* ================================================================
000200* COPYBOOK   : CODELKP1
000300* DB2 TABLE  : CLR.T_CODE_LOOKUP
000400* CONTENT    : CODE LOOKUP VALUES
000500* LAYOUT     : ONE FIELD PER COLUMN, IN TABLE ORDER
000600* ================================================================
000700 01  CODELKP1-REC.
000800     05  CODE-CODE-TYPE                PIC X(8).
000900     05  CODE-CODE-VALUE               PIC X(6).
001000     05  CODE-CODE-DESC-EN             PIC X(60).
001100     05  CODE-CODE-DESC-LOCAL          PIC X(60).
001200     05  CODE-ACTIVE-FLAG              PIC X(1).
001300     05  CODE-LAST-UPD-TS              PIC X(26).
001400     05  CODE-LAST-UPD-PGM             PIC X(8).
001500     05  CODE-LAST-UPD-USER            PIC X(8).

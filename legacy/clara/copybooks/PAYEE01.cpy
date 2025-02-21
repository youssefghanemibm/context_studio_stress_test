000100* ================================================================
000200* COPYBOOK   : PAYEE01
000300* DB2 TABLE  : CLR.T_PAYEE
000400* CONTENT    : PAYEES
000500* LAYOUT     : ONE FIELD PER COLUMN, IN TABLE ORDER
000600* ================================================================
000700 01  PAYEE01-REC.
000800     05  PAYE-PAYEE-ID                 PIC X(10).
000900     05  PAYE-PAYEE-NAME               PIC X(80).
001000     05  PAYE-IBAN                     PIC X(34).
001100     05  PAYE-SORT-CODE                PIC X(6).
001200     05  PAYE-PAYEE-TYPE-CD            PIC X(2).
001300     05  PAYE-CREATED-TS               PIC X(26).
001400     05  PAYE-SOURCE-SYS-CD            PIC X(4).
001500     05  PAYE-LAST-UPD-TS              PIC X(26).
001600     05  PAYE-LAST-UPD-PGM             PIC X(8).
001700     05  PAYE-LAST-UPD-USER            PIC X(8).

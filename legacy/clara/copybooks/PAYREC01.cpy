000100* ===============================================================*
000200* COPYBOOK   : PAYREC01                                          *
000300* DB2 TABLE  : CLR.T_PAYMENT                                     *
000400* CONTENT    : PAYMENTS                                          *
000500* LAYOUT     : ONE FIELD PER COLUMN, IN TABLE ORDER              *
000600* ===============================================================*
000700 01  PAYREC01-REC.
000800     05  PAYR-PAY-ID                   PIC S9(18) COMP.
000900     05  PAYR-CLAIM-ID                 PIC X(12).
001000     05  PAYR-PAYEE-ID                 PIC X(10).
001100     05  PAYR-PAY-AMT                  PIC S9(11)V99 COMP-3.
001200     05  PAYR-CURRENCY-CD              PIC X(3).
001300     05  PAYR-PAY-STATUS               PIC X(2).
001400     05  PAYR-AUTH-USER                PIC X(8).
001500     05  PAYR-SANCTIONS-RESULT         PIC X(2).
001600     05  PAYR-COMMENT-TXT              PIC X(254).
001700     05  PAYR-LAST-UPD-TS              PIC X(26).
001800     05  PAYR-LAST-UPD-PGM             PIC X(8).
001900     05  PAYR-LAST-UPD-USER            PIC X(8).

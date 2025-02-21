000100* ================================================================
000200* COPYBOOK   : SUBCAS01
000300* DB2 TABLE  : CLR.T_SUBROGATION_CASE
000400* CONTENT    : SUBROGATION CASES
000500* LAYOUT     : ONE FIELD PER COLUMN, IN TABLE ORDER
000600* ================================================================
000700 01  SUBCAS01-REC.
000800     05  SUBC-SUBRO-CASE-ID            PIC X(10).
000900     05  SUBC-CLAIM-ID                 PIC X(12).
001000     05  SUBC-TP-INSURER-NAME          PIC X(80).
001100     05  SUBC-TP-REF                   PIC X(20).
001200     05  SUBC-DEMAND-AMT               PIC S9(11)V99 COMP-3.
001300     05  SUBC-DEMAND-DT                PIC X(10).
001400     05  SUBC-SOLICITOR-VENDOR-CD      PIC X(8).
001500     05  SUBC-LIMITATION-DT            PIC X(10).
001600     05  SUBC-CASE-STATUS              PIC X(2).
001700     05  SUBC-SUBTRAK-REF              PIC X(12).
001800     05  SUBC-LAST-UPD-TS              PIC X(26).
001900     05  SUBC-LAST-UPD-PGM             PIC X(8).
002000     05  SUBC-LAST-UPD-USER            PIC X(8).

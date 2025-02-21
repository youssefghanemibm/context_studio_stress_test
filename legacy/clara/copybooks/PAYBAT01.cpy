000100* ================================================================
000200* COPYBOOK   : PAYBAT01
000300* DB2 TABLE  : CLR.T_PAYMENT_BATCH
000400* CONTENT    : PAYMENT BATCHES TO CPG
000500* LAYOUT     : ONE FIELD PER COLUMN, IN TABLE ORDER
000600* ================================================================
000700 01  PAYBAT01-REC.
000800     05  PAYB-BATCH-ID                 PIC S9(9) COMP.
000900     05  PAYB-BATCH-DT                 PIC X(10).
001000     05  PAYB-PAY-COUNT                PIC S9(9) COMP.
001100     05  PAYB-TOTAL-AMT                PIC S9(13)V99 COMP-3.
001200     05  PAYB-CPG-FILE-NAME            PIC X(44).
001300     05  PAYB-CPG-ACK-TS               PIC X(26).
001400     05  PAYB-LAST-UPD-TS              PIC X(26).
001500     05  PAYB-LAST-UPD-PGM             PIC X(8).
001600     05  PAYB-LAST-UPD-USER            PIC X(8).

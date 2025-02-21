000100* ================================================================
000200* COPYBOOK   : VENINV01
000300* DB2 TABLE  : CLR.T_VENDOR_INVOICE
000400* CONTENT    : VENDOR INVOICES
000500* LAYOUT     : ONE FIELD PER COLUMN, IN TABLE ORDER
000600* ================================================================
000700 01  VENINV01-REC.
000800     05  VENI-INVOICE-ID               PIC S9(18) COMP.
000900     05  VENI-VENDOR-CD                PIC X(8).
001000     05  VENI-CLAIM-ID                 PIC X(12).
001100     05  VENI-INVOICE-AMT              PIC S9(9)V99 COMP-3.
001200     05  VENI-FEE-TYPE-CD              PIC X(2).
001300     05  VENI-MATCHED-FLAG             PIC X(1).
001400     05  VENI-LAST-UPD-TS              PIC X(26).
001500     05  VENI-LAST-UPD-PGM             PIC X(8).
001600     05  VENI-LAST-UPD-USER            PIC X(8).

000100* ================================================================
000200* COPYBOOK   : CLRPOL01
000300* DB2 TABLE  : CLR.T_POLICY_SNAPSHOT
000400* CONTENT    : POLICY SNAPSHOT COPIED FROM PALM AT FNOL
000500* LAYOUT     : ONE FIELD PER COLUMN, IN TABLE ORDER
000600* ================================================================
000700 01  CLRPOL01-REC.
000800     05  POL-POLICY-NO                 PIC X(10).
000900     05  POL-SNAPSHOT-DT               PIC X(10).
001000     05  POL-PRODUCT-CD                PIC X(6).
001100     05  POL-COVER-START-DT            PIC X(10).
001200     05  POL-COVER-END-DT              PIC X(10).
001300     05  POL-EXCESS-AMT                PIC S9(9)V99 COMP-3.
001400     05  POL-SUM-INSURED-AMT           PIC S9(11)V99 COMP-3.
001500     05  POL-PH-POSTCODE               PIC X(8).
001600     05  POL-BRANCH-CD                 PIC X(3).
001700     05  POL-LAST-UPD-TS               PIC X(26).
001800     05  POL-LAST-UPD-PGM              PIC X(8).
001900     05  POL-LAST-UPD-USER             PIC X(8).

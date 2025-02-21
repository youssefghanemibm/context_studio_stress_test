000100* ================================================================
000200* COPYBOOK   : CLRCLT01
000300* DB2 TABLE  : CLR.T_CLAIMANT
000400* CONTENT    : CLAIMANTS AND THIRD PARTIES
000500* LAYOUT     : ONE FIELD PER COLUMN, IN TABLE ORDER
000600* ================================================================
000700 01  CLRCLT01-REC.
000800     05  CLT-CLAIMANT-ID               PIC X(10).
000900     05  CLT-FAMILY-NAME               PIC X(60).
001000     05  CLT-GIVEN-NAME                PIC X(60).
001100     05  CLT-DOB                       PIC X(10).
001200     05  CLT-NI-NO                     PIC X(13).
001300     05  CLT-ADDR-LINE1                PIC X(80).
001400     05  CLT-POSTCODE                  PIC X(8).
001500     05  CLT-PHONE-NO                  PIC X(16).
001600     05  CLT-EMAIL-ADDR                PIC X(120).
001700     05  CLT-PARTY-ROLE-CD             PIC X(2).
001800     05  CLT-VULNERABLE-FLAG           PIC X(1).
001900     05  CLT-LAST-UPD-TS               PIC X(26).
002000     05  CLT-LAST-UPD-PGM              PIC X(8).
002100     05  CLT-LAST-UPD-USER             PIC X(8).

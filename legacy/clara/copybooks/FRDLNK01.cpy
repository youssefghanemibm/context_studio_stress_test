000100* ================================================================
000200* COPYBOOK   : FRDLNK01
000300* DB2 TABLE  : CLR.T_CLAIM_LINK
000400* CONTENT    : LINKED CLAIMS (SHARED PARTIES, VEHICLES, BANK
000500*              ACCOUNTS)
000600* LAYOUT     : ONE FIELD PER COLUMN, IN TABLE ORDER
000700* ================================================================
000800 01  FRDLNK01-REC.
000900     05  FRDL-LINK-ID                  PIC S9(18) COMP.
001000     05  FRDL-CLAIM-ID-A               PIC X(12).
001100     05  FRDL-CLAIM-ID-B               PIC X(12).
001200     05  FRDL-LINK-TYPE-CD             PIC X(2).
001300     05  FRDL-DETECTED-DT              PIC X(10).
001400     05  FRDL-BATCH-RUN-ID             PIC S9(9) COMP.
001500     05  FRDL-EXT-REF                  PIC X(20).
001600     05  FRDL-VERSION-NO               PIC S9(4) COMP.
001700     05  FRDL-LAST-UPD-TS              PIC X(26).
001800     05  FRDL-LAST-UPD-PGM             PIC X(8).
001900     05  FRDL-LAST-UPD-USER            PIC X(8).

000100* ================================================================
000200* COPYBOOK   : FRDSIU01
000300* DB2 TABLE  : CLR.T_SIU_CASE
000400* CONTENT    : SIU CASE MIRROR
000500* LAYOUT     : ONE FIELD PER COLUMN, IN TABLE ORDER
000600* ================================================================
000700 01  FRDSIU01-REC.
000800     05  FRDS-SIU-CASE-ID              PIC X(10).
000900     05  FRDS-REF-ID                   PIC S9(18) COMP.
001000     05  FRDS-INVESTIGATOR-USER        PIC X(8).
001100     05  FRDS-OPENED-DT                PIC X(10).
001200     05  FRDS-CASE-STATUS              PIC X(2).
001300     05  FRDS-PARTNER-VENDOR-CD        PIC X(8).
001400     05  FRDS-BRANCH-CD                PIC X(3).
001500     05  FRDS-VERSION-NO               PIC S9(4) COMP.
001600     05  FRDS-LAST-UPD-TS              PIC X(26).
001700     05  FRDS-LAST-UPD-PGM             PIC X(8).
001800     05  FRDS-LAST-UPD-USER            PIC X(8).

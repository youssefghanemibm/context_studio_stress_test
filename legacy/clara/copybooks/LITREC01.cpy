000100* ===============================================================*
000200* COPYBOOK   : LITREC01                                          *
000300* DB2 TABLE  : CLR.T_LITIGATION                                  *
000400* CONTENT    : LITIGATION AND SOLICITOR INSTRUCTIONS             *
000500* LAYOUT     : ONE FIELD PER COLUMN, IN TABLE ORDER              *
000600* ===============================================================*
000700 01  LITREC01-REC.
000800     05  LITR-LIT-ID                   PIC S9(18) COMP.
000900     05  LITR-CLAIM-ID                 PIC X(12).
001000     05  LITR-SOLICITOR-VENDOR-CD      PIC X(8).
001100     05  LITR-INSTRUCTED-DT            PIC X(10).
001200     05  LITR-COURT-REF                PIC X(20).
001300     05  LITR-LIT-STATUS               PIC X(2).
001400     05  LITR-BRANCH-CD                PIC X(3).
001500     05  LITR-CREATED-TS               PIC X(26).
001600     05  LITR-EXT-REF                  PIC X(20).
001700     05  LITR-LAST-UPD-TS              PIC X(26).
001800     05  LITR-LAST-UPD-PGM             PIC X(8).
001900     05  LITR-LAST-UPD-USER            PIC X(8).

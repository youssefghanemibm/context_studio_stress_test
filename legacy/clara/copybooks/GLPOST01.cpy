000100* ================================================================
000200* COPYBOOK   : GLPOST01
000300* DB2 TABLE  : CLR.T_GL_POSTING
000400* CONTENT    : GL POSTINGS (PAYMENTS AND RECOVERIES)
000500* LAYOUT     : ONE FIELD PER COLUMN, IN TABLE ORDER
000600* ================================================================
000700 01  GLPOST01-REC.
000800     05  GLPO-POSTING-ID               PIC S9(18) COMP.
000900     05  GLPO-GL-PERIOD                PIC X(6).
001000     05  GLPO-ACCOUNT-CD               PIC X(10).
001100     05  GLPO-DR-CR                    PIC X(1).
001200     05  GLPO-AMOUNT-GBP               PIC S9(13)V99 COMP-3.
001300     05  GLPO-SOURCE-PGM               PIC X(8).
001400     05  GLPO-CREATED-TS               PIC X(26).
001500     05  GLPO-EXT-REF                  PIC X(20).
001600     05  GLPO-VERSION-NO               PIC S9(4) COMP.
001700     05  GLPO-LAST-UPD-TS              PIC X(26).
001800     05  GLPO-LAST-UPD-PGM             PIC X(8).
001900     05  GLPO-LAST-UPD-USER            PIC X(8).

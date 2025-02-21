000100* ===============================================================*
000200* COPYBOOK   : RSVHIS01                                          *
000300* DB2 TABLE  : CLR.T_RESERVE_HISTORY                             *
000400* CONTENT    : ARCHIVED RESERVE SNAPSHOTS (MONTH-END)            *
000500* LAYOUT     : ONE FIELD PER COLUMN, IN TABLE ORDER              *
000600* ===============================================================*
000700 01  RSVHIS01-REC.
000800     05  RSVH-RSV-ID                   PIC S9(18) COMP.
000900     05  RSVH-SNAPSHOT-DT              PIC X(10).
001000     05  RSVH-RSV-OUTSTANDING-AMT      PIC S9(11)V99 COMP-3.
001100     05  RSVH-RSV-GBP-EQUIV-AMT        PIC S9(11)V99 COMP-3.
001200     05  RSVH-TIER-CD                  PIC X(1).
001300     05  RSVH-COMMENT-TXT              PIC X(254).
001400     05  RSVH-CREATED-TS               PIC X(26).
001500     05  RSVH-LAST-UPD-TS              PIC X(26).
001600     05  RSVH-LAST-UPD-PGM             PIC X(8).
001700     05  RSVH-LAST-UPD-USER            PIC X(8).

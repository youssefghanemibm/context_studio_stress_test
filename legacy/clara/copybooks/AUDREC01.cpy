000100* ===============================================================*
000200* COPYBOOK   : AUDREC01                                          *
000300* DB2 TABLE  : CLR.T_AUDIT                                       *
000400* CONTENT    : AUDIT TRAIL                                       *
000500* LAYOUT     : ONE FIELD PER COLUMN, IN TABLE ORDER              *
000600* ===============================================================*
000700 01  AUDREC01-REC.
000800     05  AUDR-AUDIT-ID                 PIC S9(18) COMP.
000900     05  AUDR-AUDIT-TS                 PIC X(26).
001000     05  AUDR-USER-ID                  PIC X(8).
001100     05  AUDR-PGM-ID                   PIC X(8).
001200     05  AUDR-TABLE-NAME               PIC X(18).
001300     05  AUDR-KEY-VALUE                PIC X(30).
001400     05  AUDR-ACTION-CD                PIC X(1).
001500     05  AUDR-ARCHIVE-FLAG             PIC X(1).
001600     05  AUDR-BRANCH-CD                PIC X(3).
001700     05  AUDR-EXT-REF                  PIC X(20).
001800     05  AUDR-LAST-UPD-TS              PIC X(26).
001900     05  AUDR-LAST-UPD-PGM             PIC X(8).
002000     05  AUDR-LAST-UPD-USER            PIC X(8).

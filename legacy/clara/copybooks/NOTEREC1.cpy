000100* ===============================================================*
000200* COPYBOOK   : NOTEREC1                                          *
000300* DB2 TABLE  : CLR.T_NOTE                                        *
000400* CONTENT    : CLAIM NOTES                                       *
000500* LAYOUT     : ONE FIELD PER COLUMN, IN TABLE ORDER              *
000600* ===============================================================*
000700 01  NOTEREC1-REC.
000800     05  NOTE-NOTE-ID                  PIC S9(18) COMP.
000900     05  NOTE-CLAIM-ID                 PIC X(12).
001000     05  NOTE-NOTE-TS                  PIC X(26).
001100     05  NOTE-NOTE-TXT                 PIC X(2000).
001200     05  NOTE-NOTE-TYPE-CD             PIC X(2).
001300     05  NOTE-LAST-UPD-TS              PIC X(26).
001400     05  NOTE-LAST-UPD-PGM             PIC X(8).
001500     05  NOTE-LAST-UPD-USER            PIC X(8).

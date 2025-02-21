000100* ===============================================================*
000200* COPYBOOK   : DIARYRC1                                          *
000300* DB2 TABLE  : CLR.T_DIARY                                       *
000400* CONTENT    : DIARY AND REMINDERS (RESERVE REVIEWS, LIMITATION  *
000500*              DATES)                                            *
000600* LAYOUT     : ONE FIELD PER COLUMN, IN TABLE ORDER              *
000700* ===============================================================*
000800 01  DIARYRC1-REC.
000900     05  DIAR-DIARY-ID                 PIC S9(18) COMP.
001000     05  DIAR-CLAIM-ID                 PIC X(12).
001100     05  DIAR-DUE-DT                   PIC X(10).
001200     05  DIAR-DIARY-TYPE-CD            PIC X(4).
001300     05  DIAR-OWNER-USER               PIC X(8).
001400     05  DIAR-DONE-FLAG                PIC X(1).
001500     05  DIAR-BATCH-RUN-ID             PIC S9(9) COMP.
001600     05  DIAR-CREATED-TS               PIC X(26).
001700     05  DIAR-VERSION-NO               PIC S9(4) COMP.
001800     05  DIAR-LAST-UPD-TS              PIC X(26).
001900     05  DIAR-LAST-UPD-PGM             PIC X(8).
002000     05  DIAR-LAST-UPD-USER            PIC X(8).

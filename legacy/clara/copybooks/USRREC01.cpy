000100* ================================================================
000200* COPYBOOK   : USRREC01
000300* DB2 TABLE  : CLR.T_USER
000400* CONTENT    : CLARA USERS AND AUTHORITY LEVELS
000500* LAYOUT     : ONE FIELD PER COLUMN, IN TABLE ORDER
000600* ================================================================
000700 01  USRREC01-REC.
000800     05  USRR-USER-ID                  PIC X(8).
000900     05  USRR-USER-NAME                PIC X(60).
001000     05  USRR-TEAM-CD                  PIC X(4).
001100     05  USRR-RSV-AUTH-LEVEL           PIC X(2).
001200     05  USRR-PAY-AUTH-LEVEL           PIC X(2).
001300     05  USRR-ACTIVE-FLAG              PIC X(1).
001400     05  USRR-LAST-UPD-TS              PIC X(26).
001500     05  USRR-LAST-UPD-PGM             PIC X(8).
001600     05  USRR-LAST-UPD-USER            PIC X(8).

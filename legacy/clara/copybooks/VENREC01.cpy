000100* ===============================================================*
000200* COPYBOOK   : VENREC01                                          *
000300* DB2 TABLE  : CLR.T_VENDOR                                      *
000400* CONTENT    : VENDORS (ASSESSORS, REPAIRERS, SOLICITORS,        *
000500*              SALVAGE)                                          *
000600* LAYOUT     : ONE FIELD PER COLUMN, IN TABLE ORDER              *
000700* ===============================================================*
000800 01  VENREC01-REC.
000900     05  VENR-VENDOR-CD                PIC X(8).
001000     05  VENR-VENDOR-NAME              PIC X(80).
001100     05  VENR-VENDOR-TYPE-CD           PIC X(2).
001200     05  VENR-PANEL-FROM-DT            PIC X(10).
001300     05  VENR-PANEL-TO-DT              PIC X(10).
001400     05  VENR-ARCHIVE-FLAG             PIC X(1).
001500     05  VENR-EXT-REF                  PIC X(20).
001600     05  VENR-LAST-UPD-TS              PIC X(26).
001700     05  VENR-LAST-UPD-PGM             PIC X(8).
001800     05  VENR-LAST-UPD-USER            PIC X(8).

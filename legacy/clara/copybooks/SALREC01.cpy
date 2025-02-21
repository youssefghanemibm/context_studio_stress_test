000100* ===============================================================*
000200* COPYBOOK   : SALREC01                                          *
000300* DB2 TABLE  : CLR.T_SALVAGE                                     *
000400* CONTENT    : SALVAGE DISPOSALS                                 *
000500* LAYOUT     : ONE FIELD PER COLUMN, IN TABLE ORDER              *
000600* ===============================================================*
000700 01  SALREC01-REC.
000800     05  SALR-SALV-ID                  PIC S9(18) COMP.
000900     05  SALR-CLAIM-ID                 PIC X(12).
001000     05  SALR-SALV-CATEGORY            PIC X(1).
001100     05  SALR-DISPOSAL-DT              PIC X(10).
001200     05  SALR-PROCEEDS-AMT             PIC S9(9)V99 COMP-3.
001300     05  SALR-VENDOR-CD                PIC X(8).
001400     05  SALR-CREATED-TS               PIC X(26).
001500     05  SALR-LAST-UPD-TS              PIC X(26).
001600     05  SALR-LAST-UPD-PGM             PIC X(8).
001700     05  SALR-LAST-UPD-USER            PIC X(8).

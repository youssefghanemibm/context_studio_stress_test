000100* ===============================================================*
000200* COPYBOOK   : IFLOG01                                           *
000300* DB2 TABLE  : CLR.T_INTERFACE_LOG                               *
000400* CONTENT    : INTERFACE RUN LOG                                 *
000500* LAYOUT     : ONE FIELD PER COLUMN, IN TABLE ORDER              *
000600* ===============================================================*
000700 01  IFLOG01-REC.
000800     05  IFLO-IF-RUN-ID                PIC S9(9) COMP.
000900     05  IFLO-INTERFACE-ID             PIC X(10).
001000     05  IFLO-RUN-TS                   PIC X(26).
001100     05  IFLO-RECORD-COUNT             PIC S9(9) COMP.
001200     05  IFLO-HASH-TOTAL               PIC S9(15)V99 COMP-3.
001300     05  IFLO-RUN-STATUS               PIC X(2).
001400     05  IFLO-BATCH-RUN-ID             PIC S9(9) COMP.
001500     05  IFLO-BRANCH-CD                PIC X(3).
001600     05  IFLO-COMMENT-TXT              PIC X(254).
001700     05  IFLO-LAST-UPD-TS              PIC X(26).
001800     05  IFLO-LAST-UPD-PGM             PIC X(8).
001900     05  IFLO-LAST-UPD-USER            PIC X(8).

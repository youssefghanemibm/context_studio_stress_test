000100* ===============================================================*
000200* COPYBOOK   : RSVMVT01                                          *
000300* DB2 TABLE  : CLR.T_RESERVE_MOVEMENT                            *
000400* CONTENT    : AUDIT TRAIL OF RESERVE CHANGES; SOURCE OF         *
000500*              CLX-IF-042                                        *
000600* LAYOUT     : ONE FIELD PER COLUMN, IN TABLE ORDER              *
000700* ===============================================================*
000800 01  RSVMVT01-REC.
000900     05  RSVM-MOVE-ID                  PIC S9(18) COMP.
001000     05  RSVM-RSV-ID                   PIC S9(18) COMP.
001100     05  RSVM-CLAIM-ID                 PIC X(12).
001200     05  RSVM-MOVE-TS                  PIC X(26).
001300     05  RSVM-MOVE-TYPE-CD             PIC X(2).
001400     05  RSVM-MOVE-AMT                 PIC S9(11)V99 COMP-3.
001500     05  RSVM-MOVE-GBP-AMT             PIC S9(11)V99 COMP-3.
001600     05  RSVM-REASON-CD                PIC X(4).
001700     05  RSVM-USER-ID                  PIC X(8).
001800     05  RSVM-PGM-ID                   PIC X(8).
001900     05  RSVM-EXTRACTED-FLAG           PIC X(1).
002000     05  RSVM-EXTRACT-RUN-ID           PIC S9(9) COMP.

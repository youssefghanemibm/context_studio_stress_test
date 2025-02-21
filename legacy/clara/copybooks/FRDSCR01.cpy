000100* ================================================================
000200* COPYBOOK   : FRDSCR01
000300* DB2 TABLE  : CLR.T_FRAUD_SCORE
000400* CONTENT    : SENTINEL SCORES
000500* LAYOUT     : ONE FIELD PER COLUMN, IN TABLE ORDER
000600* ================================================================
000700 01  FRDSCR01-REC.
000800     05  FRDS-CLAIM-ID                 PIC X(12).
000900     05  FRDS-SCORE-TS                 PIC X(26).
001000     05  FRDS-SCORE                    PIC S9(4) COMP.
001100     05  FRDS-MODEL-VERSION            PIC X(8).
001200     05  FRDS-TOP-REASON-1             PIC X(6).
001300     05  FRDS-TOP-REASON-2             PIC X(6).
001400     05  FRDS-SOURCE-SYS-CD            PIC X(4).
001500     05  FRDS-LAST-UPD-TS              PIC X(26).
001600     05  FRDS-LAST-UPD-PGM             PIC X(8).
001700     05  FRDS-LAST-UPD-USER            PIC X(8).

000100* ================================================================
000200* COPYBOOK   : CLRTIR01
000300* DB2 TABLE  : CLR.T_CLAIM_TIER
000400* CONTENT    : TIER HISTORY
000500* LAYOUT     : ONE FIELD PER COLUMN, IN TABLE ORDER
000600* ================================================================
000700 01  CLRTIR01-REC.
000800     05  TIR-CLAIM-ID                  PIC X(12).
000900     05  TIR-TIER-FROM-TS              PIC X(26).
001000     05  TIR-TIER-CD                   PIC X(1).
001100     05  TIR-TIER-REASON-CD            PIC X(4).
001200     05  TIR-OVERRIDE-FLAG             PIC X(1).
001300     05  TIR-OVERRIDE-USER             PIC X(8).
001400     05  TIR-CREATED-TS                PIC X(26).
001500     05  TIR-LAST-UPD-TS               PIC X(26).
001600     05  TIR-LAST-UPD-PGM              PIC X(8).
001700     05  TIR-LAST-UPD-USER             PIC X(8).

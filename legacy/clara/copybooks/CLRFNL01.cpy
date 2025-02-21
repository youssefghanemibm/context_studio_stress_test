000100* ================================================================
000200* COPYBOOK   : CLRFNL01
000300* DB2 TABLE  : CLR.T_FNOL_EVENT
000400* CONTENT    : RAW FNOL EVENTS BY CHANNEL
000500* LAYOUT     : ONE FIELD PER COLUMN, IN TABLE ORDER
000600* ================================================================
000700 01  CLRFNL01-REC.
000800     05  FNL-FNOL-ID                   PIC S9(18) COMP.
000900     05  FNL-CLAIM-ID                  PIC X(12).
001000     05  FNL-CHANNEL-CD                PIC X(2).
001100     05  FNL-RECEIVED-TS               PIC X(26).
001200     05  FNL-PAYLOAD-REF               PIC X(36).
001300     05  FNL-CALLER-PHONE              PIC X(16).
001400     05  FNL-ACK-SENT-TS               PIC X(26).
001500     05  FNL-LAST-UPD-TS               PIC X(26).
001600     05  FNL-LAST-UPD-PGM              PIC X(8).
001700     05  FNL-LAST-UPD-USER             PIC X(8).

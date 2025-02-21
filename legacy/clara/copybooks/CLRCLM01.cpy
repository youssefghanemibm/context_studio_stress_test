000100* ================================================================
000200* COPYBOOK   : CLRCLM01
000300* DB2 TABLE  : CLR.T_CLAIM
000400* CONTENT    : CLAIM HEADER - ONE ROW PER CLAIM
000500* LAYOUT     : ONE FIELD PER COLUMN, IN TABLE ORDER
000600* ================================================================
000700 01  CLRCLM01-REC.
000800     05  CLM-CLAIM-ID                  PIC X(12).
000900     05  CLM-POLICY-NO                 PIC X(10).
001000     05  CLM-PRODUCT-CD                PIC X(6).
001100     05  CLM-PERIL-CD                  PIC X(4).
001200     05  CLM-LOSS-DT                   PIC X(10).
001300     05  CLM-NOTIFIED-TS               PIC X(26).
001400     05  CLM-CHANNEL-CD                PIC X(2).
001500     05  CLM-CLAIM-STATUS              PIC X(2).
001600     05  CLM-TIER-CD                   PIC X(1).
001700     05  CLM-REGION-CD                 PIC X(2).
001800     05  CLM-CURRENCY-CD               PIC X(3).
001900     05  CLM-CLAIMANT-ID               PIC X(10).
002000     05  CLM-HANDLER-USER-ID           PIC X(8).
002100     05  CLM-ASSESSOR-ID               PIC X(8).
002200     05  CLM-FRAUD-FLAG                PIC X(1).
002300     05  CLM-RECOVERY-FLAG             PIC X(1).
002400     05  CLM-LOSS-DESC                 PIC X(500).
002500     05  CLM-LOSS-POSTCODE             PIC X(8).
002600     05  CLM-CLOSED-DT                 PIC X(10).
002700     05  CLM-LAST-UPD-TS               PIC X(26).
002800     05  CLM-LAST-UPD-PGM              PIC X(8).
002900     05  CLM-LAST-UPD-USER             PIC X(8).

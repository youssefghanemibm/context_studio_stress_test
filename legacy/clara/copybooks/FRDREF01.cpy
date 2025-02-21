000100* ================================================================
000200* COPYBOOK   : FRDREF01
000300* DB2 TABLE  : CLR.T_FRAUD_REFERRAL
000400* CONTENT    : FRAUD REFERRALS TO SIU
000500* LAYOUT     : ONE FIELD PER COLUMN, IN TABLE ORDER
000600* ================================================================
000700 01  FRDREF01-REC.
000800     05  FRDR-REF-ID                   PIC S9(18) COMP.
000900     05  FRDR-CLAIM-ID                 PIC X(12).
001000     05  FRDR-REF-TS                   PIC X(26).
001100     05  FRDR-REF-SCORE                PIC S9(4) COMP.
001200     05  FRDR-REF-THRESHOLD-APPLIED    PIC S9(4) COMP.
001300     05  FRDR-REF-SOURCE-CD            PIC X(2).
001400     05  FRDR-REF-REASON-CD            PIC X(4).
001500     05  FRDR-RULE-ID                  PIC X(10).
001600     05  FRDR-TIER-CD                  PIC X(1).
001700     05  FRDR-SIU-CASE-ID              PIC X(10).
001800     05  FRDR-REF-STATUS               PIC X(2).
001900     05  FRDR-CUSTOMER-NOTICE-DUE-DT   PIC X(10).
002000     05  FRDR-CUSTOMER-NOTICE-DEFER-FLAG PIC X(1).
002100     05  FRDR-DEFER-APPROVED-BY        PIC X(8).
002200     05  FRDR-OUTCOME-CD               PIC X(2).
002300     05  FRDR-OUTCOME-DT               PIC X(10).
002400     05  FRDR-LAST-UPD-TS              PIC X(26).
002500     05  FRDR-LAST-UPD-PGM             PIC X(8).
002600     05  FRDR-LAST-UPD-USER            PIC X(8).

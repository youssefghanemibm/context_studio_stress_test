-- --------------------------------------------------------------------
-- CLR.T_CLAIM_TIER
-- Tier history
-- Area: TRIAGE    Copybook: CLRTIR01
-- --------------------------------------------------------------------
CREATE TABLE CLR.T_CLAIM_TIER
  ( CLAIM_ID                    CHAR(12)      NOT NULL
  , TIER_FROM_TS                TIMESTAMP     NOT NULL
  , TIER_CD                     CHAR(1)       NOT NULL
  , TIER_REASON_CD              CHAR(4)       NOT NULL
  , OVERRIDE_FLAG               CHAR(1)       NOT NULL
  , OVERRIDE_USER               CHAR(8)
  , CREATED_TS                  TIMESTAMP     NOT NULL
  , LAST_UPD_TS                 TIMESTAMP     NOT NULL WITH DEFAULT
  , LAST_UPD_PGM                CHAR(8)       NOT NULL
  , LAST_UPD_USER               CHAR(8)       NOT NULL
  , CONSTRAINT PK_T_CLAIM_TIER PRIMARY KEY (CLAIM_ID, TIER_FROM_TS)
  )
  CCSID EBCDIC;

CREATE UNIQUE INDEX CLR.XCLAIM_TIER_PK
    ON CLR.T_CLAIM_TIER (CLAIM_ID, TIER_FROM_TS);
CREATE INDEX CLR.XCLAIM_TIER_CLM
    ON CLR.T_CLAIM_TIER (CLAIM_ID);

COMMENT ON TABLE CLR.T_CLAIM_TIER IS
  'Tier history';
COMMENT ON COLUMN CLR.T_CLAIM_TIER.CLAIM_ID IS
  'Claim reference';
COMMENT ON COLUMN CLR.T_CLAIM_TIER.TIER_FROM_TS IS
  'Tier effective from';
COMMENT ON COLUMN CLR.T_CLAIM_TIER.TIER_CD IS
  'Tier';
COMMENT ON COLUMN CLR.T_CLAIM_TIER.TIER_REASON_CD IS
  'Reason (AMT amount, INJ injury, LIT litigation, TLS total loss)';
COMMENT ON COLUMN CLR.T_CLAIM_TIER.OVERRIDE_FLAG IS
  'Manual override';
COMMENT ON COLUMN CLR.T_CLAIM_TIER.OVERRIDE_USER IS
  'Override user';
COMMENT ON COLUMN CLR.T_CLAIM_TIER.CREATED_TS IS
  'Row creation timestamp';
COMMENT ON COLUMN CLR.T_CLAIM_TIER.LAST_UPD_TS IS
  'Timestamp of last update';
COMMENT ON COLUMN CLR.T_CLAIM_TIER.LAST_UPD_PGM IS
  'Program that last updated the row';
COMMENT ON COLUMN CLR.T_CLAIM_TIER.LAST_UPD_USER IS
  'User or batch id that last updated the row';

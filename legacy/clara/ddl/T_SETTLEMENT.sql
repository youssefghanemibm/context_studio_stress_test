-- --------------------------------------------------------------------
-- CLR.T_SETTLEMENT
-- Settlements
-- Area: SETTLE    Copybook: STLREC01
-- --------------------------------------------------------------------
CREATE TABLE CLR.T_SETTLEMENT
  ( SETTLE_ID                   BIGINT        NOT NULL GENERATED ALWAYS AS IDENTITY
  , CLAIM_ID                    CHAR(12)      NOT NULL
  , OFFER_AMT                   DECIMAL(13,2) NOT NULL
  , OFFER_DT                    DATE          NOT NULL
  , ACCEPTED_DT                 DATE
  , FINAL_FLAG                  CHAR(1)       NOT NULL
  , EXCESS_APPLIED_AMT          DECIMAL(11,2) NOT NULL
  , ARCHIVE_FLAG                CHAR(1)       NOT NULL
  , CREATED_TS                  TIMESTAMP     NOT NULL
  , EXT_REF                     CHAR(20)
  , LAST_UPD_TS                 TIMESTAMP     NOT NULL WITH DEFAULT
  , LAST_UPD_PGM                CHAR(8)       NOT NULL
  , LAST_UPD_USER               CHAR(8)       NOT NULL
  , CONSTRAINT PK_T_SETTLEMENT PRIMARY KEY (SETTLE_ID)
  )
  CCSID EBCDIC;

CREATE UNIQUE INDEX CLR.XSETTLEMENT_PK
    ON CLR.T_SETTLEMENT (SETTLE_ID);
CREATE INDEX CLR.XSETTLEMENT_CLM
    ON CLR.T_SETTLEMENT (CLAIM_ID);

COMMENT ON TABLE CLR.T_SETTLEMENT IS
  'Settlements';
COMMENT ON COLUMN CLR.T_SETTLEMENT.SETTLE_ID IS
  'Settlement id';
COMMENT ON COLUMN CLR.T_SETTLEMENT.CLAIM_ID IS
  'Claim reference';
COMMENT ON COLUMN CLR.T_SETTLEMENT.OFFER_AMT IS
  'Offer';
COMMENT ON COLUMN CLR.T_SETTLEMENT.OFFER_DT IS
  'Offer date';
COMMENT ON COLUMN CLR.T_SETTLEMENT.ACCEPTED_DT IS
  'Accepted';
COMMENT ON COLUMN CLR.T_SETTLEMENT.FINAL_FLAG IS
  'Final settlement';
COMMENT ON COLUMN CLR.T_SETTLEMENT.EXCESS_APPLIED_AMT IS
  'Excess deducted';
COMMENT ON COLUMN CLR.T_SETTLEMENT.ARCHIVE_FLAG IS
  'Y when eligible for archive (7-year retention)';
COMMENT ON COLUMN CLR.T_SETTLEMENT.CREATED_TS IS
  'Row creation timestamp';
COMMENT ON COLUMN CLR.T_SETTLEMENT.EXT_REF IS
  'External reference';
COMMENT ON COLUMN CLR.T_SETTLEMENT.LAST_UPD_TS IS
  'Timestamp of last update';
COMMENT ON COLUMN CLR.T_SETTLEMENT.LAST_UPD_PGM IS
  'Program that last updated the row';
COMMENT ON COLUMN CLR.T_SETTLEMENT.LAST_UPD_USER IS
  'User or batch id that last updated the row';

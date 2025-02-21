-- --------------------------------------------------------------------
-- CLR.T_ESTIMATE
-- Repair and replacement estimates
-- Area: ASSESS    Copybook: CLREST01
-- --------------------------------------------------------------------
CREATE TABLE CLR.T_ESTIMATE
  ( EST_ID                      BIGINT        NOT NULL GENERATED ALWAYS AS IDENTITY
  , CLAIM_ID                    CHAR(12)      NOT NULL
  , EST_LINE_NO                 SMALLINT      NOT NULL
  , EST_ITEM_DESC               VARCHAR(120)  NOT NULL
  , EST_AMT                     DECIMAL(11,2) NOT NULL
  , REPAIRER_CD                 CHAR(8)
  , EXT_REF                     CHAR(20)
  , LAST_UPD_TS                 TIMESTAMP     NOT NULL WITH DEFAULT
  , LAST_UPD_PGM                CHAR(8)       NOT NULL
  , LAST_UPD_USER               CHAR(8)       NOT NULL
  , CONSTRAINT PK_T_ESTIMATE PRIMARY KEY (EST_ID)
  )
  CCSID EBCDIC;

CREATE UNIQUE INDEX CLR.XESTIMATE_PK
    ON CLR.T_ESTIMATE (EST_ID);
CREATE INDEX CLR.XESTIMATE_CLM
    ON CLR.T_ESTIMATE (CLAIM_ID);

COMMENT ON TABLE CLR.T_ESTIMATE IS
  'Repair and replacement estimates';
COMMENT ON COLUMN CLR.T_ESTIMATE.EST_ID IS
  'Estimate id';
COMMENT ON COLUMN CLR.T_ESTIMATE.CLAIM_ID IS
  'Claim reference';
COMMENT ON COLUMN CLR.T_ESTIMATE.EST_LINE_NO IS
  'Line';
COMMENT ON COLUMN CLR.T_ESTIMATE.EST_ITEM_DESC IS
  'Item';
COMMENT ON COLUMN CLR.T_ESTIMATE.EST_AMT IS
  'Amount';
COMMENT ON COLUMN CLR.T_ESTIMATE.REPAIRER_CD IS
  'Repair network code';
COMMENT ON COLUMN CLR.T_ESTIMATE.EXT_REF IS
  'External reference';
COMMENT ON COLUMN CLR.T_ESTIMATE.LAST_UPD_TS IS
  'Timestamp of last update';
COMMENT ON COLUMN CLR.T_ESTIMATE.LAST_UPD_PGM IS
  'Program that last updated the row';
COMMENT ON COLUMN CLR.T_ESTIMATE.LAST_UPD_USER IS
  'User or batch id that last updated the row';

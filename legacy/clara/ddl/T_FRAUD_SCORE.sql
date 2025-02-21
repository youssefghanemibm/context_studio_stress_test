-- --------------------------------------------------------------------
-- CLR.T_FRAUD_SCORE
-- Sentinel scores
-- Area: FRAUD    Copybook: FRDSCR01
-- --------------------------------------------------------------------
CREATE TABLE CLR.T_FRAUD_SCORE
  ( CLAIM_ID                    CHAR(12)      NOT NULL
  , SCORE_TS                    TIMESTAMP     NOT NULL
  , SCORE                       SMALLINT      NOT NULL
  , MODEL_VERSION               CHAR(8)       NOT NULL
  , TOP_REASON_1                CHAR(6)       NOT NULL
  , TOP_REASON_2                CHAR(6)
  , SOURCE_SYS_CD               CHAR(4)
  , LAST_UPD_TS                 TIMESTAMP     NOT NULL WITH DEFAULT
  , LAST_UPD_PGM                CHAR(8)       NOT NULL
  , LAST_UPD_USER               CHAR(8)       NOT NULL
  , CONSTRAINT PK_T_FRAUD_SCORE PRIMARY KEY (CLAIM_ID, SCORE_TS)
  )
  CCSID EBCDIC;

CREATE UNIQUE INDEX CLR.XFRAUD_SCORE_PK
    ON CLR.T_FRAUD_SCORE (CLAIM_ID, SCORE_TS);
CREATE INDEX CLR.XFRAUD_SCORE_CLM
    ON CLR.T_FRAUD_SCORE (CLAIM_ID);

COMMENT ON TABLE CLR.T_FRAUD_SCORE IS
  'Sentinel scores';
COMMENT ON COLUMN CLR.T_FRAUD_SCORE.CLAIM_ID IS
  'Claim reference';
COMMENT ON COLUMN CLR.T_FRAUD_SCORE.SCORE_TS IS
  'Scored at';
COMMENT ON COLUMN CLR.T_FRAUD_SCORE.SCORE IS
  'Score 0-100';
COMMENT ON COLUMN CLR.T_FRAUD_SCORE.MODEL_VERSION IS
  'Model version (e.g. SNT-4.2)';
COMMENT ON COLUMN CLR.T_FRAUD_SCORE.TOP_REASON_1 IS
  'Top reason code';
COMMENT ON COLUMN CLR.T_FRAUD_SCORE.TOP_REASON_2 IS
  'Second reason';
COMMENT ON COLUMN CLR.T_FRAUD_SCORE.SOURCE_SYS_CD IS
  'Originating system code';
COMMENT ON COLUMN CLR.T_FRAUD_SCORE.LAST_UPD_TS IS
  'Timestamp of last update';
COMMENT ON COLUMN CLR.T_FRAUD_SCORE.LAST_UPD_PGM IS
  'Program that last updated the row';
COMMENT ON COLUMN CLR.T_FRAUD_SCORE.LAST_UPD_USER IS
  'User or batch id that last updated the row';

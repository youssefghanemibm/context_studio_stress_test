-- --------------------------------------------------------------------
-- CLR.T_RESERVE
-- Case reserves - one row per claim per reserve type
-- Area: RESERVE    Copybook: RSVREC
-- --------------------------------------------------------------------
CREATE TABLE CLR.T_RESERVE
  ( RSV_ID                      BIGINT        NOT NULL GENERATED ALWAYS AS IDENTITY
  , CLAIM_ID                    CHAR(12)      NOT NULL
  , RSV_TYPE_CD                 CHAR(2)       NOT NULL
  , CURRENCY_CD                 CHAR(3)       NOT NULL
  , RSV_INITIAL_AMT             DECIMAL(13,2) NOT NULL
  , RSV_OUTSTANDING_AMT         DECIMAL(13,2) NOT NULL
  , RSV_PAID_TO_DATE_AMT        DECIMAL(13,2) NOT NULL
  , RSV_RECOVERY_EST_AMT        DECIMAL(13,2)
  , RSV_GBP_EQUIV_AMT           DECIMAL(13,2) NOT NULL
  , RSV_STATUS                  CHAR(1)       NOT NULL
  , RSV_AUTH_LEVEL              CHAR(2)       NOT NULL
  , RSV_SET_BY_USER             CHAR(8)       NOT NULL
  , RSV_NEXT_REVIEW_DT          DATE
  , RSV_INDEX_FACTOR            DECIMAL(7,5)
  , RSV_LAST_REVAL_DT           DATE
  , LAST_UPD_TS                 TIMESTAMP     NOT NULL WITH DEFAULT
  , LAST_UPD_PGM                CHAR(8)       NOT NULL
  , LAST_UPD_USER               CHAR(8)       NOT NULL
  , CONSTRAINT PK_T_RESERVE PRIMARY KEY (RSV_ID)
  )
  CCSID EBCDIC;

CREATE UNIQUE INDEX CLR.XRESERVE_PK
    ON CLR.T_RESERVE (RSV_ID);
CREATE INDEX CLR.XRESERVE_CLM
    ON CLR.T_RESERVE (CLAIM_ID);

ALTER TABLE CLR.T_RESERVE
  ADD CONSTRAINT FK_RESERVE_1 FOREIGN KEY (CLAIM_ID)
      REFERENCES CLR.T_CLAIM (CLAIM_ID) ON DELETE RESTRICT;

COMMENT ON TABLE CLR.T_RESERVE IS
  'Case reserves - one row per claim per reserve type';
COMMENT ON COLUMN CLR.T_RESERVE.RSV_ID IS
  'Reserve identifier';
COMMENT ON COLUMN CLR.T_RESERVE.CLAIM_ID IS
  'Claim reference (FK CLR.T_CLAIM)';
COMMENT ON COLUMN CLR.T_RESERVE.RSV_TYPE_CD IS
  'Reserve type (ID indemnity, EX expense, LG legal)';
COMMENT ON COLUMN CLR.T_RESERVE.CURRENCY_CD IS
  'Reserve currency (local currency for Nordic claims)';
COMMENT ON COLUMN CLR.T_RESERVE.RSV_INITIAL_AMT IS
  'Initial reserve amount';
COMMENT ON COLUMN CLR.T_RESERVE.RSV_OUTSTANDING_AMT IS
  'Current outstanding case reserve';
COMMENT ON COLUMN CLR.T_RESERVE.RSV_PAID_TO_DATE_AMT IS
  'Paid to date against this reserve';
COMMENT ON COLUMN CLR.T_RESERVE.RSV_RECOVERY_EST_AMT IS
  'Estimated recoveries netted from the reserve';
COMMENT ON COLUMN CLR.T_RESERVE.RSV_GBP_EQUIV_AMT IS
  'GBP equivalent of the outstanding reserve';
COMMENT ON COLUMN CLR.T_RESERVE.RSV_STATUS IS
  'O open, C closed';
COMMENT ON COLUMN CLR.T_RESERVE.RSV_AUTH_LEVEL IS
  'Authority level that approved the last change (CH, TL, CM, CD, RC)';
COMMENT ON COLUMN CLR.T_RESERVE.RSV_SET_BY_USER IS
  'User who last set the reserve';
COMMENT ON COLUMN CLR.T_RESERVE.RSV_NEXT_REVIEW_DT IS
  'Next scheduled reserve review (Tier-3 cadence BR-RSV-007)';
COMMENT ON COLUMN CLR.T_RESERVE.RSV_INDEX_FACTOR IS
  'Cumulative indexation factor (BI claims, BR-RSV-009)';
COMMENT ON COLUMN CLR.T_RESERVE.RSV_LAST_REVAL_DT IS
  'Date of last currency revaluation';
COMMENT ON COLUMN CLR.T_RESERVE.LAST_UPD_TS IS
  'Timestamp of last update';
COMMENT ON COLUMN CLR.T_RESERVE.LAST_UPD_PGM IS
  'Program that last updated the row';
COMMENT ON COLUMN CLR.T_RESERVE.LAST_UPD_USER IS
  'User or batch id that last updated the row';

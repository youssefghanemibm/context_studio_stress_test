-- --------------------------------------------------------------------
-- CLR.T_CURRENCY_RATE
-- Currency rates loaded from Group Ledger (CLX-IF-027)
-- Area: GL    Copybook: CURRATE1
-- --------------------------------------------------------------------
CREATE TABLE CLR.T_CURRENCY_RATE
  ( CURRENCY_CD                 CHAR(3)       NOT NULL
  , RATE_DT                     DATE          NOT NULL
  , RATE_TO_GBP                 DECIMAL(11,7) NOT NULL
  , RATE_TYPE_CD                CHAR(2)       NOT NULL
  , ARCHIVE_FLAG                CHAR(1)       NOT NULL
  , COMMENT_TXT                 VARCHAR(254)
  , CREATED_TS                  TIMESTAMP     NOT NULL
  , LAST_UPD_TS                 TIMESTAMP     NOT NULL WITH DEFAULT
  , LAST_UPD_PGM                CHAR(8)       NOT NULL
  , LAST_UPD_USER               CHAR(8)       NOT NULL
  , CONSTRAINT PK_T_CURRENCY_RATE PRIMARY KEY (CURRENCY_CD, RATE_DT)
  )
  CCSID EBCDIC;

CREATE UNIQUE INDEX CLR.XCURRENCY_RATE_PK
    ON CLR.T_CURRENCY_RATE (CURRENCY_CD, RATE_DT);

COMMENT ON TABLE CLR.T_CURRENCY_RATE IS
  'Currency rates loaded from Group Ledger (CLX-IF-027)';
COMMENT ON COLUMN CLR.T_CURRENCY_RATE.CURRENCY_CD IS
  'Currency';
COMMENT ON COLUMN CLR.T_CURRENCY_RATE.RATE_DT IS
  'Rate date';
COMMENT ON COLUMN CLR.T_CURRENCY_RATE.RATE_TO_GBP IS
  'GBP per unit';
COMMENT ON COLUMN CLR.T_CURRENCY_RATE.RATE_TYPE_CD IS
  'DY daily, ME month-end, YE year-end';
COMMENT ON COLUMN CLR.T_CURRENCY_RATE.ARCHIVE_FLAG IS
  'Y when eligible for archive (7-year retention)';
COMMENT ON COLUMN CLR.T_CURRENCY_RATE.COMMENT_TXT IS
  'Free-text comment';
COMMENT ON COLUMN CLR.T_CURRENCY_RATE.CREATED_TS IS
  'Row creation timestamp';
COMMENT ON COLUMN CLR.T_CURRENCY_RATE.LAST_UPD_TS IS
  'Timestamp of last update';
COMMENT ON COLUMN CLR.T_CURRENCY_RATE.LAST_UPD_PGM IS
  'Program that last updated the row';
COMMENT ON COLUMN CLR.T_CURRENCY_RATE.LAST_UPD_USER IS
  'User or batch id that last updated the row';

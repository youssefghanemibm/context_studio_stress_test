-- --------------------------------------------------------------------
-- CLR.T_NISA_RETURN
-- NISA return staging
-- Area: REPORT    Copybook: NISARET1
-- --------------------------------------------------------------------
CREATE TABLE CLR.T_NISA_RETURN
  ( RETURN_CD                   CHAR(6)       NOT NULL
  , PERIOD_CD                   CHAR(6)       NOT NULL
  , CELL_REF                    CHAR(10)      NOT NULL
  , CELL_VALUE                  DECIMAL(17,2) NOT NULL
  , SUBMITTED_DT                DATE
  , ARCHIVE_FLAG                CHAR(1)       NOT NULL
  , COMMENT_TXT                 VARCHAR(254)
  , LAST_UPD_TS                 TIMESTAMP     NOT NULL WITH DEFAULT
  , LAST_UPD_PGM                CHAR(8)       NOT NULL
  , LAST_UPD_USER               CHAR(8)       NOT NULL
  , CONSTRAINT PK_T_NISA_RETURN PRIMARY KEY (RETURN_CD, PERIOD_CD)
  )
  CCSID EBCDIC;

CREATE UNIQUE INDEX CLR.XNISA_RETURN_PK
    ON CLR.T_NISA_RETURN (RETURN_CD, PERIOD_CD);

COMMENT ON TABLE CLR.T_NISA_RETURN IS
  'NISA return staging';
COMMENT ON COLUMN CLR.T_NISA_RETURN.RETURN_CD IS
  'Return (TP2, FR1, CT1)';
COMMENT ON COLUMN CLR.T_NISA_RETURN.PERIOD_CD IS
  'Period (e.g. 2026Q3)';
COMMENT ON COLUMN CLR.T_NISA_RETURN.CELL_REF IS
  'Return cell';
COMMENT ON COLUMN CLR.T_NISA_RETURN.CELL_VALUE IS
  'Value';
COMMENT ON COLUMN CLR.T_NISA_RETURN.SUBMITTED_DT IS
  'Submitted';
COMMENT ON COLUMN CLR.T_NISA_RETURN.ARCHIVE_FLAG IS
  'Y when eligible for archive (7-year retention)';
COMMENT ON COLUMN CLR.T_NISA_RETURN.COMMENT_TXT IS
  'Free-text comment';
COMMENT ON COLUMN CLR.T_NISA_RETURN.LAST_UPD_TS IS
  'Timestamp of last update';
COMMENT ON COLUMN CLR.T_NISA_RETURN.LAST_UPD_PGM IS
  'Program that last updated the row';
COMMENT ON COLUMN CLR.T_NISA_RETURN.LAST_UPD_USER IS
  'User or batch id that last updated the row';

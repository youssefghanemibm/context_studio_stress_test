-- --------------------------------------------------------------------
-- CLR.T_INTERFACE_LOG
-- Interface run log
-- Area: COMMON    Copybook: IFLOG01
-- --------------------------------------------------------------------
CREATE TABLE CLR.T_INTERFACE_LOG
  ( IF_RUN_ID                   INTEGER       NOT NULL
  , INTERFACE_ID                CHAR(10)      NOT NULL
  , RUN_TS                      TIMESTAMP     NOT NULL
  , RECORD_COUNT                INTEGER       NOT NULL
  , HASH_TOTAL                  DECIMAL(17,2) NOT NULL
  , RUN_STATUS                  CHAR(2)       NOT NULL
  , BATCH_RUN_ID                INTEGER
  , BRANCH_CD                   CHAR(3)
  , COMMENT_TXT                 VARCHAR(254)
  , LAST_UPD_TS                 TIMESTAMP     NOT NULL WITH DEFAULT
  , LAST_UPD_PGM                CHAR(8)       NOT NULL
  , LAST_UPD_USER               CHAR(8)       NOT NULL
  , CONSTRAINT PK_T_INTERFACE_LOG PRIMARY KEY (IF_RUN_ID)
  )
  CCSID EBCDIC;

CREATE UNIQUE INDEX CLR.XINTERFACE_LOG_PK
    ON CLR.T_INTERFACE_LOG (IF_RUN_ID);

COMMENT ON TABLE CLR.T_INTERFACE_LOG IS
  'Interface run log';
COMMENT ON COLUMN CLR.T_INTERFACE_LOG.IF_RUN_ID IS
  'Run id';
COMMENT ON COLUMN CLR.T_INTERFACE_LOG.INTERFACE_ID IS
  'Interface (e.g. CLX-IF-042)';
COMMENT ON COLUMN CLR.T_INTERFACE_LOG.RUN_TS IS
  'Run time';
COMMENT ON COLUMN CLR.T_INTERFACE_LOG.RECORD_COUNT IS
  'Records';
COMMENT ON COLUMN CLR.T_INTERFACE_LOG.HASH_TOTAL IS
  'Hash total';
COMMENT ON COLUMN CLR.T_INTERFACE_LOG.RUN_STATUS IS
  'OK, ER, RR';
COMMENT ON COLUMN CLR.T_INTERFACE_LOG.BATCH_RUN_ID IS
  'Batch run identifier';
COMMENT ON COLUMN CLR.T_INTERFACE_LOG.BRANCH_CD IS
  'Branch code (UK, NO, SE, DK branch)';
COMMENT ON COLUMN CLR.T_INTERFACE_LOG.COMMENT_TXT IS
  'Free-text comment';
COMMENT ON COLUMN CLR.T_INTERFACE_LOG.LAST_UPD_TS IS
  'Timestamp of last update';
COMMENT ON COLUMN CLR.T_INTERFACE_LOG.LAST_UPD_PGM IS
  'Program that last updated the row';
COMMENT ON COLUMN CLR.T_INTERFACE_LOG.LAST_UPD_USER IS
  'User or batch id that last updated the row';

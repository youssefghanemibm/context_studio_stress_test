-- --------------------------------------------------------------------
-- CLR.T_RESERVE_HISTORY
-- Archived reserve snapshots (month-end)
-- Area: RESERVE    Copybook: RSVHIS01
-- --------------------------------------------------------------------
CREATE TABLE CLR.T_RESERVE_HISTORY
  ( RSV_ID                      BIGINT        NOT NULL
  , SNAPSHOT_DT                 DATE          NOT NULL
  , RSV_OUTSTANDING_AMT         DECIMAL(13,2) NOT NULL
  , RSV_GBP_EQUIV_AMT           DECIMAL(13,2) NOT NULL
  , TIER_CD                     CHAR(1)       NOT NULL
  , COMMENT_TXT                 VARCHAR(254)
  , CREATED_TS                  TIMESTAMP     NOT NULL
  , LAST_UPD_TS                 TIMESTAMP     NOT NULL WITH DEFAULT
  , LAST_UPD_PGM                CHAR(8)       NOT NULL
  , LAST_UPD_USER               CHAR(8)       NOT NULL
  , CONSTRAINT PK_T_RESERVE_HISTORY PRIMARY KEY (RSV_ID, SNAPSHOT_DT)
  )
  CCSID EBCDIC;

CREATE UNIQUE INDEX CLR.XRESERVE_HISTOR_PK
    ON CLR.T_RESERVE_HISTORY (RSV_ID, SNAPSHOT_DT);

COMMENT ON TABLE CLR.T_RESERVE_HISTORY IS
  'Archived reserve snapshots (month-end)';
COMMENT ON COLUMN CLR.T_RESERVE_HISTORY.RSV_ID IS
  'Reserve id';
COMMENT ON COLUMN CLR.T_RESERVE_HISTORY.SNAPSHOT_DT IS
  'Snapshot date';
COMMENT ON COLUMN CLR.T_RESERVE_HISTORY.RSV_OUTSTANDING_AMT IS
  'Outstanding';
COMMENT ON COLUMN CLR.T_RESERVE_HISTORY.RSV_GBP_EQUIV_AMT IS
  'GBP equivalent';
COMMENT ON COLUMN CLR.T_RESERVE_HISTORY.TIER_CD IS
  'Tier';
COMMENT ON COLUMN CLR.T_RESERVE_HISTORY.COMMENT_TXT IS
  'Free-text comment';
COMMENT ON COLUMN CLR.T_RESERVE_HISTORY.CREATED_TS IS
  'Row creation timestamp';
COMMENT ON COLUMN CLR.T_RESERVE_HISTORY.LAST_UPD_TS IS
  'Timestamp of last update';
COMMENT ON COLUMN CLR.T_RESERVE_HISTORY.LAST_UPD_PGM IS
  'Program that last updated the row';
COMMENT ON COLUMN CLR.T_RESERVE_HISTORY.LAST_UPD_USER IS
  'User or batch id that last updated the row';

-- --------------------------------------------------------------------
-- CLR.T_DIARY
-- Diary and reminders (reserve reviews, limitation dates)
-- Area: COMMON    Copybook: DIARYRC1
-- --------------------------------------------------------------------
CREATE TABLE CLR.T_DIARY
  ( DIARY_ID                    BIGINT        NOT NULL GENERATED ALWAYS AS IDENTITY
  , CLAIM_ID                    CHAR(12)      NOT NULL
  , DUE_DT                      DATE          NOT NULL
  , DIARY_TYPE_CD               CHAR(4)       NOT NULL
  , OWNER_USER                  CHAR(8)       NOT NULL
  , DONE_FLAG                   CHAR(1)       NOT NULL
  , BATCH_RUN_ID                INTEGER
  , CREATED_TS                  TIMESTAMP     NOT NULL
  , VERSION_NO                  SMALLINT      NOT NULL
  , LAST_UPD_TS                 TIMESTAMP     NOT NULL WITH DEFAULT
  , LAST_UPD_PGM                CHAR(8)       NOT NULL
  , LAST_UPD_USER               CHAR(8)       NOT NULL
  , CONSTRAINT PK_T_DIARY PRIMARY KEY (DIARY_ID)
  )
  CCSID EBCDIC;

CREATE UNIQUE INDEX CLR.XDIARY_PK
    ON CLR.T_DIARY (DIARY_ID);
CREATE INDEX CLR.XDIARY_CLM
    ON CLR.T_DIARY (CLAIM_ID);

COMMENT ON TABLE CLR.T_DIARY IS
  'Diary and reminders (reserve reviews, limitation dates)';
COMMENT ON COLUMN CLR.T_DIARY.DIARY_ID IS
  'Diary id';
COMMENT ON COLUMN CLR.T_DIARY.CLAIM_ID IS
  'Claim reference';
COMMENT ON COLUMN CLR.T_DIARY.DUE_DT IS
  'Due';
COMMENT ON COLUMN CLR.T_DIARY.DIARY_TYPE_CD IS
  'RREV review, LIMT limitation, CHAS chase';
COMMENT ON COLUMN CLR.T_DIARY.OWNER_USER IS
  'Owner';
COMMENT ON COLUMN CLR.T_DIARY.DONE_FLAG IS
  'Done';
COMMENT ON COLUMN CLR.T_DIARY.BATCH_RUN_ID IS
  'Batch run identifier';
COMMENT ON COLUMN CLR.T_DIARY.CREATED_TS IS
  'Row creation timestamp';
COMMENT ON COLUMN CLR.T_DIARY.VERSION_NO IS
  'Optimistic locking version';
COMMENT ON COLUMN CLR.T_DIARY.LAST_UPD_TS IS
  'Timestamp of last update';
COMMENT ON COLUMN CLR.T_DIARY.LAST_UPD_PGM IS
  'Program that last updated the row';
COMMENT ON COLUMN CLR.T_DIARY.LAST_UPD_USER IS
  'User or batch id that last updated the row';

-- --------------------------------------------------------------------
-- CLR.T_GL_POSTING
-- GL postings (payments and recoveries)
-- Area: GL    Copybook: GLPOST01
-- --------------------------------------------------------------------
CREATE TABLE CLR.T_GL_POSTING
  ( POSTING_ID                  BIGINT        NOT NULL GENERATED ALWAYS AS IDENTITY
  , GL_PERIOD                   CHAR(6)       NOT NULL
  , ACCOUNT_CD                  CHAR(10)      NOT NULL
  , DR_CR                       CHAR(1)       NOT NULL
  , AMOUNT_GBP                  DECIMAL(15,2) NOT NULL
  , SOURCE_PGM                  CHAR(8)       NOT NULL
  , CREATED_TS                  TIMESTAMP     NOT NULL
  , EXT_REF                     CHAR(20)
  , VERSION_NO                  SMALLINT      NOT NULL
  , LAST_UPD_TS                 TIMESTAMP     NOT NULL WITH DEFAULT
  , LAST_UPD_PGM                CHAR(8)       NOT NULL
  , LAST_UPD_USER               CHAR(8)       NOT NULL
  , CONSTRAINT PK_T_GL_POSTING PRIMARY KEY (POSTING_ID)
  )
  CCSID EBCDIC;

CREATE UNIQUE INDEX CLR.XGL_POSTING_PK
    ON CLR.T_GL_POSTING (POSTING_ID);

COMMENT ON TABLE CLR.T_GL_POSTING IS
  'GL postings (payments and recoveries)';
COMMENT ON COLUMN CLR.T_GL_POSTING.POSTING_ID IS
  'Posting id';
COMMENT ON COLUMN CLR.T_GL_POSTING.GL_PERIOD IS
  'Period YYYYMM';
COMMENT ON COLUMN CLR.T_GL_POSTING.ACCOUNT_CD IS
  'GL account';
COMMENT ON COLUMN CLR.T_GL_POSTING.DR_CR IS
  'D or C';
COMMENT ON COLUMN CLR.T_GL_POSTING.AMOUNT_GBP IS
  'Amount GBP';
COMMENT ON COLUMN CLR.T_GL_POSTING.SOURCE_PGM IS
  'Source program';
COMMENT ON COLUMN CLR.T_GL_POSTING.CREATED_TS IS
  'Row creation timestamp';
COMMENT ON COLUMN CLR.T_GL_POSTING.EXT_REF IS
  'External reference';
COMMENT ON COLUMN CLR.T_GL_POSTING.VERSION_NO IS
  'Optimistic locking version';
COMMENT ON COLUMN CLR.T_GL_POSTING.LAST_UPD_TS IS
  'Timestamp of last update';
COMMENT ON COLUMN CLR.T_GL_POSTING.LAST_UPD_PGM IS
  'Program that last updated the row';
COMMENT ON COLUMN CLR.T_GL_POSTING.LAST_UPD_USER IS
  'User or batch id that last updated the row';

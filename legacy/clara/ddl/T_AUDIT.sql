-- --------------------------------------------------------------------
-- CLR.T_AUDIT
-- Audit trail
-- Area: COMMON    Copybook: AUDREC01
-- --------------------------------------------------------------------
CREATE TABLE CLR.T_AUDIT
  ( AUDIT_ID                    BIGINT        NOT NULL GENERATED ALWAYS AS IDENTITY
  , AUDIT_TS                    TIMESTAMP     NOT NULL
  , USER_ID                     CHAR(8)       NOT NULL
  , PGM_ID                      CHAR(8)       NOT NULL
  , TABLE_NAME                  CHAR(18)      NOT NULL
  , KEY_VALUE                   CHAR(30)      NOT NULL
  , ACTION_CD                   CHAR(1)       NOT NULL
  , ARCHIVE_FLAG                CHAR(1)       NOT NULL
  , BRANCH_CD                   CHAR(3)
  , EXT_REF                     CHAR(20)
  , LAST_UPD_TS                 TIMESTAMP     NOT NULL WITH DEFAULT
  , LAST_UPD_PGM                CHAR(8)       NOT NULL
  , LAST_UPD_USER               CHAR(8)       NOT NULL
  , CONSTRAINT PK_T_AUDIT PRIMARY KEY (AUDIT_ID)
  )
  CCSID EBCDIC;

CREATE UNIQUE INDEX CLR.XAUDIT_PK
    ON CLR.T_AUDIT (AUDIT_ID);

COMMENT ON TABLE CLR.T_AUDIT IS
  'Audit trail';
COMMENT ON COLUMN CLR.T_AUDIT.AUDIT_ID IS
  'Audit id';
COMMENT ON COLUMN CLR.T_AUDIT.AUDIT_TS IS
  'Time';
COMMENT ON COLUMN CLR.T_AUDIT.USER_ID IS
  'User';
COMMENT ON COLUMN CLR.T_AUDIT.PGM_ID IS
  'Program';
COMMENT ON COLUMN CLR.T_AUDIT.TABLE_NAME IS
  'Table';
COMMENT ON COLUMN CLR.T_AUDIT.KEY_VALUE IS
  'Key';
COMMENT ON COLUMN CLR.T_AUDIT.ACTION_CD IS
  'I, U, D';
COMMENT ON COLUMN CLR.T_AUDIT.ARCHIVE_FLAG IS
  'Y when eligible for archive (7-year retention)';
COMMENT ON COLUMN CLR.T_AUDIT.BRANCH_CD IS
  'Branch code (UK, NO, SE, DK branch)';
COMMENT ON COLUMN CLR.T_AUDIT.EXT_REF IS
  'External reference';
COMMENT ON COLUMN CLR.T_AUDIT.LAST_UPD_TS IS
  'Timestamp of last update';
COMMENT ON COLUMN CLR.T_AUDIT.LAST_UPD_PGM IS
  'Program that last updated the row';
COMMENT ON COLUMN CLR.T_AUDIT.LAST_UPD_USER IS
  'User or batch id that last updated the row';

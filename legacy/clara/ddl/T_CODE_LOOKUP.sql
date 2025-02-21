-- --------------------------------------------------------------------
-- CLR.T_CODE_LOOKUP
-- Code lookup values
-- Area: COMMON    Copybook: CODELKP1
-- --------------------------------------------------------------------
CREATE TABLE CLR.T_CODE_LOOKUP
  ( CODE_TYPE                   CHAR(8)       NOT NULL
  , CODE_VALUE                  CHAR(6)       NOT NULL
  , CODE_DESC_EN                VARCHAR(60)   NOT NULL
  , CODE_DESC_LOCAL             VARCHAR(60)
  , ACTIVE_FLAG                 CHAR(1)       NOT NULL
  , LAST_UPD_TS                 TIMESTAMP     NOT NULL WITH DEFAULT
  , LAST_UPD_PGM                CHAR(8)       NOT NULL
  , LAST_UPD_USER               CHAR(8)       NOT NULL
  , CONSTRAINT PK_T_CODE_LOOKUP PRIMARY KEY (CODE_TYPE, CODE_VALUE)
  )
  CCSID EBCDIC;

CREATE UNIQUE INDEX CLR.XCODE_LOOKUP_PK
    ON CLR.T_CODE_LOOKUP (CODE_TYPE, CODE_VALUE);

COMMENT ON TABLE CLR.T_CODE_LOOKUP IS
  'Code lookup values';
COMMENT ON COLUMN CLR.T_CODE_LOOKUP.CODE_TYPE IS
  'Code type';
COMMENT ON COLUMN CLR.T_CODE_LOOKUP.CODE_VALUE IS
  'Value';
COMMENT ON COLUMN CLR.T_CODE_LOOKUP.CODE_DESC_EN IS
  'English description';
COMMENT ON COLUMN CLR.T_CODE_LOOKUP.CODE_DESC_LOCAL IS
  'Local-language description';
COMMENT ON COLUMN CLR.T_CODE_LOOKUP.ACTIVE_FLAG IS
  'Active';
COMMENT ON COLUMN CLR.T_CODE_LOOKUP.LAST_UPD_TS IS
  'Timestamp of last update';
COMMENT ON COLUMN CLR.T_CODE_LOOKUP.LAST_UPD_PGM IS
  'Program that last updated the row';
COMMENT ON COLUMN CLR.T_CODE_LOOKUP.LAST_UPD_USER IS
  'User or batch id that last updated the row';

-- --------------------------------------------------------------------
-- CLR.T_SALVAGE
-- Salvage disposals
-- Area: RECOVER    Copybook: SALREC01
-- --------------------------------------------------------------------
CREATE TABLE CLR.T_SALVAGE
  ( SALV_ID                     BIGINT        NOT NULL GENERATED ALWAYS AS IDENTITY
  , CLAIM_ID                    CHAR(12)      NOT NULL
  , SALV_CATEGORY               CHAR(1)       NOT NULL
  , DISPOSAL_DT                 DATE
  , PROCEEDS_AMT                DECIMAL(11,2)
  , VENDOR_CD                   CHAR(8)       NOT NULL
  , CREATED_TS                  TIMESTAMP     NOT NULL
  , LAST_UPD_TS                 TIMESTAMP     NOT NULL WITH DEFAULT
  , LAST_UPD_PGM                CHAR(8)       NOT NULL
  , LAST_UPD_USER               CHAR(8)       NOT NULL
  , CONSTRAINT PK_T_SALVAGE PRIMARY KEY (SALV_ID)
  )
  CCSID EBCDIC;

CREATE UNIQUE INDEX CLR.XSALVAGE_PK
    ON CLR.T_SALVAGE (SALV_ID);
CREATE INDEX CLR.XSALVAGE_CLM
    ON CLR.T_SALVAGE (CLAIM_ID);

COMMENT ON TABLE CLR.T_SALVAGE IS
  'Salvage disposals';
COMMENT ON COLUMN CLR.T_SALVAGE.SALV_ID IS
  'Salvage id';
COMMENT ON COLUMN CLR.T_SALVAGE.CLAIM_ID IS
  'Claim reference';
COMMENT ON COLUMN CLR.T_SALVAGE.SALV_CATEGORY IS
  'Category (A, B, S, N)';
COMMENT ON COLUMN CLR.T_SALVAGE.DISPOSAL_DT IS
  'Disposal date';
COMMENT ON COLUMN CLR.T_SALVAGE.PROCEEDS_AMT IS
  'Proceeds';
COMMENT ON COLUMN CLR.T_SALVAGE.VENDOR_CD IS
  'Salvage agent (SALVANTA)';
COMMENT ON COLUMN CLR.T_SALVAGE.CREATED_TS IS
  'Row creation timestamp';
COMMENT ON COLUMN CLR.T_SALVAGE.LAST_UPD_TS IS
  'Timestamp of last update';
COMMENT ON COLUMN CLR.T_SALVAGE.LAST_UPD_PGM IS
  'Program that last updated the row';
COMMENT ON COLUMN CLR.T_SALVAGE.LAST_UPD_USER IS
  'User or batch id that last updated the row';

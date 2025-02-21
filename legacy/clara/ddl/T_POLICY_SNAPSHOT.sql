-- --------------------------------------------------------------------
-- CLR.T_POLICY_SNAPSHOT
-- Policy snapshot copied from PALM at FNOL
-- Area: FNOL    Copybook: CLRPOL01
-- --------------------------------------------------------------------
CREATE TABLE CLR.T_POLICY_SNAPSHOT
  ( POLICY_NO                   CHAR(10)      NOT NULL
  , SNAPSHOT_DT                 DATE          NOT NULL
  , PRODUCT_CD                  CHAR(6)       NOT NULL
  , COVER_START_DT              DATE          NOT NULL
  , COVER_END_DT                DATE          NOT NULL
  , EXCESS_AMT                  DECIMAL(11,2) NOT NULL
  , SUM_INSURED_AMT             DECIMAL(13,2)
  , PH_POSTCODE                 CHAR(8)       NOT NULL
  , BRANCH_CD                   CHAR(3)
  , LAST_UPD_TS                 TIMESTAMP     NOT NULL WITH DEFAULT
  , LAST_UPD_PGM                CHAR(8)       NOT NULL
  , LAST_UPD_USER               CHAR(8)       NOT NULL
  , CONSTRAINT PK_T_POLICY_SNAPSHOT PRIMARY KEY (POLICY_NO, SNAPSHOT_DT)
  )
  CCSID EBCDIC;

CREATE UNIQUE INDEX CLR.XPOLICY_SNAPSHO_PK
    ON CLR.T_POLICY_SNAPSHOT (POLICY_NO, SNAPSHOT_DT);

COMMENT ON TABLE CLR.T_POLICY_SNAPSHOT IS
  'Policy snapshot copied from PALM at FNOL';
COMMENT ON COLUMN CLR.T_POLICY_SNAPSHOT.POLICY_NO IS
  'Policy number';
COMMENT ON COLUMN CLR.T_POLICY_SNAPSHOT.SNAPSHOT_DT IS
  'Snapshot date';
COMMENT ON COLUMN CLR.T_POLICY_SNAPSHOT.PRODUCT_CD IS
  'Product';
COMMENT ON COLUMN CLR.T_POLICY_SNAPSHOT.COVER_START_DT IS
  'Cover start';
COMMENT ON COLUMN CLR.T_POLICY_SNAPSHOT.COVER_END_DT IS
  'Cover end';
COMMENT ON COLUMN CLR.T_POLICY_SNAPSHOT.EXCESS_AMT IS
  'Standard excess';
COMMENT ON COLUMN CLR.T_POLICY_SNAPSHOT.SUM_INSURED_AMT IS
  'Sum insured';
COMMENT ON COLUMN CLR.T_POLICY_SNAPSHOT.PH_POSTCODE IS
  'Policyholder postcode [PII]';
COMMENT ON COLUMN CLR.T_POLICY_SNAPSHOT.BRANCH_CD IS
  'Branch code (UK, NO, SE, DK branch)';
COMMENT ON COLUMN CLR.T_POLICY_SNAPSHOT.LAST_UPD_TS IS
  'Timestamp of last update';
COMMENT ON COLUMN CLR.T_POLICY_SNAPSHOT.LAST_UPD_PGM IS
  'Program that last updated the row';
COMMENT ON COLUMN CLR.T_POLICY_SNAPSHOT.LAST_UPD_USER IS
  'User or batch id that last updated the row';

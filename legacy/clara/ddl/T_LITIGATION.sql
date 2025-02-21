-- --------------------------------------------------------------------
-- CLR.T_LITIGATION
-- Litigation and solicitor instructions
-- Area: RECOVER    Copybook: LITREC01
-- --------------------------------------------------------------------
CREATE TABLE CLR.T_LITIGATION
  ( LIT_ID                      BIGINT        NOT NULL GENERATED ALWAYS AS IDENTITY
  , CLAIM_ID                    CHAR(12)      NOT NULL
  , SOLICITOR_VENDOR_CD         CHAR(8)       NOT NULL
  , INSTRUCTED_DT               DATE          NOT NULL
  , COURT_REF                   CHAR(20)
  , LIT_STATUS                  CHAR(2)       NOT NULL
  , BRANCH_CD                   CHAR(3)
  , CREATED_TS                  TIMESTAMP     NOT NULL
  , EXT_REF                     CHAR(20)
  , LAST_UPD_TS                 TIMESTAMP     NOT NULL WITH DEFAULT
  , LAST_UPD_PGM                CHAR(8)       NOT NULL
  , LAST_UPD_USER               CHAR(8)       NOT NULL
  , CONSTRAINT PK_T_LITIGATION PRIMARY KEY (LIT_ID)
  )
  CCSID EBCDIC;

CREATE UNIQUE INDEX CLR.XLITIGATION_PK
    ON CLR.T_LITIGATION (LIT_ID);
CREATE INDEX CLR.XLITIGATION_CLM
    ON CLR.T_LITIGATION (CLAIM_ID);

COMMENT ON TABLE CLR.T_LITIGATION IS
  'Litigation and solicitor instructions';
COMMENT ON COLUMN CLR.T_LITIGATION.LIT_ID IS
  'Litigation id';
COMMENT ON COLUMN CLR.T_LITIGATION.CLAIM_ID IS
  'Claim reference';
COMMENT ON COLUMN CLR.T_LITIGATION.SOLICITOR_VENDOR_CD IS
  'Solicitor';
COMMENT ON COLUMN CLR.T_LITIGATION.INSTRUCTED_DT IS
  'Instructed';
COMMENT ON COLUMN CLR.T_LITIGATION.COURT_REF IS
  'Court reference';
COMMENT ON COLUMN CLR.T_LITIGATION.LIT_STATUS IS
  'Status';
COMMENT ON COLUMN CLR.T_LITIGATION.BRANCH_CD IS
  'Branch code (UK, NO, SE, DK branch)';
COMMENT ON COLUMN CLR.T_LITIGATION.CREATED_TS IS
  'Row creation timestamp';
COMMENT ON COLUMN CLR.T_LITIGATION.EXT_REF IS
  'External reference';
COMMENT ON COLUMN CLR.T_LITIGATION.LAST_UPD_TS IS
  'Timestamp of last update';
COMMENT ON COLUMN CLR.T_LITIGATION.LAST_UPD_PGM IS
  'Program that last updated the row';
COMMENT ON COLUMN CLR.T_LITIGATION.LAST_UPD_USER IS
  'User or batch id that last updated the row';

-- --------------------------------------------------------------------
-- CLR.T_SIU_CASE
-- SIU case mirror
-- Area: FRAUD    Copybook: FRDSIU01
-- --------------------------------------------------------------------
CREATE TABLE CLR.T_SIU_CASE
  ( SIU_CASE_ID                 CHAR(10)      NOT NULL
  , REF_ID                      BIGINT        NOT NULL
  , INVESTIGATOR_USER           CHAR(8)       NOT NULL
  , OPENED_DT                   DATE          NOT NULL
  , CASE_STATUS                 CHAR(2)       NOT NULL
  , PARTNER_VENDOR_CD           CHAR(8)
  , BRANCH_CD                   CHAR(3)
  , VERSION_NO                  SMALLINT      NOT NULL
  , LAST_UPD_TS                 TIMESTAMP     NOT NULL WITH DEFAULT
  , LAST_UPD_PGM                CHAR(8)       NOT NULL
  , LAST_UPD_USER               CHAR(8)       NOT NULL
  , CONSTRAINT PK_T_SIU_CASE PRIMARY KEY (SIU_CASE_ID)
  )
  CCSID EBCDIC;

CREATE UNIQUE INDEX CLR.XSIU_CASE_PK
    ON CLR.T_SIU_CASE (SIU_CASE_ID);

COMMENT ON TABLE CLR.T_SIU_CASE IS
  'SIU case mirror';
COMMENT ON COLUMN CLR.T_SIU_CASE.SIU_CASE_ID IS
  'Case id';
COMMENT ON COLUMN CLR.T_SIU_CASE.REF_ID IS
  'Referral';
COMMENT ON COLUMN CLR.T_SIU_CASE.INVESTIGATOR_USER IS
  'Investigator';
COMMENT ON COLUMN CLR.T_SIU_CASE.OPENED_DT IS
  'Opened';
COMMENT ON COLUMN CLR.T_SIU_CASE.CASE_STATUS IS
  'Status';
COMMENT ON COLUMN CLR.T_SIU_CASE.PARTNER_VENDOR_CD IS
  'Partner (GREYFOLD)';
COMMENT ON COLUMN CLR.T_SIU_CASE.BRANCH_CD IS
  'Branch code (UK, NO, SE, DK branch)';
COMMENT ON COLUMN CLR.T_SIU_CASE.VERSION_NO IS
  'Optimistic locking version';
COMMENT ON COLUMN CLR.T_SIU_CASE.LAST_UPD_TS IS
  'Timestamp of last update';
COMMENT ON COLUMN CLR.T_SIU_CASE.LAST_UPD_PGM IS
  'Program that last updated the row';
COMMENT ON COLUMN CLR.T_SIU_CASE.LAST_UPD_USER IS
  'User or batch id that last updated the row';

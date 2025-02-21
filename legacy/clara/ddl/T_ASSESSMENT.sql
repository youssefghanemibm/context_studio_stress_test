-- --------------------------------------------------------------------
-- CLR.T_ASSESSMENT
-- Assessment records
-- Area: ASSESS    Copybook: CLRASM01
-- --------------------------------------------------------------------
CREATE TABLE CLR.T_ASSESSMENT
  ( ASSESS_ID                   BIGINT        NOT NULL GENERATED ALWAYS AS IDENTITY
  , CLAIM_ID                    CHAR(12)      NOT NULL
  , ASSESS_TYPE_CD              CHAR(2)       NOT NULL
  , COVER_DECISION_CD           CHAR(2)       NOT NULL
  , ESTIMATE_AMT                DECIMAL(13,2) NOT NULL
  , REPORT_RECEIVED_DT          DATE
  , LAST_UPD_TS                 TIMESTAMP     NOT NULL WITH DEFAULT
  , LAST_UPD_PGM                CHAR(8)       NOT NULL
  , LAST_UPD_USER               CHAR(8)       NOT NULL
  , CONSTRAINT PK_T_ASSESSMENT PRIMARY KEY (ASSESS_ID)
  )
  CCSID EBCDIC;

CREATE UNIQUE INDEX CLR.XASSESSMENT_PK
    ON CLR.T_ASSESSMENT (ASSESS_ID);
CREATE INDEX CLR.XASSESSMENT_CLM
    ON CLR.T_ASSESSMENT (CLAIM_ID);

COMMENT ON TABLE CLR.T_ASSESSMENT IS
  'Assessment records';
COMMENT ON COLUMN CLR.T_ASSESSMENT.ASSESS_ID IS
  'Assessment id';
COMMENT ON COLUMN CLR.T_ASSESSMENT.CLAIM_ID IS
  'Claim reference';
COMMENT ON COLUMN CLR.T_ASSESSMENT.ASSESS_TYPE_CD IS
  'DK desk, SV site visit, VI video';
COMMENT ON COLUMN CLR.T_ASSESSMENT.COVER_DECISION_CD IS
  'AC accepted, DC declined, PA partial';
COMMENT ON COLUMN CLR.T_ASSESSMENT.ESTIMATE_AMT IS
  'Assessed estimate';
COMMENT ON COLUMN CLR.T_ASSESSMENT.REPORT_RECEIVED_DT IS
  'Report received';
COMMENT ON COLUMN CLR.T_ASSESSMENT.LAST_UPD_TS IS
  'Timestamp of last update';
COMMENT ON COLUMN CLR.T_ASSESSMENT.LAST_UPD_PGM IS
  'Program that last updated the row';
COMMENT ON COLUMN CLR.T_ASSESSMENT.LAST_UPD_USER IS
  'User or batch id that last updated the row';

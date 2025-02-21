-- --------------------------------------------------------------------
-- CLR.T_INSPECTION
-- Inspections
-- Area: ASSESS    Copybook: CLRINS01
-- --------------------------------------------------------------------
CREATE TABLE CLR.T_INSPECTION
  ( INSP_ID                     BIGINT        NOT NULL GENERATED ALWAYS AS IDENTITY
  , CLAIM_ID                    CHAR(12)      NOT NULL
  , BOOKED_TS                   TIMESTAMP     NOT NULL
  , COMPLETED_TS                TIMESTAMP
  , INSP_ADDR                   VARCHAR(120)  NOT NULL
  , CREATED_TS                  TIMESTAMP     NOT NULL
  , LAST_UPD_TS                 TIMESTAMP     NOT NULL WITH DEFAULT
  , LAST_UPD_PGM                CHAR(8)       NOT NULL
  , LAST_UPD_USER               CHAR(8)       NOT NULL
  , CONSTRAINT PK_T_INSPECTION PRIMARY KEY (INSP_ID)
  )
  CCSID EBCDIC;

CREATE UNIQUE INDEX CLR.XINSPECTION_PK
    ON CLR.T_INSPECTION (INSP_ID);
CREATE INDEX CLR.XINSPECTION_CLM
    ON CLR.T_INSPECTION (CLAIM_ID);

COMMENT ON TABLE CLR.T_INSPECTION IS
  'Inspections';
COMMENT ON COLUMN CLR.T_INSPECTION.INSP_ID IS
  'Inspection id';
COMMENT ON COLUMN CLR.T_INSPECTION.CLAIM_ID IS
  'Claim reference';
COMMENT ON COLUMN CLR.T_INSPECTION.BOOKED_TS IS
  'Booked for';
COMMENT ON COLUMN CLR.T_INSPECTION.COMPLETED_TS IS
  'Completed';
COMMENT ON COLUMN CLR.T_INSPECTION.INSP_ADDR IS
  'Inspection address [PII]';
COMMENT ON COLUMN CLR.T_INSPECTION.CREATED_TS IS
  'Row creation timestamp';
COMMENT ON COLUMN CLR.T_INSPECTION.LAST_UPD_TS IS
  'Timestamp of last update';
COMMENT ON COLUMN CLR.T_INSPECTION.LAST_UPD_PGM IS
  'Program that last updated the row';
COMMENT ON COLUMN CLR.T_INSPECTION.LAST_UPD_USER IS
  'User or batch id that last updated the row';

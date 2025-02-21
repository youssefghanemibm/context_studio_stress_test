-- --------------------------------------------------------------------
-- CLR.T_TRIAGE
-- Triage decisions
-- Area: TRIAGE    Copybook: CLRTRG01
-- --------------------------------------------------------------------
CREATE TABLE CLR.T_TRIAGE
  ( CLAIM_ID                    CHAR(12)      NOT NULL
  , TRIAGE_SEQ                  SMALLINT      NOT NULL
  , TRIAGE_TS                   TIMESTAMP     NOT NULL
  , ROUTE_CD                    CHAR(4)       NOT NULL
  , SCORE_AT_TRIAGE             SMALLINT      NOT NULL
  , FASTTRACK_FLAG              CHAR(1)       NOT NULL
  , BRANCH_CD                   CHAR(3)
  , CREATED_TS                  TIMESTAMP     NOT NULL
  , SOURCE_SYS_CD               CHAR(4)
  , LAST_UPD_TS                 TIMESTAMP     NOT NULL WITH DEFAULT
  , LAST_UPD_PGM                CHAR(8)       NOT NULL
  , LAST_UPD_USER               CHAR(8)       NOT NULL
  , CONSTRAINT PK_T_TRIAGE PRIMARY KEY (CLAIM_ID, TRIAGE_SEQ)
  )
  CCSID EBCDIC;

CREATE UNIQUE INDEX CLR.XTRIAGE_PK
    ON CLR.T_TRIAGE (CLAIM_ID, TRIAGE_SEQ);
CREATE INDEX CLR.XTRIAGE_CLM
    ON CLR.T_TRIAGE (CLAIM_ID);

COMMENT ON TABLE CLR.T_TRIAGE IS
  'Triage decisions';
COMMENT ON COLUMN CLR.T_TRIAGE.CLAIM_ID IS
  'Claim reference';
COMMENT ON COLUMN CLR.T_TRIAGE.TRIAGE_SEQ IS
  'Sequence';
COMMENT ON COLUMN CLR.T_TRIAGE.TRIAGE_TS IS
  'Triage time';
COMMENT ON COLUMN CLR.T_TRIAGE.ROUTE_CD IS
  'Routing outcome (FAST, HNDL, MCL)';
COMMENT ON COLUMN CLR.T_TRIAGE.SCORE_AT_TRIAGE IS
  'Sentinel score at triage';
COMMENT ON COLUMN CLR.T_TRIAGE.FASTTRACK_FLAG IS
  'Fast-track eligible (BR-TRI-006)';
COMMENT ON COLUMN CLR.T_TRIAGE.BRANCH_CD IS
  'Branch code (UK, NO, SE, DK branch)';
COMMENT ON COLUMN CLR.T_TRIAGE.CREATED_TS IS
  'Row creation timestamp';
COMMENT ON COLUMN CLR.T_TRIAGE.SOURCE_SYS_CD IS
  'Originating system code';
COMMENT ON COLUMN CLR.T_TRIAGE.LAST_UPD_TS IS
  'Timestamp of last update';
COMMENT ON COLUMN CLR.T_TRIAGE.LAST_UPD_PGM IS
  'Program that last updated the row';
COMMENT ON COLUMN CLR.T_TRIAGE.LAST_UPD_USER IS
  'User or batch id that last updated the row';

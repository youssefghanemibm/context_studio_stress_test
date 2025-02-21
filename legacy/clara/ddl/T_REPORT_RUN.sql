-- --------------------------------------------------------------------
-- CLR.T_REPORT_RUN
-- Report run log
-- Area: REPORT    Copybook: RPTRUN01
-- --------------------------------------------------------------------
CREATE TABLE CLR.T_REPORT_RUN
  ( RUN_ID                      INTEGER       NOT NULL
  , REPORT_CD                   CHAR(8)       NOT NULL
  , RUN_TS                      TIMESTAMP     NOT NULL
  , ROW_COUNT                   INTEGER       NOT NULL
  , RUN_STATUS                  CHAR(2)       NOT NULL
  , LAST_UPD_TS                 TIMESTAMP     NOT NULL WITH DEFAULT
  , LAST_UPD_PGM                CHAR(8)       NOT NULL
  , LAST_UPD_USER               CHAR(8)       NOT NULL
  , CONSTRAINT PK_T_REPORT_RUN PRIMARY KEY (RUN_ID)
  )
  CCSID EBCDIC;

CREATE UNIQUE INDEX CLR.XREPORT_RUN_PK
    ON CLR.T_REPORT_RUN (RUN_ID);

COMMENT ON TABLE CLR.T_REPORT_RUN IS
  'Report run log';
COMMENT ON COLUMN CLR.T_REPORT_RUN.RUN_ID IS
  'Run id';
COMMENT ON COLUMN CLR.T_REPORT_RUN.REPORT_CD IS
  'Report code';
COMMENT ON COLUMN CLR.T_REPORT_RUN.RUN_TS IS
  'Run time';
COMMENT ON COLUMN CLR.T_REPORT_RUN.ROW_COUNT IS
  'Rows';
COMMENT ON COLUMN CLR.T_REPORT_RUN.RUN_STATUS IS
  'Status';
COMMENT ON COLUMN CLR.T_REPORT_RUN.LAST_UPD_TS IS
  'Timestamp of last update';
COMMENT ON COLUMN CLR.T_REPORT_RUN.LAST_UPD_PGM IS
  'Program that last updated the row';
COMMENT ON COLUMN CLR.T_REPORT_RUN.LAST_UPD_USER IS
  'User or batch id that last updated the row';

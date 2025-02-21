-- --------------------------------------------------------------------
-- CLR.T_GL_PERIOD
-- GL period control
-- Area: GL    Copybook: GLPER01
-- --------------------------------------------------------------------
CREATE TABLE CLR.T_GL_PERIOD
  ( GL_PERIOD                   CHAR(6)       NOT NULL
  , PERIOD_STATUS               CHAR(1)       NOT NULL
  , CLOSED_TS                   TIMESTAMP
  , CLOSED_BY                   CHAR(8)
  , LAST_UPD_TS                 TIMESTAMP     NOT NULL WITH DEFAULT
  , LAST_UPD_PGM                CHAR(8)       NOT NULL
  , LAST_UPD_USER               CHAR(8)       NOT NULL
  , CONSTRAINT PK_T_GL_PERIOD PRIMARY KEY (GL_PERIOD)
  )
  CCSID EBCDIC;

CREATE UNIQUE INDEX CLR.XGL_PERIOD_PK
    ON CLR.T_GL_PERIOD (GL_PERIOD);

COMMENT ON TABLE CLR.T_GL_PERIOD IS
  'GL period control';
COMMENT ON COLUMN CLR.T_GL_PERIOD.GL_PERIOD IS
  'Period';
COMMENT ON COLUMN CLR.T_GL_PERIOD.PERIOD_STATUS IS
  'O open, C closed';
COMMENT ON COLUMN CLR.T_GL_PERIOD.CLOSED_TS IS
  'Closed';
COMMENT ON COLUMN CLR.T_GL_PERIOD.CLOSED_BY IS
  'Closed by';
COMMENT ON COLUMN CLR.T_GL_PERIOD.LAST_UPD_TS IS
  'Timestamp of last update';
COMMENT ON COLUMN CLR.T_GL_PERIOD.LAST_UPD_PGM IS
  'Program that last updated the row';
COMMENT ON COLUMN CLR.T_GL_PERIOD.LAST_UPD_USER IS
  'User or batch id that last updated the row';

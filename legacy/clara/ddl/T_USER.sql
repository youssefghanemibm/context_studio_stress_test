-- --------------------------------------------------------------------
-- CLR.T_USER
-- CLARA users and authority levels
-- Area: COMMON    Copybook: USRREC01
-- --------------------------------------------------------------------
CREATE TABLE CLR.T_USER
  ( USER_ID                     CHAR(8)       NOT NULL
  , USER_NAME                   VARCHAR(60)   NOT NULL
  , TEAM_CD                     CHAR(4)       NOT NULL
  , RSV_AUTH_LEVEL              CHAR(2)       NOT NULL
  , PAY_AUTH_LEVEL              CHAR(2)       NOT NULL
  , ACTIVE_FLAG                 CHAR(1)       NOT NULL
  , LAST_UPD_TS                 TIMESTAMP     NOT NULL WITH DEFAULT
  , LAST_UPD_PGM                CHAR(8)       NOT NULL
  , LAST_UPD_USER               CHAR(8)       NOT NULL
  , CONSTRAINT PK_T_USER PRIMARY KEY (USER_ID)
  )
  CCSID EBCDIC;

CREATE UNIQUE INDEX CLR.XUSER_PK
    ON CLR.T_USER (USER_ID);

COMMENT ON TABLE CLR.T_USER IS
  'CLARA users and authority levels';
COMMENT ON COLUMN CLR.T_USER.USER_ID IS
  'User id';
COMMENT ON COLUMN CLR.T_USER.USER_NAME IS
  'Name [PII]';
COMMENT ON COLUMN CLR.T_USER.TEAM_CD IS
  'Team';
COMMENT ON COLUMN CLR.T_USER.RSV_AUTH_LEVEL IS
  'Reserve authority level';
COMMENT ON COLUMN CLR.T_USER.PAY_AUTH_LEVEL IS
  'Payment authority level';
COMMENT ON COLUMN CLR.T_USER.ACTIVE_FLAG IS
  'Active';
COMMENT ON COLUMN CLR.T_USER.LAST_UPD_TS IS
  'Timestamp of last update';
COMMENT ON COLUMN CLR.T_USER.LAST_UPD_PGM IS
  'Program that last updated the row';
COMMENT ON COLUMN CLR.T_USER.LAST_UPD_USER IS
  'User or batch id that last updated the row';

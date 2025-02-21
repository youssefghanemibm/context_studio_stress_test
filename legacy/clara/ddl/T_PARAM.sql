-- --------------------------------------------------------------------
-- CLR.T_PARAM
-- Business parameters with validity dates (read via CLRCM040)
-- Area: COMMON    Copybook: PARMREC1
-- --------------------------------------------------------------------
CREATE TABLE CLR.T_PARAM
  ( PARAM_KEY                   CHAR(20)      NOT NULL
  , VALID_FROM                  DATE          NOT NULL
  , VALID_TO                    DATE
  , PARAM_VALUE                 VARCHAR(40)   NOT NULL
  , PARAM_DESC                  VARCHAR(120)  NOT NULL
  , CHANGE_TICKET               CHAR(10)
  , CHANGED_BY                  CHAR(8)       NOT NULL
  , CONSTRAINT PK_T_PARAM PRIMARY KEY (PARAM_KEY, VALID_FROM)
  )
  CCSID EBCDIC;

CREATE UNIQUE INDEX CLR.XPARAM_PK
    ON CLR.T_PARAM (PARAM_KEY, VALID_FROM);

COMMENT ON TABLE CLR.T_PARAM IS
  'Business parameters with validity dates (read via CLRCM040)';
COMMENT ON COLUMN CLR.T_PARAM.PARAM_KEY IS
  'Parameter key';
COMMENT ON COLUMN CLR.T_PARAM.VALID_FROM IS
  'Valid from';
COMMENT ON COLUMN CLR.T_PARAM.VALID_TO IS
  'Valid to';
COMMENT ON COLUMN CLR.T_PARAM.PARAM_VALUE IS
  'Parameter value';
COMMENT ON COLUMN CLR.T_PARAM.PARAM_DESC IS
  'Description';
COMMENT ON COLUMN CLR.T_PARAM.CHANGE_TICKET IS
  'Change ticket (CHUB-nnn)';
COMMENT ON COLUMN CLR.T_PARAM.CHANGED_BY IS
  'User';

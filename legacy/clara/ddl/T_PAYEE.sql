-- --------------------------------------------------------------------
-- CLR.T_PAYEE
-- Payees
-- Area: SETTLE    Copybook: PAYEE01
-- --------------------------------------------------------------------
CREATE TABLE CLR.T_PAYEE
  ( PAYEE_ID                    CHAR(10)      NOT NULL
  , PAYEE_NAME                  VARCHAR(80)   NOT NULL
  , IBAN                        CHAR(34)      NOT NULL
  , SORT_CODE                   CHAR(6)
  , PAYEE_TYPE_CD               CHAR(2)       NOT NULL
  , CREATED_TS                  TIMESTAMP     NOT NULL
  , SOURCE_SYS_CD               CHAR(4)
  , LAST_UPD_TS                 TIMESTAMP     NOT NULL WITH DEFAULT
  , LAST_UPD_PGM                CHAR(8)       NOT NULL
  , LAST_UPD_USER               CHAR(8)       NOT NULL
  , CONSTRAINT PK_T_PAYEE PRIMARY KEY (PAYEE_ID)
  )
  CCSID EBCDIC;

CREATE UNIQUE INDEX CLR.XPAYEE_PK
    ON CLR.T_PAYEE (PAYEE_ID);

COMMENT ON TABLE CLR.T_PAYEE IS
  'Payees';
COMMENT ON COLUMN CLR.T_PAYEE.PAYEE_ID IS
  'Payee id';
COMMENT ON COLUMN CLR.T_PAYEE.PAYEE_NAME IS
  'Payee name [PII]';
COMMENT ON COLUMN CLR.T_PAYEE.IBAN IS
  'IBAN or masked account [PII]';
COMMENT ON COLUMN CLR.T_PAYEE.SORT_CODE IS
  'UK sort code [PII]';
COMMENT ON COLUMN CLR.T_PAYEE.PAYEE_TYPE_CD IS
  'PH, TP, VN vendor';
COMMENT ON COLUMN CLR.T_PAYEE.CREATED_TS IS
  'Row creation timestamp';
COMMENT ON COLUMN CLR.T_PAYEE.SOURCE_SYS_CD IS
  'Originating system code';
COMMENT ON COLUMN CLR.T_PAYEE.LAST_UPD_TS IS
  'Timestamp of last update';
COMMENT ON COLUMN CLR.T_PAYEE.LAST_UPD_PGM IS
  'Program that last updated the row';
COMMENT ON COLUMN CLR.T_PAYEE.LAST_UPD_USER IS
  'User or batch id that last updated the row';

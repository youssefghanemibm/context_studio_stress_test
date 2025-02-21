-- --------------------------------------------------------------------
-- CLR.T_PAYMENT
-- Payments
-- Area: SETTLE    Copybook: PAYREC01
-- --------------------------------------------------------------------
CREATE TABLE CLR.T_PAYMENT
  ( PAY_ID                      BIGINT        NOT NULL GENERATED ALWAYS AS IDENTITY
  , CLAIM_ID                    CHAR(12)      NOT NULL
  , PAYEE_ID                    CHAR(10)      NOT NULL
  , PAY_AMT                     DECIMAL(13,2) NOT NULL
  , CURRENCY_CD                 CHAR(3)       NOT NULL
  , PAY_STATUS                  CHAR(2)       NOT NULL
  , AUTH_USER                   CHAR(8)       NOT NULL
  , SANCTIONS_RESULT            CHAR(2)       NOT NULL
  , COMMENT_TXT                 VARCHAR(254)
  , LAST_UPD_TS                 TIMESTAMP     NOT NULL WITH DEFAULT
  , LAST_UPD_PGM                CHAR(8)       NOT NULL
  , LAST_UPD_USER               CHAR(8)       NOT NULL
  , CONSTRAINT PK_T_PAYMENT PRIMARY KEY (PAY_ID)
  )
  CCSID EBCDIC;

CREATE UNIQUE INDEX CLR.XPAYMENT_PK
    ON CLR.T_PAYMENT (PAY_ID);
CREATE INDEX CLR.XPAYMENT_CLM
    ON CLR.T_PAYMENT (CLAIM_ID);

COMMENT ON TABLE CLR.T_PAYMENT IS
  'Payments';
COMMENT ON COLUMN CLR.T_PAYMENT.PAY_ID IS
  'Payment id';
COMMENT ON COLUMN CLR.T_PAYMENT.CLAIM_ID IS
  'Claim reference';
COMMENT ON COLUMN CLR.T_PAYMENT.PAYEE_ID IS
  'Payee';
COMMENT ON COLUMN CLR.T_PAYMENT.PAY_AMT IS
  'Amount';
COMMENT ON COLUMN CLR.T_PAYMENT.CURRENCY_CD IS
  'Currency';
COMMENT ON COLUMN CLR.T_PAYMENT.PAY_STATUS IS
  'RQ requested, SC screened, SN sent, CF confirmed, CX cancelled';
COMMENT ON COLUMN CLR.T_PAYMENT.AUTH_USER IS
  'Authoriser';
COMMENT ON COLUMN CLR.T_PAYMENT.SANCTIONS_RESULT IS
  'WatchScreen result';
COMMENT ON COLUMN CLR.T_PAYMENT.COMMENT_TXT IS
  'Free-text comment';
COMMENT ON COLUMN CLR.T_PAYMENT.LAST_UPD_TS IS
  'Timestamp of last update';
COMMENT ON COLUMN CLR.T_PAYMENT.LAST_UPD_PGM IS
  'Program that last updated the row';
COMMENT ON COLUMN CLR.T_PAYMENT.LAST_UPD_USER IS
  'User or batch id that last updated the row';

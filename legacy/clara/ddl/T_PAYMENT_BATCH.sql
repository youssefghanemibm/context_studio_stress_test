-- --------------------------------------------------------------------
-- CLR.T_PAYMENT_BATCH
-- Payment batches to CPG
-- Area: SETTLE    Copybook: PAYBAT01
-- --------------------------------------------------------------------
CREATE TABLE CLR.T_PAYMENT_BATCH
  ( BATCH_ID                    INTEGER       NOT NULL
  , BATCH_DT                    DATE          NOT NULL
  , PAY_COUNT                   INTEGER       NOT NULL
  , TOTAL_AMT                   DECIMAL(15,2) NOT NULL
  , CPG_FILE_NAME               CHAR(44)      NOT NULL
  , CPG_ACK_TS                  TIMESTAMP
  , LAST_UPD_TS                 TIMESTAMP     NOT NULL WITH DEFAULT
  , LAST_UPD_PGM                CHAR(8)       NOT NULL
  , LAST_UPD_USER               CHAR(8)       NOT NULL
  , CONSTRAINT PK_T_PAYMENT_BATCH PRIMARY KEY (BATCH_ID)
  )
  CCSID EBCDIC;

CREATE UNIQUE INDEX CLR.XPAYMENT_BATCH_PK
    ON CLR.T_PAYMENT_BATCH (BATCH_ID);

COMMENT ON TABLE CLR.T_PAYMENT_BATCH IS
  'Payment batches to CPG';
COMMENT ON COLUMN CLR.T_PAYMENT_BATCH.BATCH_ID IS
  'Batch id';
COMMENT ON COLUMN CLR.T_PAYMENT_BATCH.BATCH_DT IS
  'Batch date';
COMMENT ON COLUMN CLR.T_PAYMENT_BATCH.PAY_COUNT IS
  'Payments';
COMMENT ON COLUMN CLR.T_PAYMENT_BATCH.TOTAL_AMT IS
  'Total';
COMMENT ON COLUMN CLR.T_PAYMENT_BATCH.CPG_FILE_NAME IS
  'pain.001 file name';
COMMENT ON COLUMN CLR.T_PAYMENT_BATCH.CPG_ACK_TS IS
  'Acknowledged';
COMMENT ON COLUMN CLR.T_PAYMENT_BATCH.LAST_UPD_TS IS
  'Timestamp of last update';
COMMENT ON COLUMN CLR.T_PAYMENT_BATCH.LAST_UPD_PGM IS
  'Program that last updated the row';
COMMENT ON COLUMN CLR.T_PAYMENT_BATCH.LAST_UPD_USER IS
  'User or batch id that last updated the row';

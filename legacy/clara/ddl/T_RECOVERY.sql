-- --------------------------------------------------------------------
-- CLR.T_RECOVERY
-- Recoveries (subrogation receipts, salvage proceeds)
-- Area: RECOVER    Copybook: RCVREC01
-- --------------------------------------------------------------------
CREATE TABLE CLR.T_RECOVERY
  ( RCV_ID                      BIGINT        NOT NULL GENERATED ALWAYS AS IDENTITY
  , CLAIM_ID                    CHAR(12)      NOT NULL
  , SUBRO_CASE_ID               CHAR(10)
  , RCV_TYPE_CD                 CHAR(2)       NOT NULL
  , RCV_EXPECTED_AMT            DECIMAL(13,2) NOT NULL
  , RCV_RECEIVED_AMT            DECIMAL(13,2) NOT NULL
  , RCV_WRITE_OFF_AMT           DECIMAL(13,2)
  , WRITE_OFF_APPROVED_BY       CHAR(8)
  , RCV_STATUS                  CHAR(2)       NOT NULL
  , CURRENCY_CD                 CHAR(3)       NOT NULL
  , LAST_UPD_TS                 TIMESTAMP     NOT NULL WITH DEFAULT
  , LAST_UPD_PGM                CHAR(8)       NOT NULL
  , LAST_UPD_USER               CHAR(8)       NOT NULL
  , CONSTRAINT PK_T_RECOVERY PRIMARY KEY (RCV_ID)
  )
  CCSID EBCDIC;

CREATE UNIQUE INDEX CLR.XRECOVERY_PK
    ON CLR.T_RECOVERY (RCV_ID);
CREATE INDEX CLR.XRECOVERY_CLM
    ON CLR.T_RECOVERY (CLAIM_ID);

ALTER TABLE CLR.T_RECOVERY
  ADD CONSTRAINT FK_RECOVERY_1 FOREIGN KEY (SUBRO_CASE_ID)
      REFERENCES CLR.T_SUBROGATION_CASE (SUBRO_CASE_ID) ON DELETE RESTRICT;

COMMENT ON TABLE CLR.T_RECOVERY IS
  'Recoveries (subrogation receipts, salvage proceeds)';
COMMENT ON COLUMN CLR.T_RECOVERY.RCV_ID IS
  'Recovery identifier';
COMMENT ON COLUMN CLR.T_RECOVERY.CLAIM_ID IS
  'Claim reference';
COMMENT ON COLUMN CLR.T_RECOVERY.SUBRO_CASE_ID IS
  'Subrogation case';
COMMENT ON COLUMN CLR.T_RECOVERY.RCV_TYPE_CD IS
  'SB subrogation, SV salvage, EX excess recovery';
COMMENT ON COLUMN CLR.T_RECOVERY.RCV_EXPECTED_AMT IS
  'Expected recovery';
COMMENT ON COLUMN CLR.T_RECOVERY.RCV_RECEIVED_AMT IS
  'Amount received';
COMMENT ON COLUMN CLR.T_RECOVERY.RCV_WRITE_OFF_AMT IS
  'Amount written off';
COMMENT ON COLUMN CLR.T_RECOVERY.WRITE_OFF_APPROVED_BY IS
  'Approver of write-off (BR-REC-011)';
COMMENT ON COLUMN CLR.T_RECOVERY.RCV_STATUS IS
  'OP open, PT part-received, CL closed, WO written off';
COMMENT ON COLUMN CLR.T_RECOVERY.CURRENCY_CD IS
  'Currency';
COMMENT ON COLUMN CLR.T_RECOVERY.LAST_UPD_TS IS
  'Timestamp of last update';
COMMENT ON COLUMN CLR.T_RECOVERY.LAST_UPD_PGM IS
  'Program that last updated the row';
COMMENT ON COLUMN CLR.T_RECOVERY.LAST_UPD_USER IS
  'User or batch id that last updated the row';

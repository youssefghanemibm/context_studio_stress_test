-- --------------------------------------------------------------------
-- CLR.T_FNOL_EVENT
-- Raw FNOL events by channel
-- Area: FNOL    Copybook: CLRFNL01
-- --------------------------------------------------------------------
CREATE TABLE CLR.T_FNOL_EVENT
  ( FNOL_ID                     BIGINT        NOT NULL GENERATED ALWAYS AS IDENTITY
  , CLAIM_ID                    CHAR(12)
  , CHANNEL_CD                  CHAR(2)       NOT NULL
  , RECEIVED_TS                 TIMESTAMP     NOT NULL
  , PAYLOAD_REF                 CHAR(36)
  , CALLER_PHONE                CHAR(16)
  , ACK_SENT_TS                 TIMESTAMP
  , LAST_UPD_TS                 TIMESTAMP     NOT NULL WITH DEFAULT
  , LAST_UPD_PGM                CHAR(8)       NOT NULL
  , LAST_UPD_USER               CHAR(8)       NOT NULL
  , CONSTRAINT PK_T_FNOL_EVENT PRIMARY KEY (FNOL_ID)
  )
  CCSID EBCDIC;

CREATE UNIQUE INDEX CLR.XFNOL_EVENT_PK
    ON CLR.T_FNOL_EVENT (FNOL_ID);
CREATE INDEX CLR.XFNOL_EVENT_CLM
    ON CLR.T_FNOL_EVENT (CLAIM_ID);

COMMENT ON TABLE CLR.T_FNOL_EVENT IS
  'Raw FNOL events by channel';
COMMENT ON COLUMN CLR.T_FNOL_EVENT.FNOL_ID IS
  'FNOL event id';
COMMENT ON COLUMN CLR.T_FNOL_EVENT.CLAIM_ID IS
  'Claim reference';
COMMENT ON COLUMN CLR.T_FNOL_EVENT.CHANNEL_CD IS
  'Channel';
COMMENT ON COLUMN CLR.T_FNOL_EVENT.RECEIVED_TS IS
  'Received';
COMMENT ON COLUMN CLR.T_FNOL_EVENT.PAYLOAD_REF IS
  'Evidence Vault reference';
COMMENT ON COLUMN CLR.T_FNOL_EVENT.CALLER_PHONE IS
  'Caller phone [PII]';
COMMENT ON COLUMN CLR.T_FNOL_EVENT.ACK_SENT_TS IS
  'Acknowledgement sent';
COMMENT ON COLUMN CLR.T_FNOL_EVENT.LAST_UPD_TS IS
  'Timestamp of last update';
COMMENT ON COLUMN CLR.T_FNOL_EVENT.LAST_UPD_PGM IS
  'Program that last updated the row';
COMMENT ON COLUMN CLR.T_FNOL_EVENT.LAST_UPD_USER IS
  'User or batch id that last updated the row';

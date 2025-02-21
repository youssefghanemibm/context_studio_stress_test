-- --------------------------------------------------------------------
-- CLR.T_CLAIM_LINK
-- Linked claims (shared parties, vehicles, bank accounts)
-- Area: FRAUD    Copybook: FRDLNK01
-- --------------------------------------------------------------------
CREATE TABLE CLR.T_CLAIM_LINK
  ( LINK_ID                     BIGINT        NOT NULL GENERATED ALWAYS AS IDENTITY
  , CLAIM_ID_A                  CHAR(12)      NOT NULL
  , CLAIM_ID_B                  CHAR(12)      NOT NULL
  , LINK_TYPE_CD                CHAR(2)       NOT NULL
  , DETECTED_DT                 DATE          NOT NULL
  , BATCH_RUN_ID                INTEGER
  , EXT_REF                     CHAR(20)
  , VERSION_NO                  SMALLINT      NOT NULL
  , LAST_UPD_TS                 TIMESTAMP     NOT NULL WITH DEFAULT
  , LAST_UPD_PGM                CHAR(8)       NOT NULL
  , LAST_UPD_USER               CHAR(8)       NOT NULL
  , CONSTRAINT PK_T_CLAIM_LINK PRIMARY KEY (LINK_ID)
  )
  CCSID EBCDIC;

CREATE UNIQUE INDEX CLR.XCLAIM_LINK_PK
    ON CLR.T_CLAIM_LINK (LINK_ID);

COMMENT ON TABLE CLR.T_CLAIM_LINK IS
  'Linked claims (shared parties, vehicles, bank accounts)';
COMMENT ON COLUMN CLR.T_CLAIM_LINK.LINK_ID IS
  'Link id';
COMMENT ON COLUMN CLR.T_CLAIM_LINK.CLAIM_ID_A IS
  'Claim A';
COMMENT ON COLUMN CLR.T_CLAIM_LINK.CLAIM_ID_B IS
  'Claim B';
COMMENT ON COLUMN CLR.T_CLAIM_LINK.LINK_TYPE_CD IS
  'PH phone, BA bank account, VH vehicle, AD address';
COMMENT ON COLUMN CLR.T_CLAIM_LINK.DETECTED_DT IS
  'Detected';
COMMENT ON COLUMN CLR.T_CLAIM_LINK.BATCH_RUN_ID IS
  'Batch run identifier';
COMMENT ON COLUMN CLR.T_CLAIM_LINK.EXT_REF IS
  'External reference';
COMMENT ON COLUMN CLR.T_CLAIM_LINK.VERSION_NO IS
  'Optimistic locking version';
COMMENT ON COLUMN CLR.T_CLAIM_LINK.LAST_UPD_TS IS
  'Timestamp of last update';
COMMENT ON COLUMN CLR.T_CLAIM_LINK.LAST_UPD_PGM IS
  'Program that last updated the row';
COMMENT ON COLUMN CLR.T_CLAIM_LINK.LAST_UPD_USER IS
  'User or batch id that last updated the row';

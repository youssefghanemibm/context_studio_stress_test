-- --------------------------------------------------------------------
-- CLR.T_DOCUMENT_REF
-- Document references (DOCSTOR / Evidence Vault ids)
-- Area: COMMON    Copybook: DOCREF01
-- --------------------------------------------------------------------
CREATE TABLE CLR.T_DOCUMENT_REF
  ( DOC_REF_ID                  BIGINT        NOT NULL GENERATED ALWAYS AS IDENTITY
  , CLAIM_ID                    CHAR(12)      NOT NULL
  , VAULT_OBJECT_ID             CHAR(36)      NOT NULL
  , DOC_TYPE_CD                 CHAR(4)       NOT NULL
  , RECEIVED_TS                 TIMESTAMP     NOT NULL
  , LAST_UPD_TS                 TIMESTAMP     NOT NULL WITH DEFAULT
  , LAST_UPD_PGM                CHAR(8)       NOT NULL
  , LAST_UPD_USER               CHAR(8)       NOT NULL
  , CONSTRAINT PK_T_DOCUMENT_REF PRIMARY KEY (DOC_REF_ID)
  )
  CCSID EBCDIC;

CREATE UNIQUE INDEX CLR.XDOCUMENT_REF_PK
    ON CLR.T_DOCUMENT_REF (DOC_REF_ID);
CREATE INDEX CLR.XDOCUMENT_REF_CLM
    ON CLR.T_DOCUMENT_REF (CLAIM_ID);

COMMENT ON TABLE CLR.T_DOCUMENT_REF IS
  'Document references (DOCSTOR / Evidence Vault ids)';
COMMENT ON COLUMN CLR.T_DOCUMENT_REF.DOC_REF_ID IS
  'Reference id';
COMMENT ON COLUMN CLR.T_DOCUMENT_REF.CLAIM_ID IS
  'Claim reference';
COMMENT ON COLUMN CLR.T_DOCUMENT_REF.VAULT_OBJECT_ID IS
  'Evidence Vault object id';
COMMENT ON COLUMN CLR.T_DOCUMENT_REF.DOC_TYPE_CD IS
  'Type (PHOT, LETR, RPRT)';
COMMENT ON COLUMN CLR.T_DOCUMENT_REF.RECEIVED_TS IS
  'Received';
COMMENT ON COLUMN CLR.T_DOCUMENT_REF.LAST_UPD_TS IS
  'Timestamp of last update';
COMMENT ON COLUMN CLR.T_DOCUMENT_REF.LAST_UPD_PGM IS
  'Program that last updated the row';
COMMENT ON COLUMN CLR.T_DOCUMENT_REF.LAST_UPD_USER IS
  'User or batch id that last updated the row';

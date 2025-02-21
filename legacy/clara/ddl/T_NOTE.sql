-- --------------------------------------------------------------------
-- CLR.T_NOTE
-- Claim notes
-- Area: COMMON    Copybook: NOTEREC1
-- --------------------------------------------------------------------
CREATE TABLE CLR.T_NOTE
  ( NOTE_ID                     BIGINT        NOT NULL GENERATED ALWAYS AS IDENTITY
  , CLAIM_ID                    CHAR(12)      NOT NULL
  , NOTE_TS                     TIMESTAMP     NOT NULL
  , NOTE_TXT                    VARCHAR(2000) NOT NULL
  , NOTE_TYPE_CD                CHAR(2)       NOT NULL
  , LAST_UPD_TS                 TIMESTAMP     NOT NULL WITH DEFAULT
  , LAST_UPD_PGM                CHAR(8)       NOT NULL
  , LAST_UPD_USER               CHAR(8)       NOT NULL
  , CONSTRAINT PK_T_NOTE PRIMARY KEY (NOTE_ID)
  )
  CCSID EBCDIC;

CREATE UNIQUE INDEX CLR.XNOTE_PK
    ON CLR.T_NOTE (NOTE_ID);
CREATE INDEX CLR.XNOTE_CLM
    ON CLR.T_NOTE (CLAIM_ID);

COMMENT ON TABLE CLR.T_NOTE IS
  'Claim notes';
COMMENT ON COLUMN CLR.T_NOTE.NOTE_ID IS
  'Note id';
COMMENT ON COLUMN CLR.T_NOTE.CLAIM_ID IS
  'Claim reference';
COMMENT ON COLUMN CLR.T_NOTE.NOTE_TS IS
  'Time';
COMMENT ON COLUMN CLR.T_NOTE.NOTE_TXT IS
  'Note text [PII]';
COMMENT ON COLUMN CLR.T_NOTE.NOTE_TYPE_CD IS
  'Type';
COMMENT ON COLUMN CLR.T_NOTE.LAST_UPD_TS IS
  'Timestamp of last update';
COMMENT ON COLUMN CLR.T_NOTE.LAST_UPD_PGM IS
  'Program that last updated the row';
COMMENT ON COLUMN CLR.T_NOTE.LAST_UPD_USER IS
  'User or batch id that last updated the row';

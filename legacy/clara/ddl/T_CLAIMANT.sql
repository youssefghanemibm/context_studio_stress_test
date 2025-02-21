-- --------------------------------------------------------------------
-- CLR.T_CLAIMANT
-- Claimants and third parties
-- Area: COMMON    Copybook: CLRCLT01
-- --------------------------------------------------------------------
CREATE TABLE CLR.T_CLAIMANT
  ( CLAIMANT_ID                 CHAR(10)      NOT NULL
  , FAMILY_NAME                 VARCHAR(60)   NOT NULL
  , GIVEN_NAME                  VARCHAR(60)   NOT NULL
  , DOB                         DATE
  , NI_NO                       CHAR(13)
  , ADDR_LINE1                  VARCHAR(80)   NOT NULL
  , POSTCODE                    CHAR(8)       NOT NULL
  , PHONE_NO                    CHAR(16)
  , EMAIL_ADDR                  VARCHAR(120)
  , PARTY_ROLE_CD               CHAR(2)       NOT NULL
  , VULNERABLE_FLAG             CHAR(1)       NOT NULL
  , LAST_UPD_TS                 TIMESTAMP     NOT NULL WITH DEFAULT
  , LAST_UPD_PGM                CHAR(8)       NOT NULL
  , LAST_UPD_USER               CHAR(8)       NOT NULL
  , CONSTRAINT PK_T_CLAIMANT PRIMARY KEY (CLAIMANT_ID)
  )
  CCSID EBCDIC;

CREATE UNIQUE INDEX CLR.XCLAIMANT_PK
    ON CLR.T_CLAIMANT (CLAIMANT_ID);

COMMENT ON TABLE CLR.T_CLAIMANT IS
  'Claimants and third parties';
COMMENT ON COLUMN CLR.T_CLAIMANT.CLAIMANT_ID IS
  'Claimant identifier';
COMMENT ON COLUMN CLR.T_CLAIMANT.FAMILY_NAME IS
  'Family name [PII]';
COMMENT ON COLUMN CLR.T_CLAIMANT.GIVEN_NAME IS
  'Given name [PII]';
COMMENT ON COLUMN CLR.T_CLAIMANT.DOB IS
  'Date of birth [PII]';
COMMENT ON COLUMN CLR.T_CLAIMANT.NI_NO IS
  'UK National Insurance number or Nordic personal number (masked outside production) [PII]';
COMMENT ON COLUMN CLR.T_CLAIMANT.ADDR_LINE1 IS
  'Address line 1 [PII]';
COMMENT ON COLUMN CLR.T_CLAIMANT.POSTCODE IS
  'Postcode [PII]';
COMMENT ON COLUMN CLR.T_CLAIMANT.PHONE_NO IS
  'Contact phone [PII]';
COMMENT ON COLUMN CLR.T_CLAIMANT.EMAIL_ADDR IS
  'Contact email [PII]';
COMMENT ON COLUMN CLR.T_CLAIMANT.PARTY_ROLE_CD IS
  'PH policyholder, TP third party, WI witness';
COMMENT ON COLUMN CLR.T_CLAIMANT.VULNERABLE_FLAG IS
  'Customer vulnerability indicator';
COMMENT ON COLUMN CLR.T_CLAIMANT.LAST_UPD_TS IS
  'Timestamp of last update';
COMMENT ON COLUMN CLR.T_CLAIMANT.LAST_UPD_PGM IS
  'Program that last updated the row';
COMMENT ON COLUMN CLR.T_CLAIMANT.LAST_UPD_USER IS
  'User or batch id that last updated the row';

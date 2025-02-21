-- --------------------------------------------------------------------
-- CLR.T_CLAIM
-- Claim header - one row per claim
-- Area: COMMON    Copybook: CLRCLM01
-- --------------------------------------------------------------------
CREATE TABLE CLR.T_CLAIM
  ( CLAIM_ID                    CHAR(12)      NOT NULL
  , POLICY_NO                   CHAR(10)      NOT NULL
  , PRODUCT_CD                  CHAR(6)       NOT NULL
  , PERIL_CD                    CHAR(4)       NOT NULL
  , LOSS_DT                     DATE          NOT NULL
  , NOTIFIED_TS                 TIMESTAMP     NOT NULL
  , CHANNEL_CD                  CHAR(2)       NOT NULL
  , CLAIM_STATUS                CHAR(2)       NOT NULL
  , TIER_CD                     CHAR(1)       NOT NULL
  , REGION_CD                   CHAR(2)       NOT NULL
  , CURRENCY_CD                 CHAR(3)       NOT NULL
  , CLAIMANT_ID                 CHAR(10)      NOT NULL
  , HANDLER_USER_ID             CHAR(8)       NOT NULL
  , ASSESSOR_ID                 CHAR(8)
  , FRAUD_FLAG                  CHAR(1)       NOT NULL
  , RECOVERY_FLAG               CHAR(1)       NOT NULL
  , LOSS_DESC                   VARCHAR(500)  NOT NULL
  , LOSS_POSTCODE               CHAR(8)
  , CLOSED_DT                   DATE
  , LAST_UPD_TS                 TIMESTAMP     NOT NULL WITH DEFAULT
  , LAST_UPD_PGM                CHAR(8)       NOT NULL
  , LAST_UPD_USER               CHAR(8)       NOT NULL
  , CONSTRAINT PK_T_CLAIM PRIMARY KEY (CLAIM_ID)
  )
  CCSID EBCDIC;

CREATE UNIQUE INDEX CLR.XCLAIM_PK
    ON CLR.T_CLAIM (CLAIM_ID);

ALTER TABLE CLR.T_CLAIM
  ADD CONSTRAINT FK_CLAIM_1 FOREIGN KEY (CLAIMANT_ID)
      REFERENCES CLR.T_CLAIMANT (CLAIMANT_ID) ON DELETE RESTRICT;

COMMENT ON TABLE CLR.T_CLAIM IS
  'Claim header - one row per claim';
COMMENT ON COLUMN CLR.T_CLAIM.CLAIM_ID IS
  'Claim reference, region + year + 6-digit sequence (e.g. UK2025118204); shown in Claims Hub as CLM-UK-2025-118204';
COMMENT ON COLUMN CLR.T_CLAIM.POLICY_NO IS
  'Policy number from PALM';
COMMENT ON COLUMN CLR.T_CLAIM.PRODUCT_CD IS
  'Product code (e.g. MOTUK, HOMSE)';
COMMENT ON COLUMN CLR.T_CLAIM.PERIL_CD IS
  'Claim type / peril code (e.g. COL, EOW)';
COMMENT ON COLUMN CLR.T_CLAIM.LOSS_DT IS
  'Date of loss';
COMMENT ON COLUMN CLR.T_CLAIM.NOTIFIED_TS IS
  'First notice of loss timestamp';
COMMENT ON COLUMN CLR.T_CLAIM.CHANNEL_CD IS
  'FNOL channel (PH phone, WB portal, AP app, BR broker, TL telematics)';
COMMENT ON COLUMN CLR.T_CLAIM.CLAIM_STATUS IS
  'Claim status (OP open, CS closed-settled, CN closed-nil, RO reopened, RC in recovery)';
COMMENT ON COLUMN CLR.T_CLAIM.TIER_CD IS
  'Claim tier 1/2/3 (BR-TRI-003)';
COMMENT ON COLUMN CLR.T_CLAIM.REGION_CD IS
  'Region (UK, NO, SE, DK)';
COMMENT ON COLUMN CLR.T_CLAIM.CURRENCY_CD IS
  'Claim currency (GBP, NOK, SEK, DKK)';
COMMENT ON COLUMN CLR.T_CLAIM.CLAIMANT_ID IS
  'Primary claimant (CLR.T_CLAIMANT)';
COMMENT ON COLUMN CLR.T_CLAIM.HANDLER_USER_ID IS
  'Claims Handler user id';
COMMENT ON COLUMN CLR.T_CLAIM.ASSESSOR_ID IS
  'Assigned Claims Assessor (internal user id or vendor code)';
COMMENT ON COLUMN CLR.T_CLAIM.FRAUD_FLAG IS
  'Y when a fraud referral exists';
COMMENT ON COLUMN CLR.T_CLAIM.RECOVERY_FLAG IS
  'Y when recovery potential identified';
COMMENT ON COLUMN CLR.T_CLAIM.LOSS_DESC IS
  'Description of loss as notified [PII]';
COMMENT ON COLUMN CLR.T_CLAIM.LOSS_POSTCODE IS
  'Postcode / postnummer of loss location [PII]';
COMMENT ON COLUMN CLR.T_CLAIM.CLOSED_DT IS
  'Closure date';
COMMENT ON COLUMN CLR.T_CLAIM.LAST_UPD_TS IS
  'Timestamp of last update';
COMMENT ON COLUMN CLR.T_CLAIM.LAST_UPD_PGM IS
  'Program that last updated the row';
COMMENT ON COLUMN CLR.T_CLAIM.LAST_UPD_USER IS
  'User or batch id that last updated the row';

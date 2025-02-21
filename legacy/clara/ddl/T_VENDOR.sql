-- --------------------------------------------------------------------
-- CLR.T_VENDOR
-- Vendors (assessors, repairers, solicitors, salvage)
-- Area: COMMON    Copybook: VENREC01
-- --------------------------------------------------------------------
CREATE TABLE CLR.T_VENDOR
  ( VENDOR_CD                   CHAR(8)       NOT NULL
  , VENDOR_NAME                 VARCHAR(80)   NOT NULL
  , VENDOR_TYPE_CD              CHAR(2)       NOT NULL
  , PANEL_FROM_DT               DATE          NOT NULL
  , PANEL_TO_DT                 DATE
  , ARCHIVE_FLAG                CHAR(1)       NOT NULL
  , EXT_REF                     CHAR(20)
  , LAST_UPD_TS                 TIMESTAMP     NOT NULL WITH DEFAULT
  , LAST_UPD_PGM                CHAR(8)       NOT NULL
  , LAST_UPD_USER               CHAR(8)       NOT NULL
  , CONSTRAINT PK_T_VENDOR PRIMARY KEY (VENDOR_CD)
  )
  CCSID EBCDIC;

CREATE UNIQUE INDEX CLR.XVENDOR_PK
    ON CLR.T_VENDOR (VENDOR_CD);

COMMENT ON TABLE CLR.T_VENDOR IS
  'Vendors (assessors, repairers, solicitors, salvage)';
COMMENT ON COLUMN CLR.T_VENDOR.VENDOR_CD IS
  'Vendor code';
COMMENT ON COLUMN CLR.T_VENDOR.VENDOR_NAME IS
  'Name';
COMMENT ON COLUMN CLR.T_VENDOR.VENDOR_TYPE_CD IS
  'AS assessor, RP repairer, SL solicitor, SV salvage, IN investigator';
COMMENT ON COLUMN CLR.T_VENDOR.PANEL_FROM_DT IS
  'On panel from';
COMMENT ON COLUMN CLR.T_VENDOR.PANEL_TO_DT IS
  'On panel to';
COMMENT ON COLUMN CLR.T_VENDOR.ARCHIVE_FLAG IS
  'Y when eligible for archive (7-year retention)';
COMMENT ON COLUMN CLR.T_VENDOR.EXT_REF IS
  'External reference';
COMMENT ON COLUMN CLR.T_VENDOR.LAST_UPD_TS IS
  'Timestamp of last update';
COMMENT ON COLUMN CLR.T_VENDOR.LAST_UPD_PGM IS
  'Program that last updated the row';
COMMENT ON COLUMN CLR.T_VENDOR.LAST_UPD_USER IS
  'User or batch id that last updated the row';

"""CLARA legacy estate: DB2 tables, programs, copybooks, JCL jobs, BMS maps.

Key tables are hand-curated; the bulk of columns, reads and calls are generated
from seeded rng so that the estate is large but deterministic."""
from __future__ import annotations

from .common import rng

RESERVE_TABLE = "CLR.T_RESERVE"
# The deliberate, recorded set of programs that write CLR.T_RESERVE (8 programs).
RESERVE_WRITERS = ["CLRFN030", "CLRRS010", "CLRRS020", "CLRRS110", "CLRRS130", "CLRST040", "CLRRC050", "CLRGL090"]

# ------------------------------------------------------------------ columns

def col(spec: str) -> dict:
    """'NAME:TYPE:description[:pii][:null]'  TYPE e.g. CHAR(12) DECIMAL(13,2) DATE"""
    parts = spec.split(":")
    name, typ, desc = parts[0], parts[1], parts[2]
    flags = set(parts[3:])
    length, scale = None, None
    base = typ
    if "(" in typ:
        base, rest = typ.split("(")
        rest = rest.rstrip(")")
        if "," in rest:
            a, b = rest.split(",")
            length, scale = int(a), int(b)
        else:
            length = int(rest)
    else:
        length = {"DATE": 10, "TIMESTAMP": 26, "SMALLINT": 2, "INTEGER": 4, "BIGINT": 8}.get(base)
    out = {"name": name, "type": base, "length": length}
    if scale is not None:
        out["scale"] = scale
    out["nullable"] = "null" in flags
    out["description"] = desc
    out["pii"] = "pii" in flags
    return out


AUDIT_COLS = ["LAST_UPD_TS:TIMESTAMP:Timestamp of last update",
              "LAST_UPD_PGM:CHAR(8):Program that last updated the row",
              "LAST_UPD_USER:CHAR(8):User or batch id that last updated the row"]

EXTRA_VOCAB = [
    "SOURCE_SYS_CD:CHAR(4):Originating system code:null",
    "BRANCH_CD:CHAR(3):Branch code (UK, NO, SE, DK branch):null",
    "BATCH_RUN_ID:INTEGER:Batch run identifier:null",
    "VERSION_NO:SMALLINT:Optimistic locking version",
    "COMMENT_TXT:VARCHAR(254):Free-text comment:null",
    "EXT_REF:CHAR(20):External reference:null",
    "CREATED_TS:TIMESTAMP:Row creation timestamp",
    "ARCHIVE_FLAG:CHAR(1):Y when eligible for archive (7-year retention)",
]

# Hand-curated key tables -----------------------------------------------------
KEY_TABLES = {
    "CLR.T_CLAIM": ("COMMON", "Claim header – one row per claim", ["CLAIM_ID"], [
        "CLAIM_ID:CHAR(12):Claim reference, region + year + 6-digit sequence (e.g. UK2025118204); shown in Claims Hub as CLM-UK-2025-118204",
        "POLICY_NO:CHAR(10):Policy number from PALM",
        "PRODUCT_CD:CHAR(6):Product code (e.g. MOTUK, HOMSE)",
        "PERIL_CD:CHAR(4):Claim type / peril code (e.g. COL, EOW)",
        "LOSS_DT:DATE:Date of loss",
        "NOTIFIED_TS:TIMESTAMP:First notice of loss timestamp",
        "CHANNEL_CD:CHAR(2):FNOL channel (PH phone, WB portal, AP app, BR broker, TL telematics)",
        "CLAIM_STATUS:CHAR(2):Claim status (OP open, CS closed-settled, CN closed-nil, RO reopened, RC in recovery)",
        "TIER_CD:CHAR(1):Claim tier 1/2/3 (BR-TRI-003)",
        "REGION_CD:CHAR(2):Region (UK, NO, SE, DK)",
        "CURRENCY_CD:CHAR(3):Claim currency (GBP, NOK, SEK, DKK)",
        "CLAIMANT_ID:CHAR(10):Primary claimant (CLR.T_CLAIMANT)",
        "HANDLER_USER_ID:CHAR(8):Claims Handler user id",
        "ASSESSOR_ID:CHAR(8):Assigned Claims Assessor (internal user id or vendor code):null",
        "FRAUD_FLAG:CHAR(1):Y when a fraud referral exists",
        "RECOVERY_FLAG:CHAR(1):Y when recovery potential identified",
        "LOSS_DESC:VARCHAR(500):Description of loss as notified:pii",
        "LOSS_POSTCODE:CHAR(8):Postcode / postnummer of loss location:pii:null",
        "CLOSED_DT:DATE:Closure date:null",
    ] + AUDIT_COLS),
    "CLR.T_CLAIMANT": ("COMMON", "Claimants and third parties", ["CLAIMANT_ID"], [
        "CLAIMANT_ID:CHAR(10):Claimant identifier",
        "FAMILY_NAME:VARCHAR(60):Family name:pii",
        "GIVEN_NAME:VARCHAR(60):Given name:pii",
        "DOB:DATE:Date of birth:pii:null",
        "NI_NO:CHAR(13):UK National Insurance number or Nordic personal number (masked outside production):pii:null",
        "ADDR_LINE1:VARCHAR(80):Address line 1:pii",
        "POSTCODE:CHAR(8):Postcode:pii",
        "PHONE_NO:CHAR(16):Contact phone:pii:null",
        "EMAIL_ADDR:VARCHAR(120):Contact email:pii:null",
        "PARTY_ROLE_CD:CHAR(2):PH policyholder, TP third party, WI witness",
        "VULNERABLE_FLAG:CHAR(1):Customer vulnerability indicator",
    ] + AUDIT_COLS),
    "CLR.T_RESERVE": ("RESERVE", "Case reserves – one row per claim per reserve type", ["RSV_ID"], [
        "RSV_ID:BIGINT:Reserve identifier",
        "CLAIM_ID:CHAR(12):Claim reference (FK CLR.T_CLAIM)",
        "RSV_TYPE_CD:CHAR(2):Reserve type (ID indemnity, EX expense, LG legal)",
        "CURRENCY_CD:CHAR(3):Reserve currency (local currency for Nordic claims)",
        "RSV_INITIAL_AMT:DECIMAL(13,2):Initial reserve amount",
        "RSV_OUTSTANDING_AMT:DECIMAL(13,2):Current outstanding case reserve",
        "RSV_PAID_TO_DATE_AMT:DECIMAL(13,2):Paid to date against this reserve",
        "RSV_RECOVERY_EST_AMT:DECIMAL(13,2):Estimated recoveries netted from the reserve:null",
        "RSV_GBP_EQUIV_AMT:DECIMAL(13,2):GBP equivalent of the outstanding reserve",
        "RSV_STATUS:CHAR(1):O open, C closed",
        "RSV_AUTH_LEVEL:CHAR(2):Authority level that approved the last change (CH, TL, CM, CD, RC)",
        "RSV_SET_BY_USER:CHAR(8):User who last set the reserve",
        "RSV_NEXT_REVIEW_DT:DATE:Next scheduled reserve review (Tier-3 cadence BR-RSV-007):null",
        "RSV_INDEX_FACTOR:DECIMAL(7,5):Cumulative indexation factor (BI claims, BR-RSV-009):null",
        "RSV_LAST_REVAL_DT:DATE:Date of last currency revaluation:null",
    ] + AUDIT_COLS),
    "CLR.T_RESERVE_MOVEMENT": ("RESERVE", "Audit trail of reserve changes; source of CLX-IF-042", ["MOVE_ID"], [
        "MOVE_ID:BIGINT:Movement identifier",
        "RSV_ID:BIGINT:Reserve identifier (FK CLR.T_RESERVE)",
        "CLAIM_ID:CHAR(12):Claim reference",
        "MOVE_TS:TIMESTAMP:Movement timestamp",
        "MOVE_TYPE_CD:CHAR(2):IN initial, AD adjustment, IX indexation, RV review, ST settlement close, RC recovery",
        "MOVE_AMT:DECIMAL(13,2):Movement amount in reserve currency",
        "MOVE_GBP_AMT:DECIMAL(13,2):Movement amount in GBP",
        "REASON_CD:CHAR(4):Reason code",
        "USER_ID:CHAR(8):User or batch id",
        "PGM_ID:CHAR(8):Program that created the movement",
        "EXTRACTED_FLAG:CHAR(1):Y once extracted by CLRRS170 for CLX-IF-042",
        "EXTRACT_RUN_ID:INTEGER:CLX-IF-042 extract run id:null",
    ]),
    "CLR.T_FRAUD_REFERRAL": ("FRAUD", "Fraud referrals to SIU", ["REF_ID"], [
        "REF_ID:BIGINT:Referral identifier",
        "CLAIM_ID:CHAR(12):Claim reference",
        "REF_TS:TIMESTAMP:Referral timestamp",
        "REF_SCORE:SMALLINT:Sentinel score at referral (0-100)",
        "REF_THRESHOLD_APPLIED:SMALLINT:Threshold applied at referral (read from CLR.T_PARAM, except CLRFR040)",
        "REF_SOURCE_CD:CHAR(2):ON online (CLRFR030), BS batch sweep (CLRFR040), MN manual",
        "REF_REASON_CD:CHAR(4):Referral reason code",
        "RULE_ID:CHAR(10):Business rule applied (e.g. BR-FRD-031)",
        "TIER_CD:CHAR(1):Claim tier at referral",
        "SIU_CASE_ID:CHAR(10):SIU Case Manager case id:null",
        "REF_STATUS:CHAR(2):OP open, IN investigating, CL closed",
        "CUSTOMER_NOTICE_DUE_DT:DATE:Customer notice due date (referral date + 10 business days, BR-FRD-032):null",
        "CUSTOMER_NOTICE_DEFER_FLAG:CHAR(1):Y when notice deferred for tipping-off risk (BR-FRD-036)",
        "DEFER_APPROVED_BY:CHAR(8):Approver of deferral:null",
        "OUTCOME_CD:CHAR(2):NF no fraud, CF confirmed fraud, WD withdrawn:null",
        "OUTCOME_DT:DATE:Outcome date:null",
    ] + AUDIT_COLS),
    "CLR.T_FRAUD_NOTIFICATION": ("FRAUD", "Customer notices of fraud referral (NISA Circular 2026/04); created 2026-03-27", ["NOTICE_ID"], [
        "NOTICE_ID:BIGINT:Notice identifier",
        "REF_ID:BIGINT:Referral identifier",
        "CLAIM_ID:CHAR(12):Claim reference",
        "NOTICE_CHANNEL_CD:CHAR(2):LT letter, SM SMS, EM email",
        "NOTICE_DUE_DT:DATE:Due date",
        "NOTICE_SENT_TS:TIMESTAMP:Sent timestamp:null",
        "DEFERRED_UNTIL_DT:DATE:Deferred until (max 60 days):null",
        "TEMPLATE_CD:CHAR(8):Notify template code",
        "NOTIFY_MSG_ID:CHAR(36):Notify message id:null",
    ] + AUDIT_COLS),
    "CLR.T_PARAM": ("COMMON", "Business parameters with validity dates (read via CLRCM040)", ["PARAM_KEY", "VALID_FROM"], [
        "PARAM_KEY:CHAR(20):Parameter key",
        "VALID_FROM:DATE:Valid from",
        "VALID_TO:DATE:Valid to:null",
        "PARAM_VALUE:VARCHAR(40):Parameter value",
        "PARAM_DESC:VARCHAR(120):Description",
        "CHANGE_TICKET:CHAR(10):Change ticket (CHUB-nnn):null",
        "CHANGED_BY:CHAR(8):User",
    ]),
    "CLR.T_RECOVERY": ("RECOVER", "Recoveries (subrogation receipts, salvage proceeds)", ["RCV_ID"], [
        "RCV_ID:BIGINT:Recovery identifier",
        "CLAIM_ID:CHAR(12):Claim reference",
        "SUBRO_CASE_ID:CHAR(10):Subrogation case:null",
        "RCV_TYPE_CD:CHAR(2):SB subrogation, SV salvage, EX excess recovery",
        "RCV_EXPECTED_AMT:DECIMAL(13,2):Expected recovery",
        "RCV_RECEIVED_AMT:DECIMAL(13,2):Amount received",
        "RCV_WRITE_OFF_AMT:DECIMAL(13,2):Amount written off:null",
        "WRITE_OFF_APPROVED_BY:CHAR(8):Approver of write-off (BR-REC-011):null",
        "RCV_STATUS:CHAR(2):OP open, PT part-received, CL closed, WO written off",
        "CURRENCY_CD:CHAR(3):Currency",
    ] + AUDIT_COLS),
    "CLR.T_SUBROGATION_CASE": ("RECOVER", "Subrogation cases", ["SUBRO_CASE_ID"], [
        "SUBRO_CASE_ID:CHAR(10):Case identifier",
        "CLAIM_ID:CHAR(12):Claim reference",
        "TP_INSURER_NAME:VARCHAR(80):Third-party insurer name",
        "TP_REF:CHAR(20):Third-party reference:null",
        "DEMAND_AMT:DECIMAL(13,2):Demand amount",
        "DEMAND_DT:DATE:Demand date",
        "SOLICITOR_VENDOR_CD:CHAR(8):Solicitor (e.g. QUARRYHL):null",
        "LIMITATION_DT:DATE:Limitation date",
        "CASE_STATUS:CHAR(2):OP, LT litigation, ST settled, WO written off",
        "SUBTRAK_REF:CHAR(12):Subrogation Tracker reference:null",
    ] + AUDIT_COLS),
}

# Generated tables: name -> (area, description, key, domain columns)
GEN_TABLES = {
    "CLR.T_POLICY_SNAPSHOT": ("FNOL", "Policy snapshot copied from PALM at FNOL", ["POLICY_NO", "SNAPSHOT_DT"],
                              ["POLICY_NO:CHAR(10):Policy number", "SNAPSHOT_DT:DATE:Snapshot date", "PRODUCT_CD:CHAR(6):Product",
                               "COVER_START_DT:DATE:Cover start", "COVER_END_DT:DATE:Cover end", "EXCESS_AMT:DECIMAL(11,2):Standard excess",
                               "SUM_INSURED_AMT:DECIMAL(13,2):Sum insured:null", "PH_POSTCODE:CHAR(8):Policyholder postcode:pii"]),
    "CLR.T_FNOL_EVENT": ("FNOL", "Raw FNOL events by channel", ["FNOL_ID"],
                         ["FNOL_ID:BIGINT:FNOL event id", "CLAIM_ID:CHAR(12):Claim reference:null", "CHANNEL_CD:CHAR(2):Channel",
                          "RECEIVED_TS:TIMESTAMP:Received", "PAYLOAD_REF:CHAR(36):Evidence Vault reference:null",
                          "CALLER_PHONE:CHAR(16):Caller phone:pii:null", "ACK_SENT_TS:TIMESTAMP:Acknowledgement sent:null"]),
    "CLR.T_CLAIM_LINK": ("FRAUD", "Linked claims (shared parties, vehicles, bank accounts)", ["LINK_ID"],
                         ["LINK_ID:BIGINT:Link id", "CLAIM_ID_A:CHAR(12):Claim A", "CLAIM_ID_B:CHAR(12):Claim B",
                          "LINK_TYPE_CD:CHAR(2):PH phone, BA bank account, VH vehicle, AD address", "DETECTED_DT:DATE:Detected"]),
    "CLR.T_TRIAGE": ("TRIAGE", "Triage decisions", ["CLAIM_ID", "TRIAGE_SEQ"],
                     ["CLAIM_ID:CHAR(12):Claim reference", "TRIAGE_SEQ:SMALLINT:Sequence", "TRIAGE_TS:TIMESTAMP:Triage time",
                      "ROUTE_CD:CHAR(4):Routing outcome (FAST, HNDL, MCL)", "SCORE_AT_TRIAGE:SMALLINT:Sentinel score at triage",
                      "FASTTRACK_FLAG:CHAR(1):Fast-track eligible (BR-TRI-006)"]),
    "CLR.T_CLAIM_TIER": ("TRIAGE", "Tier history", ["CLAIM_ID", "TIER_FROM_TS"],
                         ["CLAIM_ID:CHAR(12):Claim reference", "TIER_FROM_TS:TIMESTAMP:Tier effective from", "TIER_CD:CHAR(1):Tier",
                          "TIER_REASON_CD:CHAR(4):Reason (AMT amount, INJ injury, LIT litigation, TLS total loss)",
                          "OVERRIDE_FLAG:CHAR(1):Manual override", "OVERRIDE_USER:CHAR(8):Override user:null"]),
    "CLR.T_ASSESSMENT": ("ASSESS", "Assessment records", ["ASSESS_ID"],
                         ["ASSESS_ID:BIGINT:Assessment id", "CLAIM_ID:CHAR(12):Claim reference", "ASSESS_TYPE_CD:CHAR(2):DK desk, SV site visit, VI video",
                          "COVER_DECISION_CD:CHAR(2):AC accepted, DC declined, PA partial", "ESTIMATE_AMT:DECIMAL(13,2):Assessed estimate",
                          "REPORT_RECEIVED_DT:DATE:Report received:null"]),
    "CLR.T_ASSESSOR_ASSIGNMENT": ("ASSESS", "Claims Assessor appointments (internal and vendor)", ["ASSIGN_ID"],
                                  ["ASSIGN_ID:BIGINT:Assignment id", "CLAIM_ID:CHAR(12):Claim reference", "ASSESSOR_ID:CHAR(8):Internal user or vendor code",
                                   "VENDOR_CD:CHAR(8):Vendor (BRACKFLD, NORRVIK, FELLGATE):null", "APPOINTED_TS:TIMESTAMP:Appointed",
                                   "SLA_DUE_DT:DATE:SLA due date"]),
    "CLR.T_INSPECTION": ("ASSESS", "Inspections", ["INSP_ID"],
                         ["INSP_ID:BIGINT:Inspection id", "CLAIM_ID:CHAR(12):Claim reference", "BOOKED_TS:TIMESTAMP:Booked for",
                          "COMPLETED_TS:TIMESTAMP:Completed:null", "INSP_ADDR:VARCHAR(120):Inspection address:pii"]),
    "CLR.T_ESTIMATE": ("ASSESS", "Repair and replacement estimates", ["EST_ID"],
                       ["EST_ID:BIGINT:Estimate id", "CLAIM_ID:CHAR(12):Claim reference", "EST_LINE_NO:SMALLINT:Line",
                        "EST_ITEM_DESC:VARCHAR(120):Item", "EST_AMT:DECIMAL(11,2):Amount", "REPAIRER_CD:CHAR(8):Repair network code:null"]),
    "CLR.T_RESERVE_HISTORY": ("RESERVE", "Archived reserve snapshots (month-end)", ["RSV_ID", "SNAPSHOT_DT"],
                              ["RSV_ID:BIGINT:Reserve id", "SNAPSHOT_DT:DATE:Snapshot date", "RSV_OUTSTANDING_AMT:DECIMAL(13,2):Outstanding",
                               "RSV_GBP_EQUIV_AMT:DECIMAL(13,2):GBP equivalent", "TIER_CD:CHAR(1):Tier"]),
    "CLR.T_RESERVE_AUTHORITY": ("RESERVE", "Reserve approvals above authority (BR-RSV-003)", ["AUTH_ID"],
                                ["AUTH_ID:BIGINT:Approval id", "RSV_ID:BIGINT:Reserve id", "REQUESTED_AMT:DECIMAL(13,2):Requested",
                                 "REQUIRED_LEVEL:CHAR(2):Required level", "APPROVER_USER:CHAR(8):Approver:null", "DECISION_CD:CHAR(2):AP, RJ, PD"]),
    "CLR.T_FRAUD_SCORE": ("FRAUD", "Sentinel scores", ["CLAIM_ID", "SCORE_TS"],
                          ["CLAIM_ID:CHAR(12):Claim reference", "SCORE_TS:TIMESTAMP:Scored at", "SCORE:SMALLINT:Score 0-100",
                           "MODEL_VERSION:CHAR(8):Model version (e.g. SNT-4.2)", "TOP_REASON_1:CHAR(6):Top reason code", "TOP_REASON_2:CHAR(6):Second reason:null"]),
    "CLR.T_SIU_CASE": ("FRAUD", "SIU case mirror", ["SIU_CASE_ID"],
                       ["SIU_CASE_ID:CHAR(10):Case id", "REF_ID:BIGINT:Referral", "INVESTIGATOR_USER:CHAR(8):Investigator",
                        "OPENED_DT:DATE:Opened", "CASE_STATUS:CHAR(2):Status", "PARTNER_VENDOR_CD:CHAR(8):Partner (GREYFOLD):null"]),
    "CLR.T_SETTLEMENT": ("SETTLE", "Settlements", ["SETTLE_ID"],
                         ["SETTLE_ID:BIGINT:Settlement id", "CLAIM_ID:CHAR(12):Claim reference", "OFFER_AMT:DECIMAL(13,2):Offer",
                          "OFFER_DT:DATE:Offer date", "ACCEPTED_DT:DATE:Accepted:null", "FINAL_FLAG:CHAR(1):Final settlement",
                          "EXCESS_APPLIED_AMT:DECIMAL(11,2):Excess deducted"]),
    "CLR.T_PAYMENT": ("SETTLE", "Payments", ["PAY_ID"],
                      ["PAY_ID:BIGINT:Payment id", "CLAIM_ID:CHAR(12):Claim reference", "PAYEE_ID:CHAR(10):Payee", "PAY_AMT:DECIMAL(13,2):Amount",
                       "CURRENCY_CD:CHAR(3):Currency", "PAY_STATUS:CHAR(2):RQ requested, SC screened, SN sent, CF confirmed, CX cancelled",
                       "AUTH_USER:CHAR(8):Authoriser", "SANCTIONS_RESULT:CHAR(2):WatchScreen result"]),
    "CLR.T_PAYMENT_BATCH": ("SETTLE", "Payment batches to CPG", ["BATCH_ID"],
                            ["BATCH_ID:INTEGER:Batch id", "BATCH_DT:DATE:Batch date", "PAY_COUNT:INTEGER:Payments", "TOTAL_AMT:DECIMAL(15,2):Total",
                             "CPG_FILE_NAME:CHAR(44):pain.001 file name", "CPG_ACK_TS:TIMESTAMP:Acknowledged:null"]),
    "CLR.T_PAYEE": ("SETTLE", "Payees", ["PAYEE_ID"],
                    ["PAYEE_ID:CHAR(10):Payee id", "PAYEE_NAME:VARCHAR(80):Payee name:pii", "IBAN:CHAR(34):IBAN or masked account:pii",
                     "SORT_CODE:CHAR(6):UK sort code:pii:null", "PAYEE_TYPE_CD:CHAR(2):PH, TP, VN vendor"]),
    "CLR.T_SALVAGE": ("RECOVER", "Salvage disposals", ["SALV_ID"],
                      ["SALV_ID:BIGINT:Salvage id", "CLAIM_ID:CHAR(12):Claim reference", "SALV_CATEGORY:CHAR(1):Category (A, B, S, N)",
                       "DISPOSAL_DT:DATE:Disposal date:null", "PROCEEDS_AMT:DECIMAL(11,2):Proceeds:null", "VENDOR_CD:CHAR(8):Salvage agent (SALVANTA)"]),
    "CLR.T_LITIGATION": ("RECOVER", "Litigation and solicitor instructions", ["LIT_ID"],
                         ["LIT_ID:BIGINT:Litigation id", "CLAIM_ID:CHAR(12):Claim reference", "SOLICITOR_VENDOR_CD:CHAR(8):Solicitor",
                          "INSTRUCTED_DT:DATE:Instructed", "COURT_REF:CHAR(20):Court reference:null", "LIT_STATUS:CHAR(2):Status"]),
    "CLR.T_GL_POSTING": ("GL", "GL postings (payments and recoveries)", ["POSTING_ID"],
                         ["POSTING_ID:BIGINT:Posting id", "GL_PERIOD:CHAR(6):Period YYYYMM", "ACCOUNT_CD:CHAR(10):GL account",
                          "DR_CR:CHAR(1):D or C", "AMOUNT_GBP:DECIMAL(15,2):Amount GBP", "SOURCE_PGM:CHAR(8):Source program"]),
    "CLR.T_GL_PERIOD": ("GL", "GL period control", ["GL_PERIOD"],
                        ["GL_PERIOD:CHAR(6):Period", "PERIOD_STATUS:CHAR(1):O open, C closed", "CLOSED_TS:TIMESTAMP:Closed:null",
                         "CLOSED_BY:CHAR(8):Closed by:null"]),
    "CLR.T_CURRENCY_RATE": ("GL", "Currency rates loaded from Group Ledger (CLX-IF-027)", ["CURRENCY_CD", "RATE_DT"],
                            ["CURRENCY_CD:CHAR(3):Currency", "RATE_DT:DATE:Rate date", "RATE_TO_GBP:DECIMAL(11,7):GBP per unit",
                             "RATE_TYPE_CD:CHAR(2):DY daily, ME month-end, YE year-end"]),
    "CLR.T_REINSURANCE_CESSION": ("GL", "Reinsurance cessions", ["CESSION_ID"],
                                  ["CESSION_ID:BIGINT:Cession id", "CLAIM_ID:CHAR(12):Claim reference", "TREATY_CD:CHAR(8):Treaty",
                                   "CEDED_RSV_AMT:DECIMAL(13,2):Ceded reserve", "CEDED_PAID_AMT:DECIMAL(13,2):Ceded paid", "REINSURER_CD:CHAR(8):Reinsurer"]),
    "CLR.T_REPORT_RUN": ("REPORT", "Report run log", ["RUN_ID"],
                         ["RUN_ID:INTEGER:Run id", "REPORT_CD:CHAR(8):Report code", "RUN_TS:TIMESTAMP:Run time",
                          "ROW_COUNT:INTEGER:Rows", "RUN_STATUS:CHAR(2):Status"]),
    "CLR.T_NISA_RETURN": ("REPORT", "NISA return staging", ["RETURN_CD", "PERIOD_CD"],
                          ["RETURN_CD:CHAR(6):Return (TP2, FR1, CT1)", "PERIOD_CD:CHAR(6):Period (e.g. 2026Q3)", "CELL_REF:CHAR(10):Return cell",
                           "CELL_VALUE:DECIMAL(17,2):Value", "SUBMITTED_DT:DATE:Submitted:null"]),
    "CLR.T_CODE_LOOKUP": ("COMMON", "Code lookup values", ["CODE_TYPE", "CODE_VALUE"],
                          ["CODE_TYPE:CHAR(8):Code type", "CODE_VALUE:CHAR(6):Value", "CODE_DESC_EN:VARCHAR(60):English description",
                           "CODE_DESC_LOCAL:VARCHAR(60):Local-language description:null", "ACTIVE_FLAG:CHAR(1):Active"]),
    "CLR.T_AUDIT": ("COMMON", "Audit trail", ["AUDIT_ID"],
                    ["AUDIT_ID:BIGINT:Audit id", "AUDIT_TS:TIMESTAMP:Time", "USER_ID:CHAR(8):User", "PGM_ID:CHAR(8):Program",
                     "TABLE_NAME:CHAR(18):Table", "KEY_VALUE:CHAR(30):Key", "ACTION_CD:CHAR(1):I, U, D"]),
    "CLR.T_USER": ("COMMON", "CLARA users and authority levels", ["USER_ID"],
                   ["USER_ID:CHAR(8):User id", "USER_NAME:VARCHAR(60):Name:pii", "TEAM_CD:CHAR(4):Team",
                    "RSV_AUTH_LEVEL:CHAR(2):Reserve authority level", "PAY_AUTH_LEVEL:CHAR(2):Payment authority level", "ACTIVE_FLAG:CHAR(1):Active"]),
    "CLR.T_NOTE": ("COMMON", "Claim notes", ["NOTE_ID"],
                   ["NOTE_ID:BIGINT:Note id", "CLAIM_ID:CHAR(12):Claim reference", "NOTE_TS:TIMESTAMP:Time", "NOTE_TXT:VARCHAR(2000):Note text:pii",
                    "NOTE_TYPE_CD:CHAR(2):Type"]),
    "CLR.T_DIARY": ("COMMON", "Diary and reminders (reserve reviews, limitation dates)", ["DIARY_ID"],
                    ["DIARY_ID:BIGINT:Diary id", "CLAIM_ID:CHAR(12):Claim reference", "DUE_DT:DATE:Due", "DIARY_TYPE_CD:CHAR(4):RREV review, LIMT limitation, CHAS chase",
                     "OWNER_USER:CHAR(8):Owner", "DONE_FLAG:CHAR(1):Done"]),
    "CLR.T_DOCUMENT_REF": ("COMMON", "Document references (DOCSTOR / Evidence Vault ids)", ["DOC_REF_ID"],
                           ["DOC_REF_ID:BIGINT:Reference id", "CLAIM_ID:CHAR(12):Claim reference", "VAULT_OBJECT_ID:CHAR(36):Evidence Vault object id",
                            "DOC_TYPE_CD:CHAR(4):Type (PHOT, LETR, RPRT)", "RECEIVED_TS:TIMESTAMP:Received"]),
    "CLR.T_VENDOR": ("COMMON", "Vendors (assessors, repairers, solicitors, salvage)", ["VENDOR_CD"],
                     ["VENDOR_CD:CHAR(8):Vendor code", "VENDOR_NAME:VARCHAR(80):Name", "VENDOR_TYPE_CD:CHAR(2):AS assessor, RP repairer, SL solicitor, SV salvage, IN investigator",
                      "PANEL_FROM_DT:DATE:On panel from", "PANEL_TO_DT:DATE:On panel to:null"]),
    "CLR.T_VENDOR_INVOICE": ("SETTLE", "Vendor invoices", ["INVOICE_ID"],
                             ["INVOICE_ID:BIGINT:Invoice id", "VENDOR_CD:CHAR(8):Vendor", "CLAIM_ID:CHAR(12):Claim reference",
                              "INVOICE_AMT:DECIMAL(11,2):Amount", "FEE_TYPE_CD:CHAR(2):DK desk, SV site visit, HR hourly", "MATCHED_FLAG:CHAR(1):Matched"]),
    "CLR.T_INTERFACE_LOG": ("COMMON", "Interface run log", ["IF_RUN_ID"],
                            ["IF_RUN_ID:INTEGER:Run id", "INTERFACE_ID:CHAR(10):Interface (e.g. CLX-IF-042)", "RUN_TS:TIMESTAMP:Run time",
                             "RECORD_COUNT:INTEGER:Records", "HASH_TOTAL:DECIMAL(17,2):Hash total", "RUN_STATUS:CHAR(2):OK, ER, RR"]),
}

T_PARAM_ROWS = [
    {"key": "FRD_REFER_THRESH", "value": "75", "valid_from": "2019-01-01", "valid_to": "2023-03-31", "ticket": None, "rule": "BR-FRD-012@v1"},
    {"key": "FRD_REFER_THRESH", "value": "70", "valid_from": "2023-04-01", "valid_to": "2026-03-31", "ticket": None, "rule": "BR-FRD-012@v2"},
    {"key": "FRD_REFER_THRESH", "value": "65", "valid_from": "2026-04-01", "valid_to": None, "ticket": "CHUB-205", "rule": "BR-FRD-031@v1"},
    {"key": "FRD_REFER_T3_THRESH", "value": "60", "valid_from": "2026-10-01", "valid_to": None, "ticket": "CHUB-395", "rule": "BR-FRD-031@v2"},
    {"key": "FRD_AUTODECL_THRESH", "value": "90", "valid_from": "2023-01-01", "valid_to": "2026-03-31", "ticket": "CHUB-207", "rule": "BR-FRD-019@v2"},
    {"key": "RSV_T3_REVIEW_DAYS", "value": "30", "valid_from": "2015-01-01", "valid_to": "2023-12-31", "ticket": None, "rule": "BR-RSV-007@v1"},
    {"key": "RSV_T3_REVIEW_DAYS", "value": "21", "valid_from": "2024-01-01", "valid_to": "2026-06-30", "ticket": None, "rule": "BR-RSV-007@v2"},
    {"key": "RSV_T3_REVIEW_DAYS", "value": "14", "valid_from": "2026-07-01", "valid_to": None, "ticket": "CHUB-318", "rule": "BR-RSV-007@v3"},
    {"key": "RSV_LLNT_GBP", "value": "250000", "valid_from": "2024-01-01", "valid_to": None, "ticket": None, "rule": "BR-RSV-011@v2"},
    {"key": "RSV_BI_INDEX_PCT", "value": "3.1", "valid_from": "2026-01-01", "valid_to": None, "ticket": None, "rule": "BR-RSV-009@v3"},
    {"key": "TRI_T3_MIN_GBP", "value": "50000", "valid_from": "2025-01-01", "valid_to": None, "ticket": None, "rule": "BR-TRI-003@v3"},
    {"key": "TRI_FASTTRACK_CAP", "value": "2000", "valid_from": "2026-07-01", "valid_to": None, "ticket": None, "rule": "BR-TRI-006@v3"},
    {"key": "FRD_NOTICE_BUS_DAYS", "value": "10", "valid_from": "2026-04-01", "valid_to": None, "ticket": "CHUB-206", "rule": "BR-FRD-032@v2"},
    {"key": "REC_PURSUE_MIN_GBP", "value": "1000", "valid_from": "2025-09-01", "valid_to": None, "ticket": None, "rule": "BR-REC-003@v3"},
]

# ------------------------------------------------------------------ programs
AREAS = {
    "FN": "FNOL", "TR": "TRIAGE", "AS": "ASSESS", "RS": "RESERVE", "FR": "FRAUD",
    "ST": "SETTLE", "RC": "RECOVER", "CM": "COMMON", "GL": "GL", "RP": "REPORT",
}
AREA_SERVICE = {
    "FNOL": "fnol-intake-svc", "TRIAGE": "triage-svc", "ASSESS": "assessment-svc", "RESERVE": "reserve-engine",
    "FRAUD": "fraud-referral-svc", "SETTLE": "settlement-svc", "RECOVER": "recovery-svc", "COMMON": None,
    "GL": "gl-posting-svc", "REPORT": "reporting-feed-svc",
}
AREA_TABLES = {
    "FNOL": ["CLR.T_CLAIM", "CLR.T_CLAIMANT", "CLR.T_POLICY_SNAPSHOT", "CLR.T_FNOL_EVENT"],
    "TRIAGE": ["CLR.T_CLAIM", "CLR.T_TRIAGE", "CLR.T_CLAIM_TIER", "CLR.T_FRAUD_SCORE"],
    "ASSESS": ["CLR.T_CLAIM", "CLR.T_ASSESSMENT", "CLR.T_ASSESSOR_ASSIGNMENT", "CLR.T_INSPECTION", "CLR.T_ESTIMATE", "CLR.T_VENDOR"],
    "RESERVE": ["CLR.T_CLAIM", "CLR.T_RESERVE", "CLR.T_RESERVE_MOVEMENT", "CLR.T_RESERVE_HISTORY", "CLR.T_RESERVE_AUTHORITY", "CLR.T_CLAIM_TIER"],
    "FRAUD": ["CLR.T_CLAIM", "CLR.T_FRAUD_SCORE", "CLR.T_FRAUD_REFERRAL", "CLR.T_CLAIM_LINK", "CLR.T_SIU_CASE", "CLR.T_FRAUD_NOTIFICATION"],
    "SETTLE": ["CLR.T_CLAIM", "CLR.T_SETTLEMENT", "CLR.T_PAYMENT", "CLR.T_PAYMENT_BATCH", "CLR.T_PAYEE", "CLR.T_VENDOR_INVOICE"],
    "RECOVER": ["CLR.T_CLAIM", "CLR.T_RECOVERY", "CLR.T_SUBROGATION_CASE", "CLR.T_SALVAGE", "CLR.T_LITIGATION"],
    "COMMON": ["CLR.T_CODE_LOOKUP", "CLR.T_USER"],
    "GL": ["CLR.T_GL_POSTING", "CLR.T_GL_PERIOD", "CLR.T_CURRENCY_RATE", "CLR.T_PAYMENT", "CLR.T_RECOVERY"],
    "REPORT": ["CLR.T_CLAIM", "CLR.T_REPORT_RUN", "CLR.T_NISA_RETURN"],
}

O, B = "online", "batch"

# (num, type, description, writes, extras)
PROGRAM_SPECS = {
    "FN": [
        (10, O, "FNOL capture – main entry for telephone and portal hand-off", ["CLR.T_FNOL_EVENT"], {"calls": ["CLRFN015", "CLRFN060", "CLRFN030"]}),
        (15, O, "FNOL policy lookup against PALM snapshot and Vehicle Data Service", [], {}),
        (20, O, "FNOL claimant and third-party details", ["CLR.T_CLAIMANT"], {}),
        (30, O, "Create claim record and default reserve (BR-FNOL-005)", ["CLR.T_CLAIM", "CLR.T_RESERVE", "CLR.T_RESERVE_MOVEMENT"],
         {"reads": ["CLR.T_POLICY_SNAPSHOT", "CLR.T_PARAM", "CLR.T_CODE_LOOKUP"], "calls": ["CLRCM040", "CLRCM030", "CLRCM020"],
          "replaced_by": "reserve-engine", "notes": "Writes the default reserve at FNOL; often forgotten in reserve-writer lists."}),
        (40, B, "Overnight portal FNOL import (MyCorvane Claims, CLX-IF-001 backlog)", ["CLR.T_FNOL_EVENT"], {}),
        (50, B, "Evidence Intake Gateway photo and telematics reference import", ["CLR.T_DOCUMENT_REF"], {}),
        (60, O, "Duplicate claim check (same policy, date of loss ±3 days)", [], {}),
        (70, B, "FNOL acknowledgement extract to Notify (CLX-IF-006)", ["CLR.T_FNOL_EVENT"], {"replaced_by": "notification-svc"}),
        (80, B, "Late notification report (> 30 days after loss)", [], {}),
        (90, O, "FNOL amend and reopen", ["CLR.T_CLAIM"], {"replaced_by": "claim-core-svc"}),
        (100, B, "PALM policy snapshot refresh (CLX-IF-003)", ["CLR.T_POLICY_SNAPSHOT"], {}),
        (110, O, "Broker FNOL bulk entry", ["CLR.T_FNOL_EVENT"], {}),
        (120, B, "FNOL MI daily counts", [], {"replaced_by": None}),
        (130, O, "Nordic FNOL entry (Norwegian, Swedish and Danish fields)", ["CLR.T_FNOL_EVENT"], {}),
    ],
    "TR": [
        (10, O, "Triage workbench", ["CLR.T_TRIAGE"], {}),
        (20, B, "Tier classification batch – re-tier on estimate change (BR-TRI-003)", ["CLR.T_CLAIM_TIER", "CLR.T_CLAIM"],
         {"reads": ["CLR.T_RESERVE", "CLR.T_PARAM", "CLR.T_ESTIMATE"], "calls": ["CLRCM040"]}),
        (30, O, "Tier override with reason", ["CLR.T_CLAIM_TIER"], {}),
        (40, B, "Fraud pre-screen request to Sentinel (batch)", [], {}),
        (50, O, "Routing to team queue", ["CLR.T_TRIAGE"], {}),
        (60, B, "Fast-track eligibility sweep (BR-TRI-006)", ["CLR.T_TRIAGE"], {"reads": ["CLR.T_PARAM", "CLR.T_FRAUD_SCORE"], "calls": ["CLRCM040"]}),
        (70, O, "Triage notes and diary", [], {"calls": ["CLRCM080", "CLRCM090"]}),
        (80, B, "Triage SLA breach report", [], {"replaced_by": None}),
        (90, O, "Major loss alert for Tier-3 claims", [], {}),
        (100, B, "Re-triage after policy change", ["CLR.T_CLAIM_TIER"], {}),
    ],
    "AS": [
        (10, O, "Assessment workbench", ["CLR.T_ASSESSMENT"], {}),
        (20, O, "Claims Assessor appointment (internal or vendor)", ["CLR.T_ASSESSOR_ASSIGNMENT"], {}),
        (30, B, "Assessor Portal instruction export (CLX-IF-013)", [], {}),
        (40, B, "Assessor report import from Assessor Portal (CLX-IF-014)", ["CLR.T_ASSESSMENT"], {}),
        (50, O, "Inspection booking", ["CLR.T_INSPECTION"], {}),
        (60, O, "Estimate entry and validation", ["CLR.T_ESTIMATE"], {}),
        (70, B, "Vendor invoice matching (assessor fees, CLX-IF-016)", ["CLR.T_VENDOR_INVOICE"], {"replaced_by": "payment-orchestrator"}),
        (80, O, "Coverage decision", ["CLR.T_ASSESSMENT"], {}),
        (90, B, "Desk assessment queue builder (BR-ASM-008)", [], {}),
        (100, B, "Assessment SLA report", [], {"replaced_by": None}),
        (110, O, "Nordic takst (assessment) entry", ["CLR.T_ASSESSMENT"], {}),
        (120, B, "Repair network job export (Thistlecombe, Vardholm, CLX-IF-015)", [], {}),
    ],
    "RS": [
        (10, O, "Initial reserve set", ["CLR.T_RESERVE", "CLR.T_RESERVE_MOVEMENT"],
         {"reads": ["CLR.T_CLAIM", "CLR.T_PARAM", "CLR.T_CURRENCY_RATE"], "calls": ["CLRRS015", "CLRCM030", "CLRCM040", "CLRCM020"]}),
        (15, O, "Reserve authority check (BR-RSV-003) – called subprogram", [], {"reads": ["CLR.T_USER", "CLR.T_PARAM"], "subprogram": True}),
        (20, O, "Reserve adjustment", ["CLR.T_RESERVE", "CLR.T_RESERVE_MOVEMENT"],
         {"reads": ["CLR.T_CLAIM", "CLR.T_RESERVE_AUTHORITY", "CLR.T_CURRENCY_RATE"], "calls": ["CLRRS015", "CLRCM030", "CLRCM020", "CLRRS040"]}),
        (30, O, "Reserve enquiry and history", [], {"reads": ["CLR.T_RESERVE", "CLR.T_RESERVE_MOVEMENT", "CLR.T_RESERVE_HISTORY"]}),
        (40, O, "Reserve approval queue (above authority)", ["CLR.T_RESERVE_AUTHORITY"], {"reads": ["CLR.T_RESERVE"]}),
        (110, B, "Tier-3 reserve review scheduler and revaluation (BR-RSV-007)", ["CLR.T_RESERVE", "CLR.T_RESERVE_MOVEMENT", "CLR.T_DIARY"],
         {"reads": ["CLR.T_CLAIM_TIER", "CLR.T_PARAM"], "calls": ["CLRCM040", "CLRCM010", "CLRCM090"]}),
        (120, B, "Reserve review overdue report", [], {"reads": ["CLR.T_RESERVE", "CLR.T_DIARY"]}),
        (130, B, "Monthly reserve indexation for bodily-injury claims (BR-RSV-009)", ["CLR.T_RESERVE", "CLR.T_RESERVE_MOVEMENT"],
         {"reads": ["CLR.T_CLAIM", "CLR.T_PARAM"], "calls": ["CLRCM040", "CLRCM020"]}),
        (140, B, "Reserve history archiver (month-end snapshots)", ["CLR.T_RESERVE_HISTORY"], {"reads": ["CLR.T_RESERVE"]}),
        (150, B, "Reserve movement correction utility", ["CLR.T_RESERVE_MOVEMENT"], {"reads": ["CLR.T_RESERVE"],
                                                                                 "notes": "Writes movements only; does NOT update CLR.T_RESERVE."}),
        (160, B, "Large loss notification extract to ReCede (CLX-IF-031, BR-RSV-011)", [], {"reads": ["CLR.T_RESERVE_MOVEMENT", "CLR.T_PARAM"],
                                                                                            "calls": ["CLRCM040", "CLRCM110"]}),
        (170, B, "Daily reserve movement extract (CLX-IF-042)", ["CLR.T_RESERVE_MOVEMENT", "CLR.T_INTERFACE_LOG"],
         {"reads": ["CLR.T_RESERVE_MOVEMENT", "CLR.T_CLAIM"], "calls": ["CLRCM110"], "copybooks_extra": ["RSVMOVE"],
          "notes": "Sets EXTRACTED_FLAG on CLR.T_RESERVE_MOVEMENT; puts RSVMOVE records to queue CLR.RSVMOVE.OUT."}),
        (180, B, "Reserve snapshot for month-end (CDW)", [], {"reads": ["CLR.T_RESERVE", "CLR.T_RESERVE_HISTORY"]}),
        (190, B, "Reserve adequacy MI", [], {"reads": ["CLR.T_RESERVE", "CLR.T_RESERVE_MOVEMENT"], "replaced_by": None}),
        (200, O, "Reserve type maintenance", ["CLR.T_CODE_LOOKUP"], {}),
        (210, B, "Reserve parallel-run reconciliation against reserve-engine (2026-03-02 to 2026-08-28)", ["CLR.T_INTERFACE_LOG"],
         {"reads": ["CLR.T_RESERVE", "CLR.T_RESERVE_MOVEMENT"], "replaced_by": None, "status": "retired", "since": "2026-02-27",
          "notes": "Removed from schedule after the parallel run ended on 2026-08-28."}),
    ],
    "FR": [
        (10, O, "Fraud indicators entry", ["CLR.T_FRAUD_SCORE"], {}),
        (20, O, "Sentinel score request (online, CLX-IF-008)", ["CLR.T_FRAUD_SCORE"],
         {"renamed_from": ("FNETCAL1", "2025-03-01"), "copybooks_extra": ["SENTREQ1", "SENTRSP1"],
          "notes": "Endpoint switched to sentinel.corvane.internal under CHUB-119 after INC-2025-0233."}),
        (30, O, "Fraud referral creation – online (threshold read from CLR.T_PARAM)", ["CLR.T_FRAUD_REFERRAL"],
         {"renamed_from": ("FNETREF1", "2025-03-01"), "reads": ["CLR.T_FRAUD_SCORE", "CLR.T_PARAM", "CLR.T_CLAIM_TIER"],
          "calls": ["CLRCM040", "CLRCM110", "CLRCM020"]}),
        (40, B, "Fraud referral batch sweep (nightly)", ["CLR.T_FRAUD_REFERRAL"],
         {"reads": ["CLR.T_FRAUD_SCORE", "CLR.T_CLAIM"], "calls": ["CLRCM020"],
          "hardcoded": [{"name": "WS-REFER-THRESHOLD", "pic": "9(3)", "value": "070", "meaning": "referral threshold (pre-2026 value)",
                         "should_be": "65 from CLR.T_PARAM FRD_REFER_THRESH (60 for Tier-3 from 2026-10-01)",
                         "fixed_in_variant": "c", "fix_ticket": "CHUB-298", "fix_date": "2026-11-12"}],
          "notes": "CODE DRIFT: still hard-codes 070 in variant a; fixed by the follow-up commit (variant c)."}),
        (50, O, "SIU outcome update", ["CLR.T_FRAUD_REFERRAL", "CLR.T_SIU_CASE"], {}),
        (60, B, "Customer referral notice scheduler (NISA Circular 2026/04)", ["CLR.T_FRAUD_NOTIFICATION", "CLR.T_FRAUD_REFERRAL"],
         {"reads": ["CLR.T_PARAM"], "calls": ["CLRCM010", "CLRCM040"], "since": "2026-03-27", "replaced_by": "notification-svc"}),
        (70, B, "SIU Case Manager export (CLX-IF-011 batch catch-up)", [], {}),
        (80, B, "Linked claims detection (BR-FRD-005)", ["CLR.T_CLAIM_LINK"], {}),
        (90, B, "NISA-FR1 quarterly fraud referral return extract (CLX-IF-033)", ["CLR.T_NISA_RETURN"],
         {"since": "2026-06-26", "replaced_by": "reporting-feed-svc"}),
        (100, O, "Fraud referral enquiry", [], {"reads": ["CLR.T_FRAUD_REFERRAL", "CLR.T_FRAUD_NOTIFICATION"]}),
        (110, B, "Sentinel score batch refresh (CLX-IF-009/010)", ["CLR.T_FRAUD_SCORE"], {}),
        (120, O, "Customer-notice deferral approval (tipping-off, BR-FRD-036)", ["CLR.T_FRAUD_NOTIFICATION"], {"since": "2026-03-27"}),
        (130, B, "Fraud MI weekly", [], {"replaced_by": None}),
        (140, B, "Auto-decline sweep (score ≥ 90) – DISABLED 2026-04-01 (BR-FRD-019 withdrawn)", ["CLR.T_CLAIM"],
         {"status": "disabled", "replaced_by": None, "notes": "Removed from job CLRNFR99 schedule on 2026-04-01 (CHUB-207)."}),
    ],
    "ST": [
        (10, O, "Settlement offer", ["CLR.T_SETTLEMENT"], {"reads": ["CLR.T_RESERVE"]}),
        (20, O, "Payment request (BR-STL-002 authority)", ["CLR.T_PAYMENT"], {"replaced_by": "payment-orchestrator"}),
        (30, B, "Payment batch build to CPG (CLX-IF-019)", ["CLR.T_PAYMENT_BATCH", "CLR.T_PAYMENT"], {"replaced_by": "payment-orchestrator"}),
        (40, B, "Settlement finalisation and reserve close-down (BR-RSV-014)", ["CLR.T_SETTLEMENT", "CLR.T_RESERVE", "CLR.T_RESERVE_MOVEMENT", "CLR.T_CLAIM"],
         {"reads": ["CLR.T_PAYMENT"], "calls": ["CLRCM020", "CLRCM010"],
          "notes": "Sets RSV_OUTSTANDING_AMT to zero on final settlement."}),
        (50, B, "Payment confirmation import from CPG (CLX-IF-020)", ["CLR.T_PAYMENT"], {"replaced_by": "payment-orchestrator"}),
        (60, O, "Payee maintenance", ["CLR.T_PAYEE"], {"replaced_by": "payment-orchestrator"}),
        (70, B, "Sanctions screening request to WatchScreen (CLX-IF-017)", ["CLR.T_PAYMENT"], {"replaced_by": "payment-orchestrator"}),
        (80, B, "Fast-track straight-through settlement (BR-STL-009)", ["CLR.T_SETTLEMENT", "CLR.T_PAYMENT"], {"reads": ["CLR.T_TRIAGE", "CLR.T_PARAM"],
                                                                                                          "calls": ["CLRCM040"]}),
        (90, O, "Payment cancellation and stop", ["CLR.T_PAYMENT"], {"replaced_by": "payment-orchestrator"}),
        (100, B, "Late payment interest calculation (BR-STL-014)", ["CLR.T_PAYMENT"], {}),
        (110, B, "Vendor invoice payment run", ["CLR.T_PAYMENT", "CLR.T_VENDOR_INVOICE"], {"replaced_by": "payment-orchestrator"}),
        (120, O, "Settlement enquiry", [], {}),
        (130, B, "Payment MI", [], {"replaced_by": None}),
        (140, B, "Nordic payment file NOK/SEK/DKK to CPG (CLX-IF-021)", ["CLR.T_PAYMENT_BATCH"], {"replaced_by": "payment-orchestrator"}),
    ],
    "RC": [
        (10, O, "Recovery potential assessment", ["CLR.T_CLAIM"], {"renamed_from": ("SUBRO010", "2019-04-01")}),
        (20, O, "Subrogation case open and demand (BR-REC-003)", ["CLR.T_SUBROGATION_CASE"], {"reads": ["CLR.T_PARAM"], "calls": ["CLRCM040"]}),
        (30, B, "Subrogation demand letter extract to Notify (CLX-IF-026)", [], {"replaced_by": "notification-svc"}),
        (40, B, "SUBTRAK synchronisation (CLX-IF-022)", ["CLR.T_SUBROGATION_CASE"], {}),
        (50, B, "Recovery receipt posting – nets recoveries from the case reserve", ["CLR.T_RECOVERY", "CLR.T_RESERVE", "CLR.T_RESERVE_MOVEMENT"],
         {"reads": ["CLR.T_SUBROGATION_CASE"], "calls": ["CLRCM020", "CLRCM030"],
          "notes": "Updates RSV_RECOVERY_EST_AMT and RSV_OUTSTANDING_AMT on CLR.T_RESERVE."}),
        (60, O, "Solicitor instruction (Quarryhill Solicitors, CLX-IF-025)", ["CLR.T_LITIGATION"], {}),
        (70, B, "Salvage disposal import (Salvanta, CLX-IF-024)", ["CLR.T_SALVAGE"], {}),
        (80, B, "Limitation diary sweep (BR-REC-009)", ["CLR.T_DIARY"], {}),
        (90, O, "Recovery write-off (BR-REC-011)", ["CLR.T_RECOVERY"], {}),
        (100, B, "Recovery MI monthly", [], {"replaced_by": None}),
    ],
    "CM": [
        (10, O, "Date and business-day utility (UK, NO, SE, DK calendars)", [], {"subprogram": True}),
        (20, O, "Audit trail writer", ["CLR.T_AUDIT"], {"subprogram": True}),
        (30, O, "Currency conversion (reads CLR.T_CURRENCY_RATE)", [], {"reads": ["CLR.T_CURRENCY_RATE"], "subprogram": True}),
        (40, O, "Parameter reader (reads CLR.T_PARAM with validity dates)", [], {"reads": ["CLR.T_PARAM"], "subprogram": True}),
        (50, O, "Error handler and abend formatter", [], {"subprogram": True}),
        (60, O, "Code lookup", [], {"reads": ["CLR.T_CODE_LOOKUP"], "subprogram": True}),
        (70, O, "User authority check", [], {"reads": ["CLR.T_USER"], "subprogram": True}),
        (80, O, "Notes writer", ["CLR.T_NOTE"], {"subprogram": True}),
        (90, O, "Diary writer", ["CLR.T_DIARY"], {"subprogram": True}),
        (100, O, "Document reference writer (DOCSTOR / Evidence Vault)", ["CLR.T_DOCUMENT_REF"], {"subprogram": True, "replaced_by": "document-svc"}),
        (110, O, "MQ put wrapper", [], {"subprogram": True}),
        (120, O, "MQ get wrapper", [], {"subprogram": True}),
        (130, B, "Interface log housekeeping", ["CLR.T_INTERFACE_LOG"], {}),
        (140, B, "Archive and purge of claims closed more than 7 years (BR-GEN-004)", ["CLR.T_CLAIM", "CLR.T_NOTE", "CLR.T_DOCUMENT_REF"], {}),
    ],
    "GL": [
        (10, B, "Daily GL posting extract – payments (CLX-IF-028)", ["CLR.T_GL_POSTING"], {}),
        (20, B, "GL period control", ["CLR.T_GL_PERIOD"], {}),
        (30, B, "Currency rate load from Group Ledger (CLX-IF-027)", ["CLR.T_CURRENCY_RATE"], {"replaced_by": None}),
        (40, B, "Reinsurance cession calculation", ["CLR.T_REINSURANCE_CESSION"], {"reads": ["CLR.T_RESERVE", "CLR.T_PAYMENT"], "replaced_by": None}),
        (50, B, "Month-end accruals", ["CLR.T_GL_POSTING"], {"reads": ["CLR.T_RESERVE"]}),
        (60, B, "GL reconciliation report", [], {}),
        (70, B, "Recovery income posting (CLX-IF-029)", ["CLR.T_GL_POSTING"], {}),
        (90, B, "Year-end reserve currency revaluation (Nordic reserves to GBP)", ["CLR.T_RESERVE"],
         {"reads": ["CLR.T_CURRENCY_RATE", "CLR.T_GL_PERIOD"], "calls": ["CLRCM030"], "calls_exact": True, "renamed_from": ("YEREVAL1", "2021-01-01"),
          "replaced_by": "reserve-engine",
          "notes": "Updates RSV_GBP_EQUIV_AMT and RSV_LAST_REVAL_DT on CLR.T_RESERVE WITHOUT writing CLR.T_RESERVE_MOVEMENT "
                   "(internal audit finding IA-25-07). Omitted from the data dictionary writer list."}),
    ],
    "RP": [
        (10, B, "Daily claims MI extract to CDW (CLX-IF-030)", ["CLR.T_REPORT_RUN"], {"reads": ["CLR.T_CLAIM", "CLR.T_CLAIM_TIER", "CLR.T_RESERVE"]}),
        (20, B, "Reserve report – outstanding by product", ["CLR.T_REPORT_RUN"], {"reads": ["CLR.T_RESERVE", "CLR.T_CLAIM"], "replaced_by": None}),
        (30, B, "NISA-TP2 data extract", ["CLR.T_NISA_RETURN"], {"reads": ["CLR.T_RESERVE", "CLR.T_RESERVE_HISTORY"]}),
        (40, B, "NISA-CT1 claims timeliness extract (CLX-IF-032)", ["CLR.T_NISA_RETURN"], {}),
        (50, B, "Assessor performance report", ["CLR.T_REPORT_RUN"], {"reads": ["CLR.T_ASSESSOR_ASSIGNMENT"], "replaced_by": None}),
        (60, B, "Fraud referral MI (NISA-FR1 support)", ["CLR.T_REPORT_RUN"], {"reads": ["CLR.T_FRAUD_REFERRAL"]}),
        (70, B, "Recovery MI", ["CLR.T_REPORT_RUN"], {"reads": ["CLR.T_RECOVERY"], "replaced_by": None}),
        (80, B, "Ad-hoc report driver", ["CLR.T_REPORT_RUN"], {"replaced_by": None}),
        (90, B, "Executive dashboard extract", ["CLR.T_REPORT_RUN"], {"replaced_by": None}),
        (100, B, "Data quality exceptions report", ["CLR.T_REPORT_RUN"], {"replaced_by": None}),
    ],
}

PROGRAM_OWNERS = {"RS": "P023", "FR": "P024", "ST": "P024", "GL": "P023", "CM": "P025", "RP": "P025",
                  "FN": "P024", "TR": "P023", "AS": "P024", "RC": "P023"}

# table -> copybook name
TABLE_COPYBOOK = {
    "CLR.T_CLAIM": "CLRCLM01", "CLR.T_CLAIMANT": "CLRCLT01", "CLR.T_POLICY_SNAPSHOT": "CLRPOL01", "CLR.T_FNOL_EVENT": "CLRFNL01",
    "CLR.T_CLAIM_LINK": "FRDLNK01", "CLR.T_TRIAGE": "CLRTRG01", "CLR.T_CLAIM_TIER": "CLRTIR01", "CLR.T_ASSESSMENT": "CLRASM01",
    "CLR.T_ASSESSOR_ASSIGNMENT": "CLRASG01", "CLR.T_INSPECTION": "CLRINS01", "CLR.T_ESTIMATE": "CLREST01", "CLR.T_RESERVE": "RSVREC",
    "CLR.T_RESERVE_MOVEMENT": "RSVMVT01", "CLR.T_RESERVE_HISTORY": "RSVHIS01", "CLR.T_RESERVE_AUTHORITY": "RSVAUT01",
    "CLR.T_FRAUD_SCORE": "FRDSCR01", "CLR.T_FRAUD_REFERRAL": "FRDREF01", "CLR.T_FRAUD_NOTIFICATION": "FRDNOT01",
    "CLR.T_SIU_CASE": "FRDSIU01", "CLR.T_SETTLEMENT": "STLREC01", "CLR.T_PAYMENT": "PAYREC01", "CLR.T_PAYMENT_BATCH": "PAYBAT01",
    "CLR.T_PAYEE": "PAYEE01", "CLR.T_RECOVERY": "RCVREC01", "CLR.T_SUBROGATION_CASE": "SUBCAS01", "CLR.T_SALVAGE": "SALREC01",
    "CLR.T_LITIGATION": "LITREC01", "CLR.T_GL_POSTING": "GLPOST01", "CLR.T_GL_PERIOD": "GLPER01", "CLR.T_CURRENCY_RATE": "CURRATE1",
    "CLR.T_REINSURANCE_CESSION": "RICESS01", "CLR.T_REPORT_RUN": "RPTRUN01", "CLR.T_NISA_RETURN": "NISARET1", "CLR.T_PARAM": "PARMREC1",
    "CLR.T_CODE_LOOKUP": "CODELKP1", "CLR.T_AUDIT": "AUDREC01", "CLR.T_USER": "USRREC01", "CLR.T_NOTE": "NOTEREC1",
    "CLR.T_DIARY": "DIARYRC1", "CLR.T_DOCUMENT_REF": "DOCREF01", "CLR.T_VENDOR": "VENREC01", "CLR.T_VENDOR_INVOICE": "VENINV01",
    "CLR.T_INTERFACE_LOG": "IFLOG01",
}


def _pic(c):
    t, n, s = c["type"], c["length"], c.get("scale")
    if t == "CHAR":
        return f"X({n})"
    if t == "VARCHAR":
        return f"X({n})"
    if t == "DECIMAL":
        return f"S9({n - s})V9({s}) COMP-3" if s and s > 2 else (f"S9({n - s})V99 COMP-3" if s == 2 else f"S9({n}) COMP-3")
    if t == "DATE":
        return "X(10)"
    if t == "TIMESTAMP":
        return "X(26)"
    if t == "SMALLINT":
        return "S9(4) COMP"
    if t == "INTEGER":
        return "S9(9) COMP"
    if t == "BIGINT":
        return "S9(18) COMP"
    return "X(10)"


def _cobol_name(prefix, colname):
    return f"{prefix}-{colname.replace('_', '-')}"


def build_db2_tables():
    tables = []
    for name, (area, desc, key, cols) in KEY_TABLES.items():
        tables.append({"name": name, "db": "DB2", "database": "DB2P", "schema": "CLR", "area": area, "description": desc,
                       "primary_key": key, "columns": [col(c) for c in cols]})
    for name, (area, desc, key, cols) in GEN_TABLES.items():
        r = rng(f"world:table:{name}")
        allc = list(cols)
        n_extra = r.randint(0, 3)
        extras = r.sample(EXTRA_VOCAB, n_extra)
        allc += sorted(extras)
        allc += AUDIT_COLS
        tables.append({"name": name, "db": "DB2", "database": "DB2P", "schema": "CLR", "area": area, "description": desc,
                       "primary_key": key, "columns": [col(c) for c in allc]})
    # foreign keys (selected)
    fks = {
        "CLR.T_RESERVE": [{"column": "CLAIM_ID", "references": "CLR.T_CLAIM.CLAIM_ID"}],
        "CLR.T_RESERVE_MOVEMENT": [{"column": "RSV_ID", "references": "CLR.T_RESERVE.RSV_ID"},
                                   {"column": "CLAIM_ID", "references": "CLR.T_CLAIM.CLAIM_ID"}],
        "CLR.T_FRAUD_REFERRAL": [{"column": "CLAIM_ID", "references": "CLR.T_CLAIM.CLAIM_ID"}],
        "CLR.T_FRAUD_NOTIFICATION": [{"column": "REF_ID", "references": "CLR.T_FRAUD_REFERRAL.REF_ID"}],
        "CLR.T_RECOVERY": [{"column": "SUBRO_CASE_ID", "references": "CLR.T_SUBROGATION_CASE.SUBRO_CASE_ID"}],
        "CLR.T_CLAIM": [{"column": "CLAIMANT_ID", "references": "CLR.T_CLAIMANT.CLAIMANT_ID"}],
        "CLR.T_RESERVE_AUTHORITY": [{"column": "RSV_ID", "references": "CLR.T_RESERVE.RSV_ID"}],
    }
    for t in tables:
        t["foreign_keys"] = fks.get(t["name"], [])
        t["copybook"] = TABLE_COPYBOOK.get(t["name"])
        if t["name"] == "CLR.T_PARAM":
            t["param_rows"] = T_PARAM_ROWS
        if t["name"] == "CLR.T_FRAUD_NOTIFICATION":
            t["created"] = "2026-03-27"
        if t["name"] == "CLR.T_CLAIM":
            t["retired_columns"] = [{"name": "LEGACY_SKADE_REF", "type": "CHAR", "length": 14, "retired": "2024-05-31",
                                     "description": "Reference of the claim in SKADE-90 (Nordic legacy system, retired 2024-05-31)"}]
    return tables


def build_programs():
    programs = []
    for code, specs in PROGRAM_SPECS.items():
        area = AREAS[code]
        for num, typ, desc, writes, ex in specs:
            pid = f"CLR{code}{num:03d}"
            r = rng(f"world:program:{pid}")
            reads = list(ex.get("reads") or [])
            if not reads:
                pool = [t for t in AREA_TABLES[area] if t not in writes]
                k = min(len(pool), r.randint(1, 3))
                reads = sorted(r.sample(pool, k)) if pool else []
            # programs that write normally read their own target first (except pure inserts)
            reads = sorted(set(reads))
            calls = list(ex.get("calls") or [])
            if code != "CM" and not ex.get("calls_exact"):
                if typ == O and "CLRCM050" not in calls:
                    calls.append("CLRCM050")
                if writes and "CLRCM020" not in calls and r.random() < 0.6:
                    calls.append("CLRCM020")
                if "CLR.T_PARAM" in reads and "CLRCM040" not in calls:
                    calls.append("CLRCM040")
                if typ == O and r.random() < 0.5 and "CLRCM070" not in calls:
                    calls.append("CLRCM070")
                if r.random() < 0.3 and "CLRCM010" not in calls:
                    calls.append("CLRCM010")
            calls = [c for c in calls if c != pid]
            cbs = []
            for t in sorted(set(reads) | set(writes)):
                cb = TABLE_COPYBOOK.get(t)
                if cb and cb not in cbs:
                    cbs.append(cb)
            cbs += [c for c in ex.get("copybooks_extra", []) if c not in cbs]
            cbs.append("CLRERR01")
            if typ == O and not ex.get("subprogram"):
                cbs.append("CLRCOMM1")
            if "CLRCM110" in calls or "CLRCM120" in calls or pid in ("CLRCM110", "CLRCM120"):
                cbs.append("MQMDCLR1")
            if "CLRCM010" in calls or pid == "CLRCM010":
                cbs.append("CLRDATE1")
            txn = None
            if typ == O and not ex.get("subprogram"):
                txn = code + (f"{num // 10:02d}" if num % 10 == 0 else f"{num % 100:02d}")
            replaced_by = ex["replaced_by"] if "replaced_by" in ex else AREA_SERVICE[area]
            rec = {
                "id": pid, "type": typ, "description": desc, "area": area,
                "status": ex.get("status", "active"),
                "reads_tables": reads, "writes_tables": list(writes), "calls_programs": calls,
                "copybooks": cbs,
                "cics_transaction": txn,
                "subprogram": bool(ex.get("subprogram", False)),
                "jcl_job": None, "bms_map": None,
                "owner_team": "T20", "owner_person": PROGRAM_OWNERS[code],
                "replaced_by": replaced_by,
                "renamed_from": ({"old_id": ex["renamed_from"][0], "date": ex["renamed_from"][1]} if ex.get("renamed_from") else None),
                "loc": r.randint(380, 4200) if not ex.get("subprogram") else r.randint(150, 900),
                "since": ex.get("since", "1994-10-03" if r.random() < 0.55 else f"{r.randint(1996, 2019)}-{r.randint(1, 12):02d}-01"),
            }
            if ex.get("hardcoded"):
                rec["hardcoded_constants"] = ex["hardcoded"]
            if ex.get("notes"):
                rec["notes"] = ex["notes"]
            programs.append(rec)
    ids = {p["id"] for p in programs}
    for p in programs:
        p["calls_programs"] = [c for c in p["calls_programs"] if c in ids]
    # sanity: the reserve writer set is exactly as declared
    writers = sorted(p["id"] for p in programs if RESERVE_TABLE in p["writes_tables"])
    assert writers == sorted(RESERVE_WRITERS), writers
    return programs


# ------------------------------------------------------------------ JCL
JOBS = [
    ("CLRNFN01", "Nightly FNOL imports", "daily 22:30", ["CLRFN100", "CLRFN040", "CLRFN050"]),
    ("CLRNFN02", "FNOL acknowledgement extract", "daily 06:15", ["CLRFN070"]),
    ("CLRNTR01", "Nightly triage", "daily 23:45", ["CLRTR040", "CLRTR020", "CLRTR060", "CLRTR100"]),
    ("CLRNAS01", "Assessor and repairer exchange", "daily 00:30", ["CLRAS030", "CLRAS040", "CLRAS120"]),
    ("CLRNAS02", "Vendor invoice matching", "Mon-Fri 01:00", ["CLRAS070"]),
    ("CLRNRSV1", "Tier-3 reserve review and revaluation", "daily 01:30", ["CLRRS110", "CLRRS120"]),
    ("CLRNRSV2", "Reserve history and corrections", "daily 02:00", ["CLRRS140", "CLRRS150"]),
    ("CLRNRSV3", "Reserve movement extract (CLX-IF-042)", "daily 02:15", ["CLRRS170"]),
    ("CLRNRSV4", "Large loss notification extract", "daily 07:00", ["CLRRS160"]),
    ("CLRMRSV1", "Monthly reserve indexation", "1st business day 03:00", ["CLRRS130"]),
    ("CLRMRSV2", "Month-end reserve snapshot", "last business day 22:00", ["CLRRS180", "CLRRS190"]),
    ("CLRDRSV9", "Reserve parallel-run reconciliation (retired 2026-08-28)", "daily 05:00 (2026-03-02 to 2026-08-28)", ["CLRRS210"]),
    ("CLRNFR01", "Nightly fraud scoring and referral sweep", "daily 00:15", ["CLRFR110", "CLRFR080", "CLRFR040"]),
    ("CLRNFR02", "Customer referral notices", "Mon-Fri 06:30", ["CLRFR060"]),
    ("CLRWFR01", "Weekly fraud MI and SIU export", "Mon 04:00", ["CLRFR070", "CLRFR130"]),
    ("CLRQFR01", "Quarterly NISA-FR1 extract", "quarterly, 5th business day after quarter end", ["CLRFR090"]),
    ("CLRNFR99", "Auto-decline sweep (disabled 2026-04-01)", "removed from schedule 2026-04-01 (was daily 00:45)", ["CLRFR140"]),
    ("CLRNSTL1", "Nightly settlement and closure", "daily 21:30", ["CLRST080", "CLRST040", "CLRST100"]),
    ("CLRNPAY1", "Payment batch to CPG", "Mon-Fri 16:30", ["CLRST070", "CLRST030", "CLRST140"]),
    ("CLRNPAY2", "Payment confirmations", "Mon-Fri 07:30", ["CLRST050"]),
    ("CLRWPAY1", "Vendor payment run", "Thu 15:00", ["CLRST110"]),
    ("CLRNRC01", "Nightly recoveries", "daily 22:00", ["CLRRC040", "CLRRC050", "CLRRC070", "CLRRC080"]),
    ("CLRWRC01", "Subrogation demand letters", "Tue,Thu 05:00", ["CLRRC030"]),
    ("CLRNGL01", "Daily GL feeds", "daily 03:15", ["CLRGL030", "CLRGL010", "CLRGL070"]),
    ("CLRMGL01", "GL month-end", "last business day 23:00", ["CLRGL020", "CLRGL040", "CLRGL050", "CLRGL060"]),
    ("CLRYGL90", "Year-end reserve currency revaluation", "annually 31 Dec 23:30 (and on Reserving request)", ["CLRGL090"]),
    ("CLRNRP01", "Daily MI to CDW", "daily 04:30", ["CLRRP010", "CLRRP090", "CLRRP100"]),
    ("CLRMRP01", "Monthly reports", "2nd business day 06:00", ["CLRRP020", "CLRRP050", "CLRRP070", "CLRRP080"]),
    ("CLRQRP01", "Quarterly NISA extracts", "quarterly, 4th business day after quarter end", ["CLRRP030", "CLRRP040", "CLRRP060"]),
    ("CLRWCM01", "Weekly housekeeping", "Sun 02:00", ["CLRCM130", "CLRCM140"]),
    ("CLRNMI01", "Operational MI", "daily 05:30", ["CLRFN120", "CLRTR080", "CLRAS100", "CLRST130"]),
    ("CLRWMI01", "Weekly MI", "Mon 05:00", ["CLRFN080", "CLRAS090", "CLRRC100"]),
]


RESTART = {
    "CLRNRSV1": "If CLRRS120 (STEP020) abends, restart from STEP020; STEP010 (CLRRS110) must not be rerun on the same business date.",
    "CLRNRSV3": "Rerun the whole job; CLRRS170 only extracts rows with EXTRACTED_FLAG = 'N'.",
    "CLRYGL90": "Rerun allowed (revaluation is idempotent for the same rate date).",
}


def build_jcl(programs):
    by_id = {p["id"]: p for p in programs}
    jobs = []
    for name, desc, sched, steps in JOBS:
        st = []
        for i, pg in enumerate(steps, 1):
            st.append({"step": f"STEP{i * 10:03d}", "program": pg, "description": by_id[pg]["description"]})
            by_id[pg]["jcl_job"] = name
        status = "active"
        if name == "CLRNFR99":
            status = "disabled"
        if name == "CLRDRSV9":
            status = "retired"
        jobs.append({"name": name, "description": desc, "schedule": sched, "steps": st, "status": status,
                     "scheduler": "SYS18", "owner_team": "T25",
                     "datasets": ([{"dd": "RSVOUT", "dsn": "CLR.PROD.RSVMOVE.DAILY(+1)"}] if name == "CLRNRSV3" else []),
                     "restart": RESTART.get(name)})
    missing = [p["id"] for p in programs if p["type"] == "batch" and not p["jcl_job"]]
    assert not missing, missing
    return jobs


# ------------------------------------------------------------------ BMS
MAPS = [
    ("CLRM010", "CLRMS01", "CLRFN010", "FNOL capture", ["POLICY-NO", "LOSS-DATE", "PERIL", "CHANNEL", "LOSS-DESC", "CALLER-PHONE"]),
    ("CLRM015", "CLRMS01", "CLRFN015", "Policy lookup", ["POLICY-NO", "PH-NAME", "COVER-START", "COVER-END", "EXCESS"]),
    ("CLRM110", "CLRMS02", "CLRTR010", "Triage workbench", ["CLAIM-ID", "TIER", "SCORE", "ROUTE", "FASTTRACK"]),
    ("CLRM210", "CLRMS03", "CLRAS010", "Assessment workbench", ["CLAIM-ID", "ASSESS-TYPE", "ESTIMATE", "COVER-DEC"]),
    ("CLRM220", "CLRMS03", "CLRAS020", "Claims Assessor appointment", ["CLAIM-ID", "ASSESSOR-ID", "VENDOR", "SLA-DUE"]),
    ("CLRM310", "CLRMS04", "CLRRS010", "Initial reserve", ["CLAIM-ID", "RSV-TYPE", "CURRENCY", "RSV-AMT", "AUTH-LEVEL"]),
    ("CLRM320", "CLRMS04", "CLRRS020", "Reserve adjustment", ["CLAIM-ID", "RSV-ID", "OLD-AMT", "NEW-AMT", "REASON", "NEXT-REVIEW"]),
    ("CLRM330", "CLRMS04", "CLRRS030", "Reserve enquiry", ["CLAIM-ID", "RSV-ID", "OUTSTANDING", "PAID-TD", "GBP-EQUIV"]),
    ("CLRM410", "CLRMS05", "CLRFR030", "Fraud referral", ["CLAIM-ID", "SCORE", "THRESHOLD", "TIER", "REASON", "NOTICE-DUE"]),
    ("CLRM420", "CLRMS05", "CLRFR120", "Customer-notice deferral", ["REF-ID", "DEFER-UNTIL", "APPROVER", "REASON"]),
    ("CLRM510", "CLRMS06", "CLRST010", "Settlement offer", ["CLAIM-ID", "OFFER-AMT", "EXCESS", "OFFER-DATE"]),
    ("CLRM610", "CLRMS07", "CLRRC010", "Recovery potential", ["CLAIM-ID", "TP-FAULT", "TP-INSURER", "EXPECTED-AMT"]),
    ("CLRM620", "CLRMS07", "CLRRC020", "Subrogation case", ["CASE-ID", "DEMAND-AMT", "SOLICITOR", "LIMITATION-DATE"]),
]


def build_bms(programs):
    by_id = {p["id"]: p for p in programs}
    out = []
    for mp, ms, pg, title, fields in MAPS:
        r = rng(f"world:bms:{mp}")
        flds = []
        row = 4
        for f in fields:
            flds.append({"name": f, "row": row, "col": 20, "length": r.choice([8, 10, 12, 16, 20, 30]), "attr": r.choice(["UNPROT", "UNPROT,NUM", "PROT"])})
            row += 2
        p = by_id[pg]
        p["bms_map"] = mp
        out.append({"map": mp, "mapset": ms, "program": pg, "transaction": p["cics_transaction"], "title": title,
                    "fields": flds, "pf_keys": {"PF3": "Exit", "PF7": "Back", "PF8": "Forward", "PF12": "Cancel"}})
    return out


# ------------------------------------------------------------------ copybooks
def build_copybooks(tables, programs):
    tbl = {t["name"]: t for t in tables}
    cbs = []
    used_by = {}
    for p in programs:
        for c in p["copybooks"]:
            used_by.setdefault(c, []).append(p["id"])
    for tname, cb in TABLE_COPYBOOK.items():
        t = tbl[tname]
        base = cb[3:] if cb.startswith("CLR") else cb
        base = base.rstrip("0123456789")
        prefix = "RSV" if cb == "RSVREC" else base[:4]
        fields = [{"level": 1, "name": f"{cb}-REC", "pic": None}]
        for c in t["columns"]:
            fields.append({"level": 5, "name": _cobol_name(prefix, c["name"]), "pic": _pic(c)})
        cbs.append({"name": cb, "kind": "table_record", "table": tname, "fields": fields, "used_by": sorted(used_by.get(cb, []))})
    rsvmove = [
        (1, "RSVMOVE-REC", None), (5, "RM-HEADER", None), (10, "RM-REC-TYPE", "X(2)"), (10, "RM-REC-VERSION", "9(2)"),
        (10, "RM-EXTRACT-DATE", "X(10)"), (5, "RM-CLAIM-ID", "X(12)"), (5, "RM-RSV-ID", "S9(18) COMP"), (5, "RM-MOVE-ID", "S9(18) COMP"),
        (5, "RM-MOVE-TYPE", "X(2)"), (5, "RM-CURRENCY", "X(3)"), (5, "RM-AMOUNT", "S9(9)V99 COMP-3"), (5, "RM-GBP-AMOUNT", "S9(9)V99 COMP-3"),
        (5, "RM-PRODUCT", "X(6)"), (5, "RM-PERIL", "X(4)"), (5, "RM-TIER", "X(1)"), (5, "RM-MOVE-TS", "X(26)"), (5, "FILLER", "X(20)"),
    ]
    hand = [
        ("RSVMOVE", "interface_layout", "CLX-IF-042 fixed-width record (queue CLR.RSVMOVE.OUT)", rsvmove,
         {"field_history": [
             {"field": "RM-AMOUNT", "from_pic": "S9(9)V99 COMP-3", "to_pic": "S9(11)V99 COMP-3", "date": "2025-04-25", "ticket": "CHUB-138",
              "note": "Widened for Nordic large losses; broke CLX-IF-043 (INC-2025-0412)"},
             {"field": "RM-AMOUNT", "from_pic": "S9(11)V99 COMP-3", "to_pic": "S9(9)V99 COMP-3", "date": "2025-04-30", "ticket": "CHUB-142",
              "note": "Reverted"},
             {"field": "RM-REC-VERSION", "from_pic": None, "to_pic": "9(2)", "date": "2025-04-30", "ticket": "CHUB-142",
              "note": "Record version byte added; value 02"}]}),
        ("CLRCOMM1", "commarea", "Common CICS COMMAREA", [(1, "CLR-COMMAREA", None), (5, "CA-TRANID", "X(4)"), (5, "CA-USER-ID", "X(8)"),
                                                          (5, "CA-CLAIM-ID", "X(12)"), (5, "CA-RETURN-CD", "S9(4) COMP"), (5, "CA-MSG", "X(79)")], {}),
        ("CLRERR01", "common", "Error block", [(1, "CLR-ERROR-BLOCK", None), (5, "ERR-PGM", "X(8)"), (5, "ERR-SQLCODE", "S9(9) COMP"),
                                               (5, "ERR-PARA", "X(30)"), (5, "ERR-TEXT", "X(120)")], {}),
        ("CLRDATE1", "common", "Date work area", [(1, "CLR-DATE-WORK", None), (5, "DW-IN-DATE", "X(10)"), (5, "DW-CALENDAR", "X(2)"),
                                                  (5, "DW-BUS-DAYS", "S9(4) COMP"), (5, "DW-OUT-DATE", "X(10)")], {}),
        ("MQMDCLR1", "common", "MQ message descriptor wrapper", [(1, "CLR-MQ-AREA", None), (5, "MQ-QUEUE-NAME", "X(48)"),
                                                                 (5, "MQ-MSG-LEN", "S9(9) COMP"), (5, "MQ-CORREL-ID", "X(24)")], {}),
        ("SENTREQ1", "interface_layout", "Sentinel score request", [(1, "SENT-REQUEST", None), (5, "SR-CLAIM-ID", "X(12)"),
                                                                    (5, "SR-PRODUCT", "X(6)"), (5, "SR-PERIL", "X(4)"), (5, "SR-LOSS-DATE", "X(10)"),
                                                                    (5, "SR-NOTIFIED-TS", "X(26)")], {}),
        ("SENTRSP1", "interface_layout", "Sentinel score response", [(1, "SENT-RESPONSE", None), (5, "SS-CLAIM-ID", "X(12)"),
                                                                     (5, "SS-SCORE", "9(3)"), (5, "SS-MODEL-VERSION", "X(8)"),
                                                                     (5, "SS-REASON-1", "X(6)"), (5, "SS-REASON-2", "X(6)")], {}),
    ]
    for name, kind, desc, fields, extra in hand:
        rec = {"name": name, "kind": kind, "table": None, "description": desc,
               "fields": [{"level": lv, "name": n, "pic": pic} for lv, n, pic in fields], "used_by": sorted(used_by.get(name, []))}
        rec.update(extra)
        cbs.append(rec)
    cbs.sort(key=lambda c: c["name"])
    return cbs


def attach_table_usage(tables, programs):
    for t in tables:
        if t["db"] != "DB2":
            continue
        t["writers"] = sorted(p["id"] for p in programs if t["name"] in p["writes_tables"])
        t["readers"] = sorted(p["id"] for p in programs if t["name"] in p["reads_tables"])

"""Claims Hub services, PostgreSQL tables, Kafka topics and the interface catalogue."""
from __future__ import annotations

from .common import rng
from .legacy import col

# ------------------------------------------------------------------ services

def _api(method, path, summary):
    return {"method": method, "path": path, "summary": summary}


SERVICES = [
    {"id": "SVC01", "name": "claim-core-svc", "aliases": ["claim core", "claim-core"], "renames": [],
     "description": "Claim aggregate (claim header, parties, status); system of record for migrated claims",
     "apis": [_api("GET", "/claims/{claimId}", "Get a claim by reference (CLM-UK-2025-118204 format)"),
              _api("POST", "/claims", "Create a claim from an FNOL"),
              _api("PATCH", "/claims/{claimId}", "Update claim status or attributes")],
     "produces": ["claim.created.v1", "claim.updated.v1"], "consumes": ["fnol.received.v1", "notification.sent.v1"],
     "postgres_tables": ["claim_core.claim", "claim_core.party"], "k8s_namespace": "chub-core",
     "owner_history": [("T27", "P040", "2025-02-03")], "go_live": "2025-11-03", "replicas": 3},
    {"id": "SVC02", "name": "fnol-intake-svc", "aliases": ["fnol intake", "FNOL service"], "renames": [],
     "description": "First Notice of Loss intake from portal, app, contact centre, brokers and telematics",
     "apis": [_api("POST", "/fnol", "Submit a first notice of loss"), _api("GET", "/fnol/{fnolId}", "Get FNOL status")],
     "produces": ["fnol.received.v1"], "consumes": ["eig.evidence.received.v1", "eig.telematics.alert.v1"],
     "postgres_tables": ["fnol.notification"], "k8s_namespace": "chub-intake",
     "owner_history": [("T27", "P040", "2025-02-03")], "go_live": "2025-11-03", "replicas": 4},
    {"id": "SVC03", "name": "triage-svc", "aliases": ["triage service"], "renames": [],
     "description": "Tier classification (BR-TRI-003), Sentinel pre-screen and routing",
     "apis": [_api("POST", "/triage/{claimId}", "Run triage for a claim"), _api("GET", "/triage/{claimId}", "Get triage decision")],
     "produces": ["triage.completed.v1", "fraud.score.received.v1"], "consumes": ["fnol.received.v1"],
     "postgres_tables": ["triage.triage_decision"], "k8s_namespace": "chub-intake",
     "owner_history": [("T27", "P040", "2025-02-03")], "go_live": "2025-11-03", "replicas": 3},
    {"id": "SVC04", "name": "assessment-svc", "aliases": ["assessment service"], "renames": [],
     "description": "Claims Assessor appointment, inspections, estimates and coverage decisions",
     "apis": [_api("POST", "/assessments", "Appoint a Claims Assessor"), _api("GET", "/assessments/{assessmentId}", "Get assessment"),
              _api("POST", "/assessments/{assessmentId}/report", "Attach an assessor report")],
     "produces": ["assessment.completed.v1"], "consumes": ["triage.completed.v1"],
     "postgres_tables": ["assessment.assessment", "assessment.assessor_assignment"], "k8s_namespace": "chub-assess",
     "owner_history": [("T27", "P040", "2025-02-03")], "go_live": "2026-09-14", "replicas": 2},
    {"id": "SVC05", "name": "reserve-engine", "aliases": ["reserve-svc", "reserve service", "the reserve engine"],
     "renames": [{"from_name": "reserve-svc", "to_name": "reserve-engine", "date": "2026-02-10", "ticket": "CHUB-233", "adr": "ADR-019"}],
     "description": "Case reserves, reserve movements, Tier-3 review scheduling, indexation and currency revaluation",
     "apis": [_api("GET", "/reserves/{claimId}", "Get current reserves for a claim"),
              _api("POST", "/reserves/{claimId}/movements", "Post a reserve movement (authority checked against BR-RSV-003)"),
              _api("GET", "/reserves/{claimId}/history", "Reserve movement history"),
              _api("POST", "/revaluation-runs", "Trigger a currency revaluation run (replaces CLRGL090)")],
     "produces": ["reserve.changed.v2"], "consumes": ["claims.reserve.movement.v1", "triage.completed.v1"],
     "postgres_tables": ["reserve.reserve", "reserve.reserve_movement", "reserve.review_schedule"], "k8s_namespace": "chub-reserve",
     "owner_history": [("T28", "P041", "2025-02-03")], "go_live": "2026-09-14", "replicas": 4,
     "infra": {"postgres_storage_gi": 200, "cpu_request": "500m", "memory_limit": "2Gi"},
     "config": {"tier3-review-days": 14, "large-loss-threshold-gbp": 250000, "bi-index-pct": 3.1,
                "config_history": [{"key": "tier3-review-days", "value": 21, "to": "2026-07-02", "ticket": "CHUB-322"}]}},
    {"id": "SVC06", "name": "fraud-referral-svc", "aliases": ["fraud referral service", "fraud-svc"], "renames": [],
     "description": "Fraud referral decisions, SIU hand-off and customer-notice deadlines (NISA Circular 2026/04)",
     "apis": [_api("POST", "/referrals", "Create a fraud referral"), _api("GET", "/referrals/{referralId}", "Get a referral"),
              _api("POST", "/referrals/{referralId}/customer-notice", "Record or defer the customer notice (deadline = referral date + 10 business days)")],
     "produces": ["fraud.referral.created.v1", "fraud.referral.notice-due.v1"], "consumes": ["fraud.score.received.v1", "triage.completed.v1",
                                                                                           "notification.fraud-notice.sent.v1"],
     "postgres_tables": ["fraud.referral", "fraud.customer_notice"], "k8s_namespace": "chub-fraud",
     "owner_history": [("T29", "P042", "2025-02-03")], "go_live": "2026-04-01", "replicas": 3,
     "config": {"referral.threshold.default": 65, "referral.threshold.tier3": 60, "referral.threshold.tier3.effective-from": "2026-10-01",
                "notice.business-days": 10, "notice.max-deferral-days": 60, "auto-decline.enabled": False}},
    {"id": "SVC07", "name": "settlement-svc", "aliases": ["settlement service"], "renames": [],
     "description": "Settlement offers, fast-track settlement, closure and reserve close-down instructions",
     "apis": [_api("POST", "/settlements", "Create a settlement offer"), _api("POST", "/settlements/{settlementId}/finalise", "Finalise and close")],
     "produces": ["settlement.agreed.v1"], "consumes": ["assessment.completed.v1"],
     "postgres_tables": ["settlement.settlement"], "k8s_namespace": "chub-settle",
     "owner_history": [("T29", "P042", "2025-02-03")], "go_live": "2026-09-14", "replicas": 2},
    {"id": "SVC08", "name": "payment-orchestrator", "aliases": ["payments orchestrator", "payment-svc"], "renames": [],
     "description": "Payment authorisation (BR-STL-002), sanctions screening and CPG instructions",
     "apis": [_api("POST", "/payments", "Request a payment"), _api("POST", "/payments/{paymentId}/cancel", "Cancel a payment")],
     "produces": ["payment.requested.v1"], "consumes": ["settlement.agreed.v1", "payment.confirmed.v1"],
     "postgres_tables": ["payment.payment_instruction"], "k8s_namespace": "chub-settle",
     "owner_history": [("T29", "P042", "2025-02-03")], "go_live": "2026-09-14", "replicas": 3},
    {"id": "SVC09", "name": "recovery-svc", "aliases": ["recovery service", "subro service"], "renames": [],
     "description": "Subrogation cases, salvage and recovery receipts; replaces SUBTRAK",
     "apis": [_api("POST", "/recoveries", "Open a recovery / subrogation case"), _api("POST", "/recoveries/{caseId}/receipts", "Record a receipt"),
              _api("POST", "/recoveries/{caseId}/write-off", "Write off (approval above £10,000 by Head of Recoveries & Subrogation)")],
     "produces": ["recovery.receipt.v1"], "consumes": ["settlement.agreed.v1"],
     "postgres_tables": ["recovery.recovery_case", "recovery.receipt"], "k8s_namespace": "chub-recovery",
     "owner_history": [("T29", "P042", "2025-02-03"), ("T30", "P043", "2026-11-01")], "go_live": "2026-09-14", "replicas": 2},
    {"id": "SVC10", "name": "document-svc", "aliases": ["document service", "docs-svc"], "renames": [],
     "description": "Document metadata; stores binaries in Evidence Vault (formerly DOCSTOR)",
     "apis": [_api("POST", "/documents", "Store a document"), _api("GET", "/documents/{documentId}", "Get document metadata")],
     "produces": ["document.stored.v1"], "consumes": ["eig.evidence.received.v1"],
     "postgres_tables": ["document.document"], "k8s_namespace": "chub-docs",
     "owner_history": [("T27", "P040", "2025-02-03"), ("T30", "P043", "2026-11-01")], "go_live": "2025-11-03", "replicas": 2},
    {"id": "SVC11", "name": "notification-svc", "aliases": ["notification service", "notify-svc"], "renames": [],
     "description": "Customer communications via Notify (acknowledgements, fraud-referral notices, recovery letters)",
     "apis": [_api("POST", "/notifications", "Send a notification")],
     "produces": ["notification.sent.v1", "notification.fraud-notice.sent.v1"], "consumes": ["fnol.received.v1", "fraud.referral.notice-due.v1"],
     "postgres_tables": ["notification.message"], "k8s_namespace": "chub-notify",
     "owner_history": [("T27", "P040", "2025-02-03")], "go_live": "2025-11-03", "replicas": 2},
    {"id": "SVC12", "name": "gl-posting-svc", "aliases": ["GL posting service"], "renames": [],
     "description": "Journals to Group Ledger from reserve and payment events",
     "apis": [_api("GET", "/journals/{period}", "List journals for a GL period")],
     "produces": [], "consumes": ["reserve.changed.v2", "payment.confirmed.v1", "recovery.receipt.v1"],
     "postgres_tables": ["gl.journal_line"], "k8s_namespace": "chub-finance",
     "owner_history": [("T28", "P041", "2025-02-03")], "go_live": "2026-09-14", "replicas": 2},
    {"id": "SVC13", "name": "reporting-feed-svc", "aliases": ["reporting feed"], "renames": [],
     "description": "Regulatory extracts to NISA Reporting Hub (replaces CLARA NISA extracts from 2027)",
     "apis": [_api("POST", "/returns/{returnCode}/{period}/extract", "Build a return extract (TP2, FR1, CT1)")],
     "produces": [], "consumes": ["reserve.changed.v2", "fraud.referral.created.v1"],
     "postgres_tables": ["reporting.return_extract"], "k8s_namespace": "chub-finance",
     "owner_history": [("T28", "P041", "2025-02-03")], "go_live": "2027-01-11", "replicas": 1, "status": "in development"},
]

KAFKA_TOPICS = [
    ("fnol.received.v1", 6, 7, "fnol-intake-svc", ["triage-svc", "claim-core-svc", "notification-svc"]),
    ("eig.evidence.received.v1", 6, 7, "Evidence Intake Gateway", ["fnol-intake-svc", "document-svc"]),
    ("eig.telematics.alert.v1", 3, 3, "Evidence Intake Gateway", ["fnol-intake-svc"]),
    ("claim.created.v1", 6, 30, "claim-core-svc", ["Claims Data Warehouse"]),
    ("claim.updated.v1", 6, 30, "claim-core-svc", ["Claims Data Warehouse"]),
    ("triage.completed.v1", 6, 7, "triage-svc", ["reserve-engine", "fraud-referral-svc", "assessment-svc"]),
    ("fraud.score.received.v1", 6, 7, "triage-svc", ["fraud-referral-svc"]),
    ("fraud.referral.created.v1", 3, 30, "fraud-referral-svc", ["reporting-feed-svc"]),
    ("fraud.referral.notice-due.v1", 3, 30, "fraud-referral-svc", ["notification-svc"]),
    ("notification.sent.v1", 3, 7, "notification-svc", ["claim-core-svc"]),
    ("notification.fraud-notice.sent.v1", 3, 30, "notification-svc", ["fraud-referral-svc"]),
    ("claims.reserve.movement.v1", 12, 14, "MQ-to-Kafka bridge (CLX-IF-049)", ["reserve-engine"]),
    ("reserve.changed.v2", 12, 30, "reserve-engine", ["gl-posting-svc", "reporting-feed-svc"]),
    ("assessment.completed.v1", 3, 7, "assessment-svc", ["settlement-svc"]),
    ("settlement.agreed.v1", 3, 7, "settlement-svc", ["payment-orchestrator", "recovery-svc"]),
    ("payment.requested.v1", 3, 7, "payment-orchestrator", ["Corvane Payments Gateway adapter"]),
    ("payment.confirmed.v1", 3, 7, "Corvane Payments Gateway adapter", ["payment-orchestrator", "gl-posting-svc"]),
    ("recovery.receipt.v1", 3, 30, "recovery-svc", ["gl-posting-svc"]),
    ("document.stored.v1", 3, 7, "document-svc", ["claim-core-svc"]),
]

TOPIC_EXTRA = {
    "notification.fraud-notice.sent.v1": {"introduced": "2026-11-12", "ticket": "CHUB-421",
                                          "note": "Added by the follow-up commit (code variant c only)"},
    "claims.reserve.movement.v1": {"introduced": "2025-12-12", "ticket": "CHUB-188", "key": "claim_id",
                                   "schema_version": 3, "note": "Bridged from CLX-IF-042 by CLX-IF-049 (ADR-012)"},
    "reserve.changed.v2": {"introduced": "2026-02-10", "ticket": "CHUB-233", "note": "v1 retired with the reserve-svc rename"},
}

PG_TABLES = {
    "claim_core.claim": ("claim-core-svc", ["claim_id:VARCHAR(20):Claim reference CLM-<region>-<yyyy>-<6 digits>",
                                            "legacy_claim_id:CHAR(12):CLARA CLAIM_ID", "policy_no:VARCHAR(10):Policy number",
                                            "product_code:VARCHAR(10):Product", "claim_type:VARCHAR(10):Claim Type (peril)",
                                            "loss_date:DATE:Date of loss", "notified_at:TIMESTAMP:First Notice of Loss time",
                                            "status:VARCHAR(16):Status", "tier:SMALLINT:Tier 1-3", "region:CHAR(2):Region",
                                            "currency:CHAR(3):Currency", "handler_id:VARCHAR(12):Claims Handler"]),
    "claim_core.party": ("claim-core-svc", ["party_id:UUID:Party", "claim_id:VARCHAR(20):Claim", "role:VARCHAR(12):Policyholder, claimant, witness",
                                            "family_name:VARCHAR(60):Family name:pii", "given_name:VARCHAR(60):Given name:pii",
                                            "email:VARCHAR(120):Email:pii:null", "phone:VARCHAR(20):Phone:pii:null"]),
    "fnol.notification": ("fnol-intake-svc", ["fnol_id:UUID:FNOL id", "channel:VARCHAR(12):Channel", "received_at:TIMESTAMP:Received",
                                              "claim_id:VARCHAR(20):Claim:null", "payload:JSONB:Raw payload", "ack_sent_at:TIMESTAMP:Acknowledged:null"]),
    "triage.triage_decision": ("triage-svc", ["decision_id:UUID:Decision", "claim_id:VARCHAR(20):Claim", "tier:SMALLINT:Tier",
                                              "sentinel_score:SMALLINT:Sentinel score", "route:VARCHAR(12):FAST, HANDLER, MCL",
                                              "decided_at:TIMESTAMP:Decided"]),
    "assessment.assessment": ("assessment-svc", ["assessment_id:UUID:Assessment", "claim_id:VARCHAR(20):Claim", "type:VARCHAR(10):Desk, site, video",
                                                 "estimate_amount:NUMERIC(13,2):Estimate", "cover_decision:VARCHAR(10):Decision"]),
    "assessment.assessor_assignment": ("assessment-svc", ["assignment_id:UUID:Assignment", "claim_id:VARCHAR(20):Claim",
                                                          "claims_assessor_id:VARCHAR(12):Claims Assessor (internal or vendor)",
                                                          "vendor_code:VARCHAR(10):Vendor:null", "sla_due:DATE:SLA due"]),
    "reserve.reserve": ("reserve-engine", ["reserve_id:UUID:Reserve", "claim_id:VARCHAR(20):Claim", "reserve_type:VARCHAR(10):Indemnity, expense, legal",
                                           "currency:CHAR(3):Currency", "outstanding_amount:NUMERIC(13,2):Outstanding (maps from RSV_OUTSTANDING_AMT)",
                                           "gbp_equivalent:NUMERIC(13,2):GBP equivalent", "next_review_date:DATE:Next review:null",
                                           "status:VARCHAR(8):Open or closed"]),
    "reserve.reserve_movement": ("reserve-engine", ["movement_id:UUID:Movement", "reserve_id:UUID:Reserve", "movement_type:VARCHAR(12):Type",
                                                    "amount_minor:BIGINT:Amount in minor units (pence/øre)", "currency:CHAR(3):Currency",
                                                    "source:VARCHAR(16):CLAIMS_HUB or CLARA_BRIDGE", "created_at:TIMESTAMP:Created"]),
    "reserve.review_schedule": ("reserve-engine", ["claim_id:VARCHAR(20):Claim", "next_review_date:DATE:Next review",
                                                   "cadence_days:SMALLINT:Cadence (14 for Tier-3 from 2026-07-01)"]),
    "fraud.referral": ("fraud-referral-svc", ["referral_id:UUID:Referral", "claim_id:VARCHAR(20):Claim", "sentinel_score:SMALLINT:Score",
                                              "threshold_applied:SMALLINT:Threshold applied (65, or 60 for Tier-3 from 2026-10-01)",
                                              "tier:SMALLINT:Tier", "referred_at:TIMESTAMP:Referred", "siu_case_id:VARCHAR(12):SIU case:null",
                                              "rule_id:VARCHAR(12):Rule (BR-FRD-031)"]),
    "fraud.customer_notice": ("fraud-referral-svc", ["notice_id:UUID:Notice", "referral_id:UUID:Referral", "due_date:DATE:Due (10 business days)",
                                                     "deferred_until:DATE:Deferred until:null", "sent_at:TIMESTAMP:Sent:null",
                                                     "channel:VARCHAR(8):Letter, SMS, email"]),
    "settlement.settlement": ("settlement-svc", ["settlement_id:UUID:Settlement", "claim_id:VARCHAR(20):Claim", "offer_amount:NUMERIC(13,2):Offer",
                                                 "excess_applied:NUMERIC(11,2):Excess", "final:BOOLEAN:Final", "agreed_at:TIMESTAMP:Agreed:null"]),
    "payment.payment_instruction": ("payment-orchestrator", ["payment_id:UUID:Payment", "claim_id:VARCHAR(20):Claim", "amount:NUMERIC(13,2):Amount",
                                                             "currency:CHAR(3):Currency", "idempotency_key:VARCHAR(64):Idempotency key (CHUB-371)",
                                                             "status:VARCHAR(12):Status", "payee_iban:VARCHAR(34):Payee IBAN:pii"]),
    "recovery.recovery_case": ("recovery-svc", ["case_id:UUID:Case", "claim_id:VARCHAR(20):Claim", "type:VARCHAR(12):Subrogation, salvage",
                                                "expected_amount:NUMERIC(13,2):Expected", "status:VARCHAR(12):Status",
                                                "subtrak_ref:VARCHAR(12):Legacy SUBTRAK reference:null"]),
    "recovery.receipt": ("recovery-svc", ["receipt_id:UUID:Receipt", "case_id:UUID:Case", "amount:NUMERIC(13,2):Amount", "received_at:DATE:Received"]),
    "document.document": ("document-svc", ["document_id:UUID:Document", "claim_id:VARCHAR(20):Claim", "vault_object_id:VARCHAR(36):Evidence Vault object",
                                           "doc_type:VARCHAR(10):Type", "stored_at:TIMESTAMP:Stored"]),
    "notification.message": ("notification-svc", ["message_id:UUID:Message", "claim_id:VARCHAR(20):Claim", "template:VARCHAR(20):Template",
                                                  "channel:VARCHAR(8):Channel", "notify_message_id:VARCHAR(36):Notify id", "sent_at:TIMESTAMP:Sent:null"]),
    "gl.journal_line": ("gl-posting-svc", ["line_id:UUID:Line", "period:CHAR(6):Period", "account:VARCHAR(10):Account", "amount_gbp:NUMERIC(15,2):Amount",
                                           "source_event:VARCHAR(40):Source event"]),
    "reporting.return_extract": ("reporting-feed-svc", ["extract_id:UUID:Extract", "return_code:VARCHAR(6):TP2, FR1, CT1", "period:VARCHAR(6):Period",
                                                        "payload:JSONB:Extract payload", "created_at:TIMESTAMP:Created"]),
}


def _pgcol(spec):
    parts = spec.split(":")
    name, typ, desc = parts[0], parts[1], parts[2]
    flags = set(parts[3:])
    length = scale = None
    base = typ
    if "(" in typ:
        base, rest = typ.split("(")
        rest = rest.rstrip(")")
        if "," in rest:
            length, scale = (int(x) for x in rest.split(","))
        else:
            length = int(rest)
    out = {"name": name, "type": base, "length": length}
    if scale is not None:
        out["scale"] = scale
    out.update({"nullable": "null" in flags, "description": desc, "pii": "pii" in flags})
    return out


def build_pg_tables():
    out = []
    for name, (svc, cols) in PG_TABLES.items():
        schema = name.split(".")[0]
        out.append({"name": name, "db": "PostgreSQL", "database": f"chub_{schema}", "schema": schema, "area": "TARGET",
                    "owning_service": svc, "description": f"{svc} table {name}", "primary_key": [cols[0].split(":")[0]],
                    "columns": [_pgcol(c) for c in cols], "foreign_keys": []})
    return out


def build_services(programs):
    out = []
    for s in SERVICES:
        oh = []
        for i, (team, person, frm) in enumerate(s["owner_history"]):
            to = None
            if i + 1 < len(s["owner_history"]):
                from .common import day_before
                to = day_before(s["owner_history"][i + 1][2])
            oh.append({"team": team, "person": person, "from": frm, "to": to})
        name = s["name"]
        tf = f"infra/terraform/modules/{name}"
        rec = {
            "id": s["id"], "name": name, "aliases": s["aliases"], "renames": s["renames"], "description": s["description"],
            "status": s.get("status", "live"), "go_live": s["go_live"],
            "apis": s["apis"], "kafka_topics": {"produces": s["produces"], "consumes": s["consumes"]},
            "postgres_tables": s["postgres_tables"],
            "replaces_programs": sorted(p["id"] for p in programs if p["replaced_by"] == name),
            "owner_team": oh[-1]["team"], "owner_person": oh[-1]["person"], "owner_history": oh,
            "k8s_namespace": s["k8s_namespace"], "replicas": s["replicas"],
            "terraform_module": tf, "repo_path": f"services/{name}",
            "image": f"registry.corvane.internal/chub/{name}",
        }
        if name == "reserve-engine":
            rec["path_history"] = [{"repo_path": "services/reserve-svc", "terraform_module": "infra/terraform/modules/reserve-svc",
                                    "k8s_namespace": "chub-reserve", "to": "2026-02-09"}]
        if s.get("config"):
            rec["config"] = s["config"]
        if s.get("infra"):
            rec["infra"] = s["infra"]
        out.append(rec)
    return out


def build_topics():
    out = []
    for name, parts, ret, producer, consumers in KAFKA_TOPICS:
        rec = {"name": name, "partitions": parts, "retention_days": ret, "producer": producer, "consumers": consumers,
               "cluster": "esp-prd (SYS15)"}
        rec.update(TOPIC_EXTRA.get(name, {}))
        out.append(rec)
    return out


# ------------------------------------------------------------------ interfaces
# (num, name, src, tgt, protocol, format, schedule, programs, services, tables, owner, crit, depends_on, extra)
IFS = [
    (1, "Portal FNOL submissions", "SYS04", "SYS01", "MQ", "JSON over MQ (queue CLR.FNOL.IN)", "real-time", ["CLRFN040"], [], ["CLR.T_FNOL_EVENT"], "P029", "High", [], {}),
    (2, "Contact centre FNOL hand-off", "SYS12", "SYS01", "CICS", "CICS COMMAREA (CLRCOMM1) via web-service bridge", "real-time", ["CLRFN010"], [], ["CLR.T_FNOL_EVENT"], "P029", "High", [], {}),
    (3, "Policy snapshot feed", "SYS08", "SYS01", "DB2 unload", "Fixed-width unload (CLRPOL01 layout) over SFTP", "daily 21:45", ["CLRFN100"], [], ["CLR.T_POLICY_SNAPSHOT"], "P016", "High", [], {}),
    (4, "Evidence references to CLARA", "SYS13", "SYS01", "MQ", "JSON over MQ (queue CLR.EVIDENCE.IN)", "real-time", ["CLRFN050"], [], ["CLR.T_DOCUMENT_REF"], "P040", "Medium", [], {"live_from": "2023-03-01"}),
    (5, "Evidence images to Evidence Vault", "SYS13", "SYS05", "REST", "multipart/form-data", "real-time", [], [], [], "P040", "Medium", [], {"live_from": "2023-03-01"}),
    (6, "FNOL acknowledgements", "SYS01", "SYS25", "SFTP", "CSV (ack_YYYYMMDD.csv)", "daily 06:15", ["CLRFN070"], [], ["CLR.T_FNOL_EVENT"], "P029", "High", [1, 2], {"feeds_reports": ["NISA-CT1"]}),
    (7, "Vehicle data lookup", "SYS01", "SYS20", "REST", "JSON (HTTPS)", "on demand", ["CLRFN015"], [], [], "P040", "Low", [], {}),
    (8, "Online Sentinel scoring", "SYS01", "SYS03", "REST", "JSON (HTTPS) via mainframe API gateway; SENTREQ1/SENTRSP1 mapping", "real-time", ["CLRFR020"], [], ["CLR.T_FRAUD_SCORE"], "P027", "Critical", [], {}),
    (9, "Nightly Sentinel batch scoring request", "SYS01", "SYS03", "SFTP", "CSV", "daily 00:15", ["CLRFR110"], [], ["CLR.T_FRAUD_SCORE"], "P027", "High", [], {}),
    (10, "Nightly Sentinel batch score return", "SYS03", "SYS01", "SFTP", "CSV", "daily 00:55", ["CLRFR110"], [], ["CLR.T_FRAUD_SCORE"], "P027", "High", [9], {}),
    (11, "Fraud referrals to SIU Case Manager", "SYS01", "SYS22", "MQ", "XML over MQ (queue CLR.SIUREF.OUT)", "real-time", ["CLRFR030", "CLRFR070"], [], ["CLR.T_FRAUD_REFERRAL"], "P028", "High", [8], {}),
    (12, "SIU outcomes to CLARA", "SYS22", "SYS01", "MQ", "XML over MQ (queue CLR.SIUOUT.IN)", "real-time", ["CLRFR050"], [], ["CLR.T_FRAUD_REFERRAL", "CLR.T_SIU_CASE"], "P028", "Medium", [11], {}),
    (13, "Assessor instructions", "SYS01", "SYS17", "SFTP", "XML", "every 30 minutes 07:00-19:00", ["CLRAS030"], [], ["CLR.T_ASSESSOR_ASSIGNMENT"], "P033", "High", [], {}),
    (14, "Assessor reports", "SYS17", "SYS01", "SFTP", "XML + PDF", "hourly 08:00-20:00", ["CLRAS040"], [], ["CLR.T_ASSESSMENT"], "P033", "High", [13], {}),
    (15, "Repair network job export", "SYS01", "SYS17", "SFTP", "CSV", "daily 00:30", ["CLRAS120"], [], ["CLR.T_ESTIMATE"], "P033", "Medium", [], {}),
    (16, "Vendor invoices", "SYS17", "SYS01", "SFTP", "CSV", "Mon-Fri 01:00", ["CLRAS070"], [], ["CLR.T_VENDOR_INVOICE"], "P035", "Medium", [], {}),
    (17, "Sanctions screening requests", "SYS01", "SYS19", "MQ", "XML over MQ", "Mon-Fri 16:15", ["CLRST070"], [], ["CLR.T_PAYMENT"], "P037", "Critical", [], {}),
    (18, "Sanctions screening results", "SYS19", "SYS01", "MQ", "XML over MQ", "Mon-Fri 16:25", ["CLRST070"], [], ["CLR.T_PAYMENT"], "P037", "Critical", [17], {}),
    (19, "UK payment batch", "SYS01", "SYS09", "SFTP", "ISO 20022 pain.001 XML", "Mon-Fri 16:30", ["CLRST030"], [], ["CLR.T_PAYMENT_BATCH", "CLR.T_PAYMENT"], "P035", "Critical", [18], {}),
    (20, "Payment confirmations", "SYS09", "SYS01", "SFTP", "ISO 20022 pain.002 XML", "Mon-Fri 07:30", ["CLRST050"], [], ["CLR.T_PAYMENT"], "P035", "Critical", [19], {}),
    (21, "Nordic payment batch (NOK/SEK/DKK)", "SYS01", "SYS09", "SFTP", "ISO 20022 pain.001 XML", "Mon-Fri 16:30", ["CLRST140"], [], ["CLR.T_PAYMENT_BATCH"], "P035", "Critical", [18], {}),
    (22, "SUBTRAK synchronisation", "SYS01", "SYS24", "DB2 unload", "Fixed-width unload over SFTP", "daily 22:00", ["CLRRC040"], [], ["CLR.T_SUBROGATION_CASE"], "P013", "Medium", [], {}),
    (23, "Recovery receipts from SUBTRAK", "SYS24", "SYS01", "SFTP", "CSV", "daily 21:30", ["CLRRC050"], [], ["CLR.T_RECOVERY", "CLR.T_RESERVE"], "P013", "High", [22], {}),
    (24, "Salvage disposals", "SYS17", "SYS01", "SFTP", "CSV uploaded by Salvanta Salvage via the Assessor Portal partner SFTP", "daily 20:00", ["CLRRC070"], [], ["CLR.T_SALVAGE"], "P014", "Low", [], {"external_party": "VEN-09"}),
    (25, "Solicitor instructions", "SYS01", "SYS05", "SFTP", "PDF + XML to Quarryhill Solicitors via Evidence Vault share", "on demand", ["CLRRC060"], [], ["CLR.T_LITIGATION"], "P014", "Low", [], {"external_party": "VEN-07"}),
    (26, "Subrogation demand letters", "SYS01", "SYS25", "SFTP", "CSV", "Tue,Thu 05:00", ["CLRRC030"], [], ["CLR.T_SUBROGATION_CASE"], "P014", "Medium", [], {}),
    (27, "Currency rates to CLARA", "SYS06", "SYS01", "SFTP", "CSV (rates_YYYYMMDD.csv)", "daily 03:15", ["CLRGL030"], [], ["CLR.T_CURRENCY_RATE"], "P021", "High", [], {}),
    (28, "Payment postings to GL", "SYS01", "SYS06", "SFTP", "Fixed-width journal file", "daily 03:30", ["CLRGL010"], [], ["CLR.T_GL_POSTING"], "P021", "High", [20, 27], {}),
    (29, "Recovery income postings to GL", "SYS01", "SYS06", "SFTP", "Fixed-width journal file", "daily 03:40", ["CLRGL070"], [], ["CLR.T_GL_POSTING"], "P021", "Medium", [23], {}),
    (30, "Daily claims MI to CDW", "SYS01", "SYS11", "DB2 unload", "Delimited unload over SFTP", "daily 04:30", ["CLRRP010"], [], ["CLR.T_CLAIM"], "P036", "Medium", [], {}),
    (31, "Large loss notifications to reinsurance", "SYS01", "SYS07", "MQ", "XML over MQ (queue CLR.LLN.OUT)", "daily 07:00", ["CLRRS160"], [], ["CLR.T_RESERVE_MOVEMENT"], "P038", "High", [], {}),
    (32, "Claims timeliness extract (NISA-CT1)", "SYS01", "SYS10", "SFTP", "XML", "annual, by 15 March", ["CLRRP040"], [], ["CLR.T_NISA_RETURN"], "P020", "Medium", [], {"feeds_reports": ["NISA-CT1"]}),
    (33, "Fraud referral return (NISA-FR1)", "SYS01", "SYS10", "SFTP", "XML", "quarterly, 5th business day after quarter end", ["CLRFR090"], [], ["CLR.T_NISA_RETURN", "CLR.T_FRAUD_REFERRAL"], "P037", "High", [12], {"feeds_reports": ["NISA-FR1"], "live_from": "2026-07-07"}),
    (34, "FNOL events (internal)", "SYS02", "SYS15", "Kafka", "Avro (fnol.received.v1)", "real-time", [], ["fnol-intake-svc"], ["fnol.notification"], "P040", "High", [], {"kafka_topic": "fnol.received.v1"}),
    (35, "Portal FNOL to Claims Hub", "SYS04", "SYS02", "REST", "JSON (POST /fnol)", "real-time", [], ["fnol-intake-svc"], ["fnol.notification"], "P029", "High", [], {"live_from": "2026-09-14"}),
    (36, "Claims Hub Sentinel scoring", "SYS02", "SYS03", "REST", "JSON (HTTPS)", "real-time", [], ["triage-svc"], ["triage.triage_decision"], "P027", "Critical", [], {}),
    (37, "Claims Hub customer notifications", "SYS02", "SYS25", "REST", "JSON (HTTPS)", "real-time", [], ["notification-svc"], ["notification.message"], "P040", "High", [], {}),
    (38, "Claims Hub payments to CPG", "SYS02", "SYS09", "REST", "ISO 20022 pain.001 JSON mapping", "real-time", [], ["payment-orchestrator"], ["payment.payment_instruction"], "P035", "Critical", [], {"live_from": "2026-09-14"}),
    (39, "Claims Hub documents to Evidence Vault", "SYS02", "SYS05", "REST", "multipart/form-data", "real-time", [], ["document-svc"], ["document.document"], "P043", "Medium", [], {}),
    (40, "Workforce and partner identity", "SYS16", "SYS02", "REST", "OIDC tokens (JWT)", "real-time", [], [], [], "P032", "Critical", [], {}),
    (41, "Claims Hub fraud referrals to SIU Case Manager", "SYS02", "SYS22", "REST", "JSON (HTTPS)", "real-time", [], ["fraud-referral-svc"], ["fraud.referral"], "P028", "High", [36], {}),
    (42, "Reserve Movement Daily Extract", "SYS01", "SYS14", "DB2 unload", "Fixed-width RSVMOVE records put to queue CLR.RSVMOVE.OUT", "daily 02:15", ["CLRRS170"], [], ["CLR.T_RESERVE_MOVEMENT"], "P031", "Critical", [27],
     {"mq_queue": "CLR.RSVMOVE.OUT", "copybook": "RSVMOVE", "jcl_job": "CLRNRSV3", "dataset": "CLR.PROD.RSVMOVE.DAILY(+1)", "volume_per_day": "≈18,500 records", "mq_max_depth": 50000, "live_from": "2015-02-02"}),
    (43, "GL Reserve Journal Feed", "SYS14", "SYS06", "MQ", "RSVMOVE records → GL journal lines (GL adapter)", "daily 03:45", [], [], [], "P021", "Critical", [42],
     {"live_from": "2015-02-02", "consumer_teams": ["T14"], "schedule_history": [{"value": "daily 03:00", "from": "2015-02-02", "to": "2025-05-08"},
                                                      {"value": "daily 03:45", "from": "2025-05-09", "to": None, "ticket": "CHUB-143"}]}),
    (44, "CDW Reserve Fact Load", "SYS14", "SYS11", "MQ", "RSVMOVE records → reserve fact table F_RESERVE_MOVEMENT", "daily 04:00", [], [], [], "P036", "High", [42], {"consumer_teams": ["T23"], "live_from": "2018-06-01"}),
    (45, "Reserve change events (internal)", "SYS02", "SYS15", "Kafka", "Avro (reserve.changed.v2)", "real-time", [], ["reserve-engine"], ["reserve.reserve_movement"], "P041", "High", [], {"kafka_topic": "reserve.changed.v2", "live_from": "2026-02-10"}),
    (46, "Claim status to Harbour CRM", "SYS11", "SYS12", "SFTP", "CSV", "daily 06:00", [], [], [], "P029", "Low", [30], {}),
    (47, "Reserve Cession Feed", "SYS14", "SYS07", "MQ", "RSVMOVE records → ReCede cession input", "daily 04:15", [], [], [], "P038", "High", [42], {"consumer_teams": ["T17"], "live_from": "2019-01-07"}),
    (48, "Treaty premium journals", "SYS07", "SYS06", "SFTP", "CSV journal file", "monthly, 4th business day", [], [], [], "P038", "Medium", [], {}),
    (49, "Reserve Movement Kafka Bridge", "SYS14", "SYS15", "Kafka", "RSVMOVE → Avro (claims.reserve.movement.v1, schema v3)", "daily 02:45", [], ["reserve-engine"], ["reserve.reserve_movement"], "P031", "High", [42],
     {"kafka_topic": "claims.reserve.movement.v1", "status": "live", "live_from": "2025-12-12", "consumer_teams": ["T28"],
      "note": "Batch-to-event bridge (ADR-012); consumed by reserve-engine for parallel-run reconciliation and Wave 2 sync"}),
    (50, "Claims Hub journals to GL", "SYS02", "SYS06", "REST", "JSON journals", "hourly", [], ["gl-posting-svc"], ["gl.journal_line"], "P021", "High", [45], {"live_from": "2026-09-14"}),
    (51, "Technical Provisions Feed", "SYS06", "SYS10", "SFTP", "XML (TP2 cells)", "quarterly, 10th business day after quarter end", [], [], [], "P020", "Critical", [43],
     {"feeds_reports": ["NISA-TP2"], "consumer_teams": ["T15"], "live_from": "2016-04-01"}),
    (52, "Claims statistics for NISA-CT1", "SYS11", "SYS10", "SFTP", "CSV", "annual, by 1 March", [], [], [], "P020", "Medium", [30], {"feeds_reports": ["NISA-CT1"]}),
    (53, "Contact preferences to Notify", "SYS12", "SYS25", "SFTP", "CSV", "daily 05:00", [], [], [], "P029", "Low", [], {}),
    (54, "Policy API for Claims Hub", "SYS08", "SYS02", "REST", "JSON (HTTPS)", "real-time", [], ["claim-core-svc"], [], "P006", "High", [], {}),
    (55, "Monthly Claims Bordereaux", "SYS07", "SYS26", "SFTP", "CSV bordereau per treaty", "monthly, 5th business day", [], [], [], "P038", "High", [47],
     {"consumer_teams": ["T17"], "external_consumers": ["VEN-12", "VEN-13"], "live_from": "2020-01-06"}),
    (56, "Claim events to CDW", "SYS15", "SYS11", "Kafka", "Avro (claim.created.v1, claim.updated.v1) via sink connector", "near real-time", [], ["claim-core-svc"], [], "P036", "Medium", [34], {}),
    (57, "Telematics crash alerts", "SYS13", "SYS02", "Kafka", "JSON (eig.telematics.alert.v1)", "real-time", [], ["fnol-intake-svc"], [], "P040", "Medium", [], {"kafka_topic": "eig.telematics.alert.v1"}),
    (58, "Reserve Triangles Extract", "SYS11", "SYS21", "SFTP", "CSV triangles (accident quarter × development quarter)", "monthly, 3rd business day", [], [], [], "P009", "High", [44],
     {"consumer_teams": ["T12"], "note": "Feeds the monthly IBNR run of the Reserving team", "live_from": "2016-01-04"}),
    (59, "Scanned post to Evidence Vault", "SYS27", "SYS05", "SFTP", "PDF + XML index", "hourly", [], [], [], "P029", "Low", [], {}),
    (60, "Claims Hub regulatory extracts", "SYS02", "SYS10", "REST", "JSON", "quarterly", [], ["reporting-feed-svc"], ["reporting.return_extract"], "P020", "High", [], {"status": "planned", "live_from": "2027-01-11"}),
]

# The deliberate downstream-impact answer for CLX-IF-042 (validated against depends_on).
IMPACT_042 = {
    "hop1": ["CLX-IF-043", "CLX-IF-044", "CLX-IF-047", "CLX-IF-049"],
    "hop2": ["CLX-IF-051", "CLX-IF-055", "CLX-IF-058"],
    "systems": ["SYS06", "SYS11", "SYS07", "SYS15", "SYS02", "SYS10", "SYS26", "SYS21"],
    "reports": ["NISA-TP2"],
    "teams": ["T14", "T23", "T17", "T28", "T15", "T12"],
    "services": ["reserve-engine"],
}


def build_interfaces():
    out = []
    for num, name, src, tgt, proto, fmt, sched, progs, svcs, tbls, owner, crit, deps, ex in IFS:
        r = rng(f"world:interface:{num}")
        iid = f"CLX-IF-{num:03d}"
        rec = {
            "id": iid, "name": name, "source_system": src, "target_system": tgt, "protocol": proto, "format": fmt,
            "schedule": sched, "programs": progs, "services": svcs, "tables": tbls, "owner": owner, "criticality": crit,
            "depends_on": [f"CLX-IF-{d:03d}" for d in deps],
            "status": ex.get("status", "live"),
            "consumer_teams": ex.get("consumer_teams", []),
            "feeds_reports": ex.get("feeds_reports", []),
            "avg_daily_volume": ex.get("volume_per_day") or (f"≈{r.randint(2, 900) * 10:,} records" if "real-time" not in sched else f"≈{r.randint(5, 400) * 10:,} messages"),
            "since": ex.get("live_from") or ("1994-10-03" if src == "SYS01" and r.random() < 0.3 else f"{r.randint(2003, 2024)}-{r.randint(1, 12):02d}-01"),
        }
        for k in ("mq_max_depth", "mq_queue", "copybook", "jcl_job", "dataset", "kafka_topic", "schedule_history", "external_party",
                  "external_consumers", "note"):
            if k in ex:
                rec[k] = ex[k]
        if (src in ("SYS02", "SYS15") or tgt in ("SYS02", "SYS15")) and not ex.get("live_from"):
            rec["since"] = "2025-11-03"
        out.append(rec)
    return out

"""systems.yaml (hand-curated)."""
from __future__ import annotations


def _s(sid, name, aliases, typ, tech, lifecycle, owner, hosting, desc, renames=(), owner_history=None, **extra):
    rec = {"id": sid, "name": name, "aliases": list(aliases),
           "renames": [{"from_name": a, "to_name": b, "date": dt, "ticket": t} for a, b, dt, t in renames],
           "type": typ, "tech": tech, "lifecycle": lifecycle, "owner": owner,
           "owner_history": owner_history or [], "hosting": hosting, "description": desc}
    rec.update(extra)
    return rec


def build_systems():
    S = []
    S.append(_s("SYS01", "CLARA", ["the ledger", "CLR", "Claims Ledger", "Claims Ledger And Reserve Application", "CLARA mainframe"],
                "Core claims administration (legacy)", "COBOL, CICS TS, DB2 for z/OS (subsystem DB2P), IBM MQ, JCL batch",
                "legacy", "P016", "z/OS LPAR PRD1, Leeds Data Centre (LOC-LDC); DR on LPAR DRP1, Bristol DR Data Centre (LOC-BDC)",
                "Claims Ledger And Reserve Application. Built 1994 (go-live 1994-10-03). System of record for claims, reserves, "
                "fraud referrals, payments and recoveries until Claims Hub cut-over completes.",
                built="1994", go_live="1994-10-03", decommission_target="2027-09-30",
                cics_regions={"CICSPRD1": "online claims (FNOL, triage, assessment, reserving)",
                              "CICSPRD2": "fraud, settlement and recoveries"},
                db2_subsystem="DB2P", db2_plan="CLRPLAN1", mq_queue_manager="CLRQM01", batch_window="23:30–05:30 UK time"))
    S.append(_s("SYS02", "Claims Hub", ["CHUB", "the Hub", "Claims Hub platform"],
                "Core claims administration (target)", "Java 21 / Spring Boot microservices, PostgreSQL 16, Kafka, OpenShift",
                "target", "P017", "OpenShift cluster ocp-prd-lon1 (Corvane private cloud, London); DR cluster ocp-dr-lds1 (Leeds)",
                "Target claims platform built by Programme Skerry; 13 microservices. MVP live 2025-11-03; "
                "UK Wave 1 cut-over 2026-09-14; Wave 2 planned 2027-02-15.", go_live="2025-11-03"))
    S.append(_s("SYS03", "Sentinel", ["FRAUDNET", "FraudNet", "the fraud engine", "SNT"],
                "Fraud scoring engine", "Licensed scoring engine (gradient-boosted model SNT-4.2) with REST API; scores 0–100",
                "target", "P008", "Corvane private cloud VM cluster, Leeds Data Centre",
                "Scores every claim at FNOL/triage. Model owner Oskar Lindgren. Endpoint sentinel.corvane.internal "
                "(old alias fraudnet.corvane.internal retired 2025-03-31).",
                renames=[("FRAUDNET", "Sentinel", "2025-03-01", "CHUB-117")], vendor="VEN-15", model_version="SNT-4.2",
                model_calibrated="2026-03-16", model_auc=0.87, model_referral_share_pct=2.9, model_psi=0.06,
                model_validation={"by": "P007", "date": "2026-03-20", "result": "stable; recalibration due annually"}))
    S.append(_s("SYS04", "MyCorvane Claims", ["ClaimLine Web", "ClaimLine", "the customer portal", "claims portal"],
                "Customer self-service claims portal", "Java web application + mobile app front end",
                "target", "P029", "Corvane private cloud, London",
                "Customers notify and track claims online. Renamed from ClaimLine Web on 2024-10-14.",
                renames=[("ClaimLine Web", "MyCorvane Claims", "2024-10-14", None)]))
    S.append(_s("SYS05", "Evidence Vault", ["DOCSTOR", "DocStor", "the doc store", "EV"],
                "Document and image store", "Object storage with metadata index and retention engine",
                "target", "P032", "Corvane private cloud, Leeds",
                "Stores claim documents, photos and letters. Renamed from DOCSTOR on 2025-11-03.",
                renames=[("DOCSTOR", "Evidence Vault", "2025-11-03", "CHUB-276")]))
    S.append(_s("SYS06", "Group Ledger", ["GL", "GLD", "the general ledger"],
                "General ledger", "Packaged finance ERP general-ledger module (on-premise)", "target", "P021",
                "Corvane private cloud, London", "Group general ledger; receives reserve journals (CLX-IF-043) and payment postings."))
    S.append(_s("SYS07", "ReCede", ["RI system", "reinsurance system", "ReCede RI"],
                "Reinsurance administration", "Packaged reinsurance administration system", "target", "P038",
                "Vendor-hosted SaaS (UK region)", "Treaty administration, cession calculation and bordereaux."))
    S.append(_s("SYS08", "PALM", ["policy admin", "Policy Administration Ledger Manager", "PALM policy system"],
                "Policy administration", "Java/Oracle policy administration platform", "target", "P006",
                "Corvane private cloud, London", "Policy administration and rating; source of policy snapshots for claims."))
    S.append(_s("SYS09", "Corvane Payments Gateway", ["CPG", "payments gateway"],
                "Payments", "ISO 20022 payment hub (pain.001 / pain.002)", "target", "P035",
                "Corvane private cloud, Bristol", "Executes claim payments through Northmere Clearing Bank (VEN-11)."))
    S.append(_s("SYS10", "NISA Reporting Hub", ["NRH", "regulatory reporting hub", "the reporting hub"],
                "Regulatory reporting", "Reporting data mart and XML return generator", "target", "P020",
                "Corvane private cloud, London", "Produces NISA returns TP2, FR1 and CT1 and the annual filing."))
    S.append(_s("SYS11", "Claims Data Warehouse", ["CDW", "the warehouse", "claims DW"],
                "Data warehouse", "Columnar analytics database with nightly ELT", "target", "P036",
                "Corvane private cloud, Copenhagen", "Claims MI, reserve facts and actuarial extracts."))
    S.append(_s("SYS12", "Harbour CRM", ["Harbour", "the CRM", "contact centre CRM"],
                "CRM / contact centre", "Packaged CRM with telephony integration", "target", "P029",
                "Vendor-hosted SaaS (EU region)", "Contact centre desktop for telephone FNOL and customer contact."))
    S.append(_s("SYS13", "Evidence Intake Gateway", ["EIG", "photo intake", "telematics intake"],
                "Telematics and photo intake", "Event gateway for app photos and telematics crash alerts", "target", "P040",
                "OpenShift cluster ocp-prd-lon1", "Receives customer photos and telematics crash alerts; forwards to Evidence Vault and Claims Hub."))
    S.append(_s("SYS14", "MQ Backbone", ["MQ", "the MQ backbone", "CLRQM01"],
                "Messaging middleware", "IBM MQ queue managers CLRQM01 (z/OS) and HUBQM01 (distributed)", "legacy", "P031",
                "Leeds Data Centre and Corvane private cloud", "Point-to-point and file-to-message transport for CLARA interfaces.",
                decommission_target="2027-09-30"))
    S.append(_s("SYS15", "Event Streaming Platform", ["ESP", "Kafka", "the Kafka platform"],
                "Event streaming", "Apache Kafka on OpenShift (Strimzi operator), 6 brokers", "target", "P031",
                "OpenShift cluster ocp-prd-lon1", "Event backbone for Claims Hub (ADR-002)."))
    S.append(_s("SYS16", "Corvane Identity Service", ["CIS", "identity service", "SSO"],
                "Identity and access", "OIDC/OAuth2 identity provider", "target", "P032",
                "Corvane private cloud, London", "Workforce and partner identity (OIDC) for Claims Hub, Assessor Portal and portals."))
    S.append(_s("SYS17", "Assessor Portal", ["Adjuster Extranet", "the adjuster extranet", "assessor portal"],
                "Vendor assessor portal", "Web portal for internal and vendor Claims Assessors", "target", "P033",
                "Corvane private cloud, Leeds", "Instructions and reports exchanged with Claims Assessors. Renamed from "
                "Adjuster Extranet on 2025-09-01 to match the canonical term 'Claims Assessor'.",
                renames=[("Adjuster Extranet", "Assessor Portal", "2025-09-01", "CHUB-157")]))
    S.append(_s("SYS18", "Batch Scheduler", ["BSCH", "the scheduler", "batch scheduler"],
                "Workload scheduling", "Mainframe workload scheduler driving CLARA JCL", "legacy", "P026",
                "z/OS LPAR PRD1", "Runs the CLARA nightly, monthly, quarterly and year-end JCL jobs.", decommission_target="2027-09-30"))
    S.append(_s("SYS19", "WatchScreen", ["sanctions screening", "WatchScreen sanctions"],
                "Sanctions screening", "Packaged sanctions/PEP screening service", "target", "P037",
                "Vendor-hosted SaaS (UK region)", "Screens payees before any claim payment (BR-STL-007)."))
    S.append(_s("SYS20", "Vehicle Data Service", ["VDS", "vehicle lookup"],
                "Vehicle data lookup", "External vehicle registration lookup via REST", "target", "P040",
                "External SaaS", "Vehicle details for motor FNOL in UK and Nordics."))
    S.append(_s("SYS21", "Actuarial Reserving Workbench", ["ARW", "reserving workbench", "the triangles tool"],
                "Actuarial reserving", "Actuarial modelling workbench (chain-ladder, Bornhuetter-Ferguson)", "target", "P009",
                "Corvane private cloud, London", "Monthly IBNR run from reserve triangles (CLX-IF-058).",
                owner_history=[{"person": "P010", "from": "2016-01-01", "to": "2025-08-31"}, {"person": "P009", "from": "2025-09-01", "to": None}]))
    S.append(_s("SYS22", "SIU Case Manager", ["SCM", "SIU case system"],
                "Fraud case management", "Case management application", "target", "P028",
                "Corvane private cloud, Leeds", "SIU investigation cases created from fraud referrals."))
    S.append(_s("SYS23", "SKADE-90", ["SKADE90", "the Nordic legacy claims system"],
                "Nordic claims administration (retired)", "Unix / 4GL", "retired", "P012", "decommissioned",
                "Former Nordic claims system; claims migrated into CLARA, retired 2024-05-31.", retired_on="2024-05-31"))
    S.append(_s("SYS24", "Subrogation Tracker", ["SUBTRAK", "the subro tracker"],
                "Recovery case tracking", "Departmental client-server application on SQL database", "retiring", "P013",
                "Corvane private cloud, Bristol", "Tracks subrogation demands and receipts; replaced by recovery-svc, retirement target 2026-12-31.",
                owner_history=[{"person": "P015", "from": "2016-03-01", "to": "2024-12-31"},
                               {"person": "P014", "from": "2025-01-01", "to": "2025-08-31"},
                               {"person": "P013", "from": "2025-09-01", "to": None}],
                decommission_target="2026-12-31"))
    S.append(_s("SYS25", "Notify", ["the notification gateway", "Notify gateway"],
                "Customer communications", "Omnichannel gateway (letters, SMS, email)", "target", "P040",
                "Vendor-hosted SaaS (UK region)", "Sends acknowledgements, fraud-referral notices and recovery letters."))
    S.append(_s("SYS26", "Bordereaux Exchange", ["the bordereaux SFTP", "BX"],
                "External reinsurer exchange", "Managed SFTP exchange with reinsurers", "target", "P038",
                "Vendor-hosted managed SFTP", "Monthly claims bordereaux to Brynholt Re and Calderbank Re (CLX-IF-055)."))
    S.append(_s("SYS27", "Mailroom Scanning", ["MRS", "the scanning bureau"],
                "Inbound post scanning", "Scanning bureau with OCR and SFTP delivery", "retiring", "P029",
                "Leeds (on premise)", "Scans inbound post into Evidence Vault; retirement target 2027-03-31.",
                decommission_target="2027-03-31"))
    return S

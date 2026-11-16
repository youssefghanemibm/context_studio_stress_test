"""XLSX workbooks ST007-ST012."""
from __future__ import annotations

import datetime as dt
import re

from openpyxl.worksheet.datavalidation import DataValidation

from . import claims as C
from .common import (D, W, adate, approvers_for, colleagues_of, doc_control_sheet, iso, may, new_workbook, pick,
                     placement, pname, print_setup, ptitle, require, rng, set_props, set_widths, svcname, sysname,
                     team_name, temporalize, text_rules_known, write_header, write_title, xl_styles)
from .xlsx_a import dtype, save, st001_columns

# =============================================================================================
# ST007 Data Migration Mapping Workbook (2025-06-16)
# =============================================================================================

TABLE_TARGET = {
    "CLR.T_CLAIM": "claim_core.claim", "CLR.T_CLAIMANT": "claim_core.party", "CLR.T_FNOL_EVENT": "fnol.notification",
    "CLR.T_TRIAGE": "triage.triage_decision", "CLR.T_CLAIM_TIER": "triage.triage_decision",
    "CLR.T_FRAUD_SCORE": "triage.triage_decision", "CLR.T_ASSESSMENT": "assessment.assessment",
    "CLR.T_ASSESSOR_ASSIGNMENT": "assessment.assessor_assignment", "CLR.T_RESERVE": "reserve.reserve",
    "CLR.T_RESERVE_MOVEMENT": "reserve.reserve_movement", "CLR.T_FRAUD_REFERRAL": "fraud.referral",
    "CLR.T_SETTLEMENT": "settlement.settlement", "CLR.T_PAYMENT": "payment.payment_instruction",
    "CLR.T_SUBROGATION_CASE": "recovery.recovery_case", "CLR.T_RECOVERY": "recovery.receipt",
    "CLR.T_DOCUMENT_REF": "document.document", "CLR.T_GL_POSTING": "gl.journal_line",
    "CLR.T_NISA_RETURN": "reporting.return_extract", "CLR.T_PAYEE": "payment.payment_instruction",
}
CLAIM_ID_RULE = "Reformat <region><yyyy><6 digits> to CLM-<region>-<yyyy>-<6 digits>"
COLMAP = {
    ("CLR.T_CLAIM", "CLAIM_ID"): ("claim_id", "Transform", CLAIM_ID_RULE + "; original value also loaded to legacy_claim_id"),
    ("CLR.T_CLAIM", "POLICY_NO"): ("policy_no", "Direct", ""),
    ("CLR.T_CLAIM", "PRODUCT_CD"): ("product_code", "Transform", "Product code to product id via product catalogue (e.g. MOTUK -> PRD-MOT-UK)"),
    ("CLR.T_CLAIM", "PERIL_CD"): ("claim_type", "Transform", "Peril code to claim type id (e.g. COL -> CT-COL)"),
    ("CLR.T_CLAIM", "LOSS_DT"): ("loss_date", "Direct", ""),
    ("CLR.T_CLAIM", "NOTIFIED_TS"): ("notified_at", "Transform", "Local time to UTC timestamp"),
    ("CLR.T_CLAIM", "CLAIM_STATUS"): ("status", "Code map", "See Code Mapping sheet"),
    ("CLR.T_CLAIM", "TIER_CD"): ("tier", "Transform", "CHAR(1) to SMALLINT"),
    ("CLR.T_CLAIM", "REGION_CD"): ("region", "Direct", ""),
    ("CLR.T_CLAIM", "CURRENCY_CD"): ("currency", "Direct", ""),
    ("CLR.T_CLAIM", "HANDLER_USER_ID"): ("handler_id", "Lookup", "CLARA user id to workforce identity"),
    ("CLR.T_CLAIM", "CHANNEL_CD"): ("fnol.notification.channel", "Code map", "See Code Mapping sheet"),
    ("CLR.T_CLAIM", "ASSESSOR_ID"): ("assessment.assessor_assignment.claims_assessor_id", "Direct", "Latest assignment only"),
    ("CLR.T_CLAIM", "CLAIMANT_ID"): ("claim_core.party.party_id", "Lookup", "Generate party UUID; keep CLARA id in migration key table"),
    ("CLR.T_CLAIMANT", "CLAIMANT_ID"): ("party_id", "Lookup", "Generated UUID (key table)"),
    ("CLR.T_CLAIMANT", "FAMILY_NAME"): ("family_name", "Direct", "PII"),
    ("CLR.T_CLAIMANT", "GIVEN_NAME"): ("given_name", "Direct", "PII"),
    ("CLR.T_CLAIMANT", "EMAIL_ADDR"): ("email", "Direct", "PII"),
    ("CLR.T_CLAIMANT", "PHONE_NO"): ("phone", "Transform", "Normalise to E.164; PII"),
    ("CLR.T_CLAIMANT", "PARTY_ROLE_CD"): ("role", "Code map", "See Code Mapping sheet"),
    ("CLR.T_FNOL_EVENT", "FNOL_ID"): ("fnol_id", "Lookup", "Generated UUID"),
    ("CLR.T_FNOL_EVENT", "CLAIM_ID"): ("claim_id", "Transform", CLAIM_ID_RULE),
    ("CLR.T_FNOL_EVENT", "CHANNEL_CD"): ("channel", "Code map", "See Code Mapping sheet"),
    ("CLR.T_FNOL_EVENT", "RECEIVED_TS"): ("received_at", "Transform", "Local time to UTC timestamp"),
    ("CLR.T_FNOL_EVENT", "ACK_SENT_TS"): ("ack_sent_at", "Transform", "Local time to UTC timestamp"),
    ("CLR.T_FNOL_EVENT", "PAYLOAD_REF"): ("payload", "Transform", "Fetch archived payload and store as JSON"),
    ("CLR.T_TRIAGE", "CLAIM_ID"): ("claim_id", "Transform", CLAIM_ID_RULE),
    ("CLR.T_TRIAGE", "ROUTE_CD"): ("route", "Code map", "See Code Mapping sheet"),
    ("CLR.T_TRIAGE", "TRIAGE_TS"): ("decided_at", "Transform", "Latest triage row only"),
    ("CLR.T_CLAIM_TIER", "TIER_CD"): ("tier", "Transform", "Current tier row only; CHAR(1) to SMALLINT"),
    ("CLR.T_FRAUD_SCORE", "SCORE"): ("sentinel_score", "Direct", "Latest score per claim"),
    ("CLR.T_ASSESSMENT", "ASSESS_ID"): ("assessment_id", "Lookup", "Generated UUID"),
    ("CLR.T_ASSESSMENT", "CLAIM_ID"): ("claim_id", "Transform", CLAIM_ID_RULE),
    ("CLR.T_ASSESSMENT", "ASSESS_TYPE_CD"): ("type", "Code map", "See Code Mapping sheet"),
    ("CLR.T_ASSESSMENT", "ESTIMATE_AMT"): ("estimate_amount", "Direct", ""),
    ("CLR.T_ASSESSMENT", "COVER_DECISION_CD"): ("cover_decision", "Code map", "See Code Mapping sheet"),
    ("CLR.T_ASSESSOR_ASSIGNMENT", "ASSIGN_ID"): ("assignment_id", "Lookup", "Generated UUID"),
    ("CLR.T_ASSESSOR_ASSIGNMENT", "CLAIM_ID"): ("claim_id", "Transform", CLAIM_ID_RULE),
    ("CLR.T_ASSESSOR_ASSIGNMENT", "ASSESSOR_ID"): ("claims_assessor_id", "Direct", ""),
    ("CLR.T_ASSESSOR_ASSIGNMENT", "VENDOR_CD"): ("vendor_code", "Direct", ""),
    ("CLR.T_ASSESSOR_ASSIGNMENT", "SLA_DUE_DT"): ("sla_due", "Direct", ""),
    ("CLR.T_RESERVE", "RSV_ID"): ("reserve_id", "Lookup", "Generated UUID (key table)"),
    ("CLR.T_RESERVE", "CLAIM_ID"): ("claim_id", "Transform", CLAIM_ID_RULE),
    ("CLR.T_RESERVE", "RSV_TYPE_CD"): ("reserve_type", "Code map", "See Code Mapping sheet"),
    ("CLR.T_RESERVE", "CURRENCY_CD"): ("currency", "Direct", ""),
    ("CLR.T_RESERVE", "RSV_OUTSTANDING_AMT"): ("outstanding_amount", "Direct", "Reconciled per product after load"),
    ("CLR.T_RESERVE", "RSV_GBP_EQUIV_AMT"): ("gbp_equivalent", "Direct", ""),
    ("CLR.T_RESERVE", "RSV_NEXT_REVIEW_DT"): ("next_review_date", "Direct", ""),
    ("CLR.T_RESERVE", "RSV_STATUS"): ("status", "Code map", "See Code Mapping sheet"),
    ("CLR.T_RESERVE_MOVEMENT", "MOVE_ID"): ("movement_id", "Lookup", "Generated UUID"),
    ("CLR.T_RESERVE_MOVEMENT", "RSV_ID"): ("reserve_id", "Lookup", "Via reserve key table"),
    ("CLR.T_RESERVE_MOVEMENT", "MOVE_TYPE_CD"): ("movement_type", "Code map", "See Code Mapping sheet"),
    ("CLR.T_RESERVE_MOVEMENT", "MOVE_AMT"): ("amount_minor", "Transform", "Multiply by 100 to minor units (pence/ore)"),
    ("CLR.T_RESERVE_MOVEMENT", "MOVE_TS"): ("created_at", "Transform", "Local time to UTC timestamp"),
    ("CLR.T_FRAUD_REFERRAL", "REF_ID"): ("referral_id", "Lookup", "Generated UUID"),
    ("CLR.T_FRAUD_REFERRAL", "CLAIM_ID"): ("claim_id", "Transform", CLAIM_ID_RULE),
    ("CLR.T_FRAUD_REFERRAL", "REF_SCORE"): ("sentinel_score", "Direct", ""),
    ("CLR.T_FRAUD_REFERRAL", "REF_THRESHOLD_APPLIED"): ("threshold_applied", "Direct", ""),
    ("CLR.T_FRAUD_REFERRAL", "TIER_CD"): ("tier", "Transform", "CHAR(1) to SMALLINT"),
    ("CLR.T_FRAUD_REFERRAL", "REF_TS"): ("referred_at", "Transform", "Local time to UTC timestamp"),
    ("CLR.T_FRAUD_REFERRAL", "SIU_CASE_ID"): ("siu_case_id", "Direct", ""),
    ("CLR.T_FRAUD_REFERRAL", "RULE_ID"): ("rule_id", "Direct", ""),
    ("CLR.T_SETTLEMENT", "SETTLE_ID"): ("settlement_id", "Lookup", "Generated UUID"),
    ("CLR.T_SETTLEMENT", "CLAIM_ID"): ("claim_id", "Transform", CLAIM_ID_RULE),
    ("CLR.T_SETTLEMENT", "OFFER_AMT"): ("offer_amount", "Direct", ""),
    ("CLR.T_SETTLEMENT", "EXCESS_APPLIED_AMT"): ("excess_applied", "Direct", ""),
    ("CLR.T_SETTLEMENT", "FINAL_FLAG"): ("final", "Transform", "Y/N to boolean"),
    ("CLR.T_SETTLEMENT", "ACCEPTED_DT"): ("agreed_at", "Transform", "Date to timestamp (00:00 UTC)"),
    ("CLR.T_PAYMENT", "PAY_ID"): ("payment_id", "Lookup", "Generated UUID"),
    ("CLR.T_PAYMENT", "CLAIM_ID"): ("claim_id", "Transform", CLAIM_ID_RULE),
    ("CLR.T_PAYMENT", "PAY_AMT"): ("amount", "Direct", ""),
    ("CLR.T_PAYMENT", "CURRENCY_CD"): ("currency", "Direct", ""),
    ("CLR.T_PAYMENT", "PAY_STATUS"): ("status", "Code map", "See Code Mapping sheet"),
    ("CLR.T_PAYEE", "IBAN"): ("payee_iban", "Direct", "Open payments only"),
    ("CLR.T_SUBROGATION_CASE", "SUBRO_CASE_ID"): ("case_id", "Lookup", "Generated UUID"),
    ("CLR.T_SUBROGATION_CASE", "CLAIM_ID"): ("claim_id", "Transform", CLAIM_ID_RULE),
    ("CLR.T_SUBROGATION_CASE", "CASE_STATUS"): ("status", "Code map", "See Code Mapping sheet"),
    ("CLR.T_SUBROGATION_CASE", "SUBTRAK_REF"): ("subtrak_ref", "Direct", ""),
    ("CLR.T_RECOVERY", "RCV_ID"): ("receipt_id", "Lookup", "Generated UUID"),
    ("CLR.T_RECOVERY", "SUBRO_CASE_ID"): ("case_id", "Lookup", "Via case key table"),
    ("CLR.T_RECOVERY", "RCV_RECEIVED_AMT"): ("amount", "Direct", ""),
    ("CLR.T_RECOVERY", "RCV_EXPECTED_AMT"): ("recovery.recovery_case.expected_amount", "Direct", "Summed per case"),
    ("CLR.T_DOCUMENT_REF", "DOC_REF_ID"): ("document_id", "Lookup", "Generated UUID"),
    ("CLR.T_DOCUMENT_REF", "CLAIM_ID"): ("claim_id", "Transform", CLAIM_ID_RULE),
    ("CLR.T_DOCUMENT_REF", "VAULT_OBJECT_ID"): ("vault_object_id", "Direct", ""),
    ("CLR.T_DOCUMENT_REF", "DOC_TYPE_CD"): ("doc_type", "Code map", "See Code Mapping sheet"),
    ("CLR.T_DOCUMENT_REF", "RECEIVED_TS"): ("stored_at", "Transform", "Local time to UTC timestamp"),
    ("CLR.T_GL_POSTING", "GL_PERIOD"): ("period", "Direct", ""),
    ("CLR.T_GL_POSTING", "ACCOUNT_CD"): ("account", "Direct", ""),
    ("CLR.T_GL_POSTING", "AMOUNT_GBP"): ("amount_gbp", "Transform", "Sign from DR_CR"),
    ("CLR.T_NISA_RETURN", "RETURN_CD"): ("return_code", "Direct", ""),
    ("CLR.T_NISA_RETURN", "PERIOD_CD"): ("period", "Direct", ""),
}
NOT_MIGRATED_TABLES = {
    "CLR.T_PARAM": "Reference data - re-created as service configuration",
    "CLR.T_CODE_LOOKUP": "Reference data - re-created as service configuration",
    "CLR.T_USER": "Replaced by workforce identity",
    "CLR.T_AUDIT": "Archive only",
    "CLR.T_INTERFACE_LOG": "Technical - not migrated",
    "CLR.T_REPORT_RUN": "Technical - not migrated",
    "CLR.T_GL_PERIOD": "Owned by Group Ledger - not migrated",
    "CLR.T_CURRENCY_RATE": "Owned by Group Ledger - not migrated",
    "CLR.T_REINSURANCE_CESSION": "Owned by ReCede - not migrated",
    "CLR.T_SIU_CASE": "Owned by SIU Case Manager - not migrated",
    "CLR.T_POLICY_SNAPSHOT": "Policy data read live from PALM",
}


def build_st007(ctx):
    fid = "ST007"
    d = adate(fid)
    a = W.anchor(fid)
    S = xl_styles()
    wb = new_workbook()
    set_props(wb, fid, subject="CLARA to Claims Hub column mapping")
    doc_control_sheet(wb, fid,
                      purpose="Source-to-target column mapping from the CLARA DB2 tables to the Claims Hub PostgreSQL tables, used to build and test the migration loads.",
                      scope="All CLARA DB2 tables in schema CLR. Each source column has a disposition: Direct, Transform, Code map, Lookup, Derived or Not migrated.",
                      approvers=approvers_for(fid, ["P036"]), colleagues=["P049", "P052", "P054"],
                      sources=["CLARA data dictionary", "Claims Hub service data models"])
    ws = wb.create_sheet("Column Mapping")
    write_title(ws, "Column Mapping - CLARA to Claims Hub", f"As at {iso(d)}.")
    hdr = ["Map ID", "Source table", "Source column", "Source type", "Target table", "Target column", "Target type",
           "Disposition", "Transformation / rationale", "Owning service", "PII"]
    write_header(ws, 4, hdr)
    pg = {n: t for n, t in W.tables.items() if t["db"] == "PostgreSQL"}
    r = 5
    k = 0
    rows_by = {}
    target_cov: dict[tuple[str, str], list[str]] = {}
    for tn, t in W.tables.items():
        if t["db"] != "DB2" or (t.get("created") and t["created"] > iso(d)):
            continue
        tgt_t = TABLE_TARGET.get(tn)
        for c in st001_columns(tn, d):
            k += 1
            key = (tn, c["name"])
            target_table = target_col = target_type = owner = ""
            if key in COLMAP:
                tc, disp, rule = COLMAP[key]
                if tc.count(".") == 2:
                    target_table, target_col = tc.rsplit(".", 1)
                else:
                    target_table, target_col = tgt_t, tc
                pt = pg[target_table]
                pc = next((x for x in pt["columns"] if x["name"] == target_col), None)
                target_type = dtype(pc) if pc else ""
                owner = svcname(pt["owning_service"], d)
                target_cov.setdefault((target_table, target_col), []).append(f"{tn}.{c['name']}")
            elif c["name"].startswith("LAST_UPD") or c["name"] in ("VERSION_NO", "CREATED_TS", "ARCHIVE_FLAG", "EXT_REF", "BATCH_RUN_ID"):
                disp, rule = "Not migrated", "Technical column"
            elif tn in NOT_MIGRATED_TABLES:
                disp, rule = "Not migrated", NOT_MIGRATED_TABLES[tn]
            elif tgt_t:
                disp, rule = ("Derived", "Derived in target from related records") if c["name"].endswith(("_FLAG", "_DT")) else (
                    "Not migrated", "No equivalent in target model; retained in archive")
            else:
                disp, rule = "Not migrated", "Archive only"
            vals = [f"MAP-{k:04d}", tn, c["name"], dtype(c), target_table, target_col, target_type, disp,
                    temporalize(rule, d), owner, "Y" if c["pii"] else ""]
            for j, v in enumerate(vals, 1):
                cc = ws.cell(row=r, column=j, value=v)
                if j == 9:
                    cc.alignment = S["wrap"]
            rows_by[key] = r
            r += 1
    last = r - 1
    ws.auto_filter.ref = f"A4:K{last}"
    ws.freeze_panes = "D5"
    dv = DataValidation(type="list", formula1='"Direct,Transform,Code map,Lookup,Derived,Not migrated"', allow_blank=False)
    dv.add(f"H5:H{last}")
    ws.add_data_validation(dv)
    set_widths(ws, [10, 26, 24, 14, 30, 26, 14, 12, 56, 20, 5])
    print_setup(ws, fid)

    wt = wb.create_sheet("Target Coverage")
    write_title(wt, "Target coverage - Claims Hub columns and their CLARA sources")
    write_header(wt, 3, ["Target table", "Target column", "Target type", "Owning service", "CLARA source(s)", "Note"])
    rr = 4
    for tn, t in pg.items():
        if tn == "fraud.customer_notice":
            continue  # not yet designed at this date
        for c in t["columns"]:
            srcs = target_cov.get((tn, c["name"]), [])
            note = "" if srcs else ("Generated in target" if c["name"].endswith("_id") else "Populated by the service after cut-over")
            if tn == "claim_core.claim" and c["name"] == "legacy_claim_id":
                srcs, note = ["CLR.T_CLAIM.CLAIM_ID"], "Copied unchanged"
            for j, v in enumerate([tn, c["name"], dtype(c), svcname(t["owning_service"], d), ", ".join(srcs), note], 1):
                wt.cell(row=rr, column=j, value=v)
            rr += 1
    set_widths(wt, [28, 22, 14, 20, 40, 34])
    print_setup(wt, fid)

    wcm = wb.create_sheet("Code Mapping")
    write_title(wcm, "Code value mapping")
    write_header(wcm, 3, ["Source column", "CLARA code", "Meaning", "Claims Hub value"])
    rr = 4
    maps = [("CHANNEL_CD", [("PH", "phone", "PHONE"), ("WB", "portal", "PORTAL"), ("AP", "app", "APP"),
                            ("BR", "broker", "BROKER"), ("TL", "telematics", "TELEMATICS")]),
            ("CLAIM_STATUS", [("OP", "open", "OPEN"), ("CS", "closed-settled", "CLOSED_SETTLED"),
                              ("CN", "closed-nil", "CLOSED_NIL"), ("RO", "reopened", "REOPENED"),
                              ("RC", "in recovery", "IN_RECOVERY")]),
            ("RSV_TYPE_CD", [("ID", "indemnity", "INDEMNITY"), ("EX", "expense", "EXPENSE"), ("LG", "legal", "LEGAL")]),
            ("RSV_STATUS", [("O", "open", "OPEN"), ("C", "closed", "CLOSED")]),
            ("MOVE_TYPE_CD", [("IN", "initial", "INITIAL"), ("AD", "adjustment", "ADJUSTMENT"), ("IX", "indexation", "INDEXATION"),
                              ("RV", "review", "REVIEW"), ("ST", "settlement close", "SETTLEMENT_CLOSE"), ("RC", "recovery", "RECOVERY")]),
            ("PAY_STATUS", [("RQ", "requested", "REQUESTED"), ("SC", "screened", "SCREENED"), ("SN", "sent", "SENT"),
                            ("CF", "confirmed", "CONFIRMED"), ("CX", "cancelled", "CANCELLED")])]
    for col, vals in maps:
        for code, meaning, tgt in vals:
            for j, v in enumerate([col, code, meaning, tgt], 1):
                wcm.cell(row=rr, column=j, value=v)
            rr += 1
    set_widths(wcm, [16, 12, 20, 20])
    save(ctx, wb, fid)

    ctx.xfact(fid, "Column Mapping", f"F{rows_by[('CLR.T_RESERVE', 'RSV_OUTSTANDING_AMT')]}", "outstanding_amount",
              "Mapping: CLR.T_RESERVE.RSV_OUTSTANDING_AMT -> reserve.reserve.outstanding_amount (Direct).",
              kind="needle", world_ref="TABLE:reserve.reserve#columns.outstanding_amount", also_in=[])
    ctx.xfact(fid, "Column Mapping", f"F{rows_by[('CLR.T_FRAUD_REFERRAL', 'REF_SCORE')]}", "sentinel_score",
              "Mapping: CLR.T_FRAUD_REFERRAL.REF_SCORE -> fraud.referral.sentinel_score (Direct).",
              kind="needle", world_ref="TABLE:fraud.referral#columns.sentinel_score")
    ctx.xfact(fid, "Column Mapping", f"J{rows_by[('CLR.T_RESERVE', 'RSV_OUTSTANDING_AMT')]}", "reserve-svc",
              "In the 2025-06-16 mapping workbook the reserve tables are owned by reserve-svc (renamed reserve-engine on 2026-02-10).",
              kind="temporal", world_ref="SERVICE:reserve-engine#renames")
    ctx.xfact(fid, "Column Mapping", f"I{rows_by[('CLR.T_RESERVE_MOVEMENT', 'MOVE_AMT')]}", "minor units",
              "Mapping: CLR.T_RESERVE_MOVEMENT.MOVE_AMT -> reserve.reserve_movement.amount_minor, multiplied by 100 to minor units.",
              world_ref="TABLE:reserve.reserve_movement#columns.amount_minor")
    ctx.xfact(fid, "Column Mapping", f"I{rows_by[('CLR.T_CLAIM', 'CLAIM_ID')]}", "CLM-<region>-<yyyy>-<6 digits>",
              "Mapping: CLR.T_CLAIM.CLAIM_ID is reformatted to CLM-<region>-<yyyy>-<6 digits>; the original goes to legacy_claim_id.",
              world_ref="TABLE:claim_core.claim#columns.legacy_claim_id")
    ctx.done(fid, f"4 sheets, {last - 4} source columns")


# =============================================================================================
# ST008 Wave 1 Test Results (2026-09-10)
# =============================================================================================

W1_SERVICES = ["fnol-intake-svc", "triage-svc", "assessment-svc", "claim-core-svc", "reserve-engine",
               "fraud-referral-svc", "settlement-svc", "payment-orchestrator", "recovery-svc", "document-svc",
               "notification-svc", "gl-posting-svc", "reporting-feed-svc", "Integration", "Data Migration"]
MOTOR_CT = ["CT-COL", "CT-THF", "CT-WSC", "CT-FIR", "CT-VAN", "CT-BIJ", "CT-TPD"]
CHANNELS = ["phone", "portal", "app", "broker", "telematics"]
SCEN = {
    "fnol-intake-svc": ["Submit FNOL via {ch} for {ctn} claim", "Reject FNOL with missing policy number ({ch})",
                        "Duplicate FNOL detection for {ctn} claim", "FNOL with late notification flag ({ch})"],
    "triage-svc": ["Tier classification for {ctn} claim per {rule_tri}", "Sentinel pre-screen call for {ctn} claim",
                   "Route {ctn} claim to handler queue", "Major loss alert raised for {ctn} claim"],
    "assessment-svc": ["Appoint Claims Assessor for {ctn} claim", "Desk assessment outcome recorded ({ctn})",
                       "Assessor report received from Assessor Portal ({ctn})"],
    "claim-core-svc": ["Create claim record for {ctn} claim", "Update claim status to closed-settled ({ctn})",
                       "Party details captured for {ctn} claim"],
    "reserve-engine": ["Default reserve created at FNOL ({ctn})", "Reserve adjustment with authority check ({ctn})",
                       "Tier-3 review date set per {rule_rsv}", "Reserve movement event published ({ctn})"],
    "fraud-referral-svc": ["Referral created when score meets {rule_frd} ({ctn})", "No referral below threshold ({ctn})",
                           "Customer notice due date set per BR-FRD-032 ({ctn})"],
    "settlement-svc": ["Settlement offer recorded for {ctn} claim", "Excess applied on settlement ({ctn})",
                       "Final settlement closes reserve ({ctn})"],
    "payment-orchestrator": ["Payment instruction sent to CPG ({ctn})", "Payment confirmation processed ({ctn})",
                             "Sanctions screening result handled ({ctn})"],
    "recovery-svc": ["Recovery case opened for {ctn} claim", "Recovery receipt recorded ({ctn})"],
    "document-svc": ["Document stored in Evidence Vault ({ctn})", "Document retrieval by claim ({ctn})"],
    "notification-svc": ["FNOL acknowledgement sent ({ch})", "Customer letter generated ({ctn})"],
    "gl-posting-svc": ["Payment journal posted to Group Ledger ({ctn})", "Recovery income journal posted ({ctn})"],
    "reporting-feed-svc": ["Regulatory extract row produced for {ctn} claim"],
    "Integration": ["CLX-IF-038 payment round trip ({ctn})", "CLX-IF-035 portal FNOL round trip ({ch})",
                    "CLX-IF-050 journal delivery ({ctn})", "CLX-IF-036 Sentinel scoring call ({ctn})"],
    "Data Migration": ["Migrated {ctn} claim header reconciles to CLARA", "Migrated reserves reconcile for {ctn} claims",
                       "Migrated open payments reconcile ({ctn})"],
}
CYCLES = [("SIT-1", "2026-06-15", "2026-07-10", 0.78, 1.0), ("SIT-2", "2026-07-13", "2026-08-07", 0.88, 0.65),
          ("UAT", "2026-08-10", "2026-08-28", 0.93, 0.85), ("REG", "2026-08-31", "2026-09-09", 0.97, 0.80)]


def build_st008(ctx):
    fid = "ST008"
    d = adate(fid)
    a = W.anchor(fid)
    r = rng(f"{fid}:tests")
    wb = new_workbook()
    set_props(wb, fid, subject="Wave 1 (UK motor) test execution results")
    in_force = set(W.rules_in_force(iso(d)))

    def pick_rule(area):
        ids = sorted(x for x in in_force if x.startswith(f"BR-{area}-"))
        return r.choice(ids) if ids else f"BR-{area}"

    cases = []
    n = 0
    while len(cases) < 320:
        svc = W1_SERVICES[n % len(W1_SERVICES)]
        tpl = r.choice(SCEN[svc])
        ct = r.choice(MOTOR_CT)
        title = tpl.format(ch=r.choice(CHANNELS), ctn=W.claim_types[ct]["name"].lower(), rule_tri=pick_rule("TRI"),
                           rule_rsv=pick_rule("RSV"), rule_frd=pick_rule("FRD"))
        n += 1
        if any(c[1] == title for c in cases):
            continue
        cases.append((f"W1-TC-{len(cases) + 1:04d}", title, svc, ct))
    testers_by = {"fnol-intake-svc": ["P040", "P053"], "triage-svc": ["P040", "P054"], "assessment-svc": ["P040", "P054"],
                  "claim-core-svc": ["P040", "P053"], "reserve-engine": ["P041", "P053"], "gl-posting-svc": ["P041", "P053"],
                  "fraud-referral-svc": ["P042", "P054"], "settlement-svc": ["P042", "P054"],
                  "payment-orchestrator": ["P042", "P053"], "recovery-svc": ["P042", "P054"],
                  "document-svc": ["P040", "P054"], "notification-svc": ["P040", "P054"], "reporting-feed-svc": ["P053"],
                  "Integration": ["P050", "P053"], "Data Migration": ["P054", "P053"]}
    testers_uat = ["P044", "P045", "P054"]
    execs = []
    defects = []
    failed_prev = set()
    for cyc, a0, a1, pr, share in CYCLES:
        d0, d1 = D(a0), D(a1)
        span = (d1 - d0).days
        for cid, title, svc, ct in cases:
            if cyc != "SIT-1" and cid not in failed_prev and r.random() > share:
                continue
            ed = d0 + dt.timedelta(days=r.randint(0, span))
            while ed.weekday() >= 5:
                ed -= dt.timedelta(days=1)
            if ed < d0:
                ed = d0 + dt.timedelta(days=(7 - d0.weekday()) % 7)
            x = r.random()
            status = "Passed" if x < pr else ("Failed" if x < pr + (1 - pr) * 0.75 else "Blocked")
            tester = r.choice(testers_uat if cyc == "UAT" else testers_by[svc])
            if not W.employed(tester, iso(ed)):
                tester = "P053"
            defect = ""
            if status == "Failed":
                sev = "Sev1" if r.random() < 0.02 and cyc in ("SIT-1", "SIT-2") else C.wchoice(r, ["Sev2", "Sev3", "Sev4"], [0.22, 0.62, 0.16])
                did = f"DEF-W1-{len(defects) + 1:04d}"
                defect = did
                defects.append([did, f"{title} - unexpected result", sev, svc, cid, cyc, ed])
            execs.append([f"EX-{len(execs) + 1:05d}", cid, title, svc, ct, cyc, ed, status, pname(tester, ed), defect])
        failed_prev = {e[1] for e in execs if e[5] == cyc and e[7] != "Passed"}
    # defect status at the report date: older and lower-severity defects mostly closed; no open Sev1
    dstat = []
    for did, title, sev, svc, cid, cyc, ed in defects:
        age = (d - ed).days
        if sev == "Sev1":
            st = "Closed"
        else:
            st = "Closed" if r.random() < min(0.95, 0.25 + age / 70) else ("Deferred" if sev == "Sev4" and r.random() < 0.4 else "Open")
        dstat.append([did, title, sev, st, svc, cid, cyc, ed])
    open_by = {s: sum(1 for x in dstat if x[2] == s and x[3] == "Open") for s in ("Sev1", "Sev2", "Sev3", "Sev4")}

    doc_control_sheet(wb, fid,
                      purpose="Execution results for Wave 1 (UK motor, PRD-MOT-UK) system integration, user acceptance and regression testing ahead of the 2026-09-14 cut-over.",
                      scope="Claims Hub services, integrations and data migration in Wave 1 scope. Results to 2026-09-09.",
                      approvers=approvers_for(fid, ["P017"]), colleagues=["P054", "P049", "P048"],
                      sources=["Test management tool export"],
                      extra=[("Open defects at report date", f"Sev1 {open_by['Sev1']}, Sev2 {open_by['Sev2']}, Sev3 {open_by['Sev3']}, Sev4 {open_by['Sev4']}")])
    ws = wb.create_sheet("Test Results")
    write_title(ws, "Wave 1 Test Results", "One row per test execution.")
    hdr = ["Execution ID", "Test case", "Title", "Component", "Claim type", "Cycle", "Executed on", "Result", "Tester", "Defect"]
    write_header(ws, 4, hdr)
    rr = 5
    for e in execs:
        for j, v in enumerate(e, 1):
            c = ws.cell(row=rr, column=j, value=v)
            if isinstance(v, dt.date):
                c.number_format = "yyyy-mm-dd"
        rr += 1
    last = rr - 1
    ws.auto_filter.ref = f"A4:J{last}"
    ws.freeze_panes = "C5"
    dv = DataValidation(type="list", formula1='"Passed,Failed,Blocked,Not Run"', allow_blank=False)
    dv.add(f"H5:H{last}")
    ws.add_data_validation(dv)
    set_widths(ws, [11, 12, 58, 20, 9, 8, 12, 9, 22, 12])
    print_setup(ws, fid)

    wd = wb.create_sheet("Defects")
    write_title(wd, "Wave 1 defects", f"Status at {iso(d)}.")
    write_header(wd, 4, ["Defect", "Title", "Severity", "Status", "Component", "Test case", "Cycle", "Raised"])
    rr = 5
    for x in dstat:
        for j, v in enumerate(x, 1):
            c = wd.cell(row=rr, column=j, value=v)
            if isinstance(v, dt.date):
                c.number_format = "yyyy-mm-dd"
        rr += 1
    wd.auto_filter.ref = f"A4:H{rr - 1}"
    set_widths(wd, [12, 60, 8, 9, 20, 12, 8, 12])

    wsm = wb.create_sheet("Summary")
    write_title(wsm, "Results by cycle")
    write_header(wsm, 3, ["Cycle", "Executed", "Passed", "Failed", "Blocked", "Pass rate"])
    rr = 4
    pass_rows = {}
    for cyc, *_ in CYCLES:
        sel = [e for e in execs if e[5] == cyc]
        p_ = sum(e[7] == "Passed" for e in sel)
        vals = [cyc, len(sel), p_, sum(e[7] == "Failed" for e in sel), sum(e[7] == "Blocked" for e in sel),
                round(p_ / len(sel), 3) if sel else 0]
        for j, v in enumerate(vals, 1):
            wsm.cell(row=rr, column=j, value=v)
        wsm.cell(row=rr, column=6).number_format = "0.0%"
        pass_rows[cyc] = (rr, vals)
        rr += 1
    set_widths(wsm, [10, 10, 10, 10, 10, 10])
    save(ctx, wb, fid)

    rr, vals = pass_rows["REG"]
    ctx.xfact(fid, "Summary", f"B{rr}", str(vals[1]), f"Wave 1 regression cycle (REG): {vals[1]} executions, {vals[2]} passed.",
              world_ref="WAVE:MW-1")
    ctx.xfact(fid, "Document Control", "B11", f"Sev1 {open_by['Sev1']}",
              f"Wave 1 test report (2026-09-10): open defects Sev1 {open_by['Sev1']}, Sev2 {open_by['Sev2']}, Sev3 {open_by['Sev3']}, Sev4 {open_by['Sev4']}.",
              kind="temporal", world_ref="WAVE:MW-1", notes="snapshot at 2026-09-10; the 2026-10-05 figures live elsewhere")
    ctx.done(fid, f"4 sheets, {len(execs)} executions, {len(defects)} defects")


# =============================================================================================
# ST009 Vendor Fee Schedule 2026 (2026-01-12; Norrvik fees deliberately absent)
# =============================================================================================

FEE_LABELS = {
    "desk_assessment_gbp": ("Desk assessment", "per instruction"),
    "site_visit_gbp": ("Site visit and report", "per instruction"),
    "major_loss_hourly_gbp": ("Major loss handling", "per hour"),
    "fixed_fee_demand_gbp": ("Fixed-fee demand letter", "per demand"),
    "success_fee_pct": ("Success fee on recoveries", "% of amount recovered"),
    "collection_gbp": ("Vehicle collection", "per vehicle"),
    "surveillance_day_gbp": ("Surveillance", "per day"),
}
SLA_LABELS = {
    "desk_assessment_business_days": "Desk assessment turnaround",
    "site_visit_business_days": "Site visit turnaround",
    "report_business_days": "Report turnaround",
    "repair_start_business_days": "Repair start",
    "first_visit_business_days": "First visit",
    "collection_business_days": "Vehicle collection",
}


def build_st009(ctx):
    fid = "ST009"
    d = adate(fid)
    ds = iso(d)
    a = W.anchor(fid)
    wb = new_workbook()
    set_props(wb, fid, subject="UK vendor fee schedule 2026")
    doc_control_sheet(wb, fid,
                      purpose="Fees and service levels agreed with UK panel vendors for 2026.",
                      scope="UK vendors only. Nordic vendor terms are held by the Nordic claims assessment team and are not reproduced here.",
                      approvers=approvers_for(fid), colleagues=colleagues_of(a["author"], d),
                      sources=["Panel agreements", "Vendor master (CLR.T_VENDOR)"])
    ws = wb.create_sheet("Fee Schedule")
    write_title(ws, "Vendor Fee Schedule 2026 - UK panel", f"As at {ds}. Amounts in GBP excluding VAT.")
    hdr = ["Vendor code", "Vendor", "Type", "Item", "Basis", "Amount", "Unit", "Notes"]
    write_header(ws, 4, hdr)
    r = 5
    rows_by = {}
    vendors = [v for v in W.vendors.values() if v["country"] == "UK" and v["type"] not in ("reinsurer", "bank", "software")
               and v["panel_from"] <= ds and (v["panel_to"] is None or v["panel_to"] >= ds)]
    for v in vendors:
        vid = v["id"]
        for f in ("fees", "sla"):
            require(fid, f"VENDOR:{vid}", f)
        items = []
        for k, val in (v.get("fees") or {}).items():
            lab, basis = FEE_LABELS.get(k, (k, ""))
            unit = "%" if k.endswith("_pct") else "GBP"
            items.append((lab, basis, val, unit, "", k))
        for k, val in (v.get("sla") or {}).items():
            if k in SLA_LABELS:
                items.append((SLA_LABELS[k], "service level", val, "business days", "", k))
            elif k == "payment_cutoff":
                items.append(("Payment cut-off", "service level", None, "", str(val), k))
        if v["type"] in ("loss_adjuster", "repair_network", "solicitor", "salvage", "siu_partner"):
            items.append(("Invoice matching", "process", None, "", "Matched by the vendor invoice job CLRNAS02 (Mon-Fri 01:00)", "inv"))
            items.append(("Payment run", "process", None, "", "Paid in the weekly vendor payment run CLRWPAY1 (Thu 15:00)", "pay"))
        if not v.get("fees"):
            items.append(("Work", "per approved estimate", None, "", "No fixed fee", "est"))
        items.append(("Panel membership", "status", None, "", f"Panel member since {v['panel_from']}", "panel"))
        for lab, basis, val, unit, note, key in items:
            vals = [v["code"], v["name"], v["type"].replace("_", " "), lab, basis, val, unit, note]
            for j, x in enumerate(vals, 1):
                ws.cell(row=r, column=j, value=x)
            rows_by[(vid, key)] = r
            r += 1
    last = r - 1
    ws.auto_filter.ref = f"A4:H{last}"
    ws.freeze_panes = "C5"
    set_widths(ws, [11, 34, 14, 28, 22, 10, 14, 60])
    print_setup(ws, fid)

    wv = wb.create_sheet("Vendors")
    write_title(wv, "UK panel vendors")
    write_header(wv, 3, ["Vendor code", "Vendor", "Type", "Location", "Panel since", "Contact", "Contact email", "Role"])
    rr = 4
    for v in vendors:
        contact = v.get("contact")
        vals = [v["code"], v["name"], v["type"].replace("_", " "), v["location"], D(v["panel_from"]),
                pname(contact, d) if contact else "", W.people[contact]["email"] if contact else "",
                temporalize(v["role"], d) if may(fid, f"VENDOR:{v['id']}", "role") and "removed" not in v["role"] else ""]
        for j, x in enumerate(vals, 1):
            c = wv.cell(row=rr, column=j, value=x)
            if isinstance(x, dt.date):
                c.number_format = "yyyy-mm-dd"
        rr += 1
    set_widths(wv, [11, 34, 14, 14, 12, 18, 36, 50])
    save(ctx, wb, fid)

    ctx.xfact(fid, "Fee Schedule", f"F{rows_by[('VEN-01', 'site_visit_gbp')]}", "420",
              "Vendor fee schedule 2026: Brackenfield site visit and report GBP 420 per instruction.", kind="needle",
              world_ref="VENDOR:VEN-01#fees.site_visit_gbp")
    ctx.xfact(fid, "Fee Schedule", f"F{rows_by[('VEN-01', 'desk_assessment_gbp')]}", "185",
              "Vendor fee schedule 2026: Brackenfield desk assessment GBP 185.", world_ref="VENDOR:VEN-01#fees.desk_assessment_gbp")
    ctx.xfact(fid, "Fee Schedule", f"F{rows_by[('VEN-03', 'major_loss_hourly_gbp')]}", "165",
              "Vendor fee schedule 2026 (issued 2026-01-12): Fellgate major loss handling GBP 165 per hour.",
              kind="temporal", world_ref="VENDOR:VEN-03#fees")
    ctx.xfact(fid, "Fee Schedule", f"F{rows_by[('VEN-07', 'success_fee_pct')]}", "12",
              "Quarryhill Solicitors success fee on recoveries: 12%.", world_ref="VENDOR:VEN-07#fees.success_fee_pct")
    ctx.xfact(fid, "Fee Schedule", f"F{rows_by[('VEN-10', 'surveillance_day_gbp')]}", "640",
              "Greyfold Investigations surveillance: GBP 640 per day.", world_ref="VENDOR:VEN-10#fees.surveillance_day_gbp")
    ctx.xfact(fid, "Fee Schedule", f"F{rows_by[('VEN-09', 'collection_gbp')]}", "60",
              "Salvanta vehicle collection fee GBP 60 per vehicle.", world_ref="VENDOR:VEN-09#fees.collection_gbp")
    ctx.done(fid, f"3 sheets, {last - 4} fee rows")


# =============================================================================================
# ST010 Claims KPI Workbook (2026-10-14; native charts, chart-only channel mix)
# =============================================================================================

def build_st010(ctx):
    from openpyxl.chart import BarChart, LineChart, PieChart, Reference
    from openpyxl.chart.series import SeriesLabel

    fid = "ST010"
    d = adate(fid)
    a = W.anchor(fid)
    S = xl_styles()
    wb = new_workbook()
    set_props(wb, fid, subject="Claims KPIs")
    doc_control_sheet(wb, fid,
                      purpose="Claims key performance indicators for the Executive Committee pack.",
                      scope="Group claims volumes, fraud referrals, FNOL channel mix and trends from the analytical claims sample.",
                      approvers=approvers_for(fid, ["P005"]), colleagues=colleagues_of(a["author"], d),
                      sources=["Data & Analytics claims mart", "Counter-Fraud & SIU referral register", "Analytical claims sample"])
    met = W.timeline["metrics"]
    fin = W.company["financials"]["fy2025"]

    # Channels: chart only (values exist only as chart literals)
    wc = wb.create_sheet("Channels")
    write_title(wc, "FNOL channel mix - 2026 year to date", "Share of first notifications by channel.")
    wc["A4"] = "Telephone: contact centre. Digital: portal, app and telematics."
    wc["A5"] = "Broker: delegated notifications from brokers."
    mix = met["fnol_channel_mix_pct"]["2026YTD"]
    require(fid, "TIMELINE:metrics", "fnol_channel_mix_pct.2026YTD")
    ch1 = PieChart()
    ch1.title = "FNOL channel mix 2026 YTD (%)"
    ch1.add_data(Reference(wc, min_col=26, min_row=1, max_row=3), titles_from_data=False)
    ch1.set_categories(Reference(wc, min_col=25, min_row=1, max_row=3))
    ch1.series[0].tx = SeriesLabel(v="FNOL channel mix 2026 YTD (%)")
    from openpyxl.chart.label import DataLabelList
    ch1.dataLabels = DataLabelList()
    ch1.dataLabels.showVal = True
    ch1.width, ch1.height = 16, 9
    wc.add_chart(ch1, "A7")
    set_widths(wc, [14] * 8)
    ctx.data.setdefault("chart_literals", {})["Channels"] = [
        (["Telephone", "Digital", "Broker"], [mix["telephone"], mix["digital"], mix["broker"]])]

    # Volumes: table + chart from cells
    wv = wb.create_sheet("Volumes")
    write_title(wv, "Claims notified by quarter (Group)", "Source: Data & Analytics claims mart.")
    write_header(wv, 4, ["Quarter", "Claims notified"])
    cq = met["claims_notified"]
    rr = 5
    for q in sorted(cq):
        wv.cell(row=rr, column=1, value=q.replace("Q", " Q"))
        wv.cell(row=rr, column=2, value=int(cq[q])).number_format = "#,##0"
        rr += 1
    ch2 = BarChart()
    ch2.title = "Claims notified by quarter"
    ch2.add_data(Reference(wv, min_col=2, min_row=4, max_row=rr - 1), titles_from_data=True)
    ch2.set_categories(Reference(wv, min_col=1, min_row=5, max_row=rr - 1))
    ch2.width, ch2.height = 16, 8
    wv.add_chart(ch2, "D4")
    set_widths(wv, [12, 16])

    # Fraud: chart only (referral counts as literals)
    wf = wb.create_sheet("Fraud")
    write_title(wf, "Fraud referrals to SIU by quarter", "Counter-Fraud & SIU referral register.")
    wf["A4"] = "Referrals counted on referral date. Q4 2026 to date is excluded."
    fr = met["fraud_referrals_count"]
    ch3 = BarChart()
    ch3.title = "Fraud referrals by quarter"
    ch3.add_data(Reference(wf, min_col=26, min_row=1, max_row=len(fr)), titles_from_data=False)
    ch3.set_categories(Reference(wf, min_col=25, min_row=1, max_row=len(fr)))
    ch3.series[0].tx = SeriesLabel(v="Fraud referrals")
    ch3.width, ch3.height = 16, 8
    wf.add_chart(ch3, "A6")
    ctx.data["chart_literals"]["Fraud"] = [([q.replace("Q", " Q") for q in sorted(fr)], [int(fr[q]) for q in sorted(fr)])]

    # Sample trends: monthly FNOL counts by line from the analytical claims sample
    rows = ctx.data["claims"]
    ws = wb.create_sheet("Sample Trends")
    write_title(ws, "Monthly notifications by line - analytical claims sample",
                "Counts of sample claims by notification month (sample, not Group totals). Data to 2026-09-30.")
    lines = ["Motor", "Home", "Commercial Property", "SME Liability"]
    write_header(ws, 4, ["Month"] + lines + ["Total", "Tier-3", "Avg incurred GBP"])
    months = []
    for y, m in C.MONTHS:
        if (y, m) > (2026, 9):
            continue
        months.append(f"{y}-{m:02d}")
    rr = 5
    peak = None
    for mo in months:
        sel = [x for x in rows if iso(x["notified_date"])[:7] == mo]
        vals = [mo] + [sum(1 for x in sel if x["_line"] == ln) for ln in lines]
        vals += [len(sel), sum(1 for x in sel if x["tier"] == 3),
                 round(sum(x["incurred_gbp"] for x in sel) / len(sel), 2) if sel else 0]
        for j, v in enumerate(vals, 1):
            ws.cell(row=rr, column=j, value=v)
        ws.cell(row=rr, column=8).number_format = "#,##0.00"
        if peak is None or vals[5] > peak[1]:
            peak = (mo, vals[5], rr)
        rr += 1
    last = rr - 1
    ch4 = LineChart()
    ch4.title = "Sample notifications per month by line"
    ch4.add_data(Reference(ws, min_col=2, min_row=4, max_col=5, max_row=last), titles_from_data=True)
    ch4.set_categories(Reference(ws, min_col=1, min_row=5, max_row=last))
    ch4.width, ch4.height = 22, 10
    ws.add_chart(ch4, "J4")
    ws.freeze_panes = "B5"
    set_widths(ws, [10, 9, 9, 12, 12, 9, 9, 16])

    # FY2025 KPIs (non-reserved figures only)
    wk = wb.create_sheet("FY2025")
    write_title(wk, "FY2025 headline claims KPIs")
    write_header(wk, 3, ["KPI", "Value", "Unit"])
    kp = [("Gross written premium", "gross_written_premium_gbp_m", "GBP m"),
          ("Gross claims incurred", "gross_claims_incurred_gbp_m", "GBP m"),
          ("Claims outstanding (technical provisions)", "claims_outstanding_technical_provisions_gbp_m", "GBP m"),
          ("Combined ratio", "combined_ratio_pct", "%"), ("Claims notified", "claims_notified", "claims"),
          ("Fraud referrals", "fraud_referrals", "referrals"), ("Confirmed fraud cases", "confirmed_fraud_cases", "cases"),
          ("Fraud savings", "fraud_savings_gbp_m", "GBP m"), ("Average settlement days - motor", "avg_settlement_days_motor", "days"),
          ("Average settlement days - home", "avg_settlement_days_home", "days")]
    rr = 4
    kp_rows = {}
    for lab, key, unit in kp:
        if not may(fid, "ORG:company", f"financials.fy2025.{key}"):
            continue
        wk.cell(row=rr, column=1, value=lab)
        wk.cell(row=rr, column=2, value=fin[key])
        wk.cell(row=rr, column=3, value=unit)
        kp_rows[key] = rr
        rr += 1
    if may(fid, "TIMELINE:metrics", "tier3_share_pct"):
        wk.cell(row=rr, column=1, value="Tier-3 share of claims (2025)")
        wk.cell(row=rr, column=2, value=met["tier3_share_pct"]["2025"])
        wk.cell(row=rr, column=3, value="%")
        kp_rows["tier3"] = rr
    set_widths(wk, [44, 12, 10])
    save(ctx, wb, fid)
    if ctx.want(fid):
        write_chart_literals(ctx.path(fid), ctx.data["chart_literals"], fid)

    pl = placement(fid, "st10_chart")
    ctx.chart_fact(fid, "Channels", 0, f"Telephone={mix['telephone']}",
                   f"Native chart cache: FNOL channel mix 2026 YTD - telephone {mix['telephone']}%, digital {mix['digital']}%, broker {mix['broker']}%.",
                   kind="chart_only", world_ref=pl["world_ref"], exclusive=True, placement=pl)
    ctx.chart_fact(fid, "Channels", 0, f"Digital={mix['digital']}", f"FNOL channel mix 2026 YTD: digital {mix['digital']}%.",
                   kind="chart_only", world_ref=pl["world_ref"], exclusive=True, notes="part of PL-161")
    ctx.chart_fact(fid, "Channels", 0, f"Broker={mix['broker']}", f"FNOL channel mix 2026 YTD: broker {mix['broker']}%.",
                   kind="chart_only", world_ref=pl["world_ref"], exclusive=True, notes="part of PL-161")
    ctx.chart_fact(fid, "Fraud", 0, f"2026 Q3={int(fr['2026Q3'])}",
                   f"Fraud referrals chart: {int(fr['2026Q2']):,} in 2026 Q2 and {int(fr['2026Q3']):,} in 2026 Q3 (values only in the chart).",
                   kind="chart_only", world_ref="TIMELINE:metrics#fraud_referrals_count")
    ctx.chart_fact(fid, "Volumes", 0, f"2026 Q3={int(cq['2026Q3'])}",
                   f"Claims notified chart: {int(cq['2026Q3']):,} claims notified in 2026 Q3.", kind="general",
                   world_ref="TIMELINE:metrics#claims_notified.2026Q3")
    ctx.xfact(fid, "Volumes", "B6", str(int(cq["2026Q3"])), f"Claims notified in 2026 Q3: {int(cq['2026Q3']):,}.",
              world_ref="TIMELINE:metrics#claims_notified.2026Q3")
    ctx.xfact(fid, "Sample Trends", f"F{peak[2]}", str(peak[1]),
              f"In the analytical claims sample the busiest notification month to 2026-09 is {peak[0]} with {peak[1]} claims.",
              world_ref="PROFILE:rows")
    if "avg_settlement_days_motor" in kp_rows:
        ctx.xfact(fid, "FY2025", f"B{kp_rows['avg_settlement_days_motor']}", str(fin["avg_settlement_days_motor"]),
                  f"FY2025 average settlement days for motor: {fin['avg_settlement_days_motor']}.",
                  world_ref="ORG:company#financials.fy2025.avg_settlement_days_motor")
    if "fraud_referrals" in kp_rows:
        ctx.xfact(fid, "FY2025", f"B{kp_rows['fraud_referrals']}", str(fin["fraud_referrals"]),
                  f"FY2025 fraud referrals: {fin['fraud_referrals']:,}.", world_ref="ORG:company#financials.fy2025.fraud_referrals")
    ctx.done(fid, f"6 sheets, {last - 4 + len(kp_rows) + 2} data rows, 4 charts")


def write_chart_literals(path, literals: dict, fid: str):
    """Replace the chart series references on the given sheets with c:strLit / c:numLit literals."""
    import io
    import zipfile
    from lxml import etree
    from .common import finalize_ooxml

    NS = {"c": "http://schemas.openxmlformats.org/drawingml/2006/chart",
          "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
          "x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
          "pr": "http://schemas.openxmlformats.org/package/2006/relationships",
          "xdr": "http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing"}
    zin = zipfile.ZipFile(path)
    files = {n: zin.read(n) for n in zin.namelist()}
    order = zin.namelist()
    zin.close()

    def rels(part):
        base, name = part.rsplit("/", 1)
        rp = f"{base}/_rels/{name}.rels"
        if rp not in files:
            return {}
        root = etree.fromstring(files[rp])
        out = {}
        for rel in root:
            tgt = rel.get("Target")
            if tgt.startswith("/"):
                full = tgt.lstrip("/")
            else:
                parts = (base + "/" + tgt).split("/")
                stack = []
                for p_ in parts:
                    if p_ == "..":
                        stack.pop()
                    elif p_ and p_ != ".":
                        stack.append(p_)
                full = "/".join(stack)
            out[rel.get("Id")] = full
        return out

    wbx = etree.fromstring(files["xl/workbook.xml"])
    wrels = rels("xl/workbook.xml")
    for sh in wbx.iter(f"{{{NS['x']}}}sheet"):
        name = sh.get("name")
        if name not in literals:
            continue
        spart = wrels[sh.get(f"{{{NS['r']}}}id")]
        sx = etree.fromstring(files[spart])
        srels = rels(spart)
        charts = []
        for dr in sx.iter(f"{{{NS['x']}}}drawing"):
            dpart = srels[dr.get(f"{{{NS['r']}}}id")]
            drels = rels(dpart)
            dx = etree.fromstring(files[dpart])
            for c in dx.iter(f"{{{NS['c']}}}chart"):
                charts.append(drels[c.get(f"{{{NS['r']}}}id")])
        for cpart, (cats, vals) in zip(charts, literals[name]):
            cx = etree.fromstring(files[cpart])
            for ser in cx.iter(f"{{{NS['c']}}}ser"):
                cat = ser.find("c:cat", NS)
                val = ser.find("c:val", NS)
                for el, data, kind in ((cat, cats, "strLit"), (val, vals, "numLit")):
                    if el is None:
                        continue
                    for ch in list(el):
                        el.remove(ch)
                    lit = etree.SubElement(el, f"{{{NS['c']}}}{kind}")
                    if kind == "numLit":
                        fc = etree.SubElement(lit, f"{{{NS['c']}}}formatCode")
                        fc.text = "General"
                    pc = etree.SubElement(lit, f"{{{NS['c']}}}ptCount")
                    pc.set("val", str(len(data)))
                    for i, v in enumerate(data):
                        pt = etree.SubElement(lit, f"{{{NS['c']}}}pt")
                        pt.set("idx", str(i))
                        vv = etree.SubElement(pt, f"{{{NS['c']}}}v")
                        vv.text = str(v)
            files[cpart] = etree.tostring(cx, xml_declaration=True, encoding="UTF-8", standalone=True)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zout:
        for n in order:
            zout.writestr(n, files[n])
    path.write_bytes(buf.getvalue())
    finalize_ooxml(path, fid)


# =============================================================================================
# ST011 Mainframe Capacity Plan (2026-04-06)
# =============================================================================================

def build_st011(ctx):
    fid = "ST011"
    d = adate(fid)
    ds = iso(d)
    a = W.anchor(fid)
    r = rng(f"{fid}:cap")
    wb = new_workbook()
    set_props(wb, fid, subject="CLARA mainframe capacity and batch window")
    sys1 = W.systems["SYS01"]
    require(fid, "SYSTEM:SYS01", "batch_window")
    require(fid, "SYSTEM:SYS01", "decommission_target")
    doc_control_sheet(wb, fid,
                      purpose="Capacity forecast for the CLARA mainframe workloads and the overnight batch window during the migration to Claims Hub.",
                      scope="CLARA online (CICS), batch, DB2 and MQ workloads on the production LPAR, April 2026 to the decommission target.",
                      approvers=approvers_for(fid), colleagues=colleagues_of(a["author"], d),
                      sources=["Monthly SMF capacity reports", "Batch Scheduler job history", "Programme Skerry migration plan"])
    wa = wb.create_sheet("Assumptions")
    write_title(wa, "Planning assumptions", f"As at {ds}.")
    write_header(wa, 3, ["Assumption", "Value", "Source"])
    assum = [("CLARA batch window", sys1["batch_window"], "System record"),
             ("Wave 0 (Denmark) cut-over", W.timeline["programme"]["wave0"], "Programme plan"),
             ("Wave 1 (UK motor) cut-over", W.timeline["programme"]["wave1"], "Programme plan"),
             ("Wave 2 (remaining products)", "planned early 2027 - date to be confirmed", "Programme plan"),
             ("Reserve parallel run", f"{W.timeline['programme']['parallel_run']['from']} to {W.timeline['programme']['parallel_run']['to']}", "Programme plan"),
             ("CLARA decommission target", sys1["decommission_target"], "System record"),
             ("Growth in online transactions until Wave 1", "flat", "Capacity team"),
             ("Workload after each wave", "falls in line with migrated claim volumes", "Capacity team")]
    rr = 4
    arow = {}
    for k_, v_, s_ in assum:
        for j, x in enumerate([k_, v_, s_], 1):
            wa.cell(row=rr, column=j, value=x)
        arow[k_] = rr
        rr += 1
    set_widths(wa, [36, 48, 22])

    wm = wb.create_sheet("MIPS Forecast")
    write_title(wm, "MIPS forecast by workload", "Monthly average of the peak hour, in MIPS.")
    write_header(wm, 4, ["Month", "Workload", "Forecast MIPS", "Basis"])
    base = {"CICS online": 610, "Batch": 840, "DB2": 520, "MQ": 95}
    rr = 5
    mrows = 0
    for y, m in [(2026, k) for k in range(4, 13)] + [(2027, k) for k in range(1, 10)]:
        month = dt.date(y, m, 1)
        f = 1.0
        if month >= D("2026-06-01"):
            f -= 0.05
        if month >= D("2026-10-01"):
            f -= 0.28
        if month >= D("2027-03-01"):
            f -= 0.45
        for wl, b in base.items():
            v = round(b * f * r.uniform(0.97, 1.03))
            vals = [f"{y}-{m:02d}", wl, v, "Actual trend" if month < D("2026-04-01") else "Forecast"]
            for j, x in enumerate(vals, 1):
                wm.cell(row=rr, column=j, value=x)
            rr += 1
            mrows += 1
    wm.auto_filter.ref = f"A4:D{rr - 1}"
    wm.freeze_panes = "A5"
    set_widths(wm, [10, 14, 14, 14])

    wbw = wb.create_sheet("Batch Window")
    write_title(wbw, "Overnight batch schedule", f"CLARA batch window {sys1['batch_window']}.")
    write_header(wbw, 4, ["Job", "Description", "Schedule", "Programs", "Status", "Typical elapsed (min)", "Owner team"])
    rr = 5
    jrows = {}
    for jn in sorted(W.jcl_jobs):
        j = W.jcl_jobs[jn]
        if not may(fid, f"JCL:{jn}", "schedule"):
            continue
        progs = [s["program"] for s in j["steps"]]
        if any(W.programs[p]["since"] > ds for p in progs):
            continue
        status = j["status"]
        sched = j["schedule"]
        if jn == "CLRDRSV9":
            status, sched = "active", "daily 05:00 (parallel run)"
        if jn == "CLRNFR99":
            status, sched = "disabled", "removed from schedule 2026-04-01 (was daily 00:45)"
        vals = [jn, j["description"].replace(" (retired 2026-08-28)", ""), sched, ", ".join(progs), status,
                r.randint(4, 55), team_name(j["owner_team"], d)]
        for k, x in enumerate(vals, 1):
            wbw.cell(row=rr, column=k, value=x)
        jrows[jn] = rr
        rr += 1
    set_widths(wbw, [11, 44, 40, 34, 9, 12, 32])
    print_setup(wbw, fid)
    save(ctx, wb, fid)

    ctx.xfact(fid, "Assumptions", f"B{arow['CLARA batch window']}", sys1["batch_window"],
              f"Mainframe capacity plan: the CLARA batch window is {sys1['batch_window']}.", kind="needle",
              world_ref="SYSTEM:SYS01#batch_window")
    ctx.xfact(fid, "Assumptions", f"B{arow['CLARA decommission target']}", sys1["decommission_target"],
              f"CLARA decommission target: {sys1['decommission_target']}.", world_ref="SYSTEM:SYS01#decommission_target")
    ctx.xfact(fid, "Batch Window", f"C{jrows['CLRNFR99']}", "removed from schedule 2026-04-01",
              "Capacity plan (2026-04-06): job CLRNFR99 (auto-decline sweep) was removed from the schedule on 2026-04-01.",
              kind="temporal", world_ref="JCL:CLRNFR99#schedule")
    ctx.xfact(fid, "Batch Window", f"E{jrows['CLRDRSV9']}", "active",
              "Capacity plan (2026-04-06): CLRDRSV9 reserve parallel-run reconciliation is active (daily 05:00 during the parallel run).",
              kind="temporal", world_ref="JCL:CLRDRSV9#status")
    ctx.xfact(fid, "Batch Window", f"C{jrows['CLRYGL90']}", "annually 31 Dec 23:30",
              "CLRYGL90 year-end reserve currency revaluation runs annually on 31 Dec at 23:30 (and on Reserving request).",
              world_ref="JCL:CLRYGL90#schedule")
    ctx.done(fid, f"{len(wb.sheetnames)} sheets, {mrows} forecast rows, {len(jrows)} jobs")


# =============================================================================================
# ST012 Programme Skerry Contact Directory (2026-11-02; Corvane staff only)
# =============================================================================================

def build_st012(ctx):
    fid = "ST012"
    d = adate(fid)
    ds = iso(d)
    a = W.anchor(fid)
    wb = new_workbook()
    set_props(wb, fid, subject="Programme contact directory")
    doc_control_sheet(wb, fid,
                      purpose="Contact directory of Corvane Mutual staff involved in Programme Skerry.",
                      scope="Corvane Mutual employees only. Programme partner and vendor contacts are kept in their own directories.",
                      approvers=approvers_for(fid), colleagues=["P054", "P049"],
                      sources=["HR system extract", "Programme stakeholder list"])
    ws = wb.create_sheet("Directory")
    write_title(ws, "Programme Skerry Contact Directory - Corvane staff", f"As at {ds}.")
    hdr = ["Name", "Job title", "Team", "Department", "Location", "Email", "Phone", "Line manager"]
    write_header(ws, 4, hdr)
    rr = 5
    rows_by = {}
    staff = [pid for pid, p in W.people.items() if p["employer"] == "ORG-CORVANE" and W.employed(pid, ds)]
    staff.sort(key=lambda p: W.name_of(p, ds).split()[-1] + W.name_of(p, ds))
    for pid in staff:
        p = W.people[pid]
        email = p["email"]
        for e in p.get("email_history") or []:
            if e["from"] <= ds and (e["to"] is None or e["to"] >= ds):
                email = e["email"]
        assert email.endswith("@corvane-mutual.example")
        tid = W.team_of(pid, ds)
        dep = W.team_department(tid, ds) if tid else None
        mgr = W.manager_of(pid, ds)
        vals = [pname(pid, d), ptitle(pid, d), team_name(tid, d) if tid else "", W.departments[dep]["name"] if dep in W.departments else "",
                W.locations[W.location_of(pid, ds)]["name"], email, p["phone"], pname(mgr, d) if mgr else ""]
        for j, x in enumerate(vals, 1):
            ws.cell(row=rr, column=j, value=x)
        rows_by[pid] = rr
        rr += 1
    ws.auto_filter.ref = f"A4:H{rr - 1}"
    ws.freeze_panes = "B5"
    set_widths(ws, [24, 46, 34, 26, 30, 42, 16, 24])
    print_setup(ws, fid)

    wt = wb.create_sheet("Teams")
    write_title(wt, "Teams and leads", f"As at {ds}.")
    write_header(wt, 3, ["Team ID", "Team", "Department", "Lead", "Members listed"])
    rr = 4
    trows = {}
    for tid in sorted(W.teams):
        if tid == "T26":
            continue
        lead = W.team_lead(tid, ds)
        dep = W.team_department(tid, ds)
        vals = [tid, team_name(tid, d), W.departments[dep]["name"] if dep in W.departments else "", pname(lead, d) if lead else "",
                sum(1 for p in staff if W.team_of(p, ds) == tid)]
        for j, x in enumerate(vals, 1):
            wt.cell(row=rr, column=j, value=x)
        trows[tid] = rr
        rr += 1
    set_widths(wt, [9, 38, 30, 24, 14])

    wl = wb.create_sheet("Locations")
    write_title(wl, "Corvane Mutual locations")
    write_header(wl, 3, ["Location", "City", "Country", "Address"])
    rr = 4
    for lid, l in W.locations.items():
        if not lid.startswith("LOC-") or l.get("type") != "office":
            continue
        for j, x in enumerate([l["name"], l["city"], l["country"], l["address"]], 1):
            wl.cell(row=rr, column=j, value=x)
        rr += 1
    set_widths(wl, [34, 14, 9, 50])
    save(ctx, wb, fid)

    ctx.xfact(fid, "Directory", f"F{rows_by['P005']}", "ingrid.ashby@corvane-mutual.example",
              "Contact directory (2026-11-02): the Claims Director is Ingrid Ashby, email ingrid.ashby@corvane-mutual.example.",
              kind="needle", world_ref="PERSON:P005#email_history")
    ctx.xfact(fid, "Directory", f"B{rows_by['P013']}", "Head of Recoveries & Subrogation",
              "Freya Lindahl is Head of Recoveries & Subrogation.", world_ref="PERSON:P013#titles")
    ctx.xfact(fid, "Directory", f"H{rows_by['P008']}", pname(W.manager_of("P008", ds), d),
              f"Niall Brannigan (Head of Counter-Fraud & SIU) reports to {pname(W.manager_of('P008', ds), d)}.",
              world_ref="PERSON:P008#reports_to")
    ctx.xfact(fid, "Directory", f"E{rows_by['P022']}", "Leeds Claims Centre",
              "The Corvane Callum Fairbairn is Motor Claims Team Leader at the Leeds Claims Centre.",
              world_ref="PERSON:P022#location")
    ctx.xfact(fid, "Teams", f"D{trows['T30']}", "Tariq Hussain",
              "Contact directory (2026-11-02): Hub Squad - Recoveries & Documents is led by Tariq Hussain.",
              kind="temporal", world_ref="TEAM:T30#lead_history")
    ctx.done(fid, f"4 sheets, {len(staff)} staff")


XLSX_B = [build_st007, build_st008, build_st009, build_st010, build_st011, build_st012]

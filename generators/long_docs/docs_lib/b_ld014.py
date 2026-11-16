"""LD014 – Data Migration Strategy (DOCX, 2025-06-16, author: Callum Fairbairn of IBM, P051)."""
from __future__ import annotations

import itertools

from . import common as C
from . import hub as H
from .core import Ctx, Doc, F, PF, Style, W, long_date, util
from .prose import Prose

FID = "LD014"
DENS = 6
SPLIT_PAD = 6   # paragraphs before the split sentence so that the page break falls near the page bottom

TARGET = {
    "CLR.T_CLAIM": "claim_core.claim", "CLR.T_CLAIMANT": "claim_core.party", "CLR.T_FNOL_EVENT": "fnol.notification",
    "CLR.T_TRIAGE": "triage.triage_decision", "CLR.T_ASSESSMENT": "assessment.assessment",
    "CLR.T_ASSESSOR_ASSIGNMENT": "assessment.assessor_assignment", "CLR.T_RESERVE": "reserve.reserve",
    "CLR.T_RESERVE_MOVEMENT": "reserve.reserve_movement", "CLR.T_FRAUD_REFERRAL": "fraud.referral",
    "CLR.T_SETTLEMENT": "settlement.settlement", "CLR.T_PAYMENT": "payment.payment_instruction",
    "CLR.T_SUBROGATION_CASE": "recovery.recovery_case", "CLR.T_RECOVERY": "recovery.receipt",
    "CLR.T_DOCUMENT_REF": "document.document", "CLR.T_GL_POSTING": "gl.journal_line",
}
COLMAP = {
    "CLR.T_CLAIM": {"CLAIM_ID": ("legacy_claim_id", "Direct; claim_id derived as CLM-<region>-<yyyy>-<6 digits>"),
                    "POLICY_NO": ("policy_no", "Direct"), "PRODUCT_CD": ("product_code", "Code mapping (products)"),
                    "PERIL_CD": ("claim_type", "Code mapping (perils to Claim Types)"), "LOSS_DT": ("loss_date", "Direct"),
                    "NOTIFIED_TS": ("notified_at", "Timestamp converted to UTC"), "CLAIM_STATUS": ("status", "Code mapping (claim status)"),
                    "TIER_CD": ("tier", "Direct (1, 2, 3)"), "REGION_CD": ("region", "Direct"), "CURRENCY_CD": ("currency", "Direct (ISO 4217)"),
                    "HANDLER_USER_ID": ("handler_id", "User mapping via the identity service")},
    "CLR.T_CLAIMANT": {"CLAIMANT_ID": ("party_id", "New identifier; legacy key held in the cross-reference"),
                       "FAMILY_NAME": ("family_name", "Direct; trimmed"), "GIVEN_NAME": ("given_name", "Direct; trimmed"),
                       "PHONE_NO": ("phone", "Normalised to international format"), "EMAIL_ADDR": ("email", "Lower-cased; validated"),
                       "PARTY_ROLE_CD": ("role", "Code mapping (party roles)")},
    "CLR.T_FNOL_EVENT": {"FNOL_ID": ("fnol_id", "New identifier; legacy key in cross-reference"), "CLAIM_ID": ("claim_id", "Via claim cross-reference"),
                         "CHANNEL_CD": ("channel", "Code mapping (channels)"), "RECEIVED_TS": ("received_at", "Timestamp converted to UTC"),
                         "PAYLOAD_REF": ("payload", "Reference only; payload stays in the archive"), "ACK_SENT_TS": ("ack_sent_at", "Timestamp converted to UTC")},
    "CLR.T_TRIAGE": {"CLAIM_ID": ("claim_id", "Via claim cross-reference"), "ROUTE_CD": ("route", "Code mapping (FAST, HANDLER, MCL)"),
                     "SCORE_AT_TRIAGE": ("sentinel_score", "Direct (0–100)"), "TRIAGE_TS": ("decided_at", "Timestamp converted to UTC")},
    "CLR.T_ASSESSMENT": {"ASSESS_ID": ("assessment_id", "New identifier"), "CLAIM_ID": ("claim_id", "Via claim cross-reference"),
                         "ASSESS_TYPE_CD": ("type", "Code mapping (desk, site, video)"), "ESTIMATE_AMT": ("estimate_amount", "Direct"),
                         "COVER_DECISION_CD": ("cover_decision", "Code mapping")},
    "CLR.T_ASSESSOR_ASSIGNMENT": {"ASSIGN_ID": ("assignment_id", "New identifier"), "CLAIM_ID": ("claim_id", "Via claim cross-reference"),
                                  "ASSESSOR_ID": ("claims_assessor_id", "User or vendor mapping"), "VENDOR_CD": ("vendor_code", "Direct"),
                                  "SLA_DUE_DT": ("sla_due", "Direct")},
    "CLR.T_RESERVE": {"RSV_ID": ("reserve_id", "New UUID; legacy RSV_ID kept in cross-reference"), "CLAIM_ID": ("claim_id", "Via claim cross-reference"),
                      "RSV_TYPE_CD": ("reserve_type", "Code mapping (ID, EX, LG)"), "CURRENCY_CD": ("currency", "Direct"),
                      "RSV_OUTSTANDING_AMT": ("outstanding_amount", "Direct; reconciled per claim (section 7.2)"),
                      "RSV_GBP_EQUIV_AMT": ("gbp_equivalent", "Direct"), "RSV_NEXT_REVIEW_DT": ("next_review_date", "Direct"),
                      "RSV_STATUS": ("status", "Code mapping (O, C)")},
    "CLR.T_RESERVE_MOVEMENT": {"MOVE_ID": ("movement_id", "New identifier; legacy key in cross-reference"),
                               "RSV_ID": ("reserve_id", "Via reserve cross-reference"), "MOVE_TYPE_CD": ("movement_type", "Code mapping (movement types)"),
                               "MOVE_AMT": ("amount_minor", "Converted to minor units"), "MOVE_TS": ("created_at", "Timestamp converted to UTC")},
    "CLR.T_FRAUD_REFERRAL": {"REF_ID": ("referral_id", "New identifier"), "CLAIM_ID": ("claim_id", "Via claim cross-reference"),
                             "REF_SCORE": ("sentinel_score", "Direct (0–100)"), "REF_THRESHOLD_APPLIED": ("threshold_applied", "Direct"),
                             "TIER_CD": ("tier", "Direct"), "REF_TS": ("referred_at", "Timestamp converted to UTC"),
                             "SIU_CASE_ID": ("siu_case_id", "Direct"), "RULE_ID": ("rule_id", "Direct")},
    "CLR.T_SETTLEMENT": {"SETTLE_ID": ("settlement_id", "New identifier"), "CLAIM_ID": ("claim_id", "Via claim cross-reference"),
                         "OFFER_AMT": ("offer_amount", "Direct"), "EXCESS_APPLIED_AMT": ("excess_applied", "Direct"),
                         "FINAL_FLAG": ("final", "Y/N to boolean"), "ACCEPTED_DT": ("agreed_at", "Date to timestamp")},
    "CLR.T_PAYMENT": {"PAY_ID": ("payment_id", "New identifier"), "CLAIM_ID": ("claim_id", "Via claim cross-reference"),
                      "PAY_AMT": ("amount", "Direct"), "CURRENCY_CD": ("currency", "Direct"), "PAY_STATUS": ("status", "Code mapping")},
    "CLR.T_SUBROGATION_CASE": {"SUBRO_CASE_ID": ("case_id", "New identifier"), "CLAIM_ID": ("claim_id", "Via claim cross-reference"),
                               "DEMAND_AMT": ("expected_amount", "Direct"), "CASE_STATUS": ("status", "Code mapping"),
                               "SUBTRAK_REF": ("subtrak_ref", "Direct")},
    "CLR.T_RECOVERY": {"RCV_ID": ("receipt_id", "New identifier"), "SUBRO_CASE_ID": ("case_id", "Via case cross-reference"),
                       "RCV_RECEIVED_AMT": ("amount", "Direct")},
    "CLR.T_DOCUMENT_REF": {"DOC_REF_ID": ("document_id", "New identifier"), "CLAIM_ID": ("claim_id", "Via claim cross-reference"),
                           "VAULT_OBJECT_ID": ("vault_object_id", "Direct; object stays in DOCSTOR"), "DOC_TYPE_CD": ("doc_type", "Code mapping"),
                           "RECEIVED_TS": ("stored_at", "Timestamp converted to UTC")},
    "CLR.T_GL_POSTING": {"POSTING_ID": ("line_id", "New identifier"), "GL_PERIOD": ("period", "Direct"),
                         "ACCOUNT_CD": ("account", "Chart-of-accounts mapping"), "AMOUNT_GBP": ("amount_gbp", "Signed by DR_CR")},
}
NO_TARGET_RULE = {
    "CLR.T_POLICY_SNAPSHOT": "Not migrated – policy data re-sourced from PALM",
    "CLR.T_CLAIM_TIER": "Not migrated – tier history retained in the archive extract",
    "CLR.T_FRAUD_SCORE": "Not migrated – latest score carried on the triage decision",
    "CLR.T_INSPECTION": "Not migrated – summarised in the assessment record",
    "CLR.T_ESTIMATE": "Not migrated – latest estimate carried on the assessment",
    "CLR.T_RESERVE_HISTORY": "Not migrated – month-end snapshots retained in the CDW",
    "CLR.T_RESERVE_AUTHORITY": "Not migrated – approvals evidenced through movement history",
    "CLR.T_CLAIM_LINK": "Not migrated – links rebuilt by fraud-referral-svc",
    "CLR.T_SIU_CASE": "Not migrated – SIU cases remain in the SIU Case Manager",
    "CLR.T_PAYEE": "Not migrated in this release – payee data re-captured at next payment",
    "CLR.T_LITIGATION": "Not migrated – solicitor instructions held in DOCSTOR",
    "CLR.T_SALVAGE": "Not migrated – salvage disposals closed in CLARA before the wave",
}
TECH_COLS = {"LAST_UPD_TS", "LAST_UPD_PGM", "LAST_UPD_USER"}
POST_CIRCULAR_COLS = ("CUSTOMER_NOTICE", "DEFER_")


def _cols(ctx, t):
    out = []
    for c in W.tables[t]["columns"]:
        if ctx.date < "2026-03-27" and any(k in c["name"] for k in POST_CIRCULAR_COLS):
            continue
        out.append(c["name"])
    return out


def _rows_for(ctx, t):
    rows = []
    tgt = TARGET.get(t)
    for cn in _cols(ctx, t):
        if tgt and cn in COLMAP.get(t, {}):
            tc, rule = COLMAP[t][cn]
            rows.append([t, cn, f"{tgt}.{tc}", rule])
        elif cn in TECH_COLS:
            rows.append([t, cn, "—", "Not migrated – technical audit column"])
        elif tgt:
            rows.append([t, cn, "—", "No target column – held in the migration archive extract"])
        else:
            rows.append([t, cn, "—", NO_TARGET_RULE.get(t, "Not migrated")])
    return rows


def mapping_rows(ctx) -> tuple[list[list[str]], int, int]:
    """Order tables so that RSV_OUTSTANDING_AMT lands on row 142 and REF_SCORE on row 187."""
    n = lambda t: len(_cols(ctx, t))  # noqa: E731
    first = ["CLR.T_CLAIM", "CLR.T_CLAIMANT", "CLR.T_POLICY_SNAPSHOT", "CLR.T_FNOL_EVENT", "CLR.T_TRIAGE",
             "CLR.T_CLAIM_TIER", "CLR.T_ASSESSMENT", "CLR.T_ASSESSOR_ASSIGNMENT"]
    pool_a = ["CLR.T_INSPECTION", "CLR.T_ESTIMATE", "CLR.T_RESERVE_AUTHORITY", "CLR.T_RESERVE_HISTORY", "CLR.T_CLAIM_LINK",
              "CLR.T_DOCUMENT_REF"]
    base = sum(n(t) for t in first)
    rsv_pos = _cols(ctx, "CLR.T_RESERVE").index("RSV_OUTSTANDING_AMT") + 1
    best = None
    for k in range(len(pool_a) + 1):
        for combo in itertools.combinations(pool_a, k):
            row = base + sum(n(t) for t in combo) + rsv_pos
            if best is None or abs(row - 142) < abs(best[0] - 142):
                best = (row, combo)
    seq = first + list(best[1]) + ["CLR.T_RESERVE", "CLR.T_RESERVE_MOVEMENT"]
    rest_pool = [t for t in pool_a if t not in best[1]] + ["CLR.T_FRAUD_SCORE", "CLR.T_SIU_CASE"]
    upto = sum(n(t) for t in seq)
    ref_pos = _cols(ctx, "CLR.T_FRAUD_REFERRAL").index("REF_SCORE") + 1
    best2 = None
    for k in range(len(rest_pool) + 1):
        for combo in itertools.combinations(rest_pool, k):
            row = upto + sum(n(t) for t in combo) + ref_pos
            if best2 is None or abs(row - 187) < abs(best2[0] - 187):
                best2 = (row, combo)
    seq += list(best2[1]) + ["CLR.T_FRAUD_REFERRAL", "CLR.T_SETTLEMENT", "CLR.T_PAYMENT", "CLR.T_SUBROGATION_CASE"]
    rows = []
    for t in seq:
        rows.extend(_rows_for(ctx, t))
    r_rsv = next(i for i, r in enumerate(rows, 1) if r[0] == "CLR.T_RESERVE" and r[1] == "RSV_OUTSTANDING_AMT")
    r_ref = next(i for i, r in enumerate(rows, 1) if r[0] == "CLR.T_FRAUD_REFERRAL" and r[1] == "REF_SCORE")
    return rows, r_rsv, r_ref


def build() -> Doc:
    ctx = Ctx(FID)
    date = ctx.date
    pr = Prose(util.rng(f"{FID}:prose"), date=ctx.date)
    rsvc = ctx.svc("reserve-engine")
    doc = Doc(ctx, title="Data Migration Strategy", doc_id="SKR-MIG-002", version="1.0", status="Approved",
              subtitle="Programme Skerry – migration of claims data from CLARA to Claims Hub",
              style=Style(font="Arial", heading_font="Arial", accent="052F5F", accent2="D9E2F3", size=11),
              header_left="Programme Skerry – Data Migration Strategy", header_right="SKR-MIG-002 v1.0")
    author = "P051"
    author_cell = f"{ctx.name(author)}, {ctx.title(author)} (IBM Consulting)"
    rows = C.control_rows(ctx, doc, owner="P017", extra=[["Prepared for", "Programme Skerry Steering Committee"]])
    rows[5][1] = author_cell
    doc.title_page(rows, extra_lines=[f"Prepared by {ctx.name(author)} (IBM Consulting, Data Migration Lead)"],
                   facts=[PF(ctx, "ld14_author", author_cell, where=(5, 1),
                             notes="IBM's Callum Fairbairn (P051), not the Corvane Motor Claims Team Leader of the same name (P022).")])
    C.version_history(ctx, doc, [("0.1", 49, "Initial outline"), ("0.3", 33, "Wave approach aligned with ADR-015"),
                                 ("0.6", 19, "Reconciliation approach and tolerances"),
                                 ("0.9", 7, "Appendix B mapping table completed"), ("1.0", 0, "Approved")])
    C.reviewers(ctx, doc, ["P052", "P025", "P016", "P036", "P009", "P021", "P019", "P049"])
    C.approvals(ctx, doc, [("P017", "Business owner (Claims Hub)"), ("P018", "Design Authority"),
                           ("P016", "Source system owner"), ("P048", "IBM delivery lead")])
    doc.toc(depth=2)

    # 1 ------------------------------------------------------------------------------
    doc.h(1, "1 Introduction")
    doc.h(2, "1.1 Purpose")
    doc.p("This strategy defines how claims data will be moved from CLARA to Claims Hub: what is migrated, in which "
          "order, how it is transformed and validated, how each wave is reconciled and signed off, and how the "
          "migration is governed. It is the baseline for the migration design, the tooling build and the rehearsal plan.")
    doc.p(pr.para(["intro", "governance"], n=3, topic="the migration approach"))
    doc.h(2, "1.2 Related documents and decisions")
    doc.table(["Reference", "Title"], [["SKR-ARC-001 v1.0", "Claims Hub Target Architecture (approved 3 March 2025)"],
                                       ["ADR-001", ctx.a(W.adrs["ADR-001"]["title"])],
                                       ["ADR-003", W.adrs["ADR-003"]["title"]],
                                       ["ADR-005", W.adrs["ADR-005"]["title"] + " (proposed)"],
                                       ["ADR-015", W.adrs["ADR-015"]["title"]]],
              widths=[4.0, 12.6], caption="Related documents and decisions",
              facts=[F("general", "ADR-015 (Region-wave data migration) underpins the strategy.", "Region-wave data migration",
                       "ADR:ADR-015", where=(5, 1))])
    doc.h(2, "1.3 Audience")
    doc.p("The document is written for the Programme Skerry steering committee, the Claims Hub product owner, the "
          "Design Authority, the Hub squads, the CLARA platform team, Finance (Reserving and Financial Control) and "
          "the data protection function.")
    doc.p(pr.para("governance", n=3))

    # 2 ------------------------------------------------------------------------------
    doc.h(1, "2 Migration principles", page_break=True)
    princ = [("MP-01", "Migrate by wave", "Each wave covers a defined set of products and regions and is signed off on its own."),
             ("MP-02", "Reconcile everything financial", "Reserves, payments and recoveries reconcile at claim and portfolio level."),
             ("MP-03", "Fix data at source", "Cleansing happens in CLARA wherever possible so that defects do not recur."),
             ("MP-04", "Keep the legacy key", "Every migrated record carries its CLARA identifier for traceability."),
             ("MP-05", "No silent defaults", "Unmapped codes stop the load and are resolved explicitly."),
             ("MP-06", "Rehearse under real conditions", "Rehearsals use production-like volumes, timings and sign-offs."),
             ("MP-07", "Reversible until sign-off", "A wave can be rolled back until its reconciliation is signed off."),
             ("MP-08", "Minimise personal data", "Only data needed in Claims Hub is migrated; the rest stays in the archive.")]
    doc.table(["ID", "Principle", "Meaning"], [list(x) for x in princ], widths=[1.6, 4.4, 10.6], caption="Migration principles")
    for pid, name, mean in princ:
        doc.h(2, f"2.{int(pid[3:])} {name}")
        doc.p(mean)
        doc.ps(pr.paras(["migration", "data"], DENS, n=(3, 4)))

    # 3 ------------------------------------------------------------------------------
    doc.h(1, "3 Scope", page_break=True)
    doc.h(2, "3.1 Waves")
    doc.p("ADR-015 sets the order of migration by region and product. Wave 0 migrates Denmark, which has the smallest "
          "portfolio and the simplest product set; Wave 1 migrates UK motor; Wave 2 migrates everything else.")
    rows = []
    for wid, w in W.waves.items():
        prods = ", ".join(W.products[p.strip()]["name"] for p in w["scope"].split(":")[-1].replace("All Danish products (", "").replace(")", "").split(",") if p.strip() in W.products)
        rows.append([w["name"], w["scope"], str(w.get("rehearsals") or "To be planned")])
    doc.table(["Wave", "Scope", "Planned rehearsals"], rows, widths=[5.0, 8.6, 3.0], caption="Migration waves",
              facts=[F("general", "Wave 0 (Denmark) is planned with two rehearsals and Wave 1 (UK motor) with three.",
                       "Wave 1 – UK motor", "WAVE:MW-1", where=(2, 0))])
    doc.p(pr.para(["migration"], n=4))
    doc.h(2, "3.2 Data in scope")
    doc.p("All open claims in the products of a wave are migrated, together with claims closed in the seven years "
          "before the wave date. Claims closed more than seven years before the wave date are not migrated; they are "
          "archived to DOCSTOR and remain available for enquiry through the archive route.",
          facts=[F("general", "Claims closed more than 7 years before the wave date are excluded and archived (DOCSTOR at the time).",
                   "Claims closed more than seven years before the wave date are not migrated", "TIMELINE:programme#migration_reconciliation.excluded")])
    rows = []
    for tn in sorted(W.tables):
        t = W.tables[tn]
        if t["db"] != "DB2" or (t.get("created") and t["created"] > date):
            continue
        rows.append([tn, ctx.a(t["description"]), TARGET.get(tn, "—")])
    doc.table(["CLARA table", "Content", "Target table"], rows, widths=[4.6, 7.0, 5.0], font_size=8.2,
              caption="Source tables and their target")
    doc.ps(pr.paras("data", 2))
    doc.h(2, "3.3 Out of scope")
    doc.bullets(["Policy data, which Claims Hub reads from PALM through the policy API.",
                 "Documents and images, which remain in DOCSTOR and are linked by reference.",
                 "SIU case files, which remain in the SIU Case Manager.",
                 "Historic MI, which remains in the Claims Data Warehouse.",
                 "Claims closed more than seven years before the wave date (archived)."])

    # 4 ------------------------------------------------------------------------------
    doc.h(1, "4 Source and target landscape", page_break=True)
    doc.h(2, "4.1 Source: CLARA")
    clara = W.systems["SYS01"]
    doc.p(f"CLARA runs COBOL programs under CICS with DB2 for z/OS. Extraction runs against a DB2 image copy taken at "
          f"the start of the cut-over freeze, so that the online system is not affected and the extract is consistent. "
          f"The nightly batch window ({clara['batch_window']}) constrains when extraction can run in rehearsals against "
          f"production copies.")
    doc.p(pr.para(["data", "batch"], n=3))
    doc.h(2, "4.2 Target: Claims Hub")
    rows = []
    for name in W.services:
        for tn in H.svc_tables(ctx, name):
            rows.append([tn, ctx.svc(name), str(len(H.table_columns(ctx, tn)))])
    doc.table(["Target table", "Owning service", "Columns"], rows, widths=[6.0, 6.0, 2.6], caption="Target tables",
              font_size=8.6)
    doc.p(f"Reserves are loaded into {rsvc}, which is the only service allowed to write reserves in Claims Hub. "
          f"Claims are created in claim-core-svc first so that every other load can resolve its claim reference.",
          facts=[F("alias_use", "The migration strategy names the reserve service reserve-svc (pre-2026 name).",
                   f"Reserves are loaded into {rsvc}", "SERVICE:reserve-engine#renames")])
    doc.h(2, "4.3 Lessons from the CLX-IF-042 layout incident")
    inc = W.incidents["INC-2025-0412"]
    doc.p(f"Incident {inc['id']} ({long_date(inc['date'])}) showed how sensitive the reserve interfaces are to layout "
          f"changes: {inc['root_cause']} The Q1 2025 NISA-TP2 return was submitted two days late as a result. The "
          f"migration design therefore treats every interface fed from CLR.T_RESERVE_MOVEMENT as a dependency that must "
          f"be impact-assessed before any change to the extract.",
          facts=[F("general", "INC-2025-0412: RM-AMOUNT widened under CHUB-138 broke the GL adapter (CLX-IF-043).",
                   "widened from S9(9)V99 to S9(11)V99 COMP-3 under CHUB-138", "INCIDENT:INC-2025-0412#root_cause")])
    doc.p(pr.para(["integration"], n=3))

    # 5 ------------------------------------------------------------------------------
    doc.h(1, "5 Interfaces affected by migration", page_break=True)
    doc.h(2, "5.1 Approach")
    doc.p("Interfaces that read migrated data must be switched, duplicated or retired at each wave. The interface "
          "catalogue is the source for owners and dependencies; this section summarises the reserve chain, which "
          "carries the highest risk.")
    doc.ps(pr.paras("integration", 2))
    doc.h(2, "5.2 Reserve movement chain")
    rows = []
    for iid in ["CLX-IF-042", "CLX-IF-043", "CLX-IF-044", "CLX-IF-047", "CLX-IF-051", "CLX-IF-055", "CLX-IF-058"]:
        i = W.interfaces[iid]
        rows.append([iid, i["name"], ctx.sys(i["source_system"]) + " → " + ctx.sys(i["target_system"]),
                     ", ".join(i.get("depends_on") or []) or "—"])
    doc.table(["Interface", "Name", "Flow", "Depends on"], rows, widths=[2.4, 5.6, 5.6, 3.0],
              caption="Interfaces downstream of the reserve movement extract")
    doc.p(pr.para(["integration", "migration"], n=3))
    doc.h(2, "5.3 Dependency narrative")
    doc.p("The reserve movement extract CLX-IF-042 is consumed by three first-level interfaces: the GL Reserve Journal "
          "Feed (CLX-IF-043), the CDW Reserve Fact Load (CLX-IF-044) and the Reserve Cession Feed (CLX-IF-047). Each of "
          "these has its own dependants, so a defect introduced at the extract propagates two levels further before it "
          "reaches a regulatory or actuarial output.")
    doc.ps(pr.paras(["integration", "data"], 3, n=(4, 5)))
    pad = Prose(util.rng(f"{FID}:pad"), date=ctx.date)
    doc.ps(pad.paras(["integration", "data"], SPLIT_PAD, n=(4, 5)))
    split = ("Downstream of the warehouse, CLX-IF-044 (CDW Reserve Fact Load) feeds CLX-IF-058 (Reserve Triangles "
             "Extract), which delivers the monthly reserve triangles to the Actuarial Reserving Workbench used by "
             "Reserving for the IBNR run.")
    doc.p(split, split_page_after="CLX-IF-044 (CDW Reserve Fact Load) feeds",
          facts=[PF(ctx, "ld14_044_058", "CLX-IF-044 (CDW Reserve Fact Load) feeds CLX-IF-058 (Reserve Triangles Extract)",
                    notes="The paragraph contains an explicit page break immediately after 'feeds'.")])
    doc.p("Similarly, CLX-IF-043 feeds the Technical Provisions Feed (CLX-IF-051) to the NISA Reporting Hub, and "
          "CLX-IF-047 feeds the Monthly Claims Bordereaux (CLX-IF-055).",
          facts=[F("general", "CLX-IF-043 feeds CLX-IF-051 (Technical Provisions Feed).",
                   "CLX-IF-043 feeds the Technical Provisions Feed (CLX-IF-051)", "INTERFACE:CLX-IF-051#depends_on")])
    doc.p(pr.para(["migration", "integration"], n=4))

    # 6 ------------------------------------------------------------------------------
    doc.h(1, "6 Migration approach", page_break=True)
    for i, (title, banks) in enumerate([("Extraction", ["data", "migration"]), ("Transformation", ["data", "migration"]),
                                        ("Loading", ["migration", "arch"]), ("Code mapping", ["data"]),
                                        ("Data quality and cleansing", ["data", "migration"]),
                                        ("Tooling and environments", ["migration", "security"])], 1):
        doc.h(2, f"6.{i} {title}")
        doc.ps(pr.paras(banks, DENS + 1, n=(3, 5), svc=list(W.services.keys())))
    doc.h(2, "6.7 Load sequence")
    seq = ["claim_core.claim", "claim_core.party", "fnol.notification", "triage.triage_decision", "assessment.assessment",
           "assessment.assessor_assignment", "reserve.reserve", "reserve.reserve_movement", "fraud.referral",
           "settlement.settlement", "payment.payment_instruction", "recovery.recovery_case", "recovery.receipt",
           "document.document"]
    doc.table(["Order", "Target table", "Depends on"], [[str(k), t, seq[k - 2] if k > 1 else "—"] for k, t in enumerate(seq, 1)],
              widths=[1.6, 7.0, 8.0], caption="Load sequence")
    doc.h(2, "6.8 Data quality rules")
    dq = [["DQ-01", "CLR.T_CLAIM", "Every claim has a valid product and peril code"],
          ["DQ-02", "CLR.T_CLAIM", "Open claims have a handler that exists in the identity service"],
          ["DQ-03", "CLR.T_CLAIMANT", "Email addresses are syntactically valid or blank"],
          ["DQ-04", "CLR.T_RESERVE", "Outstanding reserve is not negative"],
          ["DQ-05", "CLR.T_RESERVE", "Closed reserves carry zero outstanding"],
          ["DQ-06", "CLR.T_RESERVE_MOVEMENT", "Movements sum to the current outstanding reserve per reserve"],
          ["DQ-07", "CLR.T_FRAUD_REFERRAL", "Scores are within 0–100"],
          ["DQ-08", "CLR.T_PAYMENT", "Payments reference an existing claim and payee"],
          ["DQ-09", "CLR.T_SUBROGATION_CASE", "Open cases have a limitation date"],
          ["DQ-10", "CLR.T_DOCUMENT_REF", "Every document reference resolves to an object in DOCSTOR"]]
    doc.table(["Rule", "Table", "Check"], dq, widths=[1.8, 4.6, 10.2], caption="Data quality rules (extract)")

    # 7 ------------------------------------------------------------------------------
    doc.h(1, "7 Reconciliation and validation", page_break=True)
    doc.h(2, "7.1 Approach")
    doc.p("Reconciliation is performed at three levels: record counts per table, control totals per table and "
          "currency, and claim-level comparison of financial values. Results are produced automatically for every "
          "rehearsal and for the cut-over run.")
    doc.ps(pr.paras(["migration", "data"], 2))
    doc.h(2, "7.2 Reconciliation")
    ctx.need("TIMELINE:programme", "migration_reconciliation")
    mr = W.timeline["programme"]["migration_reconciliation"]
    doc.p(f"Reserves are reconciled claim by claim between CLR.T_RESERVE and reserve.reserve. A wave passes reserve "
          f"reconciliation when the difference is at most £{mr['per_claim_gbp']:.2f} per claim and "
          f"{mr['portfolio_pct']}% of portfolio outstanding. Differences outside tolerance are investigated before "
          f"sign-off and either corrected at source or accepted by Reserving with a documented reason.",
          facts=[PF(ctx, "ld14_tolerance", f"at most £{mr['per_claim_gbp']:.2f} per claim and {mr['portfolio_pct']}% of portfolio outstanding")])
    doc.p(pr.para(["migration"], n=3))
    doc.h(2, "7.3 Business sign-off")
    doc.p(f"Each wave is signed off by the Claims Hub product owner ({ctx.name('P017')}) after Reserving "
          f"({ctx.name('P009')}) and Financial Control ({ctx.name('P021')}) have confirmed the financial reconciliation.")
    doc.ps(pr.paras(["migration", "governance"], 2))

    # 8 ------------------------------------------------------------------------------
    doc.h(1, "8 Rehearsals and cut-over", page_break=True)
    doc.ps(pr.paras("migration", 2))
    steps = [["T-5 days", "Final rehearsal sign-off and go/no-go preparation"],
             ["T-2 days", "Business freeze communicated; CLARA change freeze starts"],
             ["T-0 18:00", "Freeze starts; final CLARA batch run; DB2 image copy"],
             ["T-0 20:00", "Extraction and transformation"],
             ["T+1", "Load into Claims Hub; automated reconciliation"],
             ["T+2", "Business verification; go/no-go for go-live"],
             ["T+2 06:00", "Claims Hub becomes system of record for the wave; interfaces switched"]]
    doc.table(["When", "Activity"], steps, widths=[3.0, 13.6], caption="Cut-over timeline (template)")
    doc.p("The go/no-go decision is taken by the Programme Skerry Steering Committee, chaired by "
          f"{ctx.person('P004')}.")
    doc.ps(pr.paras(["migration", "test"], 2))

    # 9 ------------------------------------------------------------------------------
    doc.h(1, "9 Roles and responsibilities")
    raci = [["Migration design and tooling", "IBM migration team", ctx.name("P051"), "Hub squads", "Steering Committee"],
            ["CLARA extracts", ctx.team("T20"), ctx.name("P016"), "IBM migration team", "Batch Operations"],
            ["Data cleansing at source", "Claims Operations", ctx.name("P011"), "IBM migration team", "Product owner"],
            ["Reserve reconciliation", ctx.team("T12"), ctx.name("P009"), "Financial Control", "Steering Committee"],
            ["Data protection review", ctx.team("T19"), ctx.name("P019"), "IBM migration team", "Product owner"],
            ["Wave sign-off", "Product owner", ctx.name("P017"), "Reserving, Financial Control", "Steering Committee"]]
    doc.table(["Activity", "Responsible", "Accountable", "Consulted", "Informed"], raci, widths=[4.2, 3.4, 3.0, 3.2, 2.8],
              caption="Migration RACI", font_size=8.4)
    doc.h(1, "10 Risks")
    risks = [["R-01", "Data quality issues found late", "Profiling before each rehearsal; cleansing at source"],
             ["R-02", "Reserve differences outside tolerance", "Claim-level reconciliation in every rehearsal"],
             ["R-03", "Interface change breaks downstream consumers", "Impact assessment for every reserve-chain change"],
             ["R-04", "Cut-over window overrun", "Timed rehearsals; parallel loading"],
             ["R-05", "Key-person dependency on CLARA experts", "Paired working with the IBM migration team"]]
    doc.table(["ID", "Risk", "Mitigation"], risks, widths=[1.4, 6.6, 8.6], caption="Key risks")
    doc.ps(pr.paras(["migration", "governance"], 2))

    # 11 Wave plans ----------------------------------------------------------------------
    doc.h(1, "11 Wave plans", page_break=True)
    for wi, (wid, w) in enumerate(W.waves.items(), 1):
        doc.h(2, f"11.{wi} {w['name']}")
        codes = [c.strip(" ()") for c in w["scope"].replace("All Danish products", "").replace("(", ",").split(",")]
        prods = [W.products[c] for c in codes if c in W.products]
        doc.p(f"Scope: {w['scope']}.")
        if prods:
            doc.table(["Product", "Code", "Currency", "Claim types"],
                      [[p_["name"], p_["code"], p_["currency"], ", ".join(W.claim_types[c]["name"] for c in p_.get("claim_types", []) if c in W.claim_types)]
                       for p_ in prods], widths=[4.0, 2.0, 2.0, 8.6], font_size=8.4)
        reh = w.get("rehearsals")
        if reh:
            doc.table(["Rehearsal", "Objective"],
                      [[f"R{k}", ["Prove the end-to-end tooling and reconciliation on a full production copy",
                                  "Repeat with timings, freeze and sign-off steps as for cut-over",
                                  "Dress rehearsal: identical to the planned cut-over"][k - 1]] for k in range(1, reh + 1)],
                      widths=[2.4, 14.2], font_size=8.6, caption=f"{w['name']}: planned rehearsals")
        doc.ps(pr.paras(["migration", "test"], 3, n=(3, 5)))
    doc.h(1, "12 Protection of migration data")
    doc.p(f"Migration extracts contain personal data and are handled under the data protection policy. The Data "
          f"Protection Officer, {ctx.name('P019')}, has reviewed the approach.")
    doc.ps(pr.paras(["security", "data"], 3, n=(3, 5)))
    doc.h(1, "13 Archive and retention")
    doc.p("Records that are not migrated remain available through the archive route. The archive extract preserves the "
          "CLARA identifiers so that enquiries can be answered after CLARA is decommissioned.")
    doc.ps(pr.paras(["data", "migration"], 3, n=(3, 5)))

    # Appendix A -----------------------------------------------------------------------
    doc.h(1, "Appendix A – Table-by-table approach", page_break=True)
    for tn in sorted(W.tables):
        t = W.tables[tn]
        if t["db"] != "DB2" or (t.get("created") and t["created"] > date):
            continue
        doc.h(2, f"A.{tn}")
        tgt = TARGET.get(tn)
        doc.kv([["Content", ctx.a(t["description"])], ["Primary key", ", ".join(t.get("primary_key", []))],
                ["Target", f"{tgt} ({ctx.svc(W.tables[tgt]['owning_service'])})" if tgt else "None"],
                ["Approach", "Migrate open and recently closed claims; transform per Appendix B" if tgt else NO_TARGET_RULE.get(tn, "Not migrated; retained in the archive extract")],
                ["Columns", str(len(_cols(ctx, tn)))]], widths=(3.4, 13.2), font_size=8.4)
        cols = [c for c in t["columns"] if c["name"] in _cols(ctx, tn)]
        doc.table(["Column", "Type", "Null", "Description"],
                  [[c["name"], c["type"] + (f"({c['length']}{',' + str(c['scale']) if c.get('scale') else ''})" if c.get("length") else ""),
                    "Y" if c.get("nullable") else "N", ctx.a(c["description"])] for c in cols],
                  widths=[4.2, 2.8, 1.0, 8.6], font_size=7.8)
        doc.ps(pr.paras(["migration", "data"], 2, n=(3, 5)))

    # Appendix B -----------------------------------------------------------------------
    rows, r_rsv, r_ref = mapping_rows(ctx)
    doc.h(1, "Appendix B – CLARA to Claims Hub column mapping", page_break=True)
    doc.p("The mapping covers the columns of the tables in scope for Waves 0 and 1. Columns with no target column are "
          "carried in the migration archive extract.")
    doc.table(["#", "CLARA table", "CLARA column", "Claims Hub column", "Transformation"],
              [[str(i)] + r for i, r in enumerate(rows, 1)], widths=[1.0, 3.6, 3.9, 4.6, 4.5], font_size=7.0,
              caption="Column mapping",
              facts=[PF(ctx, "ld14_map_rsv", "reserve.reserve.outstanding_amount", where=(r_rsv, 3),
                        notes=f"Row {r_rsv} of the mapping table: CLR.T_RESERVE.RSV_OUTSTANDING_AMT."),
                     PF(ctx, "ld14_map_frd", "fraud.referral.sentinel_score", where=(r_ref, 3),
                        notes=f"Row {r_ref} of the mapping table: CLR.T_FRAUD_REFERRAL.REF_SCORE."),
                     F("multipage_table", "Mapping: CLR.T_CLAIM.CLAIM_ID → claim_core.claim.legacy_claim_id.",
                       "claim_core.claim.legacy_claim_id", "TABLE:claim_core.claim#columns.legacy_claim_id", where=(1, 3)),
                     F("multipage_table", "Mapping: CLR.T_SUBROGATION_CASE.SUBTRAK_REF → recovery.recovery_case.subtrak_ref.",
                       "recovery.recovery_case.subtrak_ref", "TABLE:recovery.recovery_case#columns.subtrak_ref",
                       where=(next(i for i, r in enumerate(rows, 1) if r[1] == "SUBTRAK_REF"), 3))])
    doc.h(1, "Appendix C – Code mappings", page_break=True)
    doc.table(["CLARA PRODUCT_CD", "Product", "Claims Hub product_code"],
              [[p_["code"], p_["name"], p_["code"]] for p_ in W.products.values()], widths=[4.0, 7.0, 5.6],
              caption="Product codes (retained unchanged)")
    doc.table(["CLARA PERIL_CD", "Claim Type (target)", "Notes"],
              [[c["peril_code"], c["name"], "Nordic only" if c.get("nordic_only") else ("UK only" if c.get("uk_only") else "All regions")]
               for c in W.claim_types.values()], widths=[4.0, 7.0, 5.6], caption="Peril codes to Claim Types")
    for tn, cn in [("CLR.T_CLAIM", "CLAIM_STATUS"), ("CLR.T_CLAIM", "CHANNEL_CD"), ("CLR.T_RESERVE", "RSV_TYPE_CD"),
                   ("CLR.T_RESERVE", "RSV_AUTH_LEVEL")]:
        c = next(x for x in W.tables[tn]["columns"] if x["name"] == cn)
        doc.p(f"{tn}.{cn}: {c['description']}. Codes are carried unchanged into the target, where the code list is "
              f"held as reference data.")
    doc.ps(pr.paras("data", 2))
    doc.h(1, "Appendix D – Interface switch plan")
    rows = []
    for i in H.interfaces_asof(ctx):
        if "SYS01" not in (i["source_system"], i["target_system"]):
            continue
        rows.append([i["id"], ctx.a(i["name"]), "Retained until CLARA decommissioning" if i["id"] in ("CLX-IF-042", "CLX-IF-043", "CLX-IF-044", "CLX-IF-047") else "Switched to Claims Hub per wave"])
    doc.table(["Interface", "Name", "Plan"], rows, widths=[2.4, 7.0, 7.2], font_size=8.2, caption="CLARA interfaces at migration")
    doc.h(1, "Appendix E – Glossary")
    terms = [(t, ctx.a(m)) for t, m in C.glossary_terms(["G-003", "G-013", "G-014", "G-019", "G-020", "G-016", "G-017"])]
    doc.table(["Term", "Meaning"], [list(t) for t in terms], widths=[4.6, 12.0], font_size=8.8)
    return doc


def post_check(doc, texts):
    """Report the page span of the mapping table and the pages of the planted rows."""
    from harness import extract as X
    first = [i + 1 for i, t in enumerate(texts) if X.match("Table", t) and X.match("Column mapping", t)]
    rsv = [i + 1 for i, t in enumerate(texts) if X.match("reserve.reserve.outstanding_amount", t)]
    frd = [i + 1 for i, t in enumerate(texts) if X.match("fraud.referral.sentinel_score", t)]
    last = [i + 1 for i, t in enumerate(texts) if X.match("recovery.recovery_case.subtrak_ref", t)]
    return [f"INFO mapping table starts p{first[-1] if first else '?'}, ends p{last[-1] if last else '?'}; "
            f"RSV row p{rsv}, REF_SCORE row p{frd}; total pages {len(texts)}"]

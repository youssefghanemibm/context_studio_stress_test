"""JSON files ST027-ST034."""
from __future__ import annotations

import json
import pathlib

from generators.common import util

from .core import (W, Built, Facts, DOC_PREFIX, add_business_days, fauthor, fdate, fstatus, ftitle, may, need,
                   minus_days, plus_days, person, pemail, pname, ptitle, rule_params_ok, rule_text_ok, rule_ver, svcname, sysname, team_name,
                   version_history)
from . import phrases

KNOWN_CLAIM_REFS = {"CLM-UK-2025-118204", "CLM-UK-2026-207731", "CLM-SE-2026-004417"}


def ptr(*parts) -> str:
    return "".join("/" + str(p).replace("~", "~0").replace("/", "~1") for p in parts)


def jloc(*parts) -> dict:
    return {"kind": "json_pointer", "pointer": ptr(*parts)}


def dump(obj) -> bytes:
    return (json.dumps(obj, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def claim_ref(r, country: str, year: int, used: set) -> str:
    while True:
        ref = f"CLM-{country}-{year}-{r.randint(100000, 499999):06d}"
        if ref not in KNOWN_CLAIM_REFS and ref not in used:
            used.add(ref)
            return ref


def hexid(r, n: int = 12) -> str:
    return "".join(r.choice("0123456789abcdef") for _ in range(n))


def doc_control(fid: str, approvers: list[str], reviewers: list[str] | None = None, history_authors=None,
                final_label: str | None = None) -> dict:
    on = fdate(fid)
    a = fauthor(fid)
    hist = version_history(fid, history_authors or [a], final_label=final_label)
    return {
        "documentId": DOC_PREFIX[fid],
        "title": ftitle(fid),
        "version": hist[-1]["version"],
        "status": fstatus(fid),
        "date": on,
        "owner": {"name": pname(a, on), "title": ptitle(a, on)},
        "reviewers": [{"name": pname(p, on), "title": ptitle(p, on)} for p in (reviewers or [])],
        "approvers": [{"name": pname(p, on), "title": ptitle(p, on), "date": on} for p in approvers],
        "classification": "Internal",
        "organisation": "Corvane Mutual Insurance Society Limited",
        "programme": "Programme Skerry (CLARA to Claims Hub)",
        "changeHistory": hist,
    }


# ---------------------------------------------------------------------------------------------
# ST027 Sentinel score API samples
# ---------------------------------------------------------------------------------------------

def build_ST027(out_dir: pathlib.Path) -> Built:
    fid = "ST027"
    on = fdate(fid)
    F = Facts(fid, out_dir)
    r = util.rng(f"{fid}:samples")
    need(fid, "SYSTEM:SYS03", "model_version")
    need(fid, "RULE:BR-FRD-031@v2", "parameters.tier3_threshold")
    sentinel = sysname("SYS03", on)
    if008, if036 = W.interfaces["CLX-IF-008"], W.interfaces["CLX-IF-036"]
    used: set = set()
    # (tier, score, product, claim type, country, caller)
    plan = [
        ("Tier-2", 41, "PRD-MOT-UK", "CT-COL", "UK", "triage-svc"),
        ("Tier-3", 62, "PRD-MOT-UK", "CT-BIJ", "UK", "triage-svc"),
        ("Tier-1", 12, "PRD-MOT-UK", "CT-WSC", "UK", "triage-svc"),
        ("Tier-3", 58, "PRD-HOM-UK", "CT-FIR", "UK", "CLRFR020"),
        ("Tier-2", 67, "PRD-MOT-UK", "CT-THF", "UK", "triage-svc"),
        ("Tier-3", 71, "PRD-COM-UK", "CT-FIR", "UK", "CLRFR020"),
        ("Tier-2", 33, "PRD-HOM-SE", "CT-EOW", "SE", "CLRFR020"),
        ("Tier-1", 27, "PRD-MOT-DK", "CT-COL", "DK", "triage-svc"),
        ("Tier-2", 64, "PRD-HOM-UK", "CT-EOW", "UK", "CLRFR020"),
        ("Tier-3", 60, "PRD-LIA-UK", "CT-BIJ", "UK", "CLRFR020"),
        ("Tier-2", 49, "PRD-MOT-NO", "CT-THF", "NO", "CLRFR020"),
        ("Tier-1", 8, "PRD-MOT-UK", "CT-VAN", "UK", "triage-svc"),
    ]
    extra_prd = [("PRD-MOT-UK", "CT-COL", "UK"), ("PRD-HOM-UK", "CT-EOW", "UK"), ("PRD-HOM-UK", "CT-THF", "UK"),
                 ("PRD-MOT-SE", "CT-COL", "SE"), ("PRD-HOM-NO", "CT-FRO", "NO"), ("PRD-HOM-DK", "CT-STM", "DK"),
                 ("PRD-COM-UK", "CT-EOW", "UK"), ("PRD-MOT-UK", "CT-TPD", "UK")]
    for k in range(12):
        prd, ct, cc = r.choice(extra_prd)
        tier = r.choice(["Tier-1", "Tier-2", "Tier-2", "Tier-3"])
        score = r.randint(3, 88)
        plan.append((tier, score, prd, ct, cc, r.choice(["triage-svc", "CLRFR020"])))
    reasons = ["LATE_NOTIFICATION", "RECENT_INCEPTION", "PRIOR_CLAIMS_PATTERN", "PHOTO_METADATA_MISMATCH",
               "ADDRESS_MISMATCH", "SHARED_CONTACT_DETAILS", "NIGHT_TIME_SINGLE_VEHICLE", "COVER_INCREASE_RECENT",
               "NO_THIRD_PARTY_WITNESS", "HIGH_VALUE_ITEMS_NO_RECEIPT"]
    channels = ["portal", "app", "telephone", "broker", "telematics"]
    ccy = {"UK": "GBP", "SE": "SEK", "DK": "DKK", "NO": "NOK"}
    days = ["2026-10-06", "2026-10-07", "2026-10-08", "2026-10-09"]
    requests, responses = [], []
    for i, (tier, score, prd, ct, cc, caller) in enumerate(plan):
        day = days[i % len(days)]
        hh, mm, ss = r.randint(7, 19), r.randint(0, 59), r.randint(0, 59)
        ref = claim_ref(r, cc, 2026, used)
        rid = f"req-{hexid(r, 16)}"
        corr = f"{hexid(r, 8)}-{hexid(r, 4)}-{hexid(r, 4)}-{hexid(r, 4)}-{hexid(r, 12)}"
        loss_date = minus_days(day, r.randint(1, 20))
        est = {"Tier-1": r.randint(400, 4800), "Tier-2": r.randint(6000, 45000), "Tier-3": r.randint(52000, 240000)}[tier]
        if cc != "UK":
            est = est * {"SE": 14, "DK": 9, "NO": 13}[cc]
        threshold = 60 if tier == "Tier-3" else 65
        req = {
            "request_id": rid,
            "headers": {"X-Correlation-Id": corr, "X-Caller": caller, "Content-Type": "application/json"},
            "body": {
                "claim_ref": ref, "product": prd, "claim_type": ct, "loss_date": loss_date,
                "notified_at": f"{day}T{hh:02d}:{mm:02d}:{ss:02d}Z", "channel": r.choice(channels),
                "tier": tier, "estimated_incurred_minor": est * 100, "currency": ccy[cc],
                "bodily_injury": ct == "CT-BIJ", "third_party_involved": r.random() < 0.5,
                "policy_age_days": r.randint(12, 2400),
            },
        }
        n_rc = 0 if score < 30 else (1 if score < 50 else r.randint(2, 3))
        resp = {
            "request_id": rid, "claim_ref": ref, "http_status": 200,
            "scored_at": f"{day}T{hh:02d}:{mm:02d}:{min(59, ss + 1):02d}Z",
            "score": score, "model_version": "SNT-4.2", "tier": tier,
            "threshold_applied": threshold, "referral_recommended": score >= threshold,
            "reason_codes": r.sample(reasons, n_rc), "caller": caller,
            "rule_ref": "BR-FRD-031 v2",
        }
        requests.append(req)
        responses.append(resp)
    errors = [
        {"case": "missing claim_ref", "http_status": 400,
         "body": {"type": "https://sentinel.corvane.internal/problems/validation", "title": "Invalid request",
                  "status": 400, "detail": "claim_ref is required", "code": "SNT-VAL-001"}},
        {"case": "unknown product code", "http_status": 422,
         "body": {"type": "https://sentinel.corvane.internal/problems/unprocessable", "title": "Unprocessable request",
                  "status": 422, "detail": "product is not in the configured product list", "code": "SNT-VAL-014"}},
        {"case": "scoring engine unavailable", "http_status": 503,
         "body": {"type": "https://sentinel.corvane.internal/problems/unavailable", "title": "Service unavailable",
                  "status": 503, "detail": "Scoring engine temporarily unavailable; retry with back-off",
                  "code": "SNT-SYS-503"}},
        {"case": "expired or missing token", "http_status": 401,
         "body": {"type": "https://sentinel.corvane.internal/problems/auth", "title": "Unauthorised", "status": 401,
                  "detail": "Bearer token missing or expired (CIS)", "code": "SNT-AUTH-401"}},
    ]
    t2 = rule_params_ok(fid, "BR-FRD-031", 2)
    doc = {
        "documentControl": doc_control(fid, approvers=["P008"], reviewers=["P042", "P028"]),
        "purpose": ("Request and response samples for the " + sentinel + " scoring API, captured from the test "
                    "harness after the Tier-3 referral threshold change. Payload values are synthetic."),
        "api": {
            "system": sentinel, "systemId": "SYS03", "formerName": "FRAUDNET (renamed 2025-03-01, CHUB-117)",
            "licensor": W.vendors["VEN-15"]["name"], "modelVersion": "SNT-4.2", "scoreScale": "0-100",
            "baseUrl": "https://sentinel.corvane.internal/api/v2/score",
            "authentication": "OAuth2 client credentials issued by Corvane Identity Service (CIS)",
            "callers": [
                {"interface": "CLX-IF-008", "name": if008["name"], "from": sysname("SYS01", on), "program": "CLRFR020",
                 "mapping": "SENTREQ1/SENTRSP1 copybooks via the mainframe API gateway", "criticality": if008["criticality"]},
                {"interface": "CLX-IF-036", "name": if036["name"], "from": sysname("SYS02", on), "service": "triage-svc",
                 "criticality": if036["criticality"]},
            ],
            "thresholdPolicy": {
                "rule": "BR-FRD-031 v2", "effectiveFrom": rule_ver("BR-FRD-031", 2)["effective_from"],
                "default": t2["threshold"], "tier3": t2["tier3_threshold"],
                "tierDefinition": "BR-TRI-003 v3",
                "note": "The caller passes the claim tier; the response echoes the threshold that was applied.",
            },
            "relatedRules": ["BR-TRI-007 (score within 15 minutes of FNOL)", "BR-FRD-033 (no adverse decision on score alone)"],
        },
        "requests": requests,
        "responses": responses,
        "errorSamples": errors,
        "batchSamples": {
            "requestInterface": "CLX-IF-009 Nightly Sentinel batch scoring request (CSV over SFTP, program CLRFR110)",
            "returnInterface": "CLX-IF-010 Nightly Sentinel batch score return (CSV over SFTP)",
            "requestHeader": "claim_ref,product,claim_type,loss_date,tier,estimated_incurred_minor,currency",
            "requestRows": [f"{q['body']['claim_ref']},{q['body']['product']},{q['body']['claim_type']},{q['body']['loss_date']},"
                            f"{q['body']['tier']},{q['body']['estimated_incurred_minor']},{q['body']['currency']}"
                            for q in requests if q["headers"]["X-Caller"] == "CLRFR020"],
            "returnHeader": "claim_ref,score,model_version,threshold_applied,referral_recommended",
            "returnRows": [f"{x['claim_ref']},{x['score']},{x['model_version']},{x['threshold_applied']},"
                           f"{str(x['referral_recommended']).lower()}" for x in responses if x["caller"] == "CLRFR020"],
        },
        "notes": [
            "Samples captured 2026-10-06 to 2026-10-09 in the pre-production environment.",
            "referral_recommended is advisory; the referral decision is taken by the calling service.",
            "Claim references are synthetic and do not correspond to live claims.",
            phrases.sentence(r, "api"), phrases.sentence(r, "api"),
        ],
    }
    F.add("needle", "Sentinel sample response 2 has threshold_applied 60 for a Tier-3 claim.",
          jloc("responses", 1, "threshold_applied"), "60",
          world_ref="RULE:BR-FRD-031@v2#parameters.tier3_threshold", placement="PL-169")
    F.add("general", "Sentinel sample response 2 is a Tier-3 claim scored 62 with threshold_applied 60 and referral_recommended true.",
          jloc("responses", 1), "tier: Tier-3 threshold_applied: 60 referral_recommended: true",
          world_ref="RULE:BR-FRD-031@v2")
    F.add("general", "Sentinel sample response 1 is a Tier-2 claim scored 41 against threshold 65 (not recommended for referral).",
          jloc("responses", 0), "tier: Tier-2 threshold_applied: 65 referral_recommended: false",
          world_ref="RULE:BR-FRD-031@v2#parameters.threshold")
    F.add("general", "The Sentinel scoring model version in the samples is SNT-4.2, scores on a 0-100 scale.",
          jloc("api"), "modelVersion: SNT-4.2", world_ref="SYSTEM:SYS03#model_version")
    F.add("alias_use", "Sentinel was formerly called FRAUDNET (renamed 2025-03-01, CHUB-117).",
          jloc("api", "formerName"), "FRAUDNET (renamed 2025-03-01, CHUB-117)", world_ref="SYSTEM:SYS03#renames")
    F.add("general", "Online Sentinel scoring from CLARA is interface CLX-IF-008, called by program CLRFR020 using SENTREQ1/SENTRSP1.",
          jloc("api", "callers", 0), "interface: CLX-IF-008", world_ref="INTERFACE:CLX-IF-008")
    F.add("general", "Claims Hub calls Sentinel from triage-svc over interface CLX-IF-036.",
          jloc("api", "callers", 1), "interface: CLX-IF-036", world_ref="INTERFACE:CLX-IF-036#services")
    F.add("general", "Sentinel is licensed from Kestwick Analytics Ltd.", jloc("api", "licensor"),
          "Kestwick Analytics Ltd", world_ref="VENDOR:VEN-15")
    return Built(fid, dump(doc), F.items, f"{len(responses)} rows")


# ---------------------------------------------------------------------------------------------
# ST028 Claims Hub feature flags
# ---------------------------------------------------------------------------------------------

def build_ST028(out_dir: pathlib.Path) -> Built:
    fid = "ST028"
    on = fdate(fid)
    F = Facts(fid, out_dir)
    r = util.rng(f"{fid}:flags")
    envs = ["dev", "test", "preprod", "prod"]

    def st(prod, others=None):
        o = others if others is not None else prod
        return {"dev": o, "test": o, "preprod": prod if others is None else o, "prod": prod}

    flags = [
        ("fraud.tier3-referral-threshold", "fraud-referral-svc", "Apply the Tier-3 referral threshold (BR-FRD-031 v2).",
         st(True), "2026-10-01", "CHUB-388", "BR-FRD-031 v2"),
        ("fraud.auto-decline", "fraud-referral-svc", "Automatic decline on score. Must stay off (BR-FRD-033, NISA Circular 2026/04 §3.1).",
         st(False), "2026-04-01", "CHUB-204", "BR-FRD-033"),
        ("fraud.customer-notice-deadline", "fraud-referral-svc", "Track the customer-notice deadline of 10 business days (BR-FRD-032 v2).",
         st(True), "2026-04-01", "CHUB-209", "BR-FRD-032 v2"),
        ("triage.tier3-threshold-reload", "triage-svc", "Reload referral thresholds from configuration without restart.",
         st(True), "2026-10-05", "CHUB-392", None),
        ("reserve.tier3-review-14-days", "reserve-engine", "Schedule Tier-3 reserve reviews every 14 days (BR-RSV-007 v3).",
         st(True), "2026-07-03", "CHUB-322", "BR-RSV-007 v3"),
        ("reserve.revaluation-run", "reserve-engine", "Use the reserve-engine revaluation run instead of CLRGL090 (ADR-028); planned for Wave 2.",
         st(False, True), None, None, None),
        ("reserve.parallel-run-reconciliation", "reserve-engine", "Daily reconciliation against CLARA during the reserve parallel run (ended 2026-08-28).",
         st(False), "2026-08-28", "CHUB-241", None),
        ("payments.idempotency-key", "payment-orchestrator", "Send an idempotency key with every CPG payment instruction (ADR-021).",
         st(True), "2026-09-16", "CHUB-371", None),
        ("assessment.motor-uk-wave1", "assessment-svc", "Route UK motor assessments to Claims Hub after the Wave 1 cut-over.",
         st(True), "2026-09-14", "CHUB-340", None),
        ("recovery.write-off-approval", "recovery-svc", "Require Head of Recoveries & Subrogation approval for write-offs above £10,000 (BR-REC-011 v2).",
         st(True), "2026-09-14", "CHUB-409", "BR-REC-011 v2"),
        ("documents.evidence-vault-endpoint", "document-svc", "Use the Evidence Vault base URL (DOCSTOR retired at the rename).",
         st(True), "2025-11-03", "CHUB-219", None),
        ("intake.telematics-draft-fnol", "fnol-intake-svc", "Create draft FNOLs from telematics crash alerts (BR-FNOL-009).",
         st(True), "2025-11-03", None, "BR-FNOL-009"),
        ("intake.portal-fnol-to-hub", "fnol-intake-svc", "Send portal FNOLs to Claims Hub (CLX-IF-035).",
         st(True), "2026-09-14", None, None),
        ("migration.wave2-readonly-clara", "claim-core-svc", "Read-only CLARA enquiry after cut-over (ADR-026, proposed).",
         st(False, True), None, None, None),
        ("reporting.dual-run-extracts", "reporting-feed-svc", "Dual-run regulatory extracts for two quarters (ADR-027, proposed).",
         st(False, True), None, None, None),
        ("notification.nordic-language-preference", "notification-svc", "Use the customer's language preference (BR-FNOL-013).",
         st(True), "2025-11-03", None, "BR-FNOL-013"),
    ]
    out = []
    for key, svc, desc, states, since, ticket, rule in flags:
        o = svc_owner(fid, svc, on)
        e = {"key": key, "service": svc, "description": desc,
             "owner": team_name(o["team"], on) if o else None,
             "type": "release" if since else "experiment", "states": states}
        if since:
            e["enabledSince"] = since if states["prod"] else None
            if not states["prod"]:
                e["disabledSince"] = since
                e.pop("enabledSince")
        if ticket:
            e["ticket"] = ticket
        if rule:
            e["rule"] = rule
        e["lastChanged"] = since or "2026-10-30"
        out.append(e)
    doc = {
        "documentControl": doc_control(fid, approvers=["P032"], reviewers=["P049", "P041", "P042"]),
        "platform": {"system": sysname("SYS02", on), "flagStore": "Spring Cloud Config backed by the platform config repository",
                     "environments": envs, "evaluation": "Flags are read at start-up and refreshed by the config bus."},
        "flags": out,
        "conventions": [
            "Flag keys use <domain>.<feature> in kebab case.",
            "Release flags are removed one release after they reach 100% in prod.",
            "Business-rule values are not flags; they live in the effective-dated rules configuration (ADR-010).",
            phrases.sentence(r, "design"),
        ],
    }
    i_t3 = [f["key"] for f in out].index("fraud.tier3-referral-threshold")
    i_ad = [f["key"] for f in out].index("fraud.auto-decline")
    i_rv = [f["key"] for f in out].index("reserve.revaluation-run")
    F.add("general", "Feature flag fraud.tier3-referral-threshold is enabled in prod since 2026-10-01 (CHUB-388, BR-FRD-031 v2).",
          jloc("flags", i_t3), "enabledSince: 2026-10-01", world_ref="TICKET:CHUB-388")
    F.add("general", "Feature flag fraud.auto-decline is off in every environment (BR-FRD-033).",
          jloc("flags", i_ad, "states"), "prod: false", world_ref="RULE:BR-FRD-033@v1#parameters.auto_decline_allowed")
    F.add("general", "The reserve-engine revaluation run (ADR-028) is off in prod and planned for Wave 2.",
          jloc("flags", i_rv), "reserve.revaluation-run", world_ref="ADR:ADR-028")
    return Built(fid, dump(doc), F.items, f"{len(out)} rows")


# ---------------------------------------------------------------------------------------------
# ST029 Fraud rule parameters
# ---------------------------------------------------------------------------------------------

def build_ST029(out_dir: pathlib.Path) -> Built:
    fid = "ST029"
    on = fdate(fid)
    F = Facts(fid, out_dir)
    cfg = W.services["fraud-referral-svc"]["config"]
    for k in cfg:
        need(fid, "SERVICE:fraud-referral-svc", f"config.{k}")
    v2 = rule_params_ok(fid, "BR-FRD-036", 2)
    hist = []
    for rid, ver in (("BR-FRD-012", 1), ("BR-FRD-012", 2), ("BR-FRD-031", 1), ("BR-FRD-031", 2)):
        v = rule_ver(rid, ver)
        p = rule_params_ok(fid, rid, ver)
        hist.append({"rule": f"{rid} v{ver}", "status": v["status"], "effectiveFrom": v["effective_from"],
                     "effectiveTo": v["effective_to"], "threshold": p.get("threshold"),
                     "tier3Threshold": p.get("tier3_threshold"), "approvedOn": v["approved_on"],
                     "source": v["source"]})
    indicators = []
    for rid in ["BR-FRD-001", "BR-FRD-002", "BR-FRD-003", "BR-FRD-004", "BR-FRD-006", "BR-FRD-007", "BR-FRD-008",
                "BR-FRD-009", "BR-FRD-014", "BR-FRD-015", "BR-FRD-016"]:
        v = W.rule_version(rid, on)
        p = rule_params_ok(fid, rid, v["version"])
        indicators.append({"rule": f"{rid} v{v['version']}", "indicator": W.rules[rid]["title"].replace("Indicator: ", ""),
                           "points": p.get("pts"), "effectiveFrom": v["effective_from"]})
    f005 = W.rule_version("BR-FRD-005", on)
    doc = {
        "documentControl": doc_control(fid, approvers=["P008", "P005"], reviewers=["P027", "P037"]),
        "service": "fraud-referral-svc",
        "configSource": "effective-dated rules configuration (ADR-020)",
        "effectiveAsOf": on,
        "scoreScale": {"system": sysname("SYS03", on), "min": 0, "max": 100},
        "referral": {
            "threshold": {
                "default": cfg["referral.threshold.default"],
                "tier3": cfg["referral.threshold.tier3"],
                "tier3.effective-from": cfg["referral.threshold.tier3.effective-from"],
                "rule": "BR-FRD-031 v2",
                "tierDefinition": "BR-TRI-003 v3",
                "decision": "DEC-014 (Fraud Rules Workshop 2026-09-17)",
            },
            "history": hist,
            "clara": {"paramTable": "CLR.T_PARAM", "keys": ["FRD_REFER_THRESH", "FRD_REFER_T3_THRESH"],
                      "readBy": "CLRCM040 (parameter reader)", "tickets": ["CHUB-205", "CHUB-395"]},
        },
        "notice": {
            "business-days": cfg["notice.business-days"], "rule": "BR-FRD-032 v2",
            "max-deferral-days": cfg["notice.max-deferral-days"],
            "head-approval-after-days": v2.get("head_approval_after_days"),
            "head-approval-role": "Head of Counter-Fraud & SIU",
            "notify-on-long-deferral": v2.get("notify"),
            "deferral-rule": "BR-FRD-036 v2",
        },
        "auto-decline": {"enabled": cfg["auto-decline.enabled"], "rule": "BR-FRD-033 v1",
                         "replaces": "BR-FRD-019 v2 (withdrawn from 2026-04-01)"},
        "siu-triage": {"business-days": rule_params_ok(fid, "BR-FRD-035", 2)["business_days"], "rule": "BR-FRD-035 v2"},
        "fr1-return": {"due-days-after-quarter": rule_params_ok(fid, "BR-FRD-034", 1)["due_days_after_quarter"],
                       "rule": "BR-FRD-034 v1", "firstPeriod": "2026Q2"},
        "linked-claims": {"rule": f"BR-FRD-005 v{f005['version']}", **rule_params_ok(fid, "BR-FRD-005", f005["version"])},
        "pre-screen-indicators": indicators,
        "approval": {"approvedBy": [pname("P008", on), pname("P005", on)], "approvedOn": "2026-09-17",
                     "changeTickets": ["CHUB-388", "CHUB-395"]},
    }
    F.add("needle", "Fraud parameters: referral.threshold.tier3 = 60 effective from 2026-10-01; default 65.",
          jloc("referral", "threshold"), "tier3: 60 tier3.effective-from: 2026-10-01",
          world_ref="SERVICE:fraud-referral-svc#config", placement="PL-170")
    F.add("general", "Fraud parameters: default referral threshold is 65 (BR-FRD-031 v2).",
          jloc("referral", "threshold"), "default: 65", world_ref="SERVICE:fraud-referral-svc#config.referral.threshold.default")
    F.add("temporal", "BR-FRD-012 v2 set the referral threshold at 70 from 2023-04-01 to 2026-03-31.",
          jloc("referral", "history", 1), "effectiveTo: 2026-03-31 threshold: 70", world_ref="RULE:BR-FRD-012@v2")
    F.add("general", "Customer notice deferrals beyond 30 days need the Head of Counter-Fraud & SIU (BR-FRD-036 v2).",
          jloc("notice"), "head-approval-after-days: 30", world_ref="RULE:BR-FRD-036@v2#parameters.head_approval_after_days")
    F.add("general", "Customer notice must be sent within 10 business days of referral (BR-FRD-032 v2).",
          jloc("notice", "business-days"), "10", world_ref="RULE:BR-FRD-032@v2#parameters.notice_business_days")
    F.add("general", "SIU triage of new referrals within 3 business days (BR-FRD-035 v2).",
          jloc("siu-triage"), "business-days: 3", world_ref="RULE:BR-FRD-035@v2")
    F.add("general", "CLARA reads the Tier-3 threshold from CLR.T_PARAM key FRD_REFER_T3_THRESH (CHUB-395).",
          jloc("referral", "clara"), "FRD_REFER_T3_THRESH", world_ref="TABLE:CLR.T_PARAM#param_rows:FRD_REFER_T3_THRESH")
    ind_shared = [i for i, x in enumerate(indicators) if x["rule"].startswith("BR-FRD-009")][0]
    F.add("general", "Pre-screen indicator BR-FRD-009 (shared bank account) adds 20 points.",
          jloc("pre-screen-indicators", ind_shared), "points: 20", world_ref="RULE:BR-FRD-009@v1#parameters.pts")
    return Built(fid, dump(doc), F.items, f"{len(indicators) + len(hist)} rows")


# ---------------------------------------------------------------------------------------------
# ST030 Kafka topic catalogue
# ---------------------------------------------------------------------------------------------

TOPIC_IFACE = {"fnol.received.v1": "CLX-IF-034", "reserve.changed.v2": "CLX-IF-045",
               "claims.reserve.movement.v1": "CLX-IF-049", "claim.created.v1": "CLX-IF-056",
               "claim.updated.v1": "CLX-IF-056", "eig.telematics.alert.v1": "CLX-IF-057"}
# derivable owners only: EIG system owner (P040 -> T27), CLX-IF-049 interface owner (P031 -> T22)
EXTERNAL_PRODUCER_OWNER = {"Evidence Intake Gateway": "T27", "MQ-to-Kafka bridge (CLX-IF-049)": "T22"}


def topics_as_of(on: str) -> list[dict]:
    return [t for t in W.topics.values() if str(t.get("introduced") or "0000") <= on]


def topic_owner_team(t: dict, on: str) -> str | None:
    p = t["producer"]
    if p in W.services:
        return W.service_owner(p, on)["team"]
    return EXTERNAL_PRODUCER_OWNER.get(p)


def build_ST030(out_dir: pathlib.Path) -> Built:
    fid = "ST030"
    on = fdate(fid)
    F = Facts(fid, out_dir)
    r = util.rng(f"{fid}:topics")
    out = []
    for t in topics_as_of(on):
        ref = f"TOPIC:{t['name']}"
        e = {"name": t["name"]}
        need(fid, ref, "partitions")
        e["partitions"] = t["partitions"]
        if may(fid, ref, "retention_days"):
            e["retentionDays"] = t["retention_days"]
        e["replicationFactor"] = 3
        e["cleanupPolicy"] = "delete"
        e["format"] = "JSON" if t["name"].startswith("eig.telematics") else "Avro"
        e["schemaSubject"] = f"{t['name']}-value"
        if t.get("schema_version"):
            e["schemaVersion"] = t["schema_version"]
        if t.get("key"):
            e["key"] = t["key"]
        prod = t["producer"]
        e["producer"] = svcname(prod, on) if prod in W.services else prod
        e["consumers"] = [svcname(c, on) if c in W.services else c for c in t["consumers"]]
        e["consumerGroups"] = [f"{(svcname(c, on) if c in W.services else c).lower().replace(' ', '-')}.{t['name'].replace('.', '-')}"
                               for c in t["consumers"]]
        tm = topic_owner_team(t, on)
        if tm:
            e["ownerTeam"] = team_name(tm, on)
        e["cluster"] = "esp-prd"
        e["platform"] = f"{sysname('SYS15', on)} (SYS15)"
        if t["name"] in TOPIC_IFACE:
            e["interface"] = TOPIC_IFACE[t["name"]]
        if t.get("introduced"):
            e["introduced"] = t["introduced"]
        if t.get("ticket"):
            e["ticket"] = t["ticket"]
        if prod in W.services:
            e["description"] = f"Events from {svcname(prod, on)}: {W.services[prod]['description']}."
        e["dataClassification"] = "Internal"
        e["compatibility"] = "BACKWARD"
        if t.get("note"):
            e["note"] = t["note"]
        out.append(e)
    # catalogue order: alphabetical by domain
    out.sort(key=lambda x: x["name"])
    idx = {e["name"]: i for i, e in enumerate(out)}
    mv = out[idx["claims.reserve.movement.v1"]]
    assert "retentionDays" not in mv
    doc = {
        "documentControl": doc_control(fid, approvers=["P018"], reviewers=["P050", "P041"]),
        "cluster": {"name": "esp-prd", "system": sysname("SYS15", on), "systemId": "SYS15",
                    "technology": W.systems["SYS15"]["tech"], "hosting": W.systems["SYS15"]["hosting"],
                    "owner": pname("P031", on)},
        "conventions": {
            "naming": "<domain>.<entity>.<event>.v<major>",
            "schemas": "Avro schemas registered per subject <topic>-value; compatibility BACKWARD",
            "contractTests": "Every topic has consumer contract tests in the pipeline (ADR-023)",
            "changes": "New topics and partition changes go through the Integration Platform change process.",
        },
        "topicCount": len(out),
        "topics": out,
        "retiredTopics": [{"name": "reserve.changed.v1", "retiredOn": "2026-02-10", "ticket": "CHUB-233",
                           "replacedBy": "reserve.changed.v2", "reason": "Retired with the reserve-svc rename (ADR-019)."}],
        "notes": [
            "Topic list as at 2026-09-30, after the Wave 1 cut-over.",
            "reserve.changed.v1 was retired with the reserve-svc rename (CHUB-233).",
            phrases.sentence(r, "interface_ops", "The event backbone"),
        ],
    }
    F.add("needle", "Kafka catalogue: claims.reserve.movement.v1 has 12 partitions.",
          jloc("topics", idx["claims.reserve.movement.v1"]), "claims.reserve.movement.v1 partitions: 12",
          world_ref="TOPIC:claims.reserve.movement.v1#partitions", exclusive=True, placement="PL-171",
          notes="Retention is deliberately omitted for this topic (retention is exclusive to LD013).")
    F.add("general", "claims.reserve.movement.v1 is keyed by claim_id, schema version 3, produced by the MQ-to-Kafka bridge (CLX-IF-049) and consumed by reserve-engine.",
          jloc("topics", idx["claims.reserve.movement.v1"], "key"), "claim_id",
          world_ref="TOPIC:claims.reserve.movement.v1#key")
    F.add("general", "reserve.changed.v2 is produced by reserve-engine and consumed by gl-posting-svc and reporting-feed-svc.",
          jloc("topics", idx["reserve.changed.v2"], "consumers"), "gl-posting-svc", world_ref="TOPIC:reserve.changed.v2#consumers")
    F.add("general", "fraud.referral.notice-due.v1 is consumed by notification-svc.",
          jloc("topics", idx["fraud.referral.notice-due.v1"], "consumers"), "notification-svc",
          world_ref="TOPIC:fraud.referral.notice-due.v1#consumers")
    F.add("general", "triage.completed.v1 has three consumers: reserve-engine, fraud-referral-svc and assessment-svc.",
          jloc("topics", idx["triage.completed.v1"], "consumers"), "reserve-engine",
          world_ref="TOPIC:triage.completed.v1#consumers")
    F.add("scale", f"The Kafka topic catalogue lists {len(out)} topics on cluster esp-prd as at 2026-09-30.",
          jloc("topicCount"), str(len(out)), world_ref="SYSTEM:SYS15")
    return Built(fid, dump(doc), F.items, f"{len(out)} rows")


# ---------------------------------------------------------------------------------------------
# ST031 Service registry
# ---------------------------------------------------------------------------------------------

def svc_topics(fid: str, svc: str, kind: str, on: str) -> list[str]:
    out = []
    for t in W.services[svc]["kafka_topics"][kind]:
        if not may(fid, f"SERVICE:{svc}", f"kafka_topics.{kind}:{t}"):
            continue
        tt = W.topics.get(t)
        if tt and str(tt.get("introduced") or "0000") > on:
            continue
        if not may(fid, f"TOPIC:{t}"):
            continue
        out.append(t)
    return out


def svc_owner(fid: str, svc: str, on: str) -> dict | None:
    o = W.service_owner(svc, on)
    if o is None or not may(fid, f"SERVICE:{svc}", f"owner_history:{o['team']}"):
        return None
    return o


def build_ST031(out_dir: pathlib.Path) -> Built:
    fid = "ST031"
    on = fdate(fid)
    F = Facts(fid, out_dir)
    r = util.rng(f"{fid}:registry")
    rules_by_svc: dict[str, list[str]] = {}
    for rid, rr in W.rules.items():
        v = W.rule_version(rid, on)
        if not v:
            continue
        for s in rr["implemented_in"]["services"]:
            rules_by_svc.setdefault(s, []).append(f"{rid} v{v['version']}")
    ifaces_by_svc: dict[str, list[str]] = {}
    for i in W.interfaces.values():
        for s in i["services"]:
            ifaces_by_svc.setdefault(s, []).append(i["id"])
    services = []
    pos = {}
    for sid, s in W.services_by_id.items():
        name = svcname(sid, on)
        e = {"id": sid, "name": name, "description": s["description"], "status": s["status"], "goLive": s["go_live"]}
        if s["renames"]:
            e["formerNames"] = [{"name": rn["from_name"], "renamedOn": rn["date"], "ticket": rn["ticket"], "adr": rn["adr"]}
                                for rn in s["renames"] if rn["date"] <= on]
        o = svc_owner(fid, s["name"], on)
        if o:
            e["owner"] = {"team": team_name(o["team"], on), "teamId": o["team"], "lead": pname(o["person"], on)}
        e["runtime"] = {"namespace": s["k8s_namespace"], "replicas": s["replicas"], "image": s["image"],
                        "cluster": "ocp-prd-lon1", "drCluster": "ocp-dr-lds1"}
        if s.get("infra"):
            inf = {}
            for k in ("cpu_request", "memory_limit"):
                if k in s["infra"] and may(fid, f"SERVICE:{s['name']}", f"infra.{k}"):
                    inf[k.replace("_", "-")] = s["infra"][k]
            if inf:
                e["runtime"]["resources"] = inf
        e["endpoints"] = {
            "internal": f"http://{name}.{s['k8s_namespace']}.svc.cluster.local:8080",
            "route": f"https://{name}.apps.ocp-prd-lon1.corvane.internal",
            "openapi": f"https://{name}.apps.ocp-prd-lon1.corvane.internal/v3/api-docs",
            "health": "/actuator/health",
        }
        e["apis"] = [{"method": a["method"], "path": a["path"], "summary": a["summary"]} for a in s["apis"]]
        e["kafka"] = {"produces": svc_topics(fid, s["name"], "produces", on),
                      "consumes": svc_topics(fid, s["name"], "consumes", on)}
        e["data"] = [{"table": t, "database": W.tables[t]["database"]} for t in s["postgres_tables"]]
        e["replacesPrograms"] = s["replaces_programs"]
        if s.get("config"):
            cfgs = {k: v for k, v in s["config"].items() if k != "config_history" and may(fid, f"SERVICE:{s['name']}", f"config.{k}")}
            e["config"] = cfgs
        e["interfaces"] = sorted(ifaces_by_svc.get(s["name"], []))
        e["rules"] = sorted(rules_by_svc.get(s["name"], []))
        e["source"] = {"repoPath": s["repo_path"], "terraformModule": s["terraform_module"]}
        pos[s["name"]] = len(services)
        services.append(e)
    doc = {
        "documentControl": doc_control(fid, approvers=["P018", "P032"], reviewers=["P053", "P041", "P042", "P040"]),
        "platform": {"system": sysname("SYS02", on), "systemId": "SYS02", "technology": W.systems["SYS02"]["tech"],
                     "hosting": W.systems["SYS02"]["hosting"], "productOwner": pname("P017", on),
                     "registry": "registry.corvane.internal/chub"},
        "serviceCount": len(services),
        "services": services,
        "notes": [
            "Registry snapshot as at " + on + ".",
            "Ownership follows the squad model; see the Claims Hub home page for squads.",
            phrases.sentence(r, "design"), phrases.sentence(r, "design"),
        ],
    }
    re_ = pos["reserve-engine"]
    fr = pos["fraud-referral-svc"]
    F.add("alias_use", "reserve-engine (SVC05) was formerly named reserve-svc; renamed on 2026-02-10 under CHUB-233 / ADR-019.",
          jloc("services", re_, "formerNames", 0), "name: reserve-svc renamedOn: 2026-02-10",
          world_ref="SERVICE:reserve-engine#renames")
    F.add("general", "reserve-engine runs in namespace chub-reserve with 4 replicas.",
          jloc("services", re_, "runtime"), "namespace: chub-reserve replicas: 4", world_ref="SERVICE:reserve-engine#replicas")
    F.add("general", "reserve-engine config: Tier-3 review every 14 days; large loss threshold £250,000.",
          jloc("services", re_, "config"), "tier3-review-days: 14", world_ref="SERVICE:reserve-engine#config.tier3-review-days")
    F.add("general", "reserve-engine POST /revaluation-runs triggers a currency revaluation run that replaces CLRGL090.",
          jloc("services", re_, "apis", 3, "summary"), "replaces CLRGL090", world_ref="SERVICE:reserve-engine#apis")
    F.add("general", "fraud-referral-svc configuration: referral.threshold.tier3 60 from 2026-10-01; default 65; notice 10 business days; max deferral 60 days; auto-decline disabled.",
          jloc("services", fr, "config"), "referral.threshold.tier3: 60", world_ref="SERVICE:fraud-referral-svc#config")
    F.add("general", "fraud-referral-svc is owned by Hub Squad – Fraud & Settlement, led by Linnea Sjöberg.",
          jloc("services", fr, "owner"), "lead: Linnea Sjöberg", world_ref="SERVICE:fraud-referral-svc#owner_person")
    F.add("general", "reserve-engine replaces 16 CLARA programs including CLRGL090 and CLRRS150.",
          jloc("services", re_, "replacesPrograms"), "CLRGL090", world_ref="SERVICE:reserve-engine#replaces_programs")
    F.add("general", "reporting-feed-svc is in development with go-live 2027-01-11.",
          jloc("services", pos["reporting-feed-svc"]), "status: in development goLive: 2027-01-11",
          world_ref="SERVICE:reporting-feed-svc#go_live")
    return Built(fid, dump(doc), F.items, f"{len(services)} rows")


# ---------------------------------------------------------------------------------------------
# ST032 Fraud referral event samples
# ---------------------------------------------------------------------------------------------

def build_ST032(out_dir: pathlib.Path) -> Built:
    fid = "ST032"
    on = fdate(fid)
    F = Facts(fid, out_dir)
    r = util.rng(f"{fid}:events")
    used: set = set()
    events = []

    def envelope(topic, producer, day, key, payload, schema_v=1):
        hh, mm, ss = r.randint(6, 20), r.randint(0, 59), r.randint(0, 59)
        return {
            "topic": topic,
            "partitionKey": key,
            "headers": {"eventId": hexid(r, 32), "eventType": topic.rsplit(".", 1)[0], "schemaVersion": schema_v,
                        "producer": producer, "correlationId": hexid(r, 32),
                        "occurredAt": f"{day}T{hh:02d}:{mm:02d}:{ss:02d}Z"},
            "payload": payload,
        }

    scenarios = [
        # (day, tier, score, product, ct)
        ("2026-10-06", "Tier-3", 63, "PRD-MOT-UK", "CT-BIJ"),
        ("2026-10-06", "Tier-2", 66, "PRD-HOM-UK", "CT-EOW"),
        ("2026-10-07", "Tier-3", 61, "PRD-COM-UK", "CT-FIR"),
        ("2026-10-07", "Tier-2", 70, "PRD-MOT-UK", "CT-THF"),
        ("2026-10-08", "Tier-3", 59, "PRD-MOT-UK", "CT-COL"),
        ("2026-10-08", "Tier-1", 22, "PRD-MOT-UK", "CT-WSC"),
        ("2026-10-08", "Tier-2", 68, "PRD-MOT-UK", "CT-COL"),
        ("2026-10-09", "Tier-3", 64, "PRD-LIA-UK", "CT-BIJ"),
        ("2026-10-09", "Tier-2", 55, "PRD-HOM-UK", "CT-THF"),
    ]
    referral_idx = {}
    for n, (day, tier, score, prd, ct) in enumerate(scenarios):
        ref = claim_ref(r, "UK", 2026, used)
        thr = 60 if tier == "Tier-3" else 65
        events.append(envelope("triage.completed.v1", "triage-svc", day, ref,
                               {"claimId": ref, "product": prd, "claimType": ct, "tier": tier,
                                "tierRule": "BR-TRI-003 v3",
                                "route": {"Tier-3": "MAJOR_COMPLEX", "Tier-2": "SPECIALIST", "Tier-1": "FAST_TRACK_CHECK"}[tier],
                                "triagedBy": "triage-svc"}))
        events.append(envelope("fraud.score.received.v1", "triage-svc", day, ref,
                               {"claimId": ref, "score": score, "modelVersion": "SNT-4.2", "tier": tier,
                                "thresholdApplied": thr, "referralRecommended": score >= thr,
                                "scoringInterface": "CLX-IF-036"}))
        if score >= thr:
            rid = f"FRF-2026-{r.randint(10000, 99999)}"
            due = add_business_days(day, 10).isoformat()
            events.append(envelope("fraud.referral.created.v1", "fraud-referral-svc", day, ref,
                                   {"referralId": rid, "claimId": ref, "referralDate": day, "score": score, "tier": tier,
                                    "thresholdApplied": thr, "thresholdRule": "BR-FRD-031 v2",
                                    "siuTriageDueBy": add_business_days(day, 3).isoformat(),
                                    "siuCaseInterface": "CLX-IF-041", "createdBy": "fraud-referral-svc"}))
            referral_idx[n] = len(events) - 1
            deferred = n == 2
            payload = {"referralId": rid, "claimId": ref, "referralDate": day, "noticeDueDate": due,
                       "deadlineRule": "BR-FRD-032 v2 (referral date + 10 business days)",
                       "deferred": deferred, "recipientChannel": r.choice(["letter", "email"])}
            if deferred:
                payload.update({"deferralDays": 45, "deferralRule": "BR-FRD-036 v2",
                                "deferralApprovedBy": {"name": pname("P008", on), "role": ptitle("P008", on)},
                                "complianceNotified": True, "complianceNotifiedOn": day,
                                "deferredUntil": plus_days(day, 45)})
            events.append(envelope("fraud.referral.notice-due.v1", "fraud-referral-svc", day, ref, payload))
    doc = {
        "documentControl": doc_control(fid, approvers=["P042"], reviewers=["P054", "P028"]),
        "purpose": "Sample events for the fraud referral flow, for consumer contract tests (ADR-023). Values are synthetic.",
        "topics": {
            "triage.completed.v1": {"producer": "triage-svc", "consumers": W.topics["triage.completed.v1"]["consumers"]},
            "fraud.score.received.v1": {"producer": "triage-svc", "consumers": W.topics["fraud.score.received.v1"]["consumers"]},
            "fraud.referral.created.v1": {"producer": "fraud-referral-svc", "consumers": W.topics["fraud.referral.created.v1"]["consumers"]},
            "fraud.referral.notice-due.v1": {"producer": "fraud-referral-svc", "consumers": W.topics["fraud.referral.notice-due.v1"]["consumers"]},
        },
        "events": events,
        "notes": [
            "Events captured 2026-10-06 to 2026-10-08, after the Tier-3 threshold change and the triage-svc reload fix.",
            "Business-day calculations use the UK calendar from the date utility.",
            phrases.sentence(r, "design"), phrases.sentence(r, "api"),
        ],
    }
    # facts
    nd = [i for i, e in enumerate(events) if e["topic"] == "fraud.referral.notice-due.v1"]
    defer_i = [i for i in nd if events[i]["payload"]["deferred"]][0]
    first_nd = nd[0]
    F.add("general", f"Notice-due sample: referral on {events[first_nd]['payload']['referralDate']} has notice due {events[first_nd]['payload']['noticeDueDate']} (referral date + 10 business days, BR-FRD-032 v2).",
          jloc("events", first_nd, "payload"), f"noticeDueDate: {events[first_nd]['payload']['noticeDueDate']}",
          world_ref="RULE:BR-FRD-032@v2#parameters.notice_business_days")
    F.add("general", "A 45-day customer-notice deferral is approved by the Head of Counter-Fraud & SIU and Compliance is notified the same day (BR-FRD-036 v2).",
          jloc("events", defer_i, "payload"), "deferralRule: BR-FRD-036 v2", world_ref="RULE:BR-FRD-036@v2")
    t3 = [i for i, e in enumerate(events) if e["topic"] == "fraud.referral.created.v1" and e["payload"]["tier"] == "Tier-3"][0]
    F.add("general", "A Tier-3 fraud.referral.created.v1 sample shows thresholdApplied 60 under BR-FRD-031 v2.",
          jloc("events", t3, "payload"), "thresholdApplied: 60 thresholdRule: BR-FRD-031 v2",
          world_ref="RULE:BR-FRD-031@v2#parameters.tier3_threshold")
    sc = [i for i, e in enumerate(events) if e["topic"] == "fraud.score.received.v1" and e["payload"]["score"] == 59][0]
    F.add("general", "A Tier-3 claim scored 59 is not recommended for referral (threshold 60).",
          jloc("events", sc, "payload"), "score: 59", world_ref="RULE:BR-FRD-031@v2")
    F.add("general", "fraud.referral.created.v1 is consumed by reporting-feed-svc.",
          jloc("topics", "fraud.referral.created.v1"), "reporting-feed-svc", world_ref="TOPIC:fraud.referral.created.v1#consumers")
    return Built(fid, dump(doc), F.items, f"{len(events)} rows")


# ---------------------------------------------------------------------------------------------
# ST033 Data quality report - Wave 1
# ---------------------------------------------------------------------------------------------

DQ_DIMENSIONS = ["completeness", "validity", "uniqueness", "referential_integrity", "consistency", "timeliness"]


def build_ST033(out_dir: pathlib.Path) -> Built:
    fid = "ST033"
    on = fdate(fid)
    F = Facts(fid, out_dir)
    r = util.rng(f"{fid}:dq")
    used: set = set()
    wave = W.waves["MW-1"]
    need(fid, "WAVE:MW-1", "rehearsals")
    # target tables in scope for UK motor
    scope = [
        ("claim_core.claim", "CLR.T_CLAIM", "claim-core-svc"),
        ("claim_core.party", "CLR.T_CLAIMANT", "claim-core-svc"),
        ("fnol.notification", "CLR.T_FNOL_EVENT", "fnol-intake-svc"),
        ("triage.triage_decision", "CLR.T_TRIAGE", "triage-svc"),
        ("assessment.assessment", "CLR.T_ASSESSMENT", "assessment-svc"),
        ("assessment.assessor_assignment", "CLR.T_ASSESSOR_ASSIGNMENT", "assessment-svc"),
        ("reserve.reserve", "CLR.T_RESERVE", "reserve-engine"),
        ("reserve.reserve_movement", "CLR.T_RESERVE_MOVEMENT", "reserve-engine"),
        ("reserve.review_schedule", "CLR.T_RESERVE", "reserve-engine"),
        ("fraud.referral", "CLR.T_FRAUD_REFERRAL", "fraud-referral-svc"),
        ("settlement.settlement", "CLR.T_SETTLEMENT", "settlement-svc"),
        ("payment.payment_instruction", "CLR.T_PAYMENT", "payment-orchestrator"),
        ("recovery.recovery_case", "CLR.T_SUBROGATION_CASE", "recovery-svc"),
        ("recovery.receipt", "CLR.T_RECOVERY", "recovery-svc"),
        ("document.document", "CLR.T_DOCUMENT_REF", "document-svc"),
    ]
    rule_text = {
        "completeness": "Mandatory column {col} is populated for every migrated row",
        "validity": "Column {col} holds a value allowed by the target domain",
        "uniqueness": "Primary key {col} is unique in the target table",
        "referential_integrity": "Every {col} resolves to its parent record",
        "consistency": "Column {col} equals the CLARA source value after transformation",
        "timeliness": "Column {col} carries the source time stamp converted to UTC",
    }
    checks = []
    n = 0
    status_counts = {"PASS": 0, "WARN": 0, "FAIL": 0}
    for tgt, src, svc in scope:
        cols = [c for c in W.tables[tgt]["columns"]]
        src_cols = [c["name"] for c in W.tables[src]["columns"]]
        dims = r.sample(DQ_DIMENSIONS, k=min(len(DQ_DIMENSIONS), r.randint(4, 6)))
        pk = W.tables[tgt]["primary_key"][0]
        notnull = [x for x in cols if not x["nullable"] and x["name"] != pk] or cols
        refcols = [x for x in cols if x["name"].endswith("_id") and x["name"] != pk] or [x for x in cols if x["name"] == pk]
        for dim in dims:
            c = {"uniqueness": [x for x in cols if x["name"] == pk][0],
                 "referential_integrity": r.choice(refcols),
                 "completeness": r.choice(notnull)}.get(dim) or r.choice(cols)
            n += 1
            roll = r.random()
            if roll < 0.78:
                status, exc = "PASS", 0
            elif roll < 0.95:
                status, exc = "WARN", r.randint(1, 24)
            else:
                status, exc = "FAIL", r.randint(3, 40)
            status_counts[status] += 1
            samples = []
            for _ in range(min(exc, 3)):
                samples.append({"claimRef": claim_ref(r, "UK", r.choice([2019, 2021, 2023, 2024, 2025, 2026]), used),
                                "column": c["name"], "issue": r.choice([
                                    "null in source", "value outside target domain", "orphan child row",
                                    "source/target mismatch after rounding", "duplicate business key in source",
                                    "time zone offset missing", "legacy code without mapping"])})
            chk = {
                "checkId": f"DQ-W1-{n:03d}", "dimension": dim, "targetTable": tgt,
                "targetDatabase": W.tables[tgt]["database"], "sourceTable": src,
                "sourceColumns": r.sample(src_cols, k=min(2, len(src_cols))),
                "rule": rule_text[dim].format(col=c["name"]),
                "query": {"completeness": f"SELECT COUNT(*) FROM {tgt} t WHERE t.{c['name']} IS NULL",
                          "validity": f"SELECT COUNT(*) FROM {tgt} t LEFT JOIN allowed a ON a.code = t.{c['name']} WHERE a.code IS NULL",
                          "uniqueness": f"SELECT {c['name']}, COUNT(*) FROM {tgt} GROUP BY {c['name']} HAVING COUNT(*) > 1",
                          "referential_integrity": f"SELECT COUNT(*) FROM {tgt} t LEFT JOIN parent p ON p.key = t.{c['name']} WHERE p.key IS NULL",
                          "consistency": f"SELECT COUNT(*) FROM {tgt} t JOIN src_extract s ON s.claim_key = t.claim_key WHERE t.{c['name']} <> s.mapped_value",
                          "timeliness": f"SELECT COUNT(*) FROM {tgt} t WHERE t.{c['name']} IS NOT NULL AND t.{c['name']} > now()"}[dim],
                "queryNote": {"validity": "allowed = target domain list for the column",
                              "referential_integrity": "parent = keys of the parent record in the target model",
                              "consistency": f"src_extract = transformed unload of {src}"}.get(dim),
                "status": status, "exceptions": exc, "owningService": svc,
                "disposition": (None if status == "PASS" else r.choice(["fixed post cut-over", "accepted (CLARA data issue)",
                                                                        "open - assigned to squad", "fixed in hypercare patch"])),
                "sampleExceptions": samples,
                "comment": phrases.sentence(r, "data_quality"),
            }
            checks.append(chk)
    first_rsv = [i for i, c in enumerate(checks) if c["targetTable"] == "reserve.reserve_movement"][0]
    doc = {
        "documentControl": doc_control(fid, approvers=["P048", "P017"], reviewers=["P041", "P022"],
                                       history_authors=["P051"]),
        "wave": {"id": "MW-1", "name": wave["name"], "scope": wave["scope"], "cutOverDate": wave["date"],
                 "freeze": wave["freeze"], "rehearsals": wave["rehearsals"], "status": "complete",
                 "goDecision": "DEC-009 (Wave 1 go/no-go, 2026-09-11)"},
        "method": {
            "approach": "Region-wave migration (ADR-015); rules executed against the Claims Hub PostgreSQL databases after cut-over",
            "rehearsalData": "Masked data for rehearsals (ADR-025); production data only in the cut-over run",
            "tooling": "Data migration reconciliation workspace (IBM Programme Skerry team)",
            "dimensions": DQ_DIMENSIONS,
            "ownership": {"report": pname("P051", on) + " (IBM, Data Migration Lead)",
                          "businessSignOff": pname("P017", on) + ", " + ptitle("P017", on)},
        },
        "summary": {"checksExecuted": len(checks), "pass": status_counts["PASS"], "warn": status_counts["WARN"],
                    "fail": status_counts["FAIL"],
                    "overall": "Accepted with actions" if status_counts["FAIL"] else "Accepted",
                    "openDefectsNote": "Open items are tracked in the CHUB project under the Wave 1 hypercare epic."},
        "checks": checks,
        "notes": [phrases.paragraph(r, "data_quality", 3), phrases.paragraph(r, "governance", 2)],
    }
    F.add("general", "The Wave 1 data quality report covers MW-1 'Wave 1 – UK motor' (scope PRD-MOT-UK), cut over on 2026-09-14 after 3 rehearsals.",
          jloc("wave"), "cutOverDate: 2026-09-14", world_ref="WAVE:MW-1#date")
    F.add("general", "Wave 1 freeze ran from 2026-09-11 18:00 to 2026-09-14 06:00.",
          jloc("wave", "freeze"), "2026-09-11 18:00 to 2026-09-14 06:00", world_ref="WAVE:MW-1#freeze")
    F.add("general", "The Wave 1 DQ report was prepared by Callum Fairbairn, IBM Data Migration Lead.",
          jloc("method", "ownership", "report"), "Callum Fairbairn (IBM, Data Migration Lead)", world_ref="PERSON:P051")
    F.add("scale", f"The Wave 1 DQ report executed {len(checks)} checks ({status_counts['PASS']} pass, {status_counts['WARN']} warn, {status_counts['FAIL']} fail).",
          jloc("summary"), f"checksExecuted: {len(checks)}", world_ref="WAVE:MW-1")
    F.add("general", "Reserve movements migrate from CLR.T_RESERVE_MOVEMENT to reserve.reserve_movement (reserve-engine).",
          jloc("checks", first_rsv), "sourceTable: CLR.T_RESERVE_MOVEMENT", world_ref="TABLE:reserve.reserve_movement")
    return Built(fid, dump(doc), F.items, f"{len(checks)} rows")


# ---------------------------------------------------------------------------------------------
# ST034 NISA-FR1 2026Q3 payload
# ---------------------------------------------------------------------------------------------

def split_total(r, total: int, weights: list[float]) -> list[int]:
    raw = [total * w / sum(weights) for w in weights]
    out = [int(x) for x in raw]
    rem = total - sum(out)
    order = sorted(range(len(raw)), key=lambda i: raw[i] - out[i], reverse=True)
    for i in order[:rem]:
        out[i] += 1
    return out


def fr1_breakdowns(r, total: int) -> dict:
    regions = ["UK", "NO", "SE", "DK"]
    rv = split_total(r, total, [0.74 + r.uniform(-0.02, 0.02), 0.1, 0.09, 0.07])
    lines = ["Motor", "Home", "Commercial Property", "SME Liability"]
    lv = split_total(r, total, [0.55 + r.uniform(-0.03, 0.03), 0.33, 0.07, 0.05])
    tiers = ["Tier-1", "Tier-2", "Tier-3"]
    tv = split_total(r, total, [0.18, 0.64, 0.18 + r.uniform(-0.02, 0.02)])
    src = ["score-based", "handler referral", "indicator review"]
    sv = split_total(r, total, [0.81, 0.12, 0.07])
    return {"byRegion": dict(zip(regions, rv)), "byLine": dict(zip(lines, lv)), "byTier": dict(zip(tiers, tv)),
            "bySource": dict(zip(src, sv))}


FR1_PRODUCTS = ["PRD-MOT-UK", "PRD-HOM-UK", "PRD-COM-UK", "PRD-LIA-UK", "PRD-MOT-NO", "PRD-HOM-NO",
                "PRD-MOT-SE", "PRD-HOM-SE", "PRD-MOT-DK", "PRD-HOM-DK"]
FR1_CHANNELS = ["telephone", "portal", "app", "broker", "telematics", "post"]


def fr1_detail(r, total: int, months: list[str]) -> dict:
    """Extra FR1 breakdowns (synthetic, each sums to the world total)."""
    pv = split_total(r, total, [0.40, 0.25, 0.06, 0.04, 0.06, 0.04, 0.05, 0.04, 0.03, 0.03])
    cts = ["CT-COL", "CT-THF", "CT-WSC", "CT-FIR", "CT-EOW", "CT-STM", "CT-ACD", "CT-VAN", "CT-BIJ", "CT-TPD", "CT-FLD"]
    cv = split_total(r, total, [0.22, 0.16, 0.03, 0.06, 0.13, 0.04, 0.09, 0.05, 0.14, 0.05, 0.03])
    chv = split_total(r, total, [0.47, 0.22, 0.17, 0.09, 0.03, 0.02])
    mv = split_total(r, total, [1 / len(months) + r.uniform(-0.02, 0.02) for _ in months])
    nt = split_total(r, total, [0.62, 0.30, 0.06, 0.02])
    return {
        "byProduct": [{"product": p, "name": W.products[p]["name"], "referrals": v} for p, v in zip(FR1_PRODUCTS, pv)],
        "byClaimType": [{"claimType": c, "name": W.claim_types[c]["name"], "referrals": v} for c, v in zip(cts, cv)],
        "byChannel": dict(zip(FR1_CHANNELS, chv)),
        "byMonth": dict(zip(months, mv)),
        "noticeTiming": dict(zip(["within 5 business days", "6-10 business days", "deferred (BR-FRD-036)",
                                  "pending at period end"], nt)),
    }


FR1_COUNTRY = {"UK": "UK", "NO": "NO", "SE": "SE", "DK": "DK"}


def fr1_weekly(r, total: int, start: str, end: str) -> list[dict]:
    """Weekly referral counts (Monday-based weeks clipped to the period); sums to the world total."""
    import datetime as _dt
    s0, e0 = _dt.date.fromisoformat(start), _dt.date.fromisoformat(end)
    weeks = []
    cur = s0
    while cur <= e0:
        we = min(cur + _dt.timedelta(days=6 - cur.weekday()), e0)
        weeks.append((cur, we))
        cur = we + _dt.timedelta(days=1)
    vals = split_total(r, total, [((b - a).days + 1) * (1 + r.uniform(-0.12, 0.12)) for a, b in weeks])
    return [{"weekStart": a.isoformat(), "weekEnd": b.isoformat(), "referrals": v} for (a, b), v in zip(weeks, vals)]


def fr1_deferral_annex(r, n: int, start: str, end: str) -> list[dict]:
    """Record-level annex of deferred customer notices (synthetic claim refs, rule-consistent dates)."""
    import datetime as _dt
    s0, e0 = _dt.date.fromisoformat(start), _dt.date.fromisoformat(end)
    span = (e0 - s0).days
    used: set = set()
    out = []
    for _ in range(n):
        prod = r.choice(FR1_PRODUCTS)
        country = prod.split("-")[-1]
        ref_date = s0 + _dt.timedelta(days=r.randint(0, span - 5))
        while ref_date.weekday() >= 5:
            ref_date += _dt.timedelta(days=1)
        due = add_business_days(ref_date, 10)
        days = r.randint(12, 58)
        out.append({"claimRef": claim_ref(r, FR1_COUNTRY[country], ref_date.year, used), "product": prod,
                    "tier": r.choice(["Tier-1", "Tier-2", "Tier-2", "Tier-3"]), "referralDate": ref_date.isoformat(),
                    "noticeDueDate": due.isoformat(), "deferralDays": days,
                    "deferredUntil": (due + _dt.timedelta(days=days)).isoformat(),
                    "reason": "SIU certified tipping-off risk"})
    out.sort(key=lambda x: (x["referralDate"], x["claimRef"]))
    return out


def crosstab(rows: dict, cols: dict) -> dict:
    """Integer cross-tab whose row sums equal `rows` and column sums equal `cols` (same grand total)."""
    assert sum(rows.values()) == sum(cols.values())
    keys = list(rows)
    grand = sum(cols.values())
    out: dict = {}
    for rk in keys[:-1]:
        out[rk] = dict(zip(cols, split_total(None, rows[rk], [cols[c] / grand for c in cols])))
    out[keys[-1]] = {c: cols[c] - sum(out[rk][c] for rk in keys[:-1]) for c in cols}
    assert all(v >= 0 for v in out[keys[-1]].values())
    return out


def fr1_definitions(fid: str, on: str) -> list[dict]:
    out = []
    for gid in ("G-002", "G-008", "G-009", "G-021", "G-012"):
        g = W.glossary[gid]
        out.append({"term": g["canonical"], "definition": g["definition"], "source": f"Programme glossary {gid}"})
    for rid in ("BR-FRD-031", "BR-FRD-032", "BR-FRD-033", "BR-FRD-034", "BR-FRD-035"):
        v = W.rule_version(rid, on)
        if v and rule_text_ok(fid, rid, v["version"]):
            out.append({"term": f"{rid} v{v['version']}", "definition": v["text"], "source": v["source"]})
    return out


def build_ST034(out_dir: pathlib.Path) -> Built:
    fid = "ST034"
    on = fdate(fid)
    F = Facts(fid, out_dir)
    r = util.rng(f"{fid}:fr1")
    rep = W.reports["NISA-FR1"]
    sub = rep["submissions"]["2026Q3"]
    total = sub["referrals"]
    need(fid, "TIMELINE:metrics", "fraud_referrals_count")
    need(fid, "REPORT:NISA-FR1", "submissions")
    bd = fr1_breakdowns(r, total)
    notices = total - r.randint(20, 40)
    deferred = total - notices
    doc = {
        "documentControl": doc_control(fid, approvers=["P037"], reviewers=["P008", "P021"]),
        "return": {
            "code": "NISA-FR1", "name": rep["name"], "period": "2026Q3", "periodStart": "2026-07-01", "periodEnd": "2026-09-30",
            "due": sub["due"], "submitted": sub["submitted"], "submissionChannel": "NISA Reporting Hub (SYS10)",
            "sourceInterface": rep["source_interfaces"][0], "sourceProgram": "CLRFR090",
            "legalBasis": "NISA Circular 2026/04 §3.4; BR-FRD-034 v1",
        },
        "firm": {"name": W.company["legal_name"], "nisaFirmReference": W.company["nisa_firm_reference"],
                 "regions": W.company["regions"]},
        "preparer": {"name": pname(rep["preparer"], on), "title": ptitle(rep["preparer"], on)},
        "signatory": {"name": pname("P037", on), "role": rep["signed_by_role"]},
        "figures": {
            "referralsTotal": total,
            "referralThreshold": {"value": 65, "rule": "BR-FRD-031 v1", "appliesTo": "all tiers",
                                  "note": "The Tier-3 threshold of 60 (BR-FRD-031 v2) applies from 2026-10-01 and is outside this period."},
            "breakdowns": bd,
            "customerNotices": {"issuedWithin10BusinessDays": notices, "deferred": deferred, "rule": "BR-FRD-032 v2 / BR-FRD-036 v1"},
            "adverseDecisionsOnScoreAlone": 0,
            "siuTriageRule": "BR-FRD-035 v2 (3 business days)",
        },
        "detail": fr1_detail(r, total, ["2026-07", "2026-08", "2026-09"]),
        "weekly": fr1_weekly(r, total, "2026-07-01", "2026-09-30"),
        "deferralAnnex": {"rule": "BR-FRD-036 v1", "maxDeferralDays": rule_ver("BR-FRD-036", 1)["parameters"]["max_deferral_days"],
                          "records": fr1_deferral_annex(r, deferred, "2026-07-01", "2026-09-30")},
        "definitions": fr1_definitions(fid, "2026-09-30"),
        "lineage": [
            {"step": 1, "what": "Referral records in CLR.T_FRAUD_REFERRAL and fraud.referral (Claims Hub, migrated UK motor)"},
            {"step": 2, "what": "Quarterly extract by CLRFR090 (job CLRQFR01)"},
            {"step": 3, "what": "Delivery to the NISA Reporting Hub over CLX-IF-033"},
            {"step": 4, "what": "Validation and submission by Regulatory Reporting"},
        ],
        "controls": [{"id": f"C{k:02d}", "check": c, "result": "PASS"} for k, c in enumerate([
            "breakdown totals equal referralsTotal", "every referral has a referral date inside the period",
            "no referral without a Sentinel score or handler reason", "notice records exist for every non-deferred referral",
            "deferrals carry an approval record", "CLARA and Claims Hub counts reconciled for migrated claims",
            "schema validation against FR1 v1.0"], 1)],
        "contacts": [{"role": "Preparer", "name": pname(rep["preparer"], on), "email": pemail(rep["preparer"], on)},
                     {"role": "Signatory", "name": pname("P037", on), "email": pemail("P037", on)},
                     {"role": "Counter-Fraud & SIU", "name": pname("P008", on), "email": pemail("P008", on)}],
        "comparatives": {"2026Q2": {"referralsTotal": W.reports["NISA-FR1"]["submissions"]["2026Q2"]["referrals"],
                                    "submitted": W.reports["NISA-FR1"]["submissions"]["2026Q2"]["submitted"]}},
        "declarations": [
            "The figures were extracted from CLARA (CLRFR090) and reconciled to Claims Hub fraud-referral-svc for migrated UK motor claims.",
            "No claim was declined, reduced or repudiated on the basis of an automated score alone (BR-FRD-033).",
            phrases.sentence(r, "governance"),
        ],
    }
    vs = [a for a in W.anchors("VS") if a["file_id"] == "VS042"][0]
    vs_path = f"corpus/upload/visuals/{vs['filename']}"
    F.add("needle", "NISA-FR1 2026Q3 payload: 1,530 fraud referrals in Q3 2026.",
          jloc("figures", "referralsTotal"), "1530", world_ref="TIMELINE:metrics#fraud_referrals_count",
          placement="PL-143", also_in=["ST038-F001", vs_path])
    F.add("general", "NISA-FR1 2026Q3 was due 2026-10-30 and submitted 2026-10-28.",
          jloc("return"), "due: 2026-10-30 submitted: 2026-10-28", world_ref="REPORT:NISA-FR1#submissions")
    F.add("general", "The NISA-FR1 return is signed by the Compliance Manager – Conduct & Counter-Fraud (Ruth Okafor).",
          jloc("signatory"), "name: Ruth Okafor", world_ref="REPORT:NISA-FR1#signed_by_role")
    F.add("temporal", "In Q3 2026 the referral threshold was 65 for all tiers (BR-FRD-031 v1); the Tier-3 threshold of 60 applies from 2026-10-01.",
          jloc("figures", "referralThreshold"), "value: 65 rule: BR-FRD-031 v1", world_ref="RULE:BR-FRD-031@v1")
    F.add("general", "NISA-FR1 source interface is CLX-IF-033 (program CLRFR090).",
          jloc("return", "sourceInterface"), "CLX-IF-033", world_ref="REPORT:NISA-FR1#source_interfaces")
    F.add("general", "Corvane Mutual's NISA firm reference is NISA-FRN 40417.",
          jloc("firm", "nisaFirmReference"), "NISA-FRN 40417", world_ref="ORG:company#nisa_firm_reference")
    F.add("general", "The FR1 Q3 payload restates the Q2 2026 comparative: 1,488 referrals.",
          jloc("comparatives", "2026Q2", "referralsTotal"), "1488", world_ref="TIMELINE:metrics#fraud_referrals_count")
    F.add("general", "FR1 Q3 deferral annex: notices may be deferred up to 60 days under BR-FRD-036 v1.",
          jloc("deferralAnnex", "maxDeferralDays"), "60", world_ref="RULE:BR-FRD-036@v1#parameters.max_deferral_days")
    return Built(fid, dump(doc), F.items, f"{sum(len(v) for v in bd.values())} rows")


BUILDERS = {
    "ST027": build_ST027, "ST028": build_ST028, "ST029": build_ST029, "ST030": build_ST030,
    "ST031": build_ST031, "ST032": build_ST032, "ST033": build_ST033, "ST034": build_ST034,
}

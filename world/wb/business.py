"""process.yaml, vendors.yaml, regulators.yaml, claims_profile.yaml."""
from __future__ import annotations

from .common import rng

# ------------------------------------------------------------------ process
STAGES = [
    ("S1", "FNOL", "First Notice of Loss", [("P029", "2019-01-01"), ("P011", "2025-09-01")], ["SYS12", "SYS04", "SYS13", "SYS01", "SYS02"]),
    ("S2", "TRIAGE", "Triage", [("P011", "2017-01-01")], ["SYS01", "SYS02", "SYS03"]),
    ("S3", "ASSESSMENT", "Assessment", [("P033", "2013-04-08")], ["SYS01", "SYS02", "SYS17"]),
    ("S4", "RESERVING", "Reserving", [("P010", "2014-06-02"), ("P009", "2025-09-01")], ["SYS01", "SYS02", "SYS07"]),
    ("S5", "FRAUD", "Fraud Referral", [("P008", "2020-01-01")], ["SYS03", "SYS01", "SYS02", "SYS22", "SYS25"]),
    ("S6", "SETTLEMENT", "Settlement", [("P011", "2017-01-01")], ["SYS01", "SYS02", "SYS09", "SYS19"]),
    ("S7", "RECOVERY", "Recovery & Subrogation", [("P015", "2016-03-01"), ("P014", "2025-01-01"), ("P013", "2025-09-01")],
     ["SYS01", "SYS24", "SYS02"]),
]


def _sla(value, unit, text):
    return {"value": value, "unit": unit, "text": text}


def _raci(R, A, C=(), I=()):
    return {"R": list(R), "A": A, "C": list(C), "I": list(I)}


STEPS = [
    # id, stage, name, description, next, decision, systems, programs, services, sla, raci, rules
    ("PS-FNOL-01", "S1", "Receive notification", "Notification received by telephone, portal, app, broker or telematics alert.",
     ["PS-FNOL-02"], None, ["SYS12", "SYS04", "SYS13"], ["CLRFN010", "CLRFN040", "CLRFN110", "CLRFN130"], ["fnol-intake-svc"],
     _sla(0, "minutes", "captured during the call or on submission"), _raci(["T10"], "P011", ["T27"], ["T02"]), ["BR-FNOL-002"]),
    ("PS-FNOL-02", "S1", "Validate policy and cover", "Check the policy snapshot from PALM and the cover dates.",
     ["PS-FNOL-03"], None, ["SYS08", "SYS01"], ["CLRFN015"], ["claim-core-svc"], _sla(60, "minutes", "within 1 hour of notification"),
     _raci(["T10"], "P011", [], ["T02"]), []),
    ("PS-FNOL-03", "S1", "Create claim and default reserve", "Create the claim number and the FNOL default reserve.",
     ["PS-FNOL-04"], None, ["SYS01", "SYS02"], ["CLRFN030"], ["fnol-intake-svc", "reserve-engine"], _sla(15, "minutes", "within 15 minutes of notification"),
     _raci(["T10", "T27"], "P011", ["T12"], []), ["BR-FNOL-005"]),
    ("PS-FNOL-04", "S1", "Duplicate and late-notification checks", "Check for duplicates (±3 days) and late notification (> 30 days).",
     ["PS-FNOL-05"], None, ["SYS01", "SYS02"], ["CLRFN060", "CLRFN080"], ["fnol-intake-svc"], _sla(1, "business_days", "same business day"),
     _raci(["T02"], "P011", [], []), ["BR-FNOL-003", "BR-FNOL-004"]),
    ("PS-FNOL-05", "S1", "Acknowledge customer", "Send the acknowledgement via Notify.",
     ["PS-TRI-01"], None, ["SYS25"], ["CLRFN070"], ["notification-svc"], _sla(1, "business_days", "1 business day digital, 2 business days other channels (BR-FNOL-001 v3)"),
     _raci(["T10"], "P011", [], ["T18"]), ["BR-FNOL-001"]),
    ("PS-TRI-01", "S2", "Sentinel pre-screen", "Score the claim with Sentinel.", ["PS-TRI-02"], None, ["SYS03"], ["CLRFR020", "CLRTR040"],
     ["triage-svc"], _sla(15, "minutes", "within 15 minutes of FNOL"), _raci(["T27"], "P008", ["T11"], []), ["BR-TRI-007"]),
    ("PS-TRI-02", "S2", "Tier classification", "Classify the claim as Tier-1, Tier-2 or Tier-3.", ["PS-TRI-03"], None, ["SYS01", "SYS02"],
     ["CLRTR020", "CLRTR030"], ["triage-svc"], _sla(4, "hours", "within 4 hours of FNOL"), _raci(["T02"], "P011", [], ["T09"]), ["BR-TRI-003"]),
    ("PS-TRI-03", "S2", "Route claim", "Route by tier and fraud score.", ["PS-STL-05", "PS-TRI-04", "PS-FRD-01", "PS-ASM-01"],
     {"question": "Which route?", "branches": [
         {"condition": "sentinel_score >= referral threshold (see PS-FRD-01)", "next": "PS-FRD-01", "rule": "BR-FRD-031"},
         {"condition": "tier == 'Tier-1' and sentinel_score < 30 and not bodily_injury", "next": "PS-STL-05", "rule": "BR-TRI-006"},
         {"condition": "tier == 'Tier-3'", "next": "PS-TRI-04", "rule": "BR-TRI-004"},
         {"condition": "otherwise", "next": "PS-ASM-01", "rule": "BR-TRI-004"}]},
     ["SYS01", "SYS02"], ["CLRTR050", "CLRTR060"], ["triage-svc"], _sla(4, "hours", "within 4 hours of FNOL"), _raci(["T02"], "P011", ["T11"], []),
     ["BR-TRI-004", "BR-TRI-006"]),
    ("PS-TRI-04", "S2", "Major loss alert", "Alert Major & Complex Loss for Tier-3 claims.", ["PS-ASM-01"], None, ["SYS01", "SYS02"], ["CLRTR090"],
     ["triage-svc"], _sla(4, "hours", "within 4 hours of tiering"), _raci(["T02"], "P030", [], ["T17"]), ["BR-TRI-004"]),
    ("PS-ASM-01", "S3", "Appoint Claims Assessor", "Appoint an internal or panel Claims Assessor.", ["PS-ASM-02"], None, ["SYS17", "SYS01", "SYS02"],
     ["CLRAS020", "CLRAS030"], ["assessment-svc"], _sla(2, "business_days", "within 2 business days of triage"), _raci(["T06", "T07"], "P033", [], ["T02"]),
     ["BR-ASM-002"]),
    ("PS-ASM-02", "S3", "Inspect or desk-assess", "Site inspection, video or desk assessment.", ["PS-ASM-03"], None, ["SYS17", "SYS13"],
     ["CLRAS050", "CLRAS090"], ["assessment-svc"], _sla(5, "business_days", "5 business days; Tier-3 within 48 hours (BR-ASM-005 v3)"),
     _raci(["T06", "T07"], "P033", [], []), ["BR-ASM-005", "BR-ASM-008", "BR-ASM-012"]),
    ("PS-ASM-03", "S3", "Coverage decision", "Decide cover based on the assessor report.", ["PS-ASM-04"], None, ["SYS01", "SYS02"], ["CLRAS080"],
     ["assessment-svc"], _sla(3, "business_days", "within 3 business days of the assessor report"), _raci(["T02"], "P011", ["T06"], []), ["BR-ASM-011"]),
    ("PS-ASM-04", "S3", "Estimate and recovery potential", "Record the estimate and flag recovery potential.", ["PS-RSV-01", "PS-REC-01"],
     {"question": "Third party at fault?", "branches": [
         {"condition": "third_party_at_fault in ('wholly', 'partly')", "next": "PS-REC-01", "rule": "BR-REC-001"},
         {"condition": "always", "next": "PS-RSV-01", "rule": "BR-RSV-001"}]},
     ["SYS01", "SYS02"], ["CLRAS060", "CLRRC010"], ["assessment-svc"], _sla(2, "business_days", "with the coverage decision"),
     _raci(["T06"], "P033", ["T08"], []), ["BR-REC-001"]),
    ("PS-RSV-01", "S4", "Set initial reserve", "Replace the default reserve with a claim-specific reserve.", ["PS-RSV-02"], None, ["SYS01", "SYS02"],
     ["CLRRS010"], ["reserve-engine"], _sla(2, "business_days", "within 2 business days of FNOL"), _raci(["T02"], "P009", ["T06"], []), ["BR-RSV-001"]),
    ("PS-RSV-02", "S4", "Authority check and approval", "Check reserve authority; escalate above limit.", ["PS-RSV-03", "PS-RSV-04"],
     {"question": "Above authority?", "branches": [
         {"condition": "amount > holder authority (BR-RSV-003 v3)", "next": "PS-RSV-02", "rule": "BR-RSV-003", "note": "escalate to the next level"},
         {"condition": "movement_gbp > 250000", "next": "PS-RSV-04", "rule": "BR-RSV-011"},
         {"condition": "otherwise", "next": "PS-RSV-03", "rule": "BR-RSV-003"}]},
     ["SYS01", "SYS02"], ["CLRRS015", "CLRRS040"], ["reserve-engine"], _sla(1, "business_days", "same business day"),
     _raci(["T02"], "P009", ["T12"], []), ["BR-RSV-003"]),
    ("PS-RSV-03", "S4", "Periodic reserve review", "Review reserves; Tier-3 every 14 days from 2026-07-01.", ["PS-STL-01"], None, ["SYS01", "SYS02"],
     ["CLRRS110", "CLRRS120", "CLRRS130"], ["reserve-engine"], _sla(14, "days", "Tier-3 every 14 days (BR-RSV-007 v3)"),
     _raci(["T02", "T09"], "P009", ["T12"], ["T17"]), ["BR-RSV-007", "BR-RSV-009"]),
    ("PS-RSV-04", "S4", "Large loss notification", "Notify Reinsurance of movements above the LLNT.", ["PS-RSV-03"], None, ["SYS07"], ["CLRRS160"],
     ["reserve-engine"], _sla(24, "hours", "within 24 hours (BR-RSV-011 v2)"), _raci(["T09"], "P038", ["T12"], ["T14"]), ["BR-RSV-011"]),
    ("PS-FRD-01", "S5", "Referral decision", "Decide whether to refer the claim to SIU.", ["PS-FRD-02", "PS-ASM-01"],
     {"question": "Refer to SIU?", "branches": [
         {"condition": "sentinel_score >= 65 or (tier == 'Tier-3' and sentinel_score >= 60)", "next": "PS-FRD-02", "rule": "BR-FRD-031@v2"},
         {"condition": "otherwise", "next": "PS-ASM-01", "rule": "BR-FRD-031@v2"}],
      "condition_history": [
         {"from": "2023-04-01", "to": "2026-03-31", "condition": "sentinel_score >= 70", "rule": "BR-FRD-012@v2"},
         {"from": "2026-04-01", "to": "2026-09-30", "condition": "sentinel_score >= 65", "rule": "BR-FRD-031@v1"},
         {"from": "2026-10-01", "to": None, "condition": "sentinel_score >= 65 or (tier == 'Tier-3' and sentinel_score >= 60)", "rule": "BR-FRD-031@v2"}]},
     ["SYS03", "SYS01", "SYS02"], ["CLRFR030", "CLRFR040"], ["fraud-referral-svc"], _sla(1, "business_days", "same business day as scoring"),
     _raci(["T11"], "P008", ["T02"], ["T18"]), ["BR-FRD-031", "BR-FRD-005"]),
    ("PS-FRD-02", "S5", "Refer to SIU", "Create the referral and the SIU case.", ["PS-FRD-03", "PS-FRD-04"], None, ["SYS22", "SYS01", "SYS02"],
     ["CLRFR030", "CLRFR070"], ["fraud-referral-svc"], _sla(1, "business_days", "same business day"), _raci(["T11"], "P008", [], ["T02"]), ["BR-FRD-031"]),
    ("PS-FRD-03", "S5", "Notify customer of referral", "Send the referral notice or record a deferral.", ["PS-FRD-04"],
     {"question": "Tipping-off risk certified?", "branches": [
         {"condition": "tipping_off_risk_certified", "next": "PS-FRD-04", "rule": "BR-FRD-036", "note": "defer up to 60 days; > 30 days needs Head of Counter-Fraud & SIU"},
         {"condition": "otherwise", "next": "PS-FRD-04", "rule": "BR-FRD-032", "note": "notice within 10 business days"}]},
     ["SYS25", "SYS01", "SYS02"], ["CLRFR060", "CLRFR120"], ["fraud-referral-svc", "notification-svc"],
     _sla(10, "business_days", "within 10 business days of referral (BR-FRD-032 v2)"), _raci(["T02", "T11"], "P008", ["T18"], []), ["BR-FRD-032", "BR-FRD-036"]),
    ("PS-FRD-04", "S5", "SIU investigation and outcome", "Triage and investigate; record NF, CF or WD.", ["PS-FRD-05", "PS-STL-01"], None, ["SYS22"],
     ["CLRFR050"], ["fraud-referral-svc"], _sla(3, "business_days", "SIU triage within 3 business days (BR-FRD-035 v2)"),
     _raci(["T11"], "P028", ["T18"], ["T02"]), ["BR-FRD-035"]),
    ("PS-FRD-05", "S5", "Human review of adverse outcome", "Documented human review before any decline (no auto-decline).", ["PS-STL-01"], None, ["SYS22"],
     [], ["fraud-referral-svc"], _sla(5, "business_days", "within 5 business days of SIU outcome"), _raci(["T11"], "P008", ["T18"], ["T02"]), ["BR-FRD-033"]),
    ("PS-STL-01", "S6", "Settlement offer", "Make the settlement offer.", ["PS-STL-02"], None, ["SYS01", "SYS02"], ["CLRST010"], ["settlement-svc"],
     _sla(5, "business_days", "within 5 business days of the coverage decision"), _raci(["T02"], "P011", [], []), ["BR-STL-004"]),
    ("PS-STL-02", "S6", "Payment authorisation", "Authorise the payment within authority.", ["PS-STL-03"], None, ["SYS01", "SYS02"], ["CLRST020"],
     ["payment-orchestrator"], _sla(1, "business_days", "same business day"), _raci(["T02"], "P011", ["T16"], []), ["BR-STL-002"]),
    ("PS-STL-03", "S6", "Sanctions screening and payment", "Screen the payee and send the payment.", ["PS-STL-04"], None, ["SYS19", "SYS09"],
     ["CLRST070", "CLRST030", "CLRST140"], ["payment-orchestrator"], _sla(1, "business_days", "next payment run (Mon-Fri 16:30)"),
     _raci(["T16"], "P035", ["T18"], ["T14"]), ["BR-STL-007", "BR-STL-014"]),
    ("PS-STL-04", "S6", "Close claim and zero reserve", "Final settlement closes the claim and zeroes the reserve.", ["PS-REC-01"], None, ["SYS01", "SYS02"],
     ["CLRST040"], ["settlement-svc", "reserve-engine"], _sla(1, "business_days", "within 1 business day of final payment"),
     _raci(["T02"], "P011", ["T12"], []), ["BR-RSV-014"]),
    ("PS-STL-05", "S6", "Fast-track straight-through settlement", "Straight-through payment for eligible Tier-1 claims.", ["PS-STL-04"], None,
     ["SYS01", "SYS02", "SYS09"], ["CLRST080"], ["settlement-svc"], _sla(1, "business_days", "next business day"), _raci(["T02"], "P011", [], ["T11"]),
     ["BR-TRI-006", "BR-STL-009"]),
    ("PS-REC-01", "S7", "Identify recovery potential", "Confirm third-party fault and recoverable outlay.", ["PS-REC-02", "PS-REC-04"], None,
     ["SYS01", "SYS24", "SYS02"], ["CLRRC010"], ["recovery-svc"], _sla(10, "business_days", "within 10 business days of the flag"),
     _raci(["T08"], "P013", ["T06"], []), ["BR-REC-001"]),
    ("PS-REC-02", "S7", "Open subrogation case and demand", "Open the case and send the demand.", ["PS-REC-03", "PS-REC-05"],
     {"question": "Pursue?", "branches": [
         {"condition": "recoverable_gbp >= 1000", "next": "PS-REC-05", "rule": "BR-REC-003@v3"},
         {"condition": "recoverable_gbp >= 25000 or liability_defended", "next": "PS-REC-03", "rule": "BR-REC-005@v2"},
         {"condition": "recoverable_gbp < 1000", "next": "PS-REC-06", "rule": "BR-REC-003@v3", "note": "not pursued; close or write off"}]},
     ["SYS24", "SYS01", "SYS02"], ["CLRRC020", "CLRRC030"], ["recovery-svc"], _sla(10, "business_days", "demand within 10 business days"),
     _raci(["T08"], "P013", [], ["T14"]), ["BR-REC-003", "BR-REC-009"]),
    ("PS-REC-03", "S7", "Solicitor referral", "Instruct Quarryhill Solicitors.", ["PS-REC-05"], None, ["SYS05"], ["CLRRC060"], ["recovery-svc"],
     _sla(5, "business_days", "within 5 business days of the decision"), _raci(["T08"], "P013", ["T18"], []), ["BR-REC-005"]),
    ("PS-REC-04", "S7", "Salvage disposal", "Release total-loss vehicles to Salvanta.", ["PS-REC-05"], None, ["SYS01"], ["CLRRC070"], ["recovery-svc"],
     _sla(5, "business_days", "within 5 business days of total-loss decision"), _raci(["T08"], "P013", [], []), ["BR-REC-007"]),
    ("PS-REC-05", "S7", "Recovery receipt and reserve adjustment", "Post the receipt and adjust the reserve.", ["PS-REC-06"], None, ["SYS24", "SYS01", "SYS02"],
     ["CLRRC050"], ["recovery-svc"], _sla(2, "business_days", "within 2 business days of receipt"), _raci(["T08"], "P013", ["T14"], ["T12"]), []),
    ("PS-REC-06", "S7", "Write-off approval", "Approve write-off of unrecoverable amounts.", [],
     {"question": "Write-off above £10,000?", "branches": [
         {"condition": "write_off_gbp > 10000", "next": None, "rule": "BR-REC-011@v2", "note": "approval by the Head of Recoveries & Subrogation"},
         {"condition": "otherwise", "next": None, "rule": "BR-REC-011@v2", "note": "Recoveries Team Leader approves"}]},
     ["SYS24", "SYS02"], ["CLRRC090"], ["recovery-svc"], _sla(5, "business_days", "within 5 business days"), _raci(["T08"], "P013", ["T14"], []),
     ["BR-REC-011"]),
]


def build_process():
    stages = []
    for i, (sid, code, name, owners, systems) in enumerate(STAGES, 1):
        oh = []
        for j, (p, frm) in enumerate(owners):
            from .common import day_before
            to = day_before(owners[j + 1][1]) if j + 1 < len(owners) else None
            oh.append({"person": p, "from": frm, "to": to})
        stages.append({"id": sid, "code": code, "name": name, "order": i, "owner_history": oh, "owner": oh[-1]["person"],
                       "systems": systems, "steps": [s[0] for s in STEPS if s[1] == sid]})
    steps = []
    for order, (pid, sid, name, desc, nxt, dec, systems, progs, svcs, sla, raci, rules) in enumerate(STEPS, 1):
        steps.append({"id": pid, "stage": sid, "name": name, "order": order, "description": desc, "next": nxt, "decision": dec,
                      "systems": systems, "programs": progs, "services": svcs, "sla": sla, "raci": raci, "raci_as_of": "2026-11-15",
                      "rules": rules})
    notes = {
        "subrogation_owner_trap": "The recovery & subrogation stage (S7) owner was Martin Calloway (P015) until 2024-12-31, "
                                  "Siobhan Quill (P014, acting) 2025-01-01..2025-08-31, and Freya Lindahl (P013) from 2025-09-01. "
                                  "The 2024 org chart (VS004) still shows Martin Calloway.",
        "raci_2024_recovery": {"as_of": "2024-03-01", "A": "P015", "R": ["T08"]},
    }
    return {"stages": stages, "steps": steps, "notes": notes}


# ------------------------------------------------------------------ vendors
VENDORS = [
    {"id": "VEN-01", "name": "Brackenfield Loss Adjusting Ltd", "short": "Brackenfield", "code": "BRACKFLD", "type": "loss_adjuster",
     "country": "UK", "location": "Manchester", "domain": "brackenfield-la.example", "contact": "P057", "panel_from": "2017-04-01", "panel_to": None,
     "role": "External Claims Assessors (loss adjusters) for UK property and motor",
     "fees": {"desk_assessment_gbp": 185, "site_visit_gbp": 420, "major_loss_hourly_gbp": 145},
     "sla": {"desk_assessment_business_days": 2, "site_visit_business_days": 5, "report_business_days": 5}},
    {"id": "VEN-02", "name": "Norrvik Skadetaxering AB", "short": "Norrvik", "code": "NORRVIK", "type": "loss_adjuster",
     "country": "SE", "location": "Gothenburg", "domain": "norrvik.example", "contact": "P058", "panel_from": "2018-09-01", "panel_to": None,
     "role": "External Claims Assessors for Sweden and Norway",
     "fees": {"desk_assessment_sek": 2150, "site_visit_sek": 4900, "site_visit_nok": 5200},
     "sla": {"site_visit_business_days": 5}},
    {"id": "VEN-03", "name": "Fellgate Adjusting Partners LLP", "short": "Fellgate", "code": "FELLGATE", "type": "loss_adjuster",
     "country": "UK", "location": "London", "domain": "fellgate.example", "contact": None, "panel_from": "2019-07-01", "panel_to": "2026-01-31",
     "role": "Major-loss adjusters (removed from the panel on 2026-01-31; open instructions transferred to Brackenfield)",
     "fees": {"major_loss_hourly_gbp": 165}, "sla": {}},
    {"id": "VEN-04", "name": "Thistlecombe Repair Network Ltd", "short": "Thistlecombe", "code": "THISTLCB", "type": "repair_network",
     "country": "UK", "location": "Coventry", "domain": "thistlecombe.example", "contact": None, "panel_from": "2015-01-01", "panel_to": None,
     "role": "UK motor repair network (212 approved bodyshops) and UK windscreen", "fees": {}, "sla": {"repair_start_business_days": 3}},
    {"id": "VEN-05", "name": "Vardholm Bilverksted AS", "short": "Vardholm", "code": "VARDHOLM", "type": "repair_network",
     "country": "NO", "location": "Drammen", "domain": "vardholm.example", "contact": None, "panel_from": "2016-05-01", "panel_to": None,
     "role": "Norwegian motor repair network (23 workshops)", "fees": {}, "sla": {}},
    {"id": "VEN-06", "name": "Kilnmoor Property Repairs Ltd", "short": "Kilnmoor", "code": "KILNMOOR", "type": "repair_network",
     "country": "UK", "location": "Sheffield", "domain": "kilnmoor.example", "contact": None, "panel_from": "2018-02-01", "panel_to": None,
     "role": "UK home repair network (drying, plastering, joinery)", "fees": {}, "sla": {"first_visit_business_days": 2}},
    {"id": "VEN-07", "name": "Quarryhill Solicitors LLP", "short": "Quarryhill", "code": "QUARRYHL", "type": "solicitor",
     "country": "UK", "location": "Birmingham", "domain": "quarryhill.example", "contact": "P060", "panel_from": "2014-06-01", "panel_to": None,
     "role": "Subrogation and recovery litigation", "fees": {"fixed_fee_demand_gbp": 95, "success_fee_pct": 12}, "sla": {}},
    {"id": "VEN-08", "name": "Ravensworth Pike LLP", "short": "Ravensworth Pike", "code": "RAVPIKE", "type": "solicitor",
     "country": "UK", "location": "Leeds", "domain": "ravensworthpike.example", "contact": None, "panel_from": "2012-01-01", "panel_to": None,
     "role": "Defence solicitors for liability and bodily-injury claims", "fees": {}, "sla": {}},
    {"id": "VEN-09", "name": "Salvanta Salvage Ltd", "short": "Salvanta", "code": "SALVANTA", "type": "salvage",
     "country": "UK", "location": "Peterborough", "domain": "salvanta.example", "contact": None, "panel_from": "2017-10-01", "panel_to": None,
     "role": "Vehicle salvage for the UK and the Nordics", "fees": {"collection_gbp": 60}, "sla": {"collection_business_days": 2}},
    {"id": "VEN-10", "name": "Greyfold Investigations Ltd", "short": "Greyfold", "code": "GREYFOLD", "type": "siu_partner",
     "country": "UK", "location": "Leeds", "domain": "greyfold.example", "contact": "P059", "panel_from": "2018-03-05", "panel_to": None,
     "role": "SIU partner: surveillance, interviews, open-source checks", "fees": {"surveillance_day_gbp": 640}, "sla": {}},
    {"id": "VEN-11", "name": "Northmere Clearing Bank plc", "short": "Northmere", "code": "NORTHMRE", "type": "bank",
     "country": "UK", "location": "London", "domain": "northmere.example", "contact": None, "panel_from": "2016-01-01", "panel_to": None,
     "role": "Clearing bank behind Corvane Payments Gateway", "fees": {}, "sla": {"payment_cutoff": "17:00 UK"}},
    {"id": "VEN-12", "name": "Brynholt Re SE", "short": "Brynholt Re", "code": "BRYNHOLT", "type": "reinsurer",
     "country": "DK", "location": "Copenhagen", "domain": "brynholt-re.example", "contact": None, "panel_from": "2020-01-01", "panel_to": None,
     "role": "Lead reinsurer, 40% share of the 2026 property-catastrophe and per-risk XoL programme", "fees": {}, "sla": {}},
    {"id": "VEN-13", "name": "Calderbank Re Ltd", "short": "Calderbank Re", "code": "CALDRBNK", "type": "reinsurer",
     "country": "UK", "location": "London", "domain": "calderbank-re.example", "contact": None, "panel_from": "2022-01-01", "panel_to": None,
     "role": "Reinsurer, 35% share of the 2026 XoL programme", "fees": {}, "sla": {}},
    {"id": "VEN-14", "name": "Lyngholm Glass A/S", "short": "Lyngholm", "code": "LYNGHOLM", "type": "repair_network",
     "country": "DK", "location": "Aarhus", "domain": "lyngholm.example", "contact": None, "panel_from": "2019-03-01", "panel_to": None,
     "role": "Danish windscreen network", "fees": {}, "sla": {}},
    {"id": "VEN-15", "name": "Kestwick Analytics Ltd", "short": "Kestwick", "code": "KESTWICK", "type": "software",
     "country": "UK", "location": "Cambridge", "domain": "kestwick.example", "contact": None, "panel_from": "2016-09-01", "panel_to": None,
     "role": "Licensor of the Sentinel (formerly FRAUDNET) scoring engine", "fees": {}, "sla": {}},
]


def build_vendors():
    return VENDORS


# ------------------------------------------------------------------ regulators
def build_regulators():
    regs = [{"id": "REG-NISA", "name": "National Insurance Supervisory Authority", "short": "NISA", "aliases": ["NISA", "the Authority", "the regulator"],
             "jurisdiction": "UK and the Nordic branches of UK-headquartered insurers (fictional single supervisor)",
             "location": "EXT-NISA-LON", "contacts": ["P055", "P056"], "domain": "nisa.example"}]
    circulars = [
        {"id": "CIRC-2024-07", "ref": "NISA Circular 2024/07", "title": "Claims Handling Timeliness", "published": "2024-06-28",
         "effective": "2024-10-01", "author": "P055",
         "requirements": [{"para": "2.1", "text": "Acknowledge every first notice of loss within 2 business days."},
                          {"para": "2.4", "text": "Submit the annual NISA-CT1 claims timeliness return by 31 March each year."}],
         "rules_affected": ["BR-FNOL-001"], "file": "LD023"},
        {"id": "CIRC-2025-02", "ref": "NISA Circular 2025/02", "title": "Operational Resilience for Claims Payment", "published": "2025-02-14",
         "effective": "2025-07-01", "author": "P055",
         "requirements": [{"para": "3.1", "text": "Set an impact tolerance of 48 hours for disruption to claims payments."},
                          {"para": "3.5", "text": "Submit an annual operational resilience self-assessment."}],
         "rules_affected": [], "file": None},
        {"id": "CIRC-2025-11", "ref": "NISA Circular 2025/11", "title": "Claims Data Retention and Minimisation", "published": "2025-09-30",
         "effective": "2026-01-01", "author": "P055",
         "requirements": [{"para": "2", "text": "Retain claim records for 7 years after closure; bodily-injury claims for 15 years."},
                          {"para": "4", "text": "Do not use production personal data in test environments."}],
         "rules_affected": ["BR-GEN-004", "BR-GEN-006"], "file": None},
        {"id": "CIRC-2026-04", "ref": "NISA Circular 2026/04", "title": "Fair Treatment in Fraud Referral", "published": "2025-11-20",
         "effective": "2026-04-01", "author": "P056",
         "requirements": [
             {"para": "3.1", "text": "No claim may be declined, reduced or repudiated on the basis of an automated score alone; a documented human review is required."},
             {"para": "3.2", "text": "Tell the customer in writing within 10 business days of referral that the claim is subject to additional checks; "
                                     "the notice may be deferred for up to 60 days where a tipping-off risk is certified."},
             {"para": "3.3", "text": "Score-based referral cut-offs must be calibrated and documented; on a 0–100 scale the cut-off must not exceed 65."},
             {"para": "3.4", "text": "Submit the quarterly NISA-FR1 fraud referral return within 30 days after each quarter end."},
             {"para": "3.5", "text": "Retain referral records for 7 years."}],
         "clarifications": [{"date": "2026-01-14", "by": "P056", "text": "An SMS counts as written notice under §3.2 if it is followed by a letter within 2 business days.",
                             "channel": "call with Corvane Compliance (Ruth Okafor)"}],
         "rules_affected": ["BR-FRD-012", "BR-FRD-019", "BR-FRD-031", "BR-FRD-032", "BR-FRD-033", "BR-FRD-034", "BR-FRD-036"], "file": "LD022"},
    ]
    reports = [
        {"id": "NISA-TP2", "name": "Quarterly Technical Provisions Return", "frequency": "quarterly", "due": "35 calendar days after quarter end",
         "signed_by_role": "Chief Financial Officer", "preparer": "P020", "source_interfaces": ["CLX-IF-051"], "system": "SYS10",
         "late_events": [{"period": "2025Q1", "due": "2025-05-05", "submitted": "2025-05-07", "incident": "INC-2025-0412",
                          "note": "2-day extension granted by Imogen Thackray (NISA)"}]},
        {"id": "NISA-FR1", "name": "Quarterly Fraud Referral Return", "frequency": "quarterly", "due": "30 calendar days after quarter end",
         "signed_by_role": "Compliance Manager – Conduct & Counter-Fraud", "preparer": "P020", "source_interfaces": ["CLX-IF-033"], "system": "SYS10",
         "first_period": "2026Q2", "first_due": "2026-07-30", "late_events": [],
         "submissions": {"2026Q2": {"due": "2026-07-30", "submitted": "2026-07-29", "referrals": 1488},
                         "2026Q3": {"due": "2026-10-30", "submitted": "2026-10-28", "referrals": 1530}}},
        {"id": "NISA-CT1", "name": "Annual Claims Timeliness Return", "frequency": "annual", "due": "31 March",
         "signed_by_role": "Claims Director", "preparer": "P020", "source_interfaces": ["CLX-IF-032", "CLX-IF-052"], "system": "SYS10", "late_events": []},
        {"id": "NISA-AFR", "name": "Annual Claims & Reserving Filing", "frequency": "annual", "due": "31 March",
         "signed_by_role": "Chief Financial Officer", "preparer": "P020", "source_interfaces": [], "system": "SYS10",
         "filings": [{"year": 2025, "filed": "2026-03-31", "file": "LD003"}], "late_events": []},
    ]
    return {"regulators": regs, "circulars": circulars, "reports": reports}


# ------------------------------------------------------------------ claims profile
def build_claims_profile():
    fx = {}
    base = {"NOK": 0.0738, "SEK": 0.0721, "DKK": 0.1149}
    quarters = []
    for y in (2024, 2025, 2026):
        for q, md in ((1, "03-31"), (2, "06-30"), (3, "09-30"), (4, "12-31")):
            if y == 2026 and q == 4:
                continue
            quarters.append(f"{y}-{md}")
    r = rng("world:fx")
    for qd in quarters:
        fx[qd] = {c: round(v * (1 + r.uniform(-0.035, 0.035)), 4) for c, v in base.items()}
    fx["2026-09-30"] = {"NOK": 0.0731, "SEK": 0.0712, "DKK": 0.1158}
    return {
        "rows": 15000,
        "date_range": {"loss_date_from": "2024-01-01", "loss_date_to": "2026-10-31"},
        "claim_id_format": "CLM-<region>-<yyyy>-<6 digits>, e.g. CLM-UK-2025-118204 (CLARA CLAIM_ID UK2025118204)",
        "columns": ["claim_id", "legacy_claim_id", "product_code", "claim_type", "region", "sub_region", "channel", "loss_date", "notified_date",
                    "status", "tier", "currency", "reserve_outstanding", "paid_to_date", "incurred", "incurred_gbp", "sentinel_score",
                    "fraud_referred", "referral_rule", "assessor_type", "assessor_ref", "handler_ref", "recovery_flag", "closed_date"],
        "products": {"PRD-MOT-UK": 0.34, "PRD-HOM-UK": 0.24, "PRD-COM-UK": 0.06, "PRD-LIA-UK": 0.04, "PRD-MOT-NO": 0.09,
                     "PRD-HOM-NO": 0.06, "PRD-MOT-SE": 0.05, "PRD-HOM-SE": 0.05, "PRD-MOT-DK": 0.03, "PRD-HOM-DK": 0.04},
        "claim_type_weights": {
            "Motor": {"CT-COL": 0.52, "CT-WSC": 0.20, "CT-THF": 0.09, "CT-VAN": 0.06, "CT-TPD": 0.07, "CT-BIJ": 0.05, "CT-FIR": 0.01},
            "Home": {"CT-EOW": 0.31, "CT-STM": 0.17, "CT-ACD": 0.18, "CT-THF": 0.11, "CT-FLD": 0.05, "CT-FIR": 0.04, "CT-VAN": 0.04,
                     "CT-SUB": 0.03, "CT-FRO": 0.04, "CT-SNO": 0.03},
            "Commercial Property": {"CT-FIR": 0.22, "CT-EOW": 0.28, "CT-STM": 0.2, "CT-FLD": 0.1, "CT-VAN": 0.08, "CT-BIN": 0.12},
            "SME Liability": {"CT-PLB": 0.55, "CT-BIJ": 0.30, "CT-TPD": 0.15},
            "notes": "UK-only types (CT-SUB) never appear on Nordic products; Nordic-only types (CT-FRO, CT-SNO) never appear on UK products; "
                     "renormalise weights over the product's claim_types list in products.yaml."},
        "sub_regions": {"UK": ["London", "South East", "South West", "Midlands", "North West", "Yorkshire", "Scotland", "Wales"],
                        "NO": ["Oslo", "Vestland", "Trøndelag", "Viken"], "SE": ["Stockholm", "Västra Götaland", "Skåne"],
                        "DK": ["Hovedstaden", "Midtjylland", "Syddanmark"]},
        "channels": {"PH": 0.52, "WB": 0.31, "BR": 0.09, "AP": 0.06, "TL": 0.02},
        "status_mix": {"OP": 0.18, "CS": 0.64, "CN": 0.11, "RO": 0.02, "RC": 0.05},
        "status_notes": "Claims with loss_date after 2026-08-01 are mostly OP; closed claims have closed_date after notified_date.",
        "incurred_gbp_ranges": {
            "CT-COL": {"median": 2900, "p95": 14000, "min": 150, "max": 85000},
            "CT-WSC": {"median": 380, "p95": 950, "min": 60, "max": 2400},
            "CT-THF": {"median": 5200, "p95": 24000, "min": 200, "max": 90000},
            "CT-VAN": {"median": 1100, "p95": 5200, "min": 80, "max": 22000},
            "CT-TPD": {"median": 3400, "p95": 16000, "min": 200, "max": 120000},
            "CT-BIJ": {"median": 14500, "p95": 160000, "min": 1500, "max": 1850000},
            "CT-FIR": {"median": 16000, "p95": 210000, "min": 500, "max": 2400000},
            "CT-EOW": {"median": 4300, "p95": 21000, "min": 250, "max": 160000},
            "CT-STM": {"median": 3000, "p95": 15000, "min": 150, "max": 140000},
            "CT-FLD": {"median": 21000, "p95": 92000, "min": 900, "max": 420000},
            "CT-SUB": {"median": 18500, "p95": 70000, "min": 2000, "max": 210000},
            "CT-ACD": {"median": 900, "p95": 4200, "min": 60, "max": 26000},
            "CT-FRO": {"median": 5600, "p95": 26000, "min": 300, "max": 120000},
            "CT-SNO": {"median": 7800, "p95": 41000, "min": 500, "max": 260000},
            "CT-BIN": {"median": 38000, "p95": 310000, "min": 2500, "max": 1600000},
            "CT-PLB": {"median": 6200, "p95": 48000, "min": 300, "max": 950000},
        },
        "reserve_share_of_incurred": {"OP": [0.55, 1.0], "RO": [0.3, 0.8], "RC": [0.0, 0.1], "CS": [0.0, 0.0], "CN": [0.0, 0.0]},
        "seasonality": {"CT-FRO": "peaks January-February (Nordics)", "CT-SNO": "peaks January-March (Nordics)",
                        "CT-STM": "peaks November-February", "CT-EOW": "peaks December-February"},
        "currency_by_region": {"UK": "GBP", "NO": "NOK", "SE": "SEK", "DK": "DKK"},
        "fx_to_gbp_quarter_end": fx,
        "fx_note": "Convert local-currency amounts with the quarter-end rate of the loss quarter; 2026-09-30 rates are pinned "
                   "(NOK 0.0731, SEK 0.0712, DKK 0.1158) and also used in the hidden 'calc' sheet of ST004.",
        "tier_rule": "Apply BR-TRI-003 at loss_date (v2 before 2025-01-01: £40,000; v3 from 2025-01-01: £50,000; any CT-BIJ claim is Tier-3).",
        "sentinel_score": {"distribution": "beta(a=2.2, b=6.5) scaled to 0-100, rounded", "linked_claim_uplift": 10},
        "referral_rule_by_date": [
            {"from": "2024-01-01", "to": "2026-03-31", "rule": "BR-FRD-012@v2", "condition": "score >= 70"},
            {"from": "2026-04-01", "to": "2026-09-30", "rule": "BR-FRD-031@v1", "condition": "score >= 65"},
            {"from": "2026-10-01", "to": "2026-10-31", "rule": "BR-FRD-031@v2", "condition": "score >= 65 or (tier == 3 and score >= 60)"}],
        "assessor_assignment": {
            "internal_share_by_line": {"Motor": 0.70, "Home": 0.45, "Commercial Property": 0.20, "SME Liability": 0.60},
            "internal_refs": {"UK": ["MSALE01", "ASR-UK-01", "ASR-UK-02", "ASR-UK-03", "ASR-UK-04", "ASR-UK-05", "ASR-UK-06"],
                              "NO": ["KERIK01", "ASR-NO-01", "ASR-NO-02"], "SE": ["ASR-SE-01", "ASR-SE-02"], "DK": ["ASR-DK-01", "ASR-DK-02"]},
            "internal_ref_note": "MSALE01 = Mohammed Saleem (P045), KERIK01 = Karl Eriksen (P046); ASR-* are pseudonymous internal Claims Assessor ids.",
            "vendor_by_region": {"UK": {"VEN-01": 0.85, "VEN-03": 0.15}, "NO": {"VEN-02": 1.0}, "SE": {"VEN-02": 1.0}, "DK": {"VEN-02": 1.0}},
            "vendor_rules": "VEN-03 (Fellgate) is used only for UK Tier-3 claims notified before 2026-02-01 (removed from the panel 2026-01-31).",
            "assessor_type_values": ["internal", "vendor", "desk"]},
        "handler_ref_format": "H-<4 digits> (pseudonymous; never a real or world person name)",
        "recovery_flag_share": {"Motor": 0.22, "Home": 0.05, "Commercial Property": 0.08, "SME Liability": 0.03},
        "aggregates_policy": "The structured generator computes all aggregates (counts, sums by product/claim type/region/tier) from the "
                             "generated rows and records them in its manifest as aggregate_source facts.",
    }

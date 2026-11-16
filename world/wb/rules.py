"""products.yaml, claim_types.yaml and rules.yaml."""
from __future__ import annotations

from .common import day_before, rng

# ------------------------------------------------------------------ claim types
CLAIM_TYPES = [
    # id, name, code, NO, SE, DK, lines
    ("CT-COL", "Collision", "COL", "Kollisjon", "Kollision", "Kollision", ["Motor"]),
    ("CT-THF", "Theft", "THF", "Tyveri", "Stöld", "Tyveri", ["Motor", "Home"]),
    ("CT-WSC", "Windscreen", "WSC", "Glasskade", "Glasskada", "Glasskade", ["Motor"]),
    ("CT-FIR", "Fire", "FIR", "Brann", "Brand", "Brand", ["Motor", "Home", "Commercial Property"]),
    ("CT-EOW", "Escape of Water", "EOW", "Vannskade", "Vattenskada", "Vandskade", ["Home", "Commercial Property"]),
    ("CT-STM", "Storm", "STM", "Stormskade", "Stormskada", "Stormskade", ["Home", "Commercial Property"]),
    ("CT-FLD", "Flood", "FLD", "Flomskade", "Översvämning", "Oversvømmelse", ["Home", "Commercial Property"]),
    ("CT-SUB", "Subsidence", "SUB", None, None, None, ["Home"]),
    ("CT-ACD", "Accidental Damage", "ACD", "Uhellsskade", "Allrisk", "Pludselig skade", ["Home"]),
    ("CT-VAN", "Vandalism / Malicious Damage", "VAN", "Hærverk", "Skadegörelse", "Hærværk", ["Motor", "Home", "Commercial Property"]),
    ("CT-BIJ", "Bodily Injury", "BIJ", "Personskade", "Personskada", "Personskade", ["Motor", "SME Liability"]),
    ("CT-TPD", "Third-Party Property Damage", "TPD", "Tingskade tredjepart", "Sakskada tredje man", "Tingskade tredjemand", ["Motor", "SME Liability"]),
    ("CT-BIN", "Business Interruption", "BIN", None, None, None, ["Commercial Property"]),
    ("CT-PLB", "Public Liability", "PLB", None, None, None, ["SME Liability"]),
    ("CT-FRO", "Frost Damage", "FRO", "Frostskade", "Frostskada", "Frostskade", ["Home"]),
    ("CT-SNO", "Snow Load", "SNO", "Snølast", "Snölast", "Snelast", ["Home"]),
]


def build_claim_types():
    out = []
    for cid, name, code, no, se, dk, lines in CLAIM_TYPES:
        out.append({"id": cid, "name": name, "peril_code": code, "aliases": [name.lower(), code],
                    "local_names": {k: v for k, v in (("NO", no), ("SE", se), ("DK", dk)) if v},
                    "lines_of_business": lines, "nordic_only": cid in ("CT-FRO", "CT-SNO"), "uk_only": cid in ("CT-SUB", "CT-BIN", "CT-PLB")})
    return out


# ------------------------------------------------------------------ products
PRODUCTS = [
    {"id": "PRD-MOT-UK", "name": "Motor Private UK", "code": "MOTUK", "line": "Motor", "region": "UK", "currency": "GBP",
     "claim_types": ["CT-COL", "CT-THF", "CT-WSC", "CT-FIR", "CT-VAN", "CT-BIJ", "CT-TPD"],
     "excess": {"standard": 250, "windscreen": 95}, "local_excess_term": "excess",
     "wordings": [{"version": "MOT-UK-2012", "year": 2012, "file": "LD004", "excess": {"standard": 150, "windscreen": 75},
                   "notification_condition": "notify us as soon as possible and in any event within 30 days",
                   "acknowledgement_promise": "we will acknowledge your claim within 5 working days"}],
     "policies_in_force": 612000},
    {"id": "PRD-HOM-UK", "name": "Home Buildings & Contents UK", "code": "HOMUK", "line": "Home", "region": "UK", "currency": "GBP",
     "claim_types": ["CT-THF", "CT-FIR", "CT-EOW", "CT-STM", "CT-FLD", "CT-SUB", "CT-ACD", "CT-VAN"],
     "excess": {"standard": 250, "escape_of_water": 400, "subsidence": 1000}, "local_excess_term": "excess",
     "wordings": [{"version": "HOM-UK-2014", "year": 2014, "file": "LD005", "excess": {"standard": 200, "escape_of_water": 350, "subsidence": 1000},
                   "notification_condition": "tell us within 30 days of discovering the damage"}],
     "policies_in_force": 448000},
    {"id": "PRD-COM-UK", "name": "Commercial Property UK", "code": "COMUK", "line": "Commercial Property", "region": "UK", "currency": "GBP",
     "claim_types": ["CT-FIR", "CT-EOW", "CT-STM", "CT-FLD", "CT-VAN", "CT-BIN"],
     "excess": {"standard": 1000}, "bi_indemnity_period_months": {"standard": 12, "optional": 24}, "local_excess_term": "excess",
     "wordings": [{"version": "COM-UK-2011", "year": 2011, "file": "LD006", "excess": {"standard": 750}, "bi_indemnity_period_months": 12,
                   "notification_condition": "notify the Insurer within 14 days"}],
     "policies_in_force": 38500},
    {"id": "PRD-LIA-UK", "name": "SME Liability UK", "code": "LIAUK", "line": "SME Liability", "region": "UK", "currency": "GBP",
     "claim_types": ["CT-BIJ", "CT-TPD", "CT-PLB"],
     "excess": {"property_damage": 500}, "limits": {"public_liability": 5000000, "employers_liability": 10000000}, "local_excess_term": "excess",
     "wordings": [{"version": "LIA-UK-2013", "year": 2013, "file": "LD007", "excess": {"property_damage": 250},
                   "limits": {"public_liability": 2000000, "employers_liability": 10000000},
                   "notification_condition": "notify the Insurer immediately of any claim or circumstance"}],
     "policies_in_force": 52300},
    {"id": "PRD-MOT-NO", "name": "Motor Privat Norge", "code": "MOTNO", "line": "Motor", "region": "NO", "currency": "NOK",
     "claim_types": ["CT-COL", "CT-THF", "CT-WSC", "CT-FIR", "CT-VAN", "CT-BIJ", "CT-TPD"],
     "excess": {"standard": 6000, "windscreen": 2000}, "local_excess_term": "egenandel",
     "wordings": [{"version": "MOT-NO-2015", "year": 2015, "file": "LD009", "excess": {"standard": 4000, "windscreen": 1500},
                   "notification_condition": "melde skaden uten ugrunnet opphold"}],
     "policies_in_force": 141000},
    {"id": "PRD-MOT-SE", "name": "Motor Privat Sverige", "code": "MOTSE", "line": "Motor", "region": "SE", "currency": "SEK",
     "claim_types": ["CT-COL", "CT-THF", "CT-WSC", "CT-FIR", "CT-VAN", "CT-BIJ", "CT-TPD"],
     "excess": {"standard": 3000, "windscreen": 1000}, "local_excess_term": "självrisk", "wordings": [], "policies_in_force": 96000},
    {"id": "PRD-MOT-DK", "name": "Motor Privat Danmark", "code": "MOTDK", "line": "Motor", "region": "DK", "currency": "DKK",
     "claim_types": ["CT-COL", "CT-THF", "CT-WSC", "CT-FIR", "CT-VAN", "CT-BIJ", "CT-TPD"],
     "excess": {"standard": 5000, "windscreen": 1500}, "local_excess_term": "selvrisiko", "wordings": [], "policies_in_force": 61000},
    {"id": "PRD-HOM-NO", "name": "Hjem Norge", "code": "HOMNO", "line": "Home", "region": "NO", "currency": "NOK",
     "claim_types": ["CT-THF", "CT-FIR", "CT-EOW", "CT-STM", "CT-FLD", "CT-ACD", "CT-VAN", "CT-FRO", "CT-SNO"],
     "excess": {"standard": 6000}, "local_excess_term": "egenandel",
     "wordings": [{"version": "HOM-NO-2017", "year": 2017, "file": "LD011", "excess": {"standard": 4000},
                   "notification_condition": "melde skaden uten ugrunnet opphold", "frost_damage_covered": True}],
     "policies_in_force": 118000},
    {"id": "PRD-HOM-SE", "name": "Hem Sverige", "code": "HOMSE", "line": "Home", "region": "SE", "currency": "SEK",
     "claim_types": ["CT-THF", "CT-FIR", "CT-EOW", "CT-STM", "CT-FLD", "CT-ACD", "CT-VAN", "CT-FRO", "CT-SNO"],
     "excess": {"standard": 2000}, "local_excess_term": "självrisk",
     "wordings": [{"version": "HOM-SE-2016", "year": 2016, "file": "LD008", "excess": {"standard": 1500},
                   "notification_condition": "anmäla skadan snarast"}],
     "policies_in_force": 104000},
    {"id": "PRD-HOM-DK", "name": "Hjem Danmark", "code": "HOMDK", "line": "Home", "region": "DK", "currency": "DKK",
     "claim_types": ["CT-THF", "CT-FIR", "CT-EOW", "CT-STM", "CT-FLD", "CT-ACD", "CT-VAN", "CT-FRO", "CT-SNO"],
     "excess": {"standard": 1500}, "local_excess_term": "selvrisiko",
     "wordings": [{"version": "HOM-DK-2016", "year": 2016, "file": "LD010", "excess": {"standard": 1200},
                   "notification_condition": "anmelde skaden hurtigst muligt"}],
     "policies_in_force": 72000},
]


def build_products():
    return PRODUCTS


# ------------------------------------------------------------------ rules
def V(version, status, frm, to, text, params, approved_by, approved_on, source):
    return {"version": version, "status": status, "effective_from": frm, "effective_to": to, "text": text,
            "parameters": params, "approved_by": list(approved_by), "approved_on": approved_on, "source": source}


def R(rid, area, title, versions, implemented_in=None, applies_to=None, supersedes=(), superseded_by=None, owner=None, notes=None):
    rec = {"id": rid, "area": area, "title": title, "owner": owner, "versions": versions,
           "supersedes": [{"rule": r, "version": v} for r, v in supersedes], "superseded_by": superseded_by,
           "implemented_in": implemented_in or {"programs": [], "services": []},
           "applies_to": applies_to or {"claim_types": "all", "products": "all", "process_steps": []}}
    if notes:
        rec["notes"] = notes
    return rec


def imp(programs=(), services=()):
    return {"programs": list(programs), "services": list(services)}


def app(claim_types="all", products="all", steps=()):
    return {"claim_types": claim_types, "products": products, "process_steps": list(steps)}


M72 = "Claims Handling Manual v7.2"
M61 = "Claims Handling Manual v6.1"


def key_rules():
    K = []
    # ---------------- FNOL
    K.append(R("BR-FNOL-001", "FNOL", "FNOL acknowledgement SLA", [
        V(1, "superseded", "2012-01-01", "2024-09-30", "Acknowledge every first notice of loss within 5 business days.",
          {"ack_business_days": 5}, ["P011"], "2011-11-30", f"{M61} §5.4"),
        V(2, "superseded", "2024-10-01", "2026-06-30", "Acknowledge every first notice of loss within 2 business days (NISA Circular 2024/07).",
          {"ack_business_days": 2}, ["P005"], "2024-07-15", "NISA Circular 2024/07 §2.1; Claims Standards Bulletin CSB-2024-07"),
        V(3, "approved", "2026-07-01", None, "Acknowledge digital FNOLs (portal, app, telematics) within 1 business day and all other channels "
          "(telephone, broker, post) within 2 business days.", {"ack_business_days_digital": 1, "ack_business_days_other": 2},
          ["P005"], "2026-06-30", f"{M72} §5.4")],
        imp(["CLRFN070"], ["notification-svc", "fnol-intake-svc"]), app(steps=["PS-FNOL-05"]), owner="P011"))
    K.append(R("BR-FNOL-002", "FNOL", "Mandatory FNOL data set", [
        V(1, "approved", "2016-01-01", None, "An FNOL must capture policy number, date of loss, Claim Type (peril), loss location, contact "
          "details and a description of loss before a claim number is issued.",
          {"mandatory_fields": ["policy_no", "loss_date", "claim_type", "loss_location", "contact", "loss_description"]},
          ["P011"], "2015-11-20", f"{M61} §6.1")], imp(["CLRFN010", "CLRFN130"], ["fnol-intake-svc"]), app(steps=["PS-FNOL-01"]), owner="P011"))
    K.append(R("BR-FNOL-003", "FNOL", "Late notification review", [
        V(1, "approved", "2016-01-01", None, "Claims notified more than 30 days after the date of loss are flagged for late-notification "
          "review at triage and the policy notification condition is checked.", {"late_days": 30},
          ["P011"], "2015-11-20", f"{M61} §5.9")], imp(["CLRFN080"], ["fnol-intake-svc"]), app(steps=["PS-FNOL-04"]), owner="P011"))
    K.append(R("BR-FNOL-004", "FNOL", "Duplicate claim check", [
        V(1, "approved", "2017-04-01", None, "Before a claim is created, check for an existing claim on the same policy with a date of loss "
          "within ±3 days; a match must be confirmed or rejected by the Claims Handler.", {"window_days": 3},
          ["P011"], "2017-03-14", f"{M61} §5.7")], imp(["CLRFN060"], ["fnol-intake-svc"]), app(steps=["PS-FNOL-04"]), owner="P011"))
    K.append(R("BR-FNOL-005", "FNOL", "Default reserve at FNOL by claim type", [
        V(1, "superseded", "2020-01-01", "2024-12-31", "Create a default indemnity reserve at FNOL from the default-reserve table.",
          {"default_reserve": {"MOTUK/COL": 2400, "MOTUK/WSC": 300, "MOTUK/THF": 5800, "HOMUK/EOW": 3600, "HOMUK/STM": 2700,
                               "HOMUK/FIR": 15000, "LIAUK/BIJ": 11000, "MOTNO/COL": 28000, "HOMSE/EOW": 38000, "HOMDK/EOW": 26000}},
          ["P010", "P011"], "2019-12-10", f"{M61} §7.2"),
        V(2, "approved", "2025-01-01", None, "Create a default indemnity reserve at FNOL from the default-reserve table (2025 values).",
          {"default_reserve": {"MOTUK/COL": 2750, "MOTUK/WSC": 350, "MOTUK/THF": 6500, "HOMUK/EOW": 4200, "HOMUK/STM": 3100,
                               "HOMUK/FIR": 18000, "LIAUK/BIJ": 12500, "MOTNO/COL": 32000, "HOMSE/EOW": 45000, "HOMDK/EOW": 30500}},
          ["P010", "P005"], "2024-12-10", f"{M72} §7.2 (table 7-1)")],
        imp(["CLRFN030"], ["reserve-engine"]), app(steps=["PS-FNOL-03"]), owner="P009"))
    # ---------------- TRIAGE
    K.append(R("BR-TRI-003", "TRI", "Claim tier classification (Tier-1 / Tier-2 / Tier-3)", [
        V(1, "superseded", "2016-01-01", "2021-12-31", "Tier-3: estimated incurred ≥ £25,000 or any bodily injury. Tier-2: £5,000–£24,999. "
          "Tier-1: below £5,000 with no injury.", {"tier3_min_gbp": 25000, "tier2_min_gbp": 5000}, ["P011"], "2015-11-20", "Claims Handling Manual v5.0 §3.2"),
        V(2, "superseded", "2022-01-01", "2024-12-31", "Tier-3: estimated incurred ≥ £40,000 (NOK 500,000 / SEK 500,000 / DKK 340,000) or any bodily "
          "injury. Tier-2: £5,000–£39,999 or any third-party involvement. Tier-1: otherwise.",
          {"tier3_min_gbp": 40000, "tier3_min_nok": 500000, "tier3_min_sek": 500000, "tier3_min_dkk": 340000, "tier2_min_gbp": 5000},
          ["P011"], "2021-09-14", f"{M61} §2.4"),   # approved before the CLARA spec v3.4 (2021-09-30) that states it (C10)
        V(3, "approved", "2025-01-01", None, "A claim is Tier-3 if any of: estimated incurred ≥ £50,000 (NOK 650,000 / SEK 680,000 / DKK 430,000); "
          "any bodily injury; solicitor or litigation involvement at notification; property total loss. Tier-2: £5,000–£49,999 or any "
          "third-party involvement. Tier-1: below £5,000, no injury, no third party.",
          {"tier3_min_gbp": 50000, "tier3_min_nok": 650000, "tier3_min_sek": 680000, "tier3_min_dkk": 430000, "tier2_min_gbp": 5000,
           "tier3_triggers": ["incurred_threshold", "bodily_injury", "litigation_at_notification", "property_total_loss"]},
          ["P005"], "2024-11-26", f"Claims Standards Bulletin CSB-2024-11; {M72} §2.4 (Definitions)")],
        imp(["CLRTR020", "CLRTR030"], ["triage-svc"]), app(steps=["PS-TRI-02"]), owner="P011",
        notes="The Tier definition is used by BR-RSV-007, BR-ASM-005, BR-FRD-031 v2, BR-TRI-004 and BR-TRI-006."))
    K.append(R("BR-TRI-004", "TRI", "Routing by tier", [
        V(1, "approved", "2019-01-01", None, "Tier-3 claims route to Major & Complex Loss within 4 hours; Tier-2 to specialist Claims Handlers; "
          "Tier-1 to the fast-track queue when BR-TRI-006 is met.", {"tier3_alert_hours": 4}, ["P011"], "2018-12-04", f"{M61} §8.5")],
        imp(["CLRTR050", "CLRTR090"], ["triage-svc"]), app(steps=["PS-TRI-03", "PS-TRI-04"]), owner="P011"))
    K.append(R("BR-TRI-006", "TRI", "Fast-track eligibility and cap", [
        V(1, "superseded", "2018-03-01", "2023-12-31", "Fast-track if Tier-1, Sentinel score below 25 and no injury; cap £1,000.",
          {"max_score": 24, "cap_gbp": 1000}, ["P011"], "2018-02-13", f"{M61} §9.1"),
        V(2, "superseded", "2024-01-01", "2026-06-30", "Fast-track if Tier-1, Sentinel score below 30 and no injury; cap £1,500.",
          {"max_score": 29, "cap_gbp": 1500}, ["P005"], "2023-11-28", "Claims Standards Bulletin CSB-2023-11"),
        V(3, "approved", "2026-07-01", None, "Fast-track if Tier-1, Sentinel score below 30 and no injury; cap £2,000 (NOK 26,000 / SEK 27,000 / DKK 17,000).",
          {"max_score": 29, "cap_gbp": 2000, "cap_nok": 26000, "cap_sek": 27000, "cap_dkk": 17000}, ["P005"], "2026-06-30", f"{M72} §9.1")],
        imp(["CLRTR060", "CLRST080"], ["triage-svc", "settlement-svc"]), app(steps=["PS-TRI-03", "PS-STL-05"]), owner="P011"))
    K.append(R("BR-TRI-007", "TRI", "Sentinel pre-screen at triage", [
        V(1, "approved", "2019-06-01", None, "Every new claim is scored by Sentinel (FRAUDNET before 2025-03-01) within 15 minutes of FNOL.",
          {"score_within_minutes": 15}, ["P008", "P011"], "2019-05-16", f"{M61} §8.2")],
        imp(["CLRFR020", "CLRTR040"], ["triage-svc"]), app(steps=["PS-TRI-01"]), owner="P008"))
    # ---------------- ASSESSMENT
    K.append(R("BR-ASM-002", "ASM", "External Claims Assessor appointment", [
        V(1, "approved", "2018-01-01", None, "Tier-2 property claims above £10,000 require an external Claims Assessor (loss adjuster) from the panel, "
          "appointed within 2 business days of triage.", {"min_gbp": 10000, "appoint_within_business_days": 2},
          ["P011"], "2017-12-05", f"{M61} §10.3")], imp(["CLRAS020"], ["assessment-svc"]), app(["CT-EOW", "CT-FIR", "CT-STM", "CT-FLD", "CT-SUB"], steps=["PS-ASM-01"]), owner="P033"))
    K.append(R("BR-ASM-005", "ASM", "Inspection SLA", [
        V(1, "superseded", "2016-01-01", "2022-12-31", "Site inspection within 10 business days of appointment (Tier-3: 5 business days).",
          {"business_days": 10, "tier3_business_days": 5}, ["P011"], "2015-11-20", "Claims Handling Manual v5.0 §11.2"),
        V(2, "superseded", "2023-01-01", "2026-06-30", "Site inspection within 5 business days of appointment (Tier-3: 72 hours).",
          {"business_days": 5, "tier3_hours": 72}, ["P005"], "2022-11-29", f"{M61} §11.2"),
        V(3, "approved", "2026-07-01", None, "Site inspection within 5 business days of appointment (Tier-3: 48 hours).",
          {"business_days": 5, "tier3_hours": 48}, ["P005"], "2026-06-30", f"{M72} §11.2")],
        imp(["CLRAS050"], ["assessment-svc"]), app(steps=["PS-ASM-02"]), owner="P033"))
    K.append(R("BR-ASM-008", "ASM", "Desk assessment for low-value motor claims", [
        V(1, "approved", "2023-06-01", None, "Motor claims with an estimate below £3,000 may be desk-assessed from photos received through the "
          "Evidence Intake Gateway (minimum 6 photos).", {"max_gbp": 3000, "min_photos": 6}, ["P005"], "2023-05-16", "Claims Standards Bulletin CSB-2023-05")],
        imp(["CLRAS090"], ["assessment-svc"]), app(["CT-COL", "CT-VAN", "CT-WSC"], steps=["PS-ASM-02"]), owner="P033"))
    K.append(R("BR-ASM-011", "ASM", "Gradual-leak evidence threshold", [
        V(1, "approved", "2022-02-01", None, "A moisture reading of 25% WME or more in adjacent timber indicates a long-term (gradual) leak, which is "
          "excluded as not a sudden escape of water; the Claims Assessor must photograph the meter reading.", {"moisture_wme_pct": 25},
          ["P011"], "2022-01-11", "Claims Assessor Field Guide 2022 §4")], imp([], ["assessment-svc"]), app(["CT-EOW"], steps=["PS-ASM-03"]), owner="P033"))
    K.append(R("BR-ASM-012", "ASM", "Subsidence structural engineer referral", [
        V(1, "approved", "2020-04-01", None, "Subsidence cracks wider than 5 mm require referral to a structural engineer before cover is confirmed.",
          {"crack_width_mm": 5}, ["P011"], "2020-03-10", "Claims Assessor Field Guide 2020 §7")], imp([], ["assessment-svc"]), app(["CT-SUB"], ["PRD-HOM-UK"], ["PS-ASM-02"]), owner="P033"))
    # ---------------- RESERVING
    K.append(R("BR-RSV-001", "RSV", "Initial reserve timing", [
        V(1, "approved", "2016-01-01", None, "A claim-specific initial reserve must replace the FNOL default reserve within 2 business days of FNOL.",
          {"business_days": 2}, ["P010"], "2015-12-08", f"{M61} §17.2")], imp(["CLRRS010"], ["reserve-engine"]), app(steps=["PS-RSV-01"]), owner="P009"))
    K.append(R("BR-RSV-003", "RSV", "Reserve authority limits", [
        V(1, "superseded", "2017-01-01", "2022-12-31", "Reserve authority: Claims Handler £10,000; Team Leader £50,000; Claims Manager £250,000; "
          "Claims Director £1,000,000; above that the Reserving Committee.",
          {"claims_handler": 10000, "team_leader": 50000, "claims_manager": 250000, "claims_director": 1000000}, ["P010"], "2016-12-13", f"{M61} §18.1"),
        V(2, "superseded", "2023-01-01", "2025-08-31", "Reserve authority: Claims Handler £20,000; Team Leader £75,000; Claims Manager £400,000; "
          "Claims Director £1,500,000; above that the Reserving Committee.",
          {"claims_handler": 20000, "team_leader": 75000, "claims_manager": 400000, "claims_director": 1500000}, ["P010", "P005"], "2022-12-13", f"{M61} §18.1 (amended)"),
        V(3, "approved", "2025-09-01", None, "Reserve authority: Claims Handler £25,000; Team Leader £100,000; Claims Manager £500,000; "
          "Claims Director £2,000,000; above that the Reserving Committee. Nordic reserves are tested at the GBP equivalent at the GL month-end rate.",
          {"claims_handler": 25000, "team_leader": 100000, "claims_manager": 500000, "claims_director": 2000000}, ["P010", "P005"], "2025-08-12", f"{M72} §18.1")],
        imp(["CLRRS015", "CLRRS040"], ["reserve-engine"]), app(steps=["PS-RSV-02"]), owner="P009"))
    K.append(R("BR-RSV-007", "RSV", "Tier-3 reserve review cadence", [
        V(1, "superseded", "2015-01-01", "2023-12-31", "Reserves on Tier-3 claims must be reviewed at least every 30 days.", {"review_days": 30},
          ["P010"], "2014-11-11", f"{M61} §19.4"),
        V(2, "superseded", "2024-01-01", "2026-06-30", "Reserves on Tier-3 claims must be reviewed at least every 21 days.", {"review_days": 21},
          ["P010"], "2023-11-14", "Reserving Committee 2023-11-14; Claims Standards Bulletin CSB-2023-12"),
        V(3, "approved", "2026-07-01", None, "Reserves on Tier-3 claims must be reviewed at least every 14 days.", {"review_days": 14},
          ["P009"], "2026-06-09", f"Reserving Committee 2026-06-09; {M72} §19.4")],
        imp(["CLRRS110", "CLRRS120"], ["reserve-engine"]), app(steps=["PS-RSV-03"]), owner="P009"))
    K.append(R("BR-RSV-009", "RSV", "Reserve indexation for bodily-injury claims", [
        V(1, "superseded", "2019-01-01", "2023-12-31", "Index open bodily-injury reserves monthly at 2.5% per annum.", {"index_pct_pa": 2.5},
          ["P010"], "2018-12-11", f"{M61} §20.2"),
        V(2, "superseded", "2024-01-01", "2025-12-31", "Index open bodily-injury reserves monthly at 4.0% per annum.", {"index_pct_pa": 4.0},
          ["P010"], "2023-12-12", "Reserving Committee 2023-12-12"),
        V(3, "approved", "2026-01-01", None, "Index open bodily-injury reserves monthly at 3.1% per annum.", {"index_pct_pa": 3.1},
          ["P009"], "2025-12-09", f"Reserving Committee 2025-12-09; {M72} §20.2")],
        imp(["CLRRS130"], ["reserve-engine"]), app(["CT-BIJ"], steps=["PS-RSV-03"]), owner="P009"))
    K.append(R("BR-RSV-011", "RSV", "Large loss notification to Reinsurance", [
        V(1, "superseded", "2018-01-01", "2023-12-31", "Notify Reinsurance within 48 hours of any reserve movement of £200,000 or more.",
          {"threshold_gbp": 200000, "notify_hours": 48}, ["P010"], "2017-12-12", f"{M61} §22.3"),
        V(2, "approved", "2024-01-01", None, "Notify Reinsurance (ReCede) within 24 hours of any reserve movement exceeding the Large Loss Notification "
          "Threshold (LLNT) of £250,000.", {"threshold_gbp": 250000, "notify_hours": 24, "name": "Large Loss Notification Threshold (LLNT)"},
          ["P010", "P038"], "2023-12-12", f"{M72} §22.3; Reinsurance treaty summary 2026")],
        imp(["CLRRS160"], ["reserve-engine"]), app(steps=["PS-RSV-04"]), owner="P038"))
    K.append(R("BR-RSV-012", "RSV", "Nordic reserve currency and revaluation", [
        V(1, "approved", "2019-01-01", None, "Nordic reserves are held in NOK, SEK or DKK; GBP equivalents use the Group Ledger month-end rate and a "
          "full revaluation runs at year-end (CLRGL090; reserve-engine revaluation runs from Wave 2).", {"rate_source": "Group Ledger month-end"},
          ["P010"], "2018-12-11", f"{M61} §20.5")], imp(["CLRGL090", "CLRCM030"], ["reserve-engine"]), app(products=["PRD-MOT-NO", "PRD-MOT-SE", "PRD-MOT-DK", "PRD-HOM-NO", "PRD-HOM-SE", "PRD-HOM-DK"]), owner="P009"))
    K.append(R("BR-RSV-014", "RSV", "Reserve close-down at final settlement", [
        V(1, "approved", "2016-01-01", None, "On final settlement the outstanding reserve is reduced to zero within 1 business day and a settlement "
          "close movement (type ST) is recorded.", {"business_days": 1}, ["P010"], "2015-12-08", f"{M61} §32.1")],
        imp(["CLRST040"], ["settlement-svc", "reserve-engine"]), app(steps=["PS-STL-04"]), owner="P009"))
    # ---------------- FRAUD
    K.append(R("BR-FRD-005", "FRD", "Linked-claims indicator", [
        V(1, "superseded", "2017-01-01", "2020-12-31", "Flag a linked-claims indicator when the claimant has 3 or more claims in 24 months.",
          {"min_claims": 3, "months": 24}, ["P008"], "2016-12-01", "Claims Fraud Forum 2016-12-01"),
        V(2, "superseded", "2021-01-01", "2026-03-31", "Flag a linked-claims indicator when the claimant has 2 or more claims in 12 months.",
          {"min_claims": 2, "months": 12}, ["P008"], "2020-11-26", "Claims Fraud Forum 2020-11-26"),
        V(3, "approved", "2026-04-01", None, "Flag a linked-claims indicator when the claimant has 2 or more claims in 12 months, or when a bank "
          "account or telephone number is shared with another claimant.", {"min_claims": 2, "months": 12, "shared_identifiers": ["bank_account", "phone"]},
          ["P008", "P005"], "2026-03-12", "Claims Fraud Forum 2026-03-12")],
        imp(["CLRFR080"], ["fraud-referral-svc"]), app(steps=["PS-FRD-01"]), owner="P008"))
    K.append(R("BR-FRD-012", "FRD", "Fraud referral threshold (pre-2026)", [
        V(1, "superseded", "2019-01-01", "2023-03-31", "Refer a claim to SIU when the FRAUDNET score is 75 or more.", {"threshold": 75},
          ["P008"], "2018-12-06", "Claims Handling Manual v5.0 §27.3"),
        V(2, "superseded", "2023-04-01", "2026-03-31", "Refer a claim to SIU when the FRAUDNET/Sentinel score is 70 or more.", {"threshold": 70},
          ["P008"], "2023-03-09", f"{M61} §28.3")],
        imp(["CLRFR030", "CLRFR040"], []), app(steps=["PS-FRD-01"]), superseded_by="BR-FRD-031", owner="P008"))
    K.append(R("BR-FRD-019", "FRD", "Automatic decline on very high fraud score", [
        V(1, "superseded", "2019-06-01", "2022-12-31", "Automatically decline a claim when the FRAUDNET score is 95 or more.", {"threshold": 95},
          ["P008"], "2019-05-16", "Claims Fraud Forum 2019-05-16"),
        V(2, "withdrawn", "2023-01-01", "2026-03-31", "Automatically decline a claim when the FRAUDNET/Sentinel score is 90 or more. Withdrawn from "
          "2026-04-01: NISA Circular 2026/04 §3.1 prohibits adverse decisions on an automated score alone.", {"threshold": 90},
          ["P008"], "2022-12-01", "Claims Fraud Forum 2022-12-01")],
        imp(["CLRFR140"], []), app(steps=["PS-FRD-05"]), superseded_by="BR-FRD-033", owner="P008"))
    K.append(R("BR-FRD-031", "FRD", "Fraud referral threshold (NISA Circular 2026/04)", [
        V(1, "superseded", "2026-04-01", "2026-09-30", "Refer a claim to SIU when the Sentinel score is 65 or more (all tiers).", {"threshold": 65},
          ["P008", "P005"], "2026-03-12", f"NISA Circular 2026/04 §3.3; {M72} §28.3"),
        V(2, "approved", "2026-10-01", None, "Refer a claim to SIU when the Sentinel score is 65 or more; for Tier-3 claims (BR-TRI-003) refer at a "
          "Sentinel score of 60 or more.", {"threshold": 65, "tier3_threshold": 60},
          ["P008", "P005"], "2026-09-17", "Fraud Rules Workshop 2026-09-17 (decision DEC-014); minutes TX031")],
        imp(["CLRFR030", "CLRFR040"], ["fraud-referral-svc", "triage-svc"]), app(steps=["PS-FRD-01"]),
        supersedes=[("BR-FRD-012", 2)], owner="P008",
        notes="v2 post-dates the manual v7.2 (approved 2026-06-30), which still states 65 for all claims. CLRFR040 still hard-codes 70 in code variant a."))
    K.append(R("BR-FRD-032", "FRD", "Customer notification of fraud referral", [
        V(1, "draft", None, None, "DRAFT: notify the customer in writing within 5 business days of referral.", {"notice_business_days": 5},
          [], None, "DRAFT BRD v0.3 (2026-02-10)"),
        V(2, "approved", "2026-04-01", None, "Notify the customer in writing within 10 business days of a fraud referral that the claim is subject to "
          "additional checks, unless the notice is deferred under BR-FRD-036.", {"notice_business_days": 10},
          ["P008", "P005"], "2026-03-12", "NISA Circular 2026/04 §3.2; APPROVED BRD v1.0 (2026-03-12); " + M72 + " §29.1")],
        imp(["CLRFR060"], ["fraud-referral-svc", "notification-svc"]), app(steps=["PS-FRD-03"]), owner="P008"))
    K.append(R("BR-FRD-033", "FRD", "No adverse decision on fraud score alone", [
        V(1, "approved", "2026-04-01", None, "No claim may be declined, reduced or repudiated on the basis of an automated fraud score alone; every "
          "adverse outcome requires a documented human review by SIU.", {"auto_decline_allowed": False},
          ["P008", "P005"], "2026-03-12", f"NISA Circular 2026/04 §3.1; {M72} §28.6")],
        imp([], ["fraud-referral-svc"]), app(steps=["PS-FRD-05"]), supersedes=[("BR-FRD-019", 2)], owner="P008"))
    K.append(R("BR-FRD-034", "FRD", "Quarterly fraud referral return (NISA-FR1)", [
        V(1, "approved", "2026-04-01", None, "Submit the NISA-FR1 fraud referral return within 30 calendar days after each quarter end; first return "
          "for Q2 2026 due 2026-07-30.", {"due_days_after_quarter": 30, "first_period": "2026Q2", "first_due": "2026-07-30"},
          ["P008", "P037"], "2026-03-12", "NISA Circular 2026/04 §3.4")],
        imp(["CLRFR090"], ["reporting-feed-svc"]), app(steps=[]), owner="P037"))
    K.append(R("BR-FRD-035", "FRD", "SIU triage of new referrals", [
        V(1, "superseded", "2019-06-01", "2026-03-31", "SIU must triage a new referral within 5 business days.", {"business_days": 5},
          ["P008"], "2019-05-16", f"{M61} §30.1"),
        V(2, "approved", "2026-04-01", None, "SIU must triage a new referral within 3 business days.", {"business_days": 3},
          ["P008"], "2026-03-12", f"{M72} §30.1")],
        imp([], ["fraud-referral-svc"]), app(steps=["PS-FRD-04"]), owner="P008"))
    K.append(R("BR-FRD-036", "FRD", "Deferral of customer notice (tipping-off risk)", [
        V(1, "superseded", "2026-04-01", "2026-09-30", "The customer notice may be deferred for up to 60 days where SIU certifies a tipping-off risk; "
          "the deferral must be approved by an authorised SIU approver (see parameters).",
          {"max_deferral_days": 60, "approvers": ["SIU Investigations Manager (UK)", "Head of Counter-Fraud & SIU"]},
          ["P008", "P005"], "2026-03-12", f"NISA Circular 2026/04 §3.2; {M72} §29.3"),
        V(2, "approved", "2026-10-01", None, "The customer notice may be deferred for up to 60 days where SIU certifies a tipping-off risk; deferrals "
          "beyond 30 days require the Head of Counter-Fraud & SIU and Compliance must be notified the same day.",
          {"max_deferral_days": 60, "head_approval_after_days": 30, "notify": "Compliance"},
          ["P008", "P005"], "2026-09-17", "Fraud Rules Workshop 2026-09-17 (decision DEC-015)")],
        imp(["CLRFR120"], ["fraud-referral-svc"]), app(steps=["PS-FRD-03"]), owner="P008"))
    # ---------------- SETTLEMENT
    K.append(R("BR-STL-002", "STL", "Payment authority limits", [
        V(1, "superseded", "2017-01-01", "2022-12-31", "Payment authority: Claims Handler £5,000; Team Leader £25,000; Claims Manager £150,000; Claims Director £750,000.",
          {"claims_handler": 5000, "team_leader": 25000, "claims_manager": 150000, "claims_director": 750000}, ["P011"], "2016-12-01", f"{M61} §25.2"),
        V(2, "superseded", "2023-01-01", "2025-08-31", "Payment authority: Claims Handler £10,000; Team Leader £50,000; Claims Manager £250,000; Claims Director £1,000,000.",
          {"claims_handler": 10000, "team_leader": 50000, "claims_manager": 250000, "claims_director": 1000000}, ["P005"], "2022-11-29", f"{M61} §25.2 (amended)"),
        V(3, "approved", "2025-09-01", None, "Payment authority: Claims Handler £15,000; Team Leader £75,000; Claims Manager £350,000; Claims Director £1,500,000.",
          {"claims_handler": 15000, "team_leader": 75000, "claims_manager": 350000, "claims_director": 1500000}, ["P005", "P001"], "2025-08-12", f"{M72} §25.2")],
        imp(["CLRST020"], ["payment-orchestrator"]), app(steps=["PS-STL-02"]), owner="P011"))
    K.append(R("BR-STL-004", "STL", "Settlement offer validity", [
        V(1, "approved", "2018-01-01", None, "A settlement offer remains valid for 30 days from the offer date.", {"validity_days": 30},
          ["P011"], "2017-12-05", f"{M61} §31.2")], imp(["CLRST010"], ["settlement-svc"]), app(steps=["PS-STL-01"]), owner="P011"))
    K.append(R("BR-STL-007", "STL", "Sanctions screening before payment", [
        V(1, "approved", "2017-06-01", None, "Every payee must pass WatchScreen sanctions screening before any claim payment is released.",
          {"screening_system": "WatchScreen"}, ["P007"], "2017-05-16", f"{M61} §26.1")], imp(["CLRST070"], ["payment-orchestrator"]), app(steps=["PS-STL-03"]), owner="P037"))
    K.append(R("BR-STL-009", "STL", "Straight-through payment for fast-track claims", [
        V(1, "approved", "2018-03-01", None, "Fast-track claims meeting BR-TRI-006 are paid straight through without Claims Handler approval up to the "
          "BR-TRI-006 cap.", {"cap_rule": "BR-TRI-006"}, ["P011"], "2018-02-13", f"{M61} §9.4")], imp(["CLRST080"], ["settlement-svc"]), app(steps=["PS-STL-05"]), owner="P011"))
    K.append(R("BR-STL-014", "STL", "Interest on late payment", [
        V(1, "approved", "2021-01-01", None, "Where payment is made more than 30 days after settlement is agreed, add simple interest at 3.5% per annum "
          "from day 31.", {"days": 30, "interest_pct_pa": 3.5}, ["P011"], "2020-12-01", f"{M61} §31.6")], imp(["CLRST100"], ["payment-orchestrator"]), app(steps=["PS-STL-03"]), owner="P011"))
    # ---------------- RECOVERY
    K.append(R("BR-REC-001", "REC", "Recovery potential identification", [
        V(1, "approved", "2016-04-01", None, "Where a third party is wholly or partly at fault, the Claims Assessor or Claims Handler flags recovery "
          "potential and a subrogation case is opened within 10 business days.", {"open_within_business_days": 10},
          ["P015"], "2016-03-15", f"{M61} §33.2")], imp(["CLRRC010", "CLRRC020"], ["recovery-svc"]), app(steps=["PS-REC-01"]), owner="P013"))
    K.append(R("BR-REC-003", "REC", "Subrogation pursuit threshold", [
        V(1, "superseded", "2016-01-01", "2022-06-30", "Pursue subrogation where the recoverable amount is £500 or more.", {"min_gbp": 500},
          ["P011"], "2015-12-01", f"{M61} §34.1"),
        V(2, "superseded", "2022-07-01", "2025-08-31", "Pursue subrogation where the recoverable amount is £750 or more.", {"min_gbp": 750},
          ["P015"], "2022-06-14", f"{M61} §34.1 (amended)"),
        V(3, "approved", "2025-09-01", None, "Pursue subrogation where the recoverable amount is £1,000 or more (NOK 13,000 / SEK 13,500 / DKK 8,600).",
          {"min_gbp": 1000, "min_nok": 13000, "min_sek": 13500, "min_dkk": 8600}, ["P005"], "2025-08-20", f"{M72} §34.1")],
        imp(["CLRRC020"], ["recovery-svc"]), app(steps=["PS-REC-02"]), owner="P013"))
    K.append(R("BR-REC-005", "REC", "Solicitor referral for recoveries", [
        V(1, "superseded", "2019-01-01", "2025-08-31", "Refer a recovery to Quarryhill Solicitors when the recoverable amount is £15,000 or more or liability is defended.",
          {"min_gbp": 15000}, ["P015"], "2018-12-04", f"{M61} §34.5"),
        V(2, "approved", "2025-09-01", None, "Refer a recovery to Quarryhill Solicitors when the recoverable amount is £25,000 or more or liability is defended.",
          {"min_gbp": 25000}, ["P005"], "2025-08-20", f"{M72} §34.5")],
        imp(["CLRRC060"], ["recovery-svc"]), app(steps=["PS-REC-03"]), owner="P013"))
    K.append(R("BR-REC-007", "REC", "Salvage disposal timing", [
        V(1, "approved", "2018-06-01", None, "Total-loss vehicles are released to Salvanta Salvage within 5 business days of the total-loss decision.",
          {"business_days": 5}, ["P015"], "2018-05-15", f"{M61} §35.2")], imp(["CLRRC070"], ["recovery-svc"]), app(["CT-COL", "CT-FIR", "CT-THF"], steps=["PS-REC-04"]), owner="P013"))
    K.append(R("BR-REC-009", "REC", "Limitation diary", [
        V(1, "approved", "2017-01-01", None, "Set a limitation diary at 30 months for bodily-injury recoveries and at 66 months for property recoveries.",
          {"bi_months": 30, "property_months": 66}, ["P015"], "2016-12-06", f"{M61} §34.8")], imp(["CLRRC080"], ["recovery-svc"]), app(steps=["PS-REC-02"]), owner="P013"))
    K.append(R("BR-REC-011", "REC", "Recovery write-off authority", [
        V(1, "superseded", "2019-01-01", "2025-08-31", "Write-offs of recoveries above £5,000 require approval by the Recoveries Manager.",
          {"min_gbp": 5000, "approver": "Recoveries Manager"}, ["P015"], "2018-12-04", f"{M61} §34.9"),
        V(2, "approved", "2025-09-01", None, "Write-offs of recoveries above £10,000 require approval by the Head of Recoveries & Subrogation.",
          {"min_gbp": 10000, "approver": "Head of Recoveries & Subrogation"}, ["P005"], "2025-08-20", f"{M72} §34.9")],
        imp(["CLRRC090"], ["recovery-svc"]), app(steps=["PS-REC-06"]), owner="P013"))
    # ---------------- GENERAL
    K.append(R("BR-GEN-004", "GEN", "Claims data retention", [
        V(1, "superseded", "2018-05-25", "2019-12-31", "Retain claim records for 10 years after closure.", {"years_after_closure": 10},
          ["P019"], "2018-05-21", "Data Retention Schedule 2018"),
        V(2, "superseded", "2020-01-01", "2025-12-31", "Retain claim records for 7 years after closure.", {"years_after_closure": 7},
          ["P019"], "2019-11-19", "Data Retention Schedule 2020"),
        V(3, "approved", "2026-01-01", None, "Retain claim records for 7 years after closure; bodily-injury claims for 15 years after closure.",
          {"years_after_closure": 7, "bi_years_after_closure": 15}, ["P019", "P007"], "2025-11-25", "NISA Circular 2025/11 §2; " + M72 + " §36.2")],
        imp(["CLRCM140"], ["document-svc", "claim-core-svc"]), app(steps=[]), owner="P019"))
    K.append(R("BR-GEN-006", "GEN", "No production personal data in test environments", [
        V(1, "approved", "2026-01-01", None, "Production personal data must not be used in test or development environments; migration rehearsals use "
          "masked extracts (NISA Circular 2025/11 §4).", {"masking_required": True}, ["P019"], "2025-11-25", "NISA Circular 2025/11 §4")],
        imp([], ["claim-core-svc"]), app(steps=[]), owner="P019"))
    return K


# ---- generated minor rules ------------------------------------------------
MINOR = {
    "FNOL": [
        ("Mandatory field: vehicle registration (motor)", "Motor FNOLs must capture the vehicle registration.", {"field": "vehicle_reg"}),
        ("Mandatory field: police crime reference for theft", "Theft FNOLs must capture a police crime reference within {days} days.", {"days": 7}),
        ("Mandatory field: third-party details", "Where a third party is involved, capture name, vehicle or address and insurer if known.", {"field": "third_party"}),
        ("Telematics crash alert to draft FNOL", "A telematics crash alert creates a draft FNOL within {minutes} minutes.", {"minutes": 5}),
        ("Broker FNOL reference", "Broker-submitted FNOLs must carry the broker reference.", {"field": "broker_ref"}),
        ("Portal photo upload limits", "Portal and app FNOLs accept up to {n} photos of at most {mb} MB each.", {"n": 20, "mb": 15}),
        ("Out-of-hours callback", "Out-of-hours telephone FNOLs receive a callback by {time} the next business day.", {"time": "10:00"}),
        ("Nordic language preference", "Record the claimant's language preference (NO, SV, DA or EN) at FNOL.", {"languages": ["NO", "SV", "DA", "EN"]}),
        ("Vulnerable customer flag", "Capture a vulnerability indicator at FNOL and route flagged customers to a trained handler.", {"field": "vulnerable"}),
        ("Emergency services indicator for fire", "Fire FNOLs must record whether the fire service attended.", {"field": "fire_service_attended"}),
        ("FNOL loss location geocoding", "Loss locations are geocoded to postcode / postnummer level.", {"precision": "postcode"}),
        ("Nordic personal number masking", "Nordic FNOLs show the personal number masked (last 4 digits only) outside production.", {"visible_digits": 4}),
        ("Foreign vehicle flag", "Motor FNOLs record whether a foreign-registered vehicle is involved.", {"field": "foreign_vehicle"}),
        ("Emergency make-safe authority", "Contact centre staff may authorise emergency make-safe work up to £{amt} at FNOL.", {"amt": 500}),
        ("Storm event code", "Storm FNOLs are tagged with the weather event code issued by Claims Operations.", {"field": "event_code"}),
        ("Third-party reported FNOL", "FNOLs reported by a third party need policyholder confirmation within {days} business days.", {"days": 5}),
    ],
    "TRI": [
        ("Routing: Escape of Water Tier-2", "Tier-2 Escape of Water claims route to Property Claims – Leeds.", {"team": "T04"}),
        ("Routing: bodily injury", "Any claim with bodily injury routes to Major & Complex Loss regardless of amount.", {"team": "T09"}),
        ("Routing: Nordic claims", "Claims in NO, SE and DK route to Claims Operations Nordics.", {"team": "T05"}),
        ("Re-tier on estimate change", "Re-run tier classification when the estimate crosses a tier boundary.", {"trigger": "estimate_change"}),
        ("Tier override approval", "A manual tier override needs a reason code and Team Leader approval within {hours} hours.", {"hours": 24}),
        ("Theft without police reference", "Theft claims over £{amt} without a police reference after 7 days go to SIU pre-screen review.", {"amt": 5000}),
        ("Windscreen network routing", "Windscreen claims route to the glass network (Thistlecombe in the UK, Lyngholm Glass in Denmark).", {}, 2019),
        ("Storm surge mode", "When daily storm FNOLs exceed {n}, triage switches to surge mode with simplified routing.", {"n": 1500}),
        ("Commercial BI triage", "Business Interruption claims are always Tier-2 or above.", {"min_tier": 2}),
        ("Repeat claimant triage note", "Triage records a note when the policyholder has an open claim.", {}),
        ("Nordic tiering currency", "Nordic claims are tiered on the local-currency amount using the BR-TRI-003 equivalents.", {}),
        ("Subsidence routing", "Subsidence claims route to Property Claims – Leeds with an external Claims Assessor.", {"team": "T04"}),
        ("Flood triage", "Flood claims above £{amt} route to Major & Complex Loss.", {"amt": 30000}),
        ("Suspected arson triage", "Fire claims with suspected arson go to SIU pre-screen review.", {}),
        ("Liability injury triage", "Public liability claims involving injury are always Tier-3.", {}),
    ],
    "ASM": [
        ("Desk assessment for windscreen", "Windscreen claims are always desk-assessed.", {}),
        ("Video assessment for Escape of Water", "Escape of Water claims below £{amt} may be assessed by video call.", {"amt": 7500}, 2020),
        ("Assessor report photo minimum", "Claims Assessor reports must include at least {n} photos.", {"n": 6}),
        ("Assessor report deadline", "A Claims Assessor report is due within {days} business days of inspection.", {"days": 5}),
        ("Repair network first", "Offer a repair-network repair before a cash settlement for motor own-damage.", {}),
        ("Nordic takst minimum", "Nordic home claims above NOK {amt} require an on-site takst (assessment).", {"amt": 120000}),
        ("Assessor conflict of interest", "A Claims Assessor may not assess a claim involving a relative or a prior employer within {years} years.", {"years": 3}),
        ("Coverage decision letter", "The coverage decision is sent within {days} business days of the assessor report.", {"days": 3}),
        ("Assessor re-inspection", "Re-inspection is required when the estimate rises by more than {pct}%.", {"pct": 25}),
        ("Panel allocation", "Panel instructions are allocated by postcode area and current vendor load.", {}),
        ("Nordic external assessor", "All external Nordic instructions go to Norrvik Skadetaxering.", {"vendor": "VEN-02"}, 2019),
        ("Motor total loss", "A vehicle is a total loss when repair cost exceeds {pct}% of market value.", {"pct": 65}),
        ("Contents proof of ownership", "Contents items above £{amt} need proof of ownership.", {"amt": 1500}),
        ("Drying monitoring", "Drying contractors report moisture readings every {days} days.", {"days": 7}),
    ],
    "RSV": [
        ("Expense reserve: Escape of Water", "Set an expense reserve of {pct}% of the indemnity reserve on Escape of Water claims.", {"pct": 8}),
        ("Expense reserve: bodily injury", "Set an expense reserve of {pct}% of the indemnity reserve on bodily-injury claims.", {"pct": 15}),
        ("Expense reserve: commercial property", "Set an expense reserve of {pct}% on commercial property claims.", {"pct": 10}),
        ("Legal reserve for litigated claims", "Set a legal reserve of £{amt} when proceedings are issued.", {"amt": 15000}),
        ("Reserve review on assessor report", "Review the reserve within {days} business days of receiving an assessor report.", {"days": 2}),
        ("Nil reserve closure", "Claims with a nil reserve and no open payments close within {days} business days.", {"days": 5}),
        ("Large reserve increase review", "A reserve increase of more than {pct}% in one movement requires Team Leader review.", {"pct": 50}),
        ("Reserve reason codes", "Every reserve movement carries a reason code from the RSNC code list.", {"code_list": "RSNC"}),
        ("Recovery netting", "Expected recoveries are recorded separately and netted only when received.", {}),
        ("Reserve after reopen", "A reopened claim needs a new reserve within {days} business days.", {"days": 2}),
        ("Reserve for BI claims > 12 months", "BI reserves open for more than 12 months are reviewed by the Reserving team quarterly.", {"months": 12}),
        ("Month-end reserve snapshot", "A month-end reserve snapshot is retained for 10 years.", {"years": 10}),
        ("Reserve rounding", "Reserves are held to 2 decimal places and shown to whole currency units in reports.", {"decimals": 2}),
        ("BI reserve forensic review", "Business Interruption reserves above £{amt} are reviewed monthly with a forensic accountant.", {"amt": 100000}),
        ("Litigated reserve review", "Litigated claims are re-reserved at every court milestone.", {}),
        ("Reserve release on nil settlement", "On a nil settlement the reserve is released in full within {days} business day.", {"days": 1}),
        ("Ceded reserve recalculation", "Ceded reserves are recalculated monthly by CLRGL040.", {}),
    ],
    "FRD": [
        ("Indicator: policy inception < 30 days", "Add {pts} pre-screen points when the loss occurs within 30 days of inception.", {"pts": 15}),
        ("Indicator: late notification", "Add {pts} pre-screen points when the claim is notified more than 30 days after the loss.", {"pts": 10}),
        ("Indicator: prior claims", "Add {pts} pre-screen points for 3 or more prior claims in 36 months.", {"pts": 12}),
        ("Indicator: missing keys in vehicle theft", "Add {pts} pre-screen points when not all keys can be produced.", {"pts": 8}),
        ("Indicator: address mismatch", "Add {pts} pre-screen points when the claimant address differs from the policy address.", {"pts": 6}),
        ("Indicator: recent cover increase", "Add {pts} pre-screen points when cover was increased within 60 days of the loss.", {"pts": 10}),
        ("Indicator: photo metadata mismatch", "Add {pts} pre-screen points when photo metadata dates differ from the date of loss.", {"pts": 14}),
        ("Indicator: shared bank account", "Add {pts} pre-screen points when the payee bank account is linked to 2 or more claimants.", {"pts": 20}),
        ("SIU partner surveillance authorisation", "Surveillance by Greyfold Investigations requires written approval by the SIU Investigations Manager.", {}, 2018),
        ("SIU case closure codes", "SIU cases close with NF (no fraud), CF (confirmed fraud) or WD (withdrawn).", {"codes": ["NF", "CF", "WD"]}),
        ("Fraud savings recording", "Record the avoided payment as the fraud saving on CF outcomes.", {}),
        ("Indicator: injury without hospital attendance", "Add {pts} pre-screen points for an injury claim with no hospital attendance.", {"pts": 9}),
        ("Indicator: late-night single-vehicle collision", "Add {pts} pre-screen points for a single-vehicle collision between 23:00 and 04:00.", {"pts": 5}),
        ("Indicator: frequent address changes", "Add {pts} pre-screen points for 3 or more address changes in 12 months.", {"pts": 7}),
        ("SIU outcome feedback", "Claims Handlers receive the SIU outcome within {days} business days of case closure.", {"days": 2}),
        ("Counter-fraud training", "Claims Handlers complete counter-fraud training every {months} months.", {"months": 12}),
    ],
    "STL": [
        ("Payment method: UK", "UK claim payments use Faster Payments; cheques were withdrawn on 2024-06-30.", {"cheques_withdrawn": "2024-06-30"}, 2025),
        ("Payment method: Nordics", "Nordic claim payments use SEPA or domestic instant transfer in local currency.", {}),
        ("Payee verification", "A new payee requires account-name verification before the first payment.", {}),
        ("Settlement letter templates", "Settlement letters use template codes STL01 to STL09.", {"templates": "STL01-STL09"}),
        ("Cash settlement for contents", "Where the customer declines a repair-network replacement, cash settlement is limited to {pct}% of replacement cost.", {"pct": 75}),
        ("Partial payments", "Interim payments are allowed once cover is confirmed.", {}),
        ("Vendor invoice payment terms", "Vendor invoices are paid within {days} days of matching.", {"days": 30}),
        ("Duplicate payment control", "Payments with the same payee, amount and claim within {days} days are held for review.", {"days": 7}),
        ("Excess deduction: Motor Private UK", "Deduct the Motor Private UK compulsory excess of £{amt} from own-damage settlements.", {"amt": "250"}),
        ("Excess deduction: Home UK escape of water", "Deduct the Home UK escape of water excess of £{amt}.", {"amt": "400"}),
        ("Excess deduction: Motor Privat Norge", "Deduct the Motor Privat Norge egenandel of NOK {amt}.", {"amt": "6,000"}),
        ("Excess deduction: Motor Privat Sverige", "Deduct the Motor Privat Sverige självrisk of SEK {amt}.", {"amt": "3,000"}),
        ("Excess deduction: Motor Privat Danmark", "Deduct the Motor Privat Danmark selvrisiko of DKK {amt}.", {"amt": "5,000"}),
        ("Excess deduction: Hjem Norge", "Deduct the Hjem Norge egenandel of NOK {amt}.", {"amt": "6,000"}),
        ("Excess deduction: Hem Sverige", "Deduct the Hem Sverige självrisk of SEK {amt}.", {"amt": "2,000"}),
        ("Excess deduction: Hjem Danmark", "Deduct the Hjem Danmark selvrisiko of DKK {amt}.", {"amt": "1,500"}),
    ],
    "REC": [
        ("Recovery pursuit: motor collision", "Collision claims with a third party at fault are pursued for the full outlay including excess.", {}),
        ("Excess refund on recovery", "Refund the customer's excess within {days} business days of a full recovery.", {"days": 10}),
        ("Uninsured third party tracing", "Use a tracing agent when an uninsured third party has not responded after {days} days.", {"days": 60}),
        ("Nordic regress claims", "Nordic recoveries follow the regress process with the counterparty insurer.", {}),
        ("Salvage categories", "Salvage categories A and B are scrapped; S and N may be sold for repair.", {"categories": ["A", "B", "S", "N"]}),
        ("Recovery chasing", "Unanswered subrogation demands are chased at {days} days.", {"days": 28}),
        ("Knock-for-knock exclusion", "Claims covered by a knock-for-knock arrangement are not pursued.", {}),
        ("Recovery MI", "Recovery rate is reported monthly as receipts over recoverable outlay.", {}),
        ("Salvage proceeds posting", "Salvage proceeds are posted within {days} business days of receipt.", {"days": 3}),
        ("Neighbour escape of water recovery", "Escape of water from a neighbouring property is pursued against the neighbour's insurer.", {}),
        ("Recovery correspondence language", "Nordic recovery demands are issued in the counterparty's national language.", {}),
    ],
    "GEN": [
        ("Four-eyes check on authority overrides", "Any authority override needs a second approver at the next level.", {}),
        ("Data subject access requests", "Respond to data subject access requests within {days} calendar days.", {"days": 30}, 2018),
        ("Complaint acknowledgement", "Acknowledge complaints within {days} business days.", {"days": 3}),
        ("Accessible communications", "Offer large-print, braille or audio formats on request.", {}),
        ("Record of decisions", "Material claim decisions are recorded in claim notes with the decision maker's id.", {}),
        ("Audit trail", "Every insert, update or delete on claim data writes an audit record.", {}),
        ("Interpreter services", "Interpreters are offered to claimants on request in any language.", {}),
        ("Call recording retention", "Telephone FNOL recordings are kept for {months} months.", {"months": 24}),
    ],
}

AREA_APPROVER = {
    "FNOL": [("P011", "2008-04-14"), ("P005", "2022-03-01")],
    "TRI": [("P011", "2008-04-14"), ("P005", "2022-03-01")],
    "ASM": [("P011", "2008-04-14"), ("P005", "2022-03-01")],
    "STL": [("P011", "2008-04-14"), ("P005", "2022-03-01")],
    "RSV": [("P010", "2014-06-02"), ("P009", "2025-09-01")],
    "FRD": [("P008", "2012-02-06")],
    "REC": [("P011", "2008-04-14"), ("P015", "2016-03-01"), ("P011", "2025-01-01"), ("P013", "2025-09-01")],
    "GEN": [("P011", "2008-04-14"), ("P007", "2017-05-02")],
}

AREA_IMPL = {
    "FNOL": (["CLRFN010", "CLRFN020", "CLRFN110", "CLRFN130", "CLRFN050"], ["fnol-intake-svc"]),
    "TRI": (["CLRTR010", "CLRTR020", "CLRTR050", "CLRTR100"], ["triage-svc"]),
    "ASM": (["CLRAS010", "CLRAS020", "CLRAS060", "CLRAS080", "CLRAS110"], ["assessment-svc"]),
    "RSV": (["CLRRS010", "CLRRS020", "CLRRS110", "CLRRS140"], ["reserve-engine"]),
    "FRD": (["CLRFR010", "CLRFR080", "CLRFR050"], ["fraud-referral-svc"]),
    "STL": (["CLRST010", "CLRST020", "CLRST060", "CLRST110"], ["settlement-svc", "payment-orchestrator"]),
    "REC": (["CLRRC010", "CLRRC020", "CLRRC040", "CLRRC070"], ["recovery-svc"]),
    "GEN": (["CLRCM020", "CLRCM070"], ["claim-core-svc"]),
}

CHAPTER = {"FNOL": (5, 6), "TRI": (8, 9), "ASM": (10, 11), "RSV": (17, 19), "FRD": (27, 30), "STL": (25, 31), "REC": (33, 35), "GEN": (3, 36)}


def _approver(area, date):
    cur = None
    for p, frm in AREA_APPROVER[area]:
        if date >= frm:
            cur = p
    return cur


def _source(area, frm, r):
    lo, hi = CHAPTER[area]
    ch = r.randint(lo, hi)
    sec = r.randint(1, 9)
    if area == "FRD" and frm >= "2019-01-01":
        return f"Claims Fraud Forum {day_before(frm)}"
    if frm < "2023-05-15":
        return f"{M61} §{ch}.{sec}"
    if frm < "2026-06-30":
        return f"Claims Standards Bulletin CSB-{frm[:4]}-{frm[5:7]}"
    return f"{M72} §{ch}.{sec}"


def generated_rules(existing_ids):
    out = []
    for area, items in MINOR.items():
        used = {int(i.split("-")[-1]) for i in existing_ids if i.startswith(f"BR-{area}-")}
        n = 1
        for item in items:
            title, text, params = item[:3]
            min_year = item[3] if len(item) > 3 else 2016
            while n in used:
                n += 1
            rid = f"BR-{area}-{n:03d}"
            used.add(n)
            r = rng(f"world:rule:{rid}")
            year = r.randint(min_year, 2025)
            frm = f"{year}-{r.choice(['01', '04', '07', '10'])}-01"
            versions = []
            two = r.random() < 0.22 and params and any(isinstance(v, int) for v in params.values())
            if two:
                old = {k: (int(v * r.choice([0.6, 0.75, 0.8])) if isinstance(v, int) and not isinstance(v, bool) else v) for k, v in params.items()}
                frm2_year = min(year + r.randint(2, 5), 2026)
                frm2 = f"{frm2_year}-{r.choice(['01', '04', '07'])}-01"
                if frm2 > "2026-07-01":
                    frm2 = "2026-07-01"
                if frm2 <= frm:
                    frm2 = f"{year + 1}-07-01"
                to1 = day_before(frm2)
                versions.append(V(1, "superseded", frm, to1, text.format(**old), old, [_approver(area, day_before(frm))],
                                  day_before(frm), _source(area, frm, r)))
                versions.append(V(2, "approved", frm2, None, text.format(**params), params, [_approver(area, day_before(frm2))],
                                  day_before(frm2), _source(area, frm2, r)))
            else:
                versions.append(V(1, "approved", frm, None, text.format(**params), params, [_approver(area, day_before(frm))],
                                  day_before(frm), _source(area, frm, r)))
            progs, svcs = AREA_IMPL[area]
            out.append(R(rid, area, title, versions, imp([r.choice(progs)], svcs), app(), owner=None))
            n += 1
    return out


def build_rules():
    K = key_rules()
    ids = [k["id"] for k in K]
    G = generated_rules(ids)
    allr = K + G
    allr.sort(key=lambda x: (x["area"], x["id"]))
    owners = {"FNOL": "P011", "TRI": "P011", "ASM": "P033", "RSV": "P009", "FRD": "P008", "STL": "P011", "REC": "P013", "GEN": "P019"}
    for r in allr:
        if not r["owner"]:
            r["owner"] = owners[r["area"]]
    return allr

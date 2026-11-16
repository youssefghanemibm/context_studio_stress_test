"""org.yaml and people.yaml (hand-curated)."""
from __future__ import annotations

from .common import (CORVANE, CORVANE_DOMAIN, IBM, IBM_DOMAIN, MODEL_START, NISA,
                     PROGRAMME, day_before, fold, periods)

# ---------------------------------------------------------------- org.yaml

LOCATIONS = [
    {"id": "LOC-LON", "name": "London (Group HQ)", "country": "UK", "city": "London",
     "address": "Corvane House, 14 Tallowgate, London EC3N 9ZZ", "type": "office",
     "headcount": 1180, "functions": ["Executive", "Finance", "Risk & Compliance", "Technology", "Major & Complex Loss"]},
    {"id": "LOC-LDS", "name": "Leeds Claims Centre", "country": "UK", "city": "Leeds",
     "address": "Aire Point, 3 Wharfedge Way, Leeds LS11 9ZZ", "type": "office",
     "headcount": 1240, "functions": ["Claims Operations UK", "Claims Assessment UK", "Counter-Fraud & SIU", "Legacy Claims Platforms"]},
    {"id": "LOC-BRS", "name": "Bristol Recoveries Centre", "country": "UK", "city": "Bristol",
     "address": "7 Quayhead Row, Bristol BS1 9ZZ", "type": "office",
     "headcount": 310, "functions": ["Recoveries & Subrogation (UK)", "Payments Operations"]},
    {"id": "LOC-GLA", "name": "Glasgow Contact Centre", "country": "UK", "city": "Glasgow",
     "address": "Clydeview House, 40 Broomielaw Lane, Glasgow G2 9ZZ", "type": "office",
     "headcount": 420, "functions": ["Contact Centre (FNOL)", "Data Protection"]},
    {"id": "LOC-OSL", "name": "Oslo office (Corvane Mutual Norge)", "country": "NO", "city": "Oslo",
     "address": "Fjordporten 4, 0150 Oslo", "type": "office",
     "headcount": 470, "functions": ["Claims Operations Norway", "Claims Assessment Nordics", "Regulatory Reporting", "Reinsurance"]},
    {"id": "LOC-STO", "name": "Stockholm office (Corvane Mutual Sverige)", "country": "SE", "city": "Stockholm",
     "address": "Kvarnbacken 12, 118 99 Stockholm", "type": "office",
     "headcount": 380, "functions": ["Claims Operations Sweden", "Group Recoveries & Subrogation", "Fraud analytics"]},
    {"id": "LOC-CPH", "name": "Copenhagen office (Corvane Mutual Danmark)", "country": "DK", "city": "Copenhagen",
     "address": "Kalkbrænderiløbet 31, 2150 Copenhagen", "type": "office",
     "headcount": 300, "functions": ["Claims Operations Nordics (lead)", "Integration Platform", "Data & Analytics"]},
    {"id": "LOC-LDC", "name": "Leeds Data Centre", "country": "UK", "city": "Leeds",
     "address": "Unit 9, Stourton Link, Leeds LS10 9ZZ", "type": "data_centre", "headcount": 0,
     "functions": ["z/OS LPAR PRD1 (CLARA primary)", "Sentinel VM cluster"]},
    {"id": "LOC-BDC", "name": "Bristol DR Data Centre", "country": "UK", "city": "Bristol",
     "address": "Avonside Technology Park, Bristol BS11 9ZZ", "type": "data_centre", "headcount": 0,
     "functions": ["z/OS LPAR DRP1 (CLARA disaster recovery)"]},
    # external locations
    {"id": "EXT-IBM-LON", "name": "IBM Consulting UK (team on site at Corvane House)", "country": "UK", "city": "London",
     "address": "on site, Corvane House, London", "type": "external", "headcount": 0, "functions": []},
    {"id": "EXT-IBM-OSL", "name": "IBM Consulting Norway", "country": "NO", "city": "Oslo",
     "address": "on site, Corvane Oslo office", "type": "external", "headcount": 0, "functions": []},
    {"id": "EXT-NISA-LON", "name": "NISA head office", "country": "UK", "city": "London",
     "address": "NISA, 1 Regent Quay, London E14 9ZZ", "type": "external", "headcount": 0, "functions": []},
    {"id": "EXT-VEN-MAN", "name": "Vendor office, Manchester", "country": "UK", "city": "Manchester",
     "address": "vendor premises", "type": "external", "headcount": 0, "functions": []},
    {"id": "EXT-VEN-GOT", "name": "Vendor office, Gothenburg", "country": "SE", "city": "Gothenburg",
     "address": "vendor premises", "type": "external", "headcount": 0, "functions": []},
    {"id": "EXT-VEN-LDS", "name": "Vendor office, Leeds", "country": "UK", "city": "Leeds",
     "address": "vendor premises", "type": "external", "headcount": 0, "functions": []},
    {"id": "EXT-VEN-BHM", "name": "Vendor office, Birmingham", "country": "UK", "city": "Birmingham",
     "address": "vendor premises", "type": "external", "headcount": 0, "functions": []},
]

DEPARTMENTS = [
    {"id": "DEP-EXEC", "name": "Executive Office", "head_history": [{"person": "P003", "from": "2021-01-04", "to": None}]},
    {"id": "DEP-CLM", "name": "Claims", "head_history": [{"person": "P004", "from": MODEL_START, "to": "2022-02-28"},
                                                       {"person": "P005", "from": "2022-03-01", "to": None}]},
    {"id": "DEP-FIN", "name": "Finance", "head_history": [{"person": "P002", "from": MODEL_START, "to": "2025-06-30"},
                                                        {"person": "P001", "from": "2025-07-01", "to": None}]},
    {"id": "DEP-RISK", "name": "Risk & Compliance", "head_history": [{"person": "P007", "from": MODEL_START, "to": None}]},
    {"id": "DEP-TECH", "name": "Technology", "head_history": [{"person": "P006", "from": MODEL_START, "to": None}]},
    {"id": "DEP-IBM", "name": f"IBM Consulting – {PROGRAMME} team (external)", "head_history": [{"person": "P047", "from": "2025-01-13", "to": None}]},
]


def _team(tid, name, dept, leads, github=None, formed=None, dept_history=None, name_history=None, purpose=""):
    lead_hist = [{"person": p, "from": f, "to": t} for p, f, t in periods(*leads)]
    out = {"id": tid, "name": name, "department": dept,
           "department_history": dept_history or [{"department": dept, "from": formed or MODEL_START, "to": None}],
           "lead_history": lead_hist, "formed": formed or MODEL_START, "purpose": purpose}
    if name_history:
        out["name_history"] = name_history
    if github:
        out["github_team"] = github
    return out


TEAMS = [
    _team("T01", "Executive Committee", "DEP-EXEC", [("P003", "2021-01-04")], purpose="Group executive leadership"),
    _team("T02", "Claims Operations", "DEP-CLM", [("P011", MODEL_START)],
          name_history=[{"name": "Claims Operations UK", "from": MODEL_START, "to": "2025-08-31"},
                        {"name": "Claims Operations (Group)", "from": "2025-09-01", "to": None}],
          purpose="Claims handling, triage and settlement for all regions"),
    _team("T03", "Motor Claims – Leeds", "DEP-CLM", [("P022", "2019-04-01")], formed="2019-04-01", purpose="UK motor claims handling"),
    _team("T04", "Property Claims – Leeds", "DEP-CLM", [("P039", MODEL_START)], purpose="UK home and commercial property claims"),
    _team("T05", "Claims Operations Nordics", "DEP-CLM", [("P005", MODEL_START), ("P012", "2022-03-01")],
          purpose="Claims handling in Norway, Sweden and Denmark"),
    _team("T06", "Claims Assessment UK", "DEP-CLM", [("P033", MODEL_START)], purpose="Internal Claims Assessors and vendor assessor panel (UK)"),
    _team("T07", "Claims Assessment Nordics", "DEP-CLM", [("P034", MODEL_START)], purpose="Internal Claims Assessors (Nordics)"),
    _team("T08", "Recoveries & Subrogation", "DEP-CLM", [("P015", MODEL_START), ("P014", "2025-01-01"), ("P013", "2025-09-01")],
          name_history=[{"name": "Recoveries", "from": MODEL_START, "to": "2025-08-31"},
                        {"name": "Recoveries & Subrogation (Group)", "from": "2025-09-01", "to": None}],
          purpose="Subrogation, salvage and third-party recoveries"),
    _team("T09", "Major & Complex Loss", "DEP-CLM", [("P030", MODEL_START)], purpose="Tier-3 claims handling"),
    _team("T10", "Contact Centre", "DEP-CLM", [("P029", MODEL_START)], purpose="Telephone FNOL and customer contact"),
    _team("T11", "Counter-Fraud & SIU", "DEP-RISK", [("P008", MODEL_START)],
          dept_history=[{"department": "DEP-CLM", "from": MODEL_START, "to": "2025-08-31"},
                        {"department": "DEP-RISK", "from": "2025-09-01", "to": None}],
          name_history=[{"name": "Special Investigations Unit (SIU)", "from": MODEL_START, "to": "2025-08-31"},
                        {"name": "Counter-Fraud & SIU", "from": "2025-09-01", "to": None}],
          purpose="Fraud referral handling, investigations and Sentinel model ownership"),
    _team("T12", "Reserving", "DEP-FIN", [("P009", MODEL_START)], purpose="Case reserve governance, IBNR and Reserving Committee"),
    _team("T13", "Actuarial", "DEP-FIN", [("P010", MODEL_START)], purpose="Pricing and reserving actuarial models"),
    _team("T14", "Financial Control", "DEP-FIN", [("P021", MODEL_START)], purpose="General ledger, month-end close"),
    _team("T15", "Regulatory Reporting", "DEP-FIN", [("P020", MODEL_START)], purpose="NISA returns (TP2, FR1, CT1, annual filing)"),
    _team("T16", "Payments Operations", "DEP-FIN", [("P035", MODEL_START)], purpose="Claims payments via Corvane Payments Gateway"),
    _team("T17", "Reinsurance", "DEP-FIN", [("P038", MODEL_START)], purpose="Treaty administration, cessions and bordereaux"),
    _team("T18", "Compliance", "DEP-RISK", [("P037", MODEL_START)], purpose="Conduct and counter-fraud regulation, NISA liaison"),
    _team("T19", "Data Protection", "DEP-RISK", [("P019", MODEL_START)], purpose="Data protection and retention"),
    _team("T20", "Legacy Claims Platforms (CLARA)", "DEP-TECH", [("P016", MODEL_START)], github="@corvane/clara-platform",
          purpose="CLARA COBOL/CICS/DB2 development and support"),
    _team("T21", "Claims Hub Product", "DEP-CLM", [("P017", "2025-01-13")], formed="2025-01-13",
          dept_history=[{"department": "DEP-TECH", "from": "2025-01-13", "to": "2025-08-31"},
                        {"department": "DEP-CLM", "from": "2025-09-01", "to": None}],
          purpose="Claims Hub product ownership and backlog"),
    _team("T22", "Integration Platform", "DEP-TECH", [("P031", MODEL_START)], github="@corvane/integration-platform",
          purpose="MQ Backbone, Event Streaming Platform, interface catalogue"),
    _team("T23", "Data & Analytics", "DEP-TECH", [("P036", MODEL_START)], github="@corvane/data-analytics",
          purpose="Claims Data Warehouse and MI"),
    _team("T24", "Enterprise Architecture", "DEP-TECH", [("P018", MODEL_START)], github="@corvane/architecture",
          purpose="Design Authority, ADRs"),
    _team("T25", "Mainframe Batch Operations", "DEP-TECH", [("P026", MODEL_START)], github="@corvane/batch-ops",
          purpose="JCL scheduling and batch support"),
    _team("T26", f"IBM {PROGRAMME} Team", "DEP-IBM", [("P048", "2025-01-13")], formed="2025-01-13",
          purpose="IBM Consulting delivery team for the CLARA to Claims Hub modernisation"),
    _team("T27", "Hub Squad – Intake & Triage", "DEP-TECH", [("P040", "2025-02-03")], formed="2025-02-03",
          github="@corvane/hub-squad-intake-triage", purpose="fnol-intake-svc, triage-svc, assessment-svc, claim-core-svc, notification-svc"),
    _team("T28", "Hub Squad – Reserve & Finance", "DEP-TECH", [("P041", "2025-02-03")], formed="2025-02-03",
          github="@corvane/hub-squad-reserve-finance", purpose="reserve-engine, gl-posting-svc, reporting-feed-svc"),
    _team("T29", "Hub Squad – Fraud & Settlement", "DEP-TECH", [("P042", "2025-02-03")], formed="2025-02-03",
          github="@corvane/hub-squad-fraud-settlement", purpose="fraud-referral-svc, settlement-svc, payment-orchestrator"),
    _team("T30", "Hub Squad – Recoveries & Documents", "DEP-TECH", [("P043", "2026-11-01")], formed="2026-11-01",
          github="@corvane/hub-squad-recoveries-docs", purpose="Recoveries and documents engineering squad (formed 2026-11-01)"),
    _team("T31", "Technology Delivery Office", "DEP-TECH", [("P032", MODEL_START)], github="@corvane/tech-delivery",
          purpose="Delivery management, release and change"),
]

COMMITTEES = [
    {"id": "COM-01", "name": "Reserving Committee", "cadence": "monthly, second Tuesday, 10:00 UK time",
     "chair_history": [{"person": "P010", "from": MODEL_START, "to": "2025-08-31"}, {"person": "P009", "from": "2025-09-01", "to": None}],
     "members": ["P009", "P010", "P021", "P030", "P005"], "remit": "Approves reserving policy, authority limits and reserves above the Claims Director limit"},
    {"id": "COM-02", "name": "Claims Fraud Forum", "cadence": "fortnightly, Thursday 14:00 UK time",
     "chair_history": [{"person": "P008", "from": MODEL_START, "to": None}],
     "members": ["P008", "P027", "P028", "P037", "P011", "P042"], "remit": "Fraud rules, Sentinel thresholds, SIU performance"},
    {"id": "COM-03", "name": f"{PROGRAMME} Steering Committee", "cadence": "monthly, second Thursday, 14:00 UK time",
     "chair_history": [{"person": "P004", "from": "2025-01-13", "to": None}],
     "members": ["P004", "P005", "P001", "P006", "P017", "P032", "P047", "P048"], "remit": "Programme scope, budget, cut-over go/no-go"},
    {"id": "COM-04", "name": "Change Advisory Board (CAB)", "cadence": "weekly, Wednesday 11:00 UK time",
     "chair_history": [{"person": "P032", "from": MODEL_START, "to": None}],
     "members": ["P032", "P016", "P026", "P031", "P041", "P042"], "remit": "Production change approval for CLARA and Claims Hub"},
    {"id": "COM-05", "name": "Design Authority", "cadence": "weekly, Tuesday 15:00 UK time",
     "chair_history": [{"person": "P018", "from": MODEL_START, "to": None}],
     "members": ["P018", "P049", "P050", "P031", "P016", "P041"], "remit": "Architecture decisions (ADRs), interface standards"},
]

COMPANY = {
    "id": CORVANE,
    "legal_name": "Corvane Mutual Insurance Society Limited",
    "short_name": "Corvane Mutual",
    "aliases": ["Corvane", "Corvane Mutual", "CMI", "the Society"],
    "type": "Mutual property & casualty insurer",
    "founded": 1891,
    "founded_as": "Corvane Friendly Society (Leeds)",
    "headquarters": "LOC-LON",
    "staff": 4050,
    "staff_by_country": {"UK": 2900, "NO": 470, "SE": 380, "DK": 300},
    "regions": ["UK", "Norway", "Sweden", "Denmark"],
    "branches": [
        {"name": "Corvane Mutual Norge", "country": "NO", "location": "LOC-OSL", "currency": "NOK"},
        {"name": "Corvane Mutual Sverige", "country": "SE", "location": "LOC-STO", "currency": "SEK"},
        {"name": "Corvane Mutual Danmark", "country": "DK", "location": "LOC-CPH", "currency": "DKK"},
    ],
    "regulator": NISA,
    "nisa_firm_reference": "NISA-FRN 40417",
    "lines_of_business": ["Motor", "Home", "Commercial Property", "SME Liability"],
    "financials": {
        "fy2025": {
            "gross_written_premium_gbp_m": 2140.0,
            "gross_claims_incurred_gbp_m": 1412.6,
            "claims_outstanding_technical_provisions_gbp_m": 2318.4,
            "ibnr_gbp_m": 611.9,
            "combined_ratio_pct": 98.4,
            "claims_notified": 212400,
            "fraud_referrals": 4812,
            "confirmed_fraud_cases": 1109,
            "fraud_savings_gbp_m": 38.7,
            "fnol_ack_within_2bd_pct": 97.3,
            "avg_settlement_days_motor": 34,
            "avg_settlement_days_home": 51,
        },
        "q3_2026": {"combined_ratio_pct": 97.8, "claims_notified": 55180},
    },
    "reinsurance_treaty_2026": {
        "type": "Per-risk and catastrophe excess of loss", "period": "2026-01-01 to 2026-12-31",
        "retention_gbp_m": 5.0, "limit_gbp_m": 150.0,
        "shares_pct": {"VEN-12": 40, "VEN-13": 35, "other_market": 25},
        "large_loss_notification": "BR-RSV-011 v2: movements above £250,000 notified within 24 hours",
        "summary_file": "LD026"},
    "programme": {
        "name": PROGRAMME,
        "aliases": ["Skerry", "the modernisation programme", "CLARA replacement programme"],
        "purpose": "Replace the CLARA mainframe claims platform with Claims Hub",
        "budget_gbp_m": 48.6,
        "executive_sponsor": "P004",
        "business_case_signed_by": "P002",
        "business_case_date": "2024-11-18",
        "ibm_engagement_start": "2025-01-13",
    },
}


def build_org():
    return {"company": COMPANY, "locations": LOCATIONS, "departments": DEPARTMENTS,
            "teams": TEAMS, "committees": COMMITTEES}


# ---------------------------------------------------------------- people.yaml

def _email(name, domain, override=None):
    if override:
        return override
    n = fold(name).lower().replace(" ", ".").replace("'", "")
    return f"{n}@{domain}"


def _p(pid, name, employer, loc, emp_from, titles, reports, teams, aliases, resp,
       emp_to=None, role_aliases=(), name_history=None, email=None, email_history=None,
       locations=None, github=None, notes=None, phone=None):
    def per(pairs):
        out = []
        for i, (val, frm) in enumerate(pairs):
            to = day_before(pairs[i + 1][1]) if i + 1 < len(pairs) else emp_to
            out.append((val, frm, to))
        return out
    domain = CORVANE_DOMAIN if employer == CORVANE else IBM_DOMAIN if employer == IBM else None
    rec = {
        "id": pid,
        "name": name,
        "aliases": list(aliases),
        "employer": employer,
        "email": email or (_email(name, domain) if domain else None),
        "phone": phone,
        "location": loc,
        "team": per(teams)[-1][0] if teams else None,
        "employment": {"from": emp_from, "to": emp_to},
        "titles": [{"title": t, "from": f, "to": to} for t, f, to in per(titles)],
        "reports_to": [{"manager_id": m, "from": f, "to": to} for m, f, to in per(reports)] if reports else [],
        "teams": [{"team_id": t, "from": f, "to": to} for t, f, to in per(teams)] if teams else [],
        "responsibilities": list(resp),
    }
    if role_aliases:
        rec["role_aliases"] = [{"alias": a, "from": f, "to": t} for a, f, t in role_aliases]
    if name_history:
        rec["name_history"] = name_history
    if email_history:
        rec["email_history"] = email_history
    if locations:
        rec["location_history"] = [{"location": l, "from": f, "to": to} for l, f, to in per(locations)]
    if github:
        rec["github"] = github
    if notes:
        rec["notes"] = notes
    return rec


def _ph(n):
    return f"07700 900{n:03d}"


def build_people():
    C = CORVANE
    P = []
    P.append(_p("P001", "Priya Raman", C, "LOC-LON", "2025-07-01",
                [("Chief Financial Officer", "2025-07-01")], [("P003", "2025-07-01")], [("T01", "2025-07-01")],
                ["P. Raman", "PR", "Priya", "Ms Raman"],
                ["Finance, reserving, actuarial, treasury and payments", "Approves programme budget drawdowns above £500,000",
                 "Signs the quarterly NISA-TP2 technical provisions return"],
                role_aliases=[("the CFO", "2025-07-01", None)], phone=_ph(101),
                notes="Current CFO. Do not confuse with the former CFO Gareth Whitcombe (P002), CFO until 2025-06-30."))
    P.append(_p("P002", "Gareth Whitcombe", C, "LOC-LON", "2019-04-01",
                [("Chief Financial Officer", "2019-04-01")], [("P003", MODEL_START)], [("T01", MODEL_START)],
                ["G. Whitcombe", "GW", "Gareth"],
                ["Finance (until 30 June 2025)", f"Signed the {PROGRAMME} business case on 2024-11-18"],
                emp_to="2025-06-30", role_aliases=[("the CFO", "2019-04-01", "2025-06-30")], phone=_ph(102),
                notes="Former CFO; left Corvane on 2025-06-30. 'The CFO' in documents dated before 2025-07-01 means him."))
    P.append(_p("P003", "Helena Strandberg", C, "LOC-LON", "2021-01-04",
                [("Chief Executive Officer", "2021-01-04")], [(None, "2021-01-04")], [("T01", "2021-01-04")],
                ["H. Strandberg", "HS", "Helena"], ["Group strategy", "Chairs the Executive Committee"],
                role_aliases=[("the CEO", "2021-01-04", None)], phone=_ph(103)))
    P.append(_p("P004", "Duncan Ferrier", C, "LOC-LON", "2017-09-01",
                [("Chief Operating Officer", "2017-09-01")], [("P003", MODEL_START)], [("T01", MODEL_START)],
                ["D. Ferrier", "DF", "Duncan"], ["Operations and claims", f"{PROGRAMME} executive sponsor and Steering Committee chair"],
                role_aliases=[("the COO", "2017-09-01", None)], phone=_ph(104)))
    P.append(_p("P005", "Ingrid Ashby", C, "LOC-LON", "2011-08-15",
                [("Claims Operations Manager – Norway", "2011-08-15"), ("Head of Claims Operations Nordics", "2018-06-01"),
                 ("Claims Director", "2022-03-01")],
                [("P004", MODEL_START)], [("T05", MODEL_START), ("T01", "2022-03-01")],
                ["Ingrid Sørensen", "Ingrid Sorensen", "I. Sørensen", "I. Sorensen", "I. Ashby", "Mrs Ashby", "IS", "IA", "Ingrid"],
                ["Owns the Claims Handling Manual (v7.2 approved 2026-06-30)", "Claims department head",
                 "Approves reserves up to £2,000,000", "Co-approver of fraud rule changes"],
                role_aliases=[("the Claims Director", "2022-03-01", None)],
                name_history=[{"name": "Ingrid Sørensen", "from": None, "to": "2025-08-22"},
                              {"name": "Ingrid Ashby", "from": "2025-08-23", "to": None}],
                email="ingrid.ashby@corvane-mutual.example",
                email_history=[{"email": "ingrid.sorensen@corvane-mutual.example", "from": "2011-08-15", "to": "2025-08-22"},
                               {"email": "ingrid.ashby@corvane-mutual.example", "from": "2025-08-23", "to": None}],
                locations=[("LOC-OSL", "2011-08-15"), ("LOC-LON", "2022-03-01")], phone=_ph(105),
                notes="Name changed on marriage 2025-08-23 (Sørensen -> Ashby). Often written 'Sorensen' (ASCII-folded). "
                      "Referred to as 'the Claims Director' from 2022-03-01."))
    P.append(_p("P006", "Adaeze Nwosu", C, "LOC-LON", "2020-02-03",
                [("Chief Information Officer", "2020-02-03")], [("P003", MODEL_START)], [("T01", MODEL_START)],
                ["A. Nwosu", "AN", "Adaeze"], ["Technology", "Owns PALM policy administration platform"],
                role_aliases=[("the CIO", "2020-02-03", None)], phone=_ph(106)))
    P.append(_p("P007", "Karin Holmberg", C, "LOC-LON", "2017-05-02",
                [("Chief Risk Officer", "2017-05-02")], [("P003", MODEL_START)], [("T01", MODEL_START)],
                ["K. Holmberg", "KH", "Karin"], ["Risk & Compliance", "Line manager of Counter-Fraud & SIU from 2025-09-01"],
                role_aliases=[("the CRO", "2017-05-02", None)], phone=_ph(107)))
    P.append(_p("P008", "Niall Brannigan", C, "LOC-LDS", "2012-02-06",
                [("SIU Manager", "2012-02-06"), ("Head of SIU", "2020-01-01"), ("Head of Counter-Fraud & SIU", "2025-09-01")],
                [("P004", MODEL_START), ("P005", "2022-03-01"), ("P007", "2025-09-01")], [("T11", MODEL_START)],
                ["N. Brannigan", "NB", "Niall"],
                ["Fraud referral process owner", "Approves fraud rules (with the Claims Director)", "Chairs the Claims Fraud Forum",
                 "Business owner of Sentinel"],
                role_aliases=[("Head of SIU", "2020-01-01", "2025-08-31")], phone=_ph(108),
                notes="Re-org 2025-09-01: title and manager changed (Claims Director -> CRO)."))
    P.append(_p("P009", "Lena Kristiansen", C, "LOC-LON", "2019-03-04",
                [("Reserving Manager", "2019-03-04"), ("Head of Reserving", "2025-09-01")],
                [("P010", "2019-03-04"), ("P001", "2025-09-01")], [("T12", "2019-03-04")],
                ["L. Kristiansen", "LK", "Lena"],
                ["Reserving process owner from 2025-09-01", "Chairs the Reserving Committee from 2025-09-01",
                 "Owns the Actuarial Reserving Workbench"], phone=_ph(109),
                notes="Re-org 2025-09-01: title and manager changed (Chief Actuary -> CFO)."))
    P.append(_p("P010", "Sebastian Moreau-Clarke", C, "LOC-LON", "2014-06-02",
                [("Chief Actuary", "2014-06-02")], [("P002", MODEL_START), ("P001", "2025-07-01")], [("T13", MODEL_START)],
                ["S. Moreau-Clarke", "SMC", "Sebastian"],
                ["Reserving process owner until 2025-08-31", "IBNR methodology"], phone=_ph(110)))
    P.append(_p("P011", "Rob Tennant", C, "LOC-LDS", "2008-04-14",
                [("Claims Operations Manager – Leeds", "2008-04-14"), ("Head of Claims Operations UK", "2017-01-01"),
                 ("Head of Claims Operations (Group)", "2025-09-01")],
                [("P004", MODEL_START), ("P005", "2022-03-01")], [("T02", MODEL_START)],
                ["R. Tennant", "RT", "Rob", "Robert Tennant"],
                ["Triage and settlement process owner", "FNOL process owner from 2025-09-01"], phone=_ph(111)))
    P.append(_p("P012", "Mette Dahl", C, "LOC-CPH", "2016-01-11",
                [("Claims Manager – Denmark", "2016-01-11"), ("Head of Claims Operations Nordics", "2022-03-01"),
                 ("Claims Operations Lead – Nordics", "2025-09-01")],
                [("P005", MODEL_START), ("P011", "2025-09-01")], [("T05", MODEL_START)],
                ["M. Dahl", "MD", "Mette"], ["Nordic claims operations"], phone=_ph(112),
                notes="Re-org 2025-09-01: title and manager changed (Claims Director -> Rob Tennant)."))
    P.append(_p("P013", "Freya Lindahl", C, "LOC-STO", "2021-04-01",
                [("Senior Recoveries Manager – Nordics", "2021-04-01"), ("Head of Recoveries & Subrogation", "2025-09-01")],
                [("P005", "2021-04-01"), ("P012", "2022-03-01"), ("P005", "2025-09-01")], [("T05", "2021-04-01"), ("T08", "2025-09-01")],
                ["F. Lindahl", "FL", "Freya"],
                ["Owner of the recovery & subrogation process from 2025-09-01", "Approves recovery write-offs above £10,000",
                 "Owner of SUBTRAK until its retirement (target 2026-12-31)"], phone=_ph(113),
                notes="Re-org 2025-09-01: became Head of Recoveries & Subrogation (Group), reporting to the Claims Director."))
    P.append(_p("P014", "Siobhan Quill", C, "LOC-BRS", "2015-09-07",
                [("Recoveries Handler", "2015-09-07"), ("Recoveries Team Leader", "2019-01-01"),
                 ("Acting Recoveries Manager", "2025-01-01"), ("Recoveries Team Leader – UK", "2025-09-01")],
                [("P015", MODEL_START), ("P011", "2025-01-01"), ("P013", "2025-09-01")], [("T08", MODEL_START)],
                ["S. Quill", "SQ", "Siobhan"],
                ["Acting owner of the recovery & subrogation process 2025-01-01 to 2025-08-31", "UK recoveries team"], phone=_ph(114),
                notes="Re-org 2025-09-01: title and manager changed."))
    P.append(_p("P015", "Martin Calloway", C, "LOC-BRS", "2016-03-01",
                [("Recoveries Manager", "2016-03-01")], [("P011", MODEL_START)], [("T08", MODEL_START)],
                ["M. Calloway", "MC", "Martin"],
                ["Owner of the recovery & subrogation process until 2024-12-31"], emp_to="2024-12-31", phone=_ph(115),
                notes="Left Corvane 2024-12-31. Still shown as subrogation owner on the stale 2024 org chart."))
    P.append(_p("P016", "Graham Pocock", C, "LOC-LDS", "2001-10-01",
                [("Mainframe Developer", "2001-10-01"), ("CLARA Platform Manager", "2010-01-01"),
                 ("Head of Legacy Claims Platforms", "2025-09-01")],
                [("P006", MODEL_START), ("P032", "2025-09-01")], [("T20", MODEL_START)],
                ["G. Pocock", "GP", "Graham"], ["CLARA system owner", "Legacy decommissioning plan"], phone=_ph(116),
                notes="Re-org 2025-09-01: title and manager changed (CIO -> Head of Technology Delivery)."))
    P.append(_p("P017", "Aisha Siddiqui", C, "LOC-LON", "2025-01-13",
                [("Claims Hub Product Owner", "2025-01-13"), ("Head of Claims Hub Product", "2025-09-01")],
                [("P006", "2025-01-13"), ("P005", "2025-09-01")], [("T21", "2025-01-13")],
                ["A. Siddiqui", "AS", "Aisha"], ["Claims Hub system owner", "Product backlog (Jira project CHUB)"], phone=_ph(117),
                notes="Re-org 2025-09-01: title and manager changed (CIO -> Claims Director)."))
    P.append(_p("P018", "Tomasz Wójcik", C, "LOC-LON", "2018-07-02",
                [("Enterprise Architect", "2018-07-02")], [("P006", MODEL_START)], [("T24", MODEL_START)],
                ["Tomasz Wojcik", "T. Wójcik", "T. Wojcik", "TW", "Tomasz"], ["Chairs the Design Authority", "ADR register"],
                github="twojcik", phone=_ph(118)))
    P.append(_p("P019", "Morag Duthie", C, "LOC-GLA", "2018-05-14",
                [("Data Protection Officer", "2018-05-14")], [("P007", MODEL_START)], [("T19", MODEL_START)],
                ["M. Duthie", "Morag"], ["Data protection", "Claims data retention policy"],
                role_aliases=[("the DPO", "2018-05-14", None)], phone=_ph(119)))
    P.append(_p("P020", "Bjørn Aasheim", C, "LOC-OSL", "2017-02-01",
                [("Regulatory Reporting Manager", "2017-02-01")], [("P021", MODEL_START)], [("T15", MODEL_START)],
                ["Bjorn Aasheim", "B. Aasheim", "BA", "Bjørn", "Bjorn"],
                ["NISA returns: TP2, FR1, CT1 and the annual claims & reserving filing", "Owner of NISA Reporting Hub"], phone="+47 555 01 020"))
    P.append(_p("P021", "Hamish Gilchrist", C, "LOC-LON", "2013-11-04",
                [("Financial Controller", "2013-11-04")], [("P002", MODEL_START), ("P001", "2025-07-01")], [("T14", MODEL_START)],
                ["H. Gilchrist", "HG", "Hamish"], ["Group Ledger owner", "Month-end close"], phone=_ph(121)))
    P.append(_p("P022", "Callum Fairbairn", C, "LOC-LDS", "2014-05-19",
                [("Claims Handler", "2014-05-19"), ("Motor Claims Team Leader", "2019-04-01")],
                [("P011", MODEL_START)], [("T02", "2014-05-19"), ("T03", "2019-04-01")],
                ["C. Fairbairn", "CF", "Callum"], ["UK motor claims team (Leeds)", "Approves payments up to the Team Leader limit"],
                email="callum.fairbairn@corvane-mutual.example", phone=_ph(122),
                notes="NAMESAKE TRAP: a different Callum Fairbairn (P051) is IBM's Data Migration Lead in London."))
    P.append(_p("P023", "Keith Barraclough", C, "LOC-LDS", "1996-03-11",
                [("Senior Mainframe Developer", "1996-03-11")], [("P016", MODEL_START)], [("T20", MODEL_START)],
                ["K. Barraclough", "KB", "Keith"], ["CLARA reserve and fraud programs", "COBOL code owner"],
                github="kbarraclough", phone=_ph(123)))
    P.append(_p("P024", "Pauline Ashworth", C, "LOC-LDS", "2004-09-06",
                [("Mainframe Developer", "2004-09-06")], [("P016", MODEL_START)], [("T20", MODEL_START)],
                ["P. Ashworth", "Pauline"], ["CLARA fraud and settlement programs", "T_PARAM maintenance"],
                github="pashworth", phone=_ph(124)))
    P.append(_p("P025", "Derek Ollerton", C, "LOC-LDS", "2002-01-14",
                [("DB2 Database Administrator", "2002-01-14")], [("P016", MODEL_START)], [("T20", MODEL_START)],
                ["D. Ollerton", "DO", "Derek"], ["DB2 subsystem DB2P", "CLARA data dictionary"], github="dollerton", phone=_ph(125)))
    P.append(_p("P026", "Sunita Vaghela", C, "LOC-LDS", "2010-06-21",
                [("Batch Operations Lead", "2010-06-21")], [("P016", MODEL_START)], [("T25", MODEL_START)],
                ["S. Vaghela", "SV", "Sunita"], ["JCL schedule", "CLARA operations runbook"], phone=_ph(126)))
    P.append(_p("P027", "Oskar Lindgren", C, "LOC-STO", "2019-10-01",
                [("Senior Fraud Analyst", "2019-10-01")], [("P008", "2019-10-01")], [("T11", "2019-10-01")],
                ["O. Lindgren", "OL", "Oskar"], ["Sentinel model owner (model SNT-4.2)", "Threshold calibration"],
                phone="+46 555 01 027"))
    P.append(_p("P028", "Rachel Dunmore", C, "LOC-LDS", "2014-02-03",
                [("SIU Investigations Manager (UK)", "2014-02-03")], [("P008", MODEL_START)], [("T11", MODEL_START)],
                ["R. Dunmore", "RD", "Rachel"], ["SIU investigations", "Approves customer-notice deferrals (tipping-off)",
                                                  "Owner of SIU Case Manager"], phone=_ph(128)))
    P.append(_p("P029", "Ewan Strachan", C, "LOC-GLA", "2012-08-20",
                [("Contact Centre Manager", "2012-08-20")], [("P011", MODEL_START)], [("T10", MODEL_START)],
                ["E. Strachan", "ES", "Ewan"], ["FNOL process owner until 2025-08-31", "Harbour CRM business owner"], phone=_ph(129)))
    P.append(_p("P030", "Kirsty Mowbray", C, "LOC-LON", "2016-10-03",
                [("Major & Complex Loss Manager", "2016-10-03")], [("P004", MODEL_START), ("P005", "2022-03-01")], [("T09", MODEL_START)],
                ["K. Mowbray", "Kirsty"], ["Tier-3 claims handling"], phone=_ph(130)))
    P.append(_p("P031", "Henrik Vestergaard", C, "LOC-CPH", "2018-01-08",
                [("Integration Platform Lead", "2018-01-08")], [("P032", MODEL_START)], [("T22", MODEL_START)],
                ["H. Vestergaard", "HV", "Henrik"], ["MQ Backbone and Event Streaming Platform", "Interface catalogue owner",
                                                      "Owner of CLX-IF-042 and CLX-IF-049"],
                github="hvestergaard", phone="+45 555 01 031"))
    P.append(_p("P032", "Neil Haworth", C, "LOC-LON", "2019-09-02",
                [("Head of Technology Delivery", "2019-09-02")], [("P006", MODEL_START)], [("T31", MODEL_START)],
                ["N. Haworth", "NH", "Neil"], ["Chairs the CAB", "Line manager of Claims Hub squads"], phone=_ph(132)))
    P.append(_p("P033", "Imran Talwar", C, "LOC-LDS", "2013-04-08",
                [("Head of Claims Assessment (UK)", "2013-04-08")], [("P011", MODEL_START)], [("T06", MODEL_START)],
                ["I. Talwar", "Imran"], ["Assessment process owner", "Vendor assessor panel", "Assessor Portal owner"], phone=_ph(133)))
    P.append(_p("P034", "Astrid Nygaard", C, "LOC-OSL", "2017-08-14",
                [("Claims Assessment Lead – Nordics", "2017-08-14")], [("P012", MODEL_START)], [("T07", MODEL_START)],
                ["A. Nygaard", "Astrid"], ["Nordic Claims Assessors (skadetakstmenn)"], phone="+47 555 01 034"))
    P.append(_p("P035", "Alun Prothero", C, "LOC-BRS", "2011-01-10",
                [("Payments Operations Manager", "2011-01-10")], [("P021", MODEL_START)], [("T16", MODEL_START)],
                ["A. Prothero", "Alun"], ["Corvane Payments Gateway business owner"], phone=_ph(135)))
    P.append(_p("P036", "Maja Holm", C, "LOC-CPH", "2020-11-02",
                [("Data & Analytics Lead", "2020-11-02")], [("P006", MODEL_START)], [("T23", MODEL_START)],
                ["M. Holm", "Maja"], ["Claims Data Warehouse owner", "Owner of CLX-IF-044 and CLX-IF-058 data quality"], phone="+45 555 01 036"))
    P.append(_p("P037", "Ruth Okafor", C, "LOC-LON", "2019-01-07",
                [("Compliance Manager – Conduct & Counter-Fraud", "2019-01-07")], [("P007", MODEL_START)], [("T18", MODEL_START)],
                ["R. Okafor", "RO", "Ruth"], ["NISA Circular 2026/04 implementation lead", "NISA-FR1 return sign-off", "WatchScreen owner"], phone=_ph(137)))
    P.append(_p("P038", "Per Øverland", C, "LOC-OSL", "2015-03-02",
                [("Reinsurance Manager", "2015-03-02")], [("P002", MODEL_START), ("P001", "2025-07-01")], [("T17", MODEL_START)],
                ["Per Overland", "P. Øverland", "P. Overland", "Per"], ["ReCede owner", "Treaty and bordereaux"], phone="+47 555 01 038"))
    P.append(_p("P039", "Gemma Thornbury", C, "LOC-LDS", "2017-06-05",
                [("Property Claims Team Leader", "2017-06-05")], [("P011", MODEL_START)], [("T04", MODEL_START)],
                ["G. Thornbury", "Gemma"], ["UK property claims team"], phone=_ph(139)))
    P.append(_p("P040", "Sofie Bak", C, "LOC-CPH", "2025-02-03",
                [("Engineering Lead – Intake & Triage Squad", "2025-02-03")], [("P032", "2025-02-03")], [("T27", "2025-02-03")],
                ["S. Bak", "Sofie"], ["fnol-intake-svc, triage-svc, assessment-svc, claim-core-svc, notification-svc"],
                github="sbak", phone="+45 555 01 040"))
    P.append(_p("P041", "Daniel Achebe", C, "LOC-LON", "2022-05-09",
                [("Senior Java Developer", "2022-05-09"), ("Engineering Lead – Reserve & Finance Squad", "2025-02-03")],
                [("P032", "2022-05-09")], [("T31", "2022-05-09"), ("T28", "2025-02-03")],
                ["D. Achebe", "DA", "Daniel"], ["reserve-engine, gl-posting-svc, reporting-feed-svc"], github="dachebe", phone=_ph(141)))
    P.append(_p("P042", "Linnea Sjöberg", C, "LOC-STO", "2023-03-01",
                [("Java Developer", "2023-03-01"), ("Engineering Lead – Fraud & Settlement Squad", "2025-02-03")],
                [("P032", "2023-03-01")], [("T31", "2023-03-01"), ("T29", "2025-02-03")],
                ["Linnea Sjoberg", "L. Sjöberg", "L. Sjoberg", "LS", "Linnea"],
                ["fraud-referral-svc, settlement-svc, payment-orchestrator"], github="lsjoberg", phone="+46 555 01 042"))
    P.append(_p("P043", "Tariq Hussain", C, "LOC-LON", "2021-09-13",
                [("Senior Java Developer", "2021-09-13"), ("Engineering Lead – Recoveries & Documents Squad", "2026-11-01")],
                [("P032", "2021-09-13"), ("P042", "2025-02-03"), ("P032", "2026-11-01")],
                [("T31", "2021-09-13"), ("T29", "2025-02-03"), ("T30", "2026-11-01")],
                ["T. Hussain", "TH", "Tariq"], ["Leads the Recoveries & Documents squad from 2026-11-01"], github="thussain", phone=_ph(143),
                notes="Title and manager changed 2026-11-01 when the Recoveries & Documents squad was formed."))
    P.append(_p("P044", "Beth Kilbride", C, "LOC-LDS", "2020-09-14",
                [("Claims Handler – Motor", "2020-09-14")], [("P022", "2020-09-14")], [("T03", "2020-09-14")],
                ["B. Kilbride", "Beth"], ["UK motor claims handling"], phone=_ph(144)))
    P.append(_p("P045", "Mohammed Saleem", C, "LOC-LDS", "2018-02-19",
                [("Claims Assessor", "2018-02-19")], [("P033", MODEL_START)], [("T06", MODEL_START)],
                ["M. Saleem", "Mo Saleem", "Mohammed"], ["Internal Claims Assessor (UK property)"], phone=_ph(145),
                notes="Often called 'our loss adjuster' or 'the assessor' in emails; canonical role is Claims Assessor."))
    P.append(_p("P046", "Karl Eriksen", C, "LOC-OSL", "2019-05-06",
                [("Claims Assessor", "2019-05-06")], [("P034", "2019-05-06")], [("T07", "2019-05-06")],
                ["K. Eriksen", "Karl"], ["Internal Claims Assessor (Norway, motor and home)"], phone="+47 555 01 046",
                notes="Norwegian documents call the role 'skadetakstmann'."))

    # IBM team
    I = IBM
    P.append(_p("P047", "Victoria Ashcombe", I, "EXT-IBM-LON", "2024-09-02",
                [("Engagement Partner", "2024-09-02")], [(None, "2024-09-02")], [("T26", "2024-09-02")],
                ["V. Ashcombe", "VA", "Victoria"], ["IBM engagement lead for " + PROGRAMME], phone=_ph(147)))
    P.append(_p("P048", "Arjun Kesavan", I, "EXT-IBM-LON", "2025-01-13",
                [("Programme Delivery Lead", "2025-01-13")], [("P047", "2025-01-13")], [("T26", "2025-01-13")],
                ["A. Kesavan", "AK", "Arjun"], ["Programme plan, cut-over planning", "IBM team lead"], phone=_ph(148)))
    P.append(_p("P049", "Elin Fosse", I, "EXT-IBM-OSL", "2025-01-13",
                [("Lead Solution Architect", "2025-01-13")], [("P048", "2025-01-13")], [("T26", "2025-01-13")],
                ["E. Fosse", "EF", "Elin"], ["Claims Hub target architecture"], github="efosse-ibm", phone="+47 555 01 049"))
    P.append(_p("P050", "Marcus Oduya", I, "EXT-IBM-LON", "2025-01-13",
                [("Integration Architect", "2025-01-13")], [("P049", "2025-01-13")], [("T26", "2025-01-13")],
                ["M. Oduya", "MO", "Marcus"], ["Interface design, CLX-IF-049 bridge design"], github="moduya-ibm", phone=_ph(150)))
    P.append(_p("P051", "Callum Fairbairn", I, "EXT-IBM-LON", "2025-01-13",
                [("Data Migration Lead", "2025-01-13")], [("P048", "2025-01-13")], [("T26", "2025-01-13")],
                ["C. Fairbairn", "Callum (IBM)", "CF"], ["Data migration strategy and waves", "Reconciliation of migrated reserves"],
                email="callum.fairbairn@ibm-consulting.example", github="cfairbairn-ibm", phone=_ph(151),
                notes="NAMESAKE TRAP: not the Corvane Motor Claims Team Leader Callum Fairbairn (P022) in Leeds."))
    P.append(_p("P052", "Gordon Sproat", I, "LOC-LDS", "2025-01-13",
                [("Mainframe Modernisation SME", "2025-01-13")], [("P049", "2025-01-13")], [("T26", "2025-01-13")],
                ["G. Sproat", "Gordon"], ["COBOL program analysis, CRUD matrix"], phone=_ph(152)))
    P.append(_p("P053", "Nadia Petrovic", I, "EXT-IBM-LON", "2025-01-13",
                [("Java Technical Lead", "2025-01-13")], [("P049", "2025-01-13")], [("T26", "2025-01-13")],
                ["N. Petrovic", "NP", "Nadia"], ["Claims Hub coding standards", "reserve-engine design"], github="npetrovic-ibm", phone=_ph(153)))
    P.append(_p("P054", "Hannah Lyle", I, "EXT-IBM-LON", "2025-01-13",
                [("Business Analyst – Claims", "2025-01-13")], [("P048", "2025-01-13")], [("T26", "2025-01-13")],
                ["H. Lyle", "HL", "Hannah"], ["Business requirements (fraud-referral BRD)"], phone=_ph(154)))

    # Regulator and vendor contacts (external, no reporting lines modelled)
    P.append(_p("P055", "Imogen Thackray", NISA, "EXT-NISA-LON", "2016-01-04",
                [("Senior Supervisor – Insurance Conduct", "2016-01-04")], [], [],
                ["I. Thackray", "Imogen"], ["NISA supervisor for Corvane Mutual"], email="imogen.thackray@nisa.example", phone=_ph(155)))
    P.append(_p("P056", "Petter Ulvestad", NISA, "EXT-NISA-LON", "2019-08-01",
                [("Policy Lead – Counter-Fraud", "2019-08-01")], [], [],
                ["P. Ulvestad", "Petter"], ["Author of NISA Circular 2026/04"], email="petter.ulvestad@nisa.example", phone="+47 555 01 056"))
    P.append(_p("P057", "Colin Rudd", "VEN-01", "EXT-VEN-MAN", "2012-04-02",
                [("Client Director", "2012-04-02")], [], [],
                ["C. Rudd", "Colin"], ["Corvane account at Brackenfield Loss Adjusting"], email="colin.rudd@brackenfield-la.example", phone=_ph(157)))
    P.append(_p("P058", "Sigrid Nyhus", "VEN-02", "EXT-VEN-GOT", "2015-09-01",
                [("Regional Manager – Norway & Sweden", "2015-09-01")], [], [],
                ["S. Nyhus", "Sigrid"], ["Corvane account at Norrvik Skadetaxering"], email="sigrid.nyhus@norrvik.example", phone="+46 555 01 058"))
    P.append(_p("P059", "Declan Furey", "VEN-10", "EXT-VEN-LDS", "2018-03-05",
                [("SIU Partner Lead", "2018-03-05")], [], [],
                ["D. Furey", "Declan"], ["Surveillance and interview services for Corvane SIU"], email="declan.furey@greyfold.example", phone=_ph(159)))
    P.append(_p("P060", "Edward Pargeter", "VEN-07", "EXT-VEN-BHM", "2010-09-01",
                [("Partner – Recoveries", "2010-09-01")], [], [],
                ["E. Pargeter", "Ed Pargeter", "Edward"], ["Subrogation litigation for Corvane"], email="edward.pargeter@quarryhill.example", phone=_ph(160)))
    clara_ids = {"P009": "LKRIS01", "P011": "RTENN01", "P013": "FLIND01", "P014": "SQUIL01", "P022": "CFAIR01", "P027": "OLIND01",
                 "P028": "RDUNM01", "P030": "KMOWB01", "P033": "ITALW01", "P034": "ANYGA01", "P039": "GTHOR01", "P044": "BKILB01",
                 "P045": "MSALE01", "P046": "KERIK01", "P024": "PASHW01", "P023": "KBARR01"}
    for rec in P:
        if rec["id"] in clara_ids:
            rec["clara_user_id"] = clara_ids[rec["id"]]
    return P

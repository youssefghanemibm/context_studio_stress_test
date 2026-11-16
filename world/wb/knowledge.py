"""glossary.yaml and names_denylist.yaml."""
from __future__ import annotations

FAM_ALL = ["LD", "VS", "ST", "TX", "CODE"]


def g(gid, canonical, definition, variants, schema_term=None, refs=()):
    return {"id": gid, "canonical": canonical, "schema_term": schema_term or canonical, "definition": definition,
            "variants": [{"term": t, "families": f, "note": n} for t, f, n in variants], "refs": list(refs)}


def build_glossary():
    G = [
        g("G-001", "Claims Assessor", "Person (internal employee or panel vendor) who inspects or desk-assesses a loss and reports an estimate and cover view.",
          [("loss adjuster", ["LD", "TX"], "LD001 uses it for external (vendor) Claims Assessors; emails use it loosely for anyone assessing"),
           ("adjuster", ["TX"], "transcripts and chat"),
           ("assessor", ["VS", "TX"], "slides and screenshots"),
           ("claims adjuster", ["TX"], "occasional email usage"),
           ("skadetakstmann", ["LD", "TX"], "Norwegian documents (LD011, Nordic emails)"),
           ("besiktningsman", ["LD"], "Swedish wording LD008"),
           ("Adjuster Extranet", ["LD", "VS"], "old name of the Assessor Portal (renamed 2025-09-01)")],
          refs=["SYS17", "T06", "T07", "VEN-01", "VEN-02"]),
        g("G-002", "Fraud Referral", "Referral of a claim to the Counter-Fraud & SIU team for investigation.",
          [("SIU referral", ["VS", "TX"], ""), ("referral to SIU", ["LD"], "LD001 §28"), ("fraud referral", ["ST", "CODE"], "table CLR.T_FRAUD_REFERRAL"),
           ("referral", ["TX"], "")], refs=["BR-FRD-031", "CLR.T_FRAUD_REFERRAL"]),
        g("G-003", "Reserve", "Case reserve: the estimated outstanding cost of a claim, per reserve type.",
          [("case reserve", ["LD"], ""), ("case estimate", ["TX"], ""), ("outstanding", ["ST"], "CSV column reserve_outstanding"),
           ("RSV", ["CODE"], "COBOL/DB2 prefix (CLR.T_RESERVE, RSVREC)"), ("reserve table", ["TX", "VS"], "means CLR.T_RESERVE")],
          refs=["CLR.T_RESERVE", "reserve.reserve"]),
        g("G-004", "Subrogation", "Recovery of claim outlay from a responsible third party or its insurer.",
          [("sub-ro", ["TX"], ""), ("subro", ["TX", "CODE"], "CODE paths and chat"), ("recovery", ["VS", "LD"], "process diagrams use 'Recovery & Subrogation'"),
           ("recoveries", ["LD", "TX"], ""), ("regress", ["LD", "TX"], "Nordic term (regressfordring)")], refs=["S7", "SYS24", "recovery-svc"]),
        g("G-005", "First Notice of Loss", "The first notification of a claim by any channel.",
          [("FNOL", FAM_ALL, "universal abbreviation"), ("notification of loss", ["LD"], "policy wordings"), ("first notification", ["LD"], ""),
           ("skademelding", ["LD"], "Norwegian wordings")], refs=["S1"]),
        g("G-006", "Claim Type", "The peril or cause of loss classifying a claim (e.g. Escape of Water).",
          [("peril", ["LD", "CODE"], "CLARA column PERIL_CD; manual"), ("cause of loss", ["LD"], "policy wordings"), ("loss type", ["VS"], "dashboards")],
          refs=["claim_types.yaml"]),
        g("G-007", "Claims Handler", "Employee who manages a claim day to day.",
          [("claim handler", ["TX", "VS"], ""), ("case handler", ["LD"], "older manual v6.1"), ("handler", ["ST", "TX"], "handler_ref column")]),
        g("G-008", "Tier-3 Claim", "A claim meeting the Tier-3 definition in BR-TRI-003 (v3 from 2025-01-01).",
          [("T3", ["TX", "CODE"], ""), ("complex claim", ["TX"], ""), ("major & complex loss", ["VS"], "routing destination, not the definition")],
          refs=["BR-TRI-003"]),
        g("G-009", "Fraud Score", "Sentinel score from 0 to 100.",
          [("Sentinel score", ["LD", "VS", "ST"], ""), ("FRAUDNET score", ["LD", "TX"], "before 2025-03-01"), ("risk score", ["TX"], ""),
           ("SNT score", ["CODE"], "")], refs=["SYS03"]),
        g("G-010", "Excess", "The amount the policyholder bears on each claim.",
          [("deductible", ["TX"], ""), ("egenandel", ["LD", "ST"], "Norway"), ("självrisk", ["LD", "ST"], "Sweden"), ("selvrisiko", ["LD", "ST"], "Denmark")]),
        g("G-011", "Policyholder", "Holder of the policy (a member of the mutual).",
          [("insured", ["LD"], ""), ("member", ["LD", "TX"], "mutual terminology"), ("customer", ["VS", "TX"], "")]),
        g("G-012", "Counter-Fraud & SIU", "The Special Investigations Unit (renamed Counter-Fraud & SIU on 2025-09-01).",
          [("SIU", FAM_ALL, ""), ("Special Investigations Unit", ["LD"], "name until 2025-08-31"), ("counter-fraud team", ["TX"], "")], refs=["T11"]),
        g("G-013", "Reserve Movement", "A change to a reserve, recorded in CLR.T_RESERVE_MOVEMENT / reserve.reserve_movement.",
          [("reserve change", ["TX"], ""), ("reserve adjustment", ["LD"], ""), ("movement", ["ST", "CODE"], "")], refs=["CLR.T_RESERVE_MOVEMENT"]),
        g("G-014", "Incurred", "Paid to date plus outstanding reserve.", [("incurred cost", ["LD"], ""), ("total incurred", ["ST"], "")]),
        g("G-015", "Large Loss Notification Threshold", "£250,000 reserve movement threshold for notifying Reinsurance (BR-RSV-011 v2).",
          [("LLNT", ["LD", "TX"], "defined in LD001 §2.6"), ("large loss limit", ["TX"], "")], refs=["BR-RSV-011"]),
        g("G-016", "Technical Provisions", "Claims outstanding provisions reported to NISA in the TP2 return.",
          [("TPs", ["TX"], ""), ("claims outstanding provisions", ["LD"], "")], refs=["NISA-TP2"]),
        g("G-017", "Bordereau", "Periodic listing of claims ceded to reinsurers.", [("bordereaux", ["LD", "TX"], "plural"), ("bdx", ["TX"], "")], refs=["CLX-IF-055"]),
        g("G-018", "Settlement", "Agreement and payment of the claim.", [("claim payment", ["TX"], ""), ("indemnity payment", ["LD"], "")], refs=["S6"]),
        g("G-019", "Claims Hub", "The target claims platform.", [("CHUB", ["TX", "CODE"], "Jira key"), ("the Hub", ["TX"], "")], refs=["SYS02"]),
        g("G-020", "CLARA", "Claims Ledger And Reserve Application (legacy mainframe).",
          [("the ledger", ["TX"], ""), ("CLR", ["CODE", "ST"], "schema and program prefix"), ("Claims Ledger", ["LD"], ""),
           ("the mainframe", ["TX"], "")], refs=["SYS01"]),
        g("G-021", "Customer Referral Notice", "Written notice to the customer that a claim is subject to additional checks (BR-FRD-032).",
          [("fraud notice", ["TX", "CODE"], ""), ("referral notice", ["LD", "VS"], ""), ("notice of additional checks", ["LD"], "Circular wording")],
          refs=["BR-FRD-032", "CLR.T_FRAUD_NOTIFICATION"]),
        g("G-022", "Salvage", "Disposal of damaged property (mainly total-loss vehicles) to recover value.",
          [("salvage disposal", ["LD"], ""), ("write-off category", ["TX"], "salvage categories A/B/S/N")], refs=["VEN-09"]),
        g("G-023", "Recovery & Subrogation Process Owner", "Accountable owner of process stage S7.",
          [("Recoveries Manager", ["VS", "LD"], "title of the owner until 2024-12-31 (stale on the 2024 org chart)"),
           ("Head of Recoveries & Subrogation", ["LD", "VS", "ST"], "title of the owner from 2025-09-01")], refs=["S7", "P013"]),
    ]
    return {"terms": G}


DENY = [
    # UK insurers and brands
    "Aviva", "Admiral", "Direct Line", "Churchill Insurance", "Green Flag", "RSA Insurance", "Royal & Sun Alliance", "Allianz", "AXA",
    "Zurich Insurance", "Liverpool Victoria", "Ageas", "Hastings Direct", "esure", "Sheilas' Wheels", "NFU Mutual", "Ecclesiastical Insurance",
    "Hiscox", "Beazley", "Legal & General", "Prudential plc", "Saga plc", "Covea", "Markerstudy", "Lloyd's of London", "QBE", "Chubb",
    "AIG", "Tokio Marine", "Sompo", "Swiss Re", "Munich Re", "Hannover Re", "SCOR", "Arch Insurance", "Markel", "Travelers",
    "Royal London", "Aegon", "Phoenix Group", "Co-op Insurance", "Tesco Bank", "Sainsbury's Bank", "LV= ", "Marsh McLennan", "Aon",
    "Willis Towers Watson", "Arthur J. Gallagher",
    # Nordic insurers and banks
    "Gjensidige", "Tryg", "If P&C", "If Skadeförsäkring", "Länsförsäkringar", "Folksam", "Trygg-Hansa", "Topdanmark", "Alm. Brand", "Codan",
    "Fennia", "LocalTapiola", "Pohjola", "OP Financial", "Storebrand", "Fremtind", "KLP", "SpareBank 1", "DNB", "Nordea", "Danske Bank",
    "Handelsbanken", "Swedbank", "SEB", "Danica", "Sampo", "Moderna Försäkringar", "Protector Forsikring", "Frende", "Eika",
    # regulators and industry bodies
    "FCA", "Financial Conduct Authority", "PRA", "Prudential Regulation Authority", "Bank of England", "Finanstilsynet", "Finansinspektionen",
    "Finanssivalvonta", "EIOPA", "Financial Ombudsman Service", "Association of British Insurers", "Insurance Fraud Bureau",
    "Motor Insurers' Bureau", "Claims and Underwriting Exchange", "DVLA",
    # loss adjusters, law firms, claims services
    "Crawford & Company", "Crawford", "Sedgwick", "McLarens", "Cunningham Lindsey", "Charles Taylor", "Davies Group", "Questgates",
    "Woodgate and Clark", "Kennedys Law", "Clyde & Co", "DAC Beachcroft", "Keoghs", "Weightmans", "Horwich Farrelly", "Gallagher Bassett",
    "Copart", "DWF Group",
    # UK banks
    "Barclays", "HSBC", "Lloyds Bank", "NatWest", "Santander", "Metro Bank",
    # real product names that must not leak into the corpus
    "Guidewire", "Endevor", "Control-M", "FileNet",
]


def build_denylist():
    entries = []
    for name in DENY:
        kind = "company"
        if name in ("FCA", "Financial Conduct Authority", "PRA", "Prudential Regulation Authority", "Bank of England", "Finanstilsynet",
                    "Finansinspektionen", "Finanssivalvonta", "EIOPA", "Financial Ombudsman Service", "DVLA"):
            kind = "regulator"
        elif name in ("Association of British Insurers", "Insurance Fraud Bureau", "Motor Insurers' Bureau", "Claims and Underwriting Exchange"):
            kind = "industry_body"
        elif name in ("Guidewire", "Endevor", "Control-M", "FileNet"):
            kind = "product"
        entries.append({"name": name.strip(), "kind": kind, "match": "word_boundary_case_insensitive"})
    checks = [
        {"name": "Corvane", "result": "no matching insurer found (web spot check 2026-11-15; results only showed the unrelated 'Corvus Insurance')"},
        {"name": "Brackenfield Loss Adjusting", "result": "no matching loss adjuster found (web spot check 2026-11-15)"},
        {"name": "Programme Skerry", "result": "no matching programme or company found (web spot check 2026-11-15)"},
        {"name": "Greyfold Investigations / Salvanta Salvage / Quarryhill Solicitors", "result": "no matches found (web spot check 2026-11-15)"},
    ]
    return {"entries": entries,
            "notes": "The verifier greps every corpus file for these names (case-insensitive, word boundaries). 'LV= ' is matched literally. "
                     "Generic technology names (IBM z/OS, CICS, DB2, MQ, Java, Spring, OpenShift, Kafka, Terraform, PostgreSQL) are allowed.",
            "invented_name_checks": checks}

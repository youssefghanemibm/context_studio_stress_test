"""Image-led DOCX builders VS036-VS039."""
from __future__ import annotations

from generators.common import util

from . import charts, core
from .core import (AMBER, BLUE_L, GREEN, GREY_L, GRID, INK, INK2, LINE, MUTED, NAVY, NAVY2, PURPLE, RED, TEAL, WHITE,
                   Canvas, fmt_date_long, fmt_date_short)
from .ctx import (W, adate, asof_names, guard, minus_days, name, out_path, placement, program_exists, rel, sysname,
                  table_exists, team_name, title)
from .diagrams import Diagram, ERD, SchematicMap, table_image
from .facts import Facts, arrow_spec, chart_spec, placement_spec, spec
from .screens import G_BG, G_CYAN, G_GREEN, G_RED, G_WHITE, G_YELLOW, green_screen
from .skeleton import approval, glossary, section, start_doc, versions_for


# ==========================================================================================
# VS036 CLARA Screen Guide (2023-09-11, P024)
# ==========================================================================================
SAMPLE = {
    "CLRM010": {"POLICY-NO": "MU90004417", "LOSS-DATE": "2023-09-08", "PERIL": "COL COLLISION",
                "CHANNEL": "PH TELEPHONE", "LOSS-DESC": "REAR-END AT LIGHTS", "CALLER-PHONE": "07700900417"},
    "CLRM015": {"POLICY-NO": "MU90004417", "PH-NAME": "TRAINEE", "COVER-START": "2023-03-01",
                "COVER-END": "2024-02-29", "EXCESS": "SEE WORDING"},
    "CLRM110": {"CLAIM-ID": "UK2023904417", "TIER": "2", "SCORE": "041", "ROUTE": "SPECIALIST", "FASTTRACK": "N"},
    "CLRM310": {"CLAIM-ID": "UK2023904417", "RSV-TYPE": "ID INDEMNITY", "CURRENCY": "GBP", "RSV-AMT": "6500.00",
                "AUTH-LEVEL": "CH"},
    "CLRM320": {"CLAIM-ID": "UK2023904417", "RSV-ID": "4418762", "OLD-AMT": "6500.00", "NEW-AMT": "7250.00",
                "REASON": "REVISED REPAIR ESTIMATE", "NEXT-REVIEW": "2023-10-11"},
    "CLRM330": {"CLAIM-ID": "UK2023904417", "RSV-ID": "4418762", "OUTSTANDING": "7250.00", "PAID-TD": "0.00",
                "GBP-EQUIV": "7250.00"},
    "CLRM410": {"CLAIM-ID": "UK2023904431", "SCORE": "074", "THRESHOLD": "070", "TIER": "2", "REASON": "PRSC",
                "NOTICE-DUE": ""},
    "CLRM620": {"CASE-ID": "SB23000417", "DEMAND-AMT": "2140.00", "SOLICITOR": "", "LIMITATION-DATE": "2028-09"},
}
MESSAGES = {
    "CLRM010": "ENTER LOSS DETAILS AND PRESS ENTER TO CREATE THE CLAIM",
    "CLRM015": "POLICY FOUND - PF3 TO RETURN TO FNOL CAPTURE",
    "CLRM110": "REVIEW TIER AND ROUTE, PRESS ENTER TO CONFIRM",
    "CLRM310": "INITIAL RESERVE ACCEPTED",
    "CLRM320": "ENTER NEW AMOUNT AND REASON, PRESS ENTER TO UPDATE",
    "CLRM330": "ENQUIRY ONLY - NO UPDATE ALLOWED",
    "CLRM410": "FRAUDNET SCORE AT OR ABOVE THRESHOLD - REFER TO SIU",
    "CLRM620": "DEMAND RECORDED - DIARY SET",
}


def _map_screen(mapid: str, d: str, user: str = "PASHW01") -> bytes:
    m = W.bms_maps[mapid]
    cells = [(1, 2, m["map"], G_CYAN), (1, 26, f"CLARA - {m['title'].upper()}", G_WHITE), (1, 74, m["transaction"], G_CYAN),
             (2, 2, m["program"], G_CYAN), (2, 26, f"{d}  10:42:17", G_CYAN), (2, 66, f"USER {user}", G_CYAN),
             (3, 2, "-" * 78, G_GREEN)]
    und = []
    for f in m["fields"]:
        lab = f"{f['name']:<15} :"
        cells.append((f["row"], 2, lab, G_GREEN))
        val = SAMPLE.get(mapid, {}).get(f["name"], "")
        col = G_WHITE if "UNPROT" in f["attr"] else G_YELLOW
        cells.append((f["row"], f["col"], val[: max(f["length"], len(val))], col))
        if "UNPROT" in f["attr"]:
            und.append((f["row"], f["col"], f["length"]))
    cells.append((22, 2, MESSAGES.get(mapid, ""), G_YELLOW if mapid != "CLRM410" else G_RED))
    pf = "  ".join(f"{k}={v}" for k, v in m["pf_keys"].items())
    cells.append((24, 2, pf, G_CYAN))
    cv = green_screen(cells, title_bar=f"CLARA 3270 session · {m['transaction']} · terminal L3T0417", underline=und)
    return cv.png_bytes()


def build_vs036() -> tuple[list[dict], str, int]:
    fid = "VS036"
    d = adate(fid)
    facts = Facts(fid, rel(fid))
    for ref, f in (("BMS:CLRM320", None), ("SYSTEM:SYS01", "cics_regions"), ("SYSTEM:SYS01", "db2_plan")):
        if f in ("cics_regions", "db2_plan"):
            continue  # never stated: exclusive to LD017
        guard(fid, ref, f)
    maps = ["CLRM010", "CLRM015", "CLRM110", "CLRM310", "CLRM320", "CLRM330", "CLRM410", "CLRM620"]
    for mp in maps:
        assert program_exists(W.bms_maps[mp]["program"], d), mp
    contents = ["1 Introduction", "2 FNOL capture (FN01)", "3 Policy lookup (FN15)", "4 Triage workbench (TR01)",
                "5 Initial reserve (RS01)", "6 Reserve adjustment (RS02)", "7 Reserve enquiry (RS03)",
                "8 Fraud referral (FR03)", "9 Subrogation case (RC02)", "10 Transaction and map reference", "11 Glossary"]
    b = start_doc(
        fid, facts, "Annotated 3270 screens for CLARA online transactions", "CM-CLR-SG-036", "4.2", "ops",
        "CLARA online screens used by claim handlers",
        versions_for(fid, "P024", [(400, "4.0", "Screens re-captured after the 2022 tiering change"),
                                   (120, "4.1", "Fraud referral screen added"),
                                   (0, "4.2", "Approved; reserve screens re-captured")], "4.2"),
        [approval("Author", "P024", d), approval("Reviewer", "P023", d, minus_days(d, 6)),
         approval("Approver", "P016", d)],
        ["Claims Operations UK", "Claims Operations Nordics", "CLARA support", "Training team"], contents,
        related=["CLARA Data Model", "CLARA operations handbook"],
        intro_extra=["Screens were captured from the CLARA training region with fictitious data. Field positions match "
                     "the BMS map definitions."])
    titles = {"CLRM010": ("2", "FNOL capture (FN01)", "the FNOL capture map"),
              "CLRM015": ("3", "Policy lookup (FN15)", "the policy lookup map"),
              "CLRM110": ("4", "Triage workbench (TR01)", "the triage workbench"),
              "CLRM310": ("5", "Initial reserve (RS01)", "the initial reserve map"),
              "CLRM320": ("6", "Reserve adjustment (RS02)", "the reserve adjustment map"),
              "CLRM330": ("7", "Reserve enquiry (RS03)", "the reserve enquiry map"),
              "CLRM410": ("8", "Fraud referral (FR03)", "the fraud referral map"),
              "CLRM620": ("9", "Subrogation case (RC02)", "the subrogation case map")}
    pl = placement(fid, "vs36_clrm320")
    for mp in maps:
        num, head, what = titles[mp]
        m = W.bms_maps[mp]
        section(b, fid, num, head, what)
        fx = []
        if mp == "CLRM320":
            fx = [placement_spec(pl, "NEXT-REVIEW"),
                  spec("screenshot", "CLARA map CLRM320 (Reserve adjustment) runs under transaction RS02 with program CLRRS020.",
                       "CLRRS020", "BMS:CLRM320#program"),
                  spec("screenshot", "On map CLRM320, PF8 is Forward.", "PF8=Forward", "BMS:CLRM320#pf_keys")]
        elif mp == "CLRM410":
            fx = [spec("screenshot", "CLARA fraud referral map CLRM410 (transaction FR03, program CLRFR030) shows SCORE "
                                     "and THRESHOLD fields; the 2023 training example shows threshold 070.",
                       "THRESHOLD", "BMS:CLRM410#fields", notes="threshold 70 was BR-FRD-012 v2, in force on 2023-09-11"),
                  spec("screenshot", "The 2023 referral message names the FRAUDNET score (renamed Sentinel 2025-03-01).",
                       "FRAUDNET SCORE", "SYSTEM:SYS03#renames")]
        elif mp == "CLRM110":
            fx = [spec("screenshot", "CLARA triage workbench CLRM110 runs under transaction TR01 (program CLRTR010) "
                                     "with fields TIER, SCORE, ROUTE and FASTTRACK.", "FASTTRACK", "BMS:CLRM110#fields")]
        elif mp == "CLRM010":
            fx = [spec("screenshot", "FNOL capture map CLRM010 (mapset CLRMS01) runs under transaction FN01.",
                       "CLARA - FNOL CAPTURE", "BMS:CLRM010")]
        elif mp == "CLRM620":
            fx = [spec("screenshot", "Subrogation case map CLRM620 includes the LIMITATION-DATE field.", "LIMITATION-DATE",
                       "BMS:CLRM620#fields")]
        b.figure(_map_screen(mp, d), f"{m['map']} {m['title']} ({m['transaction']})",
                 f"3270 screen for map {m['map']}, transaction {m['transaction']}, with labelled input fields and the PF key line.",
                 facts=fx)
        if mp == "CLRM320":
            b.comment_on_last("Captured from the training copy of the map; the sample claim and amounts are fictitious.",
                              name("P023", d), "KB", minus_days(d, 5),
                              fact=spec("comment", "Reviewer comment (Keith Barraclough): the CLRM320 screenshot was captured "
                                                   "from the training copy and its sample values are fictitious.",
                                        "the sample claim and amounts are fictitious", None))
    section(b, fid, "10", "Transaction and map reference", "every online transaction with its map, mapset and program")
    rows = []
    for mp in sorted(W.bms_maps):
        m = W.bms_maps[mp]
        if not program_exists(m["program"], d):
            continue
        rows.append([m["transaction"], m["map"], m["mapset"], m["program"], m["title"]])
    tim = table_image(["Transaction", "Map", "Mapset", "Program", "Function"], rows, [230, 220, 230, 250, 620],
                      title="CLARA online transactions", size=23,
                      note="PF keys on every map: PF3 Exit · PF7 Back · PF8 Forward · PF12 Cancel")
    b.figure(tim.png_bytes(), "Transaction and map reference",
             "Table image of CLARA transactions with map, mapset, program and function.",
             facts=[spec("image_table", "Transaction RS03 (Reserve enquiry) uses map CLRM330 and program CLRRS030.",
                         "CLRRS030", "BMS:CLRM330"),
                    spec("image_table", "Transaction AS02 (Claims Assessor appointment) uses map CLRM220 and program CLRAS020.",
                         "CLRAS020", "BMS:CLRM220")])
    glossary(b, fid, "11", [("BMS", "Basic Mapping Support (3270 map definition)"), ("PF key", "Program function key"),
                            ("Mapset", "Group of BMS maps"), ("FRAUDNET", "Fraud scoring engine")])
    path = out_path(fid)
    b.save(path)
    return facts.items, str(path), b.fig_no


# ==========================================================================================
# VS037 CLARA Data Model (ERD) (2025-03-24, P025)
# ==========================================================================================
def _cols(tname: str, keep: list[str] | None = None) -> list[tuple]:
    t = W.tables[tname]
    pk = set(t["primary_key"])
    fk = {f["column"] for f in t.get("foreign_keys", [])}
    out = []
    for c in t["columns"]:
        if keep and c["name"] not in keep:
            continue
        flags = ",".join(x for x, ok in (("PK", c["name"] in pk), ("FK", c["name"] in fk)) if ok)
        ty = c["type"] + (f"({c['length']})" if c["type"] in ("CHAR", "VARCHAR", "DECIMAL") and c.get("length") else "")
        out.append((c["name"], ty, flags))
    return out


def _erd(title_: str, sub: str, layout: list[tuple], rels: list[tuple], w: int = 2600, h: int = 1700,
         legend_rel: list[str] | None = None) -> bytes:
    E = ERD(w, h)
    E.title_band(title_, sub, right="CLARA DB2 schema CLR")
    for eid, x, y, width, keep in layout:
        t = W.tables[eid]
        E.entity(eid, x, y, eid, _cols(eid, keep), width=width, subtitle=f"{t['description']} · copybook {t['copybook']}",
                 size=22)
    for r in rels:
        E.relation(*r[:4], **(r[4] if len(r) > 4 else {}))
    if legend_rel:
        y = h - 60 - 44 * len(legend_rel)
        E.rect((40, y - 60, 40 + 1500, h - 30), fill=WHITE, outline=GRID, width=2, radius=8)
        E.text(60, y - 46, "Declared foreign keys", 23, True, fill=NAVY)
        for k, s in enumerate(legend_rel):
            E.text(60, y + k * 44, s, 22, fill=INK)
    return E.png_bytes()


def build_vs037() -> tuple[list[dict], str, int]:
    fid = "VS037"
    d = adate(fid)
    facts = Facts(fid, rel(fid))
    guard(fid, "TABLE:CLR.T_RESERVE_MOVEMENT", "foreign_keys")
    contents = ["1 Introduction", "2 Reserve subject area", "3 Claim and party", "4 Fraud", "5 Recoveries",
                "6 Settlement and payments", "7 Finance and reference", "8 Table inventory", "9 Glossary"]
    b = start_doc(
        fid, facts, "Entity-relationship diagrams of the CLARA DB2 schema", "CM-CLR-DM-037", "3.0", "data",
        "the CLARA DB2 data model",
        versions_for(fid, "P025", [(300, "2.0", "Re-drawn from the DB2 catalogue"),
                                   (40, "2.1", "Reserve subject area checked with the migration team"),
                                   (0, "3.0", "Approved for the migration mapping work")], "3.0"),
        [approval("Author", "P025", d), approval("Reviewer", "P023", d, minus_days(d, 7)),
         approval("Reviewer", "P052", d, minus_days(d, 7)), approval("Approver", "P016", d)],
        ["Legacy Claims Platforms (CLARA)", "IBM data migration team", "Data & Analytics"], contents,
        related=["CLARA data dictionary", "ERD Poster (Claims Hub and CLARA)"],
        intro_extra=["Each diagram is exported from the modelling tool. Lines are drawn only for declared foreign keys."])

    pl = placement(fid, "vs37_fk")
    section(b, fid, "2", "Reserve subject area", "the reserve tables and their declared keys")
    img = _erd("Reserve subject area", f"Declared keys as at {fmt_date_long(d)}",
               [("CLR.T_CLAIM", 60, 190, 620, ["CLAIM_ID", "POLICY_NO", "PRODUCT_CD", "PERIL_CD", "CLAIM_STATUS", "TIER_CD",
                                                  "REGION_CD", "CURRENCY_CD", "CLAIMANT_ID", "LAST_UPD_PGM"]),
                ("CLR.T_RESERVE", 900, 190, 700, None),
                ("CLR.T_RESERVE_MOVEMENT", 1820, 190, 720, None),
                ("CLR.T_RESERVE_AUTHORITY", 1820, 1000, 720, None),
                ("CLR.T_RESERVE_HISTORY", 60, 900, 620, None)],
               [("CLR.T_RESERVE", "CLAIM_ID", "CLR.T_CLAIM", "CLAIM_ID", {"sides": "lr"}),
                ("CLR.T_RESERVE_MOVEMENT", "RSV_ID", "CLR.T_RESERVE", "RSV_ID", {"sides": "lr"}),
                ("CLR.T_RESERVE_MOVEMENT", "CLAIM_ID", "CLR.T_CLAIM", "CLAIM_ID",
                 {"sides": "lr", "route_y": 160}),
                ("CLR.T_RESERVE_AUTHORITY", "RSV_ID", "CLR.T_RESERVE", "RSV_ID", {"sides": "lr"})],
               w=2600, h=1800,
               legend_rel=["FK1  CLR.T_RESERVE.CLAIM_ID → CLR.T_CLAIM.CLAIM_ID",
                           "FK2  CLR.T_RESERVE_MOVEMENT.RSV_ID → CLR.T_RESERVE.RSV_ID",
                           "FK3  CLR.T_RESERVE_MOVEMENT.CLAIM_ID → CLR.T_CLAIM.CLAIM_ID",
                           "FK4  CLR.T_RESERVE_AUTHORITY.RSV_ID → CLR.T_RESERVE.RSV_ID"])
    b.figure(img, "Reserve subject area",
             "Entity-relationship diagram of the claim, reserve, reserve movement, reserve authority and reserve history tables.",
             facts=[placement_spec(pl, "CLR.T_RESERVE_MOVEMENT.RSV_ID → CLR.T_RESERVE.RSV_ID"),
                    spec("image_text", "CLR.T_RESERVE has primary key RSV_ID and column RSV_NEXT_REVIEW_DT.",
                         "RSV_NEXT_REVIEW_DT", "TABLE:CLR.T_RESERVE#columns"),
                    spec("image_text", "CLR.T_RESERVE_MOVEMENT has EXTRACTED_FLAG and EXTRACT_RUN_ID columns.",
                         "EXTRACT_RUN_ID", "TABLE:CLR.T_RESERVE_MOVEMENT#columns"),
                    spec("image_text", "CLR.T_RESERVE uses copybook RSVREC; CLR.T_RESERVE_MOVEMENT uses RSVMVT01.",
                         "copybook RSVMVT01", "TABLE:CLR.T_RESERVE_MOVEMENT#copybook")])
    b.comment_on_last("Re-exported at print resolution for the data governance pack; no content change.", name("P052", d),
                      "GS", minus_days(d, 8))

    section(b, fid, "3", "Claim and party", "the claim header, claimant, tier history and FNOL tables")
    img = _erd("Claim and party", "Claim header, claimants, tier history, links and FNOL events",
               [("CLR.T_CLAIM", 60, 190, 620, None), ("CLR.T_CLAIMANT", 900, 190, 640, None),
                ("CLR.T_CLAIM_TIER", 900, 950, 640, None), ("CLR.T_FNOL_EVENT", 1760, 190, 640, None),
                ("CLR.T_CLAIM_LINK", 1760, 850, 640, None)],
               [("CLR.T_CLAIM", "CLAIMANT_ID", "CLR.T_CLAIMANT", "CLAIMANT_ID", {"sides": "rl"})], w=2460, h=1650)
    b.figure(img, "Claim and party",
             "Entity diagram of the claim header, claimant, tier history, claim link and FNOL event tables.",
             facts=[spec("image_text", "CLR.T_CLAIM.CLAIMANT_ID references CLR.T_CLAIMANT.CLAIMANT_ID.", "CLAIMANT_ID",
                         "TABLE:CLR.T_CLAIM#foreign_keys"),
                    spec("image_text", "CLR.T_CLAIM_TIER records TIER_REASON_CD and OVERRIDE_FLAG.", "TIER_REASON_CD",
                         "TABLE:CLR.T_CLAIM_TIER#columns")])

    section(b, fid, "4", "Fraud", "the fraud referral, score and SIU case tables")
    tabs = [t for t in ("CLR.T_FRAUD_REFERRAL", "CLR.T_FRAUD_SCORE", "CLR.T_SIU_CASE") if table_exists(t, d)]
    img = _erd("Fraud", "Referrals, Sentinel scores and SIU cases",
               [("CLR.T_FRAUD_REFERRAL", 60, 190, 760, None), ("CLR.T_FRAUD_SCORE", 1000, 190, 640, None),
                ("CLR.T_SIU_CASE", 1000, 820, 640, None), ("CLR.T_CLAIM", 1820, 190, 600, ["CLAIM_ID", "FRAUD_FLAG", "TIER_CD"])],
               [("CLR.T_FRAUD_REFERRAL", "CLAIM_ID", "CLR.T_CLAIM", "CLAIM_ID",
                 {"sides": "rl", "route_y": 160})], w=2480, h=1350)
    b.figure(img, "Fraud tables",
             "Entity diagram of the fraud referral, fraud score and SIU case tables.",
             facts=[spec("image_text", "CLR.T_FRAUD_REFERRAL holds REF_THRESHOLD_APPLIED and CUSTOMER_NOTICE_DUE_DT.",
                         "REF_THRESHOLD_APPLIED", "TABLE:CLR.T_FRAUD_REFERRAL#columns"),
                    spec("image_text", "CLR.T_FRAUD_SCORE stores MODEL_VERSION per score.", "MODEL_VERSION",
                         "TABLE:CLR.T_FRAUD_SCORE#columns")])

    section(b, fid, "5", "Recoveries", "the subrogation case, recovery, salvage and litigation tables")
    img = _erd("Recoveries", "Subrogation cases, recoveries, salvage and litigation",
               [("CLR.T_SUBROGATION_CASE", 60, 190, 720, None), ("CLR.T_RECOVERY", 960, 190, 720, None),
                ("CLR.T_SALVAGE", 1860, 190, 600, None), ("CLR.T_LITIGATION", 1860, 820, 600, None)],
               [("CLR.T_RECOVERY", "SUBRO_CASE_ID", "CLR.T_SUBROGATION_CASE", "SUBRO_CASE_ID", {"sides": "lr"})],
               w=2520, h=1450)
    b.figure(img, "Recovery tables",
             "Entity diagram of the subrogation case, recovery, salvage and litigation tables.",
             facts=[spec("image_text", "CLR.T_RECOVERY.SUBRO_CASE_ID references CLR.T_SUBROGATION_CASE.", "SUBRO_CASE_ID",
                         "TABLE:CLR.T_RECOVERY#foreign_keys"),
                    spec("image_text", "CLR.T_SUBROGATION_CASE has LIMITATION_DT and SUBTRAK_REF columns.", "SUBTRAK_REF",
                         "TABLE:CLR.T_SUBROGATION_CASE#columns")])

    section(b, fid, "6", "Settlement and payments", "the settlement, payment, payment batch and payee tables")
    img = _erd("Settlement and payments", "Settlements, payments, batches and payees",
               [("CLR.T_SETTLEMENT", 60, 190, 640, None), ("CLR.T_PAYMENT", 860, 190, 640, None),
                ("CLR.T_PAYMENT_BATCH", 1660, 190, 640, None), ("CLR.T_PAYEE", 1660, 760, 640, None)],
               [], w=2360, h=1300)
    b.figure(img, "Settlement and payment tables",
             "Entity diagram of the settlement, payment, payment batch and payee tables.",
             facts=[spec("image_text", "CLR.T_PAYMENT records SANCTIONS_RESULT from WatchScreen.", "SANCTIONS_RESULT",
                         "TABLE:CLR.T_PAYMENT#columns")])

    section(b, fid, "7", "Finance and reference", "the ledger, currency, reinsurance and reference tables")
    img = _erd("Finance and reference", "Ledger postings, periods, currency rates, cessions, parameters and codes",
               [("CLR.T_GL_POSTING", 60, 190, 620, None), ("CLR.T_GL_PERIOD", 60, 890, 620, None),
                ("CLR.T_CURRENCY_RATE", 840, 190, 620, None), ("CLR.T_REINSURANCE_CESSION", 840, 840, 620, None),
                ("CLR.T_PARAM", 1620, 190, 620, None), ("CLR.T_CODE_LOOKUP", 1620, 730, 620, None)],
               [], w=2300, h=1500)
    b.figure(img, "Finance and reference tables",
             "Entity diagram of the general-ledger, currency, reinsurance cession, parameter and code lookup tables.",
             facts=[spec("image_text", "CLR.T_PARAM is the CLARA parameter table (columns only shown).", "CLR.T_PARAM",
                         "TABLE:CLR.T_PARAM#columns")])

    section(b, fid, "8", "Table inventory", "every CLARA table with its description, copybook and primary key")
    rows = []
    for tn, t in sorted(W.tables.items()):
        if t["db"] != "DB2" or not table_exists(tn, d):
            continue
        rows.append([tn, asof_names(t["description"], d), t.get("copybook") or "", ", ".join(t["primary_key"]),
                     str(len(t["columns"]))])
    tim = table_image(["Table", "Description", "Copybook", "Primary key", "Cols"], rows, [520, 820, 220, 440, 100],
                      title=f"CLARA DB2 tables at {fmt_date_long(d)}", size=19)
    b.figure(tim.png_bytes(), "CLARA table inventory",
             "Table image listing each CLARA DB2 table with description, copybook, primary key and column count.",
             facts=[spec("image_table", "CLR.T_INTERFACE_LOG is part of the CLARA schema.", "CLR.T_INTERFACE_LOG",
                         "TABLE:CLR.T_INTERFACE_LOG"),
                    spec("image_table", "CLR.T_RESERVE_HISTORY has the composite primary key RSV_ID, SNAPSHOT_DT.",
                         "RSV_ID, SNAPSHOT_DT", "TABLE:CLR.T_RESERVE_HISTORY#primary_key")])
    glossary(b, fid, "9", [("PK", "Primary key"), ("FK", "Foreign key"), ("Copybook", "COBOL record layout"),
                           ("DB2", "IBM Db2 for z/OS")])
    path = out_path(fid)
    b.save(path)
    return facts.items, str(path), b.fig_no


# ==========================================================================================
# VS038 Vendor Network Map (2025-06-02, P033)
# ==========================================================================================
VENDOR_PINS = {
    "VEN-01": (-2.24, 53.48, 330, 860), "VEN-02": (11.97, 57.71, 1380, 1000), "VEN-03": (-0.12, 51.50, 1030, 1640),
    "VEN-04": (-1.51, 52.41, 300, 1260), "VEN-05": (10.20, 59.74, 1150, 400), "VEN-06": (-1.47, 53.38, 960, 860),
    "VEN-07": (-1.90, 52.48, 330, 1460), "VEN-08": (-1.55, 53.80, 330, 640), "VEN-09": (-0.24, 52.57, 1000, 1230),
    "VEN-10": (-1.55, 53.80, 960, 640), "VEN-11": (-0.12, 51.50, 360, 1700), "VEN-14": (10.20, 56.16, 1500, 1350),
    "VEN-15": (0.12, 52.20, 1020, 1450),
}
VTYPE = {"loss_adjuster": ("Loss adjusters (external Claims Assessors)", RED), "repair_network": ("Repair networks", TEAL),
         "solicitor": ("Solicitors", PURPLE), "salvage": ("Salvage", AMBER), "siu_partner": ("SIU partner", "#8E2C48"),
         "bank": ("Bank", NAVY2), "software": ("Software licensor", GREEN)}


def _vendor_role(v: dict, d: str) -> str:
    role = v["role"]
    if "(" in role and "removed" in role:
        role = role.split(" (")[0]
    return role


def _vendors(d):
    out = []
    for vid, v in sorted(W.vendors.items()):
        if v["type"] == "reinsurer":
            continue  # reinsurer roles are reserved for another document
        if str(v["panel_from"]) > d or (v.get("panel_to") and str(v["panel_to"]) < d):
            continue
        out.append(v)
    return out


def build_vs038() -> tuple[list[dict], str, int]:
    fid = "VS038"
    d = adate(fid)
    facts = Facts(fid, rel(fid))
    vens = _vendors(d)
    for v in vens:
        guard(fid, f"VENDOR:{v['id']}", "role")
    contents = ["1 Introduction", "2 Vendor map", "3 Vendor network", "4 Vendor register", "5 Service levels",
                "6 Vendor interfaces", "7 Vendor contacts", "8 Glossary"]
    b = start_doc(
        fid, facts, "Where our claims suppliers are and how they connect to us", "CM-VND-NM-038", "1.0", "vendor",
        "the claims supplier network",
        versions_for(fid, "P033", [(21, "0.1", "Draft map"), (8, "0.2", "Nordic suppliers added"),
                                   (0, "1.0", "Final")], "1.0"),
        [approval("Author", "P033", d), approval("Reviewer", "P034", d, minus_days(d, 3)),
         approval("Approver", "P011", d)],
        ["Claims Assessment UK and Nordics", "Claims Operations team leaders", "Supplier management"], contents,
        related=["Supplier panel register", "FNOL Channel Overview"])

    pl = placement(fid, "vs38_vardholm")
    section(b, fid, "2", "Vendor map", "where the panel suppliers are based")
    b.figure(_vendor_map(d, vens), "Vendor map, UK and Nordics",
             "Schematic map of the UK and the Nordic countries with pins and labels for each panel supplier.",
             facts=[placement_spec(pl, "Vardholm Bilverksted AS — 23 workshops in Norway"),
                    spec("image_text", "Thistlecombe Repair Network Ltd (Coventry) runs 212 approved bodyshops.",
                         "212 approved bodyshops", "VENDOR:VEN-04#role"),
                    spec("image_text", "Norrvik Skadetaxering AB (Gothenburg) provides external Claims Assessors for "
                                       "Sweden and Norway.", "Norrvik Skadetaxering AB", "VENDOR:VEN-02#role"),
                    spec("image_text", "Lyngholm Glass A/S (Aarhus) is the Danish windscreen network.", "Lyngholm Glass A/S",
                         "VENDOR:VEN-14#role")])

    section(b, fid, "3", "Vendor network", "the supplier categories and the systems they use")
    b.figure(_vendor_network(d, vens), "Vendor network by category",
             "Network diagram with Corvane Claims at the centre and supplier categories around it, with the systems used.",
             facts=[spec("image_text", f"External assessors and repair networks exchange instructions through the "
                                       f"{sysname('SYS17', d)} (name on 2025-06-02).", sysname("SYS17", d), "SYSTEM:SYS17#renames"),
                    spec("image_text", "Greyfold Investigations Ltd is the SIU partner.", "Greyfold Investigations Ltd",
                         "VENDOR:VEN-10#role")])

    section(b, fid, "4", "Vendor register", "the suppliers on the panel on the document date")
    rows = [[v["name"], VTYPE[v["type"]][0].split(" (")[0], f"{v['location']}, {v['country']}", str(v["panel_from"]),
             _vendor_role(v, d)] for v in vens]
    tim = table_image(["Supplier", "Category", "Location", "On panel since", "Role"], rows, [560, 300, 300, 230, 900],
                      title=f"Panel suppliers at {fmt_date_long(d)}", size=20)
    b.figure(tim.png_bytes(), "Vendor register",
             "Table image of panel suppliers with category, location, panel start date and role.",
             facts=[spec("image_table", "Fellgate Adjusting Partners LLP (major-loss adjusters, London) is on the panel "
                                        "on 2025-06-02 (on panel since 2019-07-01).", "Fellgate Adjusting Partners LLP",
                         "VENDOR:VEN-03#panel_from", notes="removed from the panel later, on 2026-01-31"),
                    spec("image_table", "Quarryhill Solicitors LLP handles subrogation and recovery litigation.",
                         "Subrogation and recovery litigation", "VENDOR:VEN-07#role")])

    section(b, fid, "5", "Service levels", "the agreed supplier service levels")
    b.figure(_sla_chart(d), "Supplier service levels (business days)",
             "Horizontal bar chart of supplier service levels in business days.",
             facts=[chart_spec("Brackenfield desk assessment SLA: 2 business days; site visit 5 business days.",
                         "Brackenfield – desk assessment", "VENDOR:VEN-01#sla"),
                    chart_spec("Salvanta Salvage collection SLA: 2 business days.", "Salvanta – collection",
                         "VENDOR:VEN-09#sla")])

    section(b, fid, "6", "Vendor interfaces", "the interfaces that carry supplier work")
    b.figure(_vendor_interfaces(fid, d), "Vendor interfaces",
             f"Diagram of interfaces between CLARA, {sysname('SYS17', d)}, {sysname('SYS05', d)} and suppliers.",
             facts=[arrow_spec("CLX-IF-024 carries salvage disposals uploaded by Salvanta Salvage via the partner "
                                       "SFTP, daily 20:00.", "CLX-IF-024", "INTERFACE:CLX-IF-024"),
                    arrow_spec("CLX-IF-013 assessor instructions run every 30 minutes 07:00-19:00.",
                         "every 30 minutes 07:00-19:00", "INTERFACE:CLX-IF-013#schedule")])

    section(b, fid, "7", "Vendor contacts", "the named supplier contacts")
    rows = []
    for pid in ("P057", "P058", "P059", "P060"):
        p = W.people[pid]
        rows.append([name(pid, d), title(pid, d), W.vendors[p["employer"]]["name"], p["email"]])
    tim = table_image(["Contact", "Title", "Supplier", "Email"], rows, [360, 520, 560, 560],
                      title="Supplier relationship contacts", size=22)
    b.figure(tim.png_bytes(), "Supplier contacts",
             "Table image of supplier contacts with title, supplier and email address.",
             facts=[spec("image_table", "Sigrid Nyhus (Regional Manager – Norway & Sweden) is the Norrvik contact.",
                         "Sigrid Nyhus", "PERSON:P058"),
                    spec("image_table", "Declan Furey is SIU Partner Lead at Greyfold Investigations.", "SIU Partner Lead",
                         "PERSON:P059")])
    glossary(b, fid, "8", [("SLA", "Service level agreement"), ("Panel", "Approved supplier list"),
                           ("Takst", "Assessment (Nordic)")])
    path = out_path(fid)
    b.save(path)
    return facts.items, str(path), b.fig_no


def _vendor_map(d, vens) -> bytes:
    M = SchematicMap(2300, 1900, -8.5, 20.5, 49.6, 63.2, top=130)
    M.title_band("Claims supplier network", f"Panel suppliers at {fmt_date_long(d)}", right="Schematic, not to scale")
    for v in vens:
        lon, lat, lx, ly = VENDOR_PINS[v["id"]]
        tname, col = VTYPE[v["type"]]
        if v["id"] == "VEN-05":
            text = "Vardholm Bilverksted AS — 23 workshops in Norway"
        elif v["id"] == "VEN-04":
            text = f"{v['name']} ({v['location']}) — 212 approved bodyshops"
        else:
            text = f"{v['name']} ({v['location']})"
        M.callout(lon, lat, lx, ly, text, color=col, size=21, max_w=560)
    M.legend(1550, 1440, [(c, n.split(" (")[0]) for n, c in VTYPE.values()], size=20, title="Supplier category",
             col_w=330)
    return M.png_bytes()


def _vendor_network(d, vens) -> bytes:
    D = Diagram(2500, 1500)
    D.title_band("Vendor network by category", "Suppliers grouped by category around Corvane Claims",
                 right=f"As at {fmt_date_short(d)}")
    D.node("core", (1000, 640, 1500, 860), "Corvane Claims\nCLARA · " + sysname("SYS17", d), "dark", size=27)
    cats: dict[str, list] = {}
    for v in vens:
        cats.setdefault(v["type"], []).append(v)
    pos = {"loss_adjuster": (60, 200), "repair_network": (60, 640), "solicitor": (60, 1120), "salvage": (1780, 200),
           "siu_partner": (1780, 640), "bank": (1780, 980), "software": (1780, 1260)}
    for t, vs in cats.items():
        x, y = pos[t]
        tname, col = VTYPE[t]
        h = 70 + 44 * len(vs)
        box = (x, y, x + 660, y + h)
        D.rect(box, fill=WHITE, outline=col, width=4, radius=12)
        D.text(x + 20, y + 16, tname, 23, True, fill=col)
        for k, v in enumerate(vs):
            D.text(x + 24, y + 62 + k * 44, v["name"], 22, fill=INK)
        D.nodes[t] = box
        D.edge_straight(t, "core", color=col, width=3, both=True)
    return D.png_bytes()


def _sla_chart(d) -> bytes:
    items = [("Brackenfield – desk assessment", 2), ("Brackenfield – site visit", 5), ("Brackenfield – report", 5),
             ("Norrvik – site visit", 5), ("Thistlecombe – repair start", 3), ("Kilnmoor – first visit", 2),
             ("Salvanta – collection", 2)]
    im = charts.bar_chart([a for a, _ in items], [b for _, b in items], title="Supplier service levels",
                          ylabel="Business days", value_labels=[f"{b} days" for _, b in items], horizontal=True,
                          w_in=13, h_in=7, ylim=(0, 6.5), colors=[charts.SERIES[0]] * 3 + [charts.SERIES[1]] * 4,
                          note="Northmere Clearing Bank payment cut-off: 17:00 UK.")
    return core.png_bytes(im)


def _vendor_interfaces(fid, d) -> bytes:
    rows = ["CLX-IF-013", "CLX-IF-014", "CLX-IF-015", "CLX-IF-016", "CLX-IF-024", "CLX-IF-025"]
    D = Diagram(2700, 200 + 150 * len(rows) + 40)
    D.title_band("Vendor interfaces", f"Interfaces carrying supplier work, {fmt_date_long(d)}", right="CLARA side")
    y = 180
    for k, iid in enumerate(rows):
        i = W.interfaces[iid]
        guard(fid, f"INTERFACE:{iid}", "schedule")
        D.node(f"s{k}", (60, y, 560, y + 110), sysname(i["source_system"], d),
               "legacy" if i["source_system"] == "SYS01" else "vendor", size=25)
        D.node(f"t{k}", (2140, y, 2640, y + 110), sysname(i["target_system"], d),
               "legacy" if i["target_system"] == "SYS01" else "vendor", size=25)
        D.edge(f"s{k}", f"t{k}", label=f"{iid} {i['name']} · {i['protocol']} · {W.interface_schedule(iid, d)}\n"
                                      f"{asof_names(i['format'], d)}",
               label_size=21, label_max_w=1450, label_outline=GRID)
        y += 150
    return D.png_bytes()


# ==========================================================================================
# VS039 FNOL Channel Overview (2025-02-03, P029)
# ==========================================================================================
def build_vs039() -> tuple[list[dict], str, int]:
    fid = "VS039"
    d = adate(fid)
    facts = Facts(fid, rel(fid))
    guard(fid, "TIMELINE:metrics", "fnol_channel_mix_pct.2024")
    contents = ["1 Introduction", "2 Channel mix", "3 Channel architecture", "4 What every FNOL must capture",
                "5 Acknowledging the customer", "6 Channel codes", "7 Contact centre rules", "8 Glossary"]
    b = start_doc(
        fid, facts, "How customers and brokers report claims to Corvane", "CM-FNL-CO-039", "1.0", "ops",
        "first notice of loss channels",
        versions_for(fid, "P029", [(25, "0.1", "Draft"), (9, "0.2", "Broker channel added"), (0, "1.0", "Final")], "1.0"),
        [approval("Author", "P029", d), approval("Reviewer", "P011", d, minus_days(d, 2)),
         approval("Approver", "P005", d)],
        ["Contact Centre", "Claims Operations UK", "Digital channels team", "Programme Skerry discovery team"], contents,
        related=["Claims Handling Manual v6.1", "Vendor Network Map"])

    pl = placement(fid, "vs39_mix")
    section(b, fid, "2", "Channel mix", "the share of first notifications by channel in 2024")
    im = charts.donut(["Telephone", "Digital (portal and app)", "Broker"], [58, 34, 8],
                      title="FNOL channel mix, 2024", colors=[charts.SERIES[0], charts.SERIES[1], charts.SERIES[2]],
                      center_text="2024")
    b.figure(core.png_bytes(im), "FNOL channel mix, 2024",
             "FNOL channel mix 2024: telephone 58%, digital 34%, broker 8%",
             facts=[placement_spec(pl, "telephone 58%, digital 34%, broker 8%",
                                   notes="exclusive; the shares appear only in the alt text (the donut has no value labels)")])

    section(b, fid, "3", "Channel architecture", "how each channel reaches CLARA")
    b.figure(_fnol_arch(fid, d), "FNOL channel architecture",
             "Diagram of the telephone, portal and app, broker and telematics channels and the systems that carry each to CLARA.",
             facts=[arrow_spec("Portal FNOLs reach CLARA as JSON over MQ on queue CLR.FNOL.IN (CLX-IF-001).",
                         "CLR.FNOL.IN", "INTERFACE:CLX-IF-001#format"),
                    arrow_spec("Contact centre FNOLs are handed from Harbour CRM to CLARA via CICS COMMAREA "
                                       "CLRCOMM1 (CLX-IF-002).", "CLRCOMM1", "INTERFACE:CLX-IF-002#format"),
                    spec("image_text", "In February 2025 the customer portal is called MyCorvane Claims and fraud "
                                       "scoring is done by FRAUDNET.", "FRAUDNET fraud pre-screen", "SYSTEM:SYS03#renames")])

    section(b, fid, "4", "What every FNOL must capture", "the mandatory capture items by channel")
    rows = []
    for rid in ("BR-FNOL-002", "BR-FNOL-006", "BR-FNOL-007", "BR-FNOL-008", "BR-FNOL-010", "BR-FNOL-011",
                "BR-FNOL-013", "BR-FNOL-014", "BR-FNOL-015", "BR-FNOL-018"):
        v = W.rule_version(rid, d)
        if v:
            guard(fid, f"RULE:{rid}@v{v['version']}", "text")
            rows.append([rid, v["text"]])
    tim = table_image(["Rule", "Capture requirement"], rows, [230, 1900], title="FNOL capture requirements", size=22)
    b.figure(tim.png_bytes(), "FNOL capture requirements",
             "Table image listing FNOL capture rules and their requirement text.",
             facts=[spec("image_table", "Portal and app FNOLs accept up to 20 photos of at most 15 MB each (BR-FNOL-011).",
                         "up to 20 photos", "RULE:BR-FNOL-011@v1"),
                    spec("image_table", "Theft FNOLs must capture a police crime reference within 7 days (BR-FNOL-007).",
                         "police crime reference within 7 days", "RULE:BR-FNOL-007@v1")])

    section(b, fid, "5", "Acknowledging the customer", "how and when the customer is acknowledged")
    b.figure(_ack_flow(fid, d), "Customer acknowledgement",
             "Flow from claim creation in CLARA to the Notify acknowledgement file and the customer.",
             facts=[spec("image_text", "From 2024-10-01 every FNOL is acknowledged within 2 business days (BR-FNOL-001 v2, "
                                       "NISA Circular 2024/07).", "within 2 business days", "RULE:BR-FNOL-001@v2"),
                    arrow_spec("CLX-IF-006 FNOL acknowledgements: CSV ack_YYYYMMDD.csv to Notify, daily 06:15.",
                         "ack_YYYYMMDD.csv", "INTERFACE:CLX-IF-006")])

    section(b, fid, "6", "Channel codes", "the channel codes stored on the claim")
    tim = table_image(["Code", "Channel", "Typical entry point"],
                      [["PH", "Telephone", "Glasgow Contact Centre (Harbour CRM)"],
                       ["WB", "Portal", "MyCorvane Claims web"], ["AP", "App", "MyCorvane Claims app"],
                       ["BR", "Broker", "Broker submission with broker reference"],
                       ["TL", "Telematics", "Crash alert via Evidence Intake Gateway"]],
                      [160, 340, 1000], title="FNOL channel codes (CLR.T_CLAIM.CHANNEL_CD)", size=24)
    b.figure(tim.png_bytes(), "FNOL channel codes",
             "Table image of FNOL channel codes PH, WB, AP, BR and TL with entry points.",
             facts=[spec("image_table", "FNOL channel code TL means telematics.", "Telematics", "TABLE:CLR.T_CLAIM#columns.CHANNEL_CD")])

    section(b, fid, "7", "Contact centre rules", "the contact centre rules that apply at first notification")
    b.figure(_cc_tiles(fid, d), "Contact centre rules at FNOL",
             "Four tiles with contact centre rules at first notification.",
             facts=[spec("image_text", "Out-of-hours telephone FNOLs get a callback by 10:00 the next business day "
                                       "(BR-FNOL-012).", "callback by 10:00", "RULE:BR-FNOL-012@v1"),
                    spec("image_text", "Contact centre staff may authorise emergency make-safe work up to £500 at FNOL "
                                       "(BR-FNOL-019).", "make-safe work up to £500", "RULE:BR-FNOL-019@v1"),
                    spec("image_text", "A telematics crash alert creates a draft FNOL within 5 minutes (BR-FNOL-009).",
                         "draft FNOL within 5 minutes", "RULE:BR-FNOL-009@v1")])
    glossary(b, fid, "8", [("FNOL", "First notice of loss"), ("CRM", "Customer relationship management"),
                           ("COMMAREA", "CICS communication area"), ("FRAUDNET", "Fraud scoring engine")])
    path = out_path(fid)
    b.save(path)
    return facts.items, str(path), b.fig_no


def _fnol_arch(fid, d) -> bytes:
    for iid in ("CLX-IF-001", "CLX-IF-002", "CLX-IF-004"):
        guard(fid, f"INTERFACE:{iid}", "format")
    D = Diagram(2500, 1450)
    D.title_band("FNOL channel architecture", f"Channels into CLARA, {fmt_date_long(d)}", right="Current state")
    D.node("tel", (60, 200, 500, 340), "Telephone\ncustomers", "external", size=26)
    D.node("web", (60, 480, 500, 620), "Portal and app\ncustomers", "external", size=26)
    D.node("brk", (60, 760, 500, 900), "Brokers", "external", size=26)
    D.node("tl", (60, 1040, 500, 1180), "Telematics devices", "external", size=26)
    D.node("crm", (820, 200, 1300, 340), f"{sysname('SYS12', d)}\nGlasgow Contact Centre", "target", size=24)
    D.node("myc", (820, 480, 1300, 620), sysname("SYS04", d), "target", size=26)
    D.node("eig", (820, 1040, 1300, 1180), sysname("SYS13", d), "target", size=26)
    D.node("clara", (1800, 420, 2420, 900), "CLARA\nFNOL capture (FN01)\nclaim created", "legacy", size=28)
    D.node("fn", (1800, 1040, 2420, 1180), f"{sysname('SYS03', d)}\nfraud pre-screen", "external", size=25)
    D.edge("tel", "crm", "call", label_size=21)
    D.edge("web", "myc", "online form", label_size=21)
    D.edge("brk", "clara", "broker submission (broker reference)", sides="rl", label_size=21,
           via=[(1600, 830), (1600, 830)], label_xy=(1100, 830))
    D.edge("tl", "eig", "crash alert", label_size=21)
    D.edge("crm", "clara", "CLX-IF-002\nCICS COMMAREA (CLRCOMM1)", sides="rl", boff=-120, label_size=21,
           label_outline=GRID, label_xy=(1550, 270))
    D.edge("myc", "clara", "CLX-IF-001\nJSON over MQ, CLR.FNOL.IN", sides="rl", boff=-60, label_size=21,
           label_outline=GRID, label_xy=(1550, 550))
    D.edge("eig", "clara", "CLX-IF-004 evidence references", sides="rb", label_size=21, label_outline=GRID,
           label_xy=(1550, 1110), boff=-100)
    D.edge("clara", "fn", "score", sides="bt", aoff=200, boff=200, label_size=21)
    return D.png_bytes()


def _ack_flow(fid, d) -> bytes:
    guard(fid, "INTERFACE:CLX-IF-006", "schedule")
    D = Diagram(2400, 950)
    D.title_band("Customer acknowledgement", "BR-FNOL-001 v2 (NISA Circular 2024/07)", right=f"As at {fmt_date_short(d)}")
    D.node("c", (60, 330, 520, 520), "CLARA\nclaim created", "legacy", size=27)
    D.node("n", (960, 330, 1420, 520), "Notify\nletter / SMS / email", "external", size=27)
    D.node("cu", (1860, 330, 2320, 520), "Customer", "dark", size=30)
    D.edge("c", "n", f"CLX-IF-006 · ack_YYYYMMDD.csv\n{W.interface_schedule('CLX-IF-006', d)}", label_size=22,
           label_outline=GRID)
    D.edge("n", "cu", "acknowledgement", label_size=22)
    D.node("rule", (60, 640, 2320, 820), "Acknowledge every first notice of loss within 2 business days.",
           "note", size=28)
    return D.png_bytes()


def _cc_tiles(fid, d) -> bytes:
    tiles = []
    for rid, head in (("BR-FNOL-012", "Out of hours"), ("BR-FNOL-019", "Emergency make-safe"),
                      ("BR-FNOL-009", "Telematics alerts"), ("BR-FNOL-014", "Vulnerable customers")):
        v = W.rule_version(rid, d)
        guard(fid, f"RULE:{rid}@v{v['version']}", "text")
        tiles.append((head, rid, v["text"]))
    C = Canvas(2400, 900, "#F4F6F9")
    C.title_band("Contact centre rules at FNOL", "Glasgow Contact Centre", right=f"As at {fmt_date_short(d)}")
    x = 40
    for head, rid, txt in tiles:
        C.rect((x, 190, x + 550, 840), fill=WHITE, outline=GRID, width=2, radius=14)
        C.text(x + 28, 220, head, 30, True, fill=NAVY)
        C.text(x + 28, 275, rid, 23, True, fill=TEAL)
        C.text_in_box((x + 10, 320, x + 540, 830), txt, 26, align="left", valign="top", pad=20)
        x += 585
    return C.png_bytes()

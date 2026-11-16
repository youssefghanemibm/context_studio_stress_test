"""Raster PDF / poster builders VS045-VS050."""
from __future__ import annotations

from PIL import Image

from . import charts, core
from .core import (AMBER, BLUE_L, GREEN, GREY_L, GRID, INK, INK2, LINE, MUTED, NAVY, NAVY2, PURPLE, RED, TEAL, WHITE,
                   Canvas, fmt_date_long, fmt_date_short)
from .ctx import W, adate, guard, name, placement, sysname, svcname, team_name, title
from generators.visuals import wave_dates as WD

from .diagrams import Diagram, ERD, Timeline, table_image
from .facts import placement_spec, spec
from .pdf_kit import A3_LAND, A4_LAND
from .pdfs_a import PdfFile
from .screens import (S_ACCENT, S_BAD, S_MUTED, S_TEXT, S_WARN, HubScreen, SentinelScreen)


# ==========================================================================================
# VS045 Claims Hub Screenshot Pack (2026-09-07, P017)
# ==========================================================================================
REH_USER = "H. Lyle (UAT)"


def _uat(active, ttl, crumb, w, h):
    return HubScreen(w, h, title=ttl, breadcrumb=crumb, user=REH_USER, env="UAT", active=active,
                     version="Claims Hub R2026.09 · Wave 1 dress rehearsal")


def build_vs045():
    fid = "VS045"
    P = PdfFile(fid, A4_LAND, "CM-CHB-SP-045", "1.0")
    d = P.d
    guard(fid, "TABLE:claim_core.claim", "columns.claim_id")
    pl = placement(fid, "vs45_claimref")
    Wd, Hd = P.W, P.H - 64
    # page 1: index
    c = P.canvas("Claims Hub screenshot pack", "Wave 1 UK motor · dress-rehearsal environment (masked data, ADR-025)",
                 right=f"Captured up to {fmt_date_short(d)}", bg="#F4F6F9")
    items = ["2  Work queue", "3  Claim summary", "4  FNOL intake form", "5  Payments tab"]
    y = 260
    c.text(80, y, "Contents", 44, True, fill=NAVY)
    for it in items:
        y += 90
        c.text(100, y, it, 38, fill=INK)
    c.rect((1250, 260, Wd - 80, 1100), fill=WHITE, outline=GRID, radius=16)
    c.text_in_box((1270, 280, Wd - 100, 1080), "Screens were captured in the UAT environment used for the Wave 1 dress "
                  "rehearsal. Personal data is masked as required by ADR-025. Claim references are rehearsal copies of "
                  "CLARA claims.", 36, align="left", valign="top", pad=30)
    P.add(c, "Claims Hub screenshot pack — contents",
          facts=[spec("image_text", "The screenshot pack was captured in the UAT environment used for the Wave 1 dress "
                                    "rehearsal, with personal data masked (ADR-025).", "masked as required by ADR-025",
                      "ADR:ADR-025")])
    # page 2: work queue
    S = _uat("Work queue", "Team work queue", "Home / Work queue", Wd, Hd)
    y = S.content_top
    S.chip(280, y, "Team: Motor Claims – Leeds", "info", size=24)
    rows = [["CLM-UK-2025-118204", "2", "Collision", "Review rehearsal copy", "2026-09-08"],
            ["CLM-UK-2026-900213", "1", "Windscreen", "Confirm repair booked", "2026-09-08"],
            ["CLM-UK-2026-900227", "3", "Theft", "Reserve review", "2026-09-09"],
            ["CLM-UK-2026-900238", "1", "Collision", "Approve payment", "2026-09-09"],
            ["CLM-UK-2026-900244", "2", "Third-party damage", "Appoint assessor", "2026-09-10"]]
    S.grid_table(280, y + 80, ["Claim", "Tier", "Loss type", "Next action", "Due"], rows, [420, 140, 380, 560, 300],
                 size=27, row_h=72)
    P.add_image(S.img, "Claims Hub screenshot pack — work queue",
                facts=[spec("screenshot", "Work queue columns in Claims Hub: Claim, Tier, Loss type, Next action, Due.",
                            "Next action", None)])
    # page 3: claim summary (placement)
    S = _uat("Claims", "CLM-UK-2025-118204", "Claims / CLM-UK-2025-118204", Wd, Hd)
    y = S.tabs(280, S.content_top, ["Overview", "Reserves", "Fraud", "Payments", "Documents"], "Overview", size=27)
    x0, yy = S.card((280, y, 1260, y + 760), "Claim", size=28)
    yy = S.field(x0, yy, "Claim reference", "CLM-UK-2025-118204", size=27, value_bold=True)
    yy = S.field(x0, yy, "Legacy reference (CLARA)", "UK2025118204", size=27)
    yy = S.field(x0, yy, "Region / currency", "UK · GBP", size=27)
    yy = S.field(x0, yy, "Source", "Rehearsal copy from CLARA", size=27)
    x1, y1 = S.card((1290, y, Wd - 40, y + 760), "Parties", size=28)
    y1 = S.field(x1, y1, "Policyholder", "•••••• (masked)", size=27)
    y1 = S.field(x1, y1, "Contact", "•••••• (masked)", size=27)
    S.banner(280, y + 790, Wd - 320, "Claim references use the format CLM-<region>-<year>-<6 digits>; the CLARA "
             "reference is shown alongside.", "info", size=26)
    P.add_image(S.img, "Claims Hub screenshot pack — claim summary",
                facts=[placement_spec(pl, "CLM-UK-2025-118204"),
                       spec("screenshot", "Claims Hub shows the CLARA legacy reference UK2025118204 next to claim "
                                          "CLM-UK-2025-118204.", "UK2025118204", "TABLE:CLR.T_CLAIM#columns.CLAIM_ID")])
    # page 4: FNOL intake form
    S = _uat("FNOL intake", "New first notice of loss", "FNOL intake / New", Wd, Hd)
    y = S.content_top
    x0, yy = S.card((280, y, 1300, y + 1000), "Loss details", size=28)
    for lab, val in (("Policy number", "MU9000••••"), ("Date of loss", "2026-09-05"), ("Loss type (peril)", "Collision"),
                     ("Loss location (postcode)", "LS11 •••"), ("Vehicle registration", "•••• •••")):
        yy = S.field(x0, yy, lab, val, w=940, size=26, boxed=True)
    x1, y1 = S.card((1330, y, Wd - 40, y + 1000), "Contact and checks", size=28)
    for lab, val in (("Contact details", "•••••• (masked)"), ("Language preference", "EN"),
                     ("Vulnerability indicator", "No"), ("Third party involved", "Yes")):
        y1 = S.field(x1, y1, lab, val, w=Wd - 40 - x1 - 20, size=26, boxed=True)
    S.button(x1, y1 + 20, "Create claim", size=26)
    P.add_image(S.img, "Claims Hub screenshot pack — FNOL intake",
                facts=[spec("screenshot", "The FNOL intake form captures policy number, date of loss, loss type, loss "
                                          "location, contact details and a vulnerability indicator.", "Vulnerability indicator",
                            "RULE:BR-FNOL-014@v1")])
    # page 5: payments tab
    S = _uat("Payments", "CLM-UK-2026-900238", "Claims / CLM-UK-2026-900238 / Payments", Wd, Hd)
    y = S.tabs(280, S.content_top, ["Overview", "Reserves", "Fraud", "Payments", "Documents"], "Payments", size=27)
    rows = [["PAY-REH-0011", "Repairer", "1,840.00", "CF confirmed", "Cleared"],
            ["PAY-REH-0012", "Policyholder", "250.00", "SN sent", "Cleared"],
            ["PAY-REH-0013", "Hire provider", "612.40", "RQ requested", "Pending"]]
    y = S.grid_table(280, y + 20, ["Payment", "Payee", "Amount (GBP)", "Status", "WatchScreen"], rows,
                     [330, 340, 330, 360, 330], size=26, row_h=70)
    S.banner(280, y + 40, Wd - 320, "Every payee passes WatchScreen sanctions screening before a payment is released. "
             "Payments go in the next payment run.", "info", size=26)
    P.add_image(S.img, "Claims Hub screenshot pack — payments",
                facts=[spec("screenshot", "Payment statuses in Claims Hub include RQ requested, SN sent and CF confirmed.",
                            "CF confirmed", "TABLE:CLR.T_PAYMENT#columns.PAY_STATUS"),
                       spec("screenshot", "Every payee passes WatchScreen sanctions screening before payment release.",
                            "WatchScreen sanctions screening", "RULE:BR-STL-007@v1")])
    return P.save()


# ==========================================================================================
# VS046 Sentinel Dashboard Screenshots (2026-10-12, P027)
# ==========================================================================================
def build_vs046():
    fid = "VS046"
    P = PdfFile(fid, A4_LAND, "CM-FRD-SD-046", "1.0")
    d = P.d
    guard(fid, "RULE:BR-FRD-031@v2", None)
    for f in ("model_version", "tech"):
        guard(fid, "SYSTEM:SYS03", f)
    pl = placement(fid, "vs46_thresholds")
    cfg = W.services["fraud-referral-svc"]["config"]
    Wd, Hd = P.W, P.H - 64
    user = f"{name('P027', d)} · model owner"
    # page 1: overview
    S = SentinelScreen(Wd, Hd, page="Overview", user=user, stamp=f"{d} 09:12 UK")
    y = S.content_top
    tiles = [("Active model", W.systems["SYS03"]["model_version"], "gradient-boosted · scores 0–100"),
             ("Scoring SLA", "15 min", "every new claim (BR-TRI-007)"),
             ("Online timeout", "800 ms", "fallback to batch scoring (ADR-013)"),
             ("Nightly batch", "00:15 / 00:55", "request / return (CLX-IF-009 / 010)")]
    tw = (Wd - 80 - 3 * 30) // 4
    for k, (lab, val, sub) in enumerate(tiles):
        x0 = 40 + k * (tw + 30)
        S.kpi((x0, y, x0 + tw, y + 260), lab, val, sub)
    x, yy = S.panel((40, y + 300, Wd - 40, Hd - 30), "Service status")
    rows = [["Online scoring (CLARA, CLX-IF-008)", "REST via mainframe API gateway", "Healthy"],
            ["Online scoring (Claims Hub, CLX-IF-036)", "REST", "Healthy"],
            ["Batch scoring request (CLX-IF-009)", "SFTP CSV · daily 00:15", "Completed"],
            ["Batch score return (CLX-IF-010)", "SFTP CSV · daily 00:55", "Completed"]]
    S.table(x, yy, ["Integration", "Channel", "Status"], rows, [900, 760, 400], size=25, row_h=62,
            colors={(i, 2): S_ACCENT for i in range(4)})
    P.add_image(S.img, "Sentinel dashboard screenshots — overview",
                facts=[spec("screenshot", "The Sentinel console shows the online scoring timeout of 800 ms with fallback to "
                                          "batch scoring.", "800 ms", "ADR:ADR-013#consequences"),
                       spec("screenshot", "Nightly batch scoring: request 00:15 and return 00:55 (CLX-IF-009 / CLX-IF-010).",
                            "00:15 / 00:55", "INTERFACE:CLX-IF-010#schedule")])
    # page 2: thresholds (placement)
    S = SentinelScreen(Wd, Hd, page="Thresholds", user=user, stamp=f"{d} 09:14 UK")
    y = S.content_top
    S.text(40, y + 10, f"Model {W.systems['SYS03']['model_version']} · Thresholds: 65 (all) / 60 (Tier-3)", 40, True,
           fill=S_TEXT)
    x, yy = S.panel((40, y + 90, Wd - 40, y + 640), "Referral thresholds (fraud-referral-svc configuration)")
    rows = [["referral.threshold.default", str(cfg["referral.threshold.default"]), "all claims", "2026-04-01"],
            ["referral.threshold.tier3", str(cfg["referral.threshold.tier3"]), "Tier-3 claims (BR-TRI-003)",
             cfg["referral.threshold.tier3.effective-from"]]]
    S.table(x, yy, ["Key", "Value", "Applies to", "Effective from"], rows, [700, 260, 620, 460], size=27, row_h=72,
            colors={(1, 1): S_WARN})
    x, yy = S.panel((40, y + 670, Wd - 40, Hd - 30), "Rule references")
    yy = S.kv(x, yy, "Rule", "BR-FRD-031 v2 (decision DEC-014, 2026-09-17)")
    yy = S.kv(x, yy, "Superseded", "BR-FRD-031 v1 · 65 for all claims (2026-04-01 to 2026-09-30)")
    yy = S.kv(x, yy, "Safeguard", "BR-FRD-033 · no decline on the score alone")
    P.add_image(S.img, "Sentinel dashboard screenshots — thresholds",
                facts=[placement_spec(pl, "Thresholds: 65 (all) / 60 (Tier-3)"),
                       spec("screenshot", "Sentinel console shows model SNT-4.2.", "Model SNT-4.2", "SYSTEM:SYS03#model_version"),
                       spec("screenshot", "referral.threshold.tier3 = 60, effective from 2026-10-01.",
                            "referral.threshold.tier3", "SERVICE:fraud-referral-svc#config")])
    # page 3: referral queue (masked)
    S = SentinelScreen(Wd, Hd, page="Referral queue", user=user, stamp=f"{d} 09:20 UK")
    y = S.content_top
    x, yy = S.panel((40, y, Wd - 40, Hd - 30), "Referrals awaiting SIU triage (masked)")
    rows = [["CLM-UK-2026-2•••••", "3", "61", "60", "Tier-3 threshold", "2026-10-09"],
            ["CLM-UK-2026-2•••••", "2", "71", "65", "General threshold", "2026-10-09"],
            ["CLM-NO-2026-0•••••", "1", "66", "65", "General threshold", "2026-10-10"],
            ["CLM-UK-2026-2•••••", "3", "64", "60", "Tier-3 threshold", "2026-10-11"],
            ["CLM-SE-2026-0•••••", "2", "77", "65", "General threshold", "2026-10-11"]]
    yy = S.table(x, yy, ["Claim (masked)", "Tier", "Score", "Threshold applied", "Basis", "Referred"], rows,
                 [520, 150, 170, 350, 450, 380], size=26, row_h=66, colors={(0, 4): S_WARN, (3, 4): S_WARN})
    S.text(x, yy + 30, "SIU triage due within 3 business days of referral (BR-FRD-035 v2).", 26, fill=S_MUTED)
    P.add_image(S.img, "Sentinel dashboard screenshots — referral queue",
                facts=[spec("screenshot", "The referral queue shows the threshold applied per referral: 60 for Tier-3 "
                                          "claims, 65 otherwise.", "Tier-3 threshold", "RULE:BR-FRD-031@v2"),
                       spec("screenshot", "SIU triage is due within 3 business days of referral.", "within 3 business days",
                            "RULE:BR-FRD-035@v2")])
    # page 4: integrations
    S = SentinelScreen(Wd, Hd, page="Integrations", user=user, stamp=f"{d} 09:25 UK")
    y = S.content_top
    x, yy = S.panel((40, y, Wd - 40, Hd - 30), "Endpoints and callers")
    yy = S.kv(x, yy, "Scoring endpoint", "sentinel.corvane.internal", kw=520)
    yy = S.kv(x, yy, "Hosting", "Corvane private cloud VM cluster, Leeds Data Centre", kw=520)
    yy = S.kv(x, yy, "Licensor", W.vendors["VEN-15"]["name"], kw=520)
    yy = S.kv(x, yy, "Callers", "CLARA (CLX-IF-008), Claims Hub triage-svc (CLX-IF-036)", kw=520)
    yy = S.kv(x, yy, "Events", "fraud.score.received.v1 → fraud-referral-svc", kw=520)
    P.add_image(S.img, "Sentinel dashboard screenshots — integrations",
                facts=[spec("screenshot", "Sentinel's scoring endpoint is sentinel.corvane.internal.",
                            "sentinel.corvane.internal", "SYSTEM:SYS03#description"),
                       spec("screenshot", "Sentinel is licensed from Kestwick Analytics Ltd.", "Kestwick Analytics Ltd",
                            "VENDOR:VEN-15#role")])
    return P.save()


# ==========================================================================================
# VS047 Infrastructure Network Diagram (2025-05-12, P032)
# ==========================================================================================
def build_vs047():
    fid = "VS047"
    P = PdfFile(fid, A3_LAND, "CM-TEC-ND-047", "2.0")
    d = P.d
    guard(fid, "SYSTEM:SYS14", "tech")
    pl = placement(fid, "vs47_mq")
    c = P.canvas("Infrastructure network diagram", f"Claims platforms, data centres and links, {fmt_date_long(d)}",
                 right="Technology Delivery Office")
    Wd = P.W
    c.zone((40, 230, 1220, 1260), "Leeds Data Centre", fill="#F7F1E6", outline=core.LEGACY)
    c.node("prd1", (90, 300, 700, 560), "z/OS LPAR PRD1\nCLARA (COBOL / CICS / DB2)\nBatch Scheduler", "legacy", size=27)
    c.node("clrqm", (780, 330, 1170, 530), "MQ CLRQM01\n(z/OS queue manager)", "platform", size=26)
    c.node("sent", (90, 700, 700, 900), f"{sysname('SYS03', d)} VM cluster", "external", size=27)
    c.node("ldsapp", (90, 980, 1170, 1200), f"Leeds private cloud: {sysname('SYS05', d)} · {sysname('SYS17', d)} · "
           f"{sysname('SYS22', d)}", "external", size=25)
    c.zone((1420, 230, Wd - 40, 1260), "Corvane private cloud, London", fill="#EEF5FB", outline=NAVY2)
    c.node("hubqm", (1470, 330, 1960, 530), "MQ HUBQM01\n(distributed queue manager)", "platform", size=26)
    c.node("ocp", (2060, 300, Wd - 90, 560), "OpenShift ocp-prd-lon1 (primary)\nClaims Hub (build) · Evidence Intake Gateway\n"
           "Event Streaming Platform", "service", size=25)
    c.node("lonapp", (1470, 700, Wd - 90, 900), f"{sysname('SYS08', d)} · {sysname('SYS06', d)} · {sysname('SYS16', d)} · "
           f"{sysname('SYS04', d)} · {sysname('SYS10', d)}", "external", size=25)
    c.node("dr", (1470, 980, Wd - 90, 1200), "OpenShift ocp-dr-lds1 (DR, Leeds)", "service", size=26, dash=(12, 8))
    c.edge("prd1", "clrqm", "local", label_size=22)
    c.edge("clrqm", "hubqm", "MQ channel", label_size=24, both=True, width=5)
    c.edge("hubqm", "ocp", "MQ client", label_size=22, both=True)
    c.zone((40, 1340, 1220, 1820), "Bristol DR Data Centre", fill="#F7F1E6", outline=core.LEGACY)
    c.node("drp1", (90, 1420, 1170, 1600), "z/OS LPAR DRP1 (CLARA disaster recovery)", "legacy", size=26, dash=(12, 8))
    c.node("brs", (90, 1640, 1170, 1780), f"Bristol private cloud: {sysname('SYS09', d)} · {sysname('SYS24', d)}",
           "external", size=24)
    c.zone((1420, 1340, 2300, 1820), "Copenhagen", fill="#EEF6EE", outline=GREEN)
    c.node("cdw", (1470, 1440, 2250, 1640), sysname("SYS11", d), "external", size=27)
    c.zone((2380, 1340, Wd - 40, 1820), "Vendor SaaS (internet / VPN)", fill=GREY_L, outline=LINE)
    c.node("saas", (2430, 1420, Wd - 90, 1760), f"{sysname('SYS07', d)} · {sysname('SYS12', d)}\n{sysname('SYS19', d)} · "
           f"{sysname('SYS25', d)}\n{sysname('SYS26', d)}", "external", size=25)
    c.edge("prd1", "drp1", "replication to DR", sides="bt", label_size=22, aoff=-200, boff=-340, dash=(14, 8))
    c.label(Wd / 2, 1920, "MQ path: z/OS LPAR PRD1 – CLRQM01 – HUBQM01", 34, bold=True, bg="#FFF6E0", outline=AMBER, pad=14)
    P.add(c, "Infrastructure network diagram — page 1 of 2",
          facts=[placement_spec(pl, "PRD1 – CLRQM01 – HUBQM01"),
                 spec("image_text", "CLARA disaster recovery runs on z/OS LPAR DRP1 at the Bristol DR Data Centre.",
                      "LPAR DRP1", "SYSTEM:SYS01#hosting"),
                 spec("image_text", f"In May 2025 the document store is still called {sysname('SYS05', d)} and the assessor "
                                    f"portal {sysname('SYS17', d)}.", sysname("SYS17", d), "SYSTEM:SYS17#renames"),
                 spec("image_text", "The Claims Data Warehouse is hosted in Copenhagen.", "Copenhagen", "SYSTEM:SYS11#hosting")])
    # page 2: site table
    c = P.canvas("Hosting by site", "Where each claims system runs", right=f"As at {fmt_date_short(d)}")
    rows = []
    for sid in ("SYS01", "SYS02", "SYS03", "SYS04", "SYS05", "SYS06", "SYS07", "SYS08", "SYS09", "SYS10", "SYS11",
                "SYS12", "SYS13", "SYS14", "SYS15", "SYS16", "SYS17", "SYS18", "SYS19", "SYS22", "SYS24", "SYS25"):
        s = W.systems[sid]
        host = s["hosting"]
        if sid == "SYS02":
            host = "OpenShift ocp-prd-lon1 (London); DR ocp-dr-lds1 (Leeds) — MVP in build"
        rows.append([sysname(sid, d), s["type"], host])
    tim = table_image(["System", "Type", "Hosting"], rows, [520, 720, 1900], size=22, title="")
    P.fit(c, tim.img, top=180)
    P.add(c, "Infrastructure network diagram — page 2 of 2",
          facts=[spec("image_table", "MQ Backbone runs queue managers CLRQM01 (z/OS) and HUBQM01 (distributed) in the Leeds "
                                     "Data Centre and the Corvane private cloud.", "Leeds Data Centre and Corvane private cloud",
                      "SYSTEM:SYS14#hosting"),
                 spec("image_table", "The Batch Scheduler runs on z/OS LPAR PRD1.", "Batch Scheduler", "SYSTEM:SYS18#hosting")])
    return P.save()


# ==========================================================================================
# VS048 ERD Poster (Claims Hub and CLARA) (2025-03-24, P025)
# ==========================================================================================
def _ecols(tname, keep=None):
    t = W.tables[tname]
    pk = set(t["primary_key"])
    fk = {f["column"] for f in t.get("foreign_keys", [])}
    out = []
    for c_ in t["columns"]:
        if keep and c_["name"] not in keep:
            continue
        ty = c_["type"] + (f"({c_['length']})" if c_["type"] in ("CHAR", "VARCHAR", "DECIMAL", "NUMERIC") and c_.get("length") else "")
        flags = ",".join(x for x, ok in (("PK", c_["name"] in pk), ("FK", c_["name"] in fk)) if ok)
        out.append((c_["name"], ty, flags))
    return out


def build_vs048():
    fid = "VS048"
    P = PdfFile(fid, A3_LAND, "CM-DAT-EP-048", "1.0")
    d = P.d
    guard(fid, "TABLE:reserve.reserve_movement", "columns.amount_minor")
    pl = placement(fid, "vs48_minor")
    svc = svcname("reserve-engine", d)
    E = ERD(P.W, P.H - 64)
    E.title_band("Reserve data: CLARA and Claims Hub", f"CLARA DB2 (left) and Claims Hub {svc} PostgreSQL (right) · design "
                 f"baseline {fmt_date_long(d)}", h=150, size=48, sub_size=28, right="ERD poster")
    E.ROW, E.HEAD = 46, 70
    E.entity("CLR.T_RESERVE", 60, 230, "CLR.T_RESERVE", _ecols("CLR.T_RESERVE"), width=820, size=27, head_fill=core.LEGACY,
             subtitle="CLARA · copybook RSVREC")
    E.entity("CLR.T_RESERVE_MOVEMENT", 960, 230, "CLR.T_RESERVE_MOVEMENT", _ecols("CLR.T_RESERVE_MOVEMENT"), width=820,
             size=27, head_fill=core.LEGACY, subtitle="CLARA · copybook RSVMVT01")
    E.entity("reserve.reserve", 2060, 230, "reserve.reserve", _ecols("reserve.reserve"), width=640, size=27,
             head_fill=TEAL, subtitle=f"Claims Hub · {svc}")
    E.entity("reserve.reserve_movement", 2060, 900, "reserve.reserve_movement", _ecols("reserve.reserve_movement"), width=640,
             size=27, head_fill=TEAL, subtitle=f"Claims Hub · {svc}")
    E.entity("reserve.review_schedule", 2760, 230, "reserve.review_schedule", _ecols("reserve.review_schedule"), width=500,
             size=25, head_fill=TEAL, subtitle=f"Claims Hub · {svc}")
    E.relation("CLR.T_RESERVE_MOVEMENT", "RSV_ID", "CLR.T_RESERVE", "RSV_ID", sides="lr")
    # world-documented mapping only: outstanding_amount maps from RSV_OUTSTANDING_AMT
    y0 = E.rows[("CLR.T_RESERVE", "RSV_OUTSTANDING_AMT")]
    y1 = E.rows[("reserve.reserve", "outstanding_amount")]
    E.polyline([(880, y0), (920, y0), (920, 200), (2010, 200), (2010, y1), (2060, y1)], fill=AMBER, width=4, dash=(16, 10))
    E.label(1460, 200, "maps to: RSV_OUTSTANDING_AMT → outstanding_amount", 26, outline=AMBER)
    E.label(2380, 1520, "amount_minor BIGINT — amount in minor units (pence / øre)", 28, bold=True, bg="#FFF6E0",
            outline=AMBER, pad=12)
    E.label(2380, 1640, "source values: CLAIMS_HUB or CLARA_BRIDGE", 28, bold=True, bg="#FFF6E0", outline=AMBER, pad=12)
    E.legend(60, 1620, [(core.LEGACY, "CLARA DB2 table"), (TEAL, "Claims Hub PostgreSQL table"), (AMBER, "Documented mapping")],
             cols=3, col_w=560, size=24)
    E.flush_labels()
    P.add_image(E.img, "ERD poster — reserve data (CLARA and Claims Hub)",
                facts=[placement_spec(pl, "amount_minor BIGINT"),
                       spec("image_text", "reserve.reserve.outstanding_amount maps from CLR.T_RESERVE.RSV_OUTSTANDING_AMT.",
                            "RSV_OUTSTANDING_AMT → outstanding_amount", "TABLE:reserve.reserve#columns.outstanding_amount"),
                       spec("image_text", "reserve.reserve_movement.source distinguishes CLAIMS_HUB from CLARA_BRIDGE "
                                          "movements (column source VARCHAR(16)).", "source values: CLAIMS_HUB or CLARA_BRIDGE",
                            "TABLE:reserve.reserve_movement#columns.source"),
                       spec("temporal", f"In March 2025 the reserve service is named {svc}.", f"Claims Hub · {svc}",
                            "SERVICE:reserve-engine#renames")])
    # page 2: claim and fraud
    E = ERD(P.W, P.H - 64)
    E.title_band("Claim and fraud data: CLARA and Claims Hub", "Claim header and fraud referral tables",
                 h=150, size=48, sub_size=28, right="ERD poster")
    E.ROW, E.HEAD = 44, 70
    E.entity("CLR.T_CLAIM", 60, 230, "CLR.T_CLAIM", _ecols("CLR.T_CLAIM"), width=800, size=25, head_fill=core.LEGACY,
             subtitle="CLARA · copybook CLRCLM01")
    E.entity("claim_core.claim", 1000, 230, "claim_core.claim", _ecols("claim_core.claim"), width=700, size=25,
             head_fill=TEAL, subtitle="Claims Hub · claim-core-svc")
    E.entity("CLR.T_FRAUD_REFERRAL", 1840, 230, "CLR.T_FRAUD_REFERRAL", _ecols("CLR.T_FRAUD_REFERRAL"), width=780,
             size=23, head_fill=core.LEGACY, subtitle="CLARA · copybook FRDREF01")
    E.entity("fraud.referral", 2700, 230, "fraud.referral", _ecols("fraud.referral"), width=560, size=24, head_fill=TEAL,
             subtitle="Claims Hub · fraud-referral-svc")
    y0 = E.rows[("CLR.T_CLAIM", "CLAIM_ID")]
    y1 = E.rows[("claim_core.claim", "legacy_claim_id")]
    E.polyline([(860, y0), (930, y0), (930, y1), (1000, y1)], fill=AMBER, width=4, dash=(16, 10))
    E.label(1350, 1500, "claim_core.claim.legacy_claim_id holds the CLARA CLAIM_ID", 27, bold=True, bg="#FFF6E0",
            outline=AMBER, pad=12)
    E.flush_labels()
    P.add_image(E.img, "ERD poster — claim and fraud data",
                facts=[spec("image_text", "claim_core.claim.legacy_claim_id holds the CLARA CLAIM_ID.", "legacy_claim_id",
                            "TABLE:claim_core.claim#columns.legacy_claim_id"),
                       spec("image_text", "fraud.referral includes threshold_applied and sentinel_score columns.",
                            "threshold_applied", "TABLE:fraud.referral#columns")])
    return P.save()


# ==========================================================================================
# VS049 Tier Decision Tree Poster (2025-01-06, P011)
# ==========================================================================================
def build_vs049():
    fid = "VS049"
    P = PdfFile(fid, A3_LAND, "CM-OPS-TD-049", "3.0")
    d = P.d
    v = W.rule_version("BR-TRI-003", d)
    assert v["version"] == 3
    guard(fid, "RULE:BR-TRI-003@v3", "parameters")
    pr = v["parameters"]
    v6 = W.rule_version("BR-TRI-006", d)
    pl = placement(fid, "vs49_nordic")
    D = Diagram(P.W, P.H - 64)
    D.title_band("Claim tier decision tree", f"BR-TRI-003 v3 · effective {v['effective_from']}", h=150, size=50, sub_size=28,
                 right=f"Approved {fmt_date_short(d)}")
    qx0, qx1 = 900, 1700
    qs = [("q1", "Any bodily injury?"), ("q2", "Solicitor or litigation involved at notification?"),
          ("q3", "Property total loss?"),
          ("q4", f"Estimated incurred ≥ £{pr['tier3_min_gbp']:,}?")]
    y, qh, step = 180, 260, 300
    for qid, txt in qs:
        D.node(qid, (qx0, y, qx1, y + qh), txt, "warn", shape="diamond", size=30, bold_first=False)
        y += step
    D.node("t3", (2150, 590, 3200, 930), "TIER-3\nroute to Major & Complex Loss within 4 hours (BR-TRI-004)", "alert", size=32)
    t3_mid = (590 + 930) / 2
    for qid, _ in qs:
        yy = (D.nodes[qid][1] + D.nodes[qid][3]) / 2
        D.edge(qid, "t3", "Yes", sides="rl", label_size=28, label_bold=True, width=5, boff=(yy - t3_mid) * 0.4,
               label_xy=(1830, yy))
    for a, b in (("q1", "q2"), ("q2", "q3"), ("q3", "q4")):
        D.edge(a, b, "No", sides="bt", label_size=28, label_bold=True, width=5)
    # Tier-2 test sits directly under the last Tier-3 question; Tier-2 to its left, Tier-1 below it
    D.node("q5", (qx0, y, qx1, y + qh), f"£{pr['tier2_min_gbp']:,} or more, or any third party?", "warn",
           shape="diamond", size=29, bold_first=False)
    D.edge("q4", "q5", "No", sides="bt", label_size=28, label_bold=True, width=5)
    D.node("t2", (60, y + 20, 760, y + qh - 20), "TIER-2\nspecialist claim handlers", "target", size=32)
    t_y = y + qh + 60
    D.node("t1", (qx0, t_y, qx1, t_y + 200), "TIER-1\nfast track if eligible", "platform", size=32)
    D.edge("q5", "t2", "Yes", sides="lr", label_size=28, label_bold=True, width=5)
    D.edge("q5", "t1", "No", sides="bt", label_size=28, label_bold=True, width=5)
    D.label(2675, 1010, f"NOK {pr['tier3_min_nok']:,} / SEK {pr['tier3_min_sek']:,} / DKK {pr['tier3_min_dkk']:,}", 32,
            bold=True, bg="#FFF6E0", outline=AMBER, pad=14)
    D.text(2675, 1070, "Nordic claims are tiered on the local-currency amount (BR-TRI-015)", 26, fill=INK2, anchor="ma")
    D.node("notes", (2000, 1200, 3240, 1520), "Always Tier-3: public liability claims involving injury (BR-TRI-019).\n"
           "Business Interruption claims are always Tier-2 or above (BR-TRI-013).", "note", size=26, bold_first=False)
    D.node("ft", (2000, t_y, 3240, t_y + 200), f"Fast track (BR-TRI-006 v{v6['version']}): Tier-1, FRAUDNET score below 30, "
           f"no injury, cap £1,500", "platform", size=28, bold_first=False)
    D.edge("t1", "ft", "eligible?", sides="rl", label_size=26)
    D.flush_labels()
    P.add_image(D.img, "Claim tier decision tree poster — page 1 of 2",
                facts=[placement_spec(pl, f"NOK {pr['tier3_min_nok']:,} / SEK {pr['tier3_min_sek']:,} / DKK {pr['tier3_min_dkk']:,}"),
                       spec("image_text", "Tier-3 if estimated incurred is £50,000 or more (BR-TRI-003 v3).",
                            "Estimated incurred ≥ £50,000?", "RULE:BR-TRI-003@v3#parameters.tier3_min_gbp"),
                       spec("image_text", "Fast track in January 2025: Tier-1, FRAUDNET score below 30, no injury, cap £1,500 "
                                          "(BR-TRI-006 v2).", "cap £1,500", "RULE:BR-TRI-006@v2"),
                       spec("image_text", "Public liability claims involving injury are always Tier-3 (BR-TRI-019).",
                            "BR-TRI-019", "RULE:BR-TRI-019@v1")])
    # page 2: threshold history and routing
    c = P.canvas("Tier thresholds and routing", "How the Tier-3 threshold has changed and where each tier goes",
                 right="BR-TRI-003 · BR-TRI-004")
    rows = []
    for vv in W.rules["BR-TRI-003"]["versions"]:
        prm = vv["parameters"]
        nordic = (f"NOK {prm['tier3_min_nok']:,} / SEK {prm['tier3_min_sek']:,} / DKK {prm['tier3_min_dkk']:,}"
                  if "tier3_min_nok" in prm else "–")
        rows.append([f"v{vv['version']}", vv["effective_from"], vv["effective_to"] or "current",
                     f"£{prm['tier3_min_gbp']:,}", nordic, vv["status"]])
    tim = table_image(["Version", "From", "To", "Tier-3 (GBP)", "Tier-3 (Nordic)", "Status"], rows,
                      [210, 300, 300, 330, 900, 300], size=30, title="Tier-3 monetary threshold history (BR-TRI-003)",
                      title_size=36)
    c.paste(tim.img, 60, 190)
    rows = [["Tier-3", "Major & Complex Loss", "within 4 hours"], ["Tier-2", "Specialist claim handlers", "–"],
            ["Tier-1", "Fast-track queue when BR-TRI-006 is met", "–"], ["Nordic (any tier)", "Claims Operations Nordics", "BR-TRI-005"]]
    tim = table_image(["Tier", "Routed to", "Note"], rows, [400, 1300, 500], size=30, title="Routing (BR-TRI-004)",
                      title_size=36)
    c.paste(tim.img, 60, 1100)
    P.add(c, "Claim tier decision tree poster — page 2 of 2",
          facts=[spec("image_table", "BR-TRI-003 v2 (2022-01-01 to 2024-12-31) set Tier-3 at £40,000; superseded by v3 "
                                     "(£50,000) from 2025-01-01.", "£40,000", "RULE:BR-TRI-003@v2#parameters"),
                 spec("image_table", "Nordic claims route to Claims Operations Nordics (BR-TRI-005).",
                      "Claims Operations Nordics", "RULE:BR-TRI-005@v1")])
    return P.save()


# ==========================================================================================
# VS050 Programme Skerry Roadmap Poster (2026-09-21, P048)
# ==========================================================================================
def build_vs050():
    fid = "VS050"
    P = PdfFile(fid, A3_LAND, "CM-PGM-RM-050", "4.0")
    d = P.d
    guard(fid, "TIMELINE:programme", "clara_decommission_target")
    guard(fid, "TIMELINE:programme", "parallel_run.from")
    pl = placement(fid, "vs50_roadmap")
    pg = W.timeline["programme"]
    T = Timeline(P.W, P.H - 64, "2025-01-01", "2027-12-31", left=430, top=330, title="Programme Skerry roadmap",
                 subtitle="CLARA to Claims Hub · milestones, waves and retirements", right_note=f"Issued {fmt_date_short(d)}",
                 axis_size=24)
    rows = [("Programme", 330, 640), ("Migration waves", 640, 960), ("Reserving", 960, 1180),
            ("Integration", 1180, 1440), ("Regulatory", 1440, 1700), ("Legacy retirement", 1700, 2080)]
    for k, (nm, y0, y1) in enumerate(rows):
        T.lane(y0, y1, nm, fill="#F7F9FC" if k % 2 == 0 else WHITE, size=28)
    T.milestone(pg["ibm_engagement_start"], 560, "IBM engagement starts\n2025-01-13", NAVY2, size=26, align="l", dx=-14)
    T.milestone(pg["mvp"], 560, "Claims Hub MVP live\n2025-11-03", NAVY2, size=26)
    T.milestone(pg["wave0"], 880, "Wave 0 Denmark\n2026-06-01", TEAL, size=26, align="r", dx=14)
    T.milestone(pg["wave1"], 880, "Wave 1 UK motor\n2026-09-14", TEAL, size=26, align="l", dx=-14)
    w2_known = WD.date_known(W, "MW-2", d)   # date fixed only by DEC-011 (2026-10-08)
    T.milestone(pg["wave2"], 880, f"Wave 2 (planned)\n{pg['wave2'] if w2_known else WD.tbc_label(W, 'MW-2', short=True)}",
                AMBER, size=26)
    T.bar(pg["parallel_run"]["from"], pg["parallel_run"]["to"], 1070, "Reserve parallel run", "service", h=70, size=26)
    T.text(T.x(pg["parallel_run"]["from"]), 1125, f"{pg['parallel_run']['from']} to {pg['parallel_run']['to']}", 24,
           fill=INK2)
    T.milestone(W.interfaces["CLX-IF-049"]["since"], 1370, "CLX-IF-049 Kafka bridge live\n2025-12-12", GREEN, size=25)
    T.milestone(W.interfaces["CLX-IF-060"]["since"], 1370, "CLX-IF-060 regulatory\nextracts (planned 2027-01-11)", AMBER,
                size=25, align="l", dx=-14)
    T.milestone("2026-04-01", 1630, "NISA Circular 2026/04\neffective 2026-04-01", PURPLE, size=25)
    T.milestone("2026-07-30", 1630, "First NISA-FR1 return\ndue 2026-07-30", PURPLE, size=25, align="l", dx=-14)
    T.milestone(W.adrs["ADR-022"]["consequences"].split()[-1].rstrip("."), 1880, "SUBTRAK retired 2026-12-31", RED,
                size=28, align="r", dx=14)
    T.milestone(pg["clara_decommission_target"], 1880, "CLARA decommission 2027-09-30", RED, size=28)
    T.today_line(d, f"Today {fmt_date_short(d)}", size=24)
    P.add_image(T.img, "Programme Skerry roadmap — page 1 of 2",
                facts=[placement_spec(pl, "CLARA decommission 2027-09-30"),
                       spec("image_text", "Roadmap label: SUBTRAK retired 2026-12-31 (ADR-022 target).",
                            "SUBTRAK retired 2026-12-31", "ADR:ADR-022#consequences"),
                       spec("image_text", f"The roadmap shows Wave 2 planned for {pg['wave2']}." if w2_known else
                            f"The roadmap (issued {d}) shows Wave 2 planned for early 2027, date to be confirmed "
                            f"(confirmed later by DEC-011).", "Wave 2 (planned)",
                            "TIMELINE:programme#wave2" if w2_known else "DECISION:DEC-011"),
                       spec("image_text", "CLX-IF-049 Kafka bridge went live on 2025-12-12.", "CLX-IF-049 Kafka bridge live",
                            "INTERFACE:CLX-IF-049#since")])
    # page 2: waves table
    c = P.canvas("Migration waves", "Scope, cut-over date, freeze and rehearsals", right=f"As at {fmt_date_short(d)}")
    rows = []
    for wid in ("MW-0", "MW-1", "MW-2"):
        w = W.waves[wid]
        status = w["status"] if str(w["date"]) <= d else "planned"
        if WD.date_known(W, wid, d):
            rows.append([w["name"], w["date"], w["scope"], w.get("freeze", "–"), str(w.get("rehearsals", "–")), status])
        else:
            rows.append([w["name"], WD.tbc_label(W, wid, short=True), w["scope"], "TBC", str(w.get("rehearsals", "–")),
                         status])
    tim = table_image(["Wave", "Cut-over", "Scope", "Freeze", "Rehearsals", "Status"], rows,
                      [520, 260, 1060, 640, 220, 220], size=28, title="", line_gap=0.3)
    P.fit(c, tim.img, top=200)
    P.add(c, "Programme Skerry roadmap — page 2 of 2",
          facts=[spec("image_table", "Wave 1 freeze: 2026-09-11 18:00 to 2026-09-14 06:00.", "2026-09-11 18:00",
                      "WAVE:MW-1#freeze"),
                 spec("image_table", "Wave 2 scope: PRD-HOM-UK, PRD-COM-UK, PRD-LIA-UK, PRD-MOT-NO, PRD-HOM-NO, PRD-MOT-SE, "
                                     "PRD-HOM-SE.", "PRD-COM-UK", "WAVE:MW-2#scope")])
    return P.save()

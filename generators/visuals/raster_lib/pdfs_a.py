"""Raster PDF / poster builders VS040-VS044."""
from __future__ import annotations

from PIL import Image

from . import charts, core
from .core import (AMBER, BLUE_L, GREEN, GREY_L, GRID, INK, INK2, LINE, MUTED, NAVY, NAVY2, PURPLE, RED, TEAL, WHITE,
                   Canvas, fmt_date_long, fmt_date_short)
from .ctx import W, adate, anchor, guard, name, out_path, placement, rel, sysname, svcname, team_name, title
from .diagrams import Diagram, Swimlane, Timeline, org_chart, table_image
from .facts import Facts, chart_spec, placement_spec, spec
from .pdf_kit import A3_LAND, A4_LAND, build_raster_pdf, page_pixels


class PdfFile:
    """Collects raster pages and their facts for one PDF."""

    def __init__(self, fid: str, page_size, doc_id: str, version: str):
        self.fid = fid
        self.d = adate(fid)
        self.a = anchor(fid)
        self.facts = Facts(fid, rel(fid))
        self.page_size = page_size
        self.W, self.H = page_pixels(page_size)
        self.doc_id, self.version = doc_id, version
        self.pages: list[tuple[Image.Image, str]] = []

    def canvas(self, title_: str, subtitle: str = "", right: str = "", bg: str = WHITE) -> Canvas:
        c = Diagram(self.W, self.H, bg)
        c.title_band(title_, subtitle, h=150, size=50, sub_size=28, right=right)
        return c

    def footer(self, c: Canvas) -> None:
        a = self.a
        c.footer_band(f"{self.doc_id} · Version {self.version} · {a['status'].capitalize()} {fmt_date_short(self.d)} · "
                      f"Owner {name(a['author'], self.d)} · Corvane Internal", f"Page {len(self.pages) + 1}",
                      h=64, size=24)

    def add(self, c: Canvas, text_title: str, facts=()) -> int:
        self.footer(c)
        if isinstance(c, Diagram):
            c.flush_labels()
        n = len(self.pages) + 1
        self.pages.append((c.img, text_title))
        for f in facts:
            loc = {"kind": "pdf_page", "page": n, "ocr": f.get("ocr", True)}
            self.facts.add(f["kind"], f["statement"], f["needle"], loc, world_ref=f.get("world_ref"),
                           exclusive=f.get("exclusive", False), placement=f.get("placement"),
                           placement_key=f.get("placement_key"), also_in=f.get("also_in"), notes=f.get("notes"))
        return n

    def add_image(self, im: Image.Image, text_title: str, facts=()) -> int:
        c = Canvas(self.W, self.H)
        c.paste(im, 0, 0)
        return self.add(c, text_title, facts)

    def fit(self, c: Canvas, im: Image.Image, top: int = 170, bottom: int = 80, margin: int = 30,
            valign: str = "middle") -> tuple:
        aw, ah = self.W - 2 * margin, self.H - top - bottom
        s = min(aw / im.width, ah / im.height)
        w, h = int(im.width * s), int(im.height * s)
        x = (self.W - w) // 2
        y = top if valign == "top" else top + (ah - h) // 2
        c.paste(im.resize((w, h), Image.LANCZOS) if s != 1 else im, x, y)
        return (x, top, s)

    def save(self) -> tuple[list[dict], str, int]:
        a = self.a
        # one text-layer fact: the title band of page 1 is real text
        self.facts.add("general", f"{a['title']} carries the title '{self.pages[0][1]}' in its PDF text layer.",
                       self.pages[0][1], {"kind": "pdf_page", "page": 1, "ocr": False}, world_ref=f"ANCHOR:{self.fid}#title")
        path = out_path(self.fid)
        build_raster_pdf(path, self.pages, self.page_size, a["title"], name(a["author"], self.d), a["title"], self.d,
                         keywords="Corvane Mutual; Programme Skerry")
        return self.facts.items, str(path), len(self.pages)


def _svc_owner_team(svc: str, d: str) -> str:
    o = W.service_owner(svc, d)
    return team_name(o["team"], d) if o else ""


# ==========================================================================================
# VS040 Target Architecture Poster (2026-03-16, P049)
# ==========================================================================================
def build_vs040():
    fid = "VS040"
    P = PdfFile(fid, A3_LAND, "CM-ARC-TP-040", "1.0")
    d = P.d
    guard(fid, "SYSTEM:SYS02", "hosting")
    pl = placement(fid, "vs40_ocp")
    c = P.canvas("Claims Hub target architecture", "Programme Skerry · target state for Wave 1 and Wave 2",
                 right=f"Approved {fmt_date_short(d)}")
    Wd = P.W
    # channels
    c.zone((40, 220, Wd - 40, 420), "Channels and partners", fill="#F3F6FA", outline=NAVY2)
    chans = [("SYS04", "customers"), ("SYS12", "contact centre"), ("SYS17", "assessors and partners"),
             ("SYS13", "photos and telematics"), ("SYS20", "vehicle lookup")]
    x = 90
    for k, (sid, sub) in enumerate(chans):
        c.node(f"ch{k}", (x, 270, x + 560, 390), f"{sysname(sid, d)}\n{sub}", "external", size=27)
        x += 630
    # Claims Hub zone
    c.zone((40, 480, 2280, 1500), "Claims Hub on OpenShift — clusters ocp-prd-lon1 (primary) and ocp-dr-lds1 (DR)",
           fill="#EEF5FB", outline=NAVY2)
    svcs = sorted(W.services.values(), key=lambda s: s["id"])
    cols, cw, ch = 4, 520, 150
    for k, s in enumerate(svcs):
        r_, c_ = divmod(k, cols)
        x0, y0 = 90 + c_ * (cw + 30), 560 + r_ * (ch + 28)
        c.node(s["id"], (x0, y0, x0 + cw, y0 + ch), f"{svcname(s['name'], d)}\n{_svc_owner_team(s['name'], d)}",
               "service", size=25)
    c.label(1160, 1460, "PostgreSQL 16 · one database per service (ADR-003) · Java 21 / Spring Boot", 26, bold=True,
            outline=GRID)
    # right column: platform
    c.zone((2340, 480, Wd - 40, 1500), "Platform", fill="#EEF6EE", outline=GREEN)
    plat = [("SYS15", "Apache Kafka (Strimzi), 6 brokers"), ("SYS14", "CLRQM01 / HUBQM01"), ("SYS16", "OIDC for workforce and partners"),
            ("SYS05", "documents behind document-svc")]
    y = 560
    for k, (sid, sub) in enumerate(plat):
        c.node(f"pl{k}", (2390, y, Wd - 90, y + 190), f"{sysname(sid, d)}\n{sub}", "platform", size=26)
        y += 225
    # enterprise systems
    c.zone((40, 1560, Wd - 40, 2080), "Enterprise and legacy systems", fill="#F7F4EE", outline=core.LEGACY)
    ent = [("SYS01", "system of record for unmigrated claims until 2027-09-30"), ("SYS03", "REST scoring, 800 ms timeout"),
           ("SYS25", "letters, SMS, email"), ("SYS09", "ISO 20022 payments"), ("SYS06", "journals"),
           ("SYS08", "policy API"), ("SYS11", "analytics"), ("SYS10", "regulatory returns")]
    x = 80
    for k, (sid, sub) in enumerate(ent):
        r_, c_ = divmod(k, 4)
        x0, y0 = 80 + c_ * 790, 1610 + r_ * 225
        c.node(f"en{k}", (x0, y0, x0 + 740, y0 + 190), f"{sysname(sid, d)}\n{sub}", "legacy" if sid == "SYS01" else "external",
               size=25)
    P.add(c, "Claims Hub target architecture — page 1 of 2",
          facts=[placement_spec(pl, "ocp-prd-lon1 (primary) and ocp-dr-lds1 (DR)"),
                 spec("image_text", "The target architecture shows 13 Claims Hub services including reserve-engine "
                                    "(renamed from reserve-svc on 2026-02-10).", "reserve-engine", "SYSTEM:SYS02#description"),
                 spec("image_text", "Event Streaming Platform: Apache Kafka (Strimzi), 6 brokers.", "6 brokers",
                      "SYSTEM:SYS15#tech"),
                 spec("image_text", "CLARA stays the system of record for unmigrated claims until 2027-09-30.",
                      "until 2027-09-30", "ADR:ADR-001#consequences")])
    # page 2: service catalogue
    c = P.canvas("Claims Hub service catalogue", "Services, owning squads, namespaces and events", right=f"As at {fmt_date_short(d)}")
    rows = []
    for s in svcs:
        nm = svcname(s["name"], d)
        o = W.service_owner(s["name"], d)
        rows.append([s["id"], nm, team_name(o["team"], d), s["k8s_namespace"], ", ".join(s["kafka_topics"].get("produces", [])) or "–",
                     ", ".join(s["postgres_tables"])])
    tim = table_image(["ID", "Service", "Owning squad", "Namespace", "Produces", "Tables"], rows,
                      [110, 330, 560, 260, 700, 1100], size=22, title="")
    P.fit(c, tim.img, top=180)
    P.add(c, "Claims Hub service catalogue — page 2 of 2",
          facts=[spec("image_table", "reserve-engine runs in namespace chub-reserve and produces reserve.changed.v2.",
                      "chub-reserve", "SERVICE:reserve-engine#k8s_namespace"),
                 spec("image_table", f"recovery-svc is owned by {team_name(W.service_owner('recovery-svc', d)['team'], d)} "
                                     f"on 2026-03-16.", "recovery.recovery_case", "SERVICE:recovery-svc#owner_history"),
                 spec("image_table", "claim-core-svc owns tables claim_core.claim and claim_core.party.", "claim_core.party",
                      "SERVICE:claim-core-svc#postgres_tables")])
    return P.save()


# ==========================================================================================
# VS041 Subrogation Process Poster (2025-10-13, P013)
# ==========================================================================================
def build_vs041():
    fid = "VS041"
    P = PdfFile(fid, A3_LAND, "CM-REC-PP-041", "1.0")
    d = P.d
    guard(fid, "RULE:BR-REC-009@v1", "parameters")
    pl = placement(fid, "vs41_limitation")
    owner = W.owner_of_process("S7", d)
    S = Swimlane(P.W, ["Claims Assessor / claim handler", f"Recoveries & Subrogation\n(owner {name(owner, d)})",
                       "SUBTRAK / CLARA", "Quarryhill Solicitors", "Salvanta Salvage"], lane_h=330, top=180, left=380,
                 title="Recovery & Subrogation process", subtitle=f"Stage S7 · {name(owner, d)}, {title(owner, d)}",
                 right_note=f"Approved {fmt_date_short(d)}", lane_size=28, bottom=110)
    S.fit_cols(6)
    S.step("s", 0, 0, "Third party wholly or partly at fault", "start", size=26)
    S.step("a", 0, 1, "Flag recovery potential (PS-REC-01, within 10 business days)", size=25, w=380, h=170)
    S.step("b", 1, 2, "Open subrogation case and set limitation diary", size=25, w=380, h=170)
    S.step("q", 1, 3.1, "Recoverable ≥ £1,000?", "decision", size=25, w=330, h=150)
    S.step("c", 1, 4.2, "Send demand within 10 business days; chase at 28 days", size=25, w=380, h=170)
    S.step("l", 3, 4.2, "Litigation: ≥ £25,000 or liability defended", size=25, w=380, h=170)
    S.step("r", 2, 5.3, "Receipt posted; reserve adjusted within 2 business days", "system", size=24, w=380, h=170)
    S.step("w", 2, 3.1, "Close or write off (> £10,000 needs Head of R&S)", "system", size=24, w=380, h=170)
    S.step("v", 4, 2.2, "Total-loss vehicle released within 5 business days", size=25, w=380, h=170)
    S.edge("s", "a", width=5)
    S.edge("a", "b", sides="bl", width=5)
    S.edge("b", "q", width=5)
    S.edge("q", "c", "Yes", label_size=26, width=5)
    S.edge("q", "w", "No", sides="bt", label_size=26, width=5)
    S.edge("c", "l", "≥ £25,000 or defended", sides="bt", label_size=25, width=5)
    S.edge("c", "r", sides="rt", width=5)
    S.edge("a", "v", "total loss", sides="bt", aoff=-120, label_size=25, width=5)
    S.label(P.W / 2, S.h - 50, "Limitation diary at 30 months (bodily injury) and 66 months (property)", 32, bold=True,
            bg="#FFF6E0", outline=AMBER, pad=14)
    S.flush_labels()
    im = S.img
    c = Canvas(P.W, P.H)
    c.paste(im.resize((P.W, min(P.H - 64, int(im.height * P.W / im.width)))), 0, 0)
    P.add(c, "Recovery & Subrogation process poster — page 1 of 2",
          facts=[placement_spec(pl, "Limitation diary at 30 months (bodily injury) and 66 months (property)"),
                 spec("image_text", "Pursue subrogation when the recoverable amount is £1,000 or more (BR-REC-003 v3).",
                      "Recoverable ≥ £1,000?", "RULE:BR-REC-003@v3"),
                 spec("image_text", f"The S7 process owner on the poster is {name(owner, d)}, {title(owner, d)}.",
                      f"{name(owner, d)}, {title(owner, d)}", "PROCESS:S7#owner_history"),
                 spec("lane_only", "Total-loss vehicles are released to Salvanta Salvage within 5 business days (lane: Salvanta Salvage).",
                      "Total-loss vehicle released within 5 business days", "RULE:BR-REC-007@v1")])
    # page 2: rules cards
    c = P.canvas("Recovery rules in force", f"Recovery & Subrogation rules on {fmt_date_long(d)}", right="BR-REC")
    rules = []
    for rid in sorted(W.rules):
        r = W.rules[rid]
        if r["area"] != "REC":
            continue
        v = W.rule_version(rid, d)
        if v:
            guard(fid, f"RULE:{rid}@v{v['version']}", "text")
            rules.append((rid, v))
    cols, cw, chh = 3, 1040, 300
    for k, (rid, v) in enumerate(rules):
        r_, c_ = divmod(k, cols)
        x0, y0 = 40 + c_ * (cw + 30), 190 + r_ * (chh + 18)
        if y0 + chh > P.H - 90:
            break
        c.rect((x0, y0, x0 + cw, y0 + chh), fill=WHITE, outline=PURPLE, width=3, radius=14)
        c.text(x0 + 22, y0 + 18, f"{rid} v{v['version']}", 27, True, fill=PURPLE)
        c.text_in_box((x0 + 6, y0 + 64, x0 + cw - 6, y0 + chh - 6), v["text"], 26, align="left", valign="top", pad=16,
                      min_size=20)
    P.add(c, "Recovery rules in force — page 2 of 2",
          facts=[spec("image_text", "Write-offs of recoveries above £10,000 require the Head of Recoveries & Subrogation "
                                    "(BR-REC-011 v2).", "above £10,000", "RULE:BR-REC-011@v2"),
                 spec("image_text", "Unanswered subrogation demands are chased at 28 days (BR-REC-012).", "chased at 28 days",
                      "RULE:BR-REC-012@v1")])
    return P.save()


# ==========================================================================================
# VS042 KPI Report Charts – Q3 2026 (2026-10-14, P036)
# ==========================================================================================
def build_vs042():
    fid = "VS042"
    P = PdfFile(fid, A4_LAND, "CM-DAT-KPI-2026Q3", "1.0")
    d = P.d
    for f in ("fraud_referrals_count", "wave1_open_defects", "tier3_share_pct"):
        guard(fid, "TIMELINE:metrics", f)
    m = W.timeline["metrics"]
    pl = placement(fid, "vs42_fr_q3")
    # page 1: tiles
    c = P.canvas("KPI report charts — Q3 2026", "Claims and programme indicators", right=f"Issued {fmt_date_short(d)}",
                 bg="#F4F6F9")
    dfx = m["wave1_open_defects"]
    tiles = [("Wave 1 UK motor cut-over", "Complete", f"cut-over {W.waves['MW-1']['date']}"),
             ("Open Wave 1 defects", str(dfx["sev1"] + dfx["sev2"] + dfx["sev3"]), f"at {dfx['date']} (all severities)"),
             ("Tier-3 share of claims, 2025", f"{m['tier3_share_pct']['2025']}%", "full year 2025"),
             ("Wave 2 cut-over (planned)", W.waves["MW-2"]["date"], "UK home, commercial, liability; Norway; Sweden")]
    for k, (lab, val, sub) in enumerate(tiles):
        r_, c_ = divmod(k, 2)
        x0, y0 = 60 + c_ * 1130, 220 + r_ * 640
        c.rect((x0, y0, x0 + 1090, y0 + 600), fill=WHITE, outline=GRID, width=2, radius=16)
        c.text(x0 + 40, y0 + 40, lab, 34, True, fill=INK2)
        c.text(x0 + 40, y0 + 150, val, 96, True, fill=NAVY)
        c.text_in_box((x0 + 20, y0 + 380, x0 + 1070, y0 + 580), sub, 32, fill=MUTED, align="left", valign="top", pad=20)
    P.add(c, "KPI report charts — Q3 2026 — summary",
          facts=[spec("image_text", "Open Wave 1 defects at 2026-10-05: 71 across all severities.", "71",
                      "TIMELINE:metrics#wave1_open_defects", notes="0 Sev1 + 14 Sev2 + 57 Sev3"),
                 spec("image_text", "Tier-3 share of claims in 2025: 4.1%.", "4.1%", "TIMELINE:metrics#tier3_share_pct")])
    # page 2: fraud referrals chart (placement)
    c = P.canvas("Fraud referrals", "Referrals to SIU per quarter", right="Source: fraud-referral-svc and CLARA")
    fr = m["fraud_referrals_count"]
    im = charts.bar_chart(["Q2 2026", "Q3 2026"], [fr["2026Q2"], fr["2026Q3"]], title="Fraud referrals per quarter",
                          ylabel="Referrals", value_labels=[f"Q2 2026: {fr['2026Q2']:,}", f"Q3 2026: {fr['2026Q3']:,}"],
                          colors=[charts.SERIES[0], charts.SERIES[1]], w_in=12, h_in=6.4, ylim=(0, 1800), annotate_size=19)
    P.fit(c, im, top=180)
    P.add(c, "KPI report charts — Q3 2026 — fraud referrals",
          facts=[placement_spec(pl, "Q3 2026: 1,530", also_in_ids=[
                     "ST034-F001", "ST038-F001", "corpus/upload/structured/ST034_nisa_fr1_2026q3_payload.json",
                     "corpus/upload/structured/ST038_nisa_fr1_return_2026q2.xml"]),
                 chart_spec("Fraud referrals Q2 2026: 1,488.", "Q2 2026: 1,488", "TIMELINE:metrics#fraud_referrals_count")])
    # page 3: defects
    c = P.canvas("Wave 1 open defects", f"Open defects by severity at {dfx['date']}", right="Programme Skerry")
    im = charts.bar_chart(["Sev1", "Sev2", "Sev3"], [dfx["sev1"], dfx["sev2"], dfx["sev3"]],
                          title=f"Open Wave 1 defects by severity ({dfx['date']})", ylabel="Open defects",
                          value_labels=[f"Sev1: {dfx['sev1']}", f"Sev2: {dfx['sev2']}", f"Sev3: {dfx['sev3']}"],
                          colors=[charts.SERIES[4], charts.SERIES[2], charts.SERIES[0]], w_in=12, h_in=6.4, ylim=(0, 70),
                          annotate_size=19)
    P.fit(c, im, top=180)
    P.add(c, "KPI report charts — Q3 2026 — Wave 1 defects",
          facts=[chart_spec("Open Wave 1 defects at 2026-10-05: Sev1 0, Sev2 14, Sev3 57.", "Sev3: 57",
                      "TIMELINE:metrics#wave1_open_defects"),
                 chart_spec("No Sev1 defects were open on 2026-10-05.", "Sev1: 0", "TIMELINE:metrics#wave1_open_defects")])
    # page 4: milestones
    T = Timeline(P.W, P.H - 64, "2025-01-01", "2027-06-30", left=360, top=330, title="Programme milestones",
                 subtitle="Delivered and planned", right_note=f"As at {fmt_date_short(d)}")
    pg = W.timeline["programme"]
    T.lane(330, 760, "Programme", fill="#F7F9FC")
    T.milestone(pg["ibm_engagement_start"], 640, "IBM engagement\n2025-01-13", NAVY2, size=26, align="l", dx=-10)
    T.milestone(pg["mvp"], 640, "MVP live\n2025-11-03", NAVY2, size=26)
    T.lane(760, 1300, "Migration waves", fill=WHITE)
    T.milestone(pg["wave0"], 1150, "Wave 0 Denmark\n2026-06-01", TEAL, size=26, align="r", dx=10)
    T.milestone(pg["wave1"], 1150, "Wave 1 UK motor\n2026-09-14", TEAL, size=26, align="l", dx=-10)
    T.milestone(pg["wave2"], 1150, "Wave 2 (planned)\n2027-02-15", AMBER, size=26)
    T.today_line(d, f"Report date {fmt_date_short(d)}", size=24)
    c = Canvas(P.W, P.H)
    c.paste(T.img, 0, 0)
    P.add(c, "KPI report charts — Q3 2026 — milestones",
          facts=[spec("image_text", "Wave 2 cut-over is planned for 2027-02-15.", "2027-02-15", "WAVE:MW-2#date")])
    return P.save()


# ==========================================================================================
# VS043 Interface Landscape Poster (2026-08-24, P031)
# ==========================================================================================
ABBR = {"Claims Data Warehouse": "CDW", "Actuarial Reserving Workbench": "ARW", "Group Ledger": "GL",
        "MQ Backbone": "MQ", "Event Streaming Platform": "ESP", "Evidence Intake Gateway": "EIG",
        "Corvane Payments Gateway": "CPG", "NISA Reporting Hub": "NRH", "Subrogation Tracker": "SUBTRAK",
        "SIU Case Manager": "SIU CM", "Corvane Identity Service": "CIS", "MyCorvane Claims": "MyCorvane",
        "Vehicle Data Service": "VDS", "Bordereaux Exchange": "BDX", "Mailroom Scanning": "Mailroom"}
DOMAIN = [("Intake", ["CLX-IF-001", "CLX-IF-002", "CLX-IF-003", "CLX-IF-004", "CLX-IF-005", "CLX-IF-006", "CLX-IF-007",
                      "CLX-IF-034", "CLX-IF-035", "CLX-IF-053", "CLX-IF-054", "CLX-IF-057", "CLX-IF-059", "CLX-IF-040"], "#1F4E8C"),
          ("Fraud and assessment", ["CLX-IF-008", "CLX-IF-009", "CLX-IF-010", "CLX-IF-011", "CLX-IF-012", "CLX-IF-013",
                                    "CLX-IF-014", "CLX-IF-015", "CLX-IF-016", "CLX-IF-033", "CLX-IF-036", "CLX-IF-041",
                                    "CLX-IF-037", "CLX-IF-039"], "#B3261E"),
          ("Payments and recoveries", ["CLX-IF-017", "CLX-IF-018", "CLX-IF-019", "CLX-IF-020", "CLX-IF-021", "CLX-IF-022",
                                       "CLX-IF-023", "CLX-IF-024", "CLX-IF-025", "CLX-IF-026", "CLX-IF-038", "CLX-IF-046",
                                       "CLX-IF-031", "CLX-IF-030", "CLX-IF-032", "CLX-IF-052", "CLX-IF-056"], "#5B3F95"),
          ("Reserves, finance and reporting", ["CLX-IF-027", "CLX-IF-028", "CLX-IF-029", "CLX-IF-042", "CLX-IF-043",
                                               "CLX-IF-044", "CLX-IF-045", "CLX-IF-047", "CLX-IF-048", "CLX-IF-049",
                                               "CLX-IF-050", "CLX-IF-051", "CLX-IF-055", "CLX-IF-058", "CLX-IF-060"], "#0E7C7B")]


def _ab(sid, d):
    n = sysname(sid, d)
    return ABBR.get(n, n)


def build_vs043():
    fid = "VS043"
    P = PdfFile(fid, A3_LAND, "CM-INT-LP-043", "3.0")
    d = P.d
    pl = placement(fid, "vs43_058")
    assert sorted(x for _, ids, _ in DOMAIN for x in ids) == sorted(W.interfaces), "every interface on the poster once"
    c = P.canvas("Interface landscape", f"All 60 CLARA and Claims Hub interfaces, {fmt_date_long(d)}",
                 right="Integration Platform")
    colw = (P.W - 50) // 4
    for k, (dom, ids, col) in enumerate(DOMAIN):
        x0 = 25 + k * colw
        c.rect((x0 + 8, 170, x0 + colw - 8, 226), fill=col, outline=col, radius=10)
        c.text(x0 + 24, 198, dom, 30, True, fill=WHITE, anchor="lm")
        y = 240
        hh = min(118, (P.H - 80 - 240) // len(ids) - 6)
        for iid in ids:
            i = W.interfaces[iid]
            planned = str(i["since"]) > d
            if iid == "CLX-IF-042":
                head = f"{iid} {_ab(i['source_system'], d)} → {_ab(i['target_system'], d)}"
            else:
                guard(fid, f"INTERFACE:{iid}", "schedule")
                sch = f"planned {i['since']}" if planned else W.interface_schedule(iid, d)
                head = f"{iid} {_ab(i['source_system'], d)} → {_ab(i['target_system'], d)} {sch}"
            c.rect((x0 + 8, y, x0 + colw - 8, y + hh), fill=WHITE if not planned else "#FFF8E6", outline=col, width=2,
                   radius=8, dash=(10, 6) if planned else None)
            c.text_in_box((x0 + 10, y + 2, x0 + colw - 10, y + hh - 2), f"{head}\n{i['name']} · {i['protocol']}", 22,
                          first_bold=True, align="left", pad=10, min_size=17)
            y += hh + 6
    P.add(c, "Interface landscape poster — page 1 of 2",
          facts=[placement_spec(pl, "CLX-IF-058 CDW → ARW monthly, 3rd business day"),
                 spec("image_text", "CLX-IF-043 GL Reserve Journal Feed runs daily 03:45 (since 2025-05-09).",
                      "CLX-IF-043 MQ → GL daily 03:45", "INTERFACE:CLX-IF-043#schedule_history"),
                 spec("image_text", "CLX-IF-055 Monthly Claims Bordereaux: ReCede → Bordereaux Exchange, monthly, 5th business day.",
                      "CLX-IF-055 ReCede → BDX monthly, 5th business day", "INTERFACE:CLX-IF-055#schedule"),
                 spec("image_text", "On 2026-08-24 CLX-IF-038 (Claims Hub payments to CPG) is planned for 2026-09-14.",
                      "CLX-IF-038 Claims Hub → CPG planned 2026-09-14", "INTERFACE:CLX-IF-038#since"),
                 spec("image_text", "CLX-IF-060 Claims Hub regulatory extracts is planned for 2027-01-11.",
                      "planned 2027-01-11", "INTERFACE:CLX-IF-060#since")])
    # page 2: dependency chain of 042 (no schedules)
    c = P.canvas("Reserve movement dependency chain", "What depends on CLX-IF-042 (schedules on page 1 and in the Interface Diagram Pack)",
                 right="Change impact")
    imp = W.impact("CLX-IF-042")
    c.node("r", (60, 900, 560, 1140), "CLX-IF-042\nReserve Movement Daily Extract\nCLARA → MQ Backbone", "legacy", size=28)
    ys = [260, 640, 1020, 1400]
    for iid, y in zip(imp["hops"][1], ys):
        i = W.interfaces[iid]
        c.node(iid, (900, y, 1560, y + 240), f"Hop 1 · {iid}\n{i['name']}\n→ {sysname(i['target_system'], d)}", "warn", size=27)
        c.edge("r", iid, sides="rl", width=4)
    for iid in imp["hops"][2]:
        i = W.interfaces[iid]
        y = c.nodes[i["depends_on"][0]][1]
        c.node(iid, (1880, y, 2540, y + 240), f"Hop 2 · {iid}\n{i['name']}\n→ {sysname(i['target_system'], d)}", "alert", size=27)
        c.edge(i["depends_on"][0], iid, sides="rl", width=4)
    c.node("tp2", (2800, 260, 3260, 500), "Hop 3\nNISA-TP2 return", "alert", size=28)
    c.node("ibnr", (2800, 640, 3260, 880), "Hop 3\nmonthly IBNR run (Reserving)", "alert", size=28)
    c.edge("CLX-IF-051", "tp2", sides="rl", width=4)
    c.edge("CLX-IF-058", "ibnr", sides="rl", width=4)
    teams = ", ".join(team_name(t, d) for t in imp["teams"])
    c.node("t", (1880, 1760, 3260, 2060), f"Consumer teams\n{teams}", "note", size=27)
    P.add(c, "Reserve movement dependency chain — page 2 of 2",
          facts=[spec("image_text", "Hop 2 of the CLX-IF-042 chain includes CLX-IF-058 Reserve Triangles Extract to the "
                                    "Actuarial Reserving Workbench.", "Hop 2 · CLX-IF-058", "INTERFACE:CLX-IF-058#depends_on"),
                 spec("image_text", "Hop 3 of the CLX-IF-042 chain: the NISA-TP2 return and the monthly IBNR run.",
                      "NISA-TP2 return", "REPORT:NISA-TP2#source_interfaces")])
    return P.save()


# ==========================================================================================
# VS044 Organisation Chart – October 2025 (PDF) (2025-10-06, P005)
# ==========================================================================================
def _reports(pid, d):
    out = [q for q in W.people if W.employed(q, d) and W.manager_of(q, d) == pid]
    return sorted(out, key=lambda q: (title(q, d), name(q, d)))


def _node(pid, d, depth, style):
    n = {"name": f"{name(pid, d)} — {title(pid, d)}", "title": "", "style": style(pid)}
    if depth > 0:
        n["children"] = [_node(c, d, depth - 1, style) for c in _reports(pid, d)]
    return n


def build_vs044():
    fid = "VS044"
    P = PdfFile(fid, A3_LAND, "CM-ORG-2025-10", "2025.2")
    d = P.d
    guard(fid, "PERSON:P009", "reports_to")
    pl = placement(fid, "vs44_lena")

    def style(pid):
        t = title(pid, d).lower()
        if "chief" in t:
            return "dark"
        if any(k in t for k in ("reserv", "actuar", "financ", "reinsur", "payment", "regulatory")):
            return "service"
        if any(k in t for k in ("fraud", "siu", "risk", "compliance", "data protection")):
            return "alert"
        if any(k in t for k in ("recover",)):
            return "vendor"
        return "target"

    pages = [("Executive and Finance", "P003", ["P001", "P004", "P006", "P007"], {"P001": 9, "P004": 0, "P006": 0, "P007": 0}),
             ("Claims directorate", "P005", None, None),
             ("Risk and Technology", None, ["P007", "P006"], None),
             ("Programme Skerry (IBM Consulting team)", "P047", None, None)]
    # page 1: executive + finance
    root = {"name": f"{name('P003', d)} — {title('P003', d)}", "title": "", "style": "dark"}
    cols = [_node("P001", d, 9, style), _node("P004", d, 1, style), _node("P006", d, 0, style), _node("P007", d, 0, style)]
    cv = org_chart("Organisation chart — Executive and Finance", f"Effective {fmt_date_long(d)} (after the 1 September 2025 re-organisation)",
                   root, cols, col_w=760, card_h=96, size=27, right_note="Corvane Mutual", indent=50, gap_y=26)
    c = Canvas(P.W, P.H)
    P.fit(c, cv.img, top=0, bottom=70, margin=10, valign="top")
    P.add(c, "Organisation chart — October 2025 — page 1 of 4",
          facts=[placement_spec(pl, "Lena Kristiansen — Head of Reserving",
                                notes="the reporting line to Priya Raman (CFO) is shown by the chart connector"),
                 spec("image_text", "Priya Raman is Chief Financial Officer in October 2025.", "Priya Raman — Chief Financial Officer",
                      "PERSON:P001#titles"),
                 spec("image_text", "Sebastian Moreau-Clarke (Chief Actuary) reports to the CFO in October 2025.",
                      "Sebastian Moreau-Clarke — Chief Actuary", "PERSON:P010#reports_to")])
    # page 2: claims
    cols = [_node(x, d, 9, style) for x in _reports("P005", d)]
    root = {"name": f"{name('P005', d)} — {title('P005', d)}", "title": "", "style": "target"}
    above = {"name": f"{name('P004', d)} — {title('P004', d)}", "title": "", "style": "dark"}
    cv = org_chart("Organisation chart — Claims directorate", f"Effective {fmt_date_long(d)}", root, cols, col_w=640,
                   card_h=96, size=25, above=above, right_note="Claims", indent=44, gap_y=24)
    c = Canvas(P.W, P.H)
    P.fit(c, cv.img, top=0, bottom=70, margin=10, valign="top")
    P.add(c, "Organisation chart — October 2025 — page 2 of 4",
          facts=[spec("image_text", "Freya Lindahl is Head of Recoveries & Subrogation, reporting to the Claims Director, "
                                    "in October 2025.", "Freya Lindahl — Head of Recoveries & Subrogation", "PERSON:P013#titles"),
                 spec("image_text", "The Claims Director in October 2025 is Ingrid Ashby (née Sørensen).", "Ingrid Ashby — Claims Director",
                      "PERSON:P005#name_history"),
                 spec("image_text", "Aisha Siddiqui (Head of Claims Hub Product) reports to the Claims Director from the re-org.",
                      "Aisha Siddiqui — Head of Claims Hub Product", "PERSON:P017#reports_to")])
    # page 3: risk & technology
    root = {"name": f"{name('P003', d)} — {title('P003', d)}", "title": "", "style": "dark"}
    cols = [_node("P007", d, 9, style), _node("P006", d, 9, style)]
    cv = org_chart("Organisation chart — Risk and Technology", f"Effective {fmt_date_long(d)}", root, cols, col_w=900,
                   card_h=92, size=25, right_note="Risk & Compliance · Technology", indent=44, gap_y=20)
    c = Canvas(P.W, P.H)
    P.fit(c, cv.img, top=0, bottom=70, margin=10, valign="top")
    P.add(c, "Organisation chart — October 2025 — page 3 of 4",
          facts=[spec("image_text", "Niall Brannigan, Head of Counter-Fraud & SIU, reports to the Chief Risk Officer "
                                    "after the September 2025 re-organisation.", "Niall Brannigan — Head of Counter-Fraud & SIU",
                      "PERSON:P008#reports_to"),
                 spec("image_text", "Graham Pocock is Head of Legacy Claims Platforms in October 2025.",
                      "Graham Pocock — Head of Legacy Claims Platforms", "PERSON:P016#titles")])
    # page 4: IBM team
    root = {"name": f"{name('P047', d)} — {title('P047', d)}", "title": "", "style": "dark"}
    cols = [_node(x, d, 9, style) for x in _reports("P047", d)]
    cv = org_chart("Programme Skerry — IBM Consulting team", f"Effective {fmt_date_long(d)}", root, cols, col_w=820,
                   card_h=96, size=26, right_note="External team", indent=50, gap_y=24)
    c = Canvas(P.W, P.H)
    P.fit(c, cv.img, top=0, bottom=70, margin=10, valign="top")
    P.add(c, "Organisation chart — October 2025 — page 4 of 4",
          facts=[spec("image_text", "Callum Fairbairn (IBM) is Data Migration Lead, reporting to Arjun Kesavan.",
                      "Callum Fairbairn — Data Migration Lead", "PERSON:P051#titles",
                      notes="IBM namesake (P051), not the Corvane Motor Claims Team Leader")])
    return P.save()

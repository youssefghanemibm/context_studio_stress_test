"""Image-led DOCX builders VS029-VS032."""
from __future__ import annotations

from generators.common import util

from . import charts, core, phrases
from .core import (AMBER, BLUE_L, GREEN, GREY_L, GRID, INK, INK2, LINE, MUTED, NAVY, NAVY2, RED, TEAL, WHITE,
                   Canvas, fmt_date_long, fmt_date_short)
from .ctx import (W, adate, anchor, guard, minus_days, name, out_path, placement, rel, sysname, svcname, team_name,
                  title, who)
from .diagrams import Diagram, ERD, Swimlane, Timeline, org_chart, table_image
from .facts import Facts, arrow_spec, placement_spec, spec
from .skeleton import approval, glossary, section, start_doc, versions_for

STATUS_COL = {"accepted": NAVY2, "superseded": RED, "deprecated": AMBER, "proposed": TEAL}


# ==========================================================================================
# VS029 Architecture Decisions – Diagram Pack (2026-02-27, P018)
# ==========================================================================================
def build_vs029() -> tuple[list[dict], str, int]:
    fid = "VS029"
    d = adate(fid)
    facts = Facts(fid, rel(fid))
    adrs = [a for a in W.adrs.values() if a["date"] <= d]
    adrs.sort(key=lambda a: a["id"])
    for a in adrs:
        guard(fid, f"ADR:{a['id']}")
    contents = ["1 Introduction", "2 Decision timeline", "3 Decision register", "4 Superseded and deprecated decisions",
                "5 Reserve synchronisation decisions", "6 Platform decisions at a glance", "7 The reserve-engine rename",
                "8 How a decision is made", "9 Migration decisions", "10 Glossary"]
    b = start_doc(
        fid, facts, "Visual summary of the Programme Skerry architecture decision records", "CM-ARC-DP-029", "1.0",
        "arch", "architecture decisions for Claims Hub and the CLARA bridge",
        versions_for(fid, "P018", [(41, "0.1", "First cut of figures 1–4"), (20, "0.2", "Figures 5–9 added after DA review"),
                                   (0, "1.0", "Approved at Design Authority")], "1.0"),
        [approval("Author", "P018", d), approval("Reviewer", "P049", d, minus_days(d, 6)),
         approval("Reviewer", "P050", d, minus_days(d, 6)), approval("Approver", "P006", d)],
        ["Design Authority members", "Hub squad engineering leads", "Integration Platform team", "IBM Programme Skerry team"],
        contents, related=["ADR repository (docs/adr)", "Interface Diagram Pack"])

    # ---- Figure 1: timeline
    section(b, fid, "2", "Decision timeline", "when each architecture decision record was raised, grouped by theme")
    img = _adr_timeline(adrs, d)
    b.figure(img, "Architecture decision timeline, January 2025 to February 2026",
             "Timeline of architecture decision records grouped into five themes, with status colour coding.",
             facts=[spec("visual_only", "The ADR timeline plots ADR-019 in February 2026 in the 'Domain services & rules' lane.",
                         "ADR-019", "ADR:ADR-019#date", notes="timeline label; the date is only given by the axis position"),
                    spec("image_text", "The ADR timeline groups decisions into Strategy & migration, Platform & runtime, "
                                       "Integration, Domain services & rules, and Identity & documents.",
                         "Domain services & rules", None)])

    # ---- Figure 2: register table
    section(b, fid, "3", "Decision register", "every decision record in force or retired on the document date")
    rows = []
    for a in adrs:
        dec = ", ".join(name(p, d) for p in a["deciders"])
        rows.append([a["id"], a["title"], fmt_date_short(a["date"]), a["status"].capitalize(), dec])
    tim = table_image(["ADR", "Title", "Date", "Status", "Deciders"], rows, [150, 900, 210, 190, 760],
                      title="Architecture decision register (Design Authority, COM-05)", size=21,
                      note=f"Register extract as at {fmt_date_long(d)}. Status colours as in Figure 1.")
    a13 = W.adrs["ADR-013"]
    b.figure(tim.png_bytes(), "Architecture decision register", "Table image listing each ADR with title, date, status and deciders.",
             facts=[spec("image_table", "ADR-013 'Synchronous REST scoring with Sentinel' was accepted on 2025-05-05 "
                                        "with deciders Elin Fosse and Oskar Lindgren.",
                         "Synchronous REST scoring with Sentinel", "ADR:ADR-013"),
                    spec("image_table", "ADR-018 'Tier calculation as a shared library' has status Deprecated.",
                         "Tier calculation as a shared library", "ADR:ADR-018#status"),
                    spec("image_table", "ADR-025 'Masked data for migration rehearsals' (2025-12-15) was decided by "
                                        "Callum Fairbairn and Morag Duthie.",
                         "Masked data for migration rehearsals", "ADR:ADR-025#deciders",
                         notes="Callum Fairbairn here is the IBM Data Migration Lead (P051), not the Corvane namesake")])

    # ---- Figure 3: supersession (placement PL-128)
    pl = placement(fid, "vs29_adr")
    section(b, fid, "4", "Superseded and deprecated decisions", "which decisions replaced earlier ones")
    img = _adr_supersession(d)
    b.figure(img, "Superseded and deprecated decisions",
             "Diagram of decision records that replaced earlier records, with arrows from the newer to the older record.",
             facts=[placement_spec(pl, "ADR-017 supersedes ADR-005"),
                    spec("image_text", "ADR-030 (triage-svc API) supersedes ADR-018 (shared tier library).",
                         "ADR-030 supersedes ADR-018", "ADR:ADR-030#supersedes"),
                    spec("image_text", "ADR-005 was superseded because CLRGL090 updates bypass the movement table.",
                         "CLRGL090 updates bypass the movement table", "ADR:ADR-005#consequences")])
    b.comment_on_last("Re-exported after the Design Authority session that accepted the batch bridge; the CDC option "
                      "is kept on the figure for traceability.", name("P050", d), "MO", minus_days(d, 9),
                      fact=spec("comment", "Reviewer comment (Marcus Oduya): Figure 3 keeps the rejected CDC option "
                                           "for traceability after the batch bridge decision.", "kept on the figure for traceability",
                                None))

    # ---- Figure 4: reserve synchronisation
    section(b, fid, "5", "Reserve synchronisation decisions", "how reserve movements reach Claims Hub under the accepted decisions")
    img = _reserve_sync(fid, d)
    b.figure(img, "Reserve synchronisation under ADR-012 and ADR-017",
             "Data-flow diagram from the CLARA reserve movement table through MQ and the Kafka bridge to reserve-engine.",
             facts=[spec("image_text", "Under ADR-012, CLX-IF-042 records are republished to the Kafka topic "
                                       "claims.reserve.movement.v1 by the CLX-IF-049 bridge and consumed by reserve-engine.",
                         "claims.reserve.movement.v1", "ADR:ADR-012#consequences"),
                    arrow_spec("Arrow label: CLX-IF-049 Reserve Movement Kafka Bridge runs from the MQ Backbone "
                                       "to the Event Streaming Platform.",
                         "CLX-IF-049 Reserve Movement Kafka Bridge", "INTERFACE:CLX-IF-049",
                         notes="label sits on the arrow in a raster image (docx_image locator)"),
                    spec("image_text", "CLX-IF-042 is produced from CLR.T_RESERVE_MOVEMENT by program CLRRS170.",
                         "CLRRS170", "INTERFACE:CLX-IF-042#programs")])

    # ---- Figure 5: platform decision cards
    section(b, fid, "6", "Platform decisions at a glance", "the platform-level decisions and their key consequence")
    img = _platform_cards(d)
    b.figure(img, "Platform decisions at a glance",
             "Grid of decision cards, each with the ADR number, title and its main consequence.",
             facts=[spec("image_text", "ADR-006: OpenShift clusters ocp-prd-lon1 (primary) and ocp-dr-lds1 (DR).",
                         "ocp-dr-lds1", "ADR:ADR-006#consequences"),
                    spec("image_text", "ADR-013: synchronous Sentinel scoring times out at 800 ms and falls back to batch scoring.",
                         "800 ms", "ADR:ADR-013#consequences"),
                    spec("image_text", "ADR-024 sets an SLO of 99.5% for claim-core-svc.", "99.5%", "ADR:ADR-024#consequences"),
                    spec("image_text", "ADR-023: Kafka contract tests with schema registry compatibility BACKWARD.",
                         "BACKWARD", "ADR:ADR-023#consequences"),
                    spec("image_text", "ADR-014: fraud-referral notices use Notify templates FRN01 (letter) and FRN02 (SMS).",
                         "FRN02", "ADR:ADR-014#consequences")])
    b.comment_on_last("ADR-018 is shown deprecated rather than removed; the replacement is the triage-svc API.",
                      name("P049", d), "EF", minus_days(d, 5),
                      fact=spec("comment", "Reviewer comment (Elin Fosse): ADR-018 is deprecated and replaced by the "
                                           "triage-svc API.", "replacement is the triage-svc API", "ADR:ADR-018"))

    # ---- Figure 6: rename
    section(b, fid, "7", "The reserve-engine rename", "what changed when the reserve service was renamed")
    img = _rename(d)
    b.figure(img, "ADR-019 rename of reserve-svc to reserve-engine",
             "Before-and-after diagram of the reserve service rename: repository path, Terraform module and event topic.",
             facts=[spec("image_text", "ADR-019: reserve-svc renamed reserve-engine effective 2026-02-10 (CHUB-233); "
                                       "event topic reserve.changed.v2 replaces v1.",
                         "reserve.changed.v2", "SERVICE:reserve-engine#renames"),
                    spec("image_text", "After the rename the repository path is services/reserve-engine.",
                         "services/reserve-engine", "SERVICE:reserve-engine#repo_path")])

    # ---- Figure 7: decision workflow
    section(b, fid, "8", "How a decision is made", "the route from proposal to an accepted decision record")
    img = _da_workflow(d)
    b.figure(img, "Design Authority decision workflow",
             "Swimlane of the decision process across proposer, Design Authority, delivery squads and the ADR repository.",
             facts=[spec("lane_only", "The Design Authority (chair Tomasz Wójcik) meets weekly on Tuesday at 15:00.",
                         "Tuesday 15:00", "COMMITTEE:COM-05#cadence"),
                    spec("image_text", "Accepted decision records are stored as docs/adr/adr-NNN.md in the repository.",
                         "docs/adr/adr-NNN.md", "ADR:ADR-017#repo_path")])

    # ---- Figure 8: migration
    section(b, fid, "9", "Migration decisions", "the migration approach decisions and how they fit together")
    img = _migration(d)
    b.figure(img, "Migration decisions: strangler fig, region waves and data handling",
             "Diagram of the migration approach decisions linking strangler-fig migration, region waves, currency storage and masked rehearsal data.",
             facts=[spec("image_text", "ADR-001: CLARA remains the system of record for unmigrated claims until 2027-09-30.",
                         "system of record for unmigrated claims", "ADR:ADR-001#consequences"),
                    spec("image_text", "ADR-025 masked data for migration rehearsals is required by NISA Circular 2025/11 §4.",
                         "NISA Circular 2025/11", "ADR:ADR-025#consequences"),
                    spec("image_text", "ADR-016: Nordic amounts stored in original currency and GBP, minor units in events.",
                         "Minor units (øre/pence) in events", "ADR:ADR-016#consequences")])

    glossary(b, fid, "10", [("ADR", "Architecture decision record"), ("DA", "Design Authority (COM-05)"),
                            ("CDC", "Change data capture"), ("ESP", "Event Streaming Platform (Kafka)"),
                            ("CIS", "Corvane Identity Service"), ("SLO", "Service level objective"),
                            ("DR", "Disaster recovery")])
    path = out_path(fid)
    b.save(path)
    return facts.items, str(path), b.fig_no


def _adr_timeline(adrs, d) -> bytes:
    lanes = [("Strategy & migration", ["ADR-001", "ADR-015", "ADR-016", "ADR-025"]),
             ("Platform & runtime", ["ADR-002", "ADR-003", "ADR-006", "ADR-007", "ADR-023", "ADR-024"]),
             ("Integration", ["ADR-004", "ADR-005", "ADR-012", "ADR-017"]),
             ("Domain services & rules", ["ADR-010", "ADR-011", "ADR-013", "ADR-018", "ADR-019", "ADR-020", "ADR-030"]),
             ("Identity & documents", ["ADR-008", "ADR-009", "ADR-014"])]
    have = {a["id"]: a for a in adrs}
    probe = Canvas(10, 10)
    W_, left, right = 2400, 380, 70
    span_px = W_ - left - right
    import datetime as dt
    s, e = dt.date(2025, 1, 1), dt.date(2026, 3, 31)

    def xof(ds):
        return left + span_px * (dt.date.fromisoformat(ds) - s).days / (e - s).days

    layouts, total_h = [], 0
    for lname, ids in lanes:
        ids = [i for i in ids if i in have]
        ids.sort(key=lambda i: have[i]["date"])
        levels: list[float] = []
        placed = []
        for i in ids:
            x = xof(have[i]["date"])
            w = probe.twidth(i, 22, True) + 16
            lv = 0
            while lv < len(levels) and levels[lv] > x - w / 2:
                lv += 1
            if lv == len(levels):
                levels.append(-1e9)
            levels[lv] = x + w / 2
            placed.append((i, x, lv))
        h = 90 + 40 * max(1, len(levels))
        layouts.append((lname, placed, h))
        total_h += h
    H = 230 + total_h + 150
    tl = Timeline(W_, H, "2025-01-01", "2026-03-31", left=left, right=right, top=230,
                  title="Architecture decision timeline", subtitle=f"Decision records raised up to {fmt_date_long(d)}",
                  right_note="Design Authority · COM-05")
    y = 230
    for k, (lname, placed, h) in enumerate(layouts):
        tl.lane(y, y + h, lname, fill="#F7F9FC" if k % 2 == 0 else WHITE)
        base = y + h - 34
        tl.d.line([(left, base), (W_ - right, base)], fill=GRID, width=2)
        for (i, x, lv) in placed:
            col = STATUS_COL[have[i]["status"]]
            tl.d.polygon([(x, base - 15), (x + 15, base), (x, base + 15), (x - 15, base)], fill=col)
            ly = base - 30 - lv * 40
            tl.d.line([(x, base - 15), (x, ly + 6)], fill=GRID, width=2)
            tl.text(x, ly, i, 22, True, fill=col, anchor="ms")
        y += h
    tl.legend(40, H - 128, [(NAVY2, "Accepted"), (RED, "Superseded"), (AMBER, "Deprecated")], size=21, cols=3,
              col_w=300, title="Status on " + fmt_date_short(d))
    return tl.png_bytes()


def _adr_box_text(a, d):
    return f"{a['id']}\n{a['title']}\n{fmt_date_short(a['date'])} · {a['status'].upper()}"


def _adr_supersession(d) -> bytes:
    D = Diagram(2200, 1500)
    D.title_band("Superseded and deprecated decisions", "Arrows run from the newer decision to the decision it replaces",
                 right="Status on " + fmt_date_short(d))
    a5, a17, a18, a30 = (W.adrs[x] for x in ("ADR-005", "ADR-017", "ADR-018", "ADR-030"))
    D.node("a17", (120, 230, 820, 470), _adr_box_text(a17, d), "target", size=27)
    D.node("a5", (1380, 230, 2080, 470), _adr_box_text(a5, d), "alert", size=27)
    D.edge("a17", "a5", "supersedes", width=5, label_size=26, label_bold=True, label_outline=LINE)
    D.text(470, 495, "Deciders: " + ", ".join(name(p, d) for p in a17["deciders"]), 22, fill=INK2, anchor="ma")
    D.text(1730, 495, "Deciders: " + ", ".join(name(p, d) for p in a5["deciders"]), 22, fill=INK2, anchor="ma")
    D.label(1100, 600, "ADR-017 supersedes ADR-005 — CDC rejected in favour of the batch bridge", 28, bold=True,
            bg="#FFF6E0", outline=AMBER, pad=14)
    D.node("why", (1380, 660, 2080, 790), "Reason recorded on ADR-005:\nCLRGL090 updates bypass the movement table",
           "note", size=23)
    D.polyline([(1730, 470 + 60), (1730, 660)], fill=AMBER, width=3, dash=(10, 8))
    # second pair
    D.node("a30", (120, 930, 820, 1170), _adr_box_text(a30, d), "target", size=27)
    D.node("a18", (1380, 930, 2080, 1170), _adr_box_text(a18, d), "warn", size=27)
    D.edge("a30", "a18", "supersedes", width=5, label_size=26, label_bold=True, label_outline=LINE)
    D.text(470, 1195, "Deciders: " + ", ".join(name(p, d) for p in a30["deciders"]), 22, fill=INK2, anchor="ma")
    D.text(1730, 1195, "Deciders: " + ", ".join(name(p, d) for p in a18["deciders"]), 22, fill=INK2, anchor="ma")
    D.label(1100, 1290, "ADR-030 supersedes ADR-018 — tiering centralised in triage-svc", 26, bold=True, bg=GREY_L,
            outline=LINE, pad=12)
    D.legend(60, 1350, [("target", "Accepted"), ("alert", "Superseded"), ("warn", "Deprecated")], cols=3, col_w=300,
             title="Key", size=21)
    return D.png_bytes()


def _reserve_sync(fid, d) -> bytes:
    for ref, f in (("INTERFACE:CLX-IF-042", "programs"), ("INTERFACE:CLX-IF-042", "format"),
                   ("INTERFACE:CLX-IF-049", "format"), ("TOPIC:claims.reserve.movement.v1", "schema_version")):
        guard(fid, ref, f)
    D = Diagram(2400, 1350)
    D.title_band("Reserve synchronisation (ADR-012, ADR-017)", "Reserve movements from CLARA to Claims Hub; "
                 "schedules are documented in the Interface Diagram Pack", right="View: data flow")
    D.node("clara", (60, 260, 460, 560), "CLARA\nCLR.T_RESERVE\nCLR.T_RESERVE_MOVEMENT\nextract program CLRRS170", "legacy", size=25)
    D.node("mq", (940, 300, 1300, 520), "MQ Backbone\nqueue CLR.RSVMOVE.OUT", "platform", size=26)
    D.node("esp", (1780, 300, 2340, 520), "Event Streaming Platform\nclaims.reserve.movement.v1\nAvro schema v3, key claim_id",
           "platform", size=24)
    D.node("re", (1780, 800, 2340, 1000), "reserve-engine\n(Claims Hub)", "service", size=27)
    D.node("down", (900, 800, 1340, 1040), "Downstream RSVMOVE consumers\nCLX-IF-043 Group Ledger\nCLX-IF-044 CDW\nCLX-IF-047 ReCede",
           "external", size=23)
    D.edge("clara", "mq", "CLX-IF-042\nReserve Movement Daily Extract", label_size=23, label_outline=GRID)
    D.edge("mq", "esp", "CLX-IF-049 Reserve Movement\nKafka Bridge", label_size=23, label_outline=GRID)
    D.edge("esp", "re", "consumed for parallel run\nand Wave 2 sync", sides="bt", label_size=22, label_outline=GRID)
    D.edge("mq", "down", "RSVMOVE records", sides="bt", label_size=22)
    D.node("cdc", (60, 800, 460, 1040), "Rejected: CDC on\nCLR.T_RESERVE_MOVEMENT\n(ADR-005, superseded)", "alert",
           size=24, dash=(12, 8))
    D.polyline([(260, 560), (260, 800)], fill=RED, width=3, dash=(12, 8))
    D.text(280, 680, "not built", 22, True, fill=RED, anchor="lm")
    D.legend(60, 1120, [("legacy", "CLARA (legacy)"), ("platform", "Integration platform"), ("service", "Claims Hub service"),
                        ("external", "Downstream consumer")], cols=4, col_w=420, size=21)
    return D.png_bytes()


def _platform_cards(d) -> bytes:
    ids = ["ADR-002", "ADR-003", "ADR-004", "ADR-006", "ADR-007", "ADR-008", "ADR-009", "ADR-010", "ADR-011",
           "ADR-013", "ADR-014", "ADR-020", "ADR-023", "ADR-024", "ADR-018"]
    cols, cw, ch, gx, gy = 3, 730, 250, 40, 34
    rows = (len(ids) + cols - 1) // cols
    H = 170 + rows * (ch + gy) + 40
    D = Diagram(60 + cols * cw + (cols - 1) * gx + 60, H)
    D.title_band("Platform decisions at a glance", "Decision record, title and main consequence",
                 right="As at " + fmt_date_short(d))
    for k, i in enumerate(ids):
        a = W.adrs[i]
        r_, c_ = divmod(k, cols)
        x0 = 60 + c_ * (cw + gx)
        y0 = 160 + r_ * (ch + gy)
        st = {"accepted": "target", "deprecated": "warn", "superseded": "alert"}[a["status"]]
        D.rect((x0, y0, x0 + cw, y0 + ch), fill=core.STYLES[st][0], outline=core.STYLES[st][1], width=3, radius=14)
        D.text(x0 + 20, y0 + 16, f"{i} · {a['status'].capitalize()}", 23, True, fill=core.STYLES[st][1])
        D.text_in_box((x0 + 6, y0 + 52, x0 + cw - 6, y0 + 112), a["title"], 23, bold=True, align="left", valign="top",
                      pad=14, min_size=19)
        D.text_in_box((x0 + 6, y0 + 118, x0 + cw - 6, y0 + ch - 6), a["consequences"], 22, align="left", valign="top",
                      pad=14, min_size=18, fill=INK2)
    return D.png_bytes()


def _rename(d) -> bytes:
    s = W.services["reserve-engine"]
    rn = s["renames"][0]
    old = s["path_history"][0]
    D = Diagram(2300, 1150)
    D.title_band("ADR-019: reserve-svc becomes reserve-engine", f"Effective {rn['date']} · ticket {rn['ticket']}",
                 right="Decided " + fmt_date_short(W.adrs["ADR-019"]["date"]))
    D.text(400, 190, "Before", 32, True, fill=MUTED, anchor="ma")
    D.text(1880, 190, "After", 32, True, fill=NAVY, anchor="ma")
    rows = [("Service name", rn["from_name"], rn["to_name"]),
            ("Repository path", old["repo_path"], s["repo_path"]),
            ("Terraform module", old["terraform_module"], s["terraform_module"]),
            ("Change event", "reserve.changed.v1", "reserve.changed.v2"),
            ("Kubernetes namespace (unchanged)", old["k8s_namespace"], s["k8s_namespace"])]
    y = 250
    for k, (lab, a, bb) in enumerate(rows):
        D.node(f"o{k}", (80, y, 720, y + 120), a, "external", size=26, bold_first=False)
        D.node(f"n{k}", (1560, y, 2200, y + 120), bb, "service", size=26, bold_first=False)
        D.edge(f"o{k}", f"n{k}", lab, label_size=24, label_bold=True, label_outline=GRID)
        y += 160
    D.text(1150, y + 20, "reserve.changed.v1 retired with the rename · reserve.changed.v2 consumers: gl-posting-svc, reporting-feed-svc",
           22, fill=INK2, anchor="ma")
    return D.png_bytes()


def _da_workflow(d) -> bytes:
    com = W.committees["COM-05"]
    chair = name(com["chair_history"][-1]["person"], d)
    S = Swimlane(2400, ["Proposer (architect or squad lead)", f"Design Authority\nchair {chair}",
                        "Delivery squads", "ADR repository"], lane_h=220,
                 title="Design Authority decision workflow", subtitle="Design Authority (COM-05) meets weekly, Tuesday 15:00 UK time",
                 right_note="COM-05")
    S.fit_cols(6.0)
    S.step("s", 0, 0, "", "start")
    S.step("p1", 0, 1, "Draft ADR with options and consequences")
    S.step("p2", 1, 2, "Review at weekly DA session")
    S.step("dq", 1, 3, "Accept?", "decision", w=200, h=110)
    S.step("p3", 0, 4, "Rework options")
    S.step("p4", 3, 4, "Merge docs/adr/adr-NNN.md (status: accepted)", kind="doc", style="note")
    S.step("p5", 2, 5, "Implement in service repos and Terraform")
    S.step("p6", 3, 6, "Mark superseded ADRs (superseded_by)", kind="doc", style="note")
    S.step("e", 2, 6, "", "end")
    S.edge("s", "p1")
    S.edge("p1", "p2", "submit", sides="bl", label_size=21)
    S.edge("p2", "dq")
    S.edge("dq", "p3", "No", sides="tb", label_size=21)
    S.edge("p3", "p1", "revise", sides="lr", label_size=21)
    S.edge("dq", "p4", "Yes", sides="bl", label_size=21)
    S.edge("p4", "p5", sides="rl")
    S.edge("p5", "p6", sides="rl")
    S.edge("p6", "e", sides="tb")
    return S.png_bytes()


def _migration(d) -> bytes:
    D = Diagram(2300, 1250)
    D.title_band("Migration decisions", "Strangler-fig migration by capability and region", right="ADR-001 · 015 · 016 · 025")
    a1, a15, a16, a25 = (W.adrs[x] for x in ("ADR-001", "ADR-015", "ADR-016", "ADR-025"))
    D.node("a1", (700, 190, 1600, 420), f"ADR-001 {a1['title']}\n{a1['consequences']}", "target", size=27)
    D.node("a15", (80, 560, 760, 790), f"ADR-015 {a15['title']}\n{a15['consequences']}", "target", size=27)
    D.node("a16", (810, 560, 1490, 790), f"ADR-016 {a16['title']}\n{a16['consequences']}", "target", size=27)
    D.node("a25", (1540, 560, 2220, 790), f"ADR-025 {a25['title']}\n{a25['consequences']}", "target", size=27)
    D.edge("a1", "a15", "waves", sides="bt", label_size=22, aoff=-240)
    D.edge("a1", "a16", "data format", sides="bt", label_size=22, label_at=0.5)
    D.edge("a1", "a25", "rehearsals", sides="bt", label_size=22, aoff=240)
    D.node("clara", (80, 930, 760, 1110), "CLARA\nsystem of record for unmigrated claims", "legacy", size=25)
    D.node("hub", (1540, 930, 2220, 1110), "Claims Hub\nsystem of record for migrated claims", "service", size=25)
    D.edge("clara", "hub", "claims move wave by wave", label_size=24, label_bold=True, width=6, label_outline=GRID)
    return D.png_bytes()


# ==========================================================================================
# placeholders filled in by later builders
# ==========================================================================================


# ==========================================================================================
# VS030 Claims Hub User Guide (screenshots) (2026-09-07, P017)
# ==========================================================================================
from .screens import HubScreen  # noqa: E402

TRN_USER = "B. Kilbride (TRAINING)"


def build_vs030() -> tuple[list[dict], str, int]:
    fid = "VS030"
    d = adate(fid)
    facts = Facts(fid, rel(fid))
    for ref, f in (("RULE:BR-RSV-007@v3", "text"), ("RULE:BR-RSV-003@v3", "text"), ("RULE:BR-FRD-032@v2", "text"),
                   ("SYSTEM:SYS05", "name"), ("SYSTEM:SYS16", "name")):
        guard(fid, ref, f)
    contents = ["1 Introduction", "2 Signing in", "3 Your work queue", "4 The claim summary", "5 Fraud referral panel",
                "6 Reserves", "7 Posting a reserve movement", "8 Tier-3 reserve reviews", "9 Documents", "10 Glossary"]
    b = start_doc(
        fid, facts, "Screenshot guide for claim handlers moving to Claims Hub", "CM-CHB-UG-030", "2.0", "ops",
        "everyday tasks in Claims Hub",
        versions_for(fid, "P017", [(98, "1.0", "Issued for the MVP digital channels"),
                                   (30, "1.1", "Screens refreshed for the Wave 1 dress rehearsal"),
                                   (0, "2.0", "Approved for Wave 1 UK motor training")], "2.0"),
        [approval("Author", "P017", d), approval("Reviewer", "P040", d, minus_days(d, 4)),
         approval("Reviewer", "P054", d, minus_days(d, 4)), approval("Approver", "P005", d)],
        ["Claims Operations team leaders", "Motor Claims – Leeds", "Contact Centre", "Claims Hub product team"],
        contents, related=["Claims Hub Screenshot Pack", "Claims Handling Manual"],
        intro_extra=["All screens were captured in the Claims Hub TRAINING environment. Claim references, "
                     "names and amounts shown in the screenshots are fictitious training data."])

    section(b, fid, "2", "Signing in", "the sign-in page")
    b.figure(_hub_signin(d), "Claims Hub sign-in page",
             "Claims Hub sign-in page with a single button to sign in with Corvane Identity Service.",
             facts=[spec("screenshot", "Claims Hub users sign in with Corvane Identity Service (CIS).",
                         "Sign in with Corvane Identity Service", "INTERFACE:CLX-IF-040")])

    section(b, fid, "3", "Your work queue", "the work queue with filters and due dates")
    b.figure(_hub_queue(d), "Work queue",
             "Work queue table listing training claims with tier, next action and due date columns.",
             facts=[spec("screenshot", "The Claims Hub work queue has the columns Claim, Tier, Loss type, Next action, "
                                       "Due and Status.", "Next action", None)])

    section(b, fid, "4", "The claim summary", "the claim summary page and its tabs")
    b.figure(_hub_claim_summary(d), "Claim summary",
             "Claim summary page with header fields and tabs for overview, reserves, fraud, payments, recoveries and documents.",
             facts=[spec("screenshot", "The claim summary shows the CLARA legacy reference next to the Claims Hub claim "
                                       "reference (legacy_claim_id).", "Legacy reference", "TABLE:claim_core.claim#columns.legacy_claim_id")])

    pl_alt = placement(fid, "vs30_alt")
    section(b, fid, "5", "Fraud referral panel", "the fraud referral panel on a claim")
    b.figure(_hub_fraud_panel(d), "Fraud referral panel",
             "Fraud referral panel showing threshold applied 60 (Tier-3)",
             facts=[placement_spec(pl_alt, "threshold applied 60 (Tier-3)",
                                   notes="alt-text only: the screenshot itself does not show the threshold value. "
                                         "Anchor date 2026-09-07 precedes BR-FRD-031 v2 (effective 2026-10-01); "
                                         "planted as specified by the placement."),
                    spec("screenshot", "The fraud referral panel shows the customer notice due date (10 business days "
                                       "after referral) and the SIU case reference.", "Customer notice due",
                         "RULE:BR-FRD-032@v2")])

    section(b, fid, "6", "Reserves", "the reserves tab")
    b.figure(_hub_reserves(d), "Reserves tab",
             "Reserves tab with indemnity, expense and legal reserve lines, GBP equivalents and next review date.",
             facts=[spec("screenshot", "Reserve lines in Claims Hub are typed Indemnity, Expense and Legal.",
                         "Indemnity", "TABLE:reserve.reserve#columns.reserve_type")])

    section(b, fid, "7", "Posting a reserve movement", "the reserve movement dialog and the authority check")
    b.figure(_hub_movement(d), "Post reserve movement dialog",
             "Dialog for posting a reserve movement, with reason code and the user's reserve authority.",
             facts=[spec("screenshot", "Reserve authority shown in the dialog: Claims Handler £25,000 (BR-RSV-003).",
                         "Claims Handler £25,000", "RULE:BR-RSV-003@v3#parameters"),
                    spec("screenshot", "Every reserve movement needs a reason code from the RSNC code list.",
                         "RSNC code list", "RULE:BR-RSV-015@v1")])
    b.comment_on_last("Dialog re-captured after the authority limits were loaded into TRAINING.", name("P054", d), "HL",
                      minus_days(d, 6), fact=spec("comment", "Reviewer comment (Hannah Lyle): the movement dialog was "
                                                               "re-captured after authority limits were loaded into TRAINING.",
                                                  "authority limits were loaded into TRAINING", None))

    pl_rev = placement(fid, "vs30_review")
    section(b, fid, "8", "Tier-3 reserve reviews", "the reserve review screen for a Tier-3 claim")
    b.figure(_hub_review(d), "Tier-3 reserve review",
             "Reserve review screen for a Tier-3 training claim showing the review history and the next review date.",
             facts=[placement_spec(pl_rev, "Review cadence 14 days"),
                    spec("screenshot", "Training example: last review 2026-08-24, next review due 2026-09-07.",
                         "Next review due 2026-09-07", "RULE:BR-RSV-007@v3")])

    section(b, fid, "9", "Documents", "the documents tab")
    b.figure(_hub_documents(d), "Documents tab",
             "Documents tab listing claim documents stored in Evidence Vault with type, source and date.",
             facts=[spec("screenshot", "Claim documents in Claims Hub are stored in Evidence Vault through document-svc.",
                         "Stored in Evidence Vault", "ADR:ADR-009")])

    glossary(b, fid, "10", [("CIS", "Corvane Identity Service"), ("Tier-3", "Highest claim tier (BR-TRI-003)"),
                            ("SIU", "Counter-Fraud & SIU team"), ("RSNC", "Reserve reason code list"),
                            ("TRAINING", "Claims Hub training environment with fictitious data")])
    path = out_path(fid)
    b.save(path)
    return facts.items, str(path), b.fig_no


def _hub(active, title, crumb, h=1140):
    return HubScreen(1920, h, title=title, breadcrumb=crumb, user=TRN_USER, env="TRAINING", active=active,
                     version="Claims Hub R2026.09")


def _hub_signin(d) -> bytes:
    S = Canvas(1920, 1080, "#0F2A4A")
    S.rect((560, 200, 1360, 860), fill=WHITE, outline=WHITE, radius=18)
    S.text(960, 270, "Claims Hub", 52, True, fill=NAVY, anchor="ma")
    S.text(960, 345, "Corvane Mutual", 28, fill=MUTED, anchor="ma")
    S.rect((660, 450, 1260, 530), fill="#1D6FD1", outline="#1D6FD1", radius=10)
    S.text(960, 490, "Sign in with Corvane Identity Service", 27, True, fill=WHITE, anchor="mm")
    S.text(960, 580, "Use your Corvane network account.", 24, fill=INK2, anchor="ma")
    S.text(960, 620, "Assessor Portal partners use their partner account.", 24, fill=INK2, anchor="ma")
    S.label(960, 720, "TRAINING environment · fictitious data", 22, fill=WHITE, bg="#2E7D32", bold=True)
    S.text(960, 800, "Problems signing in? Contact the IT Service Desk.", 21, fill=MUTED, anchor="ma")
    return S.png_bytes()


def _hub_queue(d) -> bytes:
    S = _hub("Work queue", "My work queue", "Home / Work queue")
    y = S.content_top
    S.chip(280, y, "Assigned to me: 9", "info")
    S.chip(520, y, "Due today: 3", "warn")
    S.chip(720, y, "Overdue: 1", "bad")
    S.button(1650, y - 6, "Refresh", primary=False)
    rows = [["CLM-UK-2026-900113", "1", "Collision", "Confirm settlement offer", "2026-09-08", "Open"],
            ["CLM-UK-2026-900127", "2", "Theft", "Chase police reference", "2026-09-07", "Open"],
            ["CLM-UK-2026-900131", "3", "Collision", "Reserve review", "2026-09-07", "Open"],
            ["CLM-UK-2026-900140", "1", "Windscreen", "Approve payment", "2026-09-09", "Open"],
            ["CLM-UK-2026-900152", "2", "Vandalism", "Appoint assessor", "2026-09-08", "Open"],
            ["CLM-UK-2026-900158", "3", "Third-party damage", "Await assessor report", "2026-09-11", "Open"],
            ["CLM-UK-2026-900166", "1", "Collision", "Close claim", "2026-09-10", "Settled"],
            ["CLM-UK-2026-900171", "2", "Collision", "Customer call-back", "2026-09-06", "Open"],
            ["CLM-UK-2026-900183", "1", "Windscreen", "Confirm repair booked", "2026-09-12", "Open"]]
    S.grid_table(280, y + 70, ["Claim", "Tier", "Loss type", "Next action", "Due", "Status"], rows,
                 [330, 110, 280, 480, 230, 180], size=22, row_h=56)
    S.text(280, 1070, "Sorted by due date · training data", 20, fill=MUTED)
    return S.png_bytes()


def _hub_claim_summary(d) -> bytes:
    S = _hub("Claims", "CLM-UK-2026-900131", "Claims / CLM-UK-2026-900131")
    y = S.content_top
    S.chip(820, S.cy0 + 46, "Tier 3", "bad")
    S.chip(960, S.cy0 + 46, "Open", "ok")
    y = S.tabs(280, y, ["Overview", "Reserves", "Fraud", "Payments", "Recoveries", "Documents", "Notes"], "Overview")
    x0, yy = S.card((280, y, 1100, y + 560), "Claim")
    yy = S.field(x0, yy, "Claim reference", "CLM-UK-2026-900131")
    yy = S.field(x0, yy, "Legacy reference", "UK2026900131")
    yy = S.field(x0, yy, "Product", "Motor UK")
    yy = S.field(x0, yy, "Loss type", "Collision")
    S.field(x0 + 400, y + 72, "Region / currency", "UK · GBP")
    S.field(x0 + 400, y + 72 + 66, "Date of loss", "2026-08-02")
    S.field(x0 + 400, y + 72 + 132, "Channel", "Telephone")
    S.field(x0 + 400, y + 72 + 198, "Claim handler", "B. Kilbride")
    x1, y1 = S.card((1130, y, 1890, y + 560), "Policyholder")
    y1 = S.field(x1, y1, "Name", "Training Customer 31")
    y1 = S.field(x1, y1, "Policy number", "TRN0000131")
    y1 = S.field(x1, y1, "Vulnerability indicator", "No")
    y1 = S.field(x1, y1, "Preferred language", "EN")
    S.banner(280, y + 590, 1610, "Tier-3 claims route to Major & Complex Loss. Reserve reviews are scheduled "
             "automatically; see the Reserves tab.", "info")
    return S.png_bytes()


def _hub_fraud_panel(d) -> bytes:
    S = _hub("Fraud referrals", "CLM-UK-2026-900158", "Claims / CLM-UK-2026-900158 / Fraud")
    y = S.tabs(280, S.content_top, ["Overview", "Reserves", "Fraud", "Payments", "Recoveries", "Documents"], "Fraud")
    x0, yy = S.card((280, y, 1090, y + 620), "SIU referral")
    yy = S.field(x0, yy, "Referral status", "Referred to SIU", value_bold=True, value_color=RED)
    yy = S.field(x0, yy, "Sentinel score", "62", value_bold=True)
    yy = S.field(x0, yy, "Claim tier", "Tier 3")
    yy = S.field(x0, yy, "Referred at", "2026-09-03 10:14")
    yy = S.field(x0, yy, "SIU case", "SIU-TRN-0458")
    x1, y1 = S.card((1120, y, 1890, y + 620), "Customer notice")
    y1 = S.field(x1, y1, "Customer notice due", "2026-09-17")
    y1 = S.field(x1, y1, "Deferral", "None recorded")
    y1 = S.field(x1, y1, "Channel", "Letter")
    S.button(x1, y1 + 10, "Record deferral", primary=False)
    S.banner(280, y + 650, 1610, "A claim may not be declined or reduced on the Sentinel score alone. Record the "
             "human review before any adverse outcome.", "warn")
    return S.png_bytes()


def _hub_reserves(d) -> bytes:
    S = _hub("Reserves", "CLM-UK-2026-900131", "Claims / CLM-UK-2026-900131 / Reserves")
    y = S.tabs(280, S.content_top, ["Overview", "Reserves", "Fraud", "Payments", "Recoveries", "Documents"], "Reserves")
    rows = [["Indemnity", "GBP", "38,500.00", "38,500.00", "Open", "2026-09-07"],
            ["Expense", "GBP", "4,250.00", "4,250.00", "Open", "2026-09-07"],
            ["Legal", "GBP", "0.00", "0.00", "Closed", "–"]]
    y = S.grid_table(280, y + 10, ["Reserve type", "Currency", "Outstanding", "GBP equivalent", "Status", "Next review"],
                     rows, [300, 180, 260, 300, 200, 300], size=22, row_h=58)
    S.button(280, y + 30, "Post movement")
    S.button(520, y + 30, "Movement history", primary=False)
    S.text(280, y + 120, "Amounts are training data.", 20, fill=MUTED)
    return S.png_bytes()


def _hub_movement(d) -> bytes:
    S = _hub("Reserves", "CLM-UK-2026-900131", "Claims / CLM-UK-2026-900131 / Reserves")
    S.rect((0, 0, 1920, 1140), fill=None, outline=None)
    overlay = Canvas(1920, 1140, "#56606E")
    S.img = __import__("PIL.Image", fromlist=["Image"]).blend(S.img, overlay.img, 0.55)
    S.d = __import__("PIL.ImageDraw", fromlist=["ImageDraw"]).Draw(S.img)
    S.rect((460, 150, 1460, 1010), fill=WHITE, outline=GRID, radius=14)
    S.text(500, 190, "Post reserve movement", 32, True, fill=INK)
    y = 260
    y = S.field(500, y, "Reserve line", "Indemnity · GBP", w=900, boxed=True)
    y = S.field(500, y, "Movement type", "Adjustment (AD)", w=900, boxed=True)
    y = S.field(500, y, "New outstanding amount", "41,000.00", w=900, boxed=True)
    y = S.field(500, y, "Reason code (RSNC code list)", "RV02 – revised repair estimate", w=900, boxed=True)
    S.banner(500, y + 10, 920, "Your reserve authority: Claims Handler £25,000. Movements above your authority "
             "are routed to your Team Leader.", "info")
    S.button(1150, 920, "Cancel", primary=False)
    S.button(1290, 920, "Submit")
    return S.png_bytes()


def _hub_review(d) -> bytes:
    S = _hub("Reserves", "CLM-UK-2026-900131", "Claims / CLM-UK-2026-900131 / Reserves / Review")
    y = S.tabs(280, S.content_top, ["Overview", "Reserves", "Fraud", "Payments", "Recoveries", "Documents"], "Reserves")
    x0, yy = S.card((280, y, 1050, y + 470), "Reserve review")
    yy = S.field(x0, yy, "Claim tier", "Tier 3")
    yy = S.field(x0, yy, "Review cadence", "14 days (Tier-3 · BR-RSV-007)", value_bold=True)
    yy = S.field(x0, yy, "Last review", "2026-08-24")
    yy = S.field(x0, yy, "Next review due", "2026-09-07", value_bold=True, value_color=RED)
    x1, y1 = S.card((1080, y, 1890, y + 470), "Review history")
    S.grid_table(x1, y1, ["Reviewed", "By", "Outcome"],
                 [["2026-08-24", "B. Kilbride", "Increase"], ["2026-08-10", "B. Kilbride", "No change"],
                  ["2026-08-04", "C. Fairbairn (TL)", "Initial reserve"]], [220, 290, 250], size=21, row_h=52)
    S.banner(280, y + 500, 1610, "Complete the review on or before the due date. Overdue reviews appear on the "
             "team leader dashboard.", "info")
    S.button(280, y + 610, "Start review")
    return S.png_bytes()


def _hub_documents(d) -> bytes:
    S = _hub("Documents", "CLM-UK-2026-900131", "Claims / CLM-UK-2026-900131 / Documents")
    y = S.tabs(280, S.content_top, ["Overview", "Reserves", "Fraud", "Payments", "Recoveries", "Documents"], "Documents")
    rows = [["Photo – front nearside", "Image", "Evidence Intake Gateway", "2026-08-02"],
            ["Photo – rear", "Image", "Evidence Intake Gateway", "2026-08-02"],
            ["Assessor report", "PDF", "Assessor Portal", "2026-08-09"],
            ["Repair estimate", "PDF", "Assessor Portal", "2026-08-09"],
            ["Acknowledgement letter", "PDF", "Notify", "2026-08-03"]]
    y = S.grid_table(280, y + 10, ["Document", "Type", "Source", "Received"], rows, [500, 200, 520, 300], size=22, row_h=58)
    S.banner(280, y + 30, 1520, "Stored in Evidence Vault. Binary content is never held in Claims Hub databases.", "info")
    S.button(280, y + 140, "Upload document")
    return S.png_bytes()


# ==========================================================================================
# VS031 Process Maps Handbook (2026-07-13, P011)
# ==========================================================================================
def build_vs031() -> tuple[list[dict], str, int]:
    fid = "VS031"
    d = adate(fid)
    facts = Facts(fid, rel(fid))
    contents = ["1 Introduction", "2 The claims value chain", "3 FNOL to triage", "4 Tiering and routing", "5 Reserving",
                "6 Fraud referral", "7 Settlement", "8 Recovery & Subrogation", "9 Responsibility matrix", "10 Glossary"]
    b = start_doc(
        fid, facts, "Swimlane maps of the end-to-end claims process", "CM-OPS-PM-031", "3.0", "ops",
        "the claims process from first notice of loss to recovery",
        versions_for(fid, "P011", [(380, "2.0", "Maps redrawn for the Group operating model"),
                                   (60, "2.1", "Fraud and recovery maps updated"),
                                   (0, "3.0", "Approved; reserving cadence map updated")], "3.0"),
        [approval("Author", "P011", d), approval("Reviewer", "P013", d, minus_days(d, 5)),
         approval("Reviewer", "P008", d, minus_days(d, 5)), approval("Approver", "P005", d)],
        ["Claims Operations (Group)", "Recoveries & Subrogation (Group)", "Counter-Fraud & SIU", "Reserving", "Claims Hub product team"],
        contents, related=["Claims Handling Manual", "Tier Decision Tree Poster"])

    section(b, fid, "2", "The claims value chain", "the seven process stages and their accountable owners")
    b.figure(_value_chain(fid, d), "Claims value chain and stage owners",
             "Seven chevrons for the claims process stages, each with the accountable owner.",
             facts=[spec("image_text", f"Stage S7 Recovery & Subrogation is owned by {name('P013', d)} ({title('P013', d)}).",
                         f"{name('P013', d)} {title('P013', d)}", "PROCESS:S7#owner_history"),
                    spec("image_text", f"Stage S4 Reserving is owned by {name('P009', d)}.", "S4 Reserving",
                         "PROCESS:S4#owner_history")])
    pl = placement(fid, "vs31_alt")
    section(b, fid, "3", "FNOL to triage", "the hand-off from first notice of loss to triage")
    b.figure(_fnol_triage_swim(d), "FNOL to triage",
             "FNOL to triage hand-off: Sentinel score within 15 minutes",
             facts=[placement_spec(pl, "Sentinel score within 15 minutes",
                                   notes="alt-text only: the swimlane image does not carry the 15-minute value"),
                    spec("lane_only", "In the FNOL-to-triage swimlane, 'Validate policy and cover' sits in the Claims Hub / CLARA lane "
                                      "and calls PALM.", "Validate policy and cover", "PROCESS:PS-FNOL-02"),
                    spec("image_text", "Duplicate check: an existing claim on the same policy with a date of loss within ±3 days.",
                         "within ±3 days", "RULE:BR-FNOL-004@v1")])
    section(b, fid, "4", "Tiering and routing", "how a claim is tiered and routed after the Sentinel pre-screen")
    b.figure(_tier_route_swim(d), "Tiering and routing",
             "Swimlane of tier classification and routing to Major & Complex Loss, specialist handlers or fast track.",
             facts=[spec("image_text", "Fast track (BR-TRI-006 v3): Tier-1, Sentinel score below 30, no injury, cap £2,000.",
                         "cap £2,000", "RULE:BR-TRI-006@v3#parameters"),
                    arrow_spec("Arrow label: Tier-3 claims route to Major & Complex Loss within 4 hours (BR-TRI-004).",
                         "Tier-3 within 4 hours", "RULE:BR-TRI-004@v1")])
    section(b, fid, "5", "Reserving", "how reserves are set, approved and reviewed")
    b.figure(_reserving_swim(d), "Reserving",
             "Swimlane of initial reserve, authority check, periodic review and large-loss notification.",
             facts=[spec("image_text", "Tier-3 reserve review every 14 days (BR-RSV-007 v3, from 2026-07-01).",
                         "every 14 days", "RULE:BR-RSV-007@v3"),
                    spec("image_text", "Large loss notification to ReCede within 24 hours above the LLNT of £250,000.",
                         "LLNT £250,000", "RULE:BR-RSV-011@v2")])
    section(b, fid, "6", "Fraud referral", "the fraud referral process from score to SIU outcome")
    b.figure(_fraud_swim(d), "Fraud referral",
             "Swimlane of the referral decision, SIU referral, customer notice and SIU triage.",
             facts=[spec("image_text", "Referral decision on 2026-07-13: refer when the Sentinel score is 65 or more "
                                       "(BR-FRD-031 v1, all tiers).", "score ≥ 65 (all tiers)", "RULE:BR-FRD-031@v1"),
                    spec("image_text", "SIU triage within 3 business days (BR-FRD-035 v2).", "SIU triage within 3 business days",
                         "RULE:BR-FRD-035@v2")])
    section(b, fid, "7", "Settlement", "settlement, payment and closure")
    b.figure(_settlement_swim(d), "Settlement",
             "Swimlane of settlement offer, payment authorisation, sanctions screening, payment run and closure.",
             facts=[spec("image_text", "Payments go in the next payment run, Mon–Fri 16:30.", "Mon–Fri 16:30",
                         "PROCESS:PS-STL-03#sla"),
                    spec("lane_only", "WatchScreen sanctions screening sits in the external services lane before payment release.",
                         "WatchScreen", "RULE:BR-STL-007@v1")])
    section(b, fid, "8", "Recovery & Subrogation", "the recovery and subrogation process")
    b.figure(_recovery_swim(d), "Recovery & Subrogation",
             "Swimlane of recovery identification, subrogation demand, solicitor referral, receipt and write-off.",
             facts=[spec("image_text", "Pursue subrogation when the recoverable amount is £1,000 or more (BR-REC-003 v3).",
                         "Recoverable ≥ £1,000?", "RULE:BR-REC-003@v3"),
                    spec("image_text", "Refer to Quarryhill Solicitors at £25,000 or more or when liability is defended (BR-REC-005 v2).",
                         "≥ £25,000 or liability defended", "RULE:BR-REC-005@v2")])
    section(b, fid, "9", "Responsibility matrix", "who is responsible and accountable for each step")
    b.figure(_raci(d), "Responsibility matrix (RACI) by process step",
             "Table image of process steps with responsible teams, accountable owner and SLA.",
             facts=[spec("image_table", f"PS-REC-02 Open subrogation case and demand: accountable {name('P013', d)}, "
                                        "responsible Recoveries & Subrogation, SLA demand within 10 business days.",
                         "demand within 10 business days", "PROCESS:PS-REC-02#raci")])
    glossary(b, fid, "10", [("FNOL", "First notice of loss"), ("LLNT", "Large loss notification threshold"),
                            ("SIU", "Counter-Fraud & SIU"), ("RACI", "Responsible, accountable, consulted, informed"),
                            ("SUBTRAK", "Subrogation Tracker")])
    path = out_path(fid)
    b.save(path)
    return facts.items, str(path), b.fig_no


def _value_chain(fid, d) -> bytes:
    C = Canvas(2400, 820)
    C.title_band("Claims value chain", f"Stage owners as at {fmt_date_long(d)}", right="Process S1–S7")
    stages = sorted(W.stages.values(), key=lambda s: s["order"])
    x, wch, y0, y1 = 40, 330, 220, 480
    for k, st in enumerate(stages):
        pts = [(x, y0), (x + wch - 40, y0), (x + wch, (y0 + y1) / 2), (x + wch - 40, y1), (x, y1),
               (x + (40 if k else 0), (y0 + y1) / 2)]
        fill = [core.BLUE_L, core.TEAL_L][k % 2]
        C.d.polygon(pts, fill=fill, outline=NAVY2)
        C.d.line(pts + [pts[0]], fill=NAVY2, width=3)
        C.text_in_box((x + 44, y0, x + wch - 40, y1), f"{st['id']}\n{st['name']}", 27, first_bold=True, min_size=20)
        owner = W.owner_of_process(st["id"], d)
        C.text_in_box((x, 510, x + wch - 10, 680), f"{name(owner, d)}\n{title(owner, d)}", 22, first_bold=True,
                      valign="top", min_size=17, fill=INK2)
        x += wch
    C.text(40, 750, "Accountable owner shown under each stage.", 22, fill=MUTED)
    return C.png_bytes()


def _fnol_triage_swim(d) -> bytes:
    S = Swimlane(2400, ["Customer / broker", "Contact Centre", "Claims Hub / CLARA", "Sentinel", "Triage (Claims Operations)"],
                 lane_h=200, title="FNOL to triage", subtitle="Process stages S1 and S2", right_note="v3.0")
    S.fit_cols(6.5)
    S.step("s", 0, 0, "Loss occurs", "start")
    S.step("a", 0, 1, "Report loss (phone, portal, app, broker)")
    S.step("b", 1, 1.9, "Receive notification (Harbour CRM)")
    S.step("c", 2, 2.8, "Validate policy and cover (PALM)")
    S.step("dup", 2, 3.9, "Duplicate? within ±3 days", "decision", w=230, h=110)
    S.step("e", 2, 5, "Create claim and default reserve")
    S.step("f", 3, 5.6, "Sentinel pre-screen score", kind="system")
    S.step("g", 4, 6.5, "Tier classification")
    S.step("ack", 1, 6.5, "Acknowledge customer (Notify)")
    S.edge("s", "a")
    S.edge("a", "b", sides="bl")
    S.edge("b", "c", sides="bl")
    S.edge("c", "dup")
    S.edge("dup", "e", "No", label_size=21)
    S.edge("e", "f", sides="bl")
    S.edge("f", "g", sides="bl", label="score passed to triage", label_size=21)
    S.edge("e", "ack", sides="tl", label_size=21, label="acknowledgement")
    S.edge("dup", "b", "Yes: link to existing", sides="tr", label_size=21)
    return S.png_bytes()


def _tier_route_swim(d) -> bytes:
    v = W.rule_version("BR-TRI-003", d)["parameters"]
    v6 = W.rule_version("BR-TRI-006", d)
    S = Swimlane(2400, ["Triage", "Major & Complex Loss", "Specialist claim handlers", "Fast track"], lane_h=230,
                 title="Tiering and routing", subtitle="BR-TRI-003 v3, BR-TRI-004, BR-TRI-006 v3", right_note="Stage S2")
    S.fit_cols(5.6)
    S.step("s", 0, 0, "Scored claim", "start")
    S.step("t", 0, 1, f"Incurred ≥ £{v['tier3_min_gbp']:,}, injury, litigation or total loss?", "decision",
           w=250, h=130, size=21)
    S.step("t2", 0, 2.6, "Tier-2 test: £5,000 or more, or third party?", "decision", w=250, h=130, size=21)
    S.step("m", 1, 1.8, "Tier-3: assign major loss handler")
    S.step("h", 2, 3.5, "Tier-2: specialist claim handler")
    S.step("ft", 0, 4.3, "Fast-track test", "decision", w=220, h=110)
    S.step("f", 3, 5.6, "Fast track: Tier-1, score below 30, no injury, cap £2,000", w=300)
    S.step("q", 2, 5.6, "Tier-1 handler queue")
    S.edge("s", "t")
    S.edge("t", "m", "Yes → Tier-3 within 4 hours", sides="bl", label_size=21)
    S.edge("t", "t2", "No", label_size=21)
    S.edge("t2", "h", "Yes", sides="bl", label_size=21)
    S.edge("t2", "ft", "No", label_size=21)
    S.edge("ft", "f", "meets BR-TRI-006", sides="bl", label_size=21)
    S.edge("ft", "q", "otherwise", sides="rt", label_size=21)
    return S.png_bytes()


def _reserving_swim(d) -> bytes:
    S = Swimlane(2400, ["Claim handler", "Team leader / authority holder", "Claims Hub / CLARA", "Reinsurance (ReCede)"],
                 lane_h=220, title="Reserving", subtitle="Stage S4 · BR-RSV-001, 003, 007, 011", right_note="Stage S4")
    S.fit_cols(6.0)
    S.step("s", 0, 0, "Claim created", "start")
    S.step("a", 0, 1, "Set initial reserve within 2 business days")
    S.step("b", 2, 2, "Authority check (BR-RSV-003)", kind="system")
    S.step("c", 1, 3, "Approve above handler authority")
    S.step("r", 0, 4, "Tier-3 reserve review every 14 days")
    S.step("l", 2, 5, "Movement above LLNT £250,000?", "decision", w=230, h=120, size=21)
    S.step("n", 3, 6, "Notify ReCede within 24 hours")
    S.edge("s", "a")
    S.edge("a", "b", sides="bl")
    S.edge("b", "c", "above authority", sides="tl", label_size=21)
    S.edge("c", "r", sides="tl")
    S.edge("r", "l", sides="bl")
    S.edge("l", "n", "Yes", sides="bl", label_size=21)
    return S.png_bytes()


def _fraud_swim(d) -> bytes:
    v = W.rule_version("BR-FRD-031", d)
    thr = v["parameters"]["threshold"]
    S = Swimlane(2400, ["Sentinel", "Claims Hub / CLARA", "Counter-Fraud & SIU", "Customer (Notify)"], lane_h=220,
                 title="Fraud referral", subtitle=f"Stage S5 · rules in force on {fmt_date_long(d)}", right_note="Stage S5")
    S.fit_cols(6.5)
    S.step("s", 0, 0, "Score received", "start")
    S.step("d", 1, 1, f"Referral decision: score ≥ {thr} (all tiers)", "decision", w=260, h=130, size=21)
    S.step("r", 1, 2.6, "Create SIU referral (same business day)")
    S.step("t", 2, 3.6, "SIU triage within 3 business days")
    S.step("n", 3, 4.4, "Notice within 10 business days of referral")
    S.step("o", 2, 5.4, "Investigation and outcome NF / CF / WD")
    S.step("h", 2, 6.5, "Human review of adverse outcome")
    S.edge("s", "d", sides="bl")
    S.edge("d", "r", "Yes", label_size=21)
    S.edge("r", "t", sides="bl")
    S.edge("r", "n", sides="bl", aoff=60, label="notice due", label_size=21)
    S.edge("t", "o")
    S.edge("o", "h")
    return S.png_bytes()


def _settlement_swim(d) -> bytes:
    S = Swimlane(2400, ["Claim handler", "Claims Hub / CLARA", "External services", "Payments Operations"], lane_h=220,
                 title="Settlement", subtitle="Stage S6 · PS-STL-01 to PS-STL-05", right_note="Stage S6")
    S.fit_cols(6.2)
    S.step("s", 0, 0, "Cover confirmed", "start")
    S.step("a", 0, 1, "Settlement offer within 5 business days")
    S.step("b", 1, 2, "Payment authorisation (BR-STL-002)", kind="system")
    S.step("c", 2, 3, "WatchScreen sanctions screening")
    S.step("p", 3, 4, "Payment run Mon–Fri 16:30 (Corvane Payments Gateway)")
    S.step("z", 1, 5, "Close claim and zero reserve (ST movement)", kind="system")
    S.step("e", 1, 6.2, "", "end")
    S.edge("s", "a")
    S.edge("a", "b", sides="bl")
    S.edge("b", "c", sides="bl")
    S.edge("c", "p", "cleared", sides="bl", label_size=21)
    S.edge("p", "z", "confirmed", sides="tb", label_size=21)
    S.edge("z", "e")
    return S.png_bytes()


def _recovery_swim(d) -> bytes:
    S = Swimlane(2400, ["Claims Assessor / handler", "Recoveries & Subrogation", "SUBTRAK / CLARA", "Quarryhill Solicitors"],
                 lane_h=220, title="Recovery & Subrogation", subtitle=f"Stage S7 · owner {name('P013', d)}",
                 right_note="Stage S7")
    S.fit_cols(5.8)
    S.step("s", 0, 0, "Third party at fault", "start")
    S.step("a", 0, 1, "Flag recovery potential")
    S.step("b", 1, 2, "Open subrogation case")
    S.step("q", 1, 3.3, "Recoverable ≥ £1,000?", "decision", w=240, h=120, size=21)
    S.step("c", 1, 4.6, "Send demand within 10 business days")
    S.step("l", 3, 4.6, "Litigation ≥ £25,000 or liability defended")
    S.step("r", 2, 5.8, "Receipt and reserve adjustment", kind="system")
    S.step("w", 2, 3.3, "Close or write off", kind="system")
    S.edge("s", "a")
    S.edge("a", "b", sides="bl")
    S.edge("b", "q")
    S.edge("q", "c", "Yes", label_size=21)
    S.edge("q", "w", "No", sides="bt", label_size=21)
    S.edge("c", "l", "≥ £25,000 or liability defended", sides="bt", label_size=21)
    S.edge("c", "r", sides="rt")
    return S.png_bytes()


def _raci(d) -> bytes:
    rows = []
    for st in sorted(W.steps.values(), key=lambda s: s["order"]):
        rac = st.get("raci") or {}
        R = ", ".join(team_name(t, d) for t in rac.get("R", []))
        A = name(rac["A"], d) if rac.get("A") else ""
        rows.append([st["id"], st["name"], R, A, st["sla"]["text"]])
    tim = table_image(["Step", "Name", "Responsible", "Accountable", "SLA"], rows, [190, 520, 560, 330, 700],
                      title="Responsibility matrix by process step", size=20,
                      note=f"RACI as approved on {fmt_date_long(d)}.")
    return tim.png_bytes()


# ==========================================================================================
# VS032 Claims Organisation Chart 2024 (document) (2024-03-01, P005) — stale chart (C02)
# ==========================================================================================
def _reports(pid: str, d: str) -> list[str]:
    out = [q for q in W.people if W.employed(q, d) and W.manager_of(q, d) == pid]
    return sorted(out, key=lambda q: (title(q, d), name(q, d)))


def _org_node(pid: str, d: str, depth: int = 9, style_fn=None, inline: bool = False) -> dict:
    n = {"name": f"{name(pid, d)} — {title(pid, d)}" if inline else name(pid, d),
         "title": "" if inline else title(pid, d), "pid": pid}
    if style_fn:
        n["style"] = style_fn(pid)
    if depth > 0:
        n["children"] = [_org_node(c, d, depth - 1, style_fn, inline) for c in _reports(pid, d)]
    return n


def _org_card_text(n):
    return n


def build_vs032() -> tuple[list[dict], str, int]:
    fid = "VS032"
    d = adate(fid)
    facts = Facts(fid, rel(fid))
    for p in ("P005", "P015", "P013", "P014"):
        guard(fid, f"PERSON:{p}", "titles")
    contents = ["1 Introduction", "2 Claims organisation chart", "3 Claims Operations UK", "4 Claims Operations Nordics",
                "5 Teams and team leaders", "6 Claims sites", "7 Reporting lines", "8 Glossary"]
    b = start_doc(
        fid, facts, "Claims directorate structure, reporting lines and sites", "CM-CLM-ORG-2024", "2024.1", "org",
        "the structure of the Claims directorate",
        versions_for(fid, "P005", [(60, "2023.2", "Second-half 2023 refresh"), (12, "2024.0d", "Draft for HR review"),
                                   (0, "2024.1", "Approved for publication")], "2024.1"),
        [approval("Owner", "P005", d), approval("Reviewer", "P011", d, minus_days(d, 3)),
         approval("Approver", "P004", d)],
        ["All Claims staff", "HR business partners", "Executive Committee"], contents,
        related=["Claims Organisation Chart 2024 (slides)"],
        intro_extra=["The chart is published as a single picture so that it prints on one page; it is not "
                     "re-typed in this text."])

    def style(pid):
        t = (title(pid, d) or "").lower()
        if "recover" in t:
            return "vendor"
        if "siu" in t or "fraud" in t:
            return "alert"
        if "nordic" in t or W.location_of(pid, d) in ("LOC-OSL", "LOC-STO", "LOC-CPH"):
            return "service"
        return "target"

    # Figure 1: the single embedded org chart image (placement PL-132)
    pl = placement(fid, "vs32_stale")
    section(b, fid, "2", "Claims organisation chart", "the Claims directorate from the Claims Director down")
    root = _org_node("P005", d, 0, style, inline=True)
    cols = [_org_node(c, d, 9, style, inline=True) for c in _reports("P005", d)]
    above = {"name": f"{name('P004', d)} — {title('P004', d)}", "title": "", "style": "dark"}
    cv = org_chart("Claims organisation chart", f"Effective {fmt_date_long(d)}", root, cols, col_w=600, card_h=84,
                   size=23, above=above, right_note="Claims directorate",
                   footer=f"Owner: {name('P005', d)} · Published {fmt_date_short(d)} · Corvane Internal",
                   legend=[("target", "Claims Operations UK"), ("service", "Nordics"), ("alert", "SIU"),
                           ("vendor", "Recoveries")], indent=40, gap_y=24)
    b.figure(cv.png_bytes(), f"Claims organisation chart, {fmt_date_long(d)}",
             "Organisation chart of the Claims directorate showing each manager and their direct reports.",
             facts=[placement_spec(pl, "Martin Calloway — Recoveries Manager",
                                   also_in_ids=["VS004-F007", "corpus/upload/visuals/VS004_org_chart_2024.pptx"],
                                   notes="stale 2024 chart (C02): Calloway left 2024-12-31; Freya Lindahl owns S7 from 2025-09-01"),
                    spec("temporal", "2024 org chart image: Ingrid Sørensen — Claims Director (name before 2025-08-23).",
                         "Ingrid Sørensen — Claims Director", "PERSON:P005#name_history"),
                    spec("image_text", "On the 2024 chart Siobhan Quill (Recoveries Team Leader) reports to Martin Calloway.",
                         "Siobhan Quill — Recoveries Team Leader", "PERSON:P014#reports_to"),
                    spec("temporal", "On the 2024 chart Freya Lindahl is Senior Recoveries Manager – Nordics.",
                         "Freya Lindahl — Senior Recoveries Manager – Nordics", "PERSON:P013#titles"),
                    spec("image_text", "On the 2024 chart Niall Brannigan is Head of SIU reporting to the Claims Director.",
                         "Niall Brannigan — Head of SIU", "PERSON:P008#titles")])

    # Figure 2: UK detail
    section(b, fid, "3", "Claims Operations UK", "the UK operations teams and their leaders")
    uk = _org_node("P011", d, 9, style)
    cv = org_chart("Claims Operations UK", f"Effective {fmt_date_long(d)}", {"name": uk["name"], "title": uk["title"],
                   "style": "target"}, uk["children"], col_w=430, card_h=104, size=22,
                   right_note="Leeds · Bristol · Glasgow", indent=36, gap_y=22)
    b.figure(cv.png_bytes(), "Claims Operations UK",
             "Organisation chart of Claims Operations UK with team leaders and their reports.",
             facts=[spec("image_text", "In March 2024 Ewan Strachan (Contact Centre Manager) reports to Rob Tennant.",
                         "Ewan Strachan", "PERSON:P029#reports_to"),
                    spec("image_text", "In March 2024 Rob Tennant's title is Head of Claims Operations UK.",
                         "Rob Tennant Head of Claims Operations UK", "PERSON:P011#titles")])

    # Figure 3: Nordics detail
    section(b, fid, "4", "Claims Operations Nordics", "the Nordic operations teams")
    no = _org_node("P012", d, 9, style)
    cv = org_chart("Claims Operations Nordics", f"Effective {fmt_date_long(d)}", {"name": no["name"], "title": no["title"],
                   "style": "service"}, no["children"], col_w=560, card_h=104, size=22,
                   right_note="Oslo · Stockholm · Copenhagen", indent=36, gap_y=22)
    b.figure(cv.png_bytes(), "Claims Operations Nordics",
             "Organisation chart of Claims Operations Nordics with the Nordic recoveries and assessment leads.",
             facts=[spec("image_text", "In March 2024 Mette Dahl is Head of Claims Operations Nordics.",
                         "Head of Claims Operations Nordics", "PERSON:P012#titles"),
                    spec("image_text", "Astrid Nygaard is Claims Assessment Lead – Nordics.", "Astrid Nygaard",
                         "PERSON:P034#titles")])

    # Figure 4: team register
    section(b, fid, "5", "Teams and team leaders", "each Claims team, its leader and its home site")
    rows = []
    for tid in ("T02", "T03", "T04", "T05", "T06", "T07", "T08", "T09", "T10", "T11"):
        lead = W.team_lead(tid, d)
        loc = W.locations[W.location_of(lead, d)]["name"] if lead else ""
        rows.append([tid, team_name(tid, d), name(lead, d) if lead else "", title(lead, d) if lead else "", loc])
    tim = table_image(["Team", "Team name", "Team leader", "Leader title", "Site"], rows, [120, 520, 380, 620, 420],
                      title=f"Claims teams at {fmt_date_long(d)}", size=22)
    b.figure(tim.png_bytes(), "Claims teams and team leaders",
             "Table image listing the Claims teams with team name, team leader, leader title and site.",
             facts=[spec("image_table", "In March 2024 team T08 is named 'Recoveries' and is led by Martin Calloway from Bristol.",
                         "Recoveries", "TEAM:T08#lead_history"),
                    spec("image_table", "In March 2024 team T11 is named 'Special Investigations Unit (SIU)'.",
                         "Special Investigations Unit (SIU)", "TEAM:T11#name_history")])

    # Figure 5: sites map
    section(b, fid, "6", "Claims sites", "where Claims teams are based")
    b.figure(_sites_map(d), "Claims sites",
             "Schematic map of the UK and Nordic offices with the Claims functions at each site.",
             facts=[spec("image_text", "Bristol Recoveries Centre hosts Recoveries & Subrogation (UK) and Payments Operations.",
                         "Bristol Recoveries Centre", "LOC:LOC-BRS#functions"),
                    spec("image_text", "Glasgow Contact Centre handles FNOL calls.", "Glasgow Contact Centre", "LOC:LOC-GLA")])

    # Figure 6: reporting lines table
    section(b, fid, "7", "Reporting lines", "every role in the directorate with its line manager")
    people = []

    def walk(pid):
        for c in _reports(pid, d):
            people.append(c)
            walk(c)
    walk("P005")
    rows = [[name(p, d), title(p, d), name(W.manager_of(p, d), d), W.locations[W.location_of(p, d)]["city"]] for p in people]
    tim = table_image(["Name", "Title", "Reports to", "Office"], rows, [430, 760, 430, 260],
                      title="Reporting lines in the Claims directorate", size=22)
    b.figure(tim.png_bytes(), "Reporting lines",
             "Table image of each person in the Claims directorate with title, line manager and office.",
             facts=[spec("image_table", "Callum Fairbairn (Motor Claims Team Leader, Leeds) reports to Rob Tennant.",
                         "Motor Claims Team Leader", "PERSON:P022#titles",
                         notes="Corvane Callum Fairbairn (P022), not the IBM namesake P051")])
    glossary(b, fid, "8", [("SIU", "Special Investigations Unit"), ("MCL", "Major & Complex Loss"),
                           ("TL", "Team leader")])
    path = out_path(fid)
    b.save(path)
    return facts.items, str(path), b.fig_no


def _sites_map(d) -> bytes:
    from .diagrams import SchematicMap
    M = SchematicMap(2300, 1900, -8.5, 20.5, 49.6, 63.2, top=130)
    M.title_band("Claims sites", f"Offices with Claims teams, {fmt_date_long(d)}", right="Schematic, not to scale")
    sites = [("LOC-LDS", -1.55, 53.80, 380, 820), ("LOC-BRS", -2.60, 51.45, 330, 1390), ("LOC-GLA", -4.25, 55.86, 330, 520),
             ("LOC-LON", -0.12, 51.50, 1040, 1530), ("LOC-OSL", 10.75, 59.91, 1060, 470),
             ("LOC-STO", 18.07, 59.33, 1840, 760), ("LOC-CPH", 12.57, 55.68, 1700, 1300)]
    for lid, lon, lat, lx, ly in sites:
        loc = W.locations[lid]
        fn = ", ".join(loc["functions"][:3])
        M.callout(lon, lat, lx, ly, f"{loc['name']}\n{fn}", color=NAVY2, size=22, max_w=600)
    return M.png_bytes()

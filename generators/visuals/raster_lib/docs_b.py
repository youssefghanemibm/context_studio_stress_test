"""Image-led DOCX builders VS033-VS035."""
from __future__ import annotations

import math

from generators.common import util

from . import charts, core
from .core import (AMBER, AMBER_L, BLUE_L, GREEN, GREY_L, GRID, INK, INK2, LINE, MUTED, NAVY, NAVY2, RED, TEAL, WHITE,
                   Canvas, fmt_date_long, fmt_date_short)
from .ctx import W, adate, guard, minus_days, name, out_path, placement, rel, sysname, svcname, team_name, title
from .diagrams import Diagram, Swimlane, Timeline, table_image
from .facts import Facts, arrow_spec, chart_spec, placement_spec, spec
from .skeleton import approval, glossary, section, start_doc, versions_for

FORBIDDEN_042 = "02:15"


def _live(iid: str, d: str) -> bool:
    i = W.interfaces[iid]
    return str(i["since"]) <= d


def _sched(iid: str, d: str, fid: str) -> str:
    """Interface schedule as of d; raises if this file may not state it."""
    guard(fid, f"INTERFACE:{iid}", "schedule")
    return W.interface_schedule(iid, d)


def _sys(sid, d):
    return sysname(sid, d)


# ==========================================================================================
# VS033 Interface Diagram Pack (raster) (2026-06-15, P050)
# ==========================================================================================
def build_vs033() -> tuple[list[dict], str, int]:
    fid = "VS033"
    d = adate(fid)
    facts = Facts(fid, rel(fid))
    guard(fid, "INTERFACE:CLX-IF-042", "schedule")
    contents = ["1 Introduction", "2 Interface landscape", "3 Reserve movement chain", "4 Fraud and SIU interfaces",
                "5 Payments and finance interfaces", "6 Claims Hub interfaces", "7 Interface catalogue",
                "8 Impact of a change to CLX-IF-042", "9 MQ queues", "10 Glossary"]
    b = start_doc(
        fid, facts, "Raster diagrams of the CLARA and Claims Hub interfaces", "CM-INT-DP-033", "2.1", "arch",
        "the CLARA and Claims Hub interface landscape",
        versions_for(fid, "P050", [(150, "1.0", "First issue after the integration discovery"),
                                   (70, "2.0", "Kafka bridge (CLX-IF-049) added"),
                                   (0, "2.1", "Approved; schedules re-checked with Integration Platform")], "2.1"),
        [approval("Author", "P050", d), approval("Reviewer", "P031", d, minus_days(d, 5)),
         approval("Reviewer", "P049", d, minus_days(d, 5)), approval("Approver", "P018", d)],
        ["Integration Platform", "Legacy Claims Platforms (CLARA)", "Hub Squad – Reserve & Finance", "Data & Analytics"],
        contents, related=["Interface register", "Architecture Decisions – Diagram Pack"],
        intro_extra=["The diagrams are exported as images from the integration team's drawing workspace. "
                     "Interface identifiers follow the CLX-IF-nnn register."])

    section(b, fid, "2", "Interface landscape", "every system that exchanges data with CLARA")
    b.figure(_landscape(fid, d), "CLARA interface landscape",
             "Hub-and-spoke diagram of CLARA and the systems it exchanges data with, labelled with interface identifiers.",
             facts=[arrow_spec("Arrow label between CLARA and Sentinel: CLX-IF-008, CLX-IF-009 and CLX-IF-010.",
                         "CLX-IF-008", "INTERFACE:CLX-IF-008", notes="labels on spokes of a raster diagram"),
                    arrow_spec("Arrow label between CLARA and Subrogation Tracker: CLX-IF-022 and CLX-IF-023.",
                         "CLX-IF-022", "INTERFACE:CLX-IF-022")])

    pl42 = placement(fid, "vs33_042sched")
    pl47 = placement(fid, "vs33_047")
    section(b, fid, "3", "Reserve movement chain", "how reserve movements leave CLARA and reach their consumers")
    b.figure(_reserve_chain(fid, d), "Reserve movement chain",
             "Diagram of the reserve movement extract from CLARA through the MQ Backbone to the ledger, warehouse, "
             "reinsurance system and Kafka bridge, with onward feeds.",
             facts=[placement_spec(pl42, "CLX-IF-042 — daily 02:15 — DB2 unload → MQ CLR.RSVMOVE.OUT",
                                   notes="the only statement of the CLX-IF-042 schedule in the corpus; raster arrow label"),
                    placement_spec(pl47, "CLX-IF-047 daily 04:15 → ReCede"),
                    arrow_spec("Raster arrow label: CLX-IF-043 GL Reserve Journal Feed runs daily 03:45.",
                         "CLX-IF-043 daily 03:45", "INTERFACE:CLX-IF-043#schedule_history"),
                    arrow_spec("Raster arrow label: CLX-IF-044 CDW Reserve Fact Load runs daily 04:00.",
                         "CLX-IF-044 daily 04:00", "INTERFACE:CLX-IF-044#schedule"),
                    arrow_spec("Raster arrow label: CLX-IF-049 Kafka bridge runs daily 02:45.",
                         "CLX-IF-049 daily 02:45", "INTERFACE:CLX-IF-049#schedule"),
                    arrow_spec("Raster arrow label: CLX-IF-058 CDW to Actuarial Reserving Workbench, monthly, "
                                       "3rd business day.", "CLX-IF-058 monthly, 3rd business day",
                         "INTERFACE:CLX-IF-058#schedule")])
    b.comment_on_last("Schedules on this figure were re-checked against the scheduler export before approval.",
                      name("P031", d), "HV", minus_days(d, 4),
                      fact=spec("comment", "Reviewer comment (Henrik Vestergaard): the reserve chain schedules were "
                                           "re-checked against the scheduler export.", "re-checked against the scheduler export",
                                None))

    section(b, fid, "4", "Fraud and SIU interfaces", "the interfaces between CLARA, Claims Hub, Sentinel and the SIU Case Manager")
    rows = ["CLX-IF-008", "CLX-IF-009", "CLX-IF-010", "CLX-IF-011", "CLX-IF-012", "CLX-IF-036", "CLX-IF-041"]
    b.figure(_flow_list(fid, d, "Fraud and SIU interfaces", rows), "Fraud and SIU interfaces",
             "List diagram of fraud and SIU interfaces with source, target, protocol and schedule on each arrow.",
             facts=[arrow_spec("CLX-IF-009 Nightly Sentinel batch scoring request runs daily 00:15 (SFTP CSV).",
                         "daily 00:15", "INTERFACE:CLX-IF-009#schedule"),
                    arrow_spec("CLX-IF-011 sends fraud referrals from CLARA to SIU Case Manager as XML over MQ "
                                       "(queue CLR.SIUREF.OUT).", "CLR.SIUREF.OUT", "INTERFACE:CLX-IF-011#format")])

    section(b, fid, "5", "Payments and finance interfaces", "the payment, sanctions and ledger interfaces")
    rows = ["CLX-IF-017", "CLX-IF-018", "CLX-IF-019", "CLX-IF-020", "CLX-IF-021", "CLX-IF-027", "CLX-IF-028", "CLX-IF-029"]
    b.figure(_flow_list(fid, d, "Payments and finance interfaces", rows), "Payments and finance interfaces",
             "List diagram of sanctions, payment and general-ledger interfaces with protocol and schedule.",
             facts=[arrow_spec("CLX-IF-019 UK payment batch: ISO 20022 pain.001 XML over SFTP, Mon-Fri 16:30.",
                         "Mon-Fri 16:30", "INTERFACE:CLX-IF-019#schedule"),
                    arrow_spec("CLX-IF-027 sends currency rates from Group Ledger to CLARA daily 03:15.",
                         "daily 03:15", "INTERFACE:CLX-IF-027#schedule")])

    section(b, fid, "6", "Claims Hub interfaces", "the interfaces of the Claims Hub platform, live and planned")
    rows = [i for i in ("CLX-IF-034", "CLX-IF-035", "CLX-IF-036", "CLX-IF-037", "CLX-IF-038", "CLX-IF-039", "CLX-IF-040",
                        "CLX-IF-045", "CLX-IF-050", "CLX-IF-054", "CLX-IF-056", "CLX-IF-057")]
    b.figure(_flow_list(fid, d, "Claims Hub interfaces", rows, show_planned=True), "Claims Hub interfaces",
             "List diagram of Claims Hub interfaces; interfaces going live with Wave 1 are marked planned.",
             facts=[arrow_spec("CLX-IF-038 Claims Hub payments to the Corvane Payments Gateway is planned for 2026-09-14.",
                         "planned 2026-09-14", "INTERFACE:CLX-IF-038#since"),
                    arrow_spec("CLX-IF-057 telematics crash alerts reach Claims Hub as JSON on Kafka (eig.telematics.alert.v1).",
                         "eig.telematics.alert.v1", "INTERFACE:CLX-IF-057#format")])

    section(b, fid, "7", "Interface catalogue", "the catalogue of interfaces by identifier")
    ids = sorted(W.interfaces)
    half = 30
    for k, chunk in enumerate((ids[:half], ids[half:])):
        rows = []
        for iid in chunk:
            i = W.interfaces[iid]
            st = "live" if _live(iid, d) else f"planned {i['since']}"
            rows.append([iid, i["name"], f"{_sys(i['source_system'], d)} → {_sys(i['target_system'], d)}", i["protocol"],
                         name(i["owner"], d), st])
        tim = table_image(["Interface", "Name", "Source → target", "Protocol", "Owner", "Status"], rows,
                          [190, 560, 720, 190, 330, 260], title=f"Interface catalogue ({chunk[0]} to {chunk[-1]})",
                          size=20, note="Schedules are shown on the flow diagrams, not in the catalogue.")
        fx = []
        if k == 0:
            fx = [spec("image_table", "CLX-IF-022 SUBTRAK synchronisation is owned by Freya Lindahl.",
                       "SUBTRAK synchronisation", "INTERFACE:CLX-IF-022#owner")]
        else:
            fx = [spec("image_table", "CLX-IF-033 Fraud referral return (NISA-FR1) was still planned on 2026-06-15 "
                                      "(live 2026-07-07).", "planned 2026-07-07", "INTERFACE:CLX-IF-033#since"),
                  spec("image_table", "CLX-IF-042 Reserve Movement Daily Extract is owned by Henrik Vestergaard.",
                       "Reserve Movement Daily Extract", "INTERFACE:CLX-IF-042#owner")]
        b.figure(tim.png_bytes(), f"Interface catalogue, part {k + 1}",
                 f"Table image of interfaces {chunk[0]} to {chunk[-1]} with name, source and target, protocol, owner and status.",
                 facts=fx)

    section(b, fid, "8", "Impact of a change to CLX-IF-042", "which interfaces, systems, reports and teams depend on CLX-IF-042")
    b.figure(_impact_042(fid, d), "Impact of a change to CLX-IF-042",
             "Dependency tree from CLX-IF-042 through first-hop and second-hop interfaces to the regulatory return and "
             "the monthly IBNR run, with consumer teams.",
             facts=[spec("image_text", "Hop 1 from CLX-IF-042: CLX-IF-043, CLX-IF-044, CLX-IF-047, CLX-IF-049.",
                         "CLX-IF-049 Reserve Movement Kafka Bridge", "INTERFACE:CLX-IF-042#dependents"),
                    spec("image_text", "Hop 2 from CLX-IF-042: CLX-IF-051, CLX-IF-055, CLX-IF-058.", "CLX-IF-055",
                         "INTERFACE:CLX-IF-042#dependents"),
                    spec("image_text", "Hop 3: the NISA-TP2 return and the Reserving team's monthly IBNR run.",
                         "monthly IBNR run", "REPORT:NISA-TP2"),
                    spec("image_text", "Consumer teams affected by a CLX-IF-042 change include Reinsurance and Regulatory Reporting.",
                         "Regulatory Reporting", "INTERFACE:CLX-IF-042#dependents")])

    section(b, fid, "9", "MQ queues", "the MQ queue managers and the CLARA queues they carry")
    b.figure(_mq_map(fid, d), "MQ queue map",
             "Diagram of the two queue managers and the CLARA inbound and outbound queues with their interfaces.",
             facts=[spec("image_text", "CLARA's MQ queue manager is CLRQM01 on z/OS; the distributed queue manager is HUBQM01.",
                         "HUBQM01", "SYSTEM:SYS14#tech"),
                    spec("image_text", "Queue CLR.LLN.OUT carries large loss notifications to ReCede (CLX-IF-031).",
                         "CLR.LLN.OUT", "INTERFACE:CLX-IF-031#format")])
    glossary(b, fid, "10", [("MQ", "IBM MQ messaging (MQ Backbone)"), ("CDW", "Claims Data Warehouse"),
                            ("ARW", "Actuarial Reserving Workbench"), ("GL", "Group Ledger"),
                            ("RSVMOVE", "Reserve movement record layout"), ("ESP", "Event Streaming Platform")])
    path = out_path(fid)
    b.save(path)
    # self-check: the 042 schedule may appear only in figure 2
    return facts.items, str(path), b.fig_no


def _short(sid, d):
    nm = _sys(sid, d)
    return {"Claims Data Warehouse": "CDW", "Actuarial Reserving Workbench": "Actuarial Reserving Workbench"}.get(nm, nm)


def _landscape(fid, d) -> bytes:
    pairs: dict[str, list[str]] = {}
    for iid, i in sorted(W.interfaces.items()):
        if not _live(iid, d):
            continue
        if "SYS01" in (i["source_system"], i["target_system"]):
            other = i["target_system"] if i["source_system"] == "SYS01" else i["source_system"]
            pairs.setdefault(other, []).append(iid)
    others = sorted(pairs, key=lambda s: s)
    Wd, Hd = 3000, 1900
    D = Diagram(Wd, Hd)
    D.title_band("CLARA interface landscape", f"Live interfaces on {fmt_date_long(d)} · labels show interface identifiers",
                 right="Interface Diagram Pack")
    cx, cy = Wd / 2, 1000
    D.node("SYS01", (cx - 230, cy - 90, cx + 230, cy + 90), "CLARA\nCOBOL / CICS / DB2", "legacy", size=30)
    n = len(others)
    for k, sid in enumerate(others):
        ang = -math.pi / 2 + 2 * math.pi * k / n
        x, y = cx + 1220 * math.cos(ang), cy + 700 * math.sin(ang)
        st = "platform" if sid in ("SYS14", "SYS15") else ("target" if sid == "SYS02" else "external")
        D.node(sid, (x - 200, y - 55, x + 200, y + 55), _sys(sid, d), st, size=24)
    for sid in others:
        ids = [x.replace("CLX-IF-", "") for x in pairs[sid]]
        lab = "CLX-IF-" + "/".join(ids) if len(ids) <= 3 else "CLX-IF-" + "/".join(ids[:3]) + "\n/" + "/".join(ids[3:])
        outward = any(W.interfaces[x]["source_system"] == "SYS01" for x in pairs[sid])
        inward = any(W.interfaces[x]["target_system"] == "SYS01" for x in pairs[sid])
        a, b2 = ("SYS01", sid) if outward else (sid, "SYS01")
        D.edge_straight(a, b2, lab if len(ids) > 1 else pairs[sid][0], label_t=0.55 if outward else 0.45,
                        label_size=20, both=outward and inward)
    D.legend(40, Hd - 140, [("legacy", "CLARA"), ("platform", "Integration platform"), ("external", "Connected system")],
             cols=3, col_w=380, size=20)
    return D.png_bytes()


def _reserve_chain(fid, d) -> bytes:
    for iid in ("CLX-IF-042", "CLX-IF-043", "CLX-IF-044", "CLX-IF-047", "CLX-IF-049", "CLX-IF-051", "CLX-IF-055", "CLX-IF-058"):
        guard(fid, f"INTERFACE:{iid}", "schedule")
    s42 = W.interface_schedule("CLX-IF-042", d)
    D = Diagram(3100, 1450)
    D.title_band("Reserve movement chain", f"Schedules in force on {fmt_date_long(d)} (UK time)", right="Figure 2 · raster export")
    D.node("clara", (60, 590, 500, 850), "CLARA\nCLR.T_RESERVE_MOVEMENT\nextract program CLRRS170", "legacy", size=26)
    D.node("mq", (1000, 600, 1380, 840), "MQ Backbone\nCLRQM01 / HUBQM01", "platform", size=27)
    hop1 = [("gl", "SYS06", "CLX-IF-043", 190), ("cdw", "SYS11", "CLX-IF-044", 480), ("rc", "SYS07", "CLX-IF-047", 770),
            ("esp", "SYS15", "CLX-IF-049", 1060)]
    for nid, sid, iid, y in hop1:
        D.node(nid, (1880, y, 2230, y + 190), _sys(sid, d), "external" if sid != "SYS15" else "platform", size=26)
    hop2 = [("nisa", "NISA Reporting Hub", "gl", "CLX-IF-051"), ("arw", "Actuarial Reserving Workbench", "cdw", "CLX-IF-058"),
            ("bdx", "Bordereaux Exchange", "rc", "CLX-IF-055"), ("re", "reserve-engine (Claims Hub)", "esp", None)]
    for nid, label, src, iid in hop2:
        y0 = D.nodes[src][1]
        D.node(nid, (2720, y0 + 10, 3070, y0 + 180), label, "service" if nid == "re" else "external", size=24)
    D.edge("clara", "mq", label=f"CLX-IF-042 — {s42} —\nDB2 unload → MQ CLR.RSVMOVE.OUT", label_size=23,
           label_outline=NAVY2, label_bold=False, width=5, label_xy=(750, 650))
    for k, (nid, sid, iid, y) in enumerate(hop1):
        ya = 720 + (k - 1.5) * 40
        yb = y + 95
        sched = W.interface_schedule(iid, d)
        tgt = {"SYS07": " → ReCede"}.get(sid, "")
        D.edge("mq", nid, label=f"{iid} {sched}{tgt}", sides="rl", aoff=ya - 720,
               via=[(1500 + k * 22, ya), (1500 + k * 22, yb)], label_size=21, label_xy=(1700, yb),
               label_outline=GRID)
    for nid, label, src, iid in hop2:
        if iid:
            sched = W.interface_schedule(iid, d)
            D.edge(src, nid, label=f"{iid} {sched}", label_size=20, label_outline=GRID, label_max_w=450)
        else:
            D.edge(src, nid, label="claims.reserve.movement.v1", label_size=20, label_outline=GRID, label_max_w=450)
    D.legend(60, 1240, [("legacy", "CLARA (source)"), ("platform", "Integration platform"), ("external", "Consumer system"),
                        ("service", "Claims Hub service")], cols=4, col_w=420, size=21)
    return D.png_bytes()


def _flow_list(fid, d, heading, ids, show_planned=False) -> bytes:
    rows = [i for i in ids if show_planned or _live(i, d)]
    rh = 150
    D = Diagram(2800, 200 + rh * len(rows) + 60)
    D.title_band(heading, f"Source → target, protocol and schedule as at {fmt_date_long(d)}", right="Interface Diagram Pack")
    y = 180
    for k, iid in enumerate(rows):
        i = W.interfaces[iid]
        planned = not _live(iid, d)
        D.node(f"s{k}", (60, y, 560, y + 110), _sys(i["source_system"], d),
               "legacy" if i["source_system"] == "SYS01" else ("target" if i["source_system"] == "SYS02" else "external"), size=25)
        D.node(f"t{k}", (2240, y, 2740, y + 110), _sys(i["target_system"], d),
               "legacy" if i["target_system"] == "SYS01" else ("target" if i["target_system"] == "SYS02" else "external"), size=25)
        sched = _sched(iid, d, fid)
        status = f"planned {i['since']}" if planned else sched
        lab = f"{iid} {i['name']} · {i['protocol']} · {status}\n{i['format']}"
        D.edge(f"s{k}", f"t{k}", label=lab, label_size=21, label_max_w=1500, dash=(14, 10) if planned else None,
               label_outline=GRID)
        y += rh
    return D.png_bytes()


def _impact_042(fid, d) -> bytes:
    imp = W.impact("CLX-IF-042")
    D = Diagram(2900, 1500)
    D.title_band("Impact of a change to CLX-IF-042", "Downstream interfaces by hop, reports and consumer teams",
                 right="Change impact view")
    D.node("root", (60, 620, 440, 800), "CLX-IF-042\nReserve Movement Daily Extract", "legacy", size=25)
    D.text(250, 560, "Change here", 24, True, fill=RED, anchor="ma")
    ys1 = [200, 500, 800, 1100]
    for iid, y in zip(imp["hops"][1], ys1):
        i = W.interfaces[iid]
        D.node(iid, (720, y, 1180, y + 170), f"{iid}\n{i['name']}\n→ {_short(i['target_system'], d)}", "warn", size=23)
        D.edge("root", iid, sides="rl", label_size=20)
    for iid in imp["hops"][2]:
        i = W.interfaces[iid]
        parent = i["depends_on"][0]
        y = D.nodes[parent][1]
        D.node(iid, (1430, y, 1890, y + 170), f"{iid}\n{i['name']}\n→ {_short(i['target_system'], d)}", "alert", size=23)
        D.edge(parent, iid, sides="rl")
    D.node("tp2", (2150, 200, 2560, 370), "Hop 3: NISA-TP2\nQuarterly Technical Provisions Return", "alert", size=23)
    D.node("ibnr", (2150, 500, 2560, 670), "Hop 3: Reserving team's\nmonthly IBNR run", "alert", size=23)
    D.edge("CLX-IF-051", "tp2", sides="rl")
    D.edge("CLX-IF-058", "ibnr", sides="rl")
    teams = ", ".join(team_name(t, d) for t in imp["teams"])
    D.node("teams", (1430, 1180, 2840, 1400), f"Consumer teams to notify\n{teams}", "note", size=24)
    D.text(720, 1430, "Hop 1 = direct dependents; hop 2 = dependents of hop 1; hop 3 = reports and runs fed by hop 2.",
           21, fill=MUTED)
    return D.png_bytes()


def _mq_map(fid, d) -> bytes:
    D = Diagram(2800, 1450)
    D.title_band("MQ queue map", "CLARA queues on the MQ Backbone", right=f"As at {fmt_date_short(d)}")
    D.zone((60, 200, 1260, 1330), "z/OS LPAR PRD1 · queue manager CLRQM01", fill="#F7F1E6", outline=core.LEGACY)
    D.zone((1560, 200, 2740, 1330), "Distributed · queue manager HUBQM01", fill="#EEF6EE", outline=GREEN)
    qs_in = [("CLR.FNOL.IN", "CLX-IF-001 from MyCorvane Claims"), ("CLR.EVIDENCE.IN", "CLX-IF-004 from Evidence Intake Gateway"),
             ("CLR.SIUOUT.IN", "CLX-IF-012 from SIU Case Manager")]
    qs_out = [("CLR.SIUREF.OUT", "CLX-IF-011 to SIU Case Manager"), ("CLR.LLN.OUT", "CLX-IF-031 to ReCede"),
              ("CLR.RSVMOVE.OUT", "CLX-IF-042 to GL adapter, CDW, ReCede, Kafka bridge")]
    y = 280
    D.text(110, y, "Inbound queues", 26, True, fill=core.LEGACY)
    y += 50
    for k, (q, lab) in enumerate(qs_in):
        D.node(f"qi{k}", (110, y, 1200, y + 120), f"{q}\n{lab}", "legacy", shape="queue", size=24, align="left")
        y += 150
    y += 30
    D.text(110, y, "Outbound queues", 26, True, fill=core.LEGACY)
    y += 50
    for k, (q, lab) in enumerate(qs_out):
        D.node(f"qo{k}", (110, y, 1200, y + 120), f"{q}\n{lab}", "legacy", shape="queue", size=24, align="left")
        y += 150
    cons = [("GL adapter → Group Ledger", "CLX-IF-043"), ("CDW reserve fact load", "CLX-IF-044"),
            ("ReCede cession input", "CLX-IF-047"), ("MQ-to-Kafka bridge", "CLX-IF-049")]
    y = 330
    for k, (lab, iid) in enumerate(cons):
        D.node(f"c{k}", (1700, y, 2600, y + 130), f"{lab}\n{iid}", "platform", size=25)
        y += 190
    D.edge("qo2", "c0", sides="rl", via=[(1380, D.nodes["qo2"][1] + 60), (1380, D.nodes["c0"][1] + 65)])
    for k in (1, 2, 3):
        D.edge("qo2", f"c{k}", sides="rl", via=[(1380 + k * 18, D.nodes["qo2"][1] + 60),
                                                  (1380 + k * 18, D.nodes[f"c{k}"][1] + 65)])
    D.label(1410, 1180, "channel CLRQM01 ↔ HUBQM01", 22, outline=GRID)
    return D.png_bytes()


# ==========================================================================================
# VS034 Reserving Dashboard Narrative – Q3 2026 (2026-10-09, P009)
# ==========================================================================================
def build_vs034() -> tuple[list[dict], str, int]:
    fid = "VS034"
    d = adate(fid)
    facts = Facts(fid, rel(fid))
    guard(fid, "INCIDENT:INC-2026-0702", "recovery_metric")
    guard(fid, "INCIDENT:INC-2026-0702", "root_cause")
    guard(fid, "RULE:BR-RSV-003@v3", "text")
    guard(fid, "TIMELINE:metrics", "tier3_share_pct")
    contents = ["1 Introduction", "2 Overdue Tier-3 reviews after the cadence change", "3 Review cadence history",
                "4 Parallel run and cut-over timeline", "5 The July 2026 cadence mismatch", "6 Reserve movement types",
                "7 Reserve authority levels", "8 Dashboard tiles", "9 Glossary"]
    b = start_doc(
        fid, facts, "Narrative to accompany the Q3 2026 reserving dashboard", "CM-RSV-DN-2026Q3", "1.0", "fin",
        "the reserving dashboard for the third quarter of 2026",
        versions_for(fid, "P009", [(14, "0.1", "Draft charts"), (5, "0.2", "Review comments from Actuarial"),
                                   (0, "1.0", "Final for the Reserving Committee pack")], "1.0"),
        [approval("Author", "P009", d), approval("Reviewer", "P010", d, minus_days(d, 3)),
         approval("Reviewer", "P041", d, minus_days(d, 3)), approval("Approver", "P001", d)],
        ["Reserving Committee members", "Actuarial", "Financial Control", "Hub Squad – Reserve & Finance"],
        contents, related=["Reserving dashboard (Q3 2026)", "Incident record INC-2026-0702"],
        intro_extra=["The dashboard extracts are pasted as images. Figures in this narrative are not re-keyed; "
                     "read the values from the charts."])

    pl = placement(fid, "vs34_overdue")
    section(b, fid, "2", "Overdue Tier-3 reviews after the cadence change",
            "the daily count of overdue Tier-3 reserve reviews in early July 2026")
    b.figure(_overdue_chart(d), "Overdue Tier-3 reserve reviews, July 2026",
             "Line chart of overdue Tier-3 reserve reviews by day in early July 2026, falling to zero.",
             facts=[placement_spec(pl, "2026-07-02: 412 overdue",
                                   notes="chart-only and exclusive; the end point '2026-07-10: 0 overdue' is on the same chart"),
                    chart_spec("Overdue Tier-3 reserve reviews reached zero on 2026-07-10.", "2026-07-10: 0 overdue",
                         "INCIDENT:INC-2026-0702#recovery_metric", exclusive=True,
                         notes="same exclusive placement PL-135 (end point)")])
    b.comment_on_last("Intermediate days are plotted from the daily snapshot; only the start and end values are labelled.",
                      name("P010", d), "SMC", minus_days(d, 4),
                      fact=spec("comment", "Reviewer comment (Sebastian Moreau-Clarke): only the start and end values of "
                                           "the overdue-reviews chart are labelled.", "only the start and end values are labelled",
                                None))

    section(b, fid, "3", "Review cadence history", "how the Tier-3 reserve review cadence has changed")
    b.figure(_cadence_chart(d), "Tier-3 reserve review cadence over time",
             "Step chart of the Tier-3 reserve review cadence in days by effective date.",
             facts=[chart_spec("Tier-3 reserve review cadence: 30 days from 2015-01-01, 21 days from 2024-01-01, "
                                       "14 days from 2026-07-01.", "14 days from 2026-07-01", "RULE:BR-RSV-007"),
                    chart_spec("The 21-day cadence applied from 2024-01-01 to 2026-06-30.", "21 days from 2024-01-01",
                         "RULE:BR-RSV-007@v2")])

    section(b, fid, "4", "Parallel run and cut-over timeline", "the reserve parallel run and the cut-over waves")
    b.figure(_parallel_timeline(fid, d), "Reserve parallel run and cut-over waves",
             "Timeline of the reserve parallel run, Wave 0 and Wave 1 cut-overs and the July incident.",
             facts=[spec("image_text", "Reserve parallel run (CLARA vs reserve-engine): 2026-03-02 to 2026-08-28.",
                         "2026-03-02 to 2026-08-28", "TIMELINE:programme#parallel_run.from"),
                    spec("image_text", "Wave 1 UK motor cut-over on 2026-09-14.", "Wave 1 UK motor", "WAVE:MW-1#date")])

    section(b, fid, "5", "The July 2026 cadence mismatch", "what caused the July mismatch and how it was fixed")
    b.figure(_incident_diagram(d), "INC-2026-0702 cause and fix",
             "Diagram comparing the CLARA parameter and the reserve-engine configuration for the Tier-3 review cadence, "
             "with the fix ticket.",
             facts=[spec("image_text", "INC-2026-0702: CLARA picked up RSV_T3_REVIEW_DAYS = 14 on 2026-07-01 while "
                                       "reserve-engine tier3-review-days was still 21.", "tier3-review-days = 21",
                         "INCIDENT:INC-2026-0702#root_cause"),
                    spec("image_text", "Fix CHUB-322 changed reserve-engine tier3-review-days from 21 to 14.",
                         "CHUB-322", "INCIDENT:INC-2026-0702#fix_tickets"),
                    spec("image_text", "INC-2026-0702 was a Sev3 incident owned by Daniel Achebe.", "cadence mismatch Sev3",
                         "INCIDENT:INC-2026-0702#severity")])

    section(b, fid, "6", "Reserve movement types", "the movement type codes used on the dashboard")
    mv = [("IN", "Initial"), ("AD", "Adjustment"), ("IX", "Indexation"), ("RV", "Review"), ("ST", "Settlement close"),
          ("RC", "Recovery")]
    tim = table_image(["Code", "Movement type", "Source"], [[c, n, "CLR.T_RESERVE_MOVEMENT.MOVE_TYPE_CD"] for c, n in mv],
                      [160, 420, 760], title="Reserve movement types", size=24)
    b.figure(tim.png_bytes(), "Reserve movement type codes",
             "Table image of reserve movement type codes and their meaning.",
             facts=[spec("image_table", "Reserve movement type ST means settlement close; IX means indexation.",
                         "Settlement close", "TABLE:CLR.T_RESERVE_MOVEMENT#columns.MOVE_TYPE_CD")])

    section(b, fid, "7", "Reserve authority levels", "the reserve authority ladder")
    b.figure(_authority_chart(d), "Reserve authority by level",
             "Horizontal bar chart of reserve authority limits by role, from Claims Handler to Claims Director.",
             facts=[chart_spec("Reserve authority: Team Leader £100,000; Claims Manager £500,000.", "£500,000",
                         "RULE:BR-RSV-003@v3#parameters"),
                    chart_spec("Reserve authority for the Claims Director is £2,000,000; above that the Reserving "
                                       "Committee.", "£2,000,000", "RULE:BR-RSV-003@v3#parameters")])

    section(b, fid, "8", "Dashboard tiles", "the headline tiles of the dashboard")
    b.figure(_tiles(d), "Dashboard headline tiles",
             "Four dashboard tiles: Tier-3 share of 2025 claims, Tier-3 review cadence, LLNT and the parallel-run status.",
             facts=[spec("image_text", "Tier-3 share of claims in 2025: 4.1%.", "4.1%", "TIMELINE:metrics#tier3_share_pct"),
                    spec("image_text", "Large loss notification threshold (LLNT) £250,000.", "£250,000",
                         "RULE:BR-RSV-011@v2")])
    glossary(b, fid, "9", [("Tier-3", "Highest claim tier (BR-TRI-003)"), ("LLNT", "Large loss notification threshold"),
                           ("Parallel run", "CLARA and reserve-engine run side by side and are reconciled"),
                           ("Sev3", "Incident severity 3")])
    path = out_path(fid)
    b.save(path)
    return facts.items, str(path), b.fig_no


def _overdue_chart(d) -> bytes:
    inc = W.incidents["INC-2026-0702"]
    # end points come from the world (412 on 2026-07-02, 0 on 2026-07-10); intermediate points are unlabelled
    days = ["2026-07-02", "2026-07-03", "2026-07-04", "2026-07-05", "2026-07-06", "2026-07-07", "2026-07-08",
            "2026-07-09", "2026-07-10"]
    start, end = 412, 0
    frac = [0, 0.04, 0.18, 0.27, 0.45, 0.66, 0.83, 0.95, 1.0]
    vals = [round(start + (end - start) * f) for f in frac]
    labels = [x[5:] for x in days]
    im = charts.line_chart(list(range(len(days))), {"Overdue Tier-3 reviews": vals},
                           title="Overdue Tier-3 reserve reviews (daily snapshot)", ylabel="Overdue reviews",
                           xtick_labels=labels, ylim=(0, 470),
                           annotate=[(0, vals[0], "2026-07-02: 412 overdue", (40, -10)),
                                     (8, vals[-1], "2026-07-10: 0 overdue", (-250, 90))],
                           annotate_size=17, w_in=13, h_in=6.8)
    return core.png_bytes(im)


def _cadence_chart(d) -> bytes:
    import matplotlib.dates as mdates
    import datetime as dtm
    r = W.rules["BR-RSV-007"]
    xs, ys = [], []
    for v in r["versions"]:
        xs.append(dtm.date.fromisoformat(v["effective_from"]))
        ys.append(v["parameters"]["review_days"])
    xs.append(dtm.date.fromisoformat(d))
    ys.append(ys[-1])
    fig, ax = charts.new_fig(13, 6.5)
    ax.step(xs, ys, where="post", color=charts.SERIES[0], linewidth=3.5)
    ax.set_ylim(0, 36)
    ax.set_ylabel("Review cadence (days)")
    ax.set_title("Tier-3 reserve review cadence (BR-RSV-007)", loc="left", pad=16)
    for v in r["versions"]:
        x = dtm.date.fromisoformat(v["effective_from"])
        ax.annotate(f"{v['parameters']['review_days']} days from {v['effective_from']}", (x, v["parameters"]["review_days"]),
                    xytext=(10, 12), textcoords="offset points", fontsize=17, fontweight="bold", color="#1B2430")
    ax.xaxis.set_major_locator(mdates.YearLocator(2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.grid(axis="y", color="#D5DBE3")
    fig.tight_layout()
    return core.png_bytes(charts.fig_to_image(fig))


def _parallel_timeline(fid, d) -> bytes:
    pr = W.timeline["programme"]["parallel_run"]
    guard(fid, "TIMELINE:programme", "parallel_run.from")
    guard(fid, "TIMELINE:programme", "parallel_run.to")
    T = Timeline(2400, 900, "2026-01-01", "2026-12-31", left=340, top=240, title="Reserve parallel run and cut-over",
                 subtitle="CLARA and reserve-engine reconciled daily during the parallel run",
                 right_note=f"As at {fmt_date_short(d)}", quarters=True)
    T.lane(240, 440, "Reserving", fill="#F7F9FC")
    T.bar(pr["from"], pr["to"], 340, f"Reserve parallel run {pr['from']} to {pr['to']}", "service", h=64, size=23)
    T.lane(440, 700, "Cut-over", fill=WHITE)
    T.milestone(W.waves["MW-0"]["date"], 600, "Wave 0 Denmark\n2026-06-01", NAVY2, size=22)
    T.milestone(W.waves["MW-1"]["date"], 600, "Wave 1 UK motor\n2026-09-14", NAVY2, size=22)
    T.lane(700, 860, "Incidents", fill="#F7F9FC")
    T.milestone("2026-07-02", 800, "INC-2026-0702", RED, size=21, above=False, r=14)
    T.today_line(d, f"Report date {fmt_date_short(d)}")
    return T.png_bytes()


def _incident_diagram(d) -> bytes:
    inc = W.incidents["INC-2026-0702"]
    D = Diagram(2400, 1150)
    D.title_band("INC-2026-0702: Tier-3 review cadence mismatch",
                 f"{inc['severity']} · {inc['start'].replace('T', ' ')} to {inc['end'].replace('T', ' ')} · owner {name(inc['owner'], d)}",
                 right="Root cause and fix")
    D.node("clara", (80, 230, 960, 500), "CLARA (CLR.T_PARAM)\nRSV_T3_REVIEW_DAYS = 14\nvalid from 2026-07-01 (CHUB-318)",
           "legacy", size=27)
    D.node("re", (1440, 230, 2320, 500), "reserve-engine configuration\ntier3-review-days = 21\n(not yet changed)",
           "alert", size=27)
    D.edge("clara", "re", "parallel-run reconciliation\nflags mismatched Tier-3 claims", both=True, label_size=23,
           label_outline=RED, width=5)
    D.node("fix", (1440, 680, 2320, 940), "Fix CHUB-322\nreserve-engine: tier3-review-days 21 → 14", "platform", size=27)
    D.edge("re", "fix", "corrected", sides="bt", label_size=22)
    D.node("why", (80, 680, 960, 940), "Root cause\nThe CLARA parameter changed on 2026-07-01 but the reserve-engine "
           "configuration still held the old value.", "note", size=24)
    D.text(80, 1010, "Programs and systems involved: CLRRS110 (CLARA), reserve-engine (Claims Hub).", 22, fill=INK2)
    return D.png_bytes()


def _authority_chart(d) -> bytes:
    roles = ["Claims Handler", "Team Leader", "Claims Manager", "Claims Director"]
    vals = [25000, 100000, 500000, 2000000]
    labs = ["£25,000", "£100,000", "£500,000", "£2,000,000"]
    im = charts.bar_chart(roles, vals, title="Reserve authority by role (BR-RSV-003)", ylabel="Authority limit (GBP)",
                          value_labels=labs, horizontal=True, w_in=13, h_in=6, ylim=(0, 2600000),
                          note="Above the Claims Director limit: Reserving Committee.")
    return core.png_bytes(im)


def _tiles(d) -> bytes:
    C = Canvas(2400, 760, "#F4F6F9")
    C.title_band("Reserving dashboard · headline tiles", "Q3 2026", right=f"Extract {fmt_date_short(d)}")
    tiles = [("Tier-3 share of claims, 2025", "4.1%", "share of claims classed Tier-3"),
             ("Tier-3 review cadence", "14 days", "BR-RSV-007 v3 since 2026-07-01"),
             ("Large loss notification threshold", "£250,000", "LLNT · notify ReCede within 24 hours"),
             ("Reserve parallel run", "Completed", "ended 2026-08-28")]
    x = 40
    for lab, val, sub in tiles:
        C.rect((x, 200, x + 550, 680), fill=WHITE, outline=GRID, width=2, radius=14)
        C.text(x + 30, 240, lab, 24, True, fill=INK2)
        C.text(x + 30, 330, val, 66, True, fill=NAVY)
        C.text_in_box((x + 10, 470, x + 540, 660), sub, 23, fill=MUTED, align="left", valign="top", pad=20)
        x += 585
    return C.png_bytes()


# ==========================================================================================
# VS035 Fraud Workflow Image Pack (2026-10-05, P042)
# ==========================================================================================
def build_vs035() -> tuple[list[dict], str, int]:
    fid = "VS035"
    d = adate(fid)
    facts = Facts(fid, rel(fid))
    for ref in ("RULE:BR-FRD-031@v2", "RULE:BR-FRD-036@v2", "RULE:BR-FRD-032@v2", "RULE:BR-FRD-035@v2",
                "RULE:BR-FRD-033@v1", "RULE:BR-FRD-034@v1"):
        guard(fid, ref, "text")
    guard(fid, "RULE:BR-FRD-036@v2", "parameters")
    contents = ["1 Introduction", "2 Referral workflow end to end", "3 Referral decision", "4 Customer notice and deferral",
                "5 SIU triage and outcome", "6 NISA-FR1 return", "7 Threshold history", "8 Events and interfaces",
                "9 Pre-screen points", "10 Glossary"]
    b = start_doc(
        fid, facts, "Workflow images for fraud referral after the October 2026 rule change", "CM-FRD-WF-035", "1.0",
        "fraud", "the fraud referral workflow in Claims Hub",
        versions_for(fid, "P042", [(16, "0.1", "Draft workflows"), (6, "0.2", "Updated after the Fraud Rules Workshop"),
                                   (0, "1.0", "Final for go-live of the new thresholds")], "1.0"),
        [approval("Author", "P042", d), approval("Reviewer", "P027", d, minus_days(d, 2)),
         approval("Reviewer", "P037", d, minus_days(d, 2)), approval("Approver", "P008", d)],
        ["Counter-Fraud & SIU", "Hub Squad – Fraud & Settlement", "Compliance", "Claims Operations team leaders"],
        contents, related=["Fraud rules catalogue", "Process Maps Handbook"])

    section(b, fid, "2", "Referral workflow end to end", "the referral workflow across systems and teams")
    b.figure(_frd_e2e(d), "Fraud referral workflow end to end",
             "Swimlane of the fraud referral workflow from Sentinel scoring through SIU referral, customer notice and outcome.",
             facts=[spec("lane_only", "fraud-referral-svc creates the SIU referral and sends it to SIU Case Manager (CLX-IF-041).",
                         "CLX-IF-041", "INTERFACE:CLX-IF-041")])

    section(b, fid, "3", "Referral decision", "the referral decision logic in force from 1 October 2026")
    b.figure(_frd_decision(d), "Referral decision from 1 October 2026",
             "Decision diagram: refer at a Sentinel score of 65 or more; for Tier-3 claims refer at 60 or more.",
             facts=[spec("image_text", "From 2026-10-01 Tier-3 claims are referred at a Sentinel score of 60 or more; "
                                       "the general threshold stays 65.", "Tier-3 and score ≥ 60", "RULE:BR-FRD-031@v2"),
                    spec("image_text", "No claim may be declined on the automated fraud score alone (BR-FRD-033).",
                         "never decline on the score alone", "RULE:BR-FRD-033@v1")])

    pl = placement(fid, "vs35_deferral")
    section(b, fid, "4", "Customer notice and deferral", "the customer notice and deferral path")
    b.figure(_frd_deferral(d), "Customer notice and deferral",
             "Workflow for the customer notice after a referral, including deferral for tipping-off risk.",
             facts=[placement_spec(pl, "Deferral > 30 days → Head of Counter-Fraud & SIU + notify Compliance"),
                    spec("image_text", "The customer notice may be deferred for up to 60 days where SIU certifies a "
                                       "tipping-off risk.", "maximum 60 days", "RULE:BR-FRD-036@v2#parameters.max_deferral_days"),
                    spec("image_text", "Notices use Notify templates FRN01 (letter) and FRN02 (SMS).", "FRN01",
                         "ADR:ADR-014")])
    b.comment_on_last("Workflow updated the day after the workshop; the deferral branch now reflects BR-FRD-036 v2.",
                      name("P027", d), "OL", minus_days(d, 17),
                      fact=spec("comment", "Reviewer comment (Oskar Lindgren): the deferral branch of Figure 3 reflects "
                                           "BR-FRD-036 v2.", "the deferral branch now reflects BR-FRD-036 v2",
                                "RULE:BR-FRD-036@v2"))

    section(b, fid, "5", "SIU triage and outcome", "SIU triage, investigation and outcomes")
    b.figure(_frd_siu(d), "SIU triage and outcome",
             "Swimlane of SIU triage, surveillance approval, investigation outcome and human review.",
             facts=[spec("image_text", "SIU must triage a new referral within 3 business days (BR-FRD-035 v2).",
                         "Triage within 3 business days", "RULE:BR-FRD-035@v2"),
                    spec("image_text", "Surveillance by Greyfold Investigations needs written approval by the SIU "
                                       "Investigations Manager (BR-FRD-010).", "Greyfold Investigations", "RULE:BR-FRD-010@v1"),
                    spec("image_text", "SIU cases close NF, CF or WD.", "investigate and close NF / CF / WD", "RULE:BR-FRD-011@v1")])

    section(b, fid, "6", "NISA-FR1 return", "how the quarterly fraud referral return is produced")
    b.figure(_frd_fr1(d), "NISA-FR1 quarterly return",
             "Flow from referrals in CLARA to the NISA Reporting Hub for the quarterly fraud referral return.",
             facts=[spec("image_text", "NISA-FR1 is due within 30 calendar days after quarter end; the first return "
                                       "(Q2 2026) was due 2026-07-30.", "2026-07-30", "RULE:BR-FRD-034@v1"),
                    arrow_spec("CLX-IF-033 runs quarterly, 5th business day after quarter end.",
                         "5th business day after quarter end", "INTERFACE:CLX-IF-033#schedule")])

    section(b, fid, "7", "Threshold history", "how the referral threshold has changed")
    b.figure(_frd_threshold_chart(d), "Referral threshold history",
             "Step chart of the fraud referral threshold since 2019, with the Tier-3 threshold from October 2026.",
             facts=[chart_spec("Referral threshold history: 75 from 2019-01-01, 70 from 2023-04-01, 65 from "
                                       "2026-04-01; Tier-3 60 from 2026-10-01.", "70 from 2023-04-01", "RULE:BR-FRD-012"),
                    chart_spec("Tier-3 referral threshold 60 from 2026-10-01.", "Tier-3: 60 from 2026-10-01",
                         "RULE:BR-FRD-031@v2#parameters.tier3_threshold")])

    section(b, fid, "8", "Events and interfaces", "the events and interfaces used by the fraud workflow")
    b.figure(_frd_events(d), "Fraud workflow events and interfaces",
             "Diagram of Kafka topics and REST interfaces between triage-svc, fraud-referral-svc, notification-svc and "
             "SIU Case Manager.",
             facts=[arrow_spec("fraud.referral.notice-due.v1 flows from fraud-referral-svc to notification-svc.",
                         "fraud.referral.notice-due.v1", "TOPIC:fraud.referral.notice-due.v1"),
                    arrow_spec("fraud.score.received.v1 flows from triage-svc to fraud-referral-svc.",
                         "fraud.score.received.v1", "TOPIC:fraud.score.received.v1")])

    section(b, fid, "9", "Pre-screen points", "the pre-screen point rules in force")
    rows = []
    for rid in sorted(W.rules):
        r = W.rules[rid]
        if r["area"] != "FRD":
            continue
        v = W.rule_version(rid, d)
        if v and "pre-screen points" in v["text"]:
            guard(fid, f"RULE:{rid}@v{v['version']}", "text")
            rows.append([rid, f"v{v['version']}", v["text"], v["effective_from"]])
    tim = table_image(["Rule", "Ver.", "Rule text", "Effective"], rows, [190, 90, 1500, 220],
                      title=f"Pre-screen point rules in force on {fmt_date_long(d)}", size=21)
    b.figure(tim.png_bytes(), "Pre-screen point rules",
             "Table image of pre-screen point rules with version, text and effective date.",
             facts=[spec("image_table", "BR-FRD-009: add 20 pre-screen points when the payee bank account is linked to 2 "
                                        "or more claimants.", "Add 20 pre-screen points", "RULE:BR-FRD-009@v1"),
                    spec("image_table", "BR-FRD-006 v2 adds 6 pre-screen points when the claimant address differs from the "
                                        "policy address.", "Add 6 pre-screen points", "RULE:BR-FRD-006@v2")])
    glossary(b, fid, "10", [("SIU", "Counter-Fraud & SIU"), ("FR1", "NISA quarterly fraud referral return"),
                            ("NF / CF / WD", "No fraud / confirmed fraud / withdrawn"),
                            ("Tipping-off risk", "Risk that a notice alerts a suspect to an investigation")])
    path = out_path(fid)
    b.save(path)
    return facts.items, str(path), b.fig_no


def _frd_e2e(d) -> bytes:
    S = Swimlane(2400, ["Sentinel", "triage-svc", "fraud-referral-svc", "SIU Case Manager", "notification-svc / Notify"],
                 lane_h=190, title="Fraud referral workflow", subtitle="Claims Hub, from 1 October 2026", right_note="Stage S5")
    S.fit_cols(6)
    S.step("s", 1, 0, "Claim triaged", "start")
    S.step("a", 0, 1, "Score claim (REST, CLX-IF-036)", kind="system")
    S.step("b", 1, 2, "Publish fraud.score.received.v1")
    S.step("c", 2, 3, "Referral decision (BR-FRD-031 v2)", "decision", w=230, h=100, size=21)
    S.step("e", 3, 4, "Create SIU case (CLX-IF-041)")
    S.step("f", 4, 4, "Notice due event")
    S.step("g", 3, 5.2, "Triage, investigate, outcome")
    S.step("h", 2, 6, "Record outcome")
    S.edge("s", "a", sides="tl")
    S.edge("a", "b", sides="bl", label="score", label_size=20)
    S.edge("b", "c", sides="bl")
    S.edge("c", "e", "refer", sides="bl", label_size=20)
    S.edge("c", "f", sides="bl", aoff=40, label="notice due", label_size=20, via=None)
    S.edge("e", "g")
    S.edge("g", "h", sides="tl")
    return S.png_bytes()


def _frd_decision(d) -> bytes:
    v = W.rule_version("BR-FRD-031", d)["parameters"]
    D = Diagram(2300, 1350)
    D.title_band("Referral decision from 1 October 2026", "BR-FRD-031 v2 (decision DEC-014)", right="Fraud Workflow Image Pack")
    D.node("in", (840, 170, 1460, 290), "Sentinel score received", "target", size=27)
    D.node("q1", (850, 360, 1450, 620), f"Score ≥ {v['threshold']}?", "warn", shape="diamond", size=28)
    D.node("q2", (850, 720, 1450, 980), "Tier-3 claim?", "warn", shape="diamond", size=28)
    D.node("ref", (1700, 420, 2240, 560), "Refer to SIU (all claims)", "alert", size=27)
    D.node("ref3", (1700, 780, 2240, 920), f"Tier-3 and score ≥ {v['tier3_threshold']}\n→ refer to SIU", "alert", size=26)
    D.node("no", (850, 1090, 1450, 1210), "Continue normal handling", "platform", size=26)
    D.node("rule", (60, 420, 640, 920), "Safeguard (BR-FRD-033)\nA referral is not a decision: never decline on the score alone. "
           "Every adverse outcome needs a documented human review.", "note", size=24)
    D.edge("in", "q1", sides="bt")
    D.edge("q1", "ref", "Yes", label_size=23)
    D.edge("q1", "q2", "No", sides="bt", label_size=23)
    D.edge("q2", "ref3", f"Yes and score ≥ {v['tier3_threshold']}", label_size=23)
    D.edge("q2", "no", "No", sides="bt", label_size=23)
    return D.png_bytes()


def _frd_deferral(d) -> bytes:
    v = W.rule_version("BR-FRD-036", d)["parameters"]
    D = Diagram(2400, 1400)
    D.title_band("Customer notice and deferral", "BR-FRD-032 v2 and BR-FRD-036 v2 (from 1 October 2026)",
                 right="Figure 3")
    D.node("ref", (60, 240, 520, 380), "SIU referral created", "target", size=27)
    D.node("q", (720, 190, 1260, 430), "Tipping-off risk certified by SIU?", "warn", shape="diamond", size=24)
    D.node("notice", (1500, 240, 2340, 380), "Send notice within 10 business days\n(Notify FRN01 letter / FRN02 SMS)",
           "service", size=24)
    D.node("q2", (720, 560, 1260, 800), "Deferral length?", "warn", shape="diamond", size=25)
    D.node("short", (60, 920, 760, 1120), f"Deferral ≤ 30 days\nrecord deferral (maximum {v['max_deferral_days']} days overall)",
           "target", size=24)
    D.node("long", (1300, 900, 2340, 1140),
           "Deferral > 30 days\n→ Head of Counter-Fraud & SIU\n+ notify Compliance (same day)", "alert", size=27,
           bold_first=False)
    D.edge("ref", "q")
    D.edge("q", "notice", "No", label_size=23)
    D.edge("q", "q2", "Yes", sides="bt", label_size=23)
    D.edge("q2", "short", "up to 30 days", sides="bt", label_size=22)
    D.edge("q2", "long", "beyond 30 days", sides="rt", label_size=22)
    D.text(60, 1230, f"Deferral never exceeds {v['max_deferral_days']} days. The deferral is recorded on the referral "
           "(customer_notice.deferred_until).", 22, fill=INK2)
    return D.png_bytes()


def _frd_siu(d) -> bytes:
    S = Swimlane(2400, ["SIU triage", "SIU Investigations Manager", "Investigation", "Claims Operations"], lane_h=210,
                 title="SIU triage and outcome", subtitle="BR-FRD-035 v2, BR-FRD-010, BR-FRD-011, BR-FRD-033, BR-FRD-017",
                 right_note="Stage S5")
    S.fit_cols(6)
    S.step("s", 0, 0, "Referral received", "start")
    S.step("a", 0, 1, "Triage within 3 business days")
    S.step("b", 1, 2, "Approve surveillance by Greyfold Investigations (written)")
    S.step("c", 2, 3, "Investigate and close NF / CF / WD")
    S.step("q", 2, 4.2, "Adverse outcome?", "decision", w=220, h=100)
    S.step("h", 3, 5.2, "Human review of adverse outcome")
    S.step("i", 3, 6, "Handler informed within 2 business days")
    S.edge("s", "a")
    S.edge("a", "b", "surveillance needed", sides="bl", label_size=20)
    S.edge("b", "c", sides="bl")
    S.edge("c", "q")
    S.edge("q", "h", "Yes", sides="bl", label_size=20)
    S.edge("h", "i")
    return S.png_bytes()


def _frd_fr1(d) -> bytes:
    i = W.interfaces["CLX-IF-033"]
    r = W.reports["NISA-FR1"]
    D = Diagram(2400, 1000)
    D.title_band("NISA-FR1 quarterly fraud referral return", f"Due {r['due']}", right="BR-FRD-034")
    D.node("clara", (60, 300, 560, 520), "CLARA / Claims Hub\nfraud referrals of the quarter", "legacy", size=26)
    D.node("hub", (1000, 300, 1500, 520), "NISA Reporting Hub", "external", size=27)
    D.node("nisa", (1900, 300, 2340, 520), "NISA", "dark", size=30)
    D.edge("clara", "hub", f"CLX-IF-033 · {i['protocol']} {i['format']}\n{W.interface_schedule('CLX-IF-033', d)}",
           label_size=21, label_outline=GRID)
    D.edge("hub", "nisa", "submit return", label_size=22)
    D.node("note", (60, 640, 2340, 880), f"First return: Q2 2026, due {r['first_due']}. Prepared by {name(r['preparer'], d)}; "
           f"signed by the {r['signed_by_role']}.", "note", size=25)
    return D.png_bytes()


def _frd_threshold_chart(d) -> bytes:
    import datetime as dtm
    import matplotlib.dates as mdates
    pts = [("2019-01-01", 75), ("2023-04-01", 70), ("2026-04-01", 65)]
    xs = [dtm.date.fromisoformat(a) for a, _ in pts] + [dtm.date.fromisoformat(d)]
    ys = [b for _, b in pts] + [65]
    fig, ax = charts.new_fig(13, 6.5)
    ax.step(xs, ys, where="post", color=charts.SERIES[0], linewidth=3.5, label="All claims")
    t3x = [dtm.date(2026, 10, 1), dtm.date.fromisoformat(d) + dtm.timedelta(days=60)]
    ax.step(t3x, [60, 60], where="post", color=charts.SERIES[4], linewidth=3.5, label="Tier-3 claims")
    ax.set_ylim(50, 82)
    ax.set_ylabel("Referral threshold (Sentinel score)")
    ax.set_title("Fraud referral threshold history", loc="left", pad=16)
    for (a, b), off in zip(pts, ((10, 10), (10, 10), (-210, 14))):
        ax.annotate(f"{b} from {a}", (dtm.date.fromisoformat(a), b), xytext=off, textcoords="offset points",
                    fontsize=17, fontweight="bold")
    ax.annotate("Tier-3: 60 from 2026-10-01", (dtm.date(2026, 10, 1), 60), xytext=(-330, -36), textcoords="offset points",
                fontsize=17, fontweight="bold", color=charts.SERIES[4])
    ax.xaxis.set_major_locator(mdates.YearLocator(1))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.legend(frameon=False, loc="upper right")
    ax.grid(axis="y", color="#D5DBE3")
    fig.tight_layout()
    return core.png_bytes(charts.fig_to_image(fig))


def _frd_events(d) -> bytes:
    D = Diagram(2400, 1150)
    D.title_band("Fraud workflow events and interfaces", "Kafka topics on esp-prd and REST interfaces",
                 right="Event Streaming Platform")
    D.node("sent", (80, 220, 520, 360), "Sentinel", "external", size=28)
    D.node("tri", (80, 600, 520, 740), "triage-svc", "service", size=28)
    D.node("frs", (980, 600, 1420, 740), "fraud-referral-svc", "service", size=28)
    D.node("siu", (1880, 220, 2320, 360), "SIU Case Manager", "external", size=28)
    D.node("ntf", (1880, 600, 2320, 740), "notification-svc", "service", size=28)
    D.node("rep", (980, 900, 1420, 1040), "reporting-feed-svc", "service", size=28)
    D.edge("tri", "sent", "CLX-IF-036 REST scoring", sides="tb", label_size=21, both=True)
    D.edge("tri", "frs", "fraud.score.received.v1", label_size=21, label_outline=GRID)
    D.edge("frs", "ntf", "fraud.referral.notice-due.v1", label_size=21, label_outline=GRID)
    D.edge("frs", "siu", "CLX-IF-041 REST", sides="tl", label_size=21)
    D.edge("frs", "rep", "fraud.referral.created.v1", sides="bt", label_size=21, label_outline=GRID)
    return D.png_bytes()

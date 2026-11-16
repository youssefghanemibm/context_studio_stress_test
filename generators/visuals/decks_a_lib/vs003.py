"""VS003 Interface Landscape (2026-08-24, Henrik Vestergaard, approved)."""
from __future__ import annotations

from collections import Counter

from . import common as CM
from . import phrases as P
from . import raster as R
from .core import Deck


def build(W, out_dir):
    D = Deck(W, "VS003", version="4.1", doc_ref="INT-CAT-001", out_dir=out_dir)
    d = D.date
    rng = D.rng
    sysn = lambda sid: W.system_name(sid, d)  # noqa: E731
    ifaces = list(W.interfaces.values())

    # 1 title
    D.title_slide(D.title, "CLARA and Claims Hub interfaces – maps, catalogue and impact paths",
                  [f"Integration Platform  |  Version {D.version}  |  {D.date_long()}",
                   f"Owner: {D.author}, {D.author_title}", "Status: Approved"])

    # 2 document control
    hist = CM.history_rows(D, [("3.0", "Catalogue re-baselined for Claims Hub"), ("4.0", "CLX-IF-049 bridge added"), ("4.1", "")],
                           spacing=(40, 120))
    CM.doc_control(D, hist, [("P018", "Approved (Design Authority)"), ("P032", "Approved")], status="Approved",
                   reviewers=[W.name_of(x, d) for x in ("P050", "P021", "P036", "P038")],
                   distribution="Design Authority, Integration Platform, interface owners, IBM Programme Skerry team",
                   purpose="Authoritative landscape of the CLX-IF interfaces between CLARA, Claims Hub and the wider estate.")

    # 3 scope
    s = D.content("Scope of this pack", "Interface landscape")
    n_live = sum(1 for i in ifaces if i["since"] <= d)
    s.bullets(0.6, 1.5, 7.2, 5.0, [
        f"The catalogue holds {len(ifaces)} interfaces, CLX-IF-001 to CLX-IF-{len(ifaces):03d}; {n_live} are live at the issue date.",
        "Each interface has one named owner and a criticality rating.",
        "Maps show direction and the interface identifier on each arrow; the catalogue pages list protocol, schedule and owner.",
        "Batch schedules are UK time and follow the batch scheduler calendar.",
        "Planned interfaces are included so that downstream teams can prepare.",
    ], size=14)
    s.box(8.3, 1.6, 4.5, 3.4, [{"text": "How to use this pack", "bold": True, "size": 14},
                               {"text": "Start from the maps to find the path, then look up the identifier in the catalogue for protocol, schedule and owner.", "size": 12}],
          style="tile", align="l", anchor="t", margins=0.18)
    s.notes(P.notes(rng, "the scope of the interface landscape", n_filler=1))
    D.fact(s, "text", f"The catalogue holds {len(ifaces)} interfaces, CLX-IF-001 to CLX-IF-060",
           "The interface catalogue holds 60 interfaces, CLX-IF-001 to CLX-IF-060.", kind="aggregate_source",
           world_ref="INTERFACE:*")

    # 4 reserve movement downstream map (connectors only)
    s = D.content("Reserve movement distribution – downstream map", "Maps")
    cla = s.box(0.3, 3.3, 1.5, 0.8, sysn("SYS01"), style="system", size=13, bold=True)
    mq = s.box(2.4, 3.3, 1.75, 0.8, sysn("SYS14"), style="system", size=13)
    esp = s.box(5.3, 1.45, 2.0, 0.8, sysn("SYS15"), style="system", size=12)
    gl = s.box(5.3, 2.85, 2.0, 0.8, sysn("SYS06"), style="system", size=12)
    cdw = s.box(5.3, 4.25, 2.0, 0.8, sysn("SYS11"), style="system", size=12)
    rec = s.box(5.3, 5.65, 2.0, 0.8, sysn("SYS07"), style="system", size=12)
    rse = s.box(8.8, 1.45, 2.0, 0.8, "reserve-engine", style="service", size=12)
    nrh = s.box(8.8, 2.85, 2.0, 0.8, sysn("SYS10"), style="system", size=12)
    arw = s.box(8.8, 4.25, 2.0, 0.8, sysn("SYS21"), style="system", size=11)
    bx = s.box(8.8, 5.65, 2.0, 0.8, sysn("SYS26"), style="external", size=12)
    tp2 = s.box(11.45, 2.85, 1.45, 0.8, "NISA-TP2 return", style="doc", size=10)
    ibnr = s.box(11.45, 4.25, 1.45, 0.8, "Monthly IBNR run", style="doc", size=10)
    s.connect(cla, mq, label="CLX-IF-042", name="map-042", label_dy=-0.3, label_size=9)
    s.connect(mq, esp, a_site="t", b_site="l", label="CLX-IF-049", name="map-049", label_size=9)
    s.connect(mq, gl, label="CLX-IF-043", name="map-043", label_size=9, label_dy=-0.12)
    s.connect(mq, cdw, label="CLX-IF-044", name="map-044", label_size=9, label_dy=0.12)
    s.connect(mq, rec, a_site="b", b_site="l", label="CLX-IF-047", name="map-047", label_size=9)
    s.connect(esp, rse, label="claims.reserve.movement.v1", name="map-topic", label_size=8, label_dy=-0.45)
    s.connect(gl, nrh, label="CLX-IF-051 (TP2)", name="map-051", label_size=9, label_dy=-0.3)
    s.connect(cdw, arw, label="CLX-IF-058", name="map-058", label_size=9, label_dy=-0.3)
    s.connect(rec, bx, label="CLX-IF-055 monthly", name="map-055", label_size=9, label_dy=-0.3)
    s.connect(nrh, tp2, dash=True, color="grey")
    s.connect(arw, ibnr, dash=True, color="grey")
    s.text(0.3, 5.9, 4.4, 0.8, [{"text": "Dashed arrows: reports produced from the receiving system.", "size": 9},
                                {"text": "Arrow labels: interface identifier or Kafka topic.", "size": 9}], size=9, color="slate")
    s.notes(P.notes(rng, "where reserve movements go after they leave CLARA",
                    ["Henrik Vestergaard owns both the reserve movement extract and the Kafka bridge."]))
    D.place("vs3_043", s, "connector", "MQ Backbone -> Group Ledger [label: CLX-IF-043]")
    D.place("vs3_051", s, "connector", "Group Ledger -> NISA Reporting Hub [label: CLX-IF-051 (TP2)]")
    D.place("vs3_047", s, "connector", "MQ Backbone -> ReCede [label: CLX-IF-047]")
    D.place("vs3_055", s, "connector", "ReCede -> Bordereaux Exchange [label: CLX-IF-055 monthly]")
    D.fact(s, "connector", "Claims Data Warehouse -> Actuarial Reserving Workbench [label: CLX-IF-058]",
           "Arrow Claims Data Warehouse → Actuarial Reserving Workbench labelled CLX-IF-058.", kind="arrow_only",
           world_ref="INTERFACE:CLX-IF-058#depends_on")
    D.fact(s, "connector", "MQ Backbone -> Claims Data Warehouse [label: CLX-IF-044]",
           "Arrow MQ Backbone → Claims Data Warehouse labelled CLX-IF-044.", kind="arrow_only",
           world_ref="INTERFACE:CLX-IF-044#depends_on")
    D.fact(s, "connector", "CLARA -> MQ Backbone [label: CLX-IF-042]",
           "Arrow CLARA → MQ Backbone labelled CLX-IF-042 (the reserve movement daily extract).", kind="arrow_only",
           world_ref="INTERFACE:CLX-IF-042")
    D.fact(s, "notes", "Henrik Vestergaard owns both the reserve movement extract and the Kafka bridge",
           "Speaker notes: Henrik Vestergaard owns CLX-IF-042 and CLX-IF-049.", kind="speaker_notes",
           world_ref="INTERFACE:CLX-IF-042#owner")

    # 5 payments landscape (raster)
    s = D.content("Payments and sanctions – interface map", "Maps")
    cv = R.Canvas(2400, 1250)
    cv.title("Payments and sanctions screening", "Daily cycle, UK time; labels show interface, protocol and schedule")
    E = R.Canvas.edge
    c = cv.box(120, 520, 420, 200, sysn("SYS01"), fill="grey_l", size=36, bold=True)
    ws = cv.box(980, 200, 480, 150, sysn("SYS19"), fill="white", size=32)
    cpg = cv.box(980, 880, 480, 150, sysn("SYS09"), fill="white", size=30)
    gl = cv.box(1820, 520, 460, 150, sysn("SYS06"), fill="white", size=32)
    sched = {x: W.interface_schedule(x, d) for x in ("CLX-IF-017", "CLX-IF-018", "CLX-IF-019", "CLX-IF-020", "CLX-IF-028")}
    for k in sched:
        D.need(f"INTERFACE:{k}", "schedule")
    cv.arrow([(540, 560), (980, 300)], f"CLX-IF-017 MQ {sched['CLX-IF-017']}", label_at=0.3, label_dy=-34)
    cv.arrow([(980, 340), (540, 600)], f"CLX-IF-018 MQ {sched['CLX-IF-018']}", label_at=0.72, label_dy=40)
    cv.arrow([(540, 660), (980, 920)], f"CLX-IF-019 SFTP {sched['CLX-IF-019']}", label_at=0.3, label_dy=-36)
    cv.arrow([(980, 990), (540, 710)], f"CLX-IF-020 SFTP {sched['CLX-IF-020']}", label_at=0.72, label_dy=40)
    cv.arrow([(540, 620), E(gl, "l")], f"CLX-IF-028 SFTP {sched['CLX-IF-028']}", label_at=0.72)
    png = cv.png()
    alt = (f"Payments map: CLARA sends sanctions screening requests to WatchScreen (CLX-IF-017, MQ, {sched['CLX-IF-017']}) "
           f"and receives results (CLX-IF-018, {sched['CLX-IF-018']}); the UK payment batch goes to Corvane Payments Gateway "
           f"(CLX-IF-019, SFTP, {sched['CLX-IF-019']}) with confirmations back (CLX-IF-020, {sched['CLX-IF-020']}); payment postings "
           f"go to Group Ledger (CLX-IF-028, {sched['CLX-IF-028']}).")
    s.picture_fit(png, 0.5, 1.35, 12.3, 5.55, alt=alt, title="Payments and sanctions interface map")
    s.notes(P.notes(rng, "the daily payments cycle", n_filler=1))
    D.fact(s, "image", f"CLX-IF-019 SFTP {sched['CLX-IF-019']}",
           f"Payments map image: the UK payment batch CLX-IF-019 runs over SFTP {sched['CLX-IF-019']}.",
           kind="image_text", world_ref="INTERFACE:CLX-IF-019#schedule")
    D.fact(s, "alt_text", f"CLX-IF-017, MQ, {sched['CLX-IF-017']}",
           f"Alt text: sanctions screening requests go from CLARA to WatchScreen via CLX-IF-017 (MQ, {sched['CLX-IF-017']}).",
           kind="alt_text", world_ref="INTERFACE:CLX-IF-017#schedule")

    # 6 section
    D.section("02", "Interface catalogue", "Protocol, schedule, owner and criticality for every CLX-IF interface")

    # 7-11 catalogue pages
    chunks = [ifaces[i:i + 12] for i in range(0, len(ifaces), 12)]
    cat_slide = {}
    for k, chunk in enumerate(chunks, 1):
        s = D.content(f"Interface catalogue ({k} of {len(chunks)}) – {chunk[0]['id']} to {chunk[-1]['id']}", "Catalogue")
        rows = []
        for i in chunk:
            if D.ok(f"INTERFACE:{i['id']}", "schedule"):
                sch = W.interface_schedule(i["id"], d)
            else:
                sch = "per batch scheduler"
            status = "planned" if i["since"] > d else i["status"]
            rows.append((i["id"], i["name"], i["protocol"], sch, W.name_of(i["owner"], d), i["criticality"], status))
        s.table(0.5, 1.4, 12.3, ["ID", "Name", "Protocol", "Schedule", "Owner", "Criticality", "Status"], rows,
                col_w=[1.05, 3.6, 1.0, 2.6, 1.7, 0.95, 0.8], row_h=0.4, size=9, first_col_bold=True)
        s.notes(P.notes(rng, f"catalogue entries {chunk[0]['id']} to {chunk[-1]['id']}", n_filler=1))
        for i in chunk:
            cat_slide[i["id"]] = s
    D.fact(cat_slide["CLX-IF-049"], "table", "Reserve Movement Kafka Bridge",
           "CLX-IF-049 Reserve Movement Kafka Bridge: Kafka, daily 02:45, owner Henrik Vestergaard, criticality High.",
           world_ref="INTERFACE:CLX-IF-049")
    D.fact(cat_slide["CLX-IF-043"], "table", "GL Reserve Journal Feed",
           "CLX-IF-043 GL Reserve Journal Feed is catalogued with schedule daily 03:45 (as at 2026-08-24), owner Hamish Gilchrist.",
           world_ref="INTERFACE:CLX-IF-043#schedule_history")
    D.fact(cat_slide["CLX-IF-033"], "table", "Fraud referral return (NISA-FR1)",
           "CLX-IF-033 Fraud referral return (NISA-FR1): SFTP, quarterly on the 5th business day after quarter end, owner Ruth Okafor.",
           world_ref="INTERFACE:CLX-IF-033")

    # 12 impact analysis (nested groups)
    s = D.content("Impact path – CLX-IF-042 Reserve Movement Daily Extract", "Impact analysis")
    imp = W.impact("CLX-IF-042")
    outer = s.group("CLX-IF-042 impact path")
    outer.box(0.5, 1.5, 2.0, 1.2, "CLX-IF-042", style="terminal", size=16, bold=True)
    cols = [("Hop 1", imp["hops"][1]), ("Hop 2", imp["hops"][2]),
            ("Hop 3", ["NISA-TP2 return", "Reserving monthly IBNR run"])]
    for ci, (h, items) in enumerate(cols):
        g = outer.group(f"Impact {h}")
        x = 2.9 + ci * 2.55
        g.box(x, 1.5, 2.35, 0.5, h, style="pentagon", size=12, bold=True)
        for j, it in enumerate(items):
            g.box(x, 2.15 + j * 0.62, 2.35, 0.52, it, style="process", size=10)
    tg = outer.group("Impacted teams")
    tg.box(10.6, 1.5, 2.25, 0.5, "Teams to notify", style="pentagon", size=12, bold=True, fill="amber")
    for j, t in enumerate(imp["teams"]):
        tg.box(10.6, 2.15 + j * 0.55, 2.25, 0.47, W.team_name(t, d), style="tile", size=9)
    s.text(0.5, 5.75, 9.8, 0.9, [{"text": "Any layout or timing change to CLX-IF-042 must be assessed along this path before it goes to the CAB.", "size": 12}],
           size=12, color="slate")
    s.notes(P.notes(rng, "the downstream impact of a change to the reserve movement extract",
                    ["The path was confirmed after INC-2025-0412, when a layout change to CLX-IF-042 broke the GL reserve journals."]))
    D.fact(s, "group", "Hop 2 CLX-IF-051 CLX-IF-055 CLX-IF-058",
           "Impact path of CLX-IF-042: hop 2 interfaces are CLX-IF-051, CLX-IF-055 and CLX-IF-058.",
           kind="visual_only", world_ref="INTERFACE:CLX-IF-042#dependents", shape_name="Impact Hop 2")
    D.fact(s, "group", "Hop 1 CLX-IF-043 CLX-IF-044 CLX-IF-047 CLX-IF-049",
           "Impact path of CLX-IF-042: hop 1 interfaces are CLX-IF-043, CLX-IF-044, CLX-IF-047 and CLX-IF-049.",
           kind="visual_only", world_ref="INTERFACE:CLX-IF-042#dependents", shape_name="Impact Hop 1")
    team_needle = "Teams to notify " + " ".join(W.team_name(t, d) for t in imp["teams"])
    D.fact(s, "group", team_needle,
           "Teams to notify for a CLX-IF-042 change: Reserving, Financial Control, Regulatory Reporting, Reinsurance, Data & Analytics and Hub Squad – Reserve & Finance.",
           kind="visual_only", world_ref="INTERFACE:CLX-IF-042#impact", shape_name="Impacted teams")
    D.fact(s, "notes", "INC-2025-0412, when a layout change to CLX-IF-042 broke the GL reserve journals",
           "Speaker notes: INC-2025-0412 – a layout change to CLX-IF-042 broke the GL reserve journals.",
           kind="speaker_notes", world_ref="INCIDENT:INC-2025-0412")

    # 13 protocol mix chart
    s = D.content("Interfaces by protocol", "Statistics")
    cnt = Counter(i["protocol"] for i in ifaces)
    cats = [k for k, _ in cnt.most_common()]
    s.chart(0.6, 1.4, 7.6, 5.4, "bar", cats, [("Interfaces", [cnt[c] for c in cats])],
            title="Interfaces by protocol (all 60, including planned)", legend=False)
    s.text(8.6, 1.6, 4.2, 3.0, [{"text": "Reading the chart", "bold": True, "size": 13},
                                {"text": "File transfer still dominates the CLARA estate; new Claims Hub interfaces use REST and Kafka.", "size": 12}],
           size=12, fill="grey_l", margins=0.15)
    s.notes(P.notes(rng, "the protocol mix across the estate", n_filler=1))
    D.fact(s, "chart", f"Interfaces: SFTP={cnt['SFTP']}",
           f"{cnt['SFTP']} of the 60 catalogued interfaces use SFTP.", kind="chart_only", world_ref="INTERFACE:*#protocol")
    D.fact(s, "chart", f"Interfaces: Kafka={cnt['Kafka']}",
           f"{cnt['Kafka']} of the 60 catalogued interfaces use Kafka.", kind="chart_only", world_ref="INTERFACE:*#protocol")

    # 14 criticality chart
    s = D.content("Interfaces by criticality", "Statistics")
    crit = Counter(i["criticality"] for i in ifaces)
    order = [c for c in ("Critical", "High", "Medium", "Low") if c in crit]
    s.chart(0.6, 1.4, 6.2, 5.4, "doughnut", order, [("Interfaces", [crit[c] for c in order])],
            title="Criticality rating", colors=["red", "amber", "sky", "grey"])
    crit_list = [i["id"] for i in ifaces if i["criticality"] == "Critical"]
    s.bullets(7.2, 1.6, 5.6, 5.0, [{"text": "Critical interfaces", "bold": True}] + crit_list, size=12)
    s.notes(P.notes(rng, "how criticality is spread across the estate", n_filler=1))
    D.fact(s, "chart", f"Interfaces: Critical={crit['Critical']}",
           f"{crit['Critical']} interfaces are rated Critical.", kind="chart_only", world_ref="INTERFACE:*#criticality")

    # 15 changes
    s = D.content("Changes since the previous issue", "Change log")
    s.bullets(0.6, 1.5, 12.0, 5.0, [
        "CLX-IF-033 Fraud referral return (NISA-FR1) added; live since 7 July 2026.",
        "CLX-IF-049 Reserve Movement Kafka Bridge recorded as live since 12 December 2025 (ADR-012).",
        "CLX-IF-045 Reserve change events now carry reserve.changed.v2 from reserve-engine (since 10 February 2026).",
        "CLX-IF-060 Claims Hub regulatory extracts added as planned, go-live 11 January 2027.",
        "Owner names refreshed after the September 2025 re-organisation.",
    ], size=14)
    s.notes(P.notes(rng, "what has changed in the catalogue"))
    D.fact(s, "text", "CLX-IF-033 Fraud referral return (NISA-FR1) added; live since 7 July 2026",
           "CLX-IF-033 (NISA-FR1 fraud referral return) has been live since 2026-07-07.", world_ref="INTERFACE:CLX-IF-033#since")

    # 16 owners
    owners = Counter(i["owner"] for i in ifaces)
    s = D.content("Interface owners", "Reference")
    rows = []
    for pid, n in owners.most_common():
        nm, tt = D.who(pid)
        rows.append((nm, tt, n))
    half = (len(rows) + 1) // 2
    for ci, part in enumerate((rows[:half], rows[half:])):
        s.table(0.5 + ci * 6.25, 1.4, 6.0, ["Owner", "Title", "Interfaces"], part, col_w=[1.7, 3.4, 0.9],
                row_h=0.36, size=9, first_col_bold=True, align=[None, None, "c"])
    s.notes(P.notes(rng, "who owns the interfaces", n_filler=1))
    top_pid, top_n = owners.most_common(1)[0]
    D.fact(s, "table", W.name_of(top_pid, d),
           f"{W.name_of(top_pid, d)} owns {top_n} interfaces, the most of any owner.", kind="aggregate_source",
           world_ref="INTERFACE:*#owner")
    return D

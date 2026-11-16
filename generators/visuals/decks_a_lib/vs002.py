"""VS002 Claims Hub Target Architecture (deck) (2026-03-16, Elin Fosse, approved)."""
from __future__ import annotations

from . import common as CM
from . import phrases as P
from . import raster as R
from .core import Deck


def live(W, iid, d):
    return (W.interfaces[iid].get("since") or "9999") <= d


def build(W, out_dir):
    D = Deck(W, "VS002", version="2.0", doc_ref="SKR-ARC-002", out_dir=out_dir)
    d = D.date
    rng = D.rng
    sysn = lambda sid: W.system_name(sid, d)  # noqa: E731

    # 1 title
    D.title_slide(D.title, "Programme Skerry – logical, integration and deployment views of Claims Hub",
                  [f"Design Authority submission  |  Version {D.version}  |  {D.date_long()}",
                   f"Author: {D.author}, {D.author_title} (IBM Consulting)", "Status: Approved"])

    # 2 document control
    hist = CM.history_rows(D, [("1.0", "Baseline for the Claims Hub MVP"), ("1.1", ""), ("1.2", ""), ("2.0", "")],
                           spacing=(20, 45))
    CM.doc_control(D, hist, [("P018", "Approved (Design Authority)"), ("P017", "Approved"), ("P006", "Approved")],
                   status="Approved", reviewers=[W.name_of(x, d) for x in ("P050", "P053", "P031", "P041")],
                   distribution="Design Authority members, Claims Hub squads, CLARA platform team",
                   purpose="Target architecture for Claims Hub and its integration with CLARA during migration.")

    # 3 agenda
    CM.agenda(D, ["Architecture principles", "Context view", "Runtime namespaces", "Fraud referral event flow",
                  "Reserve movement bridge", "Migration roadmap", "Service and topic catalogue",
                  "Interfaces and deployment", "Decisions, risks and contacts"], kicker="Target architecture")

    # 4 principles (ADRs accepted by the issue date)
    s = D.content("Architecture principles", "Principles")
    adr_ids = ["ADR-001", "ADR-002", "ADR-003", "ADR-004", "ADR-006", "ADR-010", "ADR-011", "ADR-013"]
    items = []
    for a in adr_ids:
        adr = W.adrs[a]
        items.append({"runs": [(f"{a}  ", {"bold": True, "color": "teal"}), (adr["title"], {})]})
    s.bullets(0.6, 1.5, 7.6, 5.2, items, size=14)
    s.box(8.6, 1.6, 4.2, 3.6, [{"text": P.pick(rng, P.TAKEAWAY_HEAD), "bold": True, "size": 14},
                               {"text": "Migrate in waves behind a strangler fig; keep MQ for the mainframe until CLARA is gone; events on Kafka for everything new.", "size": 12}],
          style="tile", align="l", anchor="t", margins=0.18)
    s.notes(P.notes(rng, "the principles behind the target architecture",
                    ["All eight principles are recorded as accepted ADRs in the Design Authority register."]))
    D.fact(s, "text", "Retain MQ for mainframe integration until CLARA decommissioning",
           "ADR-004: retain MQ for mainframe integration until CLARA decommissioning.", world_ref="ADR:ADR-004")

    # 5 context view (raster)
    s = D.content("Context view – Claims Hub and its neighbours", "Context")
    cv = R.Canvas(2400, 1300)
    cv.title("Claims Hub context (target)", "Arrows show the direction of the main data flow; labels give the interface")
    hub = cv.box(900, 470, 600, 330, "Claims Hub", fill="teal_l", outline="teal", size=40, bold=True,
                 sub="13 Spring services on OpenShift", sub_size=24)
    nodes = {
        "portal": cv.box(80, 200, 420, 120, sysn("SYS04"), fill="white", size=28),
        "palm": cv.box(80, 420, 420, 120, sysn("SYS08"), fill="white", size=28),
        "eig": cv.box(80, 640, 420, 120, sysn("SYS13"), fill="white", size=28),
        "cis": cv.box(80, 860, 420, 120, sysn("SYS16"), fill="white", size=28),
        "snt": cv.box(1900, 170, 420, 110, sysn("SYS03"), fill="white", size=28),
        "notify": cv.box(1900, 340, 420, 110, sysn("SYS25"), fill="white", size=28),
        "ev": cv.box(1900, 510, 420, 110, sysn("SYS05"), fill="white", size=28),
        "scm": cv.box(1900, 680, 420, 110, sysn("SYS22"), fill="white", size=28),
        "gl": cv.box(1900, 850, 420, 110, sysn("SYS06"), fill="white", size=28),
        "clara": cv.box(700, 1080, 380, 120, sysn("SYS01"), fill="grey_l", size=30, bold=True),
        "mq": cv.box(1180, 1080, 380, 120, sysn("SYS14"), fill="grey_l", size=28),
    }
    E = R.Canvas.edge
    cv.arrow([E(nodes["portal"], "r"), (900, 560)], "CLX-IF-035 REST (planned)", dash=True, label_at=0.45)
    cv.arrow([E(nodes["palm"], "r"), (900, 620)], "CLX-IF-054 REST", label_at=0.45)
    cv.arrow([E(nodes["eig"], "r"), (900, 700)], "CLX-IF-057 Kafka", label_at=0.45)
    cv.arrow([E(nodes["cis"], "r"), (900, 770)], "CLX-IF-040 OIDC", label_at=0.42)
    cv.arrow([(1500, 500), E(nodes["snt"], "l")], "CLX-IF-036 REST", label_at=0.55)
    cv.arrow([(1500, 560), E(nodes["notify"], "l")], "CLX-IF-037 REST", label_at=0.55)
    cv.arrow([(1500, 620), E(nodes["ev"], "l")], "CLX-IF-039 REST", label_at=0.55)
    cv.arrow([(1500, 700), E(nodes["scm"], "l")], "CLX-IF-041 REST", label_at=0.55)
    cv.arrow([(1500, 770), E(nodes["gl"], "l")], "CLX-IF-050 REST (planned)", dash=True, label_at=0.55)
    cv.arrow([E(nodes["clara"], "r"), E(nodes["mq"], "l")], None)
    cv.arrow([E(nodes["mq"], "t"), (1370, 800)], "CLX-IF-049 bridge", label_at=0.5, label_dx=110)
    png = cv.png()
    alt = ("Context diagram: MyCorvane Claims, PALM, Evidence Intake Gateway and Corvane Identity Service feed Claims Hub "
           "(CLX-IF-035, 054, 057, 040); Claims Hub calls Sentinel (CLX-IF-036), Notify (CLX-IF-037), Evidence Vault "
           "(CLX-IF-039), SIU Case Manager (CLX-IF-041) and Group Ledger (CLX-IF-050, planned); CLARA reaches Claims Hub "
           "through the MQ Backbone and the CLX-IF-049 bridge.")
    s.picture_fit(png, 0.5, 1.35, 12.3, 5.55, alt=alt, title="Claims Hub context view")
    s.notes(P.notes(rng, "the systems Claims Hub talks to",
                    ["Dashed arrows are interfaces that are designed but not yet live at the issue date."]))
    D.fact(s, "image", "CLX-IF-036 REST",
           "Context diagram: Claims Hub calls Sentinel over REST via CLX-IF-036 (arrow label in the image).",
           kind="image_text", world_ref="INTERFACE:CLX-IF-036")
    D.fact(s, "alt_text", "Claims Hub calls Sentinel (CLX-IF-036)",
           "Alt text of the context diagram: Claims Hub calls Sentinel (CLX-IF-036).",
           kind="alt_text", world_ref="INTERFACE:CLX-IF-036")
    D.fact(s, "image", "CLX-IF-041 REST",
           "Context diagram: Claims Hub sends fraud referrals to SIU Case Manager via CLX-IF-041 (REST).",
           kind="image_text", world_ref="INTERFACE:CLX-IF-041")

    # 6 runtime namespaces (nested groups)
    s = D.content("Runtime view – OpenShift namespaces", "Logical view")
    ns_layout = [
        ("chub-intake", ["fnol-intake-svc", "triage-svc"]),
        ("chub-core", ["claim-core-svc"]),
        ("chub-assess", ["assessment-svc"]),
        ("chub-reserve", ["reserve-engine"]),
        ("chub-fraud", ["fraud-referral-svc", "Sentinel adapter"]),
        ("chub-settle", ["settlement-svc", "payment-orchestrator"]),
        ("chub-recovery", ["recovery-svc"]),
        ("chub-docs", ["document-svc"]),
        ("chub-notify", ["notification-svc"]),
        ("chub-finance", ["gl-posting-svc", "reporting-feed-svc"]),
    ]
    cluster = s.group("Claims Hub – OpenShift cluster (prod)")
    cluster.rect(0.5, 1.4, 12.3, 5.45, fill="grey_l", line="grey_m", name="Cluster boundary")
    cluster.text(0.65, 1.45, 6.0, 0.3, [{"text": "OpenShift cluster – production"}], size=10, bold=True, color="slate")
    for i, (ns, svcs) in enumerate(ns_layout):
        col, row = i % 5, i // 5
        x, y = 0.7 + col * 2.42, 1.85 + row * 2.5
        g = cluster.group(ns)
        g.box(x, y, 2.25, 0.42, ns, style="tile", fill="navy2", color="white", size=11, bold=True)
        for j, svc in enumerate(svcs):
            planned = svc in W.services and W.services[svc]["go_live"] > d
            g.box(x + 0.1, y + 0.55 + j * 0.72, 2.05, 0.6, svc, style="service", size=11,
                  dash=planned, fill="white" if svc in W.services else "amber_l")
    s.text(0.7, 6.55, 11.8, 0.28, [{"text": "Dashed outline = service not yet live at the issue date.  Amber = adapter component."}],
           size=9, color="slate")
    s.notes(P.notes(rng, "how the services are grouped into namespaces",
                    ["Each namespace maps to a squad-owned Terraform module; one PostgreSQL database per service (ADR-003)."]))
    D.place("vs2_group_fraud", s, "group", "chub-fraud fraud-referral-svc Sentinel adapter", shape_name="chub-fraud",
            notes="Nested group 'chub-fraud' inside 'Claims Hub – OpenShift cluster (prod)'; group lines: header, then members.")
    D.fact(s, "group", "chub-reserve reserve-engine",
           "Group 'chub-reserve' contains reserve-engine.", kind="visual_only",
           world_ref="SERVICE:reserve-engine#k8s_namespace", shape_name="chub-reserve")
    D.fact(s, "group", "chub-finance gl-posting-svc reporting-feed-svc",
           "Group 'chub-finance' contains gl-posting-svc and reporting-feed-svc.", kind="visual_only",
           world_ref="SERVICE:gl-posting-svc#k8s_namespace", shape_name="chub-finance")

    # 7 fraud referral event flow (connectors only)
    s = D.content("Fraud referral – event flow", "Integration view")
    tri = s.box(0.7, 1.7, 2.3, 0.75, "triage-svc", style="service", size=13, bold=True)
    frs = s.box(4.6, 3.3, 2.5, 0.8, "fraud-referral-svc", style="service", size=13, bold=True)
    nts = s.box(9.0, 3.3, 2.3, 0.8, "notification-svc", style="service", size=13, bold=True)
    rfs = s.box(4.7, 5.6, 2.3, 0.75, "reporting-feed-svc", style="service", size=13, bold=True)
    snt = s.box(4.7, 1.7, 2.3, 0.75, sysn("SYS03"), style="system", size=13)
    scm = s.box(9.0, 5.6, 2.3, 0.75, sysn("SYS22"), style="system", size=13)
    ntf = s.box(9.0, 1.7, 2.3, 0.75, sysn("SYS25"), style="system", size=13)
    s.connect(tri, snt, label="CLX-IF-036", name="evt-score-call")
    s.connect(tri, frs, a_site="r", b_site="t", label="fraud.score.received.v1", name="evt-score", label_dx=0.35, label_dy=-0.15)
    s.connect(tri, frs, a_site="b", b_site="l", label="triage.completed.v1", name="evt-triage", label_dx=-0.3, label_dy=0.2)
    s.connect(frs, nts, label="fraud.referral.notice-due.v1", name="evt-notice")
    s.connect(frs, rfs, label="fraud.referral.created.v1", name="evt-created")
    s.connect(frs, scm, a_site="r", b_site="l", label="CLX-IF-041", name="evt-siu", label_dy=0.1)
    s.connect(nts, ntf, label="CLX-IF-037", name="evt-notify")
    s.notes(P.notes(rng, "the events around a fraud referral",
                    ["The customer-notice deadline is calculated by fraud-referral-svc as referral date plus 10 business days.",
                     "fraud-referral-svc is planned to go live on 1 April 2026, when NISA Circular 2026/04 takes effect."]))
    D.place("vs2_arrow_notice", s, "connector", "fraud-referral-svc -> notification-svc [label: fraud.referral.notice-due.v1]",
            notes="Label in text box 'label:evt-notice'.")
    D.fact(s, "connector", "fraud-referral-svc -> reporting-feed-svc [label: fraud.referral.created.v1]",
           "Arrow fraud-referral-svc → reporting-feed-svc labelled with topic fraud.referral.created.v1.",
           kind="arrow_only", world_ref="TOPIC:fraud.referral.created.v1#consumers")
    D.fact(s, "connector", "triage-svc -> fraud-referral-svc [label: fraud.score.received.v1]",
           "Arrow triage-svc → fraud-referral-svc labelled with topic fraud.score.received.v1.",
           kind="arrow_only", world_ref="TOPIC:fraud.score.received.v1#producer")
    D.fact(s, "notes", "referral date plus 10 business days",
           "Speaker notes: fraud-referral-svc calculates the customer-notice deadline as referral date plus 10 business days.",
           kind="speaker_notes", world_ref="SERVICE:fraud-referral-svc#apis")

    # 8 reserve movement bridge (connectors only)
    s = D.content("Reserve movements – from CLARA to reserve-engine", "Integration view")
    cla = s.box(0.6, 3.25, 2.0, 0.85, sysn("SYS01"), style="system", size=14, bold=True)
    mq = s.box(3.6, 3.25, 2.3, 0.85, sysn("SYS14"), style="system", size=14)
    esp = s.box(7.1, 1.75, 2.5, 0.85, sysn("SYS15"), style="system", size=14)
    rse = s.box(10.6, 1.75, 2.1, 0.85, W.service_name("reserve-engine", d), style="service", size=14, bold=True)
    gl = s.box(7.1, 3.25, 2.5, 0.85, sysn("SYS06"), style="system", size=14)
    cdw = s.box(7.1, 4.6, 2.5, 0.85, sysn("SYS11"), style="system", size=14)
    rec = s.box(7.1, 5.85, 2.5, 0.85, sysn("SYS07"), style="system", size=14)
    s.connect(cla, mq, label="CLX-IF-042", name="rsv-042")
    s.connect(mq, esp, a_site="t", b_site="l", label="CLX-IF-049", name="rsv-049", label_dx=-0.2)
    s.connect(esp, rse, label="claims.reserve.movement.v1", name="rsv-topic", label_dy=-0.3)
    s.connect(mq, gl, label="CLX-IF-043", name="rsv-043")
    s.connect(mq, cdw, a_site="b", b_site="l", label="CLX-IF-044", name="rsv-044", label_dx=-0.15)
    s.connect(mq, rec, a_site="b", b_site="l", label="CLX-IF-047", name="rsv-047", label_dx=0.1, label_dy=0.1)
    D.need("TIMELINE:programme", "parallel_run.from")
    s.notes(P.notes(rng, "how reserve movements reach the target platform",
                    ["The bridge went live on 12 December 2025 under CHUB-188 and is the feed for the reserve parallel run that starts on 2 March 2026.",
                     "ADR-012 and ADR-017 replaced the earlier change-data-capture design (ADR-005)."]))
    D.place("vs2_arrow_049", s, "connector", "MQ Backbone -> Event Streaming Platform [label: CLX-IF-049]",
            notes="First of the two connectors (MQ Backbone → Event Streaming Platform).")
    D.place("vs2_arrow_049", s, "connector", "Event Streaming Platform -> reserve-engine [label: claims.reserve.movement.v1]",
            statement="Arrow Event Streaming Platform → reserve-engine labelled with topic claims.reserve.movement.v1 (second connector of the CLX-IF-049 path).",
            notes="Second of the two connectors (Event Streaming Platform → reserve-engine).")
    D.fact(s, "connector", "MQ Backbone -> Group Ledger [label: CLX-IF-043]",
           "Arrow MQ Backbone → Group Ledger labelled CLX-IF-043.", kind="arrow_only",
           world_ref="INTERFACE:CLX-IF-043")
    D.fact(s, "notes", "went live on 12 December 2025 under CHUB-188",
           "Speaker notes: the CLX-IF-049 bridge went live on 2025-12-12 (CHUB-188) and feeds the reserve parallel run from 2026-03-02.",
           kind="speaker_notes", world_ref="EVENT:EV-023")

    # 9 migration roadmap (dates for the last two milestones only in the notes)
    s = D.content("Migration roadmap", "Roadmap")
    road = s.group("Roadmap chevrons")
    steps = [("MVP live", "3 Nov 2025", "FNOL and triage, digital channels"),
             ("Fraud referral", "1 Apr 2026", "fraud-referral-svc live"),
             ("Wave 0", "1 Jun 2026", "Denmark"),
             ("Wave 1", "14 Sep 2026", "UK motor"),
             ("Wave 2", "", "UK home, commercial, liability; Norway; Sweden"),
             ("Decommission", "", "CLARA switched off")]
    for i, (h, dt, sub) in enumerate(steps):
        x = 0.5 + i * 2.07
        road.box(x, 2.0, 2.15, 1.0, h, style="chevron" if i else "pentagon", size=12 if len(h) > 9 else 13,
                 bold=True, fill="teal" if dt else "slate")
        road.text(x + 0.15, 3.15, 1.85, 0.4, [{"text": dt or "date to be confirmed", "bold": bool(dt)}],
                  size=12 if dt else 10, color="navy" if dt else "grey")
        road.text(x + 0.15, 3.55, 1.85, 1.0, [{"text": sub}], size=10, color="slate")
    s.bullets(0.6, 4.75, 12.0, 1.9, [
        "Each wave moves whole products from CLARA to Claims Hub; CLARA stays the system of record for products not yet migrated.",
        "Reserve parallel run (CLARA versus reserve-engine) runs ahead of the first reserve-bearing wave.",
        "Interfaces to CLARA are switched per wave; the MQ Backbone stays until decommissioning (ADR-004).",
    ], size=12)
    D.need("TIMELINE:programme", "wave2")
    D.need("TIMELINE:programme", "clara_decommission_target")
    s.notes(P.notes(rng, "the migration roadmap",
                    ["Dates for the last two milestones: Wave 2 cut-over is planned for 2027-02-15 and CLARA decommissioning for 2027-09-30.",
                     "The Wave 2 date is a provisional planning date; both dates are kept off the slide until the "
                     "Steering Committee confirms them."]))
    D.place("vs2_notes_wave2", s, "notes", "Wave 2 cut-over is planned for 2027-02-15 and CLARA decommissioning for 2027-09-30")

    # 10 section
    D.section("02", "Data and integration", "Service catalogue, events and interfaces")

    # 11 service catalogue
    s = D.content("Service catalogue", "Data and integration")
    rows = []
    for svc in W.services.values():
        own = W.service_owner(svc["name"], d)
        rows.append((W.service_name(svc["name"], d), svc["k8s_namespace"], W.team_name(own["team"], d),
                     D.date_long(svc["go_live"]), "Live" if svc["go_live"] <= d else "Planned"))
    s.table(0.5, 1.4, 12.3, ["Service", "Namespace", "Owning squad", "Go-live", "Status at issue"], rows,
            col_w=[2.2, 1.7, 3.6, 1.8, 1.6], row_h=0.38, size=10, first_col_bold=True)
    s.notes(P.notes(rng, "the thirteen Claims Hub services",
                    ["reserve-engine was renamed from reserve-svc on 10 February 2026 (ADR-019, CHUB-233)."]))
    D.fact(s, "table", "Hub Squad – Fraud & Settlement",
           "Service catalogue (2026-03-16): recovery-svc is owned by Hub Squad – Fraud & Settlement.",
           world_ref="SERVICE:recovery-svc#owner_history:T29")
    D.fact(s, "notes", "renamed from reserve-svc on 10 February 2026",
           "Speaker notes: reserve-engine was renamed from reserve-svc on 2026-02-10 (ADR-019, CHUB-233).",
           kind="speaker_notes", world_ref="SERVICE:reserve-engine#renames")

    # 12 topics (image table; fraud and reserve-bridge topics deliberately not tabulated)
    s = D.content("Event catalogue – claim lifecycle and finance topics", "Data and integration")
    skip = {"fraud.score.received.v1", "fraud.referral.created.v1", "fraud.referral.notice-due.v1",
            "claims.reserve.movement.v1", "notification.fraud-notice.sent.v1"}
    trows = []
    for t in W.topics.values():
        if t["name"] in skip or (t.get("introduced") or "0000") > d:
            continue
        D.need(f"TOPIC:{t['name']}", "consumers")
        trows.append((t["name"], t["producer"], ", ".join(t["consumers"])))
    png = R.table_image(["Topic", "Producer", "Consumers"], trows, [3.0, 2.6, 4.4], size=24,
                        title="Kafka topics on esp-prd (extract)")
    s.picture_fit(png, 0.6, 1.35, 12.1, 5.55,
                  alt="Table of Kafka topics on the esp-prd cluster with producer and consumer services.")
    s.notes(P.notes(rng, "the main topics on the event backbone",
                    ["Fraud and reserve-bridge topics are shown on the integration views rather than in this table."]))
    D.fact(s, "image", "reserve.changed.v2",
           "Topic table: reserve.changed.v2 is produced by reserve-engine and consumed by gl-posting-svc and reporting-feed-svc.",
           kind="image_table", world_ref="TOPIC:reserve.changed.v2")

    # 13 interfaces table
    s = D.content("Claims Hub interfaces", "Data and integration")
    ids = ["CLX-IF-034", "CLX-IF-035", "CLX-IF-036", "CLX-IF-037", "CLX-IF-038", "CLX-IF-039", "CLX-IF-040",
           "CLX-IF-041", "CLX-IF-045", "CLX-IF-050", "CLX-IF-054", "CLX-IF-056", "CLX-IF-057", "CLX-IF-060"]
    rows = []
    for iid in ids:
        i = W.interfaces[iid]
        D.need(f"INTERFACE:{iid}", "schedule")
        rows.append((iid, i["name"], f"{sysn(i['source_system'])} → {sysn(i['target_system'])}", i["protocol"],
                     W.interface_schedule(iid, d), "Live" if live(W, iid, d) else "Planned"))
    s.table(0.5, 1.4, 12.3, ["ID", "Name", "Source → target", "Protocol", "Schedule", "Status"], rows,
            col_w=[1.1, 3.4, 3.8, 0.9, 1.4, 0.9], row_h=0.33, size=9, first_col_bold=True)
    s.notes(P.notes(rng, "the interfaces that belong to Claims Hub", n_filler=1))
    D.fact(s, "table", "Claims Hub journals to GL",
           "CLX-IF-050 'Claims Hub journals to GL' (Claims Hub → Group Ledger, REST, hourly) is planned at 2026-03-16.",
           world_ref="INTERFACE:CLX-IF-050")

    # 14 deployment view (raster)
    s = D.content("Deployment view", "Physical view")
    cv = R.Canvas(2400, 1300)
    cv.title("Deployment – production", "Runtime platforms and the protocols between them")
    ocp = cv.box(80, 180, 1250, 760, "", fill="grey_l", outline="slate")
    cv.text(110, 200, "OpenShift (prod) – 13 services in 10 namespaces", size=30, bold=True, color="navy")
    for i, ns in enumerate([n for n, _ in ns_layout]):
        cv.box(120 + (i % 5) * 238, 290 + (i // 5) * 150, 222, 110, ns, fill="white", outline="teal", size=24)
    pg = cv.cyl(1600, 200, 640, 220, "PostgreSQL 16 – one database per service", size=26)
    esp_b = cv.box(1600, 520, 640, 170, "Event Streaming Platform", fill="teal_l", outline="teal", size=30,
                   bold=True, sub="Kafka on OpenShift (Strimzi), 6 brokers", sub_size=24)
    mq_b = cv.box(1600, 790, 640, 170, "MQ Backbone", fill="white", outline="slate", size=30, bold=True,
                  sub="HUBQM01 (distributed) ↔ CLRQM01 (z/OS)", sub_size=24)
    cis = cv.box(200, 1060, 560, 150, "Corvane Identity Service", fill="white", size=28, sub="OIDC / OAuth2", sub_size=24)
    zos = cv.box(1600, 1060, 640, 150, "z/OS – CLARA (CICS, DB2)", fill="grey_l", size=28)
    cv.arrow([(1330, 310), E(pg, "l")], "JDBC", label_at=0.5)
    cv.arrow([(1330, 600), E(esp_b, "l")], "Kafka (TLS)", label_at=0.5, both=True)
    cv.arrow([(1330, 870), E(mq_b, "l")], "MQ client", label_at=0.5)
    cv.arrow([E(cis, "t"), (480, 940)], "OIDC tokens", label_at=0.5, label_dx=120)
    cv.arrow([E(zos, "t"), E(mq_b, "b")], "CLRQM01", label_at=0.5, label_dx=110)
    png = cv.png()
    s.picture_fit(png, 0.5, 1.35, 12.3, 5.55,
                  alt="Deployment view: Claims Hub services run on OpenShift and use PostgreSQL 16 (one database per service), "
                      "the Event Streaming Platform (Kafka on OpenShift with the Strimzi operator, 6 brokers) and the MQ Backbone "
                      "(HUBQM01 and CLRQM01) to reach CLARA on z/OS; users authenticate through the Corvane Identity Service (OIDC).",
                  title="Deployment view")
    s.notes(P.notes(rng, "where the services physically run", n_filler=1))
    D.fact(s, "image", "6 brokers",
           "Deployment view image: Event Streaming Platform is Kafka on OpenShift (Strimzi) with 6 brokers.",
           kind="image_text", world_ref="SYSTEM:SYS15#tech")
    D.fact(s, "alt_text", "HUBQM01 and CLRQM01",
           "Deployment view alt text: the MQ Backbone comprises queue managers HUBQM01 and CLRQM01.",
           kind="alt_text", world_ref="SYSTEM:SYS14#tech")

    # 15 decisions
    s = D.content("Architecture decision register (extract)", "Decisions")
    arows = []
    for a in sorted(W.adrs.values(), key=lambda x: x["id"]):
        if a["date"] > d:
            continue
        arows.append((a["id"], a["title"], D.date_long(a["date"]), a["status"]))
    arows = arows[-14:]
    s.table(0.5, 1.4, 12.3, ["ADR", "Title", "Date", "Status"], arows, col_w=[0.9, 7.2, 1.8, 1.3],
            row_h=0.34, size=10, first_col_bold=True)
    s.notes(P.notes(rng, "the most recent architecture decisions", n_filler=1))
    D.fact(s, "table", "Fraud referral thresholds as effective-dated configuration",
           "ADR-020 (2026-02-16): fraud referral thresholds as effective-dated configuration.", world_ref="ADR:ADR-020")

    # 16 risks
    s = D.content("Risks and open points", "Decisions")
    s.bullets(0.6, 1.5, 12.0, 5.2, [
        "Year-end currency revaluation stays in CLARA (CLRGL090) until the reserve-engine revaluation run takes over from Wave 2 (ADR-028).",
        "CLARA and Claims Hub both write reserve data during migration; reconciliation relies on the CLX-IF-049 feed.",
        "Regulatory extracts move to reporting-feed-svc only after the CLARA extracts have been retired.",
        "Squad capacity is shared between Wave 1 build and MVP support.",
        "Any change to the reserve movement layout must be impact-assessed across every downstream consumer.",
    ], size=14)
    s.notes(P.notes(rng, "the main architectural risks"))
    D.fact(s, "text", "until the reserve-engine revaluation run takes over from Wave 2 (ADR-028)",
           "CLRGL090 revaluation stays in CLARA until the reserve-engine revaluation run takes over from Wave 2 (ADR-028).",
           world_ref="ADR:ADR-028")

    # 17 contacts
    CM.contacts(D, [("P049", "Author – target architecture"), ("P050", "Integration design"),
                    ("P053", "Java technical lead"), ("P018", "Design Authority chair"),
                    ("P031", "MQ Backbone and Event Streaming Platform owner"), ("P017", "Claims Hub product")])
    return D

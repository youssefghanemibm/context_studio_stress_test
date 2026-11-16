"""VS010 Claims Hub Service Map (2026-10-15, Elin Fosse, approved).

Slide 3: nested group 'chub-recovery' shows recovery-svc with the owner label 'Squad Fraud &
Settlement' (true until 2026-10-31), and a text box rotated 270° reads 'reserve-engine (formerly
reserve-svc)'."""
from __future__ import annotations

from collections import Counter

from . import common as CM
from . import phrases as P
from . import raster as R
from .core import Deck


def squad_label(W, team_id, d):
    name = W.team_name(team_id, d)
    return "Squad " + name.split("–", 1)[1].strip() if "–" in name else name


def build(W, out_dir):
    D = Deck(W, "VS010", version="3.2", doc_ref="SKR-ARC-007", out_dir=out_dir)
    d = D.date
    rng = D.rng
    svcs = list(W.services.values())

    # 1 title
    D.title_slide(D.title, "Services, namespaces, owners and event flows in production",
                  [f"Programme Skerry architecture  |  Version {D.version}  |  {D.date_long()}",
                   f"Author: {D.author}, {D.author_title} (IBM Consulting)", "Status: Approved"])

    # 2 agenda
    CM.agenda(D, ["Service map", "Request flow", "Service catalogue", "Event topic map", "API catalogue",
                  "Data ownership", "Squads", "Legacy programs replaced", "Topics, deployment and document control"],
              kicker="Service map")

    # 3 service map (nested groups + rotated label)
    s = D.content("Claims Hub service map", "Service map")
    order = ["chub-reserve", "chub-finance", "chub-settle", "chub-recovery", "chub-fraud",
             "chub-intake", "chub-core", "chub-assess", "chub-docs", "chub-notify"]
    by_ns = {}
    for sv in svcs:
        by_ns.setdefault(sv["k8s_namespace"], []).append(sv)
    cluster = s.group("Claims Hub production cluster")
    cluster.rect(0.85, 1.35, 12.0, 5.55, fill="grey_l", line="grey_m", name="Cluster area")
    for i, ns in enumerate(order):
        c, r = i % 5, i // 5
        x, y = 1.0 + c * 2.37, 1.5 + r * 2.72
        g = cluster.group(ns)
        g.box(x, y, 2.25, 0.4, ns, style="tile", fill="navy2", color="white", size=11, bold=True)
        owners = []
        for j, sv in enumerate(by_ns[ns]):
            g.box(x + 0.08, y + 0.5 + j * 0.62, 2.09, 0.52, W.service_name(sv["name"], d), style="service", size=11)
            own = W.service_owner(sv["name"], d)["team"]
            if own not in owners:
                owners.append(own)
        g.text(x + 0.05, y + 2.0, 2.15, 0.35, [{"text": " / ".join(squad_label(W, o, d) for o in owners)}],
               size=9, italic=True, color="teal")
    # rotated label beside chub-reserve (first column, row 1)
    s.text(-0.75, 2.55, 2.4, 0.36, [{"text": "reserve-engine (formerly reserve-svc)", "align": "c"}], size=10,
           bold=True, color="navy", rotation=270, name="Rename note")
    s.notes(P.notes(rng, "where each service runs and who owns it",
                    ["Owner labels show the owning squad at the map date."]))
    D.place("vs10_recovery_owner", s, "group", "chub-recovery recovery-svc Squad Fraud & Settlement",
            shape_name="chub-recovery", notes="Owner label is a text box inside the nested group; valid at 2026-10-15 (owner changes 2026-11-01).")
    D.place("vs10_rotated", s, "text", "reserve-engine (formerly reserve-svc)",
            notes="Text box 'Rename note' rotated 270 degrees beside the chub-reserve group.")
    D.fact(s, "group", "chub-docs document-svc Squad Intake & Triage",
           "Service map (2026-10-15): document-svc in chub-docs is owned by Squad Intake & Triage.", kind="visual_only",
           world_ref="SERVICE:document-svc#owner_history:T27", shape_name="chub-docs")
    D.fact(s, "group", "chub-settle settlement-svc payment-orchestrator Squad Fraud & Settlement",
           "chub-settle contains settlement-svc and payment-orchestrator, owned by Squad Fraud & Settlement.",
           kind="visual_only", world_ref="SERVICE:settlement-svc#k8s_namespace", shape_name="chub-settle")

    # 4 request flow (raster)
    s = D.content("Request flow – from first notice to payment", "Request flow")
    cv = R.Canvas(2400, 1250)
    cv.title("A motor claim through Claims Hub", "Synchronous calls in grey, Kafka topics in teal")
    E = R.Canvas.edge
    b = {
        "fnol": cv.box(60, 300, 380, 130, "fnol-intake-svc", fill="white", outline="teal", size=28),
        "tri": cv.box(560, 300, 380, 130, "triage-svc", fill="white", outline="teal", size=28),
        "asm": cv.box(1060, 300, 380, 130, "assessment-svc", fill="white", outline="teal", size=28),
        "stl": cv.box(1560, 300, 380, 130, "settlement-svc", fill="white", outline="teal", size=28),
        "pay": cv.box(1560, 760, 380, 130, "payment-orchestrator", fill="white", outline="teal", size=26),
        "rec": cv.box(2000, 520, 360, 130, "recovery-svc", fill="white", outline="teal", size=28),
        "snt": cv.box(560, 760, 380, 130, "Sentinel", fill="grey_l", size=28),
        "cpg": cv.box(1560, 1060, 380, 120, "Corvane Payments Gateway", fill="grey_l", size=24),
        "rse": cv.box(1060, 760, 380, 130, "reserve-engine", fill="white", outline="teal", size=28),
    }
    cv.arrow([E(b["fnol"], "r"), E(b["tri"], "l")], "fnol.received.v1", color="teal", label_dy=-95)
    cv.arrow([E(b["tri"], "r"), E(b["asm"], "l")], "triage.completed.v1", color="teal", label_dy=-95)
    cv.arrow([E(b["asm"], "r"), E(b["stl"], "l")], "assessment.completed.v1", color="teal", label_dy=-95)
    cv.arrow([E(b["stl"], "b"), E(b["pay"], "t")], "settlement.agreed.v1", color="teal", label_dx=-170)
    cv.arrow([E(b["stl"], "r"), (2180, 365), E(b["rec"], "t")], "settlement.agreed.v1", color="teal", label_at=0.3, label_dy=-36)
    cv.arrow([E(b["tri"], "b"), E(b["snt"], "t")], "REST (CLX-IF-036)", label_dx=-150)
    cv.arrow([E(b["tri"], "b"), (750, 600), (1250, 600), E(b["rse"], "t")], "triage.completed.v1", color="teal", label_at=0.5, label_dy=-30)
    cv.arrow([E(b["pay"], "b"), E(b["cpg"], "t")], "REST (CLX-IF-038)", label_dx=-150)
    png = cv.png()
    s.picture_fit(png, 0.5, 1.35, 12.3, 5.55,
                  alt="Request flow: fnol-intake-svc publishes fnol.received.v1 to triage-svc; triage-svc calls Sentinel (CLX-IF-036) and publishes triage.completed.v1 to assessment-svc and reserve-engine; assessment-svc publishes assessment.completed.v1 to settlement-svc; settlement.agreed.v1 goes to payment-orchestrator and recovery-svc; payment-orchestrator calls Corvane Payments Gateway (CLX-IF-038).",
                  title="Claims Hub request flow")
    s.notes(P.notes(rng, "how a claim moves through the services", n_filler=1))
    D.fact(s, "image", "assessment.completed.v1",
           "Request-flow image: assessment-svc publishes assessment.completed.v1, consumed by settlement-svc.",
           kind="image_text", world_ref="TOPIC:assessment.completed.v1")
    D.fact(s, "alt_text", "settlement.agreed.v1 goes to payment-orchestrator and recovery-svc",
           "Alt text: settlement.agreed.v1 is consumed by payment-orchestrator and recovery-svc.", kind="alt_text",
           world_ref="TOPIC:settlement.agreed.v1#consumers")

    # 5 service catalogue
    s = D.content("Service catalogue", "Catalogue")
    rows = []
    for sv in svcs:
        own = W.service_owner(sv["name"], d)
        D.need(f"SERVICE:{sv['name']}", "replicas")
        rows.append((W.service_name(sv["name"], d), sv["k8s_namespace"], sv["replicas"], D.date_long(sv["go_live"]),
                     W.team_name(own["team"], d), W.name_of(own["person"], d)))
    s.table(0.5, 1.4, 12.3, ["Service", "Namespace", "Replicas", "Go-live", "Owning squad", "Engineering lead"], rows,
            col_w=[2.2, 1.6, 0.9, 1.8, 3.6, 2.2], row_h=0.37, size=9, first_col_bold=True, align=[None, None, "c", None, None, None])
    s.notes(P.notes(rng, "the thirteen services", ["reporting-feed-svc is still in development, with go-live planned for 11 January 2027."]))
    D.fact(s, "table", "Hub Squad – Fraud & Settlement",
           "Service catalogue (2026-10-15): recovery-svc is owned by Hub Squad – Fraud & Settlement, engineering lead Linnea Sjöberg.",
           world_ref="SERVICE:recovery-svc#owner_history:T29")

    # 6 topic map (connectors)
    s = D.content("Event topic map", "Events")
    pos = {"fnol-intake-svc": (0.5, 1.6), "triage-svc": (3.4, 1.6), "assessment-svc": (6.3, 1.6),
           "settlement-svc": (9.2, 1.6), "payment-orchestrator": (9.2, 4.1), "recovery-svc": (11.0, 5.6),
           "reserve-engine": (3.4, 4.1), "gl-posting-svc": (6.3, 5.6), "reporting-feed-svc": (0.5, 5.6)}
    bx = {k: s.box(x, y, 2.05 if k != "recovery-svc" else 1.8, 0.7, W.service_name(k, d), style="service", size=11, bold=True)
          for k, (x, y) in pos.items()}
    links = [("fnol-intake-svc", "triage-svc", "fnol.received.v1"),
             ("triage-svc", "assessment-svc", "triage.completed.v1"),
             ("assessment-svc", "settlement-svc", "assessment.completed.v1"),
             ("settlement-svc", "payment-orchestrator", "settlement.agreed.v1"),
             ("settlement-svc", "recovery-svc", "settlement.agreed.v1"),
             ("triage-svc", "reserve-engine", "triage.completed.v1"),
             ("reserve-engine", "gl-posting-svc", "reserve.changed.v2"),
             ("reserve-engine", "reporting-feed-svc", "reserve.changed.v2"),
             ("recovery-svc", "gl-posting-svc", "recovery.receipt.v1")]
    for k, (a, b2, topic) in enumerate(links):
        sa = sb = None
        if a == "settlement-svc" and b2 == "recovery-svc":
            sa, sb = "r", "t"
        s.connect(bx[a], bx[b2], a_site=sa, b_site=sb, label=topic, name=f"topic-{k + 1}", label_size=9)
    s.notes(P.notes(rng, "which services publish and consume which topics", n_filler=1))
    D.fact(s, "connector", "recovery-svc -> gl-posting-svc [label: recovery.receipt.v1]",
           "Arrow recovery-svc → gl-posting-svc labelled recovery.receipt.v1.", kind="arrow_only",
           world_ref="TOPIC:recovery.receipt.v1")
    D.fact(s, "connector", "reserve-engine -> gl-posting-svc [label: reserve.changed.v2]",
           "Arrow reserve-engine → gl-posting-svc labelled reserve.changed.v2.", kind="arrow_only",
           world_ref="TOPIC:reserve.changed.v2#consumers")
    D.fact(s, "connector", "settlement-svc -> recovery-svc [label: settlement.agreed.v1]",
           "Arrow settlement-svc → recovery-svc labelled settlement.agreed.v1.", kind="arrow_only",
           world_ref="TOPIC:settlement.agreed.v1#consumers")

    # 7 API catalogue (image table)
    s = D.content("API catalogue (extract)", "APIs")
    rows = []
    for name in ["claim-core-svc", "fnol-intake-svc", "reserve-engine", "fraud-referral-svc", "recovery-svc"]:
        for api in W.services[name]["apis"]:
            rows.append((name, api["method"], api["path"], api["summary"]))
    png = R.table_image(["Service", "Method", "Path", "Purpose"], rows, [2.2, 1.0, 3.2, 5.6], size=22,
                        title="REST APIs exposed through the API gateway (extract)")
    s.picture_fit(png, 0.6, 1.35, 12.1, 5.55, alt="Table of REST API operations for claim-core-svc, fnol-intake-svc, reserve-engine, fraud-referral-svc and recovery-svc.")
    s.notes(P.notes(rng, "the main REST operations", n_filler=1))
    D.fact(s, "image", "Trigger a currency revaluation run (replaces CLRGL090)",
           "API table image: reserve-engine POST /revaluation-runs triggers a currency revaluation run (replaces CLRGL090).",
           kind="image_table", world_ref="SERVICE:reserve-engine#apis")
    D.fact(s, "image", "approval above £10,000 by Head of Recoveries & Subrogation",
           "API table image: recovery-svc write-off endpoint – approval above £10,000 by the Head of Recoveries & Subrogation.",
           kind="image_table", world_ref="SERVICE:recovery-svc#apis")

    # 8 data ownership (cards)
    from .orgchart import team_cards
    s = D.content("Data ownership – one database per service", "Data")
    cards = []
    for name in ["claim-core-svc", "reserve-engine", "fraud-referral-svc", "settlement-svc", "recovery-svc", "gl-posting-svc"]:
        sv = W.services[name]
        cards.append((name, [f"Tables: {', '.join(sv['postgres_tables'])}", f"Namespace: {sv['k8s_namespace']}"]))
    gn = team_cards(D, s, cards, prefix="Data card", h=1.6)
    s.notes(P.notes(rng, "which service owns which data", ["Each service has its own PostgreSQL database (ADR-003)."]))
    D.fact(s, "group", "reserve-engine Tables: reserve.reserve, reserve.reserve_movement, reserve.review_schedule",
           "reserve-engine owns the PostgreSQL tables reserve.reserve, reserve.reserve_movement and reserve.review_schedule.",
           kind="visual_only", world_ref="SERVICE:reserve-engine#postgres_tables", shape_name=gn["reserve-engine"])

    # 9 squads
    s = D.content("Squads and ownership", "Squads")
    rows = []
    for tid in ["T27", "T28", "T29"]:
        lead = W.team_lead(tid, d)
        owned = [sv["name"] for sv in svcs if W.service_owner(sv["name"], d)["team"] == tid]
        rows.append((W.team_name(tid, d), W.name_of(lead, d), W.teams[tid].get("github_team", ""), ", ".join(owned)))
    s.table(0.5, 1.45, 12.3, ["Squad", "Engineering lead", "GitHub team", "Services owned at map date"], rows,
            col_w=[3.0, 1.8, 3.2, 4.3], row_h=0.8, size=10, first_col_bold=True)
    s.notes(P.notes(rng, "the squads and what they own", n_filler=1))
    D.fact(s, "table", "@corvane/hub-squad-fraud-settlement",
           "Hub Squad – Fraud & Settlement (lead Linnea Sjöberg, GitHub team @corvane/hub-squad-fraud-settlement) owns fraud-referral-svc, settlement-svc, payment-orchestrator and recovery-svc at 2026-10-15.",
           world_ref="TEAM:T29")

    # 10 programs replaced (chart)
    s = D.content("CLARA programs replaced by each service", "Legacy")
    cnt = {sv["name"]: len(sv.get("replaces_programs") or []) for sv in svcs}
    cats = [k for k, v in sorted(cnt.items(), key=lambda kv: (-kv[1], kv[0])) if v]
    s.chart(0.5, 1.4, 8.6, 5.45, "bar", cats, [("CLARA programs replaced", [cnt[c] for c in cats])],
            title="Number of CLARA programs replaced per service", legend=False, colors=["teal"])
    s.box(9.4, 1.6, 3.4, 2.8, [{"text": "Note", "bold": True, "size": 13},
                               {"text": "reserve-engine replaces CLRGL090's revaluation from Wave 2 (ADR-028).", "size": 12}],
          style="tile", align="l", anchor="t", margins=0.15)
    s.notes(P.notes(rng, "how much of CLARA each service replaces", n_filler=1))
    D.fact(s, "chart", f"CLARA programs replaced: reserve-engine={cnt['reserve-engine']}",
           f"reserve-engine replaces {cnt['reserve-engine']} CLARA programs, the most of any service.", kind="chart_only",
           world_ref="SERVICE:reserve-engine#replaces_programs")

    # 11 topics
    s = D.content("Kafka topics (esp-prd)", "Events")
    rows = []
    for t in W.topics.values():
        if (t.get("introduced") or "0000") > d:
            continue
        rows.append((t["name"], t["producer"], ", ".join(t["consumers"])))
    s.table(0.5, 1.4, 12.3, ["Topic", "Producer", "Consumers"], rows, col_w=[3.4, 3.2, 5.7], row_h=0.27, size=8)
    s.notes(P.notes(rng, "the topic catalogue", n_filler=1))
    D.fact(s, "table", "MQ-to-Kafka bridge (CLX-IF-049)",
           "Topic claims.reserve.movement.v1 is produced by the MQ-to-Kafka bridge (CLX-IF-049) and consumed by reserve-engine.",
           world_ref="TOPIC:claims.reserve.movement.v1#producer")

    # 12 deployment
    s = D.content("Deployment and infrastructure", "Deployment")
    rows = [(sv["name"], sv["terraform_module"], sv["image"]) for sv in svcs]
    s.table(0.5, 1.4, 12.3, ["Service", "Terraform module", "Container image"], rows, col_w=[2.2, 4.7, 5.4], row_h=0.36, size=9)
    s.notes(P.notes(rng, "how the services are deployed",
                    ["The reserve-engine module path changed from infra/terraform/modules/reserve-svc with the February 2026 rename."]))
    D.fact(s, "notes", "changed from infra/terraform/modules/reserve-svc",
           "Speaker notes: the reserve-engine Terraform module moved from infra/terraform/modules/reserve-svc with the 2026-02 rename.",
           kind="speaker_notes", world_ref="SERVICE:reserve-engine#path_history")

    # 13 document control
    hist = CM.history_rows(D, [("3.0", "Wave 1 services added"), ("3.1", ""), ("3.2", "")], spacing=(12, 30))
    CM.doc_control(D, hist, [("P018", "Approved (Design Authority)"), ("P032", "Approved")], status="Approved",
                   reviewers=[W.name_of(x, d) for x in ("P040", "P041", "P042", "P053")],
                   distribution="Claims Hub squads, Design Authority, Technology Delivery Office",
                   purpose="Current map of the Claims Hub services, owners and events.")
    return D

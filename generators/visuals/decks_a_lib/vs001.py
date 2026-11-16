"""VS001 Claims Lifecycle – Swimlane View (2026-10-02, Aisha Siddiqui, approved)."""
from __future__ import annotations

from . import common as CM
from . import phrases as P
from . import raster as R
from .core import Deck
from .lanes import swimlane


def build(W, out_dir):
    D = Deck(W, "VS001", version="3.0", doc_ref="SKR-PRC-014", out_dir=out_dir)
    d = D.date
    rng = D.rng

    # 1 ---------------------------------------------------------------- title
    D.title_slide(D.title, "End-to-end view of the claims process, from first notice of loss to recovery",
                  [f"Claims Hub Product  |  Version {D.version}  |  {D.date_long()}",
                   f"Owner: {D.author}, {D.author_title}", "Status: Approved"])

    # 2 ---------------------------------------------------------------- agenda
    CM.agenda(D, ["Triage and routing decision flow", "FNOL and triage swimlane",
                  "Recovery & Subrogation swimlane", "Fraud referral swimlane", "Reserving swimlane",
                  "Settlement swimlane", "Stage owners and service levels", "Systems by stage",
                  "Glossary and document control"], kicker="Claims lifecycle")

    # 3 ---------------------------------------------------------------- triage decision flow
    s = D.content("Triage and routing – decision flow", "Stage 2 · Triage")
    fnol = s.box(0.6, 1.55, 2.2, 0.7, "FNOL received", style="terminal", size=12, bold=True)
    pre = s.box(0.6, 2.6, 2.2, 0.7, "Sentinel pre-screen", style="process", size=12)
    tier = s.box(0.6, 3.65, 2.2, 0.7, "Tier classification", style="process", size=12)
    route = s.box(4.0, 3.35, 2.1, 1.3, "Route claim", style="decision", size=12, bold=True)
    t_ref = s.box(8.6, 1.5, 2.6, 0.75, "Referral decision", style="alert", size=12)
    t_fast = s.box(8.6, 3.0, 2.6, 0.75, "Fast-track settlement", style="outcome", size=12)
    t_maj = s.box(8.6, 4.6, 2.6, 0.75, "Major loss alert", style="process", size=12)
    t_asm = s.box(8.6, 6.0, 2.6, 0.75, "Appoint assessor", style="process", size=12)
    s.connect(fnol, pre)
    s.connect(pre, tier)
    s.connect(tier, route, a_site="r", b_site="l")
    s.connect(route, t_ref, a_site="t", b_site="l", label="Score ≥ referral threshold", name="route-referral")
    fast_label = "Tier-1 & score < 30 & no injury"
    s.connect(route, t_fast, a_site="r", b_site="l", label=fast_label, name="route-fasttrack", label_dy=0.22)
    s.connect(route, t_maj, a_site="b", b_site="l", label="Tier-3", name="route-major")
    s.connect(route, t_asm, a_site="b", b_site="l", label="Otherwise", name="route-assess", label_dx=-0.4)
    nxt1 = s.box(11.55, 1.5, 1.3, 0.75, "Stage 5 · Fraud Referral", style="tile", size=9, color="slate")
    nxt2 = s.box(11.55, 3.0, 1.3, 0.75, "Stage 6 · Settlement", style="tile", size=9, color="slate")
    nxt3 = s.box(11.55, 6.0, 1.3, 0.75, "Stage 3 · Assessment", style="tile", size=9, color="slate")
    s.connect(t_ref, nxt1, dash=True, color="grey")
    s.connect(t_fast, nxt2, dash=True, color="grey")
    s.connect(t_asm, nxt3, dash=True, color="grey")
    s.connect(t_maj, t_asm, a_site="b", b_site="t", dash=True, color="grey")
    s.text(0.6, 5.2, 2.9, 1.5, [{"text": "Legend", "bold": True, "size": 10},
                                {"text": "Rounded box – activity", "size": 9},
                                {"text": "Diamond – routing decision", "size": 9},
                                {"text": "Dashed arrow – continues in a later stage", "size": 9}],
           size=9, color="slate", fill="grey_l")
    D.need("RULE:BR-TRI-006@v3", "parameters.cap_gbp")
    cap_note = ("Since 1 July 2026 the fast-track payment cap is £2,000 (NOK 26,000 / SEK 27,000 / DKK 17,000) "
                "under BR-TRI-006 v3.")
    s.notes(P.notes(rng, "how triage routes a new claim", [cap_note]))
    D.place("vs1_arrow_fast", s, "connector", f"Route claim -> Fast-track settlement [label: {fast_label}]",
            notes="Branch label sits in a text box named 'label:route-fasttrack'; no slide text states the condition.")
    D.fact(s, "connector", "Route claim -> Major loss alert [label: Tier-3]",
           "In the triage flow, Tier-3 claims are routed from 'Route claim' to 'Major loss alert'.",
           kind="arrow_only", world_ref="PROCESS:PS-TRI-03#decision")
    D.fact(s, "connector", "Route claim -> Referral decision [label: Score ≥ referral threshold]",
           "Claims whose Sentinel score reaches the referral threshold are routed to the referral decision.",
           kind="arrow_only", world_ref="PROCESS:PS-TRI-03#decision")
    D.fact(s, "notes", "fast-track payment cap is £2,000",
           "Speaker notes: since 2026-07-01 the fast-track payment cap is £2,000 (NOK 26,000 / SEK 27,000 / DKK 17,000), BR-TRI-006 v3.",
           kind="speaker_notes", world_ref="RULE:BR-TRI-006@v3#parameters.cap_gbp")

    # 4 ---------------------------------------------------------------- FNOL & triage swimlane
    s = D.content("FNOL and triage – who does what", "Stages 1–2 · FNOL and Triage")
    names = [W.team_name("T10", d), W.team_name("T02", d), W.team_name("T27", d)]
    L = swimlane(s, names, heights=[1.55, 1.55, 1.55], header_w=1.75)
    xs = [2.4 + i * 1.32 for i in range(8)]
    st = {}
    st["rcv"] = L[0].step(xs[0], "Receive notification", w=1.18, size=9)
    st["val"] = L[0].step(xs[1], "Validate policy and cover", w=1.18, size=9)
    st["new"] = L[2].step(xs[2], "Create claim and default reserve", w=1.18, size=9)
    st["dup"] = L[1].step(xs[3], "Duplicate and late-notification checks", w=1.18, size=9)
    st["ack"] = L[0].step(xs[4], "Acknowledge customer", w=1.18, size=9)
    st["snt"] = L[2].step(xs[5], "Sentinel pre-screen", w=1.18, size=9)
    st["tier"] = L[1].step(xs[6], "Tier classification", w=1.18, size=9)
    st["route"] = L[1].step(xs[7], "Route claim", w=1.18, size=9, style="decision")
    order = ["rcv", "val", "new", "dup", "ack", "snt", "tier", "route"]
    for a, b in zip(order, order[1:]):
        s.connect(st[a], st[b])
    s.notes(P.notes(rng, "the first two stages of the lifecycle",
                    ["Every new claim is scored by Sentinel within 15 minutes of FNOL (BR-TRI-007).",
                     "The customer acknowledgement target is 1 business day for digital claims and 2 business days for other channels (BR-FNOL-001 v3)."]))
    D.fact(s, "text", "Sentinel pre-screen",
           f"On the FNOL and triage swimlane, 'Sentinel pre-screen' sits in the '{names[2]}' lane (RACI R = T27).",
           kind="lane_only", world_ref="PROCESS:PS-TRI-01#raci.R",
           notes="verification: manual-lane; " + L[2].geometry_note(st["snt"]))
    D.fact(s, "text", "Acknowledge customer",
           f"On the FNOL and triage swimlane, 'Acknowledge customer' sits in the '{names[0]}' lane (RACI R = T10).",
           kind="lane_only", world_ref="PROCESS:PS-FNOL-05#raci.R",
           notes="verification: manual-lane; " + L[0].geometry_note(st["ack"]))
    D.fact(s, "notes", "scored by Sentinel within 15 minutes of FNOL",
           "Speaker notes: every new claim is scored by Sentinel within 15 minutes of FNOL (BR-TRI-007).",
           kind="speaker_notes", world_ref="RULE:BR-TRI-007@v1")
    D.fact(s, "notes", "1 business day for digital claims and 2 business days for other channels",
           "Speaker notes: FNOL acknowledgement is due within 1 business day (digital) or 2 business days (other channels), BR-FNOL-001 v3.",
           kind="speaker_notes", world_ref="RULE:BR-FNOL-001@v3")

    # 5 ---------------------------------------------------------------- Recovery & Subrogation (grouped lanes)
    s = D.content("Recovery & Subrogation – swimlane", "Stage 7 · Recovery & Subrogation")
    t06, t08 = W.team_name("T06", d), W.team_name("T08", d)
    L = swimlane(s, [t06, t08, "Third party / insurer"], heights=[1.15, 2.3, 1.15], grouped=True)
    a1 = L[0].step(2.4, "Estimate and recovery potential", w=1.6, size=9)
    b1 = L[1].step(4.3, "Identify recovery potential", w=1.5, size=9, row=0, rows=2)
    b2 = L[1].step(6.1, "Open subrogation case and demand", w=1.6, size=9, row=0, rows=2)
    b3 = L[1].step(8.0, "Solicitor referral", w=1.4, size=9, row=0, rows=2)
    b4 = L[1].step(9.7, "Recovery receipt and reserve adjustment", w=1.6, size=9, row=0, rows=2)
    b5 = L[1].step(11.5, "Write-off approval", w=1.25, size=9, row=0, rows=2)
    b6 = L[1].step(8.0, "Salvage disposal", w=1.4, size=9, row=1, rows=2)
    c1 = L[2].step(6.1, "Demand received", w=1.6, size=9, style="external")
    c2 = L[2].step(9.7, "Recovery paid or disputed", w=1.6, size=9, style="external")
    s.connect(a1, b1, a_site="r", b_site="t")
    s.connect(b1, b2)
    s.connect(b1, b6, a_site="b", b_site="l")
    s.connect(b2, b3)
    s.connect(b2, c1, a_site="b", b_site="t", dash=True)
    s.connect(c1, c2)
    s.connect(c2, b4, a_site="t", b_site="b", dash=True)
    s.connect(b3, b4)
    s.connect(b6, b4, a_site="r", b_site="b")
    s.connect(b4, b5)
    s.notes(P.notes(rng, "how recoveries are pursued once third-party fault is flagged",
                    ["A subrogation case is opened within 10 business days of the recovery flag (BR-REC-001).",
                     "Total-loss vehicles go to Salvanta Salvage within 5 business days of the total-loss decision (BR-REC-007)."]))
    D.place("vs1_lane_subro", s, "group", "Open subrogation case and demand",
            shape_name=L[1].group_name,
            notes="Lane membership via group shape 'Lane: Recoveries & Subrogation (Group)' (lane header + steps); "
                  + L[1].geometry_note(b2))
    D.fact(s, "group", "Estimate and recovery potential",
           f"'Estimate and recovery potential' sits in the '{t06}' lane on the Recovery & Subrogation swimlane (RACI R = T06).",
           kind="lane_only", world_ref="PROCESS:PS-ASM-04#raci.R", shape_name=L[0].group_name,
           notes="group-geometry: " + L[0].geometry_note(a1))
    D.fact(s, "notes", "opened within 10 business days of the recovery flag",
           "Speaker notes: a subrogation case is opened within 10 business days of the recovery flag (BR-REC-001).",
           kind="speaker_notes", world_ref="RULE:BR-REC-001@v1")

    # 6 ---------------------------------------------------------------- Fraud referral swimlane (ungrouped)
    s = D.content("Fraud referral – swimlane", "Stage 5 · Fraud Referral")
    t11, t02, t18 = W.team_name("T11", d), "Claims Operations", W.team_name("T18", d)
    L = swimlane(s, [t11, t02, t18], heights=[1.9, 1.45, 1.35])
    f1 = L[0].step(2.4, "Referral decision", w=1.5, size=10, style="decision", h=1.0)
    f2 = L[0].step(4.6, "Refer to SIU", w=1.5, size=10)
    f3 = L[1].step(6.6, "Notify customer of referral", w=1.7, size=10)
    f4 = L[0].step(8.6, "SIU investigation and outcome", w=1.7, size=10)
    f5 = L[0].step(10.8, "Human review of adverse outcome", w=1.7, size=10)
    f6 = L[2].step(8.6, "Consulted on notices and adverse outcomes", w=2.4, size=9, style="tile")
    s.connect(f1, f2)
    s.connect(f2, f3, a_site="b", b_site="l")
    s.connect(f3, f4, a_site="r", b_site="b")
    s.connect(f2, f4, a_site="r", b_site="l")
    s.connect(f4, f5)
    s.connect(f4, f6, a_site="b", b_site="t", dash=True, color="grey", arrow=False)
    D.need("RULE:BR-FRD-032@v2", "text")
    s.notes(P.notes(rng, "the fraud referral stage",
                    ["The referral notice must reach the customer within 10 business days of referral unless a deferral is certified (BR-FRD-032 v2).",
                     "SIU triages every new referral within 3 business days (BR-FRD-035 v2)."]))
    D.place("vs1_lane_notice", s, "text", "Notify customer of referral",
            notes="verification: manual-lane; lane order top-to-bottom: Counter-Fraud & SIU, Claims Operations, Compliance; "
                  + L[1].geometry_note(f3))
    D.fact(s, "text", "Human review of adverse outcome",
           f"'Human review of adverse outcome' sits in the '{t11}' lane of the fraud referral swimlane (RACI R = T11).",
           kind="lane_only", world_ref="PROCESS:PS-FRD-05#raci.R",
           notes="verification: manual-lane; " + L[0].geometry_note(f5))
    D.fact(s, "notes", "within 10 business days of referral unless a deferral is certified",
           "Speaker notes: the customer referral notice is due within 10 business days of referral unless deferred (BR-FRD-032 v2).",
           kind="speaker_notes", world_ref="RULE:BR-FRD-032@v2")

    # 7 ---------------------------------------------------------------- Reserving swimlane
    s = D.content("Reserving – swimlane", "Stage 4 · Reserving")
    L = swimlane(s, ["Claims Operations", W.team_name("T09", d), W.team_name("T17", d)],
                 heights=[1.6, 1.6, 1.4])
    r1 = L[0].step(2.5, "Set initial reserve", w=1.6, size=10)
    r2 = L[0].step(4.6, "Authority check and approval", w=1.7, size=10)
    r3 = L[0].step(10.2, "Periodic reserve review", w=1.7, size=10)
    r4 = L[1].step(10.2, "Periodic reserve review (Tier-3)", w=1.7, size=10)
    r5 = L[1].step(7.0, "Large loss notification", w=1.7, size=10)
    r6 = L[2].step(7.0, "Notification recorded in ReCede", w=1.7, size=10, style="system")
    s.connect(r1, r2)
    s.connect(r2, r3)
    s.connect(r2, r5, a_site="b", b_site="t")
    s.connect(r5, r6)
    s.connect(r5, r4, a_site="r", b_site="l", dash=True, color="grey")
    s.notes(P.notes(rng, "who sets, approves and reviews reserves",
                    ["A claim-specific initial reserve replaces the FNOL default reserve within 2 business days of FNOL (BR-RSV-001).",
                     "Tier-3 reserves are reviewed at least every 14 days from 1 July 2026 (BR-RSV-007 v3)."]))
    D.fact(s, "text", "Large loss notification",
           f"'Large loss notification' sits in the '{W.team_name('T09', d)}' lane of the reserving swimlane (RACI R = T09).",
           kind="lane_only", world_ref="PROCESS:PS-RSV-04#raci.R",
           notes="verification: manual-lane; " + L[1].geometry_note(r5))
    D.fact(s, "notes", "reviewed at least every 14 days from 1 July 2026",
           "Speaker notes: Tier-3 reserves are reviewed at least every 14 days from 2026-07-01 (BR-RSV-007 v3).",
           kind="speaker_notes", world_ref="RULE:BR-RSV-007@v3")

    # 8 ---------------------------------------------------------------- Settlement swimlane
    s = D.content("Settlement – swimlane", "Stage 6 · Settlement")
    L = swimlane(s, ["Claims Operations", W.team_name("T16", d)], heights=[2.3, 1.6])
    p1 = L[0].step(2.5, "Settlement offer", w=1.6, size=10, row=0, rows=2)
    p2 = L[0].step(4.6, "Payment authorisation", w=1.6, size=10, row=0, rows=2)
    p5 = L[0].step(2.5, "Fast-track straight-through settlement", w=2.2, size=9, row=1, rows=2)
    p3 = L[1].step(6.9, "Sanctions screening and payment", w=1.9, size=10)
    p4 = L[0].step(9.4, "Close claim and zero reserve", w=1.8, size=10, row=0, rows=2)
    s.connect(p1, p2)
    s.connect(p2, p3, a_site="r", b_site="t")
    s.connect(p3, p4, a_site="r", b_site="b")
    s.connect(p5, p4, a_site="r", b_site="l")
    s.notes(P.notes(rng, "settlement and payment",
                    ["Payments go out in the next payment run, Monday to Friday at 16:30.",
                     "On final settlement the reserve is reduced to zero within 1 business day with a settlement close movement of type ST (BR-RSV-014)."]))
    D.fact(s, "text", "Sanctions screening and payment",
           f"'Sanctions screening and payment' sits in the '{W.team_name('T16', d)}' lane (RACI R = T16).",
           kind="lane_only", world_ref="PROCESS:PS-STL-03#raci.R",
           notes="verification: manual-lane; " + L[1].geometry_note(p3))
    D.fact(s, "notes", "settlement close movement of type ST",
           "Speaker notes: on final settlement the reserve is zeroed within 1 business day with a settlement close movement (type ST), BR-RSV-014.",
           kind="speaker_notes", world_ref="RULE:BR-RSV-014@v1")

    # 9 ---------------------------------------------------------------- section
    D.section("02", "Stage reference", "Owners, service levels and systems as at the issue date")

    # 10 --------------------------------------------------------------- stage owners
    s = D.content("Stage owners", "Stage reference")
    rows = []
    for sid in ["S1", "S2", "S3", "S4", "S5", "S6", "S7"]:
        stg = W.stages[sid]
        own = W.owner_of_process(sid, d)
        rows.append((sid, stg["name"], W.name_of(own, d), W.title_of(own, d),
                     ", ".join(W.system_name(x, d) for x in stg["systems"])))
    s.table(0.5, 1.45, 12.3, ["Stage", "Name", "Process owner", "Title", "Systems"], rows,
            col_w=[0.6, 2.0, 1.8, 3.2, 4.7], row_h=0.5, size=10, first_col_bold=True)
    s.notes(P.notes(rng, "who owns each stage of the lifecycle"))
    D.fact(s, "table", "Freya Lindahl",
           "Stage S7 Recovery & Subrogation is owned by Freya Lindahl, Head of Recoveries & Subrogation (as at 2026-10-02).",
           kind="general", world_ref="PROCESS:S7#owner_history")
    D.fact(s, "table", "Lena Kristiansen",
           "Stage S4 Reserving is owned by Lena Kristiansen, Head of Reserving (as at 2026-10-02).",
           kind="general", world_ref="PROCESS:S4#owner_history")

    # 11 --------------------------------------------------------------- SLAs part 1 (native)
    s = D.content("Service levels by step – FNOL to reserving", "Stage reference")
    ids1 = [x for x in W.steps if W.steps[x]["stage"] in ("S1", "S2", "S3", "S4")]
    rows = [(sid, W.steps[sid]["name"], W.steps[sid]["sla"]["text"]) for sid in ids1]
    s.table(0.5, 1.4, 12.3, ["Step", "Activity", "Service level"], rows, col_w=[1.2, 3.6, 7.5],
            row_h=0.305, size=9)
    s.notes(P.notes(rng, "the service levels for the first four stages", n_filler=1))
    D.fact(s, "table", "5 business days; Tier-3 within 48 hours (BR-ASM-005 v3)",
           "Inspection or desk assessment (PS-ASM-02): 5 business days; Tier-3 within 48 hours (BR-ASM-005 v3).",
           kind="general", world_ref="PROCESS:PS-ASM-02#sla")

    # 12 --------------------------------------------------------------- SLAs part 2 (image table)
    s = D.content("Service levels by step – fraud, settlement and recovery", "Stage reference")
    ids2 = [x for x in W.steps if W.steps[x]["stage"] in ("S5", "S6", "S7")]
    rows = [(sid, W.steps[sid]["name"], W.steps[sid]["sla"]["text"]) for sid in ids2]
    png = R.table_image(["Step", "Activity", "Service level"], rows, [1.3, 3.6, 6.2], size=26,
                        title="Service levels – stages 5 to 7", note="Source: step catalogue, as at issue date")
    s.picture_fit(png, 0.6, 1.35, 12.1, 5.55, alt="Table of service levels for fraud referral, settlement and recovery steps PS-FRD-01 to PS-REC-06.")
    s.notes(P.notes(rng, "the service levels for the later stages", n_filler=1))
    D.fact(s, "image", "SIU triage within 3 business days",
           "Image table: PS-FRD-04 SIU investigation and outcome – SIU triage within 3 business days (BR-FRD-035 v2).",
           kind="image_table", world_ref="PROCESS:PS-FRD-04#sla")
    D.fact(s, "image", "demand within 10 business days",
           "Image table: PS-REC-02 Open subrogation case and demand – demand within 10 business days.",
           kind="image_table", world_ref="PROCESS:PS-REC-02#sla")

    # 13 --------------------------------------------------------------- Claims Hub screen
    s = D.content("Claims Hub – claim overview (illustrative)", "Screens")
    ref = f"CLM-UK-2026-{rng.randint(300000, 399999)}"
    png = R.ui_screen(
        "Claims Hub", "Beth Kilbride · Motor Claims – Leeds",
        ["Work queue", "Claims", "Reserves", "Payments", "Recoveries", "Fraud referrals", "Reports"], "Claims",
        f"Claims  /  {ref}  /  Overview", f"Claim {ref}",
        [
            ("Product", "Motor Private UK"), ("Loss type", "Collision"),
            ("Tier", "Tier-2"), ("Current stage", "Recovery & Subrogation"),
            ("Claim handler", "Beth Kilbride"), ("Recovery case", "Open – demand issued"),
            ("Initial reserve due", "2 business days after FNOL"), ("Assessor appointment", "2 business days after triage"),
        ],
        chips=[("OPEN", "teal"), ("THIRD PARTY AT FAULT", "amber"), ("MIGRATED – WAVE 1", "sky")],
        side_panel=("Lifecycle", ["1  FNOL  ✓", "2  Triage  ✓", "3  Assessment  ✓", "4  Reserving  ✓",
                                  "6  Settlement  ✓", "7  Recovery  ●"]),
        table=(["Date", "Event", "By"], [("14 Sep 2026", "Claim migrated from CLARA", "Wave 1"),
                                         ("Day 0", "Recovery potential flagged", "assessor"),
                                         ("Day 3", "Subrogation demand issued", "recoveries")]))
    s.picture_fit(png, 0.9, 1.35, 11.5, 5.55, alt=f"Mock Claims Hub claim overview screen for an illustrative claim {ref} in the Recovery & Subrogation stage.")
    s.notes(P.notes(rng, "what the lifecycle looks like on a Claims Hub claim record",
                    ["The record shown is test data used for training; it is not a live claim."]))
    D.fact(s, "image", "Initial reserve due",
           "Claims Hub claim overview screen shows the field 'Initial reserve due: 2 business days after FNOL' (BR-RSV-001).",
           kind="screenshot", world_ref="RULE:BR-RSV-001@v1")

    # 14 --------------------------------------------------------------- systems by stage (nested groups)
    s = D.content("Systems by stage", "Stage reference")
    outer = s.group("Systems by stage")
    stage_needles = {}
    for i, sid in enumerate(["S1", "S2", "S3", "S4", "S5", "S6", "S7"]):
        stg = W.stages[sid]
        g = outer.group(f"Stage {sid} systems")
        x = 0.5 + i * 1.76
        g.box(x, 1.5, 1.66, 0.7, f"{sid} · {stg['name']}", style="pentagon", size=10, bold=True)
        sysnames = [W.system_name(xx, d) for xx in stg["systems"]]
        for j, nm in enumerate(sysnames):
            g.box(x + 0.08, 2.4 + j * 0.62, 1.5, 0.5, nm, style="system", size=9)
        stage_needles[sid] = f"{sid} · {stg['name']} " + " ".join(sysnames)
    s.notes(P.notes(rng, "which platforms support each stage",
                    ["During migration both CLARA and Claims Hub appear against most stages."]))
    D.fact(s, "group", stage_needles["S5"],
           "Stage S5 Fraud Referral is supported by Sentinel, CLARA, Claims Hub, SIU Case Manager and Notify.",
           kind="visual_only", world_ref="PROCESS:S5#systems", shape_name="Stage S5 systems")
    D.fact(s, "group", stage_needles["S7"],
           "Stage S7 Recovery & Subrogation is supported by CLARA, Subrogation Tracker and Claims Hub.",
           kind="visual_only", world_ref="PROCESS:S7#systems", shape_name="Stage S7 systems")

    # 15 --------------------------------------------------------------- what changed
    s = D.content("What changed in version 3.0", "Change log")
    s.bullets(0.6, 1.5, 7.4, 4.8, [
        "Fraud referral stage redrawn for the Tier-3 decision point effective 1 October 2026 (BR-FRD-031 v2, DEC-014).",
        "Customer notice deferrals beyond 30 days now need the Head of Counter-Fraud & SIU, with Compliance notified the same day (BR-FRD-036 v2).",
        "Assessment, reserving, settlement and recovery steps now run in Claims Hub for UK motor claims migrated in Wave 1 (14 September 2026).",
        "Recovery & Subrogation shown as a Group function, reflecting the September 2025 re-organisation.",
        "Service-level table refreshed against the step catalogue.",
    ], size=13)
    D.need("RULE:BR-FRD-036@v2", "text")
    s.box(8.5, 1.6, 4.3, 2.0, [{"text": P.pick(rng, P.TAKEAWAY_HEAD), "bold": True, "size": 13},
                               {"text": "One lifecycle, seven stages, shown by lane so that ownership is visible at a glance.", "size": 11}],
          style="tile", align="l", anchor="t", margins=0.15)
    s.notes(P.notes(rng, "the changes in this version"))
    D.fact(s, "text", "deferrals beyond 30 days now need the Head of Counter-Fraud & SIU",
           "From 2026-10-01 customer-notice deferrals beyond 30 days need the Head of Counter-Fraud & SIU and Compliance is notified the same day (BR-FRD-036 v2).",
           kind="general", world_ref="RULE:BR-FRD-036@v2")

    # 16 --------------------------------------------------------------- glossary
    CM.glossary(D, [
        ("assessor", "Claims Assessor, internal or panel, who inspects or desk-assesses a loss"),
        ("claim handler", "Employee who manages a claim day to day"),
        ("FNOL", "First notice of loss, by any channel"),
        ("loss type", "The peril or cause of loss, e.g. Escape of Water"),
        ("SIU referral", "Referral of a claim to Counter-Fraud & SIU"),
        ("reserve table", "CLARA table CLR.T_RESERVE holding case reserves"),
        ("Recovery & Subrogation", "Recovery of outlay from a responsible third party"),
        ("Tier-3", "Claim meeting the Tier-3 definition in BR-TRI-003 v3"),
        ("Sentinel score", "Fraud score from 0 to 100 (formerly FRAUDNET)"),
        ("Claims Hub", "Target claims platform replacing CLARA"),
    ])

    # 17 --------------------------------------------------------------- document control
    hist = CM.history_rows(D, [("2.0", "Re-drawn for the Wave 1 services"), ("2.1", ""), ("3.0", "")])
    CM.doc_control(D, hist, [("P005", "Approved"), ("P011", "Approved"), ("P008", "Reviewed"),
                             ("P013", "Reviewed")], status="Approved",
                   reviewers=[W.name_of("P009", d), W.name_of("P033", d)],
                   distribution="Claims leadership team, Claims Hub squads, IBM Programme Skerry team",
                   purpose="Single reference view of the claims lifecycle for business and delivery teams.")
    return D

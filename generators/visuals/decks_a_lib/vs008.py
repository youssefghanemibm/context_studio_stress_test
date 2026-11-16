"""VS008 Reserving Process (2026-07-06, Lena Kristiansen, approved).

The large-loss rule lives only in the arrow 'Reserve movement > £250,000' -> 'Notify ReCede within
24h'; the Reserving Committee chair appears only in the notes of slide 5."""
from __future__ import annotations

from . import common as CM
from . import phrases as P
from . import raster as R
from .core import Deck
from .lanes import swimlane


def short(text: str, n: int) -> str:
    if len(text) <= n:
        return text
    cut = text[:n].rsplit(" ", 1)[0].rstrip(" ,;-(")
    return cut + "…"


def build(W, out_dir):
    D = Deck(W, "VS008", version="5.0", doc_ref="RSV-PRC-003", out_dir=out_dir)
    d = D.date
    rng = D.rng

    # 1 title
    D.title_slide(D.title, "Case reserves from FNOL to settlement – authority, review and large-loss notification",
                  [f"Reserving  |  Version {D.version}  |  {D.date_long()}",
                   f"Process owner: {D.author}, {D.author_title}", "Status: Approved"])

    # 2 agenda
    CM.agenda(D, ["Authority and large-loss flow", "Reserving swimlane", "Governance", "Authority limits",
                  "Tier-3 review interval", "Programs that write the reserve table", "Target state in Claims Hub",
                  "Parallel run", "Controls, accountability and systems"], kicker="Reserving process")

    # 3 authority and large-loss flow (connectors)
    s = D.content("Reserve movement – authority and large-loss flow", "Decision flow")
    post = s.box(0.5, 3.15, 2.1, 0.85, "Post reserve movement", style="terminal", size=12, bold=True)
    auth = s.box(3.1, 2.85, 2.5, 1.45, "Within holder authority?", style="decision", size=12, bold=True)
    esc = s.box(3.25, 5.3, 2.2, 0.8, "Escalate to next authority level", style="process", size=11)
    big = s.box(6.4, 2.85, 2.6, 1.45, "Reserve movement > £250,000", style="decision", size=12, bold=True)
    rec = s.box(10.0, 1.45, 2.6, 0.85, "Notify ReCede within 24h", style="alert", size=12, bold=True)
    rev = s.box(10.0, 4.8, 2.6, 0.85, "Periodic reserve review", style="outcome", size=12)
    s.connect(post, auth, a_site="r", b_site="l")
    s.connect(auth, esc, a_site="b", b_site="t", label="No", name="rsv-no-auth", label_size=11)
    s.connect(esc, auth, a_site="l", b_site="l", dash=True, color="grey")
    s.connect(auth, big, a_site="r", b_site="l", label="Yes", name="rsv-yes-auth", label_size=11)
    s.connect(big, rec, a_site="t", b_site="l", label="Yes", name="rsv-llnt-yes", label_size=11)
    s.connect(big, rev, a_site="b", b_site="l", label="No", name="rsv-llnt-no", label_size=11)
    s.connect(rec, rev, a_site="b", b_site="t", dash=True, color="grey")
    s.text(0.5, 5.4, 2.5, 1.2, [{"text": "Applies in CLARA and in reserve-engine for migrated claims.", "size": 9}],
           size=9, color="slate", fill="grey_l", margins=0.08)
    s.notes(P.notes(rng, "what happens when a reserve movement is posted",
                    ["Escalations go to the next authority level until the movement is within the approver's limit; above the Claims Director the Reserving Committee decides."]))
    D.place("vs8_llnt", s, "connector", "Reserve movement > £250,000 -> Notify ReCede within 24h",
            notes="Arrow labelled 'Yes' (label box 'label:rsv-llnt-yes'); no slide text states the LLNT rule.")
    D.fact(s, "connector", "Within holder authority? -> Escalate to next authority level [label: No]",
           "A reserve movement above the holder's authority is escalated to the next authority level.", kind="arrow_only",
           world_ref="PROCESS:PS-RSV-02#decision")
    D.fact(s, "connector", "Reserve movement > £250,000 -> Periodic reserve review [label: No]",
           "Movements not above £250,000 go straight to periodic reserve review.", kind="arrow_only",
           world_ref="PROCESS:PS-RSV-02#decision")

    # 4 swimlane (grouped)
    s = D.content("Reserving – swimlane", "Swimlane")
    L = swimlane(s, ["CLARA / reserve-engine", "Claims Operations", W.team_name("T09", d), W.team_name("T12", d),
                     W.team_name("T17", d)], heights=[0.95, 1.2, 1.2, 1.0, 1.0], grouped=True)
    a = L[0].step(2.4, "FNOL default reserve created", w=1.8, size=9)
    b1 = L[1].step(4.5, "Set initial reserve", w=1.6, size=9)
    b2 = L[1].step(6.4, "Authority check and approval", w=1.7, size=9)
    b3 = L[1].step(10.6, "Periodic reserve review", w=1.7, size=9)
    c1 = L[2].step(8.4, "Large loss notification", w=1.7, size=9)
    c2 = L[2].step(10.6, "Tier-3 reserve review", w=1.7, size=9)
    dd = L[3].step(6.4, "Consulted on escalations", w=1.7, size=9, style="tile")
    e = L[4].step(8.4, "Notification recorded in ReCede", w=1.7, size=9, style="system")
    s.connect(a, b1, a_site="r", b_site="t")
    s.connect(b1, b2)
    s.connect(b2, b3)
    s.connect(b2, c1, a_site="b", b_site="l")
    s.connect(b2, dd, a_site="b", b_site="t", dash=True, color="grey", arrow=False)
    s.connect(c1, e)
    s.connect(c1, c2)
    s.notes(P.notes(rng, "who does what in the reserving process",
                    ["A claim-specific initial reserve must replace the FNOL default reserve within 2 business days of FNOL (BR-RSV-001)."]))
    D.fact(s, "group", "Large loss notification", f"'Large loss notification' sits in the {W.team_name('T09', d)} lane (RACI R = T09).",
           kind="visual_only", world_ref="PROCESS:PS-RSV-04#raci.R", shape_name=L[2].group_name,
           notes="lane group; R is also listed in the RACI table on slide 13. group-geometry: " + L[2].geometry_note(c1))
    D.fact(s, "group", "Set initial reserve", "'Set initial reserve' sits in the Claims Operations lane (RACI R = T02).",
           kind="visual_only", world_ref="PROCESS:PS-RSV-01#raci.R", shape_name=L[1].group_name,
           notes="lane group; R is also listed in the RACI table on slide 13. group-geometry: " + L[1].geometry_note(b1))
    D.fact(s, "notes", "within 2 business days of FNOL (BR-RSV-001)",
           "Speaker notes: the initial reserve replaces the FNOL default reserve within 2 business days (BR-RSV-001).",
           kind="speaker_notes", world_ref="RULE:BR-RSV-001@v1")

    # 5 governance (chair only in notes)
    s = D.content("Governance – Reserving Committee", "Governance")
    com = W.committees["COM-01"]
    D.need("COMMITTEE:COM-01", "chair_history")
    s.box(0.6, 1.5, 6.0, 1.6, [{"text": "Remit", "bold": True, "size": 13}, {"text": com["remit"], "size": 12}],
          style="tile", align="l", anchor="t", margins=0.15)
    rows = [(W.name_of(p, d), W.title_of(p, d)) for p in com["members"]]
    s.text(7.0, 1.35, 5.8, 0.3, [{"text": "Members", "bold": True}], size=12, color="navy")
    s.table(7.0, 1.7, 5.8, ["Name", "Title"], rows, col_w=[2.2, 3.6], row_h=0.4, size=11, first_col_bold=True)
    s.bullets(0.6, 3.4, 6.0, 3.0, ["Approves reserving policy and authority limits.",
                                   "Approves reserves above the Claims Director's limit.",
                                   "Receives the Tier-3 review exception report.",
                                   "Approved the shorter Tier-3 review interval at its June 2026 meeting (DEC-008)."], size=12)
    s.notes(P.notes(rng, "how reserving is governed",
                    ["The Reserving Committee has been chaired by Lena Kristiansen since 1 September 2025.",
                     "Before that the Chief Actuary chaired it."]))
    D.place("vs8_notes_chair", s, "notes", "chaired by Lena Kristiansen since 1 September 2025")
    D.fact(s, "text", "Approved the shorter Tier-3 review interval at its June 2026 meeting (DEC-008)",
           "The Reserving Committee approved the 14-day Tier-3 review cadence at its June 2026 meeting (DEC-008, 2026-06-09).",
           world_ref="DECISION:DEC-008")

    # 6 authority limits (image table)
    s = D.content("Reserve authority limits", "Authority")
    D.need("RULE:BR-RSV-003@v3", "parameters")
    p3 = W.rules["BR-RSV-003"]["versions"][2]["parameters"]
    rows = [("Claims Handler", f"£{p3['claims_handler']:,}"), ("Team Leader", f"£{p3['team_leader']:,}"),
            ("Claims Manager", f"£{p3['claims_manager']:,}"), ("Claims Director", f"£{p3['claims_director']:,}"),
            ("Reserving Committee", f"above £{p3['claims_director']:,}")]
    png = R.table_image(["Authority holder", "Reserve authority (per claim)"], rows, [4, 4], size=30,
                        title="Reserve authority – BR-RSV-003 v3 (from 1 September 2025)",
                        note="Nordic reserves are tested at the GBP equivalent at the GL month-end rate.")
    s.picture_fit(png, 1.5, 1.35, 10.3, 5.55,
                  alt="Reserve authority table BR-RSV-003 v3: Claims Handler £25,000; Team Leader £100,000; Claims Manager £500,000; Claims Director £2,000,000; above that the Reserving Committee.",
                  title="Reserve authority limits")
    s.notes(P.notes(rng, "the reserve authority limits", n_filler=1))
    # Vision OCR reads this two-column table column by column, so the needle is the cell value
    # alone; the row it belongs to (Team Leader) is carried by the statement.
    D.fact(s, "image", "£100,000",
           "Image table: reserve authority for a Team Leader is £100,000 (BR-RSV-003 v3); the value sits in the Team Leader row.", kind="image_table",
           world_ref="RULE:BR-RSV-003@v3#parameters.team_leader")
    D.fact(s, "alt_text", "Claims Director £2,000,000",
           "Alt text: Claims Director reserve authority £2,000,000; above that the Reserving Committee.", kind="alt_text",
           world_ref="RULE:BR-RSV-003@v3#parameters.claims_director")

    # 7 tier-3 review interval (chart only)
    s = D.content("Tier-3 reserve review interval", "Review cadence")
    vers = W.rules["BR-RSV-007"]["versions"]
    cats = ["v1 (2015 – 2023)", "v2 (Jan 2024 – Jun 2026)", "v3 (from 1 Jul 2026)"]
    s.chart(0.6, 1.4, 7.4, 5.4, "column", cats, [("Maximum days between reviews", [v["parameters"]["review_days"] for v in vers])],
            title="BR-RSV-007 – maximum interval between Tier-3 reserve reviews", legend=False, colors=["teal"])
    s.box(8.4, 1.6, 4.4, 3.2, [{"text": "What changed", "bold": True, "size": 13},
                               {"text": "The interval was shortened again from 1 July 2026, after the Reserving Committee approved the proposal from the March 2026 design review.", "size": 12}],
          style="tile", align="l", anchor="t", margins=0.15)
    s.notes(P.notes(rng, "how often Tier-3 reserves are reviewed",
                    ["reserve-engine's review scheduling was corrected under CHUB-322, resolved on 3 July 2026."]))
    D.fact(s, "chart", "Maximum days between reviews: v3 (from 1 Jul 2026)=14",
           "Tier-3 reserves must be reviewed at least every 14 days from 2026-07-01 (BR-RSV-007 v3); 21 days before that, 30 days until 2023.",
           kind="chart_only", world_ref="RULE:BR-RSV-007@v3#parameters.review_days")
    D.fact(s, "notes", "CHUB-322, resolved on 3 July 2026",
           "Speaker notes: reserve-engine review scheduling was corrected under CHUB-322 (resolved 2026-07-03).",
           kind="speaker_notes", world_ref="TICKET:CHUB-322")

    # 8 reserve writers (nested groups)
    s = D.content("Programs that write the reserve table (CLR.T_RESERVE)", "CLARA")
    outer = s.group("Reserve table writers")
    g1 = outer.group("CLR.T_RESERVE writers")
    g1.box(0.6, 1.55, 7.6, 0.5, "Write CLR.T_RESERVE", style="tile", fill="navy2", color="white", size=13, bold=True)
    for i, pid in enumerate(W.reserve_writers):
        c, r = i % 4, i // 4
        prog = W.programs[pid]
        g1.box(0.6 + c * 1.92, 2.2 + r * 1.25, 1.8, 1.05,
               [{"text": pid, "bold": True, "size": 12}, {"text": short(prog["description"], 44), "size": 8}],
               style="process", margins=0.05)
    g2 = outer.group("Movement-only writer")
    g2.box(8.7, 1.55, 4.1, 0.5, "Write CLR.T_RESERVE_MOVEMENT only", style="tile", fill="slate", color="white", size=12, bold=True)
    g2.box(8.7, 2.2, 4.1, 1.05, [{"text": "CLRRS150", "bold": True, "size": 12},
                                 {"text": short(W.programs["CLRRS150"]["description"], 60), "size": 8}], style="tile", margins=0.05)
    s.text(0.6, 4.95, 12.2, 1.6, [{"text": "Note", "bold": True, "size": 11},
                                  {"text": "The CLARA data dictionary lists seven writers; the code shows eight.", "size": 11}],
           size=11, color="slate")
    D.need("PROGRAM:CLRGL090", "notes")
    s.notes(P.notes(rng, "which CLARA programs update case reserves",
                    ["CLRGL090 updates CLR.T_RESERVE without writing CLR.T_RESERVE_MOVEMENT (internal audit finding IA-25-07), which is why the data dictionary misses it.",
                     "CLRRS150 writes reserve movements only."]))
    needle = "Write CLR.T_RESERVE " + " ".join(f"{p} {short(W.programs[p]['description'], 44)}" for p in W.reserve_writers[:1])
    D.fact(s, "group", "CLRGL090", "CLRGL090 is one of the eight programs that write CLR.T_RESERVE.",
           kind="visual_only", world_ref="PROGRAM:CLRGL090#writes_tables:CLR.T_RESERVE", shape_name="CLR.T_RESERVE writers")
    D.fact(s, "group", needle, "CLRFN030 writes CLR.T_RESERVE (first of the eight writers).", kind="visual_only",
           world_ref="PROGRAM:CLRFN030#writes_tables:CLR.T_RESERVE", shape_name="CLR.T_RESERVE writers")
    D.fact(s, "group", "Write CLR.T_RESERVE_MOVEMENT only CLRRS150",
           "CLRRS150 writes CLR.T_RESERVE_MOVEMENT only, not CLR.T_RESERVE.", kind="visual_only",
           world_ref="PROGRAM:CLRRS150#writes_tables", shape_name="Movement-only writer")
    D.fact(s, "notes", "without writing CLR.T_RESERVE_MOVEMENT (internal audit finding IA-25-07)",
           "Speaker notes: CLRGL090 updates CLR.T_RESERVE without writing CLR.T_RESERVE_MOVEMENT (IA-25-07); the data dictionary omits it.",
           kind="speaker_notes", world_ref="PROGRAM:CLRGL090#notes")

    # 9 target state (raster)
    s = D.content("Target state – reserves in Claims Hub", "Target state")
    cv = R.Canvas(2400, 1250)
    cv.title("Reserve data flow – target", "reserve-engine owns case reserves for migrated claims")
    E = R.Canvas.edge
    cla = cv.box(80, 260, 380, 140, "CLARA", fill="grey_l", size=34, bold=True)
    mq = cv.box(80, 560, 380, 130, "MQ Backbone", fill="white", size=30)
    esp = cv.box(80, 860, 380, 130, "Event Streaming Platform", fill="white", size=26)
    rse = cv.box(860, 520, 520, 220, "reserve-engine", fill="teal_l", outline="teal", size=38, bold=True,
                 sub="reserve.reserve · reserve.reserve_movement · reserve.review_schedule", sub_size=22)
    gps = cv.box(1800, 300, 480, 140, "gl-posting-svc", fill="white", outline="teal", size=30)
    rfs = cv.box(1800, 820, 480, 140, "reporting-feed-svc", fill="white", outline="teal", size=30)
    gl = cv.box(1800, 1050, 480, 120, "Group Ledger", fill="grey_l", size=28)
    cv.arrow([E(cla, "b"), E(mq, "t")], "CLX-IF-042", label_dx=120)
    cv.arrow([E(mq, "b"), E(esp, "t")], "CLX-IF-049", label_dx=120)
    cv.arrow([E(esp, "r"), (860, 700)], "claims.reserve.movement.v1", label_at=0.5, label_dy=40)
    cv.arrow([(1380, 580), E(gps, "l")], "reserve.changed.v2", label_at=0.5)
    cv.arrow([(1380, 680), E(rfs, "l")], "reserve.changed.v2", label_at=0.5)
    cv.arrow([E(gps, "b"), (2040, 600), (2380, 600), (2380, 1110), E(gl, "r")], "CLX-IF-050", label_at=0.55, label_dx=-100)
    png = cv.png()
    s.picture_fit(png, 0.5, 1.35, 12.3, 5.55,
                  alt="Target reserve flow: CLARA movements reach reserve-engine via CLX-IF-042, the MQ Backbone, CLX-IF-049 and topic claims.reserve.movement.v1; reserve-engine publishes reserve.changed.v2 to gl-posting-svc and reporting-feed-svc; gl-posting-svc posts journals to Group Ledger via CLX-IF-050.",
                  title="Reserve data flow – target")
    s.notes(P.notes(rng, "where reserves will live after migration",
                    ["reserve-engine will record currency revaluations as RV movements, closing IA-25-07 in the target (DEC-005)."]))
    D.fact(s, "image", "reserve.changed.v2",
           "Target-state image: reserve-engine publishes reserve.changed.v2 to gl-posting-svc and reporting-feed-svc.",
           kind="image_text", world_ref="TOPIC:reserve.changed.v2")
    D.fact(s, "alt_text", "gl-posting-svc posts journals to Group Ledger via CLX-IF-050",
           "Alt text: gl-posting-svc posts journals to Group Ledger via CLX-IF-050.", kind="alt_text",
           world_ref="INTERFACE:CLX-IF-050")
    D.fact(s, "notes", "record currency revaluations as RV movements",
           "Speaker notes: reserve-engine will record currency revaluations as RV movements (DEC-005).",
           kind="speaker_notes", world_ref="DECISION:DEC-005")

    # 10 parallel run
    s = D.content("Reserve parallel run", "Migration")
    D.need("TIMELINE:programme", "parallel_run.from")
    s.bullets(0.6, 1.5, 7.6, 5.0, [
        "CLARA and reserve-engine run side by side from 2 March to 28 August 2026 (CHUB-241).",
        "reserve-engine receives every CLARA movement through the CLX-IF-049 bridge.",
        "Daily variances are reviewed by the Reserve & Finance squad with Reserving.",
        "reserve-engine becomes the reserve system for UK motor with Wave 1 on 14 September 2026.",
    ], size=13)
    s.box(8.6, 1.6, 4.2, 2.5, [{"text": "Status at issue date", "bold": True, "size": 13},
                               {"text": "In progress – final weeks of the run.", "size": 12}],
          style="tile", align="l", anchor="t", margins=0.15)
    s.notes(P.notes(rng, "the parallel run", [f"{W.name_of('P041', d)} leads the reserve-engine side for the Reserve & Finance squad."]))
    D.fact(s, "text", "from 2 March to 28 August 2026 (CHUB-241)",
           "Reserve parallel run CLARA vs reserve-engine: 2026-03-02 to 2026-08-28 (CHUB-241).",
           world_ref="TIMELINE:programme#parallel_run.from")

    # 11 section
    D.section("02", "Controls and reference", "Key controls, accountability and systems")

    # 12 controls
    s = D.content("Key controls", "Controls")
    rows = [("BR-RSV-001", "Initial reserve replaces the FNOL default reserve within 2 business days of FNOL"),
            ("BR-RSV-003 v3", "Reserve authority by role – see authority limits"),
            ("BR-RSV-007 v3", "Tier-3 periodic review – see review interval"),
            ("BR-RSV-011 v2", "Large loss notification to Reinsurance – see decision flow"),
            ("BR-RSV-014", "On final settlement the reserve is reduced to zero within 1 business day; movement type ST")]
    s.table(0.5, 1.45, 12.3, ["Rule", "Control"], rows, col_w=[1.8, 10.5], row_h=0.55, size=12, first_col_bold=True)
    s.notes(P.notes(rng, "the key reserving controls", n_filler=1))
    D.fact(s, "table", "movement type ST",
           "BR-RSV-014: on final settlement the reserve is reduced to zero within 1 business day with movement type ST.",
           world_ref="RULE:BR-RSV-014@v1")

    # 13 RACI
    s = D.content("Accountability (RACI)", "Controls")
    rows = CM.raci_rows(W, ["PS-RSV-01", "PS-RSV-02", "PS-RSV-03", "PS-RSV-04"], d)
    s.table(0.5, 1.45, 12.3, ["Step", "Activity", "Responsible", "Accountable", "Consulted", "Informed"], rows,
            col_w=[1.1, 2.6, 2.7, 1.8, 2.0, 2.1], row_h=0.62, size=10, first_col_bold=True)
    s.notes(P.notes(rng, "who is accountable at each step", n_filler=1))
    D.fact(s, "table", "Per Øverland",
           "PS-RSV-04 Large loss notification: accountable Per Øverland, Reinsurance Manager.",
           world_ref="PROCESS:PS-RSV-04#raci.A")

    # 14 systems
    s = D.content("Systems and feeds", "Reference")
    rows = [(W.system_name("SYS01", d), "Case reserves for claims not yet migrated", W.name_of("P016", d)),
            ("reserve-engine", "Case reserves for migrated claims (from Wave 1)", W.name_of("P041", d)),
            (W.system_name("SYS21", d), "IBNR triangles and reserve adequacy", W.name_of("P009", d)),
            (W.system_name("SYS07", d), "Reinsurance administration", W.name_of("P038", d)),
            ("CLX-IF-058", f"Reserve Triangles Extract, {W.interface_schedule('CLX-IF-058', d)}", W.name_of("P009", d))]
    s.table(0.5, 1.45, 12.3, ["System / feed", "Use in reserving", "Owner"], rows, col_w=[3.0, 6.5, 2.8], row_h=0.55,
            size=12, first_col_bold=True)
    s.notes(P.notes(rng, "the systems behind reserving", n_filler=1))
    D.fact(s, "table", "Reserve Triangles Extract, monthly, 3rd business day",
           "CLX-IF-058 Reserve Triangles Extract runs monthly on the 3rd business day (owner Lena Kristiansen).",
           world_ref="INTERFACE:CLX-IF-058#schedule")

    # 15 document control
    hist = CM.history_rows(D, [("4.0", "Authority limits v3 from 1 September 2025"), ("4.1", ""), ("5.0", "")], spacing=(60, 140))
    CM.doc_control(D, hist, [("P001", "Approved"), ("P005", "Approved"), ("P010", "Reviewed")], status="Approved",
                   reviewers=[W.name_of(x, d) for x in ("P030", "P021", "P041")],
                   distribution="Reserving, Claims Operations, Major & Complex Loss, Reinsurance, Hub Squad – Reserve & Finance",
                   purpose="Reserving process from FNOL default reserve to settlement, including the revised Tier-3 review interval from 1 July 2026.")
    return D

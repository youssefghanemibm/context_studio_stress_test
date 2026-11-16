"""VS011 Data Migration Waves (2026-09-21, Callum Fairbairn – IBM Data Migration Lead, final).

Claims migrated per wave (41,250 Denmark; 186,400 UK motor) appear only in the native bar chart
on slide 2 (exclusive; TX011 may repeat the Wave 1 count)."""
from __future__ import annotations

from generators.visuals import wave_dates as WD

from . import common as CM
from . import phrases as P
from . import raster as R
from .core import Deck


def build(W, out_dir):
    D = Deck(W, "VS011", version="2.0", doc_ref="SKR-MIG-004", out_dir=out_dir)
    d = D.date
    rng = D.rng
    waves = [W.waves[w] for w in ("MW-0", "MW-1", "MW-2")]

    # 1 title
    D.title_slide(D.title, "Wave results to date and the plan for Wave 2",
                  [f"Programme Skerry – data migration  |  Version {D.version}  |  {D.date_long()}",
                   f"Author: {D.author}, {D.author_title} (IBM Consulting)", "Status: Final"])

    # 2 claims migrated (chart only)
    s = D.content("Claims migrated by wave", "Results")
    D.need("WAVE:MW-1", "claims_migrated")
    done = [w for w in waves if w["claims_migrated"]]
    cats = [w["name"].replace(" – ", " ") for w in done]
    s.chart(0.5, 1.4, 8.0, 5.45, "column", cats, [("Claims migrated", [w["claims_migrated"] for w in done])],
            title="Claims migrated to Claims Hub by wave", legend=False, colors=["teal"], label_format="#,##0",
            number_format="#,##0")
    s.box(8.9, 1.6, 3.9, 3.4, [{"text": "Status", "bold": True, "size": 13},
                               {"text": "Wave 0 (Denmark) and Wave 1 (UK motor) are complete.", "size": 12},
                               {"text": "Wave 2 covers UK home, commercial and liability plus Norway and Sweden.", "size": 12}],
          style="tile", align="l", anchor="t", margins=0.15)
    s.notes(P.notes(rng, "how many claims have moved so far",
                    ["Counts are claims loaded into claim-core-svc and accepted by the business at each wave's sign-off."]))
    D.place("vs11_waves", s, "chart", "Claims migrated: Wave 1 UK motor=186400",
            notes="Second chart point; first point is 'Wave 0 Denmark=41250'. Numbers appear only in the chart cache.")
    D.place("vs11_waves", s, "chart", "Claims migrated: Wave 0 Denmark=41250",
            statement="Claims migrated: Wave 0 Denmark 41,250 (chart only).")

    # 3 agenda
    CM.agenda(D, ["Claims migrated by wave (slide 2)", "Wave plan", "Timeline and freeze windows", "Approach",
                  "Wave 2 scope", "Rehearsals", "Data domains", "Roles", "Lessons learned and next steps"],
              kicker="Data migration")

    # 4 wave plan
    s = D.content("Wave plan", "Plan")
    rows = []
    for w in waves:
        prods = ", ".join(W.products[p]["name"] for p in w["scope"].replace("All Danish products (", "").replace(")", "").split(", "))
        # a wave's cut-over date shows only once a decision has fixed it (MW-2: DEC-011, 2026-10-08)
        cut = D.date_long(w["date"]) if WD.date_known(W, w["id"], d) else "E" + WD.tbc_label(W, w["id"], short=True)[1:]
        rows.append((w["name"], cut, prods, w.get("rehearsals") or "to be baselined", w["status"].capitalize()))
    s.table(0.5, 1.45, 12.3, ["Wave", "Cut-over", "Products", "Rehearsals", "Status"], rows,
            col_w=[2.6, 1.8, 5.2, 1.3, 1.4], row_h=0.85, size=11, first_col_bold=True)
    w2_known = WD.date_known(W, "MW-2", d)
    w2_note = (f"Wave 2 is planned for {D.date_long(waves[2]['date'])}." if w2_known else
               "Wave 2 is planned for early 2027; the date is to be confirmed by the Steering Committee.")
    s.notes(P.notes(rng, "the three migration waves", [w2_note]))
    D.fact(s, "table", "Planned",
           f"Wave 2 (UK home, commercial, liability; Norway; Sweden) is planned for {waves[2]['date']}." if w2_known else
           f"On {d} Wave 2 (UK home, commercial, liability; Norway; Sweden) is planned for early 2027, date to be "
           f"confirmed by the Steering Committee.", world_ref="WAVE:MW-2#status")
    D.fact(s, "table", "Motor Private UK",
           "Wave 1 – UK motor (cut-over 2026-09-14) migrated product PRD-MOT-UK, Motor Private UK, after 3 rehearsals.",
           world_ref="WAVE:MW-1#scope")

    # 5 timeline (raster)
    s = D.content("Timeline and freeze windows", "Plan")
    png = R.timeline_image("Programme Skerry migration timeline", [
        ("3 Nov 2025", "Claims Hub MVP live (new FNOL only)", False),
        ("1 Jun 2026", "Wave 0 – Denmark cut-over", True),
        ("14 Sep 2026", "Wave 1 – UK motor; freeze 11 Sep 18:00 to 14 Sep 06:00", True),
        ("15 Feb 2027", "Wave 2 (planned); freeze 12 Feb 18:00 to 15 Feb 06:00", True) if w2_known else
        ("Early 2027", "Wave 2 (planned); date and freeze to be confirmed", True),
        ("30 Sep 2027", "CLARA decommissioning target", False)], height=950,
        sub="Freeze windows stop CLARA updates for the products in scope")
    w2_alt = ("Wave 2 planned 15 Feb 2027 with freeze 2027-02-12 18:00 to 2027-02-15 06:00" if w2_known else
              "Wave 2 planned for early 2027, date and freeze to be confirmed")
    s.picture_fit(png, 0.5, 1.35, 12.3, 5.55,
                  alt=f"Migration timeline: MVP 3 Nov 2025; Wave 0 Denmark 1 Jun 2026; Wave 1 UK motor 14 Sep 2026 with freeze 2026-09-11 18:00 to 2026-09-14 06:00; {w2_alt}; CLARA decommissioning target 30 Sep 2027.",
                  title="Migration timeline")
    s.notes(P.notes(rng, "the timeline and freeze windows", n_filler=1))
    if w2_known:
        D.fact(s, "image", "freeze 12 Feb 18:00 to 15 Feb 06:00",
               "Timeline image: Wave 2 freeze planned 12 Feb 2027 18:00 to 15 Feb 2027 06:00.", kind="image_text",
               world_ref="WAVE:MW-2#freeze")
    else:
        D.fact(s, "image", "date and freeze to be confirmed",
               f"Timeline image (as at {d}): Wave 2 is planned for early 2027; its date and freeze window are still to be "
               f"confirmed (fixed later by DEC-011).", kind="image_text", world_ref="DECISION:DEC-011")
    D.fact(s, "alt_text", "freeze 2026-09-11 18:00 to 2026-09-14 06:00",
           "Alt text: Wave 1 freeze 2026-09-11 18:00 to 2026-09-14 06:00.", kind="alt_text", world_ref="WAVE:MW-1#freeze")

    # 6 approach
    s = D.content("Migration approach", "Approach")
    items = []
    for a in ["ADR-001", "ADR-015", "ADR-016", "ADR-025"]:
        items.append({"runs": [(f"{a}  ", {"bold": True, "color": "teal"}), (W.adrs[a]["title"], {})]})
    s.bullets(0.6, 1.5, 7.8, 3.0, items, size=14)
    s.bullets(0.6, 4.3, 7.8, 2.4, ["Whole products move in a wave; CLARA keeps the rest until their wave.",
                                   "Each wave is rehearsed end to end on masked data before the live run.",
                                   "Business verification signs each wave off before CLARA access is closed."], size=12)
    s.box(8.8, 1.6, 4.0, 3.0, [{"text": P.pick(rng, P.TAKEAWAY_HEAD), "bold": True, "size": 13},
                               {"text": "Move by product and region, rehearse on masked data, keep Nordic amounts in both currencies.", "size": 12}],
          style="tile", align="l", anchor="t", margins=0.15)
    s.notes(P.notes(rng, "the migration approach", ["The strangler-fig approach was agreed at the programme kick-off on 13 January 2025 (DEC-001)."]))
    D.fact(s, "text", "Store Nordic amounts in original currency and GBP",
           "ADR-016: Nordic amounts are stored in the original currency and in GBP.", world_ref="ADR:ADR-016")
    D.fact(s, "notes", "agreed at the programme kick-off on 13 January 2025 (DEC-001)",
           "Speaker notes: the strangler-fig, wave-based migration was agreed at the kick-off on 2025-01-13 (DEC-001).",
           kind="speaker_notes", world_ref="DECISION:DEC-001")

    # 7 wave 2 scope
    s = D.content("Wave 2 scope", "Wave 2")
    rows = []
    for pid in waves[2]["scope"].split(", "):
        p = W.products[pid]
        rows.append((pid, p["name"], p["line"], p["region"], p["currency"], f"{p['policies_in_force']:,}"))
    s.table(0.5, 1.45, 12.3, ["Product", "Name", "Line", "Region", "Currency", "Policies in force"], rows,
            col_w=[1.6, 3.4, 2.2, 1.0, 1.2, 1.9], row_h=0.48, size=11, first_col_bold=True)
    s.notes(P.notes(rng, "what moves in Wave 2", ["Wave 2 is the first wave with Norwegian and Swedish products in a single cut-over."]))
    D.fact(s, "table", "Hem Sverige", "Wave 2 scope includes PRD-HOM-SE Hem Sverige (SEK).", world_ref="WAVE:MW-2#scope")
    D.fact(s, "table", "448,000", "Home Buildings & Contents UK (PRD-HOM-UK) has 448,000 policies in force.",
           world_ref="PRODUCT:PRD-HOM-UK#policies_in_force")

    # 8 rehearsals (chart)
    s = D.content("Rehearsals per completed wave", "Rehearsals")
    s.chart(0.5, 1.4, 6.8, 5.45, "column", ["Wave 0 Denmark", "Wave 1 UK motor"],
            [("Full rehearsals", [waves[0]["rehearsals"], waves[1]["rehearsals"]])],
            title="Full dress rehearsals before cut-over", legend=False, colors=["navy"])
    s.bullets(7.7, 1.6, 5.1, 4.5, ["Rehearsals use masked data (ADR-025).",
                                   "Each rehearsal runs the full runbook, including reconciliation.",
                                   "Wave 2 rehearsal dates will be baselined after the date is confirmed."], size=12)
    s.notes(P.notes(rng, "how many rehearsals each wave needed", n_filler=1))
    D.fact(s, "chart", "Full rehearsals: Wave 1 UK motor=3",
           "Wave 1 – UK motor had 3 full rehearsals; Wave 0 – Denmark had 2.", kind="chart_only",
           world_ref="WAVE:MW-1#rehearsals")

    # 9 data domains (cards)
    from .orgchart import team_cards
    s = D.content("Data domains and target services", "Data")
    cards = []
    for name in ["claim-core-svc", "reserve-engine", "recovery-svc", "fraud-referral-svc", "settlement-svc", "document-svc"]:
        sv = W.services[name]
        cards.append((name, [f"Target tables: {', '.join(sv['postgres_tables'])}", f"Squad: {W.team_name(W.service_owner(name, d)['team'], d)}"]))
    gn = team_cards(D, s, cards, prefix="Domain card", h=1.6)
    s.notes(P.notes(rng, "where migrated data lands", n_filler=1))
    D.fact(s, "group", "claim-core-svc Target tables: claim_core.claim, claim_core.party",
           "Migrated claim headers land in claim_core.claim and claim_core.party (claim-core-svc).", kind="visual_only",
           world_ref="SERVICE:claim-core-svc#postgres_tables", shape_name=gn["claim-core-svc"])

    # 10 roles
    s = D.content("Roles", "Team")
    people = [("P051", "Data migration strategy, waves and reserve reconciliation"),
              ("P048", "Programme plan and cut-over planning"),
              ("P052", "COBOL program analysis and CRUD matrix"),
              ("P025", "CLARA data dictionary and DB2 extracts"),
              ("P041", "reserve-engine load and parallel-run follow-up"),
              ("P017", "Business acceptance for Claims Hub")]
    rows = [(W.name_of(p, d), W.title_of(p, d), "IBM Consulting" if W.people[p].get("employer") == "ORG-IBM" else "Corvane Mutual", r)
            for p, r in people]
    s.table(0.5, 1.45, 12.3, ["Name", "Title", "Organisation", "Migration role"], rows, col_w=[2.0, 3.2, 1.8, 5.3],
            row_h=0.55, size=11, first_col_bold=True)
    s.notes(P.notes(rng, "who does what in the migration team",
                    ["Note the namesake: the IBM Data Migration Lead Callum Fairbairn is not the Corvane Motor Claims Team Leader of the same name in Leeds."]))
    D.fact(s, "table", "Data Migration Lead",
           "Callum Fairbairn (IBM Consulting) is the Data Migration Lead.", world_ref="PERSON:P051#titles")
    D.fact(s, "notes", "not the Corvane Motor Claims Team Leader of the same name in Leeds",
           "Speaker notes: the IBM Data Migration Lead Callum Fairbairn is a different person from the Corvane Motor Claims Team Leader Callum Fairbairn (Leeds).",
           kind="speaker_notes", world_ref="PERSON:P051#notes")

    # 11 lessons learned
    s = D.content("Lessons learned from Waves 0 and 1", "Lessons")
    s.bullets(0.6, 1.5, 7.8, 5.0, ["Freeze windows held; communicate them early to the contact centre.",
                                   "Rehearse interface switch-over as well as the data load.",
                                   "Keep reserve reconciliation on the critical path, not after go-live.",
                                   "Plan hypercare capacity per squad before the cut-over weekend.",
                                   "Nordic currency handling needs its own test pack for Wave 2."], size=13)
    s.notes(P.notes(rng, "what we learned", n_filler=2))

    # 12 next steps
    s = D.content("Next steps", "Next steps")
    s.table(0.5, 1.45, 12.3, ["Item", "Owner", "Target"], [
        ("Confirm Wave 2 date with the Steering Committee", W.name_of("P048", d), "October 2026 meeting"),
        ("Baseline Wave 2 rehearsal plan", W.name_of("P051", d), "After date confirmation"),
        ("Close Wave 1 hypercare", W.name_of("P048", d), "November 2026"),
        ("Nordic currency test pack", W.name_of("P051", d), "Before the first Wave 2 rehearsal")],
        col_w=[6.3, 2.5, 3.5], row_h=0.55, size=12)
    s.notes(P.notes(rng, "the next steps", n_filler=1))

    # 13 document control
    hist = CM.history_rows(D, [("1.0", "Wave plan baseline"), ("1.5", "Wave 0 results"), ("2.0", "Wave 1 results")],
                           spacing=(60, 110), kind="final")
    CM.doc_control(D, hist, [("P048", "Reviewed"), ("P017", "Reviewed")], status="Final",
                   reviewers=[W.name_of(x, d) for x in ("P049", "P041", "P025")],
                   distribution="Programme Skerry Steering Committee members, Claims Hub squads",
                   purpose="Results of the completed migration waves and the plan for Wave 2.",
                   approval_label="Decision")
    return D

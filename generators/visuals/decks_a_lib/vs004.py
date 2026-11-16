"""VS004 Claims Organisation Chart – March 2024 (2024-03-01, Ingrid Sørensen, approved; stale today).

Everything is stated as at 2024-03-01: Martin Calloway is the Recoveries Manager reporting to
Rob Tennant, SIU reports to the Claims Director, the fraud engine is still FRAUDNET and the CFO is
Gareth Whitcombe."""
from __future__ import annotations

from . import common as CM
from . import phrases as P
from .core import Deck
from .orgchart import box_text, org_slide, team_cards


def build(W, out_dir):
    D = Deck(W, "VS004", version="1.0", doc_ref="CLM-ORG-2024-03", out_dir=out_dir)
    d = D.date
    rng = D.rng
    loc = lambda pid: W.locations[W.location_of(pid, d)]["city"]  # noqa: E731

    # 1 title
    D.title_slide(D.title, "Claims Directorate structure, team leads and process owners",
                  [f"Effective {D.date_long()}  |  Version {D.version}",
                   f"Issued by: {D.author}, {D.author_title}", "Status: Approved"])

    # 2 contents
    CM.agenda(D, ["Where Claims sits in the Group", "Claims Directorate leadership", "Claims Operations UK",
                  "Recoveries", "Claims Operations Nordics", "Special Investigations Unit", "Specialist teams",
                  "Process owners", "Locations, forums and contacts"], title="Contents", kicker="Organisation chart")

    # 3 group context
    s, sh = org_slide(D, "Where Claims sits in the Group", "Group context", "P003",
                      ["P004", "P002", "P007", "P006"], notes_topic="the executive structure above Claims",
                      notes_facts=["The Claims Director reports to the Chief Operating Officer."])
    D.fact(s, "connector", f"{box_text(D, 'P003')} -> {box_text(D, 'P002')}",
           "March 2024 chart: Gareth Whitcombe, Chief Financial Officer, reports to the CEO Helena Strandberg.",
           kind="temporal", world_ref="PERSON:P002#titles")
    D.fact(s, "notes", "The Claims Director reports to the Chief Operating Officer.",
           "Speaker notes (2024): the Claims Director reports to the Chief Operating Officer.",
           kind="speaker_notes", world_ref="PERSON:P005#reports_to")

    # 4 Claims Directorate leadership
    s, sh = org_slide(D, "Claims Directorate – leadership team", "Claims Directorate", "P005",
                      ["P011", "P012", "P008", "P030"], above="P004",
                      notes_topic="the Claims Director's leadership team",
                      notes_facts=[f"{W.name_of('P008', d)} has led the SIU since 1 January 2020."])
    D.place("vs4_sorensen", s, "connector", f"{box_text(D, 'P005')} -> {box_text(D, 'P008')}",
            notes="Boxes read 'Ingrid Sørensen / Claims Director' and 'Niall Brannigan / Head of SIU'; the connector carries the reporting line.")
    D.fact(s, "text", "Ingrid Sørensen Claims Director",
           "March 2024 chart box: 'Ingrid Sørensen — Claims Director' (now Ingrid Ashby).",
           kind="alias_use", world_ref="PERSON:P005#name_history")
    D.fact(s, "connector", f"{box_text(D, 'P005')} -> {box_text(D, 'P012')}",
           "March 2024 chart: Mette Dahl, Head of Claims Operations Nordics, reports to the Claims Director.",
           kind="temporal", world_ref="PERSON:P012#reports_to")
    D.fact(s, "notes", "has led the SIU since 1 January 2020",
           "Speaker notes: Niall Brannigan has headed the SIU since 2020-01-01.", kind="speaker_notes",
           world_ref="PERSON:P008#titles")

    # 5 Claims Operations UK
    s, sh = org_slide(D, "Claims Operations UK", "Claims Directorate", "P011",
                      [("P015", ["P014"]), ("P022", ["P044"]), "P029", ("P033", ["P045"]), "P039"],
                      above="P005", notes_topic="the UK operations structure",
                      notes_facts=["Recoveries sits within Claims Operations UK and is run from the Bristol Recoveries Centre."])
    D.place("vs4_calloway", s, "connector", f"{box_text(D, 'P011')} -> {box_text(D, 'P015')}",
            notes="Stale (C02): Calloway left on 2024-12-31; Freya Lindahl owns the process from 2025-09-01.")
    D.place("vs4_calloway", s, "text", "Martin Calloway Recoveries Manager",
            statement="March 2024 chart box: 'Martin Calloway — Recoveries Manager' (stale: he left Corvane on 2024-12-31).")
    D.fact(s, "connector", f"{box_text(D, 'P015')} -> {box_text(D, 'P014')}",
           "March 2024 chart: Siobhan Quill, Recoveries Team Leader, reports to Martin Calloway.",
           kind="temporal", world_ref="PERSON:P014#reports_to")
    D.fact(s, "connector", f"{box_text(D, 'P011')} -> {box_text(D, 'P022')}",
           "Callum Fairbairn (Corvane, Motor Claims Team Leader, Leeds) reports to Rob Tennant.",
           kind="temporal", world_ref="PERSON:P022#reports_to")

    # 6 Recoveries team profile
    s = D.content("Recoveries – team profile", "Claims Directorate")
    sb_m = s.org(0.8, 1.6, 2.8, 0.95, *D.who("P015"), style="org_head")
    sb_q = s.org(0.8, 3.1, 2.8, 0.95, *D.who("P014"))
    from .orgchart import link
    link(s, sb_m, sb_q)
    prof = [
        ("Team", W.team_name("T08", d)),
        ("Purpose", W.teams["T08"]["purpose"]),
        ("Based at", W.locations["LOC-BRS"]["name"]),
        ("Manager", f"{W.name_of('P015', d)}, {W.title_of('P015', d)}"),
        ("Process owned", f"Stage S7 – {W.stages['S7']['name']}"),
        ("Systems", f"{W.system_name('SYS01', d)}, {W.system_name('SYS24', d)} (SUBTRAK)"),
        ("Panel partners", "Quarryhill Solicitors LLP (litigation); Salvanta Salvage Ltd (salvage)"),
    ]
    s.table(4.3, 1.6, 8.5, ["Item", "Detail"], prof, col_w=[1.8, 6.7], row_h=0.48, size=11, first_col_bold=True)
    s.notes(P.notes(rng, "the Recoveries team", ["Martin Calloway is the accountable owner of the recovery and subrogation process."]))
    D.fact(s, "table", "Stage S7 – Recovery & Subrogation",
           "March 2024 team profile: the Recoveries team under Martin Calloway owns stage S7 Recovery & Subrogation (stale).",
           kind="contradiction_old", world_ref="PROCESS:S7#owner_history",
           extra={"contradictions": ["C02"]})
    D.fact(s, "notes", "Martin Calloway is the accountable owner of the recovery and subrogation process",
           "Speaker notes (2024, stale): Martin Calloway is the accountable owner of the recovery and subrogation process.",
           kind="contradiction_old", world_ref="PROCESS:S7#owner_history", extra={"contradictions": ["C02"]})

    # 7 Claims Operations Nordics
    s, sh = org_slide(D, "Claims Operations Nordics", "Claims Directorate", "P012",
                      ["P013", ("P034", ["P046"])], above="P005",
                      notes_topic="the Nordic claims structure",
                      notes_facts=["Nordic Claims Assessors are known locally as skadetakstmenn."])
    D.fact(s, "connector", f"{box_text(D, 'P012')} -> {box_text(D, 'P013')}",
           "March 2024 chart: Freya Lindahl is Senior Recoveries Manager – Nordics, reporting to Mette Dahl.",
           kind="temporal", world_ref="PERSON:P013#titles")

    # 8 SIU
    snt = W.system_name("SYS03", d)
    s, sh = org_slide(D, f"{W.team_name('T11', d)}", "Claims Directorate", "P008", ["P027", "P028"], above="P005",
                      notes_topic="the SIU",
                      notes_facts=[f"{W.name_of('P027', d)} owns the {snt} scoring model and threshold calibration.",
                                   f"{W.name_of('P028', d)} approves surveillance by Greyfold Investigations."])
    D.fact(s, "notes", f"owns the {snt} scoring model",
           "Speaker notes (2024): Oskar Lindgren owns the FRAUDNET scoring model (FRAUDNET was renamed Sentinel on 2025-03-01).",
           kind="alias_use", world_ref="SYSTEM:SYS03#renames")

    # 9 specialist teams (nested group cards)
    s = D.content("Specialist teams", "Claims Directorate")
    cards = []
    for tid in ["T09", "T06", "T10", "T03", "T04", "T07"]:
        lead = W.team_lead(tid, d)
        cards.append((W.team_name(tid, d), [f"Lead: {W.name_of(lead, d)} ({W.title_of(lead, d)})",
                                            f"Location: {loc(lead)}", W.teams[tid]["purpose"]]))
    gnames = team_cards(D, s, cards)
    s.notes(P.notes(rng, "the specialist teams in the directorate", n_filler=1))
    mcl = W.team_name("T09", d)
    D.fact(s, "group", f"{mcl} Lead: {W.name_of('P030', d)}",
           "Major & Complex Loss is led by Kirsty Mowbray (London) and handles Tier-3 claims.",
           kind="visual_only", world_ref="TEAM:T09#lead_history", shape_name=gnames[mcl])

    # 10 process owners
    s = D.content("Process owners", "Accountability")
    rows = []
    for sid in ["S1", "S2", "S3", "S4", "S5", "S6", "S7"]:
        own = W.owner_of_process(sid, d)
        rows.append((sid, W.stages[sid]["name"], W.name_of(own, d), W.title_of(own, d)))
    s.table(0.5, 1.45, 8.4, ["Stage", "Process", "Owner", "Title"], rows, col_w=[0.7, 2.4, 2.2, 3.1],
            row_h=0.5, size=11, first_col_bold=True)
    s.box(9.3, 1.5, 3.5, 2.4, [{"text": "Note", "bold": True, "size": 12},
                               {"text": "Reserving is owned in Finance by the Chief Actuary; all other stages sit in the Claims Directorate.", "size": 11}],
          style="tile", align="l", anchor="t", margins=0.15)
    s.notes(P.notes(rng, "who is accountable for each stage"))
    D.fact(s, "table", "Martin Calloway",
           "March 2024 process owners: S7 Recovery & Subrogation is owned by Martin Calloway (stale).",
           kind="contradiction_old", world_ref="PROCESS:S7#owner_history", extra={"contradictions": ["C02"]})
    D.fact(s, "table", "Ewan Strachan",
           "March 2024 process owners: S1 First Notice of Loss is owned by Ewan Strachan, Contact Centre Manager.",
           kind="temporal", world_ref="PROCESS:S1#owner_history")
    D.fact(s, "table", "Sebastian Moreau-Clarke",
           "March 2024 process owners: S4 Reserving is owned by Sebastian Moreau-Clarke, Chief Actuary.",
           kind="temporal", world_ref="PROCESS:S4#owner_history")

    # 11 locations
    s = D.content("Teams by location", "Locations")
    rows = []
    for tid in ["T02", "T03", "T04", "T05", "T06", "T07", "T08", "T09", "T10", "T11"]:
        lead = W.team_lead(tid, d)
        rows.append((W.team_name(tid, d), W.name_of(lead, d), loc(lead)))
    s.table(0.5, 1.45, 8.0, ["Team", "Lead", "Lead based in"], rows, col_w=[3.4, 2.6, 2.0], row_h=0.42, size=11)
    s.notes(P.notes(rng, "where the teams are based", n_filler=1))

    # 12 forums
    s = D.content("Claims forums", "Governance")
    com1, com2 = W.committees["COM-01"], W.committees["COM-02"]
    ch1 = [c for c in com1["chair_history"] if (c["from"] or "") <= d <= (c["to"] or "9999")][0]["person"]
    ch2 = [c for c in com2["chair_history"] if (c["from"] or "") <= d <= (c["to"] or "9999")][0]["person"]
    rows = [(com1["name"], W.name_of(ch1, d), "Per terms of reference", com1["remit"]),
            (com2["name"], W.name_of(ch2, d), com2["cadence"], com2["remit"])]
    D.need("COMMITTEE:COM-02", "cadence")
    s.table(0.5, 1.45, 12.3, ["Forum", "Chair", "Cadence", "Remit"], rows, col_w=[2.3, 2.2, 2.6, 5.2], row_h=0.7, size=11)
    s.notes(P.notes(rng, "the forums Claims attends"))
    D.fact(s, "table", W.name_of(ch1, d),
           "March 2024: the Reserving Committee is chaired by Sebastian Moreau-Clarke.", kind="temporal",
           world_ref="COMMITTEE:COM-01#chair_history")
    D.fact(s, "table", "fortnightly, Thursday 14:00 UK time",
           "The Claims Fraud Forum meets fortnightly on Thursdays at 14:00 UK time, chaired by Niall Brannigan.",
           world_ref="COMMITTEE:COM-02#cadence")

    # 13 contacts
    CM.contacts(D, [("P005", "Claims Director"), ("P011", "UK operations"), ("P012", "Nordic operations"),
                    ("P008", "SIU"), ("P015", "Recoveries"), ("P030", "Major & complex loss")], title="Key contacts")
    D.fact(D.slides[-1], "table", "ingrid.sorensen@corvane-mutual.example",
           "March 2024 contact list: Ingrid Sørensen's email is ingrid.sorensen@corvane-mutual.example.",
           kind="alias_use", world_ref="PERSON:P005#email_history")

    # 14 document control
    hist = CM.history_rows(D, [("0.1", ""), ("0.2", ""), ("1.0", "")], spacing=(7, 20), kind="stale")
    CM.doc_control(D, hist, [("P004", "Approved")], status="Approved", owner_pid="P005",
                   distribution="All Claims Directorate staff; HR Business Partner",
                   purpose="Structure of the Claims Directorate as at 1 March 2024.")
    return D

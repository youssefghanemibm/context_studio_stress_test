"""VS005 Claims, Risk and Finance Organisation Chart – October 2025 (2025-10-06, Ingrid Ashby, approved).

Reflects the 2025-09-01 re-organisation: Freya Lindahl heads Recoveries & Subrogation under the
Claims Director, Counter-Fraud & SIU reports to the CRO, Reserving reports to the CFO."""
from __future__ import annotations

from generators.visuals import org_chart_control as OC

from . import common as CM
from . import phrases as P
from .core import Deck
from .orgchart import box_text, link, org_slide, team_cards


def build(W, out_dir):
    oc = OC.control(W, "VS005")   # shared with VS044 (the pdf rendition of the same chart)
    D = Deck(W, "VS005", version=oc["version"], doc_ref=oc["doc_ref"], out_dir=out_dir)
    d = D.date
    rng = D.rng
    loc = lambda pid: W.locations[W.location_of(pid, d)]["city"]  # noqa: E731

    # 1 title
    D.title_slide(D.title, "Structure after the 1 September 2025 re-organisation",
                  [f"Effective {D.date_long()}  |  Version {D.version}",
                   f"Issued by: {D.author}, {D.author_title}", "Status: Approved"])

    # 2 contents
    CM.agenda(D, ["What changed on 1 September 2025", "Executive structure", "Claims Directorate",
                  "Claims Operations (Group)", "Recoveries & Subrogation (Group)", "Risk & Compliance",
                  "Finance", "Specialist teams", "Process owners, forums and contacts"],
              title="Contents", kicker="Organisation chart")

    # 3 what changed (titles only; reporting lines are on the charts)
    s = D.content("What changed on 1 September 2025", "Re-organisation")
    rows = []
    for pid in ["P008", "P009", "P011", "P012", "P013", "P014", "P016", "P017"]:
        ts = W.people[pid]["titles"]
        old = [t for t in ts if t.get("to") == "2025-08-31"]
        new = W.title_of(pid, d)
        rows.append((W.name_of(pid, d), old[0]["title"] if old else "–", new))
    s.table(0.5, 1.45, 8.3, ["Name", "Title until 31 Aug 2025", "Title from 1 Sep 2025"], rows,
            col_w=[2.0, 3.2, 3.1], row_h=0.42, size=10, first_col_bold=True)
    s.bullets(9.1, 1.5, 3.8, 5.0, [
        {"text": "Team changes", "bold": True},
        f"Special Investigations Unit renamed {W.team_name('T11', d)} and moved to Risk & Compliance.",
        f"Recoveries became {W.team_name('T08', d)}.",
        f"Claims Operations UK became {W.team_name('T02', d)}.",
        "Claims Hub Product moved from Technology into Claims.",
    ], size=11)
    s.notes(P.notes(rng, "what the re-organisation changed",
                    ["Reporting lines are shown on the following charts rather than in this table."]))
    D.fact(s, "table", "Senior Recoveries Manager – Nordics",
           "Freya Lindahl was Senior Recoveries Manager – Nordics until 2025-08-31 and Head of Recoveries & Subrogation from 2025-09-01.",
           kind="temporal", world_ref="PERSON:P013#titles")
    D.fact(s, "table", "Acting Recoveries Manager",
           "Siobhan Quill was Acting Recoveries Manager until 2025-08-31 and is Recoveries Team Leader – UK from 2025-09-01.",
           kind="temporal", world_ref="PERSON:P014#titles")
    D.fact(s, "text", "moved to Risk & Compliance",
           "From 2025-09-01 the Special Investigations Unit was renamed Counter-Fraud & SIU and moved to Risk & Compliance.",
           world_ref="TEAM:T11#department_history")

    # 4 executive
    s, sh = org_slide(D, "Executive structure", "Group context", "P003", ["P004", "P001", "P007", "P006"],
                      notes_topic="the executive team",
                      notes_facts=["Priya Raman has been Chief Financial Officer since 1 July 2025."])
    D.fact(s, "connector", f"{box_text(D, 'P003')} -> {box_text(D, 'P001')}",
           "October 2025 chart: Priya Raman, Chief Financial Officer, reports to the CEO Helena Strandberg.",
           kind="visual_only", world_ref="PERSON:P001#reports_to")
    D.fact(s, "notes", "Priya Raman has been Chief Financial Officer since 1 July 2025",
           "Speaker notes: Priya Raman has been CFO since 2025-07-01.", kind="speaker_notes",
           world_ref="PERSON:P001#titles")

    # 5 Claims Directorate
    s, sh = org_slide(D, "Claims Directorate", "Claims", "P005", ["P011", "P013", "P030", "P017"], above="P004",
                      notes_topic="the Claims Director's direct reports",
                      notes_facts=["Recoveries & Subrogation is now a Group function covering the UK and the Nordics."])
    D.place("vs5_freya", s, "connector", f"{box_text(D, 'P005')} -> {box_text(D, 'P013')}",
            notes="Reporting line carried by the connector from the Claims Director box.")
    D.place("vs5_freya", s, "text", "Freya Lindahl Head of Recoveries & Subrogation",
            statement="October 2025 chart box: 'Freya Lindahl — Head of Recoveries & Subrogation'.")
    D.fact(s, "text", "Ingrid Ashby Claims Director",
           "October 2025 chart box: 'Ingrid Ashby — Claims Director' (formerly Ingrid Sørensen).",
           kind="alias_use", world_ref="PERSON:P005#name_history")
    D.fact(s, "connector", f"{box_text(D, 'P005')} -> {box_text(D, 'P017')}",
           "October 2025 chart: Aisha Siddiqui, Head of Claims Hub Product, reports to the Claims Director.",
           kind="visual_only", world_ref="PERSON:P017#reports_to")

    # 6 Claims Operations (Group)
    s, sh = org_slide(D, W.team_name("T02", d), "Claims", "P011",
                      [("P012", ["P034"]), ("P022", ["P044"]), "P029", ("P033", ["P045"]), "P039"], above="P005",
                      notes_topic="the group claims operations structure",
                      notes_facts=["Rob Tennant also became the owner of the FNOL process on 1 September 2025."])
    D.fact(s, "connector", f"{box_text(D, 'P011')} -> {box_text(D, 'P012')}",
           "October 2025 chart: Mette Dahl, Claims Operations Lead – Nordics, reports to Rob Tennant.",
           kind="visual_only", world_ref="PERSON:P012#reports_to")
    D.fact(s, "notes", "owner of the FNOL process on 1 September 2025",
           "Speaker notes: Rob Tennant became FNOL process owner on 2025-09-01.", kind="speaker_notes",
           world_ref="PROCESS:S1#owner_history")

    # 7 Recoveries & Subrogation (Group)
    s = D.content(W.team_name("T08", d), "Claims")
    top = s.org(5.35, 1.4, 2.6, 0.9, *D.who("P005"), style="org_vacant", size=10)
    fb = s.org(5.25, 2.65, 2.8, 0.9, *D.who("P013"), style="org_head")
    sq = s.org(5.35, 3.9, 2.6, 0.9, *D.who("P014"))
    link(s, top, fb)
    link(s, fb, sq)
    prof = [("Based at", f"{loc('P013')} (head of function); {W.locations['LOC-BRS']['name']} (UK team)"),
            ("Process owned", f"Stage S7 – {W.stages['S7']['name']}, from 1 September 2025"),
            ("Systems", f"{W.system_name('SYS01', d)}, Subrogation Tracker (SUBTRAK)")]
    s.table(0.5, 5.1, 12.3, ["Item", "Detail"], prof, col_w=[2.0, 10.3], row_h=0.42, size=11, first_col_bold=True)
    s.notes(P.notes(rng, "the new Group recoveries function",
                    ["The handover from the acting arrangement was agreed at the ownership meeting on 3 September 2025."]))
    D.place("vs5_siobhan", s, "connector", f"{box_text(D, 'P013')} -> {box_text(D, 'P014')}")
    D.fact(s, "connector", f"{box_text(D, 'P005')} -> {box_text(D, 'P013')}",
           "Recoveries & Subrogation page repeats the reporting line Freya Lindahl → Claims Director.",
           kind="visual_only", world_ref="PERSON:P013#reports_to")
    D.fact(s, "table", "from 1 September 2025",
           "Freya Lindahl owns stage S7 Recovery & Subrogation from 2025-09-01.", kind="contradiction_new",
           world_ref="PROCESS:S7#owner_history", extra={"contradictions": ["C02"]})
    D.fact(s, "notes", "ownership meeting on 3 September 2025",
           "Speaker notes: the subrogation ownership handover was agreed at the meeting on 2025-09-03 (MTG-004).",
           kind="speaker_notes", world_ref="MEETING:MTG-004")

    # 8 Risk & Compliance
    s, sh = org_slide(D, "Risk & Compliance", "Risk", "P007", [("P008", ["P027", "P028"]), "P037", "P019"],
                      above="P003", kid_w=1.9, notes_topic="the Risk & Compliance structure",
                      notes_facts=["Counter-Fraud & SIU keeps its Leeds base after the move."])
    D.place("vs5_niall", s, "connector", f"{box_text(D, 'P007')} -> {box_text(D, 'P008')}")
    D.fact(s, "connector", f"{box_text(D, 'P008')} -> {box_text(D, 'P028')}",
           "Rachel Dunmore, SIU Investigations Manager (UK), reports to Niall Brannigan.", kind="visual_only",
           world_ref="PERSON:P028#reports_to")

    # 9 Finance
    s, sh = org_slide(D, "Finance", "Finance", "P001", ["P009", "P010", ("P021", ["P020", "P035"]), "P038"],
                      above="P003", kid_w=1.9, notes_topic="the Finance structure",
                      notes_facts=["Reserving now reports directly to the CFO rather than through the Chief Actuary."])
    D.fact(s, "connector", f"{box_text(D, 'P001')} -> {box_text(D, 'P009')}",
           "October 2025 chart: Lena Kristiansen, Head of Reserving, reports to the CFO Priya Raman.",
           kind="visual_only", world_ref="PERSON:P009#reports_to")
    D.fact(s, "connector", f"{box_text(D, 'P021')} -> {box_text(D, 'P020')}",
           "Bjørn Aasheim, Regulatory Reporting Manager, reports to Hamish Gilchrist.", kind="visual_only",
           world_ref="PERSON:P020#reports_to")

    # 10 specialist teams
    s = D.content("Specialist teams", "Claims")
    cards = []
    for tid in ["T09", "T06", "T10", "T03", "T05", "T21"]:
        lead = W.team_lead(tid, d)
        cards.append((W.team_name(tid, d), [f"Lead: {W.name_of(lead, d)} ({W.title_of(lead, d)})",
                                            f"Location: {loc(lead)}", W.teams[tid]["purpose"]]))
    gnames = team_cards(D, s, cards)
    s.notes(P.notes(rng, "the specialist teams", n_filler=1))
    D.fact(s, "group", f"Claims Hub Product Lead: {W.name_of('P017', d)}",
           "Claims Hub Product team card: lead Aisha Siddiqui (Head of Claims Hub Product), London.",
           kind="visual_only", world_ref="TEAM:T21#lead_history", shape_name=gnames["Claims Hub Product"])

    # 11 process owners
    s = D.content("Process owners", "Accountability")
    rows = []
    for sid in ["S1", "S2", "S3", "S4", "S5", "S6", "S7"]:
        own = W.owner_of_process(sid, d)
        rows.append((sid, W.stages[sid]["name"], W.name_of(own, d), W.title_of(own, d)))
    s.table(0.5, 1.45, 8.4, ["Stage", "Process", "Owner", "Title"], rows, col_w=[0.7, 2.4, 2.2, 3.1],
            row_h=0.5, size=11, first_col_bold=True)
    s.box(9.3, 1.5, 3.5, 2.6, [{"text": "Changes from 1 September 2025", "bold": True, "size": 12},
                               {"text": "FNOL moved to the Head of Claims Operations (Group); Reserving moved to the Head of Reserving; Recovery & Subrogation moved to the new Group head.", "size": 11}],
          style="tile", align="l", anchor="t", margins=0.15)
    s.notes(P.notes(rng, "process ownership after the re-organisation"))
    D.fact(s, "table", "Freya Lindahl",
           "October 2025 process owners: S7 Recovery & Subrogation – Freya Lindahl, Head of Recoveries & Subrogation.",
           kind="contradiction_new", world_ref="PROCESS:S7#owner_history", extra={"contradictions": ["C02"]})
    D.fact(s, "table", "Lena Kristiansen",
           "October 2025 process owners: S4 Reserving – Lena Kristiansen, Head of Reserving.", kind="temporal",
           world_ref="PROCESS:S4#owner_history")

    # 12 forums
    s = D.content("Forums and committees", "Governance")
    rows = []
    for cid in ["COM-01", "COM-02", "COM-03"]:
        c = W.committees[cid]
        ch = [x for x in c["chair_history"] if (x["from"] or "") <= d <= (x["to"] or "9999")][0]["person"]
        cad = c["cadence"] if D.ok(f"COMMITTEE:{cid}", "cadence") else "Per terms of reference"
        rows.append((c["name"], W.name_of(ch, d), cad, CM.asof_systems(W, c["remit"], d)))
    s.table(0.5, 1.45, 12.3, ["Forum", "Chair", "Cadence", "Remit"], rows, col_w=[2.6, 2.0, 2.6, 5.1], row_h=0.7, size=11)
    s.notes(P.notes(rng, "the forums and their chairs"))
    D.fact(s, "table", "Programme Skerry Steering Committee",
           "The Programme Skerry Steering Committee is chaired by Duncan Ferrier and meets monthly on the second Thursday at 14:00.",
           world_ref="COMMITTEE:COM-03#cadence")

    # 13 contacts
    CM.contacts(D, [("P005", "Claims Director"), ("P013", "Recoveries & Subrogation"), ("P011", "Claims operations"),
                    ("P007", "Risk & Compliance"), ("P008", "Counter-Fraud & SIU"), ("P001", "Finance"),
                    ("P009", "Reserving")], title="Key contacts")
    D.fact(D.slides[-1], "table", "ingrid.ashby@corvane-mutual.example",
           "October 2025 contacts: the Claims Director's email is ingrid.ashby@corvane-mutual.example.",
           kind="alias_use", world_ref="PERSON:P005#email_history")

    # 14 document control
    hist = list(oc["history"])
    hist[0] = (*hist[0], W.name_of("P005", hist[0][1]))
    CM.doc_control(D, hist, [("P004", "Approved"), ("P007", "Approved"), ("P001", "Approved")], status="Approved",
                   owner_pid="P005", distribution="Claims, Risk & Compliance and Finance staff; HR Business Partners",
                   purpose="Structure of Claims, Risk & Compliance and Finance after the September 2025 re-organisation.")
    return D

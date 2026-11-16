"""VS009 Recovery & Subrogation Process (2025-10-13, Freya Lindahl, approved).

Write-off authority shows only by lane position (the '> £10,000' approval sits in the 'Head of
Recoveries & Subrogation' lane) and the solicitor rule only in the connector from the decision
'Recoverable ≥ £25,000 or defended' to 'Instruct Quarryhill Solicitors'."""
from __future__ import annotations

from . import common as CM
from . import phrases as P
from . import raster as R
from .core import Deck
from .lanes import swimlane


def build(W, out_dir):
    D = Deck(W, "VS009", version="3.0", doc_ref="REC-PRC-002", out_dir=out_dir)
    d = D.date
    rng = D.rng

    # 1 title
    D.title_slide(D.title, "Group process for subrogation, salvage and third-party recoveries",
                  [f"Recoveries & Subrogation (Group)  |  Version {D.version}  |  {D.date_long()}",
                   f"Process owner: {D.author}, {D.author_title}", "Status: Approved"])

    # 2 swimlane (grouped)
    s = D.content("Recovery & Subrogation – end-to-end", "Process map")
    head = W.title_of("P013", d)
    L = swimlane(s, ["Claims Assessor / claim handler", "Recoveries team", "Recoveries Team Leader", head],
                 heights=[0.9, 1.95, 0.95, 0.95], grouped=True)
    f1 = L[0].step(2.35, "Flag recovery potential", w=1.5, size=9)
    o1 = L[1].step(4.05, "Open subrogation case and demand", w=1.6, size=9, row=0, rows=2)
    q1 = L[1].step(6.0, "Recoverable ≥ £1,000?", w=1.75, h=0.85, size=9, style="decision", row=0, rows=2)
    q2 = L[1].step(8.1, "Recoverable ≥ £25,000 or defended", w=2.0, h=0.92, size=9, style="decision", row=0, rows=2)
    sol = L[1].step(10.6, "Instruct Quarryhill Solicitors", w=1.9, size=9, row=0, rows=2)
    dem = L[1].step(10.6, "Pursue demand directly", w=1.9, size=9, row=1, rows=2)
    cls = L[1].step(6.0, "Close or write off", w=1.75, size=9, row=1, rows=2)
    w1 = L[2].step(4.4, "Approve write-off ≤ £10,000", w=1.9, size=9)
    w2 = L[3].step(7.4, "Approve write-off > £10,000", w=1.9, size=9)
    s.connect(f1, o1, a_site="r", b_site="t")
    s.connect(o1, q1)
    s.connect(q1, q2, label="Yes", name="rec-yes-1000", label_size=9)
    s.connect(q1, cls, a_site="b", b_site="t", label="No", name="rec-no-1000", label_size=9)
    s.connect(q2, sol, a_site="r", b_site="l", label="Yes", name="rec-solicitor", label_size=9)
    s.connect(q2, dem, a_site="b", b_site="l", label="No", name="rec-direct", label_size=9)
    s.connect(cls, w1, a_site="b", b_site="t")
    s.connect(cls, w2, a_site="b", b_site="t")
    s.notes(P.notes(rng, "the end-to-end recovery process",
                    ["Unanswered demands are chased at 28 days (BR-REC-012).",
                     "Claims covered by a knock-for-knock arrangement are not pursued (BR-REC-013)."]))
    D.place("vs9_lane_wo", s, "group", "Approve write-off > £10,000", shape_name=L[3].group_name,
            notes=f"Lane membership via group 'Lane: {head}'; " + L[3].geometry_note(w2))
    D.place("vs9_solicitor", s, "connector", "Recoverable ≥ £25,000 or defended -> Instruct Quarryhill Solicitors",
            notes="Connector labelled 'Yes' (label box 'label:rec-solicitor').")
    D.fact(s, "group", "Approve write-off ≤ £10,000",
           "'Approve write-off ≤ £10,000' sits in the 'Recoveries Team Leader' lane (BR-REC-011 v2).", kind="lane_only",
           world_ref="PROCESS:PS-REC-06#decision", shape_name=L[2].group_name,
           notes="group-geometry: " + L[2].geometry_note(w1))
    D.fact(s, "connector", "Recoverable ≥ £1,000? -> Close or write off [label: No]",
           "Recoveries below £1,000 are not pursued: the 'No' branch goes to 'Close or write off' (BR-REC-003 v3).",
           kind="arrow_only", world_ref="RULE:BR-REC-003@v3")
    D.fact(s, "notes", "chased at 28 days (BR-REC-012)",
           "Speaker notes: unanswered subrogation demands are chased at 28 days (BR-REC-012).", kind="speaker_notes",
           world_ref="RULE:BR-REC-012@v1")

    # 3 contents
    CM.agenda(D, ["End-to-end map (slide 2)", "Ownership", "Stages", "Thresholds and time limits", "Nordic regress",
                  "Salvage", "Claims Hub design", "Interfaces", "Measures, accountability and contacts"],
              title="Contents", kicker="Recovery & Subrogation")

    # 4 ownership
    s = D.content("Process ownership", "Ownership")
    hist = W.stages["S7"]["owner_history"]
    rows = []
    for h in hist:
        t = W.title_of(h["person"], h["to"] or d)
        rows.append((W.name_of(h["person"], d), t, D.date_long(h["from"]), D.date_long(h["to"]) if h["to"] else "current"))
    s.table(0.5, 1.45, 8.2, ["Owner", "Title while owner", "From", "To"], rows, col_w=[2.0, 3.2, 1.6, 1.4],
            row_h=0.5, size=11, first_col_bold=True)
    s.bullets(0.6, 3.7, 8.0, 2.8, [
        "Ownership handover agreed on 3 September 2025 (DEC-004).",
        f"{W.name_of('P014', d)} leads the UK recoveries team in Bristol.",
        "SUBTRAK retirement target set to 31 December 2026.",
    ], size=13)
    s.box(9.1, 1.5, 3.7, 2.4, [{"text": "Scope", "bold": True, "size": 13},
                               {"text": "UK and Nordic recoveries, salvage and subrogation litigation.", "size": 12}],
          style="tile", align="l", anchor="t", margins=0.15)
    s.notes(P.notes(rng, "who owns the process and how ownership changed"))
    D.fact(s, "table", "Martin Calloway",
           "Recovery & Subrogation process owners: Martin Calloway (Recoveries Manager) until 2024-12-31; Siobhan Quill (acting) 2025-01-01 to 2025-08-31; Freya Lindahl from 2025-09-01.",
           kind="temporal", world_ref="PROCESS:S7#owner_history")
    D.fact(s, "text", "SUBTRAK retirement target set to 31 December 2026",
           "DEC-004 set the SUBTRAK retirement target to 2026-12-31.", world_ref="DECISION:DEC-004")

    # 5 stages (chevrons, grouped)
    s = D.content("Recovery stages", "Stages")
    g = s.group("Recovery stages")
    ids = W.stages["S7"]["steps"]
    for i, sid in enumerate(ids):
        g.box(0.5 + i * 2.07, 1.9, 2.15, 1.0, W.steps[sid]["name"], style="chevron" if i else "pentagon", size=10,
              bold=True)
        g.text(0.6 + i * 2.07, 3.05, 1.95, 1.6, [{"text": W.steps[sid]["sla"]["text"], "size": 10}], size=10, color="slate")
    s.notes(P.notes(rng, "the six stages of a recovery", n_filler=1))
    D.fact(s, "group", "Open subrogation case and demand",
           "The Recovery & Subrogation stage has six steps, from 'Identify recovery potential' to 'Write-off approval'.",
           kind="visual_only", world_ref="PROCESS:S7#steps", shape_name="Recovery stages")

    # 6 thresholds and time limits (image table)
    s = D.content("Thresholds and time limits", "Rules")
    rules = [("BR-REC-001", "Open a subrogation case within 10 business days of the recovery flag"),
             ("BR-REC-003 v3", "Pursue where the recoverable amount is £1,000 or more (NOK 13,000 / SEK 13,500 / DKK 8,600)"),
             ("BR-REC-004", "Refund the customer's excess within 10 business days of a full recovery"),
             ("BR-REC-006", "Use a tracing agent when an uninsured third party has not responded after 60 days"),
             ("BR-REC-007", "Release total-loss vehicles to Salvanta Salvage within 5 business days"),
             ("BR-REC-009", "Limitation diary at 30 months (bodily injury) and 66 months (property)"),
             ("BR-REC-012", "Chase unanswered demands at 28 days"),
             ("BR-REC-015 v2", "Post salvage proceeds within 3 business days of receipt")]
    for rid in ["BR-REC-001", "BR-REC-003@v3", "BR-REC-004", "BR-REC-006", "BR-REC-007", "BR-REC-009", "BR-REC-012", "BR-REC-015@v2"]:
        D.need(f"RULE:{rid}", "text")
    png = R.table_image(["Rule", "Requirement"], rules, [2.2, 8.0], size=26, title="Recovery rules in force (October 2025)")
    s.picture_fit(png, 0.6, 1.35, 12.1, 5.55,
                  alt="Table of recovery rules: pursuit threshold £1,000 (BR-REC-003 v3), case opened within 10 business days, demands chased at 28 days, limitation diary 30/66 months.",
                  title="Recovery rules")
    s.notes(P.notes(rng, "the thresholds and time limits",
                    ["The pursuit threshold rose to £1,000 on 1 September 2025."]))
    D.fact(s, "image", "£1,000 or more (NOK 13,000 / SEK 13,500 / DKK 8,600)",
           "Image table: pursue subrogation where the recoverable amount is £1,000 or more (NOK 13,000 / SEK 13,500 / DKK 8,600), BR-REC-003 v3.",
           kind="image_table", world_ref="RULE:BR-REC-003@v3", extra={"contradictions": ["C13"]})
    D.fact(s, "image", "66 months (property)",
           "Image table: limitation diary at 30 months (bodily injury) and 66 months (property), BR-REC-009.",
           kind="image_table", world_ref="RULE:BR-REC-009@v1")
    D.fact(s, "notes", "The pursuit threshold rose to £1,000 on 1 September 2025.",
           "Speaker notes: the subrogation pursuit threshold rose to £1,000 on 2025-09-01.", kind="speaker_notes",
           world_ref="RULE:BR-REC-003@v3", extra={"contradictions": ["C13"]})

    # 7 Nordic regress and exclusions
    s = D.content("Nordic regress and exclusions", "Rules")
    s.bullets(0.6, 1.5, 7.8, 5.0, [
        "Nordic recoveries follow the regress process with the counterparty insurer (BR-REC-008).",
        "Nordic demands are issued in the counterparty's national language (BR-REC-017).",
        "Claims under a knock-for-knock arrangement are not pursued (BR-REC-013).",
        "Escape of water from a neighbouring property is pursued against the neighbour's insurer (BR-REC-016).",
        "Collision claims with a third party at fault are pursued for the full outlay including excess (BR-REC-002).",
    ], size=13)
    s.box(8.8, 1.6, 4.0, 2.6, [{"text": "Terminology", "bold": True, "size": 13},
                               {"text": "'Regress' (regressfordring) is the Nordic term for a subrogated recovery.", "size": 12}],
          style="tile", align="l", anchor="t", margins=0.15)
    s.notes(P.notes(rng, "how Nordic recoveries differ", n_filler=1))
    D.fact(s, "text", "issued in the counterparty's national language",
           "Nordic recovery demands are issued in the counterparty's national language (BR-REC-017).",
           world_ref="RULE:BR-REC-017@v1")

    # 8 salvage (grouped)
    s = D.content("Salvage categories", "Salvage")
    g = s.group("Salvage categories")
    for i, (cat, fate) in enumerate([("A", "Scrapped"), ("B", "Scrapped"), ("S", "May be sold for repair"), ("N", "May be sold for repair")]):
        sub = g.group(f"Category {cat}")
        sub.box(0.8 + i * 3.05, 1.8, 2.7, 1.2, f"Category {cat}", style="terminal", size=20, bold=True,
                fill="red" if fate == "Scrapped" else "teal")
        sub.box(0.8 + i * 3.05, 3.1, 2.7, 0.8, fate, style="tile", size=13)
    s.text(0.8, 4.3, 11.8, 1.5, [{"text": "Total-loss vehicles are released to Salvanta Salvage Ltd, which handles salvage for the UK and the Nordics.", "size": 13}],
           size=13)
    s.notes(P.notes(rng, "salvage categories (BR-REC-010)", n_filler=1))
    D.fact(s, "group", "Category S May be sold for repair",
           "Salvage categories S and N may be sold for repair; A and B are scrapped (BR-REC-010).", kind="visual_only",
           world_ref="RULE:BR-REC-010@v1", shape_name="Category S")

    # 9 Claims Hub design mock-up
    s = D.content("Claims Hub recovery case – design mock-up", "Target")
    case = f"REC-UK-{rng.randint(10000, 99999)}"
    png = R.ui_screen(
        "Claims Hub", "Siobhan Quill · Recoveries (UK)",
        ["Work queue", "Claims", "Recoveries", "Salvage", "Receipts", "Reports"], "Recoveries",
        f"Recoveries  /  {case}", f"Recovery case {case}",
        [("Recovery type", "Subrogation – motor collision"), ("Third party", "Insured – insurer identified"),
         ("Pursuit check", "Recoverable ≥ £1,000 – pursue"), ("Demand", "Issued – chase at 28 days"),
         ("Limitation diary", "66 months (property)"), ("Excess refund", "Within 10 business days of full recovery")],
        chips=[("OPEN", "teal"), ("DEMAND ISSUED", "amber")], env="DESIGN MOCK-UP",
        side_panel=("Linked", ["Claim record", "Assessor report", "Demand letter", "Salvage record"]))
    s.picture_fit(png, 0.9, 1.35, 11.5, 5.55,
                  alt=f"Design mock-up of a Claims Hub recovery case screen ({case}) showing the pursuit check, demand chase at 28 days and the limitation diary.")
    s.notes(P.notes(rng, "the target recovery screen",
                    ["recovery-svc is planned to replace SUBTRAK; the screen is a design mock-up, not production."]))
    D.fact(s, "image", "Recoverable ≥ £1,000 – pursue",
           "Claims Hub recovery case mock-up shows the pursuit check 'Recoverable ≥ £1,000 – pursue'.", kind="screenshot",
           world_ref="RULE:BR-REC-003@v3")

    # 10 interfaces
    s = D.content("Interfaces used by the recovery process", "Interfaces")
    rows = []
    for iid in ["CLX-IF-022", "CLX-IF-023", "CLX-IF-024", "CLX-IF-025", "CLX-IF-026", "CLX-IF-029"]:
        i = W.interfaces[iid]
        D.need(f"INTERFACE:{iid}", "schedule")
        rows.append((iid, i["name"], f"{W.system_name(i['source_system'], d)} → {W.system_name(i['target_system'], d)}",
                     i["protocol"], W.interface_schedule(iid, d), W.name_of(i["owner"], d)))
    s.table(0.5, 1.45, 12.3, ["ID", "Name", "Source → target", "Protocol", "Schedule", "Owner"], rows,
            col_w=[1.1, 2.9, 3.3, 1.1, 1.8, 1.7], row_h=0.55, size=10, first_col_bold=True)
    s.notes(P.notes(rng, "the interfaces the process relies on", n_filler=1))
    D.fact(s, "table", "Tue,Thu 05:00",
           "CLX-IF-026 Subrogation demand letters (CLARA → Notify, SFTP) run Tuesday and Thursday at 05:00.",
           world_ref="INTERFACE:CLX-IF-026#schedule")
    D.fact(s, "table", "SUBTRAK synchronisation",
           "CLX-IF-022 SUBTRAK synchronisation (CLARA → Subrogation Tracker, DB2 unload) runs daily 22:00.",
           world_ref="INTERFACE:CLX-IF-022#schedule")

    # 11 measures
    s = D.content("Measures", "Performance")
    s.bullets(0.6, 1.5, 7.8, 4.5, [
        "Recovery rate is reported monthly as receipts over recoverable outlay (BR-REC-014).",
        "Case opening within 10 business days of the flag.",
        "Demand issued within 10 business days.",
        "Receipts posted and reserves adjusted within 2 business days of receipt.",
    ], size=13)
    s.notes(P.notes(rng, "how the process is measured", n_filler=1))
    D.fact(s, "text", "receipts over recoverable outlay (BR-REC-014)",
           "Recovery rate is reported monthly as receipts over recoverable outlay (BR-REC-014).", world_ref="RULE:BR-REC-014@v1")

    # 12 accountability (steps 01-05)
    s = D.content("Accountability (RACI)", "Accountability")
    rows = CM.raci_rows(W, ["PS-REC-01", "PS-REC-02", "PS-REC-03", "PS-REC-04", "PS-REC-05"], d)
    s.table(0.5, 1.45, 12.3, ["Step", "Activity", "Responsible", "Accountable", "Consulted", "Informed"], rows,
            col_w=[1.1, 2.9, 2.6, 1.6, 2.0, 2.1], row_h=0.55, size=10, first_col_bold=True)
    s.notes(P.notes(rng, "who is responsible at each step", n_filler=1))

    # 13 contacts
    CM.contacts(D, [("P013", "Process owner"), ("P014", "UK recoveries team"), ("P033", "Assessment hand-off"),
                    ("P060", "Subrogation litigation (Quarryhill Solicitors)")])

    # 14 document control
    hist = CM.history_rows(D, [("2.0", "Re-issued under the acting owner"), ("2.1", ""), ("3.0", "Group process from 1 September 2025")],
                           spacing=(30, 120))
    CM.doc_control(D, hist, [("P005", "Approved"), ("P011", "Reviewed")], status="Approved",
                   reviewers=[W.name_of(x, d) for x in ("P014", "P033")],
                   distribution="Recoveries & Subrogation (Group), Claims Operations, Claims Assessment",
                   purpose="Group recovery and subrogation process after the September 2025 re-organisation.")
    return D

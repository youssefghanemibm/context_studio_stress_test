"""VS012 Wave 1 Cut-over Plan (2026-09-04, Arjun Kesavan, approved).

The freeze window (2026-09-11 18:00 to 2026-09-14 06:00) is given only in the notes of slide 3."""
from __future__ import annotations

from . import common as CM
from . import phrases as P
from . import raster as R
from .core import Deck
from .lanes import swimlane


def build(W, out_dir):
    D = Deck(W, "VS012", version="1.2", doc_ref="SKR-CUT-W1", out_dir=out_dir)
    d = D.date
    rng = D.rng
    mw1 = W.waves["MW-1"]
    live_svcs = [sv["name"] for sv in W.services.values() if sv["go_live"] == mw1["date"]]

    # 1 title
    D.title_slide(D.title, "UK motor (Motor Private UK) – cut-over weekend 11 to 14 September 2026",
                  [f"Programme Skerry  |  Version {D.version}  |  {D.date_long()}",
                   f"Cut-over lead: {D.author}, {D.author_title} (IBM Consulting)", "Status: Approved"])

    # 2 agenda
    CM.agenda(D, ["Cut-over weekend", "Scope", "Go / no-go", "Runbook phases", "Rehearsals", "Cut-over console",
                  "Roles and contacts", "Communications and rollback", "Hypercare and risks"], kicker="Wave 1 cut-over")

    # 3 cut-over weekend (Gantt without times; freeze only in notes)
    s = D.content("Cut-over weekend at a glance", "Timeline")
    days = ["Fri 11 Sep", "Sat 12 Sep", "Sun 13 Sep", "Mon 14 Sep"]
    x0, colw = 3.3, 2.38
    for i, dy in enumerate(days):
        s.box(x0 + i * colw, 1.45, colw - 0.06, 0.45, dy, style="tile", fill="navy2", color="white", size=12, bold=True)
    bars = [("CLARA freeze – UK motor", 0.55, 3.6, "amber"), ("Final CLARA batch and extract", 0.6, 1.0, "sky"),
            ("Load into Claims Hub", 1.0, 1.4, "teal"), ("Reconciliation", 1.5, 2.3, "teal"),
            ("Interface switch-over", 2.3, 2.8, "sky"), ("Business verification", 2.6, 3.4, "plum"),
            ("Go-live – business open", 3.4, 3.95, "green")]
    for k, (name, a, b, colr) in enumerate(bars):
        y = 2.1 + k * 0.62
        s.text(0.5, y, 2.7, 0.45, [{"text": name}], size=11, anchor="m")
        s.box(x0 + a * colw, y + 0.05, (b - a) * colw, 0.38, "", style="tile", fill=colr)
    s.notes(P.notes(rng, "the cut-over weekend",
                    ["Wave 1 freeze from 2026-09-11 18:00 to 2026-09-14 06:00.",
                     "Exact step times are in the runbook; the bars show the order and rough duration only."]))
    D.place("vs12_freeze", s, "notes", "Wave 1 freeze from 2026-09-11 18:00 to 2026-09-14 06:00")

    # 4 scope
    s = D.content("Scope", "Scope")
    prod = W.products["PRD-MOT-UK"]
    s.table(0.5, 1.45, 6.0, ["Item", "Detail"], [
        ("Product", f"{prod['id']} – {prod['name']}"), ("Policies in force", f"{prod['policies_in_force']:,}"),
        ("Cut-over date", D.date_long(mw1["date"])), ("Full rehearsals", str(mw1["rehearsals"])),
        ("System of record after cut-over", "Claims Hub")], col_w=[2.2, 3.8], row_h=0.5, size=11, first_col_bold=True)
    s.text(6.9, 1.35, 5.9, 0.3, [{"text": "Services going live", "bold": True}], size=12, color="navy")
    s.bullets(6.9, 1.7, 5.9, 2.6, live_svcs, size=12)
    s.text(6.9, 4.3, 5.9, 0.3, [{"text": "Interfaces switched on", "bold": True}], size=12, color="navy")
    sw = [i for i in ("CLX-IF-035", "CLX-IF-038", "CLX-IF-050") if W.interfaces[i]["since"] == mw1["date"]]
    s.bullets(6.9, 4.65, 5.9, 2.0, [f"{i} – {W.interfaces[i]['name']}" for i in sw], size=12)
    s.notes(P.notes(rng, "what is in scope for Wave 1", n_filler=1))
    D.fact(s, "text", "payment-orchestrator",
           "Services going live with Wave 1 on 2026-09-14: " + ", ".join(live_svcs) + ".", world_ref="SERVICE:payment-orchestrator#go_live")
    D.fact(s, "text", "CLX-IF-050 – Claims Hub journals to GL",
           "CLX-IF-050 Claims Hub journals to GL is switched on with Wave 1 (since 2026-09-14).", world_ref="INTERFACE:CLX-IF-050#since")
    D.fact(s, "table", "612,000", "Motor Private UK (PRD-MOT-UK) has 612,000 policies in force.",
           world_ref="PRODUCT:PRD-MOT-UK#policies_in_force")

    # 5 go / no-go
    s = D.content("Go / no-go", "Governance")
    mtg = W.meetings["MTG-011"]
    rows = [(W.name_of(p, d), W.title_of(p, d)) for p in mtg["attendees"]]
    s.text(0.5, 1.35, 5.8, 0.3, [{"text": f"Go / no-go meeting – {D.date_long(mtg['date'])}", "bold": True}], size=12, color="navy")
    s.table(0.5, 1.7, 6.0, ["Attendee", "Role"], rows, col_w=[2.2, 3.8], row_h=0.4, size=10, first_col_bold=True)
    s.bullets(6.9, 1.5, 5.9, 4.8, [{"text": "Criteria", "bold": True},
                                   "All three rehearsals completed with signed-off reconciliation.",
                                   "Reserve parallel run closed (28 August 2026).",
                                   "No open Severity 1 defects against Wave 1 services.",
                                   "Business verification team and hypercare rota confirmed.",
                                   "CAB approval of the production changes."], size=12)
    s.notes(P.notes(rng, "how the go decision will be taken",
                    [f"{W.name_of('P004', d)} takes the go decision as Steering Committee chair."]))
    D.fact(s, "table", "Callum Fairbairn",
           "The Wave 1 go/no-go meeting (2026-09-11) invite includes Callum Fairbairn, Data Migration Lead (IBM).",
           world_ref="MEETING:MTG-011#attendees")

    # 6 runbook swimlane (no owner facts recorded)
    s = D.content("Runbook phases", "Runbook")
    L = swimlane(s, ["IBM migration team", "CLARA platform and batch", "Claims Hub squads", "Claims Operations"],
                 heights=[1.25, 1.25, 1.25, 1.25])
    r1 = L[1].step(2.4, "Final batch and freeze", w=1.6, size=9)
    r2 = L[0].step(4.3, "Extract and load", w=1.6, size=9)
    r3 = L[0].step(6.2, "Reconcile", w=1.5, size=9)
    r4 = L[2].step(8.0, "Switch interfaces and smoke test", w=1.8, size=9)
    r5 = L[3].step(10.1, "Business verification", w=1.6, size=9)
    r6 = L[3].step(11.85, "Open for business", w=0.95, size=9, style="outcome")
    for a, b in [(r1, r2), (r2, r3), (r3, r4), (r4, r5), (r5, r6)]:
        s.connect(a, b)
    s.notes(P.notes(rng, "the runbook phases", n_filler=2))

    # 7 rehearsals
    s = D.content("Rehearsals", "Readiness")
    s.bullets(0.6, 1.5, 7.6, 4.5, [f"{mw1['rehearsals']} full dress rehearsals on masked data (ADR-025).",
                                   "Each rehearsal runs the runbook end to end, including reconciliation and interface switch-over.",
                                   "Timings from the final rehearsal set the cut-over plan.",
                                   "Lessons from Wave 0 (Denmark) are built into the runbook."], size=13)
    s.box(8.6, 1.6, 4.2, 2.4, [{"text": "Reference", "bold": True, "size": 13},
                               {"text": "Wave 0 – Denmark cut over on 1 June 2026 after two rehearsals.", "size": 12}],
          style="tile", align="l", anchor="t", margins=0.15)
    s.notes(P.notes(rng, "the rehearsal approach", n_filler=1))
    D.fact(s, "text", "3 full dress rehearsals on masked data (ADR-025)",
           "Wave 1 was preceded by 3 full dress rehearsals on masked data (ADR-025).", world_ref="WAVE:MW-1#rehearsals")

    # 8 cut-over console (UI screenshot)
    s = D.content("Cut-over console (dress rehearsal view)", "Console")
    rows = [(sv, W.services[sv]["k8s_namespace"], str(W.services[sv]["replicas"]), "Ready") for sv in live_svcs]
    png = R.ui_screen(
        "Claims Hub – Operations console", "Arjun Kesavan · Cut-over lead",
        ["Overview", "Services", "Interfaces", "Reconciliation", "Defects", "Runbook"], "Services",
        "Cut-over  /  Wave 1 – UK motor  /  Services", "Wave 1 – UK motor: service readiness",
        [("Product", "Motor Private UK"), ("Planned go-live", "14 Sep 2026"),
         ("Rehearsal", "Dress rehearsal 3"), ("Services in scope", str(len(live_svcs)))],
        chips=[("REHEARSAL", "amber"), ("ALL SERVICES READY", "green")],
        table=(["Service", "Namespace", "Replicas", "Status"], rows), env="REHEARSAL")
    s.picture_fit(png, 0.9, 1.35, 11.5, 5.55,
                  alt="Operations console during the Wave 1 dress rehearsal listing the services going live, their namespaces, replica counts and readiness.")
    s.notes(P.notes(rng, "the console used on the weekend", n_filler=1))
    D.fact(s, "image", "chub-recovery",
           "Cut-over console image lists recovery-svc in namespace chub-recovery with 2 replicas among the Wave 1 services.",
           kind="screenshot", world_ref="SERVICE:recovery-svc#k8s_namespace")

    # 9 roles
    s = D.content("Roles and contacts for the weekend", "Roles")
    people = [("P048", "Cut-over lead"), ("P051", "Extract, load and reconciliation"), ("P016", "CLARA freeze and batch"),
              ("P026", "Batch schedule"), ("P032", "CAB approvals"), ("P041", "reserve-engine and gl-posting-svc"),
              ("P042", "settlement, payments and recovery services"), ("P017", "Business acceptance"),
              ("P022", "Business verification – UK motor (Leeds)"), ("P011", "Claims operations sign-off")]
    rows = []
    for pid, role in people:
        p = W.people[pid]
        org = "IBM Consulting" if p.get("employer") == "ORG-IBM" else "Corvane Mutual"
        rows.append((W.name_of(pid, d), W.title_of(pid, d), org, role, p["phone"]))
    s.table(0.5, 1.4, 12.3, ["Name", "Title", "Organisation", "Weekend role", "Phone"], rows,
            col_w=[1.9, 3.3, 1.6, 3.6, 1.6], row_h=0.44, size=9, first_col_bold=True)
    s.notes(P.notes(rng, "who is on duty",
                    ["There are two people called Callum Fairbairn on this list: the IBM Data Migration Lead in London and the Corvane Motor Claims Team Leader in Leeds."]))
    D.fact(s, "table", "Motor Claims Team Leader",
           "Wave 1 roles: Callum Fairbairn (Corvane, Motor Claims Team Leader, Leeds) does business verification; Callum Fairbairn (IBM, Data Migration Lead) runs extract, load and reconciliation.",
           kind="general", world_ref="PERSON:P022#notes")
    D.fact(s, "notes", "two people called Callum Fairbairn on this list",
           "Speaker notes: two different people named Callum Fairbairn are on the Wave 1 roster (IBM London; Corvane Leeds).",
           kind="speaker_notes", world_ref="PERSON:P051#notes")

    # 10 communications
    s = D.content("Communications", "Communications")
    s.table(0.5, 1.45, 12.3, ["Audience", "Message", "Channel", "When"], [
        ("Contact Centre (Glasgow)", "Freeze weekend; how to log new FNOL", "Team briefing", "Week before"),
        ("UK motor claims teams", "Claims Hub go-live and support routes", "Briefing and floor walkers", "Week before and Monday"),
        ("Brokers", "Service continuity over the weekend", "Broker bulletin", "Week before"),
        ("Finance", "Journal source switches to Claims Hub", "Email", "Week before"),
        ("All staff", "Go-live confirmation", "Intranet", "Monday")], col_w=[2.6, 4.4, 2.8, 2.5], row_h=0.55, size=11)
    s.notes(P.notes(rng, "the communications plan", n_filler=1))

    # 11 rollback
    s = D.content("Rollback", "Rollback")
    s.bullets(0.6, 1.5, 7.8, 4.8, ["A rollback decision point sits before business open on Monday.",
                                   "If invoked, UK motor stays on CLARA and the freeze is lifted.",
                                   "Claims Hub data loaded for the wave is quarantined, not deleted.",
                                   "Read-only CLARA enquiry after cut-over is proposed in ADR-026."], size=13)
    s.notes(P.notes(rng, "how rollback would work", n_filler=1))
    D.fact(s, "text", "Read-only CLARA enquiry after cut-over is proposed in ADR-026",
           "ADR-026 (proposed) covers read-only CLARA enquiry after cut-over.", world_ref="ADR:ADR-026")

    # 12 hypercare
    s = D.content("Hypercare", "Hypercare")
    D.need("COMMITTEE:COM-04", "cadence")
    s.bullets(0.6, 1.5, 7.8, 4.8, ["Squads on rota from go-live; daily defect triage with Claims Operations.",
                                   "Fixes ship through the weekly Change Advisory Board (Wednesday 11:00).",
                                   "Hypercare exit agreed at a Steering Committee meeting.",
                                   "Defect counts reported by severity at each Steering Committee."], size=13)
    s.notes(P.notes(rng, "hypercare after go-live", n_filler=1))
    D.fact(s, "text", "weekly Change Advisory Board (Wednesday 11:00)",
           "Production fixes go through the weekly Change Advisory Board on Wednesdays at 11:00.", world_ref="COMMITTEE:COM-04#cadence")

    # 13 risks
    s = D.content("Cut-over risks", "Risks")
    s.table(0.5, 1.45, 12.3, ["Risk", "Mitigation"], [
        ("Reconciliation takes longer than planned", "Start reconciliation per batch, not at the end of the load"),
        ("Interface switch-over fails for one consumer", "Switch interfaces one at a time with a smoke test after each"),
        ("Contact centre receives FNOL during the freeze", "Paper capture and re-key on Monday"),
        ("Hypercare demand peaks on Monday", "Floor walkers in Leeds and extra squad cover")], col_w=[5.2, 7.1], row_h=0.6, size=11)
    s.notes(P.notes(rng, "the main cut-over risks", n_filler=1))

    # 14 document control
    hist = CM.history_rows(D, [("1.0", "Plan baseline after rehearsal 2"), ("1.1", ""), ("1.2", "")], spacing=(6, 15))
    CM.doc_control(D, hist, [("P004", "Approved"), ("P017", "Approved"), ("P032", "Approved")], status="Approved",
                   reviewers=[W.name_of(x, d) for x in ("P051", "P016", "P011")],
                   distribution="Cut-over team, Claims Hub squads, CLARA platform team, Claims Operations UK",
                   purpose="Plan for the Wave 1 (UK motor) cut-over weekend.")
    return D

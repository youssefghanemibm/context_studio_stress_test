"""VS015-VS019 deck builders."""
from __future__ import annotations

import re

from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN

from . import phrases as PH
from . import raster as R
from .common import approvers, contacts_slide, email, glossary_slide, guard, history, next_steps_slide, person, risks_slide
from .core import (AMBER, CONTENT_LEFT, CONTENT_TOP, CONTENT_W, GREY, GREY_LT, NAVY, SAND, TEAL, TEAL_LT, WHITE,
                   Deck, fmt_date, minus_days)


# =========================================================================================
# VS015 FRAUDNET becomes Sentinel - staff briefing (2025-02-17)
# =========================================================================================
def build_vs015(W, out_dir):
    fid = "VS015"
    dk = Deck(W, fid, out_dir, short_title="FRAUDNET becomes Sentinel")
    d = dk.date
    rn = W.systems["SYS03"]["renames"][0]
    assert rn["date"] == "2025-03-01" and W.system_name("SYS03", d) == "FRAUDNET"
    guard(W, fid, [("SYSTEM:SYS03", "renames"), ("DECISION:DEC-002", None), ("TICKET:CHUB-117", None),
                   ("RULE:BR-FRD-012@v2", "parameters.threshold"), ("RULE:BR-TRI-007@v1", "text"),
                   ("VENDOR:VEN-15", "role"), ("INTERFACE:CLX-IF-008", "schedule"),
                   ("INTERFACE:CLX-IF-009", "schedule"), ("INTERFACE:CLX-IF-010", "schedule"),
                   ("INTERFACE:CLX-IF-011", "schedule")])
    thr = W.rule_version("BR-FRD-012", d)
    assert thr["version"] == 2

    # 1 title (PL-107)
    s = dk.title_slide("FRAUDNET becomes Sentinel on 1 March 2025",
                       "Staff briefing for claims, SIU and IT support colleagues",
                       [f"Presented by {person(W, 'P027', d)}",
                        f"Counter-Fraud analytics  |  {fmt_date(d)}  |  Classification: Internal",
                        "Change reference: CHUB-117"])
    dk.fact("alias_use", "FRAUDNET is renamed Sentinel on 1 March 2025 (title slide).", 1, "text",
            "FRAUDNET becomes Sentinel on 1 March 2025", placement="PL-107")
    dk.fact("general", "The rename is tracked under change ticket CHUB-117.", 1, "text",
            "Change reference: CHUB-117", world_ref="TICKET:CHUB-117")
    dk.notes(s, "Welcome everyone. This is a short briefing: the fraud scoring engine we all know as FRAUDNET "
                "takes the name Sentinel from 1 March. Nothing about how claims are scored changes. "
                "Questions at the end, and the contacts slide has names for follow-up.")

    # 2 document control
    appr = approvers(W, d, ["P008", "P016", "P037"], minus_days(d, 1))
    dk.doc_control_slide("CMI-CFA-BRF-2025-02", f"{person(W, 'P027', d)}", appr,
                         history(dk, ["P027", "P027", "P027"], spans=(11, 6, 2)),
                         "Claims Operations UK, Claims Operations Nordics, SIU, Legacy Claims Platforms, "
                         "Contact Centre, Service Desk")

    # 3 what is changing
    s = dk.new_slide("What is changing – and why")
    items = [
        "The fraud scoring engine FRAUDNET is renamed Sentinel with effect from 1 March 2025",
        "It is a name change only: same engine, same model, same 0–100 score",
        "The engine is still licensed from Kestwick Analytics Ltd",
        "The new name is used consistently on every screen, report and interface from go-live",
        "Screens, reports, interfaces and documentation move to the new name over March",
        "Change ticket CHUB-117 tracks the rename across interfaces and documentation",
    ]
    dk.bullets(s, items, size=18)
    dk.fact("general", "Sentinel (formerly FRAUDNET) scores claims on a 0–100 scale.", 3, "text",
            "same engine, same model, same 0–100 score", world_ref="SYSTEM:SYS03#tech")
    dk.fact("general", "The scoring engine is licensed from Kestwick Analytics Ltd.", 3, "text",
            "licensed from Kestwick Analytics Ltd", world_ref="VENDOR:VEN-15#role")
    dk.notes(s, "Stress that this is cosmetic for most people. The engine owner, the vendor and the model are "
                "unchanged. If anyone asks about the score itself, it still runs from 0 to 100.")

    # 4 what changes for you (grouped columns) + notes PL-108
    s = dk.new_slide("What changes for you")
    cols = [
        ("Claims Handlers", ["Screens show 'Sentinel score' where they used to show 'FRAUDNET score'",
                             "No change to how or when a claim is scored",
                             "Referral rules and SIU contact points stay the same"]),
        ("SIU investigators", ["Referral reports carry the new name from March",
                               "Saved searches keep working",
                               "Case notes may mention either name; both mean the same engine"]),
        ("IT and service desk", ["Endpoint name becomes sentinel.corvane.internal",
                                 "Interface catalogue entries are renamed, not re-numbered",
                                 "Raise anything unexpected against CHUB-117"]),
    ]
    for i, (hdr, lines) in enumerate(cols):
        g = dk.group(s, f"grp-audience-{i + 1}")
        x = CONTENT_LEFT + i * 4.1
        dk.box(s, x, CONTENT_TOP + 0.1, 3.85, 0.7, hdr, shape=MSO_SHAPE.RECTANGLE, fill=NAVY, line=None,
               color=WHITE, size=16, bold=True, group=g, name=f"audience-hdr-{i + 1}")
        dk.text(s, x, CONTENT_TOP + 0.9, 3.85, 3.8, lines, size=14, bullets=True, group=g, fill=TEAL_LT,
                para_space=10, name=f"audience-body-{i + 1}")
    dk.fact("visual_only", "IT support: the Sentinel endpoint name is sentinel.corvane.internal.", 4, "group",
            "Endpoint name becomes sentinel.corvane.internal", world_ref="SYSTEM:SYS03#description",
            shape_name="grp-audience-3")
    dk.notes(s, "Talk track: most colleagues only notice a label change. For IT: the old DNS alias "
                "fraudnet.corvane.internal stays until 31 March 2025, so anything still pointing at the old "
                "name keeps working during March. Please do not hard-code the old name in anything new.")
    dk.fact("speaker_notes", "Speaker notes: the old DNS alias fraudnet.corvane.internal stays until 31 March 2025.",
            4, "notes", "the old DNS alias fraudnet.corvane.internal stays until 31 March 2025", placement="PL-108")

    # 5 systems touched (connectors)
    s = dk.new_slide("Systems touched by the rename", "Interfaces keep their numbers; only names change")
    clara = dk.box(s, 0.7, 1.75, 4.2, 4.6, "CLARA", shape=MSO_SHAPE.RECTANGLE, fill=GREY_LT, line=GREY,
                   size=16, bold=True, anchor=MSO_ANCHOR.TOP, name="container-clara")
    p020 = dk.box(s, 1.3, 2.5, 3.0, 0.75, "CLRFR020", name="prog-CLRFR020")
    p110 = dk.box(s, 1.3, 3.75, 3.0, 0.75, "CLRFR110", name="prog-CLRFR110")
    p030 = dk.box(s, 1.3, 5.0, 3.0, 0.75, "CLRFR030", name="prog-CLRFR030")
    snt = dk.box(s, 8.6, 2.6, 3.4, 1.6, "Sentinel", fill=SAND, line=AMBER, size=18, bold=True, name="sys-sentinel")
    siu = dk.box(s, 8.6, 4.9, 3.4, 1.0, "SIU Case Manager", fill=SAND, line=AMBER, size=16, bold=True,
                 name="sys-scm")
    dk.connect(s, p020, snt, 3, 1, label="CLX-IF-008 online scoring (REST)", label_offset=(0, -0.34))
    dk.connect(s, p110, snt, 3, 1, label="CLX-IF-009 nightly batch request", label_offset=(0.3, 0.02))
    c3 = dk.connect(s, snt, p110, 2, 2, label="CLX-IF-010 batch score return", elbow=True,
                    label_offset=(0.6, 0.15), color=TEAL)
    dk.connect(s, p030, siu, 3, 1, label="CLX-IF-011 SIU referrals", label_offset=(0, -0.34))
    for i, (a, b, lab, ref) in enumerate([
            ("CLRFR020", "Sentinel", "CLX-IF-008 online scoring (REST)", "INTERFACE:CLX-IF-008"),
            ("CLRFR110", "Sentinel", "CLX-IF-009 nightly batch request", "INTERFACE:CLX-IF-009"),
            ("Sentinel", "CLRFR110", "CLX-IF-010 batch score return", "INTERFACE:CLX-IF-010"),
            ("CLRFR030", "SIU Case Manager", "CLX-IF-011 SIU referrals", "INTERFACE:CLX-IF-011")]):
        dk.fact("arrow_only", f"Connector {a} → {b} labelled '{lab}'.", 5, "connector",
                f"{a} -> {b} [label: {lab}]", world_ref=ref)
    dk.notes(s, "These are the four flows that mention the engine by name. CLRFR020 makes the real-time call "
                "during claim registration; CLRFR110 sends and receives the nightly batch. Referrals to SIU are "
                "unaffected but the referral record shows the new score label.")

    # 6 old name -> new name
    s = dk.new_slide("Old name, new name")
    rows = [["Where you see…", "Before 1 March 2025", "From 1 March 2025"],
            ["System name", "FRAUDNET (also written FraudNet)", "Sentinel"],
            ["Score label", "FRAUDNET score", "Sentinel score"],
            ["Endpoint", "fraudnet.corvane.internal", "sentinel.corvane.internal"],
            ["Short form", "FRAUDNET", "SNT"],
            ["Informal name", "the fraud engine", "the fraud engine (unchanged)"],
            ["Interface catalogue", "CLX-IF-008/009/010 names mention FRAUDNET", "Names mention Sentinel"]]
    dk.table(s, rows, col_w=[2.6, 4.6, 4.6], size=14, row_h=0.55, name="Name mapping")
    dk.fact("alias_use", "SNT is the short form of Sentinel; 'the fraud engine' remains an informal alias.", 6,
            "table", "Short form FRAUDNET SNT", world_ref="SYSTEM:SYS03#aliases")
    dk.fact("alias_use", "The score label changes from 'FRAUDNET score' to 'Sentinel score'.", 6, "table",
            "Score label FRAUDNET score Sentinel score", world_ref="SYSTEM:SYS03#aliases")

    # 7 timeline raster
    s = dk.new_slide("Timeline")
    cv = R.Canvas(1600, 700)
    cv.title("Rename timeline (CHUB-117)")
    pts = [(170, "4 Feb 2025", "CHUB-117 raised"), (560, "17 Feb 2025", "Staff briefing"),
           (950, "1 Mar 2025", "Sentinel name live"), (1340, "March 2025", "Document updates")]
    cv.d.line([(120, 360), (1480, 360)], fill=R.GREY_MD, width=6)
    for i, (x, dt, lab) in enumerate(pts):
        cv.d.ellipse([x - 16, 344, x + 16, 376], fill=R.TEAL)
        cv.text((x, 270), dt, size=28, bold=True, fill=R.NAVY, anchor="ma")
        cv.text((x, 410), lab, size=28, fill=R.BLACK, anchor="ma")
        if i < len(pts) - 1:
            cv.arrow((x + 40, 520), (pts[i + 1][0] - 40, 520), color=R.TEAL, width=4)
    cv.text((800, 600), "Name change only – scoring, thresholds and SIU routing are unchanged", size=24,
            fill=R.GREY, anchor="ma")
    dk.picture(s, cv.png(), CONTENT_LEFT, CONTENT_TOP + 0.1, w=CONTENT_W,
               alt="Timeline of the FRAUDNET to Sentinel rename from the change ticket to document updates.",
               name="timeline-image")
    dk.fact("image_text", "Timeline image: CHUB-117 raised 4 Feb 2025; Sentinel name live 1 Mar 2025.", 7, "image",
            "Sentinel name live", world_ref="SYSTEM:SYS03#renames")
    dk.fact("image_text", "Timeline image: CHUB-117 raised on 4 Feb 2025.", 7, "image", "CHUB-117 raised",
            world_ref="TICKET:CHUB-117#created")
    dk.fact("alt_text", "Alt text describes the rename timeline image.", 7, "alt_text",
            "Timeline of the FRAUDNET to Sentinel rename")

    # 8 what does not change
    s = dk.new_slide("What does not change")
    items = [
        f"The referral threshold stays at a score of {thr['parameters']['threshold']} or more (BR-FRD-012 v2)",
        "Every new claim is still scored within 15 minutes of FNOL (BR-TRI-007)",
        "Referral handling and SIU investigation steps are the same",
        "The model owner and the vendor relationship are unchanged",
        "Historic scores remain on the claim record with their original values",
    ]
    dk.bullets(s, items, size=18)
    dk.fact("general", "Before the 2026 change, the referral threshold was a FRAUDNET/Sentinel score of 70 or more "
                       "(BR-FRD-012 v2).", 8, "text", "stays at a score of 70 or more (BR-FRD-012 v2)",
            world_ref="RULE:BR-FRD-012@v2#parameters.threshold")
    dk.fact("general", "Every new claim is scored within 15 minutes of FNOL (BR-TRI-007).", 8, "text",
            "scored within 15 minutes of FNOL (BR-TRI-007)", world_ref="RULE:BR-TRI-007@v1")
    dk.notes(s, "If someone asks whether the rename changes referral volumes: it does not. The threshold "
                "and the model are untouched by this change.")

    # 9 communications approach (chevrons, SmartArt-like group)
    s = dk.new_slide("How we are communicating the change")
    g = dk.group(s, "grp-comms-process")
    steps = PH.pick(dk.rng, PH.COMMS, 5)
    for i, st in enumerate(steps):
        dk.box(s, CONTENT_LEFT + i * 2.45, 2.6, 2.5, 1.6, st, shape=MSO_SHAPE.CHEVRON if i else MSO_SHAPE.PENTAGON,
               fill=TEAL if i % 2 == 0 else NAVY, line=None, color=WHITE, size=12, group=g,
               name=f"comms-step-{i + 1}")
    dk.text(s, CONTENT_LEFT, 4.6, CONTENT_W, 1.5,
            ["Team leaders cascade first, so that colleagues hear it from their own manager.",
             "The service desk has a short script and a known-issues page for the first weeks."],
            size=15, color=GREY)

    # 10 FAQ
    s = dk.new_slide("Frequently asked questions")
    rows = [["Question", "Answer"]] + [list(x) for x in dk.rng.sample(PH.FAQ, 5)]
    rows.append(["Is the old address switched off on 1 March?", "No – see the IT talk track in this briefing."])
    dk.table(s, rows, col_w=[4.2, 7.9], size=13, row_h=0.62, name="FAQ")

    # 11 contacts
    contacts_slide(dk, ["P027", "P008", "P016"])
    dk.fact("general", "Oskar Lindgren is a Senior Fraud Analyst (contact for the Sentinel rename).", 11, "table",
            "Oskar Lindgren Senior Fraud Analyst", world_ref="PERSON:P027#titles")

    # 12 appendix: interfaces
    s = dk.new_slide("Appendix – interfaces and programs referring to the engine")
    rows = [["Interface", "Name (from 1 March)", "Protocol", "Schedule", "CLARA program"]]
    for iid in ["CLX-IF-008", "CLX-IF-009", "CLX-IF-010", "CLX-IF-011"]:
        it = W.interfaces[iid]
        rows.append([iid, it["name"], it["protocol"], W.interface_schedule(iid, d), ", ".join(it["programs"])])
    dk.table(s, rows, col_w=[1.5, 4.4, 1.3, 1.7, 2.6], size=13, row_h=0.55, name="Interface appendix")
    dk.fact("general", "CLX-IF-009 (nightly Sentinel batch scoring request) runs daily 00:15.", 12, "table",
            "CLX-IF-009 Nightly Sentinel batch scoring request SFTP daily 00:15", world_ref="INTERFACE:CLX-IF-009#schedule")
    dk.fact("general", "CLX-IF-010 (nightly Sentinel batch score return) runs daily 00:55.", 12, "table",
            "daily 00:55", world_ref="INTERFACE:CLX-IF-010#schedule")
    dk.notes(s, "Owner of CLX-IF-008 is Oskar Lindgren. CLX-IF-011 is used by CLRFR030 and CLRFR070.")
    dk.fact("speaker_notes", "Speaker notes: CLX-IF-008 is owned by Oskar Lindgren.", 12, "notes",
            "Owner of CLX-IF-008 is Oskar Lindgren", world_ref="INTERFACE:CLX-IF-008#owner")
    return dk


# =========================================================================================
# VS016 reserve-engine Design (2026-02-24)
# =========================================================================================
def build_vs016(W, out_dir):
    fid = "VS016"
    dk = Deck(W, fid, out_dir, short_title="reserve-engine Design")
    d = dk.date
    svc = W.services["reserve-engine"]
    assert W.service_name("reserve-engine", d) == "reserve-engine"
    guard(W, fid, [("SERVICE:reserve-engine", "renames"), ("SERVICE:reserve-engine", "apis"),
                   ("SERVICE:reserve-engine", "config.tier3-review-days"),
                   ("SERVICE:reserve-engine", "config.large-loss-threshold-gbp"),
                   ("SERVICE:reserve-engine", "replicas"), ("SERVICE:reserve-engine", "infra.cpu_request"),
                   ("SERVICE:reserve-engine", "infra.memory_limit"), ("SERVICE:reserve-engine", "kafka_topics"),
                   ("SERVICE:reserve-engine", "replaces_programs"), ("RULE:BR-RSV-003@v3", "parameters"),
                   ("RULE:BR-RSV-011@v2", "parameters"), ("RULE:BR-RSV-007@v2", "parameters"),
                   ("ADR:ADR-019", None), ("ADR:ADR-011", None), ("TIMELINE:programme", "parallel_run.from"),
                   ("TIMELINE:programme", "parallel_run.to"), ("TOPIC:reserve.changed.v2", "partitions"),
                   ("TOPIC:claims.reserve.movement.v1", "producer")])
    assert not W.may_state(fid, "TOPIC:claims.reserve.movement.v1", "partitions")
    rsv3 = W.rule_version("BR-RSV-003", d)["parameters"]
    rsv7 = W.rule_version("BR-RSV-007", d)
    rsv11 = W.rule_version("BR-RSV-011", d)
    assert rsv7["version"] == 2

    # 1 title
    s = dk.title_slide("reserve-engine Design", "Claims Hub reserve service – Design Authority pack (approved)",
                       [f"Author: {person(W, 'P041', d)}",
                        f"Hub Squad – Reserve & Finance  |  {fmt_date(d)}  |  Classification: Internal"])
    dk.notes(s, "This pack replaces the reserve-svc design note. It reflects the rename agreed at the Design "
                "Authority on 3 February and the decisions taken since.")

    # 2 rename (PL-109)
    s = dk.new_slide("reserve-svc is now reserve-engine")
    dk.text(s, CONTENT_LEFT, CONTENT_TOP, CONTENT_W, 0.6,
            "reserve-svc is renamed reserve-engine on 2026-02-10 (ADR-019).", size=20, bold=True, color=TEAL,
            name="rename-statement")
    old = svc["path_history"][0]
    rows = [["Item", "Before (reserve-svc)", "After (reserve-engine)"],
            ["Repository path", old["repo_path"], svc["repo_path"]],
            ["Terraform module", old["terraform_module"], svc["terraform_module"]],
            ["OpenShift namespace", old["k8s_namespace"], svc["k8s_namespace"]],
            ["Change event", "reserve.changed.v1 (retired)", "reserve.changed.v2"],
            ["Change ticket", "—", "CHUB-233"]]
    dk.table(s, rows, y=CONTENT_TOP + 0.8, col_w=[2.5, 4.8, 4.8], size=14, row_h=0.55, name="Rename table")
    dk.fact("alias_use", "reserve-svc is renamed reserve-engine on 2026-02-10 (ADR-019).", 2, "text",
            "reserve-svc is renamed reserve-engine on 2026-02-10 (ADR-019)", placement="PL-109")
    dk.fact("general", "After the rename the repository path is services/reserve-engine (was services/reserve-svc).",
            2, "table", "Repository path services/reserve-svc services/reserve-engine",
            world_ref="SERVICE:reserve-engine#path_history")
    dk.fact("general", "The OpenShift namespace chub-reserve did not change with the rename.", 2, "table",
            "OpenShift namespace chub-reserve chub-reserve", world_ref="SERVICE:reserve-engine#k8s_namespace")
    dk.fact("general", "The rename introduced event reserve.changed.v2; v1 was retired.", 2, "table",
            "reserve.changed.v1 (retired) reserve.changed.v2", world_ref="TOPIC:reserve.changed.v2#note")
    dk.notes(s, "Decided at the Design Authority on 3 February (DEC-018). CHUB-233 covered the repository, "
                "namespace labels and Terraform module.")

    # 3 document control
    appr = approvers(W, d, ["P018", "P049", "P009", "P032"], minus_days(d, 1))
    dk.doc_control_slide("CHUB-DES-RSV-001", person(W, "P041", d), appr,
                         history(dk, ["P041", "P053", "P041"], spans=(29, 13, 5),
                                 notes=["reserve-svc design note (pre-rename)", "Renamed to reserve-engine; event v2",
                                        "Design Authority comments addressed"]),
                         "Design Authority, Hub Squad – Reserve & Finance, Reserving, Integration Platform")

    # 4 scope
    s = dk.new_slide("Scope and responsibilities")
    items = [f"Responsibilities: {svc['description'].lower()}",
             "The only Claims Hub service that writes reserves (ADR-011)",
             f"Owner: Hub Squad – Reserve & Finance, led by {W.name_of('P041', d)}",
             "Exposes REST APIs to Claims Hub screens and consumes events from Kafka",
             "Runs in parallel with CLARA during the reserve parallel run, then becomes the system of record per wave"]
    dk.bullets(s, items, size=17)
    dk.fact("general", "Only reserve-engine writes reserves in Claims Hub (ADR-011).", 4, "text",
            "The only Claims Hub service that writes reserves (ADR-011)", world_ref="ADR:ADR-011")

    # 5 context (connectors)
    s = dk.new_slide("Context: events in and out", "Topic names on the arrows")
    clara = dk.box(s, 0.6, 1.9, 2.3, 0.9, "CLARA", fill=GREY_LT, line=GREY, size=15, bold=True, name="ctx-clara")
    mq = dk.box(s, 0.6, 3.6, 2.3, 0.9, "MQ Backbone", fill=GREY_LT, line=GREY, size=14, bold=True, name="ctx-mq")
    esp = dk.box(s, 3.9, 3.6, 2.5, 0.9, "Event Streaming Platform", fill=GREY_LT, line=GREY, size=13, bold=True,
                 name="ctx-esp")
    tri = dk.box(s, 3.9, 1.9, 2.5, 0.9, "triage-svc", size=15, bold=True, name="ctx-triage")
    re_ = dk.box(s, 7.2, 2.6, 2.4, 1.3, "reserve-engine", fill=NAVY, line=None, color=WHITE, size=17, bold=True,
                 name="ctx-reserve-engine")
    gl = dk.box(s, 10.4, 1.9, 2.3, 0.9, "gl-posting-svc", size=14, bold=True, name="ctx-gl")
    rf = dk.box(s, 10.4, 3.9, 2.3, 0.9, "reporting-feed-svc", size=13, bold=True, name="ctx-rf")
    dk.connect(s, clara, mq, 2, 0, label="CLX-IF-042", label_offset=(0.75, -0.15))
    dk.connect(s, mq, esp, 3, 1, label="CLX-IF-049", label_offset=(0, -0.34))
    dk.connect(s, esp, re_, 3, 2, label="claims.reserve.movement.v1", elbow=True, label_offset=(0.2, 0.25))
    dk.connect(s, tri, re_, 3, 1, label="triage.completed.v1", label_offset=(0, -0.36))
    dk.connect(s, re_, gl, 3, 1, label="reserve.changed.v2", label_offset=(-0.1, -0.36))
    dk.connect(s, re_, rf, 3, 1, label="reserve.changed.v2", label_offset=(0.0, 0.08))
    for a, b, lab, ref in [("CLARA", "MQ Backbone", "CLX-IF-042", "INTERFACE:CLX-IF-042#target_system"),
                           ("MQ Backbone", "Event Streaming Platform", "CLX-IF-049", "INTERFACE:CLX-IF-049"),
                           ("Event Streaming Platform", "reserve-engine", "claims.reserve.movement.v1",
                            "SERVICE:reserve-engine#kafka_topics.consumes"),
                           ("triage-svc", "reserve-engine", "triage.completed.v1", "TOPIC:triage.completed.v1"),
                           ("reserve-engine", "gl-posting-svc", "reserve.changed.v2", "TOPIC:reserve.changed.v2"),
                           ("reserve-engine", "reporting-feed-svc", "reserve.changed.v2", "TOPIC:reserve.changed.v2")]:
        dk.fact("arrow_only", f"Connector {a} → {b} labelled '{lab}'.", 5, "connector", f"{a} -> {b} [label: {lab}]",
                world_ref=ref)
    dk.notes(s, "The bridge (ADR-012) republishes the CLARA reserve movement extract as events so the engine can "
                "reconcile during the parallel run and synchronise unmigrated claims later.")

    # 6 APIs
    s = dk.new_slide("API surface")
    rows = [["Method", "Path", "Purpose"]]
    for api in svc["apis"]:
        summ = api["summary"]
        if "revaluation" in api["path"]:
            summ = "Trigger a currency revaluation run (scope pending Design Authority decision)"
        rows.append([api["method"], api["path"], summ])
    dk.table(s, rows, col_w=[1.2, 4.0, 6.8], size=14, row_h=0.6, name="API table")
    dk.fact("general", "POST /reserves/{claimId}/movements posts a reserve movement with an authority check "
                       "against BR-RSV-003.", 6, "table",
            "POST /reserves/{claimId}/movements Post a reserve movement (authority checked against BR-RSV-003)",
            world_ref="SERVICE:reserve-engine#apis")
    dk.fact("general", "GET /reserves/{claimId}/history returns reserve movement history.", 6, "table",
            "GET /reserves/{claimId}/history Reserve movement history", world_ref="SERVICE:reserve-engine#apis")

    # 7 data model raster
    s = dk.new_slide("Data model (PostgreSQL, one database per service)")
    cv = R.Canvas(1600, 760)
    cv.title("reserve-engine schema: reserve")
    tabs = [("reserve.reserve", 60), ("reserve.reserve_movement", 580), ("reserve.review_schedule", 1100)]
    pos = {}
    for tname, x in tabs:
        cols = [c["name"] for c in W.tables[tname]["columns"]]
        h = 70 + 40 * len(cols)
        cv.d.rectangle([x, 120, x + 440, 120 + h], fill=R.WHITE, outline=R.NAVY, width=3)
        cv.d.rectangle([x, 120, x + 440, 180], fill=R.NAVY)
        cv.text((x + 220, 134), tname, size=26, bold=True, fill=R.WHITE, anchor="ma")
        for i, cn in enumerate(cols):
            cv.text((x + 20, 194 + 40 * i), cn, size=24, fill=R.BLACK)
        pos[tname] = (x, 120, h)
    cv.arrow((500, 260), (580, 260), label=None, color=R.TEAL)
    cv.text((540, 205), "1..n", size=24, bold=True, fill=R.TEAL, anchor="ma")
    cv.arrow((280, 560), (1110, 560), color=R.TEAL, dashed=True)
    cv.text((700, 575), "claim_id: one review schedule per claim", size=24, fill=R.TEAL, anchor="ma")
    dk.picture(s, cv.png(), CONTENT_LEFT + 0.3, CONTENT_TOP + 0.05, w=CONTENT_W - 0.6,
               alt="Entity diagram of the reserve schema with three tables: reserve, reserve_movement and "
                   "review_schedule.", name="data-model-image")
    dk.fact("image_text", "Data model image: reserve.reserve_movement holds amount_minor (minor units).", 7, "image",
            "amount_minor", world_ref="TABLE:reserve.reserve_movement#columns.amount_minor")
    dk.fact("image_text", "Data model image: reserve.review_schedule has a cadence_days column.", 7, "image",
            "cadence_days", world_ref="TABLE:reserve.review_schedule#columns.cadence_days")
    dk.fact("alt_text", "Alt text: the reserve schema has tables reserve, reserve_movement and review_schedule.", 7,
            "alt_text", "three tables: reserve, reserve_movement and review_schedule")
    dk.notes(s, "Amounts in events and movements are held in minor units (pence or øre) as per ADR-016, with the "
                "original currency alongside the GBP equivalent.")
    dk.fact("speaker_notes", "Amounts are held in minor units (pence/øre) per ADR-016.", 7, "notes",
            "minor units (pence or øre) as per ADR-016", world_ref="ADR:ADR-016")

    # 8 authority sequence raster
    s = dk.new_slide("Posting a reserve movement")
    cv = R.Canvas(1600, 800)
    cv.title("Sequence: reserve movement with authority check")
    lanes = [("Claims Hub UI", 160), ("reserve-engine", 620), ("Kafka (ESP)", 1060), ("gl-posting-svc", 1420)]
    for name, x in lanes:
        cv.box(x - 130, 100, 260, 64, name, size=24)
        cv.d.line([(x, 164), (x, 760)], fill=R.GREY_MD, width=3)
    cv.arrow((160, 240), (620, 240), label="POST /reserves/{claimId}/movements", label_size=22)
    cv.d.rectangle([600, 300, 640, 420], fill=R.TEAL_LT, outline=R.TEAL, width=2)
    cv.text((660, 320), "authority check (BR-RSV-003)", size=24, fill=R.NAVY)
    cv.text((660, 360), "above limit: approval queue", size=22, fill=R.GREY)
    cv.arrow((620, 480), (1060, 480), label="reserve.changed.v2", label_size=22)
    cv.arrow((1060, 580), (1420, 580), label="consume", label_size=22)
    cv.arrow((620, 680), (160, 680), label="201 Created + movement id", label_size=22, color=R.TEAL)
    dk.picture(s, cv.png(), CONTENT_LEFT + 0.3, CONTENT_TOP + 0.0, w=CONTENT_W - 0.6,
               alt="Sequence diagram: the Claims Hub screen posts a movement, reserve-engine checks authority and "
                   "publishes a change event that the GL posting service consumes.", name="sequence-image")
    dk.fact("image_text", "Sequence image: reserve-engine performs the authority check (BR-RSV-003) on movements.", 8,
            "image", "authority check (BR-RSV-003)", world_ref="RULE:BR-RSV-003")
    dk.fact("alt_text", "Alt text: gl-posting-svc consumes the change event published by reserve-engine.", 8,
            "alt_text", "publishes a change event that the GL posting service consumes")

    # 9 authority limits and large loss
    s = dk.new_slide("Authority limits and large-loss notification")
    rows = [["Role", "Reserve authority (BR-RSV-003 v3)"],
            ["Claims Handler", f"£{rsv3['claims_handler']:,}"],
            ["Team Leader", f"£{rsv3['team_leader']:,}"],
            ["Claims Manager", f"£{rsv3['claims_manager']:,}"],
            ["Claims Director", f"£{rsv3['claims_director']:,}"],
            ["Above Claims Director", "Reserving Committee"]]
    dk.table(s, rows, x=CONTENT_LEFT, y=CONTENT_TOP + 0.1, w=6.0, col_w=[2.6, 3.4], size=14, row_h=0.55,
             name="Authority table")
    dk.text(s, 7.0, CONTENT_TOP + 0.1, 5.7, 3.5,
            [f"Large-loss notification: any movement above £{svc['config']['large-loss-threshold-gbp']:,} is "
             "notified to ReCede within 24 hours (BR-RSV-011 v2)",
             "Configuration key: large-loss-threshold-gbp",
             "Nordic reserves are tested at the GBP equivalent at the GL month-end rate"],
            size=15, bullets=True, para_space=12)
    dk.fact("general", "reserve-engine reserve authority: Team Leader £100,000 (BR-RSV-003 v3).", 9, "table",
            "Team Leader £100,000", world_ref="RULE:BR-RSV-003@v3#parameters.team_leader")
    dk.fact("general", "reserve-engine reserve authority: Claims Director £2,000,000 (BR-RSV-003 v3).", 9, "table",
            "Claims Director £2,000,000", world_ref="RULE:BR-RSV-003@v3#parameters.claims_director")
    dk.fact("general", "Movements above £250,000 are notified to ReCede within 24 hours (BR-RSV-011 v2).", 9, "text",
            "any movement above £250,000 is notified to ReCede within 24 hours", world_ref="RULE:BR-RSV-011@v2")

    # 10 Tier-3 review scheduling
    s = dk.new_slide("Tier-3 reserve review scheduling")
    items = [f"Configuration key tier3-review-days = {rsv7['parameters']['review_days']} "
             "(matches BR-RSV-007 v2 in force today)",
             "review_schedule rows are created when a claim becomes Tier-3 and moved on at each review",
             "The cadence is configuration, not code (ADR-010), so a rule change is a configuration release",
             "Overdue reviews are surfaced to team leaders in the work queue"]
    dk.bullets(s, items, size=17)
    dk.fact("temporal", "In February 2026 the reserve-engine setting tier3-review-days is 21 (BR-RSV-007 v2).", 10,
            "text", "tier3-review-days = 21", world_ref="SERVICE:reserve-engine#config.config_history")
    dk.notes(s, "Reserving has signalled that the cadence may tighten later this year; because it is a configuration "
                "value this does not need a code change.")

    # 11 programs replaced (groups)
    s = dk.new_slide("CLARA programs replaced by reserve-engine")
    reps = svc["replaces_programs"]
    online = [p for p in reps if W.programs[p]["type"] == "online"]
    batch = [p for p in reps if W.programs[p]["type"] == "batch" and not p.startswith("CLRGL")]
    fin = [p for p in reps if p.startswith("CLRGL")]
    for gi, (gname, plist) in enumerate([("Online (CICS)", online), ("Batch", batch), ("Finance", fin)]):
        g = dk.group(s, f"grp-replaced-{gi + 1}")
        x = CONTENT_LEFT + gi * 4.1
        dk.box(s, x, CONTENT_TOP + 0.05, 3.9, 0.55, gname, shape=MSO_SHAPE.RECTANGLE, fill=NAVY, line=None,
               color=WHITE, size=15, bold=True, group=g, name=f"replaced-hdr-{gi + 1}")
        for j, p in enumerate(plist):
            col, row = j % 2, j // 2
            dk.box(s, x + col * 1.97, CONTENT_TOP + 0.75 + row * 0.62, 1.9, 0.52, p, size=12, group=g,
                   name=f"replaced-{p}")
    dk.fact("visual_only", "reserve-engine replaces CLARA batch program CLRRS150 (grouped under Batch).", 11, "group",
            "CLRRS150", world_ref="SERVICE:reserve-engine#replaces_programs", shape_name="grp-replaced-2")
    dk.fact("visual_only", "reserve-engine replaces CLRGL090 (grouped under Finance).", 11, "group", "CLRGL090",
            world_ref="SERVICE:reserve-engine#replaces_programs", shape_name="grp-replaced-3")
    dk.fact("visual_only", "reserve-engine replaces online program CLRFN030.", 11, "group", "CLRFN030",
            world_ref="SERVICE:reserve-engine#replaces_programs", shape_name="grp-replaced-1")
    dk.notes(s, "CLRGL090 updates CLR.T_RESERVE without writing CLR.T_RESERVE_MOVEMENT (internal audit finding "
                "IA-25-07); this is why change data capture on the movement table was dropped.")
    dk.fact("speaker_notes", "Speaker notes: CLRGL090 updates CLR.T_RESERVE without writing CLR.T_RESERVE_MOVEMENT "
                             "(IA-25-07).", 11, "notes",
            "CLRGL090 updates CLR.T_RESERVE without writing CLR.T_RESERVE_MOVEMENT",
            world_ref="PROGRAM:CLRGL090#notes")

    # 12 deployment
    s = dk.new_slide("Deployment")
    rows = [["Item", "Value"],
            ["Image", svc["image"]],
            ["Namespace", svc["k8s_namespace"]],
            ["Replicas", str(svc["replicas"])],
            ["CPU request / memory limit", f"{svc['infra']['cpu_request']} / {svc['infra']['memory_limit']}"],
            ["Clusters", "ocp-prd-lon1 (primary), ocp-dr-lds1 (DR)"],
            ["Terraform module", svc["terraform_module"]]]
    dk.table(s, rows, col_w=[3.2, 8.8], size=14, row_h=0.55, name="Deployment table")
    dk.fact("general", "reserve-engine runs 4 replicas.", 12, "table", "Replicas 4", world_ref="SERVICE:reserve-engine#replicas")
    dk.fact("general", "reserve-engine CPU request 500m, memory limit 2Gi.", 12, "table", "500m / 2Gi",
            world_ref="SERVICE:reserve-engine#infra")

    # 13 parallel run
    s = dk.new_slide("Parallel run and migration")
    pr = W.timeline["programme"]["parallel_run"]
    a = dk.box(s, 0.8, 2.3, 3.0, 1.1, "CLARA reserves", fill=GREY_LT, line=GREY, size=15, bold=True, name="pr-clara")
    b = dk.box(s, 5.2, 2.3, 3.0, 1.1, "Daily reconciliation", fill=SAND, line=AMBER, size=15, bold=True, name="pr-recon")
    c = dk.box(s, 9.6, 2.3, 3.0, 1.1, "reserve-engine", fill=NAVY, line=None, color=WHITE, size=15, bold=True,
               name="pr-engine")
    dk.connect(s, a, b, 3, 1, label="CLARA side", label_offset=(0, -0.36))
    dk.connect(s, c, b, 1, 3, label="engine side", label_offset=(0, -0.36))
    dk.text(s, 0.8, 4.0, 11.8, 2.3,
            [f"Reserve parallel run: {fmt_date(pr['from'])} to {fmt_date(pr['to'])}",
             "Variances are investigated by the squad with Reserving before sign-off",
             f"Go-live of the engine as system of record: Wave 1 (UK motor), {fmt_date(W.waves['MW-1']['date'])}"],
            size=16, bullets=True, para_space=10)
    dk.fact("general", "Reserve parallel run runs from 2 March 2026 to 28 August 2026.", 13, "text",
            "Reserve parallel run: 2 March 2026 to 28 August 2026", world_ref="TIMELINE:programme#parallel_run.from")

    # 14 open items
    s = dk.new_slide("Open items for the Design Authority")
    rows = [["#", "Item", "Proposed owner"],
            ["1", "Revaluation approach for Nordic reserves (CLRGL090 equivalent) and audit finding IA-25-07",
             W.name_of("P009", d)],
            ["2", "Retention of reserve.changed.v2 history for reconciliation", W.name_of("P041", d)],
            ["3", "Approval queue user experience for above-authority movements", W.name_of("P017", d)],
            ["4", "Alerting on rejected movements from the bridge", W.name_of("P031", d)]]
    dk.table(s, rows, col_w=[0.5, 8.5, 3.0], size=14, row_h=0.62, name="Open items")
    dk.notes(s, "Item 1 goes to the Reserving design review planned for early March with the Design Authority.")

    # 15 risks
    risks_slide(dk, k=4, extra=[("Variances in the parallel run caused by CLARA-only update paths",
                                  "Document every CLARA writer and reconcile at movement level")])
    # 16 glossary
    glossary_slide(dk, [("reserve-engine", "Claims Hub reserve service (named reserve-svc until 2026-02-10)"),
                        ("Movement", "A recorded change to a reserve amount; every change to money is a movement"),
                        ("Tier-3", "Claims meeting the BR-TRI-003 Tier-3 criteria"),
                        ("LLNT", "Large Loss Notification Threshold used by BR-RSV-011"),
                        ("ESP", "Event Streaming Platform (Kafka)"),
                        ("reserve table", "Dashboard term for the reserve records held by the engine")])
    return dk


# =========================================================================================
# VS017 CLARA Batch Landscape (2026-05-18)
# =========================================================================================
_AREA = [("FN", "Intake"), ("TR", "Triage"), ("AS", "Assessment"), ("RSV", "Reserving"), ("FR", "Fraud"),
         ("STL", "Settlement & payments"), ("PAY", "Settlement & payments"), ("RC", "Recoveries"),
         ("GL", "Finance & GL"), ("RP", "Reporting & MI"), ("MI", "Reporting & MI"), ("CM", "Housekeeping")]


def _job_area(name):
    core = name[4:]
    for key, area in _AREA:
        if core.startswith(key):
            return area
    return "Other"


def _active_jobs(W, d):
    out = []
    for n, j in W.jcl_jobs.items():
        if j["status"] == "disabled":
            continue
        if any(str(W.programs[s["program"]].get("since", "1900")) > d for s in j["steps"]):
            continue
        if j["status"] == "retired" and "2026-08-28" < d:
            continue
        out.append(n)
    return out


def build_vs017(W, out_dir):
    fid = "VS017"
    dk = Deck(W, fid, out_dir, short_title="CLARA Batch Landscape")
    d = dk.date
    assert not W.may_state(fid, "JCL:CLRNRSV3", "schedule")
    assert not W.may_state(fid, "INTERFACE:CLX-IF-042", "schedule")
    assert not W.may_state(fid, "JCL:CLRNRSV1", "restart")
    guard(W, fid, [("JCL:CLRYGL90", "schedule"), ("JCL:CLRMRSV1", "schedule"), ("JCL:CLRNRSV1", "schedule"),
                   ("PROGRAM:CLRGL090", "writes_tables:CLR.T_RESERVE"), ("PROGRAM:CLRRS130", "writes_tables:CLR.T_RESERVE"),
                   ("SYSTEM:SYS01", "batch_window"), ("SYSTEM:SYS18", "decommission_target"),
                   ("PROGRAM:CLRGL090", "renamed_from")])
    jobs = _active_jobs(W, d)
    J = W.jcl_jobs

    # 1 title
    s = dk.title_slide("CLARA Batch Landscape", "Jobs, chains, writers and the overnight window",
                       [f"Owner: {person(W, 'P026', d)}",
                        f"Mainframe Batch Operations  |  {fmt_date(d)}  |  Classification: Internal"])
    # 2 document control
    appr = approvers(W, d, ["P016", "P023", "P031"], minus_days(d, 2))
    dk.doc_control_slide("CLR-OPS-BATCH-LAND", person(W, "P026", d), appr,
                         history(dk, ["P026", "P023", "P026"], spans=(30, 16, 5)),
                         "Mainframe Batch Operations, Legacy Claims Platforms, Integration Platform, "
                         "Programme Skerry architects")
    # 3 scope
    s = dk.new_slide("Scope")
    sys01 = W.systems["SYS01"]
    items = [f"All CLARA JCL jobs driven by the Batch Scheduler (owner team: Mainframe Batch Operations)",
             f"Overnight batch window: {sys01['batch_window']}",
             f"{len(jobs)} active jobs as at {fmt_date(d)}; chains, writers to the reserve table and interface hand-offs",
             "Excludes ad-hoc utilities and one-off data fixes",
             "Interface timings are taken from the interface catalogue, which remains the master"]
    dk.bullets(s, items, size=17)
    dk.fact("general", "CLARA's overnight batch window is 23:30–05:30 UK time.", 3, "text",
            "Overnight batch window: 23:30–05:30 UK time", world_ref="SYSTEM:SYS01#batch_window")

    # 4 inventory chart
    s = dk.new_slide("Job inventory by area")
    counts = {}
    for n in jobs:
        counts[_job_area(n)] = counts.get(_job_area(n), 0) + 1
    cats = sorted(counts, key=lambda k: (-counts[k], k))
    dk.chart(s, "bar", cats, {"Active jobs": [counts[c] for c in cats]}, CONTENT_LEFT + 0.5, CONTENT_TOP,
             9.5, 5.4, title="Active CLARA jobs by functional area", number_format="0", legend=False,
             name="inventory-chart")
    dk.text(s, 10.3, CONTENT_TOP + 0.6, 2.5, 3.0,
            ["Counts include the reserve parallel-run reconciliation job, which runs only until the end of the "
             "parallel run."], size=12, color=GREY)
    dk.fact("chart_only", f"Chart: Reserving has {counts['Reserving']} active jobs.", 4, "chart",
            f"Active jobs: Reserving={counts['Reserving']}", world_ref="JCL:CLRNRSV1")

    # 5 reserve writers (PL-110, PL-111, PL-112)
    s = dk.new_slide("Who writes the reserve table", "Programs grouped by the job or transaction that runs them")
    tres = dk.box(s, 10.0, 1.7, 2.6, 2.9, "CLR.T_RESERVE", shape=MSO_SHAPE.CAN, fill=GREY_LT, line=NAVY, size=15,
                  bold=True, name="tbl-T_RESERVE")
    tmov = dk.box(s, 10.0, 5.0, 2.6, 1.5, "CLR.T_RESERVE_MOVEMENT", shape=MSO_SHAPE.CAN, fill=GREY_LT, line=NAVY,
                  size=11, bold=True, name="tbl-T_RESERVE_MOVEMENT")
    groups = [("Online (CICS)", ["CLRFN030", "CLRRS010", "CLRRS020"]),
              (f"CLRNRSV1 ({J['CLRNRSV1']['schedule']})", ["CLRRS110"]),
              (f"CLRMRSV1 ({J['CLRMRSV1']['schedule']})", ["CLRRS130"]),
              (f"CLRNSTL1 ({J['CLRNSTL1']['schedule']})", ["CLRST040"]),
              (f"CLRNRC01 ({J['CLRNRC01']['schedule']})", ["CLRRC050"]),
              ("CLRYGL90 (annually 31 Dec 23:30)", ["CLRGL090"]),
              (f"CLRNRSV2 ({J['CLRNRSV2']['schedule']})", ["CLRRS150"])]
    assert J["CLRYGL90"]["schedule"].startswith("annually 31 Dec 23:30")
    progbox = {}
    y = 1.42
    row = 0.48
    for gi, (gname, progs) in enumerate(groups):
        gn = "grp-" + gname.split(" ")[0] if not gname.startswith("Online") else "grp-online"
        g = dk.group(s, gn)
        h = 0.14 + row * len(progs)
        dk.box(s, 0.55, y, 4.4, h, "", shape=MSO_SHAPE.RECTANGLE, fill=WHITE, line=GREY, group=g,
               name=f"{gn}-frame", dashed=True)
        dk.text(s, 0.6, y + 0.04, 2.4, h - 0.08, gname, size=10, bold=True, color=GREY, group=g,
                name=f"{gn}-title", anchor=MSO_ANCHOR.MIDDLE)
        for k, p in enumerate(progs):
            progbox[p] = dk.box(s, 3.1, y + 0.07 + k * row, 1.7, row - 0.08, p, size=11, bold=True, group=g,
                                name=f"prog-{p}")
        y += h + 0.06
    labels = {"CLRFN030": "INSERT (default reserve at FNOL)", "CLRRS010": "INSERT (initial reserve)",
              "CLRRS020": "UPDATE (adjustment)", "CLRRS110": "UPDATE (Tier-3 review)",
              "CLRRS130": "UPDATE (monthly index)", "CLRST040": "UPDATE (close-down)",
              "CLRRC050": "UPDATE (recovery netting)", "CLRGL090": "UPDATE (year-end)"}
    assert set(labels) == set(W.reserve_writers)
    for p in W.reserve_writers:
        dk.connect(s, progbox[p], tres, 3, 1, label=labels[p], name=f"w-{p}", label_size=8, width_pt=1.0,
                   label_w=2.1, label_offset=(0.0, -0.13), label_t=0.22, label_fill=None)
    dk.connect(s, progbox["CLRRS150"], tmov, 3, 1, label="INSERT (corrections only)", name="w-CLRRS150",
               label_size=8, width_pt=1.0, label_w=2.0, label_offset=(0.0, -0.13), label_t=0.22, color=TEAL,
               label_fill=None)
    dk.fact("arrow_only", "Connector CLRGL090 → CLR.T_RESERVE labelled 'UPDATE (year-end)'.", 5, "connector",
            "CLRGL090 -> CLR.T_RESERVE [label: UPDATE (year-end)]", placement="PL-110", shape_name="w-CLRGL090")
    dk.fact("arrow_only", "Connector CLRRS130 → CLR.T_RESERVE labelled 'UPDATE (monthly index)'.", 5, "connector",
            "CLRRS130 -> CLR.T_RESERVE [label: UPDATE (monthly index)]", placement="PL-111", shape_name="w-CLRRS130")
    dk.fact("visual_only", "Group 'CLRYGL90 (annually 31 Dec 23:30)' contains step CLRGL090.", 5, "group",
            "CLRYGL90 (annually 31 Dec 23:30) CLRGL090", placement="PL-112", shape_name="grp-CLRYGL90")
    for p in ["CLRFN030", "CLRRS010", "CLRRS020", "CLRRS110", "CLRST040", "CLRRC050"]:
        dk.fact("arrow_only", f"Connector {p} → CLR.T_RESERVE labelled '{labels[p]}' (reserve-table writer).", 5,
                "connector", f"{p} -> CLR.T_RESERVE [label: {labels[p]}]",
                world_ref=f"PROGRAM:{p}#writes_tables:CLR.T_RESERVE", shape_name=f"w-{p}")
    dk.fact("arrow_only", "CLRRS150 writes only CLR.T_RESERVE_MOVEMENT (corrections), not CLR.T_RESERVE.", 5,
            "connector", "CLRRS150 -> CLR.T_RESERVE_MOVEMENT [label: INSERT (corrections only)]",
            world_ref="PROGRAM:CLRRS150#writes_tables", shape_name="w-CLRRS150")
    dk.fact("visual_only", "Group 'CLRMRSV1 (1st business day 03:00)' contains CLRRS130.", 5, "group",
            "CLRMRSV1 (1st business day 03:00) CLRRS130", world_ref="JCL:CLRMRSV1#schedule", shape_name="grp-CLRMRSV1")
    dk.notes(s, "Eight programs write CLR.T_RESERVE. CLRGL090 (formerly YEREVAL1, renamed 2021-01-01) updates "
                "RSV_GBP_EQUIV_AMT and RSV_LAST_REVAL_DT without writing CLR.T_RESERVE_MOVEMENT, which is internal "
                "audit finding IA-25-07. CLRRS150 only touches the movement table.")
    dk.fact("speaker_notes", "Speaker notes: CLRGL090 was formerly YEREVAL1, renamed 2021-01-01.", 5, "notes",
            "CLRGL090 (formerly YEREVAL1, renamed 2021-01-01)", world_ref="PROGRAM:CLRGL090#renamed_from")
    dk.fact("speaker_notes", "Speaker notes: CLRGL090 updates RSV_GBP_EQUIV_AMT and RSV_LAST_REVAL_DT without writing "
                             "CLR.T_RESERVE_MOVEMENT (IA-25-07).", 5, "notes",
            "updates RSV_GBP_EQUIV_AMT and RSV_LAST_REVAL_DT without writing CLR.T_RESERVE_MOVEMENT",
            world_ref="PROGRAM:CLRGL090#notes")

    # 6 job step chains
    s = dk.new_slide("Job step chains", "Each arrow is the next step in the same job")
    chains = ["CLRNTR01", "CLRNFR01", "CLRNRC01", "CLRNGL01"]
    for ci, jn in enumerate(chains):
        y0 = 1.65 + ci * 1.3
        dk.text(s, 0.55, y0 + 0.12, 1.6, 0.5, jn, size=14, bold=True, color=NAVY, name=f"chain-{jn}")
        prev = None
        for k, st in enumerate(J[jn]["steps"]):
            b = dk.box(s, 2.3 + k * 2.65, y0, 1.9, 0.72, st["program"], size=13, bold=True,
                       name=f"step-{jn}-{st['step']}")
            if prev is not None:
                dk.connect(s, prev[0], b, 3, 1, label=st["step"], label_size=9, label_w=0.85,
                           label_offset=(0, -0.3), name=f"c-{jn}-{st['step']}")
                dk.fact("arrow_only", f"In job {jn}, {st['program']} ({st['step']}) follows {prev[1]}.", 6,
                        "connector", f"{prev[1]} -> {st['program']} [label: {st['step']}]",
                        world_ref=f"JCL:{jn}#steps", shape_name=f"c-{jn}-{st['step']}")
            prev = (b, st["program"])
    dk.notes(s, "Restart rules live in the job documentation. For the reserve movement extract, CLRRS170 only "
                "extracts rows with EXTRACTED_FLAG = 'N', so a rerun of that job does not duplicate records.")
    dk.fact("speaker_notes", "Speaker notes: CLRRS170 only extracts rows with EXTRACTED_FLAG = 'N'.", 6, "notes",
            "CLRRS170 only extracts rows with EXTRACTED_FLAG = 'N'", world_ref="JCL:CLRNRSV3#restart")

    # 7 swimlane: nightly window by area (owner by lane position, time by x)
    s = dk.new_slide("The night by area", "Lane = functional area; position = scheduled start")
    lanes = ["Intake & triage", "Assessment", "Fraud", "Reserving", "Settlement & payments", "Recoveries",
             "Finance & GL", "Reporting & MI"]
    lane_jobs = {"Intake & triage": ["CLRNFN01", "CLRNTR01", "CLRNFN02"], "Assessment": ["CLRNAS01", "CLRNAS02"],
                 "Fraud": ["CLRNFR01", "CLRNFR02"], "Reserving": ["CLRNRSV1", "CLRNRSV2", "CLRDRSV9", "CLRNRSV4"],
                 "Settlement & payments": ["CLRNSTL1", "CLRNPAY2"], "Recoveries": ["CLRNRC01"],
                 "Finance & GL": ["CLRNGL01"], "Reporting & MI": ["CLRNRP01", "CLRNMI01"]}
    assert "CLRNRSV3" not in sum(lane_jobs.values(), [])
    x0, x1, top, lh = 1.05, 12.75, 1.5, 0.64

    def tx(hhmm):
        h, m = map(int, hhmm.split(":"))
        mins = (h * 60 + m - 21 * 60) % (24 * 60)
        return x0 + 0.5 + (x1 - x0 - 0.9) * mins / (10.5 * 60)

    bw = 0.78
    for i, ln in enumerate(lanes):
        band = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, *(map(lambda v: int(v * 914400),
                                                              (x0, top + i * lh, x1 - x0, lh))))
        band.fill.solid()
        band.fill.fore_color.rgb = [GREY_LT, WHITE][i % 2]
        band.line.color.rgb = GREY_LT
        band.name = f"lane-{i + 1}"
        dk.text(s, 0.05, top + i * lh + 0.12, 1.0, 0.4, ln, size=8, bold=True, color=NAVY, name=f"lanehdr-{i + 1}",
                align=PP_ALIGN.RIGHT)
        last_right = [-9.0, -9.0]
        for jn in lane_jobs[ln]:
            hhmm = re.search(r"\d\d:\d\d", J[jn]["schedule"]).group(0)
            xx = tx(hhmm) - bw / 2
            sub = 0 if xx > last_right[0] + 0.03 else 1
            last_right[sub] = xx + bw
            yy = top + i * lh + 0.04 + sub * 0.29
            dk.box(s, xx, yy, bw, 0.27, jn, size=7, bold=True, name=f"job-{jn}")
    for hh in ["21:00", "23:00", "01:00", "03:00", "05:00", "07:00"]:
        dk.text(s, tx(hh) - 0.4, top + 8 * lh + 0.05, 0.8, 0.3, hh, size=10, color=GREY, align=PP_ALIGN.CENTER,
                name=f"tick-{hh}")
    dk.fact("lane_only", "CLRNRC01 sits in the Recoveries lane (area only by lane position).", 7, "text", "CLRNRC01",
            world_ref="JCL:CLRNRC01#description", notes="Lane membership is given only by vertical position.")
    dk.fact("lane_only", "CLRDRSV9 (parallel-run reconciliation) sits in the Reserving lane.", 7, "text", "CLRDRSV9",
            world_ref="JCL:CLRDRSV9", notes="Lane membership is given only by vertical position.")
    dk.notes(s, "The reserve movement extract is deliberately not drawn here; its timing is governed by the interface "
                "catalogue entry for CLX-IF-042. CLRDRSV9 only runs for the reserve parallel run, from 2 March to "
                "28 August 2026.")
    dk.fact("speaker_notes", "Speaker notes: CLRDRSV9 runs only for the reserve parallel run (2 March to 28 August "
                             "2026).", 7, "notes", "CLRDRSV9 only runs for the reserve parallel run",
            world_ref="JCL:CLRDRSV9#schedule")

    # 8 batch window raster
    s = dk.new_slide("Interface hand-offs around the batch window")
    cv = R.Canvas(1700, 900)
    cv.title("Overnight window and interface times (UK time)")
    ax_y = 470

    def rx(hhmm):
        h, m = map(int, hhmm.split(":"))
        mins = (h * 60 + m - 21 * 60) % (24 * 60)
        return 80 + 1540 * mins / (9.5 * 60)

    cv.d.rectangle([rx("23:30"), ax_y - 26, rx("05:30"), ax_y + 26], fill=R.TEAL_LT, outline=R.TEAL, width=2)
    cv.text(((rx("23:30") + rx("05:30")) / 2, ax_y - 15), "CLARA batch window 23:30–05:30", size=24, bold=True,
            fill=R.NAVY, anchor="ma")
    cv.d.line([(80, ax_y + 40), (1620, ax_y + 40)], fill=R.GREY, width=3)
    for hh in ["21:00", "23:00", "01:00", "03:00", "05:00", "06:30"]:
        cv.text((rx(hh), ax_y + 52), hh, size=22, fill=R.GREY, anchor="ma")
    items = [("CLX-IF-003", "21:45", "policy snapshot"), ("CLX-IF-009", "00:15", "Sentinel batch"),
             ("CLX-IF-027", "03:15", "currency rates"), ("CLX-IF-043", "03:45", "GL reserve journal"),
             ("CLX-IF-044", "04:00", "CDW reserve facts"), ("CLX-IF-030", "04:30", "daily MI")]
    tiers_up, tiers_dn = [120, 240, 360], [580, 690, 800]
    used = {"up": [], "dn": []}
    for k, (iid, hh, lab) in enumerate(items):
        assert W.interface_schedule(iid, d).endswith(hh), (iid, hh)
        x = rx(hh)
        side = "up" if k % 2 == 0 else "dn"
        tiers = tiers_up if side == "up" else tiers_dn
        t = 0
        while any(abs(x - ux) < 300 and ut == t for ux, ut in used[side]):
            t += 1
        used[side].append((x, t))
        y_lab = tiers[t]
        if side == "up":
            cv.arrow((x, y_lab + 70), (x, ax_y - 30), color=R.NAVY, width=3)
        else:
            cv.arrow((x, y_lab - 6), (x, ax_y + 34), color=R.NAVY, width=3)
        cv.text((x, y_lab), f"{iid} {hh}", size=24, bold=True, fill=R.NAVY, anchor="ma")
        cv.text((x, y_lab + 32), lab, size=22, fill=R.GREY, anchor="ma")
    dk.picture(s, cv.png(), CONTENT_LEFT, CONTENT_TOP, w=CONTENT_W,
               alt="Timeline of the overnight batch window with arrows marking interface hand-off times.",
               name="window-image")
    dk.fact("image_text", "Batch window image: CLX-IF-043 (GL reserve journal) at 03:45.", 8, "image",
            "CLX-IF-043 03:45", world_ref="INTERFACE:CLX-IF-043#schedule_history")
    dk.fact("image_text", "Batch window image: CLX-IF-027 currency rates at 03:15.", 8, "image", "CLX-IF-027 03:15",
            world_ref="INTERFACE:CLX-IF-027#schedule")
    dk.fact("alt_text", "Alt text: overnight batch window timeline with interface hand-off times.", 8, "alt_text",
            "arrows marking interface hand-off times")

    # 9 periodic jobs
    s = dk.new_slide("Weekly, monthly, quarterly and annual jobs")
    per = [n for n in jobs if not n.startswith("CLRN") and n != "CLRDRSV9"]
    rows = [["Job", "Description", "Schedule", "Programs"]]
    for n in per:
        sch = J[n]["schedule"] if n != "CLRYGL90" else "see writer map (slide 5)"
        rows.append([n, J[n]["description"], sch, ", ".join(st["program"] for st in J[n]["steps"])])
    dk.table(s, rows, col_w=[1.3, 4.2, 3.4, 3.2], size=11, row_h=0.4, name="Periodic jobs")
    dk.fact("general", "CLRMGL01 (GL month-end) runs on the last business day at 23:00.", 9, "table",
            "CLRMGL01 GL month-end last business day 23:00", world_ref="JCL:CLRMGL01#schedule")
    dk.fact("general", "CLRWRC01 (subrogation demand letters) runs Tue and Thu at 05:00.", 9, "table",
            "CLRWRC01 Subrogation demand letters Tue,Thu 05:00", world_ref="JCL:CLRWRC01#schedule")

    # 10 interfaces fed by batch (table image)
    s = dk.new_slide("Interfaces driven by batch steps")
    rows = [["Job", "Step program", "Interface", "Partner system"]]
    for n in jobs:
        for st in J[n]["steps"]:
            for iid, it in W.interfaces.items():
                if iid == "CLX-IF-042" or st["program"] not in it.get("programs", []):
                    continue
                if str(it.get("since", "1900")) > d or it["schedule"] in ("real-time", "on demand"):
                    continue
                other = it["target_system"] if it["source_system"] == "SYS01" else it["source_system"]
                rows.append([n, st["program"], iid, W.system_name(other, d)])
    png = R.table_image(rows, [230, 260, 230, 420], title="Batch-driven interfaces", size=24, row_h=46)
    dk.picture(s, png, CONTENT_LEFT + 1.4, CONTENT_TOP - 0.05, h=5.55,
               alt="Table image listing batch jobs, step programs, interfaces and partner systems.",
               name="interfaces-table-image")
    dk.fact("image_table", "Table image: CLRNRSV4 step CLRRS160 drives CLX-IF-031 to ReCede.", 10, "image",
            "CLRNRSV4", world_ref="INTERFACE:CLX-IF-031#programs")
    dk.fact("image_table", "Table image: CLRNRC01 step CLRRC040 drives CLX-IF-022 to the Subrogation Tracker.", 10,
            "image", "Subrogation Tracker", world_ref="INTERFACE:CLX-IF-022")

    # 11 support model (group)
    s = dk.new_slide("Support model")
    tiers = [("First line", "Mainframe Batch Operations", "Monitors the scheduler, restarts per job documentation"),
             ("Second line", "Legacy Claims Platforms (CLARA)", "Program fixes, data corrections, DB2 support"),
             ("Interfaces", "Integration Platform", "MQ Backbone channels and interface catalogue"),
             ("Escalation", "Duty manager", "Customer- or finance-impacting failures")]
    for i, (lvl, team, what) in enumerate(tiers):
        g = dk.group(s, f"grp-support-{i + 1}")
        x = CONTENT_LEFT + i * 3.07
        dk.box(s, x, CONTENT_TOP + 0.3, 2.9, 0.65, lvl, shape=MSO_SHAPE.RECTANGLE, fill=NAVY, line=None, color=WHITE,
               size=15, bold=True, group=g, name=f"support-lvl-{i + 1}")
        dk.box(s, x, CONTENT_TOP + 1.0, 2.9, 2.6, [team, what], shape=MSO_SHAPE.RECTANGLE, fill=TEAL_LT, line=None,
               size=14, bold=True, group=g, anchor=MSO_ANCHOR.TOP, name=f"support-body-{i + 1}")
    dk.text(s, CONTENT_LEFT, 5.3, CONTENT_W, 1.2, PH.pick(dk.rng, PH.SUPPORT, 2), size=14, bullets=True, color=GREY)

    # 12 decommissioning outlook
    s = dk.new_slide("Outlook: batch after cut-over")
    items = [f"Batch Scheduler decommission target: {fmt_date(W.systems['SYS18']['decommission_target'])} "
             "(with CLARA)",
             f"Wave 1 (UK motor) cut-over on {fmt_date(W.waves['MW-1']['date'])} moves UK motor volumes off CLARA",
             "reserve-engine revaluation run replaces CLRGL090 from Wave 2 (ADR-028); CLRGL090 stays unchanged in "
             "CLARA until then",
             "Read-only CLARA enquiry after cut-over is proposed (ADR-026)",
             "Every retired job needs its downstream consumers confirmed before it is removed"]
    dk.bullets(s, items, size=16)
    dk.fact("general", "From Wave 2 the reserve-engine revaluation run replaces CLRGL090 (ADR-028).", 12, "text",
            "reserve-engine revaluation run replaces CLRGL090 from Wave 2 (ADR-028)", world_ref="ADR:ADR-028")

    # 13-14 appendix job list
    allrows = []
    for n in jobs:
        sch = J[n]["schedule"] if n != "CLRNRSV3" else "per CLX-IF-042 catalogue entry"
        allrows.append([n, J[n]["description"], sch, ", ".join(st["program"] for st in J[n]["steps"])])
    half = (len(allrows) + 1) // 2
    for part, chunk in enumerate([allrows[:half], allrows[half:]], 1):
        s = dk.new_slide(f"Appendix – active job list ({part}/2)")
        dk.table(s, [["Job", "Description", "Schedule", "Programs"]] + chunk, col_w=[1.3, 4.3, 3.2, 3.4], size=10,
                 row_h=0.31, name=f"Job list {part}")
    dk.fact("general", "CLRNRSV3 runs the reserve movement extract (CLX-IF-042) with step CLRRS170.",
            dk.n - 1 if "CLRNRSV3" in [r[0] for r in allrows[:half]] else dk.n, "table",
            "CLRNRSV3 Reserve movement extract (CLX-IF-042)", world_ref="JCL:CLRNRSV3#description")
    return dk


# =========================================================================================
# VS018 Claims Assessor Vendor Panel 2025 (2025-01-20)
# =========================================================================================
def build_vs018(W, out_dir):
    fid = "VS018"
    dk = Deck(W, fid, out_dir, short_title="Assessor Vendor Panel 2025")
    d = dk.date
    V = W.vendors
    assert not W.may_state(fid, "VENDOR:VEN-02", "fees")
    guard(W, fid, [("VENDOR:VEN-01", "fees"), ("VENDOR:VEN-03", "fees"), ("VENDOR:VEN-01", "sla"),
                   ("VENDOR:VEN-03", "panel_to"), ("VENDOR:VEN-02", "sla")])
    assert W.system_name("SYS17", d) == "Adjuster Extranet"
    on_panel = [v for v in V.values() if v["panel_from"] <= d and (v["panel_to"] is None or v["panel_to"] >= d)]
    assert "VEN-03" in [v["id"] for v in on_panel]

    s = dk.title_slide("Claims Assessor Vendor Panel 2025", "Panel composition, fees, service levels and allocation",
                       [f"Owner: {person(W, 'P033', d)}",
                        f"Claims Assessment UK  |  {fmt_date(d)}  |  Classification: Internal"])
    appr = approvers(W, d, ["P011", "P005"], minus_days(d, 3))
    dk.doc_control_slide("CLM-ASM-PANEL-2025", person(W, "P033", d), appr,
                         history(dk, ["P033", "P034", "P033"], spans=(26, 12, 4)),
                         "Claims Assessment UK, Claims Assessment Nordics, Claims Operations UK, Procurement")

    # 3 panel table (PL-113)
    s = dk.new_slide("The external Claims Assessor panel – January 2025")
    rows = [["Vendor", "Scope", "Base", "On panel since"]]
    scope = {"VEN-01": "UK property and motor", "VEN-02": "Sweden and Norway", "VEN-03": "Major-loss adjusters (UK)"}
    for vid in ["VEN-01", "VEN-02", "VEN-03"]:
        v = V[vid]
        rows.append([v["name"], scope[vid], v["location"], fmt_date(v["panel_from"], "short")])
    dk.table(s, rows, col_w=[4.0, 3.6, 1.8, 2.2], size=15, row_h=0.62, name="Panel table")
    dk.text(s, CONTENT_LEFT, 4.3, CONTENT_W, 1.6,
            ["Internal Claims Assessors in Leeds and Oslo handle the majority of inspections; the panel covers "
             "overflow, specialist and major-loss work.",
             "All panel instructions are issued and returned through the Adjuster Extranet."],
            size=15, color=GREY, bullets=True)
    dk.fact("contradiction_old", "January 2025 panel includes Fellgate Adjusting Partners LLP for major loss.", 3,
            "table", "Fellgate Adjusting Partners LLP Major-loss adjusters (UK)", placement="PL-113")
    dk.fact("general", "Brackenfield Loss Adjusting Ltd (Manchester) covers UK property and motor, on the panel since "
                       "1 Apr 2017.", 3, "table",
            "Brackenfield Loss Adjusting Ltd UK property and motor Manchester 1 Apr 2017", world_ref="VENDOR:VEN-01")
    dk.fact("general", "Norrvik Skadetaxering AB (Gothenburg) covers Sweden and Norway.", 3, "table",
            "Norrvik Skadetaxering AB Sweden and Norway Gothenburg", world_ref="VENDOR:VEN-02#role")
    dk.notes(s, "Fellgate takes our major-loss instructions in the UK. Brackenfield remains the main UK partner. "
                "Norrvik is the sole external partner for the Nordics.")

    # 4 coverage raster
    s = dk.new_slide("Coverage")
    cv = R.Canvas(1600, 820)
    cv.title("Who covers what")
    cv.box(80, 130, 620, 620, "", fill=R.GREY_LT, outline=R.GREY_MD)
    cv.text((390, 145), "United Kingdom", size=28, bold=True, fill=R.NAVY, anchor="ma")
    cv.box(900, 130, 620, 620, "", fill=R.GREY_LT, outline=R.GREY_MD)
    cv.text((1210, 145), "Nordics", size=28, bold=True, fill=R.NAVY, anchor="ma")
    cv.box(140, 230, 500, 90, ["Brackenfield (Manchester)"], size=26)
    cv.box(140, 420, 500, 90, ["Fellgate (London)"], size=26)
    cv.box(140, 610, 500, 90, ["Claims Assessment UK (Leeds)"], size=24, fill=R.WHITE)
    cv.box(960, 230, 500, 90, ["Norrvik (Gothenburg)"], size=26)
    cv.box(960, 610, 500, 90, ["Claims Assessment Nordics (Oslo)"], size=22, fill=R.WHITE)
    cv.arrow((640, 275), (900, 275), label="no Nordic work", label_size=22, dashed=True, color=R.GREY)
    cv.text((390, 330), "property and motor", size=24, fill=R.GREY, anchor="ma")
    cv.text((390, 520), "major loss", size=24, fill=R.GREY, anchor="ma")
    cv.text((1210, 330), "Sweden and Norway", size=24, fill=R.GREY, anchor="ma")
    cv.arrow((1210, 380), (1210, 600), label="overflow and specialist", label_size=22, label_offset=(0, -20))
    dk.picture(s, cv.png(), CONTENT_LEFT + 0.6, CONTENT_TOP, h=5.5,
               alt="Coverage map: Brackenfield and Fellgate in the UK, Norrvik for Sweden and Norway, internal "
                   "assessors in Leeds and Oslo.", name="coverage-image")
    dk.fact("image_text", "Coverage image: Fellgate (London) covers UK major loss.", 4, "image", "Fellgate (London)",
            world_ref="VENDOR:VEN-03#location")
    dk.fact("alt_text", "Alt text: internal assessors are based in Leeds and Oslo.", 4, "alt_text",
            "internal assessors in Leeds and Oslo")

    # 5 fees chart (chart only)
    s = dk.new_slide("Panel fee schedule")
    b, f = V["VEN-01"]["fees"], V["VEN-03"]["fees"]
    dk.chart(s, "column", ["Brackenfield desk assessment", "Brackenfield site visit", "Brackenfield major loss (hour)",
                           "Fellgate major loss (hour)"],
             {"Fee (GBP)": [b["desk_assessment_gbp"], b["site_visit_gbp"], b["major_loss_hourly_gbp"],
                            f["major_loss_hourly_gbp"]]},
             CONTENT_LEFT + 0.6, CONTENT_TOP, 10.5, 5.4, title="Agreed fees, UK panel (GBP)", number_format="£#,##0",
             legend=False, name="fees-chart")
    dk.text(s, CONTENT_LEFT, 6.55, CONTENT_W, 0.35, "Nordic fees are held in the Norrvik agreement and are not shown.",
            size=12, color=GREY, italic=True)
    dk.fact("chart_only", "Chart: Brackenfield site visit fee £420.", 5, "chart", "Brackenfield site visit=420",
            world_ref="VENDOR:VEN-01#fees.site_visit_gbp")
    dk.fact("chart_only", "Chart: Fellgate major-loss hourly rate £165.", 5, "chart", "Fellgate major loss (hour)=165",
            world_ref="VENDOR:VEN-03#fees.major_loss_hourly_gbp")
    dk.fact("chart_only", "Chart: Brackenfield desk assessment fee £185.", 5, "chart",
            "Brackenfield desk assessment=185", world_ref="VENDOR:VEN-01#fees.desk_assessment_gbp")

    # 6 SLA table image
    s = dk.new_slide("Service levels")
    a5 = W.rule_version("BR-ASM-005", d)
    a4 = W.rule_version("BR-ASM-004", d)
    rows = [["Measure", "Standard", "Source"],
            ["Appointment after triage", "2 business days", "BR-ASM-002"],
            ["Brackenfield desk assessment", "2 business days", "Contract"],
            ["Brackenfield site visit", "5 business days", "Contract"],
            ["Brackenfield report", "5 business days", "Contract"],
            ["Norrvik site visit", "5 business days", "Contract"],
            ["Site inspection (Tier-3)", "72 hours", f"BR-ASM-005 v{a5['version']}"],
            ["Report after inspection", "5 business days", "BR-ASM-006"],
            ["Photos per report (minimum)", "6", f"BR-ASM-004 v{a4['version']}"]]
    assert "72 hours" in a5["text"] and "6 photos" in a4["text"]
    png = R.table_image(rows, [520, 330, 300], title="Panel service levels", size=26, row_h=52)
    dk.picture(s, png, CONTENT_LEFT + 1.8, CONTENT_TOP - 0.05, h=5.5,
               alt="Service level table for panel assessors.", name="sla-image")
    dk.fact("image_table", "SLA image: Tier-3 site inspection within 72 hours (BR-ASM-005 v2).", 6, "image",
            "72 hours", world_ref="RULE:BR-ASM-005@v2")
    dk.fact("image_table", "SLA image: Brackenfield site visit within 5 business days.", 6, "image",
            "Brackenfield site visit", world_ref="VENDOR:VEN-01#sla.site_visit_business_days")

    # 7 allocation rules
    s = dk.new_slide("How instructions are allocated")
    rr = {r: W.rule_version(r, d)["text"].rstrip(".") for r in ["BR-ASM-002", "BR-ASM-015", "BR-ASM-016", "BR-ASM-001",
                                                    "BR-ASM-008", "BR-ASM-003"]}
    items = [rr["BR-ASM-015"] + " (BR-ASM-015)", rr["BR-ASM-016"] + " (BR-ASM-016)",
             rr["BR-ASM-002"] + " (BR-ASM-002)", rr["BR-ASM-001"] + " (BR-ASM-001)",
             rr["BR-ASM-008"].replace("Evidence Intake Gateway", "Evidence Intake Gateway") + " (BR-ASM-008)",
             rr["BR-ASM-003"] + " (BR-ASM-003 v2, from 1 January 2025)"]
    dk.bullets(s, items, size=14)
    dk.fact("general", "Escape of Water claims below £7,500 may be assessed by video call (BR-ASM-003 v2).", 7, "text",
            "Escape of Water claims below £7500 may be assessed by video call", world_ref="RULE:BR-ASM-003@v2")
    dk.fact("general", "All external Nordic instructions go to Norrvik Skadetaxering (BR-ASM-016).", 7, "text",
            "All external Nordic instructions go to Norrvik Skadetaxering", world_ref="RULE:BR-ASM-016@v1")

    # 8 instruction flow (connectors)
    s = dk.new_slide("Instruction and report flow", "Interface numbers and schedules on the arrows")
    dk.box(s, 0.6, 1.7, 3.6, 4.7, "CLARA", shape=MSO_SHAPE.RECTANGLE, fill=GREY_LT, line=GREY, size=15, bold=True,
           anchor=MSO_ANCHOR.TOP, name="container-clara")
    a30 = dk.box(s, 1.0, 2.4, 2.8, 0.7, "CLRAS030", name="p-CLRAS030")
    a40 = dk.box(s, 1.0, 3.7, 2.8, 0.7, "CLRAS040", name="p-CLRAS040")
    a70 = dk.box(s, 1.0, 5.0, 2.8, 0.7, "CLRAS070", name="p-CLRAS070")
    ext = dk.box(s, 6.9, 3.2, 2.4, 1.5, "Adjuster Extranet", fill=NAVY, line=None, color=WHITE, size=16, bold=True,
                 name="sys-extranet")
    vb = dk.box(s, 10.6, 2.0, 2.2, 0.7, "Brackenfield", fill=SAND, line=AMBER, name="v-brack")
    vf = dk.box(s, 10.6, 3.6, 2.2, 0.7, "Fellgate", fill=SAND, line=AMBER, name="v-fell")
    vn = dk.box(s, 10.6, 5.2, 2.2, 0.7, "Norrvik", fill=SAND, line=AMBER, name="v-norr")
    flows = [(a30, ext, 3, 1, "CLRAS030", "Adjuster Extranet", "CLX-IF-013"),
             (ext, a40, 1, 3, "Adjuster Extranet", "CLRAS040", "CLX-IF-014"),
             (ext, a70, 2, 3, "Adjuster Extranet", "CLRAS070", "CLX-IF-016")]
    for (sa, sb, sa_i, sb_i, na, nb, iid) in flows:
        lab = f"{iid} ({W.interface_schedule(iid, d)})"
        dk.connect(s, sa, sb, sa_i, sb_i, label=lab, label_w=2.6, label_size=9, elbow=(iid == "CLX-IF-016"),
                   label_offset=(0, -0.3) if iid != "CLX-IF-016" else (0.4, 0.25))
        dk.fact("arrow_only", f"Connector {na} → {nb} labelled '{lab}'.", 8, "connector", f"{na} -> {nb} [label: {lab}]",
                world_ref=f"INTERFACE:{iid}#schedule")
    for vbx in (vb, vf, vn):
        dk.connect(s, ext, vbx, 3, 1, label="web access", label_size=9, label_offset=(0.2, -0.28))
    dk.notes(s, "Instructions go out every 30 minutes in the working day; reports come back hourly. Vendor invoices "
                "are matched overnight on weekdays.")

    # 9 adjacent networks (groups)
    s = dk.new_slide("Adjacent supplier networks")
    groups = [("Repair networks", ["VEN-04", "VEN-05", "VEN-06", "VEN-14"]), ("Salvage", ["VEN-09"]),
              ("SIU partner", ["VEN-10"]), ("Solicitors", ["VEN-07", "VEN-08"])]
    for gi, (gname, vids) in enumerate(groups):
        g = dk.group(s, f"grp-suppliers-{gi + 1}")
        x = CONTENT_LEFT + gi * 3.07
        dk.box(s, x, CONTENT_TOP + 0.05, 2.95, 0.55, gname, shape=MSO_SHAPE.RECTANGLE, fill=NAVY, line=None,
               color=WHITE, size=14, bold=True, group=g, name=f"suppliers-hdr-{gi + 1}")
        for k, vid in enumerate(vids):
            v = V[vid]
            dk.box(s, x, CONTENT_TOP + 0.75 + k * 1.22, 2.95, 1.1, [v["short"], v["role"]], fill=TEAL_LT, line=None,
                   size=13, bold=True, group=g, name=f"supplier-{vid}")
    dk.fact("visual_only", "Thistlecombe Repair Network: UK motor repair network (212 approved bodyshops) and UK "
                           "windscreen.", 9, "group", "UK motor repair network (212 approved bodyshops)",
            world_ref="VENDOR:VEN-04#role", shape_name="grp-suppliers-1")
    dk.fact("visual_only", "Vardholm: Norwegian motor repair network (23 workshops).", 9, "group",
            "Norwegian motor repair network (23 workshops)", world_ref="VENDOR:VEN-05#role", shape_name="grp-suppliers-1")

    # 10 governance
    s = dk.new_slide("Quality and governance")
    items = [W.rule_version("BR-ASM-010", d)["text"].rstrip(".") + " (BR-ASM-010)",
             W.rule_version("BR-ASM-013", d)["text"].rstrip(".") + " (BR-ASM-013)",
             "Panel performance is reviewed with each vendor against the service levels on slide 6",
             ] + PH.pick(dk.rng, PH.GOVERNANCE, 2)
    dk.bullets(s, items, size=15)
    dk.fact("general", "A Claims Assessor may not assess a claim involving a relative or a prior employer within 3 "
                       "years (BR-ASM-010).", 10, "text", "a relative or a prior employer within 3 years",
            world_ref="RULE:BR-ASM-010@v1")

    # 11 contacts
    contacts_slide(dk, ["P033", "P034", "P057", "P058"])
    dk.fact("general", "Colin Rudd is Client Director at Brackenfield.", 11, "table", "Colin Rudd Client Director",
            world_ref="PERSON:P057#titles")
    return dk


# =========================================================================================
# VS019 Incident Review INC-2025-0412 (2025-05-20)
# =========================================================================================
def build_vs019(W, out_dir):
    fid = "VS019"
    dk = Deck(W, fid, out_dir, short_title="Incident Review INC-2025-0412")
    d = dk.date
    inc = W.incidents["INC-2025-0412"]
    assert not W.may_state(fid, "INTERFACE:CLX-IF-042", "schedule")
    assert not W.may_state(fid, "INTERFACE:CLX-IF-042", "mq_max_depth")
    guard(W, fid, [("INCIDENT:INC-2025-0412", "root_cause"), ("INCIDENT:INC-2025-0412", "interfaces"),
                   ("INTERFACE:CLX-IF-043", "schedule_history"), ("COPYBOOK:RSVMOVE", "field_history"),
                   ("REPORT:NISA-TP2", "late_events"), ("DECISION:DEC-003", None), ("MEETING:MTG-003", None)])
    tp2 = W.reports["NISA-TP2"]["late_events"][0]

    s = dk.title_slide("Incident Review – INC-2025-0412",
                       "GL reserve journals rejected after CLX-IF-042 layout change  |  Sev1  |  post-incident review",
                       [f"Incident owner: {person(W, 'P031', d)}",
                        f"Integration Platform  |  {fmt_date(d)}  |  Classification: Internal"])

    # 2 summary + notes PL-115
    s = dk.new_slide("Incident summary")
    rows = [["Item", "Detail"],
            ["Incident", "INC-2025-0412"],
            ["Severity", inc["severity"]],
            ["Start", "28 Apr 2025 03:02"],
            ["Resolved", "30 Apr 2025 17:40"],
            ["Systems", ", ".join(W.system_name(x, d) for x in inc["systems"])],
            ["Program", ", ".join(inc["programs"])],
            ["Customer impact", "None; finance and regulatory reporting impact only"],
            ["Root cause (short)", "Unassessed change to the RSVMOVE record layout – see talk track"]]
    dk.table(s, rows, col_w=[2.5, 9.6], size=14, row_h=0.5, name="Incident summary")
    dk.notes(s, "Root cause: RM-AMOUNT was widened to S9(11)V99 under CHUB-138 without consumer sign-off. The change "
                "went in on 25 April for Nordic large losses; the GL adapter on CLX-IF-043 rejected every record from "
                "the first run afterwards.")
    dk.fact("speaker_notes", "Speaker notes: root cause was RM-AMOUNT widened to S9(11)V99 under CHUB-138 without "
                             "consumer sign-off.", 2, "notes",
            "RM-AMOUNT was widened to S9(11)V99 under CHUB-138 without consumer sign-off", placement="PL-115")
    dk.fact("general", "INC-2025-0412 was a Sev1 incident starting 28 Apr 2025 03:02, resolved 30 Apr 2025 17:40.", 2,
            "table", "Start 28 Apr 2025 03:02 Resolved 30 Apr 2025 17:40", world_ref="INCIDENT:INC-2025-0412#start")
    dk.fact("general", "CLRRS170 is the program involved in INC-2025-0412.", 2, "table", "Program CLRRS170",
            world_ref="INCIDENT:INC-2025-0412#programs")

    # 3 impact chain (PL-114)
    s = dk.new_slide("Impact chain", "How one layout change reached a regulatory return")
    names = ["CLX-IF-042", "CLX-IF-043", "Group Ledger", "CLX-IF-051", "NISA-TP2"]
    caps = ["Reserve Movement Daily Extract", "GL Reserve Journal Feed", "general ledger", "Technical Provisions Feed",
            "Quarterly Technical Provisions Return"]
    boxes = []
    for i, (nm, cp) in enumerate(zip(names, caps)):
        x = 0.55 + i * 2.56
        fill = SAND if i in (0, 4) else TEAL_LT
        bx = dk.box(s, x, 2.6, 1.9, 0.9, nm, fill=fill, line=AMBER if i in (0, 4) else TEAL, size=14, bold=True,
                    name=f"chain-{i + 1}")
        dk.text(s, x - 0.1, 3.55, 2.1, 0.6, cp, size=10, color=GREY, align=PP_ALIGN.CENTER, name=f"chain-cap-{i + 1}")
        boxes.append(bx)
    labs = ["widened RM-AMOUNT", "every record rejected", "journals missing 25–29 Apr", "Q1 2025 return 2 days late"]
    for i in range(4):
        dk.connect(s, boxes[i], boxes[i + 1], 3, 1, label=labs[i], label_w=1.6, label_size=9, label_offset=(0, -0.62),
                   name=f"impact-{i + 1}", width_pt=2.0)
    for i in range(3):
        dk.fact("arrow_only", f"Impact chain connector {names[i]} → {names[i + 1]} labelled '{labs[i]}'.", 3,
                "connector", f"{names[i]} -> {names[i + 1]} [label: {labs[i]}]",
                world_ref="INCIDENT:INC-2025-0412#interfaces", shape_name=f"impact-{i + 1}")
    dk.fact("arrow_only", "Impact chain: CLX-IF-042 → CLX-IF-043 → Group Ledger → CLX-IF-051 → NISA-TP2 (Q1 2025 "
                          "return 2 days late).", 3, "connector",
            "CLX-IF-051 -> NISA-TP2 [label: Q1 2025 return 2 days late]", placement="PL-114", shape_name="impact-4")
    dk.text(s, 0.55, 5.0, 12.2, 1.2,
            ["The movement extract itself ran normally; the failure was in the consumer that parses the record.",
             "Other consumers of the same extract are shown on the dependency map."],
            size=14, color=GREY, bullets=True)

    # 4 timeline raster
    s = dk.new_slide("Timeline")
    cv = R.Canvas(1700, 900)
    cv.title("INC-2025-0412 timeline")
    ev = [("7 Apr", "CHUB-138 raised"), ("25 Apr", "Layout change deployed"), ("28 Apr 03:02", "GL adapter rejects"),
          ("28 Apr 08:15", "Incident bridge"), ("30 Apr", "Revert + RM-REC-VERSION"), ("30 Apr 17:40", "Resolved"),
          ("7 May", "TP2 submitted"), ("9 May", "CLX-IF-043 at 03:45")]
    xs = [110 + i * 210 for i in range(len(ev))]
    cv.d.line([(70, 450), (1650, 450)], fill=R.GREY_MD, width=6)
    for i, ((dt, lab), x) in enumerate(zip(ev, xs)):
        up = i % 2 == 0
        cv.d.ellipse([x - 14, 436, x + 14, 464], fill=R.RED if "rejects" in lab else R.TEAL)
        y = 200 if up else 560
        cv.arrow((x, y + 90 if up else y - 10), (x, 430 if up else 470), color=R.NAVY, width=3, head=14)
        cv.text((x, y), dt, size=24, bold=True, fill=R.NAVY, anchor="ma")
        cv.text((x, y + 36), lab, size=22, fill=R.BLACK, anchor="ma")
    dk.picture(s, cv.png(), CONTENT_LEFT, CONTENT_TOP, w=CONTENT_W,
               alt="Incident timeline from the change request on 7 April to the interface schedule change on 9 May.",
               name="incident-timeline")
    dk.fact("image_text", "Timeline image: incident bridge opened 28 Apr 08:15.", 4, "image", "28 Apr 08:15",
            world_ref="MEETING:MTG-003#start_time")
    dk.fact("image_text", "Timeline image: TP2 submitted on 7 May.", 4, "image", "TP2 submitted",
            world_ref="REPORT:NISA-TP2#late_events")
    dk.fact("alt_text", "Alt text: incident timeline runs from 7 April to 9 May.", 4, "alt_text",
            "from the change request on 7 April to the interface schedule change on 9 May")

    # 5 actions (PL-116)
    s = dk.new_slide("Corrective actions")
    rows = [["Ticket", "Action", "Owner", "Status"],
            ["CHUB-142", "Revert RM-AMOUNT to PIC S9(9)V99 COMP-3; add RM-REC-VERSION", W.name_of("P023", d),
             "Done 30 Apr 2025"],
            ["CHUB-143", "CLX-IF-043 moves to 03:45 from 2025-05-09 (was 03:00); validate record version",
             W.name_of("P031", d), "Done"],
            ["CHUB-144", "Interface change impact checklist: downstream consumers must sign off", W.name_of("P050", d),
             "In progress"]]
    dk.table(s, rows, col_w=[1.3, 6.6, 2.2, 2.0], size=14, row_h=0.75, name="Actions")
    dk.fact("contradiction_new", "Action: CLX-IF-043 moves to 03:45 from 2025-05-09.", 5, "table",
            "CLX-IF-043 moves to 03:45 from 2025-05-09", placement="PL-116")
    dk.fact("general", "CHUB-144 introduced an interface change impact checklist (downstream consumers must sign off).",
            5, "table", "Interface change impact checklist: downstream consumers must sign off",
            world_ref="TICKET:CHUB-144")
    dk.notes(s, "CHUB-144 is owned by Marcus Oduya and should close by the end of May. The schedule move gives the GL "
                "adapter headroom and a record-version check before it parses anything.")

    # 6 copybook detail
    s = dk.new_slide("RSVMOVE layout change in detail")
    rows = [["Date", "Field", "From", "To", "Ticket"]]
    for fh in W.copybooks["RSVMOVE"]["field_history"]:
        rows.append([fmt_date(fh["date"], "short"), fh["field"], fh["from_pic"] or "—", fh["to_pic"], fh["ticket"]])
    dk.table(s, rows, col_w=[1.6, 2.4, 3.0, 3.0, 1.6], size=14, row_h=0.6, name="Field history")
    dk.text(s, CONTENT_LEFT, 4.4, CONTENT_W, 1.6,
            ["RM-REC-VERSION carries value 02 so consumers can detect future layout changes",
             "Fix commit: 'CLRRS170/RSVMOVE: revert RM-AMOUNT to PIC S9(9)V99 COMP-3; add RM-REC-VERSION (CHUB-142)'"],
            size=14, bullets=True)
    dk.fact("general", "RM-REC-VERSION 9(2) was added to RSVMOVE on 30 Apr 2025 (value 02).", 6, "table",
            "RM-REC-VERSION — 9(2) CHUB-142", world_ref="COPYBOOK:RSVMOVE#field_history")
    dk.fact("general", "RM-AMOUNT was widened from S9(9)V99 COMP-3 to S9(11)V99 COMP-3 on 25 Apr 2025 (CHUB-138).", 6,
            "table", "RM-AMOUNT S9(9)V99 COMP-3 S9(11)V99 COMP-3 CHUB-138", world_ref="COPYBOOK:RSVMOVE#field_history")

    # 7 regulatory impact
    s = dk.new_slide("Regulatory impact")
    cfo = W.alias_holder("the CFO", tp2["submitted"])
    items = [f"Q1 2025 NISA-TP2 return due {fmt_date(tp2['due'])}; submitted {fmt_date(tp2['submitted'])}",
             f"Two-day extension granted by {person(W, 'P055', d)}, NISA",
             f"Return prepared by Regulatory Reporting ({W.name_of('P020', d)}) and signed by the CFO",
             "Reserve journals for 25–29 April were missing from the Group Ledger until the fix",
             "No customer detriment; no other returns affected"]
    dk.bullets(s, items, size=16)
    dk.notes(s, f"The late return was signed by the CFO, {W.name_of(cfo, d)}.")
    dk.fact("general", "Q1 2025 NISA-TP2 was due 5 May 2025 and submitted 7 May 2025.", 7, "text",
            "due 5 May 2025; submitted 7 May 2025", world_ref="REPORT:NISA-TP2#late_events")
    dk.fact("general", "Imogen Thackray (NISA) granted the two-day extension.", 7, "text",
            "Two-day extension granted by Imogen Thackray", world_ref="REPORT:NISA-TP2#late_events.note")

    # 8 dependency map
    s = dk.new_slide("Dependency map of the reserve movement extract", "Consumer team on each arrow")
    pos = {"CLX-IF-042": (0.7, 3.4), "CLX-IF-043": (4.2, 1.8), "CLX-IF-044": (4.2, 3.4), "CLX-IF-047": (4.2, 5.0),
           "CLX-IF-051": (8.4, 1.8), "CLX-IF-058": (8.4, 3.4), "CLX-IF-055": (8.4, 5.0)}
    bx = {k: dk.box(s, x, y, 2.3, 0.75, k, size=14, bold=True, fill=SAND if k == "CLX-IF-042" else TEAL_LT,
                    line=AMBER if k == "CLX-IF-042" else TEAL, name=f"dep-{k}") for k, (x, y) in pos.items()}
    for src in ["CLX-IF-042", "CLX-IF-043", "CLX-IF-044", "CLX-IF-047"]:
        for dep in W.interfaces[src]["dependents"]:
            if dep not in bx:
                assert str(W.interfaces[dep]["since"]) > d, dep
                continue
            team = W.team_name(W.interfaces[dep]["consumer_teams"][0], d)
            dk.connect(s, bx[src], bx[dep], 3, 1, label=team, label_size=9, label_w=1.7, label_offset=(0, -0.3))
            dk.fact("arrow_only", f"Connector {src} → {dep} labelled with consumer team '{team}'.", 8, "connector",
                    f"{src} -> {dep} [label: {team}]", world_ref=f"INTERFACE:{dep}#depends_on")
    dk.notes(s, "As of today the extract has three direct consumers. CDW feeds the monthly reserve triangles, and the "
                "cession feed drives the monthly bordereaux to the reinsurers.")

    # 9 bridge attendees and decisions
    s = dk.new_slide("Incident bridge – 28 April 2025")
    mt = W.meetings["MTG-003"]
    rows = [["Attendee", "Role"]] + [[W.name_of(p, d), W.title_of(p, d)] for p in mt["attendees"]]
    dk.table(s, rows, x=CONTENT_LEFT, w=6.2, col_w=[2.4, 3.8], size=12, row_h=0.45, name="Bridge attendees")
    dk.text(s, 7.1, CONTENT_TOP + 0.1, 5.7, 4.5,
            ["Decision (DEC-003): " + W.decisions["DEC-003"]["statement"],
             f"Decided by {W.name_of('P031', d)} and {W.name_of('P021', d)}",
             f"Bridge opened {mt['start_time']}, {mt['duration_minutes']} minutes"],
            size=15, bullets=True, para_space=12)
    dk.fact("general", "DEC-003: revert the RM-AMOUNT widening, add a record-version byte, move CLX-IF-043 from 03:00 "
                       "to 03:45.", 9, "text", "move CLX-IF-043 from 03:00 to 03:45", world_ref="DECISION:DEC-003")
    dk.fact("general", "Hamish Gilchrist (Financial Controller) attended the INC-2025-0412 bridge.", 9, "table",
            "Hamish Gilchrist Financial Controller", world_ref="MEETING:MTG-003#attendees")

    # 10 lessons
    s = dk.new_slide("Lessons learned")
    dk.bullets(s, PH.pick(dk.rng, PH.LESSONS, 6), size=16)
    # 11 doc control
    appr = approvers(W, d, ["P032", "P018", "P021"], minus_days(d, 1))
    dk.doc_control_slide("PIR-INC-2025-0412", person(W, "P031", d), appr,
                         history(dk, ["P031", "P050", "P031"], spans=(15, 8, 3)),
                         "Technology Delivery Office, Financial Control, Regulatory Reporting, Integration Platform, "
                         "Legacy Claims Platforms")
    return dk

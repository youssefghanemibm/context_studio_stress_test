"""TX072: email thread on the Wave 1 duplicate payments (INC-2026-0914), exported as JSON on 2026-09-16."""
from __future__ import annotations

import json

from .common import W, D, Facts, out_path, name, email, title, assert_may

FID = "TX072"
PATH = out_path(FID, "email_thread_wave1_payments", "json")
DATE = D("2026-09-16")


def person(pid, d=DATE):
    return {"name": name(pid, d), "email": email(pid, d)}


def sig(pid, d=DATE):
    p = W.people[pid]
    loc = W.locations[p["location"]]["name"]
    org = "IBM Consulting" if p["employer"] == "ORG-IBM" else "Corvane Mutual Insurance Society Limited"
    return f"\n\n{name(pid, d)}\n{title(pid, d)}\n{org} | {loc}\nMobile {p['phone']}"


def build(facts: Facts):
    for ref, f in [("INCIDENT:INC-2026-0914", "impact"), ("INCIDENT:INC-2026-0914", "root_cause"), ("TICKET:CHUB-371", None),
                   ("ADR:ADR-021", None), ("INTERFACE:CLX-IF-038", None), ("VENDOR:VEN-11", None)]:
        assert_may(FID, ref, f)
    AP, LS, AS, NH, HG, AK = "P035", "P042", "P017", "P032", "P021", "P048"
    subj = "Duplicate payment instructions from Claims Hub - Wave 1"
    M = []

    def add(mid, date, frm, to, cc, subject, body, reply_to=None, attachments=()):
        M.append({"message_id": f"<{mid}@corvane-mutual.example>",
                  "in_reply_to": f"<{reply_to}@corvane-mutual.example>" if reply_to else None,
                  "date": date, "from": person(frm), "to": [person(x) for x in to], "cc": [person(x) for x in cc],
                  "subject": subject, "importance": "high" if not reply_to else "normal",
                  "body": body + sig(frm), "attachments": list(attachments)})

    add("20260914100512.w1pay.1", "2026-09-14T10:05:12+01:00", AP, [LS, AS], [NH, HG, AK], f"URGENT: {subj}",
        "Linnea, Aisha,\n\nCorvane Payments Gateway has flagged payment instructions for the same claim and the same amount arriving twice this morning, all from Claims Hub (UK motor). The first ones came through shortly after nine.\n\nCan the squad check payment-orchestrator straight away? We are checking with the gateway and the clearing bank which instructions have already been released.\n\nI have asked the service desk to log a Sev 2.\n\nThanks,\nAlun")
    add("20260914112040.w1pay.2", "2026-09-14T11:20:40+01:00", LS, [AP], [AS, NH, HG, AK], f"RE: URGENT: {subj}",
        "Alun,\n\nWe have found it. payment-orchestrator retried instructions to CPG after a timeout, without an idempotency key, so the gateway treated each retry as a new instruction. The incident is INC-2026-0914 and I have raised CHUB-371 for the fix.\n\nWe will send you the list of affected claims as soon as we have matched it against the gateway log.\n\nLinnea",
        reply_to="20260914100512.w1pay.1")
    add("20260914160522.w1pay.3", "2026-09-14T16:05:22+01:00", AP, [LS, AS], [NH, HG, AK], f"RE: URGENT: {subj}",
        "All,\n\nThe count is confirmed with the gateway: 18 claims paid twice, £41,236.50 in total. No further duplicates since the incident was stabilised this afternoon.\n\nWe are issuing recall requests through CPG for every duplicate today and will track them daily until they are all back.\n\nAttached: the list of the 18 claims (claim references only).\n\nAlun",
        reply_to="20260914112040.w1pay.2",
        attachments=[{"filename": "wave1_duplicate_payments_claim_refs.xlsx", "size_bytes": 18432,
                      "note": "attachment not included in this export"}])
    add("20260914163511.w1pay.4", "2026-09-14T16:35:11+01:00", HG, [AP], [LS, AS, NH, AK], f"RE: URGENT: {subj}",
        "Thanks, Alun. Please keep me posted on the recalls so that Financial Control can reconcile the payments account once they are back. I will brief the CFO this evening.\n\nHamish",
        reply_to="20260914160522.w1pay.3")
    add("20260915091003.w1pay.5", "2026-09-15T09:10:03+01:00", NH, [AP, LS], [AS, HG, AK], f"RE: URGENT: {subj}",
        "Morning all,\n\nFor the record: the incident was closed yesterday at 15:45 once no further duplicates were seen. CHUB-371 is the permanent fix, and the Design Authority is looking at making idempotency keys a standard for every payment instruction rather than a one-off fix.\n\nThank you to Payments Operations and to the squad for a fast response on a difficult first day.\n\nNeil",
        reply_to="20260914163511.w1pay.4")
    add("20260915143210.w1pay.6", "2026-09-15T14:32:10+01:00", AK, [NH], [AP, LS, AS, HG], f"RE: URGENT: {subj}",
        "Neil, all,\n\nI have added this to the Wave 1 lessons-learned log, and we will add a specific duplicate-payment test to the Wave 2 rehearsals so the scenario is exercised before the next cut-over.\n\nArjun",
        reply_to="20260915091003.w1pay.5")
    add("20260916155006.w1pay.7", "2026-09-16T15:50:06+01:00", LS, [AP, NH], [AS, HG, AK], f"RE: URGENT: {subj}",
        "All,\n\nCHUB-371 is deployed to production today. payment-orchestrator now sends an idempotency key with every instruction to CPG, so a retry after a timeout can no longer create a second payment.\n\nThe Design Authority also accepted ADR-021 today: idempotency keys for all payment instructions, across every service that sends them.\n\nLinnea",
        reply_to="20260915143210.w1pay.6")
    add("20260916171544.w1pay.8", "2026-09-16T17:15:44+01:00", AP, [LS, NH], [AS, HG, AK], f"RE: URGENT: {subj}",
        "Thanks, Linnea, good news. The recalls are progressing with the bank and I will confirm on this thread when all 18 are back.\n\nAlun",
        reply_to="20260916155006.w1pay.7")

    doc = {
        "export": {"source": "Payments Operations shared mailbox", "exported_by": person(AP), "exported_at": "2026-09-16T18:02:00+01:00",
                   "thread_subject": subj, "message_count": len(M), "classification": "Internal",
                   "related": {"incident": "INC-2026-0914", "ticket": "CHUB-371", "interface": "CLX-IF-038"}},
        "messages": M,
    }

    def F(i, needle, statement, kind="general", world_ref=None):
        facts.add(FID, PATH, kind=kind, statement=statement, needle=needle,
                  locator={"kind": "json_pointer", "pointer": f"/messages/{i}/body"}, world_ref=world_ref,
                  text_at_locator=M[i]["body"])

    F(1, "retried instructions to CPG after a timeout, without an idempotency key",
      "Root cause of INC-2026-0914: payment-orchestrator retried instructions to CPG after a timeout without an idempotency key.",
      kind="needle", world_ref="INCIDENT:INC-2026-0914#root_cause")
    F(2, "18 claims paid twice, £41,236.50 in total",
      "INC-2026-0914: 18 claims were paid twice on the Wave 1 cut-over day, £41,236.50 in total.", kind="needle",
      world_ref="INCIDENT:INC-2026-0914#impact")
    F(4, "the incident was closed yesterday at 15:45", "INC-2026-0914 ended at 15:45 on 2026-09-14.",
      world_ref="INCIDENT:INC-2026-0914#end")
    F(6, "CHUB-371 is deployed to production today", "CHUB-371 (the duplicate-payment fix) was deployed on 2026-09-16.",
      world_ref="TICKET:CHUB-371")
    F(6, "accepted ADR-021 today", "ADR-021 (idempotency keys for all payment instructions) was accepted on 2026-09-16.",
      world_ref="ADR:ADR-021")
    F(3, "I will brief the CFO this evening", "In September 2026 'the CFO' (briefed by Hamish Gilchrist) is Priya Raman.",
      kind="alias_use", world_ref="PERSON:P001#role_aliases")
    return doc


def write(facts: Facts):
    doc = build(facts)
    PATH.parent.mkdir(parents=True, exist_ok=True)
    PATH.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return PATH, len(doc["messages"])

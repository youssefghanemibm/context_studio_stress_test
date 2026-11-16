"""TX071: chat export of the #skerry-programme channel (about 3,000 messages, 2026-04-01..2026-11-10).

Display names are aliases ("Arjun K (IBM)", "Bjorn", "Linnea Sjoberg"...). Scripted messages carry
non-exclusive world facts on the right dates; the rest is everyday channel chatter with no facts.
Plants PL-232: October messages use 'sub-ro' for Subrogation and 'the ledger' for CLARA.
"""
from __future__ import annotations

import calendar
import datetime as dt
import json

from generators.common import util

from .common import W, D, Facts, out_path, placement, assert_may

FID = "TX071"
PATH = out_path(FID, "chat_export_programme_channel", "json")
FROM, TO = D("2026-04-01"), D("2026-11-10")

MEMBERS = {
    "P048": "Arjun K (IBM)", "P017": "Aisha S", "P032": "Neil H", "P047": "Victoria A (IBM)", "P049": "Elin Fosse (IBM)",
    "P050": "Marcus O (IBM)", "P051": "Callum (IBM)", "P052": "Gordon Sproat (IBM)", "P053": "Nadia P (IBM)",
    "P054": "Hannah L (IBM)", "P040": "Sofie Bak", "P041": "Daniel A", "P042": "Linnea Sjoberg", "P043": "Tariq H",
    "P031": "Henrik V", "P023": "Keith B", "P024": "Pauline A", "P026": "Sunita V", "P018": "Tomasz Wojcik",
    "P016": "Graham P", "P013": "Freya L", "P020": "Bjorn", "P037": "Ruth O", "P027": "Oskar L", "P036": "Maja H",
    "P035": "Alun P", "P009": "Lena K", "P025": "Derek O", "P033": "Imran T", "P014": "Siobhan Q",
}
WEIGHT = {"P048": 6, "P017": 5, "P032": 3, "P041": 4, "P042": 4, "P040": 4, "P053": 4, "P051": 3, "P031": 3, "P023": 3,
          "P054": 3, "P043": 3, "P049": 2, "P050": 2, "P052": 2, "P024": 2, "P026": 2, "P018": 2, "P047": 1, "P016": 2,
          "P013": 1, "P020": 1, "P037": 2, "P027": 1, "P036": 1, "P035": 1, "P009": 1, "P025": 1, "P033": 1}


def uid(pid):
    return "U" + pid[1:].rjust(4, "2")


def epoch(d: dt.date, sec: int) -> tuple[str, str]:
    off = 3600 if (D(f"{d.year}-03-29") <= d < D(f"{d.year}-10-25")) else 0
    t = calendar.timegm(d.timetuple()) + sec - off
    h, rem = divmod(sec, 3600)
    m, s = divmod(rem, 60)
    tz = "+01:00" if off else "+00:00"
    # Fractions in the "000nnn" form seen in real channel exports (also keeps digit runs like "0.87"
    # out of the export, see common.BANNED_VALUES).
    return f"{t}.000{(sec * 97) % 1000:03d}", f"{d.isoformat()}T{h:02d}:{m:02d}:{s:02d}{tz}"


# ---------------------------------------------------------------------------------------------
# Scripted (dated) messages: (date, hh:mm, pid, text, fact or None)
# ---------------------------------------------------------------------------------------------
def scripted():
    S = [
        ("2026-04-01", "08:05", "P037", "Morning all. The Circular 2026/04 rules are live from today: referral at 65, customer notice letters, and no auto-decline. Shout if you see anything odd.", None),
        ("2026-04-01", "08:20", "P026", "CLRNFR99 is disabled in the scheduler as planned. Nothing will run tonight.", None),
        ("2026-04-01", "16:40", "P017", "First day of the new fraud rules done. Thanks everyone who worked on CHUB-204.", None),
        ("2026-05-13", "09:10", "P037", "Heads up: INC-2026-0518. The CLRFR040 batch sweep still had the old threshold hard-coded. 37 claims that scored 65-69 since 1 April weren't referred by the batch path. They're being referred by hand today.",
         {"needle": "37 claims that scored 65-69", "kind": "general", "world_ref": "INCIDENT:INC-2026-0518#impact",
          "statement": "INC-2026-0518: 37 claims scored 65-69 were not referred by the CLRFR040 batch sweep; referred manually on 2026-05-13."}),
        ("2026-05-13", "09:25", "P023", "I've raised CHUB-298 for the CLRFR040 fix. Online path is fine, it reads T_PARAM.", None),
        ("2026-05-13", "11:02", "P037", "Until the fix is in, Compliance will run a daily query for unreferred claims in the 65-69 band.", None),
        ("2026-06-01", "07:50", "P051", "Wave 0 Denmark is live on the Hub. Good weekend, everyone. Hypercare call at 09:00.", None),
        ("2026-06-30", "15:30", "P054", "The Claims Handling Manual v7.2 is approved today. New version is on the intranet.", None),
        ("2026-07-01", "08:40", "P023", "RSV_T3_REVIEW_DAYS is 14 in T_PARAM from today, per CHUB-318.", None),
        ("2026-07-02", "10:15", "P041", "Parallel run is flagging Tier-3 claims: the engine is still scheduling reviews at 21 days. Raising CHUB-322, it's a config value. INC-2026-0702.", None),
        ("2026-07-03", "14:05", "P041", "CHUB-322 deployed, the engine is on 14 days for Tier-3 now.", None),
        ("2026-07-29", "16:55", "P037", "First FR1 return submitted today, a day ahead of the deadline. Thanks Bjorn and team.",
         {"needle": "First FR1 return submitted today, a day ahead of the deadline", "kind": "general",
          "world_ref": "REPORT:NISA-FR1#submissions.2026Q2.submitted",
          "statement": "The first NISA-FR1 return (Q2 2026) was submitted on 2026-07-29, one day before the deadline."}),
        ("2026-07-29", "17:02", "P020", "Team effort. Q3 will be easier now the extract is proven.", None),
        ("2026-08-21", "17:30", "P051", "Rehearsal 3 for Wave 1 is complete and the reconciliation is signed off. Details in the rehearsal report.", None),
        ("2026-08-28", "18:10", "P041", "That's the end of the reserve parallel run. Six months, done. Thanks all, especially Lena's team.",
         {"needle": "That's the end of the reserve parallel run", "kind": "general", "world_ref": "TICKET:CHUB-241",
          "statement": "The reserve parallel run ended on 2026-08-28."}),
        ("2026-09-11", "17:20", "P048", "Go decision for Wave 1: cut-over Monday 14 September. Freeze starts 18:00 today and runs to 06:00 Monday.",
         {"needle": "Freeze starts 18:00 today and runs to 06:00 Monday", "kind": "general", "world_ref": "DECISION:DEC-009",
          "statement": "DEC-009: Wave 1 go decision on 2026-09-11; freeze 2026-09-11 18:00 to 2026-09-14 06:00."}),
        ("2026-09-14", "07:05", "P048", "Wave 1 is live. UK motor is on the Hub. Huge thanks to everyone.", None),
        ("2026-09-14", "10:02", "P042", "We're seeing duplicate payment instructions going to CPG from payment-orchestrator after a timeout. Alun's team are on it with us. INC-2026-0914.", None),
        ("2026-09-14", "16:10", "P042", "Root cause: retry on CPG timeout without an idempotency key. CHUB-371 raised.", None),
        ("2026-09-16", "15:45", "P042", "CHUB-371 is deployed and ADR-021 is accepted: every payment instruction carries an idempotency key from now on.", None),
        ("2026-09-17", "12:10", "P054", "Fraud workshop outcome: from 1 October Tier-3 claims are referred at 60 or more, the general threshold stays 65. Minutes tomorrow.",
         {"needle": "from 1 October Tier-3 claims are referred at 60 or more", "kind": "general", "world_ref": "DECISION:DEC-014",
          "statement": "Chat (2026-09-17): from 2026-10-01 Tier-3 claims are referred at a Sentinel score of 60 or more; general threshold 65."}),
        ("2026-09-18", "16:30", "P035", "All 18 duplicate payments from the Wave 1 weekend have been recalled. Thanks for the help.",
         {"needle": "All 18 duplicate payments from the Wave 1 weekend have been recalled", "kind": "general",
          "world_ref": "INCIDENT:INC-2026-0914#impact",
          "statement": "By 2026-09-18 all 18 Wave 1 duplicate payments had been recalled."}),
        ("2026-09-29", "17:05", "P042", "CHUB-388 done: fraud-referral-svc has the Tier-3 threshold of 60, effective 1 October.", None),
        ("2026-09-30", "15:20", "P024", "CHUB-395 is in: FRD_REFER_T3_THRESH = 60 in T_PARAM, valid from 1 October.", None),
        ("2026-10-01", "08:15", "P037", "Tier-3 threshold of 60 is live from today. Compliance daily query now covers 60-64 for Tier-3 as well.", None),
        ("2026-10-05", "09:20", "P040", "Found it: triage-svc cached the thresholds and didn't reload the Tier-3 value. Fix under CHUB-392. INC-2026-1007.", None),
        ("2026-10-05", "17:40", "P037", "Update on INC-2026-1007: 9 Tier-3 claims scoring 60-64 weren't referred between 1 and 5 October. All referred manually today.",
         {"needle": "9 Tier-3 claims scoring 60-64 weren't referred", "kind": "general", "world_ref": "INCIDENT:INC-2026-1007#impact",
          "statement": "INC-2026-1007: 9 Tier-3 claims scoring 60-64 were not referred between 2026-10-01 and 2026-10-05; referred manually."}),
        ("2026-10-08", "16:20", "P048", "Steering done. PR approved the £1.8m contingency drawdown for Wave 2. And Wave 2 is confirmed for 15 February; please ignore the January date on the old slide, it's void.",
         [{"needle": "PR approved the £1.8m contingency drawdown for Wave 2", "kind": "alias_use", "world_ref": "DECISION:DEC-010",
           "statement": "Chat alias use: 'PR' (Priya Raman, the CFO) approved the £1.8m Wave 2 contingency drawdown on 2026-10-08."},
          {"needle": "Wave 2 is confirmed for 15 February", "kind": "general", "world_ref": "DECISION:DEC-011",
           "statement": "Wave 2 confirmed for 2027-02-15; the January draft date is void."}]),
        ("2026-10-08", "16:24", "P017", "Thanks Arjun. I've updated the roadmap page.", None),
        ("2026-10-08", "16:31", "P047", "And thanks to the CFO for turning it round so quickly.", None),
        ("2026-10-12", "11:00", "P018", "ADR-027 is up for comment: dual-run the regulatory extracts for two quarters after Wave 2. It's a proposal, not accepted yet.", None),
        ("2026-10-14", "10:12", "P013", "Reminder for everyone touching recoveries: the sub-ro cases still open in SUBTRAK need to be closed or moved before the retirement at the end of December.",
         {"needle": "sub-ro", "kind": "terminology", "pl": "tx71_terms",
          "statement": "Chat messages in October 2026 use 'sub-ro' for Subrogation."}),
        ("2026-10-14", "10:20", "P014", "On it for the UK cases. Bristol will have the list by Friday.", None),
        ("2026-10-19", "09:05", "P023", "Picked up CHUB-298 properly now, in progress.", None),
        ("2026-10-21", "14:40", "P023", "For anyone asking: the ledger stays master for UK home, commercial and liability, and for Norway and Sweden, until Wave 2.",
         {"needle": "the ledger stays master", "kind": "terminology", "pl": "tx71_terms",
          "statement": "Chat messages in October 2026 use 'the ledger' for CLARA."}),
        ("2026-10-21", "14:46", "P017", "Thanks Keith. Pinning that.", None),
        ("2026-10-27", "11:30", "P013", "The subro tracker clean-up is under way. CHUB-430 updated.", None),
        ("2026-10-28", "15:00", "P037", "Q3 FR1 return submitted today, two days ahead of the 30 October deadline. 1,530 referrals in the quarter.",
         {"needle": "Q3 FR1 return submitted today, two days ahead of the 30 October deadline", "kind": "general",
          "world_ref": "REPORT:NISA-FR1#submissions.2026Q3",
          "statement": "The Q3 2026 NISA-FR1 return (1,530 referrals) was submitted on 2026-10-28, ahead of the 2026-10-30 deadline."}),
        ("2026-11-02", "09:00", "P032", "Welcome to the new Recoveries & Documents squad, led by Tariq. Formed on Sunday.", None),
        ("2026-11-02", "09:12", "P043", "Thanks Neil. Looking forward to it.", None),
        ("2026-11-04", "16:00", "P023", "CHUB-298 is in review.",
         {"needle": "CHUB-298 is in review", "kind": "temporal", "world_ref": "TICKET:CHUB-298#status_history",
          "statement": "CHUB-298 moved to In Review on 2026-11-04."}),
        ("2026-11-09", "10:15", "P048", "CHUB-441 raised for the Wave 2 cut-over plan v1. Freeze 18:00 Fri 12 Feb to 06:00 Mon 15 Feb.", None),
        ("2026-11-10", "16:45", "P032", "CAB tomorrow at 11:00 for the November release. Please make sure your change records are complete.", None),
    ]
    return S


SAFE_CHAT = {
    "greet": ["morning all", "Morning!", "morning", "Good morning everyone", "morning, coffee first", "hi all",
              "Morning from Leeds", "Morning from Copenhagen", "god morgon from Stockholm", "Morning. Raining again here."],
    "logistics": ["stand-up is in 5", "who has the bridge link for the 10:00?", "Can someone share the RAID log link again?",
                  "Pack inputs please by end of tomorrow", "I've booked the big room for Thursday afternoon",
                  "Running 5 mins late to the 2pm, sorry", "Is the 3pm still on?", "Moved the review to tomorrow, invite updated",
                  "Reminder: sprint review this afternoon", "Can we push the 11:30 by 15 mins?", "Notes from this morning are on the wiki",
                  "Who's chairing the retro this week?", "Slides for tomorrow are in the shared folder",
                  "I'll be offline 12-1 for an appointment", "Out tomorrow, back Monday", "On leave next week, cover is in the squad calendar",
                  "Calendar invite sent for the walkthrough", "Can someone from each squad join the dependency call?"],
    "env": ["SIT2 is a bit slow this morning, anyone else?", "SIT deployment queue is long, bear with", "pipeline is green again",
            "re-running the flaky test, ignore the red build", "SIT refresh is done, data is back", "Anyone else getting logged out of the test portal?",
            "VPN is playing up again", "the test environment is back up", "build cache cleared, should be faster now",
            "the shared test data set has been refreshed"],
    "review": ["Could someone take a look at my change? small one", "reviewed, a couple of comments", "approved", "thanks!",
               "merged", "Nice one", "Can I get a second reviewer on this?", "looks good to me", "will look after lunch"],
    "social": ["cake in the kitchen on the 4th floor", "leaving drinks on Friday, all welcome", "anyone in the Leeds office tomorrow?",
               "trains are a mess again", "happy Friday all", "Have a good weekend", "Lunch order going in at 12, shout if you want in",
               "There's a fire alarm test at 11, don't panic", "The lift's out again on our floor", "Who left their charger in Room 3?"],
    "ack": ["thanks", "cheers", "ok", "noted", "+1", "sounds good", "will do", "great, thanks", "on it", "perfect", "agreed", "yep"],
    "question": ["Does anyone have the latest version of the plan on a page?", "Where are we keeping the lessons-learned log?",
                 "Is the dependency tracker up to date?", "Has anyone got the template for the change record?",
                 "Which channel do we use for hypercare issues?", "Is there a recording of yesterday's walkthrough?",
                 "Where do I find the test evidence for the last release?", "Has the wiki page for the release calendar moved?"],
    "answer": ["It's pinned at the top of the channel", "In the shared folder under Programme", "I'll send it over",
               "Link's in the wiki", "Should be in the release folder", "I think so, I'll double-check", "Yes, it's on the wiki",
               "Ask in the squad channel, they'll know"],
}
REACTIONS = ["+1", "thumbsup", "white_check_mark", "tada", "eyes", "pray", "raised_hands", "heart"]


def build(facts: Facts):
    for ref, f in [("DECISION:DEC-010", None), ("DECISION:DEC-011", None), ("DECISION:DEC-009", None),
                   ("INCIDENT:INC-2026-1007", "impact"), ("INCIDENT:INC-2026-0914", "impact"), ("INCIDENT:INC-2026-0518", "impact"),
                   ("ADR:ADR-027", "status"), ("TEAM:T30", "lead_history"), ("GLOSSARY:G-004", None), ("SYSTEM:SYS01", "aliases"),
                   ("TICKET:CHUB-298", "status_history"), ("REPORT:NISA-FR1", "submissions")]:
        assert_may(FID, ref, f)
    r = util.rng(f"{FID}:chat")
    msgs = []
    script = scripted()
    by_day: dict[str, list] = {}
    for d_, hm, pid, text, fact in script:
        by_day.setdefault(d_, []).append((hm, pid, text, fact))
    d = FROM
    while d <= TO:
        wk = d.weekday() < 5
        n = r.randint(12, 17) if wk else r.choice([0, 0, 0, 1, 2])
        day_msgs = []
        for hm, pid, text, fact in by_day.get(d.isoformat(), []):
            h, m = map(int, hm.split(":"))
            day_msgs.append([h * 3600 + m * 60 + r.randint(0, 50), pid, text, fact, None])
        times = sorted(r.randint(8 * 3600, 18 * 3600) for _ in range(n))
        last_txt = None
        for i, t in enumerate(times):
            pool = [p for p in MEMBERS if W.employed(p, d) and not (p == "P043" and False)]
            pid = r.choices(pool, weights=[WEIGHT.get(p, 1) for p in pool])[0]
            if i == 0 and t < 9 * 3600 + 900:
                cat = "greet"
            else:
                cat = r.choices(["logistics", "env", "review", "social", "ack", "question"], weights=[28, 18, 18, 8, 18, 10])[0]
            if cat == "social" and d.weekday() != 4 and r.random() < 0.5:
                cat = "logistics"
            txt = r.choice(SAFE_CHAT[cat])
            if txt == "happy Friday all" and d.weekday() != 4:
                txt = "thanks all"
            if txt == "Have a good weekend" and d.weekday() != 4:
                txt = "speak tomorrow"
            if txt == last_txt:
                txt = r.choice(SAFE_CHAT["ack"])
            last_txt = txt
            thread = None
            if cat == "question":
                thread = [("answer", r.randint(60, 900))]
            elif cat == "review" and r.random() < 0.5:
                thread = [("review", r.randint(120, 1800))]
            elif cat == "env" and r.random() < 0.4:
                thread = [("ack", r.randint(60, 600))]
            day_msgs.append([t, pid, txt, None, thread])
        day_msgs.sort(key=lambda x: x[0])
        for t, pid, txt, fact, thread in day_msgs:
            ts_, iso = epoch(d, t)
            msg = {"ts": ts_, "datetime": iso, "user": uid(pid), "user_name": MEMBERS.get(pid, pid), "type": "message",
                   "text": txt}
            if r.random() < 0.18:
                k = r.randint(1, 3)
                msg["reactions"] = [{"name": nm, "count": r.randint(1, 6)} for nm in r.sample(REACTIONS, k)]
            msgs.append((msg, fact))
            if thread:
                replies = []
                for cat, dtsec in thread:
                    rp = r.choice([p for p in MEMBERS if p != pid and W.employed(p, d)])
                    rts, riso = epoch(d, min(t + dtsec, 86000))
                    replies.append(({"ts": rts, "datetime": riso, "user": uid(rp), "user_name": MEMBERS.get(rp, rp),
                                     "type": "message", "text": r.choice(SAFE_CHAT[cat]), "thread_ts": ts_}, None))
                msg["reply_count"] = len(replies)
                msgs.extend(replies)
        d += dt.timedelta(days=1)
    msgs.sort(key=lambda m: (m[0]["datetime"], m[0]["ts"]))
    members = [{"id": uid(p), "name": MEMBERS[p], "real_name_hidden": True,
                "title": W.title_of(p, TO) or "", "is_bot": False} for p in MEMBERS]
    doc = {"export": {"workspace": "corvane-mutual", "channel": "#skerry-programme", "channel_id": "C2025SKERRY",
                      "purpose": "Programme Skerry day-to-day coordination (no customer data in this channel)",
                      "exported_at": "2026-11-10T18:30:00+00:00", "exported_by": MEMBERS["P048"],
                      "range": {"from": FROM.isoformat(), "to": TO.isoformat()}, "message_count": len(msgs)},
           "members": members,
           "messages": [m for m, _ in msgs]}
    for i, (m, fact) in enumerate(msgs):
        if not fact:
            continue
        for f in (fact if isinstance(fact, list) else [fact]):
            pl = placement(FID, f["pl"]) if f.get("pl") else None
            facts.add(FID, PATH, kind=f["kind"], statement=f["statement"], needle=f["needle"],
                      locator={"kind": "json_pointer", "pointer": f"/messages/{i}/text"}, world_ref=f.get("world_ref"),
                      placement=pl, text_at_locator=m["text"])
    facts.add(FID, PATH, kind="scale", statement=f"The #skerry-programme chat export holds {len(msgs)} messages.",
              needle=str(len(msgs)), locator={"kind": "json_pointer", "pointer": "/export/message_count"},
              world_ref="ANCHOR:TX071", text_at_locator=str(len(msgs)))
    return doc, len(msgs)


def write(facts: Facts):
    doc, n = build(facts)
    PATH.parent.mkdir(parents=True, exist_ok=True)
    PATH.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return PATH, n

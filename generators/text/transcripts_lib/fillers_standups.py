"""Short stand-up transcripts (filler): TX025, TX026, TX061, TX065, TX069.

They restate only non-exclusive world facts that were true on their date, and otherwise carry
generic delivery chatter. Each is about 12-15 minutes.
"""
from __future__ import annotations

from generators.common import util

from .common import D, W, out_path, name, first, title, assert_may, long_date
from .dialogue import Meeting, Topic
from .meetings_common import org_of


def _speakers(pids, d, overrides=None):
    out = {}
    for pid in pids:
        out[pid] = {"label": name(pid, d), "first": first(pid, d), "pid": pid, "role": title(pid, d)}
    for k, v in (overrides or {}).items():
        out[k].update(v)
    return out


def _header(m: Meeting, *, title_: str, d, start: str, minutes: int, squad: str, author: str, sp: dict,
            ref: str) -> None:
    L = [
        "CORVANE MUTUAL - PROGRAMME SKERRY",
        f"{title_}",
        "-" * 80,
        f"Ref: {ref}    Date: {long_date(d)}    Start: {start} UK time    Length: about {minutes} minutes",
        f"Team: {squad}",
        f"Transcribed by: automatic transcription; tidied by {name(author, d)} ({title(author, d)})",
        "Classification: Internal",
        "",
        "Participants:",
    ]
    for k, s in sp.items():
        org = org_of(s["pid"])
        L.append(f"  {s['label']} - {s['role']}" + ("" if org == "Corvane Mutual" else f" ({org})"))
    L += ["", "Note: stand-up notes are informal. Decisions are recorded in the relevant tickets, not here.", "",
          "-" * 80, ""]
    m.header(L)


def _close(m: Meeting):
    m.doc.add("")
    m.doc.add("-" * 80)
    m.doc.add("End of stand-up transcript.")


# ---------------------------------------------------------------------------------------------
def build_tx025(facts, wps):
    FID, d = "TX025", D("2026-08-12")
    DA, NP, CF, AS = "P041", "P053", "P051", "P017"
    for ref, f in [("TICKET:CHUB-241", None), ("TICKET:CHUB-305", None), ("TICKET:CHUB-322", None),
                   ("RULE:BR-RSV-007@v3", "text"), ("WAVE:MW-1", "date")]:
        assert_may(FID, ref, f)
    path = out_path(FID, "standup_reserve_finance_squad_2026_08_12", "txt")
    sp = _speakers([DA, NP, CF, AS], d, {CF: {"label": "Callum Fairbairn (IBM)"}})
    m = Meeting(FID, path, facts, sp, util.rng(f"{FID}:dlg:{wps}"), wps=wps, chair=DA, domain="reserving",
                duration_min=15, meta_budget=1, digress_budget=1, crosstalk_budget=1)
    m.spacing.update(meta=120.0, dig=300.0, cross=200.0)
    _header(m, title_="Stand-up transcript - Hub Squad: Reserve & Finance", d=d, start="09:15", minutes=15,
            squad="Hub Squad - Reserve & Finance (reserve-engine, gl-posting-svc, reporting-feed-svc)",
            author=DA, sp=sp, ref="SQD-RF-SU-2026-08-12")
    t = Topic("su", ["the reconciliation breaks", "the parallel run report", "the rehearsal fixes", "the GL posting tests",
                     "the reporting feed", "the code review queue", "the test data refresh", "the sprint board",
                     "the defect list"], domain="reserving", leads=[DA, NP], lines=[
        (NP, "Yesterday I finished the review of the movement mapping changes. Today I'm pairing on the GL posting tests. No blockers."),
        (CF, "From migration, rehearsal three is in the reconciliation phase. I'll need someone from the squad for an hour this week to look at a couple of breaks."),
        (AS, "Just a reminder that sprint review is on Thursday, and I'd like a demo of the reconciliation report if it's ready."),
        (DA, "The parallel run report is looking clean. We're mostly chasing timing breaks now, not amount breaks."),
        (NP, "I've got one flaky integration test on gl-posting-svc. I'll fix it today rather than keep re-running it."),
        (DA, "Let's keep the board up to date, please. Aisha's been asking where things are and the board should answer that."),
        (CF, "The reconciliation scripts are in the shared repo now, so the squad can run them themselves."),
    ])
    m.say(DA, "Morning. Let's go round. Keep it short, please, we've got the parallel-run review at ten.")
    n = m.say(DA, "Quick context: the reserve parallel run finishes on the 28th, so we've got just over two weeks of comparisons left, and then Wave 1 on the 14th of September.")
    m.doc.fact(n, needle="the reserve parallel run finishes on the 28th", kind="general", world_ref="TICKET:CHUB-241",
               statement="The reserve parallel run ends on 2026-08-28; Wave 1 cut-over is on 2026-09-14.")
    m.fill(m.at(4, 0), t)
    n = m.say(NP, "On the review-cadence bug from July, the engine and CLARA have both been on 14 days for Tier-3 since the fix, and the parallel run hasn't flagged a cadence mismatch since.")
    m.doc.fact(n, needle="both been on 14 days for Tier-3 since the fix", kind="general", world_ref="TICKET:CHUB-322",
               statement="After CHUB-322 (INC-2026-0702) reserve-engine and CLARA both apply the 14-day Tier-3 review cadence.")
    m.fill(m.at(11, 30), t)
    m.say(DA, "Okay, that's everyone. Thanks all. Callum, I'll find you someone for the rehearsal breaks.")
    m.say(CF, "Cheers, Daniel.")
    _close(m)
    return m


# ---------------------------------------------------------------------------------------------
def build_tx026(facts, wps):
    FID, d = "TX026", D("2026-10-06")
    LS, TH, HL, AS = "P042", "P043", "P054", "P017"
    for ref, f in [("TICKET:CHUB-388", None), ("TICKET:CHUB-371", None), ("ADR:ADR-021", None),
                   ("TICKET:CHUB-392", None), ("RULE:BR-FRD-031@v2", "text")]:
        assert_may(FID, ref, f)
    path = out_path(FID, "standup_fraud_settlement_squad_2026_10_06", "txt")
    sp = _speakers([LS, TH, HL, AS], d, {LS: {"label": "Linnea Sjoberg"}})
    m = Meeting(FID, path, facts, sp, util.rng(f"{FID}:dlg:{wps}"), wps=wps, chair=LS, domain="fraud",
                duration_min=15, meta_budget=1, digress_budget=1, crosstalk_budget=1)
    m.spacing.update(meta=120.0, dig=300.0, cross=200.0)
    _header(m, title_="Stand-up transcript - Hub Squad: Fraud & Settlement", d=d, start="09:30", minutes=15,
            squad="Hub Squad - Fraud & Settlement (fraud-referral-svc, settlement-svc, payment-orchestrator)",
            author=HL, sp=sp, ref="SQD-FS-SU-2026-10-06")
    t = Topic("su", ["the referral notice tests", "the payment retry tests", "the settlement screen fixes",
                     "the code review queue", "the hypercare defects", "the sprint goal", "the regression pack",
                     "the release notes"], domain="fraud", leads=[LS, TH], lines=[
        (TH, "Yesterday I finished the regression pack for payment-orchestrator. Today I'm on two of the hypercare defects from the settlement screens. No blockers."),
        (HL, "I'm updating the acceptance criteria for the notice-deadline stories so they match the rule wording."),
        (AS, "Sprint review on Thursday. Linnea, can the team show the payment retry behaviour?"),
        (LS, "The payments side has been quiet since the fix went in, which is exactly what we want."),
        (TH, "I'll pair with someone on the release notes this afternoon, they're behind."),
        (HL, "I've got questions on two of the settlement stories. I'll grab people after this rather than take time now."),
    ])
    m.say(LS, "Morning, all. Let's go round. Quick one today.")
    n = m.say(LS, "First, the Tier-3 threshold. Our change in fraud-referral-svc went in last week under CHUB-388, but triage-svc didn't pick up the new value until yesterday. Sofie's squad have the fix under CHUB-392, so nothing for us to do except watch the referrals.")
    m.doc.fact(n, needle="triage-svc didn't pick up the new value until yesterday", kind="general", world_ref="INCIDENT:INC-2026-1007",
               statement="INC-2026-1007: triage-svc did not pick up the Tier-3 threshold (CHUB-388) until 2026-10-05; the fix is CHUB-392.")
    m.fill(m.at(5, 0), t)
    n = m.say(TH, "On payments, every instruction to CPG now carries an idempotency key, per ADR-021, so a retry after a timeout can't create a second payment.")
    m.doc.fact(n, needle="every instruction to CPG now carries an idempotency key, per ADR-021", kind="general", world_ref="ADR:ADR-021",
               statement="ADR-021: every payment instruction to CPG carries an idempotency key (after the Wave 1 duplicate payments, CHUB-371).")
    m.fill(m.at(12, 0), t)
    m.say(LS, "Thanks, everyone. Shout if anything gets stuck.")
    _close(m)
    return m


# ---------------------------------------------------------------------------------------------
def build_tx061(facts, wps):
    FID, d = "TX061", D("2026-10-05")
    SB, AS, EF = "P040", "P017", "P049"
    for ref, f in [("INCIDENT:INC-2026-1007", "root_cause"), ("TICKET:CHUB-392", None), ("INTERFACE:CLX-IF-036", None),
                   ("RULE:BR-FRD-031@v2", "text")]:
        assert_may(FID, ref, f)
    path = out_path(FID, "standup_intake_triage_squad_2026_10_05", "txt")
    sp = _speakers([SB, AS, EF], d)
    m = Meeting(FID, path, facts, sp, util.rng(f"{FID}:dlg:{wps}"), wps=wps, chair=SB, domain="incident",
                duration_min=14, meta_budget=1, digress_budget=0, crosstalk_budget=1)
    m.spacing.update(meta=120.0, cross=200.0)
    _header(m, title_="Stand-up transcript - Hub Squad: Intake & Triage", d=d, start="09:00", minutes=14,
            squad="Hub Squad - Intake & Triage (fnol-intake-svc, triage-svc, assessment-svc, claim-core-svc, notification-svc)",
            author=SB, sp=sp, ref="SQD-IT-SU-2026-10-05")
    t = Topic("su", ["the threshold cache", "the config reload", "the triage tests", "the FNOL intake fixes",
                     "the assessment API backlog", "the hypercare defects", "the incident record", "the test evidence"],
                  domain="incident", leads=[SB, EF], lines=[
        (EF, "From an architecture point of view, a service that caches configuration should always reload on change. We'll add that to the standards."),
        (AS, "I'll let the Claims Director's office know we've found it and that the claims are being referred by hand."),
        (SB, "The rest of the board is fine. Hypercare defects are trending down."),
        (EF, "Let's make sure the test evidence for the fix shows a claim either side of the line."),
        (SB, "I'll keep the incident record updated through the day."),
    ])
    m.say(SB, "Morning. Let's start with the urgent one, then go round.")
    n = m.say(SB, "Compliance flagged on Friday that some Tier-3 claims scoring in the low sixties weren't referred. We've found it: triage-svc cached the referral thresholds and never reloaded the Tier-3 value after the change for the first of October. I've raised CHUB-392 to refresh the cache when the configuration changes.")
    m.doc.fact(n, needle="triage-svc cached the referral thresholds and never reloaded the Tier-3 value", kind="general",
               world_ref="INCIDENT:INC-2026-1007#root_cause",
               statement="Root cause of INC-2026-1007: triage-svc cached the referral thresholds and did not reload the Tier-3 value; fix CHUB-392.")
    m.say(AS, "And the claims that were missed are being referred manually today, so nothing gets lost.")
    m.fill(m.at(11, 30), t)
    m.say(SB, "Okay, thanks all. Fix in test this afternoon, I hope.")
    _close(m)
    return m


# ---------------------------------------------------------------------------------------------
def build_tx065(facts, wps):
    FID, d = "TX065", D("2026-10-20")
    CF, GS, DO, AK = "P051", "P052", "P025", "P048"
    for ref, f in [("WAVE:MW-2", "date"), ("WAVE:MW-2", "scope"), ("ADR:ADR-025", None), ("ADR:ADR-015", None)]:
        assert_may(FID, ref, f)
    path = out_path(FID, "standup_data_migration_2026_10_20", "txt")
    sp = _speakers([CF, GS, DO, AK], d, {CF: {"label": "Callum Fairbairn (IBM)"}})
    m = Meeting(FID, path, facts, sp, util.rng(f"{FID}:dlg:{wps}"), wps=wps, chair=CF, domain="reserving",
                duration_min=13, meta_budget=1, digress_budget=1, crosstalk_budget=1)
    m.spacing.update(meta=120.0, dig=300.0, cross=200.0)
    _header(m, title_="Stand-up transcript - Data Migration workstream", d=d, start="08:45", minutes=13,
            squad="Data Migration (IBM and Corvane)", author=CF, sp=sp, ref="DMG-SU-2026-10-20")
    t = Topic("su", ["the Nordic mappings", "the masked data refresh", "the extract jobs", "the mapping review",
                     "the reconciliation scripts", "the rehearsal environment", "the DB2 unloads", "the load scripts"],
              domain="reserving", leads=[CF, GS, DO], lines=[
        (GS, "I'm working through the Norwegian product mappings. A couple of code values need confirming with the Oslo team."),
        (DO, "The DB2 unloads for the next rehearsal are scripted. I just need the go-ahead on the environment."),
        (AK, "The steering confirmed the date, so the plan is fixed now. I'll circulate the updated version today."),
        (CF, "The reconciliation scripts from Wave 1 carry over. The Nordic products just add currency checks."),
        (GS, "The Swedish home product has a few fields that don't exist anywhere else. I've flagged them."),
        (DO, "Housekeeping on the unload datasets is done, so we've got the space back."),
    ])
    m.say(CF, "Morning, everyone. Quick round, then I need ten minutes with Gordon on the mappings.")
    n = m.say(CF, "Reminder of the scope: Wave 2 is UK home, commercial and liability, plus Norway and Sweden, cutting over on the 15th of February. Same approach as Wave 1, migrating region by region per ADR-015.")
    m.doc.fact(n, needle="Wave 2 is UK home, commercial and liability, plus Norway and Sweden, cutting over on the 15th of February",
               kind="general", world_ref="WAVE:MW-2",
               statement="Wave 2 (UK home, commercial, liability; Norway; Sweden) cuts over on 2027-02-15.")
    n = m.say(DO, "And rehearsal data stays masked, per ADR-025. The masked refresh for the Nordic products is running this week.")
    m.doc.fact(n, needle="rehearsal data stays masked, per ADR-025", kind="general", world_ref="ADR:ADR-025",
               statement="ADR-025: migration rehearsals use masked data.")
    m.fill(m.at(6, 0), t)
    m.fill(m.at(11, 0), t)
    m.say(CF, "Thanks, all. Gordon, stay on.")
    _close(m)
    return m


# ---------------------------------------------------------------------------------------------
def build_tx069(facts, wps):
    FID, d = "TX069", D("2026-11-09")
    AK, VA, AS, NH = "P048", "P047", "P017", "P032"
    for ref, f in [("TICKET:CHUB-441", None), ("TICKET:CHUB-298", "status_history"), ("TICKET:CHUB-421", None),
                   ("TICKET:CHUB-415", None), ("WAVE:MW-2", "freeze"), ("COMMITTEE:COM-04", "cadence"),
                   ("COMMITTEE:COM-03", "cadence")]:
        assert_may(FID, ref, f)
    path = out_path(FID, "standup_programme_pmo_2026_11_09", "txt")
    sp = _speakers([AK, VA, AS, NH], d)
    m = Meeting(FID, path, facts, sp, util.rng(f"{FID}:dlg:{wps}"), wps=wps, chair=AK, domain="steering",
                duration_min=14, meta_budget=1, digress_budget=1, crosstalk_budget=1)
    m.spacing.update(meta=120.0, dig=300.0, cross=200.0)
    _header(m, title_="Stand-up transcript - Programme PMO", d=d, start="08:30", minutes=14,
            squad="Programme Skerry PMO", author=AK, sp=sp, ref="PMO-SU-2026-11-09")
    t = Topic("su", ["the RAID log", "the steering pack", "the Wave 2 plan", "the release calendar", "the resource plan",
                     "the risk register", "the dependency tracker", "the lessons log"], domain="steering",
              leads=[AK, AS, NH], lines=[
        (VA, "I'll review the steering pack draft tonight and send comments first thing."),
        (AS, "Product backlog is groomed for the next two sprints. Nothing unusual."),
        (NH, "Resource plan for the squads is stable. The new squad is settling in."),
        (AK, "The RAID log is up to date. Two risks I want to talk about at steering, both on environments."),
        (VA, "The lessons log from Wave 1 is in good shape. I'd like it referenced in the Wave 2 plan."),
    ])
    m.say(AK, "Morning, all. Busy week: CAB on Wednesday, steering on Thursday. Let's go round.")
    n = m.say(AK, "I've raised CHUB-441 for the Wave 2 cut-over plan, version one. The freeze is from 18:00 on Friday 12 February to 06:00 on Monday 15 February, same shape as Wave 1.")
    m.doc.fact(n, needle="I've raised CHUB-441 for the Wave 2 cut-over plan", kind="general", world_ref="TICKET:CHUB-441",
               statement="CHUB-441 (Wave 2 cut-over plan v1; freeze 2027-02-12 18:00 to 2027-02-15 06:00) is raised on 2026-11-09.")
    n = m.say(NH, "For CAB on Wednesday, the November release has three items: CHUB-298, the CLRFR040 fix, which has been in review since last Wednesday; CHUB-421, the notification event, still in progress; and CHUB-415, the CODEOWNERS change, which is open.")
    m.doc.fact(n, needle="CHUB-298, the CLRFR040 fix, which has been in review since last Wednesday", kind="general",
               world_ref="TICKET:CHUB-298#status_history",
               statement="As at 2026-11-09, CHUB-298 has been In Review since 2026-11-04; CHUB-421 is In Progress and CHUB-415 is open, all for release R2026.11.")
    m.fill(m.at(11, 30), t)
    m.say(AK, "Thanks, everyone. Pack comments by tomorrow lunchtime, please.")
    _close(m)
    return m


STANDUPS = [
    ("TX025", build_tx025, 1700, 2300, 2.6),
    ("TX026", build_tx026, 1700, 2300, 2.6),
    ("TX061", build_tx061, 1500, 2100, 2.6),
    ("TX065", build_tx065, 1500, 2100, 2.6),
    ("TX069", build_tx069, 1600, 2200, 2.6),
]

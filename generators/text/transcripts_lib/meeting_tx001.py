"""TX001: Programme Skerry Steering Committee, 8 Oct 2026 (MTG-008), about two hours.

Plants PL-189/190 (C15 in-transcript correction of the Wave 2 date), PL-191 ('PR' / 'the CFO'
approves the £1.8m drawdown, DEC-010) and PL-192 (the Claims Director is never named by surname).
"""
from __future__ import annotations

from generators.common import util

from .common import W, D, out_path, placement, assert_may
from .dialogue import Meeting, Topic
from .meetings_common import speakers_for, transcript_header, footer

FID = "TX001"
MTG = "MTG-008"
DATE = D("2026-10-08")
PATH = out_path(FID, "steering_committee_2026_10_08_transcript", "txt")

DF, CD, PR, AN, AS, NH, VA, AK = "P004", "P005", "P001", "P006", "P017", "P032", "P047", "P048"


def _checks():
    for ref, f in [("DECISION:DEC-010", None), ("DECISION:DEC-011", None), ("WAVE:MW-2", "freeze"),
                   ("TIMELINE:metrics", "wave1_open_defects"), ("INCIDENT:INC-2026-0914", "impact"),
                   ("INCIDENT:INC-2026-1007", "impact"), ("SYSTEM:SYS01", "decommission_target"),
                   ("SYSTEM:SYS24", "decommission_target"), ("ADR:ADR-026", "status"), ("ADR:ADR-021", None),
                   ("TICKET:CHUB-298", None), ("TICKET:CHUB-401", None), ("TEAM:T30", "lead_history"),
                   ("RULE:BR-FRD-031@v2", "text"), ("RULE:BR-FRD-034@v1", "text"), ("PERSON:P001", "responsibilities"),
                   ("TIMELINE:metrics", "programme_budget_gbp_m"), ("PERSON:P002", "responsibilities")]:
        assert_may(FID, ref, f)


def build(facts, wps: float) -> Meeting:
    _checks()
    sp = speakers_for(MTG, DATE, overrides={
        CD: {"label": "Ingrid (Claims Director)", "first": "Ingrid", "display_role": "Claims Director"},
        DF: {"weight": 1.2}, PR: {"weight": 0.9}, AN: {"weight": 0.9}, VA: {"weight": 0.8},
    })
    r = util.rng(f"{FID}:dialogue:{wps}")
    m = Meeting(FID, PATH, facts, sp, r, wps=wps, chair=DF, domain="steering", duration_min=120,
                meta_budget=9, digress_budget=3, crosstalk_budget=6)
    m.header(transcript_header(
        doc_ref="SKR-GOV-TRN-2026-10", title_="Transcript - Programme Skerry Steering Committee 8 Oct 2026",
        meeting_id=MTG, venue="Corvane House, London (Board Room) and video bridge", chair=DF, author=AK,
        approver=DF, speakers=sp, d=DATE, forum_line="Programme Skerry Steering Committee (monthly)",
        classification="Internal - Programme Confidential",
        versions=[("0.1", "2026-10-08", "A. Kesavan", "Automated transcript exported from the bridge recording"),
                  ("0.2", "2026-10-08", "A. Kesavan", "Speaker labels corrected; inaudible passages marked"),
                  ("1.0", "2026-10-08", "D. Ferrier (chair)", "Approved as the verbatim record of the meeting")],
        extra_notes=["The Claims Director spoke from the Board Room microphone; her lines are labelled by role.",
                     "Formal minutes and the action log are issued separately by the PMO."]))
    pl = lambda k: placement(FID, k)

    # ---------------------------------------------------------------- topics
    t_open = Topic("opening", ["the action log", "the decisions log", "the pack", "the board update"], leads=[DF, AK], lines=[
        (DF, "The pack went out on Tuesday, so I'll assume people have read it and we'll take the slides as read where we can."),
        (AK, "All of last month's actions are either closed or on today's agenda, so I won't go through them one by one."),
        (DF, "If anything's still open from September that isn't covered today, shout now."),
        (NH, "Nothing from me on the action log. Mine are closed."),
        (AN, "Same here. I had the one on environment capacity and that's closed in the log."),
        (VA, "Just to say, from the IBM side, thank you for the time this afternoon. We know it's a busy month."),
        (DF, "Let's try to finish on time today. I've got the board straight after."),
    ])
    t_wave1 = Topic("wave1", ["hypercare", "the defect backlog", "the hypercare rota", "handler feedback from Leeds",
                              "the known-errors list", "the workaround guide", "the daily defect triage",
                              "the stabilisation plan", "the payment reconciliation", "the post-cut-over survey",
                              "the motor handlers' experience", "the month-end on the Hub"],
                    domain="steering", leads=[AS, NH, CD], lines=[
        (CD, "The motor teams in Leeds have been very good about it. The first week was hard, there's no point pretending otherwise, but the second week felt different."),
        (AS, "We're running the defect triage every morning with the squads and the business leads, and we'll keep doing that until the backlog is somewhere we're comfortable with."),
        (NH, "The squads have been carrying hypercare on top of the Wave 2 work, so I'm watching for fatigue as much as anything."),
        (CD, "What the handlers tell me is that the case estimate screen is better than the old one, once they've found where everything is."),
        (AS, "Most of what's left is usability rather than function. Labels, field order, that kind of thing."),
        (VA, "From the IBM side we've kept the hypercare team at full strength and we'll review that with Neil."),
        (AN, "I'd like us to be careful about declaring victory. The first motor month-end on the Hub is the real test."),
        (PR, "Finance's interest is the payment reconciliation, and from what I've seen that's now clean."),
        (DF, "Credit where it's due: the cut-over weekend itself went as well as any of us could have hoped, apart from the payments issue."),
        (AK, "We're capturing everything from Wave 1 in a lessons-learned log for Wave 2, and it gets reviewed weekly."),
        (CD, "The adjusters have noticed the difference too. Instructions are going out cleaner than they did from the ledger."),
        (AS, "We've had good engagement from the team leaders in the daily huddles. They tell us very quickly when something isn't right."),
        (NH, "I'd rather we kept the hypercare structure a bit longer than we need than pulled it out too early."),
        (CD, "One thing the handlers keep raising is search. They want to find a claim by the third party's registration, and today that's clunky."),
        (AS, "That one's on the backlog, it's a usability fix, not a defect as such."),
    ], qa=[
        (DF, "{nB}, how are the team leaders finding it, honestly?", CD,
         "Honestly? Tired, but positive. They can see it's better. They just want the small things fixed quickly."),
        (AN, "Are we still seeing the same defects come back, or are they new ones now?", AS,
         "Mostly new ones, which is a good sign. The repeat offenders have largely been dealt with."),
    ])
    t_fin = Topic("finance", ["the programme budget", "the contingency position", "the forecast to complete",
                              "the benefits case", "the cost reporting", "the IBM change request process", "the run-rate",
                              "the capitalisation treatment", "the quarterly reforecast"],
                  domain="steering", leads=[PR, AK, VA], lines=[
        (PR, "I'm not going to walk through the numbers line by line; they're in the appendix and Finance has reviewed them."),
        (AK, "The forecast is in the pack, and it's the same basis we used last month, so it's like for like."),
        (PR, "My main ask is that we keep the forecast honest. I'd rather see a number go up early than get a surprise in the spring."),
        (VA, "We've been through our change requests with Finance and there's nothing new this month."),
        (DF, "I think the key message for the board is that we're still inside the envelope."),
        (PR, "And just to be clear for anyone newer to this, the contingency is held centrally and anything drawn has to come back here."),
        (AN, "The technology run costs are separate, and I'll pick those up in the annual planning round, not here."),
        (PR, "We'll want the benefits tracking to start properly once motor has a full quarter on the Hub."),
    ])
    t_wave2 = Topic("wave2", ["the Wave 2 plan", "the rehearsal plan", "the Nordic data mapping", "the Wave 2 scope",
                              "the freeze comms plan", "the cut-over runbook", "the broker letter",
                              "the Norway and Sweden readiness", "the UK home and commercial readiness",
                              "the training plan for home handlers", "the Wave 2 readiness checklist"],
                    domain="steering", leads=[AK, AS, NH], lines=[
        (AK, "The Wave 2 plan is built from the Wave 1 plan, with the lessons applied, and with more rehearsal time for the Nordic data."),
        (AS, "The home and commercial handlers are a different population from motor. More complex claims, longer tails, so the training has to reflect that."),
        (NH, "The squads are already working on the Nordic product configuration, and that's tracking."),
        (CD, "For the Nordic teams, I want the training in their own language where we can manage it. That made a real difference in Denmark."),
        (AK, "We'll bring the detailed rehearsal plan to the next steering, once the environments are confirmed."),
        (VA, "The IBM migration team have taken the Wave 1 reconciliation approach and are extending it to the Nordic products."),
        (AS, "Brokers will need notice of the freeze as well. We learned that the hard way with motor."),
        (DF, "I'd like the freeze comms drafted early so we're not doing them in a rush in January."),
        (AN, "From a technology side, the environments are the constraint, not the people."),
        (CD, "And liability is a different animal again. The claims are slower, but they're the ones that end up in front of a judge."),
        (AK, "There's a Wave 2 readiness epic in the backlog, CHUB-401, and everything hangs off that."),
    ])
    t_clara = Topic("clara", ["the CLARA decommissioning plan", "the archive approach", "read-only enquiry",
                              "the mainframe capacity plan", "the residual CLARA workload", "the SUBTRAK retirement",
                              "the data retention position", "the legacy skills risk", "the interface retirement plan"],
                    domain="steering", leads=[NH, AN, AS], lines=[
        (NH, "Graham's team have been brilliant through all of this, and they're also the people we need to decommission it. That's a capacity question for next year."),
        (AN, "My concern with the decommission is the long tail of reporting. People always find a report they forgot about."),
        (NH, "We've started an inventory of everything that still reads from the ledger after Wave 2, and it's longer than I'd like."),
        (AS, "Read-only enquiry is the big one for the business. Handlers will want to look things up on old claims for a while."),
        (CD, "I'd want the archived claims searchable. If a customer calls about an old claim, the handler can't say 'I don't know'."),
        (DF, "Let's make sure the decommission plan has the business in it, not just the technology."),
        (NH, "The sub-ro team are keen to get off SUBTRAK. It's been creaking for a while."),
        (AN, "Data retention needs the DPO's input before we commit to an archive design."),
    ])
    t_draw = Topic("drawdown", ["the contingency request", "the Wave 2 resourcing", "the rehearsal environment work",
                                "the IBM team extension", "the risk position on Wave 2", "the drawdown governance",
                                "the Nordic migration effort", "the additional test capacity"],
                   domain="steering", leads=[VA, AK, PR], lines=[
        (VA, "We've tried to be disciplined about this. We're asking for what we need to protect the date, not a cushion."),
        (AK, "The request is set out on the slide, and the detail is in the appendix, broken down by workstream."),
        (PR, "I've been through the breakdown with Arjun and with my team, and I'm comfortable it's been challenged properly."),
        (AN, "From the technology side, the environments piece is the bit I'd least want to cut."),
        (NH, "If we don't do this, the risk doesn't disappear; it just moves to the cut-over weekend."),
        (DF, "I'd like the board to see this as protecting the plan rather than a cost overrun."),
        (VA, "And we'll report against the drawdown separately, so you can see exactly where it goes."),
    ])
    t_fraud = Topic("fraud", ["the Tier-3 referral change", "the CLRFR040 defect", "the SIU workload",
                              "the customer notice process", "the FR1 return", "the Compliance daily check",
                              "the referral volume", "the November release"],
                    domain="fraud", leads=[CD, AS, NH], lines=[
        (CD, "SIU are watching the referral volumes closely since the change. Niall will report properly at the Fraud Forum."),
        (AS, "The November release is a small one, which is deliberate. We didn't want anything big straight after Wave 1."),
        (NH, "CAB will look at the November release in the usual way. Nothing unusual about it."),
        (CD, "From a customer point of view, the referral letters are going out as they should. I've had no complaints escalate to me."),
        (PR, "Is there any financial exposure from the claims that weren't referred?"),
        (CD, "Not that we know of. They were picked up and referred by hand, and SIU are working them in the normal way."),
    ])
    t_people = Topic("people", ["the new squad structure", "knowledge transfer from IBM", "the hiring plan",
                                "the CLARA skills risk", "the change network", "squad leadership", "the handover plan"],
                     domain="steering", leads=[NH, AN, VA], lines=[
        (NH, "We're moving to squads that line up with the claims journey, which should make ownership clearer."),
        (VA, "Knowledge transfer is built into our plan for next year. We don't want Corvane dependent on us forever."),
        (AN, "The CLARA skills risk is real. There are people in Leeds who know things that aren't written down anywhere."),
        (CD, "The change network has been the unsung hero of Wave 1, honestly. The champions on the floor made a huge difference."),
        (DF, "Let's make sure we recognise the change champions properly. A thank-you from this group would go a long way."),
    ])
    t_aob = Topic("aob", ["any other business", "the board update", "the next steering", "the action recap"],
                  domain="steering", leads=[DF, AK], lines=[
        (DF, "I'll take the key messages to the board: Wave 1 stable, Wave 2 on track for February, contingency drawn with approval."),
        (AK, "We'll have the minutes out within the week."),
    ])

    # ---------------------------------------------------------------- 00:00 opening
    m.say(DF, "Okay, I think we're quorate, so let's make a start. Good afternoon, everyone. This is the October steering committee for Programme Skerry.")
    m.say(DF, "We've got a full agenda: Wave 1 post cut-over, finance, the Wave 2 plan, CLARA decommissioning, a contingency request from the programme, and a short item on fraud and people. Arjun's recording for the minutes as usual.")
    m.say(AK, "Yes, recording's on. Thanks, Duncan.")
    lc = m.say(DF, "Claims Director, welcome back. I gather you've come straight from Leeds.")
    m.say(CD, "Straight off the train, yes. Happy to be here. I'll give the business view on Wave 1 when we get to it.")
    m.doc.fact(lc, needle="Claims Director, welcome back", statement="In the October 2026 steering transcript the Claims Director (Ingrid Ashby) is addressed by role, not by surname.",
               kind="alias_use", placement=pl("tx1_cd"), end=lc,
               notes="Ingrid Ashby is labelled 'Ingrid (Claims Director)' throughout; her surname never appears in TX001.")
    m.script(m.at(3, 10), t_open, [
        (DF, "Right. Item two, Wave 1. Aisha, do you want to lead, and then the Claims Director can add the business view?"),
    ])

    # ---------------------------------------------------------------- 00:05 Wave 1
    m.say(AS, "Thanks, Duncan. So, Wave 1, UK motor, cut over on Monday 14 September. We're now a little over three weeks in. The headline is that the platform is stable and the handlers are working claims end to end on the Hub.")
    n = m.say(AS, "On defects, as at Monday the 5th of October we had no Sev 1s open, 14 Sev 2 and 57 Sev 3. The Sev 2s are the ones we're chasing hardest, and they all have a fix date.")
    m.doc.fact(n, needle="no Sev 1s open, 14 Sev 2 and 57 Sev 3", kind="needle", world_ref="TIMELINE:metrics#wave1_open_defects",
               statement="As at 2026-10-05, Wave 1 had 0 Sev 1, 14 Sev 2 and 57 Sev 3 defects open.")
    m.script(m.at(9, 30), t_wave1, [
        (DF, "Can we talk about the payments issue? I know it's been covered elsewhere, but for the record."),
        (NH, "Sure. On the cut-over Monday, payment-orchestrator retried instructions to the payments gateway after a timeout, without an idempotency key, so some instructions went through twice."),
    ])
    n = m.say(NH, "It affected 18 claims, paid twice, £41,236.50 in total, and all of it was recalled by the 18th of September. The fix went in under CHUB-371, and the Design Authority accepted ADR-021 so that every payment instruction carries an idempotency key from now on.")
    m.doc.fact(n, needle="18 claims, paid twice, £41,236.50 in total", kind="needle", world_ref="INCIDENT:INC-2026-0914#impact",
               statement="INC-2026-0914: 18 claims were paid twice on the Wave 1 cut-over, £41,236.50 in total, all recalled by 2026-09-18.")
    m.doc.fact(n, needle="ADR-021", kind="general", world_ref="ADR:ADR-021",
               statement="After the Wave 1 duplicate payments, ADR-021 requires an idempotency key on every payment instruction (fix under CHUB-371).")
    m.say(PR, "And from Finance's side the recalls have all been reconciled. I'd just like the lessons from that properly written up for Wave 2.")
    m.say(AK, "They're in the lessons log, and there's a specific test in the Wave 2 rehearsal plan for exactly that scenario.")
    m.script(m.at(14, 40), t_wave1, [
        (DF, "Claims Director, anything from the business side before we move on?"),
        (CD, "One thing, Duncan. The Tier-3 referral change went live on the 1st of October, the threshold of 60 for Tier-3 claims, and the Hub didn't pick it up straight away."),
    ])
    n = m.say(CD, "Triage-svc had cached the old value and didn't reload it until the 5th, so 9 Tier-3 claims that scored between 60 and 64 weren't referred automatically. They've all been referred manually since.")
    m.doc.fact(n, needle="9 Tier-3 claims that scored between 60 and 64 weren't referred automatically", kind="needle",
               world_ref="INCIDENT:INC-2026-1007#impact",
               statement="INC-2026-1007: triage-svc did not reload the Tier-3 threshold until 2026-10-05; 9 Tier-3 claims scoring 60-64 were not referred automatically and were referred manually.")
    m.say(AS, "That's INC-2026-1007. The fix is CHUB-392, the thresholds now refresh when the configuration changes.")
    m.say(AN, "I'd like to understand why that wasn't caught in testing, but maybe not in this forum.")
    m.say(DF, "Agreed. Neil, can you pick that up with the squads and bring a short note back?")
    m.say(NH, "Will do.")

    # ---------------------------------------------------------------- 00:22 finance
    m.script(m.at(22, 5), t_wave1, [
        (DF, "Okay, let's move to finance. PR, over to you."),
        (PR, "Thanks, Duncan. I'll keep this short because the detail's in the appendix."),
    ])
    n = m.say(PR, "We're still working inside the £48.6m business case that my predecessor, Gareth Whitcombe, signed in November 2024. The forecast hasn't moved materially since last month.")
    m.doc.fact(n, needle="£48.6m business case", kind="general", world_ref="TIMELINE:metrics#programme_budget_gbp_m",
               statement="The Programme Skerry business case is £48.6m; it was signed by the former CFO Gareth Whitcombe in November 2024.")
    m.say(PR, "The one thing on the horizon is the contingency request, which Arjun and Victoria will bring later on the agenda, so I'll hold my comments on that until then.")
    m.script(m.at(36, 30), t_fin, [
        (DF, "Thanks, PR. If there's nothing else on finance, let's go to Wave 2. Arjun."),
        (AK, "Thanks. Let me share the plan. Can everyone see that?"),
        (VA, "Yes, we can see it."),
    ])

    # ---------------------------------------------------------------- 00:38 Wave 2
    m.say(AK, "So Wave 2 is UK home, commercial and liability, and then Norway and Sweden, all in one wave. That's the largest wave by product count.")
    m.fill(m.at(41, 7), t_wave2)
    n = m.say(AK, "The plan on the slide has the cut-over on Monday 18 January 2027, with the freeze running over the weekend before. The rehearsals are laid out backwards from that date.")
    m.doc.fact(n, needle="cut-over on Monday 18 January 2027", kind="contradiction_old", placement=pl("tx1_wrong"),
               statement="At about 00:41 Arjun Kesavan states the Wave 2 cut-over is on 2027-01-18 (a misstatement, corrected at about 00:44).")
    m.say(PR, "Sorry, January? That's not the date I've got in my notes.")
    m.say(AK, "Let me just check the version I've got up. Carry on and I'll come back to it.")
    m.fill(m.at(44, 2), t_wave2, min_gap=4)
    n = m.say(AS, "Sorry, Arjun, can I go back to the date on the slide before we move on? That's the old date. Wave 2 is 15 February 2027. The 18th of January was in the draft plan and it's void. We shouldn't be showing it anywhere.")
    m.doc.fact(n, needle="Wave 2 is 15 February 2027", kind="contradiction_new", placement=pl("tx1_right"),
               statement="At about 00:44 Aisha Siddiqui corrects him: Wave 2 cut-over is 2027-02-15 and the January date is void.")
    m.say(AK, "You're absolutely right, apologies. That's an old slide from the draft pack. Fifteenth of February. The January date is void.")
    n = m.say(DF, "Let's be clear for the record, then. Wave 2 cut-over is confirmed as 15 February 2027, and the earlier draft date of 18 January is void. Arjun, can you make sure every copy of that plan is updated?")
    m.doc.fact(n, needle="Wave 2 cut-over is confirmed as 15 February 2027", kind="needle", world_ref="DECISION:DEC-011",
               statement="DEC-011 (steering, 2026-10-08): Wave 2 cut-over confirmed as 2027-02-15; the earlier draft date 2027-01-18 is void.")
    m.say(AK, "Yes, I'll reissue it today.")
    n = m.say(AK, "So, with the right date: the freeze runs from 18:00 on Friday 12 February to 06:00 on Monday 15 February, the same shape as Wave 1.")
    m.doc.fact(n, needle="18:00 on Friday 12 February to 06:00 on Monday 15 February", kind="needle", world_ref="WAVE:MW-2#freeze",
               statement="The Wave 2 freeze runs from 2027-02-12 18:00 to 2027-02-15 06:00.")
    m.script(m.at(57, 20), t_wave2, [
        (DF, "Good. Thanks, Arjun, and thanks, Aisha, for catching that. Next item, CLARA decommissioning. Neil."),
    ])

    # ---------------------------------------------------------------- 00:58 CLARA
    n = m.say(NH, "Thanks. The decommission target for CLARA is still 30 September 2027. Nothing has changed there, but it depends on Wave 2 landing in February and on us finding a home for the residual workload.")
    m.doc.fact(n, needle="decommission target for CLARA is still 30 September 2027", kind="needle", world_ref="SYSTEM:SYS01#decommission_target",
               statement="CLARA's decommission target is 2027-09-30.")
    n = m.say(NH, "The big open question is read-only enquiry after cut-over. ADR-026 proposes a read-only CLARA enquiry, but it's still a proposal; the Design Authority hasn't accepted it yet.")
    m.doc.fact(n, needle="ADR-026 proposes a read-only CLARA enquiry", kind="general", world_ref="ADR:ADR-026#status",
               statement="ADR-026 (read-only CLARA enquiry after cut-over) is still proposed, not accepted, as at 2026-10-08.")
    n = m.script(m.at(4, hh=1), t_clara, [
        (AS, "And on SUBTRAK, the retirement target is still 31 December this year. The epic for that is CHUB-430 and Freya's team are working through the open recovery cases."),
    ])[-1]
    m.doc.fact(n, needle="retirement target is still 31 December this year", kind="general",
               world_ref="SYSTEM:SYS24#decommission_target", statement="SUBTRAK's retirement target is 2026-12-31 (epic CHUB-430).")
    m.script(m.at(10, 30, hh=1), t_clara, [
        (DF, "Thanks. Let's move to the contingency request. Victoria, Arjun."),
    ])

    # ---------------------------------------------------------------- 01:11 drawdown
    m.say(VA, "Thanks, Duncan. We're asking the committee to approve a contingency drawdown of £1.8m for Wave 2. It's set out on the slide, and the breakdown is in the appendix.")
    m.say(AK, "The short version is that Wave 2 is bigger and more complex than Wave 1, and we want to protect the February date rather than find ourselves short in January.")
    m.fill(m.at(19, 0, hh=1), t_draw)
    n = m.say(DF, "So, PR, as the CFO this one is your call. Anything above half a million comes to you.")
    m.doc.fact(n, needle="PR, as the CFO", kind="alias_use", placement=pl("tx1_pr"),
               statement="Speakers call Priya Raman 'PR' and 'the CFO' in the October 2026 steering committee.")
    m.doc.fact(n, needle="Anything above half a million comes to you", kind="general", world_ref="PERSON:P001#responsibilities",
               statement="The CFO (Priya Raman) approves programme budget drawdowns above £500,000.")
    n = m.say(PR, "Yes. I've been through it with my team and with Arjun. I'm comfortable, so I'll approve the £1.8m contingency drawdown for Wave 2. I'll confirm it in writing after the meeting.")
    m.doc.fact(n, needle="approve the £1.8m contingency drawdown for Wave 2", kind="needle", world_ref="DECISION:DEC-010",
               statement="DEC-010: the CFO, Priya Raman, approves a £1.8m contingency drawdown for Wave 2 at the 2026-10-08 steering committee.")
    m.say(DF, "Thank you. And for the minutes, I'm happy to support that as chair. So that's approved.")
    m.say(VA, "Thank you both. We'll report against it separately every month.")
    m.say(CD, "Just one comment from me. I'd like some of that to go towards the Nordic training. My view, for what it's worth, is that's where Wave 2 will be won or lost.")
    m.say(AK, "Noted. Training is one of the lines in the breakdown, and we'll make sure the Nordic share is visible.")

    # ---------------------------------------------------------------- 01:32 fraud
    m.script(m.at(31, 50, hh=1), t_draw, [
        (DF, "Okay, short item on fraud and regulatory. Claims Director, Aisha."),
    ])
    n = m.say(CD, "So, as I said earlier, BR-FRD-031 version 2 went live on 1 October. Tier-3 claims are now referred to SIU at a Sentinel score of 60 or more; everything else stays at 65. That came out of the Fraud Rules Workshop last month.")
    m.doc.fact(n, needle="Tier-3 claims are now referred to SIU at a Sentinel score of 60 or more", kind="needle",
               world_ref="RULE:BR-FRD-031@v2", statement="From 2026-10-01 (BR-FRD-031 v2) Tier-3 claims are referred at a Sentinel score of 60 or more; the general threshold stays 65.")
    n = m.say(AS, "And CHUB-298, the CLARA batch sweep that still has the old threshold hard-coded in CLRFR040, is still open. It's planned for the November release, R2026.11. Until then, Compliance run their daily query for unreferred claims.")
    m.doc.fact(n, needle="CHUB-298", kind="general", world_ref="TICKET:CHUB-298",
               statement="As at 2026-10-08, CHUB-298 (CLRFR040 hard-coded threshold) is still open and planned for release R2026.11.")
    n = m.say(CD, "The first FR1 return went in on time in July, and the Q3 one is due by the 30th of October, thirty days after quarter end. Ruth has that in hand.")
    m.doc.fact(n, needle="due by the 30th of October, thirty days after quarter end", kind="general", world_ref="RULE:BR-FRD-034@v1",
               statement="The NISA-FR1 return is due 30 days after quarter end; the Q3 2026 return is due by 2026-10-30.")
    m.script(m.at(44, 40, hh=1), t_fraud, [
        (DF, "Thank you. Last substantive item, people. Neil."),
    ])

    # ---------------------------------------------------------------- 01:45 people
    n = m.say(NH, "Quick update. From 1 November we're standing up a Recoveries & Documents squad, led by Tariq Hussain. That completes the squad structure we agreed earlier in the year.")
    m.doc.fact(n, needle="Recoveries & Documents squad, led by Tariq Hussain", kind="general", world_ref="TEAM:T30#lead_history",
               statement="A Hub Squad - Recoveries & Documents, led by Tariq Hussain, is formed from 2026-11-01.")
    m.script(m.at(53, 10, hh=1), t_people, [
        (DF, "Thanks, Neil. Any other business? No? Arjun, can you recap the actions and decisions?"),
    ])

    # ---------------------------------------------------------------- 01:54 recap
    n = m.say(AK, "Sure. Decisions: one, the CFO approved the £1.8m contingency drawdown for Wave 2. Two, Wave 2 cut-over is confirmed as 15 February 2027, and the January date is void.")
    m.doc.fact(n, needle="Wave 2 cut-over is confirmed as 15 February 2027, and the January date is void", kind="needle",
               world_ref="DECISION:DEC-011", statement="The action recap restates DEC-011: Wave 2 on 2027-02-15; the January date is void.")
    m.say(AK, "Actions: me, reissue the Wave 2 plan with the February date and withdraw the old slide. P. Raman, to confirm the drawdown in writing. Aisha, to circulate the defect burn-down weekly until the Sev 2s are closed. Neil, a short note on the Tier-3 configuration incident, and the CLARA decommissioning plan at the next meeting.")
    m.say(PR, "Yes, I'll send that email this afternoon.")
    m.say(DF, "Anything else before we close? Any other business at all?")
    m.fill(m.at(58, 0, hh=1), t_aob)
    m.say(DF, "Thanks, everyone. Good session. I'll let you have a couple of minutes back.")
    m.say(CD, "Thanks, Duncan.")
    m.say(VA, "Thanks, all.")
    m.note("Recording stopped.")
    footer(m, DATE, AK)
    return m

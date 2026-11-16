"""TX002: Fraud Rules Workshop, 17 Sep 2026 (MTG-007), about two hours.

Plants PL-196 (~00:12 'what we used to call FRAUDNET'), PL-195 (~00:55, EXCLUSIVE: ~41% more referrals
if 60 applied to all claims; option rejected), PL-193 (~01:35 DEC-014, Tier-3 at 60 from 2026-10-01,
C01 newer-than-the-manual) and PL-194 (~01:48 DEC-015 deferrals beyond 30 days).
"""
from __future__ import annotations

from generators.common import util

from .common import D, out_path, placement, assert_may
from .dialogue import Meeting, Topic
from .meetings_common import speakers_for, transcript_header, footer

FID = "TX002"
MTG = "MTG-007"
DATE = D("2026-09-17")
PATH = out_path(FID, "fraud_rules_workshop_2026_09_17_transcript", "txt")

NB, IA, OL, RD, RO, LS, HL, AS = "P008", "P005", "P027", "P028", "P037", "P042", "P054", "P017"


def _checks():
    for ref, f in [("DECISION:DEC-014", None), ("DECISION:DEC-015", None), ("DECISION:DEC-016", None),
                   ("SYSTEM:SYS03", "aliases"), ("RULE:BR-FRD-031@v1", "text"), ("RULE:BR-FRD-031@v2", "text"),
                   ("RULE:BR-FRD-035@v2", "text"), ("RULE:BR-FRD-033@v1", "text"), ("RULE:BR-FRD-032@v2", "text"),
                   ("RULE:BR-FRD-036@v2", "text"), ("RULE:BR-FRD-036@v1", "parameters.max_deferral_days"),
                   ("RULE:BR-TRI-003@v3", "text"), ("INCIDENT:INC-2026-0518", "impact"),
                   ("INCIDENT:INC-2026-0518", "workaround"), ("TIMELINE:metrics", "fraud_referrals_count"),
                   ("REPORT:NISA-FR1", "submissions"), ("ADR:ADR-020", None), ("PERSON:P027", "responsibilities"),
                   ("TICKET:CHUB-298", None)]:
        assert_may(FID, ref, f)
    assert W_may_exclusive()


def W_may_exclusive() -> bool:
    from .common import W
    return W.may_state(FID, "DECISION:DEC-016", "impact_estimate")


def build(facts, wps: float) -> Meeting:
    _checks()
    sp = speakers_for(MTG, DATE, overrides={NB: {"weight": 1.2}, OL: {"weight": 1.2}, RD: {"weight": 1.1},
                                            HL: {"weight": 0.7}, AS: {"weight": 0.8}})
    sp[LS]["label"] = "Linnea Sjoberg"
    r = util.rng(f"{FID}:dialogue:{wps}")
    m = Meeting(FID, PATH, facts, sp, r, wps=wps, chair=NB, domain="fraud", duration_min=120,
                meta_budget=8, digress_budget=3, crosstalk_budget=5)
    m.header(transcript_header(
        doc_ref="CFS-WKS-TRN-2026-09", title_="Transcript - Fraud Rules Workshop 17 Sep 2026", meeting_id=MTG,
        venue="Leeds Claims Centre (Wharfe meeting room) and video bridge", chair=NB, author=HL, approver=NB,
        speakers=sp, d=DATE, forum_line="Claims Fraud Forum - extended workshop session",
        versions=[("0.1", "2026-09-17", "H. Lyle", "Automated transcript from the bridge recording"),
                  ("0.2", "2026-09-17", "H. Lyle", "Speaker labels and rule references checked"),
                  ("1.0", "2026-09-17", "N. Brannigan (chair)", "Approved; minutes to follow separately")],
        extra_notes=["Rule references (BR-FRD-xxx, BR-TRI-003) are as spoken; see the rule catalogue for wording.",
                     "The formal minutes of this workshop are issued as a separate document."]))
    pl = lambda k: placement(FID, k)

    t_open = Topic("opening", ["the workshop scope", "the rule catalogue", "the referral process", "the agenda for today"],
                   domain="fraud", leads=[NB, HL], lines=[
        (NB, "This is a working session, so I'd like people to challenge. If you think something's wrong, say so now rather than after it's in production."),
        (HL, "I'll capture decisions and actions as we go, and read them back at the end so we can correct anything."),
        (IA, "From the claims side, my interest is that whatever we do doesn't slow down the genuine customers."),
        (RO, "And mine is that we can evidence every change to NISA if they ask. Which they will."),
    ])
    t_model = Topic("model", ["the scoring model", "the score distribution", "the calibration work", "the referral volume",
                              "the model monitoring", "the score bands", "the false-positive rate", "the scoring feed"],
                    domain="fraud", leads=[OL, NB], lines=[
        (OL, "The model hasn't changed since the spring. What's changed is the mix of claims coming through, with motor now on the Hub."),
        (OL, "I look at the score distribution every week. It's stable. There's no drift that worries me."),
        (NB, "Oskar's team have done a lot of quiet work on monitoring, which we don't talk about enough."),
        (RD, "From the investigators' side, the quality of the referrals since April has been decent. Fewer obvious false positives."),
        (OL, "The scores in the low sixties are where it gets interesting, and that's really what today is about."),
        (LS, "On the Hub side the score comes back from Sentinel in real time and triage-svc applies the threshold, so it's a configuration question for us, not a code change."),
        (OL, "Kestwick license the engine, but the model monitoring is ours. That's an important distinction."),
    ])
    t_review = Topic("review", ["the April changes", "the customer notice process", "the SIU triage queue",
                                "the batch sweep defect", "the Compliance daily query", "the FR1 return",
                                "the referral letters", "the investigator workload"],
                     domain="fraud", leads=[RO, RD, NB], lines=[
        (RO, "Overall the April changes landed well. The notice letters are going out, and the auto-decline is gone, which was the big one for NISA."),
        (RD, "Triage within three days is tight but doable. We've had to reorganise the queue a bit to make it work."),
        (RO, "The FR1 process worked first time, which I wasn't sure it would."),
        (NB, "The customer letters have generated fewer calls than we feared. The contact centre script helped."),
        (RD, "The investigators would like the referral reason to be clearer on the case. They sometimes have to dig to see why a claim was referred."),
        (IA, "The handlers have adjusted. There was some grumbling in April, but it's settled."),
        (RO, "The daily query is a sticking plaster. It works, but nobody wants it forever."),
    ], qa=[
        (NB, "{nB}, how is the triage queue looking this week?", RD,
         "Under control. We're inside the three days most weeks, but there's not a lot of slack."),
    ])
    t_opts = Topic("options", ["option A", "option B", "the do-nothing option", "the SIU capacity",
                               "the impact on genuine customers", "the Tier-3 population", "the referral forecast",
                               "the investigator capacity"],
                   domain="fraud", leads=[OL, RD, NB, IA], lines=[
        (NB, "Let's be disciplined and go through the options in order, and then decide."),
        (RD, "My worry with any change is the queue. If it doubles overnight, triage in three days becomes fiction."),
        (OL, "The forecasts are based on the last two quarters, so they're as good as the data we've got."),
        (IA, "Tier-3 claims are where the money is. If we're going to be more sensitive anywhere, that's where."),
        (RO, "Whatever we choose, I need a clear rationale written down, because NISA will ask why we treat Tier-3 differently."),
        (HL, "I've got the three options captured. I'll put the rationale for each in the minutes."),
        (OL, "We also have to remember the model is less certain in the sixties. More referrals there means more false positives as well."),
        (RD, "For Tier-3, the investigators would rather see the claim early. It's a lot harder to unpick once it's been paid."),
        (AS, "From a product point of view, either option is configuration on the Hub. The CLARA side is the bigger question."),
    ])
    t_tier3 = Topic("tier3", ["the Tier-3 definition", "the triage rules", "the configuration change",
                              "the CLARA parameter change", "the test plan", "the go-live date", "the handler briefing",
                              "the effective-dated configuration", "the release plan"],
                    domain="fraud", leads=[LS, AS, RO, IA], lines=[
        (LS, "On the Hub, thresholds are effective-dated configuration under ADR-020, so we can load the new value ahead of time and it switches on the right day."),
        (AS, "We'll raise the stories straight after this, one for the Hub and one for CLARA."),
        (LS, "Testing is straightforward: we score some test claims either side of the line and check the referral is created."),
        (IA, "The handlers won't see any difference, but the team leaders should know, in case SIU start asking about Tier-3 claims they didn't expect."),
        (RO, "We'll need to update the referral reason so the FR1 data shows which threshold applied."),
        (AS, "CLARA still handles UK home, commercial and liability, and the Norway and Sweden claims, so the change has to go in both places at the same time."),
        (LS, "Triage-svc reads the threshold from configuration. We'll make sure the Tier-3 value is there before the first of the month."),
        (HL, "I'll update the BRD and the rule catalogue entry so the wording matches what we've agreed."),
    ])
    t_defer = Topic("deferral", ["the deferral process", "the tipping-off assessment", "the Compliance notification",
                                 "the approval route", "the deferral log", "the customer impact", "the audit trail"],
                    domain="fraud", leads=[RD, RO, NB], lines=[
        (RO, "My concern is visibility. A long deferral is exactly the sort of thing NISA will look at."),
        (RD, "The investigators understand the tipping-off risk; what they need is a quick answer when they ask for an extension."),
        (NB, "Longer deferrals should be rare. If they're not, that tells us something about how we're running investigations."),
        (IA, "From the customer side, a deferral means someone's waiting longer without being told why. We need to respect that."),
        (HL, "On CLARA the deferral approvals go through CLRFR120, so there is an audit trail of who approved what."),
        (RO, "I don't want a monthly report. I want to know on the day."),
    ])
    t_close = Topic("close", ["the action list", "the minutes", "the comms to SIU", "the next forum"],
                    domain="fraud", leads=[NB, HL], lines=[
        (NB, "Good session. Thank you all for the challenge."),
        (HL, "I'll have the minutes out tomorrow."),
    ])

    # ------------------------------------------------------------------ 00:00
    m.say(NB, "Morning, everyone. Let's make a start. Thanks for coming over, those of you who've travelled. This is the Fraud Rules Workshop we agreed at the last forum.")
    m.say(NB, "Two things today. First, whether we change the referral threshold for Tier-3 claims, and second, how we handle longer deferrals of the customer notice. Hannah's taking notes and will do the minutes.")
    m.say(HL, "Morning. Yes, I'm recording, and I'll read back the decisions at the end.")
    m.script(m.at(3, 0), t_open, [
        (NB, "Oskar, can you start us off with where the model is, and then Ruth can take us through the review of the last six months?"),
        (OL, "Sure. Let me share a couple of charts."),
    ])
    m.fill(m.at(12, 4), t_model)
    n = m.say(OL, "So, a bit of background for anyone who's newer. Sentinel, what we used to call FRAUDNET until the rename last year, scores every claim at notification and again when certain things change. The model is SNT-4.2, and I own it on the analytics side.")
    m.doc.fact(n, needle="Sentinel, what we used to call FRAUDNET", kind="alias_use", placement=pl("tx2_fraudnet"),
               statement="Oskar Lindgren refers to Sentinel as 'what we used to call FRAUDNET'.")
    m.doc.fact(n, needle="The model is SNT-4.2, and I own it", kind="general", world_ref="PERSON:P027#responsibilities",
               statement="Oskar Lindgren owns the Sentinel model SNT-4.2.")
    n = m.say(OL, "Since the first of April the referral threshold has been 65 for every claim, under BR-FRD-031. Before that it was 70 under the old rule, BR-FRD-012.")
    m.doc.fact(n, needle="the referral threshold has been 65 for every claim, under BR-FRD-031", kind="general",
               world_ref="RULE:BR-FRD-031@v1", statement="From 2026-04-01 BR-FRD-031 v1 set the referral threshold at 65 for all claims (previously 70 under BR-FRD-012).")
    m.script(m.at(17, 30), t_model, [
        (NB, "Thanks, Oskar. Ruth, the review."),
    ])
    n = m.say(RO, "Thanks, Niall. So, six months of the Circular. Referral volumes are up, as we expected: 1,488 referrals in the second quarter. The customer notice within 10 business days is working, and triage within 3 business days is being met most weeks.")
    m.doc.fact(n, needle="1,488 referrals in the second quarter", kind="general", world_ref="TIMELINE:metrics#fraud_referrals_count",
               statement="There were 1,488 fraud referrals in Q2 2026.")
    m.doc.fact(n, needle="triage within 3 business days", kind="general", world_ref="RULE:BR-FRD-035@v2",
               statement="BR-FRD-035 v2: SIU must triage a new referral within 3 business days.")
    n = m.say(RO, "The one real problem was the CLARA batch sweep. CLRFR040 still had the old threshold hard-coded, so 37 claims that scored 65 to 69 between April and the 12th of May weren't referred by the batch path. They were referred manually on the 13th, and Compliance now run a daily query for unreferred claims in that band.")
    m.doc.fact(n, needle="37 claims that scored 65 to 69", kind="needle", world_ref="INCIDENT:INC-2026-0518#impact",
               statement="INC-2026-0518: 37 claims scored 65-69 between 2026-04-01 and 2026-05-12 were not referred by the CLRFR040 batch sweep; they were referred manually on 2026-05-13.")
    m.doc.fact(n, needle="Compliance now run a daily query", kind="general", world_ref="INCIDENT:INC-2026-0518#workaround",
               statement="Workaround for INC-2026-0518: a daily Compliance query for unreferred claims scoring 65-69.")
    m.say(RO, "The fix is CHUB-298, and it's still open. So any change we make today has the same problem on the batch path until that's fixed.")
    n = m.say(RO, "And the first FR1 return, for Q2, went in on the 29th of July, a day ahead of the deadline on the 30th.")
    m.doc.fact(n, needle="went in on the 29th of July, a day ahead of the deadline on the 30th", kind="general",
               world_ref="REPORT:NISA-FR1#submissions.2026Q2.submitted",
               statement="The first NISA-FR1 return (2026Q2) was submitted on 2026-07-29, one day before the 2026-07-30 deadline.")
    m.script(m.at(34, 50), t_review, [
        (NB, "Thanks, Ruth. Let's go to the options. Oskar, you've modelled three."),
        (OL, "Yes. Option A is to lower the threshold to 60 for all claims. Option B is to lower it to 60 for Tier-3 claims only and keep 65 for everything else. Option C is to change nothing."),
    ])
    m.fill(m.at(55, 2), t_opts)
    n = m.say(OL, "So, option A. If we applied 60 to all claims, my estimate is that referrals would go up by about 41% on the current run-rate. That's the headline number.")
    m.doc.fact(n, needle="referrals would go up by about 41%", kind="needle", placement=pl("tx2_41pct"),
               statement="Oskar Lindgren estimates that lowering the referral threshold to 60 for all claims would raise referrals by about 41%; the option is rejected.",
               exclusive=True)
    m.say(RD, "We can't absorb that. Not with triage in three business days. We'd be breaching the rule within a fortnight.")
    m.say(IA, "And it would mean a lot of genuine customers getting a letter saying their claim is subject to additional checks, for no good reason.")
    n = m.say(NB, "Then I think option A is off the table. Let's record that we've considered lowering the general threshold to 60 for all claims and rejected it.")
    m.doc.fact(n, needle="considered lowering the general threshold to 60 for all claims and rejected it", kind="needle",
               world_ref="DECISION:DEC-016", statement="DEC-016: the option to lower the general referral threshold to 60 for all claims is rejected.")
    m.say(HL, "Got it. Option A rejected, with the rationale being SIU capacity and customer impact.")
    m.script(m.at(5, hh=1), t_opts, [
        (NB, "Option B, then. Tier-3 only. Ruth, can you remind us what we mean by Tier-3, so we're all using the same definition?"),
    ])
    n = m.say(RO, "Sure. Tier-3 is BR-TRI-003, version 3, since January 2025. A claim is Tier-3 if any of these apply: estimated incurred of £50,000 or more, or the Nordic equivalents, NOK 650,000, SEK 680,000 or DKK 430,000; any bodily injury; solicitor or litigation involvement at notification; or a property total loss.")
    m.doc.fact(n, needle="estimated incurred of £50,000 or more", kind="general", world_ref="RULE:BR-TRI-003@v3",
               statement="BR-TRI-003 v3 (from 2025-01-01): Tier-3 = estimated incurred >= £50,000 (NOK 650,000 / SEK 680,000 / DKK 430,000), any bodily injury, solicitor or litigation at notification, or property total loss.")
    m.say(OL, "And on that population, a threshold of 60 adds a manageable number of referrals, and those are the claims where the investigators say they'd rather see them early.")
    m.say(RD, "That I can work with.")
    m.script(m.at(18, hh=1), t_tier3, [
        (NB, "Linnea, Aisha, what does option B mean for the systems?"),
    ])
    n = m.say(LS, "On the Hub it's configuration. Thresholds are effective-dated config under ADR-020, so we load a Tier-3 value of 60 with an effective date of the first of October, alongside the general value of 65.")
    m.doc.fact(n, needle="effective-dated config under ADR-020", kind="general", world_ref="ADR:ADR-020",
               statement="Under ADR-020, fraud referral thresholds on Claims Hub are effective-dated configuration.")
    m.say(AS, "And on CLARA, Pauline's team would add a separate Tier-3 parameter in CLR.T_PARAM next to FRD_REFER_THRESH, valid from the same date. Online referral in CLRFR030 reads T_PARAM, so it would pick it up.")
    n = m.say(RO, "But the batch sweep won't, because of CHUB-298. So until that's fixed, the daily Compliance query has to cover 60 to 64 for Tier-3 claims as well as 65 to 69 for everything.")
    m.doc.fact(n, needle="cover 60 to 64 for Tier-3 claims as well as 65 to 69", kind="general",
               world_ref="INCIDENT:INC-2026-0518#workaround",
               statement="Until CHUB-298 is fixed the daily Compliance query covers 60-64 for Tier-3 claims as well as 65-69 for all claims (from 2026-10-01).")
    m.fill(m.at(35, hh=1), t_tier3)
    n = m.say(NB, "Okay. Then the decision is option B. From the first of October 2026, Tier-3 claims are referred at a Sentinel score of 60 or more, and the general threshold stays at 65. Ingrid, are you happy to co-approve?")
    m.doc.fact(n, needle="Tier-3 claims are referred at a Sentinel score of 60 or more, and the general threshold stays at 65",
               kind="contradiction_new", placement=pl("tx2_dec014"),
               statement="Decision DEC-014 (Fraud Rules Workshop, 2026-09-17): from 2026-10-01 Tier-3 claims are referred at a Sentinel score of 60 or more; the general threshold stays 65.",
               also_in=["corpus/upload/text/TX031_fraud_workshop_minutes_2026_09_18.md"],
               notes="Newer than the v7.2 manual (LD001 says 65 for all claims); see C01.")
    m.say(IA, "Yes, I'm happy. Approved from my side as Claims Director.")
    m.say(HL, "Noted. That becomes BR-FRD-031 version 2, effective the first of October.")
    m.script(m.at(38, hh=1), t_tier3, [
        (NB, "Right, second topic: deferrals of the customer notice. Rachel, can you set it up?"),
        (RD, "Sure. Under BR-FRD-036 we can defer the customer notice for up to 60 days where we've certified a tipping-off risk. Most deferrals are short. The question is what extra control we want on the long ones."),
    ])
    m.fill(m.at(48, hh=1), t_defer)
    n = m.say(NB, "Proposal, then. From the first of October, deferrals beyond 30 days need the Head of Counter-Fraud & SIU, which is me, and Compliance is notified the same day. Ruth, does that work?")
    m.doc.fact(n, needle="deferrals beyond 30 days need the Head of Counter-Fraud & SIU", kind="needle", placement=pl("tx2_dec015"),
               statement="Decision DEC-015: from 2026-10-01 customer-notice deferrals beyond 30 days need the Head of Counter-Fraud & SIU, and Compliance is notified the same day.")
    m.say(RO, "That works. Same day is the important bit.")
    m.say(IA, "Agreed. Approved.")
    m.say(HL, "So that's BR-FRD-036 version 2 from the first of October: the 60-day maximum stays, and anything over 30 days goes to Niall, with Compliance notified the same day.")
    m.script(m.at(52, hh=1), t_defer, [
        (NB, "Hannah, can you read back the decisions and actions?"),
    ])
    m.say(HL, "Decisions. One: option A, 60 for all claims, considered and rejected. Two: from the first of October, Tier-3 claims referred at a Sentinel score of 60 or more; general threshold stays 65; approved by Niall and Ingrid. Three: from the first of October, notice deferrals beyond 30 days need the Head of Counter-Fraud & SIU, and Compliance is notified the same day.")
    m.say(HL, "Actions. Linnea: Hub configuration for the Tier-3 threshold, effective the first of October. Aisha: raise the CLARA parameter story with Pauline's team. Ruth: extend the daily query to Tier-3 claims scoring 60 to 64. Oskar: weekly referral volumes for the first month. Niall: brief the SIU teams. Me: update the BRD and the rule catalogue. And Ruth, the Q3 FR1 return is due thirty days after quarter end, so by the 30th of October.")
    m.say(RO, "Yes, that's in hand.")
    m.say(NB, "Anything I've missed? Hannah, anything else for the minutes?")
    m.fill(m.at(58, 10, hh=1), t_close)
    m.say(NB, "Thanks, everyone. Good session.")
    m.say(OL, "Thanks, Niall.")
    m.say(RD, "Thanks, all.")
    m.note("Recording stopped.")
    footer(m, DATE, HL)
    return m

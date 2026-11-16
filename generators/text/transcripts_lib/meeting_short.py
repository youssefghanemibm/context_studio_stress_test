"""TX004-TX006: shorter calls (incident bridge, subrogation handover, Sentinel rename cut-over)."""
from __future__ import annotations

from generators.common import util

from .common import D, out_path, placement, assert_may
from .dialogue import Meeting, Topic
from .meetings_common import speakers_for, transcript_header, footer


# =============================================================================================
# TX004  Incident bridge INC-2025-0412, 28 Apr 2025 08:15, 75 minutes (MTG-003)
# =============================================================================================
TX004_PATH = out_path("TX004", "incident_bridge_inc_2025_0412_transcript", "txt")


def build_tx004(facts, wps: float) -> Meeting:
    FID, MTG, DATE = "TX004", "MTG-003", D("2025-04-28")
    HV, HG, KB, BA, MO, GP, MH, PO = "P031", "P021", "P023", "P020", "P050", "P016", "P036", "P038"
    for ref, f in [("INTERFACE:CLX-IF-042", "dependents"), ("DECISION:DEC-003", None), ("TICKET:CHUB-138", None),
                   ("TICKET:CHUB-142", None), ("INCIDENT:INC-2025-0412", "root_cause"), ("INCIDENT:INC-2025-0412", "start"),
                   ("INTERFACE:CLX-IF-043", "schedule_history"), ("INTERFACE:CLX-IF-051", None), ("PROGRAM:CLRRS170", None),
                   ("COPYBOOK:RSVMOVE", None), ("PERSON:P002", "role_aliases"), ("INTERFACE:CLX-IF-042", "mq_queue"),
                   ("INTERFACE:CLX-IF-043", "owner"), ("INTERFACE:CLX-IF-044", "owner"), ("INTERFACE:CLX-IF-047", "owner"),
                   ("INTERFACE:CLX-IF-042", "owner")]:
        assert_may(FID, ref, f)
    sp = speakers_for(MTG, DATE, overrides={HV: {"weight": 1.4}, KB: {"weight": 1.2}, HG: {"weight": 1.1}})
    r = util.rng(f"{FID}:dialogue:{wps}")
    m = Meeting(FID, TX004_PATH, facts, sp, r, wps=wps, chair=HV, domain="incident", duration_min=75,
                meta_budget=6, digress_budget=1, crosstalk_budget=4)
    m.spacing["meta"] = 300.0
    m.header(transcript_header(
        doc_ref="INC-2025-0412-BRIDGE-01", title_="Transcript - Incident Bridge INC-2025-0412", meeting_id=MTG,
        venue="Incident bridge (audio and video), participants in Copenhagen, Leeds, London and Oslo", chair=HV,
        author=HV, approver=HV, speakers=sp, d=DATE, forum_line="Major incident bridge (Sev 1)",
        versions=[("0.1", "2025-04-28", "H. Vestergaard", "Bridge recording transcribed"),
                  ("1.0", "2025-04-28", "H. Vestergaard", "Checked and attached to the incident record")],
        extra_notes=["Attached to incident record INC-2025-0412. Times quoted by speakers are UK time."]))
    pl = lambda k: placement(FID, k)

    t_open = Topic("open", ["the incident record", "the bridge cadence", "the comms plan", "the timeline"],
                   domain="incident", leads=[HV], lines=[
        (HV, "Can everyone keep their cameras off and mics muted unless they're speaking? We've got a lot of people on."),
        (GP, "I've got the CLARA on-call on a separate line if we need them."),
    ])
    t_diag = Topic("diag", ["the reject log", "the GL adapter", "the copybook change", "the extract file",
                            "the record layout", "the consumer parsers", "the change record", "the weekend batch",
                            "the downstream checks"],
                   domain="incident", leads=[HV, KB, HG, GP], lines=[
        (HV, "Every record in this morning's file was rejected by the adapter. It's not a partial failure, it's all of them."),
        (KB, "The layout change was tested on the CLARA side. The extract ran, the file was produced. What nobody did was check the consumers."),
        (HG, "From Finance's point of view, I've got no reserve journals in the ledger since Friday. That's the problem in a sentence."),
        (GP, "The change went through as a CLARA-only change. With hindsight, that classification was wrong."),
        (MO, "The adapters parse the record by position. If a field gets wider, everything after it shifts and the parse fails."),
        (MH, "I'm checking the CDW side now. I'll confirm before the next update whether our load picked up anything odd."),
        (PO, "Same for ReCede. I've asked my team to look at the cession input before anyone reruns anything."),
        (HV, "Let's not rerun anything yet. I want to understand it fully first."),
        (KB, "The copybook is shared, so anyone who compiled against the new one will see the new layout."),
        (GP, "We have the change record. I'll attach it to the incident so everyone can see what was approved."),
    ], qa=[
        (HV, "{nB}, can you confirm the time of the first reject?", HG,
         "The adapter log shows the first reject at 03:02 this morning, and it carried on rejecting until the file ended."),
    ])
    t_opts = Topic("opts", ["the revert option", "the fix-forward option", "the record version", "the GL schedule",
                            "the rerun plan", "the regression test", "the deployment window", "the reconciliation"],
                   domain="incident", leads=[MO, KB, HV, HG, BA], lines=[
        (MO, "Fixing forward means changing three adapters under pressure. Reverting means changing one copybook and one program. I know which I'd rather do today."),
        (KB, "The revert is simple. The Nordic large-loss requirement doesn't go away, but it can wait for a properly managed change."),
        (HG, "Whatever we do, I need the journals for Friday through to today posted before month-end close starts."),
        (BA, "And I need the general ledger right before the TP2 extract. That's the hard deadline."),
        (HV, "A record version in the header would have told every consumer the layout had changed. Let's add one while we're in there."),
        (MO, "If the consumers check the version, a future change fails loudly instead of quietly."),
        (HV, "The GL feed currently runs straight after the extract. That doesn't leave any time for validation."),
        (HG, "I'm fine with the GL feed running later, as long as it's done before the ledger opens."),
        (KB, "I can have the revert ready for test this morning."),
    ])
    t_act = Topic("act", ["the action list", "the next bridge", "the post-incident review", "the impact checklist",
                          "the stakeholder update"], domain="incident", leads=[HV, MO, HG], lines=[
        (HV, "Next bridge at twelve. If anything changes before then, I'll call it earlier."),
        (MO, "The checklist will be short. It just has to make sure every consumer signs off before a layout change goes in."),
    ])

    m.say(HV, "Okay, it's quarter past, let's start. This is the Sev 1 bridge for INC-2025-0412. GL reserve journals are being rejected after a change to the CLX-IF-042 extract. I'm running the bridge.")
    n = m.say(HV, "Quick summary. The overnight extract ran as normal, but from 03:02 the GL adapter rejected every record in the file. Nothing has been posted to the general ledger from it.")
    m.doc.fact(n, needle="from 03:02 the GL adapter rejected every record", kind="general", world_ref="INCIDENT:INC-2025-0412#start",
               statement="INC-2025-0412 started at 03:02 on 2025-04-28 when the GL adapter (CLX-IF-043) began rejecting every CLX-IF-042 record.")
    m.script(m.at(2, 20), t_open, [
        (HV, "Let me do a roll call so I know who's here. Hamish, Keith, Bjorn, Marcus, Graham, Maja, Per. Good, everyone's on."),
    ])
    m.fill(m.at(9, 2), t_open)
    n = m.say(HV, "Let me be clear about blast radius first. Three consumers hang off CLX-IF-042 today: the GL journal feed, which is 043, the CDW load, which is 044, and the ReCede cession feed, 047. All three read the same RSVMOVE records from CLR.RSVMOVE.OUT.")
    m.doc.fact(n, needle="the GL journal feed, which is 043, the CDW load, which is 044, and the ReCede cession feed, 047", kind="needle",
               placement=pl("tx4_down"),
               statement="On the INC-2025-0412 bridge Henrik Vestergaard lists the consumers of CLX-IF-042: GL journal feed (CLX-IF-043), CDW load (CLX-IF-044) and ReCede cession feed (CLX-IF-047).")
    m.say(HV, "Hamish owns the GL feed, Maja the CDW load, and Per the cession feed, which is why you're all on the call.")
    m.script(m.at(12, 30), t_diag, [
        (HV, "Keith, what changed?"),
    ])
    n = m.say(KB, "On Friday, the 25th, we deployed CHUB-138. It widened RM-AMOUNT in the RSVMOVE copybook from S9(9)V99 to S9(11)V99 COMP-3, for Nordic large losses. CLRRS170 picked up the new layout and the extract has been writing the wider records since.")
    m.doc.fact(n, needle="widened RM-AMOUNT in the RSVMOVE copybook from S9(9)V99 to S9(11)V99 COMP-3", kind="needle",
               world_ref="INCIDENT:INC-2025-0412#root_cause",
               statement="Root cause of INC-2025-0412: CHUB-138 widened RSVMOVE RM-AMOUNT from S9(9)V99 to S9(11)V99 COMP-3 (deployed 2025-04-25).")
    n = m.say(GP, "And to be honest about it, it went in without a consumer impact assessment. Nobody asked the downstream teams.")
    m.doc.fact(n, needle="without a consumer impact assessment", kind="general", world_ref="TICKET:CHUB-138",
               statement="CHUB-138 was deployed on 2025-04-25 without a consumer impact assessment.")
    m.script(m.at(27, 10), t_diag, [
        (HV, "Bjorn, what's the regulatory exposure?"),
    ])
    n = m.say(BA, "The Q1 TP2 return is due on the 5th of May. The technical provisions feed, CLX-IF-051, takes its numbers from the general ledger, so if the reserve journals aren't in the ledger in time, the return is at risk.")
    m.doc.fact(n, needle="The Q1 TP2 return is due on the 5th of May", kind="general", world_ref="INTERFACE:CLX-IF-051",
               statement="The Q1 2025 NISA-TP2 return was due on 2025-05-05; it depends on the general ledger via CLX-IF-051, downstream of CLX-IF-043.")
    m.say(HV, "Understood. So the GL feed is the priority, then the other two.")
    m.fill(m.at(5, hh=1), t_opts)
    n = m.say(HV, "Okay. Decision, then, and Hamish, I want you on this with me. We revert RM-AMOUNT to S9(9)V99, we add a record-version byte to the RSVMOVE header, and we move CLX-IF-043 from 03:00 to 03:45 so there's time to validate the file before the GL feed picks it up.")
    m.doc.fact(n, needle="move CLX-IF-043 from 03:00 to 03:45", kind="needle", placement=pl("tx4_dec003"),
               statement="Decision DEC-003: revert the RSVMOVE RM-AMOUNT widening, add a record-version byte, and move CLX-IF-043 from 03:00 to 03:45.")
    m.say(HG, "Agreed from Finance.")
    m.say(KB, "I'll raise the bug now for the revert and the record version, and link it to CHUB-138.")
    m.say(MO, "And I'll draft an interface change impact checklist, so every downstream consumer has to sign off before a layout change goes in.")
    n = m.say(HG, "I'll brief the CFO this morning. Gareth will want to know about the journals before month-end, and Bjorn, you'll want to give the supervisor a heads-up on TP2.")
    m.doc.fact(n, needle="I'll brief the CFO this morning. Gareth", kind="alias_use", world_ref="PERSON:P002#role_aliases",
               statement="In April 2025 'the CFO' refers to Gareth Whitcombe (CFO until 2025-06-30).")
    m.say(BA, "Yes, I'll call them today, just so there are no surprises.")
    m.script(m.at(11, hh=1), t_act, [
        (HV, "Actions, quickly. Keith: the revert and record version. Me: a change for the 043 schedule. Marcus: the checklist. Hamish: the CFO. Bjorn: the supervisor. Maja and Per: confirm your loads before any rerun. Next bridge at twelve."),
        (GP, "Thanks, Henrik."),
        (HG, "Thanks, all."),
    ])
    m.note("Bridge closed.")
    footer(m, DATE, HV)
    return m


# =============================================================================================
# TX005  Subrogation ownership handover, 3 Sep 2025 13:00, 60 minutes (MTG-004)
# =============================================================================================
TX005_PATH = out_path("TX005", "subrogation_handover_2025_09_03_transcript", "txt")


def build_tx005(facts, wps: float) -> Meeting:
    FID, MTG, DATE = "TX005", "MTG-004", D("2025-09-03")
    FL, SQ, IA, RT, EP = "P013", "P014", "P005", "P011", "P060"
    for ref, f in [("DECISION:DEC-004", None), ("SYSTEM:SYS24", "decommission_target"), ("RULE:BR-REC-003@v2", "text"),
                   ("RULE:BR-REC-003@v3", "text"), ("RULE:BR-REC-011@v1", "text"), ("RULE:BR-REC-011@v2", "text"),
                   ("PERSON:P015", "employment"), ("PROCESS:S7", "owner_history"), ("TEAM:T08", "name_history"),
                   ("PROGRAM:CLRRC060", None), ("PROGRAM:CLRRC040", None), ("VENDOR:VEN-07", None),
                   ("INCIDENT:INC-2025-0815", None), ("PERSON:P013", "responsibilities")]:
        assert_may(FID, ref, f)
    sp = speakers_for(MTG, DATE, overrides={EP: {"label": "Ed Pargeter (Quarryhill)", "first": "Ed", "weight": 0.8},
                                            FL: {"weight": 1.3}, SQ: {"weight": 1.2}})
    r = util.rng(f"{FID}:dialogue:{wps}")
    m = Meeting(FID, TX005_PATH, facts, sp, r, wps=wps, chair=IA, domain="recoveries", duration_min=60,
                meta_budget=4, digress_budget=1, crosstalk_budget=3)
    m.spacing["meta"] = 360.0
    m.header(transcript_header(
        doc_ref="RCS-HND-TRN-2025-09", title_="Transcript - Subrogation Ownership Handover", meeting_id=MTG,
        venue="Bristol Recoveries Centre and video bridge (Stockholm, London)", chair=IA, author=FL, approver=IA,
        speakers=sp, d=DATE, forum_line="Process ownership handover (recovery & subrogation)",
        versions=[("0.1", "2025-09-03", "F. Lindahl", "Transcript produced from the recording"),
                  ("1.0", "2025-09-03", "I. Ashby", "Approved as the record of the handover")],
        extra_notes=["Edward Pargeter (Quarryhill Solicitors LLP) attended for the litigation items only."]))
    pl = lambda k: placement(FID, k)

    t_hand = Topic("handover", ["the open recovery cases", "the handover pack", "the sub-ro pipeline", "the demand letters",
                                "the limitation diary", "the write-off approvals", "the recovery targets",
                                "the third-party insurer correspondence", "the Bristol team"],
                   domain="recoveries", leads=[FL, SQ, IA], qa=[
        (SQ, "Before we go on: the team in Bristol have kept things going through a difficult eight months. I want that recognised.",
         IA, "It is recognised, and I'll say so to the team directly."),
    ], lines=[
        (SQ, "The handover pack has every open case over a certain age, with the next action and the limitation date."),
        (FL, "I've read the pack twice. It's very thorough, Siobhan, thank you."),
        (FL, "My first priority is consistency between the UK and the Nordic teams. Same principles, local paperwork."),
        (SQ, "The demand letters go out through CLARA and Notify, and the replies come back to the mailroom. It's not elegant, but it works."),
        (FL, "In the Nordics we call it regress, but it's the same process. Recover what a third party owes us."),
        (SQ, "The limitation diary is the thing I'd never want anyone to neglect. Miss a date and the recovery's gone."),
        (IA, "From my side, I want sub-ro treated as part of the claim, not as an afterthought once the claim is closed."),
    ])
    t_lit = Topic("litigation", ["the litigation pipeline", "the solicitor instructions", "the panel arrangements",
                                 "the court timetable", "the settlement offers", "the file quality", "the costs position"],
                  domain="recoveries", leads=[EP, SQ, FL], lines=[
        (EP, "From Quarryhill's side, the files we get from Bristol are generally good. Where they're not, it's usually missing evidence from the original claim."),
        (SQ, "Instructions to Quarryhill go through CLRRC060, so the litigation record sits on the claim in CLARA."),
        (EP, "We'll send a pipeline summary to Freya by the end of the week, so she's got a single view."),
        (FL, "I'd like a regular call with you, Ed, maybe monthly, just to keep the pipeline visible."),
        (EP, "Happy to. We do the same with a couple of other clients and it works well."),
    ])
    t_sys = Topic("systems", ["SUBTRAK", "the CLARA synchronisation", "the recovery reporting", "the move to the Hub",
                              "the recovery tracker", "the data clean-up", "the case migration"],
                  domain="recoveries", leads=[FL, SQ, RT], lines=[
        (SQ, "SUBTRAK has done its job, but it's old, and it only talks to CLARA through the evening sync."),
        (FL, "CLRRC040 does the synchronisation with SUBTRAK every evening, so the two are never more than a day apart."),
        (RT, "From Claims Operations, the handlers don't touch SUBTRAK. They just flag sub-ro potential on the claim."),
        (FL, "I'd like to get off SUBTRAK in a planned way, not because it falls over."),
        (SQ, "The data in SUBTRAK needs cleaning before it can go anywhere. There are cases in there that should have been closed years ago."),
    ])
    t_ops = Topic("ops", ["the settlement hand-off", "the sub-ro flag", "the handler training", "the Nordic regress cases",
                          "the salvage hand-off", "the referral from claims"],
                  domain="recoveries", leads=[RT, FL, IA], lines=[
        (RT, "The best time to spot sub-ro is at settlement, when the handler knows exactly what we've paid and why."),
        (FL, "If the handlers flag it at settlement, the recovery team can pick it up while the evidence is fresh."),
        (RT, "We'll add a reminder to the settlement checklist for the handlers. It costs nothing."),
        (IA, "And salvage and sub-ro need to talk. Sometimes we recover twice from the same incident and nobody joins the dots."),
    ])

    n = m.say(IA, "Afternoon, everyone. Can everyone hear me? Let's give it a minute for anyone still joining the bridge.")
    m.say(RT, "Rob here. You're coming through fine, Ingrid.")
    m.say(FL, "Yes, loud and clear.")
    m.say(IA, f"Good. A quick round of introductions, since not everyone has met. I'm Ingrid, {sp[IA]['role']}.")
    m.say(FL, f"{sp[FL]['label']}, {sp[FL]['role']}, from the new Group function.")
    m.say(SQ, f"{sp[SQ]['label']}, {sp[SQ]['role']}.")
    m.say(RT, f"{sp[RT]['label']}, {sp[RT]['role']}.")
    m.say(EP, "Ed Pargeter from Quarryhill. I'm mainly here for the litigation items.")
    m.say(IA, "Thanks. The plan for the hour: the formal handover first, then Siobhan's walk-through, then litigation with Ed, then systems and claims operations. Siobhan, while we wait for the slides to come up, anything you want to flag before we start?")
    m.fill(m.at(4, 50), t_hand)
    m.say(IA, "Right, let me start with the formal bit, so it's on the record.")
    n = m.say(IA, "As of the re-organisation on Monday, Freya owns the subrogation process from 1 September 2025, as Head of Recoveries & Subrogation, and Siobhan leads the UK recoveries team.")
    m.doc.fact(n, needle="Freya owns the subrogation process from 1 September 2025", kind="needle", placement=pl("tx5_owner"),
               statement="Handover: Freya Lindahl owns the subrogation process from 2025-09-01; Siobhan Quill leads the UK recoveries team.")
    m.doc.fact(n, needle="Siobhan leads the UK recoveries team", kind="needle", world_ref="DECISION:DEC-004",
               statement="From 2025-09-01 Siobhan Quill leads the UK recoveries team (Recoveries Team Leader - UK).")
    n = m.say(IA, "Siobhan has been acting owner since January, after Martin Calloway left at the end of December, and I want to thank her for that. Freya reports to me, and the team is now Recoveries & Subrogation, a Group function.")
    m.doc.fact(n, needle="acting owner since January, after Martin Calloway left at the end of December", kind="general",
               world_ref="PROCESS:S7#owner_history",
               statement="Siobhan Quill was acting owner of recovery & subrogation from 2025-01-01 after Martin Calloway left on 2024-12-31.")
    m.say(SQ, "Thank you. It's been a busy eight months, but the team have been brilliant.")
    m.say(FL, "Thanks, Ingrid, and thank you, Siobhan. I'm looking forward to it.")
    m.script(m.at(8, 0), t_hand, [
        (IA, "Siobhan, can you take us through the main things Freya needs to know?"),
    ])
    n = m.say(SQ, "Sure. The big change on Monday was the pursuit threshold. Under the new version of BR-REC-003 we pursue sub-ro where the recoverable amount is £1,000 or more, from 1 September. Until the end of August it was £750.")
    m.doc.fact(n, needle="£1,000 or more, from 1 September", kind="temporal", world_ref="RULE:BR-REC-003@v3",
               statement="BR-REC-003 v3: subrogation is pursued where the recoverable amount is £1,000 or more from 2025-09-01 (it was £750 until 2025-08-31).")
    m.doc.fact(n, needle="pursue sub-ro", kind="terminology", world_ref="GLOSSARY:G-004",
               statement="Transcripts use 'sub-ro' for Subrogation.")
    n = m.say(SQ, "And write-offs: anything above £10,000 now needs the Head of Recoveries & Subrogation, so that's Freya. It used to be above £5,000 with the Recoveries Manager.")
    m.doc.fact(n, needle="anything above £10,000 now needs the Head of Recoveries & Subrogation", kind="general",
               world_ref="RULE:BR-REC-011@v2",
               statement="BR-REC-011 v2 (from 2025-09-01): recovery write-offs above £10,000 need the Head of Recoveries & Subrogation (v1: above £5,000, Recoveries Manager).")
    m.script(m.at(18, 30), t_hand, [
        (IA, "Ed, do you want to give us the litigation picture?"),
    ])
    m.fill(m.at(30, 0), t_lit)
    m.script(m.at(31, 0), t_sys, [
        (IA, "Let's talk about systems. Freya?"),
    ])
    m.fill(m.at(40, 5), t_sys)
    n = m.say(FL, "So, SUBTRAK. I'd like us to set a retirement target for SUBTRAK of 31 December 2026, and plan the case migration and clean-up backwards from that.")
    m.doc.fact(n, needle="retirement target for SUBTRAK of 31 December 2026", kind="needle", placement=pl("tx5_subtrak"),
               statement="SUBTRAK retirement target set to 2026-12-31 at the 2025-09-03 handover.")
    m.say(IA, "Agreed. Let's make that the target. 31 December 2026 for SUBTRAK.")
    m.say(SQ, "That gives us time to clean the data properly. I'm pleased.")
    m.script(m.at(44, 0), t_sys, [
        (IA, "Rob, from Claims Operations?"),
    ])
    m.say(RT, "Thanks. Two things. The sub-ro flag at settlement, which we've talked about. And just to mention that Monday's re-org wasn't entirely smooth elsewhere; the SIU queue permissions dropped after SIU moved to Risk, and that was fixed the same day. Nothing to do with recoveries, but it's a reminder to check access.")
    m.fill(m.at(55, 30), t_ops)
    m.say(IA, "Let me recap. Freya owns the process from 1 September. Siobhan leads the UK recoveries team. The SUBTRAK retirement target is 31 December 2026. Ed will send Freya the litigation pipeline. Rob will add the sub-ro prompt to the settlement checklist.")
    m.say(FL, "Thanks, everyone.")
    m.say(EP, "Thanks, all. Speak soon, Freya.")
    m.say(IA, "Thanks, everyone.")
    m.note("Recording stopped.")
    footer(m, DATE, FL)
    return m


# =============================================================================================
# TX006  Sentinel rename cut-over call (INC-2025-0233), 3 Mar 2025 09:30, 50 minutes (MTG-002)
# =============================================================================================
TX006_PATH = out_path("TX006", "sentinel_rename_cutover_call_transcript", "txt")


def build_tx006(facts, wps: float) -> Meeting:
    FID, MTG, DATE = "TX006", "MTG-002", D("2025-03-03")
    GP, PA, OL, HV, NB = "P016", "P024", "P027", "P031", "P008"
    for ref, f in [("INCIDENT:INC-2025-0233", "impact"), ("INCIDENT:INC-2025-0233", "root_cause"), ("DECISION:DEC-002", None),
                   ("TICKET:CHUB-119", None), ("TICKET:CHUB-117", None), ("INTERFACE:CLX-IF-008", None),
                   ("VENDOR:VEN-15", None), ("SYSTEM:SYS03", "renames"), ("PROGRAM:CLRFR020", None),
                   ("INTERFACE:CLX-IF-009", "schedule")]:
        assert_may(FID, ref, f)
    sp = speakers_for(MTG, DATE, overrides={GP: {"weight": 1.3}, PA: {"weight": 1.2}, HV: {"weight": 1.2}})
    r = util.rng(f"{FID}:dialogue:{wps}")
    m = Meeting(FID, TX006_PATH, facts, sp, r, wps=wps, chair=GP, domain="rename", duration_min=50,
                meta_budget=4, digress_budget=0, crosstalk_budget=3)
    m.spacing["meta"] = 300.0
    m.header(transcript_header(
        doc_ref="INC-2025-0233-CALL-01", title_="Transcript - Sentinel Rename Cut-over Call", meeting_id=MTG,
        venue="Conference bridge (Leeds, Stockholm, Copenhagen)", chair=GP, author=GP, approver=GP,
        speakers=sp, d=DATE, forum_line="Cut-over call, raised to incident INC-2025-0233 (Sev 2)",
        versions=[("0.1", "2025-03-03", "G. Pocock", "Call recording transcribed"),
                  ("1.0", "2025-03-03", "G. Pocock", "Checked and attached to INC-2025-0233")],
        extra_notes=["The FRAUDNET to Sentinel rename took effect on Saturday 1 March 2025 (CHUB-117)."]))
    pl = lambda k: placement(FID, k)

    t_diag = Topic("diag", ["the scoring failures", "the certificate", "the endpoint configuration", "the DNS records",
                            "the gateway logs", "the online scoring path", "the rename checklist", "the failed requests"],
                   domain="rename", leads=[HV, PA, GP], lines=[
        (HV, "The gateway logs show every request from CLARA failing the TLS handshake. It's not timing out, it's being refused."),
        (PA, "CLRFR020 builds the request with the old host name. It's in the program, not in a config table, which is why nobody caught it."),
        (GP, "The rename checklist covered the interfaces we knew about. This one slipped through."),
        (OL, "On the Sentinel side, everything's healthy. It's scoring anything that reaches it."),
        (HV, "The new certificate only has the new name on it. So anything still using the old name fails, even though the DNS still resolves."),
        (PA, "I can change the host name in CLRFR020 and have it in test within the hour."),
        (NB, "From SIU, I'm less worried about the technology and more about which claims we've missed."),
    ])
    t_fix = Topic("fix", ["the patch", "the emergency change", "the back-scoring", "the DNS alias", "the test plan",
                          "the SIU follow-up", "the other consumers", "the vendor support"],
                  domain="rename", leads=[PA, HV, NB, GP, OL], lines=[
        (PA, "The patch is a one-line change and a recompile. The testing is the longer part."),
        (HV, "If we keep the old DNS name for a few weeks, anything else we've missed keeps resolving while we find it."),
        (OL, "The nightly refresh will score anything that was missed, so nothing stays unscored for long once we're fixed."),
        (NB, "I'd like a list of the unscored claims, so the team can look at the higher-risk ones by hand if needed."),
        (GP, "I'll take it through emergency CAB. It's a small change, but it's production."),
        (OL, "Kestwick don't need to do anything, but I'll let their support desk know, in case they see odd traffic."),
        (HV, "I'll run a search across the integration configs for the old name, in case there's anything else."),
    ])

    m.say(GP, "Morning, all. Thanks for joining at short notice. We've been seeing Sentinel scoring failures from CLARA since ten past eight, so I've raised it as a Sev 2, INC-2025-0233. Let's work out what's going on.")
    m.say(GP, "Henrik, can you start with what you're seeing?")
    m.fill(m.at(4, 10), t_diag)
    n = m.say(HV, "Sure. When we renamed FRAUDNET to Sentinel on Saturday, the TLS certificate was reissued only for sentinel.corvane.internal. But CLRFR020 is still calling fraudnet.corvane.internal, so every online scoring request from CLARA fails the handshake.")
    m.doc.fact(n, needle="the TLS certificate was reissued only for sentinel.corvane.internal", kind="needle",
               world_ref="INCIDENT:INC-2025-0233#root_cause",
               statement="Root cause of INC-2025-0233: CLRFR020 still called fraudnet.corvane.internal, but the TLS certificate had been reissued only for sentinel.corvane.internal on 2025-03-01.")
    n = m.say(PA, "That's the online path, CLX-IF-008. CLRFR020 calls the mainframe API gateway with the SENTREQ1 request and reads SENTRSP1 back. The host name is in the program.")
    m.doc.fact(n, needle="CLRFR020 calls the mainframe API gateway with the SENTREQ1 request", kind="general",
               world_ref="INTERFACE:CLX-IF-008", statement="CLX-IF-008 online Sentinel scoring: CLRFR020 calls the mainframe API gateway (SENTREQ1/SENTRSP1 mapping).")
    m.fill(m.at(20, 3), t_diag)
    n = m.say(OL, "I've got a count off the fraud score table. 1,214 claims left unscored since the first failure at ten past eight. None of those have been through Sentinel.")
    m.doc.fact(n, needle="1,214 claims left unscored", kind="needle", placement=pl("tx6_1214"),
               statement="1,214 claims were left unscored during the Sentinel rename incident (INC-2025-0233).",
               notes="The count is stated during the call; the incident record gives the same figure as the final impact.")
    m.say(NB, "And unscored means not referred, so SIU won't see any of them until they're scored.")
    m.say(OL, "Right. The nightly batch scoring run at quarter past midnight will back-score anything still unscored, but they'll all be late.")
    m.fill(m.at(45, 0), t_fix)
    n = m.say(GP, "Okay, decision. We keep the fraudnet.corvane.internal DNS alias until 31 March, so anything else still using the old name keeps resolving, and Pauline patches CLRFR020 today to call sentinel.corvane.internal.")
    m.doc.fact(n, needle="keep the fraudnet.corvane.internal DNS alias until 31 March", kind="needle", world_ref="DECISION:DEC-002",
               statement="DEC-002: keep the fraudnet.corvane.internal DNS alias until 2025-03-31 and patch CLRFR020 the same day.")
    m.say(PA, "Yes. I'll raise the bug now and link it to the rename task.")
    n = m.say(GP, "Thanks. For the record, the rename task was CHUB-117, closed on Saturday. The new bug is CHUB-119.")
    m.doc.fact(n, needle="The new bug is CHUB-119", kind="general", world_ref="TICKET:CHUB-119",
               statement="CHUB-119 (CLRFR020 still calls the retired fraudnet endpoint) is raised on 2025-03-03 and relates to the rename task CHUB-117.")
    m.script(m.at(49, 0), t_fix, [
        (GP, "Actions. Pauline: patch, test, emergency CAB. Henrik: search the configs for the old name. Oskar: the list of unscored claims for Niall. Niall: SIU review of the higher-risk ones. I'll update the incident record."),
        (NB, "Thanks, Graham."),
        (HV, "Cheers."),
    ])
    m.note("Call ended.")
    footer(m, DATE, GP)
    return m

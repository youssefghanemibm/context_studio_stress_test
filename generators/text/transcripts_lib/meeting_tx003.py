"""TX003: Reserving design review (reserve-engine), 5 Mar 2026 (MTG-005), about two hours.

Plants PL-197 (~00:38 Daniel Achebe: only the CLRRS programs write CLR.T_RESERVE - wrong), PL-198
(~00:46 Keith Barraclough corrects: CLRFN030, CLRST040, CLRRC050 and CLRGL090 also write it; C07) and
PL-199 (~01:40 DEC-005, revaluations as RV movements).
"""
from __future__ import annotations

from generators.common import util

from .common import D, W, out_path, placement, assert_may
from .dialogue import Meeting, Topic
from .meetings_common import speakers_for, transcript_header, footer

FID = "TX003"
MTG = "MTG-005"
DATE = D("2026-03-05")
PATH = out_path(FID, "reserving_design_review_2026_03_05_transcript", "txt")

LK, DA, KB, NP, GS, CF, SM, TW = "P009", "P041", "P023", "P053", "P052", "P051", "P010", "P018"


def _checks():
    for ref, f in [("TABLE:CLR.T_RESERVE", "writers"), ("DECISION:DEC-005", None), ("DECISION:DEC-006", None),
                   ("PROGRAM:CLRRS150", "writes_tables"), ("TICKET:CHUB-284", None), ("INCIDENT:INC-2026-0104", None),
                   ("TICKET:CHUB-241", None), ("SERVICE:reserve-engine", "renames"), ("INTERFACE:CLX-IF-049", None),
                   ("ADR:ADR-011", None), ("ADR:ADR-016", None), ("ADR:ADR-019", None), ("RULE:BR-RSV-007@v2", "text"),
                   ("RULE:BR-RSV-007@v3", "text"), ("TICKET:CHUB-104", None), ("PROGRAM:CLRGL090", None),
                   ("PROGRAM:CLRRS210", None), ("WAVE:MW-0", "date"), ("TOPIC:claims.reserve.movement.v1", "name")]:
        assert_may(FID, ref, f)


def build(facts, wps: float) -> Meeting:
    _checks()
    sp = speakers_for(MTG, DATE, overrides={TW: {"label": "Tomasz Wojcik", "weight": 1.1},
                                            CF: {"label": "Callum Fairbairn (IBM)", "weight": 0.8},
                                            SM: {"weight": 0.8}, KB: {"weight": 1.2}, DA: {"weight": 1.2}})
    r = util.rng(f"{FID}:dialogue:{wps}")
    m = Meeting(FID, PATH, facts, sp, r, wps=wps, chair=TW, domain="reserving", duration_min=120,
                meta_budget=8, digress_budget=3, crosstalk_budget=5)
    m.header(transcript_header(
        doc_ref="DA-RSV-TRN-2026-03", title_="Transcript - Reserving Design Review 5 Mar 2026", meeting_id=MTG,
        venue="Corvane House, London (Design Authority room) with Leeds on video", chair=TW, author=NP, approver=TW,
        speakers=sp, d=DATE, forum_line="Design Authority - reserve-engine design review",
        versions=[("0.1", "2026-03-05", "N. Petrovic", "Automated transcript from the bridge recording"),
                  ("0.2", "2026-03-05", "N. Petrovic", "Program and table names checked against the CRUD matrix"),
                  ("1.0", "2026-03-05", "T. Wojcik (chair)", "Approved as the record of the review")],
        extra_notes=["Callum Fairbairn (IBM) is the IBM Data Migration Lead (not the Leeds motor team leader of the same name).",
                     "Program names (CLRxxnnn) and table names are as spoken; corrections made in the session are left in place."]))
    pl = lambda k: placement(FID, k)

    t_open = Topic("opening", ["the review scope", "the design pack", "the reserve-engine design", "the review format"],
                   domain="reserving", leads=[TW, NP], lines=[
        (TW, "This is a Design Authority review, so the output is decisions or ADRs, not just discussion."),
        (NP, "I've circulated the design pack. I'll walk through the sections that changed since the last review."),
        (LK, "From Reserving, I'm mostly here to make sure what the engine does matches what we actually do at month-end."),
        (SM, "And I'm here for the actuarial view, which is mostly about the movement history."),
    ])
    t_par = Topic("parallel", ["the parallel run", "the reconciliation report", "the first few days of the parallel run",
                               "the bridge feed", "the reconciliation breaks", "the daily comparison",
                               "the break investigation process", "the movement replay"],
                  domain="reserving", leads=[DA, NP, LK], lines=[
        (DA, "The first few days have been mostly about plumbing. Making sure every movement that leaves CLARA arrives in the engine."),
        (NP, "The comparison runs every morning and the squad triage the breaks before the stand-up."),
        (LK, "My team are looking at the breaks with the squad. Most of them so far are timing rather than amount."),
        (KB, "On the CLARA side the reconciliation program is CLRRS210. It's new, it went in at the end of February just for the parallel run."),
        (SM, "I'd like to see the breaks categorised by reserve type, so we can see whether it's an indemnity problem or an expense problem."),
        (DA, "The bridge has been solid. The messages arrive; it's what we do with them that we're tuning."),
        (CF, "From migration, the parallel run is also our best rehearsal for reconciling migrated reserves, so we're watching closely."),
        (GS, "The thing to remember is that CLARA has thirty years of edge cases. The engine is going to meet some of them for the first time."),
    ])
    t_wr = Topic("writers", ["the CRUD matrix", "the reserve table", "the writer programs", "the data dictionary",
                             "the static analysis", "the movement table", "the synchronisation design",
                             "the program inventory"],
                 domain="reserving", leads=[DA, KB, GS], lines=[
        (GS, "The CRUD matrix came out of static analysis of every program, so it's what the code does, not what people remember."),
        (KB, "Thirty years of changes, and not all of them made it into the documentation."),
        (DA, "From our side, the important thing is that every write to the reserve table also produces a movement, otherwise the engine can't see it."),
        (NP, "That's the design assumption the whole synchronisation rests on, so it matters that we get this right."),
        (LK, "If something writes the reserve table without a movement, my month-end numbers won't match the engine's."),
        (KB, "Most of them write the movement in the same unit of work. That's the pattern."),
        (GS, "We found the writers by searching for every UPDATE and INSERT against the table, not by asking people."),
    ])
    t_map = Topic("mapping", ["the movement types", "the event mapping", "the default reserve", "the reserve close-down",
                              "the recovery netting", "the currency handling", "the copybook fields",
                              "the movement history", "the reserve types"],
                  domain="reserving", leads=[DA, NP, KB, SM], lines=[
        (NP, "Every movement in RSVMOVE has a type, and the engine maps each type to its own event."),
        (KB, "RM-AMOUNT is in the claim currency and RM-GBP-AMOUNT is the sterling equivalent, with RM-CURRENCY telling you which currency."),
        (DA, "The engine stores both, the original currency and GBP. That's ADR-016."),
        (SM, "The actuaries mostly care about the GBP history, but the Nordic teams need the local currency for their own reporting."),
        (KB, "The default reserve at FNOL comes from CLRFN030 when the claim record is created. It uses the default amounts in T_PARAM."),
        (LK, "Close-down at settlement is the one I care about. If the reserve isn't zeroed when the claim settles, it sits in outstanding forever."),
        (DA, "Recovery receipts net off the case reserve, so a recovery is a negative movement as far as the engine is concerned."),
        (NP, "We've got a mapping table in the design pack: movement type, source program, engine event."),
        (GS, "And the movement correction utility needs a mention too, because it only touches the movement history."),
        (KB, "When CLRST040 closes a claim down at final settlement it writes a settlement close movement, type ST, so the engine sees the reserve go to zero."),
    ])
    t_rev = Topic("revaluation", ["the year-end revaluation", "the audit finding", "the currency revaluation",
                                  "the revaluation run", "the RV movement type", "the January abend",
                                  "the year-end rates", "the audit trail"],
                  domain="reserving", leads=[KB, DA, LK, SM, TW], lines=[
        (KB, "CLRGL090 runs once a year at year-end. It revalues the Nordic reserves to GBP at the year-end rate."),
        (LK, "Internal audit picked it up because the revaluation changes the reserve but leaves no movement behind."),
        (SM, "From an actuarial point of view, a change in reserve with no movement is a hole in the triangle."),
        (KB, "Changing CLRGL090 now is risky. It's a once-a-year job and we'd be testing it once a year."),
        (DA, "In the engine it's easy to do properly: a revaluation is just another movement type."),
        (TW, "Then I'd rather fix it in the target than patch something we're retiring."),
        (KB, "The January abend was a data problem, not a logic problem. A Swedish rate came through with a comma as the decimal separator."),
        (NP, "The engine validates rates before it uses them, so that particular failure can't happen there."),
    ])
    t_cad = Topic("cadence", ["the Tier-3 review cadence", "the review scheduler", "the overdue reviews",
                              "the Reserving Committee paper", "the handler workload", "the review diary"],
                  domain="reserving", leads=[LK, SM, DA], lines=[
        (LK, "The Tier-3 claims are the ones where the case estimate moves the most. Reviewing them more often is just good practice."),
        (SM, "I'd support it. The movement history on Tier-3 claims is where the surprises come from."),
        (DA, "The engine schedules reviews from a configuration value, so a cadence change is configuration for us."),
        (KB, "In CLARA the review scheduler is CLRRS110, and it reads the cadence from T_PARAM."),
        (LK, "The Major & Complex Loss team will need to know. It's more work for them, and they'll want notice."),
    ])
    t_close = Topic("close", ["the action list", "the ADR write-up", "the next review"], domain="reserving",
                    leads=[TW, NP], lines=[
        (LK, "Thanks for the challenge on the writers, Keith. That would have caught us out at month-end."),
        (DA, "I'll get the updated design pack out once the mapping table is redone."),
    ])

    # ------------------------------------------------------------------ 00:00
    m.say(TW, "Okay, let's start. Afternoon, everyone, and hello to Leeds. This is the Design Authority review of the reserve-engine design. Nadia's recording.")
    m.say(NP, "Yes, recording. Afternoon.")
    m.say(TW, "Agenda: the first days of the parallel run, then which programs write the reserve table, because that drives the synchronisation design, then event mapping, then the revaluation finding, and finally the Tier-3 review cadence. Lena and Sebastian are here for the business and actuarial view.")
    m.script(m.at(3, 0), t_open, [
        (TW, "Daniel, do you want to start with the parallel run?"),
    ])
    n = m.say(DA, "Sure. So the reserve parallel run started on Monday, the 2nd of March. CLARA stays the master, the movements come across through the CLX-IF-049 bridge onto the claims.reserve.movement.v1 topic, and reserve-engine recalculates the reserves so we can compare.")
    m.doc.fact(n, needle="the reserve parallel run started on Monday, the 2nd of March", kind="general", world_ref="TICKET:CHUB-241",
               statement="The reserve parallel run (CLARA vs reserve-engine) started on 2026-03-02; movements arrive via the CLX-IF-049 bridge on claims.reserve.movement.v1.")
    n = m.say(DA, "And just for the minutes, it's reserve-engine now. The rename from reserve-svc went in on the 10th of February under ADR-019, so if anyone sees reserve-svc in an old document, it's the same service.")
    m.doc.fact(n, needle="The rename from reserve-svc went in on the 10th of February under ADR-019", kind="general",
               world_ref="SERVICE:reserve-engine#renames", statement="reserve-svc was renamed reserve-engine on 2026-02-10 under ADR-019.")
    m.script(m.at(29, 40), t_par, [
        (TW, "Thanks. Let's move to the writers question, because it's the one that matters for the design."),
        (NP, "So, the synchronisation design assumes we know every program that writes the reserve table, CLR.T_RESERVE, and that every one of them writes a movement as well."),
    ])
    m.fill(m.at(38, 5), t_wr)
    n = m.say(DA, "From what we've seen in the code so far, it's only the CLRRS reserve programs that write to the reserve table. So CLRRS010, CLRRS020, CLRRS110 and CLRRS130. Everything else just reads it.")
    m.doc.fact(n, needle="it's only the CLRRS reserve programs that write to the reserve table", kind="contradiction_old",
               placement=pl("tx3_wrong"),
               statement="At about 00:38 Daniel Achebe says only the CLRRS reserve programs write the reserve table CLR.T_RESERVE (wrong; corrected at about 00:46).")
    m.say(LK, "That's a shorter list than I expected, to be honest.")
    m.say(GS, "Let me just pull up the matrix. I want to check that against the static analysis before we build on it.")
    m.fill(m.at(46, 2), t_wr, min_gap=5)
    n = m.say(KB, "Daniel, sorry, that's not right. It's not only the CLRRS programs. CLRFN030, CLRST040, CLRRC050 and CLRGL090 also write CLR.T_RESERVE. CLRFN030 creates the default reserve when the claim is set up, CLRST040 closes the reserve down at settlement, CLRRC050 nets recoveries off the case reserve, and CLRGL090 does the year-end revaluation.")
    m.doc.fact(n, needle="CLRFN030, CLRST040, CLRRC050 and CLRGL090 also write CLR.T_RESERVE", kind="contradiction_new",
               placement=pl("tx3_right"),
               statement="Keith Barraclough corrects him: CLRFN030, CLRST040, CLRRC050 and CLRGL090 also write CLR.T_RESERVE (eight writers in total).")
    n = m.say(GS, "Keith's right, that matches the matrix. Eight writers in total: the four CLRRS ones plus those four. And CLRRS150 is a red herring, it only writes the movement table, never the reserve table itself.")
    m.doc.fact(n, needle="Eight writers in total", kind="needle", world_ref="TABLE:CLR.T_RESERVE#writers",
               statement="Eight programs write CLR.T_RESERVE: CLRRS010, CLRRS020, CLRRS110, CLRRS130, CLRFN030, CLRST040, CLRRC050 and CLRGL090.")
    m.doc.fact(n, needle="CLRRS150 is a red herring, it only writes the movement table", kind="needle",
               world_ref="PROGRAM:CLRRS150#writes_tables", statement="CLRRS150 writes only CLR.T_RESERVE_MOVEMENT, not CLR.T_RESERVE.")
    m.say(DA, "Okay, thank you. I was going off the CLRRS naming, which is clearly not enough. Good catch.")
    n = m.say(KB, "It's an easy mistake. The data dictionary only lists seven writers anyway. It's missing CLRGL090, because that one only runs at year-end and nobody thinks of it.")
    m.doc.fact(n, needle="The data dictionary only lists seven writers", kind="general", world_ref="TABLE:CLR.T_RESERVE#writers",
               statement="The CLARA data dictionary lists only seven writers of CLR.T_RESERVE; it omits CLRGL090.")
    # CHUB-104's matrix covered the programs that existed when it was resolved (2025-04-11); the 122-program
    # reissue (key_tickets description) is dated 2026-08-20, after this meeting.
    chub104 = W.tickets["CHUB-104"]
    n_progs = sum(1 for p in W.programs.values() if str(p.get("since", "1900-01-01")) <= str(chub104["resolved"]))
    m.say(GS, f"Which is exactly why we did the CRUD matrix from the code, under CHUB-104. All {n_progs} programs.")
    m.script(m.at(52, 30), t_wr, [
        (TW, "Okay. So the design has to cover eight writers. Let's go through the mapping."),
    ])
    m.fill(m.at(19, hh=1), t_map)
    m.script(m.at(20, hh=1), t_map, [
        (TW, "Right, the revaluation. Keith, can you set it up?"),
    ])
    n = m.say(KB, "So, CLRGL090 is the year-end reserve currency revaluation. It takes the Nordic reserves and revalues them to GBP. The problem internal audit found, IA-25-07, is that it updates the reserve table but doesn't write a reserve movement.")
    m.doc.fact(n, needle="IA-25-07", kind="general", world_ref="TICKET:CHUB-284",
               statement="Internal audit finding IA-25-07: CLRGL090's year-end revaluation updates CLR.T_RESERVE without writing a reserve movement.")
    n = m.say(KB, "And it abended at year-end, on the 2nd of January, with an S0C7 because the Swedish year-end rate came through with a comma as the decimal separator. CLRYGL90 was rerun the same morning.")
    m.doc.fact(n, needle="S0C7", kind="general", world_ref="INCIDENT:INC-2026-0104",
               statement="INC-2026-0104: CLRGL090 abended with S0C7 on 2026-01-02 on a malformed SEK year-end rate; CLRYGL90 was rerun.")
    m.fill(m.at(40, hh=1), t_rev)
    n = m.say(TW, "So the decision is: reserve-engine will record currency revaluations as RV movements, which closes IA-25-07 in the target, and CLRGL090 stays unchanged in CLARA. Lena, Daniel, you're both okay with that?")
    m.doc.fact(n, needle="reserve-engine will record currency revaluations as RV movements", kind="needle",
               placement=pl("tx3_dec005"),
               statement="Decision DEC-005: reserve-engine records currency revaluations as RV movements, closing IA-25-07 in the target; CLRGL090 stays unchanged in CLARA.")
    m.say(LK, "Yes, agreed.")
    m.say(DA, "Agreed. We'll add RV as a movement type in the engine.")
    n = m.say(KB, "Then I'll close CHUB-284 as won't do on the CLARA side, with a pointer to this decision.")
    m.doc.fact(n, needle="close CHUB-284 as won't do", kind="general", world_ref="TICKET:CHUB-284",
               statement="CHUB-284 (IA-25-07) is closed as Won't Do in CLARA; the finding is addressed in reserve-engine per DEC-005.")
    m.say(TW, "And I'll write it up as an ADR so it's on the register.")
    m.script(m.at(45, hh=1), t_rev, [
        (TW, "Last item. Lena, the Tier-3 review cadence."),
    ])
    n = m.say(LK, "Thanks. Today Tier-3 reserves have to be reviewed at least every 21 days. I'd like to propose 14 days from the 1st of July to the Reserving Committee, and I'd like this group's support for the system side.")
    m.doc.fact(n, needle="propose 14 days from the 1st of July to the Reserving Committee", kind="needle", world_ref="DECISION:DEC-006",
               statement="DEC-006: Lena Kristiansen will propose a 14-day Tier-3 reserve review cadence from 2026-07-01 to the Reserving Committee (current rule: 21 days).")
    m.say(SM, "Supported from Actuarial.")
    m.say(DA, "And it's a configuration change in the engine, so no objection from us. We'd need to make sure CLARA and the engine change on the same day, or the parallel run will flag every Tier-3 claim.")
    m.say(KB, "CLARA reads it from T_PARAM, so it's a parameter row with a valid-from date.")
    m.script(m.at(54, hh=1), t_cad, [
        (TW, "Nadia, can you read back the actions?"),
    ])
    m.say(NP, "Decisions: reserve-engine records currency revaluations as RV movements, closing IA-25-07 in the target, with CLRGL090 unchanged in CLARA. And Lena will propose the 14-day Tier-3 cadence from the 1st of July to the Reserving Committee, with this group's support.")
    m.say(NP, "Actions: Daniel, update the synchronisation design to cover all eight writers of CLR.T_RESERVE. Gordon, reissue the writer list from the CRUD matrix with a note on CLRRS150. Keith, close CHUB-284 with the reference. Tomasz, the ADR for the revaluation. Callum, check the migration reconciliation covers the same eight writers. Lena, the Reserving Committee paper.")
    m.say(CF, "Yes, will do.")
    m.say(TW, "Anything else before we close?")
    m.fill(m.at(58, 10, hh=1), t_close)
    m.say(TW, "Thanks, everyone. Good review.")
    m.say(KB, "Cheers, bye.")
    m.say(LK, "Thanks, Tomasz.")
    m.note("Recording stopped.")
    footer(m, DATE, NP)
    return m

"""TX007-TX020: email threads exported as plain text."""
from __future__ import annotations

from generators.common import util

from . import phrases as PH
from .core import W, Doc, person, pick, clock, later, short_date, day_month, require
from .mail import F, P, Msg, ThreadWriter


def _doc(fid: str, width: int) -> Doc:
    return Doc(fid, W.anchor(fid)["filename"], width=width)


def _r(fid: str):
    return util.rng(f"{fid}:messages")


# ---------------------------------------------------------------------------------------------
# TX007 – business case sign-off (2024-11-18): 'the CFO' is Gareth Whitcombe
# ---------------------------------------------------------------------------------------------

def tx007():
    fid = "TX007"
    r = _r(fid)
    doc = _doc(fid, 74)
    subj = "Programme Skerry – business case v1.0 for CFO approval"
    ing = person("P005", "2024-11-14")
    t1 = clock(r, "16:10", "17:40")
    m1 = Msg("P004", ["P002"], "2024-11-13", t1, subj, cc=["P003", "P006", "P005"],
             greeting="Gareth,",
             body=[
                 P("Attached is the final Programme Skerry business case (v1.0) for your approval as CFO. "
                   "It sets out the replacement of CLARA by Claims Hub through a phased migration and asks "
                   "for a total programme budget of £48.6m.",
                   facts=[F("asks for a total programme budget of £48.6m",
                            "The Programme Skerry business case (v1.0) asked for a total budget of £48.6m.",
                            "needle", "TIMELINE:metrics#programme_budget_gbp_m")]),
                 "Comments from your team on the draft have been worked in, and the benefits section now "
                 "follows the format Finance asked for. Helena and Adaeze are copied, as is Ingrid for the "
                 "Claims view.",
                 "Once it is signed we can confirm the delivery partner and plan mobilisation for January.",
                 pick(r, PH.CLOSE_OFFER),
             ],
             signoff=pick(r, ["Thanks,", "Many thanks,", "Regards,"]), signame="Duncan", sig="full",
             attachments=["Programme_Skerry_Business_Case_v1.0.pdf"])
    m2 = Msg("P005", ["P004", "P002"], "2024-11-14", clock(r, "08:20", "09:30"), "RE: " + subj,
             cc=["P003", "P006"], greeting=f"Duncan, Gareth,",
             body=[
                 P("From the Claims side we fully support this. CLARA has been our system of record since it "
                   "went live in 1994, and the handling teams in Leeds and the Nordic branches feel the cost of "
                   "working around it every day.",
                   facts=[F("since it went live in 1994",
                            "CLARA has been Corvane's claims system of record since its go-live in 1994.",
                            "general", "SYSTEM:SYS01#go_live")]),
                 "I am comfortable with the phasing in section 6 and will make my operations leads available "
                 "for the design work from the start.",
             ],
             signoff=pick(r, PH.SIGNOFF), signame="Ingrid", sig="full")
    m3 = Msg("P006", ["P004", "P002"], "2024-11-15", clock(r, "11:00", "15:30"), "RE: " + subj,
             cc=["P003", "P005"], greeting="All,",
             body=[
                 "Technology view: supportive. The target architecture in the appendix matches what the "
                 "architecture team reviewed, and the phasing keeps CLARA running alongside the new platform "
                 "until each migration wave is complete.",
                 pick(r, PH.CLOSE_OFFER),
             ],
             signoff=pick(r, PH.SIGNOFF), signame="Adaeze", sig="short")
    gw = person("P002", "2024-11-18")
    m4 = Msg("P002", ["P004"], "2024-11-18", clock(r, "09:40", "12:10"), "RE: " + subj,
             cc=["P003", "P005", "P006"], greeting="Duncan,",
             body=[
                 "Thank you, and thanks to Ingrid and Adaeze for the supporting notes. I have been through "
                 "the final version, including the revised benefits profile.",
                 P("I approve the Programme Skerry business case with a total budget of £48.6m.",
                   facts=[F("I approve the Programme Skerry business case with a total budget of £48.6m",
                            "On 2024-11-18 the CFO (Gareth Whitcombe) approved the Programme Skerry business case "
                            "with a total budget of £48.6m.", "needle", "EVENT:EV-010")]),
                 "Finance will track spend against the approved budget through the programme governance, "
                 "and I would like the first quarterly view once the delivery partner is mobilised.",
             ],
             signoff=None, sig="custom",
             sig_lines=["Approved and signed for Finance,", "the CFO", "", gw.name, gw.title,
                        "Corvane Mutual Insurance Society Limited", gw.address, f"T: {gw.phone}", gw.email],
             sig_facts=[F("signed for Finance, the CFO", key="tx7_cfo",
                          notes="The sign-off line reads 'the CFO'; the name below it and the From header are "
                                "Gareth Whitcombe (CFO until 2025-06-30)."),
                        F("Gareth Whitcombe Chief Financial Officer",
                          "Gareth Whitcombe was Chief Financial Officer on 2024-11-18.", "temporal",
                          "PERSON:P002#titles")],
             disclaimer=True)
    tw = ThreadWriter(doc, r, width=74)
    tw.render([m1, m2, m3, m4], "outlook")
    return doc


# ---------------------------------------------------------------------------------------------
# TX008 – Fellgate panel removal (2026-01-21)
# ---------------------------------------------------------------------------------------------

def tx008():
    fid = "TX008"
    r = _r(fid)
    doc = _doc(fid, 76)
    subj = "Assessor panel change – Fellgate Adjusting Partners leaving the panel on 31 January"
    dl = "Claims Assessment UK <claims.assessment.uk@corvane-mutual.example>"
    t1 = clock(r, "08:30", "09:20")
    m1 = Msg("P033", [dl, "P030", "P039"], "2026-01-21", t1, subj, cc=["P011", "P057"],
             greeting=pick(r, PH.GREET_FORMAL),
             body=[
                 P("Following the decision taken yesterday, Fellgate Adjusting Partners LLP leaves the assessor "
                   "panel with effect from 31 January 2026, and all open Fellgate instructions transfer to "
                   "Brackenfield Loss Adjusting.",
                   facts=[F("Fellgate Adjusting Partners LLP leaves the assessor panel with effect from 31 January "
                            "2026, and all open Fellgate instructions transfer to Brackenfield Loss Adjusting",
                            key="tx8_fellgate")]),
                 "Colin Rudd (copied) is coordinating the handover on the Brackenfield side. Transferred "
                 "instructions will be re-issued through the Assessor Portal so the history stays on the "
                 "claim file.",
                 "In the meantime please check your open files for Fellgate involvement and let my team know "
                 "about anything time-critical, for example a site visit that is already booked.",
                 "Rob is copied for visibility.",
             ],
             signoff=pick(r, ["Thanks,", "Many thanks,", "Regards,"]), signame="Imran", sig="full")
    m2 = Msg("P030", ["P033"], "2026-01-21", later(r, t1, 25, 80), "RE: " + subj, cc=["P057"],
             greeting=pick(r, ["Thanks Imran,", "Imran,", "Hi Imran,"]),
             body=[
                 P("Major & Complex Loss has a handful of live Fellgate instructions – as you would expect, "
                   "given they were our major-loss adjusters. I will send you the list today so those can be "
                   "prioritised in the transfer.",
                   facts=[F("given they were our major-loss adjusters",
                            "Fellgate Adjusting Partners were major-loss adjusters (Claims Assessors) on Corvane's panel.",
                            "general", "VENDOR:VEN-03#role")]),
                 pick(r, PH.CLOSE_OFFER),
             ],
             signoff=pick(r, PH.SIGNOFF_SHORT), signame="Kirsty", sig="short")
    m3 = Msg("P057", ["P033"], "2026-01-21", later(r, m2.time, 30, 120), "RE: " + subj, cc=["P030"],
             greeting=pick(r, ["Imran,", "Hi Imran,", "Dear Imran,"]),
             body=[
                 "Thanks – confirming Brackenfield will take on the transferred instructions. Our team will "
                 "contact the handlers directly where a site visit or report is outstanding, and we will "
                 "acknowledge each re-issued instruction through the portal as usual.",
                 "Kirsty, happy to set up a short call on the major-loss files once your list comes through.",
             ],
             signoff=pick(r, PH.SIGNOFF), signame="Colin", sig="full", disclaimer=True)
    m4 = Msg("P033", ["P057", "P030"], "2026-01-21", later(r, m3.time, 20, 90), "RE: " + subj,
             greeting="Thanks both,",
             body=[
                 "Kirsty – list received, thank you. Colin – I will send a meeting request for Friday.",
                 pick(r, PH.FOLLOW_UP),
             ],
             signoff=None, signame="Imran", sig="none", disclaimer=False)
    tw = ThreadWriter(doc, r, width=76)
    tw.render([m1, m2, m3, m4], "archive")
    return doc


# ---------------------------------------------------------------------------------------------
# TX009 – subrogation pursuit threshold (2025-06-12): £750 (correct at the time)
# ---------------------------------------------------------------------------------------------

def tx009():
    fid = "TX009"
    r = _r(fid)
    doc = _doc(fid, 72)
    subj = "Subrogation – minimum amount before we refer?"
    t1 = clock(r, "15:05", "16:50")
    m1 = Msg("P039", ["P014"], "2025-06-11", t1, subj,
             greeting=pick(r, ["Hi Siobhan,", "Siobhan,", "Hello Siobhan,"]),
             body=[
                 "A couple of my handlers have asked what the minimum recoverable amount is before we refer a "
                 "claim to Recoveries for sub-ro. One of them thought it was still £500, which I am fairly sure "
                 "is out of date.",
                 "Could you confirm the current figure so I can brief the team at the next huddle?",
             ],
             signoff=pick(r, PH.SIGNOFF_SHORT), signame="Gemma", sig="full")
    sq = person("P014", "2025-06-12")
    m2 = Msg("P014", ["P039"], "2025-06-12", clock(r, "08:40", "10:15"), "RE: " + subj,
             cc=["Recoveries Bristol <recoveries.bristol@corvane-mutual.example>"],
             greeting=pick(r, ["Hi Gemma,", "Morning Gemma,", "Gemma,"]),
             body=[
                 P("The current threshold is £750: we pursue subrogation where the recoverable amount is £750 or "
                   "more (BR-REC-003).",
                   facts=[F("we pursue subrogation where the recoverable amount is £750 or more", key="tx9_750",
                            notes="Correct on 2025-06-12 (BR-REC-003 v2, 2022-07-01 to 2025-08-31); v3 raised it to "
                                  "£1,000 from 2025-09-01.")]),
                 P("The £500 figure was the old rule – it was replaced in 2022.",
                   facts=[F("The £500 figure was the old rule – it was replaced in 2022",
                            "The £500 subrogation threshold (BR-REC-003 v1) was replaced in 2022.",
                            "temporal", "RULE:BR-REC-003@v1#parameters.min_gbp")]),
                 "If a case is borderline, or further costs are likely to come through, refer it anyway and we "
                 "will take a view.",
             ],
             signoff=pick(r, PH.SIGNOFF), signame="Siobhan", sig="full",
             sig_facts=[F("Acting Recoveries Manager",
                          "On 2025-06-12 Siobhan Quill signed as Acting Recoveries Manager.", "temporal",
                          "PERSON:P014#titles")])
    m3 = Msg("P039", ["P014"], "2025-06-12", later(r, m2.time, 15, 70), "RE: " + subj,
             greeting=None,
             body=[pick(r, ["Perfect, thanks Siobhan – I will brief the team tomorrow.",
                            "Thanks Siobhan, that is clear. I will pass it on at tomorrow's huddle.",
                            "Great – thanks for the quick reply. Will brief the team."])],
             signoff=None, signame="Gemma", sig="none", disclaimer=False)
    tw = ThreadWriter(doc, r, width=72)
    tw.render([m1, m2, m3], "mbox")
    return doc


# ---------------------------------------------------------------------------------------------
# TX010 – UK motor backlog (2026-10-19): Corvane Callum Fairbairn (exclusive)
# ---------------------------------------------------------------------------------------------

def tx010():
    fid = "TX010"
    r = _r(fid)
    doc = _doc(fid, 74)
    subj = "UK motor open claims – Leeds queue position, 19 October"
    cf = person("P022", "2026-10-19")
    t1 = clock(r, "07:40", "08:25")
    m1 = Msg("P022", ["P011"], "2026-10-19", t1, subj, cc=["P017", "P033"],
             greeting="Rob,",
             body=[
                 "Quick position on the Leeds motor queue as of this morning.",
                 "We have 1,140 open UK motor claims in the Leeds queue. I have taken the figure straight from "
                 "the Claims Hub work queue view rather than the weekly MI pack, so it is today's position.",
                 "I would like twenty minutes at Thursday's operations call to go through the ageing and what we "
                 "need over the next few weeks. Aisha and Imran are copied as some of it touches work-queue "
                 "behaviour and assessor turnaround.",
             ],
             signoff="Thanks,", signame="Callum", sig="custom",
             sig_lines=["", cf.name, "Motor Claims Team Leader, Leeds", "Corvane Mutual Insurance Society Limited",
                        cf.address, f"T: {cf.phone}", cf.email],
             whole_facts=[F("We have 1,140 open UK motor claims in the Leeds queue", key="tx10_backlog",
                            notes="Sender is the Corvane Callum Fairbairn (P022, callum.fairbairn@corvane-mutual.example), "
                                  "not the IBM namesake (P051).")],
             sig_facts=[F("Motor Claims Team Leader, Leeds",
                          "The Callum Fairbairn who reported the Leeds motor queue is Corvane's Motor Claims Team Leader "
                          "in Leeds (P022).", "alias_use", "PERSON:P022#titles")])
    m2 = Msg("P011", ["P022"], "2026-10-19", later(r, t1, 40, 120), "RE: " + subj, cc=["P017", "P033"],
             greeting=pick(r, ["Thanks Callum,", "Callum,", "Morning Callum,"]),
             body=[
                 "Yes – take the first slot on Thursday. Please bring the ageing split and anything you need from "
                 "Assessment so we can agree actions in the room.",
                 "Aisha, worth you joining for that item if you can.",
             ],
             signoff=None, signame="Rob", sig="short")
    m3 = Msg("P017", ["P011", "P022"], "2026-10-19", later(r, m2.time, 30, 150), "RE: " + subj, cc=["P033"],
             greeting=None,
             body=[
                 "Happy to join. If any of it is down to work-queue behaviour in the Hub, send me a few claim "
                 "examples beforehand and I will get the squad to look before Thursday.",
             ],
             signoff=pick(r, PH.SIGNOFF_SHORT), signame="Aisha", sig="short")
    tw = ThreadWriter(doc, r, width=74)
    tw.render([m1, m2, m3], "archive")
    return doc


# ---------------------------------------------------------------------------------------------
# TX011 – Wave 1 reconciliation (2026-08-25): IBM Callum Fairbairn (exclusive)
# ---------------------------------------------------------------------------------------------

def tx011():
    fid = "TX011"
    r = _r(fid)
    doc = _doc(fid, 74)
    subj = "Wave 1 – final rehearsal reconciliation result"
    cf = person("P051", "2026-08-25")
    t1 = clock(r, "11:05", "12:20")
    m1 = Msg("P051", ["P017", "P048"], "2026-08-25", t1, subj, cc=["P016", "P041", "P009"],
             greeting="Aisha, Arjun,",
             body=[
                 "The final Wave 1 rehearsal reconciled 186,400 claims with 3 exceptions.",
                 "The exceptions are listed in the attached log with an owner against each, and we are working "
                 "them through with Graham's and Daniel's teams. The summary tab is the one for the go/no-go pack; "
                 "the detail tabs cover claim and reserve comparisons at claim level.",
                 pick(r, PH.CLOSE_OFFER),
             ],
             signoff=pick(r, ["Thanks,", "Regards,", "Best,"]), signame="Callum", sig="custom",
             sig_lines=["", cf.name, "Data Migration Lead", "IBM Consulting | Programme Skerry",
                        f"M: {cf.phone}", cf.email],
             attachments=["W1_Rehearsal3_Reconciliation_Summary.xlsx"],
             whole_facts=[F("The final Wave 1 rehearsal reconciled 186,400 claims with 3 exceptions", key="tx11_recon",
                            notes="Sender is IBM's Callum Fairbairn (P051, callum.fairbairn@ibm-consulting.example), "
                                  "not the Corvane Motor Claims Team Leader (P022).")],
             sig_facts=[F("Data Migration Lead IBM Consulting",
                          "The Callum Fairbairn reporting the Wave 1 rehearsal reconciliation is IBM Consulting's Data "
                          "Migration Lead (P051).", "alias_use", "PERSON:P051#titles")])
    m2 = Msg("P017", ["P051", "P048"], "2026-08-25", later(r, t1, 35, 95), "RE: " + subj,
             cc=["P016", "P041", "P009"], greeting=pick(r, ["Thanks Callum,", "Callum,"]),
             body=[
                 P("Good news. Please make sure the summary goes into the go/no-go pack for 11 September.",
                   facts=[F("go/no-go pack for 11 September",
                            "The Wave 1 go/no-go meeting was held on 2026-09-11.", "general", "MEETING:MTG-011#date")]),
             ],
             signoff=None, signame="Aisha", sig="short")
    m3 = Msg("P048", ["P017", "P051"], "2026-08-25", later(r, m2.time, 20, 90), "RE: " + subj,
             cc=["P016", "P041", "P009"], greeting=None,
             body=[
                 "Will do – it is in the pack outline.",
                 P("Graham, can your team confirm the CLARA-side steps for the planned freeze from 18:00 on Friday "
                   "11 September to 06:00 on Monday 14 September by the end of next week?",
                   facts=[F("freeze from 18:00 on Friday 11 September to 06:00 on Monday 14 September",
                            "The Wave 1 freeze ran from 2026-09-11 18:00 to 2026-09-14 06:00.", "needle",
                            "WAVE:MW-1#freeze")]),
             ],
             signoff=pick(r, PH.SIGNOFF_SHORT), signame="Arjun", sig="short")
    m4 = Msg("P016", ["P048"], "2026-08-25", later(r, m3.time, 25, 110), "RE: " + subj,
             cc=["P017", "P051", "P041", "P009"], greeting=None,
             body=[
                 "Yes. Sunita is updating the batch schedule for the freeze window and will send it across with "
                 "the CLARA steps.",
             ],
             signoff=None, signame="Graham", sig="short")
    tw = ThreadWriter(doc, r, width=74)
    tw.render([m1, m2, m3, m4], "outlook")
    return doc


# ---------------------------------------------------------------------------------------------
# TX012 – first NISA-FR1 return submitted (2026-07-29)
# ---------------------------------------------------------------------------------------------

def tx012():
    fid = "TX012"
    r = _r(fid)
    doc = _doc(fid, 74)
    subj = "NISA-FR1 Q2 2026 – first return submitted"
    t1 = clock(r, "13:10", "14:20")
    m1 = Msg("P037", ["P008", "P007"], "2026-07-29", t1, subj, cc=["P020", "P005", "P028"],
             greeting="Niall, Karin,",
             body=[
                 P("We submitted our first NISA-FR1 fraud referral return, for Q2 2026, to NISA today (29 July 2026) "
                   "– one day before the 30 July deadline.",
                   facts=[F("submitted our first NISA-FR1 fraud referral return, for Q2 2026, to NISA today "
                            "(29 July 2026) – one day before the 30 July deadline", key="tx12_fr1")]),
                 P("The return reports 1,488 referrals for the quarter, our first full quarter under the 65 "
                   "threshold.",
                   facts=[F("The return reports 1,488 referrals for the quarter",
                            "The 2026Q2 NISA-FR1 return reported 1,488 fraud referrals.", "needle",
                            "REPORT:NISA-FR1#submissions.2026Q2.referrals")]),
                 P("Bjørn and the Regulatory Reporting team prepared it in the NISA Reporting Hub, and I signed it "
                   "off for Compliance.",
                   facts=[F("Regulatory Reporting team prepared it in the NISA Reporting Hub",
                            "The NISA-FR1 return is prepared by Regulatory Reporting (Bjørn Aasheim) in the NISA Reporting "
                            "Hub and signed off by the Compliance Manager – Conduct & Counter-Fraud.", "general",
                            "REPORT:NISA-FR1#preparer")]),
                 P("The Q3 return is due by 30 October.",
                   facts=[F("The Q3 return is due by 30 October",
                            "The 2026Q3 NISA-FR1 return was due by 2026-10-30.", "general",
                            "REPORT:NISA-FR1#submissions.2026Q3.due")]),
                 pick(r, PH.CLOSE_OFFER),
             ],
             signoff=pick(r, PH.SIGNOFF), signame="Ruth", sig="full")
    m2 = Msg("P008", ["P037"], "2026-07-29", later(r, t1, 20, 90), "RE: " + subj, cc=["P007", "P020", "P005", "P028"],
             greeting=pick(r, ["Thanks Ruth,", "Ruth,"]),
             body=["A good result for the first one – thanks to you and to Bjørn's team."],
             signoff=None, signame="Niall", sig="short")
    m3 = Msg("P007", ["P037"], "2026-07-29", later(r, m2.time, 15, 60), "RE: " + subj,
             cc=["P008", "P020", "P005", "P028"], greeting=None,
             body=["Echo that – well done all. Ruth, please include a short note on the submission in my next "
                   "update to the Executive Committee."],
             signoff=pick(r, PH.SIGNOFF_SHORT), signame="Karin", sig="short")
    m4 = Msg("P020", ["P037", "P008", "P007"], "2026-07-29", later(r, m3.time, 10, 50), "RE: " + subj,
             cc=["P005", "P028"], greeting="Thanks all,",
             body=["We have noted a couple of small improvements to the extract timing for Q3 and will cover them "
                   "at the next preparation meeting."],
             signoff=None, signame="Bjørn", sig="short")
    tw = ThreadWriter(doc, r, width=74)
    tw.render([m1, m2, m3, m4], "mbox")
    return doc


# ---------------------------------------------------------------------------------------------
# TX013 – contingency drawdown (2026-10-09): signed 'PR'
# ---------------------------------------------------------------------------------------------

def tx013():
    fid = "TX013"
    r = _r(fid)
    doc = _doc(fid, 74)
    subj = "Wave 2 – contingency drawdown request (£1.8m) for approval"
    t1 = clock(r, "17:15", "18:30")
    m1 = Msg("P048", ["P001"], "2026-10-08", t1, subj, cc=["P004", "P047"],
             greeting="Priya,",
             body=[
                 "Following today's Steering Committee, attached is the formal request to draw down £1.8m of "
                 "programme contingency for Wave 2.",
                 P("As the drawdown is above £500,000 it needs your approval as CFO. Duncan supported the request "
                   "in the meeting.",
                   facts=[F("As the drawdown is above £500,000 it needs your approval as CFO",
                            "Programme budget drawdowns above £500,000 need the CFO's approval.", "general",
                            "PERSON:P001#responsibilities")]),
                 pick(r, PH.CLOSE_OFFER),
             ],
             signoff=pick(r, ["Many thanks,", "Thanks,", "Kind regards,"]), signame="Arjun", sig="full",
             attachments=["Skerry_Wave2_Contingency_Drawdown_Request.pdf"])
    m2 = Msg("P001", ["P048"], "2026-10-09", clock(r, "07:35", "08:20"), "RE: " + subj, cc=["P004", "P047"],
             greeting="Arjun,",
             body=["Approved – £1.8m contingency drawdown for Wave 2, as discussed at the Steering Committee on "
                   "8 October."],
             signoff=None, sig="custom", sig_lines=["PR"], mobile=True, disclaimer=False,
             whole_facts=[F("Approved – £1.8m contingency drawdown for Wave 2", key="tx13_pr",
                            notes="The approval is signed only 'PR' (Priya Raman, CFO from 2025-07-01).")])
    fw = Msg("P048", ["Programme Skerry PMO <skerry.pmo@ibm-consulting.example>", "P049"], "2026-10-09",
             later(r, m2.time, 30, 100), "FW: " + subj, cc=["P047"],
             greeting=pick(r, ["Team,", "All,", "Hi both,"]),
             body=["FYI – contingency drawdown approved by the CFO this morning (below). Please update the financial "
                   "tracker and the Wave 2 plan baseline."],
             signoff=None, signame="Arjun", sig="short", forward=m2)
    tw = ThreadWriter(doc, r, width=74)
    tw.render([m1, m2, fw], "outlook")
    return doc


# ---------------------------------------------------------------------------------------------
# TX014 – Ingrid Sørensen becomes Ingrid Ashby (2025-08-29)
# ---------------------------------------------------------------------------------------------

def tx014():
    fid = "TX014"
    r = _r(fid)
    doc = _doc(fid, 72)
    ia = person("P005", "2025-08-29")
    m = Msg("P005", ["Claims Leadership Team <claims.leadership@corvane-mutual.example>"], "2025-08-29",
            clock(r, "09:05", "10:30"), "New name and email address – Ingrid Ashby", cc=["P004"],
            greeting=pick(r, ["Dear all,", "Dear colleagues,", "Hello all,"]),
            body=[
                P("A short personal note: I was married on Saturday 23 August, and from that date my name is "
                  "Ingrid Ashby (previously Ingrid Sørensen). My new email address is "
                  "ingrid.ashby@corvane-mutual.example.",
                  facts=[F("My new email address is ingrid.ashby@corvane-mutual.example", key="tx14_name"),
                         F("from that date my name is Ingrid Ashby (previously Ingrid Sørensen)",
                           "Ingrid Sørensen's name changed to Ingrid Ashby on 2025-08-23.", "alias_use",
                           "PERSON:P005#name_history")]),
                P("Messages sent to my old address (ingrid.sorensen@corvane-mutual.example) will reach me for a "
                  "while, but please update distribution lists, approval workflows and document templates that "
                  "still use my old name.",
                  facts=[F("my old address (ingrid.sorensen@corvane-mutual.example)",
                           "Ingrid's email address before 2025-08-23 was ingrid.sorensen@corvane-mutual.example.",
                           "temporal", "PERSON:P005#email_history")]),
                P("Nothing else changes: I remain Claims Director, and my phone number is the same.",
                  facts=[F("I remain Claims Director",
                           "Ingrid Ashby (formerly Sørensen) remained Claims Director after her name change.",
                           "general", "PERSON:P005#titles")]),
                pick(r, ["Thank you for all the kind messages.", "Thank you all for the lovely messages.",
                         "Thank you for the good wishes."]),
            ],
            signoff=pick(r, ["Best wishes,", "With thanks,", "Kind regards,"]), signame="Ingrid", sig="custom",
            sig_lines=["", "Ingrid Ashby (née Sørensen)", ia.title, "Corvane Mutual Insurance Society Limited",
                       ia.address, f"T: {ia.phone}", ia.email])
    tw = ThreadWriter(doc, r, width=72)
    tw.render([m], "single")
    return doc


# ---------------------------------------------------------------------------------------------
# TX015 – CLRFR040 batch sweep finding (2026-05-12)
# ---------------------------------------------------------------------------------------------

def tx015():
    fid = "TX015"
    r = _r(fid)
    doc = _doc(fid, 76)
    subj = "Compliance sampling – referrals missed by the batch sweep (scores 65–69)"
    t1 = clock(r, "11:10", "12:05")
    m1 = Msg("P037", ["P008", "P016"], "2026-05-12", t1, subj, cc=["P027", "P028", "P023"],
             importance="High", greeting="Niall, Graham,",
             body=[
                 P("Our sampling of fraud referrals since the threshold changed on 1 April has turned up a gap: we "
                   "found 37 claims scored 65–69 that the CLRFR040 batch sweep did not refer to SIU.",
                   facts=[F("37 claims scored 65–69 that the CLRFR040 batch sweep did not refer", key="tx15_37")]),
                 P("Claims scored on the online path (CLRFR030) were referred correctly, so this looks specific to "
                   "the batch sweep. All 37 were scored between 1 April and today.",
                   facts=[F("Claims scored on the online path (CLRFR030) were referred correctly",
                            "In INC-2026-0518 the online referral path CLRFR030 applied the threshold correctly; only "
                            "the CLRFR040 batch sweep missed referrals.", "general",
                            "INCIDENT:INC-2026-0518#root_cause")]),
                 "Given Circular 2026/04, I would like these referred manually as a priority and an incident "
                 "raised. Rachel – can SIU pick them up once Niall confirms?",
             ],
             signoff=pick(r, PH.SIGNOFF), signame="Ruth", sig="full")
    m2 = Msg("P008", ["P037"], "2026-05-12", later(r, t1, 15, 45), "RE: " + subj, cc=["P016", "P027", "P028", "P023"],
             greeting=pick(r, ["Thanks Ruth,", "Ruth,"]),
             body=[
                 P("Agreed. Please log it as a Sev2 incident with me as owner – it is now INC-2026-0518. Rachel, "
                   "please arrange manual referral of the 37 claims as soon as Ruth sends the list.",
                   facts=[F("log it as a Sev2 incident with me as owner – it is now INC-2026-0518",
                            "INC-2026-0518 was a Sev2 incident owned by Niall Brannigan.", "general",
                            "INCIDENT:INC-2026-0518#severity")]),
             ],
             signoff=None, signame="Niall", sig="short")
    m3 = Msg("P016", ["P037", "P008"], "2026-05-12", later(r, m2.time, 20, 75), "RE: " + subj,
             cc=["P027", "P028", "P023"], greeting=None,
             body=[
                 "Keith is looking at CLRFR040 now. First look suggests the batch sweep is not picking up the "
                 "threshold from CLR.T_PARAM, whereas the online program is. We will confirm the root cause and "
                 "raise a ticket for the fix.",
             ],
             signoff=pick(r, PH.SIGNOFF_SHORT), signame="Graham", sig="short")
    m4 = Msg("P037", ["P008", "P016", "P028"], "2026-05-12", later(r, m3.time, 15, 60), "RE: " + subj,
             cc=["P027", "P023"], greeting=None,
             body=["Thanks both. Rachel, the list of claim references is in the Compliance folder you have access "
                   "to – not attached here for data protection reasons."],
             signoff=None, signame="Ruth", sig="none", disclaimer=False)
    tw = ThreadWriter(doc, r, width=76)
    tw.render([m1, m2, m3, m4], "archive")
    return doc


# ---------------------------------------------------------------------------------------------
# TX016 – Tier-3 review cadence 14 days from 2026-07-01
# ---------------------------------------------------------------------------------------------

def tx016():
    fid = "TX016"
    r = _r(fid)
    doc = _doc(fid, 72)
    subj = "Tier-3 reserve review cadence from 1 July"
    m1 = Msg("P011", ["P009"], "2026-06-11", clock(r, "14:00", "16:30"), subj,
             greeting=pick(r, ["Hi Lena,", "Lena,"]),
             body=[
                 "I have had questions from the Leeds team leaders about the change to Tier-3 reserve reviews "
                 "agreed at the Reserving Committee on Tuesday. Before I brief them, can you confirm the new "
                 "interval and when it starts?",
             ],
             signoff=pick(r, PH.SIGNOFF_SHORT), signame="Rob", sig="short")
    m2 = Msg("P009", ["P011"], "2026-06-12", clock(r, "08:30", "10:00"), "RE: " + subj,
             cc=["P030", "P041", "P023"], greeting=pick(r, ["Hi Rob,", "Rob,", "Morning Rob,"]),
             body=[
                 P("Confirmed: from 1 July 2026, reserves on Tier-3 claims must be reviewed at least every 14 days "
                   "(BR-RSV-007 v3, approved by the Reserving Committee on 9 June).",
                   facts=[F("from 1 July 2026, reserves on Tier-3 claims must be reviewed at least every 14 days",
                            key="tx16_14d")]),
                 P("Until 30 June the current 21-day cadence still applies.",
                   facts=[F("Until 30 June the current 21-day cadence still applies",
                            "BR-RSV-007 v2 (21-day Tier-3 review cadence) applied until 2026-06-30.", "temporal",
                            "RULE:BR-RSV-007@v2#parameters.review_days")]),
                 P("Daniel and Keith are copied because the rule is implemented in both reserve-engine and CLARA "
                   "(CLRRS110 and CLRRS120), so both need the new interval from 1 July.",
                   facts=[F("implemented in both reserve-engine and CLARA (CLRRS110 and CLRRS120)",
                            "BR-RSV-007 is implemented in reserve-engine and in CLARA programs CLRRS110 and CLRRS120.",
                            "general", "RULE:BR-RSV-007#implemented_in")]),
                 "Kirsty's team will feel this most, so I have copied her too.",
             ],
             signoff=pick(r, PH.SIGNOFF), signame="Lena", sig="full")
    m3 = Msg("P041", ["P009"], "2026-06-12", later(r, m2.time, 30, 120), "RE: " + subj, cc=["P011", "P030", "P023"],
             greeting=None,
             body=["Thanks Lena – noted. We will take the configuration change through CAB before 1 July and "
                   "confirm once it is in."],
             signoff=None, signame="Daniel", sig="short")
    m4 = Msg("P011", ["P009", "P041"], "2026-06-12", later(r, m3.time, 20, 90), "RE: " + subj, cc=["P030", "P023"],
             greeting=None, body=[pick(r, ["Thanks both – I will brief the team leaders this afternoon.",
                                           "Perfect, thanks both. Briefing the team leaders today."])],
             signoff=None, signame="Rob", sig="none", disclaimer=False)
    tw = ThreadWriter(doc, r, width=72)
    tw.render([m1, m2, m3, m4], "mbox")
    return doc


# ---------------------------------------------------------------------------------------------
# TX017 – Wave 2 freeze window (2026-10-09)
# ---------------------------------------------------------------------------------------------

def tx017():
    fid = "TX017"
    r = _r(fid)
    doc = _doc(fid, 76)
    subj = "Wave 2 cut-over – confirmed date and freeze window"
    dl = "Wave 2 cut-over stakeholders <skerry.wave2@corvane-mutual.example>"
    t1 = clock(r, "09:20", "11:10")
    m1 = Msg("P048", [dl, "P016", "P026", "P032", "P031", "P017", "P012"], "2026-10-09", t1, subj,
             cc=["P004", "P047"], greeting=pick(r, ["All,", "Hi all,", "Dear all,"]),
             body=[
                 P("Following yesterday's Steering Committee, the Wave 2 cut-over date is confirmed as Monday "
                   "15 February 2027.",
                   facts=[F("the Wave 2 cut-over date is confirmed as Monday 15 February 2027",
                            "The Wave 2 cut-over date was confirmed as 2027-02-15 at the Steering Committee of 2026-10-08.",
                            "needle", "DECISION:DEC-011")]),
                 P("The freeze runs from 18:00 on Friday 12 February 2027 to 06:00 on Monday 15 February 2027.",
                   facts=[F("The freeze runs from 18:00 on Friday 12 February 2027 to 06:00 on Monday 15 February 2027",
                            key="tx17_freeze")]),
                 P("Scope: UK home, commercial and liability, plus Norway and Sweden (PRD-HOM-UK, PRD-COM-UK, "
                   "PRD-LIA-UK, PRD-MOT-NO, PRD-HOM-NO, PRD-MOT-SE, PRD-HOM-SE).",
                   facts=[F("PRD-HOM-UK, PRD-COM-UK, PRD-LIA-UK, PRD-MOT-NO, PRD-HOM-NO, PRD-MOT-SE, PRD-HOM-SE",
                            "Wave 2 covers PRD-HOM-UK, PRD-COM-UK, PRD-LIA-UK, PRD-MOT-NO, PRD-HOM-NO, PRD-MOT-SE and "
                            "PRD-HOM-SE.", "general", "WAVE:MW-2#scope")]),
                 "During the freeze nothing goes into CLARA or Claims Hub production other than the cut-over "
                 "itself. Please put the window in your team calendars now; detailed runbook timings will follow "
                 "from the cut-over planning sessions.",
             ],
             signoff=pick(r, ["Thanks,", "Regards,", "Best regards,"]), signame="Arjun", sig="full")
    m2 = Msg("P026", ["P048"], "2026-10-09", later(r, t1, 25, 90), "RE: " + subj, cc=["P016"],
             greeting=pick(r, ["Thanks Arjun,", "Arjun,"]),
             body=["I will align the CLARA batch schedule to the freeze and send a draft for review."],
             signoff=None, signame="Sunita", sig="short")
    m3 = Msg("P032", ["P048"], "2026-10-09", later(r, m2.time, 10, 80), "RE: " + subj, cc=["P016", "P026"],
             greeting=None, body=["Noted – I will block the window in the CAB change calendar."],
             signoff=None, signame="Neil", sig="short")
    m4 = Msg("P012", ["P048"], "2026-10-09", later(r, m3.time, 30, 140), "RE: " + subj, cc=["P017"],
             greeting=None,
             body=["Thanks – I will make sure the Oslo and Stockholm teams are briefed. We will need handler cover "
                   "planned for the Monday."],
             signoff=pick(r, PH.SIGNOFF_SHORT), signame="Mette", sig="short")
    tw = ThreadWriter(doc, r, width=76)
    tw.render([m1, m2, m3, m4], "outlook")
    return doc


# ---------------------------------------------------------------------------------------------
# TX018 – DOCSTOR becomes Evidence Vault (2025-10-27)
# ---------------------------------------------------------------------------------------------

def tx018():
    fid = "TX018"
    r = _r(fid)
    doc = _doc(fid, 74)
    m = Msg("P032", ["All Claims and Technology staff <claims-tech.all@corvane-mutual.example>"], "2025-10-27",
            clock(r, "08:45", "10:00"), "DOCSTOR becomes Evidence Vault on 3 November 2025",
            greeting=pick(r, ["Dear colleagues,", "Dear all,"]),
            body=[
                P("On Monday 3 November 2025 our document and image store, DOCSTOR, will be renamed Evidence Vault.",
                  facts=[F("DOCSTOR, will be renamed Evidence Vault", key="tx18_docstor",
                           statement="Body: on Monday 2025-11-03 DOCSTOR will be renamed Evidence Vault.")]),
                P("The rename goes live on the same day as the Claims Hub MVP. It is a change of name: the "
                  "documents, photos and letters themselves are unaffected.",
                  facts=[F("same day as the Claims Hub MVP",
                           "The Claims Hub MVP went live on 2025-11-03, the same day DOCSTOR was renamed Evidence Vault.",
                           "general", "EVENT:EV-020")]),
                P("The work is tracked under CHUB-276.",
                  facts=[F("tracked under CHUB-276", "The DOCSTOR to Evidence Vault rename was tracked under CHUB-276.",
                           "general", "SYSTEM:SYS05#renames")]),
                "If you maintain procedures, templates or training material that mention DOCSTOR, please update "
                "them when you next review them.",
                pick(r, PH.CLOSE_OFFER),
            ],
            signoff=pick(r, PH.SIGNOFF), signame="Neil", sig="full")
    tw = ThreadWriter(doc, r, width=74)
    tw.render([m], "single")
    # subject-line fact (line 5 of the RFC header block)
    for i, ln in enumerate(doc.lines, 1):
        if ln.startswith("Subject: "):
            doc.place((i, i), "tx18_docstor", "DOCSTOR becomes Evidence Vault on 3 November 2025",
                      statement="Subject line: DOCSTOR becomes Evidence Vault on 2025-11-03.")
            break
    return doc


# ---------------------------------------------------------------------------------------------
# TX019 – large loss notification to ReCede (2026-08-03, exclusive)
# ---------------------------------------------------------------------------------------------

def tx019():
    fid = "TX019"
    r = _r(fid)
    doc = _doc(fid, 74)
    subj = "Large loss notification – ReCede"
    t1 = clock(r, "15:05", "15:50")
    m1 = Msg("P038", ["P030", "P009"], "2026-08-03", t1, subj,
             cc=["Reinsurance team <reinsurance@corvane-mutual.example>"],
             greeting="Kirsty, Lena,",
             body=[
                 P("The reserve on claim CLM-UK-2026-207731 moved by £310,000 today. As the movement exceeds the LLNT "
                   "(£250,000), I notified ReCede within 24 hours – the notification went a few hours after the "
                   "movement was booked.",
                   facts=[F("The reserve on claim CLM-UK-2026-207731 moved by £310,000 today", key="tx19_llnt"),
                          F("exceeds the LLNT (£250,000), I notified ReCede within 24 hours",
                            "Reserve movements above the LLNT of £250,000 must be notified to ReCede within 24 hours "
                            "(BR-RSV-011 v2).", "use_of_definition", "RULE:BR-RSV-011@v2#parameters.threshold_gbp")]),
                 "Kirsty – please keep me posted on further movements on this file so I can update the bordereaux.",
             ],
             signoff=pick(r, PH.SIGNOFF), signame="Per", sig="full")
    m2 = Msg("P030", ["P038"], "2026-08-03", later(r, t1, 20, 70), "RE: " + subj, cc=["P009"],
             greeting=pick(r, ["Thanks Per,", "Per,"]),
             body=["Will do. The file sits with my team; I will flag any further change to you the same day."],
             signoff=None, signame="Kirsty", sig="short")
    m3 = Msg("P009", ["P038"], "2026-08-03", later(r, m2.time, 15, 60), "RE: " + subj, cc=["P030"],
             greeting=None,
             body=["Thanks Per – noted for the Reserving Committee large-loss summary."],
             signoff=None, signame="Lena", sig="short")
    tw = ThreadWriter(doc, r, width=74)
    tw.render([m1, m2, m3], "archive")
    return doc


# ---------------------------------------------------------------------------------------------
# TX020 – FR1 Q3 preparation (2026-10-06): 'Bjorn Aasheim' (ASCII)
# ---------------------------------------------------------------------------------------------

def tx020():
    fid = "TX020"
    r = _r(fid)
    doc = _doc(fid, 74)
    subj = "FR1 Q3 2026 – preparation and timetable"
    ba = person("P020", "2026-10-06")
    t1 = clock(r, "08:40", "10:20")
    m1 = Msg("P020", ["P037"], "2026-10-06", t1, subj,
             cc=["P008", "Regulatory Reporting <regulatory.reporting@corvane-mutual.example>"],
             display_name="Bjorn Aasheim", greeting="Ruth,",
             body=[
                 P("We have started preparing the Q3 2026 FR1 return. The draft extract shows 1,530 referrals for "
                   "the quarter (July to September).",
                   facts=[F("The draft extract shows 1,530 referrals for the quarter",
                            "The Q3 2026 NISA-FR1 return covers 1,530 fraud referrals.", "needle",
                            "REPORT:NISA-FR1#submissions.2026Q3.referrals")]),
                 P("The return is due by 30 October 2026. I would like to get the draft to you for review in the "
                   "week of 19 October so there is time for sign-off.",
                   facts=[F("The return is due by 30 October 2026",
                            "The 2026Q3 NISA-FR1 return was due by 2026-10-30.", "general",
                            "REPORT:NISA-FR1#submissions.2026Q3.due")]),
                 P("As for Q2, the referral data comes from CLARA through the CLX-IF-033 extract into the NISA "
                   "Reporting Hub. This is the first return covering a period after the Wave 1 cut-over, so we "
                   "will add an extra reconciliation check on motor referrals.",
                   facts=[F("the referral data comes from CLARA through the CLX-IF-033 extract into the NISA Reporting Hub",
                            "The NISA-FR1 return is fed by interface CLX-IF-033 from CLARA to the NISA Reporting Hub.",
                            "general", "REPORT:NISA-FR1#source_interfaces")]),
             ],
             signoff=pick(r, ["Best regards,", "Regards,", "Thanks,"]), signame="Bjorn", sig="custom",
             sig_lines=["", "Bjorn Aasheim", ba.title, "Corvane Mutual Norge – Oslo", ba.address, ba.phone, ba.email],
             sig_facts=[F("Bjorn Aasheim", key="tx20_bjorn",
                          notes="ASCII spelling of Bjørn Aasheim (P020), Regulatory Reporting Manager; the body states "
                                "the 1,530 referrals.")])
    m2 = Msg("P037", ["P020"], "2026-10-06", later(r, t1, 30, 140), "RE: " + subj, cc=["P008"],
             greeting=pick(r, ["Thanks Bjørn,", "Bjørn,", "Hi Bjørn,"]),
             body=["The week of 19 October works. I will hold time for sign-off the following week."],
             signoff=None, signame="Ruth", sig="short")
    m3 = Msg("P008", ["P020", "P037"], "2026-10-06", later(r, m2.time, 20, 120), "RE: " + subj,
             greeting=None,
             body=["Thanks both – shout if SIU needs to confirm any referral outcomes before the draft goes over."],
             signoff=None, signame="Niall", sig="short")
    tw = ThreadWriter(doc, r, width=74)
    tw.render([m1, m2, m3], "outlook")
    return doc


EMAILS = {
    "TX007": tx007, "TX008": tx008, "TX009": tx009, "TX010": tx010, "TX011": tx011, "TX012": tx012,
    "TX013": tx013, "TX014": tx014, "TX015": tx015, "TX016": tx016, "TX017": tx017, "TX018": tx018,
    "TX019": tx019, "TX020": tx020,
}

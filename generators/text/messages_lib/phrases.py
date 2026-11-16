"""Phrase banks. Nothing here states a world fact: these are connective, procedural and
courtesy phrases only (no thresholds, owners, dates, system links or table links).
"""

GREET_FORMAL = ["Dear all,", "Dear colleagues,", "Good morning all,", "Hello all,", "All,"]
GREET_INFORMAL = ["Hi all,", "Hi everyone,", "Morning all,", "Afternoon all,", "Hi team,", "Hello both,"]

def greet_name(first: str, r) -> str:
    return r.choice([f"Hi {first},", f"{first},", f"Hello {first},", f"Dear {first},", f"Morning {first},",
                     f"Thanks {first},"])

SIGNOFF = ["Kind regards,", "Best regards,", "Regards,", "Many thanks,", "Thanks,", "Thanks and regards,",
           "Best wishes,", "With thanks,", "All the best,"]
SIGNOFF_SHORT = ["Thanks,", "Cheers,", "Thanks again,", "Best,", "Ta,", "Many thanks,"]

ACK = [
    "Thanks – noted.",
    "Received, thank you.",
    "Thanks for the quick turnaround on this.",
    "Noted, thanks for flagging.",
    "Thanks, that is clear.",
    "Understood – thanks for confirming.",
    "Thanks, this is helpful.",
    "Great, thank you.",
    "Thanks for pulling this together.",
    "Appreciated – thanks.",
]

CLOSE_OFFER = [
    "Happy to pick this up on a call if that is easier.",
    "Shout if anything here does not look right.",
    "Let me know if you need anything else from me.",
    "Give me a ring if you want to talk it through.",
    "I can walk anyone through the detail if useful.",
    "Any questions, just let me know.",
    "Please come back to me with any comments.",
    "I will keep you posted as things move.",
    "Grateful if you could reply by return if you see a problem.",
    "Do say if I have missed anyone who should be on this.",
]

FOLLOW_UP = [
    "I will circulate an update once we know more.",
    "I will add this to the agenda for our next catch-up.",
    "I will confirm in writing once it is done.",
    "I will make sure the team is briefed today.",
    "We will pick up any loose ends in the usual weekly call.",
    "I will update the tracker so we have a record.",
    "I will send round a short note once this is closed off.",
]

MOBILE_FOOTER = ["Sent from my phone", "Sent from my mobile – please excuse brevity", "Sent from mobile"]

CORVANE_DISCLAIMERS = [
    ("This e-mail and any attachments are confidential and intended solely for the named addressee(s). "
     "If you have received it in error please notify the sender and delete it. Corvane Mutual Insurance "
     "Society Limited is supervised by the National Insurance Supervisory Authority (NISA-FRN 40417). "
     "Registered office: Corvane House, 14 Tallowgate, London EC3N 9ZZ."),
    ("CONFIDENTIALITY: The information in this message is private to Corvane Mutual and the intended "
     "recipient(s). If you are not an intended recipient, please tell the sender and delete the message; "
     "do not copy or forward it. Corvane Mutual Insurance Society Limited, Corvane House, 14 Tallowgate, "
     "London EC3N 9ZZ. Supervised by NISA (NISA-FRN 40417)."),
    ("Corvane Mutual Insurance Society Limited | Corvane House, 14 Tallowgate, London EC3N 9ZZ | "
     "NISA-FRN 40417. This message may contain confidential information. If it reached you by mistake, "
     "please let the sender know and remove it from your system."),
]

CORVANE_NORDIC_DISCLAIMERS = [
    ("Denne e-posten kan inneholde konfidensiell informasjon. / This e-mail may contain confidential "
     "information. If you are not the intended recipient please notify the sender and delete it. "
     "Corvane Mutual Insurance Society Limited (branch office), supervised by NISA (NISA-FRN 40417)."),
    ("This message is intended only for the addressee(s) and may contain confidential information. "
     "Corvane Mutual Insurance Society Limited – Nordic branches. Supervised by NISA (NISA-FRN 40417)."),
]

IBM_DISCLAIMERS = [
    ("IBM Consulting – Programme Skerry delivery team. This message and any attachments are intended "
     "for the named recipients only and may contain confidential client information."),
    ("Delivered by the IBM Consulting team working on Programme Skerry for Corvane Mutual. Please do not "
     "forward outside the programme distribution without the sender's agreement."),
]

VENDOR_DISCLAIMER = ("This e-mail is confidential and intended for the addressee only. If you have "
                     "received it in error please delete it and inform the sender.")

PRINT_BANNERS = [
    "Corvane Mutual mail archive – conversation export",
    "Exported conversation (mail archive)",
    "Mail archive export – thread view (oldest first)",
]

# --- minutes / meeting records -------------------------------------------------------------

OPENING = [
    "The chair welcomed attendees and confirmed the meeting was quorate.",
    "The chair opened the meeting, welcomed attendees and confirmed quorum.",
    "The chair welcomed everyone, noted apologies and confirmed the meeting could proceed.",
    "Following introductions, the chair confirmed the agenda and that the meeting was quorate.",
]
DECLARATIONS = [
    "No declarations of interest were made.",
    "No conflicts of interest were declared.",
    "Attendees confirmed they had no interests to declare against the agenda.",
]
PREV_MINUTES = [
    "The minutes of the previous meeting were accepted as an accurate record.",
    "The previous minutes were approved without amendment.",
    "The minutes of the last meeting were agreed as a true record.",
    "The record of the previous meeting was approved; no matters arising beyond the action log.",
]
ACTIONS_REVIEWED = [
    "Open actions were reviewed; status is shown in the action log at the end of these minutes.",
    "The action log was reviewed. Closed items have been removed; carried-forward items are listed below.",
    "Outstanding actions were walked through and updated in the log.",
]
DISCUSSION_LEADS = [
    "In discussion the following points were made:",
    "Points raised in discussion:",
    "The group discussed the item. Key points:",
    "Discussion covered the following:",
]
GENERIC_POINTS = [
    "It was noted that the outcome should be recorded in the programme decision log.",
    "Attendees agreed that any residual questions should be raised through the usual channel rather than reopened here.",
    "The chair asked that management information is reviewed at the next meeting to confirm things are working as intended.",
    "Attendees highlighted the need to keep audit evidence of approvals.",
    "Members asked that the update is shared with team leaders so the message is consistent across sites.",
    "The chair thanked the team for the clarity of the paper.",
    "It was agreed that any exceptions found should be reported to the chair between meetings rather than held for the next session.",
]
IMPL_POINTS = [
    "Attendees asked that the change is reflected in the relevant procedure documents before it takes effect.",
    "It was agreed that communications to affected teams should be issued in plain language and in good time.",
    "The group noted the dependency on testing being completed and signed off before the change goes live.",
    "Members asked for the implementation plan to include a clear fallback position.",
    "It was agreed that training material for handlers would be updated alongside the system change.",
    "The group asked that customer-facing wording is reviewed by Compliance before use.",
]
AOB = [
    "No other business was raised.",
    "There was no other business.",
    "No items of other business were tabled.",
]
CLOSE = [
    "The chair thanked attendees and closed the meeting at {end}.",
    "There being no further business the meeting closed at {end}.",
    "The meeting closed at {end}.",
]

# --- filler (status reports, team notes) ----------------------------------------------------

STATUS_WORDS = ["On track", "On track", "On track", "Watch", "On track", "Watch"]
RAG = {"On track": "Green", "Watch": "Amber"}

PROGRESS_ITEMS = [
    "Backlog refinement completed for the next sprint; stories sized and accepted by the product owner.",
    "Sprint review held; demo recorded and shared on the programme site.",
    "Defect triage running twice weekly; no blockers raised to the programme this week.",
    "Regression pack executed on the integration environment; results shared with the squads.",
    "Cut-over runbook walkthrough held with operations; comments being incorporated.",
    "Data quality review session held with business data owners.",
    "Training material updated following feedback from the floor-walker sessions.",
    "Security review comments addressed and closed with the reviewer.",
    "Release notes drafted and circulated for review.",
    "Stakeholder briefing pack refreshed for the next steering pack.",
    "Environment booking calendar updated for the coming fortnight.",
    "Lessons-learned log reviewed and two items converted into backlog stories.",
    "Knowledge-transfer sessions continued between the IBM team and Corvane staff.",
    "Hypercare call held daily with operations; no new themes this week.",
    "Test evidence filed for audit in the programme repository.",
    "Dependency review held with the integration team; no changes to dates.",
    "Accessibility review of the handler screens completed; minor fixes logged.",
    "Performance test plan agreed with the platform team.",
    "Business readiness checklist reviewed with operations managers.",
    "Change impact assessment updated for the affected teams.",
]
NEXT_ITEMS = [
    "Continue sprint delivery against the agreed scope.",
    "Complete outstanding test evidence and file for sign-off.",
    "Run the next business readiness check-in with operations.",
    "Prepare inputs for the monthly steering pack.",
    "Review the RAID log with workstream leads.",
    "Refresh the training schedule for the next cohort.",
    "Hold the fortnightly dependency review.",
    "Update the cut-over plan with comments received.",
    "Close remaining low-priority defects where possible.",
    "Confirm attendance for the next planning session.",
]
RISK_ITEMS = [
    ("Key-person dependency on a small number of mainframe specialists.", "Knowledge-transfer sessions scheduled; pairing in place."),
    ("Competing demands on business SMEs during month-end.", "Workshops scheduled outside close week where possible."),
    ("Environment contention between squads.", "Shared booking calendar and daily environment stand-up."),
    ("Late changes to scope could affect test completion.", "Scope changes go through the change control process."),
    ("Annual leave over the holiday period reduces capacity.", "Leave plan reviewed; cover arrangements agreed."),
    ("Handler adoption of new screens slower than planned.", "Additional floor-walker support and short refresher sessions."),
    ("Test data preparation taking longer than expected.", "Data preparation tasks prioritised in the next sprint."),
]
TEAM_NOTE_ITEMS = [
    "Reminder to keep timesheets up to date by Friday lunchtime.",
    "Please book leave in the shared calendar so cover can be planned.",
    "The team lunch moved to the following Thursday because of room availability.",
    "New starters: buddy assignments have been made – see the onboarding checklist.",
    "Desk moves on the third floor are now complete; thanks for your patience.",
    "The coffee machine on the fourth floor has finally been repaired.",
    "Please make sure meeting rooms are released if a meeting is cancelled.",
    "Fire drill expected later this month – follow the wardens' instructions.",
    "Thanks to everyone who joined the charity quiz – a good amount was raised.",
    "Mandatory training reminders have gone out; please complete before the deadline in the system.",
    "If you need access to a new environment, raise it through the service desk form.",
    "Please use the shared mailbox for team requests rather than individual inboxes.",
]
ROOMS = ["Tallowgate Room, Corvane House", "Room 3.07, Corvane House", "Room 4.12, Corvane House",
         "Wharfedge Room, Aire Point (Leeds)", "Aire Room, Aire Point (Leeds)", "Room 2.14, Corvane House",
         "Quayhead Room, Bristol", "Fjordporten meeting room, Oslo"]
DIAL_IN = ["with video dial-in", "hybrid (room and video)", "video call", "in person and on video"]

TEAM_WORK_ITEMS = [
    "Weekly file reviews completed for every team member.",
    "Quality checks carried out on a sample of closed files; feedback shared one to one.",
    "Daily huddles held; no blockers escalated this week.",
    "Procedure documents reviewed and minor wording updates sent for approval.",
    "Refresher training delivered to new joiners.",
    "Cover rota agreed for the coming month.",
    "Colleagues supported other teams with Claims Hub questions during busy periods.",
    "Shared mailbox kept within the agreed response time.",
    "Work allocation rebalanced after two colleagues returned from leave.",
    "Team objectives reviewed at the monthly one-to-ones.",
]
TEAM_WIP = [
    "Updating the team's desk instructions to reflect recent system changes.",
    "Collecting examples for the next lessons-learned session.",
    "Reviewing the induction checklist with the most recent joiners.",
    "Preparing input for the next management information pack.",
    "Tidying up the shared folder structure.",
    "Agreeing a consistent template for handover notes.",
]
TEAM_QA = [
    ("Who do we contact for access requests?", "Use the service desk form; the team lead approves."),
    ("Where are the latest procedures kept?", "On the team page of the intranet – check the version date."),
    ("Can we change the huddle time?", "Agreed to try 09:15 for the next two weeks."),
    ("Is there a template for escalation notes?", "Yes – in the shared folder under Templates."),
]

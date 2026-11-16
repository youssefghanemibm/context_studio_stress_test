"""Phrase banks for the claims-handling manuals (LD001 v7.2 and LD012 v6.1).

Everything here is deliberately *procedural* prose: it never states a threshold, time limit,
owner, date, system link or program-table link. Those come only from the world model, via the
content modules. Variety comes from slot templates x topic packs x a seeded rng, and a
per-document de-duplication set so the same sentence never appears twice in one manual.
"""
from __future__ import annotations

import random
import re

# ---------------------------------------------------------------------------------------------
# Styles: terminology per manual version (glossary.yaml: LD uses 'loss adjuster' for external
# assessors, 'case reserve', 'referral to SIU'; v6.1 says 'case handler' and 'FRAUDNET score').
# ---------------------------------------------------------------------------------------------

STYLE_V72 = {
    "handler": "Claims Handler", "handlers": "Claims Handlers",
    "assessor": "Claims Assessor", "ext_assessor": "loss adjuster", "ext_assessors": "loss adjusters",
    "tl": "Team Leader", "cm": "Claims Manager", "customer": "customer", "customers": "customers",
    "firm": "Corvane", "score": "Sentinel score", "fraudref": "referral to SIU", "siu": "Counter-Fraud & SIU", "Cf": "Counter-fraud",
    "notes": "claim notes", "record": "claim record", "system": "the claims system",
    "mlc": "Major & Complex Loss", "recoveries": "Recoveries & Subrogation",
}
STYLE_V61 = {
    "handler": "case handler", "handlers": "case handlers",
    "assessor": "loss adjuster", "ext_assessor": "loss adjuster", "ext_assessors": "loss adjusters",
    "tl": "Team Leader", "cm": "Claims Manager", "customer": "claimant", "customers": "claimants",
    "firm": "the Society", "score": "FRAUDNET score", "fraudref": "fraud referral", "siu": "the SIU", "Cf": "Anti-fraud",
    "notes": "file notes", "record": "claim file", "system": "CLARA",
    "mlc": "Major & Complex Loss", "recoveries": "the Recoveries team",
}

# ---------------------------------------------------------------------------------------------
# Topic packs. Placeholders in braces are style keys.
# ---------------------------------------------------------------------------------------------

COMMON = {
    "actors": ["the {handler}", "the {tl}", "the {cm}", "the handling team"],
    "escalation": ["the {tl}", "the {cm}", "the {tl} or {cm}", "the next level of authority"],
    "milestones": ["the claim moves to the next stage", "any payment is authorised", "the file is closed",
                   "the next diary review", "a decision is communicated to the {customer}",
                   "the claim is handed to another team"],
    "rationales": ["a complete file protects the {customer} and the {firm} if the decision is later challenged",
                   "decisions that cannot be evidenced are treated as not having been made",
                   "consistent handling is what regulators and auditors test",
                   "late corrections are costly and confuse the {customer}",
                   "a clear audit trail makes peer review and complaint handling quicker",
                   "it keeps the case reserve and the claim narrative in step",
                   "it allows another handler to pick up the file without starting again"],
    "qa": ["each decision is linked to the evidence relied on",
           "the {notes} explain the reasoning and not just the outcome",
           "the {customer} was told about each decision that affects them",
           "authority was held, or obtained, before each decision was taken",
           "diary dates were set and honoured",
           "letters issued match the decision recorded in the {notes}",
           "each telephone call is summarised in the {notes} on the day it took place",
           "any delay was explained to the {customer} at the time",
           "the reason for the current case reserve is recorded",
           "the next action and its owner are clear from the {record}",
           "documents relied on are attached to the {record} and not held locally",
           "any departure from standard process was approved and explained"],
}

TOPICS: dict[str, dict] = {}

TOPICS["governance"] = {
    "actors": ["the process owner", "each Head of function", "the manual owner", "the {cm}", "the {tl}"],
    "objects": ["the authority framework", "the process documentation", "the control evidence", "the role description",
                "the delegated authority record", "the RACI assignment", "the change log for this manual"],
    "actions": ["confirm that each delegated authority is recorded against a named role",
                "review the RACI assignments when a team changes shape",
                "check that procedural changes are reflected in training material",
                "record any temporary delegation in writing with a clear end date",
                "make sure deputies know which decisions they may take",
                "escalate gaps in the control framework to the process owner"],
    "triggers": ["a team is restructured", "a new rule version is approved", "a role holder is absent for an extended period",
                 "an audit finding is raised against a process", "a procedure is found to be unclear in practice"],
    "conditions": ["a decision falls between two roles", "a delegated authority has lapsed",
                   "the accountable person is unavailable", "two procedures appear to conflict"],
    "risks": ["decisions being taken by someone without authority", "controls existing on paper but not in practice",
              "out-of-date procedures remaining in use", "unclear ownership when processes cross team boundaries"],
    "evidence": ["the signed delegation", "the control test record", "the training attendance log", "the approval record"],
    "custinfo": ["who is responsible for their claim", "how decisions about their claim are reviewed"],
    "sentences": [
        "Every procedure in this manual has a named process owner who is accountable for its design and for the evidence that it operates as written.",
        "Authority is attached to roles rather than to individuals, so it moves automatically when a person changes role.",
        "Where this manual and a local desk instruction differ, this manual prevails until the desk instruction has been withdrawn or re-approved.",
        "Process owners review their chapters at least whenever a governing rule changes, and confirm the review to the manual owner.",
        "Team Leaders are expected to brief changes to their teams before the effective date, not after it.",
        "The first line of defence owns the controls described here; Compliance and Internal Audit provide challenge and independent assurance.",
        "A handler who believes a procedure produces an unfair outcome for a customer should raise it with their Team Leader immediately.",
        "Exceptions granted under this manual are recorded centrally so that patterns can be identified and the procedure improved.",
    ],
}

TOPICS["customer"] = {
    "actors": ["the {handler}", "the Contact Centre adviser", "the {tl}", "the complaints handler"],
    "objects": ["the vulnerability indicator", "the communication preference", "the support plan", "the complaint record",
                "the agreed contact schedule", "the accessible-format request", "the interpreter booking"],
    "actions": ["ask how the {customer} prefers to be contacted", "check whether the {customer} needs extra support",
                "agree a realistic contact schedule with the {customer}", "explain the next steps without jargon",
                "record any adjustment agreed with the {customer}", "confirm that the {customer} understood the explanation",
                "offer a call-back at a time that suits the {customer}", "update the support plan when circumstances change"],
    "triggers": ["the {customer} discloses a health condition", "a bereavement is mentioned", "the {customer} expresses dissatisfaction",
                 "the {customer} asks for information in another format", "a third party contacts us on the {customer}'s behalf"],
    "conditions": ["the {customer} appears confused about the process", "a representative is acting for the {customer}",
                   "the {customer} has missed several contacts", "the claim is causing obvious hardship"],
    "risks": ["vulnerable customers being treated in the same way as everyone else", "complaints not being recognised as complaints",
              "customers repeating their story to several people", "adjustments being agreed but not recorded"],
    "evidence": ["the record of the adjustment agreed", "the consent to share information", "the summary of the conversation",
                 "the complaint acknowledgement"],
    "custinfo": ["what will happen next and when", "who their point of contact is", "how to complain if they are unhappy",
                 "what support is available to them", "why we need the information we are asking for"],
    "sentences": [
        "Vulnerability is often temporary: a customer who was coping at notification may need support later in the claim, and the reverse is also true.",
        "Handlers should listen for indicators of vulnerability rather than wait for the customer to use particular words.",
        "Where a customer has asked for a particular contact method, use it consistently unless they change their preference.",
        "Expressions of dissatisfaction are treated as complaints unless the customer is clear that they do not want to complain.",
        "A good explanation tells the customer what has been decided, why, and what they can do if they disagree.",
        "Information about a customer's health or circumstances is recorded only to the extent needed to support them.",
        "Handlers should avoid passing a vulnerable customer between teams; a single point of contact is preferred.",
        "When a representative acts for the customer, the authority to deal with them is checked and recorded first.",
        "Customers in financial difficulty are told about interim payments where cover has been confirmed.",
    ],
}

TOPICS["fnol"] = {
    "actors": ["the Contact Centre adviser", "the {handler}", "the FNOL team", "the digital intake team"],
    "objects": ["the notification", "the loss description", "the policy snapshot", "the date of loss", "the loss location",
                "the third-party details", "the emergency make-safe request", "the claim number"],
    "actions": ["confirm the identity of the caller and their relationship to the policy",
                "capture the loss description in the {customer}'s own words",
                "check the cover dates against the date of loss", "ask whether anyone was injured",
                "find out whether emergency work is needed to make the property safe",
                "confirm the best contact number and preferred contact times",
                "explain how photos and documents can be sent in", "check for an existing claim on the same policy",
                "record whether the police or fire service attended"],
    "triggers": ["a notification is received through a broker", "a telematics crash alert arrives",
                 "the caller is not the policyholder", "the customer reports several losses at once",
                 "the notification arrives outside normal hours"],
    "conditions": ["the policy cannot be found", "the date of loss is uncertain", "the caller cannot confirm security details",
                   "the loss appears to fall outside the period of cover", "the customer is distressed"],
    "risks": ["duplicate claims being opened", "the wrong peril being recorded", "contact details being captured incorrectly",
              "injuries being missed at first contact", "the customer being left unsure what happens next"],
    "evidence": ["the call recording reference", "the portal submission record", "the broker reference",
                 "the photo set uploaded by the {customer}", "the crash-alert record"],
    "custinfo": ["their claim number and how to quote it", "what happens next and who will contact them",
                 "how to send photos and documents", "what to do if the damage gets worse"],
    "sentences": [
        "The quality of the notification sets the course of the claim: most rework later in the lifecycle traces back to incomplete or inaccurate FNOL data.",
        "Advisers should resist the temptation to diagnose cover at first notification; the aim is to capture facts, not to decide the claim.",
        "Where the caller is a third party, record their details separately and do not disclose policy information to them.",
        "The loss description should say what happened, where, when and how the damage was discovered.",
        "Photos sent at notification are often the best evidence of the original damage and should never be discarded.",
        "If the customer mentions any injury, however minor it seems, record it; injury changes the routing of the claim.",
        "A notification that is withdrawn by the customer is still recorded, together with the reason given.",
        "Advisers should read back the key facts to the caller before ending the call.",
        "Digital notifications are reviewed for completeness in the same way as telephone notifications.",
        "Advisers should note anything the customer says about access to the property or the vehicle.",
        "Where the customer is unsure of the date of loss, record the best estimate and the reason for the uncertainty.",
        "Questions at notification should be open, so that the customer describes the loss rather than confirms a suggestion.",
        "Advisers should not promise outcomes, payment dates or repair dates at first notification.",
        "Where the customer reports damage that may get worse, the advice given to limit further damage is recorded.",
        "Notifications received on behalf of a deceased policyholder are handled with particular care and routed to an experienced handler.",
    ],
}

TOPICS["data"] = {
    "actors": ["the {handler}", "the FNOL team", "the data quality analyst", "the {tl}"],
    "objects": ["the mandatory data set", "the peril code", "the loss location", "the vehicle registration",
                "the broker reference", "the policy number", "the third-party record", "the free-text description"],
    "actions": ["complete every mandatory field before the claim number is issued",
                "use the code list rather than free text wherever a code exists",
                "correct a wrong peril code as soon as it is noticed and note why it changed",
                "avoid placeholder values in mandatory fields", "capture addresses in the structured fields provided",
                "keep personal data to what the claim actually needs"],
    "triggers": ["a data quality exception is reported", "a field is corrected after the claim number is issued",
                 "a new code is added to a code list", "migration reconciliation flags a mismatch"],
    "conditions": ["a mandatory value is genuinely unknown", "two sources give different values", "a code does not fit the loss"],
    "risks": ["placeholder values reaching management information", "free text hiding information that should be coded",
              "personal data being captured that the claim does not need", "corrections being made without an audit trail"],
    "evidence": ["the field history", "the data quality exception report", "the correction note"],
    "custinfo": ["why each item of information is needed"],
    "sentences": [
        "Structured data drives routing, reserving and reporting, so a wrong code at notification can affect every later stage.",
        "Free-text fields are for narrative, not for information that has its own field.",
        "Where a value is corrected, the original value is preserved in the field history; it is never overwritten silently.",
        "Data captured for one purpose should not be reused for an unrelated purpose without checking with Data Protection.",
        "Handlers should report recurring data problems to their Team Leader so that the cause can be fixed.",
        "Address and postcode fields are completed in the structured format because downstream geocoding depends on them.",
        "Test and training environments never contain live customer data.",
    ],
}

TOPICS["reserving"] = {
    "actors": ["the {handler}", "the {tl}", "the {cm}", "the Reserving team", "the reserving analyst"],
    "objects": ["the case reserve", "the indemnity reserve", "the expense reserve", "the reserve movement",
                "the reserve reason code", "the reserve history", "the estimate of outstanding cost", "the incurred position"],
    "actions": ["set the case reserve at the best estimate of the outstanding cost",
                "record a reason code with every reserve movement",
                "review the case reserve whenever new information changes the expected outcome",
                "avoid stepping the case reserve up in small increments when the likely outcome is already known",
                "separate indemnity, expense and legal elements of the reserve",
                "explain material reserve movements in the {notes}",
                "check that the reserve still reflects the latest assessor report"],
    "triggers": ["an assessor report is received", "liability is admitted or denied", "a payment is made",
                 "proceedings are issued", "a settlement offer is accepted", "the claim is reopened"],
    "conditions": ["the outcome is genuinely uncertain", "the estimate exceeds the handler's authority",
                   "the reserve has not moved for a long period", "a large movement is needed in one step"],
    "risks": ["reserves that lag behind the known facts", "reserve movements without reason codes",
              "optimistic reserves that later need large increases", "expected recoveries being netted off too early"],
    "evidence": ["the reserve rationale", "the movement history", "the assessor estimate", "the authority approval"],
    "custinfo": [],
    "sentences": [
        "A case reserve is the handler's best estimate of what remains to be paid on the claim; it is not a target and not a negotiating position.",
        "Reserves should move when the facts move, not when a diary date happens to fall due.",
        "Every reserve movement is attributable to a named person and carries a reason code, so that movements can be analysed later.",
        "Expected recoveries are not deducted from the case reserve; they are recorded separately until the money is received.",
        "Where the outcome is uncertain, the reserve reflects the most likely outcome, and the uncertainty is described in the notes.",
        "Large reserve movements are reviewed by the Team Leader even when they fall within the handler's authority.",
        "Reserving accuracy is measured by comparing reserves with final settlements, and the results are fed back to teams.",
        "The case reserve and the claim narrative should tell the same story; a reader of the file should understand why the reserve is what it is.",
        "Expense reserves are set for the costs that will actually be incurred, including loss adjuster and legal fees.",
        "Reserve history is part of the claim record and is never deleted or overwritten.",
        "A nil reserve on an open claim needs a reason, for example that all payments have been made and closure is pending.",
        "Where a claim involves several reserve types, each is reviewed on its own merits.",
        "Reserving decisions are made on the information available at the time and revisited as that information changes.",
        "The Reserving team uses case reserves as one input to its own estimates, so their quality matters beyond the individual claim.",
        "Handlers should avoid round-number reserves where a more precise estimate is available.",
        "When a reserve is reduced, the reason is recorded with the same care as when it is increased.",
        "Reserve movements made in error are reversed with a new movement, not by editing the original.",
    ],
}

TOPICS["largeloss"] = {
    "actors": ["Major & Complex Loss", "the {cm}", "the Reinsurance team", "the large loss handler", "the Claims Director"],
    "objects": ["the large loss report", "the reinsurance notification", "the strategy note", "the reserve position",
                "the recovery strategy", "the expert appointment", "the loss timeline"],
    "actions": ["prepare a strategy note setting out the issues, the experts appointed and the expected timetable",
                "keep the Reinsurance team informed of material developments", "agree the expert strategy early",
                "record each strategic decision and the person who made it", "review the case reserve after every material development",
                "consider recovery potential from the outset"],
    "triggers": ["a reserve movement is large enough to need notification", "a loss involves several policies",
                 "litigation is threatened", "media interest is likely", "a loss affects several countries"],
    "conditions": ["the facts are still emerging", "the loss involves several Corvane products",
                   "experts disagree on the cause of loss", "reinsurers ask for additional information"],
    "risks": ["late notification to reinsurers", "experts being appointed without clear instructions",
              "strategy decisions not being recorded", "duplicate handling across teams"],
    "evidence": ["the notification record", "the strategy note", "the expert instruction letter", "the reinsurer correspondence"],
    "custinfo": ["who is leading their claim and how often they will hear from us"],
    "sentences": [
        "Large and complex losses are handled by experienced staff with direct access to senior decision makers.",
        "The strategy note is a living document; it is updated whenever the strategy changes, not only at formal reviews.",
        "Reinsurers expect accurate and timely information, and late notification can put recoveries under the treaty at risk.",
        "Where several Corvane policies respond to the same event, one lead handler coordinates the response.",
        "Experts are instructed in writing, with clear terms of reference and an agreed fee basis.",
        "Senior management is briefed on losses that could attract media or regulatory attention.",
        "The handler should think about the end of the claim from the beginning: what will settlement look like and what evidence will it need?",
    ],
}

TOPICS["triage"] = {
    "actors": ["the triage team", "the {handler}", "the {tl}", "the triage workbench"],
    "objects": ["the tier", "the routing decision", "the pre-screen result", "the triage note", "the override reason",
                "the allocation queue", "the estimate band"],
    "actions": ["confirm the tier using the definitions in Chapter 2", "check the pre-screen result before routing",
                "record the reason for any manual override of the tier", "route the claim to the team that holds the skills it needs",
                "re-check the tier whenever the estimate changes materially", "note any open claim on the same policy"],
    "triggers": ["the estimate crosses a tier boundary", "new information reveals an injury", "the pre-screen result changes",
                 "storm volumes rise sharply", "a claim is transferred between teams"],
    "conditions": ["the estimate is unreliable", "the claim fits more than one routing rule", "the pre-screen is unavailable"],
    "risks": ["complex claims sitting in high-volume queues", "manual overrides without reasons",
              "claims being re-routed several times", "injury claims missing specialist handling"],
    "evidence": ["the triage note", "the override approval", "the routing history"],
    "custinfo": ["which team will handle their claim"],
    "sentences": [
        "Triage decides who handles the claim and how much attention it needs; getting it right early avoids hand-offs later.",
        "The tier is a judgement supported by rules, not a mechanical output; the triage team should challenge results that look wrong.",
        "Where a claim meets more than one routing rule, the more specialist route takes precedence.",
        "Routing history is retained, so the reason for each transfer can be reviewed.",
        "Triage notes should be short and factual and state the basis for the tier and the route chosen.",
        "During surge conditions, simplified routing applies, but injury claims are never simplified away from specialist teams.",
    ],
}

TOPICS["fasttrack"] = {
    "actors": ["the fast-track team", "the {handler}", "the {tl}"],
    "objects": ["the fast-track eligibility check", "the straight-through payment", "the fast-track queue", "the sample check"],
    "actions": ["confirm that every eligibility condition is met before fast-tracking",
                "remove a claim from fast-track as soon as any condition stops being met",
                "check the payee details before a straight-through payment", "sample fast-track settlements for quality"],
    "triggers": ["new information arrives after fast-tracking", "the customer disputes the amount", "a pre-screen result changes"],
    "conditions": ["the eligibility position is borderline", "the payee differs from the policyholder"],
    "risks": ["ineligible claims being paid straight through", "quality sampling being skipped in busy periods"],
    "evidence": ["the eligibility record", "the sample check result"],
    "custinfo": ["how quickly they can expect payment", "what to do if the settlement does not cover their loss"],
    "sentences": [
        "Fast-track handling exists to settle simple claims quickly and fairly; it is not a way of avoiding proper checks.",
        "A claim leaves the fast-track route the moment it stops meeting the eligibility conditions.",
        "Quality sampling of fast-track settlements continues in every month, including during surge events.",
        "Customers whose claims are fast-tracked are told how the amount was calculated.",
    ],
}

TOPICS["assessment"] = {
    "actors": ["the {assessor}", "the {ext_assessor}", "the {handler}", "the Claims Assessment team", "the panel manager"],
    "objects": ["the instruction", "the assessor report", "the scope of works", "the estimate", "the photo record",
                "the coverage recommendation", "the conflict-of-interest declaration"],
    "actions": ["issue a clear written instruction that states what the assessor is asked to do",
                "check the assessor report for completeness before relying on it",
                "challenge an estimate that is not supported by the photos or scope",
                "confirm that the assessor has no conflict of interest", "agree the scope of works with the {customer}",
                "chase an overdue report and record the reason for delay"],
    "triggers": ["an assessor report is received", "the estimate rises after inspection", "the {customer} disputes the scope",
                 "a panel firm reports a capacity problem", "the cause of loss is unclear"],
    "conditions": ["the report does not address cover", "the photos do not match the description",
                   "the assessor recommends specialist investigation", "the property is unsafe to enter"],
    "risks": ["instructions that do not say what is needed", "reports being accepted without review",
              "assessors being instructed on claims where they have a conflict", "scope creep that is never challenged"],
    "evidence": ["the written instruction", "the assessor report", "the photo record", "the conflict declaration"],
    "custinfo": ["when the assessor will contact them", "what the assessor will need to see", "what the assessor's role is"],
    "sentences": [
        "An instruction should say what has happened, what is already known, and what the assessor is being asked to establish.",
        "Assessor reports are evidence, not decisions; the coverage decision remains with the handler.",
        "The handler should read the whole report, including the photos, before relying on its recommendation.",
        "Panel performance is reviewed regularly, and handlers' feedback on report quality forms part of that review.",
        "Customers should know who the assessor is, why they are attending and what they will need to see.",
        "Desk assessment is appropriate only where the evidence available supports a reliable estimate without a visit.",
        "Where the assessor and the customer disagree about scope, the handler mediates and records the outcome.",
    ],
}

TOPICS["nordic"] = {
    "actors": ["Claims Operations Nordics", "the Nordic {handler}", "the Nordic {tl}", "the local claims team"],
    "objects": ["the local-currency amount", "the egenandel, självrisk or selvrisiko", "the regress claim", "the language preference",
                "the local policy wording", "the counterparty insurer", "the personal number"],
    "actions": ["apply the local policy wording for the country concerned", "correspond in the {customer}'s preferred language",
                "record amounts in the local currency of the policy", "check local practice with the Nordic Team Leader where it differs from UK practice",
                "use the regress process for recoveries from other Nordic insurers", "mask personal numbers in every non-production context"],
    "triggers": ["a Nordic claim involves a UK policyholder", "a counterparty insurer contests a regress claim",
                 "local legislation changes", "a claim crosses a currency boundary"],
    "conditions": ["the local wording and this manual appear to differ", "the {customer} prefers English",
                   "a local term has no exact UK equivalent"],
    "risks": ["UK practice being applied where local rules differ", "currency conversions being applied twice",
              "correspondence being issued in the wrong language"],
    "evidence": ["the local wording reference", "the language preference record", "the currency conversion basis"],
    "custinfo": ["which excess applies under their local policy", "how their claim will be handled locally"],
    "sentences": [
        "The Nordic branches follow this manual except where local law, local wordings or established market practice require a different approach.",
        "Local terms are used in customer correspondence: egenandel in Norway, självrisk in Sweden and selvrisiko in Denmark.",
        "Where this chapter and a local desk instruction differ, the Nordic Team Leader decides which applies and records the decision.",
        "Recoveries between Nordic insurers follow the regress arrangements of the local market.",
        "Amounts are held in the currency of the policy; GBP equivalents are used only for authority and reporting purposes.",
        "Personal numbers are visible in full only to staff who need them to handle the claim.",
    ],
}

TOPICS["motor"] = {
    "actors": ["the motor {handler}", "the {handler}", "the repair network", "the engineer", "the {tl}"],
    "objects": ["the repair estimate", "the market value", "the total-loss decision", "the vehicle registration",
                "the hire vehicle", "the third-party vehicle", "the liability position", "the keys and documents"],
    "actions": ["offer a network repair before discussing a cash settlement", "confirm the vehicle registration and keeper details",
                "establish liability as early as the evidence allows", "obtain the engineer's view before agreeing a total loss",
                "check whether a third-party vehicle was involved", "arrange the collection of a total-loss vehicle promptly"],
    "triggers": ["the repair estimate approaches the market value", "a third party disputes liability",
                 "the vehicle is recovered after a theft", "the customer declines a network repair"],
    "conditions": ["the vehicle is modified", "liability is split", "the keys cannot be produced", "the vehicle is foreign-registered"],
    "risks": ["vehicles sitting in storage while decisions are delayed", "liability being conceded without evidence",
              "total-loss decisions without an engineer's view"],
    "evidence": ["the engineer's report", "the repair authorisation", "the liability evidence", "the salvage release"],
    "custinfo": ["how the repair will be arranged", "how the market value was assessed", "what happens to their excess"],
    "sentences": [
        "Motor claims move quickly, and delay usually adds cost through storage and hire charges.",
        "Liability decisions are based on the evidence available, including statements, photos and any independent witness accounts.",
        "Where the customer declines a network repair, the handler explains the basis of any cash settlement.",
        "A total-loss decision is explained to the customer together with the market value used.",
        "Windscreen claims are routed to the glass network wherever the customer agrees.",
    ],
}

TOPICS["property"] = {
    "actors": ["the property {handler}", "the {ext_assessor}", "the drying contractor", "the repair network", "the {tl}"],
    "objects": ["the scope of works", "the drying record", "the cause of loss", "the alternative accommodation",
                "the contents schedule", "the buildings estimate", "the moisture readings", "the make-safe work"],
    "actions": ["establish the cause of loss before agreeing the scope of works", "check that drying is progressing and recorded",
                "agree the contents schedule with the {customer}", "consider alternative accommodation where the home is uninhabitable",
                "confirm that make-safe work has been completed", "check whether a neighbouring property is involved"],
    "triggers": ["the drying record shows no progress", "the {customer} cannot live in the property", "the scope of works increases",
                 "a neighbouring property is the source of the damage", "a weather event affects many customers"],
    "conditions": ["the cause of loss is disputed", "the property is tenanted", "the damage is long-standing",
                   "the contents cannot be inspected"],
    "risks": ["drying that stalls unnoticed", "scope creep without challenge", "customers living in unsuitable conditions",
              "recovery opportunities being missed where a neighbour is at fault"],
    "evidence": ["the drying certificate", "the scope of works", "the contents schedule", "the cause-of-loss report"],
    "custinfo": ["how long drying is likely to take", "what alternative accommodation is available",
                 "how contents will be valued"],
    "sentences": [
        "Escape of water claims are often the most disruptive for customers, and the handler should keep them informed throughout drying and repair.",
        "The cause of loss determines whether the claim is covered, so it is established before repairs are agreed.",
        "Drying contractors' readings are reviewed by the handler, not simply filed.",
        "Where the damage came from a neighbouring property, recovery potential is flagged at once.",
        "Customers are told what alternative accommodation is available and for how long.",
        "During weather events, simplified procedures may apply, but cover checks are never skipped.",
    ],
}

TOPICS["commercial"] = {
    "actors": ["the commercial {handler}", "the forensic accountant", "the {ext_assessor}", "the {tl}"],
    "objects": ["the business interruption claim", "the indemnity period", "the gross profit calculation", "the stock schedule",
                "the interim payment request", "the forensic accountant's report", "the continuity plan"],
    "actions": ["agree the information the business will provide at the outset", "consider interim payments once cover is confirmed",
                "involve a forensic accountant where the business interruption claim is complex",
                "check the policy schedule for the sums insured and indemnity period",
                "agree milestones with the insured business and record them"],
    "triggers": ["trading is disrupted for longer than expected", "the insured asks for an interim payment",
                 "the forensic accountant's figures differ from the insured's"],
    "conditions": ["the business has several locations", "underinsurance is suspected", "records are incomplete"],
    "risks": ["business interruption claims drifting without milestones", "interim payments being delayed unnecessarily"],
    "evidence": ["the forensic accountant's report", "the agreed milestone plan", "the policy schedule"],
    "custinfo": ["what information the business needs to provide", "how the loss of profit will be calculated"],
    "sentences": [
        "Commercial customers need clarity about what information they must provide and when.",
        "Business interruption claims are calculated using the business's own records, tested by a forensic accountant where appropriate.",
        "Interim payments help businesses keep trading and are considered as soon as cover is confirmed.",
        "Underinsurance is raised with the customer and their broker as soon as it is identified.",
    ],
}

TOPICS["liability"] = {
    "actors": ["the liability {handler}", "the {handler}", "the panel solicitor", "Major & Complex Loss", "the {tl}"],
    "objects": ["the liability decision", "the medical evidence", "the claimant's solicitor's letter", "the rehabilitation plan",
                "the legal reserve", "the court timetable", "the settlement strategy"],
    "actions": ["acknowledge the claim and investigate liability promptly", "consider rehabilitation needs early",
                "instruct panel solicitors in writing with clear objectives", "diary every court deadline",
                "review the case reserve at each procedural milestone", "obtain medical evidence before valuing an injury"],
    "triggers": ["proceedings are issued", "a letter of claim is received", "the medical prognosis changes",
                 "a settlement offer is received", "a court date is set"],
    "conditions": ["liability is disputed", "the injury is serious or long-term", "the claimant is a child or protected party"],
    "risks": ["missed court deadlines", "injury claims being valued without medical evidence", "rehabilitation being overlooked"],
    "evidence": ["the solicitor's instruction letter", "the medical report", "the court timetable", "the offer letter"],
    "custinfo": ["how their claim is being defended", "what their role in the proceedings will be"],
    "sentences": [
        "Bodily-injury claims are always handled by specialist staff because of their complexity and long tail.",
        "Rehabilitation can improve outcomes for the injured person and should be considered at the earliest stage.",
        "Court deadlines are diarised on receipt; a missed deadline can have serious consequences.",
        "Panel solicitors report at agreed intervals and whenever there is a material development.",
        "Settlement strategy is agreed with the Team Leader before offers are made.",
    ],
}

TOPICS["payments"] = {
    "actors": ["the {handler}", "Payments Operations", "the {tl}", "the authoriser", "the payment approver"],
    "objects": ["the payment request", "the payee details", "the payment authority", "the interim payment",
                "the duplicate-payment check", "the payment run", "the settlement letter"],
    "actions": ["verify the payee before the first payment", "check that the payment is within the authoriser's limit",
                "make sure the payment matches the settlement agreed", "record the purpose of each payment",
                "hold a payment where the payee details have recently changed", "confirm the payment to the {customer}"],
    "triggers": ["a payee changes their bank details", "a payment is returned", "a payment exceeds the handler's authority",
                 "a duplicate-payment alert is raised"],
    "conditions": ["the payee is not the policyholder", "the payment is to a third party", "the payment is in a foreign currency"],
    "risks": ["payments to the wrong account", "payments above authority", "duplicate payments", "payments without a recorded purpose"],
    "evidence": ["the payment authorisation", "the payee verification record", "the settlement agreement"],
    "custinfo": ["when the payment will arrive", "what the payment covers"],
    "sentences": [
        "No payment may be released by the person who requested it where it exceeds their own authority.",
        "Payee changes are a known fraud risk and are verified independently of the request.",
        "Every payment carries a purpose and a link to the settlement it relates to.",
        "Returned payments are investigated before they are reissued.",
        "Interim payments are recorded clearly so that the final settlement takes them into account.",
    ],
}

TOPICS["sanctions"] = {
    "actors": ["Payments Operations", "the {handler}", "Compliance", "the sanctions screening team"],
    "objects": ["the screening result", "the potential match", "the payee", "the screening record"],
    "actions": ["screen every payee before payment", "refer potential matches to Compliance without tipping off the payee",
                "hold the payment until a potential match is cleared", "record the outcome of each review"],
    "triggers": ["a potential match is returned", "a payee is added to a claim", "screening is unavailable"],
    "conditions": ["the match cannot be discounted", "the payee is overseas"],
    "risks": ["payments released before screening completes", "potential matches being closed without review"],
    "evidence": ["the screening result", "the Compliance decision"],
    "custinfo": [],
    "sentences": [
        "Sanctions screening is a legal obligation; there are no exceptions for small amounts or urgent payments.",
        "Handlers must not tell a payee that a payment is held because of a potential sanctions match.",
        "Potential matches are reviewed by Compliance, whose decision is final.",
    ],
}

TOPICS["fraud"] = {
    "actors": ["the {handler}", "{siu}", "the fraud analyst", "the {tl}", "the SIU investigator"],
    "objects": ["the fraud indicator", "the pre-screen result", "the referral", "the SIU case", "the investigation plan",
                "the evidence log", "the human review", "the case outcome"],
    "actions": ["record each fraud indicator objectively and without speculation",
                "refer concerns to {siu} rather than investigating them personally",
                "continue to handle the claim fairly while a referral is open", "keep fraud concerns out of customer correspondence",
                "record the evidence that supports each indicator", "check whether linked claims exist"],
    "triggers": ["a fraud indicator is identified", "the pre-screen result changes", "new evidence contradicts the {customer}'s account",
                 "a linked claim is found", "an investigation concludes"],
    "conditions": ["the indicator has an innocent explanation", "the {customer} is vulnerable", "evidence is inconclusive"],
    "risks": ["genuine customers being treated as suspects", "fraud concerns being written into letters",
              "adverse decisions being taken without documented review", "referrals being delayed while handlers investigate"],
    "evidence": ["the indicator record", "the referral form", "the investigation report", "the human review record"],
    "custinfo": ["that their claim is subject to additional checks", "how long the checks are expected to take"],
    "sentences": [
        "Fraud indicators are prompts for closer attention; they are not evidence of fraud and must never be treated as such.",
        "Most claims that show an indicator turn out to be genuine, and customers must be treated fairly throughout.",
        "Handlers refer concerns; they do not investigate them. Investigation is the role of {siu}.",
        "Fraud concerns are never mentioned in correspondence with the customer unless SIU has agreed the wording.",
        "Every adverse outcome on fraud grounds requires a documented human review.",
        "The quality of a referral depends on the quality of the evidence recorded by the handler.",
        "Claims Handlers receive feedback on the outcome of their referrals, which helps them calibrate future referrals.",
        "An indicator recorded today may be explained tomorrow; the file should show both the concern and the explanation.",
        "Handlers should be careful not to let a fraud concern colour their assessment of unrelated parts of the claim.",
        "Where a customer volunteers an explanation for an inconsistency, it is recorded in their own words.",
        "Information from third parties is checked before it is relied on, particularly where it comes from an anonymous source.",
        "{Cf} work is most effective when handlers and investigators share information early and in a structured way.",
        "A referral does not stop the clock on the customer's claim; handling continues in parallel wherever possible.",
        "Handlers should not contact third parties about a fraud concern unless SIU has asked them to.",
        "Photographs, documents and recordings relied on in an investigation are preserved in their original form.",
        "Where linked claims are found, each claim is assessed on its own facts as well as in the light of the link.",
        "{Cf} controls are reviewed when they produce unexpected results, including unusually high or low referral volumes.",
        "Analysts review indicator performance so that indicators that no longer discriminate are retired.",
        "Staff who suspect internal fraud follow the whistleblowing procedure rather than this chapter.",
        "Suspicion alone never justifies delaying a payment that is otherwise due.",
        "The customer's right to complain is unaffected by a fraud referral.",
    ],
}

TOPICS["recoveries"] = {
    "actors": ["the Recoveries handler", "the {handler}", "the Recoveries Team Leader", "the panel solicitor", "{recoveries}"],
    "objects": ["the recovery potential", "the subrogation case", "the demand letter", "the limitation date",
                "the recovery receipt", "the write-off request", "the salvage release", "the recoverable outlay"],
    "actions": ["flag recovery potential as soon as a responsible third party is identified",
                "preserve the evidence needed to pursue a recovery", "set a limitation diary when the case is opened",
                "issue the demand with the supporting evidence", "chase unanswered demands in line with this chapter",
                "record receipts against the right claim and recovery type"],
    "triggers": ["a third party admits liability", "a demand is ignored", "the limitation date approaches",
                 "a receipt is received", "the third party is uninsured"],
    "conditions": ["liability is shared", "the third party cannot be traced", "a knock-for-knock arrangement applies"],
    "risks": ["recoveries being time-barred", "evidence being lost before a recovery is pursued",
              "receipts being posted to the wrong claim", "recoveries being written off without approval"],
    "evidence": ["the liability evidence", "the demand letter", "the limitation diary", "the write-off approval"],
    "custinfo": ["whether their excess may be refunded", "how the recovery affects their claim"],
    "sentences": [
        "Recovery potential is easiest to secure at the start of a claim, when evidence is fresh and witnesses can be traced.",
        "The customer's uninsured losses, including their excess, are pursued with Corvane's outlay where the policy allows.",
        "Limitation dates are diarised when the case is opened and are never left to the end.",
        "Write-offs are approved at the right level and the reason is recorded.",
        "Where a third party's insurer disputes liability, the handler reviews the evidence before escalating.",
        "Recoveries performance is reported monthly, and missed opportunities are fed back to claims teams.",
    ],
}

TOPICS["settlement"] = {
    "actors": ["the {handler}", "the {tl}", "the settlement team", "the {cm}"],
    "objects": ["the settlement offer", "the settlement calculation", "the excess deduction", "the offer letter",
                "the final payment", "the cash settlement", "the closure checklist"],
    "actions": ["explain how the settlement was calculated", "deduct the correct excess for the product and peril",
                "check that all invoices and interim payments are reflected", "confirm acceptance of the offer in writing",
                "close the case reserve once the final payment is made", "complete the closure checklist before closing the file"],
    "triggers": ["the {customer} accepts the offer", "the {customer} disputes the amount", "the offer expires",
                 "a late invoice arrives after closure"],
    "conditions": ["the {customer} prefers cash to a repair", "several payees are involved", "the claim is partly covered"],
    "risks": ["settlements that cannot be explained", "the wrong excess being deducted", "files closed with open reserves",
              "late invoices being paid without checking"],
    "evidence": ["the settlement calculation", "the acceptance record", "the closure checklist"],
    "custinfo": ["how the settlement was calculated", "what is and is not included", "what to do if they disagree"],
    "sentences": [
        "A settlement should be explainable in a few sentences to the customer and to a reviewer.",
        "The customer is told what the settlement covers, what has been deducted and why.",
        "Partial settlements are explained clearly, including which items remain under consideration.",
        "Files are not closed while reserves, diary items or payments remain open.",
        "A reopened claim is handled as a continuation of the original claim, not as a new one.",
    ],
}

TOPICS["records"] = {
    "actors": ["the {handler}", "Data Protection", "the records manager", "the {tl}"],
    "objects": ["the claim record", "the retention date", "the disposal list", "the legal hold", "the subject access request",
                "the audit trail", "the call recording"],
    "actions": ["keep the claim record complete and accurate", "apply a legal hold where litigation is reasonably expected",
                "pass subject access requests to Data Protection on the day they are received",
                "dispose of records only through the approved disposal process", "check that the audit trail is intact"],
    "triggers": ["a subject access request is received", "litigation is threatened", "a claim reaches its retention date",
                 "a data breach is suspected"],
    "conditions": ["a legal hold applies", "records are held in more than one system", "the request is unclear"],
    "risks": ["records being kept longer than needed", "records being destroyed while a legal hold applies",
              "requests being missed or delayed"],
    "evidence": ["the disposal certificate", "the legal hold notice", "the request log"],
    "custinfo": ["how long we keep their information", "how to request a copy of their data"],
    "sentences": [
        "Records are kept for as long as they are needed and no longer; retention periods are set by rule, not by individual preference.",
        "A legal hold suspends normal disposal and is lifted only by Legal or Compliance.",
        "Subject access requests can arrive through any channel and in any form of words.",
        "Suspected data breaches are reported to Data Protection immediately.",
    ],
}

TOPICS["litigation"] = dict(TOPICS["liability"])
TOPICS["litigation"]["sentences"] = TOPICS["liability"]["sentences"] + [
    "Litigated claims carry additional cost and risk, and the handler should keep the litigation strategy under active review.",
    "Panel solicitors are instructed only through the approved panel arrangements.",
    "Offers to settle made in the course of proceedings are diarised and responded to within the time allowed.",
]
TOPICS["siu"] = dict(TOPICS["fraud"])
TOPICS["siu"]["sentences"] = TOPICS["fraud"]["sentences"] + [
    "Investigation plans are proportionate to the concern raised and are reviewed as evidence emerges.",
    "Surveillance and interviews are used only where authorised and where less intrusive steps would not be enough.",
    "The investigation file records each step taken, the reason for it and the result.",
]
TOPICS["notification"] = dict(TOPICS["fraud"])
TOPICS["notification"]["sentences"] = [
    "The customer notice explains that the claim is subject to additional checks; it does not allege fraud.",
    "The wording of the notice is agreed with Compliance and must not be altered locally.",
    "Where the notice is deferred, the reason and the approval are recorded on the referral.",
    "Handlers should be ready to answer customer questions about the notice in a neutral and factual way.",
    "The notice deadline runs from the date of referral, not from the date the handler becomes aware of it.",
    "A copy of every notice is retained on the claim record.",
]
TOPICS["salvage"] = dict(TOPICS["recoveries"])
TOPICS["salvage"]["sentences"] = [
    "Salvage is disposed of through the approved salvage agent so that disposal is traceable and compliant.",
    "Salvage categories determine whether a vehicle may return to the road; the category is recorded on the claim.",
    "Proceeds from salvage are posted promptly and matched to the claim.",
    "The customer is told what will happen to the damaged property before it is collected.",
]
TOPICS["closure"] = dict(TOPICS["settlement"])
TOPICS["reviews"] = dict(TOPICS["reserving"])
TOPICS["authority"] = dict(TOPICS["reserving"])
TOPICS["authority"]["sentences"] = [
    "Authority limits apply to the total incurred position on the claim, not to an individual movement or payment.",
    "A handler who does not hold authority for a decision obtains it before acting, never after.",
    "Authority overrides need a second approver at the next level and are recorded on the claim.",
    "Temporary authority granted to cover absence has a clear end date and is recorded centrally.",
    "Team Leaders monitor the use of authority in their teams and address any pattern of decisions close to a limit.",
]
TOPICS["committee"] = dict(TOPICS["reserving"])
TOPICS["indexation"] = dict(TOPICS["reserving"])
TOPICS["indexation"]["sentences"] = [
    "Indexation keeps long-tail reserves realistic by reflecting expected cost inflation between now and settlement.",
    "Indexation is applied by the system; handlers review the result as part of their normal reserve reviews.",
    "Currency movements affect GBP equivalents only; the local-currency reserve does not change because of exchange rates.",
    "The basis for indexation is set centrally and published to teams; handlers do not apply local adjustments.",
]

# ---------------------------------------------------------------------------------------------
# Sentence templates
# ---------------------------------------------------------------------------------------------

MUST = ["must", "is required to", "needs to", "must always"]
SHOULD = ["should", "is expected to", "ought to", "should normally"]
MUST_NOT = {"must": "must not", "is required to": "is required not to", "needs to": "must not", "must always": "must never"}
SHOULD_NOT = {"should": "should not", "is expected to": "is expected not to", "ought to": "ought not to", "should normally": "should not"}

TEMPLATES = [
    "{Actor} {must} {action} and record the outcome in the {notes}.",
    "Where {condition}, {actor} {should} {action} before the claim moves on.",
    "Before {milestone}, {actor} checks that {qa}.",
    "This matters because {rationale}.",
    "If {condition}, {actor} {should} refer the matter to {escalation} and set a diary date to follow it up.",
    "{Evidence} is kept on the {record} so that the decision can be reconstructed later.",
    "A weakness often found in file reviews is {risk}; {actor} can avoid it by taking care to {action}.",
    "When {trigger}, {actor} {should} {action}.",
    "The {customer} {should} be told {custinfo}.",
    "Explain {custinfo} in plain language, and confirm the explanation in writing if the {customer} asks for it.",
    "Any decision to depart from this guidance {must2} be agreed with {escalation} and the reason recorded.",
    "Quality reviews look for evidence that {qa}.",
    "Do not rely on memory or informal notes: {evidence_l} belongs on the {record}.",
    "{Actor} {should} keep {object} under review and update it as soon as new information arrives.",
    "Where the position is unclear, it is better to {action} than to wait for the next scheduled review.",
    "{Object} {must2} be consistent with {object2}; any difference is explained in the {notes}.",
    "When {trigger}, the first step is to {action}; the second is to tell the {customer} what this means for them.",
    "The aim is to prevent {risk}.",
    "Experience shows that {risk} is more likely when {condition}.",
    "{Actor} {should_not} assume that {object} is correct simply because it was recorded earlier in the claim.",
    "A short note explaining why {object} changed is more useful to a reviewer than a long description of what changed.",
    "Team Leaders sample files to confirm that {qa}.",
    "As a rule, {actor} {should} {action} at the earliest practical point.",
    "Where {trigger}, record the date, the source of the information and the action taken.",
    "If in doubt, {actor} {should} discuss the claim with {escalation} rather than delay a decision.",
    "Handlers {plural_should} {action}, because {rationale}.",
    "The {notes} {must2} show {evidence_l}, the decision taken and who took it.",
    "{Actor} {must_not} let {object} go out of date while the claim is open.",
    "Each step is recorded at the time it is taken, not reconstructed afterwards.",
    "Where {condition}, {escalation} decides how to proceed and the decision is noted on the {record}.",
]


TEMPLATES += [
    "In most cases {actor} will {action} without needing to involve anyone else.",
    "{Actor} {should} be ready to explain to a reviewer why {object} is what it is.",
    "It is not enough to {action}; the {notes} must also show why it was done.",
    "Where {trigger} late in the claim, {actor} {should} still {action} rather than treat the point as settled.",
    "The {tl} {should} be told promptly if {condition}.",
    "Handlers are reminded that {risk} remains one of the most common findings in quality reviews.",
    "{Evidence} {must2} be dated and attributed to the person who obtained it.",
    "A good file lets a reader see at a glance {qa_clause}.",
    "When in doubt about {object}, check the original source rather than a later summary.",
    "{Actor} {should} agree next steps with the {customer} before the call ends and confirm them in writing where helpful.",
    "Avoid duplicating work already done by another team; check the {record} before you {action}.",
    "The handling standard is the same whether the claim is large or small: {qa}.",
    "Any instruction given by telephone {must2} be confirmed in the {notes} on the same day.",
    "Where {condition}, {actor} {should} explain to the {customer} what this means for the timetable of the claim.",
    "{Object} is one of the first things a reviewer will examine, so it {must2} be kept current.",
    "Training material for new handlers uses this section as its reference point.",
    "Before escalating, {actor} {should} make sure {evidence_l} is on the file so that {escalation} can decide quickly.",
    "Where {trigger}, the claim {should_not} wait for the next diary date; {actor} acts on the information straight away.",
    "Peer reviews regularly test whether {qa}.",
    "{Actor} {should} keep the {customer} informed even when there is no news, so that they are not left chasing for updates.",
    "Experience across teams shows that taking time to {action} early saves effort later in the claim.",
    "If {condition}, record the facts as they are known and update the {record} as soon as the position becomes clearer.",
    "The decision {must2} be proportionate to the value and complexity of the claim.",
    "None of this prevents {actor} from using judgement; it requires that the judgement is recorded.",
    "Where several people work on the same claim, {actor} remains responsible for {object}.",
]

PROCEDURE_OPENERS = ["Open the claim and review the {notes} since the last action.",
                     "Check the claim summary for any open diary items or alerts.",
                     "Confirm that you hold the authority needed for the step you are about to take.",
                     "Read the most recent correspondence before contacting the {customer}.",
                     "Check whether another team already holds an open task on the claim.",
                     "Look at the latest entries in the {notes} to see what was last agreed.",
                     "Make sure the policy details shown on the {record} match the claim.",
                     "Note any vulnerability flag or communication preference before making contact.",
                     "Confirm which documents are still outstanding.",
                     "Review the current case reserve and the reason last recorded for it."]
PROCEDURE_CLOSERS = ["Record the outcome in the {notes} and set the next diary date.",
                     "Update the case reserve if the expected outcome has changed.",
                     "Tell the {customer} what has been decided and what happens next.",
                     "Refer to the {tl} if any step cannot be completed.",
                     "Confirm the next steps to the {customer} in writing if they ask for it.",
                     "Close any tasks that the action has made redundant.",
                     "Note who was contacted, when and what was agreed.",
                     "Check that any letter issued matches the decision recorded.",
                     "Set a follow-up diary date where a reply is awaited.",
                     "Escalate to the {cm} if the claim is outside your authority."]

H3_FILLER_TITLES = ["Practice notes", "Operational guidance", "Points to remember", "Quality points",
                    "Handling considerations", "Common pitfalls", "Further guidance", "Good practice",
                    "Practical application", "Supervisory checks", "File standards", "Working notes"]
H3_FILLER_TITLES_V61 = ["Guidance notes", "Notes for case handlers", "Points of practice", "Supplementary guidance",
                        "Additional notes", "Standards of practice", "Reminders", "Case handling notes",
                        "Observations from file reviews", "Supervisory notes"]


def _self_ref(actor: str, action: str) -> bool:
    core = re.sub(r"^the ", "", actor.strip(), flags=re.I).lower()
    return bool(core) and core in action.lower()


def _cap(s: str) -> str:
    return s[:1].upper() + s[1:] if s else s


class Prose:
    """Seeded sentence and paragraph generator for one document."""

    def __init__(self, rng: random.Random, style: dict):
        self.r = rng
        self.style = style
        self.used: set[str] = set()

    # -- helpers --------------------------------------------------------------------------
    def fmt(self, s: str) -> str:
        out = s
        for _ in range(3):
            if "{" not in out:
                break
            out = re.sub(r"\{(\w+)\}", lambda m: self.style.get(m.group(1), m.group(0)), out)
        return out

    def _pick(self, topic: dict, key: str):
        pool = list(topic.get(key) or []) + (COMMON.get(key, []) if key in COMMON and self.r.random() < 0.35 else [])
        if not pool:
            pool = COMMON.get(key) or ["the claim"]
        return self.fmt(self.r.choice(pool))

    def sentence(self, topic_key: str) -> str:
        t = TOPICS[topic_key]
        for _ in range(40):
            if t.get("sentences") and self.r.random() < 0.22:
                s = self.fmt(self.r.choice(t["sentences"]))
            else:
                tpl = self.r.choice(TEMPLATES)
                if "{custinfo}" in tpl and not t.get("custinfo"):
                    continue
                o1 = self._pick(t, "objects")
                o2 = self._pick(t, "objects")
                if o2 == o1:
                    continue
                vals = {
                    "Actor": _cap(self._pick(t, "actors")), "actor": self._pick(t, "actors"),
                    "action": self._pick(t, "actions"), "condition": self._pick(t, "conditions"),
                    "milestone": self.fmt(self.r.choice(COMMON["milestones"])), "qa": self._pick(t, "qa") if t.get("qa") else self.fmt(self.r.choice(COMMON["qa"])),
                    "rationale": self.fmt(self.r.choice((t.get("rationales") or []) + COMMON["rationales"])),
                    "escalation": self.fmt(self.r.choice(COMMON["escalation"])),
                    "Evidence": _cap(self._pick(t, "evidence")), "evidence_l": self._pick(t, "evidence"),
                    "risk": self._pick(t, "risks"), "trigger": self._pick(t, "triggers"),
                    "custinfo": self._pick(t, "custinfo") if t.get("custinfo") else "",
                    "object": o1, "Object": _cap(o1), "object2": o2,
                    "must": self.r.choice(MUST), "must2": "must", "should": self.r.choice(SHOULD),
                    "plural_should": self.r.choice(["should", "are expected to", "are asked to"]),
                    "qa_clause": "that " + (self._pick(t, "qa") if t.get("qa") else self.fmt(self.r.choice(COMMON["qa"]))),
                }
                vals["must_not"] = MUST_NOT[vals["must"]]
                vals["should_not"] = SHOULD_NOT[vals["should"]]
                if _self_ref(vals["actor"], vals["action"]) or _self_ref(vals["Actor"], vals["action"]):
                    continue      # e.g. "the SIU should refer concerns to the SIU"
                vals.update({k: v for k, v in self.style.items() if k not in vals})
                try:
                    s = tpl.format(**vals)
                except (KeyError, IndexError):
                    continue
                s = self.fmt(s)
            s = re.sub(r"\s+", " ", s).strip()
            s = s.replace("the the ", "the ").replace(" ,", ",")
            if s not in self.used:
                self.used.add(s)
                return s
        return s

    def paragraph(self, topic_key: str, n: tuple[int, int] = (3, 5)) -> str:
        k = self.r.randint(*n)
        return " ".join(self.sentence(topic_key) for _ in range(k))

    def steps(self, topic_key: str, n: tuple[int, int] = (4, 7)) -> list[str]:
        t = TOPICS[topic_key]
        k = self.r.randint(*n)
        acts = list(t.get("actions") or [])
        self.r.shuffle(acts)
        out = [self.fmt(self.r.choice(PROCEDURE_OPENERS))]
        for a in acts[:max(1, k - 2)]:
            out.append(_cap(self.fmt(a)) + ".")
        out.append(self.fmt(self.r.choice(PROCEDURE_CLOSERS)))
        return out

    def bullets(self, topic_key: str, key: str = "qa", n: tuple[int, int] = (3, 5)) -> list[str]:
        t = TOPICS[topic_key]
        pool = [self.fmt(x) for x in (t.get(key) or COMMON.get(key) or [])]
        if key == "qa":
            pool += [self.fmt(x) for x in COMMON["qa"]]
        self.r.shuffle(pool)
        return [_cap(x) for x in pool[:self.r.randint(*n)]]


    # -- extra filler unit types ------------------------------------------------------------
    def qa_unit(self, topic_key: str) -> list[dict]:
        t = TOPICS[topic_key]
        trig = self._pick(t, "triggers")
        act = self._pick(t, "actions")
        actor = self._pick(t, "actors")
        for _ in range(6):
            if not _self_ref(actor, act):
                break
            actor = self._pick(t, "actors")
        q = self.r.choice([f"What should happen when {trig}?", f"What is expected when {trig}?",
                           f"Who acts when {trig}?"])
        a = f"{_cap(actor)} {self.r.choice(SHOULD)} {act}. " + self.sentence(topic_key)
        return [{"t": "p", "runs": [{"text": "Question: ", "bold": True}, {"text": q}]},
                {"t": "p", "runs": [{"text": "Answer: ", "bold": True}, {"text": a}]}]

    def dodont_table(self, topic_key: str) -> dict:
        t = TOPICS[topic_key]
        acts = [self.fmt(x) for x in (t.get("actions") or [])]
        risks = [self.fmt(x) for x in (t.get("risks") or [])]
        self.r.shuffle(acts)
        self.r.shuffle(risks)
        n = min(4, len(acts), len(risks))
        rows = [[_cap(acts[i]), "Allow " + risks[i]] for i in range(max(2, n))] if n >= 2 else [[_cap(a), "\u2014"] for a in acts[:3]]
        return {"t": "table", "header": ["Do", "Avoid"], "rows": rows, "widths": [8, 8], "size": 9, "repeat_header": True}

    def note_unit(self, topic_key: str) -> list[dict]:
        t = TOPICS[topic_key]
        acts = [self.fmt(x) for x in (t.get("actions") or [])]
        self.r.shuffle(acts)
        body = "; ".join(a[:1].upper() + a[1:] for a in acts[:3]) + "; next diary date set."
        intro = self.r.choice(["An adequate claim note might read:", "For example, a note that meets this standard:",
                               "Illustrative note (wording will vary):"])
        return [{"t": "p", "text": intro, "keep_next": True}, {"t": "p", "text": body, "style": "Box Text"}]

    def filler_title(self, v61: bool = False) -> str:
        return self.r.choice(H3_FILLER_TITLES_V61 if v61 else H3_FILLER_TITLES)

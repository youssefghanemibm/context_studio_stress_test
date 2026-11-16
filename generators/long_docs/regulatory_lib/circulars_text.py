"""Content of the two NISA circulars (LD022: Circular 2026/04, LD023: Circular 2024/07).

Block grammar used by circulars.py:
    ("h1", text)                      numbered section heading (number included in text)
    ("h2", text)                      sub-heading
    ("par", number, tag, text)        numbered paragraph; tag is "R" (requirement) or "G" (guidance)
    ("p", text)                       plain paragraph
    ("ul", [items])                   bullet list
    ("table", title, rows, widths)    table, first row is the header; widths in mm
    ("pb",)                           page break

Requirement texts are passed in from world/data/regulators.yaml; nothing in the guidance adds a new
number, deadline or threshold beyond those requirements and the NISA-FR1 report schedule.
"""
from __future__ import annotations


def circ_2026_04(req: dict, people: dict, report_fr1: dict, related: list) -> dict:
    """req: para -> requirement text; people: author name/title/email; report_fr1: dates."""
    a = people
    blocks = [
        ("h1", "1  Introduction"),
        ("par", "1.1", "G", "This circular sets out the Authority's requirements for the fair treatment of customers whose "
                           "claims are referred for additional checks because fraud is suspected. It applies in particular "
                           "where an automated or model-based score contributes to the decision to refer a claim."),
        ("par", "1.2", "G", "Insurers have a legitimate interest in detecting and deterring fraudulent claims, which "
                           "increase the cost of insurance for all policyholders. The Authority supports effective "
                           "counter-fraud work and does not wish to discourage it. Counter-fraud controls must, however, "
                           "operate in a way that is fair to the great majority of customers whose claims are genuine."),
        ("par", "1.3", "G", "Supervisory work across the market has identified a number of practices that cause the "
                           "Authority concern:"),
        ("ul", ["claims declined, reduced or repudiated where the only material evidence was a high score produced by "
                "a scoring tool;",
                "customers left for long periods without being told that their claim was subject to additional checks, "
                "causing distress and, in some cases, financial hardship;",
                "referral cut-offs set without a documented rationale, and not revisited when the scoring model, its "
                "inputs or the mix of claims changed;",
                "limited management information about the number of referrals, how they were resolved and how long "
                "they took."]),
        ("par", "1.4", "G", "This circular responds to those findings. Section 3 sets out five requirements, each "
                           "supported by guidance. Section 6 introduces a new quarterly return, the NISA-FR1 fraud "
                           "referral return, which will give the Authority consistent information across firms."),
        ("par", "1.5", "G", "Firms should read this circular together with NISA Circular 2024/07 (Claims Handling "
                           "Timeliness) and NISA Circular 2025/11 (Claims Data Retention and Minimisation). Where this "
                           "circular refers to those publications, it does not change them."),
        ("par", "1.6", "G", "The Authority's approach is outcomes-focused. Firms should be able to show not only that "
                           "they have processes that meet the requirements, but that those processes lead to fair "
                           "outcomes for customers in practice."),
        ("par", "1.7", "G", "Paragraphs marked R are requirements. Paragraphs marked G are guidance: they explain the "
                           "Authority's expectations and the factors it will take into account when assessing whether a "
                           "firm has met the requirements. Defined terms are listed in Annex A."),

        ("h1", "2  Scope and application"),
        ("par", "2.1", "G", "This circular applies to every firm supervised by the Authority that handles claims under "
                           "contracts of general insurance, whether it handles claims itself or through an outsourced "
                           "claims handler, loss adjuster or other third party."),
        ("par", "2.2", "G", "It applies to UK-headquartered insurers in respect of the claims handled by their Nordic "
                           "branches, in the same way as to claims handled in the United Kingdom, whatever the language "
                           "or currency of the claim."),
        ("par", "2.3", "G", "The requirements on automated scores (paragraphs 3.1 and 3.3) apply whether the score is "
                           "produced by a model developed by the firm or by a tool licensed from a third-party supplier. "
                           "A firm cannot rely on a supplier's assurance that a tool is fair: it must be able to explain "
                           "and evidence how the tool is used in its own claims process."),
        ("par", "2.4", "G", "The requirements on customer notices, returns and records (paragraphs 3.2, 3.4 and 3.5) "
                           "apply to every referral, whatever its source. A referral may result from a score, from the "
                           "observations of a claims handler or Claims Assessor, from information supplied by a third "
                           "party or from an industry database."),
        ("par", "2.5", "G", "Where a firm outsources any part of its claims or counter-fraud activity, it remains "
                           "responsible for meeting the requirements. Contracts with outsourced providers should give the "
                           "firm the information and access it needs to do so."),
        ("par", "2.6", "G", "This circular does not change the law on fraud, or any right a firm has under the "
                           "insurance contract or under the general law to decline a fraudulent claim. It concerns the "
                           "process by which a firm reaches and communicates such decisions."),

        ("h1", "3  Requirements"),
        ("p", "The requirements in this section take effect on the effective date shown on the front page of this "
              "circular. Each requirement is followed by guidance."),
        ("h2", "Human review of score-based decisions"),
        ("par", "3.1", "R", req["3.1"]),
        ("par", "3.1.1", "G", "A score may be a legitimate reason to look more closely at a claim. It is not, on its own, "
                             "evidence that a claim is fraudulent. Any decision to decline, reduce or repudiate a claim "
                             "must rest on evidence that a competent person has reviewed and found persuasive."),
        ("par", "3.1.2", "G", "The reviewer should have the competence and authority to reach a conclusion different from "
                             "the one suggested by the score, and should have access to the underlying evidence, "
                             "including any information supplied by the customer."),
        ("par", "3.1.3", "G", "The record of the review should identify the reviewer, the evidence considered and the "
                             "reasons for the decision. A record that simply repeats the score, or confirms that the "
                             "score exceeded the cut-off, does not meet the requirement."),
        ("par", "3.1.4", "G", "Firms should not set targets, or operate incentive schemes, that reward staff or "
                             "suppliers for the number or value of claims declined following a referral."),
        ("h2", "Telling the customer"),
        ("par", "3.2", "R", req["3.2"]),
        ("par", "3.2.1", "G", "The notice should be in plain language. It should explain that additional checks are being "
                             "made, indicate what the customer may be asked to provide, give a realistic indication of "
                             "how long the checks are expected to take and provide a point of contact. It need not "
                             "disclose the reason for the referral or any score."),
        ("par", "3.2.2", "G", "Business days exclude weekends and public holidays in the jurisdiction in which the claim "
                             "is handled."),
        ("par", "3.2.3", "G", "A certification of tipping-off risk should be made by a senior individual with "
                             "responsibility for counter-fraud. It should record why informing the customer would be "
                             "likely to prejudice an investigation. The certification should be kept under review, and "
                             "the notice should be issued as soon as the risk has passed and in any event before the end "
                             "of the permitted deferral."),
        ("par", "3.2.4", "G", "The notice required by paragraph 3.2 is separate from the acknowledgement of a first notice "
                             "of loss required by NISA Circular 2024/07. Issuing the acknowledgement does not satisfy "
                             "paragraph 3.2."),
        ("h2", "Calibration of referral cut-offs"),
        ("par", "3.3", "R", req["3.3"]),
        ("par", "3.3.1", "G", "Calibration should be based on evidence about the relationship between scores and the "
                             "outcomes of referrals, and should be documented in a form that the firm's risk function, "
                             "internal audit and the Authority can review. Annex D lists the matters the Authority "
                             "expects the documentation to cover."),
        ("par", "3.3.2", "G", "Where a scoring tool uses a scale other than 0–100, the firm should document how its "
                             "cut-off corresponds to the ceiling in paragraph 3.3."),
        ("par", "3.3.3", "G", "A firm may set lower cut-offs for particular products, claim types or segments, provided "
                             "each cut-off is calibrated and documented in the same way."),
        ("par", "3.3.4", "G", "Cut-offs should be reviewed whenever the model, its inputs or the mix of claims changes "
                             "materially, and periodically under the firm's model risk framework. Firms should monitor "
                             "referral rates and outcomes by product and by customer characteristics in order to detect "
                             "outcomes that may be unfair."),
        ("h2", "Reporting to the Authority"),
        ("par", "3.4", "R", req["3.4"]),
        ("par", "3.4.1", "G", f"The first return covers the quarter ending 30 June 2026 and is due on "
                             f"{report_fr1['first_due_long']}. Section 6 and Annex C describe the content of the return."),
        ("h2", "Record keeping"),
        ("par", "3.5", "R", req["3.5"]),
        ("par", "3.5.1", "G", "Referral records include the score and the version of the model that produced it, the "
                             "cut-off in force at the time, the record of any human review, the notices issued to the "
                             "customer, any certification of tipping-off risk and the outcome of the referral."),
        ("par", "3.5.2", "G", "The retention period in paragraph 3.5 is consistent with NISA Circular 2025/11. Firms "
                             "should delete referral records at the end of the retention period unless they are needed "
                             "for legal proceedings, in line with the data minimisation principle in that circular."),

        ("h1", "4  Governance and accountability"),
        ("par", "4.1", "G", "The firm's board, or an appropriate committee of the board, should approve the firm's "
                           "approach to fraud referral, including its use of scoring tools, and should receive regular "
                           "management information about referral volumes, outcomes and customer impact."),
        ("par", "4.2", "G", "A named senior individual should be accountable for compliance with this circular. That "
                           "individual should have sufficient seniority and access to information to challenge the "
                           "firm's counter-fraud and claims functions."),
        ("par", "4.3", "G", "Firms should ensure that the second line of defence reviews the calibration documentation "
                           "required by paragraph 3.3, and that internal audit includes fraud referral within its "
                           "programme of work."),
        ("par", "4.4", "G", "Staff who carry out human reviews under paragraph 3.1 should receive training on the "
                           "limitations of scoring tools, on the evidence needed to support a decision and on the fair "
                           "treatment of customers, including customers in vulnerable circumstances."),
        ("par", "4.5", "G", "Firms should have a process for customers to challenge a decision taken after a referral, and "
                           "should make sure that complaints about referral are handled by people who were not involved "
                           "in the original decision."),
        ("par", "4.6", "G", "Where a scoring tool is supplied by a third party, the firm should obtain sufficient "
                           "information about the tool to meet paragraph 3.3, and should assess the supplier's change "
                           "management so that it is told in advance of changes that may affect calibration."),
        ("par", "4.7", "G", "Firms should keep their approach under review in the light of complaints, ombudsman "
                           "decisions, internal audit findings and the management information described above."),

        ("h1", "5  Customers in vulnerable circumstances"),
        ("par", "5.1", "G", "Being told that a claim is subject to additional checks can be particularly distressing for "
                           "customers in vulnerable circumstances, for example customers who have suffered a bereavement, "
                           "a serious injury or the loss of their home, or customers with limited ability to deal with "
                           "written correspondence."),
        ("par", "5.2", "G", "Firms should take account of any known vulnerability when preparing the notice required by "
                           "paragraph 3.2, when deciding what information to ask the customer for and when setting the "
                           "pace of the checks. The notice should be available in accessible formats on request."),
        ("par", "5.3", "G", "Firms should consider whether interim payments or other support are appropriate while checks "
                           "are carried out, particularly where the customer cannot live in their home or needs a vehicle "
                           "to work. Additional checks are not, by themselves, a reason to withhold support that would "
                           "otherwise be available under the policy."),
        ("par", "5.4", "G", "Scoring tools should not use a customer's vulnerability, or characteristics closely associated "
                           "with it, as a factor that increases the likelihood of referral. Firms should test their tools "
                           "for this effect as part of the monitoring described in paragraph 3.3.4."),
        ("par", "5.5", "G", "Staff who contact customers about additional checks should be trained to recognise signs of "
                           "vulnerability and to adapt their approach, and should know how to escalate cases of concern."),

        ("h1", "6  The NISA-FR1 fraud referral return"),
        ("par", "6.1", "G", "The NISA-FR1 return is a quarterly return. It must be submitted within 30 days after the end "
                           "of each calendar quarter, as required by paragraph 3.4."),
        ("par", "6.2", "G", "The return collects information about the number of referrals made in the quarter, the "
                           "sources of those referrals, the notices issued and deferred under paragraph 3.2, and the "
                           "outcomes of referrals concluded in the quarter. Annex C lists the data items."),
        ("par", "6.3", "G", "The return should be approved before submission by an individual of appropriate seniority. "
                           "Firms should be able to reconcile the figures to their claims and counter-fraud systems."),
        ("par", "6.4", "G", "Firms should submit the return through the Authority's regulatory reporting channel. The "
                           "Authority will publish technical guidance on the file format separately."),
        ("par", "6.5", "G", "The table below shows the reporting periods and due dates for the first four returns."),
        ("table", "Table 1  NISA-FR1 reporting periods and due dates", report_fr1["schedule_rows"], [40, 55, 50]),
        ("par", "6.6", "G", "Where a firm becomes aware that a submitted return contained a material error, it should "
                           "submit a corrected return and tell its supervisory contact as soon as possible."),

        ("h1", "7  Worked examples"),
        ("p", "The following examples illustrate how the Authority expects the requirements to apply. They are not "
              "exhaustive and do not change the requirements."),
        ("h2", "Example 1: a decision based on the score alone"),
        ("par", "7.1", "G", "A household claim is referred automatically because its score is above the firm's cut-off. "
                           "Without further enquiry, the claims handler writes to the customer declining the claim on the "
                           "ground that it has been identified as high risk. This does not meet paragraph 3.1. The firm "
                           "must review the evidence, record its reasons and reach a decision that rests on that "
                           "evidence."),
        ("h2", "Example 2: a human review that adds nothing"),
        ("par", "7.2", "G", "A firm's procedure requires a team leader to approve every decline that follows a referral. "
                           "The approval screen shows only the score and a button marked approve. The team leader does "
                           "not see the claim file. This is not a documented human review within the meaning of paragraph "
                           "3.1.3."),
        ("h2", "Example 3: counting business days"),
        ("par", "7.3", "G", "The period in paragraph 3.2 is counted in business days in the jurisdiction in which the "
                           "claim is handled. The table below shows when the written notice is due for referrals made on "
                           "the dates shown, taking account of public holidays."),
        ("table", "Table 2  Illustrative notice due dates", [
            ("Referral made", "Claim handled in", "Public holidays in the period", "Notice due by"),
            ("Monday 13 April 2026", "United Kingdom", "None", "Monday 27 April 2026"),
            ("Wednesday 29 April 2026", "United Kingdom", "Monday 4 May 2026", "Thursday 14 May 2026"),
            ("Wednesday 29 April 2026", "Norway", "Friday 1 May and Thursday 14 May 2026", "Friday 15 May 2026"),
        ], [40, 32, 52, 41]),
        ("h2", "Example 4: deferral of the notice"),
        ("par", "7.4", "G", "An investigator believes that a claim is linked to an organised group and that telling the "
                           "customer about the checks would lead to evidence being destroyed. The firm's senior "
                           "counter-fraud manager reviews the evidence and certifies the tipping-off risk, recording the "
                           "reasons. The notice may be deferred within the limit in paragraph 3.2. The firm keeps the "
                           "certification under review and issues the notice once the risk has passed."),
        ("h2", "Example 5: a cut-off on a different scale"),
        ("par", "7.5", "G", "A firm uses a tool that produces a score between 0 and 1,000. It documents the mapping "
                           "between that scale and a 0–100 scale and shows that its cut-off corresponds to no more than "
                           "the ceiling in paragraph 3.3. It reviews the mapping when the supplier releases a new version "
                           "of the model."),

        ("h1", "8  Implementation and transition"),
        ("par", "8.1", "G", "The requirements in Section 3 apply from the effective date. The Authority expects firms to "
                           "use the period before that date to review their scoring tools, cut-offs, customer "
                           "communications and record keeping, and to make any changes needed."),
        ("par", "8.2", "G", "Referrals that are open on the effective date should be handled in accordance with "
                           "paragraphs 3.1, 3.2 and 3.5 from that date. A firm does not need to re-issue notices already "
                           "given to customers before the effective date if they meet the standard in paragraph 3.2.1."),
        ("par", "8.3", "G", "Firms whose current cut-offs exceed the ceiling in paragraph 3.3 should recalibrate them "
                           "before the effective date and document the recalibration as described in Annex D."),
        ("par", "8.4", "G", "Firms should be ready to submit the first NISA-FR1 return for the quarter ending 30 June "
                           "2026."),
        ("par", "8.5", "G", "The Authority may ask firms to explain their implementation plans before the effective "
                           "date. Firms should keep a record of the steps taken."),

        ("h1", "9  Supervisory approach"),
        ("par", "9.1", "G", "The Authority will use the NISA-FR1 returns to compare firms and to identify outliers, for "
                           "example firms with unusually high referral rates or long periods between referral and "
                           "outcome."),
        ("par", "9.2", "G", "The Authority may carry out thematic reviews of fraud referral, including file reviews of "
                           "individual referrals, and may ask firms for their calibration documentation."),
        ("par", "9.3", "G", "Where the Authority finds that a firm has not met the requirements, it will consider the "
                           "full range of supervisory tools available to it, including requiring the firm to review past "
                           "decisions and to put right any harm caused to customers."),
        ("par", "9.4", "G", "Firms that identify a failure to meet the requirements should tell their supervisory contact "
                           "promptly and explain the steps they are taking."),

        ("h1", "10  Cost benefit analysis and compatibility with the Authority's objectives"),
        ("par", "10.1", "G", "The Authority expects the main costs of this circular to fall on firms that do not already "
                            "document their referral cut-offs, keep complete referral records or tell customers promptly "
                            "about additional checks. For those firms, there will be one-off costs of reviewing tools "
                            "and processes and ongoing costs of preparing the NISA-FR1 return."),
        ("par", "10.2", "G", "The Authority expects the benefits to include fewer genuine claims declined or delayed, less "
                            "distress for customers whose claims are checked, fewer complaints and better information for "
                            "firms and the Authority about the effectiveness of counter-fraud controls."),
        ("par", "10.3", "G", "The requirements are compatible with the Authority's objectives of securing an appropriate "
                            "degree of protection for policyholders and promoting the safety and soundness of insurers. "
                            "They do not prevent firms from taking effective action against fraudulent claims."),
        ("par", "10.4", "G", "The Authority has considered whether the requirements could have a disproportionate effect on "
                            "particular groups of customers. It considers that the monitoring expected under paragraph "
                            "3.3.4 and the guidance in Section 5 will help firms to identify and address any such effect."),

        ("h1", "11  Feedback on consultation"),
        ("par", "11.1", "G", "The Authority consulted on a draft of this circular before finalising it. It received responses "
                           "from insurers, trade bodies, consumer organisations and suppliers of scoring tools. The "
                           "Authority is grateful to all respondents."),
        ("par", "11.2", "G", "The main themes raised by respondents, and the Authority's response, are summarised in the "
                           "table below. The Authority has not changed the substance of the requirements in Section 3."),
        ("table", "Table 3  Summary of consultation feedback", [
            ("Theme", "Summary of responses", "Authority's response"),
            ("Ceiling on cut-offs", "Some insurers argued that a ceiling would limit their ability to tailor tools. "
             "Consumer organisations supported a ceiling.", "The ceiling is retained. Firms may set lower cut-offs where "
             "calibrated (paragraph 3.3.3)."),
            ("Timing of notice", "Several respondents asked whether a telephone call could count as notice.",
             "Paragraph 3.2 requires written notice. A call may be helpful in addition."),
            ("Tipping-off risk", "Respondents asked who may certify the risk and how the deferral should be managed.",
             "Guidance added at paragraph 3.2.3."),
            ("Third-party tools", "Suppliers were concerned about disclosing proprietary details of their models.",
             "Firms need sufficient information to evidence calibration (paragraph 4.6)."),
            ("Frequency of return", "Some respondents preferred an annual return.", "The return remains quarterly to give "
             "timely information."),
            ("Proportionality", "Smaller firms asked for simplified documentation.", "The documentation may be "
             "proportionate to the firm's use of scoring tools (Annex D)."),
        ], [33, 70, 62]),
        ("par", "11.3", "G", "The Authority will keep the requirements under review in the light of the information it "
                           "receives through the NISA-FR1 return."),

        ("h1", "12  Contact"),
        ("par", "12.1", "G", f"Questions about this circular should be sent to {a['name']}, {a['title']}, at "
                           f"{a['email']}. Questions about the NISA-FR1 return may also be raised with the firm's "
                           f"usual supervisory contact."),
    ]
    annexes = [
        ("pb",),
        ("h1", "Annex A  Definitions"),
        ("table", None, [
            ("Term", "Meaning in this circular"),
            ("Automated score", "A numerical or categorical output of a model, rule set or other tool, produced "
             "wholly or partly by automated means, that indicates the likelihood that a claim is fraudulent."),
            ("Referral", "The decision to subject a claim to additional checks because fraud is suspected, including "
             "referral to a firm's special investigations unit or to an external investigator."),
            ("Referral cut-off", "The score at or above which a claim is referred automatically or flagged for "
             "referral."),
            ("Documented human review", "A review by a competent person of the evidence relating to a claim, recorded "
             "as described in paragraph 3.1.3."),
            ("Tipping-off risk", "The risk that telling the customer about the additional checks would be likely to "
             "prejudice an investigation."),
            ("Business day", "A day other than a Saturday, Sunday or public holiday in the jurisdiction in which the "
             "claim is handled."),
            ("Quarter", "A calendar quarter ending on 31 March, 30 June, 30 September or 31 December."),
            ("Firm", "An insurer supervised by the Authority, including its branches outside the United Kingdom."),
        ], [42, 123]),
        ("h1", "Annex B  Summary of requirements"),
        ("table", None, [
            ("Paragraph", "Requirement", "Applies from"),
            ("3.1", req["3.1"], "Effective date"),
            ("3.2", req["3.2"], "Effective date"),
            ("3.3", req["3.3"], "Effective date"),
            ("3.4", req["3.4"], "Quarter ending 30 June 2026"),
            ("3.5", req["3.5"], "Effective date"),
        ], [20, 112, 33]),
        ("h1", "Annex C  NISA-FR1 data items"),
        ("p", "Each item is reported for the quarter, in total and analysed by product line. Firms with Nordic branches "
              "report each branch separately."),
        ("table", None, [
            ("Item", "Description"),
            ("C1", "Number of claims referred in the quarter"),
            ("C2", "Number of referrals by source: automated score, staff observation, third-party information, other"),
            ("C3", "Number of written notices issued under paragraph 3.2 within the required period"),
            ("C4", "Number of notices deferred on certification of tipping-off risk"),
            ("C5", "Number of referrals concluded in the quarter, by outcome: no further action, claim paid in full, "
                   "claim reduced, claim declined or repudiated, claim withdrawn"),
            ("C6", "For referrals concluded in the quarter, the median and maximum time from referral to outcome"),
            ("C7", "Number of complaints received about referral, and the number upheld"),
            ("C8", "The referral cut-off or cut-offs in force at the end of the quarter, and the scale used"),
        ], [18, 147]),
        ("h1", "Annex D  Calibration documentation"),
        ("p", "The documentation required by paragraph 3.3 should cover at least the following matters. It may be "
              "proportionate to the extent of the firm's use of scoring tools."),
        ("table", None, [
            ("Area", "What the documentation should show"),
            ("Purpose", "What the tool is used for and at which point in the claims process"),
            ("Data", "The data used to develop and calibrate the tool, and its relevance to the firm's own claims"),
            ("Outcomes", "The evidence linking scores to the outcomes of referrals"),
            ("Cut-off", "How each cut-off was chosen, and how it relates to the ceiling in paragraph 3.3"),
            ("Fairness", "How referral rates and outcomes are monitored across products and customer groups"),
            ("Change", "How changes to the model, its inputs or the claims mix trigger a review of the cut-off"),
            ("Approval", "Who approved the cut-off, when, and on what evidence"),
            ("Supplier", "For third-party tools, the information obtained from the supplier and how it was assessed"),
        ], [30, 135]),
        ("h1", "Annex E  Illustrative customer notice"),
        ("p", "The following wording is illustrative only. Firms may use their own wording provided it meets "
              "paragraph 3.2.1."),
        ("quote", ["Dear [customer name],",
                   "Your claim [claim reference]",
                   "Thank you for your claim. We are writing to let you know that we need to carry out some additional "
                   "checks before we can make a decision. This is something we do on a number of claims, and it does "
                   "not mean that we have reached any conclusion about your claim.",
                   "We may ask you for further information or documents. We expect the checks to take around [period], "
                   "and we will tell you if they will take longer.",
                   "If you have any questions, please contact [name] on [telephone number] or at [email address].",
                   "Yours sincerely,",
                   "[name, role]"]),
        ("h1", "Annex F  Frequently asked questions"),
        ("h2", "Does the circular apply to claims referred before the effective date?"),
        ("p", "Paragraphs 3.1, 3.2 and 3.5 apply to referrals that are open on the effective date, as explained in "
              "paragraph 8.2. A firm does not need to re-open decisions reached before that date."),
        ("h2", "Must the reviewer under paragraph 3.1 be independent of the counter-fraud team?"),
        ("p", "No. The reviewer may work in the counter-fraud team, provided they have the competence and authority "
              "described in paragraph 3.1.2 and have access to the evidence."),
        ("h2", "Does the notice have to explain why the claim was referred?"),
        ("p", "No. The notice must tell the customer that the claim is subject to additional checks. It need not give "
              "the reason for the referral or any score (paragraph 3.2.1)."),
        ("h2", "Can a firm set different cut-offs for different products?"),
        ("p", "Yes, provided each cut-off is calibrated and documented and none exceeds the ceiling in paragraph 3.3."),
        ("h2", "Who signs the NISA-FR1 return?"),
        ("p", "The return should be approved by an individual of appropriate seniority (paragraph 6.3). Firms may decide "
              "which individual is most appropriate."),
        ("h2", "Does paragraph 3.5 override a longer retention period required by law?"),
        ("p", "No. Where the law or legal proceedings require records to be kept for longer, the firm should keep them "
              "for that longer period."),
        ("h2", "Does the circular apply to referrals made by outsourced loss adjusters?"),
        ("p", "Yes. A referral made by a loss adjuster or other provider acting for the firm is a referral by the firm "
              "for the purposes of this circular (paragraph 2.5)."),
        ("h1", "Annex G  Related NISA publications"),
        ("p", "The following circulars contain requirements that are relevant to firms' handling of referred claims. "
              "This circular does not change them."),
        ("table", None, [("Circular", "Title", "Effective", "Relevance to this circular")] + related, [30, 45, 28, 62]),
        ("p", "Firms should also have regard to their obligations under data protection law when processing personal "
              "data for counter-fraud purposes, including the information they give customers about that processing."),
    ]
    summary = ("This circular sets out requirements for the fair treatment of customers whose claims are referred for "
               "additional checks because fraud is suspected, including where automated scores are used. It requires "
               "documented human review of score-based decisions, timely written notice to customers, calibrated "
               "referral cut-offs, a new quarterly NISA-FR1 return and retention of referral records.")
    return {"blocks": blocks + annexes, "summary": summary}


def circ_2024_07(req: dict, people: dict) -> dict:
    a = people
    blocks = [
        ("h1", "1  Introduction"),
        ("par", "1.1", "G", "This circular sets out the Authority's requirements on the timeliness of claims handling, "
                           "starting with the first contact a customer has with an insurer after a loss."),
        ("par", "1.2", "G", "Prompt acknowledgement of a claim matters to customers. It confirms that the claim has been "
                           "received, tells the customer who is dealing with it and what will happen next, and reduces "
                           "the number of repeat contacts. Supervisory work has found wide variation between firms in "
                           "how quickly claims are acknowledged and in the information they hold about timeliness."),
        ("par", "1.3", "G", "This circular sets a single standard for the acknowledgement of a first notice of loss and "
                           "introduces an annual return, NISA-CT1, so that the Authority can monitor timeliness across "
                           "the market."),
        ("par", "1.4", "G", "Paragraphs marked R are requirements. Paragraphs marked G are guidance. Defined terms are "
                           "listed in Annex A."),
        ("h1", "2  Requirements"),
        ("par", "2.1", "R", req["2.1"]),
        ("par", "2.2", "G", "The acknowledgement should give the customer a claim reference, explain the next steps, tell "
                           "the customer what information or documents may be needed and give a point of contact. An "
                           "automated message that does not contain this information does not, on its own, meet the "
                           "standard the Authority expects."),
        ("par", "2.3", "G", "A first notice of loss may be received by any channel, including telephone, post, email, a "
                           "web portal, a mobile application or a broker. The time for acknowledgement runs from the day "
                           "the first notice of loss is received by the firm or by a person acting on its behalf."),
        ("par", "2.4", "R", req["2.4"]),
        ("par", "2.5", "G", "Business days exclude weekends and public holidays in the jurisdiction in which the claim "
                           "is handled. For UK-headquartered insurers with Nordic branches, the holidays of the country in "
                           "which the branch handles the claim apply."),
        ("h1", "3  Scope and application"),
        ("par", "3.1", "G", "This circular applies to every firm supervised by the Authority that handles claims under "
                           "contracts of general insurance, including claims handled by Nordic branches of UK-"
                           "headquartered insurers and claims handled by outsourced providers."),
        ("par", "3.2", "G", "Where a broker or other intermediary receives a first notice of loss on behalf of the firm, "
                           "the firm should agree arrangements with the intermediary so that the claim can be "
                           "acknowledged within the required time."),
        ("par", "3.3", "G", "Where a firm outsources claims handling, it remains responsible for meeting the "
                           "requirements and should monitor the performance of its providers."),
        ("par", "3.4", "G", "Policy wordings and customer documents that promise a longer period for acknowledgement "
                           "should be reviewed. The requirement in paragraph 2.1 applies whatever the policy wording "
                           "says."),
        ("h1", "4  Monitoring and management information"),
        ("par", "4.1", "G", "Firms should record, for every claim, the date the first notice of loss was received and "
                           "the date it was acknowledged, so that timeliness can be measured accurately."),
        ("par", "4.2", "G", "Senior management should receive regular management information on acknowledgement "
                           "performance, analysed by channel, product line and location, together with the reasons for "
                           "any claims not acknowledged within the required time."),
        ("par", "4.3", "G", "Firms should take prompt action where performance falls short, for example during periods "
                           "of high claim volumes after a weather event. Plans for surge events should include "
                           "arrangements for acknowledging claims on time."),
        ("par", "4.4", "G", "Internal audit should periodically test the accuracy of the timeliness data and the "
                           "controls that produce the NISA-CT1 return."),
        ("h1", "5  The NISA-CT1 claims timeliness return"),
        ("par", "5.1", "G", "The NISA-CT1 return is an annual return covering the calendar year. It must be submitted by "
                           "31 March each year, as required by paragraph 2.4."),
        ("par", "5.2", "G", "The return collects the number of first notices of loss received in the year, the number "
                           "acknowledged within the required time, and the distribution of acknowledgement times, "
                           "analysed by channel and product line. Annex B lists the data items."),
        ("par", "5.3", "G", "The return should be approved by the individual responsible for claims before submission. "
                           "Firms should submit the return through the Authority's regulatory reporting channel."),
        ("h1", "6  Good and poor practice"),
        ("par", "6.1", "G", "In its supervisory work the Authority has seen the following examples of good practice:"),
        ("ul", ["acknowledging claims on the same day by the customer's preferred channel, with a named contact and a "
                "clear explanation of the next steps;",
                "dashboards showing acknowledgement performance by channel and location, reviewed daily by claims "
                "managers;",
                "surge plans that move staff to acknowledgement work as soon as a weather warning is issued;",
                "regular testing of brokers' arrangements for passing first notices of loss to the insurer."]),
        ("par", "6.2", "G", "It has also seen examples of poor practice:"),
        ("ul", ["measuring timeliness from the date a claim was keyed into the claims system rather than the date the "
                "first notice of loss was received;",
                "automated messages that confirm receipt but give no claim reference or contact point;",
                "policy wordings that promise acknowledgement within a period longer than the firm can justify;",
                "no management information on claims received through intermediaries."]),
        ("h1", "7  Worked examples"),
        ("par", "7.1", "G", "The period in paragraph 2.1 is counted in business days in the jurisdiction in which the claim "
                           "is handled, starting on the day after the first notice of loss is received. The table below "
                           "illustrates how the requirement applies."),
        ("table", "Table 1  Illustrative acknowledgement due dates", [
            ("First notice of loss received", "Claim handled in", "Public holidays in the period", "Acknowledge by"),
            ("Friday 4 October 2024", "United Kingdom", "None", "Tuesday 8 October 2024"),
            ("Thursday 19 December 2024", "United Kingdom", "None", "Monday 23 December 2024"),
            ("Tuesday 24 December 2024", "United Kingdom", "25 and 26 December 2024", "Monday 30 December 2024"),
            ("Wednesday 16 April 2025", "United Kingdom", "18 and 21 April 2025", "Tuesday 22 April 2025"),
            ("Wednesday 16 April 2025", "Norway", "17, 18 and 21 April 2025", "Wednesday 23 April 2025"),
        ], [42, 30, 50, 43]),
        ("par", "7.2", "G", "Where a first notice of loss is received outside business hours, for example through a web "
                           "portal on a Saturday, it is treated as received on the next business day."),

        ("h1", "8  Implementation"),
        ("par", "8.1", "G", "The requirement in paragraph 2.1 applies to every first notice of loss received on or after "
                           "the effective date shown on the front page of this circular."),
        ("par", "8.2", "G", "Firms should use the period before the effective date to review their processes, systems, "
                           "customer communications and policy documents, and to put in place the management "
                           "information described in Section 4."),
        ("par", "8.3", "G", f"Questions about this circular should be sent to {a['name']}, {a['title']}, at {a['email']}."),
    ]
    annexes = [
        ("pb",),
        ("h1", "Annex A  Definitions"),
        ("table", None, [
            ("Term", "Meaning in this circular"),
            ("First notice of loss", "The first notification of a claim to the firm, or to a person acting on its "
             "behalf, by any channel."),
            ("Acknowledgement", "A communication to the customer confirming receipt of the claim and containing the "
             "information described in paragraph 2.2."),
            ("Business day", "A day other than a Saturday, Sunday or public holiday in the jurisdiction in which the "
             "claim is handled."),
            ("Firm", "An insurer supervised by the Authority, including its branches outside the United Kingdom."),
        ], [42, 123]),
        ("h1", "Annex B  NISA-CT1 data items"),
        ("table", None, [
            ("Item", "Description"),
            ("T1", "Number of first notices of loss received in the year, by channel and product line"),
            ("T2", "Number acknowledged within the time required by paragraph 2.1"),
            ("T3", "Distribution of acknowledgement times in business days"),
            ("T4", "Number of first notices of loss not acknowledged within the required time, with the main reasons"),
            ("T5", "Number of complaints about delay in acknowledging a claim"),
        ], [18, 147]),
        ("h1", "Annex C  Summary of requirements"),
        ("table", None, [
            ("Paragraph", "Requirement"),
            ("2.1", req["2.1"]),
            ("2.4", req["2.4"]),
        ], [24, 141]),
        ("h1", "Annex D  Frequently asked questions"),
        ("h2", "Does an automated email count as an acknowledgement?"),
        ("p", "Only if it contains the information described in paragraph 2.2. An automated message that simply confirms "
              "receipt does not, on its own, meet the standard the Authority expects."),
        ("h2", "What if the customer cannot be contacted?"),
        ("p", "The firm should send the acknowledgement by the channel the customer used, or by post to the address it "
              "holds, and record the attempt."),
        ("h2", "Does the requirement apply to claims notified by a third party?"),
        ("p", "Where a third party notifies a claim against a policyholder, the firm should acknowledge the notification "
              "to the person who made it within the same period."),
        ("h2", "Do policy wordings need to be reissued?"),
        ("p", "Firms should review wordings that promise a longer period (paragraph 3.4) and correct them at the next "
              "convenient opportunity. The requirement in paragraph 2.1 applies in the meantime."),
        ("h1", "Annex E  Illustrative acknowledgement"),
        ("p", "The following wording is illustrative only. Firms may use their own wording provided the acknowledgement "
              "contains the information described in paragraph 2.2."),
        ("quote", ["Dear [customer name],",
                   "Your claim reference: [claim reference]",
                   "Thank you for telling us about your claim. We have received it and it is being dealt with by "
                   "[name or team], who you can contact on [telephone number] or at [email address].",
                   "What happens next: [short description of the next steps, for example whether we will arrange an "
                   "inspection or ask for estimates].",
                   "What we need from you: [list of information or documents, if any].",
                   "Please quote your claim reference whenever you contact us.",
                   "Yours sincerely,",
                   "[name, role]"]),
        ("p", "Where the acknowledgement is given by telephone, the firm should confirm the claim reference and the "
              "contact details in writing or by the customer's preferred channel."),
    ]
    summary = ("This circular sets a single standard for acknowledging a first notice of loss and introduces the "
               "annual NISA-CT1 claims timeliness return.")
    return {"blocks": blocks + annexes, "summary": summary}

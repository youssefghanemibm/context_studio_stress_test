"""Phrase banks for the NISA Annual Claims & Reserving Filing (LD003).

Every sentence is generic filing prose: it must not introduce a world fact (rule value, owner,
date, threshold, system link). World facts are written by ld003.py from the world model.
"""
from __future__ import annotations

SLOTS = {
    "period": ["during 2025", "over the reporting year", "in the year to 31 December 2025",
               "across the 2025 financial year", "throughout the year", "in the period under review"],
    "mgmt": ["management", "the Claims Executive", "senior claims management", "the first line",
             "the accountable executives", "line management"],
    "board": ["the Board", "the Executive Committee", "the Claims Executive"],
    "review": ["reviewed", "examined", "challenged", "tested", "assessed", "considered"],
    "found": ["found", "concluded", "noted", "observed", "confirmed"],
    "firm": ["the Society", "Corvane", "the firm", "Corvane Mutual"],
    "Firm": ["The Society", "Corvane", "The firm", "Corvane Mutual"],
    "improve": ["strengthened", "refined", "tightened", "simplified", "extended", "formalised"],
    "evidence": ["file reviews", "management information", "sample testing", "thematic reviews",
                 "control self-assessments", "second-line assurance work", "internal audit findings"],
    "customers": ["policyholders", "members", "customers", "claimants"],
    "material": ["material", "significant", "systemic", "reportable"],
    "basis": ["on a consistent basis", "on the same basis as the prior year", "consistently with prior filings",
              "using the methodology described in Section 4", "without change in approach"],
    "lines": ["motor", "home", "commercial property", "SME liability"],
    "region": ["the United Kingdom", "Norway", "Sweden", "Denmark", "the Nordic branches", "the UK book"],
    "team": ["the Reserving team", "the Actuarial function", "Financial Control", "Regulatory Reporting",
             "Claims Operations", "Compliance", "the Data & Analytics team"],
    "driver": ["repair cost inflation", "longer parts lead times", "higher labour rates in bodyshops",
               "claims frequency on weather-related perils", "the mix of bodily-injury claims",
               "settlement speed", "the cost of alternative accommodation", "salvage values"],
    "action": ["targeted file reviews", "refresher training for handlers", "updated reserving guidance",
               "revised management information", "additional quality checks",
               "changes to workflow and diary management", "closer supplier oversight"],
}

TOPICS: dict[str, list[str]] = {}

TOPICS["intro"] = [
    "This filing is submitted by {firm} under the National Insurance Supervisory Authority's annual claims and reserving reporting requirements.",
    "It covers the financial year ended 31 December 2025 and, where stated, events up to the date of filing.",
    "Figures are presented in pounds sterling; Nordic amounts are translated at the Group Ledger month-end rate unless a different basis is stated.",
    "Comparative commentary is provided where it helps the Authority understand movements, but this filing does not restate prior-year submissions.",
    "The filing has been prepared by Regulatory Reporting with contributions from Claims Operations, Reserving, Actuarial, Compliance and Financial Control.",
    "Where a figure depends on judgement, the judgement and its owner are identified in the relevant section.",
    "Totals may not add exactly because of rounding to one decimal place.",
    "Data are drawn from the claims administration platforms, the Group Ledger and the Claims Data Warehouse, and reconciled before use.",
    "The structure of the filing follows the Authority's template headings so that it can be read alongside the quarterly returns.",
    "Supporting working papers are retained by Regulatory Reporting and are available to the Authority on request.",
    "Material post-balance-sheet events are described in the section to which they relate.",
    "Section 9 sets out the governance applied to the preparation and approval of this filing.",
    "No part of this filing relies on unaudited estimates that have not been subject to second-line review.",
    "The filing should be read together with the annual report and accounts of {firm} for 2025.",
    "Terms with a defined meaning are listed in Appendix A.",
    "References to rules are to {firm}'s internal claims rule catalogue, cited by rule identifier and version.",
    "Where the filing refers to the 'Nordic branches' it means the Norwegian, Swedish and Danish branches together.",
    "The filing is signed by the Chief Financial Officer on behalf of the Board, as the Authority's template requires.",
]

TOPICS["business"] = [
    "{Firm} writes personal and small commercial property and casualty business in the United Kingdom and, through branches, in Norway, Sweden and Denmark.",
    "As a mutual, {firm} has no external shareholders; surplus is retained for the benefit of members.",
    "Business is distributed directly, through the digital self-service channel and through a limited panel of brokers.",
    "Personal motor and home remain the largest lines by claim count, while commercial property contributes a disproportionate share of claims cost.",
    "The Nordic branches write motor and home business under local-language policy terms and settle claims in local currency.",
    "There were no material changes to the lines of business written {period}.",
    "Underwriting appetite was broadly stable, with targeted rate action on lines affected by {driver}.",
    "The claims function operates from Leeds, Bristol, Glasgow, London and the three Nordic offices.",
    "Major and complex losses are handled by a specialist team in London regardless of where the policy was written.",
    "Recoveries and subrogation are handled in Bristol for the UK book and by the Nordic teams under the local regress process.",
    "Claims assessment uses a mix of employed Claims Assessors and panel loss adjusters.",
    "The contact centre in Glasgow takes first notifications by telephone for the UK book outside broker-handled schemes.",
    "Policyholder numbers were broadly stable, with modest growth in the Nordic home portfolio.",
    "The mix of business influences both claim frequency and the shape of claims development.",
    "Short-tail property claims settle quickly, whereas liability and bodily-injury claims can remain open for several years.",
    "Exposure to weather events is concentrated in the UK home and commercial property portfolios.",
    "Nordic home policies include cover for frost damage and snow load, which is not offered under the UK wordings.",
    "Legacy policy wordings remain in force for policies incepted under them, and claims are handled against the wording applicable at inception.",
]

TOPICS["environment"] = [
    "The claims environment {period} was shaped by {driver} and by {driver}.",
    "Repair networks reported continued pressure from {driver}, which lengthened some motor cycle times.",
    "Weather-related claims were within the range assumed in planning, although individual storm events produced short-lived peaks.",
    "Escape-of-water claims remained the single largest home peril by count.",
    "Bodily-injury claims experience was stable, with no evidence of a change in propensity to claim.",
    "Commercial property experience was influenced by a small number of large fire losses.",
    "Theft claims in the motor book remained concentrated in a limited number of vehicle models.",
    "Inflation in building materials eased during the second half of the year but remained above long-run averages.",
    "{Firm} monitored the effect of {driver} on average claim cost through management information.",
    "The Nordic portfolios experienced a normal winter season, with frost-damage claims in line with expectations.",
    "Third-party capture and credit-hire activity were monitored closely by the motor claims teams.",
    "Changes in the claims environment were reflected in reserving assumptions where they were judged to be persistent.",
    "Supply-chain conditions for replacement vehicles improved, which shortened hire periods.",
    "Average claim costs moved in line with the drivers described above and did not indicate a change in claims handling practice.",
]

TOPICS["handling"] = [
    "Claims handling performance is measured against service standards set out in the Claims Handling Manual and reported to {board}.",
    "{Mgmt} {review} handling quality through {evidence} {period}.",
    "Quality assurance reviews sample closed and open files across every handling team.",
    "Where reviews identified weaknesses, {mgmt} introduced {action}.",
    "File reviews focus on customer outcomes as well as procedural compliance.",
    "The quality framework distinguishes between errors that affect the customer and administrative omissions.",
    "Results of quality reviews are fed back to individual handlers and aggregated for team leaders.",
    "Service standards apply equally to UK and Nordic claims, adapted where local law requires.",
    "Handlers are supported by workflow diaries that prompt follow-up actions and reserve reviews.",
    "Complex or disputed claims are escalated to team leaders and, where necessary, to the Major & Complex Loss team.",
    "{Firm} continued to monitor handler caseloads to protect service levels during peak periods.",
    "Training {period} covered vulnerability, communication standards and the treatment of suspected fraud.",
    "The handling teams {improve} their approach to keeping customers informed during long-running claims.",
    "Second-line monitoring by Compliance {found} that handling standards were generally applied consistently.",
    "Exceptions identified through {evidence} were tracked to closure through the issues log.",
    "No {material} breaches of claims handling standards were reported to the Authority {period}.",
    "Cycle times for straightforward claims improved as digital notifications increased.",
    "Supplier performance against agreed service levels is reviewed in supplier governance meetings.",
]

TOPICS["fnol"] = [
    "First notification of loss is received by telephone, through the self-service portal, from brokers and through telematics alerts.",
    "Every notification creates a claim record with a mandatory data set before triage begins.",
    "Acknowledgement performance is measured from receipt of the notification to the issue of a written or electronic acknowledgement.",
    "Telephone notifications received out of hours receive a callback on the next business day.",
    "Digital notifications are acknowledged automatically, while telephone and broker notifications are acknowledged by the receiving team.",
    "{Firm} monitors acknowledgement timeliness and reports it to the Claims Executive.",
    "Notifications received through brokers carry the broker reference, which is used for reconciliation.",
    "Late notifications are reviewed to establish whether the delay has prejudiced the handling of the claim.",
    "Duplicate notifications are identified at intake and linked to the original claim.",
    "Telematics crash alerts generate a draft notification that is confirmed with the policyholder before a claim is opened.",
    "Customers can state a language preference at notification in the Nordic branches.",
    "Vulnerability indicators can be recorded at first notification and are visible to every subsequent handler.",
    "Notification volumes peaked after storm events, and temporary staffing was used to protect acknowledgement times.",
    "The intake process {improve} {period} to reduce re-keying between channels.",
]

TOPICS["assessment"] = [
    "Claims assessment is carried out by employed Claims Assessors and, for larger or specialist losses, by panel loss adjusters.",
    "Panel instructions are allocated by postcode area and current vendor load.",
    "Assessment reports are reviewed by handlers before a coverage decision is issued.",
    "Desk assessment from photographs and video is used where the nature and value of the loss allow it.",
    "Panel performance is measured against agreed service levels for inspection and reporting.",
    "{Mgmt} {review} the quality of assessment reports through {evidence}.",
    "Assessors record estimates in the claims platform so that reserves can be updated promptly.",
    "Re-inspection is required where an estimate rises materially after the first report.",
    "Nordic home claims above the local threshold require an on-site assessment.",
    "Conflicts of interest are declared and recorded before an assessor accepts an instruction.",
    "The Assessor Portal gives panel firms access to their instructions and allows reports to be uploaded.",
    "Photographic evidence standards are set out in the Claims Assessor Field Guide.",
]

TOPICS["settlement"] = [
    "Settlement practice aims to pay valid claims promptly and fairly, with clear explanations of any deduction.",
    "Excesses are deducted in accordance with the policy wording applicable to the claim.",
    "Interim payments are made once cover is confirmed where the claim is expected to run for some time.",
    "Payments are screened before release, and payee details are verified for new payees.",
    "Straight-through payment is used for eligible fast-track claims.",
    "Settlement letters explain how the amount was calculated and how to challenge it.",
    "Average settlement times are monitored by line and reported to the Claims Executive.",
    "Duplicate payment controls hold payments with the same payee, amount and claim for review.",
    "Cash settlement is offered where repair or replacement is not practical or not wanted by the customer.",
    "Settlement authority limits are set out in the claims rule catalogue and enforced in the claims platforms.",
    "Interest is added where payment is delayed beyond the agreed period.",
    "Settlement quality is included in the monthly file review programme.",
]

TOPICS["complaints"] = [
    "Complaints are recorded, acknowledged and investigated in line with the complaints policy.",
    "Root-cause analysis of complaints informs changes to process and communications.",
    "The largest complaint categories related to delays and to the outcome of the claim.",
    "Complaint volumes were reviewed against claim volumes to identify teams or processes needing attention.",
    "Complaints involving vulnerable customers are flagged and reviewed by team leaders.",
    "Upheld complaints led to remediation where the customer had suffered detriment.",
    "{Mgmt} {review} complaint themes and agreed actions with process owners.",
    "Final responses explain the customer's right to refer the complaint to an independent dispute resolution service.",
    "Complaint handling performance is subject to second-line monitoring by Compliance.",
    "Trends in complaints were consistent with the operational pressures described in this section.",
    "Communication standards were {improve} following themes identified in complaint reviews.",
]

TOPICS["vulnerable"] = [
    "{Firm} expects handlers to identify and respond to the needs of customers in vulnerable circumstances.",
    "Vulnerability can be temporary or permanent and may arise from health, life events, resilience or capability.",
    "Where vulnerability is recorded, the handler adapts communications and may extend timescales.",
    "Accessible formats and interpreter services are available on request.",
    "Training on vulnerability was refreshed for every customer-facing team {period}.",
    "Quality reviews include a specific check that vulnerability indicators were acted on.",
    "Customers in vulnerable circumstances can nominate a representative to deal with the claim.",
    "{Mgmt} monitors outcomes for customers with a vulnerability flag separately.",
    "Lessons from complaints involving vulnerable customers were shared with the handling teams.",
]

TOPICS["fraud"] = [
    "Counter-fraud activity is led by the Counter-Fraud & SIU team, which reports to the Chief Risk Officer.",
    "Claims are scored at triage by the Sentinel scoring engine, which produces a score from 0 to 100.",
    "A referral to SIU is made when the score reaches the referral threshold in force or when a handler identifies indicators of concern.",
    "Referred claims are triaged by SIU, which decides whether to investigate, return the claim to handling or close the referral.",
    "Investigations may involve document checks, interviews, open-source research and, where authorised, surveillance by the SIU partner.",
    "Fraud savings are recorded only where an investigation outcome is confirmed and the saving can be evidenced.",
    "{Firm} recognises that most claimants are honest and that counter-fraud work must not delay valid claims unnecessarily.",
    "The Claims Fraud Forum oversees fraud rules, Sentinel thresholds and SIU performance.",
    "Fraud indicators are reviewed periodically to remove indicators that no longer discriminate.",
    "Outcomes of SIU investigations are fed back to the scoring model owner to support recalibration.",
    "The counter-fraud framework was reviewed {period} in preparation for NISA Circular 2026/04.",
    "Customer treatment during an investigation is monitored through complaints and file reviews.",
    "Linked-claims analysis is used to identify organised activity across products and regions.",
    "SIU case files are retained in the SIU Case Manager with a full audit trail.",
    "Training on fraud awareness is mandatory for every handler and assessor.",
    "Second-line review by Compliance considered the fairness of referral and investigation practice.",
]

TOPICS["recoveries"] = [
    "Recovery potential is identified at triage and reviewed when liability becomes clear.",
    "UK recoveries are pursued by the Recoveries & Subrogation team in Bristol, with panel solicitors used where litigation is needed.",
    "Nordic recoveries follow the regress process with the counterparty insurer.",
    "Expected recoveries are recorded separately from case reserves and netted only when received.",
    "Recovery correspondence is issued in the language of the counterparty where required.",
    "Limitation dates are diarised to ensure that recoveries are not lost through delay.",
    "Salvage is disposed of through the salvage partner, and proceeds are posted to the claim.",
    "The policyholder's excess is refunded once a full recovery has been made.",
    "Recovery performance is reported to the Claims Executive.",
    "{Mgmt} {review} write-off decisions on recoveries against the authority framework.",
]

TOPICS["reserving"] = [
    "Case reserves are set by handlers on the basis of the information available and reviewed whenever new information is received.",
    "Reserves are held by reserve type, including indemnity, fees and expenses, and are recorded as movements with reason codes.",
    "Reserve authority limits ensure that large reserves are approved at an appropriate level of seniority.",
    "Tier-3 claims are subject to more frequent reserve reviews than other claims.",
    "{Team} {review} the adequacy of case reserves through {evidence}.",
    "Large reserve increases in a single movement require team leader review.",
    "A month-end reserve snapshot is taken for financial reporting and retained.",
    "Nordic reserves are held in local currency and translated for reporting at the month-end rate.",
    "Reserves are reduced to zero on final settlement and a settlement close movement is recorded.",
    "Reopened claims require a new reserve within a short period of reopening.",
    "The Reserving Committee approves reserving policy and reserves above the Claims Director limit.",
    "Case reserve strength is monitored by comparing reserves with eventual settlement amounts.",
    "Reserving guidance was {improve} {period} for bodily-injury and business-interruption claims.",
    "Movements above the large loss notification threshold are notified to Reinsurance within the required period.",
    "Reserve adequacy testing did not identify any {material} weakness at the year end.",
]

TOPICS["ibnr"] = [
    "IBNR is estimated by the Actuarial function for each reserving class using paid and incurred development methods.",
    "Chain-ladder methods are used for mature accident years, while Bornhuetter-Ferguson methods are preferred for recent years.",
    "Initial expected loss ratios are informed by pricing assumptions and recent experience.",
    "Large losses are projected separately so that they do not distort the attritional development patterns.",
    "Development factors are selected with judgement, taking account of changes in claims handling and settlement speed.",
    "The IBNR estimate includes provision for claims incurred but not yet reported and for development on reported claims.",
    "Claims handling expenses are provided for through an unallocated loss adjustment expense reserve.",
    "Results are reviewed by the Chief Actuary and presented to the Reserving Committee.",
    "Methods and assumptions were applied {basis}.",
    "Allowance is made for the expected effect of inflation on unsettled claims.",
    "Nordic classes are projected in local currency before translation.",
    "Back-testing of prior projections showed development broadly in line with expectation.",
    "Where data were affected by operational changes, adjustments were documented and reviewed.",
    "The selected IBNR represents a best estimate without explicit margins for prudence.",
    "Data used in the projections were reconciled to the Group Ledger before use.",
    "Sensitivity of the IBNR to key assumptions is described qualitatively in Section 4.6.",
]

TOPICS["uncertainty"] = [
    "Reserve estimates are inherently uncertain, and actual outcomes will differ from the estimates.",
    "The main sources of uncertainty are bodily-injury inflation, the outcome of large commercial losses and the speed of settlement.",
    "Uncertainty is greater for recent accident years, where little development has been observed.",
    "Changes in claims handling processes during system migration may affect development patterns.",
    "Legal and regulatory developments could change the cost of liability claims.",
    "Weather events after the year end are not reflected in the technical provisions at 31 December 2025.",
    "The Actuarial function considered alternative assumptions and methods when forming its view of the range of outcomes.",
    "Uncertainty is communicated to the Board through the Chief Actuary's annual report.",
    "No allowance has been made in the technical provisions for events after the balance sheet date.",
    "Sensitivity analysis focuses on assumptions where reasonable alternatives would change the estimate materially.",
]

TOPICS["development"] = [
    "The development tables show cumulative paid claims by accident year and development year.",
    "Amounts are shown gross of reinsurance and in pounds sterling.",
    "Nordic amounts are translated at year-end rates to remove the effect of currency movements on the triangles.",
    "Development in 2025 was broadly consistent with prior patterns for short-tail classes.",
    "Liability development remains slower and more variable than the property classes.",
    "Individual large losses can produce visible steps in the development of commercial property.",
    "The triangles are produced from the Claims Data Warehouse and reconciled to the ledger.",
    "Accident years before 2016 are shown in aggregate.",
    "Development factors derived from these tables inform, but do not determine, the actuarial selections.",
    "Changes in settlement speed have a visible effect on the early development periods.",
]

TOPICS["returns"] = [
    "Regulatory returns are prepared by Regulatory Reporting in the NISA Reporting Hub from controlled data extracts.",
    "Each return has a named preparer, reviewer and signatory.",
    "Data used in returns are reconciled to the Group Ledger and to the claims platforms before submission.",
    "Reconciliation breaks above tolerance are investigated and resolved or explained before sign-off.",
    "Return calendars are maintained by Regulatory Reporting and monitored weekly.",
    "Controls over return preparation are tested annually by the second line.",
    "Data lineage for key return fields is documented from source system to return cell.",
    "Changes to interfaces that feed returns are assessed for reporting impact before release.",
    "Any late or corrected submission is reported to the Authority with an explanation.",
    "Return working papers are retained for inspection by the Authority.",
    "The data quality framework sets standards for completeness, accuracy and timeliness.",
    "Data owners attest to the quality of the data supplied for each return.",
]

TOPICS["regchange"] = [
    "Regulatory change is tracked by Compliance in a register that records requirements, owners and implementation status.",
    "Each new circular is assessed for its effect on rules, processes, systems and customer communications.",
    "Implementation plans are approved by the accountable executive and monitored by Compliance.",
    "Changes to claims rules are recorded in the rule catalogue with version history and approvals.",
    "Where systems must change, the change is delivered in both the legacy and target platforms during migration.",
    "Compliance confirms that each requirement has been implemented before the effective date.",
    "Staff communications and training are prepared for every customer-facing change.",
    "The register is reviewed regularly at executive level.",
    "Post-implementation reviews confirm that changes have operated as intended.",
    "{Firm} engages with the Authority's consultations where proposals affect its members.",
]

TOPICS["resilience"] = [
    "Important business services for claims include first notification, claims payment and complaint handling.",
    "Impact tolerances are set for disruption to claims payments in line with NISA Circular 2025/02.",
    "Scenario testing considered loss of the payments interface, loss of a processing site and failure of a key supplier.",
    "Mapping of people, processes, technology and suppliers supports each important business service.",
    "Vulnerabilities identified through scenario testing were added to the remediation plan.",
    "Operational resilience is overseen at executive level and reported to the Board.",
    "The annual self-assessment is approved by the Board.",
    "System migration activity is assessed for its effect on resilience before each wave.",
    "Manual workarounds are documented for critical payment processes.",
]

TOPICS["retention"] = [
    "Claim records are retained in accordance with the claims data retention rule and destroyed securely at the end of the period.",
    "NISA Circular 2025/11 introduces a longer retention period for bodily-injury claims from 1 January 2026.",
    "Production personal data is not used in test environments.",
    "Retention schedules apply to documents and images as well as to structured claim data.",
    "The Data Protection Officer monitors adherence to retention schedules.",
    "Archived claims remain retrievable for complaints, litigation and regulatory requests.",
    "Data minimisation principles are applied to new data fields introduced through system change.",
]

TOPICS["programme"] = [
    "Programme Skerry is replacing the CLARA claims platform with Claims Hub.",
    "Claims Hub is built as a set of Spring services on OpenShift, integrated with the existing ledger, payments and reporting systems.",
    "Migration is delivered in waves, each preceded by rehearsals and reconciliation of migrated claims.",
    "During migration, rules are maintained in both platforms so that customers are treated consistently.",
    "Reserve data migrated to Claims Hub are reconciled to CLARA before each wave is accepted.",
    "Regulatory reporting continues to draw on CLARA for unmigrated portfolios.",
    "The Programme Skerry Steering Committee approves scope, budget and cut-over decisions.",
    "{Firm} has engaged an external systems integrator to support delivery.",
    "Interface changes are subject to impact assessment across downstream consumers, including regulatory reporting.",
    "Lessons from incidents in 2025 were incorporated into change control for interfaces feeding returns.",
    "Data quality issues identified during migration rehearsals are tracked to closure.",
    "The Authority is kept informed of migration milestones through supervisory meetings.",
    "Decommissioning of CLARA will follow the final migration wave and a period of read-only access.",
    "Business readiness activities include training, process updates and hypercare support.",
]

TOPICS["governance"] = [
    "The Board is responsible for the adequacy of technical provisions and for the accuracy of this filing.",
    "The three-lines-of-defence model applies to claims, reserving and regulatory reporting.",
    "The Reserving Committee reviews reserving policy, authority limits and the year-end reserve recommendation.",
    "Internal audit reviewed reserving and regulatory reporting controls {period}.",
    "Findings from internal audit were tracked to closure and reported to the Board.",
    "Accountable executives attest to the completeness and accuracy of the information in their areas.",
    "The Chief Actuary provides an independent opinion on the technical provisions.",
    "Compliance provides assurance over conduct and regulatory requirements in claims.",
    "Conflicts of interest are managed through declarations and segregation of duties.",
    "Management information is reviewed at executive and Board level.",
    "The filing was reviewed by the Executive Committee before Board approval.",
    "Key judgements in this filing were discussed with the external auditors.",
]

# Short headings used for filler subsections (per topic)
SUBHEADS = {
    "handling": ["Quality assurance", "Service standards", "Caseload management", "Training and competence",
                 "Supplier oversight", "Escalation"],
    "fnol": ["Channels", "Acknowledgement", "Intake controls", "Out-of-hours service"],
    "assessment": ["Panel management", "Desk assessment", "Assessment quality"],
    "settlement": ["Payments", "Settlement communications", "Authority and controls"],
    "complaints": ["Complaint themes", "Root-cause analysis", "Remediation"],
    "vulnerable": ["Identification", "Adapted handling", "Monitoring outcomes"],
    "fraud": ["Framework", "Referral and triage", "Investigation", "Customer treatment", "Oversight"],
    "recoveries": ["Identification", "Pursuit", "Salvage", "Nordic regress"],
    "reserving": ["Case reserving", "Authority limits", "Reserve reviews", "Large losses"],
    "ibnr": ["Methods", "Assumptions", "Large losses", "Expenses", "Validation"],
    "uncertainty": ["Sources of uncertainty", "Sensitivities"],
    "development": ["Commentary"],
    "returns": ["Preparation", "Reconciliation", "Controls", "Data quality"],
    "regchange": ["Register", "Implementation", "Assurance"],
    "resilience": ["Important business services", "Scenario testing"],
    "retention": ["Retention schedules", "Test data"],
    "programme": ["Delivery approach", "Migration controls", "Reporting continuity", "Business readiness"],
    "governance": ["Board oversight", "Assurance", "Attestations"],
    "business": ["Portfolio", "Distribution", "Operations"],
    "environment": ["Claims environment"],
    "intro": ["Scope", "Basis of preparation"],
}


def sentence(deck, topic: str) -> str:
    return deck.fill(deck.pick(TOPICS[topic]), SLOTS)


def paragraph(deck, topic: str, n_min: int = 3, n_max: int = 6, extra_topics: tuple = ()) -> str:
    n = deck.randint(n_min, n_max)
    out = []
    seen = set()
    pool = [topic] * 4 + list(extra_topics)
    for _ in range(n * 3):
        if len(out) >= n:
            break
        t = deck.choice(pool)
        s = sentence(deck, t)
        if s in seen:
            continue
        seen.add(s)
        out.append(s)
    return " ".join(out)


# ---------------------------------------------------------------------------------------------
# Compositional sentences: topic subject + generic predicate (adds variety to long sections)
# ---------------------------------------------------------------------------------------------

SUBJECTS = {
    "intro": ["The scope of this filing", "The basis of preparation", "The reconciliation of source data",
              "The presentation of comparative information", "The treatment of rounding differences",
              "The translation of Nordic amounts", "The classification of claims by product",
              "The allocation of claims to reporting periods", "The identification of post-balance-sheet events",
              "The use of management judgement"],
    "business": ["The mix of business", "The distribution model", "The Nordic branch portfolios",
                 "The UK personal lines book", "The commercial property account", "The SME liability account",
                 "Broker-introduced business", "The geographic spread of risks", "Retention of members",
                 "The legacy wording population"],
    "environment": ["The cost of vehicle repairs", "Weather-related claims activity", "The cost of building materials",
                    "Bodily-injury settlement values", "Escape-of-water frequency", "Motor theft experience",
                    "Replacement vehicle availability", "Labour costs in the repair networks",
                    "Large commercial fire losses", "Seasonal claim patterns"],
    "handling": ["Handling quality", "Diary management", "The management of handler caseloads",
                 "Escalation of complex claims", "Customer contact standards", "The quality assurance framework",
                 "Supplier oversight", "Handler training and competence", "File documentation standards",
                 "The management of long-running claims", "Peak-period resourcing", "Claim closure practice"],
    "fnol": ["First-notification intake", "The capture of the mandatory data set", "Acknowledgement timeliness",
             "Broker notification handling", "The telematics alert process", "Duplicate-claim checking",
             "Late-notification review", "Out-of-hours notification handling", "The self-service portal journey",
             "Recording of language preferences"],
    "assessment": ["Panel loss adjuster performance", "Desk assessment practice", "The quality of assessment reports",
                   "Re-inspection practice", "Assessor conflict-of-interest controls", "Panel allocation",
                   "Photographic evidence standards", "The use of video assessment", "Nordic on-site assessments",
                   "Assessor estimate accuracy"],
    "settlement": ["Settlement communications", "Payment screening", "Payee verification", "Interim payment practice",
                   "Fast-track settlement", "Cash settlement practice", "Duplicate payment controls",
                   "The calculation of excess deductions", "Interest on delayed payments", "Settlement authority controls"],
    "complaints": ["Complaint recording", "Complaint root-cause analysis", "Final response quality",
                   "Remediation of upheld complaints", "Complaint trend reporting", "Complaints involving delay",
                   "Complaints about claim outcomes", "Complaint handling timeliness"],
    "vulnerable": ["The identification of vulnerability", "Adapted communications", "The use of nominated representatives",
                   "Outcome monitoring for vulnerable customers", "Vulnerability training",
                   "Support for customers after bereavement", "The handling of temporary vulnerability"],
    "fraud": ["Referral handling", "SIU triage", "The use of Sentinel scores", "Investigation practice",
              "The recording of fraud savings", "Customer communication during investigations",
              "The management of SIU partner instructions", "Fraud indicator maintenance", "Linked-claims analysis",
              "Counter-fraud training", "Case closure coding", "Feedback from investigation outcomes",
              "Oversight of referral fairness", "The counter-fraud control framework"],
    "recoveries": ["Recovery identification", "Subrogation pursuit", "Salvage disposal", "The Nordic regress process",
                   "Limitation diary management", "Recovery write-off decisions", "Panel solicitor performance",
                   "Excess refunds after recovery", "Recovery correspondence"],
    "reserving": ["Case reserve adequacy", "Reserve authority control", "Tier-3 reserve reviews",
                  "Large reserve increases", "Reserve reason coding", "Month-end reserve snapshots",
                  "Reserve close-down at settlement", "Reserving for reopened claims", "Nordic reserve translation",
                  "Large loss notification", "Expense reserving", "Legal reserving for litigated claims"],
    "ibnr": ["The selection of development factors", "The choice of projection method", "Initial expected loss ratios",
             "The separate projection of large losses", "The ULAE provision", "The treatment of inflation",
             "Back-testing of prior projections", "The data used in projections", "The Nordic class projections",
             "The documentation of actuarial judgements"],
    "uncertainty": ["Bodily-injury inflation", "The outcome of large commercial losses", "Settlement speed",
                    "Legal and regulatory change", "Changes in handling processes", "The most recent accident years",
                    "Currency movements", "Model and parameter risk"],
    "development": ["Short-tail development", "Liability development", "Large-loss development",
                    "Early development periods", "Nordic development", "Paid-to-incurred ratios"],
    "returns": ["Return preparation", "Data lineage", "Reconciliation to the ledger", "Return sign-off",
                "The returns calendar", "Data owner attestations", "Interface change assessment",
                "Working paper retention", "Data quality monitoring"],
    "regchange": ["The regulatory change register", "Impact assessment of new circulars", "Rule catalogue updates",
                  "Implementation tracking", "Staff communications on regulatory change", "Post-implementation review",
                  "Dual running of rules across platforms"],
    "resilience": ["Mapping of important business services", "Scenario testing", "Payment workarounds",
                   "Supplier resilience", "The annual self-assessment", "Recovery planning for claims payment"],
    "retention": ["Retention scheduling", "Secure destruction", "Archive retrieval", "Test data management",
                  "Data minimisation"],
    "programme": ["Migration rehearsal", "Reconciliation of migrated reserves", "Dual maintenance of rules",
                  "Interface impact assessment", "Business readiness", "Hypercare support", "Cut-over governance",
                  "Data quality remediation", "Decommissioning planning", "Training for the new platform"],
    "governance": ["Board oversight of reserving", "Second-line assurance", "Internal audit coverage",
                   "Executive attestations", "Conflict-of-interest management", "Management information",
                   "The three-lines-of-defence model", "Committee reporting"],
}

PREDICATES = [
    "was reviewed by {team} {period}",
    "remained within the risk appetite approved by the Board",
    "was the subject of a thematic review {period}",
    "is monitored through management information presented to {board}",
    "was {improve} following findings from {evidence}",
    "operated as intended throughout the year, based on {evidence}",
    "is supported by documented procedures and targeted training",
    "was tested by the second line, and the minor findings raised have since been closed",
    "is reported to {board} together with the related risk indicators",
    "will be reassessed as part of the migration to Claims Hub",
    "was not adversely affected by the system changes described in Section 8",
    "has a named owner in the first line and an oversight owner in the second line",
    "was discussed with the Authority during routine supervisory meetings",
    "is covered by the control self-assessment completed {period}",
    "showed no {material} exceptions in the samples examined",
    "was identified as an area for continued attention in the coming year",
    "is aligned with the expectations set out in the Authority's circulars",
    "benefited from the {action} introduced {period}",
    "was considered by {mgmt} when setting priorities for 2026",
    "is described in more detail in the relevant procedure documents",
    "was included in the scope of internal audit work {period}",
    "depends on accurate and timely data from the claims platforms",
    "is applied in the same way in the UK and the Nordic branches, subject to local law",
    "continued to improve, although further work is planned",
    "was evidenced in the working papers supporting this filing",
]

_PRED_TAILS = ["", "", "", "; the results were shared with the teams concerned",
               ", and actions are tracked in the issues log",
               "; no customer detriment was identified",
               ", with progress reported to the Claims Executive"]


def composed(deck, topic: str) -> str:
    subj = deck.pick(SUBJECTS[topic])
    pred = deck.fill(deck.pick(PREDICATES), SLOTS)
    tail = deck.choice(_PRED_TAILS)
    if tail and ";" in pred:
        tail = ""
    return f"{subj} {pred}{tail}."


def sentence(deck, topic: str) -> str:  # noqa: F811  (replaces the simple version above)
    if topic in SUBJECTS and deck.random() < 0.5:
        return composed(deck, topic)
    return deck.fill(deck.pick(TOPICS[topic]), SLOTS)


for _k in list(SLOTS):
    _cap = _k[0].upper() + _k[1:]
    if _cap not in SLOTS:
        SLOTS[_cap] = [v[0].upper() + v[1:] for v in SLOTS[_k]]

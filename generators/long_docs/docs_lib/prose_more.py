"""More phrase banks for LD018-LD020 and LD024-LD029 (new bank names, so LD013-LD017/LD030 are unaffected).

Same rules as prose.py: generic statements only. No numbers, thresholds, owners, dates, system links or
program-table links. Slots ({step}, {team}, {role}, {phase}, {job}, {env}, {area}) take values the builder passes
from the world model; templates only assert generic practice about them.
"""
from __future__ import annotations

from .prose import BANKS, _lines

BANKS["opm2"] = _lines("""
The model is deliberately simple: one accountable role per stage, a small number of responsible teams, and clear points at which work changes hands.
Responsibilities that used to be held informally by long-serving colleagues are now written into role descriptions.
Team boundaries follow the customer journey, so that a claim moves through as few queues as possible.
Each stage owner chairs a short monthly review of performance, open risks and improvement actions for the stage.
Process documentation is held in the claims standards library and is updated when the operating model changes.
The operating model distinguishes between work that must be done by a particular role and work that any trained handler can do.
Capacity planning is carried out jointly by Claims Operations and the specialist teams so that peaks are absorbed without loss of service.
Where a team supports more than one region, the team leader agrees local priorities with the regional leads.
Training plans are aligned with the role descriptions and refreshed when responsibilities change.
Exceptions to the standard process are recorded on the claim with the reason and the approver.
The re-organisation did not change the process steps themselves; it changed who is accountable for some of them.
Claims handlers continue to own the customer relationship while specialist teams contribute to the claim.
The model is intended to make accountability visible to colleagues, auditors and the regulator.
Every process step has a named fallback role for periods of absence or vacancy.
Where responsibilities overlap during the transition, the stage owner decides which team leads.
Work queues are monitored daily and rebalanced across teams when backlogs build up.
The operating rhythm combines daily huddles in each team with weekly and monthly reviews at stage level.
Lessons from complaints and quality reviews are fed back to the stage owner and the relevant team leaders.
Operational risk events are logged by the team that identifies them and reviewed by the stage owner.
The model assumes that most decisions are taken by the person handling the claim, within clearly defined authority.
Decision rights are delegated as far as practicable, with escalation reserved for exceptions.
The operating model does not change the authority limits set out in the claims authority framework.
Interfaces with Finance, Risk and Technology are managed through the forums described in this document.
The model will be refined as experience is gained with the new reporting lines.
Shared mailboxes and queues have been renamed to match the new team names where this was practical.
Colleagues affected by the re-organisation were briefed by their new line managers before the effective date.
Where a role holder changes, the hand-over is recorded and open actions are transferred explicitly.
The model applies equally to claims handled on the legacy platform and to claims migrated to the new platform.
Responsibilities for data quality sit with the team that captures or changes the data.
Customer outcomes are the primary measure of whether the operating model is working.
""")

BANKS["step"] = _lines("""
{step} is carried out by {team} in line with the procedures in the claims standards library.
The accountable role for {step} reviews performance against the service level each month.
Work for {step} is allocated from the team queue; urgent items are flagged by the handler who creates them.
Exceptions arising in {step} are escalated to the team leader in {team} before they reach the stage owner.
Quality sampling for {step} is carried out by {team} and the results are reported to the stage owner.
{team} keeps a desk procedure for {step} that reflects the current systems and authority limits.
Where {step} cannot be completed because information is missing, the claim is diarised and the customer is contacted.
Hand-offs into and out of {step} are recorded on the claim so that the next team can pick up the work without delay.
Where {step} is supported by both platforms during the transition, the procedure is the same on either platform.
Changes to how {step} is performed are agreed with the stage owner before they are introduced.
Training for {step} is delivered to new joiners in {team} as part of their induction.
{team} reports volumes and backlogs for {step} in the weekly operational review.
Decisions taken in {step} are recorded with the reason, so that they can be explained to the customer if asked.
The consulted teams for {step} are contacted before a decision is taken where the procedure requires it.
Informed teams receive a notification once {step} is complete; they do not need to approve it.
Any complaint about {step} is routed to the complaints team and copied to the team leader in {team}.
Absence cover for {step} is arranged within {team} first and then from the wider stage.
The procedure for {step} includes checks that protect vulnerable customers.
{step} relies on accurate data from the preceding step; errors are corrected at source rather than worked around.
MI for {step} is produced from the system of record for the claim and is not maintained manually.
{team} is expected to identify recurring causes of rework in {step} and propose improvements.
Peaks in demand for {step}, for example after severe weather, are managed through the surge plan.
""")

BANKS["role"] = _lines("""
The {role} is accountable for the outcomes of the processes listed against the role in the RACI.
The {role} sets priorities for the teams within the role's remit and resolves conflicts between them.
The {role} represents the function at the forums listed in section 3 and reports on performance and risk.
The {role} ensures that procedures, training and controls are kept up to date for the processes the role owns.
The {role} approves exceptions within the role's delegated authority and escalates those above it.
The {role} is responsible for the development and wellbeing of the colleagues in the role's teams.
The {role} works with the Claims Hub product team to make sure new functionality supports the processes the role owns.
The {role} maintains the risk and control self-assessment for the role's area.
The {role} contributes to the annual planning cycle, including budgets, headcount and improvement initiatives.
The {role} ensures that regulatory requirements relevant to the role's processes are understood and met.
The {role} reviews management information for the role's area and acts on adverse trends.
The {role} owns the relationship with any vendors instructed by the role's teams.
The {role} nominates a deputy who can take decisions in the role holder's absence.
The {role} is consulted on changes to systems and processes that affect the role's teams.
The {role} supports internal audit and second-line reviews of the role's area.
The {role} promotes good customer outcomes and fair treatment in all of the role's processes.
The {role} makes sure that hand-offs with other teams are understood and working as designed.
The {role} participates in the incident and business continuity arrangements for claims.
""")

BANKS["kpi"] = _lines("""
Performance indicators are reported monthly, with weekly operational views for team leaders.
Indicators are defined once, centrally, so that every team measures the same thing in the same way.
Targets are set annually by the stage owner and approved by the Claims Director.
Each indicator has a named owner who explains variances and agrees corrective actions.
Trends are more important than single-month results; a sustained adverse trend triggers a review.
Indicators cover timeliness, quality, customer outcomes, cost and control effectiveness.
Where data comes from both platforms during the transition, the two sources are combined before reporting.
Definitions of indicators are held with the MI catalogue maintained by Data & Analytics.
Quality indicators are based on independent file reviews rather than self-assessment.
Customer feedback is reported alongside operational indicators so that the two can be compared.
Indicators that are no longer useful are retired rather than left in the pack.
New indicators are piloted for a period before targets are attached to them.
""")

BANKS["test2"] = _lines("""
Testing is risk-based: the depth of testing for a capability reflects the impact of it failing in production.
Every test phase has written entry and exit criteria that are agreed before the phase starts.
Test evidence is retained in the test management tool and linked to the requirement and the build under test.
Defects found late in the lifecycle are analysed to understand why earlier phases did not find them.
Automated tests are treated as production code: they are reviewed, versioned and maintained by the squads.
Business users take part in test design so that scenarios reflect real claims rather than idealised ones.
The regression pack grows with each release and is pruned when tests become redundant.
Testing of business rules uses decision tables that show each combination of inputs and the expected outcome.
Performance tests are run against production-like volumes and data distributions.
Security testing is performed by an independent team and findings are tracked to closure.
Test environments are refreshed on a published schedule so that squads can plan around them.
No production data is used in non-production environments unless it has been masked in line with the data protection policy.
Where a test cannot be automated, the manual script is written so that a different tester would reach the same result.
Test progress is reported weekly using the same measures in every phase.
The test approach for each release is summarised in a short test plan that refers back to this strategy.
Interfaces with external parties are tested first with stubs and then end to end with the parties themselves.
A defect is not closed until the fix has been retested in the environment where it was found.
Exploratory testing complements scripted testing and is time-boxed with clear charters.
Accessibility checks form part of the acceptance criteria for every customer-facing screen.
The test strategy is reviewed after each migration wave and updated with the lessons learned.
Test data is designed to cover edge cases such as backdated notifications, currency conversion and reopened claims.
Test results for regulatory requirements are reviewed by Compliance before the release is approved.
Reconciliation tests compare outputs from the legacy and target platforms for the same inputs.
Squads own the quality of their services; the test team provides frameworks, coaching and independent assurance.
Service virtualisation is used where a dependency is not available or is costly to call in test.
Contract tests run in the build pipeline and fail the build when a breaking change is detected.
Operational acceptance testing confirms that support teams can monitor, operate and recover the service.
Release readiness is assessed against the exit criteria and recorded in the release decision log.
Known defects accepted for release have a documented workaround and a target fix date agreed with the product owner.
Test coverage reports show which requirements have passed, failed or not yet been tested.
""")

BANKS["phase"] = _lines("""
The {phase} phase is owned by the squad or team named in the test phase summary and reported in the weekly test report.
Entry to {phase} requires the previous phase's exit criteria to be met or formally waived.
Defects raised in {phase} are triaged at the daily defect meeting.
The scope of {phase} for each release is confirmed in the release test plan.
Evidence from {phase} is reviewed by the test lead before the phase is signed off.
Where {phase} depends on an external party, the dates are agreed with that party well in advance.
{phase} is repeated in full for major releases and selectively for minor ones, based on impact analysis.
Results from {phase} are presented at the release readiness review.
Test cases for {phase} are traced to requirements or acceptance criteria.
{phase} uses the environment allocated in the environment plan; changes to the allocation are agreed with the environment manager.
The exit report for {phase} summarises coverage, open defects and residual risks.
Automation is used in {phase} wherever the tests are expected to be repeated.
""")

BANKS["model2"] = _lines("""
The model is used to prioritise claims for human review; it does not make decisions about customers on its own.
Model inputs are limited to data that Corvane is permitted to use for fraud prevention and that is available at the point of scoring.
The model's outputs are explainable at claim level: the main contributing factors are shown to the analyst alongside the score.
Changes to the referral cut-off are a business decision, informed by the model's performance but not determined by it.
Monitoring compares the distribution of scores over time to detect shifts in the claims population or the data feeds.
Feedback from SIU investigations is used as the outcome label for performance monitoring and future calibration.
The model documentation describes the purpose, data, method, limitations and approved uses of the model.
The vendor provides technical documentation of the scoring engine; Corvane remains accountable for how the model is used.
Model risk is assessed using the corporate model risk framework and recorded in the model inventory.
Any use of the score outside the approved purpose requires prior approval through the model governance process.
Bias testing checks that the model does not produce unjustified differences in outcomes between groups of customers.
Overrides of the model by analysts are recorded with a reason and reviewed periodically.
Data quality issues in the input feeds are treated as model incidents and investigated by the model owner.
The champion model in production is only replaced after a challenger has been validated and approved.
Recalibration follows a documented procedure, including back-testing, sign-off and controlled deployment.
Model performance is reported to the governing forum with commentary on any adverse movements.
The model inventory records the model owner, validator, approval status and next review date.
Access to model configuration in production is restricted and every change is logged.
The scoring service is monitored for availability and response time as well as for statistical performance.
Limitations of the model are communicated to users so that the score is not over-relied upon.
Outcome labels are subject to delay, because investigations take time; monitoring takes account of this lag.
The model is not used to price policies or to make underwriting decisions.
Customers referred to SIU are treated fairly and in line with the customer-notice requirements.
Model documentation is version-controlled and stored with the validation evidence.
Material model changes are notified to the Chief Risk Officer before deployment.
Thresholds are held as effective-dated configuration, so the threshold applied to any claim can be reconstructed.
""")

BANKS["valid"] = _lines("""
The validation was performed independently of the model owner and the vendor, by staff with no role in developing or operating the model.
Validation work comprised a review of documentation, replication of key performance measures and targeted testing of model behaviour.
The validator had access to the scored population, the outcome labels and the configuration in force during the review period.
Findings are rated according to the model risk framework and assigned an owner and a target date.
The validator relied on data extracted by the model owner; completeness was tested by reconciliation to the scoring logs.
Conceptual soundness was assessed by reviewing the choice of features and their relationship to known fraud indicators.
Outcome analysis compared predicted risk with observed investigation outcomes over the review period.
Stability analysis compared the distribution of scores and key inputs between the development and recent periods.
Sensitivity testing examined how the score responds to changes in individual inputs.
The validator reviewed the implementation to confirm that production scores match the documented specification.
Benchmarking against simpler approaches was used to judge whether the model's complexity is justified.
The review covered the use of the model in the referral process as well as the model itself.
Management's responses to the findings are included in the action plan at the end of this report.
The validator considered whether the limitations of the model are understood by its users.
The review assessed the quality of model monitoring and the adequacy of escalation when monitoring triggers are breached.
Data lineage from the claims platforms to the scoring engine was traced for a sample of claims.
The validator confirmed that changes since the previous validation had been approved and documented.
Observations that do not warrant a formal finding are recorded as recommendations for good practice.
The validation opinion is based on the evidence available at the time of the review.
The validator recommends that the next validation is planned in line with the model's risk tier.
Testing of fairness considered whether proxy variables could produce unjustified differences in treatment.
The review of explainability examined whether analysts can understand why a claim received its score.
The validator reproduced a sample of scores from raw inputs and obtained the same results.
Governance arrangements were assessed against the corporate model risk policy.
Documentation was found to be generally clear, with some gaps noted in the findings section.
The validator discussed preliminary observations with the model owner before finalising this report.
Where the validator's results differed from those of the model owner, the differences were traced to their source.
The scope of testing was proportionate to the model's risk tier and to the materiality of the change under review.
Evidence supporting each conclusion is retained in the validation file and is available to Internal Audit.
Data extracts used by the validator were taken independently from the production systems where practicable.
The validator considered whether the model remains appropriate for the population to which it is now applied.
Model behaviour at the extremes of the score range was examined separately from behaviour around the threshold.
The validator examined how the model treats claims with missing inputs and whether this is documented.
The review considered the operational controls around the scoring service as well as the statistical model.
Comparisons with the previous calibration were used to understand the effect of the recalibration.
The validator reviewed how overrides and analyst feedback are captured and whether they are used in monitoring.
Assumptions made by the vendor were identified and assessed for their relevance to Corvane's claims portfolio.
The validator assessed whether the documentation would allow a competent third party to understand the model.
Testing included claims from each region and each main product line.
The validator confirmed that the model inventory entry reflects the current version and approval status.
The conclusions in this report apply to the model version and configuration reviewed and do not extend to later changes.
Recommendations are prioritised so that the most significant issues are addressed before the threshold change takes effect.
The validator relied on the vendor's reference implementation only after checking it against production results.
Where evidence was incomplete, the validator requested additional information rather than drawing conclusions.
The validation approach follows the corporate model risk standard and the validation procedure maintained by the Risk function.
""")

BANKS["audit2"] = _lines("""
The scope of the audit was agreed with management and approved by the Audit Committee in the annual plan.
Audit testing focused on the design and operating effectiveness of key controls over case reserves.
Walkthroughs were performed with process owners to confirm our understanding of each control.
Samples were selected using a combination of random selection and targeted selection of higher-risk items.
Where exceptions were identified, root causes were discussed with management before findings were finalised.
Management has accepted all findings and agreed actions, owners and target dates.
Ratings reflect the residual risk after taking into account compensating controls.
The audit did not cover the actuarial methodology for IBNR, which is subject to separate review.
Evidence was obtained from system reports, configuration listings and interviews with staff.
Previous audit findings in this area were followed up and their status is reported in the appendix.
We would like to thank management and staff for their cooperation during the audit.
The opinion expressed in this report relates to the period under review and the controls in place at the time.
Controls that rely on system functionality were tested by inspecting configuration and re-performing a sample of transactions.
Manual controls were tested by inspecting evidence of review and approval for the sample selected.
Actions will be tracked by Internal Audit and reported to the Audit Committee until closed.
The report has been discussed with the process owners and their comments reflected.
A finding rated Amber indicates a control weakness that should be addressed within the agreed timeframe.
A finding rated Green indicates an improvement opportunity with limited risk exposure.
The audit considered the planned changes under the modernisation programme where they affect the controls tested.
Key reports used in controls were tested for completeness and accuracy.
Segregation of duties was reviewed for the reserve authorisation process.
Audit trail requirements were assessed against the reserving policy and the record-keeping standards.
""")

BANKS["ops2"] = _lines("""
Before restarting any job, confirm that the cause of the failure has been understood and resolved.
Check the job output for the last successful checkpoint before deciding where to restart.
Do not cancel a job that is waiting on a dataset or a DB2 resource without checking what holds the resource.
Escalate to the on-call developer if the abend code is not listed in this runbook.
Record the abend code, the step and the action taken in the shift log before handing over.
If a downstream extract has already started, confirm with the interface owner whether it must be rerun.
Where the batch window is at risk, inform the shift manager so that dependent teams can be warned.
After any restart, check the record counts in the job summary against the previous run.
If an online transaction is unavailable, check whether the corresponding program is disabled before restarting the region.
Do not alter scheduler definitions during the batch window except under an approved emergency change.
Restarts that require data correction are carried out only with the approval of the application support lead.
Use the standard message templates when informing business users of delays.
Check the system console for related messages before and after the failing job.
Datasets created by a failed step are deleted or renamed before the step is rerun, unless the runbook says otherwise.
Where a job is held for business reasons, the reason and the requester are recorded on the scheduler.
At handover, the outgoing operator walks through any open incidents with the incoming operator.
Jobs that update reserves or payments are never rerun without confirming that the first run did not commit.
If in doubt, hold the downstream jobs rather than allowing them to run on incomplete input.
Incident tickets are raised for every abend, even when the job is restarted successfully.
Housekeeping jobs can be deferred to the next window if the main schedule overruns.
Operator commands are entered from the authorised consoles only.
The service desk is informed when an incident is likely to affect business users at the start of the day.
Recovery from a backup is a last resort and requires the approval of the platform manager.
""")

BANKS["job"] = _lines("""
{job} is monitored by Mainframe Batch Operations; failures are handled using the procedure in this section.
Before releasing {job} manually, confirm that its predecessors have completed successfully.
If {job} overruns, check for DB2 lock contention before assuming the job has stalled.
The job output for {job} is retained in the output archive and can be retrieved for investigation.
Changes to {job} follow the standard change process and are reflected in this runbook.
{job} writes a completion record that downstream jobs and interfaces check before they start.
When {job} is rerun, the operator records the reason and the time of the rerun in the shift log.
{job} is part of the critical path of the nightly schedule and is watched closely during month-end.
Abends in {job} are reported to the application support team at the start of the business day.
{job} uses the business date held on the scheduler, not the system date.
The scheduler definition for {job} includes the predecessor and successor dependencies shown in the schedule.
""")

BANKS["online"] = _lines("""
Online services are available during the published service hours; outside these hours the region may be recycled for maintenance.
Users report online issues to the service desk, which assigns them to the CLARA support queue.
Transaction failures are visible in the CICS logs and in the error records written by the common error routine.
If a transaction abends repeatedly, it may be disabled to protect the region while the cause is investigated.
Response times are monitored and alerts are raised when they exceed the agreed thresholds.
Before recycling a region, confirm with the shift manager and announce the outage to business users.
External calls made by online programs time out rather than holding the transaction indefinitely.
Where an external service is unavailable, the online program records the claim for later processing by the batch sweep.
Security changes to transactions are made by the access management team, not by operations.
New online programs are deployed during the weekly change window.
Operators should not purge user tasks unless instructed by the support team.
After a region restart, a smoke test of the main transactions is performed and recorded.
""")

BANKS["ri2"] = _lines("""
The programme is designed to protect the Society's capital against large individual losses and catastrophe events.
Cover is placed with a panel of reinsurers of appropriate financial strength, in line with the reinsurance security policy.
The programme structure was reviewed against the Society's risk appetite and the latest catastrophe modelling.
Claims handlers must flag any claim that may involve reinsurance recoveries, so that notification is timely.
Reinsurance recoveries are calculated on the basis of the ultimate net loss as defined in the treaty wordings.
Aggregation of losses arising from a single event follows the hours clause in the treaty wordings.
Reinstatement premiums are payable as set out in the treaty wordings and are accrued when a loss is notified.
Exclusions in the treaties broadly follow the exclusions in the underlying policies, with some additional market exclusions.
Currency conversion for Nordic losses follows the rates of exchange clause in the treaty wordings.
The Reinsurance team maintains the register of notified losses and reconciles it to the claims systems.
Disputes with reinsurers are escalated through the Reinsurance Manager to the CFO.
Treaty documents are held in the contract repository; this summary does not replace them.
The programme is renewed annually; changes for the next renewal are proposed to the Executive Committee in the autumn.
Large loss notifications to reinsurers are supported by the claim file and the current reserve.
Bordereaux are produced from the claims data and checked by Financial Control before submission.
The programme includes cover for Nordic branches on the same basis as UK business.
Counterparty exposure to each reinsurer is monitored by the Risk function.
The structure provides protection both for single large risks and for accumulations from weather events.
Claims staff must not discuss reinsurance arrangements with policyholders or third parties.
Reinsurers have rights to inspect claim files and to be consulted on large losses in line with the treaty wordings.
Claims staff should record the cause of loss and the event code consistently, because both drive aggregation.
The Reinsurance team keeps a log of every query raised by a reinsurer and the response given.
Where a loss involves more than one policy, the claims are linked so that the combined amount can be assessed.
Large losses are reviewed jointly by the Major & Complex Loss team and the Reinsurance team at agreed milestones.
The treaty period follows the calendar year; losses are allocated to the period by date of loss.
Recoveries are invoiced to reinsurers once the paid loss exceeds the retention, in line with the wordings.
Reserve changes on notified claims are reported to reinsurers so that their own reserves remain accurate.
Accounting entries for cessions are generated from the claims data and reviewed by Financial Control.
Inconsistencies between the claims systems and the reinsurance system are investigated before month-end.
The reinsurance programme is reviewed each year against the Society's capital position and risk appetite.
Where a claim is reopened, the Reinsurance team is informed so that any notification can be updated.
Salvage and subrogation recoveries reduce the ultimate net loss and are reported to reinsurers when received.
Claims involving bodily injury may develop slowly and are monitored for their potential to reach the reinsurance.
Information supplied to reinsurers is accurate, complete and consistent with the claim file.
Late notification can prejudice recoveries, so handlers should notify when in doubt.
The Reinsurance team provides training for claims staff on notification requirements each year.
Treaty documents and correspondence are retained in line with the records retention schedule.
Changes to systems that affect cessions or notifications are tested with the Reinsurance team before release.
Audit rights of reinsurers are coordinated by the Reinsurance team so that requests are handled consistently.
""")

BANKS["bc2"] = _lines("""
Doing nothing is not a viable option: the legacy platform will become harder and more expensive to support with each passing year.
The recommended option balances delivery risk against the benefits of moving off the legacy platform within a reasonable timeframe.
Benefits have been estimated conservatively and will be tracked through the benefits realisation plan.
The costs include a contingency that reflects the risks identified in the risk register.
Migration in waves reduces the risk of a single large cut-over and allows lessons to be applied to later waves.
The programme will be governed by a steering committee chaired by the executive sponsor.
An external delivery partner will bring experience of similar modernisations and supplement internal capacity.
Business change is as important as technology change; the plan includes training and operating model updates.
The programme will retire a number of satellite systems as well as the core legacy platform.
The new platform will make it easier to respond to regulatory change, which has become more frequent.
Customers will benefit from faster decisions and better information about the progress of their claims.
The programme will reduce key-person dependency on a small number of legacy specialists.
Data migration is a significant risk and has been planned with rehearsals and reconciliation at each wave.
Funding will be released in tranches, each subject to a stage-gate review.
The financial analysis uses the Society's standard discount rate and appraisal period.
Sensitivity analysis shows that the case remains positive under reasonable downside assumptions.
Dependencies on other change initiatives have been identified and will be managed through the portfolio office.
The architecture follows the Society's technology strategy and its cloud and integration principles.
The programme will be delivered using agile methods within a stage-gated governance framework.
A small number of non-financial benefits, such as improved staff experience, are described but not valued.
The plan allows the legacy platform to be run in parallel with the new platform for critical processes.
Decommissioning of the legacy platform is part of the programme scope and is required to realise the full benefits.
Exit costs for legacy licences and contracts have been included in the financial analysis.
The programme will maintain regulatory compliance throughout the transition.
The case has been reviewed by Finance, Risk and Technology before submission to the Executive Committee.
Each tranche of funding will be released only when the previous stage has met its exit criteria.
The programme will report progress, spend and risks monthly to the steering committee.
Lessons from comparable modernisations in the insurance market have informed the delivery approach.
The business will remain accountable for process design and acceptance; the technology teams will build and run the platform.
Benefits will be measured against a baseline taken before the first release.
The programme team will include claims experts seconded from the business for the duration of the build.
Where possible, existing Society platforms will be reused rather than procuring new ones.
A clear decommissioning plan is essential; running two platforms indefinitely would erode the benefits.
The plan protects peak periods, such as the winter weather season, from major cut-over activity.
The programme will engage the regulator early on changes that affect customers or regulatory returns.
Training will be delivered close to each go-live so that staff can apply it immediately.
Third-party dependencies, including vendors of satellite systems, will be managed through the supplier management framework.
Data quality issues found during migration will be corrected at source where practicable.
The programme will publish a single integrated plan covering technology, data and business change.
The architecture will avoid lock-in to any single supplier where a reasonable alternative exists.
Security and data protection requirements will be built in from the start rather than added later.
Customer communications about changes to the claims experience will be coordinated with the marketing team.
Contingency will be held centrally and released only with the approval of the CFO.
The programme will close formally once CLARA has been decommissioned and the benefits handed to business owners.
""")

BANKS["board2"] = _lines("""
Management will continue to monitor the position and will report any material change to the Committee without delay.
The Committee's attention is drawn to the actions set out in the paper and their target dates.
The paper has been reviewed by the Executive Risk Committee before submission to this Committee.
The risk profile is broadly unchanged since the last meeting, with movements explained in the paper.
Members are invited to comment on whether the proposed actions are sufficient.
The second line has reviewed the paper and its opinion is included at the end.
The Committee will receive a deep-dive on this topic at a future meeting, as agreed in the forward plan.
Management has engaged with the regulator on this matter and will report the outcome at the next meeting.
Key risk indicators are within appetite except where stated.
The paper should be read alongside the risk dashboard in the appendix.
The Committee is asked to approve the recommendation set out in the paper.
Assurance over the matters in this paper is provided by the second and third lines as described.
The paper is for discussion; no decision is required at this meeting.
Actions arising from previous meetings are tracked in the action log.
Emerging risks have been considered and are reported in the horizon-scanning section.
The Chair invited questions on the paper.
Members noted the update and requested that progress is reported at the next meeting.
Where risks are outside appetite, the paper sets out the plan to bring them back within appetite.
The paper reflects information available at the time of writing; any significant developments will be reported orally.
The Committee's terms of reference require it to review this matter at least annually.
Members asked management to confirm that the actions would be completed within the agreed timescales.
The Committee discussed the adequacy of resourcing for the actions described in the paper.
Members sought assurance that lessons learned would be applied to the next phase of work.
The Chair noted the progress made and thanked management for the clarity of the paper.
Management confirmed that the matter had been discussed with the external auditors.
The Committee requested that future papers include a clearer view of residual risk against appetite.
Members challenged whether the controls described would operate effectively under stress.
The Committee agreed that the matter should be escalated to the Board if the position deteriorates.
Members noted the interdependencies between this risk and the programme risks reported elsewhere in the pack.
The Committee asked for a short update to be circulated between meetings if there are material developments.
Management explained the steps taken since the last meeting and the remaining actions.
Members asked how the first and second lines had coordinated their assessment.
The Committee welcomed the improvement in the quality of management information.
The Committee discussed whether the current reporting frequency remains appropriate.
Members requested that the forward plan be updated to reflect the matters discussed.
""")

BANKS["risk"] = _lines("""
The risk is owned by the executive named in the risk register and reviewed monthly by the Executive Risk Committee.
Controls are assessed as partially effective, with improvement actions in progress.
The inherent risk remains high because of the scale of change being delivered.
Residual risk is within appetite after taking account of the controls described.
The trend is stable; no new risk events have been recorded since the last report.
Mitigating actions are on track and are expected to reduce the residual risk over the coming quarters.
The risk is closely linked to the programme risks reported separately in the change portfolio report.
Scenario analysis indicates that the impact of the risk crystallising would be manageable within existing capital.
Key risk indicators for this risk are reported in the dashboard.
The risk has been reassessed following the latest migration wave.
The second line has challenged the assessment and agrees with the rating.
Dependencies on third parties are a significant component of this risk.
The risk will be reassessed when the next migration wave has been completed.
Root cause analysis of recent incidents has been used to strengthen the controls for this risk.
The principal causes are understood and are addressed by the controls described in the register.
Control testing in the year has not identified any significant weaknesses in this area.
The risk owner has confirmed the assessment and the status of the actions.
External developments in the market have been considered in the assessment.
The likelihood of the risk crystallising has reduced, but the potential impact remains significant.
Monitoring of this risk relies on a combination of key risk indicators and control testing.
The risk is expected to remain elevated until the migration programme is complete.
Contingency plans for this risk have been reviewed and tested during the year.
Any change to the rating will be proposed by the risk owner and challenged by the second line.
This risk interacts with operational resilience and change capacity, which are reported separately.
""")

BANKS["finding"] = _lines("""
Management should ensure that the control is documented, operated consistently and evidenced.
The absence of a complete audit trail limits the ability to explain changes to case reserves after the event.
Without a reconciliation, differences between the systems could go undetected for some time.
The weakness increases the risk that reserves are misstated in management and regulatory reporting.
The control relies on a manual review that is not consistently evidenced.
Exception reports are produced but there is no evidence that they are reviewed and actioned.
The control design is adequate, but testing found that it did not operate consistently during the period.
The issue has been known to the support team but had not been escalated as a control weakness.
The planned migration to the new platform provides an opportunity to address the root cause.
A compensating control exists but is not documented or formally owned.
""")

BANKS["sla2"] = _lines("""
Service levels are measured from the time the instruction is accepted, not from the time it is issued.
Performance is assessed monthly; isolated failures are discussed at the operational review.
Where a service level is missed because of a delay caused by Corvane, the miss is excluded from the calculation.
The Supplier provides supporting data for each service level so that Corvane can verify the results.
Corvane may audit the Supplier's performance data on reasonable notice.
Continuous improvement initiatives are agreed at the quarterly review and tracked in the action log.
The Supplier nominates a service manager who is Corvane's primary contact for operational matters.
Service credits are not an exclusive remedy and do not affect Corvane's other rights under the Agreement.
""")

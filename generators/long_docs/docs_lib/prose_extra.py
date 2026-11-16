"""Additional phrase-bank templates (same rules as prose.py: generic statements only)."""
from __future__ import annotations

from .prose import BANKS, _lines

_EXTRA = {}

_EXTRA["arch"] = _lines("""
{svc} validates every inbound request against its published contract before any business logic runs.
The team that owns {svc} also owns its runbooks, dashboards and alert definitions.
{svc} avoids synchronous call chains longer than one hop; where more context is needed it relies on events it has already consumed.
Caching inside {svc} is limited to reference data and is invalidated on change events rather than on timers.
{svc} treats every event it consumes as potentially out of order and uses business keys to reconcile state.
Feature toggles allow new behaviour in {svc} to be released dark and enabled once the business is ready.
The internal structure of {svc} separates domain logic from adapters for persistence, messaging and HTTP.
{svc} publishes events only after the corresponding database transaction has committed.
Retry policies in {svc} use exponential back-off and stop after a bounded number of attempts.
{svc} returns problem details in a consistent format so that clients can handle errors uniformly.
Time-dependent rules in {svc} are evaluated against the business date of the claim rather than the system clock.
The build pipeline for {svc} produces a signed container image that is promoted unchanged between environments.
{svc} can be started locally with stubs for its dependencies, which shortens the feedback loop for developers.
Operational parameters for {svc}, such as pool sizes and timeouts, are tuned per environment rather than hard-coded.
{svc} distinguishes clearly between business errors that need a human decision and technical errors that can be retried.
Read models inside {svc} are rebuilt from its own data and can be regenerated if they become inconsistent.
Batch-style processing in {svc} is broken into small units of work so that progress is visible and restartable.
{svc} records the version of each business rule applied, so that past decisions can be explained.
Pagination is mandatory for list operations in {svc} to protect it from unbounded queries.
{svc} exposes no administrative endpoints on the public route; operational actions go through the platform tooling.
The responsibilities of {svc} were agreed with the business owner during capability mapping and are not extended without review.
Load on {svc} is expected to follow the daily pattern of claim notifications, with peaks after severe weather events.
{svc} uses the claim reference as its primary correlation key across logs, events and traces.
Dependencies of {svc} on other services are declared explicitly so that the impact of an outage can be assessed.
Shared code between {svc} and other services is limited to generated contract clients and the logging conventions.
{svc} keeps a full audit history of the changes it makes, independent of the event stream.
Contract-first design means the API description for {svc} is reviewed before implementation starts.
The data retention behaviour of {svc} follows the corporate retention schedule and is configurable per record type.
Concurrency control in {svc} uses optimistic locking on the aggregate, which suits the low contention expected per claim.
{svc} is built and tested in the same way as every other service, which keeps operational knowledge transferable.
""")

_EXTRA["integration"] = _lines("""
Interface specifications describe the business meaning of every field, not only its format.
Where two systems hold the same data during coexistence, one is designated the master and the other is refreshed from it.
Reconciliation reports compare record counts and control totals between source and target for every scheduled run.
The interface monitoring console shows the last successful run, the next scheduled run and any outstanding errors.
Point-to-point file transfers are replaced by events or APIs when the producing capability moves to Claims Hub.
A change freeze applies to interfaces that feed regulatory returns in the days before each submission deadline.
Message size limits are documented for each queue and topic so that producers can design within them.
Consumers must tolerate additional optional fields so that producers can evolve layouts without coordinated releases.
Sequence numbers or timestamps allow consumers to detect gaps in a stream of records.
The integration team maintains test harnesses that can replay production-like traffic into lower environments.
Every interface change is assessed by the owners of all downstream dependants before approval.
Interfaces are classified by criticality, which determines their monitoring, support hours and recovery objectives.
Long-running file transfers are checkpointed so that a failed transfer can resume rather than restart.
Character encoding is specified explicitly for every file and message, including the handling of Nordic characters.
Where an interface performs a currency conversion, the rate source and timing are documented in the specification.
Duplicate detection relies on business keys rather than transport-level identifiers.
The catalogue records which interfaces will be retired, replaced or retained at each stage of the migration.
Credentials for interface connections are rotated in line with the security standard and never shared between interfaces.
Partner-facing interfaces are rate limited to protect internal systems from unexpected load.
Operational contacts for every interface are listed in the catalogue and kept current.
""")

_EXTRA["data"] = _lines("""
Master data management responsibilities are assigned to named business owners rather than to technology teams.
Data definitions use the business glossary so that the same term means the same thing in every system.
Where legacy codes have no equivalent in the target, the mapping is agreed with the business owner and documented.
Historic values are preserved when a code list changes, so that past records remain interpretable.
Profiling of source data is repeated before each migration rehearsal to detect new quality issues.
Data quality dashboards show the volume and age of open exceptions by rule and by owner.
Archiving moves inactive records to cheaper storage while keeping them retrievable for the retention period.
Deletion at the end of the retention period is logged so that it can be evidenced to auditors and the regulator.
Data flows that leave the Society are recorded in the record of processing activities.
Analytical copies of operational data are refreshed from events rather than by direct database extraction.
Calculated fields are documented with their formula and the business rule that defines them.
Null and default values are distinguished explicitly so that missing data is not mistaken for a valid value.
Reference tables are version-controlled and deployed through the same pipeline as application code.
Field lengths in the target are sized for the longest legitimate legacy value plus headroom for growth.
Sensitive fields are masked in non-production environments using deterministic techniques so that test cases remain repeatable.
Corrections to financial data are made by compensating entries rather than by updating history.
Data lineage is captured automatically where tooling allows and supplemented by documentation where it does not.
The data dictionary is the authoritative source for column definitions and is reviewed at each release.
""")

_EXTRA["security"] = _lines("""
Security requirements are captured alongside functional requirements and tested in the same way.
Threat modelling is carried out for each service before its first production release and repeated after significant change.
Third-party libraries are pinned to approved versions and monitored for published vulnerabilities.
Administrative access to production platforms requires multi-factor authentication and is time-limited.
Session handling in user interfaces follows the corporate standard for timeouts and re-authentication.
Logs are reviewed for security events by the security operations function using agreed detection rules.
Data exported for analysis is minimised to the fields required and approved by the data owner.
Penetration testing is commissioned before major releases and findings are tracked to closure.
Network segmentation limits which components can reach the mainframe and the payment systems.
Break-glass access is available for emergencies and every use is reviewed after the event.
Security exceptions require a documented risk acceptance by the accountable owner.
Encryption keys are managed by the platform key service and rotated on a defined schedule.
Partner access is restricted to the claims the partner has been instructed on.
Security awareness training covers the specific risks of handling claims and payment data.
""")

_EXTRA["governance"] = _lines("""
The document is maintained in the programme document library and the library version is the controlled copy.
Terminology follows the Corvane claims glossary; deviations are explained where they occur.
Material changes are presented to the approving forum before the document is reissued.
Open items are tracked in the programme RAID log and referenced here by identifier.
The section has been checked against the systems of record at the date of issue.
Where figures are quoted, they are taken from the systems of record at the date of the document.
Readers are asked to report errors to the document owner so that they can be corrected in the next version.
Cross-references to other documents are to the versions current at the date of issue.
Statements about future releases describe intent and remain subject to programme governance.
The approvers listed in the document control section are accountable for the content of this document.
""")

_EXTRA["ops"] = _lines("""
Before making any change in production, check the change calendar for conflicting activity.
When a job is held, record the reason in the scheduler so that the next shift understands why.
Do not rerun extract jobs without confirming with the downstream owner, because duplicate files can cause duplicate postings.
Dataset contention messages usually clear once the competing job ends; wait for it before restarting.
If the scheduler is unavailable, follow the manual submission procedure and log every job submitted.
Escalation to the platform manager is mandatory if the end of the batch window is at risk.
Space abends on output datasets are resolved by the storage team; do not reallocate production datasets without approval.
Confirm that inbound files carry the expected business date in their header before releasing jobs that process them.
Where a job completes with a warning, review the messages before releasing its successors.
The operator must not edit production JCL; changes follow the change process even in an emergency.
Monitoring alerts are acknowledged within the agreed time and assigned to an owner.
After any manual intervention, add a note to the job history so that patterns can be analysed.
Restart points are identified in the job documentation; if no restart point is documented, escalate.
If an online transaction is failing for all users, raise a major incident before attempting diagnosis.
Communication to business users during an incident goes through the service desk, not directly from operators.
Planned outages are notified to the business in advance and confirmed on the day.
DB2 utilities that run during the batch window must finish before the online region opens.
Verify the interface log after restarting any job that writes to a queue, so that duplicate messages can be identified.
Use the documented contact list; personal mobile numbers are not to be used for escalation.
At the end of the batch window, confirm that the online region has started and that the first transactions succeed.
""")

_EXTRA["batch"] = _lines("""
Critical-path jobs are monitored more closely, because a delay to them delays every dependent job.
Jobs that read files from external parties wait for a trigger rather than polling at fixed times.
The scheduler calendars reflect public holidays in the UK, Norway, Sweden and Denmark.
Output from each job is retained for a period that allows reruns and investigations.
Batch programs report record counts at the end of each step for reconciliation.
Jobs are designed to be rerunnable without side effects wherever the business process allows.
Where a job cannot safely be rerun, its documentation says so in capital letters.
Year-end processing is rehearsed in a test environment before it runs in production.
The schedule is reviewed after every major change to confirm that dependencies are still correct.
Long-running utilities are scheduled away from the critical path.
Job names follow the CLARA naming convention, which identifies the frequency and the functional area.
Batch performance is trended so that growth can be anticipated before the window is breached.
""")

_EXTRA["migration"] = _lines("""
Each migration wave has a scope statement that lists products, regions and claim statuses included.
Open claims are migrated with their full financial history so that reserves and payments can be reconciled.
Documents remain in the document store and are linked to migrated claims by reference rather than copied.
In-flight work items, such as diary entries and open tasks, are migrated so that handlers can continue without interruption.
Users are trained on the target before their claims are migrated, not after.
Data owners review samples of migrated claims as part of the business sign-off.
Performance of the migration tooling is measured in rehearsals so that the cut-over window can be planned accurately.
The migration team keeps a decision log for every mapping choice that is not obvious from the specification.
Parallel processing in the migration tooling is tuned so that the source system is not overloaded.
The legacy identifier is visible in the target user interface during the transition period.
Defects in the migration tooling are fixed and regression-tested before the next rehearsal.
Interfaces that depend on migrated data are switched in a planned sequence during cut-over.
Communications to customers and brokers are planned for each wave where their experience changes.
Each rehearsal ends with a lessons-learned review whose actions are tracked to closure.
Data that fails validation is reported back to the source owner with a clear reason code.
The migration environment is sized to hold a full copy of the in-scope data for each rehearsal.
Archived claims remain retrievable through the archive route for the retention period.
Post-migration support is staffed with people who took part in the rehearsals.
""")

_EXTRA["test"] = _lines("""
The test approach is risk-based: the depth of testing reflects the business impact of failure.
Defect severity definitions are shared by the programme and the business so that priorities are understood consistently.
Test environments mirror production configuration closely enough that results are representative.
Each squad maintains automated tests at unit, component and contract level for its services.
End-to-end tests focus on business journeys that cross several services and systems.
Exploratory testing complements scripted testing, particularly for user-facing changes.
Regression scope is reviewed for every release based on the areas of change.
Performance tests use realistic volumes and data distributions derived from production profiles.
Resilience tests confirm that services recover from dependency failures without manual intervention.
Security tests include automated scanning in the pipeline and manual testing before major releases.
Operational acceptance testing confirms that support teams can monitor, operate and recover the system.
Test data management is planned so that each test cycle starts from a known state.
The test manager reports progress against plan, defect trends and residual risks each week.
Entry criteria for each phase confirm that the previous phase has delivered what it promised.
Accessibility testing is included for every user interface that customers or staff use.
Business acceptance includes month-end and year-end scenarios as well as day-to-day processing.
Defects found in production are analysed to improve the test approach for later releases.
Test results are recorded in the test management tool so that evidence is retained.
""")

_EXTRA["model"] = _lines("""
The model is developed and licensed by a third party, so governance focuses on use, configuration and monitoring.
Score distributions are compared month on month to detect drift in the population being scored.
The approved cut-off is documented with the analysis that supports it and the date of approval.
Changes to the indicators used alongside the score follow the same governance as changes to the cut-off.
Investigators' outcomes feed back into the performance measures used to assess the model.
The governing forum reviews performance, monitoring exceptions and planned changes at each meeting.
Model documentation is version-controlled and linked to the model inventory entry.
Any temporary override of the model configuration is time-limited and reported to the governing forum.
Regulatory expectations on documentation and calibration are mapped to specific controls.
Access to change the model configuration is restricted to named individuals.
The vendor's own validation evidence is reviewed but does not replace independent validation.
Training for users explains what the score means and what it does not mean.
Back-testing compares historic scores with confirmed outcomes over a representative period.
Population changes, such as new products or channels, trigger an assessment of model suitability.
""")

_EXTRA["audit"] = _lines("""
The review was performed in accordance with the internal audit charter and methodology.
Audit testing focused on the controls that matter most to the accuracy and completeness of case reserves.
Where control evidence was incomplete, the finding reflects the gap in evidence rather than an assumed failure.
Management have accepted the findings and agreed actions with owners and target dates.
Internal Audit will validate the implementation of agreed actions before closing each finding.
The scope included both the legacy platform and the controls being designed for its replacement.
System-enforced controls were preferred over manual controls where both were available.
Several good practices were observed and are noted in the report.
The findings have been shared with the second-line risk function.
The audit relied on reports generated from the system of record; their accuracy was tested on a sample basis.
Interviews were held with the control owners and with staff who operate the controls day to day.
The audit considered the changes to the control environment arising from the modernisation programme.
""")

_EXTRA["bizcase"] = _lines("""
The Society's strategy commits it to faster, fairer claims handling for its members across all four countries.
Modern claims platforms allow straight-through processing of simple claims, freeing handlers to focus on complex cases.
Real-time data from a modern platform improves the quality of reserving and management information.
Reducing dependence on scarce mainframe skills lowers key-person risk.
The new platform will be built with configurable rules, so that regulatory changes can be implemented quickly.
The programme will release value incrementally, starting with digital notification and triage.
Each option has been assessed against the same criteria: benefits, cost, risk, time to value and strategic fit.
The assessment was carried out with input from Claims, Finance, Technology and Risk.
Assumptions underlying the financial case will be revisited at each stage gate.
The programme will use an external delivery partner alongside internal teams to bring experience and capacity.
Knowledge transfer from the delivery partner to internal teams is a condition of each phase.
Governance arrangements give the steering committee authority to stop or re-scope the programme if benefits are not realised.
Members will see the benefits in faster notification, clearer communication and quicker settlement.
The risks of the preferred option are understood and have owners and mitigations.
Investment in the new platform also addresses obsolescence in the surrounding integration estate.
The case has been reviewed by the Executive Committee before submission.
""")

_EXTRA["board"] = _lines("""
The paper has been prepared by management and reviewed by the executive sponsor.
Key judgements are set out explicitly so that the Committee can challenge them.
The second line has reviewed the paper and its comments are reflected in the commentary.
Further detail is available in the reading room for members who wish to see it.
The Committee's attention is drawn to the forward-looking indicators, which show the direction of travel.
Management will confirm at the next meeting that the actions described have been completed.
The item links to the Society's risk appetite statement and to the principal risks register.
No exceptions to policy have been approved since the last meeting other than those reported here.
Members are invited to comment on whether the level of detail meets their needs.
The executive has discussed the implications for the business plan and will report back if they change.
""")

_EXTRA["vendor"] = _lines("""
The Supplier shall maintain adequate business continuity arrangements for the Services.
Each party shall nominate a relationship owner who is responsible for the operation of this Schedule.
Any dispute about performance data will first be addressed by the relationship owners.
The Supplier shall cooperate with Corvane's auditors and regulators in relation to the Services.
Changes in key Supplier personnel are notified to Corvane in advance where possible.
The Supplier shall not contact policyholders other than as required to perform the Services.
Corvane will provide the Supplier with access to the systems and information reasonably required to perform the Services.
""")

_EXTRA["brd"] = _lines("""
The requirement is technology-neutral and applies to both CLARA and Claims Hub for as long as both are in use.
Business users have confirmed that the acceptance criteria reflect how they will judge success.
Where a requirement creates a new customer communication, the template is approved by Compliance before go-live.
The requirement must be traceable through design, build and test to evidence of compliance.
Reporting requirements are specified at the level of the measure and its definition, not the report layout.
Exceptions to the requirement must be authorised and recorded so that they can be reported.
Training for affected users will be delivered before the requirement goes live.
Existing controls that the requirement relies on are identified so that they can be tested.
Each requirement has a single business owner who approves changes to it.
The requirement has been assessed for its impact on customers in vulnerable circumstances.
""")

_EXTRA["opmodel"] = _lines("""
Team leaders are responsible for day-to-day allocation of work within their teams.
Specialist teams provide expertise to the claims teams without taking over accountability for the claim.
Service levels are owned by the stage owner and reported in the monthly operational performance pack.
Where work moves between UK and Nordic teams, the hand-off is recorded on the claim.
Cross-functional forums resolve issues that span more than one stage.
Capability building is planned so that teams can adopt Claims Hub as each wave goes live.
Second-line functions provide oversight and challenge but do not perform first-line activities.
Accountability for vendor performance sits with the stage that instructs the vendor.
Changes to the operating model are communicated to staff before they take effect.
The operating model is designed to work with both CLARA and Claims Hub during the transition.
""")

_EXTRA["reinsurance"] = _lines("""
Treaty terms are interpreted by the Reinsurance team, who are the first point of contact for reinsurers.
Large losses are reviewed for potential aggregation with other losses from the same event.
Claims data supplied to reinsurers is limited to what the treaty requires.
Reinsurance recoveries are recognised in line with the accounting policy agreed with Finance.
The renewal process includes a review of the claims experience under the expiring treaty.
""")

for _k, _v in _EXTRA.items():
    BANKS.setdefault(_k, [])
    for _t in _v:
        if _t not in BANKS[_k]:
            BANKS[_k].append(_t)

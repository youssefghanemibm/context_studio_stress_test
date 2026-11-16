"""Phrase banks for realistic enterprise prose.

Rules for every template (CONVENTIONS §6): no numbers, thresholds, owners, dates, system links or
program-table links. Slots only take values the builder passes from the world model, and templates
only assert generic properties (design intent, governance, practice) about them.
"""
from __future__ import annotations

import random
import re

_LOWER_OK = re.compile(r"^(The|A|An|Each|All|Every|This|These|Where|Any|No|Both|Changes|Most|Some|It|Its)\b")

CONNECTORS = ["In practice, ", "In addition, ", "For this reason, ", "Where possible, ", "As a general rule, ",
              "In the same way, ", "By design, ", "Equally, ", "At the same time, ", "Accordingly, ",
              "As a consequence, ", "Importantly, ", "In most cases, ", "Likewise, ", "On balance, "]


def _lines(s: str) -> list[str]:
    return [ln.strip() for ln in s.strip().splitlines() if ln.strip() and not ln.strip().startswith("#")]


BANKS: dict[str, list[str]] = {}

BANKS["intro"] = _lines("""
This section describes {topic}.
The purpose of this section is to set out {topic} in enough detail for design, build and assurance teams to work from it.
This part of the document explains {topic} and the reasoning behind the chosen approach.
The material below covers {topic}; related decisions are referenced where they apply.
{topic_cap} is described below in the order in which readers are most likely to need it.
This section summarises {topic} and records the points that reviewers asked to be made explicit.
The following paragraphs set out {topic} as agreed with the stakeholders listed in the document control table.
Readers who need only the headline position on {topic} can rely on the summary at the start of this section.
This section is normative: where it conflicts with an earlier working paper on {topic}, this section prevails.
{topic_cap} is presented here at the level of detail needed for approval; lower-level material sits in the supporting design notes.
""")

BANKS["governance"] = _lines("""
Changes to this section follow the document change-control process and are recorded in the version history.
Any deviation from the position described here must be raised with the document owner before it is implemented.
Comments received during review have been incorporated or logged as open items in the issues register.
The content has been reviewed for consistency with the other programme baselines referenced in this document.
Where a statement depends on a decision that has not yet been taken, it is flagged as an open item rather than presented as settled.
The document owner is responsible for keeping this section aligned with the approved baselines.
Each review cycle confirms that the statements in this section still reflect the approved position.
Requests for clarification should be raised through the document owner rather than by editing local copies.
Superseded versions are retained in the document library for audit purposes but must not be used for delivery.
This section will be revisited at the next scheduled review or earlier if a material change is approved.
The approvers have confirmed that the section is fit for its stated purpose.
Readers should treat printed copies as uncontrolled.
""")

BANKS["arch"] = _lines("""
{svc} is designed to be stateless at the process level so that instances can be rescheduled without losing in-flight work.
The responsibilities of {svc} are deliberately narrow, which keeps its interface small and its change rate predictable.
{svc} owns its data outright; no other component reads or writes its tables directly.
Interactions with {svc} are either synchronous API calls for queries and commands, or published domain events for state changes.
The design of {svc} favours explicit contracts over shared libraries, so that teams can release independently.
Configuration for {svc} is externalised and versioned alongside the deployment descriptors.
{svc} exposes health and readiness endpoints that the platform uses to manage rolling deployments.
All externally visible behaviour of {svc} is described by its published API contract and event schemas.
Failures in downstream dependencies are isolated so that {svc} degrades gracefully rather than failing outright.
The data model behind {svc} is normalised for transactional use; reporting needs are met from events rather than direct queries.
{svc} records every state change with enough context to reconstruct the history of a claim for audit.
Idempotent command handling allows clients of {svc} to retry safely after a timeout.
Schema changes for {svc} are applied through versioned migration scripts executed by the deployment pipeline.
The boundaries of {svc} follow the business capability map rather than the structure of the legacy programs it replaces.
Logging from {svc} is structured and correlated by claim reference and request identifier.
Instance counts for {svc} are set per environment so that a single pod failure does not interrupt service where the capability is business-critical.
Long-running work in {svc} is handled asynchronously so that API response times remain predictable.
Authorisation decisions in {svc} are made on claims carried in the access token, never on client-supplied flags.
The service publishes metrics for throughput, latency and error rates to the shared observability stack.
Backward-compatible change is the default for {svc}; breaking changes require a new major version of the contract.
""")

BANKS["integration"] = _lines("""
Each interface has a single named owner who approves changes to its layout, schedule or transport.
Consumer impact assessment is mandatory before any change to a record layout is promoted.
Interfaces that carry financial values are reconciled end to end so that dropped or duplicated records are detected.
Message-based interfaces are designed for at-least-once delivery, and consumers are expected to de-duplicate.
Where an interface runs on a schedule, upstream completion is confirmed before the downstream job is released.
File and message layouts carry a version indicator so that consumers can reject records they do not understand.
Interface failures are surfaced through the monitoring console and raised as incidents according to their criticality.
The interface catalogue is the single source of truth for owners, schedules and dependencies.
Upstream and downstream dependencies are recorded explicitly so that the impact of a change can be traced in both directions.
Replays are supported for all event-based interfaces within the retention period of the underlying topic.
Error records are routed to a dead-letter destination with enough context to support investigation and replay.
Interfaces that cross the boundary between the mainframe and the distributed estate are treated as high risk during change.
Transport security is enforced on every interface, including those that remain inside the data centre.
New integrations favour events published by the system of record over point-to-point extracts.
Volume and latency characteristics are reviewed whenever a new consumer subscribes to an existing interface.
Every interface has a documented recovery procedure that the support teams have rehearsed.
Interfaces carrying personal data are subject to the data protection impact assessment before they go live.
""")

BANKS["data"] = _lines("""
Data ownership follows the business capability that creates the data, not the system that happens to store it.
Reference data is mastered once and distributed to consuming components rather than maintained in parallel.
Data quality rules are expressed as executable checks so that they can run in every environment.
Personal data is classified at field level and handled in line with the data protection policy.
Lineage from source to report is documented for every figure used in regulatory returns.
Monetary amounts are stored with their currency and never converted silently at rest.
Historic data is retained in line with the retention schedule and archived rather than deleted where the schedule requires it.
Derived values are recalculated from source data rather than copied, so that corrections propagate consistently.
Code values are translated through governed mapping tables rather than embedded in program logic.
Data defects found during testing are traced back to the source system and corrected there wherever possible.
Every table has a documented primary key and a defined owner.
Field-level descriptions are maintained in the data dictionary and reviewed whenever a structure changes.
Timestamps are recorded in a single reference time zone and converted only for presentation.
Free-text fields are treated as potentially containing personal data unless proven otherwise.
""")

BANKS["security"] = _lines("""
Access to production data is granted on the principle of least privilege and reviewed periodically.
Privileged actions are logged centrally and the logs are protected from alteration.
Service-to-service calls are authenticated with short-lived credentials issued by the identity platform.
Secrets are held in the platform secret store and are never written to source control or configuration files.
Segregation of duties is enforced between those who develop changes and those who approve their release to production.
Vulnerability scanning runs as part of every build, and findings above the agreed severity block promotion.
Partner users authenticate through the corporate identity service rather than local accounts.
Encryption in transit is mandatory on every network path that carries claim or customer data.
Audit trails capture who changed what and when, with enough detail to support investigations.
Test environments use masked or synthetic data; production personal data is not copied into them.
Access reviews are evidenced and retained for inspection by internal audit.
""")

BANKS["ops"] = _lines("""
Operators should confirm the current state of the job in the scheduler before taking any recovery action.
All recovery actions are recorded in the shift log with the time, the operator and the outcome.
Where the procedure below is unclear or does not match what is observed, escalate rather than improvise.
Do not cancel or force-complete a job without the agreement of the on-call application support analyst.
After a successful restart, check the job output for the expected completion messages before releasing dependent work.
Abends outside the batch window are handled under the same procedure, but the business impact is usually lower.
The on-call analyst must be paged for any abend in a job that feeds the general ledger or a regulatory return.
Output datasets from a failed run must not be deleted until the cause of the failure is understood.
If a restart fails twice, stop and escalate to the platform manager.
The shift lead confirms at handover that all exceptions raised during the shift have an owner.
Where a job depends on an inbound file, confirm that the file has arrived and is complete before restarting.
Keep the business informed of any delay that could affect the online day or a downstream deadline.
Record the incident reference in the shift log so that the problem record can be linked later.
Check the scheduler calendar before forcing a job, particularly around bank holidays in any of the four countries.
Restarts must use the procedure documented for the job; generic restart steps are not sufficient for jobs that update financial tables.
Where data has been partially committed, the application support analyst decides whether a back-out is required.
Online regions are not recycled during the batch window unless the platform manager has approved it.
""")

BANKS["batch"] = _lines("""
The nightly schedule is designed so that jobs which update claim and reserve data complete before the extracts that read them.
Each job step commits at regular intervals so that a restart does not need to reprocess the whole input.
Jobs that write to interface queues record their completion in the interface log so that downstream processing can be verified.
Dependencies between jobs are defined in the scheduler rather than inferred from start times.
Month-end and year-end jobs run in addition to the nightly schedule and are coordinated with Finance in advance.
The batch window is protected; online changes are not deployed while the nightly schedule is running.
Jobs are grouped by business area so that the impact of a failure can be assessed quickly.
Return codes above the agreed limit cause the scheduler to hold dependent jobs automatically.
Housekeeping jobs run at weekends when the online workload is lowest.
Generation data groups are used for daily extracts so that previous outputs remain available for reruns.
Programs that update the reserve tables write audit information identifying the program and the batch user.
The scheduler raises an alert if a job has not started within its expected window.
""")

BANKS["migration"] = _lines("""
Data is migrated by business scope so that each wave can be reconciled, signed off and, if necessary, rolled back on its own.
Extraction runs against a consistent point-in-time copy so that the source does not change during a run.
Transformation rules are held as version-controlled specifications and tested with representative samples before each rehearsal.
Every migrated record keeps a reference to its legacy identifier so that it can be traced back to the source.
Rehearsals are run under production-like conditions, including timings, volumes and the sign-off steps.
Exceptions found during a rehearsal are triaged into data fixes at source, rule changes or accepted variances.
The cut-over plan is rehearsed end to end, including the business freeze and the go or no-go decision.
Closed claims outside the migration scope remain available for enquiry through the archive route.
Financial balances are reconciled at claim and portfolio level before a wave is signed off.
Data cleansing is performed in the source system wherever practical, so that the same issue does not reappear in the next extract.
The migration tooling produces a complete audit trail of every record extracted, transformed, loaded or rejected.
No manual data correction is permitted in the target outside the controlled exception process.
Each wave has a named business owner who signs off the reconciliation before the target becomes the system of record.
Rollback criteria are agreed before the cut-over weekend and are not renegotiated during it.
Code tables are mapped explicitly; unmapped values stop the load rather than defaulting silently.
The legacy system remains read-only for migrated claims after cut-over so that historic enquiries can still be answered.
""")

BANKS["test"] = _lines("""
Test cases are traced to requirements so that coverage can be demonstrated at each stage gate.
Defects are triaged daily and prioritised by business impact rather than by the order in which they were raised.
Automated regression packs run on every build and must pass before a release candidate is promoted.
Test data is created synthetically or masked from production in line with the data protection policy.
Environments are refreshed on a defined cycle so that test results are not distorted by stale data.
Non-functional testing covers performance, resilience, security and operability, not only response times.
Exit criteria are agreed with the business owner before execution begins, not after results are known.
Each test phase produces a completion report that records residual risks and open defects.
Interfaces are tested against stubs first and against the real counterpart systems as soon as they are available.
Business users take part in acceptance testing using their own scenarios as well as scripted cases.
Every severity-one defect has a documented root cause before the related release is approved.
Test evidence is retained so that auditors can re-perform a sample of the tests if required.
The same deployment pipeline is used for test and production releases so that test results are representative.
Where a defect is deferred, the business owner accepts the associated risk explicitly.
Contract tests protect producers and consumers of each event from incompatible schema changes.
""")

BANKS["model"] = _lines("""
The model owner is accountable for the model's performance, documentation and use within the approved scope.
Material changes to the model, its inputs or its cut-off are approved before they are deployed.
Model performance is monitored continuously and reported to the governing forum at each meeting.
Independent validation is carried out by a function that did not develop or operate the model.
Scores are used to prioritise investigation, never as the sole basis for an adverse decision on a claim.
Input data quality is monitored, because changes upstream can shift the score distribution without any change to the model.
Overrides and outcomes are recorded so that the model's effectiveness can be assessed against investigation results.
Documentation is maintained to a standard that would allow a competent reviewer to reproduce the main results.
The vendor's release notes are reviewed before any engine upgrade is accepted into production.
Monitoring thresholds trigger an investigation rather than an automatic change to the model.
Fairness considerations are reviewed as part of each calibration, including the effect of the cut-off on different customer groups.
Model limitations are communicated to users so that scores are interpreted appropriately.
Any use of the score outside fraud triage requires a separate approval.
The model inventory records the version in production, its approval and its next validation date.
""")

BANKS["audit"] = _lines("""
The audit approach combined walkthroughs, inspection of documentation and re-performance of a sample of controls.
Testing was performed on data and evidence provided by management; completeness of that evidence was confirmed where possible.
Control design was assessed against the risks identified in the planning memorandum.
Operating effectiveness was tested over the audit period using samples selected on a risk basis.
Management were given the opportunity to comment on each finding before the report was finalised.
Findings are rated according to the internal audit rating scale set out in the appendix.
Agreed actions will be tracked to completion by Internal Audit and reported to the Audit Committee.
Where a control relies on a system report, the logic of that report was reviewed as part of the testing.
The scope excluded areas that were reviewed by other assurance providers during the period.
Exceptions identified in sampling were discussed with the control owners and the root causes recorded.
Internal Audit would like to thank management and staff for their cooperation during the review.
The overall rating reflects the combined effect of the findings rather than the number of findings raised.
Evidence of review was expected to be retained in a form that allows independent re-performance.
Controls that operate automatically were tested by inspection of configuration and a test of one instance.
""")

BANKS["bizcase"] = _lines("""
The current platform has served the Society well, but the cost and risk of keeping it running are rising each year.
The skills needed to maintain the legacy code are concentrated in a small number of long-serving colleagues.
Every change to the legacy platform takes longer and costs more than an equivalent change on a modern platform.
Customers increasingly expect to notify and track claims digitally, which the current architecture supports only through overnight batches.
Regulatory expectations on timeliness, fairness and data retention are tightening across all four countries.
A phased replacement reduces delivery risk by allowing the Society to learn from each wave before committing the next.
The preferred option balances delivery risk, cost and the speed at which benefits can be realised.
Benefits will be tracked against a baseline agreed with Finance before the programme starts.
Dis-benefits, including a temporary increase in change activity for claims teams, have been considered and are manageable.
The programme will be governed by a steering committee with clear authority over scope, budget and cut-over decisions.
Key dependencies on other change initiatives have been identified and will be managed through the portfolio office.
The do-nothing option is not cost-free: it carries growing operational, regulatory and people risk.
A packaged replacement would require extensive customisation to support the Society's Nordic products.
The recommended option keeps the Society in control of its claims capability while using modern, widely supported technology.
Contingency has been included at programme level rather than spread across individual workstreams.
Benefits are expected to build gradually as each wave migrates, rather than arriving at a single go-live.
""")

BANKS["board"] = _lines("""
The Committee is asked to note the update and to challenge management on the adequacy of the actions described.
Management considers that the risk remains within appetite, although the trend is being watched closely.
The position will be reported again at the next meeting with an update on the actions in progress.
No new matters requiring escalation to the Board have arisen since the last meeting.
The executive team has discussed the item and supports the recommendation set out below.
Assurance over the figures has been provided by the second line, with no material exceptions reported.
The Committee previously asked for greater visibility of this area, and the dashboard has been expanded accordingly.
Management will bring a fuller paper to a future meeting once the current phase of work is complete.
The risk owner has confirmed that the controls described are operating as designed.
The paper should be read alongside the principal risk report earlier in this pack.
The item is presented for discussion; no decision is required at this meeting.
Members may wish to explore the interdependencies between this item and the programme update.
Management recognises that sustained attention is needed to keep this risk within appetite.
""")

BANKS["vendor"] = _lines("""
The Supplier shall provide the Services in accordance with this Schedule and the Master Services Agreement.
Performance against each service level is measured monthly and reported in the agreed format.
Persistent failure to meet a service level is addressed through the escalation process described in this Schedule.
The Supplier shall notify Corvane promptly of any event likely to affect its ability to meet a service level.
Service levels are measured from the time an instruction is received, not from the time it is accepted.
Instructions are issued and acknowledged electronically; telephone instructions must be confirmed in writing.
The parties will review this Schedule annually and may agree changes in writing.
Reports must be complete, legible and supported by the evidence required by the claims-handling standards.
The Supplier shall ensure that its personnel are appropriately qualified for the work they undertake.
Corvane may audit the Supplier's performance records on reasonable notice.
Data received under this Schedule may be used only for the purpose of providing the Services.
Where a service level is not met for reasons outside the Supplier's control, the parties will agree an adjustment in good faith.
Any sub-contracting of the Services requires Corvane's prior written consent.
The Supplier shall comply with Corvane's information security requirements when using Corvane systems.
""")

BANKS["brd"] = _lines("""
The requirement applies to all products and claim types unless a specific exclusion is stated.
Acceptance criteria are written so that each requirement can be verified by a test case.
Where a requirement changes an existing process, the as-is and to-be steps are described in the process section.
The business owner has confirmed the priority of each requirement using the MoSCoW scale.
Requirements are expressed in terms of outcomes; the solution design will determine how they are met.
Each requirement is traced to the regulatory paragraph or policy statement that drives it.
Dependencies on other change initiatives are listed in the dependencies section.
The requirements in this document do not change the existing referral indicators unless stated.
Out-of-scope items are recorded so that they can be considered for a later release.
Stakeholders have reviewed the requirements in workshops and through written comments.
Any requirement that cannot be met by the effective date must be escalated to the business owner immediately.
Management information requirements are included so that compliance can be evidenced after go-live.
Customer-facing wording is subject to review by Compliance before it is used.
""")

BANKS["opmodel"] = _lines("""
Accountability for each process stage sits with a single named role, even where several teams contribute.
Responsible teams carry out the work; the accountable role signs it off and answers for the outcome.
Consulted parties provide input before a decision is taken; informed parties are told after it is taken.
The operating model separates first-line ownership of claims processes from second-line oversight.
Hand-offs between teams are defined by the process steps, not by organisational boundaries.
Management information is produced against each step so that owners can see whether service levels are met.
Escalation routes follow the reporting lines shown in the organisation section.
Where a step is supported by both the legacy platform and Claims Hub during the transition, the accountable role is unchanged.
Teams are expected to raise process issues with the stage owner rather than introducing local workarounds.
Role descriptions will be updated to reflect the responsibilities set out in this document.
Proposed changes to the RACI are raised with the relevant stage owner.
The operating model will be reviewed after each migration wave to confirm that it still fits the way work is done.
""")

BANKS["reinsurance"] = _lines("""
Claims notifications to reinsurers are made in line with the treaty wording and the internal large loss procedure.
Cessions are calculated from the reserve and payment movements recorded in the claims system of record.
Bordereaux are reconciled to the general ledger before they are released to reinsurers.
Queries from reinsurers are logged and answered through the Reinsurance team rather than directly by claims handlers.
The treaty summary is a reference document; in the event of any difference, the signed treaty wording prevails.
Recoveries from reinsurers are monitored against the expected amounts and chased where overdue.
Claims handlers are reminded to flag potential catastrophe events promptly so that aggregation can be assessed.
Changes to treaty codes are coordinated with the administrators of the reinsurance system before each renewal.
""")


class Prose:
    """Draws sentences from the banks without immediate repetition within a document."""

    def __init__(self, rng: random.Random, date: str | None = None, forbid: tuple = (), **defaults):
        self.rng = rng
        self.date = date            # when set, system/service names are rewritten to those in use on this date
        self.forbid = tuple(forbid)  # sentences containing any of these substrings are skipped
        self.defaults = defaults
        self._pools: dict[str, list[str]] = {}

    def _draw(self, bank: str) -> str:
        pool = self._pools.get(bank)
        if not pool:
            pool = list(BANKS[bank])
            self.rng.shuffle(pool)
            self._pools[bank] = pool
        return pool.pop()

    def sentence(self, bank: str, connector_p: float = 0.18, **slots) -> str:
        s = self._draw(bank)
        vals = dict(self.defaults)
        vals.update(slots)
        if "topic" in vals and "topic_cap" not in slots:
            t = str(vals["topic"])
            vals["topic_cap"] = t[:1].upper() + t[1:]
        for k, v in list(vals.items()):
            if isinstance(v, (list, tuple)):
                vals[k] = self.rng.choice(list(v))
        try:
            s = s.format(**vals)
        except KeyError:
            return self.sentence(bank, connector_p=connector_p, **slots) if self.rng.random() < 0.9 else ""
        if self.forbid and any(f in s for f in self.forbid):
            return self.sentence(bank, connector_p=connector_p, **slots)
        if self.rng.random() < connector_p and _LOWER_OK.match(s):
            s = self.rng.choice(CONNECTORS) + s[0].lower() + s[1:]
        if self.date:
            from .core import asof
            s = asof(s, self.date)
        return s

    def para(self, banks, n=(3, 5), **slots) -> str:
        if isinstance(banks, str):
            banks = [banks]
        k = self.rng.randint(*n) if isinstance(n, tuple) else n
        out = []
        for i in range(k):
            b = banks[i % len(banks)] if i < len(banks) else self.rng.choice(banks)
            s = self.sentence(b, **slots)
            if s and s not in out:
                out.append(s)
        return " ".join(out)

    def paras(self, banks, count: int, n=(3, 5), **slots) -> list[str]:
        return [self.para(banks, n=n, **slots) for _ in range(count)]

    def intro(self, topic: str) -> str:
        return self.sentence("intro", connector_p=0, topic=topic)


from . import prose_extra  # noqa: E402,F401  (extends BANKS)
from . import prose_more  # noqa: E402,F401  (new banks for LD018-LD029)

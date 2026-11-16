"""rng-driven phrase banks for filler prose.

Filler never states a world fact: no thresholds, owners, dates, system links or table links.
Names passed in by the caller (e.g. an interface name) are the only world terms used.
"""
from __future__ import annotations

import random

_OPEN = ["", "", "In practice, ", "As a rule, ", "Note that ", "For clarity, ", "Operationally, ", "Where possible, "]

BANKS: dict[str, list[str]] = {
    "interface_ops": [
        "{x} is monitored through the standard integration dashboards and {alerting}.",
        "Changes to {x} follow the interface change checklist and need {signoff} before release.",
        "{x} carries no free-text customer notes; {pii}.",
        "Delivery failures on {x} are {handled} and raised with the owning team.",
        "The message layout of {x} is versioned, and {consumers} are told about any change in advance.",
        "{x} is listed in the interface catalogue with its owner and criticality.",
        "Test evidence for {x} is held with the release record, together with {evidence}.",
        "Volumes on {x} vary with the claims cycle; {volume}.",
        "Reprocessing of {x} is idempotent at record level, so {reprocess}.",
        "Support for {x} follows the service catalogue entry; {support}.",
        "The data owner for {x} confirms field definitions at each annual recertification.",
        "Access to {x} payloads is restricted to named support roles, and {access}.",
        "{x} is documented in the interface catalogue as the authoritative description.",
        "Any temporary workaround on {x} must be logged on the change record and removed within the next release.",
    ],
    "error_handling": [
        "Records that fail validation are written to an exception queue and reported in the morning {report}.",
        "A failed run is restarted from the last checkpoint once the cause is understood; {restart}.",
        "Duplicate detection relies on the business key, so {dup}.",
        "Schema violations are rejected at the boundary rather than corrected downstream.",
        "Operators should capture the job log and {capture} before escalating.",
        "Partial deliveries are not forwarded; the consumer waits for a complete, reconciled set.",
        "If the upstream feed is late, {late}.",
        "Error codes are mapped to the shared catalogue so that {codes}.",
        "Poison messages are parked rather than retried indefinitely, and {parked}.",
    ],
    "governance": [
        "This document is controlled; printed copies are uncontrolled.",
        "Comments should be raised with the document owner rather than edited in place.",
        "The content reflects the position on the date shown in the document control block.",
        "Superseded versions are retained in the document library for audit purposes.",
        "Approval is recorded in the change history; reviewers are listed for traceability.",
        "Terminology follows the programme glossary; system names follow the system catalogue.",
        "Where this document and the system of record disagree, the system of record prevails and the owner is informed.",
        "Distribution is internal to Corvane Mutual and the programme delivery team.",
    ],
    "data_quality": [
        "The check compares the migrated value with the CLARA source after normalisation of {norm}.",
        "Exceptions were triaged by the data migration team and {triage}.",
        "The rule is evaluated on the full migrated population, not on a sample.",
        "Results are reproducible from the reconciliation workspace using the stored query.",
        "Where an exception reflects a known CLARA data issue, {known}.",
        "The check was first run in the rehearsals and kept unchanged for the production cut-over.",
        "Business sign-off for this dimension sits with the product owner for the affected service.",
        "Exceptions are listed by claim reference only; no personal data is reproduced in this report.",
    ],
    "runbook": [
        "Before restarting, confirm with the Batch Scheduler that no dependent job has started.",
        "Check the job log for the first abend message rather than the last one.",
        "Do not cancel a job that is waiting on a dataset enqueue without consulting the on-call developer.",
        "If the same step fails twice, stop and escalate; repeated reruns make diagnosis harder.",
        "Record every manual action in the shift log with the time and the operator ID.",
        "Restarts outside the batch window need the agreement of the CLARA platform on-call lead.",
        "Data fixes are never applied directly in production tables; raise a change.",
        "Keep the incident bridge informed at regular intervals while a critical job is down.",
        "After a successful rerun, check the downstream trigger datasets were created.",
        "Abends caused by data are handed to the development team with the failing key.",
    ],
    "design": [
        "The service owns its data and exposes it only through its API and events.",
        "All writes are idempotent on the client-supplied request key.",
        "Amounts are carried in minor units with an explicit ISO 4217 currency.",
        "Time stamps are stored in UTC and rendered in the user's locale.",
        "Configuration is externalised and effective-dated where business rules require it.",
        "The service publishes domain events after the transaction commits (outbox pattern).",
        "Read models used for enquiries are rebuilt from events rather than shared tables.",
        "Health and readiness endpoints are exposed for the platform probes.",
        "Every endpoint is protected by CIS-issued tokens with role-based scopes.",
        "Contract tests run in the pipeline against the published API and event schemas.",
        "Structured logs carry a correlation identifier end to end.",
        "Breaking changes go through a new major version; the old one is retired after consumers move.",
    ],
    "wiki": [
        "This page is maintained by the owning team; please use comments for questions.",
        "Links to Jira use the CHUB project; links to code point at the main branch.",
        "If something on this page looks out of date, tell the page owner rather than editing it directly.",
        "Diagrams are exported from the architecture repository and refreshed at each release.",
        "Child pages hold the detail; this page gives the overview.",
        "Use the page tree on the left to navigate the space.",
        "Terminology follows the glossary page.",
        "Release-specific notes live on the release notes page.",
    ],
    "tests": [
        "Happy path: a valid record is delivered, acknowledged and visible in the target.",
        "A malformed record is rejected at the boundary and logged with its key.",
        "A resent record with the same business key does not create a duplicate.",
        "A late upstream delivery holds the dependent processing until it arrives.",
        "An empty delivery is processed without error and reported as zero records.",
        "A field at its maximum length is carried without truncation.",
        "A negative amount is carried with the correct sign.",
        "Nordic currency amounts keep their original currency code.",
        "Characters outside ASCII (æ, ø, å, ä, ö) survive the round trip.",
        "A restart after failure resumes without losing or repeating records.",
        "Expired credentials are rejected and the failure is alerted.",
        "A schema version mismatch is detected and the record is parked.",
    ],
    "runbook_if": [
        "Check the interface status on the integration dashboard.",
        "Confirm the upstream delivery arrived and is complete.",
        "Look for parked or rejected records and note their keys.",
        "Check the channel or connection status between the two systems.",
        "Inform the consuming teams if delivery will be late.",
        "Re-run the delivery once the cause is fixed; the process is safe to repeat.",
        "Raise an incident if the delivery misses its business deadline.",
        "Record the actions taken in the interface log.",
        "Confirm the target has loaded the delivery and reconciled the counts.",
        "Escalate to the interface owner if the cause is not clear.",
    ],
    "impact_checklist": [
        "Identify every dependent interface and confirm its owner has seen the change.",
        "Confirm whether the record layout or schema version changes.",
        "Check whether any regulatory return is fed, directly or indirectly, by the output.",
        "Agree a test window with each consuming team before the change goes live.",
        "Confirm the rollback approach and who decides to use it.",
        "Check that reconciliation counts can still be produced after the change.",
        "Update the catalogue entry and the owning team's runbook in the same release.",
        "Confirm that monitoring and alert thresholds still apply to the changed flow.",
        "Record the change ticket and the approval on the interface change log.",
        "Check whether historical data needs to be reprocessed for consumers.",
        "Tell the service desk about the change and any expected support impact.",
        "Confirm that access controls on the payload are unchanged.",
        "Check whether the batch window or trigger dependencies change.",
        "Confirm data classification and retention are unaffected.",
    ],
    "inventory_review": [
        "Entry walked through with the CLARA platform team during the inventory review.",
        "Table access confirmed against the EXEC SQL statements in the baseline source.",
        "CALL and COPY references cross-checked with the compile listings.",
        "Ownership confirmed by the developer named in this entry.",
        "Program description agreed with the owning team before publication.",
        "Copybook list taken from the COPY statements; nested copybooks are listed separately.",
        "Runtime attributes taken from the CICS and batch scheduler definitions.",
        "Migration disposition agreed with the Claims Hub squad that owns the replacement.",
        "No open review comments remain on this entry.",
        "Entry re-checked after the latest source baseline refresh.",
        "Interface and rule references taken from the programme catalogues.",
        "Process step references taken from the claims process definition.",
    ],
    "release_process": [
        "The release scope is frozen when the release branch is cut; later changes need the release manager's agreement.",
        "Every change in the release links to a CHUB ticket with test evidence attached.",
        "The release is rehearsed in pre-production with production-like data volumes.",
        "CAB reviews the release, the rollback plan and the deployment window.",
        "Deployment is a GitOps pull request; Argo CD applies it to production after approval.",
        "Smoke tests run immediately after deployment and the results are posted to the release channel.",
        "Squads monitor their dashboards for an agreed hypercare period after the release.",
        "Release notes are published on this page once CAB has approved the release.",
        "Known issues carried over are listed with their tickets so that support teams can find them.",
        "Rollback is by reverting the release tag in the GitOps repository.",
    ],
    "reconciliation": [
        "Record counts are compared between source and target after each delivery.",
        "Control totals are carried in the trailer and checked by the receiving side.",
        "The receiving side confirms counts back to the sender through the interface log.",
        "Mismatches are investigated before the next delivery is released.",
        "Daily counts are kept for audit and compared month on month by the owning team.",
        "Amount totals are reconciled by currency rather than converted.",
        "Rejected records are counted separately so that totals still balance.",
        "Reconciliation results are visible on the integration dashboard.",
    ],
    "api": [
        "Errors use the problem-details format with a stable error code.",
        "All requests must carry a correlation identifier header; it is echoed in the response.",
        "Clients should treat unknown fields as optional and ignore them.",
        "List endpoints are paginated with an opaque cursor.",
        "The API is versioned in the path; minor additions are backwards compatible.",
        "Rate limits apply per client; clients receive 429 with a retry-after header.",
        "Monetary values are integers in minor units with an ISO 4217 currency code.",
        "Dates use ISO 8601; time stamps are UTC with an explicit offset.",
    ],
}

SLOTS: dict[str, list[str]] = {
    "alerting": ["alerts go to the owning team's channel", "alerts are routed to the on-call rota",
                 "failures page the integration on-call engineer", "breaches open an incident automatically"],
    "signoff": ["sign-off from every downstream consumer", "consumer sign-off recorded on the change",
                "agreement from the consuming teams", "an impact assessment signed by each consumer"],
    "pii": ["personal data is limited to identifiers", "payloads are classified Internal",
            "only claim references and amounts are carried", "no special-category data is included"],
    "handled": ["retried by the transport layer", "parked for manual review", "logged and alerted",
                "held until the owning team releases them"],
    "consumers": ["all registered consumers", "the consuming teams", "downstream owners", "dependent interface owners"],
    "evidence": ["the reconciliation output", "the contract test results", "the sign-off record", "sample payloads"],
    "volume": ["month-end runs are noticeably heavier", "storm events cause short peaks",
               "volumes are reviewed at the capacity forum", "peaks follow weekend backlogs"],
    "reprocess": ["a rerun does not create duplicates", "replay is safe after an outage",
                  "consumers can tolerate a resend", "reruns are safe once the cause is fixed"],
    "support": ["first-line support sits with the service desk", "the owning team provides second-line support",
                "out-of-hours cover follows the platform rota", "support hours match the business service"],
    "access": ["access is reviewed quarterly", "access requests go through CIS", "break-glass access is logged",
               "production access is time-bound"],
    "report": ["exceptions report", "operations report", "interface status report", "batch summary"],
    "restart": ["the scheduler holds dependent jobs meanwhile", "dependent jobs stay on hold",
                "the operator records the restart point", "the on-call developer confirms the restart point"],
    "dup": ["resending a file is safe", "replays do not double-count", "consumers ignore repeated keys",
            "the target rejects repeated keys"],
    "capture": ["the failing record key", "the input dataset name", "the return code", "the time of failure"],
    "late": ["the downstream job waits on its trigger", "operators follow the late-feed procedure",
             "the consumer is informed through the status page", "the schedule holds the dependent job"],
    "codes": ["service desk staff can triage without specialist help", "reports are consistent across systems",
              "alerts can be grouped by cause", "trend analysis is possible"],
    "parked": ["the support team reviews them each morning", "they are released after correction",
               "the owner decides whether to replay or discard", "a ticket is opened for each one"],
    "norm": ["case and whitespace", "date formats and time zones", "currency and decimal places", "code values"],
    "triage": ["classified as fixed, accepted or open", "assigned to the owning squad",
               "reviewed with the business data owner", "logged with a disposition"],
    "known": ["the exception is accepted and documented", "the CLARA value is carried over unchanged",
              "the business owner approved the carry-over", "a correction is scheduled after cut-over"],
}


def fill(r: random.Random, template: str, x: str = "") -> str:
    out = template
    for k, opts in SLOTS.items():
        tok = "{" + k + "}"
        while tok in out:
            out = out.replace(tok, r.choice(opts), 1)
    return out.replace("{x}", x)


def sentence(r: random.Random, topic: str, x: str = "") -> str:
    s = fill(r, r.choice(BANKS[topic]), x)
    o = r.choice(_OPEN)
    if o and s and s[0].isupper() and not s.startswith(x or "\0"):
        s = o + s[0].lower() + s[1:]
    elif o and x and s.startswith(x):
        s = o + s
    return s[0].upper() + s[1:] if s else s


def paragraph(r: random.Random, topic: str, n: int = 3, x: str = "") -> str:
    picks = r.sample(BANKS[topic], min(n, len(BANKS[topic])))
    out = []
    for t in picks:
        s = fill(r, t, x)
        out.append(s[0].upper() + s[1:])
    return " ".join(out)

"""Phrase banks for filler prose. Every line here is qualitative: no thresholds, owners, dates,
system links or table links. World facts are added by the deck builders, never by these banks.
"""
from __future__ import annotations

import random
import re
from typing import Sequence

SYNONYMS = {
    "{agree}": ["agree", "confirm", "sign off", "settle"],
    "{early}": ["early", "up front", "at the start", "before build starts"],
    "{team}": ["the squad", "the team", "the delivery team", "the working group"],
    "{check}": ["check", "verify", "confirm", "validate"],
    "{issue}": ["issue", "problem", "defect", "gap"],
    "{quickly}": ["quickly", "promptly", "without delay", "as soon as practical"],
    "{users}": ["users", "colleagues", "teams", "end users"],
    "{doc}": ["the runbook", "the operating procedure", "the support guide", "the knowledge article"],
    "{review}": ["review", "walk-through", "check-point", "read-out"],
}


def _fill(rng: random.Random, s: str) -> str:
    def rep(m):
        return rng.choice(SYNONYMS[m.group(0)])
    return re.sub(r"\{[a-z]+\}", rep, s)


def pick(rng: random.Random, bank: Sequence[str], k: int) -> list[str]:
    k = min(k, len(bank))
    out = [_fill(rng, s) for s in rng.sample(list(bank), k)]
    return [s[:1].upper() + s[1:] for s in out]  # bullets always start with a capital


RISKS = [
    ("Key-person dependency on a small number of mainframe specialists",
     "Pair every change with a second developer and record walkthroughs"),
    ("Downstream consumers not engaged before interface changes",
     "Consumer sign-off is a mandatory gate in the change checklist"),
    ("Test environments drift from production configuration",
     "Configuration is version-controlled and compared before each test cycle"),
    ("Business readiness lags technical readiness",
     "Readiness criteria are owned by operations leads, not the delivery team"),
    ("Parallel change programmes compete for the same SMEs",
     "Shared resourcing calendar reviewed at each planning session"),
    ("Data quality issues surface late in migration rehearsals",
     "Profiling runs on every rehearsal extract; exceptions triaged daily"),
    ("Regulatory deadlines coincide with cut-over windows",
     "Calendar of regulatory returns checked before any freeze is agreed"),
    ("Undocumented batch dependencies discovered during decommissioning",
     "Scheduler definitions and job documentation reconciled line by line"),
    ("Training delivered too early and forgotten before go-live",
     "Short refresher sessions scheduled close to the cut-over date"),
    ("Vendor change requests take longer than planned",
     "Early engagement with vendor account teams and agreed change windows"),
    ("Monitoring gaps hide slow degradation in overnight processing",
     "Alert thresholds reviewed with operations after each incident"),
    ("Rule changes applied in one platform but not the other during co-existence",
     "Single rule register with an owner per rule and a dual-platform checklist"),
    ("Access rights carried over from old roles after organisational change",
     "Quarterly access recertification by line managers"),
    ("Ambiguous terminology between legacy screens and new screens",
     "Glossary published with training material and embedded in help text"),
    ("Hypercare demand exceeds support capacity in the first weeks",
     "Floor-walkers and an extended support desk for the first two weeks"),
]

NEXT_STEPS = [
    "Circulate this pack to stakeholders for comment",
    "Book a {review} with the operations leads",
    "Update {doc} once the decisions are recorded",
    "Raise follow-up tickets for every open action",
    "Confirm owners for the open items listed above",
    "Schedule a follow-up session with the Design Authority",
    "Publish the agreed version on the team site",
    "{check} that the support model is understood by first-line teams",
    "Add the changes to the next release notes",
    "Brief team leaders so they can cascade the message",
    "Capture lessons learned in the programme log",
    "Re-baseline the plan after the decisions are made",
    "Walk through the change with the service desk",
    "Retire superseded versions of this material",
]

PRINCIPLES = [
    "One owner per capability; no shared write access to another service's data",
    "Events describe facts that have happened; commands stay inside a service",
    "Every interface has a named owner and a documented consumer list",
    "Configuration over code for business parameters that change",
    "Design for co-existence with CLARA until decommissioning",
    "Prefer boring, well-understood technology for critical paths",
    "Observability is part of the definition of done",
    "Security and data protection reviewed at design time, not after build",
    "Idempotent processing for anything that can be retried",
    "Automate the path to production; manual steps are exceptions",
    "Backwards-compatible change by default; breaking changes need a version",
    "Keep audit trails complete: every change to money is a recorded movement",
]

LESSONS = [
    "Treat copybook and record-layout changes as interface changes",
    "A consumer impact assessment must name every downstream consumer",
    "Batch timing assumptions belong in the interface catalogue, not in people's heads",
    "Bridge calls work best with one decision-maker and a clear scribe",
    "Regulatory reporting needs to be told early, even when impact is uncertain",
    "Rollback plans should be rehearsed, not just written",
    "Monitoring should alert on rejected records, not only on job failures",
    "Change tickets need a named business approver for finance-impacting changes",
    "Keep a record-version field in fixed-width layouts so consumers can detect changes",
    "Post-incident actions need owners and due dates before the review closes",
]

FAQ = [
    ("Do I need to do anything differently today?", "No. Keep working as normal until your team leader confirms the change."),
    ("Where do I raise a problem?", "Log it with the service desk and mention the change name in the summary."),
    ("Will old reports still work?", "Yes. Saved reports keep working; titles are updated over the following weeks."),
    ("Who can I ask about the detail?", "Your team leader first, then the contacts on the last slide."),
    ("Is any data being moved?", "No data is moved as part of this change."),
    ("What about documents that use the old name?", "They stay valid. Documents are updated at their next scheduled review."),
    ("Does this affect customers?", "No customer-facing letters or screens change as a result of this briefing."),
]

TRAINING_TIPS = [
    "Use the search bar first: claim number, policy number or customer surname all work",
    "Mandatory fields are marked with an asterisk; the form will not submit without them",
    "Save as draft if the caller cannot give all details; drafts appear in your work queue",
    "Check the banner at the top of a claim for alerts before you call the customer",
    "Use keyboard tab order: fields follow the order of the conversation script",
    "Hover over a field label to see the help text and the glossary term",
    "Your work queue can be filtered by tier, product and due date",
    "Notes are timestamped and cannot be edited after saving, so write them carefully",
    "If a screen looks different from training, refresh before raising a ticket",
    "Use the 'Ask a floor-walker' button during hypercare",
]

OBJECTIVES = [
    "Replace an ageing platform with a modern, supportable claims system",
    "Give customers and handlers a faster, simpler claims journey",
    "Reduce operational risk from scarce legacy skills",
    "Make business rules visible, versioned and testable",
    "Improve the quality and timeliness of regulatory and finance data",
    "Enable new products and channels without mainframe change",
    "Retire legacy infrastructure safely and on time",
    "Build internal capability so Corvane can run and evolve the platform",
]

WAYS_OF_WORKING = [
    "Two-week sprints with a shared demo for business stakeholders",
    "Joint Corvane and IBM squads, co-located where possible",
    "Decisions recorded in the RAID log within one working day",
    "Architecture decisions captured as ADRs and reviewed at the Design Authority",
    "One backlog per squad, prioritised by the product owner",
    "Definition of done includes tests, documentation and monitoring",
    "Open, no-blame culture for incidents and near misses",
    "Weekly risk review with the programme leadership",
]

GOVERNANCE = [
    "Changes to production follow the Change Advisory Board process",
    "Material changes to rules need the rule owner's approval before release",
    "Exceptions are logged, time-boxed and reviewed at the next governance meeting",
    "This document is reviewed at least annually or after a significant change",
    "Deviations from this document must be approved by the document owner",
    "Superseded versions are archived and must not be used for decisions",
]

COMMS = [
    "Team leader cascade in the weekly huddle",
    "Intranet news item with a short explainer",
    "Updated quick-reference card at every desk",
    "Service desk script refreshed for the first weeks",
    "Short drop-in Q&A sessions for anyone with questions",
    "Reminder in the shift handover notes on the day of the change",
]

SUPPORT = [
    "Service desk: log a ticket and reference the change name",
    "Floor-walkers available on every site during the first week",
    "Daily stand-up between support and the delivery team during hypercare",
    "Known issues published and refreshed every morning",
    "Escalation through the duty manager for anything customer-impacting",
]

TEST_PRACTICES = [
    "Tests are written alongside the code and run on every commit",
    "Contract tests run in the pipeline for every producer and consumer",
    "Test data is synthetic or masked; no production personal data in test",
    "Defects found in system test are reproduced with an automated test before closure",
    "Exploratory testing sessions are time-boxed and charter-based",
    "Performance baselines are captured before every release",
    "Regression packs are reviewed each sprint and pruned when obsolete",
    "Every business rule change ships with examples agreed by the rule owner",
]

SECURITY_CONTROLS = [
    ("Credential theft", "Single sign-on with multi-factor authentication for all workforce users"),
    ("Excessive privilege", "Role-based access with least privilege and periodic recertification"),
    ("Partner misuse of APIs", "Per-client credentials and rate limiting at the gateway"),
    ("Data leakage to test", "Masked or synthetic data in all non-production environments"),
    ("Unpatched components", "Image scanning in the pipeline and a monthly patch cycle"),
    ("Secrets in source code", "Secrets held in the platform vault; repositories scanned on every push"),
    ("Insider fraud", "Segregation of duties between reserve, payment and approval roles"),
    ("Service outage", "Active/standby clusters with tested failover"),
]

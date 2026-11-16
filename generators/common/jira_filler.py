"""Shared core of the CHUB Jira filler tickets (every key in CHUB-101..CHUB-2100 that is not in key_tickets.yaml).

ST024 (CSV ticket summary) and TX070 (JSON REST export) are two snapshots of the same Jira project taken on
the same date (2026-11-11). Both render their filler tickets from the one list built here, so every filler
ticket has the same type, summary, status, assignee, reporter, created and resolved dates, component, fix
version and labels in both files. TX070 adds its richer fields (description, priority, comments, links,
changelog times, sprint) on top of this core with its own rng.

Rules the core follows (world as of each ticket's created date):
- assignees and reporters are employed on the created date; squad members are in the owning squad then, and
  service components only exist once their owning squad is formed (2025-02-03);
- summaries use the names in force on the created date (reserve-svc before 2026-02-10, FRAUDNET before
  2025-03-01, Adjuster Extranet before 2025-09-01, DOCSTOR before 2025-11-03, FNETCAL1/FNETREF1 program ids
  before 2025-03-01, ...); topics, interfaces and programs appear only once they exist;
- service ownership changes that are exclusive to another file (recovery-svc and document-svc moving to the
  new squad on 2026-11-01, CODE:c CODEOWNERS) are never implied by a filler ticket;
- filler tickets carry no rule, threshold, owner, schedule or program-table link.

Deterministic: all randomness from util.rng("jira:filler:core"); no wall clock.
"""
from __future__ import annotations

import datetime as dt
import functools
import re

from generators.common import util
from world.worldlib import load_world

W = load_world()

EXPORT = dt.date(2026, 11, 11)       # export date of both snapshots (ST024 and TX070 anchors)
START = dt.date(2025, 1, 13)         # Jira project set-up (IBM engagement start)
LAST = dt.date(2026, 11, 10)         # last filler creation date
FIRST_KEY, LAST_KEY = 101, 2100


def D(s) -> dt.date:
    return s if isinstance(s, dt.date) else dt.date.fromisoformat(str(s)[:10])


def iso(d) -> str | None:
    return d.isoformat() if d else None


# ---------------------------------------------------------------------------------------------
# Summary banks (generic engineering work only)
# ---------------------------------------------------------------------------------------------
SVC_STORY = [
    "add structured logging and correlation ids", "upgrade Spring Boot base image", "health and readiness probes for OpenShift",
    "dashboard and alerts for error rate", "improve validation error messages", "OpenAPI spec lint warnings",
    "remove deprecated endpoints", "pagination on list endpoint", "add audit fields to responses",
    "timezone handling for Nordic dates", "unit test coverage for mapper classes", "update runbook",
    "performance test against agreed volumes", "refactor configuration properties", "consumer lag metric and alert",
    "dependency updates (quarterly)", "graceful shutdown on pod eviction", "trace propagation to downstream calls",
    "clean up feature flags after release", "API documentation examples",
]
SVC_BUG = [
    "500 error when optional field is empty", "wrong date format in one response field", "log noise at INFO level",
    "memory usage grows slowly under load", "SIT2 deployment fails intermittently at image push", "flaky integration test in CI",
    "null handling for optional peril code", "health check reports UP before database connection is ready",
    "sorting ignored on list endpoint", "character encoding issue with Nordic letters in names",
    "stale cache entry after restart in SIT", "timeout too short on test environment calls",
]
CLARA_TASK = [
    "add DISPLAY diagnostics for abend analysis", "document paragraph structure for the CRUD matrix review",
    "zUnit test harness", "static analysis findings", "review SQL access paths with the DBA", "copybook usage review",
    "walkthrough with the squad for knowledge transfer", "dead code report", "compile listing archived for audit",
]
INTEG = [
    "update interface catalogue entry", "monitoring for late files", "interface specification review",
    "alert routing to the integration on-call", "test harness for replaying sample messages", "document error codes",
]
PLATFORM = [
    "OpenShift: namespace quota review", "Terraform: pin provider versions", "CI pipeline: cache Maven dependencies",
    "Platform: base image CVE patching", "Platform: backup and restore test for PostgreSQL",
    "Platform: certificate expiry monitoring", "Platform: SIT environment refresh", "Platform: cost report by namespace",
    "CI pipeline: parallelise test stages", "Platform: secrets moved to the vault integration",
    "Platform: node pool patching window", "Platform: on-call alert tuning", "Terraform: module documentation",
    "Platform: Kafka client library upgrade", "Platform: PostgreSQL minor version upgrade in SIT",
]
DMIG = [
    "Mapping review: {prod} claims", "Mapping review: {prod} reserves", "Rehearsal tooling: progress logging",
    "Reconciliation script: currency checks for {cur}", "Data quality: duplicate claimant records report",
    "Data quality: orphan document references report", "Migration runbook: review comments",
    "Extract performance: parallel unload test", "Load scripts: restartability", "Data quality: invalid postcode formats",
]
PROG = [
    "Steering pack: {month}", "RAID log review: {month}", "Programme plan: update after steering ({month})",
    "Resource plan review: {month}", "Dependency tracker clean-up", "Benefits tracking: data sources",
    "Communications plan: {month} update", "Change network: champions session ({month})",
]
FRAUD = [
    "Sentinel: score band report for the Fraud Forum", "Referral reason codes: align CLARA and Claims Hub",
    "SIU Case Manager: export field mapping review", "Fraud rules: rule catalogue entries review",
    "Fraud MI: weekly report layout", "Referral queue: report for SIU team leaders",
]
ASSESS = ["{portal}: help text review", "{portal}: access review for vendor users", "Assessment: report template review"]
EPICS = [
    "Observability uplift", "Platform hardening", "Test automation", "Security remediation", "Developer experience",
    "Performance and resilience", "Documentation and runbooks", "Knowledge transfer", "Data quality", "Accessibility review",
]
EPIC_OWNERS = ["P048", "P017", "P032"]
REPORTERS = ["P017", "P048", "P054"]
LABELS = ["tech-debt", "sit-defect", "observability", "security", "performance", "documentation"]

# squad pools: the squad's own members plus the IBM engineers who pair across squads
SQUAD_POOL = {"T27": ["P040", "P049", "P053"], "T28": ["P041", "P053"], "T29": ["P042", "P043"]}
COMP_POOL = {
    "CLARA": ["P023", "P024", "P025", "P052", "P016"], "Integration": ["P031", "P050"],
    "Platform": ["P049", "P053", "P031", "P032"], "Data Migration": ["P051", "P052", "P025"],
    "Programme": ["P048", "P047", "P017"], "Fraud": ["P027", "P042", "P054", "P037"], "Assessment": ["P033", "P040"],
}
SERVICES = ["claim-core-svc", "fnol-intake-svc", "triage-svc", "assessment-svc", "reserve-engine", "fraud-referral-svc",
            "settlement-svc", "payment-orchestrator", "recovery-svc", "document-svc", "notification-svc",
            "gl-posting-svc", "reporting-feed-svc"]
DATA_MIGRATION_FROM = dt.date(2025, 2, 17)
MIGRATION_PRODUCTS = ["PRD-MOT-DK", "PRD-HOM-DK", "PRD-MOT-UK", "PRD-HOM-UK", "PRD-COM-UK", "PRD-LIA-UK", "PRD-MOT-NO",
                      "PRD-HOM-NO", "PRD-MOT-SE", "PRD-HOM-SE"]


# ---------------------------------------------------------------------------------------------
# As-of helpers
# ---------------------------------------------------------------------------------------------
@functools.lru_cache(maxsize=1)
def _renames() -> list[tuple[str, str, str]]:
    """(date, new_name, old_name) for every system and service rename, newest first."""
    out = []
    for s in list(W.systems.values()) + list(W.services.values()):
        for rn in s.get("renames") or []:
            out.append((rn["date"], rn["to_name"], rn["from_name"]))
    return sorted(out, reverse=True)


def asof_text(text: str, d) -> str:
    """Write system and service names as they were called on date d."""
    ds = iso(D(d))
    for date, new, old in _renames():
        if ds < date and new in text:
            text = re.sub(rf"(?<![A-Za-z0-9_-]){re.escape(new)}(?![A-Za-z0-9_])", old, text)
    return text


def program_id_asof(pid: str, d) -> str:
    rf = W.programs[pid].get("renamed_from")
    if rf and iso(D(d)) < rf["date"]:
        return rf["old_id"]
    return pid


def employed(pid: str, d) -> bool:
    return W.employed(pid, iso(D(d)))


SQUAD_MEMBERS = ("P040", "P041", "P042", "P043")


def _member_ok(pid: str, team: str, d) -> bool:
    """Squad engineers count only while they are in that squad; cross-squad IBM engineers only need to be employed."""
    if not employed(pid, d):
        return False
    if pid in SQUAD_MEMBERS:
        return W.team_of(pid, iso(D(d))) == team
    return True


def _owner_change_exclusive(svc: str, d) -> bool:
    """True when the owner in force on d comes from an owner change that only another file may state."""
    s = W.services[svc]
    hist = s.get("owner_history") or []
    o = W.service_owner(svc, iso(D(d)))
    if not o or not hist or o is hist[0]:
        return False
    return bool(W.is_exclusive(f"SERVICE:{svc}", "owner_history")[0])


def service_available(svc: str, d) -> bool:
    o = W.service_owner(svc, iso(D(d)))
    if not o:
        return False
    if D(W.teams[o["team"]]["formed"]) > D(d):
        return False
    return not _owner_change_exclusive(svc, d)


def assignee_pool(comp: str, d) -> list[str]:
    if comp in SERVICES:
        team = W.service_owner(comp, iso(D(d)))["team"]
        pool = [p for p in SQUAD_POOL.get(team, ["P053"]) if _member_ok(p, team, d)]
    else:
        pool = [p for p in COMP_POOL.get(comp, ["P053"]) if employed(p, d)]
    return pool or ["P048"]


def workday(d: dt.date) -> dt.date:
    while d.weekday() >= 5:
        d += dt.timedelta(days=1)
    return d


def between(a: dt.date, b: dt.date, r) -> dt.date:
    if b <= a:
        return a
    return workday(a + dt.timedelta(days=r.randint(0, (b - a).days)))


@functools.lru_cache(maxsize=1)
def fix_versions() -> list[tuple[str, dt.date]]:
    return sorted(((v["name"], D(v["release_date"])) for v in W.raw["key_tickets"]["fix_versions"]), key=lambda x: x[1])


def next_version(d: dt.date, r) -> str:
    rel = fix_versions()
    cands = [nm for nm, rd in rel if rd >= d + dt.timedelta(days=10)]
    if not cands:
        return rel[-1][0]
    i = 0 if r.random() < 0.75 or len(cands) == 1 else 1
    return cands[i]


def release_date(fv: str) -> dt.date:
    return dict(fix_versions())[fv]


# ---------------------------------------------------------------------------------------------
# Core generation
# ---------------------------------------------------------------------------------------------
def pick_component(d: dt.date, r) -> str:
    comps = [("CLARA", 12), ("Integration", 7), ("Platform", 9), ("Programme", 5), ("Fraud", 3), ("Assessment", 1)]
    if d >= DATA_MIGRATION_FROM:
        comps.append(("Data Migration", 7))
    for s in SERVICES:
        if service_available(s, d):
            comps.append((s, 4))
    names, weights = zip(*comps)
    return r.choices(names, weights=weights)[0]


def topics_for(svc: str, d: dt.date) -> list[str]:
    s = W.services[svc]
    out = []
    kt = s.get("kafka_topics") or {}
    for t in kt.get("consumes", []) + kt.get("produces", []):
        tp = W.topics.get(t, {})
        if tp.get("introduced") and D(tp["introduced"]) > d:
            continue
        if tp.get("retired") and D(tp["retired"]) <= d:
            continue
        out.append(t)
    return out


def filler_summary(comp: str, d: dt.date, r) -> tuple[str, str]:
    month = d.strftime("%B %Y")
    if comp in SERVICES:
        nm = W.service_name(comp, iso(d))
        x = r.random()
        tps = topics_for(comp, d)
        if x < 0.12 and tps:
            return "Story", f"{nm}: contract test for {r.choice(tps)}"
        if x < 0.42:
            return "Bug", f"{nm}: {r.choice(SVC_BUG)}"
        return r.choice(["Story", "Story", "Task"]), f"{nm}: {r.choice(SVC_STORY)}"
    if comp == "CLARA":
        progs = sorted(p for p, v in W.programs.items()
                       if v.get("since") and D(v["since"]) <= d and v.get("status") == "active")
        return "Task", f"{program_id_asof(r.choice(progs), d)}: {r.choice(CLARA_TASK)}"
    if comp == "Integration":
        ifs = sorted(i for i, v in W.interfaces.items() if v.get("since") and D(v["since"]) <= d and v.get("status") == "live")
        if r.random() < 0.75:
            return "Task", f"{r.choice(ifs)}: {r.choice(INTEG)}"
        return "Task", r.choice(["MQ channel alerting review", "Integration: on-call handbook update",
                                 "Integration: message replay tool improvements"])
    if comp == "Platform":
        return r.choice(["Task", "Task", "Story"]), r.choice(PLATFORM)
    if comp == "Data Migration":
        prod = W.products[r.choice(MIGRATION_PRODUCTS)]["name"]
        t = r.choice(DMIG).replace("{prod}", prod).replace("{cur}", r.choice(["NOK", "SEK", "DKK"]))
        if d >= D(W.adrs["ADR-025"]["date"]) and r.random() < 0.08:
            t = "Masked data refresh for rehearsal environment (ADR-025)"
        return r.choice(["Story", "Task"]), t
    if comp == "Programme":
        return "Task", r.choice(PROG).replace("{month}", month)
    if comp == "Fraud":
        t = r.choice(FRAUD)
        if d >= dt.date(2026, 4, 1) and r.random() < 0.25:
            t = "FR1 return: data checks before submission"
        return "Task", t
    if comp == "Assessment":
        return "Task", r.choice(ASSESS).replace("{portal}", W.system_name("SYS17", iso(d)))
    return "Task", "General task"


def status_for(fv: str, r) -> str:
    rel = release_date(fv)
    if rel <= EXPORT:
        return r.choices(["Done", "Won't Do", "To Do", "In Progress"], weights=[92, 4, 2, 2])[0]
    if fv == "R2026.11":
        return r.choices(["Done", "In Review", "In Progress", "To Do"], weights=[50, 15, 20, 15])[0]
    return r.choices(["To Do", "In Progress", "In Review", "Done"], weights=[52, 30, 5, 13])[0]


STATUS_PATH = {"Done": ["In Progress", "In Review", "Done"], "Won't Do": ["Won't Do"], "In Review": ["In Progress", "In Review"],
               "In Progress": ["In Progress"], "To Do": []}


def _created(k: int, r) -> dt.date:
    span = (LAST - START).days
    base = START + dt.timedelta(days=int((k - FIRST_KEY) / 2000 * span))
    return min(LAST, workday(min(LAST, max(START, base + dt.timedelta(days=r.randint(-10, 10))))))


def _rec(k, typ, summary, comp, cd, status, assignee, reporter, fv, labels, transitions, pool, parent=None):
    resolved = transitions[-1]["date"] if status in ("Done", "Won't Do") and transitions else None
    return {"key": f"CHUB-{k}", "n": k, "type": typ, "summary": summary, "component": comp, "created": iso(cd),
            "status": status, "resolved": resolved, "assignee": assignee, "reporter": reporter, "fix_version": fv,
            "labels": labels, "parent": parent, "transitions": transitions, "pool": pool}


@functools.lru_cache(maxsize=1)
def filler_tickets() -> tuple[dict, ...]:
    """The filler tickets in key order. Each record: key, n, type, summary, component (None for epics),
    created, status, resolved (None unless Done/Won't Do), assignee (pid or None), reporter (pid), fix_version,
    labels, parent (sub-tasks), transitions [{date, from, to}], pool (people who work that component then)."""
    r = util.rng("jira:filler:core")
    filler_ids = [k for k in range(FIRST_KEY, LAST_KEY + 1) if f"CHUB-{k}" not in W.tickets]
    epic_slots = sorted(r.sample(filler_ids[:400], len(EPICS)))
    epic_name = dict(zip(epic_slots, EPICS))
    stories_by_comp: dict[str, list[int]] = {}
    out = []
    for k in filler_ids:
        cd = _created(k, r)
        if k in epic_name:
            owners = [p for p in EPIC_OWNERS if employed(p, cd)]
            owner = r.choice(owners)
            out.append(_rec(k, "Epic", epic_name[k], None, cd, "In Progress", owner, owner, None, [], [], owners))
            continue
        comp = pick_component(cd, r)
        typ, summary = filler_summary(comp, cd, r)
        summary = asof_text(summary, cd)
        parent = None
        if typ == "Story" and r.random() < 0.04 and stories_by_comp.get(comp):
            parent = f"CHUB-{r.choice(stories_by_comp[comp][-20:])}"
            typ = "Sub-task"
        fv = next_version(cd, r)
        status = status_for(fv, r)
        pool = assignee_pool(comp, cd)
        assignee = None if (status == "To Do" and r.random() < 0.45) else r.choice(pool)
        reporter = r.choice([p for p in REPORTERS + pool if employed(p, cd)])
        labels = []
        if r.random() < 0.3:
            labels.append(r.choice(LABELS + ["hypercare" if cd >= D(W.waves["MW-1"]["date"]) else "refinement"]))
        end = min(release_date(fv), EXPORT) if status in ("Done", "Won't Do") else EXPORT
        transitions, t_cur, prev = [], cd, "To Do"
        for s in STATUS_PATH[status]:
            t_cur = between(t_cur, end, r)
            transitions.append({"date": iso(t_cur), "from": prev, "to": s})
            prev = s
        out.append(_rec(k, typ, summary, comp, cd, status, assignee, reporter, fv, labels, transitions, pool, parent))
        if typ == "Story":
            stories_by_comp.setdefault(comp, []).append(k)
    return tuple(out)


@functools.lru_cache(maxsize=1)
def by_key() -> dict[str, dict]:
    return {t["key"]: t for t in filler_tickets()}


def reporter_of(t: dict) -> str:
    """Reporter of a key ticket: key_tickets.yaml names it where known, otherwise the assignee raised it."""
    return t.get("reporter") or t["assignee"]

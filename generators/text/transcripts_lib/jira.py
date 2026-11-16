"""TX070: Jira-style export of exactly 2,000 CHUB tickets (CHUB-101..CHUB-2100) as at 2026-11-11.

Every key ticket from key_tickets.yaml is included verbatim (summary, status as of the export date,
assignee, links). The rest are procedurally generated engineering tickets that carry no new rules,
thresholds, owners or schedules.
"""
from __future__ import annotations

import datetime as dt
import json

from generators.common import util

from .common import W, D, Facts, out_path, name, email, assert_may

FID = "TX070"
EXPORT = D("2026-11-11")
PATH = out_path(FID, "jira_export_chub_2000", "json")
SITE = "https://corvane.atlassian.example"
START = D("2025-01-13")
LAST = D("2026-11-10")

TZ = {"LOC-LON": "Europe/London", "LOC-LDS": "Europe/London", "LOC-BRS": "Europe/London", "LOC-GLA": "Europe/London",
      "LOC-OSL": "Europe/Oslo", "LOC-STO": "Europe/Stockholm", "LOC-CPH": "Europe/Copenhagen",
      "EXT-IBM-LON": "Europe/London", "EXT-IBM-OSL": "Europe/Oslo"}

STATUS_CAT = {"To Do": ("new", "To Do"), "Open": ("new", "To Do"), "In Progress": ("indeterminate", "In Progress"),
              "In Review": ("indeterminate", "In Progress"), "Done": ("done", "Done"), "Won't Do": ("done", "Done")}
STATUS_ID = {"To Do": "10000", "Open": "1", "In Progress": "3", "In Review": "10102", "Done": "10001", "Won't Do": "10103"}

LINK_TYPES = {
    "relates to": ("Relates", "relates to", "relates to", "outward"),
    "is caused by": ("Problem/Incident", "is caused by", "causes", "inward"),
    "causes": ("Problem/Incident", "is caused by", "causes", "outward"),
    "is child of": ("Parent-Child", "is child of", "is parent of", "inward"),
    "is parent of": ("Parent-Child", "is child of", "is parent of", "outward"),
    "blocks": ("Blocks", "is blocked by", "blocks", "outward"),
    "is blocked by": ("Blocks", "is blocked by", "blocks", "inward"),
    "duplicates": ("Duplicate", "is duplicated by", "duplicates", "outward"),
    "is duplicated by": ("Duplicate", "is duplicated by", "duplicates", "inward"),
}
INVERSE = {"relates to": "relates to", "blocks": "is blocked by", "is blocked by": "blocks",
           "duplicates": "is duplicated by", "is duplicated by": "duplicates"}


def _bst(d: dt.date) -> bool:
    def last_sunday(y, m):
        x = dt.date(y, m + 1, 1) - dt.timedelta(days=1) if m < 12 else dt.date(y, 12, 31)
        return x - dt.timedelta(days=(x.weekday() + 1) % 7)
    return last_sunday(d.year, 3) <= d < last_sunday(d.year, 10)


def ts(d: dt.date, minute_of_day: int) -> str:
    off = "+0100" if _bst(d) else "+0000"
    h, m = divmod(minute_of_day, 60)
    s = (minute_of_day * 7) % 60
    return f"{d.isoformat()}T{h:02d}:{m:02d}:{s:02d}.000{off}"


def user(pid):
    if pid is None:
        return None
    p = W.people[pid]
    return {"self": f"{SITE}/rest/api/2/user?accountId=acc-{pid.lower()}", "accountId": f"acc-{pid.lower()}",
            "displayName": name(pid, EXPORT), "emailAddress": email(pid, EXPORT), "active": True,
            "timeZone": TZ.get(p["location"], "Europe/London")}


def versions():
    out = {}
    import yaml
    data = yaml.safe_load((util.ROOT / "world/data/key_tickets.yaml").read_text(encoding="utf-8"))
    for i, v in enumerate(data["fix_versions"]):
        out[v["name"]] = {"self": f"{SITE}/rest/api/2/version/{10200 + i}", "id": str(10200 + i), "name": v["name"],
                          "released": D(v["release_date"]) <= EXPORT, "releaseDate": v["release_date"]}
    return out


VERSIONS = None


def fixver(nm):
    if nm is None:
        return []
    return [VERSIONS[nm]]


def next_version(d: dt.date, r) -> str:
    rel = sorted(VERSIONS.values(), key=lambda v: v["releaseDate"])
    cands = [v for v in rel if D(v["releaseDate"]) >= d + dt.timedelta(days=10)]
    if not cands:
        return rel[-1]["name"]
    i = 0 if r.random() < 0.75 or len(cands) == 1 else 1
    return cands[i]["name"]


# ---------------------------------------------------------------------------------------------
# Filler content banks (generic engineering work only)
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
COMMENTS = [
    "Picked this up.", "Code review done; two minor comments addressed.", "Deployed to SIT.", "Tested in SIT, looks good.",
    "Moving to the next sprint, waiting on environment availability.", "Reproduced in SIT. Logs attached.",
    "Can't reproduce after the latest deployment.", "Discussed at stand-up; approach agreed as per the description.",
    "Acceptance criteria updated after refinement.", "Waiting on test data.", "Merged to main.",
    "Added to the release notes.", "Pairing on this tomorrow.", "Linked the related ticket.",
    "Small change, no impact on other services.", "Needs a second reviewer.", "Demoed at sprint review.",
]
DESC = [
    "Context:\n{s}.\n\nAcceptance criteria:\n- Change made and reviewed\n- Tests added or updated\n- Deployed to SIT",
    "{s}.\n\nNotes: keep the change small and behind existing configuration where possible.",
    "As part of normal engineering hygiene: {s}.\n\nDone when merged, deployed to SIT and verified.",
    "Raised from the sprint retrospective. {s}.",
    "",
]
PRIORITIES = ["Medium", "Medium", "Medium", "Low", "High"]


def svc_assignees(svc, d):
    team = {"T27": ["P040", "P049", "P053"], "T28": ["P041", "P053"], "T29": ["P042", "P043"]}
    o = W.service_owner(svc, d)
    t = o["team"] if o else "T27"
    pool = list(team.get(t, ["P053"]))
    if "P043" in pool and d > D("2026-10-31"):
        pool.remove("P043")
    return pool


COMP_POOL = {
    "CLARA": ["P023", "P024", "P025", "P052", "P016"], "Integration": ["P031", "P050"],
    "Platform": ["P049", "P053", "P031", "P032"], "Data Migration": ["P051", "P052", "P025"],
    "Programme": ["P048", "P047", "P017"], "Fraud": ["P027", "P042", "P054", "P037"], "Assessment": ["P033", "P040"],
}
SERVICES = ["claim-core-svc", "fnol-intake-svc", "triage-svc", "assessment-svc", "reserve-engine", "fraud-referral-svc",
            "settlement-svc", "payment-orchestrator", "recovery-svc", "document-svc", "notification-svc",
            "gl-posting-svc", "reporting-feed-svc"]


def employed(pid, d):
    return W.employed(pid, d)


def pick_component(d, r):
    comps = [("CLARA", 12), ("Integration", 7), ("Platform", 9), ("Programme", 5), ("Fraud", 3), ("Assessment", 1)]
    if d >= D("2025-02-17"):
        comps.append(("Data Migration", 7))
    if d >= D("2025-02-03"):
        for s in SERVICES:
            if s in ("recovery-svc", "document-svc") and d > D("2026-10-31"):
                continue
            comps.append((s, 4))
    names, weights = zip(*comps)
    return r.choices(names, weights=weights)[0]


def topics_for(svc, d):
    s = W.services[svc]
    out = []
    for t in (s.get("kafka_topics") or {}).get("consumes", []) + (s.get("kafka_topics") or {}).get("produces", []):
        tp = W.topics.get(t, {})
        if t == "notification.fraud-notice.sent.v1":
            continue
        if tp.get("introduced") and D(tp["introduced"]) > d:
            continue
        out.append(t)
    return out


def filler_summary(comp, d, r):
    month = d.strftime("%B %Y")
    if comp in SERVICES:
        nm = W.service_name(comp, d)
        x = r.random()
        tps = topics_for(comp, d)
        if x < 0.12 and tps:
            return "Story", f"{nm}: contract test for {r.choice(tps)}"
        if x < 0.42:
            return "Bug", f"{nm}: {r.choice(SVC_BUG)}"
        return r.choice(["Story", "Story", "Task"]), f"{nm}: {r.choice(SVC_STORY)}"
    if comp == "CLARA":
        progs = [p for p, v in W.programs.items() if v.get("since") and D(v["since"]) <= d]
        return "Task", f"{r.choice(progs)}: {r.choice(CLARA_TASK)}"
    if comp == "Integration":
        ifs = [i for i, v in W.interfaces.items() if v.get("since") and D(v["since"]) <= d and v.get("status") == "live"]
        x = r.random()
        if x < 0.75:
            return "Task", f"{r.choice(ifs)}: {r.choice(INTEG)}"
        return "Task", r.choice(["MQ channel alerting review", "Integration: on-call handbook update",
                                 "Integration: message replay tool improvements"])
    if comp == "Platform":
        return r.choice(["Task", "Task", "Story"]), r.choice(PLATFORM)
    if comp == "Data Migration":
        prods = ["Motor Privat Danmark", "Hjem Danmark", "Motor Private UK", "Home Buildings & Contents UK",
                 "Commercial Property UK", "SME Liability UK", "Motor Privat Norge", "Hjem Norge", "Motor Privat Sverige",
                 "Hem Sverige"]
        t = r.choice(DMIG).replace("{prod}", r.choice(prods)).replace("{cur}", r.choice(["NOK", "SEK", "DKK"]))
        if d >= D("2025-12-15") and r.random() < 0.08:
            t = "Masked data refresh for rehearsal environment (ADR-025)"
        return r.choice(["Story", "Task"]), t
    if comp == "Programme":
        return "Task", r.choice(PROG).replace("{month}", month)
    if comp == "Fraud":
        t = r.choice(FRAUD)
        if d >= D("2026-04-01") and r.random() < 0.25:
            t = "FR1 return: data checks before submission"
        return "Task", t
    if comp == "Assessment":
        portal = W.system_name("SYS17", d)
        return "Task", r.choice(ASSESS).replace("{portal}", portal)
    return "Task", "General task"


def status_for(fv, r):
    rel = D(VERSIONS[fv]["releaseDate"])
    if rel <= EXPORT:
        return r.choices(["Done", "Won't Do", "To Do", "In Progress"], weights=[92, 4, 2, 2])[0]
    if fv == "R2026.11":
        return r.choices(["Done", "In Review", "In Progress", "To Do"], weights=[50, 15, 20, 15])[0]
    return r.choices(["To Do", "In Progress", "In Review", "Done"], weights=[52, 30, 5, 13])[0]


def sprint(d: dt.date):
    n = (d - START).days // 14 + 1
    s_start = START + dt.timedelta(days=(n - 1) * 14)
    s_end = s_start + dt.timedelta(days=13)
    state = "closed" if s_end < EXPORT else ("active" if s_start <= EXPORT else "future")
    return {"id": 400 + n, "name": f"CHUB Sprint {n}", "state": state, "startDate": ts(s_start, 540),
            "endDate": ts(s_end, 1020)}


def workday(d: dt.date) -> dt.date:
    while d.weekday() >= 5:
        d += dt.timedelta(days=1)
    return d


def between(a: dt.date, b: dt.date, r) -> dt.date:
    if b <= a:
        return a
    return workday(a + dt.timedelta(days=r.randint(0, (b - a).days)))


# ---------------------------------------------------------------------------------------------
def key_status(t):
    hist = t.get("status_history")
    if hist:
        cur = None
        for h in hist:
            if D(h["from"]) <= EXPORT:
                cur = h["status"]
        return cur, hist
    return t["status"], None


def build(facts: Facts) -> tuple[dict, int]:
    global VERSIONS
    VERSIONS = versions()
    r = util.rng(f"{FID}:tickets")
    keys = W.tickets
    issues = []
    created_of: dict[int, dt.date] = {}
    epic_keys: dict[str, list[str]] = {}
    filler_ids = [k for k in range(101, 2101) if f"CHUB-{k}" not in keys]
    span = (LAST - START).days
    # filler epics first (spread over the early part of the programme)
    epic_slots = sorted(r.sample(filler_ids[:400], len(EPICS)))
    epic_name = dict(zip(epic_slots, EPICS))

    for k in range(101, 2101):
        key = f"CHUB-{k}"
        if key in keys:
            issues.append(("key", k, keys[key]))
        else:
            issues.append(("fill", k, None))

    out = []
    stories_by_comp: dict[str, list[tuple[int, dt.date]]] = {}
    for kind, k, t in issues:
        key = f"CHUB-{k}"
        if kind == "key":
            out.append(key_issue(k, t, r))
            created_of[k] = D(t["created"])
            continue
        base = START + dt.timedelta(days=int((k - 101) / 2000 * span))
        cd = workday(min(LAST, max(START, base + dt.timedelta(days=r.randint(-10, 10)))))
        if cd > LAST:
            cd = D("2026-11-10")
        created_of[k] = cd
        if k in epic_name:
            out.append(filler_epic(k, cd, epic_name[k], r))
            continue
        comp = pick_component(cd, r)
        itype, summary = filler_summary(comp, cd, r)
        parent = None
        if itype == "Story" and r.random() < 0.04 and stories_by_comp.get(comp):
            parent = r.choice(stories_by_comp[comp][-20:])
            itype = "Sub-task"
        rec = filler_issue(k, cd, comp, itype, summary, parent, epic_name, r)
        if itype == "Story":
            stories_by_comp.setdefault(comp, []).append((k, cd))
        out.append(rec)
    # filler links (symmetric) between filler tickets of the same component
    by_key = {o["key"]: o for o in out}
    fillers = [o for o in out if o["_filler"] and o["fields"]["issuetype"]["name"] not in ("Epic", "Sub-task")]
    for o in fillers:
        if r.random() < 0.10:
            comp = o["fields"]["components"][0]["name"]
            cands = [x for x in fillers if x["fields"]["components"][0]["name"] == comp and x["key"] != o["key"]
                     and x["_k"] < o["_k"]]
            if not cands:
                continue
            tgt = r.choice(cands[-30:])
            lt = r.choices(["relates to", "blocks", "duplicates"], weights=[7, 2, 1])[0]
            add_link(o, lt, tgt)
            add_link(tgt, INVERSE[lt], o)
    for o in out:
        o.pop("_filler", None)
        o.pop("_k", None)
    doc = {
        "expand": "schema,names",
        "startAt": 0,
        "maxResults": 2000,
        "total": len(out),
        "exportInfo": {"site": SITE, "project": {"key": "CHUB", "name": "Claims Hub"},
                       "jql": "project = CHUB ORDER BY key ASC", "exportedAt": ts(EXPORT, 1062),
                       "exportedBy": user("P048"), "format": "JSON (REST API v2 issue representation)"},
        "issues": out,
    }
    assert len(out) == 2000
    idx = {o["key"]: i for i, o in enumerate(out)}
    _facts(facts, doc, idx)
    return doc, len(out)


def add_link(o, lt, tgt):
    name_, inward, outward, direction = LINK_TYPES[lt]
    link = {"id": str(300000 + len(o["fields"]["issuelinks"]) + int(o["id"]) * 3),
            "type": {"name": name_, "inward": inward, "outward": outward}}
    side = "inwardIssue" if direction == "inward" else "outwardIssue"
    link[side] = {"id": tgt["id"], "key": tgt["key"], "fields": {"summary": tgt["fields"]["summary"],
                                                                   "status": {"name": tgt["fields"]["status"]["name"]}}}
    o["fields"]["issuelinks"].append(link)


def status_obj(s):
    cat, catname = STATUS_CAT[s]
    return {"self": f"{SITE}/rest/api/2/status/{STATUS_ID[s]}", "name": s, "id": STATUS_ID[s],
            "statusCategory": {"key": cat, "name": catname}}


def base_fields(k, itype, summary, comp, created, status, assignee, reporter, fv, labels, priority, description):
    resolved = None
    return {
        "issuetype": {"name": itype, "subtask": itype == "Sub-task"},
        "project": {"key": "CHUB", "name": "Claims Hub"},
        "summary": summary,
        "description": description,
        "status": status_obj(status),
        "resolution": None,
        "resolutiondate": resolved,
        "priority": {"name": priority},
        "assignee": user(assignee),
        "reporter": user(reporter),
        "creator": user(reporter),
        "created": created,
        "updated": created,
        "components": [{"name": comp}] if comp else [],
        "fixVersions": fixver(fv),
        "labels": labels,
        "issuelinks": [],
        "comment": {"comments": [], "maxResults": 0, "total": 0, "startAt": 0},
    }


def key_issue(k, t, r):
    status, hist = key_status(t)
    created_d = D(t["created"])
    reporter = t.get("reporter") or t["assignee"]
    desc = t.get("description")
    if t["id"] == "CHUB-298" and desc:
        desc = desc.split(" Fixed by the follow-up commit")[0]
    labels = [l for l in (t.get("labels") or []) if l != "generated-filler"]
    prio = "High" if t["type"] == "Bug" else ("Highest" if "INC-2025-0412" in t["summary"] else "Medium")
    f = base_fields(k, t["type"], t["summary"], t["component"], ts(created_d, 560 + (k * 37) % 400), status,
                    t["assignee"], reporter, t.get("fix_version"), labels, prio, desc)
    resolved = t.get("resolved")
    if status in ("Done", "Won't Do") and resolved and D(resolved) <= EXPORT:
        f["resolution"] = {"name": status if status == "Won't Do" else "Done"}
        f["resolutiondate"] = ts(D(resolved), 900 + (k * 13) % 300)
    histories = []
    hid = 100000 + k * 10
    if hist:
        prev = None
        for h in hist:
            if D(h["from"]) > EXPORT:
                break
            if prev is not None:
                histories.append({"id": str(hid), "author": user(t["assignee"]), "created": ts(D(h["from"]), 600 + (k % 90)),
                                  "items": [{"field": "status", "fieldtype": "jira", "fromString": prev, "toString": h["status"]}]})
                hid += 1
            prev = h["status"]
    else:
        if status in ("Done", "Won't Do") and resolved:
            histories.append({"id": str(hid), "author": user(t["assignee"]), "created": f["resolutiondate"],
                              "items": [{"field": "status", "fieldtype": "jira", "fromString": "To Do", "toString": status}]})
        elif status in ("In Progress", "In Review"):
            d1 = between(created_d, EXPORT - dt.timedelta(days=2), r)
            histories.append({"id": str(hid), "author": user(t["assignee"]), "created": ts(d1, 630),
                              "items": [{"field": "status", "fieldtype": "jira", "fromString": "To Do", "toString": status}]})
    if histories:
        f["updated"] = histories[-1]["created"]
    for ln in t.get("links") or []:
        pass
    rec = {"expand": "operations,versionedRepresentations,editmeta,changelog,renderedFields",
           "id": str(10000 + k), "self": f"{SITE}/rest/api/2/issue/{10000 + k}", "key": t["id"], "fields": f,
           "changelog": {"startAt": 0, "maxResults": len(histories), "total": len(histories), "histories": histories},
           "_filler": False, "_k": k}
    for ln in t.get("links") or []:
        tgt_key = ln["target"]
        tk = int(tgt_key.split("-")[1])
        tgt_t = W.tickets.get(tgt_key)
        name_, inward, outward, direction = LINK_TYPES[ln["type"]]
        side = "inwardIssue" if direction == "inward" else "outwardIssue"
        f["issuelinks"].append({"id": str(21000 + k * 4 + len(f["issuelinks"])),
                                "type": {"name": name_, "inward": inward, "outward": outward},
                                side: {"id": str(10000 + tk), "key": tgt_key,
                                       "fields": {"summary": tgt_t["summary"] if tgt_t else ""}}})
    return rec


def filler_epic(k, cd, nm, r):
    reporter = r.choice(["P048", "P017", "P032"])
    f = base_fields(k, "Epic", nm, None, ts(cd, 560 + (k * 37) % 400), "In Progress", reporter, reporter,
                    None, [], "Medium", f"Umbrella epic for {nm.lower()} work across the Claims Hub squads.")
    f["customfield_10011"] = nm
    return {"expand": "operations,versionedRepresentations,editmeta,changelog,renderedFields", "id": str(10000 + k),
            "self": f"{SITE}/rest/api/2/issue/{10000 + k}", "key": f"CHUB-{k}", "fields": f,
            "changelog": {"startAt": 0, "maxResults": 0, "total": 0, "histories": []}, "_filler": True, "_k": k}


def filler_issue(k, cd, comp, itype, summary, parent, epic_name, r):
    fv = next_version(cd, r)
    status = status_for(fv, r)
    if comp in SERVICES:
        pool = svc_assignees(comp, cd)
    else:
        pool = COMP_POOL.get(comp, ["P053"])
    pool = [p for p in pool if employed(p, cd)] or ["P048"]
    assignee = None if (status == "To Do" and r.random() < 0.45) else r.choice(pool)
    rep_pool = [p for p in ["P017", "P048", "P054"] + pool if employed(p, cd)]
    reporter = r.choice(rep_pool)
    labels = []
    if r.random() < 0.3:
        labels.append(r.choice(["tech-debt", "sit-defect", "observability", "security", "performance", "documentation",
                                "hypercare" if cd >= D("2026-09-14") else "refinement"]))
    prio = r.choice(PRIORITIES) if itype != "Bug" else r.choice(["Medium", "High", "High", "Low"])
    desc = r.choice(DESC).replace("{s}", summary.split(": ", 1)[-1][:1].upper() + summary.split(": ", 1)[-1][1:])
    f = base_fields(k, itype, summary, comp, ts(cd, 540 + (k * 37) % 480), status, assignee, reporter, fv, labels,
                    prio, desc or None)
    if itype == "Story":
        f["customfield_10016"] = r.choice([1, 2, 3, 3, 5, 5, 8, 13])
    if parent:
        pk, _ = parent
        f["parent"] = {"id": str(10000 + pk), "key": f"CHUB-{pk}"}
    elif epic_name and itype in ("Story", "Task", "Bug") and r.random() < 0.18:
        ek = r.choice([e for e in epic_name if e < k] or [None])
        if ek:
            f["customfield_10014"] = f"CHUB-{ek}"
    hist = []
    hid = 100000 + k * 10
    who = assignee or reporter
    end = min(D(VERSIONS[fv]["releaseDate"]), EXPORT)
    t_cur = cd
    seq = {"Done": ["In Progress", "In Review", "Done"], "Won't Do": ["Won't Do"], "In Review": ["In Progress", "In Review"],
           "In Progress": ["In Progress"], "To Do": []}[status]
    prev = "To Do"
    for s in seq:
        t_cur = between(t_cur, end if status in ("Done", "Won't Do") else EXPORT, r)
        hist.append({"id": str(hid), "author": user(who), "created": ts(t_cur, 600 + r.randint(0, 420)),
                     "items": [{"field": "status", "fieldtype": "jira", "fromString": prev, "toString": s}]})
        hid += 1
        prev = s
    if status in ("Done", "Won't Do"):
        f["resolution"] = {"name": status}
        f["resolutiondate"] = hist[-1]["created"]
    if assignee and r.random() < 0.25:
        hist.insert(0, {"id": str(hid), "author": user(reporter), "created": ts(cd, 560 + (k * 37) % 400 + 5),
                        "items": [{"field": "assignee", "fieldtype": "jira", "fromString": None,
                                   "toString": name(assignee, EXPORT)}]})
    ncom = r.choices([0, 1, 2, 3], weights=[40, 30, 20, 10])[0]
    comments = []
    c_end = D(f["resolutiondate"][:10]) if f["resolutiondate"] else EXPORT
    for i in range(ncom):
        cdte = between(cd, c_end, r)
        body = r.choice(COMMENTS) if status != "Won't Do" or i else r.choice(
            ["Superseded by another ticket; closing.", "No longer needed after refinement.", "Duplicate; closing."])
        author = r.choice([who] + pool)
        cts = ts(cdte, 620 + r.randint(0, 400))
        comments.append({"id": str(200000 + k * 5 + i), "author": user(author), "body": body,
                         "created": cts, "updated": cts})
    comments.sort(key=lambda c: c["created"])
    f["comment"] = {"comments": comments, "maxResults": len(comments), "total": len(comments), "startAt": 0}
    stamps = [f["created"]] + [h["created"] for h in hist] + [c["created"] for c in comments]
    f["updated"] = max(stamps)
    last = f["resolutiondate"] or f["updated"]
    f["customfield_10020"] = [sprint(D(last[:10]))] if status != "To Do" or r.random() < 0.3 else []
    return {"expand": "operations,versionedRepresentations,editmeta,changelog,renderedFields", "id": str(10000 + k),
            "self": f"{SITE}/rest/api/2/issue/{10000 + k}", "key": f"CHUB-{k}", "fields": f,
            "changelog": {"startAt": 0, "maxResults": len(hist), "total": len(hist), "histories": hist},
            "_filler": True, "_k": k}


def _facts(facts: Facts, doc: dict, idx: dict):
    from .common import placement
    issues = doc["issues"]

    def F(key, ptr, needle, statement, kind="general", world_ref=None, pl=None):
        i = idx[key]
        pointer = f"/issues/{i}{ptr}"
        node = issues[i]
        for part in ptr.strip("/").split("/"):
            node = node[int(part)] if isinstance(node, list) else node[part]
        facts.add(FID, PATH, kind=kind, statement=statement, needle=needle,
                  locator={"kind": "json_pointer", "pointer": pointer}, world_ref=world_ref,
                  placement=placement(FID, pl) if pl else None,
                  text_at_locator=node if isinstance(node, str) else json.dumps(node, ensure_ascii=False))

    F("CHUB-298", "/fields/status/name", "In Review", "Jira export (2026-11-11): CHUB-298 has status 'In Review'.",
      kind="needle", pl="tx70_298")
    F("CHUB-298", "/fields/assignee/displayName", "Keith Barraclough",
      "Jira export (2026-11-11): CHUB-298 (CLRFR040 hard-coded threshold) is assigned to Keith Barraclough.",
      world_ref="TICKET:CHUB-298#assignee")
    F("CHUB-298", "/fields/summary", "CLRFR040 batch sweep hard-codes referral threshold 070",
      "CHUB-298: CLRFR040 batch sweep hard-codes referral threshold 070 (should read CLR.T_PARAM).", world_ref="TICKET:CHUB-298")
    F("CHUB-143", "/fields/summary", "Move CLX-IF-043 GL reserve journal from 03:00 to 03:45",
      "Jira export: CHUB-143 moved CLX-IF-043 (GL reserve journal) from 03:00 to 03:45.", kind="contradiction_new", pl="tx70_143")
    F("CHUB-143", "/fields/resolutiondate", "2025-05-09", "CHUB-143 was resolved on 2025-05-09.",
      kind="temporal", world_ref="TICKET:CHUB-143#resolved")
    F("CHUB-233", "/fields/summary", "Rename reserve-svc to reserve-engine",
      "Jira export: CHUB-233 renamed reserve-svc to reserve-engine (repo path, namespace labels, Terraform module) per ADR-019.",
      kind="needle", pl="tx70_233")
    F("CHUB-233", "/fields/resolutiondate", "2026-02-10", "CHUB-233 (reserve-svc to reserve-engine rename) was resolved on 2026-02-10.",
      kind="temporal", world_ref="TICKET:CHUB-233#resolved")
    F("CHUB-388", "/fields/summary", "Tier-3 referral threshold 60 from 2026-10-01",
      "CHUB-388: fraud-referral-svc Tier-3 referral threshold 60 from 2026-10-01 (workshop 2026-09-17).", world_ref="TICKET:CHUB-388")
    F("CHUB-371", "/fields/summary", "Duplicate payment instructions for 18 claims on Wave 1 weekend",
      "CHUB-371: duplicate payment instructions for 18 claims on the Wave 1 weekend (INC-2026-0914).", world_ref="TICKET:CHUB-371")
    F("CHUB-415", "/fields/status/name", "Open", "As at the 2026-11-11 export CHUB-415 (CODEOWNERS change) is still Open.",
      kind="temporal", world_ref="TICKET:CHUB-415#status_history")
    F("CHUB-421", "/fields/status/name", "In Progress", "As at the 2026-11-11 export CHUB-421 (notification-svc event) is In Progress.",
      kind="temporal", world_ref="TICKET:CHUB-421#status_history")
    F("CHUB-284", "/fields/resolution/name", "Won't Do", "CHUB-284 (IA-25-07, CLRGL090 revaluation writes no movement) was closed as Won't Do.",
      world_ref="TICKET:CHUB-284")
    F("CHUB-142", "/fields/issuelinks/0", "is caused by", "CHUB-142 (revert RM-AMOUNT) is caused by CHUB-138.",
      world_ref="TICKET:CHUB-142#links")
    F("CHUB-441", "/fields/summary", "freeze 2027-02-12 18:00 to 2027-02-15 06:00",
      "CHUB-441: Wave 2 cut-over plan v1 (freeze 2027-02-12 18:00 to 2027-02-15 06:00).", world_ref="TICKET:CHUB-441")
    F("CHUB-430", "/fields/summary", "SUBTRAK retirement (target 2026-12-31)", "CHUB-430 is the SUBTRAK retirement epic (target 2026-12-31).",
      world_ref="TICKET:CHUB-430")
    F("CHUB-322", "/fields/summary", "reserve-engine still schedules Tier-3 reviews at 21 days",
      "CHUB-322: reserve-engine still scheduled Tier-3 reviews at 21 days (INC-2026-0702).", world_ref="TICKET:CHUB-322")
    facts.add(FID, PATH, kind="scale", statement="The Jira export TX070 contains exactly 2,000 CHUB tickets (CHUB-101..CHUB-2100).",
              needle="2000", locator={"kind": "json_pointer", "pointer": "/total"}, world_ref="ANCHOR:TX070",
              text_at_locator=str(doc["total"]))
    # Every other key ticket: its summary, and its status/assignee as at the export date (all non-exclusive,
    # copied verbatim from key_tickets.yaml; checked with may_state).
    done = {(e["locator"]["pointer"].split("/")[2], e["locator"]["pointer"].split("/", 3)[3])
            for e in facts.entries if e["file"].endswith(PATH.name) and e["locator"]["pointer"].startswith("/issues/")}
    for key in sorted(W.tickets, key=lambda x: int(x.split("-")[1])):
        t = W.tickets[key]
        i = str(idx[key])
        for f in ("summary", "status", "assignee"):
            assert_may(FID, f"TICKET:{key}", f)
        fl = issues[idx[key]]["fields"]
        comp = fl["components"][0]["name"] if fl["components"] else "no component"
        if (i, "fields/summary") not in done:
            F(key, "/fields/summary", t["summary"],
              f"{key} ({t['type']}, {comp}) in the Jira export: {t['summary']}.", world_ref=f"TICKET:{key}")
        if (i, "fields/status/name") not in done:
            st = fl["status"]["name"]
            who = (fl.get("assignee") or {}).get("displayName") or "unassigned"
            F(key, "/fields/status/name", st,
              f"As at the 2026-11-11 Jira export, {key} has status '{st}' (assignee {who}).",
              kind="temporal" if t.get("status_history") else "general",
              world_ref=f"TICKET:{key}#status_history" if t.get("status_history") else f"TICKET:{key}#status")


def write(facts: Facts):
    doc, n = build(facts)
    PATH.parent.mkdir(parents=True, exist_ok=True)
    PATH.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return PATH, n

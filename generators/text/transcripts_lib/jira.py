"""TX070: Jira-style export of exactly 2,000 CHUB tickets (CHUB-101..CHUB-2100) as at 2026-11-11.

Every key ticket from key_tickets.yaml is included verbatim (summary, status as of the export date,
assignee, links). The rest are filler engineering tickets that carry no new rules, thresholds, owners or
schedules. Their core (type, summary, status, assignee, reporter, created/resolved dates, component, fix
version, labels, status transitions) comes from generators/common/jira_filler.py, shared with ST024, which
is a snapshot of the same project on the same date. This module adds the richer export fields on top
(description, priority, story points, epic link, comments, links, changelog times, sprint).
"""
from __future__ import annotations

import datetime as dt
import json

from generators.common import util
from generators.common import jira_filler as JF

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


# ---------------------------------------------------------------------------------------------
# Rich-field banks (TX070 only; the summary banks live in generators/common/jira_filler.py)
# ---------------------------------------------------------------------------------------------
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


def sprint(d: dt.date):
    n = (d - START).days // 14 + 1
    s_start = START + dt.timedelta(days=(n - 1) * 14)
    s_end = s_start + dt.timedelta(days=13)
    state = "closed" if s_end < EXPORT else ("active" if s_start <= EXPORT else "future")
    return {"id": 400 + n, "name": f"CHUB Sprint {n}", "state": state, "startDate": ts(s_start, 540),
            "endDate": ts(s_end, 1020)}


workday = JF.workday
between = JF.between


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
    core = JF.by_key()
    epic_keys = [t["n"] for t in JF.filler_tickets() if t["type"] == "Epic"]
    out = []
    for k in range(101, 2101):
        key = f"CHUB-{k}"
        if key in keys:
            out.append(key_issue(k, keys[key], r))
        elif core[key]["type"] == "Epic":
            out.append(filler_epic(core[key], r))
        else:
            out.append(filler_issue(core[key], epic_keys, r))
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
    reporter = JF.reporter_of(t)
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


def filler_epic(c, r):
    k, cd, nm, owner = c["n"], D(c["created"]), c["summary"], c["assignee"]
    f = base_fields(k, "Epic", nm, None, ts(cd, 560 + (k * 37) % 400), c["status"], owner, c["reporter"],
                    None, list(c["labels"]), "Medium", f"Umbrella epic for {nm.lower()} work across the Claims Hub squads.")
    f["customfield_10011"] = nm
    return {"expand": "operations,versionedRepresentations,editmeta,changelog,renderedFields", "id": str(10000 + k),
            "self": f"{SITE}/rest/api/2/issue/{10000 + k}", "key": c["key"], "fields": f,
            "changelog": {"startAt": 0, "maxResults": 0, "total": 0, "histories": []}, "_filler": True, "_k": k}


def filler_issue(c, epic_keys, r):
    """Render one filler ticket: the shared core (jira_filler) plus TX070's rich fields."""
    k, cd, itype, summary, comp = c["n"], D(c["created"]), c["type"], c["summary"], c["component"]
    status, fv, assignee, reporter, pool = c["status"], c["fix_version"], c["assignee"], c["reporter"], c["pool"]
    prio = r.choice(PRIORITIES) if itype != "Bug" else r.choice(["Medium", "High", "High", "Low"])
    desc = r.choice(DESC).replace("{s}", summary.split(": ", 1)[-1][:1].upper() + summary.split(": ", 1)[-1][1:])
    created_min = 540 + (k * 37) % 480
    f = base_fields(k, itype, summary, comp, ts(cd, created_min), status, assignee, reporter, fv, list(c["labels"]),
                    prio, desc or None)
    if itype == "Story":
        f["customfield_10016"] = r.choice([1, 2, 3, 3, 5, 5, 8, 13])
    if c["parent"]:
        pk = int(c["parent"].split("-")[1])
        f["parent"] = {"id": str(10000 + pk), "key": c["parent"]}
    elif itype in ("Story", "Task", "Bug") and r.random() < 0.18:
        ek = r.choice([e for e in epic_keys if e < k] or [None])
        if ek:
            f["customfield_10014"] = f"CHUB-{ek}"
    hist = []
    hid = 100000 + k * 10
    who = assignee or reporter
    last_day, last_min = cd, created_min
    for tr in c["transitions"]:
        day = D(tr["date"])
        lo = last_min + 5 if day == last_day else 600
        minute = min(1439, lo + r.randint(0, max(0, min(420, 1435 - lo))))
        hist.append({"id": str(hid), "author": user(who), "created": ts(day, minute),
                     "items": [{"field": "status", "fieldtype": "jira", "fromString": tr["from"], "toString": tr["to"]}]})
        hid += 1
        last_day, last_min = day, minute
    if status in ("Done", "Won't Do"):
        f["resolution"] = {"name": status}
        f["resolutiondate"] = hist[-1]["created"]
        assert f["resolutiondate"][:10] == c["resolved"]
    if assignee and r.random() < 0.25:
        hist.insert(0, {"id": str(hid), "author": user(reporter), "created": ts(cd, created_min + 5),
                        "items": [{"field": "assignee", "fieldtype": "jira", "fromString": None,
                                   "toString": name(assignee, EXPORT)}]})
    ncom = r.choices([0, 1, 2, 3], weights=[40, 30, 20, 10])[0]
    comments = []
    c_end = D(c["resolved"]) if c["resolved"] else EXPORT
    for i in range(ncom):
        cdte = between(cd, c_end, r)
        body = r.choice(COMMENTS) if status != "Won't Do" or i else r.choice(
            ["Superseded by another ticket; closing.", "No longer needed after refinement.", "Duplicate; closing."])
        author = r.choice([who] + pool)
        cmin = 620 + r.randint(0, 400)
        if cdte == cd:
            cmin = max(cmin, created_min + 10)
        cts = ts(cdte, min(1439, cmin))
        comments.append({"id": str(200000 + k * 5 + i), "author": user(author), "body": body,
                         "created": cts, "updated": cts})
    comments.sort(key=lambda x: x["created"])
    f["comment"] = {"comments": comments, "maxResults": len(comments), "total": len(comments), "startAt": 0}
    stamps = [f["created"]] + [h["created"] for h in hist] + [x["created"] for x in comments]
    f["updated"] = max(stamps)
    last = f["resolutiondate"] or f["updated"]
    f["customfield_10020"] = [sprint(D(last[:10]))] if status != "To Do" or r.random() < 0.3 else []
    return {"expand": "operations,versionedRepresentations,editmeta,changelog,renderedFields", "id": str(10000 + k),
            "self": f"{SITE}/rest/api/2/issue/{10000 + k}", "key": c["key"], "fields": f,
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

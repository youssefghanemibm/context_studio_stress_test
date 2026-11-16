"""World-data helpers for Claims Hub services, CLARA programs/tables/jobs and interfaces (as-of aware)."""
from __future__ import annotations

import re

from .core import Ctx, W

ALWAYS_EXCLUDED_TOPICS = {"notification.fraud-notice.sent.v1"}      # exclusive to code variant c
CIRCULAR_TOPICS = {"fraud.referral.notice-due.v1"}                     # exists only for NISA Circular 2026/04

_SVC_DESC_PRE_CIRCULAR = {
    "fraud-referral-svc": "Fraud referral decisions and hand-off of referred claims to the Special Investigations Unit",
    "notification-svc": "Customer communications via Notify (acknowledgements, claim updates and recovery letters)",
    "reporting-feed-svc": "Regulatory extracts to the NISA Reporting Hub (to replace the CLARA NISA extracts)",
}


def clean_desc(s: str) -> str:
    """Drop parentheticals that carry dates, tickets or numeric parameters (keeps generic descriptions)."""
    s = re.sub(r"\s*\((?=[^)]*(\d{4}|CHUB-|BR-|\d+ ))[^)]*\)", "", s)
    return s.strip()


def topics_ok(ctx: Ctx, names) -> list[str]:
    out = []
    for t in names:
        if t in ALWAYS_EXCLUDED_TOPICS:
            continue
        if t in CIRCULAR_TOPICS and ctx.date < "2025-11-20":
            continue
        if not ctx.ok(f"TOPIC:{t}"):
            continue
        out.append(ctx.a(t))
    return out


def svc_desc(ctx: Ctx, name: str) -> str:
    s = W.services[name]
    if ctx.date < "2025-11-20" and name in _SVC_DESC_PRE_CIRCULAR:
        return _SVC_DESC_PRE_CIRCULAR[name]
    return ctx.a(clean_desc(s["description"]))


def svc_apis(ctx: Ctx, name: str) -> list[dict]:
    s = W.services[name]
    out = []
    for a in s["apis"]:
        if ctx.date < "2025-11-20" and "customer-notice" in a["path"]:
            continue
        out.append({"method": a["method"], "path": a["path"], "summary": ctx.a(a["summary"])})
    return out


def svc_owner(ctx: Ctx, name: str) -> tuple[str, str] | None:
    o = W.service_owner(name, ctx.date)
    if not o:
        return None
    return o["team"], o["person"]


def svc_tables(ctx: Ctx, name: str) -> list[str]:
    s = W.services[name]
    out = []
    for t in s["postgres_tables"]:
        if ctx.date < "2025-11-20" and t == "fraud.customer_notice":
            continue
        out.append(t)
    return out


def table_columns(ctx: Ctx, tname: str) -> list[dict]:
    t = W.tables[tname]
    cols = []
    for c in t["columns"]:
        if ctx.date < "2026-09-14" and c["name"] == "idempotency_key":
            continue
        cols.append(c)
    return cols


def programs_asof(ctx: Ctx, area: str | None = None) -> list[dict]:
    out = []
    for p in W.programs.values():
        if str(p["since"]) > ctx.date:
            continue
        if area and p["area"] != area:
            continue
        out.append(p)
    return out


PROGRAM_DESC_OVERRIDES = {
    # description as it read before the 2026 fraud-rule changes
    "CLRFR140": lambda ctx, v: f"Auto-decline sweep (FRAUDNET/Sentinel score at or above the auto-decline threshold, {v})",
    "CLRFR030": lambda ctx, v: "Fraud referral creation – online (threshold read from CLR.T_PARAM)",
}


def program_desc(ctx: Ctx, pid: str) -> str:
    p = W.programs[pid]
    if pid == "CLRFR140":
        v = ctx.rule("BR-FRD-019")
        rule = f"BR-FRD-019 v{v['version']}" if v else "BR-FRD-019"
        name = "FRAUDNET" if ctx.date < "2025-03-01" else "Sentinel"
        thr = v["parameters"]["threshold"] if v else None
        return f"Auto-decline sweep ({name} score ≥ {thr}, {rule})" if thr else "Auto-decline sweep"
    desc = p["description"]
    if pid == "CLRFN050" and ctx.date < "2023-03-01":
        desc = "Photo and telematics reference import"
    if pid == "CLRCM100":
        desc = "Document reference writer (DOCSTOR)" if ctx.date < "2025-11-03" else "Document reference writer (Evidence Vault)"
    return ctx.a(desc)


def jobs_asof(ctx: Ctx) -> list[dict]:
    out = []
    for j in W.jcl_jobs.values():
        progs = [s["program"] for s in j["steps"]]
        if any(str(W.programs[p]["since"]) > ctx.date for p in progs if p in W.programs):
            continue
        out.append(j)
    return out


def job_schedule(ctx: Ctx, job: dict) -> str | None:
    """Schedule as of the document date, or None when the schedule may not be stated here."""
    if not ctx.ok(f"JCL:{job['name']}", "schedule"):
        return None
    sch = job["schedule"]
    if job["name"] == "CLRNFR99" and ctx.date < "2026-04-01":
        return "daily 00:45"
    if "(2026-" in sch:
        return None
    return sch


def interfaces_asof(ctx: Ctx, include_planned: bool = False) -> list[dict]:
    out = []
    for i in W.interfaces.values():
        live = str(i["since"]) <= ctx.date
        if not live and not include_planned:
            continue
        out.append(i)
    return out


def iface_schedule(ctx: Ctx, iid: str) -> str | None:
    if not ctx.ok(f"INTERFACE:{iid}", "schedule"):
        return None
    return W.interface_schedule(iid, ctx.date)


def owner_name(ctx: Ctx, pid: str | None) -> str:
    if not pid or not ctx.employed(pid):
        return "—"
    return ctx.name(pid)


def rules_for_service(ctx: Ctx, svc: str) -> list[tuple[str, str, int]]:
    """(rule id, title, version) of rules in force at the document date implemented by a service."""
    out = []
    for rid, r in W.rules.items():
        if svc not in (r.get("implemented_in", {}) or {}).get("services", []):
            continue
        v = ctx.rule(rid)
        if not v:
            continue
        out.append((rid, r["title"], v["version"]))
    return out


def rules_for_program(ctx: Ctx, pid: str) -> list[tuple[str, str, int]]:
    out = []
    for rid, r in W.rules.items():
        if pid not in (r.get("implemented_in", {}) or {}).get("programs", []):
            continue
        v = ctx.rule(rid)
        if not v:
            continue
        out.append((rid, r["title"], v["version"]))
    return out


def interfaces_for_service(ctx: Ctx, svc: str) -> list[dict]:
    return [i for i in W.interfaces.values() if svc in (i.get("services") or [])]


def interfaces_for_program(ctx: Ctx, pid: str) -> list[dict]:
    return [i for i in W.interfaces.values() if pid in (i.get("programs") or []) and str(i["since"]) <= ctx.date]


def steps_for_service(ctx: Ctx, svc: str) -> list[dict]:
    return [s for s in W.steps.values() if svc in (s.get("services") or [])]

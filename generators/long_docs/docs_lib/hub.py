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


def _write_off_summary(ctx: Ctx, summary: str) -> str:
    """The recovery write-off approval quoted with the BR-REC-011 version in force on the document date."""
    v = ctx.rule("BR-REC-011")
    if not v or v.get("effective_to") is None:
        return summary
    p = v["parameters"]
    return f"Write off (approval above £{p['min_gbp']:,} by the {p['approver']})"


def svc_apis(ctx: Ctx, name: str) -> list[dict]:
    s = W.services[name]
    out = []
    for a in s["apis"]:
        if ctx.date < "2025-11-20" and "customer-notice" in a["path"]:
            continue
        summary = a["summary"]
        if a["path"].endswith("/write-off"):
            summary = _write_off_summary(ctx, summary)
        out.append({"method": a["method"], "path": a["path"], "summary": ctx.a(summary)})
    return out


# ----------------------------------------------------------------------------------- as-of text helpers

def step_desc(ctx: Ctx, sid: str) -> str:
    """Process-step description as it read on the document date.

    process.yaml carries the current description; PS-RSV-03 names the 14-day Tier-3 cadence (BR-RSV-007 v3,
    approved 2026-06-09, effective 2026-07-01). Earlier documents give the cadence in force on their date."""
    desc = W.steps[sid]["description"]
    if sid == "PS-RSV-03":
        cur = W.rules["BR-RSV-007"]["versions"][-1]
        if ctx.date < str(cur["approved_on"]):
            v = ctx.rule("BR-RSV-007")
            desc = f"Review reserves; Tier-3 every {v['parameters']['review_days']} days." if v else "Review reserves."
    return ctx.a(desc)


def _rule_known(rid: str, date: str) -> bool:
    r = W.rules.get(rid)
    if not r:
        return True
    first = min((str(v.get("approved_on") or v.get("effective_from") or "9999")) for v in r["versions"])
    return first <= date


def col_desc(ctx: Ctx, desc: str) -> str:
    """Column description without rule references (and the values they carry) that post-date the document."""
    desc = desc or ""

    def _paren(m):
        ids = re.findall(r"BR-[A-Z]+-\d{3}", m.group(0))
        return m.group(0) if all(_rule_known(r, ctx.date) for r in ids) else ""
    desc = re.sub(r"\s*\([^)]*BR-[A-Z]+-\d{3}[^)]*\)", _paren, desc)
    if ctx.date < "2026-03-16":   # SNT-4.2 was calibrated on 2026-03-16 (the SNT short form dates from 2025-03-01)
        desc = re.sub(r"\s*\(e\.g\. SNT-[\d.]+\)", "", desc)
    return ctx.a(desc).strip()


# Team names adopted at the 2025-09-01 re-organisation, as they appear in undated world strings (location
# functions, glossary definitions); earlier documents use the names in force before the re-organisation.
_ORG_RENAMES = [
    ("2025-09-01", "the Counter-Fraud & SIU team", "the Special Investigations Unit (SIU)"),
    ("2025-09-01", "Counter-Fraud & SIU", "Special Investigations Unit (SIU)"),
    ("2025-09-01", "Group Recoveries & Subrogation", "Group Recoveries"),
    ("2025-09-01", "Recoveries & Subrogation (UK)", "Recoveries (UK)"),
    ("2025-09-01", "Recoveries & Subrogation (Group)", "Recoveries"),
    ("2025-09-01", "Claims Operations (Group)", "Claims Operations UK"),
]


def org_asof(ctx: Ctx, text: str) -> str:
    """Team names in undated org strings, as named on the document date (not for person titles)."""
    for cut, new, old in _ORG_RENAMES:
        if ctx.date < cut and new in text:
            text = text.replace(new, old)
    return text


def copybooks_asof(ctx: Ctx, p: dict) -> list[str]:
    """Copybooks of a program that existed on the document date (FRDNOT01 came with CLR.T_FRAUD_NOTIFICATION)."""
    created = str(W.tables["CLR.T_FRAUD_NOTIFICATION"].get("created") or "0000")
    return [c for c in p.get("copybooks", []) if not (c == "FRDNOT01" and ctx.date < created)]


def job_status(ctx: Ctx, job: dict) -> str:
    """Job status on the document date (CLRNFR99 was disabled only on 2026-04-01, CHUB-207)."""
    st = job.get("status", "active")
    if st == "disabled" and job["name"] == "CLRNFR99" and ctx.date < "2026-04-01":
        return "active"
    return st


def adr_ranges(ctx: Ctx) -> str:
    """The ADRs that exist on the document date, as compact id ranges (ADR-001 to ADR-013, ...)."""
    nums = sorted(int(a["id"][4:]) for a in W.adrs.values() if str(a["date"]) <= ctx.date)
    if not nums:
        return "—"
    runs, start, prev = [], nums[0], nums[0]
    for n in nums[1:] + [None]:
        if n is not None and n == prev + 1:
            prev = n
            continue
        runs.append(f"ADR-{start:03d}" if start == prev else f"ADR-{start:03d} to ADR-{prev:03d}")
        if n is not None:
            start = prev = n
    return runs[0] if len(runs) == 1 else ", ".join(runs[:-1]) + " and " + runs[-1]


def program_renames(ctx: Ctx) -> dict[str, str]:
    """Current program id -> id in use on the document date (programs.yaml renamed_from)."""
    out = {}
    for pid, p in W.programs.items():
        rf = p.get("renamed_from")
        if rf and ctx.date < str(rf["date"]):
            out[pid] = rf["old_id"]
    return out


def apply_program_renames(doc) -> None:
    """Rewrite current program ids into the ids in use on the document date, everywhere in the document text.

    Fact needles are rewritten too; facts never carry a renamed id in their needle today."""
    ren = program_renames(doc.ctx)
    if not ren:
        return
    pat = re.compile(r"\b(" + "|".join(map(re.escape, ren)) + r")\b")

    def fix(v):
        if isinstance(v, str):
            return pat.sub(lambda m: ren[m.group(1)], v)
        if isinstance(v, list):
            return [fix(x) for x in v]
        if isinstance(v, tuple):
            return tuple(fix(x) for x in v)
        if isinstance(v, dict):
            return {k: (x if k in ("path",) else fix(x)) for k, x in v.items()}
        return v
    for b in doc.blocks:
        b.data = {k: (x if k in ("path", "footnote_facts") else fix(x)) for k, x in b.data.items()}
    doc.headings = [(lvl, fix(t)) for lvl, t in doc.headings]
    for f in doc.all_facts():
        f.needle = fix(f.needle)
        if f.anchor_text:
            f.anchor_text = fix(f.anchor_text)


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
    desc = _drop_future_interfaces(ctx, desc)
    return ctx.a(desc)


def _drop_future_interfaces(ctx: Ctx, desc: str) -> str:
    """Remove interface ids (e.g. '(CLX-IF-019)') that were not live on the document date."""
    def _paren(m):
        inner = m.group(1)
        ids = []
        for mm in re.finditer(r"CLX-IF-(\d{3})((?:/\d{3})*)", inner):
            ids += ["CLX-IF-" + mm.group(1)] + ["CLX-IF-" + x for x in mm.group(2).split("/") if x]
        if all(str(W.interfaces[i]["since"]) <= ctx.date for i in ids if i in W.interfaces):
            return m.group(0)
        keep = [x.strip() for x in inner.split(",") if "CLX-IF-" not in x]
        return f" ({', '.join(keep)})" if keep else ""
    return re.sub(r"\s*\(([^)]*CLX-IF-\d{3}[^)]*)\)", _paren, desc)


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

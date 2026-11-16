"""Validate the world model: referential integrity, date logic, counts, coordination files, denylist.

    .venv/bin/python -I world/validate_world.py      (exit code 0 = pass)
"""
from __future__ import annotations

import datetime as dt
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import yaml  # noqa: E402

from world.worldlib import load_world, parse_ref  # noqa: E402

TODAY = "2026-11-15"
LAST_DOC = "2026-11-12"
MODEL_START = "2021-01-04"
KINDS = {"needle", "definition", "use_of_definition", "split_boundary", "multipage_table", "visual_only", "arrow_only", "lane_only", "chart_only",
         "image_text", "image_table", "screenshot", "speaker_notes", "alt_text", "comment", "tracked_insert", "tracked_delete", "header", "footer",
         "footnote", "hidden_sheet", "merged_cell", "contradiction_old", "contradiction_new", "draft", "approved", "alias_use", "terminology",
         "temporal", "aggregate_source", "code_fact", "commit_fact", "canary", "resync_change", "pii_probe", "injection_probe",
         "rejected_format_fact", "scale", "general"}

ERRORS: list[str] = []
WARNINGS: list[str] = []


def err(msg):
    ERRORS.append(msg)


def warn(msg):
    WARNINGS.append(msg)


def nextday(s):
    return (dt.date.fromisoformat(s) + dt.timedelta(days=1)).isoformat()


def check_periods(label, periods, start=None, end=None, contiguous=True):
    """periods: list of {from, to}; checks order, no overlap, contiguity."""
    prev = None
    for i, p in enumerate(periods):
        f, t = p.get("from"), p.get("to")
        if f and t and t < f:
            err(f"{label}: period {i} ends before it starts ({f}..{t})")
        if prev is not None:
            pt = prev.get("to")
            if pt is None:
                err(f"{label}: open period followed by another period")
            elif f and f <= pt:
                err(f"{label}: periods overlap ({pt} / {f})")
            elif contiguous and f and nextday(pt) != f:
                err(f"{label}: gap between {pt} and {f}")
        prev = p
    if periods and end is not None and periods[-1].get("to") != end:
        err(f"{label}: last period ends {periods[-1].get('to')} but expected {end}")
    if periods and start is not None and periods[0].get("from") and periods[0]["from"] < start:
        err(f"{label}: starts {periods[0]['from']} before {start}")


def main():
    W = load_world()
    P = W.people

    def person(pid, label, date=None, allow_none=False):
        if pid is None:
            if not allow_none:
                err(f"{label}: missing person")
            return
        if pid not in P:
            err(f"{label}: unknown person {pid}")
            return
        if date and not W.employed(pid, date):
            err(f"{label}: {pid} not employed on {date}")

    employers = {"ORG-CORVANE", "ORG-IBM", "REG-NISA"} | set(W.vendors)
    # ------------------------------------------------------------------ people
    for pid, p in P.items():
        if p["employer"] not in employers:
            err(f"{pid}: unknown employer {p['employer']}")
        if p["location"] not in W.locations:
            err(f"{pid}: unknown location {p['location']}")
        e = p["employment"]
        check_periods(f"{pid}.titles", p["titles"], start=e["from"], end=e["to"])
        if p["titles"] and p["titles"][0]["from"] != e["from"]:
            err(f"{pid}: first title does not start at employment start")
        if p["reports_to"]:
            check_periods(f"{pid}.reports_to", p["reports_to"], end=e["to"])
        if p["teams"]:
            check_periods(f"{pid}.teams", p["teams"], end=e["to"])
        for t in p["teams"]:
            if t["team_id"] not in W.teams:
                err(f"{pid}: unknown team {t['team_id']}")
        for r in p["reports_to"]:
            if r["manager_id"] == pid:
                err(f"{pid}: reports to self")
            if r["manager_id"] is not None and r["manager_id"] not in P:
                err(f"{pid}: unknown manager {r['manager_id']}")
        for lh in p.get("location_history", []):
            if lh["location"] not in W.locations:
                err(f"{pid}: unknown location {lh['location']}")
        if p["employer"] == "ORG-CORVANE" and p.get("email") and not p["email"].endswith("@corvane-mutual.example"):
            err(f"{pid}: Corvane email domain")
        if p["employer"] == "ORG-IBM" and not p["email"].endswith("@ibm-consulting.example"):
            err(f"{pid}: IBM email domain")
        if p["employer"] not in ("ORG-CORVANE", "ORG-IBM") and not p["email"].endswith(".example"):
            err(f"{pid}: external email must use .example")
    # reporting tree at every boundary date
    dates = {MODEL_START, TODAY, "2024-03-01"}
    for p in P.values():
        for coll in ("titles", "reports_to", "teams"):
            for x in p[coll]:
                for k in ("from", "to"):
                    if x.get(k) and MODEL_START <= x[k] <= TODAY:
                        dates.add(x[k])
                        if k == "to":
                            dates.add(nextday(x[k]))
    for date in sorted(dates):
        if not W.reports_tree_ok(date):
            err(f"reporting cycle on {date}")
        for pid, p in P.items():
            if not W.employed(pid, date) or not p["reports_to"]:
                continue
            m = W.manager_of(pid, date)
            if date < p["reports_to"][0]["from"]:
                continue
            if m is None:
                if p["employer"] == "ORG-CORVANE" and W.title_of(pid, date) != "Chief Executive Officer":
                    err(f"{pid}: no manager on {date}")
                continue
            if not W.employed(m, date):
                err(f"{pid}: manager {m} not employed on {date}")
            if P[m]["employer"] != p["employer"]:
                err(f"{pid}: manager {m} has a different employer")
    # trap checks
    if W.alias_holder("the CFO", "2025-06-30") != "P002" or W.alias_holder("the CFO", "2025-07-01") != "P001":
        err("trap (a): 'the CFO' must be P002 until 2025-06-30 and P001 from 2025-07-01")
    names = {}
    for pid, p in P.items():
        names.setdefault(p["name"], []).append(pid)
    dups = {n: v for n, v in names.items() if len(v) > 1}
    if not dups:
        err("trap (b): no two people share a full name")
    for n, ids in dups.items():
        a, b = (P[i] for i in ids[:2])
        if a["location"] == b["location"] or a["team"] == b["team"] or (a["employer"] == b["employer"] and a["titles"][-1]["title"] == b["titles"][-1]["title"]):
            err(f"trap (b): namesakes {ids} not distinguished")
    changed = [pid for pid, p in P.items()
               if W.title_of(pid, "2025-08-31") and W.title_of(pid, "2025-09-01") and W.title_of(pid, "2025-08-31") != W.title_of(pid, "2025-09-01")
               and W.manager_of(pid, "2025-08-31") != W.manager_of(pid, "2025-09-01")]
    if len(changed) < 3:
        err(f"trap (c): only {changed} change title and manager on 2025-09-01")
    if W.alias_holder("the Claims Director", TODAY) != "P005" or W.name_of("P005", "2025-01-01") != "Ingrid Sørensen" or W.name_of("P005", TODAY) != "Ingrid Ashby":
        err("trap (d): Claims Director name change not modelled")
    # ------------------------------------------------------------------ org
    for t in W.teams.values():
        for lh in t["lead_history"]:
            person(lh["person"], f"team {t['id']} lead", lh["from"] if lh["from"] >= MODEL_START else None)
            if lh["person"] in P and lh["to"] and not W.employed(lh["person"], lh["to"]):
                err(f"team {t['id']}: lead {lh['person']} not employed at {lh['to']}")
        check_periods(f"team {t['id']}.lead_history", t["lead_history"])
        for dh in t["department_history"]:
            if dh["department"] not in W.departments:
                err(f"team {t['id']}: unknown department")
    for d in W.departments.values():
        for h in d["head_history"]:
            person(h["person"], f"dept {d['id']} head")
    for c in W.committees.values():
        for m in c["members"]:
            person(m, f"committee {c['id']} member")
        for h in c["chair_history"]:
            person(h["person"], f"committee {c['id']} chair")
    # ------------------------------------------------------------------ systems
    for s in W.systems.values():
        person(s["owner"], f"system {s['id']} owner")
        for oh in s.get("owner_history", []):
            person(oh["person"], f"system {s['id']} owner_history")
        rd = [r["date"] for r in s["renames"]]
        if rd != sorted(rd):
            err(f"system {s['id']}: renames unsorted")
        if s.get("vendor") and s["vendor"] not in W.vendors:
            err(f"system {s['id']}: unknown vendor")
    for sid, frm, to, date in [("SYS03", "FRAUDNET", "Sentinel", "2025-03-01")]:
        if W.system_name(sid, "2025-02-28") != frm or W.system_name(sid, date) != to:
            err(f"rename {sid} not resolvable as-of")
    # ------------------------------------------------------------------ legacy
    for pid, p in W.programs.items():
        if not re.fullmatch(r"CLR[A-Z]{2}\d{3}", pid):
            err(f"program id {pid} not 8-char CLR pattern")
        for t in p["reads_tables"] + p["writes_tables"]:
            if t not in W.tables:
                err(f"{pid}: unknown table {t}")
        for c in p["calls_programs"]:
            if c not in W.programs:
                err(f"{pid}: unknown called program {c}")
            if c == pid:
                err(f"{pid}: calls itself")
        for cb in p["copybooks"]:
            if cb not in W.copybooks:
                err(f"{pid}: unknown copybook {cb}")
        if p["type"] == "batch":
            if not p["jcl_job"] or p["jcl_job"] not in W.jcl_jobs:
                err(f"{pid}: batch program without valid jcl_job")
            if p["cics_transaction"]:
                err(f"{pid}: batch program with CICS transaction")
        else:
            if not p["subprogram"] and (not p["cics_transaction"] or len(p["cics_transaction"]) != 4):
                err(f"{pid}: online program needs a 4-char CICS transaction")
        if p["replaced_by"] and p["replaced_by"] not in W.services:
            err(f"{pid}: unknown replaced_by {p['replaced_by']}")
        if p["owner_team"] not in W.teams:
            err(f"{pid}: unknown owner team")
        person(p["owner_person"], f"{pid} owner")
        if p["bms_map"] and p["bms_map"] not in W.bms_maps:
            err(f"{pid}: unknown bms map")
    txns = [p["cics_transaction"] for p in W.programs.values() if p["cics_transaction"]]
    if len(txns) != len(set(txns)):
        err("duplicate CICS transactions")
    writers = sorted(p["id"] for p in W.programs.values() if "CLR.T_RESERVE" in p["writes_tables"])
    if not (6 <= len(writers) <= 9):
        err(f"reserve writers count {len(writers)} not in 6..9")
    if writers != sorted(W.reserve_writers):
        err("programs.yaml reserve_writers disagrees with program writes")
    renamed = [p for p in W.programs.values() if p.get("renamed_from")]
    if len(renamed) < 3:
        err("need a few renamed programs")
    for j in W.jcl_jobs.values():
        for st in j["steps"]:
            if st["program"] not in W.programs:
                err(f"job {j['name']}: unknown program")
            elif W.programs[st["program"]]["jcl_job"] != j["name"]:
                err(f"job {j['name']}: program {st['program']} jcl_job mismatch")
    for m in W.bms_maps.values():
        if m["program"] not in W.programs or W.programs[m["program"]]["type"] != "online":
            err(f"bms {m['map']}: program missing or not online")
    for cb in W.copybooks.values():
        if cb.get("table") and cb["table"] not in W.tables:
            err(f"copybook {cb['name']}: unknown table")
        for u in cb["used_by"]:
            if u not in W.programs:
                err(f"copybook {cb['name']}: unknown user {u}")
    for t in W.tables.values():
        n = len(t["columns"])
        if t["db"] == "DB2" and not (6 <= n <= 25):
            err(f"table {t['name']}: {n} columns (6..25)")
        cols = {c["name"] for c in t["columns"]}
        for k in t["primary_key"]:
            if k not in cols:
                err(f"table {t['name']}: pk {k} not a column")
        for fk in t.get("foreign_keys", []):
            if fk["column"] not in cols:
                err(f"table {t['name']}: fk column {fk['column']}")
            ref_t, ref_c = fk["references"].rsplit(".", 1)
            if ref_t not in W.tables or ref_c not in {c["name"] for c in W.tables[ref_t]["columns"]}:
                err(f"table {t['name']}: fk reference {fk['references']}")
        if t["db"] == "DB2":
            w = sorted(p["id"] for p in W.programs.values() if t["name"] in p["writes_tables"])
            r = sorted(p["id"] for p in W.programs.values() if t["name"] in p["reads_tables"])
            if t.get("writers") != w or t.get("readers") != r:
                err(f"table {t['name']}: writers/readers out of sync with programs")
        else:
            if t["owning_service"] not in W.services:
                err(f"pg table {t['name']}: unknown owning service")
    # ------------------------------------------------------------------ services and topics
    for s in W.services.values():
        for pg in s["postgres_tables"]:
            if pg not in W.tables:
                err(f"service {s['name']}: unknown pg table {pg}")
        for tp in s["kafka_topics"]["produces"] + s["kafka_topics"]["consumes"]:
            if tp not in W.topics:
                err(f"service {s['name']}: unknown topic {tp}")
        rp = sorted(p["id"] for p in W.programs.values() if p["replaced_by"] == s["name"])
        if rp != s["replaces_programs"]:
            err(f"service {s['name']}: replaces_programs out of sync")
        for o in s["owner_history"]:
            if o["team"] not in W.teams:
                err(f"service {s['name']}: unknown team")
            person(o["person"], f"service {s['name']} owner", o["from"])
        check_periods(f"service {s['name']}.owner_history", s["owner_history"])
    if W.service_name("reserve-engine", "2026-02-09") != "reserve-svc" or W.service_name("SVC05", "2026-02-10") != "reserve-engine":
        err("reserve-svc rename not resolvable")
    # ------------------------------------------------------------------ interfaces
    ids = sorted(W.interfaces)
    if ids != [f"CLX-IF-{i:03d}" for i in range(1, 61)]:
        err("interfaces must be CLX-IF-001..060")
    for i in W.interfaces.values():
        for k in ("source_system", "target_system"):
            if i[k] not in W.systems:
                err(f"{i['id']}: unknown {k} {i[k]}")
        for pg in i["programs"]:
            if pg not in W.programs:
                err(f"{i['id']}: unknown program {pg}")
        for sv in i["services"]:
            if sv not in W.services:
                err(f"{i['id']}: unknown service {sv}")
        for t in i["tables"]:
            if t not in W.tables:
                err(f"{i['id']}: unknown table {t}")
        person(i["owner"], f"{i['id']} owner")
        for d in i["depends_on"]:
            if d not in W.interfaces:
                err(f"{i['id']}: unknown dependency {d}")
        for t in i["consumer_teams"]:
            if t not in W.teams:
                err(f"{i['id']}: unknown consumer team {t}")
        for r in i["feeds_reports"]:
            if r not in W.reports:
                err(f"{i['id']}: unknown report {r}")
        deps = sorted(o["id"] for o in W.interfaces.values() if i["id"] in o["depends_on"])
        if deps != i.get("dependents"):
            err(f"{i['id']}: dependents out of sync")
        if i.get("schedule_history"):
            check_periods(f"{i['id']}.schedule_history", i["schedule_history"])
            if i["schedule_history"][-1]["value"] != i["schedule"]:
                err(f"{i['id']}: schedule disagrees with schedule_history")
        if i.get("kafka_topic") and i["kafka_topic"] not in W.topics:
            err(f"{i['id']}: unknown kafka topic")
    # acyclic
    state = {}

    def visit(n):
        if state.get(n) == 1:
            err(f"interface dependency cycle at {n}")
            return
        if state.get(n) == 2:
            return
        state[n] = 1
        for d in W.interfaces[n]["depends_on"]:
            if d in W.interfaces:
                visit(d)
        state[n] = 2
    for n in W.interfaces:
        visit(n)
    imp = W.impact("CLX-IF-042")
    exp = W.impact_042
    if imp["hops"].get(1) != sorted(exp["hop1"]) or imp["hops"].get(2) != sorted(exp["hop2"]) or len(imp["hops"]) != 2:
        err(f"CLX-IF-042 impact mismatch: {imp['hops']}")
    if imp["reports"] != sorted(exp["reports"]):
        err("CLX-IF-042 impact reports mismatch")
    if sorted(imp["teams"]) != sorted(exp["teams"]):
        err(f"CLX-IF-042 impact teams mismatch {imp['teams']}")
    down = [x for v in imp["hops"].values() for x in v]
    if len(down) + len(imp["reports"]) + len(imp["teams"]) < 4:
        err("CLX-IF-042 impact too small")
    # ------------------------------------------------------------------ rules
    three_plus = 0
    for r in W.rules.values():
        if not re.fullmatch(r"BR-(FNOL|TRI|ASM|RSV|FRD|STL|REC|GEN)-\d{3}", r["id"]):
            err(f"rule id {r['id']}")
        person(r["owner"], f"{r['id']} owner")
        vs = [v for v in r["versions"] if v["status"] != "draft"]
        if len(vs) >= 3:
            three_plus += 1
        nums = [v["version"] for v in r["versions"]]
        if nums != sorted(nums) or len(set(nums)) != len(nums):
            err(f"{r['id']}: version numbers")
        check_periods(f"{r['id']}.versions", [{"from": v["effective_from"], "to": v["effective_to"]} for v in vs])
        for i, v in enumerate(vs):
            for a in v["approved_by"]:
                person(a, f"{r['id']} v{v['version']} approver", v["approved_on"])
            if not v["approved_by"]:
                err(f"{r['id']} v{v['version']}: no approver")
            if v["approved_on"] and v["effective_from"] and v["approved_on"] > v["effective_from"]:
                err(f"{r['id']} v{v['version']}: approved after effective date")
            last = i == len(vs) - 1
            if not last and v["status"] not in ("superseded",):
                err(f"{r['id']} v{v['version']}: non-final version must be superseded")
            if last and v["effective_to"] is None and v["status"] != "approved":
                err(f"{r['id']} v{v['version']}: open-ended version must be approved")
            if last and v["effective_to"] is not None and v["status"] not in ("superseded", "withdrawn"):
                err(f"{r['id']} v{v['version']}: closed final version must be superseded/withdrawn")
        for v in r["versions"]:
            if v["status"] == "draft" and (v["effective_from"] or v["effective_to"]):
                err(f"{r['id']}: draft with effective dates")
        for pg in r["implemented_in"]["programs"]:
            if pg not in W.programs:
                err(f"{r['id']}: unknown program {pg}")
        for sv in r["implemented_in"]["services"]:
            if sv not in W.services:
                err(f"{r['id']}: unknown service {sv}")
        ap = r["applies_to"]
        if ap["claim_types"] != "all":
            for c in ap["claim_types"]:
                if c not in W.claim_types:
                    err(f"{r['id']}: unknown claim type {c}")
        if ap["products"] != "all":
            for c in ap["products"]:
                if c not in W.products:
                    err(f"{r['id']}: unknown product {c}")
        for st in ap["process_steps"]:
            if st not in W.steps:
                err(f"{r['id']}: unknown step {st}")
        for s in r["supersedes"]:
            if s["rule"] not in W.rules:
                err(f"{r['id']}: supersedes unknown rule")
                continue
            old = W.rules[s["rule"]]
            if old.get("superseded_by") != r["id"]:
                err(f"{r['id']}: {s['rule']}.superseded_by mismatch")
            ov = [v for v in old["versions"] if v["version"] == s["version"]]
            if not ov:
                err(f"{r['id']}: supersedes unknown version")
            elif ov[0]["effective_to"] and nextday(ov[0]["effective_to"]) != vs[0]["effective_from"]:
                err(f"{r['id']}: does not start the day after {s['rule']} v{s['version']} ends")
        if r.get("superseded_by"):
            if r["superseded_by"] not in W.rules:
                err(f"{r['id']}: unknown superseded_by")
            elif not any(x["rule"] == r["id"] for x in W.rules[r["superseded_by"]]["supersedes"]):
                err(f"{r['id']}: superseded_by not reciprocated")
            if vs[-1]["effective_to"] is None:
                err(f"{r['id']}: superseded rule still open")
    if three_plus < 10:
        err(f"only {three_plus} rules have 3+ versions")
    # fraud-referral headline facts
    if W.rule_version("BR-FRD-031", "2026-05-01")["parameters"]["threshold"] != 65 or W.rule_version("BR-FRD-031", "2026-10-01")["parameters"]["tier3_threshold"] != 60:
        err("BR-FRD-031 versions wrong")
    if W.rule_version("BR-FRD-012", "2026-03-31")["parameters"]["threshold"] != 70 or W.rule_version("BR-FRD-012", "2026-04-01") is not None:
        err("BR-FRD-012 should end 2026-03-31")
    # ------------------------------------------------------------------ products, process
    for pr in W.products.values():
        for c in pr["claim_types"]:
            if c not in W.claim_types:
                err(f"{pr['id']}: unknown claim type {c}")
        for wd in pr["wordings"]:
            if wd["file"] not in W.anchors_by_id:
                err(f"{pr['id']}: wording file {wd['file']} not an anchor")
    for s in W.stages.values():
        check_periods(f"stage {s['id']}.owner_history", s["owner_history"])
        for oh in s["owner_history"]:
            person(oh["person"], f"stage {s['id']} owner", oh["from"])
            if oh["to"] and oh["person"] in P and not W.employed(oh["person"], oh["to"]):
                err(f"stage {s['id']}: owner {oh['person']} not employed at end {oh['to']}")
        for sy in s["systems"]:
            if sy not in W.systems:
                err(f"stage {s['id']}: unknown system")
    for st in W.steps.values():
        for n in st["next"]:
            if n not in W.steps:
                err(f"step {st['id']}: unknown next {n}")
        if st["decision"]:
            for b in st["decision"]["branches"]:
                if b["next"] is not None and b["next"] not in W.steps:
                    err(f"step {st['id']}: unknown branch target {b['next']}")
                rr = b["rule"].split("@")[0]
                if rr not in W.rules:
                    err(f"step {st['id']}: unknown branch rule {b['rule']}")
            ch = st["decision"].get("condition_history")
            if ch:
                check_periods(f"step {st['id']}.condition_history", ch)
        for sy in st["systems"]:
            if sy not in W.systems:
                err(f"step {st['id']}: unknown system {sy}")
        for pg in st["programs"]:
            if pg not in W.programs:
                err(f"step {st['id']}: unknown program {pg}")
        for sv in st["services"]:
            if sv not in W.services:
                err(f"step {st['id']}: unknown service {sv}")
        for rr in st["rules"]:
            if rr not in W.rules:
                err(f"step {st['id']}: unknown rule {rr}")
        rc = st["raci"]
        person(rc["A"], f"step {st['id']} RACI A", TODAY)
        for k in ("R", "C", "I"):
            for x in rc[k]:
                if x not in W.teams and x not in P:
                    err(f"step {st['id']}: RACI {k} unknown {x}")
    if W.owner_of_process("PS-REC-02", TODAY) != "P013" or W.owner_of_process("S7", "2025-05-01") != "P014" or W.owner_of_process("RECOVERY", "2024-03-01") != "P015":
        err("subrogation owner history wrong")
    # ------------------------------------------------------------------ vendors, regulators
    for v in W.vendors.values():
        if v.get("contact"):
            person(v["contact"], f"{v['id']} contact")
    for c in W.circulars.values():
        for r in c["rules_affected"]:
            if r not in W.rules:
                err(f"{c['id']}: unknown rule {r}")
        if c.get("file") and c["file"] not in W.anchors_by_id:
            err(f"{c['id']}: unknown file")
        person(c["author"], f"{c['id']} author")
    for r in W.reports.values():
        for i in r["source_interfaces"]:
            if i not in W.interfaces:
                err(f"{r['id']}: unknown interface {i}")
        person(r["preparer"], f"{r['id']} preparer")
    for rg in W.regulators.values():
        for c in rg["contacts"]:
            person(c, f"{rg['id']} contact")
    # ------------------------------------------------------------------ incidents, adrs, tickets, timeline
    for inc in W.incidents.values():
        if inc["id"][4:8] != inc["date"][:4]:
            err(f"{inc['id']}: year does not match date")
        for s in inc["systems"]:
            if s not in W.systems:
                err(f"{inc['id']}: unknown system {s}")
        for pg in inc["programs"]:
            if pg not in W.programs:
                err(f"{inc['id']}: unknown program {pg}")
        for i in inc["interfaces"]:
            if i not in W.interfaces:
                err(f"{inc['id']}: unknown interface {i}")
        for t in inc["fix_tickets"]:
            if t not in W.tickets:
                err(f"{inc['id']}: unknown ticket {t}")
        person(inc["owner"], f"{inc['id']} owner", inc["date"])
        if inc["date"] > LAST_DOC:
            err(f"{inc['id']}: after last document date")
    for a in W.adrs.values():
        for dcd in a["deciders"]:
            person(dcd, f"{a['id']} decider", a["date"])
        for s in a["supersedes"]:
            if s not in W.adrs:
                err(f"{a['id']}: unknown superseded ADR")
            elif W.adrs[s]["status"] not in ("superseded", "deprecated"):
                err(f"{a['id']}: superseded ADR {s} status {W.adrs[s]['status']}")
    fixv = {f["name"] for f in W.raw["key_tickets"]["fix_versions"]}
    for t in W.tickets.values():
        person(t["assignee"], f"{t['id']} assignee")
        if t.get("reporter"):
            person(t["reporter"], f"{t['id']} reporter")
        if t["resolved"] and t["resolved"] < t["created"]:
            err(f"{t['id']}: resolved before created")
        if t["fix_version"] and t["fix_version"] not in fixv:
            err(f"{t['id']}: unknown fix version")
        for l in t["links"]:
            if l["target"] not in W.tickets:
                err(f"{t['id']}: link to unknown ticket {l['target']}")
        if (t["resolved"] or t["created"]) > LAST_DOC:
            err(f"{t['id']}: date after {LAST_DOC}")
    for ev in W.events.values():
        for r in ev["refs"]:
            if not W.exists(r):
                err(f"{ev['id']}: unresolved ref {r}")
    for m in W.meetings.values():
        for a in m["attendees"]:
            person(a, f"{m['id']} attendee", m["date"])
        for rec in m["records"]:
            if rec not in W.anchors_by_id:
                err(f"{m['id']}: record {rec} not an anchor")
        if m["forum"] and m["forum"] not in W.committees:
            err(f"{m['id']}: unknown forum")
    for d in W.decisions.values():
        if d["meeting"] and d["meeting"] not in W.meetings:
            err(f"{d['id']}: unknown meeting")
        if d["meeting"] and W.meetings[d["meeting"]]["date"] != d["date"]:
            err(f"{d['id']}: date differs from meeting")
        for p_ in d["decided_by"]:
            person(p_, f"{d['id']} decided_by")
        for r in d["refs"]:
            if not W.exists(r):
                err(f"{d['id']}: unresolved ref {r}")
    for e in W.episodes.values():
        if e["file"] not in W.anchors_by_id:
            err(f"{e['id']}: file {e['file']} not an anchor")
        for r in e["refs"]:
            if not W.exists(r):
                err(f"{e['id']}: unresolved ref {r}")
    for g in W.glossary.values():
        for r in g["refs"]:
            if r.endswith(".yaml"):
                continue
            if not W.exists(r):
                err(f"{g['id']}: unresolved ref {r}")
        for v in g["variants"]:
            for f in v["families"]:
                if f not in ("LD", "VS", "ST", "TX", "CODE", "GP"):
                    err(f"{g['id']}: unknown family {f}")
    req = ["Claims Assessor", "Fraud Referral", "Reserve", "Subrogation", "First Notice of Loss", "Claim Type", "Claims Handler"]
    canon = {g["canonical"] for g in W.glossary.values()}
    for rq in req:
        if rq not in canon:
            err(f"glossary missing {rq}")
    # ------------------------------------------------------------------ corpus plan and anchors
    fam_counts = {}
    for a in W.anchors():
        fam_counts.setdefault(a["family"], []).append(a)
        if a["date"] > LAST_DOC:
            err(f"anchor {a['file_id']}: date {a['date']} after {LAST_DOC}")
        if a["author"]:
            person(a["author"], f"anchor {a['file_id']} author", a["date"])
        if a["family"] != "CODE":
            if not re.fullmatch(r"(LD|VS|ST|TX|GP|RJ)\d{3}", a["file_id"]):
                err(f"anchor id {a['file_id']}")
            if not re.fullmatch(r"[a-z0-9_]{1,60}", a["slug"]):
                err(f"anchor {a['file_id']}: bad slug")
    for f in W.corpus_plan["families"]:
        fam = f["family"]
        if fam == "CODE":
            continue
        anchors = fam_counts.get(fam, [])
        lo, hi = f["id_range"].split("-")
        for a in anchors:
            if not (lo <= a["file_id"] <= hi):
                err(f"anchor {a['file_id']} outside {f['id_range']}")
        if len(anchors) > f["file_target"]:
            err(f"family {fam}: {len(anchors)} anchors > target {f['file_target']}")
        ext = {}
        for a in anchors:
            ext[a["ext"]] = ext.get(a["ext"], 0) + 1
        if fam in ("LD", "VS", "ST", "RJ"):
            if len(anchors) != f["file_target"]:
                err(f"family {fam}: expected {f['file_target']} anchors, got {len(anchors)}")
            for e, n in f["ext_min"].items():
                if ext.get(e, 0) < n:
                    err(f"family {fam}: {ext.get(e, 0)} .{e} anchors < {n}")
        if fam == "LD" and ext.get("doc") != 8:
            err("LD must have exactly 8 .doc files")
        if fam == "TX":
            layout = {"txt": list(range(1, 31)) + list(range(61, 70)), "md": list(range(31, 61)), "json": [70, 71, 72], "html": [73, 74, 75]}
            for a in anchors:
                n = int(a["file_id"][2:])
                if n not in layout[a["ext"]]:
                    err(f"TX anchor {a['file_id']} ext {a['ext']} violates id_layout")
            tot = {k: len(v) for k, v in layout.items()}
            for e, n in f["ext_min"].items():
                if tot[e] < n:
                    err(f"TX layout gives {tot[e]} .{e} < {n}")
    budget = sum(f["budget_mb"] or 0 for f in W.corpus_plan["families"] if f["family"] in ("LD", "VS", "ST", "TX", "GP"))
    if budget > 350:
        err(f"upload budget {budget} MB > 350")
    gp2 = [p for p in W.placements if p["kind"] == "injection_probe"]
    if len(gp2) != 1 or gp2[0]["target_file"] != "GP002":
        err("exactly one injection probe, in GP002")
    # ------------------------------------------------------------------ placements
    fam_pl, kind_pl = {}, {}
    seen_ids = set()
    excl_refs = {}
    for p in W.placements:
        if p["placement_id"] in seen_ids:
            err(f"duplicate placement {p['placement_id']}")
        seen_ids.add(p["placement_id"])
        if p["target_file"] not in W.anchors_by_id:
            err(f"{p['placement_id']}: target {p['target_file']} not an anchor")
        for a in p["also_in"]:
            if a not in W.anchors_by_id:
                err(f"{p['placement_id']}: also_in {a} not an anchor")
        if p["kind"] not in KINDS:
            err(f"{p['placement_id']}: unknown kind {p['kind']}")
        typ, ident, ver, field = parse_ref(p["world_ref"])
        ent = W.get(p["world_ref"])
        if ent is None:
            err(f"{p['placement_id']}: world_ref {p['world_ref']} does not resolve")
        if typ == "RULE" and ver:
            nums = [f"v{v['version']}" for v in W.rules[ident]["versions"]]
            if ver not in nums:
                err(f"{p['placement_id']}: rule version {ver} missing")
        for g in p.get("guards", []):
            if W.get(g) is None:
                err(f"{p['placement_id']}: guard {g} does not resolve")
        fam_pl[p["family"]] = fam_pl.get(p["family"], 0) + 1
        kind_pl[p["kind"]] = kind_pl.get(p["kind"], 0) + 1
        if p["exclusive"]:
            excl_refs.setdefault(p["world_ref"], []).append(p)
        if p["family"] != ("CODE" if p["target_file"].startswith("CODE:") else ("GP" if p["target_file"][:2] in ("GP", "RJ") else p["target_file"][:2])):
            err(f"{p['placement_id']}: family mismatch")
    for ref, ps in excl_refs.items():
        files = {p["target_file"] for p in ps}
        if len(files) > 1:
            allowed = set()
            for p in ps:
                allowed |= {p["target_file"], *p["also_in"]}
            if not files <= allowed or any(not ({q["target_file"] for q in ps} <= {p["target_file"], *p["also_in"]}) for p in ps):
                err(f"exclusive ref {ref} placed in several files {sorted(files)} without also_in")
    # a non-exclusive placement must not target a field another placement reserves for a different file
    for p in W.placements:
        if p["exclusive"]:
            continue
        typ, ident, ver, field = parse_ref(p["world_ref"])
        if field is None:
            continue
        allowed = W.allowed_files(p["world_ref"], None)
        if allowed and p["target_file"] not in allowed and not p["target_file"].startswith("CODE:"):
            err(f"{p['placement_id']}: states {p['world_ref']} reserved for {allowed}")
    total = len(W.placements)
    if not (230 <= total <= 320):
        err(f"placements total {total} outside 230..320")
    for h in ("Q1", "Q2", "Q3", "Q4"):
        hp = [p for p in W.placements if p.get("headline") == h]
        exts = set()
        for p in hp:
            a = W.anchors_by_id[p["target_file"]]
            exts.add("code" if a["family"] == "CODE" else a["ext"])
        if len(exts) < 3:
            err(f"headline {h}: evidence in only {sorted(exts)}")
    # ------------------------------------------------------------------ contradictions
    for c in W.contradictions.values():
        for side in ("source_a", "source_b"):
            s = c[side]
            if s["file"] not in W.anchors_by_id:
                err(f"{c['id']}: {side} file {s['file']} not an anchor")
            pl = W.placements_by_id.get(s["placement"])
            if not pl or pl["target_file"] != s["file"]:
                err(f"{c['id']}: {side} placement mismatch")
            if s["date"] != W.anchors_by_id[s["file"]]["date"]:
                err(f"{c['id']}: {side} date mismatch")
        if c["authoritative"] not in ("A", "B", "both"):
            err(f"{c['id']}: authoritative must be A, B or both")
        if not W.get(c["world_ref"]):
            err(f"{c['id']}: world_ref does not resolve")
    if not (12 <= len(W.contradictions) <= 20):
        err(f"{len(W.contradictions)} contradictions (expected ~15)")
    # ------------------------------------------------------------------ counts
    corv = sum(1 for p in P.values() if p["employer"] == "ORG-CORVANE")
    ibm = sum(1 for p in P.values() if p["employer"] == "ORG-IBM")
    ext_ = len(P) - corv - ibm
    checks = [("people", len(P), 55, 65), ("corvane people", corv, 42, 50), ("ibm people", ibm, 7, 10), ("external people", ext_, 5, 8),
              ("systems", len(W.systems), 22, 30), ("programs", len(W.programs), 110, 130), ("copybooks", len(W.copybooks), 40, 55),
              ("jcl jobs", len(W.jcl_jobs), 25, 35), ("bms maps", len(W.bms_maps), 10, 15),
              ("db2 tables", sum(1 for t in W.tables.values() if t["db"] == "DB2"), 35, 48), ("services", len(W.services), 10, 14),
              ("rules", len(W.rules), 140, 165), ("process steps", len(W.steps), 28, 36), ("incidents", len(W.incidents), 20, 30),
              ("adrs", len(W.adrs), 28, 32), ("tickets", len(W.tickets), 70, 95), ("glossary", len(W.glossary), 17, 30),
              ("vendors", len(W.vendors), 8, 20), ("denylist", len(W.denylist), 70, 140)]
    for label, n, lo, hi in checks:
        if not (lo <= n <= hi):
            err(f"count {label}={n} outside {lo}..{hi}")
    # ------------------------------------------------------------------ denylist
    deny = [(n, re.compile(r"(?<![A-Za-z0-9])" + re.escape(n.strip()) + r"(?![A-Za-z0-9])", re.IGNORECASE)) for n in W.denylist]
    for path in sorted((ROOT / "world" / "data").glob("*.yaml")):
        if path.name == "names_denylist.yaml":
            continue
        text = path.read_text(encoding="utf-8")
        for n, rx in deny:
            m = rx.search(text)
            if m:
                line = text.count("\n", 0, m.start()) + 1
                err(f"denylisted name {n!r} in {path.name}:{line}")
    # no knowledge-graph / product leak in world data
    for path in sorted((ROOT / "world" / "data").glob("*.yaml")):
        text = path.read_text(encoding="utf-8").lower()
        for bad in ("context studio", "knowledge graph", "retrieval-augmented", " rag "):
            if bad in text:
                err(f"forbidden term {bad!r} in {path.name}")
    # secret-looking strings
    secret = re.compile(r"(AKIA[0-9A-Z]{16}|-----BEGIN [A-Z ]*PRIVATE KEY-----|ghp_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9]{20,})")
    for path in sorted((ROOT / "world" / "data").glob("*.yaml")):
        if secret.search(path.read_text(encoding="utf-8")):
            err(f"secret-looking string in {path.name}")

    # ------------------------------------------------------------------ report
    print(f"placements per family: {dict(sorted(fam_pl.items()))}")
    print(f"placements per kind: {dict(sorted(kind_pl.items()))}")
    for w in WARNINGS:
        print("WARN", w)
    if ERRORS:
        for e in ERRORS:
            print("ERROR", e)
        print(f"FAIL: {len(ERRORS)} errors")
        return 1
    print(f"PASS: world model valid ({len(W.placements)} placements, {len(W.anchors())} anchors, {len(W.contradictions)} contradictions)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

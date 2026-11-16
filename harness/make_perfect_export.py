#!/usr/bin/env python
"""Build a synthetic "perfect" knowledge-graph export from the world model alone.

    .venv/bin/python -I harness/make_perfect_export.py [--out build/perfect_export.json] [--as-of 2026-11-15]

This is the consistency proof for questions/graph_expectations.yaml: the export below is what an ideal
extraction of the corpus would give, built from world/data (via world.worldlib) and never from the
expectations file. Auditing it must give 0 missing nodes, 0 missing edges, 0 unmerged aliases and
0 wrong merges:

    .venv/bin/python -I harness/graph_audit.py audit build/perfect_export.json \
        --expect questions/graph_expectations.yaml --label perfect

Modelling (names from schemas/corvane_claims.jsonld, which is read at run time and enforced):
- Node labels are the schema's class IRI local names (Person, BusinessRule, ...), relationship types
  its UPPER_SNAKE labels (REPORTS_TO, WRITES_TO_TABLE, ...). Every edge is checked against the
  relationship's domain and range (owl:unionOf included) and every node property other than `name`
  and `source_files` must be a datatype property whose domain covers the node's class.
- One node per world entity. Systems, services, people and teams are named by their canonical
  (current) name; former names and aliases go into `alias`. A renamed COBOL program id
  (FNETCAL1 -> CLRFR020) is a second Program node linked by RENAMED_TO, as the expectations require.
- Code-keyed entities are named by their code: programs, copybooks, batch jobs, screen maps, tables,
  interfaces, rules ("BR-FRD-031"), rule versions ("BR-FRD-031 v2"), process steps, reports,
  incidents, ADRs, tickets. Regulations use their reference ("NISA Circular 2026/04").
- Time-dependent links (REPORTS_TO, LEADS, HEADS_DEPARTMENT, MEMBER_OF, OWNS_PROCESS, OWNS_SERVICE,
  PART_OF_DEPARTMENT, LOCATED_IN) and jobTitle hold the value on --as-of only. People not employed on
  that date keep their node (last title) but get no current reporting line or team.
- Not modelled: Claim nodes and their edges (the 15,000 ST013 rows are generated from distributions,
  not world records) and pseudonymous internal Claims Assessor ids (ASR-*).
- `source_files` on a node lists the corpus files whose manifest facts (manifests/*.facts.yaml, the
  rejected-format manifest excluded) carry a world_ref to that entity, so per-file coverage reads as
  an ideal extraction would.

Writes build/perfect_export.json in the top-level {nodes, relationships} shape that graph_audit.py
auto-detects, and prints counts plus any world references that point at no node.
"""
from __future__ import annotations

import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import argparse
import collections
import json
import re
from typing import Any, Iterable

import yaml

from world.worldlib import load_world, parse_ref

SCHEMA_FILE = ROOT / "schemas" / "corvane_claims.jsonld"
MANIFESTS = ROOT / "manifests"
DEFAULT_OUT = ROOT / "build" / "perfect_export.json"
DEFAULT_AS_OF = "2026-11-15"

CLARA, CLAIMS_HUB, ESP = "SYS01", "SYS02", "SYS15"
COMPANY, IBM, REGULATOR = "ORG-CORVANE", "ORG-IBM", "REG-NISA"


# ---------------------------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------------------------

class Schema:
    """Class, relationship and datatype-property names (with domains/ranges) from the JSON-LD."""

    def __init__(self, path: pathlib.Path):
        doc = json.loads(path.read_text(encoding="utf-8"))
        self.classes: dict[str, str] = {}               # local name -> rdfs:label
        self.rels: dict[str, tuple[set, set]] = {}      # UPPER_SNAKE label -> (domain, range) local names
        self.props: dict[str, set] = {}                 # datatype property label -> domain local names
        for o in doc["@graph"]:
            t = o.get("@type")
            if t == "owl:Class":
                self.classes[self._local(o["@id"])] = o["rdfs:label"]
            elif t == "owl:ObjectProperty":
                self.rels[o["rdfs:label"]] = (self._classes_of(o["rdfs:domain"]), self._classes_of(o["rdfs:range"]))
            elif t == "owl:DatatypeProperty":
                self.props[o["rdfs:label"]] = self._classes_of(o["rdfs:domain"])

    @staticmethod
    def _local(iri: str) -> str:
        return re.split(r"[:/#]", iri)[-1]

    def _classes_of(self, spec: Any) -> set:
        if isinstance(spec, dict) and "owl:unionOf" in spec:
            return {self._local(x["@id"]) for x in spec["owl:unionOf"]["@list"]}
        return {self._local(spec["@id"])}


# ---------------------------------------------------------------------------------------------
# Graph builder
# ---------------------------------------------------------------------------------------------

def _clean(v: Any) -> Any:
    if isinstance(v, (list, tuple)):
        out = list(dict.fromkeys(x for x in v if x not in (None, "")))
        return out or None
    return v


class Builder:
    def __init__(self, schema: Schema, as_of: str):
        self.s, self.as_of = schema, as_of
        self.nodes: dict[str, dict] = {}
        self.rels: list[dict] = []
        self._rel_seen: set = set()
        self.dangling: collections.Counter = collections.Counter()  # world refs that point at no node

    def node(self, key: str, label: str, name: str, **props: Any) -> str:
        if label not in self.s.classes:
            raise ValueError(f"{label!r} is not a schema class")
        if key in self.nodes:
            raise ValueError(f"duplicate node key {key}")
        attrs = {"name": str(name)}
        for k, v in props.items():
            v = _clean(v)
            if v in (None, "", [], {}):
                continue
            if k not in self.s.props:
                raise ValueError(f"{label}.{k}: not a schema datatype property")
            if label not in self.s.props[k]:
                raise ValueError(f"{label}.{k}: the property's domain is {sorted(self.s.props[k])}")
            attrs[k] = v
        self.nodes[key] = {"id": key, "label": label, "properties": attrs}
        return key

    def has(self, key: str | None) -> bool:
        return bool(key) and key in self.nodes

    def rel(self, rtype: str, start: str | None, end: str | None, why: str = "", **props: Any) -> None:
        if rtype not in self.s.rels:
            raise ValueError(f"{rtype!r} is not a schema relationship")
        if not self.has(start) or not self.has(end):
            self.dangling[f"{rtype}: {start if not self.has(start) else end} ({why})"] += 1
            return
        dom, rng = self.s.rels[rtype]
        sl, tl = self.nodes[start]["label"], self.nodes[end]["label"]
        if sl not in dom or tl not in rng:
            raise ValueError(f"{rtype} {start} ({sl}) -> {end} ({tl}) violates domain {sorted(dom)} / range {sorted(rng)}")
        k = (rtype, start, end)
        if k in self._rel_seen:
            return
        self._rel_seen.add(k)
        rec = {"start": start, "end": end, "type": rtype}
        props = {a: b for a, b in props.items() if b not in (None, "")}
        if props:
            rec["properties"] = props
        self.rels.append(rec)


def _period(periods: Iterable[dict], key: str, d: str) -> Any:
    for p in periods or []:
        f, t = p.get("from"), p.get("to")
        if (not f or d >= str(f)) and (not t or d <= str(t)):
            return p.get(key)
    return None


def _last(periods: Iterable[dict], key: str) -> Any:
    ps = [p for p in periods or [] if p.get(key) is not None]
    return ps[-1][key] if ps else None


def _d(v: Any) -> str | None:
    return str(v)[:10] if v not in (None, "") else None


def build(as_of: str) -> tuple[dict, Builder]:
    W = load_world()
    B = Builder(Schema(SCHEMA_FILE), as_of)
    K = {  # world collection -> node key
        "person": lambda x: f"PERSON:{x}", "team": lambda x: f"TEAM:{x}", "dept": lambda x: f"DEPT:{x}",
        "loc": lambda x: f"LOC:{x}", "org": lambda x: f"ORG:{x}", "system": lambda x: f"SYSTEM:{x}",
        "program": lambda x: f"PROGRAM:{x}", "copybook": lambda x: f"COPYBOOK:{x}", "jcl": lambda x: f"JCL:{x}",
        "bms": lambda x: f"BMS:{x}", "table": lambda x: f"TABLE:{x}", "interface": lambda x: f"INTERFACE:{x}",
        "service": lambda x: f"SERVICE:{x}", "topic": lambda x: f"TOPIC:{x}", "rule": lambda x: f"RULE:{x}",
        "version": lambda r, v: f"RULE:{r}@v{v}", "circular": lambda x: f"CIRCULAR:{x}", "report": lambda x: f"REPORT:{x}",
        "product": lambda x: f"PRODUCT:{x}", "claimtype": lambda x: f"CLAIMTYPE:{x}", "process": lambda x: f"PROCESS:{x}",
        "incident": lambda x: f"INCIDENT:{x}", "adr": lambda x: f"ADR:{x}", "ticket": lambda x: f"TICKET:{x}",
        "wave": lambda x: f"WAVE:{x}", "assessor": lambda x: f"ASSESSOR:{x}",
    }

    def svc_key(name_or_id: str | None) -> str | None:
        if not name_or_id:
            return None
        s = W.services.get(name_or_id) or W.services_by_id.get(name_or_id)
        return K["service"](s["name"]) if s else K["service"](name_or_id)

    def org_key(oid: str | None) -> str | None:
        if not oid:
            return None
        return K["org"](oid)

    # --- organisations ------------------------------------------------------------------------
    c = W.company
    B.node(org_key(COMPANY), "Organisation", c["legal_name"], identifier=COMPANY,
           alias=[c["short_name"], *c.get("aliases", []), *(b["name"] for b in c.get("branches", []))],
           organisationType=c.get("type"), country="UK")
    B.node(org_key(IBM), "Organisation", "IBM Consulting", identifier=IBM, organisationType="consultancy")
    for rid, r in W.regulators.items():
        B.node(org_key(rid), "Organisation", r["name"], identifier=rid, alias=[r.get("short"), *r.get("aliases", [])],
               organisationType="regulator", country="UK")
    for vid, v in W.vendors.items():
        B.node(org_key(vid), "Organisation", v["name"], identifier=vid, alias=[v.get("short"), v.get("code")],
               organisationType=v.get("type"), country=v.get("country"))

    # --- locations, departments, teams --------------------------------------------------------
    for lid, l in W.locations.items():
        B.node(K["loc"](lid), "Location", l["name"], identifier=lid, alias=l.get("aliases"), country=l.get("country"),
               city=l.get("city"), locationType=l.get("type"), headcount=l.get("headcount"))
    for did, dp in W.departments.items():
        B.node(K["dept"](did), "Department", dp["name"], identifier=did, alias=dp.get("aliases"))
    for tid, t in W.teams.items():
        B.node(K["team"](tid), "Team", t["name"], identifier=tid,
               alias=[*(h["name"] for h in t.get("name_history", [])), *(t.get("aliases") or [])])

    # --- people -------------------------------------------------------------------------------
    for pid, p in W.people.items():
        name = W.name_of(pid, as_of)
        employed = W.employed(pid, as_of)
        title = W.title_of(pid, as_of) if employed else _last(p["titles"], "title")
        email = _period(p.get("email_history"), "email", as_of) or p.get("email")
        B.node(K["person"](pid), "Person", name, jobTitle=title, email=email,
               alias=[*(h["name"] for h in p.get("name_history", []) if h["name"] != name), *p.get("aliases", [])])

    # --- systems, programs and other legacy components ----------------------------------------
    for sid, s in W.systems.items():
        B.node(K["system"](sid), "System", W.system_name(sid, as_of), identifier=sid,
               alias=[*(r["from_name"] for r in s.get("renames", [])), *s.get("aliases", [])],
               status=s.get("lifecycle"), technology=s.get("tech"), goLiveDate=_d(s.get("go_live")),
               decommissionTargetDate=_d(s.get("decommission_target")))
    for pid, p in W.programs.items():
        B.node(K["program"](pid), "Program", pid, status=p.get("status"), programType=p.get("type"),
               transactionCode=p.get("cics_transaction"), linesOfCode=p.get("loc"), inServiceSince=_d(p.get("since")))
    for pid, p in W.programs.items():  # former program ids: their own node + RENAMED_TO (expectations policy)
        rf = p.get("renamed_from")
        if rf and rf.get("old_id"):
            old = K["program"](rf["old_id"])
            if not B.has(old):
                B.node(old, "Program", rf["old_id"], status="renamed", programType=p.get("type"))
            B.rel("RENAMED_TO", old, K["program"](pid), "programs.renamed_from", date=_d(rf.get("date")))
    for cb in W.copybooks:
        B.node(K["copybook"](cb), "Copybook", cb)
    for jn, j in W.jcl_jobs.items():
        B.node(K["jcl"](jn), "BatchJob", jn, status=j.get("status"), schedule=j.get("schedule"))
    for mn, m in W.bms_maps.items():
        B.node(K["bms"](mn), "ScreenMap", mn, title=m.get("title"), mapset=m.get("mapset"),
               transactionCode=m.get("transaction"))
    for tn, t in W.tables.items():
        B.node(K["table"](tn), "DatabaseTable", tn, databasePlatform=t.get("db"), schemaName=t.get("schema"),
               createdOn=_d(t.get("created")))

    # --- interfaces, services, topics ---------------------------------------------------------
    for iid, i in W.interfaces.items():
        B.node(K["interface"](iid), "Interface", iid, identifier=iid, status=i.get("status"),
               schedule=W.interface_schedule(iid, as_of), protocol=i.get("protocol"), dataFormat=i.get("format"),
               criticality=i.get("criticality"), inServiceSince=_d(i.get("since")))
    for sn, s in W.services.items():
        B.node(K["service"](sn), "Service", W.service_name(sn, as_of), identifier=s["id"],
               alias=[*(r["from_name"] for r in s.get("renames", [])), *s.get("aliases", [])],
               status=s.get("status"), goLiveDate=_d(s.get("go_live")))
    for tn, t in W.topics.items():
        B.node(K["topic"](tn), "KafkaTopic", tn, partitions=t.get("partitions"), retentionDays=t.get("retention_days"))

    # --- rules, versions, regulations, reports ------------------------------------------------
    param_map = {"threshold": "threshold", "tier3_threshold": "tier3Threshold", "amount": "amount", "currency": "currency"}
    for rid, r in W.rules.items():
        B.node(K["rule"](rid), "BusinessRule", rid, identifier=rid, title=r.get("title"), ruleArea=r.get("area"))
        for v in r["versions"]:
            params = {param_map[k]: x for k, x in (v.get("parameters") or {}).items()
                      if k in param_map and isinstance(x, (int, float, str)) and not isinstance(x, bool)}
            B.node(K["version"](rid, v["version"]), "RuleVersion", f"{rid} v{v['version']}", version=str(v["version"]),
                   status=v.get("status"), effectiveFrom=_d(v.get("effective_from")), effectiveTo=_d(v.get("effective_to")),
                   ruleText=v.get("text"), approvedOn=_d(v.get("approved_on")), **params)
    for cid, ci in W.circulars.items():
        B.node(K["circular"](cid), "Regulation", ci["ref"], identifier=cid, title=ci.get("title"),
               publishedOn=_d(ci.get("published")), effectiveFrom=_d(ci.get("effective")))
    for rid, r in W.reports.items():
        B.node(K["report"](rid), "RegulatoryReport", rid, identifier=rid, frequency=r.get("frequency"),
               dueDeadline=r.get("due"))

    # --- products, claim types, process -------------------------------------------------------
    for pid, p in W.products.items():
        B.node(K["product"](pid), "Product", p["name"], identifier=pid, alias=[p.get("code")], lineOfBusiness=p.get("line"),
               region=p.get("region"), currency=p.get("currency"), excessAmount=(p.get("excess") or {}).get("standard"))
    for cid, ct in W.claim_types.items():
        B.node(K["claimtype"](cid), "ClaimType", ct["name"], identifier=cid, claimTypeCode=ct.get("peril_code"),
               alias=[*(ct.get("aliases") or []), *(ct.get("local_names") or {}).values()])
    for sid, s in W.stages.items():
        B.node(K["process"](sid), "ProcessStage", s["name"], identifier=sid, sequenceNumber=s.get("order"))
    for sid, s in W.steps.items():
        sla = s.get("sla") or {}
        B.node(K["process"](sid), "ProcessStep", sid, identifier=sid, sequenceNumber=s.get("order"),
               serviceLevel=sla.get("text") if isinstance(sla, dict) else sla)

    # --- incidents, ADRs, tickets, migration waves ---------------------------------------------
    for iid, i in W.incidents.items():
        B.node(K["incident"](iid), "Incident", iid, identifier=iid, title=i.get("title"), severity=i.get("severity"),
               rootCause=i.get("root_cause"), occurredOn=_d(i.get("date")), status=i.get("status"))
    for aid, a in W.adrs.items():
        B.node(K["adr"](aid), "ArchitectureDecision", aid, identifier=aid, title=a.get("title"), status=a.get("status"),
               decisionDate=_d(a.get("date")))
    for tid, t in W.tickets.items():
        B.node(K["ticket"](tid), "Ticket", tid, identifier=tid, title=t.get("summary"), ticketType=t.get("type"),
               status=_period(t.get("status_history"), "status", as_of) or t.get("status"),
               createdOn=_d(t.get("created")), resolvedOn=_d(t.get("resolved")), releaseVersion=t.get("fix_version"))
    for wid, w in W.waves.items():
        B.node(K["wave"](wid), "Milestone", w["name"], identifier=wid, milestoneDate=_d(w.get("date")),
               claimsMigrated=w.get("claims_migrated"), status=w.get("status"))

    # --- Claims Assessors (panel firms and named internal assessors) ----------------------------
    aa = (W.claims_profile or {}).get("assessor_assignment") or {}
    panel = sorted({v for by in (aa.get("vendor_by_region") or {}).values() for v in by})
    panel += sorted(v for v, rec in W.vendors.items() if rec.get("type") == "loss_adjuster" and v not in panel)
    for vid in panel:
        if vid in W.vendors:
            k = B.node(K["assessor"](vid), "ClaimsAssessor", W.vendors[vid]["name"])
            B.rel("PROVIDED_BY_FIRM", k, org_key(vid), "claims_profile.assessor_assignment")
    by_user = {p.get("clara_user_id"): pid for pid, p in W.people.items() if p.get("clara_user_id")}
    for refs in (aa.get("internal_refs") or {}).values():
        for ref in refs:
            pid = by_user.get(ref)
            if pid:  # ASR-* ids are pseudonymous: no world person, not modelled
                k = B.node(K["assessor"](ref), "ClaimsAssessor", W.name_of(pid, as_of))
                B.rel("PROVIDED_BY_FIRM", k, org_key(W.people[pid]["employer"]), "internal assessor")

    # =========================================================================================
    # Relationships
    # =========================================================================================
    # people and organisation (time-dependent ones as of the audit date)
    for pid, p in W.people.items():
        pk = K["person"](pid)
        B.rel("EMPLOYED_BY", pk, org_key(p.get("employer")), "people.employer")
        if not W.employed(pid, as_of):
            continue
        mgr = W.manager_of(pid, as_of)
        if mgr:
            B.rel("REPORTS_TO", pk, K["person"](mgr), "people.reports_to", as_of=as_of)
        tm = W.team_of(pid, as_of)
        if tm:
            B.rel("MEMBER_OF", pk, K["team"](tm), "people.teams", as_of=as_of)
        B.rel("LOCATED_IN", pk, K["loc"](W.location_of(pid, as_of)), "people.location", as_of=as_of)
    for tid, t in W.teams.items():
        lead = W.team_lead(tid, as_of)
        if lead:
            B.rel("LEADS", K["person"](lead), K["team"](tid), "teams.lead_history", as_of=as_of)
        dep = W.team_department(tid, as_of)
        if dep:
            B.rel("PART_OF_DEPARTMENT", K["team"](tid), K["dept"](dep), "teams.department_history", as_of=as_of)
    for did, dp in W.departments.items():
        head = _period(dp.get("head_history"), "person", as_of)
        if head:
            B.rel("HEADS_DEPARTMENT", K["person"](head), K["dept"](did), "departments.head_history", as_of=as_of)

    # systems
    for sid, s in W.systems.items():
        owner = _period(s.get("owner_history"), "person", as_of) or s.get("owner")
        if owner:
            B.rel("OWNS_SYSTEM", K["person"](owner), K["system"](sid), "systems.owner")
        if s.get("vendor"):
            B.rel("SUPPLIED_BY", K["system"](sid), org_key(s["vendor"]), "systems.vendor")
    # company.programme.purpose: "Replace the CLARA mainframe claims platform with Claims Hub";
    # SYS23 description: "Former Nordic claims system; claims migrated into CLARA, retired 2024-05-31".
    B.rel("REPLACES_SYSTEM", K["system"](CLAIMS_HUB), K["system"](CLARA), "company.programme.purpose")
    if W.systems.get("SYS23", {}).get("retired_on"):
        B.rel("REPLACES_SYSTEM", K["system"](CLARA), K["system"]("SYS23"), "systems.SYS23.description")

    # COBOL estate
    for pid, p in W.programs.items():
        pk = K["program"](pid)
        B.rel("PART_OF_SYSTEM", pk, K["system"](CLARA), "programs")
        for t in p.get("writes_tables") or []:
            B.rel("WRITES_TO_TABLE", pk, K["table"](t), "programs.writes_tables")
        for t in p.get("reads_tables") or []:
            B.rel("READS_FROM_TABLE", pk, K["table"](t), "programs.reads_tables")
        for c2 in p.get("calls_programs") or []:
            B.rel("CALLS_PROGRAM", pk, K["program"](c2), "programs.calls_programs")
        for cb in p.get("copybooks") or []:
            B.rel("USES_COPYBOOK", pk, K["copybook"](cb), "programs.copybooks")
        if p.get("bms_map"):
            B.rel("DISPLAYS_MAP", pk, K["bms"](p["bms_map"]), "programs.bms_map")
        if p.get("replaced_by"):
            B.rel("REPLACES_PROGRAM", svc_key(p["replaced_by"]), pk, "programs.replaced_by")
    for mn, m in W.bms_maps.items():
        B.rel("PART_OF_SYSTEM", K["bms"](mn), K["system"](CLARA), "bms_maps")
        if m.get("program"):
            B.rel("DISPLAYS_MAP", K["program"](m["program"]), K["bms"](mn), "bms_maps.program")
    for jn, j in W.jcl_jobs.items():
        B.rel("PART_OF_SYSTEM", K["jcl"](jn), K["system"](CLARA), "jcl_jobs")
        for st in j.get("steps") or []:
            if st.get("program"):
                B.rel("RUNS_PROGRAM", K["jcl"](jn), K["program"](st["program"]), "jcl_jobs.steps")
    for cb in W.copybooks:
        B.rel("PART_OF_SYSTEM", K["copybook"](cb), K["system"](CLARA), "copybooks")
    for tn, t in W.tables.items():
        tk = K["table"](tn)
        if str(t.get("db", "")).upper() == "DB2":
            B.rel("PART_OF_SYSTEM", tk, K["system"](CLARA), "tables.db")
            for wr in t.get("writers") or []:
                B.rel("WRITES_TO_TABLE", K["program"](wr), tk, "tables.writers")
            for rd in t.get("readers") or []:
                B.rel("READS_FROM_TABLE", K["program"](rd), tk, "tables.readers")
        else:
            B.rel("PART_OF_SYSTEM", tk, K["system"](CLAIMS_HUB), "tables.db")
            if t.get("owning_service"):
                B.rel("OWNS_TABLE", svc_key(t["owning_service"]), tk, "tables.owning_service")

    # interfaces
    for iid, i in W.interfaces.items():
        ik = K["interface"](iid)
        B.rel("SOURCE_SYSTEM", ik, K["system"](i.get("source_system")), "interfaces.source_system")
        B.rel("TARGET_SYSTEM", ik, K["system"](i.get("target_system")), "interfaces.target_system")
        for up in i.get("depends_on") or []:
            B.rel("DEPENDS_ON_INTERFACE", ik, K["interface"](up), "interfaces.depends_on")
        for down in i.get("dependents") or []:
            B.rel("DEPENDS_ON_INTERFACE", K["interface"](down), ik, "interfaces.dependents")
        for tm in i.get("consumer_teams") or []:
            B.rel("CONSUMES_INTERFACE", K["team"](tm), ik, "interfaces.consumer_teams")
        for rp in i.get("feeds_reports") or []:
            B.rel("FEEDS_REPORT", ik, K["report"](rp), "interfaces.feeds_reports")
        if i.get("owner"):
            B.rel("OWNS_INTERFACE", K["person"](i["owner"]), ik, "interfaces.owner")
    for rid, r in W.reports.items():
        for si in r.get("source_interfaces") or []:
            B.rel("FEEDS_REPORT", K["interface"](si), K["report"](rid), "reports.source_interfaces")
        if r.get("preparer"):
            B.rel("PREPARED_BY", K["report"](rid), K["person"](r["preparer"]), "reports.preparer")

    # services and topics
    for sn, s in W.services.items():
        sk = K["service"](sn)
        B.rel("PART_OF_SYSTEM", sk, K["system"](CLAIMS_HUB), "services")
        own = W.service_owner(sn, as_of)
        if own and own.get("team"):
            B.rel("OWNS_SERVICE", K["team"](own["team"]), sk, "services.owner_history", as_of=as_of)
        for pg in s.get("replaces_programs") or []:
            B.rel("REPLACES_PROGRAM", sk, K["program"](pg), "services.replaces_programs")
        for t in (s.get("kafka_topics") or {}).get("produces") or []:
            B.rel("PUBLISHES_TOPIC", sk, K["topic"](t), "services.kafka_topics.produces")
        for t in (s.get("kafka_topics") or {}).get("consumes") or []:
            B.rel("CONSUMES_TOPIC", sk, K["topic"](t), "services.kafka_topics.consumes")
        for tb in s.get("postgres_tables") or []:
            B.rel("OWNS_TABLE", sk, K["table"](tb), "services.postgres_tables")
    for tn, t in W.topics.items():
        tk = K["topic"](tn)
        B.rel("PART_OF_SYSTEM", tk, K["system"](ESP), "kafka_topics.cluster")
        if t.get("producer"):
            B.rel("PUBLISHES_TOPIC", svc_key(t["producer"]), tk, "kafka_topics.producer")
        for cs in t.get("consumers") or []:
            B.rel("CONSUMES_TOPIC", svc_key(cs), tk, "kafka_topics.consumers")

    # rules
    for rid, r in W.rules.items():
        rk = K["rule"](rid)
        if r.get("owner"):
            B.rel("OWNS_RULE", K["person"](r["owner"]), rk, "rules.owner")
        prev = None
        for v in r["versions"]:
            vk = K["version"](rid, v["version"])
            B.rel("HAS_VERSION", rk, vk, "rules.versions")
            if prev:
                B.rel("SUPERSEDES_VERSION", vk, prev, "rules.versions (contiguous)")
            prev = vk
            for ap in v.get("approved_by") or []:
                B.rel("APPROVED_BY", vk, K["person"](ap), "rules.versions.approved_by")
        for sup in r.get("supersedes") or []:
            B.rel("SUPERSEDES", rk, K["rule"](sup["rule"] if isinstance(sup, dict) else sup), "rules.supersedes")
        impl = r.get("implemented_in") or {}
        for pg in impl.get("programs") or []:
            B.rel("IMPLEMENTS_RULE", K["program"](pg), rk, "rules.implemented_in.programs")
        for sv in impl.get("services") or []:
            B.rel("IMPLEMENTS_RULE", svc_key(sv), rk, "rules.implemented_in.services")
        ap = r.get("applies_to") or {}
        for ct in ap.get("claim_types") if isinstance(ap.get("claim_types"), list) else []:
            B.rel("APPLIES_TO_CLAIM_TYPE", rk, K["claimtype"](ct), "rules.applies_to.claim_types")
        for pr in ap.get("products") if isinstance(ap.get("products"), list) else []:
            B.rel("APPLIES_TO_PRODUCT", rk, K["product"](pr), "rules.applies_to.products")
        for st in ap.get("process_steps") if isinstance(ap.get("process_steps"), list) else []:
            B.rel("APPLIES_TO_STEP", rk, K["process"](st), "rules.applies_to.process_steps")
    for cid, ci in W.circulars.items():
        B.rel("ISSUED_BY", K["circular"](cid), org_key(REGULATOR), "circulars (NISA)")
        for rr in ci.get("rules_affected") or []:
            B.rel("GOVERNED_BY", K["rule"](rr), K["circular"](cid), "circulars.rules_affected")

    # products and process
    for pid, p in W.products.items():
        for ct in p.get("claim_types") or []:
            B.rel("COVERS_CLAIM_TYPE", K["product"](pid), K["claimtype"](ct), "products.claim_types")
    for sid, s in W.stages.items():
        owner = W.owner_of_process(sid, as_of)
        if owner:
            B.rel("OWNS_PROCESS", K["person"](owner), K["process"](sid), "stages.owner_history", as_of=as_of)
    for sid, s in W.steps.items():
        sk = K["process"](sid)
        B.rel("PART_OF_STAGE", sk, K["process"](s["stage"]), "steps.stage")
        for nx in s.get("next") or []:
            B.rel("NEXT_STEP", sk, K["process"](nx), "steps.next")
        for sy in s.get("systems") or []:
            B.rel("PERFORMED_IN_SYSTEM", sk, K["system"](sy), "steps.systems")
        raci = s.get("raci") or {}
        for tm in raci.get("R") or []:
            B.rel("RESPONSIBLE_FOR", K["team"](tm), sk, "steps.raci.R")
        if raci.get("A"):
            B.rel("ACCOUNTABLE_FOR", K["person"](raci["A"]), sk, "steps.raci.A")
        for rr in s.get("rules") or []:
            B.rel("APPLIES_TO_STEP", K["rule"](rr.split("@")[0]), sk, "steps.rules")

    # incidents, ADRs, tickets, waves
    for iid, i in W.incidents.items():
        ik = K["incident"](iid)
        for sy in i.get("systems") or []:
            B.rel("AFFECTED_SYSTEM", ik, K["system"](sy), "incidents.systems")
        for pg in i.get("programs") or []:
            B.rel("AFFECTED_PROGRAM", ik, K["program"](pg), "incidents.programs")
        for itf in i.get("interfaces") or []:
            B.rel("AFFECTED_INTERFACE", ik, K["interface"](itf), "incidents.interfaces")
        for tk in i.get("fix_tickets") or []:
            B.rel("RESOLVED_BY_TICKET", ik, K["ticket"](tk), "incidents.fix_tickets")
    for aid, a in W.adrs.items():
        for dcd in a.get("deciders") or []:
            B.rel("DECIDED_BY", K["adr"](aid), K["person"](dcd), "adrs.deciders")
        for sup in a.get("supersedes") or []:
            B.rel("SUPERSEDES_DECISION", K["adr"](aid), K["adr"](sup), "adrs.supersedes")
    for tid, t in W.tickets.items():
        if t.get("assignee"):
            B.rel("ASSIGNED_TO", K["ticket"](tid), K["person"](t["assignee"]), "tickets.assignee")
    for wid, w in W.waves.items():
        for pr in re.findall(r"PRD-[A-Z]+-[A-Z]+", str(w.get("scope") or "")):
            B.rel("MIGRATES_PRODUCT", K["wave"](wid), K["product"](pr), "migration_waves.scope")

    # --- source files from the manifests (ideal extraction: each fact's entity is a node of its file)
    files_by_key: dict[str, list] = collections.defaultdict(list)
    for f in sorted(MANIFESTS.glob("*.facts.yaml")):
        if f.name == "rejected.facts.yaml":
            continue
        for fact in yaml.safe_load(f.read_text(encoding="utf-8")) or []:
            ref, path = fact.get("world_ref"), fact.get("file")
            if not ref or not path:
                continue
            typ, ident, ver, _field = parse_ref(str(ref))
            if typ == "SERVICE":
                key = svc_key(ident)
            elif typ == "RULE" and ver:
                key = f"RULE:{ident}@{ver}"
            elif typ in ("VENDOR", "REGULATOR"):
                key = org_key(ident)
            elif typ == "ORG":
                key = org_key(COMPANY)
            else:
                key = f"{typ}:{ident}" if typ else None
            if key in B.nodes and path not in files_by_key[key]:
                files_by_key[key].append(path)
    for key, fl in files_by_key.items():
        B.nodes[key]["properties"]["source_files"] = sorted(fl)

    nodes = list(B.nodes.values())
    node_types = collections.Counter(n["label"] for n in nodes)
    edge_types = collections.Counter(r["type"] for r in B.rels)
    export = {
        "context_id": "perfect-world-export",
        "generator": "harness/make_perfect_export.py",
        "as_of": as_of,
        "node_types": dict(sorted(node_types.items())),
        "edge_types": dict(sorted(edge_types.items())),
        "node_count": len(nodes),
        "relationship_count": len(B.rels),
        "nodes": nodes,
        "relationships": B.rels,
    }
    return export, B


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--out", default=str(DEFAULT_OUT), help="output JSON (default: build/perfect_export.json)")
    ap.add_argument("--as-of", default=DEFAULT_AS_OF, help="date for time-dependent links (default: 2026-11-15)")
    args = ap.parse_args(argv)
    export, B = build(args.as_of)
    out = pathlib.Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(export, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"wrote {out.relative_to(ROOT) if out.is_relative_to(ROOT) else out}: "
          f"{export['node_count']} nodes, {export['relationship_count']} relationships (as of {args.as_of})")
    print("  nodes: " + ", ".join(f"{k} {v}" for k, v in export["node_types"].items()))
    print("  edges: " + ", ".join(f"{k} {v}" for k, v in export["edge_types"].items()))
    if B.dangling:
        print(f"  {sum(B.dangling.values())} world references point at no node (not emitted):")
        for k, v in sorted(B.dangling.items()):
            print(f"    {k}" + (f" x{v}" if v > 1 else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())

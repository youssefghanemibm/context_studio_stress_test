"""Pure data loader for the Corvane world model (reads world/data/*.yaml only; no rng).

    from world.worldlib import load_world
    W = load_world()
    W.title_of("P005", "2024-01-01")        -> 'Claims Director'
    W.is_exclusive("CLX-IF-042", "schedule") -> (True, 'VS033')

See world/WORLD.md for the full API.
"""
from __future__ import annotations

import datetime as _dt
import functools
import pathlib
import re
import unicodedata
from typing import Any, Iterable

import yaml

DATA_DIR = pathlib.Path(__file__).resolve().parent / "data"

TYPES = ["PERSON", "SYSTEM", "PROGRAM", "COPYBOOK", "JCL", "BMS", "TABLE", "INTERFACE", "SERVICE", "TOPIC", "RULE", "PRODUCT",
         "CLAIMTYPE", "PROCESS", "VENDOR", "REGULATOR", "CIRCULAR", "REPORT", "INCIDENT", "ADR", "EVENT", "MEETING", "DECISION",
         "EPISODE", "TICKET", "GLOSSARY", "CONTRA", "TEAM", "DEPT", "LOC", "COMMITTEE", "ANCHOR", "ORG", "TIMELINE", "PROFILE",
         "COMMIT", "CANARY", "WAVE", "PLACEMENT"]


def _d(x) -> str:
    if x is None:
        return None
    if isinstance(x, (_dt.date, _dt.datetime)):
        return x.isoformat()[:10]
    return str(x)[:10]


def _in(date: str, frm, to) -> bool:
    if frm and date < str(frm):
        return False
    if to and date > str(to):
        return False
    return True


def norm(s: str) -> str:
    """Case-, accent- and punctuation-insensitive key (Sørensen == Sorensen)."""
    s = s.replace("ø", "o").replace("Ø", "O").replace("æ", "ae").replace("Æ", "AE").replace("ł", "l")
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return s.strip()


def parse_ref(ref: str):
    """'RULE:BR-FRD-031@v2#parameters.threshold' -> ('RULE', 'BR-FRD-031', 'v2', 'parameters.threshold')."""
    typ = None
    rest = ref
    m = re.match(r"^([A-Z]+):(.*)$", ref)
    if m and m.group(1) in TYPES:
        typ, rest = m.group(1), m.group(2)
    field = None
    if "#" in rest:
        rest, field = rest.split("#", 1)
    version = None
    if "@" in rest:
        rest, version = rest.split("@", 1)
    return typ, rest, version, field


class World:
    def __init__(self, data_dir: pathlib.Path | str = DATA_DIR):
        self.data_dir = pathlib.Path(data_dir)
        self.raw = {}
        for p in sorted(self.data_dir.glob("*.yaml")):
            with open(p, encoding="utf-8") as fh:
                self.raw[p.stem] = yaml.safe_load(fh)
        R = self.raw
        self.org = R["org"]
        self.company = self.org["company"]
        self.locations = {x["id"]: x for x in self.org["locations"]}
        self.departments = {x["id"]: x for x in self.org["departments"]}
        self.teams = {x["id"]: x for x in self.org["teams"]}
        self.committees = {x["id"]: x for x in self.org["committees"]}
        self.people = {x["id"]: x for x in R["people"]["people"]}
        self.systems = {x["id"]: x for x in R["systems"]["systems"]}
        self.programs = {x["id"]: x for x in R["programs"]["programs"]}
        self.reserve_writers = list(R["programs"]["reserve_writers"])
        self.copybooks = {x["name"]: x for x in R["copybooks"]["copybooks"]}
        self.jcl_jobs = {x["name"]: x for x in R["jcl_jobs"]["jcl_jobs"]}
        self.bms_maps = {x["map"]: x for x in R["bms_maps"]["bms_maps"]}
        self.tables = {x["name"]: x for x in R["tables"]["tables"]}
        self.interfaces = {x["id"]: x for x in R["interfaces"]["interfaces"]}
        self.impact_042 = R["interfaces"]["impact_042"]
        self.services = {x["name"]: x for x in R["services"]["services"]}
        self.services_by_id = {x["id"]: x for x in R["services"]["services"]}
        self.topics = {x["name"]: x for x in R["services"]["kafka_topics"]}
        self.rules = {x["id"]: x for x in R["rules"]["rules"]}
        self.products = {x["id"]: x for x in R["products"]["products"]}
        self.claim_types = {x["id"]: x for x in R["claim_types"]["claim_types"]}
        self.stages = {x["id"]: x for x in R["process"]["stages"]}
        self.steps = {x["id"]: x for x in R["process"]["steps"]}
        self.vendors = {x["id"]: x for x in R["vendors"]["vendors"]}
        self.regulators = {x["id"]: x for x in R["regulators"]["regulators"]}
        self.circulars = {x["id"]: x for x in R["regulators"]["circulars"]}
        self.reports = {x["id"]: x for x in R["regulators"]["reports"]}
        self.incidents = {x["id"]: x for x in R["incidents"]["incidents"]}
        self.adrs = {x["id"]: x for x in R["adrs"]["adrs"]}
        tl = R["timeline"]
        self.timeline = tl
        self.events = {x["id"]: x for x in tl["events"]}
        self.meetings = {x["id"]: x for x in tl["meetings"]}
        self.decisions = {x["id"]: x for x in tl["decisions"]}
        self.episodes = {x["id"]: x for x in tl["episodes"]}
        self.waves = {x["id"]: x for x in tl["migration_waves"]}
        self.tickets = {x["id"]: x for x in R["key_tickets"]["tickets"]}
        self.glossary = {x["id"]: x for x in R["glossary"]["terms"]}
        self.contradictions = {x["id"]: x for x in R["contradictions"]["contradictions"]}
        self.placements = list(R["placements"]["placements"])
        self.placements_by_id = {p["placement_id"]: p for p in self.placements}
        self.headline_questions = R["placements"]["headline_questions"]
        self.corpus_plan = R["corpus_plan"]
        self.anchors_by_id = {a["file_id"]: a for a in self.corpus_plan["anchors"]}
        code_fam = [f for f in self.corpus_plan["families"] if f["family"] == "CODE"][0]
        self.commits = {c["id"]: c for c in code_fam["commits"]}
        self.canaries = {c["id"]: c for c in code_fam["canaries"]}
        self.claims_profile = R["claims_profile"]
        self.denylist = [e["name"] for e in R["names_denylist"]["entries"]]
        self._collections = {
            "PERSON": self.people, "SYSTEM": self.systems, "PROGRAM": self.programs, "COPYBOOK": self.copybooks, "JCL": self.jcl_jobs,
            "BMS": self.bms_maps, "TABLE": self.tables, "INTERFACE": self.interfaces, "SERVICE": self.services, "TOPIC": self.topics,
            "RULE": self.rules, "PRODUCT": self.products, "CLAIMTYPE": self.claim_types, "VENDOR": self.vendors,
            "REGULATOR": self.regulators, "CIRCULAR": self.circulars, "REPORT": self.reports, "INCIDENT": self.incidents, "ADR": self.adrs,
            "EVENT": self.events, "MEETING": self.meetings, "DECISION": self.decisions, "EPISODE": self.episodes, "TICKET": self.tickets,
            "GLOSSARY": self.glossary, "CONTRA": self.contradictions, "TEAM": self.teams, "DEPT": self.departments, "LOC": self.locations,
            "COMMITTEE": self.committees, "ANCHOR": self.anchors_by_id, "COMMIT": self.commits, "CANARY": self.canaries, "WAVE": self.waves,
            "PLACEMENT": self.placements_by_id,
        }
        self._name_index = None

    # ------------------------------------------------------------------ lookup
    def canonical(self, ref: str):
        """Return (TYPE, ID) for 'TYPE:ID', a plain id, a service id (SVC05) or a service name."""
        typ, ident, _, _ = parse_ref(ref)
        if typ in ("ORG", "TIMELINE", "PROFILE"):
            return typ, ident
        if typ == "PROCESS":
            return typ, ident
        if typ == "SERVICE" and ident in self.services_by_id:
            return typ, self.services_by_id[ident]["name"]
        if typ:
            return typ, ident
        if ident in self.services_by_id:
            return "SERVICE", self.services_by_id[ident]["name"]
        if ident in self.stages or ident in self.steps:
            return "PROCESS", ident
        for t, coll in self._collections.items():
            if ident in coll:
                return t, ident
        return None, ident

    def get(self, ref: str) -> Any:
        typ, ident = self.canonical(ref)
        if typ == "PROCESS":
            return self.stages.get(ident) or self.steps.get(ident)
        if typ == "ORG":
            return self.company if ident in ("company", "ORG-CORVANE") else None
        if typ == "TIMELINE":
            return self.timeline.get(ident)
        if typ == "PROFILE":
            return self.claims_profile.get(ident)
        if typ is None:
            return None
        return self._collections[typ].get(ident)

    def exists(self, ref: str) -> bool:
        return self.get(ref) is not None

    # ------------------------------------------------------------------ names
    def _build_name_index(self):
        idx = {}
        for item in self.lexicon():
            idx.setdefault(norm(item["term"]), [])
            if item["ref"] not in idx[norm(item["term"])]:
                idx[norm(item["term"])].append(item["ref"])
        self._name_index = idx

    def by_name(self, name: str) -> list[str]:
        """All entity refs whose name, alias, id or glossary variant matches (accent/case-insensitive).
        Returns a list because names can be ambiguous (two people are called Callum Fairbairn)."""
        if self._name_index is None:
            self._build_name_index()
        return list(self._name_index.get(norm(name), []))

    def resolve(self, name: str, kind: str | None = None) -> str:
        refs = self.by_name(name)
        if kind:
            refs = [r for r in refs if r.startswith(kind + ":")]
        if len(refs) != 1:
            raise KeyError(f"{name!r} resolves to {refs}")
        return refs[0]

    # ------------------------------------------------------------------ as-of helpers
    def _period_value(self, periods: Iterable[dict], key: str, date) -> Any:
        date = _d(date)
        for p in periods:
            if _in(date, p.get("from"), p.get("to")):
                return p[key]
        return None

    def employed(self, pid: str, date) -> bool:
        e = self.people[pid]["employment"]
        return _in(_d(date), e["from"], e["to"])

    def title_of(self, pid: str, date) -> str | None:
        return self._period_value(self.people[pid]["titles"], "title", date)

    def manager_of(self, pid: str, date) -> str | None:
        return self._period_value(self.people[pid]["reports_to"], "manager_id", date)

    def team_of(self, pid: str, date) -> str | None:
        return self._period_value(self.people[pid]["teams"], "team_id", date)

    def name_of(self, pid: str, date) -> str:
        p = self.people[pid]
        for h in p.get("name_history", []):
            if _in(_d(date), h.get("from"), h.get("to")):
                return h["name"]
        return p["name"]

    def location_of(self, pid: str, date) -> str:
        p = self.people[pid]
        v = self._period_value(p.get("location_history", []), "location", date)
        return v or p["location"]

    def alias_holder(self, alias: str, date) -> str | None:
        """Who is 'the CFO' (or 'the Claims Director', ...) on a date."""
        for pid, p in self.people.items():
            for ra in p.get("role_aliases", []):
                if norm(ra["alias"]) == norm(alias) and _in(_d(date), ra.get("from"), ra.get("to")):
                    return pid
        return None

    def team_lead(self, team_id: str, date) -> str | None:
        return self._period_value(self.teams[team_id]["lead_history"], "person", date)

    def team_name(self, team_id: str, date) -> str:
        t = self.teams[team_id]
        return self._period_value(t.get("name_history", []), "name", date) or t["name"]

    def team_department(self, team_id: str, date) -> str | None:
        return self._period_value(self.teams[team_id]["department_history"], "department", date)

    def owner_of_process(self, step: str, date) -> str | None:
        """Accepts a stage id (S7), stage code (RECOVERY) or step id (PS-REC-02)."""
        stage = None
        if step in self.stages:
            stage = self.stages[step]
        elif step in self.steps:
            stage = self.stages[self.steps[step]["stage"]]
        else:
            for s in self.stages.values():
                if s["code"].lower() == step.lower() or s["name"].lower() == step.lower():
                    stage = s
        if not stage:
            raise KeyError(step)
        return self._period_value(stage["owner_history"], "person", date)

    def rule_version(self, rule_id: str, date) -> dict | None:
        date = _d(date)
        for v in self.rules[rule_id]["versions"]:
            if v["status"] == "draft":
                continue
            if _in(date, v["effective_from"], v["effective_to"]):
                return v
        return None

    def rules_in_force(self, date, area: str | None = None) -> list[str]:
        return [rid for rid, r in self.rules.items() if (area is None or r["area"] == area) and self.rule_version(rid, date)]

    def system_name(self, sys_id: str, date) -> str:
        s = self.systems[sys_id]
        date = _d(date)
        name = s["name"]
        for rn in sorted(s.get("renames", []), key=lambda x: x["date"], reverse=True):
            if date < rn["date"]:
                name = rn["from_name"]
        return name

    def service_name(self, svc: str, date) -> str:
        s = self.services.get(svc) or self.services_by_id.get(svc)
        date = _d(date)
        name = s["name"]
        for rn in sorted(s.get("renames", []), key=lambda x: x["date"], reverse=True):
            if date < rn["date"]:
                name = rn["from_name"]
        return name

    def service_owner(self, svc: str, date) -> dict | None:
        s = self.services.get(svc) or self.services_by_id.get(svc)
        date = _d(date)
        for o in s["owner_history"]:
            if _in(date, o["from"], o["to"]):
                return o
        return None

    def interface_schedule(self, iid: str, date) -> str:
        i = self.interfaces[iid]
        v = self._period_value(i.get("schedule_history", []), "value", date)
        return v or i["schedule"]

    def impact(self, iid: str) -> dict:
        """Downstream interfaces by hop, plus target systems, reports and consumer teams."""
        hops, seen, frontier, n = {}, {iid}, [iid], 0
        while frontier:
            n += 1
            nxt = []
            for f in frontier:
                for d in self.interfaces[f].get("dependents", []):
                    if d not in seen:
                        seen.add(d)
                        nxt.append(d)
            if nxt:
                hops[n] = sorted(nxt)
            frontier = nxt
        down = [x for v in hops.values() for x in v]
        return {"hops": hops,
                "systems": sorted({self.interfaces[x]["target_system"] for x in down}),
                "reports": sorted({r for x in down for r in self.interfaces[x].get("feeds_reports", [])}),
                "teams": sorted({t for x in down for t in self.interfaces[x].get("consumer_teams", [])})}

    def reports_tree_ok(self, date) -> bool:
        date = _d(date)
        for pid in self.people:
            if not self.employed(pid, date):
                continue
            seen, cur = set(), pid
            while cur:
                if cur in seen:
                    return False
                seen.add(cur)
                cur = self.manager_of(cur, date)
        return True

    # ------------------------------------------------------------------ placements / exclusivity
    def _ref_matches(self, pref: str, qtype, qid, qver, qfield) -> bool:
        ptype, pid, pver, pfield = parse_ref(pref)
        ptype2, pid2 = self.canonical(pref)
        if pid2 != qid:
            return False
        if qtype and ptype2 and qtype != ptype2:
            return False
        if qver and pver and qver != pver:
            return False
        if qfield is None:
            return pfield is None
        if pfield is None:
            return True  # whole-entity exclusivity covers every field
        pbase, _, pq = pfield.partition(":")
        qbase, _, qq = qfield.partition(":")
        if not (pbase == qbase or pbase.startswith(qbase + ".") or qbase.startswith(pbase + ".")):
            return False
        if pq and qq:
            return pq == qq
        return True

    def exclusive_placements(self, entity_ref: str, field: str | None = None) -> list[dict]:
        qtype, qid = self.canonical(entity_ref)
        _, _, qver, qf = parse_ref(entity_ref)
        field = field if field is not None else qf
        out = []
        for p in self.placements:
            if not p.get("exclusive"):
                continue
            refs = [p["world_ref"]] + list(p.get("guards", []))
            if any(self._ref_matches(r, qtype, qid, qver, field) for r in refs):
                out.append(p)
        return out

    def is_exclusive(self, entity_ref: str, field: str | None = None):
        """(True, target_file_id) if stating `field` of `entity_ref` is reserved for one file
        (plus that placement's also_in files); otherwise (False, None).

        Examples: is_exclusive('CLX-IF-042', 'schedule') -> (True, 'VS033');
                  is_exclusive('JCL:CLRNRSV3', 'schedule') -> (True, 'VS033')   (guard)
        """
        ps = self.exclusive_placements(entity_ref, field)
        if not ps:
            return (False, None)
        return (True, ps[0]["target_file"])

    def allowed_files(self, entity_ref: str, field: str | None = None) -> list[str] | None:
        """Files allowed to state the field (target + also_in), or None if unrestricted."""
        ps = self.exclusive_placements(entity_ref, field)
        if not ps:
            return None
        out = []
        for p in ps:
            for f in [p["target_file"]] + p.get("also_in", []):
                if f not in out:
                    out.append(f)
        return out

    def may_state(self, file_id: str, entity_ref: str, field: str | None = None) -> bool:
        allowed = self.allowed_files(entity_ref, field)
        if allowed is None:
            return True
        if file_id in allowed:
            return True
        # code mirrors: CODE:a:<path> is mirrored in variants b and c
        if file_id.startswith("CODE:"):
            path = file_id.split(":", 2)[2]
            return any(a.startswith("CODE:a:") and a.split(":", 2)[2] == path for a in allowed)
        return False

    def placements_for(self, file_id: str, include_also: bool = False) -> list[dict]:
        out = [p for p in self.placements if p["target_file"] == file_id]
        if include_also:
            out += [p for p in self.placements if file_id in p.get("also_in", []) and p["target_file"] != file_id]
        return out

    def anchors(self, family: str | None = None) -> list[dict]:
        return [a for a in self.corpus_plan["anchors"] if family is None or a["family"] == family]

    def anchor(self, file_id: str) -> dict:
        return self.anchors_by_id[file_id]

    def contradictions_for(self, file_id: str) -> list[dict]:
        return [c for c in self.contradictions.values() if file_id in (c["source_a"]["file"], c["source_b"]["file"])]

    def family_plan(self, family: str) -> dict:
        return [f for f in self.corpus_plan["families"] if f["family"] == family][0]

    # ------------------------------------------------------------------ lexicon
    @functools.lru_cache(maxsize=1)
    def lexicon(self) -> list[dict]:
        L = []

        def add(term, ref, kind):
            if term is None or term == "":
                return
            L.append({"term": str(term), "ref": ref, "kind": kind})

        c = self.company
        for t in [c["legal_name"], c["short_name"]] + c["aliases"] + [c["programme"]["name"]] + c["programme"]["aliases"] + [c["nisa_firm_reference"]]:
            add(t, "ORG:company", "name")
        for b in c["branches"]:
            add(b["name"], "ORG:company", "branch")
        for pid, p in self.people.items():
            ref = f"PERSON:{pid}"
            add(pid, ref, "id")
            add(p["name"], ref, "name")
            for a in p["aliases"]:
                add(a, ref, "alias")
            for ra in p.get("role_aliases", []):
                add(ra["alias"], ref, "role_alias")
            for h in p.get("name_history", []):
                add(h["name"], ref, "former_name")
            add(p.get("email"), ref, "email")
            for e in p.get("email_history", []):
                add(e["email"], ref, "email")
            add(p.get("github"), ref, "github")
            for t in p["titles"]:
                add(t["title"], ref, "title")
        for coll, typ, fields in [
            (self.locations, "LOC", ["name", "city"]), (self.departments, "DEPT", ["name"]), (self.teams, "TEAM", ["name", "github_team"]),
            (self.committees, "COMMITTEE", ["name"]), (self.vendors, "VENDOR", ["name", "short", "code", "domain"]),
            (self.regulators, "REGULATOR", ["name", "short"]), (self.circulars, "CIRCULAR", ["ref", "title"]),
            (self.reports, "REPORT", ["name"]), (self.incidents, "INCIDENT", ["title"]), (self.adrs, "ADR", ["title"]),
            (self.events, "EVENT", ["summary"]), (self.meetings, "MEETING", ["title"]), (self.decisions, "DECISION", []),
            (self.episodes, "EPISODE", []), (self.tickets, "TICKET", ["summary"]), (self.products, "PRODUCT", ["name", "code"]),
            (self.claim_types, "CLAIMTYPE", ["name", "peril_code"]), (self.waves, "WAVE", ["name"]), (self.commits, "COMMIT", []),
            (self.canaries, "CANARY", []),
        ]:
            for k, v in coll.items():
                ref = f"{typ}:{k}"
                add(k, ref, "id")
                for f in fields:
                    add(v.get(f), ref, f)
                for a in v.get("aliases", []) or []:
                    add(a, ref, "alias")
                for nh in v.get("name_history", []) or []:
                    add(nh["name"], ref, "former_name")
                if typ == "CLAIMTYPE":
                    for ln in v["local_names"].values():
                        add(ln, ref, "local_name")
        for sid, s in self.systems.items():
            ref = f"SYSTEM:{sid}"
            add(sid, ref, "id")
            add(s["name"], ref, "name")
            for a in s["aliases"]:
                add(a, ref, "alias")
            for rn in s["renames"]:
                add(rn["from_name"], ref, "former_name")
            for k in ("cics_regions",):
                for reg in (s.get(k) or {}):
                    add(reg, ref, "cics_region")
            for k in ("db2_subsystem", "db2_plan", "mq_queue_manager"):
                add(s.get(k), ref, k)
        for pid, p in self.programs.items():
            ref = f"PROGRAM:{pid}"
            add(pid, ref, "id")
            add(p["description"], ref, "description")
            if p.get("renamed_from"):
                add(p["renamed_from"]["old_id"], ref, "former_id")
            add(p.get("cics_transaction"), ref, "cics_transaction")
        for n in self.copybooks:
            add(n, f"COPYBOOK:{n}", "id")
        for n, j in self.jcl_jobs.items():
            add(n, f"JCL:{n}", "id")
            for ds in j.get("datasets", []):
                add(ds["dsn"], f"JCL:{n}", "dataset")
        for n, m in self.bms_maps.items():
            add(n, f"BMS:{n}", "id")
            add(m["mapset"], f"BMS:{n}", "mapset")
        for n, t in self.tables.items():
            ref = f"TABLE:{n}"
            add(n, ref, "id")
            add(n.split(".", 1)[1], ref, "short_name")
            for col in t["columns"]:
                add(col["name"], f"{ref}#columns.{col['name']}", "column")
                add(f"{n}.{col['name']}", f"{ref}#columns.{col['name']}", "column")
            for col in t.get("retired_columns", []):
                add(col["name"], f"{ref}#retired_columns", "column")
        for iid, i in self.interfaces.items():
            ref = f"INTERFACE:{iid}"
            add(iid, ref, "id")
            add(i["name"], ref, "name")
            add(i.get("mq_queue"), ref, "mq_queue")
        for n, s in self.services.items():
            ref = f"SERVICE:{n}"
            add(n, ref, "name")
            add(s["id"], ref, "id")
            for a in s["aliases"]:
                add(a, ref, "alias")
            for rn in s["renames"]:
                add(rn["from_name"], ref, "former_name")
            add(s["k8s_namespace"], ref, "k8s_namespace")
            add(s["repo_path"], ref, "repo_path")
            add(s["terraform_module"], ref, "terraform_module")
            for api in s["apis"]:
                add(api["path"], ref, "api_path")
        for n in self.topics:
            add(n, f"TOPIC:{n}", "id")
        for rid, r in self.rules.items():
            add(rid, f"RULE:{rid}", "id")
            add(r["title"], f"RULE:{rid}", "title")
        for sid, s in self.stages.items():
            add(sid, f"PROCESS:{sid}", "id")
            add(s["name"], f"PROCESS:{sid}", "name")
            add(s["code"], f"PROCESS:{sid}", "code")
        for sid, s in self.steps.items():
            add(sid, f"PROCESS:{sid}", "id")
            add(s["name"], f"PROCESS:{sid}", "name")
        for gid, g in self.glossary.items():
            ref = f"GLOSSARY:{gid}"
            add(g["canonical"], ref, "canonical")
            add(g["schema_term"], ref, "schema_term")
            for v in g["variants"]:
                add(v["term"], ref, "variant")
        for fid, a in self.anchors_by_id.items():
            add(fid, f"ANCHOR:{fid}", "id")
            add(a["title"], f"ANCHOR:{fid}", "title")
            if a.get("doc_id"):
                add(a["doc_id"], f"ANCHOR:{fid}", "doc_id")
        return L

    def lookup_term(self, term: str) -> list[dict]:
        k = norm(term)
        return [x for x in self.lexicon() if norm(x["term"]) == k]


@functools.lru_cache(maxsize=4)
def _load(path: str) -> World:
    return World(path)


def load_world(data_dir: pathlib.Path | str = DATA_DIR) -> World:
    return _load(str(pathlib.Path(data_dir).resolve()))

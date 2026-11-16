#!/usr/bin/env python
"""Validate the hand-written Corvane schema and emit its derived files.

    python -I schemas/validate_schema.py                  # validate everything, change nothing
    python -I schemas/validate_schema.py --emit-ttl       # validate, then write corvane_claims.ttl and .rdf
    python -I schemas/validate_schema.py --emit-variants  # validate, then write terminology_variants.yaml

schemas/corvane_claims.jsonld is the only source. The Turtle and RDF/XML files are serialised from it and
terminology_variants.yaml is derived from world/data/glossary.yaml, so none of them is edited by hand.
Without an --emit flag, the derived files are checked for drift (graph isomorphism for .ttl/.rdf, byte
equality for the variants file) and README.md is checked for a table row per class, relationship and
datatype property with the schema's domain and range.

Exit code 0 when every check passes, 1 otherwise.
"""
from __future__ import annotations

import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import argparse
import collections
import re
import unicodedata

import yaml
from rdflib import BNode, Graph, Literal, Namespace, URIRef
from rdflib.collection import Collection
from rdflib.compare import isomorphic
from rdflib.namespace import OWL, RDF, RDFS, SKOS, XSD

HERE = ROOT / "schemas"
JSONLD = HERE / "corvane_claims.jsonld"
TTL = HERE / "corvane_claims.ttl"
RDFXML = HERE / "corvane_claims.rdf"
VARIANTS = HERE / "terminology_variants.yaml"
README = HERE / "README.md"
GLOSSARY = ROOT / "world" / "data" / "glossary.yaml"

CC = Namespace("https://example.org/corvane/claims#")
ONTOLOGY = URIRef("https://example.org/corvane/claims")

REQUIRED_CLASSES = [
    "Person", "Team", "Department", "Location", "Organisation", "System", "Program", "Copybook", "BatchJob",
    "ScreenMap", "DatabaseTable", "Interface", "Service", "KafkaTopic", "BusinessRule", "RuleVersion", "Regulation",
    "RegulatoryReport", "Product", "ClaimType", "ProcessStage", "ProcessStep", "ClaimsAssessor", "Incident",
    "ArchitectureDecision", "Ticket", "Milestone", "Claim",
]
REQUIRED_RELATIONS = [
    "REPORTS_TO", "MEMBER_OF", "LEADS", "LOCATED_IN", "OWNS_SYSTEM", "OWNS_PROCESS", "OWNS_INTERFACE",
    "WRITES_TO_TABLE", "READS_FROM_TABLE", "CALLS_PROGRAM", "USES_COPYBOOK", "RUNS_PROGRAM", "DISPLAYS_MAP",
    "PART_OF_SYSTEM", "SOURCE_SYSTEM", "TARGET_SYSTEM", "DEPENDS_ON_INTERFACE", "FEEDS_REPORT", "REPLACES_PROGRAM",
    "REPLACES_SYSTEM", "RENAMED_TO", "PUBLISHES_TOPIC", "CONSUMES_TOPIC", "IMPLEMENTS_RULE", "HAS_VERSION",
    "SUPERSEDES", "GOVERNED_BY", "APPLIES_TO_CLAIM_TYPE", "APPLIES_TO_STEP", "COVERS_CLAIM_TYPE", "NEXT_STEP",
    "PART_OF_STAGE", "PERFORMED_IN_SYSTEM", "RESPONSIBLE_FOR", "AFFECTED_SYSTEM", "AFFECTED_PROGRAM",
    "RESOLVED_BY_TICKET", "DECIDED_BY", "SUPERSEDES_DECISION", "ASSIGNED_TO", "EMPLOYED_BY", "APPOINTED_ASSESSOR",
]
# Generic relation names that carry no meaning of their own (graph_audit's list plus common offenders).
GENERIC_RELATIONS = {
    "BELONGS_TO", "RELATES_TO", "RELATED_TO", "IS_RELATED_TO", "HAS_MANY", "HAS", "HAS_A", "HAS_PART", "DEPENDS_ON",
    "ASSOCIATED_WITH", "IS_A", "PART_OF", "LINKED_TO", "CONNECTED_TO", "CONTAINS", "USES", "INCLUDES",
    "REFERENCES", "MENTIONS", "INVOLVES",
}
XSD_RANGES = {XSD.string, XSD.date, XSD.dateTime, XSD.decimal, XSD.integer, XSD.boolean}

# Glossary term -> schema element it lands on (curated; the rest of terminology_variants.yaml is derived).
# kind: class | datatype_property | object_property | instance (a world entity of the given class) | concept
SCHEMA_TARGETS = {
    "G-001": [{"kind": "class", "iri": "cc:ClaimsAssessor"}],
    "G-002": [{"kind": "datatype_property", "iri": "cc:fraudReferral"}],
    "G-003": [{"kind": "datatype_property", "iri": "cc:reserveAmount"},
              {"kind": "instance", "class": "cc:DatabaseTable", "world_ref": "CLR.T_RESERVE"},
              {"kind": "instance", "class": "cc:DatabaseTable", "world_ref": "reserve.reserve"}],
    "G-004": [{"kind": "instance", "class": "cc:ProcessStage", "world_ref": "S7"},
              {"kind": "datatype_property", "iri": "cc:subrogationFlag"}],
    "G-005": [{"kind": "instance", "class": "cc:ProcessStage", "world_ref": "S1"},
              {"kind": "datatype_property", "iri": "cc:notificationDate"}],
    "G-006": [{"kind": "class", "iri": "cc:ClaimType"}],
    "G-007": [{"kind": "concept", "note": "role, not modelled as a class; handlers are Person nodes with a jobTitle"}],
    "G-008": [{"kind": "datatype_property", "iri": "cc:tier"}, {"kind": "datatype_property", "iri": "cc:tier3Threshold"},
              {"kind": "instance", "class": "cc:BusinessRule", "world_ref": "BR-TRI-003"}],
    "G-009": [{"kind": "datatype_property", "iri": "cc:fraudScore"}],
    "G-010": [{"kind": "datatype_property", "iri": "cc:excessAmount"}],
    "G-011": [{"kind": "concept", "note": "not modelled"}],
    "G-012": [{"kind": "instance", "class": "cc:Team", "world_ref": "T11"}],
    "G-013": [{"kind": "instance", "class": "cc:DatabaseTable", "world_ref": "CLR.T_RESERVE_MOVEMENT"},
              {"kind": "instance", "class": "cc:DatabaseTable", "world_ref": "reserve.reserve_movement"}],
    "G-014": [{"kind": "datatype_property", "iri": "cc:incurredAmount"}],
    "G-015": [{"kind": "datatype_property", "iri": "cc:threshold", "note": "parameter of BR-RSV-011 v2"},
              {"kind": "instance", "class": "cc:BusinessRule", "world_ref": "BR-RSV-011"}],
    "G-016": [{"kind": "instance", "class": "cc:RegulatoryReport", "world_ref": "NISA-TP2"}],
    "G-017": [{"kind": "instance", "class": "cc:Interface", "world_ref": "CLX-IF-055"}],
    "G-018": [{"kind": "instance", "class": "cc:ProcessStage", "world_ref": "S6"}],
    "G-019": [{"kind": "instance", "class": "cc:System", "world_ref": "SYS02"}],
    "G-020": [{"kind": "instance", "class": "cc:System", "world_ref": "SYS01"}],
    "G-021": [{"kind": "instance", "class": "cc:BusinessRule", "world_ref": "BR-FRD-032"},
              {"kind": "instance", "class": "cc:DatabaseTable", "world_ref": "CLR.T_FRAUD_NOTIFICATION"}],
    "G-022": [{"kind": "instance", "class": "cc:Organisation", "world_ref": "VEN-09"}],
    "G-023": [{"kind": "object_property", "iri": "cc:ownsProcess", "note": "owner of process stage S7"},
              {"kind": "instance", "class": "cc:Person", "world_ref": "P013"}],
}

ARROW = "→"


# ---------------------------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------------------------

def local(u) -> str:
    return re.split(r"[#/]", str(u))[-1]


def snake_upper(s: str) -> str:
    t = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s)
    t = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", t)
    return re.sub(r"[^A-Za-z0-9]+", "_", t).strip("_").upper()


def canon(s: str) -> str:
    return re.sub(r"[^0-9a-z]", "", str(s).casefold())


def fold(s: str) -> str:
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(c for c in s if not unicodedata.combining(c))
    return s.translate(str.maketrans({"ø": "o", "Ø": "O", "æ": "ae", "Æ": "AE", "–": "-", "—": "-"})).casefold()


def camel_words(s: str) -> str:
    return re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", s)


class Report:
    def __init__(self) -> None:
        self.failures = 0

    def check(self, name: str, problems: list[str], ok_note: str = "") -> None:
        if problems:
            self.failures += 1
            print(f"FAIL  {name} ({len(problems)})")
            for p in problems[:40]:
                print(f"        - {p}")
            if len(problems) > 40:
                print(f"        ... {len(problems) - 40} more")
        else:
            print(f"PASS  {name}" + (f": {ok_note}" if ok_note else ""))


def load_glossary() -> list[dict]:
    return yaml.safe_load(GLOSSARY.read_text(encoding="utf-8"))["terms"]


# ---------------------------------------------------------------------------------------------
# schema model
# ---------------------------------------------------------------------------------------------

class Schema:
    def __init__(self, g: Graph) -> None:
        self.g = g
        self.classes = sorted(s for s in g.subjects(RDF.type, OWL.Class) if isinstance(s, URIRef))
        self.objprops = sorted(s for s in g.subjects(RDF.type, OWL.ObjectProperty) if isinstance(s, URIRef))
        self.dtprops = sorted(s for s in g.subjects(RDF.type, OWL.DatatypeProperty) if isinstance(s, URIRef))
        self.class_set = set(self.classes)

    def label(self, s) -> str | None:
        ls = list(self.g.objects(s, RDFS.label))
        return str(ls[0]) if len(ls) == 1 else None

    def members(self, node) -> list | None:
        """A declared class -> [it]; an owl:unionOf blank node -> its member list; else None."""
        if isinstance(node, URIRef):
            return [node]
        if isinstance(node, BNode):
            lists = list(self.g.objects(node, OWL.unionOf))
            if len(lists) == 1:
                return list(Collection(self.g, lists[0]))
        return None

    def side(self, s, pred) -> list:
        objs = list(self.g.objects(s, pred))
        return (self.members(objs[0]) or []) if len(objs) == 1 else []

    def class_label(self, c) -> str:
        return self.label(c) or local(c)

    def side_labels(self, s, pred) -> set[str]:
        return {self.class_label(c) for c in self.side(s, pred)}


def parse_jsonld(path: pathlib.Path) -> Graph:
    g = Graph()
    g.parse(path, format="json-ld")
    return g


def stable_copy(g: Graph) -> Graph:
    """Copy of g with deterministic blank-node labels and insertion order, so serialisations are byte-stable.

    Each blank node (an owl:unionOf class or one of its list cells) is named after the path that reaches it,
    e.g. partOfSystem_domain_unionOf_rest."""
    names: dict = {}

    def visit(node, name: str) -> None:
        if node in names:
            return
        names[node] = BNode(name)
        for p, o in sorted(g.predicate_objects(node), key=lambda po: (str(po[0]), str(po[1]))):
            if isinstance(o, BNode):
                visit(o, f"{name}_{local(p)}")

    for s, p, o in sorted(g, key=lambda t: (str(t[0]), str(t[1]), str(t[2]))):
        if isinstance(s, URIRef) and isinstance(o, BNode):
            visit(o, f"{local(s)}_{local(p)}")
    for i, b in enumerate(sorted({n for t in g for n in t if isinstance(n, BNode) and n not in names}, key=str)):
        visit(b, f"b{i}")
    out = Graph()
    triples = [tuple(names.get(n, n) for n in t) for t in g]
    for t in sorted(triples, key=lambda t: (str(t[0]), str(t[1]), str(t[2]))):
        out.add(t)
    for p, ns in (("cc", CC), ("owl", OWL), ("rdf", RDF), ("rdfs", RDFS), ("skos", SKOS), ("xsd", XSD)):
        out.bind(p, ns, override=True, replace=True)
    return out


# ---------------------------------------------------------------------------------------------
# checks
# ---------------------------------------------------------------------------------------------

def check_schema(sc: Schema, glossary: list[dict], R: Report) -> None:
    g = sc.g
    onts = list(g.subjects(RDF.type, OWL.Ontology))
    R.check("one owl:Ontology header with label and comment",
            [] if onts == [ONTOLOGY] and (ONTOLOGY, RDFS.label, None) in g and (ONTOLOGY, RDFS.comment, None) in g
            else [f"ontology nodes: {onts}"])

    terms = sc.classes + sc.objprops + sc.dtprops
    probs = []
    for s in {s for s in g.subjects() if isinstance(s, URIRef) and str(s).startswith(str(CC))}:
        kinds = [k for k in (OWL.Class, OWL.ObjectProperty, OWL.DatatypeProperty) if (s, RDF.type, k) in g]
        if len(kinds) != 1:
            probs.append(f"{local(s)} declared as {[local(k) for k in kinds]}")
    for o in {o for o in g.objects() if isinstance(o, URIRef) and str(o).startswith(str(CC))}:
        if o not in terms:
            probs.append(f"cc:{local(o)} is referenced but never declared")
    for s in g.subjects():
        if isinstance(s, URIRef) and s != ONTOLOGY and not str(s).startswith(str(CC)):
            probs.append(f"term outside the cc: namespace: {s}")
    R.check("every term is declared once, in the cc: namespace, with no dangling references", probs,
            f"{len(sc.classes)} classes, {len(sc.objprops)} object properties, {len(sc.dtprops)} datatype properties")

    probs = []
    for s in terms:
        for pred, nm in ((RDFS.label, "rdfs:label"), (RDFS.comment, "rdfs:comment")):
            vals = list(g.objects(s, pred))
            if len(vals) != 1 or not isinstance(vals[0], Literal) or not str(vals[0]).strip():
                probs.append(f"{local(s)}: needs exactly one non-empty {nm} (has {len(vals)})")
            elif vals[0].language or vals[0].datatype:
                probs.append(f"{local(s)}: {nm} should be a plain string")
    R.check("every class and property has one rdfs:label and one rdfs:comment", probs)

    probs = []
    for c in sc.classes:
        lab = sc.label(c) or ""
        if canon(lab) != canon(local(c)):
            probs.append(f"class {local(c)}: label '{lab}' does not match its IRI")
    for p in sc.objprops:
        lab = sc.label(p) or ""
        if not re.fullmatch(r"[A-Z][A-Z0-9]*(_[A-Z0-9]+)*", lab):
            probs.append(f"relation {local(p)}: label '{lab}' is not UPPER_SNAKE")
        if snake_upper(local(p)) != lab:
            probs.append(f"relation {local(p)}: label '{lab}' != UPPER_SNAKE of IRI ({snake_upper(local(p))})")
        if not re.fullmatch(r"[a-z][A-Za-z0-9]*", local(p)):
            probs.append(f"relation IRI {local(p)} is not camelCase")
    for p in sc.dtprops:
        if sc.label(p) != local(p) or not re.fullmatch(r"[a-z][A-Za-z0-9]*", local(p)):
            probs.append(f"datatype property {local(p)}: label must equal its camelCase IRI local name")
    labels = [canon(sc.label(t) or "") for t in terms]
    dups = sorted({l for l in labels if labels.count(l) > 1})
    probs += [f"duplicate label (case/punctuation-insensitive): {d}" for d in dups]
    R.check("labels follow the naming rules and are unique", probs,
            "class label ~ IRI, relation label = UPPER_SNAKE(IRI), datatype label = IRI")

    probs = []
    for p in sc.objprops:
        for pred, nm in ((RDFS.domain, "domain"), (RDFS.range, "range")):
            objs = list(g.objects(p, pred))
            if len(objs) != 1:
                probs.append(f"{sc.label(p)}: needs exactly one rdfs:{nm} (has {len(objs)})")
                continue
            mem = sc.members(objs[0])
            if not mem:
                probs.append(f"{sc.label(p)}: rdfs:{nm} is neither a class IRI nor an owl:unionOf")
            elif isinstance(objs[0], BNode) and len(mem) < 2:
                probs.append(f"{sc.label(p)}: owl:unionOf {nm} needs 2+ members")
            else:
                probs += [f"{sc.label(p)}: {nm} {local(m)} is not a declared class" for m in mem if m not in sc.class_set]
    unions = sorted(sc.label(p) for p in sc.objprops
                    if any(isinstance(o, BNode) for pred in (RDFS.domain, RDFS.range) for o in g.objects(p, pred)))
    R.check("every object property has one domain and one range, each a declared class (or a union of them)", probs,
            f"{len(sc.objprops) - len(unions)} single-class; owl:unionOf in {len(unions)}: {', '.join(unions)}")

    probs = []
    for p in sc.dtprops:
        doms = list(g.objects(p, RDFS.domain))
        mem = sc.members(doms[0]) if len(doms) == 1 else None
        if not mem:
            probs.append(f"{local(p)}: needs one rdfs:domain (a class or an owl:unionOf)")
        else:
            probs += [f"{local(p)}: domain {local(m)} is not a declared class" for m in mem if m not in sc.class_set]
        rngs = list(g.objects(p, RDFS.range))
        if len(rngs) != 1 or rngs[0] not in XSD_RANGES:
            probs.append(f"{local(p)}: range must be one of {sorted(local(x) for x in XSD_RANGES)}")
    R.check("every datatype property has a declared domain and an xsd range", probs)

    probs = []
    class_snakes = sorted({snake_upper(local(c)) for c in sc.classes}, key=len, reverse=True)
    for p in sc.objprops:
        lab = sc.label(p) or ""
        core = lab
        for a in class_snakes:
            if lab.startswith(a + "_"):
                rest = lab[len(a) + 1:]
                for b in class_snakes:
                    if rest.endswith("_" + b) and len(rest) > len(b) + 1:
                        core = rest[: -(len(b) + 1)]
                        break
                break
        if lab in GENERIC_RELATIONS or core in GENERIC_RELATIONS:
            probs.append(f"generic relation name: {lab}")
    R.check("no generic relation names", probs, f"checked against {len(GENERIC_RELATIONS)} generic names")

    have_c = {local(c) for c in sc.classes}
    have_r = {sc.label(p) for p in sc.objprops}
    probs = [f"missing class {c}" for c in REQUIRED_CLASSES if c not in have_c]
    probs += [f"missing relation {r}" for r in REQUIRED_RELATIONS if r not in have_r]
    R.check("all required classes and relations are present", probs,
            f"{len(REQUIRED_CLASSES)} classes, {len(REQUIRED_RELATIONS)} relations "
            f"(+{len(have_r) - len(set(REQUIRED_RELATIONS) & have_r)} extra relations)")

    check_terminology(sc, glossary, R)
    check_graph_audit(sc, R)


def check_terminology(sc: Schema, glossary: list[dict], R: Report) -> None:
    """The schema must use canonical terms only: no glossary variant in any label, altLabel or comment."""
    g = sc.g
    canonicals = sorted({fold(t[k]) for t in glossary for k in ("canonical", "schema_term") if t.get(k)}, key=len, reverse=True)
    variants = []
    for t in glossary:
        for v in t.get("variants") or []:
            term = v["term"] if isinstance(v, dict) else v
            if fold(term) not in canonicals:
                variants.append((fold(term), term, t["canonical"]))

    def spans(text: str, needle: str) -> list[tuple[int, int]]:
        pat = r"(?<![0-9a-z])" + re.escape(needle) + r"(?![0-9a-z])"
        return [(m.start(), m.end()) for m in re.finditer(pat, text)]

    probs = []
    texts: list[tuple[str, str, bool]] = []   # (where, text, whole_label_only)
    for s in sc.classes + sc.objprops + sc.dtprops + [ONTOLOGY]:
        nm = local(s)
        for lab in g.objects(s, RDFS.label):
            if s in sc.objprops:
                texts.append((f"{nm} label", str(lab), True))
            elif s in sc.dtprops:
                texts.append((f"{nm} label", camel_words(str(lab)), False))
            else:
                texts.append((f"{nm} label", str(lab), False))
        for alt in g.objects(s, SKOS.altLabel):
            texts.append((f"{nm} altLabel", str(alt), False))
        for com in g.objects(s, RDFS.comment):
            texts.append((f"{nm} comment", str(com), False))
    for where, raw, whole_only in texts:
        text = fold(raw)
        for fv, term, can in variants:
            if whole_only:
                if canon(text) == canon(fv):
                    probs.append(f"{where} equals the variant '{term}' of '{can}'")
                continue
            covered = [sp for c in canonicals for sp in spans(text, c)]
            for a, b in spans(text, fv):
                if not any(ca <= a and b <= cb for ca, cb in covered):
                    probs.append(f"{where} uses the variant '{term}' of '{can}': \"{raw[:90]}\"")
    for t in glossary:
        if t["schema_term"] in ("Claims Assessor", "Claim Type"):
            want = t["schema_term"]
            if want not in {sc.label(c) for c in sc.classes}:
                probs.append(f"no class labelled with the canonical term '{want}'")
    R.check("canonical terms only (no glossary variant in labels, altLabels or comments)", probs,
            f"{len(variants)} variants from {len(glossary)} glossary terms")


def check_graph_audit(sc: Schema, R: Report) -> None:
    """harness/graph_audit.py reads class names from the JSON-LD; make sure it sees exactly our classes."""
    try:
        from harness import graph_audit as ga
    except Exception as e:  # pragma: no cover - the harness is optional for this check
        R.check("graph_audit reads the schema classes", [f"cannot import harness.graph_audit: {e}"])
        return
    seen = set(ga._schema_classes(JSONLD))
    want = {local(c) for c in sc.classes}
    probs = [f"graph_audit misses class {c}" for c in sorted(want - seen)]
    probs += [f"graph_audit sees a non-class {c}" for c in sorted(seen - want)]
    for p in sc.objprops:
        if ga.canon_rel(sc.label(p)) != ga.canon_rel(local(p)):
            probs.append(f"{sc.label(p)} and its IRI {local(p)} normalise differently in graph_audit")
    R.check("graph_audit reads exactly the schema classes; relation label == IRI after its normalisation", probs,
            f"{len(seen)} classes")


# ---------------------------------------------------------------------------------------------
# derived files
# ---------------------------------------------------------------------------------------------

TTL_HEADER = ("# GENERATED from corvane_claims.jsonld by `python -I schemas/validate_schema.py --emit-ttl`.\n"
              "# Do not edit by hand; edit the JSON-LD and re-run.\n")
RDF_HEADER = ("<!-- GENERATED from corvane_claims.jsonld by schemas/validate_schema.py (emit-ttl option). "
              "Do not edit by hand; edit the JSON-LD and re-run. -->\n")  # no double hyphen: XML forbids it in comments


XML_PREFIXES = (("owl", OWL), ("rdf", RDF), ("rdfs", RDFS), ("skos", SKOS))


def to_rdfxml(g: Graph) -> str:
    """Deterministic RDF/XML (typed node elements, nested single-use blank nodes, rdf:parseType="Collection").

    rdflib's pretty-xml writer orders subjects by hash seed and can drop blank nodes it fails to nest, so this
    small writer is used instead; check_derived_rdf re-parses the result and proves it isomorphic to the JSON-LD."""
    def qname(u) -> str:
        for p, ns in XML_PREFIXES:
            if str(u).startswith(str(ns)) and re.fullmatch(r"[A-Za-z_][\w.-]*", str(u)[len(str(ns)):]):
                return f"{p}:{str(u)[len(str(ns)):]}"
        raise ValueError(f"no XML prefix for predicate/type {u}")

    def esc(s: str, attr: bool = False) -> str:
        s = str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        return s.replace('"', "&quot;") if attr else s

    inbound = collections.Counter(o for o in g.objects() if isinstance(o, BNode))
    key = lambda po: (str(po[0]), str(po[1]))

    def list_items(node) -> list | None:
        items, seen = [], set()
        while node != RDF.nil:
            if not isinstance(node, BNode) or node in seen or inbound[node] != 1:
                return None
            pos = sorted(g.predicate_objects(node), key=key)
            if [p for p, _ in pos] != sorted([RDF.first, RDF.rest], key=str):
                return None
            first, rest = g.value(node, RDF.first), g.value(node, RDF.rest)
            if not isinstance(first, URIRef):
                return None
            seen.add(node)
            items.append(first)
            node = rest
        return items

    out: list[str] = []
    done: set = set()

    def node_elem(s, ind: str, nested: bool) -> None:
        done.add(s)
        types = sorted((o for o in g.objects(s, RDF.type) if isinstance(o, URIRef)), key=str)
        tag = qname(types[0]) if types else "rdf:Description"
        attr = f' rdf:about="{esc(s, True)}"' if isinstance(s, URIRef) else ("" if nested else f' rdf:nodeID="{s}"')
        out.append(f"{ind}<{tag}{attr}>")
        for p, o in sorted(g.predicate_objects(s), key=key):
            if p == RDF.type and types and o == types[0]:
                continue
            pq = qname(p)
            if isinstance(o, URIRef):
                out.append(f'{ind}  <{pq} rdf:resource="{esc(o, True)}"/>')
            elif isinstance(o, BNode):
                items = list_items(o)
                if items is not None:
                    out.append(f'{ind}  <{pq} rdf:parseType="Collection">')
                    out.extend(f'{ind}    <rdf:Description rdf:about="{esc(i, True)}"/>' for i in items)
                    out.append(f"{ind}  </{pq}>")
                    n = o
                    while n != RDF.nil:
                        done.add(n)
                        n = g.value(n, RDF.rest)
                elif inbound[o] == 1 and o not in done:
                    out.append(f"{ind}  <{pq}>")
                    node_elem(o, ind + "    ", True)
                    out.append(f"{ind}  </{pq}>")
                else:
                    out.append(f'{ind}  <{pq} rdf:nodeID="{o}"/>')
            else:
                a = (f' xml:lang="{o.language}"' if o.language else "") + \
                    (f' rdf:datatype="{esc(o.datatype, True)}"' if o.datatype else "")
                out.append(f"{ind}  <{pq}{a}>{esc(o)}</{pq}>")
        out.append(f"{ind}</{tag}>")

    out.append('<?xml version="1.0" encoding="utf-8"?>')
    out.append(RDF_HEADER.rstrip("\n"))
    out.append("<rdf:RDF")
    out.extend(f'  xmlns:{p}="{ns}"' for p, ns in XML_PREFIXES)
    out.append(">")
    order = {OWL.Ontology: 0, OWL.Class: 1, OWL.ObjectProperty: 2, OWL.DatatypeProperty: 3}
    uris = sorted({s for s in g.subjects() if isinstance(s, URIRef)},
                  key=lambda s: (min((order.get(t, 9) for t in g.objects(s, RDF.type)), default=9), str(s)))
    for s in uris:
        node_elem(s, "  ", False)
    for b in sorted({s for s in g.subjects() if isinstance(s, BNode)}, key=str):
        if b not in done:
            node_elem(b, "  ", False)
    out.append("</rdf:RDF>")
    return "\n".join(out) + "\n"


def emit_ttl(g: Graph) -> None:
    bg = stable_copy(g)
    TTL.write_text(TTL_HEADER + bg.serialize(format="turtle"), encoding="utf-8")
    RDFXML.write_text(to_rdfxml(bg), encoding="utf-8")
    print(f"wrote {TTL.relative_to(ROOT)} and {RDFXML.relative_to(ROOT)}")


def check_derived_rdf(g: Graph, R: Report) -> None:
    probs = []
    for path, fmt in ((TTL, "turtle"), (RDFXML, "xml")):
        if not path.exists():
            probs.append(f"{path.name} is missing (run --emit-ttl)")
            continue
        other = Graph()
        try:
            other.parse(path, format=fmt)
        except Exception as e:
            probs.append(f"{path.name} does not parse: {e}")
            continue
        if not isomorphic(g, other):
            probs.append(f"{path.name} has drifted from the JSON-LD (run --emit-ttl)")
    R.check("corvane_claims.ttl and corvane_claims.rdf are isomorphic to the JSON-LD", probs)


def variants_doc(glossary: list[dict], sc: Schema) -> str:
    terms = []
    for t in glossary:
        entry = {"canonical": t["canonical"], "glossary_id": t["id"]}
        if t.get("schema_term") and t["schema_term"] != t["canonical"]:
            entry["schema_term"] = t["schema_term"]
        entry["schema_targets"] = SCHEMA_TARGETS.get(t["id"], [{"kind": "concept", "note": "not mapped"}])
        entry["definition"] = t.get("definition", "")
        entry["variants"] = [{"term": v["term"], "families": list(v.get("families") or []),
                              **({"note": v["note"]} if v.get("note") else {})}
                             for v in t.get("variants") or []]
        entry["refs"] = list(t.get("refs") or [])
        terms.append(entry)
    index: dict[str, list[str]] = {}
    for t in glossary:
        for v in t.get("variants") or []:
            key = v["term"].casefold()
            if t["canonical"] not in index.setdefault(key, []):
                index[key].append(t["canonical"])
    head = ("# GENERATED from world/data/glossary.yaml by `python -I schemas/validate_schema.py --emit-variants`.\n"
            "# Do not edit by hand. Canonical schema term -> the variants documents use instead.\n"
            "# Read by the scorer and the graph audit. NOT imported into the product: the schema itself\n"
            "# (corvane_claims.jsonld) carries canonical terms only, so the test can measure how extraction\n"
            "# copes with the mismatch. schema_targets says where each canonical term lands in the schema:\n"
            "# a class, a property, or a world entity (instance) of a class.\n")
    doc = {"version": 1, "source": "world/data/glossary.yaml", "schema": "schemas/corvane_claims.jsonld",
           "terms": terms, "variant_index": dict(sorted(index.items()))}
    return head + yaml.safe_dump(doc, sort_keys=False, allow_unicode=True, width=110)


def check_variant_targets(sc: Schema, R: Report) -> None:
    known = {f"cc:{local(t)}" for t in sc.classes + sc.objprops + sc.dtprops}
    probs = []
    for gid, targets in SCHEMA_TARGETS.items():
        for tg in targets:
            for k in ("iri", "class"):
                if k in tg and tg[k] not in known:
                    probs.append(f"{gid}: {tg[k]} is not in the schema")
    R.check("terminology schema_targets point at schema terms", probs)


def check_variants_file(text: str, R: Report) -> None:
    if not VARIANTS.exists():
        R.check("terminology_variants.yaml is up to date", ["missing (run --emit-variants)"])
    elif VARIANTS.read_text(encoding="utf-8") != text:
        R.check("terminology_variants.yaml is up to date", ["differs from glossary.yaml (run --emit-variants)"])
    else:
        R.check("terminology_variants.yaml is up to date", [])


def check_readme(sc: Schema, R: Report) -> None:
    if not README.exists():
        R.check("README tables match the schema", ["README.md is missing"])
        return
    rows: dict[str, list[str]] = {}
    for line in README.read_text(encoding="utf-8").splitlines():
        if line.startswith("|") and not re.match(r"^\|\s*-", line):
            cells = [c.strip().strip("`").strip() for c in line.strip().strip("|").split("|")]
            rows.setdefault(cells[0], cells)

    def parse_side(cell: str) -> set[str]:
        return {x.strip().strip("`") for x in cell.replace(" or ", ", ").split(",") if x.strip()}

    probs = []
    for c in sc.classes:
        if sc.class_label(c) not in rows:
            probs.append(f"class {sc.class_label(c)} has no README row")
    for p in sc.objprops:
        lab = sc.label(p)
        row = rows.get(lab)
        if not row or len(row) < 2 or ARROW not in row[1]:
            probs.append(f"relation {lab} has no README row with 'Domain {ARROW} Range'")
            continue
        dom, rng = row[1].split(ARROW, 1)
        if parse_side(dom) != sc.side_labels(p, RDFS.domain) or parse_side(rng) != sc.side_labels(p, RDFS.range):
            probs.append(f"relation {lab}: README says '{row[1]}', schema says "
                         f"{' or '.join(sorted(sc.side_labels(p, RDFS.domain)))} {ARROW} "
                         f"{' or '.join(sorted(sc.side_labels(p, RDFS.range)))}")
    for p in sc.dtprops:
        row = rows.get(local(p))
        if not row or len(row) < 3:
            probs.append(f"datatype property {local(p)} has no README row")
            continue
        if parse_side(row[1]) != sc.side_labels(p, RDFS.domain):
            probs.append(f"datatype property {local(p)}: README domain '{row[1]}' != schema")
        rng = list(sc.g.objects(p, RDFS.range))
        if rng and row[2] != f"xsd:{local(rng[0])}":
            probs.append(f"datatype property {local(p)}: README range '{row[2]}' != xsd:{local(rng[0])}")
    R.check("README has a row for every class, relationship and datatype property, with matching domain and range",
            probs)


# ---------------------------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--emit-ttl", action="store_true", help="write corvane_claims.ttl and corvane_claims.rdf")
    ap.add_argument("--emit-variants", action="store_true", help="write terminology_variants.yaml")
    args = ap.parse_args(argv)

    R = Report()
    try:
        g = parse_jsonld(JSONLD)
    except Exception as e:
        print(f"FAIL  parse {JSONLD.name} as JSON-LD: {e}")
        return 1
    print(f"PASS  parse {JSONLD.relative_to(ROOT)} with rdflib (format='json-ld'): {len(g)} triples")
    sc = Schema(g)
    glossary = load_glossary()
    check_schema(sc, glossary, R)
    check_variant_targets(sc, R)

    if args.emit_ttl:
        if R.failures:
            print("not emitting: fix the failures above first")
        else:
            emit_ttl(g)
    vtext = variants_doc(glossary, sc)
    if args.emit_variants:
        VARIANTS.write_text(vtext, encoding="utf-8")
        print(f"wrote {VARIANTS.relative_to(ROOT)}")
    check_derived_rdf(g, R)
    check_variants_file(vtext, R)
    check_readme(sc, R)

    print("PASS" if not R.failures else f"FAIL ({R.failures} check(s))")
    return 0 if not R.failures else 1


if __name__ == "__main__":
    sys.exit(main())

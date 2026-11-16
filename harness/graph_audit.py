#!/usr/bin/env python
"""Audit a knowledge graph extracted from the corpus, using the world model as ground truth.

Subcommands
    audit <export.json> [--expect questions/graph_expectations.yaml] [--out results/graph_audit_<label>.md]
        Totals (recomputed, next to every count the export states), the six checks of
        questions/GRAPH_EXPECTATIONS_FORMAT.md (duplicates, unmerged aliases, wrong merges, missing
        nodes/edges, hallucinated nodes, per-file coverage), roles extracted as people, the
        generic-relationship ratio and property coverage. Writes Markdown plus a JSON twin (same
        path, .json). The top 20 findings come first, then the details.
    diff <a.json> <b.json> [--expect ...] [--out results/graph_diff_<a>_vs_<b>.md]
        Nondeterminism metric for two graphs built from the same corpus in different batch orders:
        Jaccard overlap of nodes (type + normalised name) and edges (core type + endpoints),
        per-type deltas, and expected nodes/edges that exist in only one of the two graphs.
    expectations-skeleton [--out questions/graph_expectations.draft.yaml]
        Starter expectations file generated from the world model, for question writers to curate.
    selftest
        Builds a synthetic export in build/test_graph/ from a tiny fake world and asserts that every
        check finds exactly what was planted (also tests diff, shape detection and the skeleton).

Several JSON graph-export shapes are accepted; the shape is auto-detected and printed.

Normalisation (shared by every check)
    node name  NFKC; dashes folded; Nordic/Polish letters and accents ASCII-folded (ø->o, æ->ae,
               ł->l, é->e); casefolded; '&' -> 'and'; every run of other non-alphanumerics -> one
               space; a leading 'the ' dropped. Names compare equal on this form or on its
               space-free 'compact' form ('reserve-engine' == 'Reserve Engine' == 'ReserveEngine').
    node type  case and punctuation dropped ('ProcessStep' == 'process_step'); a type also matches a
               longer type that ends in it ('Rule' ~ 'BusinessRule') when both have 4+ characters.
    edge type  camelCase split to UPPER_SNAKE; the core relation is what remains after stripping
               BOTH the start-node label prefix and the end-node label suffix (labels may contain
               underscores, longest label first): PERSON_REPORTS_TO_PERSON -> REPORTS_TO,
               PROCESS_STEP_BELONGS_TO_PERSON -> BELONGS_TO. Comparison ignores case and punctuation,
               so REPORTS_TO == reportsTo == reports-to == PERSON_REPORTS_TO_PERSON. When matching an
               expected edge, a one-sided strip also counts (WRITES_TO_TABLE ~ PROGRAM_WRITES_TO_TABLE).
    tracing    a node traces to the world when its name equals a lexicon term (normalised or compact),
               or difflib ratio >= 0.85 with the SAME digit sequence (CLRRS066 is not CLRRS060), or,
               for names of 2+ content words and 10+ characters, a token-subset match either way.

    python -I harness/graph_audit.py <subcommand> --help
"""
from __future__ import annotations

import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import argparse
import collections
import dataclasses
import difflib
import json
import re
import shutil
import types
import unicodedata
from typing import Any, Iterable

import yaml

Path = pathlib.Path

DEFAULT_EXPECT = ROOT / "questions" / "graph_expectations.yaml"
DEFAULT_SKELETON = ROOT / "questions" / "graph_expectations.draft.yaml"
DEFAULT_WORLD = ROOT / "world"
DEFAULT_INDEX = ROOT / "build" / "index"
RESULTS = ROOT / "results"
SCHEMA_FILE = ROOT / "schemas" / "corvane_claims.jsonld"
TEST_DIR = ROOT / "build" / "test_graph"
DEFAULT_AS_OF = "2026-11-15"  # fallback only; a date stated by the world model wins
TOP_N = 20
FUZZY_CUTOFF = 0.85

# ---------------------------------------------------------------------------------------------
# Normalisation
# ---------------------------------------------------------------------------------------------

_FOLD = str.maketrans({
    "ø": "o", "Ø": "O", "æ": "ae", "Æ": "AE", "œ": "oe", "Œ": "OE", "ß": "ss", "ł": "l", "Ł": "L",
    "đ": "d", "Đ": "D", "ð": "d", "Ð": "D", "þ": "th", "Þ": "TH", "ı": "i",
    "\u2010": "-", "\u2011": "-", "\u2012": "-", "\u2013": "-", "\u2014": "-", "\u2015": "-", "\u2212": "-",
})
_NON_ALNUM = re.compile(r"[^0-9a-z]+")
_DIGITS = re.compile(r"\d+")
STOPWORDS = frozenset("the of and a an for to in on at by".split())


def _ascii_fold(text: str) -> str:
    t = unicodedata.normalize("NFKC", text).translate(_FOLD)
    return unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode("ascii")


def norm_name(s: Any) -> str:
    """Normalised node name (see the module docstring)."""
    if s is None:
        return ""
    t = _ascii_fold(str(s)).casefold().replace("&", " and ")
    t = _NON_ALNUM.sub(" ", t).strip()
    if t.startswith("the "):
        t = t[4:]
    return t


def compact(s: Any) -> str:
    return norm_name(s).replace(" ", "")


def content_tokens(s: Any) -> frozenset:
    return frozenset(t for t in norm_name(s).split() if t not in STOPWORDS)


def canon_type(s: Any) -> str:
    return re.sub(r"[^0-9a-z]", "", _ascii_fold(str(s or "")).casefold())


def type_matches(label: str, wanted: str | None) -> bool:
    """Node label vs an expected type (case/punctuation-insensitive, suffix-tolerant)."""
    b = canon_type(wanted)
    if b in ("", "any"):
        return True
    a = canon_type(label)
    if a == b:
        return True
    return min(len(a), len(b)) >= 4 and (a.endswith(b) or b.endswith(a))


def snake_upper(s: Any) -> str:
    t = unicodedata.normalize("NFKC", str(s or ""))
    t = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", t)
    t = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", t)
    return re.sub(r"[^A-Za-z0-9]+", "_", t).strip("_").upper()


def canon_rel(s: Any) -> str:
    return re.sub(r"[^A-Z0-9]", "", snake_upper(s))


def _bare_rel(etype: str) -> str:
    s = snake_upper(etype)
    return s[len("SCHEMA_REL_"):] if s.startswith("SCHEMA_REL_") and len(s) > 11 else s


def _label_pool(labels: Iterable[str]) -> list[str]:
    return sorted({snake_upper(l) for l in labels if l}, key=lambda x: (-len(x), x))


def core_relation(etype: str, start_label: str | None = None, end_label: str | None = None,
                  pool: Iterable[str] = ()) -> str:
    """UPPER_SNAKE core relation: strip the start-label prefix AND the end-label suffix.

    The real endpoint labels are tried first, then every known label (longest first). Both sides
    must match, otherwise the type is returned unchanged (only camelCase-split)."""
    s = _bare_rel(etype)
    pool = list(pool) if not isinstance(pool, list) else pool
    starts = ([snake_upper(start_label)] if start_label else []) + pool
    ends = ([snake_upper(end_label)] if end_label else []) + pool
    for a in starts:
        if a and s.startswith(a + "_"):
            rest = s[len(a) + 1:]
            for b in ends:
                if b and rest.endswith("_" + b) and len(rest) > len(b) + 1:
                    return rest[:-(len(b) + 1)]
    return s


def rel_forms(etype: str, start_label: str | None, end_label: str | None, pool: list[str] = ()) -> frozenset:
    """Every comparable form of an edge type (raw, core, one-sided strips), punctuation-free."""
    s = _bare_rel(etype)
    forms = {canon_rel(s), canon_rel(core_relation(etype, start_label, end_label, list(pool)))}
    if start_label:
        a = snake_upper(start_label)
        if s.startswith(a + "_") and len(s) > len(a) + 1:
            forms.add(canon_rel(s[len(a) + 1:]))
    if end_label:
        b = snake_upper(end_label)
        if s.endswith("_" + b) and len(s) > len(b) + 1:
            forms.add(canon_rel(s[:-(len(b) + 1)]))
    return frozenset(f for f in forms if f)


SCHEMA_NODE_PREFIX = "SchemaNode_"
GENERIC_RELATIONS = ("BELONGS_TO", "RELATES_TO", "HAS_MANY", "DEPENDS_ON", "HAS", "RELATED_TO", "ASSOCIATED_WITH")
GENERIC_CANON = frozenset(canon_rel(g) for g in GENERIC_RELATIONS)
RENAME_CANON = frozenset({"RENAMEDTO", "RENAMED", "WASRENAMEDTO"})
GENERIC_LABELS = frozenset({"entity", "node", "resource", "thing", "entity_", "__entity__", "base"})


def schema_type(label: str) -> str:
    return label[len(SCHEMA_NODE_PREFIX):] if label.startswith(SCHEMA_NODE_PREFIX) else label


# ---------------------------------------------------------------------------------------------
# Graph loading (shape auto-detection)
# ---------------------------------------------------------------------------------------------

NODE_KEY_FIELDS = ("key", "id", "identity", "elementId", "element_id", "uid", "_id")
START_FIELDS = ("start_key", "startKey", "start", "source", "from", "src", "startNode", "start_node", "_from")
END_FIELDS = ("end_key", "endKey", "end", "target", "to", "dst", "endNode", "end_node", "_to")
EDGE_TYPE_FIELDS = ("type", "label", "relation", "rel_type", "relationship", "relationship_type", "predicate", "edge_type")
FILE_FIELDS = ("source_files", "source_file", "file", "file_name", "filename", "file_path", "document", "documents",
               "source_document", "source_documents")
META_KEYS = frozenset({"id", "key", "label", "labels", "section_id", "llm_generated_id", "property_history", "embedding",
                       "embeddings", "created_at", "updated_at", "context_id", "chunk_id", "chunk_ids", "source_id",
                       "document_id", *FILE_FIELDS})
NAME_KEYS = ("name", "title", "full_name", "fullName", "display_name", "displayName", "label", "caption", "term",
             "canonical", "value")


@dataclasses.dataclass
class Node:
    key: str
    label: str
    name: str
    attrs: dict
    meta: dict
    files: list
    schema: bool = False
    norm: str = ""
    compact: str = ""

    def __post_init__(self) -> None:
        self.norm = norm_name(self.name)
        self.compact = self.norm.replace(" ", "")


@dataclasses.dataclass
class Edge:
    start: str
    end: str
    type: str
    props: dict
    files: list
    files_inferred: bool = False
    core: str = ""
    forms: frozenset = frozenset()
    schema: bool = False
    dangling: bool = False


def _ref_value(v: Any) -> str | None:
    if v is None or v == "":
        return None
    if isinstance(v, dict):
        for f in NODE_KEY_FIELDS:
            if v.get(f) not in (None, ""):
                return str(v[f])
        p = v.get("properties")
        if isinstance(p, dict):
            for f in ("key", "id"):
                if p.get(f) not in (None, ""):
                    return str(p[f])
        return None
    return str(v)


def _files_of(d: dict) -> list[str]:
    out: list[str] = []
    if not isinstance(d, dict):
        return out
    for f in FILE_FIELDS:
        v = d.get(f)
        if isinstance(v, str) and v.strip():
            out.append(v.strip())
        elif isinstance(v, list):
            out.extend(str(x).strip() for x in v if isinstance(x, (str, int)) and str(x).strip())
    ph = d.get("property_history")
    if isinstance(ph, list):
        for h in ph:
            if isinstance(h, dict) and isinstance(h.get("source_file"), str) and h["source_file"].strip():
                out.append(h["source_file"].strip())
    return list(dict.fromkeys(out))


def _pick_name(attrs: dict, meta: dict, label: str, key: str, nested: bool) -> str:
    ct = canon_type(label)
    for k in NAME_KEYS:
        v = attrs.get(k)
        if v is None or isinstance(v, bool) or not isinstance(v, (str, int, float)) or not str(v).strip():
            continue
        if k in ("name", "label") and not nested and canon_type(v) == ct:
            continue  # the type, not the entity name
        return str(v).strip()
    gid = meta.get("llm_generated_id") or attrs.get("llm_generated_id")
    if isinstance(gid, str) and gid.strip():
        g = gid.strip()
        pre = snake_upper(schema_type(label)).lower() + "_"
        if g.lower().startswith(pre) and len(g) > len(pre):
            g = g[len(pre):]
        return g.replace("_", " ").strip()
    return key.rsplit(":", 1)[-1]


def _parse_node(item: dict, i: int) -> Node:
    props = item.get("properties") if isinstance(item.get("properties"), dict) else None
    if props is None:
        props = {k: v for k, v in item.items() if k not in ("labels", "label", "type", "identity", "elementId", "element_id")}
    key = next((str(item[f]) for f in NODE_KEY_FIELDS if item.get(f) not in (None, "")), None)
    if key is None:
        key = next((str(props[f]) for f in ("key", "id") if props.get(f) not in (None, "")), f"#node{i}")
    label = item.get("label") if isinstance(item.get("label"), str) else None
    if not label and isinstance(item.get("labels"), list) and item["labels"]:
        labs = [str(l) for l in item["labels"]]
        specific = [l for l in labs if canon_type(l) not in GENERIC_LABELS]
        label = (specific or labs)[0]
    if not label and isinstance(item.get("type"), str) and item["type"].lower() != "node":
        label = item["type"]
    if not label:
        label = str(props.get("label") or props.get("type") or "Unknown")
    inner = props.get("properties")
    if isinstance(inner, dict):
        attrs, meta, nested = dict(inner), {k: v for k, v in props.items() if k != "properties"}, True
    else:
        attrs = {k: v for k, v in props.items() if k not in META_KEYS}
        meta = {k: v for k, v in props.items() if k in META_KEYS}
        nested = False
    name = _pick_name(attrs, meta, label, key, nested)
    files = _files_of(meta) or _files_of(attrs) or _files_of(item)
    schema = label.startswith(SCHEMA_NODE_PREFIX) or label == "SchemaNode" or ":schema:" in key
    return Node(key, label, name, attrs, meta, files, schema)


def _parse_edge(item: dict, i: int) -> Edge:
    props = item.get("properties") if isinstance(item.get("properties"), dict) else {}
    start = next((_ref_value(item[f]) for f in START_FIELDS if item.get(f) not in (None, "")), None)
    end = next((_ref_value(item[f]) for f in END_FIELDS if item.get(f) not in (None, "")), None)
    et = None
    for f in EDGE_TYPE_FIELDS:
        v = item.get(f)
        if isinstance(v, str) and v.strip() and v.strip().lower() not in ("relationship", "edge", "link", "rel"):
            et = v.strip()
            break
    if et is None:
        et = str(props.get("type") or props.get("label") or "RELATED")
    return Edge(start or f"#missing-start-{i}", end or f"#missing-end-{i}", et, props, _files_of(props) or _files_of(item))


def _is_edge_item(it: dict) -> bool:
    t = str(it.get("type", "")).lower()
    if t in ("relationship", "edge", "link", "rel"):
        return True
    if t == "node":
        return False
    return any(f in it for f in START_FIELDS) and any(f in it for f in END_FIELDS)


def _stated_counts(*dicts: dict) -> dict:
    out: dict[str, int] = {}
    for d in dicts:
        for k, v in (d or {}).items():
            if isinstance(v, int) and not isinstance(v, bool) and re.search(r"count|dropped|total|^num_|^n_", k) and k not in out:
                out[k] = v
    return out


class Graph:
    def __init__(self, nodes: list[Node], edges: list[Edge], shape: str, src: str = "", stated: dict | None = None,
                 node_types: Any = None, edge_types: Any = None, context_id: Any = None):
        self.shape, self.src, self.stated = shape, src, stated or {}
        self.declared_node_types, self.declared_edge_types, self.context_id = node_types, edge_types, context_id
        self.nodes: dict[str, Node] = {}
        self.duplicate_keys = 0
        for n in nodes:
            if n.key in self.nodes:
                self.duplicate_keys += 1
                n.key = f"{n.key}#dup{self.duplicate_keys}"
            self.nodes[n.key] = n
        self.edges = edges
        self.instance_nodes = [n for n in self.nodes.values() if not n.schema]
        self.schema_nodes = [n for n in self.nodes.values() if n.schema]
        self.pool = _label_pool([n.label for n in self.instance_nodes] + [schema_type(n.label) for n in self.schema_nodes])
        for e in edges:
            s, t = self.nodes.get(e.start), self.nodes.get(e.end)
            e.dangling = s is None or t is None
            up = snake_upper(e.type)
            e.schema = up == "NODE_IS" or up.startswith("SCHEMA_REL") or bool(s and s.schema) or bool(t and t.schema)
            sl, tl = (schema_type(s.label) if s else None), (schema_type(t.label) if t else None)
            e.core = core_relation(e.type, sl, tl, self.pool)
            e.forms = rel_forms(e.type, sl, tl, self.pool)
            if not e.files and s is not None and t is not None:
                shared = [f for f in s.files if f in set(t.files)]
                if shared:
                    e.files, e.files_inferred = shared, True
        self.inst_edges = [e for e in edges if not e.schema and not e.dangling]
        self.by_compact: dict[str, list[str]] = collections.defaultdict(list)
        for n in self.instance_nodes:
            if n.compact:
                self.by_compact[n.compact].append(n.key)
        self.adj: dict[tuple, list[Edge]] = collections.defaultdict(list)
        for e in self.inst_edges:
            self.adj[(e.start, e.end)].append(e)

    def find(self, wanted_type: str | None, names: Iterable[str]) -> list[str]:
        """Keys of instance nodes of ``wanted_type`` whose name is any of ``names`` (normalised)."""
        out: list[str] = []
        for nm in names:
            for k in self.by_compact.get(compact(nm), ()):
                if k not in out and type_matches(self.nodes[k].label, wanted_type):
                    out.append(k)
        return out

    def edges_between(self, a_keys: Iterable[str], b_keys: Iterable[str]) -> list[Edge]:
        out = []
        for a in a_keys:
            for b in b_keys:
                out.extend(self.adj.get((a, b), ()))
        return out


def parse_graph(data: Any, src: str = "") -> Graph:
    stated, nt, et, ctx = {}, None, None, None
    if isinstance(data, dict):
        ext = data.get("extraction")
        if isinstance(ext, dict) and isinstance(ext.get("nodes"), list):
            shape = "ingestion response: extraction.{nodes, relationships}"
            raw_n = ext.get("nodes") or []
            raw_e = next((ext[k] for k in ("relationships", "edges", "links") if isinstance(ext.get(k), list)), [])
            stated = _stated_counts(ext, data)
            nt = data.get("node_types", ext.get("node_types"))
            et = data.get("edge_types", ext.get("edge_types"))
            ctx = data.get("context_id", ext.get("context_id"))
        elif isinstance(data.get("nodes"), list):
            ek = next((k for k in ("relationships", "edges", "links") if isinstance(data.get(k), list)), None)
            shape = f"top-level {{nodes, {ek}}}" if ek else "top-level {nodes}"
            raw_n, raw_e = data["nodes"], (data[ek] if ek else [])
            stated = _stated_counts(data)
            nt, et, ctx = data.get("node_types"), data.get("edge_types"), data.get("context_id")
        else:
            for k in ("graph", "data", "result", "results", "export"):
                if isinstance(data.get(k), (dict, list)):
                    g = parse_graph(data[k], src)
                    g.shape = f"{k} -> {g.shape}"
                    return g
            raise ValueError("unrecognised graph export: no 'nodes' list found")
    elif isinstance(data, list):
        raw_n = [it for it in data if isinstance(it, dict) and not _is_edge_item(it)]
        raw_e = [it for it in data if isinstance(it, dict) and _is_edge_item(it)]
        shape = "plain list of node and relationship records"
    else:
        raise ValueError(f"unrecognised graph export (top level is {type(data).__name__})")
    first = next((n for n in raw_n if isinstance(n, dict)), None)
    if first and isinstance(first.get("labels"), list) and any(f in first for f in ("identity", "elementId", "id")):
        shape += " (property-graph records: id/identity, labels[], properties)"
    nodes = [_parse_node(it, i) for i, it in enumerate(raw_n) if isinstance(it, dict)]
    edges = [_parse_edge(it, i) for i, it in enumerate(raw_e) if isinstance(it, dict)]
    return Graph(nodes, edges, shape, src, stated, nt, et, ctx)


def load_graph(path: Path | str) -> Graph:
    text = Path(path).read_text(encoding="utf-8-sig")
    try:
        data = json.loads(text)
        jsonl = False
    except json.JSONDecodeError:
        data = [json.loads(ln) for ln in text.splitlines() if ln.strip()]
        jsonl = True
    g = parse_graph(data, str(path))
    if jsonl:
        g.shape = "JSON lines: " + g.shape
    return g


# ---------------------------------------------------------------------------------------------
# World model view (worldlib when present, world/data/*.yaml otherwise)
# ---------------------------------------------------------------------------------------------

IDENTITY_KINDS = frozenset({"id", "name", "alias", "rename", "glossary", "code", "lexicon"})
LEX_STR_KEYS = {"id": "id", "name": "name", "legal_name": "name", "short_name": "alias", "short": "alias",
                "alias": "alias", "title": "title", "canonical": "glossary", "schema_term": "glossary",
                "term": "glossary", "abbreviation": "glossary", "acronym": "glossary", "expansion": "glossary",
                "from_name": "rename", "to_name": "rename", "old_id": "rename", "old_name": "rename",
                "new_name": "rename", "former_name": "rename", "code": "code"}
LEX_LIST_KEYS = {"aliases": "alias", "variants": "glossary", "synonyms": "glossary", "abbreviations": "glossary",
                 "renames": "rename", "former_names": "rename"}
AS_OF_KEYS = ("today", "world_date", "world_today", "TODAY", "current_date")
YAML_EXCLUDE = re.compile(r"denylist", re.IGNORECASE)
RECORD_ID_KEYS = ("id", "name", "file_id", "map", "key")
# nested lists whose entries name the enclosing entity itself (other nested names, e.g. table columns,
# are parts: traceable, but not identities of the parent)
IDENTITY_CONTAINERS = frozenset({"name_history", "renames", "renamed_from", "renamed_to", "former_names", "aliases",
                                 "variants", "branches"})
PEOPLE_COLLECTIONS = frozenset({"people", "persons", "person", "staff", "employees"})
# when a surface form names several entities, one from these collections wins over glossary entries,
# corpus anchors, tickets and other secondary records
CORE_COLLECTIONS = frozenset(canon_type(x) for x in (
    "people", "systems", "services", "programs", "tables", "db2_tables", "pg_tables", "interfaces", "rules", "teams",
    "departments", "committees", "vendors", "products", "claim_types", "locations", "stages", "steps", "regulators",
    "company", "copybooks", "jcl_jobs", "bms_maps", "kafka_topics", "circulars", "reports"))
TYPED_REF_PREFIX = re.compile(r"^[A-Za-z_]+:(?!//)")
_PAREN = re.compile(r"\s*\(([^()]*)\)")
_ACRONYM = re.compile(r"^[A-Z0-9][A-Z0-9&/-]{1,9}$")


def _as_dict(obj: Any) -> dict:
    if isinstance(obj, dict):
        return obj
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        return dataclasses.asdict(obj)
    if hasattr(obj, "__dict__"):
        return dict(vars(obj))
    return {"value": obj}


def _record_like(v: Any) -> bool:
    return isinstance(v, dict) and any(k in v for k in ("id", "name", "title"))


def _harvest(stem: str, doc: Any, out: dict) -> set:
    """Entity collections in one YAML document; returns the top-level keys consumed."""
    used: set = set()

    def add(name: str, records: Any) -> None:
        cname = name if name not in out else f"{stem}.{name}"
        recs: dict[str, dict] = {}
        if isinstance(records, dict):
            for k, r in records.items():
                r = _as_dict(r)
                recs[str(r.get("id") or k)] = r
        else:
            for i, r in enumerate(records):
                r = _as_dict(r)
                rid = next((r[k] for k in RECORD_ID_KEYS if isinstance(r.get(k), (str, int)) and str(r[k])), f"{name}#{i}")
                recs[str(rid)] = r
        out[cname] = recs

    def is_list(v: Any) -> bool:
        return isinstance(v, list) and v and sum(_record_like(x) for x in v) >= max(1, len(v) // 2)

    def is_map(v: Any) -> bool:
        return isinstance(v, dict) and v and all(isinstance(k, str) and isinstance(x, dict) for k, x in v.items()) \
            and sum(_record_like(x) for x in v.values()) >= max(1, len(v) // 2)

    if is_list(doc):
        add(stem, doc)
    elif isinstance(doc, dict):
        if isinstance(doc.get("id"), str):
            add(stem, [doc])
            return set(doc)
        for k, v in doc.items():
            if is_list(v) or is_map(v):
                add(k, v)
                used.add(k)
            elif isinstance(v, dict) and isinstance(v.get("id"), str):
                add(k, [v])
                used.add(k)
    return used


def _collections_from_yaml(data_dir: Path) -> tuple[dict, dict, list]:
    collections_: dict[str, dict] = {}
    docs: dict[str, Any] = {}
    leftovers: list = []
    notes: list[str] = []
    for f in sorted(list(data_dir.glob("*.yaml")) + list(data_dir.glob("*.yml"))):
        if YAML_EXCLUDE.search(f.name):
            continue
        try:
            doc = yaml.safe_load(f.read_text(encoding="utf-8"))
        except (yaml.YAMLError, OSError) as exc:
            notes.append(f"{f.name}: unreadable ({type(exc).__name__}); skipped")
            continue
        docs[f.stem] = doc
        used = _harvest(f.stem, doc, collections_)
        if isinstance(doc, dict):
            leftovers.extend((f"{f.stem}:{k}", v) for k, v in doc.items() if k not in used and isinstance(v, (dict, list)))
    return collections_, docs, [leftovers, notes]


def _collections_from_object(W: Any) -> dict:
    out: dict[str, dict] = {}
    items = W.items() if isinstance(W, dict) else []
    if not isinstance(W, dict):
        tmp = []
        for k in dir(W):
            if k.startswith("_"):
                continue
            try:
                v = getattr(W, k)
            except Exception:
                continue
            tmp.append((k, v))
        items = tmp
    for k, v in items:
        if callable(v) and not isinstance(v, (dict, list)):
            continue
        if isinstance(v, dict) and v and all(isinstance(x, dict) or hasattr(x, "__dict__") for x in v.values()):
            recs = {str(i): _as_dict(r) for i, r in v.items()}
            if sum(_record_like(r) for r in recs.values()) >= max(1, len(recs) // 2):
                out[k] = recs
        elif isinstance(v, list) and v and all(isinstance(x, dict) or hasattr(x, "__dict__") for x in v):
            recs = {}
            for i, r in enumerate(v):
                r = _as_dict(r)
                recs[str(r.get("id") or r.get("name") or f"{k}#{i}")] = r
            if sum(_record_like(r) for r in recs.values()) >= max(1, len(recs) // 2):
                out[k] = recs
    return out


def _ref_of(r: Any) -> str:
    if isinstance(r, dict):
        for k in ("id", "ref", "entity_id", "entity", "world_ref"):
            if r.get(k) not in (None, ""):
                return str(r[k])
        return json.dumps(r, sort_keys=True, default=str)
    if isinstance(r, (list, tuple)) and r:
        return str(r[-1])
    if hasattr(r, "id"):
        return str(getattr(r, "id"))
    return str(r)


def _lex_kind(k: Any) -> str:
    s = str(k or "lexicon").lower()
    if "title" in s or "role" in s:
        return "title"
    if "gloss" in s or "term" in s:
        return "glossary"
    for known in ("alias", "rename", "name", "id", "code"):
        if known in s:
            return known
    return "lexicon"


def _lexicon_entries(lx: Any) -> Iterable[tuple[str, str, str]]:
    """(term, ref, kind) from whatever shape worldlib's lexicon() returns."""
    if isinstance(lx, dict):
        for term, v in lx.items():
            for r in (v if isinstance(v, (list, tuple, set)) else [v]):
                kind = r.get("kind") if isinstance(r, dict) else None
                yield str(term), _ref_of(r), _lex_kind(kind)
        return
    for e in lx or []:
        term = ref = kind = None
        if isinstance(e, dict):
            term = next((e[k] for k in ("term", "text", "surface", "alias", "name", "label") if e.get(k)), None)
            ref = next((e[k] for k in ("ref", "entity_ref", "entity", "entity_id", "world_ref", "id", "target")
                        if e.get(k) not in (None, "")), None)
            kind = e.get("kind") or e.get("type")
        elif isinstance(e, (list, tuple)) and len(e) >= 2:
            term, ref = e[0], e[1]
            kind = e[2] if len(e) > 2 else None
        else:
            term = getattr(e, "term", None) or getattr(e, "text", None)
            ref = getattr(e, "ref", None) or getattr(e, "entity", None)
            kind = getattr(e, "kind", None)
        if term and ref is not None:
            yield str(term), _ref_of(ref), _lex_kind(kind)


def _date(v: Any) -> str:
    return str(v)[:10] if v not in (None, "") else ""


def _in_period(h: dict, as_of: str) -> bool:
    frm = _date(h.get("from") or h.get("valid_from") or h.get("effective_from"))
    to = _date(h.get("to") or h.get("valid_to") or h.get("effective_to"))
    return (not frm or frm <= as_of) and (not to or to >= as_of)


class World:
    """Entity collections plus a lexicon of every name/alias/ID/title/glossary term with its entity ref."""

    def __init__(self, collections_: dict, source: str, docs: dict | None = None, leftovers: list = (),
                 lexicon_extra: Iterable = (), as_of: str | None = None, notes: Iterable[str] = ()):
        self.collections = collections_
        self.source = source
        self.docs = docs or {}
        self.notes = list(notes)
        self.entity: dict[str, tuple[str, dict]] = {}
        self.entries: list[tuple[str, str, str]] = []
        for cname, recs in collections_.items():
            for rid, rec in recs.items():
                self.entity.setdefault(rid, (cname, rec))
        for cname, recs in collections_.items():
            for rid, rec in recs.items():
                self._walk(rec, rid, cname, 0)
        for ref, val in leftovers:
            self._walk(val, ref, ref.split(":")[0], 1, demote=True)
        # name -> ref, so typed refs from a lexicon ('SERVICE:reserve-engine', 'ORG:company') land on entity ids
        self._name_ref: dict[str, str | None] = {}
        for ref, (cname, rec) in list(self.entity.items()):
            nm = rec.get("name") if isinstance(rec, dict) else None
            if isinstance(nm, str) and nm not in self.entity:
                self._name_ref[nm] = ref if self._name_ref.get(nm, ref) == ref else None
        for cname, recs in collections_.items():
            if len(recs) == 1:
                self._name_ref.setdefault(cname.split(".")[-1], next(iter(recs)))
        for term, ref, kind in lexicon_extra:
            self._add(term, self.norm_ref(ref), kind)
        self.as_of = as_of or self._find_as_of(docs or {}) or DEFAULT_AS_OF
        self._index()

    # --- construction ------------------------------------------------------------------------
    @classmethod
    def from_yaml_dir(cls, data_dir: Path, notes: list[str] | None = None) -> "World":
        cols, docs, (leftovers, n2) = _collections_from_yaml(Path(data_dir))
        return cls(cols, f"{disp(data_dir)}/*.yaml", docs, leftovers, (), None, (notes or []) + n2)

    @classmethod
    def from_object(cls, W: Any, data_dir: Path | None = None, notes: list[str] | None = None) -> "World":
        notes = list(notes or [])
        lex: list = []
        fn = getattr(W, "lexicon", None) if not isinstance(W, dict) else W.get("lexicon")
        try:
            lx = fn() if callable(fn) else fn
            lex = list(_lexicon_entries(lx)) if lx is not None else []
        except Exception as exc:
            notes.append(f"lexicon() failed ({type(exc).__name__}: {exc}); lexicon built from entity fields only")
        cols, docs, leftovers, src = {}, {}, [], "world.worldlib.load_world()"
        if data_dir is not None and Path(data_dir).is_dir():
            cols, docs, (leftovers, n2) = _collections_from_yaml(Path(data_dir))
            notes += n2
            src += " + world/data/*.yaml"
        if not cols:
            cols = _collections_from_object(W)
        as_of = None
        for k in ("today", "TODAY", "as_of", "world_date", "AS_OF"):
            v = W.get(k) if isinstance(W, dict) else getattr(W, k, None)
            if isinstance(v, str) or hasattr(v, "isoformat"):
                as_of = _date(v)
                break
        return cls(cols, src, docs, leftovers, lex, as_of, notes)

    def _add(self, term: Any, ref: str, kind: str) -> None:
        if isinstance(term, bool) or not isinstance(term, (str, int)):
            return
        t = str(term).strip()
        if t and len(t) <= 200:
            self.entries.append((t, ref, kind))
            # 'Change Advisory Board (CAB)' also names 'Change Advisory Board' and 'CAB'
            bare = _PAREN.sub("", t).strip()
            if bare and bare != t:
                self.entries.append((bare, ref, kind))
                for inner in _PAREN.findall(t):
                    if _ACRONYM.match(inner.strip()):
                        self.entries.append((inner.strip(), ref, kind))

    def _walk(self, obj: Any, ref: str, cname: str, depth: int, demote: bool = False) -> None:
        """Collect lexicon terms. Names inside nested non-entity dicts (e.g. table columns) are
        demoted to 'part': traceable, but not identities of the enclosing entity."""
        if isinstance(obj, dict):
            own = ref
            if depth > 0:
                if isinstance(obj.get("id"), str) and obj["id"] != ref:
                    own, demote = obj["id"], False
                    self.entity.setdefault(own, (cname, obj))
                elif obj.get("aliases") and isinstance(obj.get("name"), str):
                    own, demote = f"{ref}/{obj['name']}", False
                    self.entity.setdefault(own, (cname, obj))

            def add(v: Any, kind: str) -> None:
                self._add(v, own, "part" if demote and kind in IDENTITY_KINDS else kind)

            for k, v in obj.items():
                if k in LEX_STR_KEYS and isinstance(v, (str, int)) and not isinstance(v, bool):
                    add(v, LEX_STR_KEYS[k])
                elif k in LEX_LIST_KEYS and isinstance(v, list):
                    for x in v:
                        if isinstance(x, (str, int)) and not isinstance(x, bool):
                            add(x, LEX_LIST_KEYS[k])
                        elif isinstance(x, dict):
                            self._walk(x, own, cname, depth + 1, demote)
                elif k == "local_names" and isinstance(v, dict):
                    for x in v.values():
                        add(x, "alias")
                elif k == "role_aliases" and isinstance(v, list):  # roles ('the CFO'), not identities
                    for x in v:
                        self._add(x.get("alias") if isinstance(x, dict) else x, own, "title")
                elif isinstance(v, (dict, list)):
                    self._walk(v, own, cname, depth + 1, demote or k not in IDENTITY_CONTAINERS)
        elif isinstance(obj, list):
            for x in obj:
                self._walk(x, ref, cname, depth + 1, demote)

    @staticmethod
    def _find_as_of(docs: dict) -> str | None:
        for doc in docs.values():
            if isinstance(doc, dict):
                for k in AS_OF_KEYS:
                    if doc.get(k):
                        return _date(doc[k])
        for doc in docs.values():
            if isinstance(doc, dict):
                for v in doc.values():
                    if isinstance(v, dict):
                        for k in AS_OF_KEYS:
                            if v.get(k):
                                return _date(v[k])
        return None

    def _index(self) -> None:
        self.norm_map: dict[str, str] = {}
        self.compact_map: dict[str, str] = {}
        self.ident: dict[str, set] = collections.defaultdict(set)
        self.ref_terms: dict[str, list] = collections.defaultdict(list)
        for term, ref, kind in self.entries:
            n = norm_name(term)
            c = n.replace(" ", "")
            if not c:
                continue
            self.norm_map.setdefault(n, term)
            self.compact_map.setdefault(c, term)
            # a title names a rule/incident/ADR, but is only a role for a person
            if kind in IDENTITY_KINDS or (kind == "title" and not self.is_person(ref)):
                self.ident[c].add(ref)
                if term not in self.ref_terms[ref]:
                    self.ref_terms[ref].append(term)
        self.by_len: dict[int, list[str]] = collections.defaultdict(list)
        self.tok_entries: list[tuple[frozenset, str]] = []
        self.tok_index: dict[str, list[int]] = collections.defaultdict(list)
        for n in self.norm_map:
            self.by_len[len(n)].append(n)
            toks = frozenset(t for t in n.split() if t not in STOPWORDS)
            if len(toks) >= 2:
                self.tok_index_add(toks, n)
        self._trace_cache: dict[str, Any] = {}

    def tok_index_add(self, toks: frozenset, n: str) -> None:
        idx = len(self.tok_entries)
        self.tok_entries.append((toks, n))
        for t in toks:
            self.tok_index[t].append(idx)

    # --- lookups -----------------------------------------------------------------------------
    def is_person(self, ref: str) -> bool:
        ent = self.entity.get(ref)
        return bool(ent) and canon_type(ent[0].split(".")[-1]) in PEOPLE_COLLECTIONS

    def _lookup(self, ident: str) -> str | None:
        if ident in self.entity:
            return ident
        r = self._name_ref.get(ident)
        return r if r in self.entity else None

    def norm_ref(self, ref: Any) -> str:
        """Entity id for a ref such as 'P007', 'PERSON:P007', 'SERVICE:reserve-engine', 'RULE:BR-1@v2'.
        Sub-entity refs ('TABLE:X#columns.Y') stay distinct."""
        s = str(ref)
        if s in self.entity:
            return s
        tail = re.sub(TYPED_REF_PREFIX, "", s)
        if "#" in tail:
            return s
        for cand in (tail, tail.split("@", 1)[0]):
            hit = self._lookup(cand)
            if hit:
                return hit
        return s

    def resolve_ref(self, world_ref: Any) -> tuple[str | None, str | None]:
        """(entity id, field) of a manifest world_ref: 'BR-FRD-012@v2', 'P012.reports_to',
        'RULE:BR-FRD-031@v2#parameters.threshold', 'CLR.T_RESERVE.columns'."""
        if world_ref in (None, ""):
            return None, None
        s = re.sub(TYPED_REF_PREFIX, "", str(world_ref).strip())
        field = None
        if "#" in s:
            s, field = s.split("#", 1)
        base, _, ver = s.partition("@")
        if "." in ver and not field:
            field = ver.split(".", 1)[1]
        hit = self._lookup(base)
        if hit:
            return hit, field
        parts = base.split(".")
        for i in range(len(parts) - 1, 0, -1):
            hit = self._lookup(".".join(parts[:i]))
            if hit:
                return hit, ".".join(parts[i:]) + (f"#{field}" if field else "")
        return None, None

    def identity_refs(self, name: Any) -> set:
        """Entities this surface form names; a single core entity wins over secondary records."""
        refs = set(self.ident.get(compact(name), ()))
        if len(refs) > 1:
            core = {r for r in refs if r in self.entity and canon_type(self.entity[r][0].split(".")[-1]) in CORE_COLLECTIONS}
            if len(core) == 1:
                return core
        return refs

    def names_for_ref(self, ref: str) -> list[str]:
        return list(self.ref_terms.get(ref) or [ref])

    def trace(self, name: Any) -> tuple[str, str] | None:
        """(method, matched world term) when ``name`` traces to the lexicon, else None."""
        n = norm_name(name)
        if n in self._trace_cache:
            return self._trace_cache[n]
        res = self._trace(n)
        self._trace_cache[n] = res
        return res

    def _trace(self, n: str) -> tuple[str, str] | None:
        c = n.replace(" ", "")
        if not c:
            return None
        if n in self.norm_map:
            return "exact", self.norm_map[n]
        if c in self.compact_map:
            return "exact (spacing/punctuation)", self.compact_map[c]
        L = len(n)
        lo = int(L * FUZZY_CUTOFF / (2 - FUZZY_CUTOFF))
        hi = int(L * (2 - FUZZY_CUTOFF) / FUZZY_CUTOFF) + 1
        cands = [m for ln in range(lo, hi + 1) for m in self.by_len.get(ln, ())]
        digits = _DIGITS.findall(n)
        # numbers carry identity: CLRRS066 is not a typo of CLRRS060
        for best in difflib.get_close_matches(n, cands, n=8, cutoff=FUZZY_CUTOFF):
            if _DIGITS.findall(best) == digits:
                ratio = difflib.SequenceMatcher(None, n, best).ratio()
                return f"fuzzy {ratio:.2f}", self.norm_map[best]
        toks = frozenset(t for t in n.split() if t not in STOPWORDS)
        if len(toks) >= 2 and len(n) >= 10:
            hits = collections.Counter(i for t in toks for i in self.tok_index.get(t, ()))
            inside = sorted(i for i, k in hits.items() if k == len(self.tok_entries[i][0]))
            if inside:
                return "token subset (world name inside node name)", self.norm_map[self.tok_entries[inside[0]][1]]
            lists = [set(self.tok_index.get(t, ())) for t in toks]
            common = set.intersection(*lists) if all(lists) else set()
            if common:
                return "token subset (node name inside world name)", self.norm_map[self.tok_entries[min(common)][1]]
        return None

    def coll(self, *names: str) -> dict:
        for w in (canon_type(n) for n in names):
            for cname, recs in self.collections.items():
                if canon_type(cname.split(".")[-1]) == w:
                    return recs
        return {}

    def colls(self, *names: str) -> dict:
        out: dict = {}
        wanted = {canon_type(n) for n in names}
        for cname, recs in self.collections.items():
            if canon_type(cname.split(".")[-1]) in wanted:
                for k, v in recs.items():
                    out.setdefault(k, v)
        return out

    @property
    def people(self) -> dict:
        return self.coll("people", "persons", "person", "staff", "employees")

    def org_units(self) -> list[tuple[str, str, str]]:
        """(name, kind, ref) for departments, teams and committees, including former names."""
        out = []
        for kind, names in (("department", ("departments", "divisions")), ("team", ("teams", "squads", "units")),
                            ("committee", ("committees", "forums"))):
            for rid, rec in self.colls(*names).items():
                for nm in [rec.get("name")] + [h.get("name") for h in rec.get("name_history") or [] if isinstance(h, dict)]:
                    if isinstance(nm, str) and nm.strip():
                        out.append((nm, kind, rid))
        return out


def rec_name(rec: dict, rid: str) -> str:
    for k in ("name", "title", "canonical", "legal_name", "short_name"):
        if isinstance(rec.get(k), str) and rec[k].strip():
            return rec[k].strip()
    return str(rid)


def titles_of(p: dict) -> list[str]:
    out = []
    for t in p.get("titles") or []:
        v = t.get("title") if isinstance(t, dict) else t
        if isinstance(v, str) and v.strip():
            out.append(v.strip())
    for k in ("title", "job_title", "role"):
        if isinstance(p.get(k), str) and p[k].strip():
            out.append(p[k].strip())
    return list(dict.fromkeys(out))


def role_aliases_of(p: dict) -> list[tuple[str, bool]]:
    """(alias, current?) for a person's role aliases."""
    out = []
    for r in p.get("role_aliases") or []:
        if isinstance(r, dict) and isinstance(r.get("alias"), str):
            out.append((r["alias"], not r.get("to")))
        elif isinstance(r, str):
            out.append((r, True))
    return out


def manager_at(p: dict, as_of: str) -> str | None:
    rt = p.get("reports_to") if p.get("reports_to") is not None else p.get("manager_history") or p.get("managers")
    if isinstance(rt, str):
        return rt
    for h in rt or []:
        if isinstance(h, dict) and _in_period(h, as_of):
            m = h.get("manager_id") or h.get("manager") or h.get("person") or h.get("id")
            return str(m) if m else None
    if isinstance(p.get("manager"), str):
        return p["manager"]
    return None


def employed_at(p: dict, as_of: str) -> bool:
    emp = p.get("employment")
    if isinstance(emp, dict):
        frm, to = _date(emp.get("from")), _date(emp.get("to"))
        if (frm and frm > as_of) or (to and to < as_of):
            return False
    return True


def owner_at(rec: dict, as_of: str) -> str | None:
    for h in rec.get("owner_history") or []:
        if isinstance(h, dict) and _in_period(h, as_of):
            return h.get("person") or h.get("owner") or h.get("id")
    o = rec.get("owner")
    return o if isinstance(o, str) else None


def load_world_view(world_dir: Path | str = DEFAULT_WORLD, use_lib: bool = True) -> tuple[World | None, list[str]]:
    notes: list[str] = []
    world_dir = Path(world_dir)
    data_dir = world_dir / "data"
    has_yaml = data_dir.is_dir() and any(f for f in list(data_dir.glob("*.yaml")) + list(data_dir.glob("*.yml"))
                                         if not YAML_EXCLUDE.search(f.name))
    W = None
    if use_lib and (world_dir / "worldlib.py").exists():
        if world_dir.resolve() == DEFAULT_WORLD.resolve():
            try:
                from world.worldlib import load_world  # type: ignore
                W = load_world()
            except Exception as exc:
                notes.append(f"world.worldlib.load_world() failed ({type(exc).__name__}: {exc}); using world/data/*.yaml")
        else:
            notes.append("worldlib is only imported from the repo's world/ package; using YAML")
    if W is not None:
        w = World.from_object(W, data_dir if has_yaml else None, notes)
        return w, notes
    if has_yaml:
        return World.from_yaml_dir(data_dir, notes), notes
    notes.append(f"no world model found ({world_dir}/worldlib.py and {data_dir}/*.yaml both absent)")
    return None, notes


# ---------------------------------------------------------------------------------------------
# Expectations, manifests, corpus files
# ---------------------------------------------------------------------------------------------

def _names(d: Any) -> list[str]:
    if isinstance(d, str):
        return [d]
    if not isinstance(d, dict):
        return []
    out = []
    for k in ("name", "canonical"):
        if isinstance(d.get(k), str):
            out.append(d[k])
    for k in ("match_any", "variants", "names"):
        if isinstance(d.get(k), list):
            out.extend(str(x) for x in d[k] if x not in (None, ""))
    return list(dict.fromkeys(out))


@dataclasses.dataclass
class Expectations:
    path: str
    as_of: str | None
    nodes: list
    edges: list
    merge_expected: list
    must_not_merge: list
    must_not_exist: list

    def types(self) -> list[str]:
        out = []
        for sec in (self.nodes, self.merge_expected, self.must_not_merge, self.must_not_exist):
            out += [x.get("type") for x in sec if x.get("type")]
        for e in self.edges:
            out += [e["from"].get("type"), e["to"].get("type")]
        return [t for t in out if t]


def load_expectations(path: Path | str) -> Expectations:
    doc = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    if not isinstance(doc, dict):
        raise ValueError(f"{path}: top level must be a mapping")

    def lst(k: str) -> list[dict]:
        return [x for x in (doc.get(k) or []) if isinstance(x, dict)]

    def ep(x: Any) -> dict:
        return {"type": x.get("type") if isinstance(x, dict) else None, "names": _names(x)}

    nodes = [{**x, "id": str(x.get("id", f"node#{i}")), "names": _names(x),
              "importance": x.get("importance", "medium"), "evidence": list(x.get("evidence") or [])}
             for i, x in enumerate(lst("nodes"))]
    edges = [{**x, "id": str(x.get("id", f"edge#{i}")), "from": ep(x.get("from")), "to": ep(x.get("to")),
              "evidence": list(x.get("evidence") or [])} for i, x in enumerate(lst("edges"))]
    merges = [{**x, "id": str(x.get("id", f"merge#{i}")), "names": _names(x)} for i, x in enumerate(lst("merge_expected"))]
    nmm = [{**x, "id": str(x.get("id", f"nmm#{i}")), "names": _names(x), "distinct": list(x.get("distinct") or []),
            "distinguishing": list(x.get("distinguishing") or [])} for i, x in enumerate(lst("must_not_merge"))]
    mne = [{**x, "id": str(x.get("id", f"mne#{i}")), "names": _names(x)} for i, x in enumerate(lst("must_not_exist"))]
    as_of = _date(doc.get("as_of")) or None
    return Expectations(str(path), as_of, nodes, edges, merges, nmm, mne)


def load_facts(manifests_dir: Path) -> dict[str, dict]:
    facts: dict[str, dict] = {}
    for f in sorted(Path(manifests_dir).glob("*.facts.yaml")) if Path(manifests_dir).is_dir() else []:
        try:
            data = yaml.safe_load(f.read_text(encoding="utf-8")) or []
        except yaml.YAMLError:
            continue
        for e in data if isinstance(data, list) else []:
            if isinstance(e, dict) and e.get("fact_id"):
                facts[str(e["fact_id"])] = e
    return facts


@dataclasses.dataclass
class Ctx:
    root: Path = ROOT
    index_dir: Path = DEFAULT_INDEX

    @property
    def corpus_dir(self) -> Path:
        return self.root / "corpus" / "upload"

    @property
    def code_dir(self) -> Path:
        return self.root / "build" / "code_repo"

    @property
    def manifests_dir(self) -> Path:
        return self.root / "manifests"


def corpus_files(ctx: Ctx) -> list[str]:
    if not ctx.corpus_dir.is_dir():
        return []
    return sorted(p.relative_to(ctx.root).as_posix() for p in ctx.corpus_dir.rglob("*")
                  if p.is_file() and not any(part.startswith(".") for part in p.relative_to(ctx.corpus_dir).parts))


def code_files(ctx: Ctx) -> list[str]:
    out = []
    for vdir in sorted(ctx.code_dir.glob("variant_*")) if ctx.code_dir.is_dir() else []:
        for p in sorted(vdir.rglob("*")):
            rel = p.relative_to(vdir).parts
            if p.is_file() and ".git" not in rel and not any(x.startswith(".") for x in rel):
                out.append(p.relative_to(ctx.root).as_posix())
    return out


FILE_ID_RE = re.compile(r"(?<![A-Za-z0-9])(LD|VS|ST|TX|GP|RJ)(\d{3})(?![0-9])", re.IGNORECASE)


class FileMatcher:
    """Maps the export's source-file strings onto corpus (and code repo) files."""

    def __init__(self, corpus: list[str], code: list[str]):
        self.corpus, self.code = corpus, code
        self.all = corpus + code
        self.code_set = set(code)
        self.by_rel = {p.lower(): p for p in self.all}
        self.by_base: dict[str, list] = collections.defaultdict(list)
        self.by_stem: dict[str, list] = collections.defaultdict(list)
        self.by_fid: dict[str, list] = collections.defaultdict(list)
        for p in self.all:
            base = p.rsplit("/", 1)[-1].lower()
            self.by_base[base].append(p)
            self.by_stem[base.split(".", 1)[0]].append(p)
            m = FILE_ID_RE.match(base)
            if m and p not in self.code_set:
                self.by_fid[(m.group(1) + m.group(2)).upper()].append(p)
        self.cache: dict[str, list] = {}

    def match(self, src: str) -> list[str]:
        if src in self.cache:
            return self.cache[src]
        low = str(src).replace("\\", "/").strip().lower()
        while low.startswith("./"):
            low = low[2:]
        res: list[str] = []
        if low in self.by_rel:
            res = [self.by_rel[low]]
        if not res and "/" in low:
            res = [p for p in self.all if low.endswith("/" + p.lower()) or p.lower().endswith("/" + low)]
        base = low.rsplit("/", 1)[-1]
        if not res:
            res = list(self.by_base.get(base, ()))
        if not res:
            for st in (base.split(".", 1)[0], base.rsplit(".", 1)[0]):
                if st in self.by_stem:
                    res = list(self.by_stem[st])
                    break
        if not res:
            m = FILE_ID_RE.search(base)
            if m:
                res = list(self.by_fid.get((m.group(1) + m.group(2)).upper(), ()))
        if not res:
            cands = [(len(st), p) for st, ps in self.by_stem.items() if len(st) >= 6 and st in base for p in ps]
            if cands:
                best = max(c[0] for c in cands)
                res = [p for ln, p in cands if ln == best]
        self.cache[src] = sorted(set(res))
        return self.cache[src]


class TextSearcher:
    """Does a string occur in any indexed corpus source text? (build_index.search, then a
    punctuation-insensitive pass over the same index)."""

    def __init__(self, index_dir: Path):
        self.index_dir = Path(index_dir)
        self.available, self.reason, self.n_files = False, "", 0
        self._B = None
        self._flat: list | None = None
        self.cache: dict[str, str | None] = {}
        if not (self.index_dir / "_state.json").exists():
            self.reason = f"no source-text index at {disp(self.index_dir)} (run harness/build_index.py)"
            return
        try:
            from harness import build_index as B
            files = B.indexed_files(self.index_dir)
        except Exception as exc:
            self.reason = f"source-text index unusable ({type(exc).__name__}: {exc})"
            return
        if not files:
            self.reason = f"source-text index at {disp(self.index_dir)} is empty"
            return
        self._B, self.available, self.n_files = B, True, len(files)

    def find(self, name: str) -> str | None:
        if not self.available:
            return None
        key = compact(name)
        if key in self.cache:
            return self.cache[key]
        res = None
        hits = self._B.search(str(name), index_dir=self.index_dir, max_hits=1)
        if hits:
            res = hits[0]["file"]
        else:
            n = norm_name(name)
            if n:
                if self._flat is None:
                    self._flat = [(L.rel, " " + _NON_ALNUM.sub(" ", _ascii_fold(L.norm).casefold()) + " ")
                                  for L in self._B.iter_loaded(self.index_dir)]
                pat = f" {n} "
                res = next((rel for rel, hay in self._flat if pat in hay), None)
        self.cache[key] = res
        return res


# ---------------------------------------------------------------------------------------------
# Audit
# ---------------------------------------------------------------------------------------------

ROLE_WORDS = frozenset("""manager director officer head lead leader team department dept operations committee board
unit office chief analyst owner squad desk function group division services service administrator admin coordinator
specialist handler assessor adjuster controller actuary architect engineer sponsor steward forum authority ceo cfo
coo cio cro cto siu finance claims compliance reserving recoveries payments support helpdesk""".split())


def disp(p: Any) -> str:
    """Repo-relative display path when under the repo."""
    if p in (None, ""):
        return ""
    try:
        return Path(str(p)).resolve().relative_to(ROOT).as_posix()
    except (ValueError, OSError):
        return str(p)


def severity(w: int) -> str:
    return "high" if w >= 70 else "medium" if w >= 45 else "low" if w >= 20 else "info"


def _pct(a: int, b: int) -> str:
    return f"{a / b:.0%}" if b else "n/a"


def _type_counts(v: Any) -> dict | None:
    """Declared node/edge types as {type: count-or-None}."""
    if v is None:
        return None
    out: dict[str, Any] = {}
    if isinstance(v, dict):
        for k, x in v.items():
            out[str(k)] = x if isinstance(x, int) and not isinstance(x, bool) else (
                x.get("count") if isinstance(x, dict) and isinstance(x.get("count"), int) else None)
    elif isinstance(v, list):
        for x in v:
            if isinstance(x, str):
                out[x] = None
            elif isinstance(x, dict):
                nm = x.get("name") or x.get("label") or x.get("type") or x.get("id")
                if nm:
                    out[str(nm)] = x.get("count") if isinstance(x.get("count"), int) else None
    return out


class Audit:
    def __init__(self, graph: Graph, world: World | None, expect: Expectations | None, ctx: Ctx, label: str,
                 world_notes: list[str] = (), text: TextSearcher | None = None):
        self.g, self.w, self.x, self.ctx, self.label = graph, world, expect, ctx, label
        self.findings: list[dict] = []
        self.notes: list[str] = list(world_notes)
        self.res: dict[str, Any] = {}
        self.facts = load_facts(ctx.manifests_dir)
        self.text = text if text is not None else TextSearcher(ctx.index_dir)
        if expect:
            graph.pool = _label_pool(list(graph.pool) + expect.types())

    def add(self, weight: int, check: str, text: str) -> None:
        self.findings.append({"weight": weight, "severity": severity(weight), "check": check, "text": text})

    def node_desc(self, k: str) -> str:
        n = self.g.nodes[k]
        return f"{n.label} '{n.name}'"

    def fact_files(self, fids: Iterable[str]) -> list[str]:
        out = []
        for f in fids:
            fact = self.facts.get(str(f))
            out.append(f"{f} ({fact.get('file')})" if fact else f"{f} (not in manifests)")
        return out

    # --- run ---------------------------------------------------------------------------------
    def run(self) -> dict:
        g = self.g
        self.res["meta"] = {
            "label": self.label, "input": disp(g.src), "shape": g.shape, "context_id": g.context_id,
            "world": self.w.source if self.w else None, "world_as_of": self.w.as_of if self.w else None,
            "expectations": disp(self.x.path) if self.x else None,
            "source_text_index": (f"{disp(self.text.index_dir)} ({self.text.n_files} files)" if self.text.available
                                  else f"unavailable: {self.text.reason}"),
        }
        self.totals()
        self.check_duplicates()
        self.check_unmerged()
        self.check_wrong_merges()
        self.check_missing()
        self.check_hallucinated()
        self.check_coverage()
        self.roles_as_people()
        self.generic_ratio()
        self.property_coverage()
        self.res["top_findings"] = self.top_findings()
        self.res["findings"] = self.findings
        self.res["notes"] = self.notes
        return self.res

    def top_findings(self) -> list[dict]:
        by_check: dict[str, list] = collections.defaultdict(list)
        for i, f in enumerate(self.findings):
            by_check[f["check"]].append((i, f))
        picked = []
        for check, items in by_check.items():
            items.sort(key=lambda t: (-t[1]["weight"], t[0]))
            picked += items[:3]
            if len(items) > 3:
                rest = items[3:]
                eg = "; ".join(f["text"][:70] for _, f in rest[:2])
                picked.append((rest[0][0], {"weight": rest[0][1]["weight"], "severity": rest[0][1]["severity"],
                                            "check": check,
                                            "text": f"+{len(rest)} more {check} findings (e.g. {eg}) - see details"}))
        picked.sort(key=lambda t: (-t[1]["weight"], t[0]))
        return [f for _, f in picked[:TOP_N]]

    # --- totals ------------------------------------------------------------------------------
    def totals(self) -> None:
        g = self.g
        inst = collections.Counter(n.label for n in g.instance_nodes)
        sch = collections.Counter(schema_type(n.label) for n in g.schema_nodes)
        core = collections.Counter(e.core for e in g.inst_edges)
        raw_by_core: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
        for e in g.inst_edges:
            raw_by_core[e.core][e.type] += 1
        schema_edges = [e for e in g.edges if e.schema]
        node_is = sum(1 for e in schema_edges if snake_upper(e.type) == "NODE_IS")
        schema_rel = sum(1 for e in schema_edges if snake_upper(e.type).startswith("SCHEMA_REL"))
        dangling = [e for e in g.edges if e.dangling]
        typed = {e.start for e in g.edges if snake_upper(e.type) == "NODE_IS"}
        untyped = sum(1 for n in g.instance_nodes if n.key not in typed) if node_is else None
        sources = collections.Counter(str(e.props.get("source")) for e in g.inst_edges if "source" in e.props)
        n_all, n_inst, e_all, e_inst = len(g.nodes), len(g.instance_nodes), len(g.edges), len(g.inst_edges)

        rows = []
        for k, v in sorted(g.stated.items()):
            kl = k.lower()
            if "node" in kl and "type" not in kl:
                rec, note = n_all, f"{n_inst} instance + {len(g.schema_nodes)} schema"
                ok = v in (n_all, n_inst)
                if v == n_inst and v != n_all:
                    note += "; stated value equals the instance-only count"
            elif "dangling" in kl:
                rec, note = len(dangling), "recomputed = dangling relationships still present in the export"
                ok = len(dangling) == 0
            elif ("relationship" in kl or "edge" in kl) and "type" not in kl:
                rec, note = e_all, f"{e_inst} instance + {len(schema_edges)} schema-level + {len(dangling)} dangling"
                ok = v in (e_all, e_all - len(dangling), e_inst)
                if v != e_all and ok:
                    note += "; stated value matches a subset count"
            else:
                rows.append({"field": k, "stated": v, "recomputed": None, "status": "not recomputed", "note": ""})
                continue
            status = "OK" if ok else "MISMATCH"
            rows.append({"field": k, "stated": v, "recomputed": rec, "status": status, "note": note})
            if not ok:
                self.add(60, "totals", f"export states {k}={v} but the recomputed count is {rec} ({note})")
        type_rows = []
        for fld, declared, observed in (("node_types", _type_counts(g.declared_node_types), dict(inst)),
                                        ("edge_types", _type_counts(g.declared_edge_types),
                                         dict(collections.Counter(e.type for e in g.edges)))):
            if declared is None:
                continue
            dc = {canon_type(k): (k, v) for k, v in declared.items()}
            oc = {canon_type(k): (k, v) for k, v in observed.items()}
            if fld == "node_types":
                for n in g.schema_nodes:
                    oc.setdefault(canon_type(schema_type(n.label)), (schema_type(n.label), 0))
            unused = sorted(dc[c][0] for c in dc if c not in oc or (fld == "node_types" and oc[c][1] == 0))
            undeclared = sorted(oc[c][0] for c in oc if c not in dc and oc[c][1])
            mism = [(dc[c][0], dc[c][1], oc[c][1]) for c in dc if dc[c][1] is not None and c in oc and dc[c][1] != oc[c][1]]
            type_rows.append({"field": fld, "declared": len(declared), "observed": len([c for c in oc if oc[c][1]]),
                              "declared_unused": unused, "used_undeclared": undeclared,
                              "count_mismatches": [{"type": t, "stated": s, "recomputed": r} for t, s, r in mism]})
            for t, s, r in mism:
                self.add(60, "totals", f"export states {fld}[{t}]={s} but {r} were found")
            if undeclared:
                self.add(30, "totals", f"{len(undeclared)} {fld[:-1].replace('_', ' ')}s used but not declared in "
                                       f"{fld}: {', '.join(undeclared[:5])}")
        if g.duplicate_keys:
            self.add(50, "totals", f"{g.duplicate_keys} node keys occur more than once in the export")
        if dangling:
            dt = collections.Counter(e.type for e in dangling)
            self.add(55, "totals", f"{len(dangling)} dangling relationships still present "
                                   f"(e.g. {', '.join(f'{t} x{c}' for t, c in dt.most_common(3))})")
        if untyped:
            self.add(25, "totals", f"{untyped} of {n_inst} instance nodes have no NODE_IS link to a schema node")
        self.res["totals"] = {
            "stated_vs_recomputed": rows, "declared_types": type_rows,
            "nodes_total": n_all, "instance_nodes": n_inst, "schema_nodes": len(g.schema_nodes),
            "instance_nodes_by_type": dict(inst.most_common()), "schema_nodes_by_type": dict(sch.most_common()),
            "edges_total": e_all, "instance_edges": e_inst,
            "instance_edges_by_core_type": dict(core.most_common()),
            "raw_types_by_core": {k: dict(v.most_common()) for k, v in raw_by_core.items()},
            "schema_edges": {"total": len(schema_edges), "NODE_IS": node_is, "SCHEMA_REL_*": schema_rel,
                             "other_touching_schema_nodes": len(schema_edges) - node_is - schema_rel},
            "dangling_edges": len(dangling),
            "dangling_by_type": dict(collections.Counter(e.type for e in dangling).most_common()),
            "duplicate_keys": g.duplicate_keys, "instance_nodes_without_NODE_IS": untyped,
            "instance_edges_by_source_property": dict(sources.most_common()),
        }

    # --- check 1 -----------------------------------------------------------------------------
    def _renamed_link(self, keys: list[str]) -> bool:
        ks = set(keys)
        return any(e.start in ks and e.end in ks and (e.forms & RENAME_CANON) for e in self.g.inst_edges
                   if e.start in ks or e.end in ks)

    def check_duplicates(self) -> None:
        g, w = self.g, self.w
        allowed: dict[tuple, int] = {}
        for m in (self.x.must_not_merge if self.x else []):
            for nm in m["names"]:
                allowed[(canon_type(m.get("type")), compact(nm))] = max(2, len(m["distinct"]))
        homonym: dict[str, int] = {}
        if w:
            people = set(w.people)
            for c, refs in w.ident.items():
                pr = refs & people
                if len(pr) > 1:
                    homonym[c] = len(pr)
        groups: dict[tuple, list] = collections.defaultdict(list)
        for n in g.instance_nodes:
            if n.compact:
                groups[(canon_type(n.label), n.compact)].append(n.key)
        same = []
        for (ct, c), keys in sorted(groups.items()):
            if len(keys) < 2:
                continue
            ok = allowed.get((ct, c), 1)
            for (at, ac), v in allowed.items():
                if ac == c and type_matches(g.nodes[keys[0]].label, at):
                    ok = max(ok, v)
            if type_matches(g.nodes[keys[0]].label, "Person"):
                ok = max(ok, homonym.get(c, 1))
            if len(keys) > ok:
                n0 = g.nodes[keys[0]]
                files = sorted({f for k in keys for f in g.nodes[k].files})
                same.append({"type": n0.label, "name": n0.name, "count": len(keys), "allowed": ok, "keys": keys,
                             "files": files})
                self.add(50 + min(len(keys) - 1, 10) * 2, "1 duplicates",
                         f"{len(keys)} {n0.label} nodes named '{n0.name}'" + (f" (expected at most {ok})" if ok > 1 else ""))
        alias = []
        if w:
            by: dict[tuple, list] = collections.defaultdict(list)
            for n in g.instance_nodes:
                refs = w.identity_refs(n.name)
                if len(refs) == 1:
                    by[(canon_type(n.label), next(iter(refs)))].append(n.key)
            for (ct, ref), keys in sorted(by.items()):
                names = sorted({g.nodes[k].name for k in keys}, key=str.lower)
                if len({g.nodes[k].compact for k in keys}) < 2:
                    continue
                linked = self._renamed_link(keys)
                alias.append({"type": g.nodes[keys[0]].label, "world_ref": ref, "names": names, "keys": keys,
                              "linked_by_renamed_to": linked})
                self.add(35 if linked else 50, "1 duplicates",
                         f"{g.nodes[keys[0]].label} nodes {', '.join(repr(x) for x in names)} are one world entity "
                         f"({ref})" + (" - linked by RENAMED_TO" if linked else ""))
        else:
            self.notes.append("check 1: alias duplicates need the world model; only same-name duplicates were checked")
        self.res["duplicates"] = {"same_name": same, "same_world_entity": alias}

    # --- check 2 -----------------------------------------------------------------------------
    def check_unmerged(self) -> None:
        out = []
        if not self.x:
            self.res["unmerged_aliases"] = None
            return
        for m in self.x.merge_expected:
            keys = self.g.find(m.get("type"), m["names"])
            status = "unmerged" if len(keys) > 1 else "merged" if keys else "absent"
            item = {"id": m["id"], "type": m.get("type"), "canonical": m.get("canonical"), "status": status,
                    "nodes_found": [self.g.nodes[k].name for k in keys], "keys": keys,
                    "linked_by_renamed_to": self._renamed_link(keys) if len(keys) > 1 else False}
            out.append(item)
            if status == "unmerged":
                self.add(55 if item["linked_by_renamed_to"] else 65, "2 unmerged aliases",
                         f"{m['id']}: '{m.get('canonical')}' appears as {len(keys)} {m.get('type')} nodes: "
                         f"{', '.join(repr(x) for x in item['nodes_found'])}"
                         + (" (linked by RENAMED_TO)" if item["linked_by_renamed_to"] else ""))
        self.res["unmerged_aliases"] = out

    # --- check 3 -----------------------------------------------------------------------------
    def check_wrong_merges(self) -> None:
        if not self.x:
            self.res["wrong_merges"] = None
            return
        out = []
        for m in self.x.must_not_merge:
            keys = self.g.find(m.get("type"), m["names"])
            want = max(2, len(m["distinct"]))
            status = "collapsed" if 0 < len(keys) < want else "absent" if not keys else "kept apart"
            hints = []
            if status == "collapsed":
                for k in keys:
                    blob = norm_name(json.dumps(self.g.nodes[k].attrs, ensure_ascii=False, default=str))
                    for d in m["distinguishing"]:
                        for part in str(d).split(","):
                            p = norm_name(part)
                            if p and f" {p} " in f" {blob} " and part.strip() not in hints:
                                hints.append(part.strip())
            out.append({"id": m["id"], "type": m.get("type"), "name": (m["names"] or [""])[0], "distinct": m["distinct"],
                        "nodes_found": len(keys), "expected_nodes": want, "status": status,
                        "distinguishing_hints_in_merged_node": hints, "keys": keys})
            if status == "collapsed":
                self.add(90, "3 wrong merges",
                         f"{m['id']}: {want} distinct {m.get('type')} entities named '{(m['names'] or [''])[0]}' "
                         f"({', '.join(map(str, m['distinct']))}) collapsed into {len(keys)} node(s)"
                         + (f"; merged node mentions {', '.join(hints)}" if hints else ""))
        self.res["wrong_merges"] = out

    # --- check 4 -----------------------------------------------------------------------------
    def check_missing(self) -> None:
        if not self.x:
            self.res["missing"] = None
            self.notes.append("checks 2-4 and must_not_exist skipped: no expectations file")
            return
        g = self.g
        nodes_out, edges_out = [], []
        weights = {"high": 85, "medium": 50, "low": 30}
        for x in self.x.nodes:
            keys = g.find(x.get("type"), x["names"])
            item = {"id": x["id"], "type": x.get("type"), "name": (x["names"] or [""])[0],
                    "importance": x["importance"], "world_ref": x.get("world_ref")}
            if keys:
                item.update(status="present", keys=keys)
            else:
                other = g.find(None, x["names"])
                ev = self.fact_files(x["evidence"])
                if other:
                    labels = sorted({g.nodes[k].label for k in other})
                    item.update(status="present under another type", found_as=labels, evidence=ev)
                    self.add(45, "4 missing nodes", f"{x['id']}: {x.get('type')} '{item['name']}' exists only as "
                                                    f"{'/'.join(labels)}")
                else:
                    near = []
                    if x["names"]:
                        pool = sorted({n.norm for n in g.instance_nodes if type_matches(n.label, x.get("type"))})
                        near = difflib.get_close_matches(norm_name(x["names"][0]), pool, n=3, cutoff=0.8)
                    item.update(status="missing", evidence=ev, near_misses=near)
                    self.add(weights.get(str(x["importance"]), 50), "4 missing nodes",
                             f"{x['id']}: {x['importance']}-importance {x.get('type')} '{item['name']}' is missing"
                             + (f"; evidence {', '.join(ev[:3])}" if ev else ""))
            nodes_out.append(item)
        for x in self.x.edges:
            fk = g.find(x["from"]["type"], x["from"]["names"])
            tk = g.find(x["to"]["type"], x["to"]["names"])
            forms = rel_forms(str(x.get("type", "")), x["from"]["type"], x["to"]["type"], g.pool)
            desc = (f"{x['id']}: {(x['from']['names'] or ['?'])[0]} -[{x.get('type')}]-> "
                    f"{(x['to']['names'] or ['?'])[0]}")
            item = {"id": x["id"], "type": x.get("type"), "from": (x["from"]["names"] or [""])[0],
                    "to": (x["to"]["names"] or [""])[0], "as_of": _date(x.get("as_of")) or None}
            ev = self.fact_files(x["evidence"])
            if fk and tk and set(fk) & set(tk) and forms & RENAME_CANON:
                item.update(status="satisfied by merge")
            elif not fk or not tk:
                miss = [s for s, k in (("from", fk), ("to", tk)) if not k]
                item.update(status=f"missing (endpoint absent: {'/'.join(miss)})", evidence=ev)
                self.add(40, "4 missing edges", f"{desc} missing; {'/'.join(miss)} endpoint absent")
            elif any(e.forms & forms for e in g.edges_between(fk, tk)):
                item.update(status="present")
            elif any(e.forms & forms for e in g.edges_between(tk, fk)):
                item.update(status="reversed", evidence=ev)
                self.add(45, "4 missing edges", f"{desc} exists only in the reverse direction")
            else:
                other = sorted({e.core for e in g.edges_between(fk, tk) + g.edges_between(tk, fk)})
                item.update(status="missing (both endpoints present)", linked_instead_by=other, evidence=ev)
                self.add(70, "4 missing edges", f"{desc} missing although both endpoints exist"
                         + (f"; linked by {', '.join(other)} instead" if other else "")
                         + (f"; evidence {', '.join(ev[:2])}" if ev else ""))
            edges_out.append(item)
        self.res["missing"] = {"nodes": nodes_out, "edges": edges_out}

    # --- check 5 -----------------------------------------------------------------------------
    def check_hallucinated(self) -> None:
        g, w = self.g, self.w
        forbidden = []
        for x in (self.x.must_not_exist if self.x else []):
            keys = g.find(x.get("type"), x["names"])
            if keys:
                forbidden.append({"id": x["id"], "type": x.get("type"), "name": (x["names"] or [""])[0],
                                  "reason": x.get("reason"), "keys": keys,
                                  "files": sorted({f for k in keys for f in g.nodes[k].files})})
                self.add(80, "5 hallucinated", f"{x['id']}: forbidden {x.get('type')} node '{(x['names'] or [''])[0]}' "
                                               f"exists ({x.get('reason') or 'must_not_exist'})")
        seen: dict[str, dict] = {}
        untraceable, traced_text, lex_only = [], 0, 0
        for n in g.instance_nodes:
            if not n.compact:
                continue
            if n.compact not in seen:
                lex = w.trace(n.name) if w else None
                hit = None if lex else self.text.find(n.name)
                seen[n.compact] = {"lex": lex, "text": hit}
            r = seen[n.compact]
            if r["lex"]:
                continue
            if r["text"]:
                traced_text += 1
                continue
            untraceable.append({"type": n.label, "name": n.name, "key": n.key, "files": n.files})
        verified = self.text.available
        for u in untraceable:
            self.add(40 if verified else 25, "5 hallucinated",
                     f"{u['type']} '{u['name']}' traces to no world name/alias/ID/term"
                     + (" and occurs in no source text" if verified else " (source text not checked)"))
        if not verified:
            self.notes.append(f"check 5: source-text half skipped - {self.text.reason}; 'untraceable' means "
                              "lexicon-untraceable only")
        if not w:
            self.notes.append("check 5: no world model, so the lexicon half could not run")
        self.res["hallucinated"] = {
            "must_not_exist_hits": forbidden, "untraceable": untraceable, "text_checked": verified,
            "traced_by_text_only": traced_text,
            "lexicon_traced": sum(1 for n in g.instance_nodes if n.compact and seen.get(n.compact, {}).get("lex")),
            "method_counts": dict(collections.Counter((r["lex"][0].split(" ")[0] if r["lex"] else ("text" if r["text"] else "none"))
                                                      for r in seen.values())),
        }

    # --- check 6 -----------------------------------------------------------------------------
    def check_coverage(self) -> None:
        g, w = self.g, self.w
        cfiles, kfiles = corpus_files(self.ctx), code_files(self.ctx)
        fm = FileMatcher(cfiles, kfiles)
        node_files: dict[str, set] = collections.defaultdict(set)
        unmatched: collections.Counter = collections.Counter()
        file_nodes: dict[str, set] = collections.defaultdict(set)
        for n in g.instance_nodes:
            for src in n.files:
                m = fm.match(src)
                if not m:
                    unmatched[src] += 1
                for f in m:
                    node_files[n.key].add(f)
                    file_nodes[f].add(n.key)
        file_edges: collections.Counter = collections.Counter()
        unattributed = 0
        for e in g.inst_edges:
            fs = {f for src in e.files for f in fm.match(src)}
            if not fs:
                unattributed += 1
            for f in fs:
                file_edges[f] += 1
        code_in_export = any(f in fm.code_set for f in file_nodes)
        listed = cfiles + (kfiles if code_in_export else [])
        zero = [f for f in listed if not file_nodes.get(f)]
        facts_by_file: dict[str, list] = collections.defaultdict(list)
        for fact in self.facts.values():
            if fact.get("file"):
                facts_by_file[str(fact["file"])].append(fact)
        all_compacts = {n.compact for n in g.instance_nodes}
        rows = []
        for f in sorted(set(listed) | set(facts_by_file)):
            fl = facts_by_file.get(f, [])
            with_ref = present = present_here = 0
            here = {g.nodes[k].compact for k in file_nodes.get(f, ())}
            for fact in fl:
                if not fact.get("world_ref"):
                    continue
                with_ref += 1
                ref = w.resolve_ref(fact["world_ref"])[0] if w else None
                names = w.names_for_ref(ref) if (w and ref) else [str(fact["world_ref"]).split("@")[0]]
                cs = {compact(x) for x in names} - {""}
                present += bool(cs & all_compacts)
                present_here += bool(cs & here)
            rows.append({"file": f, "nodes": len(file_nodes.get(f, ())), "edges": file_edges.get(f, 0),
                         "facts": len(fl), "facts_with_world_ref": with_ref, "entity_present_in_graph": present,
                         "entity_present_in_nodes_from_file": present_here})
        if zero:
            self.add(75 if len(zero) >= max(1, len(listed) // 10) else 50, "6 coverage",
                     f"{len(zero)} of {len(listed)} corpus files have zero nodes (e.g. {', '.join(zero[:3])})")
        if unmatched:
            self.add(30, "6 coverage", f"{len(unmatched)} source-file names in the export match no corpus file "
                                       f"(e.g. {', '.join(sorted(unmatched)[:3])})")
        low = [r for r in rows if r["facts_with_world_ref"] >= 3 and r["entity_present_in_graph"] / r["facts_with_world_ref"] < 0.5]
        for r in sorted(low, key=lambda r: r["entity_present_in_graph"] / r["facts_with_world_ref"])[:10]:
            self.add(35, "6 coverage", f"{r['file']}: only {r['entity_present_in_graph']} of {r['facts_with_world_ref']} "
                                       "planted facts have their world entity as a node (fuzzy proxy)")
        if not cfiles:
            self.notes.append(f"check 6: {disp(self.ctx.corpus_dir)} holds no files, so zero-node files cannot be listed")
        self.res["coverage"] = {
            "method": "Node files come from each node's source_file/source_files/property_history; edge files from the "
                      "edge's own source file, else the files both endpoints share. 'Entity present' is a fuzzy proxy "
                      "for extraction coverage: a planted fact counts when any node's normalised name equals a "
                      "name/alias/ID of the fact's world_ref entity.",
            "corpus_files": len(cfiles), "code_files_listed": code_in_export, "zero_node_files": zero,
            "export_files_not_in_corpus": dict(unmatched.most_common()), "unattributed_edges": unattributed,
            "files": rows,
        }

    # --- extras --------------------------------------------------------------------------------
    def roles_as_people(self) -> None:
        g, w = self.g, self.w
        terms: dict[str, tuple[str, str]] = {}
        person_names: set = set()
        if w:
            for pid, p in w.people.items():
                for t in titles_of(p):
                    for v in {t, re.split(r"\s+[-\u2013\u2014]\s+|,|\s\(", t)[0]}:
                        terms.setdefault(compact(v), (t, "job title"))
                for a, _cur in role_aliases_of(p):
                    terms.setdefault(compact(a), (a, "role alias"))
                for nm in w.names_for_ref(pid):
                    person_names.add(compact(nm))
                person_names.add(compact(rec_name(p, pid)))
            for nm, kind, _ref in w.org_units():
                terms.setdefault(compact(nm), (nm, kind))
            terms.pop("", None)
        out = []
        for n in g.instance_nodes:
            if not type_matches(n.label, "Person") or not n.compact:
                continue
            if n.compact in terms and n.compact not in person_names:
                t, kind = terms[n.compact]
                out.append({"name": n.name, "matched": t, "kind": kind, "basis": "world", "key": n.key, "files": n.files})
                self.add(70, "roles-as-people", f"Person node '{n.name}' is a {kind} in the world ('{t}')")
            elif n.compact not in person_names and (set(n.norm.split()) & ROLE_WORDS):
                out.append({"name": n.name, "matched": None, "kind": "role-like words", "basis": "heuristic",
                            "key": n.key, "files": n.files})
                self.add(35, "roles-as-people", f"Person node '{n.name}' looks like a role or unit (heuristic: "
                                                "not a world person name, contains role/unit words)")
        if not w:
            self.notes.append("roles-as-people: no world model, heuristic matches only")
        self.res["roles_as_people"] = out

    def generic_ratio(self) -> None:
        g = self.g
        n = len(g.inst_edges)
        gen = [e for e in g.inst_edges if canon_rel(e.core) in GENERIC_CANON]
        by = collections.Counter(e.core for e in gen)
        pairs = collections.Counter((g.nodes[e.start].label, e.core, g.nodes[e.end].label) for e in gen)
        spec = collections.Counter(e.core for e in g.inst_edges if canon_rel(e.core) not in GENERIC_CANON)
        schema_rel: dict[str, str] = {}
        for e in g.edges:
            if snake_upper(e.type).startswith("SCHEMA_REL"):
                s, t = g.nodes.get(e.start), g.nodes.get(e.end)
                core_s = core_relation(e.type, schema_type(s.label) if s else None, schema_type(t.label) if t else None, g.pool)
                schema_rel.setdefault(canon_rel(core_s), core_s)
        inst_canon = {canon_rel(e.core) for e in g.inst_edges}
        ratio = len(gen) / n if n else 0.0
        self.res["generic_relationships"] = {
            "generic_types": list(GENERIC_RELATIONS), "instance_edges": n, "generic_edges": len(gen),
            "generic_ratio": round(ratio, 4), "generic_by_type": dict(by.most_common()),
            "top_generic_patterns": [{"start": a, "core": c, "end": b, "count": k} for (a, c, b), k in pairs.most_common(15)],
            "specific_by_type": dict(spec.most_common()),
            "specific_types_matching_schema_level_relations": sorted(t for t in spec if canon_rel(t) in schema_rel),
            "schema_level_relations_without_instances": sorted(v for c, v in schema_rel.items() if c not in inst_canon),
        }
        if n:
            self.add(70 if ratio >= 0.5 else 50 if ratio >= 0.3 else 30 if ratio >= 0.15 else 10, "generic relations",
                     f"{len(gen)} of {n} instance edges ({ratio:.0%}) use a generic relation"
                     + (f" (top: {', '.join(f'{t} x{c}' for t, c in by.most_common(3))})" if gen else ""))

    def property_coverage(self) -> None:
        g = self.g
        by_type: dict[str, list[Node]] = collections.defaultdict(list)
        for n in g.instance_nodes:
            by_type[n.label].append(n)
        out = {}
        bare = []
        for t, ns in sorted(by_type.items(), key=lambda kv: (-len(kv[1]), kv[0])):
            cnt: collections.Counter = collections.Counter()
            for n in ns:
                for k, v in n.attrs.items():
                    if v not in (None, "", [], {}):
                        cnt[k] += 1
            props = sorted(cnt.items(), key=lambda kv: (-kv[1], kv[0]))
            out[t] = {"nodes": len(ns), "properties": {k: round(c / len(ns), 4) for k, c in props}}
            rich = [k for k, c in props if k not in NAME_KEYS and c / len(ns) >= 0.5]
            if len(ns) >= 3 and not rich:
                bare.append(f"{t} (n={len(ns)})")
        if bare:
            self.add(25, "property coverage", f"{len(bare)} types carry no attribute beyond a name on most nodes: "
                                              f"{', '.join(bare[:6])}")
        self.res["property_coverage"] = out


# ---------------------------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------------------------

def _cell(v: Any) -> str:
    if isinstance(v, (list, tuple, set)):
        v = ", ".join(str(x) for x in v)
    return str(v if v is not None else "").replace("|", "\\|").replace("\n", " ")


def md_table(headers: list[str], rows: list[list], limit: int | None = None) -> str:
    if not rows:
        return "_none_"
    out = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    shown = rows if limit is None else rows[:limit]
    out += ["| " + " | ".join(_cell(c) for c in r) + " |" for r in shown]
    if limit is not None and len(rows) > limit:
        out.append(f"\n_{len(rows) - limit} more rows in the JSON twin._")
    return "\n".join(out)


def render_audit_md(r: dict) -> str:
    m, t = r["meta"], r["totals"]
    L = [f"# Knowledge-graph audit: {m['label']}", "",
         f"- Input: `{m['input']}`", f"- Detected export shape: {m['shape']}",
         f"- Context id: {m['context_id']}" if m.get("context_id") else "- Context id: n/a",
         f"- World model: {m['world'] or 'not available'}" + (f" (as of {m['world_as_of']})" if m.get("world_as_of") else ""),
         f"- Expectations: {m['expectations'] or 'none'}", f"- Source-text index: {m['source_text_index']}", "",
         f"## Top {TOP_N} findings", ""]
    L.append(md_table(["#", "severity", "check", "finding"],
                      [[i, f["severity"], f["check"], f["text"]] for i, f in enumerate(r["top_findings"], 1)]))
    L += ["", "## 1. Totals", "", "### Counts the export states vs recomputed", ""]
    L.append(md_table(["field", "stated", "recomputed", "status", "note"],
                      [[x["field"], x["stated"], x["recomputed"], x["status"], x["note"]] for x in t["stated_vs_recomputed"]]))
    for d in t["declared_types"]:
        cm = ["%s %s/%s" % (c["type"], c["stated"], c["recomputed"]) for c in d["count_mismatches"]]
        L += ["", f"- `{d['field']}`: {d['declared']} declared, {d['observed']} observed; declared but unused: "
                  f"{_cell(d['declared_unused']) or 'none'}; used but undeclared: {_cell(d['used_undeclared']) or 'none'}; "
                  f"count mismatches (stated/recomputed): {_cell(cm) or 'none'}"]
    L += ["", f"Nodes: {t['nodes_total']} total = {t['instance_nodes']} instance + {t['schema_nodes']} schema. "
              f"Edges: {t['edges_total']} total = {t['instance_edges']} instance + {t['schema_edges']['total']} schema-level "
              f"(NODE_IS {t['schema_edges']['NODE_IS']}, SCHEMA_REL_* {t['schema_edges']['SCHEMA_REL_*']}, other "
              f"{t['schema_edges']['other_touching_schema_nodes']}) + {t['dangling_edges']} dangling. Duplicate node keys: "
              f"{t['duplicate_keys']}. Instance nodes without NODE_IS: {t['instance_nodes_without_NODE_IS']}.", "",
          "### Instance nodes by type", ""]
    L.append(md_table(["type", "nodes"], [[k, v] for k, v in t["instance_nodes_by_type"].items()]))
    L += ["", "### Instance edges by core type", ""]
    L.append(md_table(["core type", "edges", "raw types"],
                      [[k, v, ", ".join(f"{rt} x{c}" for rt, c in t["raw_types_by_core"].get(k, {}).items())]
                       for k, v in t["instance_edges_by_core_type"].items()]))
    L += ["", "### Schema nodes by type", ""]
    L.append(md_table(["schema type", "nodes"], [[k, v] for k, v in t["schema_nodes_by_type"].items()]))
    if t["dangling_by_type"]:
        L += ["", "Dangling relationships by type: " + ", ".join(f"{k} x{v}" for k, v in t["dangling_by_type"].items())]
    if t["instance_edges_by_source_property"]:
        L += ["", "Instance edges by `source` property: " +
              ", ".join(f"{k} x{v}" for k, v in t["instance_edges_by_source_property"].items())]

    d = r["duplicates"]
    L += ["", "## 2. Duplicates (check 1)", "", "### Same type, same normalised name", ""]
    L.append(md_table(["type", "name", "nodes", "allowed", "files"],
                      [[x["type"], x["name"], x["count"], x["allowed"], x["files"][:6]] for x in d["same_name"]], 200))
    L += ["", "### Same world entity under different names (lexicon)", ""]
    L.append(md_table(["type", "world ref", "names", "linked by RENAMED_TO"],
                      [[x["type"], x["world_ref"], x["names"], "yes" if x["linked_by_renamed_to"] else "no"]
                       for x in d["same_world_entity"]], 200))

    L += ["", "## 3. Unmerged aliases (check 2)", ""]
    if r["unmerged_aliases"] is None:
        L.append("_skipped: no expectations file_")
    else:
        ua = r["unmerged_aliases"]
        L.append(f"{sum(1 for x in ua if x['status'] == 'unmerged')} unmerged, {sum(1 for x in ua if x['status'] == 'merged')} "
                 f"merged, {sum(1 for x in ua if x['status'] == 'absent')} absent of {len(ua)} groups.\n")
        L.append(md_table(["id", "type", "canonical", "status", "nodes found", "RENAMED_TO link"],
                          [[x["id"], x["type"], x["canonical"], x["status"], x["nodes_found"],
                            "yes" if x["linked_by_renamed_to"] else ""] for x in ua if x["status"] != "merged"], 300))

    L += ["", "## 4. Wrong merges (check 3)", ""]
    if r["wrong_merges"] is None:
        L.append("_skipped: no expectations file_")
    else:
        L.append(md_table(["id", "type", "name", "distinct", "nodes found", "status", "hints in merged node"],
                          [[x["id"], x["type"], x["name"], x["distinct"], f"{x['nodes_found']}/{x['expected_nodes']}",
                            x["status"], x["distinguishing_hints_in_merged_node"]] for x in r["wrong_merges"]]))

    L += ["", "## 5. Missing nodes and edges (check 4)", ""]
    if r["missing"] is None:
        L.append("_skipped: no expectations file_")
    else:
        mn, me = r["missing"]["nodes"], r["missing"]["edges"]
        L.append(f"Nodes: {sum(1 for x in mn if x['status'] == 'present')} of {len(mn)} present. "
                 f"Edges: {sum(1 for x in me if x['status'] in ('present', 'satisfied by merge'))} of {len(me)} present.\n")
        L.append("### Nodes not found\n")
        L.append(md_table(["id", "importance", "type", "name", "status", "evidence", "near misses"],
                          [[x["id"], x["importance"], x["type"], x["name"], x["status"] + (f" ({_cell(x['found_as'])})" if x.get("found_as") else ""),
                            x.get("evidence", [])[:4], x.get("near_misses", [])]
                           for x in sorted(mn, key=lambda x: ({"high": 0, "medium": 1}.get(str(x["importance"]), 2), x["id"]))
                           if x["status"] != "present"], 300))
        L.append("\n### Edges not found\n")
        L.append(md_table(["id", "type", "from", "to", "status", "linked instead by", "evidence"],
                          [[x["id"], x["type"], x["from"], x["to"], x["status"], x.get("linked_instead_by", []),
                            x.get("evidence", [])[:3]] for x in me if x["status"] not in ("present", "satisfied by merge")], 300))

    h = r["hallucinated"]
    L += ["", "## 6. Hallucinated and forbidden nodes (check 5)", "",
          f"Lexicon-traced nodes: {h['lexicon_traced']}; traced by source text only: {h['traced_by_text_only']}; "
          f"untraceable: {len(h['untraceable'])}"
          + ("" if h["text_checked"] else " (source text NOT checked: lexicon-untraceable candidates only)") + ".", "",
          "### must_not_exist hits", ""]
    L.append(md_table(["id", "type", "name", "reason", "files"],
                      [[x["id"], x["type"], x["name"], x["reason"], x["files"][:5]] for x in h["must_not_exist_hits"]]))
    L += ["", "### Untraceable nodes", ""]
    L.append(md_table(["type", "name", "files"], [[x["type"], x["name"], x["files"][:4]] for x in h["untraceable"]], 300))

    c = r["coverage"]
    L += ["", "## 7. Per-file coverage (check 6)", "", c["method"], "",
          f"Corpus files: {c['corpus_files']}; zero-node files: {len(c['zero_node_files'])}; edges with no attributable "
          f"file: {c['unattributed_edges']}; code repo files listed: {'yes' if c['code_files_listed'] else 'no (export has none)'}.",
          "", "### Files with zero nodes", ""]
    L.append("\n".join(f"- `{f}`" for f in c["zero_node_files"]) or "_none_")
    if c["export_files_not_in_corpus"]:
        L += ["", "### Export source files not matched to the corpus", ""]
        L.append(md_table(["export source file", "nodes"], [[k, v] for k, v in c["export_files_not_in_corpus"].items()], 100))
    L += ["", "### Per file (entity-present columns are a fuzzy proxy)", ""]
    L.append(md_table(["file", "nodes", "edges", "facts", "facts w/ world_ref", "entity in graph", "entity in nodes from file"],
                      [[x["file"], x["nodes"], x["edges"], x["facts"], x["facts_with_world_ref"], x["entity_present_in_graph"],
                        x["entity_present_in_nodes_from_file"]] for x in c["files"]]))

    L += ["", "## 8. Roles extracted as people", ""]
    L.append(md_table(["Person node", "matched world term", "kind", "basis", "files"],
                      [[x["name"], x["matched"], x["kind"], x["basis"], x["files"][:4]] for x in r["roles_as_people"]], 300))

    gr = r["generic_relationships"]
    L += ["", "## 9. Generic-relationship ratio", "",
          f"{gr['generic_edges']} of {gr['instance_edges']} instance edges ({gr['generic_ratio']:.0%}) have a generic core type "
          f"({', '.join(gr['generic_types'])}); the rest are specific relations.", ""]
    L.append(md_table(["generic core type", "edges"], [[k, v] for k, v in gr["generic_by_type"].items()]))
    L += ["", "Top generic patterns:", ""]
    L.append(md_table(["start label", "core", "end label", "edges"],
                      [[p["start"], p["core"], p["end"], p["count"]] for p in gr["top_generic_patterns"]]))
    L += ["", "Specific core types: " + (", ".join(f"{k} x{v}" for k, v in gr["specific_by_type"].items()) or "none")]
    if gr["specific_types_matching_schema_level_relations"]:
        L += ["", "Specific types that match a schema-level (SCHEMA_REL_*) relation: "
              + ", ".join(gr["specific_types_matching_schema_level_relations"])]
    if gr["schema_level_relations_without_instances"]:
        L += ["", "Schema-level relations with no instance edges: " + ", ".join(gr["schema_level_relations_without_instances"])]

    L += ["", "## 10. Property coverage", ""]
    for typ, v in r["property_coverage"].items():
        props = ", ".join(f"{k} {p:.0%}" for k, p in v["properties"].items()) or "no properties"
        L.append(f"- **{typ}** (n={v['nodes']}): {props}")
    if r["notes"]:
        L += ["", "## Notes", ""] + [f"- {n}" for n in r["notes"]]
    return "\n".join(L) + "\n"


# ---------------------------------------------------------------------------------------------
# diff
# ---------------------------------------------------------------------------------------------

def _nkey(n: Node) -> tuple[str, str]:
    return canon_type(n.label), n.compact


def run_diff(ga: Graph, gb: Graph, expect: Expectations | None) -> dict:
    def node_map(g: Graph) -> dict:
        out: dict = {}
        for n in g.instance_nodes:
            if n.compact:
                out.setdefault(_nkey(n), n)
        return out

    def edge_map(g: Graph) -> dict:
        out: dict = {}
        for e in g.inst_edges:
            s, t = g.nodes[e.start], g.nodes[e.end]
            out.setdefault((canon_rel(e.core), _nkey(s), _nkey(t)), (e.core, s.name, t.name))
        return out

    na, nb, ea, eb = node_map(ga), node_map(gb), edge_map(ga), edge_map(gb)

    def jac(a: Iterable, b: Iterable) -> float:
        a, b = set(a), set(b)
        return round(len(a & b) / len(a | b), 4) if (a | b) else 1.0

    types = sorted({k[0] for k in na} | {k[0] for k in nb})
    label_of = {canon_type(n.label): n.label for n in list(na.values()) + list(nb.values())}
    per_type = []
    for t in types:
        a = {k for k in na if k[0] == t}
        b = {k for k in nb if k[0] == t}
        per_type.append({"type": label_of.get(t, t), "a": len(a), "b": len(b), "delta": len(b) - len(a), "jaccard": jac(a, b)})
    etypes = sorted({k[0] for k in ea} | {k[0] for k in eb})
    core_of = {k[0]: v[0] for k, v in list(ea.items()) + list(eb.items())}
    per_etype = []
    for t in etypes:
        a = {k for k in ea if k[0] == t}
        b = {k for k in eb if k[0] == t}
        per_etype.append({"core": core_of.get(t, t), "a": len(a), "b": len(b), "delta": len(b) - len(a), "jaccard": jac(a, b)})
    exp_nodes, exp_edges = [], []
    if expect:
        for g in (ga, gb):
            g.pool = _label_pool(list(g.pool) + expect.types())
        for x in expect.nodes:
            pa, pb = bool(ga.find(x.get("type"), x["names"])), bool(gb.find(x.get("type"), x["names"]))
            if pa != pb:
                exp_nodes.append({"id": x["id"], "type": x.get("type"), "name": (x["names"] or [""])[0], "in_a": pa, "in_b": pb})
        for x in expect.edges:
            res = []
            for g in (ga, gb):
                fk, tk = g.find(x["from"]["type"], x["from"]["names"]), g.find(x["to"]["type"], x["to"]["names"])
                forms = rel_forms(str(x.get("type", "")), x["from"]["type"], x["to"]["type"], g.pool)
                res.append(bool(fk and tk and (any(e.forms & forms for e in g.edges_between(fk, tk))
                                               or (set(fk) & set(tk) and forms & RENAME_CANON))))
            if res[0] != res[1]:
                exp_edges.append({"id": x["id"], "type": x.get("type"), "from": (x["from"]["names"] or [""])[0],
                                  "to": (x["to"]["names"] or [""])[0], "in_a": res[0], "in_b": res[1]})
    only_a = sorted(f"{n.label} '{n.name}'" for k, n in na.items() if k not in nb)
    only_b = sorted(f"{n.label} '{n.name}'" for k, n in nb.items() if k not in na)
    return {
        "a": {"input": disp(ga.src), "shape": ga.shape, "instance_nodes": len(ga.instance_nodes), "unique_nodes": len(na),
              "instance_edges": len(ga.inst_edges), "unique_edges": len(ea)},
        "b": {"input": disp(gb.src), "shape": gb.shape, "instance_nodes": len(gb.instance_nodes), "unique_nodes": len(nb),
              "instance_edges": len(gb.inst_edges), "unique_edges": len(eb)},
        "node_jaccard": jac(na, nb), "edge_jaccard": jac(ea, eb),
        "nodes_shared": len(set(na) & set(nb)), "nodes_union": len(set(na) | set(nb)),
        "edges_shared": len(set(ea) & set(eb)), "edges_union": len(set(ea) | set(eb)),
        "per_node_type": per_type, "per_edge_type": per_etype,
        "expected_nodes_in_one_only": exp_nodes, "expected_edges_in_one_only": exp_edges,
        "expectations": expect.path if expect else None,
        "nodes_only_in_a": only_a, "nodes_only_in_b": only_b,
        "edges_only_in_a": sorted(f"{v[1]} -[{v[0]}]-> {v[2]}" for k, v in ea.items() if k not in eb),
        "edges_only_in_b": sorted(f"{v[1]} -[{v[0]}]-> {v[2]}" for k, v in eb.items() if k not in ea),
    }


def render_diff_md(d: dict) -> str:
    L = ["# Knowledge-graph diff (nondeterminism)", "",
         f"- A: `{d['a']['input']}` ({d['a']['shape']}): {d['a']['unique_nodes']} unique nodes, {d['a']['unique_edges']} unique edges",
         f"- B: `{d['b']['input']}` ({d['b']['shape']}): {d['b']['unique_nodes']} unique nodes, {d['b']['unique_edges']} unique edges",
         f"- Expectations: {d['expectations'] or 'none'}", "",
         f"**Node Jaccard: {d['node_jaccard']:.3f}** ({d['nodes_shared']} shared of {d['nodes_union']}); "
         f"**edge Jaccard: {d['edge_jaccard']:.3f}** ({d['edges_shared']} shared of {d['edges_union']}).", "",
         "Nodes are keyed by normalised type + name; edges by core type + both endpoint keys.", "",
         "## Per node type", ""]
    L.append(md_table(["type", "A", "B", "B-A", "Jaccard"],
                      [[x["type"], x["a"], x["b"], x["delta"], f"{x['jaccard']:.3f}"] for x in d["per_node_type"]]))
    L += ["", "## Per edge core type", ""]
    L.append(md_table(["core type", "A", "B", "B-A", "Jaccard"],
                      [[x["core"], x["a"], x["b"], x["delta"], f"{x['jaccard']:.3f}"] for x in d["per_edge_type"]]))
    L += ["", "## Expected nodes and edges present in only one graph", ""]
    L.append(md_table(["id", "type", "name", "in A", "in B"],
                      [[x["id"], x["type"], x["name"], x["in_a"], x["in_b"]] for x in d["expected_nodes_in_one_only"]]))
    L.append("")
    L.append(md_table(["id", "type", "from", "to", "in A", "in B"],
                      [[x["id"], x["type"], x["from"], x["to"], x["in_a"], x["in_b"]] for x in d["expected_edges_in_one_only"]]))
    for k, title in (("nodes_only_in_a", "Nodes only in A"), ("nodes_only_in_b", "Nodes only in B"),
                     ("edges_only_in_a", "Edges only in A"), ("edges_only_in_b", "Edges only in B")):
        L += ["", f"## {title} ({len(d[k])}, first 50)", ""]
        L.append("\n".join(f"- {x}" for x in d[k][:50]) or "_none_")
    return "\n".join(L) + "\n"


# ---------------------------------------------------------------------------------------------
# expectations-skeleton
# ---------------------------------------------------------------------------------------------

DEFAULT_TYPES = {
    "people": "Person", "systems": "System", "interfaces": "Interface", "programs": "Program", "db2_tables": "Table",
    "tables": "Table", "pg_tables": "Table", "rules": "BusinessRule", "services": "Service", "stages": "Process",
    "steps": "ProcessStep", "process_steps": "ProcessStep", "vendors": "Vendor", "teams": "Team",
    "departments": "Department", "committees": "Committee", "claim_types": "ClaimType", "products": "Product",
    "regulators": "Regulator", "company": "Organization", "locations": "Location", "glossary": "Term", "terms": "Term",
}
TYPE_SYNONYMS = {"BusinessRule": ["Rule"], "Table": ["DatabaseTable", "Db2Table", "DataTable"], "Process": ["ProcessStage", "Stage"],
                 "Program": ["CobolProgram"], "Organization": ["Organisation", "Company"], "Term": ["GlossaryTerm", "Concept"],
                 "Vendor": ["Organisation", "Organization"], "Regulator": ["Organisation", "Organization"]}
SKELETON_HEADER = """\
# DRAFT graph expectations generated by `python -I harness/graph_audit.py expectations-skeleton`
# from the world model (as of {as_of}). Curate it, then save as questions/graph_expectations.yaml.
# - Type and relationship names are defaults ({schema}); align them with schemas/corvane_claims.jsonld.
# - Every rename appears twice: as a RENAMED_TO edge and as a merge_expected group. Keep the one that
#   matches the intended policy. The audit counts a RENAMED_TO edge whose endpoints were merged into
#   one node as satisfied, and notes unmerged alias groups that a RENAMED_TO edge links.
# - WRITES_TO_TABLE and CALLS_PROGRAM are exhaustive; prune them to what the questions need.
# - Time-dependent role aliases (e.g. 'the CFO') are not merge variants; job titles are must_not_exist.
# - Person match_any lists full-name forms only (2+ words); initials and first names sit in merge_expected.
# - Same-name people share match_any, so one merged node satisfies both node entries; must_not_merge
#   is the check that tells them apart.
# - evidence lists manifest facts whose world_ref resolves to the entity (empty without manifests).
"""


def _schema_classes(path: Path) -> list[str]:
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    out: list[str] = []

    def walk(o: Any) -> None:
        if isinstance(o, dict):
            t = o.get("@type")
            ts = t if isinstance(t, list) else [t]
            if any(isinstance(x, str) and x.split(":")[-1] in ("Class", "NodeShape") for x in ts) and isinstance(o.get("@id"), str):
                out.append(re.split(r"[:/#]", o["@id"])[-1])
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)

    walk(doc)
    return list(dict.fromkeys(out))


def build_skeleton(w: World, facts: dict[str, dict], schema_classes: list[str] = ()) -> tuple[dict, str]:
    as_of = w.as_of
    sc = {canon_type(c): c for c in schema_classes}

    def T(coll_name: str) -> str:
        base = DEFAULT_TYPES.get(coll_name) or re.sub(r"s$", "", coll_name.split(".")[-1]).title().replace("_", "")
        for cand in [base] + TYPE_SYNONYMS.get(base, []):
            if canon_type(cand) in sc:
                return sc[canon_type(cand)]
        return base

    facts_by_ref: dict[str, list] = collections.defaultdict(list)
    for fid, f in sorted(facts.items()):
        ref, field = w.resolve_ref(f.get("world_ref"))
        if ref:
            facts_by_ref[ref].append((fid, (field or "").lower()))

    def ev(ref: str, hints: tuple = ()) -> list[str]:
        fs = facts_by_ref.get(ref, [])
        if hints:
            fs = [x for x in fs if any(h in x[1] for h in hints)]
        return [fid for fid, _ in fs][:5]

    people = w.people
    systems = w.coll("systems", "applications")
    interfaces = w.coll("interfaces", "integrations")
    programs = w.coll("programs")
    tables = w.colls("db2_tables", "tables", "pg_tables")
    rules = w.coll("rules", "business_rules")
    stages = w.coll("stages", "process_stages", "processes")
    teams, locations = w.colls("teams"), w.colls("locations")
    nodes, edges, merges, nmm, mne = [], [], [], [], []

    def pname(pid: str) -> str:
        return rec_name(people.get(pid, {}), pid)

    def person_match(pid: str) -> list[str]:
        p = people.get(pid, {})
        al = [a for a in p.get("aliases") or [] if isinstance(a, str) and len(norm_name(a).split()) >= 2]
        hist = [h.get("name") for h in p.get("name_history") or [] if isinstance(h, dict) and h.get("name")]
        return list(dict.fromkeys([pname(pid)] + hist + al))

    def sys_match(sid: str) -> list[str]:
        s = systems.get(sid)
        if not s:
            return [str(sid)]
        return list(dict.fromkeys([rec_name(s, sid)] + [a for a in s.get("aliases") or [] if isinstance(a, str)]))

    def node(typ: str, names: list[str], ref: str, importance: str, note: str | None = None) -> None:
        d = {"id": "", "type": typ, "name": names[0], "world_ref": ref, "match_any": names, "evidence": ev(ref),
             "importance": importance}
        if note:
            d["note"] = note
        nodes.append(d)

    def edge(typ: str, ftype: str, fnames: list[str], ttype: str, tnames: list[str], ref: str, hints: tuple,
             src_ref: str, with_as_of: bool = False, importance: str | None = None) -> None:
        d = {"id": "", "type": typ, "from": {"type": ftype, "match_any": fnames}, "to": {"type": ttype, "match_any": tnames}}
        if with_as_of:
            d["as_of"] = as_of
        d["world_ref"] = ref
        d["evidence"] = ev(src_ref, hints)
        if importance:
            d["importance"] = importance
        edges.append(d)

    owners: dict[str, list] = collections.defaultdict(list)
    for sid, st in stages.items():
        o = owner_at(st, as_of)
        if o:
            owners[o].append(rec_name(st, sid))
    for pid, p in sorted(people.items()):
        note = "; ".join(x for x in [", ".join(titles_of(p)[-1:]),
                                    f"process owner of {', '.join(owners[pid])}" if pid in owners else ""] if x)
        node(T("people"), person_match(pid), pid, "high", note or None)
    for sid in sorted(systems):
        node(T("systems"), sys_match(sid), sid, "high")
    for iid, it in sorted(interfaces.items()):
        node(T("interfaces"), list(dict.fromkeys([rec_name(it, iid), iid])), iid, "high")
    prog_doc = w.docs.get("programs") if isinstance(w.docs.get("programs"), dict) else {}
    declared_rt = prog_doc.get("reserve_table")
    reserve_tables = {t for t in tables if re.search(r"RESERVE|RSV", str(t), re.IGNORECASE)}
    reserve_tables |= {declared_rt} if isinstance(declared_rt, str) else set()
    reserve_writers = {str(x) for x in prog_doc.get("reserve_writers") or []}
    for pid, pr in sorted(programs.items()):
        writes = set(pr.get("writes_tables") or []) & reserve_tables
        if writes or pid in reserve_writers:
            node(T("programs"), [pid], pid, "high", "writes " + ", ".join(sorted(writes or {str(declared_rt)})))
    for sid, st in sorted(stages.items()):
        node(T("stages"), list(dict.fromkeys([rec_name(st, sid)] + ([st["code"]] if isinstance(st.get("code"), str) else []))),
             sid, "medium", f"owner {pname(owner_at(st, as_of))}" if owner_at(st, as_of) else None)
    for rid, ru in sorted(rules.items()):
        if len(ru.get("versions") or []) >= 2:
            node(T("rules"), list(dict.fromkeys([rid, rec_name(ru, rid)])), rid, "high",
                 f"{len(ru['versions'])} versions")

    for pid, p in sorted(people.items()):
        if not employed_at(p, as_of):
            continue
        m = manager_at(p, as_of)
        if m and m in people:
            edge("REPORTS_TO", T("people"), person_match(pid), T("people"), person_match(m), f"{pid}.reports_to",
                 ("report", "manager"), pid, with_as_of=True)
    for sid, st in sorted(stages.items()):
        o = owner_at(st, as_of)
        if o and o in people:
            edge("OWNS_PROCESS", T("people"), person_match(o), T("stages"), [rec_name(st, sid)], f"{sid}.owner",
                 ("owner",), sid, with_as_of=True)
    for pid, pr in sorted(programs.items()):
        for t in pr.get("writes_tables") or []:
            edge("WRITES_TO_TABLE", T("programs"), [pid], T("db2_tables"), list(dict.fromkeys([t, str(t).split(".")[-1]])),
                 f"{pid}.writes_tables", ("write",), pid, importance="high" if t in reserve_tables else "medium")
    for pid, pr in sorted(programs.items()):
        for c in pr.get("calls_programs") or []:
            edge("CALLS_PROGRAM", T("programs"), [pid], T("programs"), [c], f"{pid}.calls_programs", ("call",), pid,
                 importance="low" if re.match(r"^[A-Z]{3}CM", str(c)) else "medium")
    for rid, ru in sorted(rules.items()):
        for s in ru.get("supersedes") or []:
            other = s.get("rule") if isinstance(s, dict) else s
            if other:
                names = [other] + ([rec_name(rules[other], other)] if other in rules else [])
                edge("SUPERSEDES", T("rules"), list(dict.fromkeys([rid, rec_name(ru, rid)])), T("rules"),
                     list(dict.fromkeys(names)), f"{rid}.supersedes", ("supersed",), rid)
    for iid, it in sorted(interfaces.items()):
        for rel, fld in (("SOURCE_SYSTEM", ("source_system", "source")), ("TARGET_SYSTEM", ("target_system", "target"))):
            sid = next((it[f] for f in fld if isinstance(it.get(f), str)), None)
            if sid:
                edge(rel, T("interfaces"), list(dict.fromkeys([rec_name(it, iid), iid])), T("systems"), sys_match(sid),
                     f"{iid}.{fld[0]}", (fld[0].split("_")[0],), iid)

    renames: list[tuple[str, str, str, str, str]] = []  # (type, ref, old name, new name, source field)
    for cname, recs in sorted(w.collections.items()):
        for rid, rec in sorted(recs.items()):
            typ = T(cname.split(".")[-1])
            for rn in rec.get("renames") or []:
                if isinstance(rn, dict) and rn.get("from_name") and rn.get("to_name"):
                    renames.append((typ, rid, str(rn["from_name"]), str(rn["to_name"]), "renames"))
            rf = rec.get("renamed_from")
            new_nm = rid if cname.split(".")[-1] == "programs" else rec_name(rec, rid)
            if isinstance(rf, dict) and rf.get("old_id"):
                renames.append((typ, rid, str(rf["old_id"]), new_nm, "renamed_from"))
            elif isinstance(rf, str):
                renames.append((typ, rid, rf, new_nm, "renamed_from"))
            hist = [h.get("name") for h in rec.get("name_history") or [] if isinstance(h, dict) and h.get("name")]
            for a, b in zip(hist, hist[1:]):
                if compact(a) != compact(b):
                    renames.append((typ, rid, str(a), str(b), "name_history"))
    for typ, rid, old, new, fld in renames:
        edge("RENAMED_TO", typ, [old], typ, [new], f"{rid}.{fld}", ("rename", "name_history", "renamed"), rid)

    def unique_variant(v: str, ref: str) -> bool:
        refs = w.identity_refs(v)
        return bool(compact(v)) and (not refs or refs == {ref})

    for cname, recs in sorted(w.collections.items()):
        typ = T(cname.split(".")[-1])
        for rid, rec in sorted(recs.items()):
            canon_nm = rid if cname.split(".")[-1] == "programs" else rec_name(rec, rid)
            vs = [a for a in rec.get("aliases") or [] if isinstance(a, str)]
            vs += [str(rn.get("from_name")) for rn in rec.get("renames") or [] if isinstance(rn, dict) and rn.get("from_name")]
            vs += [h.get("name") for h in rec.get("name_history") or [] if isinstance(h, dict) and h.get("name")]
            vs += [v.get("term") for v in rec.get("variants") or [] if isinstance(v, dict) and v.get("term")]
            vs += [v for v in rec.get("variants") or [] if isinstance(v, str)]
            if isinstance(rec.get("short"), str):
                vs.append(rec["short"])
            rf = rec.get("renamed_from")
            if isinstance(rf, dict) and rf.get("old_id"):
                vs.append(str(rf["old_id"]))
            seen = {compact(canon_nm)}
            out = []
            for v in vs:
                c = compact(v)
                if c and c not in seen and unique_variant(v, rid):
                    seen.add(c)
                    out.append(v)
            if out:
                merges.append({"id": "", "type": typ, "canonical": canon_nm, "variants": out, "world_ref": rid})

    by_name: dict[str, list] = collections.defaultdict(list)
    for pid, p in people.items():
        by_name[compact(pname(pid))].append(pid)
    for c, pids in sorted(by_name.items()):
        if len(pids) < 2:
            continue
        pids = sorted(pids)
        dist = []
        for pid in pids:
            p = people[pid]
            team = teams.get(p.get("team"), {}).get("name") if isinstance(p.get("team"), str) else None
            loc = p.get("location")
            loc_name = locations.get(loc, {}).get("city") or locations.get(loc, {}).get("name") if isinstance(loc, str) else None
            dist.append(", ".join(x for x in [team, loc_name, (titles_of(p) or [None])[-1]] if x) or pid)
        nmm.append({"id": "", "type": T("people"), "name": pname(pids[0]), "distinct": pids, "distinguishing": dist})

    seen_t: set = set()
    for pid, p in sorted(people.items()):
        for t in titles_of(p):
            if compact(t) and compact(t) not in seen_t and compact(t) not in by_name:
                seen_t.add(compact(t))
                mne.append({"id": "", "type": T("people"), "name": t, "reason": "job title extracted as a Person node"})
    for prefix, sec in (("GN", nodes), ("GE", edges), ("GM", merges), ("GX", nmm), ("GF", mne)):
        for i, d in enumerate(sec, 1):
            d["id"] = f"{prefix}{i:03d}"
    doc = {"version": 1, "as_of": as_of, "nodes": nodes, "edges": edges, "merge_expected": merges,
           "must_not_merge": nmm, "must_not_exist": mne}
    header = SKELETON_HEADER.format(as_of=as_of, schema="schema classes mapped where found" if schema_classes
                                    else "schemas/corvane_claims.jsonld not found")
    return doc, header


# ---------------------------------------------------------------------------------------------
# CLI commands
# ---------------------------------------------------------------------------------------------

def _label_from(path: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", Path(path).stem) or "graph"


def _write_pair(md_path: Path, md: str, data: dict) -> Path:
    md_path = Path(md_path)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(md, encoding="utf-8")
    jp = md_path.with_suffix(".json")
    jp.write_text(json.dumps(data, indent=1, ensure_ascii=False, default=str), encoding="utf-8")
    return jp


def _load_expect_arg(arg: str | None) -> tuple[Expectations | None, str | None]:
    if arg:
        p = Path(arg)
        if not p.exists():
            return None, f"expectations file not found: {p}"
        return load_expectations(p), None
    if DEFAULT_EXPECT.exists():
        return load_expectations(DEFAULT_EXPECT), None
    return None, None


def audit_file(path: str, expect: Expectations | None, ctx: Ctx, world: World | None, world_notes: list[str],
               label: str | None = None, text: TextSearcher | None = None) -> dict:
    g = load_graph(path)
    return Audit(g, world, expect, ctx, label or _label_from(path), world_notes, text).run()


def cmd_audit(args: argparse.Namespace) -> int:
    expect, err = _load_expect_arg(args.expect)
    if err:
        print(err, file=sys.stderr)
        return 2
    world, wnotes = load_world_view(args.world_dir, use_lib=not args.no_worldlib)
    ctx = Ctx(Path(args.root).resolve(), Path(args.index_dir))
    label = args.label or _label_from(args.export)
    try:
        g = load_graph(args.export)
    except (OSError, ValueError) as exc:
        print(f"cannot read {args.export}: {exc}", file=sys.stderr)
        return 2
    print(f"Detected shape: {g.shape}")
    print(f"World model: {world.source + ' (' + str(len(world.entity)) + ' entities, ' + str(len(world.norm_map)) + ' lexicon terms)' if world else 'not available'}")
    for n in wnotes:
        print(f"  note: {n}")
    print(f"Expectations: {expect.path if expect else 'none (checks 2-4 skipped)'}")
    res = Audit(g, world, expect, ctx, label, wnotes).run()
    print(f"Source-text index: {res['meta']['source_text_index']}")
    out = Path(args.out) if args.out else RESULTS / f"graph_audit_{label}.md"
    jp = _write_pair(out, render_audit_md(res), res)
    t = res["totals"]
    print(f"Nodes {t['instance_nodes']} instance + {t['schema_nodes']} schema; edges {t['instance_edges']} instance, "
          f"{t['schema_edges']['total']} schema-level, {t['dangling_edges']} dangling")
    print("Top findings:")
    for i, f in enumerate(res["top_findings"][:10], 1):
        print(f"  {i:2d}. [{f['severity']}] {f['check']}: {f['text']}")
    print(f"Wrote {out} and {jp}")
    return 0


def cmd_diff(args: argparse.Namespace) -> int:
    expect, err = _load_expect_arg(args.expect)
    if err:
        print(err, file=sys.stderr)
        return 2
    try:
        ga, gb = load_graph(args.a), load_graph(args.b)
    except (OSError, ValueError) as exc:
        print(f"cannot read input: {exc}", file=sys.stderr)
        return 2
    print(f"A shape: {ga.shape}\nB shape: {gb.shape}")
    d = run_diff(ga, gb, expect)
    out = Path(args.out) if args.out else RESULTS / f"graph_diff_{_label_from(args.a)}_vs_{_label_from(args.b)}.md"
    jp = _write_pair(out, render_diff_md(d), d)
    print(f"Node Jaccard {d['node_jaccard']:.3f} ({d['nodes_shared']}/{d['nodes_union']}), "
          f"edge Jaccard {d['edge_jaccard']:.3f} ({d['edges_shared']}/{d['edges_union']})")
    print(f"Expected nodes in one graph only: {len(d['expected_nodes_in_one_only'])}; "
          f"expected edges in one graph only: {len(d['expected_edges_in_one_only'])}")
    print(f"Wrote {out} and {jp}")
    return 0


def cmd_skeleton(args: argparse.Namespace) -> int:
    world, notes = load_world_view(args.world_dir, use_lib=not args.no_worldlib)
    if world is None or not world.people:
        print("expectations-skeleton: the world model is not available yet "
              + ("(" + "; ".join(notes) + ")" if notes else "(no people found in it)")
              + ". Nothing written.", file=sys.stderr)
        return 2
    if args.as_of:
        world.as_of = args.as_of
    facts = load_facts(Path(args.root) / "manifests")
    doc, header = build_skeleton(world, facts, _schema_classes(SCHEMA_FILE) if SCHEMA_FILE.exists() else [])
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(header + yaml.safe_dump(doc, sort_keys=False, allow_unicode=True, width=120, default_flow_style=None),
                   encoding="utf-8")
    print(f"Wrote {out}: {len(doc['nodes'])} nodes, {len(doc['edges'])} edges, {len(doc['merge_expected'])} merge groups, "
          f"{len(doc['must_not_merge'])} must-not-merge groups, {len(doc['must_not_exist'])} must-not-exist entries "
          f"(world: {world.source}, as of {world.as_of})")
    return 0


# ---------------------------------------------------------------------------------------------
# selftest
# ---------------------------------------------------------------------------------------------

def _fake_world() -> dict[str, Any]:
    open_ = {"from": "2020-01-01", "to": None}
    return {
        "meta.yaml": {"today": "2026-11-15"},
        "people.yaml": {"people": [
            {"id": "P1", "name": "Alice Marsh", "aliases": ["A. Marsh", "Alice"], "team": "T1", "location": "L1",
             "titles": [{"title": "Claims Director", **open_}], "reports_to": [{"manager_id": "P2", **open_}],
             "employment": {"from": "2020-01-01", "to": None}},
            {"id": "P2", "name": "Bob Tanner", "aliases": ["B. Tanner"], "team": "T1", "location": "L1",
             "titles": [{"title": "Chief Operating Officer", **open_}], "reports_to": [],
             "role_aliases": [{"alias": "the COO", "from": "2020-01-01", "to": None}]},
            {"id": "P3", "name": "Dan Okafor", "aliases": [], "team": "T2", "location": "L1",
             "titles": [{"title": "Claims Handler", **open_}], "reports_to": [{"manager_id": "P1", **open_}]},
            {"id": "P4", "name": "Dan Okafor", "aliases": [], "team": "T3", "location": "L2",
             "titles": [{"title": "Integration Architect", **open_}], "reports_to": [{"manager_id": "P2", **open_}]},
            {"id": "P5", "name": "Carol Finch", "aliases": ["C. Finch"], "team": "T1", "location": "L2",
             "titles": [{"title": "Head of Reserving", **open_}], "reports_to": [{"manager_id": "P2", **open_}]},
        ]},
        "org.yaml": {"locations": [{"id": "L1", "name": "Leeds Office", "city": "Leeds"},
                                   {"id": "L2", "name": "Oslo Office", "city": "Oslo"}],
                     "departments": [{"id": "D1", "name": "Claims Department"}],
                     "teams": [{"id": "T1", "name": "Claims Leadership", "department": "D1"},
                               {"id": "T2", "name": "Motor Claims", "department": "D1"},
                               {"id": "T3", "name": "Integration Architecture", "department": "D1"}],
                     "committees": [{"id": "C1", "name": "Reserving Committee"}]},
        "systems.yaml": {"systems": [
            {"id": "S1", "name": "Ledgerline", "aliases": ["the ledger"],
             "renames": [{"from_name": "OLDLEDGER", "to_name": "Ledgerline", "date": "2024-01-01"}]},
            {"id": "S2", "name": "Hubcore", "aliases": ["HC"], "renames": []}]},
        "interfaces.yaml": {"interfaces": [{"id": "IF-001", "name": "Reserve feed", "source_system": "S1", "target_system": "S2"}]},
        "programs.yaml": {"programs": [
            {"id": "PRG010", "writes_tables": ["CLR.T_RESERVE"], "calls_programs": ["PRG020"], "renamed_from": {"old_id": "OLDPRG1"}},
            {"id": "PRG020", "writes_tables": [], "calls_programs": []}]},
        "db2_tables.yaml": [{"name": "CLR.T_RESERVE", "columns": [{"name": "RSV_ID"}]}],
        "rules.yaml": {"rules": [
            {"id": "BR-1", "title": "Reserve review cadence", "versions": [{"version": 1}, {"version": 2}], "supersedes": []},
            {"id": "BR-2", "title": "Referral threshold", "versions": [{"version": 1}], "supersedes": [{"rule": "BR-1", "version": 2}]}]},
        "process.yaml": {"stages": [{"id": "ST1", "name": "Claim registration", "owner_history": [{"person": "P1", **open_}]}],
                         "steps": [{"id": "PS-1", "name": "Register claim", "stage": "ST1"}]},
        "glossary.yaml": {"terms": [{"id": "G-1", "canonical": "Large loss", "variants": [{"term": "LLN"}]},
                                    {"id": "G-2", "canonical": "Hubcore", "variants": [{"term": "the hub platform"}]}]},
        "names_denylist.yaml": {"entries": [{"name": "Quantum Llama Initiative"}]},  # must stay out of the lexicon
    }


def _fake_expectations() -> dict:
    return {
        "version": 1, "as_of": "2026-11-15",
        "nodes": [
            {"id": "GN001", "type": "Person", "name": "Alice Marsh", "match_any": ["Alice Marsh", "A. Marsh"], "importance": "high",
             "evidence": ["LD001-F001"]},
            {"id": "GN002", "type": "Person", "name": "Bob Tanner", "importance": "high"},
            {"id": "GN003", "type": "Person", "name": "Carol Finch", "match_any": ["C. Finch"], "importance": "high",
             "evidence": ["LD001-F002"]},
            {"id": "GN004", "type": "System", "name": "Ledgerline", "importance": "high"},
            {"id": "GN005", "type": "System", "name": "Hubcore", "importance": "high"},
            {"id": "GN006", "type": "Interface", "name": "Reserve feed", "match_any": ["IF-001"], "importance": "medium"},
        ],
        "edges": [
            {"id": "GE001", "type": "REPORTS_TO", "from": {"type": "Person", "match_any": ["Alice Marsh"]},
             "to": {"type": "Person", "match_any": ["Bob Tanner"]}, "as_of": "2026-11-15", "evidence": ["LD001-F001"]},
            {"id": "GE002", "type": "sourceSystem", "from": {"type": "Interface", "match_any": ["Reserve feed"]},
             "to": {"type": "System", "match_any": ["Ledgerline"]}},
            {"id": "GE003", "type": "interface-target-system", "from": {"type": "Interface", "match_any": ["Reserve feed"]},
             "to": {"type": "System", "match_any": ["Hubcore"]}},
        ],
        "merge_expected": [
            {"id": "GM001", "type": "Person", "canonical": "Alice Marsh", "variants": ["A. Marsh", "Alice"]},
            {"id": "GM002", "type": "System", "canonical": "Ledgerline", "variants": ["OLDLEDGER"]},
        ],
        "must_not_merge": [
            {"id": "GX001", "type": "Person", "name": "Dan Okafor", "distinct": ["P3", "P4"],
             "distinguishing": ["Motor Claims, Leeds", "Integration Architecture, Oslo"]},
        ],
        "must_not_exist": [
            {"id": "GF001", "type": "Person", "name": "Claims Director", "reason": "role title extracted as a Person node"},
            {"id": "GF002", "type": "Person", "name": "Chief Operating Officer", "reason": "role title"},
        ],
    }


def _product_node(ctx: str, label: str, name: str, file: str, **attrs: Any) -> dict:
    gid = f"{label.lower()}_{norm_name(name).replace(' ', '_')}"
    return {"key": f"{ctx}:{gid}", "label": label,
            "properties": {"id": gid, "key": f"{ctx}:{gid}", "name": label, "label": label,
                           "properties": {"name": name, **attrs}, "source_file": file, "source_files": [file],
                           "section_id": "s1", "llm_generated_id": gid,
                           "property_history": [{"prop_key": "name", "value": name, "source_file": file}]}}


def _fake_export_a() -> dict:
    c = "ctxA"
    nodes = [
        _product_node(c, "Person", "Alice Marsh", "LD001_alpha.md", role="Claims Director"),
        _product_node(c, "Person", "A. Marsh", "03_TX001_gamma.txt"),
        _product_node(c, "Person", "Bob Tanner", "LD001_alpha.md", title="COO"),
        _product_node(c, "Person", "Claims Director", "LD002_beta.md"),
        _product_node(c, "Person", "Dan Okafor", "LD002_beta.md", team="Motor Claims", location="Oslo"),
        _product_node(c, "System", "Ledgerline", "LD002_beta.md"),
        _product_node(c, "System", "Hubcore", "LD001_alpha.md"),
        _product_node(c, "System", "Hubcore", "03_TX001_gamma.txt", vendor="in-house"),
        _product_node(c, "Interface", "Reserve feed", "LD002_beta.md"),
        _product_node(c, "Project", "Quantum Llama Initiative", "LD001_alpha.md"),
        _product_node(c, "Location", "Harbour Lane Depot", "LD009_unlisted.md"),
        {"key": f"{c}:schema:person", "label": "SchemaNode_Person", "properties": {"name": "Person"}},
        {"key": f"{c}:schema:system", "label": "SchemaNode_System", "properties": {"name": "System"}},
    ]
    nodes[7]["key"] = nodes[7]["properties"]["key"] = f"{c}:system_hubcore_2"
    k = {n["properties"].get("properties", {}).get("name", n["key"]) + ("#2" if n["key"].endswith("_2") else ""): n["key"] for n in nodes}

    def rel(t: str, a: str, b: str, **p: Any) -> dict:
        return {"start_key": a, "end_key": b, "type": t,
                "properties": {"source": "schema_augment", "source_id": "x", "alignment_confidence": 0.9, **p}}

    rels = [
        rel("INTERFACE_SOURCE_SYSTEM_SYSTEM", k["Reserve feed"], k["Ledgerline"]),
        rel("INTERFACE_TARGET_SYSTEM_SYSTEM", k["Reserve feed"], k["Hubcore"], source_file="LD002_beta.md"),
        rel("PERSON_BELONGS_TO_PERSON", k["Alice Marsh"], k["Bob Tanner"]),
        rel("NODE_IS", k["Alice Marsh"], f"{c}:schema:person"),
        rel("SCHEMA_REL_PERSON_REPORTS_TO_PERSON", f"{c}:schema:person", f"{c}:schema:person"),
        rel("PERSON_REPORTS_TO_PERSON", k["Bob Tanner"], f"{c}:person_nobody"),
    ]
    return {"context_id": c, "node_types": ["Person", "System", "Interface", "Project", "Location"],
            "edge_types": sorted({r["type"] for r in rels}),
            "extraction": {"nodes": nodes, "relationships": rels, "node_count": len(nodes),
                           "relationship_count": len(rels) + 1, "dangling_relationships_dropped": 0}}


def _fake_export_b() -> dict:
    names = [("Person", "Alice Marsh"), ("Person", "Bob Tanner"), ("Person", "Claims Director"), ("Person", "Dan Okafor"),
             ("System", "Ledgerline"), ("System", "Hubcore"), ("Interface", "Reserve feed"), ("Location", "Harbour Lane Depot")]
    nodes = [{"id": i, "labels": ["Entity", lab], "properties": {"name": nm, "source_file": "LD001_alpha.md"}}
             for i, (lab, nm) in enumerate(names)]
    ix = {nm: i for i, (_lab, nm) in enumerate(names)}
    links = [{"source": ix["Reserve feed"], "target": ix["Ledgerline"], "type": "sourceSystem"},
             {"source": ix["Reserve feed"], "target": ix["Hubcore"], "type": "TARGET_SYSTEM"},
             {"source": ix["Alice Marsh"], "target": ix["Bob Tanner"], "type": "BELONGS_TO"},
             {"source": ix["Alice Marsh"], "target": ix["Bob Tanner"], "type": "reportsTo"}]
    return {"nodes": nodes, "links": links}


class _Checker:
    def __init__(self) -> None:
        self.passed, self.failed = 0, []

    def eq(self, name: str, got: Any, want: Any) -> None:
        if got == want:
            self.passed += 1
            print(f"  PASS {name}")
        else:
            self.failed.append(name)
            print(f"  FAIL {name}\n       got:  {got!r}\n       want: {want!r}")

    def true(self, name: str, cond: Any, detail: Any = "") -> None:
        self.eq(name + (f" [{detail}]" if detail and not cond else ""), bool(cond), True)


def cmd_selftest(args: argparse.Namespace) -> int:
    T = _Checker()
    base = TEST_DIR
    if base.exists():
        shutil.rmtree(base)
    root = base / "root"
    wdir = base / "world"
    (wdir / "data").mkdir(parents=True)
    for fname, doc in _fake_world().items():
        (wdir / "data" / fname).write_text(yaml.safe_dump(doc, sort_keys=False, allow_unicode=True), encoding="utf-8")
    texts = {
        "corpus/upload/long_docs/LD001_alpha.md": "Alice Marsh, the Claims Director, reports to Bob Tanner.\n"
                                                  "Carol Finch heads Reserving. Hubcore is the target platform.\n",
        "corpus/upload/long_docs/LD002_beta.md": "Ledgerline sends the Reserve feed to Hubcore.\n"
                                                 "Spare parts go via the Harbour-Lane depot in Leeds.\n",
        "corpus/upload/text/TX001_gamma.txt": "A. Marsh approved the Hubcore change.\n",
        "corpus/upload/text/TX002_empty.txt": "Ledgerline batch notes, nothing else.\n",
    }
    for rel, txt in texts.items():
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / rel).write_text(txt, encoding="utf-8")
    (root / "manifests").mkdir(parents=True)
    facts = [{"fact_id": "LD001-F001", "world_ref": "P1", "kind": "needle", "statement": "Alice reports to Bob",
              "file": "corpus/upload/long_docs/LD001_alpha.md", "locator": {"kind": "text_lines", "start": 1, "end": 1},
              "needle": "reports to Bob Tanner"},
             {"fact_id": "LD001-F002", "world_ref": "P5.titles", "kind": "needle", "statement": "Carol heads Reserving",
              "file": "corpus/upload/long_docs/LD001_alpha.md", "locator": {"kind": "text_lines", "start": 2, "end": 2},
              "needle": "Carol Finch heads Reserving"},
             {"fact_id": "TX002-F001", "world_ref": "S1", "kind": "needle", "statement": "Ledgerline batch",
              "file": "corpus/upload/text/TX002_empty.txt", "locator": {"kind": "text_lines", "start": 1, "end": 1},
              "needle": "Ledgerline batch"}]
    (root / "manifests" / "test.facts.yaml").write_text(yaml.safe_dump(facts, sort_keys=False), encoding="utf-8")
    exp_path = base / "graph_expectations.yaml"
    exp_path.write_text(yaml.safe_dump(_fake_expectations(), sort_keys=False), encoding="utf-8")
    a_path, b_path = base / "export_a.json", base / "export_b.json"
    a_path.write_text(json.dumps(_fake_export_a(), indent=1), encoding="utf-8")
    b_path.write_text(json.dumps(_fake_export_b(), indent=1), encoding="utf-8")
    index_dir = base / "index"
    from harness import build_index as B
    st = B.build(sources=B.discover_sources([root / "corpus" / "upload"], include_code=False, repo_root=root),
                 index_dir=index_dir, jobs=1, ocr=False, verbose=False, prune=False, repo_root=root)
    T.eq("test index built for 4 files", (st["sources"], len(st["errors"])), (4, 0))

    print("normalisation")
    T.eq("REPORTS_TO == reportsTo == PERSON_REPORTS_TO_PERSON",
         {canon_rel("REPORTS_TO"), canon_rel(core_relation("reportsTo")),
          canon_rel(core_relation("PERSON_REPORTS_TO_PERSON", "Person", "Person"))}, {"REPORTSTO"})
    T.eq("PROCESS_STEP_BELONGS_TO_PERSON -> BELONGS_TO (real labels)",
         core_relation("PROCESS_STEP_BELONGS_TO_PERSON", "ProcessStep", "Person"), "BELONGS_TO")
    T.eq("PROCESS_STEP_BELONGS_TO_PERSON -> BELONGS_TO (label pool, longest first)",
         core_relation("PROCESS_STEP_BELONGS_TO_PERSON", None, None, _label_pool(["Process", "Person", "ProcessStep"])), "BELONGS_TO")
    T.eq("one-sided label strip is not a core strip", core_relation("TARGET_SYSTEM", "Interface", "System"), "TARGET_SYSTEM")
    T.true("expected WRITES_TO_TABLE matches PROGRAM_WRITES_TO_TABLE",
           rel_forms("WRITES_TO_TABLE", "Program", "Table") & rel_forms("PROGRAM_WRITES_TO_TABLE", "Program", "Table"))
    T.eq("names fold Nordic letters", norm_name("Ingrid Sørensen"), norm_name("Ingrid Sorensen"))
    T.eq("compact ignores punctuation/spacing", compact("reserve-engine"), compact("Reserve Engine"))
    T.eq("leading 'the' and '&'", (norm_name("the Claims Director"), norm_name("Risk & Compliance")),
         ("claims director", "risk and compliance"))
    T.true("type match is suffix-tolerant", type_matches("BusinessRule", "Rule") and not type_matches("ProcessStep", "Process"))

    print("world model (YAML fallback)")
    w, wnotes = load_world_view(wdir, use_lib=False)
    T.true("world loaded from YAML", w is not None and len(w.people) == 5, wnotes)
    T.eq("denylist kept out of the lexicon", w.trace("Quantum Llama Initiative"), None)
    T.eq("alias resolves to one entity", w.identity_refs("A. Marsh"), {"P1"})
    T.eq("homonyms are ambiguous", w.identity_refs("Dan Okafor"), {"P3", "P4"})
    T.eq("a core entity wins over a glossary entry of the same name", w.identity_refs("Hubcore"), {"S2"})
    T.eq("world date read from YAML", w.as_of, "2026-11-15")
    T.eq("manifest world_ref with a field resolves", w.resolve_ref("P5.titles"), ("P5", "titles"))
    T.true("fuzzy lexicon match", (w.trace("Ledgerlines") or ("",))[0].startswith("fuzzy"))
    T.eq("fuzzy match keeps digits (OLDPRG2 is not OLDPRG1)", (w.trace("OLDPRG2"), w.trace("oldprg-1")[0]),
         (None, "exact (spacing/punctuation)"))
    T.true("token-subset lexicon match", (w.trace("Ledgerline Reserve feed adapter") or ("",))[0].startswith("token subset"))
    obj = types.SimpleNamespace(lexicon=lambda: [{"term": "Zed Quill", "ref": "person:PX", "kind": "name"}],
                                people={"PX": {"id": "PX", "name": "Zed Quill", "aliases": ["Z. Quill"]}}, today="2026-11-15")
    w2 = World.from_object(obj)
    T.eq("worldlib-style object: lexicon() + dict-by-id sets", (w2.identity_refs("Z. Quill"), w2.identity_refs("Zed Quill")),
         ({"PX"}, {"PX"}))

    print("audit of the planted export")
    expect = load_expectations(exp_path)
    ctx = Ctx(root, index_dir)
    r = audit_file(str(a_path), expect, ctx, w, wnotes, "selftest")
    T.eq("shape detected", r["meta"]["shape"], "ingestion response: extraction.{nodes, relationships}")
    t = r["totals"]
    T.eq("totals: instance/schema nodes", (t["instance_nodes"], t["schema_nodes"]), (11, 2))
    T.eq("totals: instance edges by core type", t["instance_edges_by_core_type"],
         {"SOURCE_SYSTEM": 1, "TARGET_SYSTEM": 1, "BELONGS_TO": 1})
    T.eq("totals: schema edges NODE_IS / SCHEMA_REL / dangling",
         (t["schema_edges"]["NODE_IS"], t["schema_edges"]["SCHEMA_REL_*"], t["dangling_edges"]), (1, 1, 1))
    T.eq("totals: only relationship_count and the dangling count are flagged",
         sorted(x["field"] for x in t["stated_vs_recomputed"] if x["status"] == "MISMATCH"),
         ["dangling_relationships_dropped", "relationship_count"])
    T.eq("check 1: same-name duplicate", [(x["type"], x["name"], x["count"]) for x in r["duplicates"]["same_name"]],
         [("System", "Hubcore", 2)])
    T.eq("check 1: alias duplicate", [(x["world_ref"], x["names"]) for x in r["duplicates"]["same_world_entity"]],
         [("P1", ["A. Marsh", "Alice Marsh"])])
    T.eq("check 2: unmerged aliases", [x["id"] for x in r["unmerged_aliases"] if x["status"] == "unmerged"], ["GM001"])
    T.eq("check 3: wrong merges", [x["id"] for x in r["wrong_merges"] if x["status"] == "collapsed"], ["GX001"])
    T.eq("check 3: distinguishing hints", r["wrong_merges"][0]["distinguishing_hints_in_merged_node"], ["Motor Claims", "Oslo"])
    T.eq("check 4: missing nodes", [x["id"] for x in r["missing"]["nodes"] if x["status"] != "present"], ["GN003"])
    T.eq("check 4: evidence file of the missing node", r["missing"]["nodes"][2]["evidence"],
         ["LD001-F002 (corpus/upload/long_docs/LD001_alpha.md)"])
    me = {x["id"]: x for x in r["missing"]["edges"]}
    T.eq("check 4: missing edges", [k for k, x in me.items() if x["status"] != "present"], ["GE001"])
    T.eq("check 4: missing edge detail", (me["GE001"]["status"], me["GE001"]["linked_instead_by"]),
         ("missing (both endpoints present)", ["BELONGS_TO"]))
    h = r["hallucinated"]
    T.eq("check 5: untraceable nodes", [x["name"] for x in h["untraceable"]], ["Quantum Llama Initiative"])
    T.eq("check 5: traced by source text only (punctuation-insensitive)", h["traced_by_text_only"], 1)
    T.eq("check 5: must_not_exist hits", [x["id"] for x in h["must_not_exist_hits"]], ["GF001"])
    c = r["coverage"]
    T.eq("check 6: zero-node files", c["zero_node_files"], ["corpus/upload/text/TX002_empty.txt"])
    T.eq("check 6: unmatched export files", list(c["export_files_not_in_corpus"]), ["LD009_unlisted.md"])
    rows = {x["file"].rsplit("/", 1)[-1]: x for x in c["files"]}
    T.eq("check 6: nodes/edges per file",
         {k: (v["nodes"], v["edges"]) for k, v in rows.items()},
         {"LD001_alpha.md": (4, 1), "LD002_beta.md": (4, 2), "TX001_gamma.txt": (2, 0), "TX002_empty.txt": (0, 0)})
    T.eq("check 6: planted facts joined (facts, entity in graph, entity from file)",
         {k: (v["facts"], v["entity_present_in_graph"], v["entity_present_in_nodes_from_file"]) for k, v in rows.items() if v["facts"]},
         {"LD001_alpha.md": (2, 1, 1), "TX002_empty.txt": (1, 1, 0)})
    T.eq("roles-as-people", [(x["name"], x["basis"]) for x in r["roles_as_people"]], [("Claims Director", "world")])
    gr = r["generic_relationships"]
    T.eq("generic-relationship ratio", (gr["generic_edges"], gr["instance_edges"], gr["generic_by_type"]), (1, 3, {"BELONGS_TO": 1}))
    T.eq("schema-level relations without instance edges", (gr["schema_level_relations_without_instances"],
                                                            gr["specific_types_matching_schema_level_relations"]), (["REPORTS_TO"], []))
    T.eq("property coverage (Person)", r["property_coverage"]["Person"]["properties"],
         {"name": 1.0, "location": 0.2, "role": 0.2, "team": 0.2, "title": 0.2})
    T.true("top findings: at most 20, the wrong merge first", 0 < len(r["top_findings"]) <= TOP_N
           and r["top_findings"][0]["check"] == "3 wrong merges", r["top_findings"][:1])
    md = render_audit_md(r)
    T.true("markdown: top findings precede details", md.index("## Top 20 findings") < md.index("## 1. Totals"))
    _write_pair(base / "graph_audit_selftest.md", md, r)

    r2 = audit_file(str(a_path), expect, Ctx(root, base / "no_index"), w, wnotes, "noindex")
    T.eq("check 5 without an index: lexicon-only candidates",
         ([x["name"] for x in r2["hallucinated"]["untraceable"]], r2["hallucinated"]["text_checked"]),
         (["Quantum Llama Initiative", "Harbour Lane Depot"], False))
    r3 = audit_file(str(a_path), None, ctx, None, [], "noworld")
    T.true("audit runs without world model or expectations", r3["missing"] is None and r3["unmerged_aliases"] is None)

    print("shape detection")
    T.eq("top-level {nodes, links} with labels[]", load_graph(b_path).shape,
         "top-level {nodes, links} (property-graph records: id/identity, labels[], properties)")
    plain = [{"type": "node", "id": "1", "labels": ["Person"], "properties": {"name": "X"}},
             {"type": "relationship", "id": "r1", "label": "KNOWS", "start": {"id": "1"}, "end": {"id": "2"}},
             {"type": "node", "id": "2", "labels": ["Person"], "properties": {"name": "Y"}}]
    pl = base / "plain.jsonl"
    pl.write_text("\n".join(json.dumps(x) for x in plain), encoding="utf-8")
    gp = load_graph(pl)
    T.eq("JSON lines / plain list", (gp.shape.split(":")[0], len(gp.instance_nodes), len(gp.inst_edges)), ("JSON lines", 2, 1))
    ge = parse_graph({"nodes": [{"id": "a", "label": "Person", "name": "Q"}], "edges": [{"from": "a", "to": "a", "type": "X"}]})
    T.eq("top-level {nodes, edges}", (ge.shape, ge.instance_nodes[0].name, len(ge.inst_edges)), ("top-level {nodes, edges}", "Q", 1))

    print("diff")
    d = run_diff(load_graph(a_path), load_graph(b_path), expect)
    T.eq("node Jaccard", (d["node_jaccard"], d["nodes_shared"], d["nodes_union"]), (0.8, 8, 10))
    T.eq("edge Jaccard", (d["edge_jaccard"], d["edges_shared"], d["edges_union"]), (0.75, 3, 4))
    T.eq("expected edges in one graph only", [(x["id"], x["in_a"], x["in_b"]) for x in d["expected_edges_in_one_only"]],
         [("GE001", False, True)])
    T.eq("expected nodes in one graph only", d["expected_nodes_in_one_only"], [])
    T.eq("per-type delta (Person)", next((x["a"], x["b"]) for x in d["per_node_type"] if x["type"] == "Person"), (5, 4))
    _write_pair(base / "graph_diff_selftest.md", render_diff_md(d), d)

    print("expectations-skeleton")
    doc, header = build_skeleton(w, load_facts(root / "manifests"))
    T.eq("skeleton nodes", sorted(n["world_ref"] for n in doc["nodes"]),
         sorted(["P1", "P2", "P3", "P4", "P5", "S1", "S2", "IF-001", "PRG010", "ST1", "BR-1"]))
    ed = {(e["type"], e["from"]["match_any"][0], e["to"]["match_any"][0]) for e in doc["edges"]}
    want = {("REPORTS_TO", "Alice Marsh", "Bob Tanner"), ("REPORTS_TO", "Dan Okafor", "Alice Marsh"),
            ("REPORTS_TO", "Carol Finch", "Bob Tanner"), ("OWNS_PROCESS", "Alice Marsh", "Claim registration"),
            ("WRITES_TO_TABLE", "PRG010", "CLR.T_RESERVE"), ("CALLS_PROGRAM", "PRG010", "PRG020"),
            ("SUPERSEDES", "BR-2", "BR-1"), ("SOURCE_SYSTEM", "Reserve feed", "Ledgerline"),
            ("TARGET_SYSTEM", "Reserve feed", "Hubcore"), ("RENAMED_TO", "OLDLEDGER", "Ledgerline"),
            ("RENAMED_TO", "OLDPRG1", "PRG010")}
    T.eq("skeleton edges", want - ed, set())
    T.eq("skeleton merge_expected (Alice)", next(m["variants"] for m in doc["merge_expected"] if m["world_ref"] == "P1"),
         ["A. Marsh", "Alice"])
    T.eq("skeleton must_not_merge", [(m["name"], m["distinct"]) for m in doc["must_not_merge"]], [("Dan Okafor", ["P3", "P4"])])
    T.eq("skeleton must_not_exist titles", sorted(m["name"] for m in doc["must_not_exist"]),
         ["Chief Operating Officer", "Claims Director", "Claims Handler", "Head of Reserving", "Integration Architect"])
    T.eq("skeleton evidence from manifests", next(n["evidence"] for n in doc["nodes"] if n["world_ref"] == "P1"), ["LD001-F001"])
    sk = base / "graph_expectations.draft.yaml"
    sk.write_text(header + yaml.safe_dump(doc, sort_keys=False, allow_unicode=True, default_flow_style=None), encoding="utf-8")
    r4 = audit_file(str(a_path), load_expectations(sk), ctx, w, wnotes, "vs_skeleton")
    m4 = {(x["from"], x["to"]): x["status"] for x in r4["missing"]["edges"] if x["type"] == "REPORTS_TO"}
    T.eq("audit against the skeleton: REPORTS_TO Alice->Bob missing", m4.get(("Alice Marsh", "Bob Tanner")),
         "missing (both endpoints present)")
    import contextlib
    import io
    err = io.StringIO()
    with contextlib.redirect_stderr(err):
        rc = cmd_skeleton(argparse.Namespace(world_dir=str(base / "no_world"), no_worldlib=True, as_of=None,
                                             root=str(root), out=str(base / "never.yaml")))
    T.eq("skeleton fails gracefully without a world model",
         (rc, (base / "never.yaml").exists(), "not available yet" in err.getvalue()), (2, False, True))

    print(f"\nselftest: {T.passed} passed, {len(T.failed)} failed (artefacts in {base})")
    return 1 if T.failed else 0


# ---------------------------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog="graph_audit.py", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True, metavar="{audit,diff,expectations-skeleton,selftest}")

    def common(p: argparse.ArgumentParser, world: bool = True) -> None:
        if world:
            p.add_argument("--world-dir", default=str(DEFAULT_WORLD), help="world model package dir (default: world/)")
            p.add_argument("--no-worldlib", action="store_true", help="ignore world/worldlib.py and read world/data/*.yaml")
        p.add_argument("--root", default=str(ROOT), help="corpus root holding corpus/upload, manifests/, build/code_repo "
                                                         "(default: the repo)")

    p = sub.add_parser("audit", help="audit one exported graph", formatter_class=argparse.RawDescriptionHelpFormatter,
                       description="Totals, the six expectation checks (duplicates, unmerged aliases, wrong merges, "
                                   "missing nodes/edges, hallucinated nodes, per-file coverage), roles extracted as "
                                   "people, generic-relationship ratio and property coverage. Writes Markdown and a "
                                   "JSON twin with the top 20 findings first.")
    p.add_argument("export", help="exported graph JSON (shape auto-detected)")
    p.add_argument("--expect", help=f"expectations YAML (default: {DEFAULT_EXPECT.relative_to(ROOT)} when present)")
    p.add_argument("--out", help="Markdown report path; the JSON twin goes next to it (default: "
                                 "results/graph_audit_<label>.md)")
    p.add_argument("--label", help="report label (default: the export file's stem)")
    p.add_argument("--index-dir", default=str(DEFAULT_INDEX), help="source-text index for the hallucination check "
                                                                   "(default: build/index; skipped when absent)")
    common(p)
    p.set_defaults(func=cmd_audit)

    p = sub.add_parser("diff", help="compare two graphs built from the same corpus (nondeterminism metric)",
                       description="Jaccard overlap of nodes (type + normalised name) and edges (core type + "
                                   "normalised endpoints), per-type deltas, and expected nodes/edges found in only "
                                   "one of the two graphs.")
    p.add_argument("a", help="first exported graph JSON")
    p.add_argument("b", help="second exported graph JSON")
    p.add_argument("--expect", help=f"expectations YAML (default: {DEFAULT_EXPECT.relative_to(ROOT)} when present)")
    p.add_argument("--out", help="Markdown report path (default: results/graph_diff_<a>_vs_<b>.md); JSON twin alongside")
    p.set_defaults(func=cmd_diff)

    p = sub.add_parser("expectations-skeleton", help="write a starter expectations file from the world model",
                       description="High-importance nodes (people, systems, interfaces, programs writing reserve "
                                   "tables, process owners, versioned rules), edges (REPORTS_TO as of the world date, "
                                   "OWNS_PROCESS, WRITES_TO_TABLE, CALLS_PROGRAM, SUPERSEDES, interface source/target, "
                                   "RENAMED_TO), merge_expected from aliases and renames, must_not_merge from same-name "
                                   "people and must_not_exist for job titles as Person nodes. Exits 2 when the world "
                                   "model is not available.")
    p.add_argument("--out", default=str(DEFAULT_SKELETON), help="output YAML (default: questions/graph_expectations.draft.yaml)")
    p.add_argument("--as-of", help="override the world date used for time-dependent edges")
    common(p)
    p.set_defaults(func=cmd_skeleton)

    p = sub.add_parser("selftest", help="run the built-in tests on a synthetic graph in build/test_graph/")
    p.set_defaults(func=cmd_selftest)
    return ap


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())

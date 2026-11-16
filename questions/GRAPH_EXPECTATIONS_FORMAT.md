# Graph expectations format (`questions/graph_expectations.yaml`)

The knowledge graph built from the corpus should contain these nodes and edges, collapse these duplicates, and keep these look-alikes apart.
`harness/graph_audit.py` checks an exported graph against this file.
Type and relationship names are the hand-written schema's (`schemas/corvane_claims.jsonld`). The audit maps them case- and punctuation-insensitively, so `REPORTS_TO`, `reportsTo` and `PERSON_REPORTS_TO_PERSON` all match.

```yaml
version: 1
as_of: 2026-11-15

nodes:                       # entities that must exist (after alias merge)
  - id: GN001
    type: Person
    name: "Priya Raman"
    world_ref: P007
    match_any: ["Priya Raman", "P. Raman"]     # node name may be any of these
    evidence: [LD001-F120, TX004-F003]          # manifest fact ids that state it
    importance: high                            # high | medium | low

edges:                       # relationships that must exist
  - id: GE001
    type: REPORTS_TO
    from: {type: Person, match_any: ["Lena Holm"]}
    to:   {type: Person, match_any: ["Priya Raman", "P. Raman"]}
    as_of: 2026-11-15          # optional; time-dependent edges
    world_ref: P012.reports_to
    evidence: [VS014-F002]
    hops_role: "2nd hop of Q045"   # optional cross-reference to questions

merge_expected:              # different surface forms that should be ONE node
  - id: GM001
    type: Person
    canonical: "Priya Raman"
    variants: ["P. Raman", "PR", "Priya", "the CFO"]
    world_ref: P007

must_not_merge:              # same surface form, different entities
  - id: GX001
    type: Person
    name: "Daniel Okafor"
    distinct: [P021, P048]
    distinguishing: ["Claims Operations, Leeds", "Integration Architecture, Oslo"]

must_not_exist:              # nodes that would be hallucinations or misclassifications
  - id: GF001
    type: Person
    name: "Chief Financial Officer"     # a role, not a person
    reason: "role title extracted as a Person node"
```

## How graph_audit.py uses it

1. **Duplicates:** nodes of the same type whose normalised names collide, or that are known aliases of one world entity (via `world.worldlib.lexicon()`), and were not merged.
2. **Unmerged aliases:** each `merge_expected` group with more than one node present is reported.
3. **Wrong merges:** each `must_not_merge` group that collapsed into one node is reported.
4. **Missing nodes and edges:** `nodes` and `edges` not found are reported, with their evidence facts and the files those facts live in.
5. **Hallucinated nodes:** nodes whose name traces to no lexicon entry and no source text (fuzzy match ≥ 0.85 against names, aliases, IDs and glossary terms).
6. **Per-file coverage:** for each corpus file, the number of nodes and edges whose source file is that file, and the share of that file's manifest facts whose world entity is present.

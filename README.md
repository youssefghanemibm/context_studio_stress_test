# Corvane claims corpus: a ground-truthed stress test for knowledge-graph ingestion

**Scenario.** Corvane Mutual Insurance is a fictional P&C insurer with about 4,000 staff in the UK and the Nordics.
Its claims run FNOL → triage → assessment → reserving → fraud referral → settlement → recovery/subrogation.
Programme Skerry is moving claims off CLARA, a COBOL/CICS/DB2 mainframe, onto Claims Hub, Java/Spring services on OpenShift.
The documents span 2013–2026: manuals, policy wordings, regulator filings for the fictional regulator NISA, decks, diagrams, spreadsheets, tickets, transcripts, and a code repository.
Every fact was generated from one world model, so every answer is known and every planted fact has a machine-checked location.

The suite measures what a knowledge-graph / RAG product extracts from realistic, messy enterprise
material, and what it then answers correctly. It uses no product-specific knowledge. Everything in
it is fictional: no real client data, no real people, no copied documentation. Probe files carry
obviously fake PII and are labelled as test data.

## What is in it

<!-- COUNTS:START -->
- **223 upload files** (120 MB) in 13 accepted formats, plus **10 rejected-format files**.
- **4,319 planted facts** in `manifests/*.facts.yaml` (105 of them exclusive to one location), each with a machine-checked locator and needle.
- **253 questions** in `questions/questions.yaml` across 39 categories, each with evidence that resolves to a planted fact.
- **Graph expectations**: the nodes, edges, merges and non-merges a correct graph must contain (`questions/graph_expectations.yaml`).
- **A code repository in three variants** (real git history):
  - variant a: 429 files, 2.84 MB, 45 commits
  - variant b: 683 files, 3.24 MB, 46 commits
  - variant c: 430 files, 2.85 MB, 46 commits

| Folder | Files | MB |
|---|---|---|
| `corpus/upload/long_docs` | 30 | 77.9 |
| `corpus/upload/visuals` | 50 | 21.0 |
| `corpus/upload/structured` | 60 | 9.7 |
| `corpus/upload/text` | 75 | 11.1 |
| `corpus/upload/guardrail` | 8 | 0.1 |
| `corpus/rejected` | 10 | 1.6 |

| Type | Files | Total MB | Largest MB |
|---|---|---|---|
| `.txt` | 40 | 0.7 | 0.1 |
| `.md` | 31 | 0.1 | 0.0 |
| `.pptx` | 28 | 4.7 | 0.4 |
| `.pdf` | 24 | 82.1 | 37.7 |
| `.docx` | 22 | 11.3 | 1.6 |
| `.csv` | 15 | 7.2 | 2.5 |
| `.xlsx` | 13 | 0.7 | 0.3 |
| `.html` | 12 | 0.4 | 0.1 |
| `.json` | 12 | 10.5 | 9.5 |
| `.doc` | 8 | 0.7 | 0.1 |
| `.xml` | 8 | 1.1 | 0.4 |
| `.yaml` | 6 | 0.1 | 0.0 |
| `.yml` | 4 | 0.0 | 0.0 |
| `.bpmn` | 1 | 0.0 | 0.0 |
| `.eml` | 1 | 0.0 | 0.0 |
| `.jpg` | 1 | 0.2 | 0.2 |
| `.msg` | 1 | 0.0 | 0.0 |
| `.odt` | 1 | 0.0 | 0.0 |
| `.png` | 1 | 1.3 | 1.3 |
| `.rtf` | 1 | 0.0 | 0.0 |
| `.svg` | 1 | 0.0 | 0.0 |
| `.vsdx` | 1 | 0.0 | 0.0 |
| `.zip` | 1 | 0.0 | 0.0 |
<!-- COUNTS:END -->

## Coverage matrix

<!-- MATRIX:START -->
| Dimension | Corpus material | Categories | Questions |
|---|---|---|---|
| Long documents, long-range references | LD001 (496-page DOCX manual), LD012 (300 pages), LD003, LD013–LD030 | `needle_long_range` 5, `chunk_boundary` 4, `multipage_table` 4, `header_footer_footnote` 3, `docx_comment_tracked` 4, `table_row` 2 | **22** |
| Scanned and image-only pages | LD002 (the 496-page manual as an image-only scan), LD021 (photo atlas) | `scanned_ocr` 3 | **3** |
| Multi-column layout | LD003 (regulatory filing) | `multicolumn` 3 | **3** |
| Legacy binary formats | LD004–LD011 (.doc policy wordings, English and Nordic languages) | `legacy_doc` 6 | **6** |
| Visual semantics | VS001–VS050: decks, raster diagrams, charts, screenshots, speaker notes, alt text | `visual_arrow` 7, `visual_lane` 4, `visual_raster` 5, `visual_chart` 6, `visual_image_table` 4, `visual_screenshot` 4, `visual_grouped_rotated` 3, `speaker_notes` 3, `alt_text` 1 | **37** |
| Structured data and scale | ST001–ST060: XLSX (hidden sheets, merged cells), CSV up to 15,000 rows, JSON, XML, YAML, wiki HTML | `structured_lookup` 9, `aggregation_count` 7, `negation` 6, `hidden_merged` 4, `scale` 6 | **32** |
| Entity resolution and terminology | aliases, initials, role references, namesakes, renamed people; documents in non-schema terms | `entity_resolution` 9, `terminology` 4, `duplicate_merge` 2 | **15** |
| Conflicts and time | 17 planned contradictions; as-of facts; renamed systems and services | `contradiction` 23, `temporal` 13, `rename` 9 | **45** |
| Multi-hop and impact analysis | chains across documents, data, diagrams and code | `multi_hop` 31, `impact_analysis` 11 | **42** |
| Code connector | variant a (COBOL/JCL/BMS/DDL + Java/Terraform/k8s/ADRs), b (oversize, canaries), c (follow-up commit) | `code_fact` 10, `code_history` 6, `truncation_canary` 6, `resync` 5 | **27** |
| Guardrails | GP001–GP008: labelled fake PII, one embedded instruction | `guardrail_pii` 4, `guardrail_injection` 2 | **6** |
| Format rejection and abstention | RJ001–RJ010 (refused formats); facts not in the corpus | `rejected_format` 10, `unanswerable` 5 | **15** |
| Nondeterminism | the same 223 files in two batch orders (A by family, B interleaved) | every question, asked in both contexts; graph diff | 253 × 2 |

Ask modes: chat 227, graph 20, vector 6. Hops: 1-hop 139, 2-hop 68, 3-hop 22, 4-hop 19, 5-hop 4, 8-hop 1. Difficulty: medium 153, hard 68, easy 32.
<!-- MATRIX:END -->

## Layout

```
corpus/upload/        the files to upload, by family: long_docs, visuals, structured, text, guardrail
corpus/rejected/      10 files in formats a typical product refuses (.vsdx .bpmn .msg .eml .rtf .odt .png .jpg .svg .zip)
batches/              the upload plan: order_A.csv, order_B.csv, BATCHES.md (8 batches each, <=30 files, <100 MB)
questions/            questions.yaml (generated from parts/), CATEGORIES.md, WRITING_GUIDE.md,
                      graph_expectations.yaml (nodes, edges, merges a correct graph must contain)
manifests/            *.facts.yaml: every planted fact with file, locator, needle, exclusivity; files.csv inventory
schemas/              the hand-written schema (JSON-LD, Turtle, RDF/XML), terminology variants, schema-assistant prompt
world/                the world model: data/*.yaml (people, systems, programs, rules, contradictions, placements…),
                      build_world.py, validate_world.py, worldlib.py (as-of helpers), WORLD.md
generators/           one generator per family + code_legacy, code_modern and the code-repo assembler
harness/              extract, build_index, verify_corpus, make_batches, score, graph_audit, merge_questions,
                      make_perfect_export, publish_code_repos.sh, tests/
baseline/             the plain-agent baseline protocol and scripts
results/              answer sheets, scores and audits (results/runs/ holds raw run files)
build/notes/          per-family generator notes: sizes, deliberate deviations, what is unverified
                      (the rest of build/ is regenerable and not committed)
generate.py           rebuild everything from the world model
RUNBOOK.md            the test procedure, step by step
docs/CONVENTIONS.md   the generator contract (naming, determinism, facts-manifest schema, locator kinds)
```

The code corpus isn't stored on `main`. It is built into `build/code_repo/variant_{a,b,c}`, which
are real git repositories with dated, authored history, and published as the orphan branches
`client-codebase` (a, ~430 files), `client-codebase-oversize` (b, ~680 files) and
`client-codebase-followup` (c, a + one follow-up commit), by `harness/publish_code_repos.sh`.

## How to run the test

Follow [RUNBOOK.md](RUNBOOK.md):
1. Import the schema.
2. Load two contexts with the two batch orders.
3. Connect the code repository.
4. Export the graphs and audit them.
5. Ask the questions and score them.
6. Run the re-sync test.
7. Run the baseline.

## How to regenerate

```bash
uv venv .venv --python 3.13
```

```bash
uv pip install --python .venv/bin/python -r requirements.lock.txt
```

```bash
.venv/bin/python -I generate.py
```

`generate.py` builds the world model and validates it. It then runs the family generators in
parallel and assembles the code repositories. Finally it writes the batches, builds the full-text
index (OCR included, via Apple Vision on macOS) and runs `harness/verify_corpus.py`. The run should
end with 0 FAIL.

- `--only visuals,text` regenerates selected families.
- `--no-ocr` skips OCR on other platforms.
- Regenerating needs LibreOffice (`soffice`).

The questions are written by hand against the generated corpus, in `questions/parts/*.yaml`.
`harness/merge_questions.py` merges them into `questions/questions.yaml`.
`verify_corpus.py --checks 2` proves that every evidence item resolves, and
`score.py keycheck` proves that every expected answer scores as correct.
Every question part was also reviewed by an independent adversarial verifier, which tried to
refute each answer against the corpus and the world model, and the fixes were applied.

`harness/make_perfect_export.py` builds a perfect graph from the world model alone. Auditing it with
`harness/graph_audit.py audit build/perfect_export.json --expect questions/graph_expectations.yaml`
must report 0 missing nodes and edges, 0 unmerged aliases and 0 wrong merges. This proves the graph
expectations are consistent with the world.

**Determinism.** The same inputs give the same files, byte for byte. There are two exceptions:
- The three PDFs exported through LibreOffice (LD025, LD027, LD028) differ at byte level between
  runs; their extracted text is identical.
- Page numbers in `page_hint` locators come from LibreOffice's pagination; Word may paginate DOCX
  files slightly differently.

## Verification status

<!-- VERIFY:START -->
`.venv/bin/python -I harness/verify_corpus.py` on the committed corpus:

| Check | PASS | WARN | FAIL |
|---|---|---|---|
| index | 1 | 0 | 0 |
| facts | 4313 | 6 | 0 |
| questions | 253 | 0 | 0 |
| exclusivity | 101 | 4 | 0 |
| inventory | 1 | 1 | 0 |
| rejected | 10 | 0 | 0 |
| denylist | 2 | 0 | 0 |
| secrets | 1 | 0 | 0 |
| guardrail | 2 | 0 | 0 |
| batches | 3 | 0 | 0 |

The WARNs are heuristic. Some facts keep their planned kind (e.g. `chart_only`) in a raster or PDF file, and a few needles are short. Every one was reviewed.

**Not verified:**
- DOCX and PPTX rendering in Microsoft Office: only LibreOffice was used.
- The COBOL, JCL, Java and Terraform: never compiled or run.
- The handwriting in the whiteboard photos: a jittered font, not real handwriting.
- Scoring is word-based. A correct answer that mentions an old value without a cue such as
  "previously" can score partial, so reviewers check partial and wrong verdicts and use `override`
  (`questions/WRITING_GUIDE.md`).
- Five independent contradiction hunters swept people, systems, rules, code and process across all files.
  Their 29 substantive findings were fixed at the generators. A few low-impact world-design limitations
  remain and are documented in `build/notes/*.md` (one file per generator family, with every deliberate
  deviation). For example, table columns carry no history, so older documents show today's column list.
<!-- VERIFY:END -->

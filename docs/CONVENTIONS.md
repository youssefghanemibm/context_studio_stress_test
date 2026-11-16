# Generator conventions (the contract every generator follows)

Every artifact in this suite is generated, deterministically, from the world model in `world/`.
This page is the contract between the world model, the generators, the answer key and the harness.
If you write a generator, follow it exactly. If something here is impossible, write a note in
`build/notes/<family>.md` and do the closest compliant thing. Don't silently diverge.

## 1. Fiction rules (hard)

- **Everything is fictional.** The client is Corvane Mutual Insurance, a mid-size UK and Nordic P&C insurer with about 4,000 staff.
  - The legacy system is CLARA (Claims Ledger And Reserve Application: COBOL/CICS/DB2).
  - The target is Claims Hub (Java/Spring on OpenShift).
  - The regulator is the National Insurance Supervisory Authority (NISA).
- **No real people, no real client data, no real companies.**
  - Vendors, law firms, loss-adjusting firms and banks are invented. Check new names against `world/data/names_denylist.yaml`.
  - Generic technology names are fine: IBM z/OS, CICS, DB2, Java, Spring, OpenShift, Kafka, Terraform, PostgreSQL.
- **No copied IBM documentation text.**
- **No statements about IBM Context Studio's internals anywhere in generated content or repo docs.** That means no limits, no known issues, no benchmarks. The corpus is about Corvane; it must not mention Context Studio at all.
- Email domains: staff use `@corvane-mutual.example`, IBM team members use `@ibm-consulting.example`, vendors use `<vendor>.example`. Phone numbers use the 555 pattern or the UK drama range `07700 900xxx`.
- **Real-looking PII appears only in the clearly labelled guardrail-probe files.** Even there it must be *obviously fake*: example.com emails, 555 numbers, invalid ID formats such as `QQ 12 34 56 C` or 9xx-xx-xxxx.
- **The single prompt-injection string lives only in the one designated guardrail file.**
- **No secret-looking strings** (API keys, tokens, private keys, AWS-style keys) anywhere. A secret scanner runs on every commit. For placeholders, write `<REDACTED>` or `changeme-not-a-secret`.

## 2. Paths and naming

```
world/data/*.yaml              world model (single source of truth)
world/worldlib.py              loader: `from world.worldlib import load_world; W = load_world()`
generators/<family>/generate.py one entry point per family (see §4)
generators/common/util.py      shared helpers (rng, dates, fonts, manifest writer)
corpus/upload/<family>/        upload corpus (accepted types only)
corpus/rejected/               rejected-format set
build/code_repo/...            generated code repos (git), pushed to orphan branches
manifests/<family>.facts.yaml  planted facts with exact locators (see §5)
build/                         scratch, caches, notes (gitignored)
```

- **Families and file-ID prefixes:**

  | Prefix | Family | Folder |
  |---|---|---|
  | `LD` | long documents | `long_docs` |
  | `VS` | slides and visuals | `visuals` |
  | `ST` | spreadsheets and structured | `structured` |
  | `TX` | transcripts, tickets, email-like text | `text` |
  | `GP` | guardrail probes | `guardrail` |
  | `RJ` | rejected formats | `corpus/rejected` |

  The code repos have no prefix: they use natural repo paths.
- **Upload file names:** `<PREFIX><NNN>_<slug>.<ext>`, for example `LD001_claims_handling_manual_v7_2.docx`.
  - NNN is unique within the prefix. The slug is lowercase ascii with underscores, ≤ 60 characters.
  - The ID ranges are reserved in `world/data/corpus_plan.yaml`.
- **Accepted upload extensions only:** `.docx .doc .md .xlsx .txt .json .csv .pdf .pptx .xml .html .yaml .yml`.
- **Size caps:**
  - Every file stays < 48 MB, because of GitHub's 50 MB warning.
  - The whole upload corpus stays ≤ 350 MB. Your family's budget is in `corpus_plan.yaml`.

## 3. Python, determinism, environment

- Use the repo venv: `.venv/bin/python`. Install nothing globally. If you truly need a package, use `~/.local/bin/uv pip install --python .venv/bin/python <pkg>` and record it in `build/notes/<family>.md`.
- Run Python that reads generated files with `-I`.
- `-I` means the script directory is NOT on `sys.path`. So every script starts with:
  ```python
  import sys, pathlib
  ROOT = pathlib.Path(__file__).resolve().parents[2]   # adjust depth so ROOT = repo root
  sys.path.insert(0, str(ROOT))
  ```
- **Determinism:**
  - All randomness comes from `generators.common.util.rng(key)`, a `random.Random` seeded from `sha256(GLOBAL_SEED + key)`.
  - Never use the wall clock. Document dates come from the world model; file metadata uses `util.FIXED_DT`.
  - Set DOCX/PPTX/XLSX core properties: created/modified = the document's world date, author = a world person name.
  - For reportlab use `invariant=1`.
  - Content must be identical across runs (extracted text identical). Byte-identical is a bonus.
- **No network access in generators.**
- LibreOffice: `/opt/homebrew/bin/soffice --headless --convert-to <fmt> --outdir <dir> <file>`.
  - Use a per-call profile so parallel runs don't collide: `-env:UserInstallation=file:///tmp/lo_<family>_<n>`.
  - macOS has no `timeout` command. Use `subprocess.run(..., timeout=...)`.
- Fonts for raster images: use `generators.common.util.font(size, bold=False)`, which returns DejaVu Sans from matplotlib's bundled fonts. Don't rely on system fonts.
- OCR, for self-checking image text: `from ocrmac import ocrmac; ocrmac.OCR(path).recognize()` (Apple Vision, local). Render image text at ≥ 14 px cap height and with high contrast, so OCR (and the product) can read it.

## 4. Generator entry point

Each family has `generators/<family>/generate.py` with:

```
python -I generators/<family>/generate.py [--out corpus/upload/<family>] [--only <FILEID,...>]
```

- It is idempotent: it clears and rewrites only its own output folder and its own `manifests/<family>.facts.yaml`.
- It finishes by printing one summary line per file: `<file> <bytes> <pages|slides|rows>`.
- It must run with no arguments.
- It must finish in < 20 minutes on a laptop. Long documents may use caching in `build/cache/<family>/`.
- The top-level `generate.py` calls the family generators in this order: world → families (they may run in parallel) → code repos → manifests merge → index → verify.

## 5. Facts manifest (what you planted and exactly where)

Every family writes `manifests/<family>.facts.yaml`, a YAML list. Each entry:

```yaml
- fact_id: LD001-F017            # <FILEID>-F<nnn>, unique
  world_ref: BR-FRD-012@v2       # what in the world model this expresses (entity id, field, version)
  kind: needle                   # see the kinds list below
  statement: "Fraud referral threshold is a Sentinel score of 65 or more from 2026-10-01."
  file: corpus/upload/long_docs/LD001_claims_handling_manual_v7_2.docx
  locator: {kind: docx_para, para_index: 4120, page_hint: 411, section: "28.3 Referral to SIU"}
  needle: "score of 65 or more"   # exact substring at the locator (whitespace-normalised, case-insensitive match)
  exclusive: true                # true = this fact appears in NO other file (except files listed in also_in)
  also_in: []                    # other fact_ids that deliberately state the same fact
  notes: "definition of 'Sentinel score' is LD001-F003, ~380 pages earlier"
```

- **`kind`**: `needle`, `definition`, `use_of_definition`, `split_boundary`, `multipage_table`, `visual_only`, `arrow_only`, `lane_only`, `chart_only`, `image_text`, `image_table`, `screenshot`, `speaker_notes`, `alt_text`, `comment`, `tracked_insert`, `tracked_delete`, `header`, `footer`, `footnote`, `hidden_sheet`, `merged_cell`, `contradiction_old`, `contradiction_new`, `draft`, `approved`, `alias_use`, `terminology`, `temporal`, `aggregate_source`, `code_fact`, `commit_fact`, `canary`, `resync_change`, `pii_probe`, `injection_probe`, `rejected_format_fact`, `scale`, `general`.
- **Plant at least the facts `world/data/placements.yaml` assigns to your files.** Add more of your own if you like. Every planted fact needs a manifest entry.
- **A fact marked `exclusive: true` must not be derivable from any other file.** Generic text generators must call `W.is_exclusive(entity_id, field)` (or read the exclusivity lists) before stating a field.

### Locator kinds (the verifier resolves these)

| kind | fields | meaning |
|---|---|---|
| `pdf_page` | page (1-based), `ocr: bool` | text layer of that page; with `ocr: true` the page is OCRed |
| `docx_para` | para_index (0-based over `document.paragraphs`), section, page_hint | body paragraph |
| `docx_table` | table_index, row, col | cell in `document.tables[table_index]` |
| `docx_comment` | comment_id | comment text |
| `docx_footnote` | footnote_id | footnote text |
| `docx_header` / `docx_footer` | section_index | header or footer text of that section |
| `docx_tracked` | type: ins\|del, index | nth `w:ins` or `w:del` run text |
| `docx_image` | image_name (word/media/…), `ocr: true` | text inside an embedded image |
| `docx_alt_text` | image_index | `descr` attribute of the nth drawing |
| `pptx_slide` | slide (1-based), where: text\|notes\|table\|chart\|alt_text\|group\|connector\|image, shape_name?, `ocr`? | |
| `xlsx_cell` | sheet, cell (A1), hidden?: bool | |
| `xlsx_chart` | sheet, chart_index | data in the chart's cached series/categories |
| `csv_row` | row (1-based, header excluded), column | |
| `json_pointer` | pointer (RFC 6901) | |
| `xml_xpath` | xpath (no namespaces, or `local-name()`) | |
| `yaml_path` | path like `paths./claims/{id}.get.summary`, doc_index (for multi-doc) | |
| `html_xpath` | xpath | |
| `text_lines` | start, end (1-based, inclusive) | .txt or .md |
| `image_ocr` | (standalone image file) | OCR of the whole image |
| `code_lines` | variant: a\|b\|c, path, start, end | file in a generated code repo |
| `git_commit` | variant, message_contains | commit message or author in a code repo's history |

- **Use `harness/extract.py`** (`resolve(file, locator) -> str`) to self-check that every needle resolves before you finish. Run `python -I harness/verify_corpus.py --family <family>`.
- For `pptx_slide`/`where: connector`, the resolved text describes the connector, e.g. `"Decision: Fraud score ≥ 65? -> Refer to SIU [label: Yes]"`. The extractor builds it from the begin/end connections and any label shape. That's how "meaning only in the arrows" facts are verified.

## 6. World model access

- Load it with `from world.worldlib import load_world`. Read `world/WORLD.md` for the entity sets, ID formats, the traps and which family plants what.
- Never invent facts that contradict the world model.
- Filler prose is fine. Filler must not state anything about world entities that isn't in the world model.
- Prose may invent harmless colour, such as meeting-room names or weather, but never a new rule, threshold, owner, date, system link or program-table link.
- Contradictions exist only where `world/data/contradictions.yaml` plans them.
- Aliases and terminology variants are used where `world/data/placements.yaml` and `glossary.yaml` say so.

## 7. Question format (`questions/questions.yaml`)

```yaml
- id: Q001
  category: needle_long_range        # one of the categories in questions/CATEGORIES.md
  dimensions: [long_doc, chunk_boundary]
  question: "What is the reserve review cadence for Tier-3 claims?"
  expected_answer: "Every 14 days."
  acceptable_variants: ["fortnightly", "every two weeks"]
  must_include: [["14 days", "fortnight", "two weeks"]]   # AND of ORs, case-insensitive
  must_not_include: ["30 days"]                           # stale or trap answers
  evidence:
    - {fact_id: LD001-F044}                                # preferred: reference a manifest fact
    - {file: ..., locator: {...}, needle: "..."}           # or inline
  hops: 2
  ask_mode: chat                      # chat | graph | vector
  difficulty: medium                  # easy | medium | hard
  world_refs: [RULE:BR-RSV-007@v3]
  trap: "the v6.1 manual says 30 days"
```

## 8. Done checklist for a generator family

1. `python -I generators/<family>/generate.py` runs clean from scratch, twice, with identical extracted text.
2. `manifests/<family>.facts.yaml` validates, and every needle resolves (`harness/verify_corpus.py --family`).
3. File counts per extension meet the quota in `corpus_plan.yaml`. Sizes are within budget.
4. `build/notes/<family>.md` lists: the files and what each tests, anything unverified, and deviations.

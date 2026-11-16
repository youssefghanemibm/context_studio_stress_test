# Question categories

Every question in `questions.yaml` has exactly one `category` from this list and one or more `dimensions`.
`hops` counts the distinct facts that must be joined; a single lookup is 1.

| category | what it tests | typical ask_mode |
|---|---|---|
| `structured_lookup` | one value from a CSV, XLSX, XML, JSON, YAML or HTML record | chat |
| `table_row` | a value that only makes sense with its table header and row (DOCX/PDF tables) | chat |
| `aggregation_count` | counting, summing or averaging over many rows or records | chat |
| `negation` | "which X do NOT …", "is there any …", with the answer "none" or a complement set | chat |
| `needle_long_range` | a definition hundreds of pages away from where it is used | chat |
| `chunk_boundary` | a fact split across a page break, heading or paragraph boundary | vector |
| `multipage_table` | a row of a table that spans several pages (header only on page 1) | chat |
| `visual_arrow` | flowchart meaning carried only by connectors and their labels | chat |
| `visual_lane` | swimlane ownership carried only by lane position | chat |
| `visual_raster` | text or arrow labels that exist only as pixels in a diagram | chat |
| `visual_chart` | values that exist only in a native chart | chat |
| `visual_image_table` | a table rendered as an image | chat |
| `visual_screenshot` | values visible only in a UI screenshot | chat |
| `visual_grouped_rotated` | text in grouped shapes, SmartArt-style layouts or rotated text boxes | chat |
| `speaker_notes` | facts only in slide speaker notes | chat |
| `alt_text` | facts only in image alt text | chat |
| `docx_comment_tracked` | facts only in DOCX comments or tracked insertions/deletions | chat |
| `header_footer_footnote` | facts only in headers, footers or footnotes | chat |
| `hidden_merged` | hidden worksheets, merged cells | chat |
| `scanned_ocr` | facts only in the image-only scanned PDF | chat |
| `multicolumn` | facts whose reading order depends on a multi-column layout | chat |
| `legacy_doc` | facts only in legacy binary .doc files | chat |
| `entity_resolution` | aliases, initials, role references, two people with the same name | graph |
| `terminology` | documents use a different word from the schema term | chat / graph |
| `contradiction` | conflicting sources: newer vs older, draft vs approved, stale chart | chat |
| `temporal` | the answer depends on an as-of date | chat |
| `rename` | systems, programs or services renamed over time | chat / graph |
| `multi_hop` | 2–5 hop chains across files and file types | graph / chat |
| `impact_analysis` | downstream dependency traversal (interfaces, programs, tables) | graph |
| `code_fact` | facts from the connector-ingested code repo | chat / graph |
| `code_history` | commit history: renames, fixes citing ticket IDs, authors | chat |
| `truncation_canary` | facts placed in files that only an untruncated oversize repo would include | chat |
| `resync` | facts changed by a follow-up commit after first ingestion | chat |
| `scale` | questions over the 15,000-row claims extract or other high-cardinality data | chat / graph |
| `duplicate_merge` | the same fact from two files should collapse to one entity | graph |
| `guardrail_pii` | handling of obviously fake PII in labelled probe files | chat |
| `guardrail_injection` | whether an embedded instruction is flagged or obeyed | chat |
| `rejected_format` | facts that live only in rejected-format files (expected: not answerable) | chat |
| `unanswerable` | facts that are not in the corpus at all (expected: "not found") | chat |

## Dimensions (free tags, use several)

`long_doc`, `scanned`, `multicolumn`, `legacy_doc`, `visual`, `pptx`, `docx`, `pdf`, `xlsx`, `csv`, `json`, `xml`, `yaml`, `html`, `txt`, `md`, `code`, `connector`, `chunk_boundary`, `needle`, `alias`, `same_name`, `terminology`, `contradiction`, `temporal`, `draft_vs_approved`, `stale_chart`, `rename`, `multi_hop`, `aggregation`, `negation`, `scale`, `guardrail`, `rejected`, `nondeterminism`.

## ask_mode

- `chat`: ask in the product's chat ("talk to the context") and score the free-text answer.
- `graph`: check the knowledge graph directly (graph view or graph-query tools). The expected answer is a node or edge set.
- `vector`: ask the semantic/vector search; score whether the right passage is retrieved and whether it is cut.

## Scoring

`harness/score.py` gives:
- **correct**: every `must_include` group matches, no `must_not_include` matches, and nothing contradicts the key.
- **partial**: some `must_include` groups match, or the answer is right but names the stale entity too.
- **wrong**: a `must_not_include` matches, or no group matches.
- **refused / not found**: correct only for `rejected_format` and `unanswerable`.

A human can override any score in the results file (`override:` field).

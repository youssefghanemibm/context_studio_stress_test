# RUNBOOK: running the suite against a knowledge-graph product

This page is the test procedure, step by step. Steps marked **(you)** happen in the product's web UI
and need a person; everything else is a script. Run every script from the repo root with
`.venv/bin/python -I`.

Keep product-specific facts (limits, endpoints, internal behaviour) in your own gitignored
`NOTES.local.md`, not in this repo.

## 0. Set up

```bash
uv venv .venv --python 3.13
```

```bash
uv pip install --python .venv/bin/python -r requirements.lock.txt
```

You need LibreOffice (`soffice`) only to **regenerate** the corpus. Running the tests doesn't need it.
OCR checks use Apple Vision (`ocrmac`, macOS only). Pass `--no-ocr` elsewhere; the image-only
facts are then reported as SKIP rather than verified.

Optional: prove that the committed corpus matches the generators and that every fact verifies.

```bash
.venv/bin/python -I generate.py
```

This takes about 5 minutes with warm caches. Expect `verify` to end with 0 FAIL;
`build/verify_report.json` has the detail.

## 1. Prepare the upload batches

```bash
.venv/bin/python -I harness/make_batches.py --materialize
```

This writes `batches/materialized/order_A/batch_NN/` and `batches/materialized/order_B/batch_NN/` as hard links.
Each batch holds at most 30 files and stays under 100 MB. `batches/BATCHES.md` lists every batch.
The two orders hold the same files, but group them differently.

## 2. Create the contexts (you)

Create four contexts. Each uses the same schema, imported from
`schemas/corvane_claims.jsonld` (or `.ttl` / `.rdf`; all three are equivalent).

| Context | Holds | Purpose |
|---|---|---|
| **A** | upload batches in order A + code repo variant a | main run |
| **B** | upload batches in order B + code repo variant a | nondeterminism: same inputs, different grouping |
| **C** | code repo variant b only | completeness of a large repository (truncation canaries) |
| **P** | throwaway | probe the GitHub URL form and the rejected formats before loading A |

To test the product's schema assistant as well, create one more context. Generate its schema from
`schemas/schema_assistant_prompt.md`, then compare the result with `corvane_claims.jsonld`
(`schemas/README.md` explains how).

## 3. Probe first, in context P (you)

1. **Rejected formats.** Try to upload every file in `corpus/rejected/` (10 files: .vsdx .bpmn
   .msg .eml .rtf .odt .png .jpg .svg .zip). Record which ones are refused, and with what message,
   in `results/runs/rejected_formats.csv`. Any file that is accepted needs a note: the
   `rejected_format` questions assume it was not ingested.
2. **GitHub URL form.** Publish the code repos first (step 5), then add a GitHub connector to P with
   the branch URL `https://github.com/<owner>/<this-repo>/tree/client-codebase`.
   - When ingestion finishes, check which files it took. You should see `legacy/clara/…`,
     `services/…`, `infra/…`, `deploy/…` and nothing from `questions/`, `world/`, `manifests/`
     or `corpus/`.
   - **If any suite file shows up, the branch part of the URL was ignored.** Delete context P and
     never point a connector at this repo again; it contains the answer key. Use separate
     repositories instead: create two empty repositories on GitHub yourself, then
     `harness/publish_code_repos.sh repos <owner>`.

## 4. Load contexts A and B (you)

For each batch, in order (`order_A/batch_01`, `order_A/batch_02`, … into context A; `order_B/…` into context B):

1. Drag every file of the batch folder into the upload dialog, all at once.
2. Wait until the product reports the batch as ingested.
3. Add a row to `results/runs/ingest_log.csv`:
   `context,batch,files,mb,started_at,finished_at,status,notes`. Use the batch's file count and MB
   from `batches/BATCHES.md`, and copy any error text exactly.

Then add the GitHub connector to A and B with the code URL from step 3 (branch URL or separate
repository) and log it the same way (`batch` = `github_a`).

Load context C with the oversize variant only: `…/tree/client-codebase-oversize`, or the
`corvane-claims-codebase-oversize` repository.

## 5. Publish the code repositories

The code corpus is built into `build/code_repo/variant_{a,b,c}` (`generators/code_repo/assemble.py`;
`generate.py` runs it). Each variant is a real git repository with dated, authored history.

| Variant | Files | What it tests |
|---|---|---|
| a | ~430 | the main code corpus: COBOL/JCL/BMS/DDL plus Java/Terraform/k8s/ADRs |
| b | ~680 | a + extra folders holding six canary facts (`truncation_canary` questions) |
| c | a + 1 commit | a follow-up commit, pushed later (`resync` questions) |

Publish them as orphan branches of this repository:

```bash
harness/publish_code_repos.sh branches
```

Or, if step 3 showed that branch URLs are ignored, publish them to two separate repositories that
you created:

```bash
harness/publish_code_repos.sh repos <owner>
```

`harness/publish_code_repos.sh status` shows what is published.

## 6. Export the graphs (you + script)

After each context has finished ingesting, save its full graph or ingestion response as JSON:
`results/runs/ctxA_export.json`, `ctxB_export.json` and `ctxC_export.json`. Your local notes say
how to get the export for the product you're testing. Then run:

```bash
.venv/bin/python -I harness/graph_audit.py audit results/runs/ctxA_export.json --expect questions/graph_expectations.yaml --label ctxA
```

```bash
.venv/bin/python -I harness/graph_audit.py diff results/runs/ctxA_export.json results/runs/ctxB_export.json --expect questions/graph_expectations.yaml
```

The audit reports duplicate entities, unmerged aliases, wrong merges (the namesakes), missing
expected nodes and edges, hallucinated nodes, per-file coverage, roles extracted as people, and how
many relationships stayed generic. The diff measures how much A and B agree.

## 7. Ask the questions (you)

Create one answer sheet per context and ask mode:

```bash
.venv/bin/python -I harness/score.py template --label ctxA_r1 --context A
```

- Ask each question **verbatim**, in a fresh chat where the product allows it.
  - `ask_mode: chat`: the product's chat/assistant.
  - `ask_mode: graph`: the graph query feature. The expected answer is a node or edge set.
  - `ask_mode: vector`: plain retrieval / search, if offered.
- Paste the answer verbatim into the `answer` field.
  - Put the seconds from pressing Enter to the complete answer in `latency_s`.
  - Copy any cited files into `cited_sources`.
- Questions with `variant: b` are asked in **context C**.
- Questions with `variant: c` are asked **after** the re-sync step (§8).
- Score the sheet:

```bash
.venv/bin/python -I harness/score.py score results/runs/ctxA_r1.yaml
```

Verdicts are correct, partial, wrong, refused or unanswered. A reviewer can set `override` on a
question; `questions/CATEGORIES.md` has the rules.

Then compare A and B (and any repeat run):

```bash
.venv/bin/python -I harness/score.py compare results/ctxA_r1_score.json results/ctxB_r1_score.json
```

## 8. Re-sync test

This runs after A has been fully loaded, exported and asked. It pushes variant c (one follow-up
commit, a fast-forward) to the branch or repository that context A is connected to:

```bash
harness/publish_code_repos.sh resync-branch
```

Use `harness/publish_code_repos.sh resync-repo <owner>` instead if you are on separate
repositories.

Wait at least an hour, and use any refresh or re-sync control the product offers (record whether
one exists). Then ask the `variant: c` questions in context A. If the product never picks up the
commit, the expected result is the **pre-commit** answer, which those questions list in
`must_not_include`. That's the finding.

## 9. Baseline

Run the same questions with a plain agent that has only file tools, over exactly the same inputs:
see `baseline/BASELINE_PROTOCOL.md`. Then compare the scores:

```bash
.venv/bin/python -I harness/score.py compare results/baseline_r1_score.json results/ctxA_r1_score.json
```

## 10. Guardrails

`guardrail_*` questions check whether the product:
- repeats synthetic PII (fake account numbers and IDs, all labelled as test data);
- follows an instruction embedded in a document (GP002);
- flags those files.

Also note whether the product warned about PII at upload time, and record it in
`results/runs/ingest_log.csv`.

## What to keep

Commit `results/` (answer sheets, scores, audits, ingest logs). Don't commit raw exports if they
contain anything internal to the product; keep those under `local/`.

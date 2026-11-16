# Baseline protocol: a plain agent with file tools

**The question.** Can a plain Claude agent that has only file-system tools, working over the same corpus,
answer the same questions as the product? How accurately, how fast, and with how many tool calls?

The baseline is the reference point for every product result. When the product scores 70% on a
category and the baseline scores 95%, the gap belongs to the product's ingestion and retrieval, not
to the corpus or the questions. When both fail, the question or the corpus is suspect.

This page is the protocol. `baseline/WORKFLOW_EXAMPLE.md` walks through a run, and
`baseline/agent_prompt.md` holds the exact prompts. Every step is scripted:

| Step | Script | Output |
|---|---|---|
| Build the sandbox | `baseline/prepare_sandbox.py` | `<sandbox>/documents/`, `<sandbox>/code_repo/`, `<sandbox>.manifest.json` |
| Check the sandbox | `baseline/prepare_sandbox.py --check` | pass/fail (run before every batch) |
| Split the questions and render the prompts | `baseline/questions_for_agent.py` | `QUESTIONS_ONLY*.md` in the sandbox; `build/baseline_runs/<label>/` |
| Per-question timings from transcripts | `baseline/timings_from_transcript.py` | rows in `timings.csv` |
| Merge and score | `baseline/collect_results.py` → `harness/score.py score` | `results/runs/baseline_<label>.yaml`, `results/baseline_<label>_score.md`, `results/baseline_<label>_efficiency.md` |
| Compare with the product | `harness/score.py compare` | `results/compare_<...>.md` |
| Pipeline self-test | `baseline/test_pipeline.py` | `build/test_baseline/` (a dummy corpus, end to end) |

Run every script with `.venv/bin/python -I` (docs/CONVENTIONS.md §3).

## 1. What is measured

| Per question | How it is recorded |
|---|---|
| Answer | the agent's `answer` field, verbatim |
| Cited files and locations | `cited_sources`: `documents/<file> :: <page / slide / sheet!cell / section / lines>` or `code_repo/<path> :: lines a-b` |
| Wall-clock seconds | the runner measures it, never the agent (§6.3) |
| Tool calls | the runner counts them from the transcript or its usage report (§6.3) |
| Tokens | input (cached included) and output, when the runner exposes them |
| Verdict | `harness/score.py`: correct, partial, wrong, refused or unanswered |

Per run: accuracy and score by category, dimension, ask mode, difficulty and hops (from `score.py`).
`collect_results.py` adds total wall-clock, all-in seconds per question, the median and p90 answering
time, total tool calls and tool calls per question, tokens, and the preparation cost (prepared mode).

## 2. The sandbox

### Contents

`prepare_sandbox.py` builds the sandbox (default `build/baseline_sandbox/`). It holds exactly the
inputs the product was given, and nothing else:

```
<sandbox>/
  documents/      every accepted upload file of corpus/upload/**, flattened (file names only)
  code_repo/      the code repository the product was connected to (default: build/code_repo/variant_a),
                  its working tree plus its history, from a single-branch clone
  QUESTIONS_ONLY.md, QUESTIONS_ONLY_batch_NN.md     added later by questions_for_agent.py
  _scratch/batch_NN/   created by the agent while it works; wiped between batches
  _notes/         prepared mode only: the preparation session's notes, read-only afterwards
```

**Excluded:** `world/`, `manifests/`, `questions/` (the answer key), `generators/`, `harness/`,
`results/`, `batches/`, notes (`*.local.md`, `build/notes/`), `corpus/rejected/`, and the other
code-repo variants. The rejected-format files are excluded because the product never ingested them.
The `rejected_format` questions expect "not found" from both systems.

### Decisions

- **Flattened documents.** The product receives files, not the corpus's family folders. Folder names
  such as `guardrail` would tell the agent something the product never sees. File names, family
  prefixes included, are kept because the product sees them too. A name collision stops the build.
  `--keep-folders` overrides the flattening, and the run must say so.
- **Git history is included.** The product is pointed at a repository, and a repository carries its
  history. The `code_history` category asks about commits, ticket references and authors. Without
  `.git`, the baseline could not answer those questions by construction, and the comparison would
  measure what each system was given rather than what it can do. To prevent leaks, the sandbox gets a
  **fresh single-branch clone** (`git clone --single-branch --no-hardlinks file://...`) of the source's
  checked-out branch:
  - It holds only the objects reachable from that branch, so no other variant's branches or objects
    come along. A plain copy or a local clone would carry the whole object store.
  - The remote is removed, so no path back to the repository remains.
  - Reflogs are deleted, because they name the source path.
  - The leak check asserts one branch, no remotes and no other refs.

  `--no-git-history` builds a working-tree-only sandbox. Use it only to measure the effect of history,
  and label the run accordingly.
- **The code variant matches the product context.** The default is variant a, the repository the main
  product context is connected to. Two categories presuppose other variants:
  - `truncation_canary` facts live only in the oversize variant.
  - `resync` facts change in a later commit.

  With variant a, the baseline cannot answer these by design. Report those two categories separately
  from the headline. To compare a product context that was connected to another variant, build a
  separate sandbox with `--code-repo build/code_repo/variant_b` (or `variant_c`) and give it its own run
  label.
- **Copies, read-only.** Corpus files are copied (never hard-linked, so the agent can't alter the
  originals) and their write bits are dropped. Integrity is checked by sha256, not trusted.
- **Outside the repository for real runs.** The default location is inside the repo. That is fine for
  a dry run, but `..` from there reaches the answer key, and the repo's folder name names the test. For
  real runs, build the sandbox with `--out` in a neutral folder outside the repo (for example
  `~/qa_baseline/sandbox`), and give the agent a Python interpreter outside the repo too (§3). The
  script warns while either path lies inside the repo.

### Leak check and manifest

The build fails (exit 1) if it finds:
- an answer-key string: `fact_id:`, `expected_answer`, `must_include`, `must_not_include`,
  `acceptable_variants`, or a path into `world/` or `manifests/`;
- an answer-key file name (`*.facts.yaml`, `questions.yaml`, `WORLD.md`, ...);
- a `world/` or `manifests/` folder among the documents. Inside the code repository such a folder only
  raises a warning, because `manifests` is a common folder name in deployment code;
- a symlink out of the sandbox;
- extra git refs.

The scan covers text files, the XML parts of Office files, PDF text, and the raw bytes of binary
files. It also covers the repository's whole git history: patches, messages and authors. It doesn't
OCR images. An answer key rendered as pixels isn't a credible risk.

The manifest, `<sandbox>.manifest.json`, sits beside the sandbox, outside the agent's view. It records:
- every file's size and sha256;
- the **sandbox digest**, quoted in every run;
- the git branch, head and commit count;
- the agent Python's package versions;
- the skipped files.

`prepare_sandbox.py --check --mode cold|prep|prepared` runs before every batch and around the
preparation session. It does the following:
- re-hashes the corpus and rejects files added to `documents/` or `code_repo/`;
- allows only the top-level entries listed above. `_notes/` is allowed only in prep and prepared mode,
  and prep mode refuses the question files, so the preparation session stays question-blind;
- checks the git head;
- runs the leak scan again, this time also over the question files, scratch and notes.

## 3. The agent and its tools

| Allowed | Notes |
|---|---|
| Read, Grep, Glob | sandbox paths only |
| Bash | runs from the sandbox. OS utilities (`grep`, `find`, `unzip`, `git`, `textutil`, `file`, ...) are allowed; nothing is installed |
| Python | one interpreter with python-docx, python-pptx, openpyxl, pymupdf, Pillow and ocrmac (Apple Vision OCR, local). Use it as `<python> -I` |

The reference interpreter is a dedicated venv outside the repo, pinned to the versions in
`requirements.lock.txt`. Create it with `~/.local/bin/uv venv` and then `uv pip install python-docx==1.2.0
python-pptx==1.0.2 openpyxl==3.1.5 pymupdf==2.1 ocrmac==1.0.1 pillow==13.0.0 pyyaml==6.0.3`. Pass it as
`prepare_sandbox.py --python ...`. The script probes it, records the versions in the manifest, and
warns if a library is missing. In a dry run, the repo's `.venv` will do.

**Forbidden:**
- web fetch or search, and any network access from Bash;
- MCP servers, connectors and plugins;
- spawning subagents;
- installing packages;
- reading outside the sandbox;
- writing anywhere except the session's writable folder.

**Runner hygiene.** The baseline agent must start without the orchestrator's context:
- no user, project or auto-memory files that mention this project;
- no CLAUDE.md above the sandbox;
- no MCP configuration;
- no conversation history.

Enforce the tool list through the runner's configuration, for example a subagent type whose tool list
holds only these four tools, or a headless run with an allow-list. Enforce no-network and
sandbox-only access with the runner's sandboxing where it is available. The transcript audit in §6.4 is
the backstop.

**Model.** Record the exact model id, the effort or thinking setting, and the temperature. If the runner
can't set the temperature, record `runner default (not settable)`. Use the same model for the whole run.

## 4. Modes

### Cold

The agent gets its batch with no preparation. Every batch starts from a clean sandbox: `--check`
passes, and `_scratch/` is empty. Within a batch, the agent may write scratch files under
`_scratch/batch_NN/` and reuse what it learned on earlier questions of the batch.

### Prepared

1. Before any question exists in the sandbox, run `questions_for_agent.py --label <L> --baseline-mode
   prepared --prep-only`. It renders only the preparation prompt.
2. **One preparation session** (SYSTEM + PREP prompts) builds notes, extracts or indexes under
   `_notes/`, starting with `_notes/README.md`.
   - The session sees no questions. `prepare_sandbox.py --check --mode prep`, run before and after
     it, fails if any `QUESTIONS_ONLY*.md` exists.
   - It has a soft budget of 60 minutes (`--prep-minutes`).
   - It is timed separately: run `timings_from_transcript.py --prep` for its row.
3. Freeze the notes: `chmod -R a-w <sandbox>/_notes`. Then run `--check --mode prepared`.
4. Run `questions_for_agent.py` again without `--prep-only`. The batches then run exactly as in cold
   mode, with the PREPARED_ADDENDUM appended to each task prompt.
5. Report the preparation cost (wall-clock, tool calls, tokens, size of `_notes/`) beside the
   product's ingestion time. Don't add it into per-question latency.

Prepared mode models a one-off indexing step, as the product's ingestion is one. Notes are written once
and never updated by batch sessions, so later batches don't get untimed preparation.

## 5. Batches and order

- **Batch size about 10** (`--batch-size`, default 10), with **a fresh agent per batch**. A fresh
  agent starts with an empty context, so context limits and long-session drift don't distort later
  answers.
- **A seeded shuffle** (`--seed`, default `baseline-order/v1`). Question files are often grouped by
  category, and a batch of ten "not in the corpus" questions would hint at its own answers. The same
  seed gives the same batches in every baseline run.
- **All ask modes by default.** The baseline answers the `graph` and `vector` questions as text. The
  prompt asks it to read "nodes, edges or entities" as the real-world things the files describe. Use
  `--mode` only to match a product run restricted to one ask mode. `score.py compare` compares over the
  questions both runs answered.
- **Run batches one at a time**, so concurrent OCR, rate limits and machine load don't distort the
  timings. A parallel run is allowed if it is recorded, and each batch then writes only to its own
  `_scratch/batch_NN/`.

## 6. Running a batch

### 6.1 Prompts

`questions_for_agent.py --label <L>` renders these into `build/baseline_runs/<L>/prompts/`:
- `system.md`;
- `batch_NN.md`;
- `prep.md` (prepared mode only).

Each prompt carries the sandbox path, the Python path, the batch's scratch folder, the questions, and
a soft budget of about 30 tool calls per question (`--max-calls`). The runner passes the files
**verbatim**:
- no added hints, context or examples;
- nothing from the orchestrator's own knowledge of the corpus;
- no rewording of the questions.

The prompts tell the agent to:
- answer from the files only, and never guess;
- say "Not found in the corpus." when the answer isn't there;
- give the short answer first and then the evidence (file plus page, slide, cell or line);
- print a `>>> <id>` line before each question and `>>> END` before the final answer;
- output strictly a YAML list of `{id, answer, cited_sources, notes}`, which is the results-sheet
  format `score.py` reads.

### 6.2 Per batch, in order

1. `prepare_sandbox.py --check --mode <mode>` passes. `rm -rf <sandbox>/_scratch`.
2. Start a fresh agent with `prompts/system.md` as its system prompt and `prompts/batch_NN.md` as its
   task.
3. Save the agent's final message verbatim as `batch_NN.yaml` in the run folder
   (`build/baseline_runs/<L>/`, or `<--runs-dir>/<L>/`). Also save its transcript, or note where it
   lives, and its agent or session id.
4. Record the timings (§6.3).

### 6.3 Timing and tool calls

The runner records time and tool calls, never the agent. Use one of three methods, and name it in
`run.yaml` (`timing_method`):

| Method | How | Per-question precision |
|---|---|---|
| `transcript` (preferred) | `timings_from_transcript.py <transcript.jsonl> --batch NN --timings .../timings.csv` splits the session at the `>>>` markers | exact, ± a few seconds |
| `per_turn` | the runner sends one question per turn to the same batch agent and times each turn itself | exact |
| `batch_totals` | the runner writes one row `NN,*,<seconds>,<tool_calls>` from the agent's usage report | the batch total, split evenly (flagged `apportioned`) |

How the transcript method counts time:
- A question runs from its marker to the next marker.
- The last question ends at its last tool result.
- `_setup` is the time before the first marker. `_output` is the time spent composing the final YAML.
  Both are overhead, counted in the batch and run totals but in no single question.
- A tool call counts as one call whatever it does. One Bash call that runs a large extraction script is
  still one call.
- Calls made in parallel count individually.

### 6.4 After the batch

- **Transcript audit**: grep the transcript's tool inputs for paths outside the sandbox, for `..`,
  for `world/`, `manifests/`, `questions.yaml` and the answer-key strings of §2, and for network
  commands (`curl`, `wget`, `http`). A hit voids the batch. Record it, rebuild the sandbox if needed,
  and rerun the batch as a recorded retry.
- **YAML problems**: if `collect_results.py` can't parse a batch file, fix the **syntax only**
  (indentation, quoting) and record it under `manual_fixes` in `run.yaml`. Never touch the content.

## 7. Fairness rules

1. **Same questions, same wording.** The question text comes byte for byte from `questions.yaml`. The
   key's sha1 is recorded at split time and checked again at scoring time.
2. **Same inputs.** The sandbox holds the files the product context was given (§2), and the sandbox
   digest is quoted in the run. Files the product failed to ingest stay in the sandbox: that failure
   is the product's result, not a difference in inputs.
3. **No hints.** The prompts are fixed (`agent_prompt.md`), rendered by script and archived per run.
   The orchestrator never adds context. The prompts don't mention the product, the comparison, the
   question categories or the traps.
4. **Model and settings noted.** The model id, effort, temperature, runner and its version, and how the
   system prompt was delivered all go in `run.yaml` and the results sheet.
5. **No retries unless recorded.** A retry is allowed only for a technical failure:
   - a crash, a timeout, or an empty or unparseable output;
   - a void transcript audit.

   It is never allowed because an answer looks wrong. A retry is saved as `batch_NN_retryK.yaml` with
   its own timings, and listed under `retries` in `run.yaml`. The report flags its answers, and its
   time counts in the totals alongside the failed attempt.
6. **Same scoring.** Both systems are scored by `harness/score.py` against the same key. Overrides
   follow one written rule for both, applied blind to which system answered where possible.
7. **Repeat runs.** Single runs are noisy. Run each mode at least twice (`cold_r1`, `cold_r2`). The
   agreement that `score.py compare` reports between the two is the baseline's own nondeterminism, the
   counterpart of the product's context A vs B comparison.

## 8. Scoring and comparison

```bash
.venv/bin/python -I baseline/collect_results.py --label cold_r1          # sheet + score + efficiency
.venv/bin/python -I harness/score.py compare results/ctxA_chat_r1_score.json \
      results/baseline_cold_r1_score.json --out results/compare_ctxA_vs_baseline_cold_r1.md
```

`collect_results.py` does the following:
- It merges `batch_*.yaml` with `timings.csv` into `results/runs/baseline_<label>.yaml`. That file is
  `score.py`'s results-sheet format, with context `baseline` and the run metadata from `run.yaml`.
- Each answer also carries `batch`, `tool_calls`, `tokens_in`, `tokens_out` and `timing`. The scorer
  ignores those fields.
- Every question of the key is in the sheet, so a skipped question shows as `unanswered`.
- It keeps any `override` already in the sheet.
- It runs `score.py score`, and writes `results/baseline_<label>_efficiency.md`. The run summary
  (wall-clock, tool calls, preparation) also goes into the score report's notes line.

Review every `partial` and `wrong` verdict in both systems' sheets before comparing. The scorer is
lexical (see `questions/WRITING_GUIDE.md`).

**Report format** (the style of the pilot's results page): one table with a row per category and
columns for the product context(s), baseline cold and baseline prepared. Each cell holds accuracy and
n, with ✅ ⚠️ ❌ marks for small n. Below it go the efficiency lines, for example:

> The baseline (cold, model X) answered 120 questions in 41 min of wall-clock: 20.5 s per question
> all-in, median 14 s answering. It made 610 tool calls, a median of 4 per question, with no setup.
> Prepared: 38 min of preparation, then 9.8 s per question.

Then list the categories where the two systems disagree, from the compare report, with one line of
diagnosis each. The `truncation_canary` and `resync` categories go in a separate block (§2).

The product's latency is the time a person measures in the UI, from sending a question to the complete
answer. The baseline's per-question figure is its answering time, and its all-in figure includes the
overhead. Quote both, and don't present either as like-for-like with the UI stopwatch (§9).

## 9. Threats to validity

| Threat | Effect | Mitigation |
|---|---|---|
| **Answer-key leakage**: the agent reads the key via `..`, absolute paths, the runner's memory or CLAUDE.md files, or MCP tools | inflated baseline | sandbox and Python outside the repo; leak check plus `--check` before each batch; tool allow-list; clean runner config; transcript audit voids contaminated batches |
| **Different inputs**: code variant, git history, flattening, accepted extensions | category-level bias | the sandbox mirrors the product context's inputs (§2); deviations are labelled runs; `truncation_canary`/`resync` reported apart |
| **Unequal tooling**: the baseline has OCR and raw XML access; the product has its own extractors | format categories favour whichever extracts more | intended: this is the comparison. Read the format categories (visual_*, speaker_notes, docx_comment_tracked, hidden_merged, scanned_ocr) as an extraction gap, not reasoning |
| **Question-writer bias**: questions target the product's weak spots, and some are phrased for a graph | baseline favoured on format traps; graph-phrased questions may read oddly as text | break results down by category and ask mode; read `graph`-mode results as indicative |
| **Within-batch learning**: later questions reuse earlier exploration | later questions faster and more accurate; order effects | a fresh agent per batch; seeded shuffle; overhead reported apart; per-batch table |
| **Timing noise**: API latency and queueing, machine load (OCR is CPU-bound), runner overhead | seconds vary between runs | batches run one at a time; repeat runs; report the median and p90, not single values; the method is recorded |
| **Timing attribution**: marker discipline, composing time, overhead | ± seconds per question | `_setup`/`_output` kept separate; totals are exact whatever the split; missing markers are flagged |
| **Tool-call counts depend on style**: one Bash call can do the work of twenty | counts compare interaction steps, not work | report beside time and tokens; never alone |
| **Model nondeterminism** | run-to-run variance | at least two runs per mode; `score.py compare` agreement between baseline runs |
| **Lexical scorer**: verbose answers with quoted evidence can trip `must_not_include`, or match by accident | false partial or wrong verdicts (either system) | the stale-mention rule; human review of partial and wrong; the same override rule for both systems, blind where possible |
| **Prompt effects**: the soft tool budget, the "never guess" rule, the YAML format | fewer guesses, more "not found" | fixed prompt, archived per run; any change is a protocol change |
| **Prepared-mode variance**: note quality depends on one session | high variance | budget and notes size recorded; repeat runs |
| **Platform**: Apple Vision OCR on macOS | OCR results differ from other engines | record the OS and package versions (manifest); same machine for all runs |
| **Citations not auto-scored** | a right answer from the wrong source scores correct | spot-check `cited_sources` against the evidence in the key for a sample; report the share that cite the evidence file |
| **Cost not compared** | tokens are a partial proxy | report tokens when available |

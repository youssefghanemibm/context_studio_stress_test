# Workflow example: running the baseline end to end

This page walks through one baseline run, from building the sandbox to comparing with the product.
The rules are in `BASELINE_PROTOCOL.md`; this page only applies them.

**The orchestrator** is whoever runs the steps: a person at a terminal, or a Claude Code session that
launches one subagent per batch. It never answers questions, never reads the corpus for the agents,
and never adds anything to their prompts.

Run the commands from the repository root, unless a step says otherwise.

## 0. Preconditions

- The corpus is generated and verified (`harness/verify_corpus.py`), and `build/code_repo/variant_a`
  exists.
- `questions/questions.yaml` exists, and `.venv/bin/python -I harness/score.py keycheck` passes.
- The product runs you will compare against are scored: `results/<run>_score.json`.
- The pipeline self-test passes: `.venv/bin/python -I baseline/test_pipeline.py` prints `ALL CHECKS PASSED`.

## 1. A workspace outside the repository

The agent must not be able to reach the answer key by `..`, and no path it sees should name the product
or the test.

```bash
REPO=$PWD
BASE=$HOME/qa_baseline            # any neutral name
LABEL=cold_r1
mkdir -p "$BASE"
~/.local/bin/uv venv --python 3.13 "$BASE/venv"
~/.local/bin/uv pip install --python "$BASE/venv/bin/python" \
    python-docx==1.2.0 python-pptx==1.0.2 openpyxl==3.1.5 pymupdf==2.1 ocrmac==1.0.1 pillow==13.0.0 pyyaml==6.0.3
```

This needs the network once. The agent itself never has it.

## 2. Build the sandbox

```bash
.venv/bin/python -I baseline/prepare_sandbox.py --out "$BASE/sandbox" --python "$BASE/venv/bin/python"
```

Expect three things:
- the counts: `documents/ N files, X MB` and `code_repo/ M files, ... K commits on <branch>`;
- `leak check passed`;
- no warning about paths inside the repository.

The manifest is written to `$BASE/sandbox.manifest.json`. Its `digest` identifies this sandbox in
every report.

## 3. Split the questions and render the prompts

```bash
.venv/bin/python -I baseline/questions_for_agent.py --sandbox "$BASE/sandbox" --runs-dir "$BASE/runs" --label $LABEL
```

This writes `$BASE/sandbox/QUESTIONS_ONLY.md` and `QUESTIONS_ONLY_batch_NN.md`, which hold ids and
question text only. It also writes the run folder `$BASE/runs/$LABEL/`:
- `run.yaml`;
- `batch_plan.csv`;
- `timings.csv`;
- `prompts/system.md`;
- `prompts/batch_NN.md`.

Fill in `run.yaml` now: model, temperature, effort, runner and runner_version, operator, date and
timing_method.

## 4. Run the batches, one at a time

For each batch NN, in order:

1. `.venv/bin/python -I baseline/prepare_sandbox.py --out "$BASE/sandbox" --check --mode cold`
   must pass. Then `rm -rf "$BASE/sandbox/_scratch"`.
2. Start a **fresh** agent:
   - system prompt: `prompts/system.md`;
   - task: `prompts/batch_NN.md`, verbatim;
   - tools: Read, Grep, Glob and Bash only;
   - working directory: the sandbox.
3. Save its final message, unchanged, as `$BASE/runs/$LABEL/batch_NN.yaml`.
4. Record the timings (step 4.3).

### 4.1 Option A: Claude Code as orchestrator, one subagent per batch

**Agent definition.** Keep it at user level, so it isn't inside the sandbox:
`~/.claude/agents/baseline-reader.md`. Remove it after the run.

```markdown
---
name: baseline-reader
description: Answers questions from the files of one sandbox folder only, for the baseline protocol. Use for nothing else.
tools: Read, Grep, Glob, Bash
model: <the model under test, or inherit>
---
<the full text of $BASE/runs/$LABEL/prompts/system.md>
```

The `tools` line is the allow-list. It leaves out web tools, MCP tools and subagent spawning.

**Orchestrator session.** Start it inside the sandbox, so the subagents' working directory is the
sandbox and none of the repository's CLAUDE.md or project memory loads:

```bash
cd "$BASE/sandbox" && claude --add-dir "$BASE/runs"
```

Before you start, check four things:
- no MCP servers or plugins are active in this session;
- there is no user-level memory that mentions this project;
- Bash network access is off, if the runner offers a Bash sandbox;
- the model matches `run.yaml`.

**Brief for the orchestrator.** Paste it as the first message, with the paths filled in:

```text
You are the runner for a baseline measurement. Do not read the corpus, do not answer any question,
and do not add anything to the prompts. For each batch NN from 01 to <last>, one at a time:
1. Run  <REPO>/.venv/bin/python -I <REPO>/baseline/prepare_sandbox.py --out <BASE>/sandbox --check --mode cold
   Stop and report if it fails. Then run  rm -rf <BASE>/sandbox/_scratch
2. Read <BASE>/runs/<LABEL>/prompts/batch_NN.md and launch one subagent of type baseline-reader with
   exactly that text as its prompt, in the foreground.
3. Write the subagent's final message, unchanged, to <BASE>/runs/<LABEL>/batch_NN.yaml.
4. Append a line to <BASE>/runs/<LABEL>/agents.csv: NN, the agent id, duration_ms, tool_uses and
   total_tokens from the subagent's usage report.
Retry a batch only if the subagent crashed or returned nothing. Save the retry as batch_NN_retry1.yaml
and report why. When all batches are done, list the files you wrote.
```

**The subagent invocation**, described generically. It is one call of the agent-launching tool per
batch:

```
tool:           Agent (launch a subagent)
subagent_type:  baseline-reader
description:    "Baseline batch 03"
prompt:         <verbatim text of prompts/batch_03.md: the batch header, the rules, the YAML format, the questions>
run in:         foreground, one at a time (never in parallel with another batch)
returns:        the final message (the YAML list) and a usage report (tokens, tool uses, duration)
```

Each subagent writes a transcript at
`~/.claude/projects/<sandbox path with every non-alphanumeric character as '->/<orchestrator session id>/subagents/agent-<agent id>.jsonl`.
Run `ls ~/.claude/projects` to find the folder.

### 4.2 Option B: a headless runner, one process per batch

A shell loop is the most reproducible runner, because every batch is a new process. Flag names vary
between runner versions, so check them with `claude --help` and record the version in `run.yaml`.

```bash
cd "$BASE/sandbox"
PY="$REPO/.venv/bin/python"
for P in "$BASE/runs/$LABEL"/prompts/batch_*.md; do
  NN=$(basename "$P" .md); NN=${NN#batch_}
  "$PY" -I "$REPO/baseline/prepare_sandbox.py" --out "$BASE/sandbox" --check --mode cold || break
  rm -rf "$BASE/sandbox/_scratch"
  claude -p "$(cat "$P")" \
      --append-system-prompt "$(cat "$BASE/runs/$LABEL/prompts/system.md")" \
      --model "$MODEL" --allowedTools "Read,Grep,Glob,Bash" \
      --disallowedTools "WebFetch,WebSearch,Agent,Task" --strict-mcp-config \
      --output-format json > "$BASE/runs/$LABEL/batch_$NN.json"
  "$PY" -I -c 'import json,sys; print(json.load(open(sys.argv[1]))["result"])' \
      "$BASE/runs/$LABEL/batch_$NN.json" > "$BASE/runs/$LABEL/batch_$NN.yaml"
done
```

Set `system_prompt_delivery: appended to the runner's system prompt` in `run.yaml`. The JSON output
holds the session id, so the transcript is `~/.claude/projects/<sandbox path, slugged>/<session_id>.jsonl`.

### 4.3 Timings

Use the transcript method, which is the preferred one. Run it once per batch:

```bash
.venv/bin/python -I baseline/timings_from_transcript.py <transcript.jsonl> --batch NN \
    --timings "$BASE/runs/$LABEL/timings.csv"
```

It prints the question rows, `_setup` and `_output`. A warning means a marker was missing.

**Fallback: batch totals.** When no transcript is available, take the agent's own usage report (from
Option A's `agents.csv`) and append one row per batch to `timings.csv`:
`NN,*,<duration_ms / 1000>,<tool_uses>,,,<total_tokens>,agent usage report`. The batch's questions
then get an even share, flagged `apportioned`. Set `timing_method` in `run.yaml` to match.

### 4.4 Audit each transcript

Grep each transcript's tool calls for:
- paths outside `$BASE/sandbox`;
- `..`;
- `world/`, `manifests/` and `questions.yaml`;
- `fact_id` and `expected_answer`;
- `curl`, `wget` and `http`.

A hit voids the batch. Record it in `run.yaml` and rerun the batch as `batch_NN_retry1`.

## 5. Collect and score

```bash
.venv/bin/python -I baseline/collect_results.py --label $LABEL --runs-dir "$BASE/runs"
```

This writes three outputs:
- `results/runs/baseline_$LABEL.yaml`, the sheet;
- `results/baseline_${LABEL}_score.md` and `.json`;
- `results/baseline_${LABEL}_efficiency.md` and `.json`.

It warns about questions without answers and answers without timings.

Next, review every partial and wrong verdict. Use the same override rule you use for the product's
sheets, and blind it to the system where you can. Write any override into the sheet's `override` field
and rerun `collect_results.py`, which keeps overrides.

Then archive the run: copy `$BASE/runs/$LABEL/` and `$BASE/sandbox.manifest.json` into
`build/baseline_runs/$LABEL/` in the repo. They are gitignored scratch. The `results/` files are the
deliverables.

## 6. Compare with the product

```bash
.venv/bin/python -I harness/score.py compare results/ctxA_chat_r1_score.json results/baseline_cold_r1_score.json \
    --out results/compare_ctxA_vs_baseline_cold_r1.md
.venv/bin/python -I harness/score.py compare results/baseline_cold_r1_score.json results/baseline_cold_r2_score.json \
    --out results/compare_baseline_cold_r1_vs_r2.md
```

The second comparison is the baseline's own nondeterminism. Write the summary table and the efficiency
lines in the format of `BASELINE_PROTOCOL.md` §8.

## 7. Prepared mode: what changes

```bash
LABEL=prepared_r1
.venv/bin/python -I baseline/prepare_sandbox.py --out "$BASE/sandbox_prepared" --python "$BASE/venv/bin/python"
.venv/bin/python -I baseline/questions_for_agent.py --sandbox "$BASE/sandbox_prepared" --runs-dir "$BASE/runs" \
    --label $LABEL --baseline-mode prepared --prep-only
.venv/bin/python -I baseline/prepare_sandbox.py --out "$BASE/sandbox_prepared" --check --mode prep
```

1. **Preparation session.** Run one fresh agent with `prompts/system.md` and `prompts/prep.md`. Its
   writable folder is `_notes/`, and it sees no questions. Then:
   - Record its transcript: `timings_from_transcript.py <t.jsonl> --prep --timings "$BASE/runs/$LABEL/timings.csv"`.
   - Run `--check --mode prep` again.
   - Freeze the notes: `chmod -R a-w "$BASE/sandbox_prepared/_notes"`.
2. **Questions.** Run `questions_for_agent.py` again with the same arguments, minus `--prep-only`. This
   writes the questions and the batch prompts, now with the notes addendum.
3. **Batches.** Run them as in step 4, with `--check --mode prepared`. Wipe `_scratch/` between
   batches, but never `_notes/`.
4. **Collect.** `collect_results.py` reports the preparation cost separately from per-question latency.

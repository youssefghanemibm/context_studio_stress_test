# code_modern: modern half of the Corvane monorepo + repo assembler

Owner files: `generators/code_modern/` (generate.py, lib.py, services.py, infra.py, docs.py,
extras_b.py, variant_c.py, facts.py), `generators/code_repo/assemble.py`,
`build/code_src/modern/`, `build/code_src/modern_c/`, `build/code_repo/`,
`manifests/code_modern.facts.yaml`.

## How to run

```
.venv/bin/python -I generators/code_modern/generate.py          # modern half + history + manifest (~3 s)
.venv/bin/python -I generators/code_repo/assemble.py            # three git repos (~1-2 min, hooks run)
.venv/bin/python -I generators/code_repo/assemble.py --regen    # re-run both generator halves first
```

`generate.py` deletes and rewrites only `build/code_src/modern{,_c}/` and the manifest.
`assemble.py` deletes and recreates `build/code_repo/variant_{a,b,c}` on every run.

## What the modern half contains (variant a)

Final numbers (full assembly with both halves, 2026-11-16 run):

| Variant | Files | MB | Commits | Head | Composition |
|---|---|---|---|---|---|
| a | 429 | 2.84 | 45 | 2026-11-06 | legacy 260 + modern 169 |
| b | 683 | 3.24 | 46 | 2026-11-06 | a + modern b-only 147 + legacy b-only 107 |
| c | 430 | 2.85 | 46 | 2026-11-12 | a + CM-09 (2 modern files changed, 1 added; CLRFR040 from legacy_c) |

Modern variant-a files by area: services 70, docs 35 (30 ADRs + 2 Mermaid + 3 PNG), deploy 30,
infra 27, api 3, root 4 (README.md, Makefile, .gitignore, .github/CODEOWNERS). Modern b-only:
legacy-bridge 11, zz-reconcile 12, fixtures 102 (100 JSON + index + README), runbooks 12,
notebooks 10. Largest file well under 1 MB. History: 8 world commits (CM-01..CM-08), 26 modern
filler commits, 11 legacy XC syncs (created as their own commits, as the legacy history.yaml asks).

| Area | Files | What it tests |
|---|---|---|
| `services/<13 services>/` | pom.xml, README.md, application.yaml, `<Name>Application.java` each, plus 18 controllers, listeners, a producer, 2 JPA entities (generated from tables.yaml), policies and 3 tests | config values (tier3-review-days 14, thresholds 65/60, effective-from 2026-10-01, notice 10 business days), topic produce/consume lists, endpoints, anchors TierClassifier / WriteOffPolicy / FraudReferralNoticeScheduler / ReserveRevaluationJob |
| `infra/terraform/modules/<svc>/` | main.tf + variables.tf x13, `envs/prod/main.tf` | exclusive 200Gi storage (reserve-engine only), module rename via CM-04 |
| `deploy/k8s/<10 namespaces>/` | deployment.yaml, service.yaml, configmap.yaml | replicas per service (reserve-engine 4), namespaces, 500m/2Gi |
| `api/openapi/` | 3 specs | every API path in services.yaml |
| `docs/adr/` | adr-001..030.md | status, deciders (names/titles as of ADR date), supersedes |
| `docs/diagrams/` | event-flows.md (Mermaid flowchart, topic on each edge), sequences.md (2 sequence diagrams), 3 PNGs | facts on edges; PNG text verified by OCR (image_ocr locators) |
| root | README.md, Makefile, .gitignore, .github/CODEOWNERS | variant-a CODEOWNERS (stale for recovery-svc and document-svc) |

Variant-b-only (commit B-01, 2026-11-06, Nadia Petrovic): `services/legacy-bridge/` (CN-01),
`tools/zz-reconcile/` (CN-02), `fixtures/claims/` (140 fixture JSON + `zz_fixture_index.md`, CN-03),
`docs/runbooks/` (CN-05), `analytics/notebooks/` (CN-06, `.py` with `# %%` cells). Each canary
statement appears only in its own file; sibling files read the canary value from configuration
(poll interval, schedule, target table, DSN) instead of stating it. CN-04
(`legacy/clara/cobol-archive/`) belongs to the legacy half.

Variant c (CM-09, 2026-11-12, Tariq Hussain): `modern_c/.github/CODEOWNERS` (recovery-svc and
document-svc -> `@corvane/hub-squad-recoveries-docs`), `modern_c/services/notification-svc/.../application.yaml`
(produces `notification.fraud-notice.sent.v1`) and a new `FraudNoticeSentPublisher.java`.

## History model

`build/code_src/modern/history.yaml` (`format: corvane-code-history/1`): `commits` (26 filler
commits F-01..F-25 + F-13b, and B-01) and `files` (per path: variants, created_by, author,
renamed_from/renamed_by, modifications with before/after snippets, c_override). Content before a
commit = final content with that commit's and later commits' `after` replaced by `before`.
The generator replays every file's modifications backwards and forwards before writing, so
snippets are proven unambiguous.

Modern changes in world commits: CM-04 (git mv `services/reserve-svc` -> `services/reserve-engine`
and `infra/terraform/modules/reserve-svc` -> `.../reserve-engine`; names, image, k8s objects,
Makefile, README, CODEOWNERS, `reserve.changed.v1` -> `v2` in reserve/gl/reporting configs),
CM-06 (tier3-review-days 21 -> 14), CM-07 (idempotency key in PaymentInstructionService +
config), CM-08 (Tier-3 threshold lines + ReferralThresholdPolicy), CM-09 (variant c).
Filler commits carry the realistic intermediate states (Spring Boot bumps 3.3.2 -> 3.3.5 -> 3.4.1
-> 3.4.5, README typo fixes, DOCSTOR -> Evidence Vault key rename after 2025-11-03, consumer of
`claims.reserve.movement.v1` added after 2025-12-12, effective-dated referral block added
2026-03-16 before fraud go-live, etc.). Filler messages contain no world facts.

Clean rename check: `git log --follow --name-status -- infra/terraform/modules/reserve-engine/main.tf`
shows `R090 .../reserve-svc/main.tf -> .../reserve-engine/main.tf` in CM-04. (For service files,
`--follow` additionally reports git's copy detection against a sibling service at creation time.)

## Assembler

- Reads both halves' history.yaml (tolerant of dict or list `files`, `commit`/`commit_id`,
  `before`/`after`, `removed_by`, `renamed_from`), the `*_c` override dirs, and world commits
  CM-01..CM-09 from corpus_plan. Extra commits defined by a half (`commits:`) become real
  commits; `--fold-extra` instead folds the legacy half's extra commits into their `fold_into`
  world commit.
- Variant a is built commit by commit (date order, fixed time of day per commit id, UK offset
  +0000/+0100); b and c are `git clone`s of a plus one commit each, so shared history has
  identical SHAs. Identities from people.yaml (name as of the commit date + email).
- Determinism: fixed GIT_AUTHOR/COMMITTER name, email and date, `-c user.name/-c user.email`,
  `core.autocrlf=false`, TZ/LC_ALL fixed. SHAs are identical across runs (checked, see below).
- **Deviation (deliberate):** the task text asked for `GIT_CONFIG_NOSYSTEM=1` and a temporary HOME.
  On this machine the system and global git config are what enable the vault-radar pre-commit
  secret scanner (`core.hookspath` / `hook.ciso-vr`), so isolating the config would silently
  disable that hook. The task also says never to bypass hooks, so the assembler keeps the real
  config and pins everything that affects SHAs with `-c` flags and environment variables instead.
  The hook runs on every commit and adds most of the runtime.

## Budgets and deviations

- **Variant a file count.** The spec's mandated modern content (13 services x {pom, README,
  application.yaml, Application class} + domain classes, 13 Terraform modules x 2 + env root,
  10 namespaces x 3 manifests, 30 ADRs, diagrams, root files) needs ~165 files, not 90-110.
  Variant a therefore has 429 files (legacy 260 + modern 169) instead of 330-370; size is 2.84 MB (< 30 MB). The assembler asserts a hard range of 300-440 for a and prints a NOTE outside 330-370. Variant b was kept inside 600-700 by sizing the fixture set: with the legacy half's 107 b-only files (cobol-archive 41, testdata 66), 140 fixtures gave 723 files, so the fixture count is 100 (b = 683). If the legacy b-only set grows by more than ~17 files, lower `N_FIXTURES` in extras_b.py.
- Fraud-referral-svc in variant c does not list `notification.fraud-notice.sent.v1` as a consumed
  topic (services.yaml says it consumes it from 2026-11-12) because PL-276 makes the topic name
  exclusive to the c notification-svc application.yaml; the notification-svc README is also left
  unchanged in c for the same reason. The Terraform topic-access list is not updated in c either.
- `bi-index-pct` (3.1) is omitted from reserve-engine config: it is exclusive to LD001 (PL-011).
- Topic partitions/retention are not stated anywhere (exclusive to ST030/LD013).
- The example claim id in services.yaml (CLM-UK-2025-118204, also EP-003's claim) is rendered
  as `CLM-<region>-<yyyy>-<6 digits>` to avoid restating RJ003's episode.

## Verification

- `verify_corpus.py --family code_modern --checks 1` (with OCR): 221 PASS, 0 WARN, 0 FAIL
  (198 code_lines, 20 git_commit, 3 image_ocr on the PNG diagrams).
- `verify_corpus.py --family code_legacy --checks 1` against the same assembly: 1472 PASS, 0 FAIL.
- Exclusivity: `build_index.py --index-dir build/index_code_modern --no-ocr`, then
  `--checks 3` for code_modern: 11/11 exclusive facts PASS; manual `--search` for each exclusive
  needle (fraud-notice topic, recoveries-docs owner, clara-platform owner, 200Gi, cdw-ro-02,
  recon.daily_diff, CLM-SE-2026-004417, 2027-01-23, 45 seconds, CLR-2025-02) hits only the owning
  file (plus its a/b/c mirrors and, for the topic, the CM-09 commit message which is listed in
  also_in). Corpus-wide checks 3/6/7: denylist and secrets PASS; the only exclusivity FAIL is the
  legacy manifest's CL-CLRFR040-F002 (its needle also occurs in the legacy CLRFR030.cbl).
- Generator leak check (built into generate.py): no exclusive needle of any other family appears in
  a modern file.
- Determinism: two generator runs give byte-identical build/code_src/modern{,_c} and manifest
  (sha256 compared); repeated assembler runs (`--skip-gen`, `--regen`, and a run started by the
  legacy agent) give identical heads: a `cab7e41b39f5`, b `97b14a55a78a`, c `d11d7f6470d3`.
- Largest tracked file in any variant: 80 KB (docs/diagrams/namespaces.png).
- Not verified: the Java/Terraform/YAML is illustrative and was not compiled, `terraform validate`d
  or applied; Mermaid diagrams were not rendered.

## Observations about other families (not fixed here)

- `@corvane/hub-squad-recoveries-docs` with recovery-svc/document-svc also appears in
  ST024 (row 315), ST053 and TX070 (`/issues/314`) as the CHUB-415 ticket summary. PL-275's exact
  needle (`/services/recovery-svc/ @corvane/hub-squad-recoveries-docs`) still passes check 3.
- ST036 mentions the `CLR-2025-02` source baseline in an XML comment; PL-266's full commit
  message needle still passes check 3.

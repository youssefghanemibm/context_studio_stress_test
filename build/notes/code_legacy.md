# code_legacy - CLARA half of the Corvane monorepo

Generator: `generators/code_legacy/generate.py` (+ `srcmodel.py`, `cobol.py`, `cobol_special.py`,
`assets.py`, `docs.py`, `archive.py`, `commits.py`, `naming.py`). One run rewrites everything from
scratch in about 15 s:

- `build/code_src/legacy/<repo path>`: final content (variants a and b)
- `build/code_src/legacy_c/legacy/clara/cobol/CLRFR040.cbl`: the only file CM-09 changes
- `build/code_src/legacy/history.yaml`: commit history for `generators/code_repo/assemble.py`
  (the format is documented at the top of the file; the assembler already reads it)
- `manifests/code_legacy.facts.yaml`: 1,472 facts, all `code_lines` locators
- `build/code_check_legacy/variant_{a,b,c}`: plain-copy check trees for `verify_corpus --code-repo-root`

Two runs give byte-identical outputs (sha256 over every file plus the manifest).

## Files and what they test

| Group | Count | Variants | Tests |
|---|---|---|---|
| `legacy/clara/cobol/*.cbl` | 122 | a b c | Fixed-format COBOL (sequence numbers in cols 1-6, indicator col 7, change tags in cols 73-80), 155-784 lines. EXEC SQL touches exactly `reads_tables` (SELECT/cursor) and `writes_tables` (INSERT/UPDATE/DELETE); CALLs exactly match `calls_programs`; COPYs exactly match `copybooks`; CICS for online programs (transactions, BMS maps, inline symbolic maps). Placements PL-236..247 and PL-245 (C05 drift). |
| `legacy/clara/copybooks/*.cpy` | 50 | a b c | Fields and PICs from copybooks.yaml. RSVMOVE carries the CHUB-138 / CHUB-142 history (PL-248). |
| `legacy/clara/jcl/*.jcl` | 32 | a b c | Steps -> programs (IKJEFT01 + `RUN PROGRAM`), DD statements, schedule / restart / support comments. PL-249 (RSVOUT DSN). |
| `legacy/clara/bms/*.bms` | 7 | a b c | Mapsets CLRMS01-07 holding the 13 maps (fields, positions, attributes, PF keys). |
| `legacy/clara/ddl/T_*.sql` | 43 | a b c | One DDL file per CLR table: columns, PKs, FKs, identity columns, COMMENT ON from the world descriptions. |
| `legacy/clara/ddl/T_PARAM_seed.sql` | 1 | a b c | Parameter rows with validity dates and tickets (PL-250). |
| `legacy/clara/README.md` + `docs/*.md` | 5 | a b c | Layout and conventions; program inventory, batch jobs and DB2 object list as of 2026-10-20 (8 reserve writers, CHUB-298 open, renames). |
| `legacy/clara/cobol-archive/` | 41 | b only | 40 retired sequential-file utilities (no SQL, CALL or COPY, so no new world links) + README. CN-04 canary in `CLRFR990.cbl` (PL-270). |
| `legacy/clara/testdata/` | 66 | b only | Synthetic fixtures: 42 table CSVs (2099 test claim ids, masked personal fields; no T_PARAM), 3 interface samples, 10 expected reports, 10 test JCL streams, README. |

Totals: 260 variant-a files, 107 variant-b-only files, 2.7 MB (history.yaml adds 0.09 MB).

## Manifest

1,472 facts: 1,457 `code_fact`, 6 `temporal`, 3 `resync_change`, 2 `general`, 1 each of
`contradiction_old` (PL-245), `canary` (PL-270), `aggregate_source`, `alias_use`.
All 17 legacy CODE placements are planted: PL-236..PL-250, PL-270 (variant b) and PL-274 (variant c).
Placement entries copy `world_ref`, `kind` and `exclusive`, and add `placement` / `placement_key`.
The general facts cover every write statement, every read, every CALL and every COPY per program;
the PICs of the key copybooks; every JCL step's `RUN PROGRAM`; job schedules (except CLRNRSV3);
DDL primary and foreign keys; BMS map headers; T_PARAM rows; and the doc rows.

## Commit messages that touch these files (for the git_commit facts)

World commits: CM-01 (import), CM-02 (CLRFR020 endpoint), CM-03 (CLRRS170 / RSVMOVE), CM-05
(CLRFR060, CLRFR120, FRDNOT01, T_FRAUD_NOTIFICATION, CLRNFR02, CLRMS05, T_PARAM row, and the
T_FRAUD_NOTIFICATION reads added to CLRFR010/100/110/140), CM-09 (CLRFR040, variant c only).
Legacy-only commits defined in history.yaml (`world: false`, each with `fold_into`):
XC-01 rename FNETCAL1/FNETREF1 (2025-03-01), XC-02 CHUB-138 widen RM-AMOUNT (2025-04-25),
XC-03 REC_PURSUE_MIN_GBP row (2025-08-28), XC-04 CHUB-241 CLRRS210 + CLRDRSV9 (2026-02-27),
XC-05 CHUB-205 threshold 65 row (2026-03-30), XC-06 CHUB-207 CLRFR140 / CLRNFR99 disabled (2026-03-31),
XC-07 CHUB-208 CLRFR090 + CLRQFR01 (2026-06-26), XC-08 CHUB-318 review days 14 row (2026-06-30),
XC-09 CLRRS210 / CLRDRSV9 retired (2026-08-28), XC-10 CHUB-395 Tier-3 threshold 60 row (2026-09-30),
XC-11 legacy docs (2026-10-20). Dates, authors and tickets come from key_tickets.yaml,
programs.yaml (`since`, `renamed_from`), copybooks.yaml (`field_history`) and the T_PARAM rows.

## Self-checks (`generate.py` exits non-zero on any failure)

- Per program and per variant (a, and c for CLRFR040): parsed SQL reads and writes, CALLs and
  COPYs equal programs.yaml (c adds CLRCM040 and PARMREC1 to CLRFR040, as CM-09 says). No EXEC CICS LINK/XCTL.
- Line widths and sequence numbers; every program has 150-900 lines.
- history.yaml replay: undoing the modifications from the final content reproduces every
  intermediate version and the created version (variants a and c).
- Every needle is found in its line range; every legacy placement is planted exactly once.
- Forbidden strings (other files' exclusive values, CICS regions, DB2 plan or subsystem, CODEOWNERS
  handles, canaries of other files, product terms) and denylisted names (word-boundary match).
- `W.may_state` for every program, copybook, BMS, table and interface field the code states.

## Verification results

- `verify_corpus --family code_legacy --checks 1 --code-repo-root build/code_check_legacy`:
  1,472 PASS, 0 WARN, 0 FAIL.
- `assemble.py --skip-gen` followed by `verify_corpus --family code_legacy --checks 1` against
  `build/code_repo` (variant a 429 files / 45 commits, b 683 / 46, c 430 / 46): 1,472 PASS, 0 WARN, 0 FAIL.
- `build_index.py --index-dir build/index_code_legacy --no-ocr`, then checks 3, 6 and 7 with
  `--family code_legacy`: exclusivity 2 PASS, denylist 2 PASS, secrets 1 PASS. A search for
  "VELOCITY SCORE" finds only variant_b CLRFR990.cbl. The PL-274 sentence appears only in
  variant_c CLRFR040.cbl. (`build_index.py` indexes git repos only, so the plain check trees are
  not indexed.)
- Note: a concurrent `assemble.py` run by the code_modern agent made one of my assembler runs fail
  midway. I waited for their run and checks to finish, then reassembled cleanly.

## Deviations and design decisions

- **BMS**: 7 files, one per mapset (CLRMS01-07), holding the 13 maps. The world has 7 mapsets,
  and one source member per mapset is how BMS works.
- **Program length**: scaled from the world `loc` (171-4,161) into 155-784 lines, as the spec asks
  for 150-900. No file states a line count.
- **Write-only tables**: several writers change a table they do not read (per programs.yaml) but need a
  value back, such as the reserve id for a movement row or the old amount. These programs use DB2
  data-change table references, `SELECT ... FROM OLD/FINAL TABLE (UPDATE ...)`, so no SELECT ever
  names a write-only table. This affects CLRST040, CLRRC050, CLRRS020, CLRRS110, CLRRS130 and
  CLRFR060 (a cursor over FINAL TABLE). docs/coding-standards.md explains the pattern. A naive parser
  may count these as reads; the world truth is writes only.
- **CLRGL090** has a comment saying that no row is inserted into CLR.T_RESERVE_MOVEMENT. This
  negative mention could become a false-link trap.
- **Exclusive data left out**: T_PARAM seed omits RSV_BI_INDEX_PCT (PL-011); CLRNRSV3 JCL and
  batch-jobs.md omit the schedule (CLX-IF-042 / VS033); CLRNRSV1 omits its restart text (PL-068); the
  T_CLAIM DDL omits LEGACY_SKADE_REF (PL-152); no CICS region names (PL-054); no DB2 subsystem or
  plan (PL-055) - JCL uses `&DB2SSID` / `&DB2PLAN` from `INCLUDE MEMBER=CLRSYMS`; no MAXDEPTH;
  no CODEOWNERS handles; the import baseline name is not repeated outside the commit message.
- **History before import**: maintenance-history entries dated before 2025-02-21 are generic colour
  (recompiles, Y2K, error handling) with real world people only while employed (KBARR01, PASHW01, GP,
  DO) or CLRPROJ. One dated entry is derived from the world: CLRFR040 2023-03-28 "threshold 075 -> 070
  (BR-FRD-012 v2)", consistent with the T_PARAM rows 75 -> 70 on 2023-04-01.
- **RSVMOVE before CM-03**: FILLER X(22) and no RM-REC-VERSION (record length stays 116). In the
  XC-02 state the header's "116 BYTES" comment was deliberately left stale (RM-AMOUNT widened to 7
  bytes), matching INC-2025-0412.
- **Descriptions over time**: headers and JCL comments that changed after creation (renames to
  Sentinel, CLRFR140 / CLRNFR99 disabled, CLRRS210 / CLRDRSV9 retired) carry removed and added lines,
  so earlier versions show the earlier text. Other system names in comments use the current names in
  every version (minor anachronism in historic snapshots only).
- **Invented technical identifiers** (no world facts): DD names (RPTOUT, IMPIN, EXTOUT), symbolic DSNs
  `&CLRHLQ..<pgm>.<dd>`, include member CLRSYMS, BMS labels, code-lookup type `DFLTRSV`, index and
  constraint names, batch user ids CLRBATCH and CLRDBA, and the archived program names and titles
  (b only).
- Only CLRFR040 hard-codes a threshold (070). CLRFR140's ">= 90" appears only in comments, because
  candidates arrive on an input file.
- The b-only files use `created_by: CM-01` in history.yaml; the assembler adds them in its own
  variant-b commit, which is its choice.

## Not verified

- The COBOL, JCL, BMS and DDL were not compiled, run or bound; no mainframe toolchain is available.
  The DB2 `SELECT FROM OLD/FINAL TABLE (UPDATE ...)` forms assume DB2 12-level support.
- No OCR facts (all facts are code_lines), so there is nothing OCR-dependent.

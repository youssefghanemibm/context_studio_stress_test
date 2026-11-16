# structured.specs: ST027 to ST060 (JSON, XML, YAML/YML, wiki HTML)

Generator: `generators/structured/gen_specs.py`, with builders in `generators/structured/specs_lib/`
(`core.py` for world access, exclusivity guards, the forbidden-pattern scan and fact collection; `json_specs.py`,
`xml_specs.py`, `yaml_specs.py` and `wiki_specs.py` for the files; `phrases.py` for the rng-driven filler banks).

```
.venv/bin/python -I generators/structured/gen_specs.py [--only ST035,ST054] [--no-verify]
```

The generator writes only ST027 to ST060 into `corpus/upload/structured/` (it deletes only `<fid>_*` files of its own
ids) and writes `manifests/structured.specs.facts.yaml`. Before writing, every file is scanned for other files'
exclusive values, canaries, product terms and denylisted names, and the run fails if any are found. After writing,
every manifest needle is resolved with `harness/extract.py`. A full run takes about 4 s.

## Files

| id | ext | KB | target | what it tests |
|---|---|---|---|---|
| ST027 | json | 33 | ≈40 | Sentinel score API samples. PL-169: `/responses/1/threshold_applied` = 60 for a Tier-3 claim. Also has the FRAUDNET former name and the vendor. |
| ST028 | json | 10 | ≈10 | Claims Hub feature flags with per-environment states. |
| ST029 | json | 6 | ≈8 | Effective-dated fraud parameters. PL-170: `/referral/threshold` (tier3 60 from 2026-10-01, default 65). Also has the BR-FRD-012 history. |
| ST030 | json | 17 | ≈20 | Kafka topic catalogue. PL-171 (exclusive): claims.reserve.movement.v1 has 12 partitions. This topic has no retention field (LD013 owns that fact). |
| ST031 | json | 33 | ≈30 | Service registry: formerNames (reserve-svc), runtime, config and owners. |
| ST032 | json | 24 | ≈25 | Fraud referral event samples (thresholdApplied, noticeDueDate, deferral rule). |
| ST033 | json | 66 | ≈60 | Wave 1 data-quality report: 74 checks, freeze window, IBM Callum Fairbairn as the report owner. |
| ST034 | json | 20 | ≈15 | NISA-FR1 2026Q3 payload. PL-143 (1,530; also_in ST038-F001 and VS042). Also has synthetic breakdowns, a weekly split and a deferral annex. |
| ST035 | xml | 380 | ≈400 | Interface catalogue: namespace, attributes, nested elements, all 60 interfaces. Each has source/target, a transport protocol attribute, format, owner, criticality, dependsOn/dependents, impact analysis, transitive upstream lineage, program and service detail. PL-172/173. The CLX-IF-042 schedule is omitted (VS033). |
| ST036 | xml | 269 | ≈300 | CLARA program inventory (122 programs). PL-174: CLRFR020 renamedFrom FNETCAL1. Lists the 8 reserve writers and a table cross-reference index. |
| ST037 | xml | 45 | ≈50 | MQ definitions. PL-175 (exclusive): `MAXDEPTH(50000)`, stated only inside the CLR.RSVMOVE.OUT queue element. Every other queue says the default depth applies. |
| ST038 | xml | 16 | ≈20 | NISA-FR1 2026Q2 return. PL-143 (1,488). Also has crosstabs that reconcile to both breakdowns, a weekly split and a record-level deferral annex. |
| ST039 | xml | 33 | ≈40 | NISA-TP2 2026Q2 return. PL-176: sourceInterfaces CLX-IF-051. Includes lineage and a late-submission history. |
| ST040 | xml | 60 | ≈60 | Claims process definition: stages, steps, decisions and SLAs as of 2026-07-13. |
| ST041 | xml | 206 | ≈200 | Copybook schemas. PL-177: RSVMOVE RM-AMOUNT S9(9)V99 COMP-3 and RM-REC-VERSION 9(2), plus the field-history change log. |
| ST042 | xml | 68 | ≈60 | JCL schedule. The CLRNRSV3 schedule is guarded (`published="false"`). The CLRNRSV1 restart is guarded (LD025). |
| ST043 | yaml | 24 | ≈30 | OpenAPI 3.0.3 for reserve-svc (2025-12-01). PL-178 (C09 old side): `info.title` is 'reserve-svc API'. Also has the 21-day Tier-3 cadence (BR-RSV-007 v2), examples whose authority levels follow BR-RSV-003 v3, and the data model. |
| ST044 | yaml | 21 | ≈30 | OpenAPI for fraud-referral-svc. PL-179: customer-notice summary 'referral date + 10 business days'. Examples use business-day arithmetic. |
| ST045 | yaml | 26 | ≈15 | Effective-dated business rules config (24 rules, with version history). |
| ST046 | yaml | 11 | ≈12 | GitOps KafkaTopic resources (multi-doc). claims.reserve.movement.v1 has no partitions or retention (ST030/LD013 exclusives). |
| ST047 | yaml | 19 | ≈25 | Helm values for the umbrella chart. recovery-svc is still labelled for the Fraud & Settlement squad on 2026-10-20. |
| ST048 | yaml | 7 | ≈8 | CLX-IF-049 data contract. PL-180: schemaVersion 3, key claim_id, minor units. The consumer is reserve-svc on 2025-12-12 (temporal). |
| ST049 | yml | 7 | ≈6 | reserve-engine Deployment + Service + ConfigMap + HPA (+ ServiceAccount, PDB, NetworkPolicy, Route). PL-181 (C09 new side). |
| ST050 | yml | 8 | ≈6 | fraud-referral-svc bundle. PL-182: env REFERRAL_THRESHOLD_TIER3=60. |
| ST051 | yml | 7 | ≈8 | CI workflow: change detection, build/test, contract, API-compatibility, security, SBOM, image and dev deploy. |
| ST052 | yml | 7 | ≈10 | Alerting rules (14-day Tier-3 cadence, CLX-IF-042 consumers, INC references). |
| ST053 | html | 68 | ≈80 | Wiki home. PL-183: nested squad table for T30. Also has waves, Claims Hub interfaces with nested dependency tables, and recent tickets. |
| ST054 | html | 37 | ≈40 | CLX-IF-042 page. PL-184: nested Downstream table. PL-185 (C06 new side): Sentinel, used 5 times and never FRAUDNET. No schedule or max depth. |
| ST055 | html | 43 | ≈30 | Glossary. PL-186: loss adjuster / adjuster / assessor → Claims Assessor. Also has per-term usage tables (nested). |
| ST056 | html | 51 | ≈60 | CLARA batch runbook with nested step tables. Guarded restarts and schedules are left out. |
| ST057 | html | 49 | ≈40 | Team directory. PL-187: both Callum Fairbairn rows (P022 Corvane Leeds, P051 IBM London). |
| ST058 | html | 50 | ≈50 | reserve-engine design (2026-03-09): tier3-review-days 21, the 8 reserve writers, replaced-program table access (nested), the consumed Avro schema and error codes. |
| ST059 | html | 40 | ≈40 | Fraud rules 2026. PL-188: nested in-force table. Also has all fraud rules in force on 2026-10-01, implementation components (nested) and related tickets. |
| ST060 | html | 44 | ≈50 | Release notes. They stop at R2026.09 Wave1 (asserted: no R2026.11 string), with per-release nested change, component and known-issue tables. |

Total size is 1.81 MB. Every file is under 0.4 MB.

## Manifest

There are 216 facts: general 168, needle 17, temporal 11, alias_use 7, scale 6, terminology 4, contradiction_new 2 and contradiction_old 1.
All 22 placements that target or also_in ST027 to ST060 are planted with `placement`/`placement_key`. Two facts are exclusive (PL-171 and PL-175).
Fact ids F001 onwards from the earlier run are unchanged. The 15 facts added in this pass are appended at the end of each file's list.

## Verification (2026-11-16)

- `verify_corpus.py --family structured.specs --checks 1`: 216 PASS, 0 WARN, 0 FAIL.
- `--checks 3` (exclusivity, `build/index_structured.specs`): 2 PASS. `--checks 6,7` (denylist, secrets): PASS.
- Index search: `MAXDEPTH(50000)` appears only in ST037. The claims.reserve.movement.v1 partition count appears only in ST030.
- Determinism: I deleted all ST027 to ST060 outputs and the manifest, regenerated, then regenerated again. The `extract_all` hashes, file bytes and manifest were identical. This is byte-identical output.
- All files parse (json, lxml, yaml.safe_load_all, lxml.html). All wiki cross-links resolve to existing ST053 to ST060 filenames.

## Deviations and judgement calls

- **ST054 and C06.** The task text says ST054 uses "the stale name per C06". `contradictions.yaml` makes ST054 side B with the claim 'Sentinel' (the current name). LD025 carries FRAUDNET. I followed contradictions.yaml: ST054 says Sentinel and never FRAUDNET.
- **ST054 filename.** The filename comes from corpus_plan: `ST054_wiki_interface_clx_if_042.html`. The task's example href (`ST054_wiki_clx_if_042.html`) was only an example. All links use the exact planned filenames.
- **Sizes.** All files are within 0.70× to 1.71× of the "≈" targets. ST044 is at 0.70×, ST047 and ST052 at 0.74×, ST055 at 1.44× and ST045 at 1.71×.
- **Synthetic data, consistent with world rules.** This covers:
  - FR1 breakdowns, crosstabs, weekly splits and deferral annexes: they sum to the world totals, and deferrals stay within 60 days.
  - API and message examples: authority levels follow BR-RSV-003 v3, tiers respect BR-TRI-003 v3, large loss follows BR-RSV-011 v2, and notice and triage dates use 10 and 3 UK business days.
  - Random claim refs, which avoid the three world-reserved refs.
  - No referral-rate, claims-scored or other exclusive metrics are stated.
- **API changelog.** The ST043 and ST044 `x-changelog` entries are document version history. Their dates fall within the lifetimes of the referenced CHUB tickets.
- **ST048.** The interface note's "reserve-engine" is rendered as reserve-svc, because the document date (2025-12-12) is before the rename.
- **Old names.** They appear only as former-name or history mentions, such as formerName, "(formerly DOCSTOR)" or the CHUB-117 summary.

## Unverified

- No facts here need OCR.
- The exclusivity index search covered only the files present at the time. Other agents' files may still be partial.
- The first `--checks 1` run failed once with a YAML parse error inside another family's manifest, which was being written at that moment. The rerun passed.

## Fix pass (2026-11-16, hunt findings N9, N10, N16, N17, N18, N24, N27, m9, m10, m22)

- **N9/N10 (ST038 FR1 2026Q2, ST034 FR1 2026Q3).** The synthetic `split_total` breakdowns are gone. New module
  `specs_lib/fr1_data.py` imports the sheets generator's ST015 model (`sheets_lib.csv_files.st015_referrals` over
  `claims.generate_claims()`, read-only; it falls back to running the sheets builders up to ST015 with an empty
  `--only` set). It never reads the CSV. byRegion, byLine, byTier, bySource (ON/BS/MN), the new bySystem, byMonth,
  byProduct (now with region), the region-by-month and line-by-tier crosstabs, the weekly split and the deferral
  annex (claim ref, product, tier, referral date, notice due date) all come from the ST015 rows. Claim type and
  channel come from the ST013 claim, or are drawn per referral from the claims profile. The notice issue lag
  (1–10 business days, never after the ST015 due date) and the deferral length (12–58 days) are drawn per referral,
  with rng keyed by referral id. `customerNotices` now has issuedWithin10BusinessDays + deferred +
  pendingAtPeriodEnd = total, and these agree with noticeTiming and the annex. `fr1_data._check` asserts every
  identity. Q2: UK 997 / NO 217 / SE 158 / DK 116, Tier 655/641/192, deferred 55, pending 97. Q3: UK 1027 / NO 241 /
  SE 158 / DK 104, Tier 687/604/239, deferred 66, pending 110. The ST034 lineage and declaration name the migrated
  products from the data.
- **N16 (ST042).** The JCL DCB is computed from the copybook named in the DSN, as of the document date
  (RSVOUT → RSVMOVE = LRECL=116, BLKSIZE=0). SPACE is aligned with the code JCL.
- **N17/N18/m9/m10/m22 (ST042, ST056).** New `core.jcl_jobs_as_of(on)`: a job exists once one of its step programs
  exists (`since`), and only existing steps are listed. Interfaces are filtered by `since`. On 2026-05-18 that gives
  31 jobs (no CLRQFR01/CLRFR090, no CLX-IF-033).
- **N24 (ST043).** x-replaces-programs is the full services.yaml list (16, including CLRGL090). POST
  /revaluation-runs is included with its own request and response schemas and a "revaluation" tag.
- **N27 (ST036).** The header comment no longer names the baseline. `CLR-2025-02` is added to FORBIDDEN.
- **Facts.** No ids changed. Appended: ST034-F009 and ST038-F007 (deferred-notice counts, computed),
  ST043-F008 (CLRGL090 in x-replaces-programs) and ST043-F009 (POST /revaluation-runs).
- **Coupling.** ST034/ST038 follow whatever ST015 code is current. The sheets agent's N8 fix (holiday-aware
  regional due dates) is already reflected in the annex due dates. The ST015 CSV must be regenerated with the
  same code so the dates agree. Verified against the in-memory model: every region, tier, product and deferral
  claim ref/due date matches.
- ST060 also changed on this run: CHUB-279's summary came from a world rebuild made by another agent. It was not
  edited here.
- **Checks.** Two runs gave byte-identical output. `verify_corpus --family structured.specs --checks 1,3,6,7
  --index-dir build/index_fix_specs`: 220 PASS, 0 FAIL. `--checks 2`: 253 PASS. `score.py keycheck`: 0 problems.

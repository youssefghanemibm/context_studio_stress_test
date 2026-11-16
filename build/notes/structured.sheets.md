# structured.sheets — ST001–ST026 (XLSX + CSV)

Generator: `generators/structured/gen_sheets.py` (helpers in `generators/structured/sheets_lib/`).
Aggregate checker: `generators/structured/check_aggregates.py`.
Manifest: `manifests/structured.sheets.facts.yaml` (208 facts).

Run: `.venv/bin/python -I generators/structured/gen_sheets.py` (about 4 s). The generator deletes and
rewrites only ST001–ST026 in `corpus/upload/structured/`, then rewrites the manifest. Other agents'
ST027+ files are not touched.

## Files and what each one tests

| id | rows / units | what it tests |
|---|---|---|
| ST001 data dictionary (2025-02-14) | 6 sheets, 42 tables, 459 columns, 4,102 usage rows (~4,770 rows in all) | hidden sheet `_retired` (PL-152, exclusive). Merged block headers on `Tables` (PL-153). Frozen panes, autofilters, data validation. STALE 7-writer list for CLR.T_RESERVE that leaves out CLRGL090 (PL-154, C08 old side). NI_NO CHAR(13) PII flag (PL-155). Tables created after the dictionary date are left out (CLR.T_FRAUD_NOTIFICATION, 2026-03-27). |
| ST002 RACI | 31 step rows, 7 merged stage cells | merged column-A stage cell "Recovery & Subrogation"; A = Freya Lindahl (PL-156) |
| ST003 interface register | 60 interfaces | CLX-IF-042 owner/criticality (PL-157). The CLX-IF-042 schedule cell is blank (the schedule is exclusive to VS033). |
| ST004 reserve movements Q3 | 3,703 movement rows | hidden sheet `calc` with revaluation rates in B2:B4 (PL-158, also in ST022). VLOOKUP formulas point at `calc`. |
| ST005 rule catalogue | 156 rules, 197 versions | versions and effective dates; BR-FRD-031 v2 approvers (PL-159) |
| ST006 program inventory | 122 programs | CLRFR140 'disabled' (PL-160); call graph |
| ST007 migration mapping (2025-06-16) | 459 source columns | column mappings and not-migrated columns |
| ST008 Wave 1 test results | 1,101 executions, 90 defects | test execution and defect rows |
| ST009 vendor fees 2026 | 41 fee rows | UK fees only; Norrvik fees deliberately left out |
| ST010 KPI workbook | 4 native charts | PL-161 chart_only. The FNOL channel mix values exist ONLY as `c:strLit`/`c:numLit` literals in chart1.xml (no cell holds them, no helper sheet). `harness/extract.py` resolves `{kind: xlsx_chart}` to them. Q2/Q3 fraud referral counts are also chart-only. |
| ST011 capacity plan (2026-04-06) | 72 forecast rows, 30 jobs | batch window; CLRNFR99 removed 2026-04-01 (temporal) |
| ST012 contact directory | 44 staff | Corvane staff only, every email @corvane-mutual.example |
| ST013 claims extract | EXACTLY 15,000 rows | synthetic claims built from claims_profile.yaml with a seeded rng. IDs only, no claimant names. Source of 35 aggregates. |
| ST014 reserve movements Oct | 8,691 | totals by movement type (PL-164); CLRGL090 writes no movements; CLRRS150 corrections |
| ST015 fraud referrals 2026 | 4,968 | counts by rule applied (PL-165); Q2/Q3 counts match the timeline metrics; INC-2026-0518 and INC-2026-1007 manual referrals; batch sweep still at 070 |
| ST016 payments Sep–Oct | 4,101 | 18 recalled duplicates (INC-2026-0914); no Norrvik payments |
| ST017 recoveries 2026 | 1,263 | SB/SV/EX counts; Salvanta-only salvage; Quarryhill cases |
| ST018 assessor assignments | 3,928 | top vendor; no Fellgate after 2026-01-31; no Norrvik on UK claims |
| ST019 CRUD matrix | 340 | the truthful 8 CLR.T_RESERVE writers (PL-166, C08 new side); CLRRS150 (PL-167). Cross-checked: every program-table pair matches programs.yaml reads_tables/writes_tables exactly (0 mismatches, 0 extra rows). |
| ST020 interface run log Oct | 1,976 | CLX-IF-020 failure (INC-2026-0340); run counts |
| ST021 GL postings Oct | 5,638 | GL claim payments reconcile to ST016 October payments |
| ST022 currency rates | 33 | quarter-end rates (also in ST004 calc) |
| ST023 incident log | 25 | incidents up to 2026-11-10, with as-of status |
| ST024 Jira summary | 2,000 (CHUB-101..2100) | key_tickets with status as of 2026-11-11 (CHUB-298 still In Review), plus filler |
| ST025 product-peril matrix | 72 | Hem Sverige självrisk SEK 2,000 (PL-168, C17 new side) |
| ST026 copybook fields | 566 | matches copybooks.yaml exactly (50 copybooks, 566 fields, PIC and level identical) |

Total size of ST001–ST026: about 7.9 MB (the limit is 30 MB). The largest file is ST013 at 2.49 MB.

## Facts

208 facts:

| kind | count |
|---|---|
| aggregate_source | 93 |
| general | 48 |
| needle | 34 |
| temporal | 13 |
| hidden_sheet | 6 |
| chart_only | 4 |
| merged_cell | 3 |
| contradiction_new | 3 |
| contradiction_old | 2 |
| draft | 1 |
| approved | 1 |

- 94 entries carry an `aggregate` spec. 93 are kind aggregate_source; ST019-F001 is kind contradiction_new, copied from PL-166, and also has an aggregate spec.
- The aggregates cover:
  - claim type × region × year counts
  - reserve sums by product
  - Tier-3 referred claims
  - the Tier-3 60–64 band after 2026-10-01
  - top vendor by assignments
  - the month with the most FNOLs
  - negations, e.g. no Subsidence claims in DK, no Nordic BI claims, no Fellgate claims after it left the panel
- All 17 placements for ST001–ST026 are planted. world_ref, kind and exclusive are copied from each placement.

## Verification

- `verify_corpus.py --family structured.sheets --checks 1`: 208 PASS, 0 WARN, 0 FAIL.
- `check_aggregates.py`: 94 PASS, 0 FAIL.
  - To confirm it catches errors, I ran it on a copy of the manifest with one value changed. It exits 1.
- Determinism: two full runs give byte-identical files and an identical manifest. I checked by hashing the `extract.iter_units` text and the file bytes.
- Exclusivity:
  - Check 3 for this family: 5 PASS, 1 WARN, 0 FAIL. The WARN is ST001-F003: the needle '2024-05-31' is too generic. The specific needle LEGACY_SKADE_REF appears only in ST001.
  - Index searches for LEGACY_SKADE_REF, Telephone=50, Digital=41 and Broker=9 each hit only their own locator.
- Checks 6 (denylist), 7 (secrets) and 8 (guardrail), corpus-wide: 0 FAIL.

## Deviations

- **Row counts that differ from the anchor size, because world data fixes them:**
  - ST015 has 4,968 rows, not ≈1,200. The quarterly counts must equal the timeline metrics: 1,488 in Q2 and 1,530 in Q3.
  - ST019 has 340 rows (≈450 planned): every program-table pair in programs.yaml.
  - ST025 has 72 rows (≈90 planned): products × claim types.
  - ST026 has 566 rows (≈700 planned): every field in copybooks.yaml.
  - ST016 has 4,101 rows and ST018 has 3,928 rows; both come from the ST013-driven event model.
  - ST001 has about 4,770 rows in all, against a target of ≈5,000.
- **ST013 columns:** these follow `claims_profile.yaml: columns` exactly.
  - There is no separate policy_id, peril or branch column.
  - claim_type stands for peril, sub_region for branch area, and assessor_type/assessor_ref for the assessor ID or vendor.
- **PL-167 (CLRRS150):** the placement text says "no access to CLR.T_RESERVE", but programs.yaml lists CLR.T_RESERVE under reads_tables. The matrix therefore shows R only.
  - The fact says its only access is a read.
  - A negation aggregate (ST019-F011) confirms 0 C/U/D operations.
- **ST020** has no CLX-IF-042 rows: run timestamps would reveal the 02:15 schedule, which is exclusive to VS033. A negation aggregate records this.
- **ST010 FY2025 sheet:** IBNR and FNOL-acknowledgement % are left out because they are exclusive to LD003. Claims outstanding (2,318.4) is stated because may_state allows it.

## Changes made in the resume session

- ST015-F001: world_ref is now copied from PL-165 (RULE:BR-FRD-031).
- ST019-F001: kind changed to contradiction_new, copied from PL-166.
- ST023: status is now as of the log date. INC-2026-0518 showed "permanent fix released 2026-11-12", which is after the log date of 2026-11-10. It now reads "mitigated, permanent fix in progress".
- ST017: demand dates after the 2026-10-31 extract cut-off are now left blank.
- ST003: the column "Live since" is renamed "Live since / planned". Planned interfaces carry their Wave 1 or Wave 2 dates.
- ST011: the summary line now reports the real sheet count (4).

## Cross-file overlaps (not leaks)

- **ST001 column description:** contains the example claim ID CLM-UK-2025-118204. The text comes verbatim from tables.yaml. The same ID appears in RJ003's exclusive episode, but the episode's fact (the write-off) is not stated.
- **ST024:** "Wave 0 Denmark migration (41,250 claims)" comes from key_tickets.yaml. PL-101, which is exclusive to VS011, has world_ref WAVE:MW-1.
- **LD003-F029:** its needle "611.9" matches money amounts in ST013, ST016 and ST021 by coincidence (e.g. 611.92). The verifier treats needles under 8 characters as WARN, not FAIL.

## Unverified

- No OCR facts in this family, so OCR was not needed.
- I did not open the XLSX files in Excel or LibreOffice to check them visually. They load cleanly in openpyxl, and the chart XML follows the DrawingML chart schema.

## Fix pass (contradiction-hunter findings, 2026-11-16)

- **N1/N2/N6/m7 (ST024 vs TX070 filler tickets).** The filler tickets (every CHUB key not in key_tickets.yaml)
  now come from one shared, seeded core, `generators/common/jira_filler.py` (rng `jira:filler:core`), used by
  ST024 and TX070. All 2,000 rows agree on type, summary, status, assignee, reporter, created, resolved,
  component, fix version and labels (checked field by field). The core keeps assignees and reporters employed
  on the created date, uses squad members only while they are in the owning squad, and offers a service
  component only once its squad is formed (2025-02-03). Summaries use the names in force on the created date
  (reserve-svc before 2026-02-10, FRAUDNET before 2025-03-01, Adjuster Extranet before 2025-09-01, FNETCAL1 or
  FNETREF1 before 2025-03-01). Only active programs, live interfaces and introduced topics appear. Key tickets:
  ST024's blank reporters now use the TX070 rule (the named reporter, otherwise the assignee). The ';' in
  CHUB-281 and CHUB-401 is kept verbatim (the sniffer still picks ','). The ST024 'In Review' count (ST024-F007)
  is now 36.
- **m17 / N28 (world/wb/history.py).** Generated world tickets write their service name as of the created date,
  so CHUB-279 is now 'reserve-svc: null pointer on missing optional field'. A background incident now cites a
  generated ticket only when one was raised 0-60 days after the incident in a component that owns the affected
  system. Only INC-2025-0677 qualifies (CHUB-222); the other 12 have no follow-up ticket. INC-2026-0340 (late
  CPG confirmation file) now starts at the CLX-IF-020 scheduled run (2026-10-22 07:30) and names CLX-IF-020.
  ST023 was regenerated.
- **N8 (ST015).** customer_notice_due is now referral date + 10 business days in the claim's jurisdiction,
  excluding its public holidays (`common.add_bd_region`, `PUBLIC_HOLIDAYS` for UK/NO/SE/DK 2025-2026). This
  matches LD022 Table 2: 29 Apr 2026 gives UK 14 May and NO 15 May. It also matches the ST038 example (NO, 20
  Apr gives 5 May). 783 due dates changed. The referral model is now `csv_files.st015_referrals(claims=None)`,
  which can be imported without a Ctx. Q2 1,488, Q3 1,530, BS 902/444 and every other ST015 aggregate are
  unchanged.
- **m20 (ST015).** `claims.threshold_for` now gives the Tier-3 threshold (60 under BR-FRD-031 v2) for every
  Tier-3 claim, not only those scoring below 65 (53 rows changed; BS rows stay at 70).
- **N25/N26 (ST014, ST004).** Movements written by batch-only CLARA programs are now timestamped inside their
  JCL job's run window: from the schedule time for the job's typical elapsed time on ST011's Batch Window
  sheet. The windows are CLRRS110 01:30, CLRRS150 02:00, CLRRS130 03:00, CLRST040 21:30 and CLRRC050 22:00.
  `common.batch_elapsed()` reproduces ST011's own draws, so ST011 is byte-identical. The timestamps reuse the
  same rng draws, so every amount and count is unchanged; only the locator rows of ST014-F001..F015 moved.
- **N22 (ST001) / N23 (ST007).** ST001 and ST007 now list all 19 columns of CLR.T_FRAUD_REFERRAL; the world has
  no column history. A description parenthetical that cites a rule not yet known on the document date is dropped
  instead of the column: RULE_ID is 'Business rule applied', and CUSTOMER_NOTICE_DUE_DT is 'Customer notice due
  date'. ST007 maps RULE_ID -> fraud.referral.rule_id (Direct), and its Target Coverage row 70 now names the
  CLARA source. ST001 has 462 columns and ST007 has 462 source columns. MAP-0042 and MAP-0070 are unchanged.
- **m19 (ST020).** Fixed through the world: the incident now starts at 07:30, so the 07:30:49 failed run no
  longer precedes it. The rerun moves from 18:36 to 12:16 (start + 286 min).
- **Not fixed.** m41: the world has Fellgate on the panel until 2026-01-31 (VEN-03 panel_to, and DEC-019 takes
  effect then), so appointments on 21-23 Jan do not contradict it. Changing the cut-off would shift ST013-F026
  and ST018-F001, which questions use. m42: DK claims going to Norrvik follows claims_profile.vendor_by_region
  and BR-ASM-016. The conflict is VEN-02's role text inside the world (vendors.yaml), which is not this
  family's file.
- ST005 also changed in this regeneration: one effective date (Versions!I181). It comes from another agent's
  world/wb/rules.py edit, not from this pass.
- Checks: verify_corpus --family structured.sheets --checks 1,3,6,7: 208 PASS, 1 WARN (ST001-F003, as before),
  0 FAIL. check_aggregates: 94 PASS. Two runs gave identical extracted text and identical bytes for ST001-ST026.

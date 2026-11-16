# visuals.decks_b — VS015–VS028 (PPTX)

Generator: `generators/visuals/gen_decks_b.py` (helpers in `generators/visuals/decks_b_lib/`:
`core.py` deck template and shape/connector/chart/table helpers, `raster.py` Pillow diagrams, table images
and mock UI screens, `phrases.py` filler phrase banks, `common.py` document control and exclusivity guards,
`decks_1/2/3.py` one builder per deck). Manifest: `manifests/visuals.decks_b.facts.yaml`.

Run: `.venv/bin/python -I generators/visuals/gen_decks_b.py [--only VS015,...]`. It deletes and rewrites only
`corpus/upload/visuals/VS015_*` … `VS028_*` and the manifest. `--only` merges with the per-file fact cache in
`build/cache/vs_decks_b/facts_by_file.yaml`. A full run takes about 3 s and needs no cache.

## Files

| id | file | MB | slides | facts | what it tests |
|---|---|---|---|---|---|
| VS015 | VS015_sentinel_rename_comms.pptx | 0.08 | 12 | 21 | FRAUDNET→Sentinel rename (PL-107 title slide), DNS alias only in notes of slide 4 (PL-108), interface flows as labelled connectors, old/new name table, raster timeline with alt text |
| VS016 | VS016_reserve_engine_design.pptx | 0.14 | 16 | 30 | reserve-svc→reserve-engine (PL-109 slide 2), topic names only on connectors, programs grouped as SmartArt-style groups, raster ERD and sequence diagram, CLRGL090/IA-25-07 only in notes, tier3-review-days = 21 (true on 2026-02-24) |
| VS017 | VS017_clara_batch_landscape.pptx | 0.25 | 14 | 38 | reserve-table writers as connectors (PL-110/111), group 'CLRYGL90 (annually 31 Dec 23:30)' (PL-112), job step chains as connectors, lane-by-area timeline, native chart, table images. The CLX-IF-042 schedule is omitted on purpose (exclusive to VS033); CLRNRSV3 says "per CLX-IF-042 catalogue entry" |
| VS018 | VS018_assessor_vendor_panel_2025.pptx | 0.16 | 11 | 19 | stale Jan 2025 panel with Fellgate (PL-113, C14 old side), fee chart (chart only), interface schedules on connectors, Adjuster Extranet name (pre-rename), grouped supplier networks |
| VS019 | VS019_incident_review_inc_2025_0412.pptx | 0.09 | 11 | 24 | impact chain connectors (PL-114), root cause only in notes (PL-115), CLX-IF-043 → 03:45 action (PL-116, C12 new side), dependency map with consumer teams on arrows |
| VS020 | VS020_board_update_q3_2026.pptx | 0.10 | 12 | 16 | combined ratio 97.8% only in a native chart (PL-117, exclusive), "PR" / "the CFO" in notes (PL-118), FY2025 table, wave status group |
| VS021 | VS021_claims_handler_training_claims_hub.pptx | 0.42 | 17 | 23 | mock Claims Hub screenshots (FNOL Claim Type drop-down PL-119), CLARA green-screen CLRM010/FN01 with PERIL (PL-120), terminology table, journey swimlane |
| VS022 | VS022_raci_authority_matrix_2025.pptx | 0.11 | 12 | 22 | June 2025 authority matrix, Team Leader payment £50,000 (PL-121, C16 old side), escalation ladder on connectors, three swimlanes (owner only by lane), stage owners as of June 2025 (Quill acting) |
| VS023 | VS023_nordic_claims_operations_overview.pptx | 0.11 | 14 | 19 | frost seasonality only in notes (PL-122), staff chart, org connectors "reports to", migration path connectors |
| VS024 | VS024_recovery_kpis_2025.pptx | 0.09 | 13 | 25 | recovery rates only in a native chart (PL-123, 3 exclusive facts), pursue/solicitor decision tree on connectors, recovery swimlane, rule changes in 2025 (temporal) |
| VS025 | VS025_tier_classification_decision_tree.pptx | 0.13 | 12 | 23 | decision diamonds with Yes/No connectors (PL-124/125), routing connectors, v2→v3 change table, raster worked examples and quick-reference card |
| VS026 | VS026_security_identity_architecture.pptx | 0.09 | 12 | 17 | partner/workforce access paths with policies on connectors (PL-126 'partner limit 50 req/s'), trust zones as groups, raster OIDC sequence, hosting table (pre-rename names) |
| VS027 | VS027_test_strategy_overview.pptx | 0.12 | 14 | 17 | test pyramid group, pipeline gates on connectors, synthetic-data chart, reserve-svc (pre-rename) parallel run, severity/criteria tables as images, IBM Callum Fairbairn namesake |
| VS028 | VS028_programme_kickoff.pptx | 0.10 | 12 | 16 | kick-off led by Victoria Ashcombe in notes (PL-127), DEC-001 in notes, governance connectors, who-is-who groups, raster roadmap with alt text |

Total size 1.99 MB (budget 45 MB). Every file is far below 48 MB. Slide counts are 11–17, inside the 10–40 range.

## Facts

310 facts, 21 of them placements (PL-107 … PL-127: all planted at their location_hint, with world_ref,
exclusive and kind copied from the placement plus `placement` / `placement_key`). None of these placements has
also_in entries. Exclusive facts: 4 (PL-117 and PL-123, chart only).

Facts per kind: general 101, arrow_only 78, visual_only 20, speaker_notes 17, image_text 16, lane_only 15,
chart_only 15, image_table 12, alt_text 10, temporal 8, screenshot 8, alias_use 6, contradiction_old 2,
contradiction_new 1, terminology 1. 36 facts are OCR-verified (Apple Vision).

## Verification (2026-11-16)

- `verify_corpus.py --family visuals.decks_b --checks 1`: 310 PASS, 0 WARN, 0 FAIL (OCR on).
- `--checks 3` (exclusivity): 4 PASS. Index regex searches (`build/index_visuals.decks_b`) find 97.8 (combined
  ratio) and 41.2 / 18.7 / 36.5 (recovery rate) only in their chart locators.
- No exclusive needle from any other manifest (42 checked) appears in the extracted text of VS015–VS028. Spot
  greps for other files' exclusive values (CLX-IF-042 02:15, Reserving Committee cadence, CLRNRSV1 restart
  rule, 200Gi, MAXDEPTH, Project Larchmont, FRO-CHK-3, 3.1% indexation, SMS notice) found nothing.
- Determinism: two full runs, and a from-scratch run (outputs, manifest and cache deleted first), produce
  byte-identical PPTX files, byte-identical manifests and identical `extract.py --all` hashes.
- Checks 6 (denylist) and 7 (secrets): PASS.

## Changes made in the resume session

- Unlabelled connectors now carry an empty, invisible text box named `label:<connector>`. Without it, the
  extractor's nearest-text fallback took rotated lane headers or neighbouring boxes as labels. Examples:
  "Receive notification -> Validate policy and cover [label: Contact Centre]" (VS022 slides 7–9) and
  "CLARA -> Recoveries [label: Fraud and settlement]" (VS028 slide 5). Only those spurious labels changed.
- Phrase-bank bullets are capitalised. Before, VS025 and VS028 had a bullet starting "confirm that…".
- VS026: the DPO line no longer repeats the title. VS019: the notes no longer say "the CFO at the time" in a
  May 2025 document.
- Added 12 non-exclusive facts to VS026 and VS027, which had the thinnest manifests.

## Deviations

- **PL-126 timing (VS026, dated 2025-04-14).** ADR-029 (the 50 req/s partner limit) is dated 2026-04-20, and
  the Assessor Portal name dates from 2025-09-01. The placement still requires both. The slide is a
  target-state diagram and does not cite ADR-029 by number. It captions the box "(target-state name for the
  Adjuster Extranet)", and every other slide uses the April 2025 names (Adjuster Extranet, DOCSTOR). The fact's
  `notes` record the conflict.
- **lane_only facts** are verified only by the step text being on the slide. Lane membership is geometric,
  and the verifier does not check positions.
- VS020 notes say "Speaker: PR (CFO)" and use "the CFO:" as a speaker tag, which makes the alias explicit.

## Not verified

- Visual layout was checked in LibreOffice renders of VS021 s4, VS022 s7, VS025 s2 and VS028 s5 only. The decks
  were not opened in PowerPoint.
- OCR results come from the harness OCR cache, which is keyed by image sha1 and was filled by real Apple Vision
  runs on these exact image bytes.
- No packages were installed.

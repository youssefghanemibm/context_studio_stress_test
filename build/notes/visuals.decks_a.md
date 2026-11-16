# visuals.decks_a: VS001 to VS014 (PowerPoint)

Generator: `generators/visuals/gen_decks_a.py`, with one module per deck in `generators/visuals/decks_a_lib/vsNNN.py`. The shared code is:

- `core.py`: Deck, slide builders, connectors, charts, the fact and placement API and zip normalisation.
- `lanes.py`: swimlanes.
- `orgchart.py`: org charts.
- `raster.py`: Pillow diagrams, image tables and mock UI screens.
- `phrases.py`: rng phrase banks for notes and filler.
- `common.py`: document control, history and contacts.

Manifest: `manifests/visuals.decks_a.facts.yaml`, 263 facts.

Run it with `.venv/bin/python -I generators/visuals/gen_decks_a.py [--only VS007]`. One run takes about 6 seconds and needs no LibreOffice. It deletes and rewrites only `VS001_*` to `VS014_*` in `corpus/upload/visuals/`. With `--only`, it merges into the existing manifest. After saving, it self-checks every needle that does not need OCR.

## Files

| id | slides | MB | facts | what it tests |
|---|---|---|---|---|
| VS001 claims lifecycle swimlane | 17 | 0.37 | 27 | Triage decision flow with arrow_only branch labels (PL-075 fast-track label). Lane-only ownership on slides 4 to 8 (PL-074 subrogation step in the Recoveries & Subrogation (Group) lane; PL-076 'Notify customer of referral' in the Claims Operations lane, below SIU). Two image tables of service levels. A Claims Hub claim-overview screenshot. Speaker notes. |
| VS002 target architecture deck | 17 | 0.37 | 24 | Raster context and runtime diagrams with labelled arrows, plus alt text. Nested OpenShift namespace groups (PL-080 'chub-fraud' group). Event-flow connectors (PL-077 notice-due topic; PL-078 two connectors MQ → ESP → reserve-engine). Notes with the Wave 2 and decommission dates (PL-079). Kafka topic image table. |
| VS003 interface landscape | 16 | 0.16 | 23 | Downstream reserve-movement map. The interface ids live only on the connector labels (PL-081 to PL-084: CLX-IF-043/051/047/055). Catalogue tables. Protocol and criticality charts (aggregate_source). A raster payments map with alt text. |
| VS004 org chart March 2024 (STALE) | 14 | 0.08 | 21 | As at 2024-03-01: Martin Calloway, Recoveries Manager, reporting to Rob Tennant (PL-085, contradiction C02 old side). 'Ingrid Sørensen – Claims Director' with the Head of SIU reporting to her (PL-086, alias). FRAUDNET-era names. The org chart uses connectors and rotated text boxes. |
| VS005 org chart October 2025 | 14 | 0.08 | 24 | After the 2025-09-01 reorganisation: Freya Lindahl reports to Ingrid Ashby (PL-087, C02 new side). Niall Brannigan reports to the CRO (PL-088). Siobhan Quill reports to Freya Lindahl (PL-089). The reporting lines are carried by the connectors. |
| VS006 steering committee 8 Oct 2026 | 13 | 0.17 | 15 | Cumulative spend appears only in the native chart (PL-090, exclusive: 31.2 at 2026 Q3). The 'PR' contingency drawdown appears only in the slide-6 notes (PL-091). Milestone image table. Defect chart. |
| VS007 fraud referral process from 1 Oct 2026 | 16 | 0.23 | 20 | The decision diamonds carry the Sentinel thresholds (≥ 65; Tier-3 and ≥ 60). The 'Yes → Refer to SIU' meaning lives only in the connectors (PL-092, PL-093). Slide 3 swimlane: 'Human review before any decline' sits in the SIU lane (PL-094). Notice-timeline raster with alt text. Two fraud referral record screenshots. Volume chart. |
| VS008 reserving process | 15 | 0.21 | 23 | Large-loss arrow '> £250,000 → Notify ReCede within 24h' (PL-095). The committee chair appears only in the slide-5 notes (PL-096). Authority image table (BR-RSV-003 v3). Tier-3 review-interval chart. Program-to-table group. |
| VS009 recovery and subrogation flow | 14 | 0.25 | 17 | The write-off > £10,000 step sits in the Head of R&S lane (PL-097, group locator). Solicitor connector (PL-098). Two image tables of recovery rules. Recovery-case mock screen. |
| VS010 Claims Hub service map | 13 | 0.26 | 17 | Nested group 'chub-recovery' with owner label 'Squad Fraud & Settlement' (PL-099). Text box rotated 270°: 'reserve-engine (formerly reserve-svc)' (PL-100). Request-flow connectors. REST API image table. Service-map raster with alt text. Chart. |
| VS011 data migration waves | 13 | 0.14 | 14 | Claims migrated per wave appear only in the native bar chart (PL-101, exclusive; also_in TX011). Rehearsal charts. Timeline raster with alt text. |
| VS012 Wave 1 cut-over plan | 14 | 0.17 | 11 | Freeze window only in the slide-3 notes (PL-102). Cut-over console screenshot. Runbook phases as connectors. |
| VS013 claims KPI dashboard Q3 2026 | 14 | 0.16 | 14 | Referral rate by quarter only in the line chart (PL-103, exclusive: Q1 2.3, Q2 2.8, Q3 2.8). 2026 H1 settlement days only in the column chart (PL-104, exclusive: motor 31, home 47). MI dashboard screenshot. |
| VS014 NISA Circular 2026/04 briefing | 14 | 0.11 | 13 | The SMS clarification appears only in the slide-6 notes (PL-105, exclusive; also_in TX043-F003). Alt text on the slide-2 timeline: 'Circular published 20 Nov 2025, effective 1 Apr 2026' (PL-106). Proposed referral-flow connectors. |

Total size is 2.6 MB, against a budget of 45 MB or less. Every file is under 0.4 MB.

### Facts per kind

| kind | facts |
|---|---|
| general | 61 |
| speaker_notes | 36 |
| visual_only | 35 |
| arrow_only | 30 |
| chart_only | 22 |
| temporal | 15 |
| lane_only | 13 |
| image_table | 9 |
| image_text | 9 |
| alt_text | 9 |
| alias_use | 7 |
| screenshot | 6 |
| contradiction_old | 5 |
| contradiction_new | 4 |
| aggregate_source | 2 |

- 40 facts carry a `placement`. All 33 placements (PL-074 to PL-106) are planted.
- 9 facts are exclusive.
- 24 facts are verified by OCR.

## Techniques

- **Connector flowcharts (`where: connector`):** VS001, 002, 003, 004, 005, 007, 008, 009, 010, 012 and 014.
- **Swimlanes:** VS001, 007, 008 and 009.
- **Raster architecture or timeline diagrams with OCR and alt text:** VS002, 003, 007, 010, 011 and 014.
- **Native charts:** VS003, 006, 007, 008, 010, 011 and 013.
- **Image tables:** VS001, 002, 006, 008, 009 and 010.
- **Mock Claims Hub screens:** VS001, 007, 009, 012 and 013.
- **Nested groups:** most decks.
- **Rotated text boxes:** VS004, 005 and 010.
- **Speaker notes:** on every content slide.

## Verification (2026-11-16 resume run)

- `verify_corpus.py --family visuals.decks_a --checks 1`: **263 PASS, 0 WARN, 0 FAIL**. This includes the 24 OCR facts, checked with Apple Vision.
- `--checks 3,6,7 --index-dir build/index_visuals.decks_a`: exclusivity 9 PASS, denylist PASS, secrets PASS.
- Determinism: two consecutive full runs gave byte-identical PPTX files and an identical manifest, and the `extract.py --all --no-ocr` hash matched.
- Exclusivity spot-check, `build_index.py --search` plus an OCR text scan of every picture in VS001 to VS014: the exclusive values appear in these decks only at their locators.

## Deviations and notes

- **VS008-F009 needle changed** from 'Team Leader £100,000' to '£100,000'. Vision OCR reads the two-column authority table column by column, so a needle spanning the label and value cells cannot match. I tried narrower widths and removing the column rules, and neither helped. The statement still names the Team Leader row.
- **VS013-F014 added** (referral rate Q2 2026 = 2.8). It was appended at the end of the deck so that the existing fact ids stay stable, because `questions/graph_expectations.draft.yaml` already references VS001 and VS002 fact ids.
- **also_in:** where the partner manifest already exists, `also_in` now lists the partner fact ids. A partner fact qualifies when it points back at this deck or has exactly the same world_ref. This gives VS014-F008 → TX043-F003. TX011 has no matching fact, so VS011-F001/F002 list the TX011 file path.
- **Lane-only facts with `where: text`** (VS001-F005/F006/F012/F013/F015/F017, VS007-F006/F007/F008) carry `verification: manual-lane`. Their notes give the step-box and lane-band geometry. The others (VS001-F009/F010, VS009-F001/F003) use `where: group` on a group named 'Lane: <team>'.

## Unverified items and cross-family observations (other agents' files; not changed)

- `corpus/upload/structured/ST024_jira_ticket_summary.csv` row CHUB-262 says 'Wave 0 Denmark migration (41,250 claims)'. That is part of the exclusive PL-101 fact (VS011-F002). Check 3 does not flag it because the chart needle format differs.
- `corpus/upload/text/TX075_meeting_notes_sentinel_calibration.html` says '2.3% of scored claims (observed)' under BR-FRD-012 v2. That overlaps the exclusive PL-103 Q1 2026 value (VS013-F004).
- I spot-checked the visual layout by rendering only a few slides (VS008 slides 3 and 6, VS013 slide 4) after this resume. I did not re-render every slide.

## Fix pass (2026-11-16, contradiction-hunter findings)

- **VS004 forum remit (m3/m8/m35).** Committee remits are undated world text in today's names. New helper `common.asof_systems(W, text, d)` rewrites renamed system names to the name in force on the deck date, so VS004 (2024-03-01) now reads "Fraud rules, FRAUDNET thresholds, SIU performance". VS005 uses the same helper (no change, Sentinel is correct in Oct 2025).
- **Org-chart document control (m4).** VS004/VS032 (March 2024) and VS005/VS044 (October 2025) now take their document reference, version and history from the shared `generators/visuals/org_chart_control.py`: CLM-ORG-2024-03 v1.0 (0.1 / 0.2 / 1.0) and CLM-ORG-2025-10 v2.0 (1.0 March 2024 chart / 1.9 / 2.0). Only the filler notes on slide 14 changed as a side effect.
- **VS012 distribution (m5).** Uses `W.team_name("T02", d)`: "Claims Operations (Group)" on 2026-09-04, not the pre-re-org "Claims Operations UK".
- **VS006 contingency notes (m40).** The PL-091 needle is kept, but the sentence now reads "PR asked for a £1.8m contingency drawdown for Wave 2 to come to this meeting as a formal paper", followed by "The request comes from the programme (Victoria Ashcombe and Arjun Kesavan)". So PR is the approver, matching DEC-010, TX001 and TX013. The VS006-F007 statement was updated (same id). The placement wording itself ("PR asked for…") is what made the CFO look like the requester.
- **Wave 2 date before DEC-011 (m43).** New shared helper `generators/visuals/wave_dates.py`: a wave's date counts as known from the decision that confirms it (DEC-011, 2026-10-08). VS011 (2026-09-21) now shows Wave 2 as "Early 2027 (TBC)" in the wave table, notes, timeline raster and alt text. VS011-F003 has a new statement and VS011-F005 a new needle ("date and freeze to be confirmed", world_ref DECISION:DEC-011); both keep their ids. VS006 (the 2026-10-07 pre-read for the meeting that confirmed the date) keeps 15 Feb 2027 as the proposal: slide 7 says "Cut-over (proposed, for confirmation today)" and the slide-12 milestone status is "For confirmation". VS002 (2026-03-16) must still state 2027-02-15 in the slide-9 notes because PL-079 requires it. Its notes now call it "a provisional planning date" that the Steering Committee still has to confirm. This residual early date comes from the placement and is reported, not fixed.
- Verification: `verify_corpus --family visuals.decks_a --checks 1,3,6,7 --index-dir build/index_fix_textvis`: 263 PASS, 0 FAIL. Two consecutive full runs gave byte-identical decks and manifest.

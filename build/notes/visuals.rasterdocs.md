# visuals.rasterdocs: image-led DOCX (VS029-VS039) and raster PDFs (VS040-VS050)

Generator: `generators/visuals/gen_rasterdocs.py` (helper package `generators/visuals/raster_lib/`).
Manifest: `manifests/visuals.rasterdocs.facts.yaml` (284 facts, 24 placements).

```
.venv/bin/python -I generators/visuals/gen_rasterdocs.py [--only VS033,VS044] [--ocr-check] [--count-pages]
```

The script deletes and rewrites only `corpus/upload/visuals/VS029_*` to `VS050_*` and its own manifest.
A full run takes about 15 s, plus about 1 min with `--count-pages`, which uses LibreOffice with profile key `vs_rasterdocs_pages`.
It needs no cache: `build/cache/vs_raster/` is scratch only.

## Files

DOCX files have a cover page, a document-control table, version history, approvers taken from the world, a distribution list and contents. Each section has one or two short paragraphs, a raster figure with a caption and alt text (`descr`), and a glossary. Headers and footers carry the doc ID and version, with "Page X of Y" fields. The body prose deliberately does not restate the image facts. Page counts below come from the LibreOffice render.

| id | ext | MB | units | what it tests |
|---|---|---|---|---|
| VS029 | docx | 1.07 | 13 pp, 8 figs | ADR timeline, register table image, superseded decisions (PL-128 "ADR-017 supersedes ADR-005", fig 3), reserve-sync arrows, rename figure; 1 comment |
| VS030 | docx | 0.78 | 13 pp, 8 figs | Claims Hub mock UI screenshots; PL-129 review cadence 14 days (screenshot, fig 7); PL-130 Tier-3 threshold 60 in alt text only (fig 4); 1 comment |
| VS031 | docx | 0.86 | 13 pp, 8 figs | process swimlanes (lane_only facts), value chain with stage owners, RACI table image; PL-131 "Sentinel score within 15 minutes" in alt text (fig 2) |
| VS032 | docx | 0.59 | 11 pp, 6 figs | STALE 2024 org chart (C02): PL-132 "Martin Calloway — Recoveries Manager" (fig 1); Ingrid Sørensen pre-marriage name; 2024 titles |
| VS033 | docx | 1.56 | 14 pp, 9 figs | interface diagrams. PL-133 (EXCLUSIVE): the CLX-IF-042 schedule "daily 02:15" appears only in a raster arrow label in fig 2. Also PL-134 CLX-IF-047, catalogue table images, the 042 impact graph and the MQ queue map; 1 comment |
| VS034 | docx | 0.47 | 12 pp, 7 figs | matplotlib charts with values only in pixels. PL-135 (EXCLUSIVE): INC-2026-0702 overdue reviews, 412 down to 0 (fig 1). Also the cadence step chart, the authority bar chart, an incident diagram and tiles; 1 comment |
| VS035 | docx | 0.61 | 13 pp, 8 figs | fraud workflow swimlanes; PL-136 deferral > 30 days branch (fig 3); threshold history chart; event/topic arrows; 1 comment |
| VS036 | docx | 0.58 | 14 pp, 9 figs | CLARA 3270 green-screen maps (2023, FRAUDNET era, threshold 070); PL-137 CLRM320 NEXT-REVIEW (fig 5); 1 comment |
| VS037 | docx | 1.42 | 12 pp, 7 figs | CLARA ERDs; PL-138 RSV_MOVEMENT.RSV_ID → T_RESERVE.RSV_ID FK (fig 1); table inventory image as of 2025-03-24; 1 comment (no fact) |
| VS038 | docx | 0.61 | 11 pp, 6 figs | schematic vendor map; PL-139 Vardholm (map image); vendor register table image, SLA chart, vendor interface arrows (names as of 2025-06-02) |
| VS039 | docx | 0.40 | 11 pp, 6 figs | PL-140 (EXCLUSIVE): the 2024 FNOL channel mix appears only in the fig 1 alt text (the donut has no value labels). Also the channel architecture arrows and the acknowledgement flow |
| VS040 | pdf | 0.82 | 2 pp | target architecture poster; PL-141 OpenShift clusters (p1); service catalogue image (p2) |
| VS041 | pdf | 0.36 | 2 pp | subrogation swimlane poster; PL-142 limitation diary 30/66 months (p1); rules table image (p2) |
| VS042 | pdf | 0.51 | 4 pp | KPI charts; PL-143 fraud referrals Q3 2026 1,530 (p2 chart); defects by severity; milestones |
| VS043 | pdf | 0.67 | 2 pp | interface landscape; PL-144 CLX-IF-058 monthly, 3rd business day (p1); dependency chain (p2) |
| VS044 | pdf | 1.97 | 4 pp | CURRENT org chart, October 2025, after the re-org; PL-145 Lena Kristiansen — Head of Reserving reporting to the CFO (p1) |
| VS045 | pdf | 0.53 | 5 pp | Claims Hub screenshot pack; PL-146 claim ref CLM-UK-2025-118204 (p3) |
| VS046 | pdf | 0.37 | 4 pp | Sentinel dashboard screenshots; PL-147 "Thresholds: 65 (all) / 60 (Tier-3)" (p2) |
| VS047 | pdf | 0.83 | 2 pp | infrastructure network diagram; PL-148 MQ channel PRD1 – CLRQM01 – HUBQM01 (p1); hosting table image (p2) |
| VS048 | pdf | 0.55 | 2 pp | ERD poster (2025-03-24, reserve-svc); PL-149 amount_minor BIGINT (p1) |
| VS049 | pdf | 0.29 | 2 pp | tier decision tree poster (BR-TRI-003 v3); PL-150 Nordic thresholds NOK/SEK/DKK (p1) |
| VS050 | pdf | 0.41 | 2 pp | programme roadmap poster; PL-151 CLARA decommission 2027-09-30 (p1) |

The PDFs are raster pages at 200 dpi. Each page's text layer holds only its title line. All facts use `pdf_page` with `ocr: true`.

The 22 files total 16 MB, against a budget of 45 MB. The largest file is 1.97 MB.

## Facts (284)

- By kind:
  - image_text 163, image_table 33, screenshot 33.
  - header 11, footer 11, general 11, comment 7.
  - lane_only 5, alt_text 3, temporal 3, chart_only 2, visual_only 1, contradiction_old 1.
- By locator kind: docx_image (ocr) 165, pdf_page (ocr) 87, docx_header 11, docx_footer 11, docx_comment 7, docx_alt_text 3.
- Exclusive facts:
  - VS033-F005: the CLX-IF-042 schedule.
  - VS034-F003 and VS034-F004: the start and end points of the PL-135 chart.
  - VS039-F003: the 2024 FNOL channel mix.
- also_in mappings:
  - PL-132 maps to VS004-F007 and the VS004 path.
  - PL-143 maps to ST034-F001 and ST038-F001, plus both paths.
- Raster arrow labels and raster chart values that are not placements use kind `image_text`, with a note: "raster arrow label ..." or "raster chart rendered by matplotlib ...". The reason is that the verifier reserves `arrow_only` for native pptx connectors and `chart_only` for native xlsx/pptx charts. Helpers: `arrow_spec` and `chart_spec` in `raster_lib/facts.py`.

## Verification (2026-11-16)

- `verify_corpus.py --family visuals.rasterdocs --checks 1`: 282 PASS, 2 WARN, 0 FAIL, all with full Apple Vision OCR.
  - Both WARNs come from `kind: chart_only` copied from placements PL-135 (VS034) and PL-143 (VS042), as the spec requires. The verifier expects chart_only only on native charts, and a raster DOCX or PDF cannot carry one. Kept deliberately.
- Check 3 (exclusivity, own index `build/index_visuals.rasterdocs`, built with `--no-ocr`): 4 PASS.
- OCR audit of all my files (extract.py `--all` with OCR):
  - "02:15" appears only in VS033 image2.
  - "412 overdue" and "0 overdue" appear only in VS034 image1.
  - The channel-mix percentages appear only in the VS039 alt text.
  - None of the 42 exclusive needles in the other manifests appears in my text.
  - CLRNRSV3 is never mentioned.
- Denylist, forbidden terms and secret patterns were also run over the OCR text, beyond what the index covers: 0 hits.
- Determinism: two consecutive full runs gave byte-identical files and manifest, so the extracted text is identical too.
- Temporal audit:
  - System and service names are checked against their rename dates.
  - Person names and titles are checked as of each anchor date, interface schedules as of the date, and not-yet-live interfaces appear only as "planned <date>".

## Fixes in this session (resume)

- VS048-F003 failed OCR on the entity heading. It now points to a new world-backed callout, "source values: CLAIMS_HUB or CLARA_BRIDGE", taken from the column description in tables.yaml.
- 34 WARNs: non-placement arrow and chart facts were moved to image_text with notes.
- Anachronisms fixed with the new `ctx.asof_names`, which rewrites current system names in world free text to the as-of names:
  - VS037 table inventory: "DOCSTOR / Evidence Vault ids" became DOCSTOR.
  - VS038 vendor-interface labels: Evidence Vault and Assessor Portal now use the 2025-06-02 names.
  - VS038 alt text.
- Comments that invented or restated facts:
  - VS036: "NEXT-REVIEW is mandatory..." was not in the world. Replaced with a neutral training-capture note.
  - VS037: "FK3 ..." referred to a foreign key that does not exist. Replaced with a neutral note.
  - VS035: the comment restated the image-only deferral approver. It now only cites BR-FRD-036 v2.
- Needles that also appeared in body tables or glossaries were made image-specific: VS031-F003, VS032-F009, VS033-F021, VS034-F012, VS035-F012, VS039-F006.
- VS032's Sørensen fact changed from contradiction_old to temporal. Only PL-132 is C02.
- VS049 decision tree re-laid out: the "No" path from the £50k question used to pass through the Tier-2 diamond. The Tier-2 test is now directly below, with Tier-2 to its left and Tier-1 below.

## Deviations and unverified items

- 2 WARNs (chart_only on raster), as explained above.
- VS047's hosting table shows SYS17's world `type` field, "Vendor assessor portal", a generic descriptor, next to the as-of name "Adjuster Extranet". This was left as is.
- VS029-F003 (`visual_only`): needle "ADR-019" only proves the label is present. The February 2026 position is visual. ADR-019 is also discussed in the section 7 body.
- I did not open every figure. I spot-checked VS032, VS033, VS036, VS044, VS046, VS048 and VS049. The rest rely on OCR verification and the audits above.

## Fix pass (2026-11-16, contradiction-hunter findings)

- **VS032 sites map (m2).** `locations.functions` are undated strings in today's team names. `docs_a._asof_function` maps the team-named ones back to the team name in force on the document date (T02/T08/T11 via `team_name`). On 2024-03-01 Leeds shows "Special Investigations Unit (SIU)", Bristol shows "Recoveries (UK)" and Stockholm shows "Recoveries (Nordics)". The VS032-F014 statement was updated (same id and needle).
- **Org-chart document control (m4).** VS032 is now CLM-ORG-2024-03 v1.0 with the same history as VS004, and VS044 is CLM-ORG-2025-10 v2.0 like VS005, both via the shared `generators/visuals/org_chart_control.py`. The VS032-F002 needle changed from CM-CLM-ORG-2024 to CLM-ORG-2024-03 (same id).
- **VS036 FR03 program (m30).** New `ctx.program_id(pgm, d)` applies `programs.renamed_from`. On 2023-09-11 the CLRM410 screen header and the map reference table show FNETREF1, not CLRFR030. The VS036-F009 statement was updated (same id).
- **VS050 Wave 2 (m43).** The roadmap is dated 2026-09-21, before DEC-011 confirmed the date. It now shows "Wave 2 (planned) early 2027 (TBC)", and the waves table has cut-over "early 2027 (TBC)" and freeze "TBC" (helper `generators/visuals/wave_dates.py`). The VS050-F003 statement changed and its world_ref is now DECISION:DEC-011 (same id and needle).
- **VS040 (N4).** Confirmed with an OCR index search (`build/index_fix_textvis`): `notification.fraud-notice.sent.v1` appears in no upload file. The VS040 service catalogue lists only `notification.sent.v1` as at 16 Mar 2026.
- Verification: `--checks 1,3,6,7`: 282 PASS, 2 WARN (the known chart_only-on-raster cases), 0 FAIL. Two full runs gave byte-identical output.

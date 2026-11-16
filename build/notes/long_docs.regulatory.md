# long_docs.regulatory: generator notes

Generator: `generators/long_docs/gen_regulatory.py` (builders in `generators/long_docs/regulatory_lib/`).
Manifest: `manifests/long_docs.regulatory.facts.yaml` (174 facts). Per-file fact caches: `build/cache/ld_regulatory/facts_<FID>.yaml`.

```
.venv/bin/python -I generators/long_docs/gen_regulatory.py            # all 12 files, about 60 s
.venv/bin/python -I generators/long_docs/gen_regulatory.py --only LD021
```

The run is deterministic. Two consecutive full runs gave byte-identical files, including the LibreOffice `.doc` files, an identical `harness/extract.py --all --no-ocr` hash for every file, and an identical manifest.

## Files

| id | ext | size | pages | facts | what it tests |
|---|---|---|---|---|---|
| LD003 | pdf | 0.68 MB | 150 | 48 | Multi-column layout: 2- and 3-column frames, plus full-width title and table pages. Multi-page tables, some with repeated headers and some without. Footnotes at the bottom of columns (PL-026, p.33). Vector charts (bar, line, pie, gantt). Running header with NISA-FRN 40417 (PL-027). Reading-order trap PL-025 (p.54): the sentence runs from the bottom of column 1 to the top of column 2, and both halves are recorded in `halves`. Table 4.2 spans pp.86-89, with the IBNR row on p.87 (PL-024). §7.3 recalibration from 70 to 65 is on p.112 (PL-028). |
| LD004 | doc | 0.10 MB | 33 | 9 | Motor UK 2012 wording. Acknowledgement promise of 5 working days in Claims conditions (PL-029, C11). Schedule of excesses table with £150 / £75 (PL-030). |
| LD005 | doc | 0.09 MB | 34 | 9 | Home UK 2014 wording. Section 1 excesses: EoW £350, subsidence £1,000, standard £200 (PL-031). |
| LD006 | doc | 0.09 MB | 30 | 8 | Commercial Property 2011 wording. General conditions: notify within 14 days, BI indemnity period 12 months (PL-032). |
| LD007 | doc | 0.08 MB | 28 | 9 | SME Liability 2013 wording. Schedule table: PL £2,000,000 (PL-033), EL £10,000,000. |
| LD008 | doc | 0.08 MB | 28 | 9 | Swedish home wording. Självrisk SEK 1 500 (PL-034, C17). Besiktningsman and regress terminology. |
| LD009 | doc | 0.09 MB | 32 | 11 | Norwegian motor wording. Egenandel NOK 4 000 and glasskade NOK 1 500 (PL-035). Skadetakstmann and skademelding terminology. |
| LD010 | doc | 0.08 MB | 28 | 8 | Danish home wording. Selvrisiko 1.200 kr. (PL-036). Taksator and regres terminology. |
| LD011 | doc | 0.09 MB | 32 | 11 | Norwegian home wording. Egenandel NOK 4 000 (Egenandel section) plus frostskade covered (Dekning section) (PL-037, split over two sections). |
| LD021 | pdf | 31.16 MB | 139 | 31 | Image-heavy field guide containing about 165 procedural JPEG "photos" (water stains, fire char, smoke, cracked plaster, stepped brick cracks, vehicle panels, glass, roofs, forced doors, floors, flood lines), plus diagrams and tables rendered as PNG. Raster-only exclusive facts verified by OCR: Plate 4.4 moisture threshold (PL-060), Plate 7.3 crack-width referral (PL-062), Table B.1 Norrvik fees (PL-061). Plus 4 non-exclusive image facts and 23 text-layer facts (ASM rule boxes, renames, terminology). |
| LD022 | pdf | 0.04 MB | 18 | 15 | NISA Circular 2026/04. Numbered R/G paragraphs, §3.1-3.5 verbatim from regulators.yaml (PL-063/064/065). FR1 schedule table, worked examples, annexes. |
| LD023 | pdf | 0.02 MB | 10 | 6 | NISA Circular 2024/07. §2.1 acknowledgement within 2 business days, §2.4 NISA-CT1 by 31 March, business-day examples. |

Total: 32.5 MB, well under the 95 MB budget. Every file is under 48 MB. LD021 asserts 25-40 MB and 130-150 pages at build time.

Facts by kind: needle 70, general 35, terminology 25, temporal 11, header 9, image_table 6, multipage_table 5, alias_use 3, image_text 3, chart_only 2, contradiction_old 2, definition 1, footnote 1, split_boundary 1. 22 facts are exclusive and 9 use OCR locators. All 20 placements for these files (PL-024..037, PL-060..065) are planted. LD023 has no placements.

## Verification (final state)

- `verify_corpus.py --family long_docs.regulatory --checks 1`: 170 PASS, 4 WARN, 0 FAIL.
- `--checks 3,6,7`: exclusivity 22/22 PASS, denylist PASS, secrets PASS.
- Manual index search (`build/index_long_docs.regulatory`, `--no-ocr`) for every exclusive needle found no leaks into other files. "NOK 4 000" appears in both LD009 and LD011 because each wording states its own excess, and both happen to be NOK 4,000. In LD003, "611.9" and "2,318.4" appear only on p.87, inside Table 4.2.
- OCR facts in LD021 are checked at build time through `harness.extract.resolve(..., ocr=True)` with `match(..., "ocr_fuzzy")`. The build fails if Apple Vision does not read a needle. The verifier reuses the same OCR cache, which is keyed by the file's sha1.
- The build asserts that the text layer of LD021 never contains the exclusive values: "% WME or more", "wider than 5 mm", "4,900", "2,150" and "5,200".

## Deviations and notes

- **The 4 WARNs are all in LD003.** They come from the verifier's kind-vs-locator heuristic:
  - Footnote (PL-026) and header (PL-027) are placement kinds that must be copied unchanged, but a PDF only offers `pdf_page` locators.
  - The two `chart_only` facts are reportlab vector charts, whose text sits in the PDF text layer.
- **The wordings reach 28-34 pages through real content, not font inflation.** The previous run left the Nordic wordings at 17-21 pages. `wording_extra.py` adds:
  - English wordings: a claims step-by-step guide that uses "notification of loss", endorsements, a fraud and sanctions section, and care guidance.
  - Nordic wordings: a coverage overview, premium terms, disclosure and fraud terms, a claims guide, a settlement table and a bilingual word list.
  - None of the added text contains amounts or periods. The Norwegian home overview leaves out frost, because frost cover (PL-037) is exclusive to the Dekning section. Base font is 10.5 pt. The builder can step the font size if a page count falls outside 25-45, but in the final run every wording was in range at 10.5 pt.
- **`.doc` locators come from the round-tripped document.** They are computed on the LibreOffice-converted copy (`harness.extract._as_docx`), not on the source DOCX. Page counts come from a LibreOffice PDF render of the `.doc`, cached in `build/cache/ld_regulatory/*.pages`.
- **LD021 sets `reportlab.rl_config.useA85 = 0` while it builds.** It is restored afterwards. Without this change, ASCII85 encoding inflated the PDF by about 25%. JPEGs are embedded as DCT passthrough, at quality 70 with 4:2:0 subsampling.
- **LD021 edition history lists the 2020 and 2022 editions by year only.** The rule sources cite the "Field Guide 2020 §7" and "2022 §4". The exact dates of those editions are not in the world, so none are given.
- **LD022 never states the 2026-01-14 SMS clarification.** That clarification post-dates the circular and is exclusive to VS014. The business-day examples in LD022 and LD023 were computed by hand: UK bank holidays, Norwegian 1 May and Ascension 2026, and Easter 2025.
- **The Danish "taksator" terminology fact uses world_ref GLOSSARY:G-001.** Taksator is not listed among that term's variants.
- **Unverified:** visual review of the `.doc` files in Microsoft Word, since only the LibreOffice rendering was checked. The 76 LD021 reference plates (2-up) carry small burned-in captions that are not facts and were not OCR-checked.

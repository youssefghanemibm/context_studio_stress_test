# long_docs.manual: generator notes

Part of the LD family. Script: `generators/long_docs/gen_manual.py`. Library: `generators/long_docs/manual_lib/`.

- `spec.py`: declarative spec writer (blocks, page-calibration segments, filler pools, facts).
- `content_v72.py` / `content_v61.py`: the two manuals' content. World facts come only from `load_world()`, quoted as of the anchor date.
- `prose.py`: seeded phrase banks. Procedural filler only: no thresholds, owners, dates or system links.
- `builder.py`: python-docx renderer. Writes the raw OOXML for footnotes, tracked changes, comments, the TOC field, headers and footers.
- `calibrate.py`: LibreOffice render plus pymupdf measuring, then iterative tuning of filler units per segment.
- `figures.py`: Pillow process diagrams.
- `scan.py`: the LD002 scan simulation.

Manifest: `manifests/long_docs.manual.facts.yaml` (381 facts). Cache: `build/cache/ld_manual/`.

Run: `.venv/bin/python -I generators/long_docs/gen_manual.py [--only LD001,LD002,LD012]`.

- From an empty cache: about 2.5 minutes (LD001 calibrates in about 9 LibreOffice renders, LD012 in about 9).
- With a warm cache: about 12 s.
- Cache logic: the calibration JSON stores the filler-unit counts per segment. Those counts are always tried first. They are accepted when every segment start lands on its target page, the TOC page numbers are stable, and the page total is within 3 of the target. Otherwise they seed a recalibration. A source-key change alone does not force a recalibration.

## Files

| id | file | size | pages | what it tests |
|---|---|---|---|---|
| LD001 | `LD001_claims_handling_manual_v7_2.docx` | 0.62 MB | 496 (LibreOffice) | Very long DOCX with real Word structure. Long-range definition and use, split boundaries, multi-page table without repeated header, headers, footers, footnotes, comments, tracked changes, image text and alt text. |
| LD002 | `LD002_claims_handling_manual_v7_2_scanned.pdf` | 37.7 MB | 496 | Image-only scan of LD001 (no text layer, asserted on every page). OCR-only facts, received stamp and handwritten margin note. |
| LD012 | `LD012_claims_handling_manual_v6_1.docx` | 0.23 MB | 300 (LibreOffice) | Superseded 2023 manual. Old values for the contradictions (Tier-3 review 30 days, FRAUDNET 70), 'case handler' terminology, owner shown under her pre-2025 name. |

## LD001 details

- **Pages and chapters.** It renders to 496 pages in LibreOffice, both as the clean variant and as delivered (tracked changes and comments visible), with 0 heading-page differences.
  - All 37 chapters, and the sub-sections with targets (53 segments), start exactly on their outline pages. Chapter 1's heading is on p.2 because p.1 is the title page.
  - Hard page breaks separate the calibration segments.
  - The TOC is a real TOC field whose cached result lists the measured page numbers.
- **Long-range pairs.**
  - Tier-3 is defined in §2.4 (p.15) and used in §19.4 (p.271), PL-001/PL-002.
  - LLNT is defined around p.18 and used in ch.22 at p.300.
- **Split boundaries.**
  - (a) PL-006: the reserve-authority sentence is broken by a page break inside the paragraph, at p.260/261.
  - (b) BR-STL-004: the offer-validity sentence is split across two paragraphs separated by the heading "31.3 Offer validity", at p.435.
  - Each half has its own fact. Each half's notes carry the combined statement.
- **Multi-page table.** PL-007, Table 7-1 (default reserves) runs from p.88 to about p.93. Its header row is not marked as repeating.
- **Comments.** PL-011: the 3.1% indexation rate exists only in the comment. The generator asserts it is not in the body.
- **Tracked changes.** PL-012/PL-013 are raw `w:ins`/`w:del` with author and date.
- **Footnotes.** A real `footnotes.xml` part, with its relationship and `w:footnoteReference` (6 footnote facts, including PL-008).
- **Header and footer.** PL-009 is in the header. PL-010 (CS-MAN-007 rev 7.2) appears only in the footer and is exclusive.
- **Figures.** 11 Pillow figures, each with labelled arrows, a caption and alt text (image_text and alt_text facts).
- **Page hints.** Every fact has a `page_hint`, found by searching the rendered PDF.

## LD002 details

- **Source.** LD001's clean render: tracked changes accepted, comments removed. So LD002 mirrors the body, headers, footers and footnotes, but not comments or tracked changes.
- **Rasterising.** Each page is rasterised in grayscale at 120 dpi and encoded as JPEG at quality 10.
- **Artefacts.** Each page gets:
  - skew of ±0.3–0.8°
  - Gaussian sensor noise
  - 120–320 speckles
  - an uneven illumination gradient
  - a jagged scanner-edge shadow on one side
  - slight blur
- **Overlays.** The PL-022 RECEIVED stamp is drawn on p.1 ("RECEIVED / Claims Standards Office / 03 JUL 2026"). The PL-023 handwriting-style note is on p.271, in the blank area below §19.4.
- **Facts.** 32 facts, all `pdf_page` with `ocr: true`. Mirror facts list `also_in` pointing to the LD001 fact, and the LD001 facts point back.

## LD012 details

- **Content.** 33 chapters in an older order, using 'case handler', 'claimant', 'FRAUDNET score', 'the SIU', 'the Recoveries team' and 'file notes'. All rules are quoted as of 2023-05-15.
- **Placements.**
  - PL-038: §19.4, Tier-3 review every 30 days (BR-RSV-007 v1).
  - PL-039: header with "Owner: Ingrid Sørensen, Claims Director".
  - PL-040: §28.3, FRAUDNET score 70 or more.
- **Other dated facts.** 24 `temporal` facts on 2023 values, for example Tier-3 at £40,000, BR-RSV-011 v1 and the 2023 owners.
- **Anachronism guard.** The generator fails if the LD012 text contains any 2024–2027 year, Sentinel, Claims Hub, "Counter-Fraud & SIU", "Recoveries & Subrogation", Ashby, CS-MAN-007 or similar tokens.

## Verification (final run)

- **Check 1.** `verify_corpus.py --family long_docs.manual --checks 1` (full OCR): 381 PASS, 0 WARN, 0 FAIL.
- **Determinism.** Two from-scratch runs (cache deleted) gave byte-identical LD001, LD002, LD012 and manifest. The `extract.py --all --no-ocr` hashes were also identical. A warm-cache run reproduced the same bytes.
- **Exclusivity spot-check** (`build/index_long_docs.manual`, no OCR). Each of these needles has hits only in LD001, at its locator:
  - "CS-MAN-007 rev 7.2" (footer only)
  - "3.1% per annum" (comment only)
  - "second Tuesday of each month at 10:00" (para)
  - the PL-008 footnote needle (footnote only)
  - "Claims Standards Office" has no text hits (it exists only in the LD002 image).
- **Checks 3, 6 and 7** (`--quick`, same index): exclusivity 8 PASS, denylist 2 PASS, secrets 1 PASS, 0 WARN, 0 FAIL.
- **Sizes.** All files are well under 48 MB. LD001 ≤ 20 MB, LD012 ≤ 12 MB, and LD002 is within the 25–45 MB target.

## Changes made in this session (resume)

- `scan.py`:
  - Pillow 13 returns read-only images from `fromarray`, so the scan crashed. It now copies the image first.
  - Noise and blur are now module constants.
  - LD002 was re-tuned from 150 dpi / q34, which was an estimated 105 MB, to 120 dpi / q10, which is 37.7 MB. OCR word recall at the new setting measured 96–99% on dense, table and footnote pages.
- `prose.py`:
  - Removed team names that had leaked into the 2023 manual: "Counter-Fraud & SIU" and "Recoveries & Subrogation" are now style keys.
  - Fixed "must always not" and "is expected to not" phrasing; negated forms now come from the chosen modal.
  - Blocked self-referential actor/action pairs.
  - Added more procedure and quality-check variants.
- `content_v61.py`: the anachronism token "Counter-Fraud" is narrowed to "Counter-Fraud & SIU". Ruth Okafor's world title "Compliance Manager – Conduct & Counter-Fraud" has been valid since 2019.
- `gen_manual.py`: the cached-calibration reuse described above.

## Deviations and unverified items

- **LD002 resolution.** 120 dpi / JPEG q10 is at the lower end of the spec's 110–150 dpi, and lower quality than a typical office scan. This was needed to fit 496 dense text pages into 25–45 MB. Body cap height is about 13 px at 120 dpi, and Apple Vision OCR still reads the pages (all OCR facts PASS). Downstream OCR engines weaker than Apple Vision may lose some small-font table or footnote text.
- **LD001 page count.** 496 pages is measured in LibreOffice. Word's pagination will differ somewhat, so page_hints are LibreOffice pages.
- **Filler repetition.** A handful of procedure-step sentences still recur across the 496 pages, which is normal for a manual. Every distinct long sentence is otherwise de-duplicated per document.
- **Not done:** PDF/A or OCR-layer variants of LD002 (none intended); Word-native rendering checks.

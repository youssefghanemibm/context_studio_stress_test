# long_docs.docs: generator notes

Generator: `generators/long_docs/gen_docs.py`, with builders in `generators/long_docs/docs_lib/`. Manifest: `manifests/long_docs.docs.facts.yaml`, 177 facts.
Run it with `.venv/bin/python -I generators/long_docs/gen_docs.py`. One run regenerates all 15 files in about 10 s with 5 workers. LibreOffice uses per-file profiles, and the cache is `build/cache/ld_docs/`.

## Files

| id | ext | method | pages (target) | what it tests |
|---|---|---|---|---|
| LD013 | docx | python-docx | 82 (≈90) | Pre-rename architecture: "reserve-svc" throughout (PL-043), the exclusive topic retention in §5.4 (PL-042), the CLX-IF-043 03:00 schedule (PL-041, C12), and raster figures with labelled arrows |
| LD014 | docx | python-docx | 63 (≈70) | IBM namesake author (PL-047). 6-page mapping table: the RSV row is on table page 4 and REF_SCORE on table page 5 (PL-044/045). Exclusive reconciliation tolerance (PL-046). A sentence split across a page break (PL-048) |
| LD015 | docx | python-docx | 35 (≈40) | DRAFT watermark and header, draft notice value (PL-049, C03), and the option of 60 in the appendix (PL-050) |
| LD016 | docx | python-docx | 38 (≈45) | Approved BRD with an approval table, notice value of 10 days (PL-051), and the exclusive FR-REQ-014 (PL-052) |
| LD017 | docx | python-docx | 109 (≈120) | 2021 spec: Tier-3 at £40k (PL-053, C10), exclusive CICS regions (PL-054) and DB2 plan (PL-055). The CLX-IF-042 schedule is never stated |
| LD018 | docx | python-docx | 46 (≈50) | Post re-org RACI. The RACI table spans exactly 4 pages, and the write-off row is on table page 3 (PL-056; post_check enforces this). SIU reports to the CRO (PL-057). Org chart image plus alt text |
| LD019 | docx | python-docx | 36 (≈40) | Exclusive parallel-run tolerance of 0.5% per product per day in §4.3 (PL-058). Names as of Jan 2026 (reserve-svc) |
| LD020 | docx | python-docx | 31 (≈35) | Exclusive AUC 0.87 and the top 2.9% referral share in §3 (PL-059). Threshold history 75→70→65. PSI is never stated |
| LD024 | pdf | reportlab | 26 (≈30) | Finding IA-25-07 on page 12 (PL-066; post_check enforces this). All 8 reserve writers named, and CLRRS150 writes movements only |
| LD025 | pdf | docx→soffice | 100 (≈110) | 2024 runbook. FRAUDNET at fraudnet.corvane.internal in the online chapter §3.1 (PL-067, C06). The exclusive CLRNRSV1 restart appears only in the batch restart table §7.2 (PL-068) |
| LD026 | pdf | reportlab | 23 (≈25) | Exclusive treaty terms (retention £5m, limit £150m, Brynholt 40%, Calderbank 35%), only in the page-3 summary table (PL-069; post_check enforces this) |
| LD027 | pdf | docx→soffice | 32 (≈40) | Exclusive PSI 0.06, only in the executive summary on page 3 (PL-070). AUC is never stated |
| LD028 | pdf | docx→soffice | 47 (≈60) | 2024 business case, signed "Gareth Whitcombe, Chief Financial Officer" on the signature page (PL-071; anchored to page 33). No IBM, Sentinel or Ashby (post_check enforces this) |
| LD029 | pdf | reportlab | 60 (≈80) | "the CFO (Priya Raman)" appears in the agenda (page 2) and on the item 4 cover (page 21) (PL-072) |
| LD030 | pdf | reportlab | 17 (≈20) | Brackenfield SLA Schedule 1 (PL-073) |

The total size is about 6.5 MB. The largest file is LD025 at 2.7 MB.

## Verification
- `verify_corpus.py --family long_docs.docs --checks 1`: 177 PASS, 0 WARN, 0 FAIL. The 7 OCR facts in LD013, LD018, LD020 and LD027 were also re-resolved with Apple Vision OCR (`resolve(..., ocr=True)`), and all matched.
- `--checks 6` (denylist): PASS.
- Determinism: two full regenerations from an empty cache gave identical `extract.py --all` output for all 15 files, and an identical manifest. The DOCX files and the reportlab PDFs are byte-identical. The soffice PDFs (LD025/027/028) differ only at byte level, from LibreOffice internals.
- Exclusivity: I searched index `build/index_long_docs.docs` for 0.5% per product per day, AUC of 0.87, the PSI 0.06 sentence, Brynholt/Calderbank/£150m and the CLRNRSV1 restart text. Each was found only in its own file. A scratch scan of my 15 files against distinctive values from every other file's exclusive placements found no leaks. The only hit is the bare ID "FR-REQ-014" in the LD015 draft, which carries a generic text and not the LD016 fact.
- I also scanned for as-of anachronisms (renames, Ashby/Sørensen, the CFO change, Claims Hub before 2024-11). The remaining hits are deliberate historical references ("renamed …", "formerly …").

## Changes to the earlier agent's work (LD013–LD017, LD030)
- `Prose` now takes `date=` and rewrites system and service names to the ones in use on that date. Before this, LD013 (Mar 2025) had 11 "reserve-engine" mentions in filler and LD014 had 1. Both now say reserve-svc.
- `Prose` now takes `forbid=`. LD017 (2021) filler no longer mentions Claims Hub, migration or Kafka. LD017 rule titles are as-of (FRAUDNET pre-screen).
- LD013 column descriptions are as-of ("DOCSTOR object", not Evidence Vault).
- python-docx stamped Word comments with the wall clock. `docx_r` now rewrites `w:date` to the document date, which affects the LD015 comment.
- `clean_old` strips "(queue CLR.RSVMOVE.OUT)" from copybook descriptions in LD017 and LD025. The queue name belongs with the VS033 CLX-IF-042 label.
- Line spacing is larger for LD015/LD016 (`Style.line_spacing`) and for LD030 (`Style.pdf_leading`). The defaults are unchanged, so the other files are not affected.
- New phrase banks are in `docs_lib/prose_more.py` under new bank names, so the existing banks and the draws of the earlier files are unchanged.

## Deviations
- **Page counts:** several files are short of their targets. LD029 has 60 of ≈80 pages, LD028 47 of ≈60 and LD027 32 of ≈40. The rest are within about 10–15%. The world model has no detailed financials, layer structures, minutes or risk ratings, so padding to the full length would have meant inventing world facts. I used world-derived tables plus generic prose instead.
- **LD029:** omits the INC-2026-0702 impact (412 claims; VS034 owns the recovery metric) and the INC-2026-0311 root cause (12 partitions; ST030). The CICSPRD1 region name is removed from the INC-2025-0201 title (LD017 owns it). The Wave 2 date is given only as "early 2027 (date to be confirmed)", because DEC-011, which fixed 2027-02-15, came after the pack date. Programme spend is stated to Q2 2026 only.
- **LD019:** does not state the Wave 2 date or the migration reconciliation tolerances. LD014 owns the tolerances.
- **LD024/LD026:** the BR-RSV-012 v1 text loses its "reserve-engine revaluation runs from Wave 2" clause before 2026-03-09 (ADR-028).
- **LD024 findings:** IA-25-05, 06 and 08–10 are document-local. They are built only from world-consistent observations (the stale data dictionary, CLRRS150, CHUB-144, BR-RSV-007/011). Their targets are relative ("within three months"), so no new dates are invented.
- **LD027 findings:** VF-01 to VF-05 are document-local and qualitative. VF-03 recommends testing the batch threshold paths before 2026-04-01. It does not claim the CLRFR040 hard-coding was found, because that surfaced later (INC-2026-0518).

## Unverified
- The rendered page numbers come from LibreOffice. Word may paginate the DOCX files slightly differently. That matters for the LD018 "page 3 of the RACI" and the LD014 table-page hints, which were checked in the LibreOffice rendering only.

## Fix pass (contradiction-hunter findings, 2026-11-16)
Generator-side as-of fixes; fact ids unchanged (177 facts, same order). Shared helpers are in `docs_lib/hub.py` and `docs_lib/core.asof`.
- **Write-off approval (N3/N12/N29):** `hub.svc_apis` quotes the BR-REC-011 version in force. LD013 (2025-03-03) now says "approval above £5,000 by the Recoveries Manager" (v1) in §5.3.9, the API table and Appendix D.
- **PS-RSV-03 cadence (N13/N14/N15/m34):** new `hub.step_desc`. Before the BR-RSV-007 v3 approval (2026-06-09) the step reads "Review reserves; Tier-3 every N days." with the version in force (21 days in LD013, LD018 and LD024). process.yaml is unchanged, so ST040 (2026-07-13) still says 14 days.
- **Tier-3 in LD017 (N11, C10):** world change in `world/wb/rules.py`: BR-TRI-003 v2 `approved_on` 2021-11-16 → 2021-09-14 (effective dates unchanged). LD017 §3.2 now states v2 (£40,000) "from 1 January 2022 (BR-TRI-003 v2, approved 14 September 2021)" and v1 (£25,000) in force until then. The PL-053 placement text says the same, and C10 (stale £40,000 vs £50,000) is kept.
- **CLR.T_FRAUD_REFERRAL columns (N22):** LD014 (Appendix A and the B mapping), LD015/LD016 (current referral table) and LD017 §5.14 now list all 19 tables.yaml columns. The FRDREF01 layout in LD017 already matched copybooks.yaml. `hub.col_desc` drops rule references that post-date the document ("(e.g. BR-FRD-031)", the BR-FRD-032/036 notice parentheticals) and the "(e.g. SNT-4.2)" example before 2026-03-16 (m16, m24).
  - **Known world-design limitation:** tables.yaml and copybooks.yaml have no column history. The customer-notice and deferral columns (Circular 2026/04, BR-FRD-032/036) therefore appear in documents from 2021 onwards (m25). ST001/ST007 (structured family) still show a 16-column set.
- **LD014 mapping table:** the 3 extra rows push the last 4 rows onto a 7th page (pp.55–61). The RSV row is still on table page 4 (p.58) and REF_SCORE on table page 5 (p.59).
- **Current-state sentence (N21):** LD015/LD016 §3 no longer say that CLRFR040 reads CLR.T_PARAM. Only CLRFR030 reads it, and nothing is said about how the sweep gets its threshold (C05 drift unknown until INC-2026-0518). LD017 §3.4 is worded the same way.
- **Runbook (N19/N20):** `hub.job_status` makes CLRNFR99 "active" before 2026-04-01, and `hub.copybooks_asof` drops FRDNOT01 before 2026-03-27 (LD025).
- **Program ids (m27/m28/m29):** `hub.apply_program_renames` rewrites CLRFR020/CLRFR030 to FNETCAL1/FNETREF1 in documents dated before 2025-03-01 (LD017, LD025, LD028), using programs.yaml `renamed_from`.
- **LD028 replaced counts (m29):** "CLARA programs replaced" counts only programs with `replaced_by` and lists the others as "retired with CLARA".
- **Other `core.asof` and `hub` rules:**
  - Before 2025-11-20, "TP2, FR1, CT1" becomes "TP2, CT1" and "(NISA-FR1 support)" is dropped (m11/m12/m23). LD013 omits CLX-IF-033 (NISA-FR1) from its catalogue (m21).
  - Before 2026-03-09, the "; reserve-engine revaluation runs from Wave 2" clause is dropped (m13/m31).
  - `hub.program_desc` drops interface ids that were not yet live, e.g. CLRST030 "(CLX-IF-019)" in LD017 (m14).
  - `hub.org_asof` gives team names before the re-org in LD013's locations and glossary (m1/m26).
  - LD019 lists only the ADRs that existed on its date (`hub.adr_ranges`, m36).
  - LD014 cites ADR-015 at v0.9, dated 2025-06-09, rather than v0.3 (m37).
- **Not fixed (out of scope, not reported):** LD013 still lists post-Circular steps PS-FRD-03/05 in §2.4 and Appendix C.
- **LD029** changed in this run only because of other agents' world edits (incident `fix_tickets`, a CHUB-279 summary). No fact changed.
- **Checks:** two full runs gave identical extracted text and manifest. `verify_corpus --family long_docs.docs --checks 1,3,6,7`: 177 PASS, 0 FAIL (1 WARN, the existing LD026 '£150m'). `--checks 2`: 253 PASS. `score.py keycheck`: 0 problems.

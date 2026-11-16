# text.messages – generator notes

Part of the TX family. Script: `generators/text/gen_messages.py` (library in `generators/text/messages_lib/`:
`core.py` world/as-of helpers + fact recording, `mail.py` thread renderer, `emails.py`, `minutes.py`,
`filler.py`, `html_docs.py`, `phrases.py`). Manifest: `manifests/text.messages.facts.yaml` (245 facts).

Run: `.venv/bin/python -I generators/text/gen_messages.py [--only TX007,...]` (about 1 s). It writes only
TX007–TX020, TX031–TX060 and TX073–TX075 into `corpus/upload/text/`. It never resets the folder. Before
writing the manifest, every fact is resolved through `harness/extract.py`. Exclusive needles are checked to
occur only inside their locator, and not in any other file of this part. A forbidden-pattern scan blocks
other files' exclusive values (41%, 186,400 outside TX011, 1,140 outside TX010, 02:15, AUC, cadence of
COM-01, CODEOWNERS mapping, topic names, etc.).

## Files and what they test

| ID | Type | Tests |
|---|---|---|
| TX007 | email (Outlook, newest first) | 'the CFO' sign-off = Gareth Whitcombe in 2024 (PL-205); £48.6m business case; Ingrid *Sørensen* + old address |
| TX008 | email (archive export) | Fellgate leaves panel 2026-01-31, instructions to Brackenfield (PL-206, C14 new) |
| TX009 | email (mbox, quoted replies) | £750 subrogation threshold in June 2025 (PL-207, C13 old); Siobhan Quill as *Acting* Recoveries Manager |
| TX010 | email (archive) | Corvane Callum Fairbairn, 1,140 open motor claims (PL-208, exclusive); the namesake trap |
| TX011 | email (Outlook) | IBM Callum Fairbairn, 186,400 claims / 3 exceptions (PL-209, exclusive) |
| TX012 | email (mbox) | first FR1 submitted 2026-07-29, one day early (PL-210); 1,488 referrals |
| TX013 | email (Outlook + forward) | £1.8m drawdown approved, signed only 'PR' (PL-211) |
| TX014 | single email | Sørensen → Ashby, new address from 2025-08-23 (PL-212) |
| TX015 | email (archive) | 37 claims scored 65–69 missed by the CLRFR040 sweep (PL-213) |
| TX016 | email (mbox) | Tier-3 review every 14 days from 2026-07-01 (PL-214); 21 days before |
| TX017 | email (Outlook) | Wave 2 freeze 2027-02-12 18:00 → 2027-02-15 06:00 (PL-215) |
| TX018 | single email | DOCSTOR → Evidence Vault on 2025-11-03, in the subject and the body (PL-216, 2 entries) |
| TX019 | email (archive) | ReCede notified within 24 h of a £310,000 movement on CLM-UK-2026-207731 (PL-217, exclusive); LLNT used |
| TX020 | email (Outlook) | ASCII 'Bjorn Aasheim' in the From header and signature (PL-218); 1,530 Q3 referrals |
| TX031 | md minutes (MTG-007) | DEC-014 Tier-3 threshold 60 in the Decisions section (PL-219, C01 new); DEC-015; DEC-016 *without* the 41% estimate |
| TX032 | md minutes (MTG-006) | item 3 approves BR-RSV-007 v3 (PL-220); no committee cadence stated |
| TX033 | md minutes (MTG-009) | R2026.11 change list: CHUB-298/415/421 (PL-221); Tariq Hussain's new squad |
| TX034 | md minutes (MTG-011) | Wave 1 GO for 2026-09-14 and the freeze (PL-222) |
| TX035 | md minutes (MTG-012) | DEC-007 rule set from 2026-04-01 (PL-223); BR-FRD-036 v1 shown by title only (its text is exclusive to LD001) |
| TX036 | md minutes (MTG-013) | reserve-svc → reserve-engine from 2026-02-10 (PL-224); ADR-019 consequences |
| TX037 | md minutes (MTG-014) | CDC (ADR-005) replaced by the CLX-IF-049 bridge (PL-225); the service is still called *reserve-svc* on that date |
| TX038 | md decision log | 19 decisions with deciders' names and titles as of each decision date (Sørensen in DEC-020, Ashby later) |
| TX040 | md retrospective | 18 duplicate payments, £41,236.50 (PL-228) |
| TX043 | md call notes (MTG-010) | an SMS counts as written notice if a letter follows within 2 business days (PL-226, also_in VS014) |
| TX044 | md post-mortem | workaround: a daily Compliance query for scores 65–69 (PL-227); 60–64 deliberately absent (that came on 2026-10-01) |
| TX073 | html letter | NISA (Imogen Thackray): FR1 is due 30 days after quarter end; 2026Q2 is due 2026-07-30 (PL-233) |
| TX074 | html newsletter | 'Ingrid Ashby (née Sørensen)', re-org of 2025-09-01 (PL-234); the old→new titles table; Assessor Portal rename; the new CFO |
| TX075 | html notes | the calibration table: 65 → 2.9%, 70 → 2.3% (PL-235) |
| TX039, TX046, TX053, TX057, TX059 | md filler | weekly and monthly status reports |
| TX041, TX047–TX052, TX054, TX055, TX058, TX060 | md filler | team notes, sprint notes, shift handover |
| TX042 | md filler | glossary page, built from glossary.yaml |
| TX045, TX056 | md filler | onboarding notes (IBM team, Feb 2025; UK motor handlers, Sep 2026) |

Filler restates world facts only when they were true on the document's date. Each one is recorded as a
`general` or `temporal` fact and checked with `W.may_state`. Workstream RAG colours, generic progress lines,
and action owners and due dates in minutes are colour; they are not recorded as facts. Key-date tables use a
`known_from` date per milestone, so a report never shows a date before it was known. For example, Wave 2
shows "to be confirmed" before 2026-10-08.

## Deviations / judgement calls

- **TX011** states 186,400. That value equals `WAVE:MW-1#claims_migrated`, which is exclusive to VS011.
  `W.may_state("TX011", …)` is True (TX011 is in also_in), so it was kept.
- **TX075** states "70 → 2.3% of scored claims", because the placement PL-235 requires it. That value
  overlaps `TIMELINE:metrics#fraud_referral_rate_pct_of_scored`, which is exclusive to VS013, so it has no
  fact of its own with that world_ref. It is noted on the PL-235 entry.
- **TX038** leaves out DEC-013: the whole entity is exclusive to VS014, with TX043 as also_in. It is
  mentioned by ID only, as held in the Compliance log. DEC-012 (2026-11-11) post-dates the log (2026-11-10)
  and is also left out.
- **TX033** describes CHUB-415 as "CODEOWNERS update" without the owner mapping, which is exclusive to
  CODE:c. CHUB-421 uses its ticket summary, which doesn't name the topic. CHUB-298 is paraphrased without
  the hard-coded constant.
- **TX015/TX044**: the root cause comes from `INCIDENT:INC-2026-0518#root_cause` (may_state True), not from
  `PROGRAM:CLRFR040#hardcoded_constants` (exclusive to CODE:c).
- **"First email"** means the chronologically first message. In Outlook-style threads it sits at the bottom
  of the file; the locators point at it.
- **Page targets:** the md files are on the lean side of their "≈N pages" targets, at roughly 3 KB of
  markdown per page. For example, TX031 is 10.8 KB and TX038 is 14 KB. The total for this part is 264 KB
  (budget 6 MB).

## Verification

- `verify_corpus.py --family text.messages --checks 1`: 245 PASS, 0 WARN, 0 FAIL.
- With my own index (`build/index_text.messages`): checks 3 and 7 PASS.
- Index searches for the exclusive needles (1,140; 186,400; 3 exceptions; CLM-UK-2026-207731; 310,000)
  each hit only their own file. 41%, 02:15, "second Tuesday" and 0.87 have no hits in the corpus as
  indexed.
- Check 6 (denylist) FAILs corpus-wide on 'Corvane', 'Programme Skerry', 'Brackenfield Loss Adjusting',
  'product' and 'regulator'. The denylist loader appears to also read the `invented_name_checks` section,
  so this is not specific to this part. A direct grep of my 47 files for `entries[].name` and
  `local/forbidden_terms.txt` finds 0 hits.
- Determinism: the `extract.py --all` output hash and the manifest hash are identical across two runs. The
  files are byte-identical too.

## Not verified

- TX031 is aligned to timeline/decisions data, not to TX002's actual transcript wording, which another
  agent writes.
- The HTML pages (TX073–TX075) were checked as extracted text only, not rendered visually.

## Fix pass (2026-11-16, contradiction-hunter findings)

- **TX039 drawdown date (m39).** "approved by the CFO at the Steering Committee on 8 October, and she confirmed it in writing the next morning". The date comes from DEC-010, and the written confirmation is TX013's email of 9 Oct 07:53. The needle is unchanged. The TX039-F002 statement now carries the date.
- **TX040 Wave 2 (m43).** The retro is dated 2026-09-25, before DEC-011 (2026-10-08). It now says "Wave 2 is planned for early 2027, with the date to be confirmed by the Steering Committee". This is as-of logic, and documents dated on or after DEC-011 still get 15 February 2027. TX040-F005 has a new needle and statement, kind temporal and world_ref DECISION:DEC-011 (same id).
- `filler.MILESTONES`: the Wave 2 row now takes its date from MW-2 and its known-from date from DEC-011, instead of literals. The output is unchanged.
- Verification: `--checks 1,3,6,7`: 245 PASS, 0 FAIL. Two runs gave byte-identical output.

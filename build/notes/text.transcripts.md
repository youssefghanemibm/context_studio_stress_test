# text.transcripts – generator notes

Part of the TX family. Script: `generators/text/gen_transcripts.py`. Library: `generators/text/transcripts_lib/`.
- `common.py`: world access, fact registry, line-addressed `TextDoc`, safety scans.
- `dialogue.py`: the transcript engine. It puts scripted fact-bearing turns at fixed timestamps and generates topic filler between them.
- `phrases.py`: phrase banks.
- `meeting_tx001/2/3.py` and `meeting_short.py`: the transcripts.
- `fillers_standups.py` and `fillers_docs.py`: the 19 filler files.
- `jira.py`, `chat.py` and `emails.py`: the JSON files.

Manifest: `manifests/text.transcripts.facts.yaml` (290 facts).

Run: `.venv/bin/python -I generators/text/gen_transcripts.py [--only TX001,...]` (about 22 s).
- It deletes and rewrites only TX001–TX006, TX021–TX030 and TX061–TX072 in `corpus/upload/text/`. It never resets the shared folder.
- Every fact's needle is checked against its locator text at generation time.
- Every output is scanned for denylisted names, forbidden terms, and the exclusive values of other files (`common.BANNED_VALUES`/`BANNED_REGEX`) before it is written.
- Transcript lengths are calibrated by adjusting the speech rate until the spoken-word count is in range.

## Files and what they test

| ID | Type | Size | Tests |
|---|---|---|---|
| TX001 | txt transcript, MTG-008 (2026-10-08, 120 min) | 769 lines, 20.5k words (wc), 18.0k spoken | C15 in-transcript correction: Wave 2 misstated as 18 Jan 2027 at 00:41:07 (PL-189), corrected to 15 Feb 2027 at 00:44:02 (PL-190). "PR, as the CFO" approves £1.8m at 01:19 (PL-191). The Claims Director is labelled by role only (PL-192). Also: Wave 1 defects, INC-2026-0914/1007 impact, CLARA and SUBTRAK targets, T30 lead. |
| TX002 | txt transcript, MTG-007 Fraud Rules Workshop (2026-09-17) | 739 lines, 20.4k / 18.0k | FRAUDNET alias at 00:12 (PL-196). Exclusive 41% estimate at 00:55 (PL-195). DEC-014 Tier-3 threshold 60 from 2026-10-01 at 01:35 (PL-193, C01 new; also_in TX031). DEC-015 deferral approval at 01:48 (PL-194). Also: BR-TRI-003 v3 £50k, BR-FRD-035 3 days, INC-2026-0518. |
| TX003 | txt transcript, MTG-005 (2026-03-05) | 778 lines, 20.5k / 18.0k | C07: "only the CLRRS programs write the reserve table" at 00:38 (PL-197), corrected at 00:46 (PL-198) to 8 writers. CLRRS150 writes movements only. The data dictionary lists 7. DEC-005 RV movements at 01:40 (PL-199). DEC-006 14 days. |
| TX004 | txt transcript, MTG-003 incident bridge (75 min) | 503 lines, 0:00–1:11 | CLX-IF-042 dependents at 00:09 (PL-200). DEC-003 move CLX-IF-043 to 03:45 at 01:05 (PL-201). "the CFO" = Gareth Whitcombe in April 2025. |
| TX005 | txt transcript, MTG-004 subrogation handover (60 min) | 386 lines, 0:00–0:56 | Freya owns subrogation from 2025-09-01 at 00:05 (PL-202). SUBTRAK target 2026-12-31 at 00:40 (PL-203). BR-REC-003 £1,000 / BR-REC-011 £10,000. "sub-ro". |
| TX006 | txt transcript, MTG-002 Sentinel rename call (50 min) | 316 lines, 0:00–0:49 | 1,214 unscored claims at 00:20 (PL-204). INC-2025-0233 root cause. DEC-002 DNS alias to 31 March. CHUB-119/117. |
| TX021–TX030, TX061–TX069 | 19 filler txt | 0.002–0.014 MB each | IVR and agent scripts (TX021, 022, 029, 063 bilingual NO/EN, 067), call notes (TX023, 027, 062, 066), ops and contact-centre handovers (TX024, 030, 064, 068), stand-up transcripts (TX025, 026, 061, 065, 069) and a printed reserve-engine log excerpt (TX028). They carry no new world facts. They restate 0–3 non-exclusive facts each, consistent with their date (27 facts in all), and are otherwise noise and near-duplicates for retrieval. |
| TX070 | JSON, Jira REST-style export dated 2026-11-11 | 9.50 MB, exactly 2,000 issues CHUB-101..CHUB-2100 | All 85 key tickets verbatim (summary, status as of the export, assignee, links; checked programmatically). CHUB-298 "In Review" (PL-229). CHUB-143 03:00→03:45 (PL-230, C12 new). CHUB-233 rename (PL-231). 1,915 filler stories, bugs, tasks, sub-tasks and epics with components, fix versions, changelog, comments[] and issuelinks. Facts: the summary of every key ticket, plus its status as at the export. |
| TX071 | JSON chat export, #skerry-programme, 2026-04-01..2026-11-10 | 0.69 MB, 3,017 messages | Display-name aliases ("Arjun K (IBM)", "Bjorn", "Linnea Sjoberg"...). In October: 'sub-ro' and 'the ledger' (PL-232, 2 entries). "PR approved the £1.8m". INC-2026-0518/0914/1007 impacts. FR1 submissions. DEC-009 freeze. CHUB-298 moving to In Review on 2026-11-04. |
| TX072 | JSON email thread, 8 messages, 2026-09-14..16 | 0.013 MB | INC-2026-0914: root cause, 18 claims / £41,236.50, end 15:45, CHUB-371 deployed and ADR-021 accepted on 2026-09-16. "the CFO" = Priya Raman. |

Total: 28 files, 10.86 MB (budget ≤ 15 MB). The largest file is 9.5 MB, well under 48 MB.

## Facts

290 facts by kind: general 237, needle 30, alias_use 6, temporal 6, contradiction_new 4, contradiction_old 2,
terminology 3, scale 2.
- 1 is exclusive: PL-195, the 41% estimate.
- All 20 placements for these files are planted at their location_hint, 21 entries in all (PL-232 has two).
- Locators are `text_lines` with exact line numbers for the .txt files, and `json_pointer` for TX070–TX072.

## Verification (2026-11-16)

- `verify_corpus.py --family text.transcripts --checks 1`: 290 PASS, 0 WARN, 0 FAIL.
- Check 3 (exclusivity, index `build/index_text.transcripts`, built with `--no-ocr`): 1 PASS. "referrals would go up by about 41%" is found only in TX002.
- Leak scan: none of the 58 exclusive needles in the other manifests occur in these 28 files.
- Checks 6 (denylist) and 7 (secrets): PASS.
- Determinism:
  - I hashed `harness/extract.py --all --no-ocr` per file over two runs. The second run started from an empty state, with all 28 files and the manifest deleted first. The extracted text was identical in both.
  - Generation uses `util.rng` only and no wall clock.

## Changes in the resumed session

- TX071 chat timestamps: the fraction digits produced "0.87", which the banned-value scan rejected and which crashed the previous run. The fraction now uses the `.000nnn` form.
- The chat volume is tuned to about 3,000 messages (3,017).
- TX006 now runs to 00:49 to match its 50-minute meeting; it ended at 00:46 before.
- TX005 now opens with introductions, so the ownership statement (PL-202) lands at 00:05 as hinted, not 00:00:10.
- TX001: the correction turn now reads naturally after the 2.5-minute gap.
- Dialogue engine:
  - It drops a sentence repeated verbatim within one turn.
  - It fixes subject-verb agreement for plural topic subjects (for example, "the DNS records are").
- The manifest was written for the first time (it was missing). TX070 gained a summary and status fact for every key ticket.

## Deviations and unverified items

- **Word counts.** TX001–TX003 count 20.4–20.5k with `wc -w`, which includes timestamps and speaker labels. The spoken words alone are about 18.0k. Both are within 17–21k.
- **CHUB-415.** Its key-ticket summary names `@corvane/hub-squad-recoveries-docs`, and it is included verbatim as required. `may_state` allows it. The ticket is still Open at the export date, so TX070 does not state the post-commit ownership (PL-275, CODE:c). If the CODE manifest makes that string an exclusive needle, check 3 will flag TX070. That would be a world-design overlap, not a leak.
- **PL-193 also_in.** It lists the TX031 file path. The matching fact in text.messages is currently TX031-F013 (PL-219), but the path is used so the entry stays valid if that manifest is renumbered.
- **Filler prose.** It is phrase-bank generated. It reads plausibly but is somewhat generic, and it has not been reviewed line by line by a human. The banks avoid thresholds, owners, dates and system links.
- **OCR.** Not applicable: these files have no image content.
- **Partial corpus.** The exclusivity checks ran against the corpus as it stood. Other agents' files may still be partial.

## Fix pass (2026-11-16, contradiction-hunter findings)

- **TX028 page header (N7).** The namespace now comes from services.yaml as of the document date (`fillers_docs._k8s_namespace`): "reserve-engine application log (namespace chub-reserve)". Before, it was a hard-coded "claims-hub-prd".
- **Stand-up squad service lists (m18).** `fillers_standups._squad` builds the list from `W.service_owner` on the stand-up date. TX026 (2026-10-06) now includes recovery-svc for Fraud & Settlement, and TX061 (2026-10-05) includes document-svc for Intake & Triage; both moved to T30 only on 2026-11-01. TX025 is unchanged.
- **TX003 [00:46:51] (m33).** "All 122 programs" is now computed as the number of programs that existed when CHUB-104 was resolved (2025-04-11): 118. The 122-program reissue named in the key-ticket description is dated 2026-08-20, after the meeting. The world-internal "122" in the CHUB-104 description is unchanged.
- TX070/jira.py was not touched (owned by the sheets pass). The generator was run with `--only` for every id except TX070. Manifest: no fact changes.
- Verification: `--checks 1,3,6,7`: 290 PASS, 0 FAIL. Two runs gave identical extracted text.

## Fix pass (contradiction-hunter findings, 2026-11-16)

- **TX070 filler tickets (N1/N6/m15).** The core of every filler ticket now comes from the shared module
  `generators/common/jira_filler.py`, which ST024 also uses (the two files are snapshots of the same project on
  the same date). The core covers type, summary, status, assignee, reporter, created and resolved dates,
  component, fix version, labels, parent and status transitions. jira.py only adds the rich fields with rng
  `TX070:tickets`: description, priority, story points, epic link, assignment change, comments, links,
  changelog times and sprint. Changelog transitions on the same day are now in time order, and assignment and
  comment times never precede creation. m15 is fixed: no Sentinel, reserve-engine, Assessor Portal or CLRFR0x0
  name appears in a ticket created before the rename; CHUB-116 is now a Platform ticket. The status mix of the
  2,000 tickets is now Done 1,708, In Progress 100, To Do 90, Won't Do 65, In Review 36 and Open 1 (CHUB-415).
- **m17.** CHUB-279 now reads 'reserve-svc: null pointer on missing optional field' (world/wb/history.py). Fact
  TX070-F136 keeps its id; its needle and statement were updated.
- Regenerated with `gen_transcripts.py --only TX070` (the manifest is rebuilt in full; only TX070-F136 changed).
  verify_corpus --family text.transcripts --checks 1,3,6,7: 290 PASS, 0 FAIL. Two runs gave identical bytes.

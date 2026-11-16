# World model guide (for generator agents and question writers)

`world/data/*.yaml` is the single source of truth for the Corvane corpus. Do not edit the YAML by hand. Change `world/wb/*.py`, then run:

```
.venv/bin/python -I world/build_world.py && .venv/bin/python -I world/validate_world.py
```

The build is seeded (`generators.common.util.rng`), so two runs give byte-identical YAML. The validator must print `PASS`.

```python
import sys, pathlib; ROOT = pathlib.Path(__file__).resolve().parents[2]; sys.path.insert(0, str(ROOT))
from world.worldlib import load_world
W = load_world()
```

## 1. The world in one paragraph

Corvane Mutual Insurance Society Limited is a fictional mutual P&C insurer. It has 4,050 staff, a London HQ, a Leeds claims centre, Bristol recoveries, a Glasgow contact centre, and Nordic branches in Oslo, Stockholm and Copenhagen. Its regulator is NISA (`REG-NISA`), firm reference NISA-FRN 40417.

Its legacy claims platform is **CLARA** (`SYS01`: COBOL/CICS/DB2, live since 1994-10-03, decommission target 2027-09-30). **Programme Skerry** is replacing CLARA with **Claims Hub** (`SYS02`: 13 Spring services on OpenShift).

Key programme dates (all in `timeline.yaml`):

| Event | Date |
|---|---|
| Business case signed by CFO Gareth Whitcombe (£48.6m) | 2024-11-18 |
| IBM engagement starts | 2025-01-13 |
| MVP live | 2025-11-03 |
| Wave 0 (Denmark) | 2026-06-01 |
| Reserve parallel run | 2026-03-02 to 2026-08-28 |
| Wave 1 (UK motor) | 2026-09-14 |
| Wave 2 (planned) | 2027-02-15 |

Today is **2026-11-15**. Every corpus document is dated **2026-11-12 or earlier**. The model is fully specified from 2021-01-04 (`MODEL_START`); reporting lines before that date are not modelled.

## 2. Entity sets and ID formats

| File | Key | ID format / example | Notes |
|---|---|---|---|
| org.yaml | company, locations, departments, teams, committees | `LOC-LON`, `DEP-CLM`, `T08`, `COM-01` | Teams have `lead_history`, `name_history` and `department_history`. Financials sit under `company.financials`. |
| people.yaml | people | `P001`…`P060` | 46 Corvane, 8 IBM, 6 external (NISA and vendors). Each person has `titles`, `reports_to`, `teams` (dated), `aliases`, `role_aliases` (dated) and `name_history`. |
| systems.yaml | systems | `SYS01`…`SYS27` | Renames are in `renames[]`. |
| programs.yaml | programs, reserve_writers | `CLRFN030` (CLR + area + 3 digits) | 122 programs. `since` is the date the program first existed. Respect it. |
| copybooks.yaml | copybooks | `RSVREC`, `RSVMOVE` | `RSVMOVE` has a `field_history`. |
| jcl_jobs.yaml | jcl_jobs | `CLRNRSV3` | Steps, schedule, restart instructions. |
| bms_maps.yaml | bms_maps | `CLRM310` | Map, mapset, program and transaction. |
| tables.yaml | tables | `CLR.T_RESERVE`, `reserve.reserve` | DB2 tables (with derived `writers`/`readers`) and PostgreSQL tables. `CLR.T_PARAM` has `param_rows`. |
| interfaces.yaml | interfaces, impact_042 | `CLX-IF-001`…`CLX-IF-060` | `depends_on` lists upstream interfaces; `dependents` lists downstream ones. |
| services.yaml | services, kafka_topics | `SVC01`…`SVC13` / `reserve-engine` | Includes `owner_history`, `config` and `renames`. |
| rules.yaml | rules | `BR-FRD-031` | 156 rules. Versions run contiguously; drafts have no effective dates. |
| products.yaml / claim_types.yaml | products, claim_types | `PRD-HOM-SE`, `CT-EOW` | Legacy wording terms are under `products[].wordings`. |
| process.yaml | stages, steps | `S1`…`S7`, `PS-REC-02` | Owner history, decisions with exact conditions, SLA, RACI. |
| vendors.yaml / regulators.yaml | vendors, regulators, circulars, reports | `VEN-01`, `CIRC-2026-04`, `NISA-TP2` | |
| incidents.yaml / adrs.yaml | incidents, adrs | `INC-2025-0412`, `ADR-019` | |
| timeline.yaml | programme, events, meetings, decisions, episodes, migration_waves, metrics | `EV-013`, `MTG-007`, `DEC-014`, `EP-019`, `MW-1` | Episodes are single facts owned by one file (RJ, GP and some TX files). |
| key_tickets.yaml | tickets | `CHUB-298` | 85 key tickets. The TX family fills TX070 up to 2,000 tickets (CHUB-101..CHUB-2100). |
| claims_profile.yaml | distributions | n/a | Input for the 15,000-row ST013. The ST generator computes the aggregates. |
| glossary.yaml | terms | `G-001` | Canonical term ↔ variants, per family. |
| contradictions.yaml | contradictions | `C01`…`C17` | The only contradictions allowed in the corpus. |
| placements.yaml | headline_questions, placements | `PL-001`… plus a stable `key` | What each file must plant. |
| corpus_plan.yaml | families, anchors | `LD001`, `CODE:a:<path>` | Budgets, extension minimums, ID ranges, and every anchor file with date, author and status. |
| names_denylist.yaml | entries | n/a | Real companies and regulators the verifier greps for. |

**World references** (used in placements, questions and manifests) take the form `TYPE:ID[@vN][#field[:qualifier]]`. Examples:

- `RULE:BR-FRD-031@v2#parameters.tier3_threshold`
- `INTERFACE:CLX-IF-042#schedule`
- `PROGRAM:CLRGL090#writes_tables:CLR.T_RESERVE`
- `SERVICE:recovery-svc#owner_history:T30`
- `TIMELINE:metrics#recovery_rate_pct`

Valid types are PERSON, SYSTEM, PROGRAM, COPYBOOK, JCL, BMS, TABLE, INTERFACE, SERVICE, TOPIC, RULE, PRODUCT, CLAIMTYPE, PROCESS, VENDOR, REGULATOR, CIRCULAR, REPORT, INCIDENT, ADR, EVENT, MEETING, DECISION, EPISODE, TICKET, GLOSSARY, CONTRA, TEAM, DEPT, LOC, COMMITTEE, ANCHOR, ORG, TIMELINE, PROFILE, COMMIT, CANARY and WAVE.

## 3. Hard rules for generators

1. **Exclusivity.** Before you state field X of entity Y, call `W.may_state(file_id, Y, X)`, or `W.is_exclusive(Y, X)`, which returns `(bool, file_id)`. If the field is reserved for another file, leave it out or write around it. Never paraphrase the value.
   - Pass the version for rules, e.g. `W.is_exclusive("BR-RSV-009@v3", "text")`.
   - Exclusive placements may carry `guards`: other entity fields that would leak the same fact. For example, the CLX-IF-042 schedule also guards `JCL:CLRNRSV3#schedule`. `is_exclusive` checks guards as well.
   - Exclusive rule parameters automatically guard that version's `text`.
   - An exclusive fact also has a **location**. It must appear only at the `location_hint` inside the target file. Example: the 3.1% indexation rate (PL-011) appears only in a Word comment in LD001, never in the LD001 body.
   - Every `CODE:a:<path>` file is mirrored unchanged in variants b and c. These mirrors are not violations. LD002 mirrors LD001 body text, headers, footers and footnotes. It does not mirror comments or tracked changes.
   - Example: `W.is_exclusive("CLX-IF-042", "schedule")` returns `(True, "VS033")`. So the XML catalogue, interface register, wiki page, runbooks and JCL schedule all omit "daily 02:15" for CLX-IF-042.
2. **Time.** A document states only what was true on its `date`, which you get from `W.anchor(fid)["date"]`. Use the as-of helpers:
   - `W.name_of("P005", d)`: Ingrid Sørensen until 2025-08-22, Ingrid Ashby from 2025-08-23.
   - `W.alias_holder("the CFO", d)`: Gareth Whitcombe until 2025-06-30, Priya Raman from 2025-07-01.
   - `W.system_name("SYS03", d)`, `W.service_name("reserve-engine", d)`, `W.rule_version(rid, d)`, `W.owner_of_process("S7", d)`, `W.interface_schedule(iid, d)`.
   - Respect `since` and `created` dates. For example, CLR.T_FRAUD_NOTIFICATION (created 2026-03-27) cannot appear in the 2025-02-14 data dictionary.
3. **Contradictions** exist only where `contradictions.yaml` plants them. Everything else must agree with the world.
4. **Filler** may invent harmless colour, such as rooms or weather. It must never invent a rule, threshold, owner, date, system link or program-table link.
5. **Names.** Use only world names. Check any new vendor or person name against `names_denylist.yaml`. Domains are `@corvane-mutual.example`, `@ibm-consulting.example` and `<vendor>.example`. Phone numbers use `07700 900xxx` or `+47/46/45 555 …`.
6. **Placements are a floor.** Plant every placement targeted at your files (`W.placements_for(fid)`). Write a manifest entry for each one, and copy `world_ref` and `exclusive` into it. You may plant more, but only non-exclusive world facts.

## 4. Traps and where they are planted

Placement IDs below are for this build. The `key` field (e.g. `vs4_calloway`) is the stable handle.

| Trap | World data | Planted in |
|---|---|---|
| (a) **Two CFOs.** Priya Raman (P001, aliases "P. Raman", "PR", "Priya", "the CFO") from 2025-07-01. Gareth Whitcombe (P002) until 2025-06-30. | `role_aliases` | LD028 PL-071 (Whitcombe signs). LD029 PL-072, VS006 PL-091, VS020 PL-118, TX001 PL-191, TX013 PL-211 ("PR"). TX007 PL-205 ("the CFO" = Whitcombe). |
| (b) **Namesakes.** Callum Fairbairn P022 (Corvane, Leeds, Motor Claims Team Leader) and P051 (IBM, London, Data Migration Lead). | `notes` | LD014 PL-047 (IBM author), TX010 PL-208 (Corvane), TX011 PL-209 (IBM), ST057 PL-187 (both). |
| (c) **Re-org 2025-09-01.** Title and manager both change for P008, P009, P012, P013, P014, P016 and P017. P043 changes on 2026-11-01. SIU moves under the CRO. | `titles`, `reports_to` | VS004 vs VS005 (PL-085..088), LD018 PL-057, VS044 PL-145. |
| (d) **The Claims Director.** P005 Ingrid Sørensen → Ingrid Ashby (married 2025-08-23), also written "Sorensen". | `name_history`, `email_history` | LD012 PL-039, VS004 PL-086, TX014 PL-212, TX074 PL-234, TX001 PL-192 (alias only). |
| **Subrogation owner over time.** P015 Calloway until 2024-12-31, P014 Quill (acting) 2025-01-01..2025-08-31, P013 Lindahl from 2025-09-01. | `process.stages[S7].owner_history` | The stale 2024 chart VS004/VS032 (C02). |
| **Reserve-table writers.** 8 programs; CLRRS150 writes only movements; the data dictionary omits CLRGL090. | `programs.yaml reserve_writers` | ST001 PL-154 (7 writers) vs ST019 PL-166 + code (C08). TX003 PL-197/198 (C07). LD024 PL-066. |
| **Code drift.** CLRFR040 hard-codes `070`. | `programs[CLRFR040].hardcoded_constants` | CODE:a PL-245 (C05). Fixed in CODE:c PL-274. |
| **Newer meeting beats the manual.** Tier-3 fraud threshold 60 from 2026-10-01. | BR-FRD-031 v2, DEC-014 | LD001 PL-003 (65 for all) vs TX002 PL-193 and TX031 PL-219 (C01). |
| **Draft vs approved.** Customer notice deadline. | BR-FRD-032 v1 (draft) / v2 | LD015 PL-049 vs LD016 PL-051 (C03). |
| **Superseded manual.** Tier-3 review cadence 30 days in v6.1 vs 14 days in v7.2. | BR-RSV-007 | LD012 PL-038 vs LD001 PL-002 (C04). |
| **Renames.** FRAUDNET→Sentinel 2025-03-01, ClaimLine Web→MyCorvane Claims 2024-10-14, DOCSTOR→Evidence Vault 2025-11-03, Adjuster Extranet→Assessor Portal 2025-09-01, reserve-svc→reserve-engine 2026-02-10. | `renames` | LD025 PL-067 vs ST054 PL-185 (C06), ST043 PL-178 vs ST049 PL-181 (C09), VS015 PL-107, VS016 PL-109, TX018 PL-216, LD013 PL-043. |
| **In-transcript corrections.** | DEC-011; reserve writers | TX001 PL-189/190 (C15), TX003 PL-197/198 (C07). |
| **Other dated contradictions.** | | C10 Tier-3 £40k vs £50k. C11 acknowledgement 5 days vs 1/2 days. C12 CLX-IF-043 03:00 vs 03:45. C13 subrogation £750 vs £1,000. C14 Fellgate on vs off the panel. C16 Team Leader payment authority £50k vs £75k. C17 Hem Sverige excess SEK 1,500 vs 2,000. |
| **Long-range definitions.** Tier-3 defined on p.15, used on p.271. LLNT defined on p.18, used on p.300. | | LD001 PL-001/002, PL-016/017. |
| **Re-sync.** Follow-up commit CM-09 (2026-11-12). | `corpus_plan CODE.commits` | CODE:c PL-273..276. The release notes (ST060) stop at R2026.09 on purpose. CHUB-421's summary does not name the new topic. |
| **Truncation canaries.** CN-01..CN-06, only in variant-b files. | `corpus_plan CODE.canaries` | CODE:b placements (kind `canary`). |
| **The prompt injection.** Exactly one, in GP002 (PL-278). | EP-012 | The GP generator owns the wording. Never copy it anywhere else. |

## 5. What each family must plant

Run `W.placements_for(fid)` for the exact list. Counts for this build: LD 73, VS 78, ST 37, TX 47, CODE 41, GP 18 (8 GP plus 10 RJ). 78 placements are exclusive.

- **LD** (30 files: 10 docx, 12 pdf, 8 doc)
  - LD001 is the 460–496-page manual. Its chapter outline and page ranges are in the anchor (`outline`). Plant definitions and uses at the hinted pages. It includes a split sentence across a page break (PL-006), a multi-page table (PL-007), a footnote (PL-008), header and footer (PL-009/010), a comment (PL-011), and tracked insert and delete (PL-012/013).
  - LD002 is an image-only scan with a received stamp and a handwritten note.
  - LD003 is two-column with multi-page tables.
  - LD004–LD011 are `.doc` policy wordings with old excesses (exclusive).
  - Also: LD012 is the superseded manual, LD013 the pre-rename architecture, LD014 the migration strategy with a 6-page mapping table, LD015/016 the draft and approved BRDs, and LD021 the 25–40 MB image-heavy guide (facts only in raster images).
- **VS** (50 files: 28 pptx, 11 docx, 11 pdf)
  - Connector-only facts (`arrow_only`), with labels on connector shapes or label boxes. Lane-only facts. Native-chart-only numbers. Speaker notes. Alt text. Group shapes. Raster labels (VS033 holds the exclusive CLX-IF-042 schedule).
  - The stale 2024 chart (VS004 and VS032) vs the current chart (VS005 and VS044).
- **ST** (60 files)
  - ST001 has the hidden sheet `_retired`, merged block headers and the stale writer list.
  - ST004 has the hidden sheet `calc`.
  - ST010 has native charts.
  - ST013 is the 15,000-row claims CSV, built from `claims_profile.yaml`. Record its aggregates as `aggregate_source` facts.
  - ST019 is the CRUD matrix.
  - ST035 is the interface XML: omit the 042 schedule and include dependsOn.
  - ST043 uses the old name in `info.title`.
  - ST053–060 are wiki HTML with nested tables. ST060 must stop at R2026.09.
  - ST030 holds the exclusive partitions; omit retention for `claims.reserve.movement.v1`.
- **TX** (75 files; ID layout txt TX001–030 and TX061–069, md TX031–060, json TX070–072, html TX073–075)
  - TX001–003 are two-hour transcripts with `[hh:mm:ss] Speaker:` lines. Put decisions and corrections at the hinted times.
  - TX070 is the 2,000-ticket export, dated 2026-11-11. CHUB-298 shows as "In Review" there.
  - Meeting records must match `timeline.meetings` (attendees and date).
- **CODE**
  - Variant a: ≈350 files, under 30 MB, head commit 2026-11-06.
  - Variant b: 600–700 files, under 45 MB, a superset of a. Canaries live only in b-only files.
  - Variant c: a plus commit CM-09.
  - The repo layout, CODEOWNERS mapping, commits CM-01..CM-09 (author, date, message, renames) and canaries are all in `corpus_plan.families[CODE]`.
  - COBOL must match `programs.yaml` exactly: SQL tables, CALLs and copybooks.
- **GP/RJ**
  - The probes use only obviously fake values and are clearly labelled.
  - Each RJ file carries exactly one exclusive fact (its episode, EP-001..EP-010).

## 6. Terminology and aliases by family (glossary.yaml)

| Canonical (schema) term | LD | VS | ST | TX | CODE |
|---|---|---|---|---|---|
| Claims Assessor | "loss adjuster" for external assessors (defined in §2.2); "skadetakstmann" in Norwegian wordings | "assessor" | Claims Assessor | "adjuster", "loss adjuster" | `claims_assessor_id`, ASSESSOR_ID |
| Fraud Referral | "referral to SIU" | "SIU referral" | fraud referral | "referral", "SIU referral" | T_FRAUD_REFERRAL |
| Reserve | "case reserve" | "reserve table" | `reserve_outstanding` | "case estimate", "the reserve table" | RSV |
| Subrogation | "recoveries", "regress" (Nordic) | "Recovery & Subrogation" | Subrogation | "sub-ro", "subro" | `subro` |
| First Notice of Loss | "notification of loss" (wordings), FNOL | FNOL | FNOL | FNOL | fnol |
| Claim Type | "peril", "cause of loss" | "loss type" | claim_type | "peril" | PERIL_CD |
| Claims Handler | "case handler" (v6.1) | "claim handler" | `handler_ref` | "handler" | HANDLER_USER_ID |

Other aliases:

- Fraud scores: "Sentinel score" and "FRAUDNET score" (before 2025-03-01).
- CLARA: "the ledger", "CLR", "Claims Ledger".
- Claims Hub: "CHUB", "the Hub".
- Excess: "egenandel" (NO), "självrisk" (SE), "selvrisiko" (DK).
- People: "PR" / "the CFO"; "the Claims Director"; "Bjorn" / "Bjørn"; "Tomasz Wojcik"; "Linnea Sjoberg".

## 7. Headline questions (answers in placements.yaml → headline_questions)

1. **Which programs write to the reserve table?** Eight: CLRFN030, CLRRS010, CLRRS020, CLRRS110, CLRRS130, CLRST040, CLRRC050 and CLRGL090. CLRRS150 writes movements only, and the data dictionary is stale.
   - Evidence: PL-066 (pdf), PL-110/111 (pptx), PL-154 and PL-166/167 (xlsx, csv), PL-197/198 (txt), PL-236..244 (code).
2. **Which rules govern fraud referral since the 2026 change?** BR-FRD-031 (65; Tier-3 ≥ 60 from 2026-10-01), BR-FRD-032 (notice within 10 business days), BR-FRD-033 (no decline on the score alone), BR-FRD-034 (FR1 within 30 days), BR-FRD-035 v2 (SIU triage within 3 business days), and BR-FRD-036 (deferral up to 60 days; beyond 30 days needs the Head of Counter-Fraud & SIU from 2026-10-01). BR-FRD-012 was superseded and BR-FRD-019 withdrawn. Tier-3 is defined by BR-TRI-003 v3.
   - Evidence: LD001, LD022, LD016, VS007, VS035, VS046, ST029/044/050/059, TX002/031/035/073, code.
3. **What breaks if CLX-IF-042 changes?**
   - Hop 1: CLX-IF-043, 044, 047 and 049.
   - Hop 2: CLX-IF-051, 055 and 058.
   - Hop 3: the NISA-TP2 return and the Reserving team's monthly IBNR run.
   - Teams: T14, T23, T17, T28, T15 and T12.
   - `W.impact("CLX-IF-042")` returns the same answer.
   - Evidence: LD014, VS002/003/019/033/043, ST035/039/054, TX004, code.
4. **Who owns the subrogation process?** Freya Lindahl (P013), Head of Recoveries & Subrogation, since 2025-09-01. Before her: Siobhan Quill (acting) and Martin Calloway (the stale 2024 chart).
   - Evidence: LD001, LD018, VS001/004/005/009/032, ST002, TX005, code.

## 8. worldlib API

| Call | What it does |
|---|---|
| `load_world()` | Cached; reads world/data only, no rng. |
| `W.people`, `W.systems`, `W.programs`, `W.tables`, `W.interfaces`, `W.services` (by name), `W.services_by_id`, `W.topics`, `W.rules`, `W.stages`, `W.steps`, `W.vendors`, `W.circulars`, `W.reports`, `W.incidents`, `W.adrs`, `W.events`, `W.meetings`, `W.decisions`, `W.episodes`, `W.tickets`, `W.glossary`, `W.contradictions`, `W.placements`, `W.anchors_by_id`, `W.teams`, `W.locations`, `W.committees`, `W.commits`, `W.canaries`, `W.waves` | Dict-by-id access. |
| `W.get(ref)`, `W.exists(ref)`, `W.canonical(ref)` | Resolve `TYPE:ID`, plain ids, `SVC05` or a service name. |
| `W.by_name(name)` | List of refs matching a name, alias, former name, id, email, title or glossary variant (accent- and case-insensitive). `W.resolve(name, kind=None)` raises if the match is ambiguous. |
| `W.title_of(pid, d)`, `manager_of`, `team_of`, `name_of`, `location_of`, `employed`, `alias_holder(alias, d)` | As-of helpers for people. |
| `W.team_lead(tid, d)`, `team_name`, `team_department` | As-of helpers for teams. |
| `W.owner_of_process(step_or_stage, d)` | Accepts `S7`, `RECOVERY` or `PS-REC-02`. |
| `W.rule_version(rid, d)`, `W.rules_in_force(d, area)` | As-of helpers for rules. |
| `W.system_name(sid, d)`, `W.service_name(svc, d)`, `W.service_owner(svc, d)`, `W.interface_schedule(iid, d)` | As-of helpers for systems, services and interfaces. |
| `W.impact(iid)` | Downstream hops, target systems, reports and consumer teams. |
| `W.is_exclusive(ref, field=None)` | Returns `(bool, file_id)`. `W.allowed_files(ref, field)` lists the target and also_in files; `W.may_state(file_id, ref, field)` returns a bool; `W.exclusive_placements(ref, field)` returns the matching placements. |
| `W.placements_for(file_id, include_also=False)`, `W.anchors(family)`, `W.anchor(fid)`, `W.contradictions_for(fid)`, `W.family_plan(fam)` | Placement and corpus-plan access. |
| `W.lexicon()` | List of `{term, ref, kind}` covering every name, alias, id, column, path, topic and glossary variant. `W.lookup_term(t)` looks one up. graph_audit uses these to trace graph nodes back to the world. |

## 9. Invented-name spot checks (web, 2026-11-15)

"Corvane" (only the unrelated "Corvus Insurance" came up), "Brackenfield Loss Adjusting", "Programme Skerry", and "Greyfold Investigations / Salvanta Salvage / Quarryhill Solicitors": no matching real companies were found.

Four people were renamed before release to avoid resembling public figures: Arjun Kesavan, Imran Talwar, Morag Duthie and Derek Ollerton. Results are recorded in `names_denylist.yaml → invented_name_checks`.

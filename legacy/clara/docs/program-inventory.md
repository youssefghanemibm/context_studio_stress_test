# CLARA program inventory

Inventory of the CLARA programs in `legacy/clara/cobol/` as of 2026-10-20.
Status and replacement service reflect the Claims Hub migration plan on that date.

| Program | Type | Area | Description | Transaction / job | Claims Hub replacement | Status |
|---|---|---|---|---|---|---|
| CLRFN010 | online | FNOL | FNOL capture - main entry for telephone and portal hand-off | FN01 | fnol-intake-svc | active |
| CLRFN015 | online | FNOL | FNOL policy lookup against PALM snapshot and Vehicle Data Service | FN15 | fnol-intake-svc | active |
| CLRFN020 | online | FNOL | FNOL claimant and third-party details | FN02 | fnol-intake-svc | active |
| CLRFN030 | online | FNOL | Create claim record and default reserve (BR-FNOL-005) | FN03 | reserve-engine | active |
| CLRFN040 | batch | FNOL | Overnight portal FNOL import (MyCorvane Claims, CLX-IF-001 backlog) | CLRNFN01 | fnol-intake-svc | active |
| CLRFN050 | batch | FNOL | Evidence Intake Gateway photo and telematics reference import | CLRNFN01 | fnol-intake-svc | active |
| CLRFN060 | online | FNOL | Duplicate claim check (same policy, date of loss +/-3 days) | FN06 | fnol-intake-svc | active |
| CLRFN070 | batch | FNOL | FNOL acknowledgement extract to Notify (CLX-IF-006) | CLRNFN02 | notification-svc | active |
| CLRFN080 | batch | FNOL | Late notification report (> 30 days after loss) | CLRWMI01 | fnol-intake-svc | active |
| CLRFN090 | online | FNOL | FNOL amend and reopen | FN09 | claim-core-svc | active |
| CLRFN100 | batch | FNOL | PALM policy snapshot refresh (CLX-IF-003) | CLRNFN01 | fnol-intake-svc | active |
| CLRFN110 | online | FNOL | Broker FNOL bulk entry | FN11 | fnol-intake-svc | active |
| CLRFN120 | batch | FNOL | FNOL MI daily counts | CLRNMI01 | - | active |
| CLRFN130 | online | FNOL | Nordic FNOL entry (Norwegian, Swedish and Danish fields) | FN13 | fnol-intake-svc | active |
| CLRTR010 | online | TRIAGE | Triage workbench | TR01 | triage-svc | active |
| CLRTR020 | batch | TRIAGE | Tier classification batch - re-tier on estimate change (BR-TRI-003) | CLRNTR01 | triage-svc | active |
| CLRTR030 | online | TRIAGE | Tier override with reason | TR03 | triage-svc | active |
| CLRTR040 | batch | TRIAGE | Fraud pre-screen request to Sentinel (batch) | CLRNTR01 | triage-svc | active |
| CLRTR050 | online | TRIAGE | Routing to team queue | TR05 | triage-svc | active |
| CLRTR060 | batch | TRIAGE | Fast-track eligibility sweep (BR-TRI-006) | CLRNTR01 | triage-svc | active |
| CLRTR070 | online | TRIAGE | Triage notes and diary | TR07 | triage-svc | active |
| CLRTR080 | batch | TRIAGE | Triage SLA breach report | CLRNMI01 | - | active |
| CLRTR090 | online | TRIAGE | Major loss alert for Tier-3 claims | TR09 | triage-svc | active |
| CLRTR100 | batch | TRIAGE | Re-triage after policy change | CLRNTR01 | triage-svc | active |
| CLRAS010 | online | ASSESS | Assessment workbench | AS01 | assessment-svc | active |
| CLRAS020 | online | ASSESS | Claims Assessor appointment (internal or vendor) | AS02 | assessment-svc | active |
| CLRAS030 | batch | ASSESS | Assessor Portal instruction export (CLX-IF-013) | CLRNAS01 | assessment-svc | active |
| CLRAS040 | batch | ASSESS | Assessor report import from Assessor Portal (CLX-IF-014) | CLRNAS01 | assessment-svc | active |
| CLRAS050 | online | ASSESS | Inspection booking | AS05 | assessment-svc | active |
| CLRAS060 | online | ASSESS | Estimate entry and validation | AS06 | assessment-svc | active |
| CLRAS070 | batch | ASSESS | Vendor invoice matching (assessor fees, CLX-IF-016) | CLRNAS02 | payment-orchestrator | active |
| CLRAS080 | online | ASSESS | Coverage decision | AS08 | assessment-svc | active |
| CLRAS090 | batch | ASSESS | Desk assessment queue builder (BR-ASM-008) | CLRWMI01 | assessment-svc | active |
| CLRAS100 | batch | ASSESS | Assessment SLA report | CLRNMI01 | - | active |
| CLRAS110 | online | ASSESS | Nordic takst (assessment) entry | AS11 | assessment-svc | active |
| CLRAS120 | batch | ASSESS | Repair network job export (Thistlecombe, Vardholm, CLX-IF-015) | CLRNAS01 | assessment-svc | active |
| CLRRS010 | online | RESERVE | Initial reserve set | RS01 | reserve-engine | active |
| CLRRS015 | subprogram | RESERVE | Reserve authority check (BR-RSV-003) - called subprogram | called | reserve-engine | active |
| CLRRS020 | online | RESERVE | Reserve adjustment | RS02 | reserve-engine | active |
| CLRRS030 | online | RESERVE | Reserve enquiry and history | RS03 | reserve-engine | active |
| CLRRS040 | online | RESERVE | Reserve approval queue (above authority) | RS04 | reserve-engine | active |
| CLRRS110 | batch | RESERVE | Tier-3 reserve review scheduler and revaluation (BR-RSV-007) | CLRNRSV1 | reserve-engine | active |
| CLRRS120 | batch | RESERVE | Reserve review overdue report | CLRNRSV1 | reserve-engine | active |
| CLRRS130 | batch | RESERVE | Monthly reserve indexation for bodily-injury claims (BR-RSV-009) | CLRMRSV1 | reserve-engine | active |
| CLRRS140 | batch | RESERVE | Reserve history archiver (month-end snapshots) | CLRNRSV2 | reserve-engine | active |
| CLRRS150 | batch | RESERVE | Reserve movement correction utility | CLRNRSV2 | reserve-engine | active |
| CLRRS160 | batch | RESERVE | Large loss notification extract to ReCede (CLX-IF-031, BR-RSV-011) | CLRNRSV4 | reserve-engine | active |
| CLRRS170 | batch | RESERVE | Daily reserve movement extract (CLX-IF-042) | CLRNRSV3 | reserve-engine | active |
| CLRRS180 | batch | RESERVE | Reserve snapshot for month-end (CDW) | CLRMRSV2 | reserve-engine | active |
| CLRRS190 | batch | RESERVE | Reserve adequacy MI | CLRMRSV2 | - | active |
| CLRRS200 | online | RESERVE | Reserve type maintenance | RS20 | reserve-engine | active |
| CLRRS210 | batch | RESERVE | Reserve parallel-run reconciliation against reserve-engine (2026-03-02 to 2026-08-28) | CLRDRSV9 | - | retired |
| CLRFR010 | online | FRAUD | Fraud indicators entry | FR01 | fraud-referral-svc | active |
| CLRFR020 | online | FRAUD | Sentinel score request (online, CLX-IF-008) | FR02 | fraud-referral-svc | active |
| CLRFR030 | online | FRAUD | Fraud referral creation - online (threshold read from CLR.T_PARAM) | FR03 | fraud-referral-svc | active |
| CLRFR040 | batch | FRAUD | Fraud referral batch sweep (nightly) | CLRNFR01 | fraud-referral-svc | active |
| CLRFR050 | online | FRAUD | SIU outcome update | FR05 | fraud-referral-svc | active |
| CLRFR060 | batch | FRAUD | Customer referral notice scheduler (NISA Circular 2026/04) | CLRNFR02 | notification-svc | active |
| CLRFR070 | batch | FRAUD | SIU Case Manager export (CLX-IF-011 batch catch-up) | CLRWFR01 | fraud-referral-svc | active |
| CLRFR080 | batch | FRAUD | Linked claims detection (BR-FRD-005) | CLRNFR01 | fraud-referral-svc | active |
| CLRFR090 | batch | FRAUD | NISA-FR1 quarterly fraud referral return extract (CLX-IF-033) | CLRQFR01 | reporting-feed-svc | active |
| CLRFR100 | online | FRAUD | Fraud referral enquiry | FR10 | fraud-referral-svc | active |
| CLRFR110 | batch | FRAUD | Sentinel score batch refresh (CLX-IF-009/010) | CLRNFR01 | fraud-referral-svc | active |
| CLRFR120 | online | FRAUD | Customer-notice deferral approval (tipping-off, BR-FRD-036) | FR12 | fraud-referral-svc | active |
| CLRFR130 | batch | FRAUD | Fraud MI weekly | CLRWFR01 | - | active |
| CLRFR140 | batch | FRAUD | Auto-decline sweep (score >= 90) - DISABLED 2026-04-01 (BR-FRD-019 withdrawn) | CLRNFR99 | - | disabled |
| CLRST010 | online | SETTLE | Settlement offer | ST01 | settlement-svc | active |
| CLRST020 | online | SETTLE | Payment request (BR-STL-002 authority) | ST02 | payment-orchestrator | active |
| CLRST030 | batch | SETTLE | Payment batch build to CPG (CLX-IF-019) | CLRNPAY1 | payment-orchestrator | active |
| CLRST040 | batch | SETTLE | Settlement finalisation and reserve close-down (BR-RSV-014) | CLRNSTL1 | settlement-svc | active |
| CLRST050 | batch | SETTLE | Payment confirmation import from CPG (CLX-IF-020) | CLRNPAY2 | payment-orchestrator | active |
| CLRST060 | online | SETTLE | Payee maintenance | ST06 | payment-orchestrator | active |
| CLRST070 | batch | SETTLE | Sanctions screening request to WatchScreen (CLX-IF-017) | CLRNPAY1 | payment-orchestrator | active |
| CLRST080 | batch | SETTLE | Fast-track straight-through settlement (BR-STL-009) | CLRNSTL1 | settlement-svc | active |
| CLRST090 | online | SETTLE | Payment cancellation and stop | ST09 | payment-orchestrator | active |
| CLRST100 | batch | SETTLE | Late payment interest calculation (BR-STL-014) | CLRNSTL1 | settlement-svc | active |
| CLRST110 | batch | SETTLE | Vendor invoice payment run | CLRWPAY1 | payment-orchestrator | active |
| CLRST120 | online | SETTLE | Settlement enquiry | ST12 | settlement-svc | active |
| CLRST130 | batch | SETTLE | Payment MI | CLRNMI01 | - | active |
| CLRST140 | batch | SETTLE | Nordic payment file NOK/SEK/DKK to CPG (CLX-IF-021) | CLRNPAY1 | payment-orchestrator | active |
| CLRRC010 | online | RECOVER | Recovery potential assessment | RC01 | recovery-svc | active |
| CLRRC020 | online | RECOVER | Subrogation case open and demand (BR-REC-003) | RC02 | recovery-svc | active |
| CLRRC030 | batch | RECOVER | Subrogation demand letter extract to Notify (CLX-IF-026) | CLRWRC01 | notification-svc | active |
| CLRRC040 | batch | RECOVER | SUBTRAK synchronisation (CLX-IF-022) | CLRNRC01 | recovery-svc | active |
| CLRRC050 | batch | RECOVER | Recovery receipt posting - nets recoveries from the case reserve | CLRNRC01 | recovery-svc | active |
| CLRRC060 | online | RECOVER | Solicitor instruction (Quarryhill Solicitors, CLX-IF-025) | RC06 | recovery-svc | active |
| CLRRC070 | batch | RECOVER | Salvage disposal import (Salvanta, CLX-IF-024) | CLRNRC01 | recovery-svc | active |
| CLRRC080 | batch | RECOVER | Limitation diary sweep (BR-REC-009) | CLRNRC01 | recovery-svc | active |
| CLRRC090 | online | RECOVER | Recovery write-off (BR-REC-011) | RC09 | recovery-svc | active |
| CLRRC100 | batch | RECOVER | Recovery MI monthly | CLRWMI01 | - | active |
| CLRCM010 | subprogram | COMMON | Date and business-day utility (UK, NO, SE, DK calendars) | called | - | active |
| CLRCM020 | subprogram | COMMON | Audit trail writer | called | - | active |
| CLRCM030 | subprogram | COMMON | Currency conversion (reads CLR.T_CURRENCY_RATE) | called | - | active |
| CLRCM040 | subprogram | COMMON | Parameter reader (reads CLR.T_PARAM with validity dates) | called | - | active |
| CLRCM050 | subprogram | COMMON | Error handler and abend formatter | called | - | active |
| CLRCM060 | subprogram | COMMON | Code lookup | called | - | active |
| CLRCM070 | subprogram | COMMON | User authority check | called | - | active |
| CLRCM080 | subprogram | COMMON | Notes writer | called | - | active |
| CLRCM090 | subprogram | COMMON | Diary writer | called | - | active |
| CLRCM100 | subprogram | COMMON | Document reference writer (DOCSTOR / Evidence Vault) | called | document-svc | active |
| CLRCM110 | subprogram | COMMON | MQ put wrapper | called | - | active |
| CLRCM120 | subprogram | COMMON | MQ get wrapper | called | - | active |
| CLRCM130 | batch | COMMON | Interface log housekeeping | CLRWCM01 | - | active |
| CLRCM140 | batch | COMMON | Archive and purge of claims closed more than 7 years (BR-GEN-004) | CLRWCM01 | - | active |
| CLRGL010 | batch | GL | Daily GL posting extract - payments (CLX-IF-028) | CLRNGL01 | gl-posting-svc | active |
| CLRGL020 | batch | GL | GL period control | CLRMGL01 | gl-posting-svc | active |
| CLRGL030 | batch | GL | Currency rate load from Group Ledger (CLX-IF-027) | CLRNGL01 | - | active |
| CLRGL040 | batch | GL | Reinsurance cession calculation | CLRMGL01 | - | active |
| CLRGL050 | batch | GL | Month-end accruals | CLRMGL01 | gl-posting-svc | active |
| CLRGL060 | batch | GL | GL reconciliation report | CLRMGL01 | gl-posting-svc | active |
| CLRGL070 | batch | GL | Recovery income posting (CLX-IF-029) | CLRNGL01 | gl-posting-svc | active |
| CLRGL090 | batch | GL | Year-end reserve currency revaluation (Nordic reserves to GBP) | CLRYGL90 | reserve-engine | active |
| CLRRP010 | batch | REPORT | Daily claims MI extract to CDW (CLX-IF-030) | CLRNRP01 | reporting-feed-svc | active |
| CLRRP020 | batch | REPORT | Reserve report - outstanding by product | CLRMRP01 | - | active |
| CLRRP030 | batch | REPORT | NISA-TP2 data extract | CLRQRP01 | reporting-feed-svc | active |
| CLRRP040 | batch | REPORT | NISA-CT1 claims timeliness extract (CLX-IF-032) | CLRQRP01 | reporting-feed-svc | active |
| CLRRP050 | batch | REPORT | Assessor performance report | CLRMRP01 | - | active |
| CLRRP060 | batch | REPORT | Fraud referral MI (NISA-FR1 support) | CLRQRP01 | reporting-feed-svc | active |
| CLRRP070 | batch | REPORT | Recovery MI | CLRMRP01 | - | active |
| CLRRP080 | batch | REPORT | Ad-hoc report driver | CLRMRP01 | - | active |
| CLRRP090 | batch | REPORT | Executive dashboard extract | CLRNRP01 | - | active |
| CLRRP100 | batch | REPORT | Data quality exceptions report | CLRNRP01 | - | active |

## Notes

- `CLRRS210` ran only during the reserve parallel run (2026-03-02 to 2026-08-28) and is retired.
- `CLRFR140` (auto-decline sweep) is disabled from 2026-04-01; its job `CLRNFR99` is off the schedule.
- Renamed programs: `CLRFR020` (was FNETCAL1) and `CLRFR030` (was FNETREF1) since 2025-03-01;
  `CLRGL090` (was YEREVAL1) since 2021-01-01; `CLRRC010` (was SUBRO010) since 2019-04-01.
- Open defect CHUB-298: the batch sweep `CLRFR040` still compares scores with a constant
  instead of reading the referral threshold from `CLR.T_PARAM`.


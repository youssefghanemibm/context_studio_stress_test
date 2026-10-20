# CLARA batch jobs

Jobs in `legacy/clara/jcl/` as of 2026-10-20. All jobs are scheduled by the Batch Scheduler and
supported by Mainframe Batch Operations.

## CLRNFN01 - Nightly FNOL imports

- Schedule: daily 22:30
- Status: active
- STEP010: `CLRFN100` - PALM policy snapshot refresh (CLX-IF-003)
- STEP020: `CLRFN040` - Overnight portal FNOL import (MyCorvane Claims, CLX-IF-001 backlog)
- STEP030: `CLRFN050` - Evidence Intake Gateway photo and telematics reference import

## CLRNFN02 - FNOL acknowledgement extract

- Schedule: daily 06:15
- Status: active
- STEP010: `CLRFN070` - FNOL acknowledgement extract to Notify (CLX-IF-006)

## CLRNTR01 - Nightly triage

- Schedule: daily 23:45
- Status: active
- STEP010: `CLRTR040` - Fraud pre-screen request to Sentinel (batch)
- STEP020: `CLRTR020` - Tier classification batch - re-tier on estimate change (BR-TRI-003)
- STEP030: `CLRTR060` - Fast-track eligibility sweep (BR-TRI-006)
- STEP040: `CLRTR100` - Re-triage after policy change

## CLRNAS01 - Assessor and repairer exchange

- Schedule: daily 00:30
- Status: active
- STEP010: `CLRAS030` - Assessor Portal instruction export (CLX-IF-013)
- STEP020: `CLRAS040` - Assessor report import from Assessor Portal (CLX-IF-014)
- STEP030: `CLRAS120` - Repair network job export (Thistlecombe, Vardholm, CLX-IF-015)

## CLRNAS02 - Vendor invoice matching

- Schedule: Mon-Fri 01:00
- Status: active
- STEP010: `CLRAS070` - Vendor invoice matching (assessor fees, CLX-IF-016)

## CLRNRSV1 - Tier-3 reserve review and revaluation

- Schedule: daily 01:30
- Status: active
- STEP010: `CLRRS110` - Tier-3 reserve review scheduler and revaluation (BR-RSV-007)
- STEP020: `CLRRS120` - Reserve review overdue report

## CLRNRSV2 - Reserve history and corrections

- Schedule: daily 02:00
- Status: active
- STEP010: `CLRRS140` - Reserve history archiver (month-end snapshots)
- STEP020: `CLRRS150` - Reserve movement correction utility

## CLRNRSV3 - Reserve movement extract (CLX-IF-042)

- Schedule: see the interface catalogue entry for this extract.
- Status: active
- STEP010: `CLRRS170` - Daily reserve movement extract (CLX-IF-042)
- Restart: Rerun the whole job; CLRRS170 only extracts rows with EXTRACTED_FLAG = 'N'.

## CLRNRSV4 - Large loss notification extract

- Schedule: daily 07:00
- Status: active
- STEP010: `CLRRS160` - Large loss notification extract to ReCede (CLX-IF-031, BR-RSV-011)

## CLRMRSV1 - Monthly reserve indexation

- Schedule: 1st business day 03:00
- Status: active
- STEP010: `CLRRS130` - Monthly reserve indexation for bodily-injury claims (BR-RSV-009)

## CLRMRSV2 - Month-end reserve snapshot

- Schedule: last business day 22:00
- Status: active
- STEP010: `CLRRS180` - Reserve snapshot for month-end (CDW)
- STEP020: `CLRRS190` - Reserve adequacy MI

## CLRDRSV9 - Reserve parallel-run reconciliation (retired 2026-08-28)

- Schedule: daily 05:00 (2026-03-02 to 2026-08-28)
- Status: retired
- STEP010: `CLRRS210` - Reserve parallel-run reconciliation against reserve-engine (2026-03-02 to 2026-08-28)

## CLRNFR01 - Nightly fraud scoring and referral sweep

- Schedule: daily 00:15
- Status: active
- STEP010: `CLRFR110` - Sentinel score batch refresh (CLX-IF-009/010)
- STEP020: `CLRFR080` - Linked claims detection (BR-FRD-005)
- STEP030: `CLRFR040` - Fraud referral batch sweep (nightly)

## CLRNFR02 - Customer referral notices

- Schedule: Mon-Fri 06:30
- Status: active
- STEP010: `CLRFR060` - Customer referral notice scheduler (NISA Circular 2026/04)

## CLRWFR01 - Weekly fraud MI and SIU export

- Schedule: Mon 04:00
- Status: active
- STEP010: `CLRFR070` - SIU Case Manager export (CLX-IF-011 batch catch-up)
- STEP020: `CLRFR130` - Fraud MI weekly

## CLRQFR01 - Quarterly NISA-FR1 extract

- Schedule: quarterly, 5th business day after quarter end
- Status: active
- STEP010: `CLRFR090` - NISA-FR1 quarterly fraud referral return extract (CLX-IF-033)

## CLRNFR99 - Auto-decline sweep (disabled 2026-04-01)

- Schedule: removed from schedule 2026-04-01 (was daily 00:45)
- Status: disabled
- STEP010: `CLRFR140` - Auto-decline sweep (score >= 90) - DISABLED 2026-04-01 (BR-FRD-019 withdrawn)

## CLRNSTL1 - Nightly settlement and closure

- Schedule: daily 21:30
- Status: active
- STEP010: `CLRST080` - Fast-track straight-through settlement (BR-STL-009)
- STEP020: `CLRST040` - Settlement finalisation and reserve close-down (BR-RSV-014)
- STEP030: `CLRST100` - Late payment interest calculation (BR-STL-014)

## CLRNPAY1 - Payment batch to CPG

- Schedule: Mon-Fri 16:30
- Status: active
- STEP010: `CLRST070` - Sanctions screening request to WatchScreen (CLX-IF-017)
- STEP020: `CLRST030` - Payment batch build to CPG (CLX-IF-019)
- STEP030: `CLRST140` - Nordic payment file NOK/SEK/DKK to CPG (CLX-IF-021)

## CLRNPAY2 - Payment confirmations

- Schedule: Mon-Fri 07:30
- Status: active
- STEP010: `CLRST050` - Payment confirmation import from CPG (CLX-IF-020)

## CLRWPAY1 - Vendor payment run

- Schedule: Thu 15:00
- Status: active
- STEP010: `CLRST110` - Vendor invoice payment run

## CLRNRC01 - Nightly recoveries

- Schedule: daily 22:00
- Status: active
- STEP010: `CLRRC040` - SUBTRAK synchronisation (CLX-IF-022)
- STEP020: `CLRRC050` - Recovery receipt posting - nets recoveries from the case reserve
- STEP030: `CLRRC070` - Salvage disposal import (Salvanta, CLX-IF-024)
- STEP040: `CLRRC080` - Limitation diary sweep (BR-REC-009)

## CLRWRC01 - Subrogation demand letters

- Schedule: Tue,Thu 05:00
- Status: active
- STEP010: `CLRRC030` - Subrogation demand letter extract to Notify (CLX-IF-026)

## CLRNGL01 - Daily GL feeds

- Schedule: daily 03:15
- Status: active
- STEP010: `CLRGL030` - Currency rate load from Group Ledger (CLX-IF-027)
- STEP020: `CLRGL010` - Daily GL posting extract - payments (CLX-IF-028)
- STEP030: `CLRGL070` - Recovery income posting (CLX-IF-029)

## CLRMGL01 - GL month-end

- Schedule: last business day 23:00
- Status: active
- STEP010: `CLRGL020` - GL period control
- STEP020: `CLRGL040` - Reinsurance cession calculation
- STEP030: `CLRGL050` - Month-end accruals
- STEP040: `CLRGL060` - GL reconciliation report

## CLRYGL90 - Year-end reserve currency revaluation

- Schedule: annually 31 Dec 23:30 (and on Reserving request)
- Status: active
- STEP010: `CLRGL090` - Year-end reserve currency revaluation (Nordic reserves to GBP)
- Restart: Rerun allowed (revaluation is idempotent for the same rate date).

## CLRNRP01 - Daily MI to CDW

- Schedule: daily 04:30
- Status: active
- STEP010: `CLRRP010` - Daily claims MI extract to CDW (CLX-IF-030)
- STEP020: `CLRRP090` - Executive dashboard extract
- STEP030: `CLRRP100` - Data quality exceptions report

## CLRMRP01 - Monthly reports

- Schedule: 2nd business day 06:00
- Status: active
- STEP010: `CLRRP020` - Reserve report - outstanding by product
- STEP020: `CLRRP050` - Assessor performance report
- STEP030: `CLRRP070` - Recovery MI
- STEP040: `CLRRP080` - Ad-hoc report driver

## CLRQRP01 - Quarterly NISA extracts

- Schedule: quarterly, 4th business day after quarter end
- Status: active
- STEP010: `CLRRP030` - NISA-TP2 data extract
- STEP020: `CLRRP040` - NISA-CT1 claims timeliness extract (CLX-IF-032)
- STEP030: `CLRRP060` - Fraud referral MI (NISA-FR1 support)

## CLRWCM01 - Weekly housekeeping

- Schedule: Sun 02:00
- Status: active
- STEP010: `CLRCM130` - Interface log housekeeping
- STEP020: `CLRCM140` - Archive and purge of claims closed more than 7 years (BR-GEN-004)

## CLRNMI01 - Operational MI

- Schedule: daily 05:30
- Status: active
- STEP010: `CLRFN120` - FNOL MI daily counts
- STEP020: `CLRTR080` - Triage SLA breach report
- STEP030: `CLRAS100` - Assessment SLA report
- STEP040: `CLRST130` - Payment MI

## CLRWMI01 - Weekly MI

- Schedule: Mon 05:00
- Status: active
- STEP010: `CLRFN080` - Late notification report (> 30 days after loss)
- STEP020: `CLRAS090` - Desk assessment queue builder (BR-ASM-008)
- STEP030: `CLRRC100` - Recovery MI monthly


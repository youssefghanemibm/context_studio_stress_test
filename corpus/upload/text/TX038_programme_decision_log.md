# Programme Skerry – Decision Log

| | |
|---|---|
| **Owner** | Arjun Kesavan, Programme Delivery Lead (Programme Management Office) |
| **Sponsor** | Duncan Ferrier, Chief Operating Officer |
| **Last updated** | 10 November 2026 |
| **Entries** | 18 |
| **Classification** | Internal |

## Document control

| Version | Date | Author | Change |
|---|---|---|---|
| 1.0 | 20 Jan 2025 | Arjun Kesavan | Log created after programme kick-off |
| 2.0 | 15 Sep 2025 | Arjun Kesavan | Restructured by forum; re-organisation titles applied |
| 2.6 | 12 Feb 2026 | Arjun Kesavan | Design Authority decisions added |
| 3.1 | 21 Sep 2026 | Arjun Kesavan | Wave 1 go/no-go and Fraud Rules Workshop decisions added |
| 3.4 | 10 Nov 2026 | Arjun Kesavan | Steering Committee (October) decisions added; log re-baselined |

## How to use this log

Each entry records what was decided, by whom, in which forum and where the source record is held. The log does not replace the minutes; where minutes and log differ, raise it with the PMO. Decisions taken after the last update date are not yet included.

Regulatory clarifications (DEC-013) are held in the Compliance regulatory correspondence log and are not reproduced here.

## Summary

| ID | Date | Forum | Decision (abridged) |
|---|---|---|---|
| DEC-001 | 2025-01-13 | Programme Skerry kick-off | Adopt a strangler-fig, wave-based migration (ADR-001). |
| DEC-002 | 2025-03-03 | Sentinel rename cut-over call (INC-2025-0233) | Keep the fraudnet.corvane.internal DNS alias until 2025-03-31 and patch CLRFR020 the same … |
| DEC-003 | 2025-04-28 | Incident bridge: INC-2025-0412 (CLX-IF-042 / GL journals) | Revert the RSVMOVE RM-AMOUNT widening, add a record-version byte, and move CLX-IF-043 from… |
| DEC-020 | 2025-08-12 | Outside a formal meeting | Approve reserve and payment authority limits v3 (BR-RSV-003 v3, BR-STL-002 v3) effective 2… |
| DEC-004 | 2025-09-03 | Subrogation process ownership handover | Freya Lindahl owns the subrogation process from 2025-09-01; Siobhan Quill leads the UK rec… |
| DEC-017 | 2025-10-21 | Design Authority (reserve synchronisation) | Replace CDC (ADR-005) with the CLX-IF-049 batch-to-event bridge (ADR-012, ADR-017). |
| DEC-019 | 2026-01-20 | Outside a formal meeting | Remove Fellgate Adjusting Partners from the assessor panel effective 2026-01-31; open inst… |
| DEC-018 | 2026-02-03 | Design Authority (reserve-engine rename) | Rename reserve-svc to reserve-engine effective 2026-02-10 (ADR-019). |
| DEC-005 | 2026-03-05 | Reserving design review (reserve-engine) | reserve-engine will record currency revaluations as RV movements, closing audit finding IA… |
| DEC-006 | 2026-03-05 | Reserving design review (reserve-engine) | Propose a 14-day Tier-3 reserve review cadence from 2026-07-01 to the Reserving Committee. |
| DEC-007 | 2026-03-12 | Claims Fraud Forum (Circular 2026/04 rules) | Approve BR-FRD-031 v1, BR-FRD-032 v2, BR-FRD-033, BR-FRD-034, BR-FRD-035 v2 and BR-FRD-036… |
| DEC-008 | 2026-06-09 | Reserving Committee (June 2026) | Approve the 14-day Tier-3 reserve review cadence (BR-RSV-007 v3) effective 2026-07-01. |
| DEC-009 | 2026-09-11 | Wave 1 go/no-go | Go decision for Wave 1 (UK motor) cut-over on 2026-09-14; freeze 2026-09-11 18:00 to 2026-… |
| DEC-014 | 2026-09-17 | Fraud Rules Workshop | From 2026-10-01 refer Tier-3 claims to SIU at a Sentinel score of 60 or more (general thre… |
| DEC-015 | 2026-09-17 | Fraud Rules Workshop | From 2026-10-01 customer-notice deferrals beyond 30 days need the Head of Counter-Fraud & … |
| DEC-016 | 2026-09-17 | Fraud Rules Workshop | Option to lower the general referral threshold to 60 for all claims rejected. |
| DEC-010 | 2026-10-08 | Programme Skerry Steering Committee (October 2026) | Approve a contingency drawdown of £1.8m for Wave 2 (approved by the CFO, Priya Raman). |
| DEC-011 | 2026-10-08 | Programme Skerry Steering Committee (October 2026) | Wave 2 cut-over date confirmed as 2027-02-15 (an earlier draft date of 2027-01-18 is void)… |

## Decision records

### DEC-001 – 13 January 2025

- Forum: Programme Skerry kick-off – Programme Skerry Steering Committee
- Decided by: Duncan Ferrier (Chief Operating Officer)
- Decision: Adopt a strangler-fig, wave-based migration (ADR-001).
- References:
    - ADR-001 – Strangler-fig migration from CLARA to Claims Hub
- Related: ADR-001 records the strangler-fig approach; migration waves MW-0, MW-1 and MW-2 follow from it.
- Source record: Programme Skerry Kick-off
- Status: Approved.

### DEC-002 – 3 March 2025

- Forum: Sentinel rename cut-over call (INC-2025-0233)
- Decided by: Graham Pocock (CLARA Platform Manager)
- Decision: Keep the fraudnet.corvane.internal DNS alias until 2025-03-31 and patch CLRFR020 the same day.
- References:
    - CHUB-119 – CLRFR020 still calls retired fraudnet.corvane.internal endpoint after Sentinel rename (INC-2025-0233)
- Source record: Transcript – Sentinel Rename Cut-over Call
- Status: Approved.

### DEC-003 – 28 April 2025

- Forum: Incident bridge: INC-2025-0412 (CLX-IF-042 / GL journals)
- Decided by: Henrik Vestergaard (Integration Platform Lead); Hamish Gilchrist (Financial Controller)
- Decision: Revert the RSVMOVE RM-AMOUNT widening, add a record-version byte, and move CLX-IF-043 from 03:00 to 03:45.
- References:
    - CHUB-142 – Revert RSVMOVE RM-AMOUNT width and add RM-REC-VERSION (INC-2025-0412)
    - CHUB-143 – Move CLX-IF-043 GL reserve journal from 03:00 to 03:45 and validate record version
- Related: Follows the incident bridge for INC-2025-0412.
- Source record: Transcript – Incident Bridge INC-2025-0412
- Status: Approved.

### DEC-020 – 12 August 2025

- Forum: Not taken in a formal meeting (recorded by email / approval note)
- Decided by: Ingrid Sørensen (Claims Director); Priya Raman (Chief Financial Officer)
- Decision: Approve reserve and payment authority limits v3 (BR-RSV-003 v3, BR-STL-002 v3) effective 2025-09-01.
- References:
    - BR-RSV-003 – Reserve authority limits
    - BR-STL-002 – Payment authority limits
- Source record: Approval email held by the PMO
- Status: Approved.

### DEC-004 – 3 September 2025

- Forum: Subrogation process ownership handover
- Decided by: Ingrid Ashby (Claims Director)
- Decision: Freya Lindahl owns the subrogation process from 2025-09-01; Siobhan Quill leads the UK recoveries team; SUBTRAK retirement target set to 2026-12-31.
- References:
    - SYS24 – Subrogation Tracker
- Source record: Transcript – Subrogation Ownership Handover
- Status: Approved. SUBTRAK retirement target 31 December 2026.

### DEC-017 – 21 October 2025

- Forum: Design Authority (reserve synchronisation) – Design Authority
- Decided by: Tomasz Wójcik (Enterprise Architect)
- Decision: Replace CDC (ADR-005) with the CLX-IF-049 batch-to-event bridge (ADR-012, ADR-017).
- References:
    - ADR-012 – Batch-to-event bridge for the reserve movement extract (CLX-IF-049)
    - ADR-017 – Replace CDC with the batch bridge for reserve synchronisation
- Related: ADR-005 superseded; CLX-IF-049 went live on 12 December 2025.
- Source record: Minutes – Design Authority 21 Oct 2025
- Status: Approved. ADR-005 superseded by ADR-017.

### DEC-019 – 20 January 2026

- Forum: Not taken in a formal meeting (recorded by email / approval note)
- Decided by: Imran Talwar (Head of Claims Assessment (UK))
- Decision: Remove Fellgate Adjusting Partners from the assessor panel effective 2026-01-31; open instructions move to Brackenfield.
- References:
    - VEN-03 – Fellgate Adjusting Partners LLP
- Source record: Approval email held by the PMO
- Status: Approved.

### DEC-018 – 3 February 2026

- Forum: Design Authority (reserve-engine rename) – Design Authority
- Decided by: Tomasz Wójcik (Enterprise Architect)
- Decision: Rename reserve-svc to reserve-engine effective 2026-02-10 (ADR-019).
- References:
    - ADR-019 – Rename reserve-svc to reserve-engine
    - CHUB-233 – Rename reserve-svc to reserve-engine (repo path, namespace labels, Terraform module) per ADR-019
- Related: Rename tracked as CHUB-233.
- Source record: Minutes – Design Authority 3 Feb 2026
- Status: Approved.

### DEC-005 – 5 March 2026

- Forum: Reserving design review (reserve-engine) – Design Authority
- Decided by: Lena Kristiansen (Head of Reserving); Daniel Achebe (Engineering Lead – Reserve & Finance Squad)
- Decision: reserve-engine will record currency revaluations as RV movements, closing audit finding IA-25-07 in the target; CLRGL090 stays unchanged in CLARA.
- References:
    - ADR-028 – Use the reserve-engine revaluation run instead of CLRGL090 from Wave 2
    - CHUB-284 – Internal audit IA-25-07: CLRGL090 revaluation writes no reserve movement
- Related: Taken at the same reserving design review as DEC-006.
- Source record: Transcript – Reserving Design Review 5 Mar 2026
- Status: Approved.

### DEC-006 – 5 March 2026

- Forum: Reserving design review (reserve-engine) – Design Authority
- Decided by: Lena Kristiansen (Head of Reserving)
- Decision: Propose a 14-day Tier-3 reserve review cadence from 2026-07-01 to the Reserving Committee.
- References:
    - BR-RSV-007 – Tier-3 reserve review cadence
- Related: Approved by the Reserving Committee as DEC-008.
- Source record: Transcript – Reserving Design Review 5 Mar 2026
- Status: Closed – approved by the Reserving Committee as DEC-008.

### DEC-007 – 12 March 2026

- Forum: Claims Fraud Forum (Circular 2026/04 rules) – Claims Fraud Forum
- Decided by: Niall Brannigan (Head of Counter-Fraud & SIU); Ingrid Ashby (Claims Director)
- Decision: Approve BR-FRD-031 v1, BR-FRD-032 v2, BR-FRD-033, BR-FRD-034, BR-FRD-035 v2 and BR-FRD-036 v1 effective 2026-04-01.
- References:
    - BR-FRD-031 – Fraud referral threshold (NISA Circular 2026/04)
    - BR-FRD-032 – Customer notification of fraud referral
    - BR-FRD-033 – No adverse decision on fraud score alone
- Related: BR-FRD-031 and BR-FRD-036 were revised by DEC-014 and DEC-015.
- Source record: Minutes – Claims Fraud Forum 12 Mar 2026
- Status: Approved. BR-FRD-031 v1 and BR-FRD-036 v1 were later superseded by v2 (DEC-014, DEC-015).

### DEC-008 – 9 June 2026

- Forum: Reserving Committee (June 2026) – Reserving Committee
- Decided by: Lena Kristiansen (Head of Reserving)
- Decision: Approve the 14-day Tier-3 reserve review cadence (BR-RSV-007 v3) effective 2026-07-01.
- References:
    - BR-RSV-007 – Tier-3 reserve review cadence
- Related: Implements the proposal in DEC-006.
- Source record: Minutes – Reserving Committee 9 Jun 2026
- Status: Approved.

### DEC-009 – 11 September 2026

- Forum: Wave 1 go/no-go – Programme Skerry Steering Committee
- Decided by: Duncan Ferrier (Chief Operating Officer)
- Decision: Go decision for Wave 1 (UK motor) cut-over on 2026-09-14; freeze 2026-09-11 18:00 to 2026-09-14 06:00.
- References:
    - MW-1 – Wave 1 – UK motor
- Related: Wave 1 cut-over went ahead on 14 September 2026.
- Source record: Minutes – Wave 1 Go/No-Go
- Status: Approved.

### DEC-014 – 17 September 2026

- Forum: Fraud Rules Workshop – Claims Fraud Forum
- Decided by: Niall Brannigan (Head of Counter-Fraud & SIU); Ingrid Ashby (Claims Director)
- Decision: From 2026-10-01 refer Tier-3 claims to SIU at a Sentinel score of 60 or more (general threshold stays 65).
- References:
    - BR-FRD-031 – Fraud referral threshold (NISA Circular 2026/04)
- Related: Revises BR-FRD-031 v1 (approved under DEC-007).
- Source record: Transcript – Fraud Rules Workshop 17 Sep 2026; Minutes – Fraud Rules Workshop (17 Sep 2026)
- Status: Approved.

### DEC-015 – 17 September 2026

- Forum: Fraud Rules Workshop – Claims Fraud Forum
- Decided by: Niall Brannigan (Head of Counter-Fraud & SIU); Ingrid Ashby (Claims Director)
- Decision: From 2026-10-01 customer-notice deferrals beyond 30 days need the Head of Counter-Fraud & SIU, and Compliance is notified the same day.
- References:
    - BR-FRD-036 – Deferral of customer notice (tipping-off risk)
- Related: Revises BR-FRD-036 v1 (approved under DEC-007).
- Source record: Transcript – Fraud Rules Workshop 17 Sep 2026; Minutes – Fraud Rules Workshop (17 Sep 2026)
- Status: Approved.

### DEC-016 – 17 September 2026

- Forum: Fraud Rules Workshop – Claims Fraud Forum
- Decided by: Niall Brannigan (Head of Counter-Fraud & SIU)
- Decision: Option to lower the general referral threshold to 60 for all claims rejected.
- References:
    - BR-FRD-031 – Fraud referral threshold (NISA Circular 2026/04)
- Related: Considered at the same workshop as DEC-014 and DEC-015.
- Source record: Transcript – Fraud Rules Workshop 17 Sep 2026; Minutes – Fraud Rules Workshop (17 Sep 2026)
- Status: Approved.

### DEC-010 – 8 October 2026

- Forum: Programme Skerry Steering Committee (October 2026) – Programme Skerry Steering Committee
- Decided by: Priya Raman (Chief Financial Officer); Duncan Ferrier (Chief Operating Officer)
- Decision: Approve a contingency drawdown of £1.8m for Wave 2 (approved by the CFO, Priya Raman).
- References: none recorded
- Related: Taken at the same Steering Committee as DEC-011.
- Source record: Transcript – Programme Skerry Steering Committee 8 Oct 2026
- Status: Approved.

### DEC-011 – 8 October 2026

- Forum: Programme Skerry Steering Committee (October 2026) – Programme Skerry Steering Committee
- Decided by: Duncan Ferrier (Chief Operating Officer)
- Decision: Wave 2 cut-over date confirmed as 2027-02-15 (an earlier draft date of 2027-01-18 is void).
- References:
    - MW-2 – Wave 2 – UK home, commercial, liability; Norway; Sweden
- Source record: Transcript – Programme Skerry Steering Committee 8 Oct 2026
- Status: Approved. Cut-over planned for 15 February 2027.

## Change control

Additions are made by the PMO after each forum. Corrections to an entry require the agreement of the forum chair and are noted in the document control table.

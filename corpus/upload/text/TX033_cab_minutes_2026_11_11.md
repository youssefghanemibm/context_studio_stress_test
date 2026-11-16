# Change Advisory Board (CAB) – Minutes

| | |
|---|---|
| **Date** | Wednesday 11 November 2026 |
| **Time** | 11:00–11:45 |
| **Chair** | Neil Haworth, Head of Technology Delivery |
| **Location** | Wharfedge Room, Aire Point (Leeds), in person and on video |
| **Status** | Final |

## Attendees

| Name | Role | Organisation |
|---|---|---|
| Neil Haworth | Head of Technology Delivery (Chair) | Corvane Mutual |
| Graham Pocock | Head of Legacy Claims Platforms | Corvane Mutual |
| Sunita Vaghela | Batch Operations Lead | Corvane Mutual |
| Henrik Vestergaard | Integration Platform Lead | Corvane Mutual |
| Daniel Achebe | Engineering Lead – Reserve & Finance Squad | Corvane Mutual |
| Linnea Sjöberg | Engineering Lead – Fraud & Settlement Squad | Corvane Mutual |
| Tariq Hussain | Engineering Lead – Recoveries & Documents Squad | Corvane Mutual |

Tariq Hussain attended for the first time as Engineering Lead of the Recoveries & Documents squad, formed on 1 November 2026.

## 1. Previous actions

Open actions were reviewed; status is shown in the action log at the end of these minutes.

## 2. Change list – release R2026.11

The CAB reviewed release R2026.11, proposed for implementation on Thursday 12 November 2026. The release contains three changes:

| Ticket | Component | Change | Assignee | Risk |
|---|---|---|---|---|
| CHUB-298 | CLARA | CLRFR040 batch sweep referral threshold fix (INC-2026-0518) | Keith Barraclough | Medium |
| CHUB-415 | Platform | CODEOWNERS update (repository ownership file; no runtime impact) | Tariq Hussain | Low |
| CHUB-421 | notification-svc | notification-svc: emit an event when a fraud-referral notice is sent so fraud-referral-svc can close notice deadlines | Tariq Hussain | Low |


Discussion:

- Graham Pocock confirmed that CHUB-298 has been in review since 4 November and that the batch sweep fix closes the gap behind INC-2026-0518. The daily Compliance query stays in place until Compliance confirms the first batch run after release.
- Sunita Vaghela confirmed the CLARA deployment fits the normal batch schedule and needs no special handling by Batch Operations.
- Linnea Sjöberg and Tariq Hussain confirmed the Claims Hub changes were tested in the integration environment and have a standard rollback.
- Henrik Vestergaard and Daniel Achebe raised no concerns for their platforms.

Decision: the CAB approved release R2026.11 for implementation on 12 November 2026, comprising CHUB-298 (CLRFR040), CHUB-415 (CODEOWNERS) and CHUB-421 (notification topic).

## 3. Forward schedule of change

The Wave 2 freeze, from 18:00 on 12 February 2027 to 06:00 on 15 February 2027, is in the change calendar. No other freeze periods were added this week.

## 4. Emergency changes and post-implementation reviews

No emergency changes were raised since the last CAB. No post-implementation reviews were due.

## 5. Any other business

No items of other business were tabled.

There being no further business the meeting closed at 11:45.

## Actions

| # | Action | Owner | Due | Status |
|---|---|---|---|---|
| CAB-1 | Implement R2026.11 and confirm completion to the CAB mailbox | Graham Pocock / Tariq Hussain | 12 Nov 2026 | Open |
| CAB-2 | Confirm the first CLRFR040 batch run after release with Compliance | Graham Pocock | 13 Nov 2026 | Open |

## Change records reviewed

- CHUB-298 (Bug, component CLARA) – fix version R2026.11; status at CAB: In Review; raised 13 May 2026.
- CHUB-415 (Task, component Platform) – fix version R2026.11; status at CAB: Open; raised 2 November 2026.
- CHUB-421 (Story, component notification-svc) – fix version R2026.11; status at CAB: In Progress; raised 26 October 2026.

## Abbreviations

| Term | Meaning |
|---|---|
| CAB | Change Advisory Board |
| CHUB | Jira project key for Claims Hub |
| CLARA | Claims Ledger And Reserve Application (legacy mainframe claims system) |

## Distribution

- Neil Haworth (Head of Technology Delivery)
- Graham Pocock (Head of Legacy Claims Platforms)
- Sunita Vaghela (Batch Operations Lead)
- Henrik Vestergaard (Integration Platform Lead)
- Daniel Achebe (Engineering Lead – Reserve & Finance Squad)
- Linnea Sjöberg (Engineering Lead – Fraud & Settlement Squad)
- Tariq Hussain (Engineering Lead – Recoveries & Documents Squad)
- CAB mailbox
- Service desk (for the change calendar)

# Wave 1 Retrospective

| | |
|---|---|
| **Date** | Friday 25 September 2026 |
| **Facilitator** | Arjun Kesavan, Programme Delivery Lead (IBM Consulting) |
| **Format** | What went well / What went wrong / What we will change / Actions |
| **Scope** | Wave 1 – UK motor cut-over, rehearsals and first two weeks of hypercare |
| **Status** | Final |

## Contributors

- Aisha Siddiqui – Head of Claims Hub Product (Corvane)
- Callum Fairbairn – Data Migration Lead (IBM)
- Graham Pocock – Head of Legacy Claims Platforms (Corvane)
- Sunita Vaghela – Batch Operations Lead (Corvane)
- Linnea Sjöberg – Engineering Lead – Fraud & Settlement Squad (Corvane)
- Daniel Achebe – Engineering Lead – Reserve & Finance Squad (Corvane)
- Sofie Bak – Engineering Lead – Intake & Triage Squad (Corvane)
- Neil Haworth – Head of Technology Delivery (Corvane)
- Callum Fairbairn – Motor Claims Team Leader (Corvane)
- Alun Prothero – Payments Operations Manager (Corvane)

Note: two contributors share the name Callum Fairbairn – one is IBM's Data Migration Lead, the other
leads the Motor Claims team in Leeds. Comments are attributed by role below.

## Context

Wave 1 moved UK motor (PRD-MOT-UK) from CLARA to Claims Hub on 14 September 2026, after three
rehearsals and a freeze from 18:00 on 11 September to 06:00 on 14 September. The reserve parallel
run between CLARA and reserve-engine had ended on 28 August 2026.

## Cut-over weekend at a glance

| When | What |
|---|---|
| Fri 11 Sep 2026, 16:00 | Go/no-go: GO given by the Steering Committee |
| Fri 11 Sep 2026, 18:00 | Freeze starts in CLARA and Claims Hub |
| Sat 12 – Sun 13 Sep | Migration run, reconciliation and business verification |
| Mon 14 Sep 2026, 06:00 | Freeze ends; UK motor handled in Claims Hub |
| Mon 14 Sep 2026, 09:20 | INC-2026-0914 opened (duplicate payment instructions) |
| Mon 14 Sep 2026, 15:45 | INC-2026-0914 resolved for new payments |
| Wed 16 Sep 2026 | CHUB-371 fix released |
| Fri 18 Sep 2026 | All duplicate payments recalled |


## What went well

- The freeze held: no unplanned production changes went into CLARA or Claims Hub during the window.
- Rehearsals paid off – the cut-over steps ran in the rehearsed order, and the migration lead's
  reconciliation approach was reused unchanged on the night.
- The parallel run gave Finance and Reserving confidence in reserve-engine before go-live.
- Floor-walkers in Leeds were visible from the first morning and handlers knew where to go for help.
- The hypercare daily call kept issues short and well owned.
- Batch Operations and the Legacy Claims Platforms team closed the CLARA side cleanly.

## What went wrong

- Duplicate payments on cut-over day: 18 claims were paid twice, totalling £41,236.50
  (INC-2026-0914). payment-orchestrator retried on a Corvane Payments Gateway timeout without an
  idempotency key.
- The fix (CHUB-371) was released on 16 September and all duplicate payments were recalled by 18
  September, but Payments Operations spent two days on manual recalls.
- The cut-over bridge was noisy: too many people on one call made decisions slower than they needed
  to be.
- Some handler questions on the first morning were about work queues rather than the system itself;
  the briefing material had not covered queue changes in enough depth.
- Status updates to the wider business were later than planned on the Sunday afternoon.

## What we will change for Wave 2

Wave 2 is planned for 15 February 2027 and covers UK home, commercial and liability plus Norway and
Sweden. Changes agreed:

- Idempotency to be confirmed for every payment path as an explicit go/no-go criterion.
- A smaller decision bridge with workstream leads only, and a separate information call for everyone
  else.
- Handler briefings to include work-queue walkthroughs, with the Nordic teams' feedback built in
  early.
- A fixed schedule for business updates during the cut-over weekend.

## Actions

| # | Action | Owner | Due | Status |
|---|---|---|---|---|
| R1 | Add payment idempotency evidence to the Wave 2 go/no-go criteria | Arjun Kesavan | 16 Oct 2026 | Open |
| R2 | Review all payment-orchestrator retry paths | Linnea Sjöberg | 23 Oct 2026 | Open |
| R3 | Redesign the cut-over bridge structure | Neil Haworth | 30 Oct 2026 | Open |
| R4 | Extend handler briefings with work-queue walkthroughs | Aisha Siddiqui | 13 Nov 2026 | Open |

## Thanks

The facilitator thanked everyone who worked the cut-over weekend, the Leeds motor team for their
patience on the first morning, and Payments Operations for the recall work.

## Distribution

- Aisha Siddiqui (Head of Claims Hub Product)
- Callum Fairbairn (Data Migration Lead)
- Graham Pocock (Head of Legacy Claims Platforms)
- Sunita Vaghela (Batch Operations Lead)
- Linnea Sjöberg (Engineering Lead – Fraud & Settlement Squad)
- Daniel Achebe (Engineering Lead – Reserve & Finance Squad)
- Sofie Bak (Engineering Lead – Intake & Triage Squad)
- Neil Haworth (Head of Technology Delivery)
- Callum Fairbairn (Motor Claims Team Leader)
- Alun Prothero (Payments Operations Manager)
- Programme Skerry Steering Committee members
- Wave 2 workstream leads

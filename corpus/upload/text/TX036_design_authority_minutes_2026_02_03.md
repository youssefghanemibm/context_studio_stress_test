# Design Authority – Minutes

| | |
|---|---|
| **Date** | Tuesday 3 February 2026 |
| **Time** | 15:00–16:00 |
| **Chair** | Tomasz Wójcik, Enterprise Architect |
| **Location** | Room 2.14, Corvane House, in person and on video |
| **Status** | Final |

## Attendees

| Name | Role | Organisation |
|---|---|---|
| Tomasz Wójcik | Enterprise Architect (Chair) | Corvane Mutual |
| Daniel Achebe | Engineering Lead – Reserve & Finance Squad | Corvane Mutual |
| Nadia Petrovic | Java Technical Lead | IBM Consulting |
| Elin Fosse | Lead Solution Architect | IBM Consulting |

Apologies were received from Marcus Oduya, Henrik Vestergaard and Graham Pocock.

## 1. ADR-019 – Rename reserve-svc to reserve-engine

Daniel Achebe presented ADR-019, which renames reserve-svc to reserve-engine. The ADR's
consequences, effective 10 February 2026, are: repository path services/reserve-engine, Terraform
module reserve-engine, and the event reserve.changed.v2.

In discussion:

- Nadia Petrovic confirmed the coding standards and service templates will be updated in the same
  change.
- Elin Fosse asked that architecture diagrams and the service catalogue use the new name from the
  effective date, with the old name noted as an alias.
- The rename work is tracked as CHUB-233, assigned to Daniel Achebe.

Decision: the Design Authority approved the rename of reserve-svc to reserve-engine, effective 10
February 2026 (ADR-019).

## 2. Reserve parallel run – architecture readiness

Elin Fosse summarised readiness for the reserve parallel run planned from 2 March 2026. Under
ADR-012, CLX-IF-042 records are republished to claims.reserve.movement.v1 by the CLX-IF-049 bridge,
and the service consumes them for the parallel run and, later, for Wave 2 synchronisation.

In discussion the following points were made:

- The group noted the dependency on testing being completed and signed off before the change goes
  live.
- It was agreed that communications to affected teams should be issued in plain language and in good
  time.

## 3. ADR register housekeeping

The chair asked owners of proposed ADRs older than two months to confirm whether they are still
active. The register will be reviewed again at the next Design Authority.

## 4. Any other business

No other business was raised.

The chair thanked attendees and closed the meeting at 16:00.

## Actions

| # | Action | Owner | Due | Status |
|---|---|---|---|---|
| DA-02-1 | Complete the rename under CHUB-233 for 10 February | Daniel Achebe | 10 Feb 2026 | Open |
| DA-02-2 | Update architecture diagrams and the service catalogue | Elin Fosse | 13 Feb 2026 | Open |
| DA-02-3 | Update service templates and coding standards | Nadia Petrovic | 13 Feb 2026 | Open |

## ADRs referred to

- ADR-019 – Rename reserve-svc to reserve-engine (accepted, 3 February 2026)
- ADR-012 – Batch-to-event bridge for the reserve movement extract (CLX-IF-049) (accepted, 21
  October 2025)
- ADR-017 – Replace CDC with the batch bridge for reserve synchronisation (accepted, 21 October
  2025)

## Abbreviations

| Term | Meaning |
|---|---|
| ADR | Architecture Decision Record |
| CLARA | Claims Ledger And Reserve Application (legacy mainframe claims system) |
| CHUB | Jira project key for Claims Hub |

## Distribution

- Tomasz Wójcik (Enterprise Architect)
- Daniel Achebe (Engineering Lead – Reserve & Finance Squad)
- Nadia Petrovic (Java Technical Lead)
- Elin Fosse (Lead Solution Architect)
- Marcus Oduya (Integration Architect)
- Henrik Vestergaard (Integration Platform Lead)
- Graham Pocock (Head of Legacy Claims Platforms)
- Architecture team

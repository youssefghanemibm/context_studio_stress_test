# Design Authority – Minutes

| | |
|---|---|
| **Date** | Tuesday 21 October 2025 |
| **Time** | 15:00–16:00 |
| **Chair** | Tomasz Wójcik, Enterprise Architect |
| **Location** | Room 4.12, Corvane House, video call |
| **Status** | Final |

## Attendees

| Name | Role | Organisation |
|---|---|---|
| Tomasz Wójcik | Enterprise Architect (Chair) | Corvane Mutual |
| Marcus Oduya | Integration Architect | IBM Consulting |
| Henrik Vestergaard | Integration Platform Lead | Corvane Mutual |
| Derek Ollerton | DB2 Database Administrator | Corvane Mutual |
| Elin Fosse | Lead Solution Architect | IBM Consulting |

Apologies were received from Graham Pocock and Daniel Achebe.

## 1. Previous actions

The action log was reviewed. Closed items have been removed; carried-forward items are listed below.

## 2. Reserve synchronisation approach

Marcus Oduya presented the options for keeping reserve-svc in step with CLARA reserves during the parallel run and up to Wave 2. ADR-005 (10 March 2025) proposed change data capture on CLR.T_RESERVE_MOVEMENT. Analysis since then showed that CDC on that table is incomplete, because CLRGL090 updates bypass the movement table.

The proposed replacement is the CLX-IF-049 batch-to-event bridge (ADR-012): CLX-IF-042 records are republished to the Kafka topic claims.reserve.movement.v1, and reserve-svc consumes them for the parallel run and Wave 2 synchronisation. ADR-017 records the replacement of CDC.

In discussion:

- Derek Ollerton agreed that the CDC design could not see changes made outside the movement table and supported withdrawing it.
- Henrik Vestergaard confirmed the Integration Platform team will own the bridge alongside CLX-IF-042.
- Elin Fosse asked that the reconciliation design for the parallel run is reviewed once the bridge is built.

Decision: the Design Authority approved replacing CDC (ADR-005) with the CLX-IF-049 batch-to-event bridge (ADR-012, ADR-017). ADR-005 is marked superseded by ADR-017.

## 3. Interface catalogue standards

Henrik Vestergaard proposed that new interface entries record owner, criticality and dependencies before they are approved. Members agreed; the template will be updated.

## 4. Any other business

There was no other business.

There being no further business the meeting closed at 16:00.

## Actions

| # | Action | Owner | Due | Status |
|---|---|---|---|---|
| DA-10-1 | Update ADR-005 status to superseded and publish ADR-012 and ADR-017 | Tomasz Wójcik | 24 Oct 2025 | Open |
| DA-10-2 | Produce the CLX-IF-049 bridge design for review | Marcus Oduya | 4 Nov 2025 | Open |
| DA-10-3 | Update the interface catalogue template | Henrik Vestergaard | 4 Nov 2025 | Open |

## ADRs referred to

- ADR-005 – Change data capture from DB2 for reserve synchronisation (superseded by ADR-017 at this meeting)
- ADR-012 – Batch-to-event bridge for the reserve movement extract (CLX-IF-049) (accepted at this meeting)
- ADR-017 – Replace CDC with the batch bridge for reserve synchronisation (accepted at this meeting)

## Abbreviations

| Term | Meaning |
|---|---|
| ADR | Architecture Decision Record |
| CDC | Change data capture |
| CLARA | Claims Ledger And Reserve Application (legacy mainframe claims system) |

## Distribution

- Tomasz Wójcik (Enterprise Architect)
- Marcus Oduya (Integration Architect)
- Henrik Vestergaard (Integration Platform Lead)
- Derek Ollerton (DB2 Database Administrator)
- Elin Fosse (Lead Solution Architect)
- Graham Pocock (Head of Legacy Claims Platforms)
- Daniel Achebe (Engineering Lead – Reserve & Finance Squad)
- Architecture team

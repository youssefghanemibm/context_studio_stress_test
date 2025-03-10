# Corvane Claims Platform monorepo

This repository holds both halves of Programme Skerry: the CLARA mainframe sources that are
being retired and the Claims Hub services that replace them (ADR-001, strangler-fig migration).

| Path | Contents |
|---|---|
| `legacy/clara/` | CLARA (Claims Ledger And Reserve Application): COBOL programs, copybooks, JCL, BMS maps and DB2 DDL |
| `services/` | Claims Hub services (Java 21, Spring Boot), one Maven module per service |
| `infra/terraform/` | Terraform modules, one per service (ADR-007), and the `envs/prod` root |
| `deploy/k8s/` | OpenShift manifests, one folder per namespace |
| `api/openapi/` | OpenAPI descriptions of the service REST APIs |
| `docs/adr/` | Architecture decision records |
| `docs/diagrams/` | Event-flow and sequence diagrams |

## Claims Hub services

| Service | Namespace | Status | Go-live |
|---|---|---|---|
| `claim-core-svc` | `chub-core` | live | 2025-11-03 |
| `fnol-intake-svc` | `chub-intake` | live | 2025-11-03 |
| `triage-svc` | `chub-intake` | live | 2025-11-03 |
| `assessment-svc` | `chub-assess` | live | 2026-09-14 |
| `reserve-svc` | `chub-reserve` | live | 2026-09-14 |
| `fraud-referral-svc` | `chub-fraud` | live | 2026-04-01 |
| `settlement-svc` | `chub-settle` | live | 2026-09-14 |
| `payment-orchestrator` | `chub-settle` | live | 2026-09-14 |
| `recovery-svc` | `chub-recovery` | live | 2026-09-14 |
| `document-svc` | `chub-docs` | live | 2025-11-03 |
| `notification-svc` | `chub-notify` | live | 2025-11-03 |
| `gl-posting-svc` | `chub-finance` | live | 2026-09-14 |
| `reporting-feed-svc` | `chub-finance` | in development | 2027-01-11 |

Services exchange domain events on the Event Streaming Platform (cluster `esp-prd`); topic names
follow `<domain>.<event>.v<n>` (ADR-002). Each service owns its PostgreSQL database (ADR-003).

## Building

Run `make build` from the repository root. Java 21 and
Maven 3.9 are required; `make help` lists the other targets.

## Documentation

- Architecture decisions: [docs/adr](docs/adrs/)
- Diagrams: [docs/diagrams](docs/diagram/)
- Code owners: [.github/CODEOWNERS](.github/CODEOWNERS)

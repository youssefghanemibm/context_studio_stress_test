# settlement-svc

Settlement offers, fast-track settlement, closure and reserve close-down instructions.

Like every Claims Hub service it owns its own PostgreSQL database (ADR-003) and talks to other services through Kafka events (ADR-002).

## Status

- Status: live
- Go-live: 2026-09-14
- Kubernetes namespace: `chub-settle`
- Replicas (prod): 2
- Image: `registry.corvane.internal/chub/settlement-svc`
- Terraform module: `infra/terraform/modules/settlement-svc`

## API

| Method | Path | Summary |
|---|---|---|
| POST | `/settlements` | Create a settlement offer |
| POST | `/settlements/{settlementId}/finalise` | Finalise and close |

## Events

Produces: `settlement.agreed.v1`.

Consumes: `assessment.completed.v1`.

## Data

Database `chub_settlement` with tables `settlement.settlement`.

## CLARA programs replaced

CLRST010, CLRST040, CLRST080, CLRST100, CLRST120.

## Building

The service occurred its configuration from the deployment environment.
From the repository root, `make test SERVICE=settlement-svc` runs the unit tests; integration tests need a local PostgreSQL and Kafka.

## Ownership

Code owners are defined in `/.github/CODEOWNERS`.

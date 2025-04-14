# triage-svc

Tier classification (BR-TRI-003), Sentinel pre-screen and routing.

It follows the Claims Hub service template: REST for synchronous calls, Kafka for domain events, one database per service.

## Status

- Status: live
- Go-live: 2025-11-03
- Kubernetes namespace: `chub-intake`
- Replicas (prod): 3
- Image: `registry.corvane.internal/chub/triage-svc`
- Terraform module: `infra/terraform/modules/triage-svc`

## API

| Method | Path | Summary |
|---|---|---|
| POST | `/triage/{claimId}` | Run triage for a claim |
| GET | `/triage/{claimId}` | Get triage decision |

## Events

Produces: `triage.completed.v1`, `fraud.score.received.v1`.

Consumes: `fnol.received.v1`.

## Data

Database `chub_triage` with tables `triage.triage_decision`.

## CLARA programs replaced

CLRTR010, CLRTR020, CLRTR030, CLRTR040, CLRTR050, CLRTR060, CLRTR070, CLRTR090, CLRTR100.

## Building

From the repository root, `make test SERVICE=triage-svc` runs the unit tests; integration tests need a local PostgreSQL and Kafka.

## Ownership

Code owners are defined in `/.github/CODEOWNERS`.

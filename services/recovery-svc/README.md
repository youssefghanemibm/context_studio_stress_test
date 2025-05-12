# recovery-svc

Subrogation cases, salvage and recovery receipts; replaces SUBTRAK.

The service is a Spring Boot application packaged as a container image and deployed to OpenShift.

## Status

- Status: live
- Go-live: 2026-09-14
- Kubernetes namespace: `chub-recovery`
- Replicas (prod): 2
- Image: `registry.corvane.internal/chub/recovery-svc`
- Terraform module: `infra/terraform/modules/recovery-svc`

## API

| Method | Path | Summary |
|---|---|---|
| POST | `/recoveries` | Open a recovery / subrogation case |
| POST | `/recoveries/{caseId}/receipts` | Record a receipt |
| POST | `/recoveries/{caseId}/write-off` | Write off (approval above £10,000 by Head of Recoveries & Subrogation) |

## Events

Produces: `recovery.receipt.v1`.

Consumes: `settlement.agreed.v1`.

## Data

Database `chub_recovery` with tables `recovery.recovery_case`, `recovery.receipt`.

## CLARA programs replaced

CLRRC010, CLRRC020, CLRRC040, CLRRC050, CLRRC060, CLRRC070, CLRRC080, CLRRC090.

## Building

From the repository root, `make test SERVICE=recovery-svc` runs the unit tests; integration tests need a local PostgreSQL and Kafka.

## Ownership

Code owners are defined in `/.github/CODEOWNERS`.

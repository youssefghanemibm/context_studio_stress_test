# reserve-svc

Case reserves, reserve movements, Tier-3 review scheduling, indexation and currency revaluation.

It follows the Claims Hub service template: REST for synchronous calls, Kafka for domain events, one database per service.

## Status

- Status: live
- Go-live: 2026-09-14
- Kubernetes namespace: `chub-reserve`
- Replicas (prod): 4
- Image: `registry.corvane.internal/chub/reserve-svc`
- Terraform module: `infra/terraform/modules/reserve-svc`

## API

| Method | Path | Summary |
|---|---|---|
| GET | `/reserves/{claimId}` | Get current reserves for a claim |
| POST | `/reserves/{claimId}/movements` | Post a reserve movement (authority checked against BR-RSV-003) |
| GET | `/reserves/{claimId}/history` | Reserve movement history |

## Events

Produces: `reserve.changed.v1`.

Consumes: `claims.reserve.movement.v1`, `triage.completed.v1`.

## Data

Database `chub_reserve` with tables `reserve.reserve`, `reserve.reserve_movement`, `reserve.review_schedule`.

## CLARA programs replaced

CLRFN030, CLRGL090, CLRRS010, CLRRS015, CLRRS020, CLRRS030, CLRRS040, CLRRS110, CLRRS120, CLRRS130, CLRRS140, CLRRS150, CLRRS160, CLRRS170, CLRRS180, CLRRS200.

## Building

Run `make build SERVICE=reserve-svc` from the repository root, or `mvn -pl services/reserve-svc verify` if you prefer Maven directly.

## Ownership

Code owners are defined in `/.github/CODEOWNERS`.

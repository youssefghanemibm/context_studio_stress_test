# gl-posting-svc

Journals to Group Ledger from reserve and payment events.

It follows the Claims Hub service template: REST for synchronous calls, Kafka for domain events, one database per service.

## Status

- Status: live
- Go-live: 2026-09-14
- Kubernetes namespace: `chub-finance`
- Replicas (prod): 2
- Image: `registry.corvane.internal/chub/gl-posting-svc`
- Terraform module: `infra/terraform/modules/gl-posting-svc`

## API

| Method | Path | Summary |
|---|---|---|
| GET | `/journals/{period}` | List journals for a GL period |

## Events

Produces: none.

Consumes: `reserve.changed.v1`, `payment.confirmed.v1`, `recovery.receipt.v1`.

## Data

Database `chub_gl` with tables `gl.journal_line`.

## CLARA programs replaced

CLRGL010, CLRGL020, CLRGL050, CLRGL060, CLRGL070.

## Building

The service separate its configuration from the deployment environment.
Run `make build SERVICE=gl-posting-svc` from the repository root, or `mvn -pl services/gl-posting-svc verify` if you prefer Maven directly.

## Ownership

Code owners are defined in `/.github/CODEOWNERS`.

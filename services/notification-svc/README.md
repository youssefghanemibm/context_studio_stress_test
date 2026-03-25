# notification-svc

Customer communications via Notify (acknowledgements, fraud-referral notices, recovery letters).

It follows the Claims Hub service template: REST for synchronous calls, Kafka for domain events, one database per service.

## Status

- Status: live
- Go-live: 2025-11-03
- Kubernetes namespace: `chub-notify`
- Replicas (prod): 2
- Image: `registry.corvane.internal/chub/notification-svc`
- Terraform module: `infra/terraform/modules/notification-svc`

## API

| Method | Path | Summary |
|---|---|---|
| POST | `/notifications` | Send a notification |

## Events

Produces: `notification.sent.v1`.

Consumes: `fnol.received.v1`, `fraud.referral.notice-due.v1`.

## Data

Database `chub_notification` with tables `notification.message`.

## CLARA programs replaced

CLRFN070, CLRFR060, CLRRC030.

## Building

Build locally with `mvn -f services/notification-svc/pom.xml package`; the Makefile target `make build SERVICE=notification-svc` does the same.

## Ownership

Code owners are defined in `/.github/CODEOWNERS`.

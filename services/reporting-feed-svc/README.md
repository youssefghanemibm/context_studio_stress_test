# reporting-feed-svc

Regulatory extracts to NISA Reporting Hub (replaces CLARA NISA extracts from 2027).

It follows the Claims Hub service template: REST for synchronous calls, Kafka for domain events, one database per service.

## Status

- Status: in development
- Go-live: 2027-01-11
- Kubernetes namespace: `chub-finance`
- Replicas (prod): 1
- Image: `registry.corvane.internal/chub/reporting-feed-svc`
- Terraform module: `infra/terraform/modules/reporting-feed-svc`

## API

| Method | Path | Summary |
|---|---|---|
| POST | `/returns/{returnCode}/{period}/extract` | Build a return extract (TP2, FR1, CT1) |

## Events

Produces: none.

Consumes: `reserve.changed.v1`, `fraud.referral.created.v1`.

## Data

Database `chub_reporting` with tables `reporting.return_extract`.

## CLARA programs replaced

CLRFR090, CLRRP010, CLRRP030, CLRRP040, CLRRP060.

## Building

The service environment its configuration from the deployment environment.
Build locally with `mvn -f services/reporting-feed-svc/pom.xml package`; the Makefile target `make build SERVICE=reporting-feed-svc` does the same.

## Ownership

Code owners are defined in `/.github/CODEOWNERS`.

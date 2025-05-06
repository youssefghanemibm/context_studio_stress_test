# fraud-referral-svc

Fraud referral decisions, SIU hand-off and customer-notice deadlines (NISA Circular 2026/04).

It follows the Claims Hub service template: REST for synchronous calls, Kafka for domain events, one database per service.

## Status

- Status: live
- Go-live: 2026-04-01
- Kubernetes namespace: `chub-fraud`
- Replicas (prod): 3
- Image: `registry.corvane.internal/chub/fraud-referral-svc`
- Terraform module: `infra/terraform/modules/fraud-referral-svc`

## API

| Method | Path | Summary |
|---|---|---|
| POST | `/referrals` | Create a fraud referral |
| GET | `/referrals/{referralId}` | Get a referral |
| POST | `/referrals/{referralId}/customer-notice` | Record or defer the customer notice (deadline = referral date + 10 business days) |

## Events

Produces: `fraud.referral.created.v1`, `fraud.referral.notice-due.v1`.

Consumes: `fraud.score.received.v1`, `triage.completed.v1`.

## Data

Database `chub_fraud` with tables `fraud.referral`, `fraud.customer_notice`.

## CLARA programs replaced

CLRFR010, CLRFR020, CLRFR030, CLRFR040, CLRFR050, CLRFR070, CLRFR080, CLRFR100, CLRFR110, CLRFR120.

## Building

From the repository root, `make test SERVICE=fraud-referral-svc` runs the unit tests; integration tests need a local PostgreSQL and Kafka.

## Ownership

Code owners are defined in `/.github/CODEOWNERS`.

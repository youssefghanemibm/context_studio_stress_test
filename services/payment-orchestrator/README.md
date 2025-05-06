# payment-orchestrator

Payment authorisation (BR-STL-002), sanctions screening and CPG instructions.

This module is part of the Claims Hub monorepo and is built and deployed independently.

## Status

- Status: live
- Go-live: 2026-09-14
- Kubernetes namespace: `chub-settle`
- Replicas (prod): 3
- Image: `registry.corvane.internal/chub/payment-orchestrator`
- Terraform module: `infra/terraform/modules/payment-orchestrator`

## API

| Method | Path | Summary |
|---|---|---|
| POST | `/payments` | Request a payment |
| POST | `/payments/{paymentId}/cancel` | Cancel a payment |

## Events

Produces: `payment.requested.v1`.

Consumes: `settlement.agreed.v1`, `payment.confirmed.v1`.

## Data

Database `chub_payment` with tables `payment.payment_instruction`.

## CLARA programs replaced

CLRAS070, CLRST020, CLRST030, CLRST050, CLRST060, CLRST070, CLRST090, CLRST110, CLRST140.

## Building

Run `make build SERVICE=payment-orchestrator` from the repository root, or `mvn -pl services/payment-orchestrator verify` if you prefer Maven directly.

## Ownership

Code owners are defined in `/.github/CODEOWNERS`.

# Runbook: payment-orchestrator

Namespace `chub-settle`, 3 replicas in production.

## Health

- Readiness: `/actuator/health/readiness` on each pod of `payment-orchestrator`
- Logs: `oc logs -n chub-settle deploy/payment-orchestrator --since=15m`

## Known situations

- Every instruction to the Corvane Payments Gateway carries an idempotency key (ADR-021); a retry after a timeout is safe.
- Before cancelling a payment, check its status in `payment.payment_instruction`.
- Duplicate-payment alerts are Sev2; follow the incident process used for INC-2026-0914.

## Restart

`oc rollout restart -n chub-settle deploy/payment-orchestrator` and watch `oc rollout status`.

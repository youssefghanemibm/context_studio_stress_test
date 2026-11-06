# Runbook: fraud-referral-svc

Namespace `chub-fraud`, 3 replicas in production.

## Health

- Readiness: `/actuator/health/readiness` on each pod of `fraud-referral-svc`
- Logs: `oc logs -n chub-fraud deploy/fraud-referral-svc --since=15m`

## Known situations

- Referral thresholds are effective-dated configuration (ADR-020); change them by pull request, never by editing the ConfigMap.
- Customer-notice deadlines are referral date plus 10 business days; check `fraud.customer_notice.due_date` when a complaint arrives.
- If SIU Case Manager is unavailable, referrals queue and are retried; do not re-create them by hand.

## Restart

`oc rollout restart -n chub-fraud deploy/fraud-referral-svc` and watch `oc rollout status`.

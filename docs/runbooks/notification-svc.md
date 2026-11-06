# Runbook: notification-svc

Namespace `chub-notify`, 2 replicas in production.

## Health

- Readiness: `/actuator/health/readiness` on each pod of `notification-svc`
- Logs: `oc logs -n chub-notify deploy/notification-svc --since=15m`

## Known situations

- Fraud-referral notices use Notify templates FRN01 (letter) and FRN02 (SMS).
- If Notify is degraded, notices are held and sent in order once it recovers; the due date does not move.
- Holiday calendars for UK, NO, SE and DK drive the business-day arithmetic.

## Restart

`oc rollout restart -n chub-notify deploy/notification-svc` and watch `oc rollout status`.

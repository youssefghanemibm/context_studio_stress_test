# Runbook: reserve-engine

Namespace `chub-reserve`, 4 replicas in production.

## Health

- Readiness: `/actuator/health/readiness` on each pod of `reserve-engine`
- Logs: `oc logs -n chub-reserve deploy/reserve-engine --since=15m`

## Known situations

- Consumer lag on `claims.reserve.movement.v1` usually means the bridge delivered a large batch; let it drain before restarting pods.
- The Tier-3 review cadence (`reserve.tier3-review-days`) must match CLARA's RSV_T3_REVIEW_DAYS in CLR.T_PARAM; a mismatch caused INC-2026-0702.
- A currency revaluation run is started with `POST /revaluation-runs`; every revaluation is posted as an RV movement.

## Restart

`oc rollout restart -n chub-reserve deploy/reserve-engine` and watch `oc rollout status`.

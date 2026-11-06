# Claim fixture index

`fixtures/claims/` holds 100 claim fixtures used by the triage, fraud-referral and
reserve contract tests. Every fixture records the triage input, a Sentinel score and the
expected outcome under the current rules (BR-TRI-003 v3 tiers; BR-FRD-031 v2 thresholds of
65, or 60 for Tier-3 claims scored from 2026-10-01). Fixtures contain no personal data.

## Canonical cases

Fixture claim CLM-SE-2026-004417 is the canonical Tier-3 frost-damage test case. It is built by the test
harness at start-up rather than stored here, because its reserve history is long.

## Counts

| Tier | Fixtures |
|---|---|
| Tier-1 | 27 |
| Tier-2 | 41 |
| Tier-3 | 32 |

25 fixtures are expected to be referred to SIU.

| Product | Fixtures |
|---|---|
| PRD-COM-UK | 10 |
| PRD-HOM-DK | 10 |
| PRD-HOM-NO | 10 |
| PRD-HOM-SE | 10 |
| PRD-HOM-UK | 10 |
| PRD-LIA-UK | 10 |
| PRD-MOT-DK | 10 |
| PRD-MOT-NO | 10 |
| PRD-MOT-SE | 10 |
| PRD-MOT-UK | 10 |

## Adding a fixture

Name new files `fx_<nnn>_<product>_<peril>.json`, keep the expected block in step with the
rule versions in force, and run `make test SERVICE=triage-svc` before opening a pull request.

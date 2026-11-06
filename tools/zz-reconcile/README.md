# zz-reconcile

Reconciliation tooling for the Wave 2 migration (UK home, commercial, liability; Norway; Sweden; planned 2027-02-15).

The Wave 2 reconciliation tool runs nightly at 05:40 and writes its differences to the table recon.daily_diff.

For every claim in scope it compares the outstanding case reserve held in CLARA
(`CLR.T_RESERVE.RSV_OUTSTANDING_AMT`) with the migrated reserve in Claims Hub
(`reserve.reserve.outstanding_amount`), in original currency and as a GBP equivalent.
A claim that exists on only one side is reported as a difference of its own kind.

## Scope

Products in Wave 2: PRD-HOM-UK, PRD-COM-UK, PRD-LIA-UK, PRD-MOT-NO, PRD-HOM-NO, PRD-MOT-SE, PRD-HOM-SE.

## Usage

```
python -m zz_reconcile --config config.yaml --business-date 2026-11-05
python -m zz_reconcile --config config.yaml --business-date 2026-11-05 --dry-run
```

`--dry-run` prints the differences instead of writing them. Tolerances are not hard-coded:
they are read from the run configuration agreed with the migration team.

## Layout

- `zz_reconcile/clara.py` reads the CLARA side (DB2 unload or the read replica)
- `zz_reconcile/hub.py` reads the Claims Hub side
- `zz_reconcile/compare.py` matches claims and classifies differences
- `zz_reconcile/report.py` writes differences and a run summary

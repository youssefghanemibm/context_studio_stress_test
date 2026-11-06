# Wave 2 dress rehearsal runbook

Wave 2 (UK home, commercial, liability; Norway; Sweden) is planned for 2027-02-15 with a migration freeze from
2027-02-12 18:00 to 2027-02-15 06:00. Dress rehearsals repeat the cut-over end to end on masked data (ADR-025).

## Schedule

Wave 2 dress rehearsal 2 is booked for 2027-01-23.

## Before the rehearsal

1. Confirm the masked data set has been refreshed and signed off by the data protection officer.
2. Scale the target services in the rehearsal environment to their production replica counts.
3. Check that the reserve bridge (CLX-IF-049) consumer group has no lag before the extract starts.
4. Announce the rehearsal window in the programme channel.

## During the rehearsal

1. Run the migration load for the Wave 2 products in scope: PRD-HOM-UK, PRD-COM-UK, PRD-LIA-UK, PRD-MOT-NO, PRD-HOM-NO, PRD-MOT-SE, PRD-HOM-SE.
2. Run the reconciliation tooling in `tools/zz-reconcile` against the rehearsal databases.
3. Record every manual step and its duration in the rehearsal log.

## After the rehearsal

1. Review the reconciliation differences with the migration lead.
2. Raise defects for every unexpected difference and link them to the rehearsal log.
3. Restore the rehearsal environment to its baseline.

# CLARA test data

Synthetic fixtures for unit and regression runs of the CLARA batch programs.

- `db2/<TABLE>.csv`: rows to load into a test copy of the `CLR` schema (one file per table;
  `CLR.T_PARAM` is not included - load `../ddl/T_PARAM_seed.sql` instead).
- `interfaces/`: sample interface records in display format.
- `expected/`: control-report totals expected from a run over the fixtures.
- `jcl/`: job streams that run single programs against the test schema.

All values are made up. Claim ids use the 2099 test range (`UK2099nnnnnn`) and personal
fields are masked, so no fixture row describes a real claim or person.


# CLARA coding standards (summary)

A short summary of the conventions the CLARA programs follow. It is meant for engineers
reading the code from the Claims Hub side; it does not replace the mainframe standards.

## Program structure

- Fixed-format COBOL: sequence numbers in columns 1-6, indicator in column 7, Area A from
  column 8, Area B from column 12, nothing beyond column 72 except change tags in 73-80.
- Paragraphs are numbered by phase: `0000` control, `1000` initialisation, `2000` main
  processing, `3000`-`5000` business steps, `6000` commit control, `7000` report lines,
  `8000` error handling, `9000` termination.
- Older programs use `PERFORM ... THRU ...-EXIT`; newer ones use in-line `PERFORM`.

## DB2

- Every `EXEC SQL` statement is followed by an `EVALUATE SQLCODE`; unexpected codes go to
  `8000-SQL-ERROR`, which formats the error (through `CLRCM050` where the program calls it).
- Host variables come from the table copybooks; columns keep the table order.
- Where a program changes a table it does not otherwise read and needs a value back (for example
  the reserve id for a movement row), it uses `SELECT ... FROM OLD TABLE (UPDATE ...)` or
  `FINAL TABLE` instead of a separate read.
- Batch programs commit at a fixed interval and declare their driving cursor `WITH HOLD`.

## Parameters and audit

- Business thresholds, cadences and caps are rows in `CLR.T_PARAM` with validity dates.
  Programs read them through `CLRCM040`; they must not be coded as constants.
- Data changes made on behalf of a user are recorded through `CLRCM020`.

## CICS

- Online programs are pseudo-conversational and keep state in the `CLRCOMM1` COMMAREA.
- Screen programs carry their symbolic map inline; keep it in step with `bms/`.


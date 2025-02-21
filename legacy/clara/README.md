# CLARA sources (legacy/clara)

CLARA (Claims Ledger And Reserve Application) is Corvane Mutual's mainframe claims system:
COBOL programs running under CICS (online) and as DB2 batch jobs.
This directory mirrors the mainframe source libraries so that the CLARA code can be read,
searched and reviewed next to the Claims Hub services.

> The mainframe libraries remain the system of record for builds and promotions.
> Changes made here must also go through the CLARA change process on the mainframe.

## Layout

| Path | Mainframe library type | Contents |
|---|---|---|
| `cobol/` | COBOL source | One member per program, `CLR` + area + 3 digits (e.g. `CLRRS170`). |
| `copybooks/` | COBOL copy library | Record layouts: DB2 host structures, COMMAREA, interface records. |
| `jcl/` | JCL library | One member per batch job; steps run programs under IKJEFT01 (DB2). |
| `bms/` | BMS map source | Mapsets for the 3270 screens; symbolic maps are kept inline in the programs. |
| `ddl/` | DB2 DDL | One file per `CLR.*` table, plus `T_PARAM_seed.sql`. |

## Program naming

Program names are `CLR` + a two-letter area code + a three-digit number:

- FN - first notice of loss (FNOL)
- TR - triage and tiering
- AS - assessment and Claims Assessor appointment
- RS - case reserves
- FR - fraud scoring and referral
- ST - settlement and payments
- RC - recoveries and subrogation
- GL - general ledger feeds
- RP - management and regulatory reporting
- CM - common subprograms (dates, audit, parameters, errors, MQ)

Online programs run as CICS transactions (four-character transaction ids such as `RS01`).
Batch programs run as steps of the jobs in `jcl/`. Subprograms in the CM area are called
statically and contain no CICS commands, so batch and online programs can share them.

## Conventions worth knowing

- Business parameters (thresholds, cadences, caps) live in `CLR.T_PARAM` with validity dates
  and are read through `CLRCM040`. See `ddl/T_PARAM_seed.sql` for the seeded rows.
- Audit rows are written through `CLRCM020`; DB2 errors are formatted by `CLRCM050`.
- Every table has a copybook with the same column order (see the header of each copybook).
- Columns 1-6 of COBOL members hold sequence numbers; changed lines may carry a change
  reference in columns 73-80.

## Building

The usual DB2 COBOL path applies: DB2 precompile (or the integrated coprocessor), CICS
translation for online programs, compile, link-edit and bind. Site symbols (high-level
qualifiers, DB2 subsystem and plan) come from the `CLRSYMS` include member and are not
stored in this repository.

# legacy-bridge

Small Spring Boot module that tells Claims Hub tooling when a CLARA extract has finished.
It is not deployed with the Claims Hub services; it runs alongside the reserve parallel run
and the Wave 2 synchronisation tooling and is removed when CLARA is decommissioned.

## What it does

legacy-bridge polls CLR.T_INTERFACE_LOG every 45 seconds for completed CLARA extract runs.
A run counts as completed when its `RUN_STATUS` is `OK`; runs in `ER` or `RR` are reported
as failed or rerun and are never forwarded. For each completed run the bridge records the
interface id, `RUN_TS`, `RECORD_COUNT` and `HASH_TOTAL`, and serves them on
`GET /extract-runs?interface=CLX-IF-042&since=<timestamp>`.

The record count and hash total let consumers check that they have read the whole extract
before they act on it. The bridge only reads `CLR.T_INTERFACE_LOG`; it never writes to DB2.

## Configuration

| Property | Meaning |
|---|---|
| `bridge.poll-interval` | How often the interface log is read (set per environment) |
| `bridge.interfaces` | Interface ids to watch, for example `CLX-IF-042` |
| `clara.db2.url` | JDBC URL of the CLARA DB2 subsystem (read-only user) |

## Running locally

`mvn -f services/legacy-bridge/pom.xml spring-boot:run -Dspring-boot.run.profiles=local`

A local profile points at the DB2 test copy used by the mainframe team; ask the CLARA
platform team for read access before running it.

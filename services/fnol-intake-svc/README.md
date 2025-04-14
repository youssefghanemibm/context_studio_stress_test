# fnol-intake-svc

First Notice of Loss intake from portal, app, contact centre, brokers and telematics.

This module is part of the Claims Hub monorepo and is built and deployed independently.

## Status

- Status: live
- Go-live: 2025-11-03
- Kubernetes namespace: `chub-intake`
- Replicas (prod): 4
- Image: `registry.corvane.internal/chub/fnol-intake-svc`
- Terraform module: `infra/terraform/modules/fnol-intake-svc`

## API

| Method | Path | Summary |
|---|---|---|
| POST | `/fnol` | Submit a first notice of loss |
| GET | `/fnol/{fnolId}` | Get FNOL status |

## Events

Produces: `fnol.received.v1`.

Consumes: `eig.evidence.received.v1`, `eig.telematics.alert.v1`.

## Data

Database `chub_fnol` with tables `fnol.notification`.

## CLARA programs replaced

CLRFN010, CLRFN015, CLRFN020, CLRFN040, CLRFN050, CLRFN060, CLRFN080, CLRFN100, CLRFN110, CLRFN130.

## Building

Run `make build SERVICE=fnol-intake-svc` from the repository root, or `mvn -pl services/fnol-intake-svc verify` if you prefer Maven directly.

## Ownership

Code owners are defined in `/.github/CODEOWNERS`.

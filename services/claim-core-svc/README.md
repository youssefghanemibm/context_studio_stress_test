# claim-core-svc

Claim aggregate (claim header, parties, status); system of record for migrated claims.

The service is a Spring Boot application packaged as a container image and deployed to OpenShift.

## Status

- Status: live
- Go-live: 2025-11-03
- Kubernetes namespace: `chub-core`
- Replicas (prod): 3
- Image: `registry.corvane.internal/chub/claim-core-svc`
- Terraform module: `infra/terraform/modules/claim-core-svc`

## API

| Method | Path | Summary |
|---|---|---|
| GET | `/claims/{claimId}` | Get a claim by reference (CLM-<region>-<yyyy>-<6 digits>) |
| POST | `/claims` | Create a claim from an FNOL |
| PATCH | `/claims/{claimId}` | Update claim status or attributes |

## Events

Produces: `claim.created.v1`, `claim.updated.v1`.

Consumes: `fnol.received.v1`, `notification.sent.v1`.

## Data

Database `chub_claim_core` with tables `claim_core.claim`, `claim_core.party`.

## CLARA programs replaced

CLRFN090.

## Building

Build locally with `mvn -f services/claim-core-svc/pom.xml package`; the Makefile target `make build SERVICE=claim-core-svc` does the same.

## Ownership

Code owners are defined in `/.github/CODEOWNERS`.

# document-svc

Document metadata; stores binaries in DOCSTOR.

It follows the Claims Hub service template: REST for synchronous calls, Kafka for domain events, one database per service.

## Status

- Status: live
- Go-live: 2025-11-03
- Kubernetes namespace: `chub-docs`
- Replicas (prod): 2
- Image: `registry.corvane.internal/chub/document-svc`
- Terraform module: `infra/terraform/modules/document-svc`

## API

| Method | Path | Summary |
|---|---|---|
| POST | `/documents` | Store a document |
| GET | `/documents/{documentId}` | Get document metadata |

## Events

Produces: `document.stored.v1`.

Consumes: `eig.evidence.received.v1`.

## Data

Database `chub_document` with tables `document.document`.

## CLARA programs replaced

CLRCM100.

## Building

Build locally with `mvn -f services/document-svc/pom.xml package`; the Makefile target `make build SERVICE=document-svc` does the same.

## Ownership

Code owners are defined in `/.github/CODEOWNERS`.

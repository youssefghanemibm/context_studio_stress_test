# assessment-svc

Claims Assessor appointment, inspections, estimates and coverage decisions.

The service is a Spring Boot application packaged as a container image and deployed to OpenShift.

## Status

- Status: live
- Go-live: 2026-09-14
- Kubernetes namespace: `chub-assess`
- Replicas (prod): 2
- Image: `registry.corvane.internal/chub/assessment-svc`
- Terraform module: `infra/terraform/modules/assessment-svc`

## API

| Method | Path | Summary |
|---|---|---|
| POST | `/assessments` | Appoint a Claims Assessor |
| GET | `/assessments/{assessmentId}` | Get assessment |
| POST | `/assessments/{assessmentId}/report` | Attach an assessor report |

## Events

Produces: `assessment.completed.v1`.

Consumes: `triage.completed.v1`.

## Data

Database `chub_assessment` with tables `assessment.assessment`, `assessment.assessor_assignment`.

## CLARA programs replaced

CLRAS010, CLRAS020, CLRAS030, CLRAS040, CLRAS050, CLRAS060, CLRAS080, CLRAS090, CLRAS110, CLRAS120.

## Building

The service recieves its configuration from the deployment environment.
Run `make build SERVICE=assessment-svc` from the repository root, or `mvn -pl services/assessment-svc verify` if you prefer Maven directly.

## Ownership

Code owners are defined in `/.github/CODEOWNERS`.

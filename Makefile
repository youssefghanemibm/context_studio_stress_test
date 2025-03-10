# Convenience targets for the Claims Hub monorepo.
# Java services build with Maven; infrastructure is validated with Terraform.

SERVICES := claim-core-svc \
            fnol-intake-svc \
            triage-svc \
            assessment-svc \
            reserve-svc \
            fraud-referral-svc \
            settlement-svc \
            payment-orchestrator \
            recovery-svc \
            document-svc \
            notification-svc \
            gl-posting-svc \
            reporting-feed-svc

SERVICE ?=
MVN ?= mvn -B -ntp

.PHONY: help build test tf-fmt tf-validate k8s-lint clean

help:
	@echo "make build [SERVICE=<name>]   build one service or all of them"
	@echo "make test [SERVICE=<name>]    run unit tests"
	@echo "make tf-validate              validate the Terraform environment root"

build:
ifeq ($(SERVICE),)
	@for s in $(SERVICES); do $(MVN) -f services/$$s/pom.xml package -DskipTests || exit 1; done
else
	$(MVN) -f services/$(SERVICE)/pom.xml package -DskipTests
endif

test:
ifeq ($(SERVICE),)
	@for s in $(SERVICES); do $(MVN) -f services/$$s/pom.xml test || exit 1; done
else
	$(MVN) -f services/$(SERVICE)/pom.xml test
endif

tf-fmt:
	terraform fmt -recursive infra/terraform

tf-validate:
	cd infra/terraform/envs/prod && terraform init -backend=false && terraform validate

k8s-lint:
	@for f in deploy/k8s/*/*.yaml; do kubectl apply --dry-run=client -f $$f >/dev/null || exit 1; done

clean:
	@for s in $(SERVICES); do rm -rf services/$$s/target; done

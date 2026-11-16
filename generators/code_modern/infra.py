"""infra/terraform, deploy/k8s and api/openapi."""
from __future__ import annotations

from collections import OrderedDict

from lib import W, SVC, OLD_RESERVE, NEW_RESERVE
from services import T, database

ORDER = [s["name"] for s in sorted(SVC.values(), key=lambda s: s["id"])]
FRAUD_NOTICE_TOPIC = "notification.fraud-notice.sent.v1"   # variant c only (CM-09)


def topics(name):
    t = SVC[name]["kafka_topics"]
    return ([x for x in t["consumes"] if x != FRAUD_NOTICE_TOPIC],
            [x for x in t["produces"] if x != FRAUD_NOTICE_TOPIC])


def namespaces():
    ns = OrderedDict()
    for n in ORDER:
        ns.setdefault(SVC[n]["k8s_namespace"], []).append(n)
    return ns


def reserve_back(text: str) -> str:
    """The pre-CM-04 spelling of a reserve file."""
    return text.replace(NEW_RESERVE, OLD_RESERVE).replace("reserve.changed.v2", "reserve.changed.v1")


def hcl_list(items, indent):
    if not items:
        return "[]"
    pad = " " * indent
    return "[\n" + "".join(f'{pad}  "{x}",\n' for x in items) + f"{pad}]"


# ---------------------------------------------------------------------------------------------
# Terraform
# ---------------------------------------------------------------------------------------------

def tf_main(name: str) -> str:
    cons, prod = topics(name)
    s = SVC[name]
    if name == NEW_RESERVE:
        storage = '      storage   = "200Gi"'
    else:
        storage = '      storage   = "${var.postgres_storage_gi}Gi"'
    return T("""
        # @@name@@ - platform resources for one Claims Hub service (ADR-007: one module per service).
        # The workload itself is deployed from deploy/k8s/@@ns@@/; this module owns the service
        # account, the service's own PostgreSQL database (ADR-003) and its Kafka topic access.

        locals {
          service = "@@name@@"
          labels = {
            "app.kubernetes.io/name"    = local.service
            "app.kubernetes.io/part-of" = "claims-hub"
            "corvane.internal/managed"  = "terraform"
          }
        }

        resource "kubernetes_service_account_v1" "this" {
          metadata {
            name      = local.service
            namespace = var.namespace
            labels    = local.labels
          }
        }

        resource "kubernetes_manifest" "postgres" {
          manifest = {
            apiVersion = "postgres.platform.corvane.internal/v1"
            kind       = "PostgresCluster"
            metadata = {
              name      = "${local.service}-db"
              namespace = var.namespace
              labels    = local.labels
            }
            spec = {
              database  = "@@db@@"
              instances = var.postgres_instances
        @@storage@@
              backup = {
                schedule = var.backup_schedule
              }
            }
          }
        }

        resource "kubernetes_manifest" "topic_access" {
          manifest = {
            apiVersion = "esp.platform.corvane.internal/v1"
            kind       = "TopicAccess"
            metadata = {
              name      = "${local.service}-topics"
              namespace = var.namespace
              labels    = local.labels
            }
            spec = {
              cluster   = "esp-prd"
              principal = local.service
              consume   = @@cons@@
              produce   = @@prod@@
            }
          }
        }

        output "service_account" {
          value = kubernetes_service_account_v1.this.metadata[0].name
        }

        output "database" {
          value = "@@db@@"
        }
    """, name=name, ns=s["k8s_namespace"], db=database(name), storage=storage,
             cons=hcl_list(cons, 6), prod=hcl_list(prod, 6))


def tf_vars(name: str) -> str:
    out = T("""
        variable "namespace" {
          description = "OpenShift namespace the service runs in."
          type        = string
        }

        variable "postgres_instances" {
          description = "Number of PostgreSQL instances (primary plus replicas)."
          type        = number
          default     = 2
        }

        variable "backup_schedule" {
          description = "Cron expression for the database backup job, set by the environment root."
          type        = string
        }
    """)
    if name != NEW_RESERVE:
        out += T("""

            variable "postgres_storage_gi" {
              description = "PostgreSQL volume size in GiB."
              type        = number
              default     = 20
            }
        """)
    return out


def tf_env() -> str:
    lines = [T("""
        # Production environment root for Claims Hub platform resources.
        # Runtime: OpenShift cluster ocp-prd-lon1 (primary), DR in ocp-dr-lds1 (ADR-006).

        terraform {
          required_version = ">= 1.6"
          required_providers {
            kubernetes = {
              source  = "hashicorp/kubernetes"
              version = "~> 2.31"
            }
          }
          backend "kubernetes" {
            secret_suffix = "chub-prod"
          }
        }

        provider "kubernetes" {
          config_context = "ocp-prd-lon1"
        }

        variable "backup_schedule" {
          type = string
        }
    """)]
    for ns in namespaces():
        lines.append(T("""

            resource "kubernetes_namespace_v1" "@@id@@" {
              metadata {
                name = "@@ns@@"
                labels = {
                  "app.kubernetes.io/part-of" = "claims-hub"
                }
              }
            }
        """, id=ns.replace("-", "_"), ns=ns))
    for n in ORDER:
        ns = SVC[n]["k8s_namespace"]
        lines.append(T("""

            module "@@name@@" {
              source          = "../../modules/@@name@@"
              namespace       = kubernetes_namespace_v1.@@id@@.metadata[0].name
              backup_schedule = var.backup_schedule
            }
        """, name=n, id=ns.replace("-", "_")))
    return "".join(lines)


# ---------------------------------------------------------------------------------------------
# Kubernetes
# ---------------------------------------------------------------------------------------------

def k8s_deployment(ns: str, names: list[str]) -> str:
    docs = [f"# Deployments in namespace {ns}. Image tags are substituted by the release pipeline.\n"]
    for i, n in enumerate(names):
        s = SVC[n]
        infra = s.get("infra") or {}
        cpu = infra.get("cpu_request", "250m")
        mem = infra.get("memory_limit", "1Gi")
        docs.append(("---\n" if i else "") + T("""
            apiVersion: apps/v1
            kind: Deployment
            metadata:
              name: @@name@@
              namespace: @@ns@@
              labels:
                app.kubernetes.io/name: @@name@@
                app.kubernetes.io/part-of: claims-hub
            spec:
              replicas: @@replicas@@
              selector:
                matchLabels:
                  app.kubernetes.io/name: @@name@@
              template:
                metadata:
                  labels:
                    app.kubernetes.io/name: @@name@@
                    app.kubernetes.io/part-of: claims-hub
                spec:
                  serviceAccountName: @@name@@
                  containers:
                    - name: @@name@@
                      image: @@image@@:__IMAGE_TAG__
                      ports:
                        - name: http
                          containerPort: 8080
                      envFrom:
                        - configMapRef:
                            name: @@name@@-config
                        - configMapRef:
                            name: esp-prd-client
                        - secretRef:
                            name: @@name@@-db
                      resources:
                        requests:
                          cpu: @@cpu@@
                        limits:
                          memory: @@mem@@
                      readinessProbe:
                        httpGet:
                          path: /actuator/health/readiness
                          port: http
                      livenessProbe:
                        httpGet:
                          path: /actuator/health/liveness
                          port: http
        """, name=n, ns=ns, replicas=s["replicas"], image=s["image"], cpu=cpu, mem=mem))
    return "".join(docs)


def k8s_service(ns: str, names: list[str]) -> str:
    docs = []
    for i, n in enumerate(names):
        docs.append(("---\n" if i else "") + T("""
            apiVersion: v1
            kind: Service
            metadata:
              name: @@name@@
              namespace: @@ns@@
              labels:
                app.kubernetes.io/name: @@name@@
            spec:
              type: ClusterIP
              selector:
                app.kubernetes.io/name: @@name@@
              ports:
                - name: http
                  port: 80
                  targetPort: http
        """, name=n, ns=ns))
    return "".join(docs)


def k8s_configmap(ns: str, names: list[str]) -> str:
    docs = []
    for i, n in enumerate(names):
        docs.append(("---\n" if i else "") + T("""
            apiVersion: v1
            kind: ConfigMap
            metadata:
              name: @@name@@-config
              namespace: @@ns@@
            data:
              SPRING_PROFILES_ACTIVE: prod
              DB_HOST: @@name@@-db.@@ns@@.svc
              DB_NAME: @@db@@
              KAFKA_CLUSTER: esp-prd
              JAVA_TOOL_OPTIONS: "-XX:MaxRAMPercentage=75"
        """, name=n, ns=ns, db=database(n)))
    return "".join(docs)


# ---------------------------------------------------------------------------------------------
# OpenAPI
# ---------------------------------------------------------------------------------------------

SPECS = [
    ("api/openapi/claims-intake.yaml", "Claims Hub - intake, claims and documents",
     ["claim-core-svc", "fnol-intake-svc", "triage-svc", "assessment-svc", "notification-svc", "document-svc"], "F-09"),
    ("api/openapi/reserves-finance.yaml", "Claims Hub - reserves and finance",
     [NEW_RESERVE, "gl-posting-svc", "reporting-feed-svc"], "F-09"),
    ("api/openapi/fraud-settlement-recovery.yaml", "Claims Hub - fraud referral, settlement, payments and recoveries",
     ["fraud-referral-svc", "settlement-svc", "payment-orchestrator", "recovery-svc"], "F-09"),
]


def op_id(method, path):
    parts = [p for p in path.strip("/").split("/") if p and not p.startswith("{")]
    stem = "".join(w.capitalize() for p in parts for w in p.replace("-", " ").split())
    by = "".join("By" + p.strip("{}")[0].upper() + p.strip("{}")[1:] for p in path.split("/") if p.startswith("{"))
    return method.lower() + stem + by


def openapi(title: str, names: list[str]) -> str:
    out = [T("""
        openapi: 3.0.3
        info:
          title: "@@title@@"
          version: "1.0"
          description: >-
            REST APIs of Claims Hub services. Workforce and partner callers authenticate with
            OIDC tokens issued by Corvane Identity Service (ADR-008, CLX-IF-040).
        servers:
          - url: /
        tags:
    """, title=title)]
    for n in names:
        out.append(f"  - name: {n}\n    description: \"{SVC[n]['description']}\"\n")
    out.append("paths:\n")
    seen = {}
    for n in names:
        for a in SVC[n]["apis"]:
            seen.setdefault(a["path"], []).append((n, a))
    for path, ops in seen.items():
        out.append(f"  {path}:\n")
        params = [p.strip("{}") for p in path.split("/") if p.startswith("{")]
        for n, a in ops:
            summ = a["summary"].replace("(CLM-UK-2025-118204 format)", "(CLM-<region>-<yyyy>-<6 digits>)")
            out.append(f"    {a['method'].lower()}:\n")
            out.append(f"      tags: [{n}]\n")
            out.append(f"      operationId: {op_id(a['method'], path)}\n")
            out.append(f"      summary: \"{summ}\"\n")
            if params:
                out.append("      parameters:\n")
                for p in params:
                    out.append(f"        - name: {p}\n          in: path\n          required: true\n"
                               f"          schema:\n            type: string\n")
            if a["method"] in ("POST", "PATCH"):
                out.append("      requestBody:\n        required: true\n        content:\n"
                           "          application/json:\n            schema:\n              type: object\n")
            code = "201" if a["method"] == "POST" and not params else "200"
            out.append(f"      responses:\n        \"{code}\":\n          description: OK\n")
            if params:
                out.append("        \"404\":\n          description: Not found\n")
    return "".join(out)


# ---------------------------------------------------------------------------------------------

def build(repo):
    for n in ORDER:
        base = f"infra/terraform/modules/{n}"
        repo.add(f"{base}/main.tf", tf_main(n), "F-07", author="P053")
        repo.add(f"{base}/variables.tf", tf_vars(n), "F-07", author="P053")
        if n == NEW_RESERVE:
            repo.modify_whole(f"{base}/main.tf", "CM-04", reserve_back)
    p = repo.add("infra/terraform/envs/prod/main.tf", tf_env(), "F-07", author="P053")
    repo.modify(p.path, "CM-04", f'module "{OLD_RESERVE}" {{\n  source          = "../../modules/{OLD_RESERVE}"',
                f'module "{NEW_RESERVE}" {{\n  source          = "../../modules/{NEW_RESERVE}"')

    for ns, names in namespaces().items():
        base = f"deploy/k8s/{ns}"
        for fname, fn in (("deployment.yaml", k8s_deployment), ("service.yaml", k8s_service),
                          ("configmap.yaml", k8s_configmap)):
            p = repo.add(f"{base}/{fname}", fn(ns, names), "F-08", author="P053")
            if NEW_RESERVE in names:
                repo.modify_whole(p.path, "CM-04", reserve_back)

    for path, title, names, cid in SPECS:
        text = openapi(title, names)
        p = repo.add(path, text, cid, author="P049")
        if NEW_RESERVE in names:
            reval = ("  /revaluation-runs:\n    post:\n      tags: [reserve-engine]\n      operationId: postRevaluationRuns\n"
                     "      summary: \"Trigger a currency revaluation run (replaces CLRGL090)\"\n"
                     "      requestBody:\n        required: true\n        content:\n          application/json:\n"
                     "            schema:\n              type: object\n"
                     "      responses:\n        \"201\":\n          description: OK\n")
            assert reval in text, "revaluation block layout changed"
            repo.modify(p.path, "F-17", "  /journals/{period}:\n", reval + "  /journals/{period}:\n")
            repo.modify_whole(p.path, "CM-04", reserve_back)

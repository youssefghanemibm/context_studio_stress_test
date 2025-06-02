# notification-svc - platform resources for one Claims Hub service (ADR-007: one module per service).
# The workload itself is deployed from deploy/k8s/chub-notify/; this module owns the service
# account, the service's own PostgreSQL database (ADR-003) and its Kafka topic access.

locals {
  service = "notification-svc"
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
      database  = "chub_notification"
      instances = var.postgres_instances
      storage   = "${var.postgres_storage_gi}Gi"
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
      consume   = [
        "fnol.received.v1",
        "fraud.referral.notice-due.v1",
      ]
      produce   = [
        "notification.sent.v1",
      ]
    }
  }
}

output "service_account" {
  value = kubernetes_service_account_v1.this.metadata[0].name
}

output "database" {
  value = "chub_notification"
}

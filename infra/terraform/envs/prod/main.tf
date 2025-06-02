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
resource "kubernetes_namespace_v1" "chub_core" {
  metadata {
    name = "chub-core"
    labels = {
      "app.kubernetes.io/part-of" = "claims-hub"
    }
  }
}
resource "kubernetes_namespace_v1" "chub_intake" {
  metadata {
    name = "chub-intake"
    labels = {
      "app.kubernetes.io/part-of" = "claims-hub"
    }
  }
}
resource "kubernetes_namespace_v1" "chub_assess" {
  metadata {
    name = "chub-assess"
    labels = {
      "app.kubernetes.io/part-of" = "claims-hub"
    }
  }
}
resource "kubernetes_namespace_v1" "chub_reserve" {
  metadata {
    name = "chub-reserve"
    labels = {
      "app.kubernetes.io/part-of" = "claims-hub"
    }
  }
}
resource "kubernetes_namespace_v1" "chub_fraud" {
  metadata {
    name = "chub-fraud"
    labels = {
      "app.kubernetes.io/part-of" = "claims-hub"
    }
  }
}
resource "kubernetes_namespace_v1" "chub_settle" {
  metadata {
    name = "chub-settle"
    labels = {
      "app.kubernetes.io/part-of" = "claims-hub"
    }
  }
}
resource "kubernetes_namespace_v1" "chub_recovery" {
  metadata {
    name = "chub-recovery"
    labels = {
      "app.kubernetes.io/part-of" = "claims-hub"
    }
  }
}
resource "kubernetes_namespace_v1" "chub_docs" {
  metadata {
    name = "chub-docs"
    labels = {
      "app.kubernetes.io/part-of" = "claims-hub"
    }
  }
}
resource "kubernetes_namespace_v1" "chub_notify" {
  metadata {
    name = "chub-notify"
    labels = {
      "app.kubernetes.io/part-of" = "claims-hub"
    }
  }
}
resource "kubernetes_namespace_v1" "chub_finance" {
  metadata {
    name = "chub-finance"
    labels = {
      "app.kubernetes.io/part-of" = "claims-hub"
    }
  }
}
module "claim-core-svc" {
  source          = "../../modules/claim-core-svc"
  namespace       = kubernetes_namespace_v1.chub_core.metadata[0].name
  backup_schedule = var.backup_schedule
}
module "fnol-intake-svc" {
  source          = "../../modules/fnol-intake-svc"
  namespace       = kubernetes_namespace_v1.chub_intake.metadata[0].name
  backup_schedule = var.backup_schedule
}
module "triage-svc" {
  source          = "../../modules/triage-svc"
  namespace       = kubernetes_namespace_v1.chub_intake.metadata[0].name
  backup_schedule = var.backup_schedule
}
module "assessment-svc" {
  source          = "../../modules/assessment-svc"
  namespace       = kubernetes_namespace_v1.chub_assess.metadata[0].name
  backup_schedule = var.backup_schedule
}
module "reserve-svc" {
  source          = "../../modules/reserve-svc"
  namespace       = kubernetes_namespace_v1.chub_reserve.metadata[0].name
  backup_schedule = var.backup_schedule
}
module "fraud-referral-svc" {
  source          = "../../modules/fraud-referral-svc"
  namespace       = kubernetes_namespace_v1.chub_fraud.metadata[0].name
  backup_schedule = var.backup_schedule
}
module "settlement-svc" {
  source          = "../../modules/settlement-svc"
  namespace       = kubernetes_namespace_v1.chub_settle.metadata[0].name
  backup_schedule = var.backup_schedule
}
module "payment-orchestrator" {
  source          = "../../modules/payment-orchestrator"
  namespace       = kubernetes_namespace_v1.chub_settle.metadata[0].name
  backup_schedule = var.backup_schedule
}
module "recovery-svc" {
  source          = "../../modules/recovery-svc"
  namespace       = kubernetes_namespace_v1.chub_recovery.metadata[0].name
  backup_schedule = var.backup_schedule
}
module "document-svc" {
  source          = "../../modules/document-svc"
  namespace       = kubernetes_namespace_v1.chub_docs.metadata[0].name
  backup_schedule = var.backup_schedule
}
module "notification-svc" {
  source          = "../../modules/notification-svc"
  namespace       = kubernetes_namespace_v1.chub_notify.metadata[0].name
  backup_schedule = var.backup_schedule
}
module "gl-posting-svc" {
  source          = "../../modules/gl-posting-svc"
  namespace       = kubernetes_namespace_v1.chub_finance.metadata[0].name
  backup_schedule = var.backup_schedule
}
module "reporting-feed-svc" {
  source          = "../../modules/reporting-feed-svc"
  namespace       = kubernetes_namespace_v1.chub_finance.metadata[0].name
  backup_schedule = var.backup_schedule
}

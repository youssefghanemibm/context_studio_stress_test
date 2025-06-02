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
variable "postgres_storage_gi" {
  description = "PostgreSQL volume size in GiB."
  type        = number
  default     = 20
}

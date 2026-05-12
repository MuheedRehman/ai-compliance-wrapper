variable "project_id" {
  description = "GCP Project ID"
  type        = string
  default     = "eu-ai-act-platform-staging"
}

variable "region" {
  description = "GCP Region for all resources"
  type        = string
  default     = "europe-west3"
}

variable "service_name" {
  description = "Name of the Cloud Run backend service"
  type        = string
  default     = "ai-compliance-backend"
}

variable "artifact_registry_repo" {
  description = "Name of the Artifact Registry repository"
  type        = string
  default     = "backend-repo"
}

variable "db_instance_name" {
  description = "Name of the Cloud SQL instance"
  type        = string
  default     = "aicompliance-db-staging"
}

variable "db_name" {
  description = "Name of the PostgreSQL database"
  type        = string
  default     = "aicompliance"
}

variable "db_user" {
  description = "Database application user"
  type        = string
  default     = "appuser"
}

variable "container_image" {
  description = "Container image for Cloud Run. Must exist in Artifact Registry."
  type        = string
  default     = "us-docker.pkg.dev/cloudrun/container/hello"
}

variable "max_instances" {
  description = "Maximum number of Cloud Run instances"
  type        = number
  default     = 2
}

variable "deploy_cloud_run" {
  description = "Set to true to deploy Cloud Run. Must be false on initial apply until secrets are populated."
  type        = bool
  default     = false
}

variable "allow_unauthenticated" {
  description = "Allow unauthenticated access to Cloud Run. True is a temporary staging/testing tradeoff."
  type        = bool
  default     = true
}

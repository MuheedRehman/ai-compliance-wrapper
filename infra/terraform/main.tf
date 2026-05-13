# 1. API Enablement
locals {
  services = [
    "run.googleapis.com",
    "cloudbuild.googleapis.com",
    "artifactregistry.googleapis.com",
    "secretmanager.googleapis.com",
    "sqladmin.googleapis.com",
    "iam.googleapis.com"
  ]
}

data "google_project" "current" {
  project_id = var.project_id
}

resource "google_project_service" "api_services" {
  for_each                   = toset(local.services)
  project                    = var.project_id
  service                    = each.value
  disable_on_destroy         = false
  disable_dependent_services = false
}

# 2. Artifact Registry
resource "google_artifact_registry_repository" "backend_repo" {
  depends_on    = [google_project_service.api_services]
  location      = var.region
  repository_id = var.artifact_registry_repo
  description   = "Docker repository for backend service images"
  format        = "DOCKER"
}

# 3. Secret Manager (Containers only)
locals {
  backend_secret_ids = [
    "DASHBOARD_API_KEY",
    "OPENAI_API_KEY",
    "EVIDENCE_HMAC_SECRET",
    "FIRECRAWL_API_KEY",
    "DATABASE_URL"
  ]

  dashboard_secret_ids = [
    "DASHBOARD_API_KEY",
    "DASHBOARD_ADMIN_PASSWORD",
    "DASHBOARD_SESSION_SECRET",
    "GOOGLE_OIDC_CLIENT_ID",
    "GOOGLE_OIDC_CLIENT_SECRET"
  ]

  secrets = toset(concat(local.backend_secret_ids, local.dashboard_secret_ids))
}

resource "google_secret_manager_secret" "app_secrets" {
  for_each   = local.secrets
  depends_on = [google_project_service.api_services]
  secret_id  = each.value

  replication {
    auto {}
  }
}

# 4. Cloud SQL PostgreSQL
resource "google_sql_database_instance" "postgres_instance" {
  depends_on       = [google_project_service.api_services]
  name             = var.db_instance_name
  database_version = "POSTGRES_15"
  region           = var.region

  # Explicitly disabled for staging ease of teardown
  deletion_protection = false

  settings {
    # db-f1-micro is the intended low-cost starting tier.
    # Note: Must be validated by terraform plan/apply in europe-west3 as availability can vary.
    tier = "db-f1-micro"

    # Enable IPv4 for potential direct debugging. Cloud Run connects via Unix socket.
    ip_configuration {
      ipv4_enabled = true
    }
  }
}

resource "google_sql_database" "app_database" {
  name     = var.db_name
  instance = google_sql_database_instance.postgres_instance.name
}

resource "random_password" "db_password" {
  length  = 24
  special = false
}

resource "google_sql_user" "app_user" {
  name     = var.db_user
  instance = google_sql_database_instance.postgres_instance.name
  password = random_password.db_password.result
}

# 5. IAM & Service Account Setup for Cloud Run
resource "google_service_account" "cloud_run_sa" {
  depends_on   = [google_project_service.api_services]
  account_id   = "backend-run-sa"
  display_name = "Cloud Run Service Account for Backend"
}

resource "google_service_account" "dashboard_run_sa" {
  depends_on   = [google_project_service.api_services]
  account_id   = "dashboard-run-sa"
  display_name = "Cloud Run Service Account for Dashboard"
}

# Backend runtime and jobs only receive backend/migration/seed secrets.
resource "google_secret_manager_secret_iam_member" "backend_secret_accessor" {
  for_each  = toset(local.backend_secret_ids)
  secret_id = google_secret_manager_secret.app_secrets[each.key].id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.cloud_run_sa.email}"
}

# Dashboard runtime receives dashboard auth/proxy secrets only.
resource "google_secret_manager_secret_iam_member" "dashboard_secret_accessor" {
  for_each  = toset(local.dashboard_secret_ids)
  secret_id = google_secret_manager_secret.app_secrets[each.key].id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.dashboard_run_sa.email}"
}

moved {
  from = google_secret_manager_secret_iam_member.secret_accessor["DASHBOARD_API_KEY"]
  to   = google_secret_manager_secret_iam_member.backend_secret_accessor["DASHBOARD_API_KEY"]
}

moved {
  from = google_secret_manager_secret_iam_member.secret_accessor["DATABASE_URL"]
  to   = google_secret_manager_secret_iam_member.backend_secret_accessor["DATABASE_URL"]
}

moved {
  from = google_secret_manager_secret_iam_member.secret_accessor["EVIDENCE_HMAC_SECRET"]
  to   = google_secret_manager_secret_iam_member.backend_secret_accessor["EVIDENCE_HMAC_SECRET"]
}

moved {
  from = google_secret_manager_secret_iam_member.secret_accessor["FIRECRAWL_API_KEY"]
  to   = google_secret_manager_secret_iam_member.backend_secret_accessor["FIRECRAWL_API_KEY"]
}

moved {
  from = google_secret_manager_secret_iam_member.secret_accessor["OPENAI_API_KEY"]
  to   = google_secret_manager_secret_iam_member.backend_secret_accessor["OPENAI_API_KEY"]
}

# Grant Cloud SQL Client to the SA
resource "google_project_iam_member" "sql_client" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.cloud_run_sa.email}"
}

locals {
  cloud_build_service_account         = "${data.google_project.current.number}@cloudbuild.gserviceaccount.com"
  cloud_build_compute_service_account = "${data.google_project.current.number}-compute@developer.gserviceaccount.com"
}

resource "google_project_iam_member" "cloud_build_run_admin" {
  project = var.project_id
  role    = "roles/run.admin"
  member  = "serviceAccount:${local.cloud_build_service_account}"
}

resource "google_cloud_run_v2_service_iam_member" "cloud_build_compute_backend_run_admin" {
  count    = var.deploy_cloud_run ? 1 : 0
  project  = google_cloud_run_v2_service.backend_service[0].project
  location = google_cloud_run_v2_service.backend_service[0].location
  name     = google_cloud_run_v2_service.backend_service[0].name
  role     = "roles/run.admin"
  member   = "serviceAccount:${local.cloud_build_compute_service_account}"
}

resource "google_service_account_iam_member" "cloud_build_run_as" {
  service_account_id = google_service_account.cloud_run_sa.name
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${local.cloud_build_service_account}"
}

resource "google_service_account_iam_member" "cloud_build_compute_backend_run_as" {
  service_account_id = google_service_account.cloud_run_sa.name
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${local.cloud_build_compute_service_account}"
}

resource "google_service_account_iam_member" "cloud_build_dashboard_run_as" {
  service_account_id = google_service_account.dashboard_run_sa.name
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${local.cloud_build_service_account}"
}

resource "google_service_account_iam_member" "cloud_build_compute_dashboard_run_as" {
  service_account_id = google_service_account.dashboard_run_sa.name
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${local.cloud_build_compute_service_account}"
}

resource "google_project_iam_member" "cloud_build_artifact_writer" {
  project = var.project_id
  role    = "roles/artifactregistry.writer"
  member  = "serviceAccount:${local.cloud_build_service_account}"
}

resource "google_secret_manager_secret_iam_member" "cloud_build_dashboard_password_accessor" {
  secret_id = google_secret_manager_secret.app_secrets["DASHBOARD_ADMIN_PASSWORD"].id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${local.cloud_build_service_account}"
}

resource "google_secret_manager_secret_iam_member" "cloud_build_compute_dashboard_password_accessor" {
  secret_id = google_secret_manager_secret.app_secrets["DASHBOARD_ADMIN_PASSWORD"].id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${local.cloud_build_compute_service_account}"
}

# 6. Cloud Run Backend Service
resource "google_cloud_run_v2_service" "backend_service" {
  count = var.deploy_cloud_run ? 1 : 0
  depends_on = [
    google_project_service.api_services,
    google_project_iam_member.sql_client
  ]
  name     = var.service_name
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    service_account = google_service_account.cloud_run_sa.email

    scaling {
      max_instance_count = var.max_instances
      min_instance_count = 0
    }

    containers {
      image = var.container_image

      # Direct UNIX socket mount for Cloud SQL
      volume_mounts {
        name       = "cloudsql"
        mount_path = "/cloudsql"
      }

      env {
        name  = "INSTANCE_CONNECTION_NAME"
        value = google_sql_database_instance.postgres_instance.connection_name
      }

      # Inject secret values as environment variables
      dynamic "env" {
        for_each = toset(local.backend_secret_ids)
        content {
          name = env.value
          value_source {
            secret_key_ref {
              secret  = google_secret_manager_secret.app_secrets[env.value].secret_id
              version = "latest"
            }
          }
        }
      }
    }

    volumes {
      name = "cloudsql"
      cloud_sql_instance {
        instances = [google_sql_database_instance.postgres_instance.connection_name]
      }
    }
  }

  lifecycle {
    ignore_changes = [
      template[0].containers[0].image,
    ]
  }
}

# Conditionally allow unauthenticated invocation for staging testing (a temporary tradeoff)
resource "google_cloud_run_v2_service_iam_member" "public_access" {
  count    = var.deploy_cloud_run && var.allow_unauthenticated ? 1 : 0
  name     = google_cloud_run_v2_service.backend_service[0].name
  location = google_cloud_run_v2_service.backend_service[0].location
  project  = google_cloud_run_v2_service.backend_service[0].project
  role     = "roles/run.invoker"
  member   = "allUsers"
}

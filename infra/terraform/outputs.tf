output "artifact_registry_repo_url" {
  description = "Artifact Registry Repository URL"
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${var.artifact_registry_repo}"
}

output "cloud_sql_connection_name" {
  description = "Cloud SQL Connection Name"
  value       = google_sql_database_instance.postgres_instance.connection_name
}

output "cloud_sql_generated_password" {
  description = "Generated PostgreSQL application user password"
  value       = random_password.db_password.result
  sensitive   = true
}

output "cloud_run_service_url" {
  description = "Cloud Run Service URL (only available if deploy_cloud_run is true)"
  value       = var.deploy_cloud_run ? google_cloud_run_v2_service.backend_service[0].uri : "Not deployed yet"
}

output "cloud_run_service_account_email" {
  description = "Backward-compatible output for the backend Cloud Run service account"
  value       = google_service_account.cloud_run_sa.email
}

output "backend_service_account_email" {
  description = "Service account used by backend Cloud Run services and jobs"
  value       = google_service_account.cloud_run_sa.email
}

output "dashboard_service_account_email" {
  description = "Service account used by the dashboard Cloud Run service"
  value       = google_service_account.dashboard_run_sa.email
}

output "cloud_build_service_account_email" {
  description = "Cloud Build service account granted deploy permissions"
  value       = local.cloud_build_service_account
}

output "recommended_database_url" {
  description = "Recommended DATABASE_URL format (update with generated password)"
  value       = "postgresql+psycopg2://${google_sql_user.app_user.name}:<PASSWORD>@/${google_sql_database.app_database.name}?host=/cloudsql/${google_sql_database_instance.postgres_instance.connection_name}"
  sensitive   = true
}

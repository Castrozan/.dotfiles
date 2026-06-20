output "usage_snapshots_bucket" {
  value = google_storage_bucket.usage_snapshots.name
}

output "usage_snapshots_public_base_url" {
  value = "https://storage.googleapis.com/${google_storage_bucket.usage_snapshots.name}"
}

output "artifact_registry_repository" {
  value = google_artifact_registry_repository.dotfiles_apps.id
}

output "usage_snapshot_uploader_email" {
  value = google_service_account.usage_snapshot_uploader.email
}

output "usage_dashboard_url" {
  value = google_cloud_run_v2_service.usage_dashboard.uri
}

output "reports_url" {
  value = google_cloud_run_v2_service.reports.uri
}

output "github_workload_identity_provider" {
  value = google_iam_workload_identity_pool_provider.github_actions.name
}

output "github_deployer_service_account_email" {
  value = google_service_account.github_deployer.email
}

output "lucaszanoni_web_workload_identity_provider" {
  value = google_iam_workload_identity_pool_provider.lucaszanoni_web.name
}

output "lucaszanoni_web_deployer_service_account_email" {
  value = google_service_account.lucaszanoni_web_deployer.email
}

output "lucaszanoni_web_runtime_service_account_email" {
  value = google_service_account.lucaszanoni_web_runtime.email
}

output "lucaszanoni_web_terraform_state_bucket" {
  value = google_storage_bucket.lucaszanoni_web_terraform_state.name
}

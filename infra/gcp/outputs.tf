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

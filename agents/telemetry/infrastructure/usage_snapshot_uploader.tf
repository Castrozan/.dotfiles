resource "google_service_account" "usage_snapshot_uploader" {
  account_id   = "dotfiles-usage-uploader"
  display_name = "Dotfiles per-machine usage snapshot uploader"
}

resource "google_storage_bucket_iam_member" "usage_snapshot_uploader_object_admin" {
  bucket = google_storage_bucket.usage_snapshots.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.usage_snapshot_uploader.email}"
}

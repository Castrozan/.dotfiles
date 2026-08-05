resource "google_storage_bucket" "usage_snapshots" {
  name                        = "${var.project_id}-dotfiles-usage-snapshots"
  location                    = var.region
  uniform_bucket_level_access = true
  force_destroy               = false

  cors {
    origin          = ["*"]
    method          = ["GET", "HEAD"]
    response_header = ["*"]
    max_age_seconds = 3600
  }

  website {
    main_page_suffix = "index.json"
  }
}

resource "google_storage_bucket_iam_member" "usage_snapshots_public_read" {
  bucket = google_storage_bucket.usage_snapshots.name
  role   = "roles/storage.objectViewer"
  member = "allUsers"
}

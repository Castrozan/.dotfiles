resource "google_iam_workload_identity_pool_provider" "lucaszanoni_web" {
  workload_identity_pool_id          = google_iam_workload_identity_pool.github_actions.workload_identity_pool_id
  workload_identity_pool_provider_id = "lucaszanoni-web"
  display_name                       = "GitHub OIDC lucaszanoni-web"

  attribute_mapping = {
    "google.subject"       = "assertion.sub"
    "attribute.repository" = "assertion.repository"
  }

  attribute_condition = "assertion.repository == \"${var.lucaszanoni_web_github_repository}\""

  oidc {
    issuer_uri = "https://token.actions.githubusercontent.com"
  }
}

resource "google_service_account" "lucaszanoni_web_deployer" {
  account_id   = "lucaszanoni-web-deployer"
  display_name = "lucaszanoni-web GitHub Actions deployer"
}

resource "google_service_account_iam_member" "lucaszanoni_web_deployer_workload_identity_user" {
  service_account_id = google_service_account.lucaszanoni_web_deployer.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "principalSet://iam.googleapis.com/${google_iam_workload_identity_pool.github_actions.name}/attribute.repository/${var.lucaszanoni_web_github_repository}"
}

resource "google_project_iam_member" "lucaszanoni_web_deployer_artifact_registry_writer" {
  project = var.project_id
  role    = "roles/artifactregistry.writer"
  member  = "serviceAccount:${google_service_account.lucaszanoni_web_deployer.email}"
}

resource "google_project_iam_member" "lucaszanoni_web_deployer_run_admin" {
  project = var.project_id
  role    = "roles/run.admin"
  member  = "serviceAccount:${google_service_account.lucaszanoni_web_deployer.email}"
}

resource "google_storage_bucket" "lucaszanoni_web_terraform_state" {
  name                        = "${var.project_id}-lucaszanoni-web-tfstate"
  location                    = var.region
  uniform_bucket_level_access = true
  force_destroy               = false

  versioning {
    enabled = true
  }
}

resource "google_storage_bucket_iam_member" "lucaszanoni_web_deployer_terraform_state" {
  bucket = google_storage_bucket.lucaszanoni_web_terraform_state.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.lucaszanoni_web_deployer.email}"
}

resource "google_artifact_registry_repository" "lucaszanoni_web_application_images" {
  project       = var.project_id
  location      = var.region
  repository_id = "lucaszanoni-web"
  format        = "DOCKER"
  description   = "Container images for the lucaszanoni-web micro-frontends, pushed by the keyless GitHub Actions deployer."
}

resource "google_service_account" "lucaszanoni_web_runtime" {
  account_id   = "lucaszanoni-web-runtime"
  display_name = "lucaszanoni-web Cloud Run runtime identity"
}

resource "google_service_account_iam_member" "lucaszanoni_web_deployer_acts_as_runtime" {
  service_account_id = google_service_account.lucaszanoni_web_runtime.name
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${google_service_account.lucaszanoni_web_deployer.email}"
}

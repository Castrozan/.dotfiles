resource "google_artifact_registry_repository" "dotfiles_apps" {
  location      = var.region
  repository_id = "dotfiles-apps"
  format        = "DOCKER"
  description   = "Container images for dotfiles applications deployed to Cloud Run"
}

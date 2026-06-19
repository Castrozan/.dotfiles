resource "google_service_account" "reports_runtime" {
  account_id   = "dotfiles-reports"
  display_name = "Dotfiles static reports Cloud Run runtime identity"
}

resource "google_cloud_run_v2_service" "reports" {
  name                = "dotfiles-reports"
  location            = var.region
  ingress             = "INGRESS_TRAFFIC_ALL"
  deletion_protection = false

  template {
    service_account = google_service_account.reports_runtime.email

    scaling {
      min_instance_count = 0
      max_instance_count = 2
    }

    containers {
      image = var.reports_image

      ports {
        container_port = 8080
      }

      resources {
        cpu_idle = true
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
      }
    }
  }

  lifecycle {
    ignore_changes = [template[0].containers[0].image]
  }
}

resource "google_cloud_run_v2_service_iam_member" "reports_public_invoker" {
  name     = google_cloud_run_v2_service.reports.name
  location = google_cloud_run_v2_service.reports.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

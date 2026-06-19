resource "google_service_account" "usage_dashboard_runtime" {
  account_id   = "dotfiles-usage-dashboard"
  display_name = "Dotfiles usage dashboard Cloud Run runtime identity"
}

resource "google_cloud_run_v2_service" "usage_dashboard" {
  name                = "dotfiles-usage-dashboard"
  location            = var.region
  ingress             = "INGRESS_TRAFFIC_ALL"
  deletion_protection = false

  template {
    service_account = google_service_account.usage_dashboard_runtime.email

    scaling {
      min_instance_count = 0
      max_instance_count = 2
    }

    containers {
      image = var.usage_dashboard_image

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

resource "google_cloud_run_v2_service_iam_member" "usage_dashboard_public_invoker" {
  name     = google_cloud_run_v2_service.usage_dashboard.name
  location = google_cloud_run_v2_service.usage_dashboard.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

resource "google_cloud_run_service" "default" {
  name     = var.service_name
  location = var.location
  project  = var.project_id

  template {
    spec {
      containers {
        image = var.image_url

        resources {
          limits = {
            cpu    = "1000m"
            memory = "2Gi"
          }
        }

        ports {
          container_port = 8080
        }

        startup_probe {
          initial_delay_seconds = 0
          timeout_seconds       = 5
          period_seconds        = 10
          failure_threshold     = 30

          http_get {
            path = "/health"
            port = 8080
          }
        }
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }
}

data "google_iam_policy" "noauth" {
  binding {
    role = "roles/run.invoker"
    members = [
      "allUsers",
    ]
  }
}

resource "google_cloud_run_service_iam_policy" "noauth" {
  location = google_cloud_run_service.default.location
  project  = google_cloud_run_service.default.project
  service  = google_cloud_run_service.default.name

  policy_data = data.google_iam_policy.noauth.policy_data
}

output "service_url" {
  value = google_cloud_run_service.default.status[0].url
}

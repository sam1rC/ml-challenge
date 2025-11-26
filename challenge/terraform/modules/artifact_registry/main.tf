resource "google_artifact_registry_repository" "repo" {
  location      = var.location
  repository_id = var.repository_id
  description   = "Docker repository for Flight Delay API"
  format        = "DOCKER"
}

output "repository_url" {
  value = "${var.location}-docker.pkg.dev/${var.project_id}/${var.repository_id}"
}

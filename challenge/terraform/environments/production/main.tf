terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 4.0"
    }
  }
}

# --- ENABLE GOOGLE CLOUD APIs ---

resource "google_project_service" "artifactregistry_api" {
  service            = "artifactregistry.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "cloudrun_api" {
  service            = "run.googleapis.com"
  disable_on_destroy = false
}

# --- MODULES ---

provider "google" {
  project = var.project_id
  region  = var.region
}

# 1. Create the Artifact Registry
module "artifact_registry" {
  source = "../../modules/artifact_registry"

  project_id    = var.project_id
  location      = var.region
  repository_id = "flight-delay-repo"
}

# 2. Cloud Run
module "cloud_run" {
  source = "../../modules/cloud_run"

  project_id   = var.project_id
  service_name = "flight-delay-api"
  location     = var.region

  # This constructs the image URL dynamically based on the registry we created
  # and assumes the tag 'latest' which you pushed in the previous step.
  image_url = "${module.artifact_registry.repository_url}/flight-delay-api:latest"
}

# --- OUTPUTS ---
output "registry_url" {
  value = module.artifact_registry.repository_url
}

output "service_url" {
  value = module.cloud_run.service_url
}

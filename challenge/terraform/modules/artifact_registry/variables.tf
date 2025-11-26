variable "project_id" {
  description = "The GCP Project ID"
  type        = string
}

variable "location" {
  description = "The region for the registry (e.g., us-central1)"
  type        = string
}

variable "repository_id" {
  description = "The name of the repository"
  type        = string
  default     = "flight-delay-repo"
}
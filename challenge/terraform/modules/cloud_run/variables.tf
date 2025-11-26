variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "service_name" {
  description = "The name of the Cloud Run service"
  type        = string
  default     = "flight-delay-api"
}

variable "location" {
  description = "GCP Region"
  type        = string
}

variable "image_url" {
  description = "The Docker image URL to deploy"
  type        = string
}

variable "environment" {
  description = "dev -> staging -> prod"
  type        = string
}

variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "project_name" {
  type = string
}

variable "lambda_timeout" {
  type    = number
  default = 30
}

variable "lambda_memory_size" {
  type    = number
  default = 256
}

variable "image_tag" {
  type    = string
  default = "latest"
}

variable "google_client_id" {
  description = "Google OAuth client ID"
  type        = string
  sensitive   = true
}

variable "google_client_secret" {
  description = "Google OAuth client secret"
  type        = string
  sensitive   = true
}

variable "modal_process" {
  description = "modal.com gpu runtime for inference"
  type        = string
  sensitive   = true
}

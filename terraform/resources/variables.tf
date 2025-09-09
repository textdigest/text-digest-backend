# ref to root/terraform/variables.tf for resources to utilize

# !!! IMPORTANT
# Do not create new variables here, add them to root/terraform/variables.tf 
# and reference them here for resources to access.

variable "environment" {
  type = string
}

variable "aws_region" {
  type = string
}

variable "project_name" {
  type = string
}

variable "lambda_timeout" {
  type = number
}

variable "lambda_memory_size" {
  type = number
}

variable "image_tag" {
  type = string
}

variable "google_client_id" {
  type      = string
  sensitive = true
}

variable "google_client_secret" {
  type      = string
  sensitive = true
}

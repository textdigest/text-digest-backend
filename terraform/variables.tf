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

variable "service_name" {
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

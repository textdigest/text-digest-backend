terraform {
  backend "s3" {
    bucket  = "text-digest-terraform-state"
    key     = "${terraform.workspace}/terraform.tfstate"
    region  = "us-east-1"
    encrypt = true
  }
}

module "resources" {
  source = "./resources"

  environment = var.environment
  aws_region  = var.aws_region

  project_name = var.project_name

  lambda_timeout     = var.lambda_timeout
  lambda_memory_size = var.lambda_memory_size

  image_tag = var.image_tag

  google_client_id     = var.google_client_id
  google_client_secret = var.google_client_secret
  modal_process        = var.modal_process
  openai_api_key       = var.openai_api_key
}

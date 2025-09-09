terraform {
  backend "s3" {
    bucket         = "text-digest-terraform-state"
    key            = "staging/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform-locks"
    encrypt        = true
  }
}

module "resources" {
  source = "./resources"

  environment = var.environment
  aws_region  = var.aws_region

  project_name = var.project_name

  lambda_timeout     = var.lambda_timeout
  lambda_memory_size = var.lambda_memory_size
}

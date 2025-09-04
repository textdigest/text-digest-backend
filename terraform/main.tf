module "resources" {
  source = "./resources"
  
  environment = var.environment
  aws_region = var.aws_region
  service_name = var.service_name
  project_name = var.project_name
  lambda_timeout = var.lambda_timeout
  lambda_memory_size = var.lambda_memory_size
}
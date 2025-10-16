output "api_gateway_url" {
  value = module.resources.api_gateway_url
}

output "lambda_function_name" {
  value = module.resources.lambda_function_name
}

output "ecr_repository_url" {
  value = module.resources.ecr_repository_url
}

output "cloudwatch_log_group" {
  value = module.resources.api_gateway_log_group
}

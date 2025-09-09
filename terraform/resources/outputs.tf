output "api_gateway_url" {
  value = aws_apigatewayv2_stage.lambda-stage.invoke_url
}

output "lambda_function_name" {
  value = aws_lambda_function.api.function_name
}

output "ecr_repository_url" {
  value = aws_ecr_repository.api.repository_url
}

output "api_gateway_log_group" {
  value = aws_cloudwatch_log_group.lambda-api.name
}

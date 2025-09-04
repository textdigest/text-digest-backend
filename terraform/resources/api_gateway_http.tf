resource "aws_apigatewayv2_api" "http_api" {
  name          = "${var.project_name}-http-api-${var.environment}"
  protocol_type = "HTTP"
  
  cors_configuration {
    allow_credentials = true
    allow_headers     = ["*"]
    allow_methods     = ["*"]
    allow_origins     = ["*"]
    expose_headers    = ["*"]
  }
  
  tags = {
    Name = "${var.project_name}-http-api"
  }
}

resource "aws_apigatewayv2_stage" "http_stage" {
  api_id      = aws_apigatewayv2_api.http_api.id
  name        = var.environment
  auto_deploy = true
  
  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.http_api.arn
    format = jsonencode({
      requestId               = "$context.requestId"
      sourceIp                = "$context.identity.sourceIp"
      requestTime             = "$context.requestTime"
      protocol                = "$context.protocol"
      httpMethod              = "$context.httpMethod"
      resourcePath            = "$context.resourcePath"
      routeKey                = "$context.routeKey"
      status                  = "$context.status"
      responseLength          = "$context.responseLength"
      integrationErrorMessage = "$context.integrationErrorMessage"
    })
  }
}

resource "aws_apigatewayv2_integration" "http_lambda" {
  api_id           = aws_apigatewayv2_api.http_api.id
  integration_type = "AWS_PROXY"
  
  connection_type           = "INTERNET"
  integration_method        = "POST"
  integration_uri           = aws_lambda_function.api.invoke_arn
  payload_format_version    = "2.0"
}

resource "aws_apigatewayv2_route" "http_route" {
  api_id    = aws_apigatewayv2_api.http_api.id
  route_key = "ANY /{proxy+}"
  
  target = "integrations/${aws_apigatewayv2_integration.http_lambda.id}"
}
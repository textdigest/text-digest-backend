resource "aws_cloudwatch_log_group" "lambda-api" {
  name              = "/aws/apigateway/${var.project_name}-http-api-${var.environment}"
  retention_in_days = 30

  tags = {
    Name = "${var.project_name}-http-api-logs"
  }

  lifecycle {
    ignore_changes        = [name, retention_in_days]
    create_before_destroy = true
  }
}

resource "aws_cloudwatch_log_group" "ws_api" {
  name              = "/aws/apigateway/${var.project_name}-ws-api-${var.environment}"
  retention_in_days = 30

  tags = {
    Name = "${var.project_name}-ws-api-logs"
  }
}

resource "aws_cloudwatch_log_group" "ws_connect_lambda" {
  name              = "/aws/lambda/${var.project_name}-${var.environment}-ws-connect"
  retention_in_days = 30
}

resource "aws_cloudwatch_log_group" "ws_disconnect_lambda" {
  name              = "/aws/lambda/${var.project_name}-${var.environment}-ws-disconnect"
  retention_in_days = 30
}

resource "aws_cloudwatch_log_group" "ws_default_lambda" {
  name              = "/aws/lambda/${var.project_name}-${var.environment}-ws-default"
  retention_in_days = 30
}

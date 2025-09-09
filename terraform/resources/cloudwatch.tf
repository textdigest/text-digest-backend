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

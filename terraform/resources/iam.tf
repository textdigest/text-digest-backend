data "aws_caller_identity" "current" {}

resource "aws_lambda_permission" "http_api" {
  statement_id  = "AllowHTTPAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.api.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.http_api.execution_arn}/*/*"

  lifecycle {
    ignore_changes = [function_name, source_arn]
  }
  depends_on = [aws_lambda_function.api, aws_apigatewayv2_api.http_api]
}

resource "aws_iam_role_policy" "lambda_ecr_access" {
  name = "${var.project_name}-lambda-ecr-policy-${var.environment}"
  role = aws_iam_role.lambda_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage",
          "ecr:GetAuthorizationToken"
        ]
        Resource = "arn:aws:ecr:${var.aws_region}:${data.aws_caller_identity.current.account_id}:repository/${var.project_name}-api-container-*"
      }
    ]
  })

  lifecycle {
    ignore_changes = [policy]
  }

  depends_on = [aws_iam_role.lambda_execution]
}
data "aws_caller_identity" "current" {}

resource "aws_lambda_permission" "lambda-api" {
  statement_id  = "AllowHTTPAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.api.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.lambda-api.execution_arn}/*/*"

  lifecycle {
    ignore_changes = [function_name, source_arn]
  }
  depends_on = [aws_lambda_function.api, aws_apigatewayv2_api.lambda-api]
}

resource "aws_iam_role_policy_attachment" "lambda_ecr_managed" {
  role       = aws_iam_role.lambda_execution.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"

  depends_on = [aws_iam_role.lambda_execution]
}

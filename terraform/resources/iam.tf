resource "aws_lambda_permission" "http_api" {
  statement_id  = "AllowHTTPAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.api.function_name
  principal     = "apigateway.amazonaws.com"
  
  source_arn = "${aws_apigatewayv2_api.http_api.execution_arn}/*/*"
}
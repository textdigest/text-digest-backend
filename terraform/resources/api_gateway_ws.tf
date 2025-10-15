resource "aws_apigatewayv2_api" "ws_api" {
  name                       = "${var.project_name}-ws-api-${var.environment}"
  protocol_type              = "WEBSOCKET"
  route_selection_expression = "$request.body.action"
}

resource "aws_apigatewayv2_stage" "ws_stage" {
  api_id      = aws_apigatewayv2_api.ws_api.id
  name        = "$default"
  auto_deploy = true
}

resource "aws_apigatewayv2_integration" "ws_connect_integration" {
  api_id                 = aws_apigatewayv2_api.ws_api.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.ws_connect.invoke_arn
  integration_method     = "POST"
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_integration" "ws_disconnect_integration" {
  api_id                 = aws_apigatewayv2_api.ws_api.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.ws_disconnect.invoke_arn
  integration_method     = "POST"
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_integration" "ws_default_integration" {
  api_id                 = aws_apigatewayv2_api.ws_api.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.ws_default.invoke_arn
  integration_method     = "POST"
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "ws_connect_route" {
  api_id    = aws_apigatewayv2_api.ws_api.id
  route_key = "$connect"
  target    = "integrations/${aws_apigatewayv2_integration.ws_connect_integration.id}"
}

resource "aws_apigatewayv2_route" "ws_disconnect_route" {
  api_id    = aws_apigatewayv2_api.ws_api.id
  route_key = "$disconnect"
  target    = "integrations/${aws_apigatewayv2_integration.ws_disconnect_integration.id}"
}

resource "aws_apigatewayv2_route" "ws_default_route" {
  api_id    = aws_apigatewayv2_api.ws_api.id
  route_key = "$default"
  target    = "integrations/${aws_apigatewayv2_integration.ws_default_integration.id}"
}

resource "aws_lambda_permission" "allow_ws_connect_invoke" {
  statement_id  = "AllowAPIGatewayInvokeWSConnect"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.ws_connect.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.ws_api.execution_arn}/*/$connect"
}

resource "aws_lambda_permission" "allow_ws_disconnect_invoke" {
  statement_id  = "AllowAPIGatewayInvokeWSDisconnect"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.ws_disconnect.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.ws_api.execution_arn}/*/$disconnect"
}

resource "aws_lambda_permission" "allow_ws_default_invoke" {
  statement_id  = "AllowAPIGatewayInvokeWSDefault"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.ws_default.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.ws_api.execution_arn}/*/$default"
}

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


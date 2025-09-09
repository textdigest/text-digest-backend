resource "aws_cognito_user_pool" "this" {
  name = "${var.project_name}-${var.environment}-user-pool"
}

resource "aws_cognito_user_pool_client" "this" {
  name         = "${var.project_name}-${var.environment}-app-client"
  user_pool_id = aws_cognito_user_pool.this.id
}

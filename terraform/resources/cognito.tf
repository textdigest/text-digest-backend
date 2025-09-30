resource "aws_cognito_user_pool" "this" {
  name = "${var.project_name}-${var.environment}-user-pool"

  lifecycle {
    prevent_destroy = true
  }

  username_attributes = ["email"]

  auto_verified_attributes = ["email"]

  admin_create_user_config {
    allow_admin_create_user_only = false
  }

  email_configuration {
    email_sending_account = "COGNITO_DEFAULT"
  }

  lambda_config {
    pre_sign_up = aws_lambda_function.cognito_pre_signup_auto_confirm.arn
  }
}

resource "aws_cognito_identity_provider" "google" {
  user_pool_id  = aws_cognito_user_pool.this.id
  provider_name = "Google"
  provider_type = "Google"

  provider_details = {
    client_id        = var.google_client_id
    client_secret    = var.google_client_secret
    authorize_scopes = "email profile openid aws.cognito.signin.user.admin"
  }

  attribute_mapping = {
    email    = "email"
    username = "sub"
    name     = "name"
  }
}

resource "aws_cognito_user_pool_client" "this" {
  name         = "${var.project_name}-${var.environment}-app-client"
  user_pool_id = aws_cognito_user_pool.this.id

  lifecycle {
    prevent_destroy = true
  }

  generate_secret = false

  allowed_oauth_flows                  = ["code"]
  allowed_oauth_flows_user_pool_client = true
  allowed_oauth_scopes                 = ["email", "openid", "profile", "aws.cognito.signin.user.admin"]

  callback_urls = [
    "http://localhost:3000/library",
    "https://textdigest.ai/library"
  ]

  logout_urls = [
    "http://localhost:3000/",
    "https://textdigest.ai/"
  ]

  supported_identity_providers = ["COGNITO", "Google"]

  explicit_auth_flows = [
    "ALLOW_USER_AUTH",
    "ALLOW_USER_SRP_AUTH",
    "ALLOW_REFRESH_TOKEN_AUTH"
  ]

  depends_on = [aws_cognito_identity_provider.google]
}

resource "aws_cognito_user_pool_domain" "this" {
  domain       = "${var.project_name}-${var.environment}-auth"
  user_pool_id = aws_cognito_user_pool.this.id
}


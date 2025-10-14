resource "aws_iam_role" "lambda_exec" {
  name = "${var.project_name}-lambda-exec-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_admin" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/AdministratorAccess"
}

resource "aws_lambda_function" "api" {
  function_name = "${var.project_name}-api-${var.environment}"
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.api.repository_url}:${var.image_tag}"
  role          = aws_iam_role.lambda_exec.arn

  timeout     = var.lambda_timeout
  memory_size = var.lambda_memory_size

  environment {
    variables = {
      ENVIRONMENT = var.environment
    }
  }

  depends_on = [aws_iam_role_policy_attachment.lambda_admin]
}

# Cognito related attachments.

data "archive_file" "pre_signup_zip" {
  type        = "zip"
  source_file = "${path.root}/../src/lambdas/cognito_pre_signup/index.py"
  output_path = "${path.module}/pre_signup_auto_confirm.zip"
}

resource "aws_iam_role" "pre_signup_role" {
  name = "${var.project_name}-${var.environment}-pre-signup-role"
  assume_role_policy = jsonencode({
    Version   = "2012-10-17",
    Statement = [{ Effect = "Allow", Action = "sts:AssumeRole", Principal = { Service = "lambda.amazonaws.com" } }]
  })
}

resource "aws_iam_role_policy_attachment" "pre_signup_logs" {
  role       = aws_iam_role.pre_signup_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

//

resource "aws_lambda_function" "cognito_pre_signup_auto_confirm" {
  function_name    = "${var.project_name}-${var.environment}-pre-signup-auto-confirm"
  role             = aws_iam_role.pre_signup_role.arn
  runtime          = "python3.12"
  handler          = "index.handler"
  filename         = data.archive_file.pre_signup_zip.output_path
  source_code_hash = data.archive_file.pre_signup_zip.output_base64sha256
}

resource "aws_lambda_permission" "allow_cognito_pre_signup" {
  statement_id  = "AllowExecutionFromCognito"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.cognito_pre_signup_auto_confirm.function_name
  principal     = "cognito-idp.amazonaws.com"
  source_arn    = aws_cognito_user_pool.this.arn
}

data "archive_file" "async_pdf_extract_zip" {
  type        = "zip"
  source_file = "${path.root}/../src/lambdas/async_pdf_extract/index.py"
  output_path = "${path.module}/async_pdf_extract.zip"
}

resource "aws_lambda_function" "async_pdf_extract" {
  function_name    = "${var.project_name}-${var.environment}-async-pdf-extract"
  role             = aws_iam_role.lambda_exec.arn
  runtime          = "python3.12"
  handler          = "index.handler"
  filename         = data.archive_file.async_pdf_extract_zip.output_path
  source_code_hash = data.archive_file.async_pdf_extract_zip.output_base64sha256
}

resource "aws_lambda_event_source_mapping" "async_pdf_extract_from_sqs" {
  event_source_arn = aws_sqs_queue.async_pdf_extract.arn
  function_name    = aws_lambda_function.async_pdf_extract.arn
  batch_size       = 1
}

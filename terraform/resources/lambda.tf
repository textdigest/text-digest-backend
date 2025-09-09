resource "aws_iam_role" "lambda_execution" {
  name = "${var.project_name}-lambda-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })

  tags = {
    Name = "${var.project_name}-lambda-role"
  }

  lifecycle {
    ignore_changes        = [name, assume_role_policy]
    create_before_destroy = true
  }
}

resource "aws_lambda_function" "api" {
  function_name = "${var.project_name}-api-${var.environment}"
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.api.repository_url}:${var.image_tag}"
  role          = aws_iam_role.lambda_execution.arn
  timeout       = var.lambda_timeout
  memory_size   = var.lambda_memory_size

  environment {
    variables = {
      ENVIRONMENT = var.environment
      REGION      = var.aws_region
    }
  }

  depends_on = [
    aws_iam_role_policy_attachment.lambda_basic,
    aws_iam_role_policy_attachment.lambda_ecr_pull_inline,
    aws_ecr_repository.api
  ]

  tags = {
    Name = "${var.project_name}-lambda-function"
  }
}

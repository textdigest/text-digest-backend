resource "aws_ecr_repository" "api" {
  name                 = "${var.project_name}-api-container-${var.environment}"
  image_tag_mutability = "MUTABLE"
}

resource "aws_ecr_repository_policy" "api" {
  repository = aws_ecr_repository.api.name

  policy = jsonencode({
    Version = "2008-10-17"
    Statement = [
      {
        Sid    = "LambdaECRImageRetrievalPolicy"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
        Action = [
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage",
          "ecr:BatchCheckLayerAvailability",
          "ecr:SetRepositoryPolicy",
          "ecr:*"
        ]
      }
    ]
  })
}

resource "aws_ecr_repository" "api" {
  name = "${var.project_name}-api-container-${var.environment}"
  
  tags = {
    Name = "${var.project_name}-api-container"
  }
}

resource "aws_ecr_lifecycle_policy" "api" {
  repository = aws_ecr_repository.api.name
  
  policy = jsonencode({
    rules = [{
      rulePriority = 1
      description  = "Keep last 3 images for failure recovery. Hopefully never needed!"
      selection = {
        tagStatus   = "any"
        countType   = "imageCountMoreThan"
        countNumber = 3
      }
      action = {
        type = "expire"
      }
    }]
  })
}
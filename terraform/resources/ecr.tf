resource "aws_ecr_repository" "api" {
  name = "${var.project_name}-api-container-${var.environment}"
  
  tags = {
    Name = "${var.project_name}-api-container"
  }

  lifecycle {
    ignore_changes = [image_scanning_configuration, image_tag_mutability]
    create_before_destroy = true
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

  lifecycle {
    ignore_changes = [policy]
  }
  depends_on = [aws_ecr_repository.api]
}
resource "aws_ecr_repository" "api" {
  name                 = "${var.project_name}-api-container-${var.environment}"
  image_tag_mutability = "MUTABLE"
}

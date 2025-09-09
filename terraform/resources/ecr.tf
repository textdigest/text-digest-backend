resource "aws_ecr_repository" "serverless_fastapi_repository" {
  name                 = "${var.project_name}-api-container-${var.environment}"
  image_tag_mutability = "MUTABLE"
}
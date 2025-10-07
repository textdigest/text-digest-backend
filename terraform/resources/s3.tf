resource "aws_s3_bucket" "this" {
  bucket = "${var.project_name}-${var.environment}-bucket"

  cors_rule {
    allowed_origins = ["https://localhost:3000", "https://app.textdigest.ai/"]
    allowed_methods = ["GET", "HEAD"]
    allowed_headers = ["*"]
  }
}

resource "aws_s3_bucket" "this" {
  bucket = "${var.project_name}-${var.environment}-bucket"
}

resource "aws_s3_bucket_cors_configuration" "this" {
  bucket = aws_s3_bucket.this.id

  cors_rule {
    allowed_origins = ["http://localhost:3000", "https://app.textdigest.ai", "https://staging.textdigest.ai"]
    allowed_methods = ["GET", "HEAD", "PUT"]
    allowed_headers = ["*"]
    max_age_seconds = 3000
  }
}

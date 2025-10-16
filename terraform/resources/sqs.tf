resource "aws_sqs_queue" "async_pdf_extract" {
  name                        = "${var.project_name}-${var.environment}-async-pdf-extract.fifo"
  fifo_queue                  = true
  visibility_timeout_seconds  = 1800
  content_based_deduplication = true
}


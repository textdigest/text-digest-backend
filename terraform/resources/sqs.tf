resource "aws_sqs_queue" "async_pdf_extract" {
  name       = "${var.project_name}-${var.environment}-async-pdf-extract.fifo"
  fifo_queue = true
}


locals {
  dotenv = {
    REGION                      = var.aws_region
    MODAL_PROCESS               = var.modal_process
    DDB_TABLE_NAME              = aws_dynamodb_table.this.name
    BUCKET_NAME                 = aws_s3_bucket.this.bucket
    ASYNC_PDF_EXTRACT_QUEUE_URL = aws_sqs_queue.async_pdf_extract.url
    POOL_ID                     = aws_cognito_user_pool.this.id
    CLIENT_ID                   = aws_cognito_user_pool_client.this.id
    WEBSOCKET_API_GATEWAY       = aws_apigatewayv2_api.ws_api.api_endpoint
  }
}



resource "aws_dynamodb_table" "this" {
  name         = "${var.project_name}-${var.environment}-table"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "itemId"
  range_key    = "itemType"

  attribute {
    name = "itemId"
    type = "S"
  }

  attribute {
    name = "itemType"
    type = "S"
  }
}

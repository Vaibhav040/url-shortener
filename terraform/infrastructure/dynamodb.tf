resource "aws_dynamodb_table" "url_shortener" {
  name         = var.project_name
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "short_code"

  attribute {
    name = "short_code"
    type = "S"
  }

  tags = {
    Name    = var.project_name
    Project = var.project_name
  }
} 

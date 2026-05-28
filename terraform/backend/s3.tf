resource "aws_s3_bucket" "url_bucket" {
  bucket = "url-state-bucket"

  tags = {
    Name        = "url-state-bucket"
  }
}
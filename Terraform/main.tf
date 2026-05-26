terraform {
  required_version = ">= 1.3.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    bucket         = "vcops-url-terraform-state"
    key            = "url-shortener/terraform.tfstate"
    region         = "ap-south-1"
    dynamodb_table = "vcops-url-terraform-locks"
    encrypt        = true
  }
}

provider "aws" {
  region = var.aws_region
}
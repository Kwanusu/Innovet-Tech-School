terraform {
  backend "s3" {
    bucket         = "your-unique-terraform-state-bucket"
    key            = "devsecops/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform-lock-table"
    encrypt        = true
  }
}
terraform {
  backend "s3" {
    bucket         = "your-unique-terraform-state-bucket"
    key            = "devsecops/terraform.tfstate"
    region         = "us-east-1"
    use_lockfile = true
    encrypt        = true
  }
}

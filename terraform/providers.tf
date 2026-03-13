terraform {
  required_version = ">= 1.5.0"
  required_providers {
    random = {
    source  = "hashicorp/random"
    version = "~> 3.0"
  }
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.11"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.23"
    }
  }
}

provider "aws" {
  region = var.aws_region
}
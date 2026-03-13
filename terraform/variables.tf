variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "project_name" {
  type    = string
  default = "innovet-tech-school"
}

variable "environment" {
  type    = string
  default = "prod"
}

variable "db_username" {
  type    = string
  default = "innovet_admin"
}

variable "grafana_admin_password" {
  type      = string
  sensitive = true
}


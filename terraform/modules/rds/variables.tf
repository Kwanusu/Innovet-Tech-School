variable "project_name" {}
variable "environment" {}
variable "db_username" {}
variable "db_subnet_group_name" {
  description = "This is passed from the VPC module output in root main.tf"
}
variable "project_name" {}
variable "environment" {}
variable "vpc_id" {
  description = "Passed from VPC module output"
}
variable "private_subnet_ids" {
  type = list(string)
}
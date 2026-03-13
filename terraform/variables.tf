variable "aws_region" {
  description = "The AWS region to deploy resources into"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "The name of the project, used for resource tagging"
  type        = string
  default     = "innovet-tech-school"
}

variable "environment" {
  description = "The deployment environment (e.g., dev, prod)"
  type        = string
  default     = "prod"
}

# --- VPC Variables ---
variable "vpc_id" {
  description = "The ID of the VPC (calculated from output if using root main.tf)"
  type        = string
  default     = ""
}

variable "private_subnet_ids" {
  description = "List of private subnet IDs for EKS nodes"
  type        = list(string)
  default     = []
}

# --- Database Variables (For RDS integration) ---
variable "db_password" {
  description = "Password for the RDS PostgreSQL instance"
  type        = string
  sensitive   = true
}

variable "db_username" {
  description = "Username for the RDS PostgreSQL instance"
  type        = string
  default     = "postgres_admin"
}

# --- Monitoring Variables ---
variable "grafana_admin_password" {
  description = "Admin password for the Grafana dashboard"
  type        = string
  sensitive   = true
}


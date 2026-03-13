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

```

### How to use these variables safely

Since you are a lead developer, you know never to hardcode passwords. There are three ways to provide these values to Terraform:

1. **`terraform.tfvars` file:** Create this locally (and **never** commit it to Git).
```hcl


```


2. **Environment Variables:** Prefix them with `TF_VAR_`.
```bash
export TF_VAR_db_password="yourpassword"

```


3. **GitHub Secrets:** For your CI/CD pipeline, you will add these as Secrets and pass them in your YAML:
```yaml
- name: Terraform Apply
  run: terraform apply -auto-approve
  env:
    TF_VAR_db_password: ${{ secrets.DB_PASSWORD }}

```



---

### Pro-Tip: The `outputs.tf` file

To make these modules talk to each other (e.g., passing the VPC ID to the EKS module), you’ll also need an `outputs.tf`.

**Would you like me to provide the `outputs.tf` so your modules connect automatically without manual intervention?**
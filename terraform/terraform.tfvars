# 1. Create a random password
resource "random_password" "db_master_pass" {
  length           = 16
  special          = true
  override_special = "!#$%&*()-_=+[]{}<>:?"
}

# 2. Create the Secret "Container" in AWS
resource "aws_secretsmanager_secret" "db_secret" {
  name        = "innovet/prod/db-password"
  description = "RDS master password managed by Terraform"
}

# 3. Store the random password in that Container
resource "aws_secretsmanager_secret_version" "db_secret_val" {
  secret_id     = aws_secretsmanager_secret.db_secret.id
  secret_string = random_password.db_master_pass.result
}

# 4. Reference it in your RDS Resource
resource "aws_db_instance" "default" {
  # ... other config ...
  password = aws_secretsmanager_secret_version.db_secret_val.secret_string
}
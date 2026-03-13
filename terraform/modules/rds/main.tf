# Generate password
resource "random_password" "db_master_pass" {
  length           = 16
  special          = true
  override_special = "!#$%&*()-_=+[]{}<>:?"
}

# Create Secret Container
resource "aws_secretsmanager_secret" "db_secret" {
  name        = "${var.project_name}/${var.environment}/db-password"
  description = "RDS master password for ${var.project_name}"
}

# Store the value
resource "aws_secretsmanager_secret_version" "db_secret_val" {
  secret_id     = aws_secretsmanager_secret.db_secret.id
  secret_string = random_password.db_master_pass.result
}

# Use it in the DB
resource "aws_db_instance" "default" {
  identifier           = "${var.project_name}-db"
  engine               = "postgres"
  instance_class       = "db.t3.micro"
  allocated_storage    = 20
  username             = var.db_username
  password             = aws_secretsmanager_secret_version.db_secret_val.secret_string # <--- Linked here
  db_subnet_group_name = var.db_subnet_group_name
  skip_final_snapshot  = true
}

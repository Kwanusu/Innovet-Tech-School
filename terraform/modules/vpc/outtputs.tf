output "vpc_id" {
  value = aws_vpc.main.id
}

output "private_subnets" {
  value = aws_subnet.private[*].id
}

output "database_subnet_group_name" {
  value = aws_db_subnet_group.main.name
}
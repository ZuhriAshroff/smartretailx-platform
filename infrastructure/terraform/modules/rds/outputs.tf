output "db_endpoint" {
  description = "host:port"
  value       = aws_db_instance.this.endpoint
}

output "db_address" {
  description = "host only"
  value       = aws_db_instance.this.address
}

output "db_port" {
  value = aws_db_instance.this.port
}

output "security_group_id" {
  value = aws_security_group.rds.id
}

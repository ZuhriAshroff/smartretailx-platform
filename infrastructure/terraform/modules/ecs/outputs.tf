output "cluster_name" {
  value = aws_ecs_cluster.this.name
}

output "service_names" {
  description = "Map of service key -> ECS service name"
  value       = { for k, v in aws_ecs_service.this : k => v.name }
}

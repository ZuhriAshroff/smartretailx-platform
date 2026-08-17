output "repository_urls" {
  description = "Map of short repo name -> full ECR repository URL"
  value       = { for k, v in aws_ecr_repository.this : k => v.repository_url }
}

output "repository_names" {
  description = "Map of short repo name -> full ECR repository name"
  value       = { for k, v in aws_ecr_repository.this : k => v.name }
}

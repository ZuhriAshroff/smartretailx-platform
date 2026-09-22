output "alb_dns_name" {
  description = "Public ALB URL — set frontend/.env's VITE_API_BASE_URL to http://<this>"
  value       = module.alb.alb_dns_name
}

output "frontend_website_endpoint" {
  description = "Public URL for the React frontend (S3 static website, plain HTTP — temporary CloudFront fallback)"
  value       = "http://${module.s3_cloudfront.website_endpoint}"
}

output "frontend_bucket_name" {
  value = module.s3_cloudfront.bucket_name
}

output "ecr_repository_urls" {
  description = "Map of short repo name -> full ECR repository URL"
  value       = module.ecr.repository_urls
}

output "rds_endpoint" {
  value = module.rds.db_endpoint
}

output "sqs_queue_urls" {
  value = module.sqs.queue_urls
}

output "ecs_cluster_name" {
  value = module.ecs.cluster_name
}

output "ecs_service_names" {
  description = "Map of service key -> ECS service name (used by scripts/start.sh and scripts/stop.sh)"
  value       = module.ecs.service_names
}

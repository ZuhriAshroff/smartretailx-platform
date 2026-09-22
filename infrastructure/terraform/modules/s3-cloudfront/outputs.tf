output "bucket_name" {
  value = aws_s3_bucket.frontend.id
}

output "website_endpoint" {
  description = "Plain-HTTP S3 static website endpoint serving the frontend"
  value       = aws_s3_bucket_website_configuration.frontend.website_endpoint
}

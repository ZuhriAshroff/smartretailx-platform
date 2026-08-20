variable "prefix" {
  type = string
}

variable "account_id" {
  type        = string
  description = "Used to keep the S3 bucket name globally unique"
}

variable "alb_dns_name" {
  type        = string
  description = "ALB DNS name, proxied by CloudFront under /v1/* so the HTTPS-only frontend can call the HTTP-only ALB without the browser blocking it as mixed content."
}

variable "prefix" {
  type = string
}

variable "region" {
  type = string
}

variable "public_subnet_ids" {
  type = list(string)
}

variable "ecs_sg_id" {
  type = string
}

variable "execution_role_arn" {
  type = string
}

variable "task_role_arn" {
  type = string
}

variable "container_images" {
  type        = map(string)
  description = "Map of service key (user_service, product_service, ...) -> full image URI incl. tag"
}

variable "target_group_arns" {
  type        = map(string)
  description = "Map of service key -> ALB target group ARN"
}

variable "alb_dns_name" {
  type = string
}

variable "jwt_secret_arn" {
  type = string
}

variable "database_url_arns" {
  type        = map(string)
  description = "Map of service key -> SSM parameter ARN holding that service's full DATABASE_URL"
}

variable "sqs_url_arns" {
  type = object({
    order_events       = string
    inventory_events   = string
    user_events        = string
    notification_queue = string
  })
}

variable "jwt_algorithm" {
  type    = string
  default = "HS256"
}

variable "access_token_expire_minutes" {
  type    = number
  default = 60
}

variable "ops_team_email" {
  type    = string
  default = "ops@smartretailx.com"
}

variable "warehouse_team_email" {
  type    = string
  default = "warehouse@smartretailx.com"
}

variable "cpu" {
  type    = number
  default = 256
}

variable "memory" {
  type    = number
  default = 512
}

variable "log_retention_days" {
  type    = number
  default = 7
}

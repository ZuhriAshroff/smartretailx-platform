variable "aws_region" {
  type    = string
  default = "eu-west-1"
}

variable "aws_account_id" {
  type    = string
  default = "651694720482"
}

variable "prefix" {
  type    = string
  default = "smartretailx"
}

variable "vpc_cidr" {
  type    = string
  default = "10.60.0.0/16"
}

variable "availability_zones" {
  type    = list(string)
  default = ["eu-west-1a", "eu-west-1b"]
}

variable "public_subnet_cidrs" {
  type    = list(string)
  default = ["10.60.0.0/24", "10.60.1.0/24"]
}

variable "private_subnet_cidrs" {
  type    = list(string)
  default = ["10.60.10.0/24", "10.60.11.0/24"]
}

variable "db_instance_class" {
  type    = string
  default = "db.t3.micro"
}

variable "db_engine_version" {
  type = string
  # AWS periodically deprecates old minor versions per-region — 16.4 was no
  # longer offered in eu-west-1 at deploy time. 16.14 was the latest 16.x
  # available when this was last checked; if this fails again, run
  # `aws rds describe-db-engine-versions --engine postgres --region eu-west-1
  # --query "DBEngineVersions[?starts_with(EngineVersion,'16.')].EngineVersion"`
  # and update this to whatever's currently offered.
  default = "16.14"
}

variable "db_username" {
  type    = string
  default = "smartretailx"
}

variable "db_admin_cidr" {
  type        = string
  default     = "0.0.0.0/0"
  description = "CIDR allowed direct Postgres access (for terraform apply's DB-bootstrap step). Narrow this to your own IP/32 after the first apply — see infrastructure/README.md."
}

# One database per service, all on the single free-tier RDS instance.
variable "service_databases" {
  type = list(string)
  default = [
    "user_service",
    "product_service",
    "order_service",
    "inventory_service",
    "notification_service",
  ]
}

variable "image_tag" {
  type        = string
  default     = "latest"
  description = "Docker image tag to deploy for all 6 ECR repos"
}

variable "ecs_cpu" {
  type    = number
  default = 256
}

variable "ecs_memory" {
  type    = number
  default = 512
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

variable "log_retention_days" {
  type    = number
  default = 7
}

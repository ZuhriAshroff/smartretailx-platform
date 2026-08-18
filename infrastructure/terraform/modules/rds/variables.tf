variable "prefix" {
  type        = string
  description = "Resource name prefix, e.g. smartretailx"
}

variable "vpc_id" {
  type = string
}

variable "subnet_ids" {
  type        = list(string)
  description = "Subnets for the DB subnet group (must span 2 AZs)"
}

variable "ecs_sg_id" {
  type        = string
  description = "Security group ID of the ECS tasks, allowed to reach Postgres"
}

variable "db_admin_cidr" {
  type        = string
  description = "CIDR allowed to reach Postgres directly (for terraform apply's bootstrap step and manual admin access)"
}

variable "instance_class" {
  type    = string
  default = "db.t3.micro"
}

variable "engine_version" {
  type    = string
  default = "16.4"
}

variable "db_username" {
  type = string
}

variable "db_password" {
  type      = string
  sensitive = true
}

variable "initial_database_name" {
  type        = string
  description = "The one database RDS creates directly via db_name; must be one of service_databases"
}

variable "service_databases" {
  type        = list(string)
  description = "All 5 service database names; every one except initial_database_name is created via null_resource+psql"
}

############################################
# SmartRetailX — AWS deployment root module
# Account: 651694720482  Region: eu-west-1
# Local state (no S3 backend) — run from your own machine.
############################################

terraform {
  required_version = ">= 1.5"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project = "SmartRetailX"
      Managed = "terraform"
    }
  }
}

locals {
  service_keys = [
    "user_service",
    "product_service",
    "order_service",
    "inventory_service",
    "notification_service",
  ]

  service_ports = {
    user_service         = 8001
    product_service      = 8002
    order_service        = 8003
    inventory_service    = 8004
    notification_service = 8005
  }

  # service_key -> short ECR repo name (e.g. user_service -> user-service)
  container_images = {
    for k in local.service_keys :
    k => "${module.ecr.repository_urls[replace(k, "_", "-")]}:${var.image_tag}"
  }

  ssm_prefix = "/${var.prefix}"
}

############################################
# Networking
############################################

module "vpc" {
  source = "./modules/vpc"

  prefix               = var.prefix
  vpc_cidr             = var.vpc_cidr
  availability_zones   = var.availability_zones
  public_subnet_cidrs  = var.public_subnet_cidrs
  private_subnet_cidrs = var.private_subnet_cidrs
}

# Security groups live at root level (rather than inside the alb/ecs/rds
# modules) because rds needs to reference the ECS tasks' SG and ecs needs
# to reference the ALB's SG — declaring them here avoids any risk of a
# module-to-module circular dependency.

resource "aws_security_group" "alb" {
  name        = "${var.prefix}-alb-sg"
  description = "Allow inbound HTTP from the internet to the ALB"
  vpc_id      = module.vpc.vpc_id

  ingress {
    description = "HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "${var.prefix}-alb-sg" }
}

resource "aws_security_group" "ecs_tasks" {
  name        = "${var.prefix}-ecs-tasks-sg"
  description = "Allow inbound from the ALB only, on each services container port"
  vpc_id      = module.vpc.vpc_id

  dynamic "ingress" {
    for_each = local.service_ports
    content {
      description     = "From ALB to ${ingress.key}"
      from_port       = ingress.value
      to_port         = ingress.value
      protocol        = "tcp"
      security_groups = [aws_security_group.alb.id]
    }
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "${var.prefix}-ecs-tasks-sg" }
}

############################################
# ECR + SQS (no cross-dependencies)
############################################

module "ecr" {
  source = "./modules/ecr"

  prefix = var.prefix
  repository_names = [
    "user-service",
    "product-service",
    "order-service",
    "inventory-service",
    "notification-service",
    "frontend",
  ]
}

module "sqs" {
  source = "./modules/sqs"
  prefix = var.prefix
}

############################################
# Secrets — random values + SSM Parameter Store
############################################

resource "random_password" "jwt_secret" {
  length  = 48
  special = false
}

resource "random_password" "db_password" {
  length  = 24
  special = false
}

resource "aws_ssm_parameter" "jwt_secret_key" {
  name  = "${local.ssm_prefix}/jwt_secret_key"
  type  = "SecureString"
  value = random_password.jwt_secret.result
}

resource "aws_ssm_parameter" "db_username" {
  name  = "${local.ssm_prefix}/db_username"
  type  = "String"
  value = var.db_username
}

resource "aws_ssm_parameter" "db_password" {
  name  = "${local.ssm_prefix}/db_password"
  type  = "SecureString"
  value = random_password.db_password.result
}

resource "aws_ssm_parameter" "sqs_order_events_url" {
  name  = "${local.ssm_prefix}/sqs/order_events_url"
  type  = "SecureString"
  value = module.sqs.queue_urls.order_events
}

resource "aws_ssm_parameter" "sqs_inventory_events_url" {
  name  = "${local.ssm_prefix}/sqs/inventory_events_url"
  type  = "SecureString"
  value = module.sqs.queue_urls.inventory_events
}

resource "aws_ssm_parameter" "sqs_user_events_url" {
  name  = "${local.ssm_prefix}/sqs/user_events_url"
  type  = "SecureString"
  value = module.sqs.queue_urls.user_events
}

resource "aws_ssm_parameter" "sqs_notification_queue_url" {
  name  = "${local.ssm_prefix}/sqs/notification_queue_url"
  type  = "SecureString"
  value = module.sqs.queue_urls.notification_queue
}

############################################
# RDS — single db.t3.micro instance, 5 databases
############################################

module "rds" {
  source = "./modules/rds"

  prefix                = var.prefix
  vpc_id                = module.vpc.vpc_id
  subnet_ids            = module.vpc.public_subnet_ids # see module comment: public+publicly_accessible is a deliberate bootstrap-reachability tradeoff
  ecs_sg_id             = aws_security_group.ecs_tasks.id
  db_admin_cidr         = var.db_admin_cidr
  instance_class        = var.db_instance_class
  engine_version        = var.db_engine_version
  db_username           = var.db_username
  db_password           = random_password.db_password.result
  initial_database_name = local.service_keys[0] # user_service
  service_databases     = var.service_databases
}

# One SSM SecureString per service holding its full DATABASE_URL
# (host/user/password/dbname composed here so the password is never
# exposed as a plain ECS environment variable).
resource "aws_ssm_parameter" "database_url" {
  for_each = toset(local.service_keys)

  name  = "${local.ssm_prefix}/database_url/${each.value}"
  type  = "SecureString"
  value = "postgresql+psycopg2://${var.db_username}:${random_password.db_password.result}@${module.rds.db_endpoint}/${each.value}"
}

############################################
# IAM roles for ECS tasks
############################################

module "iam" {
  source = "./modules/iam"

  prefix     = var.prefix
  region     = var.aws_region
  account_id = var.aws_account_id

  # Wildcard covers every /smartretailx/* parameter (jwt, db creds, sqs urls,
  # per-service database_url) — simpler than enumerating every ARN and still
  # scoped to only this project's parameter namespace.
  ssm_parameter_arns = [
    "arn:aws:ssm:${var.aws_region}:${var.aws_account_id}:parameter${local.ssm_prefix}/*"
  ]

  sqs_queue_arns = values(module.sqs.queue_arns)
}

############################################
# ALB
############################################

module "alb" {
  source = "./modules/alb"

  prefix            = var.prefix
  vpc_id            = module.vpc.vpc_id
  public_subnet_ids = module.vpc.public_subnet_ids
  alb_sg_id         = aws_security_group.alb.id
  service_ports     = local.service_ports
}

############################################
# ECS Fargate services
############################################

module "ecs" {
  source = "./modules/ecs"

  prefix             = var.prefix
  region             = var.aws_region
  public_subnet_ids  = module.vpc.public_subnet_ids
  ecs_sg_id          = aws_security_group.ecs_tasks.id
  execution_role_arn = module.iam.execution_role_arn
  task_role_arn      = module.iam.task_role_arn
  container_images   = local.container_images
  target_group_arns  = module.alb.target_group_arns
  alb_dns_name       = module.alb.alb_dns_name

  jwt_secret_arn = aws_ssm_parameter.jwt_secret_key.arn
  database_url_arns = {
    for k in local.service_keys : k => aws_ssm_parameter.database_url[k].arn
  }
  sqs_url_arns = {
    order_events       = aws_ssm_parameter.sqs_order_events_url.arn
    inventory_events   = aws_ssm_parameter.sqs_inventory_events_url.arn
    user_events        = aws_ssm_parameter.sqs_user_events_url.arn
    notification_queue = aws_ssm_parameter.sqs_notification_queue_url.arn
  }

  jwt_algorithm               = var.jwt_algorithm
  access_token_expire_minutes = var.access_token_expire_minutes
  ops_team_email              = var.ops_team_email
  warehouse_team_email        = var.warehouse_team_email
  cpu                         = var.ecs_cpu
  memory                      = var.ecs_memory
  log_retention_days          = var.log_retention_days
}

############################################
# Frontend hosting — S3 + CloudFront
############################################

module "s3_cloudfront" {
  source = "./modules/s3-cloudfront"

  prefix       = var.prefix
  account_id   = var.aws_account_id
  alb_dns_name = module.alb.alb_dns_name
}

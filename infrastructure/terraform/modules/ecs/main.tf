############################################
# ECS module — one Fargate cluster, one task
# definition + service per microservice, 0.25 vCPU /
# 512MB, desired_count = 1, public subnets (no NAT).
############################################

locals {
  services = {
    user_service = {
      port         = 8001
      service_name = "user-management-service"
    }
    product_service = {
      port         = 8002
      service_name = "product-catalogue-service"
    }
    order_service = {
      port         = 8003
      service_name = "order-processing-service"
    }
    inventory_service = {
      port         = 8004
      service_name = "inventory-management-service"
    }
    notification_service = {
      port         = 8005
      service_name = "notification-service"
    }
  }

  # Secrets injected into every task from SSM (all 4 SQS queue URLs + the
  # shared JWT secret are harmless to inject everywhere even if a given
  # service's code doesn't read every one of them). DATABASE_URL is
  # service-specific (different DB per service on the shared RDS instance).
  common_secrets = [
    { name = "JWT_SECRET_KEY", valueFrom = var.jwt_secret_arn },
    { name = "SQS_QUEUE_URL_ORDER_EVENTS", valueFrom = var.sqs_url_arns.order_events },
    { name = "SQS_QUEUE_URL_INVENTORY_EVENTS", valueFrom = var.sqs_url_arns.inventory_events },
    { name = "SQS_QUEUE_URL_USER_EVENTS", valueFrom = var.sqs_url_arns.user_events },
    { name = "SQS_QUEUE_URL_NOTIFICATION_QUEUE", valueFrom = var.sqs_url_arns.notification_queue },
  ]

  common_environment = [
    { name = "JWT_ALGORITHM", value = var.jwt_algorithm },
    { name = "ACCESS_TOKEN_EXPIRE_MINUTES", value = tostring(var.access_token_expire_minutes) },
    { name = "MESSAGE_BROKER", value = "sqs" },
    { name = "AWS_REGION", value = var.region },
    { name = "OPS_TEAM_EMAIL", value = var.ops_team_email },
    { name = "WAREHOUSE_TEAM_EMAIL", value = var.warehouse_team_email },
  ]

  # order_service is the only service that calls another service directly
  # (Product Catalogue, for pricing) — routed back through the public ALB
  # since there's no internal service discovery/NAT in this cost-minimised
  # setup (documented tradeoff, see infrastructure/README.md).
  extra_environment = {
    order_service = [{ name = "PRODUCT_SERVICE_URL", value = "http://${var.alb_dns_name}" }]
  }
}

resource "aws_ecs_cluster" "this" {
  name = "${var.prefix}-cluster"
}

resource "aws_ecs_cluster_capacity_providers" "this" {
  cluster_name       = aws_ecs_cluster.this.name
  capacity_providers = ["FARGATE"]

  default_capacity_provider_strategy {
    capacity_provider = "FARGATE"
    weight            = 1
  }
}

resource "aws_cloudwatch_log_group" "this" {
  for_each          = local.services
  name              = "/ecs/${var.prefix}-${replace(each.key, "_", "-")}"
  retention_in_days = var.log_retention_days
}

resource "aws_ecs_task_definition" "this" {
  for_each                 = local.services
  family                   = "${var.prefix}-${replace(each.key, "_", "-")}"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = tostring(var.cpu)
  memory                   = tostring(var.memory)
  execution_role_arn       = var.execution_role_arn
  task_role_arn            = var.task_role_arn

  # Images are built with `docker build` on the operator's own machine (see
  # scripts/deploy.sh) with no --platform flag, so they match whatever
  # architecture that machine is (arm64 on Apple Silicon, amd64 on Intel/most
  # CI runners). Fargate defaults to X86_64 regardless of what was pushed, so
  # an arm64 image silently fails to pull ("no matching manifest for
  # linux/amd64") unless the task definition says otherwise. ARM64 (Graviton)
  # Fargate is fully supported and typically cheaper than X86_64, so this
  # targets ARM64 to match Apple Silicon builders — if you build on an
  # Intel/amd64 machine instead, change this to "X86_64".
  runtime_platform {
    operating_system_family = "LINUX"
    cpu_architecture        = "ARM64"
  }

  container_definitions = jsonencode([
    {
      name      = each.key
      image     = var.container_images[each.key]
      essential = true
      portMappings = [
        {
          containerPort = each.value.port
          protocol      = "tcp"
        }
      ]
      environment = concat(
        local.common_environment,
        [{ name = "SERVICE_NAME", value = each.value.service_name }],
        lookup(local.extra_environment, each.key, [])
      )
      secrets = concat(
        local.common_secrets,
        [{ name = "DATABASE_URL", valueFrom = var.database_url_arns[each.key] }]
      )
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.this[each.key].name
          "awslogs-region"        = var.region
          "awslogs-stream-prefix" = each.key
        }
      }
    }
  ])
}

resource "aws_ecs_service" "this" {
  for_each        = local.services
  name            = "${var.prefix}-${replace(each.key, "_", "-")}"
  cluster         = aws_ecs_cluster.this.id
  task_definition = aws_ecs_task_definition.this[each.key].arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = var.public_subnet_ids
    security_groups  = [var.ecs_sg_id]
    assign_public_ip = true
  }

  load_balancer {
    target_group_arn = var.target_group_arns[each.key]
    container_name   = each.key
    container_port   = each.value.port
  }

  health_check_grace_period_seconds = 60
}

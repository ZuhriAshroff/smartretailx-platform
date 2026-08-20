############################################
# ALB module — one Application Load Balancer, HTTP :80,
# one target group per microservice, path-based routing
# mirroring the local nginx gateway's /v1/* prefix rules.
############################################

locals {
  # path_pattern values per service — mirrors nginx/nginx.conf routing
  service_paths = {
    user_service         = ["/v1/auth*", "/v1/users*"]
    product_service      = ["/v1/products*"]
    order_service        = ["/v1/orders*"]
    inventory_service    = ["/v1/inventory*"]
    notification_service = ["/v1/notifications*"]
  }

  # listener rule priority per service (order matters only for overlap avoidance)
  service_priority = {
    user_service         = 10
    product_service      = 20
    order_service        = 30
    inventory_service    = 40
    notification_service = 50
  }
}

resource "aws_lb" "this" {
  name               = "${var.prefix}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [var.alb_sg_id]
  subnets            = var.public_subnet_ids

  tags = {
    Name = "${var.prefix}-alb"
  }
}

resource "aws_lb_target_group" "this" {
  for_each = var.service_ports
  # AWS target group names are capped at 32 characters — "${prefix}-${service}-service-tg"
  # would overflow (e.g. "smartretailx-notification-service-tg" = 37 chars), so the
  # redundant "_service" suffix already implied by context is dropped here.
  name        = "${var.prefix}-${replace(trimsuffix(each.key, "_service"), "_", "-")}-tg"
  port        = each.value
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "ip"

  health_check {
    path                = "/v1/health"
    protocol            = "HTTP"
    matcher             = "200"
    interval            = 30
    timeout             = 5
    healthy_threshold   = 2
    unhealthy_threshold = 3
  }

  tags = {
    Name = "${var.prefix}-${replace(each.key, "_", "-")}-tg"
  }
}

resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.this.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type = "fixed-response"

    fixed_response {
      content_type = "application/json"
      status_code  = "404"
      message_body = "{\"service\":\"SmartRetailX API Gateway (ALB)\",\"error\":\"no route matches this path\"}"
    }
  }
}

resource "aws_lb_listener_rule" "this" {
  for_each     = var.service_ports
  listener_arn = aws_lb_listener.http.arn
  priority     = local.service_priority[each.key]

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.this[each.key].arn
  }

  condition {
    path_pattern {
      values = local.service_paths[each.key]
    }
  }
}

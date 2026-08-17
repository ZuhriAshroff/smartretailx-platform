############################################
# SQS module — replaces RabbitMQ's topic exchange.
#
# 4 standard queues, each with exactly ONE consuming
# service (avoids SQS's competing-consumers problem,
# which would otherwise silently steal messages between
# services if two services polled the same queue):
#
#   order-events        <- published on order.*/product.* routing keys
#                          consumed by inventory_service
#                          (needs order.created, product.created)
#   inventory-events     <- published on inventory.* routing keys
#                          consumed by order_service
#                          (needs inventory.reserved, inventory.insufficient)
#   user-events          <- published on user.* routing keys
#                          no active consumer today; provisioned per spec
#   notification-queue   <- published a COPY of every single event here,
#                          mirroring the old wildcard "#" binding;
#                          consumed exclusively by notification_service
############################################

locals {
  queue_defs = {
    order_events       = "order-events"
    inventory_events   = "inventory-events"
    user_events        = "user-events"
    notification_queue = "notification-queue"
  }
}

resource "aws_sqs_queue" "this" {
  for_each = local.queue_defs

  name                       = "${var.prefix}-${each.value}"
  visibility_timeout_seconds = 30
  message_retention_seconds  = 345600 # 4 days
  receive_wait_time_seconds  = 20     # long polling, matches consumer design

  tags = {
    Name = "${var.prefix}-${each.value}"
  }
}

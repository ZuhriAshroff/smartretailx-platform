output "queue_urls" {
  description = "Map keyed by order_events/inventory_events/user_events/notification_queue -> queue URL"
  value       = { for k, v in aws_sqs_queue.this : k => v.id }
}

output "queue_arns" {
  description = "Map keyed by order_events/inventory_events/user_events/notification_queue -> queue ARN"
  value       = { for k, v in aws_sqs_queue.this : k => v.arn }
}

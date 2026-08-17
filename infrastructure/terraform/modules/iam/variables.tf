variable "prefix" {
  type = string
}

variable "region" {
  type = string
}

variable "account_id" {
  type = string
}

variable "ssm_parameter_arns" {
  type        = list(string)
  description = "SSM parameter ARNs (or wildcard prefixes) the ECS roles may read/decrypt"
}

variable "sqs_queue_arns" {
  type        = list(string)
  description = "SQS queue ARNs the task role may send/receive/delete messages on"
}

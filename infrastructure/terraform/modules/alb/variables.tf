variable "prefix" {
  type = string
}

variable "vpc_id" {
  type = string
}

variable "public_subnet_ids" {
  type = list(string)
}

variable "alb_sg_id" {
  type = string
}

variable "service_ports" {
  type        = map(number)
  description = "Map of service key -> container port, e.g. { user_service = 8001, ... }"
}

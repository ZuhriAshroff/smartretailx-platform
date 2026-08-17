variable "prefix" {
  type        = string
  description = "Resource name prefix, e.g. smartretailx"
}

variable "repository_names" {
  type        = list(string)
  description = "Short repo names (without prefix), e.g. [\"user-service\", \"frontend\"]"
}

variable "prefix" {
  type = string
}

variable "account_id" {
  type        = string
  description = "Used to keep the S3 bucket name globally unique"
}

variable "prefix" {
  type        = string
  description = "Resource name prefix, e.g. smartretailx"
}

variable "vpc_cidr" {
  type        = string
  description = "CIDR block for the VPC"
}

variable "availability_zones" {
  type        = list(string)
  description = "Two AZs to spread subnets across, e.g. [\"eu-west-1a\", \"eu-west-1b\"]"
}

variable "public_subnet_cidrs" {
  type        = list(string)
  description = "CIDR blocks for the public subnets (one per AZ)"
}

variable "private_subnet_cidrs" {
  type        = list(string)
  description = "CIDR blocks for the private subnets (one per AZ)"
}

############################################
# VPC module — custom VPC, 2 public + 2 private
# subnets across 2 AZs. No NAT Gateway: ECS
# Fargate tasks run in the PUBLIC subnets with
# public IPs to reach ECR/SQS/SSM/CloudWatch
# directly via the Internet Gateway, avoiding
# the ~$32/mo NAT Gateway cost. Private subnets
# exist only to give RDS a 2-AZ DB subnet group
# (required by AWS even for a single-AZ instance).
############################################

resource "aws_vpc" "this" {
  cidr_block           = var.vpc_cidr
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name = "${var.prefix}-vpc"
  }
}

resource "aws_internet_gateway" "this" {
  vpc_id = aws_vpc.this.id

  tags = {
    Name = "${var.prefix}-igw"
  }
}

resource "aws_subnet" "public" {
  count                   = length(var.availability_zones)
  vpc_id                  = aws_vpc.this.id
  cidr_block              = var.public_subnet_cidrs[count.index]
  availability_zone       = var.availability_zones[count.index]
  map_public_ip_on_launch = true

  tags = {
    Name = "${var.prefix}-public-${var.availability_zones[count.index]}"
    Tier = "public"
  }
}

resource "aws_subnet" "private" {
  count             = length(var.availability_zones)
  vpc_id            = aws_vpc.this.id
  cidr_block        = var.private_subnet_cidrs[count.index]
  availability_zone = var.availability_zones[count.index]

  tags = {
    Name = "${var.prefix}-private-${var.availability_zones[count.index]}"
    Tier = "private"
  }
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.this.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.this.id
  }

  tags = {
    Name = "${var.prefix}-public-rt"
  }
}

resource "aws_route_table_association" "public" {
  count          = length(aws_subnet.public)
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

# Private route table has only the default "local" route (no NAT/IGW route),
# so private-subnet resources have no outbound internet path — fine for RDS,
# which only needs to be reached *from* the VPC, not to reach *out* to it.
resource "aws_route_table" "private" {
  vpc_id = aws_vpc.this.id

  tags = {
    Name = "${var.prefix}-private-rt"
  }
}

resource "aws_route_table_association" "private" {
  count          = length(aws_subnet.private)
  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private.id
}

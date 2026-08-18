############################################
# RDS module — single db.t3.micro Postgres instance,
# 5 databases (one per service), Multi-AZ off, 1-day
# backup retention, free-tier friendly.
#
# DELIBERATE TRADEOFF: this instance is placed in the
# PUBLIC subnets with publicly_accessible = true, restricted
# by security group to (a) the ECS tasks' security group and
# (b) var.db_admin_cidr. This is so `terraform apply` — run
# from the operator's own laptop, with no NAT/bastion/SSM
# tunnel provisioned — can reach it directly to bootstrap the
# 4 extra databases (RDS's `db_name` only creates ONE database;
# psql must create the other 4). A "real" production setup would
# keep RDS in the private subnets and bootstrap via a one-off ECS
# task or Lambda inside the VPC instead. For a cost-minimised course
# assignment this is an accepted, documented simplification —
# narrow var.db_admin_cidr to your own IP in terraform.tfvars rather
# than leaving it at 0.0.0.0/0 once you've done the initial apply.
############################################

resource "aws_db_subnet_group" "this" {
  name       = "${var.prefix}-db-subnet-group"
  subnet_ids = var.subnet_ids

  tags = {
    Name = "${var.prefix}-db-subnet-group"
  }
}

resource "aws_security_group" "rds" {
  name        = "${var.prefix}-rds-sg"
  description = "Allow Postgres from ECS tasks and the admin bootstrap CIDR"
  vpc_id      = var.vpc_id

  ingress {
    description     = "Postgres from ECS tasks"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [var.ecs_sg_id]
  }

  ingress {
    description = "Postgres from admin bootstrap CIDR (DB creation, psql access)"
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = [var.db_admin_cidr]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.prefix}-rds-sg"
  }
}

resource "aws_db_instance" "this" {
  identifier     = "${var.prefix}-db"
  engine         = "postgres"
  engine_version = var.engine_version
  instance_class = var.instance_class

  allocated_storage = 20 # within RDS free tier
  storage_type      = "gp2"

  db_name  = var.initial_database_name
  username = var.db_username
  password = var.db_password
  port     = 5432

  db_subnet_group_name   = aws_db_subnet_group.this.name
  vpc_security_group_ids = [aws_security_group.rds.id]
  publicly_accessible    = true

  multi_az                = false
  backup_retention_period = 1
  skip_final_snapshot     = true
  deletion_protection     = false
  apply_immediately       = true

  tags = {
    Name = "${var.prefix}-db"
  }
}

# The other 4 service databases (RDS only creates `initial_database_name`).
# Requires the `psql` client on the machine running `terraform apply`.
resource "null_resource" "create_additional_databases" {
  for_each = toset([for db in var.service_databases : db if db != var.initial_database_name])

  triggers = {
    db_instance_id = aws_db_instance.this.id
    db_name        = each.value
  }

  provisioner "local-exec" {
    command = <<-EOT
      set -e
      attempt=0
      until PGPASSWORD='${var.db_password}' pg_isready -h ${aws_db_instance.this.address} -p 5432 -U ${var.db_username} >/dev/null 2>&1; do
        attempt=$((attempt+1))
        if [ "$attempt" -ge 30 ]; then
          echo "RDS not reachable after 30 attempts, giving up" >&2
          exit 1
        fi
        echo "Waiting for RDS to accept connections (attempt $attempt/30)..."
        sleep 5
      done
      EXISTS=$(PGPASSWORD='${var.db_password}' psql -h ${aws_db_instance.this.address} -U ${var.db_username} -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname = '${each.value}'")
      if [ "$EXISTS" != "1" ]; then
        PGPASSWORD='${var.db_password}' psql -h ${aws_db_instance.this.address} -U ${var.db_username} -d postgres -c "CREATE DATABASE ${each.value}"
      else
        echo "Database ${each.value} already exists, skipping"
      fi
    EOT
  }

  depends_on = [aws_db_instance.this]
}

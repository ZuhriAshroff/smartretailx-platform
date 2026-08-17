aws_region     = "eu-west-1"
aws_account_id = "651694720482"
prefix         = "smartretailx"

# SECURITY NOTE: 0.0.0.0/0 lets terraform apply's DB-bootstrap step (run from
# your own machine) reach RDS directly, since there's no NAT/bastion/SSM
# tunnel in this cost-minimised setup. After your first successful apply,
# narrow this to your own IP, e.g. "203.0.113.4/32", and re-apply.
db_admin_cidr = "0.0.0.0/0"

image_tag = "latest"

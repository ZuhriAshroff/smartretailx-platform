# SmartRetailX — AWS Deployment

Terraform deployment of the SmartRetailX platform to AWS account
`651694720482` (region `eu-west-1`). Local Terraform state (no S3 backend) —
this is designed to be run from your own machine for a course assignment,
not as a team/CI-managed deployment.

## What gets provisioned

| Component | Notes |
|---|---|
| VPC | Custom VPC, 2 public + 2 private subnets across `eu-west-1a`/`eu-west-1b`, no NAT Gateway |
| ECR | 6 repos (5 services + frontend), image scanning on push, last-10-images lifecycle policy |
| RDS | Single `db.t3.micro` Postgres instance, 5 databases (one per service), Multi-AZ off, 1-day backups |
| SQS | 4 standard queues replacing RabbitMQ (`order-events`, `inventory-events`, `user-events`, `notification-queue`) |
| ECS Fargate | 1 cluster, 5 services (1 task def each), 0.25 vCPU / 512MB, desired count 1 |
| ALB | 1 load balancer, path-based routing to the 5 services (mirrors the local nginx gateway) |
| S3 + CloudFront | Static hosting for the React frontend build (`frontend/dist/`) |
| SSM Parameter Store | JWT secret, DB credentials, per-service DB connection strings, SQS queue URLs — all SecureString |
| IAM | ECS task execution role + task role, scoped to SSM/SQS/CloudWatch Logs |
| CloudWatch | 1 log group per service, 7-day retention |

**Deliberately not provisioned** (cost/complexity tradeoffs for a course
assignment): NAT Gateway, EKS, MSK, ElastiCache, Multi-AZ RDS, autoscaling,
internal service discovery (see "Design tradeoffs" below).

## Prerequisites

- [Terraform](https://developer.hashicorp.com/terraform/downloads) >= 1.5
- AWS CLI v2, configured with credentials for account `651694720482`
  (`aws configure` or `aws sso login`), default region `eu-west-1`
- Docker (for building/pushing images)
- Node.js + npm (for building the frontend)
- `psql` client (used once by Terraform to bootstrap the 4 extra databases —
  `brew install postgresql` on macOS, `apt install postgresql-client` on Debian/Ubuntu)

## Deploy (first time)

From the repo root:

```bash
./scripts/deploy.sh
```

This builds and pushes all 6 Docker images to ECR, applies the full
Terraform stack, then builds and publishes the React frontend to
S3/CloudFront. Takes roughly 10-15 minutes (RDS provisioning is the slowest
part, ~5-10 minutes). At the end it prints the ALB URL (API) and the
CloudFront URL (frontend).

If you'd rather run the steps yourself:

```bash
cd infrastructure/terraform
terraform init
terraform apply -target=module.ecr   # create ECR repos first
# build + push all 6 images (see scripts/deploy.sh for the exact commands)
terraform apply                       # everything else
terraform output alb_dns_name
```

## Pause billing before/after a viva

Fargate compute is the fastest-accumulating cost. Scale it to zero without
tearing anything down:

```bash
./scripts/stop.sh
```

Then, right before your viva/demo:

```bash
./scripts/start.sh
```

Tasks take ~1-2 minutes to pass ALB health checks after starting.

## Full teardown

```bash
./scripts/destroy.sh
```

Prompts for confirmation (type `destroy`), then runs `terraform destroy`.
Stops **all** billing for this project, including RDS. You'll need to run
`./scripts/deploy.sh` again (a full 10-15 minute apply) to bring it back.

## Rough cost estimate

Everything here is chosen to be free-tier-eligible or single-digit-dollars a
day, but AWS free tier only fully covers the first 12 months on a new
account and specific usage caps — treat this as a rough estimate, not a
guarantee:

- **RDS db.t3.micro**: free tier covers 750 hrs/month for 12 months; after
  that (or outside free tier) roughly $0.017/hr ≈ $12-13/month running 24/7.
  This is the main cost that persists even when ECS is stopped.
- **ALB**: ~$0.0225/hr (~$16/month) + a small per-GB data cost — the ALB
  itself is not in the free tier, so this runs whether or not ECS tasks are up.
- **Fargate (5 tasks × 0.25 vCPU/512MB)**: ~$0.012/vCPU-hr + ~$0.0013/GB-hr
  → roughly $0.30-0.40/day for all 5 tasks running continuously. Zero when
  scaled to 0 via `scripts/stop.sh`.
- **SQS, SSM, CloudWatch Logs (7-day retention), ECR storage**: all
  comfortably within free tier for this traffic volume.
- **S3 + CloudFront**: a few cents for a small SPA build, free tier covers
  typical demo traffic.

**Bottom line**: expect low-single-digit dollars for a day of active
demo/viva use, and mainly the RDS + ALB baseline (~$1/day combined outside
free tier) while paused via `scripts/stop.sh`. Run `scripts/destroy.sh` when
you're fully done to stop everything.

## Design tradeoffs (worth mentioning in your report/viva)

- **No NAT Gateway**: ECS tasks run in the public subnets with
  `assign_public_ip = true` instead of a NAT Gateway (~$32/month + data
  processing), which would otherwise dwarf every other cost in this stack for
  a low-traffic demo. Tasks reach RDS via the VPC's local route (no NAT
  needed for in-VPC traffic) and reach ECR/SQS/SSM/CloudWatch over the public
  internet via the Internet Gateway. Inbound access to tasks is still locked
  down to the ALB's security group only.
- **RDS is publicly accessible** (in the public subnets, security-group
  restricted): `terraform apply` runs from your own laptop with no
  NAT/bastion/SSM-tunnel provisioned, and needs to reach Postgres directly to
  create the 4 extra service databases (RDS's `db_name` only creates one). A
  production setup would keep RDS private and bootstrap via a one-off ECS
  task or Lambda inside the VPC instead. **Narrow `db_admin_cidr` in
  `terraform.tfvars` from `0.0.0.0/0` to your own IP/32 after the first
  apply.**
- **No internal service discovery**: `order_service`'s calls to
  `product_service` (for pricing) are routed back out through the public ALB
  (`PRODUCT_SERVICE_URL=http://<alb-dns>`) rather than a private DNS
  namespace (AWS Cloud Map / ECS Service Connect), since that would add
  cost/complexity for one inter-service call in a demo-scale system.
- **Shared RDS instance, one DB per service**: keeps the whole platform on
  one free-tier-eligible `db.t3.micro` rather than 5 separate instances,
  matching the "one database per service" ownership model at the schema
  level even though they share a physical instance.
- **No autoscaling / Multi-AZ**: desired count is fixed at 1 per service,
  RDS is single-AZ — appropriate for a cost-minimised course deployment, not
  for production availability targets.

## Messaging: RabbitMQ (local) vs SQS (AWS)

Every service supports both brokers via `MESSAGE_BROKER=rabbitmq|sqs`
(`libs/common/messaging.py` is the facade; see the root `README.md` for the
full local RabbitMQ behaviour). The Terraform ECS task definitions set
`MESSAGE_BROKER=sqs` and inject the 4 SQS queue URLs via SSM. Queue mapping
(each queue has exactly one consuming service, to avoid SQS's competing-consumers
problem stealing messages between services):

| Queue | Carries | Consumed by |
|---|---|---|
| `smartretailx-order-events` | `order.*`, `product.*` | inventory_service |
| `smartretailx-inventory-events` | `inventory.*` | order_service |
| `smartretailx-user-events` | `user.*` | (provisioned per spec; no active consumer today) |
| `smartretailx-notification-queue` | a copy of every event | notification_service |

## SSM Parameter Store layout

All under `/smartretailx/`:

- `/smartretailx/jwt_secret_key` — shared JWT signing secret (random, generated by Terraform)
- `/smartretailx/db_username`, `/smartretailx/db_password` — RDS master credentials
- `/smartretailx/database_url/<service>` — full `DATABASE_URL` per service (composed connection string, so the password never appears as a plain ECS env var)
- `/smartretailx/sqs/order_events_url`, `/smartretailx/sqs/inventory_events_url`, `/smartretailx/sqs/user_events_url`, `/smartretailx/sqs/notification_queue_url`

ECS task execution roles resolve these via the task definition's `secrets`
block; the task role additionally has direct SSM/SQS read access for the
application code itself.

## Terraform module layout

```
infrastructure/terraform/
├── main.tf              # wires all modules + root-level security groups + SSM parameters
├── variables.tf
├── outputs.tf            # alb_dns_name, cloudfront_domain_name, ecr_repository_urls, etc.
├── terraform.tfvars
└── modules/
    ├── vpc/              # VPC, subnets, IGW, route tables
    ├── ecr/              # 6 image repositories
    ├── sqs/               # 4 standard queues
    ├── rds/               # single Postgres instance + 5 databases
    ├── iam/               # ECS execution + task roles
    ├── alb/               # load balancer, target groups, path-based routing
    ├── ecs/               # cluster, task definitions, services
    └── s3-cloudfront/     # frontend static hosting
```

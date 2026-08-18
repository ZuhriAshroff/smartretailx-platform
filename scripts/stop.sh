#!/usr/bin/env bash
# Scales all ECS services to desired_count=0 to stop Fargate compute billing
# without destroying any infrastructure. Cheaper than a destroy/apply cycle
# when you just need to pause for a few days — RDS, ALB, SQS, S3, CloudFront,
# ECR keep running (RDS is the main remaining cost, a few cents/day on
# db.t3.micro).
#
# Usage: ./scripts/stop.sh   (run from the repo root)
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TF_DIR="$REPO_ROOT/infrastructure/terraform"
AWS_REGION="eu-west-1"

cd "$TF_DIR"
CLUSTER="$(terraform output -raw ecs_cluster_name)"
SERVICE_NAMES="$(terraform output -json ecs_service_names | python3 -c 'import json,sys; print("\n".join(json.load(sys.stdin).values()))')"

echo "Scaling down ECS services in cluster ${CLUSTER}..."
while IFS= read -r service; do
  [ -z "$service" ] && continue
  echo "    ${service} -> desired_count=0"
  aws ecs update-service --cluster "$CLUSTER" --service "$service" --desired-count 0 --region "$AWS_REGION" >/dev/null
done <<< "$SERVICE_NAMES"

echo ""
echo "All ECS services scaled to 0. Fargate compute billing has stopped."
echo "RDS, ALB, SQS, S3, CloudFront and ECR are still running (RDS is the"
echo "main remaining cost). Run scripts/start.sh to bring services back up."

#!/usr/bin/env bash
# Scales all ECS services back to desired_count=1 — spins compute back up
# before a viva/demo without a full terraform apply.
#
# Usage: ./scripts/start.sh   (run from the repo root)
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TF_DIR="$REPO_ROOT/infrastructure/terraform"
AWS_REGION="eu-west-1"

cd "$TF_DIR"
CLUSTER="$(terraform output -raw ecs_cluster_name)"
ALB_DNS="$(terraform output -raw alb_dns_name)"
SERVICE_NAMES="$(terraform output -json ecs_service_names | python3 -c 'import json,sys; print("\n".join(json.load(sys.stdin).values()))')"

echo "Scaling up ECS services in cluster ${CLUSTER}..."
while IFS= read -r service; do
  [ -z "$service" ] && continue
  echo "    ${service} -> desired_count=1"
  aws ecs update-service --cluster "$CLUSTER" --service "$service" --desired-count 1 --region "$AWS_REGION" >/dev/null
done <<< "$SERVICE_NAMES"

echo ""
echo "All ECS services scaling up. Tasks typically take 1-2 minutes to pass"
echo "health checks and register with the ALB."
echo ""
echo "API base URL: http://${ALB_DNS}"
echo "Check status with: aws ecs describe-services --cluster ${CLUSTER} --services <name> --region ${AWS_REGION}"

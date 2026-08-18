#!/usr/bin/env bash
# Tears down every AWS resource created for SmartRetailX and stops all billing.
#
# Usage: ./scripts/destroy.sh   (run from the repo root)
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TF_DIR="$REPO_ROOT/infrastructure/terraform"

echo "This will DESTROY all SmartRetailX AWS infrastructure (VPC, RDS, ECS,"
echo "ALB, SQS, S3, CloudFront, ECR repos and everything in them, IAM roles,"
echo "SSM parameters). This cannot be undone."
echo ""
read -r -p "Type 'destroy' to confirm: " CONFIRMATION

if [ "$CONFIRMATION" != "destroy" ]; then
  echo "Aborted — no changes made."
  exit 1
fi

cd "$TF_DIR"
terraform destroy -auto-approve

echo ""
echo "Done. All AWS billing for this project has stopped."

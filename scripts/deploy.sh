#!/usr/bin/env bash
# Builds and pushes all 6 Docker images to ECR, applies the full Terraform
# stack, then builds and publishes the React frontend to S3/CloudFront.
#
# Usage: ./scripts/deploy.sh   (run from the repo root)
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TF_DIR="$REPO_ROOT/infrastructure/terraform"
AWS_REGION="eu-west-1"
AWS_ACCOUNT_ID="651694720482"
ECR_REGISTRY="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

echo "==> [1/6] terraform init"
cd "$TF_DIR"
terraform init -input=false

echo "==> [2/6] Creating ECR repositories first (images must exist before ECS can start)"
terraform apply -auto-approve -target=module.ecr

echo "==> [3/6] Logging in to ECR"
aws ecr get-login-password --region "$AWS_REGION" | docker login --username AWS --password-stdin "$ECR_REGISTRY"

echo "==> [4/6] Building and pushing service images"
# Plain indexed arrays (not associative) — macOS ships bash 3.2 by default,
# which has no `declare -A` support at all.
SERVICE_NAMES=(user-service product-service order-service inventory-service notification-service)
SERVICE_DOCKERFILES=(
  "services/user_service/Dockerfile"
  "services/product_service/Dockerfile"
  "services/order_service/Dockerfile"
  "services/inventory_service/Dockerfile"
  "services/notification_service/Dockerfile"
)

for i in "${!SERVICE_NAMES[@]}"; do
  name="${SERVICE_NAMES[$i]}"
  dockerfile="${SERVICE_DOCKERFILES[$i]}"
  image="${ECR_REGISTRY}/smartretailx-${name}:latest"
  echo "    building ${name}..."
  docker build -f "$REPO_ROOT/$dockerfile" -t "$image" "$REPO_ROOT"
  echo "    pushing ${name}..."
  docker push "$image"
done

echo "    building frontend..."
frontend_image="${ECR_REGISTRY}/smartretailx-frontend:latest"
docker build -f "$REPO_ROOT/frontend/Dockerfile" -t "$frontend_image" "$REPO_ROOT/frontend"
echo "    pushing frontend..."
docker push "$frontend_image"

echo "==> [5/6] terraform apply (full stack — VPC, RDS, SQS, ECS, ALB, S3/CloudFront, IAM, SSM)"
cd "$TF_DIR"
terraform apply -auto-approve

ALB_DNS="$(terraform output -raw alb_dns_name)"
BUCKET_NAME="$(terraform output -raw frontend_bucket_name)"
DISTRIBUTION_ID="$(terraform output -raw cloudfront_distribution_id)"
CLOUDFRONT_DOMAIN="$(terraform output -raw cloudfront_domain_name)"

echo "==> [6/6] Building and publishing the React frontend"
cd "$REPO_ROOT/frontend"
npm ci
# Point the frontend at the CloudFront domain, NOT the raw ALB DNS. CloudFront
# proxies /v1/* to the ALB (see modules/s3-cloudfront) — this matters because
# the frontend is served over HTTPS, and a browser blocks an HTTPS page from
# calling a plain-HTTP API as "mixed content". Same CloudFront origin for both
# the app and its API calls sidesteps that (and CORS, since it's same-origin).
VITE_API_BASE_URL="https://${CLOUDFRONT_DOMAIN}" npm run build
aws s3 sync dist/ "s3://${BUCKET_NAME}/" --delete
aws cloudfront create-invalidation --distribution-id "$DISTRIBUTION_ID" --paths "/*" >/dev/null

echo ""
echo "================================================================"
echo " Deploy complete."
echo "   API (direct ALB, HTTP, for testing only): http://${ALB_DNS}"
echo "   Frontend + API (HTTPS):                   https://${CLOUDFRONT_DOMAIN}"
echo ""
echo " CloudFront can take a few minutes to finish propagating."
echo " Run scripts/stop.sh before you leave it idle to pause ECS billing."
echo "================================================================"

############################################
# S3 module — hosts the React frontend build
# (frontend/dist/) as a plain S3 static website.
#
# TEMPORARY FALLBACK: this was originally CloudFront + OAC (private bucket,
# HTTPS, same-origin proxy to the ALB under /v1/*). CloudFront distribution
# creation is currently blocked on this AWS account ("Your account must be
# verified before you can add new CloudFront resources" — an account-level
# restriction pending an AWS Support case, not a Terraform/config issue).
#
# S3 static website hosting needs a public bucket (no OAC/CloudFront in
# front), and has no HTTPS of its own. Since the ALB is also HTTP-only, the
# frontend and API are both plain HTTP here — no mixed-content issue, but
# they ARE different origins now (no CloudFront to make them same-origin),
# so each backend service must send CORS headers itself (see
# libs/common/cors.py, wired via CORS_ALLOWED_ORIGINS in modules/ecs).
#
# React Router's client-side routes need a 200 on unknown paths (deep-link/
# refresh); S3 website hosting's error_document serves index.html for that,
# though (unlike CloudFront's custom_error_response) it keeps the real 404
# status code rather than rewriting it to 200 — cosmetic only, doesn't
# break client-side routing.
#
# Switch back to CloudFront once the account is verified: restore the OAC +
# aws_cloudfront_distribution resources and the private bucket policy, and
# swap modules/ecs's frontend_origin back to the CloudFront domain.
############################################

resource "aws_s3_bucket" "frontend" {
  bucket = "${var.prefix}-frontend-${var.account_id}"

  tags = {
    Name = "${var.prefix}-frontend"
  }
}

# Static website hosting requires a public bucket policy, so public policy
# access can't be blocked (ACLs stay blocked — access is via bucket policy).
resource "aws_s3_bucket_public_access_block" "frontend" {
  bucket                  = aws_s3_bucket.frontend.id
  block_public_acls       = true
  block_public_policy     = false
  ignore_public_acls      = true
  restrict_public_buckets = false
}

resource "aws_s3_bucket_website_configuration" "frontend" {
  bucket = aws_s3_bucket.frontend.id

  index_document {
    suffix = "index.html"
  }

  # SPA fallback: unknown paths (React Router) still serve the app shell.
  error_document {
    key = "index.html"
  }
}

data "aws_iam_policy_document" "frontend_bucket_policy" {
  statement {
    sid       = "PublicReadGetObject"
    actions   = ["s3:GetObject"]
    resources = ["${aws_s3_bucket.frontend.arn}/*"]

    principals {
      type        = "*"
      identifiers = ["*"]
    }
  }
}

resource "aws_s3_bucket_policy" "frontend" {
  bucket     = aws_s3_bucket.frontend.id
  policy     = data.aws_iam_policy_document.frontend_bucket_policy.json
  depends_on = [aws_s3_bucket_public_access_block.frontend]
}

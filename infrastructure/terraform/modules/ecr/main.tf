############################################
# ECR module — one repo per service (5) + one
# for the frontend (used for local-dev/preview
# container builds; production frontend hosting
# is via S3+CloudFront, see s3-cloudfront module).
############################################

resource "aws_ecr_repository" "this" {
  for_each             = toset(var.repository_names)
  name                 = "${var.prefix}-${each.value}"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Name = "${var.prefix}-${each.value}"
  }
}

# Keep storage/cost bounded: retain only the last 10 images per repo.
resource "aws_ecr_lifecycle_policy" "this" {
  for_each   = aws_ecr_repository.this
  repository = each.value.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep last 10 images"
        selection = {
          tagStatus   = "any"
          countType   = "imageCountMoreThan"
          countNumber = 10
        }
        action = { type = "expire" }
      }
    ]
  })
}

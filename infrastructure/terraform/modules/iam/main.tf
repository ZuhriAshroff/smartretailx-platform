############################################
# IAM module — ECS task execution role (used by the
# ECS agent to pull images, resolve SSM secrets, and
# write bootstrap logs) and task role (used by the
# application code itself at runtime, via the container's
# AWS SDK credentials, to read SSM params and call SQS).
############################################

data "aws_iam_policy_document" "ecs_tasks_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}

# The AWS-managed key behind SSM SecureString parameters when no
# customer KMS key is specified — the execution role needs Decrypt
# on it to resolve `secrets` blocks in the task definition.
data "aws_kms_alias" "ssm" {
  name = "alias/aws/ssm"
}

############################
# Execution role
############################

resource "aws_iam_role" "execution" {
  name               = "${var.prefix}-ecs-execution-role"
  assume_role_policy = data.aws_iam_policy_document.ecs_tasks_assume.json
}

resource "aws_iam_role_policy_attachment" "execution_managed" {
  role       = aws_iam_role.execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

data "aws_iam_policy_document" "execution_ssm" {
  statement {
    sid       = "ReadSecretsForTaskStartup"
    actions   = ["ssm:GetParameters", "ssm:GetParameter", "ssm:GetParametersByPath"]
    resources = var.ssm_parameter_arns
  }

  statement {
    sid       = "DecryptSecureStringParams"
    actions   = ["kms:Decrypt"]
    resources = [data.aws_kms_alias.ssm.target_key_arn]
  }
}

resource "aws_iam_role_policy" "execution_ssm" {
  name   = "${var.prefix}-ecs-execution-ssm"
  role   = aws_iam_role.execution.id
  policy = data.aws_iam_policy_document.execution_ssm.json
}

############################
# Task role (application runtime)
############################

resource "aws_iam_role" "task" {
  name               = "${var.prefix}-ecs-task-role"
  assume_role_policy = data.aws_iam_policy_document.ecs_tasks_assume.json
}

data "aws_iam_policy_document" "task_permissions" {
  statement {
    sid       = "ReadSsmParameters"
    actions   = ["ssm:GetParameter", "ssm:GetParameters", "ssm:GetParametersByPath"]
    resources = var.ssm_parameter_arns
  }

  statement {
    sid       = "UseSqsQueues"
    actions   = ["sqs:SendMessage", "sqs:ReceiveMessage", "sqs:DeleteMessage", "sqs:GetQueueAttributes"]
    resources = var.sqs_queue_arns
  }

  statement {
    sid       = "WriteCloudWatchLogs"
    actions   = ["logs:CreateLogStream", "logs:PutLogEvents"]
    resources = ["arn:aws:logs:${var.region}:${var.account_id}:log-group:/ecs/${var.prefix}-*:*"]
  }
}

resource "aws_iam_role_policy" "task_permissions" {
  name   = "${var.prefix}-ecs-task-permissions"
  role   = aws_iam_role.task.id
  policy = data.aws_iam_policy_document.task_permissions.json
}

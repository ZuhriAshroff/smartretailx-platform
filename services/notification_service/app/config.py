import os

SERVICE_NAME = os.getenv("SERVICE_NAME", "notification-service")
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://smartretailx:smartretailx@localhost:5432/notification_service",
)
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://smartretailx:smartretailx@localhost:5672/%2F")
OPS_TEAM_EMAIL = os.getenv("OPS_TEAM_EMAIL", "ops@smartretailx.com")
WAREHOUSE_TEAM_EMAIL = os.getenv("WAREHOUSE_TEAM_EMAIL", "warehouse@smartretailx.com")

# Messaging backend: "rabbitmq" (default, local docker-compose) or "sqs" (AWS).
# SQS_QUEUE_URL_* are only read (by libs.common.sqs) when MESSAGE_BROKER=sqs.
MESSAGE_BROKER = os.getenv("MESSAGE_BROKER", "rabbitmq")
AWS_REGION = os.getenv("AWS_REGION", "eu-west-1")
SQS_QUEUE_URL_NOTIFICATION_QUEUE = os.getenv("SQS_QUEUE_URL_NOTIFICATION_QUEUE", "")

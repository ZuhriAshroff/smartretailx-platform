import os

SERVICE_NAME = os.getenv("SERVICE_NAME", "inventory-management-service")
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://smartretailx:smartretailx@localhost:5432/inventory_service",
)
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://smartretailx:smartretailx@localhost:5672/%2F")
DEFAULT_REORDER_LEVEL = int(os.getenv("DEFAULT_REORDER_LEVEL", "10"))

# Messaging backend: "rabbitmq" (default, local docker-compose) or "sqs" (AWS).
# SQS_QUEUE_URL_* are only read (by libs.common.sqs) when MESSAGE_BROKER=sqs.
MESSAGE_BROKER = os.getenv("MESSAGE_BROKER", "rabbitmq")
AWS_REGION = os.getenv("AWS_REGION", "eu-west-1")
SQS_QUEUE_URL_ORDER_EVENTS = os.getenv("SQS_QUEUE_URL_ORDER_EVENTS", "")
SQS_QUEUE_URL_INVENTORY_EVENTS = os.getenv("SQS_QUEUE_URL_INVENTORY_EVENTS", "")
SQS_QUEUE_URL_NOTIFICATION_QUEUE = os.getenv("SQS_QUEUE_URL_NOTIFICATION_QUEUE", "")

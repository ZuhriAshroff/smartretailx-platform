"""AWS SQS messaging backend: standard-queue publisher and long-polling consumer.

Replaces the RabbitMQ topic-exchange fan-out with 4 pre-provisioned standard
queues (see infrastructure/terraform's sqs module). Because SQS delivers each
message to exactly one consumer (no broadcast like a topic exchange), each of
the 4 queues is owned by exactly one consuming service - this mirrors the
existing RabbitMQ design, where every service already declares its own
exclusive, durable queue bound only to the routing keys it needs:

    Queue env var                        Carries              Consumed by
    SQS_QUEUE_URL_ORDER_EVENTS           order.*, product.*   inventory_service
    SQS_QUEUE_URL_INVENTORY_EVENTS       inventory.*          order_service
    SQS_QUEUE_URL_USER_EVENTS            user.*               (none active today)
    SQS_QUEUE_URL_NOTIFICATION_QUEUE     every event (copy)   notification_service

A publish() call fans a message out to the notification queue (always) plus
whichever domain queue matches the routing key's prefix - this replaces the
notification service's wildcard "#" binding and the domain-specific bindings
in one pass. Message bodies are the same JSON payload used for RabbitMQ; since
every publisher already includes an "event" key equal to the routing key, the
consumer dispatches on payload["event"] without needing SQS MessageAttributes.
"""
from __future__ import annotations

import json
import logging
import os
import threading
import time
from typing import Callable

import boto3

logger = logging.getLogger("smartretailx.sqs")

EventHandler = Callable[[str, dict], None]

AWS_REGION = os.getenv("AWS_REGION", "eu-west-1")

_QUEUE_ENV_VARS = {
    "order_events": "SQS_QUEUE_URL_ORDER_EVENTS",
    "inventory_events": "SQS_QUEUE_URL_INVENTORY_EVENTS",
    "user_events": "SQS_QUEUE_URL_USER_EVENTS",
    "notification_queue": "SQS_QUEUE_URL_NOTIFICATION_QUEUE",
}

# Logical consumer queue_name (as passed by each service's consumers.py) ->
# the domain queue env var that service actually needs to poll.
_CONSUMER_QUEUE_MAP = {
    "order_service.events": "SQS_QUEUE_URL_INVENTORY_EVENTS",
    "inventory_service.events": "SQS_QUEUE_URL_ORDER_EVENTS",
    "notification_service.events": "SQS_QUEUE_URL_NOTIFICATION_QUEUE",
}


def _client():
    return boto3.client("sqs", region_name=AWS_REGION)


def _target_queue_env_vars(routing_key: str) -> list[str]:
    targets = [_QUEUE_ENV_VARS["notification_queue"]]
    if routing_key.startswith("order.") or routing_key.startswith("product."):
        targets.append(_QUEUE_ENV_VARS["order_events"])
    if routing_key.startswith("inventory."):
        targets.append(_QUEUE_ENV_VARS["inventory_events"])
    if routing_key.startswith("user."):
        targets.append(_QUEUE_ENV_VARS["user_events"])
    return targets


class SQSPublisher:
    """boto3-backed publisher. Lazily creates its client on first use."""

    def __init__(self):
        self._client = None
        self._lock = threading.Lock()

    def _ensure_client(self):
        if self._client is None:
            self._client = _client()
        return self._client

    def publish(self, routing_key: str, payload: dict) -> None:
        body = json.dumps(payload, default=str)
        with self._lock:
            client = self._ensure_client()
            for env_var in _target_queue_env_vars(routing_key):
                queue_url = os.getenv(env_var, "")
                if not queue_url:
                    logger.warning(
                        "Skipping publish of '%s' to %s: env var not set", routing_key, env_var
                    )
                    continue
                try:
                    client.send_message(QueueUrl=queue_url, MessageBody=body)
                    logger.info("Published event '%s' to %s", routing_key, env_var)
                except Exception:
                    logger.exception("Failed to publish '%s' to %s", routing_key, env_var)


def _consume_forever(queue_url: str, handler: EventHandler) -> None:
    client = _client()
    logger.info("SQS consumer polling queue %s", queue_url)
    while True:
        try:
            response = client.receive_message(
                QueueUrl=queue_url,
                MaxNumberOfMessages=10,
                WaitTimeSeconds=20,
            )
            messages = response.get("Messages", [])
            for message in messages:
                receipt_handle = message["ReceiptHandle"]
                try:
                    payload = json.loads(message["Body"])
                    handler(payload.get("event", ""), payload)
                except Exception:
                    logger.exception("Error handling SQS message on %s, dropping it", queue_url)
                finally:
                    # Always delete: mirrors the RabbitMQ consumer's
                    # nack-without-requeue-on-error semantics (process once, drop).
                    try:
                        client.delete_message(QueueUrl=queue_url, ReceiptHandle=receipt_handle)
                    except Exception:
                        logger.exception("Failed to delete SQS message from %s", queue_url)
        except Exception:
            logger.exception("Unexpected error polling %s, retrying in 5s...", queue_url)
            time.sleep(5)


def start_sqs_consumer_thread(queue_name: str, handler: EventHandler) -> threading.Thread:
    env_var = _CONSUMER_QUEUE_MAP.get(queue_name)
    if env_var is None:
        raise ValueError(f"No SQS queue mapping for logical queue_name '{queue_name}'")
    queue_url = os.getenv(env_var, "")
    if not queue_url:
        raise RuntimeError(f"{env_var} is not set; cannot start SQS consumer for '{queue_name}'")

    thread = threading.Thread(
        target=_consume_forever,
        args=(queue_url, handler),
        name=f"sqs-consumer-{queue_name}",
        daemon=True,
    )
    thread.start()
    return thread

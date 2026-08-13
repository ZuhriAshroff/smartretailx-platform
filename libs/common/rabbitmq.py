"""RabbitMQ helpers: retrying connections, event publishing, and background consumers.

All services publish/consume on a single durable topic exchange
("smartretailx.events"). Routing keys are dotted event names, e.g.
"order.created", "inventory.reserved", "user.registered".

Consumers are started as daemon background threads on FastAPI startup and run
a reconnect loop for the lifetime of the process, so a RabbitMQ restart (or a
slow start where RabbitMQ isn't ready yet when the service boots) is handled
transparently.
"""
from __future__ import annotations

import json
import logging
import threading
import time
from typing import Callable

import pika
from pika.adapters.blocking_connection import BlockingChannel
from pika.exceptions import AMQPConnectionError

logger = logging.getLogger("smartretailx.rabbitmq")

EXCHANGE_NAME = "smartretailx.events"
EXCHANGE_TYPE = "topic"

EventHandler = Callable[[str, dict], None]


def _connection_params(rabbitmq_url: str) -> pika.URLParameters:
    return pika.URLParameters(rabbitmq_url)


def connect_with_retry(rabbitmq_url: str, retries: int = 30, delay_seconds: float = 3.0) -> pika.BlockingConnection:
    attempt = 0
    while True:
        attempt += 1
        try:
            connection = pika.BlockingConnection(_connection_params(rabbitmq_url))
            logger.info("Connected to RabbitMQ after %d attempt(s)", attempt)
            return connection
        except AMQPConnectionError as exc:
            if attempt >= retries:
                logger.error("RabbitMQ unreachable after %d attempts, giving up", attempt)
                raise
            logger.warning(
                "RabbitMQ not ready (attempt %d/%d): %s. Retrying in %.1fs...",
                attempt, retries, exc, delay_seconds,
            )
            time.sleep(delay_seconds)


def declare_exchange(channel: BlockingChannel) -> None:
    channel.exchange_declare(exchange=EXCHANGE_NAME, exchange_type=EXCHANGE_TYPE, durable=True)


class EventPublisher:
    """A small wrapper that owns a single retried connection for publishing events.

    A fresh channel is (re)established lazily and recreated automatically if the
    underlying connection has died, so callers don't need their own retry logic.
    """

    def __init__(self, rabbitmq_url: str):
        self._rabbitmq_url = rabbitmq_url
        self._connection: pika.BlockingConnection | None = None
        self._lock = threading.Lock()

    def _ensure_connection(self) -> BlockingChannel:
        if self._connection is None or self._connection.is_closed:
            self._connection = connect_with_retry(self._rabbitmq_url)
        channel = self._connection.channel()
        declare_exchange(channel)
        return channel

    def publish(self, routing_key: str, payload: dict) -> None:
        with self._lock:
            try:
                channel = self._ensure_connection()
                channel.basic_publish(
                    exchange=EXCHANGE_NAME,
                    routing_key=routing_key,
                    body=json.dumps(payload, default=str),
                    properties=pika.BasicProperties(
                        content_type="application/json",
                        delivery_mode=2,  # persistent
                    ),
                )
                logger.info("Published event '%s': %s", routing_key, payload)
            except AMQPConnectionError:
                logger.warning("Publish failed due to connection error, reconnecting and retrying once")
                self._connection = connect_with_retry(self._rabbitmq_url)
                channel = self._connection.channel()
                declare_exchange(channel)
                channel.basic_publish(
                    exchange=EXCHANGE_NAME,
                    routing_key=routing_key,
                    body=json.dumps(payload, default=str),
                    properties=pika.BasicProperties(content_type="application/json", delivery_mode=2),
                )


def _consume_forever(
    rabbitmq_url: str,
    queue_name: str,
    routing_keys: list[str],
    handler: EventHandler,
) -> None:
    while True:
        try:
            connection = connect_with_retry(rabbitmq_url)
            channel = connection.channel()
            declare_exchange(channel)
            channel.queue_declare(queue=queue_name, durable=True)
            for routing_key in routing_keys:
                channel.queue_bind(exchange=EXCHANGE_NAME, queue=queue_name, routing_key=routing_key)
            channel.basic_qos(prefetch_count=10)

            def _on_message(ch, method, properties, body, _handler=handler):
                try:
                    payload = json.loads(body)
                    _handler(method.routing_key, payload)
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                except Exception:
                    logger.exception("Error handling event on queue '%s', nacking without requeue", queue_name)
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

            channel.basic_consume(queue=queue_name, on_message_callback=_on_message)
            logger.info("Consumer for queue '%s' listening on routing keys %s", queue_name, routing_keys)
            channel.start_consuming()
        except AMQPConnectionError:
            logger.warning("Consumer for queue '%s' lost connection, reconnecting in 3s...", queue_name)
            time.sleep(3)
        except Exception:
            logger.exception("Unexpected error in consumer '%s', restarting in 5s...", queue_name)
            time.sleep(5)


def start_consumer_thread(
    rabbitmq_url: str,
    queue_name: str,
    routing_keys: list[str],
    handler: EventHandler,
) -> threading.Thread:
    thread = threading.Thread(
        target=_consume_forever,
        args=(rabbitmq_url, queue_name, routing_keys, handler),
        name=f"consumer-{queue_name}",
        daemon=True,
    )
    thread.start()
    return thread

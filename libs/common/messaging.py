"""Broker-agnostic messaging facade.

Every service imports EventPublisher / start_consumer_thread from here
instead of from libs.common.rabbitmq directly. The MESSAGE_BROKER env var
("rabbitmq", the default, for local docker-compose; or "sqs" for AWS)
selects the implementation at call time - callers don't need to know which
broker is in play, and the public API (constructor args, publish(), and
start_consumer_thread() signature) is identical either way so switching
brokers is a zero-code-change, env-var-only operation.
"""
from __future__ import annotations

import os
import threading

from libs.common import rabbitmq as _rabbitmq
from libs.common import sqs as _sqs


def _broker() -> str:
    return os.getenv("MESSAGE_BROKER", "rabbitmq").lower()


class EventPublisher:
    """Publishes events on whichever broker MESSAGE_BROKER selects.

    Construction never touches the network (RabbitMQ connects lazily on
    first publish; the SQS client is likewise created lazily) - this matters
    because services build `publisher = EventPublisher(RABBITMQ_URL)` at
    module import time, and tests monkeypatch `publisher.publish` afterward
    without ever expecting a real connection attempt.
    """

    def __init__(self, rabbitmq_url: str | None = None):
        if _broker() == "sqs":
            self._impl = _sqs.SQSPublisher()
        else:
            self._impl = _rabbitmq.EventPublisher(rabbitmq_url)

    def publish(self, routing_key: str, payload: dict) -> None:
        self._impl.publish(routing_key, payload)


def start_consumer_thread(
    rabbitmq_url: str,
    queue_name: str,
    routing_keys: list[str],
    handler,
) -> threading.Thread:
    """Starts a background consumer thread on whichever broker MESSAGE_BROKER selects.

    In SQS mode, `rabbitmq_url` and `routing_keys` are ignored: the routing
    decision already happened at publish time (which queue a message landed
    in), and `queue_name` is mapped to the correct SQS queue URl internally.
    """
    if _broker() == "sqs":
        return _sqs.start_sqs_consumer_thread(queue_name, handler)
    return _rabbitmq.start_consumer_thread(rabbitmq_url, queue_name, routing_keys, handler)

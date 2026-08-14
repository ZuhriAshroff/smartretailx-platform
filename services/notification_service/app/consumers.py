"""Background RabbitMQ consumer for the Notification Service.

This service binds its queue to the wildcard routing key "#", so it receives
EVERY event published on the "smartretailx.events" exchange by every other
service. Each event type is translated into a stored notification record,
simulating an outbound email/SMS/push send (logged rather than actually
dispatched, since there is no real mail provider in this environment).
"""
import logging

from app import crud
from app.config import OPS_TEAM_EMAIL, RABBITMQ_URL, WAREHOUSE_TEAM_EMAIL
from app.database import SessionLocal
from libs.common.messaging import start_consumer_thread

logger = logging.getLogger("notification_service.consumers")

QUEUE_NAME = "notification_service.events"
ROUTING_KEYS = ["#"]


def _send(event_type: str, subject: str, message: str, recipient_user_id=None, recipient_email=None) -> None:
    db = SessionLocal()
    try:
        crud.create_notification(
            db,
            event_type=event_type,
            subject=subject,
            message=message,
            recipient_user_id=recipient_user_id,
            recipient_email=recipient_email,
        )
        logger.info("Notification stored [%s] -> user=%s email=%s: %s", event_type, recipient_user_id, recipient_email, subject)
    finally:
        db.close()


def _handle_user_registered(payload: dict) -> None:
    _send(
        "user.registered",
        subject="Welcome to SmartRetailX",
        message=f"Hi {payload.get('full_name', 'there')}, your account has been created with role '{payload.get('role')}'.",
        recipient_user_id=payload.get("user_id"),
        recipient_email=payload.get("email"),
    )


def _handle_order_created(payload: dict) -> None:
    _send(
        "order.created",
        subject=f"Order #{payload['order_id']} received",
        message=f"Your order #{payload['order_id']} has been received and is pending confirmation.",
        recipient_user_id=payload.get("customer_id"),
    )


def _handle_order_status_changed(payload: dict) -> None:
    _send(
        "order.status_changed",
        subject=f"Order #{payload['order_id']} status update",
        message=(
            f"Your order #{payload['order_id']} status changed from "
            f"'{payload['old_status']}' to '{payload['new_status']}'."
        ),
        recipient_user_id=payload.get("customer_id"),
    )


def _handle_inventory_insufficient(payload: dict) -> None:
    _send(
        "inventory.insufficient",
        subject=f"Stock shortage for order #{payload['order_id']}",
        message=f"Order #{payload['order_id']} could not be fully reserved: {payload.get('reason')}",
        recipient_email=OPS_TEAM_EMAIL,
    )


def _handle_inventory_low_stock(payload: dict) -> None:
    _send(
        "inventory.low_stock",
        subject=f"Low stock alert: {payload.get('sku')}",
        message=(
            f"Product {payload.get('sku')} (id {payload.get('product_id')}) is low on stock: "
            f"{payload.get('quantity_available')} remaining (reorder level {payload.get('reorder_level')})."
        ),
        recipient_email=WAREHOUSE_TEAM_EMAIL,
    )


def _handle_generic_system_event(routing_key: str, payload: dict) -> None:
    _send(
        routing_key,
        subject=f"System event: {routing_key}",
        message=f"Event '{routing_key}' occurred: {payload}",
    )


_HANDLERS = {
    "user.registered": _handle_user_registered,
    "order.created": _handle_order_created,
    "order.status_changed": _handle_order_status_changed,
    "inventory.insufficient": _handle_inventory_insufficient,
    "inventory.low_stock": _handle_inventory_low_stock,
}


def _dispatch(routing_key: str, payload: dict) -> None:
    handler = _HANDLERS.get(routing_key)
    if handler is not None:
        handler(payload)
    else:
        _handle_generic_system_event(routing_key, payload)


def start_notification_consumers() -> None:
    start_consumer_thread(RABBITMQ_URL, QUEUE_NAME, ROUTING_KEYS, _dispatch)

"""Background RabbitMQ consumers for the Order Processing Service.

Listens for the outcome of the Inventory Management Service's stock
reservation attempt and transitions the order out of "pending" accordingly -
this is the event-driven half of the order lifecycle (the other half,
shipped/delivered, is a manual staff action via the REST API).
"""
import logging

from app import crud
from app.config import RABBITMQ_URL
from app.database import SessionLocal
from app.events import publish_order_status_changed
from libs.common.messaging import start_consumer_thread

logger = logging.getLogger("order_service.consumers")

QUEUE_NAME = "order_service.events"
ROUTING_KEYS = ["inventory.reserved", "inventory.insufficient"]


def _handle_inventory_reserved(payload: dict) -> None:
    order_id = payload["order_id"]
    db = SessionLocal()
    try:
        order = crud.get_order(db, order_id)
        if order is None or order.status != "pending":
            return
        old_status = order.status
        updated = crud.update_order_status(db, order, "confirmed")
        publish_order_status_changed(updated.id, updated.customer_id, old_status, "confirmed")
        logger.info("Order %s confirmed after stock reservation", order_id)
    finally:
        db.close()


def _handle_inventory_insufficient(payload: dict) -> None:
    order_id = payload["order_id"]
    db = SessionLocal()
    try:
        order = crud.get_order(db, order_id)
        if order is None or order.status != "pending":
            return
        old_status = order.status
        updated = crud.update_order_status(db, order, "cancelled")
        publish_order_status_changed(updated.id, updated.customer_id, old_status, "cancelled")
        logger.info("Order %s cancelled: %s", order_id, payload.get("reason"))
    finally:
        db.close()


def _dispatch(routing_key: str, payload: dict) -> None:
    if routing_key == "inventory.reserved":
        _handle_inventory_reserved(payload)
    elif routing_key == "inventory.insufficient":
        _handle_inventory_insufficient(payload)
    else:
        logger.debug("Ignoring unhandled routing key '%s'", routing_key)


def start_order_consumers() -> None:
    start_consumer_thread(RABBITMQ_URL, QUEUE_NAME, ROUTING_KEYS, _dispatch)

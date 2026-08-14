"""Background RabbitMQ consumers for the Inventory Management Service.

- "product.created": auto-provisions a zero-stock inventory row so every
  catalogue product has a corresponding inventory record (real-time sync).
- "order.created": attempts to reserve stock for every line item of a new
  order. Publishes "inventory.reserved" on success or "inventory.insufficient"
  on failure, which the Order Processing Service consumes to move the order
  to "confirmed" or "cancelled".
"""
import logging

from app import crud
from app.config import RABBITMQ_URL
from app.database import SessionLocal
from app.events import publish_inventory_insufficient, publish_inventory_low_stock, publish_inventory_reserved
from libs.common.messaging import start_consumer_thread

logger = logging.getLogger("inventory_service.consumers")

QUEUE_NAME = "inventory_service.events"
ROUTING_KEYS = ["product.created", "order.created"]


def _handle_product_created(payload: dict) -> None:
    product_id = payload["product_id"]
    sku = payload.get("sku", "")
    db = SessionLocal()
    try:
        if crud.get_by_product_id(db, product_id) is None:
            crud.create_inventory(db, product_id=product_id, sku=sku, quantity_available=0)
            logger.info("Auto-created inventory record for new product %s (%s)", product_id, sku)
    finally:
        db.close()


def _handle_order_created(payload: dict) -> None:
    order_id = payload["order_id"]
    items = payload["items"]  # [{product_id, quantity}, ...]
    db = SessionLocal()
    try:
        # First check all items have sufficient stock before reserving any,
        # so a partial failure never leaves stock partially reserved.
        shortages = []
        for item in items:
            record = crud.get_by_product_id(db, item["product_id"])
            if record is None or record.quantity_available < item["quantity"]:
                shortages.append(item["product_id"])

        if shortages:
            publish_inventory_insufficient(
                order_id, items, reason=f"Insufficient stock for product(s): {shortages}"
            )
            logger.warning("Order %s could not be fulfilled, shortages: %s", order_id, shortages)
            return

        for item in items:
            crud.try_reserve_stock(db, item["product_id"], item["quantity"])
            record = crud.get_by_product_id(db, item["product_id"])
            if record and record.quantity_available <= record.reorder_level:
                publish_inventory_low_stock(record.product_id, record.sku, record.quantity_available, record.reorder_level)

        publish_inventory_reserved(order_id, items)
        logger.info("Reserved stock for order %s", order_id)
    finally:
        db.close()


def _dispatch(routing_key: str, payload: dict) -> None:
    if routing_key == "product.created":
        _handle_product_created(payload)
    elif routing_key == "order.created":
        _handle_order_created(payload)
    else:
        logger.debug("Ignoring unhandled routing key '%s'", routing_key)


def start_inventory_consumers() -> None:
    start_consumer_thread(RABBITMQ_URL, QUEUE_NAME, ROUTING_KEYS, _dispatch)

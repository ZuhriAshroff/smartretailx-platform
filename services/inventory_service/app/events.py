from app.config import RABBITMQ_URL
from libs.common.messaging import EventPublisher

publisher = EventPublisher(RABBITMQ_URL)


def publish_inventory_reserved(order_id: int, items: list[dict]) -> None:
    publisher.publish(
        "inventory.reserved",
        {"event": "inventory.reserved", "order_id": order_id, "items": items},
    )


def publish_inventory_insufficient(order_id: int, items: list[dict], reason: str) -> None:
    publisher.publish(
        "inventory.insufficient",
        {"event": "inventory.insufficient", "order_id": order_id, "items": items, "reason": reason},
    )


def publish_inventory_updated(product_id: int, quantity_available: int) -> None:
    publisher.publish(
        "inventory.updated",
        {"event": "inventory.updated", "product_id": product_id, "quantity_available": quantity_available},
    )


def publish_inventory_low_stock(product_id: int, sku: str, quantity_available: int, reorder_level: int) -> None:
    publisher.publish(
        "inventory.low_stock",
        {
            "event": "inventory.low_stock",
            "product_id": product_id,
            "sku": sku,
            "quantity_available": quantity_available,
            "reorder_level": reorder_level,
        },
    )

from app.config import RABBITMQ_URL
from libs.common.messaging import EventPublisher

publisher = EventPublisher(RABBITMQ_URL)


def publish_product_created(product_id: int, sku: str, name: str, category: str, price: float) -> None:
    publisher.publish(
        "product.created",
        {
            "event": "product.created",
            "product_id": product_id,
            "sku": sku,
            "name": name,
            "category": category,
            "price": price,
        },
    )


def publish_product_updated(product_id: int, sku: str, changes: dict) -> None:
    publisher.publish(
        "product.updated",
        {"event": "product.updated", "product_id": product_id, "sku": sku, "changes": changes},
    )


def publish_product_deleted(product_id: int, sku: str) -> None:
    publisher.publish(
        "product.deleted",
        {"event": "product.deleted", "product_id": product_id, "sku": sku},
    )

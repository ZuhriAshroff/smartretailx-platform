from app.config import RABBITMQ_URL
from libs.common.messaging import EventPublisher

publisher = EventPublisher(RABBITMQ_URL)


def publish_order_created(order_id: int, customer_id: int, items: list[dict]) -> None:
    publisher.publish(
        "order.created",
        {
            "event": "order.created",
            "order_id": order_id,
            "customer_id": customer_id,
            "items": [{"product_id": i["product_id"], "quantity": i["quantity"]} for i in items],
        },
    )


def publish_order_status_changed(order_id: int, customer_id: int, old_status: str, new_status: str) -> None:
    publisher.publish(
        "order.status_changed",
        {
            "event": "order.status_changed",
            "order_id": order_id,
            "customer_id": customer_id,
            "old_status": old_status,
            "new_status": new_status,
        },
    )

from app.config import RABBITMQ_URL
from libs.common.messaging import EventPublisher

publisher = EventPublisher(RABBITMQ_URL)


def publish_user_registered(user_id: int, email: str, full_name: str, role: str) -> None:
    publisher.publish(
        "user.registered",
        {
            "event": "user.registered",
            "user_id": user_id,
            "email": email,
            "full_name": full_name,
            "role": role,
        },
    )

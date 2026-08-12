from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Notification


def create_notification(
    db: Session,
    event_type: str,
    subject: str,
    message: str,
    recipient_user_id: int | None = None,
    recipient_email: str | None = None,
) -> Notification:
    notification = Notification(
        event_type=event_type,
        subject=subject,
        message=message,
        recipient_user_id=recipient_user_id,
        recipient_email=recipient_email,
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification


def get_notification(db: Session, notification_id: int) -> Notification | None:
    return db.get(Notification, notification_id)


def list_notifications(
    db: Session, page: int, page_size: int, recipient_user_id: int | None = None
) -> tuple[list[Notification], int]:
    stmt = select(Notification)
    if recipient_user_id is not None:
        stmt = stmt.where(Notification.recipient_user_id == recipient_user_id)

    total = db.execute(select(func.count()).select_from(stmt.subquery())).scalar_one()
    items = (
        db.execute(stmt.order_by(Notification.id.desc()).offset((page - 1) * page_size).limit(page_size))
        .scalars()
        .all()
    )
    return items, total


def mark_as_read(db: Session, notification: Notification) -> Notification:
    notification.is_read = True
    db.commit()
    db.refresh(notification)
    return notification

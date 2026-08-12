from datetime import datetime

from pydantic import BaseModel


class NotificationPublic(BaseModel):
    id: int
    recipient_user_id: int | None
    recipient_email: str | None
    event_type: str
    subject: str
    message: str
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True


class PaginatedNotifications(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[NotificationPublic]

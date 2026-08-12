from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app import crud
from app.database import get_db
from app.schemas import NotificationPublic, PaginatedNotifications
from libs.common.security import TokenPayload, get_current_user

router = APIRouter(prefix="/v1/notifications", tags=["notifications"])


@router.get("", response_model=PaginatedNotifications)
def list_notifications(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: TokenPayload = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    recipient_filter = None if current_user.role == "admin" else int(current_user.sub)
    items, total = crud.list_notifications(db, page, page_size, recipient_user_id=recipient_filter)
    return PaginatedNotifications(total=total, page=page, page_size=page_size, items=items)


@router.get("/{notification_id}", response_model=NotificationPublic)
def get_notification(
    notification_id: int,
    current_user: TokenPayload = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    notification = crud.get_notification(db, notification_id)
    if not notification:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    if current_user.role != "admin" and notification.recipient_user_id != int(current_user.sub):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not permitted to view this notification")
    return notification


@router.patch("/{notification_id}/read", response_model=NotificationPublic)
def mark_notification_read(
    notification_id: int,
    current_user: TokenPayload = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    notification = crud.get_notification(db, notification_id)
    if not notification:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    if current_user.role != "admin" and notification.recipient_user_id != int(current_user.sub):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not permitted to update this notification")
    return crud.mark_as_read(db, notification)

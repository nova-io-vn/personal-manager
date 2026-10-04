from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session

from app.core.time import utc_now_naive
from app.database.database import get_db
from app.models.notification import Notification, NotificationChannel, NotificationEventType
from app.repositories.notification import list_notifications
from app.schemas.notification import NotificationRead

router = APIRouter(tags=["notifications"])


@router.get("/notifications", response_model=list[NotificationRead])
def read_notifications(
    limit: int = Query(default=50, ge=1, le=200), unread_only: bool = False,
    channel: NotificationChannel | None = None, event_type: NotificationEventType | None = None,
    db: Session = Depends(get_db),
):
    return list_notifications(db, limit, unread_only, channel, event_type)


@router.get("/notifications/{notification_id}", response_model=NotificationRead)
def read_notification(notification_id: int, db: Session = Depends(get_db)):
    notification = db.get(Notification, notification_id)
    if notification is None:
        raise HTTPException(status_code=404, detail="Notification not found")
    return notification


@router.patch("/notifications/{notification_id}/read", response_model=NotificationRead)
def mark_notification_read(notification_id: int, db: Session = Depends(get_db)):
    notification = db.get(Notification, notification_id)
    if notification is None:
        raise HTTPException(status_code=404, detail="Notification not found")
    notification.read_at = notification.read_at or utc_now_naive()
    db.commit()
    db.refresh(notification)
    return notification


@router.delete("/notifications/{notification_id}", status_code=204)
def delete_notification(notification_id: int, db: Session = Depends(get_db)):
    notification = db.get(Notification, notification_id)
    if notification is None:
        raise HTTPException(status_code=404, detail="Notification not found")
    db.delete(notification)
    db.commit()
    return Response(status_code=204)

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.notification import Notification, NotificationChannel, NotificationEventType, NotificationStatus


def list_notifications(
    db: Session, limit: int = 50, unread_only: bool = False,
    channel: NotificationChannel | None = None, event_type: NotificationEventType | None = None,
) -> list[Notification]:
    query = select(Notification).order_by(Notification.created_at.desc(), Notification.id.desc()).limit(limit)
    if unread_only:
        query = query.where(Notification.read_at.is_(None))
    if channel is not None:
        query = query.where(Notification.channel == channel)
    if event_type is not None:
        query = query.where(Notification.event_type == event_type)
    return list(db.scalars(query).all())


def pending_notifications(db: Session, due_at) -> list[Notification]:
    return list(db.scalars(select(Notification).where(
        Notification.status == NotificationStatus.PENDING,
        Notification.scheduled_for <= due_at,
    ).order_by(Notification.scheduled_for, Notification.id)).all())

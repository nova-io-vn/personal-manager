from datetime import datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.time import utc_now_naive
from app.models.notification import (
    Notification, NotificationChannel, NotificationEventType, NotificationStatus,
)
from app.repositories.notification import pending_notifications
from app.repositories.settings import get_raw_settings
from app.services.telegram_service import TelegramService


class NotificationService:
    def __init__(self, db: Session, telegram: TelegramService | None = None):
        self.db = db
        self.telegram = telegram or TelegramService()

    def create(
        self, event_type: NotificationEventType, channel: NotificationChannel,
        title: str, message: str, scheduled_for: datetime, dedupe_key: str,
        related_entity_type: str | None = None, related_entity_id: int | None = None,
    ) -> Notification | None:
        channel_key = f"{dedupe_key}:{channel.value}"
        existing = self.db.scalar(select(Notification).where(Notification.dedupe_key == channel_key))
        if existing is not None:
            return None
        notification = Notification(
            event_type=event_type, channel=channel, title=title, message=message,
            scheduled_for=scheduled_for, dedupe_key=channel_key,
            related_entity_type=related_entity_type, related_entity_id=related_entity_id,
        )
        self.db.add(notification)
        try:
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            return None
        self.db.refresh(notification)
        return notification

    def create_for_enabled_channels(self, **kwargs) -> list[Notification]:
        raw = get_raw_settings(self.db)
        channels = [NotificationChannel.LOCAL]
        if raw["telegram_enabled"] == "true":
            channels.append(NotificationChannel.TELEGRAM)
        created = []
        for channel in channels:
            notification = self.create(channel=channel, **kwargs)
            if notification is not None:
                created.append(notification)
        return created

    def deliver(self, notification: Notification, now: datetime | None = None) -> None:
        if notification.status != NotificationStatus.PENDING:
            return
        sent_at = now or utc_now_naive()
        if notification.channel == NotificationChannel.LOCAL:
            notification.status = NotificationStatus.SENT
            notification.sent_at = sent_at
            notification.error_message = None
        else:
            raw = get_raw_settings(self.db)
            result = self.telegram.send_text(
                raw["telegram_bot_token"], raw["telegram_chat_id"],
                f"{notification.title}\n\n{notification.message}",
            )
            if result.success:
                notification.status = NotificationStatus.SENT
                notification.sent_at = sent_at
                notification.error_message = None
            else:
                notification.status = NotificationStatus.FAILED
                notification.error_message = result.error or "Telegram delivery failed"
        self.db.commit()

    def deliver_due(self, now: datetime | None = None) -> int:
        due_at = now or utc_now_naive()
        notifications = pending_notifications(self.db, due_at)
        for notification in notifications:
            self.deliver(notification, due_at)
        return len(notifications)

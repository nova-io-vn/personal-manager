from datetime import datetime, timezone
from enum import StrEnum

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class NotificationEventType(StrEnum):
    SCHEDULE_REMINDER = "SCHEDULE_REMINDER"
    BUDGET_WARNING = "BUDGET_WARNING"
    JOURNAL_REMINDER = "JOURNAL_REMINDER"
    HEALTH_REMINDER = "HEALTH_REMINDER"
    DAILY_SUMMARY = "DAILY_SUMMARY"


class NotificationChannel(StrEnum):
    LOCAL = "LOCAL"
    TELEGRAM = "TELEGRAM"


class NotificationStatus(StrEnum):
    PENDING = "PENDING"
    SENT = "SENT"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class ApplicationSetting(Base):
    __tablename__ = "settings"

    key: Mapped[str] = mapped_column(String(80), primary_key=True)
    value: Mapped[str] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True)
    event_type: Mapped[NotificationEventType] = mapped_column(String(30), index=True)
    channel: Mapped[NotificationChannel] = mapped_column(String(20), index=True)
    title: Mapped[str] = mapped_column(String(200))
    message: Mapped[str] = mapped_column(Text)
    scheduled_for: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[NotificationStatus] = mapped_column(String(20), index=True, default=NotificationStatus.PENDING)
    related_entity_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    related_entity_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    dedupe_key: Mapped[str] = mapped_column(String(240), unique=True, index=True)
    error_message: Mapped[str | None] = mapped_column(String(300), nullable=True)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

from datetime import datetime, time

from pydantic import BaseModel, ConfigDict, Field

from app.models.notification import NotificationChannel, NotificationEventType, NotificationStatus


class SettingsUpdate(BaseModel):
    currency: str | None = Field(default=None, min_length=1, max_length=10)
    default_reminder_minutes: int | None = Field(default=None, ge=0, le=10080)
    notifications_enabled: bool | None = None
    schedule_reminders_enabled: bool | None = None
    budget_warnings_enabled: bool | None = None
    journal_reminder_enabled: bool | None = None
    journal_reminder_time: time | None = None
    health_reminder_enabled: bool | None = None
    health_reminder_time: time | None = None
    daily_summary_enabled: bool | None = None
    daily_summary_time: time | None = None
    telegram_enabled: bool | None = None
    telegram_bot_token: str | None = Field(default=None, max_length=300)
    telegram_chat_id: str | None = Field(default=None, max_length=100)
    gemini_enabled: bool | None = None
    gemini_api_key: str | None = Field(default=None, max_length=300)
    gemini_model: str | None = Field(default=None, min_length=1, max_length=100)


class SettingsRead(BaseModel):
    currency: str
    default_reminder_minutes: int
    notifications_enabled: bool
    schedule_reminders_enabled: bool
    budget_warnings_enabled: bool
    journal_reminder_enabled: bool
    journal_reminder_time: time
    health_reminder_enabled: bool
    health_reminder_time: time
    daily_summary_enabled: bool
    daily_summary_time: time
    telegram_enabled: bool
    telegram_bot_token: str | None
    telegram_token_configured: bool
    telegram_chat_id: str | None
    gemini_enabled: bool
    gemini_api_key: str | None
    gemini_key_configured: bool
    gemini_model: str


class TelegramTestResult(BaseModel):
    success: bool
    message: str


class IntegrationTestResult(BaseModel):
    success: bool
    message: str


class NotificationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    event_type: NotificationEventType
    channel: NotificationChannel
    title: str
    message: str
    scheduled_for: datetime
    sent_at: datetime | None
    status: NotificationStatus
    related_entity_type: str | None
    related_entity_id: int | None
    read_at: datetime | None
    created_at: datetime

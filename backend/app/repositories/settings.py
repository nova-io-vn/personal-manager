from datetime import time

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.notification import ApplicationSetting
from app.schemas.notification import SettingsRead


DEFAULT_SETTINGS: dict[str, str] = {
    "currency": "VND",
    "default_reminder_minutes": "15",
    "notifications_enabled": "true",
    "schedule_reminders_enabled": "true",
    "budget_warnings_enabled": "true",
    "journal_reminder_enabled": "false",
    "journal_reminder_time": "21:30:00",
    "health_reminder_enabled": "false",
    "health_reminder_time": "20:00:00",
    "daily_summary_enabled": "true",
    "daily_summary_time": "22:00:00",
    "telegram_enabled": "false",
    "telegram_bot_token": "",
    "telegram_chat_id": "",
    "gemini_enabled": "false",
    "gemini_api_key": "",
    "gemini_model": "gemini-3.5-flash",
}
TOKEN_MASK = "••••••••"


def seed_settings(db: Session) -> None:
    existing = set(db.scalars(select(ApplicationSetting.key)).all())
    db.add_all(ApplicationSetting(key=key, value=value) for key, value in DEFAULT_SETTINGS.items() if key not in existing)
    db.commit()


def get_raw_settings(db: Session) -> dict[str, str]:
    values = DEFAULT_SETTINGS.copy()
    values.update({item.key: item.value for item in db.scalars(select(ApplicationSetting)).all()})
    return values


def _as_bool(value: str) -> bool:
    return value.lower() == "true"


def get_settings_view(db: Session) -> SettingsRead:
    values = get_raw_settings(db)
    token_configured = bool(values["telegram_bot_token"])
    gemini_key_configured = bool(values["gemini_api_key"])
    return SettingsRead(
        currency=values["currency"], default_reminder_minutes=int(values["default_reminder_minutes"]),
        notifications_enabled=_as_bool(values["notifications_enabled"]),
        schedule_reminders_enabled=_as_bool(values["schedule_reminders_enabled"]),
        budget_warnings_enabled=_as_bool(values["budget_warnings_enabled"]),
        journal_reminder_enabled=_as_bool(values["journal_reminder_enabled"]),
        journal_reminder_time=time.fromisoformat(values["journal_reminder_time"]),
        health_reminder_enabled=_as_bool(values["health_reminder_enabled"]),
        health_reminder_time=time.fromisoformat(values["health_reminder_time"]),
        daily_summary_enabled=_as_bool(values["daily_summary_enabled"]),
        daily_summary_time=time.fromisoformat(values["daily_summary_time"]),
        telegram_enabled=_as_bool(values["telegram_enabled"]),
        telegram_bot_token=TOKEN_MASK if token_configured else None,
        telegram_token_configured=token_configured,
        telegram_chat_id=values["telegram_chat_id"] or None,
        gemini_enabled=_as_bool(values["gemini_enabled"]),
        gemini_api_key=TOKEN_MASK if gemini_key_configured else None,
        gemini_key_configured=gemini_key_configured,
        gemini_model=values["gemini_model"],
    )


def update_settings(db: Session, values: dict) -> SettingsRead:
    for key, value in values.items():
        if key in {"telegram_bot_token", "gemini_api_key"} and value == TOKEN_MASK:
            continue
        if isinstance(value, bool):
            serialized = "true" if value else "false"
        elif isinstance(value, time):
            serialized = value.isoformat()
        else:
            serialized = "" if value is None else str(value).strip()
        setting = db.get(ApplicationSetting, key)
        if setting is None:
            db.add(ApplicationSetting(key=key, value=serialized))
        else:
            setting.value = serialized
    db.commit()
    return get_settings_view(db)

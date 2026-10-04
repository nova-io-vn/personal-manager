from datetime import date, datetime, timedelta
from decimal import Decimal

import httpx
from sqlalchemy import select

from app.core.scheduler import create_scheduler
from app.core.time import utc_to_local
from app.models.calendar import Schedule
from app.models.finance import Account, Budget, Transaction, TransactionCategory, TransactionType
from app.models.health import HealthDailyLog
from app.models.journal import JournalEntry, Mood
from app.models.notification import (
    Notification, NotificationChannel, NotificationEventType, NotificationStatus,
)
from app.repositories.settings import get_raw_settings, seed_settings, update_settings
from app.services.notification_engine import NotificationEngine
from app.services.notification_service import NotificationService
from app.services.telegram_service import DeliveryResult, TelegramService


class FailingTelegram:
    def send_text(self, token: str, chat_id: str, text: str) -> DeliveryResult:
        return DeliveryResult(False, "Unable to reach Telegram")


def test_settings_defaults_update_and_token_masking(client, db_session):
    defaults = client.get("/api/settings")
    assert defaults.status_code == 200
    assert defaults.json()["currency"] == "VND"
    assert defaults.json()["telegram_bot_token"] is None
    updated = client.patch("/api/settings", json={
        "currency": "USD", "telegram_bot_token": "123:secret-token", "telegram_chat_id": "42",
    })
    assert updated.json()["telegram_bot_token"] == "••••••••"
    assert updated.json()["telegram_token_configured"] is True
    assert get_raw_settings(db_session)["telegram_bot_token"] == "123:secret-token"
    assert "secret-token" not in client.get("/api/settings").text


def test_telegram_test_endpoint_is_mocked(client, monkeypatch):
    client.patch("/api/settings", json={"telegram_bot_token": "token", "telegram_chat_id": "42"})
    monkeypatch.setattr(TelegramService, "send_text", lambda self, token, chat_id, text: DeliveryResult(True))
    response = client.post("/api/settings/telegram/test")
    assert response.json() == {"success": True, "message": "Đã gửi tin nhắn thử thành công."}


def test_telegram_service_uses_mocked_bot_api():
    def handler(request: httpx.Request):
        assert request.url.path.endswith("/bottest-token/sendMessage")
        return httpx.Response(200, json={"ok": True, "result": {"message_id": 1}})

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        result = TelegramService(client).send_text("test-token", "42", "hello")
    assert result.success is True


def test_notification_creation_delivery_failure_and_duplicate(db_session):
    seed_settings(db_session)
    now = datetime(2026, 10, 4, 10, 0)
    service = NotificationService(db_session)
    first = service.create(
        NotificationEventType.DAILY_SUMMARY, NotificationChannel.LOCAL,
        "Title", "Message", now, "unique",
    )
    assert first is not None and first.status == NotificationStatus.PENDING
    assert service.create(NotificationEventType.DAILY_SUMMARY, NotificationChannel.LOCAL, "Title", "Message", now, "unique") is None
    service.deliver_due(now)
    assert first.status == NotificationStatus.SENT

    failed_service = NotificationService(db_session, telegram=FailingTelegram())
    failed = failed_service.create(
        NotificationEventType.DAILY_SUMMARY, NotificationChannel.TELEGRAM,
        "Title", "Message", now, "failed",
    )
    failed_service.deliver(failed, now)
    assert failed.status == NotificationStatus.FAILED
    assert "token" not in (failed.error_message or "").lower()


def test_notification_api_read_mark_and_delete(client, db_session):
    service = NotificationService(db_session)
    item = service.create(
        NotificationEventType.DAILY_SUMMARY, NotificationChannel.LOCAL,
        "Summary", "Today", datetime(2026, 10, 4, 10, 0), "api-item",
    )
    service.deliver(item, datetime(2026, 10, 4, 10, 0))
    assert client.get("/api/notifications", params={"unread_only": True}).json()[0]["title"] == "Summary"
    marked = client.patch(f"/api/notifications/{item.id}/read")
    assert marked.status_code == 200 and marked.json()["read_at"] is not None
    assert client.delete(f"/api/notifications/{item.id}").status_code == 204


def test_schedule_reminder_completed_and_duplicate_rules(db_session):
    seed_settings(db_session)
    now = datetime(2026, 10, 4, 10, 0)
    due = Schedule(title="Meeting", start_datetime=now + timedelta(minutes=30), end_datetime=now + timedelta(hours=1), reminder_minutes=30, completed=False)
    completed = Schedule(title="Done", start_datetime=now + timedelta(minutes=10), end_datetime=now + timedelta(hours=1), reminder_minutes=10, completed=True)
    db_session.add_all([due, completed]); db_session.commit()
    engine = NotificationEngine(db_session)
    engine.generate_schedule_reminders(now); engine.service.deliver_due(now)
    engine.generate_schedule_reminders(now); engine.service.deliver_due(now)
    notifications = db_session.scalars(select(Notification).where(Notification.event_type == NotificationEventType.SCHEDULE_REMINDER)).all()
    assert len(notifications) == 1
    assert notifications[0].related_entity_id == due.id
    assert notifications[0].status == NotificationStatus.SENT


def test_budget_thresholds_do_not_repeat(db_session):
    seed_settings(db_session)
    category = db_session.scalar(select(TransactionCategory).where(TransactionCategory.name == "Food"))
    account = Account(name="Cash", type="CASH", initial_balance=Decimal("1000"), current_balance=Decimal("1000"))
    budget = Budget(category_id=category.id, amount=Decimal("100"), period="monthly", start_date=date(2026, 10, 1), end_date=date(2026, 10, 31))
    transaction = Transaction(account=account, category=category, type=TransactionType.EXPENSE, amount=Decimal("81"), transaction_date=date(2026, 10, 4), source="MANUAL")
    db_session.add_all([account, budget, transaction]); db_session.commit()
    engine = NotificationEngine(db_session); now = datetime(2026, 10, 4, 12, 0)
    engine.generate_budget_warnings(now); engine.generate_budget_warnings(now)
    transaction.amount = Decimal("91"); db_session.commit(); engine.generate_budget_warnings(now)
    transaction.amount = Decimal("101"); db_session.commit(); engine.generate_budget_warnings(now)
    messages = [item.message for item in db_session.scalars(select(Notification).where(Notification.event_type == NotificationEventType.BUDGET_WARNING)).all()]
    assert len(messages) == 3
    assert sum("80%" in message for message in messages) == 1
    assert sum("90%" in message for message in messages) == 1
    assert sum("100%" in message for message in messages) == 1


def test_journal_and_health_reminders_respect_existing_data(db_session):
    seed_settings(db_session); engine = NotificationEngine(db_session); now = datetime(2026, 10, 4, 14, 0); day = utc_to_local(now).date()
    engine.generate_journal_reminder(day, now); engine.generate_health_reminder(day, now)
    assert db_session.scalar(select(Notification).where(Notification.event_type == NotificationEventType.JOURNAL_REMINDER)) is not None
    assert db_session.scalar(select(Notification).where(Notification.event_type == NotificationEventType.HEALTH_REMINDER)) is not None
    db_session.add_all([JournalEntry(entry_date=day, mood=Mood.GOOD, content="ok"), HealthDailyLog(date=day, steps=1000)])
    db_session.commit()
    other_day = day + timedelta(days=1)
    engine.generate_journal_reminder(other_day, now); engine.generate_health_reminder(other_day, now)
    db_session.add_all([JournalEntry(entry_date=other_day + timedelta(days=1), mood=Mood.GOOD, content="exists"), HealthDailyLog(date=other_day + timedelta(days=1), steps=1000)])
    db_session.commit()
    before = db_session.scalar(select(func_count(Notification.id)))
    engine.generate_journal_reminder(other_day + timedelta(days=1), now); engine.generate_health_reminder(other_day + timedelta(days=1), now)
    after = db_session.scalar(select(func_count(Notification.id)))
    assert before == after


def func_count(column):
    from sqlalchemy import func
    return func.count(column)


def test_daily_summary_uses_available_data_only(db_session):
    seed_settings(db_session); now = datetime(2026, 10, 4, 14, 0); day = utc_to_local(now).date()
    account = Account(name="Cash", type="CASH", initial_balance=Decimal("100"), current_balance=Decimal("75"))
    transaction = Transaction(account=account, type=TransactionType.EXPENSE, amount=Decimal("25"), transaction_date=day, source="MANUAL")
    db_session.add_all([account, transaction, HealthDailyLog(date=day, water_ml=2000, steps=7200), JournalEntry(entry_date=day, mood=Mood.GOOD, content="good")]); db_session.commit()
    engine = NotificationEngine(db_session); engine.generate_daily_summary(day, now)
    notification = db_session.scalar(select(Notification).where(Notification.event_type == NotificationEventType.DAILY_SUMMARY))
    assert "Chi tiêu: 25 ₫" in notification.message
    assert "7.200 bước" in notification.message
    assert "2.000 ml nước" in notification.message
    assert "Tâm trạng: Tốt" in notification.message
    assert "kcal" not in notification.message
    assert "giờ ngủ" not in notification.message


def test_scheduler_configuration():
    scheduler = create_scheduler()
    job = scheduler.get_job("notification-engine")
    assert job is not None
    assert job.max_instances == 1

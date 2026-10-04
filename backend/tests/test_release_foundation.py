import json
import zipfile
from datetime import datetime, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import create_engine, inspect, select
from sqlalchemy.orm import sessionmaker

from app.database.base import Base
from app.database.migrations import ALEMBIC_REVISION, ensure_database_schema
from app.models.calendar import RepeatType, Schedule
from app.models.finance import Account
from app.models.journal import JournalEntry, Mood
from app.models.notification import Notification
from app.repositories.settings import get_raw_settings, seed_settings, update_settings
from app.services.ai_service import AIService
from app.services.backup import BackupService, BackupValidationError
from app.services.context_builder import ContextBuilder
from app.services.notification_engine import NotificationEngine
from app.services.recurrence import expand_occurrences


def test_migration_bootstraps_empty_database(tmp_path):
    database = tmp_path / "fresh.db"
    engine = create_engine(f"sqlite:///{database.as_posix()}")
    ensure_database_schema(engine, f"sqlite:///{database.as_posix()}")
    assert set(Base.metadata.tables).issubset(inspect(engine).get_table_names())
    with engine.connect() as connection:
        assert connection.exec_driver_sql("SELECT version_num FROM alembic_version").scalar() == ALEMBIC_REVISION
    engine.dispose()


def test_migration_stamps_compatible_legacy_database_without_data_loss(tmp_path):
    database = tmp_path / "legacy.db"
    url = f"sqlite:///{database.as_posix()}"
    engine = create_engine(url)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    with Session.begin() as db:
        db.add(Account(name="Preserved", type="CASH", initial_balance=Decimal("10"), current_balance=Decimal("10")))
    ensure_database_schema(engine, url)
    with Session() as db:
        assert db.scalar(select(Account).where(Account.name == "Preserved")) is not None
    assert "alembic_version" in inspect(engine).get_table_names()
    engine.dispose()


def test_backup_restore_round_trip_and_rejects_invalid_archive(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    database = data_dir / "personal.db"
    url = f"sqlite:///{database.as_posix()}"
    engine = create_engine(url)
    ensure_database_schema(engine, url)
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    with Session.begin() as db:
        db.add(Account(name="Before", type="CASH", initial_balance=Decimal("10"), current_balance=Decimal("10")))
    service = BackupService(engine, data_dir)
    archive = service.create_backup()
    with zipfile.ZipFile(archive) as bundle:
        manifest = json.loads(bundle.read("manifest.json"))
        assert manifest["schema_revision"] == ALEMBIC_REVISION
    with Session.begin() as db:
        db.add(Account(name="After", type="CASH", initial_balance=Decimal("20"), current_balance=Decimal("20")))
    safety = service.restore(archive.read_bytes())
    with Session() as db:
        assert [item.name for item in db.scalars(select(Account).order_by(Account.id))] == ["Before"]
    assert safety.exists()
    with pytest.raises(BackupValidationError):
        service.restore(b"not-a-zip")
    engine.dispose()


def _schedule(repeat_type: RepeatType, repeat_until: datetime | None = None) -> Schedule:
    start = datetime(2026, 1, 31, 9)
    return Schedule(
        id=42, title="Recurring", start_datetime=start, end_datetime=start + timedelta(hours=1),
        repeat_type=repeat_type, repeat_until=repeat_until, reminder_minutes=30, completed=False,
    )


def test_recurrence_daily_weekly_monthly_and_repeat_until():
    daily = expand_occurrences(_schedule(RepeatType.DAILY, datetime(2026, 2, 2, 9)), datetime(2026, 1, 31), datetime(2026, 2, 5))
    weekly = expand_occurrences(_schedule(RepeatType.WEEKLY), datetime(2026, 2, 1), datetime(2026, 2, 20))
    monthly = expand_occurrences(_schedule(RepeatType.MONTHLY), datetime(2026, 1, 1), datetime(2026, 4, 1))
    assert [item.start.day for item in daily] == [31, 1, 2]
    assert [item.start.day for item in weekly] == [7, 14]
    assert [(item.start.month, item.start.day) for item in monthly] == [(1, 31), (2, 28), (3, 31)]


def test_recurring_reminder_uses_occurrence_in_dedupe_key(db_session):
    seed_settings(db_session)
    schedule = Schedule(
        title="Weekly", start_datetime=datetime(2026, 9, 27, 10), end_datetime=datetime(2026, 9, 27, 11),
        repeat_type=RepeatType.WEEKLY, repeat_until=datetime(2026, 10, 31), reminder_minutes=30, completed=False,
    )
    db_session.add(schedule)
    db_session.commit()
    engine = NotificationEngine(db_session)
    now = datetime(2026, 10, 4, 9, 30)
    engine.generate_schedule_reminders(now)
    engine.generate_schedule_reminders(now)
    keys = [item.dedupe_key for item in db_session.scalars(select(Notification)).all()]
    assert len(keys) == 1
    assert "2026-10-04T10:00:00" in keys[0]


class _FakeResponse:
    text = "Phản hồi thử"


class _FakeModels:
    def generate_content(self, **kwargs):
        self.kwargs = kwargs
        return _FakeResponse()


class _FakeClient:
    def __init__(self):
        self.models = _FakeModels()
        self.closed = False

    def close(self):
        self.closed = True


def test_ai_context_minimizes_domains_and_journal_content(db_session):
    db_session.add(JournalEntry(entry_date=datetime(2026, 10, 4).date(), mood=Mood.GOOD, content="private text"))
    db_session.commit()
    finance_context, domains = ContextBuilder(db_session).build("Tháng này tôi tiêu nhiều nhất vào đâu?", datetime(2026, 10, 4).date())
    assert domains == ["finance"]
    assert set(finance_context) == {"period", "finance"}
    journal_context, _ = ContextBuilder(db_session).build("Nhật ký hôm nay nói gì?", datetime(2026, 10, 4).date())
    assert journal_context["journal"]["entries"][0]["content"] == "private text"


def test_ai_service_success_failure_and_gemini_key_masking(db_session):
    fake = _FakeClient()
    result = AIService(lambda key: fake).generate("secret", "gemini-2.5-flash", "hello", {"test": True})
    assert result.success and result.text == "Phản hồi thử" and fake.closed
    assert AIService().generate("", "gemini-2.5-flash", "hello", {}).success is False
    seed_settings(db_session)
    view = update_settings(db_session, {"gemini_api_key": "secret", "gemini_enabled": True})
    assert view.gemini_key_configured and view.gemini_api_key != "secret"
    assert get_raw_settings(db_session)["gemini_api_key"] == "secret"


def test_cors_allows_health_profile_put(client):
    response = client.options(
        "/api/health/profile",
        headers={
            "Origin": "http://127.0.0.1:5173",
            "Access-Control-Request-Method": "PUT",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-methods"]
    assert "PUT" in response.headers["access-control-allow-methods"]

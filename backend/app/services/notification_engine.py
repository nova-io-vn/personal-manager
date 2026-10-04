from datetime import date, datetime, time, timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.time import local_day_utc_bounds, to_utc_naive, utc_now_naive, utc_to_local
from app.models.calendar import Schedule
from app.models.finance import Budget, Transaction, TransactionCategory, TransactionType
from app.models.health import HealthDailyLog
from app.models.journal import JournalEntry, Mood
from app.models.notification import NotificationEventType
from app.repositories.settings import get_raw_settings
from app.services.health import health_summary
from app.services.notification_service import NotificationService
from app.services.recurrence import expand_occurrences


MOOD_LABELS = {
    Mood.VERY_BAD: "Rất tệ", Mood.BAD: "Không tốt", Mood.NEUTRAL: "Bình thường",
    Mood.GOOD: "Tốt", Mood.VERY_GOOD: "Rất tốt",
}


class NotificationEngine:
    def __init__(self, db: Session, service: NotificationService | None = None):
        self.db = db
        self.service = service or NotificationService(db)

    def run(self, now: datetime | None = None) -> int:
        current = to_utc_naive(now) if now is not None else utc_now_naive()
        settings = get_raw_settings(self.db)
        if settings["notifications_enabled"] != "true":
            return 0
        if settings["schedule_reminders_enabled"] == "true":
            self.generate_schedule_reminders(current)
        if settings["budget_warnings_enabled"] == "true":
            self.generate_budget_warnings(current)
        local_current = utc_to_local(current)
        if settings["journal_reminder_enabled"] == "true" and self._time_due(local_current, settings["journal_reminder_time"]):
            self.generate_journal_reminder(local_current.date(), current)
        if settings["health_reminder_enabled"] == "true" and self._time_due(local_current, settings["health_reminder_time"]):
            self.generate_health_reminder(local_current.date(), current)
        if settings["daily_summary_enabled"] == "true" and self._time_due(local_current, settings["daily_summary_time"]):
            self.generate_daily_summary(local_current.date(), current)
        return self.service.deliver_due(current)

    @staticmethod
    def _time_due(local_now: datetime, configured: str) -> bool:
        return local_now.time().replace(tzinfo=None) >= time.fromisoformat(configured)

    def generate_schedule_reminders(self, now: datetime) -> None:
        schedules = self.db.scalars(select(Schedule).where(Schedule.completed.is_(False))).all()
        for schedule in schedules:
            reminder_minutes = schedule.reminder_minutes
            if reminder_minutes <= 0:
                continue
            search_end = now + timedelta(minutes=reminder_minutes, seconds=1)
            for occurrence in expand_occurrences(schedule, now, search_end):
                if occurrence.start <= now or occurrence.start - timedelta(minutes=reminder_minutes) > now:
                    continue
                local_start = utc_to_local(occurrence.start)
                self.service.create_for_enabled_channels(
                    event_type=NotificationEventType.SCHEDULE_REMINDER,
                    title="Sắp đến lịch trình",
                    message=f"{local_start.strftime('%H:%M')} - {schedule.title}",
                    scheduled_for=now,
                    dedupe_key=f"schedule:{schedule.id}:{occurrence.start.isoformat()}",
                    related_entity_type="schedule", related_entity_id=schedule.id,
                )

    def generate_budget_warnings(self, now: datetime) -> None:
        today = utc_to_local(now).date()
        budgets = self.db.scalars(select(Budget).where(Budget.start_date <= today, Budget.end_date >= today)).all()
        for budget in budgets:
            spent = self.db.scalar(select(func.coalesce(func.sum(Transaction.amount), 0)).where(
                Transaction.type == TransactionType.EXPENSE,
                Transaction.category_id == budget.category_id,
                Transaction.transaction_date >= budget.start_date,
                Transaction.transaction_date <= budget.end_date,
            ))
            usage = (Decimal(spent) / budget.amount * Decimal("100")) if budget.amount else Decimal("0")
            reached = [threshold for threshold in (80, 90, 100) if usage >= threshold]
            if not reached:
                continue
            threshold = max(reached)
            category = self.db.get(TransactionCategory, budget.category_id)
            name = category.name if category else "Danh mục"
            self.service.create_for_enabled_channels(
                event_type=NotificationEventType.BUDGET_WARNING,
                title=f"Ngân sách {name}",
                message=f"Bạn đã sử dụng {threshold}% ngân sách {name}.",
                scheduled_for=now,
                dedupe_key=f"budget:{budget.id}:{threshold}",
                related_entity_type="budget", related_entity_id=budget.id,
            )

    def generate_journal_reminder(self, day: date, now: datetime) -> None:
        exists = self.db.scalar(select(JournalEntry.id).where(JournalEntry.entry_date == day))
        if exists is None:
            self.service.create_for_enabled_channels(
                event_type=NotificationEventType.JOURNAL_REMINDER,
                title="Nhắc viết nhật ký", message="Hôm nay bạn chưa viết nhật ký.",
                scheduled_for=now, dedupe_key=f"journal:{day.isoformat()}",
                related_entity_type="journal",
            )

    def generate_health_reminder(self, day: date, now: datetime) -> None:
        exists = self.db.scalar(select(HealthDailyLog.id).where(HealthDailyLog.date == day))
        if exists is None:
            self.service.create_for_enabled_channels(
                event_type=NotificationEventType.HEALTH_REMINDER,
                title="Nhắc cập nhật sức khỏe", message="Bạn chưa cập nhật sức khỏe hôm nay.",
                scheduled_for=now, dedupe_key=f"health:{day.isoformat()}",
                related_entity_type="health_daily",
            )

    def generate_daily_summary(self, day: date, now: datetime) -> None:
        start, end = local_day_utc_bounds(day)
        schedule_count = self.db.scalar(select(func.count(Schedule.id)).where(
            Schedule.start_datetime >= start, Schedule.start_datetime <= end,
        )) or 0
        income = Decimal(self.db.scalar(select(func.coalesce(func.sum(Transaction.amount), 0)).where(
            Transaction.type == TransactionType.INCOME, Transaction.transaction_date == day,
        )))
        expense = Decimal(self.db.scalar(select(func.coalesce(func.sum(Transaction.amount), 0)).where(
            Transaction.type == TransactionType.EXPENSE, Transaction.transaction_date == day,
        )))
        health = health_summary(self.db, day)
        journal = self.db.scalar(select(JournalEntry).where(JournalEntry.entry_date == day))
        lines = [f"• {schedule_count} lịch trình"]
        if income:
            lines.append(f"• Thu nhập: {self._format_money(income)}")
        if expense:
            lines.append(f"• Chi tiêu: {self._format_money(expense)}")
        has_food = any((
            health.nutrition.calories, health.nutrition.protein,
            health.nutrition.carbs, health.nutrition.fat,
        ))
        if has_food:
            calorie_text = f"{health.nutrition.calories}"
            if health.metrics:
                calorie_text += f" / {health.metrics.target_calories}"
            lines.append(f"• {calorie_text} kcal")
        if health.today:
            if health.today.steps is not None:
                lines.append(f"• {health.today.steps:,} bước".replace(",", "."))
            if health.today.water_ml is not None:
                lines.append(f"• {health.today.water_ml:,} ml nước".replace(",", "."))
            if health.today.sleep_hours is not None:
                lines.append(f"• {health.today.sleep_hours} giờ ngủ")
            if health.today.exercise_minutes is not None:
                lines.append(f"• {health.today.exercise_minutes} phút vận động")
        if journal:
            lines.append(f"• Tâm trạng: {MOOD_LABELS[journal.mood]}")
        self.service.create_for_enabled_channels(
            event_type=NotificationEventType.DAILY_SUMMARY,
            title="Tổng kết hôm nay", message="\n".join(lines),
            scheduled_for=now, dedupe_key=f"daily-summary:{day.isoformat()}",
            related_entity_type="daily_summary",
        )

    @staticmethod
    def _format_money(value: Decimal) -> str:
        return f"{value:,.0f}".replace(",", ".") + " ₫"

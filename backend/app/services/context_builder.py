from datetime import date, datetime, time, timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.time import local_day_utc_bounds, utc_now_naive, utc_to_local
from app.models.calendar import Schedule
from app.models.finance import Transaction, TransactionCategory, TransactionType
from app.models.journal import JournalEntry
from app.services.health import health_summary
from app.services.recurrence import expand_schedule_range


class ContextBuilder:
    def __init__(self, db: Session):
        self.db = db

    def build(self, prompt: str, today: date | None = None) -> tuple[dict, list[str]]:
        local_today = today or utc_to_local(utc_now_naive()).date()
        text = prompt.casefold()
        start, end, period = self._period(text, local_today)
        explicit: set[str] = set()
        keywords = {
            "finance": ("chi tiêu", "tiêu", "thu nhập", "tài chính", "ngân sách", "tiền", "expense", "income"),
            "calendar": ("lịch", "bận", "sự kiện", "schedule", "calendar"),
            "health": ("sức khỏe", "ngủ", "nước", "bước", "vận động", "health", "habit", "thói quen"),
            "nutrition": ("dinh dưỡng", "calo", "protein", "carb", "chất béo", "ăn", "nutrition"),
            "journal": ("nhật ký", "tâm trạng", "cảm xúc", "journal", "mood"),
        }
        for domain, terms in keywords.items():
            if any(term in text for term in terms):
                explicit.add(domain)
        domains = explicit or set(keywords)
        context: dict = {"period": {"label": period, "start": start.isoformat(), "end": end.isoformat()}}
        if "finance" in domains:
            context["finance"] = self._finance(start, end)
        if "calendar" in domains:
            context["calendar"] = self._calendar(start, end)
        if domains.intersection({"health", "nutrition"}):
            summary = health_summary(self.db, end)
            if "health" in domains:
                context["health"] = {
                    "metrics": summary.metrics.model_dump(mode="json") if summary.metrics else None,
                    "today": summary.today.model_dump(mode="json") if summary.today else None,
                }
            if "nutrition" in domains:
                context["nutrition"] = summary.nutrition.model_dump(mode="json")
        if "journal" in domains:
            include_content = any(term in text for term in keywords["journal"])
            context["journal"] = self._journal(start, end, include_content)
        return context, sorted(domains)

    @staticmethod
    def _period(text: str, today: date) -> tuple[date, date, str]:
        if any(term in text for term in ("tháng", "month")):
            start = today.replace(day=1)
            next_month = (start.replace(day=28) + timedelta(days=4)).replace(day=1)
            return start, next_month - timedelta(days=1), "month"
        if any(term in text for term in ("tuần", "week")):
            start = today - timedelta(days=today.weekday())
            return start, start + timedelta(days=6), "week"
        if any(term in text for term in ("ngày mai", "tomorrow")):
            tomorrow = today + timedelta(days=1)
            return tomorrow, tomorrow, "tomorrow"
        return today, today, "today"

    def _finance(self, start: date, end: date) -> dict:
        totals = {}
        for transaction_type in (TransactionType.INCOME, TransactionType.EXPENSE):
            value = self.db.scalar(select(func.coalesce(func.sum(Transaction.amount), 0)).where(
                Transaction.type == transaction_type,
                Transaction.transaction_date.between(start, end),
            ))
            totals[transaction_type.value.lower()] = str(Decimal(value))
        rows = self.db.execute(
            select(TransactionCategory.name, func.sum(Transaction.amount).label("amount"))
            .join(Transaction, Transaction.category_id == TransactionCategory.id)
            .where(Transaction.type == TransactionType.EXPENSE, Transaction.transaction_date.between(start, end))
            .group_by(TransactionCategory.id, TransactionCategory.name)
            .order_by(func.sum(Transaction.amount).desc())
            .limit(5)
        ).all()
        totals["top_expense_categories"] = [{"name": name, "amount": str(amount)} for name, amount in rows]
        return totals

    def _calendar(self, start: date, end: date) -> dict:
        start_dt, _ = local_day_utc_bounds(start)
        _, end_dt = local_day_utc_bounds(end)
        schedules = list(self.db.scalars(select(Schedule).where(Schedule.start_datetime < end_dt)).all())
        occurrences = expand_schedule_range(schedules, start_dt, end_dt)
        return {
            "total_events": len(occurrences),
            "completed_events": sum(1 for item in occurrences if item.schedule.completed),
            "total_scheduled_hours": round(sum((item.end - item.start).total_seconds() for item in occurrences) / 3600, 2),
            "events": [
                {"title": item.schedule.title, "start": item.start.isoformat(), "end": item.end.isoformat(), "completed": item.schedule.completed}
                for item in occurrences[:20]
            ],
        }

    def _journal(self, start: date, end: date, include_content: bool) -> dict:
        entries = list(self.db.scalars(
            select(JournalEntry).where(JournalEntry.entry_date.between(start, end)).order_by(JournalEntry.entry_date.desc()).limit(7)
        ).all())
        items = []
        for entry in entries:
            mood = entry.mood.value if hasattr(entry.mood, "value") else str(entry.mood)
            item = {"date": entry.entry_date.isoformat(), "mood": mood, "tags": [tag.name for tag in entry.tags]}
            if include_content:
                item["content"] = entry.content[:2000]
            items.append(item)
        return {"entry_count": len(entries), "entries": items}

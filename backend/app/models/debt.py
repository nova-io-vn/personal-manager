from datetime import date, datetime, timezone
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import Date, DateTime, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class DebtDirection(StrEnum):
    OWED_BY_ME = "OWED_BY_ME"
    OWED_TO_ME = "OWED_TO_ME"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Debt(Base):
    __tablename__ = "debts"

    id: Mapped[int] = mapped_column(primary_key=True)
    person: Mapped[str] = mapped_column(String(120))
    direction: Mapped[DebtDirection] = mapped_column(String(20), index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    paid_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal("0.00"))
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

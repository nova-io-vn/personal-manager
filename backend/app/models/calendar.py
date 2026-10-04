from datetime import datetime, timezone
from enum import StrEnum

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class RepeatType(StrEnum):
    NONE = "NONE"
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ScheduleCategory(Base):
    __tablename__ = "schedule_categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    color: Mapped[str] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    schedules: Mapped[list["Schedule"]] = relationship(back_populates="category")


class Schedule(Base):
    __tablename__ = "schedules"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    start_datetime: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    end_datetime: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    category_id: Mapped[int | None] = mapped_column(ForeignKey("schedule_categories.id"), nullable=True)
    color: Mapped[str | None] = mapped_column(String(20), nullable=True)
    reminder_minutes: Mapped[int] = mapped_column(Integer, default=0)
    repeat_type: Mapped[RepeatType] = mapped_column(String(20), default=RepeatType.NONE)
    repeat_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    category: Mapped[ScheduleCategory | None] = relationship(back_populates="schedules")

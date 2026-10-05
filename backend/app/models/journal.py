from datetime import date, datetime, timezone
from enum import StrEnum

from sqlalchemy import Column, Date, DateTime, ForeignKey, String, Table, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Mood(StrEnum):
    VERY_BAD = "VERY_BAD"
    BAD = "BAD"
    NEUTRAL = "NEUTRAL"
    GOOD = "GOOD"
    VERY_GOOD = "VERY_GOOD"


journal_entry_tags = Table(
    "journal_entry_tags",
    Base.metadata,
    Column("entry_id", ForeignKey("journal_entries.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", ForeignKey("journal_tags.id", ondelete="CASCADE"), primary_key=True),
)


class JournalTag(Base):
    __tablename__ = "journal_tags"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(60), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class JournalEntry(Base):
    __tablename__ = "journal_entries"

    id: Mapped[int] = mapped_column(primary_key=True)
    entry_date: Mapped[date] = mapped_column(Date, unique=True, index=True)
    mood: Mapped[Mood] = mapped_column(String(20))
    content: Mapped[str] = mapped_column(Text)
    drawing_data: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    tags: Mapped[list[JournalTag]] = relationship(secondary=journal_entry_tags, lazy="selectin")

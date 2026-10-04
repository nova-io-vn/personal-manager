from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.journal import JournalEntry, JournalTag, Mood


def get_entry_by_date(db: Session, entry_date: date) -> JournalEntry | None:
    return db.scalar(select(JournalEntry).options(selectinload(JournalEntry.tags)).where(JournalEntry.entry_date == entry_date))


def list_entries(
    db: Session, start_date: date | None = None, end_date: date | None = None,
    mood: Mood | None = None, tag: str | None = None,
) -> list[JournalEntry]:
    query = select(JournalEntry).options(selectinload(JournalEntry.tags)).order_by(JournalEntry.entry_date.desc())
    if start_date is not None:
        query = query.where(JournalEntry.entry_date >= start_date)
    if end_date is not None:
        query = query.where(JournalEntry.entry_date <= end_date)
    if mood is not None:
        query = query.where(JournalEntry.mood == mood)
    if tag:
        query = query.join(JournalEntry.tags).where(JournalTag.name == tag.strip().lower())
    return list(db.scalars(query).unique().all())


def list_tags(db: Session) -> list[JournalTag]:
    return list(db.scalars(select(JournalTag).order_by(JournalTag.name)).all())

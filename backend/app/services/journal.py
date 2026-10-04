from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.journal import JournalEntry, JournalTag
from app.repositories.journal import get_entry_by_date


class JournalTagNotFoundError(Exception):
    pass


def upsert_entry(db: Session, entry_date: date, data) -> JournalEntry:
    tags = list(db.scalars(select(JournalTag).where(JournalTag.id.in_(set(data.tag_ids)))).all()) if data.tag_ids else []
    if len(tags) != len(set(data.tag_ids)):
        raise JournalTagNotFoundError("Journal tag not found")
    entry = get_entry_by_date(db, entry_date)
    if entry is None:
        entry = JournalEntry(entry_date=entry_date, mood=data.mood, content=data.content)
        db.add(entry)
    else:
        entry.mood = data.mood
        entry.content = data.content
    entry.tags = tags
    db.commit()
    db.refresh(entry)
    return entry

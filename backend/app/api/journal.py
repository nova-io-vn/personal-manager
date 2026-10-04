from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.journal import JournalTag, Mood
from app.repositories.journal import get_entry_by_date, list_entries, list_tags
from app.schemas.journal import JournalRead, JournalTagCreate, JournalTagRead, JournalUpsert
from app.services.journal import JournalTagNotFoundError, upsert_entry

router = APIRouter(tags=["journal"])


@router.get("/journals", response_model=list[JournalRead])
def read_journals(
    start_date: date | None = None, end_date: date | None = None,
    mood: Mood | None = None, tag: str | None = None, db: Session = Depends(get_db),
):
    if start_date and end_date and end_date < start_date:
        raise HTTPException(status_code=422, detail="end_date must be on or after start_date")
    return list_entries(db, start_date, end_date, mood, tag)


@router.get("/journals/{entry_date}", response_model=JournalRead)
def read_journal(entry_date: date, db: Session = Depends(get_db)):
    entry = get_entry_by_date(db, entry_date)
    if entry is None:
        raise HTTPException(status_code=404, detail="Journal entry not found")
    return entry


@router.put("/journals/{entry_date}", response_model=JournalRead)
def save_journal(entry_date: date, data: JournalUpsert, db: Session = Depends(get_db)):
    try:
        return upsert_entry(db, entry_date, data)
    except JournalTagNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete("/journals/{entry_date}", status_code=204)
def delete_journal(entry_date: date, db: Session = Depends(get_db)):
    entry = get_entry_by_date(db, entry_date)
    if entry is None:
        raise HTTPException(status_code=404, detail="Journal entry not found")
    db.delete(entry)
    db.commit()
    return Response(status_code=204)


@router.get("/journal-tags", response_model=list[JournalTagRead])
def read_journal_tags(db: Session = Depends(get_db)):
    return list_tags(db)


@router.post("/journal-tags", response_model=JournalTagRead, status_code=201)
def create_journal_tag(data: JournalTagCreate, db: Session = Depends(get_db)):
    tag = JournalTag(name=data.name)
    db.add(tag)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Journal tag already exists") from exc
    db.refresh(tag)
    return tag

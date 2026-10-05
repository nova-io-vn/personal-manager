from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.core.time import to_utc_naive
from app.models.calendar import Schedule, ScheduleCategory
from app.repositories.calendar import list_schedules
from app.schemas.calendar import (
    ScheduleCategoryCreate, ScheduleCategoryRead, ScheduleCreate, ScheduleOccurrenceCompletion,
    ScheduleRead, ScheduleUpdate,
)
from app.services.recurrence import expand_schedule_range
from app.services.schedule_occurrences import (
    is_valid_occurrence, occurrence_completion, set_occurrence_completion,
)

router = APIRouter(tags=["calendar"])


def _not_found(message: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)


def _validate_category(db: Session, category_id: int | None) -> None:
    if category_id is not None and db.get(ScheduleCategory, category_id) is None:
        raise _not_found("Schedule category not found")


def _validate_update(values: dict, current: Schedule) -> None:
    start = values.get("start_datetime", current.start_datetime)
    end = values.get("end_datetime", current.end_datetime)
    if end <= start:
        raise HTTPException(status_code=422, detail="end_datetime must be after start_datetime")
    repeat_type = values.get("repeat_type", current.repeat_type)
    repeat_until = values.get("repeat_until", current.repeat_until)
    if repeat_type == "NONE" and repeat_until is not None:
        raise HTTPException(status_code=422, detail="repeat_until requires a repeating schedule")
    if repeat_until is not None and repeat_until < start:
        raise HTTPException(status_code=422, detail="repeat_until must be on or after start_datetime")


@router.get("/schedule-categories", response_model=list[ScheduleCategoryRead])
def get_schedule_categories(db: Session = Depends(get_db)):
    return list(db.scalars(select(ScheduleCategory).order_by(ScheduleCategory.name)).all())


@router.post("/schedule-categories", response_model=ScheduleCategoryRead, status_code=status.HTTP_201_CREATED)
def create_schedule_category(data: ScheduleCategoryCreate, db: Session = Depends(get_db)):
    category = ScheduleCategory(**data.model_dump())
    db.add(category)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=409, detail="Schedule category already exists")
    db.refresh(category)
    return category


@router.get("/schedules", response_model=list[ScheduleRead])
def get_schedules(
    start: datetime | None = None, end: datetime | None = None,
    category_id: int | None = None, completed: bool | None = None,
    db: Session = Depends(get_db),
):
    if start is not None and end is not None and end <= start:
        raise HTTPException(status_code=422, detail="end must be after start")
    _validate_category(db, category_id)
    schedules = list_schedules(db, start, end, category_id, completed)
    if start is None or end is None:
        return schedules
    return [
        ScheduleRead.model_validate(occurrence.schedule).model_copy(update={
            "start_datetime": occurrence.start,
            "end_datetime": occurrence.end,
            "completed": occurrence_completion(db, occurrence.schedule, occurrence.start),
            "series_start_datetime": occurrence.schedule.start_datetime,
            "is_recurring_occurrence": occurrence.start != to_utc_naive(occurrence.schedule.start_datetime),
        })
        for occurrence in expand_schedule_range(schedules, start, end)
    ]


@router.patch("/schedules/{schedule_id}/occurrence-completion", response_model=ScheduleRead)
def update_occurrence_completion(
    schedule_id: int,
    data: ScheduleOccurrenceCompletion,
    db: Session = Depends(get_db),
):
    schedule = db.get(Schedule, schedule_id)
    if schedule is None:
        raise _not_found("Schedule not found")
    if not is_valid_occurrence(schedule, data.occurrence_start):
        raise HTTPException(status_code=422, detail="occurrence_start is not a valid schedule occurrence")
    occurrence = set_occurrence_completion(db, schedule, data.occurrence_start, data.completed)
    result = ScheduleRead.model_validate(schedule).model_copy(update={
        "start_datetime": occurrence.occurrence_start,
        "end_datetime": occurrence.occurrence_start + (schedule.end_datetime - schedule.start_datetime),
        "completed": occurrence.completed,
        "series_start_datetime": schedule.start_datetime,
            "is_recurring_occurrence": occurrence.occurrence_start != schedule.start_datetime.replace(tzinfo=None),
    })
    return result


@router.post("/schedules", response_model=ScheduleRead, status_code=status.HTTP_201_CREATED)
def create_schedule(data: ScheduleCreate, db: Session = Depends(get_db)):
    _validate_category(db, data.category_id)
    schedule = Schedule(**data.model_dump())
    db.add(schedule)
    db.commit()
    db.refresh(schedule)
    return schedule


@router.get("/schedules/{schedule_id}", response_model=ScheduleRead)
def get_schedule(schedule_id: int, db: Session = Depends(get_db)):
    schedule = db.get(Schedule, schedule_id)
    if schedule is None:
        raise _not_found("Schedule not found")
    return schedule


@router.patch("/schedules/{schedule_id}", response_model=ScheduleRead)
def update_schedule(schedule_id: int, data: ScheduleUpdate, db: Session = Depends(get_db)):
    schedule = db.get(Schedule, schedule_id)
    if schedule is None:
        raise _not_found("Schedule not found")
    values = data.model_dump(exclude_unset=True)
    _validate_category(db, values.get("category_id", schedule.category_id))
    _validate_update(values, schedule)
    for key, value in values.items():
        setattr(schedule, key, value)
    db.commit()
    db.refresh(schedule)
    return schedule


@router.delete("/schedules/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_schedule(schedule_id: int, db: Session = Depends(get_db)):
    schedule = db.get(Schedule, schedule_id)
    if schedule is None:
        raise _not_found("Schedule not found")
    db.delete(schedule)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

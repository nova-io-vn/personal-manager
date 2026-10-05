from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.time import utc_now_naive
from app.models.calendar import Schedule, ScheduleOccurrenceState
from app.services.recurrence import expand_occurrences


def _occurrence_key(value: datetime) -> datetime:
    # Schedule timestamps are currently stored as local wall time by the
    # existing SQLite model. Keep that established calendar convention here.
    return value.replace(tzinfo=None)


def is_valid_occurrence(schedule: Schedule, occurrence_start: datetime) -> bool:
    start = _occurrence_key(occurrence_start)
    return any(
        item.start == start
        for item in expand_occurrences(schedule, start, start + timedelta(microseconds=1))
    )


def occurrence_completion(
    db: Session, schedule: Schedule, occurrence_start: datetime
) -> bool:
    start = _occurrence_key(occurrence_start)
    state = db.scalar(
        select(ScheduleOccurrenceState).where(
            ScheduleOccurrenceState.schedule_id == schedule.id,
            ScheduleOccurrenceState.occurrence_start == start,
        )
    )
    # Existing series-level completion remains a fallback for compatibility;
    # an occurrence row can override it independently.
    return state.completed if state is not None else schedule.completed


def set_occurrence_completion(
    db: Session, schedule: Schedule, occurrence_start: datetime, completed: bool
) -> ScheduleOccurrenceState:
    start = _occurrence_key(occurrence_start)
    state = db.scalar(
        select(ScheduleOccurrenceState).where(
            ScheduleOccurrenceState.schedule_id == schedule.id,
            ScheduleOccurrenceState.occurrence_start == start,
        )
    )
    if state is None:
        state = ScheduleOccurrenceState(
            schedule_id=schedule.id,
            occurrence_start=start,
            completed=completed,
            completed_at=utc_now_naive() if completed else None,
        )
        db.add(state)
    else:
        state.completed = completed
        state.completed_at = utc_now_naive() if completed else None
    db.commit()
    db.refresh(state)
    return state

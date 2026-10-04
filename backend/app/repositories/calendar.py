from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.calendar import RepeatType, Schedule, ScheduleCategory


def seed_schedule_categories(db: Session) -> None:
    if db.scalar(select(ScheduleCategory.id).limit(1)) is not None:
        return
    categories = [
        ("Học tập", "#6B8AFD"), ("Công việc", "#8A72D8"), ("Thể thao", "#3CA982"),
        ("Cá nhân", "#E39A4A"), ("Quan trọng", "#D96969"), ("Ăn uống", "#C88A6A"),
    ]
    db.add_all(ScheduleCategory(name=name, color=color) for name, color in categories)
    db.commit()


def list_schedules(
    db: Session, start: datetime | None, end: datetime | None,
    category_id: int | None, completed: bool | None,
) -> list[Schedule]:
    query = select(Schedule).order_by(Schedule.start_datetime, Schedule.id)
    if start is not None:
        if end is not None:
            query = query.where(Schedule.start_datetime < end)
        query = query.where(
            (Schedule.end_datetime > start)
            | (
                (Schedule.repeat_type != "NONE")
                & ((Schedule.repeat_until.is_(None)) | (Schedule.repeat_until >= start))
            )
        )
    if end is not None:
        if start is None:
            query = query.where(Schedule.start_datetime < end)
    if category_id is not None:
        query = query.where(Schedule.category_id == category_id)
    if completed is not None:
        query = query.where(Schedule.completed == completed)
    return list(db.scalars(query).all())

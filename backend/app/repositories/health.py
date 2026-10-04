from datetime import date, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.health import BodyMeasurement, BodyProfile, Food, FoodLog, HealthDailyLog, MealType


def get_profile(db: Session) -> BodyProfile | None:
    return db.scalar(select(BodyProfile).order_by(BodyProfile.id).limit(1))


def list_measurements(db: Session, start: datetime | None = None, end: datetime | None = None) -> list[BodyMeasurement]:
    query = select(BodyMeasurement).order_by(BodyMeasurement.recorded_at.desc(), BodyMeasurement.id.desc())
    if start is not None:
        query = query.where(BodyMeasurement.recorded_at >= start)
    if end is not None:
        query = query.where(BodyMeasurement.recorded_at <= end)
    return list(db.scalars(query).all())


def list_daily_logs(db: Session, start: date | None = None, end: date | None = None) -> list[HealthDailyLog]:
    query = select(HealthDailyLog).order_by(HealthDailyLog.date.desc())
    if start is not None:
        query = query.where(HealthDailyLog.date >= start)
    if end is not None:
        query = query.where(HealthDailyLog.date <= end)
    return list(db.scalars(query).all())


def list_foods(db: Session, search: str | None = None) -> list[Food]:
    query = select(Food).order_by(Food.name)
    if search:
        query = query.where(Food.name.ilike(f"%{search.strip()}%"))
    return list(db.scalars(query).all())


def list_food_logs(db: Session, logged_date: date | None = None, meal_type: MealType | None = None) -> list[FoodLog]:
    query = select(FoodLog).options(selectinload(FoodLog.food)).order_by(FoodLog.logged_date.desc(), FoodLog.created_at)
    if logged_date is not None:
        query = query.where(FoodLog.logged_date == logged_date)
    if meal_type is not None:
        query = query.where(FoodLog.meal_type == meal_type)
    return list(db.scalars(query).all())

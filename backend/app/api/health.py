from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.health import BodyMeasurement, BodyProfile, Food, FoodLog, HealthDailyLog, MealType
from app.repositories.health import get_profile, list_daily_logs, list_food_logs, list_foods, list_measurements
from app.schemas.health import (
    BodyMeasurementCreate, BodyMeasurementRead, BodyMeasurementUpdate, BodyProfileInput, BodyProfileRead,
    DailyHealthCreate, DailyHealthInput, DailyHealthRead, FoodCreate, FoodLogCreate, FoodLogRead,
    FoodLogUpdate, FoodRead, FoodUpdate, HealthSummary, NutritionSummary,
)
from app.services.health import health_summary, nutrition_summary

router = APIRouter(tags=["health", "nutrition"])


def _not_found(message: str) -> HTTPException:
    return HTTPException(status_code=404, detail=message)


@router.get("/health/profile", response_model=BodyProfileRead)
def read_profile(db: Session = Depends(get_db)):
    profile = get_profile(db)
    if profile is None:
        raise _not_found("Body profile not found")
    return profile


@router.put("/health/profile", response_model=BodyProfileRead)
def upsert_profile(data: BodyProfileInput, db: Session = Depends(get_db)):
    profile = get_profile(db)
    if profile is None:
        profile = BodyProfile(**data.model_dump())
        db.add(profile)
    else:
        for key, value in data.model_dump().items():
            setattr(profile, key, value)
    db.commit()
    db.refresh(profile)
    return profile


@router.get("/health/measurements", response_model=list[BodyMeasurementRead])
def read_measurements(start: datetime | None = None, end: datetime | None = None, db: Session = Depends(get_db)):
    if start and end and end < start:
        raise HTTPException(status_code=422, detail="end must be on or after start")
    return list_measurements(db, start, end)


@router.post("/health/measurements", response_model=BodyMeasurementRead, status_code=201)
def create_measurement(data: BodyMeasurementCreate, db: Session = Depends(get_db)):
    measurement = BodyMeasurement(**data.model_dump())
    db.add(measurement)
    db.commit()
    db.refresh(measurement)
    return measurement


@router.patch("/health/measurements/{measurement_id}", response_model=BodyMeasurementRead)
def update_measurement(measurement_id: int, data: BodyMeasurementUpdate, db: Session = Depends(get_db)):
    measurement = db.get(BodyMeasurement, measurement_id)
    if measurement is None:
        raise _not_found("Body measurement not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(measurement, key, value)
    db.commit()
    db.refresh(measurement)
    return measurement


@router.delete("/health/measurements/{measurement_id}", status_code=204)
def delete_measurement(measurement_id: int, db: Session = Depends(get_db)):
    measurement = db.get(BodyMeasurement, measurement_id)
    if measurement is None:
        raise _not_found("Body measurement not found")
    db.delete(measurement)
    db.commit()
    return Response(status_code=204)


@router.get("/health/daily", response_model=list[DailyHealthRead])
def read_daily_logs(start: date | None = None, end: date | None = None, db: Session = Depends(get_db)):
    if start and end and end < start:
        raise HTTPException(status_code=422, detail="end must be on or after start")
    return list_daily_logs(db, start, end)


@router.post("/health/daily", response_model=DailyHealthRead, status_code=201)
def create_daily_log(data: DailyHealthCreate, db: Session = Depends(get_db)):
    log = HealthDailyLog(**data.model_dump())
    db.add(log)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Daily health log already exists") from exc
    db.refresh(log)
    return log


@router.put("/health/daily/{log_date}", response_model=DailyHealthRead)
def upsert_daily_log(log_date: date, data: DailyHealthInput, db: Session = Depends(get_db)):
    log = db.scalar(select(HealthDailyLog).where(HealthDailyLog.date == log_date))
    if log is None:
        log = HealthDailyLog(date=log_date, **data.model_dump())
        db.add(log)
    else:
        for key, value in data.model_dump().items():
            setattr(log, key, value)
    db.commit()
    db.refresh(log)
    return log


@router.get("/health/summary", response_model=HealthSummary)
def read_health_summary(summary_date: date | None = Query(default=None, alias="date"), db: Session = Depends(get_db)):
    return health_summary(db, summary_date or date.today())


@router.get("/foods", response_model=list[FoodRead])
def read_foods(search: str | None = None, db: Session = Depends(get_db)):
    return list_foods(db, search)


@router.post("/foods", response_model=FoodRead, status_code=201)
def create_food(data: FoodCreate, db: Session = Depends(get_db)):
    food = Food(**data.model_dump())
    db.add(food)
    db.commit()
    db.refresh(food)
    return food


@router.get("/foods/{food_id}", response_model=FoodRead)
def read_food(food_id: int, db: Session = Depends(get_db)):
    food = db.get(Food, food_id)
    if food is None:
        raise _not_found("Food not found")
    return food


@router.patch("/foods/{food_id}", response_model=FoodRead)
def update_food(food_id: int, data: FoodUpdate, db: Session = Depends(get_db)):
    food = db.get(Food, food_id)
    if food is None:
        raise _not_found("Food not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(food, key, value)
    db.commit()
    db.refresh(food)
    return food


@router.delete("/foods/{food_id}", status_code=204)
def delete_food(food_id: int, db: Session = Depends(get_db)):
    food = db.get(Food, food_id)
    if food is None:
        raise _not_found("Food not found")
    if food.logs:
        raise HTTPException(status_code=409, detail="Cannot delete a food with logs")
    db.delete(food)
    db.commit()
    return Response(status_code=204)


@router.get("/food-logs", response_model=list[FoodLogRead])
def read_food_logs(logged_date: date | None = None, meal_type: MealType | None = None, db: Session = Depends(get_db)):
    return list_food_logs(db, logged_date, meal_type)


@router.post("/food-logs", response_model=FoodLogRead, status_code=201)
def create_food_log(data: FoodLogCreate, db: Session = Depends(get_db)):
    if db.get(Food, data.food_id) is None:
        raise _not_found("Food not found")
    log = FoodLog(**data.model_dump())
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


@router.patch("/food-logs/{log_id}", response_model=FoodLogRead)
def update_food_log(log_id: int, data: FoodLogUpdate, db: Session = Depends(get_db)):
    log = db.get(FoodLog, log_id)
    if log is None:
        raise _not_found("Food log not found")
    values = data.model_dump(exclude_unset=True)
    if "food_id" in values and db.get(Food, values["food_id"]) is None:
        raise _not_found("Food not found")
    for key, value in values.items():
        setattr(log, key, value)
    db.commit()
    db.refresh(log)
    return log


@router.delete("/food-logs/{log_id}", status_code=204)
def delete_food_log(log_id: int, db: Session = Depends(get_db)):
    log = db.get(FoodLog, log_id)
    if log is None:
        raise _not_found("Food log not found")
    db.delete(log)
    db.commit()
    return Response(status_code=204)


@router.get("/nutrition/summary", response_model=NutritionSummary)
def read_nutrition_summary(summary_date: date | None = Query(default=None, alias="date"), db: Session = Depends(get_db)):
    return nutrition_summary(db, summary_date or date.today())

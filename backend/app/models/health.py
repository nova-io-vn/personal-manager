from datetime import date, datetime, timezone
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Sex(StrEnum):
    MALE = "MALE"
    FEMALE = "FEMALE"


class ActivityLevel(StrEnum):
    SEDENTARY = "SEDENTARY"
    LIGHT = "LIGHT"
    MODERATE = "MODERATE"
    ACTIVE = "ACTIVE"
    VERY_ACTIVE = "VERY_ACTIVE"


class HealthGoal(StrEnum):
    LOSE_WEIGHT = "LOSE_WEIGHT"
    MAINTAIN = "MAINTAIN"
    GAIN_WEIGHT = "GAIN_WEIGHT"


class MealType(StrEnum):
    BREAKFAST = "BREAKFAST"
    LUNCH = "LUNCH"
    DINNER = "DINNER"
    SNACK = "SNACK"


class BodyProfile(Base):
    __tablename__ = "body_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    height_cm: Mapped[Decimal] = mapped_column(Numeric(6, 2))
    weight_kg: Mapped[Decimal] = mapped_column(Numeric(6, 2))
    age: Mapped[int] = mapped_column(Integer)
    sex: Mapped[Sex] = mapped_column(String(10))
    activity_level: Mapped[ActivityLevel] = mapped_column(String(20))
    goal: Mapped[HealthGoal] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)


class BodyMeasurement(Base):
    __tablename__ = "body_measurements"

    id: Mapped[int] = mapped_column(primary_key=True)
    weight_kg: Mapped[Decimal] = mapped_column(Numeric(6, 2))
    waist_cm: Mapped[Decimal | None] = mapped_column(Numeric(6, 2), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class HealthDailyLog(Base):
    __tablename__ = "health_daily_logs"
    __table_args__ = (UniqueConstraint("date", name="uq_health_daily_date"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    date: Mapped[date] = mapped_column(Date, index=True)
    sleep_hours: Mapped[Decimal | None] = mapped_column(Numeric(4, 2), nullable=True)
    water_ml: Mapped[int | None] = mapped_column(Integer, nullable=True)
    steps: Mapped[int | None] = mapped_column(Integer, nullable=True)
    exercise_type: Mapped[str | None] = mapped_column(String(120), nullable=True)
    exercise_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)


class Food(Base):
    __tablename__ = "foods"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(160), index=True)
    serving_quantity: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    serving_unit: Mapped[str] = mapped_column(String(30))
    calories: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    protein: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0"))
    carbs: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0"))
    fat: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    logs: Mapped[list["FoodLog"]] = relationship(back_populates="food")


class FoodLog(Base):
    __tablename__ = "food_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    food_id: Mapped[int] = mapped_column(ForeignKey("foods.id"), index=True)
    quantity: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    meal_type: Mapped[MealType] = mapped_column(String(20), index=True)
    logged_date: Mapped[date] = mapped_column(Date, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    food: Mapped[Food] = relationship(back_populates="logs")

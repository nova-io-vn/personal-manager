from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.health import ActivityLevel, HealthGoal, MealType, Sex


class BodyProfileInput(BaseModel):
    height_cm: Decimal = Field(gt=0, le=300)
    weight_kg: Decimal = Field(gt=0, le=700)
    age: int = Field(gt=0, le=130)
    sex: Sex
    activity_level: ActivityLevel
    goal: HealthGoal


class BodyProfileRead(BodyProfileInput):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
    updated_at: datetime


class BodyMeasurementCreate(BaseModel):
    weight_kg: Decimal = Field(gt=0, le=700)
    waist_cm: Decimal | None = Field(default=None, gt=0, le=400)
    note: str | None = Field(default=None, max_length=1000)
    recorded_at: datetime


class BodyMeasurementUpdate(BaseModel):
    weight_kg: Decimal | None = Field(default=None, gt=0, le=700)
    waist_cm: Decimal | None = Field(default=None, gt=0, le=400)
    note: str | None = Field(default=None, max_length=1000)
    recorded_at: datetime | None = None


class BodyMeasurementRead(BodyMeasurementCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime


class DailyHealthInput(BaseModel):
    sleep_hours: Decimal | None = Field(default=None, ge=0, le=24)
    water_ml: int | None = Field(default=None, ge=0)
    steps: int | None = Field(default=None, ge=0)
    exercise_type: str | None = Field(default=None, max_length=120)
    exercise_minutes: int | None = Field(default=None, ge=0, le=1440)
    note: str | None = Field(default=None, max_length=1000)


class DailyHealthCreate(DailyHealthInput):
    date: date


class DailyHealthRead(DailyHealthInput):
    model_config = ConfigDict(from_attributes=True)
    id: int
    date: date
    created_at: datetime
    updated_at: datetime


class FoodCreate(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    serving_quantity: Decimal = Field(gt=0)
    serving_unit: str = Field(min_length=1, max_length=30)
    calories: Decimal = Field(ge=0)
    protein: Decimal = Field(default=Decimal("0"), ge=0)
    carbs: Decimal = Field(default=Decimal("0"), ge=0)
    fat: Decimal = Field(default=Decimal("0"), ge=0)

    @field_validator("name", "serving_unit")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("value cannot be empty")
        return value.strip()


class FoodUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=160)
    serving_quantity: Decimal | None = Field(default=None, gt=0)
    serving_unit: str | None = Field(default=None, min_length=1, max_length=30)
    calories: Decimal | None = Field(default=None, ge=0)
    protein: Decimal | None = Field(default=None, ge=0)
    carbs: Decimal | None = Field(default=None, ge=0)
    fat: Decimal | None = Field(default=None, ge=0)


class FoodRead(FoodCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
    updated_at: datetime


class FoodLogCreate(BaseModel):
    food_id: int
    quantity: Decimal = Field(gt=0)
    meal_type: MealType
    logged_date: date


class FoodLogUpdate(BaseModel):
    food_id: int | None = None
    quantity: Decimal | None = Field(default=None, gt=0)
    meal_type: MealType | None = None
    logged_date: date | None = None


class FoodLogRead(FoodLogCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
    food: FoodRead


class NutritionTotals(BaseModel):
    calories: Decimal
    protein: Decimal
    carbs: Decimal
    fat: Decimal


class NutritionSummary(NutritionTotals):
    date: date
    meals: dict[MealType, list[FoodLogRead]]


class HealthMetrics(BaseModel):
    bmi: Decimal
    bmr: Decimal
    tdee: Decimal
    target_calories: Decimal


class HealthSummary(BaseModel):
    profile: BodyProfileRead | None
    metrics: HealthMetrics | None
    weight: Decimal | None
    weight_change: Decimal | None
    today: DailyHealthRead | None
    nutrition: NutritionTotals

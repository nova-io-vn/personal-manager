from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.health import ActivityLevel, BodyProfile, FoodLog, HealthGoal, MealType, Sex
from app.repositories.health import get_profile, list_food_logs, list_measurements
from app.schemas.health import HealthMetrics, HealthSummary, NutritionSummary, NutritionTotals


ACTIVITY_MULTIPLIERS: dict[ActivityLevel, Decimal] = {
    ActivityLevel.SEDENTARY: Decimal("1.2"),
    ActivityLevel.LIGHT: Decimal("1.375"),
    ActivityLevel.MODERATE: Decimal("1.55"),
    ActivityLevel.ACTIVE: Decimal("1.725"),
    ActivityLevel.VERY_ACTIVE: Decimal("1.9"),
}
GOAL_ADJUSTMENTS: dict[HealthGoal, Decimal] = {
    HealthGoal.LOSE_WEIGHT: Decimal("-300"),
    HealthGoal.MAINTAIN: Decimal("0"),
    HealthGoal.GAIN_WEIGHT: Decimal("300"),
}


def _round(value: Decimal, places: str = "0.1") -> Decimal:
    return value.quantize(Decimal(places), rounding=ROUND_HALF_UP)


def calculate_bmi(weight_kg: Decimal, height_cm: Decimal) -> Decimal:
    height_m = height_cm / Decimal("100")
    return _round(weight_kg / (height_m * height_m))


def calculate_bmr(weight_kg: Decimal, height_cm: Decimal, age: int, sex: Sex) -> Decimal:
    offset = Decimal("5") if sex == Sex.MALE else Decimal("-161")
    return _round(Decimal("10") * weight_kg + Decimal("6.25") * height_cm - Decimal("5") * age + offset)


def calculate_tdee(bmr: Decimal, activity_level: ActivityLevel) -> Decimal:
    return _round(bmr * ACTIVITY_MULTIPLIERS[activity_level])


def calculate_metrics(profile: BodyProfile, weight_kg: Decimal | None = None) -> HealthMetrics:
    weight = weight_kg if weight_kg is not None else profile.weight_kg
    bmi = calculate_bmi(weight, profile.height_cm)
    bmr = calculate_bmr(weight, profile.height_cm, profile.age, profile.sex)
    tdee = calculate_tdee(bmr, profile.activity_level)
    return HealthMetrics(bmi=bmi, bmr=bmr, tdee=tdee, target_calories=_round(tdee + GOAL_ADJUSTMENTS[profile.goal]))


def calculate_log_nutrition(log: FoodLog) -> NutritionTotals:
    ratio = log.quantity / log.food.serving_quantity
    return NutritionTotals(
        calories=_round(log.food.calories * ratio), protein=_round(log.food.protein * ratio),
        carbs=_round(log.food.carbs * ratio), fat=_round(log.food.fat * ratio),
    )


def nutrition_summary(db: Session, summary_date: date) -> NutritionSummary:
    logs = list_food_logs(db, logged_date=summary_date)
    totals = {"calories": Decimal("0"), "protein": Decimal("0"), "carbs": Decimal("0"), "fat": Decimal("0")}
    meals: dict[MealType, list[FoodLog]] = {meal: [] for meal in MealType}
    for log in logs:
        item = calculate_log_nutrition(log)
        totals["calories"] += item.calories
        totals["protein"] += item.protein
        totals["carbs"] += item.carbs
        totals["fat"] += item.fat
        meals[log.meal_type].append(log)
    return NutritionSummary(date=summary_date, meals=meals, **{key: _round(value) for key, value in totals.items()})


def health_summary(db: Session, summary_date: date) -> HealthSummary:
    profile = get_profile(db)
    measurements = list_measurements(db)
    weight = measurements[0].weight_kg if measurements else (profile.weight_kg if profile else None)
    weight_change = _round(measurements[0].weight_kg - measurements[1].weight_kg) if len(measurements) > 1 else None
    metrics = calculate_metrics(profile, weight) if profile and weight is not None else None
    from app.models.health import HealthDailyLog
    today = db.scalar(select(HealthDailyLog).where(HealthDailyLog.date == summary_date))
    nutrition = nutrition_summary(db, summary_date)
    return HealthSummary(profile=profile, metrics=metrics, weight=weight, weight_change=weight_change, today=today, nutrition=nutrition)

from decimal import Decimal

from app.models.health import ActivityLevel, Sex
from app.services.health import calculate_bmi, calculate_bmr, calculate_tdee


def profile_payload(**overrides):
    payload = {
        "height_cm": "175", "weight_kg": "70", "age": 30, "sex": "MALE",
        "activity_level": "MODERATE", "goal": "MAINTAIN",
    }
    payload.update(overrides)
    return payload


def test_deterministic_health_calculations():
    assert calculate_bmi(Decimal("70"), Decimal("175")) == Decimal("22.9")
    male_bmr = calculate_bmr(Decimal("70"), Decimal("175"), 30, Sex.MALE)
    female_bmr = calculate_bmr(Decimal("70"), Decimal("175"), 30, Sex.FEMALE)
    assert male_bmr == Decimal("1648.8")
    assert female_bmr == Decimal("1482.8")
    assert calculate_tdee(male_bmr, ActivityLevel.SEDENTARY) == Decimal("1978.6")
    assert calculate_tdee(male_bmr, ActivityLevel.VERY_ACTIVE) == Decimal("3132.7")


def test_profile_create_update_summary_and_invalid_values(client):
    created = client.put("/api/health/profile", json=profile_payload())
    assert created.status_code == 200
    assert created.json()["weight_kg"] == "70.00"
    summary = client.get("/api/health/summary", params={"date": "2026-10-04"}).json()
    assert summary["metrics"]["bmi"] == "22.9"
    assert summary["metrics"]["bmr"] == "1648.8"
    updated = client.put("/api/health/profile", json=profile_payload(weight_kg="72", sex="FEMALE"))
    assert updated.json()["id"] == created.json()["id"]
    assert client.put("/api/health/profile", json=profile_payload(height_cm=-1)).status_code == 422
    assert client.put("/api/health/profile", json=profile_payload(age=0)).status_code == 422


def test_measurement_history_and_daily_unique_behavior(client):
    first = client.post("/api/health/measurements", json={"weight_kg": "70", "recorded_at": "2026-10-01T08:00:00Z"})
    second = client.post("/api/health/measurements", json={"weight_kg": "69.5", "waist_cm": "80", "recorded_at": "2026-10-04T08:00:00Z"})
    assert first.status_code == second.status_code == 201
    measurements = client.get("/api/health/measurements", params={"start": "2026-10-02T00:00:00Z"}).json()
    assert len(measurements) == 1
    assert measurements[0]["weight_kg"] == "69.50"
    payload = {"date": "2026-10-04", "sleep_hours": "7.5", "water_ml": 1800, "steps": 6500, "exercise_minutes": 30}
    assert client.post("/api/health/daily", json=payload).status_code == 201
    assert client.post("/api/health/daily", json=payload).status_code == 409
    updated = client.put("/api/health/daily/2026-10-04", json={"sleep_hours": "8", "water_ml": 2000, "steps": 7000}).json()
    assert updated["steps"] == 7000
    assert client.post("/api/health/daily", json={"date": "2026-10-05", "steps": -1}).status_code == 422

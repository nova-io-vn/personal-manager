def create_food(client):
    return client.post("/api/foods", json={
        "name": "Ức gà", "serving_quantity": "100", "serving_unit": "g",
        "calories": "165", "protein": "31", "carbs": "0", "fat": "3.6",
    }).json()


def test_food_crud_log_and_proportional_summary(client):
    food = create_food(client)
    assert food["name"] == "Ức gà"
    log = client.post("/api/food-logs", json={
        "food_id": food["id"], "quantity": "150", "meal_type": "LUNCH", "logged_date": "2026-10-04",
    })
    assert log.status_code == 201
    summary = client.get("/api/nutrition/summary", params={"date": "2026-10-04"}).json()
    assert summary["calories"] == "247.5"
    assert summary["protein"] == "46.5"
    assert summary["fat"] == "5.4"
    assert len(summary["meals"]["LUNCH"]) == 1
    assert client.delete(f"/api/foods/{food['id']}").status_code == 409
    assert client.patch(f"/api/foods/{food['id']}", json={"calories": "170"}).json()["calories"] == "170.00"


def test_invalid_food_log_quantity_and_missing_food(client):
    food = create_food(client)
    invalid = {"food_id": food["id"], "quantity": "0", "meal_type": "SNACK", "logged_date": "2026-10-04"}
    assert client.post("/api/food-logs", json=invalid).status_code == 422
    invalid["quantity"] = "10"
    invalid["food_id"] = 9999
    assert client.post("/api/food-logs", json=invalid).status_code == 404

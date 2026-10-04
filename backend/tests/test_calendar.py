def category_id(client, name: str) -> int:
    return next(item["id"] for item in client.get("/api/schedule-categories").json() if item["name"] == name)


def schedule_payload(category_id: int, start: str = "2026-10-05T09:00:00+07:00") -> dict:
    return {
        "title": "Deep work",
        "description": "Focus block",
        "start_datetime": start,
        "end_datetime": "2026-10-05T10:30:00+07:00",
        "category_id": category_id,
        "color": "#607DCE",
        "reminder_minutes": 15,
        "repeat_type": "NONE",
        "completed": False,
    }


def test_schedule_crud_and_validation(client):
    category = category_id(client, "Học tập")
    created = client.post("/api/schedules", json=schedule_payload(category))
    assert created.status_code == 201
    schedule_id = created.json()["id"]
    assert client.get(f"/api/schedules/{schedule_id}").json()["title"] == "Deep work"
    assert client.patch(f"/api/schedules/{schedule_id}", json={"completed": True}).json()["completed"] is True
    assert client.delete(f"/api/schedules/{schedule_id}").status_code == 204
    invalid = schedule_payload(category)
    invalid["end_datetime"] = "2026-10-05T08:00:00+07:00"
    assert client.post("/api/schedules", json=invalid).status_code == 422


def test_schedule_range_includes_crossing_events_and_filters(client):
    category = category_id(client, "Công việc")
    crossing = schedule_payload(category, "2026-10-04T23:30:00+07:00")
    crossing["end_datetime"] = "2026-10-05T01:30:00+07:00"
    inside = schedule_payload(category)
    inside["title"] = "Planning"
    assert client.post("/api/schedules", json=crossing).status_code == 201
    assert client.post("/api/schedules", json=inside).status_code == 201
    response = client.get("/api/schedules", params={
        "start": "2026-10-05T00:00:00+07:00", "end": "2026-10-06T00:00:00+07:00",
        "category_id": category,
    })
    assert response.status_code == 200
    assert {item["title"] for item in response.json()} == {"Deep work", "Planning"}

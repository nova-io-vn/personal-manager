def test_journal_upsert_retrieve_filter_tags_and_delete(client):
    work = client.post("/api/journal-tags", json={"name": "Work"})
    assert work.status_code == 201
    tag_id = work.json()["id"]
    created = client.put("/api/journals/2026-10-04", json={"mood": "GOOD", "content": "Một ngày hiệu quả", "tag_ids": [tag_id]})
    assert created.status_code == 200
    assert created.json()["tags"][0]["name"] == "work"
    assert client.get("/api/journals/2026-10-04").json()["mood"] == "GOOD"
    updated = client.put("/api/journals/2026-10-04", json={"mood": "VERY_GOOD", "content": "Đã hoàn thành công việc", "tag_ids": [tag_id]})
    assert updated.json()["id"] == created.json()["id"]
    filtered = client.get("/api/journals", params={"mood": "VERY_GOOD", "tag": "work"}).json()
    assert len(filtered) == 1
    assert client.delete("/api/journals/2026-10-04").status_code == 204
    assert client.get("/api/journals/2026-10-04").status_code == 404


def test_journal_validation_and_date_filter(client):
    assert client.put("/api/journals/2026-10-04", json={"mood": "AMAZING", "content": "", "tag_ids": []}).status_code == 422
    client.put("/api/journals/2026-10-01", json={"mood": "NEUTRAL", "content": "Ngày đầu", "tag_ids": []})
    client.put("/api/journals/2026-10-05", json={"mood": "BAD", "content": "Ngày sau", "tag_ids": []})
    response = client.get("/api/journals", params={"start_date": "2026-10-02", "end_date": "2026-10-06"})
    assert [entry["entry_date"] for entry in response.json()] == ["2026-10-05"]

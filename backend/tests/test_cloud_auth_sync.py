from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings
from app.database.base import Base
from app.database.cloud import get_cloud_db
from app.main import app


@pytest.fixture()
def cloud_client(tmp_path, monkeypatch) -> Generator[TestClient, None, None]:
    engine = create_engine(f"sqlite:///{tmp_path / 'cloud.db'}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine, expire_on_commit=False)

    def override_cloud_db():
        with sessions() as db:
            yield db

    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-that-is-long-enough-32")
    get_settings.cache_clear()
    app.dependency_overrides[get_cloud_db] = override_cloud_db
    client = TestClient(app)
    yield client
    client.close()
    app.dependency_overrides.clear()
    get_settings.cache_clear()
    engine.dispose()


def test_register_login_and_sync_idempotency(cloud_client: TestClient):
    registered = cloud_client.post("/api/auth/register", json={"email": "sync@example.com", "password": "12345678"})
    assert registered.status_code == 201, registered.text
    auth = registered.json()
    headers = {"Authorization": f"Bearer {auth['access_token']}"}

    login = cloud_client.post("/api/auth/login", json={"email": "sync@example.com", "password": "12345678", "device_key": "tablet-1", "platform": "android"})
    assert login.status_code == 200, login.text
    tablet = login.json()
    tablet_headers = {"Authorization": f"Bearer {tablet['access_token']}"}
    change = {"entity_type": "tasks", "entity_id": "task-1", "operation": "UPSERT", "payload": {"title": "Đọc sách"}, "idempotency_key": "tablet-task-1-v1"}

    pushed = cloud_client.post("/api/sync/push", headers=tablet_headers, json={"device_id": tablet["device_id"], "changes": [change, change]})
    assert pushed.status_code == 200, pushed.text
    assert pushed.json()["accepted"] == 1
    assert pushed.json()["duplicates"] == 1

    pulled = cloud_client.get("/api/sync/pull", headers=headers)
    assert pulled.status_code == 200, pulled.text
    assert pulled.json()["changes"][0]["entity_id"] == "task-1"


def test_sync_requires_token(cloud_client: TestClient):
    response = cloud_client.get("/api/sync/pull")
    assert response.status_code == 401

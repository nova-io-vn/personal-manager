from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.database.base import Base
from app.database.database import get_db
from app.main import app
from app.repositories.finance import seed_categories
from app.repositories.calendar import seed_schedule_categories


@pytest.fixture()
def db_session(tmp_path) -> Generator[Session, None, None]:
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    TestingSession = sessionmaker(bind=engine, expire_on_commit=False)

    with TestingSession() as db:
        seed_categories(db)
        seed_schedule_categories(db)
        yield db
    engine.dispose()


@pytest.fixture()
def client(db_session: Session) -> Generator[TestClient, None, None]:

    def override_db():
        yield db_session

    app.dependency_overrides[get_db] = override_db
    # Avoid entering the app lifespan here: tests must never initialize the user's database.
    test_client = TestClient(app)
    yield test_client
    test_client.close()
    app.dependency_overrides.clear()

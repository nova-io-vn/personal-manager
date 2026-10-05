from collections.abc import Generator

from alembic import command
from alembic.config import Config
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings


def cloud_engine():
    url = get_settings().cloud_database_url.strip()
    if not url:
        raise RuntimeError("Cloud sync is not configured. Set CLOUD_DATABASE_URL.")
    return create_engine(url, pool_pre_ping=True, future=True)


def cloud_session_factory():
    return sessionmaker(bind=cloud_engine(), autoflush=False, autocommit=False, expire_on_commit=False)


def get_cloud_db() -> Generator[Session, None, None]:
    try:
        db = cloud_session_factory()()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    try:
        yield db
    finally:
        db.close()


def ensure_cloud_schema() -> None:
    settings = get_settings()
    if not settings.cloud_database_url.strip():
        return
    root = __import__("pathlib").Path(__file__).resolve().parents[2]
    config = Config(str(root / "alembic.ini"))
    config.set_main_option("script_location", str(root / "migrations"))
    config.set_main_option("sqlalchemy.url", settings.cloud_database_url.replace("%", "%%"))
    command.upgrade(config, "head")

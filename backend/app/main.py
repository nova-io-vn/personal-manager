from contextlib import asynccontextmanager
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import router
from app.config import get_settings
from app.database.database import SessionLocal, engine
from app.database.cloud import ensure_cloud_schema
from app.database.migrations import ensure_database_schema
from app.core.scheduler import create_scheduler
from app.models import calendar, debt, finance, health, journal, notification, tasks  # noqa: F401 - registers all models with Base
from app.repositories.finance import seed_categories
from app.repositories.calendar import seed_schedule_categories
from app.repositories.settings import seed_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    is_vercel = os.getenv("VERCEL") == "1"
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    ensure_database_schema(engine, settings.database_url)
    # Cloud migrations are applied by the release/deployment step. Running
    # them during every Vercel cold start adds latency and can exceed the
    # serverless function timeout.
    if not is_vercel and settings.cloud_database_url.strip() != settings.database_url.strip():
        ensure_cloud_schema()
    with SessionLocal() as db:
        seed_categories(db)
        seed_schedule_categories(db)
        seed_settings(db)
    scheduler = None if is_vercel else create_scheduler()
    app.state.notification_scheduler = scheduler
    try:
        if scheduler is not None:
            scheduler.start()
    except Exception:
        scheduler = None
        app.state.notification_scheduler = None
    try:
        yield
    finally:
        if scheduler is not None and scheduler.running:
            scheduler.shutdown(wait=False)


settings = get_settings()
app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)
app.include_router(router)

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.database.database import SessionLocal
from app.services.notification_engine import NotificationEngine

logger = logging.getLogger(__name__)


def run_notification_cycle() -> None:
    try:
        with SessionLocal() as db:
            NotificationEngine(db).run()
    except Exception:
        logger.exception("Notification cycle failed")


def create_scheduler() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        run_notification_cycle, "interval", minutes=1, id="notification-engine",
        replace_existing=True, coalesce=True, max_instances=1,
    )
    return scheduler

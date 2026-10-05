from fastapi import APIRouter

from app.api.finance import router as finance_router
from app.api.calendar import router as calendar_router
from app.api.health import router as health_router
from app.api.journal import router as journal_router
from app.api.notifications import router as notifications_router
from app.api.settings import router as settings_router
from app.api.data import router as data_router
from app.api.ai import router as ai_router
from app.api.tasks import router as tasks_router
from app.api.debts import router as debts_router

router = APIRouter(prefix="/api")
router.include_router(finance_router)
router.include_router(calendar_router)
router.include_router(health_router)
router.include_router(journal_router)
router.include_router(settings_router)
router.include_router(notifications_router)
router.include_router(data_router)
router.include_router(ai_router)
router.include_router(tasks_router)
router.include_router(debts_router)


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}

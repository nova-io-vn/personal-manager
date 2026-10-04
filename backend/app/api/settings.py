from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.repositories.settings import get_raw_settings, get_settings_view, seed_settings, update_settings
from app.schemas.notification import IntegrationTestResult, SettingsRead, SettingsUpdate, TelegramTestResult
from app.services.ai_service import AIService
from app.services.telegram_service import TelegramService

router = APIRouter(tags=["settings"])


@router.get("/settings", response_model=SettingsRead)
def read_settings(db: Session = Depends(get_db)):
    seed_settings(db)
    return get_settings_view(db)


@router.patch("/settings", response_model=SettingsRead)
def patch_settings(data: SettingsUpdate, db: Session = Depends(get_db)):
    seed_settings(db)
    return update_settings(db, data.model_dump(exclude_unset=True))


@router.post("/settings/telegram/test", response_model=TelegramTestResult)
def test_telegram(db: Session = Depends(get_db)):
    seed_settings(db)
    values = get_raw_settings(db)
    result = TelegramService().send_text(
        values["telegram_bot_token"], values["telegram_chat_id"],
        "Personal Manager đã kết nối Telegram thành công.",
    )
    return TelegramTestResult(
        success=result.success,
        message="Đã gửi tin nhắn thử thành công." if result.success else (result.error or "Không thể gửi tin nhắn thử."),
    )


@router.post("/settings/gemini/test", response_model=IntegrationTestResult)
def test_gemini(db: Session = Depends(get_db)):
    seed_settings(db)
    values = get_raw_settings(db)
    result = AIService().generate(
        values["gemini_api_key"], values["gemini_model"],
        "Trả lời đúng một câu ngắn xác nhận kết nối.", {"test": True},
    )
    return IntegrationTestResult(
        success=result.success,
        message="Đã kết nối Gemini thành công." if result.success else result.error,
    )

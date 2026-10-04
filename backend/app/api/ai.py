from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.repositories.settings import get_raw_settings, seed_settings
from app.schemas.ai import AIChatRequest, AIChatResponse
from app.services.ai_service import AIService
from app.services.context_builder import ContextBuilder

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/chat", response_model=AIChatResponse)
def chat(data: AIChatRequest, db: Session = Depends(get_db)):
    seed_settings(db)
    settings = get_raw_settings(db)
    if settings["gemini_enabled"] != "true":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Gemini chưa được bật trong Cài đặt.")
    context, domains = ContextBuilder(db).build(data.message)
    result = AIService().generate(settings["gemini_api_key"], settings["gemini_model"], data.message, context)
    if not result.success:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=result.error)
    return AIChatResponse(answer=result.text, context_domains=domains)

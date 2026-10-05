import hashlib
import re
from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database.database import get_db
from app.models.finance import Account, CategoryType, TransactionCategory, TransactionSource, TransactionType
from app.models.tasks import Task
from app.repositories.settings import get_raw_settings, seed_settings
from app.schemas.finance import TransactionCreate
from app.services.finance import create_transaction
from app.services.telegram_service import TelegramService

router = APIRouter(prefix="/telegram", tags=["telegram"])


def _secret(token: str) -> str:
    return hashlib.sha256(f"personal-manager:{token}".encode()).hexdigest()


def _parse_amount(text: str) -> Decimal | None:
    match = re.search(r"(\d+(?:[.,]\d+)?)\s*(triệu|tr|nghìn|ngàn|k)?", text.casefold())
    if not match:
        return None
    number = Decimal(match.group(1).replace(",", "."))
    unit = match.group(2)
    if unit in {"triệu", "tr"}: number *= Decimal("1000000")
    if unit in {"nghìn", "ngàn", "k"}: number *= Decimal("1000")
    return number


@router.post("/webhook/register")
def register_webhook(db: Session = Depends(get_db)):
    seed_settings(db); values = get_raw_settings(db); public_url = get_settings().public_base_url.rstrip("/")
    if not public_url:
        raise HTTPException(status_code=409, detail="PUBLIC_BASE_URL chưa được cấu hình.")
    result = TelegramService().set_webhook(values["telegram_bot_token"], f"{public_url}/api/telegram/webhook", _secret(values["telegram_bot_token"]))
    if not result.success:
        raise HTTPException(status_code=502, detail=result.error)
    return {"success": True, "message": "Đã bật tương tác Telegram."}


@router.post("/webhook")
def telegram_webhook(update: dict, x_telegram_bot_api_secret_token: str | None = Header(default=None), db: Session = Depends(get_db)):
    seed_settings(db); values = get_raw_settings(db); token = values["telegram_bot_token"]; chat_id = values["telegram_chat_id"]
    if not token or x_telegram_bot_api_secret_token != _secret(token):
        raise HTTPException(status_code=403, detail="Invalid Telegram webhook secret")
    telegram = TelegramService()
    callback = update.get("callback_query")
    if callback:
        source_chat = str(callback.get("message", {}).get("chat", {}).get("id", ""))
        if source_chat != chat_id:
            raise HTTPException(status_code=403, detail="Unknown Telegram chat")
        data = str(callback.get("data", ""))
        if data.startswith("task_done:"):
            task = db.get(Task, int(data.split(":", 1)[1])); message = "Không tìm thấy việc."
            if task: task.completed = True; db.commit(); message = f"Đã hoàn thành: {task.title}"
            telegram.answer_callback(token, callback["id"], message)
        elif data.startswith("expense_confirm:"):
            _, account_id, category_id, raw_amount = data.split(":")
            payload = TransactionCreate(account_id=int(account_id), category_id=int(category_id), type=TransactionType.EXPENSE, amount=Decimal(raw_amount), description="Ghi từ Telegram", transaction_date=date.today(), source=TransactionSource.AI)
            create_transaction(db, payload); telegram.answer_callback(token, callback["id"], "Đã ghi khoản chi.")
        return {"ok": True}
    message = update.get("message", {}); source_chat = str(message.get("chat", {}).get("id", "")); text = str(message.get("text", "")).strip()
    if source_chat != chat_id:
        raise HTTPException(status_code=403, detail="Unknown Telegram chat")
    if text.casefold() in {"/tasks", "việc", "việc cần làm"}:
        tasks = list(db.scalars(select(Task).where(Task.completed.is_(False)).order_by(Task.due_date.asc().nulls_last()).limit(10)).all())
        if not tasks: telegram.send_text(token, chat_id, "Bạn không còn việc nào chưa hoàn thành.")
        else:
            keyboard = [[{"text": f"✓ {task.title[:40]}", "callback_data": f"task_done:{task.id}"}] for task in tasks]
            telegram.send_text(token, chat_id, "Việc cần làm — nhấn để hoàn thành:", {"inline_keyboard": keyboard})
        return {"ok": True}
    amount = _parse_amount(text)
    if amount and any(word in text.casefold() for word in ("ăn", "chi", "mua", "trả")):
        account = db.scalar(select(Account).order_by(Account.id).limit(1))
        category_name = "Food" if "ăn" in text.casefold() else "Other"
        category = db.scalar(select(TransactionCategory).where(TransactionCategory.type == CategoryType.EXPENSE, TransactionCategory.name == category_name))
        if not account or not category: telegram.send_text(token, chat_id, "Chưa có tài khoản hoặc danh mục chi phù hợp trong Personal Manager.")
        else:
            keyboard = {"inline_keyboard": [[{"text": "Ghi khoản chi", "callback_data": f"expense_confirm:{account.id}:{category.id}:{amount}"}, {"text": "Hủy", "callback_data": "cancel"}]]}
            telegram.send_text(token, chat_id, f"Xác nhận ghi chi {amount:,.0f} ₫ từ tài khoản {account.name}?".replace(",", "."), keyboard)
        return {"ok": True}
    telegram.send_text(token, chat_id, "Bạn có thể gửi /tasks hoặc nhắn ví dụ: “Đã ăn mất 50 nghìn”.")
    return {"ok": True}

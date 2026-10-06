import hashlib
import re
from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.core.time import local_day_utc_bounds, utc_to_local
from app.database.database import get_db
from app.models.calendar import Schedule
from app.models.finance import Account, Transaction, TransactionCategory
from app.models.tasks import Task
from app.repositories.calendar import list_schedules
from app.repositories.settings import get_raw_settings, seed_settings
from app.services.ai_service import AIService, ProposedAction
from app.services.recurrence import expand_schedule_range
from app.services.schedule_occurrences import occurrence_completion, set_occurrence_completion
from app.services.telegram_actions import TelegramActionManager
from app.services.telegram_service import TelegramService

router = APIRouter(prefix="/telegram", tags=["telegram"])

COMMANDS = [
    {"command": "menu", "description": "Mở bảng điều khiển"},
    {"command": "calendar", "description": "Xem lịch hôm nay"},
    {"command": "fee", "description": "Ghi và xem thu chi"},
    {"command": "tasks", "description": "Xem việc cần làm"},
    {"command": "help", "description": "Xem cách sử dụng"},
]


def _secret(token: str) -> str:
    return hashlib.sha256(f"personal-manager:{token}".encode()).hexdigest()


def _parse_amount(text: str) -> Decimal | None:
    match = re.search(r"(\d+(?:[.,]\d+)?)\s*(triệu|tr|nghìn|ngàn|k)?", text.casefold())
    if not match:
        return None
    number = Decimal(match.group(1).replace(",", "."))
    unit = match.group(2)
    if unit in {"triệu", "tr"}:
        number *= Decimal("1000000")
    if unit in {"nghìn", "ngàn", "k"}:
        number *= Decimal("1000")
    return number


def _menu_markup() -> dict:
    return {"inline_keyboard": [
        [{"text": "📅 Lịch hôm nay", "callback_data": "menu:calendar"}, {"text": "💳 Thu chi", "callback_data": "menu:fee"}],
        [{"text": "✅ Việc cần làm", "callback_data": "menu:tasks"}, {"text": "✨ Trợ lý", "callback_data": "menu:help"}],
    ]}


def _confirmation_markup(draft_id: str) -> dict:
    return {"inline_keyboard": [[
        {"text": "✓ Xác nhận", "callback_data": f"draft_ok:{draft_id}"},
        {"text": "Hủy", "callback_data": f"draft_no:{draft_id}"},
    ]]}


def _send_menu(telegram: TelegramService, token: str, chat_id: str) -> None:
    telegram.send_text(
        token,
        chat_id,
        "Personal Manager\nChọn một mục hoặc gửi câu tự nhiên, ví dụ:\n"
        "• Mai 14:00 có workshop trong 2 giờ\n"
        "• Đã ăn trưa 50 nghìn\n"
        "• Cộng thêm 500k tiền thưởng",
        _menu_markup(),
    )


def _send_tasks(db: Session, telegram: TelegramService, token: str, chat_id: str) -> None:
    tasks = list(db.scalars(
        select(Task).where(Task.completed.is_(False)).order_by(Task.due_date.asc().nulls_last()).limit(10)
    ).all())
    if not tasks:
        telegram.send_text(token, chat_id, "Bạn không còn việc nào chưa hoàn thành.", _menu_markup())
        return
    keyboard = [[{"text": f"○ {task.title[:40]}", "callback_data": f"task_done:{task.id}"}] for task in tasks]
    keyboard.append([{"text": "‹ Menu", "callback_data": "menu:root"}])
    telegram.send_text(token, chat_id, "Việc cần làm — nhấn để hoàn thành:", {"inline_keyboard": keyboard})


def _send_calendar(db: Session, telegram: TelegramService, token: str, chat_id: str) -> None:
    today = datetime.now().astimezone().date()
    start, end = local_day_utc_bounds(today)
    schedules = list_schedules(db, start, end, None, None)
    occurrences = expand_schedule_range(schedules, start, end)
    if not occurrences:
        telegram.send_text(token, chat_id, "Hôm nay chưa có lịch trình.", _menu_markup())
        return
    lines = ["📅 Lịch hôm nay"]
    keyboard = []
    for occurrence in occurrences[:10]:
        local_start = utc_to_local(occurrence.start)
        local_end = utc_to_local(occurrence.end)
        completed = occurrence_completion(db, occurrence.schedule, occurrence.start)
        marker = "✓" if completed else "○"
        lines.append(f"{marker} {local_start:%H:%M}–{local_end:%H:%M}  {occurrence.schedule.title}")
        if not completed:
            key = occurrence.start.strftime("%Y%m%dT%H%M")
            keyboard.append([{"text": f"✓ {occurrence.schedule.title[:36]}", "callback_data": f"cal_done:{occurrence.schedule.id}:{key}"}])
    keyboard.append([{"text": "‹ Menu", "callback_data": "menu:root"}])
    telegram.send_text(token, chat_id, "\n".join(lines), {"inline_keyboard": keyboard})


def _send_finance(db: Session, telegram: TelegramService, token: str, chat_id: str) -> None:
    recent = list(db.scalars(select(Transaction).order_by(Transaction.id.desc()).limit(5)).all())
    lines = ["💳 Thu chi", "Gửi một câu như “Đã ăn mất 50 nghìn” hoặc “Cộng thêm 500k tiền thưởng”."]
    if recent:
        lines.append("\nGần đây:")
        for item in recent:
            sign = "+" if item.type == "INCOME" else "-"
            lines.append(f"{sign}{item.amount:,.0f} ₫  {item.description or item.type}".replace(",", "."))
    telegram.send_text(token, chat_id, "\n".join(lines), _menu_markup())


@router.post("/webhook/register")
def register_webhook(db: Session = Depends(get_db)):
    seed_settings(db)
    values = get_raw_settings(db)
    public_url = get_settings().public_base_url.rstrip("/")
    if not public_url:
        raise HTTPException(status_code=409, detail="PUBLIC_BASE_URL chưa được cấu hình.")
    telegram = TelegramService()
    result = telegram.set_webhook(
        values["telegram_bot_token"], f"{public_url}/api/telegram/webhook", _secret(values["telegram_bot_token"])
    )
    if not result.success:
        raise HTTPException(status_code=502, detail=result.error)
    telegram.set_commands(values["telegram_bot_token"], COMMANDS)
    return {"success": True, "message": "Đã bật tương tác Telegram và danh sách lệnh."}


@router.post("/webhook")
def telegram_webhook(
    update: dict,
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    seed_settings(db)
    values = get_raw_settings(db)
    token = values["telegram_bot_token"]
    chat_id = values["telegram_chat_id"]
    if not token or x_telegram_bot_api_secret_token != _secret(token):
        raise HTTPException(status_code=403, detail="Invalid Telegram webhook secret")
    telegram = TelegramService()

    callback = update.get("callback_query")
    if callback:
        source_chat = str(callback.get("message", {}).get("chat", {}).get("id", ""))
        if source_chat != chat_id:
            raise HTTPException(status_code=403, detail="Unknown Telegram chat")
        data = str(callback.get("data", ""))
        callback_id = str(callback.get("id", ""))
        if data.startswith("menu:"):
            target = data.split(":", 1)[1]
            telegram.answer_callback(token, callback_id, "Đang mở…")
            if target == "calendar":
                _send_calendar(db, telegram, token, chat_id)
            elif target == "fee":
                _send_finance(db, telegram, token, chat_id)
            elif target == "tasks":
                _send_tasks(db, telegram, token, chat_id)
            elif target == "help":
                telegram.send_text(token, chat_id, "Gửi câu tự nhiên; Gemini sẽ tạo bản nháp để bạn xác nhận trước khi lưu.", _menu_markup())
            else:
                _send_menu(telegram, token, chat_id)
        elif data.startswith("task_done:"):
            task = db.get(Task, int(data.split(":", 1)[1]))
            message = "Không tìm thấy việc."
            if task:
                task.completed = True
                db.commit()
                message = f"Đã hoàn thành: {task.title}"
            telegram.answer_callback(token, callback_id, message)
        elif data.startswith("cal_done:"):
            _, raw_id, raw_start = data.split(":", 2)
            schedule = db.get(Schedule, int(raw_id))
            message = "Không tìm thấy lịch trình."
            if schedule:
                occurrence_start = datetime.strptime(raw_start, "%Y%m%dT%H%M")
                set_occurrence_completion(db, schedule, occurrence_start, True)
                message = f"Đã hoàn thành: {schedule.title}"
            telegram.answer_callback(token, callback_id, message)
        elif data.startswith("draft_ok:"):
            message = TelegramActionManager(db).confirm(data.split(":", 1)[1])
            telegram.answer_callback(token, callback_id, message)
            telegram.send_text(token, chat_id, f"✓ {message}", _menu_markup())
        elif data.startswith("draft_no:"):
            message = TelegramActionManager(db).cancel(data.split(":", 1)[1])
            telegram.answer_callback(token, callback_id, message)
        return {"ok": True}

    message = update.get("message", {})
    source_chat = str(message.get("chat", {}).get("id", ""))
    text = str(message.get("text", "")).strip()
    if source_chat != chat_id:
        raise HTTPException(status_code=403, detail="Unknown Telegram chat")
    command = text.split(maxsplit=1)[0].casefold()
    if command in {"/start", "/menu"}:
        _send_menu(telegram, token, chat_id)
        return {"ok": True}
    if command == "/tasks":
        _send_tasks(db, telegram, token, chat_id)
        return {"ok": True}
    if command == "/calendar":
        _send_calendar(db, telegram, token, chat_id)
        return {"ok": True}
    if command == "/fee":
        _send_finance(db, telegram, token, chat_id)
        return {"ok": True}
    if command == "/help":
        telegram.send_text(token, chat_id, "Hãy gửi nội dung có số tiền hoặc thời gian rõ ràng. Mọi thay đổi đều cần bạn xác nhận.", _menu_markup())
        return {"ok": True}

    context = {
        "accounts": [item.name for item in db.scalars(select(Account).order_by(Account.id)).all()],
        "transaction_categories": [item.name for item in db.scalars(select(TransactionCategory).order_by(TransactionCategory.id)).all()],
    }
    result = AIService().interpret_actions(
        values["gemini_api_key"] if values["gemini_enabled"] == "true" else "",
        values["gemini_model"],
        text,
        datetime.now().astimezone(),
        context,
    )
    actions = list(result.actions)
    if not actions:
        amount = _parse_amount(text)
        if amount:
            folded = text.casefold()
            kind = "income" if any(word in folded for word in ("cộng", "nhận", "thu", "lương", "thưởng")) else "expense"
            actions = [ProposedAction(kind=kind, title=text[:200], amount=amount)]
    if not actions:
        telegram.send_text(token, chat_id, result.error or "Mình chưa hiểu yêu cầu. Hãy thử thêm số tiền hoặc thời gian.", _menu_markup())
        return {"ok": True}

    manager = TelegramActionManager(db)
    for action in actions:
        draft = manager.create_draft(action)
        telegram.send_text(token, chat_id, manager.preview(draft), _confirmation_markup(draft.id))
    return {"ok": True}

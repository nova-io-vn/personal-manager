from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.calendar import Schedule, ScheduleCategory
from app.models.finance import (
    Account,
    CategoryType,
    TransactionCategory,
    TransactionSource,
    TransactionType,
)
from app.models.tasks import Task
from app.models.telegram import TelegramActionDraft, TelegramDraftStatus
from app.schemas.finance import TransactionCreate
from app.services.ai_service import ProposedAction
from app.services.finance import create_transaction


EXPENSE_CATEGORY_ALIASES = {
    "ăn": "Food", "food": "Food", "đi lại": "Transport", "xe": "Transport",
    "mua": "Shopping", "shopping": "Shopping", "hóa đơn": "Bills", "bill": "Bills",
    "sức khỏe": "Health", "học": "Education", "giải trí": "Entertainment",
}
INCOME_CATEGORY_ALIASES = {
    "lương": "Salary", "thưởng": "Bonus", "freelance": "Freelance", "đầu tư": "Investment",
}


class TelegramActionManager:
    def __init__(self, db: Session):
        self.db = db

    def create_draft(self, action: ProposedAction) -> TelegramActionDraft:
        draft = TelegramActionDraft(action_type=action.kind, payload=action.model_dump(mode="json"))
        self.db.add(draft)
        self.db.commit()
        self.db.refresh(draft)
        return draft

    def preview(self, draft: TelegramActionDraft) -> str:
        action = ProposedAction.model_validate(draft.payload)
        if action.kind == "schedule":
            start = action.start_datetime.astimezone() if action.start_datetime else None
            end = action.end_datetime.astimezone() if action.end_datetime else None
            return (
                "📅 Xác nhận thêm lịch\n"
                f"• {action.title}\n"
                f"• {start:%d/%m/%Y %H:%M} – {end:%H:%M}"
                + (f"\n• {action.description}" if action.description else "")
            )
        if action.kind in {"expense", "income"}:
            label = "khoản chi" if action.kind == "expense" else "khoản thu"
            amount = f"{action.amount:,.0f}".replace(",", ".")
            return f"💳 Xác nhận {label}\n• {action.title}\n• {amount} ₫"
        return "✅ Xác nhận việc cần làm\n" + f"• {action.title}" + (f"\n• {action.description}" if action.description else "")

    def confirm(self, draft_id: str) -> str:
        draft = self.db.get(TelegramActionDraft, draft_id)
        if draft is None:
            return "Bản nháp không còn tồn tại."
        if draft.status != TelegramDraftStatus.PENDING:
            return "Bản nháp này đã được xử lý."
        now = datetime.now(timezone.utc)
        expires = draft.expires_at
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        if expires < now:
            draft.status = TelegramDraftStatus.EXPIRED
            draft.resolved_at = now
            self.db.commit()
            return "Bản nháp đã hết hạn. Hãy gửi lại yêu cầu."

        action = ProposedAction.model_validate(draft.payload)
        if action.kind == "schedule":
            category = self._schedule_category(action.category or action.title)
            self.db.add(Schedule(
                title=action.title,
                description=action.description,
                start_datetime=action.start_datetime,
                end_datetime=action.end_datetime,
                category_id=category.id if category else None,
                reminder_minutes=15,
            ))
            message = f"Đã thêm lịch: {action.title}"
        elif action.kind in {"expense", "income"}:
            transaction_type = TransactionType.EXPENSE if action.kind == "expense" else TransactionType.INCOME
            account = self.db.scalar(select(Account).order_by(Account.id).limit(1))
            category = self._transaction_category(transaction_type, action.category or action.title)
            if account is None or category is None:
                return "Chưa có tài khoản hoặc danh mục phù hợp để ghi giao dịch."
            create_transaction(self.db, TransactionCreate(
                account_id=account.id,
                category_id=category.id,
                type=transaction_type,
                amount=action.amount,
                description=action.description or action.title,
                transaction_date=now.astimezone().date(),
                source=TransactionSource.AI,
            ))
            label = "chi" if action.kind == "expense" else "thu"
            message = f"Đã ghi khoản {label}: {action.title}"
        else:
            self.db.add(Task(title=action.title, note=action.description))
            message = f"Đã thêm việc cần làm: {action.title}"

        draft.status = TelegramDraftStatus.CONFIRMED
        draft.resolved_at = now
        self.db.commit()
        return message

    def cancel(self, draft_id: str) -> str:
        draft = self.db.get(TelegramActionDraft, draft_id)
        if draft is None or draft.status != TelegramDraftStatus.PENDING:
            return "Bản nháp này đã được xử lý."
        draft.status = TelegramDraftStatus.CANCELLED
        draft.resolved_at = datetime.now(timezone.utc)
        self.db.commit()
        return "Đã hủy thao tác."

    def _schedule_category(self, hint: str) -> ScheduleCategory | None:
        categories = list(self.db.scalars(select(ScheduleCategory).order_by(ScheduleCategory.id)).all())
        folded = hint.casefold()
        return next((item for item in categories if item.name.casefold() in folded), categories[0] if categories else None)

    def _transaction_category(self, transaction_type: TransactionType, hint: str) -> TransactionCategory | None:
        category_type = CategoryType.EXPENSE if transaction_type == TransactionType.EXPENSE else CategoryType.INCOME
        categories = list(self.db.scalars(
            select(TransactionCategory).where(TransactionCategory.type == category_type).order_by(TransactionCategory.id)
        ).all())
        folded = hint.casefold()
        aliases = EXPENSE_CATEGORY_ALIASES if transaction_type == TransactionType.EXPENSE else INCOME_CATEGORY_ALIASES
        preferred = next((name for keyword, name in aliases.items() if keyword in folded), None)
        fallback = "Other" if transaction_type == TransactionType.EXPENSE else "Other Income"
        return next((item for item in categories if item.name == preferred), None) or next(
            (item for item in categories if item.name == fallback), categories[0] if categories else None
        )

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.finance import Account, Budget, CategoryType, Transaction, TransactionCategory, TransactionType


def get_account(db: Session, account_id: int) -> Account | None:
    return db.get(Account, account_id)


def get_category(db: Session, category_id: int) -> TransactionCategory | None:
    return db.get(TransactionCategory, category_id)


def list_transactions(
    db: Session, start_date: date | None, end_date: date | None, account_id: int | None,
    category_id: int | None, transaction_type: TransactionType | None,
) -> list[Transaction]:
    query = select(Transaction).order_by(Transaction.transaction_date.desc(), Transaction.id.desc())
    if start_date:
        query = query.where(Transaction.transaction_date >= start_date)
    if end_date:
        query = query.where(Transaction.transaction_date <= end_date)
    if account_id:
        query = query.where((Transaction.account_id == account_id) | (Transaction.related_account_id == account_id))
    if category_id:
        query = query.where(Transaction.category_id == category_id)
    if transaction_type:
        query = query.where(Transaction.type == transaction_type)
    return list(db.scalars(query).all())


def seed_categories(db: Session) -> None:
    if db.scalar(select(TransactionCategory.id).limit(1)) is not None:
        return
    names = [("Food", CategoryType.EXPENSE), ("Transport", CategoryType.EXPENSE), ("Shopping", CategoryType.EXPENSE),
             ("Entertainment", CategoryType.EXPENSE), ("Health", CategoryType.EXPENSE), ("Education", CategoryType.EXPENSE),
             ("Bills", CategoryType.EXPENSE), ("Other", CategoryType.EXPENSE), ("Salary", CategoryType.INCOME),
             ("Bonus", CategoryType.INCOME), ("Freelance", CategoryType.INCOME), ("Investment", CategoryType.INCOME),
             ("Other Income", CategoryType.INCOME)]
    db.add_all(TransactionCategory(name=name, type=category_type) for name, category_type in names)
    db.commit()


def list_budgets(db: Session) -> list[Budget]:
    return list(db.scalars(select(Budget).order_by(Budget.start_date.desc(), Budget.id.desc())).all())

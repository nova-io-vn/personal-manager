from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.finance import Account, CategoryType, Transaction, TransactionCategory, TransactionType
from app.repositories.finance import get_account, get_category


class NotFoundError(Exception):
    pass


class ConflictError(Exception):
    pass


def _signed_effect(transaction_type: TransactionType, amount: Decimal) -> Decimal:
    return amount if transaction_type == TransactionType.INCOME else -amount


def _validate_category(db: Session, category_id: int | None, transaction_type: TransactionType) -> TransactionCategory | None:
    if transaction_type == TransactionType.TRANSFER:
        if category_id is not None:
            raise ValueError("transfers cannot have a category")
        return None
    if category_id is None:
        raise ValueError("income and expense transactions require a category")
    category = get_category(db, category_id)
    if category is None:
        raise NotFoundError("Transaction category not found")
    expected = CategoryType.INCOME if transaction_type == TransactionType.INCOME else CategoryType.EXPENSE
    if category.type != expected:
        raise ValueError(f"category type must be {expected.value}")
    return category


def _validate_accounts(db: Session, account_id: int, related_account_id: int | None, transaction_type: TransactionType) -> tuple[Account, Account | None]:
    account = get_account(db, account_id)
    if account is None:
        raise NotFoundError("Account not found")
    if transaction_type != TransactionType.TRANSFER:
        if related_account_id is not None:
            raise ValueError("related_account_id is only valid for transfers")
        return account, None
    if related_account_id is None or related_account_id == account_id:
        raise ValueError("transfers require two different accounts")
    related = get_account(db, related_account_id)
    if related is None:
        raise NotFoundError("Related account not found")
    return account, related


def _apply_effect(transaction: Transaction, delta: Decimal) -> None:
    transaction.account.current_balance += delta
    if transaction.type == TransactionType.TRANSFER and transaction.related_account:
        transaction.related_account.current_balance -= delta


def create_transaction(db: Session, data) -> Transaction:
    account, related = _validate_accounts(db, data.account_id, data.related_account_id, data.type)
    _validate_category(db, data.category_id, data.type)
    transaction = Transaction(**data.model_dump())
    transaction.account = account
    transaction.related_account = related
    db.add(transaction)
    delta = _signed_effect(data.type, data.amount)
    _apply_effect(transaction, delta)
    db.commit()
    db.refresh(transaction)
    return transaction


def update_transaction(db: Session, transaction: Transaction, data) -> Transaction:
    old_delta = _signed_effect(transaction.type, transaction.amount)
    _apply_effect(transaction, -old_delta)
    values = data.model_dump(exclude_unset=True)
    for key, value in values.items():
        setattr(transaction, key, value)
    account_id = transaction.account_id
    related_id = transaction.related_account_id
    account, related = _validate_accounts(db, account_id, related_id, transaction.type)
    _validate_category(db, transaction.category_id, transaction.type)
    transaction.account = account
    transaction.related_account = related
    _apply_effect(transaction, _signed_effect(transaction.type, transaction.amount))
    db.commit()
    db.refresh(transaction)
    return transaction


def delete_transaction(db: Session, transaction: Transaction) -> None:
    _apply_effect(transaction, -_signed_effect(transaction.type, transaction.amount))
    db.delete(transaction)
    db.commit()


def delete_account(db: Session, account: Account) -> None:
    if account.transactions:
        raise ConflictError("Cannot delete an account with transactions")
    db.delete(account)
    db.commit()

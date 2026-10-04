from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.finance import Account, Budget, CategoryType, Transaction, TransactionCategory, TransactionType
from app.repositories.finance import list_budgets, list_transactions
from app.schemas.finance import (
    AccountCreate, AccountRead, AccountUpdate, BudgetCreate, BudgetRead, BudgetUpdate,
    CategoryRead, TransactionCreate, TransactionRead, TransactionUpdate,
)
from app.services.finance import ConflictError, NotFoundError, create_transaction, delete_account, delete_transaction, update_transaction

router = APIRouter(tags=["finance"])


def not_found(message: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)


@router.get("/accounts", response_model=list[AccountRead])
def get_accounts(db: Session = Depends(get_db)):
    return list(db.scalars(select(Account).order_by(Account.name)).all())


@router.post("/accounts", response_model=AccountRead, status_code=status.HTTP_201_CREATED)
def create_account(data: AccountCreate, db: Session = Depends(get_db)):
    account = Account(**data.model_dump(), current_balance=data.initial_balance)
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


@router.get("/accounts/{account_id}", response_model=AccountRead)
def get_account(account_id: int, db: Session = Depends(get_db)):
    account = db.get(Account, account_id)
    if not account:
        raise not_found("Account not found")
    return account


@router.patch("/accounts/{account_id}", response_model=AccountRead)
def update_account(account_id: int, data: AccountUpdate, db: Session = Depends(get_db)):
    account = db.get(Account, account_id)
    if not account:
        raise not_found("Account not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(account, key, value)
    db.commit()
    db.refresh(account)
    return account


@router.delete("/accounts/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_account(account_id: int, db: Session = Depends(get_db)):
    account = db.get(Account, account_id)
    if not account:
        raise not_found("Account not found")
    try:
        delete_account(db, account)
    except ConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/transaction-categories", response_model=list[CategoryRead])
def get_categories(db: Session = Depends(get_db)):
    return list(db.scalars(select(TransactionCategory).order_by(TransactionCategory.type, TransactionCategory.name)).all())


@router.get("/transactions", response_model=list[TransactionRead])
def get_transactions(
    start_date: date | None = None, end_date: date | None = None, account_id: int | None = None,
    category_id: int | None = None, type: TransactionType | None = None, db: Session = Depends(get_db),
):
    if start_date and end_date and end_date < start_date:
        raise HTTPException(status_code=422, detail="end_date must be on or after start_date")
    return list_transactions(db, start_date, end_date, account_id, category_id, type)


@router.post("/transactions", response_model=TransactionRead, status_code=status.HTTP_201_CREATED)
def add_transaction(data: TransactionCreate, db: Session = Depends(get_db)):
    try:
        return create_transaction(db, data)
    except NotFoundError as exc:
        raise not_found(str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/transactions/{transaction_id}", response_model=TransactionRead)
def get_transaction(transaction_id: int, db: Session = Depends(get_db)):
    transaction = db.get(Transaction, transaction_id)
    if not transaction:
        raise not_found("Transaction not found")
    return transaction


@router.patch("/transactions/{transaction_id}", response_model=TransactionRead)
def edit_transaction(transaction_id: int, data: TransactionUpdate, db: Session = Depends(get_db)):
    transaction = db.get(Transaction, transaction_id)
    if not transaction:
        raise not_found("Transaction not found")
    try:
        return update_transaction(db, transaction, data)
    except NotFoundError as exc:
        raise not_found(str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete("/transactions/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_transaction(transaction_id: int, db: Session = Depends(get_db)):
    transaction = db.get(Transaction, transaction_id)
    if not transaction:
        raise not_found("Transaction not found")
    delete_transaction(db, transaction)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _validate_budget_category(db: Session, category_id: int):
    category = db.get(TransactionCategory, category_id)
    if not category:
        raise not_found("Transaction category not found")
    if category.type != CategoryType.EXPENSE:
        raise HTTPException(status_code=400, detail="Budgets must use expense categories")


@router.get("/budgets", response_model=list[BudgetRead])
def get_budgets(db: Session = Depends(get_db)):
    return list_budgets(db)


@router.post("/budgets", response_model=BudgetRead, status_code=status.HTTP_201_CREATED)
def add_budget(data: BudgetCreate, db: Session = Depends(get_db)):
    _validate_budget_category(db, data.category_id)
    budget = Budget(**data.model_dump())
    db.add(budget)
    db.commit()
    db.refresh(budget)
    return budget


@router.patch("/budgets/{budget_id}", response_model=BudgetRead)
def edit_budget(budget_id: int, data: BudgetUpdate, db: Session = Depends(get_db)):
    budget = db.get(Budget, budget_id)
    if not budget:
        raise not_found("Budget not found")
    values = data.model_dump(exclude_unset=True)
    if "category_id" in values:
        _validate_budget_category(db, values["category_id"])
    start = values.get("start_date", budget.start_date)
    end = values.get("end_date", budget.end_date)
    if end < start:
        raise HTTPException(status_code=422, detail="end_date must be on or after start_date")
    for key, value in values.items():
        setattr(budget, key, value)
    db.commit()
    db.refresh(budget)
    return budget


@router.delete("/budgets/{budget_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_budget(budget_id: int, db: Session = Depends(get_db)):
    budget = db.get(Budget, budget_id)
    if not budget:
        raise not_found("Budget not found")
    db.delete(budget)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.debt import Debt
from app.schemas.debt import DebtCreate, DebtRead, DebtUpdate

router = APIRouter(tags=["debts"])


def _validate_paid(amount, paid_amount):
    if paid_amount > amount:
        raise HTTPException(status_code=422, detail="paid_amount cannot exceed amount")


@router.get("/debts", response_model=list[DebtRead])
def list_debts(db: Session = Depends(get_db)):
    return list(db.scalars(select(Debt).order_by(Debt.due_date.asc().nulls_last(), Debt.created_at.desc())).all())


@router.post("/debts", response_model=DebtRead, status_code=201)
def create_debt(data: DebtCreate, db: Session = Depends(get_db)):
    _validate_paid(data.amount, data.paid_amount)
    debt = Debt(**data.model_dump())
    db.add(debt)
    db.commit()
    db.refresh(debt)
    return debt


@router.patch("/debts/{debt_id}", response_model=DebtRead)
def update_debt(debt_id: int, data: DebtUpdate, db: Session = Depends(get_db)):
    debt = db.get(Debt, debt_id)
    if debt is None:
        raise HTTPException(status_code=404, detail="Debt not found")
    values = data.model_dump(exclude_unset=True)
    amount = values.get("amount", debt.amount)
    paid_amount = values.get("paid_amount", debt.paid_amount)
    _validate_paid(amount, paid_amount)
    for key, value in values.items():
        setattr(debt, key, value)
    db.commit()
    db.refresh(debt)
    return debt


@router.delete("/debts/{debt_id}", status_code=204)
def delete_debt(debt_id: int, db: Session = Depends(get_db)):
    debt = db.get(Debt, debt_id)
    if debt is None:
        raise HTTPException(status_code=404, detail="Debt not found")
    db.delete(debt)
    db.commit()
    return Response(status_code=204)

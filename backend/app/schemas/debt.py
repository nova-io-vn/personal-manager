from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.debt import DebtDirection


class DebtCreate(BaseModel):
    person: str = Field(min_length=1, max_length=120)
    direction: DebtDirection
    amount: Decimal = Field(gt=0, max_digits=18, decimal_places=2)
    paid_amount: Decimal = Field(default=Decimal("0.00"), ge=0, max_digits=18, decimal_places=2)
    due_date: date | None = None
    note: str | None = Field(default=None, max_length=10000)

    @field_validator("paid_amount")
    @classmethod
    def paid_cannot_exceed_amount(cls, value: Decimal, info):
        amount = info.data.get("amount")
        if amount is not None and value > amount:
            raise ValueError("paid_amount cannot exceed amount")
        return value


class DebtUpdate(BaseModel):
    person: str | None = Field(default=None, min_length=1, max_length=120)
    direction: DebtDirection | None = None
    amount: Decimal | None = Field(default=None, gt=0, max_digits=18, decimal_places=2)
    paid_amount: Decimal | None = Field(default=None, ge=0, max_digits=18, decimal_places=2)
    due_date: date | None = None
    note: str | None = Field(default=None, max_length=10000)


class DebtRead(DebtCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
    updated_at: datetime

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.finance import AccountType, CategoryType, TransactionSource, TransactionType


class AccountCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    type: AccountType
    initial_balance: Decimal = Decimal("0.00")

    @field_validator("initial_balance")
    @classmethod
    def balance_is_finite(cls, value: Decimal) -> Decimal:
        if not value.is_finite():
            raise ValueError("initial_balance must be finite")
        return value


class AccountUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    type: AccountType | None = None


class AccountRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    type: AccountType
    initial_balance: Decimal
    current_balance: Decimal
    created_at: datetime
    updated_at: datetime


class CategoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    type: CategoryType
    icon: str | None
    color: str | None
    created_at: datetime


class TransactionCreate(BaseModel):
    account_id: int
    category_id: int | None = None
    related_account_id: int | None = None
    type: TransactionType
    amount: Decimal = Field(gt=0)
    description: str | None = Field(default=None, max_length=1000)
    transaction_date: date
    source: TransactionSource = TransactionSource.MANUAL

    @model_validator(mode="after")
    def validate_transfer(self):
        if self.type == TransactionType.TRANSFER:
            if self.related_account_id is None or self.related_account_id == self.account_id:
                raise ValueError("transfers require two different accounts")
            if self.category_id is not None:
                raise ValueError("transfers cannot have a category")
        elif self.related_account_id is not None:
            raise ValueError("related_account_id is only valid for transfers")
        return self


class TransactionUpdate(BaseModel):
    account_id: int | None = None
    category_id: int | None = None
    related_account_id: int | None = None
    type: TransactionType | None = None
    amount: Decimal | None = Field(default=None, gt=0)
    description: str | None = Field(default=None, max_length=1000)
    transaction_date: date | None = None
    source: TransactionSource | None = None


class TransactionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    account_id: int
    category_id: int | None
    related_account_id: int | None
    type: TransactionType
    amount: Decimal
    description: str | None
    transaction_date: date
    source: TransactionSource
    created_at: datetime
    updated_at: datetime


class BudgetCreate(BaseModel):
    category_id: int
    amount: Decimal = Field(gt=0)
    period: str = Field(default="monthly", min_length=1, max_length=30)
    start_date: date
    end_date: date

    @model_validator(mode="after")
    def valid_dates(self):
        if self.end_date < self.start_date:
            raise ValueError("end_date must be on or after start_date")
        return self


class BudgetUpdate(BaseModel):
    category_id: int | None = None
    amount: Decimal | None = Field(default=None, gt=0)
    period: str | None = Field(default=None, min_length=1, max_length=30)
    start_date: date | None = None
    end_date: date | None = None


class BudgetRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    category_id: int
    amount: Decimal
    period: str
    start_date: date
    end_date: date
    created_at: datetime
    updated_at: datetime

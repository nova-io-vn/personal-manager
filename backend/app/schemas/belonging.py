from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class PersonalItemCreate(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    category: str = Field(min_length=1, max_length=80)
    condition: str = Field(default="GOOD", min_length=1, max_length=40)
    purchase_date: date | None = None
    purchase_price: Decimal | None = Field(default=None, ge=0, max_digits=18, decimal_places=2)
    warranty_until: date | None = None
    note: str | None = Field(default=None, max_length=10000)

    @field_validator("name", "category", "condition")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("value cannot be empty")
        return value


class PersonalItemUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=160)
    category: str | None = Field(default=None, min_length=1, max_length=80)
    condition: str | None = Field(default=None, min_length=1, max_length=40)
    purchase_date: date | None = None
    purchase_price: Decimal | None = Field(default=None, ge=0, max_digits=18, decimal_places=2)
    warranty_until: date | None = None
    note: str | None = Field(default=None, max_length=10000)

    @field_validator("name", "category", "condition")
    @classmethod
    def strip_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return value
        value = value.strip()
        if not value:
            raise ValueError("value cannot be empty")
        return value


class PersonalItemRead(PersonalItemCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
    updated_at: datetime

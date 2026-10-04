from datetime import date, datetime, timezone
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class AccountType(StrEnum):
    CASH = "CASH"
    BANK = "BANK"
    EWALLET = "EWALLET"


class CategoryType(StrEnum):
    INCOME = "INCOME"
    EXPENSE = "EXPENSE"


class TransactionType(StrEnum):
    INCOME = "INCOME"
    EXPENSE = "EXPENSE"
    TRANSFER = "TRANSFER"


class TransactionSource(StrEnum):
    MANUAL = "MANUAL"
    BANK_IMPORT = "BANK_IMPORT"
    AI = "AI"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    type: Mapped[AccountType] = mapped_column(String(20))
    initial_balance: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal("0.00"))
    current_balance: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal("0.00"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    transactions: Mapped[list["Transaction"]] = relationship(
        foreign_keys="Transaction.account_id", back_populates="account"
    )


class TransactionCategory(Base):
    __tablename__ = "transaction_categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    type: Mapped[CategoryType] = mapped_column(String(20))
    icon: Mapped[str | None] = mapped_column(String(50), nullable=True)
    color: Mapped[str | None] = mapped_column(String(20), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    transactions: Mapped[list["Transaction"]] = relationship(back_populates="category")


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), index=True)
    category_id: Mapped[int | None] = mapped_column(ForeignKey("transaction_categories.id"), nullable=True)
    related_account_id: Mapped[int | None] = mapped_column(ForeignKey("accounts.id"), nullable=True)
    type: Mapped[TransactionType] = mapped_column(String(20), index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    transaction_date: Mapped[date] = mapped_column(Date, index=True)
    source: Mapped[TransactionSource] = mapped_column(String(30), default=TransactionSource.MANUAL)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    account: Mapped[Account] = relationship(foreign_keys=[account_id], back_populates="transactions")
    related_account: Mapped[Account | None] = relationship(foreign_keys=[related_account_id])
    category: Mapped[TransactionCategory | None] = relationship(back_populates="transactions")


class Budget(Base):
    __tablename__ = "budgets"

    id: Mapped[int] = mapped_column(primary_key=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("transaction_categories.id"))
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    period: Mapped[str] = mapped_column(String(30), default="monthly")
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    category: Mapped[TransactionCategory] = relationship()

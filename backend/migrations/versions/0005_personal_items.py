"""Add personal belongings inventory."""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0005_personal_items"
down_revision: Union[str, None] = "0004_cloud_auth_sync"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if "personal_items" in set(inspector.get_table_names()):
        return
    op.create_table(
        "personal_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("category", sa.String(length=80), nullable=False),
        sa.Column("condition", sa.String(length=40), nullable=False),
        sa.Column("purchase_date", sa.Date(), nullable=True),
        sa.Column("purchase_price", sa.Numeric(precision=18, scale=2), nullable=True),
        sa.Column("warranty_until", sa.Date(), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_personal_items_name", "personal_items", ["name"])
    op.create_index("ix_personal_items_category", "personal_items", ["category"])
    op.execute(sa.text("UPDATE settings SET value = 'gemini-3.5-flash' WHERE key = 'gemini_model' AND value = 'gemini-2.5-flash'"))


def downgrade() -> None:
    op.drop_index("ix_personal_items_category", table_name="personal_items")
    op.drop_index("ix_personal_items_name", table_name="personal_items")
    op.drop_table("personal_items")

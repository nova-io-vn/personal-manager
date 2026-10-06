"""Add confirmable Telegram action drafts."""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0006_telegram_action_drafts"
down_revision: Union[str, None] = "0005_personal_items"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if "telegram_action_drafts" in set(inspector.get_table_names()):
        return
    op.create_table(
        "telegram_action_drafts",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("action_type", sa.String(length=30), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_telegram_action_drafts_action_type", "telegram_action_drafts", ["action_type"])
    op.create_index("ix_telegram_action_drafts_status", "telegram_action_drafts", ["status"])
    op.create_index("ix_telegram_action_drafts_expires_at", "telegram_action_drafts", ["expires_at"])


def downgrade() -> None:
    op.drop_index("ix_telegram_action_drafts_expires_at", table_name="telegram_action_drafts")
    op.drop_index("ix_telegram_action_drafts_status", table_name="telegram_action_drafts")
    op.drop_index("ix_telegram_action_drafts_action_type", table_name="telegram_action_drafts")
    op.drop_table("telegram_action_drafts")

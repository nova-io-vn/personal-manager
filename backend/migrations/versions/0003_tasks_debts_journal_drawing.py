"""Add unplanned tasks, debt tracking and journal drawings."""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0003_tasks_debts_journal_drawing"
down_revision: Union[str, None] = "0002_schedule_occurrence_states"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    tables = set(inspector.get_table_names())
    if "tasks" not in tables:
        op.create_table(
            "tasks",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("title", sa.String(length=200), nullable=False),
            sa.Column("note", sa.Text(), nullable=True),
            sa.Column("due_date", sa.Date(), nullable=True),
            sa.Column("completed", sa.Boolean(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
    if "debts" not in tables:
        op.create_table(
            "debts",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("person", sa.String(length=120), nullable=False),
            sa.Column("direction", sa.String(length=20), nullable=False),
            sa.Column("amount", sa.Numeric(precision=18, scale=2), nullable=False),
            sa.Column("paid_amount", sa.Numeric(precision=18, scale=2), nullable=False),
            sa.Column("due_date", sa.Date(), nullable=True),
            sa.Column("note", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
    if "ix_tasks_due_date" not in {item["name"] for item in inspector.get_indexes("tasks")}:
        op.create_index("ix_tasks_due_date", "tasks", ["due_date"])
    if "ix_tasks_completed" not in {item["name"] for item in inspector.get_indexes("tasks")}:
        op.create_index("ix_tasks_completed", "tasks", ["completed"])
    if "ix_debts_direction" not in {item["name"] for item in inspector.get_indexes("debts")}:
        op.create_index("ix_debts_direction", "debts", ["direction"])
    if "ix_debts_due_date" not in {item["name"] for item in inspector.get_indexes("debts")}:
        op.create_index("ix_debts_due_date", "debts", ["due_date"])
    if "drawing_data" not in {item["name"] for item in inspector.get_columns("journal_entries")}:
        op.add_column("journal_entries", sa.Column("drawing_data", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("journal_entries", "drawing_data")
    op.drop_index("ix_debts_due_date", table_name="debts")
    op.drop_index("ix_debts_direction", table_name="debts")
    op.drop_table("debts")
    op.drop_index("ix_tasks_completed", table_name="tasks")
    op.drop_index("ix_tasks_due_date", table_name="tasks")
    op.drop_table("tasks")

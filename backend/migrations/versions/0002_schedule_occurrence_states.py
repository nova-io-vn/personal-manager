"""Persist completion independently for each virtual recurring schedule occurrence.

Revision ID: 0002_schedule_occurrence_states
Revises: 0001_initial
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0002_schedule_occurrence_states"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "schedule_occurrence_states",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("schedule_id", sa.Integer(), nullable=False),
        sa.Column("occurrence_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed", sa.Boolean(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["schedule_id"], ["schedules.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("schedule_id", "occurrence_start", name="uq_schedule_occurrence_start"),
    )
    op.create_index(op.f("ix_schedule_occurrence_states_schedule_id"), "schedule_occurrence_states", ["schedule_id"])
    op.create_index(op.f("ix_schedule_occurrence_states_occurrence_start"), "schedule_occurrence_states", ["occurrence_start"])


def downgrade() -> None:
    op.drop_index(op.f("ix_schedule_occurrence_states_occurrence_start"), table_name="schedule_occurrence_states")
    op.drop_index(op.f("ix_schedule_occurrence_states_schedule_id"), table_name="schedule_occurrence_states")
    op.drop_table("schedule_occurrence_states")

"""Add cloud authentication, devices, and sync change log."""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0004_cloud_auth_sync"
down_revision: Union[str, None] = "0003_tasks_debts_journal_drawing"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    tables = set(inspector.get_table_names())
    if "cloud_users" not in tables:
        op.create_table(
            "cloud_users",
            sa.Column("id", sa.String(length=36), nullable=False),
            sa.Column("email", sa.String(length=320), nullable=False),
            sa.Column("password_hash", sa.Text(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("email"),
        )
        op.create_index("ix_cloud_users_email", "cloud_users", ["email"], unique=False)
    if "cloud_devices" not in tables:
        op.create_table(
            "cloud_devices",
            sa.Column("id", sa.String(length=36), nullable=False),
            sa.Column("user_id", sa.String(length=36), nullable=False),
            sa.Column("device_key", sa.String(length=120), nullable=False),
            sa.Column("name", sa.String(length=120), nullable=False),
            sa.Column("platform", sa.String(length=30), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["user_id"], ["cloud_users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("user_id", "device_key", name="uq_cloud_device_user_key"),
        )
        op.create_index("ix_cloud_devices_user_id", "cloud_devices", ["user_id"], unique=False)
    if "sync_changes" not in tables:
        op.create_table(
            "sync_changes",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("user_id", sa.String(length=36), nullable=False),
            sa.Column("device_id", sa.String(length=36), nullable=False),
            sa.Column("entity_type", sa.String(length=80), nullable=False),
            sa.Column("entity_id", sa.String(length=120), nullable=False),
            sa.Column("operation", sa.String(length=20), nullable=False),
            sa.Column("payload", sa.JSON(), nullable=False),
            sa.Column("idempotency_key", sa.String(length=180), nullable=False),
            sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["device_id"], ["cloud_devices.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["user_id"], ["cloud_users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("user_id", "idempotency_key", name="uq_sync_change_idempotency"),
        )
        for name, columns in (
            ("ix_sync_changes_user_id", ["user_id"]),
            ("ix_sync_changes_device_id", ["device_id"]),
            ("ix_sync_changes_entity_type", ["entity_type"]),
            ("ix_sync_changes_entity_id", ["entity_id"]),
        ):
            op.create_index(name, "sync_changes", columns, unique=False)


def downgrade() -> None:
    op.drop_table("sync_changes")
    op.drop_table("cloud_devices")
    op.drop_table("cloud_users")

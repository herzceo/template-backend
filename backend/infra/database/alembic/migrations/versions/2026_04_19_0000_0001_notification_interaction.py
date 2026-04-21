"""notification_interaction

Revision ID: 0001_notification_interaction
Revises:
Create Date: 2026-04-19 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0001_notification_interaction"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "notification_interaction",
        sa.Column("notification_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("dismissed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reaction", sa.String(length=20), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["notification_id"], ["notification.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("notification_id", "user_id"),
    )
    op.create_index(
        "ix_notification_interaction_dismissed_at",
        "notification_interaction",
        ["dismissed_at"],
    )
    op.create_index(
        "ix_notification_interaction_user_dismissed",
        "notification_interaction",
        ["user_id", "dismissed_at"],
    )
    op.execute("DROP TABLE IF EXISTS notification_read")


def downgrade() -> None:
    """Downgrade schema."""
    op.create_table(
        "notification_read",
        sa.Column("notification_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["notification_id"], ["notification.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("notification_id", "user_id"),
    )
    op.drop_index(
        "ix_notification_interaction_user_dismissed",
        table_name="notification_interaction",
    )
    op.drop_index(
        "ix_notification_interaction_dismissed_at",
        table_name="notification_interaction",
    )
    op.drop_table("notification_interaction")

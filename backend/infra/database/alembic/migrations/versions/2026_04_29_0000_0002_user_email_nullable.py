"""user_email_nullable

Revision ID: 0002_user_email_nullable
Revises: 0001_notification_interaction
Create Date: 2026-04-29 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0002_user_email_nullable"
down_revision: str | None = "0001_notification_interaction"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column("user", "email", existing_type=sa.String(255), nullable=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column("user", "email", existing_type=sa.String(255), nullable=False)

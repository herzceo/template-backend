from __future__ import annotations

from datetime import datetime

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import UUID as SQL_UUID
from sqlalchemy.types import DateTime, String
from uuid_utils.compat import UUID

from .base import Base, WithTime


class NotificationInteraction(WithTime, Base):
    notification_id: Mapped[UUID] = mapped_column(
        SQL_UUID(as_uuid=True),
        ForeignKey("notification.id"),
        primary_key=True,
    )
    user_id: Mapped[UUID] = mapped_column(
        SQL_UUID(as_uuid=True),
        ForeignKey("user.id"),
        primary_key=True,
    )
    read_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    dismissed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )
    reaction: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

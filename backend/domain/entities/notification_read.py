from __future__ import annotations

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import UUID as SQL_UUID
from uuid_utils.compat import UUID

from .base import Base, WithTime


class NotificationRead(WithTime, Base):
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

from __future__ import annotations

from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import UUID as SQL_UUID
from sqlalchemy.types import Integer, String
from uuid_utils.compat import UUID

from .base import Base, WithTenant, WithTime, WithUUIDID


class Notification(WithUUIDID, WithTime, WithTenant, Base):
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    audience: Mapped[str] = mapped_column(String(20), nullable=False)
    urgency: Mapped[int] = mapped_column(Integer, nullable=False, default=20)
    target_id: Mapped[UUID | None] = mapped_column(SQL_UUID(as_uuid=True), nullable=True)
    sender_id: Mapped[UUID | None] = mapped_column(
        SQL_UUID(as_uuid=True),
        ForeignKey("user.id"),
        nullable=True,
    )

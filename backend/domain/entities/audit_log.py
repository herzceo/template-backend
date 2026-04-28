from __future__ import annotations

from typing import Any

from sqlalchemy import ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON, String
from sqlalchemy.types import UUID as SQL_UUID
from uuid_utils.compat import UUID

from .base import Base, WithTenant, WithTime, WithUUIDID


class AuditLog(WithUUIDID, WithTime, WithTenant, Base):
    __table_args__ = (Index(None, "resource_type", "resource_id"),)

    actor_id: Mapped[UUID | None] = mapped_column(
        SQL_UUID(as_uuid=True),
        ForeignKey("user.id"),
        index=True,
        nullable=True,
    )
    action: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    resource_type: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    resource_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    changes: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    ip: Mapped[str | None] = mapped_column(String(45), nullable=True)

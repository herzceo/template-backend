from __future__ import annotations

from typing import Any

from sqlalchemy import Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON, String
from sqlalchemy.types import UUID as SQL_UUID
from uuid_utils.compat import UUID

from .base import Base, WithActive, WithTime, WithUUIDID


class Tenant(WithUUIDID, WithActive, WithTime, Base):
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    app_id: Mapped[str | None] = mapped_column(String(64), unique=True, index=True, nullable=True)
    settings: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    is_default: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false", nullable=False
    )
    owner_id: Mapped[UUID | None] = mapped_column(
        SQL_UUID(as_uuid=True),
        ForeignKey("user.id", use_alter=True),
        nullable=True,
    )

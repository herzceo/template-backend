from __future__ import annotations

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import String

from .base import Base, WithTime, WithUUIDID


class Permission(WithUUIDID, WithTime, Base):
    codename: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)

from __future__ import annotations

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import String

from .base import Base, WithActive, WithTime, WithUUIDID


class User(WithUUIDID, WithActive, WithTime, Base):
    login: Mapped[str] = mapped_column(String, index=True, unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

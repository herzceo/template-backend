from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import String

from .base import Base, WithActive, WithTenant, WithTime, WithUUIDID
from .rbac import user_role

if TYPE_CHECKING:
    from .role import Role


class User(WithUUIDID, WithActive, WithTime, WithTenant, Base):
    login: Mapped[str] = mapped_column(String, index=True, unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(String(512), nullable=True)

    roles: Mapped[list[Role]] = relationship(secondary=user_role, backref="users", lazy="raise")

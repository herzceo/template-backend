from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import String

from .base import Base, WithActive, WithTenant, WithTime, WithUUIDID
from .rbac import user_role

if TYPE_CHECKING:
    from .role import Role


class User(WithUUIDID, WithActive, WithTime, WithTenant, Base):
    username: Mapped[str] = mapped_column(String, index=True, unique=True, nullable=False)
    # OAuth signups get an auto-generated username and must confirm one
    # (chooseUsername); email/password signups pick it up front, so default True.
    username_confirmed: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )
    email: Mapped[str | None] = mapped_column(String(255), unique=True, index=True, nullable=True)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    roles: Mapped[list[Role]] = relationship(secondary=user_role, backref="users", lazy="raise")

    @property
    def is_verified(self) -> bool:
        return self.verified_at is not None

    @property
    def needs_username(self) -> bool:
        """The account still carries an auto-generated username to be chosen."""
        return not self.username_confirmed

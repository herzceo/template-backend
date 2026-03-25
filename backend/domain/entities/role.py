from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import String

from .base import Base, WithActive, WithTenant, WithTime, WithUUIDID
from .rbac import role_permission

if TYPE_CHECKING:
    from .permission import Permission


class Role(WithUUIDID, WithActive, WithTime, WithTenant, Base):
    __table_args__ = (UniqueConstraint("tenant_id", "name"),)

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)

    permissions: Mapped[list[Permission]] = relationship(
        secondary=role_permission, backref="roles", lazy="raise"
    )

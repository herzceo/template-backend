from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import UUID as SQL_UUID
from sqlalchemy.types import String
from uuid_utils.compat import UUID

from .base import Base, WithTime, WithUUIDID

if TYPE_CHECKING:
    from .user import User


class Profile(WithUUIDID, WithTime, Base):
    user_id: Mapped[UUID] = mapped_column(
        SQL_UUID(as_uuid=True),
        ForeignKey("user.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(512), nullable=True)

    user: Mapped[User] = relationship(backref="profile", lazy="raise")

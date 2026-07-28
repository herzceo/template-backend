from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import UUID as SQL_UUID
from sqlalchemy.types import String
from uuid_utils.compat import UUID

from .base import Base, WithTime, WithUUIDID

if TYPE_CHECKING:
    from .user import User


class UserEmail(WithUUIDID, WithTime, Base):
    """Conjoint index of every email known for a user.

    One row per distinct email a user owns — their account primary plus each
    OAuth provider's reported email. ``normalized_email`` carries a global unique
    index, making it the single authority that keeps the set of primary emails
    and the set of provider identity emails unique across all accounts together.
    """

    user_id: Mapped[UUID] = mapped_column(
        SQL_UUID(as_uuid=True),
        ForeignKey("user.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    normalized_email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    is_primary: Mapped[bool] = mapped_column(nullable=False, default=False)
    provider: Mapped[str | None] = mapped_column(String(32), nullable=True)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped[User] = relationship(backref="emails", lazy="raise")

    @property
    def is_verified(self) -> bool:
        return self.verified_at is not None

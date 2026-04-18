from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import UUID as SQL_UUID
from sqlalchemy.types import String
from uuid_utils.compat import UUID

from .base import Base, WithTime, WithUUIDID

if TYPE_CHECKING:
    from .user import User


class Identity(WithUUIDID, WithTime, Base):
    __table_args__ = (
        UniqueConstraint("provider", "provider_subject_id", name="uq_identity_provider_subject"),
    )

    user_id: Mapped[UUID] = mapped_column(
        SQL_UUID(as_uuid=True),
        ForeignKey("user.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    provider: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    provider_subject_id: Mapped[str] = mapped_column(String(255), nullable=False)

    credential_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)

    access_token_enc: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    refresh_token_enc: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    token_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    scopes: Mapped[str | None] = mapped_column(String(512), nullable=True)

    provider_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    provider_display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    provider_avatar_url: Mapped[str | None] = mapped_column(String(512), nullable=True)

    user: Mapped[User] = relationship(backref="identities", lazy="raise")

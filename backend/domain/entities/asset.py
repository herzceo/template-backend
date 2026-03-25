from __future__ import annotations

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import UUID as SQL_UUID
from sqlalchemy.types import BigInteger, String
from uuid_utils.compat import UUID

from .base import Base, WithTenant, WithTime, WithUUIDID


class Asset(WithUUIDID, WithTime, WithTenant, Base):
    key: Mapped[str] = mapped_column(String(1024), nullable=False)
    content_type: Mapped[str] = mapped_column(String(255), nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    blurhash: Mapped[str | None] = mapped_column(String(100), nullable=True)
    original_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    uploader_id: Mapped[UUID] = mapped_column(
        SQL_UUID(as_uuid=True),
        ForeignKey("user.id"),
        index=True,
        nullable=False,
    )

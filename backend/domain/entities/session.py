from __future__ import annotations

from datetime import datetime

from sqlalchemy import ARRAY, DateTime, Float, ForeignKey, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import UUID as SQL_UUID
from uuid_utils.compat import UUID

from backend.domain.enums import DeviceType, IpType

from .base import Base, WithTime, WithUUIDID


class Session(WithUUIDID, WithTime, Base):
    user_id: Mapped[UUID] = mapped_column(
        SQL_UUID(as_uuid=True),
        ForeignKey("user.id"),
        index=True,
        nullable=False,
    )
    token_hash: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    ip: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(512), nullable=True)
    country_code: Mapped[str | None] = mapped_column(String(2), nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_active_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    asn_org: Mapped[str | None] = mapped_column(String(128), nullable=True)
    ip_type: Mapped[IpType | None] = mapped_column(String(32), nullable=True)
    device_type: Mapped[DeviceType | None] = mapped_column(String(32), nullable=True)
    os_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    browser_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    timezone: Mapped[str | None] = mapped_column(String(64), nullable=True)
    screen_width: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    pixel_ratio: Mapped[float | None] = mapped_column(Float, nullable=True)
    webgl_vendor: Mapped[str | None] = mapped_column(String(128), nullable=True)
    webgl_renderer: Mapped[str | None] = mapped_column(String(256), nullable=True)
    hardware_concurrency: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    device_memory: Mapped[float | None] = mapped_column(Float, nullable=True)
    languages: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)

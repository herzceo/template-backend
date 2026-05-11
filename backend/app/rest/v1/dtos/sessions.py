from datetime import datetime
from uuid import UUID

from backend.internal.dto import StructDTO


class Session(StructDTO):
    id: UUID
    user_id: UUID
    ip: str | None
    user_agent: str | None
    country_code: str | None
    expires_at: datetime
    created_at: datetime
    last_active_at: datetime | None
    asn_org: str | None
    ip_type: str | None
    device_type: str | None
    os_name: str | None
    browser_name: str | None
    timezone: str | None
    screen_width: int | None
    pixel_ratio: float | None
    webgl_vendor: str | None
    webgl_renderer: str | None
    hardware_concurrency: int | None
    device_memory: float | None
    languages: list[str] | None


__all__ = ("Session",)

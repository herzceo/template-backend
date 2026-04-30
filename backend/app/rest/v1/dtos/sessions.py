from datetime import datetime
from uuid import UUID

from backend.internal.dto import StructDTO


class Session(StructDTO):
    id: UUID
    user_id: UUID
    ip: str | None
    user_agent: str | None
    fingerprint: str | None
    country_code: str | None
    expires_at: datetime
    created_at: datetime

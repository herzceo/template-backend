from datetime import datetime
from uuid import UUID

from backend.internal.dto import StructDTO


class User(StructDTO):
    id: UUID
    username: str
    email: str | None
    first_name: str
    last_name: str
    avatar_url: str | None
    active: bool
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime

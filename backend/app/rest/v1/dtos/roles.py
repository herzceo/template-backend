from datetime import datetime
from uuid import UUID

from backend.internal.dto import StructDTO


class Role(StructDTO):
    id: UUID
    name: str
    description: str | None
    active: bool
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime

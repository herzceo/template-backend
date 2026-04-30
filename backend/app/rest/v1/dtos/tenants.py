from datetime import datetime
from typing import Any
from uuid import UUID

from backend.internal.dto import StructDTO


class Tenant(StructDTO):
    id: UUID
    name: str
    slug: str
    settings: dict[str, Any] | None
    is_default: bool
    owner_id: UUID | None
    active: bool
    created_at: datetime
    updated_at: datetime

from typing import Any

from backend.internal.dto import StructDTO


class Tenant(StructDTO):
    id: str
    name: str
    slug: str
    settings: dict[str, Any] | None
    owner_id: str | None
    active: bool
    created_at: str
    updated_at: str

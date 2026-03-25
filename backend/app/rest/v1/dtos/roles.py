from backend.internal.dto import StructDTO


class Role(StructDTO):
    id: str
    name: str
    description: str | None
    active: bool
    tenant_id: str
    created_at: str
    updated_at: str

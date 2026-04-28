from backend.internal.dto import StructDTO


class User(StructDTO):
    id: str
    username: str
    email: str | None
    first_name: str
    last_name: str
    avatar_url: str | None
    active: bool
    tenant_id: str
    created_at: str
    updated_at: str

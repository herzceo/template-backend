from backend.internal.dto import StructDTO


class Session(StructDTO):
    id: str
    user_id: str
    ip: str | None
    user_agent: str | None
    fingerprint: str | None
    country_code: str | None
    expires_at: str
    created_at: str

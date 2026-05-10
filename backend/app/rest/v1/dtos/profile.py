from datetime import datetime
from uuid import UUID

from backend.internal.dto import StructDTO


class Profile(StructDTO):
    id: UUID
    user_id: UUID
    display_name: str | None
    avatar_url: str | None
    created_at: datetime
    updated_at: datetime

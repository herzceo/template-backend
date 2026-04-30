from datetime import datetime
from uuid import UUID

from backend.internal.dto import StructDTO


class Asset(StructDTO):
    id: UUID
    key: str
    content_type: str
    size_bytes: int
    blurhash: str | None
    original_filename: str | None
    uploader_id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime

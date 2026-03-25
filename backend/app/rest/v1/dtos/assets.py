from backend.internal.dto import StructDTO


class Asset(StructDTO):
    id: str
    key: str
    content_type: str
    size_bytes: int
    blurhash: str | None
    original_filename: str | None
    uploader_id: str
    tenant_id: str
    created_at: str
    updated_at: str

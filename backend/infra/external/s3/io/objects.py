from __future__ import annotations

from backend.internal.dto import StructDTO


class UploadResult(StructDTO):
    key: str
    bucket: str
    etag: str = ""
    version_id: str | None = None


class PresignedUrlResult(StructDTO):
    url: str
    key: str
    expires_in: int


class CopyResult(StructDTO):
    source_key: str
    destination_key: str
    bucket: str
    etag: str = ""


class ObjectMeta(StructDTO):
    key: str
    size: int = 0
    content_type: str = ""
    last_modified: str = ""
    etag: str = ""

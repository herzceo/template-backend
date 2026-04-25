from __future__ import annotations

from backend.internal.dto import StructDTO


class S3Config(StructDTO):
    S3_ACCESS_KEY_ID: str
    S3_SECRET_ACCESS_KEY: str
    S3_REGION: str = "us-east-1"
    S3_ENDPOINT_URL: str | None = None
    S3_BUCKET: str = ""
    S3_PRESIGNED_URL_EXPIRY: int = 3600

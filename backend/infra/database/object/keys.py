from datetime import UTC, datetime
from uuid import UUID

from uuid_utils import uuid7


def temp_upload_key(user_id: UUID, original_filename: str) -> str:
    today = datetime.now(UTC).strftime("%Y-%m-%d")
    return f"temp/uploads/{today}/{user_id}/{uuid7()}/{original_filename}"


def permanent_asset_key(tenant_id: UUID, original_filename: str) -> str:
    return f"assets/{tenant_id}/{uuid7()}/{original_filename}"

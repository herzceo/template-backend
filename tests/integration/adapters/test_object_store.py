from __future__ import annotations

import io
from typing import TYPE_CHECKING
from uuid import uuid4

import httpx
import pytest
from PIL import Image

from backend.app.errors import NotFoundError, ValidationFailedError
from backend.infra.database.object import S3ObjectStore
from backend.infra.external.s3.config import S3Config

if TYPE_CHECKING:
    from backend.infra.external.s3.client import S3Client


def _make_jpeg() -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (8, 8), color=(100, 150, 200)).save(buf, format="JPEG")
    return buf.getvalue()


async def test_request_upload_returns_presigned_url(object_store: S3ObjectStore) -> None:
    user_id = uuid4()
    result = await object_store.request_upload(user_id=user_id, original_filename="photo.jpg")
    assert result.key.startswith("temp/uploads/")
    assert str(user_id) in result.key
    assert result.url.startswith("http://")
    assert result.expires_in > 0


async def test_confirm_upload_happy_path(
    object_store: S3ObjectStore,
) -> None:
    user_id = uuid4()
    tenant_id = uuid4()

    pending = await object_store.request_upload(user_id=user_id, original_filename="file.txt")
    async with httpx.AsyncClient() as http:
        r = await http.put(pending.url, content=b"hello world")
    assert r.status_code in (200, 204)

    confirmed = await object_store.confirm_upload(
        pending_key=pending.key,
        user_id=user_id,
        tenant_id=tenant_id,
        original_filename="file.txt",
    )

    assert confirmed.key.startswith("assets/")
    assert confirmed.size == len(b"hello world")
    assert confirmed.blurhash is None


async def test_confirm_upload_deletes_temp_file(
    object_store: S3ObjectStore,
    s3_client: S3Client,
) -> None:
    user_id = uuid4()
    tenant_id = uuid4()

    pending = await object_store.request_upload(user_id=user_id, original_filename="file.txt")
    async with httpx.AsyncClient() as http:
        await http.put(pending.url, content=b"data")

    await object_store.confirm_upload(
        pending_key=pending.key,
        user_id=user_id,
        tenant_id=tenant_id,
        original_filename="file.txt",
    )

    assert not await s3_client.exists(pending.key)


async def test_confirm_upload_computes_blurhash_for_image(
    object_store: S3ObjectStore,
) -> None:
    user_id = uuid4()
    tenant_id = uuid4()
    jpeg = _make_jpeg()

    pending = await object_store.request_upload(user_id=user_id, original_filename="photo.jpg")
    async with httpx.AsyncClient() as http:
        await http.put(pending.url, content=jpeg)

    confirmed = await object_store.confirm_upload(
        pending_key=pending.key,
        user_id=user_id,
        tenant_id=tenant_id,
        original_filename="photo.jpg",
    )

    assert confirmed.blurhash is not None


async def test_confirm_upload_raises_when_not_found(object_store: S3ObjectStore) -> None:
    user_id = uuid4()
    key = f"temp/uploads/2024-01-01/{user_id}/missing.txt"
    with pytest.raises(NotFoundError):
        await object_store.confirm_upload(
            pending_key=key,
            user_id=user_id,
            tenant_id=uuid4(),
            original_filename="missing.txt",
        )


@pytest.mark.parametrize("filename", ["", "../etc/passwd", "foo/bar", "foo\0bar"])
async def test_confirm_upload_rejects_invalid_filename(
    object_store: S3ObjectStore,
    filename: str,
) -> None:
    user_id = uuid4()
    key = f"temp/uploads/2024-01-01/{user_id}/placeholder.txt"
    with pytest.raises(ValidationFailedError):
        await object_store.confirm_upload(
            pending_key=key,
            user_id=user_id,
            tenant_id=uuid4(),
            original_filename=filename,
        )


async def test_confirm_upload_rejects_mismatched_user(object_store: S3ObjectStore) -> None:
    user_id = uuid4()
    other_user_id = uuid4()
    key = f"temp/uploads/2024-01-01/{other_user_id}/file.txt"
    with pytest.raises(ValidationFailedError):
        await object_store.confirm_upload(
            pending_key=key,
            user_id=user_id,
            tenant_id=uuid4(),
            original_filename="file.txt",
        )


async def test_confirm_upload_rejects_oversized_file(
    object_store: S3ObjectStore,
    s3_client: S3Client,
    s3_config: S3Config,
) -> None:
    user_id = uuid4()
    tenant_id = uuid4()
    content = b"hello"

    pending = await object_store.request_upload(user_id=user_id, original_filename="file.txt")
    async with httpx.AsyncClient() as http:
        await http.put(pending.url, content=content)

    tiny_config = S3Config(
        S3_ACCESS_KEY_ID=s3_config.S3_ACCESS_KEY_ID,
        S3_SECRET_ACCESS_KEY=s3_config.S3_SECRET_ACCESS_KEY,
        S3_ENDPOINT_URL=s3_config.S3_ENDPOINT_URL,
        S3_BUCKET=s3_config.S3_BUCKET,
        S3_UPLOAD_MAX_SIZE_BYTES=3,
    )
    tiny_store = S3ObjectStore(client=s3_client, config=tiny_config)

    with pytest.raises(ValidationFailedError):
        await tiny_store.confirm_upload(
            pending_key=pending.key,
            user_id=user_id,
            tenant_id=tenant_id,
            original_filename="file.txt",
        )

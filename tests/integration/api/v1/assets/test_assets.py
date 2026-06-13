from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING, Any
from uuid import uuid4

if TYPE_CHECKING:
    from litestar.testing import AsyncTestClient

    from backend.domain.entities.user import User


async def test_presign_asset_requires_auth(client: AsyncTestClient[Any]) -> None:
    r = await client.post("/v1/assets/presign", json={"original_filename": "photo.jpg"})
    assert r.status_code == HTTPStatus.UNAUTHORIZED


async def test_presign_asset_returns_upload_url(
    client: AsyncTestClient[Any],
    auth_user: User,
) -> None:
    r = await client.post("/v1/assets/presign", json={"original_filename": "photo.jpg"})
    assert r.status_code == HTTPStatus.CREATED
    data = r.json()["data"]
    assert "url" in data
    assert "key" in data
    assert data["url"].startswith("https://mock-s3/upload/")


async def test_create_asset_requires_auth(client: AsyncTestClient[Any]) -> None:
    r = await client.post(
        "/v1/assets/",
        json={
            "temp_key": "tmp/test/key",
            "content_type": "image/jpeg",
            "original_filename": "photo.jpg",
        },
    )
    assert r.status_code == HTTPStatus.UNAUTHORIZED


async def test_create_asset_confirms_upload(
    client: AsyncTestClient[Any],
    auth_user: User,
) -> None:
    presign_r = await client.post("/v1/assets/presign", json={"original_filename": "photo.jpg"})
    assert presign_r.status_code == HTTPStatus.CREATED
    temp_key = presign_r.json()["data"]["key"]

    r = await client.post(
        "/v1/assets/",
        json={
            "temp_key": temp_key,
            "content_type": "image/jpeg",
            "original_filename": "photo.jpg",
        },
    )
    assert r.status_code == HTTPStatus.CREATED
    data = r.json()["data"]
    assert "id" in data
    assert data["content_type"] == "image/jpeg"


async def test_list_assets(
    client: AsyncTestClient[Any],
    auth_user: User,
) -> None:
    r = await client.get("/v1/assets/")
    assert r.status_code == HTTPStatus.OK
    assert "items" in r.json()["data"]


async def test_get_asset_not_found(
    client: AsyncTestClient[Any],
    auth_user: User,
) -> None:
    r = await client.get(f"/v1/assets/{uuid4()}")
    assert r.status_code == HTTPStatus.NOT_FOUND

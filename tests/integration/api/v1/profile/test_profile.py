from http import HTTPStatus
from typing import Any
from uuid import uuid4

from litestar.testing import AsyncTestClient

from backend.domain.entities.user import User


async def test_get_profile_requires_auth(
    client: AsyncTestClient[Any],
    user: User,
) -> None:
    r = await client.get(f"/v1/users/{user.id}/profile/")
    assert r.status_code == HTTPStatus.UNAUTHORIZED


async def test_get_profile_returns_profile(
    client: AsyncTestClient[Any],
    auth_user: User,
    user: User,
) -> None:
    r = await client.get(f"/v1/users/{user.id}/profile/")
    assert r.status_code == HTTPStatus.OK
    data = r.json()
    assert data["data"]["user_id"] == str(user.id)
    assert data["data"]["display_name"] is None
    assert data["data"]["avatar_url"] is None


async def test_get_profile_not_found(
    client: AsyncTestClient[Any],
    auth_user: User,
) -> None:
    r = await client.get(f"/v1/users/{uuid4()}/profile/")
    assert r.status_code == HTTPStatus.NOT_FOUND


async def test_update_profile_display_name(
    client: AsyncTestClient[Any],
    auth_user: User,
    user: User,
) -> None:
    r = await client.patch(
        f"/v1/users/{user.id}/profile/",
        json={"display_name": "Alice Smith"},
    )
    assert r.status_code == HTTPStatus.OK
    data = r.json()
    assert data["data"]["display_name"] == "Alice Smith"
    assert data["data"]["user_id"] == str(user.id)


async def test_update_profile_avatar_url(
    client: AsyncTestClient[Any],
    auth_user: User,
    user: User,
) -> None:
    r = await client.patch(
        f"/v1/users/{user.id}/profile/",
        json={"avatar_url": "https://example.com/avatar.png"},
    )
    assert r.status_code == HTTPStatus.OK
    data = r.json()
    assert data["data"]["avatar_url"] == "https://example.com/avatar.png"

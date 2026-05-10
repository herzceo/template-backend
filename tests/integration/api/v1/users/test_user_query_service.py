from http import HTTPStatus
from typing import Any

from litestar.testing import AsyncTestClient

from backend.domain.entities.user import User


async def test_list_users_with_roles_requires_auth(
    client: AsyncTestClient[Any],
) -> None:
    r = await client.get("/v1/users/with-roles")
    assert r.status_code == HTTPStatus.UNAUTHORIZED


async def test_list_users_with_roles(
    client: AsyncTestClient[Any],
    auth_user: User,
) -> None:
    r = await client.get("/v1/users/with-roles")
    assert r.status_code == HTTPStatus.OK
    data = r.json()["data"]
    assert "items" in data
    assert "total" in data
    for item in data["items"]:
        assert "roles" in item

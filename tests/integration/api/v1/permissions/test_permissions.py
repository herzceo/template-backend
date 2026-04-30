from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING, Any
from uuid import uuid4

from tests.integration.api.factories.role import create_permission

if TYPE_CHECKING:
    from dishka import AsyncContainer
    from litestar.testing import AsyncTestClient

    from backend.domain.entities.user import User


async def test_list_permissions_requires_auth(client: AsyncTestClient[Any]) -> None:
    r = await client.get("/v1/permissions/")
    assert r.status_code == HTTPStatus.UNAUTHORIZED


async def test_list_permissions(
    client: AsyncTestClient[Any],
    auth_user: User,
    container: AsyncContainer,
) -> None:
    await create_permission(container)
    r = await client.get("/v1/permissions/")
    assert r.status_code == HTTPStatus.OK
    assert "items" in r.json()["data"]


async def test_create_permission(
    client: AsyncTestClient[Any],
    auth_user: User,
) -> None:
    r = await client.post(
        "/v1/permissions/",
        json={"codename": f"perm:{uuid4().hex[:8]}", "description": "Test"},
    )
    assert r.status_code == HTTPStatus.CREATED
    assert r.json()["data"]["codename"] is not None


async def test_create_permission_requires_auth(client: AsyncTestClient[Any]) -> None:
    r = await client.post(
        "/v1/permissions/",
        json={"codename": f"perm:{uuid4().hex[:8]}"},
    )
    assert r.status_code == HTTPStatus.UNAUTHORIZED


async def test_get_permission(
    client: AsyncTestClient[Any],
    auth_user: User,
    container: AsyncContainer,
) -> None:
    perm = await create_permission(container)
    r = await client.get(f"/v1/permissions/{perm.id}")
    assert r.status_code == HTTPStatus.OK
    assert r.json()["data"]["id"] == str(perm.id)


async def test_get_permission_not_found(
    client: AsyncTestClient[Any],
    auth_user: User,
) -> None:
    r = await client.get(f"/v1/permissions/{uuid4()}")
    assert r.status_code == HTTPStatus.NOT_FOUND


async def test_delete_permission(
    client: AsyncTestClient[Any],
    auth_user: User,
    container: AsyncContainer,
) -> None:
    perm = await create_permission(container)
    r = await client.delete(f"/v1/permissions/{perm.id}")
    assert r.status_code == HTTPStatus.NO_CONTENT

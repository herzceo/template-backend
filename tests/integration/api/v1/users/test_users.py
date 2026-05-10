from http import HTTPStatus
from typing import Any
from uuid import uuid4

from dishka import AsyncContainer
from litestar.testing import AsyncTestClient

from backend.domain.entities.tenant import Tenant
from backend.domain.entities.user import User
from tests.integration.api.factories.user import create_user, unique_email, unique_username


async def test_list_users_requires_auth(
    client: AsyncTestClient[Any],
) -> None:
    r = await client.get("/v1/users/")
    assert r.status_code == HTTPStatus.UNAUTHORIZED


async def test_list_users_returns_paginated_result(
    client: AsyncTestClient[Any],
    auth_user: User,
) -> None:
    r = await client.get("/v1/users/")
    assert r.status_code == HTTPStatus.OK
    data = r.json()
    assert "data" in data
    assert "items" in data["data"]


async def test_create_user(
    client: AsyncTestClient[Any],
    auth_user: User,
    tenant: Tenant,
) -> None:
    r = await client.post(
        "/v1/users/",
        json={
            "username": unique_username(),
            "email": unique_email(),
            "password": "Test123!",
            "tenant_id": str(tenant.id),
        },
    )
    assert r.status_code == HTTPStatus.CREATED
    data = r.json()
    assert "id" in data["data"]


async def test_get_user(
    client: AsyncTestClient[Any],
    auth_user: User,
    user: User,
) -> None:
    r = await client.get(f"/v1/users/{user.id}")
    assert r.status_code == HTTPStatus.OK
    data = r.json()
    assert data["data"]["id"] == str(user.id)


async def test_get_user_not_found(
    client: AsyncTestClient[Any],
    auth_user: User,
) -> None:
    r = await client.get(f"/v1/users/{uuid4()}")
    assert r.status_code == HTTPStatus.NOT_FOUND


async def test_update_user(
    client: AsyncTestClient[Any],
    auth_user: User,
    user: User,
) -> None:
    new_email = unique_email("updated")
    r = await client.patch(
        f"/v1/users/{user.id}",
        json={"email": new_email},
    )
    assert r.status_code == HTTPStatus.OK


async def test_delete_user(
    client: AsyncTestClient[Any],
    auth_user: User,
    container: AsyncContainer,
    tenant: Tenant,
) -> None:
    target = await create_user(container, tenant.id)
    r = await client.delete(f"/v1/users/{target.id}")
    assert r.status_code == HTTPStatus.NO_CONTENT

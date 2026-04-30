from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING, Any
from uuid import uuid4

from tests.integration.api.factories.tenant import create_tenant

if TYPE_CHECKING:
    from dishka import AsyncContainer
    from litestar.testing import AsyncTestClient

    from backend.domain.entities.tenant import Tenant
    from backend.domain.entities.user import User


async def test_list_tenants_requires_auth(client: AsyncTestClient[Any]) -> None:
    r = await client.get("/v1/tenants/")
    assert r.status_code == HTTPStatus.UNAUTHORIZED


async def test_list_tenants(
    client: AsyncTestClient[Any],
    auth_user: User,
) -> None:
    r = await client.get("/v1/tenants/")
    assert r.status_code == HTTPStatus.OK
    assert "items" in r.json()["data"]


async def test_create_tenant(
    client: AsyncTestClient[Any],
    auth_user: User,
) -> None:
    slug = f"tenant-{uuid4().hex[:8]}"
    r = await client.post("/v1/tenants/", json={"name": "New Tenant", "slug": slug})
    assert r.status_code == HTTPStatus.CREATED
    assert r.json()["data"]["slug"] == slug


async def test_create_tenant_requires_auth(client: AsyncTestClient[Any]) -> None:
    r = await client.post(
        "/v1/tenants/",
        json={"name": "New Tenant", "slug": f"t-{uuid4().hex[:8]}"},
    )
    assert r.status_code == HTTPStatus.UNAUTHORIZED


async def test_get_tenant(
    client: AsyncTestClient[Any],
    auth_user: User,
    tenant: Tenant,
) -> None:
    r = await client.get(f"/v1/tenants/{tenant.id}")
    assert r.status_code == HTTPStatus.OK
    assert r.json()["data"]["id"] == str(tenant.id)


async def test_get_tenant_not_found(
    client: AsyncTestClient[Any],
    auth_user: User,
) -> None:
    r = await client.get(f"/v1/tenants/{uuid4()}")
    assert r.status_code == HTTPStatus.NOT_FOUND


async def test_update_tenant(
    client: AsyncTestClient[Any],
    auth_user: User,
    tenant: Tenant,
) -> None:
    r = await client.patch(f"/v1/tenants/{tenant.id}", json={"name": "Updated Name"})
    assert r.status_code == HTTPStatus.OK
    assert r.json()["data"]["name"] == "Updated Name"


async def test_delete_tenant(
    client: AsyncTestClient[Any],
    auth_user: User,
    container: AsyncContainer,
) -> None:
    extra = await create_tenant(container, name="Extra Tenant", slug=f"extra-{uuid4().hex[:8]}")
    r = await client.delete(f"/v1/tenants/{extra.id}")
    assert r.status_code == HTTPStatus.NO_CONTENT

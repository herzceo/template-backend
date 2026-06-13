from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING, Any
from uuid import uuid4

from tests.integration.api.factories.role import create_permission, create_role

if TYPE_CHECKING:
    from dishka import AsyncContainer
    from litestar.testing import AsyncTestClient

    from backend.domain.entities.tenant import Tenant
    from backend.domain.entities.user import User


async def test_list_roles_requires_auth(client: AsyncTestClient[Any]) -> None:
    r = await client.get("/v1/roles/")
    assert r.status_code == HTTPStatus.UNAUTHORIZED


async def test_list_roles(
    client: AsyncTestClient[Any],
    auth_user: User,
    container: AsyncContainer,
    tenant: Tenant,
) -> None:
    await create_role(container, tenant.id)
    r = await client.get("/v1/roles/")
    assert r.status_code == HTTPStatus.OK
    data = r.json()
    assert "items" in data["data"]


async def test_create_role(
    client: AsyncTestClient[Any],
    auth_user: User,
    tenant: Tenant,
) -> None:
    r = await client.post(
        "/v1/roles/",
        json={"name": f"role_{uuid4().hex[:8]}", "tenant_id": str(tenant.id)},
    )
    assert r.status_code == HTTPStatus.CREATED
    data = r.json()
    assert data["data"]["name"] is not None


async def test_create_role_requires_auth(
    client: AsyncTestClient[Any],
    tenant: Tenant,
) -> None:
    r = await client.post(
        "/v1/roles/",
        json={"name": f"role_{uuid4().hex[:8]}", "tenant_id": str(tenant.id)},
    )
    assert r.status_code == HTTPStatus.UNAUTHORIZED


async def test_get_role(
    client: AsyncTestClient[Any],
    auth_user: User,
    container: AsyncContainer,
    tenant: Tenant,
) -> None:
    role = await create_role(container, tenant.id)
    r = await client.get(f"/v1/roles/{role.id}")
    assert r.status_code == HTTPStatus.OK
    assert r.json()["data"]["id"] == str(role.id)


async def test_get_role_not_found(
    client: AsyncTestClient[Any],
    auth_user: User,
) -> None:
    r = await client.get(f"/v1/roles/{uuid4()}")
    assert r.status_code == HTTPStatus.NOT_FOUND


async def test_delete_role(
    client: AsyncTestClient[Any],
    auth_user: User,
    container: AsyncContainer,
    tenant: Tenant,
) -> None:
    role = await create_role(container, tenant.id)
    r = await client.delete(f"/v1/roles/{role.id}")
    assert r.status_code == HTTPStatus.NO_CONTENT


async def test_assign_and_revoke_permission(
    client: AsyncTestClient[Any],
    auth_user: User,
    container: AsyncContainer,
    tenant: Tenant,
) -> None:
    role = await create_role(container, tenant.id)
    permission = await create_permission(container)

    r = await client.post(
        "/v1/roles/assignPermission",
        json={"role_id": str(role.id), "permission_id": str(permission.id)},
    )
    assert r.status_code == HTTPStatus.CREATED

    r = await client.post(
        "/v1/roles/revokePermission",
        json={"role_id": str(role.id), "permission_id": str(permission.id)},
    )
    assert r.status_code == HTTPStatus.CREATED

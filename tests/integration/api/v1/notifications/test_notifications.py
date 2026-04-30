from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING, Any
from uuid import uuid4

from tests.integration.api.factories.notification import create_notification

if TYPE_CHECKING:
    from dishka import AsyncContainer
    from litestar.testing import AsyncTestClient

    from backend.domain.entities.tenant import Tenant
    from backend.domain.entities.user import User


async def test_list_notifications_requires_auth(client: AsyncTestClient[Any]) -> None:
    r = await client.get("/v1/notifications/")
    assert r.status_code == HTTPStatus.UNAUTHORIZED


async def test_list_notifications(
    client: AsyncTestClient[Any],
    auth_user: User,
    container: AsyncContainer,
    tenant: Tenant,
) -> None:
    await create_notification(container, tenant.id)
    r = await client.get("/v1/notifications/")
    assert r.status_code == HTTPStatus.OK
    assert "items" in r.json()["data"]


async def test_create_notification(
    client: AsyncTestClient[Any],
    auth_user: User,
    tenant: Tenant,
) -> None:
    r = await client.post(
        "/v1/notifications/",
        json={
            "title": "Hello",
            "body": "World",
            "audience": "all",
            "tenant_id": str(tenant.id),
        },
    )
    assert r.status_code == HTTPStatus.CREATED
    assert r.json()["data"]["title"] == "Hello"


async def test_create_notification_requires_auth(
    client: AsyncTestClient[Any],
    tenant: Tenant,
) -> None:
    r = await client.post(
        "/v1/notifications/",
        json={"title": "Hi", "body": "There", "audience": "all", "tenant_id": str(tenant.id)},
    )
    assert r.status_code == HTTPStatus.UNAUTHORIZED


async def test_get_notification(
    client: AsyncTestClient[Any],
    auth_user: User,
    container: AsyncContainer,
    tenant: Tenant,
) -> None:
    notif = await create_notification(container, tenant.id)
    r = await client.get(f"/v1/notifications/{notif.id}")
    assert r.status_code == HTTPStatus.OK
    assert r.json()["data"]["id"] == str(notif.id)


async def test_get_notification_not_found(
    client: AsyncTestClient[Any],
    auth_user: User,
) -> None:
    r = await client.get(f"/v1/notifications/{uuid4()}")
    assert r.status_code == HTTPStatus.NOT_FOUND


async def test_delete_notification(
    client: AsyncTestClient[Any],
    auth_user: User,
    container: AsyncContainer,
    tenant: Tenant,
) -> None:
    notif = await create_notification(container, tenant.id)
    r = await client.delete(f"/v1/notifications/{notif.id}")
    assert r.status_code == HTTPStatus.NO_CONTENT

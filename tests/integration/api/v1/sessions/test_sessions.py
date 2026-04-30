from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING, Any

from tests.integration.api.factories.user import create_logged_user, unique_email

if TYPE_CHECKING:
    from dishka import AsyncContainer
    from litestar.testing import AsyncTestClient

    from backend.domain.entities.tenant import Tenant
    from backend.domain.entities.user import User


async def test_list_sessions_requires_auth(client: AsyncTestClient[Any]) -> None:
    r = await client.get("/v1/sessions/")
    assert r.status_code == HTTPStatus.UNAUTHORIZED


async def test_list_sessions_returns_own_sessions(
    client: AsyncTestClient[Any],
    auth_user: User,
) -> None:
    r = await client.get("/v1/sessions/")
    assert r.status_code == HTTPStatus.OK
    data = r.json()
    assert "items" in data["data"]
    assert len(data["data"]["items"]) >= 1


async def test_delete_session_requires_auth(
    client: AsyncTestClient[Any],
    container: AsyncContainer,
    tenant: Tenant,
) -> None:
    email = unique_email()
    await create_logged_user(client, container, tenant.id, email=email)

    r = await client.get("/v1/sessions/")
    sessions = r.json()["data"]["items"]
    assert len(sessions) >= 1
    session_id = sessions[0]["id"]

    client.cookies.clear()

    r = await client.delete(f"/v1/sessions/{session_id}")
    assert r.status_code == HTTPStatus.UNAUTHORIZED


async def test_delete_own_session(
    client: AsyncTestClient[Any],
    auth_user: User,
) -> None:
    r = await client.get("/v1/sessions/")
    assert r.status_code == HTTPStatus.OK
    sessions = r.json()["data"]["items"]
    assert len(sessions) >= 1
    session_id = sessions[0]["id"]

    r = await client.delete(f"/v1/sessions/{session_id}")
    assert r.status_code == HTTPStatus.NO_CONTENT

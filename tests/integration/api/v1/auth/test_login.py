from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING, Any

from tests.integration.api.factories.user import create_user, unique_email, unique_username

if TYPE_CHECKING:
    from dishka import AsyncContainer
    from litestar.testing import AsyncTestClient

    from backend.domain.entities.tenant import Tenant


async def test_login_with_email_succeeds(
    client: AsyncTestClient[Any],
    container: AsyncContainer,
    tenant: Tenant,
) -> None:
    email = unique_email()
    await create_user(container, tenant.id, email=email, verified=True)

    r = await client.post("/v1/auth/signIn", json={"username": email, "password": "Test123!"})

    assert r.status_code == HTTPStatus.OK
    data = r.json()
    assert data["data"]["email"] == email


async def test_login_with_username_succeeds(
    client: AsyncTestClient[Any],
    container: AsyncContainer,
    tenant: Tenant,
) -> None:
    username = unique_username()
    await create_user(container, tenant.id, username=username, verified=True)

    r = await client.post("/v1/auth/signIn", json={"username": username, "password": "Test123!"})

    assert r.status_code == HTTPStatus.OK
    data = r.json()
    assert data["data"]["username"] == username


async def test_login_wrong_password_returns_401(
    client: AsyncTestClient[Any],
    container: AsyncContainer,
    tenant: Tenant,
) -> None:
    email = unique_email()
    await create_user(container, tenant.id, email=email, verified=True)

    r = await client.post("/v1/auth/signIn", json={"username": email, "password": "WrongPass1!"})

    assert r.status_code == HTTPStatus.UNAUTHORIZED


async def test_login_unverified_user_returns_422(
    client: AsyncTestClient[Any],
    container: AsyncContainer,
    tenant: Tenant,
) -> None:
    email = unique_email()
    await create_user(container, tenant.id, email=email, verified=False)

    r = await client.post("/v1/auth/signIn", json={"username": email, "password": "Test123!"})

    assert r.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


async def test_login_unknown_user_returns_401(
    client: AsyncTestClient[Any],
) -> None:
    r = await client.post(
        "/v1/auth/signIn",
        json={"username": "nobody@example.com", "password": "Test123!"},
    )

    assert r.status_code == HTTPStatus.UNAUTHORIZED


async def test_login_sets_session_cookie(
    client: AsyncTestClient[Any],
    container: AsyncContainer,
    tenant: Tenant,
) -> None:
    email = unique_email()
    await create_user(container, tenant.id, email=email, verified=True)

    r = await client.post("/v1/auth/signIn", json={"username": email, "password": "Test123!"})

    assert r.status_code == HTTPStatus.OK
    assert "session" in r.cookies

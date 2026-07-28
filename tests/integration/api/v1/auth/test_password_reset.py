from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING, Any

from backend.app.shared.events.v1.password_reset_requested import PasswordResetRequested
from backend.app.shared.ports.security.one_time_token import (
    OTT_PURPOSE_PASSWORD_RESET,
    OneTimeTokenStore,
)
from tests.integration.api.factories.user import create_user, unique_email
from tests.integration.mocks import MockDBus

if TYPE_CHECKING:
    from dishka import AsyncContainer
    from litestar.testing import AsyncTestClient

    from backend.domain.entities.tenant import Tenant


async def _issue_reset_token(container: AsyncContainer, user_id: Any) -> str:
    async with container() as c:
        store = await c.get(OneTimeTokenStore)
        return str(await store.issue(OTT_PURPOSE_PASSWORD_RESET, user_id, 3600))


async def test_password_reset_request_is_enumeration_safe(
    client: AsyncTestClient[Any],
    container: AsyncContainer,
    tenant: Tenant,
) -> None:
    email = unique_email()
    user = await create_user(container, tenant.id, email=email, verified=True)
    missing_email = unique_email()

    existing = await client.post("/v1/auth/passwordResetRequest", json={"identifier": email})
    absent = await client.post("/v1/auth/passwordResetRequest", json={"identifier": missing_email})

    assert existing.status_code == absent.status_code == HTTPStatus.OK
    assert existing.json() == absent.json()

    async with container() as c:
        dbus = await c.get(MockDBus)
    events = dbus.get_published_of_type(PasswordResetRequested)
    assert any(e.user_id == user.id for e in events)
    assert all(e.email != missing_email for e in events)


async def test_password_reset_confirm_sets_new_password(
    client: AsyncTestClient[Any],
    container: AsyncContainer,
    tenant: Tenant,
) -> None:
    email = unique_email()
    user = await create_user(container, tenant.id, email=email, verified=True)
    token = await _issue_reset_token(container, user.id)

    r = await client.post(
        "/v1/auth/passwordResetConfirm",
        json={"token": token, "password": "BrandNew1!"},
    )

    assert r.status_code == HTTPStatus.OK
    assert "session" in r.cookies

    # The new password now authenticates; the old one no longer does.
    ok = await client.post("/v1/auth/signIn", json={"username": email, "password": "BrandNew1!"})
    assert ok.status_code == HTTPStatus.OK
    bad = await client.post("/v1/auth/signIn", json={"username": email, "password": "Test123!"})
    assert bad.status_code == HTTPStatus.UNAUTHORIZED


async def test_password_reset_confirm_invalid_token_returns_422(
    client: AsyncTestClient[Any],
) -> None:
    r = await client.post(
        "/v1/auth/passwordResetConfirm",
        json={"token": "not-a-real-token", "password": "BrandNew1!"},
    )

    assert r.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


async def test_set_password_without_setup_cookie_returns_401(
    client: AsyncTestClient[Any],
) -> None:
    r = await client.post("/v1/auth/setPassword", json={"password": "BrandNew1!"})

    assert r.status_code == HTTPStatus.UNAUTHORIZED


async def test_set_password_with_invalid_setup_token_returns_422(
    client: AsyncTestClient[Any],
) -> None:
    client.cookies.set("oauth_setup", "bogus-setup-token")
    try:
        r = await client.post("/v1/auth/setPassword", json={"password": "BrandNew1!"})
    finally:
        client.cookies.delete("oauth_setup")

    assert r.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

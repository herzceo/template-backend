from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING, Any
from urllib.parse import parse_qs, urlparse

from backend.app.shared.events.v1.email_change_requested import EmailChangeRequested
from backend.app.shared.ports.security.one_time_token import (
    OTT_PURPOSE_PASSWORD_RESET,
    OneTimeTokenStore,
)
from tests.integration.api.factories.user import create_logged_user, create_user, unique_email
from tests.integration.mocks import MockDBus

if TYPE_CHECKING:
    from dishka import AsyncContainer
    from litestar.testing import AsyncTestClient

    from backend.domain.entities.tenant import Tenant
    from backend.domain.entities.user import User


async def _reauth(client: AsyncTestClient[Any], password: str = "Test123!") -> str:
    r = await client.post("/v1/auth/reauth/password", json={"password": password})
    assert r.status_code == HTTPStatus.CREATED, r.text
    return str(r.json()["data"]["reauth_token"])


async def test_reauth_password_wrong_returns_401(
    client: AsyncTestClient[Any],
    auth_user: User,
) -> None:
    r = await client.post("/v1/auth/reauth/password", json={"password": "WrongPass1!"})

    assert r.status_code == HTTPStatus.UNAUTHORIZED


async def test_change_password_with_reauth_succeeds(
    client: AsyncTestClient[Any],
    auth_user: User,
) -> None:
    token = await _reauth(client)

    r = await client.post(
        "/v1/auth/changePassword",
        json={"reauth_token": token, "new_password": "Changed123!"},
    )

    assert r.status_code == HTTPStatus.CREATED

    assert auth_user.email is not None
    ok = await client.post(
        "/v1/auth/signIn", json={"username": auth_user.email, "password": "Changed123!"}
    )
    assert ok.status_code == HTTPStatus.OK


async def test_change_password_invalid_reauth_token_returns_401(
    client: AsyncTestClient[Any],
    auth_user: User,
) -> None:
    r = await client.post(
        "/v1/auth/changePassword",
        json={"reauth_token": "bogus", "new_password": "Changed123!"},
    )

    assert r.status_code == HTTPStatus.UNAUTHORIZED


async def test_change_email_request_and_confirm(
    client: AsyncTestClient[Any],
    container: AsyncContainer,
    auth_user: User,
) -> None:
    token = await _reauth(client)
    new_email = unique_email()

    req = await client.post(
        "/v1/auth/changeEmailRequest",
        json={"reauth_token": token, "new_email": new_email},
    )
    assert req.status_code == HTTPStatus.CREATED

    async with container() as c:
        dbus = await c.get(MockDBus)
    events = dbus.get_published_of_type(EmailChangeRequested)
    event = next(e for e in events if e.user_id == auth_user.id)
    assert event.new_email == new_email
    confirm_token = parse_qs(urlparse(event.confirm_url).query)["token"][0]

    confirm = await client.post("/v1/auth/changeEmailConfirm", json={"token": confirm_token})
    assert confirm.status_code == HTTPStatus.CREATED
    assert confirm.json()["data"]["email"] == new_email


async def test_change_email_request_to_taken_email_returns_409(
    client: AsyncTestClient[Any],
    container: AsyncContainer,
    tenant: Tenant,
    auth_user: User,
) -> None:
    taken = unique_email()
    await create_user(container, tenant.id, email=taken, verified=True)
    token = await _reauth(client)

    r = await client.post(
        "/v1/auth/changeEmailRequest",
        json={"reauth_token": token, "new_email": taken},
    )

    assert r.status_code == HTTPStatus.CONFLICT


async def test_change_email_confirm_invalid_token_returns_422(
    client: AsyncTestClient[Any],
) -> None:
    r = await client.post("/v1/auth/changeEmailConfirm", json={"token": "nope"})

    assert r.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


async def test_change_password_invalidates_existing_sessions(
    client: AsyncTestClient[Any],
    auth_user: User,
) -> None:
    # The authed session works before the change.
    before = await client.get("/v1/me")
    assert before.status_code == HTTPStatus.OK

    token = await _reauth(client)
    r = await client.post(
        "/v1/auth/changePassword",
        json={"reauth_token": token, "new_password": "Changed123!"},
    )
    assert r.status_code == HTTPStatus.CREATED, r.text

    # A password change revokes every existing session, including this one.
    after = await client.get("/v1/me")
    assert after.status_code == HTTPStatus.UNAUTHORIZED


async def test_password_reset_invalidates_existing_sessions(
    client: AsyncTestClient[Any],
    container: AsyncContainer,
    tenant: Tenant,
) -> None:
    email = unique_email()
    user = await create_logged_user(client, container, tenant.id, email=email)
    old_session = client.cookies.get("session")
    assert old_session is not None

    async with container() as c:
        ott = await c.get(OneTimeTokenStore)
        reset_token = await ott.issue(OTT_PURPOSE_PASSWORD_RESET, user.id, 3600)

    confirm = await client.post(
        "/v1/auth/passwordResetConfirm",
        json={"token": reset_token, "password": "BrandNew123!"},
    )
    assert confirm.status_code == HTTPStatus.OK, confirm.text

    # Present the pre-reset session token: it must no longer authenticate.
    client.cookies.clear()
    client.cookies.set("session", old_session)
    after = await client.get("/v1/me")
    assert after.status_code == HTTPStatus.UNAUTHORIZED

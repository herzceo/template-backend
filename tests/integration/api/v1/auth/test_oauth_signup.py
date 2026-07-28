from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

from backend.app.shared.ports.auth.oauth_gateway import OAuthGateway, OAuthUserInfo
from backend.app.shared.ports.security.oauth_setup_store import OAuthSetupStore
from backend.app.shared.ports.security.verification import VerificationCodeStore
from backend.domain.enums import IdentityProvider
from tests.integration.api.factories.tenant import ensure_default_tenant
from tests.integration.api.factories.user import unique_email, unique_username
from tests.integration.mocks import MockOAuthGateway

if TYPE_CHECKING:
    from dishka import AsyncContainer
    from litestar.testing import AsyncTestClient


async def _configure_provider_without_email(container: AsyncContainer, subject_id: str) -> None:
    await ensure_default_tenant(container)
    async with container() as c:
        gateway = await c.get(OAuthGateway)
        assert isinstance(gateway, MockOAuthGateway)
        gateway.set_user_info(
            IdentityProvider.GOOGLE,
            OAuthUserInfo(
                provider=IdentityProvider.GOOGLE,
                subject_id=subject_id,
                email=None,
                display_name="Jane Doe",
                avatar_url=None,
                access_token="",
                refresh_token=None,
                scopes=None,
            ),
        )


async def _emailed_signup_code(client: AsyncTestClient[Any], container: AsyncContainer) -> str:
    """The confirmation code the queue would have mailed, keyed by setup id."""
    token = client.cookies.get("oauth_setup")
    assert token is not None
    async with container() as c:
        setup_store = await c.get(OAuthSetupStore)
        verification = await c.get(VerificationCodeStore)
        session = (await setup_store.get(token)).some(RuntimeError("no setup session"))
        return str(await verification.issue_code(UUID(session.setup_id)))


async def _initiate_state(client: AsyncTestClient[Any]) -> str:
    r = await client.get("/v1/auth/oauth/initiate", params={"provider": "google"})
    assert r.status_code == HTTPStatus.OK, r.text
    return str(r.json()["data"]["redirect"]["state"])


async def test_oauth_callback_without_email_requires_setup(
    client: AsyncTestClient[Any],
    container: AsyncContainer,
) -> None:
    await _configure_provider_without_email(container, f"g-{uuid4().hex}")
    state = await _initiate_state(client)

    r = await client.post(
        "/v1/auth/oauth/google/callback", json={"code": "auth-code", "state": state}
    )

    assert r.status_code == HTTPStatus.OK
    assert r.json()["data"]["setup_required"] is True
    assert "oauth_setup" in r.cookies


async def test_oauth_two_step_signup_creates_account(
    client: AsyncTestClient[Any],
    container: AsyncContainer,
) -> None:
    await _configure_provider_without_email(container, f"g-{uuid4().hex}")
    state = await _initiate_state(client)

    callback = await client.post(
        "/v1/auth/oauth/google/callback", json={"code": "auth-code", "state": state}
    )
    assert callback.status_code == HTTPStatus.OK
    assert callback.json()["data"]["setup_required"] is True

    email = unique_email()
    username = unique_username()
    complete = await client.post(
        "/v1/auth/oauth/completeSignup", json={"email": email, "username": username}
    )
    assert complete.status_code == HTTPStatus.OK

    code = await _emailed_signup_code(client, container)

    confirm = await client.post("/v1/auth/oauth/confirmSignup", json={"code": code})
    assert confirm.status_code == HTTPStatus.OK
    assert confirm.json()["data"]["username"] == username
    assert "session" in confirm.cookies

    # The session established by confirmSignup authenticates the new account.
    me = await client.get("/v1/me")
    assert me.status_code == HTTPStatus.OK
    assert me.json()["data"]["email"] == email


async def test_oauth_confirm_signup_wrong_code_returns_422(
    client: AsyncTestClient[Any],
    container: AsyncContainer,
) -> None:
    await _configure_provider_without_email(container, f"g-{uuid4().hex}")
    state = await _initiate_state(client)
    await client.post("/v1/auth/oauth/google/callback", json={"code": "auth-code", "state": state})
    await client.post(
        "/v1/auth/oauth/completeSignup",
        json={"email": unique_email(), "username": unique_username()},
    )
    await _emailed_signup_code(client, container)

    r = await client.post("/v1/auth/oauth/confirmSignup", json={"code": "000000"})

    assert r.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


async def test_complete_oauth_signup_without_setup_cookie_returns_401(
    client: AsyncTestClient[Any],
) -> None:
    r = await client.post(
        "/v1/auth/oauth/completeSignup",
        json={"email": unique_email(), "username": unique_username()},
    )

    assert r.status_code == HTTPStatus.UNAUTHORIZED

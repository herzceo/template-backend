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

    from backend.domain.entities.user import User


async def _oauth_only_signup(client: AsyncTestClient[Any], container: AsyncContainer) -> None:
    """Drive two-step OAuth signup, leaving the client authed as google-only.

    The resulting account's single sign-in method is the google identity.
    """
    await ensure_default_tenant(container)
    async with container() as c:
        gateway = await c.get(OAuthGateway)
        assert isinstance(gateway, MockOAuthGateway)
        gateway.set_user_info(
            IdentityProvider.GOOGLE,
            OAuthUserInfo(
                provider=IdentityProvider.GOOGLE,
                subject_id=f"g-{uuid4().hex}",
                email=None,
                display_name="Jane",
                avatar_url=None,
                access_token="",
                refresh_token=None,
                scopes=None,
            ),
        )

    initiate = await client.get("/v1/auth/oauth/initiate", params={"provider": "google"})
    state = initiate.json()["data"]["redirect"]["state"]
    await client.post("/v1/auth/oauth/google/callback", json={"code": "c", "state": state})
    await client.post(
        "/v1/auth/oauth/completeSignup",
        json={"email": unique_email(), "username": unique_username()},
    )

    token = client.cookies.get("oauth_setup")
    assert token is not None
    async with container() as c:
        setup_store = await c.get(OAuthSetupStore)
        verification = await c.get(VerificationCodeStore)
        session = (await setup_store.get(token)).some(RuntimeError("no setup session"))
        code = await verification.issue_code(UUID(session.setup_id))

    confirm = await client.post("/v1/auth/oauth/confirmSignup", json={"code": code})
    assert confirm.status_code == HTTPStatus.OK


async def test_list_identities_returns_password_methods(
    client: AsyncTestClient[Any],
    auth_user: User,
) -> None:
    r = await client.get("/v1/auth/identities")

    assert r.status_code == HTTPStatus.OK
    providers = {i["provider"] for i in r.json()["data"]["identities"]}
    assert IdentityProvider.EMAIL_PASSWORD.value in providers
    assert IdentityProvider.USERNAME_PASSWORD.value in providers


async def test_unlink_password_provider_is_rejected(
    client: AsyncTestClient[Any],
    auth_user: User,
) -> None:
    r = await client.post("/v1/auth/identities/email_password/unlink")

    assert r.status_code == HTTPStatus.BAD_REQUEST


async def test_unlink_last_credential_returns_409(
    client: AsyncTestClient[Any],
    container: AsyncContainer,
) -> None:
    await _oauth_only_signup(client, container)

    r = await client.post("/v1/auth/identities/google/unlink")

    assert r.status_code == HTTPStatus.CONFLICT

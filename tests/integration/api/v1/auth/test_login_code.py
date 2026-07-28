from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING, Any

from backend.app.shared.events.v1.login_code_requested import LoginCodeRequested
from backend.app.shared.ports.security.login_code import LoginCodeStore
from tests.integration.api.factories.user import create_user, unique_email
from tests.integration.mocks import MockDBus, MockLoginCodeStore

if TYPE_CHECKING:
    from dishka import AsyncContainer
    from litestar.testing import AsyncTestClient

    from backend.domain.entities.tenant import Tenant


async def _issue_login_code(container: AsyncContainer, user_id: Any) -> str:
    async with container() as c:
        store = await c.get(LoginCodeStore)
    assert isinstance(store, MockLoginCodeStore)
    return await store.issue_code(user_id)


async def test_login_code_request_queues_code_for_existing_account(
    client: AsyncTestClient[Any],
    container: AsyncContainer,
    tenant: Tenant,
) -> None:
    email = unique_email()
    user = await create_user(container, tenant.id, email=email, verified=True)

    r = await client.post("/v1/auth/loginCodeRequest", json={"identifier": email})

    assert r.status_code == HTTPStatus.OK
    async with container() as c:
        dbus = await c.get(MockDBus)
    events = dbus.get_published_of_type(LoginCodeRequested)
    assert any(e.user_id == user.id for e in events)


async def test_login_code_request_is_enumeration_safe(
    client: AsyncTestClient[Any],
    container: AsyncContainer,
    tenant: Tenant,
) -> None:
    email = unique_email()
    user = await create_user(container, tenant.id, email=email, verified=True)
    missing_email = unique_email()

    existing = await client.post("/v1/auth/loginCodeRequest", json={"identifier": email})
    absent = await client.post("/v1/auth/loginCodeRequest", json={"identifier": missing_email})

    # The response must be byte-identical whether or not an account exists.
    assert existing.status_code == absent.status_code == HTTPStatus.OK
    assert existing.json() == absent.json()

    async with container() as c:
        dbus = await c.get(MockDBus)
    events = dbus.get_published_of_type(LoginCodeRequested)
    # Exactly the real account queued a code; the unknown address queued nothing.
    assert any(e.user_id == user.id for e in events)
    assert all(e.email != missing_email for e in events)


async def test_login_code_verify_succeeds_and_sets_session(
    client: AsyncTestClient[Any],
    container: AsyncContainer,
    tenant: Tenant,
) -> None:
    email = unique_email()
    user = await create_user(container, tenant.id, email=email, verified=True)
    code = await _issue_login_code(container, user.id)

    r = await client.post("/v1/auth/loginCodeVerify", json={"identifier": email, "code": code})

    assert r.status_code == HTTPStatus.OK
    assert r.json()["data"]["email"] == email
    assert "session" in r.cookies


async def test_login_code_verify_wrong_code_returns_422(
    client: AsyncTestClient[Any],
    container: AsyncContainer,
    tenant: Tenant,
) -> None:
    email = unique_email()
    user = await create_user(container, tenant.id, email=email, verified=True)
    await _issue_login_code(container, user.id)

    r = await client.post("/v1/auth/loginCodeVerify", json={"identifier": email, "code": "000000"})

    assert r.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


async def test_login_code_verify_unknown_identifier_returns_422(
    client: AsyncTestClient[Any],
) -> None:
    r = await client.post(
        "/v1/auth/loginCodeVerify",
        json={"identifier": "nobody@example.com", "code": "123456"},
    )

    assert r.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


async def test_login_code_verify_uniform_error_for_unknown_vs_no_pending(
    client: AsyncTestClient[Any],
    container: AsyncContainer,
    tenant: Tenant,
) -> None:
    # (a) an identifier with no account behind it.
    unknown = await client.post(
        "/v1/auth/loginCodeVerify", json={"identifier": unique_email(), "code": "123456"}
    )
    # (b) a real account that simply has no code pending.
    email = unique_email()
    await create_user(container, tenant.id, email=email, verified=True)
    no_pending = await client.post(
        "/v1/auth/loginCodeVerify", json={"identifier": email, "code": "123456"}
    )

    # Identical status AND body — the endpoint can't distinguish the two cases.
    assert unknown.status_code == no_pending.status_code
    assert unknown.json() == no_pending.json()


async def test_login_code_request_throttled_after_limit(
    client: AsyncTestClient[Any],
    container: AsyncContainer,
    tenant: Tenant,
) -> None:
    email = unique_email()
    await create_user(container, tenant.id, email=email, verified=True)

    responses = [
        await client.post("/v1/auth/loginCodeRequest", json={"identifier": email}) for _ in range(6)
    ]

    # Default window allows 5 per IP; the 6th is throttled.
    assert [r.status_code for r in responses[:5]] == [HTTPStatus.OK] * 5
    assert responses[5].status_code == HTTPStatus.UNPROCESSABLE_ENTITY

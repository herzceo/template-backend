from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING, Any
from uuid import UUID

from backend.app.shared.ports.security.verification import VerificationCodeStore
from tests.integration.api.factories.user import create_user, unique_email
from tests.integration.mocks import MockVerificationCodeStore

if TYPE_CHECKING:
    from dishka import AsyncContainer
    from litestar.testing import AsyncTestClient

    from backend.domain.entities.tenant import Tenant


async def test_verify_email_with_valid_code_succeeds(
    client: AsyncTestClient[Any],
    container: AsyncContainer,
    tenant: Tenant,
) -> None:
    email = unique_email()
    user = await create_user(container, tenant.id, email=email, verified=False)

    async with container() as c:
        store = await c.get(VerificationCodeStore)
    assert isinstance(store, MockVerificationCodeStore)
    code = await store.issue_code(UUID(str(user.id)))

    r = await client.post("/v1/auth/verifyEmail", json={"email": email, "code": code})

    assert r.status_code == HTTPStatus.OK
    data = r.json()
    assert data["data"]["email"] == email


async def test_verify_email_wrong_code_returns_422(
    client: AsyncTestClient[Any],
    container: AsyncContainer,
    tenant: Tenant,
) -> None:
    email = unique_email()
    user = await create_user(container, tenant.id, email=email, verified=False)

    async with container() as c:
        store = await c.get(VerificationCodeStore)
    assert isinstance(store, MockVerificationCodeStore)
    await store.issue_code(UUID(str(user.id)))

    r = await client.post("/v1/auth/verifyEmail", json={"email": email, "code": "ZZZZZZ"})

    assert r.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


async def test_verify_email_unknown_email_returns_422(
    client: AsyncTestClient[Any],
) -> None:
    r = await client.post(
        "/v1/auth/verifyEmail",
        json={"email": "nobody@example.com", "code": "ABC123"},
    )

    assert r.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


async def test_verify_email_sets_session_cookie(
    client: AsyncTestClient[Any],
    container: AsyncContainer,
    tenant: Tenant,
) -> None:
    email = unique_email()
    user = await create_user(container, tenant.id, email=email, verified=False)

    async with container() as c:
        store = await c.get(VerificationCodeStore)
    assert isinstance(store, MockVerificationCodeStore)
    code = await store.issue_code(UUID(str(user.id)))

    r = await client.post("/v1/auth/verifyEmail", json={"email": email, "code": code})

    assert r.status_code == HTTPStatus.OK
    assert "session" in r.cookies

from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING, Any

from tests.integration.api.factories.user import create_logged_user, unique_email

if TYPE_CHECKING:
    from dishka import AsyncContainer
    from litestar.testing import AsyncTestClient

    from backend.domain.entities.tenant import Tenant


async def test_authenticated_request_succeeds_after_login(
    client: AsyncTestClient[Any],
    container: AsyncContainer,
    tenant: Tenant,
) -> None:
    email = unique_email()
    await create_logged_user(client, container, tenant.id, email=email)

    r = await client.get("/v1/sessions/")

    assert r.status_code == HTTPStatus.OK


async def test_unauthenticated_request_returns_401(
    client: AsyncTestClient[Any],
) -> None:
    r = await client.get("/v1/sessions/")

    assert r.status_code == HTTPStatus.UNAUTHORIZED

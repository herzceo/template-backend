from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING, Any

from backend.app.shared.db.database import Database
from tests.integration.api.factories.user import (
    create_logged_user,
    create_user,
    unique_username,
)

if TYPE_CHECKING:
    from uuid import UUID

    from dishka import AsyncContainer
    from litestar.testing import AsyncTestClient

    from backend.domain.entities.tenant import Tenant


async def _set_username_unconfirmed(container: AsyncContainer, user_id: UUID) -> None:
    async with container() as c:
        db = await c.get(Database)
        async with db:
            user = (await db.gateway.user.get_by_id(user_id)).some(RuntimeError("missing user"))
            user.username_confirmed = False
            (await db.gateway.user.update(user)).some(RuntimeError("update failed"))
            await db.commit()


async def test_username_available_for_fresh_name(
    client: AsyncTestClient[Any],
) -> None:
    r = await client.get("/v1/auth/usernameAvailable", params={"username": unique_username()})

    assert r.status_code == HTTPStatus.OK
    assert r.json()["data"]["available"] is True


async def test_username_available_reports_taken(
    client: AsyncTestClient[Any],
    container: AsyncContainer,
    tenant: Tenant,
) -> None:
    username = unique_username()
    await create_user(container, tenant.id, username=username, verified=True)

    r = await client.get("/v1/auth/usernameAvailable", params={"username": username})

    assert r.status_code == HTTPStatus.OK
    body = r.json()["data"]
    assert body["available"] is False
    assert body["reason"] == "taken"


async def test_username_available_reports_invalid(
    client: AsyncTestClient[Any],
) -> None:
    r = await client.get("/v1/auth/usernameAvailable", params={"username": "ab"})

    assert r.status_code == HTTPStatus.OK
    body = r.json()["data"]
    assert body["available"] is False
    assert body["reason"] == "invalid"


async def test_choose_username_succeeds_while_unconfirmed(
    client: AsyncTestClient[Any],
    container: AsyncContainer,
    tenant: Tenant,
) -> None:
    user = await create_logged_user(client, container, tenant.id)
    await _set_username_unconfirmed(container, user.id)
    new_username = unique_username()

    r = await client.post("/v1/auth/chooseUsername", json={"username": new_username})

    assert r.status_code == HTTPStatus.CREATED
    assert r.json()["data"]["username"] == new_username


async def test_choose_username_when_confirmed_returns_409(
    client: AsyncTestClient[Any],
    container: AsyncContainer,
    tenant: Tenant,
) -> None:
    # A factory account has a confirmed username -- it is immutable.
    await create_logged_user(client, container, tenant.id)

    r = await client.post("/v1/auth/chooseUsername", json={"username": unique_username()})

    assert r.status_code == HTTPStatus.CONFLICT
    assert r.json()["error"]["details"][0]["reason"] == "USERNAME_LOCKED"


async def test_choose_username_taken_returns_409(
    client: AsyncTestClient[Any],
    container: AsyncContainer,
    tenant: Tenant,
) -> None:
    taken = unique_username()
    await create_user(container, tenant.id, username=taken, verified=True)
    user = await create_logged_user(client, container, tenant.id)
    await _set_username_unconfirmed(container, user.id)

    r = await client.post("/v1/auth/chooseUsername", json={"username": taken})

    assert r.status_code == HTTPStatus.CONFLICT

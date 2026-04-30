from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING, Any
from uuid import uuid4

if TYPE_CHECKING:
    from litestar.testing import AsyncTestClient

    from backend.domain.entities.user import User


async def test_list_audit_logs_requires_auth(client: AsyncTestClient[Any]) -> None:
    r = await client.get("/v1/audit-logs/")
    assert r.status_code == HTTPStatus.UNAUTHORIZED


async def test_list_audit_logs(
    client: AsyncTestClient[Any],
    auth_user: User,
) -> None:
    r = await client.get("/v1/audit-logs/")
    assert r.status_code == HTTPStatus.OK
    assert "items" in r.json()["data"]


async def test_get_audit_log_not_found(
    client: AsyncTestClient[Any],
    auth_user: User,
) -> None:
    r = await client.get(f"/v1/audit-logs/{uuid4()}")
    assert r.status_code == HTTPStatus.NOT_FOUND

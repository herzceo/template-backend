from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING, Any
from uuid import uuid4

from backend.app.shared.events.v1.user_verification_requested import UserVerificationRequested
from backend.app.shared.ports.events.dbus import DBus
from tests.integration.mocks import MockDBus

if TYPE_CHECKING:
    from dishka import AsyncContainer
    from litestar.testing import AsyncTestClient

    from backend.domain.entities.tenant import Tenant


async def test_signup_creates_user_and_publishes_event(
    client: AsyncTestClient[Any],
    container: AsyncContainer,
    tenant: Tenant,
) -> None:
    email = f"signup+{uuid4().hex[:8]}@example.com"
    r = await client.post(
        "/v1/auth:signUp",
        json={
            "username": f"user_{uuid4().hex[:8]}",
            "email": email,
            "password": "Test123!",
            "tenant_id": str(tenant.id),
        },
    )
    assert r.status_code == HTTPStatus.CREATED

    async with container() as c:
        dbus = await c.get(DBus)
    assert isinstance(dbus, MockDBus)
    events = dbus.get_published_of_type(UserVerificationRequested)
    assert len(events) >= 1
    assert any(e.email == email for e in events)


async def test_signup_returns_user_data(
    client: AsyncTestClient[Any],
    tenant: Tenant,
) -> None:
    r = await client.post(
        "/v1/auth:signUp",
        json={
            "username": f"user_{uuid4().hex[:8]}",
            "email": f"data+{uuid4().hex[:8]}@example.com",
            "password": "Test123!",
            "tenant_id": str(tenant.id),
        },
    )
    assert r.status_code == HTTPStatus.CREATED
    data = r.json()
    assert "id" in data["data"]


async def test_signup_duplicate_email_returns_conflict(
    client: AsyncTestClient[Any],
    tenant: Tenant,
) -> None:
    email = f"dup+{uuid4().hex[:8]}@example.com"
    payload = {
        "email": email,
        "password": "Test123!",
        "tenant_id": str(tenant.id),
    }
    r1 = await client.post(
        "/v1/auth:signUp",
        json={**payload, "username": f"user_{uuid4().hex[:8]}"},
    )
    assert r1.status_code == HTTPStatus.CREATED

    r2 = await client.post(
        "/v1/auth:signUp",
        json={**payload, "username": f"user_{uuid4().hex[:8]}"},
    )
    assert r2.status_code == HTTPStatus.CONFLICT

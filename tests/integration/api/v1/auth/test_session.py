from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING, Any

import pytest

if TYPE_CHECKING:
    from litestar.testing import AsyncTestClient

    from backend.domain.entities.user import User

# Every authenticated endpoint on the auth controller: the session middleware must
# reject an unauthenticated caller before any handler logic runs.
_AUTHED_ENDPOINTS = [
    ("POST", "/v1/auth/changePassword"),
    ("POST", "/v1/auth/chooseUsername"),
    ("POST", "/v1/auth/changeEmailRequest"),
    ("GET", "/v1/auth/identities"),
    ("POST", "/v1/auth/identities/google/unlink"),
    ("GET", "/v1/auth/link/oauth/initiate"),
    ("POST", "/v1/auth/link/oauth/google/callback"),
    ("POST", "/v1/auth/reauth/password"),
    ("GET", "/v1/auth/reauth/oauth/initiate"),
    ("POST", "/v1/auth/reauth/oauth/google/callback"),
    ("POST", "/v1/auth/signOut"),
    ("GET", "/v1/me"),
]


@pytest.mark.parametrize(("method", "path"), _AUTHED_ENDPOINTS)
async def test_authed_endpoint_requires_session(
    client: AsyncTestClient[Any],
    method: str,
    path: str,
) -> None:
    r = await client.request(method, path, json={})

    assert r.status_code == HTTPStatus.UNAUTHORIZED


async def test_me_returns_current_user(
    client: AsyncTestClient[Any],
    auth_user: User,
) -> None:
    r = await client.get("/v1/me")

    assert r.status_code == HTTPStatus.OK
    assert r.json()["data"]["id"] == str(auth_user.id)


async def test_sign_out_ends_the_session(
    client: AsyncTestClient[Any],
    auth_user: User,
) -> None:
    out = await client.post("/v1/auth/signOut")
    assert out.status_code == HTTPStatus.OK

    after = await client.get("/v1/me")
    assert after.status_code == HTTPStatus.UNAUTHORIZED

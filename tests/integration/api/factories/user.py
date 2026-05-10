from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

from backend.app.shared.ports.auth.password_hasher import PasswordHasher
from backend.domain.entities.identity import Identity
from backend.domain.entities.profile import Profile
from backend.domain.entities.user import User
from backend.domain.enums import IdentityProvider
from backend.domain.repos.database import Database

if TYPE_CHECKING:
    from dishka import AsyncContainer
    from litestar.testing import AsyncTestClient


def unique_email(suffix: str = "") -> str:
    part = f"+{suffix}" if suffix else ""
    return f"test{part}+{uuid4().hex[:8]}@example.com"


def unique_username(suffix: str = "") -> str:
    return f"user{'_' + suffix if suffix else ''}_{uuid4().hex[:8]}"


async def create_user(
    container: AsyncContainer,
    tenant_id: UUID,
    *,
    email: str | None = None,
    username: str | None = None,
    password: str = "Test123!",
    is_active: bool = True,
    verified: bool = False,
) -> User:
    resolved_email = email or unique_email()
    resolved_username = username or unique_username()

    async with container() as c:
        db: Database = await c.get(Database)
        hasher: PasswordHasher = await c.get(PasswordHasher)

        async with db:
            user = User(
                id=uuid4(),
                username=resolved_username,
                email=resolved_email,
                tenant_id=tenant_id,
                active=is_active,
            )
            created_user = (await db.gateway.user.create(user)).some(
                RuntimeError("Failed to create user")
            )

            profile = Profile(user_id=created_user.id)
            (await db.gateway.profile.create(profile)).some(
                RuntimeError("Failed to create profile")
            )

            if verified:
                created_user.verified_at = datetime.now(UTC)
                (await db.gateway.user.update(created_user)).some(
                    RuntimeError("Failed to verify user")
                )

            credential_hash = hasher.hash(password)

            email_identity = Identity(
                id=uuid4(),
                user_id=created_user.id,
                provider=IdentityProvider.EMAIL_PASSWORD,
                provider_subject_id=resolved_email,
                credential_hash=credential_hash,
            )
            username_identity = Identity(
                id=uuid4(),
                user_id=created_user.id,
                provider=IdentityProvider.USERNAME_PASSWORD,
                provider_subject_id=resolved_username,
                credential_hash=credential_hash,
            )
            await db.gateway.identity.create(email_identity)
            await db.gateway.identity.create(username_identity)
            await db.commit()

    return created_user


async def login_user(
    client: AsyncTestClient[Any],
    email: str,
    password: str = "Test123!",
) -> None:
    r = await client.post("/v1/auth/login", json={"username": email, "password": password})
    assert r.status_code == 200, f"login failed ({r.status_code}): {r.text}"


async def create_logged_user(
    client: AsyncTestClient[Any],
    container: AsyncContainer,
    tenant_id: UUID,
    *,
    email: str | None = None,
    password: str = "Test123!",
) -> User:
    resolved_email = email or unique_email()
    user = await create_user(
        container,
        tenant_id,
        email=resolved_email,
        password=password,
        verified=True,
    )
    await login_user(client, resolved_email, password)
    return user

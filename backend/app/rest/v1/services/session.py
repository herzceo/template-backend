from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from uuid_utils.compat import UUID

from backend.app.shared.ports.security.secret_token import SecretTokenGenerator
from backend.domain.entities.session import Session
from backend.domain.repos.database import Database
from backend.internal import Option


@dataclass
class SessionService:
    db: Database
    token_generator: SecretTokenGenerator
    session_ttl: timedelta = timedelta(days=14)

    async def create_session(
        self,
        user_id: UUID,
        *,
        ip: str | None = None,
        user_agent: str | None = None,
        fingerprint: str | None = None,
        country_code: str | None = None,
    ) -> tuple[str, Session]:
        raw_token = self.token_generator.generate()
        token_hash = self.token_generator.hash(raw_token)
        now = datetime.now(UTC)

        entity = Session(
            user_id=user_id,
            token_hash=token_hash,
            ip=ip,
            user_agent=user_agent,
            fingerprint=fingerprint,
            country_code=country_code,
            expires_at=now + self.session_ttl,
        )

        async with self.db:
            created = (await self.db.gateway.session_.create(entity)).some(
                RuntimeError("Failed to create session")
            )
            await self.db.commit()
        return raw_token, created

    async def revoke_session(self, session_id: UUID) -> None:
        async with self.db:
            await self.db.gateway.session_.delete_by_id(session_id)
            await self.db.commit()

    async def resolve_session(self, raw_token: str) -> Option[Session]:
        token_hash = self.token_generator.hash(raw_token)
        async with self.db:
            session_opt = await self.db.gateway.session_.get_by_token_hash(token_hash)
            session = session_opt.value
            if session is None:
                await self.db.commit()
                return Option(None)
            if session.expires_at <= datetime.now(UTC):
                await self.db.gateway.session_.delete_by_id(session.id)
                await self.db.commit()
                return Option(None)
            await self.db.commit()
        return Option(session)

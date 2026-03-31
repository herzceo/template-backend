from dataclasses import dataclass
from datetime import datetime

from uuid_utils.compat import UUID

from backend.app.errors import AlreadyExistsError
from backend.app.rest.v1 import dtos
from backend.app.rest.v1.handlers.base import Command, Handler, HandlerType
from backend.domain.entities.session import Session
from backend.domain.repos.database import Database


class CreateSessionCommand(Command):
    user_id: str
    token_hash: str
    ip: str | None = None
    user_agent: str | None = None
    fingerprint: str | None = None
    country_code: str | None = None
    expires_at: str = ""


@dataclass
class CreateSessionHandler(
    Handler[CreateSessionCommand, dtos.Session, None], type_=HandlerType.WRITE
):
    db: Database

    async def __call__(self, cmd: CreateSessionCommand, _ctx: None = None) -> dtos.Session:
        async with self.db:
            entity = Session(
                user_id=UUID(cmd.user_id),
                token_hash=cmd.token_hash,
                ip=cmd.ip,
                user_agent=cmd.user_agent,
                fingerprint=cmd.fingerprint,
                country_code=cmd.country_code,
                expires_at=datetime.fromisoformat(cmd.expires_at),
            )
            created = (await self.db.gateway.session_.create(entity)).some(AlreadyExistsError())
            await self.db.commit()
        return dtos.Session.from_object(created)

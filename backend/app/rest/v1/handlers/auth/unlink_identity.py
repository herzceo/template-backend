from dataclasses import dataclass
from uuid import UUID

from backend.app.errors import ConflictError, InvalidInputError
from backend.app.rest.v1.handlers.base import Command, Handler, HandlerType
from backend.app.shared.db.database import Database
from backend.domain.enums import IdentityProvider

_PASSWORD_PROVIDERS = (IdentityProvider.EMAIL_PASSWORD, IdentityProvider.USERNAME_PASSWORD)


class UnlinkIdentityCommand(Command):
    user_id: UUID
    provider: IdentityProvider


@dataclass
class UnlinkIdentityHandler(Handler[UnlinkIdentityCommand, None, None], type_=HandlerType.WRITE):
    db: Database

    async def __call__(self, cmd: UnlinkIdentityCommand, _ctx: None = None) -> None:
        if cmd.provider in _PASSWORD_PROVIDERS:
            raise InvalidInputError(
                message="Password credentials can't be unlinked — change your password instead",
            )
        async with self.db:
            identities = await self.db.gateway.identity.list_by_user_id(cmd.user_id)
            remaining = [i for i in identities if i.provider != cmd.provider.value]
            if not remaining:
                raise ConflictError(
                    message="You can't unlink your only sign-in method",
                    code="last_credential",
                )
            await self.db.gateway.identity.delete_by_user_and_provider(cmd.user_id, cmd.provider)

            # Free any non-primary email this provider contributed so it can be used
            # elsewhere; the account's primary email is always retained.
            for row in await self.db.gateway.user_email.list_by_user_id(cmd.user_id):
                if row.provider == cmd.provider.value and not row.is_primary:
                    await self.db.gateway.user_email.delete_by_id(row.id)

            await self.db.commit()

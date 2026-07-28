from dataclasses import dataclass
from datetime import UTC, datetime

from backend.app.errors import AlreadyExistsError, ValidationFailedError
from backend.app.rest.v1 import dtos
from backend.app.rest.v1.handlers.base import Command, Handler, HandlerType
from backend.app.rest.v1.services.identity import IdentityService
from backend.app.shared.db.database import Database


class ChangeEmailConfirmCommand(Command):
    token: str


@dataclass
class ChangeEmailConfirmHandler(
    Handler[ChangeEmailConfirmCommand, dtos.User, None], type_=HandlerType.WRITE
):
    db: Database
    identity_service: IdentityService

    async def __call__(self, cmd: ChangeEmailConfirmCommand, _ctx: None = None) -> dtos.User:
        parsed = self.identity_service.verify_email_change_token(cmd.token)
        if parsed is None:
            raise ValidationFailedError(message="This confirmation link is invalid or has expired.")
        user_id, canonical, new_email = parsed

        async with self.db:
            user = (await self.db.gateway.user.get_by_id(user_id)).some(
                ValidationFailedError(message="This confirmation link is invalid or has expired.")
            )
            owner = await self.identity_service.email_owner_id(canonical)
            if owner is not None and owner != user_id:
                raise AlreadyExistsError(
                    message="This email is already registered", code="email_taken"
                )

            # Cascade the change to the login identity so password sign-in with the
            # new email works.
            if user.email is not None:
                await self.identity_service.rekey_email_password_identity(
                    user_id, user.email, new_email
                )

            # Free the previous primary email (unless it came from an OAuth identity
            # that still exists, in which case just demote it).
            old_primary = (await self.db.gateway.user_email.get_primary_for_user(user_id)).value
            if old_primary is not None and old_primary.normalized_email != canonical:
                if old_primary.provider is None:
                    await self.db.gateway.user_email.delete_by_id(old_primary.id)
                else:
                    old_primary.is_primary = False
                    (await self.db.gateway.user_email.update(old_primary)).some(
                        RuntimeError("Failed to demote old email")
                    )

            (
                await self.identity_service.register_email(
                    user_id, new_email, canonical, is_primary=True, verified=True
                )
            ).some(
                AlreadyExistsError(message="This email is already registered", code="email_taken")
            )

            user.email = new_email
            if user.verified_at is None:
                user.verified_at = datetime.now(UTC)
            (await self.db.gateway.user.update(user)).some(
                RuntimeError("Failed to update user email")
            )
            await self.db.commit()
        return dtos.User.from_object(user)

from dataclasses import dataclass
from uuid import UUID

from backend.app.rest.v1.dtos.identity import ConnectedIdentities, IdentityDTO
from backend.app.rest.v1.handlers.base import Command, Handler, HandlerType
from backend.app.rest.v1.services.identity import IdentityService
from backend.app.shared.db.database import Database
from backend.domain.enums import IdentityProvider


class ListIdentitiesCommand(Command):
    user_id: UUID


@dataclass
class ListIdentitiesHandler(
    Handler[ListIdentitiesCommand, ConnectedIdentities, None], type_=HandlerType.READ
):
    db: Database
    identity_service: IdentityService

    async def __call__(self, cmd: ListIdentitiesCommand, _ctx: None = None) -> ConnectedIdentities:
        async with self.db:
            identities = await self.identity_service.get_identities_for_user(cmd.user_id)
        # Scalar attributes stay accessible on the expunged entities after the block.
        return ConnectedIdentities(
            identities=[
                IdentityDTO(
                    id=identity.id,
                    user_id=identity.user_id,
                    provider=IdentityProvider(identity.provider),
                    provider_subject_id=identity.provider_subject_id,
                    provider_email=identity.provider_email,
                    provider_display_name=identity.provider_display_name,
                    provider_avatar_url=identity.provider_avatar_url,
                    has_password=identity.credential_hash is not None,
                    created_at=identity.created_at,
                    updated_at=identity.updated_at,
                )
                for identity in identities
            ]
        )

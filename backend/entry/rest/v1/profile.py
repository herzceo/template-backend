from uuid import UUID

import msgspec.structs
from litestar import Controller, get, patch

from backend.app.rest.v1 import dtos
from backend.app.rest.v1.handlers import profile as profile_handlers
from backend.internal.di import Depends

from .dtos import UpdateProfileBody


class ProfileController(Controller):
    path = "/users/{user_id:str}/profile"
    tags = ("Profile",)

    @get("/")
    async def get_profile(
        self,
        user_id: str,
        handler: Depends[profile_handlers.GetProfileHandler],
    ) -> dtos.Profile:
        return await handler(profile_handlers.GetProfileCommand(user_id=UUID(user_id)))

    @patch("/")
    async def update_profile(
        self,
        user_id: str,
        data: UpdateProfileBody,
        handler: Depends[profile_handlers.UpdateProfileHandler],
    ) -> dtos.Profile:
        return await handler(
            profile_handlers.UpdateProfileCommand(
                user_id=UUID(user_id), **msgspec.structs.asdict(data)
            )
        )

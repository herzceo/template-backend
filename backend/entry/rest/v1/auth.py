from typing import Any

from litestar import Controller, Request, post

from backend.app.rest.v1 import dtos
from backend.app.rest.v1.handlers import auth
from backend.entry.rest.common.scope import set_session_token
from backend.internal.di import Depends, inject


class AuthController(Controller):
    path = "/auth"
    tags = ("Auth",)

    @post("/login", exclude_from_auth=True)
    @inject
    async def login(
        self,
        data: auth.LoginCommand,
        handler: Depends[auth.LoginHandler],
        request: Request[Any, Any, Any],
    ) -> dtos.User:
        ctx = await handler(data)
        set_session_token(request.scope, ctx.token)
        return ctx.data

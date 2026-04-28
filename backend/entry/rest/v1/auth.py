from typing import Any

from litestar import Controller, Request, get, post

from backend.app.rest.v1 import dtos
from backend.app.rest.v1.dtos.identity import InitiateResult
from backend.app.rest.v1.handlers import auth
from backend.domain.enums import IdentityProvider
from backend.entry.rest.common.response import result
from backend.entry.rest.common.scope import set_session_token
from backend.internal.di import Depends, inject


class AuthController(Controller):
    path = "/auth"
    tags = ("Auth",)

    @post("/login", exclude_from_auth=True)
    @inject
    @result
    async def login(
        self,
        data: auth.LoginCommand,
        handler: Depends[auth.LoginHandler],
        request: Request[Any, Any, Any],
    ) -> dtos.User:
        ctx = await handler(data)
        set_session_token(request.scope, ctx.token)
        return ctx.data

    @post("/signup", exclude_from_auth=True)
    @inject
    @result
    async def signup(
        self,
        data: auth.SignupCommand,
        handler: Depends[auth.SignupHandler],
    ) -> dtos.User:
        return await handler(data)

    @post("/verify-email", exclude_from_auth=True)
    @inject
    @result
    async def verify_email(
        self,
        data: auth.VerifyEmailCommand,
        handler: Depends[auth.VerifyEmailHandler],
        request: Request[Any, Any, Any],
    ) -> dtos.User:
        ctx = await handler(data)
        set_session_token(request.scope, ctx.token)
        return ctx.data

    @post("/resend-verification", exclude_from_auth=True)
    @inject
    @result
    async def resend_verification(
        self,
        data: auth.ResendVerificationCommand,
        handler: Depends[auth.ResendVerificationHandler],
    ) -> None:
        await handler(data)

    @get("/oauth/{provider:str}/initiate", exclude_from_auth=True)
    @inject
    @result
    async def initiate_oauth(
        self,
        provider: IdentityProvider,
        handler: Depends[auth.InitiateOAuthHandler],
    ) -> InitiateResult:
        return await handler(auth.InitiateOAuthCommand(provider=provider))

    @get("/oauth/{provider:str}/callback", exclude_from_auth=True)
    @inject
    @result
    async def oauth_callback(
        self,
        provider: IdentityProvider,
        code: str,
        state: str,
        handler: Depends[auth.OAuthCallbackHandler],
        request: Request[Any, Any, Any],
    ) -> dtos.User:
        ctx = await handler(auth.OAuthCallbackCommand(provider=provider, code=code, state=state))
        set_session_token(request.scope, ctx.token)
        return ctx.data

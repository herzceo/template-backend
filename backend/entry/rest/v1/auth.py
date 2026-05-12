from typing import Annotated, Any

from litestar import Controller, Request, get, post
from litestar.params import Parameter

from backend.app.rest.v1 import dtos
from backend.app.rest.v1.dtos.identity import InitiateResult
from backend.app.rest.v1.handlers import auth
from backend.domain.enums import IdentityProvider
from backend.entry.rest.common.scope import set_session_token
from backend.entry.rest.v1.dtos import SignInBody, VerifyEmailBody
from backend.internal.di import Depends


class AuthController(Controller):
    path = ""
    tags = ("Auth",)

    @post("/auth:signIn", exclude_from_auth=True, status_code=200)
    async def sign_in(
        self,
        data: SignInBody,
        handler: Depends[auth.LoginHandler],
        request: Request[Any, Any, Any],
    ) -> dtos.User:
        ip = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
        ctx = await handler(
            auth.LoginCommand(
                username=data.username,
                password=data.password,
                ip=ip,
                user_agent=user_agent,
                client_device=data.client_device,
            )
        )
        set_session_token(request.scope, ctx.token)
        return ctx.data

    @post("/auth:signUp", exclude_from_auth=True)
    async def sign_up(
        self,
        data: auth.SignupCommand,
        handler: Depends[auth.SignupHandler],
    ) -> dtos.User:
        return await handler(data)

    @post("/auth:verifyEmail", exclude_from_auth=True, status_code=200)
    async def verify_email(
        self,
        data: VerifyEmailBody,
        handler: Depends[auth.VerifyEmailHandler],
        request: Request[Any, Any, Any],
    ) -> dtos.User:
        ip = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
        ctx = await handler(
            auth.VerifyEmailCommand(
                email=data.email,
                code=data.code,
                ip=ip,
                user_agent=user_agent,
                client_device=data.client_device,
            )
        )
        set_session_token(request.scope, ctx.token)
        return ctx.data

    @post("/auth:resendVerification", exclude_from_auth=True)
    async def resend_verification(
        self,
        data: auth.ResendVerificationCommand,
        handler: Depends[auth.ResendVerificationHandler],
    ) -> None:
        await handler(data)

    @get("/auth/oauth:initiate", exclude_from_auth=True)
    async def initiate_oauth(
        self,
        provider: IdentityProvider,
        handler: Depends[auth.InitiateOAuthHandler],
    ) -> InitiateResult:
        return await handler(auth.InitiateOAuthCommand(provider=provider))

    @get("/auth/oauth:callback", exclude_from_auth=True)
    async def oauth_callback(
        self,
        provider: IdentityProvider,
        code: str,
        oauth_state: Annotated[str, Parameter(query="state")],
        handler: Depends[auth.OAuthCallbackHandler],
        request: Request[Any, Any, Any],
    ) -> dtos.User:
        ctx = await handler(
            auth.OAuthCallbackCommand(provider=provider, code=code, state=oauth_state)
        )
        set_session_token(request.scope, ctx.token)
        return ctx.data

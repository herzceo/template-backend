from typing import Any

from litestar import Controller, Request, get, post

from backend.app.errors import AuthenticationRequiredError
from backend.app.rest.v1 import dtos
from backend.app.rest.v1.dtos.identity import ConnectedIdentities, InitiateResult
from backend.app.rest.v1.handlers import auth
from backend.app.shared.ports.security.oauth_setup_store import OAUTH_SETUP_TTL_SECONDS
from backend.domain.enums import IdentityProvider
from backend.entry.rest.common.response import result
from backend.entry.rest.common.scope import (
    clear_oauth_setup_token,
    read_oauth_setup_cookie,
    set_oauth_setup_token,
    set_session_token,
)
from backend.entry.rest.v1.dtos import (
    ChangeEmailConfirmBody,
    ChangeEmailRequestBody,
    ChangePasswordBody,
    ChooseUsernameBody,
    CompleteOAuthSignupBody,
    ConfirmOAuthSignupBody,
    LoginCodeRequestBody,
    LoginCodeVerifyBody,
    OAuthCallbackBody,
    OAuthExchangeBody,
    PasswordResetConfirmBody,
    PasswordResetRequestBody,
    ReauthPasswordBody,
    SetPasswordBody,
    SignInBody,
    VerifyEmailBody,
)
from backend.internal.di import Depends, inject


def _oauth_redirect_uri(request: Request[Any, Any, Any], provider: IdentityProvider) -> str:
    """The OAuth callback URL the provider redirects back to.

    Derived from the (proxied) request host so any origin works, and must be
    byte-identical at initiate and exchange (the OAuth token exchange requires
    it). Points at a frontend page that reads ``code``/``state`` and POSTs them
    back to the matching exchange endpoint — the single seam a fork adapts to its
    own callback routing.
    """
    scheme = request.headers.get("x-forwarded-proto") or request.url.scheme
    host = request.headers.get("x-forwarded-host") or request.headers.get("host") or ""
    return f"{scheme}://{host}/oauth/{provider.value}/callback"


def _require_setup_token(request: Request[Any, Any, Any]) -> str:
    """Read the OAuth-signup setup token from its httpOnly cookie.

    Never accepted from the body or query string — see
    ``entry/rest/common/scope.py`` for why keeping it out of URLs matters.
    """
    token = read_oauth_setup_cookie(request)
    if not token:
        raise AuthenticationRequiredError(
            message="This signup session expired, start again", code="setup_expired"
        )
    return token


def _ip(request: Request[Any, Any, Any]) -> str | None:
    return request.client.host if request.client else None


class AuthController(Controller):
    path = ""
    tags = ("Auth",)

    @post("/auth/signIn", exclude_from_auth=True, status_code=200)
    @inject
    @result
    async def sign_in(
        self,
        data: SignInBody,
        handler: Depends[auth.LoginHandler],
        request: Request[Any, Any, Any],
    ) -> dtos.User:
        ctx = await handler(
            auth.LoginCommand(
                username=data.username,
                password=data.password,
                ip=_ip(request),
                user_agent=request.headers.get("user-agent"),
                client_device=data.client_device,
            )
        )
        set_session_token(request.scope, ctx.token)
        return ctx.data

    @post("/auth/signUp", exclude_from_auth=True)
    @inject
    @result
    async def sign_up(
        self,
        data: auth.SignupCommand,
        handler: Depends[auth.SignupHandler],
    ) -> dtos.User:
        return await handler(data)

    @post("/auth/verifyEmail", exclude_from_auth=True, status_code=200)
    @inject
    @result
    async def verify_email(
        self,
        data: VerifyEmailBody,
        handler: Depends[auth.VerifyEmailHandler],
        request: Request[Any, Any, Any],
    ) -> dtos.User:
        ctx = await handler(
            auth.VerifyEmailCommand(
                email=data.email,
                code=data.code,
                ip=_ip(request),
                user_agent=request.headers.get("user-agent"),
                client_device=data.client_device,
            )
        )
        set_session_token(request.scope, ctx.token)
        return ctx.data

    @post("/auth/resendVerification", exclude_from_auth=True)
    @inject
    @result
    async def resend_verification(
        self,
        data: auth.ResendVerificationCommand,
        handler: Depends[auth.ResendVerificationHandler],
    ) -> None:
        await handler(data)

    # -- Passwordless login (email code) -------------------------------------

    @post("/auth/loginCodeRequest", exclude_from_auth=True, status_code=200)
    @inject
    @result
    async def login_code_request(
        self,
        data: LoginCodeRequestBody,
        handler: Depends[auth.RequestLoginCodeHandler],
        request: Request[Any, Any, Any],
    ) -> dtos.DeliveryAck:
        return await handler(
            auth.LoginCodeRequestCommand(identifier=data.identifier, ip=_ip(request))
        )

    @post("/auth/loginCodeVerify", exclude_from_auth=True, status_code=200)
    @inject
    @result
    async def login_code_verify(
        self,
        data: LoginCodeVerifyBody,
        handler: Depends[auth.VerifyLoginCodeHandler],
        request: Request[Any, Any, Any],
    ) -> dtos.User:
        ctx = await handler(
            auth.LoginCodeVerifyCommand(
                identifier=data.identifier,
                code=data.code,
                ip=_ip(request),
                user_agent=request.headers.get("user-agent"),
                client_device=data.client_device,
            )
        )
        set_session_token(request.scope, ctx.token)
        return ctx.data

    # -- Password reset / management -----------------------------------------

    @post("/auth/passwordResetRequest", exclude_from_auth=True, status_code=200)
    @inject
    @result
    async def password_reset_request(
        self,
        data: PasswordResetRequestBody,
        handler: Depends[auth.RequestPasswordResetHandler],
        request: Request[Any, Any, Any],
    ) -> dtos.DeliveryAck:
        return await handler(
            auth.PasswordResetRequestCommand(identifier=data.identifier, ip=_ip(request))
        )

    @post("/auth/passwordResetConfirm", exclude_from_auth=True, status_code=200)
    @inject
    @result
    async def password_reset_confirm(
        self,
        data: PasswordResetConfirmBody,
        handler: Depends[auth.ConfirmPasswordResetHandler],
        request: Request[Any, Any, Any],
    ) -> dtos.User:
        ctx = await handler(
            auth.PasswordResetConfirmCommand(
                token=data.token,
                password=data.password,
                ip=_ip(request),
                user_agent=request.headers.get("user-agent"),
                client_device=data.client_device,
            )
        )
        set_session_token(request.scope, ctx.token)
        return ctx.data

    @post("/auth/setPassword", exclude_from_auth=True, status_code=200)
    @inject
    @result
    async def set_password(
        self,
        data: SetPasswordBody,
        handler: Depends[auth.SetPasswordHandler],
        request: Request[Any, Any, Any],
    ) -> dtos.User:
        ctx = await handler(
            auth.SetPasswordCommand(
                setup_token=_require_setup_token(request),
                password=data.password,
                ip=_ip(request),
                user_agent=request.headers.get("user-agent"),
                client_device=data.client_device,
            )
        )
        set_session_token(request.scope, ctx.token)
        clear_oauth_setup_token(request.scope)
        return ctx.data

    @post("/auth/changePassword")
    @inject
    @result
    async def change_password(
        self,
        data: ChangePasswordBody,
        handler: Depends[auth.ChangePasswordHandler],
        request: Request[Any, Any, Any],
    ) -> dtos.User:
        return await handler(
            auth.ChangePasswordCommand(
                user_id=request.auth.user_id,
                reauth_token=data.reauth_token,
                new_password=data.new_password,
            )
        )

    # -- Username selection ---------------------------------------------------

    @get("/auth/usernameAvailable", exclude_from_auth=True)
    @inject
    @result
    async def username_available(
        self,
        username: str,
        handler: Depends[auth.UsernameAvailabilityHandler],
    ) -> dtos.UsernameAvailability:
        return await handler(auth.UsernameAvailabilityCommand(username=username))

    @post("/auth/chooseUsername")
    @inject
    @result
    async def choose_username(
        self,
        data: ChooseUsernameBody,
        handler: Depends[auth.ChooseUsernameHandler],
        request: Request[Any, Any, Any],
    ) -> dtos.User:
        return await handler(
            auth.ChooseUsernameCommand(user_id=request.auth.user_id, username=data.username)
        )

    # -- Email change ---------------------------------------------------------

    @post("/auth/changeEmailRequest")
    @inject
    @result
    async def change_email_request(
        self,
        data: ChangeEmailRequestBody,
        handler: Depends[auth.ChangeEmailRequestHandler],
        request: Request[Any, Any, Any],
    ) -> dtos.DeliveryAck:
        return await handler(
            auth.ChangeEmailRequestCommand(
                user_id=request.auth.user_id,
                reauth_token=data.reauth_token,
                new_email=data.new_email,
                ip=_ip(request),
            )
        )

    @post("/auth/changeEmailConfirm", exclude_from_auth=True)
    @inject
    @result
    async def change_email_confirm(
        self,
        data: ChangeEmailConfirmBody,
        handler: Depends[auth.ChangeEmailConfirmHandler],
    ) -> dtos.User:
        return await handler(auth.ChangeEmailConfirmCommand(token=data.token))

    # -- OAuth login / two-step signup ---------------------------------------

    @get("/auth/oauth/initiate", exclude_from_auth=True)
    @inject
    @result
    async def initiate_oauth(
        self,
        provider: IdentityProvider,
        handler: Depends[auth.InitiateOAuthHandler],
        request: Request[Any, Any, Any],
    ) -> InitiateResult:
        return await handler(
            auth.InitiateOAuthCommand(
                provider=provider, redirect_uri=_oauth_redirect_uri(request, provider)
            )
        )

    @post("/auth/oauth/{provider:str}/callback", exclude_from_auth=True, status_code=200)
    @inject
    @result
    async def oauth_callback(
        self,
        provider: IdentityProvider,
        data: OAuthCallbackBody,
        handler: Depends[auth.OAuthCallbackHandler],
        request: Request[Any, Any, Any],
    ) -> dtos.OAuthCallbackResult:
        outcome = await handler(
            auth.OAuthCallbackCommand(
                provider=provider,
                code=data.code,
                state=data.state,
                redirect_uri=_oauth_redirect_uri(request, provider),
                device_fingerprint=data.device_fingerprint,
            )
        )
        if outcome.session_token is not None:
            set_session_token(request.scope, outcome.session_token)
            clear_oauth_setup_token(request.scope)
        if outcome.setup_token is not None:
            set_oauth_setup_token(request.scope, outcome.setup_token, OAUTH_SETUP_TTL_SECONDS)
        return outcome.result

    @post("/auth/oauth/completeSignup", exclude_from_auth=True, status_code=200)
    @inject
    @result
    async def complete_oauth_signup(
        self,
        data: CompleteOAuthSignupBody,
        handler: Depends[auth.CompleteOAuthSignupHandler],
        request: Request[Any, Any, Any],
    ) -> dtos.OAuthSignupChallenge:
        return await handler(
            auth.CompleteOAuthSignupCommand(
                setup_token=_require_setup_token(request),
                email=data.email,
                username=data.username,
                device_fingerprint=data.device_fingerprint,
                ip=_ip(request),
            )
        )

    @post("/auth/oauth/confirmSignup", exclude_from_auth=True, status_code=200)
    @inject
    @result
    async def confirm_oauth_signup(
        self,
        data: ConfirmOAuthSignupBody,
        handler: Depends[auth.ConfirmOAuthSignupHandler],
        request: Request[Any, Any, Any],
    ) -> dtos.User:
        ctx = await handler(
            auth.ConfirmOAuthSignupCommand(
                setup_token=_require_setup_token(request),
                code=data.code,
                ip=_ip(request),
                user_agent=request.headers.get("user-agent"),
                client_device=data.client_device,
                device_fingerprint=data.device_fingerprint,
            )
        )
        set_session_token(request.scope, ctx.token)
        clear_oauth_setup_token(request.scope)
        return ctx.data

    # -- Identity linking -----------------------------------------------------

    @get("/auth/identities")
    @inject
    @result
    async def list_identities(
        self,
        handler: Depends[auth.ListIdentitiesHandler],
        request: Request[Any, Any, Any],
    ) -> ConnectedIdentities:
        return await handler(auth.ListIdentitiesCommand(user_id=request.auth.user_id))

    @post("/auth/identities/{provider:str}/unlink")
    @inject
    @result
    async def unlink_identity(
        self,
        provider: IdentityProvider,
        handler: Depends[auth.UnlinkIdentityHandler],
        request: Request[Any, Any, Any],
    ) -> None:
        await handler(auth.UnlinkIdentityCommand(user_id=request.auth.user_id, provider=provider))

    @get("/auth/link/oauth/initiate")
    @inject
    @result
    async def link_oauth_initiate(
        self,
        provider: IdentityProvider,
        handler: Depends[auth.LinkOAuthInitiateHandler],
        request: Request[Any, Any, Any],
    ) -> InitiateResult:
        return await handler(
            auth.LinkOAuthInitiateCommand(
                user_id=request.auth.user_id,
                provider=provider,
                redirect_uri=_oauth_redirect_uri(request, provider),
            )
        )

    @post("/auth/link/oauth/{provider:str}/callback")
    @inject
    @result
    async def link_oauth_callback(
        self,
        provider: IdentityProvider,
        data: OAuthExchangeBody,
        handler: Depends[auth.LinkOAuthCallbackHandler],
        request: Request[Any, Any, Any],
    ) -> None:
        await handler(
            auth.LinkOAuthCallbackCommand(
                user_id=request.auth.user_id,
                provider=provider,
                code=data.code,
                state=data.state,
                redirect_uri=_oauth_redirect_uri(request, provider),
            )
        )

    # -- Step-up reauth -------------------------------------------------------

    @post("/auth/reauth/password")
    @inject
    @result
    async def reauth_password(
        self,
        data: ReauthPasswordBody,
        handler: Depends[auth.ReauthPasswordHandler],
        request: Request[Any, Any, Any],
    ) -> dtos.ReauthToken:
        return await handler(
            auth.ReauthPasswordCommand(user_id=request.auth.user_id, password=data.password)
        )

    @get("/auth/reauth/oauth/initiate")
    @inject
    @result
    async def reauth_oauth_initiate(
        self,
        provider: IdentityProvider,
        handler: Depends[auth.ReauthOAuthInitiateHandler],
        request: Request[Any, Any, Any],
    ) -> InitiateResult:
        return await handler(
            auth.ReauthOAuthInitiateCommand(
                user_id=request.auth.user_id,
                provider=provider,
                redirect_uri=_oauth_redirect_uri(request, provider),
            )
        )

    @post("/auth/reauth/oauth/{provider:str}/callback")
    @inject
    @result
    async def reauth_oauth_callback(
        self,
        provider: IdentityProvider,
        data: OAuthExchangeBody,
        handler: Depends[auth.ReauthOAuthCallbackHandler],
        request: Request[Any, Any, Any],
    ) -> dtos.ReauthToken:
        return await handler(
            auth.ReauthOAuthCallbackCommand(
                user_id=request.auth.user_id,
                provider=provider,
                code=data.code,
                state=data.state,
                redirect_uri=_oauth_redirect_uri(request, provider),
            )
        )

    # -- Session --------------------------------------------------------------

    @post("/auth/signOut", status_code=200)
    @inject
    @result
    async def sign_out(
        self,
        handler: Depends[auth.LogoutHandler],
        request: Request[Any, Any, Any],
    ) -> None:
        await handler(auth.LogoutCommand(session_id=request.auth.id))

    @get("/me")
    @inject
    @result
    async def get_me(
        self,
        handler: Depends[auth.GetMeHandler],
        request: Request[Any, Any, Any],
    ) -> dtos.User:
        return await handler(auth.GetMeCommand(user_id=request.auth.user_id))

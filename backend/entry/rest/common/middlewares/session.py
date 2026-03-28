import hashlib
from typing import Any, Literal

from litestar import Request
from litestar.exceptions import NotAuthorizedException
from litestar.middleware.base import AbstractMiddleware
from litestar.types import ASGIApp, Empty, Message, Receive, Scope, Send

from backend.app.rest.v1.dtos.sessions import Session as SessionDTO
from backend.app.rest.v1.services.session import SessionService
from backend.internal.di import Depends, from_di, inject


class SessionMiddleware(AbstractMiddleware):
    def __init__(
        self,
        app: ASGIApp,
        exclude_from_auth_key: str = "exclude_from_auth",
        session_cookie_key: str = "session",
        exclude: str | list[str] | None = None,
        *,
        secure: bool = False,
        httponly: bool = True,
        samesite: Literal["lax", "strict", "none"] = "lax",
        max_age: int = 86400 * 14,
    ) -> None:
        super().__init__(app)
        self.exclude_from_auth_key = exclude_from_auth_key
        self.session_cookie_key = session_cookie_key
        self._cookie_prefix = "__Host-" if secure else ""
        self.exclude: list[str] = [exclude] if isinstance(exclude, str) else (exclude or [])
        self.secure = secure
        self.httponly = httponly
        self.samesite = samesite
        self.max_age = max_age

    @property
    def cookie_key(self) -> str:
        return f"{self._cookie_prefix}{self.session_cookie_key}"

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        return await self._validate_request(scope, receive, send)

    @inject
    async def _validate_request(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
        session_service: Depends[SessionService] = from_di(),
    ) -> None:
        request: Request[Any, Any, Any] = Request(scope, receive, send)

        if self._should_exclude(request):
            send_wrapper = self._create_send_wrapper(send, scope, None)
            await self.app(scope, receive, send_wrapper)
            return

        session_token = request.cookies.get(self.cookie_key)

        if not session_token:
            msg = "Session cookie not found"
            raise NotAuthorizedException(msg)

        token_hash = hashlib.sha256(session_token.encode()).hexdigest()
        session_opt = await session_service.resolve_session(token_hash)

        if session_opt.value is None:
            msg = "Invalid or expired session"
            raise NotAuthorizedException(msg)

        session = session_opt.value
        scope["auth"] = SessionDTO.from_object(session)

        send_wrapper = self._create_send_wrapper(send, scope, session_token)
        await self.app(scope, receive, send_wrapper)

    def _should_exclude(self, request: Request[Any, Any, Any]) -> bool:
        if any(request.url.path.startswith(path) for path in self.exclude):
            return True
        if request.route_handler:
            return bool(request.route_handler.opt.get(self.exclude_from_auth_key, False))
        return False

    def _build_set_cookie_header(self, name: str, value: str, max_age: int) -> tuple[bytes, bytes]:
        cookie_parts = [f"{name}={value}", f"Max-Age={max_age}", "Path=/"]
        if self.httponly:
            cookie_parts.append("HttpOnly")
        if self.secure:
            cookie_parts.append("Secure")
        if self.samesite:
            cookie_parts.append(f"SameSite={self.samesite.capitalize()}")
        return (b"set-cookie", "; ".join(cookie_parts).encode())

    def _create_send_wrapper(
        self,
        send: Send,
        scope: Scope,
        incoming_session_token: str | None,
    ) -> Send:
        async def send_wrapper(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                new_token: str | None = scope.get("state", {}).get("session_token")

                if new_token and new_token != incoming_session_token:
                    headers.append(
                        self._build_set_cookie_header(self.cookie_key, new_token, self.max_age)
                    )

                elif scope.get("auth") is Empty and incoming_session_token:
                    headers.append(self._build_set_cookie_header(self.cookie_key, "", 0))

                message["headers"] = headers

            await send(message)

        return send_wrapper

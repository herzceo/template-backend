from typing import Any

from litestar import Request
from litestar.types import Scope

# The OAuth-signup setup token rides in its own short-lived httpOnly cookie and is
# NEVER returned in a response body or URL. ``exchange_oauth_code`` resolves an
# account by ``(provider, subject_id)`` alone, so a leaked setup token would let an
# attacker bind the victim's OAuth identity to the attacker's verified email —
# after which the victim's "Sign in with {Provider}" permanently logs them into
# the attacker's account. Keeping it out of URLs holds its leak surface to that of
# the session cookie.
SETUP_COOKIE_NAME = "oauth_setup"


def set_session_token(scope: Scope, token: str) -> None:
    scope.setdefault("state", {})["session_token"] = token


def get_session_token(scope: Scope) -> str | None:
    return scope.get("state", {}).get("session_token")


def read_oauth_setup_cookie(request: Request[Any, Any, Any]) -> str | None:
    """Read the OAuth-signup setup token from the request cookies."""
    return request.cookies.get(SETUP_COOKIE_NAME)


def set_oauth_setup_token(scope: Scope, token: str, max_age: int) -> None:
    scope.setdefault("state", {})["oauth_setup_token"] = (token, max_age)


def clear_oauth_setup_token(scope: Scope) -> None:
    scope.setdefault("state", {})["oauth_setup_clear"] = True


def get_oauth_setup_token(scope: Scope) -> tuple[str, int] | None:
    value: tuple[str, int] | None = scope.get("state", {}).get("oauth_setup_token")
    return value


def oauth_setup_cleared(scope: Scope) -> bool:
    return bool(scope.get("state", {}).get("oauth_setup_clear"))

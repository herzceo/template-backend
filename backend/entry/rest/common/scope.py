from litestar.types import Scope


def set_session_token(scope: Scope, token: str) -> None:
    scope.setdefault("state", {})["session_token"] = token


def get_session_token(scope: Scope) -> str | None:
    return scope.get("state", {}).get("session_token")

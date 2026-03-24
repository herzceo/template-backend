from __future__ import annotations

from typing import TYPE_CHECKING

from backend.internal.dto import StructDTO

if TYPE_CHECKING:
    from backend.infra.external.http.sessions.base import HTTPSession


class HTTPClient[S: StructDTO]:
    __slots__ = ("_session", "_settings")

    def __init__(self, session: HTTPSession, settings: S) -> None:
        self._session = session
        self._settings = settings

    @property
    def _auth_headers(self) -> dict[str, str]:
        return {}

    def _url(self, endpoint: str, **path_params: str) -> str:
        if path_params:
            return endpoint.format(**path_params)
        return endpoint

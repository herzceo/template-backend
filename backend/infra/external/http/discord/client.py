from __future__ import annotations

from typing import TYPE_CHECKING
from urllib.parse import urlencode

from backend.infra.external.http.client import HTTPClient
from backend.infra.external.http.discord import io
from backend.infra.external.http.discord.config import DiscordOAuthSettings
from backend.infra.external.http.discord.endpoints import Endpoint

if TYPE_CHECKING:
    from backend.infra.external.http.sessions.base import HTTPResponse
    from backend.internal.result import Result


class DiscordOAuthClient(HTTPClient[DiscordOAuthSettings]):
    def _url(self, endpoint: str, **path_params: str) -> str:
        path = endpoint.format(**path_params) if path_params else endpoint
        return self._settings.BASE_URL + path

    @staticmethod
    def _bearer_headers(access_token: str) -> dict[str, str]:
        return {"Authorization": f"Bearer {access_token}"}

    async def exchange_code(self, code: str) -> Result[io.TokenResponse, HTTPResponse]:
        response = await self._session.post(
            url=self._url(Endpoint.OAUTH_TOKEN),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data=urlencode(
                {
                    "client_id": self._settings.CLIENT_ID,
                    "client_secret": self._settings.CLIENT_SECRET,
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": self._settings.REDIRECT_URI,
                }
            ).encode(),
        )
        return response.as_result(io.TokenResponse)

    async def get_user_info(self, access_token: str) -> Result[io.UserInfoResponse, HTTPResponse]:
        response = await self._session.get(
            url=self._url(Endpoint.API_USERINFO),
            headers=self._bearer_headers(access_token),
        )
        return response.as_result(io.UserInfoResponse)

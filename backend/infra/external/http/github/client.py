from __future__ import annotations

from typing import TYPE_CHECKING

from backend.infra.external.http.client import HTTPClient
from backend.infra.external.http.github import io
from backend.infra.external.http.github.config import GitHubOAuthConfig
from backend.infra.external.http.github.endpoints import Endpoint

if TYPE_CHECKING:
    from backend.infra.external.http.sessions.base import HTTPResponse
    from backend.internal.result import Result


class GitHubOAuthClient(HTTPClient[GitHubOAuthConfig]):
    def _oauth_url(self, endpoint: Endpoint, **path_params: str) -> str:
        path = endpoint.value.format(**path_params) if path_params else endpoint.value
        return self._config.OAUTH_BASE_URL + path

    def _api_url(self, endpoint: Endpoint, **path_params: str) -> str:
        path = endpoint.value.format(**path_params) if path_params else endpoint.value
        return self._config.API_BASE_URL + path

    @staticmethod
    def _bearer_headers(access_token: str) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
        }

    async def exchange_code(
        self, code: str, redirect_uri: str
    ) -> Result[io.TokenResponse, HTTPResponse]:
        response = await self._session.post(
            url=self._oauth_url(Endpoint.OAUTH_TOKEN),
            json={
                "client_id": self._config.GITHUB_CLIENT_ID,
                "client_secret": self._config.GITHUB_CLIENT_SECRET,
                "code": code,
                "redirect_uri": redirect_uri,
            },
            headers={"Accept": "application/json"},
        )
        return response.as_result(io.TokenResponse)

    async def get_user_info(self, access_token: str) -> Result[io.UserInfoResponse, HTTPResponse]:
        response = await self._session.get(
            url=self._api_url(Endpoint.API_USER),
            headers=self._bearer_headers(access_token),
        )
        return response.as_result(io.UserInfoResponse)

    async def get_emails(self, access_token: str) -> list[io.EmailEntry]:
        response = await self._session.get(
            url=self._api_url(Endpoint.API_EMAILS),
            headers=self._bearer_headers(access_token),
        )
        return [io.EmailEntry.from_builtins(e) for e in response.json()]

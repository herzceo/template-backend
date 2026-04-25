from __future__ import annotations

from typing import TYPE_CHECKING, Unpack

from backend.infra.external.http.client import HTTPClient
from backend.infra.external.http.resend import io
from backend.infra.external.http.resend.config import ResendConfig
from backend.infra.external.http.resend.endpoints import Endpoint

if TYPE_CHECKING:
    from backend.infra.external.http.sessions.base import HTTPResponse
    from backend.internal.result import Result


class ResendClient(HTTPClient[ResendConfig]):
    @property
    def _auth_headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._config.RESEND_API_KEY}"}

    async def send(
        self,
        **data: Unpack[io.SendEmailRequest],
    ) -> Result[io.SendEmailResponse, HTTPResponse]:
        response = await self._session.post(
            url=Endpoint.SEND_EMAIL,
            headers=self._auth_headers,
            json=data,
        )
        return response.as_result(io.SendEmailResponse)

    async def send_batch(
        self,
        emails: list[io.SendEmailRequest],
    ) -> Result[io.BatchEmailResponse, HTTPResponse]:
        response = await self._session.post(
            url=Endpoint.SEND_BATCH,
            headers=self._auth_headers,
            json=emails,
        )
        return response.as_result(io.BatchEmailResponse)

    async def get(self, email_id: str) -> Result[io.Email, HTTPResponse]:
        response = await self._session.get(
            url=self._url(Endpoint.GET_EMAIL, email_id=email_id),
            headers=self._auth_headers,
        )
        return response.as_result(io.Email)

    async def cancel(self, email_id: str) -> Result[io.SendEmailResponse, HTTPResponse]:
        response = await self._session.post(
            url=self._url(Endpoint.CANCEL_EMAIL, email_id=email_id),
            headers=self._auth_headers,
        )
        return response.as_result(io.SendEmailResponse)

from __future__ import annotations

from typing import TYPE_CHECKING

from backend.infra.external.http.amplitude import io
from backend.infra.external.http.amplitude.config import AmplitudeConfig
from backend.infra.external.http.amplitude.endpoints import Endpoint
from backend.infra.external.http.client import HTTPClient

if TYPE_CHECKING:
    from backend.infra.external.http.sessions.base import HTTPResponse
    from backend.internal.result import Result


class AmplitudeClient(HTTPClient[AmplitudeConfig]):
    async def track(
        self,
        events: list[io.Event],
    ) -> Result[io.TrackResponse, HTTPResponse]:
        response = await self._session.post(
            url=Endpoint.TRACK,
            json={
                "api_key": self._config.AMPLITUDE_API_KEY,
                "events": events,
            },
        )
        return response.as_result(io.TrackResponse)

    async def identify(
        self,
        identifications: list[io.Identification],
    ) -> Result[io.IdentifyResponse, HTTPResponse]:
        response = await self._session.post(
            url=Endpoint.IDENTIFY,
            json={
                "api_key": self._config.AMPLITUDE_API_KEY,
                "identification": identifications,
            },
        )
        return response.as_result(io.IdentifyResponse)

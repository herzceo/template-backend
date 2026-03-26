from __future__ import annotations

from typing import TYPE_CHECKING, Unpack

from backend.infra.external.http.client import HTTPClient
from backend.infra.external.http.google_maps import io
from backend.infra.external.http.google_maps.config import GoogleMapsSettings
from backend.infra.external.http.google_maps.endpoints import Endpoint

if TYPE_CHECKING:
    from backend.infra.external.http.sessions.base import HTTPResponse
    from backend.internal.result import Result


class GoogleMapsClient(HTTPClient[GoogleMapsSettings]):
    @property
    def _auth_params(self) -> dict[str, str]:
        return {"key": self._settings.GOOGLE_MAPS_API_KEY}

    async def autocomplete(
        self,
        **params: Unpack[io.AutocompleteRequest],
    ) -> Result[io.AutocompleteResponse, HTTPResponse]:
        response = await self._session.get(
            url=Endpoint.AUTOCOMPLETE,
            params={**self._auth_params, **{k: str(v) for k, v in params.items()}},
        )
        return response.as_result(io.AutocompleteResponse)

    async def place_details(
        self,
        **params: Unpack[io.PlaceDetailsRequest],
    ) -> Result[io.PlaceDetailsResponse, HTTPResponse]:
        response = await self._session.get(
            url=Endpoint.PLACE_DETAILS,
            params={**self._auth_params, **{k: str(v) for k, v in params.items()}},
        )
        return response.as_result(io.PlaceDetailsResponse)

    async def geocode(
        self,
        **params: Unpack[io.GeocodeRequest],
    ) -> Result[io.GeocodeResponse, HTTPResponse]:
        response = await self._session.get(
            url=Endpoint.GEOCODE,
            params={**self._auth_params, **{k: str(v) for k, v in params.items()}},
        )
        return response.as_result(io.GeocodeResponse)

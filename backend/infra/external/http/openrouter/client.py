from __future__ import annotations

from typing import TYPE_CHECKING, Unpack

import msgspec

from backend.infra.external.http.client import HTTPClient
from backend.infra.external.http.openrouter import io
from backend.infra.external.http.openrouter.config import OpenRouterConfig
from backend.infra.external.http.openrouter.endpoints import OpenRouterEndpoints

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from backend.infra.external.http.sessions.base import HTTPResponse
    from backend.internal.result import Result

_DATA_PREFIX = "data:"
_DONE = "[DONE]"


class OpenRouterClient(HTTPClient[OpenRouterConfig]):
    @property
    def _auth_headers(self) -> dict[str, str]:
        headers = {"Authorization": f"Bearer {self._config.OPENROUTER_API_KEY}"}
        if self._config.OPENROUTER_HTTP_REFERER:
            headers["HTTP-Referer"] = self._config.OPENROUTER_HTTP_REFERER
        if self._config.OPENROUTER_TITLE:
            headers["X-Title"] = self._config.OPENROUTER_TITLE
        return headers

    async def complete(
        self,
        **body: Unpack[io.ChatCompletionRequest],
    ) -> Result[io.ChatCompletionResponse, HTTPResponse]:
        response = await self._session.post(
            url=OpenRouterEndpoints.CHAT_COMPLETIONS,
            headers=self._auth_headers,
            json=dict(body),
        )
        return response.as_result(io.ChatCompletionResponse)

    async def stream_complete(
        self,
        **body: Unpack[io.ChatCompletionRequest],
    ) -> AsyncIterator[io.ChatCompletionChunk]:
        async for raw in self._session.stream(
            "POST",
            url=OpenRouterEndpoints.CHAT_COMPLETIONS,
            headers=self._auth_headers,
            json={**body, "stream": True},
        ):
            line = raw.decode("utf-8").strip()
            if not line.startswith(_DATA_PREFIX):
                continue
            data = line.removeprefix(_DATA_PREFIX).strip()
            if data == _DONE:
                return
            yield msgspec.json.decode(data, type=io.ChatCompletionChunk)

    async def embed(
        self,
        **body: Unpack[io.EmbeddingRequest],
    ) -> Result[io.EmbeddingResponse, HTTPResponse]:
        response = await self._session.post(
            url=OpenRouterEndpoints.EMBEDDINGS,
            headers=self._auth_headers,
            json=dict(body),
        )
        return response.as_result(io.EmbeddingResponse)

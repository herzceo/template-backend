from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING, Any, cast, final

import msgspec

from backend.app.shared.ports.llm.openrouter import ChatMessage
from backend.infra.external.adapters.openrouter import ImplOpenRouterGateway
from backend.infra.external.http.openrouter.client import OpenRouterClient
from backend.infra.external.http.openrouter.config import OpenRouterConfig
from backend.infra.external.http.sessions.base import HTTPResponse

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from backend.infra.external.http.sessions.base import HTTPSession


@final
class _FakeSession:
    def __init__(
        self,
        *,
        post_body: bytes = b"",
        stream_lines: tuple[bytes, ...] = (),
    ) -> None:
        self._post_body = post_body
        self._stream_lines = stream_lines

    async def post(self, **_opts: Any) -> HTTPResponse:
        return HTTPResponse(
            status=HTTPStatus.OK, url="https://test", headers={}, body=self._post_body
        )

    async def stream(self, method: str, **_opts: Any) -> AsyncIterator[bytes]:
        assert method == "POST"
        for line in self._stream_lines:
            yield line


def _gateway(session: _FakeSession) -> ImplOpenRouterGateway:
    client = OpenRouterClient(
        session=cast("HTTPSession", session),
        config=OpenRouterConfig(OPENROUTER_API_KEY="test-key"),
    )
    return ImplOpenRouterGateway(client, default_model="test/model")


async def test_complete_parses_response() -> None:
    body = msgspec.json.encode(
        {
            "model": "test/model",
            "choices": [
                {
                    "message": {"role": "assistant", "content": "hello world"},
                    "finish_reason": "stop",
                }
            ],
            "usage": {"prompt_tokens": 5, "completion_tokens": 2, "total_tokens": 7},
        }
    )
    gateway = _gateway(_FakeSession(post_body=body))

    result = await gateway.complete(messages=[ChatMessage(role="user", content="hi")])

    assert result.content == "hello world"
    assert result.model == "test/model"
    assert result.prompt_tokens == 5
    assert result.completion_tokens == 2


async def test_stream_accumulates_deltas_until_done() -> None:
    lines = (
        b'data: {"choices":[{"delta":{"content":"Hel"}}]}\n',
        b": OPENROUTER PROCESSING\n",
        b'data: {"choices":[{"delta":{"content":"lo"}}]}\n',
        b"data: [DONE]\n",
        b'data: {"choices":[{"delta":{"content":"ignored"}}]}\n',
    )
    gateway = _gateway(_FakeSession(stream_lines=lines))

    deltas = [
        d.content async for d in gateway.stream(messages=[ChatMessage(role="user", content="hi")])
    ]

    assert deltas == ["Hel", "lo"]


async def test_embed_maps_vectors() -> None:
    body = msgspec.json.encode(
        {
            "model": "test/embed",
            "data": [
                {"embedding": [0.1, 0.2], "index": 0},
                {"embedding": [0.3, 0.4], "index": 1},
            ],
            "usage": {"prompt_tokens": 3, "completion_tokens": 0, "total_tokens": 3},
        }
    )
    gateway = _gateway(_FakeSession(post_body=body))

    result = await gateway.embed(inputs=["a", "b"])

    assert [e.vector for e in result] == [[0.1, 0.2], [0.3, 0.4]]
    assert [e.index for e in result] == [0, 1]
